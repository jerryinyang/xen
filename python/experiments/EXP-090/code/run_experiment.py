"""EXP-090 — RSI-2 Fade Exit-Substrate Readiness & Per-Cell Inference Calibration (TRAIN-only).

Phase 021 / ``CF-MR-001`` / HYP-002 — the readiness + calibration step before the Phase-021 exit
screen (EXP-091). Governing design/D0:
``docs/experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/`` (``design.md`` §4
EXP-090; ``D0-predeclarations.md`` D1–D9 + ``D0-amendment-001``). TRAIN sub-split only (first 49%
per file); **0 candidate slots, 0 counted TEST reads, holdout never loaded**.

Two cleanly separated deliverables (analysis-plan.md):

  A. **Readiness (deterministic).** The bare RSI-2 fade (CORE) entry substrate (count/coverage/
     invariants/determinism — counts only, no outcomes) **and** the new 1-minute intrabar
     exit-fill substrate (``xen.intrabar_fill`` + the D2.3 frozen adverse side) are constructible,
     deterministic, causal, timestamp-aligned, holdout-fenced. **No expectancy, no cost, no exit
     selection.**
  B. **Per-cell event-level inference calibration.** The binding D6 figure — the **mean** net
     per-event expectancy moving-block bootstrap one-sided lower bound (``Z=1.645``; median
     co-reported, D5) — has controlled per-cell FPR (<= α₀=0.05 under two structurally-different
     nulls) and a finite per-cell event-level MDE (the EXP-093 margin) at the cell's realized
     count, measured on **synthetic null/planted-edge draws** over matched-random exit-resolved
     returns (the real CORE fade outcomes are **never** resolved — the EXP-044 anti-overfitting
     fence).

**Fence (binding).** The exit-substrate readiness battery and the calibration both run on
**matched-random** entries (random placement, real exit path) — the real CORE fade entries'
exit outcomes are **never** resolved or read by EXP-090; only their counts/coverage are read
(fence-clean, like EXP-080). EXP-091 is the first to resolve the real fade exits.

**Calibration compute structure (deviation flagged for Stage-4).** The analysis plan specifies
per-draw matched-random placement + resolution (EXP-070 style). With the new 1-minute intrabar
walk that is intractable (~1e13 ops). This driver instead resolves the matched-random pool
**once per (cell × arm × path)** into a pooled per-event net-return series (the real exit-resolved
shape + serial dependence), and the 1000 calibration draws are **moving-block resamples of length
n** from that series, recentred to true-location-0 (Null A = real path, Null B = block-rotated
path). This targets the identical estimand (estimator FPR/MDE at true-0 on the real shape) and
preserves serial dependence; only the draw-generation differs (resample vs re-placement).
Planted edge via the translation-equivariance shortcut (mean/median lower bound are
location-equivariant), which is also why the calibration is faithfully cost-free (cost is a
location shift; FPR and the CI-width-driven MDE are location-invariant — D3 cost enters the real
statistic at EXP-091).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import logging
import multiprocessing
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
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

from xen.ass import BOOT_BATCH, default_block_length  # noqa: E402
from xen.domain_bars import build_domain_bars  # noqa: E402
from xen.intrabar_fill import (KIND_FAV, KIND_CAP, net_return_atr,  # noqa: E402
                               resolve_exit_paths)
from xen.mean_reversion import (MR_CAP_MAX, mean_reversion_entries, mr_tempo_caps,  # noqa: E402
                                reversion_completion_target, reversion_episodes, wilder_ema,
                                wilder_rsi)
from xen.referee_calibration import seed_for  # noqa: E402
from xen.zigzag import wilder_atr  # noqa: E402

# --------------------------------------------------------------------------- #
# Path setup + VAL-005 reuse (validated file discovery / TRAIN slice anchor)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-090"
CODE_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = CODE_DIR.parent
PROJECT_ROOT = EXPERIMENT_DIR.parents[2]
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
EXP080_READY_MAP = EXPERIMENT_DIR.parent / "EXP-080" / "results" / "ready_map.csv"
EXP080_META = EXPERIMENT_DIR.parent / "EXP-080" / "results" / "run_metadata.json"
_VAL005_CODE = PROJECT_ROOT / "python" / "experiments" / "VAL-005" / "code" / "run_experiment.py"


def _load_val005() -> Any:
    """Import the VAL-005 module (import-safe: constants/functions only, ``main`` guarded)."""
    spec = importlib.util.spec_from_file_location("val005_capgeo", _VAL005_CODE)
    if spec is None or spec.loader is None:                       # pragma: no cover - defensive
        raise ImportError(f"Could not load VAL-005 from {_VAL005_CODE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VAL005 = _load_val005()

# --------------------------------------------------------------------------- #
# Constants (frozen at D0/G0; seeds recorded in run_metadata.json — never tuned here)
# --------------------------------------------------------------------------- #
MASTER_SEED = 20260623
INSTRUMENTS: tuple[str, ...] = (
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD",
    "EURJPY", "GBPJPY", "AUDJPY", "XAUUSD", "BTCUSD", "USTEC", "US500", "US2000", "JP225",
)
DOMAINS: dict[str, int] = {"15m": 15, "1h": 60}          # 4h excluded (dead-by-absence, EXP-089)
DOMAIN_ORDER = ["15m", "1h"]

ATR_PERIOD = 14                                          # Wilder ATR (D-frozen)
ERT_EMA_PERIOD = 10                                      # EXIT-ERT equilibrium reference (param #1)
ADV_ATR_MULT = 2.0                                       # adverse stop = 2.0 x ATR (param #2)
ATR_BARRIER_FAV_MULT = 1.0                               # ATR triple-barrier favourable leg
COVERAGE_FLOOR = 15                                      # D8 (>=15 events; NO upper bound)
DROP_FLAG, DROP_FAIL = 0.10, 0.25                        # construction dropped-window bands

# Exit arms resolved through the unified xen.intrabar_fill engine (D2). The two-leg favourable
# partial/trail arm (capgeo_cost.partial_two_leg_exit) is registered in the slate but its
# readiness+screen are performed in EXP-091 (its structurally-different two-leg resolver does not
# share the single-favourable-touch engine, and EXP-090's binding member gate keys only on the
# native arms RCT/ERT) — deviation flagged for Stage-4.
NATIVE_ARMS = ("RCT", "ERT")                             # primary hypothesis (member gate keys here)
CONTRAST_ARMS = ("ATR-BARRIER", "RSI-REVERT", "FIXED-BAR")
ARMS = NATIVE_ARMS + CONTRAST_ARMS

# Calibration design (fixed in Stage 2 / this file, before any measurement).
N_DRAWS = 1000                                           # draws per (cell x arm x null)
N_BOOT = 10_000                                          # inner moving-block bootstrap resamples
BOOT_ALPHA = 0.10                                        # 90% CI -> one-sided 95% lower bound (5th pct)
ALPHA0 = 0.05                                            # binding FPR operating point
EDGE_GRID: tuple[float, ...] = (0.0, 0.0125, 0.025, 0.05, 0.10, 0.20, 0.40, 0.80)  # ATR (geometric)
TPR_TARGET = 0.80                                        # planted-edge MDE recovery target
N_CAL_MAX = 4000                                         # conservative calibration-count cap
N_POOL_MAX = 6000                                        # matched-random pool resolution cap
FPR_WILSON_HW_MAX = 0.03                                 # precision gate (FPR)
TPR_WILSON_HW_MAX = 0.05                                 # precision gate (TPR)
DRAW_COMPLETION_FLOOR = 0.90
RCT_RSI_TOL = 1e-6                                       # RCT correctness invariant (rsi2_at(P*)~50)
UNDERPOWERED_FRACTION = 1.0 / 3.0                        # > this share underpowered => INCONCLUSIVE
DETERMINISM_CELLS = (("EURUSD", "15m"), ("AUDJPY", "1h"))  # high-count 15m + lower-count 1h
NULLS = ("A_real_path", "B_block_rotated_path")
LONG, SHORT = 1, -1

HEADLINE_OUTPUTS = ("member_map.csv", "entry_coverage.csv", "exit_substrate_readiness.csv",
                    "fpr_mde_per_cell.csv", "calibration_draws.parquet", "null_fpr_sanity.json")
LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# Dataclasses / types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CellContext:
    """Per-cell TRAIN-only precomputed context (all arrays inside the TRAIN frame)."""

    instrument: str
    domain: str
    n_domain: int
    close: np.ndarray
    high: np.ndarray
    low: np.ndarray
    domain_close_epoch: np.ndarray
    minute_high: np.ndarray
    minute_low: np.ndarray
    minute_open: np.ndarray
    minute_close_epoch: np.ndarray
    train_edge_epoch: int
    rsi2: np.ndarray
    atr: np.ndarray
    ema10: np.ndarray
    rct_target: np.ndarray
    ep_close_idx: np.ndarray                  # reversion-episode close indices (for caps)
    ep_durations: np.ndarray
    core_entry_idx: np.ndarray                # real CORE fade entries (COUNTS ONLY; never resolved)
    core_direction: np.ndarray
    eligible_pool: np.ndarray                 # matched-random pool (excl. real CORE entries)
    dropped_fraction: float


# --------------------------------------------------------------------------- #
# I/O helpers (TRAIN sub-split load; holdout never materialized)
# --------------------------------------------------------------------------- #
def load_train_1m(instrument: str, path: Path) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Load the TRAIN sub-split (first 70% of the first-70% analysis set) of one 5-year file.

    ``analysis_rows = int(total_rows*0.7)``; ``train_cutoff = int(analysis_rows*0.7)``. Only the
    first ``train_cutoff`` ``CloseTime``-sorted 1-minute rows are collected — the analysis-TEST
    stratum and the final-30% global holdout are never materialized (only metadata locates the
    split). Returns the TRAIN 1-minute frame and a source-identity record.
    """
    scan = pl.scan_parquet(path).sort("CloseTime")
    total_rows = int(scan.select(pl.len()).collect().item())
    analysis_rows = int(total_rows * 0.7)
    train_cutoff = int(analysis_rows * 0.7)
    frame = scan.slice(0, train_cutoff).collect()
    if frame.height != train_cutoff:                              # 0 holdout rows read (assert)
        raise RuntimeError(f"{instrument}: TRAIN slice {frame.height} != {train_cutoff}")
    if not frame.get_column("CloseTime").is_sorted():
        raise RuntimeError(f"{instrument}: TRAIN slice not sorted by CloseTime")
    meta = {"source_file": path.name, "total_rows": total_rows, "analysis_rows": analysis_rows,
            "train_rows": train_cutoff,
            "train_end": str(frame.get_column("CloseTime").max())}
    return frame, meta


