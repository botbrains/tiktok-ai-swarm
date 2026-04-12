"""Live Director — plans and runs TikTok live sessions."""
from ..llm import ask
from ..config import load_config
from ..security import sanitize_prompt_input, build_prompt

SYSTEM = """You are the Live Director for a TikTok influencer's live streams.
You plan, script, and manage live sessions that drive engagement and sales.

TikTok Live facts:
- Lives get MASSIVE algorithmic boost — TikTok pushes lives to followers' feeds
- You need 1,000 followers to go live (growth milestone #1)
- Average live viewer watches for 4-6 minutes — you need hooks every 5 min
- Comments during live boost the stream's visibility in real-time
- Gifting/tipping drives algorithm ranking for the live
- Pinned products during live get direct purchase links

Live session structure for product promotion:
1. **Energy burst (0-2 min)** — high energy greeting, acknowledge viewers by name
2. **Hook (2-5 min)** — tease what's coming, get people to stay
3. **Engagement bait (5-10 min)** — polls, questions, "type 1 if..." to fill chat
4. **Product intro (10-15 min)** — natural transition to the product
5. **Live demo (15-25 min)** — use the product, answer questions real-time
6. **Social proof (25-27 min)** — share reviews, show results
7. **CTA + close (27-30 min)** — direct to link, preview next live, end on high energy

Key techniques:
- "Welcome [username]!" — calling out viewers by name keeps them in the stream
- "Type YES if you want to see [X]" — drives comment count up
- "I'm going to show you something nobody else talks about..." — retention hook
- "Stay until the end because I'm giving away..." — watch time boost
"""


def plan_live(product: str, duration_min: int = 30, context: str = "") -> str:
    cfg = load_config()
    safe_duration = min(max(int(duration_min), 5), 120)
    persona = sanitize_prompt_input(cfg.get("persona_name", "[Creator]"), "product")
    style = sanitize_prompt_input(cfg.get("persona_style", "authentic, energetic"), "context")

    prompt = build_prompt(
        f"""Plan a TikTok LIVE session in detail.

Duration: {safe_duration} minutes
Persona: {persona}
Style: {style}

Provide a minute-by-minute rundown:""",
        product=product,
        context=context or "regular scheduled live",
    ) + """
- **Minute 0-2:** Opening script (exact words for greeting)
- **Minute 2-5:** Hook and engagement starter
- **Minute 5-10:** Warm-up content / Q&A
- **Minute 10-15:** Product introduction (natural transition)
- **Minute 15-25:** Live demo + real-time engagement
- **Minute 25-28:** Social proof + testimonials
- **Minute 28-30:** CTA + closing

Also provide:
- **10 comment prompts** to use throughout (drives algorithm)
- **5 objection responses** for live chat skeptics
- **3 energy recovery lines** for when chat goes quiet
- **Pin comment text** to pin at start of live
- **Title** for the live session (shows in notification)"""

    return ask(SYSTEM, prompt, temperature=0.7)


def generate_live_responses(product: str) -> str:
    prompt = build_prompt(
        "Generate a response bank for a TikTok LIVE session.",
        product=product,
    ) + """

Create ready-to-use responses for common live chat scenarios:

**Greetings (5 variations):**
- When a viewer joins

**Product questions (10 responses):**
- "Does it really work?"
- "How much is it?"
- "Where can I buy it?"
- "Is it worth it?"
- "What size/color should I get?"
(and 5 more common questions)

**Engagement drivers (5 responses):**
- When chat is slow
- When someone gifts
- When you hit a viewer milestone
- When someone shares the live
- When a hater comments

**Sales responses (5 responses):**
- When someone says they just bought it
- When someone is on the fence
- When someone asks for a discount
- When someone compares to competitor
- When someone asks about shipping

Keep all responses natural, conversational, and on-brand."""

    return ask(SYSTEM, prompt, temperature=0.7)
