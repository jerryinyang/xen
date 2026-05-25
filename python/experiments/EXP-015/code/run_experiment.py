"""
Experiment EXP-015: Prior High Low Sweep Reversal Behavior
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
EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-015"

BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 42
HORIZONS_MINUTES = [30, 60, 120]
BUFFER_ATR_COEFF = 0.05
# ONH/ONL levels are only fully known once the overnight window closes at 09:30 NY.
ON_LEVEL_MIN_MINUTE = OVERNIGHT_END_MINUTE  # 570

LEVEL_TYPES_HIGH = ["PDH", "ONH"]
LEVEL_TYPES_LOW = ["PDL", "ONL"]
MIN_SWEEP_EVENTS_FULL = 100
MIN_SWEEP_EVENTS_BALANCED = 50

EVENT_COLS = [
    "Instrument", "NYDate", "Segment", "CloseTime",
    "Open", "High", "Low", "Close",
    "LevelType", "Side", "EventType", "Level", "Buffer",
    "Stop", "Entry", "Risk1R",
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
        (all_bars_pl, weekday_bars_pl, levels_pd, precision_step)
        all_bars_pl is used for forward outcome bars; weekday_bars_pl for event detection.
    """
    load = load_analysis_timebars(DATA_DIR, instrument)
    train_end = train_cutoff_time(load.frame, load.train_rows)
    frame_pl = add_bar_diagnostics(add_ny_time_features(load.frame, train_end))
    levels_pd = compute_liquidity_levels(frame_pl)
    precision_step = compute_price_precision_step(frame_pl)
    wkday_pl = weekday_filter(frame_pl)
    return frame_pl, wkday_pl, levels_pd, precision_step


# ── Sweep event detection ─────────────────────────────────────────────────────

def _build_level_events(
    merged: pd.DataFrame,
    level_type: str,
) -> pd.DataFrame:
    """Build the first-touch event per NYDate for one level type.

    The first bar that penetrates the level (with buffer) on a given NYDate is
    classified as exactly one of Sweep or Breach, ensuring mutual exclusivity
    per instrument/date/level-type combination.

    Parameters
    ----------
    merged : pd.DataFrame
        Weekday bars merged with level columns; must include Buffer and NYMinuteOfDay.
    level_type : str
        One of PDH, ONH, PDL, ONL.

    Returns
    -------
    pd.DataFrame
        One row per NYDate: the first qualifying touch, classified as Sweep or Breach.
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

    first_touch = candidates.sort_values("CloseTime").groupby("NYDate", sort=False).head(1).copy()
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
        Weekday-filtered analysis bars with NY features and bar diagnostics.
    levels : pd.DataFrame
        Liquidity levels from compute_liquidity_levels.
    instrument : str
        Instrument name for level filtering.
    precision_step : float
        Buffer floor (smallest observed price increment).

    Returns
    -------
    pd.DataFrame
        Event rows with EVENT_COLS columns.
    """
    inst_lvl = levels[levels["Instrument"] == instrument][
        ["NYDate", "PDH", "PDL", "ONH", "ONL"]
    ].copy()
    merged = wkday_pd.merge(inst_lvl, on="NYDate", how="left")
    atr_safe = merged["ATR14Prior"].fillna(0.0)
    merged["Buffer"] = np.maximum(precision_step, BUFFER_ATR_COEFF * atr_safe)
    merged["Instrument"] = instrument

    parts = [
        _build_level_events(merged, lt)
        for lt in LEVEL_TYPES_HIGH + LEVEL_TYPES_LOW
    ]
    non_empty = [p for p in parts if not p.empty]
    if not non_empty:
        return pd.DataFrame(columns=EVENT_COLS)
    result = pd.concat(non_empty, ignore_index=True)
    if result.empty:
        return pd.DataFrame(columns=EVENT_COLS)
    present = [c for c in EVENT_COLS if c in result.columns]
    return result[present].reset_index(drop=True)


# ── Outcome computation ───────────────────────────────────────────────────────

