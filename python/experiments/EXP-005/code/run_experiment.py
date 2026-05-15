"""Experiment EXP-005: Cross-Chart-Type Alignment & Regime Correspondence.

Implements the analysis plan from analysis-plan.md.
"""

import sys
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[3]
PROJECT_ROOT = PYTHON_ROOT.parent
SRC_DIR = PYTHON_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

import json
from datetime import timedelta
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl
import seaborn as sns
from matplotlib.ticker import PercentFormatter

from heiken_ashi_generator import generate_heiken_ashi
from linebreak_generator import generate_linebreak
from renko_generator import generate_renko
from time_alignment import normalize_timestamp_columns

DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PYTHON_ROOT / "experiments/EXP-005"
PLOTS_DIR = EXP_DIR / "plots"
RESULTS_DIR = EXP_DIR / "results"

INSTRUMENTS = ["EURUSD", "XAUUSD", "BTCUSD", "USTEC"]
CHART_TYPES = ["timebars", "linebreak", "renko", "heiken_ashi"]
TOLERANCE_BASE = "5m"
TOLERANCE_WIDE = "15m"
REGIME_WINDOW = 60
BOOTSTRAP_ITERATIONS = 10_000
BOOTSTRAP_SEED = 42


def find_latest_timebars(instrument: str) -> Path:
    """Return the latest Parquet file for an instrument."""
    pattern = f"timebars/timebars_{instrument.lower()}_*.parquet"
    paths = sorted(DATA_DIR.glob(pattern))
    if not paths:
        raise FileNotFoundError(f"No time-bar files found for {instrument}")
    return paths[-1]


def load_time_bars(instrument: str) -> pl.DataFrame:
    """Load and chronologically scope time bars for an instrument."""
    path = find_latest_timebars(instrument)
    df = pl.read_parquet(path).sort("CloseTime")
    cutoff = int(len(df) * 0.7)
    return df.slice(0, cutoff)


def generate_chart_types(time_bars: pl.DataFrame) -> dict[str, pl.DataFrame]:
    """Generate all chart types from time bars."""
    return {
        "timebars": time_bars,
        "linebreak": generate_linebreak(time_bars, level=3),
        "renko": generate_renko(time_bars, atr_period=14),
        "heiken_ashi": generate_heiken_ashi(time_bars),
    }


def build_direction_table(
    df: pl.DataFrame,
    chart_type: str,
    instrument: str,
) -> pl.DataFrame:
    """Build a direction table for a chart type.

    Parameters
    ----------
    df : pl.DataFrame
        Chart-type DataFrame.
    chart_type : str
        One of the CHART_TYPES keys.
    instrument : str
        Instrument symbol.

    Returns
    -------
    pl.DataFrame
        Columns: timestamp, direction, instrument.
    """
    if chart_type == "timebars":
        ts_col = "CloseTime"
        direction = pl.when(pl.col("Close") >= pl.col("Open")).then(1).otherwise(-1)
    elif chart_type == "heiken_ashi":
        ts_col = "CloseTime"
        direction = pl.col("Direction")
    elif chart_type in ("linebreak", "renko"):
        ts_col = "SourceCloseTime"
        direction = pl.col("Direction")
    else:
        raise ValueError(f"Unknown chart type: {chart_type}")

    out = df.select(
        pl.col(ts_col).alias("timestamp"),
        direction.alias("direction"),
        pl.lit(instrument).alias("instrument"),
    ).with_columns(pl.col("direction").cast(pl.Int8))
    return normalize_timestamp_columns(out, ["timestamp"])


