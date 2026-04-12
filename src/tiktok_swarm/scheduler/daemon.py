"""24/7 Content Daemon — runs the swarm autonomously on a schedule.

This daemon:
1. Generates content based on the content calendar
2. Creates videos via the avatar backend
3. Queues posts for approval (or auto-publishes if approved)
4. Runs engagement tasks
5. Logs analytics
"""
import time
import json
import schedule
from datetime import datetime
from rich.console import Console
from ..config import load_config, CALENDAR_DIR
from ..agents.content_strategist import plan_today
from ..agents.script_writer import write_video_script
from ..agents.product_curator import find_products
from ..agents.seo_optimizer import optimize_post
from ..agents.engagement_manager import growth_tasks
from ..avatar.generator import generate_video
from ..tiktok.poster import queue_post, publish_approved

console = Console()


def _log(msg: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    console.print(f"  [{timestamp}] {msg}")


def content_cycle():
    """Single content creation cycle — generates one post."""
    cfg = load_config()
    _log("[bold cyan]Content cycle starting...[/]")

    # Find a product
    _log("Product Curator: finding product...")
    products = find_products(count=1)

    # Write a script
    _log("Script Writer: generating script...")
    script = write_video_script(products[:200], format="review", duration="30s")

    # Optimize SEO
    _log("SEO Optimizer: optimizing...")
    seo = optimize_post(script[:300], products[:100])

    # Generate video (if backend configured)
    _log("Avatar: generating video...")
    video_result = generate_video(script)

    # Queue the post
    result = queue_post(
        title=f"Auto-generated: {products[:50]}",
        script=script,
        caption=seo[:500] if isinstance(seo, str) else "",
        hashtags=[],
        product=products[:100] if isinstance(products, str) else "",
        video_path=video_result if not video_result.startswith("[ERROR") else "",
    )
    _log(f"[green]{result}[/]")

    # Auto-publish if approval not required
    if not cfg.get("require_approval", True):
        results = publish_approved()
        for r in results:
            _log(f"Publisher: {r}")


def engagement_cycle():
    """Engagement cycle — comment tasks, growth actions."""
    _log("[bold yellow]Engagement cycle starting...[/]")
    tasks = growth_tasks()
    _log(f"Growth tasks generated. Check: tt growth-tasks")


def daily_plan():
    """Generate the daily content plan."""
    _log("[bold magenta]Daily plan generating...[/]")
    plan = plan_today()
    today = datetime.now().strftime("%Y-%m-%d")
    plan_file = CALENDAR_DIR / f"day_{today}.json"
    plan_file.parent.mkdir(parents=True, exist_ok=True)
    plan_file.write_text(json.dumps({"date": today, "plan": plan}, indent=2))
    _log(f"Daily plan saved: {plan_file}")


def run_daemon():
    """Run the 24/7 content daemon."""
    cfg = load_config()
    post_times = cfg.get("post_times", ["09:00", "13:00", "19:00"])

    console.print("\n[bold cyan]TikTok AI Swarm — 24/7 Daemon[/]")
    console.print(f"  Model: {cfg.get('model', 'qwen2.5:32b')}")
    console.print(f"  Post times: {', '.join(post_times)}")
    console.print(f"  Approval required: {cfg.get('require_approval', True)}")
    console.print(f"  Avatar backend: {cfg.get('avatar_backend', 'none')}")
    console.print()

    # Schedule daily plan at 7am
    schedule.every().day.at("07:00").do(daily_plan)

    # Schedule content creation at configured times
    for t in post_times:
        schedule.every().day.at(t).do(content_cycle)

    # Schedule engagement 3x daily
    schedule.every().day.at("10:00").do(engagement_cycle)
    schedule.every().day.at("14:00").do(engagement_cycle)
    schedule.every().day.at("18:00").do(engagement_cycle)

    _log("Daemon started. Press Ctrl+C to stop.")
    _log(f"Scheduled: daily plan at 07:00, posts at {', '.join(post_times)}")

    # Run immediately on start
    daily_plan()

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        _log("Daemon stopped.")
