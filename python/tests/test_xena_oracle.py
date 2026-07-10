"""Tests for xen.xena.oracle (INFR-006 WS-2).

Covers the oracle's binding contracts: determinism (bit-identical), reconciliation
(equity delta == ledger net; per-trade telescoping), the global risk cap with
rejected-signal logging, non-additivity through the admission channel, segment
filtering, and censored-position marking.
"""
from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from xen.xena.oracle import CandidateStream, OracleConfig, OracleResult, evaluate

NS = 1_000_000_000  # 1s in ns; times are plain int64 "ns"


def make_marks(n: int, start: int = 0, step: int = 60, price0: float = 100.0,
               drift: float = 0.0) -> pl.DataFrame:
    t = np.arange(n, dtype=np.int64) * step * NS + start * NS
    opens = price0 + drift * np.arange(n)
    return pl.DataFrame({"CloseTime": t, "Open": opens})


def make_stream(cid: str, trades: list[dict], marks: pl.DataFrame, *,
                cost_bps: float = 0.0) -> CandidateStream:
    df = pl.DataFrame(trades, schema={"EntryTime": pl.Int64, "ExitTime": pl.Int64,
                                      "Direction": pl.Float64, "EntryPrice": pl.Float64,
                                      "ExitPrice": pl.Float64, "StopDistance": pl.Float64,
                                      "Censored": pl.Boolean})
    return CandidateStream(cid, "TEST", df, marks, cost_bps)


def trade(entry_s: int, exit_s: int, direction: float, ep: float, xp: float,
          stop: float = 1.0, censored: bool = False) -> dict:
    return {"EntryTime": entry_s * NS, "ExitTime": exit_s * NS, "Direction": direction,
            "EntryPrice": ep, "ExitPrice": xp, "StopDistance": stop, "Censored": censored}


CFG = OracleConfig(initial_equity=100_000.0, risk_per_position=0.005, r_max=0.05)


# --------------------------------------------------------------------------- #
# Reconciliation & basic accounting
# --------------------------------------------------------------------------- #
def test_single_trade_pnl_telescopes_to_fills():
    marks = make_marks(100, price0=100.0, drift=0.1)
    s = make_stream("a", [trade(120, 600, 1.0, 100.0, 101.5)], marks)
    res = evaluate({"a"}, [s], CFG)
    assert res.n_admitted == 1 and res.n_rejected == 0
    row = res.ledger.row(0, named=True)
    # gross must equal direction * (exit - entry) * units exactly (telescoping)
    expected = row["Units"] * (101.5 - 100.0)
    assert row["GrossMoney"] == pytest.approx(expected, rel=1e-12)
    # sizing: units = r*FM / stop
    assert row["Units"] == pytest.approx(0.005 * 100_000.0 / 1.0)
    assert res.equity[-1] - CFG.initial_equity == pytest.approx(row["NetMoney"])


def test_reconciliation_many_trades_with_costs():
    marks = make_marks(500, price0=100.0, drift=0.05)
    trades = [trade(60 * i, 60 * i + 300, 1.0 if i % 2 else -1.0, 100.0 + 0.05 * i,
                    100.0 + 0.05 * i + (0.7 if i % 2 else -0.3)) for i in range(1, 40)]
    s = make_stream("a", trades, marks, cost_bps=2.0)
    res = evaluate({"a"}, [s], CFG)
    ledger_net = res.ledger.get_column("NetMoney").sum()
    assert res.equity[-1] - CFG.initial_equity == pytest.approx(ledger_net, abs=1e-6)
    assert (res.ledger.get_column("CostMoney") > 0).all()


def test_loss_trade_books_negative():
    marks = make_marks(100, price0=100.0)
    s = make_stream("a", [trade(120, 600, 1.0, 100.0, 99.0)], marks)
    res = evaluate({"a"}, [s], CFG)
    assert res.ledger.row(0, named=True)["NetMoney"] < 0
    assert res.F_point < 0


