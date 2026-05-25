"""
Experiment EXP-019: Micro Swing Break Confirmation After Sweep
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
EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-019"
EXP015_RESULTS_DIR = PYTHON_ROOT / "experiments" / "EXP-015" / "results"
EXP018_RESULTS_DIR = PYTHON_ROOT / "experiments" / "EXP-018" / "results"

BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 42
SWING_LEFT_RIGHT = 2
MIN_CONFIRMED_EVENTS = 50
RETURN_IMPROVEMENT_THRESHOLD = 0.25
MAE_IMPROVEMENT_THRESHOLD = 0.25
EXCESSIVE_DELAY_BARS = 60
PLOT_R_CAP = 8.0

SWEEP_COLS = {
    "Instrument",
    "NYDate",
    "Segment",
    "CloseTime",
    "Close",
    "Side",
    "EventType",
    "LevelType",
    "Stop",
}
BASELINE_COLS = {
    "Instrument",
    "Segment",
    "SweepTime",
    "LevelType",
    "Side",
    "EntryProxy",
    "Return_R_60m",
    "MAE_R_60m",
}


def require_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    """Raise if a prerequisite artifact lacks required columns."""
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{label} is missing required columns: {missing}")


def load_sweep_events() -> pd.DataFrame:
    """Load EXP-015 failed-sweep events used as the fixed event universe."""
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
    return events.sort_values(
        ["Instrument", "Segment", "CloseTime", "LevelType", "Side"]
    ).reset_index(drop=True)


def load_exp018_baseline() -> pd.DataFrame:
    """Load EXP-018 displacement-close rows for the fixed comparison baseline."""
    path = EXP018_RESULTS_DIR / "entry_proxy_events.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Required EXP-018 baseline not found: {path}. Run EXP-018 first."
        )
    baseline = pd.read_csv(path)
    require_columns(baseline, BASELINE_COLS, "EXP-018 entry_proxy_events.csv")
    baseline = baseline[baseline["EntryProxy"] == "DisplacementClose"].copy()
    baseline["SweepTime"] = pd.to_datetime(baseline["SweepTime"])
    return baseline.reset_index(drop=True)


def load_instrument_bars(instrument: str) -> pd.DataFrame:
    """Load holdout-excluded analysis bars for one instrument.

    Only Segment labelling is needed; NY/macro features are skipped as
    EXP-019 reads neither.
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
    return bars.reset_index(drop=True)


def detect_confirmed_swings(bars: pd.DataFrame, instrument: str) -> pd.DataFrame:
    """Detect two-left/two-right swings with causal usable timestamps."""
    rows: list[dict[str, Any]] = []
    highs = bars["High"].to_numpy(dtype=float)
    lows = bars["Low"].to_numpy(dtype=float)
    for idx in range(SWING_LEFT_RIGHT, len(bars) - SWING_LEFT_RIGHT):
        left = slice(idx - SWING_LEFT_RIGHT, idx)
        right = slice(idx + 1, idx + SWING_LEFT_RIGHT + 1)
        pivot_high = highs[idx]
        pivot_low = lows[idx]
        usable_idx = idx + SWING_LEFT_RIGHT
        if pivot_high > np.max(highs[left]) and pivot_high > np.max(highs[right]):
            rows.append(
                {
                    "Instrument": instrument,
                    "SwingType": "High",
                    "PivotIndex": idx,
                    "PivotTime": bars.iloc[idx]["CloseTime"],
                    "UsableIndex": usable_idx,
                    "UsableTime": bars.iloc[usable_idx]["CloseTime"],
                    "SwingPrice": float(pivot_high),
                    "Segment": bars.iloc[usable_idx]["Segment"],
                }
            )
        if pivot_low < np.min(lows[left]) and pivot_low < np.min(lows[right]):
            rows.append(
                {
                    "Instrument": instrument,
                    "SwingType": "Low",
                    "PivotIndex": idx,
                    "PivotTime": bars.iloc[idx]["CloseTime"],
                    "UsableIndex": usable_idx,
                    "UsableTime": bars.iloc[usable_idx]["CloseTime"],
                    "SwingPrice": float(pivot_low),
                    "Segment": bars.iloc[usable_idx]["Segment"],
                }
            )
    return pd.DataFrame(rows)


