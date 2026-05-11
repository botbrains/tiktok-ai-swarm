"""Unit tests for the TikTok Shop affiliate monetization module.

Tests cover:
- Model serialization / deserialization (no I/O)
- Store CRUD (patched to a temp directory)
- Analytics rankings computation
- Beacons artifact generation (no LLM calls)
- shop_agent.select_weekly_slate (LLM mocked)
"""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import pytest


# ── helpers ────────────────────────────────────────────────────────────


def _patch_store(monkeypatch, tmp_path):
    """Redirect all store file paths to tmp_path."""
    import tiktok_swarm.shop.store as store_mod

    monkeypatch.setattr(store_mod, "OFFERS_FILE", tmp_path / "offers.json")
    monkeypatch.setattr(store_mod, "SLATES_FILE", tmp_path / "slates.json")
    monkeypatch.setattr(store_mod, "METRICS_FILE", tmp_path / "metrics.json")
    return store_mod


def _patch_artifacts(monkeypatch, tmp_path):
    import tiktok_swarm.shop.beacons as beacons_mod

    artifacts_dir = tmp_path / "artifacts"
    monkeypatch.setattr(beacons_mod, "ARTIFACTS_DIR", artifacts_dir)
    return beacons_mod


# ── Model tests ────────────────────────────────────────────────────────


class TestShopOfferModel:
    def test_roundtrip(self):
        from tiktok_swarm.shop.models import ShopOffer

        o = ShopOffer(
            offer_id="abc123",
            title="Portable Blender",
            category="kitchen",
            price_usd=24.99,
            commission_rate=0.08,
            tiktok_product_url="https://shop.tiktok.com/p/abc",
        )
        d = o.to_dict()
        o2 = ShopOffer.from_dict(d)

        assert o2.offer_id == "abc123"
        assert o2.title == "Portable Blender"
        assert o2.price_usd == 24.99
        assert o2.commission_rate == 0.08
        assert o2.active is True

    def test_estimated_commission(self):
        from tiktok_swarm.shop.models import ShopOffer

        o = ShopOffer(price_usd=50.0, commission_rate=0.10)
        assert abs(o.estimated_commission - 5.0) < 1e-9

    def test_from_dict_ignores_unknown_keys(self):
        from tiktok_swarm.shop.models import ShopOffer

        d = {"title": "Widget", "unknown_field": "should_be_ignored", "price_usd": 10.0}
        o = ShopOffer.from_dict(d)
        assert o.title == "Widget"
        assert o.price_usd == 10.0

    def test_default_offer_id_is_unique(self):
        from tiktok_swarm.shop.models import ShopOffer

        ids = {ShopOffer().offer_id for _ in range(20)}
        assert len(ids) == 20


class TestWeeklySlateModel:
    def test_roundtrip(self):
        from tiktok_swarm.shop.models import WeeklySlate

        s = WeeklySlate(
            week_of="2025-01-06",
            offer_ids=["a1", "b2"],
            headline="Big week",
            cta_strategy="tap_product_anchor",
        )
        d = s.to_dict()
        s2 = WeeklySlate.from_dict(d)

        assert s2.week_of == "2025-01-06"
        assert s2.offer_ids == ["a1", "b2"]
        assert s2.cta_strategy == "tap_product_anchor"

    def test_default_disclosure_present(self):
        from tiktok_swarm.shop.models import WeeklySlate

        s = WeeklySlate()
        assert "#ad" in s.disclosure.lower() or "affiliate" in s.disclosure.lower()


class TestOfferMetricsSnapshotModel:
    def test_roundtrip(self):
        from tiktok_swarm.shop.models import OfferMetricsSnapshot

        snap = OfferMetricsSnapshot(offer_id="x1", views=1000, clicks=50, orders=3, commission=9.0)
        d = snap.to_dict()
        snap2 = OfferMetricsSnapshot.from_dict(d)

        assert snap2.offer_id == "x1"
        assert snap2.views == 1000
        assert snap2.commission == 9.0


# ── Store CRUD tests ───────────────────────────────────────────────────


