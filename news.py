import re

import feedparser
import httpx
from datetime import datetime, timedelta, timezone


def _strip_html(text: str) -> str:
    """Remove HTML tags and decode common entities."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", text).strip()

from config import RSS_FEEDS


def fetch_feed(url: str, max_items: int = 10, cutoff_hours: int = 72) -> list[dict]:
    """Fetch and parse a single RSS feed."""
    try:
        response = httpx.get(url, timeout=15, follow_redirects=True)
        feed = feedparser.parse(response.text)
    except Exception:
        return []

    items = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=cutoff_hours)

    for entry in feed.entries[:max_items]:
        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

        if published and published < cutoff:
            continue

        items.append({
            "title": entry.get("title", "No title"),
            "link": entry.get("link", ""),
            "summary": _strip_html(entry.get("summary", ""))[:500],
            "source": feed.feed.get("title", url),
        })

    return items


def _dedup_items(items: list[dict]) -> list[dict]:
    """Remove duplicate items by URL."""
    seen: set[str] = set()
    unique: list[dict] = []
    for item in items:
        url = item.get("link", "").rstrip("/")
        if url and url in seen:
            continue
        seen.add(url)
        unique.append(item)
    return unique


PARLIAMENT_BILLS_URL = (
    "https://www.parliament.gov.sg/parliamentary-business/bills-introduced"
    "?year={year}&pageNo=1"
)


def fetch_parliament_bills(cutoff_hours: int = 168) -> list[dict]:
    """Scrape recent bills from Singapore Parliament website."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=cutoff_hours)
    year = now.year
    url = PARLIAMENT_BILLS_URL.format(year=year)

    try:
        response = httpx.get(url, timeout=15, follow_redirects=True)
        html = response.text
    except Exception:
        return []

    items = []
    # Each bill row contains a title link + introduction date
    # Pattern: <a href="/docs/default-source/bills-introduced/...pdf">Title</a>
    # and date like "06.03.2026"
    bill_blocks = re.findall(
        r'<a[^>]+href="([^"]*bills-introduced[^"]*\.pdf)"[^>]*>\s*(.*?)\s*</a>',
        html,
        re.DOTALL,
    )
    dates = re.findall(r'(\d{2}\.\d{2}\.\d{4})', html)

    for i, (pdf_path, raw_title) in enumerate(bill_blocks):
        title = _strip_html(raw_title).strip()
        if not title:
            continue

        # Parse the introduction date (first date associated with this bill)
        introduced = None
        if i < len(dates):
            try:
                introduced = datetime.strptime(dates[i], "%d.%m.%Y").replace(tzinfo=timezone.utc)
            except ValueError:
                pass

        if introduced and introduced < cutoff:
            continue

        link = pdf_path if pdf_path.startswith("http") else f"https://www.parliament.gov.sg{pdf_path}"
        items.append({
            "title": f"[Bill] {title}",
            "link": link,
            "summary": f"Bill introduced in Singapore Parliament on {dates[i] if i < len(dates) else 'unknown date'}.",
            "source": "Parliament of Singapore",
        })

    return items


CATEGORY_CUTOFF_HOURS: dict[str, int] = {
    "sg_policy": 168,  # 7 days
    "ai_conflicts": 168,  # 7 days
}
DEFAULT_CUTOFF_HOURS = 72  # 3 days


def fetch_all_news() -> dict[str, list[dict]]:
    """Fetch news from all RSS feeds, grouped by category."""
    all_news: dict[str, list[dict]] = {}

    for category, feeds in RSS_FEEDS.items():
        cutoff = CATEGORY_CUTOFF_HOURS.get(category, DEFAULT_CUTOFF_HOURS)
        items: list[dict] = []
        for feed_url in feeds:
            items.extend(fetch_feed(feed_url, cutoff_hours=cutoff))
        if category == "sg_policy":
            items.extend(fetch_parliament_bills(cutoff_hours=cutoff))
        all_news[category] = _dedup_items(items)

    return all_news
