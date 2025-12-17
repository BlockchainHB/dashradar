import httpx
import logging
from typing import List

from bot.models import Restaurant
from bot import APIFY_TOKEN
from bot.cache import cache
from bot.exceptions import ApifyError, ApifyTimeout, ApifyQuotaExceeded

ACTOR_URL = "https://api.apify.com/v2/acts/blueorion~free-google-maps-scraper-extensive/run-sync-get-dataset-items"

logger = logging.getLogger(__name__)


def _parse_restaurant(data: dict) -> Restaurant:
    """Parse a restaurant from Apify response or cache data."""
    # Handle both Apify response format and cached format
    if "location" in data:
        # Apify format
        location = data.get("location", {})
        return Restaurant(
            name=data.get("title", "Unknown"),
            address=data.get("address", ""),
            kgmid=data["kgmid"],
            place_id=data.get("placeId", ""),
            phone=data.get("phone"),
            website=data.get("website"),
            rating=data.get("reviewScore"),
            lat=location["lat"],
            lng=location["lng"],
        )
    else:
        # Cached format (already Restaurant dict)
        return Restaurant(**data)


async def search_restaurants(
    address: str,
    limit: int = 100,
    use_cache: bool = True
) -> List[Restaurant]:
    """
    Search for restaurants near an address using Apify actor.

    Args:
        address: User's address string
        limit: Max results to return
        use_cache: Whether to use cached results

    Returns:
        List of Restaurant objects with kgmid values
    """
    # Check cache first
    if use_cache:
        cached = cache.get_restaurants(address)
        if cached:
            logger.info(f"Cache hit for restaurants near: {address[:30]}")
            return [_parse_restaurant(r) for r in cached]

    async with httpx.AsyncClient(timeout=300) as client:
        logger.info(f"Searching restaurants near: {address}")

        try:
            response = await client.post(
                ACTOR_URL,
                params={"token": APIFY_TOKEN},
                json={
                    "maxItems": limit,
                    "mode": "slow",
                    "searchTerms": ["restaurant"],
                    "startingLocations": [address],
                }
            )

            if response.status_code == 402:
                raise ApifyQuotaExceeded()
            if response.status_code == 408:
                raise ApifyTimeout()

            response.raise_for_status()

        except httpx.TimeoutException:
            raise ApifyTimeout()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 402:
                raise ApifyQuotaExceeded()
            raise ApifyError(
                f"Apify API error: {e.response.status_code}",
                "Error searching for restaurants. Please try again."
            )

        results = response.json()
        logger.info(f"Found {len(results)} restaurants from Apify")

        restaurants = []
        for r in results:
            if not r.get("kgmid"):
                continue

            location = r.get("location", {})
            if not location.get("lat") or not location.get("lng"):
                continue

            restaurants.append(
                Restaurant(
                    name=r.get("title", "Unknown"),
                    address=r.get("address", ""),
                    kgmid=r["kgmid"],
                    place_id=r.get("placeId", ""),
                    phone=r.get("phone"),
                    website=r.get("website"),
                    rating=r.get("reviewScore"),
                    lat=location["lat"],
                    lng=location["lng"],
                )
            )

        # Cache the results
        if restaurants and use_cache:
            cache.set_restaurants(address, restaurants)

        return restaurants
