"""
Experiment EXP-030: 15-Minute Sweep Reversal Behavior
Implements the analysis plan from analysis-plan.md.

Detects PDH/PDL/ONH/ONL first-touch failed-breakout (Sweep) and breach events
on synthetic 15-minute bars resampled from holdout-excluded 1-minute base bars,
then evaluates outcomes on real 1-minute prices strictly after the confirming
15-minute candle close. The 1R-before-stop probability difference between
sweep and breach events is the primary comparison; the EXP-015 1-minute
point estimates are reported alongside for resolution-stability assessment.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl
import seaborn as sns

PYTHON_ROOT = Path(__file__).resolve().parents[3]
PROJECT_ROOT = PYTHON_ROOT.parent
SRC_DIR = PYTHON_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from bar_aggregator import aggregate_ohlc, coverage_summary  # noqa: E402
from ict_timebar import (  # noqa: E402
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
EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-030"
EXP015_RESULTS_DIR = PYTHON_ROOT / "experiments" / "EXP-015" / "results"

PERIOD_MINUTES = 15
ATR_PERIOD = 14
BUFFER_ATR_COEFF = 0.05
HORIZONS_MINUTES = [30, 60, 120]
PRIMARY_HORIZON = 60
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 42
MIN_SWEEP_EVENTS = 100
ON_LEVEL_MIN_MINUTE = OVERNIGHT_END_MINUTE
LEVEL_TYPES_HIGH = ["PDH", "ONH"]
LEVEL_TYPES_LOW = ["PDL", "ONL"]
PLOT_R_CAP = 8.0

EVENT_COLS = [
    "Instrument",
    "NYDate",
    "Segment",
    "CloseTime",
    "Open",
    "High",
    "Low",
    "Close",
    "LevelType",
    "Side",
    "EventType",
    "Level",
    "Buffer",
    "Stop",
    "Entry",
    "Risk1R",
]


# ── Data loading ─────────────────────────────────────────────────────────────


def _add_atr_15m(frame_15m: pl.DataFrame) -> pl.DataFrame:
    """Add TrueRange and ATR14Prior to the 15-minute frame.

    ATR is computed on completed 15-minute bars and shifted by 1 so the value
    is knowable strictly before the current bar close. The same convention
    matches the EXP-015 1-minute pipeline.
    """
    prev_close = pl.col("Close").shift(1)
    true_range = pl.max_horizontal(
        pl.col("High") - pl.col("Low"),
        (pl.col("High") - prev_close).abs(),
        (pl.col("Low") - prev_close).abs(),
    ).fill_null(pl.col("High") - pl.col("Low"))
    return frame_15m.with_columns(true_range.alias("TrueRange")).with_columns(
        pl.col("TrueRange")
        .rolling_mean(window_size=ATR_PERIOD, min_samples=ATR_PERIOD)
        .shift(1)
        .alias("ATR14Prior")
    )


def load_instrument_data(
    instrument: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, float, dict[str, int]]:
    """Load 1m analysis bars, 15m frame with NY/level joins, and precision step.

    Returns
    -------
    bars_1m : pd.DataFrame
        Holdout-excluded 1-minute bars for outcome evaluation.
    weekday_15m : pd.DataFrame
        Holdout-excluded 15-minute weekday bars with NY features, ATR, levels.
    levels : pd.DataFrame
        EXP-014-style PDH/PDL/ONH/ONL by NYDate (computed on the 1-minute frame
        since daily levels are resolution-independent).
    precision_step : float
        Smallest positive close-to-close 15-minute price increment.
    coverage : dict
        Source-to-aggregated bar diagnostics.
    """
    loaded = load_analysis_timebars(DATA_DIR, instrument)
    frame_1m = loaded.frame

    # NY features and levels on the 1m series (levels are by NYDate).
    train_end_1m = train_cutoff_time(frame_1m, loaded.train_rows)
    frame_1m_ny = add_ny_time_features(frame_1m, train_end_1m)
    levels = compute_liquidity_levels(frame_1m_ny)

    # 1-minute outcome frame.
    bars_1m = (
        frame_1m.sort("CloseTime")
        .select(["Symbol", "OpenTime", "CloseTime", "Open", "High", "Low", "Close"])
        .to_pandas()
    )
    bars_1m["CloseTime"] = pd.to_datetime(bars_1m["CloseTime"])
    bars_1m["OpenTime"] = pd.to_datetime(bars_1m["OpenTime"])

    # 15-minute aggregated frame + NY features + recomputed ATR.
    aggregated = aggregate_ohlc(frame_1m, period_minutes=PERIOD_MINUTES)
    coverage = coverage_summary(frame_1m, aggregated, period_minutes=PERIOD_MINUTES)
    if aggregated.is_empty():
        return (
            bars_1m,
            pd.DataFrame(columns=["CloseTime", "High", "Low", "Close"]),
            levels,
            1e-5,
            coverage,
        )
    train_rows_15m = int(aggregated.height * 0.70)
    train_end_15m = train_cutoff_time(aggregated, train_rows_15m)
    frame_15m = add_ny_time_features(aggregated, train_end_15m)
    frame_15m = _add_atr_15m(frame_15m)
    precision_step = compute_price_precision_step(frame_15m)
    weekday_15m = weekday_filter(frame_15m).to_pandas()
    weekday_15m["CloseTime"] = pd.to_datetime(weekday_15m["CloseTime"])
    return bars_1m, weekday_15m, levels, precision_step, coverage


# ── Sweep / breach detection on 15-minute bars ───────────────────────────────


def _build_level_events(
    merged: pd.DataFrame,
    level_type: str,
) -> pd.DataFrame:
    """Build the first-touch event per NYDate for one level type on 15m bars."""
    side = "High" if level_type in ("PDH", "ONH") else "Low"
    level_col = merged[level_type]
    valid = level_col.notna()
    if level_type in ("ONH", "ONL"):
        valid = valid & (merged["NYMinuteOfDay"] >= ON_LEVEL_MIN_MINUTE)

    if side == "High":
        sweep_mask = valid & (merged["High"] > level_col + merged["Buffer"]) & (
            merged["Close"] < level_col
        )
        breach_mask = valid & (merged["Close"] > level_col + merged["Buffer"])
    else:
        sweep_mask = valid & (merged["Low"] < level_col - merged["Buffer"]) & (
            merged["Close"] > level_col
        )
        breach_mask = valid & (merged["Close"] < level_col - merged["Buffer"])

    candidates = merged[sweep_mask | breach_mask].copy()
    if candidates.empty:
        return pd.DataFrame()

    candidates["EventType"] = np.where(
        sweep_mask.loc[candidates.index], "Sweep", "Breach"
    )

    first_touch = (
        candidates.sort_values("CloseTime")
        .groupby("NYDate", sort=False)
        .head(1)
        .copy()
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
    weekday_15m: pd.DataFrame,
    levels: pd.DataFrame,
    instrument: str,
    precision_step: float,
) -> pd.DataFrame:
    """Detect first-occurrence sweep and breach events per NYDate per level."""
    inst_lvl = (
        levels[levels["Instrument"] == instrument][
            ["NYDate", "PDH", "PDL", "ONH", "ONL"]
        ].copy()
    )
    merged = weekday_15m.merge(inst_lvl, on="NYDate", how="left")
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
    present = [c for c in EVENT_COLS if c in result.columns]
    return result[present].reset_index(drop=True)


# ── Outcomes on real 1-minute prices ─────────────────────────────────────────


def _walk_target_stop(
    highs: np.ndarray,
    lows: np.ndarray,
    target: float,
    stop: float,
    is_bearish: bool,
) -> tuple[bool, bool, bool, int, int]:
    """Return first target/stop hit state for ordered forward 1m bars."""
    for idx in range(highs.size):
        h = float(highs[idx])
        l = float(lows[idx])
        target_hit = (l <= target) if is_bearish else (h >= target)
        stop_hit = (h >= stop) if is_bearish else (l <= stop)
        if target_hit and stop_hit:
            return False, False, True, idx, idx
        if target_hit:
            return True, False, False, idx, -1
        if stop_hit:
            return False, True, False, -1, idx
    return False, False, False, -1, -1


def _empty_horizon(h: int) -> dict[str, Any]:
    """NaN outcome dict for one horizon."""
    suffix = f"_{h}m"
    out: dict[str, Any] = {
        f"MFE_R{suffix}": np.nan,
        f"MAE_R{suffix}": np.nan,
        f"Return_R{suffix}": np.nan,
        f"Hit1R{suffix}": np.nan,
        f"Hit2R{suffix}": np.nan,
    }
    if h == PRIMARY_HORIZON:
        out["Ambiguous60"] = False
    return out


def _outcomes_for_event(
    event: pd.Series,
    close_ns: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
) -> dict[str, Any]:
    """Compute multi-horizon outcomes for one 15-minute event on 1m bars.

    The outcome clock starts at the close of the confirming 15-minute candle.
    `searchsorted(..., side="right")` skips any 1-minute bar whose CloseTime
    equals the 15-minute CloseTime (the last 1-minute bar inside the
    confirming 15-minute candle), enforcing the no-intrabar-leakage rule.
    """
    entry = float(event["Entry"])
    risk = float(event["Risk1R"])
    stop = float(event["Stop"])
    is_bearish = event["Side"] == "High"
    nan_out: dict[str, Any] = {}
    for h in HORIZONS_MINUTES:
        nan_out.update(_empty_horizon(h))

    if not np.isfinite(risk) or risk <= 0.0:
        return nan_out

    event_ns = int(pd.Timestamp(event["CloseTime"]).value)
    start_idx = int(np.searchsorted(close_ns, event_ns, side="right"))

    out: dict[str, Any] = {}
    for h in HORIZONS_MINUTES:
        suffix = f"_{h}m"
        end_ns = event_ns + h * 60 * 10**9
        end_idx = int(np.searchsorted(close_ns, end_ns, side="right"))
        h_highs = highs[start_idx:end_idx]
        h_lows = lows[start_idx:end_idx]
        h_closes = closes[start_idx:end_idx]
        if h_highs.size == 0:
            out.update(_empty_horizon(h))
            continue

        mfe = (
            entry - float(np.min(h_lows))
            if is_bearish
            else float(np.max(h_highs)) - entry
        )
        mae = (
            float(np.max(h_highs)) - entry
            if is_bearish
            else entry - float(np.min(h_lows))
        )
        end_close = float(h_closes[-1])
        realized = entry - end_close if is_bearish else end_close - entry
        target_1r = entry - risk if is_bearish else entry + risk
        target_2r = entry - 2 * risk if is_bearish else entry + 2 * risk
        hit_1r, _, amb_1r, _, _ = _walk_target_stop(
            h_highs, h_lows, target_1r, stop, is_bearish
        )
        hit_2r, _, amb_2r, _, _ = _walk_target_stop(
            h_highs, h_lows, target_2r, stop, is_bearish
        )

        out[f"MFE_R{suffix}"] = max(0.0, mfe) / risk
        out[f"MAE_R{suffix}"] = max(0.0, mae) / risk
        out[f"Return_R{suffix}"] = realized / risk
        out[f"Hit1R{suffix}"] = np.nan if amb_1r else float(hit_1r)
        out[f"Hit2R{suffix}"] = np.nan if amb_2r else float(hit_2r)
        if h == PRIMARY_HORIZON:
            out["Ambiguous60"] = bool(amb_1r)
    return out


def append_outcomes(
    events: pd.DataFrame,
    bars_1m_by_instrument: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Append outcome columns to all 15m sweep/breach events using 1m bars."""
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        inst_events = events[events["Instrument"] == instrument]
        if inst_events.empty:
            continue
        bars = bars_1m_by_instrument[instrument]
        close_ns = bars["CloseTime"].values.astype(np.int64)
        highs = bars["High"].to_numpy(dtype=float)
        lows = bars["Low"].to_numpy(dtype=float)
        closes = bars["Close"].to_numpy(dtype=float)
        for _, event in inst_events.iterrows():
            outcome = _outcomes_for_event(event, close_ns, highs, lows, closes)
            rows.append({**event.to_dict(), **outcome})
    return pd.DataFrame(rows)