def _walk_bars_for_hit(
    highs: np.ndarray,
    lows: np.ndarray,
    target: float,
    stop: float,
    is_bearish: bool,
) -> tuple[bool, bool, bool, int, int]:
    """Walk bars in order; stop at first bar that hits target or stop.

    Returns (target_hit, stop_hit, ambiguous, target_bar_idx, stop_bar_idx).
    Indices are -1 when that side is not hit; an ambiguous bar triggers both.
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
    """Return Ambiguous60, TimeToTarget1R_60m, TimeToStop_60m for the 60m horizon.

    Parameters
    ----------
    tidx, sidx : int
        Bar indices of first target and stop hit (-1 = not hit).
    start_idx : int
        Index in ct_ns of the first forward bar.
    ct_ns : np.ndarray
        Full instrument CloseTime array in nanoseconds.
    event_ns : int
        Event CloseTime in nanoseconds.
    ambiguous : bool
        Whether the event was ambiguous on the first triggering bar.

    Returns
    -------
    dict
        Three metric keys.
    """
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


def _compute_horizon_outcomes(
    h: int,
    is_bearish: bool,
    entry: float,
    risk: float,
    stop: float,
    h_highs: np.ndarray,
    h_lows: np.ndarray,
    ct_ns: np.ndarray,
    start_idx: int,
    event_ns: int,
) -> dict[str, Any]:
    """Compute MFE/MAE/hit metrics for one forecast horizon.

    Parameters
    ----------
    h : int
        Horizon in minutes.
    is_bearish : bool
        True for high-side sweep events (expecting price to fall).
    entry, risk, stop : float
        Entry price, 1R risk distance, and stop price.
    h_highs, h_lows : np.ndarray
        High/Low arrays for forward bars within the horizon window.
    ct_ns : np.ndarray
        Full instrument CloseTime array (nanoseconds) for time-to-hit.
    start_idx : int
        Index in ct_ns of the first forward bar.
    event_ns : int
        Event CloseTime in nanoseconds.

    Returns
    -------
    dict
        Metric keys prefixed with the horizon (e.g. MFE_R_60m).
    """
    h_str = f"_{h}m"
    out: dict[str, Any] = {}
    if h_highs.size == 0:
        out.update({f"MFE_R{h_str}": np.nan, f"MAE_R{h_str}": np.nan,
                    f"Hit1R{h_str}": np.nan, f"Hit2R{h_str}": np.nan})
        if h == 60:
            out.update({"Ambiguous60": False, "TimeToTarget1R_60m": np.nan, "TimeToStop_60m": np.nan})
        return out

    mfe = (entry - float(np.min(h_lows))) if is_bearish else (float(np.max(h_highs)) - entry)
    mae = (float(np.max(h_highs)) - entry) if is_bearish else (entry - float(np.min(h_lows)))
    out[f"MFE_R{h_str}"] = max(0.0, mfe) / risk
    out[f"MAE_R{h_str}"] = max(0.0, mae) / risk

    t1r = (entry - risk) if is_bearish else (entry + risk)
    t2r = (entry - 2 * risk) if is_bearish else (entry + 2 * risk)
    hit1, _, amb1, tidx, sidx = _walk_bars_for_hit(h_highs, h_lows, t1r, stop, is_bearish)
    hit2, _, amb2, _, _ = _walk_bars_for_hit(h_highs, h_lows, t2r, stop, is_bearish)
    out[f"Hit1R{h_str}"] = np.nan if amb1 else float(hit1)
    out[f"Hit2R{h_str}"] = np.nan if amb2 else float(hit2)
    if h == 60:
        out.update(_time_metrics_60m(tidx, sidx, start_idx, ct_ns, event_ns, amb1))
    return out


def _compute_single_outcomes(
    event: pd.Series,
    ct_ns: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
) -> dict[str, Any]:
    """Compute all horizon outcomes for one event row.

    Parameters
    ----------
    event : pd.Series
        Single event row with Entry, Risk1R, Stop, Side, CloseTime.
    ct_ns, highs, lows : np.ndarray
        Full sorted instrument arrays (nanosecond CloseTime, High, Low).

    Returns
    -------
    dict
        Outcome metrics across all scoped horizons.
    """
    entry = float(event["Entry"])
    risk = float(event["Risk1R"])
    stop = float(event["Stop"])
    is_bearish = event["Side"] == "High"

    nan_out: dict[str, Any] = {}
    for h in HORIZONS_MINUTES:
        h_str = f"_{h}m"
        nan_out.update({f"MFE_R{h_str}": np.nan, f"MAE_R{h_str}": np.nan,
                        f"Hit1R{h_str}": np.nan, f"Hit2R{h_str}": np.nan})
    nan_out.update({"Ambiguous60": False, "TimeToTarget1R_60m": np.nan, "TimeToStop_60m": np.nan})

    if risk <= 0:
        return nan_out

    event_ns = int(pd.Timestamp(event["CloseTime"]).value)
    start_idx = int(np.searchsorted(ct_ns, event_ns, side="right"))

    out: dict[str, Any] = {}
    for h in HORIZONS_MINUTES:
        end_ns = event_ns + h * 60 * 10**9
        end_idx = int(np.searchsorted(ct_ns, end_ns, side="right"))
        out.update(
            _compute_horizon_outcomes(
                h, is_bearish, entry, risk, stop,
                highs[start_idx:end_idx], lows[start_idx:end_idx],
                ct_ns, start_idx, event_ns,
            )
        )
    return out


def compute_event_outcomes(
    events: pd.DataFrame,
    ct_ns: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
) -> pd.DataFrame:
    """Compute forward-price outcomes for all events.

    Parameters
    ----------
    events : pd.DataFrame
        Events table from detect_sweep_events.
    ct_ns, highs, lows : np.ndarray
        Full sorted instrument bar arrays (nanosecond CloseTime, High, Low).

    Returns
    -------
    pd.DataFrame
        Events table with outcome columns appended.
    """
    rows: list[dict[str, Any]] = [
        {**dict(row), **_compute_single_outcomes(row, ct_ns, highs, lows)}
        for _, row in events.iterrows()
    ]
    return pd.DataFrame(rows)


# ── Statistical analysis ──────────────────────────────────────────────────────

def _sweep_breach_arrays(
    events: pd.DataFrame,
    instrument: str,
    segment: str,
) -> tuple[np.ndarray, np.ndarray]:
    """Return Hit1R_60m arrays for non-ambiguous sweep and breach events.

    Parameters
    ----------
    events : pd.DataFrame
        Events with outcomes.
    instrument, segment : str
        Filter keys.

    Returns
    -------
    tuple
        (sweep_hits, breach_hits) as float arrays.
    """
    col = "Hit1R_60m"
    seg = events[
        (events["Instrument"] == instrument)
        & (events["Segment"] == segment)
        & ~events["Ambiguous60"].fillna(True).astype(bool)
        & events[col].notna()
    ]
    sweep = seg[seg["EventType"] == "Sweep"][col].to_numpy(dtype=float)
    breach = seg[seg["EventType"] == "Breach"][col].to_numpy(dtype=float)
    return sweep, breach


def bootstrap_primary_diff(
    events: pd.DataFrame,
    instrument: str,
    segment: str,
    rng: np.random.Generator,
) -> dict[str, Any]:
    """Bootstrap 95% CI for Sweep minus Breach 60m 1R-before-stop probability.

    Parameters
    ----------
    events : pd.DataFrame
        All events with outcome columns.
    instrument, segment : str
        Filter keys.
    rng : np.random.Generator
        Seeded RNG for reproducibility.

    Returns
    -------
    dict
        Counts, means, point estimate, CI bounds, and pass flag.
    """
    sweep, breach = _sweep_breach_arrays(events, instrument, segment)
    base: dict[str, Any] = {
        "Instrument": instrument, "Segment": segment,
        "SweepN": int(len(sweep)), "BreachN": int(len(breach)),
        "SweepMean": float(sweep.mean()) if sweep.size else np.nan,
        "BreachMean": float(breach.mean()) if breach.size else np.nan,
        "Diff": np.nan, "CI95Low": np.nan, "CI95High": np.nan,
    }
    if sweep.size < 2 or breach.size < 2:
        return base
    diffs = np.array([
        rng.choice(sweep, size=sweep.size, replace=True).mean()
        - rng.choice(breach, size=breach.size, replace=True).mean()
        for _ in range(BOOTSTRAP_REPS)
    ])
    base["Diff"] = float(np.mean(diffs))
    base["CI95Low"] = float(np.quantile(diffs, 0.025))
    base["CI95High"] = float(np.quantile(diffs, 0.975))
    return base


def evaluate_event_count_criterion(
    events: pd.DataFrame,
    instrument: str,
    segment: str,
) -> bool:
    """Return True if sweep events meet the scoped minimum count threshold.

    Parameters
    ----------
    events : pd.DataFrame
        All events table.
    instrument, segment : str
        Filter keys.

    Returns
    -------
    bool
        True when ≥100 total sweeps, or ≥50 when balanced (≤2:1 high/low ratio).
    """
    seg = events[
        (events["Instrument"] == instrument)
        & (events["Segment"] == segment)
        & (events["EventType"] == "Sweep")
    ]
    total = len(seg)
    if total >= MIN_SWEEP_EVENTS_FULL:
        return True
    if total < MIN_SWEEP_EVENTS_BALANCED:
        return False
    high_n = int((seg["Side"] == "High").sum())
    low_n = int((seg["Side"] == "Low").sum())
    if high_n == 0 or low_n == 0:
        return False
    return bool(max(high_n, low_n) / min(high_n, low_n) <= 2.0)


def compute_all_primary_effects(
    events: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Compute bootstrap primary effects for all instrument/segment pairs.

    Parameters
    ----------
    events : pd.DataFrame
        Events with outcome columns.
    rng : np.random.Generator
        Seeded RNG.

    Returns
    -------
    pd.DataFrame
        One row per (Instrument, Segment) with effect statistics.
    """
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        for segment in ("Train", "Test"):
            row = bootstrap_primary_diff(events, instrument, segment, rng)
            row["PassEventCount"] = evaluate_event_count_criterion(events, instrument, segment)
            row["CIExcludesZero"] = bool(
                np.isfinite(row.get("CI95Low", np.nan)) and row.get("CI95Low", np.nan) > 0
            )
            row["SupportsPrimary"] = bool(
                row["PassEventCount"] and row["CIExcludesZero"]
                and np.isfinite(row.get("Diff", np.nan))
            )
            rows.append(row)
    return pd.DataFrame(rows)


