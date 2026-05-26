"""
Experiment EXP-025: Fixed 1 to 2 Risk Reward Justification
Implements the analysis plan from analysis-plan.md.

Predeclared config (locked before results are inspected):
  entry_source     : EXP-024 SecondCandleOpen feasible entries
  exit_variants    : 1R, 1.5R, 2R, 3R, TimeStop60, NearestLiquidity
  stop_rule        : EXP-015 original stop (inherited via EXP-021 / EXP-024 chain)
  horizon_minutes  : 60
  train_floor      : >= 100 feasible events per instrument
  test_floor       : >= 50 feasible events per instrument
  min_eligible     : >= 3 instruments must meet both floors
"""
from __future__ import annotations

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
    add_ny_time_features,
    compute_liquidity_levels,
    load_analysis_timebars,
    train_cutoff_time,
)

LOGGER = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-025"
EXP024_RESULTS_DIR = PYTHON_ROOT / "experiments" / "EXP-024" / "results"

OUTCOME_HORIZON_MIN: int = 60
BOOTSTRAP_REPS: int = 10_000
BOOTSTRAP_SEED: int = 42
TRAIN_FLOOR: int = 100
TEST_FLOOR: int = 50
MIN_ELIGIBLE_INSTRUMENTS: int = 3
PLOT_R_CAP: float = 6.0
PLOT_SAMPLE_SEED: int = 42
PLOT_MAX_POINTS: int = 5_000
CRITERION_VERSION: str = "superiority_v2"

EXIT_VARIANTS: list[str] = ["1R", "1.5R", "2R", "3R", "TimeStop60", "NearestLiquidity"]
FIXED_R_LABELS: list[str] = ["1R", "1.5R", "2R", "3R"]
FIXED_R_VALUES: dict[str, float] = {"1R": 1.0, "1.5R": 1.5, "2R": 2.0, "3R": 3.0}
COMPARATOR_VARIANTS: list[str] = [
    "1R", "1.5R", "3R", "TimeStop60", "NearestLiquidity",
]

EXP024_REQUIRED_COLS: set[str] = {
    "Instrument", "NYDate", "Segment", "LevelType", "Side",
    "EntryProxy", "EntryTime", "Entry", "Stop", "Risk1R",
    "RiskFeasible", "Return_R_60m", "Ambiguous60",
}


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_second_candle_entries() -> pd.DataFrame:
    """Load EXP-024 SecondCandleOpen feasible entries as the approved H6 entry set.

    Returns
    -------
    pd.DataFrame
        Rows filtered to EntryProxy==SecondCandleOpen, RiskFeasible==True,
        Ambiguous60==False with EntryTime parsed as datetime.

    Raises
    ------
    FileNotFoundError
        If the EXP-024 result file is absent.
    ValueError
        If required columns are missing.
    """
    path = EXP024_RESULTS_DIR / "entry_timing_outcomes.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required prerequisite not found: {path}")
    df = pd.read_csv(path)
    missing = sorted(EXP024_REQUIRED_COLS.difference(df.columns))
    if missing:
        raise ValueError(f"EXP-024 entry_timing_outcomes.csv missing columns: {missing}")
    df = df[
        (df["EntryProxy"] == "SecondCandleOpen")
        & (df["RiskFeasible"].astype(bool))
        & (~df["Ambiguous60"].astype(bool))
    ].copy()
    df["EntryTime"] = pd.to_datetime(df["EntryTime"])
    df["NYDate"] = pd.to_datetime(df["NYDate"]).dt.date
    df["Return_R_60m"] = pd.to_numeric(df["Return_R_60m"], errors="coerce")
    return df.reset_index(drop=True)


def load_instrument_data(
    instrument: str,
) -> tuple[pd.DataFrame, dict[tuple[str, Any], dict[str, float | None]]]:
    """Load analysis bars and compute liquidity levels for one instrument in one pass.

    Parameters
    ----------
    instrument : str
        Instrument symbol (e.g. "EURUSD").

    Returns
    -------
    tuple[pd.DataFrame, dict]
        (bars_pandas, liq_index) where liq_index maps (instrument, ny_date)
        to {"PDH", "PDL", "ONH", "ONL"}.
    """
    loaded = load_analysis_timebars(DATA_DIR, instrument)
    frame = add_bar_diagnostics(loaded.frame)
    cutoff = train_cutoff_time(frame, loaded.train_rows)
    frame = add_ny_time_features(frame, cutoff)
    levels_df = compute_liquidity_levels(frame)

    liq_index: dict[tuple[str, Any], dict[str, float | None]] = {}
    for _, row in levels_df.iterrows():
        key = (instrument, _normalize_ny_date(row["NYDate"]))
        liq_index[key] = {
            "PDH": _to_float_or_none(row.get("PDH")),
            "PDL": _to_float_or_none(row.get("PDL")),
            "ONH": _to_float_or_none(row.get("ONH")),
            "ONL": _to_float_or_none(row.get("ONL")),
        }

    bars = frame.sort("CloseTime").to_pandas()
    bars["CloseTime"] = pd.to_datetime(bars["CloseTime"])
    bars["OpenTime"] = pd.to_datetime(bars["OpenTime"])
    return bars.reset_index(drop=True), liq_index