# ── Counts, bootstrap, and verdict ───────────────────────────────────────────


def summarize_counts(events: pd.DataFrame) -> pd.DataFrame:
    """Report per-instrument and per-segment failed-sweep and breach counts."""
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        for segment in ("Train", "Test"):
            group = events[
                (events["Instrument"] == instrument)
                & (events["Segment"] == segment)
            ]
            sweeps = int((group["EventType"] == "Sweep").sum())
            breaches = int((group["EventType"] == "Breach").sum())
            risk_feasible_sweeps = int(
                (
                    (group["EventType"] == "Sweep")
                    & (group["Risk1R"] > 0)
                    & np.isfinite(group["Risk1R"])
                ).sum()
            )
            rows.append(
                {
                    "Instrument": instrument,
                    "Segment": segment,
                    "SweepCount": sweeps,
                    "BreachCount": breaches,
                    "RiskFeasibleSweepCount": risk_feasible_sweeps,
                    "FloorMet": risk_feasible_sweeps >= MIN_SWEEP_EVENTS,
                }
            )
    return pd.DataFrame(rows)


def _stratified_bootstrap_diff(
    sweep_values: np.ndarray,
    breach_values: np.ndarray,
    sweep_strata: np.ndarray,
    breach_strata: np.ndarray,
    n_reps: int,
    seed: int,
) -> tuple[float, float, float]:
    """Stratified bootstrap of mean(sweep) - mean(breach); return point and 95% CI.

    Stratification preserves the side/level-type composition of each group so
    the difference is not dominated by an instrument's level mix. NaN values
    in either group are dropped within stratum.
    """
    if sweep_values.size == 0 or breach_values.size == 0:
        return float("nan"), float("nan"), float("nan")
    sweep_mask = np.isfinite(sweep_values)
    breach_mask = np.isfinite(breach_values)
    sweep_values = sweep_values[sweep_mask]
    sweep_strata = sweep_strata[sweep_mask]
    breach_values = breach_values[breach_mask]
    breach_strata = breach_strata[breach_mask]
    if sweep_values.size == 0 or breach_values.size == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    point = float(sweep_values.mean()) - float(breach_values.mean())
    diffs = np.empty(n_reps, dtype=float)
    sweep_idx_by_stratum = {
        s: np.flatnonzero(sweep_strata == s) for s in np.unique(sweep_strata)
    }
    breach_idx_by_stratum = {
        s: np.flatnonzero(breach_strata == s) for s in np.unique(breach_strata)
    }
    for rep in range(n_reps):
        sweep_pick = np.concatenate(
            [rng.choice(idx, size=idx.size, replace=True) for idx in sweep_idx_by_stratum.values()]
        )
        breach_pick = np.concatenate(
            [rng.choice(idx, size=idx.size, replace=True) for idx in breach_idx_by_stratum.values()]
        )
        diffs[rep] = sweep_values[sweep_pick].mean() - breach_values[breach_pick].mean()
    ci_low = float(np.quantile(diffs, 0.025))
    ci_high = float(np.quantile(diffs, 0.975))
    return point, ci_low, ci_high


