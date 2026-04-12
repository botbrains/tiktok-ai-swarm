"""Analytics Agent — tracks performance and optimizes the content strategy."""
import json
from datetime import datetime
from ..llm import ask
from ..config import ANALYTICS_DIR
from ..security import sanitize_prompt_input, build_prompt

METRICS_FILE = ANALYTICS_DIR / "metrics.json"


def _load_metrics() -> list:
    if METRICS_FILE.exists():
        with open(METRICS_FILE) as f:
            return json.load(f)
    return []


def _save_metrics(metrics: list):
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS_FILE, "w") as f:
        json.dump(metrics, f, indent=2)


def log_post(
    title: str,
    format: str,
    product: str = "",
    hook_type: str = "",
    post_time: str = "",
    views: int = 0,
    likes: int = 0,
    comments: int = 0,
    shares: int = 0,
    saves: int = 0,
    profile_visits: int = 0,
    follows: int = 0,
    link_clicks: int = 0,
    commission: float = 0.0,
    notes: str = "",
) -> str:
    metrics = _load_metrics()
    entry = {
        "date": datetime.now().isoformat()[:10],
        "title": sanitize_prompt_input(title, "product")[:100],
        "format": sanitize_prompt_input(format, "context")[:30],
        "product": sanitize_prompt_input(product, "product")[:100],
        "hook_type": sanitize_prompt_input(hook_type, "context")[:50],
        "post_time": post_time[:10],
        "views": views,
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "saves": saves,
        "profile_visits": profile_visits,
        "follows": follows,
        "link_clicks": link_clicks,
        "commission": commission,
        "engagement_rate": round((likes + comments + shares + saves) / views * 100, 2) if views > 0 else 0,
        "notes": notes,
    }
    metrics.append(entry)
    _save_metrics(metrics)
    return f"Logged: {title} — {views} views, {entry['engagement_rate']}% engagement, ${commission:.2f}"


def update_post(title: str, **kwargs) -> str:
    metrics = _load_metrics()
    for entry in reversed(metrics):
        if entry["title"].lower() == title.lower():
            for k, v in kwargs.items():
                if k in entry and v:
                    entry[k] = v
            if entry["views"] > 0:
                entry["engagement_rate"] = round(
                    (entry["likes"] + entry["comments"] + entry["shares"] + entry["saves"])
                    / entry["views"] * 100, 2
                )
            _save_metrics(metrics)
            return f"Updated: {title}"
    return f"No entry found for '{title}'"


def analyze_performance() -> str:
    metrics = _load_metrics()
    if not metrics:
        return "No data yet. Log posts with: tt log-post"

    summary = sanitize_prompt_input(json.dumps(metrics, indent=2), "context")

    prompt = build_prompt(
        """Analyze this TikTok account's performance data and provide actionable optimization insights.

Analyze:
1. **Top performers** — which posts got the best engagement and why
2. **Best hook types** — which hooks drove the most views/engagement
3. **Best formats** — which video formats convert best
4. **Best posting times** — when do posts perform best
5. **Product performance** — which products drove the most commission
6. **Engagement patterns** — what drives comments vs shares vs saves
7. **Growth trajectory** — followers/profile visits trend
8. **Revenue analysis** — commission per view, per post, per product category
9. **What to double down on** — specific content to make MORE of
10. **What to stop doing** — content types that underperform
11. **Next 3 videos** — exact recommendations based on data""",
        performance_data=summary,
    )

    ANALYST_SYSTEM = """You are a Performance Analyst for a TikTok influencer. Analyze
performance data and extract actionable, data-driven insights. Be specific, cite
numbers from the data, and make concrete recommendations."""

    return ask(ANALYST_SYSTEM, prompt, temperature=0.5)


def show_dashboard(limit: int = 10) -> str:
    metrics = _load_metrics()
    if not metrics:
        return "No posts tracked yet."

    recent = metrics[-limit:]
    lines = []
    for e in recent:
        lines.append(
            f"  {e['date']} | {e['title'][:25]:<25} | {e['format']:<10} | "
            f"{e['views']:>8} views | {e['engagement_rate']:>5}% eng | ${e['commission']:>7.2f}"
        )

    total_views = sum(e.get("views", 0) for e in metrics)
    total_commission = sum(e.get("commission", 0) for e in metrics)
    total_follows = sum(e.get("follows", 0) for e in metrics)
    avg_engagement = sum(e.get("engagement_rate", 0) for e in metrics) / len(metrics)

    header = f"  {'Date':<10} | {'Title':<25} | {'Format':<10} | {'Views':>8}       | {'Eng':>5}      | {'Revenue':>10}"
    sep = "  " + "-" * 95
    footer = (
        f"\n  Posts: {len(metrics)} | Total views: {total_views:,} | "
        f"Avg engagement: {avg_engagement:.1f}% | Follows gained: {total_follows} | "
        f"Total revenue: ${total_commission:.2f}"
    )

    return f"\n{header}\n{sep}\n" + "\n".join(lines) + f"\n{sep}{footer}"
