"""JSON storage for TikTok Shop offers, weekly slates, and metrics snapshots.

All files live under DATA_DIR/shop/:
  offers.json          — the offer catalog
  weekly_slates.json   — all historical weekly slates
  analytics/
    metrics.json       — ingested performance snapshots
  artifacts/           — generated .md / .json planning artifacts
"""
from __future__ import annotations

import json
from pathlib import Path

from .models import OfferMetricsSnapshot, ShopOffer, WeeklySlate
from ..config import SHOP_DIR

OFFERS_FILE = SHOP_DIR / "offers.json"
SLATES_FILE = SHOP_DIR / "weekly_slates.json"
METRICS_FILE = SHOP_DIR / "analytics" / "metrics.json"


def _ensure_dirs() -> None:
    SHOP_DIR.mkdir(parents=True, exist_ok=True)
    (SHOP_DIR / "analytics").mkdir(parents=True, exist_ok=True)
    (SHOP_DIR / "artifacts").mkdir(parents=True, exist_ok=True)


# ── Offer Catalog ──────────────────────────────────────────────────────


def load_offers() -> list[ShopOffer]:
    """Load all offers from the catalog."""
    if not OFFERS_FILE.exists():
        return []
    with open(OFFERS_FILE) as f:
        return [ShopOffer.from_dict(d) for d in json.load(f)]


def save_offers(offers: list[ShopOffer]) -> None:
    """Persist the full offer catalog."""
    _ensure_dirs()
    with open(OFFERS_FILE, "w") as f:
        json.dump([o.to_dict() for o in offers], f, indent=2)


def add_offer(offer: ShopOffer) -> ShopOffer:
    """Append a new offer to the catalog and persist."""
    offers = load_offers()
    offers.append(offer)
    save_offers(offers)
    return offer


def get_offer(offer_id: str) -> ShopOffer | None:
    """Retrieve a single offer by ID."""
    for o in load_offers():
        if o.offer_id == offer_id:
            return o
    return None


def update_offer(offer_id: str, **kwargs) -> bool:
    """Update named fields on an offer. Returns True if found and saved."""
    offers = load_offers()
    for o in offers:
        if o.offer_id == offer_id:
            for k, v in kwargs.items():
                if hasattr(o, k):
                    setattr(o, k, v)
            save_offers(offers)
            return True
    return False


def active_offers() -> list[ShopOffer]:
    """Return only offers where active=True."""
    return [o for o in load_offers() if o.active]


# ── Weekly Slates ──────────────────────────────────────────────────────


def load_slates() -> list[WeeklySlate]:
    """Load all recorded weekly slates."""
    if not SLATES_FILE.exists():
        return []
    with open(SLATES_FILE) as f:
        return [WeeklySlate.from_dict(d) for d in json.load(f)]


def save_slate(slate: WeeklySlate) -> None:
    """Persist a slate, replacing any existing entry for the same week_of."""
    _ensure_dirs()
    slates = [s for s in load_slates() if s.week_of != slate.week_of]
    slates.append(slate)
    with open(SLATES_FILE, "w") as f:
        json.dump([s.to_dict() for s in slates], f, indent=2)


def current_slate() -> WeeklySlate | None:
    """Return the most recently saved slate, or None."""
    slates = load_slates()
    return slates[-1] if slates else None


# ── Metrics / Analytics ────────────────────────────────────────────────


def load_metrics() -> list[OfferMetricsSnapshot]:
    """Load all persisted metrics snapshots."""
    if not METRICS_FILE.exists():
        return []
    with open(METRICS_FILE) as f:
        return [OfferMetricsSnapshot.from_dict(d) for d in json.load(f)]


def save_metrics(snapshots: list[OfferMetricsSnapshot]) -> None:
    """Overwrite the full metrics log."""
    _ensure_dirs()
    with open(METRICS_FILE, "w") as f:
        json.dump([s.to_dict() for s in snapshots], f, indent=2)


def append_metrics(snapshot: OfferMetricsSnapshot) -> None:
    """Append a single snapshot to the metrics log."""
    snapshots = load_metrics()
    snapshots.append(snapshot)
    save_metrics(snapshots)
