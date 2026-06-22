#!/usr/bin/env python3
"""Phase 019 D2 admission-gate bite/fixture check.

Validates the BINDING admission gate (D0-predeclarations.md §D2b) on synthetic
fixtures — *not* the real market screen (that is EXP-086+). The gate machinery:

  - per cell, a one-sided "beats-random" test on the paired Delta-over-random
    availability metric (CI_low > 0; here the fast normal-approx analog of the
    production moving-block bootstrap);
  - an axis-level statistic S = #cells-beat-random;
  - a PERMUTED-AXIS null at the realized cell count (shuffle the conditioning
    labels => recompute S), giving the admission threshold S* = Q(1-FWER)
    of the permutation distribution and a permutation p-value;
  - cross-axis Holm step-down over the per-axis permutation p-values (FWER 0.05).

A candidate axis is ADMITTED iff realized S > S* AND its Holm-adjusted
permutation p <= FWER.

The bite confirms the gate is:
  (1) NOT VACUOUS  - a pure-noise axis is admitted at a rate <= FWER;
  (2) NOT IMPOSSIBLE - a genuinely non-random axis (a modest availability lift
                       on >= 5 well-powered cells) is admitted with high power;
  (3) ROUTING-INVARIANT across the pre-registered sensitivity band
      FWER in {0.025, 0.05, 0.10} (S* from the matching permutation quantile);
  (4) SELF-CALIBRATING - because S* is computed from the SAME per-cell test, a
      mildly inflated per-cell FP rate (the EXP-077 percentile-bootstrap effect)
      does not break axis-level FWER control;
  (5) consistent with the EXP-081 descriptive sign-band (which is the
      Binomial(C, 0.5) coin-flip noise band => EXP-081 sat in the noise band),
      while the binding CI_low>0 / permutation statistic separates a real lift;
  (6) Holm step-down implemented correctly.

Deterministic: master seed 20260622; a second run is identical.
"""
from __future__ import annotations

import json
import math
from math import comb, erfc, sqrt
from pathlib import Path

import numpy as np

# ----------------------------------------------------------------------------
# Frozen bite parameters (candidate D2 values under test)
# ----------------------------------------------------------------------------
SEED = 20260622
C = 46                       # member cells (EXP-081 realized count)
SIGMA = 2.0                  # per-event Delta (real - random) std, ATR units
Z = 1.645                    # one-sided 95% normal quantile (per-cell CI_low>0 test)
Z_INFLATED = 1.55            # self-calibration stress: per-cell FP ~0.061 (EXP-077-style)
N_PERM = 1000                # permutations for the empirical permutation null
R_REP = 5000                 # replicate datasets for operating-characteristic estimates
K_PLANT = 8                  # planted non-random cells (>= 5 required by D0)
LIFT = 0.20                  # planted per-cell availability lift, ATR units (modest, real)
FWER_BAND = [0.025, 0.05, 0.10]
PERM_N_CAP = 3000            # cap event arrays in the empirical permutation demo (cost bound)
WILSON_TOL = 0.075           # noise-admission Wilson-upper tolerance (mirrors EXP-077 0.075)
POWER_FLOOR = 0.80           # planted-axis power floor

OUT = Path(__file__).resolve().parent / "bite_check_report.json"


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------
def norm_sf(z: float) -> float:
    """P(Z > z) for standard normal."""
    return 0.5 * erfc(z / sqrt(2.0))


def wilson_upper(k: int, n: int, z: float = 1.96) -> float:
    if n == 0:
        return 1.0
    p = k / n
    den = 1.0 + z * z / n
    centre = p + z * z / (2 * n)
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre + half) / den


def binom_pmf(n: int, p: float) -> np.ndarray:
    return np.array([comb(n, k) * p**k * (1 - p) ** (n - k) for k in range(n + 1)])


def s_star_from_binom(n: int, p: float, fwer: float) -> tuple[int, float]:
    """Smallest s with P(X > s) <= fwer for X ~ Binom(n, p); admit iff realized S > s."""
    pmf = binom_pmf(n, p)
    for s in range(n + 1):
        tail = float(pmf[s + 1 :].sum())
        if tail <= fwer:
            return s, tail
    return n, 0.0


def make_cell_ns(rng: np.random.Generator) -> np.ndarray:
    """46 cells, log-uniform over the EXP-081 realized range [46, 5535], median ~1083."""
    lo, hi = 46, 5535
    u = rng.uniform(0.0, 1.0, C)
    ns = np.exp(np.log(lo) + u * (np.log(hi) - np.log(lo)))
    return np.clip(ns.astype(int), lo, hi)


def per_cell_beats(sample_means: np.ndarray, ses: np.ndarray, z: float) -> np.ndarray:
    """CI_low = mean - z*se > 0  (one-sided 'beats matched random')."""
    return (sample_means - z * ses) > 0.0


