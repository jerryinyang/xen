"""Tests for xen.xena.certify (INFR-006 WS-4) — keystone detection, cliff-screen pass on
genuine plateaus, noise-only rejection, fold ranking, dispersion diagnostics."""
from __future__ import annotations

import numpy as np
import pytest

from xen.xena.certify import (certify_and_rank, contiguous_purged_folds,
                              dispersion_report, plateau_screen, rank_on_folds)
from xen.xena.oracle import OracleConfig
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
    assert rep.keystone is None
    assert rep.min_drop_ratio >= 0.5


def test_f_floor_blocks_tiny_objective():
    """Finding 3: near-zero F̂ is ratio-unstable; a pre-registered floor blocks it."""
    streams = [make_stream(f"win{i}", +40.0, seed=i) for i in range(6)]
    subset = frozenset(s.candidate_id for s in streams)
    rep = plateau_screen(subset, streams, CFG, threshold=0.5, f_floor=1e9,
                         restart_seed=1, params=FAST)
    assert not rep.passed
    assert np.isnan(rep.min_drop_ratio)


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
    res = run_restart(streams, CFG, budget=80, restart_id=1, params=FAST, segment=seg)
    rep = plateau_screen(res.best_subset, streams, CFG, threshold=0.0, f_floor=-1e9,
                         restart_seed=1, params=FAST, segment=seg, cache=res.cache)
    assert rep.F_hat == pytest.approx(res.best_F_hat)


# --------------------------------------------------------------------------- #
# Dispersion + fold ranking
# --------------------------------------------------------------------------- #
def test_dispersion_report_shapes():
    streams = toy_universe()
    finalists = [run_restart(streams, CFG, budget=60, restart_id=i, params=FAST)
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
    finalists = [run_restart(streams, CFG, budget=200, restart_id=i, params=FAST)
                 for i in (1, 2)]
    n_bars_ns = 4000 * 60 * NS
    folds = contiguous_purged_folds(0, n_bars_ns, n_folds=3, purge_ns=60 * 60 * NS)
    out = certify_and_rank(finalists, streams, CFG, plateau_threshold=0.3, f_floor=0.0, folds=folds,
                           params=FAST)
    assert out["n_certified"] >= 1
    assert out["ranked"], "certified candidates must be ranked"
    assert out["evaluation_count"] > 0
    # the top-ranked portfolio contains planted winners, not losers
    top = out["ranked"][0].subset
    assert top & {"win0", "win1", "win2"}
    assert len(top & {f"lose{i}" for i in range(5)}) <= 1


def test_noise_only_universe_certifies_nothing():
    """Zero-edge universe: the selection stage must not certify (F̂ ≤ 0 or cliff-fail)."""
    streams = [make_stream(f"n{i}", 0.0, seed=50 + i) for i in range(6)]
    finalists = [run_restart(streams, CFG, budget=120, restart_id=i, params=FAST)
                 for i in (1, 2)]
    n_bars_ns = 4000 * 60 * NS
    folds = contiguous_purged_folds(0, n_bars_ns, n_folds=3, purge_ns=60 * 60 * NS)
    out = certify_and_rank(finalists, streams, CFG, plateau_threshold=0.5, f_floor=0.0, folds=folds,
                           params=FAST)
    assert out["n_certified"] == 0
    assert out["keystones"] is not None  # attribution recorded for failures


# --------------------------------------------------------------------------- #
# Registry enforcement (review F01) + resim-divergence evidence (F04)
# --------------------------------------------------------------------------- #
def test_certify_registry_binding_and_resim_divergence(tmp_path):
    from xen.xena.calibration import SegmentLayout, freeze_registry
    streams = toy_universe()
    layout = SegmentLayout.from_span(0, 4000 * 60 * NS)
    finalists = [run_restart(streams, CFG, budget=200, restart_id=r + 1, params=FAST,
                             segment=layout.search) for r in range(2)]
    folds = contiguous_purged_folds(*layout.ranking, n_folds=2, purge_ns=60 * 60 * NS)
    reg = tmp_path / "frozen.json"
    freeze_registry(params=FAST, plateau_threshold=0.3, f_floor=0.0,
                    gate_pass_threshold=0.0, layout=layout, battery_summary={},
                    out_path=reg, operator_signoff="JI")
    # drifted threshold vs pin refuses
    with pytest.raises(ValueError, match="never re-derived"):
        certify_and_rank(finalists, streams, CFG, plateau_threshold=0.9, f_floor=0.0,
                         folds=folds, params=FAST, search_segment=layout.search,
                         registry_path=str(reg))
    out = certify_and_rank(finalists, streams, CFG, plateau_threshold=0.3, f_floor=0.0,
                           folds=folds, params=FAST, search_segment=layout.search,
                           registry_path=str(reg))
    import json  # noqa: PLC0415
    assert out["registry_sha256"] == json.loads(reg.read_text())["sha256"]
    # F04: one divergence row per certified+ranked finalist, evidence fields present
    assert len(out["resim_divergence"]) == len(out["ranked"])
    for row in out["resim_divergence"]:
        assert 0.0 <= row["frac_folds_below_search_p25"] <= 1.0
        assert "search_band_boot_p25" in row and "fold_worst_F" in row