def evaluate_hypothesis_support(effects: pd.DataFrame) -> dict[str, Any]:
    """Summarize hypothesis support verdict from primary effects table.

    Parameters
    ----------
    effects : pd.DataFrame
        Output from compute_all_primary_effects.

    Returns
    -------
    dict
        Verdict (SUPPORTED / AGAINST / INCONCLUSIVE), count, and per-instrument flags.
    """
    per_instrument: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        sub = effects[effects["Instrument"] == instrument]
        train_pass = bool(sub[sub["Segment"] == "Train"]["SupportsPrimary"].any())
        test_pass = bool(sub[sub["Segment"] == "Test"]["SupportsPrimary"].any())
        per_instrument.append({
            "Instrument": instrument,
            "TrainPass": train_pass,
            "TestPass": test_pass,
            # Support requires test-segment confirmation; train-only evidence is insufficient.
            "InstrumentPass": test_pass,
        })
    support_df = pd.DataFrame(per_instrument)
    n_support = int(support_df["InstrumentPass"].sum())
    # INCONCLUSIVE when fewer than 3 instruments have adequate test-segment event counts.
    test_effects = effects[effects["Segment"] == "Test"]
    n_count_pass_test = int(
        test_effects.groupby("Instrument")["PassEventCount"].any().sum()
    )
    if n_support >= 3:
        verdict = "SUPPORTED"
    elif n_count_pass_test < 3:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "AGAINST"
    return {
        "verdict": verdict,
        "supporting_instruments": n_support,
        "per_instrument": per_instrument,
    }


