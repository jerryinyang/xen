"""
Experiment EXP-031: 15-Minute USTEC Breaker Chain
Implements the analysis plan from analysis-plan.md.

Applies the EXP-015 sweep, EXP-018 displacement, and EXP-022 Candidate A
breaker rules unchanged at the rule level to synthetic 15-minute USTEC bars
resampled from holdout-excluded 1-minute base bars. Outcomes are evaluated on
real 1-minute prices strictly after the displacement candle close; both the
displacement-only baseline and the Candidate A breaker-labeled subset enter
at displacement-close, matching EXP-023's canonical entry timing. The breaker
acts as a future-conditional label rather than a separate entry trigger.
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
EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-031"
EXP023_RESULTS_DIR = PYTHON_ROOT / "experiments" / "EXP-023" / "results"

INSTRUMENT = "USTEC"
PERIOD_MINUTES = 15
ATR_PERIOD = 14
BUFFER_ATR_COEFF = 0.05

# Displacement (EXP-018 rule, applied to 15m bars)
MAX_CONFIRMATION_BARS = 10
BODY_MEDIAN_WINDOW = 100
BODY_MULTIPLE = 1.5
LOWER_CLOSE_QUARTILE = 0.25
UPPER_CLOSE_QUARTILE = 0.75

# Candidate A breaker (EXP-022 rule, applied to 15m bars)
CAND_A_LOOKBACK_BARS = 30
MAX_BREAKER_DELAY = 120

# Outcomes and gates
PRIMARY_HORIZON = 60
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 42
MIN_EVENTS_PER_SEGMENT = 50
ON_LEVEL_MIN_MINUTE = OVERNIGHT_END_MINUTE
LEVEL_TYPES_HIGH = ["PDH", "ONH"]
LEVEL_TYPES_LOW = ["PDL", "ONL"]
RETENTION_LIMIT = 0.30
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


# ── Data loading ─────────────────────────────────────────────────────────────


def _add_atr_15m(frame_15m: pl.DataFrame) -> pl.DataFrame:
    """Add TrueRange and ATR14Prior on the 15-minute series.

    ATR is computed only from completed bars and shifted by 1 so the value is
    knowable strictly before the current bar close, matching the EXP-015 rule.
    """
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


def _add_body_metrics(frame_15m: pl.DataFrame) -> pl.DataFrame:
    """Add BodySize, CloseLocation, and BodyMedian100Prior on the 15-minute frame.

    BodySize is the absolute open-to-close range. CloseLocation is the close
    position within the candle range (0 = at low, 1 = at high). The body
    median is a 100-bar rolling median of BodySize shifted by 1 so each bar
    sees only completed prior bars.
    """
    body = (pl.col("Close") - pl.col("Open")).abs()
    candle_range = pl.col("High") - pl.col("Low")
    close_loc = (
        pl.when(candle_range > 0)
        .then((pl.col("Close") - pl.col("Low")) / candle_range)
        .otherwise(0.5)
    )
    return frame_15m.with_columns(
        body.alias("BodySize"),
        close_loc.alias("CloseLocation"),
    ).with_columns(
        pl.col("BodySize")
        .rolling_median(window_size=BODY_MEDIAN_WINDOW, min_samples=BODY_MEDIAN_WINDOW)
        .shift(1)
        .alias("BodyMedian100Prior")
    )


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, float, dict[str, int]]:
    """Load USTEC 1m analysis bars, 15m weekday bars, levels, and precision step."""
    loaded = load_analysis_timebars(DATA_DIR, INSTRUMENT)
    frame_1m = loaded.frame

    train_end_1m = train_cutoff_time(frame_1m, loaded.train_rows)
    frame_1m_ny = add_ny_time_features(frame_1m, train_end_1m)
    levels = compute_liquidity_levels(frame_1m_ny)

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
        empty_15m = pd.DataFrame(columns=["CloseTime", "High", "Low", "Close"])
        return bars_1m, empty_15m, levels, 1e-5, coverage

    train_rows_15m = int(aggregated.height * 0.70)
    train_end_15m = train_cutoff_time(aggregated, train_rows_15m)
    frame_15m = _add_body_metrics(_add_atr_15m(add_ny_time_features(aggregated, train_end_15m)))
    precision_step = compute_price_precision_step(frame_15m)
    weekday_15m = weekday_filter(frame_15m).to_pandas()
    weekday_15m["CloseTime"] = pd.to_datetime(weekday_15m["CloseTime"])
    weekday_15m["OpenTime"] = pd.to_datetime(weekday_15m["OpenTime"])
    weekday_15m = weekday_15m.reset_index(drop=True)
    return bars_1m, weekday_15m, levels, precision_step, coverage


# ── Sweep / breach detection (EXP-015 rule on 15m) ───────────────────────────


def _build_level_events(merged: pd.DataFrame, level_type: str) -> pd.DataFrame:
    """First-touch per NYDate per level type, classified as Sweep or Breach."""
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
    weekday_15m: pd.DataFrame,
    levels: pd.DataFrame,
    precision_step: float,
) -> pd.DataFrame:
    """Detect 15m sweep and breach events for USTEC."""
    inst_lvl = (
        levels[levels["Instrument"] == INSTRUMENT][
            ["NYDate", "PDH", "PDL", "ONH", "ONL"]
        ].copy()
    )
    merged = weekday_15m.merge(inst_lvl, on="NYDate", how="left")
    atr_safe = merged["ATR14Prior"].fillna(0.0)
    merged["Buffer"] = np.maximum(precision_step, BUFFER_ATR_COEFF * atr_safe)
    merged["Instrument"] = INSTRUMENT

    parts = [
        _build_level_events(merged, lt)
        for lt in LEVEL_TYPES_HIGH + LEVEL_TYPES_LOW
    ]
    non_empty = [p for p in parts if not p.empty]
    if not non_empty:
        return pd.DataFrame(columns=SWEEP_COLS)
    result = pd.concat(non_empty, ignore_index=True)
    present = [c for c in SWEEP_COLS if c in result.columns]
    return result[present].reset_index(drop=True)


# ── Displacement on 15m (EXP-018 rule) ───────────────────────────────────────


def _is_directional_displacement(row: pd.Series, side: str) -> bool:
    """Return whether a 15m candidate bar matches the EXP-018 displacement rule."""
    median_body = row["BodyMedian100Prior"]
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
    bars_15m: pd.DataFrame,
    close_ns_15m: np.ndarray,
) -> dict[str, Any]:
    """Find the first qualifying 15m displacement candle within 10 bars after sweep."""
    event_ns = int(pd.Timestamp(sweep["CloseTime"]).value)
    start_idx = int(np.searchsorted(close_ns_15m, event_ns, side="right"))
    stop_idx = min(start_idx + MAX_CONFIRMATION_BARS, len(bars_15m))
    if start_idx >= len(bars_15m):
        return {"Confirmed": False, "MissReason": "NO_FORWARD_BARS"}

    for idx in range(start_idx, stop_idx):
        candidate = bars_15m.iloc[idx]
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
                "BodyMedian100Prior": float(candidate["BodyMedian100Prior"]),
                "CloseLocation": float(candidate["CloseLocation"]),
                "DelayBars": idx - start_idx + 1,
            }
    return {"Confirmed": False, "MissReason": "NO_DISPLACEMENT_WITHIN_10_BARS"}


def build_displacement_entries(
    sweeps: pd.DataFrame,
    bars_15m: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build displacement-confirmed entry rows at displacement-close timing."""
    close_ns_15m = bars_15m["CloseTime"].values.astype(np.int64)
    entries: list[dict[str, Any]] = []
    misses: list[dict[str, Any]] = []
    for _, sweep in sweeps[sweeps["EventType"] == "Sweep"].iterrows():
        confirmation = find_displacement_for_sweep(sweep, bars_15m, close_ns_15m)
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


