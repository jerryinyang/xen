"""EXP-055 — Long-Horizon Availability (Conditioned HA Harami; AVWAP-analog MFE/MAE).

``CF-HA-HARAMI-001`` / HYP-008 (Phase 014-B lead 3). TRAIN-only, gross; 0 candidate
slots, 0 TEST reads. For each EXP-049/053 member cell (instrument x domain) this
script, on the TRAIN analysis stratum only:

1. slices the first-49% (TRAIN) 1-minute rows by file-order prefix (TEST and the
   final-30% global holdout are never read), aggregates the domain (5m strict;
   15m/30m/1h/2h/4h at min_coverage=0.90) and fences to the TRAIN edge;
2. runs the frozen Wilder-ATR ZigZag substrate, detects HA haramis on HA candles,
   and builds the **live ``/STRONG-STAT`` conditioned population** (identical to
   EXP-053: ``live_in_progress_state`` + ``live_strong_stat``), entered at the
   harami real close and faded against the in-progress move (reversal ``rd``);
3. for each qualifying conditioned harami, measures the gross **ATR-normalised
   lifetime favourable MFE and adverse MAE** over the **end-of-reversal-move (M_b)
   window** — ``[entry+1, c2]`` where ``c2`` is the 2nd confirmed ZigZag pivot
   at/after the harami (operator decision 2026-06-16) — and bootstraps the per-cell
   median (regime-clustered moving block);
4. emits the mechanical ``MOVE_AVAILABLE`` per-cell map and the P11-composed
   ``AVAILABILITY_*`` fork, the 0.5/1.0-ATR reference-band multiples (reference
   only, never subtracted), the ``/STRONG-HA`` + MAD disclosed arms, and the two
   P13 baselines (matched-count random, MA(20,50)-segmentation) measured through
   the identical window;
5. runs a determinism replay + window-invariant check on **every** cell (the
   scope §Correctness-Gates "every per-cell figure frame-identically" gate),
   comparing all binding and disclosed arms plus both baseline contrasts, and
   reconciles the conditioned population (count + a per-cell trigger_idx/time/rd
   digest) against EXP-053 (SUBSTRATE/METHOD_DEFECT guards).

Real prices throughout; HA prices enter only the harami/impulse detectors and
never any metric. Outputs under results/ and plots/; created in orchestration.
"""
from __future__ import annotations

import hashlib
import json
import logging
import sys
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
EXP053_RESULTS = EXPERIMENT_DIR.parent / "EXP-053" / "results"

sys.path.insert(0, str(CODE_DIR))

import availability as av  # noqa: E402
from xen.bar_aggregator import aggregate_ohlc  # noqa: E402
from xen.expectancy import live_in_progress_state, live_strong_stat  # noqa: E402
from xen.ha_harami import detect_ha_harami  # noqa: E402
from xen.heiken_ashi_generator import generate_heiken_ashi  # noqa: E402
from xen.strong_move import annotate_ha_impulse, find_impulse_runs  # noqa: E402
from xen.zigzag import generate_zigzag, wilder_atr  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (Phase 014-B D0 frozen; no tuning)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-055"
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
MA_FAST, MA_SLOW = 20, 50           # P13 MA-segmentation baseline
POWER_FLOOR = av.POWER_FLOOR        # 30 qualifying events
BASE_SEED = 20260616                # frozen master seed (no tuning)
EXCLUDED_FILE_MARKERS = ("analysis70", "analysis_slice", "first70")
# RNG purpose offsets (distinct deterministic streams per cell).
RNG_STAT, RNG_HA, RNG_STATMAD, RNG_HAANY = 1, 2, 3, 4
RNG_RAND_DRAW, RNG_RAND_BOOT, RNG_MASEG = 5, 6, 7
RNG_CONTRAST_RAND, RNG_CONTRAST_MA = 8, 9
# Availability status -> integer code / colour (composition heatmap).
ASTATUS_CODES: dict[str, int] = {
    "MOVE_AVAILABLE": 0, "NOT_AVAILABLE": 1, "NOT_VIABLE_BY_POWER": 2, "EXCLUDED": 3,
}
ASTATUS_COLORS: list[str] = ["#1a9850", "#f46d43", "#cccccc", "#7b3294"]
DE30_DISCLOSURE = (
    "DE30 truncated history: broker m1 history ends 2026-01-16; counts derive "
    "from its own realized timeline and are not span-comparable (VAL-003)."
)
LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class AvailResult:
    """One arm's per-cell lifetime-availability summary + per-event arrays."""

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
    n_retained: int                 # events passing the arm's filter
    n_buildable: int                # retained with valid in-progress + finite ATR
    n_censored: int                 # buildable but M_b incomplete in TRAIN
    block_len: int
    mfe: np.ndarray                 # qualifying MFE in entry order
    mae: np.ndarray                 # qualifying MAE in entry order


def _empty_arm() -> AvailResult:
    """A zero-population arm result."""
    return AvailResult(0, None, None, None, None, None, None, None, None, None,
                       None, 0, 0, 0, 1, np.empty(0), np.empty(0))


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
# Pure computation — domain / substrate / harami alignment (EXP-053 pattern)
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
    """Detect HA haramis and map each to its real domain-bar index (exact match)."""
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


def move_arrays(moves: pl.DataFrame, bar_epoch: np.ndarray) -> dict[str, np.ndarray]:
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

    A 'move' runs crossover->crossover; ``Direction`` is the diff sign during the
    segment. ``ConfirmTime``/``EndTime`` = the closing crossover bar;
    ``StartPrice``/``EndPrice`` = real closes at the bracketing crossovers (real
    prices only). Mirrors the EXP-053 baseline segmentation.
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


