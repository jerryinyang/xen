"""EXP-059B — Uncapped Structure Trailing (Conditioned HA Harami).

``CF-HA-HARAMI-001`` / HYP-012b (Phase 014-B; follow-up to EXP-059). TRAIN-only,
gross; 0 candidate slots, 0 TEST reads. EXP-059 measured every trailing/combined
arm under the benchmark adaptive time cap (``n_event = bench_n`` in
``xen.position_exits.resolve_legs``/``build_active_stops``, explicit ``TIMECAP``
exit); even ``TRAIL-TP-NOINIT`` (no init stop) kept the cap. This script fills the
gap: the structure trailing stop as a **standalone adverse-exit model** — **no
time-cap backstop and no initial stop** (``/EXIT-TRAIL-UNCAPPED``) — on the same
conditioned population and 99-cell member grid. For each EXP-049/053 member cell on
the TRAIN stratum it:

1. slices the first-49% (TRAIN) 1-minute rows by file-order prefix (TEST and the
   final-30% global holdout are never read), aggregates the domain (5m strict;
   others min_coverage=0.90) and fences to the TRAIN edge;
2. reproduces the **EXP-053 conditioned population byte-identically** (frozen
   Wilder-ATR primary ZigZag atr_mult=1.0, HA haramis on exact CloseTime, live
   in-progress move, binding ``/STRONG-STAT`` p75; ``/STRONG-HA`` disclosed),
   entered at the harami real close and faded against the in-progress move;
3. resolves **5 arms**: ``BENCH`` (capped 1:1 reference, reproduces EXP-053/059);
   ``TRAIL-PURE-UNCAPPED`` and ``COMBINED-UNCAPPED-V2A`` (binding — the new lazy
   uncapped resolver: no cap, no init stop, DATA_CENSORED at the TRAIN edge);
   ``TRAIL-PURE-NOINIT-CAPPED`` and ``COMBINED-V2A-NOINIT-CAPPED`` (disclosed
   cap-isolation siblings — the existing capped resolver, no init stop). Binding
   endpoint = per-event **position-weighted** realised gross return (P14,
   ATR-normalised, P15 fills);
4. computes per-cell **median** expectancy (regime-clustered moving-block bootstrap
   CI), the **paired** arm-BENCH contrast (binding) and the **cap-isolation**
   contrast (uncapped vs its capped sibling, disclosed), two P13 baselines
   (matched-random, MA(20,50)-seg) per arm, composes by P11, and emits a mechanical
   EVIDENCE_* readout. ``DATA_CENSORED`` is disclosed **separately** for the uncapped
   arms; per-arm **holding-duration** percentiles are disclosed; and
5. runs a determinism replay, the EXP-053 BENCH anchor, and the predeclared
   invariants (degenerate uncapped single-trigger == single-leg; lazy uncapped stop
   == dense capped stop on the shared prefix; trailing monotone; trailing binds all
   open legs; **uncapped arms emit no TIMECAP**; exits within the TRAIN edge) as
   SUBSTRATE/METHOD_DEFECT guards.

Real prices throughout; HA prices enter only the harami/impulse detectors and never
any metric. Outputs under results/ and plots/; created in orchestration.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import logging
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
    ADV_TRAIL,
    ATR_MULT_TRAIL,
    LEG_LEVEL,
    LEG_NONE,
    PX_CLASS_LABELS,
    PX_TIMECAP,
    PX_TRAIL,
    build_active_stops,
    exit_reason_weights,
    leg_levels_from_fracs,
    resolve_legs,
    resolve_legs_uncapped,
    trail_is_monotone,
    weighted_returns,
)
from xen import expectancy as _xe_mod  # noqa: E402  (resolver-integrity hashing only)
from xen import position_exits as _pe_mod  # noqa: E402  (resolver-integrity hashing only)
from xen.strong_move import annotate_ha_impulse, find_impulse_runs  # noqa: E402
from xen.zigzag import generate_zigzag, wilder_atr  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (Phase 014-B D0 frozen; no tuning)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-059B"
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
INVARIANT_TOL = 1e-9               # degenerate / prefix reproduction tolerance
INVARIANT_MAX_EVENTS = 1500        # cap events re-resolved by the O(train_len) uncapped
#                                    invariant checks (F03; structural checks need only a
#                                    bounded, evenly-spaced sample, not the full population)
BASE_SEED = 20260616               # frozen master seed (no tuning)
DEFAULT_WORKERS_CAP = 6            # default parallel instruments (override via XEN_WORKERS;
#                                   cells are independent + per-cell seeded, so any worker
#                                   count yields byte-identical results — only speed changes)
EXCLUDED_FILE_MARKERS = ("analysis70", "analysis_slice", "first70")
DE30_DISCLOSURE = (
    "DE30 truncated history: broker m1 history ends 2026-01-16; counts derive "
    "from its own realized timeline and are not span-comparable (VAL-003).")
LOGGER = logging.getLogger(EXPERIMENT_ID)

# Arm kinds.
KIND_BENCH = "bench"
KIND_UNCAPPED = "uncapped"
KIND_CAPPED = "capped_trail"

# --------------------------------------------------------------------------- #
# Arm specification (predeclared 5-arm uncapped-trailing set)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ArmSpec:
    """One predeclared arm (OAT on the adverse-exit model: cap on/off, init stop)."""

    aid: str
    idx: int                           # stable RNG / column offset
    leg_kinds: tuple[int, ...]         # LEG_* per leg
    leg_fracs: tuple[float | None, ...]  # favourable distance fraction (None = non-level)
    weights: tuple[float, ...]         # leg weights (sum 1.0)
    kind: str                          # KIND_BENCH | KIND_UNCAPPED | KIND_CAPPED
    sibling: str | None                # capped no-init sibling (for cap-isolation)


_V2A = (1.0 / 3.0, 2.0 / 3.0, 1.0)
_W3 = (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)
_LLL = (LEG_LEVEL, LEG_LEVEL, LEG_LEVEL)
ARMS: list[ArmSpec] = [
    ArmSpec("BENCH", 0, (LEG_LEVEL,), (1.0,), (1.0,), KIND_BENCH, None),
    ArmSpec("TRAIL-PURE-UNCAPPED", 1, (LEG_NONE,), (None,), (1.0,), KIND_UNCAPPED,
            "TRAIL-PURE-NOINIT-CAPPED"),
    ArmSpec("COMBINED-UNCAPPED-V2A", 2, _LLL, _V2A, _W3, KIND_UNCAPPED,
            "COMBINED-V2A-NOINIT-CAPPED"),
    ArmSpec("TRAIL-PURE-NOINIT-CAPPED", 3, (LEG_NONE,), (None,), (1.0,), KIND_CAPPED, None),
    ArmSpec("COMBINED-V2A-NOINIT-CAPPED", 4, _LLL, _V2A, _W3, KIND_CAPPED, None),
]
ALL_ARM_IDS: list[str] = [a.aid for a in ARMS]
ALT_ARMS: list[ArmSpec] = [a for a in ARMS if a.kind != KIND_BENCH]
BINDING_ARMS: list[ArmSpec] = [a for a in ARMS if a.kind == KIND_UNCAPPED]
ARM_BY_ID: dict[str, ArmSpec] = {a.aid: a for a in ARMS}

# RNG purpose bases (distinct deterministic streams per cell/arm/purpose).
PB_STAT, PB_HA = 1000, 2000                      # signal-arm bootstraps
PB_PC_STAT, PB_PC_HA = 4000, 5000                # paired contrasts vs BENCH
PB_CAPISO = 6000                                 # cap-isolation paired contrasts
PB_RAND_DRAW, PB_RAND_BOOT, PB_MASEG = 7000, 8000, 9000  # baselines (stat arm only)

# Composition status -> integer code / colour.
VSTATUS_CODES: dict[str, int] = {
    "WIN": 0, "VIABLE_ONLY": 1, "CI_SPANS_0": 2,
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
    r_firsthit: float | None       # BENCH single-leg only; None for multi-leg arms
    win_rate: float | None
    data_censored: int
    warmup_excluded: int
    exit_weights: dict[str, float]
    population: int                # built-barrier population (pre-resolution)
    block_len: int
    hold_off: np.ndarray           # per-qualifying-event holding offset (entry order)
    hold_measured: bool            # True = measured exit offset (all arms now measured)
    r_e: np.ndarray                # qualifying weighted returns in entry order
    r_e_all: np.ndarray            # full-length weighted returns (NaN off-qual)
    qual: np.ndarray               # full-length qualifying mask (for pairing)
    dist: np.ndarray               # bootstrap median distribution (may be empty)
    exit_off_all: np.ndarray       # full-length measured exit offset (-1 off-pop)
    past_cap: np.ndarray           # full-length: exit_off_all > bench_n (cap-isolation)


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


def secondary_history(sec: dict[str, np.ndarray], entry_epoch: np.ndarray) -> np.ndarray:
    """Per-entry flag: at least one secondary move confirmed at/before the entry."""
    return np.searchsorted(sec["confirm_epoch"], entry_epoch, side="right") >= 1


def ma_segment_moves(ohlc: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """MA(20,50)-crossover segmentation as a ZigZag-shaped confirmed-move set."""
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
    fav: np.ndarray, adv: np.ndarray, bench_n: np.ndarray, sec: dict[str, np.ndarray],
    sec_hist: np.ndarray, population: np.ndarray, last_train_idx: int,
    rng: np.random.Generator,
) -> ArmResult:
    """Resolve one arm over ``population`` events and bootstrap the median expectancy."""
    n_bars = ohlc["close"].shape[0]
    n_ev = int(entry_idx.shape[0])
    no_rev = np.full(n_ev, -1, dtype=np.int64)
    exit_off = np.full(n_ev, -1, dtype=np.int64)        # measured for every arm (F04)
    if arm.kind == KIND_BENCH:                          # exact EXP-053 reuse path
        classes, exit_px = resolve_path_ordered(
            ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"], entry_idx,
            fav, adv, rd, bench_n, population, n_bars, exit_off)
        r_all = realised_returns(classes, exit_px, entry_close, rd, atr_entry)
        qual = population & qualifying_mask(classes, exit_px, atr_entry)
        weights, leg_cls = np.array([1.0]), classes[:, None]
        r_firsthit = _bench_firsthit(classes, qual)
        censored = int((population & (classes == CLASS_DATA_CENSORED)).sum())
        warmup = 0
    else:
        weights = np.asarray(arm.weights, dtype=np.float64)
        levels = leg_levels_from_fracs(entry_close, rd, fav_dist, arm.leg_fracs)
        warmup = int((population & ~sec_hist).sum())
        pop = population & sec_hist
        if arm.kind == KIND_UNCAPPED:
            leg_px, leg_cls, exit_off = resolve_legs_uncapped(
                ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"], entry_idx,
                entry_close, rd, arm.leg_kinds, levels, no_rev, sec["confirm_idx"],
                sec["direction"], sec["end_price"], pop, last_train_idx)
        else:                                           # KIND_CAPPED (no init stop)
            active = build_active_stops(entry_idx, rd, adv, True, sec["confirm_idx"],
                                        sec["direction"], sec["end_price"], bench_n,
                                        last_train_idx)
            leg_px, leg_cls = resolve_legs(
                ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"], entry_idx,
                entry_close, rd, arm.leg_kinds, levels, no_rev, adv, bench_n, pop,
                ADV_TRAIL, active, last_train_idx, exit_off)
        r_all, qual = weighted_returns(leg_px, leg_cls, weights, entry_close, rd,
                                       atr_entry, pop)
        r_firsthit = None
        censored = int((pop & ~qual & np.isfinite(atr_entry) & (atr_entry > 0.0)).sum())
    # Per-event "held past the benchmark cap" mask (F02 cap-isolation divergent
    # subset): an event whose measured exit offset exceeds bench_n is the only place
    # an uncapped arm can differ from its capped no-init sibling.
    past_cap = (exit_off >= 0) & (exit_off > bench_n.astype(np.int64))
    order = np.argsort(entry_idx[qual], kind="stable")
    r_e = r_all[qual][order]
    hold_off = exit_off[qual][order]
    exit_w = exit_reason_weights(leg_cls, weights, qual)
    return _summarize_arm(r_e, r_all, qual, exit_w, r_firsthit, censored, warmup,
                          int(population.sum()), hold_off, exit_off, past_cap, rng)


def _bench_firsthit(classes: np.ndarray, qual: np.ndarray) -> float | None:
    """BENCH first-hit r = FAV/(FAV+ADV), TIMECAP excluded (EXP-049 convention)."""
    fav_n = int((qual & (classes == CLASS_FAV)).sum())
    adv_n = int((qual & (classes == CLASS_ADV)).sum())
    resolved = fav_n + adv_n
    return (fav_n / resolved) if resolved > 0 else None


def _summarize_arm(
    r_e: np.ndarray, r_all: np.ndarray, qual: np.ndarray, exit_w: dict[str, float],
    r_firsthit: float | None, censored: int, warmup: int, population: int,
    hold_off: np.ndarray, exit_off_all: np.ndarray, past_cap: np.ndarray,
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
        dist, block_len = bootstrap_median_distribution(r_e, rng)
        ci_low, ci_lo, ci_hi = median_ci(dist)
    return ArmResult(
        m=m, median=median, mean=mean, ci_low_1s=ci_low, ci_lo_2s=ci_lo, ci_hi_2s=ci_hi,
        r_firsthit=r_firsthit, win_rate=(float((r_e > 0).mean()) if m > 0 else None),
        data_censored=censored, warmup_excluded=warmup, exit_weights=exit_w,
        population=population, block_len=block_len, hold_off=hold_off,
        hold_measured=True, r_e=r_e, r_e_all=r_all, qual=qual, dist=dist,
        exit_off_all=exit_off_all, past_cap=past_cap)


def _empty_arm() -> ArmResult:
    return ArmResult(0, None, None, None, None, None, None, None, 0, 0,
                     {label: 0.0 for label in PX_CLASS_LABELS.values()}, 0, 1,
                     np.empty(0, dtype=np.int64), True, np.empty(0), np.empty(0),
                     np.empty(0, dtype=bool), np.empty(0),
                     np.empty(0, dtype=np.int64), np.empty(0, dtype=bool))


# --------------------------------------------------------------------------- #
# Pure computation — paired contrasts (binding vs BENCH; disclosed cap-isolation)
# --------------------------------------------------------------------------- #
def paired_contrasts_vs_bench(
    entry_idx: np.ndarray, arms: dict[str, ArmResult], cell_index: int, purpose_base: int,
) -> dict[str, tuple[float, float, float, int]]:
    """Paired median contrast of each alternative arm vs ``BENCH`` on shared events."""
    bench = arms["BENCH"]
    out: dict[str, tuple[float, float, float, int]] = {
        "BENCH": (float("nan"), float("nan"), float("nan"), 0)}
    for a in ALT_ARMS:
        out[a.aid] = _single_paired(entry_idx, arms[a.aid], bench, cell_index,
                                    purpose_base + a.idx)
    return out


def cap_isolation_contrasts(
    entry_idx: np.ndarray, arms: dict[str, ArmResult], cell_index: int,
) -> dict[str, dict[str, float]]:
    """Cap-isolation contrast of each uncapped arm vs its capped no-init sibling.

    Disclosed (never binding). The uncapped arm and its capped no-init sibling
    share an identical no-init trailing stop and P15 path on
    ``[entry+1, entry+bench_n]``, so every event resolving **within** the cap exits
    byte-identically under both arms — a structural zero in the paired difference
    (F02). A median paired contrast over the *full* common subset therefore
    collapses toward 0 whenever most events resolve within the cap, which is **not**
    evidence the cap is irrelevant. We report two contrasts:

    - ``full_*`` — the paired contrast over the full common qualifying subset
      (retained for continuity; dominated by structural zeros);
    - ``div_*`` — the paired contrast over the **divergent subset** (events the
      uncapped arm held *past* ``bench_n``, the only events whose exit can differ),
      plus ``div_share`` = divergent / full-common, the fraction of paired events
      that actually differ. The divergent contrast is the interpretable measure of
      "what removing the cap does, on the events it can affect."
    """
    out: dict[str, dict[str, float]] = {}
    for a in BINDING_ARMS:
        out[a.aid] = _cap_isolation_single(entry_idx, arms[a.aid], arms[a.sibling],
                                           cell_index, PB_CAPISO + a.idx)
    return out


def _cap_isolation_single(
    entry_idx: np.ndarray, unc: ArmResult, cap: ArmResult, cell_index: int, purpose: int,
) -> dict[str, float]:
    """Full-common and divergent-subset paired contrast (uncapped − capped sibling)."""
    empty = {"full_low": float("nan"), "full_lo2s": float("nan"),
             "full_hi2s": float("nan"), "full_n": 0, "div_low": float("nan"),
             "div_lo2s": float("nan"), "div_hi2s": float("nan"), "div_n": 0,
             "div_share": float("nan")}
    if unc.qual.shape[0] == 0 or cap.qual.shape[0] == 0:
        return empty
    common = unc.qual & cap.qual
    full_n = int(common.sum())
    if full_n == 0:
        return empty
    f_cl, f_lo, f_hi, _ = _paired_on_mask(entry_idx, unc, cap, common,
                                          _rng(cell_index, purpose))
    # Divergent subset: common events the uncapped arm held past its sibling's cap.
    divergent = common & unc.past_cap
    div_n = int(divergent.sum())
    if div_n > 0:
        d_cl, d_lo, d_hi, _ = _paired_on_mask(entry_idx, unc, cap, divergent,
                                              _rng(cell_index, purpose + 1))
    else:
        d_cl = d_lo = d_hi = float("nan")
    return {"full_low": f_cl, "full_lo2s": f_lo, "full_hi2s": f_hi, "full_n": full_n,
            "div_low": d_cl, "div_lo2s": d_lo, "div_hi2s": d_hi, "div_n": div_n,
            "div_share": (div_n / full_n) if full_n else float("nan")}


def _paired_on_mask(
    entry_idx: np.ndarray, res: ArmResult, ref: ArmResult, mask: np.ndarray,
    rng: np.random.Generator,
) -> tuple[float, float, float, int]:
    """Paired median contrast of two arms on a shared event ``mask`` (entry order)."""
    s_n = int(mask.sum())
    if s_n == 0:
        return (float("nan"), float("nan"), float("nan"), 0)
    order = np.argsort(entry_idx[mask], kind="stable")
    cl, lo, hi, _ = paired_median_contrast_ci(
        res.r_e_all[mask][order], ref.r_e_all[mask][order], rng)
    return (cl, lo, hi, s_n)


def _single_paired(
    entry_idx: np.ndarray, res: ArmResult, ref: ArmResult, cell_index: int, purpose: int,
) -> tuple[float, float, float, int]:
    """Paired contrast of one arm vs a reference on their common qualifying subset."""
    if res.qual.shape[0] == 0 or ref.qual.shape[0] == 0:
        return (float("nan"), float("nan"), float("nan"), 0)
    return _paired_on_mask(entry_idx, res, ref, res.qual & ref.qual,
                           _rng(cell_index, purpose))


# --------------------------------------------------------------------------- #
# Pure computation — P13 baselines per arm (disclosed, stat arm)
# --------------------------------------------------------------------------- #
def matched_random_arm(
    ohlc: dict[str, np.ndarray], state_all: InProgressState, mv: dict[str, np.ndarray],
    warmup_all: np.ndarray, atr_all: np.ndarray, signal_idx: np.ndarray, arm: ArmSpec,
    sec: dict[str, np.ndarray], draw_count: int, last_train_idx: int, cell_index: int,
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
    drawn = np.sort(_rng(cell_index, PB_RAND_DRAW + arm.idx).choice(
        pool, size=k, replace=False))
    sub = _subset_state(state_all, drawn)
    bar = benchmark_barriers(ohlc["close"][drawn], sub.rd, sub.m_sofar)
    bench_n, bench_warmup = adaptive_time_caps_by_epoch(
        ohlc["epoch"][drawn], mv["confirm_epoch"], mv["confirm_idx"])
    pop = (sub.valid & (sub.m_sofar > 0.0) & np.isfinite(atr_all[drawn])
           & (atr_all[drawn] > 0.0) & ~bench_warmup)
    sec_hist = secondary_history(sec, ohlc["epoch"][drawn])
    return resolve_arm(ohlc, drawn, ohlc["close"][drawn], sub.rd, atr_all[drawn], arm,
                       bar["fav_dist"], bar["fav"], bar["adv"], bench_n, sec, sec_hist,
                       pop, last_train_idx, _rng(cell_index, PB_RAND_BOOT + arm.idx))


def ma_seg_arm(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, entry_epoch: np.ndarray,
    entry_close: np.ndarray, atr_entry: np.ndarray, seg: dict[str, np.ndarray],
    sec: dict[str, np.ndarray], sec_hist: np.ndarray, arm: ArmSpec, last_train_idx: int,
    cell_index: int,
) -> ArmResult:
    """MA(20,50)-segmentation baseline for one arm through the identical pipeline."""
    if seg["confirm_epoch"].shape[0] == 0:
        return _empty_arm()
    state = live_in_progress_state(entry_epoch, entry_close, seg["confirm_epoch"],
                                   seg["end_price"], seg["end_epoch"], seg["direction"])
    bench_n, bench_warmup = adaptive_time_caps_by_epoch(
        entry_epoch, seg["confirm_epoch"], seg["confirm_idx"])
    buildable = (state.valid & (state.m_sofar > 0.0) & np.isfinite(atr_entry)
                 & (atr_entry > 0.0) & ~bench_warmup)
    stat = live_strong_stat(state.k, state.m_sofar, seg["magnitude"])
    bar = benchmark_barriers(entry_close, state.rd, state.m_sofar)
    pop = buildable & stat["retained_p75"]
    return resolve_arm(ohlc, entry_idx, entry_close, state.rd, atr_entry, arm,
                       bar["fav_dist"], bar["fav"], bar["adv"], bench_n, sec, sec_hist,
                       pop, last_train_idx, _rng(cell_index, PB_MASEG + arm.idx))


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
    sec_moves = generate_zigzag(bars, atr_period=ATR_PERIOD, atr_mult=ATR_MULT_TRAIL)
    mv = move_arrays(moves, ohlc["epoch"])
    sec = move_arrays(sec_moves, ohlc["epoch"])
    atr = wilder_atr(ohlc["high"], ohlc["low"], ohlc["close"], ATR_PERIOD)
    entry_idx, entry_epoch, ha_ann = harami_entry_indices(bars, ohlc["epoch"])
    base = {"domain": domain, "n_bars": int(bars.height), "n_moves": int(moves.height),
            "n_sec_moves": int(sec_moves.height), "n_harami": int(entry_idx.shape[0])}
    if entry_idx.shape[0] == 0 or mv["confirm_epoch"].shape[0] == 0:
        return {**base, "empty": True}

    ctx = _cell_context(ohlc, atr, entry_idx, entry_epoch, mv, sec, ha_ann)
    arms = _resolve_all_arms(ctx, ohlc, sec, last_train_idx, cell_index)
    baselines = _resolve_baselines(ctx, arms["stat"]["arms"], ohlc, mv, sec,
                                   last_train_idx, cell_index)
    conditioned = ctx["buildable"] & ctx["stat"]["retained_p75"]
    return {
        **base, "empty": False, "arms": arms, "baselines": baselines,
        "buildable": int(ctx["buildable"].sum()), "conditioned": int(conditioned.sum()),
        "conditioned_digest": int(entry_epoch[conditioned].sum(dtype=np.int64)),
        "causality_ok": _causality_ok(ohlc, entry_idx, entry_epoch, ctx["state"], mv),
        "invariants": _cell_invariants(ctx, ohlc, sec, last_train_idx),
    }


def _cell_context(
    ohlc: dict[str, np.ndarray], atr: np.ndarray, entry_idx: np.ndarray,
    entry_epoch: np.ndarray, mv: dict[str, np.ndarray], sec: dict[str, np.ndarray],
    ha_ann: pl.DataFrame,
) -> dict[str, Any]:
    """Build the shared conditioned-signal context for a cell."""
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
    sec_hist = secondary_history(sec, entry_epoch)
    return {
        "entry_idx": entry_idx, "entry_epoch": entry_epoch, "entry_close": entry_close,
        "state": state, "atr": atr, "atr_entry": atr_entry, "bench_n": bench_n,
        "bench_warmup": bench_warmup, "buildable": buildable, "stat": stat,
        "ha_same": ha_same, "fav_dist": bar["fav_dist"], "fav": bar["fav"], "adv": bar["adv"],
        "sec_hist": sec_hist,
    }


def _resolve_all_arms(
    ctx: dict[str, Any], ohlc: dict[str, np.ndarray], sec: dict[str, np.ndarray],
    last_train_idx: int, cell_index: int,
) -> dict[str, dict[str, Any]]:
    """Resolve every arm on the binding and disclosed signal arms + contrasts."""
    def resolve(mask: np.ndarray, a: ArmSpec, pb: int) -> ArmResult:
        pop = ctx["buildable"] & mask
        return resolve_arm(ohlc, ctx["entry_idx"], ctx["entry_close"], ctx["state"].rd,
                           ctx["atr_entry"], a, ctx["fav_dist"], ctx["fav"], ctx["adv"],
                           ctx["bench_n"], sec, ctx["sec_hist"], pop, last_train_idx,
                           _rng(cell_index, pb + a.idx))

    arm_cfg = {"stat": (ctx["stat"]["retained_p75"], PB_STAT, PB_PC_STAT),
               "ha": (ctx["ha_same"], PB_HA, PB_PC_HA)}
    out: dict[str, dict[str, Any]] = {}
    for arm, (mask, pb, pc_pb) in arm_cfg.items():
        res = {a.aid: resolve(mask, a, pb) for a in ARMS}
        out[arm] = {
            "arms": res,
            "contrast": paired_contrasts_vs_bench(ctx["entry_idx"], res, cell_index, pc_pb),
            "capiso": cap_isolation_contrasts(ctx["entry_idx"], res, cell_index),
        }
    return out


def _resolve_baselines(
    ctx: dict[str, Any], stat_arms: dict[str, ArmResult], ohlc: dict[str, np.ndarray],
    mv: dict[str, np.ndarray], sec: dict[str, np.ndarray], last_train_idx: int,
    cell_index: int,
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
                                  a, sec, draw, last_train_idx, cell_index)
        ma = ma_seg_arm(ohlc, ctx["entry_idx"], ctx["entry_epoch"], ctx["entry_close"],
                        ctx["atr_entry"], seg, sec, ctx["sec_hist"], a, last_train_idx,
                        cell_index)
        out[a.aid] = {"matched_random": rand, "ma_seg": ma}
    return out


# --------------------------------------------------------------------------- #
# Per-cell causality / invariant gate (analysis-plan Step 13)
# --------------------------------------------------------------------------- #
def _causality_ok(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, entry_epoch: np.ndarray,
    state: InProgressState, mv: dict[str, np.ndarray],
) -> bool:
    """Runtime causality checks: strict grid, causal reference move, entry <= t_i."""
    epoch = ohlc["epoch"]
    if epoch.shape[0] >= 2 and not bool(np.all(np.diff(epoch) > 0)):
        return False
    valid = state.valid & (state.k >= 0)
    if valid.any():
        kk = state.k[valid]
        if not bool(np.all(mv["end_epoch"][kk] <= entry_epoch[valid])):
            return False
        if not bool(np.all(epoch[entry_idx[valid]] <= entry_epoch[valid])):
            return False
    return True


def _cell_invariants(
    ctx: dict[str, Any], ohlc: dict[str, np.ndarray], sec: dict[str, np.ndarray],
    last_train_idx: int,
) -> dict[str, bool]:
    """Predeclared uncapped-trailing invariants (analysis-plan Step 13)."""
    cond = ctx["buildable"] & ctx["stat"]["retained_p75"]
    o, h, lo, c = ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"]
    ei, ec, rd = ctx["entry_idx"], ctx["entry_close"], ctx["state"].rd
    adv, bench_n, fd = ctx["adv"], ctx["bench_n"], ctx["fav_dist"]
    sci, sdir, sep = sec["confirm_idx"], sec["direction"], sec["end_price"]
    pop = cond & ctx["sec_hist"]
    # The three uncapped re-resolutions below are O(train_len) per event; a bounded,
    # evenly-spaced sample exercises the structural invariants without the full-pop
    # blow-up (F03). The cheap dense-bounded checks (trail_monotone, lazy==dense
    # prefix) still run over the full conditioned population.
    pop_inv = _subsample_mask(pop, INVARIANT_MAX_EVENTS)
    no_rev = np.full(int(ei.shape[0]), -1, dtype=np.int64)
    w1, w3 = np.array([1.0]), np.array([1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0])
    weights_ok = all(abs(sum(a.weights) - 1.0) <= 1e-12 for a in ARMS)
    # (iii) degenerate 3-leg all-LEVEL@fav uncapped == single-leg LEVEL@fav uncapped.
    lvl1 = leg_levels_from_fracs(ec, rd, fd, (1.0,))
    px1, cls1, _ = resolve_legs_uncapped(o, h, lo, c, ei, ec, rd, (LEG_LEVEL,), lvl1,
                                         no_rev, sci, sdir, sep, pop_inv, last_train_idx)
    r1, q1 = weighted_returns(px1, cls1, w1, ec, rd, ctx["atr_entry"], pop_inv)
    lvl3 = leg_levels_from_fracs(ec, rd, fd, (1.0, 1.0, 1.0))
    px3, cls3, _ = resolve_legs_uncapped(o, h, lo, c, ei, ec, rd,
                                         (LEG_LEVEL, LEG_LEVEL, LEG_LEVEL), lvl3, no_rev,
                                         sci, sdir, sep, pop_inv, last_train_idx)
    r3, q3 = weighted_returns(px3, cls3, w3, ec, rd, ctx["atr_entry"], pop_inv)
    degenerate_match = _arr_match(r1, q1, r3, q3)
    # (vi) uncapped trailing binds all still-open legs at one level (PURE single leg + V2A).
    lvl_a = leg_levels_from_fracs(ec, rd, fd, _V2A)
    px_a, cls_a, off_a = resolve_legs_uncapped(o, h, lo, c, ei, ec, rd, _LLL, lvl_a, no_rev,
                                               sci, sdir, sep, pop_inv, last_train_idx)
    shared_ok = _shared_trail_ok(cls_a, px_a, pop_inv)
    # (vi.b) uncapped arms emit NO TIMECAP class.
    no_timecap = bool(not (cls_a == PX_TIMECAP).any() and not (cls3 == PX_TIMECAP).any())
    # (v) every uncapped exit is within the TRAIN edge (offset within [1, last-ei]).
    edge_ok = _edge_ok(off_a, ei, cls_a, last_train_idx)
    # (iv.a) trailing stop monotone (dense capped path, no init stop, conditioned set).
    active = build_active_stops(ei, rd, adv, True, sci, sdir, sep, bench_n, last_train_idx)
    trail_mono = all(trail_is_monotone(active[e], int(rd[e])) for e in np.flatnonzero(pop))
    # (iv.b) lazy uncapped stop == dense capped stop on the shared [entry+1, entry+bench_n]
    # prefix (the two stop computations must agree where their windows overlap).
    prefix_ok = _lazy_dense_prefix_match(ei, rd, sci, sdir, sep, bench_n, active, pop,
                                         last_train_idx)
    return {"weights_sum_ok": bool(weights_ok), "degenerate_match": bool(degenerate_match),
            "shared_stop_ok": bool(shared_ok), "no_timecap": no_timecap,
            "edge_ok": bool(edge_ok), "trail_monotone": bool(trail_mono),
            "lazy_dense_prefix_ok": bool(prefix_ok)}


def _subsample_mask(mask: np.ndarray, max_n: int) -> np.ndarray:
    """Bounded, deterministic, evenly-spaced down-sample of a boolean event mask.

    Returns ``mask`` unchanged when it has ``<= max_n`` set entries; otherwise keeps
    ``max_n`` of them spread evenly across entry order (so early- and late-TRAIN
    events — short and long uncapped windows — are both exercised by the invariant
    checks). Used only for the O(train_len) uncapped invariant re-resolutions (F03);
    never touches any reported metric.
    """
    idx = np.flatnonzero(mask)
    if idx.shape[0] <= max_n:
        return mask
    keep = idx[np.linspace(0, idx.shape[0] - 1, max_n).round().astype(np.int64)]
    out = np.zeros_like(mask)
    out[np.unique(keep)] = True
    return out


def _arr_match(ra: np.ndarray, qa: np.ndarray, rb: np.ndarray, qb: np.ndarray) -> bool:
    """Two (returns, qualifying) pairs agree on the common qualifying subset + mask."""
    if not bool(np.array_equal(qa, qb)):
        return False
    common = qa & qb
    if not common.any():
        return True
    return bool(np.allclose(ra[common], rb[common], atol=INVARIANT_TOL))


def _shared_trail_ok(cls: np.ndarray, px: np.ndarray, cond: np.ndarray) -> bool:
    """Every leg exiting via the uncapped trailing stop does so at the same bar/level."""
    has_trail = (cls == PX_TRAIL).any(axis=1) & cond
    for e in np.flatnonzero(has_trail):
        legs = cls[e] == PX_TRAIL
        vals = px[e][legs]
        if vals.shape[0] > 1 and not bool(np.allclose(vals, vals[0], atol=1e-9)):
            return False
    return True


def _edge_ok(off: np.ndarray, ei: np.ndarray, cls: np.ndarray, last_train_idx: int) -> bool:
    """Resolving offsets stay within [1, last_train_idx - entry] for resolved events.
    
    Events entered at the very last bar (``ei == last_train_idx``) have zero forward
    room; ``_scan_event_uncapped`` returns offset 0 with all legs DATA_CENSORED. This
    is a correct TRAIN-edge censoring, not an invariant violation, so we skip the
    ``off >= 1`` requirement for such events.
    """
    from xen.position_exits import PX_DATA_CENSORED
    pop_mask = off >= 0
    for e in np.flatnonzero(pop_mask):
        if int(off[e]) == 0 and (cls[e] == PX_DATA_CENSORED).all():
            continue
        if not (1 <= int(off[e]) <= last_train_idx - int(ei[e])):
            return False
    return True


def _lazy_dense_prefix_match(
    ei: np.ndarray, rd: np.ndarray, sci: np.ndarray, sdir: np.ndarray, sep: np.ndarray,
    bench_n: np.ndarray, active: np.ndarray, cond: np.ndarray, last_train_idx: int,
) -> bool:
    """Lazy uncapped stop reproduces the dense capped (no-init) stop on the shared prefix."""
    n_sec = int(sci.shape[0])
    for e in np.flatnonzero(cond):
        eidx, rd_e = int(ei[e]), int(rd[e])
        end = min(eidx + int(bench_n[e]), last_train_idx)
        stop = np.nan
        ptr = int(np.searchsorted(sci, eidx, side="right"))
        for off in range(1, end - eidx + 1):
            i = eidx + off
            while ptr < n_sec and int(sci[ptr]) <= i:
                if ptr >= 1 and int(sdir[ptr]) == rd_e:
                    cand = float(sep[ptr - 1])
                    stop = cand if not np.isfinite(stop) else (
                        max(stop, cand) if rd_e == 1 else min(stop, cand))
                ptr += 1
            dense = active[e, off]
            if np.isfinite(stop) != np.isfinite(dense):
                return False
            if np.isfinite(stop) and abs(stop - dense) > INVARIANT_TOL:
                return False
    return True


# --------------------------------------------------------------------------- #
# Per-cell record flattening + viability / win classification
# --------------------------------------------------------------------------- #
def cell_arm_records(instrument: str, cell: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten one cell into per-arm binding (stat) records."""
    domain = cell["domain"]
    fields = {"instrument": instrument, "domain": domain, "member": True,
              "excluded": False, "n_bars": cell["n_bars"], "n_moves": cell["n_moves"],
              "n_sec_moves": cell.get("n_sec_moves"), "n_harami": cell["n_harami"]}
    if cell.get("empty", False):
        return [{**fields, "arm": a.aid, **_empty_arm_fields(a)} for a in ARMS]
    stat = cell["arms"]["stat"]
    bench_m = stat["arms"]["BENCH"].m
    fields.update({"n_buildable": cell["buildable"], "n_conditioned": cell["conditioned"]})
    return [{**fields, "arm": a.aid, **_arm_record(cell, a, bench_m)} for a in ARMS]


