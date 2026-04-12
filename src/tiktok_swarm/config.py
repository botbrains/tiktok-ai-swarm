"""Configuration — Ollama, TikTok API, avatar settings, scheduling."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
CALENDAR_DIR = DATA_DIR / "calendar"
VIDEOS_DIR = DATA_DIR / "videos"
ANALYTICS_DIR = DATA_DIR / "analytics"
ASSETS_DIR = DATA_DIR / "assets"

CONFIG_FILE = ROOT / "config.json"

DEFAULT_CONFIG = {
    # LLM
    "ollama_url": "http://localhost:11434",
    "model": "qwen2.5:32b",

    # TikTok API (https://developers.tiktok.com)
    "tiktok_client_key": "",
    "tiktok_client_secret": "",
    "tiktok_access_token": "",
    "tiktok_open_id": "",

    # Avatar
    "avatar_backend": "heygen",  # heygen | d-id | local | none
    "heygen_api_key": "",
    "heygen_avatar_id": "",
    "did_api_key": "",

    # Voice
    "voice_backend": "elevenlabs",  # elevenlabs | local | none
    "elevenlabs_api_key": "",
    "elevenlabs_voice_id": "",
    "local_voice_model": "tts_models/en/ljspeech/tacotron2-DDC",

    # Content identity
    "persona_name": "",
    "persona_niche": "",
    "persona_style": "",
    "persona_bio": "",
    "persona_catchphrase": "",

    # Scheduling
    "posts_per_day": 3,
    "post_times": ["09:00", "13:00", "19:00"],
    "live_schedule": ["20:00"],  # when to go live
    "live_duration_minutes": 30,
    "timezone": "America/New_York",

    # Affiliate
    "amazon_associate_tag": "",
    "linktree_url": "",

    # Safety
    "require_approval": True,  # require human approval before posting
    "auto_engage_comments": False,  # auto-reply to comments
    "max_daily_comments": 50,
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            saved = json.load(f)
        return {**DEFAULT_CONFIG, **saved}
    return DEFAULT_CONFIG.copy()


def save_config(cfg: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)
