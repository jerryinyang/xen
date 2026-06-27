"""EXP-075 — TRAIN design of an exhaustion-cap entry filter on the MA-native N-PARTIAL-V2A
harami (CF-HA-HARAMI-001 / HYP-028).

Implements the analysis plan in ``python/experiments/EXP-075/analysis-plan.md``. TRAIN-design-and-
lock: 0 TEST reads, holdout never loaded. The endpoint is the strategy's own legs (raw-mean /
median / beats-RM / retention), NOT a feature-separation screen — no framing-consistency gate is
re-run (EXP-074 Lesson 2). All binding aggregation is PER band-core domain (15m/30m/1h); the
band-pooled line and 5m are disclosed-only (EXP-074 Lesson 1).

Pipeline:
  (A) Resolve each of the 99 cells' TRAIN N-PARTIAL-V2A events ONCE via the frozen EXP-068
      machinery (the only departure from EXP-074 is that we additionally apply an entry-time
      exhaustion cap as a boolean mask on the qualifying events). The cap only removes entries —
      each retained event's r_e is identical to its uncapped value, so the capped population is a
      boolean subset of the uncapped one. Compute baseline + M-PERCELL (per-cell tuned, diagnostic-
      only) metrics; collect the band-core pooled exhaustion distribution.
  (B) From the band-core pool, compute the M-GLOBAL pooled-quantile thresholds {p85,p90,p95};
      re-resolve band-core+5m cells and evaluate the single uniform cap (M-GLOBAL, the deployable
      arm) at each threshold; lock U by the pre-registered rule.
  (C) Per-band-core-domain verdict (improved-cell share, uplift, hurt, overfit premium) and the
      routing verdict under the pinned thresholds; freeze the locked filter (hash-pinned).

This script designs and LOCKS the filter on TRAIN only. It reads no TEST/holdout and confirms no
candidate; the one-shot sealed-holdout confirmation of the frozen filter is a separate experiment.
"""
from __future__ import annotations

import hashlib
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from tqdm.auto import tqdm  # noqa: E402

# --------------------------------------------------------------------------- #
# Path setup — import the frozen EXP-068 machinery by module (no import side
# effects; its orchestration is guarded by ``if __name__ == "__main__"``).
# --------------------------------------------------------------------------- #
EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
EXPERIMENTS_ROOT = EXPERIMENT_DIR.parent
EXP068_CODE = EXPERIMENTS_ROOT / "EXP-068" / "code"
if str(EXP068_CODE) not in sys.path:
    sys.path.insert(0, str(EXP068_CODE))
import run_experiment as exp068  # noqa: E402

EXP074_EVENTS = EXPERIMENTS_ROOT / "EXP-074" / "results"

# --------------------------------------------------------------------------- #
# Constants (frozen from EXP-068/074 — none tuned; the only free parameter is U)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-075"
BASE_SEED = exp068.BASE_SEED                 # 20260616
N_BOOT = exp068.N_BOOT                       # 10_000
BOOT_BATCH = exp068.BOOT_BATCH               # 2_000
POWER_FLOOR = exp068.POWER_FLOOR             # 30 — bootstrap/retention floor
ANALYSIS_FRACTION = exp068.ANALYSIS_FRACTION  # 0.7
TRAIN_FRACTION = exp068.TRAIN_FRACTION       # 0.7 (of the analysis set)
ATR_PERIOD = exp068.ATR_PERIOD
STAT_WINDOW, STAT_MIN_WINDOW, STAT_Q = 20, 5, 0.75   # live_strong_stat defaults (EXP-074)
BINDING_OBJECT = "nat"
BINDING_ARM = "PARTIAL-V2A"
ARM = exp068.ARM_BY_ID[BINDING_ARM]

# Pre-registered design constants (D0-amendment-007 + analysis-plan; NOT tuned post-hoc).
PERCENTILES = (0.85, 0.90, 0.95)             # U-grid (upper-tail caps)
RETENTION_FLOOR = 0.70                       # min retained fraction for "improved"
MIN_RETAINED = POWER_FLOOR                   # min absolute retained events (30)
UPLIFT_BAR = 0.15                            # per-domain improved-share uplift Δ to count "improved"
HURT_BAR = -0.10                             # per-domain Δ that flags a domain "hurt" (asymmetric)
OVERFIT_BAR = 0.20                           # max band-core mean overfit premium for FILTER_PROMISING
SHARE_BAR = 0.50                             # min capped improved-share for a domain to be "improved"
MIN_POWERED_PER_DOMAIN = 5                   # INCONCLUSIVE_POWER floor per domain
Q05 = 0.05                                   # tail quantile for the powered definition

BAND_CORE = ("15m", "30m", "1h")             # binding domains
DISCLOSED_DOMAIN = "5m"                      # evaluated under M-GLOBAL but disclosed-only
PASSB_DOMAINS = ("5m", "15m", "30m", "1h")   # M-GLOBAL evaluation set (2h/4h excluded — INCONCLUSIVE)
CONTINUITY_CELL = "GBPUSD-5m"

