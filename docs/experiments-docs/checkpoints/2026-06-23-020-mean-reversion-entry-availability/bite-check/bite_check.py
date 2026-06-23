#!/usr/bin/env python3
"""Phase 020 D2b admission-gate bite/fixture check (CF-MR-001, 6 sub-screens).

Precondition for G0. Validates the BINDING admission gate (D0-predeclarations.md
§D2b) on SYNTHETIC fixtures — *not* the real market screen (that is EXP-089). No
market data, no candidate slot, no holdout is touched here.

The gate machinery is the one already bite-checked GREEN for Phase 019
(`…/2026-06-22-019-family-selection-availability-screen/bite-check`) and shipped
as `xen.availability_gate`. The ONLY thing that changed for Phase 020 is the
WITHIN-FAMILY multiplicity: CF-MR-001 carries **six** sub-screens

    {CORE, CORE-VOL-LOW, CORE-VOL-MED, CORE-VOL-HIGH, CORE+TREND, CORE+FILTER}

combined by the **joint max** of the permuted-axis null (`combine_axis`), with
**no cross-axis Holm** (single family). Phase 019 axes carried <=4 sub-screens,
so the leg that must be re-shown is: *the joint max across 6 noise sub-screens
does not inflate the family admission above FWER, and still admits a genuine
single-lever lift with power.*

Checks (all must pass for OVERALL: GREEN):

  (A) REAL-MODULE INTEGRATION (drives `run_sub_screen` -> `combine_axis`
      verbatim, no re-implementation): a pure-noise family of 6 sub-screens is
      NOT admitted; a family with a +LIFT availability lift planted in exactly
      ONE sub-screen IS admitted and the argmax (driving_sub) names the planted
      lever.
  (B) OPERATING CHARACTERISTICS at scale (fast normal-model analog, exactly the
      Phase-019 scaffold): with S* = Q(1-FWER) of the joint max-of-6 null,
        - NOT VACUOUS: noise-family admission rate <= FWER (Wilson-hi <= ~0.075);
        - NOT IMPOSSIBLE: a one-sub-screen planted lift is admitted with
          power >= 0.80 and the planted sub-screen is the argmax;
      across the pre-registered band FWER in {0.025, 0.05, 0.10}.
  (C) JOINT-MAX NECESSITY: using the *single-sub-screen* S* (the wrong
      threshold) the 6-way max inflates family error well above FWER; the joint
      max-of-6 S* corrects it. This is the new-leg demonstration.
  (D) MC STABILITY: the joint S* and the planted perm_p do not flip routing
      between N_PERM 1000 and 5000.

Scope note (D0-amendment-001, 2026-06-23): the leg-2 beats-CORE conjunction and the
regime-membership-shuffle null are RETIRED for CF-MR-001; all 6 sub-screens are
single-test leg-1 through `run_sub_screen`, which this A-D bite already certifies
GREEN (sha f01a000b…). The former leg-2 fixture (Part E) is dropped.

Determinism: master seed 20260623; a second run is byte-identical (verified by
re-running and diffing `bite_check_report.json`).
"""
from __future__ import annotations

import json
import sys
from math import comb, erfc, sqrt
from pathlib import Path

import numpy as np

# Path setup is required before importing the shipped gate (governance script
# living outside the package tree); kept local to this entry module.
_REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(_REPO_ROOT / "python" / "src"))

from xen.availability_gate import (  # noqa: E402
    CellReadInput,
    STAT_MEDIAN,
    combine_axis,
    run_sub_screen,
)

# ----------------------------------------------------------------------------
# Frozen bite parameters (candidate D2b values under test)
# ----------------------------------------------------------------------------
SEED = 20260623
C = 46                       # EXP-080-READY member-cell count
N_SUB = 6                    # CF-MR-001 sub-screens (the only change vs Phase 019)
SUB_NAMES = ["CORE", "CORE-VOL-LOW", "CORE-VOL-MED", "CORE-VOL-HIGH",
             "CORE+TREND", "CORE+FILTER"]