def bootstrap_primary_difference(events: pd.DataFrame) -> pd.DataFrame:
    """Bootstrap the sweep-minus-breach 60m Hit1R difference per instrument/segment."""
    rows: list[dict[str, Any]] = []
    metric = f"Hit1R_{PRIMARY_HORIZON}m"
    for instrument in INSTRUMENTS:
        for segment in ("Train", "Test"):
            group = events[
                (events["Instrument"] == instrument)
                & (events["Segment"] == segment)
            ]
            sweeps = group[group["EventType"] == "Sweep"]
            breaches = group[group["EventType"] == "Breach"]
            point, ci_low, ci_high = _stratified_bootstrap_diff(
                sweeps[metric].to_numpy(dtype=float),
                breaches[metric].to_numpy(dtype=float),
                (sweeps["LevelType"] + "/" + sweeps["Side"]).to_numpy(),
                (breaches["LevelType"] + "/" + breaches["Side"]).to_numpy(),
                BOOTSTRAP_REPS,
                BOOTSTRAP_SEED,
            )
            rows.append(
                {
                    "Instrument": instrument,
                    "Segment": segment,
                    "PointDiff": point,
                    "CILow": ci_low,
                    "CIHigh": ci_high,
                    "SweepN": int(len(sweeps)),
                    "BreachN": int(len(breaches)),
                }
            )
    return pd.DataFrame(rows)


