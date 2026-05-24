"""
Experiment EXP-012: ICT Data Readiness and Feasibility
Implements the analysis plan from analysis-plan.md.
"""
import sys
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[3]
PROJECT_ROOT = PYTHON_ROOT.parent
SRC_DIR = PYTHON_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

import json
import logging
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import polars as pl
import seaborn as sns


LOGGER = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-012"

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
MACRO_FAMILY_COVERAGE_THRESHOLD = 0.80

MACRO_WINDOW_SPECS = [
    {"Window": "AM1", "Family": "AM", "StartMinute": 7 * 60 + 50, "EndMinute": 8 * 60 + 10},
    {"Window": "AM2", "Family": "AM", "StartMinute": 8 * 60 + 50, "EndMinute": 9 * 60 + 10},
    {"Window": "AM3", "Family": "AM", "StartMinute": 9 * 60 + 50, "EndMinute": 10 * 60 + 10},
    {"Window": "AM4", "Family": "AM", "StartMinute": 10 * 60 + 50, "EndMinute": 11 * 60 + 10},
    {"Window": "AM5", "Family": "AM", "StartMinute": 11 * 60 + 50, "EndMinute": 12 * 60 + 10},
    {"Window": "PM1", "Family": "PM", "StartMinute": 13 * 60 + 20, "EndMinute": 13 * 60 + 40},
    {"Window": "PM2", "Family": "PM", "StartMinute": 14 * 60 + 50, "EndMinute": 15 * 60 + 10},
    {"Window": "PM3", "Family": "PM", "StartMinute": 15 * 60 + 15, "EndMinute": 15 * 60 + 45},
    {"Window": "PM4", "Family": "PM", "StartMinute": 15 * 60 + 50, "EndMinute": 16 * 60 + 10},
]
MACRO_WINDOW_DF = pd.DataFrame(MACRO_WINDOW_SPECS)
MACRO_WINDOW_TO_FAMILY = {
    spec["Window"]: spec["Family"] for spec in MACRO_WINDOW_SPECS
}
MACRO_WINDOW_TO_LENGTH = {
    spec["Window"]: spec["EndMinute"] - spec["StartMinute"]
    for spec in MACRO_WINDOW_SPECS
}

COST_PROXY_SCENARIOS = [
    {
        "Scenario": "ZERO_COST_REFERENCE",
        "Description": "Reference-only diagnostic with no transaction-cost haircut.",
        "SpreadBpsPerSide": 0.0,
        "SlippageBpsPerSide": 0.0,
        "CommissionBpsRoundTrip": 0.0,
    },
    {
        "Scenario": "LIGHT_COST_PROXY",
        "Description": "Low-friction placeholder until instrument-specific broker data exists.",
        "SpreadBpsPerSide": 0.5,
        "SlippageBpsPerSide": 0.25,
        "CommissionBpsRoundTrip": 0.5,
    },
    {
        "Scenario": "HEAVY_COST_PROXY",
        "Description": "Stress scenario for later robustness and execution-sensitivity checks.",
        "SpreadBpsPerSide": 1.0,
        "SlippageBpsPerSide": 0.50,
        "CommissionBpsRoundTrip": 1.0,
    },
]


def instrument_timebar_paths(instrument: str) -> list[Path]:
    """Return all matching time-bar files for an instrument."""
    pattern = f"timebars/timebars_{instrument.lower()}_*.parquet"
    paths = sorted(DATA_DIR.glob(pattern))
    if not paths:
        raise FileNotFoundError(
            f"No time-bar files found for {instrument} matching {pattern}"
        )
    return paths


def load_analysis_timebars(
    instrument: str,
) -> tuple[pl.DataFrame, int, int, int, list[Path]]:
    """Load only the holdout-excluded analysis rows for one instrument."""
    paths = instrument_timebar_paths(instrument)
    scan = pl.scan_parquet(paths).select(TIMEBAR_COLUMNS)
    total_rows = int(scan.select(pl.len()).collect().item())
    analysis_rows = int(total_rows * ANALYSIS_FRACTION)
    if analysis_rows <= 0:
        return pl.DataFrame({column: [] for column in TIMEBAR_COLUMNS}), 0, 0, total_rows, paths
    analysis_df = scan.sort("CloseTime").slice(0, analysis_rows).collect()
    train_rows = int(analysis_rows * TRAIN_FRACTION)
    return analysis_df, analysis_rows, train_rows, total_rows, paths


