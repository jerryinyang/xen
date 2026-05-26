"""
Experiment EXP-028: ICT Candidate Robustness and Falsification

Subjects the EXP-027 candidate to predeclared robustness checks:
  1. Segment analysis (by instrument, year, ATR14 volatility tercile, train/test)
  2. Execution delay stress (0, 1, 2 bars from original entry)
  3. Cost scenario stress (EXP-012 ZERO, LIGHT, HEAVY scenarios)

If EXP-027 verdict is INCONCLUSIVE or AGAINST, writes a short
INCONCLUSIVE results.json and exits cleanly.

Robustness verdict (all four required for FOR):
  1. Test segment overall non-negative after LIGHT_COST_PROXY costs
  2. At least 2/3 of segments with >= 30 trades are positive (mean net R > 0)
  3. Edge survives 1-bar delay (mean net Return_R non-negative, test)
  4. Edge survives base cost LIGHT_COST_PROXY (already covered by criterion 1)
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
    load_analysis_timebars,
    train_cutoff_time,
)

LOGGER = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-028"
EXP012_DIR = PYTHON_ROOT / "experiments" / "EXP-012" / "results"
EXP027_DIR = PYTHON_ROOT / "experiments" / "EXP-027" / "results"

BOOTSTRAP_REPS: int = 10_000
BOOTSTRAP_SEED: int = 42
MIN_SEGMENT_TRADES: int = 30
MIN_POSITIVE_SEGMENT_FRACTION: float = 2 / 3
OUTCOME_HORIZON_MIN: int = 60
TARGET_MULTIPLIER: float = 2.0
PRIMARY_COST_SCENARIO: str = "LIGHT_COST_PROXY"


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_exp027_artifacts() -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load the EXP-027 model verdict and, when needed, its trade table.

    Returns
    -------
    tuple[pd.DataFrame, dict]
        (trade_table, model_verdict). The trade table is empty when the EXP-027
        verdict is already ineligible for robustness checks.

    Raises
    ------
    FileNotFoundError
        If the required verdict file is absent, or if the trade table is absent
        for an eligible EXP-027 verdict.
    """
    verdict_path = EXP027_DIR / "model_verdict.json"
    trade_path = EXP027_DIR / "trade_table.csv"
    if not verdict_path.exists():
        raise FileNotFoundError(f"EXP-027 model_verdict.json not found: {verdict_path}")
    with verdict_path.open() as fh:
        verdict = json.load(fh)
    if verdict.get("verdict", "INCONCLUSIVE") in ("INCONCLUSIVE", "AGAINST"):
        return pd.DataFrame(), verdict
    if not trade_path.exists():
        raise FileNotFoundError(f"EXP-027 trade_table.csv not found: {trade_path}")
    trades = pd.read_csv(trade_path)
    trades["NYDate"] = pd.to_datetime(trades["NYDate"])
    if "EntryTime" in trades.columns:
        trades["EntryTime"] = pd.to_datetime(trades["EntryTime"])
    return trades, verdict


def load_cost_scenarios() -> dict[str, dict[str, float]]:
    """Load EXP-012 cost proxy scenarios.

    Returns
    -------
    dict
        Scenario name -> parameter dict.

    Raises
    ------
    FileNotFoundError
        If cost_proxy_scenarios.json is absent.
    """
    path = EXP012_DIR / "cost_proxy_scenarios.json"
    if not path.exists():
        raise FileNotFoundError(f"EXP-012 cost scenarios not found: {path}")
    with path.open() as fh:
        raw = json.load(fh)
    return {item["Scenario"]: item for item in raw}


def load_instrument_bars(instrument: str) -> pd.DataFrame:
    """Load analysis bars for one instrument with ATR14Prior and NYDate.

    Calls add_bar_diagnostics and add_ny_time_features in a single pass.
    Returns pandas DataFrame with columns: CloseTime, OpenTime, Open, High,
    Low, Close, ATR14Prior, NYDate (if available).

    Parameters
    ----------
    instrument : str
        Instrument symbol.

    Returns
    -------
    pd.DataFrame
        Analysis bars, sorted by CloseTime.
    """
    loaded = load_analysis_timebars(DATA_DIR, instrument)
    frame = add_bar_diagnostics(loaded.frame)
    cutoff = train_cutoff_time(frame, loaded.train_rows)
    frame = add_ny_time_features(frame, cutoff)
    bars = frame.sort("CloseTime").to_pandas()
    bars["CloseTime"] = pd.to_datetime(bars["CloseTime"])
    if "OpenTime" in bars.columns:
        bars["OpenTime"] = pd.to_datetime(bars["OpenTime"])
    return bars.reset_index(drop=True)


# ---------------------------------------------------------------------------
# ATR14 tercile computation
# ---------------------------------------------------------------------------

