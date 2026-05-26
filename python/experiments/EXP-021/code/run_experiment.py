"""
Experiment EXP-021: IFVG Confirmation Entry Quality
Implements the analysis plan from analysis-plan.md.

Predeclared config (locked before results are inspected):
  displacement_prerequisite : EXP-018 (DisplacementClose confirmation)
  retest_entry              : excluded (EXP-020 defines no deterministic retest rule)
  stop_convention           : EXP-015 original Stop for all 4 entry variants
  ifvg_direction_match      :
    High sweep (bearish) -> Bullish FVG whose IFVG inverts bearishly (close < LowerBound)
    Low  sweep (bullish) -> Bearish FVG whose IFVG inverts bullishly (close > UpperBound)
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
EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-021"
EXP015_RESULTS_DIR = PYTHON_ROOT / "experiments" / "EXP-015" / "results"
EXP018_RESULTS_DIR = PYTHON_ROOT / "experiments" / "EXP-018" / "results"
EXP020_RESULTS_DIR = PYTHON_ROOT / "experiments" / "EXP-020" / "results"

# Predeclared config
DISPLACEMENT_PREREQUISITE = "EXP-018"
RETEST_INCLUDED = False
# High sweep -> Bullish FVG IFVG; Low sweep -> Bearish FVG IFVG
IFVG_SIDE_FOR_SWEEP: dict[str, str] = {"High": "Bullish", "Low": "Bearish"}

BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 42
MIN_IFVG_EVENTS = 50
OUTCOME_HORIZON = 60
PLOT_R_CAP = 8.0
PLOT_SAMPLE_SEED = 42
PLOT_MAX_POINTS = 5_000

DISP_REQUIRED = {
    "Instrument", "NYDate", "Segment", "LevelType", "Side",
    "SweepTime", "DisplacementTime", "EntryProxy", "EntryTime",
    "Entry", "Stop", "Risk1R",
}
SWEEP_REQUIRED = {
    "Instrument", "NYDate", "Segment", "CloseTime", "Close",
    "LevelType", "Side", "EventType", "Buffer", "Stop",
}
FVG_REQUIRED = {
    "Instrument", "Segment", "Side", "CreationTime",
    "LowerBound", "UpperBound", "IsIFVG", "InversionTime",
}

ENTRY_LABELS = ["SweepClose", "DisplacementClose", "IFVGClose", "SecondCandleOpen"]


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


def load_displacement_events(sweeps: pd.DataFrame) -> pd.DataFrame:
    """Load EXP-018 displacement-confirmed entries (DisplacementClose proxy only)."""
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
        raise ValueError("EXP-021 could not map EXP-015 Buffer onto all displacement events.")
    return df.reset_index(drop=True)


def load_fvg_events() -> pd.DataFrame:
    """Load EXP-020 IFVG events (IsIFVG == True only)."""
    path = EXP020_RESULTS_DIR / "fvg_lifecycle_events.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required prerequisite not found: {path}")
    df = pd.read_csv(path)
    _require_columns(df, FVG_REQUIRED, "EXP-020 fvg_lifecycle_events.csv")
    df["IsIFVG"] = df["IsIFVG"].map(
        {True: True, False: False, "True": True, "False": False}
    ).fillna(False).astype(bool)
    df = df[df["IsIFVG"]].copy()
    df["CreationTime"] = pd.to_datetime(df["CreationTime"])
    df["InversionTime"] = pd.to_datetime(df["InversionTime"])
    return df.sort_values(["Instrument", "InversionTime"]).reset_index(drop=True)


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

def _find_ifvg_for_event(
    disp_event: pd.Series,
    ifvg_df: pd.DataFrame,
) -> dict[str, Any] | None:
    """Return the first matching IFVG whose InversionTime exceeds DisplacementTime.

    Matching rule (predeclared):
      High sweep -> Bullish FVG IFVG (close < LowerBound = bearish signal)
      Low  sweep -> Bearish FVG IFVG (close > UpperBound = bullish signal)
    """
    target_side = IFVG_SIDE_FOR_SWEEP[str(disp_event["Side"])]
    instrument = str(disp_event["Instrument"])
    segment = str(disp_event["Segment"])
    disp_time = pd.Timestamp(disp_event["DisplacementTime"])

    candidates = ifvg_df[
        (ifvg_df["Instrument"] == instrument)
        & (ifvg_df["Side"] == target_side)
        & (ifvg_df["Segment"] == segment)
        & (ifvg_df["CreationTime"] >= disp_time)
        & (ifvg_df["InversionTime"] > disp_time)
        & (ifvg_df["InversionTime"] > ifvg_df["CreationTime"])
    ]
    if candidates.empty:
        return None
    row = candidates.sort_values("InversionTime").iloc[0]
    return {
        "IFVGSide": row["Side"],
        "IFVGCreationTime": row["CreationTime"],
        "IFVGLowerBound": float(row["LowerBound"]),
        "IFVGUpperBound": float(row["UpperBound"]),
        "InversionTime": row["InversionTime"],
    }


def _lookup_bar_at_time(
    bars: pd.DataFrame,
    close_ns: np.ndarray,
    ts: pd.Timestamp,
) -> pd.Series | None:
    """Return the bar whose CloseTime equals ts."""
    ts_ns = int(ts.value)
    idx = int(np.searchsorted(close_ns, ts_ns, side="left"))
    if idx >= len(bars):
        return None
    bar = bars.iloc[idx]
    if int(bar["CloseTime"].value) != ts_ns:
        return None
    return bar


def _build_entry_row(
    disp: pd.Series,
    proxy: str,
    entry_time: Any,
    entry: float,
) -> dict[str, Any]:
    """Construct a single entry row using EXP-015 stop convention."""
    stop = float(disp["Stop"])
    risk = abs(stop - entry)
    min_risk = float(disp["MinRisk1R"])
    return {
        "Instrument": disp["Instrument"],
        "NYDate": disp["NYDate"],
        "Segment": disp["Segment"],
        "LevelType": disp["LevelType"],
        "Side": disp["Side"],
        "SweepTime": disp["SweepTime"],
        "DisplacementTime": disp["DisplacementTime"],
        "EntryProxy": proxy,
        "EntryTime": entry_time,
        "Entry": entry,
        "Stop": stop,
        "Risk1R": risk,
        "MinRisk1R": min_risk,
        "RiskFeasible": bool(np.isfinite(risk) and np.isfinite(min_risk) and risk >= min_risk > 0.0),
    }


def build_event_chains(
    sweeps: pd.DataFrame,
    displacements: pd.DataFrame,
    ifvg_df: pd.DataFrame,
    bars_by_instrument: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build 4-column entry chains and a waterfall summary.

    Returns (entry_rows, waterfall) where entry_rows has one row per
    (sweep, entry_proxy) combination and waterfall has counts at each stage.
    """
    entries: list[dict[str, Any]] = []
    waterfall_rows: list[dict[str, Any]] = []

    ifvg_df_sorted = ifvg_df.sort_values("InversionTime").reset_index(drop=True)

    for instrument in INSTRUMENTS:
        bars = bars_by_instrument[instrument]
        close_ns = bars["CloseTime"].values.astype(np.int64)
        open_ns = bars["OpenTime"].values.astype(np.int64)

        inst_disps = displacements[displacements["Instrument"] == instrument]
        inst_sweeps = sweeps[sweeps["Instrument"] == instrument]
        inst_ifvg = ifvg_df_sorted[ifvg_df_sorted["Instrument"] == instrument]

        for segment in ("Train", "Test"):
            seg_disps = inst_disps[inst_disps["Segment"] == segment]
            seg_sweeps = inst_sweeps[inst_sweeps["Segment"] == segment]
            n_sweep = len(seg_sweeps)
            n_disp = len(seg_disps)
            n_ifvg = 0
            n_second = 0

            for _, disp in seg_disps.iterrows():
                disp_close = float(disp["Entry"])
                disp_time = disp["DisplacementTime"]
                sweep_time = disp["SweepTime"]

                # Entry 1: SweepClose (sweep bar's close)
                sweep_bar = _lookup_bar_at_time(bars, close_ns, disp["SweepTime"])
                sw_entry = float(sweep_bar["Close"]) if sweep_bar is not None else disp_close
                entries.append(_build_entry_row(disp, "SweepClose", sweep_time, sw_entry))

                # Entry 2: DisplacementClose
                entries.append(_build_entry_row(disp, "DisplacementClose", disp_time, disp_close))

                # Entries 3 & 4: IFVG-based
                match = _find_ifvg_for_event(disp, inst_ifvg)
                if match is None:
                    continue

                inv_time = match["InversionTime"]
                inv_bar = _lookup_bar_at_time(bars, close_ns, inv_time)
                if inv_bar is None:
                    continue
                if str(inv_bar["Segment"]) != segment:
                    continue
                ifvg_entry = float(inv_bar["Close"])

                n_ifvg += 1
                entry_row = _build_entry_row(disp, "IFVGClose", inv_time, ifvg_entry)
                entry_row.update({
                    "IFVGSide": match["IFVGSide"],
                    "IFVGCreationTime": match["IFVGCreationTime"],
                    "IFVGLowerBound": match["IFVGLowerBound"],
                    "IFVGUpperBound": match["IFVGUpperBound"],
                })
                entries.append(entry_row)

                # Entry 4: SecondCandleOpen
                inv_ns = int(inv_time.value)
                next_idx = int(np.searchsorted(close_ns, inv_ns, side="right"))
                if next_idx >= len(bars):
                    continue
                next_bar = bars.iloc[next_idx]
                sc_entry = float(next_bar["Open"])
                sc_time = next_bar["OpenTime"]
                n_second += 1
                entry_row2 = _build_entry_row(disp, "SecondCandleOpen", sc_time, sc_entry)
                entry_row2.update({
                    "IFVGSide": match["IFVGSide"],
                    "IFVGCreationTime": match["IFVGCreationTime"],
                    "IFVGLowerBound": match["IFVGLowerBound"],
                    "IFVGUpperBound": match["IFVGUpperBound"],
                })
                entries.append(entry_row2)

            waterfall_rows.append({
                "Instrument": instrument,
                "Segment": segment,
                "SweepN": n_sweep,
                "DisplacementN": n_disp,
                "IFVGN": n_ifvg,
                "SecondCandleN": n_second,
                "IFVGRetentionPct": n_ifvg / n_disp if n_disp else np.nan,
                "IFVGFloorMet": n_ifvg >= MIN_IFVG_EVENTS,
            })

    return pd.DataFrame(entries), pd.DataFrame(waterfall_rows)


