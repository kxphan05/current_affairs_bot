import json
import os

from config import CATEGORIES

SUBSCRIBERS_FILE = os.environ.get(
    "SUBSCRIBERS_FILE",
    os.path.join(os.path.dirname(__file__), "subscribers.json"),
)

ALL_CATEGORIES = list(CATEGORIES.keys())

# Categories that replaced the old "current_affairs" umbrella
_CURRENT_AFFAIRS_REPLACEMENTS = ["geopolitics", "science", "tech", "business"]


def _migrate_categories(cats: list[str]) -> list[str]:
    """Replace legacy 'current_affairs' with the 4 new sub-categories."""
    if "current_affairs" not in cats:
        return cats
    cats = [c for c in cats if c != "current_affairs"]
    for new in _CURRENT_AFFAIRS_REPLACEMENTS:
        if new not in cats:
            cats.append(new)
    return cats


def _load() -> dict[str, dict]:
    """Load subscribers from disk. Keys are chat_id strings."""
    if not os.path.exists(SUBSCRIBERS_FILE):
        return {}
    with open(SUBSCRIBERS_FILE) as f:
        return json.load(f)


def _save(data: dict[str, dict]) -> None:
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def subscribe(chat_id: int, time: str = "08:00") -> None:
    data = _load()
    key = str(chat_id)
    if key in data:
        data[key]["time"] = time
    else:
        data[key] = {"time": time, "categories": list(ALL_CATEGORIES)}
    _save(data)


def unsubscribe(chat_id: int) -> bool:
    data = _load()
    if str(chat_id) in data:
        del data[str(chat_id)]
        _save(data)
        return True
    return False


def set_time(chat_id: int, time: str) -> bool:
    data = _load()
    key = str(chat_id)
    if key not in data:
        return False
    data[key]["time"] = time
    _save(data)
    return True


def toggle_category(chat_id: int, category: str) -> bool | None:
    """Toggle a category on/off. Returns new state, or None if not subscribed."""
    data = _load()
    key = str(chat_id)
    if key not in data:
        return None
    cats = _migrate_categories(data[key].get("categories", list(ALL_CATEGORIES)))
    if category in cats:
        cats.remove(category)
    else:
        cats.append(category)
    data[key]["categories"] = cats
    _save(data)
    return category in cats


def get_subscriber(chat_id: int) -> dict | None:
    data = _load()
    sub = data.get(str(chat_id))
    if sub and "categories" not in sub:
        sub["categories"] = list(ALL_CATEGORIES)
    if sub:
        sub["categories"] = _migrate_categories(sub["categories"])
    return sub


def has_set_categories(chat_id: int) -> bool:
    """Check if a subscriber has explicitly set their categories."""
    data = _load()
    sub = data.get(str(chat_id))
    return sub is not None and "categories" in sub


def mark_categories_prompted(chat_id: int) -> None:
    """Mark that we've prompted this user to set categories, by writing the default."""
    data = _load()
    key = str(chat_id)
    if key in data and "categories" not in data[key]:
        data[key]["categories"] = list(ALL_CATEGORIES)
        _save(data)


def get_subscribers_for_time(time_str: str) -> list[tuple[int, list[str]]]:
    """Return (chat_id, categories) for subscribers whose delivery time matches."""
    data = _load()
    result = []
    for cid, info in data.items():
        if info["time"] == time_str:
            cats = _migrate_categories(info.get("categories", list(ALL_CATEGORIES)))
            if cats:
                result.append((int(cid), cats))
    return result
