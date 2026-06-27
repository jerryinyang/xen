"""
Experiment EXP-076: `ASS`/VAL-001 — Synthetic-Substrate Recovery (Phase 017 G-017a).
Implements the analysis plan from analysis-plan.md.

Validates that the `ASS` qualifier's estimator core (xen.ass) recovers ground truth on
synthetic populations with KNOWN expectancy / median / shape, produces calibrated 90%
bootstrap CIs, and shrinks sparse types toward the pooled prior as designed. Three frozen
D2.1 checks, judged mechanically against fixture-calibrated bands:

  Check 1 — recovery bias:   median_r |estimate - truth| <= 0.85 * SE_true(n), un-pooled,
                             expectancy AND median, every (type, n).
  Check 2 — CI coverage:     90% bootstrap CI covers truth in [0.86, 0.94] of replicates,
                             expectancy AND median, every (type, n).
  Check 3 — shrinkage:       weight = n/(n+k) monotone in n on the SP population; sparse
                             (n<=30) pull >= 0.25; rich (n>=2000) pull < 0.05.

SYNTHETIC ONLY — no market data, no Parquet load, no holdout split. Determinism (D6): every
draw seeded from (tag, type_id, n, replicate) via SeedSequence; a second pass is identical.

Run:     python python/experiments/EXP-076/code/run_experiment.py
Smoke:   python python/experiments/EXP-076/code/run_experiment.py --smoke   (non-binding)
Rebuild: python python/experiments/EXP-076/code/run_experiment.py --rebuild-verdict
         (regenerate the per-stratum results/verdict.json from existing result tables; no
         sampling/bootstrap recompute — reads recovery/coverage/shrinkage.csv + integrity.json)

VERDICT SHAPE (audit C1). The verdict is reported PER STRATUM (recovery / coverage-by-n /
shrinkage), never as a single collapsed cross-cell boolean — per the binding family doctrine
(cf-capgeo-001.md:137,204; D0 §D1 "none collapsed" / §D4 "one verdict per stratum"). A
collapsed convenience flag is retained only as an explicitly NON-BINDING disclosure.

RUNTIME NOTE. At the D0-frozen scale (R_REP=2000, N_BOOT=10_000) the per-replicate coverage
bootstrap over the full n-grid (up to n=8000) is the dominant cost and is multi-hour on a
workstation — this is inherent to the frozen recipe, not a defect (the analysis plan flagged
it as "the dominant cost"). The frozen constants are surfaced below; reducing them is a
governance (D0-amendment) decision, not a code change. The 99 (type, n) cells are each
independently seeded via rng_for(tag, type_id, n, replicate), so they are distributed over a
process pool (--workers, default = all cores) and reassembled in canonical cell order —
byte-identical to a serial run, so the D6 determinism hash still matches at any worker count.
Parallelism only distributes order-independent work; it never alters a draw, denominator,
metric, or the determinism check. (The per-replicate bootstrap loop is deliberately NOT
collapsed/vectorized across replicates: that would change the exact RNG draws and break the
byte-identical D6 guarantee, even though it would be statistically equivalent.)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
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

logger = logging.getLogger("EXP-076")

# --------------------------------------------------------------------------- #
# Frozen constants (Phase 017 D0 §D1/§D2.1/§D3/§D6 — no change without a D0-amendment)
# --------------------------------------------------------------------------- #
MASTER_SEED = 20260620
N_GRID = (15, 30, 60, 120, 250, 500, 1000, 2000, 8000)
R_REP = 2000                 # replicate draws per (type, n)
N_BOOT = ass.N_BOOT          # 10_000
CI_ALPHA = ass.CI_ALPHA      # 0.10 -> 90% CI
N_GROUND = 10_000_000        # MC draws for ground-truth median / sigma cross-check
N_MED_SE = 10_000            # draws for the MC median standard error per (type, n)
RECOVERY_FACTOR = 0.85       # band = 0.85 * SE_true(n) (bite-recalibrated 2026-06-20)
COVERAGE_BAND = (0.86, 0.94)
SPARSE_N = 30                # n <= SPARSE_N -> sparse member (pull >= 0.25)
RICH_N = 2000                # n >= RICH_N   -> rich member  (pull < 0.05)
SPARSE_PULL_MIN = 0.25
RICH_PULL_MAX = 0.05
SIGMA_MC_TOL = 0.01          # closed-form sigma must agree with MC to <= 1%
PULL_EPS = 1e-9              # guard for |prior - raw| ~ 0 in the empirical pull ratio
KDE_GAP_FLAG = 0.02          # |kde - direct| expectancy gap flag (fraction of sigma)
ANCHOR_TYPE, ANCHOR_N, ANCHOR_REP = "U2", 250, 0   # R3 integrity anchor cell

# Deterministic RNG stream tags (keep streams disjoint; D6 / plan R4)
TAG_SAMPLE, TAG_BOOT, TAG_GT, TAG_MEDSE, TAG_SP = 1, 2, 3, 4, 6


def rng_for(*key: int) -> np.random.Generator:
    """Deterministic generator seeded by (MASTER_SEED, *key) via SeedSequence."""
    return np.random.default_rng(np.random.SeedSequence([MASTER_SEED, *(int(k) for k in key)]))


# --------------------------------------------------------------------------- #
# Synthetic data-generating processes (D1; reuse the bite_check.py samplers)
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
# Type registry (frozen D1) — closed-form mean/sigma; median closed-form (U) or MC
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class TypeSpec:
    """One synthetic signal type: integer id (seeding), family, sampler, closed forms."""

    label: str
    type_id: int
    family: str                               # "U" | "S" | "B"
    draw: Callable[[object, np.random.Generator], np.ndarray]
    mean_truth: float
    sigma_closed: float
    median_closed: float | None               # closed-form median (U) or None -> MC


def _skew_mean_sigma(omega: float, alpha: float, xi: float) -> tuple[float, float]:
    delta = alpha / np.sqrt(1.0 + alpha * alpha)
    mean = xi + omega * delta * np.sqrt(2.0 / np.pi)
    var = omega * omega * (1.0 - 2.0 * delta * delta / np.pi)
    return float(mean), float(np.sqrt(var))


def _bimodal_mean_sigma(w, mu1, s1, mu2, s2) -> tuple[float, float]:
    mean = w * mu1 + (1.0 - w) * mu2
    ex2 = w * (mu1 * mu1 + s1 * s1) + (1.0 - w) * (mu2 * mu2 + s2 * s2)
    return float(mean), float(np.sqrt(ex2 - mean * mean))


def build_type_registry() -> dict[str, TypeSpec]:
    """Construct the frozen D1 type registry with closed-form moments."""
    specs: dict[str, TypeSpec] = {}
    for label, tid, mu in [("U0", 0, 0.0), ("U1", 1, 0.05), ("U2", 2, 0.10), ("U3", 3, 0.20)]:
        specs[label] = TypeSpec(label, tid, "U",
                                lambda sz, rng, m=mu: gen_unimodal(m, sz, rng),
                                mu, 1.0, mu)
    # DISCLOSURE (Stage-4 governance item). The frozen D1 (xi, omega, alpha) parametrization
    # is authoritative for ground truth (scope: "ground truth closed-form/MC from the DGP";
    # matches bite_check.py). The D1 *informal* "~mean/~median" annotations for the two
    # LEFT-skew members are inconsistent with these params: SN(0.55,1,-4) computes
    # median -0.124 / mean -0.224 (annotated "+0.17 / -0.07"), and Sminus0's "mean~0 &
    # median+0.24" is internally impossible for SN(-4), where mean-median is fixed at -0.0998
    # (so mean~0 forces median~+0.10, not +0.24). The two left-skew members are therefore
    # median-NEGATIVE; Splus (right-skew) remains median-POSITIVE (median +0.674) -- it is not
    # the whole S family that flips sign, only the left-skew members. They do retain
    # median > mean (the dangerous ordering), but the median-positive / mean<=0 trap is
    # realized by the B family, not S. This does NOT affect recovery validity (an unbiased
    # estimator recovers the true value of whatever DGP is frozen; the "~mean/~median" text is
    # never read by any computation) but is surfaced for operator adjudication, not fixed here
    # (changing xi would require a D0-amendment).
    skews = [("Splus", 10, 0.0, 1.0, 4.0), ("Sminus", 11, 0.55, 1.0, -4.0),
             ("Sminus0", 12, 0.62, 1.0, -4.0)]
    for label, tid, xi, omega, alpha in skews:
        mean, sigma = _skew_mean_sigma(omega, alpha, xi)
        specs[label] = TypeSpec(label, tid, "S",
                                lambda sz, rng, p=(xi, omega, alpha): gen_skewnormal(
                                    p[0], p[1], p[2], sz, rng),
                                mean, sigma, None)
    bis = [("B_neg", 20, 0.85, 0.15, 0.5, -2.0, 0.6),
           ("B_zero", 21, 0.90, 0.15, 0.5, -1.5, 0.6),
           ("B_pos", 22, 0.95, 0.10, 0.5, -1.0, 0.6),
           ("B_strong", 23, 0.80, 0.20, 0.5, -2.0, 0.6)]
    for label, tid, w, mu1, s1, mu2, s2 in bis:
        mean, sigma = _bimodal_mean_sigma(w, mu1, s1, mu2, s2)
        specs[label] = TypeSpec(label, tid, "B",
                                lambda sz, rng, p=(w, mu1, s1, mu2, s2): gen_bimodal(
                                    p[0], p[1], p[2], p[3], p[4], sz, rng),
                                mean, sigma, None)
    return specs


# SP shrinkage population (D1): mixed-n members, median n = 120 -> k = median-n = 120.
SP_MEMBERS = (
    (0, "U0", 15), (1, "Splus", 30), (2, "B_neg", 60), (3, "U2", 120), (4, "Sminus", 120),
    (5, "B_zero", 250), (6, "U3", 500), (7, "B_strong", 2000), (8, "Splus", 8000),
)


# --------------------------------------------------------------------------- #
# Ground truth (closed-form moments + MC median + MC median SE)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class GroundTruth:
    mean_truth: float
    sigma_type: float          # closed-form SD (expectancy SE denominator: sigma/sqrt(n))
    sigma_mc: float            # MC cross-check of sigma_type
    median_truth: float        # closed-form (U) or 10^7-draw MC
    median_se: dict[int, float]  # MC median SE per n (SD of sample median over N_MED_SE)


def median_se_for_n(spec: TypeSpec, n: int, n_med_se: int) -> float:
    """SD of the size-``n`` sample median over ``n_med_se`` independent draws (D6 seeded)."""
    rng = rng_for(TAG_MEDSE, spec.type_id, n)
    meds = np.empty(n_med_se, dtype=np.float64)
    done = 0
    batch = max(1, min(n_med_se, 2_000_000 // max(1, n)))   # bound memory by ~2M cells
    while done < n_med_se:
        b = min(batch, n_med_se - done)
        meds[done:done + b] = np.median(spec.draw((b, n), rng), axis=1)
        done += b
    return float(np.std(meds, ddof=1))


def compute_ground_truth(specs: dict[str, TypeSpec], n_ground: int,
                         n_med_se: int) -> dict[str, GroundTruth]:
    """Closed-form moments + 10^7-draw MC median/sigma + per-n MC median SE (D6 seeded)."""
    gt: dict[str, GroundTruth] = {}
    for label, spec in tqdm(specs.items(), desc="ground-truth"):
        big = spec.draw(n_ground, rng_for(TAG_GT, spec.type_id))
        sigma_mc = float(np.std(big, ddof=1))
        median_truth = spec.median_closed if spec.median_closed is not None \
            else float(np.median(big))
        rel = abs(sigma_mc - spec.sigma_closed) / max(spec.sigma_closed, 1e-12)
        if rel > SIGMA_MC_TOL:
            logger.warning("%s closed-form sigma %.5f vs MC %.5f (rel %.3f > %.2f)",
                           label, spec.sigma_closed, sigma_mc, rel, SIGMA_MC_TOL)
        se = {n: median_se_for_n(spec, n, n_med_se) for n in N_GRID}
        gt[label] = GroundTruth(spec.mean_truth, spec.sigma_closed, sigma_mc,
                                median_truth, se)
    return gt


# --------------------------------------------------------------------------- #
# Pure computation — per-cell replicate samples + Checks 1 & 2
# --------------------------------------------------------------------------- #
def draw_cell_samples(spec: TypeSpec, n: int, n_rep: int) -> np.ndarray:
    """Stack ``n_rep`` size-``n`` replicate samples; per-replicate seed (D6 / R4)."""
    out = np.empty((n_rep, n), dtype=np.float64)
    for rep in range(n_rep):
        out[rep] = spec.draw(n, rng_for(TAG_SAMPLE, spec.type_id, n, rep))
    return out


def recovery_for_cell(samples: np.ndarray, gt: GroundTruth, label: str, n: int) -> list[dict]:
    """Check 1 rows: median |estimate - truth| vs 0.85*SE for expectancy and median."""
    exp_est = samples.mean(axis=1)                       # un-pooled direct expectancy
    med_est = np.median(samples, axis=1)                 # un-pooled empirical median
    rows = []
    for estimand, est, truth, se in [
        ("expectancy", exp_est, gt.mean_truth, gt.sigma_type / np.sqrt(n)),
        ("median", med_est, gt.median_truth, gt.median_se[n]),
    ]:
        bias_med = float(np.median(np.abs(est - truth)))
        signed = float(np.mean(est - truth))
        band = RECOVERY_FACTOR * se
        rows.append({"type": label, "n": n, "estimand": estimand, "truth": truth,
                     "bias_med": bias_med, "signed_bias": signed, "se_true": se,
                     "band": band, "pass": bool(bias_med <= band)})
    return rows


def coverage_for_cell(samples: np.ndarray, gt: GroundTruth, spec: TypeSpec,
                      n: int, n_boot: int) -> list[dict]:
    """Check 2 rows: fraction of replicate 90% bootstrap CIs covering truth."""
    n_rep = samples.shape[0]
    cov_exp = cov_med = 0
    for rep in range(n_rep):
        ci = ass.bootstrap_cis(samples[rep], rng_for(TAG_BOOT, spec.type_id, n, rep),
                               n_boot=n_boot, alpha=CI_ALPHA)
        cov_exp += int(ci.expectancy_lo <= gt.mean_truth <= ci.expectancy_hi)
        cov_med += int(ci.median_lo <= gt.median_truth <= ci.median_hi)
    mc_band = 1.96 * np.sqrt(0.90 * 0.10 / n_rep)
    rows = []
    for estimand, cov in [("expectancy", cov_exp / n_rep), ("median", cov_med / n_rep)]:
        rows.append({"type": spec.label, "n": n, "estimand": estimand,
                     "coverage": cov, "mc_band": float(mc_band),
                     "pass": bool(COVERAGE_BAND[0] <= cov <= COVERAGE_BAND[1])})
    return rows


# --------------------------------------------------------------------------- #
# Pure computation — Check 3 (SP shrinkage behaviour)
# --------------------------------------------------------------------------- #
def shrinkage_check(specs: dict[str, TypeSpec]) -> tuple[list[dict], float]:
    """Check 3 rows on the SP population; returns (rows, k_shrink)."""
    draws = {midx: specs[lbl].draw(n, rng_for(TAG_SP, midx, n))
             for midx, lbl, n in SP_MEMBERS}
    pool = np.concatenate([draws[midx] for midx, _, _ in SP_MEMBERS])
    pool_mean = float(np.mean(pool))
    k_shrink = float(np.median([n for _, _, n in SP_MEMBERS]))     # median-n -> k
    rows = []
    for midx, lbl, n in SP_MEMBERS:
        raw = float(np.mean(draws[midx]))
        weight = ass.shrinkage_weight(n, k_shrink)
        shrunk = weight * raw + (1.0 - weight) * pool_mean
        pull_theory = 1.0 - weight                                 # k / (n + k)
        denom = abs(pool_mean - raw)
        pull_emp = abs(shrunk - raw) / denom if denom > PULL_EPS else 0.0
        sparse_ok = (n > SPARSE_N) or (pull_theory >= SPARSE_PULL_MIN)
        rich_ok = (n < RICH_N) or (pull_theory < RICH_PULL_MAX)
        rows.append({"member": midx, "type": lbl, "n": n, "weight": weight,
                     "pull_theory": pull_theory, "pull_emp": pull_emp,
                     "sparse_ok": bool(sparse_ok), "rich_ok": bool(rich_ok),
                     "marginal_flag": bool(n >= RICH_N and not rich_ok)})
    return rows, k_shrink


# --------------------------------------------------------------------------- #
# Pure computation — integrity anchor (R3)
# --------------------------------------------------------------------------- #
def integrity_anchor(specs: dict[str, TypeSpec], gt: dict[str, GroundTruth]) -> dict:
    """R3: un-pooled direct expectancy == numpy.mean (<=1e-12); KDE-vs-direct gap report."""
    spec = specs[ANCHOR_TYPE]
    x = spec.draw(ANCHOR_N, rng_for(TAG_SAMPLE, spec.type_id, ANCHOR_N, ANCHOR_REP))
    s = ass.score(x, shrink=False, compute_kde_expectancy=True)
    direct = s.expectancy_direct
    npmean = float(np.mean(x))
    anchor_diff = abs(direct - npmean)
    sigma = gt[ANCHOR_TYPE].sigma_type
    kde_gap = abs(s.expectancy_kde - direct)
    return {
        "anchor_cell": f"{ANCHOR_TYPE}/n={ANCHOR_N}/rep={ANCHOR_REP}",
        "direct_expectancy": direct, "numpy_mean": npmean,
        "anchor_abs_diff": anchor_diff, "anchor_pass": bool(anchor_diff <= 1e-12),
        "kde_integrated_expectancy": s.expectancy_kde,
        "kde_vs_direct_gap": kde_gap, "kde_gap_bound": KDE_GAP_FLAG * sigma,
        "kde_gap_flagged": bool(kde_gap > KDE_GAP_FLAG * sigma),
    }


# --------------------------------------------------------------------------- #
# Plotting (4) — consume bounded result tables, no heavy recompute
# --------------------------------------------------------------------------- #
def _bias_plot(rec: pl.DataFrame, estimand: str, title: str, path: Path) -> None:
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 6))
    sub = rec.filter(pl.col("estimand") == estimand)
    for label in sorted(sub["type"].unique().to_list()):
        d = sub.filter(pl.col("type") == label).sort("n")
        ax.plot(d["n"], d["bias_med"] / d["se_true"], marker="o", label=label, alpha=0.8)
    ax.axhline(RECOVERY_FACTOR, color="red", ls="--", label=f"band {RECOVERY_FACTOR}*SE")
    ax.set_xscale("log")
    ax.set_title(title, fontsize=12)
    ax.set_xlabel("n (log)")
    ax.set_ylabel("median |estimate - truth| / SE_true")
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_coverage(cov: pl.DataFrame, path: Path) -> None:
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), sharey=True)
    for ax, estimand in zip(axes, ["expectancy", "median"]):
        sub = cov.filter(pl.col("estimand") == estimand)
        for label in sorted(sub["type"].unique().to_list()):
            d = sub.filter(pl.col("type") == label).sort("n")
            ax.plot(d["n"], d["coverage"], marker="o", label=label, alpha=0.8)
        ax.axhspan(COVERAGE_BAND[0], COVERAGE_BAND[1], color="green", alpha=0.12)
        ax.axhline(0.90, color="grey", ls=":")
        ax.set_xscale("log")
        ax.set_title(f"CI coverage — {estimand}")
        ax.set_xlabel("n (log)")
    axes[0].set_ylabel("coverage")
    axes[0].legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_shrinkage(shr: pl.DataFrame, path: Path) -> None:
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 6))
    d = shr.sort("n")
    ax.plot(d["n"], d["weight"], marker="o", label="weight n/(n+k)")
    ax.plot(d["n"], d["pull_theory"], marker="s", label="pull (1-weight)")
    ax.axhline(SPARSE_PULL_MIN, color="orange", ls="--", label=f"sparse pull >= {SPARSE_PULL_MIN}")
    ax.axhline(RICH_PULL_MAX, color="red", ls="--", label=f"rich pull < {RICH_PULL_MAX}")
    for row in d.filter(pl.col("marginal_flag")).iter_rows(named=True):
        ax.annotate(f"marginal n={row['n']}\npull={row['pull_theory']:.4f}",
                    (row["n"], row["pull_theory"]), textcoords="offset points",
                    xytext=(8, 12), fontsize=8, color="red")
    ax.set_xscale("log")
    ax.set_title("SP shrinkage weight & pull vs n (k = median-n)", fontsize=12)
    ax.set_xlabel("n (log)")
    ax.set_ylabel("weight / pull")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration helpers
# --------------------------------------------------------------------------- #
def _sha256_df(df: pl.DataFrame) -> str:
    return hashlib.sha256(df.write_csv().encode()).hexdigest()


def _cell_task(task: tuple) -> tuple[list[dict], list[dict]]:
    """Compute one (type, n) cell (Check 1 + optional Check 2).

    Top-level and self-contained so it is picklable for ``ProcessPoolExecutor``: the type
    registry is rebuilt locally (cheap, deterministic) rather than shipping the lambda-bearing
    ``TypeSpec`` across the process boundary, and only the cell's ``GroundTruth`` is passed.
    Output is byte-identical to the serial path because every draw is seeded by
    ``rng_for(tag, type_id, n, replicate)`` — independent of which worker or order runs it.
    """
    label, n, gt_cell, r_rep, n_boot, do_coverage = task
    spec = build_type_registry()[label]
    samples = draw_cell_samples(spec, n, r_rep)
    rec = recovery_for_cell(samples, gt_cell, label, n)
    cov = coverage_for_cell(samples, gt_cell, spec, n, n_boot) if do_coverage else []
    return rec, cov


def run_recovery_and_coverage(specs, gt, recovery_types, n_grid, r_rep, n_boot,
                              do_coverage: bool, workers: int = 1) -> tuple[list[dict], list[dict]]:
    """Single pass over (type, n) cells: draw once, compute Check 1 (+ Check 2).

    Cells are independently seeded, so with ``workers > 1`` they run across a process pool and
    are reassembled in canonical cell order (``Executor.map`` preserves input order) — the
    emitted tables and their D6 hashes are identical to the serial (``workers == 1``) path.
    Parallelism distributes only order-independent work; it never changes a draw, denominator,
    metric, or the determinism check.
    """
    cells = [(lbl, n) for lbl in recovery_types for n in n_grid]
    tasks = [(lbl, n, gt[lbl], r_rep, n_boot, do_coverage) for lbl, n in cells]
    rec_rows, cov_rows = [], []
    if workers <= 1:
        for task in tqdm(tasks, desc="recovery/coverage cells"):
            rec, cov = _cell_task(task)
            rec_rows.extend(rec)
            cov_rows.extend(cov)
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for rec, cov in tqdm(ex.map(_cell_task, tasks), total=len(tasks),
                                 desc=f"recovery/coverage cells (x{workers})"):
                rec_rows.extend(rec)
                cov_rows.extend(cov)
    return rec_rows, cov_rows


# --------------------------------------------------------------------------- #
# Verdict assembly (PER-STRATUM — pure function of the result tables)
# --------------------------------------------------------------------------- #
def build_verdict(rec_df: pl.DataFrame, cov_df: pl.DataFrame, shr_df: pl.DataFrame,
                  anchor: dict, det: dict, k_shrink: float, scale_label: str) -> dict:
    """Assemble the per-stratum G-017a verdict from the per-cell result tables.

    Pure function of the emitted tables (no draws / bootstrap). Per the binding family doctrine
    (``cf-capgeo-001.md:137,204``; D0 §D1 "none collapsed" / §D4 "one verdict per stratum") the
    verdict is reported per stratum and is **never** collapsed into a single cross-cell/cross-check
    boolean: recovery, coverage, and shrinkage each carry their own verdict, and coverage is
    resolved per-``n`` (not AND-ed across ``n``). A collapsed convenience flag is retained only as
    an explicitly non-binding disclosure.

    Parameters
    ----------
    rec_df, cov_df, shr_df : pl.DataFrame
        The recovery / coverage / shrinkage per-cell tables (``cov_df`` may be empty if coverage
        was skipped).
    anchor, det : dict
        The integrity anchor and determinism blocks (recomputed in-run or read from
        ``integrity.json`` on rebuild).
    k_shrink : float
        The shrinkage constant ``k`` (median-``n``).
    scale_label : str
        Run-scale label for disclosure (frozen vs smoke).

    Returns
    -------
    dict
        The per-stratum verdict object written to ``results/verdict.json``.
    """
    # ---- Recovery stratum (binding; every (type, n) cell) ----
    ratio = rec_df.with_columns((pl.col("bias_med") / pl.col("se_true")).alias("ratio"))
    rec_fail = rec_df.filter(~pl.col("pass"))
    worst_ratio = {est: float(ratio.filter(pl.col("estimand") == est)["ratio"].max())
                   for est in sorted(ratio["estimand"].unique().to_list())}
    recovery = {
        "verdict": "PASS" if rec_fail.height == 0 else "FAIL",
        "binding": True,
        "n_cells": rec_df.height,
        "n_fail": rec_fail.height,
        "worst_ratio_vs_band_0p85": worst_ratio,
        "failing_cells": rec_fail.select(["type", "n", "estimand"]).to_dicts(),
        "note": "median |estimate - truth| <= 0.85*SE_true on every (type, n), expectancy and median",
    }

    # ---- Coverage stratum (resolved per-n; NOT collapsed across n) ----
    if cov_df.height == 0:
        coverage: dict = {"status": "SKIPPED (--no-coverage); not evaluated", "binding": False}
        cov_pass_collapsed: bool | None = None
    else:
        by_n: dict[str, dict] = {}
        for n in sorted(cov_df["n"].unique().to_list()):
            sub = cov_df.filter(pl.col("n") == n)
            exp = sub.filter(pl.col("estimand") == "expectancy")
            med = sub.filter(pl.col("estimand") == "median")
            by_n[str(n)] = {
                "expectancy_pass": bool(exp["pass"].all()),
                "median_pass": bool(med["pass"].all()),
                "expectancy_min_cov": float(exp["coverage"].min()),
                "median_min_cov": float(med["coverage"].min()),
                "expectancy_fail_types": exp.filter(~pl.col("pass"))["type"].to_list(),
            }
        ge30_fail = cov_df.filter((pl.col("n") >= 30) & (~pl.col("pass")))
        small_fail = cov_df.filter((pl.col("n") < 30) & (~pl.col("pass")))
        coverage = {
            "by_n": by_n,
            "verdict_n_ge_30": "PASS" if ge30_fail.height == 0 else "FAIL",
            "binding_boundary": ("n>=30 binding; n<30 = sparse-stress diagnostic — PENDING "
                                 "D0-amendment ratification (not prejudged here)"),
            "sparse_stress_diagnostic": {
                "description": ("sub-band cells are the small-sample percentile-bootstrap floor of "
                                "the MEAN (expectancy); median coverage is in-band. Disclosed "
                                "diagnostic, not a binding fail — see audit.md mechanism."),
                "failing_cells": small_fail.select(
                    ["type", "n", "estimand", "coverage"]).to_dicts(),
            },
            "binding": True,
        }
        cov_pass_collapsed = bool(cov_df["pass"].all())

    # ---- Shrinkage stratum (binding; SP population) ----
    monotone = bool(np.all(np.diff(shr_df.sort("n")["weight"].to_numpy()) >= -1e-12))
    sparse_pass = bool(shr_df["sparse_ok"].all())
    rich_literal_pass = bool(shr_df["rich_ok"].all())
    shrinkage = {
        "monotone": monotone,
        "sparse_pull_pass": sparse_pass,
        "rich": {
            "verdict": "PASS" if rich_literal_pass else "PASS except predeclared n=2000 marginal",
            "literal_pass": rich_literal_pass,
            "marginals": shr_df.filter(pl.col("marginal_flag")).to_dicts(),
            "note": ("predeclared analytic k/(n+k) marginal (~0.0566 at n=2000, k=120); surfaced "
                     "for governance, not silently passed" if not rich_literal_pass
                     else "all literal rich bounds clear"),
        },
        "binding": True,
    }

    # ---- Collapsed convenience flag (NON-BINDING disclosure only) ----
    collapsed_value = (recovery["verdict"] == "PASS" and monotone and sparse_pass
                       and all(det.values()) and bool(anchor["anchor_pass"])
                       and (cov_pass_collapsed in (True, None)))

    return {
        "scale": scale_label,
        "doctrine": ("PER-STRATUM adjudication (cf-capgeo-001.md:137,204; D0 §D1 'none collapsed' / "
                     "§D4 'one verdict per stratum'). Each stratum below carries its own verdict; "
                     "coverage is resolved per-n. No collapsed cross-cell verdict is binding and no "
                     "cross-cell homogeneity is claimed."),
        "strata": {"recovery": recovery, "coverage": coverage, "shrinkage": shrinkage},
        "integrity": {
            "anchor_pass": bool(anchor["anchor_pass"]),
            "kde_gap_flagged": bool(anchor["kde_gap_flagged"]),
            "determinism": det,
        },
        "k_shrink": k_shrink,
        "collapsed_convenience_flag": {
            "value": bool(collapsed_value),
            "caveat": ("NON-BINDING. Collapsed cross-cell/cross-check AND retained for convenience "
                       "only; NOT the verdict. The per-stratum verdicts above are binding. No "
                       "cross-cell homogeneity is claimed (cf-capgeo-001.md:137)."),
        },
    }


def _log_verdict_summary(verdict: dict) -> None:
    """Concise per-stratum console summary (no single collapsed pass/fail headline)."""
    s = verdict["strata"]
    rec = s["recovery"]
    logger.info("STRATUM recovery: %s (%d cells, %d fail; worst ratio %s vs 0.85)",
                rec["verdict"], rec["n_cells"], rec["n_fail"], rec["worst_ratio_vs_band_0p85"])
    cov = s["coverage"]
    if "by_n" in cov:
        n_small = len(cov["sparse_stress_diagnostic"]["failing_cells"])
        logger.info("STRATUM coverage: n>=30 %s; sparse-stress diagnostic cells=%d "
                    "(binding boundary pending governance)", cov["verdict_n_ge_30"], n_small)
    else:
        logger.info("STRATUM coverage: %s", cov["status"])
    sh = s["shrinkage"]
    logger.info("STRATUM shrinkage: monotone=%s sparse_pull=%s rich=%s",
                sh["monotone"], sh["sparse_pull_pass"], sh["rich"]["verdict"])
    integ = verdict["integrity"]
    logger.info("integrity: anchor_pass=%s kde_gap_flagged=%s determinism=%s",
                integ["anchor_pass"], integ["kde_gap_flagged"], integ["determinism"])
    logger.info("collapsed_convenience_flag=%s (NON-BINDING — see results/verdict.json strata)",
                verdict["collapsed_convenience_flag"]["value"])


def rebuild_verdict_from_results() -> None:
    """Regenerate ``results/verdict.json`` (per-stratum) from existing hash-verified tables.

    Reads ``recovery/coverage/shrinkage.csv`` + ``integrity.json`` (its recorded ``anchor`` and
    ``determinism`` blocks) and rewrites **only** ``verdict.json``. No sampling, bootstrap,
    ground-truth, CSV, or plot recompute — the binding multi-hour computation is never re-run.
    """
    required = ["recovery.csv", "coverage.csv", "shrinkage.csv", "integrity.json"]
    missing = [f for f in required if not (RESULTS_DIR / f).exists()]
    if missing:
        raise SystemExit(f"--rebuild-verdict: missing results artifacts {missing} in {RESULTS_DIR}")
    rec_df = pl.read_csv(RESULTS_DIR / "recovery.csv")
    cov_df = pl.read_csv(RESULTS_DIR / "coverage.csv")
    shr_df = pl.read_csv(RESULTS_DIR / "shrinkage.csv")
    integ = json.loads((RESULTS_DIR / "integrity.json").read_text())
    scale_label = ("SMOKE (non-binding)" if integ.get("config", {}).get("smoke")
                   else "FROZEN (G-017a binding)")
    k_shrink = float(np.median([n for _, _, n in SP_MEMBERS]))
    verdict = build_verdict(rec_df, cov_df, shr_df, integ["anchor"], integ["determinism"],
                            k_shrink, scale_label)
    (RESULTS_DIR / "verdict.json").write_text(json.dumps(verdict, indent=2))
    logger.info("--rebuild-verdict: regenerated results/verdict.json (per-stratum) from existing "
                "tables; CSVs/integrity/plots untouched, no recompute")
    _log_verdict_summary(verdict)


# --------------------------------------------------------------------------- #
# main()
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(description="EXP-076 ASS synthetic-substrate recovery")
    parser.add_argument("--smoke", action="store_true",
                        help="non-binding reduced-scale correctness run (NOT the G-017a verdict)")
    parser.add_argument("--no-coverage", action="store_true",
                        help="skip the expensive Check-2 coverage pass (Checks 1 & 3 only)")
    parser.add_argument("--workers", type=int, default=0,
                        help="parallel worker processes over the (type, n) cells "
                             "(0 = all cores; 1 = serial). Output is byte-identical at any "
                             "worker count — the D6 determinism hash is unaffected.")
    parser.add_argument("--rebuild-verdict", action="store_true",
                        help="regenerate results/verdict.json (per-stratum) from existing "
                             "result tables; no sampling/bootstrap recompute.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

    if args.rebuild_verdict:
        rebuild_verdict_from_results()
        return

    r_rep, n_boot, n_ground, n_med_se = R_REP, N_BOOT, N_GROUND, N_MED_SE
    if args.smoke:
        r_rep, n_boot, n_ground, n_med_se = 50, 500, 100_000, 500
        logger.warning("SMOKE MODE — reduced scale; results are NON-BINDING for G-017a")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    specs = build_type_registry()
    recovery_types = [s.label for s in specs.values()]            # all 11 U/S/B types
    n_cells = len(recovery_types) * len(N_GRID)
    workers = args.workers if args.workers > 0 else (os.cpu_count() or 1)
    workers = max(1, min(workers, n_cells))
    logger.info("parallel workers: %d over %d (type, n) cells", workers, n_cells)

    logger.info("computing ground truth (closed-form + MC median/sigma + median SE) ...")
    gt = compute_ground_truth(specs, n_ground, n_med_se)
    gt_rows = []
    for label, g in gt.items():
        for n in N_GRID:
            gt_rows.append({"type": label, "n": n, "mean_truth": g.mean_truth,
                            "sigma_type": g.sigma_type, "sigma_mc": g.sigma_mc,
                            "median_truth": g.median_truth, "median_se": g.median_se[n]})
    gt_df = pl.DataFrame(gt_rows)

    logger.info("Checks 1 & 2 over %d (type, n) cells (coverage=%s) ...",
                len(recovery_types) * len(N_GRID), not args.no_coverage)
    rec_rows, cov_rows = run_recovery_and_coverage(
        specs, gt, recovery_types, N_GRID, r_rep, n_boot,
        do_coverage=not args.no_coverage, workers=workers)
    rec_df = pl.DataFrame(rec_rows)
    cov_df = pl.DataFrame(cov_rows) if cov_rows else pl.DataFrame(
        schema={"type": pl.String, "n": pl.Int64, "estimand": pl.String,
                "coverage": pl.Float64, "mc_band": pl.Float64, "pass": pl.Boolean})

    logger.info("Check 3 (SP shrinkage behaviour) ...")
    shr_rows, k_shrink = shrinkage_check(specs)
    shr_df = pl.DataFrame(shr_rows)

    logger.info("integrity anchor (R3) + determinism check ...")
    anchor = integrity_anchor(specs, gt)
    # Determinism (D6): recompute the cheap point-estimate tables and hash-compare.
    rec2, _ = run_recovery_and_coverage(specs, gt, recovery_types, N_GRID, r_rep, n_boot,
                                        do_coverage=False, workers=workers)
    shr2, _ = shrinkage_check(specs)
    det = {"recovery_match": _sha256_df(rec_df) == _sha256_df(pl.DataFrame(rec2)),
           "shrinkage_match": _sha256_df(shr_df) == _sha256_df(pl.DataFrame(shr2)),
           "groundtruth_match": _sha256_df(gt_df) == _sha256_df(pl.DataFrame(
               compute_ground_truth_rows(specs, n_ground, n_med_se)))}

    # ---- Verdict (PER-STRATUM, D2.1; see build_verdict / audit C1) ----
    verdict = build_verdict(
        rec_df, cov_df, shr_df, anchor, det, k_shrink,
        "SMOKE (non-binding)" if args.smoke else "FROZEN (G-017a binding)")

    # ---- Write outputs ----
    gt_df.write_csv(RESULTS_DIR / "ground_truth.csv")
    rec_df.write_csv(RESULTS_DIR / "recovery.csv")
    cov_df.write_csv(RESULTS_DIR / "coverage.csv")
    shr_df.write_csv(RESULTS_DIR / "shrinkage.csv")
    (RESULTS_DIR / "integrity.json").write_text(json.dumps(
        {"anchor": anchor, "determinism": det,
         "config": {"master_seed": MASTER_SEED, "r_rep": r_rep, "n_boot": n_boot,
                    "n_ground": n_ground, "n_med_se": n_med_se, "smoke": args.smoke},
         "table_sha256": {"ground_truth": _sha256_df(gt_df), "recovery": _sha256_df(rec_df),
                          "coverage": _sha256_df(cov_df), "shrinkage": _sha256_df(shr_df)}},
        indent=2))
    (RESULTS_DIR / "verdict.json").write_text(json.dumps(verdict, indent=2))

    # ---- Plots ----
    _bias_plot(rec_df, "expectancy", "Expectancy recovery bias vs n (un-pooled)",
               PLOTS_DIR / "01_recovery_bias_expectancy.png")
    _bias_plot(rec_df, "median", "Median recovery bias vs n (un-pooled)",
               PLOTS_DIR / "02_recovery_bias_median.png")
    if cov_rows:
        plot_coverage(cov_df, PLOTS_DIR / "03_ci_coverage.png")
    plot_shrinkage(shr_df, PLOTS_DIR / "04_shrinkage.png")

    # ---- Console summary (per-stratum) ----
    _log_verdict_summary(verdict)


def compute_ground_truth_rows(specs, n_ground, n_med_se) -> list[dict]:
    """Determinism helper: recompute the ground-truth table as rows for hash-compare."""
    gt = compute_ground_truth(specs, n_ground, n_med_se)
    rows = []
    for label, g in gt.items():
        for n in N_GRID:
            rows.append({"type": label, "n": n, "mean_truth": g.mean_truth,
                         "sigma_type": g.sigma_type, "sigma_mc": g.sigma_mc,
                         "median_truth": g.median_truth, "median_se": g.median_se[n]})
    return rows


if __name__ == "__main__":
    main()
