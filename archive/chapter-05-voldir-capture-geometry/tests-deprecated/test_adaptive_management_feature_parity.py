"""Parity of the ported causal formulas against their parent screen implementations.

The adaptive-management package re-implements (never imports) SPDR-012/013/015 formulas. This
test loads the parent modules directly and asserts tolerance equality on a shared fixture, so a
silent formula drift fails here rather than in a run.
"""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from xen.adaptive_management import features as amf

SCREENS = Path(__file__).resolve().parents[1] / "experiments"
TOL = 1e-10


def _load(experiment: str, module: str):
    """Import a parent screen module with its own directory on sys.path."""
    directory = SCREENS / experiment / "screen_code"
    if not (directory / f"{module}.py").exists():
        raise FileNotFoundError(f"required parent module missing: {experiment}/{module}")
    # Parent screens share bare module names (config, indicators, ...). Load them in an isolated
    # sys.modules/sys.path window so no other test module inherits this experiment's `config`.
    saved_modules = dict(sys.modules)
    sys.path.insert(0, str(directory))
    sys.modules.pop("config", None)
    try:
        spec = importlib.util.spec_from_file_location(
            f"parent_{experiment}_{module}", directory / f"{module}.py"
        )
        loaded = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = loaded  # dataclasses resolve __module__ during exec
        spec.loader.exec_module(loaded)
        return loaded
    finally:
        sys.path.remove(str(directory))
        for name in set(sys.modules) - set(saved_modules):
            if not name.startswith("parent_"):
                del sys.modules[name]
        sys.modules.update(saved_modules)


@pytest.fixture(scope="module")
def ohlc() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(20260730)
    close = 100.0 * np.exp(np.cumsum(rng.normal(0.0, 0.004, 600)))
    span = np.abs(rng.normal(0.0, 0.003, 600)) + 1e-4
    high = close * (1.0 + span)
    low = close * (1.0 - span)
    return high, low, close


def test_parkinson_ewma_matches_spdr015(ohlc):
    high, low, _ = ohlc
    parent = _load("SPDR-015", "features")
    expected = parent._parkinson_ewma(high, low, amf.EWMA_LAMBDA)
    actual = amf._parkinson_ewma(high, low)
    assert np.allclose(actual, expected, atol=TOL, equal_nan=True)


def test_wilder_atr_matches_spdr013(ohlc):
    high, low, close = ohlc
    parent = _load("SPDR-013", "indicators")
    for period in (14, 20):
        expected = parent.wilder_atr(high, low, close, period)
        actual = amf.wilder_atr(high, low, close, period)
        assert np.allclose(actual, expected, atol=TOL, equal_nan=True)


def test_atr_zigzag_pivots_match_spdr013(ohlc):
    high, low, close = ohlc
    parent = _load("SPDR-013", "indicators")
    atr = amf.wilder_atr(high, low, close, amf.ATR_PERIOD_SWING)
    start = int(np.argmax(np.isfinite(atr)))
    expected = parent.atr_zigzag(close, atr, start, amf.ZZ_REVERSAL_ATR)
    actual = amf._atr_zigzag(close, atr, start)
    assert len(actual) == len(expected)
    for got, want in zip(actual, expected, strict=True):
        assert (got.start_idx, got.end_idx, got.confirm_idx) == (
            want.start_idx,
            want.end_idx,
            want.confirm_idx,
        )
        assert abs(got.magnitude_bps - want.magnitude_bps) < TOL
        assert abs(got.angle_bps_per_bar - want.angle_bps_per_bar) < TOL
        assert np.isclose(got.path_noise_atr, want.path_noise_atr, atol=TOL, equal_nan=True)


def test_expanding_p90_matches_spdr015(ohlc):
    _, _, close = ohlc
    r = np.concatenate([[np.nan], np.diff(np.log(close))])
    parent = _load("SPDR-015", "features")
    expected = parent._expanding_p90(np.abs(r))
    actual = amf._expanding_p90(np.abs(r))
    assert np.allclose(actual, expected, atol=TOL, equal_nan=True)


def test_logistic_ridge_fit_matches_spdr015():
    rng = np.random.default_rng(7)
    X = rng.normal(size=(200, 4))
    y = (X[:, 0] + 0.5 * X[:, 1] + rng.normal(scale=0.3, size=200) > 0).astype(np.int64)
    parent = _load("SPDR-015", "transitions")
    expected = parent._logistic_ridge_fit(X, y, amf.LOGIT_RIDGE_ALPHA)
    actual = amf._logistic_ridge_fit(X, y)
    assert np.allclose(actual, expected, atol=1e-8)


def test_frozen_parent_feature_rows_match_at_exact_timestamp_and_tolerance():
    path = (
        Path(__file__).parent
        / "fixtures"
        / "adaptive_management"
        / "parent_feature_rows.parquet"
    )
    if not path.exists():
        pytest.fail(f"required frozen parent parity fixture missing: {path}")
    fixture = pl.read_parquet(path)
    bars = fixture.select("symbol", "ts", "open", "high", "low", "close")
    calibration = amf.fit_calibration(bars, bars["ts"].min(), bars["ts"].max())
    expected = fixture.filter(pl.col("parity_row"))
    actual = amf.build_feature_panel(bars, calibration).filter(
        pl.col("ts").is_in(expected["ts"].to_list())
    )
    assert actual["ts"].to_list() == expected["ts"].to_list()
    for column in (
        "level_now", "level_forecast_k4", "level_forecast_k12",
        "shock", "swing_gt_cur", "tail_risk",
    ):
        assert actual[column].to_list() == expected[f"expected_{column}"].to_list()
    for column in (
        "range_scale_bps", "swing_scale_bps", "level_forecast_p_k4",
        "level_forecast_p_k12", "tail_risk_p", "atr20",
    ):
        assert np.allclose(
            actual[column].to_numpy(),
            expected[f"expected_{column}"].to_numpy(),
            atol=TOL,
            rtol=0.0,
            equal_nan=True,
        )
