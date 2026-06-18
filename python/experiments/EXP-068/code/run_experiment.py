"""EXP-068 — MA(20,50)-Substrate Native Combined Champion (Phase 015 S4/native).

``CF-HA-HARAMI-001`` / HYP-021 — Phase 015 **native combined champion** (mirrors EXP-060
on the **native** conditioning object; ``D0-amendment-001-dual-parallel-substrate.md``).
Governing design/D0: ``docs/experiments-docs/checkpoints/2026-06-17-015-ma-substrate-
conditioned-harami-full-surface/`` (``design.md`` §3/§5/§7; ``D0-predeclarations.md`` P1-P12;
``D0-amendment-001``). TRAIN-only, gross; **0 candidate slots, 0 TEST reads**.

This assembles the per-layer **native** surface winners (EXP-061-066) into the predeclared
champion arms and tests them under the **G-015 conjunction** -- per cell, simultaneously:

  * **(a) median-viable**  -- arm median CI_low(1s) > 0 AND m >= 30 (P3/P14, binding);
  * **(b) raw-mean-positive** -- arm raw-mean CI_low(1s) > 0 (P4 co-primary, binding in G-015);
  * **(c) signal-attributable** -- (arm - own matched-random-on-MA null) median contrast
    CI_low(1s) > 0 (P5, binding),

composed at **P11 with the P6 non-4h rule** (>=5 passing cells over >=3 instruments, with
>=3 passing cells outside the 4h domain). The deliverable is per champion arm, never pooled.

**Three native binding arms** (scope §"Champion arms"):

  * ``BENCH``        -- single-leg 0.50*M_sofar fav / 1:1 stop / MA adaptive cap. P12 primary
                       reconciliation: reproduces EXP-061 ``M0`` / EXP-060B BENCH-MA (1e-9).
  * ``PARTIAL-V2A``  -- 3 equal legs at {1/3, 2/3, 1}*fav_dist; shared 1:1 adverse stop; MA cap.
                       The S3 native winner. P12 secondary reconciliation: reproduces EXP-066
                       native ``PARTIAL-V2A`` (1e-9).
  * ``V2A-ADVNONE``  -- 3 equal legs at {1/3, 2/3, 1}*fav_dist; **no adverse stop** (the MA
                       adaptive cap is the sole stop-out); MA cap. The EXP-060B V2A x ADV-NONE
                       champion geometry with partial scaling -- **never computed before**, so
                       no P12 anchor; guarded by determinism + the ADV-NONE invariant (zero
                       adverse stop-outs).

The **hybrid** object is **NOT a binding measurement object here** (that role is EXP-067). A
single ``hyb`` ``BENCH`` arm is run **for the P12 reconciliation check only** (verifying the
ZigZag-conditioning path still reproduces EXP-061 ``H0`` (1e-9)); its result is excluded from
every native P11 composition, the G-015 conjunction, and all native plots.

The ``V2A-ADVNONE`` no-adverse forward scan is implemented in orchestration by passing an
all-``NaN`` adverse level to :func:`xen.position_exits.resolve_legs`: the shared-stop test in
:func:`xen.position_exits._scan_event` then never activates, so each leg exits only at its
favourable level (``PX_FAV``), the MA cap bar's real close (``PX_TIMECAP``), or
``PX_DATA_CENSORED`` when the TRAIN edge truncates the window. **No ``xen/`` module is
changed** -- ``BENCH`` and ``PARTIAL-V2A`` therefore reproduce EXP-061/EXP-066 exactly.

RNG: ``BENCH`` reuses EXP-061 M0/H0 + EXP-066 BENCH purposes; ``PARTIAL-V2A`` reuses EXP-066's
native PARTIAL-V2A purpose block (so both reproduce their anchors byte-identically);
``V2A-ADVNONE`` uses a fresh dedicated block (>=300000) so no existing stream shifts.

Detection on HA candles; every outcome metric on real prices; MA(20,50) on real close. Output
is byte-identical for any ``--workers`` value (order-independent per-cell RNG + fixed merge
order). **Do not adjudicate G-015** -- the single terminal gate runs after the full Phase 015
slate (results.md interpretation step).

Disclosed secondaries deferred (runtime/budget; recorded in ``run_metadata.json``): the
``/STRONG-HA`` conditioning arm and the ``V2C x ADV-NONE`` / other partial-variant x ADV-NONE
combinations (only V2A is predeclared for ADV-NONE, mirroring the EXP-060B champion axis).
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
# P12 reconciliation anchors: EXP-061's per-cell parquet carries the BENCH arms
# (M0 native / H0 hybrid); EXP-066's per-cell parquet carries native PARTIAL-V2A.
EXP061_PARQUET = EXPERIMENTS_ROOT / "EXP-061" / "results" / "per_cell_expectancy.parquet"
EXP066_PARQUET = EXPERIMENTS_ROOT / "EXP-066" / "results" / "per_cell_expectancy.parquet"

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
    PX_TRAIL,
    exit_reason_weights,
    leg_levels_from_fracs,
    resolve_legs,
    weighted_returns,
)
from xen.zigzag import generate_zigzag, wilder_atr  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (Phase 015 D0 frozen + EXP-060/061/066 inherited; no tuning)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-068"
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
ATR_MULT = 1.0                     # P1 ZigZag (hybrid conditioning; P12 H-BENCH check only)
MA_FAST, MA_SLOW = 20, 50          # P1 MA-segmentation substrate (fixed, not swept)
POWER_FLOOR = 30                   # P10/P14: minimum qualifying events to report
P11_MIN_CELLS, P11_MIN_INSTR = 5, 3
P6_MIN_NON_4H = 3                  # P6: >=3 qualifying cells outside the 4h domain
LOW_N_4H = 60                      # P4 concentration: a 4h cell with m<60 is low-n
TRIM_FRAC = 0.10                   # P4: 10% symmetric trimmed mean
TAIL_FRAC = 0.05                   # P4: worst-5% tail-share
TAIL_DRIVEN_THRESHOLD = 0.40       # P4 closure: tail-share > 0.40 => tail-driven (EXP-063 conv.)
RECON_TOL = 1e-9                   # P12 reproduction tolerance
N_BOOT = 10_000                    # P14 bootstrap resamples
BOOT_BATCH = 2_000                 # bounded bootstrap memory batch
BASE_SEED = 20260616               # frozen master seed (identical to EXP-060/061/066)
EXCLUDED_FILE_MARKERS = ("analysis70", "analysis_slice", "first70")
DE30_DISCLOSURE = (
    "DE30 truncated history: broker m1 history ends 2026-01-16; counts derive "
    "from its own realized timeline and are not span-comparable (VAL-003).")
LOGGER = logging.getLogger(EXPERIMENT_ID)

# --------------------------------------------------------------------------- #
# Conditioning objects (D0 Amendment 001). native = binding; hybrid = P12 check only.
# --------------------------------------------------------------------------- #
OBJECTS: tuple[str, ...] = ("nat", "hyb")
BINDING_OBJECT = "nat"
OBJECT_NAME: dict[str, str] = {
    "nat": "native (MA-segment /STRONG-STAT; BINDING; reconciles EXP-061 M0 + EXP-066 PARTIAL-V2A)",
    "hyb": "hybrid (ZigZag /STRONG-STAT x MA geometry; P12 CHECK ONLY -- not binding; reconciles "
           "EXP-061 H0)",
}
OBJECT_BENCH_LABEL: dict[str, str] = {"nat": "M0", "hyb": "H0"}

# --------------------------------------------------------------------------- #
# Champion arm set (3 native binding arms; hybrid runs BENCH only as a P12 check)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ArmSpec:
    """One predeclared champion arm (native object)."""

    aid: str
    idx: int                             # stable RNG / column offset
    leg_kinds: tuple[int, ...]           # LEG_* per leg
    leg_fracs: tuple[float | None, ...]  # fav_dist fraction per leg (None = non-level)
    weights: tuple[float, ...]           # leg weights (sum 1.0)
    no_adverse: bool                     # True => ADV-NONE (MA cap is the only stop-out)
    is_bench: bool


_T = (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)
_V2A = (1.0 / 3.0, 2.0 / 3.0, 1.0)
ARMS: list[ArmSpec] = [
    ArmSpec("BENCH",       0, (LEG_LEVEL,),                       (1.0,), (1.0,), False, True),
    ArmSpec("PARTIAL-V2A", 2, (LEG_LEVEL, LEG_LEVEL, LEG_LEVEL), _V2A,   _T,     False, False),
    ArmSpec("V2A-ADVNONE", 12, (LEG_LEVEL, LEG_LEVEL, LEG_LEVEL), _V2A,   _T,     True,  False),
]
ARM_BY_ID: dict[str, ArmSpec] = {a.aid: a for a in ARMS}
# Native carries all 3 binding arms; hybrid runs only BENCH (P12 reconciliation check).
OBJECT_ARMS: dict[str, list[str]] = {
    "nat": ["BENCH", "PARTIAL-V2A", "V2A-ADVNONE"],
    "hyb": ["BENCH"],
}
# The two predeclared alternative champion arms judged for the G-015 conjunction
# (BENCH is the reference baseline, not a candidate champion).
CHAMPION_ARMS: list[str] = ["PARTIAL-V2A", "V2A-ADVNONE"]
ARM_MODEL: dict[str, str] = {
    "BENCH":       "single-leg 0.50*M_sofar fav / 1:1 stop / MA adaptive cap "
                   "(reconciles EXP-061 M0/H0 + EXP-066 BENCH)",
    "PARTIAL-V2A": "3-leg {1/3,2/3,1}*fav_dist; shared 1:1 adverse stop; MA cap "
                   "(S3 native winner; reconciles EXP-066 native PARTIAL-V2A)",
    "V2A-ADVNONE": "3-leg {1/3,2/3,1}*fav_dist; NO adverse stop (MA cap is the sole stop-out) "
                   "(EXP-060B V2A x ADV-NONE champion geometry w/ partial scaling; novel)",
}

# --------------------------------------------------------------------------- #
# Per-object per-arm RNG purpose blocks
# --------------------------------------------------------------------------- #
# BENCH purposes are identical to EXP-061 M0/H0 + EXP-066 BENCH so each BENCH arm
# reproduces its anchor exactly. PARTIAL-V2A reuses EXP-066's native PARTIAL-V2A
# block (OBJ_BLOCK['nat'] + idx*10) so it reproduces EXP-066. V2A-ADVNONE uses a
# fresh block (>=300000) above EXP-066's range so no existing stream shifts.
BENCH_PB: dict[str, dict[str, int]] = {
    "nat": {"med": 9000, "mean": 23000, "trim": 43000, "rm_draw": 61000, "rm_med": 62000,
            "rm_mean": 63000, "rm_trim": 64000, "paired": 0},
    "hyb": {"med": 81000, "mean": 83000, "trim": 85000, "rm_draw": 71000, "rm_med": 72000,
            "rm_mean": 73000, "rm_trim": 74000, "paired": 0},
}
OBJ_BLOCK: dict[str, int] = {"nat": 100_000, "hyb": 200_000}
ADVNONE_BLOCK = 300_000
STAT_OFF: dict[str, int] = {"med": 0, "mean": 1, "trim": 2, "rm_draw": 3, "rm_med": 4,
                            "rm_mean": 5, "rm_trim": 6, "paired": 7}


def arm_pb(obj: str, aid: str) -> dict[str, int]:
    """Deterministic per-(object, arm) RNG purpose block.

    ``BENCH`` reuses EXP-061/066 BENCH purposes; ``PARTIAL-V2A`` reuses EXP-066's
    native PARTIAL-V2A block (byte-identical reproduction); ``V2A-ADVNONE`` uses a
    fresh dedicated block.
    """
    if aid == "BENCH":
        return BENCH_PB[obj]
    if aid == "V2A-ADVNONE":
        base = ADVNONE_BLOCK
    else:  # PARTIAL-V2A: exactly EXP-066's native PARTIAL-V2A block.
        base = OBJ_BLOCK[obj] + ARM_BY_ID[aid].idx * 10
    return {stat: base + off for stat, off in STAT_OFF.items()}


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ArmResult:
    """One arm's per-cell resolved population summary + qualifying returns.

    Carries the median (binding), the mean + 10% trimmed mean + worst-5% tail-share
    (P4 co-primary) point estimates and CIs, and the per-event arrays (``r_full``
    and ``qual``) for the arm-vs-BENCH paired contrast.
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
    adv_count: int                 # events resolving to any adverse stop (ADV-NONE => 0)
    exit_weights: dict[str, float]
    population: int                # built-barrier population (pre-resolution)
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
    """Load EXP-061's per-cell M0 (native) + H0 (hybrid) arms for the BENCH P12 anchors."""
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


