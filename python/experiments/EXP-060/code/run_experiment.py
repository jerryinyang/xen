"""EXP-060 — Combined Event System (Conditioned HA Harami; Best Per-Layer Geometry).

``CF-HA-HARAMI-001`` / HYP-013 (Phase 014-B surface read 8, the **final** 014-B
read; assembles the survivors of EXP-053/056/057/058/059). TRAIN-only, gross;
0 candidate slots, 0 TEST reads. For each EXP-049/053 member cell (instrument x
domain), on the TRAIN analysis stratum only, this script:

1. slices the first-49% (TRAIN) 1-minute rows by file-order prefix (TEST and the
   final-30% global holdout are never read), aggregates the domain (5m strict;
   others min_coverage=0.90) and fences to the TRAIN edge;
2. reproduces the **EXP-053 conditioned population byte-identically** — frozen
   Wilder-ATR primary ZigZag (atr_mult=1.0), HA haramis mapped to real bars by
   exact CloseTime match, the live in-progress move at each harami, the binding
   ``/STRONG-STAT`` (p75) filter (``/STRONG-HA`` disclosed) — entered at the
   harami real close and faded against the in-progress move;
3. holds the favourable geometry (50% of M_sofar) and the P15 path-ordered
   intrabar fills at benchmark, and assembles the **best per-layer geometry** onto
   one event over a predeclared 2x2 favourable x adverse factorial + BENCH anchor
   + one disclosed horizon sibling (5 arm configs): ``A0 BENCH`` (50% single leg,
   1:1 stop, adaptive cap floor=6); ``A1 50%xNONE`` (50% single leg, /ADV-NONE,
   floor=6); ``A2 V2A x1:1`` (V2A 3 legs {1/3,2/3,1}, 1:1 stop, floor=6);
   ``A3 V2AxNONE`` (V2A legs, /ADV-NONE, floor=6 — the **champion**, the single
   binding G2 candidate); ``A4 V2AxNONE@T48`` (champion at the registered
   /THIRD-TIME floor=48 cap — disclosed-only). The binding endpoint is the
   per-event **position-weighted** realised gross return (P14, ATR-normalised,
   P15 fills);
4. computes per-cell **median** expectancy with the regime-clustered moving-block
   bootstrap CI; for the **champion A3** the two P13 baselines (matched-random,
   MA(20,50)) and the binding two-baseline conjunction; the disclosed 2x2
   factorial decomposition (favourable / adverse main effects, the 4-series
   composite interaction, A3-A0 vs-BENCH, A4-A3 horizon) via the paired
   moving-block bootstrap; composes A3 by P11 (>=5 cells over >=3 instruments)
   and emits a mechanical PROCEED_TO_SCREEN / CHARACTERISED_NOT_VIABLE eligibility
   readout (operator adjudicates at the single 014-B G2); and
5. runs a determinism replay, a BENCH reconciliation against EXP-053's recorded
   benchmark (invariants i+ii), and the predeclared combined-system invariants
   (single-leg LEVEL == resolve_path_ordered BENCH; degenerate V2A == single leg;
   leg weights sum to 1; ADV-NONE never fires an adverse exit; shared 1:1 stop
   closes all open legs at one level; A4 differs from A3 only by the cap with
   N48 >= bench_N and A4 qual subset of A3) as SUBSTRATE/METHOD_DEFECT guards.

Real prices throughout; HA prices enter only the harami/impulse detectors and
never any metric. Outputs under results/ and plots/; created in orchestration.
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

# Pin per-process native thread pools to 1 BEFORE importing polars/numpy: parallelism
# is process-level (one worker per instrument), so N workers x M library threads would
# oversubscribe the CPU. Aggregation/bootstrap stay byte-identical single-threaded
# (OHLC aggregation is first/max/min/last/integer-sum — order-independent; the bootstrap
# is numpy median resampling, not BLAS). `setdefault` respects an explicit user override.
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
EXP053_OUTCOME = EXPERIMENTS_ROOT / "EXP-053" / "results" / "outcome_primary.csv"

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
from xen.favourable_targets import paired_median_contrast_ci  # noqa: E402
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
# Constants (Phase 014-B D0 frozen + EXP-060 predeclared; no tuning)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-060"
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
THIRD_TIME_FLOOR = 48              # registered /THIRD-TIME grid max (EXP-058); A4 only
POWER_FLOOR = 30                   # P14: minimum qualifying events to report
P11_MIN_CELLS, P11_MIN_INSTR = 5, 3
INVARIANT_TOL = 1e-9               # degenerate-arm reproduction tolerance
N_BOOT = 10_000                    # P14 bootstrap resamples
BOOT_BATCH = 2_000                 # bounded bootstrap memory batch
BASE_SEED = 20260616               # frozen master seed (no tuning)
EXCLUDED_FILE_MARKERS = ("analysis70", "analysis_slice", "first70")
DE30_DISCLOSURE = (
    "DE30 truncated history: broker m1 history ends 2026-01-16; counts derive "
    "from its own realized timeline and are not span-comparable (VAL-003).")
LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# Arm specification (predeclared 2x2 factorial + BENCH + horizon sibling)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ArmSpec:
    """One predeclared combined-system arm (recomposition of frozen resolvers)."""

    aid: str
    idx: int                           # stable RNG / column offset
    leg_fracs: tuple[float, ...]       # favourable distance fraction per leg
    weights: tuple[float, ...]         # leg weights (sum 1.0)
    adv_none: bool                     # True = /ADV-NONE sentinel; False = 1:1 stop
    cap: str                           # "bench" (floor=6) | "n48" (floor=48)
    is_bench: bool                     # A0: exact EXP-053 resolve_path_ordered path
    binding: bool                      # A3 champion only (operator decision 2)


_V2A = (1.0 / 3.0, 2.0 / 3.0, 1.0)
_W3 = (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)
ARMS: list[ArmSpec] = [
    ArmSpec("BENCH", 0, (1.0,), (1.0,), False, "bench", True, False),
    ArmSpec("50PCT-NONE", 1, (1.0,), (1.0,), True, "bench", False, False),
    ArmSpec("V2A-1TO1", 2, _V2A, _W3, False, "bench", False, False),
    ArmSpec("V2A-NONE", 3, _V2A, _W3, True, "bench", False, True),   # champion A3
    ArmSpec("V2A-NONE-T48", 4, _V2A, _W3, True, "n48", False, False),
]
ALL_ARM_IDS: list[str] = [a.aid for a in ARMS]
ARM_BY_ID: dict[str, ArmSpec] = {a.aid: a for a in ARMS}
CHAMPION_ID = "V2A-NONE"            # A3, the single binding G2 candidate
BENCH_ID = "BENCH"

# Factorial contrasts (disclosed, paired) — (label, variant, baseline).
FACTORIAL_PAIRS: list[tuple[str, str, str]] = [
    ("fav_main_1to1", "V2A-1TO1", "BENCH"),        # A2 - A0 (favourable under 1:1)
    ("fav_main_none", "V2A-NONE", "50PCT-NONE"),   # A3 - A1 (favourable under ADV-NONE)
    ("adv_main_50pct", "50PCT-NONE", "BENCH"),      # A1 - A0 (adverse under single leg)
    ("adv_main_v2a", "V2A-NONE", "V2A-1TO1"),       # A3 - A2 (adverse under V2A)
    ("champion_vs_bench", "V2A-NONE", "BENCH"),     # A3 - A0 (value of combined system)
    ("horizon_a4_a3", "V2A-NONE-T48", "V2A-NONE"),  # A4 - A3 (mechanism vs truncation)
]
# Interaction = (A3 - A2) - (A1 - A0) over the common 4-arm subset.
INTERACTION_ARMS = ("BENCH", "50PCT-NONE", "V2A-1TO1", "V2A-NONE")  # A0, A1, A2, A3

# RNG purpose bases (distinct deterministic streams per cell/arm/purpose).
PB_STAT, PB_HA = 1000, 2000                          # signal-arm median bootstraps
PB_RAND_DRAW, PB_RAND_BOOT, PB_MASEG = 7000, 8000, 9000  # baselines (binding stat arm)
PB_FACT, PB_INTER = 11000, 12000                     # factorial paired + interaction

# Champion per-cell status -> integer code / colour (binding readout).
VSTATUS_CODES: dict[str, int] = {
    "CHAMPION_WIN": 0, "VIABLE_NOT_BEAT": 1, "CI_SPANS_0": 2,
    "NOT_VIABLE_BY_POWER": 3, "EXCLUDED": 4,
}
VSTATUS_COLORS: list[str] = ["#1a9850", "#a6d96a", "#f46d43", "#cccccc", "#7b3294"]


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ArmResult:
    """One (arm, signal-arm) per-cell resolved population summary + returns."""

    m: int
    median: float | None
    mean: float | None
    ci_low_1s: float | None
    ci_lo_2s: float | None
    ci_hi_2s: float | None
    r_firsthit: float | None       # A0 (FAV/(FAV+ADV)); A1 (FAV/(FAV+TIMECAP)); else None
    win_rate: float | None
    data_censored: int
    exit_weights: dict[str, float]
    population: int                # built-barrier population (pre-resolution)
    block_len: int
    r_e: np.ndarray                # qualifying weighted returns in entry order
    r_e_all: np.ndarray            # full-length weighted returns (NaN off-qual)
    qual: np.ndarray               # full-length qualifying mask (for pairing)
    dist: np.ndarray               # bootstrap median distribution (may be empty)


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


def load_exp053_benchmark() -> dict[tuple[str, str], tuple[int, float | None, float | None]]:
    """Load EXP-053 per-cell stat (m, median, first-hit r) for the BENCH anchor."""
    if not EXP053_OUTCOME.exists():
        return {}
    df = pl.read_csv(EXP053_OUTCOME)
    out: dict[tuple[str, str], tuple[int, float | None, float | None]] = {}
    for row in df.iter_rows(named=True):
        med = row.get("stat_median")
        r = row.get("stat_r_firsthit")
        out[(row["instrument"], row["domain"])] = (
            int(row["stat_m"]) if row.get("stat_m") is not None else 0,
            float(med) if med is not None else None,
            float(r) if r is not None else None)
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

    Segments are bounded by *consecutive* crossovers, so the partial pre-first-
    crossover stretch is excluded by construction. Disclosed secondary baseline;
    the one missing partial segment does not affect the binding /STRONG-STAT arm.
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
# Pure computation — resolve one arm on one population -> ArmResult
# --------------------------------------------------------------------------- #
def resolve_arm(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, entry_close: np.ndarray,
    rd: np.ndarray, atr_entry: np.ndarray, arm: ArmSpec, fav_dist: np.ndarray,
    fav: np.ndarray, adv: np.ndarray, n_event: np.ndarray, population: np.ndarray,
    last_train_idx: int, rng: np.random.Generator,
) -> ArmResult:
    """Resolve one arm over ``population`` events and bootstrap the median expectancy.

    A0 (``is_bench``) reuses :func:`resolve_path_ordered` (the exact EXP-053 path);
    A1-A4 reuse :func:`resolve_legs` with the benchmark 1:1 stop or the /ADV-NONE
    sentinel (``adv = -+inf``, never binds). ``n_event`` is the per-event adaptive
    cap (floor=6 benchmark, or floor=48 for A4). No trailing, no reversal legs.
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
                          int(population.sum()), rng)


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
    rng: np.random.Generator,
) -> ArmResult:
    """Assemble an ``ArmResult`` and (if powered) bootstrap the median CI."""
    m = int(r_e.shape[0])
    dist = np.empty(0, dtype=np.float64)
    block_len = max(1, int(round(max(m, 1) ** (1.0 / 3.0))))
    median = mean = ci_low = ci_lo = ci_hi = None
    if m > 0:
        median = float(np.median(r_e))
        mean = float(np.mean(r_e))
    if m >= POWER_FLOOR:
        dist, block_len = bootstrap_median_distribution(r_e, rng, n_boot=N_BOOT, batch=BOOT_BATCH)
        ci_low, ci_lo, ci_hi = median_ci(dist)
    return ArmResult(
        m=m, median=median, mean=mean, ci_low_1s=ci_low, ci_lo_2s=ci_lo, ci_hi_2s=ci_hi,
        r_firsthit=r_firsthit, win_rate=(float((r_e > 0).mean()) if m > 0 else None),
        data_censored=censored, exit_weights=exit_w, population=population,
        block_len=block_len, r_e=r_e, r_e_all=r_all, qual=qual, dist=dist)


