"""EXP-062 — MA(20,50)-Substrate Lifetime Availability (Conditioned HA Harami; MFE/MAE).

``CF-HA-HARAMI-001`` / HYP-015 — Phase 015 **lead L2** (**dual conditioning object**). The
EXP-055 (HYP-008) availability read re-derived on the **MA(20,50) substrate**.
Governing design/D0: ``docs/experiments-docs/checkpoints/2026-06-17-015-ma-substrate-
conditioned-harami-full-surface/`` (``design.md`` §3/§4/§5; ``D0-predeclarations.md`` P1-P12;
``D0-amendment-001-dual-parallel-substrate.md``). TRAIN-only, gross; **0 candidate slots,
0 TEST reads**.

**Re-run under D0 Amendment 001 (2026-06-17).** The prior EXP-062 measured a single MA
availability arm labelled *hybrid* but actually conditioning on MA-segment ``/STRONG-STAT`` --
the **native** object. The genuine **hybrid** object (ZigZag-``/STRONG-STAT`` mask x MA lifetime
window) was never computed. This re-run emits **both** objects **individually** (separate arms,
separate matched-random nulls, separate readouts -- never pooled) and supersedes the prior result
in place.

**The question (scope §Question), per object.** Over the **full reversal MA segment** that follows
the conditioned harami (lifetime window ``[entry+1, c2]`` where ``c2`` is the 2nd MA(20,50)
crossover at/after entry), what is the gross, ATR-normalised distribution of lifetime favourable
MFE vs adverse MAE, and -- for each conditioning object individually:

1. is a meaningful favourable move **available** (median-MFE CI_low > 1.0 ATR AND median MFE >
   median MAE -- the EXP-055 ``MOVE_AVAILABLE`` test)?
2. is the room **signal-attributable** (P5) -- does the object's signal arm beat its **own**
   matched-random-on-MA null (``A - RM`` median-MFE difference-bootstrap CI_low > 0)?
3. what does the adverse side look like -- median MAE + the **P4** raw mean / 10% trimmed mean /
   worst-5% tail-share (the L3 downside-bounding input, EXP-063), per object?

The two objects share the same frozen HA-harami detection, the same MA lifetime window, and the
same MA in-progress ``rd``; they differ **only** in the ``/STRONG-STAT`` conditioning filter (P2):

  * **native** ``A_MA_nat`` -- ``/STRONG-STAT`` p75 on the in-progress confirmed **MA segment**;
    population byte-identical to the prior EXP-062 ``A_MA``; **reproduces EXP-055's ``ma_seg`` arm**
    (per-cell m + median MFE + median MAE to ``RECON_TOL``, P12).
  * **hybrid** ``A_MA_hyb`` -- ``/STRONG-STAT`` p75 on the in-progress confirmed **ZigZag move**
    (mask byte-identical to EXP-053/055/061 ``H0``), applied through the MA lifetime window.
    Genuinely new; **no outcome back-reconciliation anchor** (its conditioning mask is the same
    mask that defines the disclosed ``A_ZZ`` population, verified transitively via ``A_ZZ``).

Each object has its **own** matched-random-on-MA null (``RM_MA_nat`` / ``RM_MA_hyb``), matched to
its own qualifying count and excluding its own signal entries, on disjoint dedicated RNG streams.
The native arm/null/contrast RNG purposes are byte-identical to the prior EXP-062 (the hybrid arms
use fresh dedicated purposes), so nothing perturbs the native path. Median binding (P14); the
mean/trim/tail are the **P4 diagnostic** (disclosed, never a gate), per object.

Detection on HA candles; every outcome metric on real prices; MA(20,50) on real close; the
reference band ``{0.5, 1.0}`` ATR is never subtracted. Outputs under ``results/`` and ``plots/``;
created in orchestration. Output is byte-identical for any ``--workers`` value (order-independent
per-cell RNG + fixed merge order). The two objects are never pooled.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Pin per-process native thread pools to 1 BEFORE importing polars/numpy:
# parallelism is process-level (one worker per instrument), so N workers x M
# library threads would oversubscribe the CPU. Aggregation/bootstrap stay
# byte-identical single-threaded (OHLC aggregation is first/max/min/last/integer-
# sum -- order-independent; the bootstrap is numpy resampling, not BLAS).
for _thread_var in ("POLARS_MAX_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                    "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_thread_var, "1")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import polars as pl  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402
from tqdm.auto import tqdm  # noqa: E402

# --------------------------------------------------------------------------- #
# Path setup
# --------------------------------------------------------------------------- #
CODE_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = CODE_DIR.parent
EXPERIMENTS_ROOT = EXPERIMENT_DIR.parent
PROJECT_ROOT = EXPERIMENT_DIR.parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "timebars"
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
# P12 reconciliation anchor: EXP-055 carries the ma_seg (MA-native) + stat (ZigZag) availability arms.
EXP055_PARQUET = EXPERIMENTS_ROOT / "EXP-055" / "results" / "per_cell_availability.parquet"

sys.path.insert(0, str(CODE_DIR))

import availability as av  # noqa: E402
from xen.bar_aggregator import aggregate_ohlc  # noqa: E402
from xen.expectancy import (  # noqa: E402
    InProgressState,
    live_in_progress_state,
    live_strong_stat,
)
from xen.ha_harami import detect_ha_harami  # noqa: E402
from xen.heiken_ashi_generator import generate_heiken_ashi  # noqa: E402
from xen.strong_move import annotate_ha_impulse, find_impulse_runs  # noqa: E402
from xen.zigzag import generate_zigzag, wilder_atr  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (Phase 014-B / 015 D0 frozen; no tuning)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-062"
INSTRUMENTS: list[str] = [
    "BTCUSD", "EURUSD", "USTEC", "XAUUSD", "GBPUSD", "USDJPY", "USDCHF",
    "USDCAD", "AUDUSD", "NZDUSD", "EURJPY", "GBPJPY", "AUDJPY", "US500",
    "US2000", "DE30", "JP225",
]
DOMAINS: dict[str, tuple[int, float | None]] = {
    "5m": (5, None), "15m": (15, 0.90), "30m": (30, 0.90),
    "1h": (60, 0.90), "2h": (120, 0.90), "4h": (240, 0.90),
}
EXCLUDED_CELLS: set[tuple[str, str]] = {("US500", "4h"), ("JP225", "2h"), ("JP225", "4h")}
ANALYSIS_FRACTION = 0.7
TRAIN_FRACTION = 0.7
ATR_PERIOD = 14
ATR_MULT = 1.0                       # P1 ZigZag (hybrid conditioning + disclosed contrast)
MA_FAST, MA_SLOW = 20, 50            # P1 MA-segmentation substrate (binding; fixed, not swept)
POWER_FLOOR = av.POWER_FLOOR         # 30 qualifying events
P11_MIN_CELLS, P11_MIN_INSTR = av.P11_MIN_CELLS, av.P11_MIN_INSTR
P6_MIN_NON_4H = 3                    # P6: >=3 qualifying cells outside the 4h domain
TRIM_FRAC = 0.10                     # P4: 10% symmetric trimmed mean
TAIL_FRAC = 0.05                     # P4: worst-5% (largest excursions) tail-share
RECON_TOL = 1e-9                     # P12 EXP-055 reproduction tolerance
N_BOOT = av.N_BOOT                   # 10_000
BOOT_BATCH = av.BOOT_BATCH           # 2_000
BASE_SEED = 20260616                 # frozen master seed (identical to EXP-055/060/061)
EXCLUDED_FILE_MARKERS = ("analysis70", "analysis_slice", "first70")
# RNG purpose offsets (distinct deterministic per-cell streams; arm/statistic-specific).
# NATIVE arm/null/contrast purposes are byte-identical to the prior EXP-062 (the reconciliation
# population/medians are RNG-independent, but keeping the streams fixed preserves determinism).
RNG_MA_STAT, RNG_MA_STAT_MEAN, RNG_MA_STAT_TRIM = 9000, 9001, 9002       # A_MA_nat (binding native)
RNG_MA_HA, RNG_MA_HA_MEAN, RNG_MA_HA_TRIM = 9100, 9101, 9102             # A_MA_nat /STRONG-HA
RNG_MA_MAD, RNG_MA_MAD_MEAN, RNG_MA_MAD_TRIM = 9200, 9201, 9202          # A_MA_nat MAD
RNG_RM_MA_DRAW, RNG_RM_MA_BOOT = 9300, 9301                              # RM_MA_nat (native null)
RNG_RM_MA_MEAN, RNG_RM_MA_TRIM = 9302, 9303
# HYBRID arms (NEW, D0 Amendment 001): ZigZag-/STRONG-STAT mask x MA lifetime window. Fresh
# dedicated purposes so the native path stays byte-identical.
RNG_MA_HYB, RNG_MA_HYB_MEAN, RNG_MA_HYB_TRIM = 9400, 9401, 9402          # A_MA_hyb (binding hybrid)
RNG_RM_MA_HYB_DRAW, RNG_RM_MA_HYB_BOOT = 9500, 9501                      # RM_MA_hyb (hybrid null)
RNG_RM_MA_HYB_MEAN, RNG_RM_MA_HYB_TRIM = 9502, 9503
RNG_ZZ_STAT, RNG_ZZ_STAT_MEAN, RNG_ZZ_STAT_TRIM = 1000, 1001, 1002      # A_ZZ (disclosed)
RNG_RM_ZZ_DRAW, RNG_RM_ZZ_BOOT = 1100, 1101                             # RM_ZZ (disclosed null)
RNG_RM_ZZ_MEAN, RNG_RM_ZZ_TRIM = 1102, 1103
RNG_CONTRAST_MA_MFE, RNG_CONTRAST_MA_MAE = 5000, 5001                   # A_MA_nat-RM_MA_nat (binding)
RNG_CONTRAST_MA_HYB_MFE, RNG_CONTRAST_MA_HYB_MAE = 5200, 5201           # A_MA_hyb-RM_MA_hyb (binding)
RNG_CONTRAST_ZZ_MFE, RNG_CONTRAST_ZZ_MAE = 5100, 5101                   # A_ZZ-RM_ZZ (disclosed)
# Availability status -> integer code / colour (composition heatmap).
ASTATUS_CODES: dict[str, int] = {
    "MOVE_AVAILABLE": 0, "NOT_AVAILABLE": 1, "NOT_VIABLE_BY_POWER": 2, "EXCLUDED": 3,
}
ASTATUS_COLORS: list[str] = ["#1a9850", "#f46d43", "#cccccc", "#7b3294"]
# Per-object column prefixes (binding signal arms; never pooled).
OBJECTS = ("nat", "hyb")             # native, hybrid
OBJ_ARM = {"nat": "ama_nat", "hyb": "ama_hyb"}
DE30_DISCLOSURE = (
    "DE30 truncated history: broker m1 history ends 2026-01-16; counts derive "
    "from its own realized timeline and are not span-comparable (VAL-003).")
LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class AvailResult:
    """One arm's per-cell lifetime-availability summary + per-event arrays.

    Carries the median (binding) MFE/MAE + CIs, the P4 diagnostic (raw mean CI,
    10% trimmed-mean CI, worst-5% largest-tail share for MFE and MAE), the
    population accounting, and the per-event MFE/MAE arrays (used by the
    matched-random difference bootstrap).
    """

    m: int                          # qualifying (non-censored) events
    median_mfe: float | None
    mfe_ci_low_1s: float | None
    mfe_ci_lo_2s: float | None
    mfe_ci_hi_2s: float | None
    median_mae: float | None
    mae_ci_low_1s: float | None
    mae_ci_lo_2s: float | None
    mae_ci_hi_2s: float | None
    mean_mfe: float | None
    mean_mae: float | None
    # P4 diagnostic (disclosed; never a gate) ---------------------------------
    mfe_mean_ci_low_1s: float | None
    mfe_mean_ci_hi_2s: float | None
    mae_mean_ci_low_1s: float | None
    mae_mean_ci_hi_2s: float | None
    mfe_trim10: float | None
    mae_trim10: float | None
    mfe_trim_ci_low_1s: float | None
    mae_trim_ci_low_1s: float | None
    mfe_tail_share_largest5: float | None
    mae_tail_share_largest5: float | None
    # population accounting ---------------------------------------------------
    n_retained: int                 # events passing the arm's filter
    n_buildable: int                # retained with valid in-progress + finite ATR
    n_censored: int                 # buildable but M_b incomplete in TRAIN
    block_len: int
    draw_count: int                 # matched-random arms: the matched draw target
    mfe: np.ndarray                 # qualifying MFE in entry order
    mae: np.ndarray                 # qualifying MAE in entry order


def _empty_arm() -> AvailResult:
    """A zero-population arm result."""
    return AvailResult(
        0, None, None, None, None, None, None, None, None, None, None,
        None, None, None, None, None, None, None, None, None, None,
        0, 0, 0, 1, 0, np.empty(0), np.empty(0))


# --------------------------------------------------------------------------- #
# I/O helpers (TRAIN-only loader; never sorts/collects the full file)
# --------------------------------------------------------------------------- #
def find_source_file(instrument: str) -> Path:
    """Return the newest full (non-derivative) 1-minute Parquet for one symbol."""
    matches = sorted(
        p for p in DATA_DIR.glob(f"timebars_{instrument.lower()}_*.parquet")
        if not any(marker in p.name for marker in EXCLUDED_FILE_MARKERS)
    )
    if not matches:
        raise FileNotFoundError(f"no 1-minute source file for {instrument} under {DATA_DIR}")
    return matches[-1]


def load_train_1m(instrument: str) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Load exactly the TRAIN 1-minute rows (first 49%) by file-order prefix."""
    path = find_source_file(instrument)
    total_rows = int(pl.scan_parquet(path).select(pl.len()).collect().item())
    analysis_rows = int(total_rows * ANALYSIS_FRACTION)
    train_rows = int(analysis_rows * TRAIN_FRACTION)
    cols = ["Symbol", "OpenTime", "CloseTime", "Open", "High", "Low", "Close", "TickVolume"]
    train = pl.scan_parquet(path).select(cols).slice(0, train_rows).collect()
    if not train.get_column("CloseTime").is_sorted():
        raise RuntimeError(f"{instrument}: TRAIN slice not chronological by CloseTime")
    meta = {
        "source_file": path.name, "total_rows_1m": total_rows,
        "analysis_rows_1m": analysis_rows, "train_rows_1m": train_rows,
        "train_end_ts": str(train.get_column("CloseTime")[-1]),
        "train_end_epoch_s": int(train.get_column("CloseTime").dt.epoch("s")[-1]),
    }
    return train, meta


