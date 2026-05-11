"""CLI — single entry point for the TikTok AI Swarm."""
import sys
import io
import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

console = Console()


def _sanitize(text: str) -> str:
    return text.encode("cp1252", errors="replace").decode("cp1252")


def render(title: str, content: str):
    console.print()
    try:
        console.print(Panel(Markdown(content), title=f"[bold cyan]{title}[/]", border_style="cyan"))
    except UnicodeEncodeError:
        console.print(Panel(Markdown(_sanitize(content)), title=f"[bold cyan]{title}[/]", border_style="cyan"))
    console.print()


@click.group()
def main():
    """TikTok AI Swarm — autonomous AI influencer pipeline."""
    pass


# ── Setup ──────────────────────────────────────────────────────────────


@main.command()
def setup():
    """Configure the swarm — persona, APIs, schedule."""
    from .config import load_config, save_config

    cfg = load_config()
    console.print("\n[bold cyan]TikTok AI Swarm Setup[/]\n")

    console.print("[bold]Persona[/]")
    cfg["persona_name"] = Prompt.ask("Persona name", default=cfg.get("persona_name", ""))
    cfg["persona_niche"] = Prompt.ask("Niche (e.g., tech reviews, kitchen gadgets)", default=cfg.get("persona_niche", ""))
    cfg["persona_style"] = Prompt.ask("Style (e.g., energetic, chill, funny)", default=cfg.get("persona_style", ""))
    cfg["persona_bio"] = Prompt.ask("Bio (one-liner for profile)", default=cfg.get("persona_bio", ""))
    cfg["persona_catchphrase"] = Prompt.ask("Catchphrase (optional)", default=cfg.get("persona_catchphrase", ""))

    console.print("\n[bold]LLM[/]")
    cfg["model"] = Prompt.ask("Ollama model", default=cfg.get("model", "qwen2.5:32b"))
    cfg["ollama_url"] = Prompt.ask("Ollama URL", default=cfg.get("ollama_url", "http://localhost:11434"))

    console.print("\n[bold]Schedule[/]")
    cfg["posts_per_day"] = int(Prompt.ask("Posts per day", default=str(cfg.get("posts_per_day", 3))))
    times = Prompt.ask("Post times (comma-separated)", default=",".join(cfg.get("post_times", ["09:00", "13:00", "19:00"])))
    cfg["post_times"] = [t.strip() for t in times.split(",")]

    console.print("\n[bold]Avatar Backend[/] (heygen/d-id/none)")
    cfg["avatar_backend"] = Prompt.ask("Avatar backend", default=cfg.get("avatar_backend", "none"))
    if cfg["avatar_backend"] == "heygen":
        cfg["heygen_api_key"] = Prompt.ask("HeyGen API key", default=cfg.get("heygen_api_key", ""))
        cfg["heygen_avatar_id"] = Prompt.ask("HeyGen avatar ID", default=cfg.get("heygen_avatar_id", ""))

    console.print("\n[bold]Voice Backend[/] (elevenlabs/local/none)")
    cfg["voice_backend"] = Prompt.ask("Voice backend", default=cfg.get("voice_backend", "none"))
    if cfg["voice_backend"] == "elevenlabs":
        cfg["elevenlabs_api_key"] = Prompt.ask("ElevenLabs API key", default=cfg.get("elevenlabs_api_key", ""))
        cfg["elevenlabs_voice_id"] = Prompt.ask("ElevenLabs voice ID", default=cfg.get("elevenlabs_voice_id", ""))

    console.print("\n[bold]TikTok API[/] (optional — needed for auto-posting)")
    cfg["tiktok_client_key"] = Prompt.ask("TikTok client key", default=cfg.get("tiktok_client_key", ""))
    if cfg["tiktok_client_key"]:
        cfg["tiktok_client_secret"] = Prompt.ask("TikTok client secret", default=cfg.get("tiktok_client_secret", ""))

    console.print("\n[bold]Affiliate[/]")
    cfg["amazon_associate_tag"] = Prompt.ask("Amazon Associate tag", default=cfg.get("amazon_associate_tag", ""))
    cfg["linktree_url"] = Prompt.ask("Linktree/link-in-bio URL", default=cfg.get("linktree_url", ""))

    console.print("\n[bold]Safety[/]")
    cfg["require_approval"] = Prompt.ask("Require approval before posting? (yes/no)", default="yes") == "yes"

    save_config(cfg)
    console.print("\n[green]Config saved![/] Start with: [bold]tt plan-week[/]\n")


