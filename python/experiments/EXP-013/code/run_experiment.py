"""
Experiment EXP-013: NY Macro Window Characterization
Implements the approved scope and analysis plan.
"""
import sys
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[3]
PROJECT_ROOT = PYTHON_ROOT.parent
SRC_DIR = PYTHON_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

import hashlib
import json
import logging
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl
import seaborn as sns

from ict_timebar import (
    INSTRUMENTS,
    MACRO_WINDOW_SPECS,
    OVERNIGHT_END_MINUTE,
    add_bar_diagnostics,
    add_ny_time_features,
    compute_liquidity_levels,
    load_analysis_timebars,
    train_cutoff_time,
    weekday_filter,
)


LOGGER = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-013"

BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 42
RANDOM_CONTROLS_PER_WINDOW = 100
PRIMARY_EFFECT_THRESHOLD_ATR = 0.10
FORWARD_HORIZONS_MINUTES = [10, 20, 60]
DISPLACEMENT_LOW_CLOSE_LOCATION = 0.25
DISPLACEMENT_HIGH_CLOSE_LOCATION = 0.75
# F02: restrict random controls to the active NY session to avoid confounding
# macro-window effects with session-vs-overnight structure.
RANDOM_CONTROL_SESSION_START = 7 * 60   # 07:00 NY
RANDOM_CONTROL_SESSION_END = 17 * 60    # 17:00 NY


def minute_range_overlaps(start: int, end: int, other_start: int, other_end: int) -> bool:
    """Return whether two half-open minute ranges overlap."""
    return max(start, other_start) < min(end, other_end)


def overlaps_any_macro(start: int, end: int) -> bool:
    """Return True if [start, end) overlaps any macro window spec."""
    return any(
        minute_range_overlaps(start, end, spec.start_minute, spec.end_minute)
        for spec in MACRO_WINDOW_SPECS
    )


def random_control_starts(
    instrument: str,
    ny_date: Any,
    window: str,
    duration: int,
) -> list[int]:
    """Return deterministic session-bounded random control starts outside macro windows.

    Candidates are drawn from [RANDOM_CONTROL_SESSION_START, RANDOM_CONTROL_SESSION_END)
    to prevent confounding the macro-window effect with session-vs-overnight structure.
    """
    # F02: bound to active session so random controls are session-comparable.
    session_end_start = RANDOM_CONTROL_SESSION_END - duration
    candidates = [
        start
        for start in range(RANDOM_CONTROL_SESSION_START, session_end_start + 1)
        if not any(
            minute_range_overlaps(start, start + duration, spec.start_minute, spec.end_minute)
            for spec in MACRO_WINDOW_SPECS
        )
    ]
    if not candidates:
        return []
    seed_bytes = f"{instrument}|{ny_date}|{window}".encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(seed_bytes).digest()[:8], "big") % (2**32)
    rng = np.random.default_rng(seed)
    draws = rng.choice(candidates, size=RANDOM_CONTROLS_PER_WINDOW, replace=True)
    return [int(value) for value in draws]


def day_metric_arrays(day_frame: pl.DataFrame) -> dict[str, np.ndarray]:
    """Return sorted per-day arrays for fast repeated window summaries."""
    sorted_frame = day_frame.sort("NYMinuteOfDay")
    return {
        "minute": sorted_frame["NYMinuteOfDay"].to_numpy(),
        "high": sorted_frame["High"].to_numpy(),
        "low": sorted_frame["Low"].to_numpy(),
        "open": sorted_frame["Open"].to_numpy(),
        "close": sorted_frame["Close"].to_numpy(),
        "atr14_prior": sorted_frame["ATR14Prior"].to_numpy(),
        "true_range": sorted_frame["TrueRange"].to_numpy(),
        "true_range_p80_prior": sorted_frame["TrueRangeP80Prior"].to_numpy(),
        "close_location": sorted_frame["CloseLocation"].to_numpy(),
    }


