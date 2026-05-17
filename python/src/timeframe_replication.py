from __future__ import annotations

import hashlib
import json
import logging
import platform
import subprocess
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Any, Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl
import seaborn as sns

from heiken_ashi_generator import generate_heiken_ashi
from linebreak_generator import generate_linebreak
from renko_generator import generate_renko


LOGGER = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON_ROOT = PROJECT_ROOT / "python"
DATA_DIR = PROJECT_ROOT / "data"

INSTRUMENTS = ["EURUSD", "XAUUSD", "BTCUSD", "USTEC"]
TIMEFRAMES = {"15m": 15, "1h": 60}
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
BOOTSTRAP_SEED = 42
BOOTSTRAP_N = 1000
ROLLING_VOL_WINDOW = 20
ATR_PERIOD = 14
PLOT_SAMPLE_N = 20_000
TIMESTAMP_TIME_UNIT = "us"
TIMESTAMP_COLUMNS = (
    "OpenTime",
    "CloseTime",
    "SourceCloseTime",
    "Timestamp",
    "TransitionTime",
    "ReversalTime",
    "SignalTime",
)


@dataclass(frozen=True)
class LoadedTimeframe:
    instrument: str
    timeframe: str
    source_rows: int
    analysis_rows: int
    aggregated_rows: int
    dropped_rows: int
    start_time: Any
    end_time: Any
    path: Path
    bars: pl.DataFrame


def normalize_datetime_units(
    df: pl.DataFrame,
    columns: tuple[str, ...] = TIMESTAMP_COLUMNS,
) -> pl.DataFrame:
    """Cast timestamp columns to one Polars datetime unit before alignment."""
    present = [column for column in columns if column in df.columns]
    if not present:
        return df
    return df.with_columns([
        pl.col(column).cast(pl.Datetime(TIMESTAMP_TIME_UNIT)).alias(column)
        for column in present
    ])


def experiment_dirs(exp_id: str) -> tuple[Path, Path]:
    """Return and create the results and plots directories for an experiment."""
    exp_dir = PYTHON_ROOT / "experiments" / exp_id
    results_dir = exp_dir / "results"
    plots_dir = exp_dir / "plots"
    results_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)
    return results_dir, plots_dir


def find_timebar_path(instrument: str) -> Path:
    """Return the latest time-bar Parquet path for one instrument."""
    paths = sorted(DATA_DIR.glob(f"timebars/timebars_{instrument.lower()}_*.parquet"))
    if not paths:
        raise FileNotFoundError(f"No time-bar Parquet file found for {instrument}")
    return paths[-1]


def load_source_analysis(instrument: str) -> tuple[pl.DataFrame, int, int, Path]:
    """Load only the first 70 percent chronological source rows for an instrument."""
    path = find_timebar_path(instrument)
    scan = (
        pl.scan_parquet(path)
        .select(TIMEBAR_COLUMNS)
        .sort("CloseTime")
    )
    source_rows = int(scan.select(pl.len()).collect().item())
    analysis_rows = int(source_rows * ANALYSIS_FRACTION)
    source_analysis = normalize_datetime_units(scan.slice(0, analysis_rows).collect())
    return source_analysis, source_rows, analysis_rows, path


def aggregate_timeframe(
    source_analysis: pl.DataFrame,
    instrument: str,
    timeframe: str,
    minutes: int,
) -> tuple[pl.DataFrame, int]:
    """Aggregate holdout-excluded 1-minute bars into complete OHLCV bars."""
    source_analysis = normalize_datetime_units(source_analysis)
    if source_analysis.is_empty():
        return normalize_datetime_units(pl.DataFrame(schema={column: pl.Null for column in TIMEBAR_COLUMNS})), 0

    bucketed = source_analysis.with_columns(
        (
            (pl.col("CloseTime") - pl.duration(microseconds=1))
            .dt.truncate(f"{minutes}m")
            + pl.duration(minutes=minutes)
        ).alias("_bucket")
    )
    grouped = (
        bucketed.group_by("_bucket", maintain_order=True)
        .agg(
            pl.first("Symbol").alias("Symbol"),
            pl.first("OpenTime").alias("OpenTime"),
            pl.max("CloseTime").alias("CloseTime"),
            pl.first("Open").alias("Open"),
            pl.max("High").alias("High"),
            pl.min("Low").alias("Low"),
            pl.last("Close").alias("Close"),
            pl.sum("TickVolume").alias("TickVolume"),
            pl.len().alias("_source_count"),
        )
        .sort("CloseTime")
    )
    complete = normalize_datetime_units(
        grouped.filter(pl.col("_source_count") == minutes).select(TIMEBAR_COLUMNS)
    )
    dropped_rows = int(grouped.select((pl.sum("_source_count") - complete.height * minutes)).item())
    if not complete.is_empty():
        complete = complete.with_columns(pl.lit(instrument).alias("Symbol"))
    LOGGER.info(
        "%s %s: %d aggregated rows, %d source rows dropped from incomplete buckets",
        instrument,
        timeframe,
        complete.height,
        dropped_rows,
    )
    return complete, dropped_rows


def load_timeframes() -> tuple[dict[tuple[str, str], LoadedTimeframe], pd.DataFrame]:
    """Load and aggregate all scoped instruments and higher timeframes."""
    loaded: dict[tuple[str, str], LoadedTimeframe] = {}
    validation: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        source_analysis, source_rows, analysis_rows, path = load_source_analysis(instrument)
        for timeframe, minutes in TIMEFRAMES.items():
            bars, dropped_rows = aggregate_timeframe(
                source_analysis, instrument, timeframe, minutes
            )
            start_time = bars["CloseTime"][0] if bars.height else None
            end_time = bars["CloseTime"][-1] if bars.height else None
            loaded[(instrument, timeframe)] = LoadedTimeframe(
                instrument=instrument,
                timeframe=timeframe,
                source_rows=source_rows,
                analysis_rows=analysis_rows,
                aggregated_rows=bars.height,
                dropped_rows=dropped_rows,
                start_time=start_time,
                end_time=end_time,
                path=path,
                bars=bars,
            )
            validation.append(
                {
                    "Instrument": instrument,
                    "Timeframe": timeframe,
                    "InputFile": str(path.relative_to(PROJECT_ROOT)),
                    "SourceRows": source_rows,
                    "AnalysisRows": analysis_rows,
                    "AggregatedRows": bars.height,
                    "DroppedSourceRowsInIncompleteBuckets": dropped_rows,
                    "StartTime": start_time,
                    "EndTime": end_time,
                }
            )
    return loaded, pd.DataFrame(validation)


def generate_chart(time_bars: pl.DataFrame, chart_type: str) -> pl.DataFrame:
    """Generate one chart type from completed source time bars."""
    time_bars = normalize_datetime_units(time_bars)
    if chart_type == "Time":
        return time_bars.clone()
    if chart_type == "LineBreak":
        return normalize_datetime_units(generate_linebreak(time_bars, level=3))
    if chart_type == "LineBreak3":
        return normalize_datetime_units(generate_linebreak(time_bars, level=3))
    if chart_type == "LineBreak5":
        return normalize_datetime_units(generate_linebreak(time_bars, level=5))
    if chart_type == "Renko":
        return normalize_datetime_units(generate_renko(time_bars, atr_period=14))
    if chart_type == "HeikenAshi":
        return normalize_datetime_units(generate_heiken_ashi(time_bars))
    raise ValueError(f"Unknown chart type: {chart_type}")


def chart_time_col(chart_type: str) -> str:
    """Return the timestamp column used for temporal alignment."""
    return "SourceCloseTime" if chart_type in {"LineBreak", "LineBreak3", "LineBreak5", "Renko"} else "CloseTime"


def direction_array(chart_df: pl.DataFrame, chart_type: str) -> np.ndarray:
    """Extract comparable +1/-1 direction labels."""
    if chart_df.is_empty():
        return np.array([], dtype=int)
    if chart_type == "Time":
        return np.where(chart_df["Close"].to_numpy() >= chart_df["Open"].to_numpy(), 1, -1)
    return chart_df["Direction"].to_numpy()


def real_close_series(chart_df: pl.DataFrame, time_bars: pl.DataFrame, chart_type: str) -> np.ndarray:
    """Return real-price closes aligned to the chart event timestamps."""
    if chart_df.is_empty():
        return np.array([], dtype=float)
    if chart_type == "Time":
        return chart_df["Close"].to_numpy()
    if chart_type == "HeikenAshi":
        return chart_df["RealClose"].to_numpy()
    chart_df = normalize_datetime_units(chart_df, (chart_time_col(chart_type),))
    time_bars = normalize_datetime_units(time_bars, ("CloseTime",))
    joined = chart_df.join(
        time_bars.select([pl.col("CloseTime").alias("_event_time"), pl.col("Close").alias("RealClose")]),
        left_on=chart_time_col(chart_type),
        right_on="_event_time",
        how="left",
    )
    return joined["RealClose"].drop_nulls().to_numpy()


