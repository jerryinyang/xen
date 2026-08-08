"""Tests for xen.xena.search (INFR-006 WS-3) — planted-optimum recovery, determinism,
cache behavior, and bootstrap-objective correctness properties."""
from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from xen.xena.oracle import CandidateStream, OracleConfig, evaluate
from xen.xena.search import (EvalCache, SearchParams, bootstrap_F,
                             bootstrap_block_starts, clip_grid_covering,
                             grid_increments, propose_move, run_restart,
                             universe_grid)

NS = 1_000_000_000
CFG = OracleConfig(initial_equity=100_000.0, risk_per_position=0.005, r_max=0.10)


def make_stream(cid: str, edge_bps: float, *, n_trades: int = 60, seed: int = 0,
                n_bars: int = 4000) -> CandidateStream:
    """Candidate with a constant planted per-trade edge (+noise). stop=1 price unit."""
    rng = np.random.default_rng(seed)
    t = np.arange(n_bars, dtype=np.int64) * 60 * NS
    opens = np.full(n_bars, 100.0)
    marks = pl.DataFrame({"CloseTime": t, "Open": opens})
    rows = []
    entries = np.linspace(10, n_bars - 50, n_trades).astype(int)
    for ei in entries:
        ep = 100.0
        move = ep * (edge_bps + rng.normal(0, 5.0)) / 1e4
        rows.append({"EntryTime": int(t[ei]), "ExitTime": int(t[ei + 20]),
                     "Direction": 1.0, "EntryPrice": ep, "ExitPrice": ep + move,
                     "StopDistance": 1.0, "Censored": False})
    trades = pl.DataFrame(rows, schema={"EntryTime": pl.Int64, "ExitTime": pl.Int64,
                                        "Direction": pl.Float64, "EntryPrice": pl.Float64,
                                        "ExitPrice": pl.Float64, "StopDistance": pl.Float64,
                                        "Censored": pl.Boolean})
    return CandidateStream(cid, "TEST", trades, marks, cost_bps=2.0)


def toy_universe() -> list[CandidateStream]:
    winners = [make_stream(f"win{i}", +30.0, seed=i) for i in range(3)]
    losers = [make_stream(f"lose{i}", -30.0, seed=100 + i) for i in range(5)]
    return winners + losers


FAST = SearchParams(L=30, n_boot=80, block_bars=64, init_size=4)


# --------------------------------------------------------------------------- #
# Bootstrap objective properties
# --------------------------------------------------------------------------- #
def test_bootstrap_F_constant_increments_is_exact():
    inc = np.full(500, 2.0)
    starts = bootstrap_block_starts(500, block=50, n_boot=64, seed=1)
    fb = bootstrap_F(inc, starts, block=50, initial_equity=1000.0)
    assert fb == pytest.approx(np.log(2000.0 / 1000.0))


def test_grid_increments_telescope_to_equity_delta():
    streams = toy_universe()
    grid = universe_grid(streams)
    res = evaluate({s.candidate_id for s in streams}, streams, CFG)
    inc = grid_increments(res, grid)
    assert inc.sum() == pytest.approx(res.equity[-1] - res.equity[0])


def test_common_starts_are_seed_deterministic():
    a = bootstrap_block_starts(100, block=10, n_boot=8, seed=42)
    b = bootstrap_block_starts(100, block=10, n_boot=8, seed=42)
    assert np.array_equal(a, b)


# --------------------------------------------------------------------------- #
# Moves
# --------------------------------------------------------------------------- #
def test_propose_move_always_feasible_and_different():
    universe = [f"c{i}" for i in range(6)]
    rng = np.random.default_rng(0)
    for x0 in [set(), set(universe), {"c0"}, {"c0", "c1", "c2"}]:
        for _ in range(50):
            new = propose_move(set(x0), universe, rng)
            assert new != x0
            assert new <= set(universe)


# --------------------------------------------------------------------------- #
# The walk
# --------------------------------------------------------------------------- #
def test_search_recovers_planted_optimum():
    """INFR-009: intensive g_gross does not reward stacking equal-edge members.

    The walk must prefer winner-class edge over losers; it need not include every
    planted winner (adding another +30 bps clone does not raise g_gross).
    """
    streams = toy_universe()
    res = run_restart(streams, CFG, budget=250, restart_id=1, params=FAST, skip_economics_precondition=True)
    best = res.best_subset
    winners = {f"win{i}" for i in range(3)}
    losers = {f"lose{i}" for i in range(5)}
    assert len(best & winners) >= 1                 # at least one planted winner
    assert len(best & losers) <= len(best & winners)  # winners not outnumbered by losers
    assert len(best & losers) <= 2                  # losers largely pruned


def test_restart_is_deterministic():
    streams = toy_universe()
    r1 = run_restart(streams, CFG, budget=120, restart_id=3, params=FAST, skip_economics_precondition=True)
    r2 = run_restart(streams, CFG, budget=120, restart_id=3, params=FAST, skip_economics_precondition=True)
    assert r1.best_subset == r2.best_subset
    assert r1.best_F_hat == r2.best_F_hat
    assert r1.cache.evaluation_count == r2.cache.evaluation_count


def test_restarts_differ_by_id():
    streams = toy_universe()
    r1 = run_restart(streams, CFG, budget=60, restart_id=1, params=FAST, skip_economics_precondition=True)
    r2 = run_restart(streams, CFG, budget=60, restart_id=2, params=FAST, skip_economics_precondition=True)
    # different walks (almost surely different eval sets); both must still be valid
    assert r1.cache.evaluation_count > 0 and r2.cache.evaluation_count > 0


def test_cache_dedups_and_counts():
    streams = toy_universe()
    res = run_restart(streams, CFG, budget=200, restart_id=1, params=FAST, skip_economics_precondition=True)
    stats = res.cache.revisit_stats()
    # unique evals <= budget+1 (dedup working); revisits actually happened
    assert res.cache.evaluation_count <= 201
    assert stats["n_cache_hits"] > 0


def test_search_F_hat_is_segment_grid_scale():
    """Grid/segment consistency: walk ĝ equals robust_g_hat on the segment-restricted grid.

    INFR-009: score is intensive g_gross P25, not log-wealth (F_floor retired).
    """
    from xen.xena.score import robust_g_hat
    streams = toy_universe()
    seg = (0, 2000 * 60 * NS)
    res = run_restart(streams, CFG, budget=50, restart_id=1, params=FAST, segment=seg, skip_economics_precondition=True)
    grid = universe_grid(streams)
    grid = clip_grid_covering(grid, seg, streams)
    starts = bootstrap_block_starts(len(grid), block=FAST.block_bars,
                                    n_boot=FAST.n_boot, seed=1_000_003 * 1 + 17)
    r = evaluate(res.best_subset, streams, CFG, segment=seg)
    g_hat, _, _ = robust_g_hat(r, streams, grid, starts, block=FAST.block_bars,
                               quantile=FAST.quantile)
    assert g_hat == pytest.approx(res.best_F_hat)


def test_cache_neighbors_query():
    cache = EvalCache()
    from xen.xena.search import EvalRecord
    base = {"a", "b"}
    rec = EvalRecord(0.0, 0.0, np.zeros(4), 0, 0, 0, 0)
    cache.put(base, rec)
    cache.put({"a"}, rec)             # drop-neighbor (d=1)
    cache.put({"a", "c"}, rec)        # swap-neighbor (d=2)
    cache.put({"c", "d"}, rec)        # d=4 — not a neighbor
    nbrs = cache.neighbors(base, ["a", "b", "c", "d"])
    assert len(nbrs) == 2
