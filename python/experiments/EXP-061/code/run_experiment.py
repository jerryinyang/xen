"""EXP-061 — MA(20,50)-Substrate Capture Readiness & Benchmark-Geometry Conditioned Efficacy.

``CF-HA-HARAMI-001`` / HYP-014 — Phase 015 **lead L1** (dual conditioning object).
Governing design/D0: ``docs/experiments-docs/checkpoints/2026-06-17-015-ma-substrate-
conditioned-harami-full-surface/`` (``design.md`` §1/§3/§5/§7; ``D0-predeclarations.md`` P1-P12;
``D0-amendment-001-dual-parallel-substrate.md``). TRAIN-only, gross; **0 candidate slots,
0 TEST reads**.

**Re-run under D0 Amendment 001 (2026-06-17).** The prior EXP-061 measured a single MA arm
(``M0``) labelled *hybrid* but actually conditioned on MA-segment ``/STRONG-STAT`` — the **native**
object. The genuine **hybrid** object (ZigZag-``/STRONG-STAT`` mask x MA-segment geometry) was
never computed. This re-run emits **both** objects **individually** (never pooled) and supersedes
the prior result in place.

**The question (scope §Hypothesis), per object.** Does the EXP-060B MA-substrate signal edge —
which beat its own-substrate matched-random 85/99 only at the V2A x ``/ADV-NONE`` champion geometry
— **generalise to the benchmark 3-barrier geometry** (favourable = ``0.50*M_sofar``, adverse 1:1,
MA-defined adaptive cap), and does it depend on **where the strong-move filter is computed**
(ZigZag move = hybrid vs MA segment = native)? Two binding discriminators, judged individually:
**H0 (BENCH-MA-hybrid) vs RH0** and **M0 (BENCH-MA-native) vs RM0** — each median-viable
(CI_low>0, >=30 events) AND beating its own-object null (independent-contrast median CI_low>0)
AND clearing **P11 with the P6 non-4h rule** (>=5 cells / >=3 instruments / >=3 outside 4h).

The 6 arms: **H0** (BENCH-MA-hybrid, binding, NEW) / **RH0** (its null, NEW); **M0**
(BENCH-MA-native, binding) / **RM0** (its null); **Z0** (BENCH-ZZ, disclosed contrast) / **RZ0**
(its null). Corrected P12 reconciliation roles: native ``M0`` and ``Z0`` reproduce EXP-060B's
BENCH arms to ``1e-9``; **hybrid ``H0`` has no outcome anchor** (its ZigZag ``/STRONG-STAT``
conditioning mask is verified transitively via ``Z0``, which reconciles to EXP-053/060B
``n_conditioned``). The native/Z median+mean RNG paths stay byte-identical to EXP-060B; the
hybrid arms (``H0``: PB_HSEG*, ``RH0``: PB_RH0_*) and the trimmed-mean/RM0/RZ0 streams use disjoint
dedicated RNG purposes so no existing stream shifts. Mean + 10% trimmed mean + worst-5% tail-share
are the **P4 diagnostic** (disclosed; never a gate), per arm.

Binding endpoint = per-event **median** position-weighted gross ATR-normalised return (P3/P14,
P15 fills). Detection on HA candles; every outcome metric on real prices; MA(20,50) on real close.
Outputs under ``results/`` and ``plots/``; created in orchestration. Output is byte-identical for
any ``--workers`` value (order-independent per-cell RNG + fixed merge order).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
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
# P12 reconciliation anchor: EXP-060B's per-cell parquet carries the BENCH arms (M0/Z0).
EXP060B_PARQUET = EXPERIMENTS_ROOT / "EXP-060B" / "results" / "per_cell_expectancy.parquet"

from xen.bar_aggregator import aggregate_ohlc  # noqa: E402
from xen.capture_barriers import (  # noqa: E402
    CLASS_ADV,
    CLASS_DATA_CENSORED,
    CLASS_FAV,
)
from xen.expectancy import (  # noqa: E402
    InProgressState,
    adaptive_time_caps_by_epoch,
    benchmark_barriers,
    bootstrap_median_distribution,
    contrast_ci,
    live_in_progress_state,
    live_strong_stat,
    median_ci,
    qualifying_mask,
    realised_returns,
    resolve_path_ordered,
)
from xen.ha_harami import detect_ha_harami  # noqa: E402
from xen.heiken_ashi_generator import generate_heiken_ashi  # noqa: E402
from xen.position_exits import PX_CLASS_LABELS, exit_reason_weights  # noqa: E402
from xen.strong_move import annotate_ha_impulse  # noqa: E402
from xen.zigzag import generate_zigzag, wilder_atr  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (Phase 014-B / 015 D0 frozen + EXP-060/060B inherited; no tuning)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-061"
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
ATR_MULT = 1.0                     # P1 primary ZigZag
MA_FAST, MA_SLOW = 20, 50          # P1 MA-segmentation substrate (fixed, not swept)
POWER_FLOOR = 30                   # P10/P14: minimum qualifying events to report
P11_MIN_CELLS, P11_MIN_INSTR = 5, 3
P6_MIN_NON_4H = 3                  # P6: >=3 qualifying cells outside the 4h domain
TRIM_FRAC = 0.10                   # P4: 10% symmetric trimmed mean
TAIL_FRAC = 0.05                   # P4: worst-5% tail-share
RECON_TOL = 1e-9                   # P12 EXP-060B reproduction tolerance
N_BOOT = 10_000                    # P14 bootstrap resamples
BOOT_BATCH = 2_000                 # bounded bootstrap memory batch
BASE_SEED = 20260616               # frozen master seed (identical to EXP-060/060B)
EXCLUDED_FILE_MARKERS = ("analysis70", "analysis_slice", "first70")
DE30_DISCLOSURE = (
    "DE30 truncated history: broker m1 history ends 2026-01-16; counts derive "
    "from its own realized timeline and are not span-comparable (VAL-003).")
LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# Arm specification (only the BENCH geometry: 50% favourable x 1:1 adverse x cap)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ArmSpec:
    """The benchmark capture geometry (exact EXP-053/060B BENCH definition)."""

    aid: str
    idx: int                           # stable RNG offset (EXP-060B BENCH parity == 0)
    leg_fracs: tuple[float, ...]       # favourable distance fraction per leg
    weights: tuple[float, ...]         # leg weights (sum 1.0)
    is_bench: bool                     # BENCH: exact EXP-053 resolve_path_ordered path


# idx 0 == EXP-060B BENCH offset, so the M0/Z0 median+mean RNG streams reproduce exactly.
BENCH = ArmSpec("BENCH", 0, (1.0,), (1.0,), True)

# RNG purpose bases (distinct deterministic streams per cell/arm/purpose).
# Median + mean purposes are byte-identical to EXP-060B (P12 reproduction).
PB_STAT, PB_MASEG = 1000, 9000                  # Z0 / M0 median bootstrap
PB_STAT_MEAN, PB_MASEG_MEAN = 21000, 23000      # Z0 / M0 mean bootstrap
# New dedicated streams (never perturb the EXP-060B median/mean paths; reproduction-safe).
PB_STAT_TRIM, PB_MASEG_TRIM = 41000, 43000      # Z0 / M0 trimmed-mean bootstrap (P4)
PB_RZ0_DRAW, PB_RZ0_BOOT = 51000, 52000         # RZ0 (ZigZag BENCH null) draw/median
PB_RZ0_BOOT_MEAN, PB_RZ0_BOOT_TRIM = 53000, 54000
PB_RM0_DRAW, PB_RM0_BOOT = 61000, 62000         # RM0 (MA-native BENCH null) draw/median
PB_RM0_BOOT_MEAN, PB_RM0_BOOT_TRIM = 63000, 64000
# Hybrid object (NEW, D0 Amendment 001): ZigZag-/STRONG-STAT conditioning x MA-segment geometry.
# Dedicated streams so the native M0/RM0 and ZigZag Z0/RZ0 paths stay byte-identical.
PB_HSEG, PB_HSEG_MEAN, PB_HSEG_TRIM = 81000, 83000, 85000   # H0 hybrid signal median/mean/trim
PB_RH0_DRAW, PB_RH0_BOOT = 71000, 72000         # RH0 (MA-hybrid BENCH null) draw/median
PB_RH0_BOOT_MEAN, PB_RH0_BOOT_TRIM = 73000, 74000
# The H0-RH0 / M0-RM0 (binding, per object) and Z0-RZ0 (disclosed) contrasts are deterministic
# contrast_ci on the stored bootstrap distributions (no RNG).

# Per-cell MA-substrate generalisation status -> integer code (binding readout).
VSTATUS_CODES: dict[str, int] = {
    "GENERALISES": 0, "MEDIAN_VIABLE_NOT_GENERALISE": 1, "NOT_MEDIAN_VIABLE": 2,
    "NOT_POWERED": 3, "EXCLUDED": 4,
}


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ArmResult:
    """One arm's per-cell resolved population summary + qualifying returns.

    Carries the median (binding), mean + 10% trimmed mean + worst-5% tail-share
    (P4 diagnostic) point estimates and CIs, plus the per-event arrays and the
    median/mean bootstrap distributions used by the independent signal-vs-null
    contrasts.
    """

    m: int
    median: float | None
    mean: float | None
    trimmed_mean: float | None
    tail_share_worst5: float | None
    ci_low_1s: float | None
    ci_lo_2s: float | None
    ci_hi_2s: float | None
    mean_ci_low_1s: float | None
    mean_ci_lo_2s: float | None
    mean_ci_hi_2s: float | None
    trim_ci_low_1s: float | None
    trim_ci_lo_2s: float | None
    trim_ci_hi_2s: float | None
    r_firsthit: float | None       # single-leg BENCH arm (FAV/(FAV+TIMECAP)); disclosed
    win_rate: float | None
    data_censored: int
    exit_weights: dict[str, float]
    population: int                # built-barrier population (pre-resolution)
    block_len: int
    r_e: np.ndarray                # qualifying weighted returns in entry order
    dist: np.ndarray               # bootstrap median distribution (may be empty)
    mean_dist: np.ndarray          # bootstrap mean distribution (may be empty)
    draw_count: int = 0            # matched-random arms: the matched draw target


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


def load_exp060b_bench() -> dict[tuple[str, str], dict[str, Any]]:
    """Load EXP-060B's per-cell BENCH arms (M0/Z0) for the P12 reconciliation anchor.

    Returns, per (instrument, domain), the EXP-060B M0/Z0 qualifying count + median
    (the substrate-semantics anchor). A missing/empty anchor is SUBSTRATE/METHOD_DEFECT.
    """
    if not EXP060B_PARQUET.exists():
        return {}
    df = pl.read_parquet(EXP060B_PARQUET)
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for row in df.filter(pl.col("label").is_in(["M0", "Z0"])).iter_rows(named=True):
        if not row.get("member"):
            continue
        cell = out.setdefault((row["instrument"], row["domain"]), {})
        cell[row["label"]] = {"m": row.get("m"), "median": row.get("median")}
        # n_conditioned = EXP-053/060B ZigZag-/STRONG-STAT conditioned count (the hybrid-mask
        # anchor; identical across the M0/Z0 rows of a cell).
        if "n_conditioned" in row:
            cell["n_conditioned"] = row.get("n_conditioned")
    return out


# --------------------------------------------------------------------------- #
# Pure computation -- domain / substrate / harami alignment
# --------------------------------------------------------------------------- #
def build_domain(
    train_1m: pl.DataFrame, period_minutes: int, min_coverage: float | None,
    train_end_epoch: int,
) -> pl.DataFrame:
    """Aggregate one domain on the TRAIN slice and fence to the TRAIN edge."""
    bars = aggregate_ohlc(train_1m, period_minutes=period_minutes, min_coverage=min_coverage)
    return bars.filter(pl.col("CloseTime").dt.epoch("s") <= train_end_epoch)


def real_ohlc(bars: pl.DataFrame) -> dict[str, np.ndarray]:
    """Real-bar OHLC + CloseTime epochs (real prices only)."""
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
    """Confirmed-move arrays + confirm/start/end bar indices (exact match)."""
    if moves.height == 0:
        ei, ef = np.empty(0, dtype=np.int64), np.empty(0, dtype=np.float64)
        return {"confirm_epoch": ei, "end_epoch": ei, "end_price": ef, "start_price": ef,
                "direction": ei, "confirm_idx": ei, "start_idx": ei, "end_idx": ei,
                "magnitude": ef}
    confirm_epoch = moves.get_column("ConfirmTime").dt.epoch("s").to_numpy().astype(np.int64)
    start_epoch = moves.get_column("StartTime").dt.epoch("s").to_numpy().astype(np.int64)
    end_epoch = moves.get_column("EndTime").dt.epoch("s").to_numpy().astype(np.int64)
    start = moves.get_column("StartPrice").to_numpy().astype(np.float64)
    end = moves.get_column("EndPrice").to_numpy().astype(np.float64)
    return {
        "confirm_epoch": confirm_epoch, "end_epoch": end_epoch,
        "end_price": end, "start_price": start,
        "direction": moves.get_column("Direction").to_numpy().astype(np.int64),
        "confirm_idx": _map_to_grid(bar_epoch, confirm_epoch, "ConfirmTime"),
        "start_idx": _map_to_grid(bar_epoch, start_epoch, "StartTime"),
        "end_idx": _map_to_grid(bar_epoch, end_epoch, "EndTime"),
        "magnitude": np.abs(end - start),
    }


def ma_segment_moves(ohlc: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """MA(20,50)-crossover segmentation as a ZigZag-shaped confirmed-move set.

    Identical to EXP-060/060B's ``ma_segment_moves``: segments bounded by consecutive
    crossovers on the **real close**; the partial pre-first-crossover stretch is
    excluded by construction. MA(20,50) is the registered Phase 015 substrate (P1),
    fixed and not swept.
    """
    close, epoch = ohlc["close"], ohlc["epoch"]
    n = close.shape[0]
    empty = {k: np.empty(0, dtype=t) for k, t in (
        ("confirm_epoch", np.int64), ("end_epoch", np.int64), ("end_price", np.float64),
        ("start_price", np.float64), ("direction", np.int64), ("confirm_idx", np.int64),
        ("start_idx", np.int64), ("end_idx", np.int64), ("magnitude", np.float64))}
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
        "confirm_idx": e.astype(np.int64), "start_idx": s.astype(np.int64),
        "end_idx": e.astype(np.int64), "magnitude": np.abs(close[e] - close[s]),
    }


def _sma(values: np.ndarray, window: int) -> np.ndarray:
    """Trailing simple moving average; ``NaN`` until ``window`` values exist."""
    out = np.full(values.shape[0], np.nan, dtype=np.float64)
    if values.shape[0] < window:
        return out
    cs = np.cumsum(np.insert(values, 0, 0.0))
    out[window - 1:] = (cs[window:] - cs[:-window]) / window
    return out


def _subset_state(state: InProgressState, idx: np.ndarray) -> InProgressState:
    """Index every per-entry field of an InProgressState by ``idx``."""
    return InProgressState(
        valid=state.valid[idx], k=state.k[idx], rd=state.rd[idx],
        start_price=state.start_price[idx], start_epoch=state.start_epoch[idx],
        m_sofar=state.m_sofar[idx])


def _rng(cell_index: int, purpose: int) -> np.random.Generator:
    """Deterministic, independent per-cell-per-purpose RNG (reproducible)."""
    return np.random.default_rng([BASE_SEED, cell_index, purpose])


# --------------------------------------------------------------------------- #
# Pure computation -- mean / trimmed-mean moving-block bootstrap (block == median)
# --------------------------------------------------------------------------- #
def bootstrap_stat_distribution(
    values: np.ndarray, rng: np.random.Generator, statistic: str,
    n_boot: int = N_BOOT, batch: int = BOOT_BATCH,
) -> tuple[np.ndarray, int]:
    """Moving-block bootstrap distribution of the mean or 10% trimmed mean.

    Block construction is byte-identical to
    :func:`xen.expectancy.bootstrap_median_distribution` (``b = max(1,
    round(m**(1/3)))``; ``ceil(m/b)`` contiguous blocks per resample, truncated to
    ``m``); only the statistic changes. ``statistic`` is ``"mean"`` (raw mean) or
    ``"trim"`` (10% symmetric trimmed mean). Mean/trimmed-mean are tail-sensitive, so
    their CIs are wider than the median's -- that width quantifies the skew (the P4
    object under study), not a defect. Dedicated RNG so the median/mean paths are
    untouched.
    """
    m = int(values.shape[0])
    if m == 0:
        return np.empty(0, dtype=np.float64), 1
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
        if statistic == "mean":
            out[done:done + k] = np.mean(sample, axis=1)
        else:                                         # 10% symmetric trimmed mean
            out[done:done + k] = _trimmed_mean_rows(sample)
        done += k
    return out, b


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


def _tail_share_worst5(values: np.ndarray) -> float | None:
    """Fraction of total negative return contributed by the worst 5% of events.

    Worst 5% = the ``ceil(0.05*m)`` most-negative returns. Returns the ratio of their
    summed (negative) contribution to the total negative contribution -- a finite value
    in ``[0, 1]``. Zero when the cell has no negative return mass (never NaN/inf).
    """
    m = int(values.shape[0])
    if m == 0:
        return None
    total_neg = float(values[values < 0.0].sum())
    if total_neg >= 0.0:                              # no negative mass -> finite zero
        return 0.0
    k = max(1, int(np.ceil(TAIL_FRAC * m)))
    worst = np.sort(values)[:k]                       # k most-negative
    worst_neg = float(worst[worst < 0.0].sum())
    return float(worst_neg / total_neg)


# --------------------------------------------------------------------------- #
# Pure computation -- resolve one arm on one population -> ArmResult
# --------------------------------------------------------------------------- #
def resolve_arm(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, entry_close: np.ndarray,
    rd: np.ndarray, atr_entry: np.ndarray, arm: ArmSpec, fav: np.ndarray,
    adv: np.ndarray, n_event: np.ndarray, population: np.ndarray,
    rng: np.random.Generator, mean_rng: np.random.Generator,
    trim_rng: np.random.Generator, draw_count: int = 0,
) -> ArmResult:
    """Resolve the BENCH arm over ``population`` events; bootstrap median + mean + trim.

    BENCH reuses :func:`resolve_path_ordered` (the exact EXP-053 path: single
    favourable level at ``0.50*M_sofar``, a 1:1 adverse stop, the benchmark adaptive
    cap floor=6). The median path (``rng``) is byte-identical to EXP-060B; the mean CI
    (``mean_rng``) and the 10% trimmed-mean CI (``trim_rng``, NEW P4 diagnostic) use
    dedicated streams.
    """
    n_bars = ohlc["close"].shape[0]
    weights = np.asarray(arm.weights, dtype=np.float64)
    classes, exit_px = resolve_path_ordered(
        ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"], entry_idx,
        fav, adv, rd, n_event, population, n_bars)
    r_all = realised_returns(classes, exit_px, entry_close, rd, atr_entry)
    qual = population & qualifying_mask(classes, exit_px, atr_entry)
    leg_cls = classes[:, None]
    r_firsthit = _firsthit(classes, qual, CLASS_FAV, CLASS_ADV)
    censored = int((population & (classes == CLASS_DATA_CENSORED)).sum())
    order = np.argsort(entry_idx[qual], kind="stable")
    r_e = r_all[qual][order]
    exit_w = exit_reason_weights(leg_cls, weights, qual)
    return _summarize_arm(r_e, exit_w, r_firsthit, censored, int(population.sum()),
                          rng, mean_rng, trim_rng, draw_count)


def _firsthit(
    classes: np.ndarray, qual: np.ndarray, fav_code: int, other_code: int,
) -> float | None:
    """First-hit ratio FAV/(FAV+other) over qualifying single-leg events (disclosed)."""
    fav_n = int((qual & (classes == fav_code)).sum())
    other_n = int((qual & (classes == other_code)).sum())
    resolved = fav_n + other_n
    return (fav_n / resolved) if resolved > 0 else None


def _summarize_arm(
    r_e: np.ndarray, exit_w: dict[str, float], r_firsthit: float | None, censored: int,
    population: int, rng: np.random.Generator, mean_rng: np.random.Generator,
    trim_rng: np.random.Generator, draw_count: int = 0,
) -> ArmResult:
    """Assemble an ``ArmResult``; (if powered) bootstrap the median + mean + trim CIs."""
    m = int(r_e.shape[0])
    dist = np.empty(0, dtype=np.float64)
    mean_dist = np.empty(0, dtype=np.float64)
    block_len = max(1, int(round(max(m, 1) ** (1.0 / 3.0))))
    median = mean = trimmed = tail = None
    ci_low = ci_lo = ci_hi = None
    mean_low = mean_lo = mean_hi = None
    trim_low = trim_lo = trim_hi = None
    if m > 0:
        median = float(np.median(r_e))
        mean = float(np.mean(r_e))
        trimmed = _trimmed_mean(r_e)
        tail = _tail_share_worst5(r_e)
    if m >= POWER_FLOOR:
        dist, block_len = bootstrap_median_distribution(r_e, rng, n_boot=N_BOOT, batch=BOOT_BATCH)
        ci_low, ci_lo, ci_hi = median_ci(dist)
        mean_dist, _ = bootstrap_stat_distribution(r_e, mean_rng, "mean",
                                                    n_boot=N_BOOT, batch=BOOT_BATCH)
        mean_low, mean_lo, mean_hi = median_ci(mean_dist)        # generic percentile CI
        trim_dist, _ = bootstrap_stat_distribution(r_e, trim_rng, "trim",
                                                    n_boot=N_BOOT, batch=BOOT_BATCH)
        trim_low, trim_lo, trim_hi = median_ci(trim_dist)
    return ArmResult(
        m=m, median=median, mean=mean, trimmed_mean=trimmed, tail_share_worst5=tail,
        ci_low_1s=ci_low, ci_lo_2s=ci_lo, ci_hi_2s=ci_hi,
        mean_ci_low_1s=mean_low, mean_ci_lo_2s=mean_lo, mean_ci_hi_2s=mean_hi,
        trim_ci_low_1s=trim_low, trim_ci_lo_2s=trim_lo, trim_ci_hi_2s=trim_hi,
        r_firsthit=r_firsthit, win_rate=(float((r_e > 0).mean()) if m > 0 else None),
        data_censored=censored, exit_weights=exit_w, population=population,
        block_len=block_len, r_e=r_e, dist=dist, mean_dist=mean_dist, draw_count=draw_count)


def _empty_arm() -> ArmResult:
    return ArmResult(0, None, None, None, None, None, None, None, None, None, None,
                     None, None, None, None, None, 0,
                     {label: 0.0 for label in PX_CLASS_LABELS.values()}, 0, 1,
                     np.empty(0), np.empty(0), np.empty(0), 0)


# --------------------------------------------------------------------------- #
# Pure computation -- signal vs matched-random contrast (binding: median)
# --------------------------------------------------------------------------- #
def signal_vs_null_contrast(variant: ArmResult, null: ArmResult) -> dict[str, Any]:
    """Independent bootstrap contrast ``variant - null`` (median binding, mean disclosed).

    The benchmark signal arm (M0/Z0, indexed over haramis) and its matched-random
    control (RM0/RZ0, indexed over disjoint random in-regime draws) are **independent
    samples** -- no common per-event subset to pair. So the contrast is the
    independence-assuming :func:`xen.expectancy.contrast_ci` on the stored bootstrap
    distributions, mirroring EXP-060/060B's champion-vs-matched-random test. ``NaN``
    bounds when either distribution is empty (a power-limited arm).
    """
    med_low, med_lo, med_hi = contrast_ci(variant.dist, null.dist)
    mean_low, mean_lo, mean_hi = contrast_ci(variant.mean_dist, null.mean_dist)
    return {"median_low_1s": med_low, "median_lo_2s": med_lo, "median_hi_2s": med_hi,
            "mean_low_1s": mean_low, "mean_lo_2s": mean_lo, "mean_hi_2s": mean_hi,
            "variant_m": variant.m, "null_m": null.m}


# --------------------------------------------------------------------------- #
# Pure computation -- matched-random controls (the BENCH nulls RM0 / RZ0)
# --------------------------------------------------------------------------- #
def matched_random_arm(
    ohlc: dict[str, np.ndarray], state_all: InProgressState, mv: dict[str, np.ndarray],
    warmup_all: np.ndarray, atr_all: np.ndarray, signal_idx: np.ndarray,
    draw_count: int, cell_index: int, pb_draw: int, pb_boot: int,
    pb_boot_mean: int, pb_boot_trim: int,
) -> ArmResult:
    """Matched-count random control through the **benchmark** geometry (in-progress rd).

    Generic over the segmentation: ZigZag (RZ0) passes ZigZag ``state_all``/``mv``;
    MA (RM0, the NEW computation) passes the MA-segmentation analogs. The eligible pool
    is every in-regime bar (valid live state, positive ``m_sofar``, finite positive ATR,
    not in warmup) **excluding** the conditioned-harami entries; ``draw_count`` matched
    entries are drawn without replacement and resolved through the identical BENCH
    pipeline (50% x 1:1 x cap). RNG purposes are supplied so RM0/RZ0 use fresh dedicated
    streams (no EXP-060B stream shifts).
    """
    eligible = (state_all.valid & (state_all.m_sofar > 0.0) & np.isfinite(atr_all)
                & (atr_all > 0.0) & (~warmup_all))
    is_signal = np.zeros(ohlc["close"].shape[0], dtype=bool)
    is_signal[signal_idx] = True
    pool = np.flatnonzero(eligible & ~is_signal)
    if draw_count <= 0 or pool.shape[0] == 0:
        return _empty_arm()
    k = min(draw_count, pool.shape[0])
    drawn = np.sort(_rng(cell_index, pb_draw).choice(pool, size=k, replace=False))
    sub = _subset_state(state_all, drawn)
    bar = benchmark_barriers(ohlc["close"][drawn], sub.rd, sub.m_sofar)
    bench_n, bench_warmup = adaptive_time_caps_by_epoch(
        ohlc["epoch"][drawn], mv["confirm_epoch"], mv["confirm_idx"])
    pop = (sub.valid & (sub.m_sofar > 0.0) & np.isfinite(atr_all[drawn])
           & (atr_all[drawn] > 0.0) & ~bench_warmup)
    return resolve_arm(ohlc, drawn, ohlc["close"][drawn], sub.rd, atr_all[drawn], BENCH,
                       bar["fav"], bar["adv"], bench_n, pop, _rng(cell_index, pb_boot),
                       _rng(cell_index, pb_boot_mean), _rng(cell_index, pb_boot_trim),
                       draw_count=draw_count)


def bench_signal_arm(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, ctx: dict[str, Any],
    cell_index: int, pb_boot: int, pb_boot_mean: int, pb_boot_trim: int,
    cond_mask: np.ndarray | None = None,
) -> ArmResult:
    """BENCH signal arm on a substrate context's conditioned ``/STRONG-STAT`` population.

    ``ctx`` (ZigZag or MA) carries the precomputed harami-entry state / benchmark
    barriers / cap. The conditioning filter is a ``/STRONG-STAT`` p75 retained mask on
    top of ``buildable``. By default the mask is the context's own substrate filter
    (``ctx["stat"]["retained_p75"]``) -- this reproduces EXP-060B's BENCH arms exactly
    (Z0 from the ZigZag context, M0 from the MA context, both byte-identical).

    ``cond_mask`` overrides the conditioning filter while keeping ``ctx``'s geometry --
    used for the **hybrid** object H0 (D0 Amendment 001): the *ZigZag* ``/STRONG-STAT``
    mask applied to the *MA-segment* benchmark geometry. The native M0 leaves
    ``cond_mask=None``; H0 passes ``zz["stat"]["retained_p75"]`` with the MA ``ctx``.
    """
    if ctx.get("empty"):
        return _empty_arm()
    mask = ctx["stat"]["retained_p75"] if cond_mask is None else cond_mask
    pop = ctx["buildable"] & mask
    return resolve_arm(ohlc, entry_idx, ctx["entry_close"], ctx["state"].rd, ctx["atr_entry"],
                       BENCH, ctx["fav"], ctx["adv"], ctx["bench_n"], pop,
                       _rng(cell_index, pb_boot), _rng(cell_index, pb_boot_mean),
                       _rng(cell_index, pb_boot_trim))


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
    if entry_idx.shape[0] == 0 or mv["confirm_epoch"].shape[0] == 0:
        return {**base, "empty": True}

    zz = _zz_context(ohlc, atr, entry_idx, entry_epoch, mv)
    ma = _ma_context(ohlc, atr, entry_idx, entry_epoch)
    arms = _resolve_arms(ohlc, entry_idx, zz, ma, mv, cell_index)
    cond = zz["buildable"] & zz["stat"]["retained_p75"]
    return {
        **base, "empty": False, "arms": arms,
        "n_buildable": int(zz["buildable"].sum()), "n_conditioned": int(cond.sum()),
        "ma_conditioned": int((ma["buildable"] & ma["stat"]["retained_p75"]).sum()
                              ) if not ma["empty"] else 0,
        # hybrid_conditioned = ZigZag /STRONG-STAT mask under MA buildable (the H0 qualifying
        # count; a NEW disclosed quantity with no outcome anchor -- Amendment 001).
        "hybrid_conditioned": int((ma["buildable"] & zz["stat"]["retained_p75"]).sum()
                                  ) if not ma["empty"] else 0,
        "causality_ok": _causality_ok(ohlc, entry_idx, entry_epoch, zz["state"], mv, ma),
        "invariants": _cell_invariants(arms),
    }


def _zz_context(
    ohlc: dict[str, np.ndarray], atr: np.ndarray, entry_idx: np.ndarray,
    entry_epoch: np.ndarray, mv: dict[str, np.ndarray],
) -> dict[str, Any]:
    """ZigZag conditioned-signal context at the harami entries (Z0 + RZ0)."""
    entry_close = ohlc["close"][entry_idx]
    state = live_in_progress_state(entry_epoch, entry_close, mv["confirm_epoch"],
                                   mv["end_price"], mv["end_epoch"], mv["direction"])
    atr_entry = atr[entry_idx]
    bench_n, bench_warmup = adaptive_time_caps_by_epoch(
        entry_epoch, mv["confirm_epoch"], mv["confirm_idx"])
    buildable = (state.valid & (state.m_sofar > 0.0) & np.isfinite(atr_entry)
                 & (atr_entry > 0.0) & ~bench_warmup)
    stat = live_strong_stat(state.k, state.m_sofar, mv["magnitude"])
    bar = benchmark_barriers(entry_close, state.rd, state.m_sofar)
    return {"empty": False, "entry_close": entry_close, "state": state, "atr": atr,
            "atr_entry": atr_entry, "bench_n": bench_n, "buildable": buildable, "stat": stat,
            "fav_dist": bar["fav_dist"], "fav": bar["fav"], "adv": bar["adv"]}


def _ma_context(
    ohlc: dict[str, np.ndarray], atr: np.ndarray, entry_idx: np.ndarray,
    entry_epoch: np.ndarray,
) -> dict[str, Any]:
    """MA(20,50) conditioned-signal context at the harami entries (M0 + RM0).

    Built once per cell. Also exposes the MA-segmentation arrays for the RM0 control.
    """
    seg = ma_segment_moves(ohlc)
    if seg["confirm_epoch"].shape[0] == 0:
        return {"empty": True, "seg": seg}
    entry_close = ohlc["close"][entry_idx]
    atr_entry = atr[entry_idx]
    state = live_in_progress_state(entry_epoch, entry_close, seg["confirm_epoch"],
                                   seg["end_price"], seg["end_epoch"], seg["direction"])
    bench_n, bench_warmup = adaptive_time_caps_by_epoch(
        entry_epoch, seg["confirm_epoch"], seg["confirm_idx"])
    buildable = (state.valid & (state.m_sofar > 0.0) & np.isfinite(atr_entry)
                 & (atr_entry > 0.0) & ~bench_warmup)
    stat = live_strong_stat(state.k, state.m_sofar, seg["magnitude"])
    bar = benchmark_barriers(entry_close, state.rd, state.m_sofar)
    return {"empty": False, "seg": seg, "entry_close": entry_close, "state": state,
            "atr": atr, "atr_entry": atr_entry, "bench_n": bench_n, "buildable": buildable,
            "stat": stat, "fav_dist": bar["fav_dist"], "fav": bar["fav"], "adv": bar["adv"]}


def _resolve_arms(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, zz: dict[str, Any],
    ma: dict[str, Any], mv: dict[str, np.ndarray], cell_index: int,
) -> dict[str, Any]:
    """Resolve the 6 arms (two binding objects + disclosed ZigZag) + the per-object contrasts.

    Hybrid object (H0/RH0, NEW): ZigZag-``/STRONG-STAT`` conditioning x MA-segment geometry.
    Native object (M0/RM0): MA-segment-``/STRONG-STAT`` conditioning x MA geometry (byte-identical
    to EXP-060B BENCH-MA). ZigZag (Z0/RZ0): disclosed substrate contrast. The two MA objects are
    measured/reported individually -- never pooled (D0 Amendment 001).
    """
    # Z0 / M0 -- byte-identical to EXP-060B BENCH (ctx own-substrate /STRONG-STAT mask).
    z0 = bench_signal_arm(ohlc, entry_idx, zz, cell_index, PB_STAT, PB_STAT_MEAN, PB_STAT_TRIM)
    m0 = bench_signal_arm(ohlc, entry_idx, ma, cell_index, PB_MASEG, PB_MASEG_MEAN, PB_MASEG_TRIM)
    # H0 -- hybrid signal arm: ZigZag /STRONG-STAT mask through the MA benchmark geometry (NEW).
    h0 = (bench_signal_arm(ohlc, entry_idx, ma, cell_index, PB_HSEG, PB_HSEG_MEAN, PB_HSEG_TRIM,
                           cond_mask=zz["stat"]["retained_p75"])
          if not ma["empty"] else _empty_arm())
    rz0, rm0, rh0 = _resolve_nulls(ohlc, entry_idx, zz, ma, mv, z0.m, m0.m, h0.m, cell_index)
    contrasts = {
        "h0_rh0": signal_vs_null_contrast(h0, rh0),     # binding discriminator -- HYBRID
        "m0_rm0": signal_vs_null_contrast(m0, rm0),     # binding discriminator -- NATIVE
        "z0_rz0": signal_vs_null_contrast(z0, rz0),     # disclosed substrate contrast
    }
    return {"h0": h0, "m0": m0, "z0": z0, "rh0": rh0, "rm0": rm0, "rz0": rz0,
            "contrasts": contrasts}


def _resolve_nulls(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, zz: dict[str, Any],
    ma: dict[str, Any], mv: dict[str, np.ndarray], z0_m: int, m0_m: int, h0_m: int,
    cell_index: int,
) -> tuple[ArmResult, ArmResult, ArmResult]:
    """RZ0 (ZigZag BENCH null), RM0 (MA-native BENCH null), RH0 (MA-hybrid BENCH null, NEW).

    RM0 and RH0 share the MA in-regime eligible pool but are matched to their **own** object's
    qualifying count and exclude their **own** object's signal entries; they use disjoint
    dedicated RNG streams so neither perturbs the other or the EXP-060B paths.
    """
    # RZ0 -- ZigZag substrate, benchmark geometry.
    zz_state_all = live_in_progress_state(ohlc["epoch"], ohlc["close"], mv["confirm_epoch"],
                                          mv["end_price"], mv["end_epoch"], mv["direction"])
    _, zz_warmup_all = adaptive_time_caps_by_epoch(
        ohlc["epoch"], mv["confirm_epoch"], mv["confirm_idx"])
    zz_signal_idx = entry_idx[zz["stat"]["retained_p75"]]
    rz0 = matched_random_arm(ohlc, zz_state_all, mv, zz_warmup_all, zz["atr"], zz_signal_idx,
                             z0_m, cell_index, PB_RZ0_DRAW, PB_RZ0_BOOT, PB_RZ0_BOOT_MEAN,
                             PB_RZ0_BOOT_TRIM)
    # RM0 / RH0 -- MA substrate, benchmark geometry (binding nulls, per object).
    if ma["empty"]:
        return rz0, _empty_arm(), _empty_arm()
    seg = ma["seg"]
    ma_state_all = live_in_progress_state(ohlc["epoch"], ohlc["close"], seg["confirm_epoch"],
                                          seg["end_price"], seg["end_epoch"], seg["direction"])
    _, ma_warmup_all = adaptive_time_caps_by_epoch(
        ohlc["epoch"], seg["confirm_epoch"], seg["confirm_idx"])
    ma_signal_idx = entry_idx[ma["stat"]["retained_p75"]]          # native signal entries
    rm0 = matched_random_arm(ohlc, ma_state_all, seg, ma_warmup_all, ma["atr"], ma_signal_idx,
                             m0_m, cell_index, PB_RM0_DRAW, PB_RM0_BOOT, PB_RM0_BOOT_MEAN,
                             PB_RM0_BOOT_TRIM)
    h_signal_idx = entry_idx[zz["stat"]["retained_p75"]]           # hybrid signal entries
    rh0 = matched_random_arm(ohlc, ma_state_all, seg, ma_warmup_all, ma["atr"], h_signal_idx,
                             h0_m, cell_index, PB_RH0_DRAW, PB_RH0_BOOT, PB_RH0_BOOT_MEAN,
                             PB_RH0_BOOT_TRIM)
    return rz0, rm0, rh0


# --------------------------------------------------------------------------- #
# Per-cell causality / invariant gate
# --------------------------------------------------------------------------- #
def _causality_ok(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, entry_epoch: np.ndarray,
    state: InProgressState, mv: dict[str, np.ndarray], ma: dict[str, Any],
) -> bool:
    """Strict grid + causal reference moves (ZigZag and MA) + entry <= t_i."""
    epoch = ohlc["epoch"]
    if epoch.shape[0] >= 2 and not bool(np.all(np.diff(epoch) > 0)):
        return False                                   # duplicate/disordered CloseTime
    valid = state.valid & (state.k >= 0)
    if valid.any():
        kk = state.k[valid]
        if not bool(np.all(mv["end_epoch"][kk] <= entry_epoch[valid])):
            return False                               # ZigZag reference ends at/before entry
        if not bool(np.all(epoch[entry_idx[valid]] <= entry_epoch[valid])):
            return False                               # entry bar is itself (<= t_i)
    if not ma["empty"]:                                # MA reference confirmed before entry
        mvalid = ma["state"].valid & (ma["state"].k >= 0)
        if mvalid.any():
            mk = ma["state"].k[mvalid]
            if not bool(np.all(ma["seg"]["end_epoch"][mk] <= entry_epoch[mvalid])):
                return False
    return True


def _cell_invariants(arms: dict[str, Any]) -> dict[str, bool]:
    """Predeclared structural invariants (scope §Success/Failure (iv)-(vi))."""
    # (weights) BENCH single-leg weight sums to 1.0.
    weights_ok = abs(sum(BENCH.weights) - 1.0) <= 1e-12
    # (vi) the 1:1 stop's exit composition is well-formed (FAV+ADV+TIMECAP+CENSORED weights
    # sum to 1.0 on each qualifying population) -- a finite, real-bar P15 resolution.
    bench_exit_ok = all(
        (res.m == 0) or abs(sum(res.exit_weights.values()) - 1.0) <= 1e-9
        for res in (arms["h0"], arms["m0"], arms["z0"],
                    arms["rh0"], arms["rm0"], arms["rz0"]))
    # (v) matched-count holds per object: each null's draw target == its signal arm's qualifying m.
    matched_ok = (arms["rz0"].draw_count == arms["z0"].m
                  and arms["rm0"].draw_count == arms["m0"].m
                  and arms["rh0"].draw_count == arms["h0"].m)
    return {"weights_sum_ok": bool(weights_ok), "bench_exit_ok": bool(bench_exit_ok),
            "matched_count_ok": bool(matched_ok)}


# --------------------------------------------------------------------------- #
# Per-cell record flattening
# --------------------------------------------------------------------------- #
def _arm_fields(res: ArmResult) -> dict[str, Any]:
    """Flatten one ArmResult's scalar metrics + exit-reason weights (no arrays)."""
    gap = (res.median - res.mean) if (res.median is not None and res.mean is not None) else None
    out = {
        "m": res.m, "median": res.median, "mean": res.mean, "trimmed_mean": res.trimmed_mean,
        "tail_share_worst5": res.tail_share_worst5, "gap": gap,
        "ci_low_1s": res.ci_low_1s, "ci_lo_2s": res.ci_lo_2s, "ci_hi_2s": res.ci_hi_2s,
        "mean_ci_low_1s": res.mean_ci_low_1s, "mean_ci_lo_2s": res.mean_ci_lo_2s,
        "mean_ci_hi_2s": res.mean_ci_hi_2s, "trim_ci_low_1s": res.trim_ci_low_1s,
        "trim_ci_lo_2s": res.trim_ci_lo_2s, "trim_ci_hi_2s": res.trim_ci_hi_2s,
        "r_firsthit": res.r_firsthit, "win_rate": res.win_rate,
        "data_censored": res.data_censored, "population": res.population,
        "block_len": res.block_len, "draw_count": res.draw_count,
    }
    out.update({f"ew_{label}": res.exit_weights[label] for label in PX_CLASS_LABELS.values()})
    return out