# --------------------------------------------------------------------------- #
# Pure computation — measure one population's lifetime availability -> AvailResult
# --------------------------------------------------------------------------- #
def _measure(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, entry_close: np.ndarray,
    rd: np.ndarray, atr_entry: np.ndarray, c2: np.ndarray, qual: np.ndarray,
    n_retained: int, n_buildable: int, n_censored: int, rng: np.random.Generator,
) -> AvailResult:
    """Compute ATR-normalised lifetime MFE/MAE for the qualifying subset + CI."""
    qidx = np.flatnonzero(qual)
    if qidx.size:
        mfe, mae = av.lifetime_excursions_atr(
            ohlc["high"], ohlc["low"], entry_close[qidx], entry_idx[qidx],
            c2[qidx], rd[qidx], atr_entry[qidx])
    else:
        mfe = mae = np.empty(0, dtype=np.float64)
    return _summarize_arm(mfe, mae, n_retained, n_buildable, n_censored, rng)


def _summarize_arm(
    mfe: np.ndarray, mae: np.ndarray, n_retained: int, n_buildable: int,
    n_censored: int, rng: np.random.Generator,
) -> AvailResult:
    """Assemble an ``AvailResult``; bootstrap the median CIs when powered."""
    m = int(mfe.shape[0])
    median_mfe = mean_mfe = median_mae = mean_mae = None
    mfe_low = mfe_lo2 = mfe_hi2 = mae_low = mae_lo2 = mae_hi2 = None
    block_len = max(1, int(round(max(m, 1) ** (1.0 / 3.0))))
    if m > 0:
        median_mfe, mean_mfe = float(np.median(mfe)), float(np.mean(mfe))
        median_mae, mean_mae = float(np.median(mae)), float(np.mean(mae))
    if m >= POWER_FLOOR:
        median_mfe, mfe_low, mfe_lo2, mfe_hi2, block_len = av.median_block_bootstrap(mfe, rng)
        median_mae, mae_low, mae_lo2, mae_hi2, _ = av.median_block_bootstrap(mae, rng)
    return AvailResult(
        m=m, median_mfe=median_mfe, mfe_ci_low_1s=mfe_low, mfe_ci_lo_2s=mfe_lo2,
        mfe_ci_hi_2s=mfe_hi2, median_mae=median_mae, mae_ci_low_1s=mae_low,
        mae_ci_lo_2s=mae_lo2, mae_ci_hi_2s=mae_hi2, mean_mfe=mean_mfe,
        mean_mae=mean_mae, n_retained=n_retained, n_buildable=n_buildable,
        n_censored=n_censored, block_len=block_len, mfe=mfe, mae=mae)


def avail_arm(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, entry_close: np.ndarray,
    rd: np.ndarray, atr_entry: np.ndarray, c2: np.ndarray, censored: np.ndarray,
    retained_mask: np.ndarray, buildable: np.ndarray, rng: np.random.Generator,
) -> AvailResult:
    """One conditioned arm: population = buildable & retained; qual = ~censored."""
    population = buildable & retained_mask
    qual = population & (~censored)
    return _measure(
        ohlc, entry_idx, entry_close, rd, atr_entry, c2, qual,
        int(retained_mask.sum()), int(population.sum()),
        int((population & censored).sum()), rng)