def compute_regime_labels(
    time_bars: pl.DataFrame,
    window: int = REGIME_WINDOW,
) -> pl.DataFrame:
    """Compute low/medium/high volatility regime labels from time bars.

    Parameters
    ----------
    time_bars : pl.DataFrame
        Time-bar DataFrame with Close prices.
    window : int
        Rolling window size in bars for realised volatility.

    Returns
    -------
    pl.DataFrame
        Columns: CloseTime, regime.
    """
    df = time_bars.with_columns(
        (pl.col("Close").log() - pl.col("Close").shift(1).log())
        .alias("log_ret")
    ).with_columns(
        pl.col("log_ret")
        .rolling_std(window_size=window, min_periods=window)
        .alias("vol")
    )
    vol_series = df.filter(pl.col("vol").is_not_null())["vol"]
    if len(vol_series) == 0:
        raise ValueError("Insufficient data to compute regime labels")
    q33 = float(vol_series.quantile(0.33))
    q66 = float(vol_series.quantile(0.66))
    out = df.with_columns(
        pl.when(pl.col("vol").is_null())
        .then(None)
        .when(pl.col("vol") <= q33)
        .then(pl.lit("low"))
        .when(pl.col("vol") <= q66)
        .then(pl.lit("medium"))
        .otherwise(pl.lit("high"))
        .alias("regime")
    ).select(["CloseTime", "regime"])
    return normalize_timestamp_columns(out, ["CloseTime"])


def add_regime_labels(
    direction_df: pl.DataFrame,
    regime_df: pl.DataFrame,
) -> pl.DataFrame:
    """Attach regime labels to a direction table by timestamp."""
    direction_df = normalize_timestamp_columns(direction_df, ["timestamp"])
    regime_df = normalize_timestamp_columns(regime_df, ["CloseTime"])
    return direction_df.join(
        regime_df,
        left_on="timestamp",
        right_on="CloseTime",
        how="left",
    )


def _parse_tolerance(tol_str: str) -> timedelta:
    """Convert a tolerance string like '5m' or '1h' to a timedelta."""
    if tol_str.endswith("m"):
        return timedelta(minutes=int(tol_str[:-1]))
    if tol_str.endswith("h"):
        return timedelta(hours=int(tol_str[:-1]))
    raise ValueError(f"Unsupported tolerance format: {tol_str}")


def _join_asof_direction(
    left: pl.DataFrame,
    right: pl.DataFrame,
    strategy: str,
    tolerance: timedelta,
) -> pl.DataFrame:
    """As-of join two direction tables and return matched timestamp/direction."""
    left = normalize_timestamp_columns(left, ["timestamp"])
    right = normalize_timestamp_columns(right, ["timestamp"])
    right_cols = right.select(["timestamp", "direction"]).rename(
        {
            "timestamp": f"timestamp_{strategy}",
            "direction": f"direction_{strategy}",
        }
    )
    return (
        left.sort("timestamp")
        .join_asof(
            right_cols.sort(f"timestamp_{strategy}"),
            left_on="timestamp",
            right_on=f"timestamp_{strategy}",
            strategy=strategy,
            tolerance=tolerance,
        )
    )


def align_pairwise(
    left: pl.DataFrame,
    right: pl.DataFrame,
    tolerance: timedelta,
) -> pl.DataFrame:
    """Align two direction tables by nearest timestamp within tolerance.

    Parameters
    ----------
    left : pl.DataFrame
        Left direction table.
    right : pl.DataFrame
        Right direction table.
    tolerance : timedelta
        Maximum allowed distance for a match.

    Returns
    -------
    pl.DataFrame
        Left table with an added ``direction_right`` column.
    """
    bw = _join_asof_direction(left, right, "backward", tolerance)
    fw = _join_asof_direction(left, right, "forward", tolerance)
    bw = normalize_timestamp_columns(bw, ["timestamp"])
    fw = normalize_timestamp_columns(
        fw, ["timestamp", "timestamp_forward"]
    )

    combined = bw.join(
        fw.select(["timestamp", "timestamp_forward", "direction_forward"]),
        on="timestamp",
        how="left",
    )

    def _dist(col: str) -> pl.Expr:
        return (pl.col("timestamp") - pl.col(col)).dt.total_seconds().abs()

    return (
        combined.with_columns(
            _dist("timestamp_backward").alias("dist_bw"),
            _dist("timestamp_forward").alias("dist_fw"),
        )
        .with_columns(
            pl.when(pl.col("direction_backward").is_null())
            .then(pl.col("direction_forward"))
            .when(pl.col("direction_forward").is_null())
            .then(pl.col("direction_backward"))
            .when(pl.col("dist_bw") <= pl.col("dist_fw"))
            .then(pl.col("direction_backward"))
            .otherwise(pl.col("direction_forward"))
            .alias("direction_right")
        )
        .select(left.columns + ["direction_right"])
    )


