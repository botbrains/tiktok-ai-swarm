"""Shop Agent — TikTok Shop affiliate weekly planning and creative generation.

Responsibilities:
1. select_weekly_slate()       — pick the best N offers for the coming week,
                                 using past performance data when available
2. run_weekly_planning()       — full cycle: select slate → live run-of-show →
                                 write beacons_weekly_pack.md + weekly_offer_slate.json
3. generate_post_creative()    — compliant post script + caption for one offer
4. generate_live_run_of_show() — minute-by-minute live shopping plan for one offer

All post creatives enforce:
- Disclosure in caption + pinned comment (#ad / #affiliate)
- CTA = "tap product anchor" when native TikTok Shop URLs are detected,
  otherwise "link in bio"
- No unverifiable claims (no cures, guarantees, get-rich language)
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from ..llm import ask
from ..config import load_config
from ..security import sanitize_prompt_input, build_prompt
from ..shop.models import ShopOffer, WeeklySlate
from ..shop.store import active_offers, save_slate
from ..shop.analytics import top_offers_by_performance
from ..shop.beacons import write_artifacts


# ── Agent system prompt ────────────────────────────────────────────────

SHOP_AGENT_SYSTEM = """You are a TikTok Shop Affiliate Monetization Agent.

You select weekly product slates, write compliant creatives, and plan live
shopping sessions for a TikTok creator.

Rules you ALWAYS follow:
- Every post MUST include a clear disclosure: "#ad", "#affiliate", or
  "Affiliate link — I earn a commission at no extra cost to you."
- CTA strategy: use "tap the product anchor below the video" when native
  TikTok Shop links are available; otherwise use "link in bio."
- Never make unverifiable claims: no "cures", "guaranteed results",
  "get rich", or exaggerated before/after statements.
- Captions must be under 150 characters (excluding hashtags).
- Live titles must be honest and not mislead on price or availability.
- Disclosures must appear in captions AND as pinned comments.
"""

_DEFAULT_DISCLOSURE = (
    "Some links are affiliate links. "
    "I earn a small commission at no extra cost to you. #ad"
)


def _this_week_monday() -> str:
    """Return the ISO date string of the most recent Monday."""
    today = date.today()
    return (today - timedelta(days=today.weekday())).isoformat()


def _has_native_shop_url(offer: ShopOffer) -> bool:
    url = (offer.tiktok_product_url or "").lower()
    return "shop.tiktok" in url or "shp.tiktok" in url


# ── Weekly slate selection ─────────────────────────────────────────────


def select_weekly_slate(
    n: int = 5,
    focus: str = "",
    use_performance: bool = True,
) -> WeeklySlate:
    """Select the weekly offer slate and persist it.

    Args:
        n:               Maximum number of offers to include.
        focus:           Optional theme/focus (e.g. "back to school").
        use_performance: Prefer top-performing offers when True (default).

    Returns a WeeklySlate that has been saved to the store.
    """
    cfg = load_config()
    offers = active_offers()
    week_of = _this_week_monday()

    if not offers:
        slate = WeeklySlate(
            week_of=week_of,
            offer_ids=[],
            headline="No offers in catalog yet — add some with: tt shop-add-offer",
        )
        save_slate(slate)
        return slate

    n = min(n, len(offers))

    # Prefer top performers; fill remaining slots from the full active list
    top_ids: list[str] = top_offers_by_performance(n) if use_performance else []
    top_id_set = set(top_ids)
    remaining = [o for o in offers if o.offer_id not in top_id_set]
    selected_ids = (top_ids[:n] + [o.offer_id for o in remaining])[: n]

    selected_offers = [o for o in offers if o.offer_id in set(selected_ids)]

    # CTA strategy heuristic: native Shop URLs → product anchor
    has_native = any(_has_native_shop_url(o) for o in selected_offers)
    cta_strategy = "tap_product_anchor" if has_native else "link_in_bio"

    disclosure = cfg.get("shop_disclosure_template", _DEFAULT_DISCLOSURE)

    # Generate a punchy headline via the LLM
    offer_titles = ", ".join(o.title for o in selected_offers)
    headline_prompt = build_prompt(
        "Write a short (max 10 words) punchy weekly headline for a TikTok Shop "
        "creator's Beacons link-in-bio page. Do NOT include specific brand names. "
        "Return only the headline text, nothing else.",
        context=sanitize_prompt_input(focus or offer_titles, "context"),
    )
    headline = ask(SHOP_AGENT_SYSTEM, headline_prompt, temperature=0.8).strip().strip('"')

    slate = WeeklySlate(
        week_of=week_of,
        offer_ids=selected_ids,
        headline=headline,
        cta_strategy=cta_strategy,
        disclosure=disclosure,
    )
    save_slate(slate)
    return slate


# ── Full weekly planning cycle ─────────────────────────────────────────


def run_weekly_planning(
    n: int = 5,
    focus: str = "",
    include_live: bool = True,
) -> dict:
    """Run the complete weekly Shop planning cycle.

    Steps:
    1. Select the weekly offer slate (with LLM-generated headline).
    2. Optionally generate a live shopping run-of-show for the top offer.
    3. Write beacons_weekly_pack_<week>.md and weekly_offer_slate_<week>.json.

    Returns:
        {
          "slate":     WeeklySlate,
          "md_path":   Path,
          "json_path": Path,
        }
    """
    slate = select_weekly_slate(n=n, focus=focus)

    if include_live and slate.offer_ids:
        offer_map = {o.offer_id: o for o in active_offers()}
        feature_offer = offer_map.get(slate.offer_ids[0])
        if feature_offer:
            ros = generate_live_run_of_show(feature_offer)
            slate.live_run_of_show = ros
            save_slate(slate)

    md_path, json_path = write_artifacts(slate, active_offers())
    return {"slate": slate, "md_path": md_path, "json_path": json_path}


# ── Post creative generation ───────────────────────────────────────────


def generate_post_creative(offer: ShopOffer, format: str = "review") -> str:
    """Generate a compliant TikTok post creative for a Shop offer.

    Returns a Markdown string with hook, script, caption, pinned comment,
    and CTA — ready for review and production.
    """
    cfg = load_config()
    disclosure = cfg.get("shop_disclosure_template", _DEFAULT_DISCLOSURE)
    persona = sanitize_prompt_input(cfg.get("persona_name", ""), "product")
    niche = sanitize_prompt_input(cfg.get("persona_niche", ""), "niche")

    cta_method = (
        "tap the product anchor below the video"
        if _has_native_shop_url(offer)
        else "link in bio"
    )

    ALLOWED_FORMATS = {"review", "grwm", "skit", "tutorial", "storytime", "comparison", "trend"}
    safe_format = format if format in ALLOWED_FORMATS else "review"
    price_info = f"${offer.price_usd:.2f}" if offer.price_usd else "see link"

    prompt = build_prompt(
        f"""Write a TikTok Shop affiliate post creative.

