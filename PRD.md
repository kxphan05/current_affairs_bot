Build a Telegram bot that sends me daily news digests across four categories. Here are the full requirements:
Core functionality
The bot should send a daily digest message to a specified Telegram chat ID. The digest should be divided into four clearly labelled sections:

General AI developments and announcements
AI developments specifically for developers and researchers (papers, tools, frameworks, APIs, benchmarks)
Current affairs and geopolitical news
AI applications in current affairs and conflicts

How it should work

Use a news aggregation approach — either via web search (Tavily or Serper API) or RSS feeds from relevant sources (e.g. TechCrunch AI, ArXiv, Reuters, BBC, MIT Tech Review)
For each category, surface 3 to 5 items with a headline, one to two sentence summary, and source link
Send the digest once daily at a time I can configure
Use the Llama3.2 model on ollama to summarise and categorise the raw news into clean, readable digest format before sending, and include links to articles if possible.

Tech stack

Python
python-telegram-bot library for Telegram integration
APScheduler or a simple cron approach for daily scheduling
A .env file for storing API keys (Telegram bot token, news API key if used)
Keep it simple and runnable locally — no need for a hosted server

Project structure
Organise into clear files: main.py for the entry point, bot.py for Telegram logic, news.py for fetching and processing news, summariser.py for the Claude API call, config.py for settings, and a .env template.
Output format for the Telegram message
Use clean formatting with emoji section headers so it is readable on mobile. Each news item should be a short punchy summary, not a wall of text. End each digest with a timestamp of when it was generated.
Please scaffold the full project, install dependencies using uv, and walk me through how to set up the .env file.