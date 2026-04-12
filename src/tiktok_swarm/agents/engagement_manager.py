"""Engagement Manager — handles comments, community building, and growth tactics."""
from ..llm import ask
from ..config import load_config
from ..knowledge.store import load_knowledge
from ..security import sanitize_prompt_input, build_prompt, is_injection_attempt

SYSTEM = """You are the Engagement Manager for a TikTok influencer account. Your job
is to build community and drive growth through strategic engagement.

Engagement is the #1 growth lever on TikTok:
- Commenting on other creators' posts drives 3-5x more profile visits than posting alone
- Replying to your own comments within 1 hour boosts the video in the algorithm
- Controversial/debatable comments drive threads which drive distribution
- "Creator liked" notifications bring people back to the video

Comment strategy on YOUR videos:
1. Pin a comment that drives debate or asks a question
2. Reply to EVERY comment in the first hour
3. Heart comments that mention buying/wanting the product (social proof)
4. Reply with a video to the best questions (creates new content)

Comment strategy on OTHER creators' videos:
1. Leave genuine, valuable comments on trending videos in your niche
2. Never "follow for follow" or spam — add actual insight
3. Early comments on trending videos get thousands of views
4. Your comment IS your ad — make it interesting enough to click your profile

DM strategy:
1. Welcome new followers with a genuine message (NOT copy-paste spam)
2. Respond to product questions with affiliate links
3. Build relationships with other creators for collaborations
"""


def generate_comments(video_topic: str, target: str = "own", count: int = 5) -> str:
    cfg = load_config()
    persona = sanitize_prompt_input(cfg.get("persona_style", "authentic"), "context")
    safe_target = "own" if target == "own" else "others"
    safe_count = min(max(int(count), 1), 10)

    prompt = build_prompt(
        f"""Generate {safe_count} strategic TikTok comments.

Target: {"my own video" if safe_target == "own" else "other creators' videos in my niche"}
My persona: {persona}""",
        topic=video_topic,
    ) + f"""

{"For my own video — generate:" if safe_target == "own" else "For other creators' videos — generate:"}

{"For my own video — generate:" if target == "own" else "For other creators' videos — generate:"}

{'''1. **Pin comment** — drives debate or asks a polarizing question
2. **Self-reply** — adds value that wasn't in the video (teases part 2)
3. **Social proof reply** — template response when someone says they bought it
4. **Objection handler** — response to common skeptical comments
5. **Engagement driver** — comment that makes other viewers reply to it''' if target == "own" else
'''1. **Value-add comment** — genuine insight that makes people click your profile
2. **Funny/relatable comment** — personality that stands out in the comments
3. **Question comment** — asks something that positions you as knowledgeable
4. **Debate starter** — respectful disagreement that drives a thread
5. **Collab bait** — comment that naturally opens the door for a collaboration'''}

Each comment should feel human and natural, NEVER generic or spammy."""

    return ask(SYSTEM, prompt, temperature=0.9)


def reply_to_comment(comment: str, video_context: str, product: str = "") -> str:
    if is_injection_attempt(comment):
        return "[BLOCKED] Comment contains suspicious content. Skipping reply generation."

    cfg = load_config()
    style = sanitize_prompt_input(cfg.get("persona_style", "authentic, helpful"), "context")

    prompt = build_prompt(
        f"""Write a reply to this TikTok comment.

My style: {style}

The reply should:
- Feel genuine and personal (not corporate/bot-like)
- Drive further engagement (ask a follow-up or add value)
- If relevant, naturally mention the product or link
- Be concise (1-2 sentences max for TikTok)

Give 2 options: one casual, one that drives action.""",
        comment=comment,
        context=video_context,
        product=product or "none specifically",
    )

    return ask(SYSTEM, prompt, temperature=0.8)


def growth_tasks(current_followers: int = 0) -> str:
    cfg = load_config()
    safe_followers = min(max(int(current_followers), 0), 100_000_000)
    niche = sanitize_prompt_input(cfg.get("persona_niche", "product reviews"), "niche")

    prompt = build_prompt(
        f"""Generate today's growth task list for a TikTok account.

Current followers: {safe_followers or 'new account'}

Create a specific, actionable task list:
1. **5 accounts to engage with** — types of creators to comment on (not specific names)
2. **3 trending videos to stitch/duet** — the type of content to respond to
3. **Comment raid plan** — which hashtags to browse and comment on
4. **Collaboration pitch** — template for reaching out to a similar-sized creator
5. **Community action** — one thing to do that builds loyal followers (not just viewers)

Include time estimates. Total should be under 1 hour of engagement work.""",
        niche=niche,
    )

    return ask(SYSTEM, prompt, temperature=0.8)