def _latest_usable_swing(
    swings: pd.DataFrame,
    swing_type: str,
    close_time: pd.Timestamp,
) -> pd.Series | None:
    """Return the most recent swing usable before a candidate break bar.

    Segment is NOT a filter here. A swing whose UsableTime falls in Train
    can be used to detect a break in Test, matching production behaviour
    where any prior confirmed swing is available. The break event itself
    is still tagged by the break candle's segment for downstream grouping.
    """
    subset = swings[
        (swings["SwingType"] == swing_type)
        & (swings["UsableTime"] < close_time)
    ]
    if subset.empty:
        return None
    return subset.sort_values("UsableTime").iloc[-1]


def find_swing_break_for_sweep(
    sweep: pd.Series,
    bars: pd.DataFrame,
    swings: pd.DataFrame,
    close_ns: np.ndarray,
) -> dict[str, Any]:
    """Find the first post-sweep close through the latest usable swing.

    Scanning continues past segment boundaries; an event is labelled by the
    break candle's segment, not the sweep's. Crossing the segment boundary
    is allowed because in production the algorithm has no concept of the
    Train/Test split. Cross-segment events are flagged on the miss row for
    downstream auditing.
    """
    event_ns = int(pd.Timestamp(sweep["CloseTime"]).value)
    start_idx = int(np.searchsorted(close_ns, event_ns, side="right"))
    sweep_segment = str(sweep["Segment"])
    swing_type = "Low" if sweep["Side"] == "High" else "High"
    if start_idx >= len(bars):
        return {"Confirmed": False, "MissReason": "NO_FORWARD_BARS"}

    for idx in range(start_idx, len(bars)):
        candidate = bars.iloc[idx]
        swing = _latest_usable_swing(
            swings,
            swing_type,
            pd.Timestamp(candidate["CloseTime"]),
        )
        if swing is None:
            continue
        bearish_break = sweep["Side"] == "High" and candidate["Close"] < swing["SwingPrice"]
        bullish_break = sweep["Side"] == "Low" and candidate["Close"] > swing["SwingPrice"]
        if bearish_break or bullish_break:
            break_segment = str(candidate["Segment"])
            return {
                "Confirmed": True,
                "MissReason": "NONE",
                "SwingType": swing_type,
                "SwingPivotTime": swing["PivotTime"],
                "SwingUsableTime": swing["UsableTime"],
                "SwingPrice": float(swing["SwingPrice"]),
                "BreakTime": candidate["CloseTime"],
                "BreakSegment": break_segment,
                "CrossSegment": break_segment != sweep_segment,
                "BreakClose": float(candidate["Close"]),
                "DelayBars": idx - start_idx + 1,
                "SwingConfirmationDelayBars": int(swing["UsableIndex"] - swing["PivotIndex"]),
            }
    return {"Confirmed": False, "MissReason": "NO_SWING_BREAK_FOUND"}


