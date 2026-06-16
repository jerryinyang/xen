"""EXP-053 — Conditioned-Signal Efficacy (HA Harami at Strong-Move Exhaustion).

``CF-HA-HARAMI-001`` / HYP-006 (Phase 014-B lead). TRAIN-only, gross; 0 candidate
slots, 0 TEST reads. For each EXP-049 member cell (instrument x domain) this
script, on the TRAIN analysis stratum only:

1. slices the first-49% (TRAIN) 1-minute rows by file-order prefix (TEST and the
   final-30% global holdout are never read), aggregates the domain (5m strict;
   15m/30m/1h/2h/4h at min_coverage=0.90) and fences to the TRAIN edge;
2. runs the frozen Wilder-ATR ZigZag substrate, detects HA haramis on HA candles,
   maps each harami to its real domain bar by exact CloseTime match, and resolves
   the **live in-progress move** at each harami (current-price magnitude-so-far
   ``M_sofar = |C - StartPrice_inprogress|``);
3. conditions on ``/STRONG-STAT`` (binding p75; disclosed median+MAD) and
   ``/STRONG-HA`` (disclosed same-dir run; any-dir sensitivity), entered at the
   harami real close and faded against the in-progress move under the single
   benchmark geometry (``fav = C + rd*0.5*M_sofar``; 1:1 adverse; adaptive time
   cap) with **P15 path-ordered intrabar fills**;
4. computes per-cell **median** ATR-normalised gross expectancy with the
   regime-clustered moving-block bootstrap CI, two P13 baselines (matched-count
   random, MA(20,50)-segmentation) through the identical pipeline, and the
   signal-baseline contrast CI; composes by P11 (>=5 cells over >=3 instruments)
   and emits a mechanical EVIDENCE_* readout;
5. runs a determinism replay (one cell per instrument, byte-identical) and a
   reconciliation anchor (independent FAV/ADV + r_e recompute) per replayed cell
   as SUBSTRATE/METHOD_DEFECT guards.

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
import seaborn as sns  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402
from tqdm.auto import tqdm  # noqa: E402

# --------------------------------------------------------------------------- #
# Path setup
# --------------------------------------------------------------------------- #
CODE_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = CODE_DIR.parent
PROJECT_ROOT = EXPERIMENT_DIR.parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "timebars"
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"

from xen.bar_aggregator import aggregate_ohlc  # noqa: E402
from xen.capture_barriers import (  # noqa: E402
    CLASS_ADV,
    CLASS_DATA_CENSORED,
    CLASS_FAV,
    CLASS_TIMECAP,
)
from xen.expectancy import (  # noqa: E402
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
from xen.strong_move import (  # noqa: E402
    annotate_ha_impulse,
    find_impulse_runs,
)
from xen.zigzag import generate_zigzag, wilder_atr  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (Phase 014-B D0 frozen; no tuning)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-053"
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
# RNG purpose offsets (distinct deterministic streams per cell).
RNG_STAT, RNG_HA, RNG_STATMAD, RNG_HAANY = 1, 2, 3, 4
RNG_RAND_BOOT, RNG_MASEG_BOOT, RNG_RAND_DRAW = 5, 6, 7
PLOT_ARMS = ("signal_stat", "signal_ha", "matched_random", "ma_seg")
# Viability status -> integer code / colour (composition heatmap).
VSTATUS_CODES: dict[str, int] = {
    "VIABLE": 0, "CI_SPANS_0": 1, "NOT_VIABLE_BY_POWER": 2, "EXCLUDED": 3,
}
VSTATUS_COLORS: list[str] = ["#1a9850", "#f46d43", "#cccccc", "#7b3294"]
DE30_DISCLOSURE = (
    "DE30 truncated history: broker m1 history ends 2026-01-16; counts derive "
    "from its own realized timeline and are not span-comparable (VAL-003)."
)
LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ArmResult:
    """One arm's per-cell resolved population summary + qualifying returns."""

    m: int                         # qualifying events (P14 denominator)
    median: float | None
    mean: float | None
    ci_low_1s: float | None
    ci_lo_2s: float | None
    ci_hi_2s: float | None
    fav: int
    adv: int
    timecap: int
    data_censored: int
    r_firsthit: float | None       # fav/(fav+adv), disclosed secondary
    win_rate: float | None
    timecap_frac: float | None
    retained: int                  # events retained by the arm's filter
    buildable_retained: int        # retained with a built barrier (pre-resolution)
    block_len: int
    r_e: np.ndarray                # qualifying returns in entry order
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
    """Real-bar OHLC component arrays + CloseTime epochs (float64 / int64)."""
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
    """Detect HA haramis and map each to its real domain-bar index (exact match).

    Returns ``(entry_idx, entry_epoch, ha_annotated)`` where ``entry_idx`` are
    domain-bar indices (ascending) and ``ha_annotated`` is the HA candle frame
    with the ``/STRONG-HA`` impulse annotation (for the disclosed arm).
    """
    ha = generate_heiken_ashi(bars)
    ha_ann = annotate_ha_impulse(ha)
    haramis = detect_ha_harami(ha)
    if haramis.height == 0:
        return np.empty(0, dtype=np.int64), np.empty(0, dtype=np.int64), ha_ann
    harami_epoch = haramis.get_column("HA0Time").dt.epoch("s").to_numpy().astype(np.int64)
    idx = np.searchsorted(bar_epoch, harami_epoch)
    if np.any(idx >= bar_epoch.shape[0]) or np.any(bar_epoch[np.minimum(
            idx, bar_epoch.shape[0] - 1)] != harami_epoch):
        raise ValueError("harami HA0Time not found on the domain-bar grid")
    return idx.astype(np.int64), harami_epoch, ha_ann


