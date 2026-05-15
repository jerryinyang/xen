"""
Experiment EXP-002: Volatility & Trend Regime Representation
Implements the analysis plan from analysis-plan.md.
"""
import sys
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[3]
PROJECT_ROOT = PYTHON_ROOT.parent
SRC_DIR = PYTHON_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

import numpy as np
import pandas as pd
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Any

from linebreak_generator import generate_linebreak
from renko_generator import generate_renko
from heiken_ashi_generator import generate_heiken_ashi
from time_alignment import normalize_timestamp_columns

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
INSTRUMENTS = ["EURUSD", "XAUUSD", "BTCUSD", "USTEC"]

CHART_CONFIG: dict[str, dict[str, Any]] = {
    "Time": {
        "generator": None,
        "params": {},
        "time_col": "CloseTime",
        "direction_col": "Direction",
        "close_col": "Close",
        "needs_direction": True,
    },
    "LineBreak3": {
        "generator": "linebreak",
        "params": {"level": 3},
        "time_col": "SourceCloseTime",
        "direction_col": "Direction",
        "close_col": "RealClose",
        "needs_direction": False,
    },
    "Renko": {
        "generator": "renko",
        "params": {"atr_period": 14},
        "time_col": "SourceCloseTime",
        "direction_col": "Direction",
        "close_col": "RealClose",
        "needs_direction": False,
    },
    "HeikenAshi": {
        "generator": "heiken_ashi",
        "params": {},
        "time_col": "CloseTime",
        "direction_col": "Direction",
        "close_col": "RealClose",
        "needs_direction": False,
    },
}

DATA_DIR = PROJECT_ROOT / "data"
PLOTS_DIR = PYTHON_ROOT / "experiments/EXP-002/plots"
RESULTS_DIR = PYTHON_ROOT / "experiments/EXP-002/results"
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