def _directed_metrics(
    left: pl.DataFrame,
    right: pl.DataFrame,
    tolerance: timedelta,
) -> dict[str, Any]:
    """Compute directed overlap and agreement metrics."""
    aligned = align_pairwise(left, right, tolerance)
    matched = aligned.filter(pl.col("direction_right").is_not_null())
    n_left = left.height
    n_matched = matched.height
    overlap = n_matched / n_left if n_left > 0 else float("nan")
    agreement = (
        matched.filter(pl.col("direction") == pl.col("direction_right")).height
        / n_matched
        if n_matched > 0
        else float("nan")
    )
    regime_agreements: dict[str, float] = {}
    for regime in ("low", "medium", "high"):
        sub = matched.filter(pl.col("regime") == regime)
        n_sub = sub.height
        regime_agreements[regime] = (
            sub.filter(pl.col("direction") == pl.col("direction_right")).height
            / n_sub
            if n_sub > 0
            else float("nan")
        )
    return {
        "overlap": overlap,
        "agreement": agreement,
        "regime_agreements": regime_agreements,
        "n_left": n_left,
        "n_matched": n_matched,
    }


def compute_unordered_pair_metrics(
    df_a: pl.DataFrame,
    df_b: pl.DataFrame,
    tolerance: timedelta,
    chart_a: str,
    chart_b: str,
) -> dict[str, Any]:
    """Compute symmetric metrics by averaging both directions."""
    ab = _directed_metrics(df_a, df_b, tolerance)
    ba = _directed_metrics(df_b, df_a, tolerance)
    avg_regime = {
        r: float(np.nanmean([ab["regime_agreements"][r], ba["regime_agreements"][r]]))
        for r in ("low", "medium", "high")
    }
    return {
        "chart_a": chart_a,
        "chart_b": chart_b,
        "agreement": float(np.nanmean([ab["agreement"], ba["agreement"]])),
        "overlap": float(np.nanmean([ab["overlap"], ba["overlap"]])),
        "regime_agreements": avg_regime,
        "n_matched_ab": ab["n_matched"],
        "n_matched_ba": ba["n_matched"],
    }


def bootstrap_agreement_diff(
    ref_df: pl.DataFrame,
    target_a: pl.DataFrame,
    target_b: pl.DataFrame,
    tolerance: timedelta,
    n_iter: int = BOOTSTRAP_ITERATIONS,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, float]:
    """Paired bootstrap CI for difference in agreement rates.

    Compares ref->target_a agreement minus ref->target_b agreement
    on the subset of reference events that match both targets.
    """
    a_aligned = align_pairwise(ref_df, target_a, tolerance).rename(
        {"direction_right": "direction_a"}
    )
    b_aligned = align_pairwise(ref_df, target_b, tolerance).rename(
        {"direction_right": "direction_b"}
    )
    merged = a_aligned.join(
        b_aligned.select(["timestamp", "direction_b"]),
        on="timestamp",
        how="inner",
    ).filter(
        pl.col("direction_a").is_not_null() & pl.col("direction_b").is_not_null()
    )

    if merged.height == 0:
        return {
            "diff_mean": float("nan"),
            "ci_lower": float("nan"),
            "ci_upper": float("nan"),
            "n": 0,
        }

    diffs = (
        (merged["direction"] == merged["direction_a"]).cast(pl.Int8)
        - (merged["direction"] == merged["direction_b"]).cast(pl.Int8)
    ).to_numpy()
    observed = float(diffs.mean())
    rng = np.random.default_rng(seed)
    n = len(diffs)
    boot = np.empty(n_iter)
    for i in range(n_iter):
        idx = rng.integers(0, n, size=n)
        boot[i] = diffs[idx].mean()
    ci_lower, ci_upper = np.percentile(boot, [2.5, 97.5])
    return {
        "diff_mean": observed,
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "n": n,
    }