# --------------------------------------------------------------------------- #
# Pure computation — P13 baselines (matched-count random; MA segmentation)
# --------------------------------------------------------------------------- #
def matched_random_arm(
    ohlc: dict[str, np.ndarray], state_all: Any, atr_all: np.ndarray,
    confirm_idx: np.ndarray, signal_entry_idx: np.ndarray, draw_count: int,
    rng_draw: np.random.Generator, rng_boot: np.random.Generator,
) -> tuple[AvailResult, int]:
    """Matched-count random control over the eligible non-signal in-progress pool.

    Eligible bars: valid in-progress, ``M_sofar>0``, finite positive ATR, and not
    a binding ``/STRONG-STAT`` retained-signal bar. Each drawn bar takes its
    in-progress ``rd`` and is measured over **its own** end-of-M_b window (the 2nd
    confirmation at/after the bar). Direction is not random. Returns
    ``(AvailResult, pool_size)``. Mirrors the EXP-053 matched-random construction
    (P13 "matched-count random timestamps, same cell/regime via in-progress rd"),
    measured through the identical lifetime window.
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
    drawn = np.sort(rng_draw.choice(pool, size=k, replace=False))
    c2, censored = av.end_of_mb_window(drawn, confirm_idx)
    res = _measure(
        ohlc, drawn, ohlc["close"][drawn], state_all.rd[drawn], atr_all[drawn],
        c2, ~censored, k, k, int(censored.sum()), rng_boot)
    return res, int(pool.shape[0])


def ma_seg_arm(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, entry_epoch: np.ndarray,
    entry_close: np.ndarray, atr_entry: np.ndarray, rng: np.random.Generator,
) -> AvailResult:
    """MA(20,50)-segmentation baseline: conditioned haramis under MA-defined M_b."""
    seg = ma_segment_moves(ohlc)
    if seg["confirm_epoch"].shape[0] == 0:
        return _empty_arm()
    state = live_in_progress_state(entry_epoch, entry_close, seg["confirm_epoch"],
                                   seg["end_price"], seg["end_epoch"], seg["direction"])
    stat = live_strong_stat(state.k, state.m_sofar, seg["magnitude"])
    buildable = (state.valid & (state.m_sofar > 0.0) & np.isfinite(atr_entry)
                 & (atr_entry > 0.0))
    c2, censored = av.end_of_mb_window(entry_idx, seg["confirm_idx"])
    return avail_arm(ohlc, entry_idx, entry_close, state.rd, atr_entry, c2,
                     censored, stat["retained_p75"], buildable, rng)


def _rng(cell_index: int, purpose: int) -> np.random.Generator:
    """Deterministic, independent per-cell-per-purpose RNG (reproducible)."""
    return np.random.default_rng([BASE_SEED, cell_index, purpose])


def population_digest(
    entry_idx: np.ndarray, entry_epoch: np.ndarray, rd: np.ndarray, mask: np.ndarray,
) -> dict[str, Any]:
    """Per-cell event digest: count + a stable hash of (trigger_idx, time, rd).

    Identifies the *composition* of a conditioned population — not just its size
    — so the EXP-053 reconciliation (and the determinism replay) can detect two
    populations with equal counts but different event membership/timing/direction.
    Events are taken in ascending entry order (``mask`` preserves it); the hash is
    over the concatenated ``int64`` ``entry_idx``, ``entry_epoch``, and ``rd`` of
    the masked events, so it is deterministic and reproducible.
    """
    sel = np.flatnonzero(mask)
    if sel.size == 0:
        return {"n": 0, "digest": None}
    payload = np.concatenate([
        entry_idx[sel].astype(np.int64), entry_epoch[sel].astype(np.int64),
        rd[sel].astype(np.int64)]).tobytes()
    return {"n": int(sel.size), "digest": hashlib.sha1(payload).hexdigest()}


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
        return {**base, "empty": True, "n_retained": 0}

    entry_close = ohlc["close"][entry_idx]
    state = live_in_progress_state(entry_epoch, entry_close, mv["confirm_epoch"],
                                   mv["end_price"], mv["end_epoch"], mv["direction"])
    atr_entry = atr[entry_idx]
    buildable = (state.valid & (state.m_sofar > 0.0) & np.isfinite(atr_entry)
                 & (atr_entry > 0.0))
    c2, censored = av.end_of_mb_window(entry_idx, mv["confirm_idx"])
    stat = live_strong_stat(state.k, state.m_sofar, mv["magnitude"])
    ha_ret = strong_ha_retention(ha_ann, entry_epoch, state.start_epoch,
                                 -state.rd, state.valid)

    def arm(mask: np.ndarray, purpose: int) -> AvailResult:
        return avail_arm(ohlc, entry_idx, entry_close, state.rd, atr_entry, c2,
                         censored, mask, buildable, _rng(cell_index, purpose))

    arms = {
        "signal_stat": arm(stat["retained_p75"], RNG_STAT),
        "signal_ha": arm(ha_ret["same"], RNG_HA),
        "signal_stat_mad": arm(stat["retained_mad"], RNG_STATMAD),
        "signal_ha_any": arm(ha_ret["any"], RNG_HAANY),
    }
    baselines = _resolve_baselines(ohlc, mv, entry_idx, entry_epoch, entry_close,
                                   atr, atr_entry, buildable, stat["retained_p75"],
                                   arms["signal_stat"], cell_index)
    qual_stat = buildable & stat["retained_p75"] & (~censored)
    window_ok = av.window_invariants_ok(
        entry_idx, c2, mv["confirm_idx"], qual_stat, int(bars.height))
    stat_digest = population_digest(entry_idx, entry_epoch, state.rd,
                                    stat["retained_p75"])
    return {**base, "empty": False, "arms": arms,
            "n_retained": int(stat["retained_p75"].sum()),
            "n_censored_buildable": int((buildable & censored).sum()),
            "window_invariants_ok": window_ok, "stat_digest": stat_digest,
            **baselines}


def _resolve_baselines(
    ohlc: dict[str, np.ndarray], mv: dict[str, np.ndarray], entry_idx: np.ndarray,
    entry_epoch: np.ndarray, entry_close: np.ndarray, atr: np.ndarray,
    atr_entry: np.ndarray, buildable: np.ndarray, stat_retained: np.ndarray,
    signal: AvailResult, cell_index: int,
) -> dict[str, Any]:
    """P13 matched-random + MA-segmentation baselines and signal-baseline contrasts."""
    bar_epoch = ohlc["epoch"]
    state_all = live_in_progress_state(bar_epoch, ohlc["close"], mv["confirm_epoch"],
                                       mv["end_price"], mv["end_epoch"], mv["direction"])
    rand, pool_size = matched_random_arm(
        ohlc, state_all, atr, mv["confirm_idx"], entry_idx[buildable & stat_retained],
        signal.m, _rng(cell_index, RNG_RAND_DRAW), _rng(cell_index, RNG_RAND_BOOT))
    ma = ma_seg_arm(ohlc, entry_idx, entry_epoch, entry_close, atr_entry,
                    _rng(cell_index, RNG_MASEG))
    contrast_random = av.median_diff_block_bootstrap(
        signal.mfe, rand.mfe, _rng(cell_index, RNG_CONTRAST_RAND))
    contrast_ma = av.median_diff_block_bootstrap(
        signal.mfe, ma.mfe, _rng(cell_index, RNG_CONTRAST_MA))
    return {"matched_random": rand, "ma_seg": ma, "random_pool_size": pool_size,
            "contrast_random": contrast_random, "contrast_ma": contrast_ma}


# --------------------------------------------------------------------------- #
# Per-cell record flattening + availability classification
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
    sig = cell["arms"]["signal_stat"]
    rec["n_censored_buildable"] = cell["n_censored_buildable"]
    rec["random_pool_size"] = cell["random_pool_size"]
    rec.update(_arm_fields(sig, "stat"))
    rec.update(_arm_fields(cell["arms"]["signal_ha"], "ha"))
    rec.update(_arm_fields(cell["arms"]["signal_stat_mad"], "statmad"))
    rec.update(_arm_fields(cell["arms"]["signal_ha_any"], "haany"))
    rec.update(_arm_fields(cell["matched_random"], "rand"))
    rec.update(_arm_fields(cell["ma_seg"], "maseg"))
    rec["contrast_random_low"] = cell["contrast_random"][1]
    rec["contrast_ma_low"] = cell["contrast_ma"][1]
    rec["censored_fraction"] = (
        sig.n_censored / sig.n_buildable if sig.n_buildable else None)
    _classify_cell(rec, sig, cell["contrast_random"][1], cell["contrast_ma"][1],
                   cell["matched_random"], cell["ma_seg"])
    return rec


def _classify_cell(
    rec: dict[str, Any], sig: AvailResult, contrast_random_low: float,
    contrast_ma_low: float, rand: AvailResult, ma: AvailResult,
) -> None:
    """Set per-cell MOVE_AVAILABLE, reference multiples, and status code."""
    available = av.move_available(sig.m, sig.mfe_ci_low_1s, sig.median_mfe, sig.median_mae)
    rec["powered"] = sig.m >= POWER_FLOOR
    rec["move_available"] = bool(available)
    rec["mfe_mult_ref_lo"] = (
        sig.median_mfe / av.REF_LINES[0] if sig.median_mfe is not None else None)
    rec["mfe_mult_ref_hi"] = (
        sig.median_mfe / av.REF_LINES[1] if sig.median_mfe is not None else None)
    rec["mfe_gt_mae"] = bool(
        sig.median_mfe is not None and sig.median_mae is not None
        and sig.median_mfe > sig.median_mae)
    rec["beats_random_mfe"] = _beats(rand, contrast_random_low)
    rec["beats_ma_mfe"] = _beats(ma, contrast_ma_low)
    status = av.availability_status(sig.m, available)
    rec["availability_status"] = status
    rec["status_code"] = ASTATUS_CODES[status]


def _beats(baseline: AvailResult, contrast_low: float) -> bool:
    """Signal exceeds a baseline's availability iff baseline unpowered, or CI>0.

    Disclosed-secondary contrast only; never a binding MOVE_AVAILABLE leg.
    """
    if baseline.m < POWER_FLOOR:
        return True
    return contrast_low is not None and np.isfinite(contrast_low) and contrast_low > 0.0


def _arm_fields(a: AvailResult, prefix: str) -> dict[str, Any]:
    """Flatten one AvailResult into per-cell columns (no per-event arrays)."""
    return {
        f"{prefix}_m": a.m, f"{prefix}_median_mfe": a.median_mfe,
        f"{prefix}_mfe_ci_low_1s": a.mfe_ci_low_1s, f"{prefix}_mfe_ci_lo_2s": a.mfe_ci_lo_2s,
        f"{prefix}_mfe_ci_hi_2s": a.mfe_ci_hi_2s, f"{prefix}_median_mae": a.median_mae,
        f"{prefix}_mae_ci_low_1s": a.mae_ci_low_1s, f"{prefix}_mae_ci_lo_2s": a.mae_ci_lo_2s,
        f"{prefix}_mae_ci_hi_2s": a.mae_ci_hi_2s, f"{prefix}_mean_mfe": a.mean_mfe,
        f"{prefix}_mean_mae": a.mean_mae, f"{prefix}_n_retained": a.n_retained,
        f"{prefix}_n_buildable": a.n_buildable, f"{prefix}_n_censored": a.n_censored,
        f"{prefix}_block_len": a.block_len,
    }


def _empty_metric_fields() -> dict[str, Any]:
    """Metric columns for a member cell with no harami/move population."""
    rec: dict[str, Any] = {
        "n_censored_buildable": 0, "random_pool_size": 0, "censored_fraction": None,
        "powered": False, "move_available": False, "mfe_mult_ref_lo": None,
        "mfe_mult_ref_hi": None, "mfe_gt_mae": False, "beats_random_mfe": False,
        "beats_ma_mfe": False, "availability_status": "NOT_VIABLE_BY_POWER",
        "status_code": ASTATUS_CODES["NOT_VIABLE_BY_POWER"],
        "contrast_random_low": None, "contrast_ma_low": None,
    }
    for prefix in ("stat", "ha", "statmad", "haany", "rand", "maseg"):
        rec.update(_arm_fields(_empty_arm(), prefix))
    return rec


def excluded_record(instrument: str, domain: str) -> dict[str, Any]:
    """Record for a COVERAGE_EXCLUDED cell (not in the EXP-049 member grid)."""
    rec: dict[str, Any] = {
        "instrument": instrument, "domain": domain, "member": False, "excluded": True,
        "n_bars": None, "n_moves": None, "n_harami": None, "n_retained": None}
    rec.update(_empty_metric_fields())
    rec["availability_status"], rec["status_code"] = "EXCLUDED", ASTATUS_CODES["EXCLUDED"]
    return rec


# --------------------------------------------------------------------------- #
# Composition + determinism replay + EXP-053 reconciliation (DEFECT guards)
# --------------------------------------------------------------------------- #
def composition_readout(records: list[dict[str, Any]], defect: dict[str, Any]) -> dict[str, Any]:
    """P11 composition tallies + the mechanical AVAILABILITY_* fork."""
    members = [r for r in records if r["member"]]
    available = [r for r in members if r["move_available"]]
    powered = [r for r in members if r["powered"]]
    readout = av.composition_fork(available, powered, defect["is_defect"])
    readout["beats_both_mfe"] = {
        "cells": [f"{r['instrument']}-{r['domain']}" for r in available
                  if r["beats_random_mfe"] and r["beats_ma_mfe"]],
    }
    readout["defect"] = defect
    return readout


_ARM_SCALARS = (
    "m", "median_mfe", "mfe_ci_low_1s", "mfe_ci_lo_2s", "mfe_ci_hi_2s",
    "median_mae", "mae_ci_low_1s", "mae_ci_lo_2s", "mae_ci_hi_2s", "mean_mfe",
    "mean_mae", "n_retained", "n_buildable", "n_censored", "block_len")
_ALL_ARMS = ("signal_stat", "signal_ha", "signal_stat_mad", "signal_ha_any")


def _eq(a: Any, b: Any) -> bool:
    """NaN/None-aware scalar equality (CIs are None when unpowered, NaN on <2)."""
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, float) and isinstance(b, float) and (np.isnan(a) or np.isnan(b)):
        return np.isnan(a) and np.isnan(b)
    return bool(a == b)


def _arm_identical(x: AvailResult, y: AvailResult) -> bool:
    """Per-event arrays + every scalar field of one arm reproduce exactly."""
    if not (np.array_equal(x.mfe, y.mfe) and np.array_equal(x.mae, y.mae)):
        return False
    return all(_eq(getattr(x, f), getattr(y, f)) for f in _ARM_SCALARS)


def cells_identical(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """All binding + disclosed arms, both baseline contrasts, and the population
    digest reproduce frame-identically (scope §Correctness-Gates determinism)."""
    if a.get("empty") or b.get("empty"):
        return a.get("empty") == b.get("empty")
    for arm in _ALL_ARMS:
        if not _arm_identical(a["arms"][arm], b["arms"][arm]):
            return False
    if not (_arm_identical(a["matched_random"], b["matched_random"])
            and _arm_identical(a["ma_seg"], b["ma_seg"])):
        return False
    for key in ("contrast_random", "contrast_ma"):
        if not all(_eq(p, q) for p, q in zip(a[key], b[key])):
            return False
    return a.get("stat_digest") == b.get("stat_digest")


def determinism_replay(train_1m: pl.DataFrame, domain: str, train_end_epoch: int,
                       cell_index: int, reference: dict[str, Any]) -> bool:
    """Re-run one cell end-to-end and assert it reproduces ``reference`` exactly.

    Compares against the already-computed cell (one extra compute per cell) over
    all arms, both contrasts, and the population digest — covering the scope's
    "every per-cell figure" determinism gate at modest extra cost.
    """
    replay = compute_cell(train_1m, domain, train_end_epoch, cell_index)
    return cells_identical(reference, replay)


def causality_ok(cell: dict[str, Any]) -> bool:
    """Scope §Correctness-Gates window invariants on the binding arm.

    Asserts ``MFE,MAE >= 0`` (finite) on the qualifying events AND the
    window-ordering/fence invariants (``entry+1 <= c2 <= train_last_idx``,
    ``c2 == confirm_idx[pos+1]`` with ``confirm_idx[pos] > entry``) computed in
    :func:`compute_cell` via :func:`availability.window_invariants_ok`.
    """
    if cell.get("empty"):
        return True
    if not cell.get("window_invariants_ok", True):
        return False
    sig = cell["arms"]["signal_stat"]
    if sig.m == 0:
        return True
    return bool(np.all(sig.mfe >= 0.0) and np.all(sig.mae >= 0.0)
                and np.all(np.isfinite(sig.mfe)) and np.all(np.isfinite(sig.mae)))


def load_exp053_population() -> dict[tuple[str, str], dict[str, int]] | None:
    """EXP-053 per-cell conditioned-population counts (reconciliation anchor)."""
    path = EXP053_RESULTS / "outcome_primary.csv"
    if not path.exists():
        return None
    df = pl.read_csv(path, infer_schema_length=10_000)
    out: dict[tuple[str, str], dict[str, int]] = {}
    for r in df.to_dicts():
        if not r.get("member"):
            continue
        out[(r["instrument"], r["domain"])] = {
            "n_harami": r.get("n_harami"), "stat_retained": r.get("stat_retained")}
    return out


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
            if isinstance(val, (int, float)) and val is not None:
                matrix[i, j] = float(val)
    return matrix


def plot_forest(records: list[dict[str, Any]], save_path: Path) -> None:
    """Per-cell median MFE & MAE with one-sided CI whiskers + reference band."""
    rows = sorted([r for r in records if r["member"] and r["stat_median_mfe"] is not None],
                  key=lambda r: r["stat_median_mfe"])
    if not rows:
        _placeholder(save_path, "no powered cells")
        return
    labels = [f"{r['instrument']}-{r['domain']}" for r in rows]
    mfe = np.array([r["stat_median_mfe"] for r in rows])
    mfe_low = np.array([r["stat_mfe_ci_low_1s"] if r["stat_mfe_ci_low_1s"] is not None
                        else np.nan for r in rows])
    mae = np.array([r["stat_median_mae"] if r["stat_median_mae"] is not None
                    else np.nan for r in rows])
    y = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(8, max(4, 0.28 * len(labels))))
    colours = ["#1a9850" if r["move_available"] else "#999999" for r in rows]
    ax.hlines(y, np.minimum(mfe_low, mfe), mfe, color=colours, alpha=0.7, zorder=2)
    ax.scatter(mfe, y, color=colours, s=26, zorder=3, label="median MFE (CI_low whisker)")
    ax.scatter(mae, y, color="#d73027", marker="x", s=20, label="median MAE")
    for ref, ls in zip(av.REF_LINES, (":", "--")):
        ax.axvline(ref, color="k", lw=0.8, ls=ls, label=f"{ref:g}x ATR ref")
    ax.set_yticks(y, labels, fontsize=5)
    ax.set_xlabel("lifetime excursion (ATR units, gross)")
    ax.set_title(f"{EXPERIMENT_ID}: per-cell lifetime MFE/MAE (binding /STRONG-STAT)")
    ax.legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_asymmetry_heatmap(records: list[dict[str, Any]], save_path: Path) -> None:
    """Median (MFE - MAE) asymmetry heatmap (instrument x domain)."""
    domains = list(DOMAINS.keys())
    matrix = np.full((len(INSTRUMENTS), len(domains)), np.nan)
    for i, inst in enumerate(INSTRUMENTS):
        for j, dom in enumerate(domains):
            rec = next((r for r in records if r["instrument"] == inst
                        and r["domain"] == dom), None)
            if rec and rec.get("stat_median_mfe") is not None \
                    and rec.get("stat_median_mae") is not None:
                matrix[i, j] = rec["stat_median_mfe"] - rec["stat_median_mae"]
    fig, ax = plt.subplots(figsize=(7, 9))
    sns.heatmap(matrix, ax=ax, cmap="RdBu", center=0.0, annot=False,
                xticklabels=domains, yticklabels=INSTRUMENTS,
                cbar_kws={"label": "median (MFE - MAE), ATR units"})
    ax.set_title(f"{EXPERIMENT_ID}: favourable-availability asymmetry (binding /STRONG-STAT)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_pooled_distributions(pooled: dict[str, list[float]], save_path: Path) -> None:
    """Pooled per-event MFE/MAE distributions (powered cells) + reference band."""
    mfe = np.asarray(pooled.get("mfe", []))
    mae = np.asarray(pooled.get("mae", []))
    if mfe.size == 0:
        _placeholder(save_path, "no powered-cell events to pool")
        return
    hi = float(np.percentile(np.concatenate([mfe, mae]), 99)) if mae.size else float(mfe.max())
    bins = np.linspace(0.0, max(hi, av.REF_LINES[1] * 1.5), 60)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(mfe, bins=bins, alpha=0.55, color="#1a9850", label=f"MFE (n={mfe.size:,})")
    if mae.size:
        ax.hist(mae, bins=bins, alpha=0.55, color="#d73027", label=f"MAE (n={mae.size:,})")
    ax.axvline(float(np.median(mfe)), color="#1a9850", lw=1.2, ls="-", label="median MFE")
    if mae.size:
        ax.axvline(float(np.median(mae)), color="#d73027", lw=1.2, ls="-", label="median MAE")
    for ref, ls in zip(av.REF_LINES, (":", "--")):
        ax.axvline(ref, color="k", lw=0.9, ls=ls, label=f"{ref:g}x ATR ref")
    ax.set_xlabel("lifetime excursion (ATR units, gross)")
    ax.set_ylabel("events")
    ax.set_title(f"{EXPERIMENT_ID}: pooled lifetime excursions (powered cells)")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_status_heatmap(records: list[dict[str, Any]], save_path: Path) -> None:
    """MOVE_AVAILABLE / P11 composition status map (instrument x domain)."""
    matrix = _matrix(records, "status_code")
    cmap = ListedColormap(ASTATUS_COLORS)
    norm = BoundaryNorm(np.arange(-0.5, len(ASTATUS_COLORS) + 0.5), cmap.N)
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
    ax.set_title(f"{EXPERIMENT_ID}: availability status (annotated: qualifying m)")
    handles = [plt.Rectangle((0, 0), 1, 1, color=ASTATUS_COLORS[c])
               for c in ASTATUS_CODES.values()]
    ax.legend(handles, list(ASTATUS_CODES.keys()), bbox_to_anchor=(1.02, 1),
              loc="upper left", fontsize=8)
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
    plot_forest(records, PLOTS_DIR / "per_cell_mfe_mae_forest.png")
    plot_asymmetry_heatmap(records, PLOTS_DIR / "mfe_mae_asymmetry_heatmap.png")
    plot_pooled_distributions(pooled, PLOTS_DIR / "pooled_excursion_distributions.png")
    plot_status_heatmap(records, PLOTS_DIR / "move_available_composition_map.png")


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _cell_index_map() -> dict[tuple[str, str], int]:
    return {(inst, dom): i for i, (inst, dom) in enumerate(
        (inst, dom) for inst in INSTRUMENTS for dom in DOMAINS)}


def _collect_pooled(cell: dict[str, Any], rec: dict[str, Any],
                    pooled: dict[str, list[float]]) -> None:
    """Pool per-event MFE/MAE from a powered cell for the distribution plot."""
    if cell.get("empty") or not rec["powered"]:
        return
    sig = cell["arms"]["signal_stat"]
    pooled["mfe"].extend(sig.mfe.tolist())
    pooled["mae"].extend(sig.mae.tolist())


def run() -> dict[str, Any]:
    """Run all member cells and write artifacts. Returns the run summary."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    cell_index = _cell_index_map()
    exp053 = load_exp053_population()
    records: list[dict[str, Any]] = []
    recon_rows: list[dict[str, Any]] = []
    pooled: dict[str, list[float]] = {"mfe": [], "mae": []}
    instrument_meta: dict[str, Any] = {}
    defect = {"is_defect": False, "non_deterministic": [], "causality": [],
              "reconciliation_mismatch": []}

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
            recon_rows.append(_reconcile(instrument, domain, cell, exp053, defect))
            _guard_cell(train_1m, domain, meta, ci, cell, defect, instrument)
        del train_1m

    readout = composition_readout(records, defect)
    write_outputs(records, recon_rows, readout, pooled, instrument_meta, defect, exp053)
    make_plots(records, pooled)
    return _summarize(records, readout)