class TestStoreCRUD:
    def test_add_and_load_offer(self, monkeypatch, tmp_path):
        store = _patch_store(monkeypatch, tmp_path)
        from tiktok_swarm.shop.models import ShopOffer

        o = ShopOffer(title="Gadget A", price_usd=25.0)
        store.add_offer(o)

        loaded = store.load_offers()
        assert len(loaded) == 1
        assert loaded[0].title == "Gadget A"

    def test_get_offer(self, monkeypatch, tmp_path):
        store = _patch_store(monkeypatch, tmp_path)
        from tiktok_swarm.shop.models import ShopOffer

        o = ShopOffer(offer_id="test01", title="Widget")
        store.add_offer(o)

        found = store.get_offer("test01")
        assert found is not None
        assert found.title == "Widget"

        not_found = store.get_offer("nonexistent")
        assert not_found is None

    def test_update_offer(self, monkeypatch, tmp_path):
        store = _patch_store(monkeypatch, tmp_path)
        from tiktok_swarm.shop.models import ShopOffer

        o = ShopOffer(offer_id="upd01", title="Old Name", price_usd=10.0)
        store.add_offer(o)

        result = store.update_offer("upd01", price_usd=20.0, title="New Name")
        assert result is True

        updated = store.get_offer("upd01")
        assert updated.price_usd == 20.0
        assert updated.title == "New Name"

    def test_update_nonexistent_offer(self, monkeypatch, tmp_path):
        store = _patch_store(monkeypatch, tmp_path)
        assert store.update_offer("ghost", price_usd=99.0) is False

    def test_active_offers_filter(self, monkeypatch, tmp_path):
        store = _patch_store(monkeypatch, tmp_path)
        from tiktok_swarm.shop.models import ShopOffer

        store.add_offer(ShopOffer(title="Active", active=True))
        store.add_offer(ShopOffer(title="Inactive", active=False))

        active = store.active_offers()
        assert len(active) == 1
        assert active[0].title == "Active"

    def test_save_and_load_slate(self, monkeypatch, tmp_path):
        store = _patch_store(monkeypatch, tmp_path)
        from tiktok_swarm.shop.models import WeeklySlate

        s = WeeklySlate(week_of="2025-02-03", offer_ids=["x", "y"])
        store.save_slate(s)

        slates = store.load_slates()
        assert len(slates) == 1
        assert slates[0].week_of == "2025-02-03"

    def test_save_slate_replaces_same_week(self, monkeypatch, tmp_path):
        store = _patch_store(monkeypatch, tmp_path)
        from tiktok_swarm.shop.models import WeeklySlate

        store.save_slate(WeeklySlate(week_of="2025-02-03", headline="First"))
        store.save_slate(WeeklySlate(week_of="2025-02-03", headline="Updated"))

        slates = store.load_slates()
        assert len(slates) == 1
        assert slates[0].headline == "Updated"

    def test_current_slate_none_when_empty(self, monkeypatch, tmp_path):
        store = _patch_store(monkeypatch, tmp_path)
        assert store.current_slate() is None

    def test_append_and_load_metrics(self, monkeypatch, tmp_path):
        store = _patch_store(monkeypatch, tmp_path)
        from tiktok_swarm.shop.models import OfferMetricsSnapshot

        store.append_metrics(OfferMetricsSnapshot(offer_id="m1", views=500, clicks=20))
        store.append_metrics(OfferMetricsSnapshot(offer_id="m1", views=300, clicks=10))

        snaps = store.load_metrics()
        assert len(snaps) == 2
        assert sum(s.views for s in snaps) == 800


# ── Analytics ranking tests ────────────────────────────────────────────