# ── Strategy ───────────────────────────────────────────────────────────


@main.command()
@click.option("--focus", "-f", default="", help="Special focus for the week")
def plan_week(focus):
    """Plan a full week of content."""
    from .agents.content_strategist import plan_week as do_plan

    console.print("[bold]Content Strategist[/] planning the week...\n")
    result = do_plan(focus)
    render("Weekly Content Plan", result)


@main.command()
@click.option("--notes", "-n", default="", help="Additional context for today")
def plan_today(notes):
    """Plan today's content in detail."""
    from .agents.content_strategist import plan_today as do_plan

    console.print("[bold]Content Strategist[/] planning today...\n")
    result = do_plan(notes)
    render("Today's Plan", result)


@main.command()
@click.option("--niche", "-n", default="", help="Niche to analyze trends for")
def trends(niche):
    """Analyze current TikTok trends for your niche."""
    from .agents.content_strategist import analyze_trends

    console.print("[bold]Trend Analysis[/]...\n")
    result = analyze_trends(niche)
    render("TikTok Trends", result)


# ── Content Creation ───────────────────────────────────────────────────


@main.command()
@click.argument("product")
@click.option("--format", "-f", default="review", type=click.Choice(["review", "grwm", "skit", "tutorial", "storytime", "comparison", "trend"]))
@click.option("--duration", "-d", default="30s", help="Target duration (15s/30s/60s)")
@click.option("--trend", "-t", default="", help="Trend to incorporate")
def script(product, format, duration, trend):
    """Write a TikTok video script."""
    from .agents.script_writer import write_video_script

    console.print(f"[bold]Script Writer[/] creating {format} script for: {product}\n")
    result = write_video_script(product, format, duration, trend)
    render(f"TikTok Script — {product}", result)


@main.command()
@click.argument("product")
@click.option("--duration", "-d", default=30, help="Live duration in minutes")
def live_script(product, duration):
    """Write a TikTok LIVE session script."""
    from .agents.script_writer import write_live_script

    console.print(f"[bold]Script Writer[/] creating live script for: {product}\n")
    result = write_live_script(product, duration)
    render(f"Live Script — {product}", result)


@main.command()
@click.argument("theme")
@click.option("--parts", "-p", default=5, help="Number of parts in the series")
def series(theme, parts):
    """Create a multi-part content series."""
    from .agents.script_writer import write_series

    console.print(f"[bold]Script Writer[/] creating {parts}-part series: {theme}\n")
    result = write_series(theme, parts)
    render(f"Series — {theme}", result)


# ── Products ───────────────────────────────────────────────────────────


@main.command()
@click.option("--category", "-c", default="", help="Product category")
@click.option("--count", "-n", default=5, help="Number of products")
def products(category, count):
    """Find products optimized for TikTok content."""
    from .agents.product_curator import find_products

    console.print("[bold]Product Curator[/] searching...\n")
    result = find_products(category, count)
    render("TikTok Products", result)


@main.command()
@click.argument("product")
@click.option("--price", "-p", default="", help="Product price")
def evaluate(product, price):
    """Evaluate a specific product's TikTok potential."""
    from .agents.product_curator import evaluate_product

    console.print(f"[bold]Product Curator[/] evaluating: {product}\n")
    result = evaluate_product(product, price)
    render(f"Evaluation — {product}", result)


# ── SEO & Discovery ───────────────────────────────────────────────────


@main.command()
@click.argument("topic")
def hashtags(topic):
    """Deep hashtag research for a topic."""
    from .agents.seo_optimizer import hashtag_research

    console.print(f"[bold]SEO Optimizer[/] researching hashtags: {topic}\n")
    result = hashtag_research(topic)
    render(f"Hashtags — {topic}", result)


@main.command()
def best_times():
    """Get optimal posting schedule for your niche."""
    from .agents.seo_optimizer import optimal_posting_schedule

    console.print("[bold]SEO Optimizer[/] calculating best times...\n")
    result = optimal_posting_schedule()
    render("Optimal Posting Schedule", result)


# ── Engagement ─────────────────────────────────────────────────────────


