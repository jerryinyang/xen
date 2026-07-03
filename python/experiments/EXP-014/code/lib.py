"""
EXP-014 — CF-MR-004/HYP-002 shared analysis library (ANALYSIS-ONLY, L-01/P-09).

From-scratch family analysis (L-13; logic reuse of the frozen referee + native-estimand helpers
only). NEVER regenerates a signal, anchor, edge, or fill — every entry/exit/fill is engine-realized
by the native cTrader run (StrategyHost/CrossInstrumentSpreadPlanner.cs + Xen NativeOrders) and read
from data/strategy_runs/EXP-014-*/. This module holds the run map, ingestion, the engine-realized
per-bar NET bps assembly (intra-position MTM, L-09; RT cost once per entry, L-02), the frozen 4h
referee wrappers (referee_pstar.gate_stack_pstar — never tuned, L-12), and a moving-block bootstrap.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "python" / "src"))

from xen.referee_adaptive import adaptive_cost_bps_for, adaptive_row          # noqa: E402
from xen.referee_calibration import DOMAIN_SPECS                              # noqa: E402
from xen.referee_pstar import gate_stack_pstar                               # noqa: E402
from xen.signals.ingestion import load_emitted_run, assert_run_within_holdout  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (frozen) + run map
# --------------------------------------------------------------------------- #
DOMAIN = "4h"
ALPHA = 0.05
N_BOOTSTRAP = 10_000
BLOCK = 4                                       # moving-block length (availability bootstrap)
SEED = 20260702
STRATEGY = "cross_instrument_spread_mr"
MIN_STATE = DOMAIN_SPECS[DOMAIN].min_state_count   # frozen 4h power floor N_min (governs, L-12)
DATA_ROOT = ROOT / "data" / "strategy_runs"

FX = ("EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD")
IDX = ("USTEC", "US500", "US2000", "JP225")
BASKET_CELLS = FX + IDX                          # S5 / S7 / S8 (basket, F-fix): 11 each
S6_CELLS = ("EURUSD", "AUDUSD", "USDCHF", "USTEC", "US500")   # S6 pairs: 5

# Binding PRIMARY arm = none/R. Disclosure arms: none/S (A/B), allow/R, extend/R (reentry ladder).
PRIMARY_ARM = "noneR"
ARMS = ("noneR", "noneS", "allowR", "extendR")
SERIES = {
    "S5": {"tag": "s5", "cells": BASKET_CELLS, "cis": "S5_SPREAD"},
    "S6": {"tag": "s6", "cells": S6_CELLS, "cis": "S6_PAIR"},
    "S7": {"tag": "s7", "cells": BASKET_CELLS, "cis": "S7_BASKET"},
    "S8": {"tag": "s8", "cells": BASKET_CELLS, "cis": "S8_RVINDEX"},
}
PROV_COLS = ("Position", "RealOpen", "RealHigh", "RealLow", "RealClose",
             "EntryFillPrice", "ExitFillPrice", "Anchor", "Dev", "Z", "Vr", "Hl", "Beta",
             "MateCount", "MateExpected", "MateGap", "OpenLegs")
SYSTEMATIC_BREACH_FRAC = 0.05                    # >5% fills outside bar range = systematic (lookahead) → fail


def run_root(series: str, arm: str, shift: bool = False) -> Path:
    """data/strategy_runs root for one (series, arm) [+ -shift leak-tripwire variant]."""
    tag = SERIES[series]["tag"]
    name = f"EXP-014-{tag}-{arm}" + ("-shift" if shift else "")
    return DATA_ROOT / name


def newest_run_dir(root: Path, instrument: str) -> Path:
    pattern = f"{STRATEGY}_{instrument.lower()}_{DOMAIN}_*"
    hits = sorted(root.glob(pattern), key=lambda p: p.name)
    if not hits:
        raise FileNotFoundError(f"No emitted run for {instrument} under {root} ({pattern})")
    return hits[-1]


# --------------------------------------------------------------------------- #
# Ingestion / provenance
# --------------------------------------------------------------------------- #
@dataclass
class Cell:
    series: str
    arm: str
    instrument: str
    positions: pl.DataFrame
    cis_trades: pl.DataFrame
    metadata: dict


def load_cell(series: str, arm: str, instrument: str, shift: bool = False) -> Cell:
    """Load + fence-check one emitted cell; attach the per-trade table (cis_trades.parquet)."""
    rd = newest_run_dir(run_root(series, arm, shift), instrument)
    run = load_emitted_run(rd)
    assert_run_within_holdout(run.positions, run.metadata.get("analysis_end_utc"))
    cis_path = rd / "cis_trades.parquet"
    cis = pl.read_parquet(cis_path) if cis_path.exists() else pl.DataFrame()
    return Cell(series, arm, instrument, run.positions, cis, run.metadata)


def validate_provenance(positions: pl.DataFrame, instrument: str) -> dict:
    """Provenance columns present; engine fills within [Low,High] up to a gap/spread tolerance.
    Isolated breaches (bid/ask side vs bid-based OHLC, session-gap open fills of a ≤t-1 resting limit)
    are benign and reported; a >5% systematic breach rate is a non-causal hard fail (L-01 pass)."""
    missing = [c for c in PROV_COLS if c not in positions.columns]
    if missing:
        raise ValueError(f"{instrument}: emitted positions missing provenance columns {missing}")
    df = positions.sort("SourceCloseTime")
    stats: dict = {}
    for leg in ("EntryFillPrice", "ExitFillPrice"):
        fills = df.filter(pl.col(leg).is_not_nan())
        if fills.height == 0:
            stats[leg] = {"n_fills": 0, "n_breach": 0, "max_bps": 0.0, "breach_frac": 0.0}
            continue
        f = fills.with_columns(
            tol=pl.max_horizontal(0.1 * (pl.col("RealHigh") - pl.col("RealLow")), 1e-4 * pl.col(leg)),
            over=pl.max_horizontal(pl.col(leg) - pl.col("RealHigh"), pl.col("RealLow") - pl.col(leg), 0.0))
        breach = f.filter(pl.col("over") > pl.col("tol"))
        max_bps = float((breach.select((pl.col("over") / pl.col(leg) * 1e4).max()).item() or 0.0)
                        ) if breach.height else 0.0
        frac = breach.height / fills.height
        stats[leg] = {"n_fills": fills.height, "n_breach": breach.height,
                      "max_bps": max_bps, "breach_frac": frac}
        if frac > SYSTEMATIC_BREACH_FRAC:
            raise ValueError(f"{instrument}: {breach.height}/{fills.height} {leg} fills outside bar "
                             f"range ({frac:.1%} > {SYSTEMATIC_BREACH_FRAC:.0%}) — systematic non-causal")
    # Min-mate rule: fraction of bars flagged basket-invalid (no new order armed) — bound the effect.
    if "MateGap" in df.columns:
        n = df.height
        stats["mate_gap_frac"] = float(df.get_column("MateGap").cast(pl.Int8).sum() / n) if n else 0.0
    return stats


# --------------------------------------------------------------------------- #
# Engine-realized per-bar NET bps (intra-position MTM, L-09; RT cost once/entry, L-02).
# Reads ONLY emitted columns (P-09 clean). Position = dir active during the bar.
# --------------------------------------------------------------------------- #
def assemble_realized_bps(positions: pl.DataFrame, *, cost_bps: float
                          ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    df = positions.sort("SourceCloseTime")
    pos = df.get_column("Position").to_numpy().astype(float)
    op = df.get_column("RealOpen").to_numpy().astype(float)
    entry = df.get_column("EntryFillPrice").to_numpy().astype(float)
    exit_ = df.get_column("ExitFillPrice").to_numpy().astype(float)
    if len(pos) < 3:
        raise ValueError("too few emitted bars to assemble a realized series")
    next_open = op[1:]
    op, pos, entry, exit_ = op[:-1], pos[:-1], entry[:-1], exit_[:-1]
    has_entry = ~np.isnan(entry)
    has_exit = ~np.isnan(exit_)
    with np.errstate(divide="ignore", invalid="ignore"):
        open_price = np.where(has_entry, entry, op)          # entry bar → entry fill else bar open
        close_price = np.where(has_exit, exit_, next_open)   # exit bar → exit fill else next open
        gross = pos * np.log(close_price / open_price) * 10_000.0
    gross = np.where(pos != 0.0, gross, 0.0)
    gross = np.nan_to_num(gross, nan=0.0, posinf=0.0, neginf=0.0)
    realized_bps = gross - cost_bps * has_entry.astype(float)
    market_returns = np.nan_to_num(np.log(next_open / op), nan=0.0, posinf=0.0, neginf=0.0)
    return market_returns, pos, realized_bps


def pstar_core(returns: np.ndarray, pos: np.ndarray, realized_bps: np.ndarray, cost_bps: float) -> dict:
    """Frozen 4h P*-gate core (referee_pstar.gate_stack_pstar) — never tuned (L-12)."""
    return gate_stack_pstar(returns, pos, realized_bps, domain=DOMAIN, cost_bps=cost_bps,
                            n_bootstrap=N_BOOTSTRAP, seed=SEED)


def boot_p(core: dict) -> float:
    """One-sided bootstrap p from the referee's neutral-mean distribution (for Holm)."""
    neutral = np.asarray(core.get("neutral_means", []), dtype=float)
    return float(np.mean(neutral <= 0.0)) if neutral.size else float("nan")


