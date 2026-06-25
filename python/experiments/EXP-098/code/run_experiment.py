"""EXP-098 — Cross-Broker & Aggregation-Method Robustness Replication (RSI-2 Fade Deployment Portfolio).

Phase 022 / ``CF-MR-001`` / HYP-003 — a **non-binding robustness / replication disclosure** (opened by
``docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/D0-amendment-002.md``).
Scope/plan: ``scope.md`` / ``analysis-plan.md``.

What this is. Rerun the **G-022a-frozen** deployment portfolio (the EXP-097/096/095/090 construction, byte-for-byte)
**verbatim** on an **independent broker's** 1-minute data (``data/timebars/pps/``, the same 8 carry-8 instruments
and span), under **two bar-aggregation timestamping methods**, to test two overfitting hypotheses EXP-097 could
not separate:
  * **Arm 1 ``PPS-CANON``** — the deployed ``xen.domain_bars.build_domain_bars`` (bucket-right-boundary label).
    Pure cross-broker replication.
  * **Arm 2 ``PPS-ALTAGG``** — identical bucketing/coverage(0.90)/OHLC reduction, but each domain bar is
    timestamped at the **actual last source 1-minute CloseTime** (not the bucket boundary), then the same
    analysis-boundary fence. Isolates aggregation-method overfit.

The ONLY two things that change vs EXP-097 are (a) the data source and (b) the Arm-2 aggregation label. Everything
downstream of domain-bar construction (RSI-2 entry, EXIT-RCT, adverse, v2 entry fill, cost, ERC, intra-1h MTM,
circuit breaker, the m*-calibrated statistic) is reused verbatim from the validated EXP-096 module.

Non-binding. EXP-098 **cannot upgrade or revoke** EXP-097's ``DEPLOYABLE_CONFIRMED`` verdict. PPS is an independent
dataset, outside the INFR-003 analysis-TEST ledger AND the INFR-003 global holdout (the holdout is NEVER loaded
here). Read accounting: ``counted_test_reads=0``, ``candidate_slots=0``, ``exp097_verdict_unchanged=true``;
recorded as a robustness governance disclosure.

Eval slice. The **full PPS timeline** (operator decision): per-cell streams resolve over the entire PPS file; the
binding portfolio metric is computed over the **full evaluable grid after the unavoidable estimator burn-in** (the
trailing-90-day LW covariance lookback ``LOOKBACK_STEPS``) — NOT a held-back slice and NOT a holdout. ``H_eval`` is
the warmup boundary only.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import logging
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

for _thread_var in ("POLARS_MAX_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                    "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_thread_var, "1")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import polars as pl  # noqa: E402
from tqdm.auto import tqdm  # noqa: E402

from xen.ass import moving_block_bootstrap_cis  # noqa: E402
from xen.intrabar_fill import resolve_entry_fills  # noqa: E402
from xen.referee_calibration import seed_for  # noqa: E402

# --------------------------------------------------------------------------- #
# Path setup + reuse the validated EXP-096 module (transitively EXP-095 + EXP-090 + xen.portfolio)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-098"
CODE_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = CODE_DIR.parent
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
EXP_ROOT = EXPERIMENT_DIR.parent
PROJECT_ROOT = EXP_ROOT.parent.parent
EXP096_CODE = EXP_ROOT / "EXP-096" / "code" / "run_experiment.py"
EXP097_HOLDOUT_METRICS = EXP_ROOT / "EXP-097" / "results" / "holdout_metrics.csv"
EXP097_PER_CELL = EXP_ROOT / "EXP-097" / "results" / "per_cell_holdout.csv"
PPS_DIR = PROJECT_ROOT / "data" / "timebars" / "pps"


def _load_exp096() -> Any:
    """Import the validated EXP-096 module (import-safe; registers in sys.modules so dataclasses resolve)."""
    if not EXP096_CODE.exists():
        raise FileNotFoundError(f"EXP-096 module missing: {EXP096_CODE}")
    spec = importlib.util.spec_from_file_location("exp096_mr_noise", EXP096_CODE)
    if spec is None or spec.loader is None:                       # pragma: no cover - defensive
        raise ImportError(f"Could not load EXP-096 from {EXP096_CODE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module                              # register BEFORE exec (dataclass resolution)
    spec.loader.exec_module(module)
    return module


E96 = _load_exp096()
E95 = E96.E95                                                    # portfolio construction + frozen statistic
E90 = E96.E90                                                   # substrate (build_cell_context, resolve_arm)
PF = E96.pf                                                     # xen.portfolio

# --------------------------------------------------------------------------- #
# Constants (ALL inherited / frozen at G-022a; nothing tuned here)
# --------------------------------------------------------------------------- #
MASTER_SEED = E96.MASTER_SEED                                    # 20260624
ARM = E96.ARM                                                   # EXIT-RCT
CELLS = E96.CELLS                                              # the 8 G-021-confirmed cells (carry-8)
STEP_SECONDS = E96.STEP_SECONDS
N_BOOT = E96.N_BOOT                                             # 10_000
BOOT_ALPHA = E96.BOOT_ALPHA                                     # 0.10 -> one-sided 95% lower bound
REBALANCE_STEPS = E96.REBALANCE_STEPS
LOOKBACK_STEPS = E96.LOOKBACK_STEPS                            # 90*24 trailing-90-day covariance window
TARGET_ANN_VOL = E96.TARGET_ANN_VOL
CAP_MULT = E96.CAP_MULT
BREAKER_WINDOW = E96.BREAKER_WINDOW
PERIODS_PER_YEAR_HOURLY = E95.PERIODS_PER_YEAR_HOURLY
BINDING_VARIANT = E96.BINDING_VARIANT                            # "v2"
SLIPPAGE_ATR = E96.SLIPPAGE_ATR                                 # 0.05
K_WORST = E96.K_WORST                                          # 3
FRAGILE_CELLS = E96.FRAGILE_CELLS                              # ("USTEC-1h", "US2000-1h")
DOMAINS = E90.DOMAINS                                          # {"1h": 60, "4h": 240, ...}

# Frozen confirmation bands (= the inherited A4 MDE m*; G-022a §3.4). NOT tuned.
BAND: dict[str, float] = {"A": 1.75, "B": 2.00}
# Deployed domain coverage (xen.domain_bars.MIN_COVERAGE) — re-used by the Arm-2 alternate aggregation.
MIN_COVERAGE = 0.90
SECONDS_PER_MINUTE = 60

# Estimator burn-in: exclude only the leading region where the trailing covariance window is not yet full.
# This is the unavoidable warmup the ERC estimator requires — NOT a holdout (PPS was never used for selection).
BURN_IN_STEPS = LOOKBACK_STEPS

ARMS: tuple[str, ...] = ("PPS-CANON", "PPS-ALTAGG")
# The 8 carry-8 instruments (upper-case) -> required PPS coverage.
PPS_INSTRUMENTS: tuple[str, ...] = tuple(sorted({i.upper() for i, _ in CELLS}))

LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# I/O helper — independent-broker (PPS) file discovery (the INFR-003 holdout is NEVER loaded)
# --------------------------------------------------------------------------- #
def discover_pps_files() -> dict[str, Path]:
    """Map each carry-8 instrument (UPPER) -> its PPS 1-minute Parquet file under ``data/timebars/pps/``.

    Independent-data discipline: only ``data/timebars/pps/`` is read. The INFR-003 dataset and its sealed
    global holdout are never opened by this experiment.
    """
    if not PPS_DIR.is_dir():
        raise FileNotFoundError(f"PPS data directory missing: {PPS_DIR}")
    files: dict[str, Path] = {}
    for instrument in PPS_INSTRUMENTS:
        matches = sorted(PPS_DIR.glob(f"timebars_{instrument.lower()}_*.parquet"))
        if not matches:
            raise FileNotFoundError(f"no PPS file for {instrument} in {PPS_DIR}")
        files[instrument] = matches[-1]                          # newest per instrument (latest-glob convention)
    return files


def load_full_pps_1m(instrument: str, path: Path) -> tuple[pl.DataFrame, int, dict[str, Any]]:
    """Load the **full** PPS file for one instrument (the entire timeline; no holdout split exists here)."""
    if path.parent.resolve() != PPS_DIR.resolve():               # independent-data guard
        raise RuntimeError(f"{instrument}: refusing to load non-PPS file {path}")
    frame = pl.scan_parquet(path).sort("CloseTime").collect()
    if frame.height == 0:
        raise RuntimeError(f"{instrument}: empty PPS file {path.name}")
    if not frame.get_column("CloseTime").is_sorted():
        raise RuntimeError(f"{instrument}: PPS file not sorted by CloseTime")
    ce = frame.get_column("CloseTime").dt.epoch("s").to_numpy()
    meta = {"source_file": path.name, "total_rows": int(frame.height),
            "file_start": str(frame.get_column("CloseTime").min()),
            "file_end": str(frame.get_column("CloseTime").max())}
    return frame, int(ce[0]), meta


# --------------------------------------------------------------------------- #
# Pure computation — Arm-2 alternate aggregation (last-source-close label) + injection
# --------------------------------------------------------------------------- #
def aggregate_ohlc_lastclose(bars_1m: pl.DataFrame, period_minutes: int,
                             min_coverage: float = MIN_COVERAGE) -> pl.DataFrame:
    """Arm-2 aggregation: identical to ``xen.bar_aggregator.aggregate_ohlc`` EXCEPT the CloseTime label.

    Same clock-aligned bucketing ``(epoch-1)//period_s``, coverage retention, and OHLC reduction (first Open
    / max High / min Low / last Close / summed TickVolume). The ONLY difference: each bar's ``CloseTime`` is
    the **actual last source 1-minute CloseTime** in the bucket, not the bucket right boundary.
    """
    if period_minutes < 2:
        raise ValueError(f"period_minutes must be >= 2, got {period_minutes}")
    if not (0.0 < min_coverage <= 1.0):
        raise ValueError(f"min_coverage must be in (0, 1], got {min_coverage}")
    if bars_1m.is_empty():
        return bars_1m.clear()
    if not bars_1m.get_column("CloseTime").is_sorted():
        raise ValueError("bars_1m must be sorted by CloseTime before aggregation")
    has_volume = "TickVolume" in bars_1m.columns
    period_seconds = period_minutes * SECONDS_PER_MINUTE
    bucketed = bars_1m.with_columns(
        ((pl.col("CloseTime").dt.epoch("s") - 1) // period_seconds).alias("_Bucket"))
    agg_exprs = [
        pl.first("Symbol").alias("Symbol"),
        pl.first("OpenTime").alias("OpenTime"),
        pl.last("CloseTime").alias("CloseTime"),                 # <-- the only change vs aggregate_ohlc
        pl.first("Open").alias("Open"),
        pl.max("High").alias("High"),
        pl.min("Low").alias("Low"),
        pl.last("Close").alias("Close"),
        pl.len().alias("SourceBars"),
    ]
    if has_volume:
        agg_exprs.append(pl.sum("TickVolume").alias("TickVolume"))
    min_bars = max(2, math.ceil(min_coverage * period_minutes))
    aggregated = (bucketed.group_by("_Bucket").agg(agg_exprs)
                  .filter(pl.col("SourceBars") >= min_bars).drop("_Bucket").sort("CloseTime"))
    cols = ["Symbol", "OpenTime", "CloseTime", "Open", "High", "Low", "Close"]
    if has_volume:
        cols.append("TickVolume")
    cols.append("SourceBars")
    return aggregated.select(cols)


def build_domain_bars_lastclose(source: pl.DataFrame, period_minutes: int,
                                min_coverage: float = MIN_COVERAGE) -> pl.DataFrame:
    """Arm-2 domain construction: ``aggregate_ohlc_lastclose`` + the same analysis-boundary fence.

    Mirrors ``xen.domain_bars.build_domain_bars`` exactly, swapping only the aggregation label. Under the
    last-source-close label the fence ``CloseTime <= source_max`` is trivially satisfied — a behavioural
    difference (the trailing window is retained) the arm exists to surface.
    """
    agg = aggregate_ohlc_lastclose(source, period_minutes=period_minutes, min_coverage=min_coverage)
    source_max = source.select(pl.max("CloseTime")).item()
    return agg.filter(pl.col("CloseTime") <= source_max)


@contextlib.contextmanager
def aggregation_arm(arm: str) -> Iterator[None]:
    """Inject the arm's aggregation into the substrate's ``build_cell_context`` (verbatim-preserving).

    ``E90.build_cell_context`` calls the module-global ``build_domain_bars(train_1m, period)``. Arm 1 uses the
    deployed function as-is; Arm 2 temporarily rebinds that name to the last-source-close variant, restoring it
    afterward. Nothing else in the substrate changes.
    """
    original = E90.build_domain_bars
    try:
        if arm == "PPS-ALTAGG":
            E90.build_domain_bars = build_domain_bars_lastclose
        yield
    finally:
        E90.build_domain_bars = original


# --------------------------------------------------------------------------- #
# Pure computation — per-cell binding-v2 streams over the full PPS timeline (per arm)
# --------------------------------------------------------------------------- #
def build_cells_arm(arm: str, files: dict[str, Path]) -> tuple[list[Any], dict[str, Any]]:
    """Resolve all 8 cells over the full PPS file for one arm; return (NoiseCell list, source meta).

    Reuses ``E96.resolve_cell_noise`` verbatim (binding-v2 stream; exit/keep from the frozen substrate). The
    substrate's ``train_edge_epoch`` is the file's last 1-minute close, so entry-fill + exit walks resolve over
    the entire PPS series. ``ts_lo`` is the file-start epoch (provenance fields cover the full series; they are
    disclosure-only and do not enter the binding metric).
    """
    cells: list[Any] = []
    src_meta: dict[str, Any] = {}
    with aggregation_arm(arm):
        for instrument, domain in tqdm(CELLS, desc=f"resolve cells [{arm}]", unit="cell", dynamic_ncols=True):
            if instrument not in files:
                raise FileNotFoundError(f"no PPS file for {instrument}")
            full_1m, ts_lo, meta = load_full_pps_1m(instrument, files[instrument])
            ctx, dropped, status = E90.build_cell_context(full_1m, instrument, domain)
            if ctx is None:
                raise RuntimeError(f"{instrument}-{domain} [{arm}]: failed to build ({status})")
            cells.append(E96.resolve_cell_noise(ctx, ts_lo, instrument, domain))
            meta.update({"arm": arm, "dropped_fraction": float(dropped), "n_domain_bars": int(ctx.n_domain),
                         "status": status})
            src_meta[f"{instrument}-{domain}"] = meta
    return cells, src_meta


def v2_streams(cells: list[Any]) -> list[Any]:
    """The binding-v2 ``CellStream`` for each cell (the frozen deployment construction)."""
    return [c.streams[BINDING_VARIANT] for c in cells]


# --------------------------------------------------------------------------- #
# Pure computation — evaluable-region binding metric (frozen statistic, restricted to epoch >= H_eval)
# --------------------------------------------------------------------------- #
def eval_boundary(grid_start: int, n_steps: int) -> int:
    """Estimator-warmup boundary epoch: the first grid step with a full trailing-covariance lookback window."""
    if n_steps <= BURN_IN_STEPS + 2:
        raise RuntimeError(f"insufficient grid ({n_steps} steps) for a {BURN_IN_STEPS}-step covariance burn-in")
    return grid_start + BURN_IN_STEPS * STEP_SECONDS


def eval_metrics(returns: np.ndarray, grid_epochs: np.ndarray, h_eval: int, seed_key: str) -> dict[str, Any]:
    """Binding metric: ``E95.series_risk_metrics`` (the m*-calibrated statistic) on ``epoch >= H_eval``."""
    mask = grid_epochs >= h_eval
    rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "ppsrobust", seed_key))
    return E95.series_risk_metrics(np.asarray(returns, dtype=np.float64)[mask], rng, n_boot=N_BOOT)


def confirm(metrics: dict[str, Any], band: float) -> bool:
    """Frozen rule: CONFIRM iff Sharpe one-sided LB > band AND co-binding Calmar one-sided LB > 0."""
    s_lo, c_lo = metrics.get("ann_sharpe_lo"), metrics.get("calmar_lo")
    return bool(np.isfinite(s_lo) and np.isfinite(c_lo) and s_lo > band and c_lo > 0.0)


def arm_label(m_b: dict[str, Any], confirm_b: bool) -> str:
    """Per-arm robustness label keyed off primary Portfolio B (frozen rubric; NON-BINDING on EXP-097)."""
    if confirm_b:
        return "ROBUST"
    s_pt, s_lo = m_b.get("ann_sharpe"), m_b.get("ann_sharpe_lo")
    if not (np.isfinite(s_pt) and np.isfinite(s_lo)):
        return "INCONCLUSIVE"
    if s_pt <= BAND["B"] or s_lo <= 0.0:
        return "DEGRADED"
    return "INCONCLUSIVE"


# --------------------------------------------------------------------------- #
# Pure computation — per-cell PPS disclosure (LESSON-001) + masking + retention companion
# --------------------------------------------------------------------------- #
def per_cell_pps(cells: list[Any], h_eval: int) -> list[dict[str, Any]]:
    """Per-cell PPS net expectancy (mean/median/one-sided 95% MBB LB) on events with exit_epoch >= H_eval."""
    rows: list[dict[str, Any]] = []
    for c in cells:
        s = c.streams[BINDING_VARIANT]
        emask = s.exit_epoch >= h_eval
        net = np.asarray(s.net, dtype=np.float64)[emask]
        net = net[np.isfinite(net)]
        if net.shape[0] >= 2:
            rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "cell_pps", c.name))
            ci_low = float(moving_block_bootstrap_cis(net, rng, n_boot=N_BOOT, alpha=BOOT_ALPHA).expectancy_lo)
            mean, median = float(net.mean()), float(np.median(net))
        else:
            ci_low = mean = median = float("nan")
        rows.append({"cell": c.name, "n_pps_events": int(net.shape[0]), "net_mean": mean,
                     "net_median": median, "net_ci_low_1s": ci_low,
                     "net_negative": bool(np.isfinite(mean) and mean < 0.0)})
    return rows


def masking_check(pnl_mat: np.ndarray, grid_start: int, n_steps: int, h_eval: int, streams: list[Any],
                  trade_mat: np.ndarray, confirm_b: bool) -> dict[str, Any]:
    """Drop-one robustness: does removing the largest-|contribution| cell flip the Portfolio-B CONFIRM label?

    Contribution proxy = each cell's summed evaluable-region MTM. Rebuild Portfolio B without that column and
    re-evaluate the frozen rule. A flip downgrades the arm's label to one-cell-dependent (disclosed).
    """
    grid_epochs = grid_start + np.arange(n_steps) * STEP_SECONDS
    emask = grid_epochs >= h_eval
    contrib = pnl_mat[emask].sum(axis=0)
    drop = int(np.argmax(np.abs(contrib)))
    keep_cols = [i for i in range(pnl_mat.shape[1]) if i != drop]
    res = PF.build_portfolio(pnl_mat[:, keep_cols], grid_start, STEP_SECONDS,
                             rebalance_steps=REBALANCE_STEPS, lookback_steps=LOOKBACK_STEPS,
                             target_ann_vol=TARGET_ANN_VOL, cap_mult=CAP_MULT,
                             periods_per_year=PERIODS_PER_YEAR_HOURLY, use_breaker=True,
                             breaker_window=BREAKER_WINDOW, trade_mat=trade_mat[:, keep_cols])
    m = eval_metrics(res.returns, grid_epochs, h_eval, "mask_B")
    confirm_drop = confirm(m, BAND["B"])
    return {"dropped_cell": streams[drop].name, "dropped_contribution": float(contrib[drop]),
            "confirm_B_full": bool(confirm_b), "confirm_B_drop_one": bool(confirm_drop),
            "label_flips": bool(confirm_b != confirm_drop),
            "drop_one_sharpe_lo": float(m["ann_sharpe_lo"]), "drop_one_calmar_lo": float(m["calmar_lo"])}


def retention_companion(arm_metrics: dict[str, dict[str, dict[str, Any]]],
                        arm_per_cell: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Descriptive PPS-vs-INFR-003 retention (reads EXP-097 committed CSVs; INFR-003 data is NOT re-read)."""
    out: dict[str, Any] = {"note": "descriptive context vs EXP-097 committed holdout outputs; "
                                   "INFR-003 parquet is NOT re-read; band stays fixed at m*"}
    ref_port: dict[str, dict[str, float]] = {}
    if EXP097_HOLDOUT_METRICS.exists():
        for r in pl.read_csv(EXP097_HOLDOUT_METRICS).iter_rows(named=True):
            ref_port[str(r["portfolio"])] = {"ann_sharpe_lo": float(r["ann_sharpe_lo"]),
                                             "calmar_lo": float(r["calmar_lo"])}
    ref_cell: dict[str, dict[str, float]] = {}
    if EXP097_PER_CELL.exists():
        for r in pl.read_csv(EXP097_PER_CELL).iter_rows(named=True):
            ref_cell[str(r["cell"])] = {"net_mean": float(r["net_mean"]),
                                        "net_ci_low_1s": float(r["net_ci_low_1s"])}
    port: dict[str, Any] = {}
    for arm in ARMS:
        per_p = {}
        for p in ("A", "B"):
            pps_lo = float(arm_metrics[arm][p]["ann_sharpe_lo"])
            inf_lo = ref_port.get(p, {}).get("ann_sharpe_lo", float("nan"))
            ratio = pps_lo / inf_lo if np.isfinite(inf_lo) and abs(inf_lo) > 1e-12 else float("nan")
            per_p[p] = {"pps_sharpe_lo": pps_lo, "infr003_sharpe_lo": inf_lo, "retention_ratio": ratio}
        cells = []
        for pc in arm_per_cell[arm]:
            ref = ref_cell.get(pc["cell"], {})
            cells.append({"cell": pc["cell"], "pps_net_mean": pc["net_mean"],
                          "infr003_net_mean": ref.get("net_mean", float("nan")),
                          "pps_net_ci_low": pc["net_ci_low_1s"],
                          "infr003_net_ci_low": ref.get("net_ci_low_1s", float("nan"))})
        port[arm] = {"portfolio": per_p, "per_cell": cells}
    out["arms"] = port
    return out