BOOTSTRAP_SEED = 42
N_BOOTSTRAP = 10_000
ROLLING_VOL_WINDOW = 20


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def scan_timebar_data(instrument: str) -> pl.LazyFrame:
    """Scan all time-bar Parquet files for an instrument.

    Parameters
    ----------
    instrument : str
        Instrument symbol (e.g. "EURUSD").

    Returns
    -------
    pl.LazyFrame
        Sorted, deduplicated lazy time-bar scan.
    """

    pattern = f"timebars/timebars_{instrument.lower()}_*.parquet"
    matches = sorted(DATA_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(
            f"No time-bar file found for {instrument} matching {pattern}"
        )
    return (
        pl.scan_parquet(matches)
        .select(TIMEBAR_COLUMNS)
        .sort("CloseTime")
        .unique(maintain_order=True)
    )


def load_analysis_timebar_data(instrument: str) -> tuple[pl.DataFrame, int]:
    """Load only the first 70% chronological analysis slice.

    The full dataset row count is used only to determine the global holdout
    boundary. The returned DataFrame excludes the final 30% holdout.

    Parameters
    ----------
    instrument : str
        Instrument symbol (e.g. "EURUSD").

    Returns
    -------
    tuple[pl.DataFrame, int]
        Analysis-set bars and full source row count.
    """
    scan = scan_timebar_data(instrument)
    source_rows = scan.select(pl.len()).collect().item()
    analysis_rows = int(source_rows * 0.7)
    analysis_df = (
        scan
        .slice(0, analysis_rows)
        .collect()
    )
    return analysis_df, source_rows


# ---------------------------------------------------------------------------
# Chart generation
# ---------------------------------------------------------------------------
def generate_chart(
    time_bars: pl.DataFrame,
    config: dict[str, Any],
) -> pl.DataFrame:
    """Generate a chart-type DataFrame according to config.

    Parameters
    ----------
    time_bars : pl.DataFrame
        Source 1-minute time bars.
    config : dict[str, Any]
        Chart-type configuration from CHART_CONFIG.

    Returns
    -------
    pl.DataFrame
        Generated chart-type bars.
    """
    gen = config["generator"]
    if gen is None:
        return time_bars.clone()
    if gen == "linebreak":
        return generate_linebreak(time_bars, **config["params"])
    if gen == "renko":
        return generate_renko(time_bars, **config["params"])
    if gen == "heiken_ashi":
        return generate_heiken_ashi(time_bars)
    raise ValueError(f"Unknown generator: {gen}")


# ---------------------------------------------------------------------------
# Regime labelling (from time bars only, no look-ahead)
# ---------------------------------------------------------------------------
def compute_realised_volatility(time_bars: pl.DataFrame) -> pl.DataFrame:
    """Add rolling realised volatility to time bars.

    Uses log-range proxy: ln(High) - ln(Low) per bar, then
    rolling mean over ``ROLLING_VOL_WINDOW`` bars.

    Parameters
    ----------
    time_bars : pl.DataFrame
        1-minute time bars.

    Returns
    -------
    pl.DataFrame
        Time bars with ``RealisedVol`` column.
    """
    log_high = (pl.col("High") + 1e-12).log()
    log_low = (pl.col("Low") + 1e-12).log()
    vol = (log_high - log_low).rolling_mean(window_size=ROLLING_VOL_WINDOW)
    return time_bars.with_columns(vol.alias("RealisedVol"))


def assign_regime_terciles(
    time_bars: pl.DataFrame,
    train_df: pl.DataFrame,
) -> pl.DataFrame:
    """Assign low/medium/high regime labels using train-derived terciles.

    Parameters
    ----------
    time_bars : pl.DataFrame
        Full analysis-set time bars with ``RealisedVol``.
    train_df : pl.DataFrame
        Train-segment time bars (used only for tercile thresholds).

    Returns
    -------
    pl.DataFrame
        Time bars with ``Regime`` column (1=low, 2=medium, 3=high).
    """
    train_vol = train_df["RealisedVol"].drop_nulls().to_numpy()
    train_vol = train_vol[np.isfinite(train_vol)]
    if len(train_vol) == 0:
        return time_bars.with_columns(
            pl.lit(None).cast(pl.Int8).alias("Regime")
        )
    q33, q66 = np.quantile(train_vol, [1 / 3, 2 / 3])
    regime = (
        pl.when(pl.col("RealisedVol") <= q33)
        .then(1)
        .when(pl.col("RealisedVol") <= q66)
        .then(2)
        .otherwise(3)
    )
    return time_bars.with_columns(regime.alias("Regime"))


# ---------------------------------------------------------------------------
# Hybrid rate & transition lag
# ---------------------------------------------------------------------------
def compute_hybrid_rate(
    chart_df: pl.DataFrame,
    time_bars: pl.DataFrame,
    time_col: str,
    regime_col: str = "Regime",
) -> float:
    """Fraction of chart bars spanning regime boundaries.

    A bar is hybrid if any time bar it covers has a different regime
    from the bar's assigned regime. Time bars and Heiken Ashi (1:1
    mapping) have hybrid rate 0 by construction.

    Parameters
    ----------
    chart_df : pl.DataFrame
        Chart-type bars with regime labels attached.
    time_bars : pl.DataFrame
        Source time bars with ``CloseTime`` and regime labels.
    time_col : str
        Timestamp column for ordering.
    regime_col : str, optional
        Regime label column.

    Returns
    -------
    float
        Hybrid rate (0.0 if empty).
    """
    if len(chart_df) <= 1:
        return 0.0
    chart_sorted = chart_df.sort(time_col).select([time_col, regime_col])
    time_sorted = time_bars.sort("CloseTime").select(["CloseTime", regime_col])

    chart_times = chart_sorted[time_col].to_numpy()
    chart_regimes = chart_sorted[regime_col].to_numpy()
    time_times = time_sorted["CloseTime"].to_numpy()
    time_regimes = time_sorted[regime_col].to_numpy()

    # Fast path: 1:1 mapping (Time bars, Heiken Ashi).
    if len(chart_times) == len(time_times) and np.array_equal(
        chart_times, time_times
    ):
        return 0.0

    valid_time_mask = np.isfinite(time_regimes.astype(float))
    if not valid_time_mask.any():
        return 0.0

    # Prefix counts let each chart interval be checked in O(1) after sorting.
    regime_values = [1, 2, 3]
    prefix_counts = {
        value: np.concatenate(
            [[0], np.cumsum((time_regimes == value).astype(np.int64))]
        )
        for value in regime_values
    }
    valid_prefix = np.concatenate([[0], np.cumsum(valid_time_mask.astype(np.int64))])

    prev_times = np.empty_like(chart_times)
    prev_times[0] = chart_times[0]
    prev_times[1:] = chart_times[:-1]
    starts = np.searchsorted(time_times, prev_times, side="right")
    ends = np.searchsorted(time_times, chart_times, side="right")
    starts[0] = ends[0]

    hybrid_count = 0
    for start, end, regime in zip(starts, ends, chart_regimes):
        covered_count = valid_prefix[end] - valid_prefix[start]
        if covered_count == 0 or regime not in regime_values:
            continue
        same_regime_count = prefix_counts[int(regime)][end] - prefix_counts[int(regime)][start]
        if same_regime_count != covered_count:
            hybrid_count += 1

    return hybrid_count / len(chart_times)


def compute_transition_lags(
    chart_df: pl.DataFrame,
    time_bars: pl.DataFrame,
    time_col: str,
    regime_col: str = "Regime",
) -> np.ndarray:
    """Lags (in time-bar counts) from time-bar regime transition to chart bar.

    For each regime transition in the time-bar series, find the first
    chart bar at or after that timestamp and record the number of time
    bars between the transition and the chart bar.

    Parameters
    ----------
    chart_df : pl.DataFrame
        Chart-type bars with regime labels and timestamps.
    time_bars : pl.DataFrame
        Source time bars with ``CloseTime`` and regime labels.
    time_col : str
        Timestamp column.
    regime_col : str, optional
        Regime label column.

    Returns
    -------
    np.ndarray
        Array of lag values in time-bar counts (empty if no transitions).
    """
    if len(chart_df) <= 1:
        return np.array([], dtype=float)

    time_sorted = time_bars.sort("CloseTime").select(["CloseTime", regime_col])
    chart_sorted = chart_df.sort(time_col).select(time_col)

    time_times = time_sorted["CloseTime"].to_numpy()
    time_regimes = time_sorted[regime_col].to_numpy()
    chart_times = chart_sorted[time_col].to_numpy()

    valid_time_mask = np.isfinite(time_regimes.astype(float))
    comparable_pairs = valid_time_mask[1:] & valid_time_mask[:-1]
    trans_idx = np.where(
        comparable_pairs & (time_regimes[1:] != time_regimes[:-1])
    )[0] + 1
    if len(trans_idx) == 0:
        return np.array([], dtype=float)

    chart_positions = np.searchsorted(
        chart_times, time_times[trans_idx], side="left"
    )
    valid_chart_positions = chart_positions < len(chart_times)
    if not valid_chart_positions.any():
        return np.array([], dtype=float)

    matched_chart_times = chart_times[chart_positions[valid_chart_positions]]
    matched_time_idx = np.searchsorted(time_times, matched_chart_times, side="left")
    matched_trans_idx = trans_idx[valid_chart_positions]
    return (matched_time_idx - matched_trans_idx).astype(float)


def compute_median_lag_by_instrument(
    chart_df: pl.DataFrame,
    time_bars: pl.DataFrame,
    time_col: str,
    regime_col: str = "Regime",
) -> float:
    """Median transition lag for a chart-type DataFrame.

    Parameters
    ----------
    chart_df : pl.DataFrame
        Chart-type bars with regime labels.
    time_bars : pl.DataFrame
        Source time bars with ``CloseTime`` and regime labels.
    time_col : str
        Timestamp column.
    regime_col : str, optional
        Regime label column.

    Returns
    -------
    float
        Median lag in time-bar counts (NaN if no transitions).
    """
    lags = compute_transition_lags(
        chart_df, time_bars, time_col, regime_col
    )
    if len(lags) == 0:
        return np.nan
    return float(np.median(lags))


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
def bootstrap_mean_ci(
    values: np.ndarray,
    n_bootstrap: int = N_BOOTSTRAP,
    seed: int = BOOTSTRAP_SEED,
    confidence: float = 0.95,
) -> tuple[float, float, float]:
    """Bootstrap percentile CI for the mean of paired differences.

    Parameters
    ----------
    values : np.ndarray
        Paired differences (one per instrument).
    n_bootstrap : int, optional
        Number of bootstrap samples.
    seed : int, optional
        Random seed for reproducibility.
    confidence : float, optional
        Confidence level.

    Returns
    -------
    tuple[float, float, float]
        (mean, lower_bound, upper_bound).
    """
    if len(values) == 0:
        return (np.nan, np.nan, np.nan)
    rng = np.random.default_rng(seed)
    means = []
    n = len(values)
    for _ in range(n_bootstrap):
        sample = rng.choice(values, size=n, replace=True)
        means.append(np.mean(sample))
    means_arr = np.array(means)
    alpha = 1 - confidence
    return (
        float(np.mean(values)),
        float(np.quantile(means_arr, alpha / 2)),
        float(np.quantile(means_arr, 1 - alpha / 2)),
    )


# ---------------------------------------------------------------------------
# Plotting functions
# ---------------------------------------------------------------------------
def plot_regime_timeline(
    time_bars: pl.DataFrame,
    chart_events: dict[str, pl.DataFrame],
    save_path: Path,
) -> plt.Figure:
    """Regime timeline with chart-type events overlaid for one instrument.

    Parameters
    ----------
    time_bars : pl.DataFrame
        Time bars with ``CloseTime`` and ``Regime``.
    chart_events : dict[str, pl.DataFrame]
        Mapping chart-type name to event DataFrame with timestamps.
    save_path : Path
        File path to save the figure.

    Returns
    -------
    plt.Figure
        The figure object.
    """
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(14, 5))

    tb = time_bars.sort("CloseTime").to_pandas()
    ax.fill_between(
        tb["CloseTime"],
        tb["Regime"] - 0.4,
        tb["Regime"] + 0.4,
        step="mid",
        alpha=0.3,
        label="Time-bar regime",
    )

    colors = {"LineBreak3": "C1", "Renko": "C2", "HeikenAshi": "C3"}
    for chart_name, cdf in chart_events.items():
        if chart_name == "Time":
            continue
        time_col = "SourceCloseTime" if "SourceCloseTime" in cdf.columns else "CloseTime"
        cdf_pd = cdf.sort(time_col).to_pandas()
        ax.scatter(
            cdf_pd[time_col],
            cdf_pd["Regime"],
            s=8,
            alpha=0.6,
            label=f"{chart_name} events",
            color=colors.get(chart_name, None),
        )

    ax.set_title("Regime Timeline with Chart-Type Events")
    ax.set_xlabel("Time")
    ax.set_ylabel("Regime (1=low, 2=medium, 3=high)")
    ax.set_yticks([1, 2, 3])
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


