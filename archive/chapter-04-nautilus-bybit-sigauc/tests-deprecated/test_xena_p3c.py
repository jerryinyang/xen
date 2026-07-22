"""INFR-009 P3c unit tests — freeze-grade-n config, Wilson disclosure, disjoint seeds."""
from __future__ import annotations

from xen.xena.calibration_p3c import (FREEZE_GRADE, SEED_BASE_HIGH, SEED_BASE_LOW,
                                      binomial_se, enrich_alpha_disclosure,
                                      wilson_interval)


def test_n_design_power():
    # n=200 → SE at p=0.05 ≈ 1.54% (target ≤1.5% design intent)
    se = binomial_se(0.05, FREEZE_GRADE.n_null)
    assert FREEZE_GRADE.n_null == 200
    assert se < 0.016  # ~1.54%


def test_seeds_disjoint():
    assert SEED_BASE_LOW >= 21_000
    assert SEED_BASE_HIGH >= 22_000
    assert SEED_BASE_LOW != 11_000 and SEED_BASE_HIGH != 12_000


def test_wilson_and_enrich():
    lo, hi = wilson_interval(3, 40)
    assert 0.0 <= lo < 0.075 < hi <= 1.0
    block = enrich_alpha_disclosure({
        "n": 40, "n_in_domain": 40, "n_gross_lcb_positive": 3, "alpha_hat": 0.075,
        "pass_stop": False,
    })
    assert block["alpha_disclosure_only"] is True
    assert "alpha_wilson_95" in block
    assert block["alpha_se"] > 0


def test_production_within_universe_held():
    assert FREEZE_GRADE.n_cand == 64
    assert FREEZE_GRADE.budget == 200
    assert FREEZE_GRADE.n_restarts == 5