def load_exp055_anchor() -> dict[tuple[str, str], dict[str, Any]]:
    """Load EXP-055's per-cell ma_seg (MA-native) + stat (ZigZag) arms for P12 reconciliation.

    Returns, per (instrument, domain), the EXP-055 ``maseg``/``stat`` qualifying
    count + median MFE + median MAE (the availability-semantics anchor). The native
    ``A_MA_nat`` arm reconciles to ``maseg`` and the disclosed ``A_ZZ`` to ``stat``.
    A missing/empty anchor is SUBSTRATE/METHOD_DEFECT (P12).
    """
    if not EXP055_PARQUET.exists():
        return {}
    df = pl.read_parquet(EXP055_PARQUET)
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for row in df.filter(pl.col("member")).iter_rows(named=True):
        out[(row["instrument"], row["domain"])] = {
            "maseg": {"m": row.get("maseg_m"), "median_mfe": row.get("maseg_median_mfe"),
                      "median_mae": row.get("maseg_median_mae")},
            "stat": {"m": row.get("stat_m"), "median_mfe": row.get("stat_median_mfe"),
                     "median_mae": row.get("stat_median_mae")},
        }
    return out


# --------------------------------------------------------------------------- #
# Pure computation — domain / substrate / harami alignment (EXP-055 pattern)
# --------------------------------------------------------------------------- #
def build_domain(
    train_1m: pl.DataFrame, period_minutes: int, min_coverage: float | None,
    train_end_epoch: int,
) -> pl.DataFrame:
    """Aggregate one domain on the TRAIN slice and fence to the TRAIN edge."""
    bars = aggregate_ohlc(train_1m, period_minutes=period_minutes, min_coverage=min_coverage)
    return bars.filter(pl.col("CloseTime").dt.epoch("s") <= train_end_epoch)


def real_ohlc(bars: pl.DataFrame) -> dict[str, np.ndarray]:
    """Real-bar OHLC component arrays + CloseTime epochs (real prices only)."""
    return {
        "open": bars.get_column("Open").to_numpy().astype(np.float64),
        "high": bars.get_column("High").to_numpy().astype(np.float64),
        "low": bars.get_column("Low").to_numpy().astype(np.float64),
        "close": bars.get_column("Close").to_numpy().astype(np.float64),
        "epoch": bars.get_column("CloseTime").dt.epoch("s").to_numpy().astype(np.int64),
    }


def harami_entry_indices(
    bars: pl.DataFrame, bar_epoch: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, pl.DataFrame]:
    """Detect HA haramis and map each to its real domain-bar index (exact match)."""
    ha = generate_heiken_ashi(bars)
    ha_ann = annotate_ha_impulse(ha)
    haramis = detect_ha_harami(ha)
    if haramis.height == 0:
        return np.empty(0, dtype=np.int64), np.empty(0, dtype=np.int64), ha_ann
    harami_epoch = haramis.get_column("HA0Time").dt.epoch("s").to_numpy().astype(np.int64)
    idx = _map_to_grid(bar_epoch, harami_epoch, "harami HA0Time")
    return idx, harami_epoch, ha_ann


def _map_to_grid(bar_epoch: np.ndarray, times: np.ndarray, label: str) -> np.ndarray:
    """Exact CloseTime->bar-index map (raises on any mismatch)."""
    idx = np.searchsorted(bar_epoch, times)
    if np.any(idx >= bar_epoch.shape[0]) or np.any(bar_epoch[np.minimum(
            idx, bar_epoch.shape[0] - 1)] != times):
        raise ValueError(f"{label} not found on the domain-bar grid")
    return idx.astype(np.int64)


def move_arrays(moves: pl.DataFrame, bar_epoch: np.ndarray) -> dict[str, np.ndarray]:
    """Confirmed-move arrays (epochs, prices, direction) + confirm bar indices."""
    if moves.height == 0:
        ei, ef = np.empty(0, dtype=np.int64), np.empty(0, dtype=np.float64)
        return {"confirm_epoch": ei, "end_epoch": ei, "end_price": ef, "start_price": ef,
                "direction": ei, "confirm_idx": ei, "magnitude": ef}
    confirm_epoch = moves.get_column("ConfirmTime").dt.epoch("s").to_numpy().astype(np.int64)
    start = moves.get_column("StartPrice").to_numpy().astype(np.float64)
    end = moves.get_column("EndPrice").to_numpy().astype(np.float64)
    return {
        "confirm_epoch": confirm_epoch,
        "end_epoch": moves.get_column("EndTime").dt.epoch("s").to_numpy().astype(np.int64),
        "end_price": end, "start_price": start,
        "direction": moves.get_column("Direction").to_numpy().astype(np.int64),
        "confirm_idx": _map_to_grid(bar_epoch, confirm_epoch, "ConfirmTime"),
        "magnitude": np.abs(end - start),
    }


def _sma(values: np.ndarray, window: int) -> np.ndarray:
    """Trailing simple moving average; ``NaN`` until ``window`` values exist."""
    out = np.full(values.shape[0], np.nan, dtype=np.float64)
    if values.shape[0] < window:
        return out
    cs = np.cumsum(np.insert(values, 0, 0.0))
    out[window - 1:] = (cs[window:] - cs[:-window]) / window
    return out


