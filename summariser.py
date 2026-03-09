from datetime import datetime

from openai import OpenAI

from config import CATEGORIES, PUBLICAI_API_KEY, PUBLICAI_BASE_URL, PUBLICAI_MODEL


SYSTEM_PROMPT = """\
You are a TLDR news editor. Pick the 3-5 most important, distinct stories from the raw items. \
Be extremely concise — each summary must be ONE short sentence, max 15 words. \
No fluff, no filler, no editorialising. Just the core fact.

Output ONLY the items, no preamble. Use this exact format:
• **Headline** — One-sentence summary. [Link](url)
"""

CATEGORY_INSTRUCTIONS = {
    "ai_conflicts": (
        "IMPORTANT: Only pick stories where AI/technology directly intersects with "
        "geopolitics, warfare, conflicts, or international disputes. "
        "Ignore stories that are purely about AI or purely about conflicts. "
        "If no stories match this intersection, say '_No relevant stories today._'"
    ),
}

client = OpenAI(
    api_key=PUBLICAI_API_KEY,
    base_url=PUBLICAI_BASE_URL,
    default_headers={"User-Agent": "affairsbot/1.0"},
)


def summarise_category(category_key: str, items: list[dict]) -> str:
    """Use PublicAI to summarise raw news items into a clean digest section."""
    if not items:
        return "_No recent items found._"

    raw_text = "\n\n".join(
        f"Title: {item['title']}\nSource: {item['source']}\nLink: {item['link']}\nSnippet: {item['summary']}"
        for item in items[:15]
    )

    extra = CATEGORY_INSTRUCTIONS.get(category_key, "")
    prompt = f"Category: {CATEGORIES[category_key]}\n{extra}\n\nRaw items:\n{raw_text}"

    try:
        response = client.chat.completions.create(
            model=PUBLICAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"_Summarisation failed: {e}_"


def build_digest(all_news: dict[str, list[dict]]) -> str:
    """Build the full formatted digest message."""
    sections: list[str] = []

    for category_key, label in CATEGORIES.items():
        items = all_news.get(category_key, [])
        summary = summarise_category(category_key, items)
        sections.append(f"{label}\n\n{summary}")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M %Z")
    header = "📰 *Daily News Digest*\n"
    footer = f"\n\n🕐 _Generated: {timestamp}_"

    return header + "\n\n---\n\n".join(sections) + footer