def bootstrap_secondary(events: pd.DataFrame) -> pd.DataFrame:
    """Bootstrap MAE_R_60m, MFE_R_60m, Return_R_60m differences per instrument."""
    rows: list[dict[str, Any]] = []
    for metric in ("MAE_R_60m", "MFE_R_60m", "Return_R_60m"):
        for instrument in INSTRUMENTS:
            group = events[(events["Instrument"] == instrument)]
            sweeps = group[group["EventType"] == "Sweep"]
            breaches = group[group["EventType"] == "Breach"]
            point, ci_low, ci_high = _stratified_bootstrap_diff(
                sweeps[metric].to_numpy(dtype=float),
                breaches[metric].to_numpy(dtype=float),
                (sweeps["LevelType"] + "/" + sweeps["Side"]).to_numpy(),
                (breaches["LevelType"] + "/" + breaches["Side"]).to_numpy(),
                BOOTSTRAP_REPS,
                BOOTSTRAP_SEED,
            )
            rows.append(
                {
                    "Metric": metric,
                    "Instrument": instrument,
                    "PointDiff": point,
                    "CILow": ci_low,
                    "CIHigh": ci_high,
                }
            )
    return pd.DataFrame(rows)


def bootstrap_horizon_sweep(events: pd.DataFrame) -> pd.DataFrame:
    """Bootstrap sweep-minus-breach Hit1R at each horizon per instrument."""
    rows: list[dict[str, Any]] = []
    for h in HORIZONS_MINUTES:
        metric = f"Hit1R_{h}m"
        for instrument in INSTRUMENTS:
            group = events[events["Instrument"] == instrument]
            sweeps = group[group["EventType"] == "Sweep"]
            breaches = group[group["EventType"] == "Breach"]
            point, ci_low, ci_high = _stratified_bootstrap_diff(
                sweeps[metric].to_numpy(dtype=float),
                breaches[metric].to_numpy(dtype=float),
                (sweeps["LevelType"] + "/" + sweeps["Side"]).to_numpy(),
                (breaches["LevelType"] + "/" + breaches["Side"]).to_numpy(),
                BOOTSTRAP_REPS,
                BOOTSTRAP_SEED,
            )
            rows.append(
                {
                    "HorizonMin": h,
                    "Instrument": instrument,
                    "PointDiff": point,
                    "CILow": ci_low,
                    "CIHigh": ci_high,
                }
            )
    return pd.DataFrame(rows)


