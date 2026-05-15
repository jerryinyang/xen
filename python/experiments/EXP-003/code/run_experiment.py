"""
Experiment EXP-003: Noise Filtering & Statistical Robustness
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
NOISE_LEVELS = [0.0, 0.10, 0.20, 0.30]

CHART_CONFIG: dict[str, dict[str, Any]] = {
    "Time": {
        "generator": None,
        "params": {},
        "time_col": "CloseTime",
        "close_col": "Close",
        "dir_col": None,
    },
    "LineBreak": {
        "generator": "linebreak",
        "params": {"level": 3},
        "time_col": "SourceCloseTime",
        "close_col": None,
        "dir_col": "Direction",
    },
    "Renko": {
        "generator": "renko",
        "params": {"atr_period": 14},
        "time_col": "SourceCloseTime",
        "close_col": None,
        "dir_col": "Direction",
    },
    "HeikenAshi": {
        "generator": "heiken_ashi",
        "params": {},
        "time_col": "CloseTime",
        "close_col": "RealClose",
        "dir_col": "Direction",
    },
}

DATA_DIR = PROJECT_ROOT / "data"
PLOTS_DIR = PYTHON_ROOT / "experiments/EXP-003/plots"
RESULTS_DIR = PYTHON_ROOT / "experiments/EXP-003/results"

BOOTSTRAP_SEED = 42
N_BOOTSTRAP = 10_000

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_timebar_data(instrument: str) -> pl.DataFrame:
    """Load and concatenate all time-bar Parquet files for an instrument.

    Parameters
    ----------
    instrument : str
        Instrument symbol (e.g. "EURUSD").

    Returns
    -------
    pl.DataFrame
        Concatenated, sorted, deduplicated time-bar data.
    """
    pattern = f"timebars/timebars_{instrument.lower()}_*.parquet"
    matches = sorted(DATA_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(
            f"No time-bar file found for {instrument} matching {pattern}"
        )
    return (
        pl.scan_parquet(matches)
        .sort("CloseTime")
        .unique()
        .collect()
    )


# ---------------------------------------------------------------------------
# Perturbation
# ---------------------------------------------------------------------------
def perturb_time_bars(
    time_bars: pl.DataFrame,
    noise_level: float,
    instrument: str,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Deterministically perturb a fraction of source bars.

    Parameters
    ----------
    time_bars : pl.DataFrame
        Source 1-minute time bars.
    noise_level : float
        Fraction of bars to perturb (0.0-1.0).
    instrument : str
        Instrument name; used with a fixed suffix to seed the RNG,
        ensuring reproducible bar selection and magnitude signs.

    Returns
    -------
    tuple[pl.DataFrame, dict]
        Perturbed time bars and an audit dict with
        ``perturbed_rows`` and ``repaired_rows`` counts.
    """
    if noise_level == 0.0:
        return time_bars.clone(), {
            "perturbed_rows": 0,
            "repaired_rows": 0,
        }

    n = len(time_bars)
    base_seed = abs(hash(f"{instrument}_EXP003_noise")) % (2**31)
    rng = np.random.default_rng(base_seed)

    perturb_mask = rng.random(n) < noise_level
    n_perturb = int(perturb_mask.sum())

    # Deterministic signs and magnitude multipliers
    signs = rng.choice([-1, 1], size=n)
    mag_multipliers = rng.uniform(0.1, 0.5, size=n)

    bar_ranges = (time_bars["High"] - time_bars["Low"]).to_numpy()
    closes = time_bars["Close"].to_numpy()
    highs = time_bars["High"].to_numpy()
    lows = time_bars["Low"].to_numpy()

    perturbations = np.where(
        perturb_mask, signs * bar_ranges * mag_multipliers, 0.0
    )
    new_closes = closes + perturbations

    # Repair OHLC integrity: High >= Close, Low <= Close
    new_highs = np.maximum(highs, new_closes)
    new_lows = np.minimum(lows, new_closes)

    repaired = int(
        np.sum((new_highs != highs) | (new_lows != lows))
    )

    df = time_bars.with_columns(
        [
            pl.Series("Close", new_closes),
            pl.Series("High", new_highs),
            pl.Series("Low", new_lows),
        ]
    )

    return df, {
        "perturbed_rows": n_perturb,
        "repaired_rows": repaired,
    }


