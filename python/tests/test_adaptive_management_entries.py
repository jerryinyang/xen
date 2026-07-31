"""Common-origin clock and fixed breakout entry tests, including the design's golden traces.

Golden traces are hand-derived in python/experiments/SPDR-021/design.md section "Golden traces".
"""

from datetime import UTC, datetime, timedelta
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys

import numpy as np
import polars as pl
import pytest

from xen.adaptive_management.contracts import OriginState
from xen.adaptive_management.entries import (
    BREAKOUT_VARIANT,
    breach_episodes,
    breach_origins,
    breakout_episodes,
    breakout_origins,
)


def _bars(rows: list[tuple[str, float, float, float, float]]) -> pl.DataFrame:
    start = datetime(2023, 1, 1, tzinfo=UTC)
    return pl.DataFrame(
        {
            "symbol": ["GOLDUSDT"] * len(rows),
            "ts": [start + timedelta(hours=i) for i in range(len(rows))],
            "open": [r[1] for r in rows],
            "high": [r[2] for r in rows],
            "low": [r[3] for r in rows],
            "close": [r[4] for r in rows],
            "atr20": [2.0] * len(rows),
        }
    )


def golden_long_frame() -> pl.DataFrame:
    """Trace 1 plus the next actionable open after the three completed signal bars."""
    return _bars(
        [
            ("t-2", 98.0, 100.0, 98.0, 99.5),
            ("t-1", 99.0, 100.0, 97.0, 99.0),
            ("t", 99.0, 102.0, 99.0, 101.0),
            ("t+1", 101.0, 101.2, 100.8, 101.0),
        ]
    )


def golden_short_frame() -> pl.DataFrame:
    """Trace 2 plus the next actionable open after the three completed signal bars."""
    return _bars(
        [
            ("t-2", 100.0, 101.0, 99.0, 100.5),
            ("t-1", 100.0, 103.0, 99.0, 100.0),
            ("t", 100.0, 102.0, 97.0, 98.0),
            ("t+1", 98.0, 98.2, 97.8, 98.0),
        ]
    )


def test_origin_clock_is_parameter_free_and_stable():
    origins = breakout_origins(golden_long_frame())
    assert origins.height == 1
    row = origins.row(0, named=True)
    assert row["side"] == 1
    assert row["entry_variant"] == BREAKOUT_VARIANT
    # The origin id must not change when a threshold or expiry changes: it is arm-independent.
    again = breakout_origins(golden_long_frame())
    assert again.row(0, named=True)["origin_id"] == row["origin_id"]


def test_breakout_long_matches_design_golden_trace_one():
    origins = breakout_origins(golden_long_frame())
    direct = breakout_episodes(origins, threshold_atr=0.25, expiry_bars=2)
    fixed = breakout_episodes(origins, threshold_atr=0.50, expiry_bars=2)
    reverse = breakout_episodes(origins, threshold_atr=1.00, expiry_bars=2)
    assert direct.row(0, named=True)["state"] == OriginState.ORDER_CREATED
    assert direct.row(0, named=True)["stop_price"] == 102.0
    assert fixed.row(0, named=True)["state"] == OriginState.ORDER_CREATED
    # Strict '>' : an impulse of exactly 1.0 ATR does not clear a 1.00 threshold.
    assert reverse.row(0, named=True)["state"] == OriginState.NO_EVENT
    assert reverse.row(0, named=True)["stop_price"] is None


def test_breakout_short_matches_design_golden_trace_two():
    origins = breakout_origins(golden_short_frame())
    row = breakout_episodes(origins, threshold_atr=0.50, expiry_bars=2).row(0, named=True)
    assert row["side"] == -1
    assert row["stop_price"] == 97.0
    assert row["state"] == OriginState.ORDER_CREATED


def test_every_origin_survives_in_every_arm():
    frame = pl.concat([golden_long_frame(), golden_short_frame()])
    origins = breakout_origins(frame)
    for threshold in (0.25, 0.50, 1.00, 4.00):
        episodes = breakout_episodes(origins, threshold_atr=threshold, expiry_bars=2)
        assert episodes.height == origins.height
        assert set(episodes["origin_id"]) == set(origins["origin_id"])
        assert set(episodes["state"]) <= {OriginState.ORDER_CREATED, OriginState.NO_EVENT}


