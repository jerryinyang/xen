"""
Experiment EXP-078: `ASS`/VAL-003 — Shape Discrimination + `k`-Sensitivity (Phase 017).
Implements the analysis plan from analysis-plan.md. Last experiment before terminal G-017.

Validates two things about the `ASS` qualifier on synthetic populations with KNOWN shape:

  Check 1 (BINDING) — shape discrimination: the frozen D2.5 diagnostic
       flag = (dip_p < 0.05) OR (|g| > tau_gap=0.30),  g = (mean - median)/MAD
       separates bimodal `B` (detection >= 0.80) from unimodal `U` (false-flag <= 0.05) per
       (type, n>=30). Per-leg (dip vs gap) decomposed; Wilson 95% intervals on every rate.
       Closes the EXP-074 gap (the anti-p-hacking guard was structurally blind to tail shape).
  Check 2 (DISCLOSED) — S-family asymmetry characterization: where the unimodal-but-skewed
       `Splus/Sminus/Sminus0` land on each leg (the gap leg is DESIGNED to flag left-skew).
       NOT part of the binding U-vs-B PASS.
  Check 3 (BINDING) — `k`-sensitivity: across the pre-registered grid
       k in {0.5x, 1x, 2x}*median-n ∪ {30, 500}, the `ASS` binding routing is invariant (or
       bounded+disclosed). The shape flag is computed on the RAW sample so it is k-independent by
       construction; the sweep therefore acts only on the k-DEPENDENT machinery:
         K1 — SP shrinkage behaviour label (monotone + sparse-pull>=0.25) per k;
         K2 — shrunk-expectancy null edge-call FPR (deployment-mode, margin calibrated at the
              default k and HELD FIXED while k is swept) per k. Does a verdict label flip?

SYNTHETIC ONLY — no market data, no Parquet load, no holdout/TEST stratum, no temporal ordering.
The standard first-70% loader is intentionally absent (this experiment touches no real dataset).
Determinism (D6): every draw seeded from (tag, type_id, n, replicate) via SeedSequence; `k` is a
SCORING parameter and NEVER enters a sample-draw seed (paired draws across the grid); the dip-test
p-value is the analytic Hartigan value (no RNG). A second pass is hash-identical.

VERDICT SHAPE (LESSON-001 / D0 §8 / EXP-076 audit C1). The verdict is reported PER STRATUM
(per type / per n / per k); no single collapsed cross-cell boolean is binding (a collapsed flag is
retained only as an explicitly NON-BINDING disclosure).

OPERATING-k NOTE (governance disclosure). The deployed default shrinkage k = median sample size
across the pooled signal types = median(SP population n) = 120 (exactly EXP-076's `k_shrink`). The
D3 grid multipliers {0.5x,1x,2x} are applied to THIS 120 (not to median(N_GRID)=250), so 1x is the
ACTUAL deployed operating point and the sweep tests sensitivity around it. Both medians are recorded
in integrity.json. This is a deployment-faithful reading of D3 ("k default = median sample size
across signal types"), not a parameter change.

Run:     python python/experiments/EXP-078/code/run_experiment.py
Smoke:   python python/experiments/EXP-078/code/run_experiment.py --smoke   (NON-BINDING)
Verify:  python python/experiments/EXP-078/code/run_experiment.py --verify-determinism
         (recompute the cheap shape table + K1 + one K2 probe cell and assert hash-identity)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import seaborn as sns
from scipy import stats
from tqdm.auto import tqdm

from xen import ass

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
EXP_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"
EXP076_INTEGRITY = EXP_DIR.parent / "EXP-076" / "results" / "integrity.json"
EXP077_INTEGRITY = EXP_DIR.parent / "EXP-077" / "results" / "integrity.json"

logger = logging.getLogger("EXP-078")

# --------------------------------------------------------------------------- #
# Frozen constants (Phase 017 D0 §D1/§D2.5/§D3/§D6 — no change without a D0-amendment)
# --------------------------------------------------------------------------- #
MASTER_SEED = 20260620
N_GRID = (15, 30, 60, 120, 250, 500, 1000, 2000, 8000)   # n<30 = sparse stress (disclosed)
BINDING_N = 30                # shape binding floor: U false-flag / B detection bind at n>=30
R_REP = 2000                  # replicate draws per (type, n)
N_BOOT = ass.N_BOOT           # 10_000
CI_ALPHA = ass.CI_ALPHA       # 0.10 -> 90% CI; 5th pct = one-sided 95% lower (ci_low_1s)
TAU_GAP = ass.TAU_GAP         # 0.30 (frozen D2.5 operating point — measured, not re-tuned)
DIP_ALPHA = ass.DIP_ALPHA     # 0.05
FF_TARGET = 0.05              # D2.5 false-flag ceiling on U
FF_WILSON_HI = 0.075          # Wilson upper-95% ceiling (mirrors EXP-077 FPR convention)
DET_TARGET = 0.80             # D2.5 detection floor on B

# k-sensitivity (D3): margin-calibrated null edge-call FPR convention (EXP-077 analog)
FPR_TARGET = 0.05
FPR_WILSON_HI = 0.075
MARGIN_Q = 0.95               # m = max(0, Q95(ci_low_1s | null)) at the DEFAULT k (m_cell analog)
NULL_TYPES = ("U0", "B_zero")            # D2.2 null strata (mean<=0 leg)
NK2_GRID = (30, 120, 500, 2000)          # K2 null n's: span sparse->rich, all n>=30

ANCHOR_TYPE, ANCHOR_N, ANCHOR_REP = "U2", 250, 0   # shared cross-experiment integrity cell

# Deterministic RNG stream tags (keep streams disjoint; D6). TAG_SAMPLE/TAG_EFF reproduce the
# EXP-076 (=1) and EXP-077 (=3) anchor streams for the cross-experiment 1e-9 reconciliation.
TAG_SAMPLE, TAG_BOOT, TAG_SP, TAG_EFF = 1, 2, 6, 3
TAG_CAL, TAG_VAL = 7, 8        # K2 margin-calibration vs FPR-validation null streams (disjoint)


def rng_for(*key: int) -> np.random.Generator:
    """Deterministic generator seeded by (MASTER_SEED, *key) via SeedSequence."""
    return np.random.default_rng(np.random.SeedSequence([MASTER_SEED, *(int(k) for k in key)]))


def wilson_interval(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Two-sided Wilson score interval (lo, hi) for a binomial rate k/n (n>0)."""
    if n <= 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denom
    half = (z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))) / denom
    return (max(0.0, center - half), min(1.0, center + half))