def test_censored_trade_marked_to_last_open():
    marks = make_marks(10, price0=100.0, drift=1.0)  # opens 100..109
    s = make_stream("a", [trade(120, 10 ** 9, 1.0, 100.0, 999.0, censored=True)], marks)
    res = evaluate({"a"}, [s], CFG)
    row = res.ledger.row(0, named=True)
    assert row["Censored"] is True
    # marked to last open (109), NOT the bogus ExitPrice
    assert row["GrossMoney"] == pytest.approx(row["Units"] * (109.0 - 100.0), rel=1e-12)


# --------------------------------------------------------------------------- #
# Determinism
# --------------------------------------------------------------------------- #
def test_bit_identical_reruns():
    marks = make_marks(300, price0=100.0, drift=0.02)
    trades = [trade(60 * i, 60 * i + 240, (-1.0) ** i, 100.0, 100.5) for i in range(1, 30)]
    s = make_stream("a", trades, marks, cost_bps=1.0)
    r1 = evaluate({"a"}, [s], CFG, seed=0)
    r2 = evaluate({"a"}, [s], CFG, seed=7)  # seed must not matter in v1
    assert np.array_equal(r1.equity, r2.equity)
    assert np.array_equal(r1.equity_times, r2.equity_times)
    assert r1.ledger.equals(r2.ledger)
    assert r1.F_point == r2.F_point


# --------------------------------------------------------------------------- #
# Risk cap, rejection, non-additivity
# --------------------------------------------------------------------------- #
def overlapping_universe(n_candidates: int, marks: pl.DataFrame) -> list[CandidateStream]:
    """Candidates all entering at the same time, holding long — capacity contention."""
    return [make_stream(f"c{i}", [trade(120, 6000, 1.0, 100.0, 101.0)], marks)
            for i in range(n_candidates)]


def test_global_cap_rejects_and_logs():
    marks = make_marks(200, price0=100.0)
    # r=0.5% each, cap 5% → at most 10 concurrent; 12 candidates → 2 rejections
    streams = overlapping_universe(12, marks)
    res = evaluate({s.candidate_id for s in streams}, streams, CFG)
    assert res.n_admitted == 10
    assert res.n_rejected == 2
    rej = res.rejected
    assert rej.height == 2
    assert (rej.get_column("OpenRisk") + rej.get_column("RiskRequested")
            > rej.get_column("RiskCap")).all()


def test_capacity_frees_after_exit():
    marks = make_marks(400, price0=100.0)
    hoggers = [make_stream(f"h{i}", [trade(120, 300, 1.0, 100.0, 100.0)], marks)
               for i in range(10)]
    late = make_stream("late", [trade(600, 900, 1.0, 100.0, 100.5)], marks)
    streams = hoggers + [late]
    res = evaluate({s.candidate_id for s in streams}, streams, CFG)
    assert res.n_rejected == 0  # hoggers exited at t=300 before late's entry at t=600


def test_non_additivity_via_admission():
    """B's realized history differs depending on A's presence (problem-statement §3)."""
    marks = make_marks(400, price0=100.0)
    blockers = [make_stream(f"a{i}", [trade(60, 6000, 1.0, 100.0, 100.0)], marks)
                for i in range(10)]
    b = make_stream("b", [trade(120, 300, 1.0, 100.0, 102.0)], marks)  # winner if admitted
    solo = evaluate({"b"}, [b], CFG)
    combined = evaluate({s.candidate_id for s in blockers} | {"b"}, blockers + [b], CFG)
    assert solo.n_admitted == 1 and solo.F_point > 0
    b_rows = combined.ledger.filter(pl.col("CandidateId") == "b")
    assert b_rows.height == 0                      # b's trade was rejected
    assert combined.rejected.filter(pl.col("CandidateId") == "b").height == 1


def test_sizing_compounds_with_equity():
    """Later trades size off marked equity, not initial equity."""
    marks = make_marks(1000, price0=100.0)
    s = make_stream("a", [trade(60, 120, 1.0, 100.0, 120.0),      # +20% on risked units
                          trade(600, 900, 1.0, 100.0, 101.0)], marks)
    res = evaluate({"a"}, [s], CFG)
    r0 = res.ledger.row(0, named=True)
    r1 = res.ledger.row(1, named=True)
    equity_after_first = CFG.initial_equity + r0["NetMoney"]
    assert r1["Risk"] == pytest.approx(0.005 * equity_after_first, rel=1e-9)