def load_exp066_partial() -> dict[tuple[str, str], dict[str, Any]]:
    """Load EXP-066's per-cell native PARTIAL-V2A arm for the secondary P12 anchor."""
    if not EXP066_PARQUET.exists():
        return {}
    df = pl.read_parquet(EXP066_PARQUET)
    sub = df.filter((pl.col("object") == "nat") & (pl.col("arm") == "PARTIAL-V2A")
                    & (pl.col("member") == True))  # noqa: E712
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for row in sub.iter_rows(named=True):
        out[(row["instrument"], row["domain"])] = {"m": row.get("m"), "median": row.get("median")}
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
    """Confirmed ZigZag-move arrays + confirm bar indices (hybrid conditioning mask)."""
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

    Identical to EXP-060/060B/061/066's ``ma_segment_moves``.
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


def _winsorized_mean(values: np.ndarray) -> float | None:
    """10% symmetric winsorized mean point estimate (None on empty)."""
    m = int(values.shape[0])
    if m == 0:
        return None
    cut = int(np.floor(TRIM_FRAC * m))
    if cut == 0:
        return float(np.mean(values))
    ordered = np.sort(values)
    lo_val, hi_val = ordered[cut], ordered[m - cut - 1]
    return float(np.mean(np.clip(values, lo_val, hi_val)))


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
    r_firsthit: float | None, censored: int, adv_count: int, population: int,
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
        data_censored=censored, adv_count=adv_count, exit_weights=exit_w,
        population=population, block_len=block_len,
        r_e=r_e, r_full=r_full, qual=qual, dist=dist, mean_dist=mean_dist,
        draw_count=draw_count)


