"""
Experiment EXP-006: Heiken Ashi Synthetic Price Distortion Quantification
Implements the analysis plan from analysis-plan.md.
"""

import sys
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[3]
PROJECT_ROOT = PYTHON_ROOT.parent
SRC_DIR = PYTHON_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

import json
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import seaborn as sns
from heiken_ashi_generator import generate_heiken_ashi
from time_alignment import normalize_timestamp_columns

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------
DATA_DIR = PROJECT_ROOT / "data"
PLOTS_DIR = PYTHON_ROOT / "experiments/EXP-006/plots"
RESULTS_DIR = PYTHON_ROOT / "experiments/EXP-006/results"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

INSTRUMENT_FILES: dict[str, str] = {
    "EURUSD": "timebars/timebars_eurusd_20230102_000000_20260514_203330.parquet",
    "XAUUSD": "timebars/timebars_xauusd_20230102_230200_20260514_204148.parquet",
    "BTCUSD": "timebars/timebars_btcusd_20230102_000000_20260514_203813.parquet",
    "USTEC": "timebars/timebars_ustec_20230102_230000_20260514_204410.parquet",
}

HOLDOUT_FRACTION = 0.30
ROLLING_VOL_WINDOW = 30
BOOT_BLOCK_SIZE = 100
BOOT_N = 1000
BOOT_SEED = 42

sns.set_theme(style="whitegrid")


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_and_holdout(path: Path) -> pl.DataFrame:
    """Load time bars, sort chronologically, and exclude the global holdout.

    Parameters
    ----------
    path : Path
        Path to the Parquet file.

    Returns
    -------
    pl.DataFrame
        First 70 % of rows ordered by ``CloseTime``.
    """
    scan = pl.scan_parquet(path).sort("CloseTime")
    total_rows = int(scan.select(pl.len()).collect().item())
    cutoff = int(total_rows * (1.0 - HOLDOUT_FRACTION))
    return scan.slice(0, cutoff).collect()


# ---------------------------------------------------------------------------
# Regime labelling
# ---------------------------------------------------------------------------
def add_regimes(df: pl.DataFrame, window: int = ROLLING_VOL_WINDOW) -> pl.DataFrame:
    """Add a ``regime`` column (Low / Medium / High) based on rolling realised
    volatility of real log-returns.

    Parameters
    ----------
    df : pl.DataFrame
        Must contain ``real_return``.
    window : int, optional
        Rolling window size (default 30).

    Returns
    -------
    pl.DataFrame
        Input with ``rolling_vol`` and ``regime`` columns appended.
    """
    df = df.with_columns(
        pl.col("real_return")
        .rolling_std(window_size=window, min_periods=window)
        .alias("rolling_vol")
    )

    vols = df.filter(pl.col("rolling_vol").is_not_null())["rolling_vol"].to_numpy()
    if len(vols) == 0:
        return df.with_columns(pl.lit("Unknown").alias("regime"))

    q1, q2 = (
        float(np.nanquantile(vols, 1.0 / 3.0)),
        float(np.nanquantile(vols, 2.0 / 3.0)),
    )

    df = df.with_columns(
        pl.when(pl.col("rolling_vol") <= q1)
        .then(pl.lit("Low"))
        .when(pl.col("rolling_vol") <= q2)
        .then(pl.lit("Medium"))
        .otherwise(pl.lit("High"))
        .alias("regime")
    )
    return df


# ---------------------------------------------------------------------------
# Metrics helpers
# ---------------------------------------------------------------------------
def realised_volatility(returns: np.ndarray) -> float:
    """Standard deviation of returns (NaN-safe)."""
    return float(np.nanstd(returns, ddof=1))


def median_abs_return(returns: np.ndarray) -> float:
    """Median absolute return (NaN-safe)."""
    return float(np.nanmedian(np.abs(returns)))


def mean_range(ranges: np.ndarray) -> float:
    """Mean range (NaN-safe)."""
    return float(np.nanmean(ranges))


def direction_change_freq(returns: np.ndarray) -> float:
    """Fraction of consecutive bars with opposite direction.

    Parameters
    ----------
    returns : np.ndarray
        1-D array of returns.

    Returns
    -------
    float
        Direction-change frequency in [0, 1].
    """
    if len(returns) < 2:
        return 0.0
    signs = np.sign(returns)
    changes = np.diff(signs) != 0
    return float(np.nanmean(changes))