def load_exp015_reference() -> pd.DataFrame:
    """Load EXP-015 primary sweep-vs-breach effects for timeframe comparison."""
    path = EXP015_RESULTS_DIR / "primary_effects.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required EXP-015 reference is missing: {path}")
    reference = pd.read_csv(path)
    required = {
        "Instrument",
        "Segment",
        "Diff",
        "CI95Low",
        "CI95High",
        "CIExcludesZero",
        "SupportsPrimary",
    }
    missing = required - set(reference.columns)
    if missing:
        raise ValueError(f"EXP-015 reference missing columns: {sorted(missing)}")
    return reference


def build_exp015_comparison(
    primary: pd.DataFrame,
    exp015_reference: pd.DataFrame,
) -> pd.DataFrame:
    """Join 15m primary effects to EXP-015 1m reference effects."""
    ref_cols = [
        "Instrument",
        "Segment",
        "Diff",
        "CI95Low",
        "CI95High",
        "CIExcludesZero",
        "SupportsPrimary",
    ]
    ref = exp015_reference[ref_cols].rename(
        columns={
            "Diff": "EXP015PointDiff",
            "CI95Low": "EXP015CILow",
            "CI95High": "EXP015CIHigh",
            "CIExcludesZero": "EXP015CIExcludesZero",
            "SupportsPrimary": "EXP015SupportsPrimary",
        }
    )
    comparison = primary.merge(ref, on=["Instrument", "Segment"], how="left")
    missing = comparison[
        comparison[["EXP015PointDiff", "EXP015CILow", "EXP015CIHigh"]]
        .isna()
        .any(axis=1)
    ]
    if not missing.empty:
        keys = missing[["Instrument", "Segment"]].to_dict(orient="records")
        raise ValueError(f"Missing EXP-015 comparison rows for {keys}")
    comparison["EXP030CIExcludesZero"] = (
        (comparison["CILow"] > 0.0) | (comparison["CIHigh"] < 0.0)
    )
    comparison["EXP030Positive"] = (
        comparison["EXP030CIExcludesZero"] & (comparison["PointDiff"] > 0.0)
    )
    comparison["EXP015Positive"] = (
        comparison["EXP015CIExcludesZero"].astype(bool)
        & (comparison["EXP015PointDiff"] > 0.0)
    )
    comparison["EXP030CIWidth"] = comparison["CIHigh"] - comparison["CILow"]
    comparison["EXP015CIWidth"] = comparison["EXP015CIHigh"] - comparison["EXP015CILow"]
    comparison["NewPositiveVsEXP015"] = (
        comparison["EXP030Positive"] & ~comparison["EXP015Positive"]
    )
    comparison["EURUSDReplicatesTighterOrStronger"] = (
        (comparison["Instrument"] == "EURUSD")
        & comparison["EXP030Positive"]
        & comparison["EXP015Positive"]
        & (
            (comparison["PointDiff"] >= comparison["EXP015PointDiff"])
            | (comparison["EXP030CIWidth"] < comparison["EXP015CIWidth"])
        )
    )
    return comparison