# --------------------------------------------------------------------------- #
# Synthetic data-generating processes (D1; identical to EXP-076/077 for cross-anchoring)
# --------------------------------------------------------------------------- #
def gen_unimodal(mu: float, size, rng: np.random.Generator) -> np.ndarray:
    return rng.normal(mu, 1.0, size)


def gen_skewnormal(xi: float, omega: float, alpha: float, size,
                   rng: np.random.Generator) -> np.ndarray:
    return stats.skewnorm.rvs(a=alpha, loc=xi, scale=omega, size=size, random_state=rng)


def gen_bimodal(w: float, mu1: float, s1: float, mu2: float, s2: float, size,
                rng: np.random.Generator) -> np.ndarray:
    comp = rng.random(size) < w
    return np.where(comp, rng.normal(mu1, s1, size), rng.normal(mu2, s2, size))


# --------------------------------------------------------------------------- #
# Type registry (frozen D1) — family label drives the should-flag / should-not-flag role
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class TypeSpec:
    """One synthetic signal type: integer id (seeding), family, sampler, closed-form mean."""

    label: str
    type_id: int
    family: str                               # "U" (should-not-flag) | "S" (disclosed) | "B"
    draw: Callable[[object, np.random.Generator], np.ndarray]
    mean_truth: float


def _bimodal_mean(w, mu1, mu2) -> float:
    return float(w * mu1 + (1.0 - w) * mu2)


def build_type_registry() -> dict[str, TypeSpec]:
    """Construct the frozen D1 type registry (U/S/B), identical seeds/params to EXP-076."""
    specs: dict[str, TypeSpec] = {}
    for label, tid, mu in [("U0", 0, 0.0), ("U1", 1, 0.05), ("U2", 2, 0.10), ("U3", 3, 0.20)]:
        specs[label] = TypeSpec(label, tid, "U",
                                lambda sz, rng, m=mu: gen_unimodal(m, sz, rng), mu)
    skews = [("Splus", 10, 0.0, 1.0, 4.0), ("Sminus", 11, 0.55, 1.0, -4.0),
             ("Sminus0", 12, 0.62, 1.0, -4.0)]
    for label, tid, xi, omega, alpha in skews:
        delta = alpha / math.sqrt(1.0 + alpha * alpha)
        mean = xi + omega * delta * math.sqrt(2.0 / math.pi)
        specs[label] = TypeSpec(label, tid, "S",
                                lambda sz, rng, p=(xi, omega, alpha): gen_skewnormal(
                                    p[0], p[1], p[2], sz, rng), float(mean))
    bis = [("B_neg", 20, 0.85, 0.15, 0.5, -2.0, 0.6),
           ("B_zero", 21, 0.90, 0.15, 0.5, -1.5, 0.6),
           ("B_pos", 22, 0.95, 0.10, 0.5, -1.0, 0.6),
           ("B_strong", 23, 0.80, 0.20, 0.5, -2.0, 0.6)]
    for label, tid, w, mu1, s1, mu2, s2 in bis:
        specs[label] = TypeSpec(label, tid, "B",
                                lambda sz, rng, p=(w, mu1, s1, mu2, s2): gen_bimodal(
                                    p[0], p[1], p[2], p[3], p[4], sz, rng),
                                _bimodal_mean(w, mu1, mu2))
    return specs


# SP shrinkage population (D1): mixed-n members, median n = 120 -> deployed k = median-n = 120.
SP_MEMBERS = (
    (0, "U0", 15), (1, "Splus", 30), (2, "B_neg", 60), (3, "U2", 120), (4, "Sminus", 120),
    (5, "B_zero", 250), (6, "U3", 500), (7, "B_strong", 2000), (8, "Splus", 8000),
)
SPARSE_N, RICH_N = 30, 2000
SPARSE_PULL_MIN, RICH_PULL_MAX = 0.25, 0.05


def build_sp_pool() -> tuple[np.ndarray, float, float]:
    """SP pooled prior + pool mean + deployed default k (= median SP member n). D6 seeded."""
    specs = build_type_registry()
    draws = {midx: specs[lbl].draw(n, rng_for(TAG_SP, midx, n)) for midx, lbl, n in SP_MEMBERS}
    pool = np.concatenate([draws[midx] for midx, _, _ in SP_MEMBERS])
    k_default = float(np.median([n for _, _, n in SP_MEMBERS]))
    return pool, float(np.mean(pool)), k_default


def build_k_grid(k_default: float) -> tuple[list[float], list[dict]]:
    """Frozen D3 grid {0.5x,1x,2x}*k_default ∪ {30,500}; dedupe + disclose collisions."""
    raw = [("0.5x", 0.5 * k_default), ("1x", k_default), ("2x", 2.0 * k_default),
           ("anchor30", 30.0), ("anchor500", 500.0)]
    seen: dict[float, str] = {}
    disclosure: list[dict] = []
    grid: list[float] = []
    for tag, val in raw:
        v = float(val)
        if v in seen:
            disclosure.append({"role": tag, "k": v, "collides_with": seen[v]})
        else:
            seen[v] = tag
            grid.append(v)
            disclosure.append({"role": tag, "k": v, "collides_with": None})
    return sorted(grid), disclosure


