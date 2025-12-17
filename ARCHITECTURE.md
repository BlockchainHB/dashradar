# DashRadar Architecture Guide

This document provides a detailed technical overview of DashRadar for developers and AI assistants. If you're using Claude Code, Cursor, or another LLM-assisted development tool, this document will help you understand the codebase.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Directory Structure](#directory-structure)
3. [Core Flow](#core-flow)
4. [Module Documentation](#module-documentation)
5. [Data Models](#data-models)
6. [External APIs](#external-apis)
7. [Caching System](#caching-system)
8. [Error Handling](#error-handling)
9. [Testing](#testing)
10. [Common Tasks](#common-tasks)

---

## Project Overview

DashRadar is a Telegram bot that:
1. Receives an address from a user
2. Geocodes it to coordinates using Nominatim (OpenStreetMap)
3. Finds nearby restaurants using Apify's Google Maps scraper
4. Checks each restaurant for DoorDash availability via Google's chooseprovider endpoint
5. Returns results sorted by distance with direct ordering links

**Tech Stack:**
- Python 3.11+
- aiogram 3.x (Telegram bot framework)
- httpx (async HTTP client)
- Pydantic (data validation)

---

## Directory Structure

```
dashradar/
├── bot/                    # Main application code
│   ├── __init__.py         # Config loading, bot initialization
│   ├── __main__.py         # Entry point, Telegram handlers
│   ├── apify.py            # Apify API client (restaurant search)
│   ├── google.py           # Google chooseprovider scraper
│   ├── geocoding.py        # Nominatim geocoding
│   ├── distance.py         # Haversine distance math
│   ├── cache.py            # File-based caching
│   ├── rate_limit.py       # User rate limiting
│   ├── models.py           # Pydantic models
│   ├── exceptions.py       # Custom exceptions
│   └── utils.py            # Helper functions
│
├── tests/                  # Unit tests
│   ├── test_cache.py       # Cache tests
│   ├── test_distance.py    # Distance calculation tests
│   ├── test_geocoding.py   # Geocoding utility tests
│   ├── test_google.py      # Regex pattern tests
│   ├── test_main.py        # Utility function tests
│   ├── test_models.py      # Pydantic model tests
│   └── test_rate_limit.py  # Rate limiter tests
│
├── .cache/                 # Cache storage (gitignored)
│   ├── restaurants/        # Cached restaurant searches
│   ├── providers/          # Cached delivery providers
│   └── geocode/            # Cached geocode results
│
├── .env                    # API credentials (gitignored)
├── .env.example            # Template for .env
├── requirements.txt        # Python dependencies
├── README.md               # Project overview
├── ARCHITECTURE.md         # This file
├── CONTRIBUTING.md         # Contribution guidelines
└── LICENSE                 # MIT license
```

---

## Core Flow

When a user sends an address to the bot, here's what happens:

```python
# Simplified flow in bot/__main__.py

async def address_handler(message):
    address = message.text

    # 1. Check rate limits
    if not rate_limiter.can_search(user_id):
        return "Rate limit exceeded"

    # 2. Geocode address to coordinates
    lat, lng, formatted = await geocode_address(address)

    # 3. Search for restaurants via Apify
    restaurants = await search_restaurants(formatted, limit=50)

    # 4. Filter by distance (10km radius)
    nearby = filter_by_distance(restaurants, lat, lng, 10.0)

    # 5. Check DoorDash availability (concurrent)
    doordash_restaurants = await check_restaurants_for_doordash(nearby)

    # 6. Sort by distance and send results
    sorted_results = sort_by_distance(doordash_restaurants)
    await send_results(message, sorted_results)
```

---

## Module Documentation

### `bot/__init__.py`
**Purpose:** Configuration and lazy bot initialization

```python
# Loads environment variables
API_TOKEN = config("API_TOKEN")      # Telegram bot token
APIFY_TOKEN = config("APIFY_TOKEN")  # Apify API token

# Lazy initialization (bot created on first use)
def get_bot() -> aiogram.Bot
def get_dp() -> aiogram.Dispatcher
```

### `bot/__main__.py`
**Purpose:** Entry point and Telegram message handlers

**Key Functions:**
- `command_start()` — Handles /start command
- `command_help()` — Handles /help command
- `command_usage()` — Shows rate limit status
- `address_handler()` — Main handler for address messages
- `send_results()` — Formats and sends restaurant results

**To modify the bot's behavior, start here.**

### `bot/apify.py`
**Purpose:** Calls Apify to scrape Google Maps for restaurants

```python
async def search_restaurants(
    address: str,           # User's address
    limit: int = 100,       # Max results
    use_cache: bool = True  # Check cache first
) -> List[Restaurant]
```

**API Used:** `blueorion~free-google-maps-scraper-extensive`

**Important:** This API costs ~$3 per 1000 results. Results are cached for 24 hours.

### `bot/google.py`
**Purpose:** Checks Google's chooseprovider endpoint for delivery links

```python
async def get_delivery_providers(
    kgmid: str,              # Google Knowledge Graph ID
    country: str = "ca",     # Country code
    language: str = "en-CA"  # Language
) -> List[DeliveryProvider]

async def check_restaurants_for_doordash(
    restaurants: List[Restaurant],
    max_concurrent: int = 10  # Concurrent requests
) -> List[Restaurant]
```

**URL Pattern:** `https://www.google.com/viewer/chooseprovider?mid={kgmid}&orderType=1`

**Regex patterns detect:**
- DoorDash: `doordash.com/store/`
- Uber Eats: `ubereats.com/`
- SkipTheDishes: `skipthedishes.com/`

### `bot/geocoding.py`
**Purpose:** Validates addresses using Nominatim (OpenStreetMap)

```python
async def geocode_address(address: str) -> Tuple[float, float, str]
    # Returns: (latitude, longitude, formatted_address)

def simplify_address(formatted_address: str) -> str
    # Shortens "123 Main St, Neighborhood, City, Province, Postal, Country"
    # to "123 Main St, City, ON"
```

**Important:** Nominatim is free but requires a User-Agent header.

### `bot/distance.py`
**Purpose:** Distance calculations using Haversine formula

```python
def haversine_distance(lat1, lon1, lat2, lon2) -> float
    # Returns distance in kilometers

def filter_by_distance(
    restaurants: List[Restaurant],
    user_lat: float,
    user_lng: float,
    max_distance_km: float
) -> List[Restaurant]
    # Filters and sorts by distance

def sort_by_distance(restaurants: List[Restaurant]) -> List[Restaurant]
    # Sorts by distance_km field
```

### `bot/cache.py`
**Purpose:** File-based caching to reduce API costs

```python
class FileCache:
    RESTAURANT_TTL = 24   # hours
    PROVIDER_TTL = 168    # hours (7 days)
    GEOCODE_TTL = 720     # hours (30 days)

    def get_restaurants(address: str) -> Optional[List[dict]]
    def set_restaurants(address: str, restaurants: List[Restaurant])

    def get_providers(kgmid: str) -> Optional[List[dict]]
    def set_providers(kgmid: str, providers: List[DeliveryProvider])

    def get_geocode(address: str) -> Optional[dict]
    def set_geocode(address: str, lat: float, lng: float, formatted: str)

# Global instance
cache = FileCache()
```

**Cache files are stored as JSON in `.cache/` directory.**

### `bot/rate_limit.py`
**Purpose:** Prevents abuse with per-user limits

```python
class RateLimiter:
    hourly_limit = 10   # Searches per hour
    daily_limit = 30    # Searches per day

    def can_search(user_id: int) -> Tuple[bool, str]
    def start_search(user_id: int) -> bool
    def end_search(user_id: int)
    def get_usage(user_id: int) -> dict

# Global instance
rate_limiter = RateLimiter()
```

### `bot/models.py`
**Purpose:** Pydantic data models

```python
class DeliveryProvider(BaseModel):
    name: str          # "DoorDash", "Uber Eats", etc.
    url: str           # Direct ordering link

class Restaurant(BaseModel):
    name: str
    address: str
    kgmid: str         # Google Knowledge Graph ID
    place_id: str      # Google Place ID
    phone: Optional[str]
    website: Optional[str]
    rating: Optional[float]
    lat: float
    lng: float
    doordash_url: Optional[str]
    delivery_providers: List[DeliveryProvider] = []
    distance_km: Optional[float]
```

### `bot/exceptions.py`
**Purpose:** Custom exceptions with user-friendly messages

```python
class BotError(Exception):
    user_message: str  # Message shown to user

class ApifyError(BotError): ...
class ApifyQuotaExceeded(ApifyError): ...
class ApifyTimeout(ApifyError): ...
class GoogleRateLimited(BotError): ...
class InvalidAddressError(BotError): ...
class RateLimitExceeded(BotError): ...

def get_user_message(error: Exception) -> str
    # Converts any exception to user-friendly message
```

### `bot/utils.py`
**Purpose:** Helper functions

```python
def is_valid_address(text: str) -> bool
    # Basic validation (length > 10, contains digits)

def escape_markdown_v2(text: str) -> str
    # Escapes special chars for Telegram MarkdownV2
```

---

## Data Models

### Restaurant Data Flow

```
Apify Response → Restaurant Model → Cache → Filter → Results

{                           Restaurant(
  "title": "Pizza Hut",       name="Pizza Hut",
  "address": "123 Main",      address="123 Main",
  "kgmid": "/g/123",          kgmid="/g/123",
  "location": {               lat=43.65,
    "lat": 43.65,             lng=-79.38,
    "lng": -79.38             distance_km=1.5,  # Added by filter
  }                           doordash_url="..."  # Added by Google check
}                           )
```

---

## External APIs

### 1. Nominatim (Geocoding)

**Endpoint:** `https://nominatim.openstreetmap.org/search`

**Request:**
```
GET /search?q=123+Main+St+Toronto&format=json&limit=1
Headers: User-Agent: DashRadar/1.0
```

**Response:**
```json
[{
  "lat": "43.6532",
  "lon": "-79.3832",
  "display_name": "123 Main St, Toronto, ON, Canada"
}]
```

**Cost:** Free
**Rate Limit:** 1 request/second (be respectful)

### 2. Apify Google Maps Scraper

**Endpoint:** `https://api.apify.com/v2/acts/blueorion~free-google-maps-scraper-extensive/run-sync-get-dataset-items`

**Request:**
```json
POST /run-sync-get-dataset-items?token=YOUR_TOKEN
{
  "maxItems": 50,
  "mode": "slow",
  "searchTerms": ["restaurant"],
  "startingLocations": ["123 Main St, Toronto"]
}
```

**Response:** Array of restaurant objects with `kgmid`, `location`, etc.

**Cost:** ~$3 per 1000 results
**Timeout:** Up to 5 minutes

### 3. Google Chooseprovider

**Endpoint:** `https://www.google.com/viewer/chooseprovider`

**Request:**
```
GET /viewer/chooseprovider?mid=/g/123&hl=en-CA&gl=ca&orderType=1
Headers: User-Agent: Mozilla/5.0...
```

**Response:** HTML page containing delivery provider links

**Cost:** Free
**Rate Limit:** ~60 requests/minute before blocking

---

## Caching System

### Why Cache?

Without caching, every search costs money (Apify) and risks rate limiting (Google). With caching:

- Same address searched twice = 1 API call instead of 2
- Same restaurant checked twice = 1 Google request instead of 2
- **~90% cost reduction** for repeat searches

### Cache Structure

```
.cache/
├── restaurants/
│   └── a1b2c3d4e5f6.json    # SHA256(address)[:16]
├── providers/
│   └── f6e5d4c3b2a1.json    # SHA256(kgmid)[:16]
└── geocode/
    └── 1a2b3c4d5e6f.json    # SHA256(address)[:16]
```

### Cache File Format

```json
{
  "cached_at": "2024-01-15T10:30:00",
  "key": "original_key_value",
  "value": { ... }
}
```

### TTL (Time To Live)

| Cache Type | TTL | Reason |
|------------|-----|--------|
| Restaurants | 24 hours | Restaurants change rarely |
| Providers | 7 days | Delivery partnerships are stable |
| Geocode | 30 days | Addresses don't move |

---

## Error Handling

### Exception Hierarchy

```
Exception
└── BotError (base class)
    ├── ApifyError
    │   ├── ApifyQuotaExceeded
    │   ├── ApifyTimeout
    │   └── ApifyRateLimited
    ├── GoogleError
    │   └── GoogleRateLimited
    ├── InvalidAddressError
    ├── RateLimitExceeded
    ├── NoResultsError
    └── NetworkError
```

### Error Messages

Each exception has two messages:
1. **Technical message** — For logs
2. **User message** — Shown to the user

```python
class ApifyTimeout(ApifyError):
    def __init__(self):
        super().__init__(
            "Apify actor timeout",  # Logged
            "Search is taking too long. Try a more specific address."  # Shown to user
        )
```

---

## Testing

### Running Tests

```bash
source venv/bin/activate
python -m pytest tests/ -v
```

### Test Coverage

| Module | Tests | Coverage |
|--------|-------|----------|
| cache.py | 11 | Full |
| distance.py | 14 | Full |
| geocoding.py | 11 | Utilities only |
| google.py | 5 | Regex patterns |
| models.py | 4 | Full |
| rate_limit.py | 11 | Full |
| utils.py | 5 | Full |

### Adding Tests

Tests are in `tests/` directory. Each module has a corresponding test file:

```python
# tests/test_example.py
import pytest
from bot.example import some_function

class TestSomeFunction:
    def test_basic_case(self):
        result = some_function("input")
        assert result == "expected"

    def test_edge_case(self):
        with pytest.raises(ValueError):
            some_function("")
```

---

## Common Tasks

### Adding a New Delivery Provider

1. Edit `bot/google.py`
2. Add a new regex pattern:
```python
NEWPROVIDER_PATTERN = re.compile(r'https?://(?:www\.)?newprovider\.com/[^"\'>\s]+')
```
3. Add extraction in `get_delivery_providers()`:
```python
newprovider_matches = NEWPROVIDER_PATTERN.findall(html)
if newprovider_matches:
    providers.append(DeliveryProvider(
        name="NewProvider",
        url=newprovider_matches[0]
    ))
```

### Changing the Search Radius

Edit `bot/__main__.py`:
```python
DEFAULT_RADIUS_KM = 10.0  # Change this value
```

### Modifying Rate Limits

Edit `bot/rate_limit.py`:
```python
class RateLimiter:
    def __init__(
        self,
        hourly_limit: int = 10,  # Change these
        daily_limit: int = 30
    ):
```

### Adding a New Telegram Command

Edit `bot/__main__.py`:
```python
@dp.message(Command("newcommand"))
async def command_new(message: types.Message) -> None:
    await message.reply("Response text")
```

### Clearing the Cache

```python
from bot.cache import cache

# Clear all
cache.clear()

# Clear specific type
cache.clear("restaurants")
cache.clear("providers")
cache.clear("geocode")
```

Or delete files manually:
```bash
rm -rf .cache/*
```

---

## Deployment Notes

### Environment Variables

Required:
- `API_TOKEN` — Telegram bot token
- `APIFY_TOKEN` — Apify API token

### Production Considerations

1. **Use Redis** instead of file cache for multi-instance deployments
2. **Use webhooks** instead of polling for better scalability
3. **Add monitoring** for API costs and error rates
4. **Set up logging** to a service like Datadog or CloudWatch

---

## Troubleshooting

### "No restaurants found"
- Check if address is valid (try geocoding manually)
- Check Apify API quota
- Check cache isn't corrupted

### "Apify timeout"
- Apify actor takes up to 5 minutes
- Try a more specific address
- Check Apify dashboard for actor status

### "Google rate limited"
- Wait 5-10 minutes
- Reduce concurrent requests in `google.py`
- Check if IP is blocked

### Markdown parsing errors
- Check `escape_markdown_v2()` is called on all user-facing text
- Use the plain text fallback in `send_results()`

---

*This document was written for LLM-assisted development. If you're using Claude Code, Cursor, or similar tools, you can reference this document when making changes to the codebase.*
