"""JSON-based knowledge store — with path traversal protection."""
import json
from pathlib import Path
from ..config import KNOWLEDGE_DIR
from ..security import validate_topic, validate_path


def _safe_path(topic: str) -> Path:
    """Get a validated path for a topic, blocking traversal attacks."""
    safe_topic = validate_topic(topic)
    return validate_path(KNOWLEDGE_DIR, f"{safe_topic}.json")


def load_knowledge(topic: str) -> str:
    path = _safe_path(topic)
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
    path = _safe_path(topic)
    with open(path, "w") as f:
        json.dump(content, f, indent=2)


def append_knowledge(topic: str, entry: str):
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    path = _safe_path(topic)
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
