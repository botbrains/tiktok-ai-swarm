"""Content Strategist — plans what to post, when, and why. The brain of the operation."""
import json
from datetime import datetime, timedelta
from ..llm import ask
from ..config import load_config, CALENDAR_DIR, KNOWLEDGE_DIR
from ..security import sanitize_prompt_input, build_prompt

SYSTEM = """You are the Content Strategist for an AI-powered TikTok influencer account.
You plan content that GROWS the account and CONVERTS viewers into buyers.

Your strategic framework:
1. **Content pillars** — every account needs 3-5 recurring content types that the audience expects
2. **Trend riding** — 30% of content should ride current trends with your niche twist
3. **Evergreen authority** — 40% should be searchable, evergreen content that ranks long-term
4. **Viral attempts** — 20% should be high-risk/high-reward hooks designed to break out
5. **Community building** — 10% should be engagement-focused (polls, questions, duets)

Posting cadence psychology:
- 3 posts/day is the sweet spot for growth. More = diluted engagement. Less = algorithm forgets you.
- Morning (8-10am): educational/tips content catches commuters
- Midday (12-2pm): entertaining/trend content catches lunch scrollers
- Evening (7-9pm): product reviews/longer content catches couch scrollers
- Lives should be 7-9pm when engagement peaks

Growth hacking:
- First 100 videos determine your niche in the algorithm. Be CONSISTENT.
- Comments on other creators' posts drive more followers than posting alone
- Stitch/duet trending videos with your niche angle
- Series content (Part 1, Part 2...) drives follows for next installment
"""


def plan_week(focus: str = "") -> str:
    cfg = load_config()
    persona = cfg.get("persona_niche", "")
    style = sanitize_prompt_input(cfg.get("persona_style", ""), "context")
    posts_per_day = min(max(int(cfg.get("posts_per_day", 3)), 1), 10)

    prompt = build_prompt(
        f"""Create a 7-day TikTok content calendar.

Account niche: {sanitize_prompt_input(persona, 'niche') or 'product reviews and lifestyle'}
Style: {style or 'authentic, entertaining, informative'}
Posts per day: {posts_per_day}""",
        context=focus or "growth and establishing authority",
    ) + """

For each day, plan:
- **Post 1 (morning):** Content type, topic, hook concept, format (15s/30s/60s)
- **Post 2 (midday):** Content type, topic, hook concept, format
- **Post 3 (evening):** Content type, topic, hook concept, format
- **Live session:** Topic for evening live, talking points, product to feature

Also include:
- **Trend to ride:** One current trend format to adapt this week
- **Series to start:** One multi-part series concept
- **Engagement tasks:** Daily comment/duet/stitch targets"""

    result = ask(SYSTEM, prompt, temperature=0.8)

    # Save to calendar
    CALENDAR_DIR.mkdir(parents=True, exist_ok=True)
    week_start = datetime.now().strftime("%Y-%m-%d")
    cal_file = CALENDAR_DIR / f"week_{week_start}.json"
    cal_file.write_text(json.dumps({
        "week_start": week_start,
        "focus": focus,
        "plan": result,
        "created": datetime.now().isoformat(),
    }, indent=2))

    return result


def plan_today(notes: str = "") -> str:
    cfg = load_config()
    niche = sanitize_prompt_input(cfg.get("persona_niche", "product reviews"), "niche")
    style = sanitize_prompt_input(cfg.get("persona_style", "authentic"), "context")
    times = cfg.get("post_times", ["09:00", "13:00", "19:00"])

    prompt = build_prompt(
        f"""Plan today's TikTok content in detail.

Niche: {niche}
Style: {style}
Post times: {', '.join(times)}""",
        context=notes or "none",
    ) + """

For each post, provide:
1. **Exact hook** (first 3 seconds, word for word)
2. **Full script** (with [SHOW: ...] visual directions)
3. **Hashtags** (8-10, mix of broad and niche)
4. **Caption** (with CTA)
5. **Audio suggestion** (trending sound or original)
6. **Estimated production time**

Also: one engagement task to do between posts (comment raid, duet, etc.)"""

    return ask(SYSTEM, prompt, temperature=0.7)


def analyze_trends(niche: str = "") -> str:
    cfg = load_config()
    safe_niche = sanitize_prompt_input(niche or cfg.get("persona_niche", "product reviews"), "niche")

    prompt = build_prompt(
        "Analyze current TikTok trends that can be adapted for this niche.",
        niche=safe_niche,
    ) + """

Identify:
1. **3 trending formats** — the video structure/template that's going viral right now
2. **3 trending sounds** — audio that's blowing up and how to use it for product content
3. **3 trending hashtags** — emerging hashtags with momentum
4. **2 stitch/duet opportunities** — types of viral videos to respond to with your niche angle
5. **1 contrarian take** — something everyone is saying that you can disagree with (drives comments)

For each trend: how to adapt it for product promotion without feeling salesy."""

    return ask(SYSTEM, prompt, temperature=0.9)
