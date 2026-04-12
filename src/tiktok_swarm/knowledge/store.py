"""JSON-based knowledge store."""
import json
from pathlib import Path
from ..config import KNOWLEDGE_DIR


def load_knowledge(topic: str) -> str:
    path = KNOWLEDGE_DIR / f"{topic}.json"
    if not path.exists():
        return ""
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, list):
        return "\n".join(str(item) for item in data)
    if isinstance(data, dict):
        return json.dumps(data, indent=2)
    return str(data)


def save_knowledge(topic: str, content):
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    path = KNOWLEDGE_DIR / f"{topic}.json"
    with open(path, "w") as f:
        json.dump(content, f, indent=2)


def append_knowledge(topic: str, entry: str):
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    path = KNOWLEDGE_DIR / f"{topic}.json"
    data = []
    if path.exists():
        with open(path) as f:
            data = json.load(f)
    if not isinstance(data, list):
        data = [data]
    data.append(entry)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def list_topics() -> list[str]:
    if not KNOWLEDGE_DIR.exists():
        return []
    return [p.stem for p in KNOWLEDGE_DIR.glob("*.json")]