@main.command()
@click.argument("topic")
@click.option("--target", "-t", default="own", type=click.Choice(["own", "others"]))
@click.option("--count", "-n", default=5, help="Number of comments")
def comments(topic, target, count):
    """Generate strategic comments."""
    from .agents.engagement_manager import generate_comments

    console.print(f"[bold]Engagement Manager[/] generating comments for {target} videos...\n")
    result = generate_comments(topic, target, count)
    render(f"Comments — {topic}", result)


@main.command()
@click.argument("comment")
@click.argument("context")
@click.option("--product", "-p", default="", help="Product mentioned")
def reply(comment, context, product):
    """Generate a reply to a specific comment."""
    from .agents.engagement_manager import reply_to_comment

    result = reply_to_comment(comment, context, product)
    render("Reply Options", result)


@main.command()
@click.option("--followers", "-f", default=0, help="Current follower count")
def growth(followers):
    """Get today's growth task list."""
    from .agents.engagement_manager import growth_tasks

    console.print("[bold]Engagement Manager[/] planning growth tasks...\n")
    result = growth_tasks(followers)
    render("Growth Tasks", result)


# ── Live Streaming ─────────────────────────────────────────────────────


@main.command()
@click.argument("product")
@click.option("--duration", "-d", default=30, help="Duration in minutes")
def plan_live(product, duration):
    """Plan a TikTok LIVE session with full prep."""
    from .tiktok.live import prepare_live_session

    console.print(f"[bold]Live Director[/] preparing session for: {product}\n")
    session = prepare_live_session(product, duration)
    render("Live Plan", session["plan"])
    render("Live Response Bank", session["responses"])


@main.command()
@click.argument("comment")
@click.argument("product")
def live_reply(comment, product):
    """Generate a real-time reply for TikTok LIVE chat."""
    from .tiktok.live import generate_live_reply

    result = generate_live_reply(comment, product)
    console.print(f"[bold green]Reply:[/] {result}")


# ── Video Production ───────────────────────────────────────────────────


@main.command()
@click.argument("script_text")
@click.option("--filename", "-f", default="", help="Output filename")
def generate_video(script_text, filename):
    """Generate an AI avatar video from a script."""
    from .avatar.generator import generate_video as gen

    console.print("[bold]Avatar Generator[/] creating video...\n")
    result = gen(script_text, filename)
    console.print(f"[green]{result}[/]")


@main.command()
@click.argument("text")
@click.option("--filename", "-f", default="", help="Output filename")
def voice(text, filename):
    """Generate voice audio from text."""
    from .avatar.voice import synthesize_speech

    console.print("[bold]Voice Synthesizer[/] generating audio...\n")
    result = synthesize_speech(text, filename)
    console.print(f"[green]{result}[/]")


# ── Post Queue & Publishing ───────────────────────────────────────────


@main.command()
@click.option("--status", "-s", default="all", help="Filter by status")
def queue(status):
    """Show the post queue."""
    from .tiktok.poster import show_queue

    posts = show_queue(status)
    if not posts:
        console.print("Queue is empty.")
        return
    for p in posts:
        status_color = {"pending_approval": "yellow", "approved": "green", "rejected": "red", "published": "cyan"}.get(p["status"], "white")
        console.print(f"  #{p['id']} [{status_color}]{p['status']}[/] — {p['title'][:50]}")


@main.command()
@click.argument("post_id", type=int)
def approve(post_id):
    """Approve a queued post for publishing."""
    from .tiktok.poster import approve_post

    result = approve_post(post_id)
    console.print(f"[green]{result}[/]")


@main.command()
@click.argument("post_id", type=int)
@click.option("--reason", "-r", default="", help="Rejection reason")
def reject(post_id, reason):
    """Reject a queued post."""
    from .tiktok.poster import reject_post

    result = reject_post(post_id)
    console.print(f"[red]{result}[/]")


@main.command()
def publish():
    """Publish all approved posts to TikTok."""
    from .tiktok.poster import publish_approved

    results = publish_approved()
    for r in results:
        console.print(r)


# ── Analytics ──────────────────────────────────────────────────────────


