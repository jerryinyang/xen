"""
Experiment EXP-033: 15-Minute IFVG Rule Family Readiness Survey
Implements the analysis plan from analysis-plan.md.

Evaluates five predeclared rule families against six readiness checks on all
four instruments at 15-minute resolution:

- R1 Stricter size: minimum FVG size raised to max(precision_step, 0.10 * ATR).
- R2 Shorter lifecycle: 24 15-minute bars instead of the 120-bar baseline.
- R3 Displacement-qualified FVG creation: the third FVG candle must satisfy
  the EXP-018 displacement rule (BodySize >= 1.5 * BodyMedian100Prior with
  side-specific close-location threshold).
- R4 Mitigation-before-inversion: a candidate IFVG inversion is valid only if
  at least one earlier bar entered or touched the gap.
- R5 Zone-location filter: a baseline FVG is eligible only if a 15-minute
  first-touch sweep of PDH/PDL/ONH/ONL occurred within the prior 24 bars and
  the FVG midpoint lies within 1.0 * ATR of the swept level.

The experiment is readiness-only: no returns, excursions, hit rates, or P&L
statistics are computed, and selection between qualifying rules cannot depend
on any such metric.
"""
import hashlib
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl
import seaborn as sns

PYTHON_ROOT = Path(__file__).resolve().parents[3]
PROJECT_ROOT = PYTHON_ROOT.parent
SRC_DIR = PYTHON_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from bar_aggregator import aggregate_ohlc  # noqa: E402
from ict_timebar import (  # noqa: E402
    INSTRUMENTS,
    add_ny_time_features,
    compute_liquidity_levels,
    compute_price_precision_step,
    load_analysis_timebars,
    train_cutoff_time,
)


LOGGER = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-033"
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"

# ── Predeclared constants (frozen by scope.md) ────────────────────────────────

PERIOD_MINUTES = 15
ATR_PERIOD = 14
ANALYSIS_TRAIN_FRACTION = 0.70

BASELINE_LIFECYCLE_BARS = 120
BASELINE_SIZE_ATR_COEFF = 0.02

R1_SIZE_ATR_COEFF = 0.10
R2_LIFECYCLE_BARS = 24
R3_BODY_WINDOW = 100
R3_BODY_MULTIPLE = 1.5
R3_LOWER_CLOSE_QUARTILE = 0.25
R3_UPPER_CLOSE_QUARTILE = 0.75
R5_SWEEP_LOOKBACK_BARS = 24
R5_ZONE_ATR_COEFF = 1.0

SWEEP_BUFFER_ATR_COEFF = 0.05
ON_LEVEL_MIN_MINUTE = 9 * 60 + 30

MIN_FVG_PER_SEGMENT = 100
MIN_IFVG_PER_SEGMENT = 50
INVERSION_BAND_LOW = 0.55
INVERSION_BAND_HIGH = 0.75
SELECTIVITY_MAX_RETENTION = 0.80
MAX_MEDIAN_DELAY_BARS = 24

BOOTSTRAP_REPS = 2_000
BOOTSTRAP_BLOCK = 50
BOOTSTRAP_SEED = 42
REPRODUCIBILITY_SHUFFLE_SEED = 42

QUALIFYING_INSTRUMENT_FLOOR = 2
TIE_BREAK_EPSILON = 1e-6

LEVEL_TYPES_HIGH = ("PDH", "ONH")
LEVEL_TYPES_LOW = ("PDL", "ONL")
LEVEL_TYPES = LEVEL_TYPES_HIGH + LEVEL_TYPES_LOW

RULE_NAMES = ("R1", "R2", "R3", "R4", "R5")
RULE_LABELS = {
    "R1": "Stricter size",
    "R2": "Shorter lifecycle",
    "R3": "Displacement-qualified",
    "R4": "Mitigation-before-inversion",
    "R5": "Zone-location",
}
SEGMENTS = ("Train", "Test")

FVG_KEY_COLS = [
    "Instrument",
    "Segment",
    "Side",
    "CreationTime",
    "LowerBound",
    "UpperBound",
    "FVGSize",
]
IFVG_KEY_COLS = FVG_KEY_COLS + ["InversionTime"]


@dataclass(frozen=True)
class PreparedBars15m:
    """Column arrays for a holdout-excluded 15-minute analysis frame."""

    close_times: np.ndarray
    opens: np.ndarray
    highs: np.ndarray
    lows: np.ndarray
    closes: np.ndarray
    segments: np.ndarray
    atr14_prior: np.ndarray
    body_size: np.ndarray
    close_location: np.ndarray
    body_median_prior: np.ndarray
    ny_date: np.ndarray
    ny_minute: np.ndarray

    def __len__(self) -> int:
        return len(self.close_times)


@dataclass(frozen=True)
class InstrumentContext:
    """Per-instrument detection inputs used by all rules."""

    instrument: str
    bars: PreparedBars15m
    precision_step: float
    levels: pd.DataFrame
    sweeps: pd.DataFrame


# ── 15-minute load / aggregation / feature pipeline ──────────────────────────


def _segment_label_expr(train_rows: int) -> pl.Expr:
    """Return a Polars expression labelling Train/Test by chronological row."""
    return (
        pl.when(pl.col("_Row") < train_rows)
        .then(pl.lit("Train"))
        .otherwise(pl.lit("Test"))
        .alias("Segment")
    )


def _add_atr_15m(frame_15m: pl.DataFrame) -> pl.DataFrame:
    """Add ATR14Prior using only completed prior bars."""
    prev_close = pl.col("Close").shift(1)
    true_range = pl.max_horizontal(
        pl.col("High") - pl.col("Low"),
        (pl.col("High") - prev_close).abs(),
        (pl.col("Low") - prev_close).abs(),
    ).fill_null(pl.col("High") - pl.col("Low"))
    return frame_15m.with_columns(true_range.alias("TrueRange")).with_columns(
        pl.col("TrueRange")
        .rolling_mean(window_size=ATR_PERIOD, min_samples=ATR_PERIOD)
        .shift(1)
        .alias("ATR14Prior")
    )


def _add_body_diagnostics_15m(frame_15m: pl.DataFrame) -> pl.DataFrame:
    """Add BodySize, CloseLocation, and BodyMedian100Prior for R3."""
    candle_range = pl.col("High") - pl.col("Low")
    return frame_15m.with_columns(
        (pl.col("Close") - pl.col("Open")).abs().alias("BodySize"),
        pl.when(candle_range > 0)
        .then((pl.col("Close") - pl.col("Low")) / candle_range)
        .otherwise(0.5)
        .alias("CloseLocation"),
    ).with_columns(
        pl.col("BodySize")
        .rolling_median(window_size=R3_BODY_WINDOW, min_samples=R3_BODY_WINDOW)
        .shift(1)
        .alias("BodyMedian100Prior")
    )


