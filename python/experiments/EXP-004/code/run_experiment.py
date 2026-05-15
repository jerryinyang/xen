"""
Experiment EXP-004: Market Structure Capture Speed & Fidelity
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

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
INSTRUMENTS = ["EURUSD", "XAUUSD", "BTCUSD", "USTEC"]

CHART_CONFIG: dict[str, dict[str, Any]] = {
    "Time": {
        "generator": None,
        "params": {},
        "time_col": "CloseTime",
        "dir_col": None,
    },
    "LineBreak": {
        "generator": "linebreak",
        "params": {"level": 3},
        "time_col": "SourceCloseTime",
        "dir_col": "Direction",
    },
    "Renko": {
        "generator": "renko",
        "params": {"atr_period": 14},
        "time_col": "SourceCloseTime",
        "dir_col": "Direction",
    },
    "HeikenAshi": {
        "generator": "heiken_ashi",
        "params": {},
        "time_col": "CloseTime",
        "dir_col": "Direction",
    },
}

SWING_THRESHOLD = 1.5
ALT_SWING_THRESHOLD = 2.0
ATR_PERIOD = 14
TOLERANCE_MINUTES = 120

BOOTSTRAP_SEED = 42
N_BOOTSTRAP = 10_000

DATA_DIR = PROJECT_ROOT / "data"
PLOTS_DIR = PYTHON_ROOT / "experiments/EXP-004/plots"
RESULTS_DIR = PYTHON_ROOT / "experiments/EXP-004/results"


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
# ATR and swing reversal detector
# ---------------------------------------------------------------------------
def compute_atr(
    time_bars: pl.DataFrame,
    period: int = ATR_PERIOD,
) -> np.ndarray:
    """Compute simple rolling average True Range.

    Parameters
    ----------
    time_bars : pl.DataFrame
        1-minute time bars with ``High``, ``Low``, ``Close``.
    period : int
        Rolling window length.

    Returns
    -------
    np.ndarray
        ATR array (NaN for first ``period - 1`` values).
    """
    closes = time_bars["Close"].to_numpy()
    highs = time_bars["High"].to_numpy()
    lows = time_bars["Low"].to_numpy()
    n = len(closes)

    if n == 0:
        return np.array([])

    prev_closes = np.roll(closes, 1)
    prev_closes[0] = closes[0]
    tr = np.maximum(
        highs - lows,
        np.maximum(
            np.abs(highs - prev_closes),
            np.abs(lows - prev_closes),
        ),
    )
    tr[0] = highs[0] - lows[0]

    atr = np.full(n, np.nan)
    for i in range(period - 1, n):
        atr[i] = float(np.mean(tr[i - period + 1 : i + 1]))
    return atr


def detect_swing_reversals(
    time_bars: pl.DataFrame,
    threshold: float,
    atr_period: int = ATR_PERIOD,
) -> pl.DataFrame:
    """Detect ATR-scaled swing reversals on 1-minute time bars.

    A reversal is confirmed when the close moves at least
    ``threshold * ATR`` against the current trend's extreme
    (highest high in uptrend, lowest low in downtrend).

    Parameters
    ----------
    time_bars : pl.DataFrame
        1-minute time bars.
    threshold : float
        ATR multiplier for reversal confirmation.
    atr_period : int
        ATR look-back period.

    Returns
    -------
    pl.DataFrame
        Reversal table with ``ReversalTime``, ``Direction``, ``ATR``.
    """
    closes = time_bars["Close"].to_numpy()
    highs = time_bars["High"].to_numpy()
    lows = time_bars["Low"].to_numpy()
    close_times = time_bars["CloseTime"].to_numpy()
    n = len(closes)

    if n < atr_period + 2:
        return pl.DataFrame(
            {"ReversalTime": [], "Direction": [], "ATR": []}
        )

    atr = compute_atr(time_bars, atr_period)
    start_idx = atr_period
    direction = 1 if closes[start_idx] >= closes[start_idx - 1] else -1
    extreme = highs[start_idx] if direction == 1 else lows[start_idx]

    rev_times: list[Any] = []
    rev_dirs: list[int] = []
    rev_atrs: list[float] = []

    for i in range(start_idx + 1, n):
        current_atr = atr[i]
        if np.isnan(current_atr) or current_atr <= 0:
            continue

        if direction == 1:
            if highs[i] > extreme:
                extreme = highs[i]
            if closes[i] <= extreme - threshold * current_atr:
                rev_times.append(close_times[i])
                rev_dirs.append(-1)
                rev_atrs.append(float(current_atr))
                direction = -1
                extreme = lows[i]
        else:
            if lows[i] < extreme:
                extreme = lows[i]
            if closes[i] >= extreme + threshold * current_atr:
                rev_times.append(close_times[i])
                rev_dirs.append(1)
                rev_atrs.append(float(current_atr))
                direction = 1
                extreme = highs[i]

    return pl.DataFrame(
        {
            "ReversalTime": rev_times,
            "Direction": rev_dirs,
            "ATR": rev_atrs,
        }
    )


# ---------------------------------------------------------------------------
# Chart generation and signal extraction
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
        Chart type key from ``CHART_CONFIG``.

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


def extract_direction_changes(
    chart_df: pl.DataFrame,
    time_col: str,
    dir_col: str | None = None,
) -> pl.DataFrame:
    """Extract direction-change events from chart-type bars.

    Parameters
    ----------
    chart_df : pl.DataFrame
        Chart-type bars.
    time_col : str
        Timestamp column for event alignment.
    dir_col : str, optional
        Pre-computed direction column. If None, derives from
        ``Close >= Open``.

    Returns
    -------
    pl.DataFrame
        Signal table with ``SignalTime`` and ``Direction``.
    """
    if len(chart_df) < 2:
        return pl.DataFrame({"SignalTime": [], "Direction": []})

    if dir_col is not None:
        directions = chart_df[dir_col].to_numpy()
    else:
        directions = np.where(
            chart_df["Close"].to_numpy() >= chart_df["Open"].to_numpy(),
            1,
            -1,
        )

    times = chart_df[time_col].to_numpy()
    change_mask = directions[1:] != directions[:-1]
    change_indices = np.where(change_mask)[0] + 1

    return pl.DataFrame(
        {
            "SignalTime": times[change_indices],
            "Direction": directions[change_indices],
        }
    )


# ---------------------------------------------------------------------------
# Event matching
# ---------------------------------------------------------------------------
def match_signals_to_reversals(
    real_reversals: pl.DataFrame,
    signals: pl.DataFrame,
    tolerance_minutes: int = TOLERANCE_MINUTES,
) -> tuple[pl.DataFrame, int, int]:
    """Match chart-type signals to real reversals within tolerance.

    A signal matches a real reversal if it occurs after the reversal,
    within the tolerance window, and has the same direction. Each real
    reversal gets at most one matched signal (the first chronologically).
    Additional signals within the tolerance window are duplicates.
    Signals not matching any real reversal are false signals.

    Parameters
    ----------
    real_reversals : pl.DataFrame
        Reference reversal table.
    signals : pl.DataFrame
        Chart-type signal table.
    tolerance_minutes : int
        Maximum forward-looking window for a valid match.

    Returns
    -------
    tuple[pl.DataFrame, int, int]
        Matching table (one row per real reversal), false signal count,
        and duplicate signal count.
    """
    if len(real_reversals) == 0 or len(signals) == 0:
        empty = pl.DataFrame(
            {
                "ReversalTime": [],
                "SignalTime": [],
                "LatencyMinutes": [],
                "Matched": [],
                "Direction": [],
            }
        )
        return empty, 0, 0 if len(signals) == 0 else len(signals)

    rev_times = real_reversals["ReversalTime"].to_numpy()
    rev_dirs = real_reversals["Direction"].to_numpy()
    sig_times = signals["SignalTime"].to_numpy()
    sig_dirs = signals["Direction"].to_numpy()

    matched = np.zeros(len(signals), dtype=bool)
    matched_rev_idx = np.full(len(signals), -1, dtype=int)
    tolerance_td = np.timedelta64(tolerance_minutes, "m")

    for r_idx in range(len(rev_times)):
        r_time = rev_times[r_idx]
        r_dir = rev_dirs[r_idx]
        deadline = r_time + tolerance_td

        candidates = np.where(
            (sig_times >= r_time)
            & (sig_times <= deadline)
            & (sig_dirs == r_dir)
            & (~matched)
        )[0]

        if len(candidates) > 0:
            first = candidates[0]
            matched[first] = True
            matched_rev_idx[first] = r_idx

    records: list[dict[str, Any]] = []
    for r_idx in range(len(rev_times)):
        r_time = rev_times[r_idx]
        r_dir = rev_dirs[r_idx]
        sig_idx_arr = np.where(matched_rev_idx == r_idx)[0]

        if len(sig_idx_arr) > 0:
            s_time = sig_times[sig_idx_arr[0]]
            latency = float((s_time - r_time) / np.timedelta64(1, "m"))
            records.append(
                {
                    "ReversalTime": r_time,
                    "SignalTime": s_time,
                    "LatencyMinutes": latency,
                    "Matched": True,
                    "Direction": r_dir,
                }
            )
        else:
            records.append(
                {
                    "ReversalTime": r_time,
                    "SignalTime": None,
                    "LatencyMinutes": np.nan,
                    "Matched": False,
                    "Direction": r_dir,
                }
            )

    unmatched_indices = np.where(~matched)[0]
    false_count = 0
    duplicate_count = 0

    for s_idx in unmatched_indices:
        s_time = sig_times[s_idx]
        s_dir = sig_dirs[s_idx]
        is_duplicate = False

        for r_idx in range(len(rev_times)):
            r_time = rev_times[r_idx]
            r_dir = rev_dirs[r_idx]
            deadline = r_time + tolerance_td
            if (
                s_time >= r_time
                and s_time <= deadline
                and s_dir == r_dir
            ):
                is_duplicate = True
                break

        if is_duplicate:
            duplicate_count += 1
        else:
            false_count += 1

    return pl.DataFrame(records), false_count, duplicate_count


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
def compute_metrics(
    matching_df: pl.DataFrame,
    false_count: int,
    duplicate_count: int,
    total_real: int,
    total_minutes: float,
) -> dict[str, Any]:
    """Compute latency, precision, recall, and split rate.

    Parameters
    ----------
    matching_df : pl.DataFrame
        Event matching table.
    false_count : int
        Number of false signals.
    duplicate_count : int
        Number of duplicate signals.
    total_real : int
        Total reference reversals.
    total_minutes : float
        Total elapsed minutes in analysis set.

    Returns
    -------
    dict[str, Any]
        Metric dictionary.
    """
    if total_real == 0 or len(matching_df) == 0:
        return {
            "Matched": 0,
            "False": false_count,
            "Duplicates": duplicate_count,
            "MedianLatency": np.nan,
            "MeanLatency": np.nan,
            "Precision": np.nan,
            "Recall": np.nan,
            "SplitRate": np.nan,
            "FalsePerDay": np.nan,
            "DuplicatePerDay": np.nan,
        }

    matched = int(matching_df["Matched"].sum())
    latencies = (
        matching_df.filter(pl.col("Matched"))["LatencyMinutes"]
        .drop_nulls()
        .to_numpy()
    )

    median_latency = float(np.median(latencies)) if len(latencies) > 0 else np.nan
    mean_latency = float(np.mean(latencies)) if len(latencies) > 0 else np.nan

    precision = (
        matched / (matched + false_count) if (matched + false_count) > 0 else 0.0
    )
    recall = matched / total_real if total_real > 0 else 0.0
    split_rate = duplicate_count / matched if matched > 0 else 0.0

    days = total_minutes / 1440.0
    false_per_day = false_count / days if days > 0 else 0.0
    dup_per_day = duplicate_count / days if days > 0 else 0.0

    return {
        "Matched": matched,
        "False": false_count,
        "Duplicates": duplicate_count,
        "MedianLatency": median_latency,
        "MeanLatency": mean_latency,
        "Precision": precision,
        "Recall": recall,
        "SplitRate": split_rate,
        "FalsePerDay": false_per_day,
        "DuplicatePerDay": dup_per_day,
    }


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
def bootstrap_paired_latency_ci(
    instrument_latencies: dict[str, dict[str, float]],
    chart_type: str,
    baseline: str = "Time",
    n_bootstrap: int = N_BOOTSTRAP,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[float, float, float]:
    """Bootstrap percentile CI for mean paired latency difference.

    Parameters
    ----------
    instrument_latencies : dict
        ``{instrument: {chart_type: median_latency}}``.
    chart_type : str
        Chart type to compare against baseline.
    baseline : str
        Baseline chart type (default "Time").
    n_bootstrap : int
        Number of bootstrap resamples.
    seed : int
        Random seed.

    Returns
    -------
    tuple[float, float, float]
        (mean_diff, ci_lower, ci_upper).
    """
    diffs = [
        latencies[baseline] - latencies[chart_type]
        for inst, latencies in instrument_latencies.items()
        if baseline in latencies
        and chart_type in latencies
        and not np.isnan(latencies[baseline])
        and not np.isnan(latencies[chart_type])
    ]

    if len(diffs) == 0:
        return (np.nan, np.nan, np.nan)

    diffs_arr = np.array(diffs)
    rng = np.random.default_rng(seed)
    n = len(diffs_arr)
    boot_means = []
    for _ in range(n_bootstrap):
        sample = rng.choice(diffs_arr, size=n, replace=True)
        boot_means.append(np.mean(sample))

    boot_means_arr = np.array(boot_means)
    mean_diff = float(np.mean(diffs_arr))
    ci_lo = float(np.quantile(boot_means_arr, 0.025))
    ci_hi = float(np.quantile(boot_means_arr, 0.975))
    return (mean_diff, ci_lo, ci_hi)


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------
def plot_event_timeline(
    real_reversals: pl.DataFrame,
    signals_by_chart: dict[str, pl.DataFrame],
    instrument: str,
    save_path: Path,
) -> plt.Figure:
    """Event timeline for one representative reversal cluster.

    Parameters
    ----------
    real_reversals : pl.DataFrame
        Subset of real reversals in the chosen window.
    signals_by_chart : dict
        Mapping chart-type name to signal DataFrame in the window.
    instrument : str
        Instrument label.
    save_path : Path
        Output path.

    Returns
    -------
    plt.Figure
        The figure object.
    """
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(14, 6))

    rev_times = real_reversals["ReversalTime"].to_numpy()
    rev_dirs = real_reversals["Direction"].to_numpy()

    for t, d in zip(rev_times, rev_dirs):
        color = "green" if d == 1 else "red"
        ax.axvline(t, color=color, linestyle="-", alpha=0.5, linewidth=2)

    y_offsets = {"Time": 1, "HeikenAshi": 2, "LineBreak": 3, "Renko": 4}
    markers = {"Time": "o", "HeikenAshi": "s", "LineBreak": "^", "Renko": "D"}

    for chart_name, sig_df in signals_by_chart.items():
        if len(sig_df) == 0:
            continue
        sig_times = sig_df["SignalTime"].to_numpy()
        sig_dirs = sig_df["Direction"].to_numpy()
        y = y_offsets.get(chart_name, 0)
        colors = ["green" if d == 1 else "red" for d in sig_dirs]
        ax.scatter(
            sig_times,
            [y] * len(sig_times),
            c=colors,
            marker=markers.get(chart_name, "o"),
            s=60,
            label=chart_name,
            alpha=0.7,
            edgecolors="black",
            linewidth=0.5,
        )

    ax.set_title(
        f"Event Timeline: {instrument} (n_real={len(rev_times)})",
        fontsize=12,
    )
    ax.set_xlabel("Time")
    ax.set_ylabel("Chart Type")
    ax.set_yticks(list(y_offsets.values()))
    ax.set_yticklabels(list(y_offsets.keys()))
    ax.legend(title="Chart Type", loc="upper right")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


def plot_latency_boxplot(
    df: pd.DataFrame,
    save_path: Path,
) -> plt.Figure:
    """Box plot of detection latency by chart type, faceted by instrument.

    Parameters
    ----------
    df : pd.DataFrame
        Long-format with ``Instrument``, ``ChartType``, ``LatencyMinutes``.
    save_path : Path
        Output path.

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
        y="LatencyMinutes",
        col="Instrument",
        col_wrap=2,
        height=4,
        aspect=1.2,
        sharey=False,
    )
    g.set_axis_labels("Chart Type", "Latency (minutes)")
    g.set_titles("{col_name}")
    g.fig.suptitle(
        "Detection Latency by Chart Type", y=1.02, fontsize=12
    )
    g.fig.tight_layout()
    g.fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(g.fig)
    return g.fig