def _viability(res: ArmResult) -> tuple[bool, bool]:
    """(median CI_low>0 and m>=floor, powered)."""
    powered = res.m >= POWER_FLOOR
    viable = bool(powered and res.ci_low_1s is not None
                  and np.isfinite(res.ci_low_1s) and res.ci_low_1s > 0.0)
    return viable, powered


def _mean_viable(res: ArmResult) -> bool:
    """Disclosed P4 flag (never a viability gate)."""
    return bool(res.m >= POWER_FLOOR and res.mean_ci_low_1s is not None
                and np.isfinite(res.mean_ci_low_1s) and res.mean_ci_low_1s > 0.0)


def object_rows(instrument: str, cell: dict[str, Any]) -> list[dict[str, Any]]:
    """The 6 arms (H0/RH0 hybrid, M0/RM0 native, Z0/RZ0 zigzag) for one cell, object-tagged."""
    common = {"instrument": instrument, "domain": cell["domain"], "member": True,
              "excluded": False, "n_bars": cell["n_bars"], "n_moves": cell["n_moves"],
              "n_harami": cell["n_harami"], "n_conditioned": cell["n_conditioned"],
              "ma_conditioned": cell["ma_conditioned"],
              "hybrid_conditioned": cell.get("hybrid_conditioned", 0)}
    arms = cell["arms"]
    rows: list[dict[str, Any]] = []
    for label, obj, substrate, role, res in (
            ("H0", "hybrid", "MA", "signal", arms["h0"]),
            ("M0", "native", "MA", "signal", arms["m0"]),
            ("Z0", "zigzag", "ZigZag", "signal", arms["z0"]),
            ("RH0", "hybrid", "MA-random", "null", arms["rh0"]),
            ("RM0", "native", "MA-random", "null", arms["rm0"]),
            ("RZ0", "zigzag", "ZigZag-random", "null", arms["rz0"])):
        viable, _ = _viability(res)
        rows.append({**common, "label": label, "object": obj, "substrate": substrate,
                     "role": role, "geometry": "BENCH", "median_viable": viable,
                     "mean_viable": _mean_viable(res), **_arm_fields(res)})
    return rows


