"""Analytics joiner for TikTok Shop affiliate performance.

Ingests performance data from TikTok metrics exports and/or Shop affiliate
dashboard snapshots, then computes offer rankings that feed back into the
weekly slate selection.

Ranking logic (in priority order):
1. If orders + commission are available → commission_per_order
2. If only clicks + views        → EPC proxy (clicks per 1,000 views)
3. If only clicks                → total_clicks
4. Else                          → 0  (new/untested offer)
"""
from __future__ import annotations

import csv
from pathlib import Path

from .models import OfferMetricsSnapshot
from .store import (
    active_offers,
    append_metrics,
    load_metrics,
    load_offers,
)


# ── Ranking ────────────────────────────────────────────────────────────


def compute_rankings() -> list[dict]:
    """Compute offer rankings from all available metrics snapshots.

    Returns a list of dicts sorted by score descending.  Each dict contains:
      offer_id, title, score, metric_used, views, clicks, orders, commission
    """
    snapshots = load_metrics()
    offers = {o.offer_id: o for o in load_offers()}

    # Aggregate raw stats per offer
    agg: dict[str, dict] = {}
    for s in snapshots:
        if s.offer_id not in agg:
            agg[s.offer_id] = {"views": 0, "clicks": 0, "orders": 0, "commission": 0.0}
        agg[s.offer_id]["views"] += s.views
        agg[s.offer_id]["clicks"] += s.clicks
        agg[s.offer_id]["orders"] += s.orders
        agg[s.offer_id]["commission"] += s.commission

    rankings: list[dict] = []

    for offer_id, stats in agg.items():
        offer = offers.get(offer_id)
        title = offer.title if offer else offer_id

        if stats["orders"] > 0:
            score = stats["commission"] / stats["orders"]
            metric_used = "commission_per_order"
        elif stats["views"] > 0 and stats["clicks"] > 0:
            # Clicks per 1,000 impressions (EPC proxy)
            score = (stats["clicks"] / stats["views"]) * 1000
            metric_used = "epc_proxy_ctr_per_mille"
        elif stats["clicks"] > 0:
            score = float(stats["clicks"])
            metric_used = "total_clicks"
        else:
            score = 0.0
            metric_used = "none"

        rankings.append(
            {
                "offer_id": offer_id,
                "title": title,
                "score": round(score, 4),
                "metric_used": metric_used,
                **stats,
            }
        )

    # Include active offers with no data yet so callers see the full picture
    ranked_ids = {r["offer_id"] for r in rankings}
    for offer in active_offers():
        if offer.offer_id not in ranked_ids:
            rankings.append(
                {
                    "offer_id": offer.offer_id,
                    "title": offer.title,
                    "score": 0.0,
                    "metric_used": "no_data",
                    "views": 0,
                    "clicks": 0,
                    "orders": 0,
                    "commission": 0.0,
                }
            )

    return sorted(rankings, key=lambda x: x["score"], reverse=True)


def top_offers_by_performance(n: int = 5) -> list[str]:
    """Return the offer_ids of the top *n* performing offers.

    Used by shop_agent to bias weekly slate selection toward proven winners.
    """
    return [r["offer_id"] for r in compute_rankings()[:n]]


# ── Ingestion helpers ──────────────────────────────────────────────────


def ingest_snapshot(data: dict) -> OfferMetricsSnapshot:
    """Ingest a single metrics snapshot from a dict and persist it.

    Expected keys (all optional except offer_id):
      offer_id, date, views, clicks, orders, commission, video_id, source
    """
    snap = OfferMetricsSnapshot.from_dict(data)
    append_metrics(snap)
    return snap


def ingest_csv_export(path: str | Path) -> int:
    """Ingest a CSV export from TikTok or the Shop affiliate dashboard.

    Expected CSV columns (header row required, order flexible):
      offer_id, date, views, clicks, orders, commission, video_id, source

    Returns the count of records successfully ingested.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    count = 0
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            offer_id = row.get("offer_id", "").strip()
            if not offer_id:
                continue
            snap = OfferMetricsSnapshot(
                offer_id=offer_id,
                date=row.get("date", "").strip(),
                views=int(row.get("views") or 0),
                clicks=int(row.get("clicks") or 0),
                orders=int(row.get("orders") or 0),
                commission=float(row.get("commission") or 0.0),
                video_id=row.get("video_id", "").strip(),
                source=row.get("source", "csv_export").strip() or "csv_export",
            )
            append_metrics(snap)
            count += 1

    return count
