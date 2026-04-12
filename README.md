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

Built by [Swarm Labs USA](https://swarmlabsusa.com)
