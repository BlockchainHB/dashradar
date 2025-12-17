import httpx
import re
import asyncio
import logging
from typing import List

from bot.models import Restaurant, DeliveryProvider
from bot.cache import cache
from bot.exceptions import GoogleRateLimited

CHOOSEPROVIDER_URL = "https://www.google.com/viewer/chooseprovider"

# Regex patterns for delivery providers
DOORDASH_PATTERN = re.compile(r'https?://(?:www\.)?doordash\.com/store/[^"\'>\s]+')
UBEREATS_PATTERN = re.compile(r'https?://(?:www\.)?ubereats\.com/[^"\'>\s]+')
SKIP_PATTERN = re.compile(r'https?://(?:www\.)?skipthedishes\.com/[^"\'>\s]+')

logger = logging.getLogger(__name__)


async def get_delivery_providers(
    kgmid: str,
    country: str = "ca",
    language: str = "en-CA",
    use_cache: bool = True
) -> List[DeliveryProvider]:
    """
    Fetch delivery providers for a restaurant from Google.

    Args:
        kgmid: Google Knowledge Graph ID (e.g., "/g/11ybzt640l")
        country: Country code
        language: Language code
        use_cache: Whether to use cached results

    Returns:
        List of DeliveryProvider objects
    """
    # Check cache first
    if use_cache:
        cached = cache.get_providers(kgmid)
        if cached is not None:  # Empty list is valid cached result
            logger.debug(f"Cache hit for providers: {kgmid}")
            return [DeliveryProvider(**p) for p in cached]

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.get(
                CHOOSEPROVIDER_URL,
                params={
                    "mid": kgmid,
                    "hl": language,
                    "gl": country,
                    "orderType": 1,  # Delivery
                },
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
            )

            if response.status_code == 429:
                raise GoogleRateLimited()

            if response.status_code != 200:
                logger.warning(f"chooseprovider returned {response.status_code} for {kgmid}")
                return []

            html = response.text
            providers = []

            # Extract DoorDash links
            doordash_matches = DOORDASH_PATTERN.findall(html)
            if doordash_matches:
                providers.append(DeliveryProvider(
                    name="DoorDash",
                    url=doordash_matches[0]
                ))

            # Extract Uber Eats links
            ubereats_matches = UBEREATS_PATTERN.findall(html)
            if ubereats_matches:
                providers.append(DeliveryProvider(
                    name="Uber Eats",
                    url=ubereats_matches[0]
                ))

            # Extract Skip links
            skip_matches = SKIP_PATTERN.findall(html)
            if skip_matches:
                providers.append(DeliveryProvider(
                    name="SkipTheDishes",
                    url=skip_matches[0]
                ))

            # Cache the result (even if empty - means no providers)
            if use_cache:
                cache.set_providers(kgmid, providers)

            return providers

        except GoogleRateLimited:
            raise
        except Exception as e:
            logger.error(f"Error fetching providers for {kgmid}: {e}")
            return []


async def check_restaurants_for_doordash(
    restaurants: List[Restaurant],
    max_concurrent: int = 10,
    delay: float = 0.1
) -> List[Restaurant]:
    """
    Check which restaurants have DoorDash integration using concurrent requests.

    Args:
        restaurants: List of restaurants from Apify
        max_concurrent: Maximum concurrent requests to Google
        delay: Small delay between starting requests

    Returns:
        Filtered list with only DoorDash-enabled restaurants
    """
    results = []
    semaphore = asyncio.Semaphore(max_concurrent)

    async def check_one(restaurant: Restaurant) -> Restaurant | None:
        async with semaphore:
            providers = await get_delivery_providers(restaurant.kgmid)
            await asyncio.sleep(delay)  # Small delay to avoid rate limiting

            doordash = next((p for p in providers if p.name == "DoorDash"), None)
            if doordash:
                restaurant.doordash_url = doordash.url
                restaurant.delivery_providers = providers
                logger.info(f"Found DoorDash for: {restaurant.name}")
                return restaurant
            return None

    # Run all checks concurrently (limited by semaphore)
    tasks = [check_one(r) for r in restaurants]
    checked = await asyncio.gather(*tasks)

    # Filter out None results
    results = [r for r in checked if r is not None]

    return results
