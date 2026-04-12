"""AI Avatar Video Generator — pluggable backends for video creation.

Supported backends:
- heygen: HeyGen API (best quality, paid)
- d-id: D-ID API (good quality, paid)
- local: Local pipeline with Wav2Lip + TTS (free, requires GPU)
- none: Script-only mode (no video generation, just scripts)
"""
import json
import time
from pathlib import Path
import httpx
from ..config import load_config, VIDEOS_DIR
from ..security import validate_filename


class AvatarBackend:
    """Base class for avatar video generation."""

    def generate(self, script: str, output_path: Path) -> str:
        raise NotImplementedError


class HeyGenBackend(AvatarBackend):
    """HeyGen API — high quality AI avatar videos."""

    def __init__(self, api_key: str, avatar_id: str):
        self.api_key = api_key
        self.avatar_id = avatar_id
        self.base_url = "https://api.heygen.com"

    def generate(self, script: str, output_path: Path) -> str:
        headers = {"X-Api-Key": self.api_key, "Content-Type": "application/json"}

        # Create video
        payload = {
            "video_inputs": [{
                "character": {
                    "type": "avatar",
                    "avatar_id": self.avatar_id,
                    "avatar_style": "normal",
                },
                "voice": {"type": "text", "input_text": script},
                "background": {"type": "color", "value": "#FFFFFF"},
            }],
            "dimension": {"width": 1080, "height": 1920},  # TikTok vertical
        }

        resp = httpx.post(
            f"{self.base_url}/v2/video/generate",
            json=payload,
            headers=headers,
            timeout=30.0,
        )
        resp.raise_for_status()
        video_id = resp.json()["data"]["video_id"]

        # Poll for completion
        for _ in range(60):  # 5 min max
            time.sleep(5)
            status_resp = httpx.get(
                f"{self.base_url}/v1/video_status.get?video_id={video_id}",
                headers=headers,
                timeout=30.0,
            )
            data = status_resp.json()["data"]
            if data["status"] == "completed":
                # Download video
                video_url = data["video_url"]
                video_resp = httpx.get(video_url, timeout=120.0)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(video_resp.content)
                return str(output_path)
            elif data["status"] == "failed":
                return f"[ERROR] HeyGen video generation failed: {data.get('error', 'unknown')}"

        return "[ERROR] HeyGen video generation timed out"


class DIDBackend(AvatarBackend):
    """D-ID API — talking head avatar videos."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.d-id.com"

    def generate(self, script: str, output_path: Path) -> str:
        headers = {
            "Authorization": f"Basic {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "script": {"type": "text", "input": script, "provider": {"type": "microsoft", "voice_id": "en-US-JennyNeural"}},
            "config": {"result_format": "mp4"},
        }

        resp = httpx.post(f"{self.base_url}/talks", json=payload, headers=headers, timeout=30.0)
        resp.raise_for_status()
        talk_id = resp.json()["id"]

        for _ in range(60):
            time.sleep(5)
            status_resp = httpx.get(f"{self.base_url}/talks/{talk_id}", headers=headers, timeout=30.0)
            data = status_resp.json()
            if data["status"] == "done":
                video_url = data["result_url"]
                video_resp = httpx.get(video_url, timeout=120.0)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(video_resp.content)
                return str(output_path)
            elif data["status"] == "error":
                return f"[ERROR] D-ID failed: {data.get('error', 'unknown')}"

        return "[ERROR] D-ID video generation timed out"


class NoVideoBackend(AvatarBackend):
    """Script-only mode — saves scripts without generating video."""

    def generate(self, script: str, output_path: Path) -> str:
        script_path = output_path.with_suffix(".txt")
        script_path.parent.mkdir(parents=True, exist_ok=True)
        script_path.write_text(script)
        return f"Script saved (no video backend configured): {script_path}"


def get_backend() -> AvatarBackend:
    """Get the configured avatar backend."""
    cfg = load_config()
    backend = cfg.get("avatar_backend", "none")

    if backend == "heygen":
        api_key = cfg.get("heygen_api_key", "")
        avatar_id = cfg.get("heygen_avatar_id", "")
        if not api_key or not avatar_id:
            return NoVideoBackend()
        return HeyGenBackend(api_key, avatar_id)

    elif backend == "d-id":
        api_key = cfg.get("did_api_key", "")
        if not api_key:
            return NoVideoBackend()
        return DIDBackend(api_key)

    return NoVideoBackend()


def generate_video(script: str, filename: str = "") -> str:
    """Generate a video from a script using the configured backend."""
    if not filename:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"video_{timestamp}.mp4"
    else:
        filename = validate_filename(filename)

    output_path = VIDEOS_DIR / "rendered" / filename
    backend = get_backend()
    return backend.generate(script, output_path)
