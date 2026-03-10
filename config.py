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
    "geopolitics": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://feeds.reuters.com/reuters/worldNews",
    ],
    "science": [
        "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml",
        "https://www.newscientist.com/section/news/feed/",
        "https://www.nature.com/nature.rss",
    ],
    "tech": [
        "https://feeds.bbci.co.uk/news/technology/rss.xml",
        "https://www.theverge.com/rss/index.xml",
        "https://feeds.arstechnica.com/arstechnica/technology-lab",
    ],
    "business": [
        "https://feeds.bbci.co.uk/news/business/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
        "https://feeds.reuters.com/reuters/businessNews",
        "https://www.ft.com/rss/home",
    ],
    "sg_policy": [
        "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6511",
        "https://www.straitstimes.com/news/singapore/rss.xml",
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
    "geopolitics": "🌍 Geopolitics",
    "science": "🔬 Science",
    "tech": "💻 Tech",
    "business": "💰 Business & Economy",
    "sg_policy": "🇸🇬 Singapore Public Policy",
    "ai_conflicts": "⚔️ AI in Current Affairs & Conflicts",
}