class TestAnalyticsRankings:
    def _setup(self, monkeypatch, tmp_path):
        store = _patch_store(monkeypatch, tmp_path)
        import tiktok_swarm.shop.analytics as analytics_mod

        # analytics uses the same store module functions, which are already patched
        return store, analytics_mod

    def test_empty_rankings(self, monkeypatch, tmp_path):
        store, analytics = self._setup(monkeypatch, tmp_path)
        rankings = analytics.compute_rankings()
        assert rankings == []

    def test_ranking_with_orders(self, monkeypatch, tmp_path):
        store, analytics = self._setup(monkeypatch, tmp_path)
        from tiktok_swarm.shop.models import ShopOffer, OfferMetricsSnapshot

        store.save_offers([ShopOffer(offer_id="o1", title="Offer 1")])
        store.append_metrics(OfferMetricsSnapshot(offer_id="o1", orders=4, commission=20.0))

        rankings = analytics.compute_rankings()
        assert len(rankings) == 1
        assert rankings[0]["metric_used"] == "commission_per_order"
        assert abs(rankings[0]["score"] - 5.0) < 1e-6

    def test_ranking_epc_proxy(self, monkeypatch, tmp_path):
        store, analytics = self._setup(monkeypatch, tmp_path)
        from tiktok_swarm.shop.models import ShopOffer, OfferMetricsSnapshot

        store.save_offers([ShopOffer(offer_id="o2", title="Offer 2")])
        store.append_metrics(OfferMetricsSnapshot(offer_id="o2", views=2000, clicks=100))

        rankings = analytics.compute_rankings()
        assert rankings[0]["metric_used"] == "epc_proxy_ctr_per_mille"
        assert abs(rankings[0]["score"] - 50.0) < 1e-6  # 100/2000*1000 = 50

    def test_ranking_order_commission_beats_epc(self, monkeypatch, tmp_path):
        """Offer with orders+commission ranks by commission_per_order, not EPC."""
        store, analytics = self._setup(monkeypatch, tmp_path)
        from tiktok_swarm.shop.models import ShopOffer, OfferMetricsSnapshot

        store.save_offers([
            ShopOffer(offer_id="o1", title="Has Orders"),
            ShopOffer(offer_id="o2", title="Has Clicks"),
        ])
        store.append_metrics(OfferMetricsSnapshot(offer_id="o1", orders=1, commission=2.0))
        store.append_metrics(OfferMetricsSnapshot(offer_id="o2", views=100, clicks=80))

        rankings = analytics.compute_rankings()
        # o2 EPC proxy = 800, o1 comm_per_order = 2.0 → o2 ranks higher
        assert rankings[0]["offer_id"] == "o2"
        assert rankings[1]["offer_id"] == "o1"

    def test_active_offers_without_data_appear_at_bottom(self, monkeypatch, tmp_path):
        store, analytics = self._setup(monkeypatch, tmp_path)
        from tiktok_swarm.shop.models import ShopOffer, OfferMetricsSnapshot

        store.save_offers([
            ShopOffer(offer_id="has_data", title="Has Data"),
            ShopOffer(offer_id="no_data", title="No Data"),
        ])
        store.append_metrics(OfferMetricsSnapshot(offer_id="has_data", clicks=10))

        rankings = analytics.compute_rankings()
        assert len(rankings) == 2
        assert rankings[-1]["offer_id"] == "no_data"
        assert rankings[-1]["metric_used"] == "no_data"

    def test_top_offers_by_performance(self, monkeypatch, tmp_path):
        store, analytics = self._setup(monkeypatch, tmp_path)
        from tiktok_swarm.shop.models import ShopOffer, OfferMetricsSnapshot

        store.save_offers([
            ShopOffer(offer_id="a", title="A"),
            ShopOffer(offer_id="b", title="B"),
        ])
        store.append_metrics(OfferMetricsSnapshot(offer_id="a", clicks=100))
        store.append_metrics(OfferMetricsSnapshot(offer_id="b", clicks=10))

        top = analytics.top_offers_by_performance(1)
        assert top == ["a"]

    def test_ingest_csv_export(self, monkeypatch, tmp_path):
        store, analytics = self._setup(monkeypatch, tmp_path)

        csv_file = tmp_path / "perf.csv"
        csv_file.write_text(
            "offer_id,date,views,clicks,orders,commission,video_id,source\n"
            "offer1,2025-01-06,1000,50,2,6.0,vid_001,tiktok_export\n"
            "offer2,2025-01-06,500,10,0,0.0,,csv_export\n",
            encoding="utf-8",
        )

        count = analytics.ingest_csv_export(csv_file)
        assert count == 2

        metrics = store.load_metrics()
        assert len(metrics) == 2
        assert metrics[0].offer_id == "offer1"
        assert metrics[0].orders == 2

    def test_ingest_csv_skips_missing_offer_id(self, monkeypatch, tmp_path):
        store, analytics = self._setup(monkeypatch, tmp_path)

        csv_file = tmp_path / "bad.csv"
        csv_file.write_text(
            "offer_id,views,clicks\n"
            ",100,5\n"        # missing offer_id — should be skipped
            "ok_id,200,10\n",
            encoding="utf-8",
        )

        count = analytics.ingest_csv_export(csv_file)
        assert count == 1

    def test_ingest_csv_file_not_found(self, monkeypatch, tmp_path):
        _, analytics = self._setup(monkeypatch, tmp_path)
        with pytest.raises(FileNotFoundError):
            analytics.ingest_csv_export(tmp_path / "nonexistent.csv")


