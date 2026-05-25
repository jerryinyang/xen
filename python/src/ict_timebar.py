from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import polars as pl


INSTRUMENTS = ["EURUSD", "XAUUSD", "BTCUSD", "USTEC"]
TIMEBAR_COLUMNS = [
    "Symbol",
    "OpenTime",
    "CloseTime",
    "Open",
    "High",
    "Low",
    "Close",
    "TickVolume",
]

ANALYSIS_FRACTION = 0.70
TRAIN_FRACTION = 0.70
NY_TIMEZONE = "America/New_York"
SOURCE_TIMEZONE_ASSUMPTION = "UTC"

OVERNIGHT_START_MINUTE = 17 * 60
OVERNIGHT_END_MINUTE = 9 * 60 + 30


@dataclass(frozen=True)
class MacroWindowSpec:
    """Fixed EXP-012-approved macro-window definition."""

    window: str
    family: str
    start_minute: int
    end_minute: int

    @property
    def duration(self) -> int:
        return self.end_minute - self.start_minute


@dataclass(frozen=True)
class AnalysisLoad:
    """Holdout-excluded time-bar load result for one instrument."""

    frame: pl.DataFrame
    analysis_rows: int
    train_rows: int
    total_rows: int
    paths: list[Path]


MACRO_WINDOW_SPECS = [
    MacroWindowSpec("AM1", "AM", 7 * 60 + 50, 8 * 60 + 10),
    MacroWindowSpec("AM2", "AM", 8 * 60 + 50, 9 * 60 + 10),
    MacroWindowSpec("AM3", "AM", 9 * 60 + 50, 10 * 60 + 10),
    MacroWindowSpec("AM4", "AM", 10 * 60 + 50, 11 * 60 + 10),
    MacroWindowSpec("AM5", "AM", 11 * 60 + 50, 12 * 60 + 10),
    MacroWindowSpec("PM1", "PM", 13 * 60 + 20, 13 * 60 + 40),
    MacroWindowSpec("PM2", "PM", 14 * 60 + 50, 15 * 60 + 10),
    MacroWindowSpec("PM3", "PM", 15 * 60 + 15, 15 * 60 + 45),
    MacroWindowSpec("PM4", "PM", 15 * 60 + 50, 16 * 60 + 10),
]
MACRO_WINDOW_TO_FAMILY = {spec.window: spec.family for spec in MACRO_WINDOW_SPECS}
MACRO_WINDOW_TO_LENGTH = {spec.window: spec.duration for spec in MACRO_WINDOW_SPECS}


def instrument_timebar_paths(data_dir: Path, instrument: str) -> list[Path]:
    """Return all matching time-bar files for an instrument."""
    pattern = f"timebars/timebars_{instrument.lower()}_*.parquet"
    paths = sorted(data_dir.glob(pattern))
    if not paths:
        raise FileNotFoundError(
            f"No time-bar files found for {instrument} matching {pattern}"
        )
    return paths


def load_analysis_timebars(data_dir: Path, instrument: str) -> AnalysisLoad:
    """Load only the first chronological 70 percent for one instrument."""
    paths = instrument_timebar_paths(data_dir, instrument)
    scan = pl.scan_parquet(paths).select(TIMEBAR_COLUMNS)
    total_rows = int(scan.select(pl.len()).collect().item())
    analysis_rows = int(total_rows * ANALYSIS_FRACTION)
    if analysis_rows <= 0:
        empty = pl.DataFrame({column: [] for column in TIMEBAR_COLUMNS})
        return AnalysisLoad(empty, 0, 0, total_rows, paths)
    frame = scan.sort("CloseTime").slice(0, analysis_rows).collect()
    train_rows = int(analysis_rows * TRAIN_FRACTION)
    return AnalysisLoad(frame, analysis_rows, train_rows, total_rows, paths)


def train_cutoff_time(frame: pl.DataFrame, train_rows: int) -> Any:
    """Return the last timestamp included in the train segment."""
    if frame.is_empty() or train_rows <= 0:
        return None
    cutoff_idx = min(train_rows - 1, len(frame) - 1)
    return frame["CloseTime"][cutoff_idx]