def summarize_event_counts(events: pd.DataFrame) -> pd.DataFrame:
    """Count events by instrument, segment, level type, side, and event type.

    Parameters
    ----------
    events : pd.DataFrame
        Events table (with or without outcome columns).

    Returns
    -------
    pd.DataFrame
        Count table sorted by instrument.
    """
    if events.empty:
        return pd.DataFrame()
    scoped = events[events["Segment"].isin(["Train", "Test"])]
    return (
        scoped.groupby(["Instrument", "Segment", "LevelType", "Side", "EventType"], as_index=False)
        .agg(Count=("CloseTime", "count"))
        .sort_values(["Instrument", "Segment", "LevelType", "Side", "EventType"])
        .reset_index(drop=True)
    )


# ── Plots ─────────────────────────────────────────────────────────────────────

def plot_event_count_waterfall(events: pd.DataFrame, save_path: Path) -> None:
    """Grouped bar chart of sweep and breach event counts per instrument.

    Parameters
    ----------
    events : pd.DataFrame
        Events table.
    save_path : Path
        Output file path.
    """
    counts = summarize_event_counts(events)
    if counts.empty:
        return
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, segment in zip(axes, ["Train", "Test"]):
        sub = counts[counts["Segment"] == segment]
        sns.barplot(
            data=sub, x="Instrument", y="Count", hue="EventType",
            palette={"Sweep": "steelblue", "Breach": "salmon"},
            order=INSTRUMENTS, ax=ax,
        )
        ax.set_title(f"EXP-015 Event Counts — {segment}")
        ax.set_xlabel("")
        ax.set_ylabel("Events")
        ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_1r_diff_intervals(effects: pd.DataFrame, save_path: Path) -> None:
    """Forest plot of Sweep minus Breach 60m 1R-before-stop probability differences.

    Parameters
    ----------
    effects : pd.DataFrame
        Primary effects table from compute_all_primary_effects.
    save_path : Path
        Output file path.
    """
    sns.set_theme(style="whitegrid")
    plot_df = effects[effects["Segment"].isin(["Train", "Test"])].copy()
    plot_df["Label"] = plot_df["Instrument"] + " " + plot_df["Segment"]
    x = plot_df["Diff"].to_numpy(dtype=float)
    ci_lo = plot_df["CI95Low"].to_numpy(dtype=float)
    ci_hi = plot_df["CI95High"].to_numpy(dtype=float)
    y = np.arange(len(plot_df))
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.errorbar(
        x, y,
        xerr=[np.maximum(x - ci_lo, 0.0), np.maximum(ci_hi - x, 0.0)],
        fmt="o", color="steelblue", ecolor="0.35", capsize=3,
    )
    ax.axvline(0.0, color="black", linewidth=1)
    ax.set_yticks(y)
    ax.set_yticklabels(plot_df["Label"])
    ax.set_xlabel("Sweep minus Breach 60m 1R-before-stop probability (bootstrap 95% CI)")
    ax.set_title("EXP-015 Primary Effect: Failed Sweep vs Breach")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_mfe_mae_distributions(events: pd.DataFrame, save_path: Path) -> None:
    """Boxplot of 60m MFE and MAE R-multiples for sweep versus breach events.

    Parameters
    ----------
    events : pd.DataFrame
        Events table with MFE_R_60m and MAE_R_60m columns.
    save_path : Path
        Output file path.
    """
    sns.set_theme(style="whitegrid")
    scoped = events[events["Segment"].isin(["Train", "Test"])]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=False)
    for ax, col in zip(axes, ("MFE_R_60m", "MAE_R_60m")):
        if col not in events.columns:
            continue
        plot_df = scoped[["Instrument", "EventType", col]].copy()
        plot_df[col] = plot_df[col].clip(upper=PLOT_R_CAP)
        sns.boxplot(
            data=plot_df, x="Instrument", y=col, hue="EventType",
            palette={"Sweep": "steelblue", "Breach": "salmon"},
            showfliers=False, order=INSTRUMENTS, ax=ax,
        )
        ax.set_title(f"EXP-015 60m {col} (capped at {PLOT_R_CAP}R)")
        ax.set_xlabel("")
        ax.set_ylabel("R-multiple")
        ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_time_to_stop_target(events: pd.DataFrame, save_path: Path) -> None:
    """KDE of time-to-1R-target and time-to-stop within the 60m horizon.

    Parameters
    ----------
    events : pd.DataFrame
        Events table with TimeToTarget1R_60m and TimeToStop_60m columns.
    save_path : Path
        Output file path.
    """
    if "TimeToTarget1R_60m" not in events.columns or "TimeToStop_60m" not in events.columns:
        return
    sns.set_theme(style="whitegrid")
    seg_ev = events[events["Segment"].isin(["Train", "Test"])]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, (col, label) in zip(
        axes,
        (("TimeToTarget1R_60m", "1R Target"), ("TimeToStop_60m", "Stop")),
    ):
        for event_type, color in (("Sweep", "steelblue"), ("Breach", "salmon")):
            vals = seg_ev.loc[seg_ev["EventType"] == event_type, col].dropna()
            if vals.size > 1:
                sns.kdeplot(vals, ax=ax, label=event_type, color=color, fill=True, alpha=0.3)
        ax.set_xlabel(f"Minutes to {label} from event bar close")
        ax.set_ylabel("Density")
        ax.set_title(f"EXP-015 Time-to-{label} Distribution (60m horizon)")
        ax.set_xlim(0, 65)
        ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ── Output writing ────────────────────────────────────────────────────────────

