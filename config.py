import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Singapore")
# LLM provider (OpenAI-compatible; currently OpenRouter free tier).
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "openrouter/free")

RSS_FEEDS = {
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
}

CATEGORIES = {
    "geopolitics": "🌍 Geopolitics",
    "science": "🔬 Science",
    "tech": "💻 Tech",
    "business": "💰 Business & Economy",
    "sg_policy": "🇸🇬 Singapore Public Policy",
    "hackathon_sg": "🚀 Hackathons (Singapore)",
}