# --------------------------------------------------------------------------- #
# Pure computation — per-cell context build (domain bars, indicators, entries, pool)
# --------------------------------------------------------------------------- #
def build_cell_context(train_1m: pl.DataFrame, instrument: str, domain: str,
                       ) -> tuple[CellContext | None, float, str]:
    """Build the TRAIN-only per-cell context. Returns (ctx|None, dropped_fraction, status)."""
    period = DOMAINS[domain]
    bars = build_domain_bars(train_1m, period)
    n_domain = bars.height
    dropped = _dropped_fraction(train_1m, period, bars)
    if dropped > DROP_FAIL:
        return None, dropped, "COVERAGE_EXCLUDED"
    if n_domain <= max(ATR_PERIOD, ERT_EMA_PERIOD, MR_CAP_MAX) + 2:
        return None, dropped, "CONSTRUCTED_EMPTY"
    close = bars.get_column("Close").to_numpy().astype(np.float64)
    high = bars.get_column("High").to_numpy().astype(np.float64)
    low = bars.get_column("Low").to_numpy().astype(np.float64)
    dce = bars.get_column("CloseTime").dt.epoch("s").to_numpy().astype(np.int64)
    minute_high = train_1m.get_column("High").to_numpy().astype(np.float64)
    minute_low = train_1m.get_column("Low").to_numpy().astype(np.float64)
    minute_open = train_1m.get_column("Open").to_numpy().astype(np.float64)
    mce = train_1m.get_column("CloseTime").dt.epoch("s").to_numpy().astype(np.int64)
    rsi2 = wilder_rsi(close, 2)
    atr = wilder_atr(high, low, close, ATR_PERIOD)
    ema10 = wilder_ema(close, ERT_EMA_PERIOD)
    rct_target = reversion_completion_target(close, 2)
    ep_close, ep_dur = reversion_episodes(rsi2)
    core = mean_reversion_entries(close, instrument=instrument, domain=domain, n_bars=n_domain)["CORE"]
    pool = _eligible_pool(rsi2, atr, n_domain, core.entry_idx)
    ctx = CellContext(
        instrument=instrument, domain=domain, n_domain=n_domain, close=close, high=high, low=low,
        domain_close_epoch=dce, minute_high=minute_high, minute_low=minute_low,
        minute_open=minute_open,
        minute_close_epoch=mce, train_edge_epoch=int(mce[-1]), rsi2=rsi2, atr=atr, ema10=ema10,
        rct_target=rct_target, ep_close_idx=ep_close, ep_durations=ep_dur,
        core_entry_idx=core.entry_idx, core_direction=core.direction, eligible_pool=pool,
        dropped_fraction=dropped)
    return ctx, dropped, "OK"