def _empty_arm() -> ArmResult:
    return ArmResult(0, None, None, None, None, None, None, None, 0,
                     {label: 0.0 for label in PX_CLASS_LABELS.values()}, 0, 1,
                     np.empty(0), np.empty(0), np.empty(0, dtype=bool), np.empty(0))


# --------------------------------------------------------------------------- #
# Pure computation — factorial paired contrasts + 4-series composite interaction
# --------------------------------------------------------------------------- #
def paired_contrast(
    entry_idx: np.ndarray, variant: ArmResult, base: ArmResult,
    rng: np.random.Generator,
) -> tuple[float, float, float, int]:
    """Paired median contrast ``variant - base`` on their common qualifying subset."""
    common = variant.qual & base.qual
    s_n = int(common.sum())
    if s_n == 0:
        return (float("nan"), float("nan"), float("nan"), 0)
    order = np.argsort(entry_idx[common], kind="stable")
    cl, lo, hi, _ = paired_median_contrast_ci(
        variant.r_e_all[common][order], base.r_e_all[common][order], rng,
        n_boot=N_BOOT, batch=BOOT_BATCH)
    return (cl, lo, hi, s_n)


def interaction_ci(
    entry_idx: np.ndarray, arms: dict[str, ArmResult], rng: np.random.Generator,
) -> dict[str, Any]:
    """Composite interaction ``(A3-A2)-(A1-A0)`` CI on the common 4-arm subset.

    A direct generalization of :func:`paired_median_contrast_ci` to four aligned
    series (same moving-block construction, one shared block draw per resample,
    the same median-difference statistic) — **not** a new statistical method.
    Returns the point estimate, CI bounds, and the common subset size.
    """
    a0, a1, a2, a3 = (arms[a] for a in INTERACTION_ARMS)
    common = a0.qual & a1.qual & a2.qual & a3.qual
    m = int(common.sum())
    if m == 0:
        return {"point": None, "ci_low_1s": None, "ci_lo_2s": None, "ci_hi_2s": None,
                "common_m": 0, "block_len": 1}
    order = np.argsort(entry_idx[common], kind="stable")
    r0, r1, r2, r3 = (a.r_e_all[common][order] for a in (a0, a1, a2, a3))
    point = float((np.median(r3) - np.median(r2)) - (np.median(r1) - np.median(r0)))
    b = max(1, int(round(m ** (1.0 / 3.0))))
    n_blocks = int(np.ceil(m / b))
    max_start = max(0, m - b)
    offsets = np.arange(b, dtype=np.int64)
    deltas = np.empty(N_BOOT, dtype=np.float64)
    done = 0
    while done < N_BOOT:
        k = min(BOOT_BATCH, N_BOOT - done)
        starts = rng.integers(0, max_start + 1, size=(k, n_blocks))
        idx = (starts[:, :, None] + offsets[None, None, :]).reshape(k, n_blocks * b)[:, :m]
        deltas[done:done + k] = ((np.median(r3[idx], axis=1) - np.median(r2[idx], axis=1))
                                 - (np.median(r1[idx], axis=1) - np.median(r0[idx], axis=1)))
        done += k
    return {"point": point, "ci_low_1s": float(np.percentile(deltas, 5.0)),
            "ci_lo_2s": float(np.percentile(deltas, 2.5)),
            "ci_hi_2s": float(np.percentile(deltas, 97.5)), "common_m": m, "block_len": b}


def factorial_contrasts(
    entry_idx: np.ndarray, arms: dict[str, ArmResult], cell_index: int,
) -> dict[str, Any]:
    """All disclosed paired factorial contrasts + the composite interaction."""
    out: dict[str, Any] = {}
    for off, (label, variant, base) in enumerate(FACTORIAL_PAIRS):
        out[label] = paired_contrast(entry_idx, arms[variant], arms[base],
                                     _rng(cell_index, PB_FACT + off))
    out["interaction"] = interaction_ci(entry_idx, arms, _rng(cell_index, PB_INTER))
    return out


# --------------------------------------------------------------------------- #
# Pure computation — P13 baselines (binding for the champion A3)
# --------------------------------------------------------------------------- #
def _arm_caps(arm: ArmSpec, bench_n: np.ndarray, n48: np.ndarray) -> np.ndarray:
    """Per-arm adaptive time-cap window (floor=6 for A0-A3, floor=48 for A4)."""
    return n48 if arm.cap == "n48" else bench_n


def matched_random_arm(
    ohlc: dict[str, np.ndarray], state_all: InProgressState, mv: dict[str, np.ndarray],
    warmup_all: np.ndarray, atr_all: np.ndarray, signal_idx: np.ndarray, arm: ArmSpec,
    draw_count: int, last_train_idx: int, cell_index: int,
) -> ArmResult:
    """Matched-count random control for one arm (in-progress rd; non-signal pool)."""
    n_bars = ohlc["close"].shape[0]
    eligible = (state_all.valid & (state_all.m_sofar > 0.0) & np.isfinite(atr_all)
                & (atr_all > 0.0) & (~warmup_all))
    is_signal = np.zeros(n_bars, dtype=bool)
    is_signal[signal_idx] = True
    pool = np.flatnonzero(eligible & ~is_signal)
    if draw_count <= 0 or pool.shape[0] == 0:
        return _empty_arm()
    k = min(draw_count, pool.shape[0])
    drawn = np.sort(_rng(cell_index, PB_RAND_DRAW + arm.idx).choice(pool, size=k, replace=False))
    sub = _subset_state(state_all, drawn)
    bar = benchmark_barriers(ohlc["close"][drawn], sub.rd, sub.m_sofar)
    bench_n, bench_warmup = adaptive_time_caps_by_epoch(
        ohlc["epoch"][drawn], mv["confirm_epoch"], mv["confirm_idx"])
    n48, _ = adaptive_time_caps_by_epoch(
        ohlc["epoch"][drawn], mv["confirm_epoch"], mv["confirm_idx"], floor=THIRD_TIME_FLOOR)
    pop = (sub.valid & (sub.m_sofar > 0.0) & np.isfinite(atr_all[drawn])
           & (atr_all[drawn] > 0.0) & ~bench_warmup)
    n_event = _arm_caps(arm, bench_n, n48)
    return resolve_arm(ohlc, drawn, ohlc["close"][drawn], sub.rd, atr_all[drawn], arm,
                       bar["fav_dist"], bar["fav"], bar["adv"], n_event, pop,
                       last_train_idx, _rng(cell_index, PB_RAND_BOOT + arm.idx))


