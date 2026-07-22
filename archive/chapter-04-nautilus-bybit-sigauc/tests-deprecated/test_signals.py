"""Tests for the cTrader strategy-host ingestion harness (INFR-001, design.md v2).

Python does not generate strategy signals; these tests exercise the *ingestion*
side: reading emitted positions (with real OHLC), building next-step real returns
from the emitted prices, and routing them through the frozen referee suite.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import polars as pl
import pytest

from xen.signals import (
    assert_before_analysis_end,
    assert_run_within_holdout,
    returns_and_positions,
    screen_emitted_positions,
)

DOMAIN = "5m"
INSTRUMENT = "EURUSD"


def emitted_positions(closes: list[float], positions: list[int]) -> pl.DataFrame:
    """Build a synthetic strategy-host positions frame with real OHLC."""
    start = datetime(2026, 1, 1, 0, 0)
    rows = []
    for index, (close, position) in enumerate(zip(closes, positions, strict=True)):
        rows.append(
            {
                "SourceCloseTime": start + timedelta(minutes=5 * (index + 1)),
                "Domain": DOMAIN,
                "Strategy": "ma_20_50",
                "Position": int(position),
                "SignalValue": 0.0,
                "RealOpen": close,
                "RealHigh": close + 0.5,
                "RealLow": close - 0.5,
                "RealClose": close,
                "Warmup": False,
                "IsFlat": position == 0,
            }
        )
    return pl.DataFrame(rows)


def random_walk(n: int, *, seed: int = 7) -> list[float]:
    rng = np.random.default_rng(seed)
    steps = rng.normal(0.0, 0.5, size=n)
    return (100.0 + np.cumsum(steps)).tolist()


def oracle_positions(closes: list[float]) -> list[int]:
    """Position[t] = sign of the next-step return; last bar flat (no forward return)."""
    positions = []
    for index in range(len(closes)):
        if index == len(closes) - 1:
            positions.append(0)
        else:
            positions.append(1 if closes[index + 1] > closes[index] else -1)
    return positions


def test_returns_and_positions_drops_last_bar() -> None:
    closes = random_walk(50)
    frame = emitted_positions(closes, oracle_positions(closes))

    returns, positions, aligned = returns_and_positions(frame)

    assert len(returns) == len(closes) - 1
    assert len(positions) == len(returns)
    assert aligned.height == len(returns)


def test_screen_emits_both_referees_deterministically() -> None:
    closes = random_walk(400)
    frame = emitted_positions(closes, oracle_positions(closes))

    rows_a = screen_emitted_positions(
        frame, instrument=INSTRUMENT, domain=DOMAIN, seed=11, n_bootstrap=200
    )
    rows_b = screen_emitted_positions(
        frame, instrument=INSTRUMENT, domain=DOMAIN, seed=11, n_bootstrap=200
    )

    referees = {row["referee"] for row in rows_a}
    assert "gate_stack" in referees
    assert len(rows_a) == 2  # one minimal-baseline + one gate-stack row at alpha0
    # Same seed reproduces the verdicts and effect sizes exactly.
    assert [r["verdict"] for r in rows_a] == [r["verdict"] for r in rows_b]
    assert [r["effect_bps"] for r in rows_a] == [r["effect_bps"] for r in rows_b]


def test_oracle_positions_have_positive_gross_effect() -> None:
    closes = random_walk(400)
    frame = emitted_positions(closes, oracle_positions(closes))

    rows = screen_emitted_positions(
        frame, instrument=INSTRUMENT, domain=DOMAIN, seed=3, n_bootstrap=200
    )
    minimal = next(r for r in rows if r["referee"] != "gate_stack")
    # An oracle that follows the next-step return sign must earn a positive gross edge.
    assert minimal["effect_bps"] > 0.0


def test_flat_positions_are_rejected() -> None:
    closes = random_walk(400)
    frame = emitted_positions(closes, [0] * len(closes))

    rows = screen_emitted_positions(
        frame, instrument=INSTRUMENT, domain=DOMAIN, seed=5, n_bootstrap=200
    )
    assert all(row["verdict"] == "REJECT" for row in rows)


def test_missing_real_close_raises() -> None:
    frame = emitted_positions(random_walk(10), oracle_positions(random_walk(10))).drop("RealClose")
    with pytest.raises(ValueError, match="missing required columns"):
        returns_and_positions(frame)


def test_holdout_assert_fails_closed() -> None:
    cutoff = datetime(2026, 1, 1, 0, 30)
    assert_before_analysis_end(datetime(2026, 1, 1, 0, 25), cutoff)  # before: ok
    with pytest.raises(ValueError, match="reaches or passes AnalysisEndUtc"):
        assert_before_analysis_end(cutoff, cutoff)  # at cutoff: fail closed


def test_assert_run_within_holdout() -> None:
    closes = random_walk(20)
    frame = emitted_positions(closes, oracle_positions(closes))
    max_time = frame.get_column("SourceCloseTime").max()

    assert_run_within_holdout(frame, max_time + timedelta(microseconds=1))  # ok
    with pytest.raises(ValueError, match="reaches or passes AnalysisEndUtc"):
        assert_run_within_holdout(frame, max_time)  # cutoff at last row: fail closed