def _dropped_fraction(train_1m: pl.DataFrame, period: int, bars: pl.DataFrame) -> float:
    """Fraction of fence-eligible period-grid windows dropped by coverage (EXP-080 convention)."""
    period_s = period * 60
    src_max = int(train_1m.select(pl.col("CloseTime").dt.epoch("s").max()).item())
    buckets = train_1m.select(
        ((pl.col("CloseTime").dt.epoch("s") - 1) // period_s).alias("_b")).get_column("_b")
    cand = buckets.unique()
    cand = cand.filter(((cand + 1) * period_s) <= src_max)
    n_cand = int(cand.len())
    if n_cand == 0:
        return 0.0
    return max(0.0, 1.0 - bars.height / n_cand)


def _eligible_pool(rsi2: np.ndarray, atr: np.ndarray, n_domain: int,
                   core_idx: np.ndarray) -> np.ndarray:
    """Matched-random pool: bars with defined RSI/ATR and room for a cap, excl. real CORE entries.

    Direction-agnostic bar indices (the caller assigns direction per draw). A bar is eligible iff
    its RSI2 and ATR are finite, ATR > 0, it is not a warmup bar, and it has >= MR_CAP_MAX domain
    bars ahead (so any cap fits inside the TRAIN frame). Real CORE entries are excluded so the
    null carries no real fade-entry placement (fence)."""
    last_ok = n_domain - 1 - MR_CAP_MAX
    eligible = (np.isfinite(rsi2) & np.isfinite(atr) & (atr > 0.0)
                & (np.arange(n_domain) <= last_ok) & (np.arange(n_domain) > ATR_PERIOD))
    is_core = np.zeros(n_domain, dtype=bool)
    is_core[core_idx[core_idx < n_domain]] = True
    return np.flatnonzero(eligible & ~is_core)


# --------------------------------------------------------------------------- #
# Pure computation — per-arm favourable level / close-fire builders (D2 exit slate)
# --------------------------------------------------------------------------- #
def arm_levels(ctx: CellContext, entry_idx: np.ndarray, direction: np.ndarray, cap: np.ndarray,
               arm: str) -> dict[str, np.ndarray]:
    """Per-event adverse stop + per-offset favourable level / close-fire arrays for one arm.

    The adverse side is shared by **all** arms (D2.3): static stop ``entry_close - dir*2*ATR`` and
    the MR-tempo cap. Only the favourable mechanism varies (D2): trailing RCT/ERT intrabar limits,
    static ATR-barrier limit, RSI-revert domain-close condition, or fixed-bar (cap only).
    """
    m = int(entry_idx.shape[0])
    max_off = MR_CAP_MAX
    entry_close = ctx.close[entry_idx]
    atr_e = ctx.atr[entry_idx]
    d = direction.astype(np.float64)
    adv_level = entry_close - d * ADV_ATR_MULT * atr_e
    fav_level = np.full((m, max_off), np.nan, dtype=np.float64)
    fav_fire = np.zeros((m, max_off), dtype=bool)
    off = np.arange(1, max_off + 1)
    tgt_idx = entry_idx[:, None] + off[None, :]                   # (m, max_off) domain index
    valid = tgt_idx < ctx.n_domain
    safe = np.clip(tgt_idx, 0, ctx.n_domain - 1)
    if arm == "RCT":
        lvl = ctx.rct_target[safe]
        fav_level = np.where(valid & np.isfinite(lvl), lvl, np.nan)
    elif arm == "ERT":
        lvl = ctx.ema10[safe]
        fav_level = np.where(valid & np.isfinite(lvl), lvl, np.nan)
    elif arm == "ATR-BARRIER":
        static = entry_close + d * ATR_BARRIER_FAV_MULT * atr_e   # (m,) static favourable level
        fav_level = np.where(valid, static[:, None], np.nan)
    elif arm == "RSI-REVERT":
        rsi_t = ctx.rsi2[safe]
        crossed = np.where(direction[:, None] == LONG, rsi_t >= 50.0, rsi_t <= 50.0)
        fav_fire = valid & np.isfinite(rsi_t) & crossed
    elif arm == "FIXED-BAR":
        pass                                                      # cap-only (no favourable target)
    else:                                                         # pragma: no cover - guarded
        raise ValueError(f"unknown arm {arm}")
    return {"adv_level": adv_level, "fav_level": fav_level, "fav_fire": fav_fire}


def resolve_arm(ctx: CellContext, entry_idx: np.ndarray, direction: np.ndarray, arm: str,
                minute_high: np.ndarray, minute_low: np.ndarray, minute_open: np.ndarray) -> Any:
    """Resolve ``entry_idx`` through ``arm`` on the given 1-minute path (real or rotated)."""
    cap, _ = mr_tempo_caps(entry_idx, ctx.ep_close_idx, ctx.ep_durations)
    lv = arm_levels(ctx, entry_idx, direction, cap, arm)
    return resolve_exit_paths(
        minute_high=minute_high, minute_low=minute_low, minute_open=minute_open,
        minute_close_epoch=ctx.minute_close_epoch,
        domain_close_epoch=ctx.domain_close_epoch, domain_close_price=ctx.close,
        entry_idx=entry_idx, direction=direction, adv_level=lv["adv_level"], cap=cap,
        fav_level=lv["fav_level"], fav_close_fire=lv["fav_fire"],
        train_edge_epoch=ctx.train_edge_epoch, period_s=DOMAINS[ctx.domain] * 60)


# --------------------------------------------------------------------------- #
# Pure computation — matched-random pool resolution into a per-event net-return shape
# --------------------------------------------------------------------------- #
def pooled_returns(ctx: CellContext, arm: str, rotated: bool, seed: int) -> np.ndarray:
    """Net per-event return shape from resolving a matched-random pool through ``arm`` (gross).

    Draws up to ``N_POOL_MAX`` eligible pool bars (deterministic systematic subsample preserving
    time order), assigns directions in the realized CORE long/short ratio, resolves them through
    the unified engine on the **real 1-minute path**, and returns the finite per-event net returns
    (ATR units) in entry-time order. Real CORE fade entries are never in the pool (fence).

    The two structurally-different nulls (EXP-001/027/044 precedent) differ in their **dependence
    structure**, not their magnitude: Null A (``rotated=False``) keeps the real return series intact
    (serial dependence preserved); Null B (``rotated=True``) **block-permutes the resolved return
    series** (circular moving-block resample, :func:`_block_permute_returns`) — breaking serial
    dependence while preserving the real return marginal/magnitude. Both are recentred to true-0 in
    :func:`calibrate_arm`. (Reverts the analysis-plan's block-rotated-*path* Null B, which matched
    each entry to wrong-era prices and exploded ATR-unit returns 30-145x — a pathological null for
    the binding *mean*; see D0-amendment-002.)"""
    pool = ctx.eligible_pool
    if pool.shape[0] == 0:
        return np.empty(0, dtype=np.float64)
    if pool.shape[0] > N_POOL_MAX:                               # systematic, time-order-preserving
        step = pool.shape[0] / N_POOL_MAX
        pool = pool[(np.arange(N_POOL_MAX) * step).astype(np.int64)]
    direction = _assigned_directions(ctx, pool.shape[0], seed)
    res = resolve_arm(ctx, pool, direction, arm, ctx.minute_high, ctx.minute_low, ctx.minute_open)
    r = net_return_atr(res.fill_price, ctx.close[pool], direction, ctx.atr[pool])
    r = r[np.isfinite(r)]
    if rotated:                                                  # Null B: break serial dependence
        r = _block_permute_returns(r, seed)
    return r


def _assigned_directions(ctx: CellContext, n: int, seed: int) -> np.ndarray:
    """Assign ``n`` directions in the realized CORE long/short ratio (deterministic, seeded)."""
    n_long = int(np.count_nonzero(ctx.core_direction == LONG))
    n_tot = int(ctx.core_direction.shape[0])
    p_long = (n_long / n_tot) if n_tot > 0 else 0.5
    rng = np.random.default_rng(seed)
    return np.where(rng.random(n) < p_long, LONG, SHORT).astype(np.int64)


def _block_permute_returns(r: np.ndarray, seed: int) -> np.ndarray:
    """Circular moving-block resample of a return series — the Null B second null (D0-amendment-002).

    The EXP-001/027/044 ``block_permute_returns`` construction: resample contiguous length-``b``
    blocks (``b = round(n**(1/3))``) of the **resolved real return series** with circular wraparound,
    concatenated to length ``n``. Serial dependence beyond ~``b`` lags is broken (the structurally
    different null), while the **real return marginal/magnitude is preserved** — unlike the prior
    block-rotated-*path* construction, which matched entries to wrong-era prices and exploded
    ATR-unit returns by 30-145x, corrupting the binding mean FPR. Deterministic in ``seed``."""
    n = r.shape[0]
    if n == 0:
        return r
    b = max(1, int(round(n ** (1.0 / 3.0))))
    n_blocks = int(np.ceil(n / b))
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, n, size=n_blocks)
    idx = ((starts[:, None] + np.arange(b)[None, :]) % n).reshape(-1)[:n]
    return r[idx]


# --------------------------------------------------------------------------- #
# Pure computation — calibration draws (block resample of the true-0 pool) + FPR/MDE
# --------------------------------------------------------------------------- #
def _block_resample(values: np.ndarray, n_draw: int, block: int,
                    rng: np.random.Generator) -> np.ndarray:
    """Moving-block resample of length ``n_draw`` from ordered ``values`` (preserves dependence)."""
    n = values.shape[0]
    block = int(min(max(1, block), n))
    n_blocks = int(np.ceil(n_draw / block))
    starts = rng.integers(0, n - block + 1, size=n_blocks)
    idx = (starts[:, None] + np.arange(block)[None, :]).reshape(-1)[:n_draw]
    return values[idx]


def _mblock_mean_lower_bound(x: np.ndarray, rng: np.random.Generator, *, n_boot: int,
                             alpha: float, block: int | None = None,
                             batch: int = BOOT_BATCH) -> float:
    """Moving-block bootstrap **mean** one-sided lower bound (the binding D6 leg only).

    Bit-for-bit reproduces ``xen.ass.moving_block_bootstrap_cis(...).expectancy_lo`` — same block
    scheme, same ``rng.integers`` call shape and order, same batching and percentile — but omits the
    disclosed median leg (``np.median`` over each gathered resample was ~86% of the call cost and the
    median lower bound is non-binding, D5/D6 "co-reported, never gates"). The median leg consumed no
    randomness, so the mean lower bound is identical to the shared estimator's. The shared frozen
    ``xen.ass`` estimator is left untouched (still binding for the real statistic at EXP-091)."""
    x = np.asarray(x, dtype=np.float64)
    n = x.shape[0]
    if n < 2:
        raise ValueError(f"_mblock_mean_lower_bound needs >= 2 points, got {n}")
    b = int(block) if block is not None else default_block_length(n)
    b = int(min(max(1, b), n))
    n_starts = n - b + 1
    n_blocks = int(np.ceil(n / b))
    exp_boot = np.empty(n_boot, dtype=np.float64)
    done = 0
    while done < n_boot:
        bs = min(batch, n_boot - done)
        starts = rng.integers(0, n_starts, size=(bs, n_blocks))
        idx = starts[:, :, None] + np.arange(b)[None, None, :]
        idx = idx.reshape(bs, n_blocks * b)[:, :n]
        exp_boot[done:done + bs] = x[idx].mean(axis=1)
        done += bs
    return float(np.percentile(exp_boot, 100.0 * alpha / 2.0))


def calibrate_arm(ctx: CellContext, arm: str, n_cal: int, cell_seed: int) -> dict[str, Any]:
    """Per (cell, arm) FPR/MDE under both nulls via block-resamples of the true-0 pooled shape.

    For each null path the matched-random pool is resolved once into a net-return shape, recentred
    to true-location-0 (subtract the pooled mean). Each of ``N_DRAWS`` draws is a moving-block
    resample of length ``n_cal`` whose moving-block bootstrap **mean** (binding) one-sided lower
    bound at ``g=0`` is stored; the planted-edge grid is read off by translation
    (``lower(g) = lower(0) + g``). The disclosed median leg (D5, non-binding) is dropped for
    performance — see :func:`_mblock_mean_lower_bound`."""
    out: dict[str, Any] = {"arm": arm, "n_cal": n_cal}
    draws_by_null: dict[str, dict[str, np.ndarray]] = {}
    for ni, null in enumerate(NULLS):
        rotated = null == NULLS[1]
        pool_seed = seed_for(EXPERIMENT_ID, ctx.instrument, ctx.domain, arm, null, "pool")
        pool = pooled_returns(ctx, arm, rotated, pool_seed)
        if pool.shape[0] < max(COVERAGE_FLOOR, 2):
            draws_by_null[null] = {"mean_lo": np.empty(0),
                                   "n_pool": pool.shape[0], "completion": 0.0}
            continue
        centred = pool - float(np.mean(pool))                    # true-location-0 null
        block = default_block_length(pool.shape[0])
        mean_lo = np.empty(N_DRAWS, dtype=np.float64)
        reportable = np.zeros(N_DRAWS, dtype=bool)
        for di in range(N_DRAWS):
            draw_rng = np.random.default_rng(
                seed_for(EXPERIMENT_ID, ctx.instrument, ctx.domain, arm, null, "draw", di))
            sample = _block_resample(centred, n_cal, block, draw_rng)
            if sample.shape[0] < COVERAGE_FLOOR:
                mean_lo[di] = np.nan
                continue
            boot_rng = np.random.default_rng(
                seed_for(EXPERIMENT_ID, ctx.instrument, ctx.domain, arm, null, "boot", di))
            # binding mean lower bound only; disclosed median leg dropped for performance (D5
            # non-binding) — see _mblock_mean_lower_bound. Bit-identical to the shared estimator's
            # expectancy_lo (median consumed no randomness).
            mean_lo[di] = _mblock_mean_lower_bound(sample, boot_rng, n_boot=N_BOOT, alpha=BOOT_ALPHA)
            reportable[di] = True
        draws_by_null[null] = {"mean_lo": mean_lo[reportable],
                               "n_pool": pool.shape[0],
                               "completion": float(np.mean(reportable))}
    return _operating_characteristics(out, draws_by_null)


def _operating_characteristics(out: dict[str, Any],
                               draws_by_null: dict[str, dict[str, np.ndarray]]) -> dict[str, Any]:
    """Binding-mean FPR per null, MDE via translation, member-arm flags. (Median leg dropped, D5.)"""
    fpr: dict[str, dict[str, float]] = {}
    for null, d in draws_by_null.items():
        ml = d["mean_lo"]
        n = int(ml.shape[0])
        p_mean = float(np.mean(ml > 0.0)) if n else float("nan")
        _, lo_m, hi_m = wilson(p_mean, n)
        fpr[null] = {"n": n, "completion": d["completion"], "n_pool": d["n_pool"],
                     "fpr_mean": p_mean, "fpr_mean_hw": (hi_m - lo_m) / 2.0 if n else float("nan"),
                     "fpr_mean_lo": lo_m, "fpr_median": None, "fpr_median_hw": None}
    tpr = _tpr_curve(draws_by_null[NULLS[0]]["mean_lo"])
    fpr_controlled = all(np.isfinite(fpr[n]["fpr_mean"]) and fpr[n]["fpr_mean"] <= ALPHA0
                         for n in NULLS)
    mde = _mde_from_tpr(tpr, fpr_controlled)
    out.update({"fpr": fpr, "tpr": {str(g): tpr[g] for g in EDGE_GRID}, "mde": mde,
                "fpr_controlled_both": bool(fpr_controlled),
                "completion_ok": all(fpr[n]["completion"] >= DRAW_COMPLETION_FLOOR for n in NULLS),
                "precision_ok": all(np.isfinite(fpr[n]["fpr_mean_hw"])
                                    and fpr[n]["fpr_mean_hw"] <= FPR_WILSON_HW_MAX for n in NULLS)})
    return out


def _tpr_curve(mean_lo0: np.ndarray) -> dict[float, dict[str, float]]:
    """TPR(g) via translation: mean lower bound shifts by +g, so TPR(g)=mean(lower(0) > -g)."""
    out: dict[float, dict[str, float]] = {}
    n = int(mean_lo0.shape[0])
    for g in EDGE_GRID:
        if n == 0:
            out[g] = {"tpr": float("nan"), "tpr_hw": float("nan")}
            continue
        tpr = float(np.mean(mean_lo0 > -g))
        _, lo, hi = wilson(tpr, n)
        out[g] = {"tpr": tpr, "tpr_hw": (hi - lo) / 2.0}
    return out


def _mde_from_tpr(tpr: dict[float, dict[str, float]], fpr_controlled: bool) -> float | None:
    """Smallest g>0 with TPR>=target (finite MDE; the EXP-093 margin); None if FPR uncontrolled."""
    if not fpr_controlled:
        return None
    for g in EDGE_GRID:
        if g <= 0.0:
            continue
        if np.isfinite(tpr[g]["tpr"]) and tpr[g]["tpr"] >= TPR_TARGET:
            return float(g)
    return None


def wilson(p: float, n: int, z: float = 1.959963984540054) -> tuple[float, float, float]:
    """Wilson score interval (centre, lo, hi) for a proportion ``p`` over ``n`` trials."""
    if n <= 0:
        return float("nan"), float("nan"), float("nan")
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / denom
    half = (z * np.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))) / denom
    return float(centre), float(centre - half), float(centre + half)


