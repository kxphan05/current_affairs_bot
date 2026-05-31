import re
from datetime import datetime

from openai import OpenAI

from config import CATEGORIES, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL


SYSTEM_PROMPT = """\
You are a TLDR news editor. Group the raw items by common theme, then summarise each item under its theme.

FILTERING — skip these entirely, do NOT include them:
- Advertisements, deals, discounts, giveaways, or promotions
- Product reviews or buyer's guides
- Duplicate stories (if multiple articles cover the same event, pick the best one)
- Clickbait or trivial stories with no real news value

STRUCTURE:
- Maximum 3 themes. Pick the 3 most newsworthy.
- Maximum 3 bullets per theme. Pick the most important.
- Theme headers: short bold label, max 4 words.

FORMAT:
- Headline: max 6 words. DO NOT copy the article title. Write your own punchy short headline.
- Summary: one sentence, max 12 words. Add context the headline doesn't already give.
- Every bullet MUST end with a markdown link from the raw item's Link field. Never fabricate URLs.
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
        "Include any story relevant to life in Singapore — policy, economy, housing, "
        "transport, healthcare, education, cost of living, jobs, infrastructure, "
        "government announcements, court rulings, or major local developments. "
        "Be generous — if it affects Singaporeans, include it. "
        "Only skip pure entertainment, celebrity gossip, and sports results."
    ),
    "ai_conflicts": (
        "IMPORTANT: Only pick stories where AI/technology directly intersects with "
        "geopolitics, warfare, conflicts, or international disputes. "
        "Ignore stories that are purely about AI or purely about conflicts. "
        "If no stories match this intersection, say '_No relevant stories today._'"
    ),
}

client = OpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
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


MAX_THEMES = 3
MAX_BULLETS_PER_THEME = 3


def _trim_themes(text: str) -> str:
    """Enforce max themes and max bullets per theme on the LLM output."""
    lines = text.split("\n")
    result = []
    theme_count = 0
    bullet_count = 0

    for line in lines:
        stripped = line.strip()
        # Detect theme header: a bold line that isn't a bullet
        if stripped.startswith("**") and not stripped.startswith("• ") and stripped.endswith("**"):
            if theme_count >= MAX_THEMES:
                break
            theme_count += 1
            bullet_count = 0
            result.append(line)
        elif stripped.startswith("•"):
            if bullet_count < MAX_BULLETS_PER_THEME:
                result.append(line)
                bullet_count += 1
        else:
            # Blank lines / other content — keep for formatting
            result.append(line)

    return "\n".join(result).strip()


def summarise_category(category_key: str, items: list[dict], research_interests: str = "") -> str:
    """Use the configured LLM to summarise raw news items into a clean digest section."""
    if not items:
        return "_No recent items found._"

    raw_text = "\n\n".join(
        f"Title: {item['title']}\nSource: {item['source']}\nLink: {item['link']}\nSnippet: {item['summary']}"
        for item in items[:15]
    )

    extra = CATEGORY_INSTRUCTIONS.get(category_key, "")
    if research_interests:
        extra += (
            f"\n\nThe reader is a developer/researcher specifically interested in: "
            f"{research_interests}. Prioritise items matching these interests and "
            f"lead with them. Down-rank or skip items unrelated to these interests. "
            f"If nothing matches, say '_No items matching your interests today._'"
        )
    prompt = f"Category: {CATEGORIES[category_key]}\n{extra}\n\nRaw items:\n{raw_text}"

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content.strip()
        return _sanitize_telegram_markdown(_trim_themes(content))
    except Exception as e:
        if "contentfilter" in str(e).lower() or "content_policy" in str(e).lower():
            return "_Summary unavailable — content was filtered by the API provider._"
        return f"_Summarisation failed: {e}_"


def build_digest(
    all_news: dict[str, list[dict]],
    category_keys: list[str] | None = None,
    research_interests: str = "",
) -> str:
    """Build the full formatted digest message, optionally filtered to specific categories."""
    sections: list[str] = []
    keys = category_keys or list(CATEGORIES.keys())

    for category_key in keys:
        if category_key not in CATEGORIES:
            continue
        label = CATEGORIES[category_key]
        items = all_news.get(category_key, [])
        if category_key == "ai_dev":
            summary = summarise_category(category_key, items, research_interests)
        else:
            summary = summarise_category(category_key, items)
        sections.append(f"{label}\n\n{summary}")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M %Z")
    header = "📰 *Daily News Digest*\n"
    footer = f"\n\n🕐 _Generated: {timestamp}_"

    return header + "\n\n---\n\n".join(sections) + footer
