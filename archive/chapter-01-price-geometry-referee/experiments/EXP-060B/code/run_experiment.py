"""EXP-060B — MA(20,50) Substrate Dominance: Genuine Lead or Skew Artifact?

``CF-HA-HARAMI-001`` / HYP-013b (Phase 014-B diagnostic addendum to EXP-060;
``014-B-EXP-060B-ma-substrate-dominance-addendum.md``). TRAIN-only, gross;
**0 candidate slots, 0 TEST reads**; population byte-identical to EXP-053/060.

EXP-060 returned ``CHARACTERISED_NOT_VIABLE_ELIGIBLE`` and recorded the result as
*"MA-baseline dominance is a substrate property."* EXP-060B tests whether that
reading is correct or whether the MA(20,50) **median** dominance is the same
capped-upside (V2A) / uncapped-downside (/ADV-NONE) left-skew artifact the ZigZag
champion exhibits. It re-instruments EXP-060's per-cell pipeline with three
minimal changes (the median path is held byte-identical):

1. **Emit the MA mean + MA exit-reason composition** EXP-060 computed but dropped.
2. **Add RM3** — the one new computation: a matched-random control on the **MA**
   substrate (``ma_matched_random_arm``), mirroring EXP-060's ZigZag
   ``matched_random_arm`` but with MA segmentation.
3. **Bootstrap the mean** alongside the median for every arm (dedicated RNG
   streams so the median path is untouched), and compute the binding ``M3 - RM3``
   and disclosed ``Z3 - RZ3`` contrasts (independent bootstrap; median + mean).

The 10 predeclared objects: 8 signal arms — ZigZag {Z0 BENCH, Z1 50PCT-NONE,
Z2 V2A-1TO1, Z3 V2A-NONE} and MA(20,50) {M0,M1,M2,M3} — plus two matched-random
nulls RZ3 (ZigZag) and RM3 (MA). Binding endpoint unchanged: per-event
**median** position-weighted gross ATR-normalised return (P14, P15 fills). The
**mean** is the P14-sanctioned disclosed secondary and the characterisation lens.

Binding discriminator (D2): does the MA harami (M3) clear P11 median viability
**and** beat RM3 (independent-contrast median CI_low>0) **and** clear P11 on the mean
(SUBSTRATE_LEAD_FOUND), or is MA dominance the same median>>mean / entry-redundant
artifact (ARTIFACT_CONFIRMED)? Reproduction invariants vs EXP-060 (Z3<->A3 median/
count/exit-composition; M3<->maseg_median) are SUBSTRATE/METHOD_DEFECT guards.

Real prices throughout; HA prices enter only the harami/impulse detectors and
never any metric. Outputs under results/ and plots/; created in orchestration.
No floor=48 horizon arm, no factorial decomposition — substrate-vs-skew only.
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
# sum — order-independent; the bootstrap is numpy resampling, not BLAS).
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
EXP060_MAP = EXPERIMENTS_ROOT / "EXP-060" / "results" / "combined_system_map.csv"

from xen.adverse_targets import adverse_none_sentinel  # noqa: E402
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
from xen.position_exits import (  # noqa: E402
    ADV_FIXED,
    LEG_LEVEL,
    PX_ADV,
    PX_CLASS_LABELS,
    PX_FAV,
    PX_TIMECAP,
    exit_reason_weights,
    leg_levels_from_fracs,
    resolve_legs,
    weighted_returns,
)
from xen.strong_move import annotate_ha_impulse, find_impulse_runs  # noqa: E402
from xen.zigzag import generate_zigzag, wilder_atr  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (Phase 014-B D0 frozen + EXP-060 inherited; no tuning)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-060B"
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
MA_FAST, MA_SLOW = 20, 50          # P13 MA-segmentation baseline
POWER_FLOOR = 30                   # P14: minimum qualifying events to report
P11_MIN_CELLS, P11_MIN_INSTR = 5, 3
RECON_TOL = 1e-9                   # EXP-060 reproduction tolerance
N_BOOT = 10_000                    # P14 bootstrap resamples
BOOT_BATCH = 2_000                 # bounded bootstrap memory batch
BASE_SEED = 20260616               # frozen master seed (identical to EXP-060)
EXCLUDED_FILE_MARKERS = ("analysis70", "analysis_slice", "first70")
DE30_DISCLOSURE = (
    "DE30 truncated history: broker m1 history ends 2026-01-16; counts derive "
    "from its own realized timeline and are not span-comparable (VAL-003).")
LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# Arm specification (4 geometries; no floor=48 horizon arm — EXP-060 §A4 dropped)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ArmSpec:
    """One predeclared capture geometry (recomposition of frozen resolvers)."""

    aid: str
    idx: int                           # stable RNG / column offset (EXP-060 parity)
    leg_fracs: tuple[float, ...]       # favourable distance fraction per leg
    weights: tuple[float, ...]         # leg weights (sum 1.0)
    adv_none: bool                     # True = /ADV-NONE sentinel; False = 1:1 stop
    is_bench: bool                     # BENCH: exact EXP-053 resolve_path_ordered path
    binding: bool                      # V2A-NONE (the champion geometry = M3/Z3)


_V2A = (1.0 / 3.0, 2.0 / 3.0, 1.0)
_W3 = (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)
# idx values held identical to EXP-060 so PB_*+idx RNG streams reproduce exactly.
ARMS: list[ArmSpec] = [
    ArmSpec("BENCH", 0, (1.0,), (1.0,), False, True, False),       # Z0 / M0
    ArmSpec("50PCT-NONE", 1, (1.0,), (1.0,), True, False, False),  # Z1 / M1
    ArmSpec("V2A-1TO1", 2, _V2A, _W3, False, False, False),        # Z2 / M2
    ArmSpec("V2A-NONE", 3, _V2A, _W3, True, False, True),          # Z3 / M3 (champion)
]
ARM_BY_ID: dict[str, ArmSpec] = {a.aid: a for a in ARMS}
CHAMPION_ID = "V2A-NONE"            # the object under study (M3 vs RM3)

# RNG purpose bases (distinct deterministic streams per cell/arm/purpose).
# Median-path purposes are byte-identical to EXP-060 (reproduction invariants).
PB_STAT, PB_HA = 1000, 2000                          # ZigZag signal-arm medians
PB_RAND_DRAW, PB_RAND_BOOT, PB_MASEG = 7000, 8000, 9000  # RZ3 draw/boot, MA-seg arms
# New dedicated streams (never perturb the median path; reproduction-safe).
PB_STAT_MEAN, PB_HA_MEAN, PB_MASEG_MEAN = 21000, 22000, 23000     # per-arm mean boot
PB_RAND_BOOT_MEAN = 24000                                          # RZ3 mean boot
PB_MASEG_HA, PB_MASEG_HA_MEAN = 25000, 26000                       # M3 /STRONG-HA rerun
PB_RM3_DRAW, PB_RM3_BOOT, PB_RM3_BOOT_MEAN = 31000, 32000, 33000   # RM3 (NEW control)
# D2 contrasts (M3-RM3 binding, Z3-RZ3 disclosed) use the independent contrast_ci on
# the stored median/mean bootstrap distributions — no RNG (deterministic given dists).

# Per-cell MA-substrate viability status -> integer code (binding readout).
VSTATUS_CODES: dict[str, int] = {
    "LEAD_CELL": 0, "MEDIAN_VIABLE_NOT_LEAD": 1, "NOT_MEDIAN_VIABLE": 2,
    "NOT_POWERED": 3, "EXCLUDED": 4,
}


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ArmResult:
    """One arm's per-cell resolved population summary + qualifying returns.

    Carries the median (binding) and mean (disclosed) point estimates and CIs,
    plus the per-event arrays (qualifying returns in entry order + the
    full-length mask) and the median/mean bootstrap distributions used by the
    independent signal-vs-null contrasts.
    """

    m: int
    median: float | None
    mean: float | None
    ci_low_1s: float | None
    ci_lo_2s: float | None
    ci_hi_2s: float | None
    mean_ci_low_1s: float | None
    mean_ci_lo_2s: float | None
    mean_ci_hi_2s: float | None
    r_firsthit: float | None       # single-leg arms only (FAV/(FAV+TIMECAP)); else None
    win_rate: float | None
    data_censored: int
    exit_weights: dict[str, float]
    population: int                # built-barrier population (pre-resolution)
    block_len: int
    r_e: np.ndarray                # qualifying weighted returns in entry order
    r_e_all: np.ndarray            # full-length weighted returns (NaN off-qual)
    qual: np.ndarray               # full-length qualifying mask (off-population NaN)
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


def load_exp060_map() -> dict[tuple[str, str], dict[str, Any]]:
    """Load EXP-060's per-cell per-arm rows for the reproduction reconciliation.

    Returns, per (instrument, domain), the EXP-060 signal-arm m/median per arm
    (== Z0-Z3), the MA-seg m/median per arm (== M0-M3), and the champion (A3)
    exit-weights (== Z3) — the SUBSTRATE/METHOD_DEFECT reproduction guard for
    scope invariants (i) Z3, (ii) M3, (iii) all signal arms.
    """
    if not EXP060_MAP.exists():
        return {}
    df = pl.read_csv(EXP060_MAP, infer_schema_length=10_000)
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for row in df.iter_rows(named=True):
        if not row.get("member") or row.get("arm") not in ARM_BY_ID:
            continue
        cell = out.setdefault((row["instrument"], row["domain"]), {"arms": {}})
        cell["arms"][row["arm"]] = {
            "z_m": row.get("m"), "z_median": row.get("median"),
            "m_m": row.get("maseg_m"), "m_median": row.get("maseg_median")}
        if row.get("arm") == CHAMPION_ID:
            cell["ew"] = {lab: row.get(f"ew_{lab}") for lab in PX_CLASS_LABELS.values()}
    return out


# --------------------------------------------------------------------------- #
# Pure computation — domain / substrate / harami alignment
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

    Identical to EXP-060's ``ma_segment_moves``: segments bounded by consecutive
    crossovers on the **real close**; the partial pre-first-crossover stretch is
    excluded by construction. MA(20,50) is the EXP-050/053 baseline trend
    substrate (already registered), not a new detector.
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


def strong_ha_retention(
    ha_ann: pl.DataFrame, entry_epoch: np.ndarray, start_epoch: np.ndarray,
    in_trend: np.ndarray, valid: np.ndarray,
) -> np.ndarray:
    """Per-harami ``/STRONG-HA`` same-direction retention (disclosed arm)."""
    n = int(entry_epoch.shape[0])
    same = np.zeros(n, dtype=bool)
    runs = find_impulse_runs(ha_ann)
    if runs.height == 0:
        return same
    rf = runs.get_column("run_first_time").dt.epoch("s").to_numpy().astype(np.int64)
    rl = runs.get_column("run_last_time").dt.epoch("s").to_numpy().astype(np.int64)
    rdir = runs.get_column("run_dir").to_numpy().astype(np.int64)
    for e in range(n):
        if not valid[e]:
            continue
        ub = int(np.searchsorted(rl, entry_epoch[e], side="right"))
        if ub == 0:
            continue
        in_span = rf[:ub] > start_epoch[e]
        if in_span.any():
            same[e] = bool((in_span & (rdir[:ub] == in_trend[e])).any())
    return same


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
# Pure computation — mean moving-block bootstrap (block ctor == median path)
# --------------------------------------------------------------------------- #
def bootstrap_mean_distribution(
    values: np.ndarray, rng: np.random.Generator,
    n_boot: int = N_BOOT, batch: int = BOOT_BATCH,
) -> tuple[np.ndarray, int]:
    """Moving-block bootstrap distribution of the **mean** of ``values``.

    Block construction is byte-identical to
    :func:`xen.expectancy.bootstrap_median_distribution` (``b = max(1,
    round(m**(1/3)))``; ``ceil(m/b)`` contiguous blocks per resample, truncated to
    ``m``); only the statistic changes (``np.mean``). The mean is tail-sensitive,
    so its CI is wider than the median's — this quantifies the capped-up /
    uncapped-down skew (the object under study), not a defect. New statistic on the
    established machinery, drawn from a dedicated RNG so the median path is
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
        out[done:done + k] = np.mean(values[idx], axis=1)
        done += k
    return out, b


