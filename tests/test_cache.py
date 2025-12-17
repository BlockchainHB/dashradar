import pytest
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path

from bot.cache import FileCache
from bot.models import Restaurant, DeliveryProvider


@pytest.fixture
def temp_cache():
    """Create a temporary cache directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = FileCache(cache_dir=tmpdir)
        yield cache


class TestFileCache:
    def test_init_creates_directories(self, temp_cache):
        """Test that init creates cache subdirectories."""
        assert (Path(temp_cache.cache_dir) / "restaurants").exists()
        assert (Path(temp_cache.cache_dir) / "providers").exists()
        assert (Path(temp_cache.cache_dir) / "geocode").exists()

    def test_hash_key(self, temp_cache):
        """Test that hash_key produces consistent results."""
        key1 = temp_cache._hash_key("123 Main St, Toronto")
        key2 = temp_cache._hash_key("123 main st, toronto")  # Different case
        key3 = temp_cache._hash_key("456 Other St, Toronto")

        # Same address (case-insensitive) should produce same hash
        assert key1 == key2
        # Different addresses should produce different hashes
        assert key1 != key3

    def test_set_and_get(self, temp_cache):
        """Test basic set and get operations."""
        temp_cache.set("restaurants", "test_key", {"name": "Test Restaurant"})
        result = temp_cache.get("restaurants", "test_key", ttl_hours=24)

        assert result is not None
        assert result["name"] == "Test Restaurant"

    def test_get_nonexistent(self, temp_cache):
        """Test get returns None for nonexistent keys."""
        result = temp_cache.get("restaurants", "nonexistent", ttl_hours=24)
        assert result is None

    def test_cache_expiration(self, temp_cache):
        """Test that expired cache entries are not returned."""
        # Manually create an expired cache entry
        key = "expired_key"
        file_path = temp_cache._get_path("restaurants", key)

        expired_time = datetime.now() - timedelta(hours=25)
        file_path.write_text(json.dumps({
            "cached_at": expired_time.isoformat(),
            "key": key,
            "value": {"name": "Expired"}
        }))

        # Should return None because it's expired
        result = temp_cache.get("restaurants", key, ttl_hours=24)
        assert result is None

        # File should be deleted
        assert not file_path.exists()

    def test_set_restaurants(self, temp_cache):
        """Test caching Restaurant objects."""
        restaurants = [
            Restaurant(
                name="Test Restaurant",
                address="123 Main St",
                kgmid="/g/123",
                place_id="place123",
                lat=43.65,
                lng=-79.38
            )
        ]

        temp_cache.set_restaurants("Toronto, ON", restaurants)
        cached = temp_cache.get_restaurants("Toronto, ON")

        assert cached is not None
        assert len(cached) == 1
        assert cached[0]["name"] == "Test Restaurant"

    def test_set_providers(self, temp_cache):
        """Test caching DeliveryProvider objects."""
        providers = [
            DeliveryProvider(name="DoorDash", url="https://doordash.com/store/123")
        ]

        temp_cache.set_providers("/g/123", providers)
        cached = temp_cache.get_providers("/g/123")

        assert cached is not None
        assert len(cached) == 1
        assert cached[0]["name"] == "DoorDash"

    def test_set_geocode(self, temp_cache):
        """Test caching geocode results."""
        temp_cache.set_geocode("123 Main St", 43.65, -79.38, "123 Main St, Toronto, ON")
        cached = temp_cache.get_geocode("123 Main St")

        assert cached is not None
        assert cached["lat"] == 43.65
        assert cached["lng"] == -79.38
        assert "Toronto" in cached["formatted_address"]

    def test_clear_specific_type(self, temp_cache):
        """Test clearing a specific cache type."""
        temp_cache.set("restaurants", "key1", {"data": 1})
        temp_cache.set("providers", "key2", {"data": 2})

        count = temp_cache.clear("restaurants")
        assert count == 1

        # Restaurants should be cleared
        assert temp_cache.get("restaurants", "key1", 24) is None
        # Providers should still exist
        assert temp_cache.get("providers", "key2", 168) is not None

    def test_clear_all(self, temp_cache):
        """Test clearing all cache types."""
        temp_cache.set("restaurants", "key1", {"data": 1})
        temp_cache.set("providers", "key2", {"data": 2})
        temp_cache.set("geocode", "key3", {"data": 3})

        count = temp_cache.clear()
        assert count == 3

    def test_empty_providers_cached(self, temp_cache):
        """Test that empty provider list is cached (not None)."""
        temp_cache.set_providers("/g/empty", [])
        cached = temp_cache.get_providers("/g/empty")

        # Should return empty list, not None
        assert cached is not None
        assert cached == []