def _normalize_ny_date(value: Any) -> Any:
    """Normalize NYDate values so prerequisite CSVs and computed levels join."""
    if pd.isna(value):
        return value
    return pd.to_datetime(value).date()


def _to_float_or_none(val: Any) -> float | None:
    """Convert a value to float if finite, else None."""
    try:
        f = float(val)
        return f if np.isfinite(f) else None
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Liquidity target helpers
# ---------------------------------------------------------------------------

def find_nearest_opposing_liquidity(
    entry: float,
    side: str,
    levels: dict[str, float | None],
) -> float | None:
    """Return the nearest opposing liquidity level as the exit target price.

    For a bullish entry (side=="Low"), the opposing levels are PDH and ONH above entry.
    For a bearish entry (side=="High"), the opposing levels are PDL and ONL below entry.

    Parameters
    ----------
    entry : float
        Entry price.
    side : str
        "Low" for bullish, "High" for bearish.
    levels : dict
        Dictionary of {"PDH", "PDL", "ONH", "ONL"} values.

    Returns
    -------
    float or None
        Nearest opposing liquidity price, or None if none found.
    """
    is_bearish = side == "High"
    col_names = ("PDL", "ONL") if is_bearish else ("PDH", "ONH")
    candidates: list[float] = []
    for col in col_names:
        val = levels.get(col)
        if val is not None:
            if not is_bearish and val > entry:
                candidates.append(val)
            elif is_bearish and val < entry:
                candidates.append(val)
    if not candidates:
        return None
    return min(candidates) if not is_bearish else max(candidates)


# ---------------------------------------------------------------------------
# Exit simulation
# ---------------------------------------------------------------------------