def summarize_window_metrics_fast(
    arrays: dict[str, np.ndarray],
    start_minute: int,
    end_minute: int,
    levels: pd.Series | None,
) -> dict[str, Any]:
    """Compute scoped metrics for one intraday window from cached day arrays."""
    minutes = arrays["minute"]
    start_idx = int(np.searchsorted(minutes, start_minute, side="left"))
    end_idx = int(np.searchsorted(minutes, end_minute, side="left"))
    expected_bars = end_minute - start_minute

    metrics: dict[str, Any] = {
        "StartMinute": start_minute,
        "EndMinute": end_minute,
        "ExpectedBars": expected_bars,
        "ObservedBars": end_idx - start_idx,
        "CoverageRatio": (
            (end_idx - start_idx) / expected_bars if expected_bars else np.nan
        ),
        "TrueRangeNormATR14": np.nan,
        "AbsCloseReturn": np.nan,
        "SweepOccurred": np.nan,
        "DisplacementOccurred": np.nan,
    }
    for horizon in FORWARD_HORIZONS_MINUTES:
        metrics[f"ForwardReturn{horizon}m"] = np.nan

    if start_idx >= end_idx:
        return metrics

    window_slice = slice(start_idx, end_idx)
    high = float(np.max(arrays["high"][window_slice]))
    low = float(np.min(arrays["low"][window_slice]))
    # F09: use the ATR known strictly before the window (bar at start_idx - 1),
    # not the first finite value inside the window, to prevent in-window look-ahead.
    pre_window_atr = np.nan
    if start_idx > 0:
        candidate = float(arrays["atr14_prior"][start_idx - 1])
        if np.isfinite(candidate) and candidate > 0:
            pre_window_atr = candidate
    if np.isfinite(pre_window_atr):
        metrics["TrueRangeNormATR14"] = (high - low) / pre_window_atr

    prior_close = None
    if start_idx > 0:
        prior_close = float(arrays["close"][start_idx - 1])
        if prior_close != 0:
            metrics["AbsCloseReturn"] = abs(
                float(arrays["close"][end_idx - 1]) / prior_close - 1.0
            )

    for horizon in FORWARD_HORIZONS_MINUTES:
        target_minute = end_minute + horizon
        if target_minute > 24 * 60 - 1 or prior_close is None or prior_close == 0:
            continue
        forward_idx = int(np.searchsorted(minutes, target_minute, side="left"))
        if forward_idx < len(minutes):
            metrics[f"ForwardReturn{horizon}m"] = (
                float(arrays["close"][forward_idx]) / prior_close - 1.0
            )

    true_range_p80 = arrays["true_range_p80_prior"][window_slice]
    displacement_mask = (
        np.isfinite(true_range_p80)
        & (arrays["true_range"][window_slice] >= true_range_p80)
        & (
            (arrays["close_location"][window_slice] <= DISPLACEMENT_LOW_CLOSE_LOCATION)
            | (arrays["close_location"][window_slice] >= DISPLACEMENT_HIGH_CLOSE_LOCATION)
        )
    )
    metrics["DisplacementOccurred"] = int(bool(np.any(displacement_mask)))
    metrics["SweepOccurred"] = int(
        level_sweep_occurred_fast(arrays, start_idx, end_idx, levels, start_minute)
    )
    return metrics


def level_sweep_occurred_fast(
    arrays: dict[str, np.ndarray],
    start_idx: int,
    end_idx: int,
    levels: pd.Series | None,
    start_minute: int,
) -> bool:
    """Return whether a window sweeps and reclaims any liquidity level.

    A high sweep is: window max High > level AND window last Close < level.
    A low sweep is:  window min Low  < level AND window last Close > level.
    This is a window-level definition, not a single-bar rule, to match the
    ICT failed-breakout concept that EXP-015 will inherit.
    """
    if levels is None or start_idx >= end_idx:
        return False

    high_levels = [levels.get("PDH")]
    low_levels = [levels.get("PDL")]
    if start_minute >= OVERNIGHT_END_MINUTE:
        high_levels.append(levels.get("ONH"))
        low_levels.append(levels.get("ONL"))

    window_slice = slice(start_idx, end_idx)
    window_high = float(np.max(arrays["high"][window_slice]))
    window_low = float(np.min(arrays["low"][window_slice]))
    last_close = float(arrays["close"][end_idx - 1])

    for value in high_levels:
        if pd.notna(value) and window_high > float(value) and last_close < float(value):
            return True
    for value in low_levels:
        if pd.notna(value) and window_low < float(value) and last_close > float(value):
            return True
    return False


