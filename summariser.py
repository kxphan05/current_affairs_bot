from datetime import datetime

from openai import OpenAI

from config import CATEGORIES, PUBLICAI_API_KEY, PUBLICAI_BASE_URL, PUBLICAI_MODEL


SYSTEM_PROMPT = """\
You are a TLDR news editor. Pick the 3-5 most important, distinct stories from the raw items. \
Be extremely concise — each bullet must have a short headline and a single-sentence summary (max 15 words). \
No fluff, no filler, no editorialising. Just the core fact.

CRITICAL: Every bullet MUST end with a markdown link using the exact URL from the raw item's Link field. \
Never omit the link. Never fabricate a URL.

Output ONLY the bullet points, no preamble. Format each bullet exactly like this example:
• **US exits Paris accord** — Trump signs executive order withdrawing from climate agreement. [Link](https://example.com)
"""

CATEGORY_INSTRUCTIONS = {
    "sg_policy": (
        "IMPORTANT: Only pick stories about Singapore government policy, legislation, "
        "parliamentary debates, ministerial statements, regulatory changes, or public "
        "consultations. Ignore general Singapore news like crime, entertainment, sports, "
        "or human interest stories. "
        "If no stories match, say '_No relevant stories today._'"
    ),
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
        if "contentfilter" in str(e).lower() or "content_policy" in str(e).lower():
            return "_Summary unavailable — content was filtered by the API provider._"
        return f"_Summarisation failed: {e}_"


def build_digest(all_news: dict[str, list[dict]], category_keys: list[str] | None = None) -> str:
    """Build the full formatted digest message, optionally filtered to specific categories."""
    sections: list[str] = []
    keys = category_keys or list(CATEGORIES.keys())

    for category_key in keys:
        if category_key not in CATEGORIES:
            continue
        label = CATEGORIES[category_key]
        items = all_news.get(category_key, [])
        summary = summarise_category(category_key, items)
        sections.append(f"{label}\n\n{summary}")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M %Z")
    header = "📰 *Daily News Digest*\n"
    footer = f"\n\n🕐 _Generated: {timestamp}_"

    return header + "\n\n---\n\n".join(sections) + footer