def compute_secondary_effects(events: pd.DataFrame) -> pd.DataFrame:
    """Compute descriptive summary statistics for secondary outcome metrics.

    Produces mean, median, Q25, Q75, and count for MFE_R_60m, MAE_R_60m,
    Hit2R_60m, TimeToTarget1R_60m, and TimeToStop_60m, grouped by
    Instrument, Segment, Side, LevelType, and EventType.

    Parameters
    ----------
    events : pd.DataFrame
        Events table with outcome columns.

    Returns
    -------
    pd.DataFrame
        One row per group with descriptive summary columns.
    """
    scoped = events[events["Segment"].isin(["Train", "Test"])].copy()
    group_keys = ["Instrument", "Segment", "Side", "LevelType", "EventType"]
    secondary_cols = [
        "MFE_R_60m", "MAE_R_60m", "Hit2R_60m", "TimeToTarget1R_60m", "TimeToStop_60m",
    ]
    available = [c for c in secondary_cols if c in scoped.columns]
    if not available or scoped.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for keys, group in scoped.groupby(group_keys, sort=True):
        row: dict[str, Any] = dict(zip(group_keys, keys))
        row["N"] = len(group)
        for col in available:
            vals = group[col].dropna()
            n = int(vals.size)
            row[f"{col}_n"] = n
            row[f"{col}_mean"] = float(vals.mean()) if n else np.nan
            row[f"{col}_median"] = float(vals.median()) if n else np.nan
            row[f"{col}_q25"] = float(vals.quantile(0.25)) if n else np.nan
            row[f"{col}_q75"] = float(vals.quantile(0.75)) if n else np.nan
        rows.append(row)
    return pd.DataFrame(rows).reset_index(drop=True)