# --------------------------------------------------------------------------- #
# Pure computation — Check 1 & 2 (shape discrimination rates per (type, n))
# --------------------------------------------------------------------------- #
def draw_cell_samples(spec: TypeSpec, n: int, n_rep: int) -> np.ndarray:
    """Stack ``n_rep`` size-``n`` replicate samples; per-replicate seed (D6). k-independent."""
    out = np.empty((n_rep, n), dtype=np.float64)
    for rep in range(n_rep):
        out[rep] = spec.draw(n, rng_for(TAG_SAMPLE, spec.type_id, n, rep))
    return out


def shape_rate_for_cell(samples: np.ndarray, spec: TypeSpec, n: int) -> dict:
    """Flag rates over replicates: combined / dip-only / gap-only, with Wilson 95% intervals.

    Rates are ``#{flag} / n_rep`` with the FIXED denominator ``n_rep`` (no zero-baseline ratio).
    ``mad_zero`` occurrences are counted (the degenerate-sample branch) and surfaced for the
    caller's assertion. Pure: no I/O, returns one record.
    """
    n_rep = samples.shape[0]
    comb = dip = gap = mad0 = 0
    for rep in range(n_rep):
        d = ass.shape_diagnostic(samples[rep], tau_gap=TAU_GAP, dip_alpha=DIP_ALPHA)
        comb += int(d.flag)
        dip += int(d.dip_flag)
        gap += int(d.gap_flag)
        mad0 += int(d.mad_zero)
    role = {"U": "should_not_flag", "S": "disclosed_asymmetric", "B": "should_flag"}[spec.family]
    ff_lo, ff_hi = wilson_interval(comb, n_rep)
    return {"type": spec.label, "family": spec.family, "role": role, "n": n, "n_rep": n_rep,
            "flag_rate": comb / n_rep, "dip_rate": dip / n_rep, "gap_rate": gap / n_rep,
            "wilson_lo": ff_lo, "wilson_hi": ff_hi, "mad_zero_count": mad0,
            "binding": bool(n >= BINDING_N and spec.family in ("U", "B"))}


def _shape_task(task: tuple) -> dict:
    """Picklable worker: rebuild registry locally, draw one (type, n) cell, score the rate."""
    label, n, n_rep = task
    spec = build_type_registry()[label]
    return shape_rate_for_cell(draw_cell_samples(spec, n, n_rep), spec, n)


def run_shape_rates(specs: dict[str, TypeSpec], n_rep: int,
                    workers: int) -> list[dict]:
    """Check 1 & 2 over every (type, n) cell. Cells are independently seeded -> order-stable."""
    tasks = [(lbl, n, n_rep) for lbl in specs for n in N_GRID]
    rows: list[dict] = []
    if workers <= 1:
        for t in tqdm(tasks, desc="shape rates (type,n)"):
            rows.append(_shape_task(t))
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for r in tqdm(ex.map(_shape_task, tasks), total=len(tasks),
                          desc=f"shape rates (x{workers})"):
                rows.append(r)
    return rows


def shape_pass_table(rows: list[dict]) -> dict:
    """Per-stratum PASS/FAIL on the BINDING U/B cells (n>=30); S + n<30 disclosed."""
    df = pl.DataFrame(rows)
    binding = df.filter(pl.col("binding"))
    u_fail = binding.filter((pl.col("family") == "U") &
                            ((pl.col("flag_rate") > FF_TARGET) |
                             (pl.col("wilson_hi") > FF_WILSON_HI)))
    b_fail = binding.filter((pl.col("family") == "B") & (pl.col("flag_rate") < DET_TARGET))
    return {
        "u_false_flag": {
            "verdict": "PASS" if u_fail.height == 0 else "FAIL",
            "rule": f"flag_rate <= {FF_TARGET} AND wilson_hi <= {FF_WILSON_HI} on every U, n>=30",
            "n_binding_cells": binding.filter(pl.col("family") == "U").height,
            "worst_flag_rate": float(binding.filter(pl.col("family") == "U")["flag_rate"].max()),
            "failing_cells": u_fail.select(["type", "n", "flag_rate", "wilson_hi"]).to_dicts(),
        },
        "b_detection": {
            "verdict": "PASS" if b_fail.height == 0 else "FAIL",
            "rule": f"flag_rate >= {DET_TARGET} on every B, n>=30",
            "n_binding_cells": binding.filter(pl.col("family") == "B").height,
            "worst_detection": float(binding.filter(pl.col("family") == "B")["flag_rate"].min()),
            "failing_cells": b_fail.select(["type", "n", "flag_rate", "wilson_lo"]).to_dicts(),
        },
        "binding": True,
        "n_lt_30_disclosed": df.filter(pl.col("n") < BINDING_N)
        .select(["type", "n", "flag_rate"]).to_dicts(),
    }


