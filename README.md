# 🏠 Apartment Notifier Bot

Monitors Hemnet and Booli for new listings matching your filters.
Sends Telegram notifications at 07:00 and 20:00. Never repeats a listing.

## Project structure

```
apartmentbot/
├── bot.py              # Entry point — run this
├── config.py           # Your search URLs and schedule
├── .env                # Your secrets (never commit this)
├── requirements.txt
│
├── scrapers/
│   ├── hemnet.py       # Hemnet scraper
│   └── booli.py        # Booli scraper
│
├── core/
│   ├── scheduler.py    # Runs checks at configured times
│   ├── notifier.py     # Sends listings to Telegram
│   └── storage.py      # Tracks seen listings (no duplicates)
│
└── data/
    └── seen_listings.json   # Auto-created, gitignored
```

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt
python -m playwright install chromium

# 2. Create .env file
echo "TELEGRAM_BOT_TOKEN=your_token_here" > .env
echo "TELEGRAM_CHAT_ID=your_chat_id_here" >> .env

# 3. Edit config.py — paste your Hemnet and Booli search URLs

# 4. Run
python bot.py
```

## Adding more searches

In `config.py`, just add more URLs to the lists:

```python
HEMNET_SEARCH_URLS = [
    "https://www.hemnet.se/bostader?...",   # search 1
    "https://www.hemnet.se/bostader?...",   # search 2
]

BOOLI_SEARCH_URLS = [
    "https://www.booli.se/sok/till-salu?...",
]
```

## Changing notification times

```python
NOTIFY_TIMES = [
    (7,  0),   # 07:00
    (20, 0),   # 20:00
]
```