def simulate_all_exits(
    entry: float,
    stop: float,
    risk: float,
    side: str,
    entry_time: pd.Timestamp,
    return_r_60m: float,
    close_ns: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    liq_target: float | None,
) -> dict[str, Any]:
    """Walk forward bars once to compute all exit-variant realized-R values.

    Parameters
    ----------
    entry : float
        Entry price.
    stop : float
        Stop price.
    risk : float
        Risk1R (stop distance in price units).
    side : str
        "Low" (bullish) or "High" (bearish).
    entry_time : pd.Timestamp
        Entry time; forward bars start after this timestamp.
    return_r_60m : float
        Pre-computed 60-minute return in R units (for TimeStop60 variant).
    close_ns : np.ndarray
        CloseTime values as int64 nanoseconds for the full instrument bar array.
    highs : np.ndarray
        Full instrument High array.
    lows : np.ndarray
        Full instrument Low array.
    closes : np.ndarray
        Full instrument Close array.
    liq_target : float or None
        Nearest opposing liquidity price, or None.

    Returns
    -------
    dict
        Keys: "{variant}_R" for all EXIT_VARIANTS and "{variant}_HoldBars".
    """
    is_bearish = side == "High"
    entry_ns = int(entry_time.value)
    start_idx = int(np.searchsorted(close_ns, entry_ns, side="right"))
    end_ns = entry_ns + OUTCOME_HORIZON_MIN * 60 * 10**9
    end_idx = int(np.searchsorted(close_ns, end_ns, side="right"))
    fwd_highs = highs[start_idx:end_idx]
    fwd_lows = lows[start_idx:end_idx]
    fwd_closes = closes[start_idx:end_idx]
    n_bars = len(fwd_highs)

    result: dict[str, Any] = {
        "TimeStop60_R": float(return_r_60m) if np.isfinite(return_r_60m) else np.nan,
        "TimeStop60_HoldBars": float(n_bars),
        "NearestLiquidity_R": np.nan,
        "NearestLiquidity_HoldBars": np.nan,
        "NearestLiquidity_TargetR": np.nan,
    }

    targets: dict[str, float] = {}
    for label, mult in FIXED_R_VALUES.items():
        targets[label] = entry - mult * risk if is_bearish else entry + mult * risk

    liq_target_r: float | None = None
    if liq_target is not None and np.isfinite(liq_target) and risk > 0:
        liq_dist = abs(liq_target - entry) / risk
        if liq_dist > 0:
            targets["NearestLiquidity"] = liq_target
            liq_target_r = liq_dist

    if n_bars == 0:
        for label in FIXED_R_LABELS:
            result[f"{label}_R"] = np.nan
            result[f"{label}_HoldBars"] = np.nan
        return result

    stop_bar: int | None = None
    first_hit: dict[str, int] = {}

    for bar_idx in range(n_bars):
        h = float(fwd_highs[bar_idx])
        lo = float(fwd_lows[bar_idx])
        if stop_bar is None:
            if (is_bearish and h >= stop) or (not is_bearish and lo <= stop):
                stop_bar = bar_idx
        for label, t_price in targets.items():
            if label not in first_hit:
                if (is_bearish and lo <= t_price) or (not is_bearish and h >= t_price):
                    first_hit[label] = bar_idx

    end_close = float(fwd_closes[-1]) if n_bars > 0 else np.nan
    time_r_fallback = (entry - end_close) / risk if is_bearish else (end_close - entry) / risk

    for label, t_price in targets.items():
        t_bar = first_hit.get(label)
        if t_bar is None:
            realized = float(time_r_fallback) if np.isfinite(time_r_fallback) else np.nan
            hold_bars = float(n_bars)
        elif stop_bar is not None and t_bar == stop_bar:
            realized = np.nan
            hold_bars = np.nan
        elif stop_bar is not None and stop_bar < t_bar:
            realized = -1.0
            hold_bars = float(stop_bar + 1)
        else:
            hold_bars = float(t_bar + 1)
            if label == "NearestLiquidity":
                realized = float(liq_target_r) if liq_target_r is not None else np.nan
            else:
                realized = float(FIXED_R_VALUES[label])

        if label == "NearestLiquidity":
            result["NearestLiquidity_R"] = realized
            result["NearestLiquidity_HoldBars"] = hold_bars
            result["NearestLiquidity_TargetR"] = (
                float(liq_target_r) if liq_target_r is not None else np.nan
            )
        else:
            result[f"{label}_R"] = realized
            result[f"{label}_HoldBars"] = hold_bars

    for label in FIXED_R_LABELS:
        if f"{label}_R" not in result:
            result[f"{label}_R"] = np.nan
            result[f"{label}_HoldBars"] = np.nan

    return result