# ---------------------------------------------------------------------------
# Chart generation
# ---------------------------------------------------------------------------
def generate_chart(
    time_bars: pl.DataFrame,
    chart_type: str,
) -> pl.DataFrame:
    """Generate a chart-type DataFrame.

    Parameters
    ----------
    time_bars : pl.DataFrame
        Source 1-minute time bars.
    chart_type : str
        Chart type key from CHART_CONFIG.

    Returns
    -------
    pl.DataFrame
        Generated chart-type bars.
    """
    config = CHART_CONFIG[chart_type]
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
# Real-close alignment for event chart types
# ---------------------------------------------------------------------------
def attach_real_close(
    chart_df: pl.DataFrame,
    time_bars: pl.DataFrame,
    time_col: str,
) -> pl.DataFrame:
    """Join real closes from time bars onto event chart bars by timestamp.

    Parameters
    ----------
    chart_df : pl.DataFrame
        Chart-type bars.
    time_bars : pl.DataFrame
        Source time bars carrying ``CloseTime`` and ``Close``.
    time_col : str
        Timestamp column in ``chart_df`` to join on
        (``CloseTime`` or ``SourceCloseTime``).

    Returns
    -------
    pl.DataFrame
        Chart bars with ``RealClose`` joined.
    """
    chart_df = normalize_timestamp_columns(chart_df, [time_col])
    real = time_bars.select(["CloseTime", "Close"]).rename(
        {"CloseTime": time_col, "Close": "RealClose"}
    )
    real = normalize_timestamp_columns(real, [time_col])
    return chart_df.join(real, on=time_col, how="left")


# ---------------------------------------------------------------------------
# Stability metrics
# ---------------------------------------------------------------------------
def lempel_ziv_complexity(
    sequence: np.ndarray,
    max_len: int = 200_000,
) -> int:
    """Lempel-Ziv complexity of a binary sequence.

    Parameters
    ----------
    sequence : np.ndarray
        Array of +1/-1 (or any numeric) direction codes.
    max_len : int
        Maximum sequence length to analyse (truncates if longer).

    Returns
    -------
    int
        LZ complexity count (number of distinct substrings).
    """
    if len(sequence) == 0:
        return 0
    if len(sequence) > max_len:
        sequence = sequence[:max_len]
    s = "".join("1" if x > 0 else "0" for x in sequence)
    n = len(s)
    complexity = 1
    i = 1
    while i < n:
        for length in range(1, n - i + 1):
            sub = s[i : i + length]
            if sub not in s[:i]:
                complexity += 1
                i += length
                break
        else:
            break
    return complexity


def compute_direction_stability(
    baseline_directions: np.ndarray,
    perturbed_directions: np.ndarray,
) -> float:
    """Relative drift in the fraction of up-bars.

    Parameters
    ----------
    baseline_directions : np.ndarray
        Direction sequence from unperturbed chart.
    perturbed_directions : np.ndarray
        Direction sequence from perturbed chart.

    Returns
    -------
    float
        Relative drift (>=0); lower = more stable.
    """
    if len(baseline_directions) == 0 or len(perturbed_directions) == 0:
        return np.nan
    baseline_up = np.mean(baseline_directions > 0)
    perturbed_up = np.mean(perturbed_directions > 0)
    denom = max(abs(baseline_up), 1e-9)
    return abs(perturbed_up - baseline_up) / denom


def compute_variance_stability(
    baseline_returns: np.ndarray,
    perturbed_returns: np.ndarray,
) -> float:
    """Relative drift in return variance.

    Parameters
    ----------
    baseline_returns : np.ndarray
        Real-close returns from unperturbed chart.
    perturbed_returns : np.ndarray
        Real-close returns from perturbed chart.

    Returns
    -------
    float
        Relative drift (>=0); lower = more stable.
    """
    if len(baseline_returns) < 2 or len(perturbed_returns) < 2:
        return np.nan
    baseline_var = np.var(baseline_returns, ddof=1)
    perturbed_var = np.var(perturbed_returns, ddof=1)
    denom = max(abs(baseline_var), 1e-9)
    return abs(perturbed_var - baseline_var) / denom


def compute_complexity_stability(
    baseline_directions: np.ndarray,
    perturbed_directions: np.ndarray,
) -> float:
    """Relative drift in Lempel-Ziv complexity.

    Parameters
    ----------
    baseline_directions : np.ndarray
        Direction sequence from unperturbed chart.
    perturbed_directions : np.ndarray
        Direction sequence from perturbed chart.

    Returns
    -------
    float
        Relative drift (>=0); lower = more stable.
    """
    if len(baseline_directions) == 0 or len(perturbed_directions) == 0:
        return np.nan
    baseline_lz = lempel_ziv_complexity(baseline_directions)
    perturbed_lz = lempel_ziv_complexity(perturbed_directions)
    denom = max(baseline_lz, 1)
    return abs(perturbed_lz - baseline_lz) / denom