def train_cutoff_time(df: pl.DataFrame, train_rows: int) -> Any:
    """Return the last analysis timestamp included in the train segment."""
    if df.is_empty() or train_rows <= 0:
        return None
    cutoff_idx = min(train_rows - 1, len(df) - 1)
    return df["CloseTime"][cutoff_idx]


def macro_window_expr() -> pl.Expr:
    """Return a Polars expression that labels each NY minute with a macro window."""
    minute_col = pl.col("NYMinuteOfDay")
    exprs = [
        pl.when(
            (minute_col >= spec["StartMinute"])
            & (minute_col < spec["EndMinute"])
        )
        .then(pl.lit(spec["Window"]))
        .otherwise(pl.lit(None, dtype=pl.String))
        for spec in MACRO_WINDOW_SPECS
    ]
    if not exprs:
        raise ValueError("MACRO_WINDOW_SPECS must not be empty")
    return pl.coalesce(exprs)


def add_ny_time_features(df: pl.DataFrame, train_end_time: Any) -> pl.DataFrame:
    """Add NY-time and macro-window features to one instrument's analysis rows."""
    segment_expr = pl.lit("Test")
    if train_end_time is not None:
        segment_expr = (
            pl.when(pl.col("CloseTime") <= train_end_time)
            .then(pl.lit("Train"))
            .otherwise(pl.lit("Test"))
        )

    ny_df = df.with_columns(
        pl.col("CloseTime")
        .dt.replace_time_zone(SOURCE_TIMEZONE_ASSUMPTION)
        .dt.convert_time_zone(NY_TIMEZONE)
        .alias("CloseTimeNY")
    ).with_columns(
        pl.col("CloseTimeNY").dt.date().alias("NYDate"),
        (
            pl.col("CloseTimeNY").dt.hour().cast(pl.Int32) * 60
            + pl.col("CloseTimeNY").dt.minute().cast(pl.Int32)
        ).alias("NYMinuteOfDay"),
        segment_expr.alias("Segment"),
    ).with_columns(
        macro_window_expr().alias("MacroWindow")
    ).with_columns(
        pl.col("MacroWindow").replace(MACRO_WINDOW_TO_FAMILY).alias("WindowFamily"),
        pl.col("MacroWindow").replace(MACRO_WINDOW_TO_LENGTH).cast(pl.Int32).alias("ExpectedBars"),
    )
    return ny_df


def summarize_inventory(
    df: pl.DataFrame,
    input_paths: list[Path],
    total_rows: int,
    analysis_rows: int,
    train_rows: int,
) -> dict[str, Any]:
    """Summarize analysis-set inventory and basic integrity checks."""
    duplicate_timestamps = 0
    ohlc_failures = 0
    if not df.is_empty():
        unique_timestamps = int(df.select(pl.col("CloseTime").n_unique()).item())
        duplicate_timestamps = len(df) - unique_timestamps
        ohlc_failures = df.filter(
            (pl.col("High") < pl.max_horizontal("Open", "Close"))
            | (pl.col("Low") > pl.min_horizontal("Open", "Close"))
        ).height

    return {
        "Instrument": df["Symbol"][0] if not df.is_empty() else None,
        "InputFiles": ", ".join(str(path.relative_to(PROJECT_ROOT)) for path in input_paths),
        "InputFileCount": len(input_paths),
        "SourceRows": total_rows,
        "AnalysisRows": analysis_rows,
        "TrainRows": train_rows,
        "TestRows": analysis_rows - train_rows,
        "AnalysisStart": df["CloseTime"][0] if not df.is_empty() else None,
        "AnalysisEnd": df["CloseTime"][-1] if not df.is_empty() else None,
        "DuplicateCloseTimeRows": duplicate_timestamps,
        "OHLCIntegrityFailures": ohlc_failures,
    }


