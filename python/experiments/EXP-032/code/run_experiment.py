"""
Experiment EXP-032: 1-Hour USTEC Candidate A Breaker Magnitude Gate
Implements the analysis plan from analysis-plan.md.

Applies the EXP-015 sweep, EXP-018 displacement, and EXP-022 Candidate A
breaker rules at 1-hour resolution using elapsed-time-scaled constants from
scope.md. Detection uses synthetic 1-hour bars resampled from holdout-excluded
1-minute USTEC bars. Outcomes use real 1-minute prices strictly after the
confirming 1-hour displacement candle close.
"""
import json
import logging
import sys
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

from bar_aggregator import aggregate_ohlc, coverage_summary  # noqa: E402
from ict_timebar import (  # noqa: E402
    OVERNIGHT_END_MINUTE,
    add_ny_time_features,
    compute_liquidity_levels,
    compute_price_precision_step,
    load_analysis_timebars,
    train_cutoff_time,
    weekday_filter,
)


LOGGER = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-032"
EXP031_RESULTS_DIR = PYTHON_ROOT / "experiments" / "EXP-031" / "results"
EXP023_RESULTS_DIR = PYTHON_ROOT / "experiments" / "EXP-023" / "results"

INSTRUMENT = "USTEC"
PERIOD_MINUTES = 60
ATR_PERIOD = 14
BUFFER_ATR_COEFF = 0.05

# Displacement: EXP-018 rule scaled to 1-hour elapsed time.
MAX_CONFIRMATION_BARS = 3
BODY_MEDIAN_WINDOW = 25
BODY_MULTIPLE = 1.5
LOWER_CLOSE_QUARTILE = 0.25
UPPER_CLOSE_QUARTILE = 0.75

# Candidate A breaker: EXP-022 rule scaled to 1-hour elapsed time.
CAND_A_LOOKBACK_BARS = 8
MAX_BREAKER_DELAY = 30

# Outcomes and gates.
PRIMARY_HORIZON = 60
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 42
MIN_EVENTS_PER_SEGMENT = 50
RETENTION_LIMIT = 0.30
ON_LEVEL_MIN_MINUTE = OVERNIGHT_END_MINUTE
LEVEL_TYPES_HIGH = ["PDH", "ONH"]
LEVEL_TYPES_LOW = ["PDL", "ONL"]
PLOT_R_CAP = 8.0

SWEEP_COLS = [
    "Instrument",
    "NYDate",
    "Segment",
    "CloseTime",
    "Open",
    "High",
    "Low",
    "Close",
    "LevelType",
    "Side",
    "EventType",
    "Level",
    "Buffer",
    "Stop",
    "Entry",
    "Risk1R",
]


# Data loading


def _add_atr_1h(frame_1h: pl.DataFrame) -> pl.DataFrame:
    """Add TrueRange and ATR14Prior on the 1-hour detection series."""
    prev_close = pl.col("Close").shift(1)
    true_range = pl.max_horizontal(
        pl.col("High") - pl.col("Low"),
        (pl.col("High") - prev_close).abs(),
        (pl.col("Low") - prev_close).abs(),
    ).fill_null(pl.col("High") - pl.col("Low"))
    return frame_1h.with_columns(true_range.alias("TrueRange")).with_columns(
        pl.col("TrueRange")
        .rolling_mean(window_size=ATR_PERIOD, min_samples=ATR_PERIOD)
        .shift(1)
        .alias("ATR14Prior")
    )


def _add_body_metrics(frame_1h: pl.DataFrame) -> pl.DataFrame:
    """Add body size, close location, and prior body median on the 1-hour frame."""
    body = (pl.col("Close") - pl.col("Open")).abs()
    candle_range = pl.col("High") - pl.col("Low")
    close_loc = (
        pl.when(candle_range > 0)
        .then((pl.col("Close") - pl.col("Low")) / candle_range)
        .otherwise(0.5)
    )
    return frame_1h.with_columns(
        body.alias("BodySize"),
        close_loc.alias("CloseLocation"),
    ).with_columns(
        pl.col("BodySize")
        .rolling_median(window_size=BODY_MEDIAN_WINDOW, min_samples=BODY_MEDIAN_WINDOW)
        .shift(1)
        .alias("BodyMedianPrior")
    )


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, float, dict[str, int]]:
    """Load USTEC 1-minute analysis bars, 1-hour bars, levels, and diagnostics."""
    loaded = load_analysis_timebars(DATA_DIR, INSTRUMENT)
    frame_1m = loaded.frame

    train_end_1m = train_cutoff_time(frame_1m, loaded.train_rows)
    frame_1m_ny = add_ny_time_features(frame_1m, train_end_1m)
    levels = compute_liquidity_levels(frame_1m_ny)

    precision_step = compute_price_precision_step(frame_1m)
    bars_1m = (
        frame_1m.sort("CloseTime")
        .select(["Symbol", "OpenTime", "CloseTime", "Open", "High", "Low", "Close"])
        .to_pandas()
    )
    bars_1m["CloseTime"] = pd.to_datetime(bars_1m["CloseTime"])
    bars_1m["OpenTime"] = pd.to_datetime(bars_1m["OpenTime"])

    aggregated = aggregate_ohlc(frame_1m, period_minutes=PERIOD_MINUTES)
    coverage = coverage_summary(frame_1m, aggregated, period_minutes=PERIOD_MINUTES)
    if aggregated.is_empty():
        empty_1h = pd.DataFrame(columns=["CloseTime", "High", "Low", "Close"])
        return bars_1m, empty_1h, levels, precision_step, coverage

    train_rows_1h = int(aggregated.height * 0.70)
    train_end_1h = train_cutoff_time(aggregated, train_rows_1h)
    frame_1h = _add_body_metrics(_add_atr_1h(add_ny_time_features(aggregated, train_end_1h)))
    weekday_1h = weekday_filter(frame_1h).to_pandas()
    weekday_1h["CloseTime"] = pd.to_datetime(weekday_1h["CloseTime"])
    weekday_1h["OpenTime"] = pd.to_datetime(weekday_1h["OpenTime"])
    weekday_1h = weekday_1h.reset_index(drop=True)
    return bars_1m, weekday_1h, levels, precision_step, coverage


# Sweep detection


def _build_level_events(merged: pd.DataFrame, level_type: str) -> pd.DataFrame:
    """Return the first touch for one NY date and liquidity-level type."""
    side = "High" if level_type in ("PDH", "ONH") else "Low"
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

    if side == "High":
        candidates["EventType"] = np.where(
            candidates["Close"] < candidates[level_type], "Sweep", "Breach"
        )
    else:
        candidates["EventType"] = np.where(
            candidates["Close"] > candidates[level_type], "Sweep", "Breach"
        )

    first_touch = (
        candidates.sort_values("CloseTime")
        .groupby("NYDate", sort=False)
        .head(1)
        .copy()
    )
    first_touch["LevelType"] = level_type
    first_touch["Side"] = side
    first_touch["Level"] = first_touch[level_type]
    first_touch["Stop"] = np.where(
        side == "High",
        first_touch["High"] + first_touch["Buffer"],
        first_touch["Low"] - first_touch["Buffer"],
    )
    first_touch["Entry"] = first_touch["Close"]
    first_touch["Risk1R"] = (first_touch["Stop"] - first_touch["Entry"]).abs()
    return first_touch