# --------------------------------------------------------------------------- #
# Pure computation — integrity assertions (exercised in the EVALUABLE region, per arm)
# --------------------------------------------------------------------------- #
def causal_weight_eval(pnl_mat: np.ndarray, trade_mat: np.ndarray, grid_start: int, h_eval: int) -> dict[str, Any]:
    """Perturb both grid matrices strictly AFTER an evaluable rebalance row; assert that weight is unchanged."""
    reb_idx = np.arange(0, pnl_mat.shape[0], REBALANCE_STEPS, dtype=np.int64)
    reb_epochs = grid_start + reb_idx * STEP_SECONDS
    evalr = reb_idx[reb_epochs >= h_eval]
    r = int(evalr[evalr.shape[0] // 2]) if evalr.shape[0] else int(reb_idx[reb_idx.shape[0] // 2])
    kw = dict(lookback_steps=LOOKBACK_STEPS, target_ann_vol=TARGET_ANN_VOL, cap_mult=CAP_MULT,
              periods_per_year=PERIODS_PER_YEAR_HOURLY, use_breaker=True, breaker_window=BREAKER_WINDOW)
    w0, _ = PF._rebalance_weight(pnl_mat, r, trade_mat=trade_mat, **kw)
    pnl_p, trade_p = pnl_mat.copy(), trade_mat.copy()
    pnl_p[r:] += 7.5
    trade_p[r:] += 7.5
    w1, _ = PF._rebalance_weight(pnl_p, r, trade_mat=trade_p, **kw)
    if not bool(np.array_equal(w0, w1)):
        raise RuntimeError("CAUSALITY VIOLATION: future grid rows changed a past (evaluable) rebalance weight")
    return {"causal_weight_pass": True, "rebalance_row_tested": r,
            "tested_in_evaluable": bool(grid_start + r * STEP_SECONDS >= h_eval)}


def causal_fill_eval(arm: str, files: dict[str, Path], h_eval: int) -> dict[str, Any]:
    """Perturb a 1m bar strictly BEFORE an evaluable signal close; assert that event's entry fill is unchanged."""
    instrument, domain = CELLS[0]
    with aggregation_arm(arm):
        full_1m, _ts, _m = load_full_pps_1m(instrument, files[instrument])
        ctx, _d, _s = E90.build_cell_context(full_1m, instrument, domain)
    idx, direction, atr_entry = ctx.core_entry_idx, ctx.core_direction, ctx.atr[ctx.core_entry_idx]
    entry_epoch = ctx.domain_close_epoch[idx].astype(np.int64)
    base = resolve_entry_fills(ctx.minute_open, ctx.minute_high, ctx.minute_low, ctx.minute_close_epoch,
                               entry_epoch, direction, atr_entry, ctx.train_edge_epoch,
                               k_worst=K_WORST, slippage_atr=SLIPPAGE_ATR)
    j = next((k for k in range(idx.shape[0]) if entry_epoch[k] >= h_eval), None)
    if j is None:
        return {"causal_entry_fill_pass": True, "note": "no evaluable-region event in the probe cell"}
    first = int(np.searchsorted(ctx.minute_close_epoch, entry_epoch[j], side="right"))
    mo, mh, ml = ctx.minute_open.copy(), ctx.minute_high.copy(), ctx.minute_low.copy()
    mo[:first] += 13.0
    mh[:first] += 13.0
    ml[:first] += 13.0
    pert = resolve_entry_fills(mo, mh, ml, ctx.minute_close_epoch, entry_epoch, direction, atr_entry,
                               ctx.train_edge_epoch, k_worst=K_WORST, slippage_atr=SLIPPAGE_ATR)
    same = (np.array_equal(base.fill_v2[j], pert.fill_v2[j], equal_nan=True)
            and np.array_equal(base.fill_v1[j], pert.fill_v1[j], equal_nan=True)
            and np.array_equal(base.fill_v3[j], pert.fill_v3[j], equal_nan=True))
    if not same:
        raise RuntimeError("CAUSALITY VIOLATION: a pre-signal 1m bar changed an evaluable entry fill")
    return {"causal_entry_fill_pass": bool(same), "evaluable_event_tested": int(j),
            "signal_in_evaluable": bool(entry_epoch[j] >= h_eval)}


# --------------------------------------------------------------------------- #
# Per-arm build (orchestration helper; returns everything the outputs/plots need)
# --------------------------------------------------------------------------- #
def build_arm(arm: str, files: dict[str, Path]) -> dict[str, Any]:
    """Resolve one arm end-to-end: cells -> grid -> A/B/naive -> evaluable metrics -> disclosure + integrity."""
    cells, src_meta = build_cells_arm(arm, files)
    streams = v2_streams(cells)
    grid_start, n_steps, pnl_mat, trade_mat = E95.build_grid(streams)
    h_eval = eval_boundary(grid_start, n_steps)
    grid_epochs = grid_start + np.arange(n_steps) * STEP_SECONDS
    n_eval_steps = int(np.count_nonzero(grid_epochs >= h_eval))
    LOGGER.info("[%s] grid: %d hourly steps; H_eval=%s; evaluable steps=%d", arm, n_steps,
                str(np.array(h_eval).astype("datetime64[s]")), n_eval_steps)

    common = dict(rebalance_steps=REBALANCE_STEPS, lookback_steps=LOOKBACK_STEPS, target_ann_vol=TARGET_ANN_VOL,
                  cap_mult=CAP_MULT, periods_per_year=PERIODS_PER_YEAR_HOURLY, breaker_window=BREAKER_WINDOW,
                  trade_mat=trade_mat)
    res_a = PF.build_portfolio(pnl_mat, grid_start, STEP_SECONDS, use_breaker=False, **common)
    res_b = PF.build_portfolio(pnl_mat, grid_start, STEP_SECONDS, use_breaker=True, **common)
    naive = PF.naive_inverse_vol(pnl_mat, grid_start, STEP_SECONDS, rebalance_steps=REBALANCE_STEPS,
                                 lookback_steps=LOOKBACK_STEPS, target_ann_vol=TARGET_ANN_VOL,
                                 periods_per_year=PERIODS_PER_YEAR_HOURLY, trade_mat=trade_mat)

    metrics = {"A": eval_metrics(res_a.returns, grid_epochs, h_eval, f"{arm}_A"),
               "B": eval_metrics(res_b.returns, grid_epochs, h_eval, f"{arm}_B"),
               "naive_iv": eval_metrics(naive, grid_epochs, h_eval, f"{arm}_naive")}
    confirm_a, confirm_b = confirm(metrics["A"], BAND["A"]), confirm(metrics["B"], BAND["B"])
    label = arm_label(metrics["B"], confirm_b)

    pc = per_cell_pps(cells, h_eval)
    mask = masking_check(pnl_mat, grid_start, n_steps, h_eval, streams, trade_mat, confirm_b)
    conservation = E96.conservation_check(cells)
    causal_weight = causal_weight_eval(pnl_mat, trade_mat, grid_start, h_eval)
    causal_fill = causal_fill_eval(arm, files, h_eval)
    determinism = E95.determinism_replay(streams, grid_start, n_steps, pnl_mat, trade_mat,
                                         {"_res_a": res_a, "_res_b": res_b})
    m_b2 = eval_metrics(res_b.returns, grid_epochs, h_eval, f"{arm}_B")
    stat_det = bool(m_b2["ann_sharpe_lo"] == metrics["B"]["ann_sharpe_lo"]
                    and m_b2["calmar_lo"] == metrics["B"]["calmar_lo"])

    return {"arm": arm, "cells": cells, "streams": streams, "grid_start": grid_start, "n_steps": n_steps,
            "pnl_mat": pnl_mat, "h_eval": h_eval, "n_eval_steps": n_eval_steps,
            "res_a": res_a, "res_b": res_b, "naive": naive, "metrics": metrics,
            "confirm_A": confirm_a, "confirm_B": confirm_b, "label": label, "per_cell": pc, "masking": mask,
            "conservation": conservation, "causal_weight": causal_weight, "causal_fill": causal_fill,
            "determinism": determinism, "binding_statistic_determinism": stat_det, "src_meta": src_meta}


# --------------------------------------------------------------------------- #
# Plotting (5 bounded plots; evaluable region; no data reloads)
# --------------------------------------------------------------------------- #
def _equity(returns: np.ndarray) -> np.ndarray:
    return np.cumsum(np.asarray(returns, dtype=np.float64))


def _drawdown(returns: np.ndarray) -> np.ndarray:
    eq = _equity(returns)
    return np.maximum.accumulate(eq) - eq


def make_plots(arms: dict[str, dict[str, Any]], retention: dict[str, Any]) -> None:
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    _plot_equity(arms)
    _plot_metric_vs_band(arms)
    _plot_per_cell(arms, retention)
    _plot_drawdown(arms)
    _plot_arm_compare(arms)


def _eval_slice(a: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    grid_epochs = a["grid_start"] + np.arange(a["n_steps"]) * STEP_SECONDS
    return grid_epochs, grid_epochs >= a["h_eval"]


def _plot_equity(arms: dict[str, dict[str, Any]]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=False)
    for ax, arm in zip(axes, ARMS):
        a = arms[arm]
        grid_epochs, hm = _eval_slice(a)
        t = grid_epochs[hm].astype("datetime64[s]")
        ax.plot(t, _equity(a["res_a"].returns[hm]), label="A (static ERC)", color="steelblue")
        ax.plot(t, _equity(a["res_b"].returns[hm]), label="B (ERC+breaker) [primary]", color="seagreen")
        ax.plot(t, _equity(np.asarray(a["naive"])[hm]), label="naive IV", color="gray", lw=0.9, ls="--")
        for s, ci in zip(a["streams"], range(a["pnl_mat"].shape[1])):
            ax.plot(t, _equity(a["pnl_mat"][hm, ci]), lw=0.5, alpha=0.45, label=f"cell {s.name}")
        ax.axhline(0, color="black", lw=0.6)
        ax.set_title(f"{arm}", fontsize=9)
        ax.legend(fontsize=5, ncol=2)
    fig.suptitle("EXP-098 PPS evaluable equity curves (cumulative net, vol-anchored)", fontsize=10)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "pps_equity_curves.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_metric_vs_band(arms: dict[str, dict[str, Any]]) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.6))
    ports, x = ["A", "B"], np.arange(2)
    width = 0.38
    for k, arm in enumerate(ARMS):
        m = arms[arm]["metrics"]
        ax1.bar(x + (k - 0.5) * width, [m[p]["ann_sharpe_lo"] for p in ports], width, label=arm)
        ax2.bar(x + (k - 0.5) * width, [m[p]["calmar_lo"] for p in ports], width, label=arm)
    for i, p in enumerate(ports):
        ax1.axhline(BAND[p], color="red", ls="--", lw=0.7)
    ax1.set_xticks(x, [f"{p} (band {BAND[p]})" for p in ports])
    ax1.set_title("PPS Sharpe LB vs band (red), per arm", fontsize=9)
    ax1.legend(fontsize=7)
    ax2.axhline(0.0, color="red", ls="--", lw=0.7, label="Calmar band (0)")
    ax2.set_xticks(x, ports)
    ax2.set_title("PPS Calmar LB vs band (0), per arm", fontsize=9)
    ax2.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "pps_metric_vs_band.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_per_cell(arms: dict[str, dict[str, Any]], retention: dict[str, Any]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
    for ax, arm in zip(axes, ARMS):
        pc = arms[arm]["per_cell"]
        names = [r["cell"] for r in pc]
        x = np.arange(len(names))
        means = [r["net_mean"] for r in pc]
        los = [r["net_ci_low_1s"] for r in pc]
        yerr = [max(0.0, m - lo) if np.isfinite(m) and np.isfinite(lo) else 0.0 for m, lo in zip(means, los)]
        colors = ["indianred" if r["net_negative"] else "seagreen" for r in pc]
        ax.bar(x - 0.2, means, 0.4, yerr=yerr, capsize=2, color=colors, label="PPS net (mean; whisker=MBB LB)")
        ref = {d["cell"]: d for d in retention["arms"][arm]["per_cell"]}
        inf = [ref.get(n, {}).get("infr003_net_mean", float("nan")) for n in names]
        ax.bar(x + 0.2, inf, 0.4, color="gray", alpha=0.7, label="EXP-097 holdout net mean")
        ax.axhline(0, color="black", lw=0.6)
        ax.set_xticks(x, names, rotation=45, ha="right", fontsize=7)
        ax.set_title(f"{arm} (red = net-negative on PPS)", fontsize=9)
        ax.legend(fontsize=7)
    axes[0].set_ylabel("net per-event expectancy (ATR)")
    fig.suptitle("EXP-098 per-cell PPS net vs EXP-097 INFR-003 holdout (retention)", fontsize=10)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "pps_per_cell_net.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_drawdown(arms: dict[str, dict[str, Any]]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6), sharey=True)
    for ax, arm in zip(axes, ARMS):
        a = arms[arm]
        grid_epochs, hm = _eval_slice(a)
        t = grid_epochs[hm].astype("datetime64[s]")
        ax.fill_between(t, -_drawdown(a["res_a"].returns[hm]), 0, color="steelblue", alpha=0.5, label="A")
        ax.fill_between(t, -_drawdown(a["res_b"].returns[hm]), 0, color="seagreen", alpha=0.45,
                        label="B [primary]")
        ax.set_title(f"{arm}", fontsize=9)
        ax.legend(fontsize=7)
    axes[0].set_ylabel("drawdown (negative)")
    fig.suptitle("EXP-098 A vs B PPS drawdown (underwater), per arm", fontsize=10)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "pps_drawdown_A_vs_B.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_arm_compare(arms: dict[str, dict[str, Any]]) -> None:
    keys = ["B Sharpe LB", "B Calmar LB", "B MaxDD", "n_weeks", "n_domain (sum)"]
    fig, ax = plt.subplots(figsize=(10, 4.6))
    x = np.arange(len(keys))
    width = 0.38
    for k, arm in enumerate(ARMS):
        m = arms[arm]["metrics"]["B"]
        ndom = sum(v.get("n_domain_bars", 0) for v in arms[arm]["src_meta"].values())
        vals = [m["ann_sharpe_lo"], m["calmar_lo"], m["max_drawdown"], float(m["n_weeks"]), float(ndom)]
        ax.bar(x + (k - 0.5) * width, vals, width, label=arm)
    ax.set_xticks(x, keys, rotation=20, ha="right", fontsize=8)
    ax.set_yscale("symlog")
    ax.set_title("EXP-098 Arm 1 vs Arm 2 (aggregation sensitivity; symlog y)", fontsize=9)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "pps_arm_comparison.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Output writers
# --------------------------------------------------------------------------- #
def write_outputs(arms: dict[str, dict[str, Any]], retention: dict[str, Any], overall: dict[str, Any]) -> None:
    """Write every headline artifact named in the analysis plan (per arm + overall)."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    metric_rows: list[dict[str, Any]] = []
    per_cell_rows: list[dict[str, Any]] = []
    for arm in ARMS:
        a = arms[arm]
        grid_epochs = a["grid_start"] + np.arange(a["n_steps"]) * STEP_SECONDS
        ts = grid_epochs.astype("datetime64[s]").astype(str)
        in_eval = (grid_epochs >= a["h_eval"]).astype(int)
        tag = arm.lower().replace("-", "_")
        pl.DataFrame({"timestamp": ts, "net_return": a["res_a"].returns, "in_eval": in_eval}).write_csv(
            RESULTS_DIR / f"portfolio_returns_A_{tag}.csv")
        pl.DataFrame({"timestamp": ts, "net_return": a["res_b"].returns, "in_eval": in_eval}).write_csv(
            RESULTS_DIR / f"portfolio_returns_B_{tag}.csv")
        for r in a["per_cell"]:
            per_cell_rows.append({"arm": arm, **r})
        for p in ("A", "B", "naive_iv"):
            metric_rows.append({"arm": arm, "portfolio": p, **{k: v for k, v in a["metrics"][p].items()}})
        pl.DataFrame(a["conservation"]).write_csv(RESULTS_DIR / f"mtm_conservation_{tag}.csv")

    pl.DataFrame(per_cell_rows).write_csv(RESULTS_DIR / "per_cell_pps.csv")
    pl.DataFrame(metric_rows, strict=False).write_csv(RESULTS_DIR / "eval_metrics.csv")
    (RESULTS_DIR / "retention.json").write_text(json.dumps(retention, indent=2, default=str))
    (RESULTS_DIR / "verdict.json").write_text(json.dumps(overall, indent=2, default=str))

    integrity = {arm: {"mtm_conservation_pass": all(r["PASS"] for r in arms[arm]["conservation"]),
                       "causal_weight": arms[arm]["causal_weight"], "causal_fill": arms[arm]["causal_fill"],
                       "determinism": arms[arm]["determinism"],
                       "binding_statistic_determinism": arms[arm]["binding_statistic_determinism"],
                       "masking": arms[arm]["masking"]} for arm in ARMS}
    integrity["infr003_holdout_loaded"] = False
    integrity["real_prices_only"] = True
    (RESULTS_DIR / "integrity.json").write_text(json.dumps(integrity, indent=2, default=str))


def hash_outputs() -> dict[str, str]:
    """SHA-256 of each headline output (byte-identical second-pass pin)."""
    out: dict[str, str] = {}
    for p in sorted(RESULTS_DIR.glob("*.csv")) + sorted(RESULTS_DIR.glob("*.json")):
        out[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def run() -> dict[str, Any]:
    """Run both arms of the PPS robustness replication; adjudicate the (non-binding) robustness labels."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    files = discover_pps_files()
    LOGGER.info("PPS files discovered for %d instruments under %s", len(files), PPS_DIR)

    arms: dict[str, dict[str, Any]] = {}
    for arm in ARMS:
        arms[arm] = build_arm(arm, files)

    retention = retention_companion({a: arms[a]["metrics"] for a in ARMS},
                                    {a: arms[a]["per_cell"] for a in ARMS})

    cross_broker_robust = bool(arms["PPS-CANON"]["label"] == "ROBUST")
    aggregation_robust = bool(all(arms[a]["label"] == "ROBUST" for a in ARMS))
    overall: dict[str, Any] = {
        "experiment_id": EXPERIMENT_ID, "role": "non-binding cross-broker & aggregation-method robustness "
        "replication of the G-022a-frozen RSI-2 fade deployment portfolio (PPS data)",
        "primary": "B", "band": BAND,
        "rule": "CONFIRM(P) iff PPS Sharpe_LB(P) > band_P AND Calmar_LB(P) > 0; band_A=1.75, band_B=2.00",
        "cross_broker_robust": cross_broker_robust, "aggregation_robust": aggregation_robust,
        "exp097_verdict_unchanged": True, "counted_test_reads": 0, "candidate_slots": 0,
        "infr003_holdout_loaded": False,
        "per_arm": {a: {"label": arms[a]["label"], "confirm_B": arms[a]["confirm_B"],
                        "confirm_A": arms[a]["confirm_A"],
                        "B": {k: arms[a]["metrics"]["B"][k] for k in
                              ("ann_sharpe", "ann_sharpe_lo", "calmar_lo", "n_weeks", "max_drawdown")},
                        "A": {k: arms[a]["metrics"]["A"][k] for k in
                              ("ann_sharpe", "ann_sharpe_lo", "calmar_lo")},
                        "masking_label_flips": arms[a]["masking"]["label_flips"],
                        "h_eval": str(np.array(arms[a]["h_eval"]).astype("datetime64[s]")),
                        "burn_in_steps": BURN_IN_STEPS, "n_eval_steps": arms[a]["n_eval_steps"]}
                    for a in ARMS}}

    make_plots(arms, retention)
    write_outputs(arms, retention, overall)
    meta = _build_metadata(arms, overall, retention)
    meta["output_hashes"] = hash_outputs()
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(meta, indent=2, default=str))
    _log_summary(arms, overall, time.perf_counter() - t0)
    return meta


def _build_metadata(arms: dict[str, dict[str, Any]], overall: dict[str, Any],
                    retention: dict[str, Any]) -> dict[str, Any]:
    return {
        "experiment_id": EXPERIMENT_ID, "phase": "022", "family": "CF-MR-001", "hyp": "HYP-003",
        "role": "non-binding cross-broker & aggregation-method robustness replication (PPS data; D0-amendment-002)",
        "opened_by": "D0-amendment-002", "exp097_verdict_unchanged": True,
        "data_source": str(PPS_DIR), "instruments": list(PPS_INSTRUMENTS), "arms": list(ARMS),
        "arm2_aggregation": "last-source-close CloseTime label (AGG-LASTCLOSE) + analysis-boundary fence",
        "frozen_construction": "G-022a: carry-8 set; binding-v2 noise-aware ERC + intra-1h MTM; LW-90d cov, "
                               "weekly rebalance, 10% vol anchor, 1.5x cap, trailing-50 breaker; v2 fill "
                               "(next-1m-open + 0.05xATR adverse slippage); EXIT-RCT/adverse/cost/band frozen",
        "eval_slice": "full PPS timeline after the LOOKBACK_STEPS covariance burn-in (NOT a holdout)",
        "burn_in_steps": BURN_IN_STEPS, "generated_utc": datetime.now(timezone.utc).isoformat(),
        "master_seed": MASTER_SEED, "n_boot": N_BOOT, "boot_alpha": BOOT_ALPHA, "band": BAND,
        "deployable_cells": [f"{i}-{d}" for i, d in CELLS], "surviving_exit": ARM,
        "overall": overall, "retention": retention,
        "per_arm_metrics": {a: arms[a]["metrics"] for a in ARMS},
        "per_arm_source_meta": {a: arms[a]["src_meta"] for a in ARMS},
        "real_prices_only": True, "infr003_holdout_loaded": False,
        "counted_test_reads": 0, "candidate_slots": 0,
        "read_accounting": ("PPS robustness read on an independent broker dataset; outside the INFR-003 "
                            "analysis-TEST 48-stratum ledger AND the INFR-003 global holdout (never loaded); "
                            "recorded as a robustness governance disclosure; cannot upgrade/revoke EXP-097"),
    }


def _log_summary(arms: dict[str, dict[str, Any]], overall: dict[str, Any], secs: float) -> None:
    LOGGER.info("EXP-098 done in %.1fs | cross_broker_robust=%s aggregation_robust=%s",
                secs, overall["cross_broker_robust"], overall["aggregation_robust"])
    for arm in ARMS:
        m = arms[arm]["metrics"]
        LOGGER.info("  [%s] label=%s | B Sharpe %.3f (lo %.3f) Calmar_lo %.3f band %.2f CONFIRM=%s | "
                    "A lo %.3f CONFIRM=%s | n_weeks=%d mask_flip=%s det=%s",
                    arm, arms[arm]["label"], m["B"]["ann_sharpe"], m["B"]["ann_sharpe_lo"], m["B"]["calmar_lo"],
                    BAND["B"], arms[arm]["confirm_B"], m["A"]["ann_sharpe_lo"], arms[arm]["confirm_A"],
                    m["B"]["n_weeks"], arms[arm]["masking"]["label_flips"],
                    arms[arm]["determinism"]["determinism_pass"])


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    argparse.ArgumentParser(description="EXP-098 PPS cross-broker/aggregation robustness replication").parse_args()
    meta = run()
    o = meta["overall"]
    print(f"EXP-098 complete | cross_broker_robust={o['cross_broker_robust']} "
          f"aggregation_robust={o['aggregation_robust']} | "
          + " | ".join(f"{a}:{o['per_arm'][a]['label']}(B lo "
                       f"{o['per_arm'][a]['B']['ann_sharpe_lo']:.3f})" for a in ARMS)
          + f" | exp097_unchanged={o['exp097_verdict_unchanged']} counted_reads={o['counted_test_reads']}")


if __name__ == "__main__":
    main()