def plot_hybrid_rate(
    df: pd.DataFrame,
    save_path: Path,
) -> plt.Figure:
    """Grouped bar chart of hybrid rate by instrument and chart type.

    Parameters
    ----------
    df : pd.DataFrame
        Summary DataFrame with ``Instrument``, ``ChartType``, ``HybridRate``.
    save_path : Path
        File path to save the figure.

    Returns
    -------
    plt.Figure
        The figure object.
    """
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(
        data=df, x="Instrument", y="HybridRate", hue="ChartType", ax=ax
    )
    ax.set_title("Hybrid Rate by Instrument and Chart Type")
    ax.set_ylabel("Hybrid Rate")
    ax.set_xlabel("Instrument")
    ax.legend(title="Chart Type", loc="upper right")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


def plot_lag_boxplot(
    df: pd.DataFrame,
    save_path: Path,
) -> plt.Figure:
    """Box plot of transition lag by chart type, faceted by instrument.

    Parameters
    ----------
    df : pd.DataFrame
        Long-format DataFrame with ``Instrument``, ``ChartType``, ``Lag``.
    save_path : Path
        File path to save the figure.

    Returns
    -------
    plt.Figure
        The figure object.
    """
    sns.set_theme(style="whitegrid")
    g = sns.catplot(
        data=df,
        kind="box",
        x="ChartType",
        y="Lag",
        col="Instrument",
        col_wrap=2,
        height=4,
        aspect=1.2,
        sharey=False,
    )
    g.set_axis_labels("Chart Type", "Transition Lag (bars)")
    g.set_titles("{col_name}")
    g.fig.suptitle(
        "Transition Lag by Chart Type",
        y=1.02,
        fontsize=12,
    )
    g.fig.tight_layout()
    g.fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(g.fig)
    return g.fig