def plot_agreement_heatmap(df: pl.DataFrame, save_path: Path) -> plt.Figure:
    """Plot pairwise agreement heatmaps per instrument."""
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()
    chart_order = CHART_TYPES

    for ax, instrument in zip(axes, INSTRUMENTS):
        inst_df = df.filter(pl.col("instrument") == instrument)
        n = len(chart_order)
        mat = np.full((n, n), np.nan)
        for row in inst_df.iter_rows(named=True):
            i = chart_order.index(row["chart_a"])
            j = chart_order.index(row["chart_b"])
            mat[i, j] = row["agreement"]
            mat[j, i] = row["agreement"]

        sns.heatmap(
            mat,
            annot=True,
            fmt=".1%",
            cmap="YlGnBu",
            vmin=0,
            vmax=1,
            xticklabels=chart_order,
            yticklabels=chart_order,
            ax=ax,
            cbar_kws={"format": PercentFormatter(xmax=1.0)},
        )
        ax.set_title(instrument)

    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


def plot_overlap_heatmap(df: pl.DataFrame, save_path: Path) -> plt.Figure:
    """Plot pairwise overlap heatmaps per instrument."""
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()
    chart_order = CHART_TYPES

    for ax, instrument in zip(axes, INSTRUMENTS):
        inst_df = df.filter(pl.col("instrument") == instrument)
        n = len(chart_order)
        mat = np.full((n, n), np.nan)
        for row in inst_df.iter_rows(named=True):
            i = chart_order.index(row["chart_a"])
            j = chart_order.index(row["chart_b"])
            mat[i, j] = row["overlap"]
            mat[j, i] = row["overlap"]

        sns.heatmap(
            mat,
            annot=True,
            fmt=".1%",
            cmap="YlOrRd",
            vmin=0,
            vmax=1,
            xticklabels=chart_order,
            yticklabels=chart_order,
            ax=ax,
            cbar_kws={"format": PercentFormatter(xmax=1.0)},
        )
        ax.set_title(instrument)

    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


def plot_regime_bars(df: pl.DataFrame, save_path: Path) -> plt.Figure:
    """Plot regime-stratified agreement bar charts."""
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    df_pd = df.with_columns(
        (pl.col("chart_a") + "-" + pl.col("chart_b")).alias("pair")
    ).to_pandas()

    for ax, instrument in zip(axes, INSTRUMENTS):
        inst_df = df_pd[df_pd["instrument"] == instrument].copy()
        inst_df["regime"] = pd.Categorical(
            inst_df["regime"], categories=["low", "medium", "high"], ordered=True
        )

        sns.barplot(
            data=inst_df,
            x="regime",
            y="agreement",
            hue="pair",
            ax=ax,
            order=["low", "medium", "high"],
        )
        ax.axhline(0.5, color="grey", linestyle="--", linewidth=1)
        ax.set_ylim(0, 1)
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))
        ax.set_title(instrument)
        ax.legend(title="Pair", fontsize="small", loc="upper left")

    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


def plot_sensitivity(df: pl.DataFrame, save_path: Path) -> plt.Figure:
    """Plot sensitivity of key agreement rates to tolerance window."""
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    is_key = (
        ((pl.col("chart_a") == "linebreak") & (pl.col("chart_b") == "renko"))
        | ((pl.col("chart_a") == "renko") & (pl.col("chart_b") == "linebreak"))
        | ((pl.col("chart_a") == "linebreak") & (pl.col("chart_b") == "timebars"))
        | ((pl.col("chart_a") == "timebars") & (pl.col("chart_b") == "linebreak"))
        | ((pl.col("chart_a") == "renko") & (pl.col("chart_b") == "timebars"))
        | ((pl.col("chart_a") == "timebars") & (pl.col("chart_b") == "renko"))
    )
    df_pd = (
        df.filter(is_key)
        .with_columns((pl.col("chart_a") + "-" + pl.col("chart_b")).alias("pair"))
        .to_pandas()
    )

    for ax, instrument in zip(axes, INSTRUMENTS):
        inst_df = df_pd[df_pd["instrument"] == instrument]
        sns.barplot(
            data=inst_df,
            x="pair",
            y="agreement",
            hue="tolerance",
            ax=ax,
        )
        ax.axhline(0.5, color="grey", linestyle="--", linewidth=1)
        ax.set_ylim(0, 1)
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))
        ax.set_title(instrument)
        ax.legend(title="Tolerance", fontsize="small")

    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