def compute_daily_atr14(bars: pd.DataFrame) -> pd.DataFrame:
    """Compute mean ATR14Prior per NY trading date.

    Parameters
    ----------
    bars : pd.DataFrame
        Analysis bars with ATR14Prior and NYDate columns.

    Returns
    -------
    pd.DataFrame
        Columns: NYDate, ATR14_Daily (mean ATR14Prior per date).
    """
    if "NYDate" not in bars.columns or "ATR14Prior" not in bars.columns:
        return pd.DataFrame(columns=["NYDate", "ATR14_Daily"])
    daily = (
        bars.dropna(subset=["ATR14Prior"])
        .groupby("NYDate")["ATR14Prior"]
        .mean()
        .reset_index()
        .rename(columns={"ATR14Prior": "ATR14_Daily"})
    )
    return daily


def compute_atr14_tercile_boundaries(
    trades: pd.DataFrame,
    daily_atr14: dict[str, pd.DataFrame],
) -> dict[str, tuple[float, float]]:
    """Compute ATR14 tercile boundaries using TRAIN segment trades only.

    Boundaries are calibrated on train trades, then applied to all trades.

    Parameters
    ----------
    trades : pd.DataFrame
        Full trade table (train + test).
    daily_atr14 : dict
        Instrument -> daily ATR14 DataFrame (NYDate, ATR14_Daily).

    Returns
    -------
    dict
        Instrument -> (low_boundary, high_boundary) for tercile labels.
    """
    boundaries: dict[str, tuple[float, float]] = {}
    for instrument in INSTRUMENTS:
        train_trades = trades[
            (trades["Instrument"] == instrument) & (trades["Segment"] == "Train")
        ]
        daily = daily_atr14.get(instrument, pd.DataFrame())
        if daily.empty or train_trades.empty:
            boundaries[instrument] = (np.nan, np.nan)
            continue
        merged = train_trades.merge(
            daily.assign(NYDate=pd.to_datetime(daily["NYDate"])),
            on="NYDate", how="left",
        )
        atr_vals = merged["ATR14_Daily"].dropna().to_numpy()
        if len(atr_vals) < 3:
            boundaries[instrument] = (np.nan, np.nan)
            continue
        lo = float(np.percentile(atr_vals, 100 / 3))
        hi = float(np.percentile(atr_vals, 200 / 3))
        boundaries[instrument] = (lo, hi)
    return boundaries


def label_atr14_tercile(
    trades: pd.DataFrame,
    daily_atr14: dict[str, pd.DataFrame],
    boundaries: dict[str, tuple[float, float]],
) -> pd.DataFrame:
    """Add ATR14Tercile column (Low/Medium/High/Unknown) to trades.

    Parameters
    ----------
    trades : pd.DataFrame
        Full trade table.
    daily_atr14 : dict
        Instrument -> daily ATR14 DataFrame.
    boundaries : dict
        Instrument -> (low_boundary, high_boundary).

    Returns
    -------
    pd.DataFrame
        Trades with ATR14_Daily and ATR14Tercile columns added.
    """
    result = trades.copy()
    daily_frames = []
    for instrument, df in daily_atr14.items():
        if not df.empty:
            tagged = df.copy()
            tagged["Instrument"] = instrument
            tagged["NYDate"] = pd.to_datetime(tagged["NYDate"])
            daily_frames.append(tagged)
    if not daily_frames:
        result["ATR14_Daily"] = np.nan
        result["ATR14Tercile"] = "Unknown"
        return result

    all_daily = pd.concat(daily_frames, ignore_index=True)
    result["NYDate"] = pd.to_datetime(result["NYDate"])
    result = result.merge(all_daily, on=["Instrument", "NYDate"], how="left")

    tercile_labels: list[str] = []
    for _, row in result.iterrows():
        atr = row.get("ATR14_Daily", np.nan)
        instr = row["Instrument"]
        lo, hi = boundaries.get(instr, (np.nan, np.nan))
        if pd.isna(atr) or pd.isna(lo) or pd.isna(hi):
            tercile_labels.append("Unknown")
        elif atr <= lo:
            tercile_labels.append("Low")
        elif atr <= hi:
            tercile_labels.append("Medium")
        else:
            tercile_labels.append("High")
    result["ATR14Tercile"] = tercile_labels
    return result


# ---------------------------------------------------------------------------
# Segment analysis
# ---------------------------------------------------------------------------

