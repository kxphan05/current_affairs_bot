import json
import os

SUBSCRIBERS_FILE = os.environ.get(
    "SUBSCRIBERS_FILE",
    os.path.join(os.path.dirname(__file__), "subscribers.json"),
)


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
    data[str(chat_id)] = {"time": time}
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


def get_subscriber(chat_id: int) -> dict | None:
    data = _load()
    return data.get(str(chat_id))


def get_subscribers_for_time(time_str: str) -> list[int]:
    """Return chat IDs whose delivery time matches the given HH:MM."""
    data = _load()
    return [int(cid) for cid, info in data.items() if info["time"] == time_str]
