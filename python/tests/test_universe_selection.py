"""INFR-014 WP0 — universe_selection causality, determinism, tie-break, HOLDOUT refuse."""
from __future__ import annotations

from datetime import datetime, timezone

import polars as pl
import pytest

from xen.nautilus.catalog_fence import FenceManifest, FenceViolation
from xen.nautilus.universe_selection import (
    SelectionRule,
    build_membership_series,
    rank_from_volume_panel,
    rebalance_schedule,
    rule_hash,
    select_membership,
)

NS = 1_000_000_000


def _fence() -> FenceManifest:
    return FenceManifest(
        analysis_start_utc=datetime(2020, 1, 1, tzinfo=timezone.utc),
        train_end_utc=datetime(2024, 6, 1, tzinfo=timezone.utc),
        holdout_start_utc=datetime(2025, 1, 1, tzinfo=timezone.utc),
        data_end_utc=datetime(2025, 6, 1, tzinfo=timezone.utc),
        path=__file__,  # unused for unit tests
        sha256="test",
        raw={},
    )


def _panel_day(asof: datetime, *, inject_future: bool = False) -> pl.DataFrame:
    """Synthetic 1m volume panel for 3 instruments around asof."""
    asof_ns = int(asof.timestamp() * 1e9)
    rows = []
    # 1500 bars of history ending just before asof
    for iid, base_vol in [
        ("AAA-LINEAR.BYBIT", 100.0),
        ("BBB-LINEAR.BYBIT", 90.0),
        ("CCC-LINEAR.BYBIT", 80.0),
        ("DDD-LINEAR.BYBIT", 70.0),
    ]:
        for i in range(1500):
            ts = asof_ns - (1500 - i) * 60 * NS
            rows.append({"instrument_id": iid, "ts_event": ts, "volume": base_vol})
    if inject_future:
        # massive future volume on CCC that must NOT affect rank at asof
        for i in range(100):
            ts = asof_ns + (i + 1) * 60 * NS
            rows.append({
                "instrument_id": "CCC-LINEAR.BYBIT",
                "ts_event": ts,
                "volume": 1e12,
            })
    return pl.DataFrame(rows)


def test_rule_hash_stable_under_key_reorder():
    r = SelectionRule(n=10, window_bars=1440)
    h1 = rule_hash(r)
    h2 = rule_hash(SelectionRule(window_bars=1440, n=10))
    assert h1 == h2
    assert len(h1) == 64


def test_causality_future_volume_cannot_enter_rank():
    asof = datetime(2023, 6, 15, 12, 0, tzinfo=timezone.utc)
    rule = SelectionRule(n=3)
    clean = rank_from_volume_panel(_panel_day(asof, inject_future=False), rule, asof_ts=asof)
    dirty = rank_from_volume_panel(_panel_day(asof, inject_future=True), rule, asof_ts=asof)
    assert clean.get_column("instrument_id").to_list() == dirty.get_column(
        "instrument_id"
    ).to_list()
    # CCC must not leapfrog AAA/BBB via future volume
    assert dirty.get_column("instrument_id").to_list()[0] == "AAA-LINEAR.BYBIT"
    assert "CCC-LINEAR.BYBIT" != dirty.get_column("instrument_id").to_list()[0]


def test_determinism_byte_identical():
    asof = datetime(2023, 6, 15, 12, 0, tzinfo=timezone.utc)
    rule = SelectionRule(n=3)
    panel = _panel_day(asof)
    a = rank_from_volume_panel(panel, rule, asof_ts=asof)
    b = rank_from_volume_panel(panel, rule, asof_ts=asof)
    assert a.equals(b)


def test_tie_break_lexicographic_id():
    asof = datetime(2023, 6, 15, 12, 0, tzinfo=timezone.utc)
    asof_ns = int(asof.timestamp() * 1e9)
    # equal volume for ZZZ and AAA — AAA must rank first (lexicographic)
    rows = []
    for iid in ("ZZZ-LINEAR.BYBIT", "AAA-LINEAR.BYBIT", "MMM-LINEAR.BYBIT"):
        for i in range(100):
            rows.append({
                "instrument_id": iid,
                "ts_event": asof_ns - (100 - i) * 60 * NS,
                "volume": 50.0,
            })
    panel = pl.DataFrame(rows)
    out = rank_from_volume_panel(panel, SelectionRule(n=3), asof_ts=asof)
    ids = out.get_column("instrument_id").to_list()
    assert ids == sorted(ids)  # equal metric → lexicographic


def test_holdout_refusal():
    fence = _fence()
    asof = datetime(2025, 3, 1, tzinfo=timezone.utc)  # inside holdout calendar
    with pytest.raises(FenceViolation):
        select_membership(
            catalog=None,
            rule=SelectionRule(n=2),
            asof_ts=asof,
            fence=fence,
            band="HOLDOUT",
            volume_panel=_panel_day(datetime(2023, 6, 15, tzinfo=timezone.utc)),
        )
    # asof outside TRAIN also refuses
    with pytest.raises(FenceViolation):
        select_membership(
            catalog=None,
            rule=SelectionRule(n=2),
            asof_ts=asof,
            fence=fence,
            band="TRAIN",
            volume_panel=_panel_day(asof),
        )


def test_rebalance_schedule_daily_utc():
    rule = SelectionRule(rebalance="1d", rebalance_time="00:00")
    start = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)
    end = datetime(2023, 1, 4, 0, 0, tzinfo=timezone.utc)
    sched = rebalance_schedule(start, end, rule)
    assert len(sched) == 3  # Jan 2,3,4 00:00 (Jan1 00:00 before start)
    assert all(s.hour == 0 and s.minute == 0 for s in sched)


def test_build_membership_series_carries_rule_hash():
    fence = _fence()
    asof0 = datetime(2023, 1, 2, 0, 0, tzinfo=timezone.utc)
    rule = SelectionRule(n=2)
    panel = _panel_day(asof0)
    # extend panel across a few days
    parts = [panel]
    for d in range(1, 4):
        parts.append(_panel_day(datetime(2023, 1, 2 + d, 0, 0, tzinfo=timezone.utc)))
    big = pl.concat(parts)
    series = build_membership_series(
        None,
        rule,
        start=datetime(2023, 1, 2, tzinfo=timezone.utc),
        end=datetime(2023, 1, 4, tzinfo=timezone.utc),
        fence=fence,
        volume_panel=big,
    )
    assert series.height > 0
    assert set(series.get_column("rule_hash").unique().to_list()) == {rule_hash(rule)}