def average_metric_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Average numeric metrics across control rows."""
    if not rows:
        return {}
    frame = pd.DataFrame(rows)
    numeric_cols = frame.select_dtypes(include=[np.number]).columns.tolist()
    averaged = frame[numeric_cols].mean(numeric_only=True).to_dict()
    averaged["ObservedBars"] = frame["ObservedBars"].mean()
    averaged["ExpectedBars"] = frame["ExpectedBars"].mean()
    return averaged


def build_window_observations(
    instrument: str,
    frame: pl.DataFrame,
    levels: pd.DataFrame,
) -> pd.DataFrame:
    """Build macro, adjacent, and randomized control observations."""
    rows: list[dict[str, Any]] = []
    levels_by_date = {
        row.NYDate: row
        for row in levels[levels["Instrument"] == instrument].itertuples(index=False)
    }
    weekday_frame = weekday_filter(frame)

    for (ny_date,), day_frame in weekday_frame.group_by("NYDate", maintain_order=True):
        arrays = day_metric_arrays(day_frame)
        segment_count = int(day_frame.select(pl.col("Segment").n_unique()).item())
        segment = str(day_frame["Segment"][0]) if segment_count == 1 else "Boundary"
        levels_row = levels_by_date.get(ny_date)
        levels_series = pd.Series(levels_row._asdict()) if levels_row is not None else None

        for spec in MACRO_WINDOW_SPECS:
            base = {
                "Instrument": instrument,
                "Segment": segment,
                "NYDate": ny_date,
                "Window": spec.window,
                "Family": spec.family,
            }
            macro_metrics = summarize_window_metrics_fast(
                arrays,
                spec.start_minute,
                spec.end_minute,
                levels_series,
            )
            rows.append({**base, **macro_metrics, "ControlType": "Macro"})

            # F01: skip adjacent windows that overlap another macro spec to
            # prevent cross-contamination (e.g., PM3 AdjacentBefore contains PM2).
            adjacent_rows: list[dict[str, Any]] = []
            before_start = spec.start_minute - spec.duration
            if before_start >= 0 and not overlaps_any_macro(before_start, spec.start_minute):
                before = summarize_window_metrics_fast(
                    arrays,
                    before_start,
                    spec.start_minute,
                    levels_series,
                )
                adjacent_rows.append(before)
                rows.append({**base, **before, "ControlType": "AdjacentBefore"})
            after_end = spec.end_minute + spec.duration
            if after_end <= 24 * 60 and not overlaps_any_macro(spec.end_minute, after_end):
                after = summarize_window_metrics_fast(
                    arrays,
                    spec.end_minute,
                    after_end,
                    levels_series,
                )
                adjacent_rows.append(after)
                rows.append({**base, **after, "ControlType": "AdjacentAfter"})
            adjacent_mean = average_metric_rows(adjacent_rows)
            if adjacent_mean:
                rows.append({**base, **adjacent_mean, "ControlType": "AdjacentMean"})

            random_starts = random_control_starts(
                instrument,
                ny_date,
                spec.window,
                spec.duration,
            )
            random_rows = [
                summarize_window_metrics_fast(
                    arrays,
                    start,
                    start + spec.duration,
                    levels_series,
                )
                for start in random_starts
            ]
            # F03: store one representative draw (draw 0) as a single paired control
            # for bootstrap so that CI width reflects single-draw variance, not the
            # compressed variance of an average over 100 draws.
            if random_rows:
                rows.append({**base, **random_rows[0], "ControlType": "RandomControl"})
            # Keep the mean as a descriptive diagnostic (not used in primary bootstrap).
            random_mean = average_metric_rows(random_rows)
            if random_mean:
                random_mean["RandomDraws"] = len(random_rows)
                rows.append({**base, **random_mean, "ControlType": "RandomMean"})

    return pd.DataFrame(rows)


def metric_summary(observations: pd.DataFrame) -> pd.DataFrame:
    """Summarize scoped metrics by instrument, segment, and control type."""
    metric_cols = [
        "CoverageRatio",
        "TrueRangeNormATR14",
        "AbsCloseReturn",
        "SweepOccurred",
        "DisplacementOccurred",
        "ForwardReturn10m",
        "ForwardReturn20m",
        "ForwardReturn60m",
    ]
    rows: list[dict[str, Any]] = []
    scoped = observations[observations["Segment"].isin(["Train", "Test"])]
    for keys, group in scoped.groupby(["Instrument", "Segment", "ControlType"]):
        instrument, segment, control_type = keys
        for metric in metric_cols:
            values = group[metric].dropna()
            rows.append(
                {
                    "Instrument": instrument,
                    "Segment": segment,
                    "ControlType": control_type,
                    "Metric": metric,
                    "Observations": int(values.shape[0]),
                    "Mean": float(values.mean()) if not values.empty else np.nan,
                    "Median": float(values.median()) if not values.empty else np.nan,
                    "P25": float(values.quantile(0.25)) if not values.empty else np.nan,
                    "P75": float(values.quantile(0.75)) if not values.empty else np.nan,
                }
            )
    return pd.DataFrame(rows)


def bootstrap_ci(values: np.ndarray, seed: int = BOOTSTRAP_SEED) -> tuple[float, float]:
    """Return a non-parametric bootstrap 95 percent interval for mean difference.

    F08: accepts a per-comparison seed so that different estimators use
    independent RNG streams rather than all sharing BOOTSTRAP_SEED.
    """
    clean = values[np.isfinite(values)]
    if clean.size < 2:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, clean.size, size=(BOOTSTRAP_REPS, clean.size))
    samples = clean[idx].mean(axis=1)
    return float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))


def primary_effects(observations: pd.DataFrame) -> pd.DataFrame:
    """Compute primary macro-minus-control effects for the ATR-normalized range.

    Uses RandomControl (single draw per date) instead of RandomMean so that the
    bootstrap CI reflects single-draw variance rather than the compressed variance
    of an average over 100 draws (F03). Derives a distinct RNG seed per comparison
    so estimators are independent (F08). Guards against silent pivot aggregation
    of duplicate rows before pivoting (F10).
    """
    # F10: warn if key uniqueness is violated to catch upstream data bugs.
    scoped = observations[
        observations["Segment"].isin(["Train", "Test"])
        & observations["ControlType"].isin(["Macro", "AdjacentMean", "RandomControl"])
    ].copy()
    key_cols = ["Instrument", "Segment", "NYDate", "Window"]
    uniqueness_check = scoped[key_cols + ["ControlType"]].drop_duplicates()
    if len(uniqueness_check) != len(scoped):
        LOGGER.warning(
            "Duplicate (Instrument, Segment, NYDate, Window, ControlType) rows detected "
            "before pivot; aggfunc='first' will silently discard extras."
        )
    wide = scoped.pivot_table(
        index=key_cols,
        columns="ControlType",
        values="TrueRangeNormATR14",
        aggfunc="first",
    ).reset_index()

    rows: list[dict[str, Any]] = []
    # F03: RandomControl replaces RandomMean as the primary bootstrap comparator.
    for control in ["AdjacentMean", "RandomControl"]:
        if control not in wide.columns:
            continue
        wide[f"Diff_{control}"] = wide["Macro"] - wide[control]
        for keys, group in wide.groupby(["Instrument", "Segment"]):
            instrument, segment = keys
            diffs = group[f"Diff_{control}"].to_numpy(dtype=float)
            # F08: derive a distinct seed per estimator.
            seed_input = f"{instrument}|{segment}|{control}"
            ci_seed = int.from_bytes(
                hashlib.sha256(seed_input.encode()).digest()[:4], "big"
            )
            ci_low, ci_high = bootstrap_ci(diffs, seed=ci_seed)
            clean = diffs[np.isfinite(diffs)]
            rows.append(
                {
                    "Instrument": instrument,
                    "Segment": segment,
                    "ControlFamily": control,
                    "PairedObservations": int(clean.size),
                    "MedianDifferenceATR": float(np.median(clean)) if clean.size else np.nan,
                    "MeanDifferenceATR": float(np.mean(clean)) if clean.size else np.nan,
                    "CI95Low": ci_low,
                    "CI95High": ci_high,
                    "SupportsPrimaryCriterion": bool(
                        clean.size > 1
                        and np.isfinite(ci_low)
                        and ci_low > 0
                        and np.median(clean) >= PRIMARY_EFFECT_THRESHOLD_ATR
                    ),
                }
            )
    return pd.DataFrame(rows)


def evaluate_primary_support(effects: pd.DataFrame) -> dict[str, Any]:
    """Summarize whether the primary criterion passes by instrument."""
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        subset = effects[effects["Instrument"] == instrument]
        test_subset = subset[subset["Segment"] == "Test"]
        train_subset = subset[subset["Segment"] == "Train"]
        test_has_both = set(test_subset["ControlFamily"]) == {"AdjacentMean", "RandomControl"}
        train_has_both = set(train_subset["ControlFamily"]) == {"AdjacentMean", "RandomControl"}
        test_pass = bool(test_has_both and test_subset["SupportsPrimaryCriterion"].all())
        train_pass = bool(train_has_both and train_subset["SupportsPrimaryCriterion"].all())
        rows.append(
            {
                "Instrument": instrument,
                "TrainPass": train_pass,
                "TestPass": test_pass,
                "InstrumentPass": train_pass and test_pass,
            }
        )
    support = pd.DataFrame(rows)
    return {
        "instrument_support": support.to_dict(orient="records"),
        "supporting_instruments": int(support["InstrumentPass"].sum()),
        "phase_support": int(support["InstrumentPass"].sum()) >= 3,
    }


def plot_primary_distribution(observations: pd.DataFrame, save_path: Path) -> None:
    """Plot primary metric distribution by control family."""
    sns.set_theme(style="whitegrid")
    # RandomControl (single draw) shown alongside Macro and AdjacentMean.
    # RandomMean is excluded from the primary plot (diagnostic only).
    plot_df = observations[
        observations["ControlType"].isin(["Macro", "AdjacentMean", "RandomControl"])
        & observations["Segment"].isin(["Train", "Test"])
    ].copy()
    fig, ax = plt.subplots(figsize=(10, 5.5))
    sns.boxplot(
        data=plot_df,
        x="Instrument",
        y="TrueRangeNormATR14",
        hue="ControlType",
        order=INSTRUMENTS,
        showfliers=False,
        ax=ax,
    )
    ax.set_title("EXP-013 Window True Range Normalized by Prior ATR14")
    ax.set_xlabel("")
    ax.set_ylabel("Window true range / ATR14 prior to window")
    ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_primary_effects(effects: pd.DataFrame, save_path: Path) -> None:
    """Plot primary bootstrap effect intervals."""
    sns.set_theme(style="whitegrid")
    plot_df = effects.copy()
    plot_df["Label"] = (
        plot_df["Instrument"] + " " + plot_df["Segment"] + " vs " + plot_df["ControlFamily"]
    )
    fig, ax = plt.subplots(figsize=(9, 7))
    y = np.arange(len(plot_df))
    x = plot_df["MeanDifferenceATR"].to_numpy(dtype=float)
    ci_low = plot_df["CI95Low"].to_numpy(dtype=float)
    ci_high = plot_df["CI95High"].to_numpy(dtype=float)
    ax.errorbar(
        x,
        y,
        xerr=[
            np.maximum(x - ci_low, 0.0),
            np.maximum(ci_high - x, 0.0),
        ],
        fmt="o",
        color="steelblue",
        ecolor="0.35",
        capsize=3,
    )
    ax.axvline(0.0, color="black", linewidth=1)
    ax.axvline(PRIMARY_EFFECT_THRESHOLD_ATR, color="firebrick", linestyle="--", linewidth=1)
    ax.set_yticks(y)
    ax.set_yticklabels(plot_df["Label"])
    ax.set_title("EXP-013 Macro Minus Control Primary Effects")
    ax.set_xlabel("Mean difference in ATR-normalized range with 95% bootstrap CI")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_window_counts(observations: pd.DataFrame, save_path: Path) -> None:
    """Plot macro-window observation counts by instrument and segment."""
    sns.set_theme(style="whitegrid")
    counts = (
        observations[
            (observations["ControlType"] == "Macro")
            & observations["Segment"].isin(["Train", "Test"])
        ]
        .groupby(["Instrument", "Segment", "Window"], as_index=False)
        .agg(Observations=("NYDate", "nunique"))
    )
    fig, ax = plt.subplots(figsize=(11, 5.5))
    sns.barplot(
        data=counts,
        x="Window",
        y="Observations",
        hue="Instrument",
        ax=ax,
    )
    ax.set_title("EXP-013 Macro-Window Observation Counts")
    ax.set_xlabel("")
    ax.set_ylabel("NY dates")
    ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_secondary_heatmap(summary: pd.DataFrame, save_path: Path) -> None:
    """Plot secondary metric medians when the primary gate passes."""
    secondary = summary[
        (summary["ControlType"] == "Macro")
        & (summary["Metric"].isin(["SweepOccurred", "DisplacementOccurred"]))
    ].copy()
    secondary["Label"] = secondary["Instrument"] + " " + secondary["Segment"]
    pivot = secondary.pivot_table(index="Label", columns="Metric", values="Mean")
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.heatmap(
        pivot,
        annot=True,
        fmt=".2f",
        cmap="mako",
        vmin=0.0,
        vmax=1.0,
        ax=ax,
        cbar_kws={"label": "Frequency"},
    )
    ax.set_title("EXP-013 Secondary Macro-Window Frequencies")
    ax.set_xlabel("")
    ax.set_ylabel("")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def write_outputs(
    observations: pd.DataFrame,
    summary: pd.DataFrame,
    effects: pd.DataFrame,
    support: dict[str, Any],
    plots_dir: Path,
    results_dir: Path,
) -> None:
    """Write scoped machine-readable and human-readable outputs."""
    observations.to_csv(results_dir / "window_observations.csv", index=False)
    summary.to_csv(results_dir / "metric_summary.csv", index=False)
    effects.to_csv(results_dir / "primary_effects.csv", index=False)

    payload = {
        "experiment_id": "EXP-013",
        "title": "NY Macro Window Characterization",
        "bootstrap_reps": BOOTSTRAP_REPS,
        "bootstrap_seed": "per-comparison (derived from instrument+segment+control)",
        "random_controls_per_window": RANDOM_CONTROLS_PER_WINDOW,
        "primary_effect_threshold_atr": PRIMARY_EFFECT_THRESHOLD_ATR,
        "macro_boundary_note": (
            "Macro-window membership follows EXP-012: CloseTimeNY at the start "
            "minute is the first bar of the window, and end minute is excluded."
        ),
        "random_control_note": (
            "RandomControl (draw 0) is a single session-bounded random draw "
            f"[{RANDOM_CONTROL_SESSION_START//60:02d}:00–{RANDOM_CONTROL_SESSION_END//60:02d}:00 NY] "
            "used for bootstrap. RandomMean (mean of 100 draws) is a diagnostic only."
        ),
        "adjacent_overlap_note": (
            "Adjacent windows that overlap another macro spec are excluded "
            "(affects PM2/PM3/PM4 cluster). AdjacentMean averages only "
            "non-contaminated neighbours."
        ),
        "secondary_sweep_note": (
            "Sweep = window max High > level AND window last Close < level (high sweep) "
            "or window min Low < level AND window last Close > level (low sweep). "
            "PDH/PDL are eligible all day; ONH/ONL are counted only for windows "
            "starting at or after 09:30 NY to avoid using levels unavailable at "
            "earlier window starts."
        ),
        "support_summary": support,
    }
    with (results_dir / "results.json").open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, default=str)

    with (results_dir / "numerical_summary.txt").open("w", encoding="utf-8") as handle:
        handle.write("EXP-013 NY Macro Window Characterization\n")
        handle.write(
            "Boundary convention: CloseTimeNY start minute is included; end minute is excluded.\n"
        )
        handle.write(
            "Primary metric: macro window true range divided by ATR14 of bar before window start.\n"
        )
        handle.write(
            "Random control: draw 0 from session-bounded pool "
            f"[{RANDOM_CONTROL_SESSION_START//60:02d}:00–{RANDOM_CONTROL_SESSION_END//60:02d}:00 NY]. "
            "Adjacent windows overlapping other macro specs are excluded.\n"
        )
        handle.write(
            "Sweep: window max High > level AND last Close reclaims (or vice versa for lows). "
            "ONH/ONL excluded before 09:30 NY to prevent look-ahead.\n"
        )
        handle.write("\nPrimary effects:\n")
        for row in effects.itertuples(index=False):
            handle.write(
                f"- {row.Instrument} {row.Segment} vs {row.ControlFamily}: "
                f"mean={row.MeanDifferenceATR:.4f}, "
                f"mean_CI=[{row.CI95Low:.4f}, {row.CI95High:.4f}], "
                f"median={row.MedianDifferenceATR:.4f}, "
                f"n={row.PairedObservations}, pass={row.SupportsPrimaryCriterion}\n"
            )
        handle.write("\nSupport summary:\n")
        for item in support["instrument_support"]:
            handle.write(
                f"- {item['Instrument']}: train_pass={item['TrainPass']}, "
                f"test_pass={item['TestPass']}, instrument_pass={item['InstrumentPass']}\n"
            )

    plot_primary_distribution(observations, plots_dir / "01_primary_distribution.png")
    plot_primary_effects(effects, plots_dir / "02_primary_effect_intervals.png")
    plot_window_counts(observations, plots_dir / "03_window_counts.png")
    if support["phase_support"]:
        plot_secondary_heatmap(summary, plots_dir / "04_secondary_frequency_heatmap.png")


def run_experiment() -> None:
    """Execute the EXP-013 macro-window characterization workflow."""
    plots_dir = EXP_DIR / "plots"
    results_dir = EXP_DIR / "results"
    plots_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    observation_parts: list[pd.DataFrame] = []
    for instrument in INSTRUMENTS:
        LOGGER.info("loading %s analysis-set time bars", instrument)
        load = load_analysis_timebars(DATA_DIR, instrument)
        LOGGER.info(
            "loaded %s analysis rows for %s; adding NY diagnostics",
            len(load.frame),
            instrument,
        )
        train_end = train_cutoff_time(load.frame, load.train_rows)
        frame = add_bar_diagnostics(add_ny_time_features(load.frame, train_end))
        LOGGER.info("computing %s liquidity levels", instrument)
        levels = compute_liquidity_levels(frame)
        LOGGER.info("building %s macro and control observations", instrument)
        observations = build_window_observations(instrument, frame, levels)
        LOGGER.info("built %s observations for %s", len(observations), instrument)
        observation_parts.append(observations)

    if not observation_parts:
        raise ValueError("No window observations were produced.")

    observations = pd.concat(observation_parts, ignore_index=True)
    summary = metric_summary(observations)
    effects = primary_effects(observations)
    support = evaluate_primary_support(effects)
    write_outputs(observations, summary, effects, support, plots_dir, results_dir)

    print("EXP-013 complete.")
    print(f"Supporting instruments: {support['supporting_instruments']}/4")
    print(f"Plots: {plots_dir}")
    print(f"Results: {results_dir}")


def main() -> None:
    """Entry point for manual execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_experiment()


if __name__ == "__main__":
    main()