def move_arrays(moves: pl.DataFrame, bar_epoch: np.ndarray, bars: pl.DataFrame) -> dict[str, np.ndarray]:
    """Confirmed-move arrays (epochs, prices, direction) + confirm bar indices."""
    if moves.height == 0:
        empty_i = np.empty(0, dtype=np.int64)
        empty_f = np.empty(0, dtype=np.float64)
        return {"confirm_epoch": empty_i, "end_epoch": empty_i, "end_price": empty_f,
                "start_price": empty_f, "direction": empty_i, "confirm_idx": empty_i,
                "magnitude": empty_f}
    confirm_epoch = moves.get_column("ConfirmTime").dt.epoch("s").to_numpy().astype(np.int64)
    idx = np.searchsorted(bar_epoch, confirm_epoch)
    if np.any(idx >= bar_epoch.shape[0]) or np.any(bar_epoch[np.minimum(
            idx, bar_epoch.shape[0] - 1)] != confirm_epoch):
        raise ValueError("ConfirmTime not found on the domain-bar grid")
    start = moves.get_column("StartPrice").to_numpy().astype(np.float64)
    end = moves.get_column("EndPrice").to_numpy().astype(np.float64)
    return {
        "confirm_epoch": confirm_epoch,
        "end_epoch": moves.get_column("EndTime").dt.epoch("s").to_numpy().astype(np.int64),
        "end_price": end, "start_price": start,
        "direction": moves.get_column("Direction").to_numpy().astype(np.int64),
        "confirm_idx": idx.astype(np.int64), "magnitude": np.abs(end - start),
    }


