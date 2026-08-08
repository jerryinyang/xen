"""Tests for xen.xena.certify (INFR-006 WS-4) — keystone detection, cliff-screen pass on
genuine plateaus, noise-only rejection, fold ranking, dispersion diagnostics."""
from __future__ import annotations

import numpy as np
import pytest

from xen.xena.certify import (certify_and_rank, contiguous_purged_folds,
                              dispersion_report, plateau_screen, rank_on_folds)
from xen.xena.search import SearchParams, run_restart

from tests.test_xena_search import CFG, make_stream, toy_universe

NS = 1_000_000_000
FAST = SearchParams(L=30, n_boot=80, block_bars=64, init_size=4)


# --------------------------------------------------------------------------- #
# Folds
# --------------------------------------------------------------------------- #
def test_contiguous_purged_folds_disjoint_and_ordered():
    folds = contiguous_purged_folds(0, 1000 * NS, n_folds=4, purge_ns=10 * NS)
    assert len(folds) == 4
    for (a1, b1), (a2, b2) in zip(folds, folds[1:]):
        assert a1 < b1 <= a2 < b2  # ordered, disjoint (purge gap between folds)


def test_purge_too_large_raises():
    with pytest.raises(ValueError, match="purge"):
        contiguous_purged_folds(0, 100, n_folds=4, purge_ns=50)


# --------------------------------------------------------------------------- #
# Plateau screen
# --------------------------------------------------------------------------- #
def test_keystone_detected():
    """One candidate carries all the P&L; drop-screen must fail and name it."""
    hero = make_stream("hero", +60.0, seed=1)
    passengers = [make_stream(f"flat{i}", 0.0, seed=10 + i) for i in range(3)]
    streams = [hero] + passengers
    subset = frozenset(s.candidate_id for s in streams)
    rep = plateau_screen(subset, streams, CFG, threshold=0.5, f_floor=0.0, restart_seed=1,
                         params=FAST)
    assert not rep.passed
    assert rep.keystone == "hero"
    assert rep.drop_scores["hero"] < min(rep.drop_scores[f"flat{i}"] for i in range(3))


def test_broad_plateau_passes():
    """Several similar winners: removing any one member keeps most of F̂."""
    streams = [make_stream(f"win{i}", +40.0, seed=i) for i in range(6)]
    subset = frozenset(s.candidate_id for s in streams)
    rep = plateau_screen(subset, streams, CFG, threshold=0.5, f_floor=0.0, restart_seed=1,
                         params=FAST)
    assert rep.passed, (rep.min_drop_ratio, rep.drop_scores)
    # INFR-009: keystone always recorded as attribution (worst-drop member)
    assert rep.keystone is not None
    assert rep.min_drop_ratio >= 0.5


def test_f_floor_legacy_flag_not_binding():
    """INFR-009: f_floor only affects the legacy ``passed`` flag, not ratio computation.

    When base ĝ is below the (retired) floor, legacy_pass is False but keystone
    attribution still runs when drop scores exist.
    """
    streams = [make_stream(f"win{i}", +40.0, seed=i) for i in range(6)]
    subset = frozenset(s.candidate_id for s in streams)
    rep = plateau_screen(subset, streams, CFG, threshold=0.5, f_floor=1e9,
                         restart_seed=1, params=FAST)
    assert not rep.passed          # legacy flag
    assert rep.binding is False    # not a shortlist binder
    assert rep.keystone is not None or np.isfinite(rep.min_drop_ratio)


def test_nonpositive_objective_cannot_certify():
    streams = [make_stream(f"lose{i}", -40.0, seed=i) for i in range(4)]
    subset = frozenset(s.candidate_id for s in streams)
    rep = plateau_screen(subset, streams, CFG, threshold=0.5, f_floor=0.0, restart_seed=1,
                         params=FAST)
    assert not rep.passed


def test_plateau_base_matches_walk_cache_under_segment():
    """Grid-restriction lockstep: plateau_screen's base F̂ (cache-reused from the walk)
    and its fresh neighbor evals must be on the same segment-grid scale."""
    streams = toy_universe()
    seg = (0, 2000 * 60 * NS)
    res = run_restart(streams, CFG, budget=80, restart_id=1, params=FAST, segment=seg, skip_economics_precondition=True)
    rep = plateau_screen(res.best_subset, streams, CFG, threshold=0.0, f_floor=-1e9,
                         restart_seed=1, params=FAST, segment=seg, cache=res.cache)
    assert rep.F_hat == pytest.approx(res.best_F_hat)


# --------------------------------------------------------------------------- #
# Dispersion + fold ranking
# --------------------------------------------------------------------------- #
def test_dispersion_report_shapes():
    streams = toy_universe()
    finalists = [run_restart(streams, CFG, budget=60, restart_id=i, params=FAST, skip_economics_precondition=True)
                 for i in (1, 2, 3)]
    d = dispersion_report(finalists)
    assert d["n_restarts"] == 3
    assert d["F_hat"]["min"] <= d["F_hat"]["median"] <= d["F_hat"]["max"]
    assert d["hamming"]["max"] >= d["hamming"]["min"] >= 0