def test_expiry_and_threshold_are_recorded_per_episode():
    origins = breakout_origins(golden_long_frame())
    row = breakout_episodes(origins, threshold_atr=0.375, expiry_bars=4).row(0, named=True)
    assert row["threshold_atr"] == 0.375
    assert row["expiry_bars"] == 4
    assert row["episode_id"] != row["origin_id"]


def test_impulse_is_signed_against_the_shape_side():
    origins = breakout_origins(golden_short_frame())
    assert abs(origins.row(0, named=True)["impulse_atr"] - 1.0) < 1e-12


def test_actionable_bar_ohlc_cannot_change_breakout_origin_or_episode_geometry():
    bars = golden_long_frame()
    actionable_ts = bars["ts"][-1]
    changed = bars.with_columns(
        pl.when(pl.col("ts") == actionable_ts)
        .then(pl.col("open") * 4.0)
        .otherwise(pl.col("open")).alias("open"),
        pl.when(pl.col("ts") == actionable_ts)
        .then(pl.col("high") * 5.0)
        .otherwise(pl.col("high")).alias("high"),
        pl.when(pl.col("ts") == actionable_ts)
        .then(pl.col("low") * 0.2)
        .otherwise(pl.col("low")).alias("low"),
        pl.when(pl.col("ts") == actionable_ts)
        .then(pl.col("close") * 3.0)
        .otherwise(pl.col("close")).alias("close"),
    )
    left_origins = breakout_origins(bars)
    right_origins = breakout_origins(changed)
    assert left_origins.equals(right_origins)
    left = breakout_episodes(left_origins, threshold_atr=0.5, expiry_bars=2)
    right = breakout_episodes(right_origins, threshold_atr=0.5, expiry_bars=2)
    assert left.equals(right)
    row = left.row(0, named=True)
    assert row["event_ts"] == bars["ts"][-2]
    assert row["actionable_ts"] == actionable_ts
    assert row["entry_order_type"] == "STOP"


def _breach_fixture() -> tuple[pl.DataFrame, pl.DataFrame]:
    start = datetime(2023, 1, 3, tzinfo=UTC)
    rows = 14
    h1 = pl.DataFrame(
        {
            "symbol": ["GOLDUSDT"] * rows,
            "ts": [start + timedelta(hours=i) for i in range(rows)],
            "open": [
                100.0, 100.0, 101.4, 100.0, 100.0, 98.3, 100.0, 100.0,
                *([100.0] * 6),
            ],
            "high": [
                100.2, 101.6, 101.5, 100.2, 100.1, 98.6, 100.1, 100.1,
                *([100.1] * 6),
            ],
            "low": [
                99.8, 99.9, 100.5, 99.8, 98.7, 98.1, 99.9, 99.9,
                *([99.9] * 6),
            ],
            "close": [
                100.0, 101.2, 101.0, 100.0, 98.4, 98.5, 100.0, 100.0,
                *([100.0] * 6),
            ],
        }
    )
    features = h1.select("symbol", "ts").with_columns(
        pl.lit(100.0).alias("range_scale_bps")
    )
    return h1, features


def test_breach_touch_and_close_are_independent_spdr014_events():
    h1, features = _breach_fixture()
    origins = breach_origins(h1, features)
    touch = breach_episodes(
        origins, "SPDR-022", "E_TOUCH", z=1.5, horizon=4, native_arm_id="FIXED_TOUCH"
    )
    close = breach_episodes(
        origins, "SPDR-022", "E_CLOSE", z=1.5, horizon=12, native_arm_id="FIXED_CLOSE"
    )
    assert touch.row(0, named=True)["event_ts"] == h1["ts"][1]
    assert touch.row(0, named=True)["entry_ts"] == h1["ts"][2]
    assert touch.row(0, named=True)["actionable_ts"] == h1["ts"][2]
    assert touch.row(0, named=True)["entry_order_type"] == "MARKET"
    assert touch.row(0, named=True)["side"] == 1
    assert close.row(0, named=True)["event_ts"] == h1["ts"][4]
    assert touch.row(0, named=True)["entry_variant"] == "E_TOUCH"
    assert close.row(0, named=True)["entry_variant"] == "E_CLOSE"


