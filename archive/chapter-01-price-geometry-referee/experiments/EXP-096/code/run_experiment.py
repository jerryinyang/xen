"""EXP-096 — Noise Infusion: Realistic 1-Minute Entry Fill (RSI-2 Fade Portfolio, 8 confirmed cells).

Phase 022 / ``CF-MR-001`` / HYP-003 — the fill-realism leg. Governing design/D0/amendment:
``docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/`` (``design.md`` §3-4 EXP-096,
``D0-predeclarations.md`` §D1/§D5/§D7/§D9, ``D0-amendment-001.md`` A1-A4). Analysis-plan: ``analysis-plan.md``.

What this is. Re-resolve each of the 8 G-021-confirmed cells' **entries** under a realistic 1-minute entry-fill
model (v1 next-1m-open / v2 BINDING +0.05xATR adverse slippage / v3 worst-of-next-3) and re-derive the causal
ERC portfolio (static A / circuit-breaker B) under the binding v2 with intra-1h mark-to-market. Does the EXP-095
diversification benefit survive realistic execution? Analysis-set only (TRAIN + the EXP-093 already-resolved
analysis-TEST series reused as portfolio-aggregate disclosure); **0 counted TEST reads, 0 candidate slots,
final-30% global holdout NEVER loaded**. No binding holdout verdict is issued here.

Pure entry-leg perturbation (the structural fact). Under D0 §D5 only the entry execution price changes. The
EXIT-RCT target level and the adverse stop are built from the signal-bar close and are FROZEN, so the resolved
exit path (exit fill, kind, exit index, atr, keep mask) is IDENTICAL to EXP-093 and is reused verbatim — the exit
is resolved once and never perturbed. Only ``entry_fill`` changes: net = direction*(exit_fill - entry_fill)/atr -
cost. The flat round-trip cost (D0-amendment-003) is retained and is NOT double-counted by the slippage (cost
models spread/commission; the slippage is on the fill price). The realized-event population (keep mask) is
unchanged because the exit resolution is unchanged.

Reuse (verbatim). The EXP-095 module is imported and its frozen construction is reused unchanged: the EXP-090
substrate (``build_cell_context``, the EXIT-RCT arm, ``resolve_exit_paths``/``net_return_atr``), the EXP-092/093
cost overlay (``D0-amendment-003``), ``xen.portfolio`` (ERC/Ledoit-Wolf/vol-anchor/cap/breaker/intra-1h MTM/
moving-block bootstrap), and the EXP-095 helpers (``mtm_marks``, ``series_risk_metrics``, ``portfolio_block``,
``build_grid``, ``reconcile_provenance``, the causal/determinism assertions). The ONLY new code is the causal
entry-side fill (``xen.intrabar_fill.resolve_entry_fills``). The gate statistic m* (1.75 A / 2.00 B) is INHERITED
from EXP-095 (not recomputed under noise); only the realized v2 edge-vs-m* margin is re-reported.
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
from xen.intrabar_fill import net_return_atr, resolve_entry_fills  # noqa: E402
from xen.referee_calibration import seed_for  # noqa: E402
from xen import portfolio as pf  # noqa: E402

# --------------------------------------------------------------------------- #
# Path setup + EXP-095 reuse (import the validated predecessor module directly)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-096"
CODE_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = CODE_DIR.parent
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
EXP_ROOT = EXPERIMENT_DIR.parent
EXP095_CODE = EXP_ROOT / "EXP-095" / "code" / "run_experiment.py"
EXP093_TEST_PER_CELL = EXP_ROOT / "EXP-093" / "results" / "test_per_cell.csv"


def _load_exp095() -> Any:
    """Import the validated EXP-095 module (import-safe: ``main`` guarded; reuses its frozen build)."""
    if not EXP095_CODE.exists():
        raise FileNotFoundError(f"EXP-095 module missing: {EXP095_CODE}")
    spec = importlib.util.spec_from_file_location("exp095_mr_portfolio", EXP095_CODE)
    if spec is None or spec.loader is None:                       # pragma: no cover - defensive
        raise ImportError(f"Could not load EXP-095 from {EXP095_CODE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


E95 = _load_exp095()                                             # reuses E95.E90 (substrate), E95.pf, helpers
E90 = E95.E90

# --------------------------------------------------------------------------- #
# Constants (inherited from EXP-095 / frozen D0; the noise model adds §D5 params)
# --------------------------------------------------------------------------- #
MASTER_SEED = E95.MASTER_SEED                                     # 20260624
ARM = E95.ARM                                                     # EXIT-RCT
CELLS = E95.CELLS                                                 # the 8 G-021-confirmed cells
MR_COST_RT_BPS = E95.MR_COST_RT_BPS
FIN_BPS_DAY = E95.FIN_BPS_DAY                                     # 0.0
STEP_SECONDS = E95.STEP_SECONDS
SECONDS_PER_YEAR = E95.SECONDS_PER_YEAR
N_BOOT = E95.N_BOOT                                               # 10_000 (all variants, comparable ladder)
CAL_N_BOOT = E95.CAL_N_BOOT
N_NULL = E95.N_NULL                                              # FPR sanity replicates (disclosure)
BOOT_ALPHA = E95.BOOT_ALPHA                                       # 0.10 -> one-sided 95% lower bound
FPR_TARGET = E95.FPR_TARGET
PROVENANCE_TOL = E95.PROVENANCE_TOL
REBALANCE_STEPS = E95.REBALANCE_STEPS
LOOKBACK_STEPS = E95.LOOKBACK_STEPS
TARGET_ANN_VOL = E95.TARGET_ANN_VOL
CAP_MULT = E95.CAP_MULT
BREAKER_WINDOW = E95.BREAKER_WINDOW
CADENCE_STEPS = E95.CADENCE_STEPS
PERIODS_PER_YEAR_CADENCE = E95.PERIODS_PER_YEAR_CADENCE

# Noise / entry-fill model (D0 §D5 / param #8). Frozen; v2 is BINDING; brackets are disclosure.
SLIPPAGE_ATR = 0.05                                               # v2 adverse slippage (ATR units)
K_WORST = 3                                                       # v3 worst-of-next-k 1m bars
VARIANTS: tuple[str, ...] = ("ideal", "v1", "v2", "v3")          # ideal = EXP-095 at-close (overlay/provenance)
BINDING_VARIANT = "v2"
LADDER_VARIANTS: tuple[str, ...] = ("v1", "v2", "v3")
FRAGILE_CELLS = ("USTEC-1h", "US2000-1h")

# Inherited MDE m* (EXP-095 A4 — NOT recomputed under noise; operator decision 2026-06-25).
M_STAR_INHERITED: dict[str, float] = {"A": 1.75, "B": 2.00}
COV_BRACKET_DAYS = (60, 90, 120)                                  # disclosure-only nuisance bracket

LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# Dataclasses / types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class NoiseCell:
    """One cell resolved once, with per-variant entry-fill streams + per-variant per-event expectancy."""

    name: str
    streams: dict[str, pf.CellStream]            # variant -> resolved trade+MTM stream
    expectancy: dict[str, dict[str, float]]      # variant -> {net_mean, net_median, net_ci_low_1s, n}
    test_net_mean: float                         # idealized analysis-TEST stats (provenance vs EXP-093)
    test_net_median: float
    test_n_resolved: int
    test_resolved_frac: float
    keep_count: int                              # resolved-event count (keep-mask invariance vs EXP-093)
    n_entry_unavailable_on_keep: int             # kept events with no in-fence post-signal 1m bar (expect 0)
    entry_audit: dict[str, float]                # mean adverse entry gap (ATR) vs signal close, per variant


# --------------------------------------------------------------------------- #
# I/O helpers
# --------------------------------------------------------------------------- #
def load_exp093_margins() -> dict[str, float]:
    """Per-cell EXP-093 margin (the NOISE_DEGRADED flag threshold) from ``test_per_cell.csv``."""
    if not EXP093_TEST_PER_CELL.exists():
        raise FileNotFoundError(f"missing EXP-093 margins: {EXP093_TEST_PER_CELL}")
    return {r["cell"]: float(r["margin"]) for r in pl.read_csv(EXP093_TEST_PER_CELL).iter_rows(named=True)}


# --------------------------------------------------------------------------- #
# Pure computation — per-cell entry-fill re-resolution (exit reused verbatim)
# --------------------------------------------------------------------------- #
def _per_event_expectancy(net: np.ndarray, rng: np.random.Generator) -> dict[str, float]:
    """Per-cell net per-event expectancy: mean, median, one-sided 95% MBB lower bound (alpha=0.05)."""
    x = np.asarray(net, dtype=np.float64)
    x = x[np.isfinite(x)]
    if x.shape[0] < 2:
        return {"net_mean": float("nan"), "net_median": float("nan"),
                "net_ci_low_1s": float("nan"), "n": int(x.shape[0])}
    ci = moving_block_bootstrap_cis(x, rng, n_boot=N_BOOT, alpha=BOOT_ALPHA)
    return {"net_mean": float(x.mean()), "net_median": float(np.median(x)),
            "net_ci_low_1s": float(ci.expectancy_lo), "n": int(x.shape[0])}


def resolve_cell_noise(ctx: Any, ts_lo_epoch: int, instrument: str, domain: str) -> NoiseCell:
    """Resolve EXIT-RCT once, then apply the entry-fill ladder (ideal/v1/v2/v3) as a pure entry-leg perturbation.

    The exit path (``res.fill_price``/index/keep) is resolved once and reused for every variant. The entry
    execution price is the only thing that changes; ``net = direction*(exit_fill - entry_fill)/atr - cost``
    with the cost notional pinned to the signal-bar close (so cost is identical to EXP-093 — not
    double-counted with the slippage). The intra-1h MTM books the first increment from each variant's
    ``entry_fill`` so Sigma(marks) == that variant's realized net (amendment-001 A1 conservation).
    """
    idx = ctx.core_entry_idx
    direction = ctx.core_direction
    res = E90.resolve_arm(ctx, idx, direction, ARM, ctx.minute_high, ctx.minute_low, ctx.minute_open)
    p_entry, atr_entry = ctx.close[idx], ctx.atr[idx]
    hd = holding_days(idx, res.exit_domain_idx, E90.DOMAINS[domain])

    # keep mask = EXP-093/095 idealized mask (entry_close); identical across variants (exit is frozen).
    gross_ideal = net_return_atr(res.fill_price, p_entry, direction, atr_entry)
    keep = (res.resolved & np.isfinite(gross_ideal) & np.isfinite(atr_entry) & (atr_entry > 0.0)
            & np.isfinite(hd) & (hd >= 0.0))

    # Entry fills (the only new computation); ideal = signal-bar close (EXP-095 at-close).
    entry_epoch = ctx.domain_close_epoch[idx].astype(np.int64)
    ef = resolve_entry_fills(
        ctx.minute_open, ctx.minute_high, ctx.minute_low, ctx.minute_close_epoch,
        entry_epoch, direction, atr_entry, ctx.train_edge_epoch, k_worst=K_WORST, slippage_atr=SLIPPAGE_ATR)
    n_unavail_keep = int(np.count_nonzero(keep & ~ef.available))   # must be 0 (keep-mask invariance)
    entry_px = {"ideal": p_entry, "v1": ef.fill_v1, "v2": ef.fill_v2, "v3": ef.fill_v3}

    safe_exit = np.clip(res.exit_domain_idx, 0, ctx.n_domain - 1)
    exit_epoch = np.where(res.exit_domain_idx >= 0, ctx.domain_close_epoch[safe_exit], -1).astype(np.int64)
    name = f"{instrument}-{domain}"
    rt_bps = MR_COST_RT_BPS[instrument]

    streams: dict[str, pf.CellStream] = {}
    expectancy: dict[str, dict[str, float]] = {}
    net_by_variant: dict[str, np.ndarray] = {}
    for v in VARIANTS:
        gross_v = net_return_atr(res.fill_price, entry_px[v], direction, atr_entry)
        net_all = np.full(idx.shape[0], np.nan, dtype=np.float64)
        if np.any(keep):
            # cost notional pinned to the signal-bar close (identical to EXP-093; slippage is in entry_fill)
            costs = event_costs(gross_v[keep], p_entry[keep], atr_entry[keep], hd[keep],
                                rt_bps=rt_bps, fin_bps_day=FIN_BPS_DAY)
            net_all[keep] = costs.net
        net_by_variant[v] = net_all
        mark_epoch, mark_return = E95.mtm_marks(
            entry_epoch[keep], exit_epoch[keep], entry_px[v][keep], atr_entry[keep], direction[keep],
            res.fill_price[keep], net_all[keep], ctx.minute_open, ctx.minute_close_epoch, STEP_SECONDS)
        streams[v] = pf.CellStream(name=name, entry_epoch=entry_epoch[keep], exit_epoch=exit_epoch[keep],
                                   net=net_all[keep], mark_epoch=mark_epoch, mark_return=mark_return)
        rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "expectancy", v, name))
        expectancy[v] = _per_event_expectancy(net_all[keep], rng)

    # Provenance: idealized analysis-TEST subset (entry domain CloseTime >= ts_lo) vs EXP-093.
    test_mask = entry_epoch >= ts_lo_epoch
    resolved_frac = float(np.mean(res.resolved[test_mask])) if np.any(test_mask) else float("nan")
    kt = keep & test_mask
    n_res = int(np.count_nonzero(kt))
    ideal_net = net_by_variant["ideal"]
    t_mean = float(np.mean(ideal_net[kt])) if n_res else float("nan")
    t_median = float(np.median(ideal_net[kt])) if n_res else float("nan")
    # Entry-fill audit: mean adverse entry gap (ATR) vs the signal close, per variant (positive = worse).
    dk, atr_k, close_k = direction[keep].astype(np.float64), atr_entry[keep], p_entry[keep]
    entry_audit: dict[str, float] = {}
    for v in VARIANTS:
        gap = dk * (entry_px[v][keep] - close_k) / atr_k
        gap = gap[np.isfinite(gap)]
        entry_audit[f"{v}_mean_adverse_gap_atr"] = float(gap.mean()) if gap.shape[0] else float("nan")
    return NoiseCell(name=name, streams=streams, expectancy=expectancy, test_net_mean=t_mean,
                     test_net_median=t_median, test_n_resolved=n_res, test_resolved_frac=resolved_frac,
                     keep_count=int(np.count_nonzero(keep)), n_entry_unavailable_on_keep=n_unavail_keep,
                     entry_audit=entry_audit)


# --------------------------------------------------------------------------- #
# Pure computation — disclosure: optional synthetic-null FPR sanity on the v2 series (NOT a re-gate)
# --------------------------------------------------------------------------- #
def fpr_sanity(trade_mat: np.ndarray, grid_start: int, holdout_equiv_steps: int, use_breaker: bool,
               label: str) -> dict[str, Any]:
    """Disclosure-only: synthetic-null FPR of the Sharpe lower-bound rule on the v2 trade matrix.

    Null = block-permute the common time index to ``holdout_equiv_steps`` rows, zero each column
    (``block_permute_zero_mean`` / ``null_b_block_permute_returns`` form; NOT a path rotation; NOT built
    around any signal-derived target). The MDE-curve is **NOT** recomputed (m* inherited from EXP-095);
    this only confirms noise did not break FPR control. Mirrors the FPR leg of EXP-095's calibrator.
    """
    block = REBALANCE_STEPS
    n_weeks_cal = max(2, int(np.ceil(holdout_equiv_steps / CADENCE_STEPS)))
    weekly_block = default_block_length(n_weeks_cal)
    null_fire = np.zeros(N_NULL, dtype=bool)
    for i in tqdm(range(N_NULL), desc=f"FPR sanity [{label}]", unit="rep", dynamic_ncols=True):
        perm_rng = np.random.default_rng(seed_for(EXPERIMENT_ID, label, "null", i))
        r_null = pf.block_permute_zero_mean(trade_mat, perm_rng, block=block, n_out=holdout_equiv_steps)
        res = pf.build_portfolio(
            r_null, grid_start, STEP_SECONDS, rebalance_steps=REBALANCE_STEPS, lookback_steps=LOOKBACK_STEPS,
            target_ann_vol=TARGET_ANN_VOL, cap_mult=CAP_MULT, periods_per_year=E95.PERIODS_PER_YEAR_HOURLY,
            use_breaker=use_breaker, breaker_window=BREAKER_WINDOW)
        weekly = pf.aggregate_to_cadence(res.returns, CADENCE_STEPS)
        boot_rng = np.random.default_rng(seed_for(EXPERIMENT_ID, label, "boot", i))
        mean_r, sd_r = pf.moving_block_boot_components(weekly, boot_rng, n_boot=CAL_N_BOOT, block=weekly_block)
        lo = pf.sharpe_lower_bound_shift(mean_r, sd_r, 0.0, PERIODS_PER_YEAR_CADENCE, BOOT_ALPHA)
        null_fire[i] = bool(np.isfinite(lo) and lo > 0.0)
    fpr = float(np.mean(null_fire))
    return {"portfolio": label, "n_null": N_NULL, "fpr": fpr, "fpr_wilson_hi": pf.wilson_upper(fpr, N_NULL),
            "fpr_controlled": bool(fpr <= FPR_TARGET), "note": "DISCLOSURE only; m* inherited from EXP-095"}


# --------------------------------------------------------------------------- #
# Pure computation — causal entry-fill assertion (perturbing a PRE-signal 1m bar is inert)
# --------------------------------------------------------------------------- #
def causal_entry_fill_assertion(ctx: Any) -> dict[str, Any]:
    """Perturb a 1-minute bar strictly BEFORE an event's signal close; assert its entry fills are unchanged.

    A pre-signal bar entering a post-signal entry fill would be look-ahead; this fails loudly.
    """
    idx = ctx.core_entry_idx
    direction = ctx.core_direction
    atr_entry = ctx.atr[idx]
    entry_epoch = ctx.domain_close_epoch[idx].astype(np.int64)
    base = resolve_entry_fills(ctx.minute_open, ctx.minute_high, ctx.minute_low, ctx.minute_close_epoch,
                               entry_epoch, direction, atr_entry, ctx.train_edge_epoch,
                               k_worst=K_WORST, slippage_atr=SLIPPAGE_ATR)
    # choose an event with a strictly-earlier 1m bar to perturb
    j = next((k for k in range(idx.shape[0]) if int(np.searchsorted(
        ctx.minute_close_epoch, entry_epoch[k], side="right")) >= 1), None)
    if j is None:
        return {"causal_entry_fill_pass": True, "note": "no perturbable pre-signal bar found"}
    first = int(np.searchsorted(ctx.minute_close_epoch, entry_epoch[j], side="right"))
    mo, mh, ml = ctx.minute_open.copy(), ctx.minute_high.copy(), ctx.minute_low.copy()
    mo[:first] += 13.0                                            # arbitrary large perturbation strictly before
    mh[:first] += 13.0
    ml[:first] += 13.0
    pert = resolve_entry_fills(mo, mh, ml, ctx.minute_close_epoch, entry_epoch, direction, atr_entry,
                               ctx.train_edge_epoch, k_worst=K_WORST, slippage_atr=SLIPPAGE_ATR)
    same = (np.array_equal(base.fill_v1[j], pert.fill_v1[j], equal_nan=True)
            and np.array_equal(base.fill_v2[j], pert.fill_v2[j], equal_nan=True)
            and np.array_equal(base.fill_v3[j], pert.fill_v3[j], equal_nan=True))
    if not same:
        raise RuntimeError("CAUSALITY VIOLATION: a pre-signal 1m bar changed a post-signal entry fill")
    return {"causal_entry_fill_pass": bool(same), "event_tested": int(j), "first_post_signal_idx": first}


# --------------------------------------------------------------------------- #
# Orchestration — build streams, per-variant portfolios, the noise ladder
# --------------------------------------------------------------------------- #
def build_cells() -> tuple[list[NoiseCell], dict[str, Any], dict[str, Any]]:
    """Resolve all 8 cells (exit once + entry-fill ladder); return cells + source meta + a causal sample."""
    files, _ = E90.VAL005.discover_infr003_files()
    files = {k.upper(): v for k, v in files.items()}
    cells: list[NoiseCell] = []
    src_meta: dict[str, Any] = {}
    causal_sample: dict[str, Any] = {}
    for instrument, domain in tqdm(CELLS, desc="resolve cells", unit="cell", dynamic_ncols=True):
        if instrument not in files:
            raise FileNotFoundError(f"no INFR-003 file for {instrument}")
        analysis_1m, ts_lo, meta = E95.load_analysis_1m(instrument, files[instrument])
        ctx, _dropped, status = E90.build_cell_context(analysis_1m, instrument, domain)
        if ctx is None:
            raise RuntimeError(f"{instrument}-{domain}: failed to build ({status})")
        if not causal_sample:                                    # one causal-fill check is sufficient
            causal_sample = causal_entry_fill_assertion(ctx)
        cells.append(resolve_cell_noise(ctx, ts_lo, instrument, domain))
        src_meta[f"{instrument}-{domain}"] = meta
    return cells, src_meta, causal_sample


def reconcile_provenance(cells: list[NoiseCell]) -> list[dict[str, Any]]:
    """Reconcile the idealized analysis-TEST per-cell summary to EXP-093 (reuse EXP-095's gate)."""
    proxies = [E95.CellResolution(name=c.name, stream=c.streams["ideal"], test_net_mean=c.test_net_mean,
                                  test_net_median=c.test_net_median, test_n_resolved=c.test_n_resolved,
                                  test_resolved_frac=c.test_resolved_frac) for c in cells]
    return E95.reconcile_provenance(proxies)


def variant_block(cells: list[NoiseCell], variant: str, n_boot: int) -> dict[str, Any]:
    """Build the full portfolio block (A/B/naive/per-cell/benefit) for one entry-fill variant."""
    streams = [c.streams[variant] for c in cells]
    grid_start, n_steps, pnl_mat, trade_mat = E95.build_grid(streams)
    block = E95.portfolio_block(pnl_mat, trade_mat, grid_start, streams, f"noise_{variant}", n_boot=n_boot)
    block.update({"_grid_start": grid_start, "_n_steps": n_steps, "_pnl_mat": pnl_mat,
                  "_trade_mat": trade_mat, "_streams": streams})
    return block


def conservation_check(cells: list[NoiseCell]) -> list[dict[str, Any]]:
    """Binding MTM conservation: Sigma(marks) == realized net per cell under the binding v2 (<=1e-9 ATR)."""
    rows: list[dict[str, Any]] = []
    for c in cells:
        s = c.streams[BINDING_VARIANT]
        sum_marks = float(np.sum(s.mark_return)) if s.mark_return.shape[0] else 0.0
        sum_net = float(np.sum(s.net[np.isfinite(s.net)]))
        diff = abs(sum_marks - sum_net)
        rows.append({"cell": c.name, "sum_marks": sum_marks, "sum_net": sum_net, "abs_diff": diff,
                     "PASS": bool(diff <= 1e-9)})
    failures = [r["cell"] for r in rows if not r["PASS"]]
    if failures:
        raise RuntimeError(f"MTM conservation failed (v2): {failures}")
    return rows


def noise_ladder(blocks: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Portfolio A/B Sharpe LB + Calmar LB across the v1/v2/v3 ladder (+ cross-cell-median baselines)."""
    rows: list[dict[str, Any]] = []
    for v in LADDER_VARIANTS:
        b = blocks[v]
        ben = b["benefit"]
        for port in ("A", "B"):
            rows.append({"variant": v, "portfolio": port, "ann_sharpe": b[port]["ann_sharpe"],
                         "ann_sharpe_lo": b[port]["ann_sharpe_lo"], "calmar": b[port]["calmar"],
                         "calmar_lo": b[port]["calmar_lo"], "max_drawdown": b[port]["max_drawdown"],
                         "ulcer": b[port]["ulcer"],
                         "median_cell_sharpe_lo": ben["median_cell_sharpe_lo"],
                         "median_cell_calmar_lo": ben["median_cell_calmar_lo"],
                         "sharpe_benefit": b[port + "_sharpe_benefit_margin"],
                         "calmar_benefit": b[port + "_calmar_benefit_margin"]})
    return rows


def attach_benefit_margins(block: dict[str, Any]) -> None:
    """Lift the A/B Sharpe+Calmar benefit margins to top-level keys for the ladder table."""
    ben = block["benefit"]
    for port in ("A", "B"):
        block[f"{port}_sharpe_benefit_margin"] = ben[f"{port}_sharpe"]["margin"]
        block[f"{port}_calmar_benefit_margin"] = ben[f"{port}_calmar"]["margin"]


def per_cell_degradation(cells: list[NoiseCell], margins: dict[str, float]) -> list[dict[str, Any]]:
    """Per-cell net expectancy ladder (ideal->v1->v2->v3) + NOISE_DEGRADED flag (v2 LB < margin; FLAG only)."""
    rows: list[dict[str, Any]] = []
    for c in cells:
        margin = margins.get(c.name, float("nan"))
        row: dict[str, Any] = {"cell": c.name, "margin": margin}
        for v in VARIANTS:
            e = c.expectancy[v]
            row[f"{v}_net_mean"] = e["net_mean"]
            row[f"{v}_net_median"] = e["net_median"]
            row[f"{v}_net_ci_low_1s"] = e["net_ci_low_1s"]
        row["n"] = c.expectancy["v2"]["n"]
        v2_lo = c.expectancy["v2"]["net_ci_low_1s"]
        row["noise_degraded"] = bool(np.isfinite(v2_lo) and np.isfinite(margin) and v2_lo < margin)
        rows.append(row)
    return rows


def gate_recheck(block_v2: dict[str, Any]) -> dict[str, Any]:
    """Re-report the realized v2 portfolio Sharpe LB vs the INHERITED EXP-095 m* (no MDE recompute)."""
    out: dict[str, Any] = {"m_star_source": "EXP-095 A4 MDE-curve (inherited; NOT recomputed under noise)"}
    any_clears = False
    for port in ("A", "B"):
        lo = float(block_v2[port]["ann_sharpe_lo"])
        m = M_STAR_INHERITED[port]
        clears = bool(np.isfinite(lo) and lo >= m)
        any_clears = any_clears or clears
        out[port] = {"m_star": m, "v2_sharpe_lo": lo, "edge_vs_mstar": lo - m if np.isfinite(lo) else float("nan"),
                     "clears_inherited_mde": clears}
    out["statistic_clearable_under_noise"] = any_clears
    out["routing"] = (">=1 portfolio clears m* -> band >= m* still detectable under noise"
                      if any_clears else "both below m* -> FLAG G-022a band/scale reconsideration")
    return out


def adaptability(block_v2: dict[str, Any], cells: list[NoiseCell]) -> dict[str, Any]:
    """A vs B under v2: A-B Sharpe/MaxDD/Ulcer + circuit-breaker de-allocation % on the fragile cells."""
    a, b = block_v2["A"], block_v2["B"]
    res_b = block_v2["_res_b"]
    streams = block_v2["_streams"]
    dealloc: dict[str, float] = {}
    for ci, s in enumerate(streams):
        if s.name in FRAGILE_CELLS:
            w = res_b.weights[:, ci]
            active = w != 0.0
            dealloc[s.name] = float(np.mean(~active)) if active.shape[0] else float("nan")
    return {"d_sharpe_lo_A_minus_B": a["ann_sharpe_lo"] - b["ann_sharpe_lo"],
            "d_maxdd_A_minus_B": a["max_drawdown"] - b["max_drawdown"],
            "d_ulcer_A_minus_B": a["ulcer"] - b["ulcer"],
            "A_sharpe_lo": a["ann_sharpe_lo"], "B_sharpe_lo": b["ann_sharpe_lo"],
            "A_maxdd": a["max_drawdown"], "B_maxdd": b["max_drawdown"],
            "A_ulcer": a["ulcer"], "B_ulcer": b["ulcer"],
            "fragile_cell_dealloc_fraction": dealloc}


def cov_bracket_v2(block_v2: dict[str, Any]) -> dict[str, float]:
    """Disclosed nuisance bracket (NEVER selection): v2 Portfolio-A Sharpe at cov windows {60,90,120} days."""
    pnl_mat, trade_mat, grid_start = block_v2["_pnl_mat"], block_v2["_trade_mat"], block_v2["_grid_start"]
    out: dict[str, float] = {}
    for days in COV_BRACKET_DAYS:
        res = pf.build_portfolio(
            pnl_mat, grid_start, STEP_SECONDS, rebalance_steps=REBALANCE_STEPS, lookback_steps=days * 24,
            target_ann_vol=TARGET_ANN_VOL, cap_mult=CAP_MULT, periods_per_year=E95.PERIODS_PER_YEAR_HOURLY,
            use_breaker=False, breaker_window=BREAKER_WINDOW, trade_mat=trade_mat)
        weekly = pf.aggregate_to_cadence(res.returns, CADENCE_STEPS)
        out[f"cov_{days}d"] = pf.annualized_sharpe(weekly, PERIODS_PER_YEAR_CADENCE)
    return out


# --------------------------------------------------------------------------- #
# Plotting (5 bounded plots; reuse collected series — no reloads)
# --------------------------------------------------------------------------- #
def make_plots(blocks: dict[str, dict[str, Any]], ladder: list[dict[str, Any]],
               degradation: list[dict[str, Any]], gate: dict[str, Any]) -> None:
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    _plot_noise_ladder(ladder, blocks[BINDING_VARIANT], gate)
    _plot_equity_v2(blocks)
    _plot_degradation(degradation)
    _plot_breaker_timeline(blocks[BINDING_VARIANT])
    _plot_drawdown_ab(blocks[BINDING_VARIANT])


def _equity(returns: np.ndarray) -> np.ndarray:
    return np.cumsum(np.asarray(returns, dtype=np.float64))


def _plot_noise_ladder(ladder: list[dict[str, Any]], block_v2: dict[str, Any], gate: dict[str, Any]) -> None:
    order = {v: i for i, v in enumerate(LADDER_VARIANTS)}
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8))
    for port, color in (("A", "steelblue"), ("B", "seagreen")):
        xs = [order[r["variant"]] for r in ladder if r["portfolio"] == port]
        sh = [r["ann_sharpe_lo"] for r in ladder if r["portfolio"] == port]
        ca = [r["calmar_lo"] for r in ladder if r["portfolio"] == port]
        ax1.plot(xs, sh, marker="o", color=color, label=f"{port} Sharpe LB")
        ax2.plot(xs, ca, marker="o", color=color, label=f"{port} Calmar LB")
    base_sh = block_v2["benefit"]["median_cell_sharpe_lo"]
    base_ca = block_v2["benefit"]["median_cell_calmar_lo"]
    ax1.axhline(base_sh, color="gray", ls="--", lw=0.9, label=f"median-cell Sharpe LB ({base_sh:.2f})")
    for port, color in (("A", "steelblue"), ("B", "seagreen")):
        ax1.axhline(M_STAR_INHERITED[port], color=color, ls=":", lw=0.8,
                    label=f"m* {port} ({M_STAR_INHERITED[port]:.2f})")
    ax2.axhline(base_ca, color="gray", ls="--", lw=0.9, label=f"median-cell Calmar LB ({base_ca:.2f})")
    for ax, ttl in ((ax1, "Sharpe LB"), (ax2, "Calmar LB")):
        ax.set_xticks(list(order.values()), list(order.keys()))
        ax.set_xlabel("entry-fill variant")
        ax.set_title(f"EXP-096 noise ladder — portfolio {ttl}", fontsize=9)
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "noise_sensitivity_ladder.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_equity_v2(blocks: dict[str, dict[str, Any]]) -> None:
    b2 = blocks[BINDING_VARIANT]
    grid_epochs = b2["_grid_start"] + np.arange(b2["_n_steps"]) * STEP_SECONDS
    t = grid_epochs.astype("datetime64[s]")
    streams = b2["_streams"]
    best_name = b2["best_cell_name"]
    best_col = next((ci for ci, s in enumerate(streams) if s.name == best_name), 0)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(t, _equity(b2["_res_a"].returns), label="A (static ERC) v2", color="steelblue")
    ax.plot(t, _equity(b2["_res_b"].returns), label="B (ERC+breaker) v2", color="seagreen")
    ax.plot(t, _equity(b2["_naive"]), label="naive inverse-vol v2", color="gray", lw=0.9, ls="--")
    ax.plot(t, _equity(b2["_pnl_mat"][:, best_col]), label=f"best cell ({best_name}) v2",
            color="indianred", lw=0.9, ls=":")
    ideal = blocks["ideal"]
    ti = ideal["_grid_start"] + np.arange(ideal["_n_steps"]) * STEP_SECONDS
    ax.plot(ti.astype("datetime64[s]"), _equity(ideal["_res_a"].returns),
            label="A idealized (EXP-095 at-close)", color="black", lw=0.8, alpha=0.6)
    ax.axhline(0, color="black", lw=0.5)
    ax.set_title("EXP-096 analysis-set equity curves under binding v2 (vs idealized overlay)", fontsize=9)
    ax.set_ylabel("cumulative net return")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "equity_curves_v2.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_degradation(degradation: list[dict[str, Any]]) -> None:
    names = [r["cell"] for r in degradation]
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(11, 5))
    width = 0.2
    for k, (v, color) in enumerate(zip(VARIANTS, ("black", "steelblue", "darkorange", "indianred"))):
        means = [r[f"{v}_net_mean"] for r in degradation]
        los = [r[f"{v}_net_ci_low_1s"] for r in degradation]
        yerr = [max(0.0, m - lo) if np.isfinite(m) and np.isfinite(lo) else 0.0
                for m, lo in zip(means, los)]
        ax.bar(x + (k - 1.5) * width, means, width, yerr=yerr, capsize=2, label=v, color=color, alpha=0.85)
    for i, r in enumerate(degradation):                           # per-cell margin tick + flag highlight
        ax.plot([x[i] - 2 * width, x[i] + 2 * width], [r["margin"], r["margin"]], color="red", lw=1.0)
        if r["noise_degraded"]:
            ax.annotate("flag", (x[i], r["margin"]), fontsize=7, color="red", ha="center", va="bottom")
    ax.axhline(0, color="black", lw=0.6)
    ax.set_xticks(x, names, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("net per-event expectancy (ATR; bar=mean, whisker=MBB LB)")
    ax.set_title("EXP-096 per-cell net-expectancy degradation (ideal->v1->v2->v3; red=EXP-093 margin)",
                 fontsize=9)
    ax.legend(fontsize=8, title="variant")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "per_cell_degradation.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_breaker_timeline(block_v2: dict[str, Any]) -> None:
    grid_epochs = block_v2["_grid_start"] + np.arange(block_v2["_n_steps"]) * STEP_SECONDS
    t = grid_epochs.astype("datetime64[s]")
    res_b = block_v2["_res_b"]
    streams = block_v2["_streams"]
    fragile = [ci for ci, s in enumerate(streams) if s.name in FRAGILE_CELLS]
    fig, ax = plt.subplots(figsize=(9, 4))
    for n, ci in enumerate(fragile):
        allocated = (res_b.weights[:, ci] > 0).astype(float)
        ax.plot(t, allocated + 0.02 * n, label=f"{streams[ci].name} allocated", drawstyle="steps-post")
    ax.set_ylim(-0.1, 1.2)
    ax.set_yticks([0, 1], ["broken (0)", "allocated (1)"])
    ax.set_title("EXP-096 Portfolio B circuit-breaker timeline under v2 (fragile 1h cells)", fontsize=9)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "circuit_breaker_timeline_v2.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _drawdown(returns: np.ndarray) -> np.ndarray:
    eq = _equity(returns)
    return np.maximum.accumulate(eq) - eq


def _plot_drawdown_ab(block_v2: dict[str, Any]) -> None:
    grid_epochs = block_v2["_grid_start"] + np.arange(block_v2["_n_steps"]) * STEP_SECONDS
    t = grid_epochs.astype("datetime64[s]")
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.fill_between(t, -_drawdown(block_v2["_res_a"].returns), 0, color="steelblue", alpha=0.5,
                    label=f"A drawdown (Ulcer {block_v2['A']['ulcer']:.4f})")
    ax.fill_between(t, -_drawdown(block_v2["_res_b"].returns), 0, color="seagreen", alpha=0.45,
                    label=f"B drawdown (Ulcer {block_v2['B']['ulcer']:.4f})")
    ax.set_title("EXP-096 A vs B drawdown under v2; does realistic execution make the breaker de-risk?",
                 fontsize=9)
    ax.set_ylabel("drawdown (negative)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "drawdown_A_vs_B_v2.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Output writers
# --------------------------------------------------------------------------- #
def write_outputs(blocks: dict[str, dict[str, Any]], cells: list[NoiseCell],
                  provenance: list[dict[str, Any]], conservation: list[dict[str, Any]],
                  ladder: list[dict[str, Any]], degradation: list[dict[str, Any]], gate: dict[str, Any],
                  adapt: dict[str, Any], cov_bracket: dict[str, float], fpr: dict[str, Any]) -> None:
    """Write every headline artifact named in the analysis plan."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    b2 = blocks[BINDING_VARIANT]
    pl.DataFrame(provenance).write_csv(RESULTS_DIR / "provenance_reconciliation.csv")
    pl.DataFrame(conservation).write_csv(RESULTS_DIR / "mtm_conservation.csv")
    pl.DataFrame(ladder).write_csv(RESULTS_DIR / "noise_ladder.csv")
    pl.DataFrame(degradation).write_csv(RESULTS_DIR / "per_cell_degradation.csv")
    pl.DataFrame([{"cell": c.name, "n_kept": c.keep_count,
                   "n_entry_unavailable_on_keep": c.n_entry_unavailable_on_keep, **c.entry_audit}
                  for c in cells]).write_csv(RESULTS_DIR / "entry_fill_audit.csv")

    grid_epochs = b2["_grid_start"] + np.arange(b2["_n_steps"]) * STEP_SECONDS
    ts = grid_epochs.astype("datetime64[s]").astype(str)
    pl.DataFrame({"timestamp": ts, "net_return": b2["_res_a"].returns}).write_csv(
        RESULTS_DIR / "portfolio_returns_A.csv")
    pl.DataFrame({"timestamp": ts, "net_return": b2["_res_b"].returns}).write_csv(
        RESULTS_DIR / "portfolio_returns_B.csv")

    res_a = b2["_res_a"]
    reb_ts = (b2["_grid_start"] + res_a.rebalance_idx * STEP_SECONDS).astype("datetime64[s]").astype(str)
    w_reb = res_a.weights[res_a.rebalance_idx]
    wt: dict[str, Any] = {"rebalance_ts": reb_ts}
    for ci, s in enumerate(b2["_streams"]):
        wt[s.name] = w_reb[:, ci]
    pl.DataFrame(wt).write_csv(RESULTS_DIR / "weights_timeline_v2.csv")

    res_b = b2["_res_b"]
    cb: dict[str, Any] = {"timestamp": ts}
    for ci, s in enumerate(b2["_streams"]):
        if s.name in FRAGILE_CELLS:
            cb[f"{s.name}_allocated"] = (res_b.weights[:, ci] > 0).astype(int)
    pl.DataFrame(cb).write_csv(RESULTS_DIR / "circuit_breaker_timeline_v2.csv")

    metric_rows: list[dict[str, Any]] = []
    for v in VARIANTS:
        for key in ("A", "B", "naive_iv"):
            m = blocks[v][key]
            metric_rows.append({"variant": v, "portfolio": key,
                                **{k: val for k, val in m.items() if not k.startswith("_")}})
        for name, pc in blocks[v]["per_cell"].items():
            metric_rows.append({"variant": v, "portfolio": f"cell:{name}",
                                **{k: val for k, val in pc.items() if not k.startswith("_")}})
    pl.DataFrame(metric_rows, strict=False).write_csv(RESULTS_DIR / "portfolio_metrics.csv")

    (RESULTS_DIR / "benefit_v2.json").write_text(json.dumps(b2["benefit"], indent=2, default=str))
    (RESULTS_DIR / "gate_recheck.json").write_text(json.dumps(gate, indent=2, default=str))
    (RESULTS_DIR / "adaptability_v2.json").write_text(json.dumps(adapt, indent=2, default=str))
    (RESULTS_DIR / "cov_bracket_v2.json").write_text(json.dumps(
        {"cov_window_sensitivity_disclosed": cov_bracket,
         "note": "brackets are disclosed sensitivity ONLY — never used to select a value"}, indent=2))
    (RESULTS_DIR / "fpr_sanity_v2.json").write_text(json.dumps(fpr, indent=2, default=str))


def hash_outputs() -> dict[str, str]:
    """SHA-256 of each headline output (byte-identical second-pass pin)."""
    names = ("provenance_reconciliation.csv", "mtm_conservation.csv", "noise_ladder.csv",
             "per_cell_degradation.csv", "portfolio_returns_A.csv", "portfolio_returns_B.csv",
             "portfolio_metrics.csv", "benefit_v2.json", "gate_recheck.json")
    out: dict[str, str] = {}
    for name in names:
        p = RESULTS_DIR / name
        if p.exists():
            out[name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


# --------------------------------------------------------------------------- #
# Determinism
# --------------------------------------------------------------------------- #
def determinism_replay(block_v2: dict[str, Any]) -> dict[str, Any]:
    """Rebuild v2 A and B from the same matrices; assert byte-identical return series (D8)."""
    return E95.determinism_replay(block_v2["_streams"], block_v2["_grid_start"], block_v2["_n_steps"],
                                  block_v2["_pnl_mat"], block_v2["_trade_mat"], block_v2)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def run(skip_fpr_sanity: bool = False) -> dict[str, Any]:
    """Full EXP-096 entry-fill noise build under the binding v2 + the v1/v2/v3 ladder (no holdout verdict)."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    margins = load_exp093_margins()
    cells, src_meta, causal_fill = build_cells()
    provenance = reconcile_provenance(cells)
    LOGGER.info("provenance gate PASS for %d cells", len(provenance))

    # keep-mask invariance: idealized resolved counts == EXP-093 (count_match) + entry fill defined on keep.
    unavailable = {c.name: c.n_entry_unavailable_on_keep for c in cells if c.n_entry_unavailable_on_keep}
    if unavailable:
        raise RuntimeError(f"keep-mask invariance: kept events with no entry fill: {unavailable}")

    blocks: dict[str, dict[str, Any]] = {}
    for v in tqdm(VARIANTS, desc="portfolio per variant", unit="variant", dynamic_ncols=True):
        blocks[v] = variant_block(cells, v, n_boot=N_BOOT)
        attach_benefit_margins(blocks[v])
    b2 = blocks[BINDING_VARIANT]

    conservation = conservation_check(cells)
    ladder = noise_ladder(blocks)
    degradation = per_cell_degradation(cells, margins)
    gate = gate_recheck(b2)
    adapt = adaptability(b2, cells)
    cov_bracket = cov_bracket_v2(b2)
    causal_weight = E95.causal_weight_assertion(b2["_pnl_mat"], b2["_trade_mat"], b2["_grid_start"])
    determinism = determinism_replay(b2)

    holdout_equiv_steps = int(round(b2["_n_steps"] * 0.30 / 0.70))
    if skip_fpr_sanity:
        fpr = {"note": "FPR sanity skipped (disclosure-only; m* inherited from EXP-095)"}
    else:
        fpr = {"A": fpr_sanity(b2["_trade_mat"], b2["_grid_start"], holdout_equiv_steps, False, "A"),
               "B": fpr_sanity(b2["_trade_mat"], b2["_grid_start"], holdout_equiv_steps, True, "B")}

    make_plots(blocks, ladder, degradation, gate)
    write_outputs(blocks, cells, provenance, conservation, ladder, degradation, gate, adapt, cov_bracket, fpr)
    meta = _build_metadata(blocks, cells, margins, src_meta, conservation, gate, adapt, cov_bracket,
                           causal_fill, causal_weight, determinism, degradation, fpr, holdout_equiv_steps)
    meta["output_hashes"] = hash_outputs()
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(meta, indent=2, default=str))
    _log_summary(b2, gate, determinism, causal_fill, causal_weight, time.perf_counter() - t0)
    return meta


def _build_metadata(blocks: dict[str, dict[str, Any]], cells: list[NoiseCell], margins: dict[str, float],
                    src_meta: dict[str, Any], conservation: list[dict[str, Any]], gate: dict[str, Any],
                    adapt: dict[str, Any], cov_bracket: dict[str, float], causal_fill: dict[str, Any],
                    causal_weight: dict[str, Any], determinism: dict[str, Any],
                    degradation: list[dict[str, Any]], fpr: dict[str, Any],
                    holdout_equiv_steps: int) -> dict[str, Any]:
    b2 = blocks[BINDING_VARIANT]
    flagged = [r["cell"] for r in degradation if r["noise_degraded"]]
    conservation_ok = all(r["PASS"] for r in conservation)
    return {
        "experiment_id": EXPERIMENT_ID, "phase": "022", "family": "CF-MR-001", "hyp": "HYP-003",
        "role": "noise infusion — realistic 1-minute entry fill (analysis-set; no holdout verdict)",
        "amendment_inherited": "D0-amendment-001 (A1 intra-1h MTM; A2 like-for-like median-cell baseline; "
                               "A3 co-binding Calmar/CVaR/Ulcer; A4 MDE m* INHERITED, not recomputed)",
        "generated_utc": datetime.now(timezone.utc).isoformat(), "master_seed": MASTER_SEED,
        "deployable_cells": [f"{i}-{d}" for i, d in CELLS], "surviving_exit": ARM,
        "noise_model": {"binding_variant": BINDING_VARIANT, "slippage_atr": SLIPPAGE_ATR, "k_worst": K_WORST,
                        "v1": "next-1m-open", "v2": "next-1m-open + 0.05*ATR adverse slippage (BINDING)",
                        "v3": "worst (most adverse) of next k=3 1m bars",
                        "entry_leg_only": True,
                        "cost_notional": "pinned to signal-bar close (identical to EXP-093; not double-counted)"},
        "construction": "EXP-095 frozen build reused verbatim (ERC/Ledoit-Wolf/weekly/10% vol/1.5x cap/"
                        "trailing-50 breaker/intra-1h MTM); only the entry execution price changes",
        "cost_model": "EXP-085/093 CONSERVATIVE RT (D0-amendment-003); F=0", "cost_rt_bps": MR_COST_RT_BPS,
        "binding_v2_metrics": {"A": {k: v for k, v in b2["A"].items() if not k.startswith("_")},
                               "B": {k: v for k, v in b2["B"].items() if not k.startswith("_")},
                               "naive_iv": b2["naive_iv"], "best_cell_name": b2["best_cell_name"],
                               "best_cell_sharpe": b2["best_cell_sharpe"],
                               "pooled_expectancy_lo": b2["pooled_expectancy_lo"]},
        "benefit_v2": b2["benefit"],
        "noise_ladder": {v: {"A_sharpe_lo": blocks[v]["A"]["ann_sharpe_lo"],
                             "B_sharpe_lo": blocks[v]["B"]["ann_sharpe_lo"],
                             "A_calmar_lo": blocks[v]["A"]["calmar_lo"],
                             "B_calmar_lo": blocks[v]["B"]["calmar_lo"]} for v in VARIANTS},
        "gate_recheck_inherited_mstar": gate, "adaptability_v2": adapt,
        "cov_window_bracket_v2_disclosed": cov_bracket,
        "per_cell_margins": margins, "noise_degraded_cells_flagged": flagged,
        "membership_rule": "portfolio-only (operator 2026-06-25): all 8 retained; per-cell flags are "
                           "disclosure; G-022a adjudicates the holdout-frozen set",
        "fpr_sanity_v2_disclosed": fpr,
        "mtm_conservation_pass": conservation_ok,
        "causal_entry_fill_assertion": causal_fill, "causal_weight_assertion": causal_weight,
        "determinism": determinism,
        "grid_start_epoch": b2["_grid_start"], "n_grid_steps": b2["_n_steps"],
        "holdout_equiv_steps": holdout_equiv_steps,
        "n_boot": N_BOOT, "cal_n_boot": CAL_N_BOOT, "n_null": N_NULL, "boot_alpha": BOOT_ALPHA,
        "real_prices_only": True, "holdout_untouched": True, "counted_test_reads": 0, "candidate_slots": 0,
        "read_accounting": ("portfolio-aggregate / cost-re-resolution disclosure (EXP-085 precedent): "
                            "re-resolves only the entry-fill leg of the EXP-093 analysis-TEST series — same "
                            "cells, same selection, no new stratum-specific inference; 11 carried strata stay "
                            "1/2; 37 stay 0/2; final-30% global holdout never loaded"),
        "source_meta": src_meta,
    }


def _log_summary(b2: dict[str, Any], gate: dict[str, Any], determinism: dict[str, Any],
                 causal_fill: dict[str, Any], causal_weight: dict[str, Any], secs: float) -> None:
    a, b = b2["A"], b2["B"]
    LOGGER.info("EXP-096 done in %.1fs | v2 A Sharpe=%.3f (lo %.3f) | v2 B Sharpe=%.3f (lo %.3f) | "
                "median-cell LB=%.3f", secs, a["ann_sharpe"], a["ann_sharpe_lo"], b["ann_sharpe"],
                b["ann_sharpe_lo"], b2["benefit"]["median_cell_sharpe_lo"])
    for port in ("A", "B"):
        g = gate[port]
        LOGGER.info("  gate[%s]: v2 Sharpe LB %.3f vs inherited m* %.2f -> edge %.3f clears=%s", port,
                    g["v2_sharpe_lo"], g["m_star"], g["edge_vs_mstar"], g["clears_inherited_mde"])
    LOGGER.info("  determinism=%s causal_fill=%s causal_weight=%s holdout_untouched=True counted_reads=0",
                determinism["determinism_pass"], causal_fill["causal_entry_fill_pass"],
                causal_weight["causal_weight_pass"])


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description="EXP-096 entry-fill noise infusion (analysis-set)")
    ap.add_argument("--skip-fpr-sanity", action="store_true",
                    help="skip the disclosure-only v2 synthetic-null FPR sanity (faster smoke run)")
    args = ap.parse_args()
    meta = run(skip_fpr_sanity=args.skip_fpr_sanity)
    a = meta["binding_v2_metrics"]["A"]
    b = meta["binding_v2_metrics"]["B"]
    g = meta["gate_recheck_inherited_mstar"]
    print(f"EXP-096 complete | v2 A Sharpe={a['ann_sharpe']:.3f} (lo {a['ann_sharpe_lo']:.3f}) | "
          f"v2 B Sharpe={b['ann_sharpe']:.3f} (lo {b['ann_sharpe_lo']:.3f}) | "
          f"median-cell LB={meta['benefit_v2']['median_cell_sharpe_lo']:.3f} | "
          f"clears m*={g['statistic_clearable_under_noise']} | "
          f"flagged={meta['noise_degraded_cells_flagged']} | "
          f"determinism={meta['determinism']['determinism_pass']} "
          f"holdout_untouched={meta['holdout_untouched']} counted_reads={meta['counted_test_reads']}")


if __name__ == "__main__":
    main()