def test_rank_on_folds_prefers_real_edge():
    streams = toy_universe()
    n_bars_ns = 4000 * 60 * NS
    folds = contiguous_purged_folds(0, n_bars_ns, n_folds=3, purge_ns=60 * 60 * NS)
    good = frozenset({"win0", "win1", "win2"})
    bad = frozenset({"lose0", "lose1", "lose2"})
    ranked, diag = rank_on_folds([(good, 1.0), (bad, 0.5)], streams, CFG, folds)
    assert ranked[0].subset == good
    assert ranked[0].median_F > ranked[-1].median_F
    assert diag["n_folds"] == 3
    assert 0.0 <= diag["pbo_like"] <= 1.0


# --------------------------------------------------------------------------- #
# End-to-end selection stage
# --------------------------------------------------------------------------- #
def test_certify_and_rank_toy_universe():
    streams = toy_universe()
    finalists = [run_restart(streams, CFG, budget=200, restart_id=i, params=FAST, skip_economics_precondition=True)
                 for i in (1, 2)]
    n_bars_ns = 4000 * 60 * NS
    folds = contiguous_purged_folds(0, n_bars_ns, n_folds=3, purge_ns=60 * 60 * NS)
    out = certify_and_rank(finalists, streams, CFG, plateau_threshold=0.3, f_floor=0.0, folds=folds,
                           params=FAST, include_random_ref=False)
    assert out["n_shortlisted"] >= 1
    assert out["ranked"], "shortlist candidates must be ranked"
    assert out["evaluation_count"] > 0
    assert out["score_kind"] == "g_gross"
    # the top-ranked portfolio contains planted winners, not losers
    top = out["ranked"][0].subset
    assert top & {"win0", "win1", "win2"}
    assert len(top & {f"lose{i}" for i in range(5)}) <= 1


def test_noise_only_universe_still_builds_evidence_package():
    """INFR-009: zero-edge terminals still enter the evidence package (no F_floor gate).

    Absolute-F cliff certification is retired; noise is diagnosed via fold scores /
    random-subset reference, not by emptying the shortlist.
    """
    streams = [make_stream(f"n{i}", 0.0, seed=50 + i) for i in range(6)]
    finalists = [run_restart(streams, CFG, budget=120, restart_id=i, params=FAST, skip_economics_precondition=True)
                 for i in (1, 2)]
    n_bars_ns = 4000 * 60 * NS
    folds = contiguous_purged_folds(0, n_bars_ns, n_folds=3, purge_ns=60 * 60 * NS)
    out = certify_and_rank(finalists, streams, CFG, plateau_threshold=0.5, f_floor=0.0,
                           folds=folds, params=FAST, include_random_ref=False)
    assert out["n_shortlisted"] >= 1
    assert out["package_kind"] == "evidence_package"
    assert "F_floor" in out["retired_binders"]
    assert out["keystones"] is not None


# --------------------------------------------------------------------------- #
# Registry enforcement (review F01) + resim-divergence evidence (F04)
# --------------------------------------------------------------------------- #
def test_certify_registry_binding_and_resim_divergence(tmp_path):
    from xen.xena.calibration import SegmentLayout, freeze_registry
    streams = toy_universe()
    layout = SegmentLayout.from_span(0, 4000 * 60 * NS)
    finalists = [run_restart(streams, CFG, budget=200, restart_id=r + 1, params=FAST,
                             segment=layout.search, skip_economics_precondition=True) for r in range(2)]
    folds = contiguous_purged_folds(*layout.ranking, n_folds=2, purge_ns=60 * 60 * NS)
    reg = tmp_path / "frozen.json"
    freeze_registry(params=FAST, plateau_threshold=0.3, f_floor=0.0,
                    gate_pass_threshold=0.0, layout=layout, battery_summary={},
                    out_path=reg, operator_signoff="JI")
    # INFR-009: retired F_floor/plateau drift is recorded, not hard-raised
    drifted = certify_and_rank(finalists, streams, CFG, plateau_threshold=0.9, f_floor=0.0,
                               folds=folds, params=FAST, search_segment=layout.search,
                               registry_path=str(reg), include_random_ref=False)
    assert drifted["retired_threshold_drift"] is not None
    assert drifted["retired_threshold_drift"]["binding"] is False
    assert drifted["retired_threshold_drift"]["plateau_threshold_arg"] == 0.9
    # SearchParams pin still enforced
    from dataclasses import replace
    bad_params = replace(FAST, L=FAST.L + 1)
    with pytest.raises(ValueError, match="SearchParams"):
        certify_and_rank(finalists, streams, CFG, plateau_threshold=0.3, f_floor=0.0,
                         folds=folds, params=bad_params, search_segment=layout.search,
                         registry_path=str(reg), include_random_ref=False)
    out = certify_and_rank(finalists, streams, CFG, plateau_threshold=0.3, f_floor=0.0,
                           folds=folds, params=FAST, search_segment=layout.search,
                           registry_path=str(reg), include_random_ref=False)
    import json  # noqa: PLC0415
    assert out["registry_sha256"] == json.loads(reg.read_text())["sha256"]
    assert out["retired_threshold_drift"] is None  # matches pin
    # resim rows are evidence only (retired binder)
    assert len(out["resim_divergence"]) == len(out["ranked"])
    for row in out["resim_divergence"]:
        assert row.get("binding") is False
        assert "search_band_boot_p25" in row and "fold_worst_F" in row