def _aggregate_to_15m_with_features(frame_1m: pl.DataFrame) -> pl.DataFrame:
    """Aggregate 1-minute bars to 15-minute and attach detection features."""
    aggregated = aggregate_ohlc(frame_1m, period_minutes=PERIOD_MINUTES)
    if aggregated.is_empty():
        return aggregated
    train_rows_15m = int(aggregated.height * ANALYSIS_TRAIN_FRACTION)
    segmented = aggregated.with_row_index("_Row").with_columns(
        _segment_label_expr(train_rows_15m)
    )
    with_atr = _add_atr_15m(segmented)
    with_body = _add_body_diagnostics_15m(with_atr)
    return with_body.drop("_Row")


def _prepare_bars_15m(frame_15m: pl.DataFrame) -> PreparedBars15m:
    """Convert a feature-loaded 15-minute Polars frame into numpy arrays."""
    if frame_15m.is_empty():
        empty_f = np.array([], dtype=float)
        empty_o = np.array([], dtype=object)
        empty_d = np.array([], dtype="datetime64[ns]")
        empty_i = np.array([], dtype=int)
        return PreparedBars15m(
            empty_d, empty_f, empty_f, empty_f, empty_f, empty_o,
            empty_f, empty_f, empty_f, empty_f, empty_o, empty_i,
        )
    pdf = frame_15m.to_pandas().reset_index(drop=True)
    close_ts = pd.to_datetime(pdf["CloseTime"])
    return PreparedBars15m(
        close_times=close_ts.to_numpy(),
        opens=pdf["Open"].to_numpy(dtype=float),
        highs=pdf["High"].to_numpy(dtype=float),
        lows=pdf["Low"].to_numpy(dtype=float),
        closes=pdf["Close"].to_numpy(dtype=float),
        segments=pdf["Segment"].to_numpy(),
        atr14_prior=pdf["ATR14Prior"].to_numpy(dtype=float),
        body_size=pdf["BodySize"].to_numpy(dtype=float),
        close_location=pdf["CloseLocation"].to_numpy(dtype=float),
        body_median_prior=pdf["BodyMedian100Prior"].to_numpy(dtype=float),
        ny_date=pdf["NYDate"].to_numpy(),
        ny_minute=pdf["NYMinuteOfDay"].to_numpy(dtype=np.int64),
    )


def _attach_ny_features(frame_15m: pl.DataFrame, train_end_time: Any) -> pl.DataFrame:
    """Add NYDate and NYMinuteOfDay; preserve the row-derived Segment."""
    with_ny = add_ny_time_features(frame_15m.drop("Segment"), train_end_time)
    return with_ny.with_columns(frame_15m["Segment"].alias("Segment"))


def _load_instrument_15m(
    instrument: str,
    *,
    shuffle_seed: int | None = None,
) -> tuple[PreparedBars15m, float]:
    """Load holdout-excluded 1m bars and produce a 15m PreparedBars frame.

    When ``shuffle_seed`` is set, the 1-minute analysis-set frame is permuted
    deterministically and re-sorted by CloseTime before aggregation. This
    probes the determinism of the full 1m -> 15m -> detection chain.
    """
    loaded = load_analysis_timebars(DATA_DIR, instrument)
    frame_1m = loaded.frame
    if shuffle_seed is not None and not frame_1m.is_empty():
        frame_1m = _shuffle_then_resort_1m(frame_1m, shuffle_seed)
    frame_15m = _aggregate_to_15m_with_features(frame_1m)
    if frame_15m.is_empty():
        return _prepare_bars_15m(frame_15m), 1e-5
    train_end_time = train_cutoff_time(
        frame_15m, int(frame_15m.height * ANALYSIS_TRAIN_FRACTION)
    )
    frame_15m = _attach_ny_features(frame_15m, train_end_time)
    precision_step = compute_price_precision_step(frame_15m)
    return _prepare_bars_15m(frame_15m), precision_step


def _shuffle_then_resort_1m(frame_1m: pl.DataFrame, seed: int) -> pl.DataFrame:
    """Permute 1-minute rows deterministically then restore canonical sort."""
    n = frame_1m.height
    rng = np.random.default_rng(seed)
    perm = rng.permutation(n)
    permuted = frame_1m.with_columns(
        pl.Series("_PermKey", perm.astype(np.int64))
    ).sort("_PermKey").drop("_PermKey")
    return permuted.sort("CloseTime")


# ── 15-minute liquidity levels and sweep detection ───────────────────────────


def _levels_for_instrument(
    frame_15m_ny: pl.DataFrame,
    instrument: str,
) -> pd.DataFrame:
    """Compute PDH/PDL/ONH/ONL per NYDate for one instrument from 15-minute bars."""
    levels = compute_liquidity_levels(frame_15m_ny)
    if levels.empty:
        return levels
    return levels[levels["Instrument"] == instrument].reset_index(drop=True)


def _build_sweep_candidates(
    bars: PreparedBars15m,
    levels: pd.DataFrame,
    precision_step: float,
    instrument: str,
) -> pd.DataFrame:
    """Merge 15-minute bars with per-day levels for sweep detection."""
    if levels.empty or len(bars) == 0:
        return pd.DataFrame()
    bar_frame = pd.DataFrame(
        {
            "CloseTime": bars.close_times,
            "High": bars.highs,
            "Low": bars.lows,
            "Close": bars.closes,
            "Segment": bars.segments,
            "ATR14Prior": bars.atr14_prior,
            "NYDate": bars.ny_date,
            "NYMinuteOfDay": bars.ny_minute,
        }
    )
    inst_levels = levels[["NYDate"] + list(LEVEL_TYPES)]
    merged = bar_frame.merge(inst_levels, on="NYDate", how="left")
    merged["Instrument"] = instrument
    atr_safe = merged["ATR14Prior"].fillna(0.0)
    merged["Buffer"] = np.maximum(precision_step, SWEEP_BUFFER_ATR_COEFF * atr_safe)
    return merged