def ma_seg_arm(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, entry_epoch: np.ndarray,
    entry_close: np.ndarray, atr_entry: np.ndarray, seg: dict[str, np.ndarray],
    arm: ArmSpec, last_train_idx: int, cell_index: int,
) -> ArmResult:
    """MA(20,50)-segmentation baseline for one arm through the identical pipeline."""
    if seg["confirm_epoch"].shape[0] == 0:
        return _empty_arm()
    state = live_in_progress_state(entry_epoch, entry_close, seg["confirm_epoch"],
                                   seg["end_price"], seg["end_epoch"], seg["direction"])
    bench_n, bench_warmup = adaptive_time_caps_by_epoch(
        entry_epoch, seg["confirm_epoch"], seg["confirm_idx"])
    n48, _ = adaptive_time_caps_by_epoch(
        entry_epoch, seg["confirm_epoch"], seg["confirm_idx"], floor=THIRD_TIME_FLOOR)
    buildable = (state.valid & (state.m_sofar > 0.0) & np.isfinite(atr_entry)
                 & (atr_entry > 0.0) & ~bench_warmup)
    stat = live_strong_stat(state.k, state.m_sofar, seg["magnitude"])
    bar = benchmark_barriers(entry_close, state.rd, state.m_sofar)
    pop = buildable & stat["retained_p75"]
    n_event = _arm_caps(arm, bench_n, n48)
    return resolve_arm(ohlc, entry_idx, entry_close, state.rd, atr_entry, arm,
                       bar["fav_dist"], bar["fav"], bar["adv"], n_event, pop,
                       last_train_idx, _rng(cell_index, PB_MASEG + arm.idx))


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

    ctx = _cell_context(ohlc, atr, entry_idx, entry_epoch, mv, ha_ann)
    arms = _resolve_all_arms(ctx, ohlc, last_train_idx, cell_index)
    baselines = _resolve_baselines(ctx, arms["stat"]["arms"], ohlc, mv,
                                   last_train_idx, cell_index)
    conditioned = ctx["buildable"] & ctx["stat"]["retained_p75"]
    return {
        **base, "empty": False, "arms": arms, "baselines": baselines,
        "buildable": int(ctx["buildable"].sum()), "conditioned": int(conditioned.sum()),
        "conditioned_digest": int(entry_epoch[conditioned].sum(dtype=np.int64)),
        "causality_ok": _causality_ok(ohlc, entry_idx, entry_epoch, ctx["state"], mv),
        "invariants": _cell_invariants(ctx, ohlc, last_train_idx),
    }


def _cell_context(
    ohlc: dict[str, np.ndarray], atr: np.ndarray, entry_idx: np.ndarray,
    entry_epoch: np.ndarray, mv: dict[str, np.ndarray], ha_ann: pl.DataFrame,
) -> dict[str, Any]:
    """Build the shared conditioned-signal context for a cell."""
    entry_close = ohlc["close"][entry_idx]
    state = live_in_progress_state(entry_epoch, entry_close, mv["confirm_epoch"],
                                   mv["end_price"], mv["end_epoch"], mv["direction"])
    atr_entry = atr[entry_idx]
    bench_n, bench_warmup = adaptive_time_caps_by_epoch(
        entry_epoch, mv["confirm_epoch"], mv["confirm_idx"])
    n48, warmup48 = adaptive_time_caps_by_epoch(
        entry_epoch, mv["confirm_epoch"], mv["confirm_idx"], floor=THIRD_TIME_FLOOR)
    buildable = (state.valid & (state.m_sofar > 0.0) & np.isfinite(atr_entry)
                 & (atr_entry > 0.0) & ~bench_warmup)
    stat = live_strong_stat(state.k, state.m_sofar, mv["magnitude"])
    ha_same = strong_ha_retention(ha_ann, entry_epoch, state.start_epoch, -state.rd,
                                  state.valid)
    bar = benchmark_barriers(entry_close, state.rd, state.m_sofar)
    return {
        "entry_idx": entry_idx, "entry_epoch": entry_epoch, "entry_close": entry_close,
        "state": state, "atr": atr, "atr_entry": atr_entry, "bench_n": bench_n,
        "bench_warmup": bench_warmup, "n48": n48, "warmup48": warmup48,
        "buildable": buildable, "stat": stat, "ha_same": ha_same,
        "fav_dist": bar["fav_dist"], "fav": bar["fav"], "adv": bar["adv"],
    }


def _resolve_all_arms(
    ctx: dict[str, Any], ohlc: dict[str, np.ndarray], last_train_idx: int,
    cell_index: int,
) -> dict[str, dict[str, Any]]:
    """Resolve every arm on the binding (stat) + disclosed (ha) signal arms."""
    def resolve(mask: np.ndarray, a: ArmSpec, pb: int) -> ArmResult:
        pop = ctx["buildable"] & mask
        n_event = ctx["n48"] if a.cap == "n48" else ctx["bench_n"]
        return resolve_arm(ohlc, ctx["entry_idx"], ctx["entry_close"], ctx["state"].rd,
                           ctx["atr_entry"], a, ctx["fav_dist"], ctx["fav"], ctx["adv"],
                           n_event, pop, last_train_idx, _rng(cell_index, pb + a.idx))

    # Binding /STRONG-STAT arm carries the full factorial (incl. the interaction
    # bootstrap); the disclosed /STRONG-HA arm needs only per-arm medians (the
    # scope discloses HA per-arm, never its factorial), so skip its bootstrap.
    stat_res = {a.aid: resolve(ctx["stat"]["retained_p75"], a, PB_STAT) for a in ARMS}
    ha_res = {a.aid: resolve(ctx["ha_same"], a, PB_HA) for a in ARMS}
    return {
        "stat": {"arms": stat_res,
                 "factorial": factorial_contrasts(ctx["entry_idx"], stat_res, cell_index)},
        "ha": {"arms": ha_res},
    }


def _resolve_baselines(
    ctx: dict[str, Any], stat_arms: dict[str, ArmResult], ohlc: dict[str, np.ndarray],
    mv: dict[str, np.ndarray], last_train_idx: int, cell_index: int,
) -> dict[str, dict[str, Any]]:
    """P13 matched-random + MA-seg baselines per arm (binding stat arm)."""
    state_all = live_in_progress_state(ohlc["epoch"], ohlc["close"], mv["confirm_epoch"],
                                       mv["end_price"], mv["end_epoch"], mv["direction"])
    _, warmup_all = adaptive_time_caps_by_epoch(
        ohlc["epoch"], mv["confirm_epoch"], mv["confirm_idx"])
    seg = ma_segment_moves(ohlc)
    signal_idx = ctx["entry_idx"][ctx["stat"]["retained_p75"]]
    out: dict[str, dict[str, Any]] = {}
    for a in ARMS:
        draw = stat_arms[a.aid].m                      # matched-count = arm's stat qual m
        rand = matched_random_arm(ohlc, state_all, mv, warmup_all, ctx["atr"], signal_idx,
                                  a, draw, last_train_idx, cell_index)
        ma = ma_seg_arm(ohlc, ctx["entry_idx"], ctx["entry_epoch"], ctx["entry_close"],
                        ctx["atr_entry"], seg, a, last_train_idx, cell_index)
        out[a.aid] = {"matched_random": rand, "ma_seg": ma}
    return out


# --------------------------------------------------------------------------- #
# Per-cell causality / invariant gate
# --------------------------------------------------------------------------- #
def _causality_ok(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, entry_epoch: np.ndarray,
    state: InProgressState, mv: dict[str, np.ndarray],
) -> bool:
    """Runtime causality checks: strict grid, causal reference move, entry <= t_i."""
    epoch = ohlc["epoch"]
    if epoch.shape[0] >= 2 and not bool(np.all(np.diff(epoch) > 0)):
        return False                                   # duplicate/disordered CloseTime
    valid = state.valid & (state.k >= 0)
    if valid.any():
        kk = state.k[valid]
        if not bool(np.all(mv["end_epoch"][kk] <= entry_epoch[valid])):
            return False                               # reference move ends at/before entry
        if not bool(np.all(epoch[entry_idx[valid]] <= entry_epoch[valid])):
            return False                               # entry bar is itself (<= t_i)
    return True