def distinct_source_events(chart_df: pl.DataFrame, chart_type: str) -> pl.DataFrame:
    """Collapse repeated event-chart rows at the same source timestamp."""
    time_col = chart_time_col(chart_type)
    if chart_df.is_empty() or time_col not in chart_df.columns:
        return chart_df
    chart_df = normalize_datetime_units(chart_df, (time_col,))
    return chart_df.group_by(time_col, maintain_order=True).agg(pl.all().last()).sort(time_col)


def safe_div(numerator: float, denominator: float) -> float:
    """Finite division helper that returns NaN for zero or non-finite baselines."""
    if denominator == 0 or not np.isfinite(denominator):
        return float("nan")
    return float(numerator / denominator)


def directional_entropy(directions: np.ndarray) -> float:
    """Binary Shannon entropy in bits for +1/-1 direction labels."""
    if len(directions) == 0:
        return float("nan")
    up = float(np.mean(directions > 0))
    if up <= 0.0 or up >= 1.0:
        return 0.0
    return float(-(up * np.log2(up) + (1.0 - up) * np.log2(1.0 - up)))


def min_tick_proxy(closes: np.ndarray) -> float:
    """Smallest positive close-to-close movement used as a ghost threshold."""
    diffs = np.abs(np.diff(closes))
    positive = diffs[diffs > 0]
    if len(positive) == 0:
        return 1e-12
    return float(np.min(positive))


def bootstrap_mean_ci(values: np.ndarray, seed: int = BOOTSTRAP_SEED) -> dict[str, float]:
    """Descriptive bootstrap mean and percentile interval."""
    clean = values[np.isfinite(values)]
    if len(clean) == 0:
        return {"Mean": float("nan"), "CILower": float("nan"), "CIUpper": float("nan"), "N": 0}
    rng = np.random.default_rng(seed)
    draws = rng.choice(clean, size=(BOOTSTRAP_N, len(clean)), replace=True).mean(axis=1)
    return {
        "Mean": float(np.mean(clean)),
        "CILower": float(np.quantile(draws, 0.025)),
        "CIUpper": float(np.quantile(draws, 0.975)),
        "N": int(len(clean)),
    }


def realised_volatility(returns: np.ndarray) -> float:
    """Sample standard deviation of returns."""
    clean = returns[np.isfinite(returns)]
    if len(clean) < 2:
        return float("nan")
    return float(np.std(clean, ddof=1))


def log_returns(closes: np.ndarray) -> np.ndarray:
    """Compute finite close-to-close log returns."""
    closes = closes[np.isfinite(closes)]
    if len(closes) < 2:
        return np.array([], dtype=float)
    return np.diff(np.log(closes))


def add_timebar_regimes(time_bars: pl.DataFrame, window: int = ROLLING_VOL_WINDOW) -> pl.DataFrame:
    """Add train-calibrated low/medium/high realised-volatility regimes."""
    time_bars = normalize_datetime_units(time_bars)
    if time_bars.height < window + 5:
        return time_bars.with_columns(
            pl.lit(None).alias("RollingVol"),
            pl.lit(None).alias("Regime"),
        )
    df = time_bars.with_columns(
        (pl.col("Close").log() - pl.col("Close").log().shift(1)).alias("_ret")
    ).with_columns(
        pl.col("_ret").rolling_std(window_size=window, min_periods=window).alias("RollingVol")
    )
    train_rows = max(window, int(df.height * TRAIN_FRACTION))
    train_vol = df.slice(0, train_rows).filter(pl.col("RollingVol").is_not_null())["RollingVol"]
    if train_vol.len() < 3:
        return df.with_columns(pl.lit(None).alias("Regime")).drop("_ret")
    q1 = float(train_vol.quantile(1.0 / 3.0))
    q2 = float(train_vol.quantile(2.0 / 3.0))
    eval_start = df["CloseTime"][train_rows - 1]
    return (
        df.with_columns(
            pl.when(pl.col("RollingVol").is_null())
            .then(None)
            .when(pl.col("CloseTime") <= pl.lit(eval_start))
            .then(None)
            .when(pl.col("RollingVol") <= q1)
            .then(pl.lit("Low"))
            .when(pl.col("RollingVol") <= q2)
            .then(pl.lit("Medium"))
            .otherwise(pl.lit("High"))
            .alias("Regime")
        )
        .drop("_ret")
    )


def timestamp_direction_table(
    chart_df: pl.DataFrame,
    chart_type: str,
    regime_table: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """Build a timestamp/direction table for pairwise alignment."""
    if chart_df.is_empty():
        return pl.DataFrame(
            schema={
                "Timestamp": pl.Datetime(TIMESTAMP_TIME_UNIT),
                "Direction": pl.Int32,
                "Regime": pl.String,
            }
        )
    source = distinct_source_events(chart_df, chart_type)
    if chart_type == "Time":
        table = source.select(
            pl.col("CloseTime").alias("Timestamp"),
            pl.when(pl.col("Close") >= pl.col("Open")).then(1).otherwise(-1).alias("Direction"),
        )
    elif chart_type == "HeikenAshi":
        table = source.select(pl.col("CloseTime").alias("Timestamp"), "Direction")
    else:
        table = source.select(pl.col("SourceCloseTime").alias("Timestamp"), "Direction")
    table = normalize_datetime_units(table, ("Timestamp",))
    if regime_table is None:
        return table.with_columns(pl.lit(None).alias("Regime"))
    regime_lookup = normalize_datetime_units(
        regime_table.select([pl.col("CloseTime").alias("Timestamp"), "Regime"]),
        ("Timestamp",),
    )
    return table.join(
        regime_lookup,
        on="Timestamp",
        how="left",
    )


def file_sha256(path: Path) -> str:
    """Return a file SHA-256 digest."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit() -> str | None:
    """Return the current git commit when available."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    return result.stdout.strip()


def package_versions() -> dict[str, str]:
    """Return versions for packages used by the timeframe scripts."""
    versions: dict[str, str] = {}
    for name in ["numpy", "pandas", "polars", "matplotlib", "seaborn"]:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = "not-installed"
    return versions


def write_manifest(
    exp_id: str,
    results_dir: Path,
    validation_df: pd.DataFrame,
    extra: dict[str, Any] | None = None,
) -> None:
    """Write reproducibility metadata for a TF experiment."""
    files = sorted({PROJECT_ROOT / str(path) for path in validation_df["InputFile"].unique()})
    manifest = {
        "experiment": exp_id,
        "analysis_fraction": ANALYSIS_FRACTION,
        "timeframes": TIMEFRAMES,
        "instruments": INSTRUMENTS,
        "python": platform.python_version(),
        "packages": package_versions(),
        "git_commit": git_commit(),
        "input_files": [
            {
                "path": str(path.relative_to(PROJECT_ROOT)),
                "size_bytes": path.stat().st_size,
                "sha256": file_sha256(path),
            }
            for path in files
            if path.exists()
        ],
        "source_files": [
            str((PYTHON_ROOT / "src/timeframe_replication.py").relative_to(PROJECT_ROOT)),
            str((PYTHON_ROOT / "src/linebreak_generator.py").relative_to(PROJECT_ROOT)),
            str((PYTHON_ROOT / "src/renko_generator.py").relative_to(PROJECT_ROOT)),
            str((PYTHON_ROOT / "src/heiken_ashi_generator.py").relative_to(PROJECT_ROOT)),
        ],
    }
    if extra:
        manifest.update(extra)
    (results_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str, sort_keys=True) + "\n"
    )


def save_csv(df: pd.DataFrame, path: Path) -> None:
    """Save a DataFrame to CSV with stable empty-file behavior."""
    df.to_csv(path, index=False)


