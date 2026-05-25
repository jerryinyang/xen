"""
Experiment EXP-016: Macro Window Interaction With Sweep Outcomes
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
    compute_price_precision_step,
    load_analysis_timebars,
    train_cutoff_time,
    weekday_filter,
)


LOGGER = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-016"

BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 42
BUFFER_ATR_COEFF = 0.05
ON_LEVEL_MIN_MINUTE = OVERNIGHT_END_MINUTE  # 570 (09:30 NY)

LEVEL_TYPES_HIGH = ["PDH", "ONH"]
LEVEL_TYPES_LOW = ["PDL", "ONL"]
MIN_INSIDE_EVENTS = 50
MIN_MATCHED_OUTSIDE_EVENTS = 50

HIT_COL = "Hit1R_60m"
MAE_COL = "MAE_R_60m"
HIT_THRESHOLD = 0.05
MAE_THRESHOLD = 0.25

MACRO_WINDOW_NAMES = [spec.window for spec in MACRO_WINDOW_SPECS]

EVENT_COLS = [
    "Instrument", "NYDate", "Segment", "CloseTime",
    "Open", "High", "Low", "Close",
    "LevelType", "Side", "EventType", "Level", "Buffer",
    "Stop", "Entry", "Risk1R", "MacroWindow",
]

PLOT_R_CAP = 8.0


# ── I/O helpers ──────────────────────────────────────────────────────────────

def load_instrument_data(
    instrument: str,
) -> tuple[pl.DataFrame, pl.DataFrame, pd.DataFrame, float]:
    """Load analysis-set bars, weekday subset, liquidity levels, and price step.

    Parameters
    ----------
    instrument : str
        Instrument symbol.

    Returns
    -------
    tuple
        (frame_pl, wkday_pl, levels_pd, precision_step)
    """
    load = load_analysis_timebars(DATA_DIR, instrument)
    train_end = train_cutoff_time(load.frame, load.train_rows)
    frame_pl = add_bar_diagnostics(add_ny_time_features(load.frame, train_end))
    levels_pd = compute_liquidity_levels(frame_pl)
    precision_step = compute_price_precision_step(frame_pl)
    wkday_pl = weekday_filter(frame_pl)
    return frame_pl, wkday_pl, levels_pd, precision_step


# ── Sweep event detection ─────────────────────────────────────────────────────

def _build_level_events(merged: pd.DataFrame, level_type: str) -> pd.DataFrame:
    """Build the first-touch event per NYDate for one level type.

    Carries MacroWindow from merged bars so macro membership is readable
    directly from the event row without a secondary join.

    Parameters
    ----------
    merged : pd.DataFrame
        Weekday bars merged with level columns; includes Buffer and MacroWindow.
    level_type : str
        One of PDH, ONH, PDL, ONL.

    Returns
    -------
    pd.DataFrame
        One row per NYDate: first qualifying touch, classified Sweep or Breach.
    """
    side = "High" if level_type in ("PDH", "ONH") else "Low"
    level_col = merged[level_type]
    valid = level_col.notna()
    if level_type in ("ONH", "ONL"):
        valid = valid & (merged["NYMinuteOfDay"] >= ON_LEVEL_MIN_MINUTE)

    if side == "High":
        touch_mask = valid & (merged["High"] > level_col + merged["Buffer"])
    else:
        touch_mask = valid & (merged["Low"] < level_col - merged["Buffer"])

    candidates = merged[touch_mask].copy()
    if candidates.empty:
        return pd.DataFrame()

    if side == "High":
        candidates["EventType"] = np.where(
            candidates["Close"] < candidates[level_type], "Sweep", "Breach"
        )
    else:
        candidates["EventType"] = np.where(
            candidates["Close"] > candidates[level_type], "Sweep", "Breach"
        )

    first_touch = (
        candidates.sort_values("CloseTime").groupby("NYDate", sort=False).head(1).copy()
    )
    first_touch["LevelType"] = level_type
    first_touch["Side"] = side
    first_touch["Level"] = first_touch[level_type]
    first_touch["Stop"] = np.where(
        side == "High",
        first_touch["High"] + first_touch["Buffer"],
        first_touch["Low"] - first_touch["Buffer"],
    )
    first_touch["Entry"] = first_touch["Close"]
    first_touch["Risk1R"] = (first_touch["Stop"] - first_touch["Entry"]).abs()
    return first_touch


def detect_sweep_events(
    wkday_pd: pd.DataFrame,
    levels: pd.DataFrame,
    instrument: str,
    precision_step: float,
) -> pd.DataFrame:
    """Detect first-occurrence sweep and breach events per day and level type.

    Parameters
    ----------
    wkday_pd : pd.DataFrame
        Weekday bars with NY features, bar diagnostics, and MacroWindow column.
    levels : pd.DataFrame
        Liquidity levels from compute_liquidity_levels.
    instrument : str
        Instrument name.
    precision_step : float
        Buffer floor price increment.

    Returns
    -------
    pd.DataFrame
        Event rows with EVENT_COLS columns and InMacro flag.
    """
    inst_lvl = levels[levels["Instrument"] == instrument][
        ["NYDate", "PDH", "PDL", "ONH", "ONL"]
    ].copy()
    merged = wkday_pd.merge(inst_lvl, on="NYDate", how="left")
    atr_safe = merged["ATR14Prior"].fillna(0.0)
    merged["Buffer"] = np.maximum(precision_step, BUFFER_ATR_COEFF * atr_safe)
    merged["Instrument"] = instrument

    parts = [_build_level_events(merged, lt) for lt in LEVEL_TYPES_HIGH + LEVEL_TYPES_LOW]
    non_empty = [p for p in parts if not p.empty]
    if not non_empty:
        return pd.DataFrame(columns=EVENT_COLS + ["InMacro"])
    result = pd.concat(non_empty, ignore_index=True)
    if result.empty:
        return pd.DataFrame(columns=EVENT_COLS + ["InMacro"])
    for col in EVENT_COLS:
        if col not in result.columns:
            result[col] = None
    result["InMacro"] = result["MacroWindow"].notna()
    return result[EVENT_COLS + ["InMacro"]].reset_index(drop=True)


# ── Outcome computation ───────────────────────────────────────────────────────

def _walk_bars_for_hit(
    highs: np.ndarray,
    lows: np.ndarray,
    target: float,
    stop: float,
    is_bearish: bool,
) -> tuple[bool, bool, bool, int, int]:
    """Walk forward bars; stop at first bar hitting target or stop.

    Returns (target_hit, stop_hit, ambiguous, target_bar_idx, stop_bar_idx).
    """
    for i, (h, l) in enumerate(zip(highs, lows)):
        t_hit = bool(l <= target) if is_bearish else bool(h >= target)
        s_hit = bool(h >= stop) if is_bearish else bool(l <= stop)
        if t_hit and s_hit:
            return False, False, True, i, i
        if t_hit:
            return True, False, False, i, -1
        if s_hit:
            return False, True, False, -1, i
    return False, False, False, -1, -1


def _time_metrics_60m(
    tidx: int,
    sidx: int,
    start_idx: int,
    ct_ns: np.ndarray,
    event_ns: int,
    ambiguous: bool,
) -> dict[str, Any]:
    """Return Ambiguous60, TimeToTarget1R_60m, and TimeToStop_60m for 60m horizon."""
    ns_per_min = 60 * 10**9
    return {
        "Ambiguous60": bool(ambiguous),
        "TimeToTarget1R_60m": (
            float(ct_ns[start_idx + tidx] - event_ns) / ns_per_min if tidx >= 0 else np.nan
        ),
        "TimeToStop_60m": (
            float(ct_ns[start_idx + sidx] - event_ns) / ns_per_min if sidx >= 0 else np.nan
        ),
    }


def _compute_single_outcomes(
    event: pd.Series,
    ct_ns: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
) -> dict[str, Any]:
    """Compute 60-minute forward outcomes for one event row.

    Parameters
    ----------
    event : pd.Series
        Single event with Entry, Risk1R, Stop, Side, CloseTime.
    ct_ns, highs, lows : np.ndarray
        Full sorted instrument arrays (nanosecond CloseTime, High, Low).

    Returns
    -------
    dict
        MFE_R_60m, MAE_R_60m, Hit1R_60m, Ambiguous60, and time-to-hit metrics.
    """
    nan_out: dict[str, Any] = {
        "MFE_R_60m": np.nan, "MAE_R_60m": np.nan, "Hit1R_60m": np.nan,
        "Ambiguous60": False, "TimeToTarget1R_60m": np.nan, "TimeToStop_60m": np.nan,
    }
    entry = float(event["Entry"])
    risk = float(event["Risk1R"])
    if risk <= 0:
        return nan_out

    stop = float(event["Stop"])
    is_bearish = event["Side"] == "High"
    event_ns = int(pd.Timestamp(event["CloseTime"]).value)
    start_idx = int(np.searchsorted(ct_ns, event_ns, side="right"))
    end_ns = event_ns + 60 * 60 * 10**9
    end_idx = int(np.searchsorted(ct_ns, end_ns, side="right"))
    h_highs = highs[start_idx:end_idx]
    h_lows = lows[start_idx:end_idx]
    if h_highs.size == 0:
        return nan_out

    mfe = (entry - float(np.min(h_lows))) if is_bearish else (float(np.max(h_highs)) - entry)
    mae = (float(np.max(h_highs)) - entry) if is_bearish else (entry - float(np.min(h_lows)))
    t1r = (entry - risk) if is_bearish else (entry + risk)
    hit1, _, amb, tidx, sidx = _walk_bars_for_hit(h_highs, h_lows, t1r, stop, is_bearish)
    out: dict[str, Any] = {
        "MFE_R_60m": max(0.0, mfe) / risk,
        "MAE_R_60m": max(0.0, mae) / risk,
        "Hit1R_60m": np.nan if amb else float(hit1),
    }
    out.update(_time_metrics_60m(tidx, sidx, start_idx, ct_ns, event_ns, amb))
    return out


def compute_event_outcomes(
    events: pd.DataFrame,
    ct_ns: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
) -> pd.DataFrame:
    """Compute 60-minute forward outcomes for all events.

    Parameters
    ----------
    events : pd.DataFrame
        Events from detect_sweep_events.
    ct_ns, highs, lows : np.ndarray
        Full sorted instrument bar arrays (nanosecond CloseTime, High, Low).

    Returns
    -------
    pd.DataFrame
        Events with outcome columns appended.
    """
    rows: list[dict[str, Any]] = [
        {**dict(row), **_compute_single_outcomes(row, ct_ns, highs, lows)}
        for _, row in events.iterrows()
    ]
    return pd.DataFrame(rows)


# ── Macro interaction analysis ────────────────────────────────────────────────

def build_matched_outside(events: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build matched-outside pool and per-instrument sensitivity summary.

    Matched outside sweeps share (Instrument, Segment, Side, NYDate) with at
    least one inside-macro sweep. Unmatched outside sweeps appear only in the
    sensitivity summary to show what fraction of outside events can be compared.

    Parameters
    ----------
    events : pd.DataFrame
        All events with InMacro and EventType columns.

    Returns
    -------
    tuple
        (matched_outside_df, sensitivity_summary_df)
    """
    sweeps = events[events["EventType"] == "Sweep"].copy()
    inside = sweeps[sweeps["InMacro"]]
    outside = sweeps[~sweeps["InMacro"]]
    match_keys = ["Instrument", "Segment", "Side", "NYDate"]
    matched = outside.merge(inside[match_keys].drop_duplicates(), on=match_keys, how="inner")

    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        for segment in ("Train", "Test"):
            all_n = int(
                ((outside["Instrument"] == instrument) & (outside["Segment"] == segment)).sum()
            )
            mat_n = int(
                ((matched["Instrument"] == instrument) & (matched["Segment"] == segment)).sum()
            )
            rows.append({
                "Instrument": instrument, "Segment": segment,
                "AllOutsideSweeps": all_n, "MatchedOutsideSweeps": mat_n,
                "UnmatchedOutsideSweeps": all_n - mat_n,
                "MatchedFraction": mat_n / all_n if all_n > 0 else np.nan,
            })
    return matched, pd.DataFrame(rows)