# ── Candidate A breaker label (EXP-022 rule on 15m) ──────────────────────────


def _find_last_opposite_candle(
    side: str,
    before_ns: int,
    close_ns_15m: np.ndarray,
    bars_15m: pd.DataFrame,
) -> tuple[float, float, pd.Timestamp] | None:
    """Last opposite-direction 15m candle within CAND_A_LOOKBACK_BARS before timestamp."""
    before_idx = int(np.searchsorted(close_ns_15m, before_ns, side="left"))
    search_start = max(0, before_idx - CAND_A_LOOKBACK_BARS)
    for i in range(before_idx - 1, search_start - 1, -1):
        bar = bars_15m.iloc[i]
        is_bullish = float(bar["Close"]) > float(bar["Open"])
        is_bearish = float(bar["Close"]) < float(bar["Open"])
        if side == "High" and is_bullish:
            return float(bar["Low"]), float(bar["High"]), bar["CloseTime"]
        if side == "Low" and is_bearish:
            return float(bar["Low"]), float(bar["High"]), bar["CloseTime"]
    return None


def _close_invalidates_setup(side: str, close: float, stop: float) -> bool:
    """Return True when a 15m close crosses the original sweep invalidation stop."""
    return close >= stop if side == "High" else close <= stop


def _find_cand_a_breaker(
    ob_low: float,
    ob_high: float,
    side: str,
    disp_ns: int,
    stop: float,
    close_ns_15m: np.ndarray,
    bars_15m: pd.DataFrame,
) -> dict[str, Any] | None:
    """First 15m close through the order-block boundary after displacement."""
    start_idx = int(np.searchsorted(close_ns_15m, disp_ns, side="right"))
    stop_idx = min(start_idx + MAX_BREAKER_DELAY, len(bars_15m))
    for i in range(start_idx, stop_idx):
        bar = bars_15m.iloc[i]
        close = float(bar["Close"])
        if _close_invalidates_setup(side, close, stop):
            return {
                "InvalidatedBeforeBreaker": True,
                "InvalidationTime": bar["CloseTime"],
                "DelayBars": i - start_idx + 1,
            }
        if side == "High" and close < ob_low:
            return {
                "BreakerTime": bar["CloseTime"],
                "BreakerClose": close,
                "DelayBars": i - start_idx + 1,
                "InvalidatedBeforeBreaker": False,
            }
        if side == "Low" and close > ob_high:
            return {
                "BreakerTime": bar["CloseTime"],
                "BreakerClose": close,
                "DelayBars": i - start_idx + 1,
                "InvalidatedBeforeBreaker": False,
            }
    return None


