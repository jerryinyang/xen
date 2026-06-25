"""EXP-095 — Portfolio Construction & Online-Adaptive Risk Model (RSI-2 Fade, 8 confirmed cells).

Phase 022 / ``CF-MR-001`` / HYP-003 — the deployment-economics leg. Governing design/D0:
``docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/`` (``design.md`` §3-4 EXP-095,
``D0-predeclarations.md`` D1-D9 + the ratified-parameter table). Analysis-plan: ``analysis-plan.md``.

What this is. Built from the 8 G-021-confirmed cells, construct a causal, parameter-free ERC portfolio
(static **A** vs circuit-breaker **B**), compare its risk-adjusted performance to the best individual cell
(and a naive inverse-vol contrast), and **calibrate + bite-check** the NEW portfolio-level holdout
confirmation statistic that G-022a will freeze. Analysis-set only (TRAIN + the EXP-093 already-resolved
analysis-TEST series reused as portfolio-aggregate disclosure); **0 counted TEST reads, 0 candidate slots,
final-30% global holdout NEVER loaded**. No binding holdout verdict is issued here.

Substrate reuse (verbatim). The EXP-090 module (``build_cell_context``, ``resolve_arm``/RCT, the 1-minute
intrabar fill, ``net_return_atr``) and the EXP-092/093 cost overlay (``D0-amendment-003``) are imported
unchanged. The per-cell timestamped per-trade streams a portfolio curve needs were never persisted by
EXP-093 (only summary CSVs), so they are **deterministically regenerated** through this identical frozen
path and a **provenance gate** reconciles the regenerated analysis-TEST per-cell summary to EXP-093's
``test_per_cell.csv`` (<=1e-9 ATR on means/medians, exact on counts) before any portfolio math.

Construction (frozen D0). ERC weights from a trailing 90-trading-day Ledoit-Wolf covariance (causal),
weekly rebalance, 10% annualized vol anchor, 1.5x concurrent-risk cap; B adds a trailing-50-trade
circuit-breaker (multiplier 0 while a cell's trailing mean net return < 0). The equity curve is marked on
the 1h grid (4h trades realized at exit; closed-market steps flat = 0, identically for every portfolio).
The binding Sharpe statistic + its moving-block bootstrap one-sided lower bound run on the
cadence-aggregated (weekly) return series (block = rebalance cadence). Co-binding companion: pooled net
per-trade expectancy lower bound.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

for _thread_var in ("POLARS_MAX_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                    "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_thread_var, "1")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import polars as pl  # noqa: E402
from tqdm.auto import tqdm  # noqa: E402

from xen.ass import default_block_length, moving_block_bootstrap_cis  # noqa: E402
from xen.capgeo_cost import event_costs, holding_days  # noqa: E402
from xen.intrabar_fill import net_return_atr  # noqa: E402
from xen.referee_calibration import seed_for  # noqa: E402
from xen import portfolio as pf  # noqa: E402

# --------------------------------------------------------------------------- #
# Path setup + EXP-090 substrate reuse (import the validated module directly)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-095"
CODE_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = CODE_DIR.parent
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
EXP_ROOT = EXPERIMENT_DIR.parent
EXP090_CODE = EXP_ROOT / "EXP-090" / "code" / "run_experiment.py"
EXP093_TEST_PER_CELL = EXP_ROOT / "EXP-093" / "results" / "test_per_cell.csv"


def _load_exp090() -> Any:
    """Import the validated EXP-090 module (import-safe: ``main`` guarded; reuses its substrate)."""
    if not EXP090_CODE.exists():
        raise FileNotFoundError(f"EXP-090 module missing: {EXP090_CODE}")
    spec = importlib.util.spec_from_file_location("exp090_mr_readiness", EXP090_CODE)
    if spec is None or spec.loader is None:                       # pragma: no cover - defensive
        raise ImportError(f"Could not load EXP-090 from {EXP090_CODE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


E90 = _load_exp090()
E90.DOMAINS["4h"] = 240                                  # 4h ADMITTED (D0-amendment-004/005; EXP-094)

# --------------------------------------------------------------------------- #
# Constants (frozen at D0 ratified table; seeds recorded — NEVER tuned here)
# --------------------------------------------------------------------------- #
MASTER_SEED = 20260624
ARM = "RCT"                                              # EXIT-RCT (the confirmed exit)

# Deployable set (D0 param #1): the 8 G-021-confirmed cells.
CELLS: tuple[tuple[str, str], ...] = (
    ("EURUSD", "4h"), ("XAUUSD", "4h"), ("USDCHF", "4h"), ("AUDJPY", "4h"),
    ("EURJPY", "4h"), ("GBPJPY", "4h"), ("USTEC", "1h"), ("US2000", "1h"),
)

# Phase-021 cost table (D0-amendment-003; identical to EXP-093). Shared COST_CONSTANTS NOT mutated.
MR_COST_RT_BPS: dict[str, float] = {
    "EURUSD": 3.0, "USDCHF": 4.0, "XAUUSD": 6.0, "EURJPY": 6.0, "GBPJPY": 6.0, "AUDJPY": 6.0,
    "USTEC": 5.0, "US2000": 6.0,
}
FIN_BPS_DAY = 0.0

# Grid + portfolio construction (frozen D0 ratified table; brackets are DISCLOSURE only, never selected).
STEP_SECONDS = 3_600                                    # 1h common grid (finest deployable domain close)
SECONDS_PER_YEAR = 31_557_600                           # 365.25 * 86400
PERIODS_PER_YEAR_HOURLY = SECONDS_PER_YEAR / STEP_SECONDS          # ~8766 (equity / MaxDD scale)
REBALANCE_STEPS = 7 * 24                                # weekly (param #4)
LOOKBACK_STEPS = 90 * 24                                # trailing 90 trading days (param #3)
TARGET_ANN_VOL = 0.10                                   # 10% annualized vol anchor (param #5)
CAP_MULT = 1.5                                          # concurrent-risk cap 1.5x (param #6)
BREAKER_WINDOW = 50                                     # trailing-50-trade circuit-breaker (param #7)
CADENCE_STEPS = REBALANCE_STEPS                         # Sharpe statistic on weekly-aggregated returns
PERIODS_PER_YEAR_CADENCE = SECONDS_PER_YEAR / (CADENCE_STEPS * STEP_SECONDS)   # ~52.18 weekly

# Inference (D4/D6). Binding holdout statistic uses N_BOOT; calibration uses CAL_N_BOOT (FPR robust).
N_BOOT = 10_000
CAL_N_BOOT = 2_000
BOOT_ALPHA = 0.10                                       # 90% CI -> 5th pct one-sided ~95% lower bound
N_NULL = 1_000                                          # synthetic-null replicates (FPR; Wilson-hi)
FPR_TARGET = 0.05                                       # binding FPR ceiling (D6)
BITE_FIRE_FLOOR = 0.80                                  # power floor that defines the gate MDE m* (A4)
BITE_PLANT_GRID = tuple(round(x, 2) for x in np.arange(0.25, 10.01, 0.25))  # planted-Sharpe sweep (A4 MDE)
PROVENANCE_TOL = 1e-9                                   # ATR reconciliation tolerance vs EXP-093

# Disclosed sensitivity brackets (reported, NEVER used to select a binding value).
COV_WINDOW_BRACKET_DAYS = (60, 120)
VOL_TARGET_BRACKET = (0.07, 0.15)

DETERMINISM_CELLS = (("EURUSD", "4h"), ("USTEC", "1h"))
LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# Dataclasses / types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CellResolution:
    """Full-analysis-set resolved EXIT-RCT stream for one cell + the TEST-subset provenance summary."""

    name: str
    stream: pf.CellStream                  # resolved trades over the full analysis set (for the curve)
    test_net_mean: float
    test_net_median: float
    test_n_resolved: int
    test_resolved_frac: float


# --------------------------------------------------------------------------- #
# I/O helpers (analysis-set slice; the final-30% global holdout is never loaded)
# --------------------------------------------------------------------------- #
def load_analysis_1m(instrument: str, path: Path) -> tuple[pl.DataFrame, int, dict[str, Any]]:
    """Load the analysis set ``[0, int(total*0.7))`` and the analysis-TEST start epoch ``ts_lo``.

    Mirrors EXP-093's loader exactly: the full first-70% analysis set (TRAIN region = causal warmup),
    the analysis-TEST left edge ``ts_lo = CloseTime[int(int(total*0.7)*0.7)]``. The **final-30% global
    holdout is never sliced or materialized**.
    """
    scan = pl.scan_parquet(path).sort("CloseTime")
    total_rows = int(scan.select(pl.len()).collect().item())
    analysis_cutoff = int(total_rows * 0.7)
    train_cutoff = int(analysis_cutoff * 0.7)
    frame = scan.slice(0, analysis_cutoff).collect()
    if frame.height != analysis_cutoff:                          # 0 holdout rows read (assert)
        raise RuntimeError(f"{instrument}: analysis slice {frame.height} != {analysis_cutoff}")
    if not frame.get_column("CloseTime").is_sorted():
        raise RuntimeError(f"{instrument}: analysis slice not sorted by CloseTime")
    ts_lo_epoch = int(frame.get_column("CloseTime").dt.epoch("s").to_numpy()[train_cutoff])
    meta = {"source_file": path.name, "total_rows": total_rows, "analysis_rows": analysis_cutoff,
            "train_rows": train_cutoff, "test_rows": analysis_cutoff - train_cutoff,
            "analysis_end": str(frame.get_column("CloseTime").max())}
    return frame, ts_lo_epoch, meta


# --------------------------------------------------------------------------- #
# Pure computation — resolve real EXIT-RCT exits over the full analysis set (per-trade stream)
# --------------------------------------------------------------------------- #
def mtm_marks(entry_epoch: np.ndarray, exit_epoch: np.ndarray, entry_price: np.ndarray,
              atr_entry: np.ndarray, direction: np.ndarray, exit_fill: np.ndarray, net: np.ndarray,
              minute_open: np.ndarray, minute_close_epoch: np.ndarray, step: int,
              ) -> tuple[np.ndarray, np.ndarray]:
    """Per-position intra-1h mark-to-market increments (D0 §D2.1 / amendment-001 A1).

    For each resolved position, book the per-1h **unrealized-P&L increment** at every 1h close in
    ``(entry, exit]`` using the position's real causal price path: ``entry_price`` at entry, the causal
    ``minute_open`` of the most recent 1-minute bar at each intervening 1h boundary, and the real
    ``exit_fill`` at exit. Increments telescope to the position's geometric gross; the **final mark is
    pinned so the increments sum exactly to the realized net** ``net`` reused from EXP-090/093 (this
    absorbs cost + any convention into the exit step → the realized total is never altered, only its path
    is distributed). Same-bar exits (``exit <= entry``) book the whole ``net`` at the entry step. Returns
    flat ``(mark_epoch, mark_return)`` arrays across all positions (causal; holdout-fenced by the caller).
    """
    epochs_out: list[np.ndarray] = []
    vals_out: list[np.ndarray] = []
    n_min = minute_open.shape[0]
    for j in range(entry_epoch.shape[0]):
        e, x = int(entry_epoch[j]), int(exit_epoch[j])
        if x <= e:                                               # same-bar / degenerate: lump at entry step
            epochs_out.append(np.array([e], dtype=np.int64))
            vals_out.append(np.array([net[j]], dtype=np.float64))
            continue
        bnds = np.arange(e + step, x + step, step, dtype=np.int64)         # 1h marks; last element == x
        if bnds.shape[0] > 1:
            inter = bnds[:-1]
            pos = np.clip(np.searchsorted(minute_close_epoch, inter, side="right") - 1, 0, n_min - 1)
            p_inter = minute_open[pos]                            # causal real price at each 1h boundary
        else:
            p_inter = np.empty(0, dtype=np.float64)
        prices = np.concatenate([[entry_price[j]], p_inter, [exit_fill[j]]])
        incr = direction[j] * np.diff(prices) / atr_entry[j]     # telescopes to geometric gross
        incr[-1] += net[j] - incr.sum()                          # pin total to realized net (cost at exit)
        if abs(float(incr.sum()) - float(net[j])) > 1e-9:        # binding conservation invariant
            raise RuntimeError(f"MTM conservation failed at position {j}: "
                               f"{float(incr.sum())} != {float(net[j])}")
        epochs_out.append(bnds)
        vals_out.append(incr)
    if not epochs_out:
        return np.empty(0, dtype=np.int64), np.empty(0, dtype=np.float64)
    return np.concatenate(epochs_out), np.concatenate(vals_out)


def resolve_cell(ctx: Any, ts_lo_epoch: int, instrument: str, domain: str) -> CellResolution:
    """Resolve all real CORE fade entries through EXIT-RCT + cost; return the per-trade + MTM streams.

    Resolving all entries at once and subsetting is identical to resolving subsets (the engine is
    per-event independent), so the analysis-TEST subset reproduces EXP-093 exactly (the provenance gate).
    The realized per-trade net return is booked at the event's **exit** ``CloseTime`` (trade stream, for
    counts/breaker + pooled expectancy); the **intra-1h MTM increments** (amendment-001 A1) carry the
    open-position path for the binding Sharpe/MaxDD series.
    """
    idx = ctx.core_entry_idx
    direction = ctx.core_direction
    res = E90.resolve_arm(ctx, idx, direction, ARM, ctx.minute_high, ctx.minute_low, ctx.minute_open)
    gross = net_return_atr(res.fill_price, ctx.close[idx], direction, ctx.atr[idx])
    hd = holding_days(idx, res.exit_domain_idx, E90.DOMAINS[domain])
    p_entry, atr_entry = ctx.close[idx], ctx.atr[idx]
    keep = (res.resolved & np.isfinite(gross) & np.isfinite(atr_entry) & (atr_entry > 0.0)
            & np.isfinite(hd) & (hd >= 0.0))
    net_all = np.full(idx.shape[0], np.nan, dtype=np.float64)
    if np.any(keep):
        costs = event_costs(gross[keep], p_entry[keep], atr_entry[keep], hd[keep],
                            rt_bps=MR_COST_RT_BPS[instrument], fin_bps_day=FIN_BPS_DAY)
        net_all[keep] = costs.net
    entry_epoch = ctx.domain_close_epoch[idx].astype(np.int64)
    safe_exit = np.clip(res.exit_domain_idx, 0, ctx.n_domain - 1)
    exit_epoch = np.where(res.exit_domain_idx >= 0, ctx.domain_close_epoch[safe_exit], -1).astype(np.int64)
    name = f"{instrument}-{domain}"
    mark_epoch, mark_return = mtm_marks(
        entry_epoch[keep], exit_epoch[keep], p_entry[keep], atr_entry[keep], direction[keep],
        res.fill_price[keep], net_all[keep], ctx.minute_open, ctx.minute_close_epoch, STEP_SECONDS)
    stream = pf.CellStream(name=name, entry_epoch=entry_epoch[keep], exit_epoch=exit_epoch[keep],
                           net=net_all[keep], mark_epoch=mark_epoch, mark_return=mark_return)
    # Provenance: analysis-TEST subset (entry domain CloseTime >= ts_lo) vs EXP-093.
    test_mask = entry_epoch >= ts_lo_epoch
    resolved_frac = float(np.mean(res.resolved[test_mask])) if np.any(test_mask) else float("nan")
    kt = keep & test_mask
    n_res = int(np.count_nonzero(kt))
    t_mean = float(np.mean(net_all[kt])) if n_res else float("nan")
    t_median = float(np.median(net_all[kt])) if n_res else float("nan")
    return CellResolution(name=name, stream=stream, test_net_mean=t_mean, test_net_median=t_median,
                          test_n_resolved=n_res, test_resolved_frac=resolved_frac)


def reconcile_provenance(resolutions: list[CellResolution]) -> list[dict[str, Any]]:
    """Reconcile the regenerated analysis-TEST per-cell summary to EXP-093 ``test_per_cell.csv``.

    Hard-fail on any mismatch beyond tolerance (means/medians <= 1e-9 ATR; exact on integer counts) so
    the "reused verbatim" claim is a checked fact, not an assertion.
    """
    if not EXP093_TEST_PER_CELL.exists():
        raise FileNotFoundError(f"provenance gate: missing EXP-093 {EXP093_TEST_PER_CELL}")
    ref = {r["cell"]: r for r in pl.read_csv(EXP093_TEST_PER_CELL).iter_rows(named=True)}
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for cr in resolutions:
        r = ref.get(cr.name)
        if r is None:
            failures.append(f"{cr.name}: absent from EXP-093 test_per_cell.csv")
            continue
        d_mean = abs(cr.test_net_mean - float(r["net_mean"]))
        d_med = abs(cr.test_net_median - float(r["net_median"]))
        cnt_ok = cr.test_n_resolved == int(r["n_resolved"])
        frac_ok = abs(cr.test_resolved_frac - float(r["resolved_frac"])) <= PROVENANCE_TOL
        ok = d_mean <= PROVENANCE_TOL and d_med <= PROVENANCE_TOL and cnt_ok and frac_ok
        rows.append({"cell": cr.name, "regen_net_mean": cr.test_net_mean,
                     "exp093_net_mean": float(r["net_mean"]), "abs_diff_mean": d_mean,
                     "regen_net_median": cr.test_net_median, "exp093_net_median": float(r["net_median"]),
                     "abs_diff_median": d_med, "regen_n_resolved": cr.test_n_resolved,
                     "exp093_n_resolved": int(r["n_resolved"]), "count_match": cnt_ok,
                     "regen_resolved_frac": cr.test_resolved_frac,
                     "exp093_resolved_frac": float(r["resolved_frac"]), "PASS": ok})
        if not ok:
            failures.append(f"{cr.name}: dmean={d_mean:.2e} dmed={d_med:.2e} cnt_ok={cnt_ok} "
                            f"frac_ok={frac_ok}")
    if failures:
        raise RuntimeError("PROVENANCE GATE FAILED (regenerated stream != EXP-093):\n  "
                           + "\n  ".join(failures))
    return rows


# --------------------------------------------------------------------------- #
# Pure computation — portfolio metrics on a return series
# --------------------------------------------------------------------------- #
def series_risk_metrics(step_returns: np.ndarray, rng: np.random.Generator, *, n_boot: int,
                        ) -> dict[str, Any]:
    """Full risk-metric block for a per-step (hourly) MTM return series (D0-amendment-001 A2/A3).

    BINDING (scale-invariant, like-for-like across portfolio & single cells): annualized **Sharpe** and
    **Calmar** with moving-block one-sided **lower bounds** on the cadence-aggregated (weekly) series
    (block = programme default at the rebalance-cadence scale). CO-REPORTED drawdown/tail diagnostics on
    the MTM path: hourly MaxDD, weekly CVaR5, hourly Ulcer index, ann return/vol. NaN (never inf) on a
    zero denominator.
    """
    hourly = np.asarray(step_returns, dtype=np.float64)
    weekly = pf.aggregate_to_cadence(hourly, CADENCE_STEPS)
    sharpe = pf.annualized_sharpe(weekly, PERIODS_PER_YEAR_CADENCE)
    calmar_pt = pf.calmar(weekly, PERIODS_PER_YEAR_CADENCE)
    if weekly.shape[0] >= 2:
        block = default_block_length(weekly.shape[0])
        sharpe_lo = pf.moving_block_sharpe_lower_bound(
            weekly, rng, PERIODS_PER_YEAR_CADENCE, n_boot=n_boot, alpha=BOOT_ALPHA, block=block)
        calmar_lo = pf.moving_block_calmar_lower_bound(
            weekly, rng, PERIODS_PER_YEAR_CADENCE, n_boot=n_boot, alpha=BOOT_ALPHA, block=block)
    else:
        sharpe_lo = calmar_lo = float("nan")
    return {"ann_sharpe": sharpe, "ann_sharpe_lo": sharpe_lo,
            "calmar": calmar_pt, "calmar_lo": calmar_lo,
            "max_drawdown": pf.max_drawdown(hourly), "cvar5_weekly": pf.cvar(weekly, 0.05),
            "ulcer": pf.ulcer_index(hourly),
            "ann_return": float(hourly.mean() * PERIODS_PER_YEAR_HOURLY),
            "ann_vol": float(hourly.std(ddof=1) * np.sqrt(PERIODS_PER_YEAR_HOURLY))
            if hourly.shape[0] >= 2 else float("nan"),
            "n_weeks": int(weekly.shape[0])}


def vol_scaled(hourly: np.ndarray) -> np.ndarray:
    """Scale a per-step series to the TARGET_ANN_VOL anchor (for like-for-like single-cell tail/drawdown).

    Sharpe/Calmar are scale-invariant (unaffected); this only makes the co-reported MaxDD/CVaR/Ulcer of a
    standalone cell comparable to the vol-anchored portfolio. No effect on the binding lower bounds.
    """
    h = np.asarray(hourly, dtype=np.float64)
    if h.shape[0] < 2:
        return h
    ann_vol = float(h.std(ddof=1) * np.sqrt(PERIODS_PER_YEAR_HOURLY))
    return h * (TARGET_ANN_VOL / ann_vol) if ann_vol > pf.EPS else h


def pooled_expectancy_lower_bound(streams: list[pf.CellStream], rng: np.random.Generator) -> float:
    """Co-binding companion: pooled net per-trade expectancy moving-block one-sided lower bound (ATR)."""
    pooled = np.concatenate([s.net for s in streams]) if streams else np.empty(0)
    pooled = pooled[np.isfinite(pooled)]
    if pooled.shape[0] < 2:
        return float("nan")
    ci = moving_block_bootstrap_cis(pooled, rng, n_boot=N_BOOT, alpha=BOOT_ALPHA)
    return float(ci.expectancy_lo)


def turnover(weights: np.ndarray, rebalance_idx: np.ndarray) -> float:
    """Mean L1 weight change across rebalances (sum_i |w_{r,i} - w_{r-1,i}|), a cost-relevant diag."""
    if rebalance_idx.shape[0] < 2:
        return float("nan")
    w_reb = weights[rebalance_idx]
    return float(np.mean(np.abs(np.diff(w_reb, axis=0)).sum(axis=1)))


# --------------------------------------------------------------------------- #
# Pure computation — synthetic-null FPR calibration + bite-check (D6, binding for G-022a)
# --------------------------------------------------------------------------- #
def _null_portfolio_weekly(r_null: np.ndarray, grid_start: int, use_breaker: bool) -> np.ndarray:
    """Build a portfolio (A/B) on a null grid matrix and return its weekly-aggregated return series."""
    res = pf.build_portfolio(
        r_null, grid_start, STEP_SECONDS, rebalance_steps=REBALANCE_STEPS,
        lookback_steps=LOOKBACK_STEPS, target_ann_vol=TARGET_ANN_VOL, cap_mult=CAP_MULT,
        periods_per_year=PERIODS_PER_YEAR_HOURLY, use_breaker=use_breaker,
        breaker_window=BREAKER_WINDOW)
    return pf.aggregate_to_cadence(res.returns, CADENCE_STEPS)


def calibrate_statistic(r_mat: np.ndarray, grid_start: int, holdout_equiv_steps: int,
                        use_breaker: bool, label: str, realized_lo: float) -> dict[str, Any]:
    """Synthetic-null FPR + **MDE-curve** calibration of the Sharpe lower-bound rule (A or B; A4).

    Null = block-permute the common time index of the **per-trade** grid matrix to ``holdout_equiv_steps``
    rows and zero each column (``null_b_block_permute_returns`` form; preserves cross-cell covariance +
    autocorrelation; NOT a path rotation; NOT built around any signal-derived target — the calibration runs
    on realized per-trade returns because a synthetic permuted block has no price path to mark-to-market).

    For each replicate the full null portfolio is rebuilt and aggregated to weekly; one moving-block
    bootstrap caches its per-resample ``(mean_r, sd_r)``. The rule (Sharpe lower bound > 0) is then
    evaluated **analytically** for the null (shift 0 -> FPR) and for every planted annualized Sharpe ``s``
    on ``BITE_PLANT_GRID`` (shift ``s*sd_i/sqrt_ppy`` per replicate -> fire rate). The gate **MDE**
    ``m*`` = the smallest planted Sharpe whose fire rate >= the floor at the realized holdout n/block — the
    fixed-plant-vs-n mismatch (audit W1; recurring since EXP-094) is replaced by the detectable-effect the
    band must respect: READY iff FPR <= 0.05 AND m-star finite; G-022a must set the band >= m-star.
    """
    block = REBALANCE_STEPS                                       # block at the rebalance cadence
    n_weeks_cal = max(2, int(np.ceil(holdout_equiv_steps / CADENCE_STEPS)))
    weekly_block = default_block_length(n_weeks_cal)
    sqrt_ppy = np.sqrt(PERIODS_PER_YEAR_CADENCE)
    grid = np.asarray(BITE_PLANT_GRID, dtype=np.float64)
    null_fire = np.zeros(N_NULL, dtype=bool)
    fire_grid = np.zeros((N_NULL, grid.shape[0]), dtype=bool)
    for i in tqdm(range(N_NULL), desc=f"null FPR/MDE [{label}]", unit="rep", dynamic_ncols=True):
        perm_rng = np.random.default_rng(seed_for(EXPERIMENT_ID, label, "null", i))
        r_null = pf.block_permute_zero_mean(r_mat, perm_rng, block=block, n_out=holdout_equiv_steps)
        weekly = _null_portfolio_weekly(r_null, grid_start, use_breaker)
        boot_rng = np.random.default_rng(seed_for(EXPERIMENT_ID, label, "boot", i))
        mean_r, sd_r = pf.moving_block_boot_components(
            weekly, boot_rng, n_boot=CAL_N_BOOT, block=weekly_block)
        lo_null = pf.sharpe_lower_bound_shift(mean_r, sd_r, 0.0, PERIODS_PER_YEAR_CADENCE, BOOT_ALPHA)
        null_fire[i] = np.isfinite(lo_null) and lo_null > 0.0
        sd_i = float(weekly.std(ddof=1)) if weekly.shape[0] >= 2 else 0.0
        for gj, s in enumerate(grid):                            # analytic plant sweep (no re-bootstrap)
            shift = s * sd_i / sqrt_ppy if sd_i > pf.EPS else 0.0
            lo = pf.sharpe_lower_bound_shift(mean_r, sd_r, shift, PERIODS_PER_YEAR_CADENCE, BOOT_ALPHA)
            fire_grid[i, gj] = np.isfinite(lo) and lo > 0.0
    fpr = float(np.mean(null_fire))
    fire_rate = fire_grid.mean(axis=0)
    reached = np.where(fire_rate >= BITE_FIRE_FLOOR)[0]
    m_star = float(grid[reached[0]]) if reached.shape[0] else float("nan")
    fpr_hi = pf.wilson_upper(fpr, N_NULL)
    fpr_ok = fpr <= FPR_TARGET
    mde_resolved = bool(np.isfinite(m_star))
    return {"portfolio": label, "n_null": N_NULL, "fpr": fpr, "fpr_wilson_hi": fpr_hi,
            "fpr_controlled": bool(fpr_ok), "mde_sharpe": m_star, "mde_resolved": mde_resolved,
            "fire_floor": BITE_FIRE_FLOOR, "plant_grid": [float(x) for x in grid],
            "fire_rate_by_plant": [float(x) for x in fire_rate],
            "realized_portfolio_sharpe_lo": float(realized_lo),
            "realized_exceeds_mde": bool(np.isfinite(realized_lo) and mde_resolved and realized_lo >= m_star),
            "statistic_ready": bool(fpr_ok and mde_resolved),
            "band_rule": "G-022a must freeze the confirmation band >= mde_sharpe (a band below the gate MDE "
                         "is not detectable at the holdout n)",
            "holdout_equiv_steps": int(holdout_equiv_steps), "n_weeks_cal": n_weeks_cal,
            "cal_n_boot": CAL_N_BOOT}


# --------------------------------------------------------------------------- #
# Orchestration — build everything
# --------------------------------------------------------------------------- #
def build_streams() -> tuple[list[CellResolution], dict[str, Any]]:
    """Resolve all 8 cells over the analysis set; return resolutions + source metadata."""
    files, _ = E90.VAL005.discover_infr003_files()
    files = {k.upper(): v for k, v in files.items()}
    resolutions: list[CellResolution] = []
    src_meta: dict[str, Any] = {}
    for instrument, domain in tqdm(CELLS, desc="resolve cells", unit="cell", dynamic_ncols=True):
        if instrument not in files:
            raise FileNotFoundError(f"no INFR-003 file for {instrument}")
        analysis_1m, ts_lo, meta = load_analysis_1m(instrument, files[instrument])
        ctx, _dropped, status = E90.build_cell_context(analysis_1m, instrument, domain)
        if ctx is None:
            raise RuntimeError(f"{instrument}-{domain}: failed to build ({status})")
        resolutions.append(resolve_cell(ctx, ts_lo, instrument, domain))
        src_meta[f"{instrument}-{domain}"] = meta
    return resolutions, src_meta


def build_grid(streams: list[pf.CellStream]) -> tuple[int, int, np.ndarray, np.ndarray]:
    """Common 1h grid over [min ENTRY, max exit]; return (grid_start, n_steps, pnl_mat, trade_mat).

    ``pnl_mat`` = intra-1h MTM increments (amendment-001 A1; the binding Sharpe/MaxDD series) — so the grid
    must start at the earliest **entry** (a position accrues marks from entry, not exit). ``trade_mat`` =
    one realized net per resolved trade at its **exit** step (drives the active-cell warmup gate + the
    circuit-breaker's trailing-trade mean, and the pooled-expectancy companion).
    """
    entries = np.concatenate([s.entry_epoch for s in streams if s.entry_epoch.shape[0]])
    exits = np.concatenate([s.exit_epoch for s in streams if s.exit_epoch.shape[0]])
    grid_start = int(entries.min())
    grid_end = int(exits.max())
    n_steps = int((grid_end - grid_start) // STEP_SECONDS) + 1
    pnl_mat = pf.grid_mark_matrix(streams, grid_start, STEP_SECONDS, n_steps)
    trade_mat = pf.grid_return_matrix(streams, grid_start, STEP_SECONDS, n_steps)
    return grid_start, n_steps, pnl_mat, trade_mat


def _benefit(portfolio_lo: float, portfolio_pt: float, baseline_lo: float) -> dict[str, Any]:
    """Like-for-like benefit read: portfolio lower bound vs a baseline lower bound (D0-amendment-001 A2).

    Margin = portfolio_lo - baseline_lo. The portfolio "adds value" only if margin > 0 by more than the
    metric's own one-sided sampling band (point - lower bound); a miss inside that band is WITHIN_NOISE,
    not a clean negative.
    """
    band = portfolio_pt - portfolio_lo if np.isfinite(portfolio_pt) and np.isfinite(portfolio_lo) else float("nan")
    margin = portfolio_lo - baseline_lo if np.isfinite(portfolio_lo) and np.isfinite(baseline_lo) else float("nan")
    if not np.isfinite(margin) or not np.isfinite(band):
        label = "UNDEFINED"
    elif margin > 0.0:
        label = "ADDS_VALUE"
    elif abs(margin) <= band:
        label = "WITHIN_NOISE"
    else:
        label = "DOES_NOT_ADD_VALUE"
    return {"margin": margin, "sampling_band": band, "label": label}


def portfolio_block(pnl_mat: np.ndarray, trade_mat: np.ndarray, grid_start: int,
                    streams: list[pf.CellStream], boot_seed_key: str, *, n_boot: int) -> dict[str, Any]:
    """Build A, B, naive-IV, per-cell baselines + their MTM risk metrics; resolve the benefit read.

    Returns (P&L) and covariance use ``pnl_mat`` (MTM increments); the warmup gate + breaker use
    ``trade_mat`` (per-resolved-trade). Per-cell baselines are each cell's own MTM column vol-scaled to the
    anchor (so tail/drawdown are comparable); the deployment-realistic baseline is the **cross-cell median**
    of the per-cell Sharpe / Calmar lower bounds (you cannot pick the ex-post-best cell ex ante).
    """
    common = dict(rebalance_steps=REBALANCE_STEPS, lookback_steps=LOOKBACK_STEPS,
                  target_ann_vol=TARGET_ANN_VOL, periods_per_year=PERIODS_PER_YEAR_HOURLY)
    res_a = pf.build_portfolio(pnl_mat, grid_start, STEP_SECONDS, cap_mult=CAP_MULT, use_breaker=False,
                               breaker_window=BREAKER_WINDOW, trade_mat=trade_mat, **common)
    res_b = pf.build_portfolio(pnl_mat, grid_start, STEP_SECONDS, cap_mult=CAP_MULT, use_breaker=True,
                               breaker_window=BREAKER_WINDOW, trade_mat=trade_mat, **common)
    naive = pf.naive_inverse_vol(pnl_mat, grid_start, STEP_SECONDS, trade_mat=trade_mat, **common)
    m_a = series_risk_metrics(res_a.returns, np.random.default_rng(seed_for(EXPERIMENT_ID, boot_seed_key, "A")),
                              n_boot=n_boot)
    m_b = series_risk_metrics(res_b.returns, np.random.default_rng(seed_for(EXPERIMENT_ID, boot_seed_key, "B")),
                              n_boot=n_boot)
    m_n = series_risk_metrics(naive, np.random.default_rng(seed_for(EXPERIMENT_ID, boot_seed_key, "naive")),
                              n_boot=n_boot)
    # Per-cell single baselines: each cell's own MTM column, vol-scaled to the anchor (like-for-like).
    per_cell: dict[str, dict[str, Any]] = {}
    for ci in range(pnl_mat.shape[1]):
        col = vol_scaled(pnl_mat[:, ci])
        per_cell[streams[ci].name] = series_risk_metrics(
            col, np.random.default_rng(seed_for(EXPERIMENT_ID, boot_seed_key, "cell", streams[ci].name)),
            n_boot=n_boot)
    cell_sharpe_pt = {k: v["ann_sharpe"] for k, v in per_cell.items()}
    cell_sharpe_lo = [v["ann_sharpe_lo"] for v in per_cell.values() if np.isfinite(v["ann_sharpe_lo"])]
    cell_calmar_lo = [v["calmar_lo"] for v in per_cell.values() if np.isfinite(v["calmar_lo"])]
    median_cell_sharpe_lo = float(np.median(cell_sharpe_lo)) if cell_sharpe_lo else float("nan")
    median_cell_calmar_lo = float(np.median(cell_calmar_lo)) if cell_calmar_lo else float("nan")
    best_pt, best_name = max(((v, k) for k, v in cell_sharpe_pt.items() if np.isfinite(v)),
                             default=(float("nan"), ""))
    best_lo = per_cell.get(best_name, {}).get("ann_sharpe_lo", float("nan"))
    pooled_exp_lo = pooled_expectancy_lower_bound(
        streams, np.random.default_rng(seed_for(EXPERIMENT_ID, boot_seed_key, "pooled")))
    # Binding benefit (A2): portfolio Sharpe LB vs median-cell Sharpe LB; co-binding Calmar LB (A3).
    benefit = {
        "baseline": "cross-cell median single-cell lower bound (deployment-realistic)",
        "median_cell_sharpe_lo": median_cell_sharpe_lo, "median_cell_calmar_lo": median_cell_calmar_lo,
        "A_sharpe": _benefit(m_a["ann_sharpe_lo"], m_a["ann_sharpe"], median_cell_sharpe_lo),
        "B_sharpe": _benefit(m_b["ann_sharpe_lo"], m_b["ann_sharpe"], median_cell_sharpe_lo),
        "A_calmar": _benefit(m_a["calmar_lo"], m_a["calmar"], median_cell_calmar_lo),
        "B_calmar": _benefit(m_b["calmar_lo"], m_b["calmar"], median_cell_calmar_lo),
        "disclosed_best_cell_sharpe_pt": best_pt, "disclosed_best_cell_sharpe_lo": best_lo,
        "disclosed_best_cell_name": best_name,
        "disclosed_A_vs_best_cell_lo": _benefit(m_a["ann_sharpe_lo"], m_a["ann_sharpe"], best_lo),
        "disclosed_naive_sharpe_lo": m_n["ann_sharpe_lo"]}
    return {"A": {**m_a, "turnover": turnover(res_a.weights, res_a.rebalance_idx),
                  "n_indeterminate": res_a.n_indeterminate},
            "B": {**m_b, "turnover": turnover(res_b.weights, res_b.rebalance_idx),
                  "n_indeterminate": res_b.n_indeterminate},
            "naive_iv": m_n, "per_cell": per_cell, "per_cell_sharpe": cell_sharpe_pt,
            "best_cell_sharpe": best_pt, "best_cell_name": best_name, "benefit": benefit,
            "pooled_expectancy_lo": pooled_exp_lo,
            "_res_a": res_a, "_res_b": res_b, "_naive": naive}


def vol_anchor_invariance(pnl_mat: np.ndarray, trade_mat: np.ndarray, grid_start: int) -> dict[str, Any]:
    """Assert annualized Sharpe is invariant to the global vol-anchor scalar (7%/10%/15%) — A only."""
    sharpes = {}
    for tv in (VOL_TARGET_BRACKET[0], TARGET_ANN_VOL, VOL_TARGET_BRACKET[1]):
        res = pf.build_portfolio(
            pnl_mat, grid_start, STEP_SECONDS, rebalance_steps=REBALANCE_STEPS,
            lookback_steps=LOOKBACK_STEPS, target_ann_vol=tv, cap_mult=CAP_MULT,
            periods_per_year=PERIODS_PER_YEAR_HOURLY, use_breaker=False, breaker_window=BREAKER_WINDOW,
            trade_mat=trade_mat)
        weekly = pf.aggregate_to_cadence(res.returns, CADENCE_STEPS)
        sharpes[f"vol_{tv}"] = pf.annualized_sharpe(weekly, PERIODS_PER_YEAR_CADENCE)
    vals = [v for v in sharpes.values() if np.isfinite(v)]
    spread = float(max(vals) - min(vals)) if len(vals) >= 2 else float("nan")
    # Concurrent-risk cap can bind differently at different anchors -> Sharpe invariance holds up to the
    # cap activation; report the spread as a diagnostic (tolerance generous; cap is the only coupler).
    return {"sharpe_by_vol_target": sharpes, "max_abs_spread": spread,
            "invariant_within_tol": bool(np.isfinite(spread) and spread <= 0.05)}


def cov_window_sensitivity(pnl_mat: np.ndarray, trade_mat: np.ndarray, grid_start: int) -> dict[str, float]:
    """Disclosed sensitivity (NEVER selection): Portfolio-A Sharpe at covariance windows {60,120} days."""
    out: dict[str, float] = {}
    for days in COV_WINDOW_BRACKET_DAYS:
        res = pf.build_portfolio(
            pnl_mat, grid_start, STEP_SECONDS, rebalance_steps=REBALANCE_STEPS,
            lookback_steps=days * 24, target_ann_vol=TARGET_ANN_VOL, cap_mult=CAP_MULT,
            periods_per_year=PERIODS_PER_YEAR_HOURLY, use_breaker=False, breaker_window=BREAKER_WINDOW,
            trade_mat=trade_mat)
        weekly = pf.aggregate_to_cadence(res.returns, CADENCE_STEPS)
        out[f"cov_{days}d"] = pf.annualized_sharpe(weekly, PERIODS_PER_YEAR_CADENCE)
    return out


# --------------------------------------------------------------------------- #
# Plotting (5 bounded plots from collected series; no reloads)
# --------------------------------------------------------------------------- #
def make_plots(r_mat: np.ndarray, grid_start: int, n_steps: int, block: dict[str, Any],
               streams: list[pf.CellStream]) -> None:
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)                  # defensive: ensure the dir exists
    grid_epochs = grid_start + np.arange(n_steps) * STEP_SECONDS
    _plot_equity_curves(grid_epochs, block, r_mat, streams)
    _plot_weight_corr_heatmap(block, streams, r_mat)
    _plot_drawdown_ab(grid_epochs, block)
    _plot_breaker_timeline(grid_epochs, block, streams)
    _plot_null_bite(block)


def _equity(returns: np.ndarray) -> np.ndarray:
    return np.cumsum(np.asarray(returns, dtype=np.float64))


def _plot_equity_curves(grid_epochs: np.ndarray, block: dict[str, Any], r_mat: np.ndarray,
                        streams: list[pf.CellStream]) -> None:
    t = grid_epochs.astype("datetime64[s]")
    best_name = block["best_cell_name"]
    best_col = next((ci for ci, s in enumerate(streams) if s.name == best_name), 0)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(t, _equity(block["_res_a"].returns), label="Portfolio A (static ERC)", color="steelblue")
    ax.plot(t, _equity(block["_res_b"].returns), label="Portfolio B (ERC + breaker)", color="seagreen")
    ax.plot(t, _equity(block["_naive"]), label="naive inverse-vol", color="gray", lw=0.9, ls="--")
    ax.plot(t, _equity(r_mat[:, best_col]), label=f"best cell ({best_name})", color="indianred",
            lw=0.9, ls=":")
    ax.axhline(0, color="black", lw=0.6)
    ax.set_title("EXP-095 analysis-set equity curves (cumulative net, vol-anchored)", fontsize=10)
    ax.set_ylabel("cumulative net return")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "equity_curves.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_weight_corr_heatmap(block: dict[str, Any], streams: list[pf.CellStream],
                              r_mat: np.ndarray) -> None:
    res_a = block["_res_a"]
    w_reb = res_a.weights[res_a.rebalance_idx]                    # (R, k)
    names = [s.name for s in streams]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    im1 = ax1.imshow(w_reb.T, aspect="auto", cmap="viridis")
    ax1.set_yticks(range(len(names)), names, fontsize=7)
    ax1.set_xlabel("rebalance #")
    ax1.set_title("Portfolio A ERC weight path", fontsize=9)
    fig.colorbar(im1, ax=ax1, fraction=0.05)
    active = r_mat[(r_mat != 0).any(axis=1)]
    corr = np.corrcoef(active, rowvar=False) if active.shape[0] > 2 else np.eye(len(names))
    im2 = ax2.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    ax2.set_xticks(range(len(names)), names, rotation=90, fontsize=7)
    ax2.set_yticks(range(len(names)), names, fontsize=7)
    ax2.set_title("per-cell return correlation (active steps)", fontsize=9)
    fig.colorbar(im2, ax=ax2, fraction=0.05)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "weights_correlation_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _drawdown(returns: np.ndarray) -> np.ndarray:
    eq = _equity(returns)
    return np.maximum.accumulate(eq) - eq


def _plot_drawdown_ab(grid_epochs: np.ndarray, block: dict[str, Any]) -> None:
    t = grid_epochs.astype("datetime64[s]")
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.fill_between(t, -_drawdown(block["_res_a"].returns), 0, color="steelblue", alpha=0.5,
                    label="A drawdown")
    ax.fill_between(t, -_drawdown(block["_res_b"].returns), 0, color="seagreen", alpha=0.5,
                    label="B drawdown")
    ax.set_title("EXP-095 A vs B drawdown (underwater); does the breaker reduce drawdown?", fontsize=9)
    ax.set_ylabel("drawdown (negative)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "drawdown_A_vs_B.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_breaker_timeline(grid_epochs: np.ndarray, block: dict[str, Any],
                           streams: list[pf.CellStream]) -> None:
    t = grid_epochs.astype("datetime64[s]")
    res_b = block["_res_b"]
    fragile = [ci for ci, s in enumerate(streams) if s.name in ("USTEC-1h", "US2000-1h")]
    fig, ax = plt.subplots(figsize=(9, 4))
    for ci in fragile:
        allocated = (res_b.weights[:, ci] > 0).astype(float)
        ax.plot(t, allocated + 0.02 * fragile.index(ci), label=f"{streams[ci].name} allocated",
                drawstyle="steps-post")
    ax.set_ylim(-0.1, 1.2)
    ax.set_yticks([0, 1], ["broken (0)", "allocated (1)"])
    ax.set_title("EXP-095 Portfolio B circuit-breaker timeline (fragile 1h cells)", fontsize=9)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "circuit_breaker_timeline.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_null_bite(block: dict[str, Any]) -> None:
    """MDE-curve calibration plot (A4): planted-Sharpe vs detection fire rate, with FPR + m* per portfolio."""
    cal = block["calibration"]
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    colors = {"A": "steelblue", "B": "seagreen"}
    for label, c in cal.items():
        grid = np.asarray(c["plant_grid"], dtype=float)
        rate = np.asarray(c["fire_rate_by_plant"], dtype=float)
        ax.plot(grid, rate, marker="o", ms=3, color=colors.get(label, "gray"),
                label=f"{label}: fire rate (FPR={c['fpr']:.3f}, m*={c['mde_sharpe']:.2f})")
        if np.isfinite(c["mde_sharpe"]):
            ax.axvline(c["mde_sharpe"], color=colors.get(label, "gray"), ls=":", lw=0.8)
    ax.axhline(BITE_FIRE_FLOOR, color="black", ls="--", lw=0.8, label=f"power floor {BITE_FIRE_FLOOR}")
    ax.set_xlabel("planted annualized Sharpe")
    ax.set_ylabel("detection fire rate at holdout n")
    ax.set_ylim(0, 1.05)
    ax.set_title("EXP-095 gate MDE curve (A4): m* = smallest plant with fire >= floor; band must be >= m*",
                 fontsize=8.5)
    ax.legend(fontsize=7.5)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "null_fpr_bite_check.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Output writers
# --------------------------------------------------------------------------- #
def write_outputs(block: dict[str, Any], provenance: list[dict[str, Any]], grid_start: int,
                  n_steps: int, streams: list[pf.CellStream], invariance: dict[str, Any],
                  cov_sens: dict[str, float]) -> None:
    """Write every headline artifact named in the analysis plan."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)               # defensive: ensure the dir exists
    pl.DataFrame(provenance).write_csv(RESULTS_DIR / "provenance_reconciliation.csv")

    grid_epochs = grid_start + np.arange(n_steps) * STEP_SECONDS
    ts = grid_epochs.astype("datetime64[s]").astype(str)
    pl.DataFrame({"timestamp": ts, "net_return": block["_res_a"].returns}).write_csv(
        RESULTS_DIR / "portfolio_returns_A.csv")
    pl.DataFrame({"timestamp": ts, "net_return": block["_res_b"].returns}).write_csv(
        RESULTS_DIR / "portfolio_returns_B.csv")

    res_a = block["_res_a"]
    reb_ts = (grid_start + res_a.rebalance_idx * STEP_SECONDS).astype("datetime64[s]").astype(str)
    w_reb = res_a.weights[res_a.rebalance_idx]
    wt = {"rebalance_ts": reb_ts}
    for ci, s in enumerate(streams):
        wt[s.name] = w_reb[:, ci]
    pl.DataFrame(wt).write_csv(RESULTS_DIR / "weights_timeline.csv")

    res_b = block["_res_b"]
    cb = {"timestamp": ts}
    for ci, s in enumerate(streams):
        if s.name in ("USTEC-1h", "US2000-1h"):
            cb[f"{s.name}_allocated"] = (res_b.weights[:, ci] > 0).astype(int)
    pl.DataFrame(cb).write_csv(RESULTS_DIR / "circuit_breaker_timeline.csv")

    metric_rows = []
    for key in ("A", "B", "naive_iv"):
        m = block[key]
        metric_rows.append({"portfolio": key, **{k: v for k, v in m.items()}})
    for name, pc in block["per_cell"].items():
        metric_rows.append({"portfolio": f"cell:{name}", **{k: v for k, v in pc.items()}})
    pl.DataFrame(metric_rows, strict=False).write_csv(RESULTS_DIR / "portfolio_metrics.csv")
    (RESULTS_DIR / "benefit.json").write_text(json.dumps(block["benefit"], indent=2, default=str))

    (RESULTS_DIR / "risk_anchor_invariance.json").write_text(
        json.dumps({"vol_anchor_invariance": invariance, "cov_window_sensitivity_disclosed": cov_sens,
                    "note": "brackets are disclosed sensitivity ONLY — never used to select a value"},
                   indent=2))
    (RESULTS_DIR / "null_fpr_calibration.json").write_text(
        json.dumps({k: {kk: vv for kk, vv in v.items()} for k, v in block["calibration"].items()},
                   indent=2, default=str))
    (RESULTS_DIR / "bite_check.json").write_text(
        json.dumps({k: {"mde_sharpe": v["mde_sharpe"], "mde_resolved": v["mde_resolved"],
                        "fire_floor": v["fire_floor"], "fpr": v["fpr"],
                        "realized_portfolio_sharpe_lo": v["realized_portfolio_sharpe_lo"],
                        "realized_exceeds_mde": v["realized_exceeds_mde"],
                        "statistic_ready": v["statistic_ready"]}
                    for k, v in block["calibration"].items()}, indent=2, default=str))


def hash_outputs() -> dict[str, str]:
    """SHA-256 of each headline output (byte-identical second-pass pin)."""
    names = ("provenance_reconciliation.csv", "portfolio_returns_A.csv", "portfolio_returns_B.csv",
             "portfolio_metrics.csv", "benefit.json", "null_fpr_calibration.json", "bite_check.json")
    out: dict[str, str] = {}
    for name in names:
        p = RESULTS_DIR / name
        if p.exists():
            out[name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


# --------------------------------------------------------------------------- #
# Determinism + causality unit assertions
# --------------------------------------------------------------------------- #
def determinism_replay(streams: list[pf.CellStream], grid_start: int, n_steps: int,
                       pnl_mat: np.ndarray, trade_mat: np.ndarray,
                       block: dict[str, Any]) -> dict[str, Any]:
    """Rebuild A and B from the same matrices; assert the return series are byte-identical (D8)."""
    common = dict(rebalance_steps=REBALANCE_STEPS, lookback_steps=LOOKBACK_STEPS,
                  target_ann_vol=TARGET_ANN_VOL, cap_mult=CAP_MULT,
                  periods_per_year=PERIODS_PER_YEAR_HOURLY, breaker_window=BREAKER_WINDOW,
                  trade_mat=trade_mat)
    res_a2 = pf.build_portfolio(pnl_mat, grid_start, STEP_SECONDS, use_breaker=False, **common)
    res_b2 = pf.build_portfolio(pnl_mat, grid_start, STEP_SECONDS, use_breaker=True, **common)
    a_ok = bool(np.array_equal(res_a2.returns, block["_res_a"].returns))
    b_ok = bool(np.array_equal(res_b2.returns, block["_res_b"].returns))
    return {"determinism_pass": a_ok and b_ok, "A_identical": a_ok, "B_identical": b_ok}


def causal_weight_assertion(pnl_mat: np.ndarray, trade_mat: np.ndarray, grid_start: int) -> dict[str, Any]:
    """Perturb both grid matrices strictly AFTER a rebalance row; assert that rebalance's weights unchanged.

    A future return entering a past weight (cov, vol, cap, or breaker) would be look-ahead; this fails loudly.
    """
    reb_idx = np.arange(0, pnl_mat.shape[0], REBALANCE_STEPS, dtype=np.int64)
    r = int(reb_idx[len(reb_idx) // 2]) if reb_idx.shape[0] >= 2 else 0
    kw = dict(lookback_steps=LOOKBACK_STEPS, target_ann_vol=TARGET_ANN_VOL, cap_mult=CAP_MULT,
              periods_per_year=PERIODS_PER_YEAR_HOURLY, use_breaker=True, breaker_window=BREAKER_WINDOW)
    w0, _ = pf._rebalance_weight(pnl_mat, r, trade_mat=trade_mat, **kw)
    pnl_p, trade_p = pnl_mat.copy(), trade_mat.copy()
    if r < pnl_p.shape[0]:
        pnl_p[r:] += 7.5                                         # arbitrary large perturbation at/after r
        trade_p[r:] += 7.5
    w1, _ = pf._rebalance_weight(pnl_p, r, trade_mat=trade_p, **kw)
    unchanged = bool(np.array_equal(w0, w1))
    if not unchanged:
        raise RuntimeError("CAUSALITY VIOLATION: future grid rows changed a past rebalance weight")
    return {"causal_weight_pass": unchanged, "rebalance_row_tested": r}


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def run(skip_calibration: bool = False) -> dict[str, Any]:
    """Full EXP-095 analysis-set portfolio build + statistic calibration (no holdout verdict)."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    resolutions, src_meta = build_streams()
    provenance = reconcile_provenance(resolutions)
    LOGGER.info("provenance gate PASS for %d cells", len(provenance))
    streams = [r.stream for r in resolutions]
    grid_start, n_steps, pnl_mat, trade_mat = build_grid(streams)
    LOGGER.info("grid: %d hourly steps (%.2f years); MTM marks=%d trade events=%d", n_steps,
                n_steps * STEP_SECONDS / SECONDS_PER_YEAR,
                int(np.count_nonzero(pnl_mat)), int(np.count_nonzero(trade_mat)))

    block = portfolio_block(pnl_mat, trade_mat, grid_start, streams, "real", n_boot=N_BOOT)
    invariance = vol_anchor_invariance(pnl_mat, trade_mat, grid_start)
    cov_sens = cov_window_sensitivity(pnl_mat, trade_mat, grid_start)
    causal = causal_weight_assertion(pnl_mat, trade_mat, grid_start)

    holdout_equiv_steps = int(round(n_steps * 0.30 / 0.70))
    if skip_calibration:
        block["calibration"] = {}
    else:
        block["calibration"] = {
            "A": calibrate_statistic(trade_mat, grid_start, holdout_equiv_steps, False, "A",
                                     block["A"]["ann_sharpe_lo"]),
            "B": calibrate_statistic(trade_mat, grid_start, holdout_equiv_steps, True, "B",
                                     block["B"]["ann_sharpe_lo"])}

    determinism = determinism_replay(streams, grid_start, n_steps, pnl_mat, trade_mat, block)
    make_plots(pnl_mat, grid_start, n_steps, block, streams)
    write_outputs(block, provenance, grid_start, n_steps, streams, invariance, cov_sens)

    meta = _build_metadata(block, src_meta, grid_start, n_steps, determinism, causal, invariance,
                           holdout_equiv_steps)
    meta["output_hashes"] = hash_outputs()
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(meta, indent=2, default=str))
    _log_summary(block, determinism, causal, time.perf_counter() - t0)
    return meta


def _build_metadata(block: dict[str, Any], src_meta: dict[str, Any], grid_start: int, n_steps: int,
                    determinism: dict[str, Any], causal: dict[str, Any], invariance: dict[str, Any],
                    holdout_equiv_steps: int) -> dict[str, Any]:
    cal = block.get("calibration", {})
    statistic_ready = bool(cal and all(cal[k]["statistic_ready"] for k in cal))
    return {
        "experiment_id": EXPERIMENT_ID, "phase": "022", "family": "CF-MR-001", "hyp": "HYP-003",
        "amendment": "D0-amendment-001 (A1 intra-1h MTM; A2 like-for-like + median-cell baseline; "
                     "A3 co-binding Calmar/CVaR/Ulcer; A4 MDE-curve bite-check)",
        "generated_utc": datetime.now(timezone.utc).isoformat(), "master_seed": MASTER_SEED,
        "deployable_cells": [f"{i}-{d}" for i, d in CELLS], "surviving_exit": ARM,
        "construction": {
            "sizing": "ERC (equal risk contribution), Ledoit-Wolf shrinkage to diagonal",
            "covariance_lookback_days": 90, "rebalance": "weekly", "target_ann_vol": TARGET_ANN_VOL,
            "concurrent_risk_cap_mult": CAP_MULT, "breaker_window_trades": BREAKER_WINDOW,
            "grid": "1h common wall-clock; intra-1h MTM of open positions (D0 §D2.1 / amendment-001 A1); "
                    "trade counts/breaker on the per-resolved-trade stream",
            "sharpe_series": "weekly-aggregated (block = rebalance cadence)",
            "periods_per_year_cadence": PERIODS_PER_YEAR_CADENCE},
        "cost_model": "EXP-085/093 CONSERVATIVE RT (D0-amendment-003); F=0", "cost_rt_bps": MR_COST_RT_BPS,
        "metrics": {"A": block["A"], "B": block["B"], "naive_iv": block["naive_iv"],
                    "best_cell_sharpe": block["best_cell_sharpe"],
                    "best_cell_name": block["best_cell_name"],
                    "per_cell": block["per_cell"], "per_cell_sharpe": block["per_cell_sharpe"],
                    "pooled_expectancy_lo": block["pooled_expectancy_lo"]},
        "benefit": block["benefit"],
        "calibration": cal, "statistic_ready_for_g022a": statistic_ready,
        "vol_anchor_invariance": invariance,
        "determinism": determinism, "causal_weight_assertion": causal,
        "grid_start_epoch": grid_start, "n_grid_steps": n_steps,
        "holdout_equiv_steps": holdout_equiv_steps,
        "n_boot": N_BOOT, "cal_n_boot": CAL_N_BOOT, "n_null": N_NULL, "boot_alpha": BOOT_ALPHA,
        "real_prices_only": True, "holdout_untouched": True, "counted_test_reads": 0,
        "candidate_slots": 0,
        "read_accounting": ("portfolio-aggregate disclosure: re-combines the EXP-093 already-resolved "
                            "analysis-TEST series (TEST subset reconciled byte-for-byte); 11 carried "
                            "strata stay 1/2; 37 strata stay 0/2; final-30% global holdout never loaded"),
        "source_meta": src_meta,
    }


def _log_summary(block: dict[str, Any], determinism: dict[str, Any], causal: dict[str, Any],
                 secs: float) -> None:
    a, b = block["A"], block["B"]
    LOGGER.info("EXP-095 done in %.1fs | A Sharpe=%.3f (lo %.3f) | B Sharpe=%.3f (lo %.3f) | "
                "best cell %s=%.3f", secs, a["ann_sharpe"], a["ann_sharpe_lo"], b["ann_sharpe"],
                b["ann_sharpe_lo"], block["best_cell_name"], block["best_cell_sharpe"])
    for k, c in block.get("calibration", {}).items():
        LOGGER.info("  calib[%s]: FPR=%.4f (Wilson-hi %.4f) MDE m*=%.2f ready=%s (realized lo %.3f)", k,
                    c["fpr"], c["fpr_wilson_hi"], c["mde_sharpe"], c["statistic_ready"],
                    c["realized_portfolio_sharpe_lo"])
    LOGGER.info("  determinism=%s causal=%s holdout_untouched=True counted_reads=0",
                determinism["determinism_pass"], causal["causal_weight_pass"])


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description="EXP-095 portfolio construction + statistic calibration")
    ap.add_argument("--skip-calibration", action="store_true",
                    help="smoke run: skip the synthetic-null FPR/bite-check (faster)")
    args = ap.parse_args()
    meta = run(skip_calibration=args.skip_calibration)
    a, b = meta["metrics"]["A"], meta["metrics"]["B"]
    print(f"EXP-095 complete | A Sharpe={a['ann_sharpe']:.3f} (lo {a['ann_sharpe_lo']:.3f}) | "
          f"B Sharpe={b['ann_sharpe']:.3f} (lo {b['ann_sharpe_lo']:.3f}) | "
          f"best cell={meta['metrics']['best_cell_name']} {meta['metrics']['best_cell_sharpe']:.3f} | "
          f"statistic_ready={meta['statistic_ready_for_g022a']} | "
          f"determinism={meta['determinism']['determinism_pass']} "
          f"holdout_untouched={meta['holdout_untouched']} counted_reads={meta['counted_test_reads']}")


if __name__ == "__main__":
    main()
