"""
Experiment EXP-023: Breaker Confirmation Trade Quality
Implements the analysis plan from analysis-plan.md.

Predeclared config (locked before results are inspected):
  baseline                  : EXP-018 displacement (DisplacementClose)
  breaker_candidate         : loaded from EXP-022 selection.json at runtime
  stop_convention           : EXP-015 original Stop for all entries
  outcome_horizon           : 60 minutes (primary), consistent with EXP-018/019
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
EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-023"
EXP015_RESULTS_DIR = PYTHON_ROOT / "experiments" / "EXP-015" / "results"
EXP018_RESULTS_DIR = PYTHON_ROOT / "experiments" / "EXP-018" / "results"
EXP022_RESULTS_DIR = PYTHON_ROOT / "experiments" / "EXP-022" / "results"

PREDECLARED_BASELINE = "EXP-018"
OUTCOME_HORIZON = 60
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 42
MIN_BREAKER_EVENTS = 50
PLOT_R_CAP = 8.0
PLOT_SAMPLE_SEED = 42
PLOT_MAX_POINTS = 5_000

DISP_REQUIRED = {
    "Instrument", "NYDate", "Segment", "LevelType", "Side",
    "SweepTime", "DisplacementTime", "EntryProxy", "EntryTime",
    "Entry", "Stop", "Risk1R",
}
SWEEP_REQUIRED = {
    "Instrument", "NYDate", "Segment", "CloseTime",
    "LevelType", "Side", "EventType", "Buffer", "Stop",
}
CAND_A_REQUIRED = {
    "Instrument", "NYDate", "Segment", "LevelType", "Side",
    "SweepTime", "DisplacementTime", "BreakerTime", "BreakerClose",
}
CAND_B_REQUIRED = {
    "Instrument", "NYDate", "Segment", "LevelType", "Side",
    "SweepTime", "DisplacementTime", "BreakerTime", "BreakerClose",
}


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def _require_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    """Raise if a prerequisite artifact lacks required columns."""
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{label} is missing required columns: {missing}")


def load_sweep_events() -> pd.DataFrame:
    """Load EXP-015 failed-sweep events (Sweep rows only)."""
    path = EXP015_RESULTS_DIR / "sweep_events.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required prerequisite not found: {path}")
    df = pd.read_csv(path)
    _require_columns(df, SWEEP_REQUIRED, "EXP-015 sweep_events.csv")
    df = df[df["EventType"] == "Sweep"].copy()
    df["CloseTime"] = pd.to_datetime(df["CloseTime"])
    return df.sort_values(["Instrument", "Segment", "CloseTime"]).reset_index(drop=True)


def load_baseline_events(sweeps: pd.DataFrame) -> pd.DataFrame:
    """Load predeclared EXP-018 baseline (DisplacementClose rows only)."""
    path = EXP018_RESULTS_DIR / "entry_proxy_events.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required prerequisite not found: {path}")
    df = pd.read_csv(path)
    _require_columns(df, DISP_REQUIRED, "EXP-018 entry_proxy_events.csv")
    df = df[df["EntryProxy"] == "DisplacementClose"].copy()
    df["SweepTime"] = pd.to_datetime(df["SweepTime"])
    df["DisplacementTime"] = pd.to_datetime(df["DisplacementTime"])
    df["EntryTime"] = pd.to_datetime(df["EntryTime"])
    sweep_meta = (
        sweeps[
            [
                "Instrument", "NYDate", "Segment", "LevelType", "Side",
                "CloseTime", "Buffer",
            ]
        ]
        .rename(columns={"CloseTime": "SweepTime", "Buffer": "MinRisk1R"})
        .copy()
    )
    df = df.merge(
        sweep_meta,
        on=["Instrument", "NYDate", "Segment", "LevelType", "Side", "SweepTime"],
        how="left",
        validate="many_to_one",
    )
    if df["MinRisk1R"].isna().any():
        raise ValueError("EXP-023 could not map EXP-015 Buffer onto all baseline events.")
    return df.reset_index(drop=True)


def load_selected_breaker() -> tuple[str, pd.DataFrame]:
    """Load EXP-022 selection and the corresponding breaker events."""
    sel_path = EXP022_RESULTS_DIR / "selection.json"
    if not sel_path.exists():
        raise FileNotFoundError(f"EXP-022 selection not found: {sel_path}")
    with sel_path.open(encoding="utf-8") as fh:
        sel = json.load(fh)
    selected = sel.get("selection", {}).get("selected_candidate", "None")
    if selected == "None":
        raise ValueError(
            "EXP-022 did not select a candidate. "
            "EXP-023 cannot proceed without an approved breaker definition."
        )

    if selected == "CandidateA":
        events_path = EXP022_RESULTS_DIR / "candidate_a_events.csv"
        required = CAND_A_REQUIRED
        label = "EXP-022 candidate_a_events.csv"
    else:
        events_path = EXP022_RESULTS_DIR / "candidate_b_events.csv"
        required = CAND_B_REQUIRED
        label = "EXP-022 candidate_b_events.csv"

    if not events_path.exists():
        raise FileNotFoundError(f"Breaker events not found: {events_path}")
    df = pd.read_csv(events_path)
    _require_columns(df, required, label)
    df["SweepTime"] = pd.to_datetime(df["SweepTime"])
    df["DisplacementTime"] = pd.to_datetime(df["DisplacementTime"])
    df["BreakerTime"] = pd.to_datetime(df["BreakerTime"])
    return selected, df.reset_index(drop=True)


def load_instrument_bars(instrument: str) -> pd.DataFrame:
    """Load holdout-excluded analysis bars for one instrument."""
    loaded = load_analysis_timebars(DATA_DIR, instrument)
    frame = (
        add_bar_diagnostics(loaded.frame)
        .with_row_index("_Row")
        .with_columns(
            pl.when(pl.col("_Row") < loaded.train_rows)
            .then(pl.lit("Train"))
            .otherwise(pl.lit("Test"))
            .alias("Segment")
        )
    )
    bars = frame.sort("CloseTime").to_pandas()
    bars["CloseTime"] = pd.to_datetime(bars["CloseTime"])
    bars["OpenTime"] = pd.to_datetime(bars["OpenTime"])
    return bars.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Pure computation
# ---------------------------------------------------------------------------

def build_breaker_entries(
    baseline: pd.DataFrame,
    breaker_events: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Join baseline events with breaker confirmations and build entry rows.

    Returns (breaker_entries, waterfall) where waterfall has counts at each stage.
    """
    # Index breaker events by full baseline identity to avoid cross-level joins.
    join_keys = [
        "Instrument", "NYDate", "Segment", "LevelType", "Side",
        "SweepTime", "DisplacementTime",
    ]
    breaker_index = (
        breaker_events[join_keys + ["BreakerTime", "BreakerClose"]]
        .copy()
    )
    breaker_index["SweepTime"] = pd.to_datetime(breaker_index["SweepTime"])
    breaker_index["DisplacementTime"] = pd.to_datetime(breaker_index["DisplacementTime"])
    breaker_index["DuplicateJoinKeyCount"] = breaker_index.groupby(join_keys)["BreakerTime"].transform("count")

    merged = baseline.merge(
        breaker_index,
        on=join_keys,
        how="left",
    )
    confirmed = merged[
        merged["BreakerTime"].notna()
        & (pd.to_datetime(merged["BreakerTime"]) > pd.to_datetime(merged["DisplacementTime"]))
    ].copy()
    if not confirmed.empty:
        confirmed["BreakerTime"] = pd.to_datetime(confirmed["BreakerTime"])

    waterfall_rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        for segment in ("Train", "Test"):
            n_baseline = len(
                baseline[(baseline["Instrument"] == instrument) & (baseline["Segment"] == segment)]
            )
            n_breaker = len(
                confirmed[(confirmed["Instrument"] == instrument) & (confirmed["Segment"] == segment)]
            ) if not confirmed.empty else 0
            n_duplicate_join_keys = int(
                (
                    confirmed[(confirmed["Instrument"] == instrument) & (confirmed["Segment"] == segment)]
                    ["DuplicateJoinKeyCount"]
                    > 1
                ).sum()
            ) if not confirmed.empty and "DuplicateJoinKeyCount" in confirmed.columns else 0
            waterfall_rows.append({
                "Instrument": instrument, "Segment": segment,
                "BaselineN": n_baseline, "BreakerN": n_breaker,
                "DuplicateJoinKeyN": n_duplicate_join_keys,
                "RetentionPct": n_breaker / n_baseline if n_baseline else np.nan,
                "EventFloorMet": n_breaker >= MIN_BREAKER_EVENTS,
            })

    return confirmed, pd.DataFrame(waterfall_rows)