# Per-object binding discriminator: (object name, signal arm key, null arm key, contrast key).
EFFICACY_OBJECTS: tuple[tuple[str, str, str, str], ...] = (
    ("hybrid", "h0", "rh0", "h0_rh0"),
    ("native", "m0", "rm0", "m0_rm0"),
)


def object_efficacy_rows(instrument: str, cell: dict[str, Any]) -> list[dict[str, Any]]:
    """Per-object signal-vs-null discriminator rows (hybrid and native), reported individually.

    One row per binding object; never pooled. Each carries the object's signal arm summary, its
    own matched-random null contrast, and the per-cell generalisation flags + status.
    """
    arms = cell["arms"]
    rows: list[dict[str, Any]] = []
    for obj, sig_key, null_key, c_key in EFFICACY_OBJECTS:
        rows.append(_efficacy_row(instrument, cell, obj, arms[sig_key], arms[null_key],
                                  arms["contrasts"][c_key]))
    return rows


def _efficacy_row(
    instrument: str, cell: dict[str, Any], obj: str, sig: ArmResult, null: ArmResult,
    c: dict[str, Any],
) -> dict[str, Any]:
    """One object's per-cell discriminator row (common schema across objects)."""
    median_viable, sig_powered = _viability(sig)
    null_powered = null.m >= POWER_FLOOR
    beats_null = bool(np.isfinite(c["median_low_1s"]) and c["median_low_1s"] > 0.0)
    generalises = bool(median_viable and beats_null)
    if cell["domain"] is None:
        status = "EXCLUDED"
    elif not (sig_powered and null_powered):
        status = "NOT_POWERED"
    elif generalises:
        status = "GENERALISES"
    elif median_viable:
        status = "MEDIAN_VIABLE_NOT_GENERALISE"
    else:
        status = "NOT_MEDIAN_VIABLE"
    return {
        "instrument": instrument, "domain": cell["domain"], "object": obj,
        "sig_m": sig.m, "null_m": null.m, "null_draw_count": null.draw_count,
        "sig_median": sig.median, "sig_ci_low_1s": sig.ci_low_1s,
        "sig_mean": sig.mean, "sig_mean_ci_low_1s": sig.mean_ci_low_1s,
        "sig_trimmed_mean": sig.trimmed_mean, "sig_trim_ci_low_1s": sig.trim_ci_low_1s,
        "sig_tail_share_worst5": sig.tail_share_worst5,
        "contrast_median_low_1s": c["median_low_1s"], "contrast_median_hi_2s": c["median_hi_2s"],
        "contrast_mean_low_1s": c["mean_low_1s"],
        "sig_powered": sig_powered, "null_powered": null_powered,
        "median_viable": median_viable, "mean_viable": _mean_viable(sig),
        "beats_null": beats_null, "generalises": generalises,
        "viable_status": status, "status_code": VSTATUS_CODES[status],
    }