# ---------------------------------------------------------------------------
# Block bootstrap for compression ratios
# ---------------------------------------------------------------------------
def block_bootstrap_compression(
    real_arr: np.ndarray,
    ha_arr: np.ndarray,
    metric_fn: callable,
    block_size: int = BOOT_BLOCK_SIZE,
    n_boot: int = BOOT_N,
    seed: int = BOOT_SEED,
) -> dict[str, float]:
    """Block-bootstrap confidence interval for a compression ratio.

    Compression ratio is defined as ``1 - metric(ha) / metric(real)``.

    Parameters
    ----------
    real_arr, ha_arr : np.ndarray
        Paired 1-D arrays (already NaN-dropped and aligned).
    metric_fn : callable
        Function that takes a 1-D array and returns a scalar metric.
    block_size : int
        Block length in observations.
    n_boot : int
        Number of bootstrap samples.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    dict
        Keys: ``point_estimate``, ``ci_lower``, ``ci_upper``, ``median``.
    """
    rng = np.random.default_rng(seed)
    n = len(real_arr)
    if n < block_size * 2:
        raise ValueError(f"Insufficient data for block bootstrap: {n} rows")

    n_blocks = int(np.ceil(n / block_size))
    max_start = n - block_size + 1

    point = 1.0 - metric_fn(ha_arr) / metric_fn(real_arr)

    boot_values: list[float] = []
    for _ in range(n_boot):
        starts = rng.integers(0, max_start, size=n_blocks)
        indices = np.concatenate([np.arange(s, s + block_size) for s in starts])[:n]

        r_boot = real_arr[indices]
        h_boot = ha_arr[indices]

        m_real = metric_fn(r_boot)
        m_ha = metric_fn(h_boot)
        if m_real == 0 or not np.isfinite(m_real) or not np.isfinite(m_ha):
            continue

        boot_values.append(1.0 - m_ha / m_real)

    boot_arr = np.array(boot_values)
    return {
        "point_estimate": float(point),
        "ci_lower": float(np.percentile(boot_arr, 2.5)),
        "ci_upper": float(np.percentile(boot_arr, 97.5)),
        "median": float(np.percentile(boot_arr, 50.0)),
    }


