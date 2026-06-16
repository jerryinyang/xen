"""EXP-057 — Adverse-Target Geometry (Conditioned HA Harami).

``CF-HA-HARAMI-001`` / HYP-010 (Phase 014-B surface read 2). TRAIN-only, gross;
0 candidate slots, 0 TEST reads. For each EXP-049/053 member cell (instrument x
domain), on the TRAIN analysis stratum only, this script:

1. slices the first-49% (TRAIN) 1-minute rows by file-order prefix (TEST and the
   final-30% global holdout are never read), aggregates the domain (5m strict;
   others min_coverage=0.90) and fences to the TRAIN edge;
2. reproduces the **EXP-053 conditioned population byte-identically** — frozen
   Wilder-ATR ZigZag substrate, HA haramis mapped to real bars by exact CloseTime
   match, the live in-progress move at each harami, and the binding ``/STRONG-STAT``
   (p75) filter (``/STRONG-HA`` same-dir and STAT-MAD disclosed) — entered at the
   harami real close and faded against the in-progress move;
3. varies **only the adverse target** over a predeclared sweep of 4 binding
   variants (``BENCH`` 1:1; ``ADV-EXTREME-raw`` buffered faded-move extreme;
   ``ADV-EXTREME-rr1`` extreme widened to >=1:1; ``ADV-NONE`` no stop); the
   favourable target (50% of M_sofar), the third barrier (adaptive cap), and the
   P15 path-ordered intrabar fills are held at benchmark;
4. computes per-cell **median** ATR-normalised gross expectancy with the
   regime-clustered moving-block bootstrap CI, the **paired** variant-benchmark
   contrast (binding), two P13 baselines (matched-random, MA(20,50)-seg) per
   binding variant with independent contrasts (disclosed), composes each variant
   by P11 (>=5 cells over >=3 instruments) and emits a mechanical EVIDENCE_*
   readout; and
5. runs a determinism replay, a BENCH reconciliation anchor, a cross-check of the
   BENCH stat arm against EXP-053's recorded benchmark, and the predeclared
   adverse invariants (raw adv_dist <= rr1 adv_dist; ADV-NONE 0 ADV outcomes;
   raw adverse-side ordering) as SUBSTRATE/METHOD_DEFECT guards.

Real prices throughout; HA prices enter only the harami/impulse detectors and
never any metric. Outputs under results/ and plots/; created in orchestration.
"""
from __future__ import annotations

import json
import logging
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