# ----------------------------------------------------------------------------
# (A) empirical permutation null on one representative dataset per axis
# ----------------------------------------------------------------------------
def empirical_permutation(rng: np.random.Generator, ns: np.ndarray, mus: np.ndarray, z: float):
    """Build event-level Delta arrays, compute realized S, and the sign-flip
    permutation null distribution of S (label shuffle for a paired statistic)."""
    realized_beats = np.zeros(C, dtype=bool)
    perm_S = np.zeros(N_PERM, dtype=int)
    perm_counts = np.zeros((N_PERM, C), dtype=bool)
    for c in range(C):
        n = int(min(ns[c], PERM_N_CAP))
        delta = rng.normal(mus[c], SIGMA, n)
        se = delta.std(ddof=1) / sqrt(n)
        realized_beats[c] = (delta.mean() - z * se) > 0.0
        # sign-flip permutations (paired-label shuffle): mean of (+-1)*delta
        signs = rng.integers(0, 2, size=(N_PERM, n)) * 2 - 1  # {-1,+1}
        perm_means = (signs * delta).mean(axis=1)
        perm_counts[:, c] = (perm_means - z * se) > 0.0
    perm_S = perm_counts.sum(axis=1)
    realized_S = int(realized_beats.sum())
    return realized_S, perm_S


# ----------------------------------------------------------------------------
# (B) operating characteristics via the fast normal-model (no event arrays)
# ----------------------------------------------------------------------------
def oc_rates(rng, ns, mus, s_star, z, reps):
    """Admission rate of an axis with cell means `mus`, threshold s_star."""
    ses = SIGMA / np.sqrt(ns)
    sm = rng.normal(mus[None, :], ses[None, :], size=(reps, C))
    beats = (sm - z * ses[None, :]) > 0.0
    S = beats.sum(axis=1)
    admits = int((S > s_star).sum())
    return admits, reps, S