def ma_segment_moves(ohlc: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """MA(20,50)-crossover segmentation as a ZigZag-shaped confirmed-move set.

    Identical to EXP-055/060/061: segments run crossover->crossover on the
    **real close**; ``Direction`` is the diff sign during the segment;
    ``ConfirmTime``/``EndTime`` = the closing crossover bar; ``StartPrice``/
    ``EndPrice`` = real closes at the bracketing crossovers (real prices only).
    The pre-first-crossover stretch is excluded by construction. MA(20,50) is the
    registered Phase 015 substrate (P1), fixed and not swept.
    """
    close, epoch = ohlc["close"], ohlc["epoch"]
    n = close.shape[0]
    empty = {k: np.empty(0, dtype=t) for k, t in (
        ("confirm_epoch", np.int64), ("end_epoch", np.int64), ("end_price", np.float64),
        ("start_price", np.float64), ("direction", np.int64), ("confirm_idx", np.int64),
        ("magnitude", np.float64))}
    if n <= MA_SLOW:
        return empty
    diff = _sma(close, MA_FAST) - _sma(close, MA_SLOW)
    sign = np.sign(diff)
    defined = np.isfinite(diff) & (sign != 0.0)
    cross = np.zeros(n, dtype=bool)
    cross[1:] = defined[1:] & defined[:-1] & (sign[1:] != sign[:-1])
    cidx = np.flatnonzero(cross)
    if cidx.shape[0] < 2:
        return empty
    s, e = cidx[:-1], cidx[1:]
    return {
        "confirm_epoch": epoch[e], "end_epoch": epoch[e], "end_price": close[e],
        "start_price": close[s], "direction": sign[s].astype(np.int64),
        "confirm_idx": e.astype(np.int64), "magnitude": np.abs(close[e] - close[s]),
    }


def strong_ha_retention(
    ha_ann: pl.DataFrame, entry_epoch: np.ndarray, start_epoch: np.ndarray,
    in_trend: np.ndarray, valid: np.ndarray,
) -> dict[str, np.ndarray]:
    """Per-harami ``/STRONG-HA`` retention (same-dir disclosed; any-dir), EXP-053.

    A harami is retained iff a qualifying impulse run lies inside its in-progress
    span ``(StartTime_inprogress, t_i]``; same-direction additionally requires
    ``run_dir == in-progress trend``. Bounded scan over runs per harami.
    """
    n = int(entry_epoch.shape[0])
    same = np.zeros(n, dtype=bool)
    anyd = np.zeros(n, dtype=bool)
    runs = find_impulse_runs(ha_ann)
    if runs.height == 0:
        return {"same": same, "any": anyd}
    rf = runs.get_column("run_first_time").dt.epoch("s").to_numpy().astype(np.int64)
    rl = runs.get_column("run_last_time").dt.epoch("s").to_numpy().astype(np.int64)
    rd = runs.get_column("run_dir").to_numpy().astype(np.int64)
    for e in range(n):
        if not valid[e]:
            continue
        ub = int(np.searchsorted(rl, entry_epoch[e], side="right"))
        if ub == 0:
            continue
        in_span = rf[:ub] > start_epoch[e]
        if not in_span.any():
            continue
        anyd[e] = True
        same[e] = bool((in_span & (rd[:ub] == in_trend[e])).any())
    return {"same": same, "any": anyd}


def _rng(cell_index: int, purpose: int) -> np.random.Generator:
    """Deterministic, independent per-cell-per-purpose RNG (reproducible)."""
    return np.random.default_rng([BASE_SEED, cell_index, purpose])


# --------------------------------------------------------------------------- #
# Pure computation — P4 mean / 10% trimmed-mean moving-block bootstrap + tail
# --------------------------------------------------------------------------- #
def _stat_block_bootstrap(
    values: np.ndarray, rng: np.random.Generator, statistic: str,
    n_boot: int = N_BOOT, batch: int = BOOT_BATCH,
) -> tuple[float, float]:
    """Moving-block bootstrap CI of the raw mean or 10% trimmed mean.

    Block construction is byte-identical to :func:`availability._block_resample_medians`
    (``b = max(1, round(m**(1/3)))``; ``ceil(m/b)`` contiguous blocks per resample,
    truncated to ``m``); only the statistic changes. Returns
    ``(ci_low_1s, ci_hi_2s)`` (one-sided 95% lower 5th percentile + upper 97.5th).
    Mean/trim are tail-sensitive so their CIs are wider than the median's -- that
    width quantifies the skew (the P4 object), not a defect. Empty -> NaNs.
    """
    m = int(values.shape[0])
    if m == 0:
        return float("nan"), float("nan")
    b = max(1, int(round(m ** (1.0 / 3.0))))
    n_blocks = int(np.ceil(m / b))
    max_start = max(0, m - b)
    offsets = np.arange(b, dtype=np.int64)
    out = np.empty(n_boot, dtype=np.float64)
    done = 0
    while done < n_boot:
        k = min(batch, n_boot - done)
        starts = rng.integers(0, max_start + 1, size=(k, n_blocks))
        idx = (starts[:, :, None] + offsets[None, None, :]).reshape(k, n_blocks * b)[:, :m]
        sample = values[idx]
        out[done:done + k] = (np.mean(sample, axis=1) if statistic == "mean"
                              else _trimmed_mean_rows(sample))
        done += k
    return float(np.percentile(out, 5.0)), float(np.percentile(out, 97.5))


def _trimmed_mean_rows(sample: np.ndarray) -> np.ndarray:
    """Row-wise 10% symmetric trimmed mean of a (k, m) resample matrix (vectorised)."""
    m = sample.shape[1]
    cut = int(np.floor(TRIM_FRAC * m))
    if cut == 0:
        return np.mean(sample, axis=1)
    ordered = np.sort(sample, axis=1)[:, cut:m - cut]
    return np.mean(ordered, axis=1)


def _trimmed_mean(values: np.ndarray) -> float | None:
    """10% symmetric trimmed-mean point estimate (None on empty)."""
    m = int(values.shape[0])
    if m == 0:
        return None
    cut = int(np.floor(TRIM_FRAC * m))
    ordered = np.sort(values)
    core = ordered[cut:m - cut] if cut > 0 else ordered
    return float(np.mean(core)) if core.shape[0] > 0 else float(np.mean(ordered))


def _tail_share_largest5(values: np.ndarray) -> float | None:
    """Fraction of total excursion contributed by the largest 5% of events.

    For a non-negative excursion array (MFE or MAE), the "worst 5%" adverse tail
    is the ``ceil(0.05*m)`` **largest** values; the share is their summed
    contribution divided by the total -- a concentration measure in ``[0, 1]``.
    Returns ``0.0`` when there is no positive mass (never NaN/inf); ``None`` on
    empty. This is the availability-appropriate analog of a signed-return
    worst-tail share: excursions are non-negative, so the heavy tail is the set of
    largest excursions, not a negative-return mass.
    """
    m = int(values.shape[0])
    if m == 0:
        return None
    total = float(values.sum())
    if total <= 0.0:                                  # no positive mass -> finite zero
        return 0.0
    k = max(1, int(np.ceil(TAIL_FRAC * m)))
    largest = np.sort(values)[-k:]                    # k largest excursions
    return float(largest.sum() / total)


# --------------------------------------------------------------------------- #
# Pure computation — measure one population's lifetime availability -> AvailResult
# --------------------------------------------------------------------------- #
def _measure(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, entry_close: np.ndarray,
    rd: np.ndarray, atr_entry: np.ndarray, c2: np.ndarray, qual: np.ndarray,
    n_retained: int, n_buildable: int, n_censored: int, draw_count: int,
    rng: np.random.Generator, mean_rng: np.random.Generator,
    trim_rng: np.random.Generator,
) -> AvailResult:
    """Compute ATR-normalised lifetime MFE/MAE for the qualifying subset + CIs."""
    qidx = np.flatnonzero(qual)
    if qidx.size:
        mfe, mae = av.lifetime_excursions_atr(
            ohlc["high"], ohlc["low"], entry_close[qidx], entry_idx[qidx],
            c2[qidx], rd[qidx], atr_entry[qidx])
    else:
        mfe = mae = np.empty(0, dtype=np.float64)
    return _summarize_arm(mfe, mae, n_retained, n_buildable, n_censored, draw_count,
                          rng, mean_rng, trim_rng)


def _summarize_arm(
    mfe: np.ndarray, mae: np.ndarray, n_retained: int, n_buildable: int,
    n_censored: int, draw_count: int, rng: np.random.Generator,
    mean_rng: np.random.Generator, trim_rng: np.random.Generator,
) -> AvailResult:
    """Assemble an ``AvailResult``; (if powered) bootstrap median + mean + trim CIs."""
    m = int(mfe.shape[0])
    median_mfe = mean_mfe = median_mae = mean_mae = None
    mfe_low = mfe_lo2 = mfe_hi2 = mae_low = mae_lo2 = mae_hi2 = None
    mfe_mean_low = mfe_mean_hi = mae_mean_low = mae_mean_hi = None
    mfe_trim = mae_trim = mfe_trim_low = mae_trim_low = None
    mfe_tail = mae_tail = None
    block_len = max(1, int(round(max(m, 1) ** (1.0 / 3.0))))
    if m > 0:
        median_mfe, mean_mfe = float(np.median(mfe)), float(np.mean(mfe))
        median_mae, mean_mae = float(np.median(mae)), float(np.mean(mae))
        mfe_trim, mae_trim = _trimmed_mean(mfe), _trimmed_mean(mae)
        mfe_tail, mae_tail = _tail_share_largest5(mfe), _tail_share_largest5(mae)
    if m >= POWER_FLOOR:
        median_mfe, mfe_low, mfe_lo2, mfe_hi2, block_len = av.median_block_bootstrap(mfe, rng)
        median_mae, mae_low, mae_lo2, mae_hi2, _ = av.median_block_bootstrap(mae, rng)
        mfe_mean_low, mfe_mean_hi = _stat_block_bootstrap(mfe, mean_rng, "mean")
        mae_mean_low, mae_mean_hi = _stat_block_bootstrap(mae, mean_rng, "mean")
        mfe_trim_low, _ = _stat_block_bootstrap(mfe, trim_rng, "trim")
        mae_trim_low, _ = _stat_block_bootstrap(mae, trim_rng, "trim")
    return AvailResult(
        m=m, median_mfe=median_mfe, mfe_ci_low_1s=mfe_low, mfe_ci_lo_2s=mfe_lo2,
        mfe_ci_hi_2s=mfe_hi2, median_mae=median_mae, mae_ci_low_1s=mae_low,
        mae_ci_lo_2s=mae_lo2, mae_ci_hi_2s=mae_hi2, mean_mfe=mean_mfe, mean_mae=mean_mae,
        mfe_mean_ci_low_1s=mfe_mean_low, mfe_mean_ci_hi_2s=mfe_mean_hi,
        mae_mean_ci_low_1s=mae_mean_low, mae_mean_ci_hi_2s=mae_mean_hi,
        mfe_trim10=mfe_trim, mae_trim10=mae_trim, mfe_trim_ci_low_1s=mfe_trim_low,
        mae_trim_ci_low_1s=mae_trim_low, mfe_tail_share_largest5=mfe_tail,
        mae_tail_share_largest5=mae_tail, n_retained=n_retained, n_buildable=n_buildable,
        n_censored=n_censored, block_len=block_len, draw_count=draw_count, mfe=mfe, mae=mae)


def avail_arm(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, entry_close: np.ndarray,
    rd: np.ndarray, atr_entry: np.ndarray, c2: np.ndarray, censored: np.ndarray,
    retained_mask: np.ndarray, buildable: np.ndarray, rng: np.random.Generator,
    mean_rng: np.random.Generator, trim_rng: np.random.Generator,
) -> AvailResult:
    """One conditioned arm: population = buildable & retained; qual = ~censored."""
    population = buildable & retained_mask
    qual = population & (~censored)
    return _measure(
        ohlc, entry_idx, entry_close, rd, atr_entry, c2, qual,
        int(retained_mask.sum()), int(population.sum()),
        int((population & censored).sum()), 0, rng, mean_rng, trim_rng)


# --------------------------------------------------------------------------- #
# Pure computation — matched-count random control (substrate-generic null)
# --------------------------------------------------------------------------- #
def matched_random_arm(
    ohlc: dict[str, np.ndarray], state_all: InProgressState, atr_all: np.ndarray,
    confirm_idx: np.ndarray, signal_entry_idx: np.ndarray, draw_count: int,
    cell_index: int, pb_draw: int, pb_boot: int, pb_mean: int, pb_trim: int,
) -> tuple[AvailResult, int]:
    """Matched-count random control over the eligible non-signal in-progress pool.

    Substrate-generic: ZigZag (RM_ZZ) passes the ZigZag ``state_all``/``confirm_idx``;
    MA (RM_MA_nat / RM_MA_hyb, the NEW computations) pass the MA-segmentation analogs.
    Eligible bars: valid in-progress, ``M_sofar>0``, finite positive ATR, **excluding**
    that object's ``/STRONG-STAT`` retained-signal bars. Each drawn bar takes its
    in-progress ``rd`` and is measured over **its own** end-of-M_b window (the 2nd
    confirmation at/after the bar). Direction is not random. Returns
    ``(AvailResult, pool_size)``; the matched-count target is stored as ``draw_count``.
    """
    n_bars = ohlc["close"].shape[0]
    eligible = (state_all.valid & (state_all.m_sofar > 0.0)
                & np.isfinite(atr_all) & (atr_all > 0.0))
    is_signal = np.zeros(n_bars, dtype=bool)
    is_signal[signal_entry_idx] = True
    eligible &= ~is_signal
    pool = np.flatnonzero(eligible)
    if draw_count <= 0 or pool.shape[0] == 0:
        return _empty_arm(), int(pool.shape[0])
    k = min(draw_count, pool.shape[0])
    drawn = np.sort(_rng(cell_index, pb_draw).choice(pool, size=k, replace=False))
    c2, censored = av.end_of_mb_window(drawn, confirm_idx)
    res = _measure(
        ohlc, drawn, ohlc["close"][drawn], state_all.rd[drawn], atr_all[drawn],
        c2, ~censored, k, k, int(censored.sum()), draw_count,
        _rng(cell_index, pb_boot), _rng(cell_index, pb_mean), _rng(cell_index, pb_trim))
    return res, int(pool.shape[0])


def population_digest(
    entry_idx: np.ndarray, entry_epoch: np.ndarray, rd: np.ndarray, mask: np.ndarray,
) -> dict[str, Any]:
    """Per-cell event digest: count + a stable hash of (trigger_idx, time, rd)."""
    sel = np.flatnonzero(mask)
    if sel.size == 0:
        return {"n": 0, "digest": None}
    payload = np.concatenate([
        entry_idx[sel].astype(np.int64), entry_epoch[sel].astype(np.int64),
        rd[sel].astype(np.int64)]).tobytes()
    return {"n": int(sel.size), "digest": hashlib.sha1(payload).hexdigest()}


# --------------------------------------------------------------------------- #
# Per-cell substrate contexts (MA binding for both objects; ZigZag disclosed)
# --------------------------------------------------------------------------- #
def _ma_context(
    ohlc: dict[str, np.ndarray], atr: np.ndarray, entry_idx: np.ndarray,
    entry_epoch: np.ndarray, ha_ann: pl.DataFrame,
) -> dict[str, Any]:
    """MA(20,50) conditioned-signal context at the harami entries (both MA objects).

    Reproduces EXP-055's ``ma_seg_arm`` construction (the native P12 anchor) and
    exposes the MA segmentation + all-bar in-progress state for the RM_MA nulls and
    the disclosed /STRONG-HA / MAD arms. The native /STRONG-STAT mask is
    ``stat["retained_p75"]``; the hybrid object reuses this MA geometry/window but
    conditions on the ZigZag mask (supplied by the caller).
    """
    seg = ma_segment_moves(ohlc)
    if seg["confirm_epoch"].shape[0] == 0:
        return {"empty": True, "seg": seg}
    entry_close = ohlc["close"][entry_idx]
    atr_entry = atr[entry_idx]
    state = live_in_progress_state(entry_epoch, entry_close, seg["confirm_epoch"],
                                   seg["end_price"], seg["end_epoch"], seg["direction"])
    buildable = (state.valid & (state.m_sofar > 0.0) & np.isfinite(atr_entry)
                 & (atr_entry > 0.0))
    stat = live_strong_stat(state.k, state.m_sofar, seg["magnitude"])
    ha_ret = strong_ha_retention(ha_ann, entry_epoch, state.start_epoch,
                                 -state.rd, state.valid)
    c2, censored = av.end_of_mb_window(entry_idx, seg["confirm_idx"])
    return {"empty": False, "seg": seg, "entry_idx": entry_idx, "entry_close": entry_close,
            "state": state, "atr": atr, "atr_entry": atr_entry, "buildable": buildable,
            "stat": stat, "ha_ret": ha_ret, "c2": c2, "censored": censored}


def _zz_context(
    ohlc: dict[str, np.ndarray], atr: np.ndarray, entry_idx: np.ndarray,
    entry_epoch: np.ndarray, mv: dict[str, np.ndarray],
) -> dict[str, Any]:
    """ZigZag conditioned-signal context at the harami entries (A_ZZ + RM_ZZ).

    Reproduces EXP-055's binding ``stat`` arm construction (the disclosed P12 anchor)
    and caches the all-bar in-progress state + confirm/end-epoch arrays for the
    RM_ZZ matched-random null and the causality gate. Its ``stat["retained_p75"]``
    mask is the **hybrid** object's conditioning mask (over the same harami entries),
    applied to the MA context for ``A_MA_hyb``.
    """
    entry_close = ohlc["close"][entry_idx]
    atr_entry = atr[entry_idx]
    state = live_in_progress_state(entry_epoch, entry_close, mv["confirm_epoch"],
                                   mv["end_price"], mv["end_epoch"], mv["direction"])
    state_all = live_in_progress_state(ohlc["epoch"], ohlc["close"], mv["confirm_epoch"],
                                       mv["end_price"], mv["end_epoch"], mv["direction"])
    buildable = (state.valid & (state.m_sofar > 0.0) & np.isfinite(atr_entry)
                 & (atr_entry > 0.0))
    stat = live_strong_stat(state.k, state.m_sofar, mv["magnitude"])
    c2, censored = av.end_of_mb_window(entry_idx, mv["confirm_idx"])
    return {"empty": False, "entry_idx": entry_idx, "entry_close": entry_close,
            "state": state, "state_all": state_all, "atr": atr, "atr_entry": atr_entry,
            "buildable": buildable, "stat": stat, "c2": c2, "censored": censored,
            "confirm_idx": mv["confirm_idx"], "end_epoch": mv["end_epoch"]}


def _ctx_arm(
    ctx: dict[str, Any], ohlc: dict[str, np.ndarray], mask: np.ndarray,
    cell_index: int, pb_med: int, pb_mean: int, pb_trim: int,
) -> AvailResult:
    """Resolve one conditioned availability arm on a substrate context's population.

    ``mask`` selects which harami entries qualify; the geometry/window come from
    ``ctx``. For ``A_MA_nat`` ``mask = ma["stat"]["retained_p75"]`` (native); for
    ``A_MA_hyb`` ``mask = zz["stat"]["retained_p75"]`` applied to the **MA** context
    (the genuinely-new hybrid object). Both share ``ctx["entry_idx"]`` (the same
    harami array; verified in ``compute_cell``).
    """
    return avail_arm(
        ohlc, ctx["entry_idx"], ctx["entry_close"], ctx["state"].rd, ctx["atr_entry"],
        ctx["c2"], ctx["censored"], mask, ctx["buildable"],
        _rng(cell_index, pb_med), _rng(cell_index, pb_mean), _rng(cell_index, pb_trim))


# --------------------------------------------------------------------------- #
# Per-cell orchestration
# --------------------------------------------------------------------------- #
def compute_cell(
    train_1m: pl.DataFrame, domain: str, train_end_epoch: int, cell_index: int,
) -> dict[str, Any]:
    """Full pipeline for one cell. Pure given identical inputs/seeds."""
    period_minutes, min_coverage = DOMAINS[domain]
    bars = build_domain(train_1m, period_minutes, min_coverage, train_end_epoch)
    ohlc = real_ohlc(bars)
    moves = generate_zigzag(bars, atr_period=ATR_PERIOD, atr_mult=ATR_MULT)
    mv = move_arrays(moves, ohlc["epoch"])
    atr = wilder_atr(ohlc["high"], ohlc["low"], ohlc["close"], ATR_PERIOD)
    entry_idx, entry_epoch, ha_ann = harami_entry_indices(bars, ohlc["epoch"])
    base = {"domain": domain, "n_bars": int(bars.height), "n_moves": int(moves.height),
            "n_harami": int(entry_idx.shape[0])}
    ma = _ma_context(ohlc, atr, entry_idx, entry_epoch, ha_ann)
    if entry_idx.shape[0] == 0 or ma.get("empty"):
        return {**base, "empty": True, "n_retained": 0}
    zz = _zz_context(ohlc, atr, entry_idx, entry_epoch, mv)
    # Both MA objects condition over the SAME harami entry array (MA + ZigZag contexts
    # are built from the identical entry_idx); the hybrid mask therefore aligns directly.
    if not np.array_equal(ma["entry_idx"], zz["entry_idx"]):
        raise RuntimeError(f"{domain}: MA/ZigZag harami-entry arrays differ (hybrid mask misaligned)")
    arms = _resolve_arms(ohlc, ma, zz, cell_index)
    qual_ma = ma["buildable"] & ma["stat"]["retained_p75"] & (~ma["censored"])
    window_ok = av.window_invariants_ok(
        entry_idx, ma["c2"], ma["seg"]["confirm_idx"], qual_ma, int(bars.height))
    nat_mask = ma["buildable"] & ma["stat"]["retained_p75"]
    hyb_mask = ma["buildable"] & zz["stat"]["retained_p75"]
    return {
        **base, "empty": False, "arms": arms,
        "n_retained": int(ma["stat"]["retained_p75"].sum()),
        "n_retained_hyb": int(zz["stat"]["retained_p75"].sum()),
        "n_censored_buildable": int((ma["buildable"] & ma["censored"]).sum()),
        "window_invariants_ok": window_ok,
        # native digest reconciles to EXP-053/055; hybrid digest is a disclosed-new quantity.
        "nat_digest": population_digest(entry_idx, entry_epoch, ma["state"].rd, nat_mask),
        "hyb_digest": population_digest(entry_idx, entry_epoch, ma["state"].rd, hyb_mask),
        "causality_ok": _causality_ok(entry_epoch, ma, zz),
        "matched_count_ok": (arms["rm_ma_nat"].draw_count == arms["a_ma_nat"].m
                             and arms["rm_ma_hyb"].draw_count == arms["a_ma_hyb"].m
                             and arms["rm_zz"].draw_count == arms["a_zz"].m),
    }


def _resolve_arms(
    ohlc: dict[str, np.ndarray], ma: dict[str, Any], zz: dict[str, Any], cell_index: int,
) -> dict[str, Any]:
    """Resolve the two binding MA objects + disclosed arms + the per-object contrasts.

    ``A_MA_nat`` (native): MA-segment ``/STRONG-STAT`` mask through MA geometry --
    reproduces EXP-055 ``ma_seg``. ``A_MA_hyb`` (hybrid, NEW): ZigZag ``/STRONG-STAT``
    mask through the **same** MA geometry/window -- no outcome anchor. The two objects
    are measured/reported individually -- never pooled (D0 Amendment 001).
    """
    a_ma_nat = _ctx_arm(ma, ohlc, ma["stat"]["retained_p75"], cell_index,
                        RNG_MA_STAT, RNG_MA_STAT_MEAN, RNG_MA_STAT_TRIM)
    a_ma_hyb = _ctx_arm(ma, ohlc, zz["stat"]["retained_p75"], cell_index,
                        RNG_MA_HYB, RNG_MA_HYB_MEAN, RNG_MA_HYB_TRIM)
    a_ma_nat_ha = _ctx_arm(ma, ohlc, ma["ha_ret"]["same"], cell_index,
                           RNG_MA_HA, RNG_MA_HA_MEAN, RNG_MA_HA_TRIM)
    a_ma_nat_mad = _ctx_arm(ma, ohlc, ma["stat"]["retained_mad"], cell_index,
                            RNG_MA_MAD, RNG_MA_MAD_MEAN, RNG_MA_MAD_TRIM)
    a_zz = _ctx_arm(zz, ohlc, zz["stat"]["retained_p75"], cell_index,
                    RNG_ZZ_STAT, RNG_ZZ_STAT_MEAN, RNG_ZZ_STAT_TRIM)
    rm_ma_nat, rm_ma_hyb, rm_zz = _resolve_nulls(
        ohlc, ma, zz, a_ma_nat.m, a_ma_hyb.m, a_zz.m, cell_index)
    contrasts = {
        "nat": _avail_contrast(a_ma_nat, rm_ma_nat, cell_index,
                               RNG_CONTRAST_MA_MFE, RNG_CONTRAST_MA_MAE),
        "hyb": _avail_contrast(a_ma_hyb, rm_ma_hyb, cell_index,
                               RNG_CONTRAST_MA_HYB_MFE, RNG_CONTRAST_MA_HYB_MAE),
        "zz": _avail_contrast(a_zz, rm_zz, cell_index,
                              RNG_CONTRAST_ZZ_MFE, RNG_CONTRAST_ZZ_MAE),
    }
    return {"a_ma_nat": a_ma_nat, "a_ma_hyb": a_ma_hyb, "a_ma_nat_ha": a_ma_nat_ha,
            "a_ma_nat_mad": a_ma_nat_mad, "a_zz": a_zz, "rm_ma_nat": rm_ma_nat,
            "rm_ma_hyb": rm_ma_hyb, "rm_zz": rm_zz, "contrasts": contrasts}


def _resolve_nulls(
    ohlc: dict[str, np.ndarray], ma: dict[str, Any], zz: dict[str, Any],
    a_ma_nat_m: int, a_ma_hyb_m: int, a_zz_m: int, cell_index: int,
) -> tuple[AvailResult, AvailResult, AvailResult]:
    """RM_MA_nat + RM_MA_hyb (binding MA nulls, per object) + RM_ZZ (disclosed).

    RM_MA_nat and RM_MA_hyb share the MA in-regime eligible pool but are matched to
    their **own** object's qualifying count and exclude their **own** object's signal
    entries; they use disjoint dedicated RNG streams so neither perturbs the other.
    """
    ma_state_all = live_in_progress_state(
        ohlc["epoch"], ohlc["close"], ma["seg"]["confirm_epoch"], ma["seg"]["end_price"],
        ma["seg"]["end_epoch"], ma["seg"]["direction"])
    nat_signal_idx = ma["entry_idx"][ma["buildable"] & ma["stat"]["retained_p75"]]
    rm_ma_nat, _ = matched_random_arm(
        ohlc, ma_state_all, ma["atr"], ma["seg"]["confirm_idx"], nat_signal_idx, a_ma_nat_m,
        cell_index, RNG_RM_MA_DRAW, RNG_RM_MA_BOOT, RNG_RM_MA_MEAN, RNG_RM_MA_TRIM)
    hyb_signal_idx = ma["entry_idx"][ma["buildable"] & zz["stat"]["retained_p75"]]
    rm_ma_hyb, _ = matched_random_arm(
        ohlc, ma_state_all, ma["atr"], ma["seg"]["confirm_idx"], hyb_signal_idx, a_ma_hyb_m,
        cell_index, RNG_RM_MA_HYB_DRAW, RNG_RM_MA_HYB_BOOT, RNG_RM_MA_HYB_MEAN, RNG_RM_MA_HYB_TRIM)
    zz_signal_idx = zz["entry_idx"][zz["buildable"] & zz["stat"]["retained_p75"]]
    rm_zz, _ = matched_random_arm(
        ohlc, zz["state_all"], zz["atr"], zz["confirm_idx"], zz_signal_idx, a_zz_m,
        cell_index, RNG_RM_ZZ_DRAW, RNG_RM_ZZ_BOOT, RNG_RM_ZZ_MEAN, RNG_RM_ZZ_TRIM)
    return rm_ma_nat, rm_ma_hyb, rm_zz


def _avail_contrast(
    signal: AvailResult, null: AvailResult, cell_index: int, pb_mfe: int, pb_mae: int,
) -> dict[str, Any]:
    """Independent median-difference moving-block bootstrap ``signal - null``.

    Binding on **MFE** (the favourable-availability signal-attribution leg, P5);
    **MAE** disclosed. The signal (haramis) and null (disjoint random in-regime
    draws) are independent event pools -- no pairing -- so each is block-resampled by
    its own order, mirroring EXP-055's matched-random contrast.
    """
    mfe = av.median_diff_block_bootstrap(signal.mfe, null.mfe, _rng(cell_index, pb_mfe))
    mae = av.median_diff_block_bootstrap(signal.mae, null.mae, _rng(cell_index, pb_mae))
    return {"mfe_diff": mfe[0], "mfe_low_1s": mfe[1], "mfe_hi_2s": mfe[3],
            "mae_diff": mae[0], "mae_low_1s": mae[1], "mae_hi_2s": mae[3]}


# --------------------------------------------------------------------------- #
# Per-cell causality gate
# --------------------------------------------------------------------------- #
def _ref_ends_before_entry(
    state: InProgressState, end_epoch: np.ndarray, entry_epoch: np.ndarray,
) -> bool:
    """Every valid harami's referenced confirmed move ends at/before its entry bar."""
    valid = state.valid & (state.k >= 0)
    if not valid.any():
        return True
    kk = state.k[valid]
    return bool(np.all(end_epoch[kk] <= entry_epoch[valid]))


def _causality_ok(
    entry_epoch: np.ndarray, ma: dict[str, Any], zz: dict[str, Any],
) -> bool:
    """MA + ZigZag reference moves end at/before entry (no unconfirmed-pivot reference)."""
    return (_ref_ends_before_entry(ma["state"], ma["seg"]["end_epoch"], entry_epoch)
            and _ref_ends_before_entry(zz["state"], zz["end_epoch"], entry_epoch))


# --------------------------------------------------------------------------- #
# Per-cell record flattening + per-object availability classification
# --------------------------------------------------------------------------- #
def cell_record(instrument: str, cell: dict[str, Any]) -> dict[str, Any]:
    """Flatten one cell's pipeline output into a per-cell summary record."""
    rec: dict[str, Any] = {
        "instrument": instrument, "domain": cell["domain"], "member": True,
        "excluded": False, "n_bars": cell["n_bars"], "n_moves": cell["n_moves"],
        "n_harami": cell["n_harami"], "n_retained": cell["n_retained"],
    }
    if cell.get("empty", False):
        rec.update(_empty_metric_fields())
        return rec
    arms = cell["arms"]
    rec["n_retained_hyb"] = cell["n_retained_hyb"]
    rec["n_censored_buildable"] = cell["n_censored_buildable"]
    rec.update(_arm_fields(arms["a_ma_nat"], "ama_nat"))
    rec.update(_arm_fields(arms["a_ma_hyb"], "ama_hyb"))
    rec.update(_arm_fields(arms["a_ma_nat_ha"], "ama_nat_ha"))
    rec.update(_arm_fields(arms["a_ma_nat_mad"], "ama_nat_mad"))
    rec.update(_arm_fields(arms["a_zz"], "azz"))
    rec.update(_arm_fields(arms["rm_ma_nat"], "rmma_nat"))
    rec.update(_arm_fields(arms["rm_ma_hyb"], "rmma_hyb"))
    rec.update(_arm_fields(arms["rm_zz"], "rmzz"))
    c = arms["contrasts"]
    rec.update({
        "nat_rm_mfe_low_1s": c["nat"]["mfe_low_1s"], "nat_rm_mfe_diff": c["nat"]["mfe_diff"],
        "nat_rm_mae_low_1s": c["nat"]["mae_low_1s"], "nat_rm_mae_diff": c["nat"]["mae_diff"],
        "hyb_rm_mfe_low_1s": c["hyb"]["mfe_low_1s"], "hyb_rm_mfe_diff": c["hyb"]["mfe_diff"],
        "hyb_rm_mae_low_1s": c["hyb"]["mae_low_1s"], "hyb_rm_mae_diff": c["hyb"]["mae_diff"],
        "azz_rmzz_mfe_low_1s": c["zz"]["mfe_low_1s"], "azz_rmzz_mfe_diff": c["zz"]["mfe_diff"],
    })
    nat, hyb = arms["a_ma_nat"], arms["a_ma_hyb"]
    rec["nat_censored_fraction"] = (nat.n_censored / nat.n_buildable if nat.n_buildable else None)
    rec["hyb_censored_fraction"] = (hyb.n_censored / hyb.n_buildable if hyb.n_buildable else None)
    _classify_object(rec, nat, c["nat"]["mfe_low_1s"], "nat")
    _classify_object(rec, hyb, c["hyb"]["mfe_low_1s"], "hyb")
    return rec


def _classify_object(
    rec: dict[str, Any], sig: AvailResult, contrast_mfe_low: float | None, prefix: str,
) -> None:
    """Set one object's MOVE_AVAILABLE / SIGNAL_ATTRIBUTABLE / reference multiples / status."""
    available = av.move_available(sig.m, sig.mfe_ci_low_1s, sig.median_mfe, sig.median_mae)
    rec[f"{prefix}_powered"] = sig.m >= POWER_FLOOR
    rec[f"{prefix}_move_available"] = bool(available)
    rec[f"{prefix}_signal_attributable"] = bool(
        contrast_mfe_low is not None and np.isfinite(contrast_mfe_low) and contrast_mfe_low > 0.0)
    rec[f"{prefix}_available_attributable"] = bool(
        rec[f"{prefix}_move_available"] and rec[f"{prefix}_signal_attributable"])
    rec[f"{prefix}_mfe_mult_ref_lo"] = (
        sig.median_mfe / av.REF_LINES[0] if sig.median_mfe is not None else None)
    rec[f"{prefix}_mfe_mult_ref_hi"] = (
        sig.median_mfe / av.REF_LINES[1] if sig.median_mfe is not None else None)
    rec[f"{prefix}_mfe_gt_mae"] = bool(
        sig.median_mfe is not None and sig.median_mae is not None
        and sig.median_mfe > sig.median_mae)
    status = av.availability_status(sig.m, available)
    rec[f"{prefix}_availability_status"] = status
    rec[f"{prefix}_status_code"] = ASTATUS_CODES[status]


def _arm_fields(a: AvailResult, prefix: str) -> dict[str, Any]:
    """Flatten one AvailResult into per-cell columns (no per-event arrays)."""
    return {
        f"{prefix}_m": a.m, f"{prefix}_median_mfe": a.median_mfe,
        f"{prefix}_mfe_ci_low_1s": a.mfe_ci_low_1s, f"{prefix}_mfe_ci_hi_2s": a.mfe_ci_hi_2s,
        f"{prefix}_median_mae": a.median_mae, f"{prefix}_mae_ci_low_1s": a.mae_ci_low_1s,
        f"{prefix}_mae_ci_hi_2s": a.mae_ci_hi_2s, f"{prefix}_mean_mfe": a.mean_mfe,
        f"{prefix}_mean_mae": a.mean_mae, f"{prefix}_mae_mean_ci_low_1s": a.mae_mean_ci_low_1s,
        f"{prefix}_mae_mean_ci_hi_2s": a.mae_mean_ci_hi_2s, f"{prefix}_mfe_trim10": a.mfe_trim10,
        f"{prefix}_mae_trim10": a.mae_trim10, f"{prefix}_mae_trim_ci_low_1s": a.mae_trim_ci_low_1s,
        f"{prefix}_mfe_tail_share5": a.mfe_tail_share_largest5,
        f"{prefix}_mae_tail_share5": a.mae_tail_share_largest5,
        f"{prefix}_n_retained": a.n_retained, f"{prefix}_n_buildable": a.n_buildable,
        f"{prefix}_n_censored": a.n_censored, f"{prefix}_block_len": a.block_len,
        f"{prefix}_draw_count": a.draw_count,
    }


def _empty_metric_fields() -> dict[str, Any]:
    """Metric columns for a member cell with no harami/move population."""
    rec: dict[str, Any] = {
        "n_retained_hyb": 0, "n_censored_buildable": 0,
        "nat_rm_mfe_low_1s": None, "nat_rm_mfe_diff": None, "nat_rm_mae_low_1s": None,
        "nat_rm_mae_diff": None, "hyb_rm_mfe_low_1s": None, "hyb_rm_mfe_diff": None,
        "hyb_rm_mae_low_1s": None, "hyb_rm_mae_diff": None,
        "azz_rmzz_mfe_low_1s": None, "azz_rmzz_mfe_diff": None,
    }
    for prefix in ("nat", "hyb"):
        rec.update({
            f"{prefix}_censored_fraction": None, f"{prefix}_powered": False,
            f"{prefix}_move_available": False, f"{prefix}_signal_attributable": False,
            f"{prefix}_available_attributable": False, f"{prefix}_mfe_mult_ref_lo": None,
            f"{prefix}_mfe_mult_ref_hi": None, f"{prefix}_mfe_gt_mae": False,
            f"{prefix}_availability_status": "NOT_VIABLE_BY_POWER",
            f"{prefix}_status_code": ASTATUS_CODES["NOT_VIABLE_BY_POWER"]})
    for prefix in ("ama_nat", "ama_hyb", "ama_nat_ha", "ama_nat_mad", "azz",
                   "rmma_nat", "rmma_hyb", "rmzz"):
        rec.update(_arm_fields(_empty_arm(), prefix))
    return rec


def excluded_record(instrument: str, domain: str) -> dict[str, Any]:
    """Record for a COVERAGE_EXCLUDED cell (not in the EXP-049 member grid)."""
    rec: dict[str, Any] = {
        "instrument": instrument, "domain": domain, "member": False, "excluded": True,
        "n_bars": None, "n_moves": None, "n_harami": None, "n_retained": None}
    rec.update(_empty_metric_fields())
    for prefix in ("nat", "hyb"):
        rec[f"{prefix}_availability_status"] = "EXCLUDED"
        rec[f"{prefix}_status_code"] = ASTATUS_CODES["EXCLUDED"]
    return rec


# --------------------------------------------------------------------------- #
# Composition + verdict readout (P11 with the P6 non-4h rule), per object
# --------------------------------------------------------------------------- #
def _p11(rows: list[dict[str, Any]], flag: str) -> dict[str, Any]:
    """P11 + P6 tally: >=5 cells over >=3 instruments with >=3 cells outside 4h."""
    hit = [r for r in rows if r.get(flag)]
    instruments = sorted({r["instrument"] for r in hit})
    non_4h = [r for r in hit if r["domain"] != "4h"]
    n_cells, n_instr, n_non_4h = len(hit), len(instruments), len(non_4h)
    composes = (n_cells >= P11_MIN_CELLS and n_instr >= P11_MIN_INSTR
                and n_non_4h >= P6_MIN_NON_4H)
    fragile = composes and (n_cells == P11_MIN_CELLS or n_instr == P11_MIN_INSTR
                            or n_non_4h == P6_MIN_NON_4H)
    return {"n_cells": n_cells, "n_instruments": n_instr, "n_non_4h": n_non_4h,
            "composes": composes, "fragile": fragile,
            "cells": [f"{r['instrument']}-{r['domain']}" for r in hit]}


def _object_readout(members: list[dict[str, Any]], defect: dict[str, Any], prefix: str,
                    object_name: str) -> dict[str, Any]:
    """One object's P11+P6 composition tallies + the mechanical AVAILABILITY_* fork."""
    available = _p11(members, f"{prefix}_move_available")
    attributable = _p11(members, f"{prefix}_available_attributable")
    powered = _p11(members, f"{prefix}_powered")
    verdict = _verdict(defect, available, powered)
    return {"object": object_name, "verdict": verdict, "move_available": available,
            "available_attributable": attributable, "powered": powered}


def composition_readout(records: list[dict[str, Any]], defect: dict[str, Any]) -> dict[str, Any]:
    """Per-object P11+P6 composition + the mechanical AVAILABILITY_* fork (never pooled)."""
    members = [r for r in records if r["member"]]
    nat = _object_readout(members, defect, "nat",
                          "A_MA_nat (MA-segment /STRONG-STAT; reconciles EXP-055 ma_seg)")
    hyb = _object_readout(members, defect, "hyb",
                          "A_MA_hyb (ZigZag /STRONG-STAT x MA window; NEW, no outcome anchor)")
    # Phase reading = the stronger object's verdict (rank GOOD > POOR > INCONCLUSIVE > DEFECT).
    rank = {"AVAILABILITY_GOOD": 3, "AVAILABILITY_POOR": 2,
            "INCONCLUSIVE_POWER_LIMITED": 1, "SUBSTRATE_METHOD_DEFECT": 0}
    phase = nat if rank.get(nat["verdict"], 0) >= rank.get(hyb["verdict"], 0) else hyb
    return {
        "phase_verdict": phase["verdict"],
        "phase_stronger_object": phase["object"], "defect": defect,
        "native": nat, "hybrid": hyb,
        "rule": (
            "Per object, never pooled. MOVE_AVAILABLE iff m>=30 AND median-MFE CI_low(1s)>1.0 ATR "
            "(upper reference line, never subtracted) AND median_MFE>median_MAE. "
            "SIGNAL_ATTRIBUTABLE iff the object's A-RM median-MFE difference-bootstrap CI_low(1s)>0 "
            "(own-object matched-random on MA, P5). AVAILABILITY_GOOD iff MOVE_AVAILABLE composes "
            "P11 with the P6 non-4h rule (>=5 cells / >=3 instruments / >=3 cells outside 4h); else "
            "AVAILABILITY_POOR if the powered grid composes P11+P6; else INCONCLUSIVE_POWER_LIMITED; "
            "SUBSTRATE_METHOD_DEFECT on any determinism/causality/invariant/reconciliation failure. "
            "Phase reading = the stronger object's verdict."),
        "g015_routing": (
            "Feeds the single terminal G-015 after the full Phase 015 slate (no closure here). "
            "Each object's AVAILABILITY_GOOD motivates the surface reads (L3/S1-S4) on that object; "
            "the per-object MAE tail decomposition sizes the L3 (EXP-063) downside-bounding "
            "opportunity per object."),
    }


def _verdict(defect: dict[str, Any], available: dict[str, Any],
             powered: dict[str, Any]) -> str:
    """Mechanical AVAILABILITY_* verdict for one object (analysis-plan §Interpretation)."""
    if defect["is_defect"]:
        return "SUBSTRATE_METHOD_DEFECT"
    if available["composes"]:
        return "AVAILABILITY_GOOD"
    if not powered["composes"]:
        return "INCONCLUSIVE_POWER_LIMITED"
    return "AVAILABILITY_POOR"


# --------------------------------------------------------------------------- #
# Determinism replay + EXP-055 reconciliation (DEFECT guards)
# --------------------------------------------------------------------------- #
_ARM_SCALARS = ("m", "median_mfe", "mfe_ci_low_1s", "median_mae", "mae_ci_low_1s",
                "mean_mfe", "mean_mae", "mfe_trim10", "mae_trim10",
                "mfe_tail_share_largest5", "mae_tail_share_largest5", "draw_count")
_ALL_ARMS = ("a_ma_nat", "a_ma_hyb", "a_ma_nat_ha", "a_ma_nat_mad", "a_zz",
             "rm_ma_nat", "rm_ma_hyb", "rm_zz")


def _eq(a: Any, b: Any) -> bool:
    """NaN/None-aware scalar equality (CIs are None when unpowered, NaN on <2)."""
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, float) and isinstance(b, float) and (np.isnan(a) or np.isnan(b)):
        return np.isnan(a) and np.isnan(b)
    return bool(a == b)