def detect_sweeps(
    weekday_1h: pd.DataFrame,
    levels: pd.DataFrame,
    precision_step: float,
) -> pd.DataFrame:
    """Detect 1-hour sweep and breach events for USTEC."""
    inst_levels = (
        levels[levels["Instrument"] == INSTRUMENT][
            ["NYDate", "PDH", "PDL", "ONH", "ONL"]
        ].copy()
    )
    merged = weekday_1h.merge(inst_levels, on="NYDate", how="left")
    atr_safe = merged["ATR14Prior"].fillna(0.0)
    merged["Buffer"] = np.maximum(precision_step, BUFFER_ATR_COEFF * atr_safe)
    merged["Instrument"] = INSTRUMENT

    parts = [
        _build_level_events(merged, level_type)
        for level_type in LEVEL_TYPES_HIGH + LEVEL_TYPES_LOW
    ]
    non_empty = [part for part in parts if not part.empty]
    if not non_empty:
        return pd.DataFrame(columns=SWEEP_COLS)
    result = pd.concat(non_empty, ignore_index=True)
    present = [column for column in SWEEP_COLS if column in result.columns]
    return result[present].reset_index(drop=True)


# Displacement detection


def _is_directional_displacement(row: pd.Series, side: str) -> bool:
    """Return whether a 1-hour candle matches the EXP-018 displacement rule."""
    median_body = row["BodyMedianPrior"]
    body = row["BodySize"]
    if not np.isfinite(median_body) or median_body <= 0.0:
        return False
    if not np.isfinite(body) or body < BODY_MULTIPLE * median_body:
        return False
    if side == "High":
        return bool(
            row["Close"] < row["Open"] and row["CloseLocation"] <= LOWER_CLOSE_QUARTILE
        )
    return bool(
        row["Close"] > row["Open"] and row["CloseLocation"] >= UPPER_CLOSE_QUARTILE
    )


def find_displacement_for_sweep(
    sweep: pd.Series,
    bars_1h: pd.DataFrame,
    close_ns_1h: np.ndarray,
) -> dict[str, Any]:
    """Find the first qualifying displacement candle within 3 bars after a sweep."""
    event_ns = int(pd.Timestamp(sweep["CloseTime"]).value)
    start_idx = int(np.searchsorted(close_ns_1h, event_ns, side="right"))
    stop_idx = min(start_idx + MAX_CONFIRMATION_BARS, len(bars_1h))
    if start_idx >= len(bars_1h):
        return {"Confirmed": False, "MissReason": "NO_FORWARD_BARS"}

    for idx in range(start_idx, stop_idx):
        candidate = bars_1h.iloc[idx]
        if _is_directional_displacement(candidate, str(sweep["Side"])):
            return {
                "Confirmed": True,
                "MissReason": "NONE",
                "DisplacementIndex": idx,
                "DisplacementTime": candidate["CloseTime"],
                "DisplacementOpen": float(candidate["Open"]),
                "DisplacementHigh": float(candidate["High"]),
                "DisplacementLow": float(candidate["Low"]),
                "DisplacementClose": float(candidate["Close"]),
                "DisplacementBody": float(candidate["BodySize"]),
                "BodyMedianPrior": float(candidate["BodyMedianPrior"]),
                "CloseLocation": float(candidate["CloseLocation"]),
                "DelayBars": idx - start_idx + 1,
            }
    return {
        "Confirmed": False,
        "MissReason": f"NO_DISPLACEMENT_WITHIN_{MAX_CONFIRMATION_BARS}_BARS",
    }