# Cap forms: name -> per-event feature key (F1 lead; F2 normalizer-robustness).
FORMS: tuple[tuple[str, str], ...] = (("F1", "msofar_atr"), ("F2", "ss_excess"))
FORM_IDX = {name: i for i, (name, _) in enumerate(FORMS)}

# Bootstrap purposes (seed components; integer-only — no hash()).
P_MED, P_MEAN = 1, 2
SEL_BASE, SEL_GLOBAL, SEL_PERCELL = 0, 1, 2

# 99-cell MA-substrate matrix (derived from the frozen EXP-068 grid; not hand-listed).
CELLS: tuple[tuple[str, str, bool], ...] = tuple(
    (inst, dom, dom == "4h")
    for inst in exp068.INSTRUMENTS
    for dom in exp068.DOMAINS
    if (inst, dom) not in exp068.EXCLUDED_CELLS
)

RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CellResolved:
    """One cell's resolved TRAIN N-PARTIAL-V2A signal + the matched-random null context."""

    cell: str
    instrument: str
    domain: str
    r_e: np.ndarray                       # qualifying returns, entry order (certified arm)
    feats: dict[str, np.ndarray]          # feature -> array aligned to r_e (msofar_atr, ss_excess)
    n_base: int
    n_q05: int                            # baseline q05 tail count (powered = n_q05 >= POWER_FLOOR)
    null_ctx: dict[str, Any]              # context for matched_random_arm re-draws


@dataclass(frozen=True)
class Metrics:
    """Per-(cell, arm) metric vector on retained events."""

    retained_n: int
    retention: float
    mean: float
    mean_ci_low_1s: float
    median: float
    median_ci_low_1s: float
    rm_ci_low_1s: float                   # beats-RM-native median-contrast 1σ CI low

    @property
    def improved(self) -> bool:
        """Joint four-leg economic criterion (analysis-plan Step 3)."""
        return bool(
            np.isfinite(self.mean_ci_low_1s) and self.mean_ci_low_1s > 0.0
            and np.isfinite(self.median_ci_low_1s) and self.median_ci_low_1s > 0.0
            and np.isfinite(self.rm_ci_low_1s) and self.rm_ci_low_1s > 0.0
            and self.retention >= RETENTION_FLOOR and self.retained_n >= MIN_RETAINED)


# --------------------------------------------------------------------------- #
# I/O helpers (TRAIN-only loader — no TEST/holdout slice)
# --------------------------------------------------------------------------- #
def load_train_1m(instrument: str) -> tuple[pl.DataFrame, int]:
    """Return (train_1m, train_end_epoch_s); TRAIN slice only (first 49%).

    The next-21% TEST stratum and the final-30% holdout are never sliced or materialized.
    Mirrors EXP-074's loader exactly (the resolution must be byte-identical for reconciliation).
    """
    path = exp068.find_source_file(instrument)
    cols = ["Symbol", "OpenTime", "CloseTime", "Open", "High", "Low", "Close", "TickVolume"]
    scan = pl.scan_parquet(path).select(cols).sort("CloseTime")
    total = int(pl.scan_parquet(path).select(pl.len()).collect().item())
    analysis_cutoff = int(total * ANALYSIS_FRACTION)
    train_cutoff = int(analysis_cutoff * TRAIN_FRACTION)
    train_1m = scan.slice(0, train_cutoff).collect()   # TEST + holdout never sliced here
    if train_1m.is_empty():
        raise RuntimeError(f"{instrument}: empty TRAIN slice")
    if not train_1m.get_column("CloseTime").is_sorted():
        raise RuntimeError(f"{instrument}: TRAIN slice not chronological by CloseTime")
    train_end = int(train_1m.get_column("CloseTime").dt.epoch("s")[-1])
    return train_1m, train_end


def load_exp074_re(cell: str) -> np.ndarray | None:
    """Load EXP-074's certified per-event r_e for one cell (reconciliation anchor)."""
    path = EXP074_EVENTS / f"events_{cell}.parquet"
    if not path.exists():
        return None
    return pl.read_parquet(path).get_column("r_e").to_numpy().astype(np.float64)


# --------------------------------------------------------------------------- #
# Pure computation — causal strong-stat threshold (mirrors live_strong_stat; from EXP-074)
# --------------------------------------------------------------------------- #
def strong_stat_thr(
    k_inclusive: np.ndarray, magnitudes: np.ndarray,
    window: int = STAT_WINDOW, min_window: int = STAT_MIN_WINDOW, q: float = STAT_Q,
) -> tuple[np.ndarray, np.ndarray]:
    """Per-entry trailing-window p75 threshold (causal; copied from EXP-074 strong_stat_detail).

    Returns ``(defined, thr)`` — ``thr`` is the p75 of the trailing ``window`` confirmed-move
    magnitudes inclusive of the binding move ``k`` (ConfirmTime <= entry). NaN where undefined.
    """
    n = int(k_inclusive.shape[0])
    defined = np.zeros(n, dtype=bool)
    thr = np.full(n, np.nan)
    for i in range(n):
        kk = int(k_inclusive[i])
        if kk < 0:
            continue
        lo = max(0, kk - window + 1)
        w = magnitudes[lo:kk + 1]
        if w.shape[0] < min_window:
            continue
        defined[i] = True
        thr[i] = float(np.quantile(w, q, method="linear"))
    return defined, thr