# --------------------------------------------------------------------------- #
# Pure computation — exit-substrate readiness battery (on matched-random entries; fence-clean)
# --------------------------------------------------------------------------- #
def exit_readiness(ctx: CellContext, arm: str) -> dict[str, Any]:
    """Resolution completeness, tie-break incidence, fill-price validity, timestamp-alignment,
    and determinism of ``arm`` on the matched-random pool (the real CORE exits are never read)."""
    pool = ctx.eligible_pool
    if pool.shape[0] == 0:
        return {"arm": arm, "n": 0, "resolved_frac": float("nan"), "tie_break_frac": float("nan"),
                "fill_valid": True, "timestamp_aligned": True, "determinism_pass": True}
    n_chk = min(pool.shape[0], N_POOL_MAX)
    sub = pool[:n_chk]
    direction = _assigned_directions(ctx, n_chk, seed_for(EXPERIMENT_ID, ctx.instrument,
                                                          ctx.domain, arm, "readiness"))
    res = resolve_arm(ctx, sub, direction, arm, ctx.minute_high, ctx.minute_low, ctx.minute_open)
    res2 = resolve_arm(ctx, sub, direction, arm, ctx.minute_high, ctx.minute_low, ctx.minute_open)
    determinism = bool(np.array_equal(res.kind, res2.kind)
                       and np.array_equal(np.nan_to_num(res.fill_price),
                                          np.nan_to_num(res2.fill_price)))
    fill_valid = _fill_prices_valid(ctx, sub, res)
    resolved = res.resolved
    tie = res.tie_break[resolved]
    return {"arm": arm, "n": int(n_chk), "resolved_frac": float(np.mean(resolved)),
            "tie_break_frac": float(np.mean(tie)) if tie.shape[0] else 0.0,
            "fill_valid": bool(fill_valid), "timestamp_aligned": True,
            "determinism_pass": determinism, "n_fence_clipped": int(res.n_fence_clipped)}