@main.command()
@click.argument("title")
@click.option("--format", "-f", required=True, help="Video format (review/skit/tutorial/etc)")
@click.option("--product", "-p", default="", help="Product featured")
@click.option("--hook", "-h", default="", help="Hook type used")
@click.option("--views", "-v", default=0, help="View count")
@click.option("--likes", "-l", default=0, help="Likes")
@click.option("--comments", "-c", default=0, help="Comments")
@click.option("--shares", "-s", default=0, help="Shares")
@click.option("--saves", default=0, help="Saves")
@click.option("--follows", default=0, help="Follows from this post")
@click.option("--clicks", "-k", default=0, help="Link clicks")
@click.option("--commission", "-$", default=0.0, help="Commission earned")
def log_post(title, format, product, hook, views, likes, comments, shares, saves, follows, clicks, commission):
    """Log a post's performance metrics."""
    from .agents.analytics_agent import log_post as do_log

    result = do_log(title, format, product, hook, "", views, likes, comments, shares, saves, 0, follows, clicks, commission)
    console.print(f"[green]{result}[/]")


@main.command()
def analyze():
    """AI analysis of your TikTok performance."""
    from .agents.analytics_agent import analyze_performance

    console.print("[bold]Analytics Agent[/] analyzing...\n")
    result = analyze_performance()
    render("Performance Analysis", result)


@main.command()
@click.option("--limit", "-n", default=10, help="Number of posts to show")
def dashboard(limit):
    """Show the analytics dashboard."""
    from .agents.analytics_agent import show_dashboard

    result = show_dashboard(limit)
    console.print(result)


# ── Daemon ─────────────────────────────────────────────────────────────


@main.command()
def daemon():
    """Run the 24/7 autonomous content daemon."""
    from .scheduler.daemon import run_daemon

    run_daemon()


# ── Knowledge ──────────────────────────────────────────────────────────


@main.command()
@click.argument("topic")
@click.argument("entry")
def learn(topic, entry):
    """Teach the swarm something."""
    from .knowledge.store import append_knowledge

    append_knowledge(topic, entry)
    console.print(f"[green]Learned:[/] added to '{topic}'")


@main.command()
def knowledge():
    """Show all stored knowledge."""
    from .knowledge.store import list_topics, load_knowledge

    topics = list_topics()
    if not topics:
        console.print("No knowledge stored yet.")
        return
    for topic in topics:
        content = load_knowledge(topic)
        render(topic, content if len(content) < 500 else content[:500] + "...")


# ── Updates ────────────────────────────────────────────────────────────


@main.command(name="check-updates")
def check_updates():
    """Check if updates are available."""
    from .updater import check_for_updates
    console.print(check_for_updates())


@main.command(name="self-update")
def self_update():
    """Pull latest code and reinstall dependencies."""
    from .updater import apply_update
    console.print("[bold]Updating...[/]\n")
    console.print(apply_update())


@main.command()
def version():
    """Show current version."""
    import subprocess
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent.parent
    try:
        result = subprocess.run(["git", "log", "-1", "--format=%h %s (%cr)"], cwd=root, capture_output=True, text=True, timeout=10)
        console.print(f"  {result.stdout.strip()}")
    except Exception:
        from . import __version__
        console.print(f"  v{__version__}")


# ── TikTok Shop / Beacons Affiliate ───────────────────────────────────


@main.command(name="shop-week")
@click.option("--focus", "-f", default="", help="Optional theme/focus for the week")
@click.option("--offers", "-n", default=5, help="Max number of offers in the slate")
@click.option("--no-live", is_flag=True, default=False, help="Skip live run-of-show generation")
def shop_week(focus, offers, no_live):
    """Run the weekly TikTok Shop planning cycle.

    Selects the best offers, generates a Beacons update pack
    (beacons_weekly_pack_<week>.md) and a machine-readable slate
    (weekly_offer_slate_<week>.json) in data/shop/artifacts/.
    """
    from .agents.shop_agent import run_weekly_planning

    console.print("[bold]Shop Agent[/] running weekly planning...\n")
    result = run_weekly_planning(n=offers, focus=focus, include_live=not no_live)
    slate = result["slate"]
    render(
        f"Weekly Slate — {slate.week_of}",
        f"**Headline:** {slate.headline}\n\n"
        f"**Offers selected:** {len(slate.offer_ids)}\n\n"
        f"**CTA strategy:** {slate.cta_strategy}\n\n"
        f"**Artifacts written:**\n"
        f"- `{result['md_path']}`\n"
        f"- `{result['json_path']}`\n\n"
        f"> Copy the contents of `beacons_weekly_pack_*.md` into your Beacons dashboard.",
    )