# --------------------------------------------------------------------------- #
# Pure computation — resolve one cell once (signal + null context + exhaustion features)
# --------------------------------------------------------------------------- #
def resolve_cell(instrument: str, domain: str, cell_index: int) -> CellResolved | None:
    """Resolve TRAIN N-PARTIAL-V2A events for one cell; align exhaustion features to r_e.

    Mirrors EXP-074's resolution exactly (cap added later as a boolean subset). Returns the
    certified r_e, the per-event ``msofar_atr`` / ``ss_excess`` (aligned to r_e order), the
    baseline q05 tail count, and the context needed to re-draw the matched-random null.
    """
    train_1m, train_end = load_train_1m(instrument)
    period, coverage = exp068.DOMAINS[domain]
    combined = exp068.build_domain(train_1m, period, coverage, train_end).sort("CloseTime")
    ohlc = exp068.real_ohlc(combined)
    if not bool(np.all(np.diff(ohlc["epoch"]) > 0)):
        raise RuntimeError(f"{instrument}-{domain}: TRAIN domain bars not strictly increasing")
    atr = exp068.wilder_atr(ohlc["high"], ohlc["low"], ohlc["close"], ATR_PERIOD)
    entry_idx = exp068.harami_entry_indices(combined, ohlc["epoch"])
    cell = f"{instrument}-{domain}"
    if entry_idx.shape[0] == 0:
        return None
    entry_epoch = ohlc["epoch"][entry_idx]
    ma = exp068._ma_context(ohlc, atr, entry_idx, entry_epoch)
    if ma.get("empty"):
        return None

    cond = ma["stat"]["retained_p75"] & (entry_epoch <= train_end)   # native /STRONG-STAT lower gate
    last_idx = int(ohlc["close"].shape[0]) - 1
    res = exp068.signal_arm(BINDING_OBJECT, ARM, ohlc, ma, cond, entry_idx, last_idx, cell_index)
    if res.m == 0:
        return None

    # Align exhaustion features to r_e via the certified qual mask + stable entry-order argsort.
    qual = res.qual
    order = np.argsort(entry_idx[qual], kind="stable")
    if not np.allclose(res.r_full[qual][order], res.r_e, equal_nan=True):
        raise RuntimeError(f"{cell}: feature/r_e alignment check failed")
    state, seg = ma["state"], ma["seg"]
    m_sofar, atr_entry = state.m_sofar, ma["atr_entry"]
    defined, thr = strong_stat_thr(state.k, seg["magnitude"])
    with np.errstate(divide="ignore", invalid="ignore"):
        msofar_atr_full = m_sofar / atr_entry
        ss_excess_full = m_sofar / thr
    bad = ~state.valid
    msofar_atr_full[bad] = np.nan
    ss_excess_full[bad | ~defined] = np.nan
    feats = {"msofar_atr": msofar_atr_full[qual][order],
             "ss_excess": ss_excess_full[qual][order]}

    q05 = float(np.quantile(res.r_e, Q05, method="linear"))
    n_q05 = int((res.r_e < q05).sum())

    # Matched-random null context (rebuilt exactly as EXP-068 _resolve_objects native path).
    state_all = exp068.live_in_progress_state(
        ohlc["epoch"], ohlc["close"], seg["confirm_epoch"], seg["end_price"],
        seg["end_epoch"], seg["direction"])
    _, warmup_all = exp068.adaptive_time_caps_by_epoch(
        ohlc["epoch"], seg["confirm_epoch"], seg["confirm_idx"])
    null_ctx = {"ohlc": ohlc, "state_all": state_all, "seg": seg, "warmup_all": warmup_all,
                "atr": ma["atr"], "signal_idx": entry_idx[cond], "last_idx": last_idx}
    return CellResolved(cell, instrument, domain, res.r_e, feats, int(res.m), n_q05, null_ctx)


# --------------------------------------------------------------------------- #
# Pure computation — metric vector on a retained subset (frozen bootstrap + matched-random null)
# --------------------------------------------------------------------------- #
def _seed(cell_index: int, sel: int, form_idx: int, thr_idx: int, purpose: int) -> list[int]:
    """Integer-only bootstrap seed (no hash() on labels)."""
    return [BASE_SEED, cell_index, sel, form_idx, thr_idx, purpose]


def _null_key(cell_index: int, sel: int, form_idx: int, thr_idx: int) -> int:
    """Distinct integer seed-key for the matched-random draw per (cell, arm); baseline == cell."""
    if sel == SEL_BASE:
        return cell_index                                  # reconciles baseline null to EXP-068
    return 1_000_000 + cell_index * 1_000 + sel * 100 + form_idx * 10 + thr_idx