# --------------------------------------------------------------------------- #
# Pure computation — resolve one arm on one population -> ArmResult
# --------------------------------------------------------------------------- #
def resolve_arm(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, entry_close: np.ndarray,
    rd: np.ndarray, atr_entry: np.ndarray, arm: ArmSpec, fav_dist: np.ndarray,
    fav: np.ndarray, adv: np.ndarray, n_event: np.ndarray, population: np.ndarray,
    last_train_idx: int, rng: np.random.Generator, mean_rng: np.random.Generator,
    draw_count: int = 0,
) -> ArmResult:
    """Resolve one arm over ``population`` events; bootstrap median + mean.

    BENCH (``is_bench``) reuses :func:`resolve_path_ordered` (the exact EXP-053
    path); the others reuse :func:`resolve_legs` with the benchmark 1:1 stop or the
    /ADV-NONE sentinel (``adv = -+inf``, never binds). ``n_event`` is the per-event
    benchmark adaptive cap (floor=6). No trailing, no reversal legs, no floor=48
    horizon arm. The median path (``rng``) is byte-identical to EXP-060; the mean
    CI uses a dedicated ``mean_rng``.
    """
    n_bars = ohlc["close"].shape[0]
    weights = np.asarray(arm.weights, dtype=np.float64)
    if arm.is_bench:                                   # exact EXP-053 reuse path
        classes, exit_px = resolve_path_ordered(
            ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"], entry_idx,
            fav, adv, rd, n_event, population, n_bars)
        r_all = realised_returns(classes, exit_px, entry_close, rd, atr_entry)
        qual = population & qualifying_mask(classes, exit_px, atr_entry)
        leg_cls = classes[:, None]
        r_firsthit = _firsthit(classes, qual, CLASS_FAV, CLASS_ADV)
        censored = int((population & (classes == CLASS_DATA_CENSORED)).sum())
    else:
        adv_level = (adverse_none_sentinel(entry_close, rd, fav_dist)["adv"]
                     if arm.adv_none else adv)
        levels = leg_levels_from_fracs(entry_close, rd, fav_dist, arm.leg_fracs)
        no_rev = np.full(int(entry_idx.shape[0]), -1, dtype=np.int64)
        leg_kinds = tuple(LEG_LEVEL for _ in arm.leg_fracs)
        leg_px, leg_cls = resolve_legs(
            ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"], entry_idx,
            entry_close, rd, leg_kinds, levels, no_rev, adv_level, n_event,
            population, ADV_FIXED, None, last_train_idx)
        r_all, qual = weighted_returns(leg_px, leg_cls, weights, entry_close, rd,
                                       atr_entry, population)
        r_firsthit = (_firsthit(leg_cls[:, 0], qual, PX_FAV, PX_TIMECAP)
                      if len(arm.leg_fracs) == 1 else None)
        censored = int((population & ~qual & np.isfinite(atr_entry) & (atr_entry > 0.0)).sum())
    order = np.argsort(entry_idx[qual], kind="stable")
    r_e = r_all[qual][order]
    exit_w = exit_reason_weights(leg_cls, weights, qual)
    return _summarize_arm(r_e, r_all, qual, exit_w, r_firsthit, censored,
                          int(population.sum()), rng, mean_rng, draw_count)


def _firsthit(
    classes: np.ndarray, qual: np.ndarray, fav_code: int, other_code: int,
) -> float | None:
    """First-hit ratio FAV/(FAV+other) over qualifying single-leg events (disclosed)."""
    fav_n = int((qual & (classes == fav_code)).sum())
    other_n = int((qual & (classes == other_code)).sum())
    resolved = fav_n + other_n
    return (fav_n / resolved) if resolved > 0 else None


def _summarize_arm(
    r_e: np.ndarray, r_all: np.ndarray, qual: np.ndarray, exit_w: dict[str, float],
    r_firsthit: float | None, censored: int, population: int,
    rng: np.random.Generator, mean_rng: np.random.Generator, draw_count: int = 0,
) -> ArmResult:
    """Assemble an ``ArmResult``; (if powered) bootstrap the median + mean CIs."""
    m = int(r_e.shape[0])
    dist = np.empty(0, dtype=np.float64)
    mean_dist = np.empty(0, dtype=np.float64)
    block_len = max(1, int(round(max(m, 1) ** (1.0 / 3.0))))
    median = mean = ci_low = ci_lo = ci_hi = None
    mean_low = mean_lo = mean_hi = None
    if m > 0:
        median = float(np.median(r_e))
        mean = float(np.mean(r_e))
    if m >= POWER_FLOOR:
        dist, block_len = bootstrap_median_distribution(r_e, rng, n_boot=N_BOOT, batch=BOOT_BATCH)
        ci_low, ci_lo, ci_hi = median_ci(dist)
        mean_dist, _ = bootstrap_mean_distribution(r_e, mean_rng, n_boot=N_BOOT, batch=BOOT_BATCH)
        mean_low, mean_lo, mean_hi = median_ci(mean_dist)   # generic percentile CI
    return ArmResult(
        m=m, median=median, mean=mean, ci_low_1s=ci_low, ci_lo_2s=ci_lo, ci_hi_2s=ci_hi,
        mean_ci_low_1s=mean_low, mean_ci_lo_2s=mean_lo, mean_ci_hi_2s=mean_hi,
        r_firsthit=r_firsthit, win_rate=(float((r_e > 0).mean()) if m > 0 else None),
        data_censored=censored, exit_weights=exit_w, population=population,
        block_len=block_len, r_e=r_e, r_e_all=r_all, qual=qual, dist=dist,
        mean_dist=mean_dist, draw_count=draw_count)


def _empty_arm() -> ArmResult:
    return ArmResult(0, None, None, None, None, None, None, None, None, None, None, 0,
                     {label: 0.0 for label in PX_CLASS_LABELS.values()}, 0, 1,
                     np.empty(0), np.empty(0), np.empty(0, dtype=bool), np.empty(0),
                     np.empty(0), 0)


# --------------------------------------------------------------------------- #
# Pure computation — signal vs matched-random contrast (D2: median binding)
# --------------------------------------------------------------------------- #
def champion_vs_null_contrast(variant: ArmResult, null: ArmResult) -> dict[str, Any]:
    """Independent bootstrap contrast ``variant - null`` (median binding, mean disclosed).

    The signal arm (M3/Z3, indexed over haramis) and its matched-random control
    (RM3/RZ3, indexed over disjoint random in-regime draws) are **independent
    samples** — there is no common per-event subset to pair. So the contrast is the
    independence-assuming :func:`xen.expectancy.contrast_ci` on the stored
    bootstrap distributions, exactly mirroring EXP-060's champion-vs-matched-random
    test (``contrast_random_low``). Median is binding; mean is the disclosed skew
    readout. ``NaN`` bounds when either distribution is empty (a power-limited arm).
    """
    med_low, med_lo, med_hi = contrast_ci(variant.dist, null.dist)
    mean_low, mean_lo, mean_hi = contrast_ci(variant.mean_dist, null.mean_dist)
    return {"median_low_1s": med_low, "median_lo_2s": med_lo, "median_hi_2s": med_hi,
            "mean_low_1s": mean_low, "mean_lo_2s": mean_lo, "mean_hi_2s": mean_hi,
            "variant_m": variant.m, "null_m": null.m}