def build_swing_break_events(
    sweeps: pd.DataFrame,
    bars_by_instrument: dict[str, pd.DataFrame],
    swings_by_instrument: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Detect first qualifying swing-break events after EXP-015 sweeps."""
    events: list[dict[str, Any]] = []
    misses: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        bars = bars_by_instrument[instrument]
        swings = swings_by_instrument[instrument]
        close_ns = bars["CloseTime"].values.astype(np.int64)
        inst_sweeps = sweeps[sweeps["Instrument"] == instrument]
        for _, sweep in inst_sweeps.iterrows():
            confirmation = find_swing_break_for_sweep(sweep, bars, swings, close_ns)
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
            if not confirmation["Confirmed"]:
                continue
            entry = confirmation["BreakClose"]
            stop = float(sweep["Stop"])
            events.append(
                {
                    "Instrument": instrument,
                    "NYDate": sweep["NYDate"],
                    "Segment": sweep["Segment"],
                    "LevelType": sweep["LevelType"],
                    "Side": sweep["Side"],
                    "SweepTime": sweep["CloseTime"],
                    "SwingType": confirmation["SwingType"],
                    "SwingPivotTime": confirmation["SwingPivotTime"],
                    "SwingUsableTime": confirmation["SwingUsableTime"],
                    "SwingPrice": confirmation["SwingPrice"],
                    "BreakTime": confirmation["BreakTime"],
                    "DelayBars": confirmation["DelayBars"],
                    "EntryProxy": "SwingBreakClose",
                    "EntryTime": confirmation["BreakTime"],
                    "Entry": entry,
                    "Stop": stop,
                    "Risk1R": abs(stop - entry),
                }
            )
    return pd.DataFrame(events), pd.DataFrame(misses)


def append_outcomes(
    events: pd.DataFrame,
    bars_by_instrument: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Append 60-minute real-price outcomes to swing-break events."""
    rows: list[dict[str, Any]] = []
    for _, event in events.iterrows():
        bars = bars_by_instrument[str(event["Instrument"])]
        outcome = compute_real_price_outcome(event, bars, horizon_minutes=60)
        rows.append({**event.to_dict(), **outcome})
    return pd.DataFrame(rows)


def summarize_counts(
    sweeps: pd.DataFrame,
    baseline: pd.DataFrame,
    swing_events: pd.DataFrame,
    misses: pd.DataFrame,
) -> pd.DataFrame:
    """Count sweep-only, EXP-018 displacement, and swing-break events."""
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        for segment in ("Train", "Test"):
            sweep_n = len(sweeps[(sweeps["Instrument"] == instrument) & (sweeps["Segment"] == segment)])
            disp_n = len(
                baseline[
                    (baseline["Instrument"] == instrument)
                    & (baseline["Segment"] == segment)
                ]
            )
            swing_n = len(
                swing_events[
                    (swing_events["Instrument"] == instrument)
                    & (swing_events["Segment"] == segment)
                ]
            )
            delay = misses[
                (misses["Instrument"] == instrument)
                & (misses["Segment"] == segment)
                & (misses["Confirmed"])
            ]["DelayBars"].dropna()
            rows.append(
                {
                    "Instrument": instrument,
                    "Segment": segment,
                    "SweepN": sweep_n,
                    "DisplacementN": disp_n,
                    "SwingBreakN": swing_n,
                    "SwingBreakRetentionPct": swing_n / sweep_n if sweep_n else np.nan,
                    "EventFloorMet": swing_n >= MIN_CONFIRMED_EVENTS,
                    "MedianDelayBars": float(delay.median()) if delay.size else np.nan,
                    "ExcessiveDelay": bool(delay.size and delay.median() > EXCESSIVE_DELAY_BARS),
                }
            )
    return pd.DataFrame(rows)


def paired_bootstrap_diff(
    base: np.ndarray,
    variant: np.ndarray,
    rng: np.random.Generator,
    use_median: bool = False,
) -> dict[str, float]:
    """Bootstrap paired variant-minus-baseline difference (mean or median).

    `use_median=True` is required when the scope criterion is stated on a
    median (e.g., median MAE_R_60m). Using mean for a median criterion
    silently substitutes a heavy-tail-sensitive statistic.
    """
    stat_fn = np.median if use_median else np.mean
    valid = np.isfinite(base) & np.isfinite(variant)
    base = base[valid]
    variant = variant[valid]
    if base.size == 0:
        return {"N": 0, "Diff": np.nan, "CI95Low": np.nan, "CI95High": np.nan}
    diffs = variant - base
    point = float(stat_fn(diffs))
    if diffs.size < 2:
        return {"N": int(diffs.size), "Diff": point, "CI95Low": np.nan, "CI95High": np.nan}
    samples = [
        float(stat_fn(diffs[rng.integers(0, diffs.size, size=diffs.size)]))
        for _ in range(BOOTSTRAP_REPS)
    ]
    return {
        "N": int(diffs.size),
        "Diff": point,
        "CI95Low": float(np.quantile(samples, 0.025)),
        "CI95High": float(np.quantile(samples, 0.975)),
    }


def build_baseline_comparison(
    baseline: pd.DataFrame,
    swing_events: pd.DataFrame,
) -> pd.DataFrame:
    """Match swing-break events to EXP-018 displacement baseline by sweep key."""
    keys = ["Instrument", "Segment", "SweepTime", "LevelType", "Side"]
    base = baseline.copy()
    swing = swing_events.copy()
    base["SweepTime"] = pd.to_datetime(base["SweepTime"])
    swing["SweepTime"] = pd.to_datetime(swing["SweepTime"])
    return swing.merge(
        base[
            keys
            + [
                "Return_R_60m",
                "MAE_R_60m",
                "Entry",
                "EntryTime",
            ]
        ].rename(
            columns={
                "Return_R_60m": "BaselineReturn_R_60m",
                "MAE_R_60m": "BaselineMAE_R_60m",
                "Entry": "BaselineEntry",
                "EntryTime": "BaselineEntryTime",
            }
        ),
        on=keys,
        how="inner",
        validate="1:1",
    )


def compute_primary_effects(
    comparison: pd.DataFrame,
    counts: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Compute swing-break minus EXP-018 baseline effects.

    MAE uses a paired *median* bootstrap (the scope criterion is on the
    median, not the mean). Criteria require CI95-low to clear the
    predeclared threshold; point estimates alone are insufficient.

    The retention floor used here is `MatchedN` (the actual matched sample
    feeding the bootstrap), not the raw swing-break count from `counts`,
    so an instrument cannot pass the floor on counts while the bootstrap
    runs on a small subset.
    """
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        for segment in ("Train", "Test"):
            group = comparison[
                (comparison["Instrument"] == instrument)
                & (comparison["Segment"] == segment)
            ]
            count_row = counts[
                (counts["Instrument"] == instrument)
                & (counts["Segment"] == segment)
            ]
            excessive_delay = bool(count_row["ExcessiveDelay"].any())
            ret_stats = paired_bootstrap_diff(
                group["BaselineReturn_R_60m"].to_numpy(dtype=float),
                group["Return_R_60m"].to_numpy(dtype=float),
                rng,
                use_median=False,
            )
            mae_stats = paired_bootstrap_diff(
                group["MAE_R_60m"].to_numpy(dtype=float),
                group["BaselineMAE_R_60m"].to_numpy(dtype=float),
                rng,
                use_median=True,
            )
            matched_n = int(ret_stats["N"])
            floor = bool(matched_n >= MIN_CONFIRMED_EVENTS)
            rows.append(
                {
                    "Instrument": instrument,
                    "Segment": segment,
                    "MatchedN": matched_n,
                    "EventFloorMet": floor,
                    "ExcessiveDelay": excessive_delay,
                    "ReturnDiff": ret_stats["Diff"],
                    "ReturnCI95Low": ret_stats["CI95Low"],
                    "ReturnCI95High": ret_stats["CI95High"],
                    "MAEImprovement": mae_stats["Diff"],
                    "MAECI95Low": mae_stats["CI95Low"],
                    "MAECI95High": mae_stats["CI95High"],
                    "ReturnCriterionMet": bool(
                        floor
                        and not excessive_delay
                        and np.isfinite(ret_stats["CI95Low"])
                        and ret_stats["CI95Low"] >= RETURN_IMPROVEMENT_THRESHOLD
                    ),
                    "MAECriterionMet": bool(
                        floor
                        and not excessive_delay
                        and np.isfinite(mae_stats["CI95Low"])
                        and mae_stats["CI95Low"] >= MAE_IMPROVEMENT_THRESHOLD
                    ),
                    "ReturnRefutes": bool(
                        floor
                        and np.isfinite(ret_stats["CI95High"])
                        and ret_stats["CI95High"] < RETURN_IMPROVEMENT_THRESHOLD
                    ),
                    "MAERefutes": bool(
                        floor
                        and np.isfinite(mae_stats["CI95High"])
                        and mae_stats["CI95High"] < MAE_IMPROVEMENT_THRESHOLD
                    ),
                }
            )
    return pd.DataFrame(rows)


def evaluate_verdict(effects: pd.DataFrame) -> dict[str, Any]:
    """Map scoped success criteria to a FOR/AGAINST/INCONCLUSIVE verdict.

    Decision uses interval evidence on the matched paired bootstrap. A
    test-segment metric passes when its CI95-low clears the threshold; a
    test-segment metric refutes when its CI95-high is strictly below the
    threshold. An instrument refutes when both metrics refute on test.
    Wide intervals that neither pass nor refute map to INCONCLUSIVE.
    """
    per_instrument: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        train = effects[(effects["Instrument"] == instrument) & (effects["Segment"] == "Train")]
        test = effects[(effects["Instrument"] == instrument) & (effects["Segment"] == "Test")]
        floor_met = bool(
            not train.empty
            and not test.empty
            and train["EventFloorMet"].iloc[0]
            and test["EventFloorMet"].iloc[0]
        )
        excessive_delay = bool(
            (not train.empty and train["ExcessiveDelay"].iloc[0])
            or (not test.empty and test["ExcessiveDelay"].iloc[0])
        )
        pass_flag = bool(
            floor_met
            and not excessive_delay
            and not test.empty
            and (test["ReturnCriterionMet"].iloc[0] or test["MAECriterionMet"].iloc[0])
        )
        refutes = bool(
            floor_met
            and not test.empty
            and test["ReturnRefutes"].iloc[0]
            and test["MAERefutes"].iloc[0]
        )
        per_instrument.append(
            {
                "Instrument": instrument,
                "EventFloorMet": floor_met,
                "ExcessiveDelay": excessive_delay,
                "Pass": pass_flag,
                "Refutes": refutes,
            }
        )
    verdict_df = pd.DataFrame(per_instrument)
    passing = int(verdict_df["Pass"].sum())
    refuting = int(verdict_df["Refutes"].sum())
    floor_count = int(verdict_df["EventFloorMet"].sum())
    excessive_delay_count = int(verdict_df["ExcessiveDelay"].sum())
    if passing >= 3:
        verdict = "FOR"
    elif floor_count < 3:
        verdict = "INCONCLUSIVE"
    elif excessive_delay_count >= 3:
        verdict = "AGAINST"
    elif refuting >= 3:
        verdict = "AGAINST"
    else:
        verdict = "INCONCLUSIVE"
    return {
        "verdict": verdict,
        "instruments_passing": passing,
        "instruments_refuting": refuting,
        "instruments_with_event_floor": floor_count,
        "instruments_with_excessive_delay": excessive_delay_count,
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


def plot_delay_distribution(swing_events: pd.DataFrame, save_path: Path) -> None:
    """Plot swing confirmation delay after sweeps."""
    if swing_events.empty:
        return
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.boxplot(
        data=swing_events,
        x="Instrument",
        y="DelayBars",
        hue="Segment",
        order=INSTRUMENTS,
        showfliers=False,
        ax=ax,
    )
    ax.axhline(EXCESSIVE_DELAY_BARS, color="firebrick", linestyle="--", linewidth=1)
    ax.set_title("EXP-019 Swing-Break Confirmation Delay")
    ax.set_xlabel("")
    ax.set_ylabel("Bars after sweep")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_event_counts(counts: pd.DataFrame, save_path: Path) -> None:
    """Plot event count comparison across sweep, displacement, and swing break."""
    plot_df = counts.melt(
        id_vars=["Instrument", "Segment"],
        value_vars=["SweepN", "DisplacementN", "SwingBreakN"],
        var_name="Stage",
        value_name="Count",
    )
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=False)
    for ax, segment in zip(axes, ("Train", "Test")):
        sub = plot_df[plot_df["Segment"] == segment]
        sns.barplot(data=sub, x="Instrument", y="Count", hue="Stage", order=INSTRUMENTS, ax=ax)
        ax.set_title(f"EXP-019 Event Counts - {segment}")
        ax.set_xlabel("")
        ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_primary_effects(effects: pd.DataFrame, save_path: Path) -> None:
    """Plot swing-break minus displacement return intervals."""
    plot_df = effects.copy()
    plot_df["Label"] = plot_df["Instrument"] + " " + plot_df["Segment"]
    y = np.arange(len(plot_df))
    point = plot_df["ReturnDiff"].to_numpy(dtype=float)
    low = plot_df["ReturnCI95Low"].to_numpy(dtype=float)
    high = plot_df["ReturnCI95High"].to_numpy(dtype=float)
    err_low = np.where(np.isfinite(point - low), np.maximum(point - low, 0.0), 0.0)
    err_high = np.where(np.isfinite(high - point), np.maximum(high - point, 0.0), 0.0)
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.errorbar(point, y, xerr=[err_low, err_high], fmt="o", color="steelblue", capsize=3)
    ax.axvline(0.0, color="black", linewidth=1)
    ax.axvline(RETURN_IMPROVEMENT_THRESHOLD, color="green", linestyle="--", linewidth=1)
    ax.set_yticks(y)
    ax.set_yticklabels(plot_df["Label"])
    ax.set_xlabel("Swing-break minus EXP-018 displacement Return_R_60m")
    ax.set_title("EXP-019 Primary Outcome Intervals")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_mae_distribution(comparison: pd.DataFrame, save_path: Path) -> None:
    """Plot matched MAE distributions for displacement and swing-break entries."""
    if comparison.empty:
        return
    base = comparison[["Instrument", "Segment", "BaselineMAE_R_60m"]].rename(
        columns={"BaselineMAE_R_60m": "MAE_R_60m"}
    )
    base["Variant"] = "EXP-018 displacement"
    swing = comparison[["Instrument", "Segment", "MAE_R_60m"]].copy()
    swing["Variant"] = "Swing break"
    plot_df = pd.concat([base, swing], ignore_index=True)
    plot_df["MAE_R_60m"] = plot_df["MAE_R_60m"].clip(upper=PLOT_R_CAP)
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for ax, segment in zip(axes, ("Train", "Test")):
        sub = plot_df[plot_df["Segment"] == segment]
        sns.boxplot(
            data=sub,
            x="Instrument",
            y="MAE_R_60m",
            hue="Variant",
            order=INSTRUMENTS,
            showfliers=False,
            ax=ax,
        )
        ax.set_title(f"EXP-019 Matched MAE - {segment}")
        ax.set_xlabel("")
        ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def write_outputs(
    swings: pd.DataFrame,
    misses: pd.DataFrame,
    swing_events: pd.DataFrame,
    counts: pd.DataFrame,
    comparison: pd.DataFrame,
    effects: pd.DataFrame,
    verdict: dict[str, Any],
    plots_dir: Path,
    results_dir: Path,
) -> None:
    """Write EXP-019 result tables, summaries, and plots."""
    swings.to_csv(results_dir / "confirmed_swings.csv", index=False)
    misses.to_csv(results_dir / "swing_break_detection.csv", index=False)
    swing_events.to_csv(results_dir / "swing_break_events.csv", index=False)
    counts.to_csv(results_dir / "event_counts.csv", index=False)
    comparison.to_csv(results_dir / "baseline_comparison.csv", index=False)
    effects.to_csv(results_dir / "primary_effects.csv", index=False)

    payload = {
        "experiment_id": "EXP-019",
        "title": "Micro Swing Break Confirmation After Sweep",
        "bootstrap_reps": BOOTSTRAP_REPS,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "definition": (
            "Two-left/two-right swing pivots become usable only at the second "
            "right-side confirmation bar. High-side sweeps require a later "
            "close below the most recent usable swing low; low-side sweeps "
            "require a later close above the most recent usable swing high."
        ),
        "baseline": str(EXP018_RESULTS_DIR / "entry_proxy_events.csv"),
        "verdict_summary": verdict,
        "event_counts": counts.to_dict(orient="records"),
        "primary_effects": effects.to_dict(orient="records"),
    }
    with (results_dir / "results.json").open("w", encoding="utf-8") as handle:
        json.dump(_json_safe(payload), handle, indent=2, default=str, allow_nan=False)

    with (results_dir / "numerical_summary.txt").open("w", encoding="utf-8") as handle:
        handle.write("EXP-019 Micro Swing Break Confirmation After Sweep\n")
        handle.write(f"Verdict: {verdict['verdict']}\n")
        handle.write(
            f"Instruments passing: {verdict['instruments_passing']}/4; "
            f"refuting: {verdict['instruments_refuting']}/4; "
            f"event floor met: {verdict['instruments_with_event_floor']}/4; "
            f"excessive delay: {verdict['instruments_with_excessive_delay']}/4\n\n"
        )
        handle.write("Test-segment primary effects:\n")
        for row in effects[effects["Segment"] == "Test"].itertuples(index=False):
            handle.write(
                f"- {row.Instrument}: matched={row.MatchedN}, "
                f"return_diff={row.ReturnDiff:.3f} "
                f"CI=[{row.ReturnCI95Low:.3f}, {row.ReturnCI95High:.3f}], "
                f"mae_impr={row.MAEImprovement:.3f} "
                f"CI=[{row.MAECI95Low:.3f}, {row.MAECI95High:.3f}], "
                f"floor={row.EventFloorMet}, delay={row.ExcessiveDelay}\n"
            )

    plot_delay_distribution(swing_events, plots_dir / "01_swing_confirmation_delay.png")
    plot_event_counts(counts, plots_dir / "02_event_count_comparison.png")
    plot_primary_effects(effects, plots_dir / "03_primary_outcome_intervals.png")
    plot_mae_distribution(comparison, plots_dir / "04_mae_distribution.png")


def run_experiment() -> None:
    """Execute the EXP-019 swing-break confirmation workflow."""
    plots_dir = EXP_DIR / "plots"
    results_dir = EXP_DIR / "results"
    plots_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    sweeps = load_sweep_events()
    baseline = load_exp018_baseline()
    bars_by_instrument = {
        instrument: load_instrument_bars(instrument)
        for instrument in INSTRUMENTS
    }
    swings_by_instrument = {
        instrument: detect_confirmed_swings(bars_by_instrument[instrument], instrument)
        for instrument in INSTRUMENTS
    }
    swings = pd.concat(swings_by_instrument.values(), ignore_index=True)
    entries, misses = build_swing_break_events(sweeps, bars_by_instrument, swings_by_instrument)
    if entries.empty:
        raise ValueError("No swing-break events were detected.")

    swing_events = append_outcomes(entries, bars_by_instrument)
    counts = summarize_counts(sweeps, baseline, swing_events, misses)
    comparison = build_baseline_comparison(baseline, swing_events)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    effects = compute_primary_effects(comparison, counts, rng)
    verdict = evaluate_verdict(effects)

    write_outputs(
        swings,
        misses,
        swing_events,
        counts,
        comparison,
        effects,
        verdict,
        plots_dir,
        results_dir,
    )

    print("EXP-019 complete.")
    print(f"Verdict: {verdict['verdict']} ({verdict['instruments_passing']}/4 instruments)")
    print(f"Plots:   {plots_dir}")
    print(f"Results: {results_dir}")


def main() -> None:
    """Entry point for manual execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_experiment()


if __name__ == "__main__":
    main()