def substrate_contrast_row(instrument: str, cell: dict[str, Any]) -> dict[str, Any]:
    """Disclosed substrate contrast row (H0-RH0, M0-RM0, Z0-RZ0 by cell/domain)."""
    arms = cell["arms"]
    ch, cm, cz = (arms["contrasts"]["h0_rh0"], arms["contrasts"]["m0_rm0"],
                  arms["contrasts"]["z0_rz0"])
    z0 = arms["z0"]
    z0_median_viable, _ = _viability(z0)
    z0_beats_rz0 = bool(np.isfinite(cz["median_low_1s"]) and cz["median_low_1s"] > 0.0)
    return {
        "instrument": instrument, "domain": cell["domain"],
        "h0_rh0_median_low_1s": ch["median_low_1s"], "h0_rh0_mean_low_1s": ch["mean_low_1s"],
        "m0_rm0_median_low_1s": cm["median_low_1s"], "m0_rm0_mean_low_1s": cm["mean_low_1s"],
        "z0_rz0_median_low_1s": cz["median_low_1s"], "z0_rz0_mean_low_1s": cz["mean_low_1s"],
        "z0_m": z0.m, "z0_median": z0.median, "z0_median_viable": z0_median_viable,
        "z0_beats_rz0": z0_beats_rz0,
    }


