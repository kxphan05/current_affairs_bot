import feedparser
import httpx
from datetime import datetime, timedelta, timezone

from config import RSS_FEEDS


def fetch_feed(url: str, max_items: int = 10) -> list[dict]:
    """Fetch and parse a single RSS feed."""
    try:
        response = httpx.get(url, timeout=15, follow_redirects=True)
        feed = feedparser.parse(response.text)
    except Exception:
        return []

    items = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=72)

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
            "summary": entry.get("summary", "")[:500],
            "source": feed.feed.get("title", url),
        })

    return items


def fetch_all_news() -> dict[str, list[dict]]:
    """Fetch news from all RSS feeds, grouped by category."""
    all_news: dict[str, list[dict]] = {}

    for category, feeds in RSS_FEEDS.items():
        items: list[dict] = []
        for feed_url in feeds:
            items.extend(fetch_feed(feed_url))
        all_news[category] = items

    return all_news