def evaluate_verdict(
    counts: pd.DataFrame,
    primary: pd.DataFrame,
    exp015_comparison: pd.DataFrame,
) -> dict[str, Any]:
    """Map counts and primary CIs to a verdict per the scope criteria."""
    per_instrument: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        inst_counts = counts[counts["Instrument"] == instrument]
        inst_primary = primary[primary["Instrument"] == instrument]
        inst_comparison = exp015_comparison[
            (exp015_comparison["Instrument"] == instrument)
            & (exp015_comparison["Segment"] == "Test")
        ]
        floor_met = bool(inst_counts["FloorMet"].all())
        train_row = inst_primary[inst_primary["Segment"] == "Train"]
        test_row = inst_primary[inst_primary["Segment"] == "Test"]

        test_ci_low = (
            float(test_row["CILow"].iloc[0])
            if not test_row.empty and np.isfinite(test_row["CILow"].iloc[0])
            else np.nan
        )
        test_ci_high = (
            float(test_row["CIHigh"].iloc[0])
            if not test_row.empty and np.isfinite(test_row["CIHigh"].iloc[0])
            else np.nan
        )
        test_point = (
            float(test_row["PointDiff"].iloc[0])
            if not test_row.empty and np.isfinite(test_row["PointDiff"].iloc[0])
            else np.nan
        )

        sweep_excludes_zero = (
            np.isfinite(test_ci_low)
            and np.isfinite(test_ci_high)
            and (test_ci_low > 0 or test_ci_high < 0)
        )
        exp015_positive = (
            bool(inst_comparison["EXP015Positive"].iloc[0])
            if not inst_comparison.empty
            else False
        )
        new_positive = (
            bool(inst_comparison["NewPositiveVsEXP015"].iloc[0])
            if not inst_comparison.empty
            else False
        )
        eurusd_replicates = (
            bool(inst_comparison["EURUSDReplicatesTighterOrStronger"].iloc[0])
            if not inst_comparison.empty
            else False
        )
        per_instrument.append(
            {
                "Instrument": instrument,
                "FloorMet": floor_met,
                "TestPointDiff": test_point,
                "TestCILow": test_ci_low,
                "TestCIHigh": test_ci_high,
                "TestExcludesZero": bool(sweep_excludes_zero),
                "EXP015Positive": exp015_positive,
                "NewPositiveVsEXP015": new_positive,
                "EURUSDReplicatesTighterOrStronger": eurusd_replicates,
            }
        )

    verdict_df = pd.DataFrame(per_instrument)
    floors_failing = int((~verdict_df["FloorMet"]).sum())
    positive_new_instruments = verdict_df[
        verdict_df["FloorMet"] & verdict_df["NewPositiveVsEXP015"]
    ]["Instrument"].tolist()
    eurusd_replicates = bool(
        (
            verdict_df["FloorMet"]
            & verdict_df["EURUSDReplicatesTighterOrStronger"]
        ).any()
    )
    all_ci_includes_zero = bool((~verdict_df["TestExcludesZero"]).all())
    all_floor_met = floors_failing == 0

    if floors_failing >= 3:
        verdict = "INCONCLUSIVE"
    elif positive_new_instruments or eurusd_replicates:
        verdict = "FOR"
    elif all_floor_met and all_ci_includes_zero:
        verdict = "AGAINST"
    else:
        verdict = "INCONCLUSIVE"
    return {
        "verdict": verdict,
        "floors_failing": floors_failing,
        "new_positive_instruments": positive_new_instruments,
        "eurusd_replicates_tighter_or_stronger": eurusd_replicates,
        "all_ci_includes_zero": all_ci_includes_zero,
        "per_instrument": per_instrument,
    }


# ── JSON sanitization ────────────────────────────────────────────────────────


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


# ── Plotting ─────────────────────────────────────────────────────────────────


def plot_event_counts(counts: pd.DataFrame, save_path: Path) -> None:
    """Plot sweep vs breach event counts per instrument and segment."""
    plot_df = counts.melt(
        id_vars=["Instrument", "Segment"],
        value_vars=["SweepCount", "BreachCount"],
        var_name="EventType",
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
            hue="EventType",
            order=INSTRUMENTS,
            ax=ax,
        )
        ax.axhline(MIN_SWEEP_EVENTS, color="darkred", linestyle="--", linewidth=1)
        ax.set_title(f"EXP-030 15m Sweep/Breach Counts - {segment}")
        ax.set_xlabel("")
        ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_primary_difference(
    primary: pd.DataFrame,
    exp015_comparison: pd.DataFrame,
    save_path: Path,
) -> None:
    """Plot 15m effects with EXP-015 1m reference effects overlaid."""
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for ax, segment in zip(axes, ("Train", "Test")):
        sub = primary[primary["Segment"] == segment].set_index("Instrument").reindex(INSTRUMENTS)
        ref = (
            exp015_comparison[exp015_comparison["Segment"] == segment]
            .set_index("Instrument")
            .reindex(INSTRUMENTS)
        )
        if sub.empty:
            continue
        x = np.arange(len(sub))
        ax.errorbar(
            x,
            sub["PointDiff"],
            yerr=[
                (sub["PointDiff"] - sub["CILow"]).clip(lower=0).fillna(0),
                (sub["CIHigh"] - sub["PointDiff"]).clip(lower=0).fillna(0),
            ],
            fmt="o",
            color="darkblue",
            ecolor="steelblue",
            capsize=4,
            label="EXP-030 15m",
        )
        ax.errorbar(
            x + 0.18,
            ref["EXP015PointDiff"],
            yerr=[
                (ref["EXP015PointDiff"] - ref["EXP015CILow"]).clip(lower=0).fillna(0),
                (ref["EXP015CIHigh"] - ref["EXP015PointDiff"]).clip(lower=0).fillna(0),
            ],
            fmt="s",
            color="darkorange",
            ecolor="orange",
            capsize=4,
            label="EXP-015 1m",
        )
        ax.axhline(0.0, color="black", linewidth=1)
        ax.set_xticks(x)
        ax.set_xticklabels(sub.index, rotation=0)
        ax.set_title(f"EXP-030 Sweep-minus-Breach Hit1R_60m - {segment}")
        ax.set_ylabel("Hit1R difference")
        ax.set_xlabel("")
        ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_mae_mfe(events: pd.DataFrame, save_path: Path) -> None:
    """Plot MAE_R_60m and MFE_R_60m distributions by instrument and event type."""
    if events.empty:
        return
    plot_df = events.copy()
    for col in ("MAE_R_60m", "MFE_R_60m"):
        plot_df[col] = plot_df[col].clip(upper=PLOT_R_CAP)
    melt = plot_df.melt(
        id_vars=["Instrument", "EventType"],
        value_vars=["MAE_R_60m", "MFE_R_60m"],
        var_name="Metric",
        value_name="R",
    ).dropna()
    sns.set_theme(style="whitegrid")
    g = sns.catplot(
        data=melt,
        x="Instrument",
        y="R",
        hue="EventType",
        col="Metric",
        kind="box",
        order=INSTRUMENTS,
        showfliers=False,
        height=4.5,
        aspect=1.1,
    )
    g.fig.suptitle("EXP-030 MAE/MFE distributions at 60m (R-multiples, capped at 8R)", y=1.02)
    g.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(g.fig)


