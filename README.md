# TikTok AI Swarm

Autonomous AI TikTok influencer pipeline. 8 agents handle content strategy, script writing, video production, posting, live streaming, engagement, and analytics. Runs 24/7 on your machine.

## Architecture

```
Content Strategist ──→ Script Writer ──→ Avatar Generator ──→ TikTok Poster
       ↑                                                          ↓
Product Curator     SEO Optimizer     Live Director          Post Queue
       ↑                                   ↓                     ↓
       └──────── Analytics Agent ←── Engagement Manager ←── Published
                    (feedback loop to all agents)
```

## Agents

| Agent | Job | Commands |
|-------|-----|----------|
| **Content Strategist** | Plans content calendar, trend analysis | `tt plan-week`, `tt plan-today`, `tt trends` |
| **Script Writer** | TikTok-optimized video scripts | `tt script`, `tt live-script`, `tt series` |
| **Product Curator** | Finds high-conversion products | `tt products`, `tt evaluate` |
| **SEO Optimizer** | Hashtags, captions, posting times | `tt hashtags`, `tt best-times` |
| **Engagement Manager** | Comments, growth tactics, community | `tt comments`, `tt reply`, `tt growth` |
| **Live Director** | Plans and manages TikTok LIVE sessions | `tt plan-live`, `tt live-reply` |
| **Analytics Agent** | Tracks performance, optimizes strategy | `tt log-post`, `tt analyze`, `tt dashboard` |
| **Avatar Generator** | AI avatar video creation | `tt generate-video`, `tt voice` |
| **Shop Agent** | TikTok Shop affiliate weekly planning | `tt shop-week`, `tt shop-offers`, `tt shop-add-offer`, `tt shop-creative`, `tt shop-ingest`, `tt shop-rankings` |

## Install

```bash
git clone https://github.com/michaelwinczuk/tiktok-ai-swarm.git
cd tiktok-ai-swarm

# Pull a model
ollama pull qwen2.5:32b   # Best for M4 Max 48GB
# OR
ollama pull qwen2.5:7b    # Good for 16GB machines

pip install -e .
tt setup
```

## Quick Start

```bash
# Plan your week
tt plan-week --focus "launch week, establish niche"

# Find products to promote
tt products -c "kitchen gadgets" -n 5

# Create a video script
tt script "portable blender" --format review --duration 30s

# Generate hooks and SEO
tt hashtags "kitchen gadgets"
tt best-times

# Plan a live session
tt plan-live "portable blender" --duration 30

# Get today's growth tasks
tt growth --followers 0

# Start the 24/7 daemon
tt daemon
```

## Content Creation Flow

```bash
# 1. Find a product
tt products -c "tech accessories"

# 2. Write the script
tt script "MagSafe wallet" -f review -d 30s

# 3. Generate AI avatar video (requires HeyGen or D-ID)
tt generate-video "Your script text here"

# 4. Video goes to approval queue
tt queue                    # See pending posts
tt approve 1                # Approve post #1
tt publish                  # Publish approved posts to TikTok
```

## Live Streaming

```bash
# Full live session prep
tt plan-live "portable blender" -d 30

# During live — generate real-time replies
tt live-reply "does it really crush ice?" "portable blender"
tt live-reply "how much is it?" "portable blender"
tt live-reply "seems too good to be true" "portable blender"
```

## Analytics

```bash
# Log performance
tt log-post "Blender review" -f review -p "portable blender" -v 50000 -l 3000 -c 200 -s 150 --saves 400 --follows 50 -k 800 -$ 340

# AI analysis
tt analyze

# Dashboard view
tt dashboard
```

## 24/7 Daemon

The daemon runs autonomously on a schedule:

```bash
tt daemon
```

It will:
- Generate daily content plans at 7:00 AM
- Create and queue posts at your configured times (default: 9am, 1pm, 7pm)
- Run engagement tasks 3x daily
- Require approval before posting (configurable)

## Avatar Backends

| Backend | Quality | Cost | Setup |
|---------|---------|------|-------|
| **HeyGen** | Excellent | ~$0.50/video | API key + avatar creation |
| **D-ID** | Good | ~$0.30/video | API key |
| **Local** | Experimental | Free | GPU + Wav2Lip |
| **None** | Script-only | Free | No video generation |

## Voice Backends

| Backend | Quality | Cost |
|---------|---------|------|
| **ElevenLabs** | Human-like | ~$0.01/1K chars |
| **Local (Coqui)** | Good | Free |
| **None** | Manual recording | Free |

## Growth Milestones

| Milestone | Unlocks | Timeline |
|-----------|---------|----------|
| 1,000 followers | TikTok LIVE | 2-4 weeks |
| 10,000 followers | Bio link (affiliate revenue) | 1-3 months |
| 100,000 followers | Brand deals | 3-6 months |
| 100,000+ | Creator Fund + partnerships | 6-12 months |

