"""
scrapers/hemnet.py — Scrapes Hemnet search results using a headless browser.

Strategy:
  1. Load the search page with Playwright (handles JS rendering + cookie banners)
  2. Collect all /bostad/ links — the listing ID is the last 5+ digit number in the URL
  3. Enrich each listing with title, price and image from the card elements
"""

import logging
import re

from playwright.async_api import async_playwright

log = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


async def _dismiss_cookies(page):
    """Click away cookie/consent banners common on Swedish sites."""
    selectors = [
        "button[id*='accept']",
        "button[class*='accept']",
        "button[class*='consent']",
        "button:has-text('Godkänn alla')",
        "button:has-text('Acceptera alla')",
        "button:has-text('Acceptera')",
        "button:has-text('Godkänn')",
        "button:has-text('OK')",
        "[id*='cookie'] button",
        "[class*='cookie'] button",
        "[class*='consent'] button",
    ]
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=1000):
                await btn.click()
                await page.wait_for_timeout(500)
                log.info(f"Hemnet: dismissed cookie banner ({sel})")
                return
        except Exception:
            continue


def _extract_id(href: str) -> str | None:
    """
    Extract the Hemnet listing ID from a URL.
    URLs look like: /bostad/lagenhet-4rum-lund-21653043
    The ID is the last sequence of 5+ digits.
    """
    # Try the pattern: last big number at end of path
    m = re.search(r'-(\d{5,})(?:\?|#|$)', href)
    if m:
        return m.group(1)
    # Fallback: last 5+ digit number anywhere
    nums = re.findall(r'(\d{5,})', href)
    return nums[-1] if nums else None


async def fetch_hemnet(url: str) -> list[dict]:
    """Return a list of listing dicts from a Hemnet search URL."""
    listings = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(locale="sv-SE", user_agent=USER_AGENT)
        page    = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await _dismiss_cookies(page)

            # Wait for listing links to appear in the DOM
            try:
                await page.wait_for_selector("a[href*='/bostad/']", timeout=12000)
            except Exception:
                pass
            await page.wait_for_timeout(2000)

            # ── Step 1: collect all /bostad/ hrefs ──
            hrefs = await page.evaluate("""() => {
                return Array.from(document.querySelectorAll('a[href*="/bostad/"]'))
                    .map(a => a.href)
                    .filter(h => h.includes('hemnet.se'));
            }""")
            log.info(f"Hemnet: found {len(hrefs)} /bostad/ links")

            seen_ids: set[str] = set()
            for href in hrefs:
                lid = _extract_id(href)
                if not lid or lid in seen_ids:
                    continue
                seen_ids.add(lid)
                listings.append({
                    "id":     f"hemnet_{lid}",
                    "source": "Hemnet 🟢",
                    "title":  f"Hemnet annons {lid}",   # enriched below
                    "url":    href,
                    "desc":   "",
                    "image":  None,
                })

            # ── Step 2: enrich with title/price/image from card elements ──
            if listings:
                cards = await page.query_selector_all(
                    "[data-testid='result-list-item'], "
                    "[class*='ListingCard'], "
                    "[class*='listing-card']"
                )
                log.info(f"Hemnet: enriching from {len(cards)} card elements")

                # Build a lookup for quick matching
                listing_by_id = {lst["id"]: lst for lst in listings}

                for card in cards:
                    try:
                        link_el = await card.query_selector("a[href*='/bostad/']")
                        if not link_el:
                            continue
                        href = await link_el.get_attribute("href") or ""
                        lid  = _extract_id(href)
                        if not lid:
                            continue

                        listing = listing_by_id.get(f"hemnet_{lid}")
                        if not listing:
                            continue

                        # Title
                        for sel in ["[class*='address']", "[class*='Address']", "h2", "h3"]:
                            el = await card.query_selector(sel)
                            if el:
                                t = (await el.inner_text()).strip()
                                if t:
                                    listing["title"] = t
                                    break

                        # Price
                        for sel in ["[class*='price']", "[class*='Price']"]:
                            el = await card.query_selector(sel)
                            if el:
                                listing["desc"] = (await el.inner_text()).strip()
                                break

                        # Image
                        img = await card.query_selector("img")
                        if img:
                            listing["image"] = await img.get_attribute("src")

                    except Exception:
                        continue

        except Exception as e:
            log.warning(f"Hemnet error: {e}")
        finally:
            try:
                await browser.close()
            except Exception:
                pass

    log.info(f"Hemnet: returning {len(listings)} listings")
    return listings