# --------------------------------------------------------------------------- #
# Pure computation — matched-random controls (the nulls)
# --------------------------------------------------------------------------- #
def matched_random_arm(
    ohlc: dict[str, np.ndarray], state_all: InProgressState, mv: dict[str, np.ndarray],
    warmup_all: np.ndarray, atr_all: np.ndarray, signal_idx: np.ndarray, arm: ArmSpec,
    draw_count: int, last_train_idx: int, cell_index: int,
    pb_draw: int, pb_boot: int, pb_boot_mean: int,
) -> ArmResult:
    """Matched-count random control for one arm (in-progress rd; non-signal pool).

    Generic over the segmentation: ZigZag (RZ3) passes ZigZag ``state_all``/``mv``;
    MA (RM3) passes the MA-segmentation analogs. The eligible pool is every
    in-regime bar (valid live state, positive ``m_sofar``, finite positive ATR, not
    in warmup) **excluding** the conditioned-harami entries; ``draw_count`` matched
    entries are drawn without replacement and resolved through the identical
    V2A x ADV-NONE x cap pipeline. RNG purposes are supplied so RZ3 reproduces
    EXP-060 byte-identically and RM3 uses fresh dedicated streams.
    """
    n_bars = ohlc["close"].shape[0]
    eligible = (state_all.valid & (state_all.m_sofar > 0.0) & np.isfinite(atr_all)
                & (atr_all > 0.0) & (~warmup_all))
    is_signal = np.zeros(n_bars, dtype=bool)
    is_signal[signal_idx] = True
    pool = np.flatnonzero(eligible & ~is_signal)
    if draw_count <= 0 or pool.shape[0] == 0:
        return _empty_arm()
    k = min(draw_count, pool.shape[0])
    drawn = np.sort(_rng(cell_index, pb_draw + arm.idx).choice(pool, size=k, replace=False))
    sub = _subset_state(state_all, drawn)
    bar = benchmark_barriers(ohlc["close"][drawn], sub.rd, sub.m_sofar)
    bench_n, bench_warmup = adaptive_time_caps_by_epoch(
        ohlc["epoch"][drawn], mv["confirm_epoch"], mv["confirm_idx"])
    pop = (sub.valid & (sub.m_sofar > 0.0) & np.isfinite(atr_all[drawn])
           & (atr_all[drawn] > 0.0) & ~bench_warmup)
    return resolve_arm(ohlc, drawn, ohlc["close"][drawn], sub.rd, atr_all[drawn], arm,
                       bar["fav_dist"], bar["fav"], bar["adv"], bench_n, pop,
                       last_train_idx, _rng(cell_index, pb_boot + arm.idx),
                       _rng(cell_index, pb_boot_mean + arm.idx), draw_count=draw_count)


def ma_seg_arm(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, ma: dict[str, Any], arm: ArmSpec,
    retain_mask: np.ndarray, last_train_idx: int, cell_index: int,
    pb_boot: int, pb_boot_mean: int,
) -> ArmResult:
    """MA(20,50)-segmentation arm through the identical exit pipeline.

    ``ma`` carries the precomputed MA harami-entry state / barriers / cap (built
    once per cell). ``retain_mask`` is the conditioning filter applied on top of
    ``buildable`` — the binding /STRONG-STAT p75 (M0-M3) or the disclosed
    /STRONG-HA (M3 rerun). Reproduces EXP-060's ``ma_seg_arm`` for the p75 mask.
    """
    if ma["empty"]:
        return _empty_arm()
    pop = ma["buildable"] & retain_mask
    return resolve_arm(ohlc, entry_idx, ma["entry_close"], ma["state"].rd, ma["atr_entry"],
                       arm, ma["fav_dist"], ma["fav"], ma["adv"], ma["bench_n"], pop,
                       last_train_idx, _rng(cell_index, pb_boot + arm.idx),
                       _rng(cell_index, pb_boot_mean + arm.idx))


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
    last_train_idx = int(ohlc["close"].shape[0]) - 1
    moves = generate_zigzag(bars, atr_period=ATR_PERIOD, atr_mult=ATR_MULT)
    mv = move_arrays(moves, ohlc["epoch"])
    atr = wilder_atr(ohlc["high"], ohlc["low"], ohlc["close"], ATR_PERIOD)
    entry_idx, entry_epoch, ha_ann = harami_entry_indices(bars, ohlc["epoch"])
    base = {"domain": domain, "n_bars": int(bars.height), "n_moves": int(moves.height),
            "n_harami": int(entry_idx.shape[0])}
    if entry_idx.shape[0] == 0 or mv["confirm_epoch"].shape[0] == 0:
        return {**base, "empty": True}

    zz = _zz_context(ohlc, atr, entry_idx, entry_epoch, mv, ha_ann)
    ma = _ma_context(ohlc, atr, entry_idx, entry_epoch, ha_ann)
    arms = _resolve_arms(ohlc, entry_idx, zz, ma, mv, last_train_idx, cell_index)
    cond = zz["buildable"] & zz["stat"]["retained_p75"]
    return {
        **base, "empty": False, "arms": arms,
        "n_buildable": int(zz["buildable"].sum()), "n_conditioned": int(cond.sum()),
        "ma_conditioned": int((ma["buildable"] & ma["stat"]["retained_p75"]).sum()
                              ) if not ma["empty"] else 0,
        "causality_ok": _causality_ok(ohlc, entry_idx, entry_epoch, zz["state"], mv, ma),
        "invariants": _cell_invariants(arms, ohlc, entry_idx, zz, ma, last_train_idx),
    }


def _zz_context(
    ohlc: dict[str, np.ndarray], atr: np.ndarray, entry_idx: np.ndarray,
    entry_epoch: np.ndarray, mv: dict[str, np.ndarray], ha_ann: pl.DataFrame,
) -> dict[str, Any]:
    """ZigZag conditioned-signal context at the harami entries (Z arms + RZ3)."""
    entry_close = ohlc["close"][entry_idx]
    state = live_in_progress_state(entry_epoch, entry_close, mv["confirm_epoch"],
                                   mv["end_price"], mv["end_epoch"], mv["direction"])
    atr_entry = atr[entry_idx]
    bench_n, bench_warmup = adaptive_time_caps_by_epoch(
        entry_epoch, mv["confirm_epoch"], mv["confirm_idx"])
    buildable = (state.valid & (state.m_sofar > 0.0) & np.isfinite(atr_entry)
                 & (atr_entry > 0.0) & ~bench_warmup)
    stat = live_strong_stat(state.k, state.m_sofar, mv["magnitude"])
    ha_same = strong_ha_retention(ha_ann, entry_epoch, state.start_epoch, -state.rd,
                                  state.valid)
    bar = benchmark_barriers(entry_close, state.rd, state.m_sofar)
    return {"entry_close": entry_close, "state": state, "atr": atr, "atr_entry": atr_entry,
            "bench_n": bench_n, "buildable": buildable, "stat": stat, "ha_same": ha_same,
            "fav_dist": bar["fav_dist"], "fav": bar["fav"], "adv": bar["adv"]}