def _arm_record(cell: dict[str, Any], a: ArmSpec, bench_m: int) -> dict[str, Any]:
    """Per (cell, arm) metric + baseline + contrast + classification."""
    sig = cell["arms"]["stat"]["arms"][a.aid]
    contrast = cell["arms"]["stat"]["contrast"][a.aid]
    capiso = cell["arms"]["stat"]["capiso"].get(a.aid)
    bl = cell["baselines"][a.aid]
    rec: dict[str, Any] = _arm_fields(sig, a)
    rec["retained_fraction"] = (sig.m / cell["conditioned"]) if cell["conditioned"] else None
    rec["contrast_bench_low"], rec["contrast_bench_lo2s"], rec["contrast_bench_hi2s"], \
        rec["contrast_bench_n"] = contrast
    rec.update(_capiso_fields(capiso))
    rec.update(_baseline_fields(bl["matched_random"], "rand"))
    rec.update(_baseline_fields(bl["ma_seg"], "maseg"))
    rec["contrast_random_low"] = contrast_ci(sig.dist, bl["matched_random"].dist)[0]
    rec["contrast_ma_low"] = contrast_ci(sig.dist, bl["ma_seg"].dist)[0]
    _classify_arm(rec, sig, a, bench_m)
    return rec


def _capiso_fields(capiso: dict[str, float] | None) -> dict[str, Any]:
    """Flatten the cap-isolation contrast dict (full-common + divergent subset).

    ``None`` for non-binding arms (no capped sibling). The divergent-subset contrast
    (``capiso_div_*``) is the interpretable one; ``capiso_div_share`` is the fraction
    of paired events that actually diverge (held past the cap) — a low share means the
    full-common contrast is dominated by structural zeros and must not be read as a
    null cap effect (F02).
    """
    if capiso is None:
        return {"capiso_full_low": None, "capiso_full_lo2s": None,
                "capiso_full_hi2s": None, "capiso_full_n": 0, "capiso_div_low": None,
                "capiso_div_lo2s": None, "capiso_div_hi2s": None, "capiso_div_n": 0,
                "capiso_div_share": None}
    return {
        "capiso_full_low": capiso["full_low"], "capiso_full_lo2s": capiso["full_lo2s"],
        "capiso_full_hi2s": capiso["full_hi2s"], "capiso_full_n": capiso["full_n"],
        "capiso_div_low": capiso["div_low"], "capiso_div_lo2s": capiso["div_lo2s"],
        "capiso_div_hi2s": capiso["div_hi2s"], "capiso_div_n": capiso["div_n"],
        "capiso_div_share": capiso["div_share"],
    }


