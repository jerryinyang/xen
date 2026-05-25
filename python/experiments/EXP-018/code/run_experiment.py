"""
Experiment EXP-018: Displacement Confirmation Added to Sweeps
Implements the analysis plan from analysis-plan.md.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

PYTHON_ROOT = Path(__file__).resolve().parents[3]
PROJECT_ROOT = PYTHON_ROOT.parent
SRC_DIR = PYTHON_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

import polars as pl  # noqa: E402

from ict_timebar import (  # noqa: E402
    INSTRUMENTS,
    add_bar_diagnostics,
    compute_real_price_outcome,
    load_analysis_timebars,
)


LOGGER = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-018"
EXP015_RESULTS_DIR = PYTHON_ROOT / "experiments" / "EXP-015" / "results"

BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 42
MAX_CONFIRMATION_BARS = 10
BODY_MEDIAN_WINDOW = 100
BODY_MULTIPLE = 1.5
LOWER_CLOSE_QUARTILE = 0.25
UPPER_CLOSE_QUARTILE = 0.75
MIN_CONFIRMED_EVENTS = 50
IMPROVEMENT_THRESHOLD = 0.05
PLOT_R_CAP = 8.0

HIT_THRESHOLD = 0.05
MAE_IMPROVEMENT_THRESHOLD = 0.25
RETENTION_THRESHOLD = 0.50

SWEEP_COLS = {
    "Instrument",
    "NYDate",
    "Segment",
    "CloseTime",
    "Open",
    "High",
    "Low",
    "Close",
    "Side",
    "EventType",
    "LevelType",
    "Level",
    "Buffer",
    "Stop",
    "Hit1R_60m",
    "MAE_R_60m",
    "Ambiguous60",
}


def require_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    """Raise if a prerequisite artifact lacks required columns."""
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{label} is missing required columns: {missing}")


def _parse_bool_series(series: pd.Series, default: bool) -> pd.Series:
    """Normalize CSV bool encodings to pandas bool dtype.

    Python treats True/False and 1/0 as equal dict keys, so the mapping
    only needs string/bool entries; integer 1/0 values still match via
    the bool keys.
    """
    mapped = series.map(
        {
            True: True,
            False: False,
            "True": True,
            "False": False,
            "true": True,
            "false": False,
        }
    )
    return mapped.where(mapped.notna(), default).astype(bool)


def load_sweep_events() -> pd.DataFrame:
    """Load EXP-015 failed-sweep events used as the fixed baseline."""
    path = EXP015_RESULTS_DIR / "sweep_events.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required prerequisite artifact not found: {path}")
    events = pd.read_csv(path)
    require_columns(events, SWEEP_COLS, "EXP-015 sweep_events.csv")
    events = events[
        (events["EventType"] == "Sweep")
        & events["Segment"].isin(["Train", "Test"])
    ].copy()
    events["CloseTime"] = pd.to_datetime(events["CloseTime"])
    events["Ambiguous60"] = _parse_bool_series(events["Ambiguous60"], default=False)
    return events.sort_values(
        ["Instrument", "Segment", "CloseTime", "LevelType", "Side"]
    ).reset_index(drop=True)


def load_instrument_bars(instrument: str) -> pd.DataFrame:
    """Load holdout-excluded analysis bars with displacement helper columns.

    Only Segment labelling and bar diagnostics are needed; NY/macro features
    are skipped to keep memory and CPU bounded (EXP-018 never reads them).
    """
    loaded = load_analysis_timebars(DATA_DIR, instrument)
    frame = add_bar_diagnostics(loaded.frame).with_row_index("_Row").with_columns(
        pl.when(pl.col("_Row") < loaded.train_rows)
        .then(pl.lit("Train"))
        .otherwise(pl.lit("Test"))
        .alias("Segment")
    )
    bars = frame.sort("CloseTime").to_pandas()
    bars["CloseTime"] = pd.to_datetime(bars["CloseTime"])
    bars["OpenTime"] = pd.to_datetime(bars["OpenTime"])
    bars["BodyMedian100Prior"] = (
        bars["BodySize"].rolling(BODY_MEDIAN_WINDOW, min_periods=BODY_MEDIAN_WINDOW)
        .median()
        .shift(1)
    )
    return bars.reset_index(drop=True)


def _is_directional_displacement(row: pd.Series, side: str) -> bool:
    """Return whether a candidate bar matches the scoped displacement rule."""
    median_body = row["BodyMedian100Prior"]
    body = row["BodySize"]
    if not np.isfinite(median_body) or median_body <= 0.0:
        return False
    if not np.isfinite(body) or body < BODY_MULTIPLE * median_body:
        return False
    if side == "High":
        return bool(row["Close"] < row["Open"] and row["CloseLocation"] <= LOWER_CLOSE_QUARTILE)
    return bool(row["Close"] > row["Open"] and row["CloseLocation"] >= UPPER_CLOSE_QUARTILE)


def find_displacement_for_sweep(
    sweep: pd.Series,
    bars: pd.DataFrame,
    close_ns: np.ndarray,
) -> dict[str, Any]:
    """Find the first qualifying displacement candle within 10 bars after a sweep."""
    event_ns = int(pd.Timestamp(sweep["CloseTime"]).value)
    start_idx = int(np.searchsorted(close_ns, event_ns, side="right"))
    stop_idx = min(start_idx + MAX_CONFIRMATION_BARS, len(bars))
    if start_idx >= len(bars):
        return {"Confirmed": False, "MissReason": "NO_FORWARD_BARS"}

    for idx in range(start_idx, stop_idx):
        candidate = bars.iloc[idx]
        if _is_directional_displacement(candidate, str(sweep["Side"])):
            next_idx = idx + 1
            return {
                "Confirmed": True,
                "MissReason": "NONE",
                "DisplacementIndex": idx,
                "DisplacementTime": candidate["CloseTime"],
                "DisplacementOpen": float(candidate["Open"]),
                "DisplacementHigh": float(candidate["High"]),
                "DisplacementLow": float(candidate["Low"]),
                "DisplacementClose": float(candidate["Close"]),
                "DisplacementBody": float(candidate["BodySize"]),
                "BodyMedian100Prior": float(candidate["BodyMedian100Prior"]),
                "CloseLocation": float(candidate["CloseLocation"]),
                "DelayBars": idx - start_idx + 1,
                "HasNextOpen": next_idx < len(bars),
                "NextOpenTime": bars.iloc[next_idx]["OpenTime"] if next_idx < len(bars) else pd.NaT,
                "NextOpen": float(bars.iloc[next_idx]["Open"]) if next_idx < len(bars) else np.nan,
            }
    return {"Confirmed": False, "MissReason": "NO_DISPLACEMENT_WITHIN_10_BARS"}


def build_entry_event(
    sweep: pd.Series,
    proxy: str,
    entry_time: Any,
    entry: float,
    confirmation: dict[str, Any],
) -> dict[str, Any]:
    """Build one entry-proxy row with unchanged EXP-015 stop convention."""
    stop = float(sweep["Stop"])
    risk = abs(stop - entry)
    return {
        "Instrument": sweep["Instrument"],
        "NYDate": sweep["NYDate"],
        "Segment": sweep["Segment"],
        "LevelType": sweep["LevelType"],
        "Side": sweep["Side"],
        "SweepTime": sweep["CloseTime"],
        "DisplacementTime": confirmation["DisplacementTime"],
        "DelayBars": confirmation["DelayBars"],
        "EntryProxy": proxy,
        "EntryTime": entry_time,
        "Entry": entry,
        "Stop": stop,
        "Risk1R": risk,
    }


def detect_confirmed_entries(
    sweeps: pd.DataFrame,
    bars_by_instrument: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Detect displacement-confirmed sweeps and construct entry-proxy rows."""
    entries: list[dict[str, Any]] = []
    misses: list[dict[str, Any]] = []

    for instrument in INSTRUMENTS:
        bars = bars_by_instrument[instrument]
        close_ns = bars["CloseTime"].values.astype(np.int64)
        inst_sweeps = sweeps[sweeps["Instrument"] == instrument]
        for _, sweep in inst_sweeps.iterrows():
            confirmation = find_displacement_for_sweep(sweep, bars, close_ns)
            miss_base = {
                "Instrument": instrument,
                "Segment": sweep["Segment"],
                "NYDate": sweep["NYDate"],
                "SweepTime": sweep["CloseTime"],
                "Side": sweep["Side"],
                "LevelType": sweep["LevelType"],
                "Confirmed": confirmation["Confirmed"],
                "MissReason": confirmation["MissReason"],
            }
            misses.append({**miss_base, **confirmation})
            if not confirmation["Confirmed"] or not confirmation["HasNextOpen"]:
                continue

            entries.append(
                build_entry_event(
                    sweep,
                    "SweepClose",
                    sweep["CloseTime"],
                    float(sweep["Close"]),
                    confirmation,
                )
            )
            entries.append(
                build_entry_event(
                    sweep,
                    "DisplacementClose",
                    confirmation["DisplacementTime"],
                    confirmation["DisplacementClose"],
                    confirmation,
                )
            )
            entries.append(
                build_entry_event(
                    sweep,
                    "NextOpen",
                    confirmation["NextOpenTime"],
                    confirmation["NextOpen"],
                    confirmation,
                )
            )

    return pd.DataFrame(entries), pd.DataFrame(misses)