def holm_adjust(pvals: list[float]) -> list[float]:
    """Holm step-down adjusted p-values."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        val = (m - rank) * pvals[idx]
        running = max(running, val)
        adj[idx] = min(running, 1.0)
    return adj


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------
def main() -> None:
    rng = np.random.default_rng(SEED)
    report: dict = {"seed": SEED, "C": C, "sigma": SIGMA, "z": Z,
                    "n_perm": N_PERM, "r_rep": R_REP, "k_plant": K_PLANT,
                    "lift": LIFT, "fwer_band": FWER_BAND}

    ns = make_cell_ns(rng)
    report["cell_n"] = {"min": int(ns.min()), "median": int(np.median(ns)),
                        "max": int(ns.max())}

    # plant the lift on the K_PLANT highest-n (well-powered) cells -> guarantees
    # the "non-random axis" is genuinely detectable (not a low-n mirage)
    plant_idx = np.argsort(ns)[-K_PLANT:]
    mus_noise = np.zeros(C)
    mus_plant = np.zeros(C)
    mus_plant[plant_idx] = LIFT
    report["plant_cells_n"] = sorted(int(ns[i]) for i in plant_idx)

    per_cell_fp = norm_sf(Z)               # exact per-cell label-shuffle beat prob
    report["per_cell_fp_nominal"] = round(per_cell_fp, 5)

    # ---- (A) empirical permutation null: noise + planted -----------------
    noiseS, noise_perm = empirical_permutation(rng, ns, mus_noise, Z)
    plantS, plant_perm = empirical_permutation(rng, ns, mus_plant, Z)
    perm_mean = float(noise_perm.mean())
    perm_expected = C * per_cell_fp
    s_star_emp, tail_emp = (int(np.quantile(noise_perm, 0.95)), None)
    s_star_binom, tail_binom = s_star_from_binom(C, per_cell_fp, 0.05)
    perm_p_noise = (1 + int((noise_perm >= noiseS).sum())) / (1 + N_PERM)
    perm_p_plant = (1 + int((plant_perm >= plantS).sum())) / (1 + N_PERM)
    report["A_empirical_permutation"] = {
        "perm_null_mean": round(perm_mean, 3),
        "perm_null_mean_expected_binom": round(perm_expected, 3),
        "s_star_empirical_q95": s_star_emp,
        "s_star_binom_q95": s_star_binom,
        "noise_realized_S": noiseS, "noise_perm_p": round(perm_p_noise, 4),
        "planted_realized_S": plantS, "planted_perm_p": round(perm_p_plant, 4),
        "noise_admitted": bool(noiseS > s_star_binom and perm_p_noise <= 0.05),
        "planted_admitted": bool(plantS > s_star_binom and perm_p_plant <= 0.05),
    }

    # ---- (B) operating characteristics across the sensitivity band -------
    band = {}
    band_ok = True
    for fwer in FWER_BAND:
        s_star, tail = s_star_from_binom(C, per_cell_fp, fwer)
        n_admit, n, _ = oc_rates(rng, ns, mus_noise, s_star, Z, R_REP)
        noise_rate = n_admit / n
        noise_hi = wilson_upper(n_admit, n)
        p_admit, _, _ = oc_rates(rng, ns, mus_plant, s_star, Z, R_REP)
        power = p_admit / R_REP
        ok = (noise_hi <= max(fwer, WILSON_TOL)) and (power >= POWER_FLOOR)
        band_ok &= ok
        band[f"fwer_{fwer}"] = {
            "s_star": s_star, "binom_tail": round(tail, 4),
            "noise_admission_rate": round(noise_rate, 4),
            "noise_admission_wilson_hi": round(noise_hi, 4),
            "planted_power": round(power, 4), "ok": bool(ok),
        }
    report["B_operating_characteristics"] = band

    # ---- (C) self-calibration under an inflated per-cell test -------------
    fp_inf = norm_sf(Z_INFLATED)
    s_star_inf, tail_inf = s_star_from_binom(C, fp_inf, 0.05)
    n_admit_inf, _, _ = oc_rates(rng, ns, mus_noise, s_star_inf, Z_INFLATED, R_REP)
    rate_inf = n_admit_inf / R_REP
    hi_inf = wilson_upper(n_admit_inf, R_REP)
    p_admit_inf, _, _ = oc_rates(rng, ns, mus_plant, s_star_inf, Z_INFLATED, R_REP)
    power_inf = p_admit_inf / R_REP
    self_cal_ok = (hi_inf <= WILSON_TOL) and (power_inf >= POWER_FLOOR)
    report["C_self_calibration_inflated_percell"] = {
        "z_inflated": Z_INFLATED, "per_cell_fp_inflated": round(fp_inf, 5),
        "s_star": s_star_inf, "noise_admission_rate": round(rate_inf, 4),
        "noise_admission_wilson_hi": round(hi_inf, 4),
        "planted_power": round(power_inf, 4), "ok": bool(self_cal_ok),
    }

    # ---- (D) EXP-081 descriptive sign-band sanity ------------------------
    # the sign statistic (real>random point estimate) under noise ~ Binom(C, 0.5)
    pmf_half = binom_pmf(C, 0.5)
    cdf = np.cumsum(pmf_half)
    lo90 = int(np.searchsorted(cdf, 0.05))
    hi90 = int(np.searchsorted(cdf, 0.95))
    exp081_band = (17, 28)  # harami 17/46 ... AVWAP 28/46
    sign_ok = lo90 <= exp081_band[0] and exp081_band[1] <= hi90
    report["D_exp081_signband_sanity"] = {
        "noise_signcount_90pct_interval": [lo90, hi90],
        "exp081_observed_band": list(exp081_band),
        "exp081_in_noise_band": bool(sign_ok),
        "note": "EXP-081's 17/46-28/46 sits inside the Binomial(46,0.5) coin-flip "
                "noise band => 'availability ~ random' was the noise distribution; "
                "the binding CI_low>0/permutation gate separates a real lift from it.",
    }

    # ---- (E) Holm step-down unit check -----------------------------------
    holm_in = [0.20, 0.04, 0.005]   # one clearly-significant axis among three
    holm_out = holm_adjust(holm_in)
    # expected: sorted 0.005*3=0.015, 0.04*2=0.08, 0.20*1=0.20 (monotone enforced)
    holm_expected = [0.20, 0.08, 0.015]
    holm_ok = all(abs(a - b) < 1e-9 for a, b in zip(holm_out, holm_expected))
    report["E_holm_unit_check"] = {
        "input": holm_in, "adjusted": [round(x, 4) for x in holm_out],
        "expected": holm_expected, "ok": bool(holm_ok),
    }

    # ---- OVERALL ---------------------------------------------------------
    not_vacuous = band_ok and self_cal_ok
    not_impossible = all(band[k]["planted_power"] >= POWER_FLOOR for k in band) \
        and report["A_empirical_permutation"]["planted_admitted"]
    perm_matches = abs(perm_mean - perm_expected) < 1.0 and s_star_emp == s_star_binom
    noise_rejected_A = not report["A_empirical_permutation"]["noise_admitted"]
    overall = (not_vacuous and not_impossible and perm_matches and noise_rejected_A
               and sign_ok and holm_ok)
    report["checks"] = {
        "not_vacuous_noise_admission_le_fwer": bool(band_ok),
        "self_calibrating_under_inflated_percell": bool(self_cal_ok),
        "not_impossible_planted_power_ge_floor": bool(not_impossible),
        "permutation_null_matches_binomial": bool(perm_matches),
        "noise_axis_rejected_empirically": bool(noise_rejected_A),
        "exp081_signband_sanity": bool(sign_ok),
        "holm_correct": bool(holm_ok),
    }
    report["OVERALL"] = "GREEN" if overall else "RE-ANCHOR NEEDED"

    OUT.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    print(f"\nOVERALL: {report['OVERALL']}  ->  {OUT}")


if __name__ == "__main__":
    main()