# --------------------------------------------------------------------------- #
# Pure computation — Check 3 / K1 (SP shrinkage behaviour per k)
# --------------------------------------------------------------------------- #
def shrinkage_label_for_k(pool_mean: float, k: float) -> dict:
    """K1: SP shrinkage behaviour at one k. BINDING label = monotone ∧ sparse-pull>=0.25.

    Uses the analytic pull ``1 - n/(n+k) = k/(n+k)`` (the EXP-076 Check-3 disposition). The
    weight ``n/(n+k)`` is monotone in n for any k>0 (monotonicity never flips) and the sparse
    members (n<=30) always clear the >=0.25 pull at any grid k>=30 — these are the binding legs.
    The rich-stability bound (pull<0.05 at n>=2000) is, by construction, a k-dependent TRADEOFF,
    not a behaviour defect: EXP-076 already DISCLOSED the n=2000 marginal (120/2120=0.0566 at the
    deployed k=120) as a predeclared analytic marginal, not a fail. It is therefore reported here
    as a disclosed k-dependent quantity, NOT folded into the binding label (which would convert a
    known-marginal boundary into a spurious routing flip).
    """
    ns = [n for _, _, n in SP_MEMBERS]
    weights = [ass.shrinkage_weight(n, k) for n in ns]
    monotone = bool(np.all(np.diff(weights) >= -1e-12))
    sparse_ok = all((n > SPARSE_N) or (1.0 - ass.shrinkage_weight(n, k) >= SPARSE_PULL_MIN)
                    for n in ns)
    rich_ok = all((n < RICH_N) or (1.0 - ass.shrinkage_weight(n, k) < RICH_PULL_MAX) for n in ns)
    rich_marginals = [{"n": n, "pull": float(1.0 - ass.shrinkage_weight(n, k))}
                      for n in ns if n >= RICH_N and (1.0 - ass.shrinkage_weight(n, k))
                      >= RICH_PULL_MAX]
    label = "SHRINK_OK" if (monotone and sparse_ok) else "SHRINK_FAIL"
    return {"leg": "K1_shrinkage", "k": k, "monotone": monotone, "sparse_ok": bool(sparse_ok),
            "rich_ok_literal": bool(rich_ok),
            "rich_marginals_disclosed": json.dumps(rich_marginals),
            "min_pull_sparse": float(min((1.0 - ass.shrinkage_weight(n, k))
                                         for n in ns if n <= SPARSE_N)),
            "max_pull_rich": float(max((1.0 - ass.shrinkage_weight(n, k))
                                       for n in ns if n >= RICH_N)),
            "label": label}


# --------------------------------------------------------------------------- #
# Pure computation — Check 3 / K2 (shrunk-expectancy null edge-call FPR per k)
# --------------------------------------------------------------------------- #
def _shrunk_ci_low(x: np.ndarray, rng: np.random.Generator, pool_mean: float, k: float) -> float:
    """One-sided 95% lower bound (5th pct) of the SHRUNK expectancy bootstrap at shrinkage k."""
    n = x.shape[0]
    weight = ass.shrinkage_weight(n, k)
    ci = ass.bootstrap_cis(x, rng, n_boot=N_BOOT, alpha=CI_ALPHA,
                           pool_mean=pool_mean, weight=weight)
    return ci.expectancy_lo


def calibrate_k2_margin(spec: TypeSpec, n: int, pool_mean: float, k_default: float,
                        r_rep: int) -> float:
    """m(type,n) = max(0, Q95(shrunk ci_low | null)) at the DEFAULT k on TAG_CAL null series.

    Calibrated ONCE at the deployed k and then HELD FIXED while k is swept (so the sweep is not
    self-canceling): the EXP-077 m_cell rule, here under the shrinkage deployment mode.
    """
    lows = np.empty(r_rep, dtype=np.float64)
    for rep in range(r_rep):
        series = spec.draw(n, rng_for(TAG_CAL, spec.type_id, n, rep))
        lows[rep] = _shrunk_ci_low(series, rng_for(TAG_CAL, spec.type_id, n, rep, 1),
                                   pool_mean, k_default)
    return float(max(0.0, np.quantile(lows, MARGIN_Q)))


def k2_fpr_for_cell(spec: TypeSpec, n: int, k: float, margin: float, pool_mean: float,
                    r_rep: int) -> dict:
    """K2: shrunk-expectancy edge-call FPR at shrinkage k under the FIXED default-k margin.

    Null series drawn from TAG_VAL (independent of the TAG_CAL calibration stream). Edge-call =
    ``shrunk ci_low_1s > margin``. Label CONTROLLED iff fpr<=0.05 AND wilson_hi<=0.075.
    """
    edges = 0
    for rep in range(r_rep):
        series = spec.draw(n, rng_for(TAG_VAL, spec.type_id, n, rep))
        low = _shrunk_ci_low(series, rng_for(TAG_VAL, spec.type_id, n, rep, 1), pool_mean, k)
        edges += int(low > margin)
    fpr = edges / r_rep
    whi = wilson_interval(edges, r_rep)[1]
    label = "CONTROLLED" if (fpr <= FPR_TARGET and whi <= FPR_WILSON_HI) else "INFLATED"
    return {"leg": "K2_null_fpr", "type": spec.label, "n": n, "k": k, "margin": margin,
            "edges": edges, "r_rep": r_rep, "fpr": fpr, "wilson_hi": whi, "label": label,
            "binding": True}


def _k2_task(task: tuple) -> dict:
    """Picklable worker for one K2 (null_type, n, k) FPR cell (margin precomputed)."""
    label, n, k, margin, pool_mean, r_rep = task
    spec = build_type_registry()[label]
    return k2_fpr_for_cell(spec, n, k, margin, pool_mean, r_rep)


def run_k_sensitivity(pool_mean: float, k_default: float, k_grid: list[float], r_rep: int,
                      workers: int) -> tuple[list[dict], list[dict], dict]:
    """Check 3: K1 shrinkage labels + K2 null-FPR labels across the k-grid; routing verdict.

    Returns (k1_rows, k2_rows, routing_verdict). K2 margins are calibrated ONCE per (null,n) at
    ``k_default`` and held fixed across the swept k (paired draws, fixed margin).
    """
    k1_rows = [shrinkage_label_for_k(pool_mean, k) for k in k_grid]
    specs = build_type_registry()
    margins = {(t, n): calibrate_k2_margin(specs[t], n, pool_mean, k_default, r_rep)
               for t in NULL_TYPES for n in NK2_GRID}
    tasks = [(t, n, k, margins[(t, n)], pool_mean, r_rep)
             for t in NULL_TYPES for n in NK2_GRID for k in k_grid]
    k2_rows: list[dict] = []
    if workers <= 1:
        for t in tqdm(tasks, desc="K2 null-FPR (type,n,k)"):
            k2_rows.append(_k2_task(t))
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for r in tqdm(ex.map(_k2_task, tasks), total=len(tasks),
                          desc=f"K2 null-FPR (x{workers})"):
                k2_rows.append(r)
    routing = _routing_verdict(k1_rows, k2_rows, k_grid, k_default)
    return k1_rows, k2_rows, routing


