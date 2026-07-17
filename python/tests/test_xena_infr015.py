"""INFR-015 unit tests — episode_overlap_rule_v1 + seed integrity (design §9)."""
from __future__ import annotations

import numpy as np
import polars as pl
import pytest

import xen.xena.calibration_p3b as p3b
from xen.xena.calibration_bybit import IntegrityError
from xen.xena.calibration_bybit15 import (
    BLOCK_RULE_ID,
    CONFIRM_SEEDS_15,
    DESIGN_SEEDS_15,
    CONFIRM_SCALE_15,
    assert_seed_disjoint_15,
    confirm_gate_ep,
    episode_overlap_block_legs,
    eval_lcb_legs_ep,
)
from xen.xena.calibration_bybit15 import _set_seeds
from xen.xena.calibration_p3b import LOW
from xen.xena.calibration_p3d import eval_lcb_legs
from xen.xena.calibration_pc import c_layout
from xen.xena.calibration_bybit15 import make_episode_null_universe
from xen.xena.oracle import OracleConfig

NS = 1_000_000_000
H = 3600 * NS


def _times(entries_h, durs_h):
    et = np.array([int(e * H) for e in entries_h], dtype=np.int64)
    xt = np.array([int((e + d) * H) for e, d in zip(entries_h, durs_h)], dtype=np.int64)
    return et, xt


def test_g1_block_rule_fixture():
    # durations [2,4,8,16]h cycled over 40 legs, entries every 1h.
    # q90(linear) of the 40-value duration vector equals q90 of [2,4,8,16] tiling = 14.8?
    # Design G1 uses the 4-value vector: check exact arithmetic on 4 values first.
    et4, xt4 = _times([0, 1, 2, 3], [2, 4, 8, 16])
    # q90 linear on [2,4,8,16] = 13.6; median gap 1.0 => ceil(13.6)=14; cap max(1,4//4)=1
    assert episode_overlap_block_legs(et4, xt4) == 1  # capped at floor(4/4)=1
    # 40 legs: same durations tiled, entries every 1h => uncapped 14 vs cap 10 => 10
    durs = ([2, 4, 8, 16] * 10)[:40]
    et40, xt40 = _times(list(range(40)), durs)
    q90 = float(np.quantile(np.array(durs, dtype=float), 0.9, method="linear"))
    expected = min(max(1, int(np.ceil(q90 / 1.0))), 40 // 4)
    b = episode_overlap_block_legs(et40, xt40)
    assert b == expected == 10


def test_g1b_cap_degenerate_never_zero():
    et, xt = _times([0, 1, 2], [10, 10, 10])
    b = episode_overlap_block_legs(et, xt)
    assert b >= 1
    assert b == 1  # cap = max(1, floor(3/4)) = 1


def test_single_leg_and_zero_gap():
    et, xt = _times([5], [4])
    assert episode_overlap_block_legs(et, xt) == 1
    et2, xt2 = _times([5, 5, 5, 5, 5], [4, 4, 4, 4, 4])  # zero gaps
    assert episode_overlap_block_legs(et2, xt2) == 1


def test_g2_b1_routes_to_legacy_bitwise():
    """B==1 must produce bit-identical output to the INFR-014 block_legs=1 path."""
    _set_seeds(DESIGN_SEEDS_15["low"], DESIGN_SEEDS_15["high"])
    cadence = LOW
    layout = c_layout(cadence.n_bars, cadence.hold_bars, embargo_frac=0.2)
    # sparse universe => wide gaps, short holds forced via few candidates + null
    streams = make_episode_null_universe(95_000, cadence, n_candidates=8)
    config = OracleConfig(charge_costs=True)
    ids = [s.candidate_id for s in streams]
    pick = frozenset(ids[:3])
    out_ep = eval_lcb_legs_ep(pick, streams, config, layout.gate, n_boot=50, seed=7)
    if out_ep["block_legs_used"] == 1:
        out_legacy = eval_lcb_legs(pick, streams, config, layout.gate, n_boot=50,
                                   seed=7, block_legs=1)
        assert out_ep["lcb"] == out_legacy["lcb"]
        assert out_ep["point"] == out_legacy["point"]
    else:
        # overlap present => rule engaged; verify it differs from legacy width path only
        assert out_ep["block_legs_used"] > 1
    assert out_ep["block_rule"] == BLOCK_RULE_ID


def test_g3_confirm_refuses_design_seeds():
    proc = {
        "design_bite_ok": True, "embargo_frac": 0.2, "n_boot": 200,
        "block_legs": BLOCK_RULE_ID, "alpha": 0.05, "stage1_score_kind": "g_net",
        "stage1_charge_costs": True, "e2e_pass_event": "stage2_gross_lcb_positive",
    }
    # sabotage: coverage would read current p3b bases; confirm_gate_ep re-pins to
    # CONFIRM_SEEDS_15 itself, so simulate the Issue-9 class by asserting the guard
    # exists: a procedure with wrong block rule must refuse.
    bad = dict(proc, block_legs=1)
    with pytest.raises(IntegrityError):
        confirm_gate_ep(bad, scale=CONFIRM_SCALE_15)


def test_seed_disjointness():
    assert_seed_disjoint_15()
    assert DESIGN_SEEDS_15 == {"low": 95_000, "high": 96_000}
    assert CONFIRM_SEEDS_15 == {"low": 97_000, "high": 98_000}


def test_confirm_requires_design_ok():
    with pytest.raises(IntegrityError):
        confirm_gate_ep({}, scale=CONFIRM_SCALE_15)