def test_momo_and_mr_map_against_the_same_breach_side():
    h1, features = _breach_fixture()
    origins = breach_origins(h1, features)
    momo = breach_episodes(
        origins, "SPDR-022", "E_TOUCH", z=1.5, horizon=4, native_arm_id="MOMO"
    )
    mr = breach_episodes(
        origins, "SPDR-023", "E_TOUCH", z=1.5, horizon=4, native_arm_id="MR"
    )
    assert momo.row(0, named=True)["side"] == 1
    assert mr.row(0, named=True)["side"] == -1


def test_episode_identity_names_full_event_identity_without_position_collisions():
    h1, features = _breach_fixture()
    origins = breach_origins(h1, features)
    touch = breach_episodes(
        origins, "SPDR-022", "E_TOUCH", z=1.5, horizon=4, native_arm_id="ARM"
    ).row(0, named=True)
    close = breach_episodes(
        origins, "SPDR-022", "E_CLOSE", z=1.5, horizon=4, native_arm_id="ARM"
    ).row(0, named=True)
    assert touch["episode_id"] != close["episode_id"]
    assert touch["position_id"] != close["position_id"]
    assert len(touch["position_id"]) <= 36


def _breach_case(
    rows: list[tuple[float, float, float, float]],
) -> tuple[pl.DataFrame, pl.DataFrame]:
    start = datetime(2023, 2, 1, tzinfo=UTC)
    h1 = pl.DataFrame(
        {
            "symbol": ["CASEUSDT"] * len(rows),
            "ts": [start + timedelta(hours=i) for i in range(len(rows))],
            "open": [row[0] for row in rows],
            "high": [row[1] for row in rows],
            "low": [row[2] for row in rows],
            "close": [row[3] for row in rows],
        }
    )
    features = h1.select("symbol", "ts").with_columns(
        pl.lit(100.0).alias("range_scale_bps")
    )
    return h1, features


def test_dual_touch_equal_excursion_is_an_undecided_non_trade_event():
    h1, features = _breach_case(
        [
            (100.0, 101.2, 98.8, 100.0),
            (100.0, 100.2, 99.8, 100.0),
            (100.0, 100.2, 99.8, 100.0),
        ]
    )
    row = breach_episodes(
        breach_origins(h1, features),
        "SPDR-022",
        "E_TOUCH",
        z=1.0,
        horizon=2,
        native_arm_id="DUAL",
    ).row(0, named=True)
    assert row["state"] == "EVENT_UNDECIDED"
    assert row["event_ts"] == h1["ts"][0]
    assert row["side"] == 0
    assert row["entry_ts"] is None
    assert row["entry_order_type"] == "NONE"


def test_short_tail_window_is_incomplete_not_no_event():
    h1, features = _breach_case(
        [
            (100.0, 100.2, 99.8, 100.0),
            (100.0, 100.2, 99.8, 100.0),
        ]
    )
    row = breach_episodes(
        breach_origins(h1, features),
        "SPDR-022",
        "E_CLOSE",
        z=1.0,
        horizon=3,
        native_arm_id="INCOMPLETE",
    ).row(0, named=True)
    assert row["state"] == "INCOMPLETE"
    assert row["entry_ts"] is None
    assert row["entry_order_type"] == "NONE"


def test_decided_event_without_a_real_next_open_is_censored():
    h1, features = _breach_case(
        [
            (100.0, 100.2, 99.8, 100.0),
            (100.0, 101.2, 99.8, 101.1),
        ]
    )
    row = breach_episodes(
        breach_origins(h1, features),
        "SPDR-022",
        "E_CLOSE",
        z=1.0,
        horizon=2,
        native_arm_id="CENSORED",
    ).row(0, named=True)
    assert row["state"] == "CENSORED"
    assert row["event_ts"] == h1["ts"][1]
    assert row["entry_ts"] is None
    assert row["entry_order_type"] == "NONE"


def test_complete_inside_window_is_the_only_no_event_case():
    h1, features = _breach_case(
        [
            (100.0, 100.2, 99.8, 100.0),
            (100.0, 100.2, 99.8, 100.0),
            (100.0, 100.2, 99.8, 100.0),
        ]
    )
    row = breach_episodes(
        breach_origins(h1, features),
        "SPDR-022",
        "E_TOUCH",
        z=1.0,
        horizon=3,
        native_arm_id="NO_EVENT",
    ).row(0, named=True)
    assert row["state"] == "NO_EVENT"
    assert row["actionable_ts"] == h1["ts"][2]
    assert row["entry_order_type"] == "NONE"