def plot_timeline_raster(
    direction_tables: dict[str, pl.DataFrame],
    instrument: str,
    save_path: Path,
    n_events: int = 500,
) -> plt.Figure:
    """Plot a direction-label raster for a representative window."""
    sns.set_theme(style="white")
    timebars = direction_tables["timebars"]
    if timebars.height < n_events + 100:
        n_events = max(10, timebars.height - 100)
    start_idx = 100
    end_idx = start_idx + n_events
    start_t = timebars[start_idx, "timestamp"]
    end_t = timebars[end_idx, "timestamp"]

    grid = timebars.filter(
        (pl.col("timestamp") >= start_t) & (pl.col("timestamp") <= end_t)
    ).select("timestamp")
    grid = normalize_timestamp_columns(grid, ["timestamp"])

    chart_order = ["timebars", "heiken_ashi", "linebreak", "renko"]
    matrix = np.zeros((len(chart_order), grid.height), dtype=float)

    for i, chart in enumerate(chart_order):
        chart_df = direction_tables[chart]
        chart_df = normalize_timestamp_columns(chart_df, ["timestamp"])
        aligned = (
            grid.sort("timestamp")
            .join_asof(
                chart_df.sort("timestamp").select(["timestamp", "direction"]),
                left_on="timestamp",
                right_on="timestamp",
                strategy="backward",
            )
            .sort("timestamp")
        )
        arr = aligned["direction"].fill_null(0).to_numpy().astype(float)
        matrix[i, :] = arr

    fig, ax = plt.subplots(figsize=(14, 4))
    cmap = plt.cm.colors.ListedColormap(["#d62728", "#bdbdbd", "#1f77b4"])
    im = ax.imshow(
        matrix,
        aspect="auto",
        cmap=cmap,
        vmin=-1,
        vmax=1,
        interpolation="nearest",
    )
    ax.set_yticks(range(len(chart_order)))
    ax.set_yticklabels(chart_order)
    ax.set_xlabel("Time Index")
    ax.set_title(f"Direction Raster — {instrument}")
    fig.colorbar(im, ax=ax, ticks=[-1, 0, 1], label="Direction")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


def _record_pair(
    metrics: dict[str, Any],
    instrument: str,
    tolerance: str,
) -> dict[str, Any]:
    return {
        "instrument": instrument,
        "chart_a": metrics["chart_a"],
        "chart_b": metrics["chart_b"],
        "tolerance": tolerance,
        "agreement": metrics["agreement"],
        "overlap": metrics["overlap"],
        "n_matched_ab": metrics["n_matched_ab"],
        "n_matched_ba": metrics["n_matched_ba"],
    }


def _record_regime(
    metrics: dict[str, Any],
    instrument: str,
    tolerance: str,
) -> list[dict[str, Any]]:
    return [
        {
            "instrument": instrument,
            "chart_a": metrics["chart_a"],
            "chart_b": metrics["chart_b"],
            "tolerance": tolerance,
            "regime": regime,
            "agreement": metrics["regime_agreements"][regime],
        }
        for regime in ("low", "medium", "high")
    ]


