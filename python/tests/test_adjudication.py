"""Contract tests for xen.adjudication (INFR-001 WS-1).

The multi-leg fixture reproduces the critical-017 (C-1) failure shape: overlapping legs whose
per-leg profits a +/-1 fill-substitution series would double-count while marking risk once.
The reconciliation invariant must hold for the canonical series and must FAIL for the legacy
substitution construction on the same fixture.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from xen.adjudication import (
    assemble_multileg_bps,
    build_episodes,
    per_leg_net,
    reconcile,
)

T0 = datetime(2021, 1, 4, 0, 0)


def _bars(opens: list[float]) -> pl.DataFrame:
    times = [T0 + timedelta(hours=4 * i) for i in range(len(opens))]
    return pl.DataFrame({"SourceCloseTime": times, "RealOpen": opens})


def _leg(entry_bar: int, exit_bar: int, direction: int, entry_px: float, exit_px: float,
         censored: bool = False) -> dict:
    # fill timestamps strictly inside the bar (bar i spans (close[i-1], close[i]])
    return {
        "EntryTime": T0 + timedelta(hours=4 * entry_bar - 1),
        "ExitTime": T0 + timedelta(hours=4 * exit_bar - 1),
        "Direction": direction,
        "EntryFillPrice": entry_px,
        "ExitFillPrice": exit_px,
        "RealizedBps": direction * (exit_px - entry_px) / entry_px * 1e4,
        "Censored": censored,
    }


def test_single_leg_telescopes_to_realized() -> None:
    bars = _bars([100.0, 101.0, 102.0, 103.0, 104.0, 105.0])
    legs = pl.DataFrame([_leg(1, 3, +1, 100.5, 102.5)])
    s = assemble_multileg_bps(bars, legs, cost_bps=2.0)
    assert s.gross_bps.sum() == pytest.approx(legs["RealizedBps"][0], abs=1e-9)
    assert s.net_bps.sum() == pytest.approx(legs["RealizedBps"][0] - 2.0, abs=1e-9)
    assert list(s.open_legs) == [0, 1, 1, 1, 0, 0]
    assert reconcile(s, legs).ok


def test_multileg_overlap_reconciles_and_legacy_substitution_fails() -> None:
    # Three overlapping long legs on a V-shaped path — the C-1 shape: each leg books its
    # own favorable exit differential while a 1-unit path carries the adverse move once.
    bars = _bars([100.0, 98.0, 96.0, 97.0, 99.0, 101.0, 101.0])
    legs = pl.DataFrame([
        _leg(1, 4, +1, 99.0, 98.5),
        _leg(2, 5, +1, 97.0, 100.0),
        _leg(3, 5, +1, 96.5, 100.5),
    ])
    s = assemble_multileg_bps(bars, legs, cost_bps=1.0)
    rep = reconcile(s, legs)
    assert rep.ok, rep
    assert s.gross_bps.sum() == pytest.approx(float(legs["RealizedBps"].sum()), abs=1e-9)
    assert s.open_legs.max() == 3
    assert s.net_bps.sum() == pytest.approx(float(legs["RealizedBps"].sum()) - 3.0, abs=1e-9)

    # Legacy construction (EXP-014c lib lineage): +/-1 position path, every leg's fills
    # substituted into the single-unit bar series. Must violate the invariant here.
    opens = bars["RealOpen"].to_numpy()
    pos = np.array([0, 1, 1, 1, 1, 1, 0], dtype=float)
    entry_fill = np.array([np.nan, 99.0, 97.0, 96.5, np.nan, np.nan, np.nan])
    exit_fill = np.array([np.nan, np.nan, np.nan, np.nan, 98.5, 100.0, np.nan])
    next_open = opens[1:]
    p, ef, xf = pos[:-1], entry_fill[:-1], exit_fill[:-1]
    open_price = np.where(~np.isnan(ef), ef, opens[:-1])
    close_price = np.where(~np.isnan(xf), xf, next_open)
    legacy = np.where(p != 0.0, p * np.log(close_price / open_price) * 1e4, 0.0)
    assert abs(float(np.nansum(legacy)) - float(legs["RealizedBps"].sum())) > 50.0


def test_censored_leg_excluded_from_realized_series() -> None:
    bars = _bars([100.0, 101.0, 102.0, 103.0])
    legs = pl.DataFrame([
        _leg(1, 2, +1, 100.5, 101.5),
        _leg(2, 3, +1, 101.5, 0.0, censored=True),  # exit fill meaningless when censored
    ])
    s = assemble_multileg_bps(bars, legs, cost_bps=1.0)
    assert s.n_censored == 1
    assert s.gross_bps.sum() == pytest.approx(legs["RealizedBps"][0], abs=1e-9)
    assert reconcile(s, legs).ok
    expected_mtm = (103.0 - 101.5) / 101.5 * 1e4
    assert s.censored_mtm_bps == pytest.approx(expected_mtm, abs=1e-9)
    assert list(s.open_legs) == [0, 1, 2, 1]


def test_episodes_split_and_aggregate_leg_net() -> None:
    bars = _bars([100.0, 101.0, 102.0, 100.0, 100.0, 99.0, 98.0, 100.0, 101.0])
    legs = pl.DataFrame([
        _leg(1, 2, +1, 100.5, 101.5),
        _leg(2, 3, +1, 101.5, 100.5),   # episode 1: bars 1-3
        _leg(5, 7, -1, 99.5, 99.9),     # episode 2: bars 5-7
    ])
    eps = build_episodes(bars, legs, cost_bps=1.0)
    assert eps.height == 2
    nets = per_leg_net(legs, cost_bps=1.0)["NetBps"].to_list()
    assert eps["net_bps"][0] == pytest.approx(nets[0] + nets[1], abs=1e-9)
    assert eps["net_bps"][1] == pytest.approx(nets[2], abs=1e-9)
    assert eps["n_legs"].to_list() == [2, 1]
    assert eps["max_open_legs"][0] == 2
    assert not eps["censored"].any()


_US2000 = (Path(__file__).resolve().parents[2] / "data" / "strategy_runs" /
           "EXP-014c-4h-s8-e3-extend-z15" /
           "cross_instrument_spread_mr_us2000_4h_20260703_055334")


@pytest.mark.skipif(not _US2000.exists(), reason="US2000 emission not present")
def test_real_emission_reconciles_us2000_extend() -> None:
    # critical-017 ground truth: per-leg total +12,547 bps over 1,317 legs; the defective
    # legacy series reported +48,141 (3.8x). The canonical series must reconcile exactly.
    pos = pl.read_parquet(_US2000 / "positions.parquet")
    cis = pl.read_parquet(_US2000 / "cis_trades.parquet")
    s = assemble_multileg_bps(pos, cis, cost_bps=8.0)
    rep = reconcile(s, cis)
    assert rep.ok, rep
    assert rep.per_leg_realized_total == pytest.approx(12547.0, abs=1.0)
    # recomputed exposure must track the engine's own OpenLegs column; engine reports
    # end-of-bar state while span attribution counts the entry/exit bar itself as open,
    # so a one-bar boundary disagreement per leg is expected (1,317 legs / 5,886 bars)
    engine_open = pos.sort("SourceCloseTime")["OpenLegs"].to_numpy()
    match = float(np.mean((engine_open > 0) == (s.open_legs > 0)))
    assert match > 0.97