def write_outputs(
    events: pd.DataFrame,
    counts: pd.DataFrame,
    effects: pd.DataFrame,
    secondary: pd.DataFrame,
    support: dict[str, Any],
    precision_steps: dict[str, float],
    plots_dir: Path,
    results_dir: Path,
) -> None:
    """Write CSV, JSON, text summary, and all plots for EXP-015.

    Parameters
    ----------
    events, counts, effects, secondary : pd.DataFrame
        Analysis outputs.
    support : dict
        Hypothesis support summary.
    precision_steps : dict
        Per-instrument price precision step values used for sweep buffers.
    plots_dir, results_dir : Path
        Output directories (must already exist).
    """
    events.to_csv(results_dir / "sweep_events.csv", index=False)
    counts.to_csv(results_dir / "event_counts.csv", index=False)
    effects.to_csv(results_dir / "primary_effects.csv", index=False)
    if not secondary.empty:
        secondary.to_csv(results_dir / "secondary_effects.csv", index=False)

    payload: dict[str, Any] = {
        "experiment_id": "EXP-015",
        "title": "Prior High Low Sweep Reversal Behavior",
        "bootstrap_reps": BOOTSTRAP_REPS,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "sweep_definition": (
            "High sweep: High > Level + buffer AND Close < Level. "
            "Low sweep: Low < Level - buffer AND Close > Level. "
            f"Buffer = max(price_precision_step, {BUFFER_ATR_COEFF} * ATR14Prior). "
            "First touch per NYDate per LevelType classified as exactly Sweep or Breach."
        ),
        "on_level_restriction": (
            f"ONH/ONL applied only for bars at NYMinuteOfDay >= {ON_LEVEL_MIN_MINUTE} "
            "(09:30 NY) to avoid look-ahead before the overnight window closes."
        ),
        "ambiguous_rule": (
            "Events where stop and 1R target both trigger in the same bar "
            "are excluded from 1R-before-stop probability comparisons."
        ),
        "support_verdict_rule": (
            "InstrumentPass requires test-segment CI to exclude zero with adequate "
            "event counts. Train-only evidence does not satisfy the support criterion."
        ),
        "price_precision_steps": precision_steps,
        "support_summary": support,
        "primary_effects": effects[
            effects["Segment"].isin(["Train", "Test"])
        ].to_dict(orient="records"),
        "secondary_effects": secondary.to_dict(orient="records") if not secondary.empty else [],
    }
    with (results_dir / "results.json").open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)

    with (results_dir / "numerical_summary.txt").open("w", encoding="utf-8") as fh:
        fh.write("EXP-015 Prior High Low Sweep Reversal Behavior\n")
        fh.write(f"Verdict: {support['verdict']}\n")
        fh.write(f"Supporting instruments: {support['supporting_instruments']}/4\n\n")
        fh.write("Primary effects (Sweep minus Breach 60m 1R-before-stop probability):\n")
        for row in effects[effects["Segment"].isin(["Train", "Test"])].itertuples(index=False):
            fh.write(
                f"- {row.Instrument} {row.Segment}: "
                f"sweep_n={row.SweepN}, sweep_mean={row.SweepMean:.3f}, "
                f"breach_n={row.BreachN}, breach_mean={row.BreachMean:.3f}, "
                f"diff={row.Diff:.3f}, CI=[{row.CI95Low:.3f}, {row.CI95High:.3f}], "
                f"count_pass={row.PassEventCount}, supports={row.SupportsPrimary}\n"
            )

    plot_event_count_waterfall(events, plots_dir / "01_event_count_waterfall.png")
    plot_1r_diff_intervals(effects, plots_dir / "02_1r_diff_intervals.png")
    plot_mfe_mae_distributions(events, plots_dir / "03_mfe_mae_distributions.png")
    plot_time_to_stop_target(events, plots_dir / "04_time_to_stop_target.png")