def _bootstrap_metric_diff(
    inside_vals: np.ndarray,
    outside_vals: np.ndarray,
    rng: np.random.Generator,
    use_median: bool = False,
) -> dict[str, float]:
    """Bootstrap 95% CI for inside minus outside difference (mean or median).

    Parameters
    ----------
    inside_vals, outside_vals : np.ndarray
        Metric values for inside-macro and matched-outside sweeps.
    rng : np.random.Generator
        Seeded RNG.
    use_median : bool
        Use median instead of mean as the estimator.

    Returns
    -------
    dict
        InsideN, OutsideN, InsideStat, OutsideStat, Diff, CI95Low, CI95High.
    """
    stat = np.median if use_median else np.mean
    base: dict[str, float] = {
        "InsideN": float(len(inside_vals)),
        "OutsideN": float(len(outside_vals)),
        "InsideStat": float(stat(inside_vals)) if len(inside_vals) else np.nan,
        "OutsideStat": float(stat(outside_vals)) if len(outside_vals) else np.nan,
        "Diff": np.nan, "CI95Low": np.nan, "CI95High": np.nan,
    }
    if np.isfinite(base["InsideStat"]) and np.isfinite(base["OutsideStat"]):
        base["Diff"] = base["InsideStat"] - base["OutsideStat"]
    if len(inside_vals) < 2 or len(outside_vals) < 2:
        return base
    diffs = np.array([
        stat(rng.choice(inside_vals, size=len(inside_vals), replace=True))
        - stat(rng.choice(outside_vals, size=len(outside_vals), replace=True))
        for _ in range(BOOTSTRAP_REPS)
    ])
    base["CI95Low"] = float(np.quantile(diffs, 0.025))
    base["CI95High"] = float(np.quantile(diffs, 0.975))
    return base