def label_breaker(
    entries: pd.DataFrame,
    bars_15m: pd.DataFrame,
) -> pd.DataFrame:
    """Add Candidate A breaker labeling columns to displacement entries.

    The breaker is a future-conditional label: True when a Candidate A breaker
    confirms before sweep-stop invalidation within MAX_BREAKER_DELAY 15m bars.
    """
    if entries.empty:
        return entries
    close_ns_15m = bars_15m["CloseTime"].values.astype(np.int64)
    rows: list[dict[str, Any]] = []
    for _, row in entries.iterrows():
        disp_ns = int(pd.Timestamp(row["DisplacementTime"]).value)
        side = str(row["Side"])
        ob = _find_last_opposite_candle(side, disp_ns, close_ns_15m, bars_15m)
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
            ob_low, ob_high, side, disp_ns, float(row["Stop"]), close_ns_15m, bars_15m
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


# ── Outcomes on real 1-minute prices ─────────────────────────────────────────


def _walk_target_stop(
    highs: np.ndarray,
    lows: np.ndarray,
    target: float,
    stop: float,
    is_bearish: bool,
) -> tuple[bool, bool, bool]:
    """Return (target_hit, stop_hit, ambiguous) over ordered forward bars."""
    for idx in range(highs.size):
        h = float(highs[idx])
        l = float(lows[idx])
        target_hit = (l <= target) if is_bearish else (h >= target)
        stop_hit = (h >= stop) if is_bearish else (l <= stop)
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
    """Compute primary-horizon outcomes for one entry on 1-minute bars.

    Uses the displacement candle CloseTime as the entry timestamp; the
    `side="right"` searchsorted skips any 1-minute bar whose CloseTime equals
    the 15-minute displacement CloseTime, enforcing the no-intrabar-leakage
    rule.
    """
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
    target_2r = entry_price - 2 * risk if is_bearish else entry_price + 2 * risk
    hit_1r, _, amb_1r = _walk_target_stop(h_highs, h_lows, target_1r, stop, is_bearish)
    hit_2r, _, amb_2r = _walk_target_stop(h_highs, h_lows, target_2r, stop, is_bearish)
    return {
        "MFE_R_60m": max(0.0, mfe) / risk,
        "MAE_R_60m": max(0.0, mae) / risk,
        "Return_R_60m": realized / risk,
        "Hit1R_60m": np.nan if amb_1r else float(hit_1r),
        "Hit2R_60m": np.nan if amb_2r else float(hit_2r),
        "Ambiguous60": bool(amb_1r),
    }


def append_outcomes(entries: pd.DataFrame, bars_1m: pd.DataFrame) -> pd.DataFrame:
    """Append outcome columns to entries using 1-minute real prices."""
    close_ns = bars_1m["CloseTime"].values.astype(np.int64)
    highs = bars_1m["High"].to_numpy(dtype=float)
    lows = bars_1m["Low"].to_numpy(dtype=float)
    closes = bars_1m["Close"].to_numpy(dtype=float)
    rows: list[dict[str, Any]] = []
    for _, entry in entries.iterrows():
        outcome = _outcomes_for_event(entry, close_ns, highs, lows, closes)
        rows.append({**entry.to_dict(), **outcome})
    return pd.DataFrame(rows)