def append_outcomes(
    entries: pd.DataFrame,
    bars_by_instrument: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Append 60-minute real-price outcome metrics to entry-proxy rows."""
    rows: list[dict[str, Any]] = []
    for _, entry in entries.iterrows():
        bars = bars_by_instrument[str(entry["Instrument"])]
        outcome = compute_real_price_outcome(entry, bars, horizon_minutes=60)
        rows.append({**entry.to_dict(), **outcome})
    return pd.DataFrame(rows)


def summarize_retention(sweeps: pd.DataFrame, misses: pd.DataFrame) -> pd.DataFrame:
    """Summarize displacement-confirmation retention by instrument and segment."""
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        for segment in ("Train", "Test"):
            total = len(sweeps[(sweeps["Instrument"] == instrument) & (sweeps["Segment"] == segment)])
            confirmed = int(
                misses[
                    (misses["Instrument"] == instrument)
                    & (misses["Segment"] == segment)
                    & (misses["Confirmed"])
                ].shape[0]
            )
            rows.append(
                {
                    "Instrument": instrument,
                    "Segment": segment,
                    "SweepN": total,
                    "ConfirmedN": confirmed,
                    "RetainedPct": confirmed / total if total else np.nan,
                    "EventFloorMet": confirmed >= MIN_CONFIRMED_EVENTS,
                }
            )
    return pd.DataFrame(rows)


def summarize_outcomes(events: pd.DataFrame) -> pd.DataFrame:
    """Summarize outcome metrics by entry proxy, instrument, and segment."""
    rows: list[dict[str, Any]] = []
    for keys, group in events.groupby(["Instrument", "Segment", "EntryProxy"], sort=True):
        instrument, segment, proxy = keys
        hit = group.loc[~group["Ambiguous60"].fillna(True), "Hit1R_60m"].dropna()
        ret = group["Return_R_60m"].dropna()
        mae = group["MAE_R_60m"].dropna()
        rows.append(
            {
                "Instrument": instrument,
                "Segment": segment,
                "EntryProxy": proxy,
                "EventN": len(group),
                "Hit1R_N": int(hit.size),
                "Hit1R_Mean": float(hit.mean()) if hit.size else np.nan,
                "ReturnR_N": int(ret.size),
                "ReturnR_Mean": float(ret.mean()) if ret.size else np.nan,
                "MAE_N": int(mae.size),
                "MAE_Median": float(mae.median()) if mae.size else np.nan,
            }
        )
    return pd.DataFrame(rows)


def bootstrap_nested_difference(
    values: np.ndarray,
    filtered_mask: np.ndarray,
    rng: np.random.Generator,
    use_median: bool = False,
) -> dict[str, Any]:
    """Bootstrap filtered-minus-baseline difference for a nested filtered subset.

    The filtered group (displacement-confirmed) is a subset of the unfiltered
    EXP-015 sweep baseline. Each bootstrap resample is drawn from the full
    baseline rows; the filtered statistic is recomputed inside the same
    resample so dependence is preserved.
    """
    stat_fn = np.median if use_median else np.mean
    baseline_n = int(values.size)
    filtered_n = int(filtered_mask.sum())
    baseline_stat = float(stat_fn(values)) if baseline_n else np.nan
    filtered_values = values[filtered_mask]
    filtered_stat = float(stat_fn(filtered_values)) if filtered_n else np.nan
    result: dict[str, Any] = {
        "BaselineN": baseline_n,
        "FilteredN": filtered_n,
        "BaselineStat": baseline_stat,
        "FilteredStat": filtered_stat,
        "Diff": (
            filtered_stat - baseline_stat
            if np.isfinite(filtered_stat) and np.isfinite(baseline_stat)
            else np.nan
        ),
        "CI95Low": np.nan,
        "CI95High": np.nan,
    }
    if baseline_n < 2 or filtered_n < 2:
        return result
    diffs: list[float] = []
    for _ in range(BOOTSTRAP_REPS):
        indices = rng.integers(0, baseline_n, size=baseline_n)
        sample_values = values[indices]
        sample_mask = filtered_mask[indices]
        if not np.any(sample_mask):
            continue
        diffs.append(
            float(stat_fn(sample_values[sample_mask]) - stat_fn(sample_values))
        )
    if not diffs:
        return result
    diff_array = np.asarray(diffs, dtype=float)
    result["CI95Low"] = float(np.quantile(diff_array, 0.025))
    result["CI95High"] = float(np.quantile(diff_array, 0.975))
    return result


def compute_filter_effects(
    sweeps_with_confirm: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Compare displacement-confirmed-sweep outcomes vs full EXP-015 sweep
    population (unpaired nested-subset bootstrap)."""
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        for segment in ("Train", "Test"):
            group = sweeps_with_confirm[
                (sweeps_with_confirm["Instrument"] == instrument)
                & (sweeps_with_confirm["Segment"] == segment)
            ]
            total = len(group)
            confirmed = int(group["DisplacementConfirmed"].sum())
            retention_pct = confirmed / total if total else np.nan
            retention_floor = bool(
                confirmed >= MIN_CONFIRMED_EVENTS
                or (
                    np.isfinite(retention_pct)
                    and retention_pct >= RETENTION_THRESHOLD
                )
            )
            hit_group = group.loc[
                ~group["Ambiguous60"] & group["Hit1R_60m"].notna(),
                ["DisplacementConfirmed", "Hit1R_60m"],
            ]
            hit_stats = bootstrap_nested_difference(
                hit_group["Hit1R_60m"].to_numpy(dtype=float),
                hit_group["DisplacementConfirmed"].to_numpy(dtype=bool),
                rng,
                use_median=False,
            )
            mae_group = group.loc[
                group["MAE_R_60m"].notna(),
                ["DisplacementConfirmed", "MAE_R_60m"],
            ]
            mae_stats = bootstrap_nested_difference(
                mae_group["MAE_R_60m"].to_numpy(dtype=float),
                mae_group["DisplacementConfirmed"].to_numpy(dtype=bool),
                rng,
                use_median=True,
            )
            mae_improvement = (
                mae_stats["BaselineStat"] - mae_stats["FilteredStat"]
                if np.isfinite(mae_stats["BaselineStat"])
                and np.isfinite(mae_stats["FilteredStat"])
                else np.nan
            )
            mae_ci_low = -mae_stats["CI95High"] if np.isfinite(mae_stats["CI95High"]) else np.nan
            mae_ci_high = -mae_stats["CI95Low"] if np.isfinite(mae_stats["CI95Low"]) else np.nan
            rows.append(
                {
                    "Instrument": instrument,
                    "Segment": segment,
                    "TotalSweepN": total,
                    "ConfirmedSweepN": confirmed,
                    "RetentionPct": retention_pct,
                    "RetentionFloorMet": retention_floor,
                    "HitBaselineN": hit_stats["BaselineN"],
                    "HitConfirmedN": hit_stats["FilteredN"],
                    "HitBaselineMean": hit_stats["BaselineStat"],
                    "HitConfirmedMean": hit_stats["FilteredStat"],
                    "HitDiff": hit_stats["Diff"],
                    "HitCI95Low": hit_stats["CI95Low"],
                    "HitCI95High": hit_stats["CI95High"],
                    "MAEBaselineN": mae_stats["BaselineN"],
                    "MAEConfirmedN": mae_stats["FilteredN"],
                    "MAEBaselineMedian": mae_stats["BaselineStat"],
                    "MAEConfirmedMedian": mae_stats["FilteredStat"],
                    "MAEImprovement": mae_improvement,
                    "MAECI95Low": mae_ci_low,
                    "MAECI95High": mae_ci_high,
                    # Criteria use interval evidence: CI95-low must clear the
                    # predeclared threshold, not just the point estimate.
                    "HitCriterionMet": bool(
                        retention_floor
                        and np.isfinite(hit_stats["CI95Low"])
                        and hit_stats["CI95Low"] >= HIT_THRESHOLD
                    ),
                    "MAECriterionMet": bool(
                        retention_floor
                        and np.isfinite(mae_ci_low)
                        and mae_ci_low >= MAE_IMPROVEMENT_THRESHOLD
                    ),
                    "HitNegativeRefutes": bool(
                        retention_floor
                        and np.isfinite(hit_stats["CI95High"])
                        and hit_stats["CI95High"] < HIT_THRESHOLD
                    ),
                    "MAENegativeRefutes": bool(
                        retention_floor
                        and np.isfinite(mae_ci_high)
                        and mae_ci_high < MAE_IMPROVEMENT_THRESHOLD
                    ),
                }
            )
    return pd.DataFrame(rows)


def paired_bootstrap_diff(
    base: np.ndarray,
    variant: np.ndarray,
    rng: np.random.Generator,
) -> dict[str, float]:
    """Bootstrap paired variant-minus-baseline mean difference."""
    valid = np.isfinite(base) & np.isfinite(variant)
    base = base[valid]
    variant = variant[valid]
    if base.size == 0:
        return {"N": 0, "Diff": np.nan, "CI95Low": np.nan, "CI95High": np.nan}
    diffs = variant - base
    point = float(np.mean(diffs))
    if diffs.size < 2:
        return {"N": int(diffs.size), "Diff": point, "CI95Low": np.nan, "CI95High": np.nan}
    samples = [
        float(np.mean(diffs[rng.integers(0, diffs.size, size=diffs.size)]))
        for _ in range(BOOTSTRAP_REPS)
    ]
    return {
        "N": int(diffs.size),
        "Diff": point,
        "CI95Low": float(np.quantile(samples, 0.025)),
        "CI95High": float(np.quantile(samples, 0.975)),
    }


def compute_primary_effects(
    events: pd.DataFrame,
    retention: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Compute displacement-minus-sweep paired effects by proxy."""
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        for segment in ("Train", "Test"):
            group = events[
                (events["Instrument"] == instrument)
                & (events["Segment"] == segment)
            ]
            floor = bool(
                retention[
                    (retention["Instrument"] == instrument)
                    & (retention["Segment"] == segment)
                ]["EventFloorMet"].any()
            )
            wide = group.pivot_table(
                index=["SweepTime", "LevelType", "Side"],
                columns="EntryProxy",
                values=["Return_R_60m", "Hit1R_60m"],
                aggfunc="first",
            )
            for proxy in ("DisplacementClose", "NextOpen"):
                if wide.empty or ("Return_R_60m", proxy) not in wide:
                    ret_stats = {"N": 0, "Diff": np.nan, "CI95Low": np.nan, "CI95High": np.nan}
                    hit_stats = {"N": 0, "Diff": np.nan, "CI95Low": np.nan, "CI95High": np.nan}
                else:
                    ret_stats = paired_bootstrap_diff(
                        wide[("Return_R_60m", "SweepClose")].to_numpy(dtype=float),
                        wide[("Return_R_60m", proxy)].to_numpy(dtype=float),
                        rng,
                    )
                    hit_stats = paired_bootstrap_diff(
                        wide[("Hit1R_60m", "SweepClose")].to_numpy(dtype=float),
                        wide[("Hit1R_60m", proxy)].to_numpy(dtype=float),
                        rng,
                    )
                rows.append(
                    {
                        "Instrument": instrument,
                        "Segment": segment,
                        "EntryProxy": proxy,
                        "EventFloorMet": floor,
                        "ReturnN": ret_stats["N"],
                        "ReturnDiff": ret_stats["Diff"],
                        "ReturnCI95Low": ret_stats["CI95Low"],
                        "ReturnCI95High": ret_stats["CI95High"],
                        "HitN": hit_stats["N"],
                        "HitDiff": hit_stats["Diff"],
                        "HitCI95Low": hit_stats["CI95Low"],
                        "HitCI95High": hit_stats["CI95High"],
                        "ReturnCriterionMet": bool(
                            floor
                            and np.isfinite(ret_stats["Diff"])
                            and ret_stats["Diff"] >= IMPROVEMENT_THRESHOLD
                        ),
                        "HitCriterionMet": bool(
                            floor
                            and np.isfinite(hit_stats["Diff"])
                            and hit_stats["Diff"] >= IMPROVEMENT_THRESHOLD
                        ),
                    }
                )
    return pd.DataFrame(rows)


def evaluate_verdict(filter_effects: pd.DataFrame) -> dict[str, Any]:
    """Map scoped criteria to FOR/AGAINST/INCONCLUSIVE using interval evidence.

    Primary test: displacement-confirmed sweeps vs full EXP-015 sweep
    population (unpaired nested bootstrap). FOR/AGAINST decisions are made
    on test-segment intervals; train-only positives no longer veto AGAINST.
    """
    per_instrument: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        test_rows = filter_effects[
            (filter_effects["Instrument"] == instrument)
            & (filter_effects["Segment"] == "Test")
        ]
        train_rows = filter_effects[
            (filter_effects["Instrument"] == instrument)
            & (filter_effects["Segment"] == "Train")
        ]
        if test_rows.empty or train_rows.empty:
            per_instrument.append(
                {
                    "Instrument": instrument,
                    "RetentionFloorMet": False,
                    "TestPass": False,
                    "TestRefutes": False,
                }
            )
            continue
        test = test_rows.iloc[0]
        train = train_rows.iloc[0]
        floor_met = bool(test["RetentionFloorMet"]) and bool(train["RetentionFloorMet"])
        test_pass = bool(
            floor_met
            and (bool(test["HitCriterionMet"]) or bool(test["MAECriterionMet"]))
        )
        test_refutes = bool(
            floor_met
            and bool(test["HitNegativeRefutes"])
            and bool(test["MAENegativeRefutes"])
        )
        per_instrument.append(
            {
                "Instrument": instrument,
                "RetentionFloorMet": floor_met,
                "TestPass": test_pass,
                "TestRefutes": test_refutes,
            }
        )
    verdict_df = pd.DataFrame(per_instrument)
    passing = int(verdict_df["TestPass"].sum())
    refuting = int(verdict_df["TestRefutes"].sum())
    floor_count = int(verdict_df["RetentionFloorMet"].sum())
    if passing >= 3:
        verdict = "FOR"
    elif refuting >= 3:
        verdict = "AGAINST"
    elif floor_count < 3:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "INCONCLUSIVE"
    return {
        "verdict": verdict,
        "instruments_passing": passing,
        "instruments_refuting": refuting,
        "instruments_with_retention_floor": floor_count,
        "per_instrument": per_instrument,
    }


def _json_safe(value: Any) -> Any:
    """Convert numpy/pandas values to JSON-safe scalars."""
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    if pd.isna(value):
        return None
    return value


def plot_count_waterfall(retention: pd.DataFrame, save_path: Path) -> None:
    """Plot sweep versus displacement-confirmed event counts."""
    plot_df = retention.melt(
        id_vars=["Instrument", "Segment"],
        value_vars=["SweepN", "ConfirmedN"],
        var_name="Stage",
        value_name="Count",
    )
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=False)
    for ax, segment in zip(axes, ("Train", "Test")):
        sub = plot_df[plot_df["Segment"] == segment]
        sns.barplot(
            data=sub,
            x="Instrument",
            y="Count",
            hue="Stage",
            order=INSTRUMENTS,
            ax=ax,
        )
        ax.set_title(f"EXP-018 Sweep to Displacement Counts - {segment}")
        ax.set_xlabel("")
        ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_effect_intervals(effects: pd.DataFrame, save_path: Path) -> None:
    """Plot paired effect intervals for delayed entry proxies."""
    plot_df = effects[effects["Segment"].isin(["Train", "Test"])].copy()
    plot_df["Label"] = (
        plot_df["Instrument"] + " " + plot_df["Segment"] + " " + plot_df["EntryProxy"]
    )
    y = np.arange(len(plot_df))
    point = plot_df["ReturnDiff"].to_numpy(dtype=float)
    low = plot_df["ReturnCI95Low"].to_numpy(dtype=float)
    high = plot_df["ReturnCI95High"].to_numpy(dtype=float)
    err_low = np.where(np.isfinite(point - low), np.maximum(point - low, 0.0), 0.0)
    err_high = np.where(np.isfinite(high - point), np.maximum(high - point, 0.0), 0.0)
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.errorbar(point, y, xerr=[err_low, err_high], fmt="o", capsize=3, color="steelblue")
    ax.axvline(0.0, color="black", linewidth=1)
    ax.axvline(IMPROVEMENT_THRESHOLD, color="green", linestyle="--", linewidth=1)
    ax.set_yticks(y)
    ax.set_yticklabels(plot_df["Label"])
    ax.set_xlabel("Entry proxy minus sweep-close Return_R_60m")
    ax.set_title("EXP-018 Paired Return Effect Intervals")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_mfe_mae(events: pd.DataFrame, save_path: Path) -> None:
    """Plot 60-minute MFE/MAE distributions by entry proxy."""
    if events.empty:
        return
    plot_df = events.copy()
    plot_df["MFE_R_60m"] = plot_df["MFE_R_60m"].clip(upper=PLOT_R_CAP)
    plot_df["MAE_R_60m"] = plot_df["MAE_R_60m"].clip(upper=PLOT_R_CAP)
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=False)
    for ax, col in zip(axes, ("MFE_R_60m", "MAE_R_60m")):
        sns.boxplot(
            data=plot_df,
            x="Instrument",
            y=col,
            hue="EntryProxy",
            order=INSTRUMENTS,
            showfliers=False,
            ax=ax,
        )
        ax.set_title(f"EXP-018 {col} by Entry Proxy (capped at {PLOT_R_CAP}R)")
        ax.set_xlabel("")
        ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_filter_effect_intervals(filter_effects: pd.DataFrame, save_path: Path) -> None:
    """Plot confirmed-vs-all-sweep filter effects with CI95 intervals."""
    if filter_effects.empty:
        return
    plot_df = filter_effects.copy()
    plot_df["Label"] = plot_df["Instrument"] + " " + plot_df["Segment"]
    y = np.arange(len(plot_df))

    def _bounds(point: np.ndarray, low: np.ndarray, high: np.ndarray):
        err_low = np.where(np.isfinite(point - low), np.maximum(point - low, 0.0), 0.0)
        err_high = np.where(np.isfinite(high - point), np.maximum(high - point, 0.0), 0.0)
        return err_low, err_high

    hit_point = plot_df["HitDiff"].to_numpy(dtype=float)
    hit_err_low, hit_err_high = _bounds(
        hit_point,
        plot_df["HitCI95Low"].to_numpy(dtype=float),
        plot_df["HitCI95High"].to_numpy(dtype=float),
    )
    mae_point = plot_df["MAEImprovement"].to_numpy(dtype=float)
    mae_err_low, mae_err_high = _bounds(
        mae_point,
        plot_df["MAECI95Low"].to_numpy(dtype=float),
        plot_df["MAECI95High"].to_numpy(dtype=float),
    )

    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
    axes[0].errorbar(hit_point, y, xerr=[hit_err_low, hit_err_high], fmt="o",
                     color="steelblue", ecolor="0.35", capsize=3)
    axes[0].axvline(0.0, color="black", linewidth=1)
    axes[0].axvline(HIT_THRESHOLD, color="green", linestyle="--", linewidth=1)
    axes[0].set_yticks(y); axes[0].set_yticklabels(plot_df["Label"])
    axes[0].set_xlabel("Confirmed minus all-sweep Hit1R_60m")
    axes[0].set_title("EXP-018 Filter Effect: Hit1R")
    axes[1].errorbar(mae_point, y, xerr=[mae_err_low, mae_err_high], fmt="o",
                     color="darkorange", ecolor="0.35", capsize=3)
    axes[1].axvline(0.0, color="black", linewidth=1)
    axes[1].axvline(MAE_IMPROVEMENT_THRESHOLD, color="green", linestyle="--", linewidth=1)
    axes[1].set_xlabel("All-sweep minus confirmed median MAE_R_60m")
    axes[1].set_title("EXP-018 Filter Effect: Median MAE Improvement")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_delay_distribution(misses: pd.DataFrame, save_path: Path) -> None:
    """Plot delay from sweep close to displacement close."""
    confirmed = misses[misses["Confirmed"]].copy()
    if confirmed.empty:
        return
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.histplot(data=confirmed, x="DelayBars", hue="Instrument", discrete=True, ax=ax)
    ax.set_title("EXP-018 Sweep-to-Displacement Delay")
    ax.set_xlabel("Bars after sweep")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def write_outputs(
    events: pd.DataFrame,
    misses: pd.DataFrame,
    retention: pd.DataFrame,
    outcome_summary: pd.DataFrame,
    effects: pd.DataFrame,
    filter_effects: pd.DataFrame,
    verdict: dict[str, Any],
    plots_dir: Path,
    results_dir: Path,
) -> None:
    """Write EXP-018 result tables, JSON summary, text summary, and plots."""
    events.to_csv(results_dir / "entry_proxy_events.csv", index=False)
    misses.to_csv(results_dir / "displacement_detection.csv", index=False)
    retention.to_csv(results_dir / "retention_summary.csv", index=False)
    outcome_summary.to_csv(results_dir / "outcome_summary.csv", index=False)
    effects.to_csv(results_dir / "primary_effects.csv", index=False)
    filter_effects.to_csv(results_dir / "filter_effects.csv", index=False)

    payload = {
        "experiment_id": "EXP-018",
        "title": "Displacement Confirmation Added to Sweeps",
        "bootstrap_reps": BOOTSTRAP_REPS,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "definition": (
            "After each EXP-015 failed sweep, the first candle within 10 bars "
            "whose body is at least 1.5 times the prior 100-bar median absolute "
            "body and whose close is in the directional quartile confirms "
            "displacement."
        ),
        "primary_test_definition": (
            "filter_effects.csv compares displacement-confirmed-sweep outcomes "
            "(Hit1R_60m mean, MAE_R_60m median) against the full EXP-015 sweep "
            "population using a nested-subset bootstrap. CI95-low must clear "
            "the predeclared threshold to pass; CI95-high below the threshold "
            "counts as refutation on that metric. The verdict requires both "
            "Hit and MAE intervals to refute before declaring AGAINST."
        ),
        "secondary_test_definition": (
            "primary_effects.csv is the paired delay-cost diagnostic: "
            "DisplacementClose / NextOpen entry vs SweepClose entry on the "
            "same displacement-confirmed events. It is NOT the primary "
            "scope test and does not drive the verdict."
        ),
        "entry_proxy_definition": (
            "SweepClose, DisplacementClose, and NextOpen use the same EXP-015 "
            "stop convention; Risk1R is recomputed as abs(stop - entry)."
        ),
        "verdict_summary": verdict,
        "retention_summary": retention.to_dict(orient="records"),
        "filter_effects": filter_effects.to_dict(orient="records"),
        "paired_delay_effects": effects.to_dict(orient="records"),
    }
    with (results_dir / "results.json").open("w", encoding="utf-8") as handle:
        json.dump(_json_safe(payload), handle, indent=2, default=str, allow_nan=False)

    with (results_dir / "numerical_summary.txt").open("w", encoding="utf-8") as handle:
        handle.write("EXP-018 Displacement Confirmation Added to Sweeps\n")
        handle.write(f"Verdict: {verdict['verdict']}\n")
        handle.write(
            f"Instruments passing: {verdict['instruments_passing']}/4; "
            f"refuting: {verdict['instruments_refuting']}/4; "
            f"retention floor met: {verdict['instruments_with_retention_floor']}/4\n\n"
        )
        handle.write("Test-segment filter effects (confirmed vs all EXP-015 sweeps):\n")
        for row in filter_effects[filter_effects["Segment"] == "Test"].itertuples(index=False):
            handle.write(
                f"- {row.Instrument}: confirmed={row.ConfirmedSweepN}/{row.TotalSweepN} "
                f"({row.RetentionPct:.1%}), hit_diff={row.HitDiff:.3f} "
                f"CI=[{row.HitCI95Low:.3f}, {row.HitCI95High:.3f}], "
                f"mae_impr={row.MAEImprovement:.3f} "
                f"CI=[{row.MAECI95Low:.3f}, {row.MAECI95High:.3f}], "
                f"floor={row.RetentionFloorMet}, "
                f"hit_pass={row.HitCriterionMet}, mae_pass={row.MAECriterionMet}\n"
            )
        handle.write("\nTest-segment paired delay-cost (DisplacementClose - SweepClose):\n")
        for row in effects[effects["Segment"] == "Test"].itertuples(index=False):
            handle.write(
                f"- {row.Instrument} {row.EntryProxy}: n={row.ReturnN}, "
                f"return_diff={row.ReturnDiff:.3f} "
                f"CI=[{row.ReturnCI95Low:.3f}, {row.ReturnCI95High:.3f}], "
                f"hit_diff={row.HitDiff:.3f} "
                f"CI=[{row.HitCI95Low:.3f}, {row.HitCI95High:.3f}]\n"
            )

    plot_count_waterfall(retention, plots_dir / "01_sweep_to_displacement_counts.png")
    plot_filter_effect_intervals(filter_effects, plots_dir / "02_filter_effect_intervals.png")
    plot_effect_intervals(effects, plots_dir / "03_entry_proxy_delay_intervals.png")
    plot_mfe_mae(events, plots_dir / "04_mfe_mae_distributions.png")
    plot_delay_distribution(misses, plots_dir / "05_delay_distribution.png")


def run_experiment() -> None:
    """Execute the EXP-018 displacement-confirmation workflow."""
    plots_dir = EXP_DIR / "plots"
    results_dir = EXP_DIR / "results"
    plots_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    sweeps = load_sweep_events()
    if sweeps.empty:
        raise ValueError("No EXP-015 failed-sweep events were available.")

    bars_by_instrument = {
        instrument: load_instrument_bars(instrument)
        for instrument in INSTRUMENTS
    }
    entries, misses = detect_confirmed_entries(sweeps, bars_by_instrument)
    if entries.empty:
        raise ValueError("No displacement-confirmed entry proxies were detected.")

    events = append_outcomes(entries, bars_by_instrument)
    retention = summarize_retention(sweeps, misses)
    outcome_summary = summarize_outcomes(events)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    effects = compute_primary_effects(events, retention, rng)

    # Build sweeps annotated with a DisplacementConfirmed flag so the primary
    # test can compare confirmed-sweep outcomes against the FULL EXP-015 sweep
    # population (the actual scope question), not against the same events
    # entered at sweep close.
    sweep_key = ["Instrument", "NYDate", "CloseTime", "LevelType", "Side"]
    miss_key_cols = ["Instrument", "NYDate", "SweepTime", "LevelType", "Side"]
    confirmed_keys = (
        misses.loc[misses["Confirmed"], miss_key_cols]
        .rename(columns={"SweepTime": "CloseTime"})
        .drop_duplicates()
        .assign(DisplacementConfirmed=True)
    )
    confirmed_keys["CloseTime"] = pd.to_datetime(confirmed_keys["CloseTime"])
    sweeps_with_confirm = sweeps.merge(
        confirmed_keys, on=sweep_key, how="left", validate="m:1"
    )
    sweeps_with_confirm["DisplacementConfirmed"] = (
        sweeps_with_confirm["DisplacementConfirmed"].fillna(False).astype(bool)
    )
    filter_effects = compute_filter_effects(sweeps_with_confirm, rng)
    verdict = evaluate_verdict(filter_effects)

    write_outputs(
        events,
        misses,
        retention,
        outcome_summary,
        effects,
        filter_effects,
        verdict,
        plots_dir,
        results_dir,
    )

    print("EXP-018 complete.")
    print(f"Verdict: {verdict['verdict']} ({verdict['instruments_passing']}/4 instruments)")
    print(f"Plots:   {plots_dir}")
    print(f"Results: {results_dir}")


def main() -> None:
    """Entry point for manual execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_experiment()


if __name__ == "__main__":
    main()