def _filter_hit_vals(df: pd.DataFrame, instrument: str, segment: str) -> np.ndarray:
    """Return non-ambiguous, non-NaN Hit1R_60m values for instrument/segment."""
    mask = (
        (df["Instrument"] == instrument)
        & (df["Segment"] == segment)
        & ~df["Ambiguous60"].fillna(True).astype(bool)
        & df[HIT_COL].notna()
    )
    return df.loc[mask, HIT_COL].to_numpy(dtype=float)


def _filter_mae_vals(df: pd.DataFrame, instrument: str, segment: str) -> np.ndarray:
    """Return non-NaN MAE_R_60m values for instrument/segment."""
    mask = (
        (df["Instrument"] == instrument)
        & (df["Segment"] == segment)
        & df[MAE_COL].notna()
    )
    return df.loc[mask, MAE_COL].to_numpy(dtype=float)


def _instrument_segment_effects(
    inside_sweeps: pd.DataFrame,
    matched_outside: pd.DataFrame,
    instrument: str,
    segment: str,
    rng: np.random.Generator,
) -> dict[str, Any]:
    """Compute bootstrap effect sizes for one (instrument, segment) pair.

    Parameters
    ----------
    inside_sweeps : pd.DataFrame
        Inside-macro sweep events with outcome columns.
    matched_outside : pd.DataFrame
        Matched outside sweeps from build_matched_outside.
    instrument, segment : str
        Filter keys.
    rng : np.random.Generator
        Seeded RNG.

    Returns
    -------
    dict
        Effect metrics and pass flags for this instrument/segment pair.
    """
    inside_n = int(
        ((inside_sweeps["Instrument"] == instrument)
         & (inside_sweeps["Segment"] == segment)).sum()
    )
    ins_hit = _filter_hit_vals(inside_sweeps, instrument, segment)
    out_hit = _filter_hit_vals(matched_outside, instrument, segment)
    hit = _bootstrap_metric_diff(ins_hit, out_hit, rng, use_median=False)

    ins_mae = _filter_mae_vals(inside_sweeps, instrument, segment)
    out_mae = _filter_mae_vals(matched_outside, instrument, segment)
    mae = _bootstrap_metric_diff(ins_mae, out_mae, rng, use_median=True)

    hit_diff = hit["Diff"]
    # MAEImprovement = outside_median - inside_median (positive = inside has less adverse excursion)
    mae_impr = -mae["Diff"] if np.isfinite(mae["Diff"]) else np.nan
    mae_ci_lo = -mae["CI95High"] if np.isfinite(mae.get("CI95High", np.nan)) else np.nan
    mae_ci_hi = -mae["CI95Low"] if np.isfinite(mae.get("CI95Low", np.nan)) else np.nan
    outside_n = max(int(hit["OutsideN"]), int(mae["OutsideN"]))
    evaluable = inside_n >= MIN_INSIDE_EVENTS and outside_n >= MIN_MATCHED_OUTSIDE_EVENTS

    return {
        "Instrument": instrument, "Segment": segment,
        "InsideSweepN": inside_n,
        "PassEventCount": inside_n >= MIN_INSIDE_EVENTS,
        "MatchedOutsideN": outside_n,
        "PassMatchedOutsideCount": outside_n >= MIN_MATCHED_OUTSIDE_EVENTS,
        "Evaluable": evaluable,
        "InsideHitMean": hit["InsideStat"], "OutsideHitMean": hit["OutsideStat"],
        "HitDiff": hit_diff, "HitCI95Low": hit["CI95Low"], "HitCI95High": hit["CI95High"],
        "HitInsideN": int(hit["InsideN"]), "HitOutsideN": int(hit["OutsideN"]),
        "InsideMAEMedian": mae["InsideStat"], "OutsideMAEMedian": mae["OutsideStat"],
        "MAEImprovement": mae_impr, "MAECI95Low": mae_ci_lo, "MAECI95High": mae_ci_hi,
        "HitCriterionMet": evaluable and np.isfinite(hit_diff) and hit_diff >= HIT_THRESHOLD,
        "MAECriterionMet": evaluable and np.isfinite(mae_impr) and mae_impr >= MAE_THRESHOLD,
    }


