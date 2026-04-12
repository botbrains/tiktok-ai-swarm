"""Content Poster — handles the full post pipeline: generate → approve → upload → publish."""
import json
import time
from pathlib import Path
from ..config import load_config, DATA_DIR

QUEUE_FILE = DATA_DIR / "calendar" / "post_queue.json"


def _load_queue() -> list:
    if QUEUE_FILE.exists():
        return json.loads(QUEUE_FILE.read_text())
    return []


def _save_queue(queue: list):
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_FILE.write_text(json.dumps(queue, indent=2))


def queue_post(
    title: str,
    script: str,
    caption: str,
    hashtags: list[str],
    product: str = "",
    video_path: str = "",
    scheduled_time: str = "",
) -> str:
    """Add a post to the approval queue."""
    queue = _load_queue()
    post = {
        "id": len(queue) + 1,
        "title": title,
        "script": script,
        "caption": caption,
        "hashtags": hashtags,
        "product": product,
        "video_path": video_path,
        "scheduled_time": scheduled_time,
        "status": "pending_approval",
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    queue.append(post)
    _save_queue(queue)
    return f"Post #{post['id']} queued: {title} — status: pending_approval"


def approve_post(post_id: int) -> str:
    """Approve a queued post for publishing."""
    queue = _load_queue()
    for post in queue:
        if post["id"] == post_id:
            post["status"] = "approved"
            _save_queue(queue)
            return f"Post #{post_id} approved: {post['title']}"
    return f"Post #{post_id} not found"


def reject_post(post_id: int, reason: str = "") -> str:
    """Reject a queued post."""
    queue = _load_queue()
    for post in queue:
        if post["id"] == post_id:
            post["status"] = "rejected"
            post["reject_reason"] = reason
            _save_queue(queue)
            return f"Post #{post_id} rejected: {reason}"
    return f"Post #{post_id} not found"


def publish_approved() -> list[str]:
    """Publish all approved posts that have video files."""
    cfg = load_config()
    queue = _load_queue()
    results = []

    for post in queue:
        if post["status"] != "approved":
            continue
        if not post.get("video_path") or not Path(post["video_path"]).exists():
            results.append(f"Post #{post['id']}: skipped — no video file")
            continue

        if not cfg.get("tiktok_access_token"):
            results.append(f"Post #{post['id']}: skipped — TikTok API not configured")
            continue

        try:
            from .api import init_video_upload, upload_video, publish_video

            video_size = Path(post["video_path"]).stat().st_size
            init = init_video_upload(video_size)
            upload_video(init["upload_url"], post["video_path"])
            publish_video(init["publish_id"], post["caption"], post["hashtags"])
            post["status"] = "published"
            post["published_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            results.append(f"Post #{post['id']}: PUBLISHED — {post['title']}")
        except Exception as e:
            post["status"] = "failed"
            post["error"] = str(e)
            results.append(f"Post #{post['id']}: FAILED — {e}")

    _save_queue(queue)
    return results


def show_queue(status: str = "all") -> list[dict]:
    """Show posts in the queue, optionally filtered by status."""
    queue = _load_queue()
    if status != "all":
        queue = [p for p in queue if p["status"] == status]
    return queue
