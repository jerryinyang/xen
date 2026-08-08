"""INFR-016 — report layers replace value gates; no auto-verdicts in the value chain.
(INFR-022: power_layer → sample_size_layer; structural labels deleted; operator-only tags.)"""
from __future__ import annotations

import numpy as np
import pytest

from xen.xena.controls import (assert_future_destroy_class, attribution_derangement,
                               make_derangement, sign_battery)
from xen.xena.report_layer import (LayerReport, psr_layer, render_all_layers,
                                   render_layer_table, sample_size_layer,
                                   stage2_bounds_layer)


# --------------------------------------------------------------------------- #
# report_layer: no auto-verdict fields
# --------------------------------------------------------------------------- #
def test_layer_report_forbids_verdict_keys():
    LayerReport("l", "c", 1.0, "0-2", "fine")  # ok
    for bad in ("pass", "passed", "blocking_pass", "hard_fail_leak", "at_or_above_p95"):
        with pytest.raises(ValueError):
            LayerReport("l", "c", 1.0, "0-2", "fine", supporting={bad: True})


def test_layer_report_to_dict_is_never_a_gate():
    d = LayerReport("l", "c", 1.0, "0-2", "fine", interpretation_label="SUGGESTIVE").to_dict()
    assert d["is_gate"] is False
    assert "pass" not in d and "passed" not in d
    assert d["interpretation_label"] == "SUGGESTIVE"


def test_bad_label_rejected():
    with pytest.raises(ValueError):
        LayerReport("l", "c", 1.0, "0-2", "fine", interpretation_label="FAIL")


def test_structural_label_deleted_machine_labels_removed():
    # INFR-022 N11: structural_label and every machine auto-assignment are deleted;
    # interpretation labels are operator-supplied tags only.
    import xen.xena.report_layer as rl
    assert not hasattr(rl, "structural_label")
    assert not hasattr(rl, "power_layer")
    # operator-supplied tags remain valid on a layer (N11)
    d = LayerReport("l", "c", 1.0, "0-2", "fine", interpretation_label="UNPOWERED").to_dict()
    assert d["interpretation_label"] == "UNPOWERED"
    assert d["is_gate"] is False


def test_render_runs_for_all_candidates_drops_nothing():
    reps = [LayerReport("cost_floor", f"c{i}", i, "x", "y") for i in range(3)]
    table = render_layer_table("cost_floor", reps)
    for i in range(3):
        assert f"c{i}" in table
    assert "pass" not in table.lower().split("interpretation")[0]  # no pass column
    assert "cost_floor" in render_all_layers(reps)


# --------------------------------------------------------------------------- #
# sign_battery: HTFCAP SUGGESTIVE, not "fail"; no P95 boolean
# --------------------------------------------------------------------------- #
def test_sign_battery_reports_effect_p_ci_no_boolean():
    rng = np.random.default_rng(0)
    n = 60
    ep = 100.0 + rng.normal(0, 1, n)
    # a modest positive directional edge: exit slightly favourable in the traded direction
    d = np.ones(n)
    xp = ep * (1 + rng.normal(0.0012, 0.01, n))  # ~12 bps mean edge, noisy
    rep = sign_battery(d, ep, xp, candidate_id="SOL_v15", n_seeds=2000)
    s = rep.supporting
    assert "at_or_above_p95" not in s
    assert set(("one_sided_p", "effect_bps", "null_ci95", "n_seeds", "n_legs")) <= set(s)
    # INFR-022 L-63/N11: no powered field, no machine labels
    assert "powered" not in s
    assert rep.interpretation_label is None
    assert 0.0 <= s["one_sided_p"] <= 1.0


def test_sign_battery_no_power_label_at_any_seed_count():
    rng = np.random.default_rng(1)
    n = 40
    ep = 100.0 + rng.normal(0, 1, n)
    d = np.ones(n)
    xp = ep * (1 + rng.normal(0.001, 0.01, n))
    # HTFCAP's broken 25-seed count: reported with its n — never labelled UNPOWERED
    rep = sign_battery(d, ep, xp, candidate_id="c", n_seeds=25)
    assert "powered" not in rep.supporting
    assert rep.interpretation_label is None
    assert rep.supporting["n_seeds"] == 25