def _build_entry_row_from_baseline(
    row: pd.Series,
    proxy: str,
    entry_time: Any,
    entry: float,
) -> dict[str, Any]:
    """Build one entry row using EXP-015 Stop convention."""
    stop = float(row["Stop"])
    risk = abs(stop - entry)
    min_risk = float(row["MinRisk1R"])
    return {
        "Instrument": row["Instrument"],
        "NYDate": row["NYDate"],
        "Segment": row["Segment"],
        "LevelType": row["LevelType"],
        "Side": row["Side"],
        "SweepTime": row["SweepTime"],
        "EntryProxy": proxy,
        "EntryTime": entry_time,
        "Entry": entry,
        "Stop": stop,
        "Risk1R": risk,
        "MinRisk1R": min_risk,
        "RiskFeasible": bool(np.isfinite(risk) and np.isfinite(min_risk) and risk >= min_risk > 0.0),
    }


def prepare_outcome_events(
    baseline: pd.DataFrame,
    breaker_confirmed: pd.DataFrame,
) -> pd.DataFrame:
    """Combine baseline and breaker events into a single outcome-ready frame."""
    rows: list[dict[str, Any]] = []
    for _, row in baseline.iterrows():
        rows.append(
            _build_entry_row_from_baseline(row, "DisplacementClose", row["EntryTime"], float(row["Entry"]))
        )
    if not breaker_confirmed.empty:
        for _, row in breaker_confirmed.iterrows():
            rows.append(
                _build_entry_row_from_baseline(
                    row, "BreakerClose", row["BreakerTime"], float(row["BreakerClose"])
                )
            )
    return pd.DataFrame(rows)