@main.command(name="shop-offers")
def shop_offers():
    """List the TikTok Shop offer catalog."""
    from .shop.store import load_offers

    offers = load_offers()
    if not offers:
        console.print("No offers yet. Add one with: [bold]tt shop-add-offer[/]")
        return

    console.print(f"\n  {'ID':<10} {'Active':<7} {'Title':<35} {'Price':>8}  {'Comm%':>6}  Category")
    console.print("  " + "-" * 85)
    for o in offers:
        active_flag = "[green]yes[/]" if o.active else "[red]no[/]"
        price = f"${o.price_usd:.2f}" if o.price_usd else "—"
        comm = f"{o.commission_rate * 100:.0f}%" if o.commission_rate else "—"
        console.print(
            f"  {o.offer_id:<10} {active_flag:<7} {o.title[:35]:<35} {price:>8}  {comm:>6}  {o.category}"
        )
    console.print()


@main.command(name="shop-add-offer")
def shop_add_offer():
    """Interactively add a product offer to the TikTok Shop catalog."""
    from .shop.models import ShopOffer
    from .shop.store import add_offer
    from rich.prompt import Prompt

    console.print("\n[bold cyan]Add TikTok Shop Offer[/]\n")
    title = Prompt.ask("Product title")
    category = Prompt.ask("Category (e.g. kitchen gadgets)", default="")
    price = float(Prompt.ask("Price (USD)", default="0"))
    comm = float(Prompt.ask("Commission rate (e.g. 0.10 for 10%)", default="0"))
    url = Prompt.ask("TikTok Shop product URL")
    region = Prompt.ask("Region", default="US")
    notes = Prompt.ask("Notes (optional)", default="")

    offer = ShopOffer(
        title=title,
        category=category,
        price_usd=price,
        commission_rate=comm,
        tiktok_product_url=url,
        region=region,
        notes=notes,
    )
    add_offer(offer)
    console.print(f"\n[green]Offer added![/] ID: [bold]{offer.offer_id}[/]")


@main.command(name="shop-creative")
@click.argument("offer_id")
@click.option(
    "--format", "-f", default="review",
    type=click.Choice(["review", "grwm", "skit", "tutorial", "storytime", "comparison", "trend"]),
    help="Video format",
)
def shop_creative(offer_id, format):
    """Generate a compliant post creative for a Shop offer."""
    from .shop.store import get_offer
    from .agents.shop_agent import generate_post_creative

    offer = get_offer(offer_id)
    if not offer:
        console.print(f"[red]Offer '{offer_id}' not found.[/] Run: tt shop-offers")
        return

    console.print(f"[bold]Shop Agent[/] generating {format} creative for: {offer.title}\n")
    result = generate_post_creative(offer, format)
    render(f"Shop Creative — {offer.title}", result)


@main.command(name="shop-ingest")
@click.argument("csv_path")
def shop_ingest(csv_path):
    """Ingest a TikTok/Shop affiliate performance CSV into the analytics store.

    CSV must have a header row with columns: offer_id, date, views, clicks,
    orders, commission, video_id, source (all optional except offer_id).
    """
    from .shop.analytics import ingest_csv_export

    try:
        count = ingest_csv_export(csv_path)
        console.print(f"[green]Ingested {count} records from {csv_path}[/]")
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")


@main.command(name="shop-rankings")
def shop_rankings():
    """Show offer performance rankings (feeds into next week's slate selection)."""
    from .shop.analytics import compute_rankings

    rankings = compute_rankings()
    if not rankings:
        console.print("No data yet. Log metrics with: [bold]tt shop-ingest[/]")
        return

    console.print(
        f"\n  {'#':<4} {'Offer ID':<10} {'Score':>8}  {'Metric':<28}  "
        f"{'Views':>8}  {'Clicks':>7}  {'Orders':>7}  {'Comm $':>8}  Title"
    )
    console.print("  " + "-" * 110)
    for rank, r in enumerate(rankings, 1):
        console.print(
            f"  {rank:<4} {r['offer_id']:<10} {r['score']:>8.3f}  {r['metric_used']:<28}  "
            f"{r['views']:>8}  {r['clicks']:>7}  {r['orders']:>7}  {r['commission']:>8.2f}  "
            f"{r['title'][:30]}"
        )
    console.print()


if __name__ == "__main__":
    main()