def extract_directions(chart_df: pl.DataFrame, chart_type: str) -> np.ndarray:
    """Extract a direction sequence from chart-type bars.

    Parameters
    ----------
    chart_df : pl.DataFrame
        Chart-type bars.
    chart_type : str
        Chart type key.

    Returns
    -------
    np.ndarray
        Direction array (+1 for up, -1 for down).
    """
    config = CHART_CONFIG[chart_type]
    if config["dir_col"] is not None:
        return chart_df[config["dir_col"]].to_numpy()
    # Time bars: derive direction from Close vs Open
    return np.where(
        chart_df["Close"].to_numpy() >= chart_df["Open"].to_numpy(), 1, -1
    )


def extract_real_returns(
    chart_df: pl.DataFrame,
    time_bars: pl.DataFrame,
    chart_type: str,
) -> np.ndarray:
    """Extract real-close returns aligned to chart-type events.

    Parameters
    ----------
    chart_df : pl.DataFrame
        Chart-type bars.
    time_bars : pl.DataFrame
        Source time bars for real-close lookups.
    chart_type : str
        Chart type key.

    Returns
    -------
    np.ndarray
        First-differenced real-close returns.
    """
    config = CHART_CONFIG[chart_type]
    time_col = config["time_col"]

    if config["close_col"] is not None:
        # Heiken Ashi has RealClose natively
        close_series = chart_df[config["close_col"]]
    else:
        # Line Break / Renko need real-close join
        joined = attach_real_close(chart_df, time_bars, time_col)
        close_series = joined["RealClose"]

    closes = close_series.drop_nulls().to_numpy()
    if len(closes) < 2:
        return np.array([])
    return np.diff(closes)


def compute_all_stability_metrics(
    baseline_chart: pl.DataFrame,
    perturbed_chart: pl.DataFrame,
    baseline_timebars: pl.DataFrame,
    perturbed_timebars: pl.DataFrame,
    chart_type: str,
) -> dict[str, float]:
    """Compute the three stability metrics for a chart-type pair.

    Parameters
    ----------
    baseline_chart : pl.DataFrame
        Chart from unperturbed source bars.
    perturbed_chart : pl.DataFrame
        Chart from perturbed source bars.
    baseline_timebars : pl.DataFrame
        Unperturbed source bars (for real-close lookups).
    perturbed_timebars : pl.DataFrame
        Perturbed source bars (for real-close lookups).
    chart_type : str
        Chart type key.

    Returns
    -------
    dict[str, float]
        Metric dict with ``DirectionDrift``, ``VarianceDrift``,
        and ``ComplexityDrift``.
    """
    base_dirs = extract_directions(baseline_chart, chart_type)
    pert_dirs = extract_directions(perturbed_chart, chart_type)

    base_rets = extract_real_returns(baseline_chart, baseline_timebars, chart_type)
    pert_rets = extract_real_returns(perturbed_chart, perturbed_timebars, chart_type)

    return {
        "DirectionDrift": compute_direction_stability(base_dirs, pert_dirs),
        "VarianceDrift": compute_variance_stability(base_rets, pert_rets),
        "ComplexityDrift": compute_complexity_stability(base_dirs, pert_dirs),
    }