def _cell_invariants(
    ctx: dict[str, Any], ohlc: dict[str, np.ndarray], last_train_idx: int,
) -> dict[str, bool]:
    """Predeclared combined-system invariants (analysis-plan Step 11 (iii)-(vii))."""
    cond = ctx["buildable"] & ctx["stat"]["retained_p75"]
    o, h, lo, c = ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"]
    ei, ec, rd = ctx["entry_idx"], ctx["entry_close"], ctx["state"].rd
    fav, adv, bench_n = ctx["fav"], ctx["adv"], ctx["bench_n"]
    no_rev = np.full(int(ei.shape[0]), -1, dtype=np.int64)
    w1, w3 = np.array([1.0]), np.asarray(_W3)
    weights_ok = all(abs(sum(a.weights) - 1.0) <= 1e-12 for a in ARMS)
    # BENCH reference returns via resolve_path_ordered (the EXP-053 method).
    bcl, bpx = resolve_path_ordered(o, h, lo, c, ei, fav, adv, rd, bench_n, cond,
                                    int(c.shape[0]))
    bench_r = realised_returns(bcl, bpx, ec, rd, ctx["atr_entry"])
    bench_q = cond & qualifying_mask(bcl, bpx, ctx["atr_entry"])
    # (iii.a) single-leg LEVEL@fav fixed adv reproduces resolve_path_ordered BENCH.
    lvl1 = leg_levels_from_fracs(ec, rd, ctx["fav_dist"], (1.0,))
    px1, cls1 = resolve_legs(o, h, lo, c, ei, ec, rd, (LEG_LEVEL,), lvl1, no_rev, adv,
                             bench_n, cond, ADV_FIXED, None, last_train_idx)
    r1, q1 = weighted_returns(px1, cls1, w1, ec, rd, ctx["atr_entry"], cond)
    single_match = _arr_match(bench_r, bench_q, r1, q1)
    # (iii.b) degenerate 3-leg all-LEVEL@fav reproduces the single-leg R_event.
    lvl3 = leg_levels_from_fracs(ec, rd, ctx["fav_dist"], (1.0, 1.0, 1.0))
    px3, cls3 = resolve_legs(o, h, lo, c, ei, ec, rd, (LEG_LEVEL, LEG_LEVEL, LEG_LEVEL),
                             lvl3, no_rev, adv, bench_n, cond, ADV_FIXED, None, last_train_idx)
    r3, q3 = weighted_returns(px3, cls3, w3, ec, rd, ctx["atr_entry"], cond)
    degenerate_match = _arr_match(bench_r, bench_q, r3, q3)
    # (vi) shared 1:1 stop closes all still-open legs at one level (V2A x1:1 geometry).
    lvl_a = leg_levels_from_fracs(ec, rd, ctx["fav_dist"], _V2A)
    px_a, cls_a = resolve_legs(o, h, lo, c, ei, ec, rd, (LEG_LEVEL, LEG_LEVEL, LEG_LEVEL),
                               lvl_a, no_rev, adv, bench_n, cond, ADV_FIXED, None, last_train_idx)
    shared_ok = _shared_stop_ok(cls_a, px_a, adv, cond)
    # (iv) ADV-NONE never fires an adverse exit on the champion A3 geometry.
    adv_none = adverse_none_sentinel(ec, rd, ctx["fav_dist"])["adv"]
    _, cls_n = resolve_legs(o, h, lo, c, ei, ec, rd, (LEG_LEVEL, LEG_LEVEL, LEG_LEVEL),
                            lvl_a, no_rev, adv_none, bench_n, cond, ADV_FIXED, None,
                            last_train_idx)
    adv_none_ok = bool(not (cls_n == PX_ADV).any())
    # (vii) A4 differs from A3 only by the cap: N48 >= bench_N (population), warmup equal.
    cap_ok = (bool(np.all(ctx["n48"][cond] >= bench_n[cond]))
              and bool(np.array_equal(ctx["warmup48"], ctx["bench_warmup"])))
    return {"weights_sum_ok": bool(weights_ok), "single_leg_match": bool(single_match),
            "degenerate_match": bool(degenerate_match), "shared_stop_ok": bool(shared_ok),
            "adv_none_no_stop": adv_none_ok, "a4_cap_dominates": cap_ok}


def _arr_match(ra: np.ndarray, qa: np.ndarray, rb: np.ndarray, qb: np.ndarray) -> bool:
    """Two (returns, qualifying) pairs agree on the common qualifying subset + mask."""
    if not bool(np.array_equal(qa, qb)):
        return False
    common = qa & qb
    if not common.any():
        return True
    return bool(np.allclose(ra[common], rb[common], atol=INVARIANT_TOL))


def _shared_stop_ok(
    cls: np.ndarray, px: np.ndarray, adv: np.ndarray, cond: np.ndarray,
) -> bool:
    """Every leg that exits via the shared 1:1 stop does so at the benchmark adv level."""
    has_adv = (cls == PX_ADV).any(axis=1) & cond
    for e in np.flatnonzero(has_adv):
        legs = cls[e] == PX_ADV
        if not bool(np.allclose(px[e][legs], adv[e], atol=1e-9)):
            return False
    return True


def a4_subset_ok(cell: dict[str, Any]) -> bool:
    """Invariant (vii): A4 qualifying set is a subset of A3's (longer window censors more)."""
    a3 = cell["arms"]["stat"]["arms"][CHAMPION_ID]
    a4 = cell["arms"]["stat"]["arms"]["V2A-NONE-T48"]
    if a4.qual.shape[0] != a3.qual.shape[0]:
        return False
    return bool(np.all(a3.qual[a4.qual]))


