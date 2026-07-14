"""INFR-009 P3c freeze-grade-n confirm — same procedure as P3b, n_null=200.

Resolution of low e2e residual (7.5% @ n=40 underpowered). No procedure change.
Disjoint seeds from P3 and P3b. Predeclaration: design.md §P3c.
"""
from __future__ import annotations

from typing import Any

import numpy as np

import xen.xena.calibration_p3b as p3b
from xen.xena.calibration_p3b import ScaleSpec

ALPHA = 0.05

# Disjoint from P3 (1000/2000) and P3b (11000/12000)
SEED_BASE_LOW = 21_000
SEED_BASE_HIGH = 22_000

# Design-power: SE at p=0.05 ≈ 0.218/√n ≤ 1.5% → n≥≈211; predeclared n=200 (SE≈1.54%)
FREEZE_GRADE = ScaleSpec(
    name="freeze_grade",
    n_null=200,
    n_cand=64,
    budget=200,
    n_restarts=5,
    n_power=8,
    n_coverage=200,
)

P3B_SELECTED_L = 40  # baseline for drift flag only


def binomial_se(p_hat: float, n: int) -> float:
    if n <= 0:
        return float("nan")
    p = min(max(p_hat, 0.0), 1.0)
    return float(np.sqrt(p * (1.0 - p) / n))


def wilson_interval(k: int, n: int, *, z: float = 1.96) -> tuple[float, float]:
    """Two-sided Wilson score interval (disclosure). Not the pass bar."""
    if n <= 0:
        return float("nan"), float("nan")
    phat = k / n
    denom = 1.0 + z * z / n
    centre = (phat + z * z / (2 * n)) / denom
    margin = (z / denom) * np.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n))
    return float(max(0.0, centre - margin)), float(min(1.0, centre + margin))


def enrich_alpha_disclosure(alpha_block: dict[str, Any]) -> dict[str, Any]:
    """Add SE + Wilson to an end_to_end_alpha summary (disclosure only)."""
    out = dict(alpha_block)
    n = int(out.get("n_in_domain") or out.get("n") or 0)
    k = int(out.get("n_gross_lcb_positive") or 0)
    phat = float(out.get("alpha_hat") or (k / n if n else float("nan")))
    lo, hi = wilson_interval(k, n)
    out["alpha_se"] = binomial_se(phat, n)
    out["alpha_wilson_95"] = {"low": lo, "high": hi}
    out["alpha_disclosure_only"] = True
    out["gate_rule"] = "point alpha_hat <= 0.05 (Wilson/SE not binding)"
    # design-power check at predeclared n
    out["design_power_se_at_p05"] = binomial_se(0.05, n)
    out["design_power_se_target"] = 0.015
    return out


def run_p3c_calibration(*, purge_mult: int = 1) -> dict[str, Any]:
    """Single freeze-grade-n run. Mutates p3b seed bases for this process only."""
    # Hold P3b procedure; swap only seeds + n
    p3b.SEED_BASE_LOW = SEED_BASE_LOW
    p3b.SEED_BASE_HIGH = SEED_BASE_HIGH

    print(f"[P3c] freeze-grade n_null={FREEZE_GRADE.n_null} "
          f"cand={FREEZE_GRADE.n_cand} budget={FREEZE_GRADE.budget} "
          f"seeds={SEED_BASE_LOW}/{SEED_BASE_HIGH}", flush=True)

    scale_out = p3b.run_scale(FREEZE_GRADE, purge_mult=purge_mult)

    # Enrich α blocks with Wilson/SE disclosure
    scale_out["alpha_low"] = enrich_alpha_disclosure(scale_out["alpha_low"])
    scale_out["alpha_high"] = enrich_alpha_disclosure(scale_out["alpha_high"])

    selected_L = scale_out.get("selected_block")
    L_drift = (selected_L is not None and int(selected_L) != P3B_SELECTED_L)

    stop = dict(scale_out["stop_condition"])
    # Rebuild stop from enriched α + coverage (same logic, explicit gate text)
    cov_fail = bool(scale_out["block_A3_selection"].get("coverage_stop_fail"))
    a_low = scale_out["alpha_low"]
    a_high = scale_out["alpha_high"]
    alpha_low_fail = float(a_low["alpha_hat"]) > ALPHA or not a_low.get("pass_stop")
    alpha_high_fail = float(a_high["alpha_hat"]) > ALPHA or not a_high.get("pass_stop")
    # pass_stop already encodes point ≤ α among in-domain; keep consistent
    alpha_low_fail = not bool(a_low.get("pass_stop"))
    alpha_high_fail = not bool(a_high.get("pass_stop"))
    hard_stop = cov_fail or alpha_low_fail or alpha_high_fail

    stop.update({
        "coverage_fail": cov_fail,
        "alpha_low_fail": alpha_low_fail,
        "alpha_high_fail": alpha_high_fail,
        "STOP": hard_stop,
        "verdict": "STOP" if hard_stop else "PROCEED_TO_P4_ELIGIBLE",
        "selected_block": selected_L,
        "L_drift_from_p3b_40": L_drift,
        "p3b_selected_L": P3B_SELECTED_L,
        "n_null_per_cadence": FREEZE_GRADE.n_null,
        "design_power_se_target": 0.015,
        "gate_rule": (
            "PASS iff point alpha_hat<=5% both cadences AND no-search coverage<=5% "
            "both at selected L; Wilson/SE disclosure only"
        ),
        "escalation_if_stop": [
            "1 calendar/regime-scaled purge (recommend; not implemented in P3c)",
            "2 B2 distant/regime-shifted low-cadence TEST",
            "3 B3 selection-aware correction (last resort)",
        ],
        "note": (
            "If STOP: do not freeze, do not soften α, do not implement escalation in P3c — "
            "recommend rung 1. If PASS: recommend P4 (operator mandate still required)."
        ),
    })

    return {
        "schema": "xena.infr009.p3c_cal.v1",
        "predeclared": {
            "alpha": ALPHA,
            "lcb_confidence": 0.95,
            "method": "studentized_bootstrap_t",
            "purge_mult_H": purge_mult,
            "n_null_per_cadence": FREEZE_GRADE.n_null,
            "design_power_rule": "n such that SE(p=0.05)≈0.218/sqrt(n) ≤ 1.5% → n=200",
            "seed_bases": {"low": SEED_BASE_LOW, "high": SEED_BASE_HIGH},
            "disjoint_from": {"P3": [1000, 2000], "P3b": [11000, 12000]},
            "within_universe": {
                "n_cand": FREEZE_GRADE.n_cand,
                "budget": FREEZE_GRADE.budget,
                "n_restarts": FREEZE_GRADE.n_restarts,
            },
            "L_rule": "P3b joint L-selection on this bank (not blind-pin 40)",
            "gate": "point alpha_hat <= 5% both + coverage <=5% both at selected L",
            "wilson_se": "disclosure only",
            "procedure_change": False,
        },
        "freeze_grade": scale_out,
        "stop_condition": stop,
        "L_selection": {
            "selected_block": selected_L,
            "ok_blocks": scale_out["block_A3_selection"].get("ok_blocks"),
            "coverage_stop_fail": cov_fail,
            "drift_from_p3b_40": L_drift,
            "p3b_selected_L": P3B_SELECTED_L,
            "sweeps_summary": scale_out["block_A3_selection"].get("sweeps"),
        },
    }