def metric_on_subset(
    r_e: np.ndarray, keep: np.ndarray, n_base: int, ctx: dict[str, Any],
    cell_index: int, sel: int, form_idx: int, thr_idx: int,
) -> Metrics:
    """Compute the four-leg metric vector on a retained subset (NaN legs below the power floor).

    Signal legs bootstrap the retained r_e directly (frozen block bootstrap); beats-RM re-draws
    the matched-random null at the retained count and takes the median-contrast 1σ CI low.
    """
    r_sub = r_e[keep]
    n = int(r_sub.shape[0])
    retention = (n / n_base) if n_base > 0 else float("nan")
    if n < POWER_FLOOR:
        return Metrics(n, retention, float("nan"), float("nan"), float("nan"),
                       float("nan"), float("nan"))
    med_dist, _ = exp068.bootstrap_median_distribution(
        r_sub, np.random.default_rng(_seed(cell_index, sel, form_idx, thr_idx, P_MED)),
        n_boot=N_BOOT, batch=BOOT_BATCH)
    mean_dist, _ = exp068.bootstrap_stat_distribution(
        r_sub, np.random.default_rng(_seed(cell_index, sel, form_idx, thr_idx, P_MEAN)),
        "mean", n_boot=N_BOOT, batch=BOOT_BATCH)
    median_low = exp068.median_ci(med_dist)[0]
    mean_low = exp068.median_ci(mean_dist)[0]
    null = exp068.matched_random_arm(
        BINDING_OBJECT, ARM, ctx["ohlc"], ctx["state_all"], ctx["seg"], ctx["warmup_all"],
        ctx["atr"], ctx["signal_idx"], n, _null_key(cell_index, sel, form_idx, thr_idx),
        ctx["last_idx"])
    rm_low = exp068.contrast_ci(med_dist, null.dist)[0] if null.dist.shape[0] else float("nan")
    return Metrics(n, retention, float(np.mean(r_sub)), mean_low, float(np.median(r_sub)),
                   median_low, rm_low)


def cap_keep(feat: np.ndarray, u: float) -> np.ndarray:
    """Boolean retain mask for an upper exhaustion cap (NaN feature values are dropped)."""
    return np.isfinite(feat) & (feat <= u)


# --------------------------------------------------------------------------- #
# Pure computation — per-domain aggregation + locked-U selection + routing
# --------------------------------------------------------------------------- #
def select_global_u(
    domain_improved_by_p: dict[float, dict[str, bool]],
) -> tuple[float, int]:
    """Lock U at the grid percentile maximizing improved band-core domains; tie -> least restrictive."""
    best_p, best_n = PERCENTILES[0], -1
    for p in PERCENTILES:                                   # ascending; ties keep the highest p
        n_improved = sum(domain_improved_by_p[p][d] for d in BAND_CORE)
        if n_improved >= best_n:
            best_p, best_n = p, n_improved
    return best_p, best_n


def route(per_domain: dict[str, dict[str, Any]]) -> str:
    """Map the per-band-core-domain vector to the pinned four-tier routing verdict."""
    powered_domains = [d for d in BAND_CORE if per_domain[d]["n_powered"] >= MIN_POWERED_PER_DOMAIN]
    if len(powered_domains) < 2:
        return "INCONCLUSIVE_POWER"
    improved = [d for d in powered_domains if per_domain[d]["global_improved"]]
    hurt = [d for d in powered_domains if per_domain[d]["hurt"]]
    premium = float(np.nanmean([per_domain[d]["premium"] for d in powered_domains]))
    percell_uplift = [d for d in powered_domains if per_domain[d]["percell_uplift"] >= UPLIFT_BAR]
    if len(improved) >= 2 and not hurt and np.isfinite(premium) and premium <= OVERFIT_BAR:
        return "FILTER_PROMISING"
    if not percell_uplift:
        return "FILTER_INEFFECTIVE"
    return "FILTER_OVERFIT"


# --------------------------------------------------------------------------- #
# Plotting helpers (bounded; reuse computed tables — no data reload)
# --------------------------------------------------------------------------- #
def _save(fig: plt.Figure, name: str) -> None:
    fig.savefig(PLOTS_DIR / name, dpi=110, bbox_inches="tight")
    plt.close(fig)


def plot_domain_shares(per_domain: dict[str, dict[str, Any]], form: str) -> None:
    """Plot 1: per-domain improved-share, baseline vs M-GLOBAL-capped (band core + 5m disclosed)."""
    doms = list(BAND_CORE) + [DISCLOSED_DOMAIN]
    base = [per_domain[d]["baseline_share"] for d in doms]
    glob = [per_domain[d]["global_share"] for d in doms]
    x = np.arange(len(doms))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(x - 0.2, base, width=0.38, label="baseline", color="#999999")
    ax.bar(x + 0.2, glob, width=0.38, label=f"M-GLOBAL {form}", color="#2166ac")
    ax.axhline(SHARE_BAR, color="#d73027", ls="--", lw=1, label=f"share≥{SHARE_BAR:.0%}")
    ax.set_xticks(x, [f"{d}{'' if d in BAND_CORE else ' (disc)'}" for d in doms])
    ax.set_ylabel("improved-cell share")
    ax.set_title(f"Improved-cell share by domain — baseline vs M-GLOBAL ({form})")
    ax.legend(fontsize=8)
    _save(fig, "01_domain_improved_share.png")