def cost_for(instrument: str) -> float:
    return adaptive_cost_bps_for(instrument, DOMAIN)


def referee_row(returns: np.ndarray, pos: np.ndarray, realized_bps: np.ndarray, cost_bps: float) -> dict:
    return adaptive_row(pstar_core(returns, pos, realized_bps, cost_bps), alpha=ALPHA)


# --------------------------------------------------------------------------- #
# Moving-block bootstrap (availability Δ CI; block-permute per-event outcomes — never rotate the
# path, L-07). iid resample for the matched-random control arm.
# --------------------------------------------------------------------------- #
def block_bootstrap_mean_ci(x: np.ndarray, *, block: int = BLOCK, n: int = N_BOOTSTRAP,
                            seed: int = SEED, alpha: float = ALPHA) -> tuple[float, float, float]:
    """Return (mean, ci_low, ci_high) via a moving-block bootstrap over per-event outcomes."""
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if x.size == 0:
        return (float("nan"), float("nan"), float("nan"))
    if x.size < block or block <= 1:
        return (float(np.mean(x)), float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(x.size / block))
    starts_max = x.size - block + 1
    means = np.empty(n, dtype=float)
    for b in range(n):
        starts = rng.integers(0, starts_max, size=n_blocks)
        sample = np.concatenate([x[s:s + block] for s in starts])[:x.size]
        means[b] = sample.mean()
    lo = float(np.quantile(means, alpha / 2.0))
    hi = float(np.quantile(means, 1.0 - alpha / 2.0))
    return (float(np.mean(x)), lo, hi)