def _detect_level_sweeps(merged: pd.DataFrame, level_type: str) -> pd.DataFrame:
    """First-touch sweep for one level type per NYDate."""
    side = "High" if level_type in LEVEL_TYPES_HIGH else "Low"
    level_col = merged[level_type]
    valid = level_col.notna()
    if level_type in ("ONH", "ONL"):
        valid = valid & (merged["NYMinuteOfDay"] >= ON_LEVEL_MIN_MINUTE)
    if side == "High":
        touch_mask = valid & (merged["High"] > level_col + merged["Buffer"])
    else:
        touch_mask = valid & (merged["Low"] < level_col - merged["Buffer"])
    candidates = merged[touch_mask].copy()
    if candidates.empty:
        return pd.DataFrame()
    is_sweep = (
        candidates["Close"] < level_col[candidates.index]
        if side == "High"
        else candidates["Close"] > level_col[candidates.index]
    )
    sweep_rows = candidates[is_sweep].copy()
    if sweep_rows.empty:
        return pd.DataFrame()
    first_touch = (
        sweep_rows.sort_values("CloseTime")
        .groupby("NYDate", sort=False)
        .head(1)
        .copy()
    )
    first_touch["LevelType"] = level_type
    first_touch["Side"] = side
    first_touch["Level"] = first_touch[level_type]
    return first_touch[
        ["Instrument", "NYDate", "CloseTime", "Level", "LevelType", "Side"]
    ]


def _detect_sweeps(
    bars: PreparedBars15m,
    levels: pd.DataFrame,
    precision_step: float,
    instrument: str,
) -> pd.DataFrame:
    """Detect first-touch PDH/PDL/ONH/ONL sweeps on 15-minute bars."""
    merged = _build_sweep_candidates(bars, levels, precision_step, instrument)
    if merged.empty:
        return pd.DataFrame(
            columns=["Instrument", "NYDate", "CloseTime", "Level", "LevelType", "Side"]
        )
    parts = [_detect_level_sweeps(merged, lt) for lt in LEVEL_TYPES]
    non_empty = [p for p in parts if not p.empty]
    if not non_empty:
        return pd.DataFrame(
            columns=["Instrument", "NYDate", "CloseTime", "Level", "LevelType", "Side"]
        )
    out = pd.concat(non_empty, ignore_index=True)
    out["CloseTime"] = pd.to_datetime(out["CloseTime"])
    return out.sort_values("CloseTime").reset_index(drop=True)


# ── Baseline FVG detection (EXP-020/029 logic, applied at 15m) ───────────────


def _fvg_candidate_arrays(
    bars: PreparedBars15m,
    precision_step: float,
    size_atr_coeff: float,
) -> dict[str, np.ndarray]:
    """Return vectorized FVG candidates at index i.

    The candidate at index i uses the three-bar pattern (i-2, i-1, i). The
    minimum FVG size is ``max(precision_step, size_atr_coeff * ATR14Prior)``.
    """
    if len(bars) < 3:
        empty_f = np.array([], dtype=float)
        empty_i = np.array([], dtype=int)
        empty_o = np.array([], dtype=object)
        return {
            "idx": empty_i,
            "side": empty_o,
            "lower": empty_f,
            "upper": empty_f,
            "size": empty_f,
            "atr": empty_f,
        }
    candidate_idx = np.arange(2, len(bars))
    left_highs = bars.highs[:-2]
    left_lows = bars.lows[:-2]
    current_highs = bars.highs[2:]
    current_lows = bars.lows[2:]
    atr_prior = bars.atr14_prior[2:]
    bearish = current_highs < left_lows
    bullish = current_lows > left_highs
    side = np.where(bearish, "Bearish", "Bullish")
    lower = np.where(bearish, current_highs, left_highs)
    upper = np.where(bearish, left_lows, current_lows)
    size = upper - lower
    atr_component = np.where(
        np.isfinite(atr_prior), size_atr_coeff * atr_prior, 0.0
    )
    min_size = np.maximum(precision_step, atr_component)
    keep = (bearish | bullish) & np.isfinite(size) & (size >= min_size)
    return {
        "idx": candidate_idx[keep],
        "side": side[keep],
        "lower": lower[keep],
        "upper": upper[keep],
        "size": size[keep],
        "atr": atr_prior[keep],
    }


def _classify_lifecycle(
    bars: PreparedBars15m,
    creation_idx: int,
    side: str,
    lower: float,
    upper: float,
    lifecycle_bars: int,
    require_mitigation: bool,
) -> dict[str, Any]:
    """Classify lifecycle and first valid IFVG inversion for one FVG.

    When ``require_mitigation`` is True, the inversion is valid only if a
    partial-fill (gap entry) occurs strictly before the inversion bar.
    """
    start = creation_idx + 1
    end = min(start + lifecycle_bars, len(bars))
    if start >= end:
        return {"InversionTime": pd.NaT, "IsIFVG": False, "DelayBars": np.nan}
    highs = bars.highs[start:end]
    lows = bars.lows[start:end]
    closes = bars.closes[start:end]
    if side == "Bullish":
        partial_mask = lows <= upper
        inversion_mask = closes < lower
    else:
        partial_mask = highs >= lower
        inversion_mask = closes > upper
    inversion_pos = _first_valid_inversion(
        partial_mask, inversion_mask, require_mitigation
    )
    if inversion_pos is None:
        return {"InversionTime": pd.NaT, "IsIFVG": False, "DelayBars": np.nan}
    inversion_time = pd.Timestamp(bars.close_times[start + inversion_pos])
    delay_bars = inversion_pos + 1
    return {
        "InversionTime": inversion_time,
        "IsIFVG": True,
        "DelayBars": float(delay_bars),
    }


def _first_valid_inversion(
    partial_mask: np.ndarray,
    inversion_mask: np.ndarray,
    require_mitigation: bool,
) -> int | None:
    """Return index of the first inversion bar honouring the mitigation rule."""
    inv_positions = np.flatnonzero(inversion_mask)
    if inv_positions.size == 0:
        return None
    if not require_mitigation:
        return int(inv_positions[0])
    part_positions = np.flatnonzero(partial_mask)
    if part_positions.size == 0:
        return None
    first_part = int(part_positions[0])
    valid = inv_positions[inv_positions > first_part]
    return int(valid[0]) if valid.size else None


def _detect_fvgs(
    bars: PreparedBars15m,
    instrument: str,
    precision_step: float,
    lifecycle_bars: int,
    size_atr_coeff: float,
    require_mitigation: bool,
) -> pd.DataFrame:
    """Detect FVGs and IFVG inversions for one instrument with one rule shape."""
    cand = _fvg_candidate_arrays(bars, precision_step, size_atr_coeff)
    if cand["idx"].size == 0:
        return pd.DataFrame(columns=FVG_KEY_COLS + ["IsIFVG", "InversionTime", "DelayBars"])
    rows: list[dict[str, Any]] = []
    for idx, side, lower, upper, size, atr in zip(
        cand["idx"], cand["side"], cand["lower"],
        cand["upper"], cand["size"], cand["atr"],
    ):
        lifecycle = _classify_lifecycle(
            bars, int(idx), str(side), float(lower), float(upper),
            lifecycle_bars, require_mitigation,
        )
        rows.append(
            {
                "Instrument": instrument,
                "Segment": bars.segments[idx],
                "Side": side,
                "CreationIndex": int(idx),
                "CreationTime": pd.Timestamp(bars.close_times[idx]),
                "LowerBound": float(lower),
                "UpperBound": float(upper),
                "FVGSize": float(size),
                "ATR14Prior": float(atr) if np.isfinite(atr) else np.nan,
                **lifecycle,
            }
        )
    return pd.DataFrame(rows)