def build_exit_outcomes(
    entries: pd.DataFrame,
    bars_by_instrument: dict[str, pd.DataFrame],
    liq_index: dict[tuple[str, Any], dict[str, float | None]],
) -> pd.DataFrame:
    """Compute all exit-variant realized-R values for each approved entry.

    Parameters
    ----------
    entries : pd.DataFrame
        EXP-024 SecondCandleOpen feasible entries.
    bars_by_instrument : dict
        Instrument -> analysis bars pandas DataFrame.
    liq_index : dict
        (instrument, ny_date) -> liquidity levels dict.

    Returns
    -------
    pd.DataFrame
        One row per entry with columns for each exit variant's R and HoldBars.
    """
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        bars = bars_by_instrument[instrument]
        close_ns = bars["CloseTime"].values.astype(np.int64)
        highs = bars["High"].to_numpy(dtype=float)
        lows = bars["Low"].to_numpy(dtype=float)
        closes = bars["Close"].to_numpy(dtype=float)

        inst_entries = entries[entries["Instrument"] == instrument]
        for _, ev in inst_entries.iterrows():
            entry = float(ev["Entry"])
            stop = float(ev["Stop"])
            risk = float(ev["Risk1R"])
            side = str(ev["Side"])
            entry_time = pd.Timestamp(ev["EntryTime"])
            return_r_60m = float(ev["Return_R_60m"]) if pd.notna(ev["Return_R_60m"]) else np.nan
            ny_date = _normalize_ny_date(ev["NYDate"])
            levels = liq_index.get((instrument, ny_date), {})
            liq_target = find_nearest_opposing_liquidity(entry, side, levels)

            exits = simulate_all_exits(
                entry, stop, risk, side, entry_time, return_r_60m,
                close_ns, highs, lows, closes, liq_target,
            )
            rows.append({
                "Instrument": instrument,
                "NYDate": ny_date,
                "Segment": ev["Segment"],
                "Side": side,
                "LevelType": ev.get("LevelType", ""),
                "EntryTime": entry_time,
                "Entry": entry,
                "Stop": stop,
                "Risk1R": risk,
                **exits,
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def aggregate_exit_summary(outcomes: pd.DataFrame) -> pd.DataFrame:
    """Compute mean realized R and positive-return rate per variant/instrument/segment.

    Parameters
    ----------
    outcomes : pd.DataFrame
        Exit outcomes table from build_exit_outcomes.

    Returns
    -------
    pd.DataFrame
        Summary with columns Instrument, Segment, ExitVariant, N, N_valid,
        MeanReturn_R, HitRate.
    """
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        for segment in ("Train", "Test"):
            grp = outcomes[
                (outcomes["Instrument"] == instrument) & (outcomes["Segment"] == segment)
            ]
            n = len(grp)
            for variant in EXIT_VARIANTS:
                col = f"{variant}_R"
                if col not in grp.columns:
                    continue
                vals = grp[col].dropna()
                n_valid = len(vals)
                mean_r = float(vals.mean()) if n_valid > 0 else np.nan
                hit_rate = float((vals > 0).mean()) if n_valid > 0 else np.nan
                rows.append({
                    "Instrument": instrument,
                    "Segment": segment,
                    "ExitVariant": variant,
                    "N": n,
                    "N_valid": n_valid,
                    "MeanReturn_R": mean_r,
                    "HitRate": hit_rate,
                })
    return pd.DataFrame(rows)


def _bootstrap_mean_diff(
    a: np.ndarray,
    b: np.ndarray,
    rng: np.random.Generator,
    reps: int,
) -> tuple[float, float, float]:
    """Bootstrap mean difference (a minus b) with 95% CI.

    Parameters
    ----------
    a, b : np.ndarray
        Arrays of realized-R values.
    rng : np.random.Generator
        Seeded random generator.
    reps : int
        Number of bootstrap resamples.

    Returns
    -------
    tuple[float, float, float]
        (mean_diff, ci_lo, ci_hi) — all NaN if either array is empty.
    """
    if len(a) == 0 or len(b) == 0:
        return np.nan, np.nan, np.nan
    n_a, n_b = len(a), len(b)
    diffs = np.array([
        rng.choice(a, n_a, replace=True).mean() - rng.choice(b, n_b, replace=True).mean()
        for _ in range(reps)
    ])
    return float(np.mean(diffs)), float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))


def run_bootstrap_comparisons(outcomes: pd.DataFrame) -> pd.DataFrame:
    """Bootstrap 2R realized-R versus each alternative exit variant.

    Parameters
    ----------
    outcomes : pd.DataFrame
        Exit outcomes table.

    Returns
    -------
    pd.DataFrame
        One row per (Instrument, Segment, alternative) with mean difference and 95% CI.
    """
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        for segment in ("Train", "Test"):
            grp = outcomes[
                (outcomes["Instrument"] == instrument) & (outcomes["Segment"] == segment)
            ]
            base_2r = grp["2R_R"].dropna().to_numpy()
            for variant in EXIT_VARIANTS:
                if variant == "2R":
                    continue
                col = f"{variant}_R"
                if col not in grp.columns:
                    continue
                alt_vals = grp[col].dropna().to_numpy()
                mean_diff, ci_lo, ci_hi = _bootstrap_mean_diff(base_2r, alt_vals, rng, BOOTSTRAP_REPS)
                rows.append({
                    "Instrument": instrument,
                    "Segment": segment,
                    "Variant2R_vs": variant,
                    "N_2R": len(base_2r),
                    "N_alt": len(alt_vals),
                    "MeanDiff_2R_minus_alt": mean_diff,
                    "CI_Lo": ci_lo,
                    "CI_Hi": ci_hi,
                    "CI_Excludes_Zero": bool(
                        np.isfinite(ci_lo) and np.isfinite(ci_hi)
                        and (ci_lo > 0 or ci_hi < 0)
                    ),
                    "TwoR_Dominated": bool(
                        np.isfinite(ci_lo) and np.isfinite(ci_hi) and ci_hi < 0
                    ),
                })
    return pd.DataFrame(rows)


