"""
Experiment EXP-017: Premium Discount Filter Impact on Sweep Quality
Implements the analysis plan from analysis-plan.md.
"""
import sys
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PYTHON_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

import json
import logging
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from ict_timebar import INSTRUMENTS


LOGGER = logging.getLogger(__name__)

EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-017"
EXP014_RESULTS_DIR = PYTHON_ROOT / "experiments" / "EXP-014" / "results"
EXP015_RESULTS_DIR = PYTHON_ROOT / "experiments" / "EXP-015" / "results"

BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 42

HIT_COL = "Hit1R_60m"
MAE_COL = "MAE_R_60m"
HIT_THRESHOLD = 0.05
MAE_THRESHOLD = 0.25
RETENTION_THRESHOLD = 0.50
MIN_FILTERED_EVENTS = 50
PLOT_R_CAP = 8.0

REQUIRED_SWEEP_COLS = {
    "Instrument",
    "NYDate",
    "Segment",
    "CloseTime",
    "Close",
    "Side",
    "EventType",
    "Ambiguous60",
    HIT_COL,
    MAE_COL,
}
REQUIRED_LEVEL_COLS = {
    "Instrument",
    "NYDate",
    "PDH",
    "PDL",
    "HasPDLevels",
}


# ── I/O helpers ──────────────────────────────────────────────────────────────

def require_columns(
    frame: pd.DataFrame,
    required: set[str],
    label: str,
) -> None:
    """Raise if a prerequisite artifact is missing required columns."""
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{label} is missing required columns: {missing}")


def parse_bool_series(
    series: pd.Series,
    default: bool,
) -> pd.Series:
    """Normalize common CSV boolean representations to pandas bool dtype."""
    # Python treats True/False and 1/0 as equal dict keys, so the mapping
    # only needs string/bool entries; integer 1/0 values still match via
    # the bool keys.
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
    """Load EXP-015 sweep events and keep only the scoped Train/Test sweeps."""
    path = EXP015_RESULTS_DIR / "sweep_events.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Required prerequisite artifact not found: {path}"
        )
    events = pd.read_csv(path)
    require_columns(events, REQUIRED_SWEEP_COLS, "EXP-015 sweep_events.csv")
    events = events[events["EventType"] == "Sweep"].copy()
    events = events[events["Segment"].isin(["Train", "Test"])].copy()
    events["Ambiguous60"] = parse_bool_series(events["Ambiguous60"], default=False)
    return events.sort_values(
        ["Instrument", "Segment", "NYDate", "CloseTime", "Side"]
    ).reset_index(drop=True)


def load_liquidity_levels() -> pd.DataFrame:
    """Load EXP-014 liquidity levels needed for prior-day midpoint labeling."""
    path = EXP014_RESULTS_DIR / "liquidity_levels.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Required prerequisite artifact not found: {path}"
        )
    levels = pd.read_csv(path)
    require_columns(levels, REQUIRED_LEVEL_COLS, "EXP-014 liquidity_levels.csv")
    levels["HasPDLevels"] = parse_bool_series(levels["HasPDLevels"], default=False)
    return (
        levels[["Instrument", "NYDate", "PDH", "PDL", "HasPDLevels"]]
        .drop_duplicates(subset=["Instrument", "NYDate"])
        .sort_values(["Instrument", "NYDate"])
        .reset_index(drop=True)
    )


def load_prerequisite_data() -> pd.DataFrame:
    """Merge EXP-015 sweeps with EXP-014 prior-day midpoint data."""
    sweeps = load_sweep_events()
    levels = load_liquidity_levels()
    merged = sweeps.merge(
        levels,
        on=["Instrument", "NYDate"],
        how="left",
        validate="m:1",
    )
    merged["HasPDLevels"] = parse_bool_series(
        merged["HasPDLevels"],
        default=False,
    )
    merged["Midpoint"] = np.where(
        merged["HasPDLevels"],
        (merged["PDH"] + merged["PDL"]) / 2.0,
        np.nan,
    )
    merged["FilterEligible"] = merged["HasPDLevels"]

    pass_high = (merged["Side"] == "High") & (merged["Close"] > merged["Midpoint"])
    pass_low = (merged["Side"] == "Low") & (merged["Close"] < merged["Midpoint"])
    merged["PassMidpointFilter"] = merged["FilterEligible"] & (pass_high | pass_low)
    merged["FilterStatus"] = np.where(
        merged["PassMidpointFilter"],
        "Filtered",
        "Excluded",
    )
    return merged.reset_index(drop=True)


