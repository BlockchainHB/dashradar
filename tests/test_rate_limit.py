import pytest
from datetime import datetime, timedelta

from bot.rate_limit import RateLimiter


@pytest.fixture
def limiter():
    """Create a fresh rate limiter for each test."""
    return RateLimiter(hourly_limit=3, daily_limit=5)


class TestRateLimiter:
    def test_can_search_initially(self, limiter):
        """Test that new users can search."""
        can, msg = limiter.can_search(user_id=123)
        assert can is True
        assert msg == ""

    def test_start_search_records_timestamp(self, limiter):
        """Test that starting a search records the timestamp."""
        limiter.start_search(user_id=123)
        assert len(limiter.user_searches[123]) == 1

    def test_concurrent_search_blocked(self, limiter):
        """Test that concurrent searches are blocked."""
        limiter.start_search(user_id=123)

        can, msg = limiter.can_search(user_id=123)
        assert can is False
        assert "already have a search in progress" in msg

    def test_end_search_allows_new_search(self, limiter):
        """Test that ending a search allows new searches."""
        limiter.start_search(user_id=123)
        limiter.end_search(user_id=123)

        can, msg = limiter.can_search(user_id=123)
        assert can is True

    def test_hourly_limit_enforced(self, limiter):
        """Test that hourly limit is enforced."""
        user_id = 456

        # Perform 3 searches (at the limit)
        for _ in range(3):
            limiter.start_search(user_id)
            limiter.end_search(user_id)

        # 4th search should be blocked
        can, msg = limiter.can_search(user_id)
        assert can is False
        assert "Hourly limit reached" in msg

    def test_daily_limit_enforced(self, limiter):
        """Test that daily limit is enforced."""
        user_id = 789

        # Simulate searches spread across time to avoid hourly limit
        # but hit daily limit
        now = datetime.now()

        # Add 5 searches from different hours
        for i in range(5):
            limiter.user_searches[user_id].append(
                now - timedelta(hours=i * 2)  # Spread across 10 hours
            )

        can, msg = limiter.can_search(user_id)
        assert can is False
        assert "Daily limit reached" in msg

    def test_old_searches_cleaned_up(self, limiter):
        """Test that searches older than 24h are cleaned up."""
        user_id = 111
        now = datetime.now()

        # Add old search (25 hours ago)
        limiter.user_searches[user_id].append(now - timedelta(hours=25))

        # Should still be able to search
        can, msg = limiter.can_search(user_id)
        assert can is True

        # Old search should be cleaned up
        assert len(limiter.user_searches[user_id]) == 0

    def test_get_usage(self, limiter):
        """Test usage statistics."""
        user_id = 222

        # Perform some searches
        limiter.start_search(user_id)
        limiter.end_search(user_id)
        limiter.start_search(user_id)
        limiter.end_search(user_id)

        usage = limiter.get_usage(user_id)

        assert usage["hourly_used"] == 2
        assert usage["hourly_limit"] == 3
        assert usage["daily_used"] == 2
        assert usage["daily_limit"] == 5
        assert usage["has_active_search"] is False

    def test_get_usage_with_active_search(self, limiter):
        """Test usage shows active search status."""
        user_id = 333

        limiter.start_search(user_id)
        usage = limiter.get_usage(user_id)

        assert usage["has_active_search"] is True

    def test_different_users_independent(self, limiter):
        """Test that different users have independent limits."""
        user1, user2 = 444, 555

        # User 1 hits limit
        for _ in range(3):
            limiter.start_search(user1)
            limiter.end_search(user1)

        # User 1 blocked
        can1, _ = limiter.can_search(user1)
        assert can1 is False

        # User 2 should still be able to search
        can2, _ = limiter.can_search(user2)
        assert can2 is True

    def test_start_search_returns_false_if_active(self, limiter):
        """Test that start_search returns False if search already active."""
        user_id = 666

        result1 = limiter.start_search(user_id)
        assert result1 is True

        result2 = limiter.start_search(user_id)
        assert result2 is False