def ma_segment_moves(ohlc: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """MA(20,50)-crossover segmentation as a ZigZag-shaped confirmed-move set.

    A 'move' runs crossover->crossover; ``Direction`` is the diff sign during the
    segment (``+1`` fast>slow). ``ConfirmTime``/``EndTime`` = the closing
    crossover bar; ``StartPrice``/``EndPrice`` = real closes at the bracketing
    crossovers. Real prices only.
    """
    close, epoch = ohlc["close"], ohlc["epoch"]
    n = close.shape[0]
    empty = {k: np.empty(0, dtype=t) for k, t in (
        ("confirm_epoch", np.int64), ("end_epoch", np.int64), ("end_price", np.float64),
        ("start_price", np.float64), ("direction", np.int64), ("confirm_idx", np.int64),
        ("magnitude", np.float64))}
    if n <= MA_SLOW:
        return empty
    fast = _sma(close, MA_FAST)
    slow = _sma(close, MA_SLOW)
    diff = fast - slow
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


def _sma(values: np.ndarray, window: int) -> np.ndarray:
    """Trailing simple moving average; ``NaN`` until ``window`` values exist."""
    out = np.full(values.shape[0], np.nan, dtype=np.float64)
    if values.shape[0] < window:
        return out
    cs = np.cumsum(np.insert(values, 0, 0.0))
    out[window - 1:] = (cs[window:] - cs[:-window]) / window
    return out


# --------------------------------------------------------------------------- #
# Pure computation — /STRONG-HA disclosed retention (bounded loop)
# --------------------------------------------------------------------------- #
def strong_ha_retention(
    ha_ann: pl.DataFrame, entry_epoch: np.ndarray, start_epoch: np.ndarray,
    in_trend: np.ndarray, valid: np.ndarray,
) -> dict[str, np.ndarray]:
    """Per-harami ``/STRONG-HA`` retention (same-dir binding-disclosed; any-dir).

    A harami is retained iff a qualifying impulse run lies inside its in-progress
    span ``(StartTime_inprogress, t_i]`` (``run_first > start`` and
    ``run_last <= t_i``); same-direction additionally requires
    ``run_dir == in-progress trend``. Bounded scan over runs per harami (runs and
    haramis are both sparse relative to bars).
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


# --------------------------------------------------------------------------- #
# Pure computation — resolve one arm population -> ArmResult
# --------------------------------------------------------------------------- #
def resolve_arm(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, entry_close: np.ndarray,
    rd: np.ndarray, m_sofar: np.ndarray, n_event: np.ndarray, atr_entry: np.ndarray,
    buildable: np.ndarray, retained: np.ndarray, rng: np.random.Generator,
) -> ArmResult:
    """Build barriers, P15-resolve, and bootstrap the median for one arm.

    ``buildable`` = built-barrier eligibility (valid in-progress, non-warmup,
    ``M_sofar>0``, finite positive ATR). ``retained`` = the arm's filter mask.
    The population is ``buildable & retained``; the P14 denominator is its
    FAV/ADV/TIMECAP subset.
    """
    population = buildable & retained
    bar = benchmark_barriers(entry_close, rd, m_sofar)
    classes, exit_px = resolve_path_ordered(
        ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"], entry_idx,
        bar["fav"], bar["adv"], rd, n_event, population, ohlc["close"].shape[0])
    r_e_all = realised_returns(classes, exit_px, entry_close, rd, atr_entry)
    qual = population & qualifying_mask(classes, exit_px, atr_entry)
    r_e = r_e_all[qual]
    order = np.argsort(entry_idx[qual], kind="stable")
    r_e = r_e[order]
    fav = int((qual & (classes == CLASS_FAV)).sum())
    adv = int((qual & (classes == CLASS_ADV)).sum())
    timecap = int((qual & (classes == CLASS_TIMECAP)).sum())
    censored = int((population & (classes == CLASS_DATA_CENSORED)).sum())
    return _summarize_arm(r_e, fav, adv, timecap, censored,
                          int(retained.sum()), int(population.sum()), rng)


def _summarize_arm(
    r_e: np.ndarray, fav: int, adv: int, timecap: int, censored: int,
    retained: int, buildable_retained: int, rng: np.random.Generator,
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
        timecap_frac=(timecap / m if m > 0 else None),
        retained=retained, buildable_retained=buildable_retained,
        block_len=block_len, r_e=r_e, dist=dist)


# --------------------------------------------------------------------------- #
# Pure computation — matched-count random baseline
# --------------------------------------------------------------------------- #
def matched_random_arm(
    ohlc: dict[str, np.ndarray], state: Any, n_event_all: np.ndarray,
    warmup_all: np.ndarray, atr_all: np.ndarray, signal_entry_idx: np.ndarray,
    draw_count: int, rng_draw: np.random.Generator, rng_boot: np.random.Generator,
) -> tuple[ArmResult, int]:
    """Matched-count random control over the eligible non-signal bar pool.

    Eligible bars: valid in-progress, ``M_sofar>0``, finite positive ATR, a built
    adaptive cap (non-warmup), and not a binding ``/STRONG-STAT`` retained-signal
    entry bar. The exclusion set is the **binding arm only** (``signal_entry_idx``
    = ``entry_idx[stat_retained]``): this control exists solely to contrast the
    binding ``/STRONG-STAT`` arm, so disclosed ``/STRONG-HA`` haramis are *not*
    excluded — they are legitimate non-binding-signal points in the regime pool,
    and the ``/STRONG-HA`` arm carries no matched-random control of its own (it is
    reported as a standalone disclosed median/CI, never compared to this baseline
    and never able to change the binding EVIDENCE_* verdict). Retaining any
    reversal-bearing HA-only bars in the pool can only *inflate* the null, which is
    conservative for the binding contrast. Direction is **not** random — each drawn
    bar takes its in-progress ``rd``. Draws ``draw_count`` bars without replacement
    (the signal's qualifying count). Returns ``(ArmResult, pool_size)``.
    """
    n_bars = ohlc["close"].shape[0]
    eligible = (state.valid & (state.m_sofar > 0.0) & np.isfinite(atr_all)
                & (atr_all > 0.0) & (~warmup_all))
    is_signal = np.zeros(n_bars, dtype=bool)
    is_signal[signal_entry_idx] = True
    eligible &= ~is_signal
    pool = np.flatnonzero(eligible)
    if draw_count <= 0 or pool.shape[0] == 0:
        return _summarize_arm(np.empty(0), 0, 0, 0, 0, 0, 0, rng_boot), int(pool.shape[0])
    k = min(draw_count, pool.shape[0])
    drawn = np.sort(rng_draw.choice(pool, size=k, replace=False))
    buildable = np.ones(k, dtype=bool)
    retained = np.ones(k, dtype=bool)
    res = resolve_arm(
        ohlc, drawn, ohlc["close"][drawn], state.rd[drawn], state.m_sofar[drawn],
        n_event_all[drawn], atr_all[drawn], buildable, retained, rng_boot)
    return res, int(pool.shape[0])


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
    n_bars = bars.height
    moves = generate_zigzag(bars, atr_period=ATR_PERIOD, atr_mult=ATR_MULT)
    mv = move_arrays(moves, ohlc["epoch"], bars)
    atr = wilder_atr(ohlc["high"], ohlc["low"], ohlc["close"], ATR_PERIOD)
    entry_idx, entry_epoch, ha_ann = harami_entry_indices(bars, ohlc["epoch"])
    base = {"domain": domain, "n_bars": n_bars, "n_moves": int(moves.height),
            "n_harami": int(entry_idx.shape[0])}
    if entry_idx.shape[0] == 0 or mv["confirm_epoch"].shape[0] == 0:
        return {**base, "arms": {}, "empty": True}

    entry_close = ohlc["close"][entry_idx]
    state = live_in_progress_state(entry_epoch, entry_close, mv["confirm_epoch"],
                                   mv["end_price"], mv["end_epoch"], mv["direction"])
    n_event, warmup = adaptive_time_caps_by_epoch(entry_epoch, mv["confirm_epoch"], mv["confirm_idx"])
    atr_entry = atr[entry_idx]
    buildable = (state.valid & (state.m_sofar > 0.0) & np.isfinite(atr_entry)
                 & (atr_entry > 0.0) & (~warmup))

    stat = live_strong_stat(state.k, state.m_sofar, mv["magnitude"])
    ha_ret = strong_ha_retention(ha_ann, entry_epoch, state.start_epoch, -state.rd, state.valid)
    arms = _resolve_signal_arms(ohlc, entry_idx, entry_close, state, n_event, atr_entry,
                                buildable, stat, ha_ret, cell_index)
    baselines = _resolve_baselines(bars, ohlc, mv, entry_idx, entry_epoch, entry_close,
                                   state, n_event, warmup, atr, arms["signal_stat"],
                                   stat["retained_p75"], cell_index)
    return {**base, "empty": False, "arms": arms, **baselines,
            "buildable_haramis": int(buildable.sum())}


def _resolve_signal_arms(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, entry_close: np.ndarray,
    state: Any, n_event: np.ndarray, atr_entry: np.ndarray, buildable: np.ndarray,
    stat: dict[str, np.ndarray], ha_ret: dict[str, np.ndarray], cell_index: int,
) -> dict[str, ArmResult]:
    """Binding ``/STRONG-STAT`` arm + the three disclosed conditioning arms."""
    def arm(mask: np.ndarray, purpose: int) -> ArmResult:
        return resolve_arm(ohlc, entry_idx, entry_close, state.rd, state.m_sofar,
                           n_event, atr_entry, buildable, mask, _rng(cell_index, purpose))
    return {
        "signal_stat": arm(stat["retained_p75"], RNG_STAT),
        "signal_ha": arm(ha_ret["same"], RNG_HA),
        "signal_stat_mad": arm(stat["retained_mad"], RNG_STATMAD),
        "signal_ha_any": arm(ha_ret["any"], RNG_HAANY),
    }


def _resolve_baselines(
    bars: pl.DataFrame, ohlc: dict[str, np.ndarray], mv: dict[str, np.ndarray],
    entry_idx: np.ndarray, entry_epoch: np.ndarray, entry_close: np.ndarray,
    state: Any, n_event: np.ndarray, warmup: np.ndarray, atr: np.ndarray,
    signal: ArmResult, stat_retained: np.ndarray, cell_index: int,
) -> dict[str, Any]:
    """P13 matched-random and MA(20,50)-segmentation baselines + contrast CIs."""
    bar_epoch = ohlc["epoch"]
    all_idx = np.arange(ohlc["close"].shape[0], dtype=np.int64)
    state_all = live_in_progress_state(bar_epoch, ohlc["close"], mv["confirm_epoch"],
                                       mv["end_price"], mv["end_epoch"], mv["direction"])
    n_event_all, warmup_all = adaptive_time_caps_by_epoch(bar_epoch, mv["confirm_epoch"],
                                                          mv["confirm_idx"])
    rand, pool_size = matched_random_arm(
        ohlc, state_all, n_event_all, warmup_all, atr, entry_idx[stat_retained],
        signal.m, _rng(cell_index, RNG_RAND_DRAW), _rng(cell_index, RNG_RAND_BOOT))
    ma = _ma_seg_arm(bars, ohlc, entry_idx, entry_epoch, entry_close, atr, cell_index)
    # Both contrasts compare the binding /STRONG-STAT arm only (``signal``); the
    # disclosed /STRONG-HA arm has no baseline comparison (no beats_* flag is
    # computed for it). The matched-random pool above excludes only STAT-retained
    # bars — see ``matched_random_arm``.
    return {
        "matched_random": rand, "ma_seg": ma, "random_pool_size": pool_size,
        "contrast_random": contrast_ci(signal.dist, rand.dist),
        "contrast_ma": contrast_ci(signal.dist, ma.dist),
    }


def _ma_seg_arm(
    bars: pl.DataFrame, ohlc: dict[str, np.ndarray], entry_idx: np.ndarray,
    entry_epoch: np.ndarray, entry_close: np.ndarray, atr: np.ndarray, cell_index: int,
) -> ArmResult:
    """MA(20,50)-segmentation baseline through the identical conditioned pipeline."""
    seg = ma_segment_moves(ohlc)
    if seg["confirm_epoch"].shape[0] == 0:
        return _summarize_arm(np.empty(0), 0, 0, 0, 0, 0, 0, _rng(cell_index, RNG_MASEG_BOOT))
    state = live_in_progress_state(entry_epoch, entry_close, seg["confirm_epoch"],
                                   seg["end_price"], seg["end_epoch"], seg["direction"])
    n_event, warmup = adaptive_time_caps_by_epoch(entry_epoch, seg["confirm_epoch"], seg["confirm_idx"])
    atr_entry = atr[entry_idx]
    buildable = (state.valid & (state.m_sofar > 0.0) & np.isfinite(atr_entry)
                 & (atr_entry > 0.0) & (~warmup))
    stat = live_strong_stat(state.k, state.m_sofar, seg["magnitude"])
    return resolve_arm(ohlc, entry_idx, entry_close, state.rd, state.m_sofar, n_event,
                       atr_entry, buildable, stat["retained_p75"], _rng(cell_index, RNG_MASEG_BOOT))


def _rng(cell_index: int, purpose: int) -> np.random.Generator:
    """Deterministic, independent per-cell-per-purpose RNG (reproducible)."""
    return np.random.default_rng([BASE_SEED, cell_index, purpose])


# --------------------------------------------------------------------------- #
# Per-cell record flattening + viability / beats classification
# --------------------------------------------------------------------------- #
def cell_record(instrument: str, cell: dict[str, Any]) -> dict[str, Any]:
    """Flatten one cell's pipeline output into a per-cell summary record."""
    domain = cell["domain"]
    rec: dict[str, Any] = {
        "instrument": instrument, "domain": domain, "member": True,
        "n_bars": cell["n_bars"], "n_moves": cell["n_moves"],
        "n_harami": cell["n_harami"], "excluded": False,
    }
    if cell.get("empty", False):
        rec.update(_empty_metric_fields())
        return rec
    sig = cell["arms"]["signal_stat"]
    rand, ma = cell["matched_random"], cell["ma_seg"]
    rec["buildable_haramis"] = cell["buildable_haramis"]
    rec["random_pool_size"] = cell["random_pool_size"]
    rec.update(_arm_fields(sig, "stat"))
    rec.update(_arm_fields(cell["arms"]["signal_ha"], "ha"))
    rec.update(_arm_fields(cell["arms"]["signal_stat_mad"], "statmad"))
    rec.update(_arm_fields(cell["arms"]["signal_ha_any"], "haany"))
    rec.update(_arm_fields(rand, "rand"))
    rec.update(_arm_fields(ma, "maseg"))
    rec["contrast_random_low"] = cell["contrast_random"][0]
    rec["contrast_ma_low"] = cell["contrast_ma"][0]
    rec["retained_fraction"] = (
        sig.m / cell["buildable_haramis"] if cell["buildable_haramis"] else None)
    _classify_cell(rec, sig, rand, ma, cell["contrast_random"][0], cell["contrast_ma"][0])
    return rec


def _classify_cell(
    rec: dict[str, Any], sig: ArmResult, rand: ArmResult, ma: ArmResult,
    contrast_random_low: float, contrast_ma_low: float,
) -> None:
    """Set per-cell viability, baseline-beat flags, and composition status code."""
    viable = (sig.m >= POWER_FLOOR and sig.ci_low_1s is not None
              and np.isfinite(sig.ci_low_1s) and sig.ci_low_1s > 0.0)
    rec["powered"] = sig.m >= POWER_FLOOR
    rec["viable"] = bool(viable)
    rec["beats_random"] = _beats(rand, contrast_random_low)
    rec["beats_ma"] = _beats(ma, contrast_ma_low)
    rec["beats_both"] = rec["beats_random"] and rec["beats_ma"]
    if not rec["powered"]:
        status = "NOT_VIABLE_BY_POWER"
    elif viable:
        status = "VIABLE"
    else:
        status = "CI_SPANS_0"
    rec["viable_status"] = status
    rec["status_code"] = VSTATUS_CODES[status]


def _beats(baseline: ArmResult, contrast_low: float) -> bool:
    """Signal beats a baseline iff the baseline is non-viable, or contrast CI>0."""
    base_viable = (baseline.m >= POWER_FLOOR and baseline.ci_low_1s is not None
                   and np.isfinite(baseline.ci_low_1s) and baseline.ci_low_1s > 0.0)
    if not base_viable:
        return True
    return contrast_low is not None and np.isfinite(contrast_low) and contrast_low > 0.0


def _arm_fields(a: ArmResult, prefix: str) -> dict[str, Any]:
    """Flatten one ArmResult into per-cell columns (no per-event arrays)."""
    return {
        f"{prefix}_m": a.m, f"{prefix}_median": a.median, f"{prefix}_mean": a.mean,
        f"{prefix}_ci_low_1s": a.ci_low_1s, f"{prefix}_ci_lo_2s": a.ci_lo_2s,
        f"{prefix}_ci_hi_2s": a.ci_hi_2s, f"{prefix}_fav": a.fav, f"{prefix}_adv": a.adv,
        f"{prefix}_timecap": a.timecap, f"{prefix}_data_censored": a.data_censored,
        f"{prefix}_r_firsthit": a.r_firsthit, f"{prefix}_win_rate": a.win_rate,
        f"{prefix}_timecap_frac": a.timecap_frac, f"{prefix}_retained": a.retained,
        f"{prefix}_block_len": a.block_len,
    }


def _empty_metric_fields() -> dict[str, Any]:
    """Metric columns for a member cell with no harami/move population."""
    rec = {"buildable_haramis": 0, "random_pool_size": 0, "retained_fraction": None,
           "powered": False, "viable": False, "beats_random": False,
           "beats_ma": False, "beats_both": False, "viable_status": "NOT_VIABLE_BY_POWER",
           "status_code": VSTATUS_CODES["NOT_VIABLE_BY_POWER"],
           "contrast_random_low": None, "contrast_ma_low": None}
    blank = ArmResult(0, None, None, None, None, None, 0, 0, 0, 0, None, None, None,
                      0, 0, 1, np.empty(0), np.empty(0))
    for prefix in ("stat", "ha", "statmad", "haany", "rand", "maseg"):
        rec.update(_arm_fields(blank, prefix))
    return rec


def excluded_record(instrument: str, domain: str) -> dict[str, Any]:
    """Record for a COVERAGE_EXCLUDED cell (not in the EXP-049 member grid)."""
    rec: dict[str, Any] = {
        "instrument": instrument, "domain": domain, "member": False, "excluded": True,
        "n_bars": None, "n_moves": None, "n_harami": None, "powered": False,
        "viable": False, "beats_random": False, "beats_ma": False, "beats_both": False,
        "viable_status": "EXCLUDED", "status_code": VSTATUS_CODES["EXCLUDED"]}
    rec.update(_empty_metric_fields())
    rec["viable_status"], rec["status_code"] = "EXCLUDED", VSTATUS_CODES["EXCLUDED"]
    return rec


# --------------------------------------------------------------------------- #
# Composition + mechanical EVIDENCE_* classification
# --------------------------------------------------------------------------- #
def composition_readout(records: list[dict[str, Any]], defect: dict[str, Any]) -> dict[str, Any]:
    """P11 composition tallies + the mechanical EVIDENCE_* verdict."""
    members = [r for r in records if r["member"]]
    viable = [r for r in members if r["viable"]]
    powered = [r for r in members if r["powered"]]
    beat = [r for r in members if r["viable"] and r["beats_both"]]
    v_sig, i_sig = _tally(viable)
    p_pow, i_pow = _tally(powered)
    v_beat, i_beat = _tally(beat)
    evidence = _evidence_label(defect, v_sig, i_sig, v_beat, i_beat, p_pow, i_pow)
    return {
        "verdict": evidence,
        "signal_viable": {"n_cells": v_sig, "n_instruments": i_sig,
                          "cells": [f"{r['instrument']}-{r['domain']}" for r in viable],
                          "composition_met": v_sig >= P11_MIN_CELLS and i_sig >= P11_MIN_INSTR},
        "signal_beats_both": {"n_cells": v_beat, "n_instruments": i_beat,
                              "cells": [f"{r['instrument']}-{r['domain']}" for r in beat],
                              "composition_met": v_beat >= P11_MIN_CELLS and i_beat >= P11_MIN_INSTR},
        "powered": {"n_cells": p_pow, "n_instruments": i_pow,
                    "quorum_formable": p_pow >= P11_MIN_CELLS and i_pow >= P11_MIN_INSTR},
        "defect": defect,
        "rule": ("VIABLE iff median CI_low(1s)>0 AND m>=30; P11 iff >=5 cells over "
                 ">=3 instruments; EVIDENCE_FOR iff signal P11 AND beats-both P11."),
    }


def _tally(rows: list[dict[str, Any]]) -> tuple[int, int]:
    return len(rows), len({r["instrument"] for r in rows})


def _evidence_label(
    defect: dict[str, Any], v_sig: int, i_sig: int, v_beat: int, i_beat: int,
    p_pow: int, i_pow: int,
) -> str:
    """Mechanical EVIDENCE_* per the analysis-plan Interpretation Guide."""
    if defect["is_defect"]:
        return "SUBSTRATE_METHOD_DEFECT"
    signal_p11 = v_sig >= P11_MIN_CELLS and i_sig >= P11_MIN_INSTR
    beats_p11 = v_beat >= P11_MIN_CELLS and i_beat >= P11_MIN_INSTR
    if signal_p11 and beats_p11:
        return "EVIDENCE_FOR"
    if p_pow >= P11_MIN_CELLS and i_pow >= P11_MIN_INSTR:
        return "EVIDENCE_AGAINST"
    return "INCONCLUSIVE_POWER_LIMITED"


# --------------------------------------------------------------------------- #
# Determinism replay + reconciliation anchor (DEFECT guards)
# --------------------------------------------------------------------------- #
def determinism_replay(train_1m: pl.DataFrame, domain: str, train_end_epoch: int,
                       cell_index: int) -> bool:
    """Re-run one cell end-to-end and assert byte-identical binding outputs."""
    a = compute_cell(train_1m, domain, train_end_epoch, cell_index)
    b = compute_cell(train_1m, domain, train_end_epoch, cell_index)
    if a.get("empty") or b.get("empty"):
        return a.get("empty") == b.get("empty")
    sa, sb = a["arms"]["signal_stat"], b["arms"]["signal_stat"]
    return (np.array_equal(sa.r_e, sb.r_e)
            and (sa.median, sa.ci_low_1s, sa.ci_lo_2s, sa.ci_hi_2s)
            == (sb.median, sb.ci_low_1s, sb.ci_lo_2s, sb.ci_hi_2s)
            and np.array_equal(a["matched_random"].r_e, b["matched_random"].r_e)
            and np.array_equal(a["ma_seg"].r_e, b["ma_seg"].r_e))


def reconciliation_anchor(train_1m: pl.DataFrame, domain: str, train_end_epoch: int,
                          cell_index: int) -> dict[str, Any]:
    """Independently recompute the binding arm's FAV/ADV count and one r_e.

    For the single benchmark geometry every FAV exit is the favourable level and
    every ADV exit the adverse level, so |r_e| == 0.5*M_sofar/ATR_entry and the
    sign is +1 for FAV, -1 for ADV. This is an independent check of the resolver
    and the realised-return arithmetic.
    """
    cell = compute_cell(train_1m, domain, train_end_epoch, cell_index)
    if cell.get("empty"):
        return {"checked": False, "reason": "empty cell"}
    sig = cell["arms"]["signal_stat"]
    if sig.m == 0:
        return {"checked": False, "reason": "no qualifying events"}
    # Single benchmark geometry: every FAV exits at the favourable level (r_e>0)
    # and every ADV at the adverse level (r_e<0); only TIMECAP exits can be zero
    # or either sign. So positives >= fav, negatives >= adv, and the three classes
    # must partition the qualifying population exactly.
    n_pos = int((sig.r_e > 0.0).sum())
    n_neg = int((sig.r_e < 0.0).sum())
    ok = (n_pos >= sig.fav and n_neg >= sig.adv
          and (sig.fav + sig.adv + sig.timecap) == sig.m
          and bool(np.isfinite(sig.r_e[0])))
    return {"checked": True, "cell": f"{domain}#{cell_index}", "fav": sig.fav,
            "adv": sig.adv, "timecap": sig.timecap, "m": sig.m,
            "positive_returns": n_pos, "negative_returns": n_neg,
            "first_r_e": float(sig.r_e[0]), "consistent": bool(ok)}


# --------------------------------------------------------------------------- #
# Plotting (bounded; from collected summaries + pooled per-event sample)
# --------------------------------------------------------------------------- #
def _matrix(records: list[dict[str, Any]], value: str) -> np.ndarray:
    """instrument x domain matrix (NaN where missing) for heatmaps."""
    domains = list(DOMAINS.keys())
    matrix = np.full((len(INSTRUMENTS), len(domains)), np.nan)
    lookup = {(r["instrument"], r["domain"]): r.get(value) for r in records}
    for i, inst in enumerate(INSTRUMENTS):
        for j, dom in enumerate(domains):
            val = lookup.get((inst, dom))
            if val is not None and isinstance(val, (int, float)):
                matrix[i, j] = float(val)
    return matrix


def plot_forest(records: list[dict[str, Any]], save_path: Path) -> None:
    """Per-cell binding median expectancy with one-sided CI_low whisker."""
    viable_rows = sorted(
        [r for r in records if r["member"] and r["stat_median"] is not None],
        key=lambda r: r["stat_median"])
    if not viable_rows:
        _placeholder(save_path, "no powered cells")
        return
    labels = [f"{r['instrument']}-{r['domain']}" for r in viable_rows]
    med = np.array([r["stat_median"] for r in viable_rows])
    low = np.array([r["stat_ci_low_1s"] if r["stat_ci_low_1s"] is not None
                    else np.nan for r in viable_rows])
    rand = np.array([r["rand_median"] if r["rand_median"] is not None
                     else np.nan for r in viable_rows])
    ma = np.array([r["maseg_median"] if r["maseg_median"] is not None
                   else np.nan for r in viable_rows])
    y = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(8, max(4, 0.28 * len(labels))))
    colours = ["#1a9850" if r["viable"] else "#999999" for r in viable_rows]
    ax.scatter(med, y, color=colours, s=26, zorder=3, label="signal median")
    ax.hlines(y, np.minimum(low, med), med, color=colours, alpha=0.7, zorder=2)
    ax.scatter(rand, y, color="#d73027", marker="x", s=20, label="matched-random")
    ax.scatter(ma, y, color="#4575b4", marker="+", s=24, label="MA(20,50)-seg")
    ax.axvline(0.0, color="k", lw=0.8, ls="--")
    ax.set_yticks(y, labels, fontsize=5)
    ax.set_xlabel("median gross expectancy (ATR units)")
    ax.set_title(f"{EXPERIMENT_ID}: per-cell median expectancy (binding /STRONG-STAT)")
    ax.legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_status_heatmap(records: list[dict[str, Any]], save_path: Path) -> None:
    """P11 composition status heatmap (instrument x domain)."""
    matrix = _matrix(records, "status_code")
    cmap = ListedColormap(VSTATUS_COLORS)
    norm = BoundaryNorm(np.arange(-0.5, len(VSTATUS_COLORS) + 0.5), cmap.N)
    fig, ax = plt.subplots(figsize=(7, 9))
    ax.imshow(matrix, cmap=cmap, norm=norm, aspect="auto")
    for i, inst in enumerate(INSTRUMENTS):
        for j, dom in enumerate(DOMAINS):
            rec = next((r for r in records if r["instrument"] == inst
                        and r["domain"] == dom), None)
            if rec and rec.get("stat_m"):
                ax.text(j, i, str(rec["stat_m"]), ha="center", va="center", fontsize=5)
    ax.set_xticks(range(len(DOMAINS)), list(DOMAINS.keys()))
    ax.set_yticks(range(len(INSTRUMENTS)), INSTRUMENTS)
    ax.set_title(f"{EXPERIMENT_ID}: viability status (annotated: qualifying m)")
    handles = [plt.Rectangle((0, 0), 1, 1, color=VSTATUS_COLORS[c])
               for c in VSTATUS_CODES.values()]
    ax.legend(handles, list(VSTATUS_CODES.keys()), bbox_to_anchor=(1.02, 1),
              loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_return_distributions(pooled: dict[str, list[float]], save_path: Path) -> None:
    """Per-event ATR-normalised return distribution by arm (viable cells pooled)."""
    arms = [a for a in PLOT_ARMS if pooled.get(a)]
    if not arms:
        _placeholder(save_path, "no viable-cell events to pool")
        return
    data = [np.asarray(pooled[a]) for a in arms]
    fig, ax = plt.subplots(figsize=(8, 5))
    parts = ax.violinplot(data, showmedians=True, showextrema=False)
    for pc in parts["bodies"]:
        pc.set_alpha(0.5)
    ax.axhline(0.0, color="k", lw=0.8, ls="--")
    ax.set_xticks(range(1, len(arms) + 1), arms, fontsize=8)
    ax.set_ylabel("per-event gross return (ATR units)")
    ax.set_title(f"{EXPERIMENT_ID}: per-event return by arm (viable cells pooled)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_retained_fraction(records: list[dict[str, Any]], save_path: Path) -> None:
    """Conditioned qualifying-count heatmap (annotated with retained fraction)."""
    matrix = _matrix(records, "stat_m")
    fig, ax = plt.subplots(figsize=(7, 9))
    sns.heatmap(matrix, ax=ax, cmap="viridis", annot=False,
                xticklabels=list(DOMAINS.keys()), yticklabels=INSTRUMENTS,
                cbar_kws={"label": "qualifying events (binding /STRONG-STAT)"})
    for i, inst in enumerate(INSTRUMENTS):
        for j, dom in enumerate(DOMAINS):
            rec = next((r for r in records if r["instrument"] == inst
                        and r["domain"] == dom), None)
            if rec and rec.get("retained_fraction") is not None:
                ax.text(j + 0.5, i + 0.5, f"{rec['retained_fraction']:.2f}",
                        ha="center", va="center", fontsize=5, color="w")
    ax.axhline(0)  # noqa: keep frame
    ax.set_title(f"{EXPERIMENT_ID}: qualifying count (n) / retained fraction (f), floor={POWER_FLOOR}")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _placeholder(save_path: Path, message: str) -> None:
    """Write a small placeholder figure when a plot has no data."""
    fig, ax = plt.subplots(figsize=(6, 2))
    ax.text(0.5, 0.5, f"{EXPERIMENT_ID}: {message}", ha="center", va="center")
    ax.axis("off")
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def make_plots(records: list[dict[str, Any]], pooled: dict[str, list[float]]) -> None:
    """Render the four bounded plots from collected summaries + pooled events."""
    plot_forest(records, PLOTS_DIR / "per_cell_median_forest.png")
    plot_status_heatmap(records, PLOTS_DIR / "p11_composition_heatmap.png")
    plot_return_distributions(pooled, PLOTS_DIR / "return_distribution_by_arm.png")
    plot_retained_fraction(records, PLOTS_DIR / "conditioning_retained_fraction.png")


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _cell_index_map() -> dict[tuple[str, str], int]:
    return {(inst, dom): i for i, (inst, dom) in enumerate(
        (inst, dom) for inst in INSTRUMENTS for dom in DOMAINS)}


def _collect_pooled(cell: dict[str, Any], rec: dict[str, Any],
                    pooled: dict[str, list[float]]) -> None:
    """Pool per-event returns from a binding-viable cell for the distribution plot."""
    if cell.get("empty") or not rec["viable"]:
        return
    pooled["signal_stat"].extend(cell["arms"]["signal_stat"].r_e.tolist())
    pooled["signal_ha"].extend(cell["arms"]["signal_ha"].r_e.tolist())
    pooled["matched_random"].extend(cell["matched_random"].r_e.tolist())
    pooled["ma_seg"].extend(cell["ma_seg"].r_e.tolist())


def run() -> dict[str, Any]:
    """Run all member cells and write artifacts. Returns the run summary."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    cell_index = _cell_index_map()
    records: list[dict[str, Any]] = []
    pooled: dict[str, list[float]] = {a: [] for a in PLOT_ARMS}
    instrument_meta: dict[str, Any] = {}
    defect = {"is_defect": False, "non_deterministic": [], "reconciliation": []}
    replayed: set[str] = set()

    for instrument in tqdm(INSTRUMENTS, desc="instruments"):
        members = [d for d in DOMAINS if (instrument, d) not in EXCLUDED_CELLS]
        if not members:
            for domain in DOMAINS:
                records.append(excluded_record(instrument, domain))
            continue
        train_1m, meta = load_train_1m(instrument)
        instrument_meta[instrument] = meta
        for domain in DOMAINS:
            if (instrument, domain) in EXCLUDED_CELLS:
                records.append(excluded_record(instrument, domain))
                continue
            ci = cell_index[(instrument, domain)]
            cell = compute_cell(train_1m, domain, meta["train_end_epoch_s"], ci)
            rec = cell_record(instrument, cell)
            _collect_pooled(cell, rec, pooled)
            records.append(rec)
            _maybe_guard(train_1m, domain, meta, ci, cell, defect, instrument, replayed)
        del train_1m

    readout = composition_readout(records, defect)
    write_outputs(records, readout, pooled, instrument_meta, defect)
    make_plots(records, pooled)
    return _summarize(records, readout)


def _maybe_guard(
    train_1m: pl.DataFrame, domain: str, meta: dict[str, Any], cell_index: int,
    cell: dict[str, Any], defect: dict[str, Any], instrument: str,
    replayed: set[str],
) -> None:
    """Determinism replay + reconciliation on the first usable cell per instrument.

    Stratifying one replay per instrument (vs a single global cell) widens the
    non-determinism detection surface to ~17 cells spanning every data-length
    regime, at ~1% overhead, while keeping the guard bounded. Each instrument's
    first non-empty, non-zero-event cell is replayed once; results accumulate.
    """
    if instrument in replayed or cell.get("empty") or cell["arms"]["signal_stat"].m == 0:
        return
    ok = determinism_replay(train_1m, domain, meta["train_end_epoch_s"], cell_index)
    recon = reconciliation_anchor(train_1m, domain, meta["train_end_epoch_s"], cell_index)
    recon["instrument"] = instrument
    defect["reconciliation"].append(recon)
    if not ok:
        defect["non_deterministic"].append(f"{instrument}-{domain}#{cell_index}")
    if not ok or (recon.get("checked") and not recon.get("consistent")):
        defect["is_defect"] = True
    replayed.add(instrument)


def write_outputs(
    records: list[dict[str, Any]], readout: dict[str, Any],
    pooled: dict[str, list[float]], instrument_meta: dict[str, Any],
    defect: dict[str, Any],
) -> None:
    """Persist the per-cell CSV, the pooled per-event parquet, and the two JSONs."""
    df = pl.DataFrame(records, strict=False)
    df.write_csv(RESULTS_DIR / "outcome_primary.csv")

    rows: list[dict[str, Any]] = []
    for arm, vals in pooled.items():
        rows.extend({"arm": arm, "r_e": v} for v in vals)
    pooled_df = (pl.DataFrame(rows) if rows
                 else pl.DataFrame({"arm": [], "r_e": []},
                                   schema={"arm": pl.Utf8, "r_e": pl.Float64}))
    pooled_df.write_parquet(RESULTS_DIR / "per_event_returns.parquet")

    with open(RESULTS_DIR / "composition_readout.json", "w") as fh:
        json.dump(readout, fh, indent=2, default=str)

    meta = {
        "experiment_id": EXPERIMENT_ID,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "014-B", "hypothesis": "HYP-006", "family": "CF-HA-HARAMI-001",
        "stratum": "TRAIN-only (first 49%); nested TEST + final-30% holdout sealed",
        "entry_anchor": "harami confirmation-bar real close (live, pre-ZigZag-confirm)",
        "magnitude_reference": "current-price M_sofar = |C - StartPrice_inprogress| (binding)",
        "geometry": "single benchmark (G1==G2 collapse): fav=C+rd*0.5*M_sofar; 1:1 adverse",
        "fill_model": "P15 path-ordered intrabar (bullish O->L->H->C; bearish O->H->L->C)",
        "params": {
            "atr_period": ATR_PERIOD, "atr_mult": ATR_MULT, "favourable_fraction": 0.50,
            "adverse": "1:1", "stat_window": 20, "stat_min_window": 5, "stat_q": 0.75,
            "ha_run_len": 3, "timecap": "max(6, round(1.5*median(trailing-20 durations)))",
            "ma_segmentation": [MA_FAST, MA_SLOW], "power_floor": POWER_FLOOR,
            "n_boot": 10000, "boot_batch": 2000, "base_seed": BASE_SEED,
            "p11": [P11_MIN_CELLS, P11_MIN_INSTR],
        },
        "binding_endpoint": "median per-event gross ATR-normalised return (P14)",
        "baselines": ["matched-count random (in-progress rd, non-signal pool)",
                      "MA(20,50)-crossover segmentation through the identical pipeline"],
        "determinism_ok": not defect["non_deterministic"],
        "reconciliation": defect["reconciliation"],
        "is_defect": defect["is_defect"],
        "de30_disclosure": DE30_DISCLOSURE,
        "fill_approximation": ("P15 path is a documented approximation of unobserved "
                               "intrabar motion; 1-minute base bars are not replayed "
                               "inside the domain bar (EXP-054 bounds its effect)."),
        "holdout_fence": ("Only Parquet metadata + first train_rows file-order rows read "
                          "per instrument; full file never sorted/collected; every domain "
                          "bar fenced to CloseTime <= train_end_ts; forward scans clipped "
                          "to the data edge; TEST and final-30% holdout never read."),
        "registry": ("CF-HA-HARAMI-001/HYP-006; 0 candidate slots, 0 TEST reads; "
                     "characterization readout feeds the single 014-B G2."),
        "instrument_meta": instrument_meta,
    }
    with open(RESULTS_DIR / "run_metadata.json", "w") as fh:
        json.dump(meta, fh, indent=2, default=str)


def _summarize(records: list[dict[str, Any]], readout: dict[str, Any]) -> dict[str, Any]:
    """Concise stdout summary."""
    status_counts: dict[str, int] = {}
    for r in records:
        status_counts[r["viable_status"]] = status_counts.get(r["viable_status"], 0) + 1
    return {"verdict": readout["verdict"], "status_counts": status_counts,
            "signal_viable": readout["signal_viable"],
            "signal_beats_both": readout["signal_beats_both"],
            "powered": readout["powered"], "defect": readout["defect"]}


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    summary = run()
    LOGGER.info("\n=== %s complete ===", EXPERIMENT_ID)
    LOGGER.info("verdict: %s", summary["verdict"])
    LOGGER.info("viability status counts: %s", json.dumps(summary["status_counts"]))
    LOGGER.info("signal viable: %s cells over %s instruments (P11=%s)",
                summary["signal_viable"]["n_cells"], summary["signal_viable"]["n_instruments"],
                summary["signal_viable"]["composition_met"])
    LOGGER.info("signal beats both baselines: %s cells over %s instruments (P11=%s)",
                summary["signal_beats_both"]["n_cells"],
                summary["signal_beats_both"]["n_instruments"],
                summary["signal_beats_both"]["composition_met"])
    LOGGER.info("powered cells: %s over %s instruments (quorum_formable=%s)",
                summary["powered"]["n_cells"], summary["powered"]["n_instruments"],
                summary["powered"]["quorum_formable"])
    if summary["defect"]["is_defect"]:
        LOGGER.info("DEFECT: %s", json.dumps(summary["defect"], default=str))
    LOGGER.info("artifacts -> %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