# ── Summary tables ───────────────────────────────────────────────────────────

def summarize_retention(events: pd.DataFrame) -> pd.DataFrame:
    """Summarize filtered-event retention by instrument, segment, and side."""
    rows: list[dict[str, Any]] = []
    for keys, group in events.groupby(["Instrument", "Segment", "Side"], sort=True):
        instrument, segment, side = keys
        total = len(group)
        eligible = int(group["FilterEligible"].sum())
        filtered = int(group["PassMidpointFilter"].sum())
        rows.append(
            {
                "Instrument": instrument,
                "Segment": segment,
                "Side": side,
                "TotalSweeps": total,
                "EligibleSweeps": eligible,
                "FilteredSweeps": filtered,
                "MidpointMissingSweeps": total - eligible,
                "RetentionPct": filtered / total if total else np.nan,
                "EligibleRetentionPct": filtered / eligible if eligible else np.nan,
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["Instrument", "Segment", "Side"]
    ).reset_index(drop=True)


def _outcome_summary_row(
    group: pd.DataFrame,
    instrument: str,
    segment: str,
    filter_status: str,
) -> dict[str, Any]:
    """Summarize one filtered/unfiltered outcome group."""
    hit_values = group.loc[
        ~group["Ambiguous60"] & group[HIT_COL].notna(),
        HIT_COL,
    ].to_numpy(dtype=float)
    mae_values = group.loc[group[MAE_COL].notna(), MAE_COL].to_numpy(dtype=float)
    return {
        "Instrument": instrument,
        "Segment": segment,
        "FilterStatus": filter_status,
        "SweepN": int(len(group)),
        "Hit1R_N": int(hit_values.size),
        "Hit1R_Mean": float(hit_values.mean()) if hit_values.size else np.nan,
        "MAE_N": int(mae_values.size),
        "MAE_Mean": float(mae_values.mean()) if mae_values.size else np.nan,
        "MAE_Median": float(np.median(mae_values)) if mae_values.size else np.nan,
    }


def summarize_outcomes(events: pd.DataFrame) -> pd.DataFrame:
    """Summarize filtered versus all-sweep outcomes by instrument and segment."""
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        inst = events[events["Instrument"] == instrument]
        for segment in ("Train", "Test"):
            segment_events = inst[inst["Segment"] == segment]
            rows.append(
                _outcome_summary_row(
                    segment_events,
                    instrument,
                    segment,
                    "All sweeps",
                )
            )
            rows.append(
                _outcome_summary_row(
                    segment_events[segment_events["PassMidpointFilter"]],
                    instrument,
                    segment,
                    "Filtered",
                )
            )
    return pd.DataFrame(rows)


# ── Statistical analysis ─────────────────────────────────────────────────────

def bootstrap_nested_difference(
    values: np.ndarray,
    filtered_mask: np.ndarray,
    rng: np.random.Generator,
    use_median: bool = False,
) -> dict[str, Any]:
    """Bootstrap filtered-minus-baseline difference for a nested filtered subset.

    The filtered group is a subset of the unfiltered baseline. Each bootstrap
    resample is drawn from the full baseline rows, and the filtered statistic is
    recomputed inside that same resample. This keeps the dependence structure
    intact and avoids treating the subset and superset as independent samples.
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
        sample_diff = float(stat_fn(sample_values[sample_mask]) - stat_fn(sample_values))
        diffs.append(sample_diff)

    if not diffs:
        return result

    diff_array = np.asarray(diffs, dtype=float)
    result["CI95Low"] = float(np.quantile(diff_array, 0.025))
    result["CI95High"] = float(np.quantile(diff_array, 0.975))
    return result


def compute_primary_effects(
    events: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Compute filtered-versus-baseline effect sizes for all instruments."""
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        inst = events[events["Instrument"] == instrument]
        for segment in ("Train", "Test"):
            group = inst[inst["Segment"] == segment].copy()
            total_sweeps = len(group)
            filtered_sweeps = int(group["PassMidpointFilter"].sum())
            midpoint_missing = int((~group["FilterEligible"]).sum())
            retention_pct = filtered_sweeps / total_sweeps if total_sweeps else np.nan
            retention_floor = bool(
                filtered_sweeps >= MIN_FILTERED_EVENTS
                or (
                    np.isfinite(retention_pct)
                    and retention_pct >= RETENTION_THRESHOLD
                )
            )

            hit_group = group.loc[
                ~group["Ambiguous60"] & group[HIT_COL].notna(),
                ["PassMidpointFilter", HIT_COL],
            ].copy()
            hit_stats = bootstrap_nested_difference(
                hit_group[HIT_COL].to_numpy(dtype=float),
                hit_group["PassMidpointFilter"].to_numpy(dtype=bool),
                rng,
                use_median=False,
            )

            mae_group = group.loc[
                group[MAE_COL].notna(),
                ["PassMidpointFilter", MAE_COL],
            ].copy()
            mae_stats = bootstrap_nested_difference(
                mae_group[MAE_COL].to_numpy(dtype=float),
                mae_group["PassMidpointFilter"].to_numpy(dtype=bool),
                rng,
                use_median=True,
            )

            mae_improvement = (
                mae_stats["BaselineStat"] - mae_stats["FilteredStat"]
                if np.isfinite(mae_stats["BaselineStat"])
                and np.isfinite(mae_stats["FilteredStat"])
                else np.nan
            )
            mae_ci_low = (
                -mae_stats["CI95High"]
                if np.isfinite(mae_stats["CI95High"])
                else np.nan
            )
            mae_ci_high = (
                -mae_stats["CI95Low"]
                if np.isfinite(mae_stats["CI95Low"])
                else np.nan
            )
            hit_ci_positive = bool(
                np.isfinite(hit_stats["CI95Low"]) and hit_stats["CI95Low"] > 0.0
            )
            mae_ci_positive = bool(
                np.isfinite(mae_ci_low) and mae_ci_low > 0.0
            )

            rows.append(
                {
                    "Instrument": instrument,
                    "Segment": segment,
                    "TotalSweepN": total_sweeps,
                    "FilteredSweepN": filtered_sweeps,
                    "MidpointMissingN": midpoint_missing,
                    "RetentionPct": retention_pct,
                    "RetentionFloorMet": retention_floor,
                    "HitUnfilteredN": hit_stats["BaselineN"],
                    "HitFilteredN": hit_stats["FilteredN"],
                    "HitUnfilteredMean": hit_stats["BaselineStat"],
                    "HitFilteredMean": hit_stats["FilteredStat"],
                    "HitDiff": hit_stats["Diff"],
                    "HitCI95Low": hit_stats["CI95Low"],
                    "HitCI95High": hit_stats["CI95High"],
                    "HitCIPositive": hit_ci_positive,
                    "MAEUnfilteredN": mae_stats["BaselineN"],
                    "MAEFilteredN": mae_stats["FilteredN"],
                    "MAEUnfilteredMedian": mae_stats["BaselineStat"],
                    "MAEFilteredMedian": mae_stats["FilteredStat"],
                    "MAEImprovement": mae_improvement,
                    "MAECI95Low": mae_ci_low,
                    "MAECI95High": mae_ci_high,
                    "MAECIPositive": mae_ci_positive,
                    "HitCriterionMet": bool(
                        retention_floor
                        and np.isfinite(hit_stats["Diff"])
                        and hit_stats["Diff"] >= HIT_THRESHOLD
                    ),
                    "MAECriterionMet": bool(
                        retention_floor
                        and np.isfinite(mae_improvement)
                        and mae_improvement >= MAE_THRESHOLD
                    ),
                }
            )
    return pd.DataFrame(rows)


def evaluate_verdict(effects: pd.DataFrame) -> dict[str, Any]:
    """Map per-instrument train/test effects into FOR/AGAINST/INCONCLUSIVE."""
    per_instrument: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        inst_rows = effects[effects["Instrument"] == instrument]
        train_rows = inst_rows[inst_rows["Segment"] == "Train"]
        test_rows = inst_rows[inst_rows["Segment"] == "Test"]
        if train_rows.empty or test_rows.empty:
            per_instrument.append(
                {
                    "Instrument": instrument,
                    "RetentionFloorMet": False,
                    "HitPass": False,
                    "MAEPass": False,
                    "WidePositiveSignal": False,
                    "Pass": False,
                }
            )
            continue

        train = train_rows.iloc[0]
        test = test_rows.iloc[0]
        floor_met = bool(train["RetentionFloorMet"]) and bool(test["RetentionFloorMet"])
        hit_pass = bool(test["HitCriterionMet"])
        mae_pass = bool(test["MAECriterionMet"])
        # Wide-positive escape: only fires when the test point estimate is at
        # least halfway to the predeclared threshold AND the CI overlaps the
        # threshold. A tiny positive blip well below threshold is noise, not
        # signal, and must not downgrade AGAINST to INCONCLUSIVE.
        hit_wide = bool(
            np.isfinite(test["HitDiff"])
            and test["HitDiff"] >= 0.5 * HIT_THRESHOLD
            and np.isfinite(test["HitCI95High"])
            and test["HitCI95High"] >= HIT_THRESHOLD
            and not bool(test["HitCIPositive"])
        )
        mae_wide = bool(
            np.isfinite(test["MAEImprovement"])
            and test["MAEImprovement"] >= 0.5 * MAE_THRESHOLD
            and np.isfinite(test["MAECI95High"])
            and test["MAECI95High"] >= MAE_THRESHOLD
            and not bool(test["MAECIPositive"])
        )
        wide_positive = bool(
            floor_met and not (hit_pass or mae_pass) and (hit_wide or mae_wide)
        )
        per_instrument.append(
            {
                "Instrument": instrument,
                "RetentionFloorMet": floor_met,
                "HitPass": hit_pass,
                "MAEPass": mae_pass,
                "WidePositiveSignal": wide_positive,
                "Pass": bool(floor_met and (hit_pass or mae_pass)),
            }
        )

    verdict_df = pd.DataFrame(per_instrument)
    instruments_passing = int(verdict_df["Pass"].sum())
    instruments_with_floor = int(verdict_df["RetentionFloorMet"].sum())
    wide_positive_instruments = int(verdict_df["WidePositiveSignal"].sum())
    if instruments_passing >= 3:
        verdict = "FOR"
    elif instruments_with_floor < 3 or wide_positive_instruments > 0:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "AGAINST"
    return {
        "verdict": verdict,
        "instruments_passing": instruments_passing,
        "instruments_with_floor": instruments_with_floor,
        "wide_positive_instruments": wide_positive_instruments,
        "per_instrument": per_instrument,
    }


# ── Plots ─────────────────────────────────────────────────────────────────────

def plot_retention_by_side(
    retention: pd.DataFrame,
    save_path: Path,
) -> None:
    """Plot retained-event percentage by instrument, segment, and side."""
    if retention.empty:
        return
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for ax, segment in zip(axes, ["Train", "Test"]):
        sub = retention[retention["Segment"] == segment]
        sns.barplot(
            data=sub,
            x="Instrument",
            y="RetentionPct",
            hue="Side",
            hue_order=["High", "Low"],
            order=INSTRUMENTS,
            palette={"High": "steelblue", "Low": "darkorange"},
            ax=ax,
        )
        ax.axhline(
            RETENTION_THRESHOLD,
            color="firebrick",
            linestyle="--",
            linewidth=1,
            alpha=0.7,
        )
        ax.set_title(f"EXP-017 Retained Sweep Share by Side — {segment}")
        ax.set_xlabel("")
        ax.set_ylabel("Filtered sweeps / all sweeps")
        ax.set_ylim(0.0, 1.05)
        ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _error_bounds(
    point: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Convert point/lower/upper arrays into matplotlib error lengths."""
    err_low = np.where(
        np.isfinite(point - lower),
        np.maximum(point - lower, 0.0),
        0.0,
    )
    err_high = np.where(
        np.isfinite(upper - point),
        np.maximum(upper - point, 0.0),
        0.0,
    )
    return err_low, err_high


def plot_primary_effect_intervals(
    effects: pd.DataFrame,
    save_path: Path,
) -> None:
    """Plot filtered-vs-baseline hit-rate and MAE interval estimates."""
    if effects.empty:
        return
    sns.set_theme(style="whitegrid")
    plot_df = effects.copy()
    plot_df["Label"] = plot_df["Instrument"] + " " + plot_df["Segment"]
    y = np.arange(len(plot_df))

    hit_point = plot_df["HitDiff"].to_numpy(dtype=float)
    hit_low = plot_df["HitCI95Low"].to_numpy(dtype=float)
    hit_high = plot_df["HitCI95High"].to_numpy(dtype=float)
    hit_err_low, hit_err_high = _error_bounds(hit_point, hit_low, hit_high)

    mae_point = plot_df["MAEImprovement"].to_numpy(dtype=float)
    mae_low = plot_df["MAECI95Low"].to_numpy(dtype=float)
    mae_high = plot_df["MAECI95High"].to_numpy(dtype=float)
    mae_err_low, mae_err_high = _error_bounds(mae_point, mae_low, mae_high)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

    axes[0].errorbar(
        hit_point,
        y,
        xerr=[hit_err_low, hit_err_high],
        fmt="o",
        color="steelblue",
        ecolor="0.35",
        capsize=3,
    )
    axes[0].axvline(0.0, color="black", linewidth=1)
    axes[0].axvline(
        HIT_THRESHOLD,
        color="green",
        linewidth=1,
        linestyle="--",
        alpha=0.7,
        label=f"{HIT_THRESHOLD:.0%} threshold",
    )
    axes[0].set_title("Hit1R 60m Difference")
    axes[0].set_xlabel("Filtered minus all-sweep Hit1R_60m")
    axes[0].set_yticks(y)
    axes[0].set_yticklabels(plot_df["Label"])
    axes[0].legend(loc="lower right")

    axes[1].errorbar(
        mae_point,
        y,
        xerr=[mae_err_low, mae_err_high],
        fmt="o",
        color="darkorange",
        ecolor="0.35",
        capsize=3,
    )
    axes[1].axvline(0.0, color="black", linewidth=1)
    axes[1].axvline(
        MAE_THRESHOLD,
        color="green",
        linewidth=1,
        linestyle="--",
        alpha=0.7,
        label=f"{MAE_THRESHOLD:.2f}R threshold",
    )
    axes[1].set_title("Median MAE Improvement")
    axes[1].set_xlabel("All-sweep median MAE minus filtered median MAE")
    axes[1].legend(loc="lower right")

    fig.suptitle(
        "EXP-017 Filtered vs All-Sweep Primary Effects (bootstrap 95% CI)",
        fontsize=12,
    )
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_mae_distributions(
    events: pd.DataFrame,
    save_path: Path,
) -> None:
    """Plot MAE_R_60m distributions for all sweeps versus filtered sweeps."""
    if events.empty or MAE_COL not in events.columns:
        return
    all_sweeps = events[events[MAE_COL].notna()].copy()
    filtered = all_sweeps[all_sweeps["PassMidpointFilter"]].copy()
    if all_sweeps.empty:
        return
    all_sweeps["Group"] = "All sweeps"
    filtered["Group"] = "Filtered"
    plot_df = pd.concat([all_sweeps, filtered], ignore_index=True)
    plot_df[MAE_COL] = plot_df[MAE_COL].clip(upper=PLOT_R_CAP)

    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for ax, segment in zip(axes, ["Train", "Test"]):
        sub = plot_df[plot_df["Segment"] == segment]
        sns.boxplot(
            data=sub,
            x="Instrument",
            y=MAE_COL,
            hue="Group",
            order=INSTRUMENTS,
            hue_order=["All sweeps", "Filtered"],
            palette={"All sweeps": "0.7", "Filtered": "steelblue"},
            showfliers=False,
            ax=ax,
        )
        ax.set_title(f"EXP-017 60m MAE (capped at {PLOT_R_CAP}R) — {segment}")
        ax.set_xlabel("")
        ax.set_ylabel("MAE (R-multiple)")
        ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ── Output writing ────────────────────────────────────────────────────────────

def write_outputs(
    events: pd.DataFrame,
    retention: pd.DataFrame,
    outcome_summary: pd.DataFrame,
    effects: pd.DataFrame,
    verdict: dict[str, Any],
    plots_dir: Path,
    results_dir: Path,
) -> None:
    """Write CSV, JSON, text summary, and plots for EXP-017."""
    def json_safe(value: Any) -> Any:
        """Convert pandas/numpy values to strict JSON-safe Python scalars."""
        if isinstance(value, dict):
            return {str(k): json_safe(v) for k, v in value.items()}
        if isinstance(value, list):
            return [json_safe(v) for v in value]
        if isinstance(value, tuple):
            return [json_safe(v) for v in value]
        if isinstance(value, (np.bool_, bool)):
            return bool(value)
        if isinstance(value, (np.integer,)):
            return int(value)
        if isinstance(value, (np.floating, float)):
            return float(value) if np.isfinite(value) else None
        if pd.isna(value):
            return None
        return value

    events.to_csv(results_dir / "sweep_events_with_midpoint.csv", index=False)
    retention.to_csv(results_dir / "retention_summary.csv", index=False)
    outcome_summary.to_csv(results_dir / "outcome_summary.csv", index=False)
    effects.to_csv(results_dir / "primary_effects.csv", index=False)

    payload: dict[str, Any] = {
        "experiment_id": "EXP-017",
        "title": "Premium Discount Filter Impact on Sweep Quality",
        "bootstrap_reps": BOOTSTRAP_REPS,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "prerequisite_artifacts": [
            str(EXP014_RESULTS_DIR / "liquidity_levels.csv"),
            str(EXP015_RESULTS_DIR / "sweep_events.csv"),
        ],
        "midpoint_definition": (
            "Prior-day midpoint = (PDH + PDL) / 2 from EXP-014. "
            "High-side sweeps pass only when event Close > midpoint. "
            "Low-side sweeps pass only when event Close < midpoint."
        ),
        "baseline_definition": (
            "Baseline is all EXP-015 failed-sweep events with identical stop, "
            "risk, horizon, and outcome definitions."
        ),
        "retention_floor_rule": (
            "A segment passes the sample-size floor when filtered sweeps retain "
            f">= {RETENTION_THRESHOLD:.0%} of all sweeps OR filtered_sweep_n >= "
            f"{MIN_FILTERED_EVENTS}."
        ),
        "verdict_rule": (
            "FOR: test-segment filtered sweeps improve Hit1R_60m by >= 5pp OR "
            "reduce median MAE by >= 0.25R on >= 3 instruments, with retention "
            "floors met in both train and test. INCONCLUSIVE: fewer than 3 "
            "instruments meet the retention floor, OR an instrument's test "
            "point estimate is at least half the predeclared threshold AND its "
            "CI95-high overlaps the threshold (genuine ambiguity). AGAINST: at "
            "least 3 instruments meet the retention floor but fewer than 3 "
            "clear the thresholds, and no instrument shows a genuinely "
            "ambiguous wide-positive interval (point estimates below half the "
            "threshold or CIs that do not reach the threshold count as null)."
        ),
        "verdict_summary": verdict,
        "retention_summary": retention.to_dict(orient="records"),
        "outcome_summary": outcome_summary.to_dict(orient="records"),
        "primary_effects": effects.to_dict(orient="records"),
    }
    with (results_dir / "results.json").open("w", encoding="utf-8") as handle:
        json.dump(json_safe(payload), handle, indent=2, default=str, allow_nan=False)

    with (results_dir / "numerical_summary.txt").open("w", encoding="utf-8") as handle:
        handle.write("EXP-017 Premium Discount Filter Impact on Sweep Quality\n")
        handle.write(f"Verdict: {verdict['verdict']}\n")
        handle.write(
            f"Instruments passing: {verdict['instruments_passing']}/4 "
            f"(retention floor met: {verdict['instruments_with_floor']}/4)\n\n"
        )
        handle.write("Test-segment primary effects (filtered minus all sweeps):\n")
        test_rows = effects[effects["Segment"] == "Test"]
        for row in test_rows.itertuples(index=False):
            handle.write(
                f"- {row.Instrument}: filtered={row.FilteredSweepN}/{row.TotalSweepN} "
                f"({row.RetentionPct:.1%}), hit_diff={row.HitDiff:.3f} "
                f"CI=[{row.HitCI95Low:.3f}, {row.HitCI95High:.3f}], "
                f"mae_impr={row.MAEImprovement:.3f} "
                f"CI=[{row.MAECI95Low:.3f}, {row.MAECI95High:.3f}], "
                f"floor={row.RetentionFloorMet}, hit_pass={row.HitCriterionMet}, "
                f"mae_pass={row.MAECriterionMet}\n"
            )
        handle.write("\nRetention by side (test segment):\n")
        for row in retention[retention["Segment"] == "Test"].itertuples(index=False):
            handle.write(
                f"- {row.Instrument} {row.Side}: filtered={row.FilteredSweeps}/"
                f"{row.TotalSweeps} ({row.RetentionPct:.1%}), "
                f"midpoint_missing={row.MidpointMissingSweeps}\n"
            )

    plot_retention_by_side(retention, plots_dir / "01_retained_event_percentage.png")
    plot_primary_effect_intervals(effects, plots_dir / "02_primary_effect_intervals.png")
    plot_mae_distributions(events, plots_dir / "03_mae_distributions.png")


# ── Orchestration ─────────────────────────────────────────────────────────────

def run_experiment() -> None:
    """Execute the EXP-017 midpoint filter comparison workflow."""
    plots_dir = EXP_DIR / "plots"
    results_dir = EXP_DIR / "results"
    plots_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    LOGGER.info("loading prerequisite artifacts from EXP-014 and EXP-015")
    events = load_prerequisite_data()
    if events.empty:
        raise ValueError("No EXP-015 sweep events were available for EXP-017.")

    LOGGER.info("loaded %d sweep events for midpoint labeling", len(events))
    retention = summarize_retention(events)
    outcome_summary = summarize_outcomes(events)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    effects = compute_primary_effects(events, rng)
    verdict = evaluate_verdict(effects)

    write_outputs(
        events,
        retention,
        outcome_summary,
        effects,
        verdict,
        plots_dir,
        results_dir,
    )

    print("EXP-017 complete.")
    print(f"Verdict: {verdict['verdict']} ({verdict['instruments_passing']}/4 instruments)")
    print(f"Plots:   {plots_dir}")
    print(f"Results: {results_dir}")


def main() -> None:
    """Entry point for manual execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_experiment()


if __name__ == "__main__":
    main()
