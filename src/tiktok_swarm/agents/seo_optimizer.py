"""SEO Optimizer — hashtags, captions, posting times, discoverability."""
from ..llm import ask
from ..config import load_config

SYSTEM = """You are a TikTok SEO and Discovery specialist. You make content findable.

TikTok's algorithm considers:
1. **Watch time** — #1 signal. If people watch to the end, you win. Your job is to help
   structure content that holds attention.
2. **Engagement rate** — comments > shares > likes > saves. Comments are KING.
3. **Hashtags** — TikTok uses these to categorize and distribute content.
4. **Caption** — the algorithm reads this. Keywords matter.
5. **Sound** — trending sounds get algorithmic boost. Original sounds build brand.
6. **Post time** — when your target audience is scrolling.

Hashtag strategy:
- 3-5 hashtags is optimal. NOT 30.
- Mix: 1 broad (#fyp, #viral) + 2 niche (#kitchenhacks, #amazonfinds) + 1 specific (#under20dollars)
- NEVER use banned or shadow-banned hashtags
- Trending hashtags get a 24-48 hour algorithmic boost

Caption strategy:
- First line = hook (this shows before "...see more")
- Ask a question to drive comments
- Include a CTA but make it natural
- Keywords the algorithm can index

Comment strategy:
- Reply to comments within first hour (algorithm boost)
- Pin a controversial/question comment to drive thread
- Creator replies show at top of comments = more visibility
"""


def optimize_post(script: str, product: str, platform_notes: str = "") -> str:
    cfg = load_config()
    niche = cfg.get("persona_niche", "")

    prompt = f"""Optimize this TikTok post for maximum discovery and engagement.

Product: {product}
Niche: {niche or 'product reviews'}
Script summary: {script[:500] if len(script) > 500 else script}
{f'Notes: {platform_notes}' if platform_notes else ''}

Provide:
1. **Caption** (with hook as first line, question to drive comments, natural CTA)
2. **Hashtags** (3-5, strategically mixed)
3. **Sound recommendation** (trending or original)
4. **Best post time** for this content type
5. **Pin comment** — what the creator should comment and pin
6. **Comment prompt** — question to put in caption or say in video that drives replies
7. **Reply strategy** — first 3 replies to pre-write for likely comments
8. **Cross-post notes** — how to adapt for Instagram Reels and YouTube Shorts"""

    return ask(SYSTEM, prompt, temperature=0.6)


def hashtag_research(topic: str) -> str:
    prompt = f"""Deep hashtag research for TikTok content about: {topic}

Find:
1. **5 high-volume hashtags** (>1B views) — for broad reach
2. **5 mid-volume hashtags** (100M-1B views) — for niche targeting
3. **5 emerging hashtags** (<100M views but growing fast) — for early mover advantage
4. **3 hashtag combinations** — specific combos that work together
5. **3 hashtags to AVOID** — overused, shadow-banned, or wrong audience

For each: view count estimate, competition level, and audience match."""

    return ask(SYSTEM, prompt, temperature=0.6)


def optimal_posting_schedule(niche: str = "", timezone: str = "") -> str:
    cfg = load_config()
    prompt = f"""Design the optimal TikTok posting schedule.

Niche: {niche or cfg.get('persona_niche', 'product reviews')}
Timezone: {timezone or cfg.get('timezone', 'America/New_York')}
Posts per day: {cfg.get('posts_per_day', 3)}

Provide:
1. **Weekday schedule** — exact times for each post slot with content type
2. **Weekend schedule** — adjusted for different scroll patterns
3. **Live stream schedule** — best days and times for lives
4. **Engagement windows** — when to be active in comments (yours and others')
5. **Batch creation schedule** — when to film vs. edit vs. post for efficiency

Include reasoning for each time slot based on audience behavior patterns."""

    return ask(SYSTEM, prompt, temperature=0.5)