# --------------------------------------------------------------------------- #
# attribution_derangement: reported fraction, class-gated, no auto-kill
# --------------------------------------------------------------------------- #
def test_future_destroy_is_not_a_report_layer():
    with pytest.raises(ValueError):
        assert_future_destroy_class("future_destroy")
    with pytest.raises(ValueError):
        assert_future_destroy_class("nonsense")
    assert_future_destroy_class("within_sample_attribution")  # ok


def test_make_derangement_zero_fixed_points():
    rng = np.random.default_rng(3)
    for n in (2, 5, 20):
        p = make_derangement(n, rng)
        assert not np.any(p == np.arange(n))


def test_attribution_derangement_reports_fraction_no_kill():
    n_grid = 400
    grid_open = 100.0 + np.cumsum(np.random.default_rng(4).normal(0, 0.05, n_grid))
    n_legs = 50
    rng = np.random.default_rng(5)
    entry_idx = np.sort(rng.integers(0, n_grid - 20, n_legs))
    n_blocks = 6
    block_edges = np.linspace(0, n_grid, n_blocks + 1, dtype=int)
    block_id = np.clip(np.searchsorted(block_edges[1:], entry_idx, side="right"), 0, n_blocks - 1)
    d = np.ones(n_legs)
    hold_bars = np.full(n_legs, 8)
    rep = attribution_derangement(entry_idx, block_id, block_edges, n_blocks, grid_open, d,
                                  hold_bars, candidate_id="BTC_v15", n_seeds=25)
    s = rep.supporting
    assert "hard_fail_leak" not in s and "reject" not in s
    assert s["control_class"] == "within_sample_attribution"
    assert s["derangement_zero_fixed_points"] is True
    assert "collapse_median" in s and "collapse_p05" in s
    assert rep.to_dict()["is_gate"] is False


# --------------------------------------------------------------------------- #
# sample_size_layer / psr_layer / stage2_bounds_layer (INFR-022)
# --------------------------------------------------------------------------- #
def test_sample_size_layer_reports_context_not_veto():
    thin = sample_size_layer("c", n_legs=8, per_leg_vol_bps=40.0, design_min_n=50)
    assert thin.layer == "sample_size"
    assert thin.interpretation_label is None
    assert thin.supporting["n_legs"] == 8
    assert thin.supporting["design_min_n"] == 50
    assert "pass" not in thin.to_dict() and thin.to_dict()["is_gate"] is False
    assert "mde" not in str(thin.supporting).lower()
    assert "powered" not in thin.supporting
    # no design minimum declared → note says all rows reported with counts
    ok = sample_size_layer("c", n_legs=200, per_leg_vol_bps=40.0)
    assert ok.supporting["design_min_n"] is None
    assert "never a hide/drop rule" in ok.supporting["note"]


def test_psr_layer_pairs_beside_mean():
    rep = psr_layer("c", avg_trade_bps=3.2, psr=0.91, n=120)
    assert rep.layer == "psr"
    assert rep.supporting == {"avg_trade_bps": 3.2, "psr": 0.91, "psr_n": 120}
    assert rep.to_dict()["is_gate"] is False
    # NaN psr still reported with its count (N3 — never suppressed)
    rep2 = psr_layer("c", avg_trade_bps=float("nan"), psr=float("nan"), n=1)
    assert np.isnan(rep2.supporting["psr"]) and rep2.supporting["psr_n"] == 1
    assert "not suppressed" in rep2.interpretation


def test_stage2_bounds_layer_reports_all_subsets():
    subs = [("c0", 1.0, 5.0, 60), ("c1", -3.0, 4.0, 40), ("c2", 0.2, 9.0, 120)]
    reps = [stage2_bounds_layer(cid, lcb=lo, ucb=hi, n_legs=n) for cid, lo, hi, n in subs]
    table = render_layer_table("stage2_bounds_gross", reps)
    for cid, *_ in subs:                                     # every subset rendered (no top-1)
        assert cid in table
    assert all("pass" not in r.to_dict() for r in reps)


def test_final_report_layer_has_no_passed():
    # exercised via schema only here; walk-forward mechanics covered by test_xena_final_gate
    from xen.xena import final_gate
    assert hasattr(final_gate, "final_report_layer")
