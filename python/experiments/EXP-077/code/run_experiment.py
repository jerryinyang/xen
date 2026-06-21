"""
Experiment EXP-077: `ASS`/VAL-002 — Dogfood + Calibration under `WF-EXPANDING` (Phase 017).
Implements the analysis plan from analysis-plan.md.

Validates the error-control + protocol legs of G-017: under the frozen WF-EXPANDING
expanding-window walk-forward protocol (xen.wf), does the `ASS` qualifier (xen.ass) control
error and stay reliable? Five legs, all reported PER STRATUM (LESSON-001 / EXP-076 audit C1):

  Leg A — FPR (D2.2):   margin-calibrated `expectancy CI_low_1s > m` FPR <= 0.05 (Wilson-hi
                        <= 0.075) on every null stratum (U0, B_zero) AND the small-n stratum.
                        m is calibrated on TAG_CAL nulls, FPR validated on independent TAG_VAL
                        nulls (resolves the FPR<->MDE circularity). Small-n adds a single-window
                        sub-read (no folds) that directly tests the EXP-076 n<30 under-coverage.
  Leg B — MDE (D2.3):   TPR(`CI_low_1s > 0`) over a U-location mu-probe grid; MDE(N) = smallest
                        mu with TPR >= 0.80. PASS iff MDE finite/non-degenerate for every N >= 30.
  Leg C — Reliability:  P(return>X) predicted (train) vs realized (test) on held-out WF folds;
        (D2.4)          decile max-gap <= 0.10 AND calibration slope in [0.85, 1.15], per X.
  Leg D — Accounting:   xen.wf.counted_reads scenario table (D4.1) — one frozen WF run = +1
        (D4.1)          counted read; non-conforming reverts to per-fold; at-cap rejected;
                        holdout-fold rejected; rolling comparison +0. Demonstrably honors the cap.
  Leg E — Dogfood:      current-data TRAIN-only real-bar smoke (first 49% only), moving-block
        (D4.2)          bootstrap; pipeline completes, 0 counted reads, cutoff asserted in code.

SYNTHETIC + TRAIN-ONLY. No TEST stratum or holdout is ever sliced. Determinism (D6): every draw
seeded from (tag, type_id, n, replicate); a second pass of the cheap legs + an FPR/MDE probe cell
is hash-identical. The expensive FPR/MDE grid is distributed over a process pool (--workers), and
output is byte-identical at any worker count (each cell independently seeded; map preserves order).

Run:     python python/experiments/EXP-077/code/run_experiment.py
Smoke:   python python/experiments/EXP-077/code/run_experiment.py --smoke   (NON-BINDING)
No-FPR:  python python/experiments/EXP-077/code/run_experiment.py --no-fpr-mde  (Legs C/D/E only)
Rebuild: python python/experiments/EXP-077/code/run_experiment.py --rebuild-verdict
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

from xen import ass, wf
from xen.bar_aggregator import aggregate_ohlc

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
EXP_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data" / "timebars"
EXCLUDED_FILE_MARKERS = ("analysis70", "analysis_slice", "first70")

logger = logging.getLogger("EXP-077")

# --------------------------------------------------------------------------- #
# Frozen constants (Phase 017 D0 §D1/§D2/§D3/§D4/§D6 — no change without a D0-amendment)
# --------------------------------------------------------------------------- #
MASTER_SEED = 20260620
N_GRID = (15, 30, 60, 120, 250, 500, 1000, 2000, 8000)
R_REP = 2000                 # replicate series per (type, N) for FPR / MDE
N_BOOT = ass.N_BOOT          # 10_000
CI_ALPHA = ass.CI_ALPHA      # 0.10 -> 90% CI; 5th pct = one-sided 95% lower (ci_low_1s)
FPR_TARGET = 0.05            # D2.2 binding FPR
FPR_WILSON_HI = 0.075        # D2.2 Wilson upper-95% ceiling
MARGIN_Q = 0.95              # m = max(0, Q95(ci_low_1s | null))  (m_cell analog, D2.2)
TPR_FLOOR = 0.80             # D2.3 detection target
MDE_BINDING_N = 30           # MDE finiteness binding for N >= 30 (small-n = N < 30)
SMALL_N = (15, 30)           # small-n FPR stratum (single-window + WF), EXP-076 disposition (b)
MU_GRID = (0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.75, 1.00)   # U-location MDE probe grid (D1 family)
REL_TYPES = ("U0", "U2", "U3", "Splus", "Sminus", "B_neg", "B_pos")  # span P(>X) range
REL_N = (120, 500, 2000)     # reliability replicate sizes (mid/rich, fold floor reachable)
REL_DECILES = 10             # D2.4 reliability buckets
REL_MAX_GAP = 0.10           # D2.4 max |predicted - realized|
REL_SLOPE_BAND = (0.85, 1.15)  # D2.4 calibration-line slope
THRESHOLDS = ass.DEFAULT_THRESHOLDS  # X in {0, 0.05, 1.0, 2.0}
DOG_INSTRUMENTS = ("EURUSD", "XAUUSD", "BTCUSD", "USTEC")   # 4-instrument core smoke
DOG_INSTRUMENT_ID = {"EURUSD": 0, "XAUUSD": 1, "BTCUSD": 2, "USTEC": 3}  # deterministic seed id
DOG_DOMAINS = (15, 60, 240)  # 15m / 1h / 4h in minutes
DOG_MIN_COVERAGE = 0.90      # family domain-construction convention
DOG_FWD_H = 6                # forward-return horizon (bars) for the developer-defined dogfood series
DOG_ATR_PERIOD = 14          # causal ATR denominator
ANALYSIS_FRACTION = 0.7      # first 70% = analysis set
TRAIN_FRACTION = 0.7         # first 70% of analysis = TRAIN = ~49% of full
ANCHOR_TYPE, ANCHOR_N, ANCHOR_REP = "U2", 250, 0   # integrity anchor cell

# Deterministic RNG stream tags (keep streams disjoint; D6 / plan)
TAG_CAL, TAG_VAL, TAG_EFF, TAG_REL, TAG_DOG = 1, 2, 3, 4, 5


def rng_for(*key: int) -> np.random.Generator:
    """Deterministic generator seeded by (MASTER_SEED, *key) via SeedSequence."""
    return np.random.default_rng(np.random.SeedSequence([MASTER_SEED, *(int(k) for k in key)]))


def wilson_upper(k: int, n: int, z: float = 1.959963984540054) -> float:
    """Wilson score 95% upper bound for a binomial rate k/n (finite, n>=1)."""
    if n <= 0:
        return float("nan")
    p = k / n
    z2 = z * z
    centre = (p + z2 / (2 * n)) / (1 + z2 / n)
    half = (z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))) / (1 + z2 / n)
    return float(min(1.0, centre + half))


# --------------------------------------------------------------------------- #
# Synthetic data-generating processes (D1; identical to EXP-076 for cross-experiment anchoring)
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


@dataclass(frozen=True)
class TypeSpec:
    """One synthetic signal type: integer id (seeding), family, sampler, closed forms."""

    label: str
    type_id: int
    family: str
    draw: Callable[[object, np.random.Generator], np.ndarray]
    mean_truth: float


def build_type_registry() -> dict[str, TypeSpec]:
    """Construct the frozen D1 type registry (subset used by EXP-077: U/S/B null+effect types)."""
    specs: dict[str, TypeSpec] = {}
    for label, tid, mu in [("U0", 0, 0.0), ("U1", 1, 0.05), ("U2", 2, 0.10), ("U3", 3, 0.20)]:
        specs[label] = TypeSpec(label, tid, "U",
                                lambda sz, rng, m=mu: gen_unimodal(m, sz, rng), mu)
    skews = [("Splus", 10, 0.0, 1.0, 4.0), ("Sminus", 11, 0.55, 1.0, -4.0),
             ("Sminus0", 12, 0.62, 1.0, -4.0)]
    for label, tid, xi, omega, alpha in skews:
        delta = alpha / np.sqrt(1.0 + alpha * alpha)
        mean = xi + omega * delta * np.sqrt(2.0 / np.pi)
        specs[label] = TypeSpec(label, tid, "S",
                                lambda sz, rng, p=(xi, omega, alpha): gen_skewnormal(
                                    p[0], p[1], p[2], sz, rng), float(mean))
    bis = [("B_neg", 20, 0.85, 0.15, 0.5, -2.0, 0.6),
           ("B_zero", 21, 0.90, 0.15, 0.5, -1.5, 0.6),
           ("B_pos", 22, 0.95, 0.10, 0.5, -1.0, 0.6),
           ("B_strong", 23, 0.80, 0.20, 0.5, -2.0, 0.6)]
    for label, tid, w, mu1, s1, mu2, s2 in bis:
        mean = w * mu1 + (1.0 - w) * mu2
        specs[label] = TypeSpec(label, tid, "B",
                                lambda sz, rng, p=(w, mu1, s1, mu2, s2): gen_bimodal(
                                    p[0], p[1], p[2], p[3], p[4], sz, rng), float(mean))
    return specs


# --------------------------------------------------------------------------- #
# Pure computation — Leg A (FPR) and Leg B (MDE) cells
# --------------------------------------------------------------------------- #
def _wf_ci_low(series: np.ndarray, rng: np.random.Generator) -> float:
    """One WF-EXPANDING run on a synthetic series -> aggregated expectancy one-sided lower bound."""
    agg = wf.aggregate_walk_forward(series, rng, kind="iid", thresholds=THRESHOLDS,
                                    n_boot=N_BOOT, alpha=CI_ALPHA)
    return agg.ci_low_1s


def calibrate_margin(spec: TypeSpec, n: int, r_rep: int) -> float:
    """m(type, N) = max(0, Q95(ci_low_1s | null)) over r_rep TAG_CAL calibration null series."""
    lows = np.empty(r_rep, dtype=np.float64)
    for rep in range(r_rep):
        series = spec.draw(n, rng_for(TAG_CAL, spec.type_id, n, rep))
        lows[rep] = _wf_ci_low(series, rng_for(TAG_CAL, spec.type_id, n, rep, 1))
    return float(max(0.0, np.quantile(lows, MARGIN_Q)))


def fpr_for_cell(spec: TypeSpec, n: int, margin: float, r_rep: int) -> dict:
    """Leg A: WF FPR on independent TAG_VAL null series under rule ci_low_1s > margin."""
    edges = 0
    for rep in range(r_rep):
        series = spec.draw(n, rng_for(TAG_VAL, spec.type_id, n, rep))
        low = _wf_ci_low(series, rng_for(TAG_VAL, spec.type_id, n, rep, 1))
        edges += int(low > margin)
    fpr = edges / r_rep
    return {"stratum": spec.label, "n": n, "read": "wf", "margin": margin,
            "edges": edges, "r_rep": r_rep, "fpr": fpr, "wilson_hi": wilson_upper(edges, r_rep),
            "pass": bool(fpr <= FPR_TARGET and wilson_upper(edges, r_rep) <= FPR_WILSON_HI),
            "binding": bool(n >= MDE_BINDING_N)}


def fpr_single_window(spec: TypeSpec, n: int, r_rep: int) -> dict:
    """Leg A small-n sub-read: direct (no-fold) ASS CI FPR — tests EXP-076 n<30 under-coverage.

    Margin calibrated single-window on TAG_CAL; FPR validated single-window on TAG_VAL.
    """
    cal = np.empty(r_rep, dtype=np.float64)
    for rep in range(r_rep):
        series = spec.draw(n, rng_for(TAG_CAL, spec.type_id, n, rep))
        cal[rep] = ass.bootstrap_cis(series, rng_for(TAG_CAL, spec.type_id, n, rep, 2),
                                     n_boot=N_BOOT, alpha=CI_ALPHA).expectancy_lo
    margin = float(max(0.0, np.quantile(cal, MARGIN_Q)))
    edges = 0
    for rep in range(r_rep):
        series = spec.draw(n, rng_for(TAG_VAL, spec.type_id, n, rep))
        low = ass.bootstrap_cis(series, rng_for(TAG_VAL, spec.type_id, n, rep, 2),
                                n_boot=N_BOOT, alpha=CI_ALPHA).expectancy_lo
        edges += int(low > margin)
    fpr = edges / r_rep
    return {"stratum": spec.label, "n": n, "read": "single_window", "margin": margin,
            "edges": edges, "r_rep": r_rep, "fpr": fpr, "wilson_hi": wilson_upper(edges, r_rep),
            "pass": bool(fpr <= FPR_TARGET and wilson_upper(edges, r_rep) <= FPR_WILSON_HI),
            "binding": False}


def tpr_for_cell(n: int, mu: float, r_rep: int) -> dict:
    """Leg B: TPR(ci_low_1s > 0) for the U-location effect type N(mu, 1) at size N."""
    tid = 100 + int(round(mu * 1000))            # disjoint effect seed-id (not a registry type)
    hits = 0
    for rep in range(r_rep):
        series = gen_unimodal(mu, n, rng_for(TAG_EFF, tid, n, rep))
        low = _wf_ci_low(series, rng_for(TAG_EFF, tid, n, rep, 1))
        hits += int(low > 0.0)
    return {"n": n, "mu": mu, "tpr": hits / r_rep, "r_rep": r_rep}


def mde_from_tpr(tpr_rows: list[dict]) -> list[dict]:
    """MDE(N) = smallest mu with TPR >= 0.80 (monotone interp); finite flag per N (binding N>=30)."""
    out = []
    by_n: dict[int, list[dict]] = {}
    for r in tpr_rows:
        by_n.setdefault(r["n"], []).append(r)
    for n, rows in sorted(by_n.items()):
        rows = sorted(rows, key=lambda r: r["mu"])
        mus = np.array([r["mu"] for r in rows])
        tprs = np.array([r["tpr"] for r in rows])
        mde = float("inf")
        for i in range(len(mus)):
            if tprs[i] >= TPR_FLOOR:
                if i == 0:
                    mde = float(mus[0])
                else:                            # linear interp between the bracketing mu
                    t0, t1, m0, m1 = tprs[i - 1], tprs[i], mus[i - 1], mus[i]
                    mde = float(m0 + (TPR_FLOOR - t0) * (m1 - m0) / (t1 - t0)) if t1 > t0 else float(m1)
                break
        finite = math.isfinite(mde)
        out.append({"n": n, "mde": mde if finite else None, "finite": finite,
                    "max_tpr": float(tprs.max()), "binding": bool(n >= MDE_BINDING_N),
                    "pass": bool(finite or n < MDE_BINDING_N)})
    return out


# --------------------------------------------------------------------------- #
# Pure computation — Leg C (P(>X) reliability)
# --------------------------------------------------------------------------- #
def reliability_pairs(specs: dict[str, TypeSpec], r_rep: int) -> list[dict]:
    """Collect (X, predicted, realized) pairs from held-out WF folds across reliability types."""
    pairs: list[dict] = []
    cells = [(label, n) for label in REL_TYPES for n in REL_N]
    for label, n in tqdm(cells, desc="reliability (type,N) cells"):
        spec = specs[label]
        folds = wf.make_folds(n)
        for rep in range(r_rep):
            series = spec.draw(n, rng_for(TAG_REL, spec.type_id, n, rep))
            for fold in folds:
                train = series[fold.train_start:fold.train_stop]
                test = series[fold.test_start:fold.test_stop]
                if train.shape[0] < 2 or test.shape[0] < 1:
                    continue
                sc = ass.score(train, shrink=False, thresholds=THRESHOLDS)
                for thr in THRESHOLDS:
                    pairs.append({"X": float(thr), "predicted": sc.p_gt[thr],
                                  "realized": float(np.mean(test > thr)), "n_test": int(test.shape[0])})
    return pairs


def reliability_check(pairs: list[dict]) -> tuple[list[dict], list[dict]]:
    """Decile-bucket predicted vs realized per X; return (decile rows, per-X verdict rows)."""
    df = pl.DataFrame(pairs)
    decile_rows: list[dict] = []
    verdict_rows: list[dict] = []
    for thr in THRESHOLDS:
        sub = df.filter(pl.col("X") == float(thr))
        if sub.height == 0:
            continue
        pred = sub["predicted"].to_numpy()
        real = sub["realized"].to_numpy()
        # decile bins by predicted value, guard empty bins
        edges = np.quantile(pred, np.linspace(0, 1, REL_DECILES + 1))
        edges = np.unique(edges)
        idx = np.clip(np.searchsorted(edges, pred, side="right") - 1, 0, len(edges) - 2)
        pm, rm = [], []
        for d in range(len(edges) - 1):
            mask = idx == d
            if mask.sum() == 0:
                continue
            p_mean, r_mean = float(pred[mask].mean()), float(real[mask].mean())
            pm.append(p_mean)
            rm.append(r_mean)
            decile_rows.append({"X": float(thr), "decile": d, "predicted": p_mean,
                                "realized": r_mean, "gap": abs(p_mean - r_mean), "n": int(mask.sum())})
        pm_a, rm_a = np.array(pm), np.array(rm)
        max_gap = float(np.max(np.abs(pm_a - rm_a))) if pm_a.size else float("nan")
        slope = (float(np.polyfit(pm_a, rm_a, 1)[0]) if pm_a.size >= 2 and np.ptp(pm_a) > 1e-9
                 else float("nan"))
        ok = bool(max_gap <= REL_MAX_GAP and REL_SLOPE_BAND[0] <= slope <= REL_SLOPE_BAND[1])
        verdict_rows.append({"X": float(thr), "max_gap": max_gap, "slope": slope,
                             "n_deciles": int(pm_a.size), "pass": ok})
    return decile_rows, verdict_rows


# --------------------------------------------------------------------------- #
# Pure computation — Leg D (counted-read accounting scenarios)
# --------------------------------------------------------------------------- #
def accounting_scenarios() -> list[dict]:
    """Drive xen.wf.counted_reads through the D4.1 scenario table; assert expected == actual."""
    cases = [
        ("conforming_open", wf.RunSpec("S1", True, False, True, False), 0,
         {"accepted": True, "counted_increment": 1, "per_fold_reverted": False}),
        ("conforming_second_weakened", wf.RunSpec("S1", True, False, True, False), 1,
         {"accepted": True, "counted_increment": 1, "weakened_evidence": True}),
        ("at_cap_rejected", wf.RunSpec("S1", True, False, True, False), 2,
         {"accepted": False, "counted_increment": 0}),
        ("between_fold_selection_reverts", wf.RunSpec("S2", True, True, True, False, n_folds=5), 0,
         {"accepted": False, "counted_increment": 0, "per_fold_reverted": True}),
        ("not_frozen_reverts", wf.RunSpec("S3", False, False, True, False, n_folds=5), 0,
         {"accepted": False, "counted_increment": 0, "per_fold_reverted": True}),
        ("holdout_fold_rejected", wf.RunSpec("S4", True, False, True, True), 0,
         {"accepted": False, "counted_increment": 0}),
        ("rolling_comparison_zero", wf.RunSpec("S5", True, False, True, False, is_rolling_comparison=True), 1,
         {"accepted": True, "counted_increment": 0}),
    ]
    rows = []
    for name, spec, prior, expected in cases:
        out = wf.counted_reads(spec, prior)
        actual = {"accepted": out.accepted, "counted_increment": out.counted_increment,
                  "per_fold_reverted": out.per_fold_reverted, "weakened_evidence": out.weakened_evidence}
        ok = all(actual[k] == v for k, v in expected.items())
        rows.append({"scenario": name, "stratum": spec.stratum, "prior_counted": prior,
                     "expected": json.dumps(expected), "actual_increment": out.counted_increment,
                     "accepted": out.accepted, "new_counted": out.new_counted,
                     "reason": out.reason, "pass": bool(ok)})
    # Cap-honoring demonstration: two conforming runs then a third must be blocked.
    prior = 0
    cap_trace = []
    for i in range(3):
        out = wf.counted_reads(wf.RunSpec("CAP", True, False, True, False), prior)
        cap_trace.append((i, prior, out.accepted, out.new_counted))
        prior = out.new_counted
    cap_ok = (cap_trace[0][2] and cap_trace[1][2] and not cap_trace[2][2] and prior <= wf.CAP_COUNTED_READS)
    rows.append({"scenario": "cap_honored_3_runs", "stratum": "CAP", "prior_counted": 0,
                 "expected": json.dumps({"third_blocked": True, "final<=cap": True}),
                 "actual_increment": prior, "accepted": cap_ok, "new_counted": prior,
                 "reason": f"trace={cap_trace}", "pass": bool(cap_ok)})
    return rows


# --------------------------------------------------------------------------- #
# I/O helpers — Leg E dogfood TRAIN-only loader (first 49%; TEST + holdout never sliced)
# --------------------------------------------------------------------------- #
def find_source_file(instrument: str) -> Path:
    """Newest full (non-derivative) 1-minute Parquet for one symbol (excludes pre-sliced files)."""
    matches = sorted(p for p in DATA_DIR.glob(f"timebars_{instrument.lower()}_*.parquet")
                     if not any(m in p.name for m in EXCLUDED_FILE_MARKERS))
    if not matches:
        raise FileNotFoundError(f"no 1-minute source file for {instrument} under {DATA_DIR}")
    return matches[-1]


def load_train_1m(instrument: str) -> tuple[pl.DataFrame, int, int]:
    """Return (train_1m, train_cutoff_row, total_rows): first-49% TRAIN slice only.

    The next-21% TEST stratum and the final-30% holdout are never sliced or materialized — the lazy
    plan stops at train_cutoff = int(int(total*0.7)*0.7).
    """
    path = find_source_file(instrument)
    cols = ["Symbol", "OpenTime", "CloseTime", "Open", "High", "Low", "Close", "TickVolume"]
    total = int(pl.scan_parquet(path).select(pl.len()).collect().item())
    train_cutoff = int(int(total * ANALYSIS_FRACTION) * TRAIN_FRACTION)
    train = pl.scan_parquet(path).select(cols).sort("CloseTime").slice(0, train_cutoff).collect()
    if train.is_empty():
        raise RuntimeError(f"{instrument}: empty TRAIN slice")
    if not train.get_column("CloseTime").is_sorted():
        raise RuntimeError(f"{instrument}: TRAIN slice not chronological by CloseTime")
    return train, train_cutoff, total


def dogfood_returns(domain_bars: pl.DataFrame) -> np.ndarray:
    """Developer-defined CAUSAL forward-H-bar real-price return in ATR units (no edge claim).

    r_t = (Close[t+H] - Close[t]) / ATR(14)[t], the trailing H bars dropped (no look-ahead). Real
    `Close` only; no HA/Renko brick prices. Carries no market-edge claim — a pipeline smoke series.
    """
    close = domain_bars["Close"].to_numpy().astype(np.float64)
    high = domain_bars["High"].to_numpy().astype(np.float64)
    low = domain_bars["Low"].to_numpy().astype(np.float64)
    m = close.shape[0]
    if m < DOG_ATR_PERIOD + DOG_FWD_H + 2:
        return np.asarray([], dtype=np.float64)
    prev_close = np.concatenate([[close[0]], close[:-1]])
    tr = np.maximum(high - low, np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)))
    atr = np.full(m, np.nan)                      # causal rolling-mean ATR (uses only past/current)
    csum = np.cumsum(tr)
    atr[DOG_ATR_PERIOD - 1:] = (
        np.concatenate([[csum[DOG_ATR_PERIOD - 1]], csum[DOG_ATR_PERIOD:] - csum[:-DOG_ATR_PERIOD]])
        / DOG_ATR_PERIOD)
    fwd = np.full(m, np.nan)
    fwd[:m - DOG_FWD_H] = close[DOG_FWD_H:] - close[:m - DOG_FWD_H]
    r = fwd / atr
    return r[np.isfinite(r)]


def dogfood_cell(instrument: str, period_min: int) -> dict:
    """Leg E: run WF-EXPANDING + ASS (moving-block) on one (instrument, domain) TRAIN-only cell."""
    train_1m, train_cutoff, total = load_train_1m(instrument)
    max_read_ts = int(train_1m.get_column("CloseTime").dt.epoch("s").max())
    domain = aggregate_ohlc(train_1m, period_minutes=period_min, min_coverage=DOG_MIN_COVERAGE)
    r = dogfood_returns(domain)
    cutoff_ok = bool(train_cutoff <= int(total * ANALYSIS_FRACTION * TRAIN_FRACTION) + 1)
    base = {"instrument": instrument, "domain_min": period_min, "n_domain_bars": int(domain.height),
            "n_events": int(r.shape[0]), "train_cutoff_row": train_cutoff, "total_rows": total,
            "max_read_close_epoch_s": max_read_ts, "cutoff_assert_ok": cutoff_ok, "counted_reads": 0}
    if r.shape[0] < 2 * wf.N_FOLDS or r.shape[0] < 4:
        base.update({"completed": False, "all_folds_finite": False,
                     "reason": "insufficient TRAIN events for WF folds (disclosed)"})
        return base
    agg = wf.aggregate_walk_forward(r, rng_for(TAG_DOG, DOG_INSTRUMENT_ID[instrument], period_min),
                                    kind="block", thresholds=THRESHOLDS, n_boot=N_BOOT, alpha=CI_ALPHA)
    finite = bool(np.isfinite([agg.expectancy, agg.expectancy_lo, agg.expectancy_hi,
                               agg.median]).all() and all(np.isfinite(list(agg.p_gt.values()))))
    base.update({"completed": True, "all_folds_finite": finite, "n_pooled": agg.n_pooled,
                 "fold_sizes": json.dumps(list(agg.fold_sizes)),
                 "subfloor_folds": json.dumps(list(agg.subfloor_folds)),
                 "expectancy": agg.expectancy, "expectancy_lo": agg.expectancy_lo,
                 "median": agg.median, "reason": "ok"})
    return base


# --------------------------------------------------------------------------- #
# Parallel cell tasks (FPR + MDE) — picklable, seed-independent of worker/order
# --------------------------------------------------------------------------- #
def _fpr_task(task: tuple) -> list[dict]:
    label, n, r_rep = task
    spec = build_type_registry()[label]
    margin = calibrate_margin(spec, n, r_rep)
    rows = [fpr_for_cell(spec, n, margin, r_rep)]
    if n in SMALL_N:
        rows.append(fpr_single_window(spec, n, r_rep))
    return rows


def _mde_task(task: tuple) -> dict:
    n, mu, r_rep = task
    return tpr_for_cell(n, mu, r_rep)


def run_fpr(r_rep: int, workers: int) -> list[dict]:
    """Leg A over the (null type, N) grid; parallel, order-preserving, seed-deterministic."""
    tasks = [(lbl, n, r_rep) for lbl in ("U0", "B_zero") for n in N_GRID]
    rows: list[dict] = []
    if workers <= 1:
        for t in tqdm(tasks, desc="FPR cells"):
            rows.extend(_fpr_task(t))
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for out in tqdm(ex.map(_fpr_task, tasks), total=len(tasks), desc=f"FPR cells (x{workers})"):
                rows.extend(out)
    return rows


def run_mde(r_rep: int, workers: int) -> tuple[list[dict], list[dict]]:
    """Leg B: TPR over (N>=30, mu) then MDE(N) finiteness; parallel, order-preserving."""
    grid_n = [n for n in N_GRID if n >= MDE_BINDING_N]
    tasks = [(n, mu, r_rep) for n in grid_n for mu in MU_GRID]
    tpr_rows: list[dict] = []
    if workers <= 1:
        for t in tqdm(tasks, desc="MDE TPR cells"):
            tpr_rows.append(_mde_task(t))
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            for out in tqdm(ex.map(_mde_task, tasks), total=len(tasks), desc=f"MDE TPR cells (x{workers})"):
                tpr_rows.append(out)
    return tpr_rows, mde_from_tpr(tpr_rows)


# --------------------------------------------------------------------------- #
# Plotting (5) — consume bounded result tables, no heavy recompute
# --------------------------------------------------------------------------- #
def plot_fpr(fpr: pl.DataFrame, path: Path) -> None:
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 6))
    for (label, read) in sorted({(r["stratum"], r["read"]) for r in fpr.iter_rows(named=True)}):
        d = fpr.filter((pl.col("stratum") == label) & (pl.col("read") == read)).sort("n")
        ax.plot(d["n"], d["fpr"], marker="o", alpha=0.8, label=f"{label}/{read}")
    ax.axhline(FPR_TARGET, color="red", ls="--", label=f"target {FPR_TARGET}")
    ax.axhline(FPR_WILSON_HI, color="orange", ls=":", label=f"wilson-hi ceil {FPR_WILSON_HI}")
    ax.set_xscale("log")
    ax.set_title("Margin-calibrated FPR vs N under WF-EXPANDING", fontsize=12)
    ax.set_xlabel("N (log)")
    ax.set_ylabel("false-positive edge-call rate")
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_mde(mde: pl.DataFrame, tpr: pl.DataFrame, path: Path) -> None:
    sns.set_theme(style="whitegrid")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))
    finite = mde.filter(pl.col("finite")).sort("n")
    if finite.height:
        ax1.plot(finite["n"], finite["mde"], marker="o", color="#1b7837")
    degen = mde.filter(~pl.col("finite"))
    for row in degen.iter_rows(named=True):
        ax1.scatter([row["n"]], [0], marker="x", color="red", s=60)
    ax1.set_xscale("log")
    ax1.set_title("MDE(N) — finite cells (degenerate = red x)")
    ax1.set_xlabel("N (log)")
    ax1.set_ylabel("MDE (mu)")
    for n in sorted(tpr["n"].unique().to_list()):
        d = tpr.filter(pl.col("n") == n).sort("mu")
        ax2.plot(d["mu"], d["tpr"], marker=".", alpha=0.7, label=f"N={n}")
    ax2.axhline(TPR_FLOOR, color="red", ls="--", label=f"TPR {TPR_FLOOR}")
    ax2.set_title("TPR vs mu by N")
    ax2.set_xlabel("mu")
    ax2.set_ylabel("TPR")
    ax2.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_reliability(decile: pl.DataFrame, path: Path) -> None:
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.plot([0, 1], [0, 1], color="grey", ls=":", label="y=x")
    for thr in sorted(decile["X"].unique().to_list()):
        d = decile.filter(pl.col("X") == thr).sort("predicted")
        ax.plot(d["predicted"], d["realized"], marker="o", alpha=0.8, label=f"X={thr}")
    ax.set_title("P(return>X) reliability (predicted vs realized deciles)", fontsize=12)
    ax.set_xlabel("predicted P(>X)")
    ax.set_ylabel("realized frequency")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_fold_schedule(path: Path) -> None:
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5))
    folds = wf.make_folds(1000)
    for f in folds:
        ax.barh(f.index, f.train_stop / 1000, color="#9ecae1", edgecolor="grey")
        ax.barh(f.index, (f.test_stop - f.test_start) / 1000, left=f.test_start / 1000,
                color="#fc9272", edgecolor="grey")
    ax.set_title("WF-EXPANDING schedule (train=blue, test=red; series fraction)", fontsize=12)
    ax.set_xlabel("fraction of analysis series")
    ax.set_ylabel("fold")
    ax.set_yticks([f.index for f in folds])
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_dogfood(dog: pl.DataFrame, path: Path) -> None:
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))
    dog = dog.with_columns((pl.col("instrument") + "-" + pl.col("domain_min").cast(pl.String)).alias("cell"))
    ax.bar(dog["cell"], dog["n_events"], color="#2166ac")
    ax.set_title("Dogfood TRAIN-only events per (instrument, domain) — first 49% only", fontsize=12)
    ax.set_xlabel("cell")
    ax.set_ylabel("WF events (first-49% TRAIN)")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration helpers
# --------------------------------------------------------------------------- #
def _sha256_df(df: pl.DataFrame) -> str:
    return hashlib.sha256(df.write_csv().encode()).hexdigest()


def integrity_anchor() -> dict:
    """R-anchor: un-pooled ASS direct expectancy == numpy.mean (<=1e-12) on a shared seed cell."""
    spec = build_type_registry()[ANCHOR_TYPE]
    x = spec.draw(ANCHOR_N, rng_for(TAG_EFF, spec.type_id, ANCHOR_N, ANCHOR_REP))
    s = ass.score(x, shrink=False)
    diff = abs(s.expectancy_direct - float(np.mean(x)))
    return {"anchor_cell": f"{ANCHOR_TYPE}/n={ANCHOR_N}/rep={ANCHOR_REP}",
            "direct_expectancy": s.expectancy_direct, "numpy_mean": float(np.mean(x)),
            "anchor_abs_diff": diff, "anchor_pass": bool(diff <= 1e-12)}


# --------------------------------------------------------------------------- #
# Verdict assembly (PER-STRATUM — pure function of the result tables)
# --------------------------------------------------------------------------- #
def build_verdict(fpr_df: pl.DataFrame, mde_df: pl.DataFrame, rel_df: pl.DataFrame,
                  acct_df: pl.DataFrame, dog_df: pl.DataFrame, anchor: dict, det: dict,
                  scale_label: str) -> dict:
    """Assemble the per-stratum EXP-077 verdict (LESSON-001: no binding collapsed cross-cell flag)."""
    # ---- Leg A: FPR per (null stratum, N, read); binding for N>=30 ----
    if fpr_df.height:
        binding_fail = fpr_df.filter(pl.col("binding") & (~pl.col("pass")))
        small = fpr_df.filter(pl.col("n").is_in(list(SMALL_N)))
        fpr = {"verdict": "PASS" if binding_fail.height == 0 else "FAIL", "binding": True,
               "n_binding_cells": int(fpr_df.filter(pl.col("binding")).height),
               "binding_fail_cells": binding_fail.select(["stratum", "n", "read", "fpr",
                                                          "wilson_hi"]).to_dicts(),
               "small_n_stratum": small.select(["stratum", "n", "read", "fpr", "wilson_hi",
                                                "pass"]).to_dicts(),
               "note": "ci_low_1s > m (m calibrated on TAG_CAL nulls; FPR on independent TAG_VAL)"}
    else:
        fpr = {"verdict": "SKIPPED (--no-fpr-mde)", "binding": False}
    # ---- Leg B: MDE finiteness per N>=30 ----
    if mde_df.height:
        mde_fail = mde_df.filter(pl.col("binding") & (~pl.col("finite")))
        mde = {"verdict": "PASS" if mde_fail.height == 0 else "FAIL", "binding": True,
               "degenerate_binding_cells": mde_fail.select(["n", "max_tpr"]).to_dicts(),
               "mde_by_n": mde_df.select(["n", "mde", "finite", "binding"]).to_dicts(),
               "note": "MDE(N)=smallest mu with TPR(CI_low>0)>=0.80; gate=finiteness for N>=30"}
    else:
        mde = {"verdict": "SKIPPED (--no-fpr-mde)", "binding": False}
    # ---- Leg C: reliability per X ----
    rel_fail = rel_df.filter(~pl.col("pass"))
    reliability = {"verdict": "PASS" if rel_fail.height == 0 else "FAIL", "binding": True,
                   "by_X": rel_df.to_dicts(),
                   "note": "per X: max|pred-realized|<=0.10 AND slope in [0.85,1.15]"}
    # ---- Leg D: counted-read accounting per scenario ----
    acct_fail = acct_df.filter(~pl.col("pass"))
    accounting = {"verdict": "PASS" if acct_fail.height == 0 else "PROTOCOL_DEFECT",
                  "binding": True, "n_scenarios": int(acct_df.height),
                  "failing_scenarios": acct_fail.select(["scenario", "reason"]).to_dicts(),
                  "note": "D4.1: one frozen WF run=+1 counted read; cap honored; folds=disclosures"}
    # ---- Leg E: dogfood per (instrument, domain) ----
    dog_fail = dog_df.filter((~pl.col("completed")) | (~pl.col("cutoff_assert_ok")))
    finite_fail = dog_df.filter(pl.col("completed") & (~pl.col("all_folds_finite")))
    dogfood = {"verdict": "PASS" if (finite_fail.height == 0 and
                                     int(dog_df.filter(pl.col("cutoff_assert_ok")).height) == dog_df.height)
               else "PARTIAL/REVIEW", "binding": True,
               "n_cells": int(dog_df.height), "counted_reads_total": int(dog_df["counted_reads"].sum()),
               "cutoff_assert_all_ok": bool(dog_df["cutoff_assert_ok"].all()),
               "incomplete_or_fence_cells": dog_fail.select(["instrument", "domain_min",
                                                            "reason"]).to_dicts(),
               "nonfinite_cells": finite_fail.select(["instrument", "domain_min"]).to_dicts(),
               "note": "TRAIN-only (first 49%); TEST + holdout never sliced; 0 counted reads"}

    collapsed = (fpr.get("verdict") in ("PASS", "SKIPPED (--no-fpr-mde)")
                 and mde.get("verdict") in ("PASS", "SKIPPED (--no-fpr-mde)")
                 and reliability["verdict"] == "PASS" and accounting["verdict"] == "PASS"
                 and dogfood["verdict"] == "PASS" and bool(anchor["anchor_pass"]) and all(det.values()))
    return {
        "scale": scale_label,
        "doctrine": ("PER-STRATUM adjudication (cf-capgeo-001.md:137,204; D0 §D1/§D4; LESSON-001). "
                     "Each leg below carries its own per-stratum verdict; FPR per (type,N,read), "
                     "MDE per N, reliability per X, accounting per scenario, dogfood per cell. No "
                     "collapsed cross-leg verdict is binding."),
        "strata": {"fpr": fpr, "mde": mde, "reliability": reliability,
                   "accounting": accounting, "dogfood": dogfood},
        "integrity": {"anchor_pass": bool(anchor["anchor_pass"]), "determinism": det},
        "feeds_g017": ("EXP-077 reports which ASS_VALIDATED legs hold; G-017 adjudicated after "
                       "EXP-078. PROTOCOL_DEFECT if accounting fails or determinism breaks."),
        "collapsed_convenience_flag": {
            "value": bool(collapsed),
            "caveat": ("NON-BINDING. Collapsed cross-leg AND retained for convenience only; NOT the "
                       "verdict. The per-stratum leg verdicts above are binding (LESSON-001).")},
    }


def _log_verdict(v: dict) -> None:
    s = v["strata"]
    for leg in ("fpr", "mde", "reliability", "accounting", "dogfood"):
        logger.info("STRATUM %s: %s", leg, s[leg].get("verdict"))
    logger.info("integrity: anchor_pass=%s determinism=%s",
                v["integrity"]["anchor_pass"], v["integrity"]["determinism"])
    logger.info("collapsed_convenience_flag=%s (NON-BINDING — see results/verdict.json strata)",
                v["collapsed_convenience_flag"]["value"])


def rebuild_verdict_from_results() -> None:
    """Regenerate results/verdict.json (per-stratum) from existing tables; no recompute."""
    req = ["fpr.csv", "mde.csv", "reliability_verdict.csv", "accounting.csv", "dogfood.csv",
           "integrity.json"]
    missing = [f for f in req if not (RESULTS_DIR / f).exists()]
    if missing:
        raise SystemExit(f"--rebuild-verdict: missing {missing} in {RESULTS_DIR}")
    fpr_df = pl.read_csv(RESULTS_DIR / "fpr.csv")
    mde_df = pl.read_csv(RESULTS_DIR / "mde.csv")
    rel_df = pl.read_csv(RESULTS_DIR / "reliability_verdict.csv")
    acct_df = pl.read_csv(RESULTS_DIR / "accounting.csv")
    dog_df = pl.read_csv(RESULTS_DIR / "dogfood.csv")
    integ = json.loads((RESULTS_DIR / "integrity.json").read_text())
    scale = "SMOKE (non-binding)" if integ.get("config", {}).get("smoke") else "FROZEN (G-017 legs)"
    v = build_verdict(fpr_df, mde_df, rel_df, acct_df, dog_df, integ["anchor"],
                      integ["determinism"], scale)
    (RESULTS_DIR / "verdict.json").write_text(json.dumps(v, indent=2))
    logger.info("--rebuild-verdict: regenerated results/verdict.json from existing tables")
    _log_verdict(v)


# --------------------------------------------------------------------------- #
# main()
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(description="EXP-077 ASS dogfood + WF-EXPANDING calibration")
    parser.add_argument("--smoke", action="store_true",
                        help="non-binding reduced-scale correctness run (NOT the G-017 legs)")
    parser.add_argument("--no-fpr-mde", action="store_true",
                        help="skip the expensive Legs A/B (FPR+MDE); run Legs C/D/E only")
    parser.add_argument("--workers", type=int, default=0,
                        help="parallel workers over FPR/MDE cells (0=all cores, 1=serial). "
                             "Output is byte-identical at any worker count.")
    parser.add_argument("--rebuild-verdict", action="store_true",
                        help="regenerate results/verdict.json from existing tables; no recompute")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

    if args.rebuild_verdict:
        rebuild_verdict_from_results()
        return

    r_rep = R_REP
    rel_rep = R_REP
    if args.smoke:
        r_rep, rel_rep = 60, 40
        logger.warning("SMOKE MODE — reduced scale; results are NON-BINDING for the G-017 legs")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    specs = build_type_registry()
    n_cells = (2 * len(N_GRID)) + (len([n for n in N_GRID if n >= MDE_BINDING_N]) * len(MU_GRID))
    workers = args.workers if args.workers > 0 else (os.cpu_count() or 1)
    workers = max(1, min(workers, max(1, n_cells)))
    logger.info("parallel workers: %d", workers)

    # ---- Legs A & B (expensive; optional) ----
    if args.no_fpr_mde:
        fpr_rows, tpr_rows, mde_rows = [], [], []
        logger.warning("--no-fpr-mde: Legs A/B skipped")
    else:
        logger.info("Leg A — FPR (margin-calibrated) under WF-EXPANDING ...")
        fpr_rows = run_fpr(r_rep, workers)
        logger.info("Leg B — MDE finiteness under WF-EXPANDING ...")
        tpr_rows, mde_rows = run_mde(r_rep, workers)
    fpr_df = pl.DataFrame(fpr_rows) if fpr_rows else pl.DataFrame(
        schema={"stratum": pl.String, "n": pl.Int64, "read": pl.String, "margin": pl.Float64,
                "edges": pl.Int64, "r_rep": pl.Int64, "fpr": pl.Float64, "wilson_hi": pl.Float64,
                "pass": pl.Boolean, "binding": pl.Boolean})
    tpr_df = pl.DataFrame(tpr_rows) if tpr_rows else pl.DataFrame(
        schema={"n": pl.Int64, "mu": pl.Float64, "tpr": pl.Float64, "r_rep": pl.Int64})
    mde_df = pl.DataFrame(mde_rows) if mde_rows else pl.DataFrame(
        schema={"n": pl.Int64, "mde": pl.Float64, "finite": pl.Boolean, "max_tpr": pl.Float64,
                "binding": pl.Boolean, "pass": pl.Boolean})

    # ---- Leg C — reliability ----
    logger.info("Leg C — P(return>X) reliability on held-out folds ...")
    pairs = reliability_pairs(specs, rel_rep)
    rel_decile_rows, rel_verdict_rows = reliability_check(pairs)
    rel_decile_df = pl.DataFrame(rel_decile_rows)
    rel_verdict_df = pl.DataFrame(rel_verdict_rows)

    # ---- Leg D — counted-read accounting ----
    logger.info("Leg D — counted-read accounting (D4.1) ...")
    acct_df = pl.DataFrame(accounting_scenarios())

    # ---- Leg E — dogfood (TRAIN-only real bars) ----
    logger.info("Leg E — current-data TRAIN-only dogfood (first 49% only) ...")
    dog_rows = [dogfood_cell(inst, dm) for inst in tqdm(DOG_INSTRUMENTS, desc="dogfood instruments")
                for dm in DOG_DOMAINS]
    dog_df = pl.DataFrame(dog_rows)

    # ---- Integrity anchor + determinism (recompute cheap legs + a probe cell; hash-compare) ----
    logger.info("integrity anchor + determinism (D6) ...")
    anchor = integrity_anchor()
    pairs2 = reliability_pairs(specs, rel_rep)
    rel_dec2, rel_ver2 = reliability_check(pairs2)
    acct2 = pl.DataFrame(accounting_scenarios())
    det = {"reliability_match": _sha256_df(rel_verdict_df) == _sha256_df(pl.DataFrame(rel_ver2)),
           "reliability_decile_match": _sha256_df(rel_decile_df) == _sha256_df(pl.DataFrame(rel_dec2)),
           "accounting_match": _sha256_df(acct_df) == _sha256_df(acct2)}
    if not args.no_fpr_mde:                      # probe one FPR + one MDE cell for determinism
        probe_fpr = pl.DataFrame(_fpr_task(("U0", 120, r_rep)))
        probe_mde = pl.DataFrame([_mde_task((120, 0.20, r_rep))])
        det["fpr_probe_match"] = _sha256_df(probe_fpr) == _sha256_df(
            fpr_df.filter((pl.col("stratum") == "U0") & (pl.col("n") == 120)))
        det["mde_probe_match"] = _sha256_df(probe_mde) == _sha256_df(
            tpr_df.filter((pl.col("n") == 120) & (pl.col("mu") == 0.20)).select(
                ["n", "mu", "tpr", "r_rep"]))

    # ---- Verdict (per-stratum) ----
    v = build_verdict(fpr_df, mde_df, rel_verdict_df, acct_df, dog_df, anchor, det,
                      "SMOKE (non-binding)" if args.smoke else "FROZEN (G-017 legs)")

    # ---- Write outputs ----
    fpr_df.write_csv(RESULTS_DIR / "fpr.csv")
    tpr_df.write_csv(RESULTS_DIR / "mde_tpr.csv")
    mde_df.write_csv(RESULTS_DIR / "mde.csv")
    rel_decile_df.write_csv(RESULTS_DIR / "reliability_deciles.csv")
    rel_verdict_df.write_csv(RESULTS_DIR / "reliability_verdict.csv")
    acct_df.write_csv(RESULTS_DIR / "accounting.csv")
    dog_df.write_csv(RESULTS_DIR / "dogfood.csv")
    (RESULTS_DIR / "integrity.json").write_text(json.dumps(
        {"anchor": anchor, "determinism": det,
         "config": {"master_seed": MASTER_SEED, "r_rep": r_rep, "rel_rep": rel_rep,
                    "n_boot": N_BOOT, "smoke": args.smoke, "no_fpr_mde": args.no_fpr_mde},
         "table_sha256": {"fpr": _sha256_df(fpr_df), "mde": _sha256_df(mde_df),
                          "reliability_verdict": _sha256_df(rel_verdict_df),
                          "accounting": _sha256_df(acct_df), "dogfood": _sha256_df(dog_df)}},
        indent=2))
    (RESULTS_DIR / "verdict.json").write_text(json.dumps(v, indent=2))

    # ---- Plots ----
    if fpr_df.height:
        plot_fpr(fpr_df, PLOTS_DIR / "01_fpr_vs_n.png")
    if mde_df.height:
        plot_mde(mde_df, tpr_df, PLOTS_DIR / "02_mde_curve.png")
    if rel_decile_df.height:
        plot_reliability(rel_decile_df, PLOTS_DIR / "03_reliability.png")
    plot_fold_schedule(PLOTS_DIR / "04_wf_fold_schedule.png")
    plot_dogfood(dog_df, PLOTS_DIR / "05_dogfood.png")

    _log_verdict(v)


if __name__ == "__main__":
    main()