# ── Waterfall, counts, retention ─────────────────────────────────────────────


def event_waterfall(
    sweeps: pd.DataFrame,
    entries_with_outcomes: pd.DataFrame,
) -> pd.DataFrame:
    """Per-segment event-count waterfall: sweep -> displacement -> breaker -> feasible."""
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
            int(
                (seg_entries["BreakerConfirmed"] & seg_entries["RiskFeasible"]).sum()
            )
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


def load_exp023_return_reference() -> pd.DataFrame:
    """Load EXP-023 USTEC Return_R_60m breaker-minus-baseline references."""
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


def load_exp023_waterfall_reference() -> pd.DataFrame:
    """Load EXP-023 USTEC displacement baseline counts for retention checks."""
    path = EXP023_RESULTS_DIR / "chain_waterfall.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required EXP-023 waterfall reference is missing: {path}")
    reference = pd.read_csv(path)
    required = {"Instrument", "Segment", "BaselineN", "BreakerN"}
    missing = required - set(reference.columns)
    if missing:
        raise ValueError(f"EXP-023 waterfall reference missing columns: {sorted(missing)}")
    ustec = reference[reference["Instrument"] == INSTRUMENT].copy()
    if set(ustec["Segment"]) != {"Train", "Test"}:
        raise ValueError("EXP-023 USTEC waterfall reference must include Train and Test")
    return ustec


def retention_vs_exp023(
    entries_with_outcomes: pd.DataFrame,
    exp023_waterfall: pd.DataFrame,
) -> dict[str, Any]:
    """Compute 15m / 1m displacement-count retention from structured EXP-023 rows."""
    by_segment: list[dict[str, Any]] = []
    for segment in ("Train", "Test"):
        ref_row = exp023_waterfall[exp023_waterfall["Segment"] == segment]
        if ref_row.empty:
            raise ValueError(f"Missing EXP-023 USTEC {segment} retention reference")
        one_min_count = int(ref_row["BaselineN"].iloc[0])
        fifteen_min_count = int((entries_with_outcomes["Segment"] == segment).sum())
        ratio = fifteen_min_count / one_min_count if one_min_count > 0 else np.nan
        by_segment.append(
            {
                "Segment": segment,
                "EXP023DisplacementCount1m": one_min_count,
                "EXP031DisplacementCount15m": fifteen_min_count,
                "RetentionRatio": ratio,
                "ResolutionCostLimited": bool(
                    np.isfinite(ratio) and ratio < RETENTION_LIMIT
                ),
            }
        )
    one_min_total = int(sum(row["EXP023DisplacementCount1m"] for row in by_segment))
    fifteen_min_total = int(sum(row["EXP031DisplacementCount15m"] for row in by_segment))
    total_ratio = fifteen_min_total / one_min_total if one_min_total > 0 else np.nan
    resolution_limited = bool(
        np.isfinite(total_ratio) and total_ratio < RETENTION_LIMIT
    )
    return {
        "exp023_ustec_displacement_count_1m": one_min_total,
        "exp031_ustec_displacement_count_15m": fifteen_min_total,
        "retention_ratio": total_ratio,
        "resolution_cost_limited": resolution_limited,
        "by_segment": by_segment,
    }