def _reconcile(instrument: str, domain: str, cell: dict[str, Any],
               exp053: dict | None, defect: dict[str, Any]) -> dict[str, Any]:
    """Reconcile EXP-055 conditioned-population counts against EXP-053."""
    ours_harami = cell.get("n_harami")
    ours_retained = cell.get("n_retained")
    digest = cell.get("stat_digest") or {"n": None, "digest": None}
    row = {"instrument": instrument, "domain": domain, "ours_n_harami": ours_harami,
           "ours_n_retained": ours_retained, "ours_stat_digest_n": digest["n"],
           "ours_stat_digest": digest["digest"], "exp053_available": exp053 is not None}
    if exp053 is None or (instrument, domain) not in exp053:
        row.update({"theirs_n_harami": None, "theirs_stat_retained": None,
                    "theirs_stat_digest": None, "match": None})
        return row
    theirs = exp053[(instrument, domain)]
    match = (ours_harami == theirs["n_harami"] and ours_retained == theirs["stat_retained"])
    # EXP-053 persisted per-cell counts only (no per-event digest), so the cross-
    # experiment leg matches on counts; the EXP-055 self-digest is recorded for
    # provenance and is verified frame-identical by the determinism replay.
    row.update({"theirs_n_harami": theirs["n_harami"],
                "theirs_stat_retained": theirs["stat_retained"],
                "theirs_stat_digest": None, "match": bool(match)})
    if not match:
        defect["reconciliation_mismatch"].append(f"{instrument}-{domain}")
        defect["is_defect"] = True
    return row