def plot_precision_recall_scatter(
    df: pd.DataFrame,
    save_path: Path,
) -> plt.Figure:
    """Precision-recall scatter by chart type and instrument.

    Parameters
    ----------
    df : pd.DataFrame
        Summary with ``Instrument``, ``ChartType``, ``Precision``, ``Recall``.
    save_path : Path
        Output path.

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
            subset["Precision"],
            subset["Recall"],
            label=chart_type,
            s=80,
            alpha=0.7,
        )
        for _, row in subset.iterrows():
            ax.annotate(
                row["Instrument"],
                (row["Precision"], row["Recall"]),
                textcoords="offset points",
                xytext=(5, 5),
                fontsize=7,
            )

    ax.set_title("Precision vs Recall by Chart Type")
    ax.set_xlabel("Precision")
    ax.set_ylabel("Recall")
    ax.legend(title="Chart Type")
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


def plot_split_rate_barchart(
    df: pd.DataFrame,
    save_path: Path,
) -> plt.Figure:
    """Bar chart of split rate by chart type and instrument.

    Parameters
    ----------
    df : pd.DataFrame
        Summary with ``Instrument``, ``ChartType``, ``SplitRate``.
    save_path : Path
        Output path.

    Returns
    -------
    plt.Figure
        The figure object.
    """
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(
        data=df,
        x="Instrument",
        y="SplitRate",
        hue="ChartType",
        ax=ax,
    )
    ax.set_title("Split Rate by Instrument and Chart Type")
    ax.set_ylabel("Split Rate (duplicates / matched)")
    ax.set_xlabel("Instrument")
    ax.legend(title="Chart Type", loc="upper right")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


def plot_latency_precision_heatmap(
    df: pd.DataFrame,
    save_path: Path,
) -> plt.Figure:
    """Heatmap of latency improvement versus precision change.

    Parameters
    ----------
    df : pd.DataFrame
        With ``Instrument``, ``ChartType``, ``LatencyImprovement``,
        ``PrecisionChange``.
    save_path : Path
        Output path.

    Returns
    -------
    plt.Figure
        The figure object.
    """
    sns.set_theme(style="white")
    pivot = df.pivot(
        index="Instrument",
        columns="ChartType",
        values="LatencyImprovement",
    )

    annot_text = pivot.copy().astype(object)
    for i, inst in enumerate(pivot.index):
        for j, ct in enumerate(pivot.columns):
            li = pivot.loc[inst, ct]
            pc_row = df[
                (df["Instrument"] == inst) & (df["ChartType"] == ct)
            ]
            if not pc_row.empty:
                pc = pc_row["PrecisionChange"].values[0]
                annot_text.loc[inst, ct] = (
                    f"{li:.1%}\nΔP={pc:+.1f}pp"
                )
            else:
                annot_text.loc[inst, ct] = ""

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.heatmap(
        pivot,
        annot=annot_text.values,
        fmt="",
        cmap="RdYlGn",
        center=0,
        ax=ax,
        cbar_kws={"label": "Latency Improvement vs Time"},
    )
    ax.set_title("Latency Improvement vs Time (ΔP annotated)")
    ax.set_ylabel("Instrument")
    ax.set_xlabel("Chart Type")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def main() -> None:
    """Run the full EXP-004 analysis pipeline."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("EXP-004: Market Structure Capture Speed & Fidelity")
    print(f"Instruments: {', '.join(INSTRUMENTS)}")
    print(f"Swing threshold: {SWING_THRESHOLD} (alt: {ALT_SWING_THRESHOLD})")
    print(f"Tolerance window: {TOLERANCE_MINUTES} minutes")
    print(f"Output: {PLOTS_DIR} and {RESULTS_DIR}\n")

    event_matching_records: list[dict[str, Any]] = []
    latency_records: list[dict[str, Any]] = []
    pr_records: list[dict[str, Any]] = []
    latency_long_records: list[dict[str, Any]] = []

    instrument_latencies: dict[str, dict[str, float]] = {}
    instrument_metrics: dict[str, dict[str, dict[str, Any]]] = {}
    sensitivity_counts: dict[str, dict[str, int]] = {}

    # Variables for event timeline plot
    plot_instrument: str | None = None
    plot_real_reversals: pl.DataFrame | None = None
    plot_signals: dict[str, pl.DataFrame] | None = None

    for instrument in INSTRUMENTS:
        try:
            print(f"Processing {instrument} ...")
            full_df = load_timebar_data(instrument)
            if len(full_df) == 0:
                print(f"  Skipping {instrument}: empty dataset")
                continue

            analysis_df = full_df.slice(0, int(len(full_df) * 0.7))
            n_analysis = len(analysis_df)
            print(f"  Analysis rows: {n_analysis:,}")

            time_span = analysis_df["CloseTime"].max() - analysis_df["CloseTime"].min()
            total_minutes = float(time_span.total_seconds() / 60.0)

            # Real-price reversal reference
            real_reversals = detect_swing_reversals(
                analysis_df, threshold=SWING_THRESHOLD
            )
            alt_reversals = detect_swing_reversals(
                analysis_df, threshold=ALT_SWING_THRESHOLD
            )
            n_real = len(real_reversals)
            print(
                f"  Real reversals: {n_real} (alt threshold: {len(alt_reversals)})"
            )
            sensitivity_counts[instrument] = {
                "Primary": n_real,
                "Alternate": len(alt_reversals),
            }

            instrument_latencies[instrument] = {}
            instrument_metrics[instrument] = {}

            if n_real == 0:
                print(f"  Skipping {instrument}: no reversals detected")
                continue

            signals_by_chart: dict[str, pl.DataFrame] = {}

            for chart_name, config in CHART_CONFIG.items():
                chart_df = generate_chart(analysis_df, chart_name)
                signals = extract_direction_changes(
                    chart_df,
                    config["time_col"],
                    config.get("dir_col"),
                )
                signals_by_chart[chart_name] = signals

                matching_df, false_count, duplicate_count = (
                    match_signals_to_reversals(
                        real_reversals, signals, TOLERANCE_MINUTES
                    )
                )

                metrics = compute_metrics(
                    matching_df,
                    false_count,
                    duplicate_count,
                    n_real,
                    total_minutes,
                )
                instrument_metrics[instrument][chart_name] = metrics
                instrument_latencies[instrument][chart_name] = metrics[
                    "MedianLatency"
                ]

                # Event matching table records
                for row in matching_df.to_dicts():
                    event_matching_records.append(
                        {
                            "Instrument": instrument,
                            "ChartType": chart_name,
                            "ReversalTime": row["ReversalTime"],
                            "SignalTime": row["SignalTime"],
                            "LatencyMinutes": row["LatencyMinutes"],
                            "Matched": row["Matched"],
                            "Direction": row["Direction"],
                            "FalseCount": false_count,
                            "DuplicateCount": duplicate_count,
                        }
                    )

                # Latency summary
                latency_records.append(
                    {
                        "Instrument": instrument,
                        "ChartType": chart_name,
                        **metrics,
                    }
                )

                # Precision-recall summary
                pr_records.append(
                    {
                        "Instrument": instrument,
                        "ChartType": chart_name,
                        "Precision": metrics["Precision"],
                        "Recall": metrics["Recall"],
                        "SplitRate": metrics["SplitRate"],
                        "FalsePerDay": metrics["FalsePerDay"],
                        "DuplicatePerDay": metrics["DuplicatePerDay"],
                    }
                )

                # Long-format latencies for boxplot
                for row in matching_df.filter(pl.col("Matched")).to_dicts():
                    latency_long_records.append(
                        {
                            "Instrument": instrument,
                            "ChartType": chart_name,
                            "LatencyMinutes": row["LatencyMinutes"],
                        }
                    )

            # Select representative cluster for timeline plot
            if plot_instrument is None and n_real >= 3:
                rev_times = real_reversals["ReversalTime"].to_numpy()
                for i in range(n_real - 2):
                    span_hours = (
                        rev_times[i + 2] - rev_times[i]
                    ).astype("timedelta64[h]").astype(float)
                    if span_hours <= 48:
                        window_start = rev_times[i]
                        window_end = rev_times[i + 2] + np.timedelta64(
                            2, "h"
                        )
                        plot_instrument = instrument
                        plot_real_reversals = real_reversals.filter(
                            (pl.col("ReversalTime") >= window_start)
                            & (pl.col("ReversalTime") <= window_end)
                        )
                        plot_signals = {}
                        for cn, sig_df in signals_by_chart.items():
                            plot_signals[cn] = sig_df.filter(
                                (pl.col("SignalTime") >= window_start)
                                & (pl.col("SignalTime") <= window_end)
                            )
                        break

        except Exception as exc:
            print(f"  Warning: Failed to process {instrument}: {exc}")
            continue

    # --- Bootstrap latency CIs (event types vs Time) ---
    bootstrap_records: list[dict[str, Any]] = []
    event_types = ["LineBreak", "Renko", "HeikenAshi"]
    for event_type in event_types:
        mean_diff, ci_lo, ci_hi = bootstrap_paired_latency_ci(
            instrument_latencies, event_type, baseline="Time"
        )
        bootstrap_records.append(
            {
                "Comparison": f"{event_type} vs Time",
                "MeanDiff": mean_diff,
                "CI_Lower": ci_lo,
                "CI_Upper": ci_hi,
                "CI_Excludes_Zero": (ci_lo > 0) or (ci_hi < 0),
                "N_Instruments": sum(
                    1
                    for inst in instrument_latencies
                    if "Time" in instrument_latencies[inst]
                    and event_type in instrument_latencies[inst]
                    and not np.isnan(
                        instrument_latencies[inst]["Time"]
                    )
                    and not np.isnan(
                        instrument_latencies[inst][event_type]
                    )
                ),
            }
        )

    # --- Save results ---
    event_matching_df = pd.DataFrame(event_matching_records)
    latency_df = pd.DataFrame(latency_records)
    pr_df = pd.DataFrame(pr_records)
    bootstrap_df = pd.DataFrame(bootstrap_records)

    event_matching_df.to_csv(
        RESULTS_DIR / "event_matching_table.csv", index=False
    )
    latency_df.to_csv(RESULTS_DIR / "latency_summary.csv", index=False)
    pr_df.to_csv(
        RESULTS_DIR / "precision_recall_summary.csv", index=False
    )
    bootstrap_df.to_csv(
        RESULTS_DIR / "bootstrap_latency_ci.csv", index=False
    )

    print(f"\nSaved event_matching_table.csv ({len(event_matching_df)} rows)")
    print(f"Saved latency_summary.csv ({len(latency_df)} rows)")
    print(f"Saved precision_recall_summary.csv ({len(pr_df)} rows)")
    print(f"Saved bootstrap_latency_ci.csv ({len(bootstrap_df)} rows)")

    # --- Sensitivity check ---
    print("\nSensitivity check (reversal counts):")
    for inst, counts in sensitivity_counts.items():
        print(
            f"  {inst}: primary={counts['Primary']}, "
            f"alternate={counts['Alternate']}"
        )

    # --- Produce visualisations ---
    print("\nGenerating plots ...")

    if plot_instrument is not None and plot_real_reversals is not None:
        plot_event_timeline(
            plot_real_reversals,
            plot_signals or {},
            plot_instrument,
            PLOTS_DIR / "event_timeline.png",
        )

    if not latency_long_records:
        latency_long_df = pd.DataFrame()
    else:
        latency_long_df = pd.DataFrame(latency_long_records)
    if not latency_long_df.empty:
        plot_latency_boxplot(
            latency_long_df, PLOTS_DIR / "latency_boxplot.png"
        )

    if not pr_df.empty:
        plot_precision_recall_scatter(
            pr_df, PLOTS_DIR / "precision_recall_scatter.png"
        )
        plot_split_rate_barchart(
            pr_df, PLOTS_DIR / "split_rate_barchart.png"
        )

    # Heatmap data: event chart types vs Time baseline
    if not latency_df.empty and not pr_df.empty:
        heatmap_records: list[dict[str, Any]] = []
        for instrument in INSTRUMENTS:
            if instrument not in instrument_metrics:
                continue
            time_latency = instrument_metrics[instrument].get("Time", {}).get(
                "MedianLatency", np.nan
            )
            time_precision = instrument_metrics[instrument].get("Time", {}).get(
                "Precision", np.nan
            )
            if np.isnan(time_latency) or time_latency == 0:
                continue
            for chart_name in event_types:
                if chart_name not in instrument_metrics[instrument]:
                    continue
                chart_latency = instrument_metrics[instrument][chart_name][
                    "MedianLatency"
                ]
                chart_precision = instrument_metrics[instrument][chart_name][
                    "Precision"
                ]
                if np.isnan(chart_latency):
                    continue
                improvement = (time_latency - chart_latency) / time_latency
                precision_change = chart_precision - time_precision
                heatmap_records.append(
                    {
                        "Instrument": instrument,
                        "ChartType": chart_name,
                        "LatencyImprovement": improvement,
                        "PrecisionChange": precision_change,
                    }
                )
        if heatmap_records:
            heatmap_df = pd.DataFrame(heatmap_records)
            plot_latency_precision_heatmap(
                heatmap_df, PLOTS_DIR / "latency_precision_heatmap.png"
            )

    print(f"Plots saved to {PLOTS_DIR}")

    # --- Hypothesis support summary ---
    print("\nHypothesis Support Summary:")
    for event_type in event_types:
        faster_count = 0
        precision_ok_count = 0
        for inst in INSTRUMENTS:
            if (
                inst in instrument_latencies
                and "Time" in instrument_latencies[inst]
                and event_type in instrument_latencies[inst]
            ):
                time_lat = instrument_latencies[inst]["Time"]
                evt_lat = instrument_latencies[inst][event_type]
                if not np.isnan(time_lat) and not np.isnan(evt_lat):
                    if time_lat > 0 and (time_lat - evt_lat) / time_lat >= 0.30:
                        faster_count += 1
                    time_prec = instrument_metrics[inst]["Time"]["Precision"]
                    evt_prec = instrument_metrics[inst][event_type]["Precision"]
                    if not np.isnan(time_prec) and not np.isnan(evt_prec):
                        if evt_prec <= time_prec + 0.10:
                            precision_ok_count += 1
        print(
            f"  {event_type}: >=30% faster on {faster_count}/4 instruments, "
            f"precision within +10pp on {precision_ok_count}/4 instruments"
        )

    print("EXP-004 complete.")


if __name__ == "__main__":
    main()