# --------------------------------------------------------------------------- #
# Per-cell record flattening + champion classification
# --------------------------------------------------------------------------- #
def cell_arm_records(instrument: str, cell: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten one cell into per-arm binding (stat) records."""
    domain = cell["domain"]
    fields = {"instrument": instrument, "domain": domain, "member": True,
              "excluded": False, "n_bars": cell["n_bars"], "n_moves": cell["n_moves"],
              "n_harami": cell["n_harami"]}
    if cell.get("empty", False):
        return [{**fields, "arm": a.aid, **_empty_arm_fields()} for a in ARMS]
    fields.update({"n_buildable": cell["buildable"], "n_conditioned": cell["conditioned"]})
    return [{**fields, "arm": a.aid, **_arm_record(cell, a)} for a in ARMS]


def _arm_record(cell: dict[str, Any], a: ArmSpec) -> dict[str, Any]:
    """Per (cell, arm) metric + baseline + classification."""
    sig = cell["arms"]["stat"]["arms"][a.aid]
    bl = cell["baselines"][a.aid]
    rec: dict[str, Any] = _arm_fields(sig)
    rec["retained_fraction"] = (sig.m / cell["conditioned"]) if cell["conditioned"] else None
    rec.update(_baseline_fields(bl["matched_random"], "rand"))
    rec.update(_baseline_fields(bl["ma_seg"], "maseg"))
    rec["contrast_random_low"] = contrast_ci(sig.dist, bl["matched_random"].dist)[0]
    rec["contrast_ma_low"] = contrast_ci(sig.dist, bl["ma_seg"].dist)[0]
    _classify_arm(rec, sig, a)
    return rec


def _classify_arm(rec: dict[str, Any], sig: ArmResult, a: ArmSpec) -> None:
    """Per (cell, arm) powered/viable + (for the champion A3) the two-baseline win."""
    viable = (sig.m >= POWER_FLOOR and sig.ci_low_1s is not None
              and np.isfinite(sig.ci_low_1s) and sig.ci_low_1s > 0.0)
    cr, cm = rec["contrast_random_low"], rec["contrast_ma_low"]
    beats_random = cr is not None and np.isfinite(cr) and cr > 0.0
    beats_ma = cm is not None and np.isfinite(cm) and cm > 0.0
    champion_win = bool(a.binding and viable and beats_random and beats_ma)
    rec["powered"] = sig.m >= POWER_FLOOR
    rec["viable"] = bool(viable)
    rec["beats_random"] = bool(beats_random)
    rec["beats_ma"] = bool(beats_ma)
    rec["beats_both"] = bool(beats_random and beats_ma)
    rec["champion_win"] = champion_win
    rec["binding"] = a.binding
    if not a.binding:
        status = "VIABLE_NOT_BEAT" if viable else (
            "NOT_VIABLE_BY_POWER" if not rec["powered"] else "CI_SPANS_0")
    elif champion_win:
        status = "CHAMPION_WIN"
    elif viable:
        status = "VIABLE_NOT_BEAT"
    elif not rec["powered"]:
        status = "NOT_VIABLE_BY_POWER"
    else:
        status = "CI_SPANS_0"
    rec["viable_status"], rec["status_code"] = status, VSTATUS_CODES[status]


def _arm_fields(a: ArmResult) -> dict[str, Any]:
    """Flatten an ArmResult's scalar metrics + exit-reason weights (no arrays)."""
    out = {
        "m": a.m, "median": a.median, "mean": a.mean, "ci_low_1s": a.ci_low_1s,
        "ci_lo_2s": a.ci_lo_2s, "ci_hi_2s": a.ci_hi_2s, "r_firsthit": a.r_firsthit,
        "win_rate": a.win_rate, "data_censored": a.data_censored,
        "population": a.population, "block_len": a.block_len,
    }
    out.update({f"ew_{label}": a.exit_weights[label] for label in PX_CLASS_LABELS.values()})
    return out


def _baseline_fields(a: ArmResult, prefix: str) -> dict[str, Any]:
    """Compact baseline columns (m / median / one-sided CI_low)."""
    return {f"{prefix}_m": a.m, f"{prefix}_median": a.median,
            f"{prefix}_ci_low_1s": a.ci_low_1s}


def _empty_arm_fields() -> dict[str, Any]:
    rec = {"n_buildable": 0, "n_conditioned": 0, "retained_fraction": None,
           "contrast_random_low": None, "contrast_ma_low": None,
           "powered": False, "viable": False, "beats_random": False, "beats_ma": False,
           "beats_both": False, "champion_win": False, "binding": False,
           "viable_status": "NOT_VIABLE_BY_POWER",
           "status_code": VSTATUS_CODES["NOT_VIABLE_BY_POWER"]}
    rec.update(_arm_fields(_empty_arm()))
    rec.update(_baseline_fields(_empty_arm(), "rand"))
    rec.update(_baseline_fields(_empty_arm(), "maseg"))
    return rec


def excluded_records(instrument: str, domain: str) -> list[dict[str, Any]]:
    """COVERAGE_EXCLUDED cell records (one per arm)."""
    out = []
    for a in ARMS:
        rec = {"instrument": instrument, "domain": domain, "member": False, "excluded": True,
               "arm": a.aid, "n_bars": None, "n_moves": None, "n_harami": None}
        rec.update(_empty_arm_fields())
        rec["viable_status"], rec["status_code"] = "EXCLUDED", VSTATUS_CODES["EXCLUDED"]
        out.append(rec)
    return out


def factorial_records(instrument: str, cell: dict[str, Any]) -> list[dict[str, Any]]:
    """Per-cell factorial contrast rows (stat arm; disclosed)."""
    if cell.get("empty", False):
        return []
    fac = cell["arms"]["stat"]["factorial"]
    rows = []
    for label, _, _ in FACTORIAL_PAIRS:
        cl, lo, hi, sn = fac[label]
        rows.append({"instrument": instrument, "domain": cell["domain"], "contrast": label,
                     "ci_low_1s": cl, "ci_lo_2s": lo, "ci_hi_2s": hi, "common_m": sn,
                     "point": None})
    it = fac["interaction"]
    rows.append({"instrument": instrument, "domain": cell["domain"], "contrast": "interaction",
                 "ci_low_1s": it["ci_low_1s"], "ci_lo_2s": it["ci_lo_2s"],
                 "ci_hi_2s": it["ci_hi_2s"], "common_m": it["common_m"], "point": it["point"]})
    return rows


def secondary_records(instrument: str, cell: dict[str, Any]) -> list[dict[str, Any]]:
    """Disclosed /STRONG-HA rows per arm (the disclosed conditioning arm)."""
    if cell.get("empty", False):
        return []
    rows = []
    for a in ARMS:
        res = cell["arms"]["ha"]["arms"][a.aid]
        rows.append({"instrument": instrument, "domain": cell["domain"], "signal": "ha",
                     "arm": a.aid, "m": res.m, "median": res.median,
                     "ci_low_1s": res.ci_low_1s, "ci_lo_2s": res.ci_lo_2s,
                     "ci_hi_2s": res.ci_hi_2s, "r_firsthit": res.r_firsthit,
                     "win_rate": res.win_rate, "data_censored": res.data_censored})
    return rows


# --------------------------------------------------------------------------- #
# Composition + champion eligibility readout
# --------------------------------------------------------------------------- #
def composition_readout(records: list[dict[str, Any]], defect: dict[str, Any]) -> dict[str, Any]:
    """P11 composition for the champion A3 + the mechanical eligibility verdict."""
    members = [r for r in records if r["member"]]
    champ = [r for r in members if r["arm"] == CHAMPION_ID]
    powered = _tally([r for r in champ if r["powered"]])
    viable = _tally([r for r in champ if r["viable"]], with_cells=True)
    wins = _win_tally([r for r in champ if r["champion_win"]])
    verdict = _eligibility_label(defect, powered, wins)
    return {
        "verdict": verdict, "champion": CHAMPION_ID,
        "champion_powered": powered, "champion_viable": viable, "champion_wins": wins,
        "defect": defect,
        "rule": ("champion A3 (V2A x ADV-NONE) is the single binding G2 candidate. Per cell: "
                 "VIABLE iff median CI_low(1s)>0 AND m>=30; CHAMPION_WIN iff VIABLE AND "
                 "A3-matched-random CI_low(1s)>0 AND A3-MA(20,50) CI_low(1s)>0 (two-baseline "
                 "IUT conjunction). PROCEED_TO_SCREEN-eligible iff champion wins compose P11 "
                 "(>=5 cells over >=3 instruments). A0/A1/A2/A4 + factorial = disclosed, "
                 "non-binding. EXP-060 emits the eligibility readout; the operator adjudicates "
                 "the single 014-B G2 (no closure or candidate registration here)."),
        "multiplicity": ("one pre-registered binding definition (A3); P11 composition controls "
                         "across-cell risk (no per-cell Holm, frozen programme convention); the "
                         "two-baseline conjunction is a conservative IUT (size <= alpha). Zero "
                         "formal corrections applied; the full-surface FWER posture is the "
                         "single 014-B G2 desk adjudication."),
        "exit_reason_note": ("exit-reason composition (weight fraction via each V2A leg / the 1:1 "
                             "stop / the time cap) is the binding-disclosed mechanism diagnostic; "
                             "it never enters the verdict."),
    }


def _tally(rows: list[dict[str, Any]], with_cells: bool = False) -> dict[str, Any]:
    n_cells = len(rows)
    instruments = {r["instrument"] for r in rows}
    out = {"n_cells": n_cells, "n_instruments": len(instruments),
           "composition_met": n_cells >= P11_MIN_CELLS and len(instruments) >= P11_MIN_INSTR}
    if with_cells:
        out["cells"] = [f"{r['instrument']}-{r['domain']}" for r in rows]
    return out


def _win_tally(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n_cells = len(rows)
    instruments = {r["instrument"] for r in rows}
    passes = n_cells >= P11_MIN_CELLS and len(instruments) >= P11_MIN_INSTR
    return {"n_cells": n_cells, "n_instruments": len(instruments),
            "cells": [f"{r['instrument']}-{r['domain']}" for r in rows], "passes": passes,
            "fragile": passes and (n_cells == P11_MIN_CELLS or len(instruments) == P11_MIN_INSTR)}


def _eligibility_label(
    defect: dict[str, Any], powered: dict[str, Any], wins: dict[str, Any],
) -> str:
    """Mechanical champion eligibility per the analysis-plan Interpretation Guide."""
    if defect["is_defect"]:
        return "SUBSTRATE_METHOD_DEFECT"
    if wins["passes"]:
        return "PROCEED_TO_SCREEN_ELIGIBLE"
    if powered["composition_met"]:
        return "CHARACTERISED_NOT_VIABLE_ELIGIBLE"
    return "INCONCLUSIVE_POWER_LIMITED"


# --------------------------------------------------------------------------- #
# Determinism replay + reconciliation anchors (DEFECT guards)
# --------------------------------------------------------------------------- #
def determinism_replay(train_1m: pl.DataFrame, domain: str, train_end_epoch: int,
                       cell_index: int) -> bool:
    """Re-run one cell end-to-end and assert byte-identical binding outputs."""
    a = compute_cell(train_1m, domain, train_end_epoch, cell_index)
    b = compute_cell(train_1m, domain, train_end_epoch, cell_index)
    if a.get("empty") or b.get("empty"):
        return a.get("empty") == b.get("empty")
    for aid in ALL_ARM_IDS:
        sa, sb = a["arms"]["stat"]["arms"][aid], b["arms"]["stat"]["arms"][aid]
        if not (np.array_equal(sa.r_e, sb.r_e)
                and (sa.median, sa.ci_low_1s) == (sb.median, sb.ci_low_1s)):
            return False
        for bl in ("matched_random", "ma_seg"):
            if not np.array_equal(a["baselines"][aid][bl].r_e,
                                  b["baselines"][aid][bl].r_e):
                return False
    fa = a["arms"]["stat"]["factorial"]["interaction"]
    fb = b["arms"]["stat"]["factorial"]["interaction"]
    return fa["point"] == fb["point"] and fa["ci_low_1s"] == fb["ci_low_1s"]


def exp053_reconciliation(
    instrument: str, cell: dict[str, Any],
    exp053: dict[tuple[str, str], tuple[int, float | None, float | None]],
) -> dict[str, Any]:
    """Cross-check the BENCH stat arm against EXP-053's recorded benchmark (invariants i+ii)."""
    key = (instrument, cell["domain"])
    if not exp053 or key not in exp053 or cell.get("empty"):
        return {"checked": False, "cell": f"{instrument}-{cell.get('domain')}"}
    sig = cell["arms"]["stat"]["arms"][BENCH_ID]
    exp_m, exp_med, exp_r = exp053[key]
    m_match = sig.m == exp_m
    med_match = (sig.median is None and exp_med is None) or (
        sig.median is not None and exp_med is not None and abs(sig.median - exp_med) <= 1e-9)
    r_match = (sig.r_firsthit is None and exp_r is None) or (
        sig.r_firsthit is not None and exp_r is not None
        and abs(sig.r_firsthit - exp_r) <= 1e-9)
    return {"checked": True, "cell": f"{instrument}-{cell['domain']}", "bench_m": sig.m,
            "exp053_m": exp_m, "bench_median": sig.median, "exp053_median": exp_med,
            "bench_r_firsthit": sig.r_firsthit, "exp053_r_firsthit": exp_r,
            "m_match": bool(m_match), "median_match": bool(med_match), "r_match": bool(r_match),
            "consistent": bool(m_match and med_match and r_match)}


# --------------------------------------------------------------------------- #
# Plotting (bounded; from collected summaries + pooled per-event sample)
# --------------------------------------------------------------------------- #
def _cell_label(r: dict[str, Any]) -> str:
    return f"{r['instrument']}-{r['domain']}"


def _ordered_cells(records: list[dict[str, Any]], include_excluded: bool = False) -> list[str]:
    seen: list[str] = []
    for r in records:
        if not include_excluded and not r["member"]:
            continue
        label = _cell_label(r)
        if label not in seen:
            seen.append(label)
    return seen


def _placeholder(ax: plt.Axes, message: str) -> None:
    ax.text(0.5, 0.5, message, ha="center", va="center")
    ax.axis("off")


def plot_arm_forest(records: list[dict[str, Any]], save_path: Path) -> None:
    """Per-arm per-cell median expectancy with one-sided CI_low whisker (5 panels)."""
    fig, axes = plt.subplots(2, 3, figsize=(17, 11), sharex=True)
    flat = axes.ravel()
    for ax, a in zip(flat, ARMS):
        rows = sorted([r for r in records if r["arm"] == a.aid and r["member"]
                       and r["median"] is not None], key=lambda r: r["median"])
        if not rows:
            _placeholder(ax, "no powered cells")
            ax.set_title(a.aid, fontsize=9)
            continue
        med = np.array([r["median"] for r in rows])
        low = np.array([r["ci_low_1s"] if r["ci_low_1s"] is not None else np.nan for r in rows])
        y = np.arange(len(rows))
        colours = ["#1a9850" if r["champion_win"] else ("#a6d96a" if r["viable"] else "#999999")
                   for r in rows]
        ax.scatter(med, y, color=colours, s=12, zorder=3)
        ax.hlines(y, np.minimum(low, med), med, color=colours, alpha=0.6, zorder=2)
        ax.axvline(0.0, color="k", lw=0.7, ls="--")
        ax.set_yticks(y, [_cell_label(r) for r in rows], fontsize=3)
        title = f"{a.aid}{' (CHAMPION)' if a.binding else ''}"
        ax.set_title(title, fontsize=9)
    for ax in flat[len(ARMS):]:
        ax.axis("off")
    fig.suptitle(f"{EXPERIMENT_ID}: per-cell median expectancy by arm (binding /STRONG-STAT)")
    fig.supxlabel("median gross position-weighted expectancy (ATR units)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_factorial(records: list[dict[str, Any]], factorial: list[dict[str, Any]],
                   save_path: Path) -> None:
    """2x2 factorial decomposition: pooled main-effect/interaction bars + per-cell heatmap."""
    labels = [lbl for lbl, _, _ in FACTORIAL_PAIRS] + ["interaction"]
    by_cell: dict[tuple[str, str], dict[str, float]] = {}
    for row in factorial:
        by_cell.setdefault((row["instrument"], row["domain"]), {})[row["contrast"]] = \
            row["ci_low_1s"]
    cells = list(by_cell)
    matrix = np.full((len(labels), len(cells)), np.nan)
    for j, key in enumerate(cells):
        for i, lbl in enumerate(labels):
            v = by_cell[key].get(lbl)
            if v is not None and np.isfinite(v):
                matrix[i, j] = v
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(max(9, 0.16 * max(len(cells), 1)), 10))
    pooled = [np.nanmedian(matrix[i]) if np.isfinite(matrix[i]).any() else 0.0
              for i in range(len(labels))]
    x = np.arange(len(labels))
    ax1.bar(x, pooled, color="#4575b4")
    ax1.axhline(0.0, color="k", lw=0.8, ls="--")
    ax1.set_xticks(x, labels, rotation=30, fontsize=7, ha="right")
    ax1.set_ylabel("median CI_low(1s) over cells (ATR units)")
    ax1.set_title("pooled factorial contrasts (median of per-cell paired CI_low)")
    vmax = np.nanmax(np.abs(matrix)) if np.isfinite(matrix).any() else 1.0
    im = ax2.imshow(matrix, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")
    ax2.set_yticks(range(len(labels)), labels, fontsize=7)
    ax2.set_xticks(range(len(cells)), [f"{i}-{d}" for i, d in cells], rotation=90, fontsize=3)
    ax2.set_title("per-cell paired contrast CI_low (favourable / adverse main effects + "
                  "interaction + vs-BENCH + horizon)")
    fig.colorbar(im, ax=ax2, label="CI_low(delta) (ATR units)")
    fig.suptitle(f"{EXPERIMENT_ID}: 2x2 favourable x adverse factorial decomposition")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_champion_binding(records: list[dict[str, Any]], save_path: Path) -> None:
    """Champion A3 binding read: per-cell E_cell CI vs 0 + both baseline contrasts + win map."""
    champ = sorted([r for r in records if r["arm"] == CHAMPION_ID and r["member"]
                    and r["median"] is not None], key=lambda r: r["median"])
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(max(9, 0.18 * max(len(champ), 1)), 10))
    if not champ:
        _placeholder(ax1, "no powered champion cells")
        _placeholder(ax2, "no powered champion cells")
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return
    labels = [_cell_label(r) for r in champ]
    x = np.arange(len(champ))
    med = np.array([r["median"] for r in champ])
    elow = np.array([r["ci_low_1s"] if r["ci_low_1s"] is not None else np.nan for r in champ])
    cr = np.array([r["contrast_random_low"] if r["contrast_random_low"] is not None
                   else np.nan for r in champ])
    cm = np.array([r["contrast_ma_low"] if r["contrast_ma_low"] is not None
                   else np.nan for r in champ])
    colours = ["#1a9850" if r["champion_win"] else "#999999" for r in champ]
    ax1.scatter(x, med, color=colours, s=14, zorder=3, label="median E_cell")
    ax1.vlines(x, np.minimum(elow, med), med, color=colours, alpha=0.6)
    ax1.axhline(0.0, color="k", lw=0.8, ls="--")
    ax1.set_xticks(x, labels, rotation=90, fontsize=3)
    ax1.set_ylabel("median expectancy (ATR units)")
    ax1.set_title("champion A3 per-cell median E_cell + one-sided CI_low (green = CHAMPION_WIN)")
    ax2.plot(x, cr, "o-", ms=3, color="#d73027", label="A3 - matched-random CI_low")
    ax2.plot(x, cm, "s-", ms=3, color="#4575b4", label="A3 - MA(20,50) CI_low")
    ax2.axhline(0.0, color="k", lw=0.8, ls="--")
    ax2.set_xticks(x, labels, rotation=90, fontsize=3)
    ax2.set_ylabel("paired/independent contrast CI_low (ATR units)")
    ax2.set_title("champion A3 vs both P13 baselines (binding: both CI_low>0 for a win)")
    ax2.legend(fontsize=8)
    fig.suptitle(f"{EXPERIMENT_ID}: champion A3 binding read (the single 014-B G2 input)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_exit_reasons(records: list[dict[str, Any]], save_path: Path) -> None:
    """Per-arm pooled exit-reason weight composition (stacked) + median qualifying count."""
    labels = ["FAV", "ADV", "TIMECAP", "DATA_CENSORED"]
    colours = {"DATA_CENSORED": "#cccccc", "TIMECAP": "#fdae61", "ADV": "#d73027",
               "FAV": "#1a9850"}
    arms = [a.aid for a in ARMS]
    comp = np.zeros((len(arms), len(labels)))
    med_m = np.zeros(len(arms))
    for i, aid in enumerate(arms):
        rows = [r for r in records if r["arm"] == aid and r["member"] and r["m"] > 0]
        if rows:
            for k, lab in enumerate(labels):
                comp[i, k] = float(np.mean([r[f"ew_{lab}"] for r in rows]))
            med_m[i] = float(np.median([r["m"] for r in rows]))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), gridspec_kw={"width_ratios": [3, 1]})
    bottom = np.zeros(len(arms))
    x = np.arange(len(arms))
    for k, lab in enumerate(labels):
        ax1.bar(x, comp[:, k], bottom=bottom, label=lab, color=colours[lab])
        bottom += comp[:, k]
    ax1.set_xticks(x, arms, rotation=30, fontsize=8, ha="right")
    ax1.set_ylabel("mean weight fraction (qualifying events)")
    ax1.set_title("exit-reason composition by arm (mechanism diagnostic)")
    ax1.legend(fontsize=8)
    ax2.barh(x, med_m, color="#4575b4")
    ax2.axvline(POWER_FLOOR, color="k", lw=0.9, ls="--", label=f"power floor={POWER_FLOOR}")
    ax2.set_yticks(x, arms, fontsize=8)
    ax2.set_xlabel("median per-cell qualifying events")
    ax2.set_title("per-cell power by arm")
    ax2.legend(fontsize=8)
    fig.suptitle(f"{EXPERIMENT_ID}: exit-reason composition + per-arm power")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_horizon(records: list[dict[str, Any]], factorial: list[dict[str, Any]],
                 save_path: Path) -> None:
    """Horizon sensitivity A4-A3 per cell alongside each arm's cap-exit weight."""
    horizon = {(r["instrument"], r["domain"]): r["ci_low_1s"] for r in factorial
               if r["contrast"] == "horizon_a4_a3"}
    cells = list(horizon)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(max(9, 0.18 * max(len(cells), 1)), 9))
    if cells:
        vals = np.array([horizon[c] if horizon[c] is not None and np.isfinite(horizon[c])
                         else np.nan for c in cells])
        x = np.arange(len(cells))
        ax1.bar(x, vals, color="#762a83")
        ax1.axhline(0.0, color="k", lw=0.8, ls="--")
        ax1.set_xticks(x, [f"{i}-{d}" for i, d in cells], rotation=90, fontsize=3)
        ax1.set_ylabel("A4 - A3 paired CI_low (ATR units)")
        ax1.set_title("horizon sensitivity: champion at floor=48 vs floor=6 (per cell)")
    else:
        _placeholder(ax1, "no horizon contrasts")
    cap_w = {"V2A-NONE": [], "V2A-NONE-T48": []}
    for aid in cap_w:
        cap_w[aid] = [r["ew_TIMECAP"] for r in records
                      if r["arm"] == aid and r["member"] and r["m"] > 0]
    ax2.boxplot([cap_w["V2A-NONE"] or [0.0], cap_w["V2A-NONE-T48"] or [0.0]],
                positions=[1, 2])
    ax2.set_xticks([1, 2], ["A3 (floor=6)", "A4 (floor=48)"])
    ax2.set_ylabel("per-cell time-cap exit weight fraction")
    ax2.set_title("cap-exit weight: A3 vs A4 (mechanism vs horizon-truncation)")
    fig.suptitle(f"{EXPERIMENT_ID}: horizon-sensitivity disclosed sibling (A4)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def make_plots(records: list[dict[str, Any]], factorial: list[dict[str, Any]]) -> None:
    """Render the five bounded plots from collected summaries."""
    plot_arm_forest(records, PLOTS_DIR / "per_arm_median_forest.png")
    plot_factorial(records, factorial, PLOTS_DIR / "factorial_decomposition.png")
    plot_champion_binding(records, PLOTS_DIR / "champion_binding_map.png")
    plot_exit_reasons(records, PLOTS_DIR / "exit_reason_composition.png")
    plot_horizon(records, factorial, PLOTS_DIR / "horizon_sensitivity.png")


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _cell_index_map() -> dict[tuple[str, str], int]:
    return {(inst, dom): i for i, (inst, dom) in enumerate(
        (inst, dom) for inst in INSTRUMENTS for dom in DOMAINS)}


def process_instrument(
    instrument: str, exp053: dict[tuple[str, str], tuple[int, float | None, float | None]],
) -> dict[str, Any]:
    """Worker: resolve every member cell of one instrument (the parallel unit).

    Self-contained and pure given identical inputs/seeds: each cell's RNG is seeded by
    ``(BASE_SEED, cell_index, purpose)`` (order-independent), so the per-instrument
    result is identical regardless of how many workers run or in what order they finish.
    Returns the instrument's record/factorial/secondary/champion/reconciliation rows,
    its TRAIN meta, and its defect fragments — the parent merges these in ``INSTRUMENTS``
    order so the assembled outputs are byte-identical to a single-worker run.
    """
    cell_index = _cell_index_map()
    out: dict[str, Any] = {
        "records": [], "factorial": [], "secondaries": [], "champ_rows": [],
        "recon_rows": [], "meta": None, "causality_violations": [],
        "invariant_violations": [], "determinism_checked": [], "non_deterministic": []}
    members = [d for d in DOMAINS if (instrument, d) not in EXCLUDED_CELLS]
    if not members:
        for domain in DOMAINS:
            out["records"].extend(excluded_records(instrument, domain))
        return out
    train_1m, meta = load_train_1m(instrument)
    out["meta"] = meta
    replayed = False
    for domain in DOMAINS:
        if (instrument, domain) in EXCLUDED_CELLS:
            out["records"].extend(excluded_records(instrument, domain))
            continue
        ci = cell_index[(instrument, domain)]
        cell = compute_cell(train_1m, domain, meta["train_end_epoch_s"], ci)
        car = cell_arm_records(instrument, cell)
        out["records"].extend(car)
        out["factorial"].extend(factorial_records(instrument, cell))
        out["secondaries"].extend(secondary_records(instrument, cell))
        out["champ_rows"].append(_champion_row(instrument, cell, car))
        out["recon_rows"].append(exp053_reconciliation(instrument, cell, exp053))
        _record_cell_defects(cell, instrument, domain, out)
        if not replayed and not cell.get("empty") \
                and cell["arms"]["stat"]["arms"][BENCH_ID].m > 0:
            ok = determinism_replay(train_1m, domain, meta["train_end_epoch_s"], ci)
            out["determinism_checked"].append(f"{instrument}-{domain}#{ci}")
            if not ok:
                out["non_deterministic"].append(f"{instrument}-{domain}#{ci}")
            replayed = True
        del cell
    del train_1m
    return out


def _run_grid(
    exp053: dict[tuple[str, str], tuple[int, float | None, float | None]], workers: int,
) -> list[dict[str, Any]]:
    """Resolve all instruments (process pool if workers>1) in fixed ``INSTRUMENTS`` order."""
    if workers <= 1:
        return [process_instrument(inst, exp053)
                for inst in tqdm(INSTRUMENTS, desc="instruments")]
    by_inst: dict[str, dict[str, Any]] = {}
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(process_instrument, inst, exp053): inst for inst in INSTRUMENTS}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="instruments"):
            by_inst[futures[fut]] = fut.result()
    return [by_inst[inst] for inst in INSTRUMENTS]     # deterministic reassembly order


