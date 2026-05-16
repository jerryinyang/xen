"""
Experiment EXP-004: Market Structure Capture Speed & Fidelity
Implements the analysis plan from analysis-plan.md.
"""
import sys
from math import comb
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

DATA_DIR = PROJECT_ROOT / "data"
PLOTS_DIR = PYTHON_ROOT / "experiments/EXP-004/plots"
RESULTS_DIR = PYTHON_ROOT / "experiments/EXP-004/results"
TIMEBAR_COLUMNS = ["OpenTime", "CloseTime", "Open", "High", "Low", "Close"]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_timebar_data(instrument: str) -> pl.DataFrame:
    """Load the chronological non-holdout time-bar slice for an instrument.

    Parameters
    ----------
    instrument : str
        Instrument symbol (e.g. "EURUSD").

    Returns
    -------
    pl.DataFrame
        First 70% of chronologically sorted time-bar data.
    """
    pattern = f"timebars/timebars_{instrument.lower()}_*.parquet"
    matches = sorted(DATA_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(
            f"No time-bar file found for {instrument} matching {pattern}"
        )
    scan = pl.scan_parquet(matches).select(TIMEBAR_COLUMNS).sort("CloseTime")
    total_rows = int(scan.select(pl.len()).collect().item())
    return scan.slice(0, int(total_rows * 0.7)).collect()


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
    rolling_sum = np.cumsum(tr, dtype=float)
    prior_sum = np.concatenate(([0.0], rolling_sum[:-period]))
    atr[period - 1 :] = (rolling_sum[period - 1 :] - prior_sum) / period
    return atr


def detect_swing_reversals(
    time_bars: pl.DataFrame,
    threshold: float,
    atr_period: int = ATR_PERIOD,
    atr: np.ndarray | None = None,
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
    close_times = np.asarray(
        time_bars["CloseTime"].to_numpy(),
        dtype="datetime64[us]",
    )
    n = len(closes)

    if n < atr_period + 2:
        return pl.DataFrame(
            {"ReversalTime": [], "Direction": [], "ATR": []}
        )

    atr_values = compute_atr(time_bars, atr_period) if atr is None else atr
    start_idx = atr_period
    direction = 1 if closes[start_idx] >= closes[start_idx - 1] else -1
    extreme = highs[start_idx] if direction == 1 else lows[start_idx]

    rev_times: list[Any] = []
    rev_dirs: list[int] = []
    rev_atrs: list[float] = []

    for i in range(start_idx + 1, n):
        current_atr = atr_values[i]
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
            "ReversalTime": np.asarray(rev_times, dtype="datetime64[us]"),
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

    times = np.asarray(
        chart_df[time_col].to_numpy(),
        dtype="datetime64[us]",
    )
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
) -> tuple[pl.DataFrame, int, int, int]:
    """Match chart-type signals to real reversals within tolerance.

    A signal matches a real reversal if it occurs after the reversal,
    within the tolerance window, and has the same direction. Each real
    reversal gets at most one matched signal (the first chronologically).
    Additional same-direction signals before the next matched reversal
    count as duplicate signals for split-rate accounting.
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
    tuple[pl.DataFrame, int, int, int]
        Matching table (one row per real reversal), false signal count,
        duplicate signal count, and split-event count.
    """
    if len(real_reversals) == 0:
        empty = pl.DataFrame(
            {
                "ReversalTime": [],
                "SignalTime": [],
                "LatencyMinutes": [],
                "Matched": [],
                "Direction": [],
                "DuplicateSignalsInWindow": [],
            }
        )
        return empty, len(signals), 0, 0

    rev_times = real_reversals["ReversalTime"].to_numpy()
    rev_dirs = real_reversals["Direction"].to_numpy().astype(np.int8)
    sig_times = signals["SignalTime"].to_numpy()
    sig_dirs = signals["Direction"].to_numpy().astype(np.int8)
    tolerance_td = np.timedelta64(tolerance_minutes, "m")
    matched_signal_indices = np.full(len(rev_times), -1, dtype=int)
    duplicate_counts = np.zeros(len(rev_times), dtype=int)
    duplicate_signal_count = 0
    split_event_count = 0

    for direction in (-1, 1):
        rev_indices = np.flatnonzero(rev_dirs == direction)
        sig_indices = np.flatnonzero(sig_dirs == direction)
        if len(rev_indices) == 0:
            continue

        rev_times_dir = rev_times[rev_indices]
        sig_times_dir = sig_times[sig_indices]
        matched_positions = np.full(len(rev_indices), -1, dtype=int)

        signal_ptr = 0
        for rev_pos, rev_time in enumerate(rev_times_dir):
            while signal_ptr < len(sig_times_dir) and sig_times_dir[signal_ptr] < rev_time:
                signal_ptr += 1
            if (
                signal_ptr < len(sig_times_dir)
                and sig_times_dir[signal_ptr] <= rev_time + tolerance_td
            ):
                matched_positions[rev_pos] = signal_ptr
                matched_signal_indices[rev_indices[rev_pos]] = sig_indices[signal_ptr]
                signal_ptr += 1

        matched_rev_positions = np.flatnonzero(matched_positions >= 0)
        for idx, rev_pos in enumerate(matched_rev_positions):
            match_pos = matched_positions[rev_pos]
            next_match_pos = (
                matched_positions[matched_rev_positions[idx + 1]]
                if idx + 1 < len(matched_rev_positions)
                else len(sig_times_dir)
            )
            deadline = rev_times_dir[rev_pos] + tolerance_td
            dup_count = 0
            pos = match_pos + 1
            while pos < next_match_pos and sig_times_dir[pos] <= deadline:
                dup_count += 1
                pos += 1
            if dup_count > 0:
                duplicate_counts[rev_indices[rev_pos]] = dup_count
                duplicate_signal_count += dup_count
                split_event_count += 1

    matched_count = int(np.sum(matched_signal_indices >= 0))
    false_count = int(len(sig_times) - matched_count - duplicate_signal_count)

    records: list[dict[str, Any]] = []
    for r_idx in range(len(rev_times)):
        r_time = rev_times[r_idx]
        r_dir = rev_dirs[r_idx]
        sig_idx = matched_signal_indices[r_idx]

        if sig_idx >= 0:
            s_time = sig_times[sig_idx]
            latency = float((s_time - r_time) / np.timedelta64(1, "m"))
            records.append(
                {
                    "ReversalTime": r_time,
                    "SignalTime": s_time,
                    "LatencyMinutes": latency,
                    "Matched": True,
                    "Direction": r_dir,
                    "DuplicateSignalsInWindow": int(duplicate_counts[r_idx]),
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
                    "DuplicateSignalsInWindow": 0,
                }
            )

    return pl.DataFrame(records), false_count, duplicate_signal_count, split_event_count


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
def compute_metrics(
    matching_df: pl.DataFrame,
    false_count: int,
    duplicate_count: int,
    split_event_count: int,
    total_real: int,
    total_signals: int,
    total_minutes: float,
) -> dict[str, Any]:
    """Compute latency, precision, recall, and split metrics.

    Parameters
    ----------
    matching_df : pl.DataFrame
        Event matching table.
    false_count : int
        Number of false signals.
    duplicate_count : int
        Number of duplicate signals.
    split_event_count : int
        Number of real reversals with more than one same-direction signal.
    total_real : int
        Total reference reversals.
    total_signals : int
        Total chart-type signals.
    total_minutes : float
        Total elapsed minutes in analysis set.

    Returns
    -------
    dict[str, Any]
        Metric dictionary.
    """
    if total_real == 0 or len(matching_df) == 0:
        signal_precision = (
            0.0 if total_signals == 0 else 0.0
        )
        return {
            "Matched": 0,
            "SignalCount": total_signals,
            "False": false_count,
            "Duplicates": duplicate_count,
            "SplitEvents": split_event_count,
            "MedianLatency": np.nan,
            "MeanLatency": np.nan,
            "Precision": signal_precision,
            "MatchPrecision": np.nan,
            "Recall": np.nan,
            "SplitRate": np.nan,
            "DuplicateSignalRate": np.nan if total_signals == 0 else duplicate_count / total_signals,
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

    signal_precision = matched / total_signals if total_signals > 0 else 0.0
    match_precision = (
        matched / (matched + false_count) if (matched + false_count) > 0 else np.nan
    )
    recall = matched / total_real if total_real > 0 else 0.0
    split_rate = split_event_count / total_real if total_real > 0 else 0.0
    duplicate_signal_rate = duplicate_count / total_signals if total_signals > 0 else 0.0

    days = total_minutes / 1440.0
    false_per_day = false_count / days if days > 0 else 0.0
    dup_per_day = duplicate_count / days if days > 0 else 0.0

    return {
        "Matched": matched,
        "SignalCount": total_signals,
        "False": false_count,
        "Duplicates": duplicate_count,
        "SplitEvents": split_event_count,
        "MedianLatency": median_latency,
        "MeanLatency": mean_latency,
        "Precision": signal_precision,
        "MatchPrecision": match_precision,
        "Recall": recall,
        "SplitRate": split_rate,
        "DuplicateSignalRate": duplicate_signal_rate,
        "FalsePerDay": false_per_day,
        "DuplicatePerDay": dup_per_day,
    }


def exact_tail_probability_at_least(successes: int, total: int) -> float:
    """Return the exact upper-tail probability under a fair sign null."""
    if total <= 0:
        return np.nan
    return sum(comb(total, k) for k in range(successes, total + 1)) / (2 ** total)


def nearest_directional_overlap(
    reference: pl.DataFrame,
    candidate: pl.DataFrame,
    tolerance_minutes: int = TOLERANCE_MINUTES,
) -> tuple[int, np.ndarray]:
    """Count same-direction nearest matches within a symmetric tolerance."""
    if len(reference) == 0 or len(candidate) == 0:
        return 0, np.array([], dtype=float)

    ref_times = reference["ReversalTime"].to_numpy()
    ref_dirs = reference["Direction"].to_numpy().astype(np.int8)
    cand_times = candidate["ReversalTime"].to_numpy()
    cand_dirs = candidate["Direction"].to_numpy().astype(np.int8)
    tolerance_td = np.timedelta64(tolerance_minutes, "m")

    matched_count = 0
    deltas: list[np.ndarray] = []
    for direction in (-1, 1):
        ref_dir = ref_times[ref_dirs == direction]
        cand_dir = cand_times[cand_dirs == direction]
        if len(ref_dir) == 0 or len(cand_dir) == 0:
            continue

        insert = np.searchsorted(cand_dir, ref_dir, side="left")
        best_delta = np.full(len(ref_dir), np.timedelta64(tolerance_minutes + 1, "m"))

        prev_mask = insert > 0
        if np.any(prev_mask):
            prev_delta = ref_dir[prev_mask] - cand_dir[insert[prev_mask] - 1]
            best_delta[prev_mask] = np.minimum(best_delta[prev_mask], prev_delta)

        next_mask = insert < len(cand_dir)
        if np.any(next_mask):
            next_delta = cand_dir[insert[next_mask]] - ref_dir[next_mask]
            best_delta[next_mask] = np.minimum(best_delta[next_mask], next_delta)

        matched_mask = best_delta <= tolerance_td
        matched_count += int(np.sum(matched_mask))
        if np.any(matched_mask):
            deltas.append(
                best_delta[matched_mask].astype("timedelta64[m]").astype(float)
            )

    if not deltas:
        return matched_count, np.array([], dtype=float)
    return matched_count, np.concatenate(deltas)


def evaluate_reversal_stability(
    primary: pl.DataFrame,
    alternate: pl.DataFrame,
    tolerance_minutes: int = TOLERANCE_MINUTES,
) -> dict[str, Any]:
    """Measure how stable reversal labels remain under the alternate threshold."""
    primary_matches, primary_deltas = nearest_directional_overlap(
        primary,
        alternate,
        tolerance_minutes=tolerance_minutes,
    )
    alternate_matches, alternate_deltas = nearest_directional_overlap(
        alternate,
        primary,
        tolerance_minutes=tolerance_minutes,
    )
    primary_overlap = (
        primary_matches / len(primary) if len(primary) > 0 else np.nan
    )
    alternate_overlap = (
        alternate_matches / len(alternate) if len(alternate) > 0 else np.nan
    )
    all_deltas = np.concatenate(
        [arr for arr in (primary_deltas, alternate_deltas) if len(arr) > 0]
    ) if (len(primary_deltas) > 0 or len(alternate_deltas) > 0) else np.array([], dtype=float)
    median_shift = float(np.median(all_deltas)) if len(all_deltas) > 0 else np.nan
    return {
        "PrimaryCount": len(primary),
        "AlternateCount": len(alternate),
        "PrimaryOverlapRate": primary_overlap,
        "AlternateOverlapRate": alternate_overlap,
        "MedianConfirmationShiftMinutes": median_shift,
        "StableLabels": (
            min(primary_overlap, alternate_overlap) >= 0.70
            if not np.isnan(primary_overlap) and not np.isnan(alternate_overlap)
            else False
        ),
    }


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
    legacy_bootstrap_path = RESULTS_DIR / "bootstrap_latency_ci.csv"
    if legacy_bootstrap_path.exists():
        legacy_bootstrap_path.unlink()

    print("EXP-004: Market Structure Capture Speed & Fidelity")
    print(f"Instruments: {', '.join(INSTRUMENTS)}")
    print(f"Swing threshold: {SWING_THRESHOLD} (alt: {ALT_SWING_THRESHOLD})")
    print(f"Tolerance window: {TOLERANCE_MINUTES} minutes")
    print(f"Output: {PLOTS_DIR} and {RESULTS_DIR}\n")

    event_matching_records: list[dict[str, Any]] = []
    latency_records: list[dict[str, Any]] = []
    pr_records: list[dict[str, Any]] = []
    latency_long_records: list[dict[str, Any]] = []
    support_records: list[dict[str, Any]] = []
    sensitivity_records: list[dict[str, Any]] = []

    instrument_latencies: dict[str, dict[str, float]] = {}
    instrument_metrics: dict[str, dict[str, dict[str, Any]]] = {}

    # Variables for event timeline plot
    plot_instrument: str | None = None
    plot_real_reversals: pl.DataFrame | None = None
    plot_signals: dict[str, pl.DataFrame] | None = None

    for instrument in INSTRUMENTS:
        try:
            print(f"Processing {instrument} ...")
            analysis_df = load_timebar_data(instrument)
            if len(analysis_df) == 0:
                print(f"  Skipping {instrument}: empty dataset")
                continue

            n_analysis = len(analysis_df)
            print(f"  Analysis rows: {n_analysis:,}")

            time_span = analysis_df["CloseTime"].max() - analysis_df["CloseTime"].min()
            total_minutes = float(time_span.total_seconds() / 60.0)

            # Real-price reversal reference
            atr_values = compute_atr(analysis_df, ATR_PERIOD)
            real_reversals = detect_swing_reversals(
                analysis_df,
                threshold=SWING_THRESHOLD,
                atr=atr_values,
            )
            alt_reversals = detect_swing_reversals(
                analysis_df,
                threshold=ALT_SWING_THRESHOLD,
                atr=atr_values,
            )
            n_real = len(real_reversals)
            print(
                f"  Real reversals: {n_real} (alt threshold: {len(alt_reversals)})"
            )
            sensitivity = evaluate_reversal_stability(
                real_reversals,
                alt_reversals,
                tolerance_minutes=TOLERANCE_MINUTES,
            )
            sensitivity["Instrument"] = instrument
            sensitivity_records.append(sensitivity)

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
                total_signals = len(signals)

                matching_df, false_count, duplicate_count, split_event_count = (
                    match_signals_to_reversals(
                        real_reversals, signals, TOLERANCE_MINUTES
                    )
                )

                metrics = compute_metrics(
                    matching_df,
                    false_count,
                    duplicate_count,
                    split_event_count,
                    n_real,
                    total_signals,
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
                            "DuplicateSignalsInWindow": row[
                                "DuplicateSignalsInWindow"
                            ],
                            "FalseCount": false_count,
                            "DuplicateCount": duplicate_count,
                            "SplitEventCount": split_event_count,
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
                        "MatchPrecision": metrics["MatchPrecision"],
                        "Recall": metrics["Recall"],
                        "SplitRate": metrics["SplitRate"],
                        "DuplicateSignalRate": metrics["DuplicateSignalRate"],
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

    event_types = ["LineBreak", "Renko", "HeikenAshi"]

    # --- Save results ---
    event_matching_df = pd.DataFrame(event_matching_records)
    latency_df = pd.DataFrame(latency_records)
    pr_df = pd.DataFrame(pr_records)
    sensitivity_df = pd.DataFrame(sensitivity_records)

    event_matching_df.to_csv(
        RESULTS_DIR / "event_matching_table.csv", index=False
    )
    latency_df.to_csv(RESULTS_DIR / "latency_summary.csv", index=False)
    pr_df.to_csv(
        RESULTS_DIR / "precision_recall_summary.csv", index=False
    )
    sensitivity_df.to_csv(
        RESULTS_DIR / "sensitivity_summary.csv", index=False
    )

    print(f"\nSaved event_matching_table.csv ({len(event_matching_df)} rows)")
    print(f"Saved latency_summary.csv ({len(latency_df)} rows)")
    print(f"Saved precision_recall_summary.csv ({len(pr_df)} rows)")
    print(f"Saved sensitivity_summary.csv ({len(sensitivity_df)} rows)")

    # --- Sensitivity check ---
    print("\nSensitivity check:")
    for record in sensitivity_records:
        print(
            "  "
            f"{record['Instrument']}: primary={record['PrimaryCount']}, "
            f"alternate={record['AlternateCount']}, "
            f"overlap={record['PrimaryOverlapRate']:.1%}/"
            f"{record['AlternateOverlapRate']:.1%}, "
            f"median_shift={record['MedianConfirmationShiftMinutes']:.1f}m, "
            f"stable={record['StableLabels']}"
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
    total_instruments = len(INSTRUMENTS)
    for event_type in event_types:
        evaluable_count = 0
        faster_count = 0
        precision_ok_count = 0
        combined_count = 0
        for inst in INSTRUMENTS:
            if (
                inst in instrument_latencies
                and "Time" in instrument_latencies[inst]
                and event_type in instrument_latencies[inst]
            ):
                time_lat = instrument_latencies[inst]["Time"]
                evt_lat = instrument_latencies[inst][event_type]
                time_prec = instrument_metrics[inst]["Time"]["Precision"]
                evt_prec = instrument_metrics[inst][event_type]["Precision"]
                if (
                    np.isnan(time_lat)
                    or np.isnan(evt_lat)
                    or np.isnan(time_prec)
                    or np.isnan(evt_prec)
                ):
                    continue

                evaluable_count += 1
                faster = (
                    time_lat > 0 and (time_lat - evt_lat) / time_lat >= 0.30
                )
                precision_ok = evt_prec <= time_prec + 0.10

                if faster:
                    faster_count += 1
                if precision_ok:
                    precision_ok_count += 1
                if faster and precision_ok:
                    combined_count += 1
        support_records.append(
            {
                "ChartType": event_type,
                "EvaluableInstruments": evaluable_count,
                "FasterCount": faster_count,
                "PrecisionOkCount": precision_ok_count,
                "CombinedSupportCount": combined_count,
                "DecisionRuleEvaluable": evaluable_count == total_instruments,
                "FasterRuleMet": (
                    evaluable_count == total_instruments and faster_count >= 3
                ),
                "CombinedRuleMet": (
                    evaluable_count == total_instruments and combined_count >= 3
                ),
                "FasterTailProbability": exact_tail_probability_at_least(
                    faster_count,
                    evaluable_count,
                ),
                "CombinedTailProbability": exact_tail_probability_at_least(
                    combined_count,
                    evaluable_count,
                ),
            }
        )
        print(
            f"  {event_type}: evaluable={evaluable_count}/{total_instruments}, "
            f">=30% faster on {faster_count}/{evaluable_count}, "
            f"precision within +10pp on {precision_ok_count}/{evaluable_count}, "
            f"combined support on {combined_count}/{evaluable_count}, "
            f"combined tail p={exact_tail_probability_at_least(combined_count, evaluable_count):.4f}"
        )

    pd.DataFrame(support_records).to_csv(
        RESULTS_DIR / "support_summary.csv",
        index=False,
    )

    print("EXP-004 complete.")


if __name__ == "__main__":
    main()
