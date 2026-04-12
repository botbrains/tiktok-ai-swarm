"""TikTok API client — Content Posting API + Live streaming.

TikTok API docs: https://developers.tiktok.com/doc/content-posting-api-get-started

Requirements:
1. Register as a TikTok developer
2. Create an app and get client_key + client_secret
3. Complete OAuth2 flow to get access_token
4. Your app must be approved for Content Posting API access
"""
import httpx
from ..config import load_config

BASE_URL = "https://open.tiktokapis.com/v2"


def _headers() -> dict:
    cfg = load_config()
    token = cfg.get("tiktok_access_token", "")
    if not token:
        raise RuntimeError("TikTok access token not configured. Run: tt auth")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def get_auth_url() -> str:
    """Generate the OAuth2 authorization URL."""
    cfg = load_config()
    client_key = cfg.get("tiktok_client_key", "")
    if not client_key:
        return "[ERROR] tiktok_client_key not set. Run: tt setup"

    scopes = "user.info.basic,video.publish,video.upload,video.list"
    redirect_uri = "https://localhost:3000/callback"

    return (
        f"https://www.tiktok.com/v2/auth/authorize/"
        f"?client_key={client_key}"
        f"&scope={scopes}"
        f"&response_type=code"
        f"&redirect_uri={redirect_uri}"
    )


def exchange_code(code: str) -> dict:
    """Exchange authorization code for access token."""
    cfg = load_config()
    payload = {
        "client_key": cfg.get("tiktok_client_key", ""),
        "client_secret": cfg.get("tiktok_client_secret", ""),
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": "https://localhost:3000/callback",
    }
    resp = httpx.post(f"{BASE_URL}/oauth/token/", json=payload, timeout=30.0)
    resp.raise_for_status()
    return resp.json()


def init_video_upload(video_size: int) -> dict:
    """Initialize a video upload to get an upload URL.

    Returns: {"upload_url": "...", "publish_id": "..."}
    """
    payload = {
        "post_info": {
            "title": "",
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": video_size,
            "chunk_size": video_size,
            "total_chunk_count": 1,
        },
    }

    resp = httpx.post(
        f"{BASE_URL}/post/publish/inbox/video/init/",
        json=payload,
        headers=_headers(),
        timeout=30.0,
    )
    resp.raise_for_status()
    data = resp.json()["data"]
    return {"upload_url": data["upload_url"], "publish_id": data["publish_id"]}


def upload_video(upload_url: str, video_path: str) -> str:
    """Upload a video file to TikTok's upload URL."""
    from pathlib import Path

    video_bytes = Path(video_path).read_bytes()
    headers = {
        "Content-Range": f"bytes 0-{len(video_bytes) - 1}/{len(video_bytes)}",
        "Content-Type": "video/mp4",
    }

    resp = httpx.put(upload_url, content=video_bytes, headers=headers, timeout=120.0)
    resp.raise_for_status()
    return "Upload complete"


def publish_video(publish_id: str, title: str, hashtags: list[str] = None) -> dict:
    """Publish an uploaded video with title and hashtags."""
    caption = title
    if hashtags:
        caption += " " + " ".join(f"#{h.strip('#')}" for h in hashtags)

    payload = {
        "publish_id": publish_id,
        "post_info": {
            "title": caption[:2200],  # TikTok caption limit
            "privacy_level": "PUBLIC_TO_EVERYONE",
        },
    }

    resp = httpx.post(
        f"{BASE_URL}/post/publish/status/fetch/",
        json=payload,
        headers=_headers(),
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()


def get_videos(max_count: int = 20) -> dict:
    """List published videos."""
    payload = {"max_count": max_count}
    resp = httpx.post(
        f"{BASE_URL}/video/list/",
        json=payload,
        headers=_headers(),
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()
