import logging
import asyncio

from aiogram import types
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode

from bot import get_dp, get_bot
from bot.apify import search_restaurants
from bot.google import check_restaurants_for_doordash
from bot.geocoding import geocode_address, simplify_address
from bot.distance import filter_by_distance, sort_by_distance
from bot.rate_limit import rate_limiter
from bot.utils import is_valid_address, escape_markdown
from bot.exceptions import (
    BotError,
    InvalidAddressError,
    get_user_message
)

logger = logging.getLogger(__name__)

# Get bot and dispatcher instances
bot = get_bot()
dp = get_dp()

# Default search radius in km
DEFAULT_RADIUS_KM = 10.0


async def main() -> None:
    await dp.start_polling(bot)


@dp.message(CommandStart())
async def command_start(message: types.Message) -> None:
    await message.reply(
        text="""Welcome to DoorDash Restaurant Finder!

Send me an address and I'll find nearby restaurants with DoorDash ordering available.

Example: 123 Queen St W, Toronto, ON
"""
    )


@dp.message(Command("help"))
async def command_help(message: types.Message) -> None:
    await message.reply(
        text="""How to use:

1. Send me any address
2. I'll find restaurants with DoorDash nearby
3. Results are sorted by distance

Tips:
- Include city and province for best results
- Results are cached for faster repeat searches
"""
    )


@dp.message(Command("usage"))
async def command_usage(message: types.Message) -> None:
    user_id = message.from_user.id
    usage = rate_limiter.get_usage(user_id)

    await message.reply(
        text=f"""Your usage:

Hourly: {usage['hourly_used']}/{usage['hourly_limit']} searches
Daily: {usage['daily_used']}/{usage['daily_limit']} searches
"""
    )


@dp.message()
async def address_handler(message: types.Message) -> None:
    """Handle address input from user."""
    address = message.text.strip()
    user_id = message.from_user.id

    # Basic validation
    if not is_valid_address(address):
        await message.reply(
            text="Please send a valid address (e.g., 123 Queen St W, Toronto, ON)"
        )
        return

    # Check rate limits
    can_search, limit_msg = rate_limiter.can_search(user_id)
    if not can_search:
        await message.reply(text=limit_msg)
        return

    # Start the search
    if not rate_limiter.start_search(user_id):
        await message.reply("You already have a search in progress. Please wait.")
        return

    status_msg = await message.reply("Finding DoorDash restaurants near you. This may take up to a minute...")

    try:
        # Step 1: Geocode the address
        try:
            user_lat, user_lng, formatted_address = await geocode_address(address)
            simplified = simplify_address(formatted_address)
        except InvalidAddressError as e:
            await status_msg.edit_text(e.user_message)
            return

        # Step 2: Get restaurants from Apify
        restaurants = await search_restaurants(simplified, limit=50)

        if not restaurants:
            await status_msg.edit_text(
                f"No restaurants found near {simplified}. Try a different address."
            )
            return

        # Step 3: Filter by distance
        nearby = filter_by_distance(restaurants, user_lat, user_lng, DEFAULT_RADIUS_KM)

        if not nearby:
            await status_msg.edit_text(
                f"No restaurants found within {DEFAULT_RADIUS_KM}km of {simplified}."
            )
            return

        # Step 4: Check DoorDash availability (concurrent)
        doordash_restaurants = await check_restaurants_for_doordash(nearby)

        if not doordash_restaurants:
            await status_msg.edit_text(
                f"Found {len(nearby)} restaurants near {simplified}, but none have DoorDash on Google Maps."
            )
            return

        # Step 5: Sort by distance and format results
        sorted_results = sort_by_distance(doordash_restaurants)
        await send_results(status_msg, sorted_results, simplified)

    except BotError as e:
        logger.error(f"Bot error: {e}")
        await status_msg.edit_text(e.user_message)

    except Exception as e:
        logger.exception(f"Error processing search: {e}")
        await status_msg.edit_text(get_user_message(e))

    finally:
        rate_limiter.end_search(user_id)


async def send_results(message: types.Message, restaurants: list, address: str) -> None:
    """Format and send search results."""
    count = len(restaurants)
    shown = min(count, 20)

    # Build result text with proper escaping
    lines = [f"Found {count} DoorDash restaurants near {escape_markdown(address)}:\n"]

    for r in restaurants[:shown]:
        name = escape_markdown(r.name)
        addr = escape_markdown(r.address)

        lines.append(f"*{name}*")

        if r.distance_km is not None:
            lines.append(f"{r.distance_km} km away")

        lines.append(f"{addr}")

        if r.rating:
            lines.append(f"Rating: {r.rating}")

        # URL needs special handling - don't escape the URL itself
        lines.append(f"[Order on DoorDash]({r.doordash_url})\n")

    if count > shown:
        lines.append(f"\\.\\.\\. and {count - shown} more")

    result_text = "\n".join(lines)

    try:
        await message.edit_text(result_text, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        # Fallback to plain text if markdown fails
        logger.warning(f"Markdown failed, using plain text: {e}")
        plain_lines = [f"Found {count} DoorDash restaurants near {address}:\n"]

        for r in restaurants[:shown]:
            plain_lines.append(f"{r.name}")
            if r.distance_km is not None:
                plain_lines.append(f"  {r.distance_km} km away")
            plain_lines.append(f"  {r.address}")
            if r.rating:
                plain_lines.append(f"  Rating: {r.rating}")
            plain_lines.append(f"  {r.doordash_url}\n")

        if count > shown:
            plain_lines.append(f"... and {count - shown} more")

        await message.edit_text("\n".join(plain_lines))


if __name__ == "__main__":
    asyncio.run(main())