def simple_bar_plot(df: pd.DataFrame, x: str, y: str, hue: str, path: Path, title: str) -> None:
    """Write a bounded grouped bar plot."""
    if df.empty:
        return
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=df, x=x, y=y, hue=hue, ax=ax)
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def simple_heatmap(
    df: pd.DataFrame,
    index: str,
    columns: str,
    values: str,
    path: Path,
    title: str,
) -> None:
    """Write a pivoted heatmap when data is available."""
    if df.empty:
        return
    pivot = df.pivot_table(index=index, columns=columns, values=values, aggfunc="mean")
    if pivot.empty:
        return
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.heatmap(pivot, annot=True, fmt=".3f", cmap="viridis", ax=ax)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def run_exp001_tf(exp_id: str) -> None:
    """Run EXP-001-TF information-density replication."""
    results_dir, plots_dir = experiment_dirs(exp_id)
    loaded, validation_df = load_timeframes()
    summary: list[dict[str, Any]] = []
    sensitivity: list[dict[str, Any]] = []
    movement_samples: list[pd.DataFrame] = []

    chart_types = ["Time", "LineBreak3", "LineBreak5", "Renko", "HeikenAshi"]
    for loaded_tf in loaded.values():
        time_bars = loaded_tf.bars
        if time_bars.is_empty():
            continue
        base_closes = time_bars["Close"].to_numpy()
        tick = min_tick_proxy(base_closes)
        elapsed_days = max(
            (pd.Timestamp(loaded_tf.end_time) - pd.Timestamp(loaded_tf.start_time)).total_seconds() / 86400.0,
            1e-9,
        )
        for chart_type in chart_types:
            chart = generate_chart(time_bars, chart_type)
            verdict_chart = distinct_source_events(chart, chart_type)
            dirs = direction_array(verdict_chart, chart_type)
            closes = real_close_series(verdict_chart, time_bars, chart_type)
            moves = np.abs(np.diff(closes)) if len(closes) > 1 else np.array([])
            ghost_rate = float(np.mean(moves <= tick)) if len(moves) else float("nan")
            entropy = directional_entropy(dirs)
            summary.append(
                {
                    "Instrument": loaded_tf.instrument,
                    "Timeframe": loaded_tf.timeframe,
                    "ChartType": chart_type,
                    "Rows": chart.height,
                    "DistinctSourceRows": verdict_chart.height,
                    "BarsPerElapsedDay": chart.height / elapsed_days,
                    "GhostRate": ghost_rate,
                    "DirectionalEntropy": entropy,
                    "MedianAbsRealMove": float(np.median(moves)) if len(moves) else float("nan"),
                    "MinTickProxy": tick,
                }
            )
            if chart_type in {"LineBreak3", "LineBreak5", "Renko"}:
                sensitivity.append(
                    {
                        "Instrument": loaded_tf.instrument,
                        "Timeframe": loaded_tf.timeframe,
                        "ChartType": chart_type,
                        "RawRows": chart.height,
                        "DistinctSourceRows": verdict_chart.height,
                        "DuplicateSourceRows": chart.height - verdict_chart.height,
                        "DuplicateSourceShare": safe_div(chart.height - verdict_chart.height, chart.height),
                    }
                )
            if len(moves):
                sample = moves[:PLOT_SAMPLE_N]
                movement_samples.append(
                    pd.DataFrame(
                        {
                            "Instrument": loaded_tf.instrument,
                            "Timeframe": loaded_tf.timeframe,
                            "ChartType": chart_type,
                            "AbsRealMove": sample,
                        }
                    )
                )

    summary_df = pd.DataFrame(summary)
    sensitivity_df = pd.DataFrame(sensitivity)
    threshold_rows: list[dict[str, Any]] = []
    boot_rows: list[dict[str, Any]] = []
    for timeframe in TIMEFRAMES:
        for chart_type in ["LineBreak3", "Renko"]:
            diffs_ghost: list[float] = []
            diffs_entropy: list[float] = []
            for instrument in INSTRUMENTS:
                base = summary_df.query(
                    "Instrument == @instrument and Timeframe == @timeframe and ChartType == 'Time'"
                )
                event = summary_df.query(
                    "Instrument == @instrument and Timeframe == @timeframe and ChartType == @chart_type"
                )
                if base.empty or event.empty:
                    continue
                b = base.iloc[0]
                e = event.iloc[0]
                ghost_reduction = safe_div(b.GhostRate - e.GhostRate, b.GhostRate)
                entropy_gain = e.DirectionalEntropy - b.DirectionalEntropy
                headroom_capture = safe_div(entropy_gain, 1.0 - b.DirectionalEntropy)
                meets = (
                    ghost_reduction >= 0.25
                    and headroom_capture >= 0.50
                    and entropy_gain >= 0.005
                )
                threshold_rows.append(
                    {
                        "Instrument": instrument,
                        "Timeframe": timeframe,
                        "ChartType": chart_type,
                        "GhostReduction": ghost_reduction,
                        "EntropyGain": entropy_gain,
                        "HeadroomCapture": headroom_capture,
                        "MeetsThreshold": bool(meets),
                    }
                )
                diffs_ghost.append(ghost_reduction)
                diffs_entropy.append(entropy_gain)
            for metric, values in {
                "GhostReduction": np.asarray(diffs_ghost, dtype=float),
                "EntropyGain": np.asarray(diffs_entropy, dtype=float),
            }.items():
                ci = bootstrap_mean_ci(values)
                boot_rows.append({"Timeframe": timeframe, "ChartType": chart_type, "Metric": metric, **ci})

    threshold_df = pd.DataFrame(threshold_rows)
    verdict_rows = []
    for timeframe in TIMEFRAMES:
        for chart_type in ["LineBreak3", "Renko"]:
            subset = threshold_df.query("Timeframe == @timeframe and ChartType == @chart_type")
            support_count = int(subset["MeetsThreshold"].sum()) if not subset.empty else 0
            verdict_rows.append(
                {
                    "Timeframe": timeframe,
                    "ChartType": chart_type,
                    "SupportCount": support_count,
                    "Verdict": "SUPPORTED" if support_count >= 3 else "REFUTED",
                }
            )
    verdict_df = pd.DataFrame(verdict_rows)

    save_csv(summary_df, results_dir / "summary_metrics.csv")
    save_csv(validation_df, results_dir / "validation_table.csv")
    save_csv(sensitivity_df, results_dir / "distinct_source_sensitivity.csv")
    save_csv(threshold_df, results_dir / "threshold_evaluation.csv")
    save_csv(pd.DataFrame(boot_rows), results_dir / "bootstrap_results.csv")
    save_csv(verdict_df, results_dir / "hypothesis_verdict.csv")
    write_manifest(exp_id, results_dir, validation_df)

    simple_bar_plot(summary_df, "Instrument", "GhostRate", "ChartType", plots_dir / "ghost_rate_by_instrument_charttype.png", "Ghost Rate by Instrument and Chart Type")
    simple_heatmap(summary_df, "Instrument", "ChartType", "DirectionalEntropy", plots_dir / "entropy_heatmap.png", "Directional Entropy")
    if movement_samples:
        movement_df = pd.concat(movement_samples, ignore_index=True)
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.boxplot(data=movement_df, x="ChartType", y="AbsRealMove", hue="Timeframe", showfliers=False, ax=ax)
        ax.set_title("Absolute Real-Price Movement per Bar")
        ax.tick_params(axis="x", rotation=35)
        fig.tight_layout()
        fig.savefig(plots_dir / "movement_boxplot_by_charttype.png", dpi=150, bbox_inches="tight")
        plt.close(fig)
    density = summary_df[summary_df["Instrument"] == "EURUSD"]
    simple_bar_plot(density, "ChartType", "BarsPerElapsedDay", "Timeframe", plots_dir / "bar_density_timeline_eurusd.png", "EURUSD Bar Density")


def transition_table(regime_df: pl.DataFrame) -> pl.DataFrame:
    """Return timestamped regime transitions from a regime-labelled table."""
    regime_df = normalize_datetime_units(regime_df, ("CloseTime",))
    valid = regime_df.filter(pl.col("Regime").is_not_null()).select(["CloseTime", "Regime"])
    if valid.height < 2:
        return pl.DataFrame(
            schema={
                "TransitionTime": pl.Datetime(TIMESTAMP_TIME_UNIT),
                "NewRegime": pl.String,
            }
        )
    trans = valid.with_columns(pl.col("Regime").shift(1).alias("_prev")).filter(
        pl.col("_prev").is_not_null() & (pl.col("Regime") != pl.col("_prev"))
    )
    return normalize_datetime_units(
        trans.select(pl.col("CloseTime").alias("TransitionTime"), pl.col("Regime").alias("NewRegime")),
        ("TransitionTime",),
    )


def event_hybrid_rate(events: pl.DataFrame, chart_type: str, regime_df: pl.DataFrame) -> tuple[float, int, int]:
    """Measure event intervals that straddle more than one time-bar regime."""
    regime_df = normalize_datetime_units(regime_df, ("CloseTime",))
    if chart_type in {"Time", "HeikenAshi"}:
        valid = regime_df.filter(pl.col("Regime").is_not_null()).height
        return 0.0, valid, 0
    table = timestamp_direction_table(events, chart_type, regime_df).filter(pl.col("Regime").is_not_null())
    if table.height < 2:
        return float("nan"), 0, 0
    times = table["Timestamp"].to_list()
    hybrid = 0
    denom = 0
    regimes = regime_df.filter(pl.col("Regime").is_not_null()).select(["CloseTime", "Regime"])
    for prior, current in zip(times[:-1], times[1:]):
        segment = regimes.filter((pl.col("CloseTime") > prior) & (pl.col("CloseTime") <= current))
        if segment.is_empty():
            continue
        denom += 1
        if segment["Regime"].n_unique() > 1:
            hybrid += 1
    return safe_div(hybrid, denom), denom, hybrid