def _arm_identical(x: AvailResult, y: AvailResult) -> bool:
    """Per-event arrays + key scalar fields of one arm reproduce exactly."""
    if not (np.array_equal(x.mfe, y.mfe) and np.array_equal(x.mae, y.mae)):
        return False
    return all(_eq(getattr(x, f), getattr(y, f)) for f in _ARM_SCALARS)


def cells_identical(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """All arms, all contrasts, and both population digests reproduce frame-identically."""
    if a.get("empty") or b.get("empty"):
        return a.get("empty") == b.get("empty")
    for arm in _ALL_ARMS:
        if not _arm_identical(a["arms"][arm], b["arms"][arm]):
            return False
    for key in ("nat", "hyb", "zz"):
        ca, cb = a["arms"]["contrasts"][key], b["arms"]["contrasts"][key]
        if not all(_eq(ca[f], cb[f]) for f in ("mfe_low_1s", "mae_low_1s")):
            return False
    return (a.get("nat_digest") == b.get("nat_digest")
            and a.get("hyb_digest") == b.get("hyb_digest"))


def determinism_replay(train_1m: pl.DataFrame, domain: str, train_end_epoch: int,
                       cell_index: int, reference: dict[str, Any]) -> bool:
    """Re-run one cell end-to-end and assert it reproduces ``reference`` exactly."""
    replay = compute_cell(train_1m, domain, train_end_epoch, cell_index)
    return cells_identical(reference, replay)


def exp055_reconciliation(
    instrument: str, cell: dict[str, Any], anchor: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    """P12 reproduction guard vs EXP-055 ma_seg (native A_MA_nat) + stat (A_ZZ) arms.

    The **native** ``A_MA_nat`` arm reproduces EXP-055's ``ma_seg`` arm (per-cell m +
    median MFE + median MAE to ``RECON_TOL``); the disclosed ``A_ZZ`` reproduces
    EXP-055's binding ``stat`` arm likewise. The **hybrid** ``A_MA_hyb`` has **no**
    outcome anchor -- its conditioning mask is the same mask that defines ``A_ZZ``'s
    population (verified transitively via the ``A_ZZ`` count/digest). A missing/empty
    anchor or any divergence is SUBSTRATE/METHOD_DEFECT.
    """
    key = (instrument, cell.get("domain"))
    if not anchor or key not in anchor or cell.get("empty"):
        return {"checked": False, "cell": f"{instrument}-{cell.get('domain')}"}
    src = anchor[key]
    a_ma_nat, a_zz = cell["arms"]["a_ma_nat"], cell["arms"]["a_zz"]
    ma_ok = _arm_match(a_ma_nat, src["maseg"])
    zz_ok = _arm_match(a_zz, src["stat"])
    return {"checked": True, "cell": f"{instrument}-{cell['domain']}",
            "a_ma_nat_m": a_ma_nat.m, "exp055_maseg_m": src["maseg"].get("m"),
            "a_ma_nat_median_mfe": a_ma_nat.median_mfe,
            "exp055_maseg_median_mfe": src["maseg"].get("median_mfe"),
            "a_ma_nat_median_mae": a_ma_nat.median_mae,
            "exp055_maseg_median_mae": src["maseg"].get("median_mae"),
            "a_zz_m": a_zz.m, "exp055_stat_m": src["stat"].get("m"),
            "a_zz_median_mfe": a_zz.median_mfe, "exp055_stat_median_mfe": src["stat"].get("median_mfe"),
            "a_ma_hyb_m": cell["arms"]["a_ma_hyb"].m,
            "a_ma_nat_match": bool(ma_ok), "a_zz_match": bool(zz_ok),
            "consistent": bool(ma_ok and zz_ok)}


def _arm_match(arm: AvailResult, src: dict[str, Any]) -> bool:
    """One arm's m + median MFE + median MAE match the EXP-055 anchor to RECON_TOL."""
    return (arm.m == (int(src["m"]) if src.get("m") is not None else 0)
            and _float_match(arm.median_mfe, src.get("median_mfe"))
            and _float_match(arm.median_mae, src.get("median_mae")))


def _float_match(a: float | None, b: float | None) -> bool:
    """Two optional floats agree to RECON_TOL (both None counts as a match)."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return abs(float(a) - float(b)) <= RECON_TOL


# --------------------------------------------------------------------------- #
# Plotting (bounded; from collected per-cell summaries -- no reloads), per object
# --------------------------------------------------------------------------- #
def _placeholder(save_path: Path, message: str) -> None:
    """Write a small placeholder figure when a plot has no data."""
    fig, ax = plt.subplots(figsize=(6, 2))
    ax.text(0.5, 0.5, f"{EXPERIMENT_ID}: {message}", ha="center", va="center")
    ax.axis("off")
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_forest(records: list[dict[str, Any]], save_path: Path) -> None:
    """Per-cell native+hybrid median MFE (CI_low whisker) & MAE + reference band."""
    members = [r for r in records if r["member"]]
    rows = sorted([r for r in members if r["ama_nat_median_mfe"] is not None
                   or r["ama_hyb_median_mfe"] is not None],
                  key=lambda r: (r["ama_nat_median_mfe"] if r["ama_nat_median_mfe"] is not None
                                 else (r["ama_hyb_median_mfe"] or 0.0)))
    if not rows:
        _placeholder(save_path, "no powered cells")
        return
    labels = [f"{r['instrument']}-{r['domain']}" for r in rows]
    y = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(8.5, max(4, 0.30 * len(labels))))
    for prefix, colour, mkr, name in (("ama_nat", "#1a9850", "o", "native"),
                                      ("ama_hyb", "#4575b4", "s", "hybrid")):
        mfe = np.array([r[f"{prefix}_median_mfe"] if r[f"{prefix}_median_mfe"] is not None
                        else np.nan for r in rows])
        mfe_low = np.array([r[f"{prefix}_mfe_ci_low_1s"] if r[f"{prefix}_mfe_ci_low_1s"] is not None
                            else np.nan for r in rows])
        mae = np.array([r[f"{prefix}_median_mae"] if r[f"{prefix}_median_mae"] is not None
                        else np.nan for r in rows])
        ax.hlines(y, np.minimum(mfe_low, mfe), mfe, color=colour, alpha=0.6, zorder=2)
        ax.scatter(mfe, y, color=colour, s=24, marker=mkr, zorder=3, label=f"{name} median MFE")
        ax.scatter(mae, y, color=colour, marker="x", s=18,
                   zorder=3, label=f"{name} median MAE")
    for ref, ls in zip(av.REF_LINES, (":", "--")):
        ax.axvline(ref, color="k", lw=0.8, ls=ls, label=f"{ref:g}x ATR ref")
    ax.set_yticks(y, labels, fontsize=5)
    ax.set_xlabel("lifetime excursion (ATR units, gross)")
    ax.set_title(f"{EXPERIMENT_ID}: per-cell MA lifetime MFE/MAE (native + hybrid; never pooled)")
    ax.legend(fontsize=6, loc="lower right")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_attribution_forest(records: list[dict[str, Any]], save_path: Path) -> None:
    """Per-cell A-RM median-MFE contrast CI_low for native + hybrid (non-4h marked)."""
    members = [r for r in records if r["member"]]
    rows = sorted([r for r in members if r.get("nat_rm_mfe_low_1s") is not None
                   and np.isfinite(r.get("nat_rm_mfe_low_1s", np.nan))],
                  key=lambda r: r["nat_rm_mfe_low_1s"])
    fig, ax = plt.subplots(figsize=(max(9, 0.18 * max(len(rows), 1)), 7))
    if not rows:
        _placeholder(save_path, "no powered native cells")
        return
    x = np.arange(len(rows))
    nat = np.array([r["nat_rm_mfe_low_1s"] for r in rows])
    nat_col = ["#1a9850" if r["nat_signal_attributable"] else "#d73027" for r in rows]
    ax.scatter(x, nat, c=nat_col, s=20, zorder=3,
               label="native A-RM median-MFE CI_low (binding)")
    hyb = np.array([r["hyb_rm_mfe_low_1s"] if r.get("hyb_rm_mfe_low_1s") is not None
                    else np.nan for r in rows])
    ax.scatter(x, hyb, facecolors="none", edgecolors="#4575b4", marker="s", s=20, zorder=2,
               label="hybrid A-RM median-MFE CI_low (binding)")
    ax.axhline(0.0, color="k", lw=0.8, ls="--")
    labels = [f"{'*' if r['domain'] != '4h' else ''}{r['instrument']}-{r['domain']}" for r in rows]
    ax.set_xticks(x, labels, rotation=90, fontsize=4)
    ax.set_ylabel("median-MFE difference CI_low(1s) (ATR units)")
    ax.set_title(f"{EXPERIMENT_ID}: harami beats matched-random on MA? native + hybrid (* = non-4h)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_mae_tail_decomposition(records: list[dict[str, Any]], save_path: Path) -> None:
    """P4: per-cell raw-mean vs 10%-trimmed MAE with worst-5% tail-share, native + hybrid."""
    members = [r for r in records if r["member"]]
    rows = sorted([r for r in members if r.get("ama_nat_mean_mae") is not None],
                  key=lambda r: r["ama_nat_mean_mae"])
    fig, ax = plt.subplots(figsize=(max(9, 0.18 * max(len(rows), 1)), 6))
    if not rows:
        _placeholder(save_path, "no powered native cells")
        return
    x = np.arange(len(rows))
    for prefix, colour, name in (("ama_nat", "#d73027", "native"),
                                 ("ama_hyb", "#4575b4", "hybrid")):
        mean_mae = np.array([r.get(f"{prefix}_mean_mae") if r.get(f"{prefix}_mean_mae") is not None
                             else np.nan for r in rows])
        trim_mae = np.array([r.get(f"{prefix}_mae_trim10") if r.get(f"{prefix}_mae_trim10") is not None
                             else np.nan for r in rows])
        ax.scatter(x, mean_mae, c=colour, s=18, label=f"{name} raw mean MAE", zorder=3)
        ax.scatter(x, trim_mae, facecolors="none", edgecolors=colour, marker="s", s=18,
                   label=f"{name} 10% trimmed MAE", zorder=2)
    ax2 = ax.twinx()
    tail = np.array([r.get("ama_nat_mae_tail_share5") if r.get("ama_nat_mae_tail_share5") is not None
                     else np.nan for r in rows])
    ax2.scatter(x, tail, c="#999999", s=10, marker="^", alpha=0.6, label="native worst-5% tail-share")
    ax2.set_ylabel("worst-5% tail-share of MAE (native)", fontsize=8)
    ax2.set_ylim(0.0, 1.0)
    ax.set_xticks(x, [f"{r['instrument']}-{r['domain']}" for r in rows], rotation=90, fontsize=4)
    ax.set_ylabel("MAE (ATR units, gross)")
    ax.set_title(f"{EXPERIMENT_ID} P4: MAE tail decomposition (downside-bounding preview -> L3)")
    ax.legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_status_heatmap(records: list[dict[str, Any]], save_path: Path) -> None:
    """MOVE_AVAILABLE / SIGNAL_ATTRIBUTABLE composition map -- native + hybrid panels."""
    domains = list(DOMAINS.keys())
    lookup = {(r["instrument"], r["domain"]): r for r in records}
    cmap = ListedColormap(ASTATUS_COLORS)
    norm = BoundaryNorm(np.arange(-0.5, len(ASTATUS_COLORS) + 0.5), cmap.N)
    fig, axes = plt.subplots(1, 2, figsize=(13, 9))
    for ax, (prefix, name) in zip(axes, (("nat", "native"), ("hyb", "hybrid"))):
        matrix = np.full((len(INSTRUMENTS), len(domains)), np.nan)
        for i, inst in enumerate(INSTRUMENTS):
            for j, dom in enumerate(domains):
                rec = lookup.get((inst, dom))
                if rec is not None and rec.get(f"{prefix}_status_code") is not None:
                    matrix[i, j] = float(rec[f"{prefix}_status_code"])
        ax.imshow(matrix, cmap=cmap, norm=norm, aspect="auto")
        arm = OBJ_ARM[prefix]
        for i, inst in enumerate(INSTRUMENTS):
            for j, dom in enumerate(domains):
                rec = lookup.get((inst, dom))
                if rec and rec.get(f"{arm}_m"):
                    tag = f"{rec[f'{arm}_m']}{'A' if rec.get(f'{prefix}_available_attributable') else ''}"
                    ax.text(j, i, tag, ha="center", va="center", fontsize=5)
        ax.set_xticks(range(len(domains)), domains)
        ax.set_yticks(range(len(INSTRUMENTS)), INSTRUMENTS, fontsize=7)
        ax.set_title(f"{name} (annotated: m; 'A'=attributable)")
    handles = [plt.Rectangle((0, 0), 1, 1, color=ASTATUS_COLORS[c]) for c in ASTATUS_CODES.values()]
    fig.legend(handles, list(ASTATUS_CODES.keys()), loc="upper center",
               ncol=len(ASTATUS_CODES), fontsize=8)
    fig.suptitle(f"{EXPERIMENT_ID}: per-object availability status (never pooled)", y=1.02)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def make_plots(records: list[dict[str, Any]]) -> None:
    """Render the four bounded plots from collected per-cell summaries (both objects)."""
    plot_forest(records, PLOTS_DIR / "per_cell_mfe_mae_forest.png")
    plot_attribution_forest(records, PLOTS_DIR / "a_ma_rm_ma_attribution_forest.png")
    plot_mae_tail_decomposition(records, PLOTS_DIR / "mae_tail_decomposition.png")
    plot_status_heatmap(records, PLOTS_DIR / "move_available_composition_map.png")


# --------------------------------------------------------------------------- #
# Orchestration (per-instrument ProcessPoolExecutor; fixed-order reassembly)
# --------------------------------------------------------------------------- #
def _cell_index_map() -> dict[tuple[str, str], int]:
    """Stable (instrument, domain) -> int index (identical to EXP-055/060/061)."""
    return {(inst, dom): i for i, (inst, dom) in enumerate(
        (inst, dom) for inst in INSTRUMENTS for dom in DOMAINS)}


def process_instrument(
    instrument: str, anchor: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    """Worker: resolve every member cell of one instrument (the parallel unit).

    Self-contained and pure given identical inputs/seeds: each cell's RNG is seeded
    by ``(BASE_SEED, cell_index, purpose)`` (order-independent), so the
    per-instrument result is identical regardless of worker count or finish order.
    The parent merges these in ``INSTRUMENTS`` order for byte-identical output. The
    first usable cell per instrument is replayed inside the worker (determinism gate).
    """
    cell_index = _cell_index_map()
    out: dict[str, Any] = {
        "records": [], "recon_rows": [], "meta": None, "causality": [],
        "invariant_violations": [], "determinism_checked": [], "non_deterministic": [],
        "reconciliation_mismatch": []}
    members = [d for d in DOMAINS if (instrument, d) not in EXCLUDED_CELLS]
    if not members:
        for domain in DOMAINS:
            out["records"].append(excluded_record(instrument, domain))
        return out
    train_1m, meta = load_train_1m(instrument)
    out["meta"] = meta
    replayed = False
    for domain in DOMAINS:
        if (instrument, domain) in EXCLUDED_CELLS:
            out["records"].append(excluded_record(instrument, domain))
            continue
        ci = cell_index[(instrument, domain)]
        cell = compute_cell(train_1m, domain, meta["train_end_epoch_s"], ci)
        out["records"].append(cell_record(instrument, cell))
        out["recon_rows"].append(exp055_reconciliation(instrument, cell, anchor))
        _record_cell_defects(cell, instrument, domain, out)
        if not replayed and not cell.get("empty") and cell["arms"]["a_ma_nat"].m > 0:
            ok = determinism_replay(train_1m, domain, meta["train_end_epoch_s"], ci, cell)
            out["determinism_checked"].append(f"{instrument}-{domain}#{ci}")
            if not ok:
                out["non_deterministic"].append(f"{instrument}-{domain}#{ci}")
            replayed = True
        del cell
    del train_1m
    return out


def _record_cell_defects(cell: dict[str, Any], instrument: str, domain: str,
                         out: dict[str, Any]) -> None:
    """Accumulate per-cell causality / window-invariant violations."""
    label = f"{instrument}-{domain}"
    if cell.get("empty"):
        return
    if not cell.get("causality_ok", True) or not cell.get("window_invariants_ok", True):
        out["causality"].append(label)
    if not cell.get("matched_count_ok", True):
        out["invariant_violations"].append(label)


def _run_grid(
    anchor: dict[tuple[str, str], dict[str, Any]], workers: int,
) -> list[dict[str, Any]]:
    """Resolve all instruments (process pool if workers>1) in fixed order."""
    if workers <= 1:
        return [process_instrument(inst, anchor)
                for inst in tqdm(INSTRUMENTS, desc="instruments")]
    by_inst: dict[str, dict[str, Any]] = {}
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(process_instrument, inst, anchor): inst for inst in INSTRUMENTS}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="instruments"):
            by_inst[futures[fut]] = fut.result()
    return [by_inst[inst] for inst in INSTRUMENTS]     # deterministic reassembly order


def run(workers: int = 1) -> dict[str, Any]:
    """Run all member cells and write artifacts. Returns the run summary.

    Output is byte-identical for any ``workers`` value (order-independent per-cell
    RNG + fixed merge order).
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    anchor = load_exp055_anchor()
    workers = max(1, min(workers, len(INSTRUMENTS)))
    grid = _run_grid(anchor, workers)
    records: list[dict[str, Any]] = []
    recon_rows: list[dict[str, Any]] = []
    instrument_meta: dict[str, Any] = {}
    defect = {"is_defect": False, "non_deterministic": [], "causality": [],
              "invariant_violations": [], "reconciliation_mismatch": [],
              "determinism_checked": [], "exp055_available": bool(anchor),
              "exp055_checked_cells": 0, "workers": workers}
    for instrument, res in zip(INSTRUMENTS, grid):     # fixed INSTRUMENTS order
        records.extend(res["records"])
        recon_rows.extend(res["recon_rows"])
        if res["meta"] is not None:
            instrument_meta[instrument] = res["meta"]
        for key in ("causality", "invariant_violations", "determinism_checked",
                    "non_deterministic"):
            defect[key].extend(res[key])
    _finalize_defects(defect, recon_rows)
    readout = composition_readout(records, defect)
    write_outputs(records, recon_rows, readout, instrument_meta, defect)
    make_plots(records)
    return _summarize(records, readout)


def _finalize_defects(defect: dict[str, Any], recon_rows: list[dict[str, Any]]) -> None:
    """Aggregate defect gates into the binding is_defect flag."""
    defect["reconciliation_mismatch"] = [r["cell"] for r in recon_rows
                                         if r.get("checked") and not r["consistent"]]
    defect["exp055_checked_cells"] = sum(1 for r in recon_rows if r.get("checked"))
    if defect["reconciliation_mismatch"]:
        defect["is_defect"] = True
    if not defect["exp055_available"] or defect["exp055_checked_cells"] == 0:
        defect["is_defect"] = True                     # P12: missing anchor is a defect
    causal_instr = {c.split("-")[0] for c in defect["causality"]}
    if len(causal_instr) >= P11_MIN_INSTR:
        defect["is_defect"] = True
    if defect["invariant_violations"]:
        defect["is_defect"] = True
    if defect["non_deterministic"]:
        defect["is_defect"] = True


def write_outputs(
    records: list[dict[str, Any]], recon_rows: list[dict[str, Any]],
    readout: dict[str, Any], instrument_meta: dict[str, Any], defect: dict[str, Any],
) -> None:
    """Persist per-cell parquet, the binding/secondary/tail CSVs, recon CSV, and JSONs."""
    df = pl.DataFrame(records, strict=False)
    df.write_parquet(RESULTS_DIR / "per_cell_availability.parquet")
    binding_cols = ["instrument", "domain", "member", "excluded", "n_harami", "n_retained",
                    "n_retained_hyb"]
    for prefix, arm in (("nat", "ama_nat"), ("hyb", "ama_hyb")):
        binding_cols += [
            f"{arm}_m", f"{arm}_median_mfe", f"{arm}_mfe_ci_low_1s", f"{arm}_median_mae",
            f"{arm}_mae_ci_low_1s", f"{prefix}_mfe_mult_ref_lo", f"{prefix}_mfe_mult_ref_hi",
            f"{prefix}_mfe_gt_mae", f"{prefix}_rm_mfe_low_1s", f"{prefix}_rm_mae_low_1s",
            f"{prefix}_censored_fraction", f"{prefix}_powered", f"{prefix}_move_available",
            f"{prefix}_signal_attributable", f"{prefix}_available_attributable",
            f"{prefix}_availability_status"]
    df.select([c for c in binding_cols if c in df.columns]).write_csv(
        RESULTS_DIR / "availability_map.csv")
    secondary_cols = [
        "instrument", "domain", "ama_nat_ha_m", "ama_nat_ha_median_mfe",
        "ama_nat_ha_mfe_ci_low_1s", "ama_nat_mad_m", "ama_nat_mad_median_mfe",
        "ama_nat_mad_mfe_ci_low_1s", "azz_m", "azz_median_mfe", "azz_mfe_ci_low_1s",
        "azz_median_mae", "rmma_nat_m", "rmma_nat_median_mfe", "rmma_nat_median_mae",
        "rmma_hyb_m", "rmma_hyb_median_mfe", "rmma_hyb_median_mae", "rmzz_m", "rmzz_median_mfe",
        "azz_rmzz_mfe_low_1s", "ama_nat_n_retained", "ama_nat_n_buildable", "ama_nat_n_censored",
        "ama_hyb_n_retained", "ama_hyb_n_buildable", "ama_hyb_n_censored"]
    df.select([c for c in secondary_cols if c in df.columns]).write_csv(
        RESULTS_DIR / "availability_secondary.csv")
    tail_cols = ["instrument", "domain"]
    for arm in ("ama_nat", "ama_hyb"):
        tail_cols += [
            f"{arm}_m", f"{arm}_median_mae", f"{arm}_mean_mae", f"{arm}_mae_mean_ci_low_1s",
            f"{arm}_mae_mean_ci_hi_2s", f"{arm}_mae_trim10", f"{arm}_mae_trim_ci_low_1s",
            f"{arm}_mae_tail_share5", f"{arm}_median_mfe", f"{arm}_mean_mfe",
            f"{arm}_mfe_trim10", f"{arm}_mfe_tail_share5"]
    df.select([c for c in tail_cols if c in df.columns]).write_csv(
        RESULTS_DIR / "mae_tail_decomposition.csv")
    recon_clean = [r for r in recon_rows if r.get("checked")]
    (pl.DataFrame(recon_clean, strict=False) if recon_clean
     else pl.DataFrame({"cell": []})).write_csv(RESULTS_DIR / "reconciliation.csv")
    with open(RESULTS_DIR / "composition_readout.json", "w") as fh:
        json.dump(readout, fh, indent=2, default=str)
    _write_metadata(instrument_meta, defect, recon_clean, readout)


def _write_metadata(
    instrument_meta: dict[str, Any], defect: dict[str, Any],
    recon_clean: list[dict[str, Any]], readout: dict[str, Any],
) -> None:
    """Persist the frozen-constants / provenance metadata JSON."""
    meta = {
        "experiment_id": EXPERIMENT_ID,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "015", "lead": "L2", "hypothesis": "HYP-015", "family": "CF-HA-HARAMI-001",
        "checkpoint": "2026-06-17-015-ma-substrate-conditioned-harami-full-surface",
        "amendment": "D0-amendment-001-dual-parallel-substrate (2026-06-17); supersedes prior EXP-062",
        "conditioning_objects": {
            "native (A_MA_nat)": "MA-segment /STRONG-STAT-conditioned entries; reconciles EXP-055 ma_seg",
            "hybrid (A_MA_hyb)": ("ZigZag /STRONG-STAT-conditioned entries x MA lifetime window; "
                                  "NEW object, no outcome anchor (mask verified via A_ZZ)"),
        },
        "stratum": "TRAIN-only (first 49%); nested TEST + final-30% holdout sealed",
        "population": ("native byte-identical to prior EXP-062 ma arm / EXP-055 ma_seg; "
                       "hybrid mask byte-identical to EXP-053/055/061 H0; never pooled"),
        "entry_anchor": "harami confirmation-bar real close (live, pre-confirm), shared by both objects",
        "lifetime_window": ("[entry+1, c2] where c2 = 2nd MA(20,50) crossover at/after the harami "
                            "(end of reversal MA segment M_b); shared MA window for both objects; "
                            "fewer than 2 MA crossovers before the TRAIN edge -> DATA_CENSORED"),
        "metrics": "ATR-normalised lifetime favourable MFE / adverse MAE (gross, real prices)",
        "reference_band": {"lines_atr": list(av.REF_LINES),
                           "use": "comparison/reporting yardstick only; never subtracted"},
        "binding_leg": ("per object: MOVE_AVAILABLE iff m>=30 AND median-MFE CI_low(1s)>1.0 ATR AND "
                        "median_MFE>median_MAE"),
        "signal_attribution_leg": ("per object: SIGNAL_ATTRIBUTABLE iff the object's A-RM median-MFE "
                                   "difference-bootstrap CI_low(1s)>0 (own-object matched-random on MA; P5)"),
        "objects": ["A_MA_nat (binding native)", "RM_MA_nat (native null)",
                    "A_MA_hyb (binding hybrid, NEW)", "RM_MA_hyb (hybrid null, NEW)",
                    "A_ZZ (ZigZag conditioned harami, disclosed contrast)",
                    "RM_ZZ (ZigZag matched-random, disclosed)"],
        "params": {
            "atr_period": ATR_PERIOD, "atr_mult": ATR_MULT,
            "ma_segmentation": [MA_FAST, MA_SLOW], "stat_window": 20, "stat_min_window": 5,
            "stat_q": 0.75, "ha_run_len": 3, "power_floor": POWER_FLOOR, "trim_frac": TRIM_FRAC,
            "tail_frac": TAIL_FRAC, "n_boot": N_BOOT, "boot_batch": BOOT_BATCH,
            "base_seed": BASE_SEED, "p11": [P11_MIN_CELLS, P11_MIN_INSTR],
            "p6_min_non_4h": P6_MIN_NON_4H,
        },
        "p4_diagnostic": ("per object: MAE (and MFE) raw mean CI + 10% trimmed-mean CI + worst-5% "
                          "largest-tail share, disclosed; never a viability gate. A thin top-heavy "
                          "MAE tail => bounded-downside-recoverable (sizes the L3/EXP-063 opportunity)."),
        "statistical_methods": [
            "median-MFE moving-block bootstrap CI (binding, per object); median-MAE likewise",
            "A-RM median-MFE difference bootstrap (binding signal attribution per object, P5); "
            "median-MAE disclosed; A_ZZ-RM_ZZ disclosed substrate contrast",
            "P4: raw-mean + 10% trimmed-mean moving-block bootstrap CI + worst-5% tail-share "
            "(disclosed diagnostic, per object)",
        ],
        "phase_verdict": readout["phase_verdict"],
        "phase_stronger_object": readout["phase_stronger_object"],
        "native_verdict": readout["native"]["verdict"],
        "hybrid_verdict": readout["hybrid"]["verdict"],
        "native_move_available_composes": readout["native"]["move_available"]["composes"],
        "hybrid_move_available_composes": readout["hybrid"]["move_available"]["composes"],
        "native_available_attributable_composes": readout["native"]["available_attributable"]["composes"],
        "hybrid_available_attributable_composes": readout["hybrid"]["available_attributable"]["composes"],
        "parallelism": {
            "workers": defect.get("workers", 1),
            "model": ("per-instrument ProcessPoolExecutor; results reassembled in fixed "
                      "INSTRUMENTS order; per-process native threads pinned to 1. Output is "
                      "byte-identical across worker counts: every RNG is seeded by "
                      "(BASE_SEED, cell_index, purpose) so draws are order-independent, OHLC "
                      "aggregation is order-independent, and the merge order is fixed. The "
                      "first usable cell per instrument is replayed byte-identically inside "
                      "its worker (determinism gate)."),
        },
        "determinism_ok": not defect["non_deterministic"],
        "determinism_checked": defect["determinism_checked"],
        "determinism_gate": ("byte-identical re-run of the first usable cell per instrument "
                             "across all arms (native/hybrid/ZigZag/HA/MAD + both MA nulls + "
                             "ZigZag null), all three contrasts, and both population digests."),
        "causality_ok": not defect["causality"],
        "causality_violations": defect["causality"],
        "causality_coverage": ("MFE,MAE>=0 + window invariants (entry+1<=c2<=train_last_idx, "
                               "c2==ma_confirm_idx[pos+1] with ma_confirm_idx[pos]>entry) on the "
                               "shared MA window; MA + ZigZag reference moves end at/before entry."),
        "invariant_violations": defect["invariant_violations"],
        "invariant_gates": ("matched-count holds per object (RM_MA_nat.draw_count == A_MA_nat.m; "
                            "RM_MA_hyb.draw_count == A_MA_hyb.m; RM_ZZ.draw_count == A_zz.m). "
                            "Reconciliation (SUBSTRATE/METHOD_DEFECT): A_MA_nat reproduces EXP-055 "
                            "ma_seg and A_ZZ reproduces EXP-055 stat per-cell m + median MFE + median "
                            "MAE to 1e-9; the hybrid A_MA_hyb has no outcome anchor (mask verified via "
                            "A_ZZ); a missing anchor is a defect."),
        "exp055_reconciliation": recon_clean,
        "reconciliation_mismatch": defect["reconciliation_mismatch"],
        "exp055_available": defect["exp055_available"],
        "exp055_checked_cells": defect["exp055_checked_cells"],
        "exp055_anchor": str(EXP055_PARQUET),
        "is_defect": defect["is_defect"],
        "de30_disclosure": DE30_DISCLOSURE,
        "holdout_fence": ("Only Parquet metadata + first train_rows file-order rows read per "
                          "instrument; full file never sorted/collected; every domain bar fenced "
                          "to CloseTime <= train_end_ts; excursion windows end at the M_b MA "
                          "crossover inside TRAIN (censored otherwise); TEST and final-30% "
                          "holdout never read."),
        "registry": ("CF-HA-HARAMI-001/HYP-015 (EXP-062); composes the registered MA-SUBSTRATE "
                     "(hybrid + native modes) lifetime availability + the per-object matched-random "
                     "nulls. 0 candidate slots, 0 TEST reads; characterisation readout feeds the "
                     "single terminal G-015 (no closure or registration here)."),
        "instrument_meta": instrument_meta,
    }
    with open(RESULTS_DIR / "run_metadata.json", "w") as fh:
        json.dump(meta, fh, indent=2, default=str)


def _summarize(records: list[dict[str, Any]], readout: dict[str, Any]) -> dict[str, Any]:
    """Concise stdout summary."""
    counts: dict[str, dict[str, int]] = {"nat": {}, "hyb": {}}
    for r in records:
        for prefix in ("nat", "hyb"):
            s = r[f"{prefix}_availability_status"]
            counts[prefix][s] = counts[prefix].get(s, 0) + 1
    return {"phase_verdict": readout["phase_verdict"],
            "phase_stronger_object": readout["phase_stronger_object"],
            "status_counts": counts, "native": readout["native"],
            "hybrid": readout["hybrid"], "defect": readout["defect"]}


def _parse_args() -> argparse.Namespace:
    """CLI: --workers controls per-instrument parallelism (default = all CPUs)."""
    parser = argparse.ArgumentParser(description=f"{EXPERIMENT_ID} MA-substrate availability (dual-object)")
    parser.add_argument(
        "--workers", type=int, default=(os.cpu_count() or 1),
        help="per-instrument process workers (default: all CPUs; 1 = sequential). "
             "Output is byte-identical for any value.")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = _parse_args()
    workers = max(1, min(args.workers, len(INSTRUMENTS)))
    LOGGER.info("%s: running %s instruments on %s worker(s)", EXPERIMENT_ID,
                len(INSTRUMENTS), workers)
    summary = run(workers=workers)
    LOGGER.info("\n=== %s complete (dual-object) ===", EXPERIMENT_ID)
    LOGGER.info("phase verdict: %s (stronger object: %s)", summary["phase_verdict"],
                summary["phase_stronger_object"])
    for prefix, name in (("native", "NATIVE"), ("hybrid", "HYBRID")):
        obj = summary[prefix]
        LOGGER.info("[%s] verdict=%s | MOVE_AVAILABLE %s cells/%s instr (non-4h %s; P11+P6=%s) | "
                    "attributable %s cells (P11+P6=%s)", name, obj["verdict"],
                    obj["move_available"]["n_cells"], obj["move_available"]["n_instruments"],
                    obj["move_available"]["n_non_4h"], obj["move_available"]["composes"],
                    obj["available_attributable"]["n_cells"],
                    obj["available_attributable"]["composes"])
    if summary["defect"]["is_defect"]:
        LOGGER.info("DEFECT: %s", json.dumps(summary["defect"], default=str))
    LOGGER.info("artifacts -> %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