def plot_mean_shift(cell_rows: list[dict[str, Any]], form: str) -> None:
    """Plot 2: per-cell raw-mean shift (capped − baseline), M-GLOBAL vs M-PERCELL (band core)."""
    g = [r[f"global_mean_{form}"] - r["base_mean"] for r in cell_rows
         if r["domain"] in BAND_CORE and r["powered"] and np.isfinite(r[f"global_mean_{form}"])]
    p = [r[f"percell_mean_{form}"] - r["base_mean"] for r in cell_rows
         if r["domain"] in BAND_CORE and r["powered"] and np.isfinite(r[f"percell_mean_{form}"])]
    if not g and not p:
        return
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.boxplot([g, p], tick_labels=["M-GLOBAL", "M-PERCELL"], showfliers=True)
    ax.axhline(0, color="#888", lw=0.8)
    ax.set_ylabel("raw-mean shift (capped − baseline), ATR units")
    ax.set_title(f"Raw-mean lift across band-core cells ({form})")
    _save(fig, "02_mean_shift_global_vs_percell.png")


def plot_overfit_premium(per_domain: dict[str, dict[str, Any]], form: str) -> None:
    """Plot 3: per-domain overfit premium (M-PERCELL share − M-GLOBAL share)."""
    doms = list(BAND_CORE)
    prem = [per_domain[d]["premium"] for d in doms]
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(doms, prem, color="#762a83")
    ax.axhline(OVERFIT_BAR, color="#d73027", ls="--", lw=1, label=f"bar {OVERFIT_BAR:.0%}")
    ax.set_ylabel("overfit premium (M-PERCELL − M-GLOBAL share)")
    ax.set_title(f"Overfit premium by domain ({form})")
    ax.legend(fontsize=8)
    _save(fig, "03_overfit_premium.png")


def plot_retention_tradeoff(cell_rows: list[dict[str, Any]], form: str) -> None:
    """Plot 4: retention vs raw-mean-gain trade-off across band-core cells (M-GLOBAL)."""
    xs, ys = [], []
    for r in cell_rows:
        if r["domain"] in BAND_CORE and r["powered"] and np.isfinite(r[f"global_ret_{form}"]):
            xs.append(r[f"global_ret_{form}"])
            ys.append(r[f"global_mean_{form}"] - r["base_mean"])
    if not xs:
        return
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(xs, ys, s=18, alpha=0.7, color="#1b7837")
    ax.axvline(RETENTION_FLOOR, color="#d73027", ls="--", lw=1, label=f"retention {RETENTION_FLOOR:.0%}")
    ax.axhline(0, color="#888", lw=0.8)
    ax.set_xlabel("retention fraction")
    ax.set_ylabel("raw-mean gain (capped − baseline)")
    ax.set_title(f"Retention vs mean-gain trade-off ({form}, M-GLOBAL)")
    ax.legend(fontsize=8)
    _save(fig, "04_retention_tradeoff.png")


def plot_u_sensitivity(sens: dict[str, dict[float, int]]) -> None:
    """Plot 5: count of improved band-core domains vs U-percentile, per form (M-GLOBAL)."""
    fig, ax = plt.subplots(figsize=(6, 4))
    for form, series in sens.items():
        ax.plot([f"{int(p*100)}" for p in PERCENTILES], [series[p] for p in PERCENTILES],
                marker="o", label=form)
    ax.set_xlabel("U pooled percentile")
    ax.set_ylabel("improved band-core domains")
    ax.set_yticks(range(0, len(BAND_CORE) + 1))
    ax.set_title("U-sensitivity: improved band-core domains by percentile")
    ax.legend(fontsize=8)
    _save(fig, "05_u_sensitivity.png")


