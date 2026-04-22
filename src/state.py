import json
from pathlib import Path

STATE_FILE = Path(__file__).parent.parent / "state" / "last_seen.json"


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"processed_urls": []}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def is_processed(url: str) -> bool:
    state = load_state()
    return url in state["processed_urls"]


def mark_processed(url: str) -> None:
    state = load_state()
    if url not in state["processed_urls"]:
        state["processed_urls"].append(url)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