def _guard_cell(
    train_1m: pl.DataFrame, domain: str, meta: dict[str, Any], cell_index: int,
    cell: dict[str, Any], defect: dict[str, Any], instrument: str,
) -> None:
    """Determinism replay + causality/window-invariant check on **every** cell.

    The scope §Correctness-Gates require "every per-cell figure" to reproduce
    frame-identically, so every computed cell is replayed once and compared
    against its live result (all arms + contrasts + digest). Causality/window
    invariants are checked on every cell too.
    """
    tag = f"{instrument}-{domain}#{cell_index}"
    if not determinism_replay(train_1m, domain, meta["train_end_epoch_s"],
                              cell_index, cell):
        defect["non_deterministic"].append(tag)
        defect["is_defect"] = True
    if not causality_ok(cell):
        defect["causality"].append(tag)
        defect["is_defect"] = True


def write_outputs(
    records: list[dict[str, Any]], recon_rows: list[dict[str, Any]],
    readout: dict[str, Any], pooled: dict[str, list[float]],
    instrument_meta: dict[str, Any], defect: dict[str, Any], exp053: dict | None,
) -> None:
    """Persist per-cell parquet/CSV, the secondary CSV, recon CSV, and the JSONs."""
    df = pl.DataFrame(records, strict=False)
    df.write_parquet(RESULTS_DIR / "per_cell_availability.parquet")
    binding_cols = [
        "instrument", "domain", "member", "excluded", "n_harami", "n_retained",
        "stat_m", "stat_median_mfe", "stat_mfe_ci_low_1s", "stat_median_mae",
        "stat_mae_ci_low_1s", "mfe_mult_ref_lo", "mfe_mult_ref_hi", "mfe_gt_mae",
        "censored_fraction", "powered", "move_available", "availability_status"]
    df.select([c for c in binding_cols if c in df.columns]).write_csv(
        RESULTS_DIR / "availability_map.csv")
    secondary_cols = [
        "instrument", "domain", "ha_m", "ha_median_mfe", "ha_mfe_ci_low_1s",
        "statmad_m", "statmad_median_mfe", "statmad_mfe_ci_low_1s",
        "rand_m", "rand_median_mfe", "rand_mfe_ci_low_1s",
        "maseg_m", "maseg_median_mfe", "maseg_mfe_ci_low_1s",
        "contrast_random_low", "contrast_ma_low", "beats_random_mfe", "beats_ma_mfe",
        "stat_n_retained", "stat_n_buildable", "stat_n_censored", "random_pool_size"]
    df.select([c for c in secondary_cols if c in df.columns]).write_csv(
        RESULTS_DIR / "availability_secondary.csv")
    pl.DataFrame(recon_rows, strict=False).write_csv(
        RESULTS_DIR / "population_reconciliation.csv")

    with open(RESULTS_DIR / "composition_readout.json", "w") as fh:
        json.dump(readout, fh, indent=2, default=str)
    _write_metadata(instrument_meta, defect, exp053, pooled)