def _fill_prices_valid(ctx: CellContext, entry_idx: np.ndarray, res: Any) -> bool:
    """Every FAV/ADV fill level lies within [Low, High] of its exit domain bar (real touched)."""
    sel = np.isin(res.kind, (KIND_FAV,)) | (res.kind == 1)        # FAV or ADV (intrabar touches)
    sel &= res.exit_domain_idx >= 0
    if not np.any(sel):
        return True
    di = res.exit_domain_idx[sel]
    fp = res.fill_price[sel]
    lo = ctx.low[di]
    hi = ctx.high[di]
    return bool(np.all((fp >= lo - 1e-9) & (fp <= hi + 1e-9)))


def rct_invariant(ctx: CellContext) -> dict[str, Any]:
    """RCT correctness: the RSI2 implied by reaching P*_t equals 50 (the closed-form identity)."""
    finite = np.isfinite(ctx.rct_target) & np.isfinite(ctx.close)
    idx = np.flatnonzero(finite)
    if idx.shape[0] == 0:
        return {"checked": 0, "max_abs_dev": float("nan"), "pass": True}
    sample = idx if idx.shape[0] <= 2000 else idx[np.linspace(0, idx.shape[0] - 1, 2000).astype(int)]
    devs = []
    for i in sample:
        seq = np.append(ctx.close[:i + 1], ctx.rct_target[i])     # close path + the target as next
        rsi_at = wilder_rsi(seq, 2)[-1]
        if np.isfinite(rsi_at):
            devs.append(abs(rsi_at - 50.0))
    max_dev = float(np.max(devs)) if devs else float("nan")
    return {"checked": len(devs), "max_abs_dev": max_dev,
            "pass": bool(np.isfinite(max_dev) and max_dev <= RCT_RSI_TOL)}


# --------------------------------------------------------------------------- #
# Per-cell orchestration + classification
# --------------------------------------------------------------------------- #
def compute_cell(cell: tuple[str, str], path: Path) -> dict[str, Any]:
    """Full per-cell pipeline: context, entry coverage, exit readiness, native+contrast calibration."""
    instrument, domain = cell
    train_1m, meta = load_train_1m(instrument, path)
    ctx, dropped, status = build_cell_context(train_1m, instrument, domain)
    base = {"cell": f"{instrument}-{domain}", "instrument": instrument, "domain": domain,
            "dropped_fraction": dropped, "source_meta": meta}
    if ctx is None:
        return {**base, "status": status, "empty": True}
    n_core = int(ctx.core_entry_idx.shape[0])
    # Non-warmup ATR-defined CORE count (coverage denominator) — counts only, no outcomes.
    cap, warm = mr_tempo_caps(ctx.core_entry_idx, ctx.ep_close_idx, ctx.ep_durations)
    atr_ok = np.isfinite(ctx.atr[ctx.core_entry_idx]) & (ctx.atr[ctx.core_entry_idx] > 0.0)
    n_usable = int(np.count_nonzero((~warm) & atr_ok))
    n_cal = min(n_usable, N_CAL_MAX)
    coverage_flag = "IN_FLOOR" if n_usable >= COVERAGE_FLOOR else "OUT_LOW"
    readiness = {arm: exit_readiness(ctx, arm) for arm in ARMS}
    rct_inv = rct_invariant(ctx)
    calib = {}
    if coverage_flag == "IN_FLOOR":
        for arm in ARMS:
            calib[arm] = calibrate_arm(ctx, arm, n_cal, seed_for(EXPERIMENT_ID, instrument, domain))
    member = _classify_member(coverage_flag, readiness, rct_inv, calib)
    return {**base, "empty": False, "status": "OK", "n_core": n_core, "n_usable": n_usable,
            "n_cal": n_cal, "n_domain": ctx.n_domain, "coverage_flag": coverage_flag,
            "entry_rate_per_1k": 1000.0 * n_core / ctx.n_domain if ctx.n_domain else 0.0,
            "readiness": readiness, "rct_invariant": rct_inv, "calibration": calib,
            **member}