def run(workers: int = 1) -> dict[str, Any]:
    """Run all member cells and write artifacts. Returns the run summary.

    ``workers`` sets per-instrument process-pool parallelism; output is byte-identical
    for any ``workers`` value (order-independent per-cell RNG + fixed merge order).
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    exp053 = load_exp053_benchmark()
    workers = max(1, min(workers, len(INSTRUMENTS)))
    grid = _run_grid(exp053, workers)
    records: list[dict[str, Any]] = []
    factorial: list[dict[str, Any]] = []
    secondaries: list[dict[str, Any]] = []
    recon_rows: list[dict[str, Any]] = []
    champ_rows: list[dict[str, Any]] = []
    instrument_meta: dict[str, Any] = {}
    defect = {"is_defect": False, "non_deterministic": [], "exp053_mismatch": [],
              "causality_violations": [], "determinism_checked": [],
              "invariant_violations": [], "exp053_available": bool(exp053),
              "exp053_checked_cells": 0, "workers": workers}
    for instrument, res in zip(INSTRUMENTS, grid):     # fixed INSTRUMENTS order
        records.extend(res["records"])
        factorial.extend(res["factorial"])
        secondaries.extend(res["secondaries"])
        champ_rows.extend(res["champ_rows"])
        recon_rows.extend(res["recon_rows"])
        if res["meta"] is not None:
            instrument_meta[instrument] = res["meta"]
        for key in ("causality_violations", "invariant_violations",
                    "determinism_checked", "non_deterministic"):
            defect[key].extend(res[key])

    _finalize_defects(defect, recon_rows)
    readout = composition_readout(records, defect)
    write_outputs(records, factorial, secondaries, recon_rows, champ_rows, readout,
                  instrument_meta, defect)
    make_plots(records, factorial)
    return _summarize(records, readout)


def _champion_row(instrument: str, cell: dict[str, Any],
                  car: list[dict[str, Any]]) -> dict[str, Any]:
    """One champion-A3 binding readout row per cell."""
    row = next((r for r in car if r["arm"] == CHAMPION_ID), None)
    if row is None or cell.get("empty"):
        return {"instrument": instrument, "domain": cell.get("domain"), "m": 0,
                "median": None, "ci_low_1s": None, "viable": False, "champion_win": False}
    return {"instrument": instrument, "domain": cell["domain"], "m": row["m"],
            "median": row["median"], "ci_low_1s": row["ci_low_1s"],
            "ci_lo_2s": row["ci_lo_2s"], "ci_hi_2s": row["ci_hi_2s"],
            "contrast_random_low": row["contrast_random_low"],
            "contrast_ma_low": row["contrast_ma_low"], "beats_random": row["beats_random"],
            "beats_ma": row["beats_ma"], "viable": row["viable"],
            "champion_win": row["champion_win"], "n_conditioned": row.get("n_conditioned")}


def _record_cell_defects(cell: dict[str, Any], instrument: str, domain: str,
                         defect: dict[str, Any]) -> None:
    """Accumulate per-cell causality / invariant violations."""
    if cell.get("empty"):
        return
    label = f"{instrument}-{domain}"
    if not cell.get("causality_ok", True):
        defect["causality_violations"].append(label)
    inv = cell.get("invariants", {})
    inv_ok = all(inv.get(k, True) for k in (
        "weights_sum_ok", "single_leg_match", "degenerate_match", "shared_stop_ok",
        "adv_none_no_stop", "a4_cap_dominates"))
    if not (inv_ok and a4_subset_ok(cell)):
        defect["invariant_violations"].append(label)


def _finalize_defects(defect: dict[str, Any], recon_rows: list[dict[str, Any]]) -> None:
    """Aggregate defect gates into the binding is_defect flag."""
    defect["exp053_mismatch"] = [r["cell"] for r in recon_rows
                                 if r.get("checked") and not r["consistent"]]
    if defect["exp053_mismatch"]:
        defect["is_defect"] = True
    defect["exp053_checked_cells"] = sum(1 for r in recon_rows if r.get("checked"))
    if not defect["exp053_available"] or defect["exp053_checked_cells"] == 0:
        defect["is_defect"] = True
    causal_instr = {c.split("-")[0] for c in defect["causality_violations"]}
    if len(causal_instr) >= P11_MIN_INSTR:
        defect["is_defect"] = True
    if defect["invariant_violations"]:                 # exact structural checks
        defect["is_defect"] = True
    if defect["non_deterministic"]:                    # byte-identical replay failed
        defect["is_defect"] = True


def write_outputs(
    records: list[dict[str, Any]], factorial: list[dict[str, Any]],
    secondaries: list[dict[str, Any]], recon_rows: list[dict[str, Any]],
    champ_rows: list[dict[str, Any]], readout: dict[str, Any],
    instrument_meta: dict[str, Any], defect: dict[str, Any],
) -> None:
    """Persist per-cell parquet, the champion/factorial/secondary maps, and the JSONs."""
    pl.DataFrame(records, strict=False).write_parquet(RESULTS_DIR / "per_cell_expectancy.parquet")
    pl.DataFrame(records, strict=False).write_csv(RESULTS_DIR / "combined_system_map.csv")
    (pl.DataFrame(champ_rows, strict=False) if champ_rows
     else pl.DataFrame({"instrument": []})).write_csv(RESULTS_DIR / "champion_map.csv")
    (pl.DataFrame(factorial, strict=False) if factorial
     else pl.DataFrame({"contrast": []})).write_csv(RESULTS_DIR / "factorial_map.csv")
    (pl.DataFrame(secondaries, strict=False) if secondaries
     else pl.DataFrame({"signal": [], "arm": []})).write_csv(RESULTS_DIR / "secondary_map.csv")
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
        "phase": "014-B", "hypothesis": "HYP-013", "family": "CF-HA-HARAMI-001",
        "stratum": "TRAIN-only (first 49%); nested TEST + final-30% holdout sealed",
        "entry_anchor": "harami confirmation-bar real close (live, pre-ZigZag-confirm)",
        "binding_arm": "/STRONG-STAT p75; /STRONG-HA disclosed",
        "binding_endpoint": ("median per-event position-weighted gross ATR-normalised return "
                             "(P14, P15 fills)"),
        "binding_candidate": ("champion A3 V2A x ADV-NONE (operator decision 2); its own P11 "
                              "viability AND dominance over BOTH P13 baselines drive the G2 fork"),
        "geometry": ("best-per-layer assembly: 2x2 favourable (50% single leg vs V2A "
                     "{1/3,2/3,1}) x adverse (1:1 vs /ADV-NONE) factorial + BENCH anchor + A4 "
                     "champion at /THIRD-TIME floor=48; third barrier = benchmark adaptive cap "
                     "floor=6 for A0-A3"),
        "arms": ALL_ARM_IDS,
        "params": {
            "atr_period": ATR_PERIOD, "atr_mult_primary": ATR_MULT,
            "favourable_fraction_bench": 0.50, "adverse_bench": "1:1",
            "adverse_none": "sentinel adv = -+inf (never binds)",
            "n_legs_v2a": 3, "leg_weights": "equal (1/3)", "v2a_fracs": list(_V2A),
            "timecap_floor_bench": 6, "timecap_floor_a4": THIRD_TIME_FLOOR,
            "timecap_k": 1.5, "timecap_window": 20, "timecap_min_moves": 5,
            "stat_window": 20, "stat_min_window": 5, "stat_q": 0.75, "ha_run_len": 3,
            "ma_segmentation": [MA_FAST, MA_SLOW], "power_floor": POWER_FLOOR,
            "n_boot": N_BOOT, "boot_batch": BOOT_BATCH, "base_seed": BASE_SEED,
            "p11": [P11_MIN_CELLS, P11_MIN_INSTR],
        },
        "baselines": ["matched-count random (in-progress rd, non-signal pool, per arm)",
                      "MA(20,50)-crossover segmentation per arm (identical pipeline)"],
        "champion_baseline_binding": ("A3 must beat BOTH matched-random AND MA(20,50) "
                                      "(two-baseline IUT conjunction; CI_low(1s)>0 each)"),
        "factorial_contrasts": {lbl: f"{v} - {b}" for lbl, v, b in FACTORIAL_PAIRS},
        "interaction": ("(A3 - A2) - (A1 - A0) on the common 4-arm subset "
                        "(composite block bootstrap)"),
        "contrasts": {"factorial": "paired moving-block bootstrap (common qualifying subset)",
                      "arm_vs_baseline": "independent bootstrap contrast (contrast_ci)"},
        "verdict": readout["verdict"],
        "parallelism": {
            "workers": defect.get("workers", 1),
            "model": ("per-instrument ProcessPoolExecutor; results reassembled in fixed "
                      "INSTRUMENTS order; per-process native threads pinned to 1 "
                      "(POLARS_MAX_THREADS/OMP/OPENBLAS/MKL/NUMEXPR) to avoid CPU "
                      "oversubscription. Output is byte-identical across worker counts: "
                      "every RNG is seeded by (BASE_SEED, cell_index, purpose) so draws are "
                      "order-independent, OHLC aggregation is order-independent, and the merge "
                      "order is fixed. The first usable cell per instrument is replayed "
                      "byte-identically inside its worker (determinism gate)."),
        },
        "determinism_ok": not defect["non_deterministic"],
        "determinism_checked": defect["determinism_checked"],
        "determinism_gate": ("byte-identical re-run of the first usable cell per instrument "
                             "across all 5 arms' stat returns/median/CI, both baselines, and "
                             "the composite interaction."),
        "causality_ok": not defect["causality_violations"],
        "causality_violations": defect["causality_violations"],
        "invariant_violations": defect["invariant_violations"],
        "invariant_gates": ("leg weights sum to 1.0; single-leg LEVEL@fav == resolve_path_ordered "
                            "BENCH; degenerate 3-leg all-LEVEL@fav == single-leg R_event (<=1e-9); "
                            "ADV-NONE never fires an adverse exit (no PX_ADV in A1/A3/A4); shared "
                            "1:1 stop closes all open legs at the adv level; A4 differs from A3 "
                            "only by the cap (N48 >= bench_N per event, identical warmup, A4 qual "
                            "subset of A3); BENCH reproduces EXP-053 per-cell median + count + "
                            "first-hit r to 1e-9 (invariants i+ii)."),
        "exp053_reconciliation": recon_clean,
        "exp053_mismatch": defect["exp053_mismatch"],
        "exp053_available": defect["exp053_available"],
        "exp053_checked_cells": defect["exp053_checked_cells"],
        "exit_reason_disclosure": ("exit-reason composition (weight fraction via each V2A leg / "
                                   "the 1:1 stop / the time cap) is the binding mechanism "
                                   "diagnostic; never enters the verdict."),
        "horizon_note": ("A4 (floor=48) is the registered /THIRD-TIME grid max (EXP-058), "
                         "disclosed-only; bounds champion mechanism vs 6-bar-floor truncation; "
                         "A4 differs from A3 only by the cap (invariant vii)."),
        "is_defect": defect["is_defect"],
        "de30_disclosure": DE30_DISCLOSURE,
        "fill_approximation": ("P15 path is a documented approximation of unobserved intrabar "
                               "motion; 1-minute base bars are not replayed (EXP-054 bounds it)."),
        "adv_none_cost_caveat": ("ADV-NONE leaves the adverse unbounded within the cap; the median "
                                 "endpoint (P14) is robust to the fat left tail but the disclosed "
                                 "mean may diverge. Costs enter only at a future tradability "
                                 "screen if G2 returns PROCEED_TO_SCREEN (out of 014-B scope)."),
        "holdout_fence": ("Only Parquet metadata + first train_rows file-order rows read per "
                          "instrument; full file never sorted/collected; every domain bar fenced "
                          "to CloseTime <= train_end_ts; forward scans (legs, caps incl. floor=48) "
                          "clipped to the data edge -> DATA_CENSORED; TEST and final-30% holdout "
                          "never read."),
        "registry": ("CF-HA-HARAMI-001/HYP-013 (EXP-060); composes registered branches "
                     "/EXIT-PARTIAL (V2A), /ADV-NONE, /THIRD-TIME (floor=48); 0 candidate slots, "
                     "0 TEST reads; the candidate combined definition consumes a slot only at G2 "
                     "PROCEED_TO_SCREEN (P21), never here; characterization readout feeds the "
                     "single 014-B G2."),
        "instrument_meta": instrument_meta,
    }
    with open(RESULTS_DIR / "run_metadata.json", "w") as fh:
        json.dump(meta, fh, indent=2, default=str)


def _summarize(records: list[dict[str, Any]], readout: dict[str, Any]) -> dict[str, Any]:
    """Concise stdout summary."""
    status_counts: dict[str, int] = {}
    for r in records:
        if r["arm"] != CHAMPION_ID:
            continue
        status_counts[r["viable_status"]] = status_counts.get(r["viable_status"], 0) + 1
    return {"verdict": readout["verdict"], "champion": CHAMPION_ID,
            "champion_wins": readout["champion_wins"],
            "champion_status_counts": status_counts, "defect": readout["defect"]}


def _parse_args() -> argparse.Namespace:
    """CLI: --workers controls per-instrument parallelism (default = all CPUs)."""
    parser = argparse.ArgumentParser(description=f"{EXPERIMENT_ID} combined event system")
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
    wins = summary["champion_wins"]
    LOGGER.info("champion A3 wins: %s cells / %s instruments (P11 pass=%s)",
                wins["n_cells"], wins["n_instruments"], wins["passes"])
    LOGGER.info("champion per-cell status counts: %s",
                json.dumps(summary["champion_status_counts"]))
    if summary["defect"]["is_defect"]:
        LOGGER.info("DEFECT: %s", json.dumps(summary["defect"], default=str))
    LOGGER.info("artifacts -> %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