def _process_instrument(
    instrument: str,
    tol_base: timedelta,
    tol_wide: timedelta,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, pl.DataFrame],
]:
    """Load data, generate charts, and compute metrics for one instrument."""
    time_bars = load_time_bars(instrument)
    charts = generate_chart_types(time_bars)
    regime_df = compute_regime_labels(time_bars, window=REGIME_WINDOW)

    direction_tables: dict[str, pl.DataFrame] = {}
    for chart_type, df in charts.items():
        dt = build_direction_table(df, chart_type, instrument)
        dt = add_regime_labels(dt, regime_df)
        direction_tables[chart_type] = dt

    pairwise: list[dict[str, Any]] = []
    regime: list[dict[str, Any]] = []
    sens: list[dict[str, Any]] = []
    for i in range(len(CHART_TYPES)):
        for j in range(i + 1, len(CHART_TYPES)):
            ca, cb = CHART_TYPES[i], CHART_TYPES[j]
            m_base = compute_unordered_pair_metrics(
                direction_tables[ca], direction_tables[cb], tol_base, ca, cb
            )
            m_wide = compute_unordered_pair_metrics(
                direction_tables[ca], direction_tables[cb], tol_wide, ca, cb
            )
            pairwise.append(_record_pair(m_base, instrument, TOLERANCE_BASE))
            pairwise.append(_record_pair(m_wide, instrument, TOLERANCE_WIDE))
            regime.extend(_record_regime(m_base, instrument, TOLERANCE_BASE))
            regime.extend(_record_regime(m_wide, instrument, TOLERANCE_WIDE))
            for m, t in ((m_base, TOLERANCE_BASE), (m_wide, TOLERANCE_WIDE)):
                sens.append(
                    {
                        "instrument": instrument,
                        "chart_a": m["chart_a"],
                        "chart_b": m["chart_b"],
                        "tolerance": t,
                        "agreement": m["agreement"],
                    }
                )

    boot1 = bootstrap_agreement_diff(
        direction_tables["linebreak"],
        direction_tables["renko"],
        direction_tables["timebars"],
        tol_base,
    )
    boot2 = bootstrap_agreement_diff(
        direction_tables["renko"],
        direction_tables["linebreak"],
        direction_tables["timebars"],
        tol_base,
    )
    bootstrap = [
        {
            "instrument": instrument,
            "reference": "linebreak",
            "target_a": "renko",
            "target_b": "timebars",
            **boot1,
        },
        {
            "instrument": instrument,
            "reference": "renko",
            "target_a": "linebreak",
            "target_b": "timebars",
            **boot2,
        },
    ]

    return pairwise, regime, sens, bootstrap, direction_tables


def main() -> None:
    """Run the full EXP-005 analysis pipeline."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    tol_base = _parse_tolerance(TOLERANCE_BASE)
    tol_wide = _parse_tolerance(TOLERANCE_WIDE)

    pairwise_records: list[dict[str, Any]] = []
    regime_records: list[dict[str, Any]] = []
    sensitivity_records: list[dict[str, Any]] = []
    bootstrap_records: list[dict[str, Any]] = []
    all_direction_tables: dict[str, dict[str, pl.DataFrame]] = {}

    for instrument in INSTRUMENTS:
        p, r, s, b, dts = _process_instrument(instrument, tol_base, tol_wide)
        pairwise_records.extend(p)
        regime_records.extend(r)
        sensitivity_records.extend(s)
        bootstrap_records.extend(b)
        all_direction_tables[instrument] = dts

    pairwise_df = pl.DataFrame(pairwise_records)
    regime_df_out = pl.DataFrame(regime_records)
    bootstrap_df = pl.DataFrame(bootstrap_records)
    sensitivity_df = pl.DataFrame(sensitivity_records)

    pairwise_df.write_csv(RESULTS_DIR / "pairwise_metrics.csv")
    regime_df_out.write_csv(RESULTS_DIR / "regime_metrics.csv")
    bootstrap_df.write_csv(RESULTS_DIR / "bootstrap_cis.csv")
    sensitivity_df.write_csv(RESULTS_DIR / "sensitivity_metrics.csv")

    (RESULTS_DIR / "results.json").write_text(
        json.dumps(
            {
                "pairwise": pairwise_df.to_dicts(),
                "regime": regime_df_out.to_dicts(),
                "bootstrap": bootstrap_df.to_dicts(),
                "sensitivity": sensitivity_df.to_dicts(),
            },
            indent=2,
            default=str,
        )
    )

    plot_agreement_heatmap(
        pairwise_df.filter(pl.col("tolerance") == TOLERANCE_BASE),
        PLOTS_DIR / "agreement_heatmap.png",
    )
    plot_overlap_heatmap(
        pairwise_df.filter(pl.col("tolerance") == TOLERANCE_BASE),
        PLOTS_DIR / "overlap_heatmap.png",
    )
    plot_regime_bars(
        regime_df_out.filter(pl.col("tolerance") == TOLERANCE_BASE),
        PLOTS_DIR / "regime_bars.png",
    )
    plot_sensitivity(sensitivity_df, PLOTS_DIR / "sensitivity.png")
    plot_timeline_raster(
        all_direction_tables["EURUSD"],
        "EURUSD",
        PLOTS_DIR / "timeline_raster.png",
    )


if __name__ == "__main__":
    main()
