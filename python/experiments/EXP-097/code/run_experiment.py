"""EXP-097 — Global-Holdout Release: One-Shot OOS-Final Confirmation (RSI-2 Fade Deployment Portfolio).

Phase 022 / ``CF-MR-001`` / HYP-003 — **the single sanctioned global-holdout release** (à la EXP-032).
Governing: ``docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/`` (``G-022a-gate-criteria.md``
freeze, ``G-022-gate-criteria.md`` terminal rubric, ``D0-predeclarations.md`` §D1/§D4/§D7/§D9, ``D0-amendment-001.md``).
Scope/plan: ``scope.md`` / ``analysis-plan.md``.

What this is. Spend the single sanctioned final-30% global-holdout shot to adjudicate the binding deployment
verdict (G-022): deployed as the G-022a-FROZEN, noise-aware (binding **v2** entry fill) causal ERC portfolio with
intra-1h mark-to-market, does the **primary Portfolio B** confirm a positive risk-adjusted edge on the fully-fresh
holdout — ``Sharpe_LB(B) > 2.00 AND Calmar_LB(B) > 0``? Portfolio A is co-adjudicated on the **same single
materialization** (operator decision 2026-06-25 — ONE read) and disclosed, but cannot rescue the family verdict
via an OR. **Non-repeatable, non-upgradable.**

Nothing is re-derived/re-tuned/re-selected. The ONLY new acts: (a) load the final-30% global holdout for the first
time; (b) restrict the binding metric to the **holdout region** (grid steps with epoch >= H, H = max per-cell
analysis cutoff). Everything else is the EXP-095/096 construction + the *identical* m-star-calibrated statistic
(``E95.series_risk_metrics``), reused verbatim.
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

from xen.ass import moving_block_bootstrap_cis  # noqa: E402
from xen.intrabar_fill import resolve_entry_fills  # noqa: E402
from xen.referee_calibration import seed_for  # noqa: E402

# --------------------------------------------------------------------------- #
# Path setup + reuse the validated EXP-096 module (transitively EXP-095 + EXP-090)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-097"
CODE_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = CODE_DIR.parent
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
EXP_ROOT = EXPERIMENT_DIR.parent
EXP096_CODE = EXP_ROOT / "EXP-096" / "code" / "run_experiment.py"
EXP096_DEGRADATION = EXP_ROOT / "EXP-096" / "results" / "per_cell_degradation.csv"


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
MR_COST_RT_BPS = E96.MR_COST_RT_BPS
STEP_SECONDS = E96.STEP_SECONDS
SECONDS_PER_YEAR = E96.SECONDS_PER_YEAR
N_BOOT = E96.N_BOOT                                             # 10_000
BOOT_ALPHA = E96.BOOT_ALPHA                                     # 0.10 -> one-sided 95% lower bound
REBALANCE_STEPS = E96.REBALANCE_STEPS
LOOKBACK_STEPS = E96.LOOKBACK_STEPS
TARGET_ANN_VOL = E96.TARGET_ANN_VOL
CAP_MULT = E96.CAP_MULT
BREAKER_WINDOW = E96.BREAKER_WINDOW
CADENCE_STEPS = E96.CADENCE_STEPS
PERIODS_PER_YEAR_HOURLY = E95.PERIODS_PER_YEAR_HOURLY
BINDING_VARIANT = E96.BINDING_VARIANT                            # "v2"
SLIPPAGE_ATR = E96.SLIPPAGE_ATR                                 # 0.05
K_WORST = E96.K_WORST                                          # 3
FRAGILE_CELLS = E96.FRAGILE_CELLS                              # ("USTEC-1h", "US2000-1h")

# Frozen confirmation bands (= the inherited A4 MDE m\*; G-022a §3.4). NOT tuned.
BAND: dict[str, float] = {"A": 1.75, "B": 2.00}
# EXP-096 binding-v2 analysis-set portfolio Sharpe LBs (published; for the shrinkage companion only).
ANALYSIS_V2_SHARPE_LO: dict[str, float] = {"A": 5.146751974351359, "B": 4.897179416042319}

LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# I/O helper — the holdout-slice loader (the ONLY place the final-30% is read)
# --------------------------------------------------------------------------- #
def load_full_1m(instrument: str, path: Path) -> tuple[pl.DataFrame, int, dict[str, Any]]:
    """Load the **full file** ``[0, total_rows)`` (analysis warmup + the holdout shot); return frame, H_cell, meta.

    This is the single sanctioned global-holdout read: the final-30% ``[int(total*0.7), total)`` is materialized
    here for the first time. ``H_cell`` = the ``CloseTime`` epoch at row ``int(total*0.7)`` (the first holdout
    1-minute bar) — the per-file analysis/holdout boundary. The analysis region is loaded as **past-only causal
    warmup** (indicators, trailing covariance/vol, breaker mean, weight history) — not a new read.
    """
    scan = pl.scan_parquet(path).sort("CloseTime")
    total_rows = int(scan.select(pl.len()).collect().item())
    analysis_cutoff = int(total_rows * 0.7)
    frame = scan.collect()
    if frame.height != total_rows:                               # full file materialized (the shot)
        raise RuntimeError(f"{instrument}: full slice {frame.height} != {total_rows}")
    if not frame.get_column("CloseTime").is_sorted():
        raise RuntimeError(f"{instrument}: file not sorted by CloseTime")
    ce = frame.get_column("CloseTime").dt.epoch("s").to_numpy()
    h_cell = int(ce[analysis_cutoff])                            # first holdout 1m close epoch
    meta = {"source_file": path.name, "total_rows": total_rows, "analysis_cutoff": analysis_cutoff,
            "n_holdout_rows": total_rows - analysis_cutoff,
            "analysis_end": str(frame.get_column("CloseTime")[analysis_cutoff - 1]),
            "file_end": str(frame.get_column("CloseTime").max())}
    return frame, h_cell, meta


# --------------------------------------------------------------------------- #
# Pure computation — per-cell binding-v2 streams over warmup+holdout
# --------------------------------------------------------------------------- #
def build_cells_full() -> tuple[list[Any], int, dict[str, Any]]:
    """Resolve all 8 cells over the full file; return (NoiseCell list, global boundary H, source meta).

    Reuses ``E96.resolve_cell_noise`` verbatim (binding-v2 stream; exit/keep reused from the frozen substrate).
    The substrate's ``train_edge_epoch`` is the file's last 1-minute close, so entry-fill + exit walks resolve
    **through** the holdout (the intended behaviour). ``H`` = max per-cell analysis cutoff (the global
    binding-metric boundary).
    """
    files, _ = E90.VAL005.discover_infr003_files()
    files = {k.upper(): v for k, v in files.items()}
    cells: list[Any] = []
    src_meta: dict[str, Any] = {}
    h_cells: dict[str, int] = {}
    for instrument, domain in tqdm(CELLS, desc="resolve cells (holdout)", unit="cell", dynamic_ncols=True):
        if instrument not in files:
            raise FileNotFoundError(f"no INFR-003 file for {instrument}")
        full_1m, h_cell, meta = load_full_1m(instrument, files[instrument])
        ctx, _dropped, status = E90.build_cell_context(full_1m, instrument, domain)
        if ctx is None:
            raise RuntimeError(f"{instrument}-{domain}: failed to build ({status})")
        cells.append(E96.resolve_cell_noise(ctx, h_cell, instrument, domain))
        meta["H_cell_epoch"] = h_cell
        src_meta[f"{instrument}-{domain}"] = meta
        h_cells[f"{instrument}-{domain}"] = h_cell
    h_global = max(h_cells.values())
    src_meta["_H_global_epoch"] = h_global
    src_meta["_H_cells"] = h_cells
    return cells, h_global, src_meta


def v2_streams(cells: list[Any]) -> list[Any]:
    """The binding-v2 ``CellStream`` for each cell (the frozen deployment construction)."""
    return [c.streams[BINDING_VARIANT] for c in cells]


# --------------------------------------------------------------------------- #
# Pure computation — holdout-region binding metric (frozen statistic, restricted to epoch >= H)
# --------------------------------------------------------------------------- #
def holdout_metrics(returns: np.ndarray, grid_epochs: np.ndarray, h_global: int, seed_key: str,
                    ) -> dict[str, Any]:
    """Binding holdout metric: ``E95.series_risk_metrics`` (the m\\*-calibrated statistic) on ``epoch >= H``.

    The same function that produced the analysis-set LBs and the m\\* calibration — weekly-aggregated annualized
    Sharpe + Calmar moving-block one-sided lower bounds (block = ``default_block_length(n_weeks)``, N_BOOT=10_000,
    α=0.10). Restricting to the holdout region guarantees no analysis-set return enters the holdout statistic.
    """
    mask = grid_epochs >= h_global
    rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "holdout", seed_key))
    return E95.series_risk_metrics(np.asarray(returns, dtype=np.float64)[mask], rng, n_boot=N_BOOT)


def confirm(metrics: dict[str, Any], band: float) -> bool:
    """Frozen rule: CONFIRM iff Sharpe one-sided LB > band AND co-binding Calmar one-sided LB > 0."""
    s_lo, c_lo = metrics.get("ann_sharpe_lo"), metrics.get("calmar_lo")
    return bool(np.isfinite(s_lo) and np.isfinite(c_lo) and s_lo > band and c_lo > 0.0)


def adjudicate_g022(m_b: dict[str, Any], confirm_b: bool) -> str:
    """Terminal G-022 (keyed off primary B; frozen rubric). DEPLOYABLE_CONFIRMED / DECAYED / INCONCLUSIVE."""
    if confirm_b:
        return "DEPLOYABLE_CONFIRMED"
    s_pt, s_lo = m_b.get("ann_sharpe"), m_b.get("ann_sharpe_lo")
    if not (np.isfinite(s_pt) and np.isfinite(s_lo)):
        return "INCONCLUSIVE"                                    # power-limited / undefined metric
    if s_pt <= BAND["B"] or s_lo <= 0.0:
        return "DECAYED"
    return "INCONCLUSIVE"                                        # point clears band but LB <= band, or Calmar leg


# --------------------------------------------------------------------------- #
# Pure computation — per-cell holdout disclosure + shrinkage
# --------------------------------------------------------------------------- #
def per_cell_holdout(cells: list[Any], h_global: int) -> list[dict[str, Any]]:
    """Per-cell holdout net expectancy (mean/median/one-sided 95% MBB LB) on events with exit_epoch >= H."""
    rows: list[dict[str, Any]] = []
    for c in cells:
        s = c.streams[BINDING_VARIANT]
        hmask = s.exit_epoch >= h_global
        net = np.asarray(s.net, dtype=np.float64)[hmask]
        net = net[np.isfinite(net)]
        if net.shape[0] >= 2:
            rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "cell_holdout", c.name))
            ci_low = float(moving_block_bootstrap_cis(net, rng, n_boot=N_BOOT, alpha=BOOT_ALPHA).expectancy_lo)
            mean, median = float(net.mean()), float(np.median(net))
        else:
            ci_low = mean = median = float("nan")
        rows.append({"cell": c.name, "n_holdout_events": int(net.shape[0]), "net_mean": mean,
                     "net_median": median, "net_ci_low_1s": ci_low,
                     "net_negative": bool(np.isfinite(mean) and mean < 0.0)})
    return rows


def shrinkage(metrics: dict[str, dict[str, Any]], per_cell: list[dict[str, Any]]) -> dict[str, Any]:
    """Descriptive analysis-v2 -> holdout deltas (portfolio Sharpe LB + per-cell net), against the honest prior."""
    out: dict[str, Any] = {"note": "descriptive context vs EXP-096 binding-v2 analysis-set; band stays fixed at m*",
                           "portfolio_sharpe_lo": {}}
    for p in ("A", "B"):
        a = ANALYSIS_V2_SHARPE_LO[p]
        h = float(metrics[p]["ann_sharpe_lo"])
        out["portfolio_sharpe_lo"][p] = {"analysis_v2": a, "holdout": h, "delta": h - a}
    ref: dict[str, dict[str, float]] = {}
    if EXP096_DEGRADATION.exists():
        for r in pl.read_csv(EXP096_DEGRADATION).iter_rows(named=True):
            ref[r["cell"]] = {"v2_net_mean": float(r["v2_net_mean"]), "v2_net_median": float(r["v2_net_median"]),
                              "v2_net_ci_low_1s": float(r["v2_net_ci_low_1s"])}
    cell_deltas: list[dict[str, Any]] = []
    for pc in per_cell:
        a = ref.get(pc["cell"], {})
        cell_deltas.append({"cell": pc["cell"],
                            "analysis_v2_net_mean": a.get("v2_net_mean", float("nan")),
                            "holdout_net_mean": pc["net_mean"],
                            "delta_net_mean": pc["net_mean"] - a["v2_net_mean"] if a else float("nan"),
                            "analysis_v2_net_ci_low": a.get("v2_net_ci_low_1s", float("nan")),
                            "holdout_net_ci_low": pc["net_ci_low_1s"]})
    out["per_cell"] = cell_deltas
    return out


# --------------------------------------------------------------------------- #
# Pure computation — integrity assertions (exercised in the HOLDOUT region)
# --------------------------------------------------------------------------- #
def conservation_check(cells: list[Any]) -> list[dict[str, Any]]:
    """Global per-position MTM conservation Σ(marks)=realized net per cell (≤1e-9 ATR). Reuses EXP-096's check."""
    return E96.conservation_check(cells)