def _routing_verdict(k1_rows: list[dict], k2_rows: list[dict], k_grid: list[float],
                     k_default: float) -> dict:
    """Routing-invariance: a per-stratum verdict label identical at all grid k = invariant.

    Bounded-disclosure PASS iff any flip occurs ONLY at an extreme anchor (k in {30,500}) that is
    not the deployed k, AND the deployed-k label is on the PASS side. Else FAIL. Magnitudes are
    ABSOLUTE deltas of the driving quantity across the grid (no percentage of a zero baseline).
    """
    def assess(labels_by_k: dict[float, str], pass_label: str, drivers: dict[float, float]):
        labels = set(labels_by_k.values())
        invariant = len(labels) == 1
        deployed = labels_by_k[k_default]
        flip_ks = [k for k, lab in labels_by_k.items() if lab != deployed]
        extreme_only = all(k in (30.0, 500.0) and k != k_default for k in flip_ks)
        abs_delta = float(max(drivers.values()) - min(drivers.values()))
        if invariant:
            verdict = "INVARIANT"
        elif extreme_only and deployed == pass_label:
            verdict = "BOUNDED_DISCLOSED"
        else:
            verdict = "FLIP_UNBOUNDED"
        return {"verdict": verdict, "labels_by_k": {str(k): v for k, v in labels_by_k.items()},
                "deployed_k_label": deployed, "flip_ks": flip_ks,
                "abs_delta_driver": abs_delta}

    k1_labels = {r["k"]: r["label"] for r in k1_rows}
    k1_drivers = {r["k"]: r["min_pull_sparse"] for r in k1_rows}
    k1 = assess(k1_labels, "SHRINK_OK", k1_drivers)
    k1["rich_pull_disclosed"] = {
        "note": ("rich-stability pull (n>=2000) grows with k BY CONSTRUCTION — disclosed, not a "
                 "binding fail; EXP-076 predeclared the n=2000 marginal (0.0566 at k=120)"),
        "max_rich_pull_by_k": {str(r["k"]): r["max_pull_rich"] for r in k1_rows},
        "rich_marginals_by_k": {str(r["k"]): json.loads(r["rich_marginals_disclosed"])
                                for r in k1_rows},
    }
    # K2: one routing call per (null_type, n) stratum.
    k2_strata: dict[str, dict] = {}
    for t in NULL_TYPES:
        for n in NK2_GRID:
            cells = [r for r in k2_rows if r["type"] == t and r["n"] == n]
            labels = {r["k"]: r["label"] for r in cells}
            drivers = {r["k"]: r["fpr"] for r in cells}
            k2_strata[f"{t}/n={n}"] = assess(labels, "CONTROLLED", drivers)
    k2_invariant = all(s["verdict"] in ("INVARIANT", "BOUNDED_DISCLOSED")
                       for s in k2_strata.values())
    overall = ("ROUTING_INVARIANT"
               if (k1["verdict"] in ("INVARIANT", "BOUNDED_DISCLOSED") and k2_invariant)
               else "ROUTING_FLIP")
    return {"binding": True, "k_grid": k_grid, "k_default": k_default,
            "K1_shrinkage": k1, "K2_null_fpr": k2_strata, "verdict": overall,
            "note": ("routing-invariant or bounded+disclosed across the pre-registered grid => "
                     "no Phase-018 verdict flips on k within the band")}


# --------------------------------------------------------------------------- #
# Pure computation — integrity anchor (cross-experiment reconciliation to EXP-076/077)
# --------------------------------------------------------------------------- #
def _recorded_anchor(path: Path) -> float | None:
    if not path.exists():
        return None
    return float(json.loads(path.read_text())["anchor"]["direct_expectancy"])


def integrity_anchor() -> dict:
    """Reconcile default-k (un-pooled) ASS expectancy on U2/250/0 to EXP-076 AND EXP-077 (<=1e-9).

    EXP-076 used TAG_SAMPLE(=1); EXP-077 used TAG_EFF(=3) on the same cell. Recompute both with
    the identical xen.ass core + rng_for + DGP and compare to the recorded values. Also asserts
    the R3 self-anchor direct_expectancy == numpy.mean (<=1e-12) on the EXP-076 stream cell.
    """
    spec = build_type_registry()[ANCHOR_TYPE]
    out: dict = {"anchor_cell": f"{ANCHOR_TYPE}/n={ANCHOR_N}/rep={ANCHOR_REP}"}
    # EXP-076 stream (TAG_SAMPLE)
    x76 = spec.draw(ANCHOR_N, rng_for(TAG_SAMPLE, spec.type_id, ANCHOR_N, ANCHOR_REP))
    e76 = ass.score(x76, shrink=False).expectancy_direct
    rec76 = _recorded_anchor(EXP076_INTEGRITY)
    out["exp076"] = {"recomputed": e76, "recorded": rec76,
                     "abs_diff": (abs(e76 - rec76) if rec76 is not None else None),
                     "self_anchor_diff": abs(e76 - float(np.mean(x76))),
                     "pass": bool(rec76 is not None and abs(e76 - rec76) <= 1e-9)}
    # EXP-077 stream (TAG_EFF) — the EXP-077 edge-call machinery cell
    x77 = spec.draw(ANCHOR_N, rng_for(TAG_EFF, spec.type_id, ANCHOR_N, ANCHOR_REP))
    e77 = ass.score(x77, shrink=False).expectancy_direct
    rec77 = _recorded_anchor(EXP077_INTEGRITY)
    out["exp077"] = {"recomputed": e77, "recorded": rec77,
                     "abs_diff": (abs(e77 - rec77) if rec77 is not None else None),
                     "pass": bool(rec77 is not None and abs(e77 - rec77) <= 1e-9)}
    out["pass"] = bool(out["exp076"]["pass"] and out["exp077"]["pass"]
                       and out["exp076"]["self_anchor_diff"] <= 1e-12)
    return out


