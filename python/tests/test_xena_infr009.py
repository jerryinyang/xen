"""INFR-009 P0–P2 unit tests: economics integrity, g_gross score, evidence package,
fill-basis, high-cadence null. No TEST/holdout contact; no fixture tuning."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from xen.xena.economics import (SearchRefusedIntegrity, check_cost_map_integrity,
                                economics_disclosure, is_placeholder_cost,
                                require_economics_before_search)
# SearchRefusedIntegrity also raised from run_restart (P0 hard entry)
from xen.xena.fill_basis import (decompose_stream, summarize_decomposition)
from xen.xena.high_cadence_null import (HighCadenceNullSpec, build_high_cadence_null,
                                        null_diagnostics)
from xen.xena.oracle import CandidateStream, OracleConfig, evaluate
from xen.xena.score import (bootstrap_g_gross, g_gross_from_ledger, g_gross_point,
                            grid_gross_notional, robust_g_hat)
from xen.xena.search import (SearchParams, bootstrap_block_starts, clip_grid_covering,
                             run_restart, universe_grid)
from xen.xena.certify import (certify_and_rank, contiguous_purged_folds,
                              random_subset_reference)

NS = 1_000_000_000
CFG = OracleConfig(initial_equity=100_000.0, risk_per_position=0.005, r_max=0.10,
                   charge_costs=False)


def _stream(cid: str, edge_bps: float, *, n_trades: int = 40, seed: int = 0,
            n_bars: int = 2000, cost_bps: float = 2.0,
            entry_offset_bps: float = 0.0) -> CandidateStream:
    """Planted-edge stream; optional entry_offset_bps creates print premium vs bar open."""
    rng = np.random.default_rng(seed)
    t = np.arange(n_bars, dtype=np.int64) * 60 * NS
    opens = np.full(n_bars, 100.0)
    marks = pl.DataFrame({"CloseTime": t, "Open": opens})
    rows = []
    entries = np.linspace(10, n_bars - 50, n_trades).astype(int)
    for ei in entries:
        ep = 100.0 * (1.0 - entry_offset_bps / 1e4)  # buy below open → positive print
        move = 100.0 * (edge_bps + rng.normal(0, 2.0)) / 1e4
        rows.append({
            "EntryTime": int(t[ei]), "ExitTime": int(t[ei + 20]),
            "Direction": 1.0, "EntryPrice": ep, "ExitPrice": 100.0 + move,
            "StopDistance": 1.0, "Censored": False,
        })
    trades = pl.DataFrame(rows)
    return CandidateStream(cid, "TEST", trades, marks, cost_bps=cost_bps)


# --------------------------------------------------------------------------- #
# P0 — cost integrity + economics disclosure
# --------------------------------------------------------------------------- #
def test_placeholder_cost_detected():
    assert is_placeholder_cost(0.0)
    assert is_placeholder_cost(None)
    assert is_placeholder_cost(float("nan"))
    assert not is_placeholder_cost(1.5)


def test_cost_map_integrity_blocks_zero_pins():
    cands = [
        {"candidate_id": "a", "symbol": "USTEC", "cost_bps": 0.0, "money_per_unit": 1.0},
        {"candidate_id": "b", "symbol": "EURUSD", "cost_bps": 2.0, "money_per_unit": 1.0},
    ]
    st = check_cost_map_integrity(cands)
    assert not st.complete
    assert st.n_incomplete == 1
    assert st.reason == "INTEGRITY_INCOMPLETE"


def test_cost_map_complete_with_real_pins():
    cands = [
        {"candidate_id": "a", "symbol": "USTEC", "cost_bps": 1.2, "money_per_unit": 1.0},
        {"candidate_id": "b", "symbol": "EURUSD", "cost_bps": 0.8, "money_per_unit": 1.0},
    ]
    assert check_cost_map_integrity(cands).complete


def test_economics_disclosure_writes_and_refuses_search(tmp_path: Path):
    # minimal fake emission
    run = tmp_path / "c1"
    run.mkdir()
    n = 30
    t0 = 1_000_000_000_000
    cis = pl.DataFrame({
        "EntryTime": pl.Series([t0 + i * 60_000_000_000 for i in range(n)]).cast(pl.Datetime("ns")),
        "ExitTime": pl.Series([t0 + (i + 5) * 60_000_000_000 for i in range(n)]).cast(pl.Datetime("ns")),
        "Direction": [1.0] * n,
        "EntryFillPrice": [100.0] * n,
        "ExitFillPrice": [100.02] * n,  # +2 bps
        "RealizedBps": [2.0] * n,
        "Censored": [False] * n,
        "SlPrice": [99.0] * n,
    })
    pos = pl.DataFrame({
        "SourceCloseTime": pl.Series([t0 + i * 60_000_000_000 for i in range(n + 10)]).cast(pl.Datetime("ns")),
        "RealOpen": [100.0] * (n + 10),
    })
    cis.write_parquet(run / "cis_trades.parquet")
    pos.write_parquet(run / "positions.parquet")
    man = {
        "universe_id": "TOY",
        "candidates": [{
            "candidate_id": "C1-USTEC-1H5M-H05X-V00",
            "run_dir": "c1", "symbol": "USTEC",
            "cost_bps": 0.0, "money_per_unit": 1.0,
        }],
    }
    mpath = tmp_path / "universe_manifest.json"
    mpath.write_text(json.dumps(man))
    art = economics_disclosure(mpath, max_workers=1)
    assert art["cost_map_integrity"]["complete"] is False
    assert art["search_allowed"] is False
    assert art["gross_economics"]["p50"] == pytest.approx(2.0, abs=0.01)
    with pytest.raises(SearchRefusedIntegrity):
        require_economics_before_search(tmp_path)


# --------------------------------------------------------------------------- #
# P1 — intensive g_gross
# --------------------------------------------------------------------------- #
def test_g_gross_is_intensive_not_extensive():
    """Doubling identical trades does not double g_gross (unlike log-wealth F)."""
    s1 = _stream("one", +20.0, n_trades=20, seed=1)
    # two copies → more trades, same edge density
    s2a = _stream("a", +20.0, n_trades=20, seed=1)
    s2b = _stream("b", +20.0, n_trades=20, seed=1)
    # shift b times so they don't collide on capacity (separate cids)
    # rebuild b with offset entries
    r1 = evaluate({"one"}, [s1], CFG)
    r2 = evaluate({"a", "b"}, [s2a, s2b], CFG)
    g1 = g_gross_point(r1, [s1])
    g2 = g_gross_point(r2, [s2a, s2b])
    assert np.isfinite(g1) and np.isfinite(g2)
    # intensive: same order of magnitude (~20 bps), not 2×
    assert abs(g2 - g1) < abs(g1) * 0.5 + 5.0
    # extensive F grows with more activity
    assert r2.F_point > r1.F_point * 1.2 or r2.n_admitted > r1.n_admitted


def test_bootstrap_g_gross_constant_bars():
    gross = np.full(200, 1.0)
    notional = np.full(200, 1000.0)
    starts = bootstrap_block_starts(200, block=20, n_boot=32, seed=3)
    boot = bootstrap_g_gross(gross, notional, starts, block=20)
    assert boot == pytest.approx(np.full(32, 1e4 * 1.0 / 1000.0))


def test_search_uses_g_gross_score_kind():
    streams = [_stream(f"w{i}", +30.0, seed=i) for i in range(3)] + [
        _stream(f"l{i}", -30.0, seed=100 + i) for i in range(4)]
    res = run_restart(streams, CFG, budget=80, restart_id=1,
                      params=SearchParams(L=20, n_boot=40, init_size=3))
    rec = res.cache.get(res.best_subset)
    assert rec is not None
    assert rec.score_kind == "g_gross"
    assert {"w0", "w1", "w2"} & res.best_subset


def test_search_refuses_placeholder_costs():
    streams = [_stream("a", +10.0, cost_bps=0.0, seed=1),
               _stream("b", -10.0, cost_bps=0.0, seed=2)]
    with pytest.raises(SearchRefusedIntegrity):
        run_restart(streams, CFG, budget=10, restart_id=1,
                    params=SearchParams(L=5, n_boot=8, init_size=1))


def test_evidence_package_retires_binders():
    streams = [_stream(f"w{i}", +25.0, seed=i) for i in range(3)] + [
        _stream(f"l{i}", -25.0, seed=50 + i) for i in range(3)]
    params = SearchParams(L=20, n_boot=40, init_size=3)
    finals = [run_restart(streams, CFG, budget=60, restart_id=i, params=params)
              for i in (1, 2)]
    folds = contiguous_purged_folds(0, 2000 * 60 * NS, n_folds=2, purge_ns=60 * 60 * NS)
    out = certify_and_rank(finals, streams, CFG, folds=folds, params=params,
                           include_random_ref=True, n_random_ref=16)
    assert out["package_kind"] == "evidence_package"
    assert "F_floor" in out["retired_binders"]
    assert "S_as_pass_threshold" in out["retired_binders"]
    assert out["random_subset_reference"] is not None
    assert out["random_subset_reference"]["binding"] is False
    assert out["jaccard_core_spread"]["binding"] is False
    assert out["fill_basis"] is not None
    assert out["fill_basis"].get("binding") is False
    assert out["net_companion"] is not None
    assert out["net_companion"].get("binding") is False


def test_S_not_used_as_pass_threshold():
    streams = [_stream(f"w{i}", +40.0, seed=i) for i in range(4)]
    live = frozenset(s.candidate_id for s in streams[:2])
    ref = random_subset_reference(live, streams, CFG, n_random=20, seed=1)
    assert ref["binding"] is False
    assert "S" in ref


# --------------------------------------------------------------------------- #
# P0′ — high-cadence null
# --------------------------------------------------------------------------- #
def test_high_cadence_null_zero_edge_and_density():
    # compact but still high-cadence for unit speed
    spec = HighCadenceNullSpec(
        n_candidates=12, n_bars=12_000, target_legs_per_candidate=2_500,
        hold_bars=8, seed=7)
    streams = build_high_cadence_null(spec)
    diag = null_diagnostics(streams)
    assert diag["zero_edge_ok"]
    assert diag["high_cadence_ok"]
    assert abs(diag["entry_edge_mean_of_means_bps"]) < 1.0
    assert diag["legs_per_candidate_median"] >= 2000


# --------------------------------------------------------------------------- #
# P2 — print vs path
# --------------------------------------------------------------------------- #
def test_grid_entry_print_near_zero():
    s = _stream("grid", +10.0, entry_offset_bps=0.0, seed=2)
    df = decompose_stream(s)
    summ = summarize_decomposition(df)
    assert summ["identity_ok"]
    assert abs(summ["print_mean_bps"]) < 0.05
    assert summ["grid_like"]


def test_limit_print_dominance():
    s = _stream("lim", +2.0, entry_offset_bps=8.0, seed=3)  # ~8 bps print
    df = decompose_stream(s)
    summ = summarize_decomposition(df)
    assert summ["identity_ok"]
    assert summ["print_mean_bps"] > 5.0
    assert summ["limit_print_dominance"] or summ["print_mean_bps"] > summ["path_mean_bps"]