def plot_improvement_heatmap(
    df: pd.DataFrame,
    save_path: Path,
) -> plt.Figure:
    """Heatmap of improvement versus time bars by instrument and metric.

    Creates one heatmap panel per chart type.

    Parameters
    ----------
    df : pd.DataFrame
        Summary DataFrame with ``Instrument``, ``ChartType``, ``Metric``,
        ``Improvement``.
    save_path : Path
        File path to save the figure.

    Returns
    -------
    plt.Figure
        The figure object.
    """
    sns.set_theme(style="white")
    chart_types = sorted(df["ChartType"].unique())
    n_charts = len(chart_types)

    fig, axes = plt.subplots(1, n_charts, figsize=(6 * n_charts, 5))
    if n_charts == 1:
        axes = [axes]

    for ax, chart_type in zip(axes, chart_types):
        sub = df[df["ChartType"] == chart_type]
        pivot = sub.pivot(
            index="Instrument", columns="Metric", values="Improvement"
        )
        if pivot.notna().any().any():
            sns.heatmap(
                pivot,
                annot=True,
                fmt=".2%",
                cmap="RdYlGn",
                center=0,
                ax=ax,
                cbar_kws={"label": "Improvement vs Time Bars"},
            )
        else:
            ax.imshow([[0]], cmap="Greys", alpha=0.15)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.text(
                0,
                0,
                "No defined improvements",
                ha="center",
                va="center",
            )
        ax.set_title(f"{chart_type} vs Time")
        ax.set_ylabel("Instrument")
        ax.set_xlabel("Metric")

    fig.suptitle(
        "Improvement vs Time Bars by Instrument and Metric",
        y=1.02,
        fontsize=12,
    )
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def main() -> None:
    """Run the full EXP-002 analysis pipeline."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("EXP-002: Volatility & Trend Regime Representation")
    print(f"Instruments: {', '.join(INSTRUMENTS)}")
    print("Chart types: Time, LineBreak3, Renko, HeikenAshi")
    print(f"Output: {PLOTS_DIR} and {RESULTS_DIR}\n")

    summary_records: list[dict[str, Any]] = []
    validation_records: list[dict[str, Any]] = []
    lag_records: list[dict[str, Any]] = []
    improvement_records: list[dict[str, Any]] = []
    bootstrap_records: list[dict[str, Any]] = []

    instrument_metrics: dict[str, dict[str, dict[str, float]]] = {}
    timeline_events: dict[str, dict[str, pl.DataFrame]] = {}
    timeline_time_bars: pl.DataFrame | None = None

    for instrument in INSTRUMENTS:
        try:
            print(f"Processing {instrument} ...")
            analysis_df, source_rows = load_analysis_timebar_data(instrument)
            if len(analysis_df) == 0:
                print(f"  Skipping {instrument}: empty dataset")
                continue

            n_analysis = len(analysis_df)
            train_cutoff = int(n_analysis * 0.7)
            train_df = analysis_df.slice(0, train_cutoff)
            test_df = analysis_df.slice(train_cutoff, n_analysis - train_cutoff)

            # Compute realised volatility and regimes from time bars
            analysis_df = compute_realised_volatility(analysis_df)
            train_df = compute_realised_volatility(train_df)
            analysis_df = assign_regime_terciles(analysis_df, train_df)

            # Build regime lookup table by timestamp
            regime_table = analysis_df.select(["CloseTime", "Regime"])
            normalized_regime_tables: dict[str, pl.DataFrame] = {}
            for config in CHART_CONFIG.values():
                time_col = config["time_col"]
                if time_col in normalized_regime_tables:
                    continue
                lookup = regime_table.rename({"CloseTime": time_col})
                normalized_regime_tables[time_col] = normalize_timestamp_columns(
                    lookup, [time_col]
                )

            instrument_metrics[instrument] = {}
            timeline_events[instrument] = {}

            for chart_name, config in CHART_CONFIG.items():
                chart_df = generate_chart(analysis_df, config)

                # Add Direction for time bars if missing
                if config.get("needs_direction"):
                    chart_df = chart_df.with_columns(
                        pl.when(pl.col("Close") >= pl.col("Open"))
                        .then(1)
                        .otherwise(-1)
                        .cast(pl.Int32)
                        .alias("Direction")
                    )

                # Attach real close for event bars
                if chart_name in ("LineBreak3", "Renko", "HeikenAshi"):
                    chart_df = normalize_timestamp_columns(
                        chart_df, [config["time_col"]]
                    )
                    chart_df = chart_df.join(
                        normalized_regime_tables[config["time_col"]],
                        on=config["time_col"],
                        how="left",
                    )
                else:
                    # Time bars already have Regime
                    chart_df = chart_df.with_columns(
                        pl.col("Regime").alias("Regime")
                    )

                # Drop rows with missing regime labels
                chart_df = chart_df.drop_nulls(subset=["Regime"])

                hybrid = compute_hybrid_rate(
                    chart_df, analysis_df, config["time_col"]
                )
                lags = compute_transition_lags(
                    chart_df, analysis_df, config["time_col"]
                )
                median_lag = float(np.median(lags)) if len(lags) else np.nan
                n_bars = len(chart_df)

                start_time = (
                    chart_df[config["time_col"]].min()
                    if n_bars > 0
                    else None
                )
                end_time = (
                    chart_df[config["time_col"]].max()
                    if n_bars > 0
                    else None
                )

                summary_records.append(
                    {
                        "Instrument": instrument,
                        "ChartType": chart_name,
                        "AnalysisBars": n_bars,
                        "TrainBars": train_cutoff,
                        "TestBars": len(test_df),
                        "HybridRate": hybrid,
                        "MedianLag": median_lag,
                    }
                )

                validation_records.append(
                    {
                        "Instrument": instrument,
                        "ChartType": chart_name,
                        "SourceRows": source_rows,
                        "AnalysisRows": n_analysis,
                        "GeneratedRows": n_bars,
                        "AnalysisStart": start_time,
                        "AnalysisEnd": end_time,
                    }
                )

                instrument_metrics[instrument][chart_name] = {
                    "HybridRate": hybrid,
                    "MedianLag": median_lag,
                }

                # Store for timeline plot (use first instrument)
                if instrument == INSTRUMENTS[0]:
                    if timeline_time_bars is None:
                        timeline_time_bars = analysis_df
                    timeline_events[instrument][chart_name] = chart_df

                # Lag records for boxplot
                for lag in lags:
                    lag_records.append(
                        {
                            "Instrument": instrument,
                            "ChartType": chart_name,
                            "Lag": float(lag),
                        }
                    )

        except Exception as exc:
            print(f"  Warning: Failed to process {instrument}: {exc}")
            import traceback
            traceback.print_exc()
            continue

    # --- Compute improvements vs Time bars ---
    event_types = ["LineBreak3", "Renko", "HeikenAshi"]
    for event_type in event_types:
        hybrid_diffs = np.array(
            [
                instrument_metrics[inst]["Time"]["HybridRate"]
                - instrument_metrics[inst][event_type]["HybridRate"]
                for inst in INSTRUMENTS
                if inst in instrument_metrics
                and "Time" in instrument_metrics[inst]
                and event_type in instrument_metrics[inst]
            ]
        )
        lag_diffs = np.array(
            [
                instrument_metrics[inst]["Time"]["MedianLag"]
                - instrument_metrics[inst][event_type]["MedianLag"]
                for inst in INSTRUMENTS
                if inst in instrument_metrics
                and "Time" in instrument_metrics[inst]
                and event_type in instrument_metrics[inst]
                and not np.isnan(instrument_metrics[inst]["Time"]["MedianLag"])
                and not np.isnan(instrument_metrics[inst][event_type]["MedianLag"])
            ]
        )

        for inst in INSTRUMENTS:
            if (
                inst in instrument_metrics
                and "Time" in instrument_metrics[inst]
                and event_type in instrument_metrics[inst]
            ):
                base_h = instrument_metrics[inst]["Time"]["HybridRate"]
                ev_h = instrument_metrics[inst][event_type]["HybridRate"]
                base_l = instrument_metrics[inst]["Time"]["MedianLag"]
                ev_l = instrument_metrics[inst][event_type]["MedianLag"]

                h_improve = (
                    (base_h - ev_h) / base_h if base_h > 0 else np.nan
                )
                l_improve = (
                    (base_l - ev_l) / base_l
                    if base_l > 0 and not np.isnan(base_l) and not np.isnan(ev_l)
                    else np.nan
                )

                improvement_records.append(
                    {
                        "Instrument": inst,
                        "ChartType": event_type,
                        "Metric": "HybridRate",
                        "Improvement": h_improve,
                    }
                )
                improvement_records.append(
                    {
                        "Instrument": inst,
                        "ChartType": event_type,
                        "Metric": "MedianLag",
                        "Improvement": l_improve,
                    }
                )

        # Bootstrap
        if len(hybrid_diffs) > 0:
            h_mean, h_lo, h_hi = bootstrap_mean_ci(hybrid_diffs)
            bootstrap_records.append(
                {
                    "Comparison": f"{event_type} vs Time",
                    "Metric": "HybridRateReduction",
                    "MeanDiff": h_mean,
                    "CI_Lower": h_lo,
                    "CI_Upper": h_hi,
                    "CI_Excludes_Zero": (h_lo > 0) or (h_hi < 0),
                    "SignCountPositive": int(np.sum(hybrid_diffs > 0)),
                    "N_Instruments": len(hybrid_diffs),
                }
            )
        if len(lag_diffs) > 0:
            l_mean, l_lo, l_hi = bootstrap_mean_ci(lag_diffs)
            bootstrap_records.append(
                {
                    "Comparison": f"{event_type} vs Time",
                    "Metric": "LagReduction",
                    "MeanDiff": l_mean,
                    "CI_Lower": l_lo,
                    "CI_Upper": l_hi,
                    "CI_Excludes_Zero": (l_lo > 0) or (l_hi < 0),
                    "SignCountPositive": int(np.sum(lag_diffs > 0)),
                    "N_Instruments": len(lag_diffs),
                }
            )

    # --- Save machine-readable results ---
    summary_df = pd.DataFrame(summary_records)
    validation_df = pd.DataFrame(validation_records)
    lag_df = pd.DataFrame(lag_records)
    improvement_df = pd.DataFrame(improvement_records)
    bootstrap_df = pd.DataFrame(bootstrap_records)

    summary_df.to_csv(RESULTS_DIR / "summary_metrics.csv", index=False)
    validation_df.to_csv(
        RESULTS_DIR / "validation_table.csv", index=False
    )
    lag_df.to_csv(RESULTS_DIR / "lag_data.csv", index=False)
    improvement_df.to_csv(
        RESULTS_DIR / "improvement_vs_time.csv", index=False
    )
    if not bootstrap_df.empty:
        bootstrap_df.to_csv(
            RESULTS_DIR / "bootstrap_results.csv", index=False
        )

    print(f"Saved summary_metrics.csv ({len(summary_df)} rows)")
    print(f"Saved validation_table.csv ({len(validation_df)} rows)")
    print(f"Saved lag_data.csv ({len(lag_df)} rows)")
    print(f"Saved improvement_vs_time.csv ({len(improvement_df)} rows)")
    if not bootstrap_df.empty:
        print(f"Saved bootstrap_results.csv ({len(bootstrap_df)} rows)")

    # --- Produce visualisations ---
    print("Generating plots ...")
    first_inst = INSTRUMENTS[0]
    if (
        timeline_time_bars is not None
        and first_inst in timeline_events
        and timeline_events[first_inst]
    ):
        try:
            plot_regime_timeline(
                timeline_time_bars,
                timeline_events[first_inst],
                PLOTS_DIR / "regime_timeline.png",
            )
        except Exception as exc:
            print(f"  Warning: timeline plot failed: {exc}")

    if not summary_df.empty:
        plot_hybrid_rate(
            summary_df,
            PLOTS_DIR / "hybrid_rate_by_instrument_charttype.png",
        )
    if not lag_df.empty:
        plot_lag_boxplot(
            lag_df,
            PLOTS_DIR / "lag_boxplot_by_charttype.png",
        )
    if not improvement_df.empty:
        plot_improvement_heatmap(
            improvement_df,
            PLOTS_DIR / "improvement_heatmap.png",
        )

    print(f"Plots saved to {PLOTS_DIR}")
    print("EXP-002 complete.")


if __name__ == "__main__":
    main()
