"""SPDR-015 CONTROL LABEL-SHUFFLE — L-28 derangement collapse (design §4).

Fixes QA-run-1 Issue 1: the artifact claimed `destroy_form: DERANGEMENT` while the code path
used a plain `rng.shuffle` (≈1 expected fixed point, no rejection) on the 2b arm only, single
seed, no bite plant. This module supplies a truthful, reusable collapse read used by BOTH arms:

* zero-fixed-point index derangement via canonical `xen.xena.controls.make_derangement` (L-28),
  asserted per seed;
* a seed battery (design `DERANGE_SEEDS`, 200 seeds) read as a percentile, not a single draw (L-19);
* a synthetic +bite hit-rate plant (design §4 `bite/MDE`) proving the control detects a small
  real edge (non-vacuity).

Metrics are forecast-skill Brier only (no accounting primitive). Informative tier.
"""
from __future__ import annotations

import numpy as np

from xen.xena.controls import make_derangement


def _brier(y: np.ndarray, p: np.ndarray) -> float:
    """Brier score on finite/label-valid rows (leaf copy — avoids a transitions↔controls cycle)."""
    m = np.isfinite(p) & (y >= 0)
    if m.sum() < 1:
        return float("nan")
    return float(np.mean((p[m] - y[m].astype(float)) ** 2))


def _bite_plant_probs(y: np.ndarray, bite: float, rng: np.random.Generator) -> np.ndarray:
    """Synthetic predictor carrying a genuine +`bite` hit-rate edge over the majority-class base.

    Correct-side probability 0.9 with prob (majority_hit + bite), else wrong-side 0.1. Used to
    show the derangement test can SEE a small real edge (design §4 non-vacuity / MDE).
    """
    base = float(np.mean(y)) if y.size else float("nan")
    majority_hit = max(base, 1.0 - base)
    target_hit = min(0.99, majority_hit + bite)
    correct = rng.random(y.size) < target_hit
    return np.where(correct,
                    np.where(y == 1, 0.9, 0.1),
                    np.where(y == 1, 0.1, 0.9)).astype(float)


def label_derange_collapse(
    y: np.ndarray,
    p: np.ndarray,
    seeds,
    *,
    bite: float = 0.05,
) -> dict:
    """Derange the target labels (index permutation, zero fixed points) → Brier collapse.

    Returns numbers only (no raw arrays) so callers may store per-cell rows cheaply.

    Live skill (if real) should worsen under derangement: deranged Brier ↑ toward base variance,
    and few/no deranged draws beat the live Brier (`collapse_frac` ≈ 0). The bite plant confirms
    the test's power: a +`bite` planted edge is almost never beaten by a deranged draw.
    """
    m = np.isfinite(p) & (y >= 0)
    y = y[m].astype(np.int64)
    p = p[m].astype(float)
    n = int(y.size)
    if n < 30:
        return {"n": n, "powered": False, "note": "n<30"}

    live = _brier(y, p)
    idx = np.arange(n)

    deranged = np.empty(len(seeds))
    zero_fixed = True
    for i, s in enumerate(seeds):
        rng = np.random.default_rng(int(s))
        perm = make_derangement(n, rng)
        if np.any(perm == idx):
            zero_fixed = False
        deranged[i] = _brier(y[perm], p)

    # bite plant: a genuine +bite edge, checked against the same derangement battery
    rng_b = np.random.default_rng(int(seeds[0]) + 900_000)
    p_plant = _bite_plant_probs(y, bite, rng_b)
    live_plant = _brier(y, p_plant)
    plant_deranged = np.empty(len(seeds))
    for i, s in enumerate(seeds):
        rng = np.random.default_rng(int(s) + 500_000)
        perm = make_derangement(n, rng)
        plant_deranged[i] = _brier(y[perm], p_plant)

    return {
        "n": n,
        "powered": True,
        "destroy_form": "DERANGEMENT",
        "derangement_zero_fixed_points": bool(zero_fixed),
        "n_seeds": int(len(seeds)),
        "live_brier": live,
        "deranged_brier_median": float(np.median(deranged)),
        "deranged_brier_p05": float(np.percentile(deranged, 5)),
        "deranged_brier_p95": float(np.percentile(deranged, 95)),
        # fraction of deranged draws at least as good as live (≈0 if live carries real skill)
        "collapse_frac": float(np.mean(deranged <= live)),
        # bite/MDE: planted +bite edge should be detected (rarely beaten by a deranged draw)
        "bite": float(bite),
        "bite_plant_brier": live_plant,
        "bite_detect_frac": float(np.mean(plant_deranged <= live_plant)),
        "bite_detected": bool(np.mean(plant_deranged <= live_plant) < 0.05),
    }