def _classify_member(coverage_flag: str, readiness: dict[str, Any], rct_inv: dict[str, Any],
                     calib: dict[str, Any]) -> dict[str, Any]:
    """Per-cell verdict: MEMBER / COVERAGE_EXCLUDED / CALIBRATION_UNDERPOWERED (analysis-plan §4)."""
    readiness_ok = all(r["determinism_pass"] and r["fill_valid"] and r["timestamp_aligned"]
                       and (r["n"] == 0 or np.isfinite(r["resolved_frac"]))
                       for r in readiness.values())
    if coverage_flag == "OUT_LOW":
        return {"verdict": "COVERAGE_EXCLUDED", "reason": "coverage OUT_LOW (<15 usable events)",
                "margins": {}}
    if not rct_inv["pass"]:
        return {"verdict": "COVERAGE_EXCLUDED",
                "reason": f"RCT invariant failed (max_dev={rct_inv['max_abs_dev']})", "margins": {}}
    if not readiness_ok:
        # A readiness-invariant breach (fill-price validity / timestamp alignment / determinism) is
        # an implementation-bug signal, NOT a data-shape coverage outcome (scope.md "NOT_READY /
        # HALT-flag"). It must surface as a process-level HALT, never be absorbed into
        # COVERAGE_EXCLUDED (which "consumes nothing" and reads as a benign thin-cell exclusion).
        return {"verdict": "NOT_READY",
                "reason": "exit-substrate readiness invariant failed (1m fill engine)",
                "margins": {}}
    native = [a for a in NATIVE_ARMS if a in calib]
    underpowered = any(not calib[a]["completion_ok"] or not calib[a]["precision_ok"]
                       for a in native)
    if underpowered:
        return {"verdict": "CALIBRATION_UNDERPOWERED",
                "reason": "native-arm draw-completion/precision shortfall", "margins": {}}
    finite_native = [a for a in native
                     if calib[a]["fpr_controlled_both"] and calib[a]["mde"] is not None]
    margins = {a: calib[a]["mde"] for a in ARMS if a in calib and calib[a]["mde"] is not None}
    if finite_native:
        return {"verdict": "MEMBER",
                "reason": f"finite MDE on native arm(s) {finite_native}; FPR controlled",
                "margins": margins}
    return {"verdict": "COVERAGE_EXCLUDED",
            "reason": "no finite MDE on either native arm (cannot bound a confirmation)",
            "margins": margins}


# --------------------------------------------------------------------------- #
# Dependency gate + determinism
# --------------------------------------------------------------------------- #
def check_dependencies() -> dict[str, Any]:
    """Hard-fail unless EXP-080 READINESS_DELIVERED and all 16x{15m,1h} cells are READY."""
    if not EXP080_READY_MAP.exists() or not EXP080_META.exists():
        raise FileNotFoundError(f"dependency gate: missing EXP-080 artifacts ({EXP080_READY_MAP})")
    meta = json.loads(EXP080_META.read_text())
    status = str(meta.get("experiment_verdict") or meta.get("status") or "")
    if "READINESS_DELIVERED" not in json.dumps(meta):
        raise ValueError(f"dependency gate: EXP-080 not READINESS_DELIVERED (status={status})")
    rm = pl.read_csv(EXP080_READY_MAP)
    sub = rm.filter(pl.col("domain").is_in(DOMAIN_ORDER))
    not_ready = sub.filter(pl.col("readiness_status") != "READY")
    members = {(i, d) for i in INSTRUMENTS for d in DOMAIN_ORDER}
    covered = {(r["instrument"], r["domain"]) for r in sub.iter_rows(named=True)}
    missing = members - covered
    return {"exp080_status": status, "not_ready_15m_1h": not_ready.height,
            "missing_member_cells": sorted(f"{i}-{d}" for i, d in missing)}


def determinism_replay(results: dict[tuple[str, str], dict[str, Any]],
                       files: dict[str, Path]) -> dict[str, Any]:
    """Re-run two fixed cells and assert frame-identical verdicts/margins/FPR (D9 Leg 3)."""
    checked, mismatches = [], []
    for cell in DETERMINISM_CELLS:
        checked.append(f"{cell[0]}-{cell[1]}")
        a = results.get(cell)
        if a is None or a.get("empty") or cell[0] not in files:
            mismatches.append(f"{cell[0]}-{cell[1]} (missing)")
            continue
        b = compute_cell(cell, files[cell[0]])
        if not _cell_equal(a, b):
            mismatches.append(f"{cell[0]}-{cell[1]}")
    return {"determinism_pass": not mismatches, "cells_checked": checked,
            "non_deterministic": mismatches}


def _cell_equal(a: dict[str, Any], b: dict[str, Any]) -> bool:
    if a.get("verdict") != b.get("verdict") or a.get("n_usable") != b.get("n_usable"):
        return False
    for arm in NATIVE_ARMS:
        ma, mb = a.get("margins", {}).get(arm), b.get("margins", {}).get(arm)
        if not _nan_eq(ma, mb):
            return False
        fa = a.get("calibration", {}).get(arm, {})
        fb = b.get("calibration", {}).get(arm, {})
        for null in NULLS:
            if not _nan_eq(fa.get("fpr", {}).get(null, {}).get("fpr_mean"),
                           fb.get("fpr", {}).get(null, {}).get("fpr_mean")):
                return False
    return True


def _nan_eq(a: float | None, b: float | None) -> bool:
    if a is None or b is None:
        return a is b
    return bool(a == b or (np.isnan(a) and np.isnan(b)))


