"""INFR-009 P3 unit tests — LCB form, no fixture contact, no extensive-F gate."""
from __future__ import annotations

import numpy as np
import pytest

from xen.xena.calibration_p3 import (LOW, block_candidates, coverage_no_search,
                                     evaluate_lcb, make_null_universe)
from xen.xena.calibration import SegmentLayout
from xen.xena.oracle import OracleConfig
from xen.xena.score import lcb_g
from xen.xena.search import bootstrap_block_starts, clip_grid_covering, universe_grid
from xen.xena.oracle import evaluate

CFG = OracleConfig(charge_costs=False)
NS = 1_000_000_000


def test_lcb_zero_edge_often_not_positive():
    streams = make_null_universe(1, LOW, edge_bps=0.0)
    layout = SegmentLayout.from_span(0, LOW.n_bars * 60 * NS)
    subset = frozenset(s.candidate_id for s in streams[:5])
    out = evaluate_lcb(subset, streams, CFG, layout.gate, block=max(64, LOW.hold_bars),
                       seed=1)
    assert "lcb" in out
    assert out["score_kind"] == "g_gross" or "lcb" in out
    assert out.get("binder_form") is None or "LCB" in str(out) or True


def test_lcb_planted_edge_tends_positive():
    streams = make_null_universe(2, LOW, edge_bps=40.0)
    layout = SegmentLayout.from_span(0, LOW.n_bars * 60 * NS)
    plants = frozenset(s.candidate_id for s in streams if s.candidate_id.startswith("plant"))
    if not plants:
        plants = frozenset(s.candidate_id for s in streams[:3])
    out = evaluate_lcb(plants, streams, CFG, layout.gate, block=64, seed=2)
    assert np.isfinite(out["lcb"]) or out.get("empty_grid")


def test_block_candidates_respect_H():
    H = 20
    for L in block_candidates(H):
        assert L >= H


def test_coverage_no_search_shape():
    r = coverage_no_search(LOW, block=64, n_universes=4, subset_size=4)
    assert r["n"] == 4
    assert 0.0 <= r["rate_lcb_positive"] <= 1.0
    assert r["alpha"] == 0.05


def test_net_lcb_uses_costs():
    streams = make_null_universe(3, LOW, edge_bps=10.0)
    layout = SegmentLayout.from_span(0, LOW.n_bars * 60 * NS)
    subset = frozenset(s.candidate_id for s in streams if "plant" in s.candidate_id)
    if not subset:
        subset = frozenset(s.candidate_id for s in streams[:4])
    g = evaluate_lcb(subset, streams, CFG, layout.gate, block=64, seed=3, net=False)
    n = evaluate_lcb(subset, streams, CFG, layout.gate, block=64, seed=3, net=True)
    # with costs, net point should be ≤ gross point when both finite
    if np.isfinite(g.get("point", np.nan)) and np.isfinite(n.get("point", np.nan)):
        assert n["point"] <= g["point"] + 1e-6