def _classify_arm(rec: dict[str, Any], sig: ArmResult, a: ArmSpec, bench_m: int) -> None:
    """Per (cell, arm) powered/viable/beats_bench/win + status code."""
    viable = (sig.m >= POWER_FLOOR and sig.ci_low_1s is not None
              and np.isfinite(sig.ci_low_1s) and sig.ci_low_1s > 0.0)
    cl = rec["contrast_bench_low"]
    beats = (a.kind != KIND_BENCH and sig.m >= POWER_FLOOR and bench_m >= POWER_FLOOR
             and rec["contrast_bench_n"] >= POWER_FLOOR
             and cl is not None and np.isfinite(cl) and cl > 0.0)
    # Only the two binding (uncapped) arms can score a P11 WIN; capped siblings are disclosed.
    win = viable and beats and a.kind == KIND_UNCAPPED
    rec["powered"] = sig.m >= POWER_FLOOR
    rec["viable"] = bool(viable)
    rec["beats_bench"] = bool(beats)
    rec["win"] = bool(win)
    if win:
        status = "WIN"
    elif viable:
        status = "VIABLE_ONLY"
    elif not rec["powered"]:
        status = "NOT_VIABLE_BY_POWER"
    else:
        status = "CI_SPANS_0"
    rec["viable_status"], rec["status_code"] = status, VSTATUS_CODES[status]