def transition_lags(events: pl.DataFrame, chart_type: str, regime_df: pl.DataFrame, minutes: int) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Measure first event confirmation lag after each regime transition."""
    transitions = transition_table(regime_df)
    if transitions.is_empty():
        return pd.DataFrame(), {"TransitionCount": 0, "MatchedTransitions": 0, "MissedTransitions": 0}
    event_table = timestamp_direction_table(events, chart_type, regime_df).filter(pl.col("Regime").is_not_null())
    lag_rows: list[dict[str, Any]] = []
    for row in transitions.iter_rows(named=True):
        t = row["TransitionTime"]
        regime = row["NewRegime"]
        match = event_table.filter((pl.col("Timestamp") >= t) & (pl.col("Regime") == regime)).head(1)
        if match.is_empty():
            lag_rows.append({"TransitionTime": t, "LagBars": np.nan, "LagMinutes": np.nan, "Matched": False})
            continue
        matched_time = match["Timestamp"][0]
        lag_minutes = (pd.Timestamp(matched_time) - pd.Timestamp(t)).total_seconds() / 60.0
        lag_rows.append(
            {
                "TransitionTime": t,
                "MatchedTime": matched_time,
                "LagBars": lag_minutes / minutes,
                "LagMinutes": lag_minutes,
                "Matched": True,
            }
        )
    lag_df = pd.DataFrame(lag_rows)
    matched = lag_df[lag_df["Matched"]]
    summary = {
        "TransitionCount": len(lag_df),
        "MatchedTransitions": int(matched.shape[0]),
        "MissedTransitions": int((~lag_df["Matched"]).sum()),
        "MedianLagBars": float(matched["LagBars"].median()) if not matched.empty else float("nan"),
        "P95LagBars": float(matched["LagBars"].quantile(0.95)) if not matched.empty else float("nan"),
        "MaxLagBars": float(matched["LagBars"].max()) if not matched.empty else float("nan"),
        "MedianLagMinutes": float(matched["LagMinutes"].median()) if not matched.empty else float("nan"),
    }
    return lag_df, summary


def run_exp002_tf(exp_id: str) -> None:
    """Run EXP-002-TF volatility-regime boundary-cost replication."""
    results_dir, plots_dir = experiment_dirs(exp_id)
    loaded, validation_df = load_timeframes()
    summary_rows: list[dict[str, Any]] = []
    lag_rows: list[pd.DataFrame] = []
    for loaded_tf in loaded.values():
        regime_df = add_timebar_regimes(loaded_tf.bars)
        for chart_type in ["Time", "LineBreak", "Renko", "HeikenAshi"]:
            chart = generate_chart(loaded_tf.bars, chart_type)
            hybrid_rate, denom, hybrid_count = event_hybrid_rate(chart, chart_type, regime_df)
            lags, lag_summary = transition_lags(chart, chart_type, regime_df, TIMEFRAMES[loaded_tf.timeframe])
            if not lags.empty:
                lags = lags.assign(
                    Instrument=loaded_tf.instrument,
                    Timeframe=loaded_tf.timeframe,
                    ChartType=chart_type,
                )
                lag_rows.append(lags)
            summary_rows.append(
                {
                    "Instrument": loaded_tf.instrument,
                    "Timeframe": loaded_tf.timeframe,
                    "ChartType": chart_type,
                    "Rows": chart.height,
                    "HybridDenominator": denom,
                    "HybridCount": hybrid_count,
                    "HybridRate": hybrid_rate,
                    **lag_summary,
                    "WithinBounds": bool(
                        chart_type in {"LineBreak", "Renko"}
                        and hybrid_rate <= 0.05
                        and lag_summary.get("MedianLagBars", np.nan) <= 2
                    ),
                }
            )
    summary_df = pd.DataFrame(summary_rows)
    lag_df = pd.concat(lag_rows, ignore_index=True) if lag_rows else pd.DataFrame()
    improvement_rows = []
    for _, row in summary_df[summary_df["ChartType"].isin(["LineBreak", "Renko"])].iterrows():
        improvement_rows.append(
            {
                "Instrument": row.Instrument,
                "Timeframe": row.Timeframe,
                "ChartType": row.ChartType,
                "AbsoluteHybridExcessVsTime": row.HybridRate,
                "AbsoluteMedianLagExcessBarsVsTime": row.MedianLagBars,
            }
        )
    bootstrap_rows = []
    for timeframe in TIMEFRAMES:
        for chart_type in ["LineBreak", "Renko"]:
            values = summary_df.query(
                "Timeframe == @timeframe and ChartType == @chart_type"
            )["HybridRate"].to_numpy(dtype=float)
            ci = bootstrap_mean_ci(values)
            bootstrap_rows.append(
                {
                    "Timeframe": timeframe,
                    "ChartType": chart_type,
                    "Metric": "AbsoluteHybridExcessVsTime",
                    **ci,
                }
            )
    verdict_df = (
        summary_df[summary_df["ChartType"].isin(["LineBreak", "Renko"])]
        .groupby(["Timeframe", "ChartType"], as_index=False)["WithinBounds"]
        .sum()
        .rename(columns={"WithinBounds": "SupportCount"})
    )
    verdict_df["Verdict"] = np.where(verdict_df["SupportCount"] >= 3, "SUPPORTED", "REFUTED")

    save_csv(summary_df, results_dir / "summary_metrics.csv")
    save_csv(validation_df, results_dir / "validation_table.csv")
    save_csv(lag_df, results_dir / "lag_data.csv")
    save_csv(pd.DataFrame(improvement_rows), results_dir / "improvement_vs_time.csv")
    save_csv(pd.DataFrame(bootstrap_rows), results_dir / "bootstrap_results.csv")
    save_csv(verdict_df, results_dir / "hypothesis_verdict.csv")
    write_manifest(exp_id, results_dir, validation_df)

    eurusd_15 = loaded.get(("EURUSD", "15m"))
    if eurusd_15 is not None and not eurusd_15.bars.is_empty():
        regime_plot = add_timebar_regimes(eurusd_15.bars).select(
            ["CloseTime", "Close", "Regime"]
        ).tail(400).to_pandas()
        if not regime_plot.empty:
            fig, ax = plt.subplots(figsize=(10, 4))
            sns.lineplot(data=regime_plot, x="CloseTime", y="Close", ax=ax, color="black", linewidth=1)
            for regime, color in {"Low": "#4c78a8", "Medium": "#f58518", "High": "#e45756"}.items():
                subset = regime_plot[regime_plot["Regime"] == regime]
                if not subset.empty:
                    ax.scatter(subset["CloseTime"], subset["Close"], s=10, label=regime, color=color)
            ax.set_title("EURUSD 15m Regime Timeline")
            ax.legend(loc="best")
            fig.tight_layout()
            fig.savefig(plots_dir / "regime_timeline.png", dpi=150, bbox_inches="tight")
            plt.close(fig)
    simple_bar_plot(summary_df, "Instrument", "HybridRate", "ChartType", plots_dir / "hybrid_rate_by_instrument_charttype.png", "Hybrid Rate")
    if not lag_df.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.boxplot(data=lag_df[lag_df["Matched"]], x="ChartType", y="LagBars", hue="Timeframe", showfliers=False, ax=ax)
        ax.set_title("Confirmed Transition Lag")
        fig.tight_layout()
        fig.savefig(plots_dir / "lag_boxplot_by_charttype.png", dpi=150, bbox_inches="tight")
        plt.close(fig)
    simple_heatmap(pd.DataFrame(improvement_rows), "Instrument", "ChartType", "AbsoluteHybridExcessVsTime", plots_dir / "improvement_heatmap.png", "Hybrid Excess vs Time")


def perturb_time_bars(
    time_bars: pl.DataFrame,
    noise_level: float,
    instrument: str,
    timeframe: str,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Deterministically perturb close prices and repair OHLC integrity."""
    if noise_level <= 0:
        return time_bars.clone(), {"PerturbedRows": 0, "RepairedRows": 0, "InvalidRows": 0, "InvalidPct": 0.0}
    n = time_bars.height
    seed_bytes = f"{instrument}-{timeframe}-{noise_level}-EXP003TF".encode()
    seed = int(hashlib.sha256(seed_bytes).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    mask = rng.random(n) < noise_level
    ranges = (time_bars["High"] - time_bars["Low"]).to_numpy()
    closes = time_bars["Close"].to_numpy()
    opens = time_bars["Open"].to_numpy()
    highs = time_bars["High"].to_numpy()
    lows = time_bars["Low"].to_numpy()
    perturb = np.where(mask, rng.choice([-1.0, 1.0], n) * ranges * rng.uniform(0.1, 0.5, n), 0.0)
    new_close = closes + perturb
    new_high = np.maximum(highs, np.maximum(opens, new_close))
    new_low = np.minimum(lows, np.minimum(opens, new_close))
    invalid = (new_high < np.maximum(opens, new_close)) | (new_low > np.minimum(opens, new_close))
    perturbed = time_bars.with_columns(
        pl.Series("Close", new_close),
        pl.Series("High", new_high),
        pl.Series("Low", new_low),
    )
    return perturbed, {
        "PerturbedRows": int(mask.sum()),
        "RepairedRows": int(np.sum((new_high != highs) | (new_low != lows))),
        "InvalidRows": int(invalid.sum()),
        "InvalidPct": safe_div(float(invalid.sum()), float(n)),
    }


def lz_complexity(sequence: np.ndarray, max_len: int = 200_000) -> float:
    """Log-normalised LZ76 factor count for direction sequences."""
    if len(sequence) > max_len:
        sequence = sequence[:max_len]
    if len(sequence) < 2:
        return 0.0
    text = "".join("1" if item > 0 else "0" for item in sequence)
    factors = 0
    i = 0
    while i < len(text):
        best = 0
        for size in range(1, len(text) - i + 1):
            if text[i : i + size] in text[:i]:
                best = size
            else:
                break
        factors += 1
        i += max(best + 1, 1)
    return float(factors / np.log2(len(text)))


def chart_returns(chart_df: pl.DataFrame, time_bars: pl.DataFrame, chart_type: str) -> np.ndarray:
    """Return sequence for robustness metrics, with HAClose as diagnostic only."""
    if chart_type == "HeikenAshi":
        closes = chart_df["HAClose"].to_numpy()
    else:
        closes = real_close_series(chart_df, time_bars, chart_type)
    return np.diff(closes) if len(closes) > 1 else np.array([], dtype=float)


def stability_metrics(
    base_chart: pl.DataFrame,
    pert_chart: pl.DataFrame,
    base_bars: pl.DataFrame,
    pert_bars: pl.DataFrame,
    chart_type: str,
) -> dict[str, float]:
    """Compute the three scoped relative drift metrics."""
    base_dirs = direction_array(base_chart, chart_type)
    pert_dirs = direction_array(pert_chart, chart_type)
    base_returns = chart_returns(base_chart, base_bars, chart_type)
    pert_returns = chart_returns(pert_chart, pert_bars, chart_type)
    base_up = np.mean(base_dirs > 0) if len(base_dirs) else np.nan
    pert_up = np.mean(pert_dirs > 0) if len(pert_dirs) else np.nan
    base_var = np.var(base_returns, ddof=1) if len(base_returns) > 1 else np.nan
    pert_var = np.var(pert_returns, ddof=1) if len(pert_returns) > 1 else np.nan
    base_lz = lz_complexity(base_dirs)
    pert_lz = lz_complexity(pert_dirs)
    return {
        "DirectionDrift": abs(pert_up - base_up) / max(abs(base_up), 1e-9),
        "ReturnVarianceDrift": abs(pert_var - base_var) / max(abs(base_var), 1e-9),
        "ComplexityDrift": abs(pert_lz - base_lz) / max(abs(base_lz), 1e-9),
    }


def run_exp003_tf(exp_id: str) -> None:
    """Run EXP-003-TF noise robustness replication."""
    results_dir, plots_dir = experiment_dirs(exp_id)
    loaded, validation_df = load_timeframes()
    metric_rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    chart_types = ["Time", "LineBreak", "Renko", "HeikenAshi"]
    for loaded_tf in loaded.values():
        baseline = {chart_type: generate_chart(loaded_tf.bars, chart_type) for chart_type in chart_types}
        for noise_level in [0.0, 0.1, 0.2, 0.3]:
            pert_bars, audit = perturb_time_bars(
                loaded_tf.bars, noise_level, loaded_tf.instrument, loaded_tf.timeframe
            )
            audit_rows.append(
                {
                    "Instrument": loaded_tf.instrument,
                    "Timeframe": loaded_tf.timeframe,
                    "NoiseLevel": noise_level,
                    **audit,
                }
            )
            for chart_type in chart_types:
                pert_chart = generate_chart(pert_bars, chart_type)
                metrics = stability_metrics(
                    baseline[chart_type], pert_chart, loaded_tf.bars, pert_bars, chart_type
                )
                metric_rows.append(
                    {
                        "Instrument": loaded_tf.instrument,
                        "Timeframe": loaded_tf.timeframe,
                        "NoiseLevel": noise_level,
                        "ChartType": chart_type,
                        "Rows": pert_chart.height,
                        **metrics,
                    }
                )
    metric_df = pd.DataFrame(metric_rows)
    audit_df = pd.DataFrame(audit_rows)
    ranking_rows = []
    noise20 = metric_df[metric_df["NoiseLevel"] == 0.2]
    for timeframe in TIMEFRAMES:
        for chart_type in ["LineBreak", "Renko"]:
            for metric in ["DirectionDrift", "ReturnVarianceDrift", "ComplexityDrift"]:
                lower_count = 0
                for instrument in INSTRUMENTS:
                    base = noise20.query(
                        "Instrument == @instrument and Timeframe == @timeframe and ChartType == 'Time'"
                    )
                    event = noise20.query(
                        "Instrument == @instrument and Timeframe == @timeframe and ChartType == @chart_type"
                    )
                    if base.empty or event.empty:
                        continue
                    lower_count += int(event.iloc[0][metric] <= 0.75 * base.iloc[0][metric])
                ranking_rows.append(
                    {
                        "Timeframe": timeframe,
                        "ChartType": chart_type,
                        "Metric": metric,
                        "InstrumentsWithAtLeast25PctLowerDrift": lower_count,
                    }
                )
    ranking_df = pd.DataFrame(ranking_rows)
    save_csv(metric_df, results_dir / "stability_metrics.csv")
    save_csv(audit_df, results_dir / "perturbation_audit.csv")
    save_csv(ranking_df, results_dir / "robustness_ranking.csv")
    save_csv(validation_df, results_dir / "validation_table.csv")
    write_manifest(exp_id, results_dir, validation_df, {"noise_levels": [0.0, 0.1, 0.2, 0.3]})

    plot_df = metric_df.groupby(["NoiseLevel", "Timeframe", "ChartType"], as_index=False)[
        ["DirectionDrift", "ReturnVarianceDrift", "ComplexityDrift"]
    ].mean()
    long = plot_df.melt(id_vars=["NoiseLevel", "Timeframe", "ChartType"], var_name="Metric", value_name="Drift")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.lineplot(data=long, x="NoiseLevel", y="Drift", hue="ChartType", style="Timeframe", ax=ax)
    ax.set_title("Relative Drift by Noise Level")
    fig.tight_layout()
    fig.savefig(plots_dir / "drift_by_noise_level.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    simple_heatmap(ranking_df, "Metric", "ChartType", "InstrumentsWithAtLeast25PctLowerDrift", plots_dir / "robustness_heatmap_20pct.png", "20 Percent Noise Robustness Count")
    simple_bar_plot(audit_df, "Instrument", "RepairedRows", "Timeframe", plots_dir / "perturbation_quality.png", "OHLC Repair Counts")
    dir_20 = metric_df[metric_df["NoiseLevel"] == 0.2]
    if not dir_20.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.boxplot(data=dir_20, x="ChartType", y="DirectionDrift", hue="Timeframe", showfliers=False, ax=ax)
        ax.set_title("Direction Stability Drift at 20 Percent Noise")
        fig.tight_layout()
        fig.savefig(plots_dir / "direction_stability_boxplot_20pct.png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        fig, ax = plt.subplots(figsize=(7, 5))
        sns.scatterplot(
            data=dir_20,
            x="ReturnVarianceDrift",
            y="ComplexityDrift",
            hue="ChartType",
            style="Timeframe",
            ax=ax,
        )
        ax.set_title("Return Variance vs Complexity Drift")
        fig.tight_layout()
        fig.savefig(plots_dir / "variance_vs_complexity_drift.png", dpi=150, bbox_inches="tight")
        plt.close(fig)


def compute_atr(time_bars: pl.DataFrame, period: int = ATR_PERIOD) -> np.ndarray:
    """Compute simple rolling ATR from completed source bars."""
    highs = time_bars["High"].to_numpy()
    lows = time_bars["Low"].to_numpy()
    closes = time_bars["Close"].to_numpy()
    if len(closes) == 0:
        return np.array([], dtype=float)
    prev = np.roll(closes, 1)
    prev[0] = closes[0]
    tr = np.maximum(highs - lows, np.maximum(np.abs(highs - prev), np.abs(lows - prev)))
    atr = np.full(len(closes), np.nan)
    if len(closes) >= period:
        csum = np.cumsum(tr)
        prior = np.concatenate(([0.0], csum[:-period]))
        atr[period - 1 :] = (csum[period - 1 :] - prior) / period
    return atr


def detect_reversals(time_bars: pl.DataFrame, threshold: float) -> pl.DataFrame:
    """Detect ATR-scaled swing reversals timestamped when confirmed."""
    time_bars = normalize_datetime_units(time_bars, ("CloseTime",))
    atr = compute_atr(time_bars)
    closes = time_bars["Close"].to_numpy()
    highs = time_bars["High"].to_numpy()
    lows = time_bars["Low"].to_numpy()
    times = time_bars["CloseTime"].to_list()
    if len(closes) < ATR_PERIOD + 2:
        return pl.DataFrame(
            schema={
                "ReversalTime": pl.Datetime(TIMESTAMP_TIME_UNIT),
                "Direction": pl.Int32,
                "ATR": pl.Float64,
            }
        )
    direction = 1 if closes[ATR_PERIOD] >= closes[ATR_PERIOD - 1] else -1
    extreme = highs[ATR_PERIOD] if direction > 0 else lows[ATR_PERIOD]
    rows = []
    for idx in range(ATR_PERIOD + 1, len(closes)):
        if not np.isfinite(atr[idx]) or atr[idx] <= 0:
            continue
        if direction > 0:
            extreme = max(extreme, highs[idx])
            if closes[idx] <= extreme - threshold * atr[idx]:
                rows.append({"ReversalTime": times[idx], "Direction": -1, "ATR": float(atr[idx])})
                direction = -1
                extreme = lows[idx]
        else:
            extreme = min(extreme, lows[idx])
            if closes[idx] >= extreme + threshold * atr[idx]:
                rows.append({"ReversalTime": times[idx], "Direction": 1, "ATR": float(atr[idx])})
                direction = 1
                extreme = highs[idx]
    if not rows:
        return pl.DataFrame(
            schema={
                "ReversalTime": pl.Datetime(TIMESTAMP_TIME_UNIT),
                "Direction": pl.Int32,
                "ATR": pl.Float64,
            }
        )
    return normalize_datetime_units(pl.DataFrame(rows), ("ReversalTime",)).with_columns(
        pl.col("Direction").cast(pl.Int32)
    )


def direction_change_signals(chart: pl.DataFrame, chart_type: str) -> pl.DataFrame:
    """Extract direction-change signals from chart bars."""
    table = timestamp_direction_table(chart, chart_type, None).drop("Regime")
    if table.height < 2:
        return pl.DataFrame(
            schema={
                "SignalTime": pl.Datetime(TIMESTAMP_TIME_UNIT),
                "Direction": pl.Int32,
            }
        )
    return (
        table.with_columns(pl.col("Direction").shift(1).alias("_prev"))
        .filter(pl.col("_prev").is_not_null() & (pl.col("Direction") != pl.col("_prev")))
        .select(pl.col("Timestamp").alias("SignalTime"), "Direction")
        .pipe(normalize_datetime_units, ("SignalTime",))
    )


def match_reversal_signals(
    reversals: pl.DataFrame,
    signals: pl.DataFrame,
    tolerance_minutes: int,
    minutes_per_bar: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Match chart signals to same-direction real-price reversals."""
    reversals = normalize_datetime_units(reversals, ("ReversalTime",))
    signals = normalize_datetime_units(signals, ("SignalTime",))
    if reversals.is_empty() or signals.is_empty():
        total_signals = signals.height
        return pd.DataFrame(), {
            "ReferenceReversals": reversals.height,
            "TotalSignals": total_signals,
            "MatchedSignals": 0,
            "Precision": 0.0 if total_signals else np.nan,
            "Recall": 0.0 if reversals.height else np.nan,
            "MedianLatencyMinutes": np.nan,
            "MedianLatencyBars": np.nan,
            "SplitRate": np.nan,
        }
    rows = []
    sig_rows = signals.sort("SignalTime")
    for rev in reversals.iter_rows(named=True):
        start = pd.Timestamp(rev["ReversalTime"])
        end = start + pd.Timedelta(minutes=tolerance_minutes)
        start_lit = pl.lit(np.datetime64(start.to_datetime64(), TIMESTAMP_TIME_UNIT)).cast(
            pl.Datetime(TIMESTAMP_TIME_UNIT)
        )
        end_lit = pl.lit(np.datetime64(end.to_datetime64(), TIMESTAMP_TIME_UNIT)).cast(
            pl.Datetime(TIMESTAMP_TIME_UNIT)
        )
        match = sig_rows.filter(
            (pl.col("SignalTime") >= start_lit)
            & (pl.col("SignalTime") <= end_lit)
            & (pl.col("Direction") == int(rev["Direction"]))
        ).head(1)
        if match.is_empty():
            rows.append({"ReversalTime": start, "Matched": False, "LatencyMinutes": np.nan, "LatencyBars": np.nan})
        else:
            signal_time = pd.Timestamp(match["SignalTime"][0])
            latency = (signal_time - start).total_seconds() / 60.0
            rows.append(
                {
                    "ReversalTime": start,
                    "SignalTime": signal_time,
                    "Matched": True,
                    "LatencyMinutes": latency,
                    "LatencyBars": latency / minutes_per_bar,
                }
            )
    match_df = pd.DataFrame(rows)
    matched_count = int(match_df["Matched"].sum())
    total_signals = signals.height
    precision = safe_div(matched_count, total_signals)
    recall = safe_div(matched_count, reversals.height)
    split_rate = safe_div(max(total_signals - matched_count, 0), total_signals)
    matched = match_df[match_df["Matched"]]
    return match_df, {
        "ReferenceReversals": reversals.height,
        "TotalSignals": total_signals,
        "MatchedSignals": matched_count,
        "Precision": precision,
        "Recall": recall,
        "MedianLatencyMinutes": float(matched["LatencyMinutes"].median()) if not matched.empty else np.nan,
        "MedianLatencyBars": float(matched["LatencyBars"].median()) if not matched.empty else np.nan,
        "SplitRate": split_rate,
    }


def run_exp004_tf(exp_id: str) -> None:
    """Run EXP-004-TF market-structure speed/fidelity replication."""
    results_dir, plots_dir = experiment_dirs(exp_id)
    loaded, validation_df = load_timeframes()
    summary_rows: list[dict[str, Any]] = []
    match_frames: list[pd.DataFrame] = []
    sensitivity_rows: list[dict[str, Any]] = []
    for loaded_tf in loaded.values():
        reversals = detect_reversals(loaded_tf.bars, 1.5)
        alt_reversals = detect_reversals(loaded_tf.bars, 2.0)
        sensitivity_rows.append(
            {
                "Instrument": loaded_tf.instrument,
                "Timeframe": loaded_tf.timeframe,
                "PrimaryReversals": reversals.height,
                "AlternateReversals": alt_reversals.height,
                "CountRatioAltToPrimary": safe_div(alt_reversals.height, reversals.height),
            }
        )
        for chart_type in ["Time", "LineBreak", "Renko", "HeikenAshi"]:
            chart = generate_chart(loaded_tf.bars, chart_type)
            signals = direction_change_signals(chart, chart_type)
            matches, stats = match_reversal_signals(
                reversals, signals, 120, TIMEFRAMES[loaded_tf.timeframe]
            )
            if not matches.empty:
                match_frames.append(
                    matches.assign(
                        Instrument=loaded_tf.instrument,
                        Timeframe=loaded_tf.timeframe,
                        ChartType=chart_type,
                    )
                )
            summary_rows.append(
                {
                    "Instrument": loaded_tf.instrument,
                    "Timeframe": loaded_tf.timeframe,
                    "ChartType": chart_type,
                    **stats,
                }
            )
    summary_df = pd.DataFrame(summary_rows)
    match_df = pd.concat(match_frames, ignore_index=True) if match_frames else pd.DataFrame()
    sensitivity_df = pd.DataFrame(sensitivity_rows)
    support_rows = []
    for timeframe in TIMEFRAMES:
        for chart_type in ["LineBreak", "Renko"]:
            faster = 0
            for instrument in INSTRUMENTS:
                base = summary_df.query("Instrument == @instrument and Timeframe == @timeframe and ChartType == 'Time'")
                event = summary_df.query("Instrument == @instrument and Timeframe == @timeframe and ChartType == @chart_type")
                if base.empty or event.empty:
                    continue
                b = base.iloc[0]
                e = event.iloc[0]
                if np.isfinite(b.MedianLatencyBars) and np.isfinite(e.MedianLatencyBars):
                    faster += int(e.MedianLatencyBars <= 0.7 * b.MedianLatencyBars)
            support_rows.append({"Timeframe": timeframe, "ChartType": chart_type, "FasterCount": faster})
    support_df = pd.DataFrame(support_rows)
    save_csv(summary_df, results_dir / "precision_recall_summary.csv")
    save_csv(summary_df, results_dir / "latency_summary.csv")
    save_csv(match_df, results_dir / "event_matching_table.csv")
    save_csv(sensitivity_df, results_dir / "sensitivity_summary.csv")
    save_csv(support_df, results_dir / "support_summary.csv")
    save_csv(validation_df, results_dir / "validation_table.csv")
    write_manifest(exp_id, results_dir, validation_df, {"tolerance_minutes": 120})

    if not match_df.empty:
        timeline = match_df[
            (match_df["Instrument"] == "EURUSD")
            & (match_df["Timeframe"] == "15m")
        ].head(120)
        if not timeline.empty:
            fig, ax = plt.subplots(figsize=(10, 4))
            for idx, chart_type in enumerate(["Time", "LineBreak", "Renko", "HeikenAshi"]):
                subset = timeline[timeline["ChartType"] == chart_type]
                ax.scatter(subset["ReversalTime"], [idx] * len(subset), s=16, label=chart_type)
            ax.set_yticks(range(4), ["Time", "LineBreak", "Renko", "HeikenAshi"])
            ax.set_title("EURUSD 15m Reversal Match Timeline")
            ax.legend(loc="best")
            fig.tight_layout()
            fig.savefig(plots_dir / "event_timeline.png", dpi=150, bbox_inches="tight")
            plt.close(fig)
    if not match_df.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.boxplot(data=match_df[match_df["Matched"]], x="ChartType", y="LatencyBars", hue="Timeframe", showfliers=False, ax=ax)
        ax.set_title("Detection Latency")
        fig.tight_layout()
        fig.savefig(plots_dir / "latency_boxplot.png", dpi=150, bbox_inches="tight")
        plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.scatterplot(data=summary_df, x="Recall", y="Precision", hue="ChartType", style="Timeframe", ax=ax)
    ax.set_title("Precision and Recall")
    fig.tight_layout()
    fig.savefig(plots_dir / "precision_recall_scatter.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    simple_bar_plot(summary_df, "ChartType", "SplitRate", "Timeframe", plots_dir / "split_rate_barchart.png", "Split Rate")
    heat = summary_df.copy()
    time_latency = heat[heat["ChartType"] == "Time"][
        ["Instrument", "Timeframe", "MedianLatencyBars", "Precision"]
    ].rename(
        columns={
            "MedianLatencyBars": "TimeMedianLatencyBars",
            "Precision": "TimePrecision",
        }
    )
    heat = heat.merge(time_latency, on=["Instrument", "Timeframe"], how="left")
    heat["LatencyImprovement"] = 1.0 - heat["MedianLatencyBars"] / heat["TimeMedianLatencyBars"]
    heat["PrecisionChange"] = heat["Precision"] - heat["TimePrecision"]
    simple_heatmap(
        heat[heat["ChartType"].isin(["LineBreak", "Renko"])],
        "Instrument",
        "ChartType",
        "LatencyImprovement",
        plots_dir / "latency_precision_heatmap.png",
        "Latency Improvement vs Time",
    )


def nearest_match_agreement(
    left: pl.DataFrame,
    right: pl.DataFrame,
    tolerance_minutes: int,
    regimes: set[str] | None = None,
) -> dict[str, Any]:
    """Compute nearest timestamp direction agreement within a tolerance."""
    left_pd = left.to_pandas().sort_values("Timestamp")
    right_pd = right.to_pandas().sort_values("Timestamp")
    if regimes is not None:
        left_pd = left_pd[left_pd["Regime"].isin(regimes)]
    if left_pd.empty or right_pd.empty:
        return {"Matches": 0, "LeftRows": len(left_pd), "Agreement": np.nan, "OverlapRate": 0.0}
    r_times = pd.to_datetime(right_pd["Timestamp"]).to_numpy(dtype="datetime64[ns]")
    r_dirs = right_pd["Direction"].to_numpy()
    matches = 0
    agree = 0
    tol = np.timedelta64(tolerance_minutes, "m")
    for _, row in left_pd.iterrows():
        t = np.datetime64(pd.Timestamp(row["Timestamp"]), "ns")
        pos = np.searchsorted(r_times, t)
        candidates = []
        if pos < len(r_times):
            candidates.append(pos)
        if pos > 0:
            candidates.append(pos - 1)
        if not candidates:
            continue
        best = min(candidates, key=lambda idx: abs(r_times[idx] - t))
        if abs(r_times[best] - t) <= tol:
            matches += 1
            agree += int(r_dirs[best] == int(row["Direction"]))
    return {
        "Matches": matches,
        "LeftRows": len(left_pd),
        "Agreement": safe_div(agree, matches),
        "OverlapRate": safe_div(matches, len(left_pd)),
    }


def run_exp005_tf(exp_id: str) -> None:
    """Run EXP-005-TF cross-chart agreement replication."""
    results_dir, plots_dir = experiment_dirs(exp_id)
    loaded, validation_df = load_timeframes()
    pair_rows: list[dict[str, Any]] = []
    regime_rows: list[dict[str, Any]] = []
    pairs = [
        ("LineBreak", "Renko"),
        ("LineBreak", "Time"),
        ("Renko", "Time"),
        ("Time", "HeikenAshi"),
    ]
    for loaded_tf in loaded.values():
        regime_df = add_timebar_regimes(loaded_tf.bars)
        tables = {
            chart_type: timestamp_direction_table(
                generate_chart(loaded_tf.bars, chart_type), chart_type, regime_df
            )
            for chart_type in ["Time", "LineBreak", "Renko", "HeikenAshi"]
        }
        for tolerance in [5, 15]:
            for left_name, right_name in pairs:
                all_stats = nearest_match_agreement(tables[left_name], tables[right_name], tolerance)
                pair_rows.append(
                    {
                        "Instrument": loaded_tf.instrument,
                        "Timeframe": loaded_tf.timeframe,
                        "Pair": f"{left_name}<->{right_name}",
                        "ToleranceMinutes": tolerance,
                        **all_stats,
                    }
                )
                for regime in ["Low", "Medium", "High"]:
                    stats = nearest_match_agreement(
                        tables[left_name], tables[right_name], tolerance, {regime}
                    )
                    regime_rows.append(
                        {
                            "Instrument": loaded_tf.instrument,
                            "Timeframe": loaded_tf.timeframe,
                            "Pair": f"{left_name}<->{right_name}",
                            "Regime": regime,
                            "ToleranceMinutes": tolerance,
                            **stats,
                        }
                    )
    pair_df = pd.DataFrame(pair_rows)
    regime_df = pd.DataFrame(regime_rows)
    sensitivity_df = (
        pair_df.groupby(["Timeframe", "Pair", "ToleranceMinutes"], as_index=False)[["Agreement", "OverlapRate"]]
        .mean()
    )
    bootstrap_rows = []
    for timeframe in TIMEFRAMES:
        for tolerance in [5, 15]:
            lb_r = regime_df.query(
                "Timeframe == @timeframe and ToleranceMinutes == @tolerance and Pair == 'LineBreak<->Renko' and Regime in ['Medium', 'High']"
            )
            lb_t = regime_df.query(
                "Timeframe == @timeframe and ToleranceMinutes == @tolerance and Pair == 'LineBreak<->Time' and Regime in ['Medium', 'High']"
            )
            rk_t = regime_df.query(
                "Timeframe == @timeframe and ToleranceMinutes == @tolerance and Pair == 'Renko<->Time' and Regime in ['Medium', 'High']"
            )
            for label, other in [("LB_Renko_minus_LB_Time", lb_t), ("LB_Renko_minus_Renko_Time", rk_t)]:
                merged = lb_r.merge(
                    other,
                    on=["Instrument", "Timeframe", "Regime", "ToleranceMinutes"],
                    suffixes=("_lb_renko", "_other"),
                )
                diffs = merged["Agreement_lb_renko"].to_numpy(dtype=float) - merged["Agreement_other"].to_numpy(dtype=float)
                ci = bootstrap_mean_ci(diffs)
                bootstrap_rows.append(
                    {
                        "Timeframe": timeframe,
                        "ToleranceMinutes": tolerance,
                        "Comparison": label,
                        **ci,
                    }
                )
    save_csv(pair_df, results_dir / "pairwise_metrics.csv")
    save_csv(regime_df, results_dir / "regime_metrics.csv")
    save_csv(pd.DataFrame(bootstrap_rows), results_dir / "bootstrap_cis.csv")
    save_csv(sensitivity_df, results_dir / "sensitivity_metrics.csv")
    save_csv(validation_df, results_dir / "validation_table.csv")
    write_manifest(exp_id, results_dir, validation_df)
    (results_dir / "results.json").write_text(json.dumps({"pairwise": pair_rows, "regime": regime_rows}, indent=2, default=str) + "\n")

    simple_heatmap(pair_df[pair_df["ToleranceMinutes"] == 5], "Instrument", "Pair", "Agreement", plots_dir / "agreement_heatmap.png", "Pairwise Agreement")
    simple_heatmap(pair_df[pair_df["ToleranceMinutes"] == 5], "Instrument", "Pair", "OverlapRate", plots_dir / "overlap_heatmap.png", "Pairwise Overlap")
    med_high = regime_df[(regime_df["Regime"].isin(["Medium", "High"])) & (regime_df["ToleranceMinutes"] == 5)]
    simple_bar_plot(med_high, "Pair", "Agreement", "Timeframe", plots_dir / "regime_bars.png", "Medium/High Regime Agreement")
    simple_bar_plot(sensitivity_df, "Pair", "Agreement", "ToleranceMinutes", plots_dir / "sensitivity.png", "Tolerance Sensitivity")
    raster = pair_df[
        (pair_df["Instrument"] == "EURUSD")
        & (pair_df["Timeframe"] == "15m")
        & (pair_df["ToleranceMinutes"] == 5)
    ]
    if not raster.empty:
        fig, ax = plt.subplots(figsize=(9, 3))
        sns.barplot(data=raster, x="Pair", y="Agreement", hue="Pair", dodge=False, ax=ax)
        ax.set_title("EURUSD 15m Direction Agreement Snapshot")
        ax.tick_params(axis="x", rotation=25)
        ax.legend_.remove() if ax.legend_ else None
        fig.tight_layout()
        fig.savefig(plots_dir / "timeline_raster.png", dpi=150, bbox_inches="tight")
        plt.close(fig)


def block_bootstrap_compression(real_returns: np.ndarray, ha_returns: np.ndarray) -> dict[str, Any]:
    """Block-bootstrap compression intervals for HA diagnostic returns."""
    real = real_returns[np.isfinite(real_returns)]
    ha = ha_returns[np.isfinite(ha_returns)]
    n = min(len(real), len(ha))
    if n < 100:
        return {}
    real = real[:n]
    ha = ha[:n]
    block = min(100, max(10, n // 20))
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    starts_max = n - block + 1
    vals = {"VolatilityCompression": [], "MedianAbsReturnCompression": []}
    for _ in range(BOOTSTRAP_N):
        starts = rng.integers(0, starts_max, size=int(np.ceil(n / block)))
        idx = np.concatenate([np.arange(start, start + block) for start in starts])[:n]
        real_s = real[idx]
        ha_s = ha[idx]
        vals["VolatilityCompression"].append(1.0 - np.std(ha_s, ddof=1) / np.std(real_s, ddof=1))
        vals["MedianAbsReturnCompression"].append(
            1.0 - np.median(np.abs(ha_s)) / np.median(np.abs(real_s))
        )
    return {
        metric: {
            "Point": float(np.mean(series)),
            "CILower": float(np.quantile(series, 0.025)),
            "CIUpper": float(np.quantile(series, 0.975)),
        }
        for metric, series in vals.items()
    }


def run_exp006_tf(exp_id: str) -> None:
    """Run EXP-006-TF HA synthetic-price distortion replication."""
    results_dir, plots_dir = experiment_dirs(exp_id)
    loaded, validation_df = load_timeframes()
    metric_rows: list[dict[str, Any]] = []
    regime_rows: list[dict[str, Any]] = []
    plot_samples: list[pd.DataFrame] = []
    for loaded_tf in loaded.values():
        ha = generate_heiken_ashi(loaded_tf.bars)
        paired = ha.with_columns(
            (pl.col("RealClose").log() - pl.col("RealClose").log().shift(1)).alias("RealReturn"),
            (pl.col("HAClose").log() - pl.col("HAClose").log().shift(1)).alias("HAReturn"),
            (pl.col("RealHigh") - pl.col("RealLow")).alias("RealRange"),
            (pl.col("HAHigh") - pl.col("HALow")).alias("HARange"),
        ).drop_nulls(["RealReturn", "HAReturn"])
        paired = normalize_datetime_units(paired, ("CloseTime",))
        real_returns = paired["RealReturn"].to_numpy()
        ha_returns = paired["HAReturn"].to_numpy()
        real_vol = realised_volatility(real_returns)
        ha_vol = realised_volatility(ha_returns)
        real_mad = float(np.median(np.abs(real_returns))) if len(real_returns) else np.nan
        ha_mad = float(np.median(np.abs(ha_returns))) if len(ha_returns) else np.nan
        real_dir_change = float(np.mean(np.diff(np.sign(real_returns)) != 0)) if len(real_returns) > 1 else np.nan
        ha_dir_change = float(np.mean(np.diff(np.sign(ha_returns)) != 0)) if len(ha_returns) > 1 else np.nan
        boot = block_bootstrap_compression(real_returns, ha_returns)
        metric_rows.append(
            {
                "Instrument": loaded_tf.instrument,
                "Timeframe": loaded_tf.timeframe,
                "Rows": paired.height,
                "RealVolatility": real_vol,
                "HAVolatility": ha_vol,
                "VolatilityCompression": 1.0 - ha_vol / real_vol,
                "RealMedianAbsReturn": real_mad,
                "HAMedianAbsReturn": ha_mad,
                "MedianAbsReturnCompression": 1.0 - ha_mad / real_mad,
                "RealDirectionChangeFrequency": real_dir_change,
                "HADirectionChangeFrequency": ha_dir_change,
                "DirectionChangeCompression": 1.0 - ha_dir_change / real_dir_change,
                "Bootstrap": boot,
            }
        )
        sample = paired.head(min(PLOT_SAMPLE_N, paired.height)).select(["RealReturn", "HAReturn"]).to_pandas()
        sample["Instrument"] = loaded_tf.instrument
        sample["Timeframe"] = loaded_tf.timeframe
        plot_samples.append(sample)
        regime_source = add_timebar_regimes(loaded_tf.bars)
        regime_joined = paired.join(
            normalize_datetime_units(regime_source.select(["CloseTime", "Regime"]), ("CloseTime",)),
            on="CloseTime",
            how="left",
        )
        for regime in ["Low", "Medium", "High"]:
            subset = regime_joined.filter(pl.col("Regime") == regime)
            if subset.height < 3:
                continue
            r = subset["RealReturn"].to_numpy()
            h = subset["HAReturn"].to_numpy()
            regime_rows.append(
                {
                    "Instrument": loaded_tf.instrument,
                    "Timeframe": loaded_tf.timeframe,
                    "Regime": regime,
                    "Rows": subset.height,
                    "VolatilityCompression": 1.0 - realised_volatility(h) / realised_volatility(r),
                    "MedianAbsReturnCompression": 1.0 - np.median(np.abs(h)) / np.median(np.abs(r)),
                }
            )
    metrics_df = pd.DataFrame(metric_rows)
    metrics_flat = metrics_df.drop(columns=["Bootstrap"])
    regime_df = pd.DataFrame(regime_rows)
    save_csv(metrics_flat, results_dir / "distortion_metrics.csv")
    save_csv(regime_df, results_dir / "regime_distortion_metrics.csv")
    save_csv(validation_df, results_dir / "validation_table.csv")
    (results_dir / "distortion_metrics.json").write_text(json.dumps(metric_rows, indent=2, default=str) + "\n")
    write_manifest(exp_id, results_dir, validation_df)

    eurusd = loaded.get(("EURUSD", "15m"))
    if eurusd is not None and not eurusd.bars.is_empty():
        ha = generate_heiken_ashi(eurusd.bars).head(300).to_pandas()
        if not ha.empty:
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(ha["CloseTime"], ha["RealClose"], label="RealClose", linewidth=1)
            ax.plot(ha["CloseTime"], ha["HAClose"], label="HAClose diagnostic", linewidth=1)
            ax.set_title("EURUSD 15m Real vs Heiken Ashi Close")
            ax.legend(loc="best")
            fig.tight_layout()
            fig.savefig(plots_dir / "01_paired_close_window.png", dpi=150, bbox_inches="tight")
            plt.close(fig)
    simple_bar_plot(metrics_flat, "Instrument", "VolatilityCompression", "Timeframe", plots_dir / "02_volatility_compression.png", "HA Volatility Compression")
    if plot_samples:
        abs_df = pd.concat(plot_samples, ignore_index=True)
        long = abs_df.melt(id_vars=["Instrument", "Timeframe"], value_vars=["RealReturn", "HAReturn"], var_name="Series", value_name="Return")
        long["AbsReturn"] = long["Return"].abs()
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.boxplot(data=long, x="Instrument", y="AbsReturn", hue="Series", showfliers=False, ax=ax)
        ax.set_title("Absolute Real vs HA Diagnostic Returns")
        fig.tight_layout()
        fig.savefig(plots_dir / "03_abs_return_box.png", dpi=150, bbox_inches="tight")
        plt.close(fig)
    simple_heatmap(regime_df, "Instrument", "Regime", "VolatilityCompression", plots_dir / "04_regime_heatmap.png", "Regime Volatility Compression")


RUNNERS: dict[str, Callable[[str], None]] = {
    "EXP-001-TF": run_exp001_tf,
    "EXP-002-TF": run_exp002_tf,
    "EXP-003-TF": run_exp003_tf,
    "EXP-004-TF": run_exp004_tf,
    "EXP-005-TF": run_exp005_tf,
    "EXP-006-TF": run_exp006_tf,
}


def run_tf_experiment(exp_id: str) -> None:
    """Run one approved timeframe-replication experiment by ID."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if exp_id not in RUNNERS:
        raise ValueError(f"Unsupported timeframe experiment: {exp_id}")
    sns.set_theme(style="whitegrid")
    LOGGER.info("Starting %s", exp_id)
    RUNNERS[exp_id](exp_id)
    LOGGER.info("%s complete", exp_id)