# ── Beacons artifact generation tests ─────────────────────────────────


class TestBeaconsArtifacts:
    def _patch_config(self, monkeypatch):
        import tiktok_swarm.shop.beacons as beacons_mod
        monkeypatch.setattr(
            beacons_mod,
            "load_config",
            lambda: {"beacons_url": "https://beacons.ai/testhandle"},
        )

    def test_generate_beacons_pack_contains_headline(self, monkeypatch, tmp_path):
        beacons = _patch_artifacts(monkeypatch, tmp_path)
        self._patch_config(monkeypatch)
        from tiktok_swarm.shop.models import ShopOffer, WeeklySlate

        slate = WeeklySlate(
            week_of="2025-01-06",
            offer_ids=["x1"],
            headline="Top Picks This Week",
            disclosure="Affiliate link. #ad",
            cta_strategy="link_in_bio",
        )
        offers = [ShopOffer(offer_id="x1", title="Cool Gadget", price_usd=19.99)]

        md = beacons.generate_beacons_pack(slate, offers)

        assert "Top Picks This Week" in md
        assert "Cool Gadget" in md
        assert "$19.99" in md
        assert "Affiliate link" in md
        assert "beacons.ai/testhandle" in md

    def test_generate_beacons_pack_cta_strategy_tap_anchor(self, monkeypatch, tmp_path):
        beacons = _patch_artifacts(monkeypatch, tmp_path)
        self._patch_config(monkeypatch)
        from tiktok_swarm.shop.models import ShopOffer, WeeklySlate

        slate = WeeklySlate(
            week_of="2025-01-06",
            offer_ids=["y1"],
            cta_strategy="tap_product_anchor",
        )
        offers = [ShopOffer(offer_id="y1", title="Skincare Set")]

        md = beacons.generate_beacons_pack(slate, offers)
        assert "product anchor" in md.lower()

    def test_generate_beacons_pack_with_live_run_of_show(self, monkeypatch, tmp_path):
        beacons = _patch_artifacts(monkeypatch, tmp_path)
        self._patch_config(monkeypatch)
        from tiktok_swarm.shop.models import ShopOffer, WeeklySlate

        slate = WeeklySlate(
            week_of="2025-01-06",
            offer_ids=["z1"],
            live_run_of_show={
                "live_title": "Live Shop Monday",
                "pinned_comment": "Tap anchor to shop! #ad",
                "segments": ["0-2 min: Welcome"],
                "faq_snippets": ["Q: Where to buy? A: Tap anchor."],
            },
        )
        offers = [ShopOffer(offer_id="z1", title="Widget")]

        md = beacons.generate_beacons_pack(slate, offers)
        assert "Live Shop Monday" in md
        assert "0-2 min: Welcome" in md
        assert "Where to buy?" in md

    def test_write_artifacts_creates_files(self, monkeypatch, tmp_path):
        beacons = _patch_artifacts(monkeypatch, tmp_path)
        self._patch_config(monkeypatch)
        from tiktok_swarm.shop.models import ShopOffer, WeeklySlate

        slate = WeeklySlate(
            week_of="2025-01-06",
            offer_ids=["a1"],
            headline="Great Deals",
        )
        offers = [ShopOffer(offer_id="a1", title="Blender", price_usd=29.99)]

        md_path, json_path = beacons.write_artifacts(slate, offers)

        assert md_path.exists()
        assert json_path.exists()

        md_text = md_path.read_text()
        assert "Great Deals" in md_text
        assert "Blender" in md_text

        slate_data = json.loads(json_path.read_text())
        assert slate_data["week_of"] == "2025-01-06"
        assert len(slate_data["offers"]) == 1
        assert slate_data["offers"][0]["title"] == "Blender"
        assert slate_data["cta_strategy"] == "link_in_bio"

    def test_write_artifacts_json_has_required_keys(self, monkeypatch, tmp_path):
        beacons = _patch_artifacts(monkeypatch, tmp_path)
        self._patch_config(monkeypatch)
        from tiktok_swarm.shop.models import ShopOffer, WeeklySlate

        slate = WeeklySlate(week_of="2025-03-10", offer_ids=[])
        _, json_path = beacons.write_artifacts(slate, [])

        data = json.loads(json_path.read_text())
        for key in ("week_of", "offers", "cta_strategy", "disclosure", "live_run_of_show"):
            assert key in data, f"Missing key: {key}"

    def test_disclosure_templates_exported(self):
        from tiktok_swarm.shop.beacons import DISCLOSURE_TEMPLATES

        assert "short" in DISCLOSURE_TEMPLATES
        assert "medium" in DISCLOSURE_TEMPLATES
        assert "full" in DISCLOSURE_TEMPLATES
        for tmpl in DISCLOSURE_TEMPLATES.values():
            assert "affiliate" in tmpl.lower() or "#ad" in tmpl.lower()


