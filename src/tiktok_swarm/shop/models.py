"""Data models for TikTok Shop affiliate monetization.

Three core models:
- ShopOffer       — a single affiliate product in the catalog
- WeeklySlate     — the weekly selection of offers + planning artifacts
- OfferMetricsSnapshot — a point-in-time performance snapshot for one offer
"""
from __future__ import annotations

import dataclasses
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class ShopOffer:
    """A TikTok Shop affiliate product offer in the catalog."""

    offer_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    category: str = ""
    price_usd: float = 0.0
    commission_rate: float = 0.0  # fraction, e.g. 0.10 = 10 %
    tiktok_product_url: str = ""
    region: str = "US"
    active: bool = True
    added_at: str = field(default_factory=lambda: date.today().isoformat())
    notes: str = ""

    # ── serialization ──────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ShopOffer":
        known = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in known})

    # ── helpers ────────────────────────────────────────────────────────

    @property
    def estimated_commission(self) -> float:
        """Estimated commission for a single sale."""
        return round(self.price_usd * self.commission_rate, 4)


@dataclass
class WeeklySlate:
    """The weekly selection of TikTok Shop offers plus planning artifacts."""

    week_of: str = field(default_factory=lambda: date.today().isoformat())
    offer_ids: list = field(default_factory=list)
    headline: str = ""
    # "tap_product_anchor" when native TikTok Shop links are available,
    # otherwise "link_in_bio" for Beacons / external page
    cta_strategy: str = "link_in_bio"
    disclosure: str = (
        "Some links are affiliate links. "
        "I earn a small commission at no extra cost to you. #ad"
    )
    live_run_of_show: Optional[dict] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "WeeklySlate":
        known = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in known})


@dataclass
class OfferMetricsSnapshot:
    """Point-in-time performance snapshot for one offer.

    Ingested from TikTok metrics exports or Shop affiliate dashboards.
    """

    offer_id: str = ""
    date: str = field(default_factory=lambda: date.today().isoformat())
    views: int = 0
    clicks: int = 0
    orders: int = 0
    commission: float = 0.0
    video_id: str = ""
    # "tiktok_export" | "shop_affiliate_dashboard" | "csv_export" | "manual"
    source: str = "manual"

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "OfferMetricsSnapshot":
        known = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in known})