Format: {safe_format}
Persona: {persona or "[Creator]"}
Niche: {niche or "lifestyle"}
Price: {price_info}
CTA method: {cta_method}

Compliance requirements (NON-NEGOTIABLE):
- Disclosure MUST appear in caption and pinned comment: "{disclosure}"
- Caption MUST include #ad or #affiliate.
- Use only verifiable claims — no "cures", "guaranteed", or exaggerated results.
- Caption under 150 characters (excluding hashtags).

Deliver:
1. **Hook** (first 1.5 seconds, exact spoken words + first visual)
2. **Script** with camera directions ([FACE CAM], [PRODUCT SHOT], [DEMO], etc.)
3. **Caption** (≤150 chars + hashtags, includes disclosure + #ad)
4. **Pinned comment** (includes disclosure + CTA)
5. **CTA line** referencing: {cta_method}""",
        product=offer.title,
        category=offer.category or "general",
        context=offer.notes or "none",
    )

    return ask(SHOP_AGENT_SYSTEM, prompt, temperature=0.7)


# ── Live shopping run-of-show ──────────────────────────────────────────


def generate_live_run_of_show(
    offer: ShopOffer, duration_min: int = 30
) -> dict:
    """Generate a live shopping run-of-show dict for a featured offer.

    Returns a dict with keys:
      live_title, pinned_comment, segments (list), faq_snippets (list)

    If the LLM returns invalid JSON a safe fallback dict is used.
    """
    cfg = load_config()
    safe_duration = min(max(int(duration_min), 5), 120)
    persona = sanitize_prompt_input(cfg.get("persona_name", "Creator"), "product")
    disclosure = cfg.get("shop_disclosure_template", _DEFAULT_DISCLOSURE)

    prompt = build_prompt(
        f"""Generate a TikTok Live Shopping run-of-show for a {safe_duration}-minute session.

Persona: {persona}
Compliance: every mention of purchasing MUST include the affiliate disclosure.
Disclosure to use: "{disclosure}"

Return ONLY valid JSON (no markdown fences, no extra text) with this exact shape:
{{
  "live_title": "...",
  "pinned_comment": "...",
  "segments": ["0-2 min: ...", "2-5 min: ...", ...],
  "faq_snippets": ["Q: ... A: ...", ...]
}}""",
        product=offer.title,
        context=offer.notes or "standard product live",
    )

    raw = ask(SHOP_AGENT_SYSTEM, prompt, temperature=0.6)

    # Attempt JSON parse; strip optional markdown fences
    try:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = "\n".join(clean.split("\n")[1:])
        if clean.endswith("```"):
            clean = "\n".join(clean.split("\n")[:-1])
        return json.loads(clean)
    except Exception:
        return {
            "live_title": f"Live Shop: {offer.title}",
            "pinned_comment": (
                f"🛒 Tap product anchor to shop! {disclosure}"
            ),
            "segments": [
                f"0-2 min: Welcome + introduce {offer.title}",
                f"2-10 min: Live demo of {offer.title}",
                "10-20 min: Q&A with viewers",
                "20-25 min: Objection handling + social proof",
                "25-30 min: Final CTA + close stream",
            ],
            "faq_snippets": [
                "Q: Where can I buy it?  A: Tap the product anchor below or link in bio.",
                f"Q: Is this sponsored?  A: Yes — {disclosure}",
                "Q: Does it ship fast?  A: Check the product page for current shipping info.",
                "Q: Can I get a discount?  A: Price is set by the seller — check the product page.",
            ],
        }