# ── shop_agent selection tests (LLM mocked) ───────────────────────────


class TestShopAgentSelection:
    def _setup(self, monkeypatch, tmp_path):
        store = _patch_store(monkeypatch, tmp_path)
        _patch_artifacts(monkeypatch, tmp_path)

        # Mock the LLM so tests don't need Ollama
        import tiktok_swarm.agents.shop_agent as agent_mod
        monkeypatch.setattr(agent_mod, "ask", lambda *a, **kw: "Top Deals This Week")

        # Mock load_config to provide a minimal config
        monkeypatch.setattr(
            agent_mod,
            "load_config",
            lambda: {"shop_disclosure_template": "Affiliate. #ad", "beacons_url": ""},
        )

        return store, agent_mod

    def test_select_weekly_slate_no_offers(self, monkeypatch, tmp_path):
        store, agent = self._setup(monkeypatch, tmp_path)
        from tiktok_swarm.agents.shop_agent import select_weekly_slate

        slate = select_weekly_slate()
        assert slate.offer_ids == []
        assert "No offers" in slate.headline

    def test_select_weekly_slate_picks_active_offers(self, monkeypatch, tmp_path):
        store, agent = self._setup(monkeypatch, tmp_path)
        from tiktok_swarm.shop.models import ShopOffer
        from tiktok_swarm.agents.shop_agent import select_weekly_slate

        store.save_offers([
            ShopOffer(offer_id="a1", title="Offer A", active=True),
            ShopOffer(offer_id="b1", title="Offer B", active=True),
            ShopOffer(offer_id="c1", title="Inactive", active=False),
        ])

        slate = select_weekly_slate(n=5)
        assert len(slate.offer_ids) == 2  # only 2 active
        assert "c1" not in slate.offer_ids

    def test_select_weekly_slate_caps_at_n(self, monkeypatch, tmp_path):
        store, agent = self._setup(monkeypatch, tmp_path)
        from tiktok_swarm.shop.models import ShopOffer
        from tiktok_swarm.agents.shop_agent import select_weekly_slate

        store.save_offers([
            ShopOffer(offer_id=f"o{i}", title=f"Offer {i}", active=True)
            for i in range(10)
        ])

        slate = select_weekly_slate(n=3)
        assert len(slate.offer_ids) == 3

    def test_select_weekly_slate_native_url_sets_tap_anchor(self, monkeypatch, tmp_path):
        store, agent = self._setup(monkeypatch, tmp_path)
        from tiktok_swarm.shop.models import ShopOffer
        from tiktok_swarm.agents.shop_agent import select_weekly_slate

        store.save_offers([
            ShopOffer(
                offer_id="native1",
                title="Native Product",
                tiktok_product_url="https://shop.tiktok.com/product/123",
                active=True,
            )
        ])

        slate = select_weekly_slate()
        assert slate.cta_strategy == "tap_product_anchor"

    def test_select_weekly_slate_external_url_sets_link_in_bio(self, monkeypatch, tmp_path):
        store, agent = self._setup(monkeypatch, tmp_path)
        from tiktok_swarm.shop.models import ShopOffer
        from tiktok_swarm.agents.shop_agent import select_weekly_slate

        store.save_offers([
            ShopOffer(
                offer_id="ext1",
                title="External Product",
                tiktok_product_url="https://amazon.com/dp/B001",
                active=True,
            )
        ])

        slate = select_weekly_slate()
        assert slate.cta_strategy == "link_in_bio"

    def test_select_weekly_slate_persists(self, monkeypatch, tmp_path):
        store, agent = self._setup(monkeypatch, tmp_path)
        from tiktok_swarm.shop.models import ShopOffer
        from tiktok_swarm.agents.shop_agent import select_weekly_slate

        store.save_offers([ShopOffer(offer_id="p1", title="Persist Test", active=True)])
        slate = select_weekly_slate()

        saved = store.current_slate()
        assert saved is not None
        assert saved.week_of == slate.week_of