def build_exp023_comparison(
    primary: pd.DataFrame,
    exp023_reference: pd.DataFrame,
) -> pd.DataFrame:
    """Join EXP-031 15m primary effects to EXP-023 1m USTEC reference effects."""
    ref = exp023_reference.rename(
        columns={
            "MeanDiff": "EXP023PointDiff",
            "CI_Lo": "EXP023CILow",
            "CI_Hi": "EXP023CIHigh",
            "CIExcludesZero": "EXP023CIExcludesZero",
        }
    )[["Segment", "EXP023PointDiff", "EXP023CILow", "EXP023CIHigh", "EXP023CIExcludesZero"]]
    comparison = primary.merge(ref, on="Segment", how="left")
    if comparison[["EXP023PointDiff", "EXP023CILow", "EXP023CIHigh"]].isna().any().any():
        raise ValueError("Missing EXP-023 reference values in EXP-031 comparison")
    same_direction = comparison["Diff"] * comparison["EXP023PointDiff"] > 0.0
    comparison["SameDirectionAsEXP023"] = same_direction
    comparison["Within50PctOrStronger"] = same_direction & (
        comparison["Diff"].abs() >= 0.5 * comparison["EXP023PointDiff"].abs()
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
            hit = feasible["Hit1R_60m"].dropna()
            rows.append(
                {
                    "Segment": segment,
                    "EventClass": event_class,
                    "TradeCount": int(len(group)),
                    "RiskFeasibleCount": int(len(feasible)),
                    "MeanReturn_R": float(return_r.mean()) if not return_r.empty else np.nan,
                    "MeanMAE_R": (
                        float(feasible["MAE_R_60m"].dropna().mean())
                        if not feasible.empty
                        else np.nan
                    ),
                    "MeanMFE_R": (
                        float(feasible["MFE_R_60m"].dropna().mean())
                        if not feasible.empty
                        else np.nan
                    ),
                    "WinRateHit1R": float(hit.mean()) if not hit.empty else np.nan,
                }
            )
    return pd.DataFrame(rows)


# ── Bootstrap and verdict ────────────────────────────────────────────────────


def _label_stratified_bootstrap(
    return_r: np.ndarray,
    breaker_mask: np.ndarray,
    feasible_mask: np.ndarray,
    n_reps: int,
    seed: int,
) -> tuple[float, float, float, float, float]:
    """Resample displacement events with replacement; recompute baseline/breaker mean.

    Within each replicate, the baseline mean uses all risk-feasible events in
    the resample and the breaker mean uses the breaker-labeled subset of those.
    This preserves the subset relationship in each bootstrap draw.

    Returns (baseline_point, breaker_point, diff_point, ci_low, ci_high).
    """
    n = return_r.size
    if n == 0:
        return float("nan"), float("nan"), float("nan"), float("nan"), float("nan")
    finite = np.isfinite(return_r) & feasible_mask
    return_r = return_r[finite]
    breaker_mask = breaker_mask[finite]
    if return_r.size == 0 or breaker_mask.sum() == 0:
        return float("nan"), float("nan"), float("nan"), float("nan"), float("nan")

    baseline_point = float(return_r.mean())
    breaker_point = float(return_r[breaker_mask].mean())
    diff_point = breaker_point - baseline_point

    rng = np.random.default_rng(seed)
    diffs = np.empty(n_reps, dtype=float)
    indices = np.arange(return_r.size)
    valid_reps = 0
    for rep in range(n_reps):
        pick = rng.choice(indices, size=indices.size, replace=True)
        sample_returns = return_r[pick]
        sample_breaker = breaker_mask[pick]
        if not sample_breaker.any():
            diffs[rep] = np.nan
            continue
        diffs[rep] = sample_returns[sample_breaker].mean() - sample_returns.mean()
        valid_reps += 1
    finite_diffs = diffs[np.isfinite(diffs)]
    if finite_diffs.size < n_reps // 4:
        return baseline_point, breaker_point, diff_point, float("nan"), float("nan")
    ci_low = float(np.quantile(finite_diffs, 0.025))
    ci_high = float(np.quantile(finite_diffs, 0.975))
    return baseline_point, breaker_point, diff_point, ci_low, ci_high


def bootstrap_primary(entries: pd.DataFrame) -> pd.DataFrame:
    """Bootstrap expectancy-R difference (breaker minus baseline) per segment."""
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
        return_r = seg["Return_R_60m"].to_numpy(dtype=float)
        breaker_mask = seg["BreakerConfirmed"].to_numpy(dtype=bool)
        feasible_mask = seg["RiskFeasible"].to_numpy(dtype=bool)
        baseline_pt, breaker_pt, diff_pt, ci_low, ci_high = (
            _label_stratified_bootstrap(
                return_r, breaker_mask, feasible_mask, BOOTSTRAP_REPS, BOOTSTRAP_SEED
            )
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
    """Bootstrap secondary diagnostics (MAE_R_60m, Return_R_60m only)."""
    rows: list[dict[str, Any]] = []
    for metric in ("MAE_R_60m", "Return_R_60m"):
        for segment in ("Train", "Test"):
            seg = entries[entries["Segment"] == segment]
            if seg.empty:
                continue
            values = seg[metric].to_numpy(dtype=float)
            breaker_mask = seg["BreakerConfirmed"].to_numpy(dtype=bool)
            feasible_mask = seg["RiskFeasible"].to_numpy(dtype=bool)
            base_pt, br_pt, diff_pt, ci_low, ci_high = _label_stratified_bootstrap(
                values, breaker_mask, feasible_mask, BOOTSTRAP_REPS, BOOTSTRAP_SEED
            )
            rows.append(
                {
                    "Metric": metric,
                    "Segment": segment,
                    "BaselineMean": base_pt,
                    "BreakerMean": br_pt,
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
    exp023_comparison: pd.DataFrame,
) -> dict[str, Any]:
    """Map counts, retention, EXP-023 comparability, and primary CI to a verdict."""
    test_row = primary[primary["Segment"] == "Test"]
    train_row = primary[primary["Segment"] == "Train"]
    test_ref = exp023_comparison[exp023_comparison["Segment"] == "Test"]
    breaker_test_floor = bool(
        waterfall[waterfall["Segment"] == "Test"]["BreakerFloorMet"].all()
    )
    breaker_train_floor = bool(
        waterfall[waterfall["Segment"] == "Train"]["BreakerFloorMet"].all()
    )
    resolution_limited = bool(retention.get("resolution_cost_limited", False))

    test_point = (
        float(test_row["Diff"].iloc[0]) if not test_row.empty else float("nan")
    )
    test_ci_low = (
        float(test_row["CILow"].iloc[0]) if not test_row.empty else float("nan")
    )
    test_ci_high = (
        float(test_row["CIHigh"].iloc[0]) if not test_row.empty else float("nan")
    )
    train_point = (
        float(train_row["Diff"].iloc[0]) if not train_row.empty else float("nan")
    )
    exp023_test_point = (
        float(test_ref["EXP023PointDiff"].iloc[0])
        if not test_ref.empty
        else float("nan")
    )
    same_direction = (
        bool(test_ref["SameDirectionAsEXP023"].iloc[0])
        if not test_ref.empty
        else False
    )
    within_50pct_or_stronger = (
        bool(test_ref["Within50PctOrStronger"].iloc[0])
        if not test_ref.empty
        else False
    )

    excludes_zero = (
        np.isfinite(test_ci_low)
        and np.isfinite(test_ci_high)
        and (test_ci_low > 0 or test_ci_high < 0)
    )
    train_improves = (
        np.isfinite(train_point)
        and np.isfinite(exp023_test_point)
        and train_point * exp023_test_point > 0.0
    )
    test_excludes_zero_same_direction = bool(excludes_zero and same_direction)

    if not (breaker_train_floor and breaker_test_floor):
        verdict = "INCONCLUSIVE"
        reason = "RISK_FEASIBLE_BREAKER_FLOOR_NOT_MET"
    elif resolution_limited:
        verdict = "INCONCLUSIVE"
        reason = "RETENTION_VS_EXP023_BELOW_30PCT"
    elif np.isfinite(exp023_test_point) and test_point * exp023_test_point < 0.0:
        verdict = "AGAINST"
        reason = "TEST_POINT_REVERSES_SIGN_VERSUS_EXP023"
    elif not excludes_zero and np.isfinite(test_ci_low) and np.isfinite(test_ci_high):
        verdict = "AGAINST"
        reason = "TEST_CI_INCLUDES_ZERO"
    elif (
        train_improves
        and test_excludes_zero_same_direction
        and within_50pct_or_stronger
    ):
        verdict = "FOR"
        reason = "TRAIN_AND_TEST_IMPROVE_WITHIN_EXP023_REFERENCE_BAND"
    elif test_excludes_zero_same_direction and not train_improves:
        verdict = "INCONCLUSIVE"
        reason = "TEST_POSITIVE_BUT_TRAIN_EXPECTANCY_DOES_NOT_IMPROVE"
    elif test_excludes_zero_same_direction and not within_50pct_or_stronger:
        verdict = "INCONCLUSIVE"
        reason = "TEST_POSITIVE_BUT_BELOW_EXP023_50PCT_REFERENCE_BAND"
    else:
        verdict = "INCONCLUSIVE"
        reason = "TEST_CI_UNDEFINED"
    return {
        "verdict": verdict,
        "reason": reason,
        "test_point_diff": test_point,
        "test_ci_low": test_ci_low,
        "test_ci_high": test_ci_high,
        "train_point_diff": train_point,
        "exp023_test_point_diff": exp023_test_point,
        "same_direction_as_exp023": same_direction,
        "within_50pct_or_stronger": within_50pct_or_stronger,
        "train_improves": train_improves,
        "test_excludes_zero_same_direction": test_excludes_zero_same_direction,
        "breaker_train_floor_met": breaker_train_floor,
        "breaker_test_floor_met": breaker_test_floor,
        "resolution_cost_limited": resolution_limited,
        "retention": retention,
    }


# ── JSON sanitization ────────────────────────────────────────────────────────


def _json_safe(value: Any) -> Any:
    """Convert numpy/pandas values to JSON-safe scalars."""
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    if pd.isna(value):
        return None
    return value


# ── Plotting ─────────────────────────────────────────────────────────────────


def plot_waterfall(waterfall: pd.DataFrame, save_path: Path) -> None:
    """Plot sweep -> displacement -> breaker-labeled -> feasible event count waterfall."""
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
    ax.set_title("EXP-031 USTEC 15m Event-Count Waterfall")
    ax.set_xlabel("")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_expectancy(
    primary: pd.DataFrame,
    exp023_comparison: pd.DataFrame,
    save_path: Path,
) -> None:
    """Plot 15m baseline/breaker means and EXP-023 reference diff overlay."""
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
    ax.set_title("EXP-031 USTEC 15m Expectancy: Baseline vs Breaker-Labeled")
    ax.legend()

    diff_ax = axes[1]
    yerr_031 = [
        (primary["Diff"] - primary["CILow"]).clip(lower=0).fillna(0),
        (primary["CIHigh"] - primary["Diff"]).clip(lower=0).fillna(0),
    ]
    diff_ax.errorbar(
        x - 0.08,
        primary["Diff"],
        yerr=yerr_031,
        fmt="o",
        color="darkblue",
        ecolor="steelblue",
        capsize=4,
        label="EXP-031 15m",
    )
    ref = exp023_comparison.set_index("Segment").reindex(primary["Segment"]).reset_index()
    yerr_023 = [
        (ref["EXP023PointDiff"] - ref["EXP023CILow"]).clip(lower=0).fillna(0),
        (ref["EXP023CIHigh"] - ref["EXP023PointDiff"]).clip(lower=0).fillna(0),
    ]
    diff_ax.errorbar(
        x + 0.08,
        ref["EXP023PointDiff"],
        yerr=yerr_023,
        fmt="s",
        color="darkorange",
        ecolor="orange",
        capsize=4,
        label="EXP-023 1m",
    )
    diff_ax.axhline(0.0, color="black", linewidth=1)
    diff_ax.set_xticks(x)
    diff_ax.set_xticklabels(primary["Segment"])
    diff_ax.set_ylabel("Breaker minus baseline Return_R_60m")
    diff_ax.set_title("EXP-031 vs EXP-023 Reference Difference")
    diff_ax.legend()
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_r_distribution(entries: pd.DataFrame, save_path: Path) -> None:
    """Plot 60m R-multiple distribution by Test segment, baseline vs breaker."""
    test = entries[(entries["Segment"] == "Test") & entries["RiskFeasible"]].copy()
    if test.empty:
        return
    test["Return_R_60m_Capped"] = test["Return_R_60m"].clip(lower=-PLOT_R_CAP, upper=PLOT_R_CAP)
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
    ax.set_title("EXP-031 USTEC 15m Return_R_60m Distribution (Test, capped at +/-8R)")
    ax.set_xlabel("")
    ax.set_ylabel("Return in R")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_mae_proxy(primary: pd.DataFrame, secondary: pd.DataFrame, save_path: Path) -> None:
    """Plot drawdown-proxy (MAE_R_60m) interval comparison by segment."""
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
    ax.set_ylabel("Breaker minus Baseline MAE_R_60m")
    ax.set_title("EXP-031 USTEC 15m Drawdown-Proxy (MAE_R_60m) Difference With CI")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ── Output orchestration ─────────────────────────────────────────────────────


def write_outputs(
    sweeps: pd.DataFrame,
    entries: pd.DataFrame,
    waterfall: pd.DataFrame,
    outcome_summary: pd.DataFrame,
    primary: pd.DataFrame,
    secondary: pd.DataFrame,
    exp023_comparison: pd.DataFrame,
    retention: dict[str, Any],
    coverage: dict[str, int],
    precision_step: float,
    verdict: dict[str, Any],
    plots_dir: Path,
    results_dir: Path,
) -> None:
    """Write tables, JSON, text summary, and plots."""
    sweeps.to_csv(results_dir / "sweep_events_15m.csv", index=False)
    entries.to_csv(results_dir / "displacement_entries_15m.csv", index=False)
    waterfall.to_csv(results_dir / "event_waterfall.csv", index=False)
    outcome_summary.to_csv(results_dir / "outcome_summary.csv", index=False)
    primary.to_csv(results_dir / "bootstrap_primary.csv", index=False)
    secondary.to_csv(results_dir / "bootstrap_secondary.csv", index=False)
    exp023_comparison.to_csv(results_dir / "exp023_reference_comparison.csv", index=False)

    payload = {
        "experiment_id": "EXP-031",
        "title": "15-Minute USTEC Breaker Chain",
        "instrument": INSTRUMENT,
        "period_minutes": PERIOD_MINUTES,
        "buffer_atr_coefficient": BUFFER_ATR_COEFF,
        "max_confirmation_bars_15m": MAX_CONFIRMATION_BARS,
        "max_breaker_delay_15m": MAX_BREAKER_DELAY,
        "cand_a_lookback_bars_15m": CAND_A_LOOKBACK_BARS,
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
        "exp023_reference_comparison": exp023_comparison.to_dict(orient="records"),
        "retention_vs_exp023": retention,
    }
    with (results_dir / "results.json").open("w", encoding="utf-8") as handle:
        json.dump(_json_safe(payload), handle, indent=2, default=str, allow_nan=False)

    with (results_dir / "numerical_summary.txt").open("w", encoding="utf-8") as handle:
        handle.write("EXP-031 15-Minute USTEC Breaker Chain\n")
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
        handle.write("\nOutcome summary:\n")
        for row in outcome_summary.itertuples(index=False):
            handle.write(
                f"- {row.Segment} {row.EventClass}: trades={row.TradeCount}, "
                f"feasible={row.RiskFeasibleCount}, "
                f"returnR={row.MeanReturn_R:.4f}, "
                f"MAE_R={row.MeanMAE_R:.4f}, "
                f"MFE_R={row.MeanMFE_R:.4f}, "
                f"win_rate={row.WinRateHit1R:.4f}\n"
            )
        handle.write("\nEXP-023 USTEC Return_R_60m reference comparison:\n")
        for row in exp023_comparison.itertuples(index=False):
            handle.write(
                f"- {row.Segment}: exp031={row.Diff:.4f} "
                f"[{row.CILow:.4f}, {row.CIHigh:.4f}], "
                f"exp023={row.EXP023PointDiff:.4f} "
                f"[{row.EXP023CILow:.4f}, {row.EXP023CIHigh:.4f}], "
                f"same_direction={row.SameDirectionAsEXP023}, "
                f"within_50pct_or_stronger={row.Within50PctOrStronger}\n"
            )
        handle.write(
            f"\nRetention vs EXP-023 1m: "
            f"1m={retention['exp023_ustec_displacement_count_1m']}, "
            f"15m={retention['exp031_ustec_displacement_count_15m']}, "
            f"ratio={retention['retention_ratio']}\n"
        )

    plot_waterfall(waterfall, plots_dir / "01_event_waterfall.png")
    plot_expectancy(primary, exp023_comparison, plots_dir / "02_expectancy.png")
    plot_r_distribution(entries, plots_dir / "03_r_distribution.png")
    plot_mae_proxy(primary, secondary, plots_dir / "04_drawdown_proxy.png")


def run_experiment() -> None:
    """Execute the EXP-031 USTEC 15m breaker chain workflow."""
    plots_dir = EXP_DIR / "plots"
    results_dir = EXP_DIR / "results"
    plots_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    bars_1m, weekday_15m, levels, precision_step, coverage = load_data()
    LOGGER.info(
        "USTEC: 1m=%d, 15m=%d (dropped=%d)",
        coverage["source_bars_in"],
        coverage["aggregated_bars_out"],
        coverage["dropped_partial_window_bars"],
    )
    if weekday_15m.empty:
        raise ValueError("USTEC 15m frame is empty; cannot proceed.")

    sweeps = detect_sweeps(weekday_15m, levels, precision_step)
    entries, misses = build_displacement_entries(sweeps, weekday_15m)
    if entries.empty:
        raise ValueError("No displacement-confirmed sweeps on USTEC 15m series.")
    entries = label_breaker(entries, weekday_15m)
    entries = append_outcomes(entries, bars_1m)

    waterfall = event_waterfall(sweeps, entries)
    exp023_return_reference = load_exp023_return_reference()
    exp023_waterfall_reference = load_exp023_waterfall_reference()
    retention = retention_vs_exp023(entries, exp023_waterfall_reference)
    outcome_summary = summarize_outcomes(entries)
    primary = bootstrap_primary(entries)
    secondary = bootstrap_secondary(entries)
    exp023_comparison = build_exp023_comparison(primary, exp023_return_reference)
    verdict = evaluate_verdict(waterfall, primary, retention, exp023_comparison)

    misses.to_csv(results_dir / "displacement_misses_15m.csv", index=False)
    write_outputs(
        sweeps,
        entries,
        waterfall,
        outcome_summary,
        primary,
        secondary,
        exp023_comparison,
        retention,
        coverage,
        precision_step,
        verdict,
        plots_dir,
        results_dir,
    )

    print("EXP-031 complete.")
    print(f"Verdict: {verdict['verdict']} ({verdict['reason']})")
    print(f"Plots:   {plots_dir}")
    print(f"Results: {results_dir}")


def main() -> None:
    """Entry point for manual execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_experiment()


if __name__ == "__main__":
    main()