def build_daily_window_coverage(frame: pl.DataFrame) -> pd.DataFrame:
    """Build a full date-by-window coverage grid restricted to Monday–Friday.

    Off-session dates (Sundays, Saturdays) are excluded from both the expected-bar
    denominator and the observed-bar count. Sunday data is present for all instruments
    (FX/CFD markets open Sunday ~17:00 ET) but carries zero macro-window bars, which
    would otherwise depress coverage ratios by inflating the denominator with
    non-trading-day entries. This filter is a proxy for US trading days; US market
    holidays that fall on weekdays are retained in the denominator.
    """
    weekday_frame = frame.filter(
        pl.col("NYDate").dt.weekday().is_in([1, 2, 3, 4, 5])
    )
    unique_dates = (
        weekday_frame.select(["Symbol", "Segment", "NYDate"])
        .unique()
        .sort(["Symbol", "Segment", "NYDate"])
        .rename({"Symbol": "Instrument"})
        .to_pandas()
    )
    daily_grid = unique_dates.merge(MACRO_WINDOW_DF, how="cross")
    observed = (
        weekday_frame.filter(pl.col("MacroWindow").is_not_null())
        .group_by(["Symbol", "Segment", "NYDate", "MacroWindow"])
        .agg(pl.len().alias("ObservedBars"))
        .rename({"Symbol": "Instrument", "MacroWindow": "Window"})
        .to_pandas()
    )

    daily_window = daily_grid.merge(
        observed,
        on=["Instrument", "Segment", "NYDate", "Window"],
        how="left",
    )
    daily_window["ObservedBars"] = daily_window["ObservedBars"].fillna(0).astype(int)
    daily_window["ExpectedBars"] = (
        daily_window["EndMinute"] - daily_window["StartMinute"]
    ).astype(int)
    daily_window["CoverageRatio"] = (
        daily_window["ObservedBars"] / daily_window["ExpectedBars"]
    )
    return daily_window.sort_values(
        ["Instrument", "Segment", "NYDate", "Window"]
    ).reset_index(drop=True)


def summarize_window_coverage(daily_window: pd.DataFrame) -> pd.DataFrame:
    """Aggregate macro-window coverage across all dates."""
    summary = (
        daily_window.groupby(["Instrument", "Segment", "Window", "Family"], as_index=False)
        .agg(
            TradingDays=("NYDate", "nunique"),
            ObservedBars=("ObservedBars", "sum"),
            ExpectedBars=("ExpectedBars", "sum"),
        )
    )
    summary["CoverageRatio"] = summary["ObservedBars"] / summary["ExpectedBars"]
    return summary.sort_values(
        ["Instrument", "Segment", "Window"]
    ).reset_index(drop=True)


def summarize_family_coverage(daily_window: pd.DataFrame) -> pd.DataFrame:
    """Aggregate AM/PM family coverage across all dates."""
    daily_family = (
        daily_window.groupby(["Instrument", "Segment", "NYDate", "Family"], as_index=False)
        .agg(
            ObservedBars=("ObservedBars", "sum"),
            ExpectedBars=("ExpectedBars", "sum"),
        )
    )
    family_summary = (
        daily_family.groupby(["Instrument", "Segment", "Family"], as_index=False)
        .agg(
            TradingDays=("NYDate", "nunique"),
            ObservedBars=("ObservedBars", "sum"),
            ExpectedBars=("ExpectedBars", "sum"),
        )
    )
    family_summary["CoverageRatio"] = (
        family_summary["ObservedBars"] / family_summary["ExpectedBars"]
    )
    return family_summary.sort_values(
        ["Instrument", "Segment", "Family"]
    ).reset_index(drop=True)