def _arm_fields(a: ArmResult, spec: ArmSpec) -> dict[str, Any]:
    """Flatten an ArmResult's scalar metrics + exit-reason weights + holding/censoring."""
    out = {
        "kind": spec.kind, "m": a.m, "median": a.median, "mean": a.mean,
        "ci_low_1s": a.ci_low_1s, "ci_lo_2s": a.ci_lo_2s, "ci_hi_2s": a.ci_hi_2s,
        "r_firsthit": a.r_firsthit, "win_rate": a.win_rate,
        "data_censored": a.data_censored,
        "uncapped_censored": a.data_censored if spec.kind == KIND_UNCAPPED else 0,
        "capped_censored": a.data_censored if spec.kind != KIND_UNCAPPED else 0,
        "warmup_excluded": a.warmup_excluded, "population": a.population,
        "block_len": a.block_len, "hold_measured": a.hold_measured,
    }
    out.update(_hold_fields(a))
    out.update({f"ew_{label}": a.exit_weights[label] for label in PX_CLASS_LABELS.values()})
    return out


def _hold_fields(a: ArmResult) -> dict[str, Any]:
    """Holding-duration percentiles (measured for uncapped; cap bound otherwise)."""
    if a.hold_off.shape[0] == 0:
        return {"hold_p50": None, "hold_p90": None, "hold_max": None}
    return {"hold_p50": float(np.median(a.hold_off)),
            "hold_p90": float(np.percentile(a.hold_off, 90)),
            "hold_max": float(np.max(a.hold_off))}