def plot_continuity(r_e: np.ndarray, keep: np.ndarray) -> None:
    """Plot 6: GBPUSD-5m r_e before/after the locked F1 cap (disclosed; 5m non-binding)."""
    fig, ax = plt.subplots(figsize=(6, 4))
    lo, hi = float(np.quantile(r_e, 0.01)), float(np.quantile(r_e, 0.99))
    bins = np.linspace(lo, hi, 40)
    ax.hist(r_e, bins=bins, alpha=0.5, label=f"baseline (n={r_e.shape[0]})", color="#999999")
    ax.hist(r_e[keep], bins=bins, alpha=0.6, label=f"capped (n={int(keep.sum())})", color="#2166ac")
    ax.axvline(0, color="#d73027", lw=1)
    ax.set_xlabel("r_e (ATR units)")
    ax.set_ylabel("count")
    ax.set_title(f"{CONTINUITY_CELL} r_e before/after locked F1 cap (disclosed)")
    ax.legend(fontsize=8)
    _save(fig, "06_continuity_gbpusd5m.png")


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def pass_a(cell_index_map: dict[str, int]) -> tuple[list[dict[str, Any]], dict[str, list[float]]]:
    """Pass A: resolve every cell; baseline + M-PERCELL metrics; collect band-core pools.

    Returns (cell_rows, pools). Resolutions are discarded per cell (bounded memory); pass B
    re-resolves the band-core + 5m cells it needs (the bootstrap, not the resolve, dominates).
    """
    cell_rows: list[dict[str, Any]] = []
    pools: dict[str, list[float]] = {"msofar_atr": [], "ss_excess": []}
    recon_fail: list[str] = []
    for inst, dom, _ in tqdm(CELLS, desc="pass A (resolve + baseline + M-PERCELL)"):
        ci = cell_index_map[f"{inst}-{dom}"]
        rc = resolve_cell(inst, dom, ci)
        if rc is None:
            continue
        ref = load_exp074_re(rc.cell)
        if ref is not None and not (ref.shape == rc.r_e.shape
                                    and np.allclose(ref, rc.r_e, atol=1e-9, equal_nan=True)):
            recon_fail.append(rc.cell)
        powered = rc.n_q05 >= POWER_FLOOR
        full = np.ones(rc.r_e.shape[0], dtype=bool)
        base = metric_on_subset(rc.r_e, full, rc.n_base, rc.null_ctx, ci, SEL_BASE, 0, 0)
        row: dict[str, Any] = {
            "cell": rc.cell, "instrument": inst, "domain": dom, "powered": powered,
            "n_base": rc.n_base, "n_q05": rc.n_q05, "base_mean": base.mean,
            "base_improved": base.improved}
        if powered and dom in BAND_CORE:
            pools["msofar_atr"].extend(rc.feats["msofar_atr"][np.isfinite(rc.feats["msofar_atr"])])
            pools["ss_excess"].extend(rc.feats["ss_excess"][np.isfinite(rc.feats["ss_excess"])])
        for form, fkey in FORMS:                            # M-PERCELL: per-cell percentile grid
            best = _best_percell(rc, ci, form, fkey)
            row[f"percell_improved_{form}"] = best["improved"]
            row[f"percell_mean_{form}"] = best["mean"]
            # Disclose the undefined-feature share: the cap drops NaN-feature events, so events
            # the cap structurally cannot retain still count in n_base. Recording this lets a
            # retention-floor failure be attributed correctly (feature-undefinedness vs the cap).
            n_fin = int(np.isfinite(rc.feats[fkey]).sum())
            row[f"undef_share_{form}"] = float(1.0 - n_fin / rc.n_base) if rc.n_base else float("nan")
        cell_rows.append(row)
    if recon_fail:
        raise RuntimeError(f"baseline r_e reconciliation FAILED vs EXP-074: {recon_fail}")
    return cell_rows, pools


def _best_percell(rc: CellResolved, ci: int, form: str, fkey: str) -> dict[str, Any]:
    """M-PERCELL diagnostic ceiling: best of the cell's own {p85,p90,p95} caps (never deployed)."""
    feat = rc.feats[fkey]
    fin = feat[np.isfinite(feat)]
    best = {"improved": False, "mean": float("nan"), "mean_low": -np.inf}
    if fin.shape[0] < POWER_FLOOR:
        return best
    for ti, p in enumerate(PERCENTILES):
        u = float(np.quantile(fin, p, method="linear"))
        m = metric_on_subset(rc.r_e, cap_keep(feat, u), rc.n_base, rc.null_ctx,
                             ci, SEL_PERCELL, FORM_IDX[form], ti)
        if m.improved and not best["improved"]:
            best = {"improved": True, "mean": m.mean, "mean_low": m.mean_ci_low_1s}
        elif (not best["improved"] and m.retention >= RETENTION_FLOOR
              and np.isfinite(m.mean_ci_low_1s) and m.mean_ci_low_1s > best["mean_low"]):
            best = {"improved": False, "mean": m.mean, "mean_low": m.mean_ci_low_1s}
    return best


def pass_b(
    cell_rows: list[dict[str, Any]], u_global: dict[str, dict[float, float]],
    cell_index_map: dict[str, int],
) -> tuple[dict[str, dict[float, dict[str, bool]]], dict[tuple[str, str, float], Metrics],
           CellResolved | None]:
    """Pass B: evaluate the single uniform cap (M-GLOBAL) at each pooled U on band-core + 5m cells.

    Re-resolves each band-core + 5m cell (bounded memory). Returns the per-(form, percentile,
    domain) improved flags, the per-(cell, form, percentile) M-GLOBAL metric cache, and the
    continuity-cell resolution (for the disclosed before/after plot).
    """
    improved_by: dict[str, dict[float, dict[str, bool]]] = {
        form: {p: {d: False for d in BAND_CORE} for p in PERCENTILES} for form, _ in FORMS}
    cache: dict[tuple[str, str, float], Metrics] = {}
    continuity: CellResolved | None = None
    passb = [(inst, dom) for inst, dom, _ in CELLS if dom in PASSB_DOMAINS]
    for inst, dom in tqdm(passb, desc="pass B (M-GLOBAL)"):
        cell = f"{inst}-{dom}"
        ci = cell_index_map[cell]
        rc = resolve_cell(inst, dom, ci)
        if rc is None:
            continue
        if cell == CONTINUITY_CELL:
            continuity = rc
        for form, fkey in FORMS:
            for ti, p in enumerate(PERCENTILES):
                m = metric_on_subset(rc.r_e, cap_keep(rc.feats[fkey], u_global[form][p]),
                                     rc.n_base, rc.null_ctx, ci, SEL_GLOBAL, FORM_IDX[form], ti)
                cache[(cell, form, p)] = m
    for form, _ in FORMS:
        for p in PERCENTILES:
            for d in BAND_CORE:
                improved_by[form][p][d] = _domain_improved(cell_rows, cache, form, p, d)
    return improved_by, cache, continuity


