<h1 align="center">
  <br>
  <img src="readmelogo.png" alt="DashRadar" width="120">
  <br>
  DashRadar
  <br>
</h1>

<h4 align="center">A Telegram bot that discovers restaurants with DoorDash delivery using Google Maps data.</h4>

<p align="center">
  <a href="#key-features">Key Features</a> •
  <a href="#how-it-works">How It Works</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#contributing">Contributing</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/aiogram-3.x-green.svg" alt="Aiogram 3.x">
  <img src="https://img.shields.io/badge/license-MIT-orange.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome">
</p>

---

## What is DashRadar?

DashRadar is a Telegram bot that helps users discover which restaurants near them offer DoorDash delivery. Instead of manually searching through DoorDash, users simply send an address and receive a curated list of nearby restaurants with direct ordering links.

**The Problem:** DoorDash doesn't provide an easy way to see all restaurants that deliver to a specific address without signing up and browsing their app.

**The Solution:** DashRadar scrapes Google Maps to find restaurants, then checks Google's "Order Online" feature to identify which ones have DoorDash integration—all through a simple Telegram interface.

---

## Key Features

- **Address-Based Search** — Send any address, get restaurants sorted by distance
- **Smart Geocoding** — Validates and normalizes addresses using OpenStreetMap
- **Intelligent Caching** — Reduces API costs by ~90% with file-based caching
- **Rate Limiting** — Prevents abuse with per-user hourly/daily limits
- **Distance Filtering** — Only shows restaurants within 10km delivery radius
- **Concurrent Processing** — Checks multiple restaurants simultaneously for speed
- **Multiple Providers** — Also detects Uber Eats and SkipTheDishes links

---

## How It Works

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   User sends    │     │   Nominatim     │     │   Apify Google  │
│   address via   │────▶│   geocodes      │────▶│   Maps scraper  │
│   Telegram      │     │   address       │     │   finds nearby  │
└─────────────────┘     └─────────────────┘     │   restaurants   │
                                                └────────┬────────┘
                                                         │
┌─────────────────┐     ┌─────────────────┐              │
│   Results sent  │     │   Google        │◀─────────────┘
│   to user with  │◀────│   chooseprovider│
│   DoorDash links│     │   checks each   │
└─────────────────┘     └─────────────────┘
```

### Data Sources

| Source | Purpose | Cost |
|--------|---------|------|
| **Nominatim** | Address geocoding | Free |
| **Apify** | Google Maps restaurant scraping | ~$3/1000 results |
| **Google** | Delivery provider detection | Free (rate-limited) |

---

## Installation

### Prerequisites

- Python 3.11+
- Telegram Bot Token ([create one](https://core.telegram.org/bots#creating-a-new-bot))
- Apify API Token ([sign up](https://apify.com/))

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/dashradar.git
cd dashradar

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API tokens
```

### Configuration

Create a `.env` file with your credentials:

```env
API_TOKEN=your_telegram_bot_token_here
APIFY_TOKEN=your_apify_api_token_here
```

---

## Usage

### Running the Bot

```bash
source venv/bin/activate
python -m bot
```

### Telegram Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and instructions |
| `/help` | Usage guide |
| `/usage` | Check your rate limits |

### Example Interaction

```
You: 123 Queen St W, Toronto, ON

Bot: Finding DoorDash restaurants near you. This may take up to a minute...

Bot: Found 15 DoorDash restaurants near 123 Queen St W, Toronto, ON:

    Pai Northern Thai Kitchen
    0.3 km away
    18 Duncan St, Toronto, ON
    Rating: 4.6
    Order on DoorDash

    Burger King
    0.5 km away
    ...
```

---

## Architecture

```
dashradar/
├── bot/
│   ├── __init__.py      # Config and bot initialization
│   ├── __main__.py      # Telegram handlers and main flow
│   ├── apify.py         # Google Maps scraper client
│   ├── google.py        # Delivery provider detection
│   ├── geocoding.py     # Address validation (Nominatim)
│   ├── distance.py      # Haversine distance calculations
│   ├── cache.py         # File-based caching layer
│   ├── rate_limit.py    # Per-user rate limiting
│   ├── models.py        # Pydantic data models
│   ├── exceptions.py    # Custom exception classes
│   └── utils.py         # Helper functions
├── tests/               # Unit tests
├── .cache/              # Cache storage (auto-created)
├── .env                 # API credentials (not committed)
└── requirements.txt     # Python dependencies
```

### Key Components

| Module | Responsibility |
|--------|---------------|
| `apify.py` | Calls Apify actor to scrape Google Maps for restaurants |
| `google.py` | Parses Google's chooseprovider endpoint for delivery links |
| `geocoding.py` | Converts addresses to coordinates via Nominatim |
| `distance.py` | Calculates distances using Haversine formula |
| `cache.py` | File-based cache with configurable TTL |
| `rate_limit.py` | In-memory rate limiting per user |

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Caching Strategy

DashRadar uses aggressive caching to minimize API costs:

| Cache Type | TTL | Key |
|------------|-----|-----|
| Restaurants by address | 24 hours | SHA256 hash of address |
| Delivery providers | 7 days | Google Knowledge Graph ID |
| Geocoded coordinates | 30 days | SHA256 hash of address |

Cache files are stored in `.cache/` directory with JSON format.

---

## Rate Limiting

To prevent abuse and manage API costs:

| Limit | Value |
|-------|-------|
| Searches per hour | 10 per user |
| Searches per day | 30 per user |
| Concurrent searches | 1 per user |

---

## Running Tests

```bash
source venv/bin/activate
python -m pytest tests/ -v
```

All 64 tests should pass.

---

## Tech Stack

- **[aiogram 3.x](https://docs.aiogram.dev/)** — Modern async Telegram bot framework
- **[httpx](https://www.python-httpx.org/)** — Async HTTP client
- **[Pydantic](https://docs.pydantic.dev/)** — Data validation
- **[Apify](https://apify.com/)** — Web scraping platform

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Disclaimer

This project is for educational purposes. It demonstrates web scraping techniques and Telegram bot development. Please respect the terms of service of the APIs and websites used. The developers are not affiliated with DoorDash, Google, or any delivery platforms.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with Python and curiosity
  <br>
  <a href="https://github.com/BlockchainHB/dashradar">⭐ Star this repo</a> if you find it useful!
</p>