def _ma_context(
    ohlc: dict[str, np.ndarray], atr: np.ndarray, entry_idx: np.ndarray,
    entry_epoch: np.ndarray, ha_ann: pl.DataFrame,
) -> dict[str, Any]:
    """MA(20,50) conditioned-signal context at the harami entries (M arms + RM3).

    Built once per cell and shared by every MA arm so the M0-M3 medians reproduce
    EXP-060's ``ma_seg_arm`` exactly. Also exposes the MA-segmentation arrays and
    the per-bar non-signal exclusion index for the RM3 control.
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
    ha_same = strong_ha_retention(ha_ann, entry_epoch, state.start_epoch, -state.rd,
                                  state.valid)
    bar = benchmark_barriers(entry_close, state.rd, state.m_sofar)
    return {"empty": False, "seg": seg, "entry_close": entry_close, "state": state,
            "atr_entry": atr_entry, "bench_n": bench_n, "buildable": buildable,
            "stat": stat, "ha_same": ha_same, "fav_dist": bar["fav_dist"],
            "fav": bar["fav"], "adv": bar["adv"]}


def _resolve_arms(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, zz: dict[str, Any],
    ma: dict[str, Any], mv: dict[str, np.ndarray], last_train_idx: int, cell_index: int,
) -> dict[str, Any]:
    """Resolve the 8 signal arms + RZ3/RM3 nulls + the D2 signal-vs-null contrasts."""
    # ZigZag signal arms (Z0-Z3) on the binding /STRONG-STAT p75 population.
    zz_arms = {a.aid: resolve_arm(
        ohlc, entry_idx, zz["entry_close"], zz["state"].rd, zz["atr_entry"], a,
        zz["fav_dist"], zz["fav"], zz["adv"], zz["bench_n"],
        zz["buildable"] & zz["stat"]["retained_p75"], last_train_idx,
        _rng(cell_index, PB_STAT + a.idx), _rng(cell_index, PB_STAT_MEAN + a.idx))
        for a in ARMS}
    # MA signal arms (M0-M3) on the MA /STRONG-STAT p75 population.
    ma_arms = {a.aid: ma_seg_arm(ohlc, entry_idx, ma, a, ma["stat"]["retained_p75"]
                                 if not ma["empty"] else np.empty(0, dtype=bool),
                                 last_train_idx, cell_index, PB_MASEG, PB_MASEG_MEAN)
               for a in ARMS}
    champ = ARM_BY_ID[CHAMPION_ID]
    # Disclosed /STRONG-HA reruns of the champion geometry (Z3-HA, M3-HA).
    z3_ha = resolve_arm(
        ohlc, entry_idx, zz["entry_close"], zz["state"].rd, zz["atr_entry"], champ,
        zz["fav_dist"], zz["fav"], zz["adv"], zz["bench_n"],
        zz["buildable"] & zz["ha_same"], last_train_idx,
        _rng(cell_index, PB_HA + champ.idx), _rng(cell_index, PB_HA_MEAN + champ.idx))
    m3_ha = ma_seg_arm(ohlc, entry_idx, ma, champ,
                       ma["ha_same"] if not ma["empty"] else np.empty(0, dtype=bool),
                       last_train_idx, cell_index, PB_MASEG_HA, PB_MASEG_HA_MEAN)
    # Matched-random nulls (RZ3 reproduces EXP-060; RM3 is the new control).
    rz3, rm3 = _resolve_nulls(ohlc, entry_idx, zz, ma, mv, zz_arms[CHAMPION_ID].m,
                              ma_arms[CHAMPION_ID].m, last_train_idx, cell_index)
    contrasts = {
        "m3_rm3": champion_vs_null_contrast(ma_arms[CHAMPION_ID], rm3),
        "z3_rz3": champion_vs_null_contrast(zz_arms[CHAMPION_ID], rz3),
    }
    return {"zz": zz_arms, "ma": ma_arms, "z3_ha": z3_ha, "m3_ha": m3_ha,
            "rz3": rz3, "rm3": rm3, "contrasts": contrasts}


def _resolve_nulls(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, zz: dict[str, Any],
    ma: dict[str, Any], mv: dict[str, np.ndarray], z3_m: int, m3_m: int,
    last_train_idx: int, cell_index: int,
) -> tuple[ArmResult, ArmResult]:
    """RZ3 (ZigZag matched-random) and RM3 (MA matched-random) for V2A-NONE."""
    champ = ARM_BY_ID[CHAMPION_ID]
    # RZ3 — ZigZag substrate (reproduces EXP-060 matched_random for V2A-NONE).
    zz_state_all = live_in_progress_state(ohlc["epoch"], ohlc["close"], mv["confirm_epoch"],
                                          mv["end_price"], mv["end_epoch"], mv["direction"])
    _, zz_warmup_all = adaptive_time_caps_by_epoch(
        ohlc["epoch"], mv["confirm_epoch"], mv["confirm_idx"])
    zz_signal_idx = entry_idx[zz["stat"]["retained_p75"]]
    rz3 = matched_random_arm(ohlc, zz_state_all, mv, zz_warmup_all, zz["atr"],
                             zz_signal_idx, champ, z3_m, last_train_idx, cell_index,
                             PB_RAND_DRAW, PB_RAND_BOOT, PB_RAND_BOOT_MEAN)
    # RM3 — MA substrate (the one new computation; the binding discriminator).
    if ma["empty"]:
        return rz3, _empty_arm()
    seg = ma["seg"]
    ma_state_all = live_in_progress_state(ohlc["epoch"], ohlc["close"], seg["confirm_epoch"],
                                          seg["end_price"], seg["end_epoch"], seg["direction"])
    _, ma_warmup_all = adaptive_time_caps_by_epoch(
        ohlc["epoch"], seg["confirm_epoch"], seg["confirm_idx"])
    ma_signal_idx = entry_idx[ma["stat"]["retained_p75"]]
    rm3 = matched_random_arm(ohlc, ma_state_all, seg, ma_warmup_all, zz["atr"],
                             ma_signal_idx, champ, m3_m, last_train_idx, cell_index,
                             PB_RM3_DRAW, PB_RM3_BOOT, PB_RM3_BOOT_MEAN)
    return rz3, rm3


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


def _cell_invariants(
    arms: dict[str, Any], ohlc: dict[str, np.ndarray], entry_idx: np.ndarray,
    zz: dict[str, Any], ma: dict[str, Any], last_train_idx: int,
) -> dict[str, bool]:
    """Predeclared structural invariants (scope §Success/Failure (iv)-(vii))."""
    weights_ok = all(abs(sum(a.weights) - 1.0) <= 1e-12 for a in ARMS)
    # (v) ADV-NONE sentinel never fires an ADV exit on Z3/Z1/M3/M1/RZ3/RM3.
    adv_none_ok = all(res.exit_weights.get("ADV", 0.0) <= 0.0 for res in (
        arms["zz"]["V2A-NONE"], arms["zz"]["50PCT-NONE"], arms["ma"]["V2A-NONE"],
        arms["ma"]["50PCT-NONE"], arms["rz3"], arms["rm3"]))
    # (vi) shared 1:1 stop closes all still-open legs at the benchmark adv level
    # (V2A x 1:1 geometry, both substrates: Z2/M2).
    shared_ok = _shared_stop_ok(ohlc, entry_idx, zz, last_train_idx)
    if not ma["empty"]:
        shared_ok = shared_ok and _shared_stop_ok(ohlc, entry_idx, ma, last_train_idx)
    # (vii) matched-count holds: RM3/RZ3 draw target == its signal arm's qualifying m.
    matched_ok = (arms["rz3"].draw_count == arms["zz"]["V2A-NONE"].m
                  and arms["rm3"].draw_count == arms["ma"]["V2A-NONE"].m)
    return {"weights_sum_ok": bool(weights_ok), "adv_none_no_stop": bool(adv_none_ok),
            "shared_stop_ok": bool(shared_ok), "matched_count_ok": bool(matched_ok)}


def _shared_stop_ok(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, ctx: dict[str, Any],
    last_train_idx: int,
) -> bool:
    """Re-resolve V2A x 1:1 on the conditioned population; every PX_ADV leg exits
    at the benchmark adv level (mirrors EXP-060's shared-stop invariant)."""
    cond = ctx["buildable"] & ctx["stat"]["retained_p75"]
    if not cond.any():
        return True
    ec, rd, adv = ctx["entry_close"], ctx["state"].rd, ctx["adv"]
    no_rev = np.full(int(entry_idx.shape[0]), -1, dtype=np.int64)
    lvl = leg_levels_from_fracs(ec, rd, ctx["fav_dist"], _V2A)
    px, cls = resolve_legs(
        ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"], entry_idx, ec, rd,
        (LEG_LEVEL, LEG_LEVEL, LEG_LEVEL), lvl, no_rev, adv, ctx["bench_n"], cond,
        ADV_FIXED, None, last_train_idx)
    has_adv = (cls == PX_ADV).any(axis=1) & cond
    for e in np.flatnonzero(has_adv):
        legs = cls[e] == PX_ADV
        if not bool(np.allclose(px[e][legs], adv[e], atol=1e-9)):
            return False
    return True


# --------------------------------------------------------------------------- #
# Per-cell record flattening (D1 skew, D2 control, D3 exit-reason)
# --------------------------------------------------------------------------- #
ADV_NONE_ARMS = {"V2A-NONE", "50PCT-NONE"}     # ADV-NONE geometries (D1 attribution)


def _arm_fields(res: ArmResult) -> dict[str, Any]:
    """Flatten one ArmResult's scalar metrics + exit-reason weights (no arrays)."""
    gap = (res.median - res.mean) if (res.median is not None and res.mean is not None) else None
    out = {
        "m": res.m, "median": res.median, "mean": res.mean, "gap": gap,
        "ci_low_1s": res.ci_low_1s, "ci_lo_2s": res.ci_lo_2s, "ci_hi_2s": res.ci_hi_2s,
        "mean_ci_low_1s": res.mean_ci_low_1s, "mean_ci_lo_2s": res.mean_ci_lo_2s,
        "mean_ci_hi_2s": res.mean_ci_hi_2s, "r_firsthit": res.r_firsthit,
        "win_rate": res.win_rate, "data_censored": res.data_censored,
        "population": res.population, "block_len": res.block_len, "draw_count": res.draw_count,
    }
    out.update({f"ew_{label}": res.exit_weights[label] for label in PX_CLASS_LABELS.values()})
    return out


def _signal_object_rows(instrument: str, cell: dict[str, Any]) -> list[dict[str, Any]]:
    """The 10 predeclared objects for one cell (8 signal arms + RZ3 + RM3)."""
    rows: list[dict[str, Any]] = []
    common = {"instrument": instrument, "domain": cell["domain"], "member": True,
              "excluded": False, "n_bars": cell["n_bars"], "n_moves": cell["n_moves"],
              "n_harami": cell["n_harami"], "n_conditioned": cell["n_conditioned"],
              "ma_conditioned": cell["ma_conditioned"]}
    arms = cell["arms"]
    for a in ARMS:
        z_viable, _ = _viability(arms["zz"][a.aid])
        rows.append({**common, "label": f"Z{a.idx}", "substrate": "ZigZag", "role": "signal",
                     "geometry": a.aid, "adv_none": a.adv_none, "median_viable": z_viable,
                     "mean_viable": _mean_viable(arms["zz"][a.aid]), **_arm_fields(arms["zz"][a.aid])})
        m_viable, _ = _viability(arms["ma"][a.aid])
        rows.append({**common, "label": f"M{a.idx}", "substrate": "MA", "role": "signal",
                     "geometry": a.aid, "adv_none": a.adv_none, "median_viable": m_viable,
                     "mean_viable": _mean_viable(arms["ma"][a.aid]), **_arm_fields(arms["ma"][a.aid])})
    rows.append({**common, "label": "RZ3", "substrate": "ZigZag-random", "role": "null",
                 "geometry": CHAMPION_ID, "adv_none": True, "median_viable": False,
                 "mean_viable": False, **_arm_fields(arms["rz3"])})
    rows.append({**common, "label": "RM3", "substrate": "MA-random", "role": "null",
                 "geometry": CHAMPION_ID, "adv_none": True, "median_viable": False,
                 "mean_viable": False, **_arm_fields(arms["rm3"])})
    return rows


def _viability(res: ArmResult) -> tuple[bool, bool]:
    """(median CI_low>0 and m>=floor, powered)."""
    powered = res.m >= POWER_FLOOR
    viable = bool(powered and res.ci_low_1s is not None
                  and np.isfinite(res.ci_low_1s) and res.ci_low_1s > 0.0)
    return viable, powered


def _mean_viable(res: ArmResult) -> bool:
    return bool(res.m >= POWER_FLOOR and res.mean_ci_low_1s is not None
                and np.isfinite(res.mean_ci_low_1s) and res.mean_ci_low_1s > 0.0)


def ma_control_row(instrument: str, cell: dict[str, Any]) -> dict[str, Any]:
    """D2 per-cell binding discriminator row (M3 vs RM3 + the per-cell flags)."""
    arms = cell["arms"]
    m3, rm3 = arms["ma"]["V2A-NONE"], arms["rm3"]
    z3, rz3 = arms["zz"]["V2A-NONE"], arms["rz3"]
    c = arms["contrasts"]["m3_rm3"]
    cz = arms["contrasts"]["z3_rz3"]
    # Method 4 (disclosed continuity): independent bootstrap contrast of the champion
    # vs the two P13 baselines — reproduces EXP-060's contrast_random_low/contrast_ma_low.
    z3_contrast_random_low = contrast_ci(z3.dist, rz3.dist)[0]
    z3_contrast_ma_low = contrast_ci(z3.dist, m3.dist)[0]
    m3_median_viable, m3_powered = _viability(m3)
    m3_mean_viable = _mean_viable(m3)
    m3_beats_rm3 = bool(np.isfinite(c["median_low_1s"]) and c["median_low_1s"] > 0.0)
    m3_lead = bool(m3_median_viable and m3_mean_viable and m3_beats_rm3)
    if cell["domain"] is None:
        status = "EXCLUDED"
    elif not m3_powered:
        status = "NOT_POWERED"
    elif m3_lead:
        status = "LEAD_CELL"
    elif m3_median_viable:
        status = "MEDIAN_VIABLE_NOT_LEAD"
    else:
        status = "NOT_MEDIAN_VIABLE"
    return {
        "instrument": instrument, "domain": cell["domain"], "m3_m": m3.m, "rm3_m": rm3.m,
        "rm3_draw_count": rm3.draw_count, "m3_median": m3.median, "m3_ci_low_1s": m3.ci_low_1s,
        "m3_mean": m3.mean, "m3_mean_ci_low_1s": m3.mean_ci_low_1s,
        "m3_rm3_median_low_1s": c["median_low_1s"], "m3_rm3_median_hi_2s": c["median_hi_2s"],
        "m3_rm3_mean_low_1s": c["mean_low_1s"],
        "z3_rz3_median_low_1s": cz["median_low_1s"], "z3_rz3_mean_low_1s": cz["mean_low_1s"],
        "z3_contrast_random_low": z3_contrast_random_low, "z3_contrast_ma_low": z3_contrast_ma_low,
        "m3_median_viable": m3_median_viable, "m3_mean_viable": m3_mean_viable,
        "m3_beats_rm3": m3_beats_rm3, "m3_lead_cell": m3_lead,
        "viable_status": status, "status_code": VSTATUS_CODES[status],
    }


def skew_rows(instrument: str, cell: dict[str, Any]) -> list[dict[str, Any]]:
    """D1 per-cell median/mean/gap rows for the 8 signal arms."""
    arms = cell["arms"]
    rows = []
    for substrate, store in (("ZigZag", "zz"), ("MA", "ma")):
        for a in ARMS:
            res = arms[store][a.aid]
            rows.append({
                "instrument": instrument, "domain": cell["domain"],
                "label": f"{'Z' if substrate == 'ZigZag' else 'M'}{a.idx}",
                "substrate": substrate, "geometry": a.aid, "adv_none": a.adv_none,
                "m": res.m, "median": res.median, "mean": res.mean,
                "gap": (res.median - res.mean) if (res.median is not None
                                                   and res.mean is not None) else None,
                "median_ci_low_1s": res.ci_low_1s, "mean_ci_low_1s": res.mean_ci_low_1s,
                "mean_ci_lo_2s": res.mean_ci_lo_2s, "mean_ci_hi_2s": res.mean_ci_hi_2s})
    return rows


def exit_reason_rows(instrument: str, cell: dict[str, Any]) -> list[dict[str, Any]]:
    """D3 per-cell exit-reason composition for Z3 / M3 / RZ3 / RM3."""
    arms = cell["arms"]
    objs = (("Z3", arms["zz"]["V2A-NONE"]), ("M3", arms["ma"]["V2A-NONE"]),
            ("RZ3", arms["rz3"]), ("RM3", arms["rm3"]))
    rows = []
    for label, res in objs:
        row = {"instrument": instrument, "domain": cell["domain"], "label": label, "m": res.m}
        row.update({f"ew_{lab}": res.exit_weights[lab] for lab in PX_CLASS_LABELS.values()})
        rows.append(row)
    return rows


def secondary_rows(instrument: str, cell: dict[str, Any]) -> list[dict[str, Any]]:
    """Disclosed secondaries: /STRONG-HA rerun of M3/Z3 + single-leg first-hit r."""
    arms = cell["arms"]
    rows = []
    for label, res in (("Z3-HA", arms["z3_ha"]), ("M3-HA", arms["m3_ha"])):
        rows.append({"instrument": instrument, "domain": cell["domain"], "object": label,
                     "m": res.m, "median": res.median, "ci_low_1s": res.ci_low_1s,
                     "mean": res.mean, "mean_ci_low_1s": res.mean_ci_low_1s,
                     "win_rate": res.win_rate, "r_firsthit": res.r_firsthit})
    for substrate, store in (("Z", "zz"), ("M", "ma")):       # single-leg first-hit r
        for a in ARMS:
            if len(a.leg_fracs) != 1:
                continue
            res = arms[store][a.aid]
            rows.append({"instrument": instrument, "domain": cell["domain"],
                         "object": f"{substrate}{a.idx}-r", "m": res.m, "median": res.median,
                         "ci_low_1s": res.ci_low_1s, "mean": res.mean,
                         "mean_ci_low_1s": res.mean_ci_low_1s, "win_rate": res.win_rate,
                         "r_firsthit": res.r_firsthit})
    return rows


def excluded_rows(instrument: str, domain: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """COVERAGE_EXCLUDED placeholder rows for one cell."""
    obj_rows = []
    common = {"instrument": instrument, "domain": domain, "member": False, "excluded": True,
              "n_bars": None, "n_moves": None, "n_harami": None, "n_conditioned": None,
              "ma_conditioned": None}
    for label, substrate, geom in [(f"Z{a.idx}", "ZigZag", a.aid) for a in ARMS] + \
            [(f"M{a.idx}", "MA", a.aid) for a in ARMS] + \
            [("RZ3", "ZigZag-random", CHAMPION_ID), ("RM3", "MA-random", CHAMPION_ID)]:
        obj_rows.append({**common, "label": label, "substrate": substrate, "role": "excluded",
                         "geometry": geom, "adv_none": False, "median_viable": False,
                         "mean_viable": False, **_arm_fields(_empty_arm())})
    ctrl = {"instrument": instrument, "domain": domain, "viable_status": "EXCLUDED",
            "status_code": VSTATUS_CODES["EXCLUDED"], "m3_median_viable": False,
            "m3_mean_viable": False, "m3_beats_rm3": False, "m3_lead_cell": False}
    return obj_rows, ctrl


# --------------------------------------------------------------------------- #
# Composition + verdict readout
# --------------------------------------------------------------------------- #
def _p11(rows: list[dict[str, Any]], flag: str) -> dict[str, Any]:
    """P11 tally (>=5 cells over >=3 instruments) for a per-cell boolean flag."""
    hit = [r for r in rows if r.get(flag)]
    instruments = sorted({r["instrument"] for r in hit})
    n_cells, n_instr = len(hit), len(instruments)
    composes = n_cells >= P11_MIN_CELLS and n_instr >= P11_MIN_INSTR
    return {"n_cells": n_cells, "n_instruments": n_instr, "composes": composes,
            "cells": [f"{r['instrument']}-{r['domain']}" for r in hit],
            "fragile": composes and (n_cells == P11_MIN_CELLS or n_instr == P11_MIN_INSTR)}


def composition_readout(
    control_rows: list[dict[str, Any]], skew: list[dict[str, Any]], defect: dict[str, Any],
) -> dict[str, Any]:
    """P11 composition of the MA-substrate flags + the artifact-vs-lead verdict."""
    cells = [r for r in control_rows if r.get("viable_status") != "EXCLUDED"]
    median_viable = _p11(cells, "m3_median_viable")
    mean_viable = _p11(cells, "m3_mean_viable")
    beats_rm3 = _p11(cells, "m3_beats_rm3")
    lead = _p11(cells, "m3_lead_cell")
    verdict = _verdict(defect, median_viable, lead)
    return {
        "verdict": verdict, "champion_object": "M3 (V2A-NONE on MA(20,50))",
        "binding_discriminator": ("M3 - RM3 independent-contrast median CI_low>0 "
                                  "(own-substrate matched-random control; mirrors EXP-060 "
                                  "champion-vs-random)"),
        "m3_median_viable": median_viable, "m3_mean_viable": mean_viable,
        "m3_beats_rm3": beats_rm3, "m3_lead_cell": lead,
        "skew_attribution": _skew_attribution(skew), "defect": defect,
        "rule": ("Binding endpoint = median (P14); mean disclosed. Per cell (m>=30): "
                 "m3_median_viable = M3 median CI_low(1s)>0; m3_mean_viable = M3 mean "
                 "CI_low(1s)>0; m3_beats_rm3 = (M3-RM3) independent-contrast median "
                 "CI_low(1s)>0 (contrast_ci, mirrors EXP-060 champion-vs-random); "
                 "m3_lead_cell = all three. SUBSTRATE_LEAD_FOUND iff m3_lead_cell composes "
                 "P11 (>=5 cells/>=3 instruments). ARTIFACT_CONFIRMED iff m3_median_viable "
                 "composes P11 AND the lead fails P11 (skew: mean not viable; and/or "
                 "redundancy: does not beat RM3). The mean and RM3 only make the lead "
                 "criterion stricter (P14-consistent: never declare viable on the mean)."),
        "g2_routing": ("Feeds the single 014-B G2 (no closure or candidate registration "
                       "here). ARTIFACT_CONFIRMED strengthens EXP-060's CHARACTERISED_NOT_VIABLE; "
                       "SUBSTRATE_LEAD_FOUND -> G2 should not close CF-HA-HARAMI-001 without a "
                       "new scoped MA-substrate experiment."),
    }


def _verdict(defect: dict[str, Any], median_viable: dict[str, Any],
             lead: dict[str, Any]) -> str:
    """Mechanical artifact-vs-lead verdict (analysis-plan §6)."""
    if defect["is_defect"]:
        return "SUBSTRATE_METHOD_DEFECT"
    if lead["composes"]:
        return "SUBSTRATE_LEAD_FOUND"
    if median_viable["composes"]:
        return "ARTIFACT_CONFIRMED"
    return "INCONCLUSIVE_POWER_LIMITED"


def _skew_attribution(skew: list[dict[str, Any]]) -> dict[str, Any]:
    """D1 sub-readout: is the median-mean gap concentrated in the ADV-NONE arms?

    Descriptive only (never enters the verdict). Pools per-cell gaps for ADV-NONE
    arms (Z3,Z1,M3,M1) vs 1:1 arms (Z2,Z0,M2,M0) on each substrate.
    """
    def pooled(substrate: str, adv_none: bool) -> float | None:
        gaps = [r["gap"] for r in skew if r["substrate"] == substrate
                and r["adv_none"] == adv_none and r["gap"] is not None and np.isfinite(r["gap"])]
        return float(np.median(gaps)) if gaps else None

    out = {}
    for substrate in ("ZigZag", "MA"):
        adv_gap = pooled(substrate, True)
        fix_gap = pooled(substrate, False)
        out[substrate] = {
            "adv_none_median_gap": adv_gap, "fixed_1to1_median_gap": fix_gap,
            "uncapped_downside_is_skew_source": bool(
                adv_gap is not None and fix_gap is not None and adv_gap > fix_gap)}
    return out


# --------------------------------------------------------------------------- #
# Determinism replay + EXP-060 reconciliation (DEFECT guards)
# --------------------------------------------------------------------------- #
def determinism_replay(train_1m: pl.DataFrame, domain: str, train_end_epoch: int,
                       cell_index: int) -> bool:
    """Re-run one cell end-to-end and assert byte-identical binding outputs."""
    a = compute_cell(train_1m, domain, train_end_epoch, cell_index)
    b = compute_cell(train_1m, domain, train_end_epoch, cell_index)
    if a.get("empty") or b.get("empty"):
        return a.get("empty") == b.get("empty")
    for store in ("zz", "ma"):
        for aid in ARM_BY_ID:
            sa, sb = a["arms"][store][aid], b["arms"][store][aid]
            if not (np.array_equal(sa.r_e, sb.r_e)
                    and (sa.median, sa.ci_low_1s, sa.mean_ci_low_1s)
                    == (sb.median, sb.ci_low_1s, sb.mean_ci_low_1s)):
                return False
    for null in ("rz3", "rm3"):
        if not np.array_equal(a["arms"][null].r_e, b["arms"][null].r_e):
            return False
    ca = a["arms"]["contrasts"]["m3_rm3"]
    cb = b["arms"]["contrasts"]["m3_rm3"]
    return (_nan_eq(ca["median_low_1s"], cb["median_low_1s"])
            and _nan_eq(ca["mean_low_1s"], cb["mean_low_1s"]))


def _nan_eq(a: float, b: float) -> bool:
    """Float equality that treats NaN == NaN as True (for power-limited contrasts)."""
    if a is None or b is None:
        return a is b
    return bool(a == b or (np.isnan(a) and np.isnan(b)))


def exp060_reconciliation(
    instrument: str, cell: dict[str, Any], exp060: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    """Reproduction guard vs EXP-060 (scope invariants i, ii, iii).

    (iii) population + median for **all** signal arms: Z0-Z3 vs EXP-060 signal
    arms, M0-M3 vs EXP-060 ``maseg``. (i) Z3 also reconciles exit-weights;
    (ii) M3 median is the maseg V2A-NONE reproduction. Any divergence beyond
    ``RECON_TOL`` is SUBSTRATE/METHOD_DEFECT.
    """
    key = (instrument, cell["domain"])
    if not exp060 or key not in exp060 or cell.get("empty"):
        return {"checked": False, "cell": f"{instrument}-{cell.get('domain')}"}
    src = exp060[key]["arms"]
    arm_ok = True
    for a in ARMS:
        s = src.get(a.aid)
        if s is None:
            arm_ok = False
            continue
        z, mm = cell["arms"]["zz"][a.aid], cell["arms"]["ma"][a.aid]
        arm_ok &= (z.m == (int(s["z_m"]) if s["z_m"] is not None else 0)
                   and _float_match(z.median, s["z_median"])
                   and mm.m == (int(s["m_m"]) if s["m_m"] is not None else 0)
                   and _float_match(mm.median, s["m_median"]))
    z3, m3 = cell["arms"]["zz"]["V2A-NONE"], cell["arms"]["ma"]["V2A-NONE"]
    ew = exp060[key].get("ew", {})
    ew_ok = all(_float_match(z3.exit_weights[lab], ew.get(lab))
                for lab in PX_CLASS_LABELS.values())
    consistent = bool(arm_ok and ew_ok)
    return {"checked": True, "cell": f"{instrument}-{cell['domain']}",
            "z3_m": z3.m, "exp060_z3_m": src["V2A-NONE"]["z_m"], "z3_median": z3.median,
            "exp060_z3_median": src["V2A-NONE"]["z_median"], "m3_m": m3.m,
            "exp060_m3_m": src["V2A-NONE"]["m_m"], "m3_median": m3.median,
            "exp060_m3_median": src["V2A-NONE"]["m_median"],
            "all_signal_arms_match": bool(arm_ok), "z3_exit_weights_match": bool(ew_ok),
            "consistent": consistent}


def _float_match(a: float | None, b: float | None) -> bool:
    """Two optional floats agree to RECON_TOL (both None counts as a match)."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return abs(float(a) - float(b)) <= RECON_TOL


# --------------------------------------------------------------------------- #
# Plotting (bounded; from collected per-cell summaries — no reloads)
# --------------------------------------------------------------------------- #
def _placeholder(ax: plt.Axes, message: str) -> None:
    ax.text(0.5, 0.5, message, ha="center", va="center")
    ax.axis("off")


def plot_median_vs_mean(skew: list[dict[str, Any]], save_path: Path) -> None:
    """D1 headline: per-arm pooled median vs mean (M3/Z3 highlighted)."""
    order = [f"{p}{a.idx}" for p in ("Z", "M") for a in ARMS]
    fig, ax = plt.subplots(figsize=(11, 6))
    xs, med, mean = [], [], []
    for i, lab in enumerate(order):
        rows = [r for r in skew if r["label"] == lab and r["median"] is not None]
        if not rows:
            continue
        xs.append(i)
        med.append(float(np.median([r["median"] for r in rows])))
        mean.append(float(np.median([r["mean"] for r in rows if r["mean"] is not None])))
    if not xs:
        _placeholder(ax, "no powered cells")
    else:
        ax.scatter(xs, med, c="#1a9850", s=60, marker="o", label="pooled median", zorder=3)
        ax.scatter(xs, mean, c="#d73027", s=60, marker="s", label="pooled mean", zorder=3)
        for x, mlo, mhi in zip(xs, med, mean):
            ax.plot([x, x], [mlo, mhi], color="#999999", lw=1.0, zorder=1)
        for lab, x in (("Z3", order.index("Z3")), ("M3", order.index("M3"))):
            if x in xs:
                ax.axvline(x, color="#4575b4", lw=0.6, ls=":", alpha=0.6)
        ax.axhline(0.0, color="k", lw=0.8, ls="--")
        ax.set_xticks(range(len(order)), order)
        ax.set_ylabel("pooled per-cell expectancy (ATR units)")
        ax.legend(fontsize=9)
    ax.set_title(f"{EXPERIMENT_ID} D1: median vs mean per arm x substrate "
                 "(Z3/M3 = champion geometry)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_skew_gap(skew: list[dict[str, Any]], save_path: Path) -> None:
    """D1 attribution: median-mean gap by adverse model (ADV-NONE vs 1:1)."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    for ax, substrate in zip(axes, ("ZigZag", "MA")):
        groups = {"ADV-NONE": [], "1:1": []}
        for r in skew:
            if r["substrate"] != substrate or r["gap"] is None or not np.isfinite(r["gap"]):
                continue
            groups["ADV-NONE" if r["adv_none"] else "1:1"].append(r["gap"])
        data = [groups["ADV-NONE"] or [0.0], groups["1:1"] or [0.0]]
        ax.boxplot(data, positions=[1, 2], widths=0.6)
        ax.axhline(0.0, color="k", lw=0.8, ls="--")
        ax.set_xticks([1, 2], ["ADV-NONE\n(Z3,Z1,M3,M1)", "1:1\n(Z2,Z0,M2,M0)"])
        ax.set_title(f"{substrate} substrate")
    axes[0].set_ylabel("per-cell median - mean gap (ATR units)")
    fig.suptitle(f"{EXPERIMENT_ID} D1: skew gap by adverse model "
                 "(large gap under ADV-NONE only => uncapped downside is the skew source)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_m3_rm3_forest(control: list[dict[str, Any]], save_path: Path) -> None:
    """D2: per-cell M3-RM3 independent-contrast median CI_low forest (Z3-RZ3 overlaid)."""
    rows = sorted([r for r in control if r.get("m3_rm3_median_low_1s") is not None
                   and np.isfinite(r.get("m3_rm3_median_low_1s", np.nan))],
                  key=lambda r: r["m3_rm3_median_low_1s"])
    fig, ax = plt.subplots(figsize=(max(9, 0.18 * max(len(rows), 1)), 7))
    if not rows:
        _placeholder(ax, "no powered M3 cells")
    else:
        x = np.arange(len(rows))
        m3 = np.array([r["m3_rm3_median_low_1s"] for r in rows])
        z3 = np.array([r["z3_rz3_median_low_1s"] if r.get("z3_rz3_median_low_1s") is not None
                       and np.isfinite(r["z3_rz3_median_low_1s"]) else np.nan for r in rows])
        colours = ["#1a9850" if r["m3_beats_rm3"] else "#d73027" for r in rows]
        ax.scatter(x, m3, c=colours, s=18, zorder=3, label="M3 - RM3 (binding)")
        ax.scatter(x, z3, facecolors="none", edgecolors="#4575b4", s=18, zorder=2,
                   label="Z3 - RZ3 (disclosed)")
        ax.axhline(0.0, color="k", lw=0.8, ls="--")
        ax.set_xticks(x, [f"{r['instrument']}-{r['domain']}" for r in rows], rotation=90,
                      fontsize=4)
        ax.set_ylabel("independent-contrast median CI_low(1s) (ATR units)")
        ax.legend(fontsize=9)
    ax.set_title(f"{EXPERIMENT_ID} D2: does the harami beat its own-substrate matched random?")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_exit_reasons(exit_rows: list[dict[str, Any]], save_path: Path) -> None:
    """D3: pooled exit-reason composition for Z3 / M3 / RZ3 / RM3."""
    labels = ["FAV", "ADV", "TIMECAP", "DATA_CENSORED"]
    colours = {"DATA_CENSORED": "#cccccc", "TIMECAP": "#fdae61", "ADV": "#d73027",
               "FAV": "#1a9850"}
    objs = ["Z3", "M3", "RZ3", "RM3"]
    comp = np.zeros((len(objs), len(labels)))
    for i, ob in enumerate(objs):
        rows = [r for r in exit_rows if r["label"] == ob and r["m"] > 0]
        if rows:
            for j, lab in enumerate(labels):
                comp[i, j] = float(np.mean([r[f"ew_{lab}"] for r in rows]))
    fig, ax = plt.subplots(figsize=(9, 6))
    bottom = np.zeros(len(objs))
    x = np.arange(len(objs))
    for j, lab in enumerate(labels):
        ax.bar(x, comp[:, j], bottom=bottom, label=lab, color=colours[lab])
        bottom += comp[:, j]
    ax.set_xticks(x, objs)
    ax.set_ylabel("mean weight fraction (qualifying events)")
    ax.legend(fontsize=9)
    ax.set_title(f"{EXPERIMENT_ID} D3: exit-reason composition "
                 "(is MA also TIMECAP-dominated, or does it convert to FAV?)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_viability_map(control: list[dict[str, Any]], save_path: Path) -> None:
    """D2/verdict: per-cell MA-substrate status across the grid (flag heatmap)."""
    flags = ["m3_median_viable", "m3_beats_rm3", "m3_mean_viable", "m3_lead_cell"]
    cells = [r for r in control if r.get("viable_status") != "EXCLUDED"]
    cells = sorted(cells, key=lambda r: (r["instrument"], r["domain"]))
    fig, ax = plt.subplots(figsize=(max(9, 0.16 * max(len(cells), 1)), 4))
    if not cells:
        _placeholder(ax, "no member cells")
    else:
        matrix = np.array([[1.0 if r.get(f) else 0.0 for r in cells] for f in flags])
        ax.imshow(matrix, cmap="Greens", vmin=0.0, vmax=1.0, aspect="auto")
        ax.set_yticks(range(len(flags)), flags, fontsize=8)
        ax.set_xticks(range(len(cells)), [f"{r['instrument']}-{r['domain']}" for r in cells],
                      rotation=90, fontsize=3)
    ax.set_title(f"{EXPERIMENT_ID}: MA-substrate per-cell viability map "
                 "(lead cell = all three upper flags)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def make_plots(skew: list[dict[str, Any]], control: list[dict[str, Any]],
               exit_rows: list[dict[str, Any]]) -> None:
    """Render the five bounded plots from collected per-cell summaries."""
    plot_median_vs_mean(skew, PLOTS_DIR / "d1_median_vs_mean.png")
    plot_skew_gap(skew, PLOTS_DIR / "d1_skew_gap_by_adverse_model.png")
    plot_m3_rm3_forest(control, PLOTS_DIR / "d2_m3_rm3_forest.png")
    plot_exit_reasons(exit_rows, PLOTS_DIR / "d3_exit_reason_composition.png")
    plot_viability_map(control, PLOTS_DIR / "ma_substrate_viability_map.png")


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _cell_index_map() -> dict[tuple[str, str], int]:
    """Stable (instrument, domain) -> int index (identical to EXP-060)."""
    return {(inst, dom): i for i, (inst, dom) in enumerate(
        (inst, dom) for inst in INSTRUMENTS for dom in DOMAINS)}


def process_instrument(
    instrument: str, exp060: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    """Worker: resolve every member cell of one instrument (the parallel unit).

    Self-contained and pure given identical inputs/seeds: each cell's RNG is seeded
    by ``(BASE_SEED, cell_index, purpose)`` (order-independent), so the
    per-instrument result is identical regardless of worker count or finish order.
    The parent merges these in ``INSTRUMENTS`` order for byte-identical output.
    """
    cell_index = _cell_index_map()
    out: dict[str, Any] = {
        "objects": [], "skew": [], "control": [], "exit_rows": [], "secondaries": [],
        "recon_rows": [], "meta": None, "causality_violations": [],
        "invariant_violations": [], "determinism_checked": [], "non_deterministic": []}
    members = [d for d in DOMAINS if (instrument, d) not in EXCLUDED_CELLS]
    if not members:
        for domain in DOMAINS:
            obj_rows, ctrl = excluded_rows(instrument, domain)
            out["objects"].extend(obj_rows)
            out["control"].append(ctrl)
        return out
    train_1m, meta = load_train_1m(instrument)
    out["meta"] = meta
    replayed = False
    for domain in DOMAINS:
        if (instrument, domain) in EXCLUDED_CELLS:
            obj_rows, ctrl = excluded_rows(instrument, domain)
            out["objects"].extend(obj_rows)
            out["control"].append(ctrl)
            continue
        ci = cell_index[(instrument, domain)]
        cell = compute_cell(train_1m, domain, meta["train_end_epoch_s"], ci)
        if cell.get("empty"):
            obj_rows, ctrl = excluded_rows(instrument, domain)   # no signal -> placeholder
            out["objects"].extend(obj_rows)
            out["control"].append(ctrl)
            out["recon_rows"].append(exp060_reconciliation(instrument, cell, exp060))
            continue
        out["objects"].extend(_signal_object_rows(instrument, cell))
        out["skew"].extend(skew_rows(instrument, cell))
        out["control"].append(ma_control_row(instrument, cell))
        out["exit_rows"].extend(exit_reason_rows(instrument, cell))
        out["secondaries"].extend(secondary_rows(instrument, cell))
        out["recon_rows"].append(exp060_reconciliation(instrument, cell, exp060))
        _record_cell_defects(cell, instrument, domain, out)
        if not replayed and cell["arms"]["zz"]["V2A-NONE"].m > 0:
            ok = determinism_replay(train_1m, domain, meta["train_end_epoch_s"], ci)
            out["determinism_checked"].append(f"{instrument}-{domain}#{ci}")
            if not ok:
                out["non_deterministic"].append(f"{instrument}-{domain}#{ci}")
            replayed = True
        del cell
    del train_1m
    return out


def _record_cell_defects(cell: dict[str, Any], instrument: str, domain: str,
                         out: dict[str, Any]) -> None:
    """Accumulate per-cell causality / invariant violations."""
    label = f"{instrument}-{domain}"
    if not cell.get("causality_ok", True):
        out["causality_violations"].append(label)
    inv = cell.get("invariants", {})
    if not all(inv.get(k, True) for k in
               ("weights_sum_ok", "adv_none_no_stop", "shared_stop_ok", "matched_count_ok")):
        out["invariant_violations"].append(label)


def _run_grid(
    exp060: dict[tuple[str, str], dict[str, Any]], workers: int,
) -> list[dict[str, Any]]:
    """Resolve all instruments (process pool if workers>1) in fixed order."""
    if workers <= 1:
        return [process_instrument(inst, exp060)
                for inst in tqdm(INSTRUMENTS, desc="instruments")]
    by_inst: dict[str, dict[str, Any]] = {}
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(process_instrument, inst, exp060): inst for inst in INSTRUMENTS}
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
    exp060 = load_exp060_map()
    workers = max(1, min(workers, len(INSTRUMENTS)))
    grid = _run_grid(exp060, workers)
    objects: list[dict[str, Any]] = []
    skew: list[dict[str, Any]] = []
    control: list[dict[str, Any]] = []
    exit_rows: list[dict[str, Any]] = []
    secondaries: list[dict[str, Any]] = []
    recon_rows: list[dict[str, Any]] = []
    instrument_meta: dict[str, Any] = {}
    defect = {"is_defect": False, "non_deterministic": [], "exp060_mismatch": [],
              "causality_violations": [], "determinism_checked": [],
              "invariant_violations": [], "exp060_available": bool(exp060),
              "exp060_checked_cells": 0, "workers": workers}
    for instrument, res in zip(INSTRUMENTS, grid):     # fixed INSTRUMENTS order
        objects.extend(res["objects"])
        skew.extend(res["skew"])
        control.extend(res["control"])
        exit_rows.extend(res["exit_rows"])
        secondaries.extend(res["secondaries"])
        recon_rows.extend(res["recon_rows"])
        if res["meta"] is not None:
            instrument_meta[instrument] = res["meta"]
        for key in ("causality_violations", "invariant_violations",
                    "determinism_checked", "non_deterministic"):
            defect[key].extend(res[key])

    _finalize_defects(defect, recon_rows)
    readout = composition_readout(control, skew, defect)
    write_outputs(objects, skew, control, exit_rows, secondaries, recon_rows, readout,
                  instrument_meta, defect)
    make_plots(skew, control, exit_rows)
    return _summarize(control, readout)


def _finalize_defects(defect: dict[str, Any], recon_rows: list[dict[str, Any]]) -> None:
    """Aggregate defect gates into the binding is_defect flag."""
    defect["exp060_mismatch"] = [r["cell"] for r in recon_rows
                                 if r.get("checked") and not r["consistent"]]
    if defect["exp060_mismatch"]:
        defect["is_defect"] = True
    defect["exp060_checked_cells"] = sum(1 for r in recon_rows if r.get("checked"))
    if not defect["exp060_available"] or defect["exp060_checked_cells"] == 0:
        defect["is_defect"] = True
    causal_instr = {c.split("-")[0] for c in defect["causality_violations"]}
    if len(causal_instr) >= P11_MIN_INSTR:
        defect["is_defect"] = True
    if defect["invariant_violations"]:                 # exact structural checks
        defect["is_defect"] = True
    if defect["non_deterministic"]:                    # byte-identical replay failed
        defect["is_defect"] = True


def write_outputs(
    objects: list[dict[str, Any]], skew: list[dict[str, Any]],
    control: list[dict[str, Any]], exit_rows: list[dict[str, Any]],
    secondaries: list[dict[str, Any]], recon_rows: list[dict[str, Any]],
    readout: dict[str, Any], instrument_meta: dict[str, Any], defect: dict[str, Any],
) -> None:
    """Persist the per-cell parquet, the D1/D2/D3 maps, and the JSON readouts."""
    pl.DataFrame(objects, strict=False).write_parquet(
        RESULTS_DIR / "per_cell_expectancy.parquet")
    pl.DataFrame(skew, strict=False).write_csv(RESULTS_DIR / "skew_map.csv")
    pl.DataFrame(control, strict=False).write_csv(RESULTS_DIR / "ma_control_map.csv")
    pl.DataFrame(exit_rows, strict=False).write_csv(RESULTS_DIR / "exit_reason_map.csv")
    (pl.DataFrame(secondaries, strict=False) if secondaries
     else pl.DataFrame({"object": []})).write_csv(RESULTS_DIR / "secondary_map.csv")
    recon_clean = [r for r in recon_rows if r.get("checked")]
    (pl.DataFrame(recon_clean, strict=False) if recon_clean
     else pl.DataFrame({"cell": []})).write_csv(RESULTS_DIR / "population_reconciliation.csv")
    with open(RESULTS_DIR / "composition_readout.json", "w") as fh:
        json.dump(readout, fh, indent=2, default=str)
    _write_metadata(instrument_meta, defect, recon_clean, readout)


def _write_metadata(
    instrument_meta: dict[str, Any], defect: dict[str, Any],
    recon_clean: list[dict[str, Any]], readout: dict[str, Any],
) -> None:
    meta = {
        "experiment_id": EXPERIMENT_ID,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "014-B", "hypothesis": "HYP-013b", "family": "CF-HA-HARAMI-001",
        "addendum": "014-B-EXP-060B-ma-substrate-dominance-addendum.md",
        "stratum": "TRAIN-only (first 49%); nested TEST + final-30% holdout sealed",
        "population": "byte-identical to EXP-053/060 conditioned /STRONG-STAT HA harami",
        "entry_anchor": "harami confirmation-bar real close (every signal arm)",
        "binding_endpoint": ("median per-event position-weighted gross ATR-normalised return "
                             "(P14, P15 fills); mean = P14 disclosed secondary"),
        "binding_discriminator": ("M3 (V2A-NONE on MA(20,50)) must clear P11 median viability "
                                  "AND beat RM3 (own-substrate matched-random; independent "
                                  "bootstrap contrast_ci median CI_low>0, mirroring EXP-060 "
                                  "champion-vs-random) AND clear P11 on the mean for "
                                  "SUBSTRATE_LEAD_FOUND"),
        "objects": ["Z0..Z3 (ZigZag signal arms)", "M0..M3 (MA(20,50) signal arms)",
                    "RZ3 (ZigZag matched-random)", "RM3 (MA matched-random, NEW)"],
        "geometry": ("2 substrates x {BENCH 50%x1:1, 50PCT-NONE 50%xADV-NONE, V2A-1TO1 "
                     "{1/3,2/3,1}x1:1, V2A-NONE {1/3,2/3,1}xADV-NONE}; benchmark adaptive cap "
                     "floor=6; no floor=48 horizon arm; no factorial decomposition"),
        "params": {
            "atr_period": ATR_PERIOD, "atr_mult_primary": ATR_MULT,
            "favourable_fraction_bench": 0.50, "adverse_bench": "1:1",
            "adverse_none": "sentinel adv = -+inf (never binds)",
            "n_legs_v2a": 3, "leg_weights": "equal (1/3)", "v2a_fracs": list(_V2A),
            "timecap_floor_bench": 6, "timecap_k": 1.5, "timecap_window": 20,
            "timecap_min_moves": 5, "stat_window": 20, "stat_min_window": 5, "stat_q": 0.75,
            "ha_run_len": 3, "ma_segmentation": [MA_FAST, MA_SLOW], "power_floor": POWER_FLOOR,
            "n_boot": N_BOOT, "boot_batch": BOOT_BATCH, "base_seed": BASE_SEED,
            "p11": [P11_MIN_CELLS, P11_MIN_INSTR],
        },
        "statistical_methods": [
            "per-cell median CI (bootstrap_median_distribution + median_ci) — binding",
            "per-cell mean CI (bootstrap_mean_distribution, same block ctor, np.mean) — disclosed",
            "independent bootstrap contrast M3-RM3 median (contrast_ci on the median "
            "bootstrap distributions; mirrors EXP-060 champion-vs-random) — binding; "
            "Z3-RZ3 + mean variants (contrast_ci on the mean distributions) — disclosed",
        ],
        "verdict": readout["verdict"],
        "m3_median_viable_composes": readout["m3_median_viable"]["composes"],
        "m3_mean_viable_composes": readout["m3_mean_viable"]["composes"],
        "m3_beats_rm3_composes": readout["m3_beats_rm3"]["composes"],
        "m3_lead_cell_composes": readout["m3_lead_cell"]["composes"],
        "skew_attribution": readout["skew_attribution"],
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
                             "across all 8 signal arms' returns/median/CI, both nulls, and the "
                             "M3-RM3 independent contrast (median + mean)."),
        "causality_ok": not defect["causality_violations"],
        "causality_violations": defect["causality_violations"],
        "invariant_violations": defect["invariant_violations"],
        "invariant_gates": ("leg weights sum to 1.0; the /ADV-NONE sentinel never fires an ADV "
                            "exit on Z3/Z1/M3/M1/RZ3/RM3; the shared 1:1 stop (V2A x 1:1, both "
                            "substrates) closes all open legs at the benchmark adv level; "
                            "matched-count holds (RZ3.draw_count == Z3.m, RM3.draw_count == M3.m). "
                            "Reproduction (SUBSTRATE/METHOD_DEFECT): all 8 signal arms reproduce "
                            "EXP-060 per-cell m + median to 1e-9 (Z0-Z3 vs signal arms, M0-M3 vs "
                            "maseg); Z3 also reproduces A3 exit-composition; M3 == maseg_median."),
        "exp060_reconciliation": recon_clean,
        "exp060_mismatch": defect["exp060_mismatch"],
        "exp060_available": defect["exp060_available"],
        "exp060_checked_cells": defect["exp060_checked_cells"],
        "exp060_source_map": str(EXP060_MAP),
        "reproduction_safety": ("median-path RNG purposes (PB_STAT/PB_HA/PB_RAND_DRAW/"
                                "PB_RAND_BOOT/PB_MASEG) + arm.idx offsets + BASE_SEED + cell-index "
                                "map are byte-identical to EXP-060; the mean bootstrap, RM3, the "
                                "M3 /STRONG-HA rerun, and RM3 use new dedicated RNG purposes so "
                                "no EXP-060 stream shifts; the D2 contrasts are deterministic "
                                "contrast_ci on stored distributions (no RNG)."),
        "is_defect": defect["is_defect"],
        "de30_disclosure": DE30_DISCLOSURE,
        "fill_approximation": ("P15 path is a documented approximation of unobserved intrabar "
                               "motion; 1-minute base bars are not replayed (EXP-054 bounds it)."),
        "adv_none_cost_caveat": ("ADV-NONE leaves the adverse unbounded within the cap; the median "
                                 "endpoint (P14) is robust to the fat left tail but the disclosed "
                                 "mean may diverge — that median-mean gap is the object under study."),
        "holdout_fence": ("Only Parquet metadata + first train_rows file-order rows read per "
                          "instrument; full file never sorted/collected; every domain bar fenced "
                          "to CloseTime <= train_end_ts; forward scans clipped to the data edge -> "
                          "DATA_CENSORED; TEST and final-30% holdout never read."),
        "registry": ("CF-HA-HARAMI-001/HYP-013b (EXP-060B); composes registered /EXIT-PARTIAL "
                     "(V2A), /ADV-NONE, the benchmark cap, and both P13 baselines; the MA-substrate "
                     "matched-random is a null. 0 candidate slots, 0 TEST reads; diagnostic "
                     "readout feeds the single 014-B G2 (no closure or candidate registration here)."),
        "instrument_meta": instrument_meta,
    }
    with open(RESULTS_DIR / "run_metadata.json", "w") as fh:
        json.dump(meta, fh, indent=2, default=str)


def _summarize(control: list[dict[str, Any]], readout: dict[str, Any]) -> dict[str, Any]:
    """Concise stdout summary."""
    status_counts: dict[str, int] = {}
    for r in control:
        s = r.get("viable_status", "EXCLUDED")
        status_counts[s] = status_counts.get(s, 0) + 1
    return {"verdict": readout["verdict"],
            "m3_median_viable": readout["m3_median_viable"],
            "m3_mean_viable": readout["m3_mean_viable"],
            "m3_beats_rm3": readout["m3_beats_rm3"],
            "m3_lead_cell": readout["m3_lead_cell"],
            "ma_status_counts": status_counts, "defect": readout["defect"]}


def _parse_args() -> argparse.Namespace:
    """CLI: --workers controls per-instrument parallelism (default = all CPUs)."""
    parser = argparse.ArgumentParser(description=f"{EXPERIMENT_ID} MA-substrate dominance")
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
    LOGGER.info("\n=== %s complete ===", EXPERIMENT_ID)
    LOGGER.info("verdict: %s", summary["verdict"])
    LOGGER.info("M3 median-viable: %s cells / %s instruments (P11=%s)",
                summary["m3_median_viable"]["n_cells"],
                summary["m3_median_viable"]["n_instruments"],
                summary["m3_median_viable"]["composes"])
    LOGGER.info("M3 beats RM3: %s cells (P11=%s); M3 mean-viable: %s cells (P11=%s)",
                summary["m3_beats_rm3"]["n_cells"], summary["m3_beats_rm3"]["composes"],
                summary["m3_mean_viable"]["n_cells"], summary["m3_mean_viable"]["composes"])
    LOGGER.info("M3 lead cells: %s / %s instruments (P11=%s)",
                summary["m3_lead_cell"]["n_cells"], summary["m3_lead_cell"]["n_instruments"],
                summary["m3_lead_cell"]["composes"])
    LOGGER.info("MA per-cell status counts: %s", json.dumps(summary["ma_status_counts"]))
    if summary["defect"]["is_defect"]:
        LOGGER.info("DEFECT: %s", json.dumps(summary["defect"], default=str))
    LOGGER.info("artifacts -> %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