# ---------------------------------------------------------------------------
# Statistical summaries
# ---------------------------------------------------------------------------
def bootstrap_mean_ci(
    values: np.ndarray,
    n_bootstrap: int = N_BOOTSTRAP,
    seed: int = BOOTSTRAP_SEED,
    confidence: float = 0.95,
) -> tuple[float, float, float]:
    """Bootstrap percentile CI for the mean.

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


def paired_drift_summary(
    diffs: np.ndarray,
    comparison_label: str,
    metric_label: str,
) -> dict[str, Any]:
    """Descriptive summary of instrument-level paired drift differences.

    Parameters
    ----------
    diffs : np.ndarray
        Paired differences (event_drift - time_drift) per instrument.
    comparison_label : str
        Name of the comparison (e.g. "LineBreak vs Time").
    metric_label : str
        Metric name (e.g. "DirectionDrift").

    Returns
    -------
    dict[str, Any]
        Summary with mean, CI bounds, sign counts, and n.
    """
    mean_val, lo, hi = bootstrap_mean_ci(diffs)
    return {
        "Comparison": comparison_label,
        "Metric": metric_label,
        "MeanDiff": mean_val,
        "CI_Lower": lo,
        "CI_Upper": hi,
        "CI_Excludes_Zero": (lo > 0) or (hi < 0),
        "SignCountNegative": int(np.sum(diffs < 0)),
        "SignCountPositive": int(np.sum(diffs > 0)),
        "N_Instruments": len(diffs),
    }


# ---------------------------------------------------------------------------
# Plotting functions
# ---------------------------------------------------------------------------
def plot_drift_by_noise(
    df: pd.DataFrame,
    save_path: Path,
) -> plt.Figure:
    """Line plot of relative metric drift by noise level and chart type.

    Parameters
    ----------
    df : pd.DataFrame
        Long-format DataFrame with ``NoiseLevel``, ``ChartType``,
        ``Metric``, and ``MeanDrift``.
    save_path : Path
        File path to save the figure.

    Returns
    -------
    plt.Figure
        The figure object.
    """
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    metrics = ["DirectionDrift", "VarianceDrift", "ComplexityDrift"]
    titles = ["Direction Stability", "Variance Stability", "Complexity Stability"]
    for ax, metric, title in zip(axes, metrics, titles):
        subset = df[df["Metric"] == metric]
        for chart_type in subset["ChartType"].unique():
            ct_data = subset[subset["ChartType"] == chart_type]
            ax.plot(
                ct_data["NoiseLevel"],
                ct_data["MeanDrift"],
                marker="o",
                label=chart_type,
            )
        ax.set_title(title)
        ax.set_xlabel("Noise Level")
        ax.set_ylabel("Relative Drift")
        ax.set_xticks([0.0, 0.1, 0.2, 0.3])
        ax.legend(title="Chart Type", fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


def plot_robustness_heatmap(
    df: pd.DataFrame,
    save_path: Path,
) -> plt.Figure:
    """Heatmap of 20% noise robustness rank by instrument and metric.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame at noise=0.20 with ``Instrument``, ``ChartType``,
        ``Metric``, and ``DriftRank`` (1=most robust).
    save_path : Path
        File path to save the figure.

    Returns
    -------
    plt.Figure
        The figure object.
    """
    sns.set_theme(style="white")
    pivot = df.pivot_table(
        index=["Instrument", "Metric"],
        columns="ChartType",
        values="DriftRank",
    )
    fig, ax = plt.subplots(figsize=(8, 8))
    sns.heatmap(
        pivot,
        annot=True,
        fmt=".0f",
        cmap="RdYlGn_r",
        ax=ax,
        cbar_kws={"label": "Rank (1=most robust)"},
        vmin=1,
        vmax=4,
    )
    ax.set_title("Robustness Rank at 20% Noise (1=Most Robust)")
    ax.set_ylabel("Instrument / Metric")
    ax.set_xlabel("Chart Type")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


def plot_direction_boxplot(
    df: pd.DataFrame,
    save_path: Path,
) -> plt.Figure:
    """Box plot of direction stability by chart type at 20% noise.

    Parameters
    ----------
    df : pd.DataFrame
        Long-format DataFrame with ``Instrument``, ``ChartType``,
        and ``DirectionDrift``.
    save_path : Path
        File path to save the figure.

    Returns
    -------
    plt.Figure
        The figure object.
    """
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=df, x="ChartType", y="DirectionDrift", ax=ax)
    ax.set_title("Direction Stability by Chart Type (20% Noise)")
    ax.set_ylabel("Relative Direction Drift")
    ax.set_xlabel("Chart Type")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


def plot_perturbation_quality(
    df: pd.DataFrame,
    save_path: Path,
) -> plt.Figure:
    """Bar chart of repaired OHLC rows by instrument and noise level.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with ``Instrument``, ``NoiseLevel``, ``PerturbedRows``,
        and ``RepairedRows``.
    save_path : Path
        File path to save the figure.

    Returns
    -------
    plt.Figure
        The figure object.
    """
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(df))
    width = 0.35
    bars1 = ax.bar(
        x - width / 2,
        df["PerturbedRows"],
        width,
        label="Perturbed",
    )
    bars2 = ax.bar(
        x + width / 2,
        df["RepairedRows"],
        width,
        label="Repaired",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(
        [f"{r['Instrument']}\n{r['NoiseLevel']:.0%}" for _, r in df.iterrows()],
        rotation=45,
        ha="right",
    )
    ax.set_title("Perturbation Quality by Instrument and Noise Level")
    ax.set_ylabel("Row Count")
    ax.legend()
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


def plot_variance_vs_complexity(
    df: pd.DataFrame,
    save_path: Path,
) -> plt.Figure:
    """Scatter plot of variance drift versus complexity drift at 20% noise.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with ``VarianceDrift``, ``ComplexityDrift``,
        ``ChartType``, and ``Instrument``.
    save_path : Path
        File path to save the figure.

    Returns
    -------
    plt.Figure
        The figure object.
    """
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 6))
    for chart_type in df["ChartType"].unique():
        subset = df[df["ChartType"] == chart_type]
        ax.scatter(
            subset["VarianceDrift"],
            subset["ComplexityDrift"],
            label=chart_type,
            s=80,
            alpha=0.7,
        )
    ax.set_title("Variance Drift vs Complexity Drift (20% Noise)")
    ax.set_xlabel("Variance Drift")
    ax.set_ylabel("Complexity Drift")
    ax.legend(title="Chart Type")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def main() -> None:
    """Run the full EXP-003 analysis pipeline."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("EXP-003: Noise Filtering & Statistical Robustness")
    print(f"Instruments: {', '.join(INSTRUMENTS)}")
    print(f"Noise levels: {NOISE_LEVELS}")
    print(f"Chart types: {', '.join(CHART_CONFIG.keys())}")
    print(f"Output: {PLOTS_DIR} and {RESULTS_DIR}\n")

    # Records for CSV outputs
    metric_records: list[dict[str, Any]] = []
    perturbation_records: list[dict[str, Any]] = []
    bootstrap_records: list[dict[str, Any]] = []

    # Store per-instrument metric tables for later comparison
    instrument_metrics: dict[str, dict[float, dict[str, dict[str, float]]]] = {
        inst: {} for inst in INSTRUMENTS
    }

    for instrument in INSTRUMENTS:
        try:
            print(f"Processing {instrument} ...")
            full_df = load_timebar_data(instrument)
            if len(full_df) == 0:
                print(f"  Skipping {instrument}: empty dataset")
                continue

            # Global holdout: first 70% only
            analysis_df = full_df.slice(0, int(len(full_df) * 0.7))
            print(f"  Analysis rows: {len(analysis_df):,}")

            # Baseline (0% noise) charts
            baseline_charts: dict[str, pl.DataFrame] = {}
            for chart_type in CHART_CONFIG:
                baseline_charts[chart_type] = generate_chart(
                    analysis_df, chart_type
                )

            for noise_level in NOISE_LEVELS:
                perturbed_df, audit = perturb_time_bars(
                    analysis_df, noise_level, instrument
                )
                perturbation_records.append(
                    {
                        "Instrument": instrument,
                        "NoiseLevel": noise_level,
                        "PerturbedRows": audit["perturbed_rows"],
                        "RepairedRows": audit["repaired_rows"],
                    }
                )

                instrument_metrics[instrument][noise_level] = {}

                for chart_type in CHART_CONFIG:
                    perturbed_chart = generate_chart(perturbed_df, chart_type)

                    metrics = compute_all_stability_metrics(
                        baseline_charts[chart_type],
                        perturbed_chart,
                        analysis_df,
                        perturbed_df,
                        chart_type,
                    )

                    instrument_metrics[instrument][noise_level][chart_type] = metrics

                    metric_records.append(
                        {
                            "Instrument": instrument,
                            "NoiseLevel": noise_level,
                            "ChartType": chart_type,
                            **metrics,
                        }
                    )

        except Exception as exc:
            print(f"  Warning: Failed to process {instrument}: {exc}")
            continue

    # --- Paired comparisons at 20% noise ---
    print("\nPaired drift comparisons at 20% noise ...")
    target_noise = 0.20
    event_types = ["LineBreak", "Renko", "HeikenAshi"]
    metrics = ["DirectionDrift", "VarianceDrift", "ComplexityDrift"]

    for event_type in event_types:
        for metric in metrics:
            diffs = np.array(
                [
                    instrument_metrics[inst][target_noise][event_type][metric]
                    - instrument_metrics[inst][target_noise]["Time"][metric]
                    for inst in INSTRUMENTS
                    if inst in instrument_metrics
                    and target_noise in instrument_metrics[inst]
                    and event_type in instrument_metrics[inst][target_noise]
                    and "Time" in instrument_metrics[inst][target_noise]
                    and not np.isnan(
                        instrument_metrics[inst][target_noise][event_type][metric]
                    )
                    and not np.isnan(
                        instrument_metrics[inst][target_noise]["Time"][metric]
                    )
                ]
            )

            if len(diffs) > 0:
                summary = paired_drift_summary(
                    diffs, f"{event_type} vs Time", metric
                )
                bootstrap_records.append(summary)

    # --- Save machine-readable results ---
    metric_df = pd.DataFrame(metric_records)
    perturbation_df = pd.DataFrame(perturbation_records)
    bootstrap_df = pd.DataFrame(bootstrap_records)

    metric_df.to_csv(RESULTS_DIR / "stability_metrics.csv", index=False)
    perturbation_df.to_csv(
        RESULTS_DIR / "perturbation_audit.csv", index=False
    )
    bootstrap_df.to_csv(
        RESULTS_DIR / "robustness_ranking.csv", index=False
    )

    print(f"Saved stability_metrics.csv ({len(metric_df)} rows)")
    print(f"Saved perturbation_audit.csv ({len(perturbation_df)} rows)")
    print(f"Saved robustness_ranking.csv ({len(bootstrap_df)} rows)")

    # --- Produce visualisations ---
    print("Generating plots ...")

    # Plot 1: drift by noise level (mean across instruments)
    if not metric_df.empty:
        mean_drift = (
            metric_df.groupby(["NoiseLevel", "ChartType"])
            .agg(
                DirectionDrift=("DirectionDrift", "mean"),
                VarianceDrift=("VarianceDrift", "mean"),
                ComplexityDrift=("ComplexityDrift", "mean"),
            )
            .reset_index()
        )
        mean_drift_long = mean_drift.melt(
            id_vars=["NoiseLevel", "ChartType"],
            value_vars=["DirectionDrift", "VarianceDrift", "ComplexityDrift"],
            var_name="Metric",
            value_name="MeanDrift",
        )
        plot_drift_by_noise(
            mean_drift_long,
            PLOTS_DIR / "drift_by_noise_level.png",
        )

    # Plot 2: robustness heatmap at 20% noise
    if not metric_df.empty:
        noise_20 = metric_df[metric_df["NoiseLevel"] == 0.20].copy()
        if not noise_20.empty:
            # Melt metrics into long form, then rank within each
            # instrument/metric (1 = lowest drift = most robust)
            noise_20_long = noise_20.melt(
                id_vars=["Instrument", "ChartType"],
                value_vars=["DirectionDrift", "VarianceDrift", "ComplexityDrift"],
                var_name="Metric",
                value_name="Drift",
            )
            noise_20_long["DriftRank"] = noise_20_long.groupby(
                ["Instrument", "Metric"]
            )["Drift"].rank(method="min")
            plot_robustness_heatmap(
                noise_20_long,
                PLOTS_DIR / "robustness_heatmap_20pct.png",
            )

    # Plot 3: direction stability boxplot at 20% noise
    if not metric_df.empty:
        dir_20 = metric_df[metric_df["NoiseLevel"] == 0.20][
            ["Instrument", "ChartType", "DirectionDrift"]
        ].copy()
        if not dir_20.empty:
            plot_direction_boxplot(
                dir_20, PLOTS_DIR / "direction_stability_boxplot_20pct.png"
            )

    # Plot 4: perturbation quality bar chart
    if not perturbation_df.empty:
        plot_perturbation_quality(
            perturbation_df, PLOTS_DIR / "perturbation_quality.png"
        )

    # Plot 5: variance vs complexity scatter at 20% noise
    if not metric_df.empty:
        scatter_20 = metric_df[metric_df["NoiseLevel"] == 0.20][
            ["Instrument", "ChartType", "VarianceDrift", "ComplexityDrift"]
        ].copy()
        if not scatter_20.empty:
            plot_variance_vs_complexity(
                scatter_20, PLOTS_DIR / "variance_vs_complexity_drift.png"
            )

    print(f"Plots saved to {PLOTS_DIR}")

    # --- Hypothesis support summary ---
    if not bootstrap_df.empty:
        print("\nHypothesis Support Summary (20% noise):")
        for _, row in bootstrap_df.iterrows():
            sign_str = f"{row['SignCountNegative']}/{row['N_Instruments']} instruments lower drift"
            ci_str = f"CI: [{row['CI_Lower']:.4f}, {row['CI_Upper']:.4f}]"
            print(
                f"  {row['Comparison']} | {row['Metric']}: mean={row['MeanDiff']:.4f} | {sign_str} | {ci_str}"
            )

    print("EXP-003 complete.")


if __name__ == "__main__":
    main()