def _write_metadata(instrument_meta: dict[str, Any], defect: dict[str, Any],
                    exp053: dict | None, pooled: dict[str, list[float]]) -> None:
    """Persist the frozen-constants / provenance metadata JSON."""
    meta = {
        "experiment_id": EXPERIMENT_ID,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "014-B", "hypothesis": "HYP-008", "family": "CF-HA-HARAMI-001",
        "stratum": "TRAIN-only (first 49%); nested TEST + final-30% holdout sealed",
        "object": "live /STRONG-STAT-conditioned HA harami (identical to EXP-053)",
        "entry_anchor": "harami confirmation-bar real close (live, pre-ZigZag-confirm)",
        "lifetime_window": ("[entry+1, c2] where c2 = 2nd confirmed ZigZag pivot "
                            "at/after the harami (end of reversal move M_b); fewer "
                            "than 2 confirmations before TRAIN edge -> DATA_CENSORED"),
        "metrics": "ATR-normalised lifetime favourable MFE / adverse MAE (gross, real prices)",
        "reference_band": {"lines_atr": list(av.REF_LINES),
                           "use": "comparison/reporting yardstick only; never subtracted"},
        "binding_leg": ("MOVE_AVAILABLE iff m>=30 AND median-MFE CI_low(1s)>1.0 ATR "
                        "AND median_MFE>median_MAE"),
        "params": {
            "atr_period": ATR_PERIOD, "atr_mult": ATR_MULT, "stat_window": 20,
            "stat_min_window": 5, "stat_q": 0.75, "ha_run_len": 3,
            "ma_segmentation": [MA_FAST, MA_SLOW], "power_floor": POWER_FLOOR,
            "n_boot": av.N_BOOT, "boot_batch": av.BOOT_BATCH, "base_seed": BASE_SEED,
            "p11": [av.P11_MIN_CELLS, av.P11_MIN_INSTR],
        },
        "baselines": ["matched-count random (in-progress rd, non-signal pool)",
                      "MA(20,50)-crossover segmentation through the identical window"],
        "pooled_event_counts": {"mfe": len(pooled["mfe"]), "mae": len(pooled["mae"])},
        "determinism_ok": not defect["non_deterministic"],
        "determinism_coverage": ("every member cell replayed once and compared "
                                 "frame-identically across all arms, both baseline "
                                 "contrasts, and the per-cell population digest"),
        "causality_ok": not defect["causality"],
        "causality_coverage": ("MFE,MAE>=0 (finite) AND window invariants "
                               "entry+1<=c2<=train_last_idx, c2==confirm_idx[pos+1] "
                               "with confirm_idx[pos]>entry, on every cell's binding arm"),
        "reconciliation_against": str(EXP053_RESULTS / "outcome_primary.csv"),
        "reconciliation_available": exp053 is not None,
        "reconciliation_mismatch": defect["reconciliation_mismatch"],
        "reconciliation_note": ("EXP-055 records a per-cell (trigger_idx,time,rd) "
                                "digest of the binding /STRONG-STAT population, "
                                "verified frame-identical by the determinism replay. "
                                "EXP-053 persisted per-cell counts only (no per-event "
                                "digest), so the cross-experiment leg matches on "
                                "counts; a direct per-event cross-match requires "
                                "EXP-053 to re-export the same digest."),
        "is_defect": defect["is_defect"],
        "de30_disclosure": DE30_DISCLOSURE,
        "holdout_fence": ("Only Parquet metadata + first train_rows file-order rows read "
                          "per instrument; full file never sorted/collected; every domain "
                          "bar fenced to CloseTime <= train_end_ts; excursion windows end "
                          "at the M_b pivot inside TRAIN (censored otherwise); TEST and "
                          "final-30% holdout never read."),
        "registry": ("CF-HA-HARAMI-001/HYP-008; 0 candidate slots, 0 TEST reads; "
                     "characterization readout feeds the single 014-B G2."),
        "instrument_meta": instrument_meta,
    }
    with open(RESULTS_DIR / "run_metadata.json", "w") as fh:
        json.dump(meta, fh, indent=2, default=str)


