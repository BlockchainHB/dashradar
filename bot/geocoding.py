import httpx
import logging
from typing import Optional, Tuple

from bot.cache import cache
from bot.exceptions import InvalidAddressError

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


async def geocode_address(address: str) -> Tuple[float, float, str]:
    """
    Geocode an address to coordinates using Nominatim (OpenStreetMap).

    Args:
        address: User's address string

    Returns:
        Tuple of (latitude, longitude, formatted_address)

    Raises:
        InvalidAddressError: If address cannot be geocoded
    """
    # Check cache first
    cached = cache.get_geocode(address)
    if cached:
        logger.info(f"Geocode cache hit for: {address[:30]}")
        return (
            cached["lat"],
            cached["lng"],
            cached["formatted_address"]
        )

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.get(
                NOMINATIM_URL,
                params={
                    "q": address,
                    "format": "json",
                    "limit": 1,
                    "addressdetails": 1
                },
                headers={
                    "User-Agent": "DoorDashFinder/1.0 (telegram-bot)"
                }
            )
            response.raise_for_status()

            results = response.json()

            if not results:
                raise InvalidAddressError(
                    f"Could not find address: {address}. "
                    "Try including city and province/state."
                )

            result = results[0]
            lat = float(result["lat"])
            lng = float(result["lon"])
            formatted = result["display_name"]

            # Cache the result
            cache.set_geocode(address, lat, lng, formatted)

            logger.info(f"Geocoded '{address[:30]}' -> ({lat:.4f}, {lng:.4f})")
            return (lat, lng, formatted)

        except httpx.HTTPError as e:
            logger.error(f"Geocoding HTTP error for '{address}': {e}")
            raise InvalidAddressError(
                "Unable to validate address. Please try again."
            )


def simplify_address(formatted_address: str) -> str:
    """
    Simplify a Nominatim formatted address for display.

    Example:
        Input: "138 Chillery Avenue, Malvern, Scarborough, Toronto, Golden Horseshoe, Ontario, M1J 2N8, Canada"
        Output: "138 Chillery Avenue, Scarborough, Toronto, ON"
    """
    parts = [p.strip() for p in formatted_address.split(",")]

    # Extract key parts
    if len(parts) >= 4:
        # Usually: street, neighborhood, city/district, region, province, postal, country
        street = parts[0]

        # Find city (usually 3rd or 4th position)
        city = None
        province = None

        for part in parts[1:]:
            part_lower = part.lower()
            # Skip neighborhood-level names
            if any(x in part_lower for x in ["horseshoe", "region", "county", "district"]):
                continue
            # Detect province/state
            if part in ["Ontario", "Quebec", "British Columbia", "Alberta", "Manitoba",
                        "Saskatchewan", "Nova Scotia", "New Brunswick",
                        "Newfoundland and Labrador", "Prince Edward Island",
                        "Northwest Territories", "Nunavut", "Yukon"]:
                province = _abbreviate_province(part)
                break
            # Skip postal codes
            if len(part) <= 7 and any(c.isdigit() for c in part):
                continue
            # Skip country
            if part.lower() in ["canada", "usa", "united states"]:
                continue
            # This is probably a city/district name
            if city is None:
                city = part

        if city and province:
            return f"{street}, {city}, {province}"
        elif city:
            return f"{street}, {city}"

    return formatted_address


def _abbreviate_province(province: str) -> str:
    """Abbreviate Canadian province names."""
    abbreviations = {
        "Ontario": "ON",
        "Quebec": "QC",
        "British Columbia": "BC",
        "Alberta": "AB",
        "Manitoba": "MB",
        "Saskatchewan": "SK",
        "Nova Scotia": "NS",
        "New Brunswick": "NB",
        "Newfoundland and Labrador": "NL",
        "Prince Edward Island": "PE",
        "Northwest Territories": "NT",
        "Nunavut": "NU",
        "Yukon": "YT",
    }
    return abbreviations.get(province, province)