def macro_window_expr() -> pl.Expr:
    """Return a Polars expression that labels each NY minute with a macro window."""
    minute_col = pl.col("NYMinuteOfDay")
    exprs = [
        pl.when(
            (minute_col >= spec.start_minute)
            & (minute_col < spec.end_minute)
        )
        .then(pl.lit(spec.window))
        .otherwise(pl.lit(None, dtype=pl.String))
        for spec in MACRO_WINDOW_SPECS
    ]
    return pl.coalesce(exprs)


def add_ny_time_features(frame: pl.DataFrame, train_end_time: Any) -> pl.DataFrame:
    """Add EXP-012-compatible New York time and segment labels."""
    segment_expr = pl.lit("Test")
    if train_end_time is not None:
        segment_expr = (
            pl.when(pl.col("CloseTime") <= train_end_time)
            .then(pl.lit("Train"))
            .otherwise(pl.lit("Test"))
        )

    return (
        frame.with_columns(
            pl.col("CloseTime")
            .dt.replace_time_zone(SOURCE_TIMEZONE_ASSUMPTION)
            .dt.convert_time_zone(NY_TIMEZONE)
            .alias("CloseTimeNY")
        )
        .with_columns(
            pl.col("CloseTimeNY").dt.date().alias("NYDate"),
            (
                pl.col("CloseTimeNY").dt.hour().cast(pl.Int32) * 60
                + pl.col("CloseTimeNY").dt.minute().cast(pl.Int32)
            ).alias("NYMinuteOfDay"),
            segment_expr.alias("Segment"),
        )
        .with_columns(macro_window_expr().alias("MacroWindow"))
        .with_columns(
            pl.col("MacroWindow").replace(MACRO_WINDOW_TO_FAMILY).alias("WindowFamily"),
            pl.col("MacroWindow")
            .replace(MACRO_WINDOW_TO_LENGTH)
            .cast(pl.Int32)
            .alias("ExpectedBars"),
        )
    )


def add_bar_diagnostics(frame: pl.DataFrame) -> pl.DataFrame:
    """Add prior ATR and displacement helper columns without using future bars."""
    prev_close = pl.col("Close").shift(1)
    true_range = pl.max_horizontal(
        pl.col("High") - pl.col("Low"),
        (pl.col("High") - prev_close).abs(),
        (pl.col("Low") - prev_close).abs(),
    ).fill_null(pl.col("High") - pl.col("Low"))
    candle_range = pl.col("High") - pl.col("Low")
    return (
        frame.with_columns(true_range.alias("TrueRange"))
        .with_columns(
            pl.col("TrueRange")
            .rolling_mean(window_size=14, min_samples=14)
            .shift(1)
            .alias("ATR14Prior"),
            pl.col("TrueRange")
            .rolling_quantile(quantile=0.80, window_size=100, min_samples=100)
            .shift(1)
            .alias("TrueRangeP80Prior"),
            (pl.col("Close") - pl.col("Open")).abs().alias("BodySize"),
            pl.when(candle_range > 0)
            .then((pl.col("Close") - pl.col("Low")) / candle_range)
            .otherwise(0.5)
            .alias("CloseLocation"),
        )
    )


def weekday_filter(frame: pl.DataFrame) -> pl.DataFrame:
    """Restrict to Monday-Friday NY dates using Polars weekday numbering."""
    return frame.filter(pl.col("NYDate").dt.weekday().is_in([1, 2, 3, 4, 5]))