def compute_segment_results(
    trades: pd.DataFrame,
    cost_scenario: str,
) -> pd.DataFrame:
    """Compute per-segment mean net Return_R and positive rate.

    Segments: by (SegmentType, Segment, Instrument), (Year), (ATR14Tercile).

    Parameters
    ----------
    trades : pd.DataFrame
        Trade table with cost-adjusted net return, Year, ATR14Tercile columns.
    cost_scenario : str
        Cost scenario column suffix.

    Returns
    -------
    pd.DataFrame
        One row per segment with N, MeanNetReturn_R, PositiveRate, Eligible.
    """
    net_col = f"NetReturn_R_{cost_scenario}"
    if net_col not in trades.columns:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []

    def _agg(group: pd.DataFrame, seg_type: str, seg_label: str, instrument: str, segment: str) -> dict:
        vals = pd.to_numeric(group[net_col], errors="coerce").dropna().to_numpy()
        n = len(vals)
        return {
            "SegmentType": seg_type,
            "SegmentLabel": seg_label,
            "Instrument": instrument,
            "Segment": segment,
            "N": n,
            "MeanNetReturn_R": float(vals.mean()) if n > 0 else np.nan,
            "MedianNetReturn_R": float(np.median(vals)) if n > 0 else np.nan,
            "PositiveRate": float((vals > 0).mean()) if n > 0 else np.nan,
            "Eligible": n >= MIN_SEGMENT_TRADES,
        }

    # By instrument and train/test
    for instrument in INSTRUMENTS:
        for segment in ("Train", "Test"):
            grp = trades[(trades["Instrument"] == instrument) & (trades["Segment"] == segment)]
            rows.append(_agg(grp, "InstrumentSegment", f"{instrument}/{segment}", instrument, segment))

    # By year
    if "Year" in trades.columns:
        for year in sorted(trades["Year"].dropna().unique()):
            year_int = int(year)
            grp_all = trades[trades["Year"] == year]
            rows.append(_agg(grp_all, "Year", str(year_int), "ALL", "ALL"))
            for segment in ("Train", "Test"):
                grp = grp_all[grp_all["Segment"] == segment]
                if len(grp) > 0:
                    rows.append(_agg(grp, "Year_Segment", f"{year_int}/{segment}", "ALL", segment))

    # By ATR14 tercile
    if "ATR14Tercile" in trades.columns:
        for tercile in ("Low", "Medium", "High"):
            grp_all = trades[trades["ATR14Tercile"] == tercile]
            rows.append(_agg(grp_all, "ATR14Tercile", tercile, "ALL", "ALL"))
            for segment in ("Train", "Test"):
                grp = grp_all[grp_all["Segment"] == segment]
                if len(grp) > 0:
                    rows.append(_agg(grp, "ATR14Tercile_Segment", f"{tercile}/{segment}", "ALL", segment))

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Execution delay stress
# ---------------------------------------------------------------------------

def _walk_2r_outcome(
    is_bearish: bool,
    entry: float,
    stop: float,
    risk: float,
    entry_close_ns: int,
    horizon_ns: int,
    close_ns: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
) -> float:
    """Walk forward bars to compute realized 2R outcome for a given entry.

    Parameters
    ----------
    is_bearish : bool
        True for bearish (side=="High") entries.
    entry, stop, risk : float
        Entry price, stop price, risk in price units.
    entry_close_ns : int
        The CloseTime of the entry bar (int64 nanoseconds).
    horizon_ns : int
        Max forward look in nanoseconds (OUTCOME_HORIZON_MIN * 60 * 1e9).
    close_ns, highs, lows, closes : np.ndarray
        Full instrument bar arrays sorted by CloseTime.

    Returns
    -------
    float
        Realized R (2.0, -1.0, or time-exit R). NaN if no bars available.
    """
    if risk <= 0:
        return np.nan
    target = entry - TARGET_MULTIPLIER * risk if is_bearish else entry + TARGET_MULTIPLIER * risk
    start_idx = int(np.searchsorted(close_ns, entry_close_ns, side="right"))
    end_ns = entry_close_ns + horizon_ns
    end_idx = int(np.searchsorted(close_ns, end_ns, side="right"))
    fwd_highs = highs[start_idx:end_idx]
    fwd_lows = lows[start_idx:end_idx]
    fwd_closes = closes[start_idx:end_idx]
    n_bars = len(fwd_highs)
    if n_bars == 0:
        return np.nan

    stop_bar: int | None = None
    target_bar: int | None = None
    for bar_idx in range(n_bars):
        h = float(fwd_highs[bar_idx])
        lo = float(fwd_lows[bar_idx])
        if stop_bar is None:
            if (is_bearish and h >= stop) or (not is_bearish and lo <= stop):
                stop_bar = bar_idx
        if target_bar is None:
            if (is_bearish and lo <= target) or (not is_bearish and h >= target):
                target_bar = bar_idx

    if target_bar is None and stop_bar is None:
        end_close = float(fwd_closes[-1])
        return (entry - end_close) / risk if is_bearish else (end_close - entry) / risk
    if target_bar is not None and stop_bar is not None and target_bar == stop_bar:
        return np.nan  # same-bar ambiguity
    if stop_bar is not None and (target_bar is None or stop_bar < target_bar):
        return -1.0
    return float(TARGET_MULTIPLIER)