def append_outcomes(
    events: pd.DataFrame,
    bars_by_instrument: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Append 60-minute real-price outcome metrics to entry rows."""
    rows: list[dict[str, Any]] = []
    for _, row in events.iterrows():
        bars = bars_by_instrument[str(row["Instrument"])]
        outcome = compute_real_price_outcome(row, bars, horizon_minutes=OUTCOME_HORIZON)
        ret_col = f"Return_R_{OUTCOME_HORIZON}m"
        mae_col = f"MAE_R_{OUTCOME_HORIZON}m"
        outcome[f"DrawdownAdjusted_R_{OUTCOME_HORIZON}m"] = (
            outcome[ret_col] - outcome[mae_col]
            if np.isfinite(outcome[ret_col]) and np.isfinite(outcome[mae_col])
            else np.nan
        )
        rows.append({**row.to_dict(), **outcome})
    return pd.DataFrame(rows)


def _bootstrap_diff(
    a: np.ndarray,
    b: np.ndarray,
    rng: np.random.Generator,
    reps: int,
) -> tuple[float, float, float]:
    """Bootstrap mean difference (a minus b) with 95% CI."""
    if len(a) == 0 or len(b) == 0:
        return np.nan, np.nan, np.nan
    n_a, n_b = len(a), len(b)
    diffs = np.array([
        rng.choice(a, n_a).mean() - rng.choice(b, n_b).mean()
        for _ in range(reps)
    ])
    return float(np.mean(diffs)), float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))


def run_bootstrap_comparisons(outcomes: pd.DataFrame) -> pd.DataFrame:
    """Bootstrap differences between BreakerClose and DisplacementClose baseline."""
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    metrics = [
        f"Return_R_{OUTCOME_HORIZON}m",
        f"DrawdownAdjusted_R_{OUTCOME_HORIZON}m",
        f"MAE_R_{OUTCOME_HORIZON}m",
        f"Hit1R_{OUTCOME_HORIZON}m",
    ]
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        for segment in ("Train", "Test"):
            group = outcomes[
                (outcomes["Instrument"] == instrument)
                & (outcomes["Segment"] == segment)
            ]
            for metric in metrics:
                breaker_vals = group[group["EntryProxy"] == "BreakerClose"][metric].dropna().to_numpy()
                baseline_vals = group[group["EntryProxy"] == "DisplacementClose"][metric].dropna().to_numpy()
                mean_diff, ci_lo, ci_hi = _bootstrap_diff(breaker_vals, baseline_vals, rng, BOOTSTRAP_REPS)
                rows.append({
                    "Instrument": instrument, "Segment": segment,
                    "Metric": metric,
                    "Breaker_N": len(breaker_vals),
                    "Baseline_N": len(baseline_vals),
                    "MeanDiff": mean_diff,
                    "CI_Lo": ci_lo,
                    "CI_Hi": ci_hi,
                    "CIExcludesZero": bool(
                        np.isfinite(ci_lo) and np.isfinite(ci_hi)
                        and (ci_lo > 0 or ci_hi < 0)
                    ),
                })
    return pd.DataFrame(rows)


def summarize_outcomes(outcomes: pd.DataFrame) -> pd.DataFrame:
    """Compute mean outcome metrics by instrument, segment, and proxy."""
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        for segment in ("Train", "Test"):
            for proxy in ("DisplacementClose", "BreakerClose"):
                grp = outcomes[
                    (outcomes["Instrument"] == instrument)
                    & (outcomes["Segment"] == segment)
                    & (outcomes["EntryProxy"] == proxy)
                ]
                n = len(grp)
                feasible_n = int(grp["RiskFeasible"].fillna(False).sum()) if n else 0
                ret_col = f"Return_R_{OUTCOME_HORIZON}m"
                dda_col = f"DrawdownAdjusted_R_{OUTCOME_HORIZON}m"
                mae_col = f"MAE_R_{OUTCOME_HORIZON}m"
                hit_col = f"Hit1R_{OUTCOME_HORIZON}m"
                rows.append({
                    "Instrument": instrument, "Segment": segment,
                    "EntryProxy": proxy, "N": n,
                    "FeasibleRiskN": feasible_n,
                    "RiskFilteredN": int(n - feasible_n),
                    "ReturnR_N": int(grp[ret_col].notna().sum()) if n else 0,
                    "MeanReturn_R": float(grp[ret_col].mean()) if n else np.nan,
                    "MeanDrawdownAdjusted_R": float(grp[dda_col].mean()) if n else np.nan,
                    "MeanMAE_R": float(grp[mae_col].mean()) if n else np.nan,
                    "MeanHit1R": float(grp[hit_col].mean()) if n else np.nan,
                    "EventFloorMet": feasible_n >= MIN_BREAKER_EVENTS,
                })
    return pd.DataFrame(rows)


def evaluate_verdict(
    waterfall: pd.DataFrame,
    bootstrap: pd.DataFrame,
    outcome_summary: pd.DataFrame,
) -> dict[str, Any]:
    """Map event counts and bootstrap comparisons to a hypothesis verdict."""
    def _metric_improves(instrument: str, segment: str, metric: str) -> bool:
        rows = bootstrap[
            (bootstrap["Instrument"] == instrument)
            & (bootstrap["Segment"] == segment)
            & (bootstrap["Metric"] == metric)
        ]
        if rows.empty:
            return False
        row = rows.iloc[0]
        return bool(
            np.isfinite(row["CI_Lo"])
            and np.isfinite(row["CI_Hi"])
            and row["MeanDiff"] > 0
            and row["CI_Lo"] > 0
        )

    def _metric_not_higher(instrument: str, segment: str, metric: str) -> bool:
        rows = bootstrap[
            (bootstrap["Instrument"] == instrument)
            & (bootstrap["Segment"] == segment)
            & (bootstrap["Metric"] == metric)
        ]
        if rows.empty:
            return False
        row = rows.iloc[0]
        return bool(
            np.isfinite(row["CI_Lo"])
            and np.isfinite(row["CI_Hi"])
            and not (row["CI_Lo"] > 0)
        )

    def _metric_not_lower(instrument: str, segment: str, metric: str) -> bool:
        rows = bootstrap[
            (bootstrap["Instrument"] == instrument)
            & (bootstrap["Segment"] == segment)
            & (bootstrap["Metric"] == metric)
        ]
        if rows.empty:
            return False
        row = rows.iloc[0]
        return bool(
            np.isfinite(row["CI_Lo"])
            and np.isfinite(row["CI_Hi"])
            and not (row["CI_Hi"] < 0)
        )

    per_instrument: list[dict[str, Any]] = []
    ret_metric = f"Return_R_{OUTCOME_HORIZON}m"
    dda_metric = f"DrawdownAdjusted_R_{OUTCOME_HORIZON}m"
    mae_metric = f"MAE_R_{OUTCOME_HORIZON}m"
    for instrument in INSTRUMENTS:
        breaker_rows = outcome_summary[
            (outcome_summary["Instrument"] == instrument)
            & (outcome_summary["EntryProxy"] == "BreakerClose")
        ]
        floor_met = bool(
            len(breaker_rows) == 2
            and breaker_rows["EventFloorMet"].all()
        )
        test_return_improves = _metric_improves(instrument, "Test", ret_metric)
        test_dda_improves = _metric_improves(instrument, "Test", dda_metric)
        train_return_not_worse = _metric_not_lower(instrument, "Train", ret_metric)
        mae_not_worse = all(
            _metric_not_higher(instrument, segment, mae_metric)
            for segment in ("Train", "Test")
        )
        improves = (test_return_improves or test_dda_improves) and train_return_not_worse and mae_not_worse
        per_instrument.append({
            "Instrument": instrument,
            "EventFloorMet": floor_met,
            "TestReturnImproves": test_return_improves,
            "TestDrawdownAdjustedImproves": test_dda_improves,
            "TrainReturnNotWorse": train_return_not_worse,
            "MAENotWorse": mae_not_worse,
            "BreakerImproves": improves,
            "Pass": floor_met and improves,
        })
    verdict_df = pd.DataFrame(per_instrument)
    passing = int(verdict_df["Pass"].sum())
    floor_met_count = int(verdict_df["EventFloorMet"].sum())
    if passing >= 3:
        verdict = "FOR"
    elif floor_met_count < 3:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "AGAINST"
    return {
        "verdict": verdict,
        "instruments_passing": passing,
        "instruments_floor_met": floor_met_count,
        "per_instrument": per_instrument,
    }


# ---------------------------------------------------------------------------
# Plotting helpers
# ---------------------------------------------------------------------------

def plot_chain_waterfall(waterfall: pd.DataFrame, save_path: Path) -> None:
    """Plot baseline-to-breaker event-count waterfall."""
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=False)
    for ax, segment in zip(axes, ("Train", "Test")):
        sub = waterfall[waterfall["Segment"] == segment].set_index("Instrument")
        sub[["BaselineN", "BreakerN"]].plot(kind="bar", ax=ax)
        ax.axhline(MIN_BREAKER_EVENTS, color="red", linestyle="--", linewidth=1)
        ax.set_title(f"EXP-023 Baseline → Breaker Waterfall - {segment}")
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=0)
        ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_expectancy_comparison(outcome_summary: pd.DataFrame, save_path: Path) -> None:
    """Plot mean Return_R for baseline vs breaker entries."""
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for ax, segment in zip(axes, ("Train", "Test")):
        sub = outcome_summary[outcome_summary["Segment"] == segment]
        sns.barplot(
            data=sub, x="Instrument", y="MeanReturn_R", hue="EntryProxy",
            order=INSTRUMENTS, ax=ax,
        )
        ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
        ax.set_title(f"EXP-023 Mean Return_R - {segment}")
        ax.set_xlabel("")
        ax.legend(title="", fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_r_distribution(outcomes: pd.DataFrame, save_path: Path) -> None:
    """Plot R-multiple distribution by entry proxy."""
    ret_col = f"Return_R_{OUTCOME_HORIZON}m"
    plot_df = outcomes.copy()
    plot_df[ret_col] = plot_df[ret_col].clip(lower=-PLOT_R_CAP, upper=PLOT_R_CAP)
    rng = np.random.default_rng(PLOT_SAMPLE_SEED)
    if len(plot_df) > PLOT_MAX_POINTS:
        idx = rng.choice(len(plot_df), PLOT_MAX_POINTS, replace=False)
        plot_df = plot_df.iloc[idx]
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.boxplot(
        data=plot_df, x="Instrument", y=ret_col, hue="EntryProxy",
        order=INSTRUMENTS, showfliers=False, ax=ax,
    )
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_title(f"EXP-023 Return_R Distribution at {OUTCOME_HORIZON}m")
    ax.set_xlabel("")
    ax.legend(title="", fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_event_retention(waterfall: pd.DataFrame, save_path: Path) -> None:
    """Plot event retention rate from baseline to breaker."""
    plot_df = waterfall.copy()
    plot_df["RetentionPct"] = plot_df["RetentionPct"].clip(upper=1.0)
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(
        data=plot_df, x="Instrument", y="RetentionPct", hue="Segment",
        order=INSTRUMENTS, ax=ax,
    )
    ax.set_ylim(0, 1.05)
    ax.set_title("EXP-023 Breaker Retention Rate (Breaker N / Baseline N)")
    ax.set_xlabel("")
    ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def _json_safe(value: Any) -> Any:
    """Convert numpy/pandas scalars to JSON-safe types."""
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def write_outputs(
    outcomes: pd.DataFrame,
    waterfall: pd.DataFrame,
    outcome_summary: pd.DataFrame,
    bootstrap: pd.DataFrame,
    verdict: dict[str, Any],
    selected_candidate: str,
    plots_dir: Path,
    results_dir: Path,
) -> None:
    """Write all EXP-023 results, tables, and plots."""
    outcomes.to_csv(results_dir / "outcome_events.csv", index=False)
    waterfall.to_csv(results_dir / "chain_waterfall.csv", index=False)
    outcome_summary.to_csv(results_dir / "outcome_comparison.csv", index=False)
    bootstrap.to_csv(results_dir / "bootstrap_comparison.csv", index=False)

    payload = {
        "experiment_id": "EXP-023",
        "title": "Breaker Confirmation Trade Quality",
        "predeclared_config": {
            "baseline": PREDECLARED_BASELINE,
            "breaker_candidate": selected_candidate,
            "stop_convention": "EXP-015 original Stop for all entry variants",
            "min_risk_rule": "Rows with inherited Risk1R below the original EXP-015 Buffer are excluded from R-based outcome summaries.",
            "outcome_horizon_minutes": OUTCOME_HORIZON,
            "min_breaker_events_per_segment": MIN_BREAKER_EVENTS,
        },
        "verdict_summary": verdict,
        "waterfall": waterfall.to_dict(orient="records"),
        "outcome_summary": outcome_summary.to_dict(orient="records"),
    }
    with (results_dir / "results.json").open("w", encoding="utf-8") as fh:
        json.dump(_json_safe(payload), fh, indent=2, default=str, allow_nan=False)

    with (results_dir / "numerical_summary.txt").open("w", encoding="utf-8") as fh:
        fh.write("EXP-023 Breaker Confirmation Trade Quality\n")
        fh.write(f"Verdict: {verdict['verdict']}\n")
        fh.write(f"Instruments passing: {verdict['instruments_passing']}/4\n")
        fh.write(f"Selected breaker: {selected_candidate}\n\n")
        fh.write("Waterfall:\n")
        for r in waterfall.itertuples(index=False):
            fh.write(
                f"  {r.Instrument} {r.Segment}: baseline={r.BaselineN} -> "
                f"breaker={r.BreakerN} (floor={r.EventFloorMet}, "
                f"duplicate_join_keys={r.DuplicateJoinKeyN})\n"
            )
        fh.write("\nOutcome summary:\n")
        for r in outcome_summary.itertuples(index=False):
            fh.write(
                f"  {r.Instrument} {r.Segment} {r.EntryProxy}: "
                f"N={r.N}, Feasible={r.FeasibleRiskN}, RiskFiltered={r.RiskFilteredN}, "
                f"ReturnN={r.ReturnR_N}, ReturnR={r.MeanReturn_R:.3f}, "
                f"DrawdownAdjR={r.MeanDrawdownAdjusted_R:.3f}, "
                f"MAE_R={r.MeanMAE_R:.3f}, Hit1R={r.MeanHit1R:.3f}\n"
            )

    plot_chain_waterfall(waterfall, plots_dir / "01_chain_waterfall.png")
    plot_expectancy_comparison(outcome_summary, plots_dir / "02_expectancy_comparison.png")
    plot_r_distribution(outcomes, plots_dir / "03_r_distribution.png")
    plot_event_retention(waterfall, plots_dir / "04_event_retention.png")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_experiment() -> None:
    """Execute the EXP-023 breaker confirmation quality workflow."""
    plots_dir = EXP_DIR / "plots"
    results_dir = EXP_DIR / "results"
    plots_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Loading prerequisite events …")
    sweeps = load_sweep_events()
    baseline = load_baseline_events(sweeps)
    selected_candidate, breaker_events = load_selected_breaker()
    LOGGER.info(
        "Baseline: %d events; Breaker (%s): %d events",
        len(baseline), selected_candidate, len(breaker_events),
    )

    LOGGER.info("Loading instrument bars …")
    bars_by_instrument: dict[str, pd.DataFrame] = {}
    for instrument in INSTRUMENTS:
        bars_by_instrument[instrument] = load_instrument_bars(instrument)
        LOGGER.info("%s: %d analysis bars", instrument, len(bars_by_instrument[instrument]))

    LOGGER.info("Building event chains …")
    breaker_confirmed, waterfall = build_breaker_entries(baseline, breaker_events)

    LOGGER.info("Preparing combined outcome events …")
    all_events = prepare_outcome_events(baseline, breaker_confirmed)

    LOGGER.info("Computing outcomes …")
    outcomes = append_outcomes(all_events, bars_by_instrument)

    LOGGER.info("Running bootstrap comparisons …")
    bootstrap = run_bootstrap_comparisons(outcomes)
    outcome_summary = summarize_outcomes(outcomes)
    verdict = evaluate_verdict(waterfall, bootstrap, outcome_summary)

    LOGGER.info("Writing outputs …")
    write_outputs(
        outcomes, waterfall, outcome_summary, bootstrap, verdict,
        selected_candidate, plots_dir, results_dir,
    )

    print("EXP-023 complete.")
    print(f"Verdict: {verdict['verdict']} ({verdict['instruments_passing']}/4 instruments)")
    print(f"Breaker: {selected_candidate}")
    print(f"Plots:   {plots_dir}")
    print(f"Results: {results_dir}")


def main() -> None:
    """Entry point for manual execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_experiment()


if __name__ == "__main__":
    main()