def _load_parent_event_detector():
    directory = (
        Path(__file__).resolve().parents[1]
        / "experiments"
        / "SPDR-014"
        / "screen_code"
    )
    source = directory / "engine.py"
    if not source.exists():
        raise FileNotFoundError(f"required frozen SPDR-014 event source missing: {source}")
    saved_modules = dict(sys.modules)
    sys.path.insert(0, str(directory))
    for name in ("config", "costs"):
        sys.modules.pop(name, None)
    try:
        spec = importlib.util.spec_from_file_location("parent_spdr014_event_engine", source)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module.detect_event
    finally:
        sys.path.remove(str(directory))
        for name in set(sys.modules) - set(saved_modules):
            del sys.modules[name]
        sys.modules.update(saved_modules)


@pytest.mark.parametrize(
    ("event", "rows", "horizon", "expected_index", "expected_side", "expected_state"),
    [
        (
            "E_TOUCH",
            [
                (100.0, 100.2, 99.8, 100.0),
                (100.0, 101.2, 99.8, 100.0),
                (101.0, 101.1, 100.9, 101.0),
                (101.0, 101.1, 100.9, 101.0),
            ],
            3,
            1,
            1,
            "ORDER_CREATED",
        ),
        (
            "E_CLOSE",
            [
                (100.0, 100.2, 99.8, 100.0),
                (100.0, 101.2, 99.8, 101.1),
                (101.0, 101.1, 100.9, 101.0),
                (101.0, 101.1, 100.9, 101.0),
            ],
            3,
            1,
            1,
            "ORDER_CREATED",
        ),
        (
            "E_TOUCH",
            [
                (100.0, 101.2, 98.8, 100.0),
                (100.0, 100.2, 99.8, 100.0),
                (100.0, 100.2, 99.8, 100.0),
                (100.0, 100.2, 99.8, 100.0),
            ],
            3,
            0,
            0,
            "EVENT_UNDECIDED",
        ),
        (
            "E_TOUCH",
            [
                (100.0, 101.2000000005, 98.8, 100.0),
                (100.0, 100.2, 99.8, 100.0),
                (100.0, 100.2, 99.8, 100.0),
                (100.0, 100.2, 99.8, 100.0),
            ],
            3,
            0,
            1,
            "ORDER_CREATED",
        ),
        (
            "E_TOUCH",
            [
                (100.0, 100.2, 99.8, 100.0),
                (100.0, 100.2, 99.8, 100.0),
                (100.0, 100.2, 99.8, 100.0),
                (100.0, 100.2, 99.8, 100.0),
            ],
            3,
            -1,
            0,
            "NO_EVENT",
        ),
        (
            "E_CLOSE",
            [
                (100.0, 100.2, 99.8, 100.0),
                (100.0, 100.2, 99.8, 100.0),
            ],
            3,
            None,
            0,
            "INCOMPLETE",
        ),
    ],
)
def test_breach_events_match_frozen_spdr014_detector(
    event, rows, horizon, expected_index, expected_side, expected_state
):
    parent_detect = _load_parent_event_detector()
    h1, features = _breach_case(rows)
    parent = parent_detect(
        SimpleNamespace(
            open=np.array([row[0] for row in rows]),
            high=np.array([row[1] for row in rows]),
            low=np.array([row[2] for row in rows]),
            close=np.array([row[3] for row in rows]),
        ),
        -1,
        horizon,
        101.0,
        99.0,
        event.replace("_", "-"),
        100.0,
    )
    actual = breach_episodes(
        breach_origins(h1, features),
        "SPDR-022",
        event,
        z=1.0,
        horizon=horizon,
        native_arm_id="PARENT_PARITY",
    ).row(0, named=True)
    assert actual["state"] == expected_state
    assert actual["side"] == expected_side
    assert (None if parent is None else parent["event_idx"]) == expected_index
    if parent is not None:
        assert parent["side"] == expected_side
    expected_ts = None if expected_index in (None, -1) else h1["ts"][expected_index]
    assert actual["event_ts"] == expected_ts