def readiness_row(instrument: str, cell: dict[str, Any]) -> dict[str, Any]:
    """Per-cell readiness/construction row (coverage + causality + invariant flags)."""
    inv = cell.get("invariants", {})
    arms = cell["arms"]
    return {
        "instrument": instrument, "domain": cell["domain"], "n_bars": cell["n_bars"],
        "n_moves": cell["n_moves"], "n_harami": cell["n_harami"],
        "n_conditioned": cell["n_conditioned"], "ma_conditioned": cell["ma_conditioned"],
        "hybrid_conditioned": cell.get("hybrid_conditioned", 0),
        "h0_m": arms["h0"].m, "m0_m": arms["m0"].m, "z0_m": arms["z0"].m,
        "rh0_m": arms["rh0"].m, "rm0_m": arms["rm0"].m, "rz0_m": arms["rz0"].m,
        "h0_data_censored": arms["h0"].data_censored,
        "m0_data_censored": arms["m0"].data_censored,
        "causality_ok": cell.get("causality_ok", True),
        "weights_sum_ok": inv.get("weights_sum_ok", True),
        "bench_exit_ok": inv.get("bench_exit_ok", True),
        "matched_count_ok": inv.get("matched_count_ok", True),
        "construction_pass": bool(cell.get("causality_ok", True)
                                  and all(inv.get(k, True) for k in inv)),
    }