def _domain_improved(
    cell_rows: list[dict[str, Any]], cache: dict[tuple[str, str, float], Metrics],
    form: str, p: float, domain: str,
) -> bool:
    """Is a domain 'improved' under M-GLOBAL(form, p): Δ≥uplift ∧ capped share≥SHARE_BAR ∧ no hurt."""
    powered = [r for r in cell_rows if r["domain"] == domain and r["powered"]]
    if len(powered) < MIN_POWERED_PER_DOMAIN:
        return False
    base_share = float(np.mean([float(r["base_improved"]) for r in powered]))
    capped = [cache[(r["cell"], form, p)].improved for r in powered if (r["cell"], form, p) in cache]
    if not capped:
        return False
    cap_share = float(np.mean([float(c) for c in capped]))
    delta = cap_share - base_share
    return cap_share >= SHARE_BAR and delta >= UPLIFT_BAR


def build_per_domain(
    cell_rows: list[dict[str, Any]], cache: dict[tuple[str, str, float], Metrics],
    form: str, locked_p: float,
) -> dict[str, dict[str, Any]]:
    """Per-domain summary at the locked M-GLOBAL percentile (band core binding; 5m disclosed)."""
    out: dict[str, dict[str, Any]] = {}
    for d in list(BAND_CORE) + [DISCLOSED_DOMAIN]:
        powered = [r for r in cell_rows if r["domain"] == d and r["powered"]]
        n_pow = len(powered)
        base_share = float(np.mean([float(r["base_improved"]) for r in powered])) if powered else float("nan")
        glob = [cache[(r["cell"], form, locked_p)].improved for r in powered
                if (r["cell"], form, locked_p) in cache]
        perc = [bool(r[f"percell_improved_{form}"]) for r in powered]
        g_share = float(np.mean([float(x) for x in glob])) if glob else float("nan")
        p_share = float(np.mean([float(x) for x in perc])) if perc else float("nan")
        delta = g_share - base_share if np.isfinite(g_share) and np.isfinite(base_share) else float("nan")
        out[d] = {
            "n_powered": n_pow, "baseline_share": base_share, "global_share": g_share,
            "percell_share": p_share, "uplift": delta,
            "percell_uplift": (p_share - base_share) if np.isfinite(p_share) else float("nan"),
            "premium": (p_share - g_share) if np.isfinite(p_share) and np.isfinite(g_share) else float("nan"),
            "hurt": bool(np.isfinite(delta) and delta <= HURT_BAR),
            "global_improved": bool(np.isfinite(delta) and g_share >= SHARE_BAR and delta >= UPLIFT_BAR),
        }
    return out


def attach_cell_global(
    cell_rows: list[dict[str, Any]], cache: dict[tuple[str, str, float], Metrics],
    locked_p: dict[str, float],
) -> None:
    """Fill per-cell M-GLOBAL mean/retention at the locked percentile for plotting."""
    for r in cell_rows:
        for form, _ in FORMS:
            m = cache.get((r["cell"], form, locked_p[form]))
            r[f"global_mean_{form}"] = m.mean if m else float("nan")
            r[f"global_ret_{form}"] = m.retention if m else float("nan")