# ---------------------------------------------------------------------------
# Core computation per instrument
# ---------------------------------------------------------------------------
def analyse_instrument(instrument: str, path: Path) -> dict[str, Any]:
    """Run the full EXP-006 analysis for a single instrument.

    Parameters
    ----------
    instrument : str
        Instrument symbol.
    path : Path
        Path to the time-bar Parquet file.

    Returns
    -------
    dict
        Nested dict with aggregate metrics, regime-stratified metrics,
        and bootstrap confidence intervals.
    """
    print(f"[{instrument}] Loading data …")
    tb = load_and_holdout(path)

    print(f"[{instrument}] Generating Heiken Ashi …")
    ha = generate_heiken_ashi(tb)

    # Join on CloseTime to recover original High/Low alongside HA columns
    tb = normalize_timestamp_columns(tb, ["CloseTime"])
    ha = normalize_timestamp_columns(ha, ["CloseTime"])
    df = tb.join(ha, on="CloseTime", how="inner")

    print(f"[{instrument}] Computing returns and ranges …")
    df = df.with_columns(
        (pl.col("RealClose").log() - pl.col("RealClose").shift(1).log()).alias(
            "real_return"
        ),
        (pl.col("HAClose").log() - pl.col("HAClose").shift(1).log()).alias("ha_return"),
        ((pl.col("High") - pl.col("Low")) / pl.col("Close") * 100.0).alias(
            "real_range_pct"
        ),
        ((pl.col("HAHigh") - pl.col("HALow")) / pl.col("HAClose") * 100.0).alias(
            "ha_range_pct"
        ),
    )

    df = add_regimes(df, window=ROLLING_VOL_WINDOW)

    # Drop rows with missing returns or regime
    clean = df.filter(
        pl.col("real_return").is_not_null()
        & pl.col("ha_return").is_not_null()
        & pl.col("regime").is_not_null()
    )

    n_rows = len(clean)
    print(f"[{instrument}] Clean rows after regime labelling: {n_rows:,}")
    if n_rows < BOOT_BLOCK_SIZE * 2:
        raise ValueError(f"[{instrument}] Insufficient clean rows: {n_rows}")

    # --- Aggregate metrics ---
    real_ret = clean["real_return"].to_numpy()
    ha_ret = clean["ha_return"].to_numpy()
    real_range = clean["real_range_pct"].to_numpy()
    ha_range = clean["ha_range_pct"].to_numpy()

    aggregate = {
        "realised_vol_real": realised_volatility(real_ret),
        "realised_vol_ha": realised_volatility(ha_ret),
        "median_abs_return_real": median_abs_return(real_ret),
        "median_abs_return_ha": median_abs_return(ha_ret),
        "mean_range_real": mean_range(real_range),
        "mean_range_ha": mean_range(ha_range),
        "dir_change_freq_real": direction_change_freq(real_ret),
        "dir_change_freq_ha": direction_change_freq(ha_ret),
        "n_bars": n_rows,
    }

    # --- Bootstrap CIs for the two key metrics ---
    print(f"[{instrument}] Bootstrapping volatility compression …")
    vol_bootstrap = block_bootstrap_compression(real_ret, ha_ret, realised_volatility)

    print(f"[{instrument}] Bootstrapping median-abs-return compression …")
    mad_bootstrap = block_bootstrap_compression(real_ret, ha_ret, median_abs_return)

    # --- Regime-stratified metrics ---
    regime_results: dict[str, dict[str, Any]] = {}
    for regime in ("Low", "Medium", "High"):
        sub = clean.filter(pl.col("regime") == regime)
        if len(sub) < 100:
            regime_results[regime] = {"error": "insufficient data"}
            continue

        r_ret = sub["real_return"].to_numpy()
        h_ret = sub["ha_return"].to_numpy()
        r_range = sub["real_range_pct"].to_numpy()
        h_range = sub["ha_range_pct"].to_numpy()

        regime_results[regime] = {
            "realised_vol_real": realised_volatility(r_ret),
            "realised_vol_ha": realised_volatility(h_ret),
            "median_abs_return_real": median_abs_return(r_ret),
            "median_abs_return_ha": median_abs_return(h_ret),
            "mean_range_real": mean_range(r_range),
            "mean_range_ha": mean_range(h_range),
            "dir_change_freq_real": direction_change_freq(r_ret),
            "dir_change_freq_ha": direction_change_freq(h_ret),
            "n_bars": len(sub),
        }

    return {
        "instrument": instrument,
        "aggregate": aggregate,
        "regimes": regime_results,
        "bootstrap": {
            "volatility_compression": vol_bootstrap,
            "median_abs_return_compression": mad_bootstrap,
        },
    }


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------
def plot_paired_close_window(
    df: pl.DataFrame,
    instrument: str,
    n_bars: int = 500,
    save_path: Path | None = None,
) -> plt.Figure:
    """Plot a representative window of RealClose vs HAClose.

    Parameters
    ----------
    df : pl.DataFrame
        DataFrame containing ``RealClose`` and ``HAClose``.
    instrument : str
        Instrument label for the title.
    n_bars : int
        Number of bars to display.
    save_path : Path, optional
        Where to save the figure.

    Returns
    -------
    plt.Figure
        The figure object.
    """
    start = max(0, len(df) // 2 - n_bars // 2)
    window = df.slice(start, n_bars).to_pandas()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(
        window["CloseTime"],
        window["RealClose"],
        label="Real Close",
        alpha=0.8,
        linewidth=1.2,
    )
    ax.plot(
        window["CloseTime"],
        window["HAClose"],
        label="HA Close",
        alpha=0.8,
        linewidth=1.2,
    )
    ax.set_title(
        f"{instrument} — Real vs Heiken Ashi Close (representative window, "
        f"n={n_bars})",
        fontsize=12,
    )
    ax.set_xlabel("Close Time")
    ax.set_ylabel("Price")
    ax.legend()
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


def plot_volatility_compression_bar(
    results: list[dict[str, Any]],
    save_path: Path | None = None,
) -> plt.Figure:
    """Bar chart of volatility compression ratios with bootstrap error bars.

    Parameters
    ----------
    results : list[dict]
        Per-instrument result dicts.
    save_path : Path, optional
        Where to save the figure.

    Returns
    -------
    plt.Figure
        The figure object.
    """
    instruments = [r["instrument"] for r in results]
    points = [
        r["bootstrap"]["volatility_compression"]["point_estimate"] for r in results
    ]
    lows = [r["bootstrap"]["volatility_compression"]["ci_lower"] for r in results]
    highs = [r["bootstrap"]["volatility_compression"]["ci_upper"] for r in results]
    errors = [
        [p - l for p, l in zip(points, lows)],
        [h - p for p, h in zip(points, highs)],
    ]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(instruments, points, yerr=errors, capsize=5, color="steelblue")
    ax.axhline(
        0.30, color="crimson", linestyle="--", linewidth=1.2, label="30 % threshold"
    )
    ax.set_title("Volatility Compression by Instrument (block-bootstrap 95 % CI)")
    ax.set_ylabel("Compression Ratio (1 - HA / Real)")
    ax.set_ylim(bottom=min(0.0, min(points) - 0.1))
    ax.legend()
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


def plot_abs_return_box(
    all_data: list[tuple[str, np.ndarray, np.ndarray]],
    save_path: Path | None = None,
) -> plt.Figure:
    """Box plot of absolute real vs HA returns by instrument.

    Parameters
    ----------
    all_data : list[tuple]
        List of (instrument, real_abs_returns, ha_abs_returns).
    save_path : Path, optional
        Where to save the figure.

    Returns
    -------
    plt.Figure
        The figure object.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    positions: list[int] = []
    box_data: list[np.ndarray] = []
    labels: list[str] = []
    colors: list[str] = []

    pos = 1
    for instrument, real_abs, ha_abs in all_data:
        # Subsample for plotting speed if necessary
        if len(real_abs) > 20_000:
            rng = np.random.default_rng(BOOT_SEED)
            idx = rng.choice(len(real_abs), size=20_000, replace=False)
            real_plot = real_abs[idx]
            ha_plot = ha_abs[idx]
        else:
            real_plot = real_abs
            ha_plot = ha_abs

        positions.extend([pos, pos + 1])
        box_data.extend([real_plot, ha_plot])
        labels.extend([f"{instrument}\nReal", f"{instrument}\nHA"])
        colors.extend(["lightcoral", "skyblue"])
        pos += 3

    bp = ax.boxplot(
        box_data,
        positions=positions,
        widths=0.6,
        patch_artist=True,
        showfliers=False,
        medianprops={"color": "black"},
    )
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)

    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=0, fontsize=8)
    ax.set_title("Absolute Return Distribution by Instrument (Real vs HA)")
    ax.set_ylabel("|Log Return|")
    ax.set_yscale("log")
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


def plot_regime_heatmap(
    results: list[dict[str, Any]],
    save_path: Path | None = None,
) -> plt.Figure:
    """Heatmap of compression ratios by instrument and volatility regime.

    Parameters
    ----------
    results : list[dict]
        Per-instrument result dicts.
    save_path : Path, optional
        Where to save the figure.

    Returns
    -------
    plt.Figure
        The figure object.
    """
    instruments = [r["instrument"] for r in results]
    regimes = ["Low", "Medium", "High"]
    metrics = [
        ("volatility", "realised_vol"),
        ("median_abs_return", "median_abs_return"),
        ("range", "mean_range"),
        ("dir_change", "dir_change_freq"),
    ]

    n_metrics = len(metrics)
    fig, axes = plt.subplots(1, n_metrics, figsize=(4 * n_metrics, 5), sharey=True)
    if n_metrics == 1:
        axes = [axes]

    for ax, (label, key) in zip(axes, metrics):
        matrix = np.zeros((len(instruments), len(regimes)))
        for i, r in enumerate(results):
            for j, regime in enumerate(regimes):
                reg = r["regimes"].get(regime, {})
                if "error" in reg:
                    matrix[i, j] = np.nan
                    continue
                real_val = reg.get(f"{key}_real", np.nan)
                ha_val = reg.get(f"{key}_ha", np.nan)
                if (
                    real_val
                    and real_val != 0
                    and np.isfinite(real_val)
                    and np.isfinite(ha_val)
                ):
                    matrix[i, j] = 1.0 - ha_val / real_val
                else:
                    matrix[i, j] = np.nan

        im = ax.imshow(matrix, aspect="auto", cmap="RdYlGn_r", vmin=-0.5, vmax=1.0)
        ax.set_xticks(range(len(regimes)))
        ax.set_xticklabels(regimes)
        ax.set_yticks(range(len(instruments)))
        ax.set_yticklabels(instruments)
        ax.set_title(f"{label} compression")
        for i in range(len(instruments)):
            for j in range(len(regimes)):
                if not np.isnan(matrix[i, j]):
                    ax.text(
                        j,
                        i,
                        f"{matrix[i, j]:.2f}",
                        ha="center",
                        va="center",
                        color="white" if abs(matrix[i, j]) > 0.5 else "black",
                        fontsize=8,
                    )
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    fig.suptitle("Compression Ratios by Instrument and Volatility Regime", fontsize=14)
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------
def main() -> None:
    all_results: list[dict[str, Any]] = []
    plot_data: list[tuple[str, np.ndarray, np.ndarray]] = []
    example_df: pl.DataFrame | None = None
    example_instrument: str = "EURUSD"

    for instrument, rel_path in INSTRUMENT_FILES.items():
        path = DATA_DIR / rel_path
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {path}")

        result = analyse_instrument(instrument, path)
        all_results.append(result)

        # Gather data for the box plot
        df_instr = load_and_holdout(path)
        ha_instr = generate_heiken_ashi(df_instr)
        df_instr = normalize_timestamp_columns(df_instr, ["CloseTime"])
        ha_instr = normalize_timestamp_columns(ha_instr, ["CloseTime"])
        combined = df_instr.join(ha_instr, on="CloseTime", how="inner")
        combined = combined.with_columns(
            (pl.col("RealClose").log() - pl.col("RealClose").shift(1).log()).alias(
                "real_return"
            ),
            (pl.col("HAClose").log() - pl.col("HAClose").shift(1).log()).alias(
                "ha_return"
            ),
        ).filter(
            pl.col("real_return").is_not_null() & pl.col("ha_return").is_not_null()
        )
        real_abs = np.abs(combined["real_return"].to_numpy())
        ha_abs = np.abs(combined["ha_return"].to_numpy())
        plot_data.append((instrument, real_abs, ha_abs))

        # Keep one representative dataframe for the window timeline plot
        if instrument == example_instrument:
            example_df = combined

        # Print concise summary to stdout
        vol_comp = result["bootstrap"]["volatility_compression"]
        mad_comp = result["bootstrap"]["median_abs_return_compression"]
        print(
            f"[{instrument}] Vol compression: {vol_comp['point_estimate']:.3f} "
            f"(95 % CI {vol_comp['ci_lower']:.3f}–{vol_comp['ci_upper']:.3f}) | "
            f"MAD compression: {mad_comp['point_estimate']:.3f} "
            f"(95 % CI {mad_comp['ci_lower']:.3f}–{mad_comp['ci_upper']:.3f})"
        )

    # --- Save numerical results ---
    results_path = RESULTS_DIR / "distortion_metrics.json"
    with open(results_path, "w") as fh:
        json.dump(all_results, fh, indent=2, default=str)
    print(f"\nResults saved to {results_path}")

    # --- Generate plots ---
    print("\nGenerating plots …")

    if example_df is not None:
        plot_paired_close_window(
            example_df,
            example_instrument,
            save_path=PLOTS_DIR / "01_paired_close_window.png",
        )
        print("  • 01_paired_close_window.png")

    plot_volatility_compression_bar(
        all_results,
        save_path=PLOTS_DIR / "02_volatility_compression.png",
    )
    print("  • 02_volatility_compression.png")

    plot_abs_return_box(
        plot_data,
        save_path=PLOTS_DIR / "03_abs_return_box.png",
    )
    print("  • 03_abs_return_box.png")

    plot_regime_heatmap(
        all_results,
        save_path=PLOTS_DIR / "04_regime_heatmap.png",
    )
    print("  • 04_regime_heatmap.png")

    print("\nExperiment EXP-006 complete.")


if __name__ == "__main__":
    main()