# ── Rule-specific filters (R1, R3, R5 narrow the FVG set) ────────────────────


def _r3_third_candle_passes(bars: PreparedBars15m, idx: int, side: str) -> bool:
    """EXP-018 displacement check on the FVG's third (formation) candle."""
    median_body = bars.body_median_prior[idx]
    body = bars.body_size[idx]
    close_location = bars.close_location[idx]
    open_price = bars.opens[idx]
    close_price = bars.closes[idx]
    if not np.isfinite(median_body) or median_body <= 0.0:
        return False
    if not np.isfinite(body) or body < R3_BODY_MULTIPLE * median_body:
        return False
    if side == "Bearish":
        return bool(
            close_price < open_price and close_location <= R3_LOWER_CLOSE_QUARTILE
        )
    return bool(
        close_price > open_price and close_location >= R3_UPPER_CLOSE_QUARTILE
    )


def _apply_r3_filter(
    fvgs: pd.DataFrame,
    bars: PreparedBars15m,
) -> pd.DataFrame:
    """Filter FVGs whose third candle satisfies the EXP-018 displacement rule."""
    if fvgs.empty:
        return fvgs.copy()
    keep_flags = [
        _r3_third_candle_passes(bars, int(row.CreationIndex), str(row.Side))
        for row in fvgs.itertuples(index=False)
    ]
    return fvgs[pd.Series(keep_flags, index=fvgs.index)].reset_index(drop=True)


def _apply_r5_filter(
    fvgs: pd.DataFrame,
    sweeps: pd.DataFrame,
) -> pd.DataFrame:
    """Filter FVGs whose midpoint is within R5_ZONE_ATR_COEFF*ATR of a recent sweep."""
    if fvgs.empty or sweeps.empty:
        return fvgs.iloc[0:0].copy()
    lookback_ns = R5_SWEEP_LOOKBACK_BARS * PERIOD_MINUTES * 60 * 10**9
    sweep_ns = sweeps["CloseTime"].astype("datetime64[ns]").astype(np.int64).to_numpy()
    sweep_levels = sweeps["Level"].to_numpy(dtype=float)
    keep_flags = []
    for row in fvgs.itertuples(index=False):
        formation_ns = pd.Timestamp(row.CreationTime).value
        midpoint = (float(row.LowerBound) + float(row.UpperBound)) / 2.0
        atr = float(row.ATR14Prior)
        if not np.isfinite(atr) or atr <= 0.0:
            keep_flags.append(False)
            continue
        in_window = (sweep_ns < formation_ns) & (
            sweep_ns >= formation_ns - lookback_ns
        )
        if not in_window.any():
            keep_flags.append(False)
            continue
        window_levels = sweep_levels[in_window]
        within_zone = np.any(
            np.abs(window_levels - midpoint) <= R5_ZONE_ATR_COEFF * atr
        )
        keep_flags.append(bool(within_zone))
    if not keep_flags:
        return fvgs.iloc[0:0].copy()
    return fvgs[pd.Series(keep_flags, index=fvgs.index)].reset_index(drop=True)


# ── Per-rule application ─────────────────────────────────────────────────────


def _rule_event_table(
    rule: str,
    ctx: InstrumentContext,
    baseline_fvgs: pd.DataFrame,
) -> pd.DataFrame:
    """Return the rule-eligible FVG/IFVG event table for one rule on one context."""
    if rule == "R1":
        return _detect_fvgs(
            ctx.bars, ctx.instrument, ctx.precision_step,
            BASELINE_LIFECYCLE_BARS, R1_SIZE_ATR_COEFF, require_mitigation=False,
        )
    if rule == "R2":
        return _detect_fvgs(
            ctx.bars, ctx.instrument, ctx.precision_step,
            R2_LIFECYCLE_BARS, BASELINE_SIZE_ATR_COEFF, require_mitigation=False,
        )
    if rule == "R3":
        return _apply_r3_filter(baseline_fvgs, ctx.bars)
    if rule == "R4":
        return _detect_fvgs(
            ctx.bars, ctx.instrument, ctx.precision_step,
            BASELINE_LIFECYCLE_BARS, BASELINE_SIZE_ATR_COEFF,
            require_mitigation=True,
        )
    if rule == "R5":
        return _apply_r5_filter(baseline_fvgs, ctx.sweeps)
    raise ValueError(f"Unknown rule: {rule}")


def _build_baseline_and_rules(
    ctx: InstrumentContext,
) -> dict[str, pd.DataFrame]:
    """Detect baseline FVGs and all rule-eligible FVG/IFVG tables for one instrument."""
    baseline = _detect_fvgs(
        ctx.bars, ctx.instrument, ctx.precision_step,
        BASELINE_LIFECYCLE_BARS, BASELINE_SIZE_ATR_COEFF, require_mitigation=False,
    )
    return {
        "BASELINE": baseline,
        **{rule: _rule_event_table(rule, ctx, baseline) for rule in RULE_NAMES},
    }


# ── Reproducibility digests ──────────────────────────────────────────────────