def run() -> dict[str, Any]:
    """Two-pass TRAIN design: resolve + M-PERCELL (A), M-GLOBAL + lock + route (B/C)."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    cell_index_map = {f"{inst}-{dom}": i for i, (inst, dom, _) in enumerate(CELLS)}

    cell_rows, pools = pass_a(cell_index_map)

    # Pooled M-GLOBAL thresholds from the band-core pool (one scalar per form per percentile).
    u_global: dict[str, dict[float, float]] = {}
    for form, fkey in FORMS:
        arr = np.asarray(pools[fkey], dtype=np.float64)
        u_global[form] = {p: float(np.quantile(arr, p, method="linear")) for p in PERCENTILES} \
            if arr.shape[0] else {p: float("nan") for p in PERCENTILES}

    improved_by, cache, continuity = pass_b(cell_rows, u_global, cell_index_map)

    # Lock U per form (pre-registered rule), pick the lead-form (F1) verdict.
    locked_p = {form: select_global_u(improved_by[form])[0] for form, _ in FORMS}
    locked = {form: u_global[form][locked_p[form]] for form, _ in FORMS}
    attach_cell_global(cell_rows, cache, locked_p)

    lead = "F1"
    per_domain = build_per_domain(cell_rows, cache, lead, locked_p[lead])
    per_domain_f2 = build_per_domain(cell_rows, cache, "F2", locked_p["F2"])
    verdict = route(per_domain)

    sens = {form: {p: sum(improved_by[form][p][d] for d in BAND_CORE) for p in PERCENTILES}
            for form, _ in FORMS}
    _write_outputs(cell_rows, per_domain, per_domain_f2, u_global, locked_p, locked, verdict, sens)
    _make_plots(cell_rows, per_domain, continuity, locked, sens, lead)
    return {"verdict": verdict, "lead": lead, "locked_p": locked_p, "locked_u": locked,
            "per_domain": per_domain}


def _write_outputs(
    cell_rows: list[dict[str, Any]], per_domain: dict[str, dict[str, Any]],
    per_domain_f2: dict[str, dict[str, Any]], u_global: dict[str, dict[float, float]],
    locked_p: dict[str, float], locked: dict[str, float], verdict: str,
    sens: dict[str, dict[float, int]],
) -> None:
    """Write per-cell CSV, per-domain verdict JSON, hash-pinned locked filter, run metadata."""
    pl.DataFrame([{k: v for k, v in r.items() if not k.startswith("_")} for r in cell_rows]
                 ).write_csv(RESULTS_DIR / "cell_metrics.csv")
    (RESULTS_DIR / "domain_verdict.json").write_text(json.dumps(
        {"lead_form": "F1", "verdict": verdict, "band_core": list(BAND_CORE),
         "per_domain_F1": per_domain, "per_domain_F2_disclosed": per_domain_f2,
         "u_sensitivity": {f: {f"{p}": v for p, v in s.items()} for f, s in sens.items()}},
        indent=2, default=str))
    locked_spec = {
        "experiment_id": EXPERIMENT_ID, "object": BINDING_OBJECT, "arm": BINDING_ARM,
        "lead_form": "F1", "feature": "msofar_atr",
        "locked_percentile": locked_p["F1"], "locked_U": locked["F1"],
        "F2_disclosed": {"feature": "ss_excess", "locked_percentile": locked_p["F2"],
                         "locked_U": locked["F2"]},
        "band": list(BAND_CORE), "disclosed_domain": DISCLOSED_DOMAIN,
        "rule": "upper cap: keep entries with msofar_atr <= locked_U (native /STRONG-STAT p75 "
                "lower gate retained); pooled-TRAIN quantile; M-PERCELL diagnostic-only",
        "deployable": verdict == "FILTER_PROMISING",
        "note": "TRAIN-locked; NON-CONFIRMATORY until a separate one-shot sealed-holdout read",
    }
    blob = json.dumps(locked_spec, sort_keys=True, default=str).encode()
    locked_spec["sha256"] = hashlib.sha256(blob).hexdigest()
    (RESULTS_DIR / "locked_filter.json").write_text(json.dumps(locked_spec, indent=2, default=str))
    powered = sum(r["powered"] for r in cell_rows)
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps({
        "experiment_id": EXPERIMENT_ID, "hypothesis": "HYP-028", "family": "CF-HA-HARAMI-001",
        "stratum": "TRAIN only [0, train_cutoff); TEST not read; holdout sealed",
        "design": "TRAIN-design-and-lock; endpoint = strategy legs; per-band-core-domain binding",
        "n_cells": len(CELLS), "n_powered": int(powered), "n_boot": N_BOOT, "base_seed": BASE_SEED,
        "percentile_grid": list(PERCENTILES), "retention_floor": RETENTION_FLOOR,
        "uplift_bar": UPLIFT_BAR, "hurt_bar": HURT_BAR, "overfit_bar": OVERFIT_BAR,
        "u_global": {f: {f"{p}": v for p, v in d.items()} for f, d in u_global.items()},
        "locked_percentile": locked_p, "locked_U": locked, "verdict": verdict,
        "fence": "load_train_1m slices [0, train_cutoff) only; cap removes entries (causal)",
    }, indent=2, default=str))


def _make_plots(
    cell_rows: list[dict[str, Any]], per_domain: dict[str, dict[str, Any]],
    continuity: CellResolved | None, locked: dict[str, float],
    sens: dict[str, dict[float, int]], lead: str,
) -> None:
    """Render the six bounded plots from in-memory tables (no data reload)."""
    plot_domain_shares(per_domain, lead)
    plot_mean_shift(cell_rows, lead)
    plot_overfit_premium(per_domain, lead)
    plot_retention_tradeoff(cell_rows, lead)
    plot_u_sensitivity(sens)
    if continuity is not None:
        plot_continuity(continuity.r_e, cap_keep(continuity.feats["msofar_atr"], locked[lead]))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    LOGGER.info("EXP-075: TRAIN design of an exhaustion-cap entry filter (CF-HA-HARAMI-001/HYP-028)")
    summary = run()
    print("\n=== EXP-075 complete ===")
    print(f"lead form: {summary['lead']}  locked percentile: {summary['locked_p']}  "
          f"locked U: {summary['locked_u']}")
    print("per-band-core-domain (F1, binding):")
    for d in BAND_CORE:
        pd = summary["per_domain"][d]
        print(f"  {d:4} n_pow={pd['n_powered']:2}  base={pd['baseline_share']:.2f} "
              f"global={pd['global_share']:.2f} Δ={pd['uplift']:+.2f} "
              f"premium={pd['premium']:+.2f} {'HURT' if pd['hurt'] else ''}"
              f"{' IMPROVED' if pd['global_improved'] else ''}")
    print(f"ROUTING VERDICT: {summary['verdict']}")
    print(f"artifacts -> {RESULTS_DIR}")


if __name__ == "__main__":
    main()