PLANTED_SUB = 5              # plant the lever in CORE+FILTER (index 5) — argmax must find it
SIGMA = 2.0                  # per-event Delta (real - random) std, ATR units (normal model)
Z = 1.645                    # one-sided 95% normal quantile (per-cell CI_low>0 test)
N_PERM = 5000                # production permutations / joint-null draws
N_PERM_STAB = 1000           # MC-stability cross-check scale
R_REP = 5000                 # replicate datasets for operating-characteristic estimates
K_PLANT = 8                  # planted non-random cells (>= 5 required by D0)
LIFT = 0.20                  # planted per-cell availability lift, ATR units (modest, real)
FWER_BAND = [0.025, 0.05, 0.10]
WILSON_TOL = 0.075           # noise-admission Wilson-upper tolerance (mirrors Phase 019)
POWER_FLOOR = 0.80           # planted-family power floor
ARGMAX_FLOOR = 0.90          # min fraction of admitted planted families whose argmax = planted

# Part-A (real-module) cost bounds — one dataset per family, C=46, modest cells.
# Part A is an INTEGRATION smoke test of the shipped module's admit/exonerate/argmax
# routing (not a power measurement — that is Part B at the D0 +0.20/>=5 spec); so it
# plants a DECISIVE lever (strong shift on many high-n cells) for unambiguous routing.
A_N_PERM = 1000
A_POOL = 3000
A_N_LO, A_N_HI = 60, 600     # per-cell event counts (>= floor 30)
A_DELTA = 0.80               # planted cond-vs-ctrl location shift (ATR units), decisive lift
A_K_PLANT = 15               # planted cells in the lever sub-screen (decisive; >> noise S*)
# D2a beats-random noise ceiling for combine_axis disposition labelling: a cell
# "beats random" at false-positive ~0.05, so S noise band = [0, Binom(46,0.05) Q95 = 5].
A_NULL_BAND = (0, 5)

OUT = Path(__file__).resolve().parent / "bite_check_report.json"


# ----------------------------------------------------------------------------
# helpers (Phase-019 scaffold, verbatim)
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


def s_star_from_binom(n: int, p: float, fwer: float) -> int:
    """Smallest s with P(X > s) <= fwer for X ~ Binom(n, p); admit iff S > s."""
    pmf = binom_pmf(n, p)
    for s in range(n + 1):
        if float(pmf[s + 1:].sum()) <= fwer:
            return s
    return n


def make_cell_ns(rng: np.random.Generator) -> np.ndarray:
    """46 cells, log-uniform over the EXP-081 realized range [46, 5535]."""
    lo, hi = 46, 5535
    u = rng.uniform(0.0, 1.0, C)
    ns = np.exp(np.log(lo) + u * (np.log(hi) - np.log(lo)))
    return np.clip(ns.astype(int), lo, hi)


def sim_S(rng: np.random.Generator, ns: np.ndarray, mus: np.ndarray, reps: int) -> np.ndarray:
    """Fast normal-model per-sub-screen S = #cells-beat-random, vectorized over `reps`."""
    ses = SIGMA / np.sqrt(ns)
    sm = rng.normal(mus[None, :], ses[None, :], size=(reps, C))
    return ((sm - Z * ses[None, :]) > 0.0).sum(axis=1)


def family_S(rng: np.random.Generator, ns: np.ndarray,
             mus_per_sub: list[np.ndarray], reps: int) -> np.ndarray:
    """(reps, N_SUB) matrix of per-sub-screen S for a family."""
    out = np.zeros((reps, N_SUB), dtype=np.int64)
    for j in range(N_SUB):
        out[:, j] = sim_S(rng, ns, mus_per_sub[j], reps)
    return out


# ----------------------------------------------------------------------------
# (A) real-module integration — drives the shipped gate verbatim
# ----------------------------------------------------------------------------
def _make_cells(rng: np.random.Generator, planted: bool) -> list[CellReadInput]:
    ns = rng.integers(A_N_LO, A_N_HI + 1, size=C)
    plant_idx = set(np.argsort(ns)[-A_K_PLANT:].tolist()) if planted else set()
    cells: list[CellReadInput] = []
    for i in range(C):
        n = int(ns[i])
        loc = A_DELTA if i in plant_idx else 0.0
        cond = rng.normal(loc, 1.0, n)
        ctrl = rng.normal(0.0, 1.0, n)
        pool = rng.normal(0.0, 1.0, A_POOL)
        cells.append(CellReadInput(cell_id=f"cell-{i:02d}", cond_values=cond,
                                   ctrl_values=ctrl, pool_values=pool,
                                   n_cond=n, underpowered=(n < 30)))
    return cells


