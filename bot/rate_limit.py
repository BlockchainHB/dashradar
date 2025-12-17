import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Tuple, Dict, List, Set

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter for user search requests.

    Limits:
    - 10 searches per hour per user
    - 30 searches per day per user
    - 1 concurrent search per user
    """

    def __init__(
        self,
        hourly_limit: int = 10,
        daily_limit: int = 30
    ):
        self.hourly_limit = hourly_limit
        self.daily_limit = daily_limit

        # user_id -> list of search timestamps
        self.user_searches: Dict[int, List[datetime]] = defaultdict(list)

        # Set of user_ids currently running a search
        self.active_searches: Set[int] = set()

    def _cleanup_old_searches(self, user_id: int) -> None:
        """Remove searches older than 24 hours for a user."""
        day_ago = datetime.now() - timedelta(days=1)
        self.user_searches[user_id] = [
            ts for ts in self.user_searches[user_id]
            if ts > day_ago
        ]

    def can_search(self, user_id: int) -> Tuple[bool, str]:
        """
        Check if a user can perform a search.

        Args:
            user_id: Telegram user ID

        Returns:
            Tuple of (allowed: bool, message: str)
            If not allowed, message contains the reason
        """
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)

        # Check concurrent search
        if user_id in self.active_searches:
            return False, "You already have a search in progress. Please wait for it to complete."

        # Clean up old entries
        self._cleanup_old_searches(user_id)

        # Count searches in last hour
        hourly_searches = sum(
            1 for ts in self.user_searches[user_id]
            if ts > hour_ago
        )

        # Count searches in last day
        daily_searches = len(self.user_searches[user_id])

        # Check hourly limit
        if hourly_searches >= self.hourly_limit:
            # Find when the oldest search in the hour window will expire
            oldest_in_hour = min(
                ts for ts in self.user_searches[user_id]
                if ts > hour_ago
            )
            wait_minutes = 60 - int((now - oldest_in_hour).total_seconds() / 60)
            return False, f"Hourly limit reached ({self.hourly_limit} searches). Try again in {wait_minutes} minute(s)."

        # Check daily limit
        if daily_searches >= self.daily_limit:
            # Find when the oldest search will expire (24h from when it was made)
            oldest = min(self.user_searches[user_id])
            expires_at = oldest + timedelta(days=1)
            hours_left = int((expires_at - now).total_seconds() / 3600)
            return False, f"Daily limit reached ({self.daily_limit} searches). Try again in {hours_left} hour(s)."

        return True, ""

    def start_search(self, user_id: int) -> bool:
        """
        Mark the start of a search for a user.

        Args:
            user_id: Telegram user ID

        Returns:
            True if search was started, False if user already has active search
        """
        if user_id in self.active_searches:
            return False

        self.active_searches.add(user_id)
        self.user_searches[user_id].append(datetime.now())
        logger.info(f"User {user_id} started search")
        return True

    def end_search(self, user_id: int) -> None:
        """
        Mark the end of a search for a user.

        Args:
            user_id: Telegram user ID
        """
        self.active_searches.discard(user_id)
        logger.info(f"User {user_id} ended search")

    def get_usage(self, user_id: int) -> Dict[str, int]:
        """
        Get usage statistics for a user.

        Args:
            user_id: Telegram user ID

        Returns:
            Dict with hourly_used, hourly_limit, daily_used, daily_limit
        """
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)

        self._cleanup_old_searches(user_id)

        hourly_used = sum(
            1 for ts in self.user_searches[user_id]
            if ts > hour_ago
        )
        daily_used = len(self.user_searches[user_id])

        return {
            "hourly_used": hourly_used,
            "hourly_limit": self.hourly_limit,
            "daily_used": daily_used,
            "daily_limit": self.daily_limit,
            "has_active_search": user_id in self.active_searches
        }


# Global rate limiter instance
rate_limiter = RateLimiter()
