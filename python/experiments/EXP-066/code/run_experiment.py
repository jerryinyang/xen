"""EXP-066 — MA(20,50)-Substrate Position-Management Exits (dual-object).

``CF-HA-HARAMI-001`` / HYP-019 — Phase 015 **surface S3** (**dual conditioning object**).
Governing design/D0: ``docs/experiments-docs/checkpoints/2026-06-17-015-ma-substrate-
conditioned-harami-full-surface/`` (``design.md`` §3/§5/§7; ``D0-predeclarations.md`` P1-P12;
``D0-amendment-001-dual-parallel-substrate.md``). TRAIN-only, gross; **0 candidate slots,
0 TEST reads**.

**Re-run under D0 Amendment 001 (2026-06-17).** The prior EXP-066 scope measured a single
position-management exit axis labelled *hybrid* but reconciled its benchmark arm to EXP-061
``M0`` -- the **native** object. This dual-object re-run emits the full 12-arm
position-management exit axis **for both objects individually** (separate arms, separate
matched-random nulls, separate per-cell viability, separate P11 composition, separate
EVIDENCE fork -- never pooled) and corrects the reconciliation roles (native ``M-BENCH``
<-> EXP-061 ``M0``; hybrid ``H-BENCH`` <-> EXP-061 ``H0``).

**The question (scope §Hypothesis), per object.** Does varying **only the exit machinery** --
from the benchmark single-leg BENCH (50% fav / 1:1 stop / MA adaptive cap) to one of eleven
predeclared position-management arms (partial exits + structure trailing-stop variants) --
improve the conditioned harami's gross per-event **median** expectancy on the MA(20,50)
substrate (arm median CI_low>0, >=30 events), **beat its own object's matched-random-on-MA
null** (binding signal attribution, P5), **and beat that object's BENCH arm** (paired median
contrast), clearing **P11 with the P6 non-4h rule**?

The two conditioning objects share the **same** frozen HA-harami detection and the **same**
MA outcome geometry (``rd`` / ``M_sofar`` / favourable references / cap, all from the shared
MA in-progress state); they differ **only** in the ``/STRONG-STAT`` conditioning filter (P2):

  * **native** (``nat``) -- ``/STRONG-STAT`` p75 on the in-progress confirmed **MA segment**;
    population byte-identical to EXP-061 ``M0`` / EXP-060B BENCH-MA; the ``BENCH`` arm
    **reproduces EXP-061 M0** per-cell median + m (P12).
  * **hybrid** (``hyb``) -- ``/STRONG-STAT`` p75 on the in-progress confirmed **ZigZag move**
    (mask byte-identical to EXP-053/060/061 ``H0``), applied through the **same** MA geometry;
    the ``BENCH`` arm **reproduces EXP-061 H0** per-cell median + m (P12).

Each object has its **own** matched-random-on-MA null per arm, matched to its own qualifying
count and excluding its own signal entries, on disjoint dedicated RNG streams.

The secondary (``atr_mult=0.5``) ZigZag provides the structure trailing-stop ratchet for
``TRAIL-*`` and ``COMBINED-*`` arms; events without secondary-ZigZag history after entry are
warmup-excluded (disclosed per cell per arm per object). The reversal-event leg (``PARTIAL-V1``
/ ``V2C`` / ``COMBINED-V1`` / ``V2C``) uses MA-segment forward-confirmation (same direction as
the trade) + opposing conditioned harami as reversal triggers, via
:func:`xen.position_exits.reversal_event_targets` pointed at MA segments.

Reconciliation (P12): ``M-BENCH`` -> EXP-061 ``M0`` (1e-9); ``H-BENCH`` -> EXP-061 ``H0``
(1e-9). RNG streams byte-identical to EXP-061/EXP-063/EXP-064 (BENCH purposes unchanged).

Detection on HA candles; every outcome metric on real prices; MA(20,50) on real close. Outputs
under ``results/`` and ``plots/``; created in orchestration. Output is byte-identical for any
``--workers`` value (order-independent per-cell RNG + fixed merge order). The two objects are
never pooled. **Do not adjudicate G-015** -- single terminal gate after the full Phase 015
slate.

Disclosed secondaries deferred (runtime/budget; recorded in ``run_metadata.json``): the
``/STRONG-HA`` conditioning arm and the ZigZag-substrate position-management exit surface.
The binding dual-object 12-arm MA exit surface and the P4 mean diagnostic are fully computed.
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
# byte-identical single-threaded.
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
# P12 reconciliation anchor: EXP-061's per-cell parquet carries BENCH arms (M0/H0).
EXP061_PARQUET = EXPERIMENTS_ROOT / "EXP-061" / "results" / "per_cell_expectancy.parquet"

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
    ADV_TRAIL,
    ATR_MULT_TRAIL,
    LEG_FIRST_PROFIT,
    LEG_LEVEL,
    LEG_NONE,
    LEG_REVERSAL,
    PX_ADV,
    PX_CLASS_LABELS,
    build_active_stops,
    exit_reason_weights,
    leg_levels_from_fracs,
    resolve_legs,
    reversal_event_targets,
    weighted_returns,
)
from xen.zigzag import generate_zigzag, wilder_atr  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (Phase 015 D0 frozen + EXP-056/060/061/064 inherited; no tuning)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-066"
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
ATR_MULT = 1.0                     # P1 ZigZag (hybrid conditioning)
MA_FAST, MA_SLOW = 20, 50          # P1 MA-segmentation substrate (fixed, not swept)
POWER_FLOOR = 30                   # P10/P14: minimum qualifying events to report
P11_MIN_CELLS, P11_MIN_INSTR = 5, 3
P6_MIN_NON_4H = 3                  # P6: >=3 qualifying cells outside the 4h domain
LOW_N_4H = 60                      # P4 concentration: a 4h cell with m<60 is low-n
TRIM_FRAC = 0.10                   # P4: 10% symmetric trimmed mean
TAIL_FRAC = 0.05                   # P4: worst-5% tail-share
RECON_TOL = 1e-9                   # P12 EXP-061 reproduction tolerance
N_BOOT = 10_000                    # P14 bootstrap resamples
BOOT_BATCH = 2_000                 # bounded bootstrap memory batch
BASE_SEED = 20260616               # frozen master seed (identical to EXP-060/061/063/064)
EXCLUDED_FILE_MARKERS = ("analysis70", "analysis_slice", "first70")
DE30_DISCLOSURE = (
    "DE30 truncated history: broker m1 history ends 2026-01-16; counts derive "
    "from its own realized timeline and are not span-comparable (VAL-003).")
LOGGER = logging.getLogger(EXPERIMENT_ID)

# --------------------------------------------------------------------------- #
# Conditioning objects (D0 Amendment 001; reported individually, never pooled)
# --------------------------------------------------------------------------- #
OBJECTS: tuple[str, ...] = ("nat", "hyb")
OBJECT_NAME: dict[str, str] = {
    "nat": "native (MA-segment /STRONG-STAT; reconciles EXP-061 M0)",
    "hyb": "hybrid (ZigZag /STRONG-STAT x MA geometry; reconciles EXP-061 H0)",
}
OBJECT_BENCH_LABEL: dict[str, str] = {"nat": "M0", "hyb": "H0"}

# --------------------------------------------------------------------------- #
# Position-management arm set (12 predeclared binding arms; OAT on exit machinery)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ArmSpec:
    """One predeclared position-management arm."""

    aid: str
    idx: int                             # stable RNG / column offset (0..11)
    leg_kinds: tuple[int, ...]           # LEG_* per leg
    leg_fracs: tuple[float | None, ...]  # fav_dist fraction per leg (None = non-level)
    weights: tuple[float, ...]           # leg weights (sum 1.0)
    adv_mode: int                        # ADV_FIXED | ADV_TRAIL
    trail_init_none: bool                # TRAIL-TP-NOINIT (no initial stop until confirm)
    needs_reversal: bool                 # any LEG_REVERSAL leg
    is_bench: bool


_T = (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)
ARMS: list[ArmSpec] = [
    ArmSpec("BENCH",        0, (LEG_LEVEL,),                            (1.0,),                    (1.0,), ADV_FIXED, False, False, True),
    ArmSpec("PARTIAL-V1",   1, (LEG_FIRST_PROFIT, LEG_LEVEL, LEG_REVERSAL), (None, 1.0, None),    _T,     ADV_FIXED, False, True,  False),
    ArmSpec("PARTIAL-V2A",  2, (LEG_LEVEL, LEG_LEVEL, LEG_LEVEL),      (1.0/3.0, 2.0/3.0, 1.0),  _T,     ADV_FIXED, False, False, False),
    ArmSpec("PARTIAL-V2B",  3, (LEG_LEVEL, LEG_LEVEL, LEG_LEVEL),      (0.5, 1.0, 1.5),           _T,     ADV_FIXED, False, False, False),
    ArmSpec("PARTIAL-V2C",  4, (LEG_LEVEL, LEG_LEVEL, LEG_REVERSAL),   (1.0/3.0, 2.0/3.0, None), _T,     ADV_FIXED, False, True,  False),
    ArmSpec("TRAIL-PURE",   5, (LEG_NONE,),                             (None,),                   (1.0,), ADV_TRAIL, False, False, False),
    ArmSpec("TRAIL-TP-INIT",6, (LEG_LEVEL,),                           (1.0,),                    (1.0,), ADV_TRAIL, False, False, False),
    ArmSpec("TRAIL-TP-NOINIT", 7, (LEG_LEVEL,),                        (1.0,),                    (1.0,), ADV_TRAIL, True,  False, False),
    ArmSpec("COMBINED-V1",  8, (LEG_FIRST_PROFIT, LEG_LEVEL, LEG_REVERSAL), (None, 1.0, None),    _T,     ADV_TRAIL, False, True,  False),
    ArmSpec("COMBINED-V2A", 9, (LEG_LEVEL, LEG_LEVEL, LEG_LEVEL),      (1.0/3.0, 2.0/3.0, 1.0),  _T,     ADV_TRAIL, False, False, False),
    ArmSpec("COMBINED-V2B",10, (LEG_LEVEL, LEG_LEVEL, LEG_LEVEL),      (0.5, 1.0, 1.5),           _T,     ADV_TRAIL, False, False, False),
    ArmSpec("COMBINED-V2C",11, (LEG_LEVEL, LEG_LEVEL, LEG_REVERSAL),   (1.0/3.0, 2.0/3.0, None), _T,     ADV_TRAIL, False, True,  False),
]
ALL_ARM_IDS: list[str] = [a.aid for a in ARMS]
ALT_ARMS: list[ArmSpec] = [a for a in ARMS if not a.is_bench]
ARM_BY_ID: dict[str, ArmSpec] = {a.aid: a for a in ARMS}
ARM_MODEL: dict[str, str] = {
    "BENCH":          "single-leg 0.50*M_sofar fav / 1:1 stop / MA adaptive cap (reconciles EXP-061 M0/H0)",
    "PARTIAL-V1":     "3-leg: {first-profit-close, 50%-fav, reversal-event}; 1:1 shared stop",
    "PARTIAL-V2A":    "3-leg: {1/3, 2/3, 1}×fav_dist; 1:1 shared stop",
    "PARTIAL-V2B":    "3-leg: {0.5, 1.0, 1.5}×fav_dist; 1:1 shared stop",
    "PARTIAL-V2C":    "3-leg: {1/3, 2/3}×fav_dist + reversal-event runner; 1:1 shared stop",
    "TRAIL-PURE":     "single-leg; structure trail (1:1 init, 0.5-ZZ ratchet); no fav target",
    "TRAIL-TP-INIT":  "single-leg; fav=50%-M_sofar; structure trail (1:1 init)",
    "TRAIL-TP-NOINIT":"single-leg; fav=50%-M_sofar; structure trail (no init stop, then ratchet)",
    "COMBINED-V1":    "V1 partial fav legs + structure trail adverse (1:1 init)",
    "COMBINED-V2A":   "V2A partial fav legs + structure trail adverse",
    "COMBINED-V2B":   "V2B partial fav legs + structure trail adverse",
    "COMBINED-V2C":   "V2C partial fav legs + structure trail adverse",
}

# --------------------------------------------------------------------------- #
# Per-object per-arm RNG purpose blocks
# --------------------------------------------------------------------------- #
# BENCH purposes are identical to EXP-061 M0/H0 + RM0/RH0 so each BENCH arm
# reproduces its EXP-061 anchor exactly (P12). Non-BENCH arms use a fresh block
# far above EXP-061's range (<=85000) so no existing stream shifts and both
# objects' nulls are disjoint.
BENCH_PB: dict[str, dict[str, int]] = {
    "nat": {"med": 9000, "mean": 23000, "trim": 43000, "rm_draw": 61000, "rm_med": 62000,
            "rm_mean": 63000, "rm_trim": 64000, "paired": 0},
    "hyb": {"med": 81000, "mean": 83000, "trim": 85000, "rm_draw": 71000, "rm_med": 72000,
            "rm_mean": 73000, "rm_trim": 74000, "paired": 0},
}
OBJ_BLOCK: dict[str, int] = {"nat": 100_000, "hyb": 200_000}
STAT_OFF: dict[str, int] = {"med": 0, "mean": 1, "trim": 2, "rm_draw": 3, "rm_med": 4,
                            "rm_mean": 5, "rm_trim": 6, "paired": 7}


def arm_pb(obj: str, aid: str) -> dict[str, int]:
    """Deterministic per-(object, arm) RNG purpose block.

    ``BENCH`` reuses EXP-061 M0/H0 purposes for byte-identical reproduction;
    every other arm uses a fresh distinct block (``OBJ_BLOCK + idx*10 + off``).
    """
    if aid == "BENCH":
        return BENCH_PB[obj]
    base = OBJ_BLOCK[obj] + ARM_BY_ID[aid].idx * 10
    return {stat: base + off for stat, off in STAT_OFF.items()}


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ArmResult:
    """One arm's per-cell resolved population summary + qualifying returns.

    Carries the median (binding), the mean + 10% trimmed mean + worst-5% tail-share
    (P4 diagnostic) point estimates and CIs, and the per-event arrays (``r_full``
    and ``qual`` over the arm's own entry order) for the arm-vs-BENCH paired contrast.
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
    r_firsthit: float | None       # BENCH single-leg only; None for multi-leg arms
    win_rate: float | None
    data_censored: int
    warmup_excluded: int           # TRAIL-*/COMBINED-* arms: events outside sec_hist
    exit_weights: dict[str, float]
    population: int                # built-barrier population (pre-resolution)
    adv_count: int                 # events resolving to any adverse exit
    block_len: int
    r_e: np.ndarray                # qualifying weighted returns in entry order
    r_full: np.ndarray             # full-length returns aligned to entry_idx (for pairing)
    qual: np.ndarray               # qualifying mask aligned to the arm's entry order
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
    """Load exactly the TRAIN 1-minute rows (first 49%) by file-order prefix (F01)."""
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


def load_exp061_bench() -> dict[tuple[str, str], dict[str, Any]]:
    """Load EXP-061's per-cell M0 (native) + H0 (hybrid) arms for the P12 anchors."""
    if not EXP061_PARQUET.exists():
        return {}
    df = pl.read_parquet(EXP061_PARQUET)
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for row in df.filter(pl.col("label").is_in(["M0", "H0"])).iter_rows(named=True):
        if not row.get("member"):
            continue
        cell = out.setdefault((row["instrument"], row["domain"]), {})
        cell[row["label"]] = {"m": row.get("m"), "median": row.get("median")}
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
    """Real-bar OHLC + TickVolume + CloseTime epochs (real prices only)."""
    return {
        "open": bars.get_column("Open").to_numpy().astype(np.float64),
        "high": bars.get_column("High").to_numpy().astype(np.float64),
        "low": bars.get_column("Low").to_numpy().astype(np.float64),
        "close": bars.get_column("Close").to_numpy().astype(np.float64),
        "volume": bars.get_column("TickVolume").to_numpy().astype(np.float64),
        "epoch": bars.get_column("CloseTime").dt.epoch("s").to_numpy().astype(np.int64),
    }


def harami_entry_indices(bars: pl.DataFrame, bar_epoch: np.ndarray) -> np.ndarray:
    """Detect HA haramis and map each to its real domain-bar index (exact match)."""
    ha = generate_heiken_ashi(bars)
    haramis = detect_ha_harami(ha)
    if haramis.height == 0:
        return np.empty(0, dtype=np.int64)
    harami_epoch = haramis.get_column("HA0Time").dt.epoch("s").to_numpy().astype(np.int64)
    return _map_to_grid(bar_epoch, harami_epoch, "harami HA0Time")


def _map_to_grid(bar_epoch: np.ndarray, times: np.ndarray, label: str) -> np.ndarray:
    """Exact CloseTime->bar-index map (raises on any mismatch)."""
    idx = np.searchsorted(bar_epoch, times)
    if np.any(idx >= bar_epoch.shape[0]) or np.any(bar_epoch[np.minimum(
            idx, bar_epoch.shape[0] - 1)] != times):
        raise ValueError(f"{label} not found on the domain-bar grid")
    return idx.astype(np.int64)


def move_arrays(moves: pl.DataFrame, bar_epoch: np.ndarray) -> dict[str, np.ndarray]:
    """Confirmed ZigZag-move arrays + confirm bar indices."""
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


def ma_segment_moves(ohlc: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """MA(20,50)-crossover segmentation as a ZigZag-shaped confirmed-move set.

    Identical to EXP-060/060B/061/063/064's ``ma_segment_moves``.
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


def secondary_history(sec: dict[str, np.ndarray], entry_epoch: np.ndarray) -> np.ndarray:
    """Per-entry flag: at least one secondary ZigZag move confirmed at/before the entry."""
    return np.searchsorted(sec["confirm_epoch"], entry_epoch, side="right") >= 1


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

    Byte-identical block construction to
    :func:`xen.expectancy.bootstrap_median_distribution`.
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
        else:
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
    """Fraction of total negative return contributed by the worst 5% of events."""
    m = int(values.shape[0])
    if m == 0:
        return None
    total_neg = float(values[values < 0.0].sum())
    if total_neg >= 0.0:
        return 0.0
    k = max(1, int(np.ceil(TAIL_FRAC * m)))
    worst = np.sort(values)[:k]
    worst_neg = float(worst[worst < 0.0].sum())
    return float(worst_neg / total_neg)


# --------------------------------------------------------------------------- #
# Pure computation -- resolve one arm on one population -> ArmResult
# --------------------------------------------------------------------------- #
def _summarize_arm(
    r_e: np.ndarray, r_full: np.ndarray, qual: np.ndarray, exit_w: dict[str, float],
    r_firsthit: float | None, censored: int, warmup: int, adv_count: int, population: int,
    rng: np.random.Generator, mean_rng: np.random.Generator,
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
        mean_low, mean_lo, mean_hi = median_ci(mean_dist)
        trim_dist, _ = bootstrap_stat_distribution(r_e, trim_rng, "trim",
                                                    n_boot=N_BOOT, batch=BOOT_BATCH)
        trim_low, trim_lo, trim_hi = median_ci(trim_dist)
    return ArmResult(
        m=m, median=median, mean=mean, trimmed_mean=trimmed, tail_share_worst5=tail,
        ci_low_1s=ci_low, ci_lo_2s=ci_lo, ci_hi_2s=ci_hi,
        mean_ci_low_1s=mean_low, mean_ci_lo_2s=mean_lo, mean_ci_hi_2s=mean_hi,
        trim_ci_low_1s=trim_low, trim_ci_lo_2s=trim_lo, trim_ci_hi_2s=trim_hi,
        r_firsthit=r_firsthit, win_rate=(float((r_e > 0).mean()) if m > 0 else None),
        data_censored=censored, warmup_excluded=warmup, exit_weights=exit_w,
        population=population, adv_count=adv_count, block_len=block_len,
        r_e=r_e, r_full=r_full, qual=qual, dist=dist, mean_dist=mean_dist,
        draw_count=draw_count)


def _empty_arm() -> ArmResult:
    return ArmResult(0, None, None, None, None, None, None, None, None, None, None,
                     None, None, None, None, None, 0, 0,
                     {label: 0.0 for label in PX_CLASS_LABELS.values()}, 0, 0, 1,
                     np.empty(0), np.empty(0), np.empty(0, dtype=bool),
                     np.empty(0), np.empty(0), 0)


def _firsthit(
    classes: np.ndarray, qual: np.ndarray, fav_code: int, other_code: int,
) -> float | None:
    """First-hit ratio FAV/(FAV+ADV) over qualifying events (BENCH single-leg only)."""
    fav_n = int((qual & (classes == fav_code)).sum())
    other_n = int((qual & (classes == other_code)).sum())
    resolved = fav_n + other_n
    return (fav_n / resolved) if resolved > 0 else None


# --------------------------------------------------------------------------- #
# Pure computation -- reversal-event targets per object (MA segments, per-object cond haramis)
# --------------------------------------------------------------------------- #
def _reversal_for(
    entry_idx: np.ndarray, entry_epoch: np.ndarray, rd: np.ndarray,
    seg: dict[str, np.ndarray], bench_n: np.ndarray, bench_warmup: np.ndarray,
    cond_entry_idx: np.ndarray, cond_rd: np.ndarray, needs: bool,
) -> np.ndarray:
    """Per-event reversal-event bar for arms that need it (else an all -1 array).

    ``needs=True`` arms (PARTIAL-V1/V2C, COMBINED-V1/V2C): the earlier of the next
    MA-segment confirmation in direction ``rd`` and the next opposing conditioned harami
    with direction ``-rd``. Pointing at MA segments exactly mirrors EXP-059's use of
    primary ZigZag but on the MA substrate.
    """
    if not needs:
        return np.full(int(entry_idx.shape[0]), -1, dtype=np.int64)
    return reversal_event_targets(
        entry_idx, entry_epoch, rd,
        seg["confirm_epoch"], seg["confirm_idx"], seg["direction"],
        bench_n, bench_warmup, cond_entry_idx, cond_rd)


# --------------------------------------------------------------------------- #
# Pure computation -- signal arm + matched-random-on-MA null, per object/arm
# --------------------------------------------------------------------------- #
def signal_arm(
    obj: str, arm: ArmSpec, ohlc: dict[str, np.ndarray], ma: dict[str, Any],
    cond_mask: np.ndarray, entry_idx: np.ndarray, sec: dict[str, np.ndarray],
    sec_hist: np.ndarray, reversal_idx: np.ndarray,
    last_train_idx: int, cell_index: int,
) -> ArmResult:
    """Resolve one (object, arm) on the object's conditioned population.

    ``BENCH`` reuses :func:`xen.expectancy.resolve_path_ordered` (exact EXP-061
    path) and its M0/H0 RNG purposes; every other arm uses the ``position_exits``
    multi-leg pipeline. ``reversal_idx`` is pre-computed per object; arms without a
    ``LEG_REVERSAL`` leg receive it but :func:`xen.position_exits.resolve_legs`
    ignores it.
    """
    pb = arm_pb(obj, arm.aid)
    entry_close = ma["entry_close"]
    rd = ma["state"].rd
    atr_entry = ma["atr_entry"]
    bench_n = ma["bench_n"]
    fav = ma["fav"]
    adv = ma["adv"]
    fav_dist = ma["fav_dist"]
    # BENCH includes fav_dist > 0 filter for byte-identical EXP-061 reproduction.
    pop = ma["buildable"] & cond_mask & (fav_dist > 0.0)
    weights = np.asarray(arm.weights, dtype=np.float64)
    n_bars = int(ohlc["close"].shape[0])

    if arm.is_bench:
        classes, exit_px = resolve_path_ordered(
            ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"],
            entry_idx, fav, adv, rd, bench_n, pop, n_bars)
        r_all = realised_returns(classes, exit_px, entry_close, rd, atr_entry)
        qual = pop & qualifying_mask(classes, exit_px, atr_entry)
        r_firsthit = _firsthit(classes, qual, CLASS_FAV, CLASS_ADV)
        censored = int((pop & (classes == CLASS_DATA_CENSORED)).sum())
        adv_count = int((qual & (classes == CLASS_ADV)).sum())
        warmup = 0
        leg_cls = classes[:, None]
    else:
        # Non-BENCH uses full buildable & cond (no extra fav_dist filter).
        pop_base = ma["buildable"] & cond_mask
        levels = leg_levels_from_fracs(entry_close, rd, fav_dist, arm.leg_fracs)
        pop_arm = pop_base.copy()
        active = None
        warmup = 0
        if arm.adv_mode == ADV_TRAIL:
            warmup = int((pop_base & ~sec_hist).sum())
            pop_arm = pop_base & sec_hist
            active = build_active_stops(
                entry_idx, rd, adv, arm.trail_init_none,
                sec["confirm_idx"], sec["direction"], sec["end_price"],
                bench_n, last_train_idx)
        leg_px, leg_cls = resolve_legs(
            ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"],
            entry_idx, entry_close, rd, arm.leg_kinds, levels,
            reversal_idx, adv, bench_n, pop_arm, arm.adv_mode,
            active, last_train_idx)
        r_all, qual = weighted_returns(
            leg_px, leg_cls, weights, entry_close, rd, atr_entry, pop_arm)
        r_firsthit = None
        censored = int((pop_arm & ~qual & np.isfinite(atr_entry) & (atr_entry > 0.0)).sum())
        adv_count = int((qual & (leg_cls == PX_ADV).any(axis=1)).sum())

    order = np.argsort(entry_idx[qual], kind="stable")
    r_e = r_all[qual][order]
    exit_w = exit_reason_weights(leg_cls, weights, qual)
    return _summarize_arm(r_e, r_all, qual, exit_w, r_firsthit, censored, warmup, adv_count,
                          int(pop.sum()), _rng(cell_index, pb["med"]),
                          _rng(cell_index, pb["mean"]), _rng(cell_index, pb["trim"]),
                          draw_count=0)


def matched_random_arm(
    obj: str, arm: ArmSpec, ohlc: dict[str, np.ndarray], state_all: InProgressState,
    seg: dict[str, np.ndarray], warmup_all: np.ndarray, atr_all: np.ndarray,
    signal_idx: np.ndarray, draw_count: int, cell_index: int,
    sec: dict[str, np.ndarray], cond_entry_idx: np.ndarray, cond_rd: np.ndarray,
    last_train_idx: int,
) -> ArmResult:
    """Matched-count random-in-MA-regime control through one arm's pipeline (P5).

    Draws ``draw_count`` entries from the eligible MA-regime pool excluding the
    object's own signal entries, then resolves through the identical arm exit
    machinery (same benchmark fav/adv/cap, same secondary ZigZag stop, same MA
    reversal targets). The reversal locator receives the same ``cond_entry_idx``/
    ``cond_rd`` as the signal arm so opposing-harami detection is consistent.
    """
    pb = arm_pb(obj, arm.aid)
    n_bars = int(ohlc["close"].shape[0])
    eligible = (state_all.valid & (state_all.m_sofar > 0.0) & np.isfinite(atr_all)
                & (atr_all > 0.0) & (~warmup_all))
    is_signal = np.zeros(n_bars, dtype=bool)
    is_signal[signal_idx] = True
    pool = np.flatnonzero(eligible & ~is_signal)
    if draw_count <= 0 or pool.shape[0] == 0:
        return _empty_arm()
    k = min(draw_count, pool.shape[0])
    drawn = np.sort(_rng(cell_index, pb["rm_draw"]).choice(pool, size=k, replace=False))
    sub = _subset_state(state_all, drawn)
    bench_n, bench_warmup = adaptive_time_caps_by_epoch(
        ohlc["epoch"][drawn], seg["confirm_epoch"], seg["confirm_idx"])
    base_pop = (sub.valid & (sub.m_sofar > 0.0) & np.isfinite(atr_all[drawn])
                & (atr_all[drawn] > 0.0) & ~bench_warmup)
    bar = benchmark_barriers(ohlc["close"][drawn], sub.rd, sub.m_sofar)
    fav_d, fav, adv = bar["fav_dist"], bar["fav"], bar["adv"]
    reversal = _reversal_for(drawn, ohlc["epoch"][drawn], sub.rd, seg, bench_n, bench_warmup,
                             cond_entry_idx, cond_rd, arm.needs_reversal)
    sec_hist_drawn = secondary_history(sec, ohlc["epoch"][drawn])
    weights = np.asarray(arm.weights, dtype=np.float64)

    if arm.is_bench:
        pop = base_pop & (fav_d > 0.0)
        classes, exit_px = resolve_path_ordered(
            ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"],
            drawn, fav, adv, sub.rd, bench_n, pop, n_bars)
        r_all = realised_returns(classes, exit_px, ohlc["close"][drawn], sub.rd, atr_all[drawn])
        qual = pop & qualifying_mask(classes, exit_px, atr_all[drawn])
        r_firsthit = _firsthit(classes, qual, CLASS_FAV, CLASS_ADV)
        censored = int((pop & (classes == CLASS_DATA_CENSORED)).sum())
        adv_count = int((qual & (classes == CLASS_ADV)).sum())
        warmup = 0
        leg_cls = classes[:, None]
    else:
        levels = leg_levels_from_fracs(ohlc["close"][drawn], sub.rd, fav_d, arm.leg_fracs)
        pop_arm = base_pop.copy()
        active = None
        warmup = 0
        if arm.adv_mode == ADV_TRAIL:
            warmup = int((base_pop & ~sec_hist_drawn).sum())
            pop_arm = base_pop & sec_hist_drawn
            active = build_active_stops(
                drawn, sub.rd, adv, arm.trail_init_none,
                sec["confirm_idx"], sec["direction"], sec["end_price"],
                bench_n, last_train_idx)
        leg_px, leg_cls = resolve_legs(
            ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"],
            drawn, ohlc["close"][drawn], sub.rd, arm.leg_kinds, levels,
            reversal, adv, bench_n, pop_arm, arm.adv_mode,
            active, last_train_idx)
        r_all, qual = weighted_returns(
            leg_px, leg_cls, weights, ohlc["close"][drawn], sub.rd, atr_all[drawn], pop_arm)
        r_firsthit = None
        censored = int((pop_arm & ~qual & np.isfinite(atr_all[drawn]) & (atr_all[drawn] > 0.0)).sum())
        adv_count = int((qual & (leg_cls == PX_ADV).any(axis=1)).sum())

    order = np.argsort(drawn[qual], kind="stable")
    r_e = r_all[qual][order]
    exit_w = exit_reason_weights(leg_cls, weights, qual)
    population = int(base_pop.sum())
    return _summarize_arm(r_e, r_all, qual, exit_w, r_firsthit, censored, warmup, adv_count,
                          population, _rng(cell_index, pb["rm_med"]),
                          _rng(cell_index, pb["rm_mean"]), _rng(cell_index, pb["rm_trim"]),
                          draw_count=draw_count)


def contrast(sig: ArmResult, null: ArmResult) -> dict[str, Any]:
    """Independent bootstrap contrast ``signal - null`` (median binding, mean disclosed)."""
    med_low, med_lo, med_hi = contrast_ci(sig.dist, null.dist)
    mean_low, mean_lo, mean_hi = contrast_ci(sig.mean_dist, null.mean_dist)
    return {"median_low_1s": med_low, "median_lo_2s": med_lo, "median_hi_2s": med_hi,
            "mean_low_1s": mean_low, "mean_lo_2s": mean_lo, "mean_hi_2s": mean_hi}


def paired_vs_bench(arm_res: ArmResult, bench: ArmResult, cell_index: int,
                    purpose: int) -> dict[str, Any]:
    """Arm - BENCH paired-median contrast on the common qualifying subset (one object)."""
    if arm_res.qual.shape[0] == 0 or bench.qual.shape[0] == 0:
        return {"paired_low_1s": float("nan"), "paired_lo_2s": float("nan"),
                "paired_hi_2s": float("nan"), "n_common": 0}
    common = arm_res.qual & bench.qual
    n_common = int(common.sum())
    if n_common < POWER_FLOOR:
        return {"paired_low_1s": float("nan"), "paired_lo_2s": float("nan"),
                "paired_hi_2s": float("nan"), "n_common": n_common}
    low, lo, hi, _ = paired_median_contrast_ci(
        arm_res.r_full[common], bench.r_full[common], _rng(cell_index, purpose))
    return {"paired_low_1s": low, "paired_lo_2s": lo, "paired_hi_2s": hi,
            "n_common": n_common}


# --------------------------------------------------------------------------- #
# Per-cell signal contexts (MA geometry shared; ZigZag mask for the hybrid object)
# --------------------------------------------------------------------------- #
def _ma_context(
    ohlc: dict[str, np.ndarray], atr: np.ndarray, entry_idx: np.ndarray,
    entry_epoch: np.ndarray,
) -> dict[str, Any]:
    """MA(20,50) geometry context at the harami entries.

    Returns ``bench_warmup`` in addition to EXP-064's fields -- needed by
    :func:`_reversal_for` (``reversal_event_targets`` requires it).
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
            "atr": atr, "atr_entry": atr_entry, "bench_n": bench_n,
            "bench_warmup": bench_warmup, "buildable": buildable,
            "stat": stat, "fav_dist": bar["fav_dist"], "fav": bar["fav"], "adv": bar["adv"]}


def _zz_context(
    bars: pl.DataFrame, ohlc: dict[str, np.ndarray], entry_idx: np.ndarray,
    entry_epoch: np.ndarray,
) -> dict[str, Any]:
    """ZigZag conditioned-signal context: the hybrid object's /STRONG-STAT mask."""
    moves = generate_zigzag(bars, atr_period=ATR_PERIOD, atr_mult=ATR_MULT)
    mv = move_arrays(moves, ohlc["epoch"])
    if mv["confirm_epoch"].shape[0] == 0:
        n = int(entry_idx.shape[0])
        return {"empty": True, "retained_p75": np.zeros(n, dtype=bool),
                "state": None, "end_epoch": np.empty(0, dtype=np.int64)}
    entry_close = ohlc["close"][entry_idx]
    state = live_in_progress_state(entry_epoch, entry_close, mv["confirm_epoch"],
                                   mv["end_price"], mv["end_epoch"], mv["direction"])
    stat = live_strong_stat(state.k, state.m_sofar, mv["magnitude"])
    return {"empty": False, "retained_p75": stat["retained_p75"], "state": state,
            "end_epoch": mv["end_epoch"]}


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
    atr = wilder_atr(ohlc["high"], ohlc["low"], ohlc["close"], ATR_PERIOD)
    entry_idx = harami_entry_indices(bars, ohlc["epoch"])
    base = {"domain": domain, "n_bars": int(bars.height), "n_harami": int(entry_idx.shape[0])}
    if entry_idx.shape[0] == 0:
        return {**base, "empty": True}
    entry_epoch = ohlc["epoch"][entry_idx]
    ma = _ma_context(ohlc, atr, entry_idx, entry_epoch)
    if ma.get("empty"):
        return {**base, "empty": True}

    # Secondary ZigZag (atr_mult=0.5) for structure trailing stops.
    sec_moves = generate_zigzag(bars, atr_period=ATR_PERIOD, atr_mult=ATR_MULT_TRAIL)
    sec = move_arrays(sec_moves, ohlc["epoch"])
    last_train_idx = int(ohlc["close"].shape[0]) - 1

    zz = _zz_context(bars, ohlc, entry_idx, entry_epoch)
    cond_masks = {"nat": ma["stat"]["retained_p75"], "hyb": zz["retained_p75"]}
    arms = _resolve_objects(ohlc, ma, cond_masks, entry_idx, entry_epoch,
                            sec, last_train_idx, cell_index)
    n_conditioned = {o: int((ma["buildable"] & cond_masks[o]).sum()) for o in OBJECTS}
    return {
        **base, "empty": False, "arms": arms,
        "n_conditioned": n_conditioned,
        "causality_ok": _causality_ok(ohlc, entry_idx, entry_epoch, ma, zz),
        "invariants": {o: _cell_invariants(arms[o], ma["fav_dist"]) for o in OBJECTS},
    }


def _resolve_objects(
    ohlc: dict[str, np.ndarray], ma: dict[str, Any], cond_masks: dict[str, np.ndarray],
    entry_idx: np.ndarray, entry_epoch: np.ndarray,
    sec: dict[str, np.ndarray], last_train_idx: int, cell_index: int,
) -> dict[str, Any]:
    """Resolve the 12 position-management arms (signal + matched-random) + contrasts, per object."""
    seg = ma["seg"]
    bench_n = ma["bench_n"]
    bench_warmup = ma["bench_warmup"]
    state_all = live_in_progress_state(ohlc["epoch"], ohlc["close"], seg["confirm_epoch"],
                                       seg["end_price"], seg["end_epoch"], seg["direction"])
    _, warmup_all = adaptive_time_caps_by_epoch(
        ohlc["epoch"], seg["confirm_epoch"], seg["confirm_idx"])
    sec_hist = secondary_history(sec, entry_epoch)
    arms: dict[str, Any] = {}
    for obj in OBJECTS:
        cond = cond_masks[obj]
        signal_idx = entry_idx[cond]
        # Per-object conditioned entries for the reversal locator (opposing-harami search).
        cond_mask_full = ma["buildable"] & cond
        cond_entry_idx = entry_idx[cond_mask_full]
        cond_rd_arr = ma["state"].rd[cond_mask_full]
        # Pre-compute reversal targets once per object (shared by all reversal arms).
        reversal = reversal_event_targets(
            entry_idx, entry_epoch, ma["state"].rd,
            seg["confirm_epoch"], seg["confirm_idx"], seg["direction"],
            bench_n, bench_warmup, cond_entry_idx, cond_rd_arr)
        signals: dict[str, ArmResult] = {}
        nulls: dict[str, ArmResult] = {}
        for arm in ARMS:
            rev = reversal if arm.needs_reversal else np.full(entry_idx.shape[0], -1, np.int64)
            signals[arm.aid] = signal_arm(
                obj, arm, ohlc, ma, cond, entry_idx, sec, sec_hist, rev,
                last_train_idx, cell_index)
            nulls[arm.aid] = matched_random_arm(
                obj, arm, ohlc, state_all, seg, warmup_all, ma["atr"],
                signal_idx, signals[arm.aid].m, cell_index,
                sec, cond_entry_idx, cond_rd_arr, last_train_idx)
        var_rm = {a.aid: contrast(signals[a.aid], nulls[a.aid]) for a in ARMS}
        paired = {a.aid: paired_vs_bench(signals[a.aid], signals["BENCH"], cell_index,
                                          arm_pb(obj, a.aid)["paired"]) for a in ALT_ARMS}
        arms[obj] = {"signals": signals, "nulls": nulls, "var_rm": var_rm, "paired": paired}
    return arms


# --------------------------------------------------------------------------- #
# Per-cell causality / invariant gate
# --------------------------------------------------------------------------- #
def _causality_ok(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, entry_epoch: np.ndarray,
    ma: dict[str, Any], zz: dict[str, Any],
) -> bool:
    """Strict grid + causal MA reference segments + causal ZigZag reference (hybrid mask)."""
    epoch = ohlc["epoch"]
    if epoch.shape[0] >= 2 and not bool(np.all(np.diff(epoch) > 0)):
        return False
    state = ma["state"]
    valid = state.valid & (state.k >= 0)
    if valid.any():
        kk = state.k[valid]
        if not bool(np.all(ma["seg"]["end_epoch"][kk] <= entry_epoch[valid])):
            return False
        if not bool(np.all(epoch[entry_idx[valid]] <= entry_epoch[valid])):
            return False
        if not bool(np.all(ma["seg"]["end_idx"][kk] <= entry_idx[valid])):
            return False
    if not zz.get("empty") and zz["state"] is not None:
        zs = zz["state"]
        zvalid = zs.valid & (zs.k >= 0)
        if zvalid.any():
            zk = zs.k[zvalid]
            if not bool(np.all(zz["end_epoch"][zk] <= entry_epoch[zvalid])):
                return False
    return True


def _cell_invariants(
    arms_obj: dict[str, Any], fav_dist: np.ndarray,
) -> dict[str, bool]:
    """Predeclared structural invariants for one object."""
    signals, nulls = arms_obj["signals"], arms_obj["nulls"]
    exit_ok = all(
        (res.m == 0) or abs(sum(res.exit_weights.values()) - 1.0) <= 1e-9
        for res in list(signals.values()) + list(nulls.values()))
    matched_ok = all(nulls[a.aid].draw_count == signals[a.aid].m for a in ARMS)
    q = signals["BENCH"].qual
    fav_pos = True
    if q.shape[0] and fav_dist.shape[0] == q.shape[0]:
        if bool((q & ~(fav_dist > 0.0)).any()):
            fav_pos = False
    return {"exit_ok": bool(exit_ok), "matched_count_ok": bool(matched_ok),
            "fav_dist_positive": bool(fav_pos)}


# --------------------------------------------------------------------------- #
# Per-cell record flattening (one long row per cell x object x arm)
# --------------------------------------------------------------------------- #
def _viable(res: ArmResult) -> bool:
    """Median CI_low(1s) > 0 AND m >= power floor (binding viability)."""
    return bool(res.m >= POWER_FLOOR and res.ci_low_1s is not None
                and np.isfinite(res.ci_low_1s) and res.ci_low_1s > 0.0)


def _mean_viable(res: ArmResult) -> bool:
    """Disclosed P4 flag (raw-mean CI_low > 0); never a viability gate."""
    return bool(res.m >= POWER_FLOOR and res.mean_ci_low_1s is not None
                and np.isfinite(res.mean_ci_low_1s) and res.mean_ci_low_1s > 0.0)


def _beats_rm(c: dict[str, Any]) -> bool:
    return bool(np.isfinite(c["median_low_1s"]) and c["median_low_1s"] > 0.0)


def _beats_bench(p: dict[str, Any]) -> bool:
    low = p.get("paired_low_1s")
    return bool(low is not None and np.isfinite(low) and low > 0.0)


def arm_rows(instrument: str, cell: dict[str, Any]) -> list[dict[str, Any]]:
    """One long row per (cell, object, arm): signal stats, RM null, contrasts, mean P4."""
    rows: list[dict[str, Any]] = []
    for obj in OBJECTS:
        obj_arms = cell["arms"][obj]
        for arm in ARMS:
            sig = obj_arms["signals"][arm.aid]
            null = obj_arms["nulls"][arm.aid]
            c = obj_arms["var_rm"][arm.aid]
            pair = obj_arms["paired"].get(arm.aid, {})
            viable = _viable(sig)
            beats_rm = _beats_rm(c)
            beats_bench = (not arm.is_bench) and _beats_bench(pair)
            wins = bool(not arm.is_bench and viable and beats_rm and beats_bench)
            gap = (sig.median - sig.mean) if (sig.median is not None
                                              and sig.mean is not None) else None
            low_n_4h = bool(cell["domain"] == "4h" and sig.m < LOW_N_4H)
            rows.append({
                "instrument": instrument, "domain": cell["domain"], "object": obj,
                "arm": arm.aid, "arm_model": ARM_MODEL[arm.aid],
                "is_bench": arm.is_bench, "member": True, "excluded": False,
                "n_harami": cell["n_harami"], "n_conditioned": cell["n_conditioned"][obj],
                "m": sig.m, "population": sig.population, "data_censored": sig.data_censored,
                "warmup_excluded": sig.warmup_excluded, "adv_count": sig.adv_count,
                "median": sig.median, "ci_low_1s": sig.ci_low_1s,
                "ci_lo_2s": sig.ci_lo_2s, "ci_hi_2s": sig.ci_hi_2s,
                "mean": sig.mean, "mean_ci_low_1s": sig.mean_ci_low_1s,
                "mean_ci_lo_2s": sig.mean_ci_lo_2s, "mean_ci_hi_2s": sig.mean_ci_hi_2s,
                "trimmed_mean": sig.trimmed_mean,
                "trim_ci_low_1s": sig.trim_ci_low_1s, "trim_ci_lo_2s": sig.trim_ci_lo_2s,
                "trim_ci_hi_2s": sig.trim_ci_hi_2s,
                "tail_share_worst5": sig.tail_share_worst5,
                "gap_median_minus_mean": gap, "r_firsthit": sig.r_firsthit,
                "win_rate": sig.win_rate, "rm_m": null.m, "rm_draw_count": null.draw_count,
                "rm_median": null.median, "rm_mean": null.mean,
                "var_rm_median_low_1s": c["median_low_1s"],
                "var_rm_median_hi_2s": c["median_hi_2s"], "var_rm_mean_low_1s": c["mean_low_1s"],
                "var_bench_paired_low_1s": pair.get("paired_low_1s"),
                "paired_n_common": pair.get("n_common"),
                "median_viable": viable, "mean_viable": _mean_viable(sig),
                "beats_rm": beats_rm, "beats_bench": beats_bench, "arm_wins": wins,
                "low_n_4h": low_n_4h,
                **{f"ew_{label}": sig.exit_weights[label] for label in PX_CLASS_LABELS.values()},
            })
    return rows


def excluded_rows(instrument: str, domain: str) -> list[dict[str, Any]]:
    """COVERAGE_EXCLUDED / empty-cell placeholder rows (one per object x arm)."""
    rows = []
    for obj in OBJECTS:
        for arm in ARMS:
            rows.append({
                "instrument": instrument, "domain": domain, "object": obj,
                "arm": arm.aid, "arm_model": ARM_MODEL[arm.aid],
                "is_bench": arm.is_bench, "member": False, "excluded": True,
                "n_harami": None, "n_conditioned": None,
                "m": 0, "median": None, "mean": None, "trimmed_mean": None,
                "tail_share_worst5": None, "median_viable": False, "mean_viable": False,
                "beats_rm": False, "beats_bench": False, "arm_wins": False,
                "low_n_4h": False,
            })
    return rows


def readiness_row(instrument: str, cell: dict[str, Any]) -> dict[str, Any]:
    """Per-cell readiness/construction row (causality + per-object invariant flags)."""
    inv = cell.get("invariants", {})
    row = {
        "instrument": instrument, "domain": cell["domain"], "n_bars": cell["n_bars"],
        "n_harami": cell["n_harami"],
        "n_conditioned_nat": cell["n_conditioned"].get("nat"),
        "n_conditioned_hyb": cell["n_conditioned"].get("hyb"),
        "causality_ok": cell.get("causality_ok", True),
    }
    all_ok = cell.get("causality_ok", True)
    for obj in OBJECTS:
        io = inv.get(obj, {})
        for k in ("exit_ok", "matched_count_ok", "fav_dist_positive"):
            row[f"{obj}_{k}"] = io.get(k, True)
            all_ok = all_ok and io.get(k, True)
    row["construction_pass"] = bool(all_ok)
    return row


# --------------------------------------------------------------------------- #
# Composition + the EVIDENCE verdict (P11 with the P6 non-4h rule), per object
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


def _object_readout(member: list[dict[str, Any]], defect: dict[str, Any], obj: str) -> dict[str, Any]:
    """One object's per-arm P11/P6 tallies + the EVIDENCE verdict."""
    obj_rows = [r for r in member if r["object"] == obj]
    per_arm: dict[str, Any] = {}
    for arm in ARMS:
        vr = [r for r in obj_rows if r["arm"] == arm.aid]
        powered = _p11([r for r in vr if r["m"] >= POWER_FLOOR
                        and (r.get("rm_m") or 0) >= POWER_FLOOR], "median_viable")
        per_arm[arm.aid] = {
            "median_viable": _p11(vr, "median_viable"),
            "beats_rm": _p11(vr, "beats_rm"),
            "beats_bench": _p11(vr, "beats_bench"),
            "arm_wins": _p11(vr, "arm_wins"),
            "mean_viable": _p11(vr, "mean_viable"),
            "powered": powered,
        }
    verdict = _verdict(defect, per_arm)
    return {"object": OBJECT_NAME[obj], "verdict": verdict, "per_arm": per_arm}


def composition_readout(rows: list[dict[str, Any]], defect: dict[str, Any]) -> dict[str, Any]:
    """Per-object per-arm P11/P6 tallies + the EVIDENCE verdict (never pooled)."""
    member = [r for r in rows if not r.get("excluded")]
    nat = _object_readout(member, defect, "nat")
    hyb = _object_readout(member, defect, "hyb")
    rank = {"EVIDENCE_FOR": 3, "EVIDENCE_AGAINST": 2,
            "INCONCLUSIVE_POWER_LIMITED": 1, "SUBSTRATE_METHOD_DEFECT": 0}
    phase = nat if rank.get(nat["verdict"], 0) >= rank.get(hyb["verdict"], 0) else hyb
    return {
        "phase_verdict": phase["verdict"], "phase_stronger_object": phase["object"],
        "native": nat, "hybrid": hyb,
        "binding_arm_set": ("12 position-management exit arms: BENCH; PARTIAL-V1/V2A/V2B/V2C; "
                            "TRAIL-PURE/TP-INIT/TP-NOINIT; COMBINED-V1/V2A/V2B/V2C"),
        "reference": "BENCH = single-leg 0.50*M_sofar fav / 1:1 stop / MA adaptive cap (reconciles EXP-061 M0/H0)",
        "disclosed": "exit-reason composition per arm per object (secondary_map.csv)",
        "binding_endpoint": "median (P14); mean+10%trim+worst-5% tail-share = P4 diagnostic",
        "rule": _rule_text(), "g015_routing": _routing_text(), "defect": defect,
    }


def _verdict(defect: dict[str, Any], per_arm: dict[str, Any]) -> str:
    """Mechanical EVIDENCE verdict per the scope Success/Failure, for one object."""
    if defect["is_defect"]:
        return "SUBSTRATE_METHOD_DEFECT"
    alt_aids = [a.aid for a in ALT_ARMS]
    powered = any(per_arm[aid]["powered"]["composes"] for aid in alt_aids)
    if not powered:
        return "INCONCLUSIVE_POWER_LIMITED"
    wins = [aid for aid in alt_aids if per_arm[aid]["arm_wins"]["composes"]]
    return "EVIDENCE_FOR" if wins else "EVIDENCE_AGAINST"


def _rule_text() -> str:
    return ("Per object, never pooled. Binding endpoint = median (P14); mean + 10% trimmed mean + "
            "worst-5% tail-share disclosed (P4, never a viability gate). Per cell (m>=30): "
            "median_viable = arm median CI_low(1s)>0; beats_rm = (arm - own-object RM-on-MA) "
            "independent-contrast median CI_low(1s)>0; beats_bench = (arm - BENCH) paired-median "
            "contrast CI_low(1s)>0; arm_wins = all three. EVIDENCE_FOR iff an alternative arm "
            "arm_wins composes (P11 + P6 non-4h: >=5 cells / >=3 instruments / >=3 cells outside "
            "4h). EVIDENCE_AGAINST iff the powered grid composes but no alternative arm wins. "
            "INCONCLUSIVE iff <P11 quorum powered. SUBSTRATE_METHOD_DEFECT on any reconciliation / "
            "determinism / causality / invariant failure. Phase reading = stronger object's verdict.")


def _routing_text() -> str:
    return ("Feeds the single terminal G-015 after the full Phase 015 slate (no closure or "
            "candidate registration here, P9), judged per object. EVIDENCE_FOR (an object): a "
            "position-management exit geometry is an MA-substrate lever -> the winning arm + its "
            "RM and benchmark margins feed EXP-067 (hybrid) / EXP-068 (native) / G-015. "
            "EVIDENCE_AGAINST: exit machinery is not the lever on MA for that object; family stays "
            "OPEN, the surface result feeds G-015 (P9).")


# --------------------------------------------------------------------------- #
# Determinism replay + reconciliation (DEFECT guards)
# --------------------------------------------------------------------------- #
def determinism_replay(train_1m: pl.DataFrame, domain: str, train_end_epoch: int,
                       cell_index: int) -> bool:
    """Re-run one cell end-to-end and assert byte-identical binding outputs (both objects)."""
    a = compute_cell(train_1m, domain, train_end_epoch, cell_index)
    b = compute_cell(train_1m, domain, train_end_epoch, cell_index)
    if a.get("empty") or b.get("empty"):
        return a.get("empty") == b.get("empty")
    for obj in OBJECTS:
        for arm in ARMS:
            for side in ("signals", "nulls"):
                sa, sb = a["arms"][obj][side][arm.aid], b["arms"][obj][side][arm.aid]
                if not (np.array_equal(sa.r_e, sb.r_e)
                        and (sa.median, sa.ci_low_1s, sa.mean_ci_low_1s, sa.trim_ci_low_1s)
                        == (sb.median, sb.ci_low_1s, sb.mean_ci_low_1s, sb.trim_ci_low_1s)):
                    return False
            ca, cb = a["arms"][obj]["var_rm"][arm.aid], b["arms"][obj]["var_rm"][arm.aid]
            if not (_nan_eq(ca["median_low_1s"], cb["median_low_1s"])
                    and _nan_eq(ca["mean_low_1s"], cb["mean_low_1s"])):
                return False
    return True


def _nan_eq(a: float | None, b: float | None) -> bool:
    if a is None or b is None:
        return a is b
    return bool(a == b or (np.isnan(a) and np.isnan(b)))


def exp061_reconciliation(
    instrument: str, cell: dict[str, Any], anchor: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    """P12 reproduction guard: native BENCH <-> EXP-061 M0; hybrid BENCH <-> EXP-061 H0."""
    key = (instrument, cell["domain"])
    if not anchor or key not in anchor or cell.get("empty"):
        return {"checked": False, "cell": f"{instrument}-{cell.get('domain')}"}
    src = anchor[key]
    out: dict[str, Any] = {"checked": True, "cell": f"{instrument}-{cell['domain']}"}
    consistent = True
    for obj in OBJECTS:
        label = OBJECT_BENCH_LABEL[obj]
        anc = src.get(label)
        bench = cell["arms"][obj]["signals"]["BENCH"]
        if anc is None:
            out[f"{obj}_checked"] = False
            consistent = False
            continue
        m_ok = bench.m == (int(anc["m"]) if anc.get("m") is not None else 0)
        med_ok = _float_match(bench.median, anc.get("median"))
        out.update({f"{obj}_checked": True, f"{obj}_bench_m": bench.m,
                    f"{obj}_exp061_m": anc.get("m"), f"{obj}_bench_median": bench.median,
                    f"{obj}_exp061_median": anc.get("median"),
                    f"{obj}_m_match": bool(m_ok), f"{obj}_median_match": bool(med_ok)})
        consistent = consistent and m_ok and med_ok
    out["consistent"] = bool(consistent)
    return out


def _float_match(a: float | None, b: float | None) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return abs(float(a) - float(b)) <= RECON_TOL


# --------------------------------------------------------------------------- #
# Plotting (bounded; from collected per-cell summaries -- no reloads), per object
# --------------------------------------------------------------------------- #
def _placeholder(ax: plt.Axes, message: str) -> None:
    ax.text(0.5, 0.5, message, ha="center", va="center")
    ax.axis("off")


def _oa_cells(rows: list[dict[str, Any]], obj: str, aid: str) -> list[dict[str, Any]]:
    return [r for r in rows if not r.get("excluded") and r["object"] == obj and r["arm"] == aid]


def plot_median_forest(rows: list[dict[str, Any]], save_path: Path) -> None:
    """Per-object per-arm per-cell median expectancy vs BENCH (headline)."""
    fig, axes = plt.subplots(1, len(OBJECTS), figsize=(16, 7), sharey=True)
    cmap = plt.get_cmap("tab10")
    colours = {a.aid: cmap(i % 10) for i, a in enumerate(ARMS)}
    for ax, obj in zip(np.atleast_1d(axes), OBJECTS):
        any_data = False
        for arm in ARMS:
            cells = sorted([r for r in _oa_cells(rows, obj, arm.aid)
                            if r.get("median") is not None],
                           key=lambda r: (r["instrument"], r["domain"]))
            if not cells:
                continue
            any_data = True
            x = np.arange(len(cells))
            ax.scatter(x, [r["median"] for r in cells], s=10, color=colours[arm.aid],
                       label=arm.aid, alpha=0.85 if arm.is_bench else 0.5,
                       marker="o" if arm.is_bench else "x")
        if not any_data:
            _placeholder(ax, f"{obj}: no powered cells")
        else:
            ax.axhline(0.0, color="k", lw=0.8, ls="--")
            ax.set_xlabel("cell index (sorted by instrument-domain)")
            ax.legend(fontsize=6, ncol=2)
        ax.set_title(OBJECT_NAME[obj].split(" (")[0])
    axes[0].set_ylabel("per-cell median expectancy (ATR units)")
    fig.suptitle(f"{EXPERIMENT_ID}: per-arm median expectancy on MA (native | hybrid; never pooled)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_contrast_heatmap(rows: list[dict[str, Any]], save_path: Path) -> None:
    """arm-BENCH (top) and arm-RM (bottom) CI_low across alt arms x cells, per object."""
    alt_ids = [a.aid for a in ALT_ARMS]
    fig, axes = plt.subplots(2, len(OBJECTS), figsize=(18, 10), sharex="col")
    fields = [("var_bench_paired_low_1s", "arm - BENCH (paired) CI_low"),
              ("var_rm_median_low_1s", "arm - RM-on-MA CI_low")]
    for oi, obj in enumerate(OBJECTS):
        cell_keys = sorted({f"{r['instrument']}-{r['domain']}" for r in rows
                            if not r.get("excluded") and r["object"] == obj})
        for fi, (field, title) in enumerate(fields):
            ax = axes[fi, oi]
            if not cell_keys:
                _placeholder(ax, f"{obj}: no member cells")
                continue
            matrix = np.full((len(alt_ids), len(cell_keys)), np.nan)
            for ri, aid in enumerate(alt_ids):
                lut = {f"{r['instrument']}-{r['domain']}": r.get(field)
                       for r in _oa_cells(rows, obj, aid)}
                for ci, ck in enumerate(cell_keys):
                    v = lut.get(ck)
                    matrix[ri, ci] = v if (v is not None and np.isfinite(v)) else np.nan
            vmax = np.nanmax(np.abs(matrix)) if np.isfinite(matrix).any() else 1.0
            im = ax.imshow(matrix, cmap="RdYlGn", vmin=-vmax, vmax=vmax, aspect="auto")
            ax.set_yticks(range(len(alt_ids)), alt_ids, fontsize=5)
            non4 = ["*" if not ck.endswith("-4h") else "" for ck in cell_keys]
            ax.set_xticks(range(len(cell_keys)),
                          [f"{m}{ck}" for m, ck in zip(non4, cell_keys)], rotation=90, fontsize=3)
            ax.set_title(f"{obj}: {title} (* = non-4h)")
            fig.colorbar(im, ax=ax, fraction=0.025)
    fig.suptitle(f"{EXPERIMENT_ID}: position-management exit lever + signal attribution (per object)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_expectancy_distribution(rows: list[dict[str, Any]], save_path: Path) -> None:
    """Per-object per-arm pooled-within-object median distribution (box)."""
    fig, axes = plt.subplots(1, len(OBJECTS), figsize=(18, 7), sharey=True)
    for ax, obj in zip(np.atleast_1d(axes), OBJECTS):
        data = []
        labels = []
        for arm in ARMS:
            vals = [r["median"] for r in _oa_cells(rows, obj, arm.aid)
                    if r.get("median") is not None]
            data.append(vals if vals else [np.nan])
            labels.append(arm.aid)
        ax.boxplot(data, tick_labels=labels, showfliers=False)
        ax.axhline(0.0, color="k", lw=0.8, ls="--")
        ax.set_xticklabels(labels, rotation=90, fontsize=6)
        ax.set_title(OBJECT_NAME[obj].split(" (")[0])
    axes[0].set_ylabel("per-cell median expectancy (ATR units)")
    fig.suptitle(f"{EXPERIMENT_ID}: per-cell median distribution by arm (per object)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_wins_map(rows: list[dict[str, Any]], save_path: Path) -> None:
    """P11 (non-4h) wins tally per alt arm: arm_wins / median_viable / beats_rm / beats_bench."""
    alt_ids = [a.aid for a in ALT_ARMS]
    flags = ["median_viable", "beats_rm", "beats_bench", "arm_wins"]
    fig, axes = plt.subplots(1, len(OBJECTS), figsize=(16, 6), sharey=True)
    for ax, obj in zip(np.atleast_1d(axes), OBJECTS):
        matrix = np.zeros((len(flags), len(alt_ids)))
        for ci, aid in enumerate(alt_ids):
            vr = _oa_cells(rows, obj, aid)
            for ri, flag in enumerate(flags):
                matrix[ri, ci] = sum(1 for r in vr if r.get(flag))
        im = ax.imshow(matrix, cmap="Greens", aspect="auto")
        ax.set_yticks(range(len(flags)), flags, fontsize=8)
        ax.set_xticks(range(len(alt_ids)), alt_ids, rotation=90, fontsize=5)
        ax.axhline(len(flags) - 1.5, color="k", lw=0.6)
        for ri in range(len(flags)):
            for ci in range(len(alt_ids)):
                ax.text(ci, ri, int(matrix[ri, ci]), ha="center", va="center", fontsize=5)
        ax.set_title(f"{OBJECT_NAME[obj].split(' (')[0]} (quorum={P11_MIN_CELLS} cells)")
        fig.colorbar(im, ax=ax, fraction=0.03)
    fig.suptitle(f"{EXPERIMENT_ID}: per-arm P11 wins tally (per object; never pooled)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_median_vs_mean(rows: list[dict[str, Any]], save_path: Path) -> None:
    """P4 skew preview: per-object median vs raw vs trimmed mean for BENCH + best alt arm."""
    fig, axes = plt.subplots(len(OBJECTS), 2, figsize=(14, 9), sharey=True)
    for oi, obj in enumerate(OBJECTS):
        best = _best_alt_arm(rows, obj)
        panels = [("BENCH", "benchmark"), (best, f"best alt: {best}")]
        for pi, (aid, title) in enumerate(panels):
            ax = axes[oi, pi]
            cells = sorted([r for r in _oa_cells(rows, obj, aid) if r.get("mean") is not None],
                           key=lambda r: r["mean"])
            if not cells:
                _placeholder(ax, f"{obj}/{aid}: no powered cells")
                continue
            x = np.arange(len(cells))
            ax.scatter(x, [r["mean"] for r in cells], c="#d73027", s=14, label="raw mean", zorder=3)
            ax.scatter(x, [r.get("trimmed_mean") if r.get("trimmed_mean") is not None else np.nan
                           for r in cells], facecolors="none", edgecolors="#4575b4", s=14,
                       label="10% trimmed mean", zorder=2)
            ax.scatter(x, [r.get("median") if r.get("median") is not None else np.nan
                           for r in cells], c="#1a9850", s=8, marker="_", label="median", zorder=1)
            ax.axhline(0.0, color="k", lw=0.8, ls="--")
            ax.set_title(f"{obj} : {title}")
            if pi == 0:
                ax.set_ylabel("per-cell expectancy (ATR units)")
            ax.legend(fontsize=7)
    fig.suptitle(f"{EXPERIMENT_ID} P4: median vs raw/trimmed mean -- removable-tail or structural "
                 "(per object)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _best_alt_arm(rows: list[dict[str, Any]], obj: str) -> str:
    """Alt arm with the most median-viable cells (plot focus; deterministic tie-break)."""
    counts = {a.aid: sum(1 for r in _oa_cells(rows, obj, a.aid) if r.get("median_viable"))
              for a in ALT_ARMS}
    return max(ALT_ARMS, key=lambda a: (counts[a.aid], -a.idx)).aid


def make_plots(rows: list[dict[str, Any]]) -> None:
    """Render the five bounded plots from collected per-cell summaries (both objects)."""
    plot_median_forest(rows, PLOTS_DIR / "per_arm_median_forest.png")
    plot_contrast_heatmap(rows, PLOTS_DIR / "arm_contrast_heatmap.png")
    plot_expectancy_distribution(rows, PLOTS_DIR / "expectancy_distribution_by_arm.png")
    plot_wins_map(rows, PLOTS_DIR / "p11_wins_map.png")
    plot_median_vs_mean(rows, PLOTS_DIR / "median_vs_mean_p4_preview.png")


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _cell_index_map() -> dict[tuple[str, str], int]:
    """Stable (instrument, domain) -> int index (identical to EXP-060/061/063/064)."""
    return {(inst, dom): i for i, (inst, dom) in enumerate(
        (inst, dom) for inst in INSTRUMENTS for dom in DOMAINS)}


def process_instrument(
    instrument: str, anchor: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    """Worker: resolve every member cell of one instrument (the parallel unit).

    Self-contained and pure given identical inputs/seeds: each cell's RNG is seeded
    by ``(BASE_SEED, cell_index, purpose)`` (order-independent), so the result is
    identical regardless of worker count or finish order.
    """
    cell_index = _cell_index_map()
    out: dict[str, Any] = {
        "rows": [], "readiness": [], "recon_rows": [], "meta": None,
        "causality_violations": [], "invariant_violations": [],
        "determinism_checked": [], "non_deterministic": []}
    members = [d for d in DOMAINS if (instrument, d) not in EXCLUDED_CELLS]
    if not members:
        for domain in DOMAINS:
            out["rows"].extend(excluded_rows(instrument, domain))
        return out
    train_1m, meta = load_train_1m(instrument)
    out["meta"] = meta
    replayed = False
    for domain in DOMAINS:
        if (instrument, domain) in EXCLUDED_CELLS:
            out["rows"].extend(excluded_rows(instrument, domain))
            continue
        ci = cell_index[(instrument, domain)]
        cell = compute_cell(train_1m, domain, meta["train_end_epoch_s"], ci)
        if cell.get("empty"):
            out["rows"].extend(excluded_rows(instrument, domain))
            out["recon_rows"].append(exp061_reconciliation(instrument, cell, anchor))
            continue
        out["rows"].extend(arm_rows(instrument, cell))
        out["readiness"].append(readiness_row(instrument, cell))
        out["recon_rows"].append(exp061_reconciliation(instrument, cell, anchor))
        _record_cell_defects(cell, instrument, domain, out)
        if not replayed and cell["arms"]["nat"]["signals"]["BENCH"].m > 0:
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
    """Accumulate per-cell causality / invariant violations (any object)."""
    label = f"{instrument}-{domain}"
    if not cell.get("causality_ok", True):
        out["causality_violations"].append(label)
    inv = cell.get("invariants", {})
    bad = any(not all(inv.get(o, {}).get(k, True) for k in
                      ("exit_ok", "matched_count_ok", "fav_dist_positive"))
              for o in OBJECTS)
    if bad:
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
    return [by_inst[inst] for inst in INSTRUMENTS]


def run(workers: int = 1) -> dict[str, Any]:
    """Run all member cells and write artifacts. Returns the run summary.

    Output is byte-identical for any ``workers`` value.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    anchor = load_exp061_bench()
    workers = max(1, min(workers, len(INSTRUMENTS)))
    grid = _run_grid(anchor, workers)
    rows: list[dict[str, Any]] = []
    readiness: list[dict[str, Any]] = []
    recon_rows: list[dict[str, Any]] = []
    instrument_meta: dict[str, Any] = {}
    defect = {"is_defect": False, "non_deterministic": [], "exp061_mismatch": [],
              "causality_violations": [], "determinism_checked": [],
              "invariant_violations": [], "exp061_available": bool(anchor),
              "exp061_checked_cells": 0, "workers": workers}
    for instrument, res in zip(INSTRUMENTS, grid):
        rows.extend(res["rows"])
        readiness.extend(res["readiness"])
        recon_rows.extend(res["recon_rows"])
        if res["meta"] is not None:
            instrument_meta[instrument] = res["meta"]
        for key in ("causality_violations", "invariant_violations",
                    "determinism_checked", "non_deterministic"):
            defect[key].extend(res[key])
    _finalize_defects(defect, recon_rows)
    readout = composition_readout(rows, defect)
    write_outputs(rows, readiness, recon_rows, readout, instrument_meta, defect)
    make_plots(rows)
    return _summarize(rows, readout)


def _finalize_defects(defect: dict[str, Any], recon_rows: list[dict[str, Any]]) -> None:
    defect["exp061_mismatch"] = [r["cell"] for r in recon_rows
                                 if r.get("checked") and not r["consistent"]]
    if defect["exp061_mismatch"]:
        defect["is_defect"] = True
    defect["exp061_checked_cells"] = sum(1 for r in recon_rows if r.get("checked"))
    if not defect["exp061_available"] or defect["exp061_checked_cells"] == 0:
        defect["is_defect"] = True
    causal_instr = {c.split("-")[0] for c in defect["causality_violations"]}
    if len(causal_instr) >= P11_MIN_INSTR:
        defect["is_defect"] = True
    if defect["invariant_violations"]:
        defect["is_defect"] = True
    if defect["non_deterministic"]:
        defect["is_defect"] = True


def _build_secondary_map(member: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """BENCH r + exit-reason composition per arm per object (secondary_map.csv)."""
    ew_labels = list(PX_CLASS_LABELS.values())
    out = []
    for r in member:
        row: dict[str, Any] = {
            "instrument": r["instrument"], "domain": r["domain"],
            "object": r["object"], "arm": r["arm"],
            "m": r.get("m"), "median": r.get("median"),
            "r_firsthit": r.get("r_firsthit"),
            "warmup_excluded": r.get("warmup_excluded"),
            "data_censored": r.get("data_censored"),
            "adv_count": r.get("adv_count"),
        }
        for label in ew_labels:
            row[f"ew_{label}"] = r.get(f"ew_{label}")
        out.append(row)
    return out


def write_outputs(
    rows: list[dict[str, Any]], readiness: list[dict[str, Any]],
    recon_rows: list[dict[str, Any]], readout: dict[str, Any],
    instrument_meta: dict[str, Any], defect: dict[str, Any],
) -> None:
    """Persist the per-cell parquet, the position-management / attribution maps, and JSON."""
    pl.DataFrame(rows, strict=False).write_parquet(RESULTS_DIR / "per_cell_expectancy.parquet")
    member = [r for r in rows if not r.get("excluded")]
    mgmt_cols = [
        "instrument", "domain", "object", "arm", "arm_model", "is_bench", "m",
        "median", "ci_low_1s", "mean", "mean_ci_low_1s", "trimmed_mean",
        "tail_share_worst5", "median_viable", "mean_viable", "beats_rm", "beats_bench",
        "arm_wins", "var_rm_median_low_1s", "var_bench_paired_low_1s", "paired_n_common",
        "data_censored", "warmup_excluded", "low_n_4h", "r_firsthit", "win_rate",
    ]
    _write_csv([{k: r.get(k) for k in mgmt_cols} for r in member],
               RESULTS_DIR / "position_mgmt_map.csv")
    _write_csv(_build_secondary_map(member), RESULTS_DIR / "secondary_map.csv")
    _write_csv(readiness, RESULTS_DIR / "readiness.csv")
    recon_clean = [r for r in recon_rows if r.get("checked")]
    _write_csv(recon_clean, RESULTS_DIR / "reconciliation.csv")
    with open(RESULTS_DIR / "composition_readout.json", "w") as fh:
        json.dump(readout, fh, indent=2, default=str)
    _write_metadata(instrument_meta, defect, recon_clean, readout)


def _write_csv(records: list[dict[str, Any]], path: Path) -> None:
    frame = pl.DataFrame(records, strict=False) if records else pl.DataFrame({"empty": []})
    frame.write_csv(path)


def _write_metadata(
    instrument_meta: dict[str, Any], defect: dict[str, Any],
    recon_clean: list[dict[str, Any]], readout: dict[str, Any],
) -> None:
    meta = {
        "experiment_id": EXPERIMENT_ID,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "015", "surface": "S3", "hypothesis": "HYP-019", "family": "CF-HA-HARAMI-001",
        "checkpoint": "2026-06-17-015-ma-substrate-conditioned-harami-full-surface",
        "amendment": "D0-amendment-001-dual-parallel-substrate (2026-06-17); supersedes prior EXP-066 scope",
        "conditioning_objects": OBJECT_NAME,
        "stratum": "TRAIN-only (first 49%); nested TEST + final-30% holdout sealed",
        "population": ("native byte-identical to EXP-060/061 M0 (8360-class); hybrid mask "
                       "byte-identical to EXP-053/060/061 H0 (3202-class); never pooled"),
        "entry_anchor": "harami confirmation-bar real close (every signal arm, both objects)",
        "binding_endpoint": ("per object: median per-event gross ATR-normalised return (P3/P14, "
                             "P15 fills); mean + 10% trimmed mean + worst-5% tail-share = P4 "
                             "diagnostic (disclosed, never a viability gate)"),
        "arms": ARM_MODEL,
        "binding_arm_set": [a.aid for a in ALT_ARMS],
        "reference": "BENCH = single-leg 0.50*M_sofar fav / 1:1 stop / MA adaptive cap",
        "adverse_held_at_benchmark": "adv = C - rd*fav_dist (benchmark 1:1) for PARTIAL arms; "
                                     "structure trailing stop (0.5-ZZ ratchet) for TRAIL/COMBINED arms",
        "third_barrier": "MA-defined adaptive cap (k=1.5, window=20, floor=6, median, min_moves=5)",
        "reversal_event": ("next MA-segment confirmed with Direction==rd (same as trade) and "
                           "ConfirmTime>entry [via third_event_caps pointed at MA segments] "
                           "OR next opposing conditioned harami with direction=-rd, confirmed "
                           "after entry; first of the two; exit at that bar's real close, "
                           "bounded by bench_N."),
        "secondary_zigzag": (f"atr_mult={ATR_MULT_TRAIL}; substrate-independent structure "
                             "trailing-stop ratchet for TRAIL-*/COMBINED-* arms; events without "
                             "secondary-ZigZag history after entry are warmup-excluded (disclosed "
                             "per cell per arm per object in secondary_map.csv / per_cell_expectancy.parquet)."),
        "params": {
            "atr_period": ATR_PERIOD, "atr_mult_primary": ATR_MULT,
            "atr_mult_trail": ATR_MULT_TRAIL,
            "ma_segmentation": [MA_FAST, MA_SLOW],
            "favourable_fraction_bench": 0.50,
            "timecap_floor_bench": 6, "timecap_k": 1.5,
            "timecap_window": 20, "timecap_min_moves": 5, "power_floor": POWER_FLOOR,
            "low_n_4h_threshold": LOW_N_4H, "trim_frac": TRIM_FRAC, "tail_frac": TAIL_FRAC,
            "n_boot": N_BOOT, "boot_batch": BOOT_BATCH, "base_seed": BASE_SEED,
            "p11": [P11_MIN_CELLS, P11_MIN_INSTR], "p6_min_non_4h": P6_MIN_NON_4H,
        },
        "statistical_methods": [
            "per-cell median CI (bootstrap_median_distribution + median_ci) -- binding, per arm per object",
            "per-cell raw mean + 10% trimmed mean CI (bootstrap_stat_distribution) + worst-5% "
            "tail-share -- P4 diagnostic, per arm per object",
            "independent bootstrap contrast arm - own-object RM-on-MA median (contrast_ci) -- "
            "binding signal attribution, per arm per object",
            "arm - BENCH paired-median contrast (paired_median_contrast_ci, common qualifying "
            "subset) -- binding lever, per alt arm per object",
        ],
        "phase_verdict": readout["phase_verdict"],
        "phase_stronger_object": readout["phase_stronger_object"],
        "native_verdict": readout["native"]["verdict"],
        "hybrid_verdict": readout["hybrid"]["verdict"],
        "per_object_arm_composition": {
            obj: {a.aid: {
                "median_viable": readout[key]["per_arm"][a.aid]["median_viable"]["composes"],
                "beats_rm": readout[key]["per_arm"][a.aid]["beats_rm"]["composes"],
                "beats_bench": readout[key]["per_arm"][a.aid]["beats_bench"]["composes"],
                "arm_wins": readout[key]["per_arm"][a.aid]["arm_wins"]["composes"],
                "mean_viable": readout[key]["per_arm"][a.aid]["mean_viable"]["composes"],
            } for a in ARMS}
            for obj, key in (("nat", "native"), ("hyb", "hybrid"))
        },
        "parallelism": {
            "workers": defect.get("workers", 1),
            "model": ("per-instrument ProcessPoolExecutor; results reassembled in fixed "
                      "INSTRUMENTS order; per-process native threads pinned to 1. Output is "
                      "byte-identical across worker counts: every RNG is seeded by "
                      "(BASE_SEED, cell_index, purpose) so draws are order-independent, "
                      "OHLC aggregation is order-independent, and the merge order is fixed. "
                      "The first usable cell per instrument is replayed byte-identically."),
        },
        "determinism_ok": not defect["non_deterministic"],
        "determinism_checked": defect["determinism_checked"],
        "causality_ok": not defect["causality_violations"],
        "causality_violations": defect["causality_violations"],
        "invariant_violations": defect["invariant_violations"],
        "invariant_gates": ("per object: each arm's exit-reason weights sum to 1.0 (finite "
                            "real-bar P15 resolution); matched-count holds (each null draw target "
                            "== its arm's signal qualifying m); fav_dist > 0 for every counted "
                            "BENCH event (validity). Reconciliation (SUBSTRATE/METHOD_DEFECT): "
                            "native BENCH reproduces EXP-061 M0 and hybrid BENCH reproduces "
                            "EXP-061 H0 per-cell m + median to 1e-9; missing anchor is a defect."),
        "exp061_reconciliation": recon_clean,
        "exp061_mismatch": defect["exp061_mismatch"],
        "exp061_available": defect["exp061_available"],
        "exp061_checked_cells": defect["exp061_checked_cells"],
        "exp061_anchor": str(EXP061_PARQUET),
        "reproduction_safety": ("native BENCH reuses EXP-061 M0/RM0 RNG purposes and hybrid BENCH "
                                "reuses EXP-061 H0/RH0 purposes so each reproduces its EXP-061 "
                                "anchor exactly; every other (object, arm) + its RM null uses a "
                                "fresh dedicated RNG purpose block (>=100000) so no EXP-061 stream "
                                "shifts and the two objects' nulls are disjoint."),
        "disclosed_secondaries_not_computed": (
            "With the position-management exit axis now run on two conditioning objects "
            "(24 binding arm instances + their nulls per cell), the /STRONG-HA conditioning arm "
            "and the ZigZag-substrate position-management exit surface are NOT computed here "
            "(runtime/budget). The binding 12-arm dual-object MA exit axis + P4 mean diagnostic "
            "are fully computed. If G-015 needs the deferred arms, they are a bounded follow-up."),
        "is_defect": defect["is_defect"],
        "de30_disclosure": DE30_DISCLOSURE,
        "fill_approximation": ("P15 path is a documented approximation of unobserved intrabar "
                               "motion; 1-minute base bars are not replayed (EXP-054 bounds it)."),
        "holdout_fence": ("Only Parquet metadata + first train_rows file-order rows read per "
                          "instrument; full file never sorted/collected; every domain bar fenced "
                          "CloseTime <= train_end_ts; forward scans clipped to the data edge -> "
                          "DATA_CENSORED; TEST and final-30% holdout never read."),
        "registry": ("CF-HA-HARAMI-001/HYP-019 (EXP-066); composes the registered MA-SUBSTRATE "
                     "(hybrid + native modes), the 12-arm registered position-management exit "
                     "sweep, the per-object matched-random baselines (nulls), and the P4 mean "
                     "diagnostic. 0 candidate slots, 0 TEST reads; characterisation readout "
                     "feeds the single terminal G-015 (no closure or registration here)."),
        "instrument_meta": instrument_meta,
    }
    with open(RESULTS_DIR / "run_metadata.json", "w") as fh:
        json.dump(meta, fh, indent=2, default=str)


def _summarize(rows: list[dict[str, Any]], readout: dict[str, Any]) -> dict[str, Any]:
    """Concise stdout summary."""
    out: dict[str, Any] = {"phase_verdict": readout["phase_verdict"],
                           "phase_stronger_object": readout["phase_stronger_object"],
                           "defect": readout["defect"], "objects": {}}
    for obj, key in (("nat", "native"), ("hyb", "hybrid")):
        pv = readout[key]["per_arm"]
        out["objects"][obj] = {
            "verdict": readout[key]["verdict"],
            "per_arm": {a.aid: {
                "median_viable": pv[a.aid]["median_viable"]["n_cells"],
                "beats_rm": pv[a.aid]["beats_rm"]["n_cells"],
                "beats_bench": pv[a.aid]["beats_bench"]["n_cells"],
                "arm_wins": pv[a.aid]["arm_wins"]["n_cells"],
                "wins_composes": pv[a.aid]["arm_wins"]["composes"],
            } for a in ARMS}
        }
    return out


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"{EXPERIMENT_ID} MA position-management exits (dual-object)")
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
    for obj, name in (("nat", "NATIVE"), ("hyb", "HYBRID")):
        o = summary["objects"][obj]
        LOGGER.info("[%s] verdict=%s", name, o["verdict"])
        for arm in ALT_ARMS:
            s = o["per_arm"][arm.aid]
            LOGGER.info("  %-16s median-viable %s | beats_rm %s | beats_bench %s | wins %s (P11+P6=%s)",
                        arm.aid, s["median_viable"], s["beats_rm"], s["beats_bench"],
                        s["arm_wins"], s["wins_composes"])
    if summary["defect"]["is_defect"]:
        LOGGER.info("DEFECT: %s", json.dumps(summary["defect"], default=str))
    LOGGER.info("artifacts -> %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