def real_module_family(rng: np.random.Generator, planted_sub: int | None):
    """Build 6 sub-screens, run each through the shipped gate, combine by joint max."""
    subs = []
    for j, name in enumerate(SUB_NAMES):
        cells = _make_cells(rng, planted=(planted_sub is not None and j == planted_sub))
        subs.append(run_sub_screen(name, "mfe_med", STAT_MEDIAN, cells, rng, n_perm=A_N_PERM))
    # D2a beats-random noise band (reporting input to combine_axis; admit uses S*/perm_p)
    return combine_axis("CF-MR-001", subs, A_NULL_BAND, n_perm=A_N_PERM)


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------
def main() -> None:
    rng = np.random.default_rng(SEED)
    per_cell_fp = norm_sf(Z)
    report: dict = {
        "phase": "020", "family": "CF-MR-001", "seed": SEED, "C": C,
        "n_sub": N_SUB, "sub_names": SUB_NAMES, "planted_sub": SUB_NAMES[PLANTED_SUB],
        "sigma": SIGMA, "z": Z, "n_perm": N_PERM, "r_rep": R_REP,
        "k_plant": K_PLANT, "lift": LIFT, "fwer_band": FWER_BAND,
        "per_cell_fp_nominal": round(per_cell_fp, 5),
    }

    # ---- (A) real-module integration (shipped availability_gate verbatim) ----
    a_noise = real_module_family(rng, planted_sub=None)
    a_plant = real_module_family(rng, planted_sub=PLANTED_SUB)
    a_noise_admitted = a_noise.disposition.startswith("ADMITTED")
    a_plant_admitted = a_plant.disposition.startswith("ADMITTED")
    a_plant_argmax_ok = a_plant.driving_sub.startswith(SUB_NAMES[PLANTED_SUB])
    report["A_real_module_integration"] = {
        "n_perm": A_N_PERM,
        "noise": {"s_m": a_noise.s_m, "s_star": a_noise.s_star,
                  "perm_p": round(a_noise.perm_p, 4), "driving_sub": a_noise.driving_sub,
                  "disposition": a_noise.disposition, "admitted": bool(a_noise_admitted)},
        "planted": {"s_m": a_plant.s_m, "s_star": a_plant.s_star,
                    "perm_p": round(a_plant.perm_p, 4), "driving_sub": a_plant.driving_sub,
                    "disposition": a_plant.disposition, "admitted": bool(a_plant_admitted),
                    "argmax_is_planted": bool(a_plant_argmax_ok)},
        "ok": bool((not a_noise_admitted) and a_plant_admitted and a_plant_argmax_ok),
    }

    # ---- (B) operating characteristics across the sensitivity band ----------
    ns = make_cell_ns(rng)
    report["cell_n"] = {"min": int(ns.min()), "median": int(np.median(ns)),
                        "max": int(ns.max())}
    mus_noise = [np.zeros(C) for _ in range(N_SUB)]
    mus_plant = [np.zeros(C) for _ in range(N_SUB)]
    plant_idx = np.argsort(ns)[-K_PLANT:]
    mus_plant[PLANTED_SUB][plant_idx] = LIFT
    report["plant_cells_n"] = sorted(int(ns[i]) for i in plant_idx)

    # joint max-of-6 noise null (production scale) -> S*(fwer)
    joint_null = family_S(rng, ns, mus_noise, N_PERM).max(axis=1)
    # single-sub-screen noise null (Phase-019-style) -> the WRONG family threshold
    single_null = sim_S(rng, ns, np.zeros(C), N_PERM)

    band: dict = {}
    band_ok = True
    for fwer in FWER_BAND:
        s_star_joint = int(np.quantile(joint_null, 1.0 - fwer))
        s_star_single = int(np.quantile(single_null, 1.0 - fwer))

        noise_fam = family_S(rng, ns, mus_noise, R_REP).max(axis=1)
        n_admit = int((noise_fam > s_star_joint).sum())
        noise_rate = n_admit / R_REP
        noise_hi = wilson_upper(n_admit, R_REP)

        plant_fam = family_S(rng, ns, mus_plant, R_REP)
        plant_max = plant_fam.max(axis=1)
        admit_mask = plant_max > s_star_joint
        power = int(admit_mask.sum()) / R_REP
        argmax_planted = (plant_fam.argmax(axis=1) == PLANTED_SUB)
        argmax_rate = (float((argmax_planted & admit_mask).sum()) / int(admit_mask.sum())
                       if admit_mask.any() else 0.0)

        # inflation contrast: the same noise families under the WRONG single-sub S*
        inflated_rate = int((noise_fam > s_star_single).sum()) / R_REP

        ok = (noise_hi <= max(fwer, WILSON_TOL)) and (power >= POWER_FLOOR) \
            and (argmax_rate >= ARGMAX_FLOOR)
        band_ok &= ok
        band[f"fwer_{fwer}"] = {
            "s_star_joint_max6": s_star_joint,
            "s_star_single_subscreen": s_star_single,
            "noise_admission_rate": round(noise_rate, 4),
            "noise_admission_wilson_hi": round(noise_hi, 4),
            "planted_power": round(power, 4),
            "planted_argmax_rate": round(argmax_rate, 4),
            "inflated_rate_if_single_threshold": round(inflated_rate, 4),
            "ok": bool(ok),
        }
    report["B_operating_characteristics"] = band

    # ---- (C) joint-max necessity (new-leg demonstration) --------------------
    s_star_joint_05 = int(np.quantile(joint_null, 0.95))
    s_star_single_05 = int(np.quantile(single_null, 0.95))
    noise_fam_05 = family_S(rng, ns, mus_noise, R_REP).max(axis=1)
    rate_joint_05 = int((noise_fam_05 > s_star_joint_05).sum()) / R_REP
    rate_single_05 = int((noise_fam_05 > s_star_single_05).sum()) / R_REP
    necessity_ok = (s_star_joint_05 > s_star_single_05) and (rate_single_05 > 0.05) \
        and (wilson_upper(int((noise_fam_05 > s_star_joint_05).sum()), R_REP) <= WILSON_TOL)
    report["C_joint_max_necessity"] = {
        "s_star_single_subscreen_q95": s_star_single_05,
        "s_star_joint_max6_q95": s_star_joint_05,
        "family_noise_rate_under_single_threshold": round(rate_single_05, 4),
        "family_noise_rate_under_joint_threshold": round(rate_joint_05, 4),
        "note": "6-way max inflates family error under the single-sub-screen S*; "
                "the joint max-of-6 S* raises the bar and restores FWER control.",
        "ok": bool(necessity_ok),
    }

    # ---- (D) MC stability: 1000 vs 5000 (no routing flip) -------------------
    joint_null_1k = family_S(rng, ns, mus_noise, N_PERM_STAB).max(axis=1)
    s_star_1k = int(np.quantile(joint_null_1k, 0.95))
    s_star_5k = int(np.quantile(joint_null, 0.95))
    # planted family perm_p at both scales (one representative planted dataset)
    plant_rep = family_S(rng, ns, mus_plant, 1).max()
    perm_p_1k = (1 + int((joint_null_1k >= plant_rep).sum())) / (1 + N_PERM_STAB)
    perm_p_5k = (1 + int((joint_null >= plant_rep).sum())) / (1 + N_PERM)
    mc_ok = (s_star_1k == s_star_5k) and ((perm_p_1k <= 0.05) == (perm_p_5k <= 0.05))
    report["D_mc_stability"] = {
        "s_star_q95_1000": s_star_1k, "s_star_q95_5000": s_star_5k,
        "planted_perm_p_1000": round(perm_p_1k, 4),
        "planted_perm_p_5000": round(perm_p_5k, 4),
        "ok": bool(mc_ok),
    }

    # ---- OVERALL ------------------------------------------------------------
    checks = {
        "A_real_module_routes_correctly": report["A_real_module_integration"]["ok"],
        "B_not_vacuous_and_not_impossible_across_band": bool(band_ok),
        "C_joint_max_necessary_and_sufficient": bool(necessity_ok),
        "D_mc_stable_1000_vs_5000": bool(mc_ok),
    }
    report["checks"] = checks
    report["OVERALL"] = "GREEN" if all(checks.values()) else "RE-ANCHOR NEEDED"

    OUT.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    print(f"\nOVERALL: {report['OVERALL']}  ->  {OUT}")


if __name__ == "__main__":
    main()