---

## TikTok Shop Affiliate Monetization (Beacons)

Monetize with TikTok Shop affiliate links using a free [Beacons](https://beacons.ai)
link-in-bio page. No paid API required — the workflow generates ready-to-paste content.

### Setup

1. Create a free account at [beacons.ai](https://beacons.ai) and set up your page.

2. Add your Beacons URL to config (or set the `BEACONS_URL` environment variable):

```bash
# Option A — interactive setup
tt setup
# → answer "Beacons URL" prompt

# Option B — environment variable (recommended for 24/7 deployments)
export BEACONS_URL="https://beacons.ai/yourhandle"
export SHOP_DISCLOSURE="Some links are affiliate links. I earn a commission at no extra cost to you. #ad"
```

3. Add your TikTok Shop affiliate products to the catalog:

```bash
tt shop-add-offer
# → enter title, category, price, commission rate, product URL, region
```

### Weekly Beacons Workflow

Run the weekly planner every Monday (or let the daemon handle it):

```bash
tt shop-week                          # standard run (5 offers, includes live plan)
tt shop-week --focus "summer deals"   # with a theme
tt shop-week --offers 3 --no-live     # 3 offers, skip live run-of-show
```

**Output files** (written to `data/shop/artifacts/`):

| File | Purpose |
|------|---------|
| `beacons_weekly_pack_<week>.md` | Copy/paste-ready Beacons update: headline, disclosure, ordered links, CTA strategy, live promo blurb |
| `weekly_offer_slate_<week>.json` | Machine-readable slate: week_of, offers array, CTA strategy, live run-of-show |

**Manual step** — copy the contents of `beacons_weekly_pack_*.md` into your Beacons
dashboard: update the page title, paste in the links in order, and copy the disclosure
text into the page description. No API call needed.

### Offer Management

```bash
tt shop-offers              # list all offers in the catalog
tt shop-add-offer           # interactively add a new offer
```

### Post Creatives

Generate a compliant script + caption for any offer in your catalog:

```bash
tt shop-creative <offer_id>                      # review format (default)
tt shop-creative <offer_id> --format tutorial    # tutorial format
```

All creatives include:
- Disclosure in caption (`#ad` / `#affiliate`)
- Disclosure as pinned comment text
- CTA: "tap product anchor" for native TikTok Shop URLs, otherwise "link in bio"

### Analytics & Performance Feedback

Ingest exports from TikTok analytics or the Shop affiliate dashboard to feed next
week's offer selection:

```bash
# Ingest a CSV export (columns: offer_id, date, views, clicks, orders, commission, ...)
tt shop-ingest path/to/export.csv

# View current performance rankings
tt shop-rankings
```

Rankings are computed automatically:
- If orders + commission data available → `commission_per_order`
- If only clicks + views → `EPC proxy` (clicks per 1 000 views)
- New/untested offers → score 0 (shown at bottom, eligible for selection)

Top-performing offers are automatically preferred in the next `tt shop-week` run.

### 24/7 Daemon — Weekly Schedule

The daemon (`tt daemon`) runs the weekly shop planning cycle every **Monday at 06:00**:

```
Monday 06:00 → shop_weekly_cycle()
  → select_weekly_slate (top performers first)
  → generate live run-of-show for the featured offer
  → write data/shop/artifacts/beacons_weekly_pack_*.md
  → write data/shop/artifacts/weekly_offer_slate_*.json
  → log reminder to manually update Beacons
```

### Compliance / Disclosure Templates

The following templates are built into `beacons.py` (`DISCLOSURE_TEMPLATES`).
Use the one appropriate for your platform and audience:

| Template | Text |
|----------|------|
| **short** | `#ad — affiliate link, I earn a small commission.` |
| **medium** | `Some links on this page are affiliate links. I earn a small commission if you purchase — at no extra cost to you. #ad` |
| **full** | `Disclosure: This page contains affiliate links to products I recommend. As a TikTok Shop affiliate I may earn a commission on qualifying purchases at no additional cost to you. I only promote products I have reviewed or believe in. #ad #affiliate` |

**Where disclosures must appear (FTC / TikTok policy):**
- Top of your Beacons/link-in-bio page
- In every post caption (before hashtags)
- As a pinned comment on every affiliate post
- Verbally if your video features a direct product demo

Disclosures are included automatically in all `tt shop-creative` and
`tt shop-week` outputs.

### Data Layout

```
data/shop/
├── offers.json              ← offer catalog
├── weekly_slates.json       ← all historical weekly slates
├── analytics/
│   └── metrics.json         ← ingested performance snapshots
└── artifacts/
    ├── beacons_weekly_pack_2025-01-06.md
    ├── weekly_offer_slate_2025-01-06.json
    └── ...
```

---

Built by [Swarm Labs USA](https://swarmlabsusa.com)