def compute_delay_stress(
    trades: pd.DataFrame,
    bars_by_instrument: dict[str, pd.DataFrame],
    cost_scenario: str,
) -> pd.DataFrame:
    """Re-evaluate trades with 0, 1, and 2 bar execution delays.

    For delay d: shift entry to the Open of the bar d steps after the
    bar containing the original EntryTime. Recompute gross and net R.

    Parameters
    ----------
    trades : pd.DataFrame
        EXP-027 trade table with Entry, Stop, Risk1R, Side, EntryTime columns.
    bars_by_instrument : dict
        Instrument -> analysis bars pandas DataFrame.
    cost_scenario : str
        Cost scenario for net return.

    Returns
    -------
    pd.DataFrame
        One row per (Instrument, Segment, delay) with mean gross and net R.
    """
    horizon_ns = int(OUTCOME_HORIZON_MIN * 60 * 1e9)
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        bars = bars_by_instrument[instrument]
        close_ns_arr = bars["CloseTime"].values.astype(np.int64)
        highs = bars["High"].to_numpy(dtype=float)
        lows = bars["Low"].to_numpy(dtype=float)
        closes = bars["Close"].to_numpy(dtype=float)
        open_arr = bars["Open"].to_numpy(dtype=float)
        inst_trades = trades[trades["Instrument"] == instrument].copy()
        if inst_trades.empty:
            continue

        for delay in (0, 1, 2):
            gross_vals_by_seg: dict[str, list[float]] = {"Train": [], "Test": []}
            for _, ev in inst_trades.iterrows():
                entry_time = pd.Timestamp(ev["EntryTime"]) if "EntryTime" in ev and pd.notna(ev.get("EntryTime")) else None
                if entry_time is None:
                    continue
                stop = float(ev["Stop"])
                side = str(ev.get("Side", "Low"))
                is_bearish = side == "High"
                segment = str(ev["Segment"])
                entry_ns = int(entry_time.value)
                # Find bar whose CloseTime > EntryTime (first bar after entry)
                base_bar_idx = int(np.searchsorted(close_ns_arr, entry_ns, side="right"))
                delayed_bar_idx = base_bar_idx + delay
                if delayed_bar_idx >= len(close_ns_arr):
                    continue
                delayed_entry = float(open_arr[delayed_bar_idx])
                delayed_risk = abs(delayed_entry - stop)
                if delayed_risk <= 0:
                    continue
                delayed_close_ns = int(close_ns_arr[delayed_bar_idx])
                gross_r = _walk_2r_outcome(
                    is_bearish, delayed_entry, stop, delayed_risk,
                    delayed_close_ns, horizon_ns,
                    close_ns_arr, highs, lows, closes,
                )
                if np.isfinite(gross_r) and segment in gross_vals_by_seg:
                    gross_vals_by_seg[segment].append(gross_r)

            for segment, gross_list in gross_vals_by_seg.items():
                if not gross_list:
                    continue
                gross_arr = np.array(gross_list)
                rows.append({
                    "Instrument": instrument,
                    "Segment": segment,
                    "Delay": delay,
                    "N": len(gross_arr),
                    "MeanGrossReturn_R": float(gross_arr.mean()),
                    "MedianGrossReturn_R": float(np.median(gross_arr)),
                })

    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ---------------------------------------------------------------------------
# Cost scenario stress
# ---------------------------------------------------------------------------

def compute_cost_stress(
    trades: pd.DataFrame,
    scenarios: dict[str, dict[str, float]],
) -> pd.DataFrame:
    """Apply each cost scenario to gross realized R and report mean net R.

    Parameters
    ----------
    trades : pd.DataFrame
        Trade table with GrossReturn_R, Entry, Risk1R.
    scenarios : dict
        EXP-012 cost scenarios.

    Returns
    -------
    pd.DataFrame
        One row per (Instrument, Segment, Scenario) with mean net Return_R.
    """
    entry_arr = pd.to_numeric(trades.get("Entry", pd.Series(dtype=float)), errors="coerce").to_numpy()
    risk_arr = pd.to_numeric(trades.get("Risk1R", pd.Series(dtype=float)), errors="coerce").to_numpy()
    gross_arr = pd.to_numeric(trades.get("GrossReturn_R", pd.Series(dtype=float)), errors="coerce").to_numpy()
    valid_risk = risk_arr > 0

    rows: list[dict[str, Any]] = []
    for scenario_name, params in scenarios.items():
        total_bps = (
            2 * params["SpreadBpsPerSide"]
            + 2 * params["SlippageBpsPerSide"]
            + params["CommissionBpsRoundTrip"]
        )
        haircut = np.where(valid_risk, total_bps * entry_arr / (10000 * np.where(valid_risk, risk_arr, np.nan)), np.nan)
        net = gross_arr - haircut
        temp = trades.copy()
        temp["_net"] = net
        for instrument in INSTRUMENTS:
            for segment in ("Train", "Test"):
                grp = temp[(temp["Instrument"] == instrument) & (temp["Segment"] == segment)]
                vals = pd.to_numeric(grp["_net"], errors="coerce").dropna().to_numpy()
                rows.append({
                    "Instrument": instrument,
                    "Segment": segment,
                    "Scenario": scenario_name,
                    "N": len(vals),
                    "MeanNetReturn_R": float(vals.mean()) if len(vals) > 0 else np.nan,
                    "MedianNetReturn_R": float(np.median(vals)) if len(vals) > 0 else np.nan,
                })
    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ---------------------------------------------------------------------------
# Robustness verdict
# ---------------------------------------------------------------------------