def _empty_arm() -> ArmResult:
    return ArmResult(0, None, None, None, None, None, None, None, None, None, None,
                     None, None, None, None, None, 0, 0,
                     {label: 0.0 for label in PX_CLASS_LABELS.values()}, 0, 1,
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


def _adv_count_legs(leg_cls: np.ndarray, qual: np.ndarray) -> int:
    """Count qualifying events that resolved to any adverse stop (PX_ADV or PX_TRAIL)."""
    adv = ((leg_cls == PX_ADV) | (leg_cls == PX_TRAIL)).any(axis=1)
    return int((qual & adv).sum())


# --------------------------------------------------------------------------- #
# Pure computation -- signal arm + matched-random-on-MA null, per object/arm
# --------------------------------------------------------------------------- #
def signal_arm(
    obj: str, arm: ArmSpec, ohlc: dict[str, np.ndarray], ma: dict[str, Any],
    cond_mask: np.ndarray, entry_idx: np.ndarray, last_train_idx: int, cell_index: int,
) -> ArmResult:
    """Resolve one (object, arm) on the object's conditioned population.

    ``BENCH`` reuses :func:`xen.expectancy.resolve_path_ordered` (exact EXP-061
    path + M0/H0 RNG purposes). The partial arms use the ``position_exits`` multi-leg
    resolver; ``V2A-ADVNONE`` passes an all-``NaN`` adverse level so the only stop-out
    is the MA cap (``PX_TIMECAP``).
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
        leg_cls = classes[:, None]
    else:
        # Non-BENCH uses full buildable & cond (no extra fav_dist filter).
        pop_arm = ma["buildable"] & cond_mask
        levels = leg_levels_from_fracs(entry_close, rd, fav_dist, arm.leg_fracs)
        # ADV-NONE: pass an all-NaN adverse level so the shared-stop test never activates.
        adv_used = np.full_like(adv, np.nan) if arm.no_adverse else adv
        reversal = np.full(int(entry_idx.shape[0]), -1, dtype=np.int64)
        leg_px, leg_cls = resolve_legs(
            ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"],
            entry_idx, entry_close, rd, arm.leg_kinds, levels,
            reversal, adv_used, bench_n, pop_arm, ADV_FIXED, None, last_train_idx)
        r_all, qual = weighted_returns(
            leg_px, leg_cls, weights, entry_close, rd, atr_entry, pop_arm)
        r_firsthit = None
        censored = int((pop_arm & ~qual & np.isfinite(atr_entry) & (atr_entry > 0.0)).sum())
        adv_count = _adv_count_legs(leg_cls, qual)

    order = np.argsort(entry_idx[qual], kind="stable")
    r_e = r_all[qual][order]
    exit_w = exit_reason_weights(leg_cls, weights, qual)
    return _summarize_arm(r_e, r_all, qual, exit_w, r_firsthit, censored, adv_count,
                          int(pop.sum()), _rng(cell_index, pb["med"]),
                          _rng(cell_index, pb["mean"]), _rng(cell_index, pb["trim"]),
                          draw_count=0)


def matched_random_arm(
    obj: str, arm: ArmSpec, ohlc: dict[str, np.ndarray], state_all: InProgressState,
    seg: dict[str, np.ndarray], warmup_all: np.ndarray, atr_all: np.ndarray,
    signal_idx: np.ndarray, draw_count: int, cell_index: int, last_train_idx: int,
) -> ArmResult:
    """Matched-count random-in-MA-regime control through one arm's pipeline (P5).

    Draws ``draw_count`` entries from the eligible MA-regime pool excluding the
    object's own signal entries, then resolves through the identical arm exit
    machinery (same benchmark fav/adv/cap; ADV-NONE arm uses the all-NaN adverse).
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
        leg_cls = classes[:, None]
    else:
        levels = leg_levels_from_fracs(ohlc["close"][drawn], sub.rd, fav_d, arm.leg_fracs)
        adv_used = np.full_like(adv, np.nan) if arm.no_adverse else adv
        reversal = np.full(int(drawn.shape[0]), -1, dtype=np.int64)
        leg_px, leg_cls = resolve_legs(
            ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"],
            drawn, ohlc["close"][drawn], sub.rd, arm.leg_kinds, levels,
            reversal, adv_used, bench_n, base_pop, ADV_FIXED, None, last_train_idx)
        r_all, qual = weighted_returns(
            leg_px, leg_cls, weights, ohlc["close"][drawn], sub.rd, atr_all[drawn], base_pop)
        r_firsthit = None
        censored = int((base_pop & ~qual & np.isfinite(atr_all[drawn])
                        & (atr_all[drawn] > 0.0)).sum())
        adv_count = _adv_count_legs(leg_cls, qual)

    order = np.argsort(drawn[qual], kind="stable")
    r_e = r_all[qual][order]
    exit_w = exit_reason_weights(leg_cls, weights, qual)
    population = int(base_pop.sum())
    return _summarize_arm(r_e, r_all, qual, exit_w, r_firsthit, censored, adv_count,
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
    """MA(20,50) geometry context at the harami entries (EXP-060/061/066 construction)."""
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
    """ZigZag conditioned-signal context: the hybrid object's /STRONG-STAT mask (P12 check)."""
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
    last_train_idx = int(ohlc["close"].shape[0]) - 1

    zz = _zz_context(bars, ohlc, entry_idx, entry_epoch)
    cond_masks = {"nat": ma["stat"]["retained_p75"], "hyb": zz["retained_p75"]}
    arms = _resolve_objects(ohlc, ma, cond_masks, entry_idx, last_train_idx, cell_index)
    n_conditioned = {o: int((ma["buildable"] & cond_masks[o]).sum()) for o in OBJECTS}
    return {
        **base, "empty": False, "arms": arms,
        "n_conditioned": n_conditioned,
        "causality_ok": _causality_ok(ohlc, entry_idx, entry_epoch, ma, zz),
        "invariants": {o: _cell_invariants(arms[o], ma["fav_dist"], o) for o in OBJECTS},
    }


def _resolve_objects(
    ohlc: dict[str, np.ndarray], ma: dict[str, Any], cond_masks: dict[str, np.ndarray],
    entry_idx: np.ndarray, last_train_idx: int, cell_index: int,
) -> dict[str, Any]:
    """Resolve each object's arms (signal + matched-random) + contrasts.

    native: 3 binding champion arms. hybrid: BENCH only (P12 reconciliation check).
    """
    seg = ma["seg"]
    state_all = live_in_progress_state(ohlc["epoch"], ohlc["close"], seg["confirm_epoch"],
                                       seg["end_price"], seg["end_epoch"], seg["direction"])
    _, warmup_all = adaptive_time_caps_by_epoch(
        ohlc["epoch"], seg["confirm_epoch"], seg["confirm_idx"])
    arms: dict[str, Any] = {}
    for obj in OBJECTS:
        cond = cond_masks[obj]
        signal_idx = entry_idx[cond]
        signals: dict[str, ArmResult] = {}
        nulls: dict[str, ArmResult] = {}
        for aid in OBJECT_ARMS[obj]:
            arm = ARM_BY_ID[aid]
            signals[aid] = signal_arm(obj, arm, ohlc, ma, cond, entry_idx,
                                      last_train_idx, cell_index)
            nulls[aid] = matched_random_arm(
                obj, arm, ohlc, state_all, seg, warmup_all, ma["atr"],
                signal_idx, signals[aid].m, cell_index, last_train_idx)
        var_rm = {aid: contrast(signals[aid], nulls[aid]) for aid in OBJECT_ARMS[obj]}
        paired = {aid: paired_vs_bench(signals[aid], signals["BENCH"], cell_index,
                                       arm_pb(obj, aid)["paired"])
                  for aid in OBJECT_ARMS[obj] if aid != "BENCH"}
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
    arms_obj: dict[str, Any], fav_dist: np.ndarray, obj: str,
) -> dict[str, bool]:
    """Predeclared structural invariants for one object."""
    signals, nulls = arms_obj["signals"], arms_obj["nulls"]
    exit_ok = all(
        (res.m == 0) or abs(sum(res.exit_weights.values()) - 1.0) <= 1e-9
        for res in list(signals.values()) + list(nulls.values()))
    matched_ok = all(nulls[aid].draw_count == signals[aid].m for aid in OBJECT_ARMS[obj])
    q = signals["BENCH"].qual
    fav_pos = True
    if q.shape[0] and fav_dist.shape[0] == q.shape[0]:
        if bool((q & ~(fav_dist > 0.0)).any()):
            fav_pos = False
    # ADV-NONE invariant: the only stop is the MA cap -> zero adverse stop-outs.
    advnone_ok = True
    if "V2A-ADVNONE" in OBJECT_ARMS[obj]:
        advnone_ok = (signals["V2A-ADVNONE"].adv_count == 0
                      and nulls["V2A-ADVNONE"].adv_count == 0)
    return {"exit_ok": bool(exit_ok), "matched_count_ok": bool(matched_ok),
            "fav_dist_positive": bool(fav_pos), "advnone_no_stopout": bool(advnone_ok)}


# --------------------------------------------------------------------------- #
# Per-cell record flattening (one long row per cell x object x arm) + G-015 flags
# --------------------------------------------------------------------------- #
def _viable(res: ArmResult) -> bool:
    """Median CI_low(1s) > 0 AND m >= power floor (binding viability; G-015 (a))."""
    return bool(res.m >= POWER_FLOOR and res.ci_low_1s is not None
                and np.isfinite(res.ci_low_1s) and res.ci_low_1s > 0.0)


def _mean_positive(res: ArmResult) -> bool:
    """Raw-mean CI_low(1s) > 0 AND m >= power floor (P4 co-primary; G-015 (b))."""
    return bool(res.m >= POWER_FLOOR and res.mean_ci_low_1s is not None
                and np.isfinite(res.mean_ci_low_1s) and res.mean_ci_low_1s > 0.0)


def _beats_rm(c: dict[str, Any]) -> bool:
    """arm - own-object RM median contrast CI_low(1s) > 0 (P5; G-015 (c))."""
    return bool(np.isfinite(c["median_low_1s"]) and c["median_low_1s"] > 0.0)


def _beats_bench(p: dict[str, Any]) -> bool:
    low = p.get("paired_low_1s")
    return bool(low is not None and np.isfinite(low) and low > 0.0)


def arm_rows(instrument: str, cell: dict[str, Any]) -> list[dict[str, Any]]:
    """One long row per (cell, object, arm): signal stats, RM null, contrasts, G-015 flags."""
    rows: list[dict[str, Any]] = []
    for obj in OBJECTS:
        obj_arms = cell["arms"][obj]
        for aid in OBJECT_ARMS[obj]:
            arm = ARM_BY_ID[aid]
            sig = obj_arms["signals"][aid]
            null = obj_arms["nulls"][aid]
            c = obj_arms["var_rm"][aid]
            pair = obj_arms["paired"].get(aid, {})
            median_viable = _viable(sig)
            mean_positive = _mean_positive(sig)
            beats_rm = _beats_rm(c)
            beats_bench = (not arm.is_bench) and _beats_bench(pair)
            win_mean = _winsorized_mean(sig.r_e) if sig.m > 0 else None
            winsorized_mean_positive = bool(
                sig.m >= POWER_FLOOR and win_mean is not None and win_mean > 0.0)
            # G-015 conjunction (binding): median AND mean AND beats-RM, simultaneously.
            g015_passes = bool(median_viable and mean_positive and beats_rm)
            # S3 EVIDENCE_FOR criterion (disclosed, for comparison with EXP-066).
            s3_evidence_for = bool(not arm.is_bench and median_viable and beats_rm and beats_bench)
            # P4 closure diagnostics (disclosed).
            trim_hi = sig.trim_ci_hi_2s
            trimmed_mean_negative = bool(trim_hi is not None and np.isfinite(trim_hi)
                                         and trim_hi < 0.0)
            tail = sig.tail_share_worst5
            tail_driven = bool(tail is not None and np.isfinite(tail)
                               and tail > TAIL_DRIVEN_THRESHOLD)
            mean_negative_pt = bool(sig.mean is not None and sig.mean < 0.0)
            gap = (sig.median - sig.mean) if (sig.median is not None
                                              and sig.mean is not None) else None
            low_n_4h = bool(cell["domain"] == "4h" and sig.m < LOW_N_4H)
            rows.append({
                "instrument": instrument, "domain": cell["domain"], "object": obj,
                "binding": (obj == BINDING_OBJECT), "arm": aid, "arm_model": ARM_MODEL[aid],
                "is_bench": arm.is_bench, "is_champion": (aid in CHAMPION_ARMS),
                "member": True, "excluded": False,
                "n_harami": cell["n_harami"], "n_conditioned": cell["n_conditioned"][obj],
                "m": sig.m, "population": sig.population, "data_censored": sig.data_censored,
                "adv_count": sig.adv_count,
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
                "median_viable": median_viable, "mean_positive": mean_positive,
                "beats_rm": beats_rm, "beats_bench": beats_bench,
                "g015_passes": g015_passes, "s3_evidence_for": s3_evidence_for,
                "trimmed_mean_negative": trimmed_mean_negative, "tail_driven": tail_driven,
                "mean_negative_pt": mean_negative_pt, "low_n_4h": low_n_4h,
                "winsorized_mean": win_mean, "winsorized_mean_positive": winsorized_mean_positive,
                **{f"ew_{label}": sig.exit_weights[label] for label in PX_CLASS_LABELS.values()},
            })
    return rows


def excluded_rows(instrument: str, domain: str) -> list[dict[str, Any]]:
    """COVERAGE_EXCLUDED / empty-cell placeholder rows (one per object x arm)."""
    rows = []
    for obj in OBJECTS:
        for aid in OBJECT_ARMS[obj]:
            arm = ARM_BY_ID[aid]
            rows.append({
                "instrument": instrument, "domain": domain, "object": obj,
                "binding": (obj == BINDING_OBJECT), "arm": aid, "arm_model": ARM_MODEL[aid],
                "is_bench": arm.is_bench, "is_champion": (aid in CHAMPION_ARMS),
                "member": False, "excluded": True,
                "n_harami": None, "n_conditioned": None,
                "m": 0, "median": None, "mean": None, "trimmed_mean": None,
                "tail_share_worst5": None, "median_viable": False, "mean_positive": False,
                "beats_rm": False, "beats_bench": False, "g015_passes": False,
                "s3_evidence_for": False, "trimmed_mean_negative": False, "tail_driven": False,
                "mean_negative_pt": False, "low_n_4h": False,
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
        for k in ("exit_ok", "matched_count_ok", "fav_dist_positive", "advnone_no_stopout"):
            row[f"{obj}_{k}"] = io.get(k, True)
            all_ok = all_ok and io.get(k, True)
    row["construction_pass"] = bool(all_ok)
    return row


# --------------------------------------------------------------------------- #
# Composition + G-015 conjunction readout (P11 with the P6 non-4h rule; native binding)
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


def _arm_tally(obj_rows: list[dict[str, Any]], aid: str) -> dict[str, Any]:
    """Per-arm P11/P6 tallies for every G-015 criterion + the disclosed flags."""
    vr = [r for r in obj_rows if r["arm"] == aid]
    powered = _p11([r for r in vr if r["m"] >= POWER_FLOOR
                    and (r.get("rm_m") or 0) >= POWER_FLOOR], "median_viable")
    return {
        "median_viable": _p11(vr, "median_viable"),
        "mean_positive": _p11(vr, "mean_positive"),
        "winsorized_mean_positive": _p11(vr, "winsorized_mean_positive"),
        "beats_rm": _p11(vr, "beats_rm"),
        "beats_bench": _p11(vr, "beats_bench"),
        "g015_passes": _p11(vr, "g015_passes"),
        "s3_evidence_for": _p11(vr, "s3_evidence_for"),
        "powered": powered,
    }


def _p4_closure(obj_rows: list[dict[str, Any]], aid: str) -> dict[str, Any]:
    """P4 closure-rule mechanical classification over one arm's powered cells (disclosed).

    STRUCTURAL: trimmed mean also negative AND tail-share <= 0.40 in the majority of
    powered cells. TAIL_DRIVEN: tail-share > 0.40 in the majority. PARTIAL_RECOVERY:
    mean-positive cells exist but do not compose with median+RM. Used only when the
    G-015 conjunction fails; final adjudication is the gate (results.md).
    """
    powered = [r for r in obj_rows if r["arm"] == aid and r["m"] >= POWER_FLOOR]
    n = len(powered)
    if n == 0:
        return {"arm": aid, "n_powered": 0, "classification": "NO_POWERED_CELLS"}
    structural = sum(1 for r in powered
                     if r.get("trimmed_mean_negative") and not r.get("tail_driven"))
    tail_driven = sum(1 for r in powered if r.get("tail_driven"))
    mean_neg = sum(1 for r in powered if r.get("mean_negative_pt"))
    mean_pos = sum(1 for r in powered if r.get("mean_positive"))
    if tail_driven > n / 2.0:
        classification = "TAIL_DRIVEN"
    elif structural > n / 2.0:
        classification = "STRUCTURAL"
    elif mean_pos > 0:
        classification = "PARTIAL_RECOVERY"
    else:
        classification = "MIXED"
    return {"arm": aid, "n_powered": n, "n_structural": structural,
            "n_tail_driven": tail_driven, "n_mean_negative_pt": mean_neg,
            "n_mean_positive": mean_pos, "classification": classification}


def g015_readout(rows: list[dict[str, Any]], defect: dict[str, Any]) -> dict[str, Any]:
    """Native G-015 conjunction readout (binding object) + disclosed hybrid context.

    MECHANICAL ONLY -- G-015 is adjudicated at the single terminal gate after the full
    Phase 015 slate (results.md). No closure or candidate registration here (P9).
    """
    member = [r for r in rows if not r.get("excluded")]
    nat_rows = [r for r in member if r["object"] == "nat"]
    per_arm = {aid: _arm_tally(nat_rows, aid) for aid in OBJECT_ARMS["nat"]}
    p4 = {aid: _p4_closure(nat_rows, aid) for aid in CHAMPION_ARMS}

    powered = any(per_arm[aid]["powered"]["composes"] for aid in CHAMPION_ARMS)
    g015_arms = [aid for aid in CHAMPION_ARMS if per_arm[aid]["g015_passes"]["composes"]]
    s3_arms = [aid for aid in CHAMPION_ARMS if per_arm[aid]["s3_evidence_for"]["composes"]]
    mechanical = _mechanical_readout(defect, powered, g015_arms, s3_arms, per_arm, p4)

    return {
        "deliverable": "NATIVE_COMBINED_CHAMPION_G015_INPUT",
        "binding_note": ("MECHANICAL readout only. The single terminal G-015 gate adjudicates "
                         "after the full Phase 015 slate (results.md). No closure or candidate "
                         "registration here (P9). Native is the binding object; hybrid BENCH is "
                         "a P12 reconciliation check only."),
        "mechanical_native_readout": mechanical,
        "champion_arms": CHAMPION_ARMS,
        "any_champion_g015_composes": bool(g015_arms),
        "g015_composing_arms": g015_arms,
        "s3_evidence_for_arms": s3_arms,
        "native_per_arm": per_arm,
        "p4_closure_per_champion": p4,
        "conjunction_rule": _rule_text(),
        "g015_routing": _routing_text(),
        "disclosed_hybrid": _disclosed_hybrid(member),
        "defect": defect,
    }


def _mechanical_readout(
    defect: dict[str, Any], powered: bool, g015_arms: list[str], s3_arms: list[str],
    per_arm: dict[str, Any], p4: dict[str, Any],
) -> str:
    """Mechanical (non-binding) native classification mirroring the scope Success/Failure."""
    if defect["is_defect"]:
        return "SUBSTRATE_METHOD_DEFECT"
    if not powered:
        return "INCONCLUSIVE_POWER_LIMITED"
    if g015_arms:
        return "PROCEED_TO_SCREEN_CANDIDATE"
    if s3_arms:
        # Surface-positive (S3 EVIDENCE_FOR) but the mean co-primary fails the conjunction.
        classes = {p4[aid]["classification"] for aid in s3_arms}
        if "TAIL_DRIVEN" in classes or "PARTIAL_RECOVERY" in classes:
            return "MEAN_RECOVERABLE_FOLLOW_UP_CANDIDATE"
        return "EVIDENCE_FOR_SURFACE_ONLY"
    classes = {p4[aid]["classification"] for aid in CHAMPION_ARMS}
    if "STRUCTURAL" in classes and "TAIL_DRIVEN" not in classes:
        return "CHARACTERISED_NOT_VIABLE_CANDIDATE"
    if "TAIL_DRIVEN" in classes or "PARTIAL_RECOVERY" in classes:
        return "MEAN_RECOVERABLE_FOLLOW_UP_CANDIDATE"
    return "CHARACTERISED_NOT_VIABLE_CANDIDATE"


def _disclosed_hybrid(member: list[dict[str, Any]]) -> dict[str, Any]:
    """Disclosed hybrid context: the EXP-061-066 surface summary + EXP-067 status."""
    exp067 = (EXPERIMENTS_ROOT / "EXP-067" / "results" / "g015_verdict.json")
    exp067_status = "AVAILABLE" if exp067.exists() else "PENDING (EXP-067 not yet run)"
    return {
        "note": ("Hybrid is NOT a binding measurement object in EXP-068 (that role is EXP-067). "
                 "Never pooled with native."),
        "surface_summary_EXP061_066": {
            "L1_EXP061": "EVIDENCE_AGAINST (H0: 1 cell)",
            "S1_EXP064": "EVIDENCE_AGAINST (0/7 variants)",
            "S2_EXP065": "INCONCLUSIVE (power-limited)",
            "S3_EXP066": "EVIDENCE_AGAINST (0 arms at P11)",
            "dominant": "EVIDENCE_AGAINST",
        },
        "EXP067_hybrid_combined_champion": exp067_status,
        "hyb_bench_p12_check_only": True,
    }


def _rule_text() -> str:
    return ("Native binding object only (hybrid is a P12 check). G-015 conjunction per cell "
            "(m>=30): g015_passes = median CI_low(1s)>0 AND raw-mean CI_low(1s)>0 AND "
            "(arm - RM-native) independent-contrast median CI_low(1s)>0, simultaneously. "
            "Composed at P11+P6 (>=5 cells / >=3 instruments / >=3 cells outside 4h). "
            "PROCEED_TO_SCREEN iff a champion arm (PARTIAL-V2A or V2A-ADVNONE) composes the "
            "conjunction. Disclosed: S3 EVIDENCE_FOR (median_viable AND beats_rm AND beats_bench), "
            "the P4 trimmed-mean/tail-share closure inputs. Reference BENCH = single-leg "
            "0.50*M_sofar fav / 1:1 stop / MA cap.")


def _routing_text() -> str:
    return ("Feeds the single terminal G-015 after the full Phase 015 slate (no closure or "
            "candidate registration here, P9), judged per object individually. A champion arm "
            "satisfying the full conjunction => G-015 PROCEED_TO_SCREEN candidate (registers the "
            "first candidate slot at the gate). Otherwise CHARACTERISED_NOT_VIABLE or "
            "MEAN_RECOVERABLE-FOLLOW-UP per the P4 closure structure. Hybrid disclosed from "
            "EXP-061-066 / EXP-067, never pooled.")


# --------------------------------------------------------------------------- #
# Determinism replay + reconciliation (DEFECT guards)
# --------------------------------------------------------------------------- #
def determinism_replay(train_1m: pl.DataFrame, domain: str, train_end_epoch: int,
                       cell_index: int) -> bool:
    """Re-run one cell end-to-end and assert byte-identical binding outputs (all arms)."""
    a = compute_cell(train_1m, domain, train_end_epoch, cell_index)
    b = compute_cell(train_1m, domain, train_end_epoch, cell_index)
    if a.get("empty") or b.get("empty"):
        return a.get("empty") == b.get("empty")
    for obj in OBJECTS:
        for aid in OBJECT_ARMS[obj]:
            for side in ("signals", "nulls"):
                sa, sb = a["arms"][obj][side][aid], b["arms"][obj][side][aid]
                if not (np.array_equal(sa.r_e, sb.r_e)
                        and (sa.median, sa.ci_low_1s, sa.mean_ci_low_1s, sa.trim_ci_low_1s)
                        == (sb.median, sb.ci_low_1s, sb.mean_ci_low_1s, sb.trim_ci_low_1s)):
                    return False
            ca, cb = a["arms"][obj]["var_rm"][aid], b["arms"][obj]["var_rm"][aid]
            if not (_nan_eq(ca["median_low_1s"], cb["median_low_1s"])
                    and _nan_eq(ca["mean_low_1s"], cb["mean_low_1s"])):
                return False
    return True


def _nan_eq(a: float | None, b: float | None) -> bool:
    if a is None or b is None:
        return a is b
    return bool(a == b or (np.isnan(a) and np.isnan(b)))


def reconciliation(
    instrument: str, cell: dict[str, Any],
    anchor061: dict[tuple[str, str], dict[str, Any]],
    anchor066: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    """P12 reproduction guards: nat BENCH<->EXP-061 M0; hyb BENCH<->EXP-061 H0;
    nat PARTIAL-V2A<->EXP-066 native PARTIAL-V2A."""
    key = (instrument, cell["domain"])
    have_any = bool(anchor061) and bool(anchor066)
    if not have_any or cell.get("empty"):
        return {"checked": False, "cell": f"{instrument}-{cell.get('domain')}"}
    out: dict[str, Any] = {"checked": True, "cell": f"{instrument}-{cell['domain']}"}
    consistent = True
    # BENCH anchors (M0 native / H0 hybrid) from EXP-061.
    src061 = anchor061.get(key, {})
    for obj in OBJECTS:
        label = OBJECT_BENCH_LABEL[obj]
        anc = src061.get(label)
        bench = cell["arms"][obj]["signals"]["BENCH"]
        if anc is None:
            out[f"{obj}_bench_checked"] = False
            consistent = False
            continue
        m_ok = bench.m == (int(anc["m"]) if anc.get("m") is not None else 0)
        med_ok = _float_match(bench.median, anc.get("median"))
        out.update({f"{obj}_bench_checked": True, f"{obj}_bench_m": bench.m,
                    f"{obj}_bench_exp061_m": anc.get("m"), f"{obj}_bench_median": bench.median,
                    f"{obj}_bench_exp061_median": anc.get("median"),
                    f"{obj}_bench_m_match": bool(m_ok), f"{obj}_bench_median_match": bool(med_ok)})
        consistent = consistent and m_ok and med_ok
    # Native PARTIAL-V2A anchor from EXP-066.
    anc066 = anchor066.get(key)
    nat_partial = cell["arms"]["nat"]["signals"]["PARTIAL-V2A"]
    if anc066 is None:
        out["nat_partial_checked"] = False
        consistent = False
    else:
        m_ok = nat_partial.m == (int(anc066["m"]) if anc066.get("m") is not None else 0)
        med_ok = _float_match(nat_partial.median, anc066.get("median"))
        out.update({"nat_partial_checked": True, "nat_partial_m": nat_partial.m,
                    "nat_partial_exp066_m": anc066.get("m"),
                    "nat_partial_median": nat_partial.median,
                    "nat_partial_exp066_median": anc066.get("median"),
                    "nat_partial_m_match": bool(m_ok), "nat_partial_median_match": bool(med_ok)})
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
# Plotting (bounded; from collected per-cell summaries -- no reloads), native object
# --------------------------------------------------------------------------- #
def _placeholder(ax: plt.Axes, message: str) -> None:
    ax.text(0.5, 0.5, message, ha="center", va="center")
    ax.axis("off")


def _nat_cells(rows: list[dict[str, Any]], aid: str) -> list[dict[str, Any]]:
    return [r for r in rows if not r.get("excluded") and r["object"] == "nat"
            and r["arm"] == aid]


def plot_median_forest(rows: list[dict[str, Any]], save_path: Path) -> None:
    """Per-cell native median expectancy + 95% CI for the 3 champion arms (headline)."""
    fig, ax = plt.subplots(figsize=(15, 7))
    cmap = {"BENCH": "#7f7f7f", "PARTIAL-V2A": "#1f77b4", "V2A-ADVNONE": "#ff7f0e"}
    markers = {"BENCH": "o", "PARTIAL-V2A": "s", "V2A-ADVNONE": "^"}
    any_data = False
    for aid in OBJECT_ARMS["nat"]:
        cells = sorted([r for r in _nat_cells(rows, aid) if r.get("median") is not None],
                       key=lambda r: (r["instrument"], r["domain"]))
        if not cells:
            continue
        any_data = True
        x = np.arange(len(cells))
        med = np.array([r["median"] for r in cells], dtype=float)
        # 95% bootstrap CI error bars (two-sided bounds; clipped to finite).
        lo = np.array([r["ci_lo_2s"] if r.get("ci_lo_2s") is not None else r["median"]
                       for r in cells], dtype=float)
        hi = np.array([r["ci_hi_2s"] if r.get("ci_hi_2s") is not None else r["median"]
                       for r in cells], dtype=float)
        yerr = np.vstack([np.clip(med - lo, 0.0, None), np.clip(hi - med, 0.0, None)])
        g015 = [r.get("g015_passes") for r in cells]
        ax.errorbar(x, med, yerr=yerr, fmt=markers[aid], ms=4, color=cmap[aid],
                    ecolor=cmap[aid], elinewidth=0.5, capsize=0, alpha=0.8, label=aid)
        # Mark cells passing the full G-015 conjunction with a black ring.
        gx = [i for i, g in enumerate(g015) if g]
        if gx:
            ax.scatter(gx, [med[i] for i in gx], s=70, facecolors="none",
                       edgecolors="k", linewidths=1.0, zorder=5)
    if not any_data:
        _placeholder(ax, "native: no powered cells")
    else:
        ax.axhline(0.0, color="k", lw=0.8, ls="--")
        ax.set_xlabel("cell index (sorted by instrument-domain)")
        ax.set_ylabel("per-cell median expectancy (ATR units)")
        ax.legend(title="arm (black ring = G-015 conjunction cell)", fontsize=8)
    ax.set_title(f"{EXPERIMENT_ID}: native champion-arm median expectancy per cell")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_contrast_heatmap(rows: list[dict[str, Any]], save_path: Path) -> None:
    """arm - RM-native contrast CI_low across the 3 native arms x cells; G-015 overlay."""
    aids = OBJECT_ARMS["nat"]
    cell_keys = sorted({f"{r['instrument']}-{r['domain']}" for r in rows
                        if not r.get("excluded") and r["object"] == "nat"})
    fig, ax = plt.subplots(figsize=(18, 4.5))
    if not cell_keys:
        _placeholder(ax, "native: no member cells")
    else:
        matrix = np.full((len(aids), len(cell_keys)), np.nan)
        g015 = np.zeros((len(aids), len(cell_keys)), dtype=bool)
        for ri, aid in enumerate(aids):
            lut = {f"{r['instrument']}-{r['domain']}": r for r in _nat_cells(rows, aid)}
            for ci, ck in enumerate(cell_keys):
                r = lut.get(ck)
                if r is not None:
                    v = r.get("var_rm_median_low_1s")
                    matrix[ri, ci] = v if (v is not None and np.isfinite(v)) else np.nan
                    g015[ri, ci] = bool(r.get("g015_passes"))
        vmax = np.nanmax(np.abs(matrix)) if np.isfinite(matrix).any() else 1.0
        im = ax.imshow(matrix, cmap="RdYlGn", vmin=-vmax, vmax=vmax, aspect="auto")
        for ri in range(len(aids)):
            for ci in range(len(cell_keys)):
                if g015[ri, ci]:
                    ax.text(ci, ri, "*", ha="center", va="center", fontsize=8, color="k")
        ax.set_yticks(range(len(aids)), aids, fontsize=8)
        non4 = ["#" if not ck.endswith("-4h") else "" for ck in cell_keys]
        ax.set_xticks(range(len(cell_keys)),
                      [f"{m}{ck}" for m, ck in zip(non4, cell_keys)], rotation=90, fontsize=3)
        ax.set_title(f"{EXPERIMENT_ID}: arm - RM-native median contrast CI_low "
                     "(# = non-4h; * = G-015 conjunction cell)")
        fig.colorbar(im, ax=ax, fraction=0.02)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_median_vs_mean(rows: list[dict[str, Any]], save_path: Path) -> None:
    """P4 co-primary: per-cell median vs raw mean vs trimmed mean, one panel per arm."""
    aids = OBJECT_ARMS["nat"]
    fig, axes = plt.subplots(1, len(aids), figsize=(16, 5.5), sharey=True)
    colour = {True: "#1a9850", False: "#d73027"}
    for ax, aid in zip(np.atleast_1d(axes), aids):
        cells = sorted([r for r in _nat_cells(rows, aid) if r.get("mean") is not None],
                       key=lambda r: r["mean"])
        if not cells:
            _placeholder(ax, f"{aid}: no powered cells")
            continue
        x = np.arange(len(cells))
        size = [200.0 * (r.get("tail_share_worst5") or 0.0) + 8.0 for r in cells]
        cols = [colour[bool(r.get("g015_passes"))] for r in cells]
        ax.scatter(x, [r["mean"] for r in cells], c=cols, s=size, label="raw mean", zorder=3)
        ax.scatter(x, [r.get("trimmed_mean") if r.get("trimmed_mean") is not None else np.nan
                       for r in cells], facecolors="none", edgecolors="#4575b4", s=22,
                   label="10% trimmed mean", zorder=2)
        ax.scatter(x, [r.get("median") if r.get("median") is not None else np.nan
                       for r in cells], c="k", s=8, marker="_", label="median", zorder=1)
        ax.axhline(0.0, color="k", lw=0.8, ls="--")
        ax.set_title(f"native {aid}")
        ax.set_xlabel("cell (sorted by raw mean)")
        ax.legend(fontsize=7)
    axes[0].set_ylabel("per-cell expectancy (ATR units)")
    fig.suptitle(f"{EXPERIMENT_ID} P4 co-primary: median vs raw/trimmed mean "
                 "(green=G-015 pass; size=worst-5% tail-share)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_g015_summary(readout: dict[str, Any], save_path: Path) -> None:
    """Per-arm P11+P6 criterion tallies (median / mean / beats-RM / S3 / G-015 conjunction)."""
    aids = OBJECT_ARMS["nat"]
    flags = ["median_viable", "mean_positive", "beats_rm", "beats_bench",
             "s3_evidence_for", "g015_passes"]
    per_arm = readout["native_per_arm"]
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(flags))
    width = 0.25
    for i, aid in enumerate(aids):
        counts = [per_arm[aid][f]["n_cells"] for f in flags]
        bars = ax.bar(x + (i - 1) * width, counts, width, label=aid)
        for b, f in zip(bars, flags):
            composes = per_arm[aid][f]["composes"]
            ax.text(b.get_x() + b.get_width() / 2.0, b.get_height() + 0.2,
                    f"{int(b.get_height())}{'*' if composes else ''}",
                    ha="center", va="bottom", fontsize=7)
    ax.axhline(P11_MIN_CELLS, color="k", lw=0.8, ls="--", label=f"P11 quorum ({P11_MIN_CELLS})")
    ax.set_xticks(x, flags, rotation=20, fontsize=8)
    ax.set_ylabel("number of qualifying cells")
    ax.set_title(f"{EXPERIMENT_ID}: native per-arm P11+P6 criterion tally "
                 "(* = composes P11+P6 non-4h)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def make_plots(rows: list[dict[str, Any]], readout: dict[str, Any]) -> None:
    """Render the four bounded native plots from collected per-cell summaries."""
    plot_median_forest(rows, PLOTS_DIR / "native_median_forest.png")
    plot_contrast_heatmap(rows, PLOTS_DIR / "native_arm_rm_contrast_heatmap.png")
    plot_median_vs_mean(rows, PLOTS_DIR / "native_median_vs_mean_p4.png")
    plot_g015_summary(readout, PLOTS_DIR / "native_g015_conjunction_summary.png")


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _cell_index_map() -> dict[tuple[str, str], int]:
    """Stable (instrument, domain) -> int index (identical to EXP-060/061/066)."""
    return {(inst, dom): i for i, (inst, dom) in enumerate(
        (inst, dom) for inst in INSTRUMENTS for dom in DOMAINS)}


def process_instrument(
    instrument: str, anchor061: dict[tuple[str, str], dict[str, Any]],
    anchor066: dict[tuple[str, str], dict[str, Any]],
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
            out["recon_rows"].append(reconciliation(instrument, cell, anchor061, anchor066))
            continue
        out["rows"].extend(arm_rows(instrument, cell))
        out["readiness"].append(readiness_row(instrument, cell))
        out["recon_rows"].append(reconciliation(instrument, cell, anchor061, anchor066))
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
    keys = ("exit_ok", "matched_count_ok", "fav_dist_positive", "advnone_no_stopout")
    bad = any(not all(inv.get(o, {}).get(k, True) for k in keys) for o in OBJECTS)
    if bad:
        out["invariant_violations"].append(label)


def _run_grid(
    anchor061: dict[tuple[str, str], dict[str, Any]],
    anchor066: dict[tuple[str, str], dict[str, Any]], workers: int,
) -> list[dict[str, Any]]:
    """Resolve all instruments (process pool if workers>1) in fixed order."""
    if workers <= 1:
        return [process_instrument(inst, anchor061, anchor066)
                for inst in tqdm(INSTRUMENTS, desc="instruments")]
    by_inst: dict[str, dict[str, Any]] = {}
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(process_instrument, inst, anchor061, anchor066): inst
                   for inst in INSTRUMENTS}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="instruments"):
            by_inst[futures[fut]] = fut.result()
    return [by_inst[inst] for inst in INSTRUMENTS]


def run(workers: int = 1) -> dict[str, Any]:
    """Run all member cells and write artifacts. Returns the run summary.

    Output is byte-identical for any ``workers`` value.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    anchor061 = load_exp061_bench()
    anchor066 = load_exp066_partial()
    workers = max(1, min(workers, len(INSTRUMENTS)))
    grid = _run_grid(anchor061, anchor066, workers)
    rows: list[dict[str, Any]] = []
    readiness: list[dict[str, Any]] = []
    recon_rows: list[dict[str, Any]] = []
    instrument_meta: dict[str, Any] = {}
    defect = {"is_defect": False, "non_deterministic": [], "recon_mismatch": [],
              "causality_violations": [], "determinism_checked": [],
              "invariant_violations": [],
              "exp061_available": bool(anchor061), "exp066_available": bool(anchor066),
              "recon_checked_cells": 0, "workers": workers}
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
    readout = g015_readout(rows, defect)
    write_outputs(rows, readiness, recon_rows, readout, instrument_meta, defect)
    make_plots(rows, readout)
    return _summarize(rows, readout)


def _finalize_defects(defect: dict[str, Any], recon_rows: list[dict[str, Any]]) -> None:
    defect["recon_mismatch"] = [r["cell"] for r in recon_rows
                                if r.get("checked") and not r["consistent"]]
    if defect["recon_mismatch"]:
        defect["is_defect"] = True
    defect["recon_checked_cells"] = sum(1 for r in recon_rows if r.get("checked"))
    if not defect["exp061_available"] or not defect["exp066_available"] \
            or defect["recon_checked_cells"] == 0:
        defect["is_defect"] = True
    causal_instr = {c.split("-")[0] for c in defect["causality_violations"]}
    if len(causal_instr) >= P11_MIN_INSTR:
        defect["is_defect"] = True
    if defect["invariant_violations"]:
        defect["is_defect"] = True
    if defect["non_deterministic"]:
        defect["is_defect"] = True


def write_outputs(
    rows: list[dict[str, Any]], readiness: list[dict[str, Any]],
    recon_rows: list[dict[str, Any]], readout: dict[str, Any],
    instrument_meta: dict[str, Any], defect: dict[str, Any],
) -> None:
    """Persist the per-cell parquet, champion / secondary maps, reconciliation, and JSON."""
    pl.DataFrame(rows, strict=False).write_parquet(RESULTS_DIR / "per_cell_expectancy.parquet")
    member = [r for r in rows if not r.get("excluded")]
    nat_member = [r for r in member if r["object"] == "nat"]
    champion_cols = [
        "instrument", "domain", "object", "arm", "arm_model", "is_bench", "is_champion", "m",
        "median", "ci_low_1s", "mean", "mean_ci_low_1s", "trimmed_mean", "tail_share_worst5",
        "median_viable", "mean_positive", "beats_rm", "beats_bench", "g015_passes",
        "s3_evidence_for", "trimmed_mean_negative", "tail_driven",
        "var_rm_median_low_1s", "var_bench_paired_low_1s", "paired_n_common",
        "data_censored", "adv_count", "low_n_4h",
    ]
    _write_csv([{k: r.get(k) for k in champion_cols} for r in nat_member],
               RESULTS_DIR / "champion_map.csv")
    _write_csv(_build_secondary_map(member), RESULTS_DIR / "secondary_map.csv")
    _write_csv(readiness, RESULTS_DIR / "readiness.csv")
    recon_clean = [r for r in recon_rows if r.get("checked")]
    _write_csv(recon_clean, RESULTS_DIR / "reconciliation.csv")
    with open(RESULTS_DIR / "g015_verdict.json", "w") as fh:
        json.dump(readout, fh, indent=2, default=str)
    _write_metadata(instrument_meta, defect, recon_clean, readout)


def _build_secondary_map(member: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """BENCH r + exit-reason composition + P4 tail/trim per arm per object (incl. hyb check)."""
    ew_labels = list(PX_CLASS_LABELS.values())
    out = []
    for r in member:
        row: dict[str, Any] = {
            "instrument": r["instrument"], "domain": r["domain"],
            "object": r["object"], "binding": r.get("binding"), "arm": r["arm"],
            "m": r.get("m"), "median": r.get("median"), "mean": r.get("mean"),
            "trimmed_mean": r.get("trimmed_mean"),
            "tail_share_worst5": r.get("tail_share_worst5"),
            "r_firsthit": r.get("r_firsthit"),
            "data_censored": r.get("data_censored"), "adv_count": r.get("adv_count"),
        }
        for label in ew_labels:
            row[f"ew_{label}"] = r.get(f"ew_{label}")
        out.append(row)
    return out


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
        "phase": "015", "surface": "S4/native", "hypothesis": "HYP-021",
        "family": "CF-HA-HARAMI-001",
        "checkpoint": "2026-06-17-015-ma-substrate-conditioned-harami-full-surface",
        "amendment": "D0-amendment-001-dual-parallel-substrate (2026-06-17)",
        "title": "MA(20,50)-substrate native combined champion (merges old N1+N2); mirrors EXP-060",
        "conditioning_objects": OBJECT_NAME,
        "binding_object": BINDING_OBJECT,
        "stratum": "TRAIN-only (first 49%); nested TEST + final-30% holdout sealed",
        "population": ("native byte-identical to EXP-060B/061 M0 (8360-class); hybrid mask "
                       "byte-identical to EXP-053/060/061 H0 (3202-class); never pooled; "
                       "hybrid is a P12 check only, not binding"),
        "entry_anchor": "harami confirmation-bar real close (every signal arm)",
        "binding_endpoint": ("median per-event gross ATR-normalised return (P3/P14, P15 fills) "
                             "AND raw mean (P4 co-primary, binding in the G-015 conjunction); "
                             "10% trimmed mean + worst-5% tail-share disclosed (P4 closure rule)"),
        "arms": ARM_MODEL,
        "champion_arms": CHAMPION_ARMS,
        "reference_arm": "BENCH = single-leg 0.50*M_sofar fav / 1:1 stop / MA adaptive cap",
        "advnone_implementation": ("V2A-ADVNONE passes an all-NaN adverse level to resolve_legs; "
                                   "the shared-stop test in _scan_event never activates, so the "
                                   "only exits are the leg favourable targets (PX_FAV), the MA cap "
                                   "bar real close (PX_TIMECAP), or PX_DATA_CENSORED (TRAIN-edge "
                                   "truncation). No xen/ module changed."),
        "third_barrier": "MA-defined adaptive cap (k=1.5, window=20, floor=6, median, min_moves=5)",
        "g015_conjunction": ("per cell (m>=30): median CI_low(1s)>0 AND raw-mean CI_low(1s)>0 AND "
                             "(arm - RM-native) median contrast CI_low(1s)>0, simultaneously; "
                             "composed at P11 + P6 non-4h (>=5 cells / >=3 instruments / >=3 "
                             "non-4h cells). Champion arms: PARTIAL-V2A, V2A-ADVNONE."),
        "params": {
            "atr_period": ATR_PERIOD, "atr_mult_zigzag": ATR_MULT,
            "ma_segmentation": [MA_FAST, MA_SLOW], "favourable_fraction_bench": 0.50,
            "adverse_bench": "1:1 (BENCH, PARTIAL-V2A); none (V2A-ADVNONE)",
            "timecap_floor_bench": 6, "timecap_k": 1.5, "timecap_window": 20,
            "timecap_min_moves": 5, "power_floor": POWER_FLOOR, "low_n_4h_threshold": LOW_N_4H,
            "trim_frac": TRIM_FRAC, "tail_frac": TAIL_FRAC,
            "tail_driven_threshold": TAIL_DRIVEN_THRESHOLD,
            "n_boot": N_BOOT, "boot_batch": BOOT_BATCH, "base_seed": BASE_SEED,
            "p11": [P11_MIN_CELLS, P11_MIN_INSTR], "p6_min_non_4h": P6_MIN_NON_4H,
        },
        "statistical_methods": [
            "per-cell median CI (bootstrap_median_distribution + median_ci) -- binding, per arm",
            "per-cell raw mean + 10% trimmed mean CI (bootstrap_stat_distribution) + worst-5% "
            "tail-share -- P4 co-primary (raw mean binding in G-015), per arm",
            "independent bootstrap contrast arm - RM-native median (contrast_ci) -- binding "
            "signal attribution (P5), per arm",
            "arm - BENCH paired-median contrast (paired_median_contrast_ci, common qualifying "
            "subset) -- disclosed secondary (S3 EVIDENCE_FOR comparison), per champion arm",
        ],
        "mechanical_native_readout": readout["mechanical_native_readout"],
        "any_champion_g015_composes": readout["any_champion_g015_composes"],
        "g015_composing_arms": readout["g015_composing_arms"],
        "native_per_arm_composition": {
            aid: {f: readout["native_per_arm"][aid][f]["composes"]
                  for f in ("median_viable", "mean_positive", "beats_rm", "beats_bench",
                            "s3_evidence_for", "g015_passes")}
            for aid in OBJECT_ARMS["nat"]
        },
        "parallelism": {
            "workers": defect.get("workers", 1),
            "model": ("per-instrument ProcessPoolExecutor; results reassembled in fixed "
                      "INSTRUMENTS order; per-process native threads pinned to 1. Output is "
                      "byte-identical across worker counts: every RNG is seeded by "
                      "(BASE_SEED, cell_index, purpose), OHLC aggregation is order-independent, "
                      "and the merge order is fixed. The first usable native cell per instrument "
                      "is replayed byte-identically."),
        },
        "determinism_ok": not defect["non_deterministic"],
        "determinism_checked": defect["determinism_checked"],
        "causality_ok": not defect["causality_violations"],
        "causality_violations": defect["causality_violations"],
        "invariant_violations": defect["invariant_violations"],
        "invariant_gates": ("per object: each arm's exit-reason weights sum to 1.0 (finite "
                            "real-bar P15 resolution); matched-count holds (each null draw target "
                            "== its arm's signal qualifying m); fav_dist > 0 for every counted "
                            "BENCH event; ADV-NONE has zero adverse stop-outs (MA cap is the only "
                            "stop). Reconciliation (SUBSTRATE/METHOD_DEFECT): native BENCH "
                            "reproduces EXP-061 M0, hybrid BENCH reproduces EXP-061 H0, native "
                            "PARTIAL-V2A reproduces EXP-066 native PARTIAL-V2A -- per-cell m + "
                            "median to 1e-9; a missing anchor is a defect."),
        "reconciliation_rows": recon_clean,
        "recon_mismatch": defect["recon_mismatch"],
        "exp061_available": defect["exp061_available"],
        "exp066_available": defect["exp066_available"],
        "recon_checked_cells": defect["recon_checked_cells"],
        "exp061_anchor": str(EXP061_PARQUET),
        "exp066_anchor": str(EXP066_PARQUET),
        "reproduction_safety": ("BENCH reuses EXP-061 M0/H0 + EXP-066 BENCH RNG purposes; "
                                "PARTIAL-V2A reuses EXP-066's native PARTIAL-V2A purpose block; "
                                "V2A-ADVNONE + its RM null use a fresh block (>=300000). No "
                                "EXP-061/066 stream shifts; reconciled medians/m are "
                                "RNG-independent (deterministic from data)."),
        "disclosed_secondaries_not_computed": (
            "Deferred (runtime/budget; NOT silently): the /STRONG-HA conditioning arm; the "
            "V2C x ADV-NONE and other partial-variant x ADV-NONE combinations (only V2A is "
            "predeclared for ADV-NONE, mirroring the EXP-060B champion axis). A promotion "
            "follow-up only if EXP-068 PROCEEDs at G-015."),
        "is_defect": defect["is_defect"],
        "de30_disclosure": DE30_DISCLOSURE,
        "fill_approximation": ("P15 path is a documented approximation of unobserved intrabar "
                               "motion; 1-minute base bars are not replayed (EXP-054 bounds it)."),
        "holdout_fence": ("Only Parquet metadata + first train_rows file-order rows read per "
                          "instrument; full file never sorted/collected; every domain bar fenced "
                          "CloseTime <= train_end_ts; forward scans clipped to the data edge -> "
                          "DATA_CENSORED; TEST and final-30% holdout never read."),
        "registry": ("CF-HA-HARAMI-001/HYP-021 (EXP-068); exercises the registered MA-SUBSTRATE "
                     "(native mode, parallel first-class per D0-amendment-001), /EXIT-PARTIAL "
                     "(V2A), /ADV-NONE (disclosed reference), the benchmark geometry, and the "
                     "matched-random baseline. 0 candidate slots, 0 TEST reads; characterisation "
                     "readout feeds the single terminal G-015 (no closure or registration here)."),
        "instrument_meta": instrument_meta,
    }
    with open(RESULTS_DIR / "run_metadata.json", "w") as fh:
        json.dump(meta, fh, indent=2, default=str)


def _summarize(rows: list[dict[str, Any]], readout: dict[str, Any]) -> dict[str, Any]:
    """Concise stdout summary."""
    pa = readout["native_per_arm"]
    return {
        "mechanical_native_readout": readout["mechanical_native_readout"],
        "any_champion_g015_composes": readout["any_champion_g015_composes"],
        "g015_composing_arms": readout["g015_composing_arms"],
        "defect": readout["defect"],
        "per_arm": {aid: {
            "median_viable": pa[aid]["median_viable"]["n_cells"],
            "mean_positive": pa[aid]["mean_positive"]["n_cells"],
            "winsorized_mean_positive": pa[aid]["winsorized_mean_positive"]["n_cells"],
            "beats_rm": pa[aid]["beats_rm"]["n_cells"],
            "s3_evidence_for": pa[aid]["s3_evidence_for"]["n_cells"],
            "g015_passes": pa[aid]["g015_passes"]["n_cells"],
            "g015_composes": pa[aid]["g015_passes"]["composes"],
        } for aid in OBJECT_ARMS["nat"]},
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"{EXPERIMENT_ID} MA native combined champion (G-015 conjunction)")
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
    LOGGER.info("\n=== %s complete (native combined champion) ===", EXPERIMENT_ID)
    LOGGER.info("mechanical native readout: %s (NOT the G-015 gate -- see results.md)",
                summary["mechanical_native_readout"])
    for aid in OBJECT_ARMS["nat"]:
        s = summary["per_arm"][aid]
        LOGGER.info("  %-13s median-viable %s | mean+ %s | winsorm+ %s | beats_rm %s | "
                    "S3-EF %s | G015 %s (composes=%s)", aid, s["median_viable"],
                    s["mean_positive"], s["winsorized_mean_positive"],
                    s["beats_rm"], s["s3_evidence_for"], s["g015_passes"], s["g015_composes"])
    if summary["defect"]["is_defect"]:
        LOGGER.info("DEFECT: %s", json.dumps(summary["defect"], default=str))
    LOGGER.info("artifacts -> %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
