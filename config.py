"""
config.py — All settings in one place. Edit this file to customise the bot.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ──────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

# ── Hemnet search URLs ────────────────────────────────────────────────────────
# Go to hemnet.se, set your filters, copy the URL from the browser.
HEMNET_SEARCH_URLS = [
    "https://www.hemnet.se/bostader?fee_max=6000&price_max=4500000&living_area_min=70&rooms_min=3&location_ids%5B%5D=17987",
]

# ── Booli search URLs ─────────────────────────────────────────────────────────
# Go to booli.se, set your filters, copy the URL from the browser.
BOOLI_SEARCH_URLS = [
    "https://www.booli.se/sok/till-salu?areaIds=116978&maxListPrice=4000000&maxRent=6000&minLivingArea=70&minRooms=3&objectType=L%C3%A4genhet,Villa,Kedjehus-Parhus-Radhus",
]

# ── Notification schedule (24h) ───────────────────────────────────────────────
NOTIFY_TIMES = [
    (7,  0),   # 07:00 morning
    (20, 0),   # 20:00 evening
]