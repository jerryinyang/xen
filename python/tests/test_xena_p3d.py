"""INFR-009 P3d — leg bootstrap LCB unit tests."""
from __future__ import annotations

import numpy as np

from xen.xena.calibration_p3b import LOW, make_null_universe
from xen.xena.oracle import OracleConfig, evaluate
from xen.xena.score import bootstrap_g_legs, ledger_leg_arrays, lcb_g_leg_studentized


def test_leg_bootstrap_zero_edge_finite():
    streams = make_null_universe(31001, LOW, n_candidates=8)
    res = evaluate(frozenset(s.candidate_id for s in streams[:4]), streams,
                   OracleConfig(charge_costs=False), seed=0)
    pnl, notional, et = ledger_leg_arrays(res, streams)
    assert len(pnl) == len(notional) == len(et)
    boot = bootstrap_g_legs(pnl, notional, n_boot=50, seed=1, block_legs=1)
    assert len(boot) == 50
    assert np.isfinite(boot).sum() > 0


def test_lcb_leg_studentized_fields():
    streams = make_null_universe(31002, LOW, n_candidates=8)
    res = evaluate(frozenset(s.candidate_id for s in streams[:4]), streams,
                   OracleConfig(charge_costs=False), seed=1)
    out = lcb_g_leg_studentized(res, streams, n_boot=80, seed=2, block_legs=1)
    assert out["method"] == "leg_studentized_bootstrap_t"
    assert out["resample_unit"] == "legs"
    assert "n_legs" in out
    assert "pass_positive" in out