def evaluate_h6_verdict(
    bootstrap: pd.DataFrame,
    summary: pd.DataFrame,
) -> dict[str, Any]:
    """Evaluate the H6 verdict: is 2R justified vs alternatives?

    Support criterion: 2R has positive evidence of superiority (CI_Lo > 0)
    against at least one comparator, is not dominated by any comparator, and
    all scoped comparators have valid outcomes on at least MIN_ELIGIBLE_INSTRUMENTS
    instruments in the test segment.
    Against: 2R is dominated (CI_Hi < 0 for any alternative) on >= 2 instruments.
    Inconclusive: fewer than MIN_ELIGIBLE_INSTRUMENTS meet the event/comparator
    floor, or 2R is neither superior nor dominated.

    Parameters
    ----------
    bootstrap : pd.DataFrame
        Bootstrap comparison results from run_bootstrap_comparisons.
    summary : pd.DataFrame
        Exit summary from aggregate_exit_summary.

    Returns
    -------
    dict
        verdict, reason, instruments_floor_met, instruments_passing, per_instrument.
    """
    per_instrument: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        test_2r = summary[
            (summary["Instrument"] == instrument)
            & (summary["Segment"] == "Test")
            & (summary["ExitVariant"] == "2R")
        ]
        n_test = int(test_2r["N_valid"].sum()) if not test_2r.empty else 0
        meets_floor = n_test >= TEST_FLOOR

        missing_comparators: list[str] = []
        for variant in COMPARATOR_VARIANTS:
            row = summary[
                (summary["Instrument"] == instrument)
                & (summary["Segment"] == "Test")
                & (summary["ExitVariant"] == variant)
            ]
            n_valid = int(row["N_valid"].sum()) if not row.empty else 0
            if n_valid < TEST_FLOOR:
                missing_comparators.append(variant)

        dominated_by: list[str] = []
        superior_to: list[str] = []
        if meets_floor:
            test_bs = bootstrap[
                (bootstrap["Instrument"] == instrument)
                & (bootstrap["Segment"] == "Test")
            ]
            dominated_by = list(
                test_bs.loc[test_bs["TwoR_Dominated"], "Variant2R_vs"].unique()
            )
            superior_to = list(
                test_bs.loc[
                    test_bs["CI_Lo"].gt(0) & test_bs["Variant2R_vs"].isin(COMPARATOR_VARIANTS),
                    "Variant2R_vs",
                ].unique()
            )

        per_instrument.append({
            "Instrument": instrument,
            "N_2R_Test": n_test,
            "MeetsFloor": meets_floor,
            "MissingComparators": missing_comparators,
            "DominatedBy": dominated_by,
            "SuperiorTo": superior_to,
            "Pass": (
                meets_floor
                and not missing_comparators
                and len(dominated_by) == 0
                and len(superior_to) > 0
            ),
        })

    n_floor_met = sum(1 for r in per_instrument if r["MeetsFloor"])
    n_full_comparison = sum(
        1 for r in per_instrument if r["MeetsFloor"] and not r["MissingComparators"]
    )
    n_passing = sum(1 for r in per_instrument if r["Pass"])
    n_dominated = sum(1 for r in per_instrument if r["DominatedBy"])

    if n_floor_met < MIN_ELIGIBLE_INSTRUMENTS:
        verdict = "INCONCLUSIVE"
        reason = (
            f"Only {n_floor_met}/{len(INSTRUMENTS)} instruments meet the "
            f"{TEST_FLOOR} test-event floor."
        )
    elif n_full_comparison < MIN_ELIGIBLE_INSTRUMENTS:
        verdict = "INCONCLUSIVE"
        reason = (
            f"Only {n_full_comparison}/{len(INSTRUMENTS)} instruments have valid "
            f"2R and comparator outcomes; scoped alternatives are missing."
        )
    elif n_passing >= MIN_ELIGIBLE_INSTRUMENTS:
        verdict = "FOR"
        reason = (
            f"2R shows superiority evidence and no domination on "
            f"{n_passing}/{len(INSTRUMENTS)} instruments."
        )
    elif n_dominated >= 2:
        verdict = "AGAINST"
        reason = (
            f"2R is dominated by at least one comparator on "
            f"{n_dominated}/{n_full_comparison} comparable instruments."
        )
    else:
        verdict = "INCONCLUSIVE"
        reason = (
            f"2R is not positively justified: {n_passing} instruments show "
            f"superiority evidence, {n_dominated} are dominated, "
            f"{n_full_comparison} are fully comparable."
        )

    return {
        "verdict": verdict,
        "criterion_version": CRITERION_VERSION,
        "reason": reason,
        "instruments_floor_met": n_floor_met,
        "instruments_fully_comparable": n_full_comparison,
        "instruments_passing": n_passing,
        "per_instrument": per_instrument,
    }