def _summarize(records: list[dict[str, Any]], readout: dict[str, Any]) -> dict[str, Any]:
    """Concise stdout summary."""
    status_counts: dict[str, int] = {}
    for r in records:
        s = r["availability_status"]
        status_counts[s] = status_counts.get(s, 0) + 1
    return {"verdict": readout["verdict"], "status_counts": status_counts,
            "move_available": readout["move_available"], "powered": readout["powered"],
            "defect": readout["defect"]}


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    summary = run()
    LOGGER.info("\n=== %s complete ===", EXPERIMENT_ID)
    LOGGER.info("verdict: %s", summary["verdict"])
    LOGGER.info("availability status counts: %s", json.dumps(summary["status_counts"]))
    LOGGER.info("MOVE_AVAILABLE: %s cells over %s instruments (P11=%s)",
                summary["move_available"]["n_cells"],
                summary["move_available"]["n_instruments"],
                summary["move_available"]["composition_met"])
    LOGGER.info("powered cells: %s over %s instruments (quorum_formable=%s)",
                summary["powered"]["n_cells"], summary["powered"]["n_instruments"],
                summary["powered"]["quorum_formable"])
    if summary["defect"]["is_defect"]:
        LOGGER.info("DEFECT: %s", json.dumps(summary["defect"], default=str))
    LOGGER.info("artifacts -> %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