def compute_primary_effects(
    events: pd.DataFrame,
    matched_outside: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Bootstrap effects for all instrument/segment pairs.

    Computes Hit1R_60m mean difference and MAE_R_60m median difference
    between inside-macro and matched-outside sweeps.

    Parameters
    ----------
    events : pd.DataFrame
        All events with InMacro and outcome columns.
    matched_outside : pd.DataFrame
        Matched outside sweeps from build_matched_outside.
    rng : np.random.Generator
        Seeded RNG.

    Returns
    -------
    pd.DataFrame
        One row per (Instrument, Segment) with effect statistics.
    """
    inside_sweeps = events[(events["EventType"] == "Sweep") & events["InMacro"]]
    rows = [
        _instrument_segment_effects(inside_sweeps, matched_outside, inst, seg, rng)
        for inst in INSTRUMENTS
        for seg in ("Train", "Test")
    ]
    return pd.DataFrame(rows)


def evaluate_verdict(effects: pd.DataFrame) -> dict[str, Any]:
    """Evaluate the scope verdict from train/test primary effects.

    FOR: inside-macro sweeps improve Hit1R by >= 5pp OR reduce MAE by >= 0.25R
    on >= 3 instruments with train and test event/comparator floors met.
    INCONCLUSIVE: fewer than 3 instruments meet the floors. AGAINST: floors met
    but thresholds not met.

    Parameters
    ----------
    effects : pd.DataFrame
        Output from compute_primary_effects.

    Returns
    -------
    dict
        verdict, instruments_passing, instruments_with_floor, per_instrument list.
    """
    per_instrument: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        inst_rows = effects[effects["Instrument"] == instrument]
        train_rows = inst_rows[inst_rows["Segment"] == "Train"]
        test_rows = inst_rows[inst_rows["Segment"] == "Test"]
        if train_rows.empty or test_rows.empty:
            per_instrument.append({
                "Instrument": instrument,
                "FloorMet": False,
                "MatchedOutsideFloorMet": False,
                "Pass": False,
            })
            continue
        train = train_rows.iloc[0]
        test = test_rows.iloc[0]
        floor_met = bool(train["PassEventCount"]) and bool(test["PassEventCount"])
        matched_floor_met = (
            bool(train["PassMatchedOutsideCount"])
            and bool(test["PassMatchedOutsideCount"])
        )
        hit_pass = bool(test["HitCriterionMet"])
        mae_pass = bool(test["MAECriterionMet"])
        per_instrument.append({
            "Instrument": instrument, "FloorMet": floor_met,
            "MatchedOutsideFloorMet": matched_floor_met,
            "HitPass": hit_pass, "MAEPass": mae_pass,
            "Pass": floor_met and matched_floor_met and (hit_pass or mae_pass),
        })
    inst_df = pd.DataFrame(per_instrument)
    n_pass = int(inst_df["Pass"].sum())
    n_floor = int((inst_df["FloorMet"] & inst_df["MatchedOutsideFloorMet"]).sum())
    if n_pass >= 3:
        verdict = "FOR"
    elif n_floor < 3:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "AGAINST"
    return {
        "verdict": verdict,
        "instruments_passing": n_pass,
        "instruments_with_floor": n_floor,
        "per_instrument": per_instrument,
    }


# ── Plots ─────────────────────────────────────────────────────────────────────

def plot_inside_outside_counts(count_data: pd.DataFrame, save_path: Path) -> None:
    """Grouped bar chart of inside vs outside sweep counts per instrument.

    Parameters
    ----------
    count_data : pd.DataFrame
        Aggregated sweep counts by Instrument, Segment, InMacro.
    save_path : Path
        Output file path.
    """
    if count_data.empty:
        return
    sns.set_theme(style="whitegrid")
    plot_df = count_data.copy()
    plot_df["Group"] = np.where(plot_df["InMacro"], "Inside macro", "Outside macro")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, segment in zip(axes, ["Train", "Test"]):
        sub = plot_df[plot_df["Segment"] == segment]
        sns.barplot(
            data=sub, x="Instrument", y="Count", hue="Group",
            palette={"Inside macro": "steelblue", "Outside macro": "salmon"},
            order=INSTRUMENTS, ax=ax,
        )
        ax.set_title(f"EXP-016 Sweep Counts by Macro Membership — {segment}")
        ax.set_xlabel("")
        ax.set_ylabel("Sweeps")
        ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_effect_intervals(effects: pd.DataFrame, save_path: Path) -> None:
    """Forest plot of Hit1R_60m inside minus outside differences with 95% CI.

    Parameters
    ----------
    effects : pd.DataFrame
        Primary effects table from compute_primary_effects.
    save_path : Path
        Output file path.
    """
    sns.set_theme(style="whitegrid")
    plot_df = effects.copy()
    plot_df["Label"] = plot_df["Instrument"] + " " + plot_df["Segment"]
    x = plot_df["HitDiff"].to_numpy(dtype=float)
    ci_lo = plot_df["HitCI95Low"].to_numpy(dtype=float)
    ci_hi = plot_df["HitCI95High"].to_numpy(dtype=float)
    y = np.arange(len(plot_df))
    err_lo = np.where(np.isfinite(x - ci_lo), np.maximum(x - ci_lo, 0.0), 0.0)
    err_hi = np.where(np.isfinite(ci_hi - x), np.maximum(ci_hi - x, 0.0), 0.0)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.errorbar(x, y, xerr=[err_lo, err_hi], fmt="o", color="steelblue", ecolor="0.35", capsize=3)
    ax.axvline(0.0, color="black", linewidth=1)
    ax.axvline(HIT_THRESHOLD, color="green", linewidth=1, linestyle="--", alpha=0.6,
               label=f"{HIT_THRESHOLD:.0%} threshold")
    ax.set_yticks(y)
    ax.set_yticklabels(plot_df["Label"])
    ax.set_xlabel("Inside minus outside 60m 1R-before-stop probability (bootstrap 95% CI)")
    ax.set_title("EXP-016 Primary Effect: Inside-Macro vs Outside-Macro Sweep Hit Rate")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_mae_distributions(mae_data: pd.DataFrame, save_path: Path) -> None:
    """Boxplot of MAE_R_60m for inside vs outside macro sweeps.

    Parameters
    ----------
    mae_data : pd.DataFrame
        Sweep events with InMacro and MAE_R_60m columns (pre-clipped at PLOT_R_CAP).
    save_path : Path
        Output file path.
    """
    if mae_data.empty or MAE_COL not in mae_data.columns:
        return
    sns.set_theme(style="whitegrid")
    plot_df = mae_data.copy()
    plot_df["Group"] = np.where(plot_df["InMacro"], "Inside macro", "Outside macro")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.boxplot(
        data=plot_df, x="Instrument", y=MAE_COL, hue="Group",
        palette={"Inside macro": "steelblue", "Outside macro": "salmon"},
        showfliers=False, order=INSTRUMENTS, ax=ax,
    )
    ax.set_title(f"EXP-016 60m MAE (capped at {PLOT_R_CAP}R): Inside vs Outside Macro")
    ax.set_xlabel("")
    ax.set_ylabel("MAE (R-multiple)")
    ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_window_heatmap(heatmap_data: pd.DataFrame, save_path: Path) -> None:
    """Heatmap of inside-macro sweep counts by instrument and macro window.

    Parameters
    ----------
    heatmap_data : pd.DataFrame
        Inside sweep counts grouped by Instrument and MacroWindow.
    save_path : Path
        Output file path.
    """
    if heatmap_data.empty:
        return
    sns.set_theme(style="whitegrid")
    pivot = (
        heatmap_data.pivot_table(
            index="Instrument", columns="MacroWindow", values="Count", fill_value=0,
        )
        .reindex(index=INSTRUMENTS, columns=MACRO_WINDOW_NAMES, fill_value=0)
        .astype(int)
    )
    fig, ax = plt.subplots(figsize=(11, 4))
    sns.heatmap(
        pivot, annot=True, fmt="d", cmap="Blues",
        linewidths=0.5, cbar_kws={"label": "Inside-macro sweep count"}, ax=ax,
    )
    ax.set_title("EXP-016 Inside-Macro Sweep Count by Instrument and Window")
    ax.set_xlabel("Macro window")
    ax.set_ylabel("")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ── Output writing ────────────────────────────────────────────────────────────

def write_outputs(
    events: pd.DataFrame,
    matched_outside: pd.DataFrame,
    sensitivity: pd.DataFrame,
    effects: pd.DataFrame,
    verdict: dict[str, Any],
    count_data: pd.DataFrame,
    mae_data: pd.DataFrame,
    heatmap_data: pd.DataFrame,
    plots_dir: Path,
    results_dir: Path,
) -> None:
    """Write CSV, JSON, text summary, and all plots for EXP-016.

    Parameters
    ----------
    events : pd.DataFrame
        All events with macro membership and outcome columns.
    matched_outside : pd.DataFrame
        Matched outside sweeps used in primary analysis.
    sensitivity : pd.DataFrame
        Matching fraction summary by instrument/segment.
    effects : pd.DataFrame
        Primary effects table.
    verdict : dict
        Verdict summary from evaluate_verdict.
    count_data, mae_data, heatmap_data : pd.DataFrame
        Pre-aggregated, bounded plot inputs.
    plots_dir, results_dir : Path
        Output directories (must already exist).
    """
    def json_safe(value: Any) -> Any:
        """Convert pandas/numpy containers and non-finite numbers to strict JSON."""
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

    events.to_csv(results_dir / "sweep_events.csv", index=False)
    matched_outside.to_csv(results_dir / "matched_outside_sweeps.csv", index=False)
    sensitivity.to_csv(results_dir / "matching_sensitivity.csv", index=False)
    effects.to_csv(results_dir / "primary_effects.csv", index=False)

    payload: dict[str, Any] = {
        "experiment_id": "EXP-016",
        "title": "Macro Window Interaction With Sweep Outcomes",
        "bootstrap_reps": BOOTSTRAP_REPS,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "sweep_definition": (
            "Identical to EXP-015: High sweep: High > Level + buffer AND Close < Level. "
            "Low sweep: Low < Level - buffer AND Close > Level. "
            f"Buffer = max(precision_step, {BUFFER_ATR_COEFF} * ATR14Prior). "
            "First touch per NYDate per LevelType classified as Sweep or Breach."
        ),
        "macro_windows": "EXP-012 approved windows via ict_timebar.MACRO_WINDOW_SPECS: AM1-AM5, PM1-PM4.",
        "inside_macro_definition": (
            "Event CloseTime falls within an EXP-012 macro window "
            "(MacroWindow column is not null)."
        ),
        "matching_rule": (
            "Matched outside sweeps share (Instrument, Segment, Side, NYDate) "
            "with at least one inside-macro sweep event."
        ),
        "event_floor": MIN_INSIDE_EVENTS,
        "matched_outside_floor": MIN_MATCHED_OUTSIDE_EVENTS,
        "hit_threshold_pp": HIT_THRESHOLD,
        "mae_threshold_R": MAE_THRESHOLD,
        "mae_improvement_sign": (
            "MAEImprovement = outside_median_mae - inside_median_mae; "
            "positive means inside-macro sweeps have less adverse excursion."
        ),
        "verdict_rule": (
            "FOR: inside-macro sweeps improve Hit1R >= 5pp OR MAEImprovement >= 0.25R "
            "on >= 3 instruments with InsideSweepN >= 50 and matched outside N >= 50 "
            "in both train and test segments. INCONCLUSIVE: fewer than 3 instruments "
            "meet both floors. AGAINST: floors met but neither threshold met on >= 3 "
            "instruments."
        ),
        "verdict_summary": verdict,
        "primary_effects": effects.to_dict(orient="records"),
        "matching_sensitivity": sensitivity.to_dict(orient="records"),
    }
    with (results_dir / "results.json").open("w", encoding="utf-8") as fh:
        json.dump(json_safe(payload), fh, indent=2, default=str, allow_nan=False)

    with (results_dir / "numerical_summary.txt").open("w", encoding="utf-8") as fh:
        fh.write("EXP-016 Macro Window Interaction With Sweep Outcomes\n")
        fh.write(f"Verdict: {verdict['verdict']}\n")
        fh.write(
            f"Instruments passing: {verdict['instruments_passing']}/4 "
            f"(floor met: {verdict['instruments_with_floor']}/4)\n\n"
        )
        fh.write("Primary effects (test segment, inside minus outside):\n")
        for row in effects[effects["Segment"] == "Test"].itertuples(index=False):
            fh.write(
                f"- {row.Instrument}: inside_n={row.InsideSweepN}, "
                f"matched_outside_n={row.MatchedOutsideN}, "
                f"hit_diff={row.HitDiff:.3f} CI=[{row.HitCI95Low:.3f},{row.HitCI95High:.3f}], "
                f"mae_impr={row.MAEImprovement:.3f} CI=[{row.MAECI95Low:.3f},{row.MAECI95High:.3f}], "
                f"inside_floor={row.PassEventCount}, outside_floor={row.PassMatchedOutsideCount}, "
                f"hit_pass={row.HitCriterionMet}, "
                f"mae_pass={row.MAECriterionMet}\n"
            )
        fh.write("\nMatching sensitivity (test segment):\n")
        for row in sensitivity[sensitivity["Segment"] == "Test"].itertuples(index=False):
            fh.write(
                f"- {row.Instrument}: all_outside={row.AllOutsideSweeps}, "
                f"matched={row.MatchedOutsideSweeps} ({row.MatchedFraction:.1%})\n"
            )

    plot_inside_outside_counts(count_data, plots_dir / "01_inside_outside_counts.png")
    plot_effect_intervals(effects, plots_dir / "02_effect_size_intervals.png")
    plot_mae_distributions(mae_data, plots_dir / "03_mae_distributions.png")
    plot_window_heatmap(heatmap_data, plots_dir / "04_window_heatmap.png")


# ── Orchestration ─────────────────────────────────────────────────────────────

def run_experiment() -> None:
    """Execute the EXP-016 macro window interaction workflow."""
    plots_dir = EXP_DIR / "plots"
    results_dir = EXP_DIR / "results"
    plots_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    all_events_parts: list[pd.DataFrame] = []

    for instrument in INSTRUMENTS:
        LOGGER.info("loading %s bars and computing levels", instrument)
        frame_pl, wkday_pl, levels_pd, precision_step = load_instrument_data(instrument)
        LOGGER.info(
            "%s: %d analysis rows (%d weekday)",
            instrument, len(frame_pl), len(wkday_pl),
        )
        wkday_pd = wkday_pl.to_pandas()
        events = detect_sweep_events(wkday_pd, levels_pd, instrument, precision_step)
        LOGGER.info("%s: %d candidate events", instrument, len(events))
        if events.empty:
            LOGGER.warning("%s: no events detected; skipping", instrument)
            continue

        frame_sorted = frame_pl.sort("CloseTime").to_pandas()
        ct_ns = frame_sorted["CloseTime"].values.astype(np.int64)
        highs = frame_sorted["High"].values.astype(np.float64)
        lows = frame_sorted["Low"].values.astype(np.float64)

        LOGGER.info("%s: computing outcomes for %d events", instrument, len(events))
        all_events_parts.append(compute_event_outcomes(events, ct_ns, highs, lows))

    if not all_events_parts:
        raise ValueError("No events detected across all instruments.")

    all_events = pd.concat(all_events_parts, ignore_index=True)
    matched_outside, sensitivity = build_matched_outside(all_events)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    effects = compute_primary_effects(all_events, matched_outside, rng)
    verdict = evaluate_verdict(effects)

    sweeps = all_events[all_events["EventType"] == "Sweep"]
    count_data = (
        sweeps.groupby(["Instrument", "Segment", "InMacro"], as_index=False)
        .agg(Count=("CloseTime", "count"))
    )
    mae_data = sweeps[["Instrument", "Segment", "InMacro", MAE_COL]].copy()
    mae_data[MAE_COL] = mae_data[MAE_COL].clip(upper=PLOT_R_CAP)
    heatmap_data = (
        sweeps[sweeps["InMacro"]]
        .groupby(["Instrument", "MacroWindow"], as_index=False)
        .agg(Count=("CloseTime", "count"))
    )

    write_outputs(
        all_events, matched_outside, sensitivity, effects, verdict,
        count_data, mae_data, heatmap_data, plots_dir, results_dir,
    )

    print("EXP-016 complete.")
    print(f"Verdict: {verdict['verdict']} ({verdict['instruments_passing']}/4 instruments)")
    print(f"Plots:   {plots_dir}")
    print(f"Results: {results_dir}")


def main() -> None:
    """Entry point for manual execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_experiment()


if __name__ == "__main__":
    main()
