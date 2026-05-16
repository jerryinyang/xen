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
import logging
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import seaborn as sns
from heiken_ashi_generator import generate_heiken_ashi

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------
DATA_DIR = PROJECT_ROOT / "data"
PLOTS_DIR = PYTHON_ROOT / "experiments/EXP-006/plots"
RESULTS_DIR = PYTHON_ROOT / "experiments/EXP-006/results"

INSTRUMENTS = ["EURUSD", "XAUUSD", "BTCUSD", "USTEC"]
TIMEBAR_COLUMNS = ["OpenTime", "CloseTime", "Open", "High", "Low", "Close"]

HOLDOUT_FRACTION = 0.30
ROLLING_VOL_WINDOW = 30
REGIME_CALIBRATION_FRACTION = 0.7
BOOT_BLOCK_SIZE = 100
BOOT_N = 1000
BOOT_SEED = 42
PLOT_SAMPLE_N = 20_000

LOGGER = logging.getLogger(__name__)

sns.set_theme(style="whitegrid")


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def find_latest_timebars(instrument: str) -> Path:
    """Return the latest time-bar Parquet path for an instrument.

    Parameters
    ----------
    instrument : str
        Instrument symbol.

    Returns
    -------
    Path
        Latest matching time-bar file.
    """
    pattern = f"timebars/timebars_{instrument.lower()}_*.parquet"
    paths = sorted(DATA_DIR.glob(pattern))
    if not paths:
        raise FileNotFoundError(f"No time-bar files found for {instrument}")
    return paths[-1]


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
    scan = pl.scan_parquet(path).select(TIMEBAR_COLUMNS).sort("CloseTime")
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

    vol_df = df.filter(pl.col("rolling_vol").is_not_null()).select(
        ["CloseTime", "rolling_vol"]
    )
    if vol_df.height == 0:
        return df.with_columns(pl.lit(None).alias("regime"))

    calibration_rows = max(
        window,
        int(vol_df.height * REGIME_CALIBRATION_FRACTION),
    )
    calibration_rows = min(calibration_rows, vol_df.height)
    calibration = vol_df.slice(0, calibration_rows)
    q1, q2 = calibration.select(
        pl.col("rolling_vol").quantile(1.0 / 3.0).alias("q1"),
        pl.col("rolling_vol").quantile(2.0 / 3.0).alias("q2"),
    ).row(0)
    evaluation_start = calibration[-1, "CloseTime"]

    df = df.with_columns(
        pl.when(pl.col("rolling_vol").is_null())
        .then(None)
        .when(pl.col("CloseTime") <= pl.lit(evaluation_start))
        .then(None)
        .when(pl.col("rolling_vol") <= q1)
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
def block_bootstrap_key_metrics(
    real_arr: np.ndarray,
    ha_arr: np.ndarray,
    block_size: int = BOOT_BLOCK_SIZE,
    n_boot: int = BOOT_N,
    seed: int = BOOT_SEED,
) -> dict[str, dict[str, float]]:
    """Block-bootstrap confidence intervals for the two scoped key metrics.

    The two scoped metrics are:
    - realised volatility compression
    - median absolute return compression

    Parameters
    ----------
    real_arr, ha_arr : np.ndarray
        Paired 1-D arrays (already NaN-dropped and aligned).
    block_size : int
        Block length in observations.
    n_boot : int
        Number of bootstrap samples.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    dict[str, dict[str, float]]
        Bootstrap summaries for both key compression ratios.
    """
    rng = np.random.default_rng(seed)
    n = len(real_arr)
    if n < block_size * 2:
        raise ValueError(f"Insufficient data for block bootstrap: {n} rows")

    n_blocks = int(np.ceil(n / block_size))
    max_start = n - block_size + 1

    vol_real = realised_volatility(real_arr)
    vol_ha = realised_volatility(ha_arr)
    mad_real = median_abs_return(real_arr)
    mad_ha = median_abs_return(ha_arr)
    if (
        vol_real == 0
        or mad_real == 0
        or not np.isfinite(vol_real)
        or not np.isfinite(vol_ha)
        or not np.isfinite(mad_real)
        or not np.isfinite(mad_ha)
    ):
        raise ValueError("Compression ratio is undefined for non-finite or zero baseline")
    points = {
        "volatility_compression": 1.0 - vol_ha / vol_real,
        "median_abs_return_compression": 1.0 - mad_ha / mad_real,
    }

    boot_values = {
        "volatility_compression": [],
        "median_abs_return_compression": [],
    }
    for _ in range(n_boot):
        starts = rng.integers(0, max_start, size=n_blocks)
        indices = np.concatenate([np.arange(s, s + block_size) for s in starts])[:n]

        r_boot = real_arr[indices]
        h_boot = ha_arr[indices]

        r_vol = realised_volatility(r_boot)
        h_vol = realised_volatility(h_boot)
        if r_vol != 0 and np.isfinite(r_vol) and np.isfinite(h_vol):
            boot_values["volatility_compression"].append(1.0 - h_vol / r_vol)

        r_mad = median_abs_return(r_boot)
        h_mad = median_abs_return(h_boot)
        if r_mad != 0 and np.isfinite(r_mad) and np.isfinite(h_mad):
            boot_values["median_abs_return_compression"].append(
                1.0 - h_mad / r_mad
            )

    summary: dict[str, dict[str, float]] = {}
    for key, point_estimate in points.items():
        boot_arr = np.array(boot_values[key], dtype=float)
        if len(boot_arr) == 0:
            raise ValueError(f"No finite bootstrap values were produced for {key}")
        summary[key] = {
            "point_estimate": float(point_estimate),
            "ci_lower": float(np.percentile(boot_arr, 2.5)),
            "ci_upper": float(np.percentile(boot_arr, 97.5)),
            "median": float(np.percentile(boot_arr, 50.0)),
        }
    return summary


# ---------------------------------------------------------------------------
# Core computation per instrument
# ---------------------------------------------------------------------------
def build_analysis_frame(path: Path) -> pl.DataFrame:
    """Build the paired real/HA analysis DataFrame once.

    Parameters
    ----------
    path : Path
        Path to the time-bar Parquet file.

    Returns
    -------
    pl.DataFrame
        Clean paired data with real and HA diagnostic returns.
    """
    tb = load_and_holdout(path)
    ha = generate_heiken_ashi(tb)

    df = ha.with_columns(
        (pl.col("RealClose").log() - pl.col("RealClose").shift(1).log()).alias(
            "real_return"
        ),
        (pl.col("HAClose").log() - pl.col("HAClose").shift(1).log()).alias(
            "ha_return"
        ),
        ((pl.col("RealHigh") - pl.col("RealLow")) / pl.col("RealClose") * 100.0).alias(
            "real_range_pct"
        ),
        ((pl.col("HAHigh") - pl.col("HALow")) / pl.col("HAClose") * 100.0).alias(
            "ha_range_pct"
        ),
    )

    df = add_regimes(df, window=ROLLING_VOL_WINDOW)

    return df.filter(
        pl.col("real_return").is_not_null()
        & pl.col("ha_return").is_not_null()
    )


def analyse_instrument(
    instrument: str,
    path: Path,
) -> tuple[dict[str, Any], pl.DataFrame]:
    """Run the full EXP-006 analysis for a single instrument.

    Parameters
    ----------
    instrument : str
        Instrument symbol.
    path : Path
        Path to the time-bar Parquet file.

    Returns
    -------
    tuple[dict, pl.DataFrame]
        Nested metrics and bounded columns needed by plotting.
    """
    LOGGER.info("[%s] Loading data and generating Heiken Ashi", instrument)
    clean = build_analysis_frame(path)

    n_rows = len(clean)
    LOGGER.info("[%s] Clean rows after regime labelling: %s", instrument, f"{n_rows:,}")
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
    LOGGER.info("[%s] Bootstrapping key compression metrics", instrument)
    bootstrap = block_bootstrap_key_metrics(real_ret, ha_ret)

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

    result = {
        "instrument": instrument,
        "aggregate": aggregate,
        "regimes": regime_results,
        "bootstrap": bootstrap,
    }
    plot_frame = clean.select(
        ["CloseTime", "RealClose", "HAClose", "real_return", "ha_return"]
    )
    return result, plot_frame


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
        f"{instrument} - Real vs Heiken Ashi Close "
        f"(representative window, n={n_bars})",
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


def sample_abs_returns(clean: pl.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Return bounded absolute-return arrays for plotting.

    Parameters
    ----------
    clean : pl.DataFrame
        Paired analysis frame with ``real_return`` and ``ha_return``.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        Sampled absolute real and HA diagnostic returns.
    """
    real_abs = np.abs(clean["real_return"].to_numpy())
    ha_abs = np.abs(clean["ha_return"].to_numpy())
    if len(real_abs) <= PLOT_SAMPLE_N:
        return real_abs, ha_abs
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.choice(len(real_abs), size=PLOT_SAMPLE_N, replace=False)
    return real_abs[idx], ha_abs[idx]


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
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    all_results: list[dict[str, Any]] = []
    plot_data: list[tuple[str, np.ndarray, np.ndarray]] = []
    example_df: pl.DataFrame | None = None
    example_instrument: str = "EURUSD"

    for instrument in INSTRUMENTS:
        path = find_latest_timebars(instrument)
        result, clean = analyse_instrument(instrument, path)
        all_results.append(result)

        real_abs, ha_abs = sample_abs_returns(clean)
        plot_data.append((instrument, real_abs, ha_abs))

        # Keep one representative dataframe for the window timeline plot
        if instrument == example_instrument:
            example_df = clean

        vol_comp = result["bootstrap"]["volatility_compression"]
        mad_comp = result["bootstrap"]["median_abs_return_compression"]
        LOGGER.info(
            f"[{instrument}] Vol compression: {vol_comp['point_estimate']:.3f} "
            f"(95 pct CI {vol_comp['ci_lower']:.3f}-{vol_comp['ci_upper']:.3f}) | "
            f"MAD compression: {mad_comp['point_estimate']:.3f} "
            f"(95 pct CI {mad_comp['ci_lower']:.3f}-{mad_comp['ci_upper']:.3f})"
        )

    # --- Save numerical results ---
    results_path = RESULTS_DIR / "distortion_metrics.json"
    with open(results_path, "w") as fh:
        json.dump(all_results, fh, indent=2, default=str)
    LOGGER.info("")
    LOGGER.info("Results saved to %s", results_path)

    # --- Generate plots ---
    LOGGER.info("")
    LOGGER.info("Generating plots ...")

    if example_df is not None:
        plot_paired_close_window(
            example_df,
            example_instrument,
            save_path=PLOTS_DIR / "01_paired_close_window.png",
        )
        LOGGER.info("  - 01_paired_close_window.png")

    plot_volatility_compression_bar(
        all_results,
        save_path=PLOTS_DIR / "02_volatility_compression.png",
    )
    LOGGER.info("  - 02_volatility_compression.png")

    plot_abs_return_box(
        plot_data,
        save_path=PLOTS_DIR / "03_abs_return_box.png",
    )
    LOGGER.info("  - 03_abs_return_box.png")

    plot_regime_heatmap(
        all_results,
        save_path=PLOTS_DIR / "04_regime_heatmap.png",
    )
    LOGGER.info("  - 04_regime_heatmap.png")

    LOGGER.info("")
    LOGGER.info("Experiment EXP-006 complete.")


if __name__ == "__main__":
    main()
