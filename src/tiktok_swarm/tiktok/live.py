"""TikTok Live streaming via RTMP.

TikTok provides an RTMP URL + stream key when you start a live.
We stream AI-generated avatar video + audio to that RTMP endpoint using FFmpeg.
"""
import subprocess
import json
import time
from pathlib import Path
from ..config import load_config, DATA_DIR
from ..agents.live_director import plan_live, generate_live_responses
from ..llm import ask

LIVE_LOG = DATA_DIR / "analytics" / "live_sessions.json"


def start_stream(rtmp_url: str, stream_key: str, video_source: str) -> subprocess.Popen:
    """Start streaming to TikTok Live via FFmpeg.

    video_source can be:
    - A video file path (loops)
    - A virtual camera device
    - An image + audio stream
    """
    cmd = [
        "ffmpeg",
        "-re",  # Read at native framerate
        "-stream_loop", "-1",  # Loop the video
        "-i", video_source,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-maxrate", "2500k",
        "-bufsize", "5000k",
        "-pix_fmt", "yuv420p",
        "-g", "60",  # Keyframe every 2s at 30fps
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        "-f", "flv",
        f"{rtmp_url}/{stream_key}",
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return process


def prepare_live_session(product: str, duration_min: int = 30) -> dict:
    """Prepare everything needed for a live session."""
    cfg = load_config()

    # Generate the live plan
    plan = plan_live(product, duration_min)

    # Generate response bank
    responses = generate_live_responses(product)

    # Save session prep
    session = {
        "product": product,
        "duration": duration_min,
        "plan": plan,
        "responses": responses,
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "prepared",
    }

    LIVE_LOG.parent.mkdir(parents=True, exist_ok=True)
    sessions = []
    if LIVE_LOG.exists():
        sessions = json.loads(LIVE_LOG.read_text())
    sessions.append(session)
    LIVE_LOG.write_text(json.dumps(sessions, indent=2))

    return session


def generate_live_reply(viewer_comment: str, product: str, context: str = "") -> str:
    """Generate a real-time response to a viewer comment during live."""
    cfg = load_config()

    prompt = f"""You are live on TikTok right now. A viewer just commented:

"{viewer_comment}"

Product you're showing: {product}
Your persona: {cfg.get('persona_name', 'Creator')} — {cfg.get('persona_style', 'authentic')}
Context: {context or 'mid-stream, good energy'}

Generate a natural, on-brand spoken response (1-2 sentences). It should:
- Acknowledge the viewer by feel (not necessarily by name)
- Answer their question or respond to their comment
- Keep the energy of the live going
- If relevant, tie back to the product naturally

Just the response, nothing else."""

    return ask("You are a TikTok live streamer responding to chat in real-time.", prompt, temperature=0.9)