def evaluate_robustness_verdict(
    segment_results: pd.DataFrame,
    delay_stress: pd.DataFrame,
    cost_stress: pd.DataFrame,
) -> dict[str, Any]:
    """Evaluate four predeclared robustness criteria.

    Parameters
    ----------
    segment_results : pd.DataFrame
        Per-segment results from compute_segment_results.
    delay_stress : pd.DataFrame
        Delay stress from compute_delay_stress.
    cost_stress : pd.DataFrame
        Cost scenario stress from compute_cost_stress.

    Returns
    -------
    dict
        Verdict dict with all criteria and reason string.
    """
    criteria: dict[str, bool] = {}
    reasons: list[str] = []

    # Criterion 1: overall test non-negative after LIGHT_COST_PROXY
    test_overall = segment_results[
        (segment_results["SegmentType"] == "InstrumentSegment")
        & (segment_results["Segment"] == "Test")
    ]
    overall_mean_net = float(
        pd.to_numeric(test_overall["MeanNetReturn_R"], errors="coerce").mean()
    ) if not test_overall.empty else np.nan

    c1 = np.isfinite(overall_mean_net) and overall_mean_net >= 0
    criteria["TestNonNegativeAfterCosts"] = c1
    if not c1:
        reasons.append(f"Mean net Return_R in test = {overall_mean_net:.3f} (negative)")

    # Criterion 2: at least 2/3 of segments with >= 30 trades are positive
    all_instr_year = segment_results[
        segment_results["SegmentType"].isin(["Year_Segment"])
        & (segment_results["Segment"] == "Test")
    ]
    eligible = all_instr_year[all_instr_year["Eligible"]].copy() if not all_instr_year.empty else pd.DataFrame()
    if eligible.empty:
        eligible_fallback = test_overall[test_overall["Eligible"]] if not test_overall.empty else pd.DataFrame()
        eligible = eligible_fallback
    if eligible.empty:
        c2 = False
        reasons.append("No segments with >= 30 trades for criterion 2.")
    else:
        n_eligible = len(eligible)
        n_positive = int((eligible["MeanNetReturn_R"] > 0).sum())
        threshold = n_eligible * MIN_POSITIVE_SEGMENT_FRACTION
        c2 = n_positive >= threshold
        if not c2:
            reasons.append(
                f"Only {n_positive}/{n_eligible} eligible segments positive "
                f"(need >= {threshold:.1f})"
            )
    criteria["TwoThirdsSegmentsPositive"] = c2

    # Criterion 3: edge survives 1-bar delay (test mean net R >= 0)
    if delay_stress.empty:
        c3 = False
        reasons.append("No delay stress data available.")
    else:
        delay1_test = delay_stress[(delay_stress["Delay"] == 1) & (delay_stress["Segment"] == "Test")]
        if delay1_test.empty:
            c3 = False
            reasons.append("No 1-bar delay test data.")
        else:
            mean_gross_d1 = float(
                pd.to_numeric(delay1_test["MeanGrossReturn_R"], errors="coerce").mean()
            )
            # Use gross as proxy (haircut doesn't change with delay)
            c3 = np.isfinite(mean_gross_d1) and mean_gross_d1 >= 0
            if not c3:
                reasons.append(f"1-bar delay mean gross R = {mean_gross_d1:.3f} (negative)")
    criteria["Survives1BarDelay"] = c3

    # Criterion 4: edge survives base cost (LIGHT_COST_PROXY)
    light_test = cost_stress[
        (cost_stress["Scenario"] == PRIMARY_COST_SCENARIO) & (cost_stress["Segment"] == "Test")
    ] if not cost_stress.empty else pd.DataFrame()
    if light_test.empty:
        c4 = False
        reasons.append("No LIGHT_COST_PROXY stress data.")
    else:
        mean_net_light = float(
            pd.to_numeric(light_test["MeanNetReturn_R"], errors="coerce").mean()
        )
        c4 = np.isfinite(mean_net_light) and mean_net_light >= 0
        if not c4:
            reasons.append(f"LIGHT_COST_PROXY mean net R = {mean_net_light:.3f} (negative)")
    criteria["SurvivesBaseCost"] = c4

    all_pass = all(criteria.values())
    verdict = "FOR" if all_pass else "AGAINST"

    return {
        "verdict": verdict,
        "criteria": criteria,
        "reason": "; ".join(reasons) if reasons else "All robustness criteria passed.",
        "overall_test_mean_net_R": overall_mean_net,
    }


# ---------------------------------------------------------------------------
# Plotting helpers
# ---------------------------------------------------------------------------

