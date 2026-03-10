import re
from datetime import datetime

from openai import OpenAI

from config import CATEGORIES, PUBLICAI_API_KEY, PUBLICAI_BASE_URL, PUBLICAI_MODEL


SYSTEM_PROMPT = """\
You are a TLDR news editor. Group ALL the raw items by common theme, then summarise each item under its theme.

Rules:
- Identify 2-4 natural themes from the stories (e.g. "Middle East tensions", "Trade & tariffs", "AI regulation").
- Theme headers: use a short bold label, max 4 words.
- Under each theme, list every relevant story as a bullet.
- Headline: max 6 words. DO NOT copy the article title. Write your own punchy short headline.
- Summary: one sentence, max 12 words. Add context the headline doesn't already give.
- Every bullet MUST end with a markdown link from the raw item's Link field. Never fabricate URLs.
- If a story doesn't fit any theme, group it under "Other".
- No fluff, no filler, no editorialising. Just the core fact.

Output ONLY the grouped bullets, no preamble. Follow this format EXACTLY:

**Trade & tariffs**
• **EU hits back** — Retaliatory tariffs on US goods take effect Monday. [Link](https://example.com)
• **China export curbs** — Beijing restricts rare earth exports to US firms. [Link](https://example.com)

**Middle East tensions**
• **Iran talks stall** — Nuclear negotiations collapse after new sanctions. [Link](https://example.com)
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


def _sanitize_telegram_markdown(text: str) -> str:
    """Fix common Telegram Markdown issues from LLM output."""
    # Fix unclosed bold markers: ensure ** come in pairs
    parts = text.split("**")
    if len(parts) % 2 == 0:  # Odd number of ** means one is unclosed
        text = "**".join(parts[:-1]) + parts[-1]

    # Fix unclosed italic markers (standalone _ not inside links/words)
    # Count _ that are not part of URLs or __
    segments = re.split(r'(\[.*?\]\(.*?\))', text)  # Preserve markdown links
    for i, seg in enumerate(segments):
        if seg.startswith('[') and '](' in seg:
            continue  # Skip link segments
        underscores = [m.start() for m in re.finditer(r'(?<!\w)_(?!\w)|(?<=\w)_(?!\w)|(?<!\w)_(?=\w)', seg)]
        if len(underscores) % 2 != 0:
            # Remove the last unpaired underscore
            seg = seg[:underscores[-1]] + seg[underscores[-1] + 1:]
            segments[i] = seg
    text = "".join(segments)

    # Fix malformed links: [text](url  missing closing paren
    text = re.sub(r'\[([^\]]*)\]\(([^)]*?)(?:\s*$|\s*\n)', r'[\1](\2)\n', text)

    return text


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
        return _sanitize_telegram_markdown(response.choices[0].message.content.strip())
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