def plot_horizon_sweep(horizon: pd.DataFrame, save_path: Path) -> None:
    """Plot sweep-minus-breach Hit1R difference across horizons by instrument."""
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5))
    for instrument in INSTRUMENTS:
        sub = horizon[horizon["Instrument"] == instrument].sort_values("HorizonMin")
        ax.errorbar(
            sub["HorizonMin"],
            sub["PointDiff"],
            yerr=[
                (sub["PointDiff"] - sub["CILow"]).clip(lower=0).fillna(0),
                (sub["CIHigh"] - sub["PointDiff"]).clip(lower=0).fillna(0),
            ],
            fmt="o-",
            capsize=3,
            label=instrument,
        )
    ax.axhline(0.0, color="black", linewidth=1)
    ax.set_xlabel("Horizon (minutes)")
    ax.set_ylabel("Sweep minus Breach Hit1R")
    ax.set_title("EXP-030 Sweep-minus-Breach Hit1R Across Horizons")
    ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ── Output orchestration ─────────────────────────────────────────────────────


def write_outputs(
    events: pd.DataFrame,
    counts: pd.DataFrame,
    primary: pd.DataFrame,
    secondary: pd.DataFrame,
    horizon: pd.DataFrame,
    exp015_comparison: pd.DataFrame,
    coverage: dict[str, dict[str, int]],
    precision_steps: dict[str, float],
    verdict: dict[str, Any],
    plots_dir: Path,
    results_dir: Path,
) -> None:
    """Write EXP-030 result tables, JSON, text summary, and plots."""
    events.to_csv(results_dir / "sweep_events_15m.csv", index=False)
    counts.to_csv(results_dir / "event_counts.csv", index=False)
    primary.to_csv(results_dir / "bootstrap_primary.csv", index=False)
    secondary.to_csv(results_dir / "bootstrap_secondary.csv", index=False)
    horizon.to_csv(results_dir / "bootstrap_horizon_sweep.csv", index=False)
    exp015_comparison.to_csv(results_dir / "exp015_reference_comparison.csv", index=False)

    payload = {
        "experiment_id": "EXP-030",
        "title": "15-Minute Sweep Reversal Behavior",
        "period_minutes": PERIOD_MINUTES,
        "buffer_atr_coefficient": BUFFER_ATR_COEFF,
        "horizons_minutes": HORIZONS_MINUTES,
        "primary_horizon": PRIMARY_HORIZON,
        "bootstrap_reps": BOOTSTRAP_REPS,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "min_sweep_events": MIN_SWEEP_EVENTS,
        "price_precision_steps": precision_steps,
        "coverage_diagnostics": coverage,
        "verdict_summary": verdict,
        "counts": counts.to_dict(orient="records"),
        "primary_bootstrap": primary.to_dict(orient="records"),
        "secondary_bootstrap": secondary.to_dict(orient="records"),
        "horizon_bootstrap": horizon.to_dict(orient="records"),
        "exp015_reference_comparison": exp015_comparison.to_dict(orient="records"),
    }
    with (results_dir / "results.json").open("w", encoding="utf-8") as handle:
        json.dump(_json_safe(payload), handle, indent=2, default=str, allow_nan=False)

    with (results_dir / "numerical_summary.txt").open("w", encoding="utf-8") as handle:
        handle.write("EXP-030 15-Minute Sweep Reversal Behavior\n")
        handle.write(f"Verdict: {verdict['verdict']}\n")
        handle.write(
            f"New positive instruments vs EXP-015: "
            f"{', '.join(verdict['new_positive_instruments']) or 'none'}; "
            f"EURUSD replicated tighter/stronger: "
            f"{verdict['eurusd_replicates_tighter_or_stronger']}; "
            f"floors failing: {verdict['floors_failing']}/4\n\n"
        )
        for row in counts.itertuples(index=False):
            handle.write(
                f"- {row.Instrument} {row.Segment}: sweeps={row.SweepCount}, "
                f"breaches={row.BreachCount}, "
                f"risk-feasible-sweeps={row.RiskFeasibleSweepCount}, "
                f"floor={row.FloorMet}\n"
            )
        handle.write("\nPrimary Hit1R_60m sweep-minus-breach point and CI:\n")
        for row in primary.itertuples(index=False):
            handle.write(
                f"- {row.Instrument} {row.Segment}: point={row.PointDiff:.4f}, "
                f"CI=[{row.CILow:.4f}, {row.CIHigh:.4f}], "
                f"sweepN={row.SweepN}, breachN={row.BreachN}\n"
            )
        handle.write("\nEXP-015 reference comparison (Test segment):\n")
        test_comparison = exp015_comparison[exp015_comparison["Segment"] == "Test"]
        for row in test_comparison.itertuples(index=False):
            handle.write(
                f"- {row.Instrument}: exp030={row.PointDiff:.4f} "
                f"[{row.CILow:.4f}, {row.CIHigh:.4f}], "
                f"exp015={row.EXP015PointDiff:.4f} "
                f"[{row.EXP015CILow:.4f}, {row.EXP015CIHigh:.4f}], "
                f"new_positive={row.NewPositiveVsEXP015}, "
                f"eurusd_replicates={row.EURUSDReplicatesTighterOrStronger}\n"
            )

    plot_event_counts(counts, plots_dir / "01_event_counts.png")
    plot_primary_difference(
        primary,
        exp015_comparison,
        plots_dir / "02_primary_difference.png",
    )
    plot_mae_mfe(events, plots_dir / "03_mae_mfe_distributions.png")
    plot_horizon_sweep(horizon, plots_dir / "04_horizon_sweep.png")