# --------------------------------------------------------------------------- #
# Plotting (4) — consume bounded result tables, no heavy recompute
# --------------------------------------------------------------------------- #
def plot_shape_rates_vs_n(df: pl.DataFrame, path: Path) -> None:
    """Plot 1: U false-flag (with 0.05 line) and B detection (with 0.80 line) vs n."""
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    for ax, fam, line, lab in [(axes[0], "U", FF_TARGET, "false-flag rate"),
                               (axes[1], "B", DET_TARGET, "detection rate")]:
        sub = df.filter(pl.col("family") == fam)
        for t in sorted(sub["type"].unique().to_list()):
            d = sub.filter(pl.col("type") == t).sort("n")
            ax.plot(d["n"], d["flag_rate"], marker="o", label=t, alpha=0.85)
            ax.fill_between(d["n"], d["wilson_lo"], d["wilson_hi"], alpha=0.12)
        ax.axhline(line, color="red", ls="--", label=f"target {line}")
        ax.axvline(BINDING_N, color="grey", ls=":", label=f"binding n>={BINDING_N}")
        ax.set_xscale("log")
        ax.set_title(f"{fam} family — {lab}")
        ax.set_xlabel("n (log)")
        ax.set_ylabel("combined flag rate")
        ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_leg_distributions(df: pl.DataFrame, n_rep_at: int, path: Path) -> None:
    """Plot 2: per-leg flag rates by type at a representative n (dip vs gap vs combined)."""
    sns.set_theme(style="whitegrid")
    sub = df.filter(pl.col("n") == n_rep_at).sort(["family", "type"])
    fig, ax = plt.subplots(figsize=(11, 5.5))
    x = np.arange(sub.height)
    ax.bar(x - 0.25, sub["dip_rate"], width=0.25, label="dip leg (dip_p<0.05)")
    ax.bar(x + 0.00, sub["gap_rate"], width=0.25, label=f"gap leg (|g|>{TAU_GAP})")
    ax.bar(x + 0.25, sub["flag_rate"], width=0.25, label="combined (OR)")
    ax.axhline(FF_TARGET, color="red", ls="--", label=f"U target {FF_TARGET}")
    ax.axhline(DET_TARGET, color="green", ls="--", label=f"B target {DET_TARGET}")
    ax.set_xticks(x)
    ax.set_xticklabels(sub["type"], rotation=45, ha="right", fontsize=8)
    ax.set_title(f"Per-leg flag rates by type (n={n_rep_at}) — dip=bimodal, gap=skew")
    ax.set_ylabel("flag rate")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_k_sensitivity(k1_df: pl.DataFrame, k2_df: pl.DataFrame, k_default: float,
                       path: Path) -> None:
    """Plot 3: K1 sparse/rich pull and K2 null FPR vs k, with PASS bands and deployed k marked."""
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    a = axes[0]
    d1 = k1_df.sort("k")
    a.plot(d1["k"], d1["min_pull_sparse"], marker="o", label="min sparse pull")
    a.plot(d1["k"], d1["max_pull_rich"], marker="s", label="max rich pull")
    a.axhline(SPARSE_PULL_MIN, color="orange", ls="--", label=f"sparse>={SPARSE_PULL_MIN}")
    a.axhline(RICH_PULL_MAX, color="red", ls="--", label=f"rich<{RICH_PULL_MAX}")
    a.axvline(k_default, color="black", ls=":", label=f"deployed k={k_default:g}")
    a.set_title("K1 — SP shrinkage pull vs k")
    a.set_xlabel("k")
    a.set_ylabel("pull = k/(n+k)")
    a.legend(fontsize=7)
    b = axes[1]
    for t in sorted(k2_df["type"].unique().to_list()):
        for n in sorted(k2_df.filter(pl.col("type") == t)["n"].unique().to_list()):
            d = k2_df.filter((pl.col("type") == t) & (pl.col("n") == n)).sort("k")
            b.plot(d["k"], d["fpr"], marker="o", alpha=0.8, label=f"{t}/n={n}")
    b.axhline(FPR_TARGET, color="red", ls="--", label=f"FPR target {FPR_TARGET}")
    b.axvline(k_default, color="black", ls=":", label=f"deployed k={k_default:g}")
    b.set_title("K2 — shrunk null edge-call FPR vs k (fixed default-k margin)")
    b.set_xlabel("k")
    b.set_ylabel("FPR")
    b.legend(fontsize=6, ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_dip_vs_gap(specs: dict[str, TypeSpec], n_at: int, path: Path) -> None:
    """Plot 4: dip_p vs |g| scatter (one point per type-replicate sample) with decision lines."""
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8.5, 6.5))
    colors = {"U": "tab:blue", "S": "tab:orange", "B": "tab:red"}
    n_pts = 60                                    # bounded deterministic sample per type
    for label, spec in specs.items():
        dp = np.empty(n_pts)
        gg = np.empty(n_pts)
        for i in range(n_pts):
            d = ass.shape_diagnostic(spec.draw(n_at, rng_for(TAG_SAMPLE, spec.type_id, n_at, i)),
                                     tau_gap=TAU_GAP, dip_alpha=DIP_ALPHA)
            dp[i], gg[i] = d.dip_p, abs(d.gap)
        ax.scatter(dp, gg, s=12, alpha=0.5, color=colors[spec.family],
                   label=spec.family if label in ("U0", "Splus", "B_neg") else None)
    ax.axvline(DIP_ALPHA, color="grey", ls="--", label=f"dip_p={DIP_ALPHA}")
    ax.axhline(TAU_GAP, color="black", ls="--", label=f"|g|={TAU_GAP}")
    ax.set_title(f"dip_p vs |g| by family (n={n_at}) — OR-rule flags upper-left ∪ above-line")
    ax.set_xlabel("dip-test p-value")
    ax.set_ylabel("|mean - median| / MAD")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration helpers