def summarize_missing_bars(frame: pl.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Quantify within-date missing bars by instrument and segment."""
    daily = (
        frame.group_by(["Symbol", "Segment", "NYDate"])
        .agg(
            pl.len().alias("ObservedBars"),
            pl.min("CloseTimeNY").alias("FirstCloseNY"),
            pl.max("CloseTimeNY").alias("LastCloseNY"),
        )
        .rename({"Symbol": "Instrument"})
        .to_pandas()
    )
    span_minutes = (
        (daily["LastCloseNY"] - daily["FirstCloseNY"]).dt.total_seconds() / 60.0
    )
    daily["ExpectedBarsWithinObservedSpan"] = span_minutes.astype(int) + 1
    daily["MissingBarsWithinObservedSpan"] = (
        daily["ExpectedBarsWithinObservedSpan"] - daily["ObservedBars"]
    )
    daily["MissingRateWithinObservedSpan"] = (
        daily["MissingBarsWithinObservedSpan"]
        / daily["ExpectedBarsWithinObservedSpan"]
    )

    summary = (
        daily.groupby(["Instrument", "Segment"], as_index=False)
        .agg(
            TradingDays=("NYDate", "nunique"),
            ObservedBars=("ObservedBars", "sum"),
            ExpectedBarsWithinObservedSpan=("ExpectedBarsWithinObservedSpan", "sum"),
            MissingBarsWithinObservedSpan=("MissingBarsWithinObservedSpan", "sum"),
        )
    )
    summary["MissingRateWithinObservedSpan"] = (
        summary["MissingBarsWithinObservedSpan"]
        / summary["ExpectedBarsWithinObservedSpan"]
    )
    return daily.sort_values(
        ["Instrument", "Segment", "NYDate"]
    ).reset_index(drop=True), summary.sort_values(
        ["Instrument", "Segment"]
    ).reset_index(drop=True)


def summarize_active_session(frame: pl.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Summarize observed active-session timing by instrument."""
    daily_session = (
        frame.group_by(["Symbol", "Segment", "NYDate"])
        .agg(
            pl.min("CloseTimeNY").alias("FirstCloseNY"),
            pl.max("CloseTimeNY").alias("LastCloseNY"),
            pl.len().alias("ObservedBars"),
        )
        .rename({"Symbol": "Instrument"})
        .to_pandas()
    )
    daily_session["FirstMinuteOfDay"] = (
        daily_session["FirstCloseNY"].dt.hour * 60
        + daily_session["FirstCloseNY"].dt.minute
    )
    daily_session["LastMinuteOfDay"] = (
        daily_session["LastCloseNY"].dt.hour * 60
        + daily_session["LastCloseNY"].dt.minute
    )

    hourly_presence = (
        frame.group_by(
            [
                "Symbol",
                "Segment",
                "NYDate",
                pl.col("CloseTimeNY").dt.hour().alias("NYHour"),
            ]
        )
        .agg(pl.len().alias("ObservedBars"))
        .rename({"Symbol": "Instrument"})
        .to_pandas()
    )
    day_counts = (
        daily_session.groupby(["Instrument", "Segment"], as_index=False)
        .agg(TradingDays=("NYDate", "nunique"))
    )
    hourly_summary = (
        hourly_presence.groupby(["Instrument", "Segment", "NYHour"], as_index=False)
        .agg(DaysPresent=("NYDate", "nunique"))
        .merge(day_counts, on=["Instrument", "Segment"], how="left")
    )
    hourly_summary["PresenceShare"] = (
        hourly_summary["DaysPresent"] / hourly_summary["TradingDays"]
    )

    summary = (
        daily_session.groupby(["Instrument", "Segment"], as_index=False)
        .agg(
            TradingDays=("NYDate", "nunique"),
            MedianFirstMinute=("FirstMinuteOfDay", "median"),
            MedianLastMinute=("LastMinuteOfDay", "median"),
            MinFirstMinute=("FirstMinuteOfDay", "min"),
            MaxLastMinute=("LastMinuteOfDay", "max"),
            MeanBarsPerDay=("ObservedBars", "mean"),
        )
    )
    summary["MedianFirstMinute"] = summary["MedianFirstMinute"].round().astype(int)
    summary["MedianLastMinute"] = summary["MedianLastMinute"].round().astype(int)
    return summary.sort_values(
        ["Instrument", "Segment"]
    ).reset_index(drop=True), hourly_summary.sort_values(
        ["Instrument", "Segment", "NYHour"]
    ).reset_index(drop=True)


def cost_schema_summary(instrument_paths_map: dict[str, list[Path]]) -> pd.DataFrame:
    """Declare cost-field availability from the actual scoped time-bar files.

    Checks each instrument separately. Logs a warning if availability differs across
    instruments so that a single-instrument schema difference does not silently produce
    a misleading phase-wide 'available' result.
    """
    unavailable_fields = ["Bid", "Ask", "Spread", "Commission", "Slippage"]
    per_instrument: dict[str, set[str]] = {}
    for instrument, paths in instrument_paths_map.items():
        cols: set[str] = set()
        for path in paths:
            cols.update(pl.scan_parquet(path).collect_schema().names())
        per_instrument[instrument] = cols

    for field in unavailable_fields:
        availability = {instr: (field in cols) for instr, cols in per_instrument.items()}
        if len(set(availability.values())) > 1:
            LOGGER.warning(
                "Cost field '%s' availability differs across instruments: %s",
                field,
                availability,
            )

    all_columns: set[str] = set().union(*per_instrument.values())
    return pd.DataFrame(
        [
            {
                "Field": field,
                "AvailableInTimeBarSchema": field in all_columns,
            }
            for field in unavailable_fields
        ]
    )


def evaluate_readiness(
    family_summary: pd.DataFrame,
    cost_availability: pd.DataFrame,
) -> tuple[str, pd.DataFrame]:
    """Apply the scope verdict rules at the instrument and phase level."""
    instrument_rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        subset = family_summary[family_summary["Instrument"] == instrument]
        if len(subset) != 4:
            raise ValueError(
                f"{instrument}: expected 4 family×segment rows in family_summary, got {len(subset)}"
            )
        family_pass = bool(
            (subset["CoverageRatio"] >= MACRO_FAMILY_COVERAGE_THRESHOLD).all()
        )
        instrument_rows.append(
            {
                "Instrument": instrument,
                "NYConversionAssumption": f"Naive CloseTime treated as {SOURCE_TIMEZONE_ASSUMPTION}",
                "MacroFamilyCoveragePass": family_pass,
            }
        )

    readiness = pd.DataFrame(instrument_rows)
    readiness["CostProxyRequired"] = not cost_availability["AvailableInTimeBarSchema"].all()
    pass_count = int(readiness["MacroFamilyCoveragePass"].sum())

    if pass_count == len(INSTRUMENTS):
        verdict = "SUPPORTED"
    elif (len(INSTRUMENTS) - pass_count) >= 3:
        verdict = "AGAINST"
    else:
        verdict = "INCONCLUSIVE"
    return verdict, readiness


def format_minute_of_day(minute_of_day: int) -> str:
    """Format a minute-of-day integer as HH:MM."""
    hour = minute_of_day // 60
    minute = minute_of_day % 60
    return f"{hour:02d}:{minute:02d}"


def _format_hour_ranges(hours: list[int]) -> str:
    """Format a sorted list of hours as compact ranges, e.g. [0,1,2,9,10] -> '00-02, 09-10'."""
    if not hours:
        return ""
    sorted_hours = sorted(set(hours))
    ranges: list[str] = []
    start = end = sorted_hours[0]
    for h in sorted_hours[1:]:
        if h == end + 1:
            end = h
        else:
            ranges.append(f"{start:02d}-{end:02d}" if start != end else f"{start:02d}")
            start = end = h
    ranges.append(f"{start:02d}-{end:02d}" if start != end else f"{start:02d}")
    return ", ".join(ranges)


def plot_macro_window_coverage(window_summary: pd.DataFrame, save_path: Path) -> None:
    """Plot train/test macro-window coverage by instrument."""
    sns.set_theme(style="whitegrid")
    plot_df = window_summary.copy()
    plot_df["RowLabel"] = plot_df["Instrument"] + " " + plot_df["Segment"]
    pivot = (
        plot_df.pivot(index="RowLabel", columns="Window", values="CoverageRatio")
        .reindex(
            [
                f"{instrument} {segment}"
                for instrument in INSTRUMENTS
                for segment in ("Train", "Test")
            ]
        )
    )
    fig, ax = plt.subplots(figsize=(11, 5.5))
    sns.heatmap(
        pivot,
        annot=True,
        fmt=".2f",
        cmap="viridis",
        vmin=0.0,
        vmax=1.0,
        linewidths=0.5,
        cbar_kws={"label": "Observed / expected bars"},
        ax=ax,
    )
    ax.set_title("EXP-012 Macro-Window Coverage by Instrument and Segment")
    ax.set_xlabel("Macro window")
    ax.set_ylabel("")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_missing_bar_rates(missing_summary: pd.DataFrame, save_path: Path) -> None:
    """Plot within-session missing-bar rates by instrument and segment."""
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(
        data=missing_summary,
        x="Instrument",
        y="MissingRateWithinObservedSpan",
        hue="Segment",
        order=INSTRUMENTS,
        ax=ax,
    )
    ax.set_title("EXP-012 Missing-Bar Rate Within Observed Daily Span")
    ax.set_xlabel("")
    ax.set_ylabel("Missing bars / expected bars")
    ax.set_ylim(0.0, max(0.02, missing_summary["MissingRateWithinObservedSpan"].max() * 1.2))
    ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def write_outputs(
    inventory_rows: list[dict[str, Any]],
    daily_window: pd.DataFrame,
    window_summary: pd.DataFrame,
    family_summary: pd.DataFrame,
    daily_missing: pd.DataFrame,
    missing_summary: pd.DataFrame,
    active_session_summary: pd.DataFrame,
    hourly_session_summary: pd.DataFrame,
    cost_availability: pd.DataFrame,
    readiness_summary: pd.DataFrame,
    verdict: str,
    plots_dir: Path,
    results_dir: Path,
) -> None:
    """Write scoped machine-readable and human-readable outputs."""
    inventory_df = pd.DataFrame(inventory_rows)
    inventory_df.to_csv(results_dir / "inventory_summary.csv", index=False)
    daily_window.to_csv(results_dir / "daily_macro_window_coverage.csv", index=False)
    window_summary.to_csv(results_dir / "macro_window_coverage_summary.csv", index=False)
    family_summary.to_csv(results_dir / "macro_family_coverage_summary.csv", index=False)
    daily_missing.to_csv(results_dir / "daily_missing_bar_summary.csv", index=False)
    missing_summary.to_csv(results_dir / "missing_bar_summary.csv", index=False)
    active_session_summary.to_csv(results_dir / "active_session_summary.csv", index=False)
    hourly_session_summary.to_csv(results_dir / "hourly_session_presence.csv", index=False)
    cost_availability.to_csv(results_dir / "cost_data_availability.csv", index=False)

    with (results_dir / "cost_proxy_scenarios.json").open("w", encoding="utf-8") as handle:
        json.dump(COST_PROXY_SCENARIOS, handle, indent=2)

    # Compute per-window below-threshold entries and cross-segment coverage gaps for JSON.
    below_threshold = [
        {
            "Instrument": row.Instrument,
            "Segment": row.Segment,
            "Window": row.Window,
            "CoverageRatio": round(float(row.CoverageRatio), 4),
        }
        for row in window_summary.itertuples(index=False)
        if row.CoverageRatio < MACRO_FAMILY_COVERAGE_THRESHOLD
    ]

    family_pivot = family_summary.pivot_table(
        index=["Instrument", "Family"],
        columns="Segment",
        values="CoverageRatio",
    ).reset_index()
    coverage_gaps: list[dict[str, Any]] = []
    if "Train" in family_pivot.columns and "Test" in family_pivot.columns:
        family_pivot["Gap"] = (family_pivot["Train"] - family_pivot["Test"]).abs()
        for row in family_pivot[family_pivot["Gap"] > 0.05].itertuples(index=False):
            coverage_gaps.append(
                {
                    "Instrument": row.Instrument,
                    "Family": row.Family,
                    "TrainCoverage": round(float(row.Train), 4),
                    "TestCoverage": round(float(row.Test), 4),
                    "AbsGap": round(float(row.Gap), 4),
                }
            )

    summary_payload = {
        "experiment_id": "EXP-012",
        "title": "ICT Data Readiness and Feasibility",
        "verdict": verdict,
        "source_timezone_assumption": SOURCE_TIMEZONE_ASSUMPTION,
        "target_timezone": NY_TIMEZONE,
        "family_coverage_threshold": MACRO_FAMILY_COVERAGE_THRESHOLD,
        "coverage_denominator_note": (
            "Coverage ratios are computed on Monday-Friday dates only. "
            "Sunday and Saturday entries (present in FX/CFD feeds from ~17:00 ET Sunday) "
            "are excluded because they carry zero macro-window bars and would inflate the "
            "denominator. US market holidays that fall on weekdays remain in the denominator."
        ),
        "close_time_window_boundary_assumption": (
            "MacroWindow membership is assigned by CloseTimeNY minute. "
            "A bar with CloseTime at the window StartMinute is the first bar of that window "
            "(e.g., CloseTime=07:50 ET → first bar of AM1). "
            "Downstream experiments using OpenTime-based window membership will have a "
            "1-minute boundary offset relative to this experiment."
        ),
        "readiness_summary": readiness_summary.to_dict(orient="records"),
        "per_window_below_threshold": below_threshold,
        "cross_segment_coverage_gaps": coverage_gaps,
        "cost_fields_present": cost_availability.to_dict(orient="records"),
        "cost_proxy_scenarios": COST_PROXY_SCENARIOS,
    }
    with (results_dir / "results.json").open("w", encoding="utf-8") as handle:
        json.dump(summary_payload, handle, indent=2, default=str)

    with (results_dir / "numerical_summary.txt").open("w", encoding="utf-8") as handle:
        handle.write("EXP-012 ICT Data Readiness and Feasibility\n")
        handle.write(f"Verdict: {verdict}\n")
        handle.write(
            "Timestamp assumption: naive CloseTime values are treated as "
            f"{SOURCE_TIMEZONE_ASSUMPTION} and converted to {NY_TIMEZONE}. "
            "MacroWindow membership is assigned by CloseTimeNY minute: a bar with "
            "CloseTime at the window boundary is the first bar of that window. "
            "Downstream experiments using OpenTime-based window logic will have a "
            "1-minute boundary offset.\n"
        )
        handle.write(
            "Coverage denominator: Monday-Friday dates only. Sunday/Saturday entries "
            "are excluded from both expected-bar and observed-bar counts to prevent "
            "off-session dates from inflating the denominator.\n"
        )
        handle.write(
            "Cost data: bid/ask/spread/commission/slippage fields are absent from the"
            " time-bar schema; proxy scenarios were written to"
            f" {results_dir / 'cost_proxy_scenarios.json'}.\n"
        )
        handle.write("\nMacro-family coverage summary (threshold >= 0.80):\n")
        for row in family_summary.itertuples(index=False):
            flag = " [BELOW THRESHOLD]" if row.CoverageRatio < MACRO_FAMILY_COVERAGE_THRESHOLD else ""
            handle.write(
                f"- {row.Instrument} {row.Segment} {row.Family}: "
                f"{row.CoverageRatio:.3f} ({row.ObservedBars}/{row.ExpectedBars}){flag}\n"
            )
        handle.write("\nPer-window coverage (windows below threshold flagged):\n")
        for row in window_summary.itertuples(index=False):
            flag = " [BELOW THRESHOLD]" if row.CoverageRatio < MACRO_FAMILY_COVERAGE_THRESHOLD else ""
            handle.write(
                f"- {row.Instrument} {row.Segment} {row.Window}: "
                f"{row.CoverageRatio:.3f} ({row.ObservedBars}/{row.ExpectedBars}){flag}\n"
            )
        if coverage_gaps:
            handle.write("\nCross-segment coverage gaps (|Train - Test| > 0.05 by family):\n")
            for gap in coverage_gaps:
                handle.write(
                    f"- {gap['Instrument']} {gap['Family']}: "
                    f"Train={gap['TrainCoverage']:.3f}, Test={gap['TestCoverage']:.3f}, "
                    f"gap={gap['AbsGap']:.3f}\n"
                )
        else:
            handle.write("\nCross-segment coverage gaps: none above 0.05.\n")
        handle.write("\nObserved active-session summary:\n")
        for row in active_session_summary.itertuples(index=False):
            handle.write(
                f"- {row.Instrument} {row.Segment}: median NY session "
                f"{format_minute_of_day(row.MedianFirstMinute)}-"
                f"{format_minute_of_day(row.MedianLastMinute)} "
                f"across {row.TradingDays} dates\n"
            )
        handle.write("\nHourly presence (NY hours present on >= 90% of trading days):\n")
        day_counts = (
            hourly_session_summary.groupby(["Instrument", "Segment"], as_index=False)
            .agg(TradingDays=("TradingDays", "first"))
        )
        for (instrument, segment), group in hourly_session_summary.groupby(
            ["Instrument", "Segment"]
        ):
            high_presence = group[group["PresenceShare"] >= 0.90]["NYHour"].tolist()
            hour_str = _format_hour_ranges(high_presence) if high_presence else "none"
            handle.write(f"- {instrument} {segment}: NY hours {hour_str}\n")

    plot_macro_window_coverage(
        window_summary,
        plots_dir / "01_macro_window_coverage_heatmap.png",
    )
    plot_missing_bar_rates(
        missing_summary,
        plots_dir / "02_missing_bar_rate_by_segment.png",
    )


def run_experiment() -> None:
    """Execute the EXP-012 readiness workflow."""
    plots_dir = EXP_DIR / "plots"
    results_dir = EXP_DIR / "results"
    plots_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    inventory_rows: list[dict[str, Any]] = []
    instrument_paths_map: dict[str, list[Path]] = {}
    daily_window_parts: list[pd.DataFrame] = []
    daily_missing_parts: list[pd.DataFrame] = []
    missing_summary_parts: list[pd.DataFrame] = []
    active_session_parts: list[pd.DataFrame] = []
    hourly_session_parts: list[pd.DataFrame] = []

    for instrument in INSTRUMENTS:
        LOGGER.info("loading %s analysis-set time bars", instrument)
        analysis_df, analysis_rows, train_rows, total_rows, input_paths = load_analysis_timebars(instrument)
        instrument_paths_map[instrument] = input_paths
        inventory_rows.append(
            summarize_inventory(
                analysis_df,
                input_paths,
                total_rows,
                analysis_rows,
                train_rows,
            )
        )
        if analysis_df.is_empty():
            continue

        train_end = train_cutoff_time(analysis_df, train_rows)
        ny_frame = add_ny_time_features(analysis_df, train_end)

        weekday_ny_frame = ny_frame.filter(
            pl.col("NYDate").dt.weekday().is_in([1, 2, 3, 4, 5])
        )
        daily_window_parts.append(build_daily_window_coverage(ny_frame))
        daily_missing, missing_summary = summarize_missing_bars(ny_frame)
        daily_missing_parts.append(daily_missing)
        missing_summary_parts.append(missing_summary)
        active_session_summary, hourly_session_summary = summarize_active_session(weekday_ny_frame)
        active_session_parts.append(active_session_summary)
        hourly_session_parts.append(hourly_session_summary)

    if not daily_window_parts:
        raise ValueError("No analysis-set rows were loaded for any scoped instrument.")

    daily_window = pd.concat(daily_window_parts, ignore_index=True)
    window_summary = summarize_window_coverage(daily_window)
    family_summary = summarize_family_coverage(daily_window)
    daily_missing = pd.concat(daily_missing_parts, ignore_index=True)
    missing_summary = pd.concat(missing_summary_parts, ignore_index=True)
    active_session_summary = pd.concat(active_session_parts, ignore_index=True)
    hourly_session_summary = pd.concat(hourly_session_parts, ignore_index=True)
    cost_availability = cost_schema_summary(instrument_paths_map)
    verdict, readiness_summary = evaluate_readiness(family_summary, cost_availability)

    write_outputs(
        inventory_rows,
        daily_window,
        window_summary,
        family_summary,
        daily_missing,
        missing_summary,
        active_session_summary,
        hourly_session_summary,
        cost_availability,
        readiness_summary,
        verdict,
        plots_dir,
        results_dir,
    )

    print("EXP-012 complete.")
    print(f"Verdict: {verdict}")
    print(f"Plots: {plots_dir}")
    print(f"Results: {results_dir}")


def main() -> None:
    """Entry point for manual execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_experiment()


if __name__ == "__main__":
    main()
