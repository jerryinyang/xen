"""INFR-009 P3b unit tests — studentized LCB, purged layout, no fixtures."""
from __future__ import annotations


from xen.xena.calibration import SegmentLayout
from xen.xena.calibration_p3b import (LOW, SEED_BASE_LOW, coverage_no_search,
                                      evaluate_lcb_st, make_null_universe)
from xen.xena.oracle import OracleConfig
from xen.xena.score import lcb_g_studentized
from xen.xena.search import bootstrap_block_starts, clip_grid_covering, universe_grid
from xen.xena.oracle import evaluate

CFG = OracleConfig(charge_costs=False)
NS = 1_000_000_000


def test_purge_separates_ranking_and_gate():
    H = 20
    purge = H * 60 * NS
    lay = SegmentLayout.from_span(0, 6000 * 60 * NS, purge_ns=purge)
    assert lay.ranking[1] + purge == lay.gate[0]
    assert lay.purge_ns == purge
    assert lay.gate[0] > lay.ranking[1]


def test_studentized_lcb_emits_diagnostics():
    streams = make_null_universe(SEED_BASE_LOW + 1, LOW, n_candidates=12)
    layout = SegmentLayout.from_span(0, LOW.n_bars * 60 * NS,
                                     purge_ns=LOW.hold_bars * 60 * NS)
    subset = frozenset(s.candidate_id for s in streams[:5])
    res = evaluate(subset, streams, CFG, segment=layout.gate, seed=1)
    grid = clip_grid_covering(universe_grid(streams), layout.gate, streams)
    starts = bootstrap_block_starts(len(grid), block=64, n_boot=80, seed=1)
    out = lcb_g_studentized(res, streams, grid, starts, block=64)
    assert out["method"] == "studentized_bootstrap_t"
    assert "n_legs" in out and "empty_bar_fraction" in out
    assert "n_nonempty_blocks" in out


def test_floor_veto_retired_small_n_still_read():
    """INFR-022 L-63: the n_legs_floor out-of-domain veto is deleted; a tiny-n subset is
    still evaluated with its sample-size context reported."""
    streams = make_null_universe(SEED_BASE_LOW + 2, LOW, n_candidates=12)
    layout = SegmentLayout.from_span(0, LOW.n_bars * 60 * NS,
                                     purge_ns=LOW.hold_bars * 60 * NS)
    subset = frozenset(s.candidate_id for s in streams[:3])
    out = evaluate_lcb_st(subset, streams, CFG, layout.gate, block=64, seed=2)
    assert "out_of_calibration_domain" not in out
    assert "n_legs" in out  # sample size reported as context, never a veto


def test_coverage_shape_studentized():
    r = coverage_no_search(LOW, block=64, n_universes=4, n_cand=12)
    assert r["method"] == "studentized_bootstrap_t"
    assert r["n"] == 4
    assert 0.0 <= r["rate_lcb_positive"] <= 1.0


def test_seeds_disjoint_from_p3():
    assert SEED_BASE_LOW >= 11_000