# --------------------------------------------------------------------------- #
# Segment + interface
# --------------------------------------------------------------------------- #
def test_segment_filters_entries():
    marks = make_marks(1000, price0=100.0)
    s = make_stream("a", [trade(60, 120, 1.0, 100.0, 101.0),
                          trade(30_000, 30_100, 1.0, 100.0, 101.0)], marks)
    res = evaluate({"a"}, [s], CFG, segment=(0, 10_000 * NS))
    assert res.n_admitted == 1
    assert res.ledger.row(0, named=True)["EntryTime"] == 60 * NS


def test_segment_end_censors_open_positions():
    """Finding 1: a position exiting after the segment end is censored at the last
    in-segment mark; no P&L event lands outside the segment."""
    marks = make_marks(1000, price0=100.0, drift=0.1)  # opens 100, 100.1, ...
    seg_end_s = 300  # bars every 60s → last in-segment bar at 240s (index 4)
    s = make_stream("a", [trade(120, 30_000, 1.0, 100.2, 999.0)], marks)
    res = evaluate({"a"}, [s], CFG, segment=(0, seg_end_s * NS))
    row = res.ledger.row(0, named=True)
    assert row["Censored"] is True
    # marked to the last in-segment open (index 4 → 100.4), not the bogus exit price
    assert row["GrossMoney"] == pytest.approx(row["Units"] * (100.4 - 100.2), rel=1e-9)
    assert int(res.equity_times.max()) < seg_end_s * NS


def test_disjoint_segments_have_disjoint_pnl():
    """A long-holding trade must not leak P&L into the following fold."""
    marks = make_marks(1000, price0=100.0, drift=0.1)
    s = make_stream("a", [trade(120, 40_000, 1.0, 100.0, 200.0)], marks)
    seg1, seg2 = (0, 300 * NS), (300 * NS, 60_000 * NS)
    r1 = evaluate({"a"}, [s], CFG, segment=seg1)
    r2 = evaluate({"a"}, [s], CFG, segment=seg2)
    assert r1.n_admitted == 1 and r2.n_admitted == 0  # entry only in seg1
    assert int(r1.equity_times.max()) < 300 * NS       # all P&L inside seg1


def test_unknown_candidate_raises():
    marks = make_marks(10)
    s = make_stream("a", [trade(60, 120, 1.0, 100.0, 101.0)], marks)
    with pytest.raises(ValueError, match="unknown candidates"):
        evaluate({"nope"}, [s], CFG)


def test_empty_subset_is_flat():
    marks = make_marks(10)
    s = make_stream("a", [trade(60, 120, 1.0, 100.0, 101.0)], marks)
    res = evaluate(set(), [s], CFG)
    assert res.n_admitted == 0 and res.n_rejected == 0
    assert res.F_point == 0.0
    assert res.equity[-1] == CFG.initial_equity


def test_charge_costs_false_zeroes_costs():
    """Gross-selection amendment: selection configs run cost-free; ledger discloses 0."""
    marks = make_marks(100, price0=100.0)
    s = make_stream("a", [trade(120, 600, 1.0, 100.0, 101.0)], marks)
    s = CandidateStream("a", "TEST", s.trades, s.marks, cost_bps=5.0)
    net_cfg = CFG
    gross_cfg = OracleConfig(charge_costs=False)
    r_net = evaluate({"a"}, [s], net_cfg)
    r_gross = evaluate({"a"}, [s], gross_cfg)
    assert r_net.ledger.row(0, named=True)["CostMoney"] > 0
    assert r_gross.ledger.row(0, named=True)["CostMoney"] == 0.0
    assert r_gross.equity[-1] > r_net.equity[-1]


def test_nonpositive_stop_raises():
    marks = make_marks(10)
    s = make_stream("a", [trade(60, 120, 1.0, 100.0, 101.0, stop=0.0)], marks)
    with pytest.raises(ValueError, match="StopDistance"):
        evaluate({"a"}, [s], CFG)
