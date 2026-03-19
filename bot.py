"""
Apartment Notifier Bot — entry point.
Run with: python bot.py
"""

import asyncio
import logging

from telegram import Bot

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, NOTIFY_TIMES
from core.scheduler import run_scheduler
from telegram.constants import ParseMode

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)


async def main():
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    me  = await bot.get_me()
    log.info(f"Started as @{me.username}")

    times_str = ", ".join(f"{h:02d}:{m:02d}" for h, m in NOTIFY_TIMES)
    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=f"✅ *Bostadsbot igång\\!\nKollar kl: {times_str}*",
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    await run_scheduler(bot)


if __name__ == "__main__":
    asyncio.run(main())