def excluded_rows(
    instrument: str, domain: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    """COVERAGE_EXCLUDED placeholder rows for one cell (6 arms + 2 per-object efficacy rows)."""
    common = {"instrument": instrument, "domain": domain, "member": False, "excluded": True,
              "n_bars": None, "n_moves": None, "n_harami": None, "n_conditioned": None,
              "ma_conditioned": None, "hybrid_conditioned": None}
    obj_rows = []
    for label, obj, substrate in (("H0", "hybrid", "MA"), ("M0", "native", "MA"),
                                  ("Z0", "zigzag", "ZigZag"), ("RH0", "hybrid", "MA-random"),
                                  ("RM0", "native", "MA-random"),
                                  ("RZ0", "zigzag", "ZigZag-random")):
        obj_rows.append({**common, "label": label, "object": obj, "substrate": substrate,
                         "role": "excluded", "geometry": "BENCH", "median_viable": False,
                         "mean_viable": False, **_arm_fields(_empty_arm())})
    efficacy = [{"instrument": instrument, "domain": domain, "object": obj,
                 "viable_status": "EXCLUDED", "status_code": VSTATUS_CODES["EXCLUDED"],
                 "sig_powered": False, "null_powered": False, "median_viable": False,
                 "mean_viable": False, "beats_null": False, "generalises": False}
                for obj in ("hybrid", "native")]
    contrast = {"instrument": instrument, "domain": domain, "z0_median_viable": False,
                "z0_beats_rz0": False}
    ready = {"instrument": instrument, "domain": domain, "construction_pass": None,
             "causality_ok": None}
    return obj_rows, efficacy, contrast, ready


# --------------------------------------------------------------------------- #
# Composition + verdict readout (P11 with the P6 non-4h rule)
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


def generalisation_readout(
    efficacy_rows: list[dict[str, Any]], contrast_rows: list[dict[str, Any]],
    defect: dict[str, Any],
) -> dict[str, Any]:
    """Per-object P11/P6 composition + EVIDENCE_* verdict for each object (hybrid, native).

    The two objects are composed and classified **individually** (never pooled). The phase-level
    verdict is the stronger object's outcome (design.md §7); both per-object verdicts are recorded.
    """
    objects: dict[str, Any] = {}
    for obj in ("hybrid", "native"):
        cells = [r for r in efficacy_rows
                 if r.get("object") == obj and r.get("viable_status") != "EXCLUDED"]
        powered = _p11([r for r in cells if r.get("sig_powered") and r.get("null_powered")],
                       "sig_powered")
        objects[obj] = {
            "verdict": _verdict(defect, _p11(cells, "generalises"), powered),
            "powered": powered, "median_viable": _p11(cells, "median_viable"),
            "beats_null": _p11(cells, "beats_null"), "mean_viable": _p11(cells, "mean_viable"),
            "generalises": _p11(cells, "generalises"),
        }
    z0_beats = _p11([r for r in contrast_rows if r.get("instrument")], "z0_beats_rz0")
    return {
        "verdict": _phase_verdict(defect, objects),
        "hybrid": objects["hybrid"], "native": objects["native"],
        "binding_objects": {
            "hybrid": "H0 (BENCH-MA-hybrid: ZigZag /STRONG-STAT x MA 50%x1:1xcap)",
            "native": "M0 (BENCH-MA-native: MA-segment /STRONG-STAT x MA 50%x1:1xcap)"},
        "binding_discriminator": ("per object, individually: H0-RH0 (hybrid) and M0-RM0 (native) "
                                  "independent-contrast median CI_low>0 (own-object matched-random "
                                  "null, identical MA benchmark pipeline). Never pooled."),
        "z0_beats_rz0_disclosed": z0_beats, "defect": defect,
        "rule": ("Binding endpoint = median (P14); mean + 10% trimmed mean + worst-5% tail-share "
                 "disclosed (P4, never a gate). Per cell (m>=30), per object: median_viable = "
                 "signal median CI_low(1s)>0; beats_null = (signal-null) independent-contrast "
                 "median CI_low(1s)>0; generalises = both. EVIDENCE_FOR (per object) iff its "
                 "generalises composes P11 with the P6 non-4h rule (>=5 cells / >=3 instruments / "
                 ">=3 cells outside 4h). EVIDENCE_AGAINST iff its powered grid composes P11 but "
                 "generalises does not. INCONCLUSIVE iff fewer than the P11 quorum of cells are "
                 "powered (>=30 events on signal and null). SUBSTRATE_METHOD_DEFECT on any "
                 "reconciliation / determinism / causality / invariant failure. Objects are "
                 "judged individually; the phase verdict is the stronger object's."),
        "g015_routing": ("Feeds the single terminal G-015 after the full Phase 015 slate (no "
                         "closure or candidate registration here). Each object's EVIDENCE_* is an "
                         "independent G-015 input. Family stays OPEN; the surface runs regardless "
                         "(P9 no-early-closure)."),
    }


def _verdict(defect: dict[str, Any], generalises: dict[str, Any],
             powered: dict[str, Any]) -> str:
    """Mechanical per-object EVIDENCE_FOR/AGAINST/INCONCLUSIVE verdict."""
    if defect["is_defect"]:
        return "SUBSTRATE_METHOD_DEFECT"
    if generalises["composes"]:
        return "EVIDENCE_FOR"
    if not powered["composes"]:
        return "INCONCLUSIVE_POWER_LIMITED"
    return "EVIDENCE_AGAINST"


def _phase_verdict(defect: dict[str, Any], objects: dict[str, Any]) -> str:
    """Phase-level verdict = the stronger object's outcome (design.md §7)."""
    if defect["is_defect"]:
        return "SUBSTRATE_METHOD_DEFECT"
    verdicts = {objects["hybrid"]["verdict"], objects["native"]["verdict"]}
    if "EVIDENCE_FOR" in verdicts:
        return "EVIDENCE_FOR"
    if verdicts == {"INCONCLUSIVE_POWER_LIMITED"}:
        return "INCONCLUSIVE_POWER_LIMITED"
    return "EVIDENCE_AGAINST"


# --------------------------------------------------------------------------- #
# Determinism replay + EXP-060B reconciliation (DEFECT guards)
# --------------------------------------------------------------------------- #
def determinism_replay(train_1m: pl.DataFrame, domain: str, train_end_epoch: int,
                       cell_index: int) -> bool:
    """Re-run one cell end-to-end and assert byte-identical binding outputs."""
    a = compute_cell(train_1m, domain, train_end_epoch, cell_index)
    b = compute_cell(train_1m, domain, train_end_epoch, cell_index)
    if a.get("empty") or b.get("empty"):
        return a.get("empty") == b.get("empty")
    for key in ("h0", "m0", "z0", "rh0", "rm0", "rz0"):
        sa, sb = a["arms"][key], b["arms"][key]
        if not (np.array_equal(sa.r_e, sb.r_e)
                and (sa.median, sa.ci_low_1s, sa.mean_ci_low_1s, sa.trim_ci_low_1s)
                == (sb.median, sb.ci_low_1s, sb.mean_ci_low_1s, sb.trim_ci_low_1s)):
            return False
    for ckey in ("h0_rh0", "m0_rm0"):
        ca, cb = a["arms"]["contrasts"][ckey], b["arms"]["contrasts"][ckey]
        if not (_nan_eq(ca["median_low_1s"], cb["median_low_1s"])
                and _nan_eq(ca["mean_low_1s"], cb["mean_low_1s"])):
            return False
    return True


def _nan_eq(a: float, b: float) -> bool:
    """Float equality that treats NaN == NaN as True (for power-limited contrasts)."""
    if a is None or b is None:
        return a is b
    return bool(a == b or (np.isnan(a) and np.isnan(b)))


def exp060b_reconciliation(
    instrument: str, cell: dict[str, Any], anchor: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    """P12 reproduction guard vs EXP-060B BENCH arms (scope invariants i, ii).

    (i) M0 reproduces EXP-060B BENCH-MA (M0) per-cell median + qualifying count;
    (ii) Z0 reproduces EXP-060B BENCH-ZZ (Z0) likewise. Any divergence beyond
    ``RECON_TOL`` is SUBSTRATE/METHOD_DEFECT.
    """
    key = (instrument, cell["domain"])
    if not anchor or key not in anchor or cell.get("empty"):
        return {"checked": False, "cell": f"{instrument}-{cell.get('domain')}"}
    src = anchor[key]
    m0, z0, h0 = cell["arms"]["m0"], cell["arms"]["z0"], cell["arms"]["h0"]
    src_m0, src_z0 = src.get("M0", {}), src.get("Z0", {})
    m0_ok = (m0.m == (int(src_m0["m"]) if src_m0.get("m") is not None else 0)
             and _float_match(m0.median, src_m0.get("median")))
    z0_ok = (z0.m == (int(src_z0["m"]) if src_z0.get("m") is not None else 0)
             and _float_match(z0.median, src_z0.get("median")))
    # Hybrid (H0) has NO outcome anchor (NEW object). Its ZigZag /STRONG-STAT conditioning mask is
    # the same mask that defines Z0's population (= EXP-053/060B conditioned set), so the
    # conditioning is verified transitively by z0_ok (Z0.m == EXP-060B n_conditioned, exact).
    # H0's qualifying count under MA geometry is disclosed as new.
    h0_cond_verified = bool(z0_ok)
    return {"checked": True, "cell": f"{instrument}-{cell['domain']}",
            "m0_m": m0.m, "exp060b_m0_m": src_m0.get("m"), "m0_median": m0.median,
            "exp060b_m0_median": src_m0.get("median"), "z0_m": z0.m,
            "exp060b_z0_m": src_z0.get("m"), "z0_median": z0.median,
            "exp060b_z0_median": src_z0.get("median"), "m0_match": bool(m0_ok),
            "z0_match": bool(z0_ok), "consistent": bool(m0_ok and z0_ok),
            "h0_qual_m": h0.m, "h0_median": h0.median,
            "exp053_conditioned": src.get("n_conditioned"),
            "h0_cond_verified_via_z0": h0_cond_verified, "h0_has_outcome_anchor": False}


def _float_match(a: float | None, b: float | None) -> bool:
    """Two optional floats agree to RECON_TOL (both None counts as a match)."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return abs(float(a) - float(b)) <= RECON_TOL


# --------------------------------------------------------------------------- #
# Plotting (bounded; from collected per-cell summaries -- no reloads)
# --------------------------------------------------------------------------- #
def _placeholder(ax: plt.Axes, message: str) -> None:
    ax.text(0.5, 0.5, message, ha="center", va="center")
    ax.axis("off")


def _forest_facet(ax: plt.Axes, rows: list[dict[str, Any]], obj: str) -> None:
    """One object's signal-null contrast forest on a shared axis."""
    if not rows:
        _placeholder(ax, f"no powered {obj} cells")
        return
    x = np.arange(len(rows))
    y = np.array([r["contrast_median_low_1s"] for r in rows])
    colours = ["#1a9850" if r["beats_null"] else "#d73027" for r in rows]
    ax.scatter(x, y, c=colours, s=18, zorder=3)
    ax.axhline(0.0, color="k", lw=0.8, ls="--")
    ax.set_xticks(x, [f"{r['instrument']}-{r['domain']}" for r in rows], rotation=90, fontsize=4)
    ax.set_title(f"{obj} (green = beats own null)")


def plot_signal_null_forest(efficacy: list[dict[str, Any]], save_path: Path) -> None:
    """Headline (binding): per-object per-cell signal-null contrast median CI_low forest."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 7), sharey=True)
    for ax, obj in zip(axes, ("hybrid", "native")):
        rows = sorted([r for r in efficacy if r.get("object") == obj
                       and r.get("contrast_median_low_1s") is not None
                       and np.isfinite(r.get("contrast_median_low_1s", np.nan))],
                      key=lambda r: r["contrast_median_low_1s"])
        _forest_facet(ax, rows, obj)
    axes[0].set_ylabel("signal - null median CI_low(1s) (ATR units)")
    fig.suptitle(f"{EXPERIMENT_ID}: does each object's benchmark harami beat its own "
                 "matched random on MA? (objects judged individually)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_viability_map(efficacy: list[dict[str, Any]], save_path: Path) -> None:
    """Per-object per-cell benchmark status across the grid (flag heatmap; non-4h marked)."""
    flags = ["median_viable", "beats_null", "generalises", "mean_viable"]
    fig, axes = plt.subplots(2, 1, figsize=(14, 7))
    for ax, obj in zip(axes, ("hybrid", "native")):
        cells = sorted([r for r in efficacy if r.get("object") == obj
                        and r.get("viable_status") != "EXCLUDED"],
                       key=lambda r: (r["instrument"], r["domain"]))
        if not cells:
            _placeholder(ax, f"no {obj} member cells")
            continue
        matrix = np.array([[1.0 if r.get(f) else 0.0 for r in cells] for f in flags])
        ax.imshow(matrix, cmap="Greens", vmin=0.0, vmax=1.0, aspect="auto")
        ax.set_yticks(range(len(flags)), flags, fontsize=8)
        labels = [f"{'*' if r['domain'] != '4h' else ''}{r['instrument']}-{r['domain']}"
                  for r in cells]
        ax.set_xticks(range(len(cells)), labels, rotation=90, fontsize=3)
        ax.set_title(f"{obj} (* = non-4h; generalises = median-viable AND beats own null)")
    fig.suptitle(f"{EXPERIMENT_ID}: per-object benchmark viability map")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_substrate_contrast(contrast: list[dict[str, Any]], save_path: Path) -> None:
    """Substrate contrast: H0-RH0, M0-RM0, Z0-RZ0 median CI_low by domain."""
    domains = list(DOMAINS)
    fig, ax = plt.subplots(figsize=(11, 6))
    has_data = False
    for label, key, colour in (("H0 - RH0 (MA hybrid)", "h0_rh0_median_low_1s", "#762a83"),
                               ("M0 - RM0 (MA native)", "m0_rm0_median_low_1s", "#1a9850"),
                               ("Z0 - RZ0 (ZigZag)", "z0_rz0_median_low_1s", "#4575b4")):
        xs, ys = [], []
        for i, dom in enumerate(domains):
            vals = [r[key] for r in contrast if r.get("domain") == dom
                    and r.get(key) is not None and np.isfinite(r.get(key, np.nan))]
            if vals:
                xs.append(i)
                ys.append(float(np.median(vals)))
                has_data = True
        if xs:
            ax.plot(xs, ys, marker="o", label=label, color=colour)
    if not has_data:
        _placeholder(ax, "no powered cells")
    else:
        ax.axhline(0.0, color="k", lw=0.8, ls="--")
        ax.set_xticks(range(len(domains)), domains)
        ax.set_xlabel("domain")
        ax.set_ylabel("pooled per-cell contrast median CI_low(1s) (ATR units)")
        ax.legend(fontsize=9)
    ax.set_title(f"{EXPERIMENT_ID}: substrate contrast by domain "
                 "(benchmark signal on the MA objects but not ZigZag?)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _skew_facet(ax: plt.Axes, rows: list[dict[str, Any]], obj: str) -> None:
    """One object's median/mean/trimmed-mean skew preview on a shared axis."""
    if not rows:
        _placeholder(ax, f"no powered {obj} cells")
        return
    x = np.arange(len(rows))
    ax.scatter(x, [r["sig_median"] for r in rows], c="#1a9850", s=16, label="median (binding)",
               zorder=3)
    ax.scatter(x, [r.get("sig_mean") if r.get("sig_mean") is not None else np.nan
                   for r in rows], c="#d73027", s=16, marker="s", label="raw mean", zorder=2)
    ax.scatter(x, [r.get("sig_trimmed_mean") if r.get("sig_trimmed_mean") is not None
                   else np.nan for r in rows], facecolors="none", edgecolors="#4575b4",
               s=16, label="10% trimmed mean", zorder=2)
    ax.axhline(0.0, color="k", lw=0.8, ls="--")
    ax.set_xticks(x, [f"{r['instrument']}-{r['domain']}" for r in rows], rotation=90, fontsize=4)
    ax.set_title(obj)
    ax.legend(fontsize=8)


def plot_median_vs_mean(efficacy: list[dict[str, Any]], save_path: Path) -> None:
    """P4 skew preview: per-object per-cell median vs raw mean vs 10% trimmed mean (H0 and M0)."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=True)
    for ax, obj in zip(axes, ("hybrid", "native")):
        rows = sorted([r for r in efficacy if r.get("object") == obj
                       and r.get("sig_median") is not None],
                      key=lambda r: r["sig_median"])
        _skew_facet(ax, rows, obj)
    axes[0].set_ylabel("per-cell signal expectancy (ATR units)")
    fig.suptitle(f"{EXPERIMENT_ID} P4: median vs mean vs trimmed mean per object "
                 "(is any negative mean removable-tail-driven?)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_p11_composition(readout: dict[str, Any], save_path: Path) -> None:
    """Per-object P11 composition tallies (median_viable, beats_null, generalises)."""
    flags = ("median_viable", "beats_null", "generalises")
    objs = ("hybrid", "native")
    width = 0.38
    x = np.arange(len(flags))
    fig, ax = plt.subplots(figsize=(10, 6))
    for i, obj in enumerate(objs):
        vals = [readout[obj][f]["n_cells"] for f in flags]
        ax.bar(x + (i - 0.5) * width, vals, width, label=obj)
    ax.axhline(P11_MIN_CELLS, color="k", lw=0.8, ls="--",
               label=f"P11 min cells ({P11_MIN_CELLS})")
    ax.set_xticks(x, flags)
    ax.set_ylabel("n cells composing")
    ax.legend(fontsize=9)
    ax.set_title(f"{EXPERIMENT_ID}: per-object P11 composition "
                 "(>=5 cells / >=3 instruments / >=3 non-4h)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def make_plots(
    efficacy: list[dict[str, Any]], contrast: list[dict[str, Any]], readout: dict[str, Any],
) -> None:
    """Render the five bounded plots from collected per-cell summaries (no reloads)."""
    plot_signal_null_forest(efficacy, PLOTS_DIR / "signal_null_forest.png")
    plot_viability_map(efficacy, PLOTS_DIR / "hybrid_native_viability_map.png")
    plot_substrate_contrast(contrast, PLOTS_DIR / "substrate_contrast_by_domain.png")
    plot_median_vs_mean(efficacy, PLOTS_DIR / "median_vs_mean_by_object.png")
    plot_p11_composition(readout, PLOTS_DIR / "p11_composition_by_object.png")


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _cell_index_map() -> dict[tuple[str, str], int]:
    """Stable (instrument, domain) -> int index (identical to EXP-060/060B)."""
    return {(inst, dom): i for i, (inst, dom) in enumerate(
        (inst, dom) for inst in INSTRUMENTS for dom in DOMAINS)}


def process_instrument(
    instrument: str, anchor: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    """Worker: resolve every member cell of one instrument (the parallel unit).

    Self-contained and pure given identical inputs/seeds: each cell's RNG is seeded
    by ``(BASE_SEED, cell_index, purpose)`` (order-independent), so the
    per-instrument result is identical regardless of worker count or finish order.
    The parent merges these in ``INSTRUMENTS`` order for byte-identical output.
    """
    cell_index = _cell_index_map()
    out: dict[str, Any] = {
        "objects": [], "efficacy": [], "contrast": [], "readiness": [], "recon_rows": [],
        "meta": None, "causality_violations": [], "invariant_violations": [],
        "determinism_checked": [], "non_deterministic": []}
    members = [d for d in DOMAINS if (instrument, d) not in EXCLUDED_CELLS]
    if not members:
        for domain in DOMAINS:
            _append_excluded(out, instrument, domain)
        return out
    train_1m, meta = load_train_1m(instrument)
    out["meta"] = meta
    replayed = False
    for domain in DOMAINS:
        if (instrument, domain) in EXCLUDED_CELLS:
            _append_excluded(out, instrument, domain)
            continue
        ci = cell_index[(instrument, domain)]
        cell = compute_cell(train_1m, domain, meta["train_end_epoch_s"], ci)
        if cell.get("empty"):
            _append_excluded(out, instrument, domain)        # no signal -> placeholder
            out["recon_rows"].append(exp060b_reconciliation(instrument, cell, anchor))
            continue
        out["objects"].extend(object_rows(instrument, cell))
        out["efficacy"].extend(object_efficacy_rows(instrument, cell))
        out["contrast"].append(substrate_contrast_row(instrument, cell))
        out["readiness"].append(readiness_row(instrument, cell))
        out["recon_rows"].append(exp060b_reconciliation(instrument, cell, anchor))
        _record_cell_defects(cell, instrument, domain, out)
        if not replayed and cell["arms"]["m0"].m > 0:
            ok = determinism_replay(train_1m, domain, meta["train_end_epoch_s"], ci)
            out["determinism_checked"].append(f"{instrument}-{domain}#{ci}")
            if not ok:
                out["non_deterministic"].append(f"{instrument}-{domain}#{ci}")
            replayed = True
        del cell
    del train_1m
    return out


def _append_excluded(out: dict[str, Any], instrument: str, domain: str) -> None:
    """Append the placeholder rows for an excluded/empty cell."""
    obj_rows, efficacy, contrast, ready = excluded_rows(instrument, domain)
    out["objects"].extend(obj_rows)
    out["efficacy"].extend(efficacy)
    out["contrast"].append(contrast)
    out["readiness"].append(ready)


def _record_cell_defects(cell: dict[str, Any], instrument: str, domain: str,
                         out: dict[str, Any]) -> None:
    """Accumulate per-cell causality / invariant violations."""
    label = f"{instrument}-{domain}"
    if not cell.get("causality_ok", True):
        out["causality_violations"].append(label)
    inv = cell.get("invariants", {})
    if not all(inv.get(k, True) for k in
               ("weights_sum_ok", "bench_exit_ok", "matched_count_ok")):
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
    anchor = load_exp060b_bench()
    workers = max(1, min(workers, len(INSTRUMENTS)))
    grid = _run_grid(anchor, workers)
    objects: list[dict[str, Any]] = []
    efficacy: list[dict[str, Any]] = []
    contrast: list[dict[str, Any]] = []
    readiness: list[dict[str, Any]] = []
    recon_rows: list[dict[str, Any]] = []
    instrument_meta: dict[str, Any] = {}
    defect = {"is_defect": False, "non_deterministic": [], "exp060b_mismatch": [],
              "causality_violations": [], "determinism_checked": [],
              "invariant_violations": [], "exp060b_available": bool(anchor),
              "exp060b_checked_cells": 0, "workers": workers}
    for instrument, res in zip(INSTRUMENTS, grid):     # fixed INSTRUMENTS order
        objects.extend(res["objects"])
        efficacy.extend(res["efficacy"])
        contrast.extend(res["contrast"])
        readiness.extend(res["readiness"])
        recon_rows.extend(res["recon_rows"])
        if res["meta"] is not None:
            instrument_meta[instrument] = res["meta"]
        for key in ("causality_violations", "invariant_violations",
                    "determinism_checked", "non_deterministic"):
            defect[key].extend(res[key])

    _finalize_defects(defect, recon_rows)
    readout = generalisation_readout(efficacy, contrast, defect)
    write_outputs(objects, efficacy, contrast, readiness, recon_rows, readout,
                  instrument_meta, defect)
    make_plots(efficacy, contrast, readout)
    return _summarize(efficacy, readout)


def _finalize_defects(defect: dict[str, Any], recon_rows: list[dict[str, Any]]) -> None:
    """Aggregate defect gates into the binding is_defect flag."""
    defect["exp060b_mismatch"] = [r["cell"] for r in recon_rows
                                  if r.get("checked") and not r["consistent"]]
    if defect["exp060b_mismatch"]:
        defect["is_defect"] = True
    defect["exp060b_checked_cells"] = sum(1 for r in recon_rows if r.get("checked"))
    if not defect["exp060b_available"] or defect["exp060b_checked_cells"] == 0:
        defect["is_defect"] = True                     # P12: missing anchor is a defect
    causal_instr = {c.split("-")[0] for c in defect["causality_violations"]}
    if len(causal_instr) >= P11_MIN_INSTR:
        defect["is_defect"] = True
    if defect["invariant_violations"]:                 # exact structural checks
        defect["is_defect"] = True
    if defect["non_deterministic"]:                    # byte-identical replay failed
        defect["is_defect"] = True


def write_outputs(
    objects: list[dict[str, Any]], efficacy: list[dict[str, Any]],
    contrast: list[dict[str, Any]], readiness: list[dict[str, Any]],
    recon_rows: list[dict[str, Any]], readout: dict[str, Any],
    instrument_meta: dict[str, Any], defect: dict[str, Any],
) -> None:
    """Persist the per-cell parquet, the per-object efficacy / contrast / readiness maps, JSON."""
    pl.DataFrame(objects, strict=False).write_parquet(
        RESULTS_DIR / "per_cell_expectancy.parquet")
    pl.DataFrame(efficacy, strict=False).write_csv(RESULTS_DIR / "object_efficacy_map.csv")
    pl.DataFrame(contrast, strict=False).write_csv(RESULTS_DIR / "substrate_contrast.csv")
    pl.DataFrame(readiness, strict=False).write_csv(RESULTS_DIR / "readiness.csv")
    recon_clean = [r for r in recon_rows if r.get("checked")]
    (pl.DataFrame(recon_clean, strict=False) if recon_clean
     else pl.DataFrame({"cell": []})).write_csv(RESULTS_DIR / "reconciliation.csv")
    with open(RESULTS_DIR / "generalisation_readout.json", "w") as fh:
        json.dump(readout, fh, indent=2, default=str)
    _write_metadata(instrument_meta, defect, recon_clean, readout)


def _write_metadata(
    instrument_meta: dict[str, Any], defect: dict[str, Any],
    recon_clean: list[dict[str, Any]], readout: dict[str, Any],
) -> None:
    meta = {
        "experiment_id": EXPERIMENT_ID,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "015", "lead": "L1", "hypothesis": "HYP-014", "family": "CF-HA-HARAMI-001",
        "checkpoint": "2026-06-17-015-ma-substrate-conditioned-harami-full-surface",
        "conditioning_mode": ("dual object, reported individually (D0 Amendment 001): hybrid "
                              "(ZigZag-/STRONG-STAT mask x MA geometry, NEW) and native "
                              "(MA-segment-/STRONG-STAT x MA geometry); never pooled"),
        "stratum": "TRAIN-only (first 49%); nested TEST + final-30% holdout sealed",
        "population": ("hybrid = byte-identical to EXP-053 ZigZag-/STRONG-STAT conditioned set; "
                       "native = byte-identical to EXP-060B M-arms (MA-segment /STRONG-STAT)"),
        "entry_anchor": "harami confirmation-bar real close (every signal arm, both objects)",
        "binding_endpoint": ("median per-event position-weighted gross ATR-normalised return "
                             "(P3/P14, P15 fills); mean + 10% trimmed mean + worst-5% tail-share "
                             "= P4 diagnostic (disclosed, never a gate)"),
        "binding_discriminator": ("per object, individually: H0 (BENCH-MA-hybrid) must beat RH0, "
                                  "and M0 (BENCH-MA-native) must beat RM0 -- each median-viable "
                                  "AND own-object matched-random independent-contrast median "
                                  "CI_low>0 AND clear P11 with the P6 non-4h rule for that "
                                  "object's EVIDENCE_FOR. Objects never pooled; phase verdict = "
                                  "stronger object."),
        "objects": ["H0 (BENCH-MA-hybrid, binding, NEW)", "RH0 (BENCH-MA-hybrid-random, null, NEW)",
                    "M0 (BENCH-MA-native, binding; reconciles EXP-060B M0 1e-9)",
                    "RM0 (BENCH-MA-native-random, null)",
                    "Z0 (BENCH-ZZ, disclosed contrast)", "RZ0 (BENCH-ZZ-random, disclosed)"],
        "geometry": ("benchmark single-leg: favourable = 0.50*M_sofar, adverse 1:1, MA-defined "
                     "adaptive cap (k=1.5, window=20, floor=6, median, min_moves=5); no V2A / "
                     "ADV-NONE / favourable-alt / third-alt / exit / horizon arm"),
        "params": {
            "atr_period": ATR_PERIOD, "atr_mult": ATR_MULT,
            "favourable_fraction_bench": 0.50, "adverse_bench": "1:1",
            "ma_segmentation": [MA_FAST, MA_SLOW], "stat_window": 20, "stat_min_window": 5,
            "stat_q": 0.75, "timecap_floor_bench": 6, "timecap_k": 1.5, "timecap_window": 20,
            "timecap_min_moves": 5, "power_floor": POWER_FLOOR, "trim_frac": TRIM_FRAC,
            "tail_frac": TAIL_FRAC, "n_boot": N_BOOT, "boot_batch": BOOT_BATCH,
            "base_seed": BASE_SEED, "p11": [P11_MIN_CELLS, P11_MIN_INSTR],
            "p6_min_non_4h": P6_MIN_NON_4H,
        },
        "statistical_methods": [
            "per-cell median CI (bootstrap_median_distribution + median_ci) -- binding, per arm",
            "per-cell mean + 10% trimmed mean CI (bootstrap_stat_distribution, same block "
            "ctor) + worst-5% tail-share -- P4 diagnostic (disclosed), per arm",
            "independent bootstrap contrast per object: H0-RH0 (hybrid) and M0-RM0 (native), "
            "median binding + mean disclosed (contrast_ci on the bootstrap distributions; "
            "objects judged individually, never pooled); Z0-RZ0 -- disclosed substrate contrast",
        ],
        "verdict": readout["verdict"],
        "hybrid_verdict": readout["hybrid"]["verdict"],
        "native_verdict": readout["native"]["verdict"],
        "hybrid_generalises_composes": readout["hybrid"]["generalises"]["composes"],
        "hybrid_median_viable_composes": readout["hybrid"]["median_viable"]["composes"],
        "hybrid_beats_null_composes": readout["hybrid"]["beats_null"]["composes"],
        "native_generalises_composes": readout["native"]["generalises"]["composes"],
        "native_median_viable_composes": readout["native"]["median_viable"]["composes"],
        "native_beats_null_composes": readout["native"]["beats_null"]["composes"],
        "z0_beats_rz0_composes": readout["z0_beats_rz0_disclosed"]["composes"],
        "parallelism": {
            "workers": defect.get("workers", 1),
            "model": ("per-instrument ProcessPoolExecutor; results reassembled in fixed "
                      "INSTRUMENTS order; per-process native threads pinned to 1 to avoid "
                      "CPU oversubscription. Output is byte-identical across worker counts: "
                      "every RNG is seeded by (BASE_SEED, cell_index, purpose) so draws are "
                      "order-independent, OHLC aggregation is order-independent, and the merge "
                      "order is fixed. The first usable cell per instrument is replayed "
                      "byte-identically inside its worker (determinism gate)."),
        },
        "determinism_ok": not defect["non_deterministic"],
        "determinism_checked": defect["determinism_checked"],
        "determinism_gate": ("byte-identical re-run of the first usable cell per instrument "
                             "across M0/Z0/RM0/RZ0 returns/median/CIs and the M0-RM0 "
                             "independent contrast (median + mean)."),
        "causality_ok": not defect["causality_violations"],
        "causality_violations": defect["causality_violations"],
        "invariant_violations": defect["invariant_violations"],
        "invariant_gates": ("BENCH leg weight sums to 1.0; each of the 6 arms' exit-reason "
                            "weights sum to 1.0 (finite real-bar P15 resolution, 1:1 stop "
                            "well-formed); matched-count holds per object (RH0.draw_count==H0.m, "
                            "RM0.draw_count==M0.m, RZ0.draw_count==Z0.m). Reconciliation "
                            "(SUBSTRATE/METHOD_DEFECT, corrected P12 roles): native M0 reproduces "
                            "EXP-060B BENCH-MA (M0) and Z0 reproduces EXP-060B BENCH-ZZ (Z0) "
                            "per-cell m + median to 1e-9; hybrid H0 has NO outcome anchor (its "
                            "ZigZag /STRONG-STAT conditioning mask is verified transitively via "
                            "Z0, which reconciles to EXP-053/060B n_conditioned); a missing "
                            "anchor is a defect."),
        "exp060b_reconciliation": recon_clean,
        "exp060b_mismatch": defect["exp060b_mismatch"],
        "exp060b_available": defect["exp060b_available"],
        "exp060b_checked_cells": defect["exp060b_checked_cells"],
        "exp060b_anchor": str(EXP060B_PARQUET),
        "reproduction_safety": ("native/Z median + mean RNG purposes (PB_STAT/PB_MASEG, "
                                "PB_STAT_MEAN/PB_MASEG_MEAN) are byte-identical to EXP-060B so "
                                "M0/Z0 reproduce exactly; the trimmed-mean bootstrap, RM0, RZ0, "
                                "and the NEW hybrid arms (H0: PB_HSEG*; RH0: PB_RH0_*) use "
                                "disjoint dedicated RNG purposes so no existing stream shifts; "
                                "the per-object contrasts are deterministic contrast_ci on stored "
                                "distributions (no RNG)."),
        "is_defect": defect["is_defect"],
        "de30_disclosure": DE30_DISCLOSURE,
        "fill_approximation": ("P15 path is a documented approximation of unobserved intrabar "
                               "motion; 1-minute base bars are not replayed (EXP-054 bounds it)."),
        "holdout_fence": ("Only Parquet metadata + first train_rows file-order rows read per "
                          "instrument; full file never sorted/collected; every domain bar fenced "
                          "to CloseTime <= train_end_ts; forward scans clipped to the data edge -> "
                          "DATA_CENSORED; TEST and final-30% holdout never read."),
        "registry": ("CF-HA-HARAMI-001/HYP-014 (EXP-061); composes the registered MA-SUBSTRATE "
                     "(BOTH modes hybrid + native, parallel first-class per D0 Amendment 001), "
                     "the benchmark 3-barrier geometry, and the matched-random baseline (a null). "
                     "0 candidate slots, 0 TEST reads; per-object characterisation readout feeds "
                     "the single terminal G-015 (no closure or registration here)."),
        "instrument_meta": instrument_meta,
    }
    with open(RESULTS_DIR / "run_metadata.json", "w") as fh:
        json.dump(meta, fh, indent=2, default=str)


def _summarize(efficacy: list[dict[str, Any]], readout: dict[str, Any]) -> dict[str, Any]:
    """Concise stdout summary (per object)."""
    status_counts: dict[str, dict[str, int]] = {"hybrid": {}, "native": {}}
    for r in efficacy:
        obj = r.get("object")
        if obj in status_counts:
            s = r.get("viable_status", "EXCLUDED")
            status_counts[obj][s] = status_counts[obj].get(s, 0) + 1
    return {"verdict": readout["verdict"], "hybrid": readout["hybrid"],
            "native": readout["native"], "z0_beats_rz0": readout["z0_beats_rz0_disclosed"],
            "status_counts": status_counts, "defect": readout["defect"]}


def _parse_args() -> argparse.Namespace:
    """CLI: --workers controls per-instrument parallelism (default = all CPUs)."""
    parser = argparse.ArgumentParser(description=f"{EXPERIMENT_ID} MA-benchmark generalisation")
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
    LOGGER.info("\n=== %s complete (dual-object: hybrid + native, reported individually) ===",
                EXPERIMENT_ID)
    LOGGER.info("phase verdict (stronger object): %s", summary["verdict"])
    for obj in ("hybrid", "native"):
        o = summary[obj]
        LOGGER.info("[%s] verdict=%s | median-viable %s cells (P11+P6=%s); beats-null %s cells; "
                    "generalises %s cells / %s instr (non-4h %s; P11+P6=%s)", obj, o["verdict"],
                    o["median_viable"]["n_cells"], o["median_viable"]["composes"],
                    o["beats_null"]["n_cells"], o["generalises"]["n_cells"],
                    o["generalises"]["n_instruments"], o["generalises"]["n_non_4h"],
                    o["generalises"]["composes"])
    LOGGER.info("disclosed: Z0 beats RZ0 %s cells", summary["z0_beats_rz0"]["n_cells"])
    LOGGER.info("per-object status counts: %s", json.dumps(summary["status_counts"]))
    if summary["defect"]["is_defect"]:
        LOGGER.info("DEFECT: %s", json.dumps(summary["defect"], default=str))
    LOGGER.info("artifacts -> %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
