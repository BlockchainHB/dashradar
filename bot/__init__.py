import logging

import aiogram

from decouple import config
from dotenv import load_dotenv, find_dotenv


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

load_dotenv(find_dotenv())

API_TOKEN = config("API_TOKEN", default="")
APIFY_TOKEN = config("APIFY_TOKEN", default="")

# Lazy initialization - only create bot/dp when actually needed
_bot = None
_dp = None


def get_bot():
    global _bot
    if _bot is None:
        _bot = aiogram.Bot(token=API_TOKEN)
    return _bot


def get_dp():
    global _dp
    if _dp is None:
        _dp = aiogram.Dispatcher()
    return _dp


