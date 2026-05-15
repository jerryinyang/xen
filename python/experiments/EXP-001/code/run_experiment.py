"""
Experiment EXP-001: Information Density & Ghost Bar Comparison
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
        "ghost_fn": "timebar",
        "close_col": "Close",
    },
    "LineBreak3": {
        "generator": "linebreak",
        "params": {"level": 3},
        "time_col": "SourceCloseTime",
        "ghost_fn": "event",
        "close_col": None,
    },
    "LineBreak5": {
        "generator": "linebreak",
        "params": {"level": 5},
        "time_col": "SourceCloseTime",
        "ghost_fn": "event",
        "close_col": None,
    },
    "Renko": {
        "generator": "renko",
        "params": {"atr_period": 14},
        "time_col": "SourceCloseTime",
        "ghost_fn": "event",
        "close_col": None,
    },
    "HeikenAshi": {
        "generator": "heiken_ashi",
        "params": {},
        "time_col": "CloseTime",
        "ghost_fn": "heiken_ashi",
        "close_col": "RealClose",
    },
}

DATA_DIR = PROJECT_ROOT / "data"
PLOTS_DIR = PYTHON_ROOT / "experiments/EXP-001/plots"
RESULTS_DIR = PYTHON_ROOT / "experiments/EXP-001/results"

BOOTSTRAP_SEED = 42
N_BOOTSTRAP = 10_000
ANALYSIS_FRACTION = 0.7
TRAIN_FRACTION = 0.7
MIN_VALID_INSTRUMENTS = 3
GHOST_REDUCTION_THRESHOLD = 0.25
ENTROPY_INCREASE_THRESHOLD = 0.10
PRIMARY_EVENT_TYPES = ["LineBreak3", "Renko"]

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_analysis_timebar_data(instrument: str) -> tuple[pl.DataFrame, int]:
    """Load only the non-holdout analysis rows for an instrument.

    The full row count is read through the lazy plan to define the mandatory
    70% analysis cutoff, but only rows before that cutoff are collected.

    Parameters
    ----------
    instrument : str
        Instrument symbol (e.g. "EURUSD").

    Returns
    -------
    tuple[pl.DataFrame, int]
        Analysis-set time bars and the analysis row cutoff.
    """
    pattern = f"timebars/timebars_{instrument.lower()}_*.parquet"
    matches = sorted(DATA_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(
            f"No time-bar file found for {instrument} matching {pattern}"
        )
    scan = pl.scan_parquet(matches)
    total_rows = int(scan.select(pl.len()).collect().item())
    analysis_rows = int(total_rows * ANALYSIS_FRACTION)
    if analysis_rows <= 0:
        return pl.DataFrame(), analysis_rows
    analysis_df = scan.head(analysis_rows).collect().unique().sort("CloseTime")
    return analysis_df, analysis_rows


def train_cutoff_time(df: pl.DataFrame) -> Any:
    """Return the timestamp that ends the train segment.

    Parameters
    ----------
    df : pl.DataFrame
        Chronologically ordered analysis set.

    Returns
    -------
    Any
        Last `CloseTime` included in train, or None if empty.
    """
    n = len(df)
    if n == 0:
        return None
    cutoff_idx = max(int(n * TRAIN_FRACTION) - 1, 0)
    return df["CloseTime"][cutoff_idx]


def split_counts_by_time(
    chart_df: pl.DataFrame,
    time_col: str,
    cutoff_time: Any,
) -> tuple[int, int]:
    """Count continuous generated chart rows in train/test segments."""
    if cutoff_time is None or len(chart_df) == 0:
        return 0, len(chart_df)
    train_count = chart_df.filter(pl.col(time_col) <= cutoff_time).height
    return train_count, len(chart_df) - train_count


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
# Ghost-bar helpers
# ---------------------------------------------------------------------------
def compute_min_tick_proxy(closes: pl.Series) -> float:
    """Minimum positive absolute difference between consecutive closes.

    Parameters
    ----------
    closes : pl.Series
        Price close series.

    Returns
    -------
    float
        Minimum positive tick proxy (> 0).
    """
    diffs = closes.diff().abs().drop_nulls().to_numpy()
    pos = diffs[diffs > 0]
    if len(pos) == 0:
        return 1e-9
    val = float(pos.min())
    return val if val > 0 else 1e-9


def compute_ghost_rate_timebar(df: pl.DataFrame, min_tick: float) -> float:
    """Ghost rate for 1-minute time bars.

    A bar is ghost if its real range is below ``min_tick`` or its
    absolute close-to-close movement is below ``min_tick``.
    """
    if len(df) == 0:
        return 0.0
    range_ = df["High"] - df["Low"]
    close_diff = df["Close"].diff().abs()
    mask = (range_ < min_tick) | (close_diff < min_tick)
    mask = mask.fill_null(range_ < min_tick)
    return float(mask.mean())


def compute_ghost_rate_heiken_ashi(
    df: pl.DataFrame, min_tick: float
) -> float:
    """Ghost rate for Heiken Ashi candles (using real prices)."""
    if len(df) == 0:
        return 0.0
    range_ = df["RealHigh"] - df["RealLow"]
    close_diff = df["RealClose"].diff().abs()
    mask = (range_ < min_tick) | (close_diff < min_tick)
    mask = mask.fill_null(range_ < min_tick)
    return float(mask.mean())


def compute_ghost_rate_event(df: pl.DataFrame, min_tick: float) -> float:
    """Ghost rate for event bars using real closes aligned by timestamp.

    A bar is ghost if the absolute real-price movement from the previous
    aligned close is below ``min_tick``.
    """
    if len(df) == 0:
        return 0.0
    close_diff = df["RealClose"].diff().abs()
    mask = close_diff < min_tick
    mask = mask.fill_null(False)
    return float(mask.mean())


def compute_ghost_rate(
    df: pl.DataFrame,
    ghost_fn: str,
    min_tick: float,
) -> float:
    """Dispatch ghost-rate computation.

    Parameters
    ----------
    df : pl.DataFrame
        Chart-type bars with required price columns.
    ghost_fn : str
        Ghost-function key ("timebar", "heiken_ashi", or "event").
    min_tick : float
        Instrument-specific minimum non-zero tick proxy.

    Returns
    -------
    float
        Proportion of ghost bars.
    """
    if ghost_fn == "timebar":
        return compute_ghost_rate_timebar(df, min_tick)
    if ghost_fn == "heiken_ashi":
        return compute_ghost_rate_heiken_ashi(df, min_tick)
    if ghost_fn == "event":
        return compute_ghost_rate_event(df, min_tick)
    return 0.0


# ---------------------------------------------------------------------------
# Entropy helper
# ---------------------------------------------------------------------------
def directional_entropy(directions: pl.Series) -> float:
    """Shannon entropy (base 2) of the direction distribution.

    Parameters
    ----------
    directions : pl.Series
        Series of +1/-1 direction codes.

    Returns
    -------
    float
        Entropy in bits (0 = pure, 1 = balanced for binary).
    """
    if len(directions) == 0:
        return 0.0
    counts = directions.value_counts()
    total = counts.get_column("count").sum()
    if total == 0:
        return 0.0
    probs = (counts.get_column("count") / total).to_numpy()
    probs = probs[probs > 0]
    if len(probs) <= 1:
        return 0.0
    return float(-np.sum(probs * np.log2(probs)))


# ---------------------------------------------------------------------------
# Volatility terciles
# ---------------------------------------------------------------------------
def add_volatility_terciles(time_bars: pl.DataFrame) -> pl.DataFrame:
    """Add VolatilityTercile (1=low, 2=mid, 3=high).

    Terciles are based on a realised-volatility proxy: absolute
    close-to-close log movement computed from the analysis set only.

    Parameters
    ----------
    time_bars : pl.DataFrame
        1-minute time bars.

    Returns
    -------
    pl.DataFrame
        Time bars with an added ``VolatilityTercile`` column.
    """
    if len(time_bars) == 0:
        return time_bars.with_columns(
            pl.lit(None).cast(pl.Int8).alias("VolatilityTercile")
        )
    with_vol = time_bars.with_columns(
        (pl.col("Close").log() - pl.col("Close").shift(1).log())
        .abs()
        .fill_null(0.0)
        .alias("RealizedVolatilityProxy")
    )
    vol = with_vol["RealizedVolatilityProxy"].to_numpy()
    vol = vol[np.isfinite(vol)]
    if len(vol) == 0:
        return with_vol.with_columns(
            pl.lit(None).cast(pl.Int8).alias("VolatilityTercile")
        )
    q33, q66 = np.quantile(vol, [1 / 3, 2 / 3])
    tercile = (
        pl.when(pl.col("RealizedVolatilityProxy") <= q33)
        .then(1)
        .when(pl.col("RealizedVolatilityProxy") <= q66)
        .then(2)
        .otherwise(3)
    )
    return with_vol.with_columns(tercile.alias("VolatilityTercile"))


def attach_tercile(
    chart_df: pl.DataFrame,
    time_bars_tercile: pl.DataFrame,
    time_col: str,
) -> pl.DataFrame:
    """Attach volatility tercile from time bars to chart bars by timestamp.

    Parameters
    ----------
    chart_df : pl.DataFrame
        Chart-type bars.
    time_bars_tercile : pl.DataFrame
        Time bars containing ``CloseTime`` and ``VolatilityTercile``.
    time_col : str
        Timestamp column in ``chart_df`` to align on
        (``CloseTime`` or ``SourceCloseTime``).

    Returns
    -------
    pl.DataFrame
        Chart bars with ``VolatilityTercile`` joined.
    """
    chart_df = normalize_timestamp_columns(chart_df, [time_col])
    tercile_df = time_bars_tercile.select(
        ["CloseTime", "VolatilityTercile"]
    ).rename({"CloseTime": time_col})
    tercile_df = normalize_timestamp_columns(tercile_df, [time_col])
    return chart_df.join(tercile_df, on=time_col, how="left")


def compute_cv_by_tercile(
    movements: np.ndarray,
    terciles: np.ndarray,
) -> dict[int, float]:
    """Coefficient of variation (std / mean) by volatility tercile.

    Parameters
    ----------
    movements : np.ndarray
        Absolute real-price movements.
    terciles : np.ndarray
        Volatility tercile labels aligned to ``movements``.

    Returns
    -------
    dict[int, float]
        CV for terciles 1, 2, and 3 (NaN if insufficient data).
    """
    result: dict[int, float] = {}
    for t in [1, 2, 3]:
        vals = movements[terciles == t]
        if len(vals) < 2 or np.mean(vals) == 0:
            result[t] = np.nan
        else:
            result[t] = float(np.std(vals, ddof=1) / np.mean(vals))
    return result


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


def relative_change(numerator: float, denominator: float) -> float:
    """Return a relative change, or NaN when undefined."""
    if not np.isfinite(denominator) or denominator == 0:
        return np.nan
    return numerator / denominator


def decide_hypothesis_verdict(
    valid_instruments: int,
    threshold_df: pd.DataFrame,
    bootstrap_df: pd.DataFrame,
) -> tuple[str, str]:
    """Apply the EXP-001 success/failure criteria exactly."""
    if valid_instruments < MIN_VALID_INSTRUMENTS:
        return (
            "INCONCLUSIVE",
            f"Only {valid_instruments} valid instruments; at least "
            f"{MIN_VALID_INSTRUMENTS} are required.",
        )
    if threshold_df.empty or bootstrap_df.empty:
        return (
            "INCONCLUSIVE",
            "Threshold or bootstrap comparison outputs are empty.",
        )

    primary = threshold_df[
        threshold_df["ChartType"].isin(PRIMARY_EVENT_TYPES)
    ]
    support_candidates: list[str] = []
    refuted_by_all = True

    for chart_type in PRIMARY_EVENT_TYPES:
        chart_rows = primary[primary["ChartType"] == chart_type]
        meets_count = int(chart_rows["MeetsBothThresholds"].sum())
        ghost_ci = bootstrap_df[
            (bootstrap_df["Comparison"] == f"{chart_type} vs Time")
            & (bootstrap_df["Metric"] == "GhostRateReduction")
        ]
        entropy_ci = bootstrap_df[
            (bootstrap_df["Comparison"] == f"{chart_type} vs Time")
            & (bootstrap_df["Metric"] == "EntropyIncrease")
        ]
        ghost_ci_positive = (
            not ghost_ci.empty
            and bool(ghost_ci.iloc[0]["CI_Excludes_Zero"])
            and float(ghost_ci.iloc[0]["MeanDiff"]) > 0
        )
        entropy_ci_positive = (
            not entropy_ci.empty
            and bool(entropy_ci.iloc[0]["CI_Excludes_Zero"])
            and float(entropy_ci.iloc[0]["MeanDiff"]) > 0
        )

        if (
            meets_count >= MIN_VALID_INSTRUMENTS
            and ghost_ci_positive
            and entropy_ci_positive
        ):
            support_candidates.append(chart_type)
        if meets_count >= 2 and ghost_ci_positive and entropy_ci_positive:
            refuted_by_all = False

    if support_candidates:
        return (
            "SUPPORTED",
            "At least one primary event chart type met both thresholds on "
            f"{MIN_VALID_INSTRUMENTS}+ instruments with positive bootstrap "
            "intervals excluding zero: "
            + ", ".join(support_candidates),
        )
    if refuted_by_all:
        return (
            "REFUTED",
            "Fewer than two instruments met both thresholds for every "
            "primary event chart type, or bootstrap intervals failed to "
            "exclude zero.",
        )
    return (
        "INCONCLUSIVE",
        "Effects were present but did not satisfy the full support criteria.",
    )


# ---------------------------------------------------------------------------
# Density helper
# ---------------------------------------------------------------------------
def bars_per_day(df: pl.DataFrame, time_col: str) -> float:
    """Average bars per calendar day.

    Parameters
    ----------
    df : pl.DataFrame
        Chart-type bars.
    time_col : str
        Timestamp column.

    Returns
    -------
    float
        Bars per day (0.0 if empty).
    """
    if len(df) <= 1:
        return float(len(df))
    min_t = df[time_col].min()
    max_t = df[time_col].max()
    delta = max_t - min_t
    days = delta.total_seconds() / 86400.0
    if days <= 0:
        return float(len(df))
    return len(df) / days


# ---------------------------------------------------------------------------
# Plotting functions
# ---------------------------------------------------------------------------
def plot_ghost_rate(
    df: pd.DataFrame,
    save_path: Path,
) -> plt.Figure:
    """Grouped bar chart of ghost rate by instrument and chart type.

    Parameters
    ----------
    df : pd.DataFrame
        Summary DataFrame with ``Instrument``, ``ChartType``, ``GhostRate``.
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
        data=df, x="Instrument", y="GhostRate", hue="ChartType", ax=ax
    )
    ax.set_title("Ghost Rate by Instrument and Chart Type")
    ax.set_ylabel("Ghost Rate")
    ax.set_xlabel("Instrument")
    ax.legend(title="Chart Type", loc="upper right")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