def _baseline_fields(a: ArmResult, prefix: str) -> dict[str, Any]:
    """Compact baseline columns (m / median / one-sided CI_low)."""
    return {f"{prefix}_m": a.m, f"{prefix}_median": a.median,
            f"{prefix}_ci_low_1s": a.ci_low_1s}


def _empty_arm_fields(spec: ArmSpec) -> dict[str, Any]:
    rec = {"n_buildable": 0, "n_conditioned": 0, "retained_fraction": None,
           "contrast_bench_low": None, "contrast_bench_lo2s": None,
           "contrast_bench_hi2s": None, "contrast_bench_n": 0,
           "contrast_random_low": None, "contrast_ma_low": None,
           "powered": False, "viable": False, "beats_bench": False, "win": False,
           "viable_status": "NOT_VIABLE_BY_POWER",
           "status_code": VSTATUS_CODES["NOT_VIABLE_BY_POWER"]}
    rec.update(_capiso_fields(None))
    rec.update(_arm_fields(_empty_arm(), spec))
    rec.update(_baseline_fields(_empty_arm(), "rand"))
    rec.update(_baseline_fields(_empty_arm(), "maseg"))
    return rec


def excluded_records(instrument: str, domain: str) -> list[dict[str, Any]]:
    """COVERAGE_EXCLUDED cell records (one per arm)."""
    out = []
    for a in ARMS:
        rec = {"instrument": instrument, "domain": domain, "member": False, "excluded": True,
               "arm": a.aid, "n_bars": None, "n_moves": None, "n_sec_moves": None,
               "n_harami": None}
        rec.update(_empty_arm_fields(a))
        rec["viable_status"], rec["status_code"] = "EXCLUDED", VSTATUS_CODES["EXCLUDED"]
        out.append(rec)
    return out


def secondary_records(instrument: str, cell: dict[str, Any]) -> list[dict[str, Any]]:
    """Disclosed-arm rows: /STRONG-HA, per arm."""
    if cell.get("empty", False):
        return []
    return [_secondary_row(instrument, cell, "ha", a.aid) for a in ARMS]


def _secondary_row(instrument: str, cell: dict[str, Any], signal: str, aid: str) -> dict[str, Any]:
    res = cell["arms"][signal]["arms"][aid]
    con = cell["arms"][signal]["contrast"][aid]
    return {"instrument": instrument, "domain": cell["domain"], "signal": signal, "arm": aid,
            "m": res.m, "median": res.median, "ci_low_1s": res.ci_low_1s,
            "ci_lo_2s": res.ci_lo_2s, "ci_hi_2s": res.ci_hi_2s, "r_firsthit": res.r_firsthit,
            "win_rate": res.win_rate, "data_censored": res.data_censored,
            "warmup_excluded": res.warmup_excluded, "contrast_bench_low": con[0],
            "contrast_bench_n": con[3]}


# --------------------------------------------------------------------------- #
# Composition + mechanical EVIDENCE_* classification (per arm)
# --------------------------------------------------------------------------- #
def composition_readout(records: list[dict[str, Any]], defect: dict[str, Any]) -> dict[str, Any]:
    """P11 composition per arm + the mechanical EVIDENCE_* verdict."""
    members = [r for r in records if r["member"]]
    by_arm = {a.aid: [r for r in members if r["arm"] == a.aid] for a in ARMS}
    per_arm = {aid: _arm_composition(rows) for aid, rows in by_arm.items()}
    passers = [a.aid for a in BINDING_ARMS if per_arm[a.aid]["win"]["passes"]]
    verdict = _evidence_label(defect, per_arm, passers)
    fragile = [aid for aid in passers if per_arm[aid]["win"]["fragile"]]
    return {
        "verdict": verdict, "n_pass": len(passers), "passing_arms": passers,
        "fragile_passes": fragile, "per_arm": per_arm, "defect": defect,
        "censoring": _censoring_summary(members),
        "cap_isolation": _capiso_summary(members),
        "rule": ("per arm: VIABLE iff median CI_low(1s)>0 AND m>=30; BEATS_BENCH iff paired "
                 "CI_low(delta)>0 AND m>=30 AND bench_m>=30 AND |common|>=30; WIN=viable&beats "
                 "AND uncapped; P11 iff >=5 cells over >=3 instruments. EVIDENCE_FOR iff a "
                 "binding (uncapped) arm's WIN clears P11; no registration (single 014-B G2)."),
        "cap_isolation_note": ("the disclosed cap-isolation paired contrast (uncapped - capped "
                               "no-init sibling) attributes any expectancy difference to removing "
                               "the cap; it never enters the verdict. Within-cap events exit "
                               "byte-identically under both arms (structural zeros), so the binding "
                               "read is the DIVERGENT-subset contrast (capiso_div_*, events held "
                               "past bench_n) with capiso_div_share; a near-zero full-common "
                               "contrast on a small divergent share is NOT evidence of no cap "
                               "effect (F02)."),
        "censoring_note": ("uncapped DATA_CENSORED (unbounded window reaches the TRAIN edge) is "
                           "disclosed SEPARATELY from capped censoring; it drives the power "
                           "readout and gates interpretation of the vs-BENCH contrast."),
        "multiplicity": ("uncorrected per-arm one-sided 95% CIs; family-wise correction across "
                         "the full 014-B surface is deferred to the single G2 desk adjudication."),
    }


