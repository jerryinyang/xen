"""Regression tests for INFR-020 shared level provenance and availability."""

from __future__ import annotations

import datetime as dt

import polars as pl
import pytest

from xen.sigbar.ltf import (
    assign_candidate_sessions,
    available_levels_for_candidates,
    session_ib_from_1m,
    structural_levels_1m,
)


def _anchors() -> pl.DataFrame:
    previous = dt.datetime(2022, 1, 1, 13, 30)
    current = dt.datetime(2022, 1, 2, 13, 30)
    following = dt.datetime(2022, 1, 3, 13, 30)
    return pl.DataFrame(
        {
            "anchor_ts": [previous, current],
            "session_end": [current, following],
        }
    )


def _straddling_bars() -> pl.DataFrame:
    start = dt.datetime(2022, 1, 2, 12, 0)
    rows = []
    for i in range(120):
        ts = start + dt.timedelta(minutes=i)
        high = 101.0
        low = 99.0
        if ts == dt.datetime(2022, 1, 2, 13, 4):
            high = 105.0
        if ts == dt.datetime(2022, 1, 2, 12, 30):
            low = 95.0
        rows.append(
            {
                "OpenTime": ts,
                "Open": 100.0,
                "High": high,
                "Low": low,
                "Close": 100.0,
                "Volume": 10.0,
                "BuyVolume": 6.0,
                "SellVolume": 4.0,
                "NTrades": 1,
            }
        )
    return pl.DataFrame(rows)


def test_prior_levels_stamp_source_times_and_exclude_straddling_bar_sources():
    bars = _straddling_bars()
    anchors = _anchors()
    candidate = pl.DataFrame(
        {
            "OpenTime": [dt.datetime(2022, 1, 2, 13, 0)],
            "Close": [100.0],
        }
    )
    cand_sessions = assign_candidate_sessions(candidate, anchors, ltf_minutes=60)
    levels = structural_levels_1m(
        bars,
        anchors,
        60,
        only_anchors={dt.datetime(2022, 1, 2, 13, 30)},
        include_profile=True,
    )

    assert levels.height == 7
    assert levels["formed_ts"].null_count() == 0
    pairs = available_levels_for_candidates(cand_sessions, levels)
    prior_high = pairs.filter(pl.col("level_kind") == "PRIOR_SESSION_HIGH")
    prior_low = pairs.filter(pl.col("level_kind") == "PRIOR_SESSION_LOW")
    profiles = pairs.filter(
        pl.col("level_kind").is_in(["PRIOR_POC", "PRIOR_VAH", "PRIOR_VAL"])
    )

    assert prior_high["formed_ts"].item() == dt.datetime(2022, 1, 2, 13, 4)
    assert prior_high["excluded_self_made"].item()
    assert prior_low["formed_ts"].item() == dt.datetime(2022, 1, 2, 12, 30)
    assert prior_low["level_available"].item()
    assert profiles["formed_ts"].unique().to_list() == [
        dt.datetime(2022, 1, 2, 13, 29)
    ]
    assert profiles["excluded_self_made"].all()


def test_level_availability_fails_closed_without_formation_provenance():
    candidate = pl.DataFrame(
        {
            "OpenTime": [dt.datetime(2022, 1, 2, 13, 0)],
            "Close": [100.0],
            "anchor_ts": [dt.datetime(2022, 1, 2, 13, 30)],
            "mins_since_close": [30],
        }
    )
    levels = pl.DataFrame(
        {
            "anchor_ts": [dt.datetime(2022, 1, 2, 13, 30)],
            "level_price": [100.0],
            "level_kind": ["PRIOR_POC"],
            "available_mins_since": [0],
        }
    )
    with pytest.raises(RuntimeError, match="formed_ts"):
        available_levels_for_candidates(candidate, levels)


def test_ib_edge_formation_uses_first_timestamp_when_extreme_ties():
    anchor = dt.datetime(2022, 1, 2, 13, 30)
    anchors = pl.DataFrame(
        {
            "anchor_ts": [anchor],
            "session_end": [anchor + dt.timedelta(days=1)],
        }
    )
    bars = pl.DataFrame(
        {
            "OpenTime": [anchor + dt.timedelta(minutes=i) for i in range(3)],
            "High": [105.0, 104.0, 105.0],
            "Low": [95.0, 96.0, 95.0],
        }
    )
    ib = session_ib_from_1m(bars, anchors, 3)
    assert ib["ib_high_ts"].item() == anchor
    assert ib["ib_low_ts"].item() == anchor