def compute_liquidity_levels(frame: pl.DataFrame) -> pd.DataFrame:
    """Compute deterministic PDH/PDL and ONH/ONL levels for eligible NY dates.

    PDH/PDL use the previous observed weekday NY date. ONH/ONL use bars from
    17:00 NY on the prior calendar date through 09:30 NY on the event date.
    """
    if frame.is_empty():
        return pd.DataFrame()

    weekday_frame = weekday_filter(frame)

    # Weekday event dates with segment labels and intraday bar counts.
    daily_event = (
        weekday_frame.group_by(["Symbol", "NYDate"])
        .agg(
            pl.len().alias("DayBars"),
            pl.n_unique("Segment").alias("SegmentCount"),
            pl.first("Segment").alias("FirstSegment"),
        )
        .rename({"Symbol": "Instrument"})
        .sort(["Instrument", "NYDate"])
        .to_pandas()
    )
    if daily_event.empty:
        return daily_event

    daily_event["Segment"] = daily_event.apply(
        lambda row: row["FirstSegment"] if row["SegmentCount"] == 1 else "Boundary",
        axis=1,
    )

    # PDH/PDL from the previous observed weekday, matching the approved scope.
    all_daily_highs = (
        weekday_frame.group_by(["Symbol", "NYDate"])
        .agg(
            pl.max("High").alias("DayHigh"),
            pl.min("Low").alias("DayLow"),
        )
        .rename({"Symbol": "Instrument"})
        .sort(["Instrument", "NYDate"])
        .to_pandas()
    )
    all_daily_highs["PDH"] = all_daily_highs.groupby("Instrument")["DayHigh"].shift(1)
    all_daily_highs["PDL"] = all_daily_highs.groupby("Instrument")["DayLow"].shift(1)
    all_daily_highs["PriorNYDate"] = all_daily_highs.groupby("Instrument")["NYDate"].shift(1)
    pd_levels = all_daily_highs[["Instrument", "NYDate", "PDH", "PDL", "PriorNYDate"]]

    daily = daily_event.merge(pd_levels, on=["Instrument", "NYDate"], how="left")
    daily["PriorDayBars"] = daily.groupby("Instrument")["DayBars"].shift(1)

    overnight = (
        frame.with_columns(
            pl.when(pl.col("NYMinuteOfDay") >= OVERNIGHT_START_MINUTE)
            .then(pl.col("NYDate") + pl.duration(days=1))
            .when(pl.col("NYMinuteOfDay") <= OVERNIGHT_END_MINUTE)
            .then(pl.col("NYDate"))
            .otherwise(pl.lit(None, dtype=pl.Date))
            .alias("ONEventDate")
        )
        .filter(pl.col("ONEventDate").is_not_null())
        .filter(pl.col("ONEventDate").dt.weekday().is_in([1, 2, 3, 4, 5]))
        .group_by(["Symbol", "ONEventDate"])
        .agg(
            pl.max("High").alias("ONH"),
            pl.min("Low").alias("ONL"),
            pl.len().alias("OvernightBars"),
        )
        .rename({"Symbol": "Instrument", "ONEventDate": "NYDate"})
        .sort(["Instrument", "NYDate"])
        .to_pandas()
    )

    levels = daily.merge(
        overnight,
        on=["Instrument", "NYDate"],
        how="left",
    )
    levels["HasPDLevels"] = levels["PDH"].notna() & levels["PDL"].notna()
    levels["HasONLevels"] = levels["ONH"].notna() & levels["ONL"].notna()
    levels["HasAllLevels"] = levels["HasPDLevels"] & levels["HasONLevels"]
    levels["MissingReason"] = levels.apply(_missing_level_reason, axis=1)
    return levels.sort_values(["Instrument", "NYDate"]).reset_index(drop=True)


def _missing_level_reason(row: pd.Series) -> str:
    """Classify why a liquidity-level row is incomplete."""
    missing: list[str] = []
    if not bool(row["HasPDLevels"]):
        missing.append("NO_PRIOR_WEEKDAY")
    if not bool(row["HasONLevels"]):
        missing.append("NO_OVERNIGHT_BARS")
    return "NONE" if not missing else "+".join(missing)


def format_minute_of_day(minute_of_day: int) -> str:
    """Format a minute-of-day integer as HH:MM."""
    hour = minute_of_day // 60
    minute = minute_of_day % 60
    return f"{hour:02d}:{minute:02d}"


def compute_price_precision_step(frame: pl.DataFrame) -> float:
    """Return the smallest positive close-to-close price increment observed.

    The precision proxy is deliberately computed from consecutive Close prices
    rather than all OHLC values. Close-to-close differences capture stable
    tick-level observations without high/low wick noise. ATR typically dominates
    the sweep buffer; this floor matters mainly during early ATR-null bars and
    low-volatility periods where ATR is zero or missing.

    Parameters
    ----------
    frame : pl.DataFrame
        Time-bar frame for a single instrument.

    Returns
    -------
    float
        Smallest positive close-to-close price difference; falls back to 1e-5
        when no positive differences exist.
    """
    import numpy as np

    closes = frame.sort("CloseTime")["Close"].to_numpy()
    diffs = np.diff(closes)
    positive = diffs[diffs > 0]
    if positive.size == 0:
        return 1e-5
    return float(np.min(positive))