def _arm_composition(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Powered / viable / win P11 tallies for one arm."""
    return {"powered": _tally([r for r in rows if r["powered"]]),
            "viable": _tally([r for r in rows if r["viable"]], with_cells=True),
            "win": _win_tally([r for r in rows if r["win"]])}


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


def _censoring_summary(members: list[dict[str, Any]]) -> dict[str, Any]:
    """Separated uncapped vs capped censoring + median per-cell censored counts per arm."""
    out: dict[str, Any] = {}
    for a in ARMS:
        rows = [r for r in members if r["arm"] == a.aid and r["m"] is not None]
        cens = [r["data_censored"] for r in rows if r.get("data_censored") is not None]
        out[a.aid] = {
            "kind": a.kind,
            "total_censored": int(sum(cens)) if cens else 0,
            "median_cell_censored": float(np.median(cens)) if cens else None,
            "median_cell_qual": (float(np.median([r["m"] for r in rows if r["m"]]))
                                 if any(r["m"] for r in rows) else None),
        }
    return out


def _capiso_summary(members: list[dict[str, Any]]) -> dict[str, Any]:
    """Per binding arm: divergent-share distribution + divergent-contrast win count.

    Discloses how often the cap actually binds differently (median divergent share)
    and, on the divergent subset, in how many cells removing the cap helps
    (capiso_div_low > 0). The full-common contrast is summarised only for contrast;
    the divergent figures are the interpretable ones (F02).
    """
    out: dict[str, Any] = {}
    for a in BINDING_ARMS:
        rows = [r for r in members if r["arm"] == a.aid
                and r.get("capiso_div_share") is not None]
        shares = [r["capiso_div_share"] for r in rows
                  if r["capiso_div_share"] is not None and np.isfinite(r["capiso_div_share"])]
        div_pos = [r for r in rows if r.get("capiso_div_low") is not None
                   and np.isfinite(r["capiso_div_low"]) and r["capiso_div_low"] > 0.0
                   and (r.get("capiso_div_n") or 0) >= POWER_FLOOR]
        out[a.aid] = {
            "sibling": a.sibling,
            "median_divergent_share": float(np.median(shares)) if shares else None,
            "max_divergent_share": float(np.max(shares)) if shares else None,
            "n_cells_divergent_ge_power": sum(
                1 for r in rows if (r.get("capiso_div_n") or 0) >= POWER_FLOOR),
            "n_cells_div_positive": len(div_pos),
            "cells_div_positive": [f"{r['instrument']}-{r['domain']}" for r in div_pos],
        }
    return out


def _evidence_label(
    defect: dict[str, Any], per_arm: dict[str, Any], passers: list[str],
) -> str:
    """Mechanical EVIDENCE_* per the analysis-plan Interpretation Guide."""
    if defect["is_defect"]:
        return "SUBSTRATE_METHOD_DEFECT"
    if passers:
        return "EVIDENCE_FOR"
    bench_pow = per_arm["BENCH"]["powered"]["composition_met"]
    bind_pow = any(per_arm[a.aid]["powered"]["composition_met"] for a in BINDING_ARMS)
    if bench_pow and bind_pow:
        return "EVIDENCE_AGAINST"
    return "INCONCLUSIVE_POWER_LIMITED"


# --------------------------------------------------------------------------- #
# Determinism replay + reconciliation anchors (DEFECT guards)
# --------------------------------------------------------------------------- #
def determinism_replay(cell_a: dict[str, Any], train_1m: pl.DataFrame, domain: str,
                       train_end_epoch: int, cell_index: int) -> bool:
    """Recompute one cell **once** and assert byte-identical binding outputs vs ``cell_a``.

    Compares the already-computed ``cell_a`` against a single fresh recompute (one
    extra ``compute_cell``, not two), and the orchestrator targets the **lightest**
    cell per instrument — determinism is a property of the code, so any non-empty
    BENCH-powered cell validates it, and the light cell avoids re-running the heavy
    5m uncapped scans twice (a large, logic-preserving speed-up).
    """
    b = compute_cell(train_1m, domain, train_end_epoch, cell_index)
    if cell_a.get("empty") or b.get("empty"):
        return cell_a.get("empty") == b.get("empty")
    for aid in ALL_ARM_IDS:
        sa, sb = cell_a["arms"]["stat"]["arms"][aid], b["arms"]["stat"]["arms"][aid]
        if not (np.array_equal(sa.r_e, sb.r_e)
                and np.array_equal(sa.hold_off, sb.hold_off)
                and (sa.median, sa.ci_low_1s) == (sb.median, sb.ci_low_1s)):
            return False
        for bl in ("matched_random", "ma_seg"):
            if not np.array_equal(cell_a["baselines"][aid][bl].r_e,
                                  b["baselines"][aid][bl].r_e):
                return False
    return True


def reconciliation_anchor(cell: dict[str, Any]) -> dict[str, Any]:
    """Independently re-check the BENCH stat arm's win-rate consistency."""
    sig = cell["arms"]["stat"]["arms"]["BENCH"]
    if sig.m == 0:
        return {"checked": False, "reason": "no qualifying BENCH events"}
    n_pos = int((sig.r_e > 0.0).sum())
    consistent = (sig.win_rate is not None
                  and abs(sig.win_rate - n_pos / sig.m) <= 1e-12
                  and bool(np.isfinite(sig.r_e[0])))
    return {"checked": True, "m": sig.m, "positive_returns": n_pos,
            "win_rate": sig.win_rate, "consistent": bool(consistent)}


def exp053_reconciliation(
    instrument: str, cell: dict[str, Any],
    exp053: dict[tuple[str, str], tuple[int, float | None, float | None]],
) -> dict[str, Any]:
    """Cross-check the BENCH stat arm against EXP-053's recorded benchmark (invariant i)."""
    key = (instrument, cell["domain"])
    if not exp053 or key not in exp053 or cell.get("empty"):
        return {"checked": False, "cell": f"{instrument}-{cell.get('domain')}"}
    sig = cell["arms"]["stat"]["arms"]["BENCH"]
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


def _placeholder(save_path: Path, message: str) -> None:
    fig, ax = plt.subplots(figsize=(6, 2))
    ax.text(0.5, 0.5, f"{EXPERIMENT_ID}: {message}", ha="center", va="center")
    ax.axis("off")
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_arm_forest(records: list[dict[str, Any]], save_path: Path) -> None:
    """Per-arm per-cell median expectancy with one-sided CI_low whisker (5 panels)."""
    fig, axes = plt.subplots(2, 3, figsize=(16, 9), sharex=True)
    flat = axes.ravel()
    for ax, a in zip(flat, ARMS):
        rows = sorted([r for r in records if r["arm"] == a.aid and r["member"]
                       and r["median"] is not None], key=lambda r: r["median"])
        if not rows:
            ax.text(0.5, 0.5, "no powered cells", ha="center", va="center")
            ax.set_title(a.aid, fontsize=9)
            continue
        med = np.array([r["median"] for r in rows])
        low = np.array([r["ci_low_1s"] if r["ci_low_1s"] is not None else np.nan for r in rows])
        y = np.arange(len(rows))
        colours = ["#1a9850" if r["win"] else ("#a6d96a" if r["viable"] else "#999999")
                   for r in rows]
        ax.scatter(med, y, color=colours, s=12, zorder=3)
        ax.hlines(y, np.minimum(low, med), med, color=colours, alpha=0.6, zorder=2)
        ax.axvline(0.0, color="k", lw=0.7, ls="--")
        ax.set_yticks(y, [_cell_label(r) for r in rows], fontsize=4)
        ax.set_title(a.aid, fontsize=9)
    for ax in flat[len(ARMS):]:
        ax.axis("off")
    fig.suptitle(f"{EXPERIMENT_ID}: per-cell median expectancy by arm (binding /STRONG-STAT)")
    fig.supxlabel("median gross position-weighted expectancy (ATR units)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_contrast_heatmap(records: list[dict[str, Any]], save_path: Path) -> None:
    """Arm (rows) x cell (cols) paired contrast_bench_low heatmap (alternatives)."""
    cells = _ordered_cells(records)
    matrix = np.full((len(ALT_ARMS), len(cells)), np.nan)
    win = np.zeros_like(matrix, dtype=bool)
    lookup = {(r["arm"], _cell_label(r)): r for r in records if r["member"]}
    for i, a in enumerate(ALT_ARMS):
        for j, ccell in enumerate(cells):
            r = lookup.get((a.aid, ccell))
            if r and r["contrast_bench_low"] is not None and np.isfinite(r["contrast_bench_low"]):
                matrix[i, j] = r["contrast_bench_low"]
                win[i, j] = r["win"]
    fig, ax = plt.subplots(figsize=(max(8, 0.16 * len(cells)), 4))
    vmax = np.nanmax(np.abs(matrix)) if np.isfinite(matrix).any() else 1.0
    im = ax.imshow(matrix, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")
    for (i, j) in zip(*np.where(win)):
        ax.text(j, i, "*", ha="center", va="center", fontsize=7, color="k")
    ax.set_yticks(range(len(ALT_ARMS)), [a.aid for a in ALT_ARMS], fontsize=7)
    ax.set_xticks(range(len(cells)), cells, rotation=90, fontsize=3)
    ax.set_title(f"{EXPERIMENT_ID}: paired arm-benchmark contrast CI_low (* = binding WIN)")
    fig.colorbar(im, ax=ax, label="CI_low(delta) (ATR units)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_cap_isolation(records: list[dict[str, Any]], save_path: Path) -> None:
    """Cap-isolation contrast (uncapped - capped sibling) per cell, per binding arm.

    Plots the **divergent-subset** contrast (``capiso_div_low``) — events the uncapped
    arm held past the cap, the only ones whose exit can differ — not the full-common
    contrast that is dominated by structural zeros (F02). Each bar is annotated with
    the divergent share (fraction of paired events that actually diverge); a faint
    bar with a tiny share means the cap rarely binds differently in that cell.
    """
    cells = _ordered_cells(records)
    lookup = {(r["arm"], _cell_label(r)): r for r in records if r["member"]}
    fig, axes = plt.subplots(len(BINDING_ARMS), 1, figsize=(max(8, 0.16 * len(cells)), 7),
                             sharex=True)
    axes = np.atleast_1d(axes)
    for ax, a in zip(axes, BINDING_ARMS):
        vals, shares, xs = [], [], []
        for j, ccell in enumerate(cells):
            r = lookup.get((a.aid, ccell))
            if r and r.get("capiso_div_low") is not None and np.isfinite(r["capiso_div_low"]):
                xs.append(j)
                vals.append(r["capiso_div_low"])
                shares.append(r.get("capiso_div_share") or 0.0)
        if xs:
            colours = ["#1a9850" if v > 0 else "#d73027" for v in vals]
            alphas = [0.35 + 0.65 * min(1.0, s) for s in shares]   # faint = small share
            ax.bar(xs, vals, color=colours, alpha=1.0)
            for x, v, al in zip(xs, vals, alphas):
                ax.bar([x], [v], color="white", alpha=1.0 - al, zorder=3)
        ax.axhline(0.0, color="k", lw=0.7, ls="--")
        ax.set_title(f"{a.aid} - {a.sibling}  (cap-isolation, divergent subset, disclosed)",
                     fontsize=9)
        ax.set_ylabel("CI_low(delta) | div")
    axes[-1].set_xticks(range(len(cells)), cells, rotation=90, fontsize=3)
    fig.suptitle(f"{EXPERIMENT_ID}: cap-isolation contrast on the divergent subset "
                 "(held past cap; bar opacity ~ divergent share)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_wins_censoring(records: list[dict[str, Any]], save_path: Path) -> None:
    """Per-arm win/instrument counts + status grid + separated censoring rate."""
    cells = _ordered_cells(records, include_excluded=True)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(max(9, 0.16 * len(cells)), 10))
    win_counts = [sum(1 for r in records if r["arm"] == a.aid and r["member"] and r["win"])
                  for a in ARMS]
    inst_counts = [len({r["instrument"] for r in records if r["arm"] == a.aid
                        and r["member"] and r["win"]}) for a in ARMS]
    cens_rate = [_mean_censor_rate(records, a.aid) for a in ARMS]
    x = np.arange(len(ARMS))
    ax1.bar(x - 0.27, win_counts, 0.27, label="winning cells", color="#1a9850")
    ax1.bar(x, inst_counts, 0.27, label="winning instruments", color="#4575b4")
    ax1b = ax1.twinx()
    ax1b.bar(x + 0.27, cens_rate, 0.27, label="mean censor rate", color="#cccccc")
    ax1b.set_ylabel("mean DATA_CENSORED / built")
    ax1.axhline(P11_MIN_CELLS, color="k", lw=0.9, ls="--", label=f"P11 cells={P11_MIN_CELLS}")
    ax1.set_xticks(x, [a.aid for a in ARMS], rotation=20, fontsize=7)
    ax1.set_ylabel("count")
    ax1.set_title("wins-over-benchmark + separated censoring (P11: >=5 cells / >=3 instruments)")
    ax1.legend(fontsize=7, loc="upper left")
    ax1b.legend(fontsize=7, loc="upper right")
    matrix = np.full((len(ARMS), len(cells)), VSTATUS_CODES["EXCLUDED"])
    lookup = {(r["arm"], _cell_label(r)): r for r in records}
    for i, a in enumerate(ARMS):
        for j, ccell in enumerate(cells):
            r = lookup.get((a.aid, ccell))
            if r is not None:
                matrix[i, j] = r["status_code"]
    cmap = ListedColormap(VSTATUS_COLORS)
    norm = BoundaryNorm(np.arange(-0.5, len(VSTATUS_COLORS) + 0.5), cmap.N)
    ax2.imshow(matrix, cmap=cmap, norm=norm, aspect="auto")
    ax2.set_yticks(range(len(ARMS)), [a.aid for a in ARMS], fontsize=7)
    ax2.set_xticks(range(len(cells)), cells, rotation=90, fontsize=3)
    ax2.set_title("per (arm, cell) win-composition status")
    handles = [plt.Rectangle((0, 0), 1, 1, color=VSTATUS_COLORS[cd])
               for cd in VSTATUS_CODES.values()]
    ax2.legend(handles, list(VSTATUS_CODES.keys()), bbox_to_anchor=(1.01, 1),
               loc="upper left", fontsize=7)
    fig.suptitle(f"{EXPERIMENT_ID}: wins-over-benchmark + power/censoring")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _mean_censor_rate(records: list[dict[str, Any]], aid: str) -> float:
    rates = []
    for r in records:
        if r["arm"] == aid and r["member"] and r.get("n_buildable"):
            denom = r["n_buildable"] or 0
            if denom > 0 and r.get("data_censored") is not None:
                rates.append(r["data_censored"] / denom)
    return float(np.mean(rates)) if rates else 0.0


def plot_exit_reasons(records: list[dict[str, Any]], save_path: Path) -> None:
    """Per-arm pooled exit-reason composition (stacked) + holding-duration percentiles."""
    labels = list(PX_CLASS_LABELS.values())
    colours = {"DATA_CENSORED": "#cccccc", "TIMECAP": "#fdae61", "ADV": "#d73027",
               "FAV": "#1a9850", "FIRST_PROFIT": "#66bd63", "REVERSAL": "#4575b4",
               "TRAIL": "#762a83"}
    arms = [a.aid for a in ARMS]
    comp = np.zeros((len(arms), len(labels)))
    hold_p50 = np.zeros(len(arms))
    hold_p90 = np.zeros(len(arms))
    for i, aid in enumerate(arms):
        rows = [r for r in records if r["arm"] == aid and r["member"] and r["m"] > 0]
        if rows:
            for k, lab in enumerate(labels):
                comp[i, k] = float(np.mean([r[f"ew_{lab}"] for r in rows]))
            hp50 = [r["hold_p50"] for r in rows if r.get("hold_p50") is not None]
            hp90 = [r["hold_p90"] for r in rows if r.get("hold_p90") is not None]
            hold_p50[i] = float(np.median(hp50)) if hp50 else 0.0
            hold_p90[i] = float(np.median(hp90)) if hp90 else 0.0
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6), gridspec_kw={"width_ratios": [3, 2]})
    bottom = np.zeros(len(arms))
    x = np.arange(len(arms))
    for k, lab in enumerate(labels):
        ax1.bar(x, comp[:, k], bottom=bottom, label=lab, color=colours[lab])
        bottom += comp[:, k]
    ax1.set_xticks(x, arms, rotation=20, fontsize=7)
    ax1.set_ylabel("mean weight fraction (qualifying events)")
    ax1.set_title("exit-reason composition by arm (mechanism diagnostic)")
    ax1.legend(fontsize=6, ncol=2)
    ax2.bar(x - 0.2, hold_p50, 0.4, label="median hold (bars)", color="#4575b4")
    ax2.bar(x + 0.2, hold_p90, 0.4, label="p90 hold (bars)", color="#91bfdb")
    ax2.set_xticks(x, arms, rotation=20, fontsize=7)
    ax2.set_ylabel("holding duration (bars; measured exit offset, all arms)")
    ax2.set_title("holding duration by arm")
    ax2.legend(fontsize=7)
    fig.suptitle(f"{EXPERIMENT_ID}: exit-reason composition + holding duration")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def make_plots(records: list[dict[str, Any]], pooled: dict[str, list[float]]) -> None:
    """Render the five bounded plots from collected summaries + pooled events."""
    plot_arm_forest(records, PLOTS_DIR / "per_arm_median_forest.png")
    plot_contrast_heatmap(records, PLOTS_DIR / "arm_benchmark_contrast_heatmap.png")
    plot_cap_isolation(records, PLOTS_DIR / "cap_isolation_contrast.png")
    plot_wins_censoring(records, PLOTS_DIR / "p11_wins_censoring.png")
    plot_exit_reasons(records, PLOTS_DIR / "exit_reason_holding.png")


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _cell_index_map() -> dict[tuple[str, str], int]:
    return {(inst, dom): i for i, (inst, dom) in enumerate(
        (inst, dom) for inst in INSTRUMENTS for dom in DOMAINS)}


def _collect_pooled(cell: dict[str, Any], cell_records: list[dict[str, Any]],
                    pooled: dict[str, list[float]]) -> None:
    """Pool per-event returns from binding-viable cells (per arm) for the violin."""
    if cell.get("empty"):
        return
    viable = {r["arm"] for r in cell_records if r["viable"]}
    for a in ARMS:
        if a.aid in viable:
            pooled[a.aid].extend(cell["arms"]["stat"]["arms"][a.aid].r_e.tolist())


def _worker_count() -> int:
    """Parallel instrument workers: ``XEN_WORKERS`` env override, else a bounded default.

    Cells are independent and seeded by ``cell_index`` (not execution order), so any
    worker count produces byte-identical results — only wall-clock changes.
    ``XEN_WORKERS=1`` forces the serial path (determinism debugging / low memory).
    """
    env = os.environ.get("XEN_WORKERS")
    if env is not None:
        try:
            return max(1, int(env))
        except ValueError:
            LOGGER.warning("ignoring non-integer XEN_WORKERS=%r", env)
    return max(1, min(os.cpu_count() or 1, len(INSTRUMENTS), DEFAULT_WORKERS_CAP))


def _empty_defect() -> dict[str, Any]:
    return {"is_defect": False, "non_deterministic": [], "reconciliation": [],
            "causality_violations": [], "determinism_checked": [], "invariant_violations": []}


def _process_instrument(instrument: str, exp053: dict[Any, Any]) -> dict[str, Any]:
    """Compute every member cell of one instrument; return order-independent fragments.

    Pure given the inputs and the frozen per-cell seeds — safe to run in a worker
    process. The determinism + reconciliation guard runs once on the **lightest**
    member cell (the last usable domain in ``DOMAINS`` order), not the heavy 5m cell.
    """
    cell_index = _cell_index_map()
    frag: dict[str, Any] = {
        "instrument": instrument, "records": [], "secondaries": [], "recon_rows": [],
        "pooled": {a.aid: [] for a in ARMS}, "meta": None, "defect": _empty_defect()}
    members = [d for d in DOMAINS if (instrument, d) not in EXCLUDED_CELLS]
    if not members:
        for domain in DOMAINS:
            frag["records"].extend(excluded_records(instrument, domain))
        return frag
    train_1m, meta = load_train_1m(instrument)
    frag["meta"] = meta
    guard_target: tuple[str, int] | None = None
    for domain in DOMAINS:
        if (instrument, domain) in EXCLUDED_CELLS:
            frag["records"].extend(excluded_records(instrument, domain))
            continue
        ci = cell_index[(instrument, domain)]
        cell = compute_cell(train_1m, domain, meta["train_end_epoch_s"], ci)
        car = cell_arm_records(instrument, cell)
        frag["records"].extend(car)
        frag["secondaries"].extend(secondary_records(instrument, cell))
        _collect_pooled(cell, car, frag["pooled"])
        frag["recon_rows"].append(exp053_reconciliation(instrument, cell, exp053))
        _record_cell_defects(cell, instrument, domain, frag["defect"])
        if not cell.get("empty") and cell["arms"]["stat"]["arms"]["BENCH"].m > 0:
            guard_target = (domain, ci)            # keep last usable = lightest domain
        del cell
    if guard_target is not None:
        _run_guard(train_1m, meta, guard_target, instrument, frag["defect"])
    del train_1m
    return frag


def _run_guard(
    train_1m: pl.DataFrame, meta: dict[str, Any], guard_target: tuple[str, int],
    instrument: str, defect: dict[str, Any],
) -> None:
    """Determinism replay + BENCH reconciliation on one (light) cell per instrument."""
    gdom, gci = guard_target
    gcell = compute_cell(train_1m, gdom, meta["train_end_epoch_s"], gci)
    ok = determinism_replay(gcell, train_1m, gdom, meta["train_end_epoch_s"], gci)
    defect["determinism_checked"].append(f"{instrument}-{gdom}#{gci}")
    recon = reconciliation_anchor(gcell)
    recon["instrument"], recon["cell"] = instrument, f"{instrument}-{gdom}"
    defect["reconciliation"].append(recon)
    if not ok:
        defect["non_deterministic"].append(f"{instrument}-{gdom}#{gci}")
    if not ok or (recon.get("checked") and not recon.get("consistent")):
        defect["is_defect"] = True


def run() -> dict[str, Any]:
    """Run all member cells (parallel over instruments) and write artifacts."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    exp053 = load_exp053_benchmark()
    workers = _worker_count()
    LOGGER.info("computing %d instruments with %d worker(s)", len(INSTRUMENTS), workers)
    if workers > 1:
        # Bound polars/BLAS threads in spawned workers to avoid CPU oversubscription
        # (deterministic regardless of thread count; only speed is affected).
        os.environ.setdefault("POLARS_MAX_THREADS", "2")
        frags_by_inst: dict[str, dict[str, Any]] = {}
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(_process_instrument, inst, exp053): inst for inst in INSTRUMENTS}
            for fut in tqdm(as_completed(futs), total=len(futs), desc="instruments"):
                frags_by_inst[futs[fut]] = fut.result()
        frag_list = [frags_by_inst[inst] for inst in INSTRUMENTS]   # deterministic order
    else:
        frag_list = [_process_instrument(inst, exp053)
                     for inst in tqdm(INSTRUMENTS, desc="instruments")]

    records, secondaries, recon_rows = [], [], []
    pooled: dict[str, list[float]] = {a.aid: [] for a in ARMS}
    instrument_meta: dict[str, Any] = {}
    defect = {"is_defect": False, "non_deterministic": [], "reconciliation": [],
              "exp053_mismatch": [], "causality_violations": [], "determinism_checked": [],
              "invariant_violations": [], "exp053_available": bool(exp053),
              "exp053_checked_cells": 0}
    for frag in frag_list:                                         # INSTRUMENTS order
        records.extend(frag["records"])
        secondaries.extend(frag["secondaries"])
        recon_rows.extend(frag["recon_rows"])
        for aid in pooled:
            pooled[aid].extend(frag["pooled"][aid])
        if frag["meta"] is not None:
            instrument_meta[frag["instrument"]] = frag["meta"]
        fd = frag["defect"]
        for k in ("non_deterministic", "reconciliation", "causality_violations",
                  "determinism_checked", "invariant_violations"):
            defect[k].extend(fd[k])
        if fd["is_defect"]:
            defect["is_defect"] = True

    _finalize_defects(defect, recon_rows)
    readout = composition_readout(records, defect)
    write_outputs(records, secondaries, recon_rows, readout, pooled, instrument_meta, defect)
    make_plots(records, pooled)
    return _summarize(records, readout)


def _record_cell_defects(cell: dict[str, Any], instrument: str, domain: str,
                         defect: dict[str, Any]) -> None:
    """Accumulate per-cell causality / invariant violations."""
    if cell.get("empty"):
        return
    label = f"{instrument}-{domain}"
    if not cell.get("causality_ok", True):
        defect["causality_violations"].append(label)
    inv = cell.get("invariants", {})
    if not all(inv.get(k, True) for k in (
            "weights_sum_ok", "degenerate_match", "shared_stop_ok", "no_timecap",
            "edge_ok", "trail_monotone", "lazy_dense_prefix_ok")):
        defect["invariant_violations"].append(label)


def _finalize_defects(defect: dict[str, Any], recon_rows: list[dict[str, Any]]) -> None:
    """Aggregate defect gates (analysis-plan Step 13) into the binding is_defect flag."""
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
    if defect["invariant_violations"]:
        defect["is_defect"] = True


def write_outputs(
    records: list[dict[str, Any]], secondaries: list[dict[str, Any]],
    recon_rows: list[dict[str, Any]], readout: dict[str, Any],
    pooled: dict[str, list[float]], instrument_meta: dict[str, Any],
    defect: dict[str, Any],
) -> None:
    """Persist per-cell parquet, the arm maps, reconciliation, and the JSONs."""
    pl.DataFrame(records, strict=False).write_parquet(RESULTS_DIR / "per_cell_expectancy.parquet")
    pl.DataFrame(records, strict=False).write_csv(RESULTS_DIR / "uncapped_trailing_map.csv")
    sec_df = (pl.DataFrame(secondaries, strict=False) if secondaries
              else pl.DataFrame({"signal": [], "arm": []}))
    sec_df.write_csv(RESULTS_DIR / "secondary_map.csv")
    recon_clean = [r for r in recon_rows if r.get("checked")]
    (pl.DataFrame(recon_clean, strict=False) if recon_clean
     else pl.DataFrame({"cell": []})).write_csv(RESULTS_DIR / "population_reconciliation.csv")
    with open(RESULTS_DIR / "composition_readout.json", "w") as fh:
        json.dump(readout, fh, indent=2, default=str)
    pooled_rows = [{"arm": a, "r_e": x} for a, xs in pooled.items() for x in xs]
    (pl.DataFrame(pooled_rows) if pooled_rows
     else pl.DataFrame({"arm": [], "r_e": []}, schema={"arm": pl.Utf8, "r_e": pl.Float64})
     ).write_parquet(RESULTS_DIR / "per_event_returns.parquet")
    _write_metadata(instrument_meta, defect, recon_clean)


def _resolver_hashes() -> dict[str, str]:
    """SHA-256 of each resolver function's source (F06 — pin the post-fix baseline).

    Records a content hash of the frozen capped resolvers (whose behaviour EXP-059's
    results depend on) and the new uncapped resolver, so a later silent edit is
    detectable by diffing this map against the value committed alongside EXP-059B.
    The F04 change added an *additive* exit-offset return/out-param to the capped
    resolvers; these hashes pin that exact post-fix source as the new baseline.
    """
    targets = {
        "position_exits.resolve_legs": _pe_mod.resolve_legs,
        "position_exits._scan_event": _pe_mod._scan_event,
        "position_exits.build_active_stops": _pe_mod.build_active_stops,
        "position_exits.resolve_legs_uncapped": _pe_mod.resolve_legs_uncapped,
        "position_exits._scan_event_uncapped": _pe_mod._scan_event_uncapped,
        "position_exits.weighted_returns": _pe_mod.weighted_returns,
        "expectancy.resolve_path_ordered": _xe_mod.resolve_path_ordered,
        "expectancy._scan_path": _xe_mod._scan_path,
    }
    return {name: hashlib.sha256(inspect.getsource(fn).encode("utf-8")).hexdigest()
            for name, fn in targets.items()}


def _write_metadata(
    instrument_meta: dict[str, Any], defect: dict[str, Any], recon_clean: list[dict[str, Any]],
) -> None:
    meta = {
        "experiment_id": EXPERIMENT_ID,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "014-B", "hypothesis": "HYP-012b", "family": "CF-HA-HARAMI-001",
        "follow_up_to": "EXP-059",
        "stratum": "TRAIN-only (first 49%); nested TEST + final-30% holdout sealed",
        "entry_anchor": "harami confirmation-bar real close (live, pre-ZigZag-confirm)",
        "binding_arm": "/STRONG-STAT p75; /STRONG-HA disclosed",
        "binding_endpoint": ("median per-event position-weighted gross ATR-normalised return "
                             "(P14, P15 fills)"),
        "model": ("OAT on the adverse-exit model: /EXIT-TRAIL-UNCAPPED (no time-cap backstop, "
                  "no initial stop). Favourable side (50% benchmark, where present) held at "
                  "benchmark; uncapped arms have no third barrier."),
        "arms": {a.aid: {"kind": a.kind, "sibling": a.sibling} for a in ARMS},
        "binding_arms": [a.aid for a in BINDING_ARMS],
        "params": {
            "atr_period": ATR_PERIOD, "atr_mult_primary": ATR_MULT,
            "atr_mult_trail": ATR_MULT_TRAIL, "favourable_fraction_bench": 0.50,
            "adverse_bench": "1:1 (BENCH only)", "n_legs_combined": 3,
            "leg_weights": "equal (1/3)", "v2a_fracs": [1 / 3, 2 / 3, 1.0],
            "trailing_ratchet": ("monotone to most-recent confirmed secondary pivot; "
                                 "uncapped arms: no initial stop, no time cap"),
            "timecap_floor_bench": 6, "stat_window": 20, "stat_min_window": 5, "stat_q": 0.75,
            "ha_run_len": 3, "ma_segmentation": [MA_FAST, MA_SLOW], "power_floor": POWER_FLOOR,
            "n_boot": 10000, "base_seed": BASE_SEED, "p11": [P11_MIN_CELLS, P11_MIN_INSTR],
        },
        "baselines": ["matched-count random (in-progress rd, non-signal pool, per arm)",
                      "MA(20,50)-crossover segmentation per arm (identical pipeline)"],
        "contrasts": {"arm_vs_benchmark": "paired moving-block bootstrap (binding)",
                      "cap_isolation": ("paired moving-block bootstrap: uncapped arm vs its "
                                        "capped no-init sibling (disclosed). Reported on BOTH the "
                                        "full common subset (capiso_full_*, dominated by "
                                        "within-cap structural zeros) and the DIVERGENT subset "
                                        "(capiso_div_*, events held past bench_n) with "
                                        "capiso_div_share; the divergent contrast is the "
                                        "interpretable cap effect (F02)."),
                      "arm_vs_baseline": "independent bootstrap contrast (disclosed)"},
        "determinism_ok": not defect["non_deterministic"],
        "determinism_checked": defect["determinism_checked"],
        "determinism_gate": ("byte-identical re-run of the lightest usable cell per instrument "
                             "across all 5 arms' stat returns/hold_off/median/CI and baselines "
                             "(one extra recompute vs the live cell). Instruments run in parallel "
                             "worker processes; cells are seeded by cell_index, so the worker "
                             "count never changes results — only wall-clock."),
        "causality_ok": not defect["causality_violations"],
        "causality_violations": defect["causality_violations"],
        "invariant_violations": defect["invariant_violations"],
        "invariant_gates": ("leg weights sum to 1.0; degenerate 3-leg all-LEVEL@fav uncapped == "
                            "single-leg uncapped R_event (<=1e-9); uncapped trailing binds all "
                            "open legs at one level; uncapped arms emit NO TIMECAP; all uncapped "
                            "exits within [entry+1, last_train_idx]; trailing monotone; lazy "
                            "uncapped stop == dense capped (no-init) stop on the shared "
                            "[entry+1, entry+bench_n] prefix (<=1e-9); BENCH reproduces EXP-053 "
                            "per-cell median + count + first-hit r to 1e-9. The O(train_len) "
                            "uncapped re-resolution invariants (degenerate, shared-stop, "
                            "no-TIMECAP, edge) run on a bounded evenly-spaced sample of up to "
                            f"{INVARIANT_MAX_EVENTS} conditioned events per cell (F03); the "
                            "dense-bounded monotone + lazy==dense-prefix checks run on the full "
                            "conditioned population."),
        "reconciliation": defect["reconciliation"],
        "exp053_reconciliation": recon_clean,
        "exp053_mismatch": defect["exp053_mismatch"],
        "exp053_available": defect["exp053_available"],
        "exp053_checked_cells": defect["exp053_checked_cells"],
        "censoring_disclosure": ("uncapped DATA_CENSORED (unbounded window reaches the TRAIN "
                                 "edge) is reported SEPARATELY from capped censoring; it drives "
                                 "the power readout and gates the vs-BENCH contrast (the common "
                                 "qualifying subset excludes censored events)."),
        "holding_disclosure": ("holding duration: the MEASURED resolving exit offset "
                               "(exit_idx - entry_idx) for EVERY arm, including BENCH "
                               "(resolve_path_ordered) and the capped siblings (resolve_legs) "
                               "which now return the real fill bar rather than the bench_n "
                               "ceiling (F04). Uncapped arms hold to the trailing fill or the "
                               "TRAIN edge."),
        "is_defect": defect["is_defect"],
        "resolver_source_sha256": _resolver_hashes(),
        "de30_disclosure": DE30_DISCLOSURE,
        "fill_approximation": ("P15 path is a documented approximation of unobserved intrabar "
                               "motion; 1-minute base bars are not replayed (EXP-054 bounds it)."),
        "holdout_fence": ("Only Parquet metadata + first train_rows file-order rows read per "
                          "instrument; full file never sorted/collected; every domain bar fenced "
                          "to CloseTime <= train_end_ts; uncapped forward scans run to "
                          "last_train_idx and clip to the data edge -> DATA_CENSORED; TEST and "
                          "final-30% holdout never read."),
        "registry": ("CF-HA-HARAMI-001/HYP-012b (EXP-059B); exercises the new countable "
                     "/EXIT-TRAIL-UNCAPPED branch (with /EXIT-PARTIAL V2A in the combined arm); "
                     "0 candidate slots, 0 TEST reads; characterization readout feeds 014-B G2."),
        "instrument_meta": instrument_meta,
    }
    with open(RESULTS_DIR / "run_metadata.json", "w") as fh:
        json.dump(meta, fh, indent=2, default=str)


def _summarize(records: list[dict[str, Any]], readout: dict[str, Any]) -> dict[str, Any]:
    """Concise stdout summary."""
    status_counts: dict[str, int] = {}
    for r in records:
        status_counts[r["viable_status"]] = status_counts.get(r["viable_status"], 0) + 1
    return {"verdict": readout["verdict"], "n_pass": readout["n_pass"],
            "passing_arms": readout["passing_arms"],
            "fragile_passes": readout["fragile_passes"], "status_counts": status_counts,
            "defect": readout["defect"]}


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    summary = run()
    LOGGER.info("\n=== %s complete ===", EXPERIMENT_ID)
    LOGGER.info("verdict: %s", summary["verdict"])
    LOGGER.info("passing (binding) arms (%s): %s", summary["n_pass"], summary["passing_arms"])
    if summary["fragile_passes"]:
        LOGGER.info("fragile (bare-quorum) passes: %s", summary["fragile_passes"])
    LOGGER.info("status counts (per cell-arm): %s", json.dumps(summary["status_counts"]))
    if summary["defect"]["is_defect"]:
        LOGGER.info("DEFECT: %s", json.dumps(summary["defect"], default=str))
    LOGGER.info("artifacts -> %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