# ── Orchestration ─────────────────────────────────────────────────────────────

def run_experiment() -> None:
    """Execute the EXP-015 prior high/low sweep reversal behavior workflow."""
    plots_dir = EXP_DIR / "plots"
    results_dir = EXP_DIR / "results"
    plots_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    all_events_parts: list[pd.DataFrame] = []
    precision_steps: dict[str, float] = {}

    for instrument in INSTRUMENTS:
        LOGGER.info("loading %s bars and computing levels", instrument)
        frame_pl, wkday_pl, levels_pd, precision_step = load_instrument_data(instrument)
        precision_steps[instrument] = precision_step
        LOGGER.info(
            "%s: %d analysis rows (%d weekday), precision_step=%.6f",
            instrument, len(frame_pl), len(wkday_pl), precision_step,
        )

        wkday_pd = wkday_pl.to_pandas()
        events = detect_sweep_events(wkday_pd, levels_pd, instrument, precision_step)
        LOGGER.info("%s: detected %d candidate events", instrument, len(events))

        if events.empty:
            LOGGER.warning("%s: no events detected; skipping outcome computation", instrument)
            continue

        # Use all analysis-set bars for forward outcome computation so that events
        # near session boundaries are not penalized by missing weekend bars.
        frame_sorted = frame_pl.sort("CloseTime").to_pandas()
        ct_ns = frame_sorted["CloseTime"].values.astype(np.int64)
        highs = frame_sorted["High"].values.astype(np.float64)
        lows = frame_sorted["Low"].values.astype(np.float64)

        LOGGER.info("%s: computing outcomes for %d events", instrument, len(events))
        events_out = compute_event_outcomes(events, ct_ns, highs, lows)
        all_events_parts.append(events_out)

    if not all_events_parts:
        raise ValueError("No events were detected across all instruments.")

    all_events = pd.concat(all_events_parts, ignore_index=True)
    counts = summarize_event_counts(all_events)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    effects = compute_all_primary_effects(all_events, rng)
    support = evaluate_hypothesis_support(effects)
    secondary = compute_secondary_effects(all_events)

    write_outputs(all_events, counts, effects, secondary, support, precision_steps, plots_dir, results_dir)

    print("EXP-015 complete.")
    print(f"Verdict: {support['verdict']} ({support['supporting_instruments']}/4 instruments)")
    print(f"Plots:   {plots_dir}")
    print(f"Results: {results_dir}")


def main() -> None:
    """Entry point for manual execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_experiment()


if __name__ == "__main__":
    main()