# ---------------------------------------------------------------------------
# Plotting helpers
# ---------------------------------------------------------------------------

def plot_r_distribution(outcomes: pd.DataFrame, save_path: Path) -> None:
    """Plot realized-R distribution by exit variant (capped, sampled).

    Parameters
    ----------
    outcomes : pd.DataFrame
        Exit outcomes table; columns "{variant}_R" for each variant.
    save_path : Path
        Output PNG path.
    """
    rng = np.random.default_rng(PLOT_SAMPLE_SEED)
    plot_rows: list[pd.DataFrame] = []
    for variant in EXIT_VARIANTS:
        col = f"{variant}_R"
        if col not in outcomes.columns:
            continue
        sub = outcomes[["Instrument", "Segment", col]].copy()
        sub[col] = sub[col].clip(-PLOT_R_CAP, PLOT_R_CAP)
        sub["ExitVariant"] = variant
        sub.rename(columns={col: "Realized_R"}, inplace=True)
        plot_rows.append(sub)
    if not plot_rows:
        return
    plot_df = pd.concat(plot_rows, ignore_index=True).dropna(subset=["Realized_R"])
    if len(plot_df) > PLOT_MAX_POINTS:
        idx = rng.choice(len(plot_df), PLOT_MAX_POINTS, replace=False)
        plot_df = plot_df.iloc[idx]
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(13, 5))
    sns.boxplot(
        data=plot_df, x="ExitVariant", y="Realized_R", hue="Segment",
        order=EXIT_VARIANTS, showfliers=False, ax=ax,
    )
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_title(f"EXP-025 Realized R Distribution by Exit Variant (capped ±{PLOT_R_CAP}R)")
    ax.set_xlabel("Exit Variant")
    ax.set_ylabel("Realized R")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_expectancy_intervals(summary: pd.DataFrame, save_path: Path) -> None:
    """Plot mean realized R by exit variant for train and test.

    Parameters
    ----------
    summary : pd.DataFrame
        Exit summary from aggregate_exit_summary.
    save_path : Path
        Output PNG path.
    """
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
    for ax, segment in zip(axes, ("Train", "Test")):
        sub = summary[summary["Segment"] == segment]
        sns.barplot(
            data=sub, x="ExitVariant", y="MeanReturn_R", hue="Instrument",
            order=EXIT_VARIANTS, hue_order=INSTRUMENTS, ax=ax,
        )
        ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
        ax.set_title(f"EXP-025 Mean Return R by Exit Variant — {segment}")
        ax.set_xlabel("Exit Variant")
        ax.set_ylabel("Mean Realized R")
        ax.legend(fontsize=7, title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_hit_probability(summary: pd.DataFrame, save_path: Path) -> None:
    """Plot positive-return rate by exit variant and instrument.

    Parameters
    ----------
    summary : pd.DataFrame
        Exit summary from aggregate_exit_summary.
    save_path : Path
        Output PNG path.
    """
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
    for ax, segment in zip(axes, ("Train", "Test")):
        sub = summary[summary["Segment"] == segment]
        sns.barplot(
            data=sub, x="ExitVariant", y="HitRate", hue="Instrument",
            order=EXIT_VARIANTS, hue_order=INSTRUMENTS, ax=ax,
        )
        ax.axhline(0.5, color="red", linewidth=0.8, linestyle="--", label="50%")
        ax.set_title(f"EXP-025 P(Realized R > 0) by Exit Variant — {segment}")
        ax.set_xlabel("Exit Variant")
        ax.set_ylabel("Hit Rate")
        ax.set_ylim(0, 1)
        ax.legend(fontsize=7, title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_hold_time(outcomes: pd.DataFrame, save_path: Path) -> None:
    """Plot hold-time distribution by exit variant (bars until exit).

    Parameters
    ----------
    outcomes : pd.DataFrame
        Exit outcomes table with "{variant}_HoldBars" columns.
    save_path : Path
        Output PNG path.
    """
    rng = np.random.default_rng(PLOT_SAMPLE_SEED)
    hold_rows: list[pd.DataFrame] = []
    for variant in EXIT_VARIANTS:
        col = f"{variant}_HoldBars"
        if col not in outcomes.columns:
            continue
        sub = outcomes[["Instrument", "Segment", col]].copy()
        sub[col] = sub[col].clip(0, OUTCOME_HORIZON_MIN)
        sub["ExitVariant"] = variant
        sub.rename(columns={col: "HoldBars"}, inplace=True)
        hold_rows.append(sub)
    if not hold_rows:
        return
    plot_df = pd.concat(hold_rows, ignore_index=True).dropna(subset=["HoldBars"])
    if len(plot_df) > PLOT_MAX_POINTS:
        idx = rng.choice(len(plot_df), PLOT_MAX_POINTS, replace=False)
        plot_df = plot_df.iloc[idx]
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(13, 5))
    sns.boxplot(
        data=plot_df, x="ExitVariant", y="HoldBars", hue="Segment",
        order=EXIT_VARIANTS, showfliers=False, ax=ax,
    )
    ax.set_title("EXP-025 Hold-Time Distribution by Exit Variant (bars to exit, capped 60)")
    ax.set_xlabel("Exit Variant")
    ax.set_ylabel("Bars to Exit")
    ax.legend(title="", fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_instrument_contribution(summary: pd.DataFrame, save_path: Path) -> None:
    """Plot mean Return_R heatmap by instrument and exit variant (test segment).

    Parameters
    ----------
    summary : pd.DataFrame
        Exit summary from aggregate_exit_summary.
    save_path : Path
        Output PNG path.
    """
    test_summary = summary[summary["Segment"] == "Test"]
    pivot = test_summary.pivot_table(
        index="Instrument", columns="ExitVariant", values="MeanReturn_R", aggfunc="mean"
    )
    pivot = pivot.reindex(index=INSTRUMENTS, columns=EXIT_VARIANTS)
    sns.set_theme(style="white")
    fig, ax = plt.subplots(figsize=(11, 4))
    sns.heatmap(
        pivot, annot=True, fmt=".2f", center=0,
        cmap="RdYlGn", linewidths=0.5, ax=ax,
    )
    ax.set_title("EXP-025 Instrument Contribution: Mean Return_R by Exit Variant (Test)")
    ax.set_xlabel("Exit Variant")
    ax.set_ylabel("Instrument")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def _json_safe(value: Any) -> Any:
    """Recursively convert numpy/pandas types to JSON-safe Python types."""
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
    summary: pd.DataFrame,
    bootstrap: pd.DataFrame,
    verdict: dict[str, Any],
    plots_dir: Path,
    results_dir: Path,
) -> None:
    """Write all EXP-025 result tables, JSON, text summary, and plots.

    Parameters
    ----------
    outcomes : pd.DataFrame
        Full exit outcomes table.
    summary : pd.DataFrame
        Aggregated exit summary.
    bootstrap : pd.DataFrame
        Bootstrap comparison results.
    verdict : dict
        H6 verdict dict.
    plots_dir : Path
        Directory for PNG outputs.
    results_dir : Path
        Directory for CSV/JSON/TXT outputs.
    """
    outcomes.to_csv(results_dir / "exit_outcomes.csv", index=False)
    summary.to_csv(results_dir / "exit_summary.csv", index=False)
    bootstrap.to_csv(results_dir / "bootstrap_comparison.csv", index=False)

    payload: dict[str, Any] = {
        "experiment_id": "EXP-025",
        "title": "Fixed 1 to 2 Risk Reward Justification",
        "predeclared_config": {
            "entry_source": "EXP-024 SecondCandleOpen feasible entries",
            "exit_variants": EXIT_VARIANTS,
            "stop_rule": "EXP-015 original stop (inherited via EXP-021 / EXP-024 chain)",
            "horizon_minutes": OUTCOME_HORIZON_MIN,
            "train_floor": TRAIN_FLOOR,
            "test_floor": TEST_FLOOR,
            "min_eligible_instruments": MIN_ELIGIBLE_INSTRUMENTS,
            "criterion_version": CRITERION_VERSION,
            "bootstrap_reps": BOOTSTRAP_REPS,
            "bootstrap_seed": BOOTSTRAP_SEED,
        },
        "verdict_summary": verdict,
        "exit_summary": summary.to_dict(orient="records"),
    }
    with (results_dir / "results.json").open("w", encoding="utf-8") as fh:
        json.dump(_json_safe(payload), fh, indent=2, default=str, allow_nan=False)

    with (results_dir / "numerical_summary.txt").open("w", encoding="utf-8") as fh:
        fh.write("EXP-025 Fixed 1 to 2 Risk Reward Justification\n")
        fh.write(f"Verdict: {verdict['verdict']}\n")
        fh.write(f"Reason: {verdict['reason']}\n")
        fh.write(f"Instruments floor met: {verdict['instruments_floor_met']}/4\n")
        fh.write(
            f"Instruments fully comparable: {verdict['instruments_fully_comparable']}/4\n"
        )
        fh.write(
            f"Instruments passing (2R superiority evidence): "
            f"{verdict['instruments_passing']}/4\n\n"
        )
        fh.write("Exit summary (Test segment):\n")
        for r in summary[summary["Segment"] == "Test"].itertuples(index=False):
            fh.write(
                f"  {r.Instrument} {r.ExitVariant}: "
                f"N_valid={r.N_valid}, MeanReturn_R={r.MeanReturn_R:.3f}, "
                f"HitRate={r.HitRate:.3f}\n"
            )
        fh.write(
            "\nBootstrap 2R vs alternatives "
            "(Test, superior = CI_Lo > 0; dominated = CI_Hi < 0):\n"
        )
        for r in bootstrap[bootstrap["Segment"] == "Test"].itertuples(index=False):
            dominated = "DOMINATED" if r.TwoR_Dominated else ""
            superior = "SUPERIOR" if r.CI_Lo > 0 else ""
            fh.write(
                f"  {r.Instrument} 2R vs {r.Variant2R_vs}: "
                f"diff={r.MeanDiff_2R_minus_alt:.3f} CI=[{r.CI_Lo:.3f},{r.CI_Hi:.3f}] "
                f"{superior} {dominated}\n"
            )

    plot_r_distribution(outcomes, plots_dir / "01_r_distribution.png")
    plot_expectancy_intervals(summary, plots_dir / "02_expectancy_intervals.png")
    plot_hit_probability(summary, plots_dir / "03_hit_probability.png")
    plot_hold_time(outcomes, plots_dir / "04_hold_time.png")
    plot_instrument_contribution(summary, plots_dir / "05_instrument_contribution.png")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_experiment() -> None:
    """Execute the EXP-025 fixed 1:2 risk/reward justification workflow."""
    plots_dir = EXP_DIR / "plots"
    results_dir = EXP_DIR / "results"
    plots_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Loading EXP-024 SecondCandleOpen entries …")
    entries = load_second_candle_entries()
    LOGGER.info("Loaded %d feasible SecondCandleOpen entries", len(entries))

    for instrument in INSTRUMENTS:
        for segment in ("Train", "Test"):
            n = int(((entries["Instrument"] == instrument) & (entries["Segment"] == segment)).sum())
            floor = TRAIN_FLOOR if segment == "Train" else TEST_FLOOR
            status = "OK" if n >= floor else "BELOW_FLOOR"
            LOGGER.info(
                "%s %s: %d entries (floor=%d) [%s]", instrument, segment, n, floor, status
            )

    LOGGER.info("Loading instrument bars and liquidity levels …")
    bars_by_instrument: dict[str, pd.DataFrame] = {}
    liq_index: dict[tuple[str, Any], dict[str, float | None]] = {}
    for instrument in INSTRUMENTS:
        bars, inst_liq = load_instrument_data(instrument)
        bars_by_instrument[instrument] = bars
        liq_index.update(inst_liq)
        LOGGER.info("%s: %d analysis bars, %d liquidity dates", instrument, len(bars), len(inst_liq))

    LOGGER.info("Simulating exit outcomes …")
    outcomes = build_exit_outcomes(entries, bars_by_instrument, liq_index)
    LOGGER.info("Exit outcomes: %d rows", len(outcomes))

    LOGGER.info("Running analysis …")
    summary = aggregate_exit_summary(outcomes)
    bootstrap = run_bootstrap_comparisons(outcomes)
    verdict = evaluate_h6_verdict(bootstrap, summary)

    LOGGER.info("Writing outputs …")
    write_outputs(outcomes, summary, bootstrap, verdict, plots_dir, results_dir)

    print("EXP-025 complete.")
    print(f"Verdict: {verdict['verdict']}")
    print(f"Reason:  {verdict['reason']}")
    print(f"Plots:   {plots_dir}")
    print(f"Results: {results_dir}")


def main() -> None:
    """Entry point for manual execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_experiment()


if __name__ == "__main__":
    main()
