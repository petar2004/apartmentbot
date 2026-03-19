"""
core/scheduler.py — Runs the apartment check at configured times each day.
"""

import asyncio
import logging
from datetime import datetime, time

from telegram import Bot

from config import HEMNET_SEARCH_URLS, BOOLI_SEARCH_URLS, NOTIFY_TIMES
from core.storage import load_seen, save_seen
from core.notifier import send_listings
from scrapers.hemnet import fetch_hemnet
from scrapers.booli import fetch_booli

log = logging.getLogger(__name__)


async def _check_and_notify(bot: Bot):
    """Fetch all sources, find new listings, send them, save state."""
    log.info("Running apartment check...")
    seen         = load_seen()
    new_listings = []

    for url in HEMNET_SEARCH_URLS:
        for listing in await fetch_hemnet(url):
            if listing["id"] not in seen:
                new_listings.append(listing)
                seen.add(listing["id"])

    for url in BOOLI_SEARCH_URLS:
        for listing in await fetch_booli(url):
            if listing["id"] not in seen:
                new_listings.append(listing)
                seen.add(listing["id"])

    save_seen(seen)

    if new_listings:
        await send_listings(bot, new_listings)
    else:
        log.info("No new listings found.")


async def run_scheduler(bot: Bot):
    """Loop forever, firing _check_and_notify at each configured time."""
    notify_times = [time(h, m) for h, m in NOTIFY_TIMES]
    log.info(f"Scheduler active. Will notify at: {[str(t) for t in notify_times]}")

    fired_today: set = set()

    while True:
        now     = datetime.now()
        current = time(now.hour, now.minute)

        for t in notify_times:
            key = (now.date(), t)
            if current >= t and key not in fired_today:
                fired_today.add(key)
                await _check_and_notify(bot)

        # Drop keys from previous days to avoid memory growth
        today       = now.date()
        fired_today = {k for k in fired_today if k[0] == today}

        await asyncio.sleep(30)