def causal_weight_holdout(pnl_mat: np.ndarray, trade_mat: np.ndarray, grid_start: int,
                          h_global: int) -> dict[str, Any]:
    """Perturb both grid matrices strictly AFTER a HOLDOUT rebalance row; assert that weight is unchanged."""
    reb_idx = np.arange(0, pnl_mat.shape[0], REBALANCE_STEPS, dtype=np.int64)
    reb_epochs = grid_start + reb_idx * STEP_SECONDS
    hold = reb_idx[reb_epochs >= h_global]
    r = int(hold[hold.shape[0] // 2]) if hold.shape[0] else int(reb_idx[reb_idx.shape[0] // 2])
    kw = dict(lookback_steps=LOOKBACK_STEPS, target_ann_vol=TARGET_ANN_VOL, cap_mult=CAP_MULT,
              periods_per_year=PERIODS_PER_YEAR_HOURLY, use_breaker=True, breaker_window=BREAKER_WINDOW)
    w0, _ = PF._rebalance_weight(pnl_mat, r, trade_mat=trade_mat, **kw)
    pnl_p, trade_p = pnl_mat.copy(), trade_mat.copy()
    pnl_p[r:] += 7.5
    trade_p[r:] += 7.5
    w1, _ = PF._rebalance_weight(pnl_p, r, trade_mat=trade_p, **kw)
    if not bool(np.array_equal(w0, w1)):
        raise RuntimeError("CAUSALITY VIOLATION: future grid rows changed a past (holdout) rebalance weight")
    return {"causal_weight_pass": True, "rebalance_row_tested": r,
            "tested_in_holdout": bool(grid_start + r * STEP_SECONDS >= h_global)}


def causal_fill_holdout(cells_meta: dict[str, Any], h_global: int) -> dict[str, Any]:
    """Perturb a 1m bar strictly BEFORE a HOLDOUT signal close; assert that event's entry fill is unchanged.

    Rebuilds one cell's context and exercises the entry-fill on an event whose signal close lies in the holdout
    (entry_epoch >= H), so the causal-fill guard is tested on holdout data (not warmup).
    """
    files, _ = E90.VAL005.discover_infr003_files()
    files = {k.upper(): v for k, v in files.items()}
    instrument, domain = CELLS[0]
    full_1m, _h, _m = load_full_1m(instrument, files[instrument])
    ctx, _d, _s = E90.build_cell_context(full_1m, instrument, domain)
    idx, direction, atr_entry = ctx.core_entry_idx, ctx.core_direction, ctx.atr[ctx.core_entry_idx]
    entry_epoch = ctx.domain_close_epoch[idx].astype(np.int64)
    base = resolve_entry_fills(ctx.minute_open, ctx.minute_high, ctx.minute_low, ctx.minute_close_epoch,
                               entry_epoch, direction, atr_entry, ctx.train_edge_epoch,
                               k_worst=K_WORST, slippage_atr=SLIPPAGE_ATR)
    j = next((k for k in range(idx.shape[0]) if entry_epoch[k] >= h_global), None)
    if j is None:
        return {"causal_entry_fill_pass": True, "note": "no holdout event in the probe cell"}
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
        raise RuntimeError("CAUSALITY VIOLATION: a pre-signal 1m bar changed a holdout entry fill")
    return {"causal_entry_fill_pass": bool(same), "holdout_event_tested": int(j),
            "signal_in_holdout": bool(entry_epoch[j] >= h_global)}


# --------------------------------------------------------------------------- #
# Plotting (5 bounded plots; holdout region; no reloads)
# --------------------------------------------------------------------------- #
def _equity(returns: np.ndarray) -> np.ndarray:
    return np.cumsum(np.asarray(returns, dtype=np.float64))


def _drawdown(returns: np.ndarray) -> np.ndarray:
    eq = _equity(returns)
    return np.maximum.accumulate(eq) - eq


def make_plots(res_a: Any, res_b: Any, naive: np.ndarray, pnl_mat: np.ndarray, grid_start: int,
               n_steps: int, h_global: int, streams: list[Any], metrics: dict[str, dict[str, Any]],
               per_cell: list[dict[str, Any]], shrink: dict[str, Any]) -> None:
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    grid_epochs = grid_start + np.arange(n_steps) * STEP_SECONDS
    hmask = grid_epochs >= h_global
    _plot_equity(grid_epochs, hmask, res_a, res_b, naive, pnl_mat, streams)
    _plot_metric_vs_band(metrics)
    _plot_per_cell_holdout(per_cell, shrink)
    _plot_drawdown(grid_epochs, hmask, res_a, res_b)
    _plot_breaker_timeline(grid_epochs, hmask, res_b, streams)


def _plot_equity(grid_epochs: np.ndarray, hmask: np.ndarray, res_a: Any, res_b: Any, naive: np.ndarray,
                 pnl_mat: np.ndarray, streams: list[Any]) -> None:
    t = grid_epochs[hmask].astype("datetime64[s]")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(t, _equity(res_a.returns[hmask]), label="Portfolio A (static ERC)", color="steelblue")
    ax.plot(t, _equity(res_b.returns[hmask]), label="Portfolio B (ERC + breaker) [primary]", color="seagreen")
    ax.plot(t, _equity(np.asarray(naive)[hmask]), label="naive inverse-vol", color="gray", lw=0.9, ls="--")
    for ci, s in enumerate(streams):
        ax.plot(t, _equity(pnl_mat[hmask, ci]), lw=0.6, alpha=0.5, label=f"cell {s.name}")
    ax.axhline(0, color="black", lw=0.6)
    ax.set_title("EXP-097 holdout equity curves (cumulative net, vol-anchored; OOS-final)", fontsize=10)
    ax.set_ylabel("cumulative net return")
    ax.legend(fontsize=6, ncol=2)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "holdout_equity_curves.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_metric_vs_band(metrics: dict[str, dict[str, Any]]) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    ports = ["A", "B"]
    x = np.arange(2)
    sh_lo = [metrics[p]["ann_sharpe_lo"] for p in ports]
    ca_lo = [metrics[p]["calmar_lo"] for p in ports]
    ax1.bar(x, sh_lo, color=["steelblue", "seagreen"])
    for i, p in enumerate(ports):
        ax1.axhline(BAND[p], color="red", ls="--", lw=0.8)
        ax1.plot(x[i], ANALYSIS_V2_SHARPE_LO[p], marker="o", color="black",
                 label="analysis-v2 LB" if i == 0 else None)
    ax1.set_xticks(x, [f"{p} (band {BAND[p]})" for p in ports])
    ax1.set_title("EXP-097 holdout Sharpe LB vs band (red) + analysis-v2 (●)", fontsize=9)
    ax1.legend(fontsize=7)
    ax2.bar(x, ca_lo, color=["steelblue", "seagreen"])
    ax2.axhline(0.0, color="red", ls="--", lw=0.8, label="Calmar band (0)")
    ax2.set_xticks(x, ports)
    ax2.set_title("EXP-097 holdout Calmar LB vs band (0)", fontsize=9)
    ax2.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "holdout_metric_vs_band.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_per_cell_holdout(per_cell: list[dict[str, Any]], shrink: dict[str, Any]) -> None:
    names = [r["cell"] for r in per_cell]
    x = np.arange(len(names))
    ref = {d["cell"]: d for d in shrink.get("per_cell", [])}
    fig, ax = plt.subplots(figsize=(11, 5))
    means = [r["net_mean"] for r in per_cell]
    los = [r["net_ci_low_1s"] for r in per_cell]
    yerr = [max(0.0, m - lo) if np.isfinite(m) and np.isfinite(lo) else 0.0 for m, lo in zip(means, los)]
    colors = ["indianred" if r["net_negative"] else "seagreen" for r in per_cell]
    ax.bar(x - 0.2, means, 0.4, yerr=yerr, capsize=2, color=colors, label="holdout net (mean; whisker=MBB LB)")
    av = [ref.get(n, {}).get("analysis_v2_net_mean", float("nan")) for n in names]
    ax.bar(x + 0.2, av, 0.4, color="gray", alpha=0.7, label="analysis-v2 net mean")
    ax.axhline(0, color="black", lw=0.6)
    ax.set_xticks(x, names, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("net per-event expectancy (ATR)")
    ax.set_title("EXP-097 per-cell holdout net vs analysis-v2 (red = net-negative on holdout)", fontsize=9)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "per_cell_holdout_net.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_drawdown(grid_epochs: np.ndarray, hmask: np.ndarray, res_a: Any, res_b: Any) -> None:
    t = grid_epochs[hmask].astype("datetime64[s]")
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.fill_between(t, -_drawdown(res_a.returns[hmask]), 0, color="steelblue", alpha=0.5, label="A drawdown")
    ax.fill_between(t, -_drawdown(res_b.returns[hmask]), 0, color="seagreen", alpha=0.45,
                    label="B drawdown [primary]")
    ax.set_title("EXP-097 A vs B holdout drawdown (underwater; OOS-final)", fontsize=9)
    ax.set_ylabel("drawdown (negative)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "holdout_drawdown_A_vs_B.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_breaker_timeline(grid_epochs: np.ndarray, hmask: np.ndarray, res_b: Any,
                           streams: list[Any]) -> None:
    t = grid_epochs[hmask].astype("datetime64[s]")
    fragile = [ci for ci, s in enumerate(streams) if s.name in FRAGILE_CELLS]
    fig, ax = plt.subplots(figsize=(9, 4))
    for n, ci in enumerate(fragile):
        allocated = (res_b.weights[hmask, ci] > 0).astype(float)
        ax.plot(t, allocated + 0.02 * n, label=f"{streams[ci].name} allocated", drawstyle="steps-post")
    ax.set_ylim(-0.1, 1.2)
    ax.set_yticks([0, 1], ["broken (0)", "allocated (1)"])
    ax.set_title("EXP-097 Portfolio B circuit-breaker timeline on the holdout (fragile 1h cells)", fontsize=9)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "holdout_circuit_breaker_timeline.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Output writers
# --------------------------------------------------------------------------- #
def write_outputs(res_a: Any, res_b: Any, grid_start: int, n_steps: int, h_global: int, streams: list[Any],
                  metrics: dict[str, dict[str, Any]], confirm_a: bool, confirm_b: bool, g022: str,
                  per_cell: list[dict[str, Any]], shrink: dict[str, Any], src_meta: dict[str, Any],
                  conservation: list[dict[str, Any]]) -> None:
    """Write every headline artifact named in the analysis plan."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    grid_epochs = grid_start + np.arange(n_steps) * STEP_SECONDS
    ts = grid_epochs.astype("datetime64[s]").astype(str)
    in_holdout = (grid_epochs >= h_global).astype(int)
    pl.DataFrame({"timestamp": ts, "net_return": res_a.returns, "in_holdout": in_holdout}).write_csv(
        RESULTS_DIR / "portfolio_returns_A.csv")
    pl.DataFrame({"timestamp": ts, "net_return": res_b.returns, "in_holdout": in_holdout}).write_csv(
        RESULTS_DIR / "portfolio_returns_B.csv")

    pl.DataFrame(per_cell).write_csv(RESULTS_DIR / "per_cell_holdout.csv")
    pl.DataFrame(conservation).write_csv(RESULTS_DIR / "mtm_conservation.csv")

    metric_rows = [{"portfolio": p, **{k: v for k, v in metrics[p].items()}} for p in ("A", "B", "naive_iv")]
    pl.DataFrame(metric_rows, strict=False).write_csv(RESULTS_DIR / "holdout_metrics.csv")

    (RESULTS_DIR / "holdout_boundary.json").write_text(json.dumps(
        {"H_global_epoch": h_global, "H_global": str(np.array(h_global).astype("datetime64[s]")),
         "per_cell": src_meta.get("_H_cells", {}), "n_holdout_weeks": metrics["B"]["n_weeks"]},
        indent=2, default=str))
    (RESULTS_DIR / "verdict.json").write_text(json.dumps({
        "g022_state": g022, "primary": "B", "confirm_B": confirm_b, "confirm_A": confirm_a,
        "no_OR_rescue": "A confirm does NOT promote the family verdict; terminal keys off B",
        "rule": "CONFIRM(P) iff Sharpe_LB(P) > band_P AND Calmar_LB(P) > 0; band_A=1.75, band_B=2.00",
        "B": {"ann_sharpe": metrics["B"]["ann_sharpe"], "ann_sharpe_lo": metrics["B"]["ann_sharpe_lo"],
              "calmar_lo": metrics["B"]["calmar_lo"], "band": BAND["B"]},
        "A": {"ann_sharpe": metrics["A"]["ann_sharpe"], "ann_sharpe_lo": metrics["A"]["ann_sharpe_lo"],
              "calmar_lo": metrics["A"]["calmar_lo"], "band": BAND["A"]}}, indent=2, default=str))
    (RESULTS_DIR / "shrinkage.json").write_text(json.dumps(shrink, indent=2, default=str))


def hash_outputs() -> dict[str, str]:
    """SHA-256 of each headline output (byte-identical second-pass pin)."""
    names = ("portfolio_returns_A.csv", "portfolio_returns_B.csv", "per_cell_holdout.csv",
             "mtm_conservation.csv", "holdout_metrics.csv", "holdout_boundary.json", "verdict.json",
             "shrinkage.json")
    out: dict[str, str] = {}
    for name in names:
        p = RESULTS_DIR / name
        if p.exists():
            out[name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def run() -> dict[str, Any]:
    """The single sanctioned global-holdout release: build the frozen portfolio + adjudicate G-022."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    cells, h_global, src_meta = build_cells_full()
    streams = v2_streams(cells)
    grid_start, n_steps, pnl_mat, trade_mat = E95.build_grid(streams)
    grid_epochs = grid_start + np.arange(n_steps) * STEP_SECONDS
    LOGGER.info("grid: %d hourly steps; H_global=%s; holdout steps=%d", n_steps,
                str(np.array(h_global).astype("datetime64[s]")), int(np.count_nonzero(grid_epochs >= h_global)))

    common = dict(rebalance_steps=REBALANCE_STEPS, lookback_steps=LOOKBACK_STEPS, target_ann_vol=TARGET_ANN_VOL,
                  cap_mult=CAP_MULT, periods_per_year=PERIODS_PER_YEAR_HOURLY, breaker_window=BREAKER_WINDOW,
                  trade_mat=trade_mat)
    res_a = PF.build_portfolio(pnl_mat, grid_start, STEP_SECONDS, use_breaker=False, **common)
    res_b = PF.build_portfolio(pnl_mat, grid_start, STEP_SECONDS, use_breaker=True, **common)
    naive = PF.naive_inverse_vol(pnl_mat, grid_start, STEP_SECONDS, rebalance_steps=REBALANCE_STEPS,
                                 lookback_steps=LOOKBACK_STEPS, target_ann_vol=TARGET_ANN_VOL,
                                 periods_per_year=PERIODS_PER_YEAR_HOURLY, trade_mat=trade_mat)

    metrics = {"A": holdout_metrics(res_a.returns, grid_epochs, h_global, "A"),
               "B": holdout_metrics(res_b.returns, grid_epochs, h_global, "B"),
               "naive_iv": holdout_metrics(naive, grid_epochs, h_global, "naive")}
    confirm_a, confirm_b = confirm(metrics["A"], BAND["A"]), confirm(metrics["B"], BAND["B"])
    g022 = adjudicate_g022(metrics["B"], confirm_b)

    per_cell = per_cell_holdout(cells, h_global)
    shrink = shrinkage(metrics, per_cell)
    conservation = conservation_check(cells)
    causal_weight = causal_weight_holdout(pnl_mat, trade_mat, grid_start, h_global)
    causal_fill = causal_fill_holdout(src_meta, h_global)
    determinism = E95.determinism_replay(streams, grid_start, n_steps, pnl_mat, trade_mat,
                                         {"_res_a": res_a, "_res_b": res_b})
    # determinism of the binding statistic itself (same seed -> identical LB)
    m_b2 = holdout_metrics(res_b.returns, grid_epochs, h_global, "B")
    stat_det = bool(m_b2["ann_sharpe_lo"] == metrics["B"]["ann_sharpe_lo"]
                    and m_b2["calmar_lo"] == metrics["B"]["calmar_lo"])

    make_plots(res_a, res_b, naive, pnl_mat, grid_start, n_steps, h_global, streams, metrics, per_cell, shrink)
    write_outputs(res_a, res_b, grid_start, n_steps, h_global, streams, metrics, confirm_a, confirm_b, g022,
                  per_cell, shrink, src_meta, conservation)
    meta = _build_metadata(metrics, confirm_a, confirm_b, g022, per_cell, shrink, src_meta, grid_start,
                           n_steps, h_global, conservation, causal_weight, causal_fill, determinism, stat_det)
    meta["output_hashes"] = hash_outputs()
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(meta, indent=2, default=str))
    _log_summary(metrics, g022, confirm_a, confirm_b, determinism, stat_det, time.perf_counter() - t0)
    return meta


def _build_metadata(metrics: dict[str, dict[str, Any]], confirm_a: bool, confirm_b: bool, g022: str,
                    per_cell: list[dict[str, Any]], shrink: dict[str, Any], src_meta: dict[str, Any],
                    grid_start: int, n_steps: int, h_global: int, conservation: list[dict[str, Any]],
                    causal_weight: dict[str, Any], causal_fill: dict[str, Any], determinism: dict[str, Any],
                    stat_det: bool) -> dict[str, Any]:
    n_holdout_rows = {k: v["n_holdout_rows"] for k, v in src_meta.items() if isinstance(v, dict)
                      and "n_holdout_rows" in v}
    return {
        "experiment_id": EXPERIMENT_ID, "phase": "022", "family": "CF-MR-001", "hyp": "HYP-003",
        "role": "the single sanctioned global-holdout release (OOS-final deployment confirmation; a la EXP-032)",
        "g022_state": g022, "primary_portfolio": "B", "confirm_B": confirm_b, "confirm_A": confirm_a,
        "confirmation_rule": "CONFIRM(P) iff holdout Sharpe_LB(P) > band_P AND Calmar_LB(P) > 0; "
                             "band_A=1.75, band_B=2.00 (= inherited A4 m*); terminal keys off primary B, no OR",
        "frozen_construction": "G-022a: carry-8 set; binding-v2 noise-aware ERC + intra-1h MTM; LW-90d cov, "
                               "weekly rebalance, 10% vol anchor, 1.5x cap, trailing-50 breaker; v2 fill "
                               "(next-1m-open + 0.05xATR adverse slippage); EXIT-RCT/adverse/cost frozen",
        "generated_utc": datetime.now(timezone.utc).isoformat(), "master_seed": MASTER_SEED,
        "deployable_cells": [f"{i}-{d}" for i, d in CELLS], "surviving_exit": ARM,
        "holdout_metrics": metrics, "per_cell_holdout": per_cell, "shrinkage": shrink,
        "grid_start_epoch": grid_start, "n_grid_steps": n_steps, "H_global_epoch": h_global,
        "n_holdout_weeks": metrics["B"]["n_weeks"], "n_holdout_rows_per_file": n_holdout_rows,
        "mtm_conservation_pass": all(r["PASS"] for r in conservation),
        "causal_weight_assertion": causal_weight, "causal_entry_fill_assertion": causal_fill,
        "determinism": determinism, "binding_statistic_determinism": stat_det,
        "n_boot": N_BOOT, "boot_alpha": BOOT_ALPHA,
        "real_prices_only": True,
        "global_holdout_shot_spent": True, "holdout_first_touch": EXPERIMENT_ID, "holdout_untouched": False,
        "counted_test_reads": 0, "candidate_slots": 0,
        "read_accounting": ("the single sanctioned global-holdout release (one holdout-governance event, a la "
                            "EXP-032); outside the analysis-TEST 48-stratum ledger (11 carried strata stay 1/2); "
                            "both A and B from ONE materialization = ONE read (operator decision 2026-06-25); "
                            "non-repeatable, non-upgradable"),
        "source_meta": {k: v for k, v in src_meta.items() if not k.startswith("_")},
    }


def _log_summary(metrics: dict[str, dict[str, Any]], g022: str, confirm_a: bool, confirm_b: bool,
                 determinism: dict[str, Any], stat_det: bool, secs: float) -> None:
    b, a = metrics["B"], metrics["A"]
    LOGGER.info("EXP-097 done in %.1fs | G-022 = %s", secs, g022)
    LOGGER.info("  B [primary]: Sharpe %.3f (lo %.3f) Calmar_lo %.3f band %.2f -> CONFIRM=%s",
                b["ann_sharpe"], b["ann_sharpe_lo"], b["calmar_lo"], BAND["B"], confirm_b)
    LOGGER.info("  A [disclosed]: Sharpe %.3f (lo %.3f) Calmar_lo %.3f band %.2f -> CONFIRM=%s",
                a["ann_sharpe"], a["ann_sharpe_lo"], a["calmar_lo"], BAND["A"], confirm_a)
    LOGGER.info("  determinism=%s stat_determinism=%s holdout_shot_spent=True counted_reads=0",
                determinism["determinism_pass"], stat_det)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    argparse.ArgumentParser(description="EXP-097 global-holdout release (single sanctioned shot)").parse_args()
    meta = run()
    b = meta["holdout_metrics"]["B"]
    print(f"EXP-097 complete | G-022 = {meta['g022_state']} | "
          f"B [primary] Sharpe={b['ann_sharpe']:.3f} (lo {b['ann_sharpe_lo']:.3f}) Calmar_lo={b['calmar_lo']:.3f} "
          f"vs band {BAND['B']} -> CONFIRM={meta['confirm_B']} | confirm_A={meta['confirm_A']} | "
          f"determinism={meta['determinism']['determinism_pass']} holdout_shot_spent={meta['global_holdout_shot_spent']} "
          f"counted_reads={meta['counted_test_reads']}")


if __name__ == "__main__":
    main()
