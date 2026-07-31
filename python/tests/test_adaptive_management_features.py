"""Causality, calibration and frozen-definition tests for the volatility feature panel.

Binding design: adaptive-management-design.md section 4 (component table) and section 6
(calibration frozen on the first chronological 20% of TRAIN after warm-up).
"""

from datetime import UTC, datetime, timedelta

import numpy as np
import polars as pl
import pytest

from xen.adaptive_management.features import (
    FORMULA_SOURCES,
    Calibration,
    build_feature_panel,
    fit_calibration,
    tail_risk_state,
)

N_BARS = 900
START = datetime(2022, 1, 1, tzinfo=UTC)
TRAIN_END = START + timedelta(hours=N_BARS - 1)
DECISION_TS = START + timedelta(hours=700)


@pytest.fixture
def h1_bars() -> pl.DataFrame:
    rng = np.random.default_rng(20260730)
    steps = rng.normal(0.0, 0.004, N_BARS)
    close = 100.0 * np.exp(np.cumsum(steps))
    open_ = np.concatenate([[100.0], close[:-1]])
    span = np.abs(rng.normal(0.0, 0.003, N_BARS)) + 1e-4
    high = np.maximum(open_, close) * (1.0 + span)
    low = np.minimum(open_, close) * (1.0 - span)
    ts = [START + timedelta(hours=i) for i in range(N_BARS)]
    return pl.DataFrame(
        {
            "symbol": ["TESTUSDT"] * N_BARS,
            "ts": ts,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
        }
    )


def test_feature_at_t_does_not_change_when_bar_t_outcome_changes(h1_bars):
    calibration = fit_calibration(h1_bars, START, TRAIN_END)
    left = build_feature_panel(h1_bars, calibration)
    changed = h1_bars.with_columns(
        pl.when(pl.col("ts") == DECISION_TS)
        .then(pl.col("open") * 1.8)
        .otherwise(pl.col("open")).alias("open"),
        pl.when(pl.col("ts") == DECISION_TS)
        .then(pl.col("high") * 2.0)
        .otherwise(pl.col("high")).alias("high"),
        pl.when(pl.col("ts") == DECISION_TS)
        .then(pl.col("low") * 0.5)
        .otherwise(pl.col("low")).alias("low"),
        pl.when(pl.col("ts") == DECISION_TS)
        .then(pl.col("close") * 1.7)
        .otherwise(pl.col("close")).alias("close"),
    )
    right = build_feature_panel(changed, calibration)
    cols = [
        "range_scale_bps",
        "swing_scale_bps",
        "level_now",
        "level_forecast_k4",
        "level_forecast_k12",
        "level_forecast_p_k4",
        "level_forecast_p_k12",
        "shock",
        "swing_gt_cur",
        "tail_risk_p",
        "tail_risk",
        "atr20",
    ]
    at = pl.col("ts") == DECISION_TS
    assert left.filter(at).select(cols).equals(right.filter(at).select(cols))


def test_reference_values_use_only_first_twenty_percent_of_train(h1_bars):
    calibration = fit_calibration(h1_bars, START, TRAIN_END)
    assert calibration.train_start_ts == START
    assert calibration.train_end_ts == TRAIN_END
    assert calibration.start_ts == START + timedelta(hours=60)
    assert calibration.end_ts == START + timedelta(hours=228)
    assert calibration.row_count_by_symbol["TESTUSDT"] == 168
    assert calibration.median_range_scale_bps["TESTUSDT"] > 0
    assert calibration.p90_move_bps["TESTUSDT"] > 0
    mutated = h1_bars.with_columns(
        pl.when(pl.col("ts") > calibration.end_ts)
        .then(pl.col("close") * 10)
        .otherwise(pl.col("close")).alias("close")
    )
    assert fit_calibration(mutated, START, TRAIN_END) == calibration


def test_first_open_after_declared_calibration_boundary_cannot_change_references(h1_bars):
    calibration = fit_calibration(h1_bars, START, TRAIN_END)
    first_after = h1_bars.filter(pl.col("ts") > calibration.end_ts)["ts"][0]
    changed = h1_bars.with_columns(
        pl.when(pl.col("ts") == first_after)
        .then(pl.col("open") * 10.0)
        .otherwise(pl.col("open")).alias("open")
    )
    assert fit_calibration(changed, START, TRAIN_END) == calibration


def test_calibration_features_retain_causal_warmup_history(h1_bars):
    baseline = fit_calibration(h1_bars, START, TRAIN_END)
    changed_warmup = h1_bars.with_columns(
        pl.when(pl.col("ts") < baseline.start_ts)
        .then(pl.col("high") * 2.0)
        .otherwise(pl.col("high")).alias("high"),
        pl.when(pl.col("ts") < baseline.start_ts)
        .then(pl.col("low") * 0.5)
        .otherwise(pl.col("low")).alias("low"),
    )
    changed = fit_calibration(changed_warmup, START, TRAIN_END)
    assert (
        changed.median_range_scale_bps["TESTUSDT"]
        != baseline.median_range_scale_bps["TESTUSDT"]
    )


def test_calibration_rejects_rows_outside_explicit_train_fence(h1_bars):
    with pytest.raises(ValueError, match="TRAIN bounds"):
        fit_calibration(h1_bars, START - timedelta(hours=1), TRAIN_END)


def test_all_eight_component_columns_are_present_and_typed(h1_bars):
    panel = build_feature_panel(h1_bars, fit_calibration(h1_bars, START, TRAIN_END))
    for column in (
        "range_scale_bps",
        "swing_scale_bps",
        "level_now",
        "level_forecast_k4",
        "level_forecast_k12",
        "shock",
        "swing_gt_cur",
        "tail_risk",
    ):
        assert column in panel.columns
    states = ("HIGH", "LOW", "UNKNOWN")
    for column in ("level_now", "level_forecast_k4", "shock", "swing_gt_cur", "tail_risk"):
        assert set(panel[column].unique()) <= set(states)


def test_shock_state_is_active_for_two_bars():
    flags = np.array([0, 1, 0, 0, 1, 1, 0], dtype=np.int64)
    from xen.adaptive_management.features import shock_two_bar_life

    assert shock_two_bar_life(flags).tolist() == [0, 1, 1, 0, 1, 1, 1]


def test_tail_risk_is_high_only_above_the_unconditional_rate():
    assert tail_risk_state(0.14) == "HIGH"
    assert tail_risk_state(0.10) == "LOW"
    assert tail_risk_state(float("nan")) == "UNKNOWN"


def test_formula_sources_name_every_component():
    assert set(FORMULA_SOURCES) == {
        "RANGE_SCALE",
        "SWING_SCALE",
        "LEVEL_NOW",
        "LEVEL_FORECAST_K4",
        "LEVEL_FORECAST_K12",
        "SHOCK",
        "SWING_GT_CUR",
        "TAIL_RISK",
        "ATR20",
    }


def test_calibration_is_frozen_and_hashable(h1_bars):
    calibration = fit_calibration(h1_bars, START, TRAIN_END)
    assert isinstance(calibration, Calibration)
    with pytest.raises(Exception):
        calibration.end_ts = START  # frozen dataclass
