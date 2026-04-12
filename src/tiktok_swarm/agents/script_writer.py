"""Script Writer — creates TikTok video scripts optimized for the platform."""
from ..llm import ask
from ..config import load_config
from ..knowledge.store import load_knowledge

SYSTEM = """You are a TikTok Script Writer. You write scripts specifically for TikTok's
unique format and audience behavior.

TikTok script rules (non-negotiable):
1. **HOOK: 0-1.5 seconds** — You have LESS time than YouTube. Pattern interrupt immediately.
   The first frame and first word determine if they scroll. No "Hey guys", no intro, no logo.
2. **TENSION: 1.5-5 seconds** — Create a reason to keep watching. Question, conflict, promise.
3. **PAYOFF: 5-50 seconds** — Deliver on the hook's promise. Fast cuts. No dead air.
4. **CTA: last 2-3 seconds** — "Follow for part 2", "Link in bio", or ask a question (drives comments).

Format-specific scripts you write:
- **Product review** (15-60s): Hook → demo → verdict → CTA
- **Get ready with me + product** (30-60s): Routine format with product naturally integrated
- **POV/skit** (15-30s): Character-based content where the product is the punchline/solution
- **Tutorial/How-to** (30-60s): Teach something with the product as the tool
- **Storytime + product** (30-60s): Personal story that naturally leads to the product
- **Comparison** (15-30s): This vs that, always end on the winner (your affiliate product)
- **Trend adaptation** (15s): Current trend sound/format with product twist

Camera directions:
- [FACE CAM] — talking to camera
- [PRODUCT SHOT] — close-up of product
- [DEMO] — showing product in use
- [TEXT ON SCREEN: "..."] — text overlay
- [TRANSITION] — cut/transition effect
- [GREEN SCREEN] — green screen with image/video behind
"""


def write_video_script(product: str, format: str = "review", duration: str = "30s",
                       trend: str = "", key_points: str = "") -> str:
    cfg = load_config()
    persona = cfg.get("persona_name", "")
    style = cfg.get("persona_style", "")
    catchphrase = cfg.get("persona_catchphrase", "")

    hook_knowledge = load_knowledge("proven_hooks")
    hook_ctx = f"\nProven hooks that worked before:\n{hook_knowledge}" if hook_knowledge else ""

    prompt = f"""Write a TikTok video script.

Product: {product}
Format: {format}
Target duration: {duration}
Persona: {persona or '[Creator]'}
Style: {style or 'authentic, entertaining'}
Catchphrase: {catchphrase or 'none yet'}
Trend to incorporate: {trend or 'none — original content'}
Key points to hit: {key_points or 'identify the strongest selling points'}
{hook_ctx}

Deliver:
1. **3 hook options** (exact words + first visual frame)
2. **Full script** with camera directions ([FACE CAM], [PRODUCT SHOT], etc.)
3. **Text overlays** — exact text to put on screen and when
4. **Sound suggestion** — trending sound or original audio
5. **Caption** with hashtags (8-10)
6. **Thumbnail/cover frame** description
7. **CTA** that drives follows AND link clicks"""

    return ask(SYSTEM, prompt, temperature=0.7)


def write_live_script(product: str, duration_min: int = 30, talking_points: str = "") -> str:
    cfg = load_config()

    prompt = f"""Write a TikTok LIVE session script/outline.

Product to feature: {product}
Duration: {duration_min} minutes
Persona: {cfg.get('persona_name', '[Creator]')}
Talking points: {talking_points or 'generate based on product'}

Structure the live as:
1. **Opening (2 min)** — greet viewers, build energy, tease what's coming
2. **Engagement hook (3 min)** — ask a question, get comments flowing (algorithm boosts lives with comments)
3. **Product introduction (5 min)** — natural lead-in to the product
4. **Live demo (10 min)** — use the product on camera, respond to comments about it
5. **Q&A (5 min)** — answer viewer questions about the product
6. **Social proof + CTA (3 min)** — share reviews/results, direct to link
7. **Closing (2 min)** — preview next live, ask for follows

Include:
- **Comment prompts** — questions to ask that drive comment engagement
- **Objection responses** — pre-written answers to common buyer hesitations
- **Filler topics** — what to talk about during slow moments
- **Pin comment** — what to pin at the top of chat"""

    return ask(SYSTEM, prompt, temperature=0.7)


def write_series(theme: str, num_parts: int = 5) -> str:
    prompt = f"""Create a {num_parts}-part TikTok series concept.

Theme: {theme}
Goal: Drive follows (people follow to see the next part) AND product sales

For each part:
1. **Title** — "Part X: [hook title]"
2. **Hook** — must reference the series and create FOMO for the next part
3. **Core content** — what this episode covers
4. **Product integration** — how a product naturally fits this episode
5. **Cliffhanger/tease** — what makes them need Part X+1

The series should escalate — each part slightly more valuable than the last."""

    return ask(SYSTEM, prompt, temperature=0.8)
