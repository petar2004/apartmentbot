"""
core/storage.py — Tracks which listing IDs have already been sent
so we never notify about the same apartment twice.
"""

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

SEEN_FILE = Path("data/seen_listings.json")


def load_seen() -> set:
    """Load the set of already-seen listing IDs from disk."""
    if SEEN_FILE.exists():
        try:
            content = SEEN_FILE.read_text().strip()
            if content:
                return set(json.loads(content))
        except (json.JSONDecodeError, ValueError):
            log.warning("seen_listings.json was corrupt — resetting.")
    return set()


def save_seen(seen: set):
    """Persist the set of seen IDs to disk."""
    SEEN_FILE.parent.mkdir(exist_ok=True)
    SEEN_FILE.write_text(json.dumps(sorted(seen), indent=2))