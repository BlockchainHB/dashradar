# Contributing to DashRadar

Thank you for your interest in contributing! This guide is written for developers of all skill levels, including those using LLM-assisted development tools like Claude Code or Cursor.

---

## Quick Start

```bash
# 1. Fork and clone the repository
git clone https://github.com/yourusername/dashradar.git
cd dashradar

# 2. Set up the development environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Copy environment template
cp .env.example .env
# Edit .env with your API tokens

# 4. Run tests to verify setup
python -m pytest tests/ -v

# 5. Start the bot locally
python -m bot
```

---

## Project Structure

Before making changes, familiarize yourself with the codebase:

```
bot/
├── __main__.py      # START HERE - Telegram handlers
├── apify.py         # Restaurant search (Apify API)
├── google.py        # DoorDash detection (Google scraping)
├── geocoding.py     # Address validation
├── distance.py      # Distance calculations
├── cache.py         # Caching layer
├── rate_limit.py    # Rate limiting
├── models.py        # Data models
├── exceptions.py    # Error handling
└── utils.py         # Helper functions
```

For detailed documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## For LLM-Assisted Developers

If you're using Claude Code, Cursor, GitHub Copilot, or similar tools:

### Helpful Prompts

**Understanding the codebase:**
```
Read ARCHITECTURE.md and explain how the caching system works.
```

**Making changes:**
```
I want to add a filter for restaurants with 4+ star ratings.
Read the relevant files and suggest where to make changes.
```

**Debugging:**
```
The bot is returning "No restaurants found" even though there should be results.
Help me debug by checking the geocoding and Apify modules.
```

### Key Files to Reference

When asking your AI assistant to make changes, point it to:

1. **ARCHITECTURE.md** — Comprehensive system documentation
2. **bot/models.py** — Data structures used throughout
3. **bot/exceptions.py** — Error handling patterns
4. **tests/** — Examples of expected behavior

### Testing Your Changes

Always run tests after making changes:

```bash
python -m pytest tests/ -v
```

If you add new functionality, add corresponding tests.

---

## Development Guidelines

### Code Style

- Use Python 3.11+ features
- Follow PEP 8 style guide
- Use type hints for function parameters and returns
- Use async/await for I/O operations

```python
# Good
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# Bad
def fetch_data(url):
    return requests.get(url).json()
```

### Error Handling

Always use custom exceptions from `bot/exceptions.py`:

```python
from bot.exceptions import InvalidAddressError

# Good
if not results:
    raise InvalidAddressError("Could not geocode address")

# Bad
if not results:
    raise Exception("Error")
```

### Caching

When adding new API calls, consider caching:

```python
from bot.cache import cache

# Check cache first
cached = cache.get("type", key, ttl_hours=24)
if cached:
    return cached

# Make API call
result = await api_call()

# Cache the result
cache.set("type", key, result)
return result
```

### Testing

Write tests for new functionality:

```python
# tests/test_newfeature.py
import pytest
from bot.newfeature import new_function

class TestNewFunction:
    def test_basic_usage(self):
        result = new_function("input")
        assert result == "expected"

    def test_handles_empty_input(self):
        result = new_function("")
        assert result is None

    def test_raises_on_invalid(self):
        with pytest.raises(ValueError):
            new_function(None)
```

---

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Your Changes

Edit the relevant files. Common tasks:

| Task | File(s) to Edit |
|------|-----------------|
| Add Telegram command | `bot/__main__.py` |
| Change search behavior | `bot/apify.py`, `bot/google.py` |
| Modify data models | `bot/models.py` |
| Add new API integration | Create new file in `bot/` |
| Change caching behavior | `bot/cache.py` |

### 3. Test Your Changes

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_cache.py -v

# Run with coverage
python -m pytest tests/ --cov=bot
```

### 4. Test Manually

```bash
# Start the bot
python -m bot

# In Telegram, send test messages to your bot
```

### 5. Commit and Push

```bash
git add .
git commit -m "feat: add rating filter for restaurants"
git push origin feature/your-feature-name
```

### 6. Open a Pull Request

Go to GitHub and create a pull request with:
- Clear title describing the change
- Description of what and why
- Any testing notes

---

## Ideas for Contributions

### Beginner-Friendly

- [ ] Add more delivery providers (GrubHub, Postmates)
- [ ] Add cuisine type detection from restaurant names
- [ ] Improve address simplification for different countries
- [ ] Add more unit tests

### Intermediate

- [ ] Implement result pagination with inline keyboards
- [ ] Add rating filter (only show 4+ stars)
- [ ] Export results to CSV
- [ ] Add user preferences storage

### Advanced

- [ ] Switch to Redis caching for production
- [ ] Implement webhook mode instead of polling
- [ ] Add concurrent Apify requests
- [ ] Create a web dashboard for analytics

---

## Getting Help

- **Documentation:** Read [ARCHITECTURE.md](ARCHITECTURE.md)
- **Issues:** Open a GitHub issue for bugs or questions
- **Discussions:** Use GitHub Discussions for ideas

---

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Help others learn

---

Thank you for contributing!
