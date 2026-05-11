"""Configuration — Ollama, TikTok API, avatar settings, scheduling."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
CALENDAR_DIR = DATA_DIR / "calendar"
VIDEOS_DIR = DATA_DIR / "videos"
ANALYTICS_DIR = DATA_DIR / "analytics"
ASSETS_DIR = DATA_DIR / "assets"
SHOP_DIR = DATA_DIR / "shop"

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

    # Affiliate — general
    "amazon_associate_tag": "",
    "linktree_url": "",

    # TikTok Shop / Beacons affiliate monetization
    "beacons_url": "",                     # e.g. https://beacons.ai/yourhandle
    "shop_region": "US",                   # product availability region
    "shop_max_offers_per_week": 5,
    "shop_disclosure_template": (
        "Some links are affiliate links. "
        "I earn a small commission at no extra cost to you. #ad"
    ),

    # Safety
    "require_approval": True,  # require human approval before posting
    "auto_engage_comments": False,  # auto-reply to comments
    "max_daily_comments": 50,
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            saved = json.load(f)
        cfg = {**DEFAULT_CONFIG, **saved}
    else:
        cfg = DEFAULT_CONFIG.copy()

    # Environment variable overrides — useful for secrets and deployment config.
    # Set these in your shell or a .env file (loaded externally, e.g. via
    # `export BEACONS_URL=https://beacons.ai/yourhandle` before running tt).
    _env_map = {
        "BEACONS_URL": "beacons_url",
        "SHOP_REGION": "shop_region",
        "SHOP_DISCLOSURE": "shop_disclosure_template",
        "TIKTOK_CLIENT_KEY": "tiktok_client_key",
        "TIKTOK_CLIENT_SECRET": "tiktok_client_secret",
        "TIKTOK_ACCESS_TOKEN": "tiktok_access_token",
        "HEYGEN_API_KEY": "heygen_api_key",
        "ELEVENLABS_API_KEY": "elevenlabs_api_key",
    }
    for env_var, cfg_key in _env_map.items():
        val = os.environ.get(env_var)
        if val:
            cfg[cfg_key] = val

    return cfg


def save_config(cfg: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)