def two_sample_diff_ci(cond: np.ndarray, ctrl: np.ndarray, *, block: int = BLOCK,
                       n: int = N_BOOTSTRAP, seed: int = SEED, alpha: float = ALPHA
                       ) -> tuple[float, float, float]:
    """Δ = mean(cond) − mean(ctrl) with a bootstrap CI (moving-block on cond, iid on ctrl)."""
    cond = np.asarray(cond, dtype=float); cond = cond[np.isfinite(cond)]
    ctrl = np.asarray(ctrl, dtype=float); ctrl = ctrl[np.isfinite(ctrl)]
    if cond.size == 0 or ctrl.size == 0:
        return (float("nan"), float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    diffs = np.empty(n, dtype=float)
    eff_block = block if cond.size >= block else 1
    n_blocks = int(np.ceil(cond.size / eff_block))
    starts_max = max(1, cond.size - eff_block + 1)
    for b in range(n):
        starts = rng.integers(0, starts_max, size=n_blocks)
        cs = np.concatenate([cond[s:s + eff_block] for s in starts])[:cond.size]
        ks = ctrl[rng.integers(0, ctrl.size, size=ctrl.size)]
        diffs[b] = cs.mean() - ks.mean()
    delta = float(cond.mean() - ctrl.mean())
    return (delta, float(np.quantile(diffs, alpha / 2.0)), float(np.quantile(diffs, 1.0 - alpha / 2.0)))


def holm(pvals: dict[str, float], alpha: float = ALPHA) -> dict[str, bool]:
    """Holm step-down over cross-axis cell p-values (L-03 per-stratum; L-08 multiplicity)."""
    items = sorted(((k, v) for k, v in pvals.items() if np.isfinite(v)), key=lambda kv: kv[1])
    m = len(items)
    out = {k: False for k in pvals}
    for i, (k, p) in enumerate(items):
        if m - i > 0 and p <= alpha / (m - i):
            out[k] = True
        else:
            break
    return out