def append_outcomes(
    entries: pd.DataFrame,
    bars_by_instrument: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Append 60-minute real-price outcome metrics to each entry row."""
    rows: list[dict[str, Any]] = []
    for _, row in entries.iterrows():
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
    n_a, n_b = len(a), len(b)
    if n_a == 0 or n_b == 0:
        return np.nan, np.nan, np.nan
    diffs = np.empty(reps)
    for i in range(reps):
        diffs[i] = rng.choice(a, n_a).mean() - rng.choice(b, n_b).mean()
    return float(np.mean(diffs)), float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))


def run_bootstrap_comparisons(outcomes: pd.DataFrame) -> pd.DataFrame:
    """Compare IFVG-based entries vs simpler entries by instrument and segment.

    Metrics: Return_R, DrawdownAdjusted_R, MAE_R, Hit1R (all at 60 min).
    Bootstrap n=10,000.
    """
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    rows: list[dict[str, Any]] = []
    metrics = [
        f"Return_R_{OUTCOME_HORIZON}m",
        f"DrawdownAdjusted_R_{OUTCOME_HORIZON}m",
        f"MAE_R_{OUTCOME_HORIZON}m",
        f"Hit1R_{OUTCOME_HORIZON}m",
    ]

    for instrument in INSTRUMENTS:
        for segment in ("Train", "Test"):
            group = outcomes[
                (outcomes["Instrument"] == instrument)
                & (outcomes["Segment"] == segment)
            ]
            for metric in metrics:
                ifvg_vals = group[group["EntryProxy"] == "IFVGClose"][metric].dropna().to_numpy()
                for baseline in ("SweepClose", "DisplacementClose"):
                    base_vals = group[group["EntryProxy"] == baseline][metric].dropna().to_numpy()
                    mean_diff, ci_lo, ci_hi = _bootstrap_diff(ifvg_vals, base_vals, rng, BOOTSTRAP_REPS)
                    rows.append({
                        "Instrument": instrument,
                        "Segment": segment,
                        "Metric": metric,
                        "Comparison": f"IFVGClose_minus_{baseline}",
                        "IFVG_N": len(ifvg_vals),
                        "Baseline_N": len(base_vals),
                        "MeanDiff": mean_diff,
                        "CI_Lo": ci_lo,
                        "CI_Hi": ci_hi,
                        "CIExcludesZero": bool(
                            np.isfinite(ci_lo) and np.isfinite(ci_hi)
                            and (ci_lo > 0 or ci_hi < 0)
                        ),
                    })
    return pd.DataFrame(rows)


def summarize_expectancy(outcomes: pd.DataFrame) -> pd.DataFrame:
    """Compute mean outcome metrics by instrument, segment, and entry proxy."""
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        for segment in ("Train", "Test"):
            for proxy in ENTRY_LABELS:
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
                    "Instrument": instrument,
                    "Segment": segment,
                    "EntryProxy": proxy,
                    "N": n,
                    "FeasibleRiskN": feasible_n,
                    "RiskFilteredN": int(n - feasible_n),
                    "ReturnR_N": int(grp[ret_col].notna().sum()) if n else 0,
                    "MeanReturn_R": float(grp[ret_col].mean()) if n else np.nan,
                    "MeanDrawdownAdjusted_R": float(grp[dda_col].mean()) if n else np.nan,
                    "MeanMAE_R": float(grp[mae_col].mean()) if n else np.nan,
                    "MeanHit1R": float(grp[hit_col].mean()) if n else np.nan,
                    "EventFloorMet": feasible_n >= MIN_IFVG_EVENTS,
                })
    return pd.DataFrame(rows)


def evaluate_verdict(
    waterfall: pd.DataFrame,
    bootstrap: pd.DataFrame,
    expectancy: pd.DataFrame,
) -> dict[str, Any]:
    """Map IFVG event counts and bootstrap comparisons to a hypothesis verdict."""
    def _metric_improves(
        instrument: str,
        metric: str,
        comparison: str,
        segment: str,
    ) -> bool:
        rows = bootstrap[
            (bootstrap["Instrument"] == instrument)
            & (bootstrap["Segment"] == segment)
            & (bootstrap["Metric"] == metric)
            & (bootstrap["Comparison"] == comparison)
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

    def _metric_not_worse(
        instrument: str,
        metric: str,
        comparison: str,
        segment: str,
    ) -> bool:
        rows = bootstrap[
            (bootstrap["Instrument"] == instrument)
            & (bootstrap["Segment"] == segment)
            & (bootstrap["Metric"] == metric)
            & (bootstrap["Comparison"] == comparison)
        ]
        if rows.empty:
            return False
        row = rows.iloc[0]
        return bool(
            np.isfinite(row["CI_Lo"])
            and np.isfinite(row["CI_Hi"])
            and not (row["CI_Hi"] < 0)
        )

    def _metric_not_higher(
        instrument: str,
        metric: str,
        comparison: str,
        segment: str,
    ) -> bool:
        rows = bootstrap[
            (bootstrap["Instrument"] == instrument)
            & (bootstrap["Segment"] == segment)
            & (bootstrap["Metric"] == metric)
            & (bootstrap["Comparison"] == comparison)
        ]
        if rows.empty:
            return False
        row = rows.iloc[0]
        return bool(
            np.isfinite(row["CI_Lo"])
            and np.isfinite(row["CI_Hi"])
            and not (row["CI_Lo"] > 0)
        )

    per_instrument: list[dict[str, Any]] = []
    ret_metric = f"Return_R_{OUTCOME_HORIZON}m"
    dda_metric = f"DrawdownAdjusted_R_{OUTCOME_HORIZON}m"
    mae_metric = f"MAE_R_{OUTCOME_HORIZON}m"
    comparisons = ("IFVGClose_minus_SweepClose", "IFVGClose_minus_DisplacementClose")
    for instrument in INSTRUMENTS:
        ifvg_rows = expectancy[
            (expectancy["Instrument"] == instrument)
            & (expectancy["EntryProxy"] == "IFVGClose")
        ]
        floor_met = bool(
            len(ifvg_rows) == 2
            and ifvg_rows["EventFloorMet"].all()
        )
        test_return_improves = all(
            _metric_improves(instrument, ret_metric, comparison, "Test")
            for comparison in comparisons
        )
        test_dda_improves = all(
            _metric_improves(instrument, dda_metric, comparison, "Test")
            for comparison in comparisons
        )
        train_not_worse = all(
            _metric_not_worse(instrument, ret_metric, comparison, "Train")
            for comparison in comparisons
        )
        mae_not_worse = all(
            _metric_not_higher(instrument, mae_metric, comparison, segment)
            for comparison in comparisons
            for segment in ("Train", "Test")
        )
        improves = (test_return_improves or test_dda_improves) and train_not_worse and mae_not_worse
        per_instrument.append({
            "Instrument": instrument,
            "IFVGFloorMet": floor_met,
            "TestReturnImprovesBothBaselines": test_return_improves,
            "TestDrawdownAdjustedImprovesBothBaselines": test_dda_improves,
            "TrainReturnNotWorse": train_not_worse,
            "MAENotWorse": mae_not_worse,
            "IFVGImproves": improves,
            "Pass": floor_met and improves,
    })
    verdict_df = pd.DataFrame(per_instrument)
    passing = int(verdict_df["Pass"].sum())
    floor_met_count = int(verdict_df["IFVGFloorMet"].sum())
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
    """Plot event-chain count waterfall from sweep to IFVG entry."""
    stages = ["SweepN", "DisplacementN", "IFVGN", "SecondCandleN"]
    labels = ["Sweep", "Displacement", "IFVG Entry", "2nd Candle Open"]
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=False)
    for ax, segment in zip(axes, ("Train", "Test")):
        sub = waterfall[waterfall["Segment"] == segment].set_index("Instrument")
        sub[stages].rename(columns=dict(zip(stages, labels))).plot(
            kind="bar", ax=ax
        )
        ax.axhline(MIN_IFVG_EVENTS, color="red", linestyle="--", linewidth=1)
        ax.set_title(f"EXP-021 Event Chain Waterfall - {segment}")
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=0)
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_entry_expectancy(expectancy: pd.DataFrame, save_path: Path) -> None:
    """Plot mean Return_R by entry proxy and segment."""
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    for ax, segment in zip(axes, ("Train", "Test")):
        sub = expectancy[expectancy["Segment"] == segment]
        sns.barplot(
            data=sub, x="Instrument", y="MeanReturn_R", hue="EntryProxy",
            order=INSTRUMENTS, hue_order=ENTRY_LABELS, ax=ax,
        )
        ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
        ax.set_title(f"EXP-021 Mean Return_R by Entry Type - {segment}")
        ax.set_xlabel("")
        ax.legend(fontsize=7, title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_risk_distance(outcomes: pd.DataFrame, save_path: Path) -> None:
    """Plot risk-distance (Risk1R) distribution by entry proxy."""
    plot_df = outcomes[outcomes["EntryProxy"].isin(ENTRY_LABELS)].copy()
    rng = np.random.default_rng(PLOT_SAMPLE_SEED)
    if len(plot_df) > PLOT_MAX_POINTS:
        idx = rng.choice(len(plot_df), PLOT_MAX_POINTS, replace=False)
        plot_df = plot_df.iloc[idx]
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.boxplot(
        data=plot_df, x="Instrument", y="Risk1R", hue="EntryProxy",
        order=INSTRUMENTS, hue_order=ENTRY_LABELS, showfliers=False, ax=ax,
    )
    ax.set_title("EXP-021 Risk Distance (Risk1R) by Entry Type")
    ax.set_xlabel("")
    ax.legend(fontsize=7, title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_mfe_mae(outcomes: pd.DataFrame, save_path: Path) -> None:
    """Plot MFE_R vs MAE_R scatter by entry proxy (bounded sample)."""
    mfe_col = f"MFE_R_{OUTCOME_HORIZON}m"
    mae_col = f"MAE_R_{OUTCOME_HORIZON}m"
    plot_df = outcomes[outcomes["EntryProxy"].isin(ENTRY_LABELS)].copy()
    plot_df[mfe_col] = plot_df[mfe_col].clip(upper=PLOT_R_CAP)
    plot_df[mae_col] = plot_df[mae_col].clip(upper=PLOT_R_CAP)
    rng = np.random.default_rng(PLOT_SAMPLE_SEED)
    if len(plot_df) > PLOT_MAX_POINTS:
        idx = rng.choice(len(plot_df), PLOT_MAX_POINTS, replace=False)
        plot_df = plot_df.iloc[idx]
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 7))
    sns.scatterplot(
        data=plot_df, x=mae_col, y=mfe_col, hue="EntryProxy",
        hue_order=ENTRY_LABELS, alpha=0.4, s=20, ax=ax,
    )
    ax.plot([0, PLOT_R_CAP], [0, PLOT_R_CAP], "k--", linewidth=0.8)
    ax.set_title(f"EXP-021 MFE vs MAE at {OUTCOME_HORIZON}m (capped {PLOT_R_CAP}R)")
    ax.legend(fontsize=7, title="")
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
    if pd.isna(value) if not isinstance(value, (list, dict)) else False:
        return None
    return value


def write_outputs(
    outcomes: pd.DataFrame,
    waterfall: pd.DataFrame,
    expectancy: pd.DataFrame,
    bootstrap: pd.DataFrame,
    verdict: dict[str, Any],
    plots_dir: Path,
    results_dir: Path,
) -> None:
    """Write all EXP-021 results, tables, and plots."""
    outcomes.to_csv(results_dir / "entry_outcomes.csv", index=False)
    waterfall.to_csv(results_dir / "waterfall.csv", index=False)
    expectancy.to_csv(results_dir / "expectancy_summary.csv", index=False)
    bootstrap.to_csv(results_dir / "bootstrap_comparison.csv", index=False)

    payload = {
        "experiment_id": "EXP-021",
        "title": "IFVG Confirmation Entry Quality",
        "predeclared_config": {
            "displacement_prerequisite": DISPLACEMENT_PREREQUISITE,
            "retest_included": RETEST_INCLUDED,
            "ifvg_side_for_sweep": IFVG_SIDE_FOR_SWEEP,
            "stop_convention": "EXP-015 original Stop for all entry variants",
            "min_risk_rule": "Rows with inherited Risk1R below the original EXP-015 Buffer are excluded from R-based outcome summaries.",
            "outcome_horizon_minutes": OUTCOME_HORIZON,
            "min_ifvg_events_per_segment": MIN_IFVG_EVENTS,
        },
        "verdict_summary": verdict,
        "waterfall": waterfall.to_dict(orient="records"),
        "expectancy": expectancy.to_dict(orient="records"),
    }
    with (results_dir / "results.json").open("w", encoding="utf-8") as fh:
        json.dump(_json_safe(payload), fh, indent=2, default=str, allow_nan=False)

    with (results_dir / "numerical_summary.txt").open("w", encoding="utf-8") as fh:
        fh.write("EXP-021 IFVG Confirmation Entry Quality\n")
        fh.write(f"Verdict: {verdict['verdict']}\n")
        fh.write(f"Instruments passing: {verdict['instruments_passing']}/4\n\n")
        fh.write("Waterfall (instrument, segment, sweep->displacement->IFVG->2ndCandle):\n")
        for r in waterfall.itertuples(index=False):
            fh.write(
                f"  {r.Instrument} {r.Segment}: "
                f"{r.SweepN} -> {r.DisplacementN} -> {r.IFVGN} -> {r.SecondCandleN} "
                f"(floor_met={r.IFVGFloorMet})\n"
            )
        fh.write("\nExpectancy summary:\n")
        for r in expectancy.itertuples(index=False):
            fh.write(
                f"  {r.Instrument} {r.Segment} {r.EntryProxy}: "
                f"N={r.N}, Feasible={r.FeasibleRiskN}, RiskFiltered={r.RiskFilteredN}, "
                f"ReturnN={r.ReturnR_N}, ReturnR={r.MeanReturn_R:.3f}, "
                f"DrawdownAdjR={r.MeanDrawdownAdjusted_R:.3f}, "
                f"MAE_R={r.MeanMAE_R:.3f}, Hit1R={r.MeanHit1R:.3f}\n"
            )

    plot_chain_waterfall(waterfall, plots_dir / "01_chain_waterfall.png")
    plot_entry_expectancy(expectancy, plots_dir / "02_entry_expectancy_intervals.png")
    plot_risk_distance(outcomes, plots_dir / "03_risk_distance_distribution.png")
    plot_mfe_mae(outcomes, plots_dir / "04_mfe_mae_by_entry.png")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_experiment() -> None:
    """Execute the EXP-021 IFVG entry-quality workflow."""
    plots_dir = EXP_DIR / "plots"
    results_dir = EXP_DIR / "results"
    plots_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Loading prerequisite events …")
    sweeps = load_sweep_events()
    displacements = load_displacement_events(sweeps)
    ifvg_events = load_fvg_events()

    LOGGER.info("Loading instrument bars …")
    bars_by_instrument: dict[str, pd.DataFrame] = {}
    for instrument in INSTRUMENTS:
        bars_by_instrument[instrument] = load_instrument_bars(instrument)
        LOGGER.info("%s: %d analysis bars", instrument, len(bars_by_instrument[instrument]))

    LOGGER.info("Building event chains …")
    entries, waterfall = build_event_chains(
        sweeps, displacements, ifvg_events, bars_by_instrument
    )
    LOGGER.info(
        "Entry rows: %d across %d proxies",
        len(entries), entries["EntryProxy"].nunique() if not entries.empty else 0,
    )

    LOGGER.info("Computing outcomes …")
    outcomes = append_outcomes(entries, bars_by_instrument)

    LOGGER.info("Running bootstrap comparisons …")
    bootstrap = run_bootstrap_comparisons(outcomes)
    expectancy = summarize_expectancy(outcomes)
    verdict = evaluate_verdict(waterfall, bootstrap, expectancy)

    LOGGER.info("Writing outputs …")
    write_outputs(outcomes, waterfall, expectancy, bootstrap, verdict, plots_dir, results_dir)

    print("EXP-021 complete.")
    print(f"Verdict: {verdict['verdict']} ({verdict['instruments_passing']}/4 instruments)")
    print(f"Plots:   {plots_dir}")
    print(f"Results: {results_dir}")


def main() -> None:
    """Entry point for manual execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_experiment()


if __name__ == "__main__":
    main()