from xen.adverse_targets import (  # noqa: E402
    ADV_BUFFER_FRAC,
    ADV_FLOOR_FRAC,
    adverse_extreme_raw,
    adverse_extreme_rr1,
    adverse_none_sentinel,
    faded_move_extreme,
)
from xen.bar_aggregator import aggregate_ohlc  # noqa: E402
from xen.capture_barriers import (  # noqa: E402
    CLASS_ADV,
    CLASS_DATA_CENSORED,
    CLASS_FAV,
    CLASS_TIMECAP,
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
from xen.strong_move import annotate_ha_impulse, find_impulse_runs  # noqa: E402
from xen.zigzag import generate_zigzag, wilder_atr  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (Phase 014-B D0 frozen; no tuning)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-057"
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
ATR_MULT = 1.0
MA_FAST, MA_SLOW = 20, 50          # P13 MA-segmentation baseline
POWER_FLOOR = 30                   # P14: minimum qualifying events to report
P11_MIN_CELLS, P11_MIN_INSTR = 5, 3
BASE_SEED = 20260615               # frozen master seed (no tuning)
EXCLUDED_FILE_MARKERS = ("analysis70", "analysis_slice", "first70")
DE30_DISCLOSURE = (
    "DE30 truncated history: broker m1 history ends 2026-01-16; counts derive "
    "from its own realized timeline and are not span-comparable (VAL-003).")
LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# Variant specification (predeclared adverse-target sweep)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class VariantSpec:
    """One predeclared adverse-target variant."""

    vid: str
    idx: int                       # stable RNG / column offset
    kind: str                      # "bench" | "extreme_raw" | "extreme_rr1" | "none"


BINDING_VARIANTS: list[VariantSpec] = [
    VariantSpec("BENCH", 0, "bench"),
    VariantSpec("ADV-EXTREME-raw", 1, "extreme_raw"),
    VariantSpec("ADV-EXTREME-rr1", 2, "extreme_rr1"),
    VariantSpec("ADV-NONE", 3, "none"),
]
ALL_VARIANTS: list[VariantSpec] = BINDING_VARIANTS
ALT_VARIANTS: list[VariantSpec] = [v for v in BINDING_VARIANTS if v.vid != "BENCH"]
VARIANT_BY_ID: dict[str, VariantSpec] = {v.vid: v for v in ALL_VARIANTS}

# RNG purpose bases (distinct deterministic streams per cell/arm/variant/purpose).
PB_STAT, PB_HA, PB_STATMAD = 1000, 2000, 3000           # signal-arm bootstraps
PB_PC_STAT, PB_PC_HA, PB_PC_STATMAD = 4000, 5000, 6000  # paired contrasts vs BENCH
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
    """One (arm, variant) per-cell resolved population summary + returns."""

    m: int
    median: float | None
    mean: float | None
    ci_low_1s: float | None
    ci_lo_2s: float | None
    ci_hi_2s: float | None
    fav: int
    adv: int
    timecap: int
    data_censored: int
    r_firsthit: float | None
    win_rate: float | None
    timecap_frac: float | None
    population: int                # built-barrier population (pre-resolution)
    block_len: int
    r_e: np.ndarray                # qualifying returns in entry order
    r_e_all: np.ndarray            # full-length realised returns (NaN off-pop)
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


def load_exp053_benchmark() -> dict[tuple[str, str], tuple[int, float | None]]:
    """Load EXP-053 per-cell stat (m, median) for the BENCH reconciliation anchor."""
    if not EXP053_OUTCOME.exists():
        return {}
    df = pl.read_csv(EXP053_OUTCOME)
    out: dict[tuple[str, str], tuple[int, float | None]] = {}
    for row in df.iter_rows(named=True):
        med = row.get("stat_median")
        out[(row["instrument"], row["domain"])] = (
            int(row["stat_m"]) if row.get("stat_m") is not None else 0,
            float(med) if med is not None else None)
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


# --------------------------------------------------------------------------- #
# Pure computation — faded-move extreme + per-variant adverse targets
# --------------------------------------------------------------------------- #
def _zero_reasons(n: int) -> dict[str, np.ndarray]:
    return {"reason_validity": np.zeros(n, dtype=bool),
            "reason_warmup": np.zeros(n, dtype=bool),
            "reason_degenerate": np.zeros(n, dtype=bool)}


def faded_extreme_for(
    valid: np.ndarray, k: np.ndarray, end_idx: np.ndarray, low: np.ndarray,
    high: np.ndarray, entry_idx: np.ndarray, rd: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Locate each event's in-progress start bar (``end_idx[k]``) and scan its extreme."""
    n = int(entry_idx.shape[0])
    if end_idx.shape[0] == 0:
        return np.full(n, np.nan, dtype=np.float64), np.zeros(n, dtype=bool)
    avail_in = valid & (k >= 0)
    k_safe = np.where(k >= 0, k, 0)
    start_idx = np.where(avail_in, end_idx[k_safe], -1)
    return faded_move_extreme(low, high, start_idx, entry_idx, rd, avail_in)


def build_variant_targets(
    entry_close: np.ndarray, rd: np.ndarray, m_sofar: np.ndarray,
    faded_extreme: np.ndarray, atr_entry: np.ndarray, ext_avail: np.ndarray,
    variants: list[VariantSpec],
) -> dict[str, dict[str, np.ndarray]]:
    """Build ``(fav, adv, adv_dist, ok, reason_*)`` for each requested variant.

    The favourable target is the benchmark 50%-of-``M_sofar`` level for every
    variant (pure OAT on the adverse leg); only the adverse level differs.
    """
    bench = benchmark_barriers(entry_close, rd, m_sofar)
    fav_dist = bench["fav_dist"]
    n = int(entry_close.shape[0])
    out: dict[str, dict[str, np.ndarray]] = {}
    for v in variants:
        if v.kind == "bench":
            ok = fav_dist > 0.0
            res = _zero_reasons(n)
            res["reason_validity"] = ~ok
            out[v.vid] = {"fav": bench["fav"], "adv": bench["adv"], "fav_dist": fav_dist,
                          "adv_dist": np.where(ok, fav_dist, np.nan), "ok": ok, **res}
        elif v.kind == "extreme_raw":
            out[v.vid] = adverse_extreme_raw(entry_close, rd, fav_dist, faded_extreme,
                                             atr_entry, ext_avail)
        elif v.kind == "extreme_rr1":
            out[v.vid] = adverse_extreme_rr1(entry_close, rd, fav_dist, faded_extreme,
                                             atr_entry, ext_avail)
        else:                                              # none
            out[v.vid] = adverse_none_sentinel(entry_close, rd, fav_dist)
    return out


# --------------------------------------------------------------------------- #
# Pure computation — resolve one (population, targets) -> ArmResult
# --------------------------------------------------------------------------- #
def resolve_targets(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, entry_close: np.ndarray,
    rd: np.ndarray, fav: np.ndarray, adv: np.ndarray, n_event: np.ndarray,
    atr_entry: np.ndarray, population: np.ndarray, rng: np.random.Generator,
) -> ArmResult:
    """P15-resolve the population under one variant's targets and bootstrap median."""
    n_bars = ohlc["close"].shape[0]
    classes, exit_px = resolve_path_ordered(
        ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"], entry_idx,
        fav, adv, rd, n_event, population, n_bars)
    r_e_all = realised_returns(classes, exit_px, entry_close, rd, atr_entry)
    qual = population & qualifying_mask(classes, exit_px, atr_entry)
    order = np.argsort(entry_idx[qual], kind="stable")
    r_e = r_e_all[qual][order]
    fav_n = int((qual & (classes == CLASS_FAV)).sum())
    adv_n = int((qual & (classes == CLASS_ADV)).sum())
    timecap = int((qual & (classes == CLASS_TIMECAP)).sum())
    censored = int((population & (classes == CLASS_DATA_CENSORED)).sum())
    return _summarize_arm(r_e, r_e_all, qual, fav_n, adv_n, timecap, censored,
                          int(population.sum()), rng)


def _summarize_arm(
    r_e: np.ndarray, r_e_all: np.ndarray, qual: np.ndarray, fav: int, adv: int,
    timecap: int, censored: int, population: int, rng: np.random.Generator,
) -> ArmResult:
    """Assemble an ``ArmResult`` and (if powered) bootstrap the median CI."""
    m = int(r_e.shape[0])
    resolved = fav + adv
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
        m=m, median=median, mean=mean, ci_low_1s=ci_low, ci_lo_2s=ci_lo,
        ci_hi_2s=ci_hi, fav=fav, adv=adv, timecap=timecap, data_censored=censored,
        r_firsthit=(fav / resolved if resolved > 0 else None),
        win_rate=(float((r_e > 0).mean()) if m > 0 else None),
        timecap_frac=(timecap / m if m > 0 else None), population=population,
        block_len=block_len, r_e=r_e, r_e_all=r_e_all, qual=qual, dist=dist)


def _empty_arm() -> ArmResult:
    return ArmResult(0, None, None, None, None, None, 0, 0, 0, 0, None, None, None,
                     0, 1, np.empty(0), np.empty(0), np.empty(0, dtype=bool), np.empty(0))


# --------------------------------------------------------------------------- #
# Pure computation — paired variant-benchmark contrast (binding) on one arm
# --------------------------------------------------------------------------- #
def paired_contrasts_vs_bench(
    entry_idx: np.ndarray, arms: dict[str, ArmResult], cell_index: int,
    purpose_base: int,
) -> dict[str, tuple[float, float, float, int, int]]:
    """Paired median contrast of each alternative vs ``BENCH`` on the same events."""
    bench = arms["BENCH"]
    out: dict[str, tuple[float, float, float, int, int]] = {
        "BENCH": (float("nan"), float("nan"), float("nan"), 1, 0)}
    for v in ALT_VARIANTS:
        out[v.vid] = _single_paired(entry_idx, arms[v.vid], bench, cell_index,
                                    purpose_base + v.idx)
    return out


def _single_paired(
    entry_idx: np.ndarray, res: ArmResult, bench: ArmResult, cell_index: int,
    purpose: int,
) -> tuple[float, float, float, int, int]:
    """Paired contrast of one variant vs the BENCH arm on their common subset."""
    common = res.qual & bench.qual
    s_n = int(common.sum())
    if s_n == 0:
        return (float("nan"), float("nan"), float("nan"), 1, 0)
    order = np.argsort(entry_idx[common], kind="stable")
    ci = paired_median_contrast_ci(res.r_e_all[common][order], bench.r_e_all[common][order],
                                   _rng(cell_index, purpose))
    return (*ci, s_n)


# --------------------------------------------------------------------------- #
# Pure computation — P13 baselines per binding variant (disclosed, stat arm)
# --------------------------------------------------------------------------- #
def matched_random_variant(
    ohlc: dict[str, np.ndarray], state_all: InProgressState, mv: dict[str, np.ndarray],
    n_event_all: np.ndarray, warmup_all: np.ndarray, atr_all: np.ndarray,
    signal_idx: np.ndarray, variant: VariantSpec, draw_count: int, cell_index: int,
) -> ArmResult:
    """Matched-count random control for one variant (in-progress rd; non-signal pool)."""
    n_bars = ohlc["close"].shape[0]
    eligible = (state_all.valid & (state_all.m_sofar > 0.0) & np.isfinite(atr_all)
                & (atr_all > 0.0) & (~warmup_all))
    is_signal = np.zeros(n_bars, dtype=bool)
    is_signal[signal_idx] = True
    pool = np.flatnonzero(eligible & ~is_signal)
    if draw_count <= 0 or pool.shape[0] == 0:
        return _empty_arm()
    k = min(draw_count, pool.shape[0])
    drawn = np.sort(_rng(cell_index, PB_RAND_DRAW + variant.idx).choice(
        pool, size=k, replace=False))
    sub = _subset_state(state_all, drawn)
    fe, fe_avail = faded_extreme_for(sub.valid, sub.k, mv["end_idx"], ohlc["low"],
                                     ohlc["high"], drawn, sub.rd)
    t = build_variant_targets(ohlc["close"][drawn], sub.rd, sub.m_sofar, fe,
                              atr_all[drawn], fe_avail, [variant])[variant.vid]
    return resolve_targets(ohlc, drawn, ohlc["close"][drawn], sub.rd, t["fav"], t["adv"],
                           n_event_all[drawn], atr_all[drawn], t["ok"],
                           _rng(cell_index, PB_RAND_BOOT + variant.idx))


def ma_seg_variant(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, entry_epoch: np.ndarray,
    entry_close: np.ndarray, atr_entry: np.ndarray, seg: dict[str, np.ndarray],
    variant: VariantSpec, cell_index: int,
) -> ArmResult:
    """MA(20,50)-segmentation baseline for one variant through the identical pipeline."""
    if seg["confirm_epoch"].shape[0] == 0:
        return _empty_arm()
    state = live_in_progress_state(entry_epoch, entry_close, seg["confirm_epoch"],
                                   seg["end_price"], seg["end_epoch"], seg["direction"])
    n_event, warmup = adaptive_time_caps_by_epoch(
        entry_epoch, seg["confirm_epoch"], seg["confirm_idx"])
    buildable = (state.valid & (state.m_sofar > 0.0) & np.isfinite(atr_entry)
                 & (atr_entry > 0.0) & (~warmup))
    stat = live_strong_stat(state.k, state.m_sofar, seg["magnitude"])
    fe, fe_avail = faded_extreme_for(state.valid, state.k, seg["end_idx"], ohlc["low"],
                                     ohlc["high"], entry_idx, state.rd)
    t = build_variant_targets(entry_close, state.rd, state.m_sofar, fe, atr_entry,
                              fe_avail, [variant])[variant.vid]
    population = buildable & stat["retained_p75"] & t["ok"]
    return resolve_targets(ohlc, entry_idx, entry_close, state.rd, t["fav"], t["adv"],
                           n_event, atr_entry, population,
                           _rng(cell_index, PB_MASEG + variant.idx))


def _rng(cell_index: int, purpose: int) -> np.random.Generator:
    """Deterministic, independent per-cell-per-purpose RNG (reproducible)."""
    return np.random.default_rng([BASE_SEED, cell_index, purpose])


# --------------------------------------------------------------------------- #
# Per-cell causality / invariant gate (analysis-plan Step 9)
# --------------------------------------------------------------------------- #
def cell_causality_ok(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, entry_epoch: np.ndarray,
    state: InProgressState, mv: dict[str, np.ndarray],
) -> bool:
    """Runtime causality checks (analysis-plan Step 9).

    Returns ``False`` (recorded; ``>=3`` instruments -> SUBSTRATE/METHOD_DEFECT)
    if the domain-bar grid is not strictly increasing, any in-progress reference
    move is not strictly causal (``EndTime_k < t_i``), the entry bar is not
    ``<= t_i``, or the faded-move start bar lies after the entry bar.
    """
    epoch = ohlc["epoch"]
    if epoch.shape[0] >= 2 and not bool(np.all(np.diff(epoch) > 0)):
        return False                               # duplicate/disordered CloseTime
    valid = state.valid & (state.k >= 0)
    if valid.any():
        kk = state.k[valid]
        if not bool(np.all(mv["end_epoch"][kk] < entry_epoch[valid])):
            return False                           # reference move ends before entry
        if not bool(np.all(epoch[entry_idx[valid]] <= entry_epoch[valid])):
            return False                           # entry bar is itself (<= t_i)
        if not bool(np.all(mv["end_idx"][kk] <= entry_idx[valid])):
            return False                           # faded-move span ends at/before entry
    return True


def cell_invariants(
    targets: dict[str, dict[str, np.ndarray]], buildable: np.ndarray,
    stat_mask: np.ndarray, ext_avail: np.ndarray, atr_entry: np.ndarray,
) -> dict[str, bool]:
    """Predeclared adverse invariants 2 & 4 (analysis-plan Step 9)."""
    raw = targets["ADV-EXTREME-raw"]
    rr1 = targets["ADV-EXTREME-rr1"]
    both = (buildable & stat_mask & ext_avail & np.isfinite(atr_entry) & (atr_entry > 0.0))
    raw_le_rr1 = True
    if bool(both.any()):
        raw_le_rr1 = bool(np.all(rr1["adv_dist"][both] >= raw["adv_dist"][both] - 1e-9))
    ok_raw = raw["ok"]
    adv_ordering = True
    if bool(ok_raw.any()):
        adv_ordering = bool(np.all(raw["adv_dist"][ok_raw] > 0.0))
    return {"raw_le_rr1": raw_le_rr1, "adv_ordering": adv_ordering}


# --------------------------------------------------------------------------- #
# Per-cell orchestration
# --------------------------------------------------------------------------- #
def compute_cell(
    train_1m: pl.DataFrame, domain: str, train_end_epoch: int, cell_index: int,
) -> dict[str, Any]:
    """Full Step 1-7 pipeline for one cell. Pure given identical inputs/seeds."""
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

    entry_close = ohlc["close"][entry_idx]
    state = live_in_progress_state(entry_epoch, entry_close, mv["confirm_epoch"],
                                   mv["end_price"], mv["end_epoch"], mv["direction"])
    n_event, warmup = adaptive_time_caps_by_epoch(
        entry_epoch, mv["confirm_epoch"], mv["confirm_idx"])
    atr_entry = atr[entry_idx]
    buildable = (state.valid & (state.m_sofar > 0.0) & np.isfinite(atr_entry)
                 & (atr_entry > 0.0) & (~warmup))
    stat = live_strong_stat(state.k, state.m_sofar, mv["magnitude"])
    ha_same = strong_ha_retention(ha_ann, entry_epoch, state.start_epoch,
                                  -state.rd, state.valid)
    faded_extreme, ext_avail = faded_extreme_for(
        state.valid, state.k, mv["end_idx"], ohlc["low"], ohlc["high"], entry_idx, state.rd)
    targets = build_variant_targets(entry_close, state.rd, state.m_sofar, faded_extreme,
                                    atr_entry, ext_avail, ALL_VARIANTS)

    arms = _resolve_all_arms(ohlc, entry_idx, entry_close, state, n_event, atr_entry,
                             buildable, targets, stat, ha_same, cell_index)
    baselines = _resolve_baselines(ohlc, entry_idx, entry_epoch, entry_close, atr,
                                   atr_entry, mv, stat["retained_p75"],
                                   arms["stat"]["variants"], cell_index)
    conditioned = buildable & stat["retained_p75"]
    invariants = cell_invariants(targets, buildable, stat["retained_p75"], ext_avail, atr_entry)
    return {
        **base, "empty": False, "arms": arms, "baselines": baselines,
        "targets": targets, "buildable_mask": buildable, "stat_mask": stat["retained_p75"],
        "buildable": int(buildable.sum()), "conditioned": int(conditioned.sum()),
        "conditioned_digest": int(entry_epoch[conditioned].sum(dtype=np.int64)),
        "causality_ok": cell_causality_ok(ohlc, entry_idx, entry_epoch, state, mv),
        "invariants": invariants, "none_adv": _none_adv_count(arms, baselines),
    }


def _none_adv_count(arms: dict[str, Any], baselines: dict[str, Any]) -> int:
    """Count resolved ADV outcomes under /ADV-NONE across every arm (must be 0)."""
    total = sum(arms[arm]["variants"]["ADV-NONE"].adv for arm in arms)
    total += baselines["ADV-NONE"]["matched_random"].adv
    total += baselines["ADV-NONE"]["ma_seg"].adv
    return int(total)


def _resolve_all_arms(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, entry_close: np.ndarray,
    state: InProgressState, n_event: np.ndarray, atr_entry: np.ndarray,
    buildable: np.ndarray, targets: dict[str, dict[str, np.ndarray]],
    stat: dict[str, np.ndarray], ha_same: np.ndarray, cell_index: int,
) -> dict[str, dict[str, Any]]:
    """Resolve every variant on the binding and disclosed signal arms + contrasts."""
    def resolve(mask: np.ndarray, v: VariantSpec, pb: int) -> ArmResult:
        t = targets[v.vid]
        pop = buildable & mask & t["ok"]
        return resolve_targets(ohlc, entry_idx, entry_close, state.rd, t["fav"], t["adv"],
                               n_event, atr_entry, pop, _rng(cell_index, pb + v.idx))

    arm_cfg = {"stat": (stat["retained_p75"], PB_STAT, PB_PC_STAT),
               "ha": (ha_same, PB_HA, PB_PC_HA),
               "statmad": (stat["retained_mad"], PB_STATMAD, PB_PC_STATMAD)}
    out: dict[str, dict[str, Any]] = {}
    for arm, (mask, pb, pc_pb) in arm_cfg.items():
        res = {v.vid: resolve(mask, v, pb) for v in BINDING_VARIANTS}
        out[arm] = {"variants": res,
                    "contrast": paired_contrasts_vs_bench(entry_idx, res, cell_index, pc_pb)}
    return out


def _resolve_baselines(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, entry_epoch: np.ndarray,
    entry_close: np.ndarray, atr: np.ndarray, atr_entry: np.ndarray,
    mv: dict[str, np.ndarray], stat_retained: np.ndarray,
    stat_variants: dict[str, ArmResult], cell_index: int,
) -> dict[str, dict[str, Any]]:
    """P13 matched-random + MA-seg baselines per binding variant (stat arm)."""
    state_all = live_in_progress_state(ohlc["epoch"], ohlc["close"], mv["confirm_epoch"],
                                       mv["end_price"], mv["end_epoch"], mv["direction"])
    n_event_all, warmup_all = adaptive_time_caps_by_epoch(ohlc["epoch"], mv["confirm_epoch"],
                                                          mv["confirm_idx"])
    seg = ma_segment_moves(ohlc)
    signal_idx = entry_idx[stat_retained]
    out: dict[str, dict[str, Any]] = {}
    for v in BINDING_VARIANTS:
        sig = stat_variants[v.vid]
        rand = matched_random_variant(ohlc, state_all, mv, n_event_all, warmup_all, atr,
                                      signal_idx, v, sig.m, cell_index)
        ma = ma_seg_variant(ohlc, entry_idx, entry_epoch, entry_close, atr_entry, seg, v,
                            cell_index)
        out[v.vid] = {"matched_random": rand, "ma_seg": ma,
                      "contrast_random": contrast_ci(sig.dist, rand.dist),
                      "contrast_ma": contrast_ci(sig.dist, ma.dist)}
    return out


# --------------------------------------------------------------------------- #
# Per-cell record flattening + viability / win classification
# --------------------------------------------------------------------------- #
def cell_variant_records(instrument: str, cell: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten one cell into per-variant binding-arm (stat) records."""
    domain = cell["domain"]
    cell_fields = {"instrument": instrument, "domain": domain, "member": True,
                   "excluded": False, "n_bars": cell["n_bars"], "n_moves": cell["n_moves"],
                   "n_harami": cell["n_harami"]}
    if cell.get("empty", False):
        return [{**cell_fields, "variant": v.vid, **_empty_variant_fields()}
                for v in BINDING_VARIANTS]
    stat = cell["arms"]["stat"]
    bench_m = stat["variants"]["BENCH"].m
    cell_fields.update({"n_buildable": cell["buildable"], "n_conditioned": cell["conditioned"]})
    records = []
    for v in BINDING_VARIANTS:
        rec = {**cell_fields, "variant": v.vid}
        rec.update(_variant_record(cell, v, bench_m))
        records.append(rec)
    return records


def _variant_record(cell: dict[str, Any], v: VariantSpec, bench_m: int) -> dict[str, Any]:
    """Per (cell, binding variant) metric + baseline + contrast + classification."""
    sig = cell["arms"]["stat"]["variants"][v.vid]
    contrast = cell["arms"]["stat"]["contrast"][v.vid]
    bl = cell["baselines"][v.vid]
    targets = cell["targets"][v.vid]
    cond = cell["buildable_mask"] & cell["stat_mask"]
    rec: dict[str, Any] = {}
    rec.update(_arm_fields(sig, ""))
    rec["excl_validity"] = int((cond & targets["reason_validity"]).sum())
    rec["excl_warmup"] = int((cond & targets["reason_warmup"]).sum())
    rec["excl_degenerate"] = int((cond & targets["reason_degenerate"]).sum())
    rec["retained_fraction"] = (sig.m / cell["conditioned"]) if cell["conditioned"] else None
    rec["contrast_bench_low"], rec["contrast_bench_lo2s"], rec["contrast_bench_hi2s"], \
        rec["contrast_bench_block"], rec["contrast_bench_n"] = contrast
    rec.update(_baseline_fields(bl["matched_random"], "rand"))
    rec.update(_baseline_fields(bl["ma_seg"], "maseg"))
    rec["contrast_random_low"] = bl["contrast_random"][0]
    rec["contrast_ma_low"] = bl["contrast_ma"][0]
    _classify_variant(rec, sig, v, bench_m)
    return rec


def _classify_variant(rec: dict[str, Any], sig: ArmResult, v: VariantSpec, bench_m: int) -> None:
    """Per (cell, variant) powered/viable/beats_bench/win + status code."""
    viable = (sig.m >= POWER_FLOOR and sig.ci_low_1s is not None
              and np.isfinite(sig.ci_low_1s) and sig.ci_low_1s > 0.0)
    cl = rec["contrast_bench_low"]
    beats = (v.vid != "BENCH" and sig.m >= POWER_FLOOR and bench_m >= POWER_FLOOR
             and rec["contrast_bench_n"] >= POWER_FLOOR
             and cl is not None and np.isfinite(cl) and cl > 0.0)
    win = viable and beats
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


def _arm_fields(a: ArmResult, prefix: str) -> dict[str, Any]:
    """Flatten an ArmResult's scalar metrics (no per-event arrays)."""
    p = prefix
    return {
        f"{p}m": a.m, f"{p}median": a.median, f"{p}mean": a.mean,
        f"{p}ci_low_1s": a.ci_low_1s, f"{p}ci_lo_2s": a.ci_lo_2s, f"{p}ci_hi_2s": a.ci_hi_2s,
        f"{p}fav": a.fav, f"{p}adv": a.adv, f"{p}timecap": a.timecap,
        f"{p}data_censored": a.data_censored, f"{p}r_firsthit": a.r_firsthit,
        f"{p}win_rate": a.win_rate, f"{p}timecap_frac": a.timecap_frac,
        f"{p}population": a.population, f"{p}block_len": a.block_len,
    }


def _baseline_fields(a: ArmResult, prefix: str) -> dict[str, Any]:
    """Compact baseline columns (m / median / one-sided CI_low)."""
    return {f"{prefix}_m": a.m, f"{prefix}_median": a.median, f"{prefix}_ci_low_1s": a.ci_low_1s}


def _empty_variant_fields() -> dict[str, Any]:
    rec = {"n_buildable": 0, "n_conditioned": 0, "retained_fraction": None,
           "excl_validity": 0, "excl_warmup": 0, "excl_degenerate": 0,
           "contrast_bench_low": None, "contrast_bench_lo2s": None,
           "contrast_bench_hi2s": None, "contrast_bench_block": 1, "contrast_bench_n": 0,
           "contrast_random_low": None, "contrast_ma_low": None,
           "powered": False, "viable": False, "beats_bench": False, "win": False,
           "viable_status": "NOT_VIABLE_BY_POWER",
           "status_code": VSTATUS_CODES["NOT_VIABLE_BY_POWER"]}
    rec.update(_arm_fields(_empty_arm(), ""))
    rec.update(_baseline_fields(_empty_arm(), "rand"))
    rec.update(_baseline_fields(_empty_arm(), "maseg"))
    return rec


def excluded_records(instrument: str, domain: str) -> list[dict[str, Any]]:
    """COVERAGE_EXCLUDED cell records (one per binding variant)."""
    out = []
    for v in BINDING_VARIANTS:
        rec = {"instrument": instrument, "domain": domain, "member": False, "excluded": True,
               "variant": v.vid, "n_bars": None, "n_moves": None, "n_harami": None}
        rec.update(_empty_variant_fields())
        rec["viable_status"], rec["status_code"] = "EXCLUDED", VSTATUS_CODES["EXCLUDED"]
        out.append(rec)
    return out


def secondary_records(instrument: str, cell: dict[str, Any]) -> list[dict[str, Any]]:
    """Disclosed-arm rows: /STRONG-HA and STAT-MAD, per binding variant."""
    if cell.get("empty", False):
        return []
    rows = []
    for arm in ("ha", "statmad"):
        for v in BINDING_VARIANTS:
            rows.append(_secondary_row(instrument, cell, arm, v.vid))
    return rows


def _secondary_row(instrument: str, cell: dict[str, Any], arm: str, vid: str) -> dict[str, Any]:
    a = cell["arms"][arm]["variants"][vid]
    c = cell["arms"][arm]["contrast"][vid]
    return {"instrument": instrument, "domain": cell["domain"], "arm": arm, "variant": vid,
            "m": a.m, "median": a.median, "ci_low_1s": a.ci_low_1s,
            "ci_lo_2s": a.ci_lo_2s, "ci_hi_2s": a.ci_hi_2s, "r_firsthit": a.r_firsthit,
            "contrast_bench_low": c[0], "contrast_bench_n": c[4]}


# --------------------------------------------------------------------------- #
# Composition + mechanical EVIDENCE_* classification (per variant)
# --------------------------------------------------------------------------- #
def composition_readout(records: list[dict[str, Any]], defect: dict[str, Any]) -> dict[str, Any]:
    """P11 composition per binding variant + the mechanical EVIDENCE_* verdict."""
    members = [r for r in records if r["member"]]
    by_variant = {v.vid: [r for r in members if r["variant"] == v.vid] for v in BINDING_VARIANTS}
    per_variant = {vid: _variant_composition(rows) for vid, rows in by_variant.items()}
    passers = [vid for vid in (v.vid for v in ALT_VARIANTS) if per_variant[vid]["win"]["passes"]]
    verdict = _evidence_label(defect, per_variant, passers)
    fragile = [vid for vid in passers if per_variant[vid]["win"]["fragile"]]
    return {
        "verdict": verdict, "n_pass": len(passers), "passing_variants": passers,
        "fragile_passes": fragile, "per_variant": per_variant, "defect": defect,
        "rule": ("per variant: VIABLE iff median CI_low(1s)>0 AND m>=30; BEATS_BENCH iff "
                 "paired CI_low(delta)>0 AND m>=30 AND bench_m>=30 AND |S|>=30; WIN=viable&beats; "
                 "P11 iff >=5 cells over >=3 instruments. EVIDENCE_FOR iff any alternative "
                 "variant's WIN composition clears P11; no registration (single 014-B G2)."),
        "multiplicity": ("uncorrected per-variant one-sided 95% CIs; family-wise correction across "
                         "the full 014-B surface is deferred to the single G2 desk adjudication."),
    }


def _variant_composition(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Powered / viable / win P11 tallies for one variant."""
    powered = [r for r in rows if r["powered"]]
    viable = [r for r in rows if r["viable"]]
    win = [r for r in rows if r["win"]]
    return {"powered": _tally(powered), "viable": _tally(viable, with_cells=True),
            "win": _win_tally(win)}


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


def _evidence_label(
    defect: dict[str, Any], per_variant: dict[str, Any], passers: list[str],
) -> str:
    """Mechanical EVIDENCE_* per the analysis-plan Interpretation Guide."""
    if defect["is_defect"]:
        return "SUBSTRATE_METHOD_DEFECT"
    if passers:
        return "EVIDENCE_FOR"
    bench_pow = per_variant["BENCH"]["powered"]["composition_met"]
    alt_pow = any(per_variant[v.vid]["powered"]["composition_met"] for v in ALT_VARIANTS)
    if bench_pow and alt_pow:
        return "EVIDENCE_AGAINST"
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
    for vid in (v.vid for v in BINDING_VARIANTS):
        sa = a["arms"]["stat"]["variants"][vid]
        sb = b["arms"]["stat"]["variants"][vid]
        if not (np.array_equal(sa.r_e, sb.r_e)
                and (sa.median, sa.ci_low_1s) == (sb.median, sb.ci_low_1s)):
            return False
        for bl in ("matched_random", "ma_seg"):    # all variants, both baselines
            if not np.array_equal(a["baselines"][vid][bl].r_e,
                                  b["baselines"][vid][bl].r_e):
                return False
    return True


def reconciliation_anchor(cell: dict[str, Any]) -> dict[str, Any]:
    """Independently re-check the BENCH stat arm's class partition + return signs."""
    sig = cell["arms"]["stat"]["variants"]["BENCH"]
    if sig.m == 0:
        return {"checked": False, "reason": "no qualifying BENCH events"}
    n_pos = int((sig.r_e > 0.0).sum())
    n_neg = int((sig.r_e < 0.0).sum())
    ok = (n_pos >= sig.fav and n_neg >= sig.adv
          and (sig.fav + sig.adv + sig.timecap) == sig.m and bool(np.isfinite(sig.r_e[0])))
    return {"checked": True, "fav": sig.fav, "adv": sig.adv, "timecap": sig.timecap,
            "m": sig.m, "positive_returns": n_pos, "negative_returns": n_neg,
            "consistent": bool(ok)}


def exp053_reconciliation(
    instrument: str, cell: dict[str, Any], exp053: dict[tuple[str, str], tuple[int, float | None]],
) -> dict[str, Any]:
    """Cross-check the BENCH stat arm against EXP-053's recorded benchmark (same geometry)."""
    key = (instrument, cell["domain"])
    if not exp053 or key not in exp053 or cell.get("empty"):
        return {"checked": False, "cell": f"{instrument}-{cell.get('domain')}"}
    sig = cell["arms"]["stat"]["variants"]["BENCH"]
    exp_m, exp_med = exp053[key]
    m_match = sig.m == exp_m
    med_match = (sig.median is None and exp_med is None) or (
        sig.median is not None and exp_med is not None and abs(sig.median - exp_med) <= 1e-9)
    return {"checked": True, "cell": f"{instrument}-{cell['domain']}", "bench_m": sig.m,
            "exp053_m": exp_m, "bench_median": sig.median, "exp053_median": exp_med,
            "m_match": bool(m_match), "median_match": bool(med_match),
            "consistent": bool(m_match and med_match)}


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


def plot_variant_forest(records: list[dict[str, Any]], save_path: Path) -> None:
    """Per-binding-variant per-cell median expectancy with one-sided CI_low whisker."""
    fig, axes = plt.subplots(2, 2, figsize=(13, 11), sharex=True)
    for ax, v in zip(axes.ravel(), BINDING_VARIANTS):
        rows = sorted([r for r in records if r["variant"] == v.vid and r["member"]
                       and r["median"] is not None], key=lambda r: r["median"])
        if not rows:
            ax.text(0.5, 0.5, "no powered cells", ha="center", va="center")
            ax.set_title(v.vid, fontsize=9)
            continue
        med = np.array([r["median"] for r in rows])
        low = np.array([r["ci_low_1s"] if r["ci_low_1s"] is not None else np.nan for r in rows])
        y = np.arange(len(rows))
        colours = ["#1a9850" if r["win"] else ("#a6d96a" if r["viable"] else "#999999")
                   for r in rows]
        ax.scatter(med, y, color=colours, s=14, zorder=3)
        ax.hlines(y, np.minimum(low, med), med, color=colours, alpha=0.6, zorder=2)
        ax.axvline(0.0, color="k", lw=0.7, ls="--")
        ax.set_yticks(y, [_cell_label(r) for r in rows], fontsize=4)
        ax.set_title(v.vid, fontsize=9)
    fig.suptitle(f"{EXPERIMENT_ID}: per-cell median expectancy by variant (binding /STRONG-STAT)")
    fig.supxlabel("median gross expectancy (ATR units)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_contrast_heatmap(records: list[dict[str, Any]], save_path: Path) -> None:
    """Variant (rows) x cell (cols) paired contrast_bench_low heatmap (alternatives)."""
    cells = _ordered_cells(records)
    matrix = np.full((len(ALT_VARIANTS), len(cells)), np.nan)
    win = np.zeros_like(matrix, dtype=bool)
    lookup = {(r["variant"], _cell_label(r)): r for r in records if r["member"]}
    for i, v in enumerate(ALT_VARIANTS):
        for j, c in enumerate(cells):
            r = lookup.get((v.vid, c))
            if r and r["contrast_bench_low"] is not None and np.isfinite(r["contrast_bench_low"]):
                matrix[i, j] = r["contrast_bench_low"]
                win[i, j] = r["win"]
    fig, ax = plt.subplots(figsize=(max(8, 0.16 * len(cells)), 4))
    vmax = np.nanmax(np.abs(matrix)) if np.isfinite(matrix).any() else 1.0
    im = ax.imshow(matrix, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")
    for (i, j) in zip(*np.where(win)):
        ax.text(j, i, "*", ha="center", va="center", fontsize=7, color="k")
    ax.set_yticks(range(len(ALT_VARIANTS)), [v.vid for v in ALT_VARIANTS], fontsize=7)
    ax.set_xticks(range(len(cells)), cells, rotation=90, fontsize=3)
    ax.set_title(f"{EXPERIMENT_ID}: paired variant-benchmark contrast CI_low (* = WIN)")
    fig.colorbar(im, ax=ax, label="CI_low(delta) (ATR units)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_return_distributions(pooled: dict[str, list[float]], save_path: Path) -> None:
    """Pooled per-event ATR-normalised return distribution by binding variant."""
    variants = [v.vid for v in BINDING_VARIANTS if pooled.get(v.vid)]
    if not variants:
        _placeholder(save_path, "no viable-cell events to pool")
        return
    data = [np.asarray(pooled[v]) for v in variants]
    fig, ax = plt.subplots(figsize=(9, 5))
    parts = ax.violinplot(data, showmedians=True, showextrema=False)
    for pc in parts["bodies"]:
        pc.set_alpha(0.5)
    ax.axhline(0.0, color="k", lw=0.8, ls="--")
    ax.set_xticks(range(1, len(variants) + 1), variants, rotation=20, fontsize=8)
    ax.set_ylabel("per-event gross return (ATR units)")
    ax.set_title(f"{EXPERIMENT_ID}: per-event return by variant (binding-viable cells pooled)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_r_and_composition(records: list[dict[str, Any]], save_path: Path) -> None:
    """First-hit r vs 0.50 per variant (top) + variant x cell win composition grid (bottom)."""
    cells = _ordered_cells(records, include_excluded=True)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(max(9, 0.16 * len(cells)), 9))
    # (a) first-hit r distribution per variant (the off-0.50 narrative; disclosed)
    r_by_variant = []
    for v in BINDING_VARIANTS:
        vals = [r["r_firsthit"] for r in records if r["variant"] == v.vid and r["member"]
                and r["r_firsthit"] is not None and np.isfinite(r["r_firsthit"])]
        r_by_variant.append(vals)
    positions = np.arange(len(BINDING_VARIANTS))
    for i, vals in enumerate(r_by_variant):
        if vals:
            ax1.scatter(np.full(len(vals), i), vals, s=12, alpha=0.5, color="#4575b4")
            ax1.scatter([i], [np.median(vals)], s=60, marker="_", color="k", zorder=3)
    ax1.axhline(0.50, color="r", lw=0.9, ls="--", label="r=0.50 (EXP-049/053 null)")
    ax1.set_xticks(positions, [v.vid for v in BINDING_VARIANTS], fontsize=8)
    ax1.set_ylabel("first-hit r = FAV/(FAV+ADV)")
    ax1.set_title("first-hit r by variant (disclosed; off-0.50 narrative)")
    ax1.legend(fontsize=7)
    # (b) win-composition status grid
    matrix = np.full((len(BINDING_VARIANTS), len(cells)), VSTATUS_CODES["EXCLUDED"])
    lookup = {(r["variant"], _cell_label(r)): r for r in records}
    for i, v in enumerate(BINDING_VARIANTS):
        for j, c in enumerate(cells):
            r = lookup.get((v.vid, c))
            if r is not None:
                matrix[i, j] = r["status_code"]
    cmap = ListedColormap(VSTATUS_COLORS)
    norm = BoundaryNorm(np.arange(-0.5, len(VSTATUS_COLORS) + 0.5), cmap.N)
    ax2.imshow(matrix, cmap=cmap, norm=norm, aspect="auto")
    ax2.set_yticks(range(len(BINDING_VARIANTS)), [v.vid for v in BINDING_VARIANTS], fontsize=7)
    ax2.set_xticks(range(len(cells)), cells, rotation=90, fontsize=3)
    ax2.set_title("wins-over-benchmark composition (P11: 5 cells / 3 instr)")
    handles = [plt.Rectangle((0, 0), 1, 1, color=VSTATUS_COLORS[c]) for c in VSTATUS_CODES.values()]
    ax2.legend(handles, list(VSTATUS_CODES.keys()), bbox_to_anchor=(1.01, 1),
               loc="upper left", fontsize=7)
    fig.suptitle(f"{EXPERIMENT_ID}: first-hit r vs benchmark + wins composition")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_exclusion_fractions(records: list[dict[str, Any]], save_path: Path) -> None:
    """Per-variant pooled exclusion breakdown + median qualifying count (power floor)."""
    variants = [v.vid for v in BINDING_VARIANTS]
    validity = np.zeros(len(variants))
    warmup = np.zeros(len(variants))
    degenerate = np.zeros(len(variants))
    qualifying = np.zeros(len(variants))
    med_m = []
    for i, vid in enumerate(variants):
        rows = [r for r in records if r["variant"] == vid and r["member"] and not r.get("empty")]
        validity[i] = sum(r.get("excl_validity", 0) or 0 for r in rows)
        warmup[i] = sum(r.get("excl_warmup", 0) or 0 for r in rows)
        degenerate[i] = sum(r.get("excl_degenerate", 0) or 0 for r in rows)
        qualifying[i] = sum(r["m"] for r in rows)
        ms = [r["m"] for r in rows if r["m"] > 0]
        med_m.append(float(np.median(ms)) if ms else 0.0)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    x = np.arange(len(variants))
    ax1.bar(x, qualifying, label="qualifying", color="#1a9850")
    ax1.bar(x, warmup, bottom=qualifying, label="excl: warmup/extreme", color="#fdae61")
    ax1.bar(x, degenerate, bottom=qualifying + warmup, label="excl: degenerate", color="#f46d43")
    ax1.bar(x, validity, bottom=qualifying + warmup + degenerate, label="excl: validity",
            color="#cccccc")
    ax1.set_xticks(x, variants, rotation=20, fontsize=7)
    ax1.set_ylabel("pooled event count (conditioned population)")
    ax1.set_title("event accounting by variant")
    ax1.legend(fontsize=7)
    ax2.bar(x, med_m, color="#4575b4")
    ax2.axhline(POWER_FLOOR, color="k", lw=0.9, ls="--", label=f"power floor={POWER_FLOOR}")
    ax2.set_xticks(x, variants, rotation=20, fontsize=7)
    ax2.set_ylabel("median per-cell qualifying events")
    ax2.set_title("per-cell power by variant")
    ax2.legend(fontsize=7)
    fig.suptitle(f"{EXPERIMENT_ID}: qualifying / exclusion accounting by adverse-target variant")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def make_plots(records: list[dict[str, Any]], pooled: dict[str, list[float]]) -> None:
    """Render the five bounded plots from collected summaries + pooled events."""
    plot_variant_forest(records, PLOTS_DIR / "per_variant_median_forest.png")
    plot_contrast_heatmap(records, PLOTS_DIR / "variant_benchmark_contrast_heatmap.png")
    plot_return_distributions(pooled, PLOTS_DIR / "return_distribution_by_variant.png")
    plot_r_and_composition(records, PLOTS_DIR / "r_and_wins_composition.png")
    plot_exclusion_fractions(records, PLOTS_DIR / "qualifying_exclusion_accounting.png")


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _cell_index_map() -> dict[tuple[str, str], int]:
    return {(inst, dom): i for i, (inst, dom) in enumerate(
        (inst, dom) for inst in INSTRUMENTS for dom in DOMAINS)}


def _collect_pooled(cell: dict[str, Any], cell_records: list[dict[str, Any]],
                    pooled: dict[str, list[float]]) -> None:
    """Pool per-event returns from binding-viable cells (per variant) for the violin."""
    if cell.get("empty"):
        return
    viable = {r["variant"] for r in cell_records if r["viable"]}
    for v in BINDING_VARIANTS:
        if v.vid in viable:
            pooled[v.vid].extend(cell["arms"]["stat"]["variants"][v.vid].r_e.tolist())


def run() -> dict[str, Any]:
    """Run all member cells and write artifacts. Returns the run summary."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    cell_index = _cell_index_map()
    exp053 = load_exp053_benchmark()
    records: list[dict[str, Any]] = []
    secondaries: list[dict[str, Any]] = []
    recon_rows: list[dict[str, Any]] = []
    pooled: dict[str, list[float]] = {v.vid: [] for v in BINDING_VARIANTS}
    instrument_meta: dict[str, Any] = {}
    defect = {"is_defect": False, "non_deterministic": [], "reconciliation": [],
              "exp053_mismatch": [], "causality_violations": [], "determinism_checked": [],
              "invariant_violations": [], "none_adv_violations": [],
              "exp053_available": bool(exp053), "exp053_checked_cells": 0}
    replayed: set[str] = set()

    for instrument in tqdm(INSTRUMENTS, desc="instruments"):
        members = [d for d in DOMAINS if (instrument, d) not in EXCLUDED_CELLS]
        if not members:
            for domain in DOMAINS:
                records.extend(excluded_records(instrument, domain))
            continue
        train_1m, meta = load_train_1m(instrument)
        instrument_meta[instrument] = meta
        for domain in DOMAINS:
            if (instrument, domain) in EXCLUDED_CELLS:
                records.extend(excluded_records(instrument, domain))
                continue
            ci = cell_index[(instrument, domain)]
            cell = compute_cell(train_1m, domain, meta["train_end_epoch_s"], ci)
            cvr = cell_variant_records(instrument, cell)
            records.extend(cvr)
            secondaries.extend(secondary_records(instrument, cell))
            _collect_pooled(cell, cvr, pooled)
            recon_rows.append(exp053_reconciliation(instrument, cell, exp053))
            _record_cell_defects(cell, instrument, domain, defect)
            _maybe_guard(train_1m, domain, meta, ci, cell, defect, instrument, replayed)
            del cell
        del train_1m

    _finalize_defects(defect, recon_rows)
    readout = composition_readout(records, defect)
    write_outputs(records, secondaries, recon_rows, readout, pooled, instrument_meta, defect)
    make_plots(records, pooled)
    return _summarize(records, readout)


def _record_cell_defects(cell: dict[str, Any], instrument: str, domain: str,
                         defect: dict[str, Any]) -> None:
    """Accumulate per-cell causality / invariant / ADV-NONE violations."""
    if cell.get("empty"):
        return
    label = f"{instrument}-{domain}"
    if not cell.get("causality_ok", True):
        defect["causality_violations"].append(label)
    inv = cell.get("invariants", {})
    if not (inv.get("raw_le_rr1", True) and inv.get("adv_ordering", True)):
        defect["invariant_violations"].append(label)
    if cell.get("none_adv", 0) > 0:
        defect["none_adv_violations"].append(label)


def _finalize_defects(defect: dict[str, Any], recon_rows: list[dict[str, Any]]) -> None:
    """Aggregate defect gates (analysis-plan Step 9) into the binding is_defect flag."""
    # EXP-053 BENCH reconciliation: any mismatch is a SUBSTRATE/METHOD_DEFECT.
    defect["exp053_mismatch"] = [r["cell"] for r in recon_rows
                                 if r.get("checked") and not r["consistent"]]
    if defect["exp053_mismatch"]:
        defect["is_defect"] = True
    # Binding EXP-053 anchor: expected but unavailable, or zero cells checked, is a defect.
    defect["exp053_checked_cells"] = sum(1 for r in recon_rows if r.get("checked"))
    if not defect["exp053_available"] or defect["exp053_checked_cells"] == 0:
        defect["is_defect"] = True
    # Causality violations on >=3 instruments -> defect (Step 9).
    causal_instr = {c.split("-")[0] for c in defect["causality_violations"]}
    if len(causal_instr) >= P11_MIN_INSTR:
        defect["is_defect"] = True
    # Adverse invariants are exact structural checks: any violation -> defect (Step 9).
    if defect["invariant_violations"] or defect["none_adv_violations"]:
        defect["is_defect"] = True


def _maybe_guard(
    train_1m: pl.DataFrame, domain: str, meta: dict[str, Any], cell_index: int,
    cell: dict[str, Any], defect: dict[str, Any], instrument: str, replayed: set[str],
) -> None:
    """Determinism replay + BENCH reconciliation on the first usable cell per instrument."""
    if instrument in replayed or cell.get("empty"):
        return
    if cell["arms"]["stat"]["variants"]["BENCH"].m == 0:
        return
    ok = determinism_replay(train_1m, domain, meta["train_end_epoch_s"], cell_index)
    defect["determinism_checked"].append(f"{instrument}-{domain}#{cell_index}")
    recon = reconciliation_anchor(cell)
    recon["instrument"], recon["cell"] = instrument, f"{instrument}-{domain}"
    defect["reconciliation"].append(recon)
    if not ok:
        defect["non_deterministic"].append(f"{instrument}-{domain}#{cell_index}")
    if not ok or (recon.get("checked") and not recon.get("consistent")):
        defect["is_defect"] = True
    replayed.add(instrument)


def write_outputs(
    records: list[dict[str, Any]], secondaries: list[dict[str, Any]],
    recon_rows: list[dict[str, Any]], readout: dict[str, Any],
    pooled: dict[str, list[float]], instrument_meta: dict[str, Any],
    defect: dict[str, Any],
) -> None:
    """Persist per-cell parquet, the variant maps, reconciliation, and the JSONs."""
    pl.DataFrame(records, strict=False).write_parquet(RESULTS_DIR / "per_cell_expectancy.parquet")
    pl.DataFrame(records, strict=False).write_csv(RESULTS_DIR / "adverse_target_map.csv")
    sec_df = (pl.DataFrame(secondaries, strict=False) if secondaries
              else pl.DataFrame({"arm": [], "variant": []}))
    sec_df.write_csv(RESULTS_DIR / "secondary_map.csv")
    recon_clean = [r for r in recon_rows if r.get("checked")]
    (pl.DataFrame(recon_clean, strict=False) if recon_clean
     else pl.DataFrame({"cell": []})).write_csv(RESULTS_DIR / "population_reconciliation.csv")

    with open(RESULTS_DIR / "composition_readout.json", "w") as fh:
        json.dump(readout, fh, indent=2, default=str)
    pooled_rows = [{"variant": v, "r_e": x} for v, xs in pooled.items() for x in xs]
    (pl.DataFrame(pooled_rows) if pooled_rows
     else pl.DataFrame({"variant": [], "r_e": []},
                       schema={"variant": pl.Utf8, "r_e": pl.Float64})
     ).write_parquet(RESULTS_DIR / "per_event_returns.parquet")
    _write_metadata(instrument_meta, defect, recon_clean)


def _write_metadata(
    instrument_meta: dict[str, Any], defect: dict[str, Any], recon_clean: list[dict[str, Any]],
) -> None:
    meta = {
        "experiment_id": EXPERIMENT_ID,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "014-B", "hypothesis": "HYP-010", "family": "CF-HA-HARAMI-001",
        "stratum": "TRAIN-only (first 49%); nested TEST + final-30% holdout sealed",
        "entry_anchor": "harami confirmation-bar real close (live, pre-ZigZag-confirm)",
        "binding_arm": "/STRONG-STAT p75; /STRONG-HA + STAT-MAD disclosed",
        "binding_endpoint": "median per-event gross ATR-normalised return (P14, P15 fills)",
        "geometry": "OAT on adverse target; favourable 50% + adaptive cap + P15 held at benchmark",
        "variants_binding": [v.vid for v in BINDING_VARIANTS],
        "params": {
            "atr_period": ATR_PERIOD, "atr_mult": ATR_MULT, "favourable_fraction_bench": 0.50,
            "adverse_bench": "1:1", "adv_extreme_buffer_frac": ADV_BUFFER_FRAC,
            "adv_floor_frac": ADV_FLOOR_FRAC, "adv_none_sentinel": "-inf (rd=+1) / +inf (rd=-1)",
            "stat_window": 20, "stat_min_window": 5, "stat_q": 0.75, "ha_run_len": 3,
            "timecap": "max(6, round(1.5*median(trailing-20 durations)))",
            "ma_segmentation": [MA_FAST, MA_SLOW], "power_floor": POWER_FLOOR,
            "n_boot": 10000, "boot_batch": 2000, "base_seed": BASE_SEED,
            "p11": [P11_MIN_CELLS, P11_MIN_INSTR],
        },
        "baselines": ["matched-count random (in-progress rd, non-signal pool, per variant)",
                      "MA(20,50)-crossover segmentation per variant (identical pipeline)"],
        "contrasts": {"variant_vs_benchmark": "paired moving-block bootstrap (binding)",
                      "variant_vs_baseline": "independent bootstrap contrast (disclosed)"},
        "determinism_ok": not defect["non_deterministic"],
        "determinism_checked": defect["determinism_checked"],
        "determinism_gate": ("byte-identical re-run of the first usable cell per "
                             "instrument across all binding variants' stat arms and "
                             "both baselines (the agreed determinism sample)."),
        "causality_ok": not defect["causality_violations"],
        "causality_violations": defect["causality_violations"],
        "invariant_violations": defect["invariant_violations"],
        "none_adv_violations": defect["none_adv_violations"],
        "invariant_gates": ("raw adv_dist <= rr1 adv_dist (event-wise); ADV-NONE yields 0 ADV "
                            "outcomes across all arms+baselines; raw adverse-side ordering "
                            "rd*(C-adv)>0; BENCH reproduces EXP-053 per-cell median + count."),
        "reconciliation": defect["reconciliation"],
        "exp053_reconciliation": recon_clean,
        "exp053_mismatch": defect["exp053_mismatch"],
        "exp053_available": defect["exp053_available"],
        "exp053_checked_cells": defect["exp053_checked_cells"],
        "paired_contrast_conditioning": ("beats_bench is a paired contrast on the common "
                                         "qualifying subset S (res.qual & bench.qual); for "
                                         "ADV-NONE an event stopped under BENCH may run on to "
                                         "FAV/TIMECAP, so both still qualify and enter S with "
                                         "different exit prices (intended paired comparison)."),
        "is_defect": defect["is_defect"],
        "de30_disclosure": DE30_DISCLOSURE,
        "fill_approximation": ("P15 path is a documented approximation of unobserved intrabar "
                               "motion; 1-minute base bars are not replayed (EXP-054 bounds it)."),
        "holdout_fence": ("Only Parquet metadata + first train_rows file-order rows read per "
                          "instrument; full file never sorted/collected; every domain bar fenced "
                          "to CloseTime <= train_end_ts; forward scans clipped to the data edge; "
                          "TEST and final-30% holdout never read."),
        "registry": ("CF-HA-HARAMI-001/HYP-010 (EXP-057); exercises /ADV-EXTREME + /ADV-NONE; "
                     "0 candidate slots, 0 TEST reads; characterization readout feeds the "
                     "single 014-B G2."),
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
            "passing_variants": readout["passing_variants"],
            "fragile_passes": readout["fragile_passes"], "status_counts": status_counts,
            "defect": readout["defect"]}


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    summary = run()
    LOGGER.info("\n=== %s complete ===", EXPERIMENT_ID)
    LOGGER.info("verdict: %s", summary["verdict"])
    LOGGER.info("passing variants (%s): %s", summary["n_pass"], summary["passing_variants"])
    if summary["fragile_passes"]:
        LOGGER.info("fragile (bare-quorum) passes: %s", summary["fragile_passes"])
    LOGGER.info("status counts (per cell-variant): %s", json.dumps(summary["status_counts"]))
    if summary["defect"]["is_defect"]:
        LOGGER.info("DEFECT: %s", json.dumps(summary["defect"], default=str))
    LOGGER.info("artifacts -> %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