def run_experiment() -> None:
    """Execute the EXP-030 15m sweep reversal workflow."""
    plots_dir = EXP_DIR / "plots"
    results_dir = EXP_DIR / "results"
    plots_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    bars_1m_by_instrument: dict[str, pd.DataFrame] = {}
    coverage_by_instrument: dict[str, dict[str, int]] = {}
    precision_steps: dict[str, float] = {}
    event_parts: list[pd.DataFrame] = []

    for instrument in INSTRUMENTS:
        bars_1m, weekday_15m, levels, precision_step, coverage = load_instrument_data(
            instrument
        )
        bars_1m_by_instrument[instrument] = bars_1m
        coverage_by_instrument[instrument] = coverage
        precision_steps[instrument] = precision_step
        if weekday_15m.empty:
            LOGGER.info("%s: empty 15m frame, skipping", instrument)
            continue
        detected = detect_sweep_events(weekday_15m, levels, instrument, precision_step)
        event_parts.append(detected)
        LOGGER.info(
            "%s: 1m=%d, 15m=%d, events=%d",
            instrument,
            coverage["source_bars_in"],
            coverage["aggregated_bars_out"],
            len(detected),
        )

    if not event_parts:
        raise ValueError("No 15-minute events detected for any instrument.")

    events = pd.concat(event_parts, ignore_index=True)
    events = append_outcomes(events, bars_1m_by_instrument)

    counts = summarize_counts(events)
    primary = bootstrap_primary_difference(events)
    secondary = bootstrap_secondary(events)
    horizon = bootstrap_horizon_sweep(events)
    exp015_comparison = build_exp015_comparison(primary, load_exp015_reference())
    verdict = evaluate_verdict(counts, primary, exp015_comparison)

    write_outputs(
        events,
        counts,
        primary,
        secondary,
        horizon,
        exp015_comparison,
        coverage_by_instrument,
        precision_steps,
        verdict,
        plots_dir,
        results_dir,
    )

    print("EXP-030 complete.")
    print(f"Verdict: {verdict['verdict']}")
    print(f"Plots:   {plots_dir}")
    print(f"Results: {results_dir}")


def main() -> None:
    """Entry point for manual execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_experiment()


if __name__ == "__main__":
    main()