def _digest_event_table(events: pd.DataFrame, key_cols: list[str]) -> str:
    """Return a stable SHA-256 digest of an event table on its identity columns."""
    if events.empty:
        return hashlib.sha256(b"EMPTY").hexdigest()
    available = [c for c in key_cols if c in events.columns]
    stable = events[available].sort_values(available).copy()
    text = stable.to_csv(index=False, float_format="%.12g")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _split_by_segment(events: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Split an event table into Train/Test segments."""
    return {
        seg: events[events["Segment"] == seg].reset_index(drop=True)
        for seg in SEGMENTS
    }


def _rule_digests_per_segment(
    rule_events: dict[str, pd.DataFrame],
) -> dict[tuple[str, str], dict[str, str]]:
    """Compute per-(rule, segment) FVG and IFVG digests."""
    digests: dict[tuple[str, str], dict[str, str]] = {}
    for rule in RULE_NAMES:
        by_seg = _split_by_segment(rule_events[rule])
        for seg in SEGMENTS:
            seg_events = by_seg[seg]
            ifvg_events = seg_events[seg_events["IsIFVG"]] if not seg_events.empty else seg_events
            digests[(rule, seg)] = {
                "fvg": _digest_event_table(seg_events, FVG_KEY_COLS),
                "ifvg": _digest_event_table(ifvg_events, IFVG_KEY_COLS),
            }
    return digests


def _verify_reproducibility(
    canonical_rule_events_per_instrument: dict[str, dict[str, pd.DataFrame]],
    shuffled_rule_events_per_instrument: dict[str, dict[str, pd.DataFrame]],
) -> pd.DataFrame:
    """Compare canonical vs shuffled digests per (instrument, rule, segment)."""
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        canonical = _rule_digests_per_segment(
            canonical_rule_events_per_instrument[instrument]
        )
        shuffled = _rule_digests_per_segment(
            shuffled_rule_events_per_instrument[instrument]
        )
        for rule in RULE_NAMES:
            for seg in SEGMENTS:
                c_fvg = canonical[(rule, seg)]["fvg"]
                c_ifvg = canonical[(rule, seg)]["ifvg"]
                s_fvg = shuffled[(rule, seg)]["fvg"]
                s_ifvg = shuffled[(rule, seg)]["ifvg"]
                rows.append(
                    {
                        "Instrument": instrument,
                        "Rule": rule,
                        "Segment": seg,
                        "FVGDigestCanonical": c_fvg,
                        "FVGDigestShuffled": s_fvg,
                        "IFVGDigestCanonical": c_ifvg,
                        "IFVGDigestShuffled": s_ifvg,
                        "DigestsMatch": bool(c_fvg == s_fvg and c_ifvg == s_ifvg),
                    }
                )
    return pd.DataFrame(rows)


# ── Readiness statistics ─────────────────────────────────────────────────────


def _baseline_counts(
    rule_events_per_instrument: dict[str, dict[str, pd.DataFrame]],
) -> pd.DataFrame:
    """Compute baseline FVG/IFVG counts per (instrument, segment)."""
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        baseline = rule_events_per_instrument[instrument]["BASELINE"]
        by_seg = _split_by_segment(baseline)
        for seg in SEGMENTS:
            seg_events = by_seg[seg]
            ifvg_n = int(seg_events["IsIFVG"].sum()) if not seg_events.empty else 0
            rows.append(
                {
                    "Instrument": instrument,
                    "Segment": seg,
                    "BaselineFVGCount": len(seg_events),
                    "BaselineIFVGCount": ifvg_n,
                    "BaselineInversionRate": (
                        ifvg_n / len(seg_events) if len(seg_events) else np.nan
                    ),
                }
            )
    return pd.DataFrame(rows)


def _readiness_for_cell(
    instrument: str,
    rule: str,
    segment: str,
    rule_events: pd.DataFrame,
    baseline_fvg_count: int,
    r3_creation_times: set[pd.Timestamp],
) -> dict[str, Any]:
    """Compute the seven readiness statistics for one (rule, instrument, segment)."""
    seg_events = rule_events[rule_events["Segment"] == segment]
    fvg_n = len(seg_events)
    ifvg_subset = seg_events[seg_events["IsIFVG"]] if fvg_n else seg_events
    ifvg_n = len(ifvg_subset)
    inversion_rate = ifvg_n / fvg_n if fvg_n else np.nan
    selectivity = fvg_n / baseline_fvg_count if baseline_fvg_count else np.nan
    median_delay = (
        float(ifvg_subset["DelayBars"].median()) if ifvg_n else np.nan
    )
    denom_valid = bool(
        fvg_n > 0 and np.isfinite(inversion_rate)
    )
    overlap = _overlap_share(seg_events, r3_creation_times)
    return {
        "Instrument": instrument,
        "Rule": rule,
        "Segment": segment,
        "RuleEligibleFVGCount": int(fvg_n),
        "RuleEligibleIFVGCount": int(ifvg_n),
        "InversionRate": inversion_rate,
        "SelectivityRatio": selectivity,
        "MedianDelayBars": median_delay,
        "DenominatorValid": denom_valid,
        "OverlapWithDisplacementShare": overlap,
        "Check1Reproducibility": False,
        "Check2CountFloor": bool(
            fvg_n >= MIN_FVG_PER_SEGMENT and ifvg_n >= MIN_IFVG_PER_SEGMENT
        ),
        "Check3InversionBand": bool(
            np.isfinite(inversion_rate)
            and INVERSION_BAND_LOW <= inversion_rate <= INVERSION_BAND_HIGH
        ),
        "Check4Selectivity": bool(
            np.isfinite(selectivity)
            and selectivity <= SELECTIVITY_MAX_RETENTION
        ),
        "Check5MedianDelay": bool(
            np.isfinite(median_delay) and median_delay <= MAX_MEDIAN_DELAY_BARS
        ),
        "Check6DenominatorValid": denom_valid,
    }


def _overlap_share(
    seg_events: pd.DataFrame,
    r3_creation_times: set[pd.Timestamp],
) -> float:
    """Share of rule-eligible FVGs whose formation matches a R3-eligible FVG."""
    if seg_events.empty or not r3_creation_times:
        return np.nan
    hits = sum(
        pd.Timestamp(ts) in r3_creation_times
        for ts in seg_events["CreationTime"].to_numpy()
    )
    return hits / len(seg_events)


def _readiness_table(
    rule_events_per_instrument: dict[str, dict[str, pd.DataFrame]],
    baseline_counts: pd.DataFrame,
    repro_df: pd.DataFrame,
) -> pd.DataFrame:
    """Compute the 40-row per-(rule, instrument, segment) readiness table."""
    rows: list[dict[str, Any]] = []
    baseline_lookup = baseline_counts.set_index(["Instrument", "Segment"]).to_dict("index")
    repro_lookup = repro_df.set_index(["Instrument", "Rule", "Segment"]).to_dict("index")
    for instrument in INSTRUMENTS:
        r3_events = rule_events_per_instrument[instrument].get("R3", pd.DataFrame())
        r3_times = {pd.Timestamp(ts) for ts in r3_events["CreationTime"]} if not r3_events.empty else set()
        for rule in RULE_NAMES:
            for seg in SEGMENTS:
                baseline_fvg = int(
                    baseline_lookup[(instrument, seg)]["BaselineFVGCount"]
                )
                cell = _readiness_for_cell(
                    instrument, rule, seg,
                    rule_events_per_instrument[instrument][rule],
                    baseline_fvg, r3_times,
                )
                cell["Check1Reproducibility"] = bool(
                    repro_lookup[(instrument, rule, seg)]["DigestsMatch"]
                )
                cell["PassesAllSixChecks"] = bool(
                    cell["Check1Reproducibility"]
                    and cell["Check2CountFloor"]
                    and cell["Check3InversionBand"]
                    and cell["Check4Selectivity"]
                    and cell["Check5MedianDelay"]
                    and cell["Check6DenominatorValid"]
                )
                rows.append(cell)
    return pd.DataFrame(rows)


# ── Block bootstrap on inversion rate ────────────────────────────────────────


def _block_bootstrap_inversion_rate(
    is_ifvg: np.ndarray,
    n_reps: int,
    block: int,
    seed: int,
) -> dict[str, float]:
    """Block bootstrap the inversion rate; return mean, 2.5th, 97.5th percentile."""
    n = len(is_ifvg)
    if n == 0:
        return {"BootMean": np.nan, "CILow": np.nan, "CIHigh": np.nan, "N": 0}
    if n < block:
        return {
            "BootMean": float(is_ifvg.mean()),
            "CILow": np.nan,
            "CIHigh": np.nan,
            "N": n,
        }
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(n / block))
    samples = np.empty(n_reps, dtype=float)
    for rep in range(n_reps):
        starts = rng.integers(0, n - block + 1, size=n_blocks)
        idx = (starts[:, None] + np.arange(block)).reshape(-1)[:n]
        samples[rep] = is_ifvg[idx].mean()
    return {
        "BootMean": float(np.mean(samples)),
        "CILow": float(np.quantile(samples, 0.025)),
        "CIHigh": float(np.quantile(samples, 0.975)),
        "N": n,
    }


def _bootstrap_table(
    rule_events_per_instrument: dict[str, dict[str, pd.DataFrame]],
) -> pd.DataFrame:
    """Run the per-cell block bootstrap on the inversion rate."""
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        for rule in RULE_NAMES:
            events = rule_events_per_instrument[instrument][rule]
            for seg in SEGMENTS:
                seg_events = events[events["Segment"] == seg]
                is_ifvg = seg_events["IsIFVG"].astype(float).to_numpy() if len(seg_events) else np.array([], dtype=float)
                stats = _block_bootstrap_inversion_rate(
                    is_ifvg, BOOTSTRAP_REPS, BOOTSTRAP_BLOCK, BOOTSTRAP_SEED
                )
                rows.append(
                    {
                        "Instrument": instrument,
                        "Rule": rule,
                        "Segment": seg,
                        "BlockSize": BOOTSTRAP_BLOCK,
                        "Seed": BOOTSTRAP_SEED,
                        "NResamples": BOOTSTRAP_REPS,
                        **stats,
                    }
                )
    return pd.DataFrame(rows)


# ── Aggregate verdict ────────────────────────────────────────────────────────


def _qualifying_instruments_per_rule(
    readiness: pd.DataFrame,
) -> dict[str, list[str]]:
    """Identify instruments where both train AND test pass all six checks."""
    qualifying: dict[str, list[str]] = {rule: [] for rule in RULE_NAMES}
    for rule in RULE_NAMES:
        for instrument in INSTRUMENTS:
            cells = readiness[
                (readiness["Rule"] == rule)
                & (readiness["Instrument"] == instrument)
            ]
            train_pass = bool(
                cells[cells["Segment"] == "Train"]["PassesAllSixChecks"].iloc[0]
            )
            test_pass = bool(
                cells[cells["Segment"] == "Test"]["PassesAllSixChecks"].iloc[0]
            )
            if train_pass and test_pass:
                qualifying[rule].append(instrument)
    return qualifying


def _rule_contention_metrics(
    rule: str,
    qualifying_instruments: list[str],
    readiness: pd.DataFrame,
) -> dict[str, float]:
    """Combined inversion rate and IFVG count summed across qualifying segments."""
    if not qualifying_instruments:
        return {"CombinedInversionRate": np.nan, "CombinedIFVGCount": 0}
    mask = (
        (readiness["Rule"] == rule)
        & (readiness["Instrument"].isin(qualifying_instruments))
    )
    cells = readiness[mask]
    inv_mean = float(cells["InversionRate"].mean())
    ifvg_total = int(cells["RuleEligibleIFVGCount"].sum())
    return {"CombinedInversionRate": inv_mean, "CombinedIFVGCount": ifvg_total}


def _select_winning_rule(
    qualifying: dict[str, list[str]],
    readiness: pd.DataFrame,
) -> dict[str, Any]:
    """Apply scope §"Aggregate Verdict" selection mechanics."""
    contention = {
        rule: instruments
        for rule, instruments in qualifying.items()
        if len(instruments) >= QUALIFYING_INSTRUMENT_FLOOR
    }
    metrics = {
        rule: _rule_contention_metrics(rule, instruments, readiness)
        for rule, instruments in contention.items()
    }
    if not contention:
        return {
            "verdict_text": (
                "Branch B closes at EXP-033 with selectivity-gated no-go"
            ),
            "selected_rule": None,
            "rules_in_contention": [],
            "rule_metrics": metrics,
            "qualifying_instruments_per_rule": qualifying,
        }
    if len(contention) == 1:
        rule = next(iter(contention.keys()))
        return {
            "verdict_text": f"Rule {rule} ({RULE_LABELS[rule]}) selected",
            "selected_rule": rule,
            "rules_in_contention": list(contention.keys()),
            "rule_metrics": metrics,
            "qualifying_instruments_per_rule": qualifying,
        }
    return _resolve_tie(contention, metrics, qualifying)


def _resolve_tie(
    contention: dict[str, list[str]],
    metrics: dict[str, dict[str, float]],
    qualifying: dict[str, list[str]],
) -> dict[str, Any]:
    """Pick the lowest inversion rate; break ties on IFVG count; else flag failure."""
    sorted_rules = sorted(
        contention.keys(),
        key=lambda r: metrics[r]["CombinedInversionRate"],
    )
    best = sorted_rules[0]
    best_rate = metrics[best]["CombinedInversionRate"]
    tied = [
        r for r in sorted_rules
        if abs(metrics[r]["CombinedInversionRate"] - best_rate) < TIE_BREAK_EPSILON
    ]
    if len(tied) == 1:
        return {
            "verdict_text": f"Rule {best} ({RULE_LABELS[best]}) selected",
            "selected_rule": best,
            "rules_in_contention": list(contention.keys()),
            "rule_metrics": metrics,
            "qualifying_instruments_per_rule": qualifying,
        }
    tied_sorted = sorted(
        tied, key=lambda r: metrics[r]["CombinedIFVGCount"], reverse=True
    )
    top = tied_sorted[0]
    top_count = metrics[top]["CombinedIFVGCount"]
    final_tied = [r for r in tied_sorted if metrics[r]["CombinedIFVGCount"] == top_count]
    if len(final_tied) == 1:
        return {
            "verdict_text": f"Rule {top} ({RULE_LABELS[top]}) selected by tie-break",
            "selected_rule": top,
            "rules_in_contention": list(contention.keys()),
            "rule_metrics": metrics,
            "qualifying_instruments_per_rule": qualifying,
        }
    return {
        "verdict_text": (
            "Tie-break failure: route to checkpoint reflection. "
            f"Tied rules: {','.join(final_tied)}"
        ),
        "selected_rule": None,
        "rules_in_contention": list(contention.keys()),
        "rule_metrics": metrics,
        "qualifying_instruments_per_rule": qualifying,
    }


# ── Plotting helpers (bounded inputs only) ───────────────────────────────────


def _plot_fvg_count_waterfall(
    baseline_counts: pd.DataFrame,
    readiness: pd.DataFrame,
    save_path: Path,
) -> None:
    """4-panel grouped bar chart of FVG counts: baseline + R1-R5 per instrument."""
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), sharey=False)
    axes = axes.flatten()
    labels = ["Baseline"] + list(RULE_NAMES)
    width = 0.35
    x = np.arange(len(labels))
    for ax, instrument in zip(axes, INSTRUMENTS):
        train_vals = [
            int(
                baseline_counts[
                    (baseline_counts["Instrument"] == instrument)
                    & (baseline_counts["Segment"] == "Train")
                ]["BaselineFVGCount"].iloc[0]
            )
        ] + [_cell_count(readiness, instrument, rule, "Train") for rule in RULE_NAMES]
        test_vals = [
            int(
                baseline_counts[
                    (baseline_counts["Instrument"] == instrument)
                    & (baseline_counts["Segment"] == "Test")
                ]["BaselineFVGCount"].iloc[0]
            )
        ] + [_cell_count(readiness, instrument, rule, "Test") for rule in RULE_NAMES]
        ax.bar(x - width / 2, train_vals, width=width, color="#3a7bd5", label="Train")
        ax.bar(x + width / 2, test_vals, width=width, color="#f39c12", label="Test")
        ax.axhline(MIN_FVG_PER_SEGMENT, color="red", linestyle="--", linewidth=1, label="Count floor")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=20)
        ax.set_title(instrument)
        ax.set_ylabel("Rule-eligible FVG count")
        ax.legend(fontsize=8, loc="upper right")
    fig.suptitle("EXP-033: FVG count waterfall (baseline vs R1-R5)", fontsize=13)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _cell_count(readiness: pd.DataFrame, instrument: str, rule: str, seg: str) -> int:
    """Return the rule-eligible FVG count for one readiness cell."""
    row = readiness[
        (readiness["Instrument"] == instrument)
        & (readiness["Rule"] == rule)
        & (readiness["Segment"] == seg)
    ]
    return int(row["RuleEligibleFVGCount"].iloc[0]) if not row.empty else 0


def _matrix_pivot(readiness: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """Pivot readiness into a (rule x instrument-segment) matrix."""
    cells = readiness.copy()
    cells["Cell"] = cells["Instrument"] + "-" + cells["Segment"]
    pivot = cells.pivot(index="Rule", columns="Cell", values=value_col)
    cols = [f"{i}-{s}" for i in INSTRUMENTS for s in SEGMENTS]
    return pivot.reindex(columns=cols).reindex(index=list(RULE_NAMES))


def _plot_inversion_rate_matrix(readiness: pd.DataFrame, save_path: Path) -> None:
    """Heatmap of inversion rates with the [0.55, 0.75] band overlay."""
    sns.set_theme(style="white")
    matrix = _matrix_pivot(readiness, "InversionRate")
    fig, ax = plt.subplots(figsize=(11, 5))
    sns.heatmap(
        matrix.astype(float), annot=True, fmt=".3f",
        cmap="RdYlGn_r", center=0.5, vmin=0.0, vmax=1.0,
        cbar_kws={"label": "Inversion rate"}, ax=ax,
        annot_kws={"size": 9},
    )
    ax.set_title(
        "EXP-033: Inversion rate by rule × (instrument, segment) "
        f"— band [{INVERSION_BAND_LOW:.2f}, {INVERSION_BAND_HIGH:.2f}]"
    )
    ax.set_xlabel("")
    ax.set_ylabel("Rule")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_median_delay_matrix(readiness: pd.DataFrame, save_path: Path) -> None:
    """Heatmap of median confirmation delay with the 24-bar bound annotated."""
    sns.set_theme(style="white")
    matrix = _matrix_pivot(readiness, "MedianDelayBars")
    fig, ax = plt.subplots(figsize=(11, 5))
    sns.heatmap(
        matrix.astype(float), annot=True, fmt=".1f",
        cmap="viridis", vmin=0.0, vmax=120.0,
        cbar_kws={"label": "Median delay (15m bars)"}, ax=ax,
        annot_kws={"size": 9},
    )
    ax.set_title(
        "EXP-033: Median confirmation delay by rule × (instrument, segment) "
        f"— bound {MAX_MEDIAN_DELAY_BARS} bars"
    )
    ax.set_xlabel("")
    ax.set_ylabel("Rule")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_readiness_grid(readiness: pd.DataFrame, save_path: Path) -> None:
    """6-panel pass/fail grid covering each readiness check."""
    sns.set_theme(style="white")
    check_cols = [
        ("Check1Reproducibility", "1. Reproducibility"),
        ("Check2CountFloor", "2. Count floor"),
        ("Check3InversionBand", "3. Inversion band"),
        ("Check4Selectivity", "4. Selectivity"),
        ("Check5MedianDelay", "5. Median delay"),
        ("Check6DenominatorValid", "6. Denominator valid"),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    axes = axes.flatten()
    for ax, (col, title) in zip(axes, check_cols):
        matrix = _matrix_pivot(readiness, col).astype(float)
        sns.heatmap(
            matrix, annot=False, cmap=["#d9534f", "#5cb85c"], cbar=False,
            linewidths=0.5, linecolor="white", vmin=0, vmax=1, ax=ax,
        )
        ax.set_title(title, fontsize=11)
        ax.set_xlabel("")
        ax.set_ylabel("")
    fig.suptitle("EXP-033: Readiness gate pass (green) / fail (red) grid", fontsize=13)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ── Orchestration helpers ────────────────────────────────────────────────────


def _build_instrument_context(
    instrument: str,
    *,
    shuffle_seed: int | None = None,
) -> InstrumentContext:
    """Load all per-instrument detection inputs (bars, levels, sweeps)."""
    bars, precision_step = _load_instrument_15m(instrument, shuffle_seed=shuffle_seed)
    if len(bars) == 0:
        empty = pd.DataFrame()
        return InstrumentContext(instrument, bars, precision_step, empty, empty)
    levels_frame = _instrument_levels_frame(instrument, shuffle_seed=shuffle_seed)
    levels = _levels_for_instrument(levels_frame, instrument)
    sweeps = _detect_sweeps(bars, levels, precision_step, instrument)
    return InstrumentContext(instrument, bars, precision_step, levels, sweeps)


def _instrument_levels_frame(
    instrument: str,
    *,
    shuffle_seed: int | None = None,
) -> pl.DataFrame:
    """Rebuild the 15-minute NY-featured frame used for level computation."""
    loaded = load_analysis_timebars(DATA_DIR, instrument)
    frame_1m = loaded.frame
    if shuffle_seed is not None and not frame_1m.is_empty():
        frame_1m = _shuffle_then_resort_1m(frame_1m, shuffle_seed)
    frame_15m = _aggregate_to_15m_with_features(frame_1m)
    if frame_15m.is_empty():
        return frame_15m
    train_end_time = train_cutoff_time(
        frame_15m, int(frame_15m.height * ANALYSIS_TRAIN_FRACTION)
    )
    return _attach_ny_features(frame_15m, train_end_time)


def _detect_all_rule_events(
    *,
    shuffle_seed: int | None = None,
) -> dict[str, dict[str, pd.DataFrame]]:
    """Build per-instrument baseline + R1-R5 event tables for one input path."""
    by_instrument: dict[str, dict[str, pd.DataFrame]] = {}
    for instrument in INSTRUMENTS:
        LOGGER.info(
            "EXP-033: detecting events for %s (shuffle_seed=%s)",
            instrument, shuffle_seed,
        )
        ctx = _build_instrument_context(instrument, shuffle_seed=shuffle_seed)
        by_instrument[instrument] = _build_baseline_and_rules(ctx)
    return by_instrument


def _write_verdict_json(verdict: dict[str, Any], path: Path) -> None:
    """Serialize verdict mapping with safe JSON conversion."""
    payload = {
        "verdict_text": verdict["verdict_text"],
        "selected_rule": verdict["selected_rule"],
        "rules_in_contention": verdict["rules_in_contention"],
        "qualifying_instruments_per_rule": verdict["qualifying_instruments_per_rule"],
        "rule_metrics": {
            rule: {
                "CombinedInversionRate": _json_safe(m["CombinedInversionRate"]),
                "CombinedIFVGCount": int(m["CombinedIFVGCount"]),
            }
            for rule, m in verdict["rule_metrics"].items()
        },
        "selection_thresholds": {
            "qualifying_instrument_floor": QUALIFYING_INSTRUMENT_FLOOR,
            "tie_break_epsilon": TIE_BREAK_EPSILON,
            "inversion_band_low": INVERSION_BAND_LOW,
            "inversion_band_high": INVERSION_BAND_HIGH,
            "selectivity_max_retention": SELECTIVITY_MAX_RETENTION,
            "max_median_delay_bars": MAX_MEDIAN_DELAY_BARS,
            "min_fvg_per_segment": MIN_FVG_PER_SEGMENT,
            "min_ifvg_per_segment": MIN_IFVG_PER_SEGMENT,
        },
    }
    path.write_text(json.dumps(payload, indent=2, default=str))


def _json_safe(value: Any) -> Any:
    """Convert numpy/pandas scalars to plain Python types for JSON."""
    if value is None:
        return None
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (int, np.integer)):
        return int(value)
    return value


# ── Orchestration: run_experiment ────────────────────────────────────────────


def run_experiment() -> None:
    """Execute the EXP-033 readiness survey end to end."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    LOGGER.info("EXP-033: canonical detection pass")
    canonical = _detect_all_rule_events(shuffle_seed=None)

    LOGGER.info("EXP-033: shuffled-resort reproducibility pass")
    shuffled = _detect_all_rule_events(shuffle_seed=REPRODUCIBILITY_SHUFFLE_SEED)

    LOGGER.info("EXP-033: computing readiness statistics")
    baseline = _baseline_counts(canonical)
    repro = _verify_reproducibility(canonical, shuffled)
    readiness = _readiness_table(canonical, baseline, repro)
    bootstrap = _bootstrap_table(canonical)

    LOGGER.info("EXP-033: applying aggregate verdict")
    qualifying = _qualifying_instruments_per_rule(readiness)
    verdict = _select_winning_rule(qualifying, readiness)

    LOGGER.info("EXP-033: writing outputs")
    baseline.to_csv(RESULTS_DIR / "baseline_counts.csv", index=False)
    readiness.to_csv(RESULTS_DIR / "readiness_table.csv", index=False)
    repro.to_csv(RESULTS_DIR / "reproducibility_digests.csv", index=False)
    bootstrap.to_csv(RESULTS_DIR / "bootstrap_inversion_rate.csv", index=False)
    _write_verdict_json(verdict, RESULTS_DIR / "verdict.json")

    LOGGER.info("EXP-033: rendering plots")
    _plot_fvg_count_waterfall(
        baseline, readiness, PLOTS_DIR / "01_fvg_count_waterfall.png"
    )
    _plot_inversion_rate_matrix(
        readiness, PLOTS_DIR / "02_inversion_rate_matrix.png"
    )
    _plot_median_delay_matrix(
        readiness, PLOTS_DIR / "03_median_delay_matrix.png"
    )
    _plot_readiness_grid(
        readiness, PLOTS_DIR / "04_readiness_gate_grid.png"
    )

    _print_summary(baseline, readiness, verdict)


def _print_summary(
    baseline: pd.DataFrame,
    readiness: pd.DataFrame,
    verdict: dict[str, Any],
) -> None:
    """Concise manual-run summary."""
    print("\n=== EXP-033 baseline FVG/IFVG counts ===")
    print(baseline.to_string(index=False))
    print("\n=== EXP-033 readiness (PassesAllSixChecks per cell) ===")
    summary = readiness[
        ["Instrument", "Rule", "Segment", "RuleEligibleFVGCount",
         "RuleEligibleIFVGCount", "InversionRate", "SelectivityRatio",
         "MedianDelayBars", "PassesAllSixChecks"]
    ]
    print(summary.to_string(index=False))
    print("\n=== EXP-033 aggregate verdict ===")
    print(verdict["verdict_text"])
    print(f"selected_rule: {verdict['selected_rule']}")
    print(f"rules_in_contention: {verdict['rules_in_contention']}")
    print("qualifying_instruments_per_rule:")
    for rule, instruments in verdict["qualifying_instruments_per_rule"].items():
        print(f"  {rule}: {instruments}")


def main() -> None:
    """Configure logging and run the experiment."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    run_experiment()


if __name__ == "__main__":
    main()