def plot_segment_heatmap(segment_results: pd.DataFrame, save_path: Path) -> None:
    """Segment expectancy heatmap (Instrument × Year, mean net Return_R).

    Parameters
    ----------
    segment_results : pd.DataFrame
        Segment results from compute_segment_results.
    save_path : Path
        Output PNG path.
    """
    year_rows = segment_results[
        (segment_results["SegmentType"] == "Year_Segment")
        & (segment_results["Segment"] == "Test")
        & (segment_results["Instrument"] == "ALL")
    ].copy()
    # For instrument × year, use InstrumentSegment type per year
    instr_rows = segment_results[
        segment_results["SegmentType"] == "InstrumentSegment"
    ].copy()
    if instr_rows.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No segment data", ha="center", va="center", transform=ax.transAxes)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return

    pivot = instr_rows[instr_rows["Segment"] == "Test"].pivot_table(
        index="Instrument", values="MeanNetReturn_R", aggfunc="mean"
    )
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.heatmap(
        pivot, annot=True, fmt=".3f", center=0, cmap="RdYlGn",
        linewidths=0.4, ax=ax,
    )
    ax.set_title("EXP-028 Segment Expectancy: Instrument × Segment (Mean Net Return_R, Test)")
    ax.set_xlabel("")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_delay_stress(delay_stress: pd.DataFrame, save_path: Path) -> None:
    """Interval plot of mean gross Return_R by delay (0/1/2 bars).

    Parameters
    ----------
    delay_stress : pd.DataFrame
        Delay stress results from compute_delay_stress.
    save_path : Path
        Output PNG path.
    """
    if delay_stress.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No delay stress data", ha="center", va="center", transform=ax.transAxes)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return
    test_df = delay_stress[delay_stress["Segment"] == "Test"]
    agg = test_df.groupby(["Delay", "Instrument"])["MeanGrossReturn_R"].mean().reset_index()
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 5))
    for instrument in INSTRUMENTS:
        sub = agg[agg["Instrument"] == instrument].sort_values("Delay")
        ax.plot(sub["Delay"], sub["MeanGrossReturn_R"], marker="o", label=instrument)
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_xticks([0, 1, 2])
    ax.set_xlabel("Execution Delay (bars)")
    ax.set_ylabel("Mean Gross Return R")
    ax.set_title("EXP-028 Execution Delay Stress (Test Segment)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_cost_stress(cost_stress: pd.DataFrame, save_path: Path) -> None:
    """Bar chart of mean net Return_R by cost scenario (test).

    Parameters
    ----------
    cost_stress : pd.DataFrame
        Cost scenario stress results.
    save_path : Path
        Output PNG path.
    """
    if cost_stress.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No cost stress data", ha="center", va="center", transform=ax.transAxes)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return
    test_df = cost_stress[cost_stress["Segment"] == "Test"]
    agg = test_df.groupby(["Scenario", "Instrument"])["MeanNetReturn_R"].mean().reset_index()
    scenarios_order = ["ZERO_COST_REFERENCE", PRIMARY_COST_SCENARIO, "HEAVY_COST_PROXY"]
    x = np.arange(len(scenarios_order))
    width = 0.18
    fig, ax = plt.subplots(figsize=(11, 5))
    for i, instrument in enumerate(INSTRUMENTS):
        sub = agg[agg["Instrument"] == instrument].set_index("Scenario")
        vals = [
            float(sub.loc[s, "MeanNetReturn_R"]) if s in sub.index else np.nan
            for s in scenarios_order
        ]
        ax.bar(x + i * width, vals, width, label=instrument, alpha=0.8)
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_xticks(x + width * (len(INSTRUMENTS) - 1) / 2)
    ax.set_xticklabels([s.replace("_", "\n") for s in scenarios_order], fontsize=8)
    ax.set_ylabel("Mean Net Return R")
    ax.set_title("EXP-028 Cost Scenario Stress (Test Segment)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_instrument_year_contribution(segment_results: pd.DataFrame, save_path: Path) -> None:
    """Line plot of mean net Return_R by year for each instrument (test).

    Parameters
    ----------
    segment_results : pd.DataFrame
        Segment results.
    save_path : Path
        Output PNG path.
    """
    year_data = segment_results[
        (segment_results["SegmentType"] == "Year_Segment")
        & (segment_results["Segment"] == "Test")
    ].copy()
    if year_data.empty:
        # Fallback: use InstrumentSegment
        year_data = segment_results[
            segment_results["SegmentType"] == "InstrumentSegment"
        ].copy()
    fig, ax = plt.subplots(figsize=(10, 5))
    if not year_data.empty:
        if "SegmentLabel" in year_data.columns:
            ax.plot(year_data["SegmentLabel"], year_data["MeanNetReturn_R"], marker="o")
        else:
            ax.text(0.5, 0.5, "No year data", ha="center", va="center", transform=ax.transAxes)
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_xlabel("Year / Segment")
    ax.set_ylabel("Mean Net Return R")
    ax.set_title("EXP-028 Instrument/Year Contribution (Test)")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_positive_segment_share(segment_results: pd.DataFrame, save_path: Path) -> None:
    """Bar chart: fraction of positive segments by segment type.

    Parameters
    ----------
    segment_results : pd.DataFrame
        Segment results from compute_segment_results.
    save_path : Path
        Output PNG path.
    """
    if segment_results.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No segment data", ha="center", va="center", transform=ax.transAxes)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return

    summary: list[dict[str, Any]] = []
    for seg_type in segment_results["SegmentType"].unique():
        grp = segment_results[
            (segment_results["SegmentType"] == seg_type)
            & (segment_results["Eligible"])
        ]
        if grp.empty:
            continue
        n_pos = int((grp["MeanNetReturn_R"] > 0).sum())
        n_total = len(grp)
        summary.append({
            "SegmentType": seg_type,
            "PositiveFraction": n_pos / n_total if n_total > 0 else 0,
            "N_Eligible": n_total,
        })

    if not summary:
        return
    summary_df = pd.DataFrame(summary)
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = ["green" if f >= MIN_POSITIVE_SEGMENT_FRACTION else "red"
              for f in summary_df["PositiveFraction"]]
    ax.bar(summary_df["SegmentType"], summary_df["PositiveFraction"], color=colors, alpha=0.7)
    ax.axhline(MIN_POSITIVE_SEGMENT_FRACTION, color="black", linewidth=0.8, linestyle="--",
               label=f"Threshold ({MIN_POSITIVE_SEGMENT_FRACTION:.0%})")
    ax.set_ylabel("Fraction of Positive Segments")
    ax.set_ylim(0, 1.1)
    ax.set_title("EXP-028 Positive Segment Share by Segment Type")
    ax.legend(fontsize=8)
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def _json_safe(value: Any) -> Any:
    """Recursively convert numpy/pandas types to JSON-safe Python primitives."""
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


def write_inconclusive_result(reason: str, results_dir: Path) -> None:
    """Write a short INCONCLUSIVE results.json when EXP-027 is not eligible.

    Parameters
    ----------
    reason : str
        Why the experiment is inconclusive.
    results_dir : Path
        Output directory.
    """
    payload = {
        "experiment_id": "EXP-028",
        "verdict": "INCONCLUSIVE",
        "reason": reason,
        "output_contract": "early_inconclusive_no_robustness_outputs",
        "expected_outputs": [
            "results.json",
            "numerical_summary.txt",
        ],
    }
    results_dir.mkdir(parents=True, exist_ok=True)
    with (results_dir / "results.json").open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    with (results_dir / "numerical_summary.txt").open("w", encoding="utf-8") as fh:
        fh.write(f"EXP-028 ICT Candidate Robustness and Falsification\n")
        fh.write(f"Verdict: INCONCLUSIVE\n")
        fh.write(f"Reason: {reason}\n")
        fh.write("Output contract: early_inconclusive_no_robustness_outputs\n")
        fh.write("No segment, delay, cost, robustness-summary, or plot files are expected on this path.\n")


def write_outputs(
    segment_results: pd.DataFrame,
    delay_stress: pd.DataFrame,
    cost_stress: pd.DataFrame,
    robustness_summary: pd.DataFrame,
    robustness_verdict: dict[str, Any],
    plots_dir: Path,
    results_dir: Path,
) -> None:
    """Write all EXP-028 result files and plots.

    Parameters
    ----------
    segment_results : pd.DataFrame
        Per-segment results.
    delay_stress : pd.DataFrame
        Delay stress results.
    cost_stress : pd.DataFrame
        Cost scenario results.
    robustness_summary : pd.DataFrame
        Combined robustness summary.
    robustness_verdict : dict
        Verdict dict.
    plots_dir : Path
        Plot output directory.
    results_dir : Path
        CSV/JSON/TXT output directory.
    """
    segment_results.to_csv(results_dir / "segment_results.csv", index=False)
    if not delay_stress.empty:
        delay_stress.to_csv(results_dir / "delay_stress.csv", index=False)
    if not cost_stress.empty:
        cost_stress.to_csv(results_dir / "cost_stress.csv", index=False)
    if not robustness_summary.empty:
        robustness_summary.to_csv(results_dir / "robustness_summary.csv", index=False)

    with (results_dir / "results.json").open("w", encoding="utf-8") as fh:
        payload = {
            "experiment_id": "EXP-028",
            "title": "ICT Candidate Robustness and Falsification",
            "verdict": robustness_verdict["verdict"],
            "criteria": robustness_verdict["criteria"],
            "reason": robustness_verdict["reason"],
        }
        json.dump(_json_safe(payload), fh, indent=2, default=str, allow_nan=False)

    with (results_dir / "numerical_summary.txt").open("w", encoding="utf-8") as fh:
        fh.write("EXP-028 ICT Candidate Robustness and Falsification\n")
        fh.write(f"Verdict: {robustness_verdict['verdict']}\n")
        fh.write(f"Reason: {robustness_verdict['reason']}\n\n")
        fh.write("Robustness criteria:\n")
        for k, v in robustness_verdict["criteria"].items():
            fh.write(f"  {'PASS' if v else 'FAIL'} {k}\n")
        fh.write("\nSegment results (Test, eligible >= 30 trades):\n")
        elig = segment_results[segment_results["Eligible"] & (segment_results["Segment"].isin(["Test", "ALL"]))]
        for _, r in elig.iterrows():
            fh.write(
                f"  {r['SegmentType']:25s} {r['SegmentLabel']:20s}: "
                f"N={r['N']:4d}, MeanNet={r['MeanNetReturn_R']:.3f}, "
                f"Pos={'Y' if r['MeanNetReturn_R'] > 0 else 'N'}\n"
            )
        if not delay_stress.empty:
            fh.write("\nDelay stress (Test, mean gross R):\n")
            for _, r in delay_stress[delay_stress["Segment"] == "Test"].sort_values(["Delay", "Instrument"]).iterrows():
                fh.write(
                    f"  Delay={r['Delay']} {r['Instrument']:8s}: "
                    f"N={r['N']:4d}, MeanGross={r['MeanGrossReturn_R']:.3f}\n"
                )

    plot_segment_heatmap(segment_results, plots_dir / "01_segment_heatmap.png")
    plot_delay_stress(delay_stress, plots_dir / "02_delay_stress.png")
    plot_cost_stress(cost_stress, plots_dir / "03_cost_stress.png")
    plot_instrument_year_contribution(segment_results, plots_dir / "04_instrument_year_contribution.png")
    plot_positive_segment_share(segment_results, plots_dir / "05_positive_segment_share.png")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_experiment() -> None:
    """Execute the EXP-028 robustness and falsification workflow."""
    plots_dir = EXP_DIR / "plots"
    results_dir = EXP_DIR / "results"

    LOGGER.info("Loading EXP-027 artifacts …")
    trades_raw, model_verdict = load_exp027_artifacts()
    exp027_verdict = model_verdict.get("verdict", "INCONCLUSIVE")

    if exp027_verdict in ("INCONCLUSIVE", "AGAINST"):
        reason = (
            f"EXP-027 candidate is not eligible for robustness checks "
            f"(verdict={exp027_verdict})."
        )
        LOGGER.warning(reason)
        write_inconclusive_result(reason, results_dir)
        print(f"EXP-028 INCONCLUSIVE: {reason}")
        return

    plots_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    LOGGER.info("EXP-027 verdict=%s; proceeding with robustness checks.", exp027_verdict)

    LOGGER.info("Loading cost scenarios …")
    scenarios = load_cost_scenarios()

    LOGGER.info("Loading instrument bars for ATR14 and delay stress …")
    bars_by_instrument: dict[str, pd.DataFrame] = {}
    daily_atr14: dict[str, pd.DataFrame] = {}
    for instrument in INSTRUMENTS:
        bars = load_instrument_bars(instrument)
        bars_by_instrument[instrument] = bars
        daily_atr14[instrument] = compute_daily_atr14(bars)
        LOGGER.info("%s: %d bars, %d ATR14 dates", instrument, len(bars), len(daily_atr14[instrument]))

    LOGGER.info("Adding Year and ATR14 tercile labels …")
    trades = trades_raw.copy()
    trades["Year"] = pd.to_datetime(trades["NYDate"]).dt.year
    boundaries = compute_atr14_tercile_boundaries(trades, daily_atr14)
    trades = label_atr14_tercile(trades, daily_atr14, boundaries)
    LOGGER.info("ATR14 tercile boundaries: %s", {k: [f"{v:.6f}" for v in vs] for k, vs in boundaries.items()})

    LOGGER.info("Applying cost haircuts to trade table …")
    entry_arr = pd.to_numeric(trades.get("Entry", pd.Series(dtype=float)), errors="coerce").to_numpy()
    risk_arr = pd.to_numeric(trades.get("Risk1R", pd.Series(dtype=float)), errors="coerce").to_numpy()
    gross_arr = pd.to_numeric(trades.get("GrossReturn_R", pd.Series(dtype=float)), errors="coerce").to_numpy()
    valid_risk = risk_arr > 0
    for scenario_name, params in scenarios.items():
        total_bps = (
            2 * params["SpreadBpsPerSide"]
            + 2 * params["SlippageBpsPerSide"]
            + params["CommissionBpsRoundTrip"]
        )
        haircut = np.where(valid_risk, total_bps * entry_arr / (10000 * np.where(valid_risk, risk_arr, np.nan)), np.nan)
        trades[f"NetReturn_R_{scenario_name}"] = gross_arr - haircut

    LOGGER.info("Computing segment analysis …")
    segment_results = compute_segment_results(trades, PRIMARY_COST_SCENARIO)

    LOGGER.info("Computing execution delay stress …")
    delay_stress = compute_delay_stress(trades, bars_by_instrument, PRIMARY_COST_SCENARIO)

    LOGGER.info("Computing cost scenario stress …")
    cost_stress = compute_cost_stress(trades, scenarios)

    LOGGER.info("Evaluating robustness verdict …")
    robustness_verdict = evaluate_robustness_verdict(segment_results, delay_stress, cost_stress)

    robustness_summary = pd.concat(
        [df for df in [segment_results, delay_stress, cost_stress] if not df.empty],
        ignore_index=True, sort=False,
    ) if any(not df.empty for df in [segment_results, delay_stress, cost_stress]) else pd.DataFrame()

    LOGGER.info("Writing outputs …")
    write_outputs(segment_results, delay_stress, cost_stress, robustness_summary,
                  robustness_verdict, plots_dir, results_dir)

    print("EXP-028 complete.")
    print(f"Verdict: {robustness_verdict['verdict']}")
    print(f"Reason:  {robustness_verdict['reason']}")
    print(f"Results: {results_dir}")


def main() -> None:
    """Entry point for manual execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_experiment()


if __name__ == "__main__":
    main()
