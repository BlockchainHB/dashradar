import hashlib
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any, List

from bot.models import Restaurant, DeliveryProvider

logger = logging.getLogger(__name__)


class FileCache:
    """File-based caching for restaurants and delivery providers."""

    # TTL values in hours
    RESTAURANT_TTL = 24  # Cache restaurants by address for 24 hours
    PROVIDER_TTL = 168   # Cache providers by kgmid for 7 days (168 hours)
    GEOCODE_TTL = 720    # Cache geocoded addresses for 30 days (720 hours)

    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # Create subdirectories for different cache types
        (self.cache_dir / "restaurants").mkdir(exist_ok=True)
        (self.cache_dir / "providers").mkdir(exist_ok=True)
        (self.cache_dir / "geocode").mkdir(exist_ok=True)

    def _hash_key(self, key: str) -> str:
        """Create a hash from the key for filename."""
        return hashlib.sha256(key.lower().strip().encode()).hexdigest()[:16]

    def _get_path(self, cache_type: str, key: str) -> Path:
        """Get the file path for a cache entry."""
        return self.cache_dir / cache_type / f"{self._hash_key(key)}.json"

    def get(self, cache_type: str, key: str, ttl_hours: int) -> Optional[Any]:
        """
        Get a value from cache if it exists and hasn't expired.

        Args:
            cache_type: Type of cache (restaurants, providers, geocode)
            key: Cache key (address or kgmid)
            ttl_hours: Time-to-live in hours

        Returns:
            Cached value or None if not found/expired
        """
        file_path = self._get_path(cache_type, key)

        if not file_path.exists():
            return None

        try:
            data = json.loads(file_path.read_text())
            cached_at = datetime.fromisoformat(data["cached_at"])

            if datetime.now() - cached_at > timedelta(hours=ttl_hours):
                file_path.unlink()  # Delete expired cache
                logger.debug(f"Cache expired for {cache_type}:{key[:20]}")
                return None

            logger.debug(f"Cache hit for {cache_type}:{key[:20]}")
            return data["value"]

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Invalid cache file {file_path}: {e}")
            file_path.unlink(missing_ok=True)
            return None

    def set(self, cache_type: str, key: str, value: Any) -> None:
        """
        Store a value in cache.

        Args:
            cache_type: Type of cache (restaurants, providers, geocode)
            key: Cache key (address or kgmid)
            value: Value to cache (must be JSON-serializable)
        """
        file_path = self._get_path(cache_type, key)

        try:
            file_path.write_text(json.dumps({
                "cached_at": datetime.now().isoformat(),
                "key": key,
                "value": value
            }, indent=2))
            logger.debug(f"Cached {cache_type}:{key[:20]}")
        except Exception as e:
            logger.error(f"Failed to write cache {file_path}: {e}")

    # Convenience methods for specific cache types

    def get_restaurants(self, address: str) -> Optional[List[dict]]:
        """Get cached restaurants for an address."""
        return self.get("restaurants", address, self.RESTAURANT_TTL)

    def set_restaurants(self, address: str, restaurants: List[Restaurant]) -> None:
        """Cache restaurants for an address."""
        # Convert Restaurant objects to dicts for JSON serialization
        value = [r.model_dump() for r in restaurants]
        self.set("restaurants", address, value)

    def get_providers(self, kgmid: str) -> Optional[List[dict]]:
        """Get cached delivery providers for a restaurant."""
        return self.get("providers", kgmid, self.PROVIDER_TTL)

    def set_providers(self, kgmid: str, providers: List[DeliveryProvider]) -> None:
        """Cache delivery providers for a restaurant."""
        value = [p.model_dump() for p in providers]
        self.set("providers", kgmid, value)

    def get_geocode(self, address: str) -> Optional[dict]:
        """Get cached geocode result for an address."""
        return self.get("geocode", address, self.GEOCODE_TTL)

    def set_geocode(self, address: str, lat: float, lng: float, formatted: str) -> None:
        """Cache geocode result for an address."""
        self.set("geocode", address, {
            "lat": lat,
            "lng": lng,
            "formatted_address": formatted
        })

    def clear(self, cache_type: Optional[str] = None) -> int:
        """
        Clear cache files.

        Args:
            cache_type: Specific cache type to clear, or None for all

        Returns:
            Number of files deleted
        """
        count = 0

        if cache_type:
            cache_path = self.cache_dir / cache_type
            if cache_path.exists():
                for f in cache_path.glob("*.json"):
                    f.unlink()
                    count += 1
        else:
            for subdir in ["restaurants", "providers", "geocode"]:
                cache_path = self.cache_dir / subdir
                if cache_path.exists():
                    for f in cache_path.glob("*.json"):
                        f.unlink()
                        count += 1

        logger.info(f"Cleared {count} cache files")
        return count


# Global cache instance
cache = FileCache()