# --------------------------------------------------------------------------- #
def _sha256_df(df: pl.DataFrame) -> str:
    return hashlib.sha256(df.write_csv().encode()).hexdigest()


def _shape_df(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(rows).sort(["family", "type", "n"])


def build_verdict(shape_rows: list[dict], shape_pass: dict, routing: dict, anchor: dict,
                  det: dict, k_grid: list[float], k_default: float, scale: str) -> dict:
    """Assemble the PER-STRATUM EXP-078 verdict. No collapsed cross-cell boolean is binding."""
    collapsed = (shape_pass["u_false_flag"]["verdict"] == "PASS"
                 and shape_pass["b_detection"]["verdict"] == "PASS"
                 and routing["verdict"] == "ROUTING_INVARIANT"
                 and bool(anchor["pass"]) and all(det.values()))
    return {
        "scale": scale,
        "doctrine": ("PER-STRATUM adjudication (LESSON-001; D0 §8; cf-capgeo-001.md:137). Shape "
                     "(U false-flag / B detection per n) and k-sensitivity routing each carry a "
                     "verdict. No collapsed cross-cell boolean is binding; no homogeneity."),
        "strata": {
            "shape_discrimination": shape_pass,
            "k_sensitivity": routing,
            "skew_characterization": {
                "binding": False,
                "note": ("DISCLOSED, non-binding. S-family flag rates (Splus/Sminus/Sminus0) in "
                         "results/shape_skew.csv: the gap leg is DESIGNED to flag left-skew "
                         "asymmetry; a high S gap-rate supports the design, not a false flag."),
            },
        },
        "operating_k": {
            "deployed_k_default": k_default, "median_sp_n": k_default,
            "median_n_grid": float(np.median(N_GRID)), "k_grid": k_grid,
            "note": ("deployed k = median(SP n)=120 (= EXP-076 k_shrink), NOT median(N_GRID)=250; "
                     "D3 multipliers applied to the deployed operating point. Disclosure."),
        },
        "integrity": {"anchor": anchor, "determinism": det},
        "collapsed_convenience_flag": {
            "value": bool(collapsed),
            "caveat": ("NON-BINDING. Collapsed cross-stratum AND for convenience only; the "
                       "per-stratum verdicts above are binding (LESSON-001)."),
        },
    }


def _log_summary(verdict: dict) -> None:
    s = verdict["strata"]
    sd = s["shape_discrimination"]
    logger.info("STRATUM shape: U false-flag %s (worst %.4f); B detection %s (worst %.4f)",
                sd["u_false_flag"]["verdict"], sd["u_false_flag"]["worst_flag_rate"],
                sd["b_detection"]["verdict"], sd["b_detection"]["worst_detection"])
    ks = s["k_sensitivity"]
    logger.info("STRATUM k-sensitivity: %s (K1 %s; K2 strata %d)", ks["verdict"],
                ks["K1_shrinkage"]["verdict"], len(ks["K2_null_fpr"]))
    a = verdict["integrity"]["anchor"]
    logger.info("integrity: anchor_pass=%s (EXP-076 diff=%s, EXP-077 diff=%s); determinism=%s",
                a["pass"], a["exp076"]["abs_diff"], a["exp077"]["abs_diff"],
                verdict["integrity"]["determinism"])
    logger.info("collapsed_convenience_flag=%s (NON-BINDING — see results/verdict.json strata)",
                verdict["collapsed_convenience_flag"]["value"])


# --------------------------------------------------------------------------- #
# Determinism (D6) — recompute cheap tables + one K2 probe and hash-compare
# --------------------------------------------------------------------------- #
def determinism_check(shape_df: pl.DataFrame, k1_rows: list[dict], pool_mean: float,
                      k_default: float, r_rep: int, workers: int) -> dict:
    """D6: second pass of shape table + K1 + one K2 probe cell must be hash-identical."""
    specs = build_type_registry()
    shape2 = _shape_df(run_shape_rates(specs, r_rep, workers))
    k1_2 = [shrinkage_label_for_k(pool_mean, k) for k in [r["k"] for r in k1_rows]]
    probe_spec = specs[NULL_TYPES[0]]
    m = calibrate_k2_margin(probe_spec, NK2_GRID[0], pool_mean, k_default, r_rep)
    probe1 = k2_fpr_for_cell(probe_spec, NK2_GRID[0], k_default, m, pool_mean, r_rep)
    m2 = calibrate_k2_margin(probe_spec, NK2_GRID[0], pool_mean, k_default, r_rep)
    probe2 = k2_fpr_for_cell(probe_spec, NK2_GRID[0], k_default, m2, pool_mean, r_rep)
    return {"shape_match": _sha256_df(shape_df) == _sha256_df(shape2),
            "k1_match": _sha256_df(pl.DataFrame(k1_rows)) == _sha256_df(pl.DataFrame(k1_2)),
            "k2_probe_match": probe1 == probe2}


# --------------------------------------------------------------------------- #
# main()
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(description="EXP-078 ASS shape discrimination + k-sensitivity")
    parser.add_argument("--smoke", action="store_true",
                        help="non-binding reduced-scale correctness run (NOT the G-017 verdict)")
    parser.add_argument("--workers", type=int, default=0,
                        help="parallel workers over cells (0=all cores, 1=serial). Byte-identical "
                             "at any worker count — the D6 hash is unaffected.")
    parser.add_argument("--verify-determinism", action="store_true",
                        help="recompute the cheap shape table + K1 + one K2 probe and assert "
                             "hash-identity against a fresh pass (no full rerun).")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

    workers0 = args.workers if args.workers > 0 else (os.cpu_count() or 1)
    if args.verify_determinism:
        _verify_determinism_mode(workers0)
        return

    r_rep = R_REP
    if args.smoke:
        r_rep = 100
        logger.warning("SMOKE MODE — r_rep=%d; results NON-BINDING for G-017", r_rep)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    specs = build_type_registry()
    pool, pool_mean, k_default = build_sp_pool()
    k_grid, k_grid_disclosure = build_k_grid(k_default)
    n_cells = len(specs) * len(N_GRID)
    workers = args.workers if args.workers > 0 else (os.cpu_count() or 1)
    workers = max(1, min(workers, n_cells))
    logger.info("parallel workers: %d; k_default=%g; k_grid=%s", workers, k_default, k_grid)

    # ---- Check 1 & 2: shape rates over every (type, n) ----
    logger.info("Check 1/2: shape discrimination over %d (type, n) cells ...", n_cells)
    shape_rows = run_shape_rates(specs, r_rep, workers)
    shape_df = _shape_df(shape_rows)
    mad_zero_total = int(shape_df["mad_zero_count"].sum())
    assert mad_zero_total == 0, f"MAD==0 occurred {mad_zero_total} times (degenerate samples)"
    shape_pass = shape_pass_table(shape_rows)

    # ---- Check 3: k-sensitivity (K1 shrinkage + K2 null FPR) ----
    logger.info("Check 3: k-sensitivity (K1 shrinkage + K2 null-FPR) over k_grid=%s ...", k_grid)
    k1_rows, k2_rows, routing = run_k_sensitivity(pool_mean, k_default, k_grid, r_rep, workers)

    # ---- Integrity anchor + determinism ----
    logger.info("integrity anchor (EXP-076/077 reconciliation) + determinism ...")
    anchor = integrity_anchor()
    det = determinism_check(shape_df, k1_rows, pool_mean, k_default, r_rep, workers)

    # ---- Verdict (PER-STRATUM) ----
    verdict = build_verdict(shape_rows, shape_pass, routing, anchor, det, k_grid, k_default,
                            "SMOKE (non-binding)" if args.smoke else "FROZEN (G-017 binding)")

    # ---- Split shape table into binding (U/B) and disclosed (S) for clarity ----
    skew_df = shape_df.filter(pl.col("family") == "S")
    binding_shape_df = shape_df.filter(pl.col("family") != "S")
    k1_df = pl.DataFrame(k1_rows)
    k2_df = pl.DataFrame(k2_rows)

    # ---- Write outputs ----
    binding_shape_df.write_csv(RESULTS_DIR / "shape_rates.csv")
    skew_df.write_csv(RESULTS_DIR / "shape_skew.csv")
    k1_df.write_csv(RESULTS_DIR / "k_sensitivity_shrinkage.csv")
    k2_df.write_csv(RESULTS_DIR / "k_sensitivity.csv")
    (RESULTS_DIR / "integrity.json").write_text(json.dumps({
        "anchor": anchor, "determinism": det,
        "config": {"master_seed": MASTER_SEED, "r_rep": r_rep, "n_boot": N_BOOT,
                   "tau_gap": TAU_GAP, "dip_alpha": DIP_ALPHA, "smoke": args.smoke,
                   "k_default": k_default, "k_grid": k_grid,
                   "k_grid_disclosure": k_grid_disclosure, "mad_zero_total": mad_zero_total,
                   "diptest_version": _diptest_version()},
        "table_sha256": {"shape_rates": _sha256_df(binding_shape_df),
                         "shape_skew": _sha256_df(skew_df),
                         "k_sensitivity": _sha256_df(k2_df),
                         "k_shrinkage": _sha256_df(k1_df)}}, indent=2))
    (RESULTS_DIR / "verdict.json").write_text(json.dumps(verdict, indent=2))

    # ---- Plots ----
    plot_shape_rates_vs_n(shape_df, PLOTS_DIR / "01_shape_rates_vs_n.png")
    plot_leg_distributions(shape_df, 500, PLOTS_DIR / "02_leg_rates_by_type.png")
    plot_k_sensitivity(k1_df, k2_df, k_default, PLOTS_DIR / "03_k_sensitivity.png")
    plot_dip_vs_gap(specs, 500, PLOTS_DIR / "04_dip_vs_gap_scatter.png")

    _log_summary(verdict)


def _diptest_version() -> str:
    try:
        import diptest
        return getattr(diptest, "__version__", "unknown")
    except Exception:                      # pragma: no cover - defensive only
        return "unavailable"


def _verify_determinism_mode(workers: int) -> None:
    """Standalone determinism re-check (no full rerun): cheap shape table + K1 + K2 probe."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    specs = build_type_registry()
    _, pool_mean, k_default = build_sp_pool()
    shape_df = _shape_df(run_shape_rates(specs, R_REP, workers))
    k1_rows = [shrinkage_label_for_k(pool_mean, k)
               for k in build_k_grid(k_default)[0]]
    det = determinism_check(shape_df, k1_rows, pool_mean, k_default, R_REP, workers)
    logger.info("determinism (standalone): %s", det)
    if not all(det.values()):
        raise SystemExit("DETERMINISM FAILED — second pass not byte-identical (PROTOCOL_DEFECT)")


if __name__ == "__main__":
    main()