def plot_movement_boxplot(
    df: pd.DataFrame,
    save_path: Path,
) -> plt.Figure:
    """Box plot of absolute real-price movement per bar by chart type,
    faceted by instrument.

    Parameters
    ----------
    df : pd.DataFrame
        Long-format DataFrame with ``Instrument``, ``ChartType``,
        ``Movement``.
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
        y="Movement",
        col="Instrument",
        col_wrap=2,
        height=4,
        aspect=1.2,
        sharey=False,
    )
    g.set_axis_labels("Chart Type", "Absolute Real-Price Movement")
    g.set_titles("{col_name}")
    g.fig.suptitle(
        "Absolute Real-Price Movement per Bar by Chart Type",
        y=1.02,
        fontsize=12,
    )
    g.fig.tight_layout()
    g.fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(g.fig)
    return g.fig


def plot_entropy_heatmap(
    df: pd.DataFrame,
    save_path: Path,
) -> plt.Figure:
    """Heatmap of directional entropy by instrument and chart type.

    Parameters
    ----------
    df : pd.DataFrame
        Summary DataFrame with ``Instrument``, ``ChartType``,
        ``DirectionalEntropy``.
    save_path : Path
        File path to save the figure.

    Returns
    -------
    plt.Figure
        The figure object.
    """
    sns.set_theme(style="white")
    pivot = df.pivot(
        index="Instrument",
        columns="ChartType",
        values="DirectionalEntropy",
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.heatmap(
        pivot,
        annot=True,
        fmt=".3f",
        cmap="YlOrRd",
        ax=ax,
        cbar_kws={"label": "Entropy"},
    )
    ax.set_title("Directional Entropy by Instrument and Chart Type")
    ax.set_ylabel("Instrument")
    ax.set_xlabel("Chart Type")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


def plot_bar_density_timeline(
    daily_counts: dict[str, pd.DataFrame],
    save_path: Path,
) -> plt.Figure:
    """Line chart of daily bar counts by chart type for EURUSD.

    Parameters
    ----------
    daily_counts : dict[str, pd.DataFrame]
        Mapping chart-type name to daily-count DataFrame
        (columns ``Date``, ``Count``).
    save_path : Path
        File path to save the figure.

    Returns
    -------
    plt.Figure
        The figure object.
    """
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(12, 5))
    for chart_type, counts_df in daily_counts.items():
        ax.plot(
            counts_df["Date"],
            counts_df["Count"],
            label=chart_type,
            marker="o",
            markersize=3,
            alpha=0.7,
        )
    ax.set_title("Daily Bar Count by Chart Type (EURUSD)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Bars per Day")
    ax.legend(title="Chart Type", loc="upper right")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def main() -> None:
    """Run the full EXP-001 analysis pipeline."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("EXP-001: Information Density & Ghost Bar Comparison")
    print(f"Instruments: {', '.join(INSTRUMENTS)}")
    print("Chart types: Time, LineBreak3, LineBreak5, Renko, HeikenAshi")
    print(f"Output: {PLOTS_DIR} and {RESULTS_DIR}\n")

    summary_records: list[dict[str, Any]] = []
    validation_records: list[dict[str, Any]] = []
    movement_records: list[dict[str, Any]] = []
    daily_counts_eurusd: dict[str, pd.DataFrame] = {}
    failure_records: list[dict[str, str]] = []

    instrument_ghost: dict[str, dict[str, float]] = {}
    instrument_entropy: dict[str, dict[str, float]] = {}

    for instrument in INSTRUMENTS:
        try:
            print(f"Processing {instrument} ...")
            analysis_df, analysis_cutoff = load_analysis_timebar_data(
                instrument
            )
            if len(analysis_df) == 0:
                print(f"  Skipping {instrument}: empty dataset")
                failure_records.append(
                    {"Instrument": instrument, "Reason": "empty dataset"}
                )
                continue

            train_end_time = train_cutoff_time(analysis_df)

            min_tick = compute_min_tick_proxy(analysis_df["Close"])
            analysis_df = add_volatility_terciles(analysis_df)

            timebar_closes = analysis_df.select(["CloseTime", "Close"])

            instrument_ghost[instrument] = {}
            instrument_entropy[instrument] = {}

            for chart_name, config in CHART_CONFIG.items():
                chart_df = generate_chart(analysis_df, config)

                if chart_name == "Time":
                    chart_df = chart_df.with_columns(
                        pl.when(pl.col("Close") >= pl.col("Open"))
                        .then(1)
                        .otherwise(-1)
                        .cast(pl.Int32)
                        .alias("Direction")
                    )

                if config["ghost_fn"] == "event":
                    chart_df = normalize_timestamp_columns(
                        chart_df, [config["time_col"]]
                    )
                    real_closes = timebar_closes.rename(
                        {
                            "CloseTime": config["time_col"],
                            "Close": "RealClose",
                        }
                    )
                    real_closes = normalize_timestamp_columns(
                        real_closes, [config["time_col"]]
                    )
                    chart_df = chart_df.join(
                        real_closes,
                        on=config["time_col"],
                        how="left",
                    )

                chart_df = attach_tercile(
                    chart_df, analysis_df, config["time_col"]
                )

                n_bars = len(chart_df)
                bpd = bars_per_day(chart_df, config["time_col"])
                ghost = compute_ghost_rate(
                    chart_df, config["ghost_fn"], min_tick
                )
                entropy = directional_entropy(chart_df["Direction"])

                close_col = (
                    config["close_col"]
                    if config["close_col"]
                    else "RealClose"
                )
                sorted_chart = chart_df.sort(config["time_col"])
                movements = (
                    sorted_chart[close_col]
                    .diff()
                    .abs()
                    .drop_nulls()
                    .to_numpy()
                )
                terciles = sorted_chart["VolatilityTercile"].to_numpy()[1:]

                median_movement = (
                    float(np.median(movements))
                    if len(movements) > 0
                    else np.nan
                )
                cv_by_tercile = compute_cv_by_tercile(movements, terciles)

                train_bars, test_bars = split_counts_by_time(
                    chart_df, config["time_col"], train_end_time
                )

                summary_records.append(
                    {
                        "Instrument": instrument,
                        "ChartType": chart_name,
                        "AnalysisBars": n_bars,
                        "TrainBars": train_bars,
                        "TestBars": test_bars,
                        "BarsPerDay": bpd,
                        "GhostRate": ghost,
                        "DirectionalEntropy": entropy,
                        "MedianAbsMovement": median_movement,
                        "CV_Tercile1": cv_by_tercile.get(1, np.nan),
                        "CV_Tercile2": cv_by_tercile.get(2, np.nan),
                        "CV_Tercile3": cv_by_tercile.get(3, np.nan),
                    }
                )

                instrument_ghost[instrument][chart_name] = ghost
                instrument_entropy[instrument][chart_name] = entropy

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
                validation_records.append(
                    {
                        "Instrument": instrument,
                        "ChartType": chart_name,
                        "AnalysisRows": len(analysis_df),
                        "AnalysisRowCutoff": analysis_cutoff,
                        "GeneratedRows": n_bars,
                        "AnalysisStart": start_time,
                        "AnalysisEnd": end_time,
                    }
                )

                # Sample movements for boxplot to keep memory bounded
                sampled = movements
                if len(sampled) > 50000:
                    rng = np.random.default_rng(42)
                    idx = rng.choice(
                        len(sampled), size=50000, replace=False
                    )
                    sampled = sampled[idx]
                for m in sampled:
                    movement_records.append(
                        {
                            "Instrument": instrument,
                            "ChartType": chart_name,
                            "Movement": float(m),
                        }
                    )

                if instrument == "EURUSD":
                    daily = (
                        chart_df.with_columns(
                            pl.col(config["time_col"])
                            .dt.date()
                            .alias("Date")
                        )
                        .group_by("Date")
                        .agg(
                            pl.col("Date")
                            .count()
                            .alias("Count")
                        )
                        .sort("Date")
                        .to_pandas()
                    )
                    daily_counts_eurusd[chart_name] = daily

        except Exception as exc:
            print(f"  Warning: Failed to process {instrument}: {exc}")
            failure_records.append(
                {"Instrument": instrument, "Reason": str(exc)}
            )
            continue

    # --- Bootstrap comparisons (event types vs Time) ---
    bootstrap_records: list[dict[str, Any]] = []
    threshold_records: list[dict[str, Any]] = []
    event_types = ["LineBreak3", "LineBreak5", "Renko"]
    for event_type in event_types:
        ghost_diffs = np.array(
            [
                instrument_ghost[inst]["Time"]
                - instrument_ghost[inst][event_type]
                for inst in INSTRUMENTS
                if inst in instrument_ghost
                and "Time" in instrument_ghost[inst]
                and event_type in instrument_ghost[inst]
            ]
        )
        entropy_diffs = np.array(
            [
                instrument_entropy[inst][event_type]
                - instrument_entropy[inst]["Time"]
                for inst in INSTRUMENTS
                if inst in instrument_entropy
                and "Time" in instrument_entropy[inst]
                and event_type in instrument_entropy[inst]
            ]
        )

        if len(ghost_diffs) > 0:
            g_mean, g_lo, g_hi = bootstrap_mean_ci(ghost_diffs)
            bootstrap_records.append(
                {
                    "Comparison": f"{event_type} vs Time",
                    "Metric": "GhostRateReduction",
                    "MeanDiff": g_mean,
                    "CI_Lower": g_lo,
                    "CI_Upper": g_hi,
                    "CI_Excludes_Zero": (g_lo > 0) or (g_hi < 0),
                    "SignCountPositive": int(np.sum(ghost_diffs > 0)),
                    "N_Instruments": len(ghost_diffs),
                }
            )

        if len(entropy_diffs) > 0:
            e_mean, e_lo, e_hi = bootstrap_mean_ci(entropy_diffs)
            bootstrap_records.append(
                {
                    "Comparison": f"{event_type} vs Time",
                    "Metric": "EntropyIncrease",
                    "MeanDiff": e_mean,
                    "CI_Lower": e_lo,
                    "CI_Upper": e_hi,
                    "CI_Excludes_Zero": (e_lo > 0) or (e_hi < 0),
                    "SignCountPositive": int(
                        np.sum(entropy_diffs > 0)
                    ),
                    "N_Instruments": len(entropy_diffs),
                }
            )

        for inst in INSTRUMENTS:
            if (
                inst not in instrument_ghost
                or "Time" not in instrument_ghost[inst]
                or event_type not in instrument_ghost[inst]
                or inst not in instrument_entropy
                or "Time" not in instrument_entropy[inst]
                or event_type not in instrument_entropy[inst]
            ):
                continue
            time_ghost = instrument_ghost[inst]["Time"]
            event_ghost = instrument_ghost[inst][event_type]
            time_entropy = instrument_entropy[inst]["Time"]
            event_entropy = instrument_entropy[inst][event_type]
            ghost_reduction = relative_change(
                time_ghost - event_ghost, time_ghost
            )
            entropy_increase = relative_change(
                event_entropy - time_entropy, time_entropy
            )
            meets_ghost = (
                np.isfinite(ghost_reduction)
                and ghost_reduction >= GHOST_REDUCTION_THRESHOLD
            )
            meets_entropy = (
                np.isfinite(entropy_increase)
                and entropy_increase >= ENTROPY_INCREASE_THRESHOLD
            )
            threshold_records.append(
                {
                    "Instrument": inst,
                    "ChartType": event_type,
                    "GhostReductionRelative": ghost_reduction,
                    "EntropyIncreaseRelative": entropy_increase,
                    "MeetsGhostThreshold": meets_ghost,
                    "MeetsEntropyThreshold": meets_entropy,
                    "MeetsBothThresholds": meets_ghost and meets_entropy,
                    "PrimaryForVerdict": event_type in PRIMARY_EVENT_TYPES,
                }
            )

    # --- Save machine-readable results ---
    summary_df = pd.DataFrame(summary_records)
    validation_df = pd.DataFrame(validation_records)
    bootstrap_df = pd.DataFrame(bootstrap_records)
    threshold_df = pd.DataFrame(threshold_records)
    failures_df = pd.DataFrame(failure_records)
    movement_df = pd.DataFrame(movement_records)
    valid_instruments = len(instrument_ghost)
    verdict, verdict_reason = decide_hypothesis_verdict(
        valid_instruments, threshold_df, bootstrap_df
    )
    verdict_df = pd.DataFrame(
        [
            {
                "Verdict": verdict,
                "Reason": verdict_reason,
                "ValidInstruments": valid_instruments,
                "MinimumValidInstruments": MIN_VALID_INSTRUMENTS,
            }
        ]
    )

    summary_df.to_csv(RESULTS_DIR / "summary_metrics.csv", index=False)
    validation_df.to_csv(
        RESULTS_DIR / "validation_table.csv", index=False
    )
    bootstrap_df.to_csv(
        RESULTS_DIR / "bootstrap_results.csv", index=False
    )
    threshold_df.to_csv(
        RESULTS_DIR / "threshold_evaluation.csv", index=False
    )
    verdict_df.to_csv(RESULTS_DIR / "hypothesis_verdict.csv", index=False)
    failures_df.to_csv(
        RESULTS_DIR / "instrument_failures.csv", index=False
    )

    print(f"Saved summary_metrics.csv ({len(summary_df)} rows)")
    print(f"Saved validation_table.csv ({len(validation_df)} rows)")
    print(f"Saved bootstrap_results.csv ({len(bootstrap_df)} rows)")
    print(
        f"Saved threshold_evaluation.csv ({len(threshold_df)} rows)"
    )
    print(f"Saved hypothesis_verdict.csv: {verdict}")
    if not failures_df.empty:
        print(f"Saved instrument_failures.csv ({len(failures_df)} rows)")

    # --- Produce visualisations ---
    print("Generating plots ...")
    if not summary_df.empty:
        plot_ghost_rate(
            summary_df,
            PLOTS_DIR / "ghost_rate_by_instrument_charttype.png",
        )
    if not movement_df.empty:
        plot_movement_boxplot(
            movement_df,
            PLOTS_DIR / "movement_boxplot_by_charttype.png",
        )
    if not summary_df.empty:
        plot_entropy_heatmap(
            summary_df, PLOTS_DIR / "entropy_heatmap.png"
        )
    if daily_counts_eurusd:
        plot_bar_density_timeline(
            daily_counts_eurusd,
            PLOTS_DIR / "bar_density_timeline_eurusd.png",
        )

    print(f"Plots saved to {PLOTS_DIR}")
    print(f"EXP-001 complete with verdict: {verdict}")


if __name__ == "__main__":
    main()