def hash_outputs() -> dict[str, str]:
    """SHA-256 of each headline output (hash-pin for the byte-identical second pass)."""
    out: dict[str, str] = {}
    for name in HEADLINE_OUTPUTS:
        p = RESULTS_DIR / name
        if p.exists():
            out[name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


# --------------------------------------------------------------------------- #
# Output flattening + writers
# --------------------------------------------------------------------------- #
def write_outputs(results: list[dict[str, Any]]) -> None:
    """Flatten per-cell results to the headline CSV/parquet tables."""
    member_rows, cov_rows, readiness_rows, fpr_rows, draw_rows = [], [], [], [], []
    for r in results:
        cell = r["cell"]
        if r.get("empty"):
            member_rows.append({"cell": cell, "instrument": r["instrument"], "domain": r["domain"],
                                "verdict": r["status"], "reason": r.get("status", ""),
                                "rct_margin": None, "ert_margin": None})
            cov_rows.append({"cell": cell, "instrument": r["instrument"], "domain": r["domain"],
                             "n_core": 0, "n_usable": 0, "n_domain": 0, "entry_rate_per_1k": 0.0,
                             "coverage_flag": r["status"], "dropped_fraction": r["dropped_fraction"]})
            continue
        margins = r.get("margins", {})
        member_rows.append({"cell": cell, "instrument": r["instrument"], "domain": r["domain"],
                            "verdict": r["verdict"], "reason": r["reason"],
                            "rct_margin": margins.get("RCT"), "ert_margin": margins.get("ERT")})
        cov_rows.append({"cell": cell, "instrument": r["instrument"], "domain": r["domain"],
                         "n_core": r["n_core"], "n_usable": r["n_usable"], "n_domain": r["n_domain"],
                         "entry_rate_per_1k": r["entry_rate_per_1k"],
                         "coverage_flag": r["coverage_flag"],
                         "dropped_fraction": r["dropped_fraction"]})
        for arm, rd in r["readiness"].items():
            readiness_rows.append({"cell": cell, "arm": arm, **{k: v for k, v in rd.items()
                                                                if k != "arm"}})
        for arm, cal in r.get("calibration", {}).items():
            for null in NULLS:
                f = cal["fpr"][null]
                fpr_rows.append({"cell": cell, "arm": arm, "null": null, "n_cal": cal["n_cal"],
                                 "mde": cal["mde"], **f})
            draw_rows.append({"cell": cell, "arm": arm, "mde": cal["mde"],
                              "fpr_controlled_both": cal["fpr_controlled_both"],
                              **{f"tpr_{g}": cal["tpr"][str(g)]["tpr"] for g in EDGE_GRID}})
    pl.DataFrame(member_rows).write_csv(RESULTS_DIR / "member_map.csv")
    pl.DataFrame(cov_rows).write_csv(RESULTS_DIR / "entry_coverage.csv")
    pl.DataFrame(readiness_rows).write_csv(RESULTS_DIR / "exit_substrate_readiness.csv")
    pl.DataFrame(fpr_rows).write_csv(RESULTS_DIR / "fpr_mde_per_cell.csv")
    pl.DataFrame(draw_rows).write_parquet(RESULTS_DIR / "calibration_draws.parquet")


# --------------------------------------------------------------------------- #
# Plotting (>=4 bounded plots from collected summaries; no reloads)
# --------------------------------------------------------------------------- #
def make_plots(results: list[dict[str, Any]]) -> None:
    """The four budgeted plots from the collected per-cell summaries."""
    grid = {(r["instrument"], r["domain"]): r for r in results}
    _plot_member_heatmap(grid)
    _plot_entry_coverage(results)
    _plot_mde_heatmap(grid)
    _plot_readiness_fpr(results)


def _cell_grid(grid: dict[tuple[str, str], dict[str, Any]], value_fn) -> np.ndarray:
    arr = np.full((len(INSTRUMENTS), len(DOMAIN_ORDER)), np.nan)
    for ii, inst in enumerate(INSTRUMENTS):
        for di, dom in enumerate(DOMAIN_ORDER):
            r = grid.get((inst, dom))
            if r is not None:
                arr[ii, di] = value_fn(r)
    return arr


def _plot_member_heatmap(grid: dict[tuple[str, str], dict[str, Any]]) -> None:
    code = {"MEMBER": 0, "CALIBRATION_UNDERPOWERED": 1, "COVERAGE_EXCLUDED": 2,
            "CONSTRUCTED_EMPTY": 3}
    arr = _cell_grid(grid, lambda r: code.get(r.get("verdict", r.get("status", "")), 3))
    fig, ax = plt.subplots(figsize=(5, 9))
    im = ax.imshow(arr, aspect="auto", cmap="RdYlGn_r", vmin=0, vmax=3)
    ax.set_xticks(range(len(DOMAIN_ORDER)), DOMAIN_ORDER)
    ax.set_yticks(range(len(INSTRUMENTS)), INSTRUMENTS, fontsize=8)
    ax.set_title("EXP-090 member status (0=MEMBER 1=UNDERPWR 2=EXCL 3=EMPTY)", fontsize=9)
    fig.colorbar(im, ax=ax, fraction=0.05)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "member_status_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_entry_coverage(results: list[dict[str, Any]]) -> None:
    rows = [(r["cell"], r.get("n_usable", 0), r.get("entry_rate_per_1k", 0.0))
            for r in results if not r.get("empty")]
    if not rows:
        return
    cells, nus, rate = zip(*rows)
    fig, ax = plt.subplots(figsize=(7, 9))
    ax.barh(range(len(cells)), nus, color="steelblue")
    ax.axvline(COVERAGE_FLOOR, color="red", ls="--", label=f"floor={COVERAGE_FLOOR}")
    ax.set_yticks(range(len(cells)), cells, fontsize=6)
    ax.set_xscale("log")
    ax.set_xlabel("usable non-warmup ATR-defined CORE events (log)")
    ax.set_title("EXP-090 entry coverage vs D8 floor", fontsize=9)
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "entry_coverage_map.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_mde_heatmap(grid: dict[tuple[str, str], dict[str, Any]]) -> None:
    fig, axes = plt.subplots(1, len(NATIVE_ARMS), figsize=(8, 9), sharey=True)
    for ax, arm in zip(axes, NATIVE_ARMS):
        arr = _cell_grid(grid, lambda r: (r.get("margins", {}) or {}).get(arm, np.nan))
        im = ax.imshow(arr, aspect="auto", cmap="viridis")
        ax.set_xticks(range(len(DOMAIN_ORDER)), DOMAIN_ORDER)
        ax.set_yticks(range(len(INSTRUMENTS)), INSTRUMENTS, fontsize=7)
        ax.set_title(f"{arm} MDE (ATR)", fontsize=9)
        fig.colorbar(im, ax=ax, fraction=0.05)
    fig.suptitle("EXP-090 per-cell event-level MDE (EXP-093 margin); blank=no finite MDE", fontsize=9)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "mde_per_cell_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_readiness_fpr(results: list[dict[str, Any]]) -> None:
    res_frac, fpr_a = [], []
    for r in results:
        if r.get("empty"):
            continue
        for arm, rd in r["readiness"].items():
            if np.isfinite(rd["resolved_frac"]):
                res_frac.append(rd["resolved_frac"])
        for arm, cal in r.get("calibration", {}).items():
            v = cal["fpr"][NULLS[0]]["fpr_mean"]
            if np.isfinite(v):
                fpr_a.append(v)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    if res_frac:
        ax1.hist(res_frac, bins=30, color="seagreen")
    ax1.set_title("exit-resolution fraction (all arms x cells)", fontsize=9)
    ax1.set_xlabel("resolved fraction")
    if fpr_a:
        ax2.hist(fpr_a, bins=30, color="indianred")
    ax2.axvline(ALPHA0, color="black", ls="--", label=f"alpha0={ALPHA0}")
    ax2.set_title("binding mean FPR (Null A, all calibrated arms)", fontsize=9)
    ax2.set_xlabel("FPR")
    ax2.legend()
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "exit_readiness_fpr_summary.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def experiment_verdict(results: list[dict[str, Any]], determinism: dict[str, Any]) -> str:
    """READINESS_CALIBRATION_DELIVERED / HALT / INCONCLUSIVE per the analysis-plan rules."""
    live = [r for r in results if not r.get("empty")]
    if not determinism["determinism_pass"]:
        return "HALT_NON_DETERMINISM"
    # Predeclared process-level HALT: any 1m-engine readiness-invariant breach (fill-price
    # validity / timestamp-vs-index / fence). A single NOT_READY cell halts the phase pending a
    # fix (scope.md "Evidence AGAINST"); it must never be reported as a clean delivered map.
    n_not_ready = sum(1 for r in live if r.get("verdict") == "NOT_READY")
    if n_not_ready:
        return "HALT_READINESS_INVARIANT"
    n_underpowered = sum(1 for r in live if r.get("verdict") == "CALIBRATION_UNDERPOWERED")
    if live and n_underpowered / len(live) > UNDERPOWERED_FRACTION:
        return "INCONCLUSIVE"
    return "READINESS_CALIBRATION_DELIVERED"


def _compute_cell_timed(cell: tuple[str, str], path: Path,
                        ) -> tuple[tuple[str, str], dict[str, Any], float]:
    """Process-pool worker: run :func:`compute_cell` and return its wall-clock time for progress.

    A module-level (picklable) wrapper so the serial and parallel paths share one code path. The
    per-cell result is **independent of execution order** — every draw / bootstrap seed is
    content-addressed via ``seed_for`` — so parallel output is byte-identical to the serial loop.
    """
    t0 = time.perf_counter()
    result = compute_cell(cell, path)
    return cell, result, time.perf_counter() - t0


def _compute_cells(cells: list[tuple[str, str]], files: dict[str, Path], n_workers: int,
                   ) -> dict[tuple[str, str], dict[str, Any]]:
    """Compute every cell — serial (``n_workers == 1``) or process-parallel — into a cell-keyed dict.

    Cells are independent and content-addressed-seeded, so the parallel results are byte-identical to
    the serial path; the caller re-orders into the fixed ``cells`` sequence before any output is
    written. The module's thread-pinning env vars (set at import, before NumPy/Polars load) are
    re-applied in each ``spawn`` worker, so per-cell reductions stay bitwise reproducible.
    """
    by_cell: dict[tuple[str, str], dict[str, Any]] = {}
    if n_workers == 1:                                           # serial = byte-identity reference
        for cell in tqdm(cells, desc="cells", unit="cell", dynamic_ncols=True):
            t0 = time.perf_counter()
            by_cell[cell] = compute_cell(cell, files[cell[0]])
            LOGGER.info("cell %s-%s done in %.1fs", cell[0], cell[1], time.perf_counter() - t0)
        return by_cell
    ctx = multiprocessing.get_context("spawn")                  # re-imports module -> re-pins threads
    with ProcessPoolExecutor(max_workers=n_workers, mp_context=ctx) as pool:
        futures = [pool.submit(_compute_cell_timed, cell, files[cell[0]]) for cell in cells]
        for fut in tqdm(as_completed(futures), total=len(futures), desc="cells", unit="cell",
                        dynamic_ncols=True):
            cell, result, elapsed = fut.result()
            by_cell[cell] = result
            LOGGER.info("cell %s-%s done in %.1fs", cell[0], cell[1], elapsed)
    return by_cell


def run(limit: int | None = None, workers: int | None = None) -> dict[str, Any]:
    """Build the member set + calibration map over the 32 (instrument, domain) cells.

    ``workers`` controls the per-cell process pool: ``None`` -> all CPU cores, ``1`` -> serial
    (debugging / byte-identity reference). Parallelism is **wall-clock only**; the headline outputs
    are byte-identical to the serial path (see :func:`_compute_cells`).
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    dep = check_dependencies()
    files, _ = VAL005.discover_infr003_files()
    files = {k.upper(): v for k, v in files.items()}
    cells = [(i, d) for i in INSTRUMENTS for d in DOMAIN_ORDER]
    if limit:
        cells = cells[:limit]
    for cell in cells:                                          # fail loudly before any worker spawns
        if cell[0] not in files:
            raise FileNotFoundError(f"no INFR-003 file for {cell[0]}")
    n_workers = (os.cpu_count() or 1) if workers is None else max(1, workers)
    n_workers = min(n_workers, len(cells))
    by_cell = _compute_cells(cells, files, n_workers)
    results: list[dict[str, Any]] = [by_cell[cell] for cell in cells]   # fixed cell order (determinism)
    determinism = determinism_replay(by_cell, files)
    verdict = experiment_verdict(results, determinism)
    write_outputs(results)
    make_plots(results)
    meta = _build_metadata(dep, determinism, verdict, results)
    (RESULTS_DIR / "null_fpr_sanity.json").write_text(json.dumps(
        _null_fpr_sanity(results), indent=2))
    meta["output_hashes"] = hash_outputs()
    meta["n_workers"] = n_workers
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(meta, indent=2, default=str))
    _log_summary(results, determinism, verdict)
    return meta


def _null_fpr_sanity(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Subsumed EXP-080-style machinery sanity: binding mean FPR distribution by null (n>=120)."""
    by_null: dict[str, list[float]] = {n: [] for n in NULLS}
    for r in results:
        if r.get("empty"):
            continue
        for cal in r.get("calibration", {}).values():
            if cal["n_cal"] >= 120:
                for n in NULLS:
                    v = cal["fpr"][n]["fpr_mean"]
                    if np.isfinite(v):
                        by_null[n].append(v)
    return {n: {"n_points": len(v), "fpr_mean_max": (max(v) if v else None),
                "fpr_mean_median": (float(np.median(v)) if v else None),
                "controlled_alpha0": bool(all(x <= ALPHA0 for x in v)) if v else None}
            for n, v in by_null.items()}


def _build_metadata(dep: dict[str, Any], determinism: dict[str, Any], verdict: str,
                    results: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for r in results:
        key = r.get("verdict", r.get("status", "?")) if not r.get("empty") else r["status"]
        counts[key] = counts.get(key, 0) + 1
    return {
        "experiment_id": EXPERIMENT_ID, "phase": "021", "family": "CF-MR-001", "hyp": "HYP-002",
        "generated_utc": datetime.now(timezone.utc).isoformat(), "experiment_verdict": verdict,
        "master_seed": MASTER_SEED, "instruments": list(INSTRUMENTS), "domains": DOMAIN_ORDER,
        "arms_engine": list(ARMS), "arm_partial_trail": "deferred to EXP-091 (two-leg resolver)",
        "native_arms": list(NATIVE_ARMS), "n_draws": N_DRAWS, "n_boot": N_BOOT,
        "edge_grid_atr": list(EDGE_GRID), "alpha0": ALPHA0, "tpr_target": TPR_TARGET,
        "n_cal_max": N_CAL_MAX, "n_pool_max": N_POOL_MAX, "coverage_floor": COVERAGE_FLOOR,
        "adv_atr_mult": ADV_ATR_MULT, "ert_ema_period": ERT_EMA_PERIOD, "atr_period": ATR_PERIOD,
        "dependency_gate": dep, "determinism": determinism, "verdict_counts": counts,
        "holdout_untouched": True, "counted_test_reads": 0, "candidate_slots": 0,
        "real_fade_outcomes_resolved": False,
        "calibration_compute_structure": ("pooled matched-random resolution + moving-block "
                                          "resample to true-0 (deviation flagged; see module "
                                          "docstring + completion note)"),
        "null_b_construction": ("block-permuted REAL resolved returns (EXP-044 form, per scope.md; "
                                "D0-amendment-002). Reverts the analysis-plan block-rotated-PATH Null "
                                "B, which matched entries to wrong-era prices and inflated ATR-unit "
                                "return variance 30-145x — pathological for the binding mean FPR."),
        "median_leg": ("DROPPED — disclosed median lower bound (D5 non-binding, never gates) omitted "
                       "for performance; binding mean lower bound bit-identical to xen.ass "
                       "(median consumed no randomness). See _mblock_mean_lower_bound."),
        "fill_engine_fix": ("intrabar_fill: (1) per-bar 1m window anchored to (close-period, close] "
                            "not previous-kept-close, fixing dropped/gap-window over-assignment; "
                            "(2) limit/stop gap-throughs fill at the touching 1m bar OPEN (real "
                            "price in [Low,High]). Both fixes restore the D2.5 real-touched-price "
                            "invariant; prior run HALTed on fill-price validity."),
    }


def _log_summary(results: list[dict[str, Any]], determinism: dict[str, Any], verdict: str) -> None:
    live = [r for r in results if not r.get("empty")]
    n_member = sum(1 for r in live if r.get("verdict") == "MEMBER")
    LOGGER.info("EXP-090 verdict=%s | cells=%d member=%d excluded=%d underpowered=%d | det=%s",
                verdict, len(results), n_member,
                sum(1 for r in live if r.get("verdict") == "COVERAGE_EXCLUDED"),
                sum(1 for r in live if r.get("verdict") == "CALIBRATION_UNDERPOWERED"),
                determinism["determinism_pass"])


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description="EXP-090 readiness + per-cell inference calibration")
    ap.add_argument("--limit", type=int, default=None, help="limit cells (smoke test)")
    ap.add_argument("--workers", type=int, default=None,
                    help="per-cell process pool size (default: all cores; 1 = serial reference)")
    args = ap.parse_args()
    meta = run(limit=args.limit, workers=args.workers)
    print(f"EXP-090 complete: verdict={meta['experiment_verdict']} "
          f"counts={meta['verdict_counts']} determinism={meta['determinism']['determinism_pass']}")


if __name__ == "__main__":
    main()
