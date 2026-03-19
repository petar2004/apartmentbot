"""
scrapers/booli.py — Scrapes Booli search results using a headless browser.

Strategy:
  1. Load the search page with Playwright (handles JS rendering + cookie banners)
  2. Scroll to trigger lazy-loaded content
  3. Collect all /annons/ links — the listing ID is the number in the URL
  4. Enrich each listing with title, price and image from the card elements
"""

import logging
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from playwright.async_api import async_playwright

log = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


def _fix_url(url: str) -> str:
    """Re-encode the URL to ensure commas and special chars are properly escaped."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    fixed_query = urlencode({k: v[0] for k, v in params.items()})
    return urlunparse(parsed._replace(query=fixed_query))


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
                log.info(f"Booli: dismissed cookie banner ({sel})")
                return
        except Exception:
            continue


async def fetch_booli(url: str) -> list[dict]:
    """Return a list of listing dicts from a Booli search URL."""
    listings = []
    fixed_url = _fix_url(url)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(locale="sv-SE", user_agent=USER_AGENT)
            page    = await context.new_page()

            try:
                await page.goto(fixed_url, wait_until="domcontentloaded", timeout=30000)
                await _dismiss_cookies(page)
                # Scroll to trigger any lazy-loaded listing cards
                await page.evaluate("window.scrollTo(0, 600)")
                await page.wait_for_timeout(4000)

                # ── Step 1: collect all /annons/ hrefs ──
                hrefs = await page.evaluate("""() => {
                    return Array.from(document.querySelectorAll('a[href*="/annons/"]'))
                        .map(a => a.href)
                        .filter(h => h.includes('booli.se'));
                }""")
                log.info(f"Booli: found {len(hrefs)} /annons/ links")
                if hrefs:
                    log.info(f"Booli: sample hrefs: {hrefs[:2]}")

                seen_ids: set[str] = set()
                for href in hrefs:
                    m = re.search(r'/annons/(\d+)', href)
                    if not m:
                        continue
                    lid = m.group(1)
                    if lid in seen_ids:
                        continue
                    seen_ids.add(lid)
                    listings.append({
                        "id":     f"booli_{lid}",
                        "source": "Booli 🔵",
                        "title":  f"Booli annons {lid}",   # enriched below
                        "url":    href,
                        "desc":   "",
                        "image":  None,
                    })

                # ── Step 2: enrich with title/price/image ──
                if listings:
                    listing_by_id = {lst["id"]: lst for lst in listings}
                    cards = await page.query_selector_all(
                        "a[href*='/annons/'], "
                        "[class*='SearchResult'] li, "
                        "[class*='listing'], "
                        "article"
                    )
                    for card in cards:
                        try:
                            link_el = await card.query_selector("a[href*='/annons/']") or card
                            href    = await link_el.get_attribute("href") or ""
                            m       = re.search(r'/annons/(\d+)', href)
                            if not m:
                                continue
                            lid     = m.group(1)
                            listing = listing_by_id.get(f"booli_{lid}")
                            if not listing:
                                continue

                            for sel in ["[class*='address']", "[class*='Address']", "h2", "h3", "p"]:
                                el = await card.query_selector(sel)
                                if el:
                                    t = (await el.inner_text()).strip()
                                    if t and len(t) > 3:
                                        listing["title"] = t
                                        break

                            for sel in ["[class*='price']", "[class*='Price']"]:
                                el = await card.query_selector(sel)
                                if el:
                                    listing["desc"] = (await el.inner_text()).strip()
                                    break

                            img = await card.query_selector("img")
                            if img:
                                listing["image"] = await img.get_attribute("src")

                        except Exception:
                            continue

            except Exception as e:
                log.warning(f"Booli page error: {e}")
            finally:
                try:
                    await browser.close()
                except Exception:
                    pass

    except Exception as e:
        log.warning(f"Booli playwright error: {e}")

    log.info(f"Booli: returning {len(listings)} listings")
    return listings