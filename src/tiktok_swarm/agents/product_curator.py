"""Product Curator — finds and evaluates products for maximum affiliate revenue."""
from ..llm import ask
from ..config import load_config
from ..knowledge.store import load_knowledge, append_knowledge

SYSTEM = """You are a Product Curator for a TikTok influencer account focused on
affiliate revenue. You find products that are PERFECT for TikTok content.

TikTok product selection is DIFFERENT from other platforms:
1. **Visual impact** — The product must look interesting on camera in the first frame.
   Boring-looking products die on TikTok no matter how useful they are.
2. **Demo-ability** — Can you show it working in 3 seconds? Before/after? Satisfying to watch?
3. **Price point sweet spot** — $15-$60 is the TikTok impulse buy range.
   Under $15 = low commission. Over $60 = too much friction for impulse.
4. **Shareability** — Would someone send this video to a friend? "OMG you need this"
5. **Trend alignment** — Does it connect to a current trend, season, or cultural moment?
6. **Comment bait** — Will people argue about it? Ask questions? Tag friends?

Categories that CRUSH on TikTok:
- Kitchen gadgets (satisfying demos)
- Beauty/skincare (transformation content)
- Home organization (before/after)
- Tech accessories (unboxing + reaction)
- Fitness/wellness (routine integration)
- Cleaning products (satisfying cleaning videos)

Red flags to avoid:
- Products with lots of negative reviews (gets called out in comments)
- Products that look different than advertised (credibility killer)
- Anything requiring complex explanation (TikTok attention span is 3 seconds)
"""


def find_products(category: str = "", count: int = 5, context: str = "") -> str:
    cfg = load_config()
    niche = cfg.get("persona_niche", "")

    perf = load_knowledge("product_performance")
    perf_ctx = f"\nPast product performance data:\n{perf}" if perf else ""

    prompt = f"""Find {count} products optimized for TikTok affiliate content.

Account niche: {niche or 'lifestyle and product reviews'}
Category: {category or 'best opportunity across all categories'}
Context: {context or 'none'}
{perf_ctx}

For each product:
1. **Product type** (not specific brand)
2. **Price range** — sweet spot for impulse buying
3. **Visual hook** — what makes this look amazing on camera in 1 second
4. **Demo concept** — the 3-second demo that sells it
5. **TikTok format** — which video format works best for this product
6. **Trend connection** — how it ties to current trends
7. **Comment bait potential** — what will people say/argue about
8. **Commission estimate** — expected earnings per sale
9. **Content count** — how many unique videos can you make about this ONE product

Rank by: (visual impact * demo-ability * commission) — highest first."""

    return ask(SYSTEM, prompt, temperature=0.8)


def evaluate_product(product: str, price: str = "", url: str = "") -> str:
    prompt = f"""Evaluate this specific product for TikTok content potential.

Product: {product}
Price: {price or 'unknown'}
URL: {url or 'none'}

Score 1-10 on each dimension:
1. **Visual Impact** — does it look interesting on camera?
2. **Demo-ability** — can you show it working in 3 seconds?
3. **Impulse Factor** — will someone buy it immediately after watching?
4. **Content Versatility** — how many different videos can you make?
5. **Comment Potential** — will it drive engagement?
6. **Trend Fit** — does it connect to anything trending?
7. **Commission Value** — is the payout worth the effort?

**OVERALL SCORE** (weighted average)
**VERDICT** — promote it or skip it, with reasoning
**BEST VIDEO FORMAT** — exactly how to present this product
**CONTENT PLAN** — 3 different video concepts for this one product"""

    return ask(SYSTEM, prompt, temperature=0.6)
