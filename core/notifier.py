"""
core/notifier.py — Formats and sends listings to Telegram.
"""

import logging
from datetime import datetime

from telegram import Bot
from telegram.constants import ParseMode

from config import TELEGRAM_CHAT_ID

log = logging.getLogger(__name__)


def _format(listing: dict) -> str:
    """Format a listing dict into a Telegram Markdown message."""
    title  = listing.get("title", "Okänd adress")
    desc   = listing.get("desc", "")
    url    = listing.get("url", "")
    source = listing.get("source", "")

    lines = [f"*{title}*"]
    if desc:
        lines.append(desc)
    lines.append(f"[Visa annons]({url}) · _{source}_")
    return "\n".join(lines)


async def send_listings(bot: Bot, listings: list[dict]):
    """Send a batch of new listings to the Telegram chat."""
    if not listings:
        return

    n     = len(listings)
    plural = "a" if n > 1 else ""
    intro = (
        f"🔔 *{n} ny{plural} bostad{'er' if n > 1 else ''} hittades\\!*\n"
        f"_{datetime.now().strftime('%d %b %Y, %H:%M')}_"
    )
    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=intro,
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    for listing in listings:
        text = _format(listing)
        try:
            if listing.get("image"):
                await bot.send_photo(
                    chat_id=TELEGRAM_CHAT_ID,
                    photo=listing["image"],
                    caption=text,
                    parse_mode=ParseMode.MARKDOWN,
                )
            else:
                await bot.send_message(
                    chat_id=TELEGRAM_CHAT_ID,
                    text=text,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=False,
                )
        except Exception as e:
            log.warning(f"Failed to send {listing['id']}: {e}")
            # Fallback without image
            try:
                await bot.send_message(
                    chat_id=TELEGRAM_CHAT_ID,
                    text=text,
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception:
                pass

    log.info(f"Sent {n} new listings.")