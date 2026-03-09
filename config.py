import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Singapore")
PUBLICAI_API_KEY = os.getenv("PUBLICAI_API_KEY", "")
PUBLICAI_BASE_URL = os.getenv("PUBLICAI_BASE_URL", "https://api.publicai.co/v1")
PUBLICAI_MODEL = os.getenv("PUBLICAI_MODEL", "molmo")

RSS_FEEDS = {
    "ai_general": [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://www.technologyreview.com/feed/",
        "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "https://the-decoder.com/feed/",
    ],
    "ai_dev": [
        "http://export.arxiv.org/rss/cs.AI",
        "http://export.arxiv.org/rss/cs.LG",
        "https://huggingface.co/blog/feed.xml",
        "https://simonwillison.net/atom/everything/",
    ],
    "current_affairs": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://feeds.reuters.com/reuters/worldNews",
        "https://www.aljazeera.com/xml/rss/all.xml",
    ],
    "ai_conflicts": [
        "https://feeds.bbci.co.uk/news/technology/rss.xml",
        "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
    ],
}

CATEGORIES = {
    "ai_general": "🤖 General AI Developments",
    "ai_dev": "👨‍💻 AI for Developers & Researchers",
    "current_affairs": "🌍 Current Affairs & Geopolitics",
    "ai_conflicts": "⚔️ AI in Current Affairs & Conflicts",
}