def build_displacement_entries(
    sweeps: pd.DataFrame,
    bars_1h: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build displacement-confirmed entry rows at displacement-close timing."""
    close_ns_1h = bars_1h["CloseTime"].values.astype(np.int64)
    entries: list[dict[str, Any]] = []
    misses: list[dict[str, Any]] = []
    for _, sweep in sweeps[sweeps["EventType"] == "Sweep"].iterrows():
        confirmation = find_displacement_for_sweep(sweep, bars_1h, close_ns_1h)
        if not confirmation["Confirmed"]:
            misses.append(
                {
                    "NYDate": sweep["NYDate"],
                    "Segment": sweep["Segment"],
                    "SweepTime": sweep["CloseTime"],
                    "Side": sweep["Side"],
                    "LevelType": sweep["LevelType"],
                    "Confirmed": False,
                    "MissReason": confirmation["MissReason"],
                }
            )
            continue
        stop = float(sweep["Stop"])
        entry = float(confirmation["DisplacementClose"])
        risk = abs(stop - entry)
        entries.append(
            {
                "NYDate": sweep["NYDate"],
                "Segment": sweep["Segment"],
                "LevelType": sweep["LevelType"],
                "Side": sweep["Side"],
                "SweepTime": sweep["CloseTime"],
                "DisplacementTime": confirmation["DisplacementTime"],
                "DisplacementIndex": int(confirmation["DisplacementIndex"]),
                "DelayBars": int(confirmation["DelayBars"]),
                "EntryTime": confirmation["DisplacementTime"],
                "Entry": entry,
                "Stop": stop,
                "OriginalSweepBuffer": float(sweep["Buffer"]),
                "Risk1R": risk,
                "RiskFeasible": bool(risk >= float(sweep["Buffer"])),
            }
        )
    return pd.DataFrame(entries), pd.DataFrame(misses)


# Candidate A breaker label


def _find_last_opposite_candle(
    side: str,
    before_ns: int,
    close_ns_1h: np.ndarray,
    bars_1h: pd.DataFrame,
) -> tuple[float, float, pd.Timestamp] | None:
    """Return the last opposite-direction candle before the displacement."""
    before_idx = int(np.searchsorted(close_ns_1h, before_ns, side="left"))
    search_start = max(0, before_idx - CAND_A_LOOKBACK_BARS)
    for idx in range(before_idx - 1, search_start - 1, -1):
        bar = bars_1h.iloc[idx]
        is_bullish = float(bar["Close"]) > float(bar["Open"])
        is_bearish = float(bar["Close"]) < float(bar["Open"])
        if side == "High" and is_bullish:
            return float(bar["Low"]), float(bar["High"]), bar["CloseTime"]
        if side == "Low" and is_bearish:
            return float(bar["Low"]), float(bar["High"]), bar["CloseTime"]
    return None


def _close_invalidates_setup(side: str, close: float, stop: float) -> bool:
    """Return True when a 1-hour close crosses the original sweep stop."""
    return close >= stop if side == "High" else close <= stop


def _find_cand_a_breaker(
    ob_low: float,
    ob_high: float,
    side: str,
    disp_ns: int,
    stop: float,
    close_ns_1h: np.ndarray,
    bars_1h: pd.DataFrame,
) -> dict[str, Any] | None:
    """Find the first Candidate A close-through before invalidation."""
    start_idx = int(np.searchsorted(close_ns_1h, disp_ns, side="right"))
    stop_idx = min(start_idx + MAX_BREAKER_DELAY, len(bars_1h))
    for idx in range(start_idx, stop_idx):
        bar = bars_1h.iloc[idx]
        close = float(bar["Close"])
        if _close_invalidates_setup(side, close, stop):
            return {
                "InvalidatedBeforeBreaker": True,
                "InvalidationTime": bar["CloseTime"],
                "DelayBars": idx - start_idx + 1,
            }
        if side == "High" and close < ob_low:
            return {
                "BreakerTime": bar["CloseTime"],
                "BreakerClose": close,
                "DelayBars": idx - start_idx + 1,
                "InvalidatedBeforeBreaker": False,
            }
        if side == "Low" and close > ob_high:
            return {
                "BreakerTime": bar["CloseTime"],
                "BreakerClose": close,
                "DelayBars": idx - start_idx + 1,
                "InvalidatedBeforeBreaker": False,
            }
    return None


def label_breaker(entries: pd.DataFrame, bars_1h: pd.DataFrame) -> pd.DataFrame:
    """Add Candidate A breaker labels to displacement entries."""
    if entries.empty:
        return entries
    close_ns_1h = bars_1h["CloseTime"].values.astype(np.int64)
    rows: list[dict[str, Any]] = []
    for _, row in entries.iterrows():
        disp_ns = int(pd.Timestamp(row["DisplacementTime"]).value)
        side = str(row["Side"])
        ob = _find_last_opposite_candle(side, disp_ns, close_ns_1h, bars_1h)
        if ob is None:
            rows.append(
                {
                    "OBTime": pd.NaT,
                    "OBLow": np.nan,
                    "OBHigh": np.nan,
                    "BreakerConfirmed": False,
                    "BreakerTime": pd.NaT,
                    "BreakerDelayBars": np.nan,
                    "MissReason": "NO_OPPOSITE_CANDLE",
                }
            )
            continue
        ob_low, ob_high, ob_time = ob
        breaker = _find_cand_a_breaker(
            ob_low,
            ob_high,
            side,
            disp_ns,
            float(row["Stop"]),
            close_ns_1h,
            bars_1h,
        )
        if breaker is None:
            rows.append(
                {
                    "OBTime": ob_time,
                    "OBLow": ob_low,
                    "OBHigh": ob_high,
                    "BreakerConfirmed": False,
                    "BreakerTime": pd.NaT,
                    "BreakerDelayBars": np.nan,
                    "MissReason": "NO_BREAKER_WITHIN_WINDOW",
                }
            )
        elif breaker.get("InvalidatedBeforeBreaker", False):
            rows.append(
                {
                    "OBTime": ob_time,
                    "OBLow": ob_low,
                    "OBHigh": ob_high,
                    "BreakerConfirmed": False,
                    "BreakerTime": pd.NaT,
                    "BreakerDelayBars": np.nan,
                    "MissReason": "INVALIDATED_BEFORE_BREAKER",
                }
            )
        else:
            rows.append(
                {
                    "OBTime": ob_time,
                    "OBLow": ob_low,
                    "OBHigh": ob_high,
                    "BreakerConfirmed": True,
                    "BreakerTime": breaker["BreakerTime"],
                    "BreakerDelayBars": int(breaker["DelayBars"]),
                    "MissReason": "NONE",
                }
            )
    label_df = pd.DataFrame(rows, index=entries.index)
    return pd.concat([entries, label_df], axis=1)


# Outcomes on real 1-minute prices


def _walk_target_stop(
    highs: np.ndarray,
    lows: np.ndarray,
    target: float,
    stop: float,
    is_bearish: bool,
) -> tuple[bool, bool, bool]:
    """Return target/stop state over ordered forward bars."""
    for idx in range(highs.size):
        high = float(highs[idx])
        low = float(lows[idx])
        target_hit = (low <= target) if is_bearish else (high >= target)
        stop_hit = (high >= stop) if is_bearish else (low <= stop)
        if target_hit and stop_hit:
            return False, False, True
        if target_hit:
            return True, False, False
        if stop_hit:
            return False, True, False
    return False, False, False


def _outcomes_for_event(
    entry: pd.Series,
    close_ns: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
) -> dict[str, Any]:
    """Compute 60-minute outcomes using only bars after the entry timestamp."""
    entry_price = float(entry["Entry"])
    risk = float(entry["Risk1R"])
    stop = float(entry["Stop"])
    is_bearish = entry["Side"] == "High"

    nan_out = {
        "MFE_R_60m": np.nan,
        "MAE_R_60m": np.nan,
        "Return_R_60m": np.nan,
        "Hit1R_60m": np.nan,
        "Hit2R_60m": np.nan,
        "LogReturn_60m": np.nan,
        "Ambiguous60": False,
    }
    if not np.isfinite(risk) or risk <= 0.0:
        return nan_out

    entry_ns = int(pd.Timestamp(entry["EntryTime"]).value)
    start_idx = int(np.searchsorted(close_ns, entry_ns, side="right"))
    end_ns = entry_ns + PRIMARY_HORIZON * 60 * 10**9
    end_idx = int(np.searchsorted(close_ns, end_ns, side="right"))
    h_highs = highs[start_idx:end_idx]
    h_lows = lows[start_idx:end_idx]
    h_closes = closes[start_idx:end_idx]
    if h_highs.size == 0:
        return nan_out

    mfe = (
        entry_price - float(np.min(h_lows))
        if is_bearish
        else float(np.max(h_highs)) - entry_price
    )
    mae = (
        float(np.max(h_highs)) - entry_price
        if is_bearish
        else entry_price - float(np.min(h_lows))
    )
    end_close = float(h_closes[-1])
    realized = entry_price - end_close if is_bearish else end_close - entry_price
    target_1r = entry_price - risk if is_bearish else entry_price + risk
    target_2r = entry_price - 2.0 * risk if is_bearish else entry_price + 2.0 * risk
    hit_1r, _, amb_1r = _walk_target_stop(h_highs, h_lows, target_1r, stop, is_bearish)
    hit_2r, _, amb_2r = _walk_target_stop(h_highs, h_lows, target_2r, stop, is_bearish)

    log_return = np.nan
    if entry_price > 0.0 and end_close > 0.0:
        log_return = (
            np.log(entry_price / end_close)
            if is_bearish
            else np.log(end_close / entry_price)
        )

    return {
        "MFE_R_60m": max(0.0, mfe) / risk,
        "MAE_R_60m": max(0.0, mae) / risk,
        "Return_R_60m": realized / risk,
        "Hit1R_60m": np.nan if amb_1r else float(hit_1r),
        "Hit2R_60m": np.nan if amb_2r else float(hit_2r),
        "LogReturn_60m": float(log_return) if np.isfinite(log_return) else np.nan,
        "Ambiguous60": bool(amb_1r or amb_2r),
    }


def append_outcomes(entries: pd.DataFrame, bars_1m: pd.DataFrame) -> pd.DataFrame:
    """Append real-price outcome columns to displacement entries."""
    close_ns = bars_1m["CloseTime"].values.astype(np.int64)
    highs = bars_1m["High"].to_numpy(dtype=float)
    lows = bars_1m["Low"].to_numpy(dtype=float)
    closes = bars_1m["Close"].to_numpy(dtype=float)
    rows: list[dict[str, Any]] = []
    for _, entry in entries.iterrows():
        outcome = _outcomes_for_event(entry, close_ns, highs, lows, closes)
        rows.append({**entry.to_dict(), **outcome})
    return pd.DataFrame(rows)


# Counts and references


def event_waterfall(
    sweeps: pd.DataFrame,
    entries_with_outcomes: pd.DataFrame,
) -> pd.DataFrame:
    """Per-segment event-count waterfall."""
    rows: list[dict[str, Any]] = []
    for segment in ("Train", "Test"):
        seg_sweeps = sweeps[
            (sweeps["Segment"] == segment) & (sweeps["EventType"] == "Sweep")
        ]
        seg_entries = entries_with_outcomes[entries_with_outcomes["Segment"] == segment]
        sweep_n = len(seg_sweeps)
        disp_n = len(seg_entries)
        breaker_n = (
            int(seg_entries["BreakerConfirmed"].sum()) if not seg_entries.empty else 0
        )
        feasible_baseline = (
            int(seg_entries["RiskFeasible"].sum()) if not seg_entries.empty else 0
        )
        feasible_breaker = (
            int((seg_entries["BreakerConfirmed"] & seg_entries["RiskFeasible"]).sum())
            if not seg_entries.empty
            else 0
        )
        rows.append(
            {
                "Segment": segment,
                "SweepCount": sweep_n,
                "DisplacementCount": disp_n,
                "BreakerLabeledCount": breaker_n,
                "RiskFeasibleBaselineCount": feasible_baseline,
                "RiskFeasibleBreakerCount": feasible_breaker,
                "BreakerFloorMet": feasible_breaker >= MIN_EVENTS_PER_SEGMENT,
            }
        )
    return pd.DataFrame(rows)


def load_exp031_primary_reference() -> pd.DataFrame:
    """Load EXP-031 15-minute USTEC Return_R_60m primary bootstrap reference."""
    path = EXP031_RESULTS_DIR / "bootstrap_primary.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required EXP-031 reference is missing: {path}")
    reference = pd.read_csv(path)
    required = {"Segment", "Diff", "CILow", "CIHigh", "N", "BreakerN"}
    missing = required - set(reference.columns)
    if missing:
        raise ValueError(f"EXP-031 primary reference missing columns: {sorted(missing)}")
    if set(reference["Segment"]) != {"Train", "Test"}:
        raise ValueError("EXP-031 primary reference must include Train and Test")
    return reference.copy()


def load_exp031_waterfall_reference() -> pd.DataFrame:
    """Load EXP-031 displacement and feasible-breaker counts for retention checks."""
    path = EXP031_RESULTS_DIR / "event_waterfall.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required EXP-031 waterfall reference is missing: {path}")
    reference = pd.read_csv(path)
    required = {"Segment", "DisplacementCount", "RiskFeasibleBreakerCount"}
    missing = required - set(reference.columns)
    if missing:
        raise ValueError(f"EXP-031 waterfall reference missing columns: {sorted(missing)}")
    if set(reference["Segment"]) != {"Train", "Test"}:
        raise ValueError("EXP-031 waterfall reference must include Train and Test")
    return reference.copy()


def load_exp023_return_reference() -> pd.DataFrame:
    """Load EXP-023 USTEC Return_R_60m breaker-minus-baseline reference."""
    path = EXP023_RESULTS_DIR / "bootstrap_comparison.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required EXP-023 reference is missing: {path}")
    reference = pd.read_csv(path)
    required = {
        "Instrument",
        "Segment",
        "Metric",
        "MeanDiff",
        "CI_Lo",
        "CI_Hi",
        "CIExcludesZero",
    }
    missing = required - set(reference.columns)
    if missing:
        raise ValueError(f"EXP-023 bootstrap reference missing columns: {sorted(missing)}")
    ustec_return = reference[
        (reference["Instrument"] == INSTRUMENT)
        & (reference["Metric"] == "Return_R_60m")
    ].copy()
    if set(ustec_return["Segment"]) != {"Train", "Test"}:
        raise ValueError("EXP-023 USTEC Return_R_60m reference must include Train and Test")
    return ustec_return


def retention_vs_exp031(
    entries_with_outcomes: pd.DataFrame,
    exp031_waterfall: pd.DataFrame,
) -> dict[str, Any]:
    """Compute 1-hour / 15-minute retention ratios from structured EXP-031 rows."""
    by_segment: list[dict[str, Any]] = []
    for segment in ("Train", "Test"):
        ref_row = exp031_waterfall[exp031_waterfall["Segment"] == segment]
        if ref_row.empty:
            raise ValueError(f"Missing EXP-031 {segment} retention reference")
        ref_disp = int(ref_row["DisplacementCount"].iloc[0])
        ref_breaker = int(ref_row["RiskFeasibleBreakerCount"].iloc[0])
        current_segment = entries_with_outcomes[
            entries_with_outcomes["Segment"] == segment
        ]
        current_disp = int(len(current_segment))
        current_breaker = (
            int(
                (
                    current_segment["BreakerConfirmed"]
                    & current_segment["RiskFeasible"]
                ).sum()
            )
            if not current_segment.empty
            else 0
        )
        disp_ratio = current_disp / ref_disp if ref_disp > 0 else np.nan
        breaker_ratio = current_breaker / ref_breaker if ref_breaker > 0 else np.nan
        by_segment.append(
            {
                "Segment": segment,
                "EXP031DisplacementCount15m": ref_disp,
                "EXP032DisplacementCount1h": current_disp,
                "DisplacementRetentionRatio": disp_ratio,
                "EXP031FeasibleBreakerCount15m": ref_breaker,
                "EXP032FeasibleBreakerCount1h": current_breaker,
                "FeasibleBreakerRetentionRatio": breaker_ratio,
                "ResolutionCostLimited": bool(
                    np.isfinite(disp_ratio) and disp_ratio < RETENTION_LIMIT
                ),
            }
        )

    ref_disp_total = int(sum(row["EXP031DisplacementCount15m"] for row in by_segment))
    current_disp_total = int(sum(row["EXP032DisplacementCount1h"] for row in by_segment))
    ref_breaker_total = int(sum(row["EXP031FeasibleBreakerCount15m"] for row in by_segment))
    current_breaker_total = int(sum(row["EXP032FeasibleBreakerCount1h"] for row in by_segment))
    disp_total_ratio = current_disp_total / ref_disp_total if ref_disp_total > 0 else np.nan
    breaker_total_ratio = (
        current_breaker_total / ref_breaker_total if ref_breaker_total > 0 else np.nan
    )
    segment_limited = any(row["ResolutionCostLimited"] for row in by_segment)
    total_limited = bool(
        np.isfinite(disp_total_ratio) and disp_total_ratio < RETENTION_LIMIT
    )
    return {
        "exp031_displacement_count_15m": ref_disp_total,
        "exp032_displacement_count_1h": current_disp_total,
        "displacement_retention_ratio": disp_total_ratio,
        "exp031_feasible_breaker_count_15m": ref_breaker_total,
        "exp032_feasible_breaker_count_1h": current_breaker_total,
        "feasible_breaker_retention_ratio": breaker_total_ratio,
        "resolution_cost_limited": bool(segment_limited or total_limited),
        "by_segment": by_segment,
    }


def build_reference_comparison(
    primary: pd.DataFrame,
    exp031_reference: pd.DataFrame,
    exp023_reference: pd.DataFrame,
) -> pd.DataFrame:
    """Join EXP-032 effects to EXP-031 and EXP-023 reference effects."""
    exp031 = exp031_reference.rename(
        columns={
            "Diff": "EXP031PointDiff",
            "CILow": "EXP031CILow",
            "CIHigh": "EXP031CIHigh",
            "N": "EXP031N",
            "BreakerN": "EXP031BreakerN",
        }
    )[["Segment", "EXP031PointDiff", "EXP031CILow", "EXP031CIHigh", "EXP031N", "EXP031BreakerN"]]
    exp023 = exp023_reference.rename(
        columns={
            "MeanDiff": "EXP023PointDiff",
            "CI_Lo": "EXP023CILow",
            "CI_Hi": "EXP023CIHigh",
            "CIExcludesZero": "EXP023CIExcludesZero",
        }
    )[["Segment", "EXP023PointDiff", "EXP023CILow", "EXP023CIHigh", "EXP023CIExcludesZero"]]
    comparison = primary.merge(exp031, on="Segment", how="left").merge(
        exp023, on="Segment", how="left"
    )
    required = [
        "EXP031PointDiff",
        "EXP031CILow",
        "EXP031CIHigh",
        "EXP023PointDiff",
        "EXP023CILow",
        "EXP023CIHigh",
    ]
    if comparison[required].isna().any().any():
        raise ValueError("Missing reference values in EXP-032 comparison")

    comparison["SameDirectionAsEXP031"] = comparison["Diff"] * comparison["EXP031PointDiff"] > 0.0
    comparison["EXP031HalfMagnitudeGate"] = 0.5 * comparison["EXP031PointDiff"].abs()
    comparison["MeetsEXP031HalfGate"] = (
        comparison["SameDirectionAsEXP031"]
        & (comparison["Diff"].abs() >= comparison["EXP031HalfMagnitudeGate"])
    )
    comparison["SameDirectionAsEXP023"] = comparison["Diff"] * comparison["EXP023PointDiff"] > 0.0
    comparison["EXP023HalfReference"] = 0.5 * comparison["EXP023PointDiff"].abs()
    comparison["MeetsEXP023HalfReference"] = (
        comparison["SameDirectionAsEXP023"]
        & (comparison["Diff"].abs() >= comparison["EXP023HalfReference"])
    )
    return comparison


def summarize_outcomes(entries: pd.DataFrame) -> pd.DataFrame:
    """Summarize scoped trade-quality metrics by baseline and breaker class."""
    rows: list[dict[str, Any]] = []
    for segment in ("Train", "Test"):
        seg = entries[entries["Segment"] == segment]
        for event_class, group in (
            ("Baseline", seg),
            ("Breaker", seg[seg["BreakerConfirmed"]]),
        ):
            feasible = group[group["RiskFeasible"]]
            return_r = feasible["Return_R_60m"].dropna()
            mae_r = feasible["MAE_R_60m"].dropna()
            mfe_r = feasible["MFE_R_60m"].dropna()
            hit_1r = feasible["Hit1R_60m"].dropna()
            hit_2r = feasible["Hit2R_60m"].dropna()
            log_ret = feasible["LogReturn_60m"].dropna()
            drawdown_adjusted = (
                feasible["Return_R_60m"] - feasible["MAE_R_60m"]
                if not feasible.empty
                else pd.Series(dtype=float)
            ).dropna()
            rows.append(
                {
                    "Segment": segment,
                    "EventClass": event_class,
                    "TradeCount": int(len(group)),
                    "RiskFeasibleCount": int(len(feasible)),
                    "MeanReturn_R": float(return_r.mean()) if not return_r.empty else np.nan,
                    "MeanMAE_R": float(mae_r.mean()) if not mae_r.empty else np.nan,
                    "MeanMFE_R": float(mfe_r.mean()) if not mfe_r.empty else np.nan,
                    "MeanDrawdownAdjusted_R": (
                        float(drawdown_adjusted.mean())
                        if not drawdown_adjusted.empty
                        else np.nan
                    ),
                    "WinRateHit1R": float(hit_1r.mean()) if not hit_1r.empty else np.nan,
                    "WinRateHit2R": float(hit_2r.mean()) if not hit_2r.empty else np.nan,
                    "MeanLogReturn_60m": (
                        float(log_ret.mean()) if not log_ret.empty else np.nan
                    ),
                }
            )
    return pd.DataFrame(rows)


# Bootstrap and verdict


def _label_stratified_bootstrap(
    values: np.ndarray,
    breaker_mask: np.ndarray,
    feasible_mask: np.ndarray,
    n_reps: int,
    seed: int,
) -> tuple[float, float, float, float, float]:
    """Resample displacement events while preserving the breaker subset relation."""
    if values.size == 0:
        return float("nan"), float("nan"), float("nan"), float("nan"), float("nan")
    finite = np.isfinite(values) & feasible_mask
    values = values[finite]
    breaker_mask = breaker_mask[finite]
    if values.size == 0 or breaker_mask.sum() == 0:
        return float("nan"), float("nan"), float("nan"), float("nan"), float("nan")

    baseline_point = float(values.mean())
    breaker_point = float(values[breaker_mask].mean())
    diff_point = breaker_point - baseline_point

    rng = np.random.default_rng(seed)
    diffs = np.empty(n_reps, dtype=float)
    indices = np.arange(values.size)
    for rep in range(n_reps):
        pick = rng.choice(indices, size=indices.size, replace=True)
        sample_values = values[pick]
        sample_breaker = breaker_mask[pick]
        if not sample_breaker.any():
            diffs[rep] = np.nan
            continue
        diffs[rep] = sample_values[sample_breaker].mean() - sample_values.mean()
    finite_diffs = diffs[np.isfinite(diffs)]
    if finite_diffs.size < n_reps // 4:
        return baseline_point, breaker_point, diff_point, float("nan"), float("nan")
    ci_low = float(np.quantile(finite_diffs, 0.025))
    ci_high = float(np.quantile(finite_diffs, 0.975))
    return baseline_point, breaker_point, diff_point, ci_low, ci_high


def bootstrap_primary(entries: pd.DataFrame) -> pd.DataFrame:
    """Bootstrap Return_R_60m difference, breaker minus baseline, per segment."""
    rows: list[dict[str, Any]] = []
    for segment in ("Train", "Test"):
        seg = entries[entries["Segment"] == segment]
        if seg.empty:
            rows.append(
                {
                    "Segment": segment,
                    "BaselineMean": np.nan,
                    "BreakerMean": np.nan,
                    "Diff": np.nan,
                    "CILow": np.nan,
                    "CIHigh": np.nan,
                    "N": 0,
                    "BreakerN": 0,
                }
            )
            continue
        values = seg["Return_R_60m"].to_numpy(dtype=float)
        breaker_mask = seg["BreakerConfirmed"].to_numpy(dtype=bool)
        feasible_mask = seg["RiskFeasible"].to_numpy(dtype=bool)
        baseline_pt, breaker_pt, diff_pt, ci_low, ci_high = _label_stratified_bootstrap(
            values, breaker_mask, feasible_mask, BOOTSTRAP_REPS, BOOTSTRAP_SEED
        )
        rows.append(
            {
                "Segment": segment,
                "BaselineMean": baseline_pt,
                "BreakerMean": breaker_pt,
                "Diff": diff_pt,
                "CILow": ci_low,
                "CIHigh": ci_high,
                "N": int(feasible_mask.sum()),
                "BreakerN": int((breaker_mask & feasible_mask).sum()),
            }
        )
    return pd.DataFrame(rows)


def bootstrap_secondary(entries: pd.DataFrame) -> pd.DataFrame:
    """Bootstrap secondary diagnostics: MAE_R_60m and MFE_R_60m differences."""
    rows: list[dict[str, Any]] = []
    for metric in ("MAE_R_60m", "MFE_R_60m"):
        for segment in ("Train", "Test"):
            seg = entries[entries["Segment"] == segment]
            if seg.empty:
                continue
            values = seg[metric].to_numpy(dtype=float)
            breaker_mask = seg["BreakerConfirmed"].to_numpy(dtype=bool)
            feasible_mask = seg["RiskFeasible"].to_numpy(dtype=bool)
            base_pt, breaker_pt, diff_pt, ci_low, ci_high = _label_stratified_bootstrap(
                values, breaker_mask, feasible_mask, BOOTSTRAP_REPS, BOOTSTRAP_SEED
            )
            rows.append(
                {
                    "Metric": metric,
                    "Segment": segment,
                    "BaselineMean": base_pt,
                    "BreakerMean": breaker_pt,
                    "Diff": diff_pt,
                    "CILow": ci_low,
                    "CIHigh": ci_high,
                }
            )
    return pd.DataFrame(rows)


def evaluate_verdict(
    waterfall: pd.DataFrame,
    primary: pd.DataFrame,
    retention: dict[str, Any],
    reference_comparison: pd.DataFrame,
) -> dict[str, Any]:
    """Map hard gates to the EXP-032 Branch A continuation verdict."""
    test_row = primary[primary["Segment"] == "Test"]
    train_row = primary[primary["Segment"] == "Train"]
    test_ref = reference_comparison[reference_comparison["Segment"] == "Test"]

    breaker_train_floor = bool(
        waterfall[waterfall["Segment"] == "Train"]["BreakerFloorMet"].all()
    )
    breaker_test_floor = bool(
        waterfall[waterfall["Segment"] == "Test"]["BreakerFloorMet"].all()
    )
    resolution_limited = bool(retention.get("resolution_cost_limited", False))

    test_point = float(test_row["Diff"].iloc[0]) if not test_row.empty else float("nan")
    test_ci_low = float(test_row["CILow"].iloc[0]) if not test_row.empty else float("nan")
    test_ci_high = float(test_row["CIHigh"].iloc[0]) if not test_row.empty else float("nan")
    train_point = float(train_row["Diff"].iloc[0]) if not train_row.empty else float("nan")
    exp031_test_point = (
        float(test_ref["EXP031PointDiff"].iloc[0]) if not test_ref.empty else float("nan")
    )
    exp031_half_gate = (
        float(test_ref["EXP031HalfMagnitudeGate"].iloc[0])
        if not test_ref.empty
        else float("nan")
    )
    exp023_test_point = (
        float(test_ref["EXP023PointDiff"].iloc[0]) if not test_ref.empty else float("nan")
    )
    exp023_half_reference = (
        float(test_ref["EXP023HalfReference"].iloc[0])
        if not test_ref.empty
        else float("nan")
    )

    test_ci_excludes_zero_positive = (
        np.isfinite(test_ci_low) and np.isfinite(test_ci_high) and test_ci_low > 0.0
    )
    train_point_positive = np.isfinite(train_point) and train_point > 0.0
    test_point_positive = np.isfinite(test_point) and test_point > 0.0
    meets_exp031_gate = (
        np.isfinite(test_point)
        and np.isfinite(exp031_half_gate)
        and test_point >= exp031_half_gate
    )
    meets_exp023_half_reference = (
        np.isfinite(test_point)
        and np.isfinite(exp023_half_reference)
        and test_point >= exp023_half_reference
    )

    if not (breaker_train_floor and breaker_test_floor):
        verdict = "INCONCLUSIVE"
        reason = "RISK_FEASIBLE_BREAKER_FLOOR_NOT_MET"
    elif resolution_limited:
        verdict = "INCONCLUSIVE"
        reason = "RETENTION_VS_EXP031_BELOW_30PCT"
    elif not train_point_positive:
        verdict = "AGAINST"
        reason = "TRAIN_RETURN_DIFF_NON_POSITIVE"
    elif not test_point_positive:
        verdict = "AGAINST"
        reason = "TEST_RETURN_DIFF_NON_POSITIVE"
    elif not np.isfinite(exp031_half_gate):
        verdict = "INCONCLUSIVE"
        reason = "EXP031_REFERENCE_UNAVAILABLE"
    elif not (np.isfinite(test_ci_low) and np.isfinite(test_ci_high)):
        verdict = "INCONCLUSIVE"
        reason = "TEST_CI_UNDEFINED"
    elif not test_ci_excludes_zero_positive:
        verdict = "AGAINST"
        reason = "TEST_CI_INCLUDES_ZERO"
    elif not meets_exp031_gate:
        verdict = "AGAINST"
        reason = "TEST_BELOW_EXP031_50PCT_MAGNITUDE_GATE"
    else:
        verdict = "FOR"
        reason = "ALL_EXP032_HARD_GATES_PASS"

    return {
        "verdict": verdict,
        "reason": reason,
        "test_point_diff": test_point,
        "test_ci_low": test_ci_low,
        "test_ci_high": test_ci_high,
        "train_point_diff": train_point,
        "exp031_test_point_diff": exp031_test_point,
        "exp031_half_magnitude_gate": exp031_half_gate,
        "exp023_test_point_diff": exp023_test_point,
        "exp023_half_reference_nonbinding": exp023_half_reference,
        "train_point_positive": train_point_positive,
        "test_point_positive": test_point_positive,
        "test_ci_excludes_zero_positive": test_ci_excludes_zero_positive,
        "meets_exp031_half_gate": meets_exp031_gate,
        "meets_exp023_half_reference_nonbinding": meets_exp023_half_reference,
        "breaker_train_floor_met": breaker_train_floor,
        "breaker_test_floor_met": breaker_test_floor,
        "resolution_cost_limited": resolution_limited,
        "retention": retention,
    }


# JSON, plotting, and output


def _json_safe(value: Any) -> Any:
    """Convert numpy/pandas values to JSON-safe scalars."""
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    if pd.isna(value):
        return None
    return value


def plot_waterfall(waterfall: pd.DataFrame, save_path: Path) -> None:
    """Plot sweep -> displacement -> breaker-labeled -> feasible event counts."""
    melt = waterfall.melt(
        id_vars=["Segment"],
        value_vars=[
            "SweepCount",
            "DisplacementCount",
            "BreakerLabeledCount",
            "RiskFeasibleBreakerCount",
        ],
        var_name="Stage",
        value_name="Count",
    )
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=melt, x="Stage", y="Count", hue="Segment", ax=ax)
    ax.axhline(MIN_EVENTS_PER_SEGMENT, color="darkred", linestyle="--", linewidth=1)
    ax.set_title("EXP-032 USTEC 1h Event-Count Waterfall")
    ax.set_xlabel("")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_expectancy(
    primary: pd.DataFrame,
    reference_comparison: pd.DataFrame,
    save_path: Path,
) -> None:
    """Plot 1-hour expectancy and EXP-031/EXP-023 reference differences."""
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    ax = axes[0]
    x = np.arange(len(primary))
    width = 0.35
    ax.bar(x - width / 2, primary["BaselineMean"], width, label="Baseline")
    ax.bar(x + width / 2, primary["BreakerMean"], width, label="Breaker")
    ax.set_xticks(x)
    ax.set_xticklabels(primary["Segment"])
    ax.axhline(0.0, color="black", linewidth=1)
    ax.set_ylabel("Mean Return_R_60m")
    ax.set_title("EXP-032 USTEC 1h Expectancy")
    ax.legend()

    diff_ax = axes[1]
    yerr_032 = [
        (primary["Diff"] - primary["CILow"]).clip(lower=0).fillna(0),
        (primary["CIHigh"] - primary["Diff"]).clip(lower=0).fillna(0),
    ]
    diff_ax.errorbar(
        x - 0.16,
        primary["Diff"],
        yerr=yerr_032,
        fmt="o",
        color="darkblue",
        ecolor="steelblue",
        capsize=4,
        label="EXP-032 1h",
    )

    ref = reference_comparison.set_index("Segment").reindex(primary["Segment"]).reset_index()
    yerr_031 = [
        (ref["EXP031PointDiff"] - ref["EXP031CILow"]).clip(lower=0).fillna(0),
        (ref["EXP031CIHigh"] - ref["EXP031PointDiff"]).clip(lower=0).fillna(0),
    ]
    diff_ax.errorbar(
        x,
        ref["EXP031PointDiff"],
        yerr=yerr_031,
        fmt="s",
        color="darkgreen",
        ecolor="seagreen",
        capsize=4,
        label="EXP-031 15m",
    )
    yerr_023 = [
        (ref["EXP023PointDiff"] - ref["EXP023CILow"]).clip(lower=0).fillna(0),
        (ref["EXP023CIHigh"] - ref["EXP023PointDiff"]).clip(lower=0).fillna(0),
    ]
    diff_ax.errorbar(
        x + 0.16,
        ref["EXP023PointDiff"],
        yerr=yerr_023,
        fmt="^",
        color="darkorange",
        ecolor="orange",
        capsize=4,
        label="EXP-023 1m",
    )
    diff_ax.axhline(0.0, color="black", linewidth=1)
    diff_ax.set_xticks(x)
    diff_ax.set_xticklabels(primary["Segment"])
    diff_ax.set_ylabel("Breaker minus baseline Return_R_60m")
    diff_ax.set_title("Return_R_60m Difference vs References")
    diff_ax.legend()
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_r_distribution(entries: pd.DataFrame, save_path: Path) -> None:
    """Plot Test-segment R-multiple distribution, baseline-only vs breaker."""
    test = entries[(entries["Segment"] == "Test") & entries["RiskFeasible"]].copy()
    if test.empty:
        return
    test["Return_R_60m_Capped"] = test["Return_R_60m"].clip(
        lower=-PLOT_R_CAP,
        upper=PLOT_R_CAP,
    )
    test["EventClass"] = np.where(test["BreakerConfirmed"], "Breaker", "Baseline-Only")
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.boxplot(
        data=test,
        x="EventClass",
        y="Return_R_60m_Capped",
        order=["Baseline-Only", "Breaker"],
        showfliers=False,
        ax=ax,
    )
    sns.stripplot(
        data=test,
        x="EventClass",
        y="Return_R_60m_Capped",
        order=["Baseline-Only", "Breaker"],
        color="black",
        size=2,
        alpha=0.4,
        ax=ax,
    )
    ax.axhline(0.0, color="darkred", linewidth=1)
    ax.set_title("EXP-032 USTEC 1h Return_R_60m Distribution (Test, capped at +/-8R)")
    ax.set_xlabel("")
    ax.set_ylabel("Return in R")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_mae_proxy(secondary: pd.DataFrame, save_path: Path) -> None:
    """Plot breaker-minus-baseline MAE_R_60m difference by segment."""
    mae = secondary[secondary["Metric"] == "MAE_R_60m"].copy()
    if mae.empty:
        return
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(mae))
    yerr_lower = (mae["Diff"] - mae["CILow"]).clip(lower=0).fillna(0).to_numpy()
    yerr_upper = (mae["CIHigh"] - mae["Diff"]).clip(lower=0).fillna(0).to_numpy()
    ax.errorbar(
        x,
        mae["Diff"],
        yerr=[yerr_lower, yerr_upper],
        fmt="o",
        color="darkorange",
        ecolor="orange",
        capsize=4,
    )
    ax.axhline(0.0, color="black", linewidth=1)
    ax.set_xticks(x)
    ax.set_xticklabels(mae["Segment"])
    ax.set_ylabel("Breaker minus baseline MAE_R_60m")
    ax.set_title("EXP-032 USTEC 1h MAE_R_60m Difference With CI")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def write_outputs(
    sweeps: pd.DataFrame,
    entries: pd.DataFrame,
    waterfall: pd.DataFrame,
    outcome_summary: pd.DataFrame,
    primary: pd.DataFrame,
    secondary: pd.DataFrame,
    reference_comparison: pd.DataFrame,
    retention: dict[str, Any],
    coverage: dict[str, int],
    precision_step: float,
    verdict: dict[str, Any],
    plots_dir: Path,
    results_dir: Path,
) -> None:
    """Write tables, JSON, text summary, and plots."""
    sweeps.to_csv(results_dir / "sweep_events_1h.csv", index=False)
    entries.to_csv(results_dir / "displacement_entries_1h.csv", index=False)
    waterfall.to_csv(results_dir / "event_waterfall.csv", index=False)
    outcome_summary.to_csv(results_dir / "outcome_summary.csv", index=False)
    primary.to_csv(results_dir / "bootstrap_primary.csv", index=False)
    secondary.to_csv(results_dir / "bootstrap_secondary.csv", index=False)
    reference_comparison.to_csv(results_dir / "reference_comparison.csv", index=False)
    coverage_frame = pd.DataFrame([{**coverage, "price_precision_step": precision_step}])
    coverage_frame.to_csv(results_dir / "coverage_summary.csv", index=False)

    payload = {
        "experiment_id": "EXP-032",
        "title": "1-Hour USTEC Candidate A Breaker Magnitude Gate",
        "instrument": INSTRUMENT,
        "period_minutes": PERIOD_MINUTES,
        "buffer_atr_coefficient": BUFFER_ATR_COEFF,
        "max_confirmation_bars_1h": MAX_CONFIRMATION_BARS,
        "body_median_window_1h": BODY_MEDIAN_WINDOW,
        "max_breaker_delay_1h": MAX_BREAKER_DELAY,
        "cand_a_lookback_bars_1h": CAND_A_LOOKBACK_BARS,
        "primary_horizon_minutes": PRIMARY_HORIZON,
        "bootstrap_reps": BOOTSTRAP_REPS,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "min_events_per_segment": MIN_EVENTS_PER_SEGMENT,
        "retention_limit": RETENTION_LIMIT,
        "price_precision_step": precision_step,
        "coverage_diagnostics": coverage,
        "verdict_summary": verdict,
        "waterfall": waterfall.to_dict(orient="records"),
        "outcome_summary": outcome_summary.to_dict(orient="records"),
        "primary_bootstrap": primary.to_dict(orient="records"),
        "secondary_bootstrap": secondary.to_dict(orient="records"),
        "reference_comparison": reference_comparison.to_dict(orient="records"),
        "retention_vs_exp031": retention,
    }
    with (results_dir / "results.json").open("w", encoding="utf-8") as handle:
        json.dump(_json_safe(payload), handle, indent=2, default=str, allow_nan=False)

    with (results_dir / "numerical_summary.txt").open("w", encoding="utf-8") as handle:
        handle.write("EXP-032 1-Hour USTEC Candidate A Breaker Magnitude Gate\n")
        handle.write(f"Verdict: {verdict['verdict']} ({verdict['reason']})\n\n")
        handle.write("Event waterfall:\n")
        for row in waterfall.itertuples(index=False):
            handle.write(
                f"- {row.Segment}: sweep={row.SweepCount}, "
                f"displacement={row.DisplacementCount}, "
                f"breaker-labeled={row.BreakerLabeledCount}, "
                f"feasible-breaker={row.RiskFeasibleBreakerCount}, "
                f"floor={row.BreakerFloorMet}\n"
            )
        handle.write("\nPrimary bootstrap (breaker minus baseline Return_R_60m):\n")
        for row in primary.itertuples(index=False):
            handle.write(
                f"- {row.Segment}: baseline={row.BaselineMean:.4f}, "
                f"breaker={row.BreakerMean:.4f}, diff={row.Diff:.4f}, "
                f"CI=[{row.CILow:.4f}, {row.CIHigh:.4f}], "
                f"N={row.N}, BreakerN={row.BreakerN}\n"
            )
        handle.write("\nHard-gate references:\n")
        handle.write(
            f"- EXP-031 15m test diff={verdict['exp031_test_point_diff']:.4f}; "
            f"binding 50% gate={verdict['exp031_half_magnitude_gate']:.4f}\n"
        )
        handle.write(
            f"- EXP-023 1m test diff={verdict['exp023_test_point_diff']:.4f}; "
            f"non-binding 50% reference={verdict['exp023_half_reference_nonbinding']:.4f}\n"
        )
        handle.write("\nOutcome summary:\n")
        for row in outcome_summary.itertuples(index=False):
            handle.write(
                f"- {row.Segment} {row.EventClass}: trades={row.TradeCount}, "
                f"feasible={row.RiskFeasibleCount}, "
                f"returnR={row.MeanReturn_R:.4f}, "
                f"MAE_R={row.MeanMAE_R:.4f}, "
                f"MFE_R={row.MeanMFE_R:.4f}, "
                f"drawdown_adj_R={row.MeanDrawdownAdjusted_R:.4f}, "
                f"win1R={row.WinRateHit1R:.4f}, "
                f"logret={row.MeanLogReturn_60m:.6f}\n"
            )
        handle.write(
            f"\nRetention vs EXP-031 15m: "
            f"15m_displacement={retention['exp031_displacement_count_15m']}, "
            f"1h_displacement={retention['exp032_displacement_count_1h']}, "
            f"ratio={retention['displacement_retention_ratio']}\n"
        )

    plot_waterfall(waterfall, plots_dir / "01_event_waterfall.png")
    plot_expectancy(primary, reference_comparison, plots_dir / "02_expectancy.png")
    plot_r_distribution(entries, plots_dir / "03_r_distribution.png")
    plot_mae_proxy(secondary, plots_dir / "04_drawdown_proxy.png")


def run_experiment() -> None:
    """Execute the EXP-032 USTEC 1-hour breaker magnitude gate workflow."""
    plots_dir = EXP_DIR / "plots"
    results_dir = EXP_DIR / "results"
    plots_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    bars_1m, weekday_1h, levels, precision_step, coverage = load_data()
    LOGGER.info(
        "USTEC: 1m=%d, 1h=%d (dropped=%d)",
        coverage["source_bars_in"],
        coverage["aggregated_bars_out"],
        coverage["dropped_partial_window_bars"],
    )
    if weekday_1h.empty:
        raise ValueError("USTEC 1-hour frame is empty; cannot proceed.")

    sweeps = detect_sweeps(weekday_1h, levels, precision_step)
    entries, misses = build_displacement_entries(sweeps, weekday_1h)
    if entries.empty:
        raise ValueError("No displacement-confirmed sweeps on USTEC 1-hour series.")
    entries = label_breaker(entries, weekday_1h)
    entries = append_outcomes(entries, bars_1m)

    waterfall = event_waterfall(sweeps, entries)
    exp031_primary_reference = load_exp031_primary_reference()
    exp031_waterfall_reference = load_exp031_waterfall_reference()
    exp023_return_reference = load_exp023_return_reference()
    retention = retention_vs_exp031(entries, exp031_waterfall_reference)
    outcome_summary = summarize_outcomes(entries)
    primary = bootstrap_primary(entries)
    secondary = bootstrap_secondary(entries)
    reference_comparison = build_reference_comparison(
        primary,
        exp031_primary_reference,
        exp023_return_reference,
    )
    verdict = evaluate_verdict(waterfall, primary, retention, reference_comparison)

    misses.to_csv(results_dir / "displacement_misses_1h.csv", index=False)
    write_outputs(
        sweeps,
        entries,
        waterfall,
        outcome_summary,
        primary,
        secondary,
        reference_comparison,
        retention,
        coverage,
        precision_step,
        verdict,
        plots_dir,
        results_dir,
    )

    print("EXP-032 complete.")
    print(f"Verdict: {verdict['verdict']} ({verdict['reason']})")
    print(f"Plots:   {plots_dir}")
    print(f"Results: {results_dir}")


def main() -> None:
    """Entry point for manual execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_experiment()


if __name__ == "__main__":
    main()
