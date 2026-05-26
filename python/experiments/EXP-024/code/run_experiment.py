"""
Experiment EXP-024: Second Candle Open Execution Timing
Implements the analysis plan from analysis-plan.md.

Predeclared config (locked before results are inspected):
  confirmation_source       : EXP-021 IFVG confirmation events (IFVGClose rows)
  entry_variants            : ConfirmationClose, ImmediateNextOpen,
                              SecondCandleOpen, FirstRetest
  stop_convention           : EXP-015 original Stop (inherited via EXP-021 chain)
  retest_definition         : first bar after confirmation whose High/Low touches
                              the IFVG zone boundary before invalidation
  invalidation_definition   : close on the wrong side of the IFVG zone UpperBound
                              (bullish IFVG) or LowerBound (bearish IFVG)
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
EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-024"
EXP021_RESULTS_DIR = PYTHON_ROOT / "experiments" / "EXP-021" / "results"

CONFIRMATION_SOURCE = "EXP-021"
OUTCOME_HORIZON = 60
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 42
MAX_RETEST_BARS = 120
MIN_TIMING_EVENTS = 50
PLOT_R_CAP = 8.0
PLOT_SAMPLE_SEED = 42
PLOT_MAX_POINTS = 5_000

EXP021_REQUIRED = {
    "Instrument", "NYDate", "Segment", "LevelType", "Side",
    "SweepTime", "EntryProxy", "EntryTime", "Entry", "Stop", "Risk1R", "MinRisk1R",
    "IFVGSide", "IFVGLowerBound", "IFVGUpperBound",
}

ENTRY_LABELS = [
    "ConfirmationClose",
    "ImmediateNextOpen",
    "SecondCandleOpen",
    "FirstRetest",
]


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def _require_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    """Raise if a prerequisite artifact lacks required columns."""
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{label} is missing required columns: {missing}")


def load_ifvg_entries() -> pd.DataFrame:
    """Load EXP-021 IFVGClose entry rows as the confirmation event set."""
    path = EXP021_RESULTS_DIR / "entry_outcomes.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required prerequisite not found: {path}")
    df = pd.read_csv(path)
    missing = sorted(EXP021_REQUIRED.difference(df.columns))
    if missing:
        if "MinRisk1R" in missing:
            raise ValueError(
                "EXP-024 requires a rerun of EXP-021 first: "
                "entry_outcomes.csv is missing MinRisk1R from the inherited-stop feasibility guard."
            )
    _require_columns(df, EXP021_REQUIRED, "EXP-021 entry_outcomes.csv")
    df = df[df["EntryProxy"] == "IFVGClose"].copy()
    df["EntryTime"] = pd.to_datetime(df["EntryTime"])
    df["SweepTime"] = pd.to_datetime(df["SweepTime"])
    if "IFVGCreationTime" in df.columns:
        df["IFVGCreationTime"] = pd.to_datetime(df["IFVGCreationTime"])
    return df.reset_index(drop=True)


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
# Entry timing simulation
# ---------------------------------------------------------------------------

def _is_invalidated(
    bar_close: float,
    ifvg_side: str,
    ifvg_lower: float,
    ifvg_upper: float,
) -> bool:
    """Return True if this bar's close crosses the invalidation boundary.

    Bearish FVG IFVG (IFVGSide="Bearish", Low sweep, bullish setup):
      IFVG fired when close > UpperBound. Price is now above the zone.
      Invalidated when close < LowerBound (price fell back through the zone bottom).
    Bullish FVG IFVG (IFVGSide="Bullish", High sweep, bearish setup):
      IFVG fired when close < LowerBound. Price is now below the zone.
      Invalidated when close > UpperBound (price recovered back above the zone top).
    """
    if ifvg_side == "Bearish":
        return bar_close < ifvg_lower   # bullish setup: invalidated by drop below zone bottom
    # Bullish IFVG, bearish setup
    return bar_close > ifvg_upper       # invalidated by recovery above zone top


def _zone_touch(
    bar_high: float,
    bar_low: float,
    ifvg_side: str,
    ifvg_lower: float,
    ifvg_upper: float,
) -> bool:
    """Return True if this bar's range touches the IFVG zone from the entry side.

    Bearish FVG IFVG (IFVGSide="Bearish", bullish setup): price is above the zone after
    IFVG fires. A retest = bar dips DOWN to the zone top (bar_low <= UpperBound).
    Bullish FVG IFVG (IFVGSide="Bullish", bearish setup): price is below the zone after
    IFVG fires. A retest = bar reaches UP to the zone bottom (bar_high >= LowerBound).
    """
    if ifvg_side == "Bearish":
        return bar_low <= ifvg_upper    # price above zone: bar dips down to zone top
    # Bullish IFVG, bearish setup: price below zone
    return bar_high >= ifvg_lower       # bar reaches up to zone bottom


def simulate_entry_variants(
    conf_event: pd.Series,
    bars: pd.DataFrame,
    close_ns: np.ndarray,
) -> dict[str, Any]:
    """Compute 4 entry variants from one confirmed IFVG event.

    Returns a dict with per-variant timing, entry price, and retest diagnostics.
    """
    conf_ns = int(pd.Timestamp(conf_event["EntryTime"]).value)
    ifvg_side = str(conf_event["IFVGSide"])
    ifvg_lower = float(conf_event["IFVGLowerBound"])
    ifvg_upper = float(conf_event["IFVGUpperBound"])
    stop = float(conf_event["Stop"])

    # Variant 1: ConfirmationClose — already known from EXP-021
    cc_entry = float(conf_event["Entry"])
    cc_time = conf_event["EntryTime"]

    # Indices for the bars after confirmation
    start_idx = int(np.searchsorted(close_ns, conf_ns, side="right"))
    if start_idx >= len(bars):
        return {
            "ConfirmationClose_Entry": cc_entry, "ConfirmationClose_Time": cc_time,
            "ImmediateNextOpen_Entry": np.nan, "ImmediateNextOpen_Time": pd.NaT,
            "SecondCandleOpen_Entry": np.nan, "SecondCandleOpen_Time": pd.NaT,
            "FirstRetest_Entry": np.nan, "FirstRetest_Time": pd.NaT,
            "RetestFound": False, "InvalidatedBefore_Retest": False,
            "MissingForwardBars": True,
        }

    # Variant 2: ImmediateNextOpen (open of the bar AFTER confirmation)
    next_bar = bars.iloc[start_idx]
    imm_entry = float(next_bar["Open"])
    imm_time = next_bar["OpenTime"]

    # Variant 3: SecondCandleOpen (open of the second bar after confirmation)
    sc_entry = np.nan
    sc_time = pd.NaT
    if start_idx + 1 < len(bars):
        second_bar = bars.iloc[start_idx + 1]
        sc_entry = float(second_bar["Open"])
        sc_time = second_bar["OpenTime"]

    # Variant 4: FirstRetest — first bar after confirmation whose range touches the
    # IFVG zone, before invalidation or MAX_RETEST_BARS bars elapsed
    retest_entry = np.nan
    retest_time = pd.NaT
    retest_found = False
    invalidated_before = False
    stop_idx = min(start_idx + MAX_RETEST_BARS, len(bars))

    for i in range(start_idx, stop_idx):
        bar = bars.iloc[i]
        close = float(bar["Close"])
        if _is_invalidated(close, ifvg_side, ifvg_lower, ifvg_upper):
            invalidated_before = True
            break
        if _zone_touch(float(bar["High"]), float(bar["Low"]), ifvg_side, ifvg_lower, ifvg_upper):
            # Retest entry: the limit-fill price is the touched boundary, but the
            # bar's high/low is knowable only at close, so outcomes start after close.
            if ifvg_side == "Bearish":
                retest_entry = ifvg_upper  # bullish setup: price touches zone top from above
            else:
                retest_entry = ifvg_lower  # bearish setup: price touches zone bottom from below
            retest_time = bar["CloseTime"]
            retest_found = True
            break

    return {
        "ConfirmationClose_Entry": cc_entry, "ConfirmationClose_Time": cc_time,
        "ImmediateNextOpen_Entry": imm_entry, "ImmediateNextOpen_Time": imm_time,
        "SecondCandleOpen_Entry": sc_entry, "SecondCandleOpen_Time": sc_time,
        "FirstRetest_Entry": retest_entry, "FirstRetest_Time": retest_time,
        "RetestFound": retest_found, "InvalidatedBefore_Retest": invalidated_before,
        "MissingForwardBars": False,
    }


def build_timing_entries(
    ifvg_events: pd.DataFrame,
    bars_by_instrument: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Build one row per (confirmation_event, entry_variant) with timing info."""
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        bars = bars_by_instrument[instrument]
        close_ns = bars["CloseTime"].values.astype(np.int64)
        inst_events = ifvg_events[ifvg_events["Instrument"] == instrument]
        for _, conf in inst_events.iterrows():
            variants = simulate_entry_variants(conf, bars, close_ns)
            base = {
                "Instrument": instrument,
                "NYDate": conf["NYDate"],
                "Segment": conf["Segment"],
                "LevelType": conf["LevelType"],
                "Side": conf["Side"],
                "SweepTime": conf["SweepTime"],
                "ConfirmationTime": conf["EntryTime"],
                "IFVGSide": conf["IFVGSide"],
                "IFVGLowerBound": conf["IFVGLowerBound"],
                "IFVGUpperBound": conf["IFVGUpperBound"],
                "Stop": conf["Stop"],
                "MinRisk1R": conf["MinRisk1R"],
            }
            label_map = {
                "ConfirmationClose": (
                    variants["ConfirmationClose_Entry"],
                    variants["ConfirmationClose_Time"],
                ),
                "ImmediateNextOpen": (
                    variants["ImmediateNextOpen_Entry"],
                    variants["ImmediateNextOpen_Time"],
                ),
                "SecondCandleOpen": (
                    variants["SecondCandleOpen_Entry"],
                    variants["SecondCandleOpen_Time"],
                ),
                "FirstRetest": (
                    variants["FirstRetest_Entry"],
                    variants["FirstRetest_Time"],
                ),
            }
            for label, (entry, etime) in label_map.items():
                if not np.isfinite(entry) if isinstance(entry, float) else False:
                    continue
                stop = float(conf["Stop"])
                risk = abs(stop - entry)
                min_risk = float(conf["MinRisk1R"])
                risk_feasible = bool(
                    np.isfinite(risk)
                    and np.isfinite(min_risk)
                    and risk >= min_risk > 0.0
                )
                cc_entry = float(variants["ConfirmationClose_Entry"])
                slippage = (
                    (cc_entry - float(entry))
                    if str(conf["Side"]) == "High"
                    else (float(entry) - cc_entry)
                )
                rows.append({
                    **base,
                    "EntryProxy": label,
                    "EntryTime": etime,
                    "Entry": entry,
                    "Risk1R": risk,
                    "RiskFeasible": risk_feasible,
                    "Slippage_R": slippage / risk if risk_feasible and risk > 0 else np.nan,
                    "RetestFound": variants["RetestFound"] if label == "FirstRetest" else None,
                    "InvalidatedBefore": (
                        variants["InvalidatedBefore_Retest"] if label == "FirstRetest" else None
                    ),
                    "MissingForwardBars": (
                        variants["MissingForwardBars"] if label in ("SecondCandleOpen", "FirstRetest")
                        else False
                    ),
                })
    return pd.DataFrame(rows)


def append_outcomes(
    entries: pd.DataFrame,
    bars_by_instrument: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Append 60-minute real-price outcomes to entry rows."""
    rows: list[dict[str, Any]] = []
    for _, row in entries.iterrows():
        bars = bars_by_instrument[str(row["Instrument"])]
        outcome = compute_real_price_outcome(row, bars, horizon_minutes=OUTCOME_HORIZON)
        rows.append({**row.to_dict(), **outcome})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

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
    """Bootstrap differences between each entry variant and ConfirmationClose."""
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    metrics = [
        f"Return_R_{OUTCOME_HORIZON}m",
        f"MAE_R_{OUTCOME_HORIZON}m",
        f"Hit1R_{OUTCOME_HORIZON}m",
        "Slippage_R",
    ]
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        for segment in ("Train", "Test"):
            group = outcomes[
                (outcomes["Instrument"] == instrument)
                & (outcomes["Segment"] == segment)
            ]
            cc_group = group[group["EntryProxy"] == "ConfirmationClose"]
            for proxy in ("ImmediateNextOpen", "SecondCandleOpen", "FirstRetest"):
                proxy_group = group[group["EntryProxy"] == proxy]
                for metric in metrics:
                    proxy_vals = proxy_group[metric].dropna().to_numpy()
                    cc_vals = cc_group[metric].dropna().to_numpy()
                    mean_diff, ci_lo, ci_hi = _bootstrap_diff(
                        proxy_vals, cc_vals, rng, BOOTSTRAP_REPS
                    )
                    rows.append({
                        "Instrument": instrument, "Segment": segment,
                        "EntryProxy": proxy,
                        "Metric": metric,
                        "N_proxy": len(proxy_vals),
                        "N_baseline": len(cc_vals),
                        "MeanDiff": mean_diff,
                        "CI_Lo": ci_lo, "CI_Hi": ci_hi,
                        "CIExcludesZero": bool(
                            np.isfinite(ci_lo) and np.isfinite(ci_hi)
                            and (ci_lo > 0 or ci_hi < 0)
                        ),
                    })
    return pd.DataFrame(rows)


def summarize_entry_outcomes(outcomes: pd.DataFrame) -> pd.DataFrame:
    """Mean Return_R, MAE_R, Hit1R by instrument, segment, entry proxy."""
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
                mae_col = f"MAE_R_{OUTCOME_HORIZON}m"
                hit_col = f"Hit1R_{OUTCOME_HORIZON}m"
                rows.append({
                    "Instrument": instrument, "Segment": segment,
                    "EntryProxy": proxy, "N": n,
                    "FeasibleRiskN": feasible_n,
                    "RiskFilteredN": int(n - feasible_n),
                    "ReturnR_N": int(grp[ret_col].notna().sum()) if n else 0,
                    "MeanReturn_R": float(grp[ret_col].mean()) if n else np.nan,
                    "MeanMAE_R": float(grp[mae_col].mean()) if n else np.nan,
                    "MeanHit1R": float(grp[hit_col].mean()) if n else np.nan,
                    "MeanSlippage_R": float(grp["Slippage_R"].mean()) if n else np.nan,
                })
    return pd.DataFrame(rows)


def summarize_missing_forward_bars(entries: pd.DataFrame) -> pd.DataFrame:
    """Count entries with missing forward bars by proxy, instrument, segment."""
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        for segment in ("Train", "Test"):
            for proxy in ENTRY_LABELS:
                grp = entries[
                    (entries["Instrument"] == instrument)
                    & (entries["Segment"] == segment)
                    & (entries["EntryProxy"] == proxy)
                ]
                n = len(grp)
                n_missing = int(grp["MissingForwardBars"].sum()) if "MissingForwardBars" in grp.columns and n else 0
                rows.append({
                    "Instrument": instrument, "Segment": segment,
                    "EntryProxy": proxy, "N": n, "MissingForwardBars": n_missing,
                })
    return pd.DataFrame(rows)


def evaluate_verdict(
    bootstrap: pd.DataFrame,
    outcome_summary: pd.DataFrame,
) -> dict[str, Any]:
    """Map bootstrap comparisons to a hypothesis verdict.

    Support criterion: SecondCandleOpen has equal or better Return_R than
    ConfirmationClose on at least 3 instruments (CI not negative-excluding-zero)
    without worse MAE or direction-aware slippage. Both Train and Test must have
    >= 50 risk-feasible ConfirmationClose and SecondCandleOpen rows plus finite
    comparisons; missing comparisons are inconclusive, not passing.
    """
    def _summary_row(instrument: str, segment: str, proxy: str) -> pd.Series | None:
        rows = outcome_summary[
            (outcome_summary["Instrument"] == instrument)
            & (outcome_summary["Segment"] == segment)
            & (outcome_summary["EntryProxy"] == proxy)
        ]
        if rows.empty:
            return None
        return rows.iloc[0]

    def _comparison_row(instrument: str, segment: str, metric: str) -> pd.Series | None:
        rows = bootstrap[
            (bootstrap["Instrument"] == instrument)
            & (bootstrap["Segment"] == segment)
            & (bootstrap["EntryProxy"] == "SecondCandleOpen")
            & (bootstrap["Metric"] == metric)
        ]
        if rows.empty:
            return None
        row = rows.iloc[0]
        if not np.isfinite(row["CI_Lo"]) or not np.isfinite(row["CI_Hi"]):
            return None
        return row

    per_instrument: list[dict[str, Any]] = []
    ret_metric = f"Return_R_{OUTCOME_HORIZON}m"
    mae_metric = f"MAE_R_{OUTCOME_HORIZON}m"
    slippage_metric = "Slippage_R"
    for instrument in INSTRUMENTS:
        segment_states: list[dict[str, Any]] = []
        for segment in ("Train", "Test"):
            cc_summary = _summary_row(instrument, segment, "ConfirmationClose")
            sc_summary = _summary_row(instrument, segment, "SecondCandleOpen")
            ret_row = _comparison_row(instrument, segment, ret_metric)
            mae_row = _comparison_row(instrument, segment, mae_metric)
            slip_row = _comparison_row(instrument, segment, slippage_metric)
            has_floor = bool(
                cc_summary is not None
                and sc_summary is not None
                and int(cc_summary["FeasibleRiskN"]) >= MIN_TIMING_EVENTS
                and int(sc_summary["FeasibleRiskN"]) >= MIN_TIMING_EVENTS
            )
            has_finite = has_floor and ret_row is not None and mae_row is not None and slip_row is not None
            ret_not_negative = bool(has_finite and not (ret_row["CI_Hi"] < 0))
            mae_not_worse = bool(has_finite and not (mae_row["CI_Lo"] > 0))
            slippage_not_worse = bool(has_finite and not (slip_row["CI_Lo"] > 0))
            segment_states.append({
                "Segment": segment,
                "HasFeasibleFloor": has_floor,
                "HasFiniteComparison": has_finite,
                "ReturnNotNegative": ret_not_negative,
                "MAENotWorse": mae_not_worse,
                "SlippageNotWorse": slippage_not_worse,
                "Pass": ret_not_negative and mae_not_worse and slippage_not_worse,
            })
        passes = all(state["Pass"] for state in segment_states)
        per_instrument.append({
            "Instrument": instrument,
            "Segments": segment_states,
            "Pass": passes,
        })
    verdict_df = pd.DataFrame(per_instrument)
    passing = int(verdict_df["Pass"].sum())
    if passing >= 3:
        verdict = "FOR"
    elif passing <= 1:
        verdict = "AGAINST"
    else:
        verdict = "INCONCLUSIVE"
    return {
        "verdict": verdict,
        "instruments_passing": passing,
        "per_instrument": per_instrument,
    }


# ---------------------------------------------------------------------------
# Plotting helpers
# ---------------------------------------------------------------------------

def plot_entry_price_displacement(entries: pd.DataFrame, save_path: Path) -> None:
    """Plot direction-aware slippage versus ConfirmationClose by timing rule."""
    plot_df = entries[entries["EntryProxy"] != "ConfirmationClose"].copy()
    if plot_df.empty or "Slippage_R" not in plot_df.columns:
        return
    rng = np.random.default_rng(PLOT_SAMPLE_SEED)
    if len(plot_df) > PLOT_MAX_POINTS:
        idx = rng.choice(len(plot_df), PLOT_MAX_POINTS, replace=False)
        plot_df = plot_df.iloc[idx]

    proxies = ["ImmediateNextOpen", "SecondCandleOpen", "FirstRetest"]
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.boxplot(
        data=plot_df, x="Instrument", y="Slippage_R", hue="EntryProxy",
        order=INSTRUMENTS, hue_order=proxies, showfliers=False, ax=ax,
    )
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_title("EXP-024 Direction-Aware Slippage vs ConfirmationClose")
    ax.set_xlabel("")
    ax.legend(title="", fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_expectancy_intervals(outcome_summary: pd.DataFrame, save_path: Path) -> None:
    """Plot mean Return_R by entry proxy and segment."""
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    for ax, segment in zip(axes, ("Train", "Test")):
        sub = outcome_summary[outcome_summary["Segment"] == segment]
        sns.barplot(
            data=sub, x="Instrument", y="MeanReturn_R", hue="EntryProxy",
            order=INSTRUMENTS, hue_order=ENTRY_LABELS, ax=ax,
        )
        ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
        ax.set_title(f"EXP-024 Mean Return_R by Entry Timing - {segment}")
        ax.set_xlabel("")
        ax.legend(fontsize=7, title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_r_distribution(outcomes: pd.DataFrame, save_path: Path) -> None:
    """Plot Return_R distribution by entry proxy."""
    ret_col = f"Return_R_{OUTCOME_HORIZON}m"
    plot_df = outcomes.copy()
    plot_df[ret_col] = plot_df[ret_col].clip(lower=-PLOT_R_CAP, upper=PLOT_R_CAP)
    rng = np.random.default_rng(PLOT_SAMPLE_SEED)
    if len(plot_df) > PLOT_MAX_POINTS:
        idx = rng.choice(len(plot_df), PLOT_MAX_POINTS, replace=False)
        plot_df = plot_df.iloc[idx]
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(11, 5))
    sns.boxplot(
        data=plot_df, x="Instrument", y=ret_col, hue="EntryProxy",
        order=INSTRUMENTS, hue_order=ENTRY_LABELS, showfliers=False, ax=ax,
    )
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_title(f"EXP-024 Return_R Distribution at {OUTCOME_HORIZON}m")
    ax.set_xlabel("")
    ax.legend(fontsize=7, title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_missing_forward_bars(missing_summary: pd.DataFrame, save_path: Path) -> None:
    """Plot count of events with missing forward bars by proxy."""
    sub = missing_summary[missing_summary["EntryProxy"].isin(["SecondCandleOpen", "FirstRetest"])]
    if sub.empty:
        return
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(
        data=sub, x="Instrument", y="MissingForwardBars", hue="EntryProxy",
        order=INSTRUMENTS, ax=ax,
    )
    ax.set_title("EXP-024 Events with Missing Forward Bars by Timing Rule")
    ax.set_xlabel("")
    ax.legend(title="", fontsize=8)
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
    entries: pd.DataFrame,
    outcome_summary: pd.DataFrame,
    bootstrap: pd.DataFrame,
    missing_summary: pd.DataFrame,
    verdict: dict[str, Any],
    plots_dir: Path,
    results_dir: Path,
) -> None:
    """Write all EXP-024 results, tables, and plots."""
    outcomes.to_csv(results_dir / "entry_timing_outcomes.csv", index=False)
    outcome_summary.to_csv(results_dir / "outcome_summary.csv", index=False)
    bootstrap.to_csv(results_dir / "bootstrap_comparison.csv", index=False)
    missing_summary.to_csv(results_dir / "missing_forward_bars.csv", index=False)

    payload = {
        "experiment_id": "EXP-024",
        "title": "Second Candle Open Execution Timing",
        "predeclared_config": {
            "confirmation_source": CONFIRMATION_SOURCE,
            "entry_variants": ENTRY_LABELS,
            "stop_convention": "EXP-015 original Stop (inherited via EXP-021)",
            "min_risk_rule": "Rows with inherited Risk1R below the confirmation source's MinRisk1R are excluded from R-based and slippage summaries.",
            "outcome_horizon_minutes": OUTCOME_HORIZON,
            "max_retest_bars": MAX_RETEST_BARS,
            "min_timing_events_per_segment": MIN_TIMING_EVENTS,
        },
        "verdict_summary": verdict,
        "outcome_summary": outcome_summary.to_dict(orient="records"),
    }
    with (results_dir / "results.json").open("w", encoding="utf-8") as fh:
        json.dump(_json_safe(payload), fh, indent=2, default=str, allow_nan=False)

    with (results_dir / "numerical_summary.txt").open("w", encoding="utf-8") as fh:
        fh.write("EXP-024 Second Candle Open Execution Timing\n")
        fh.write(f"Verdict: {verdict['verdict']}\n")
        fh.write(f"Instruments passing: {verdict['instruments_passing']}/4\n\n")
        fh.write("Outcome summary:\n")
        for r in outcome_summary.itertuples(index=False):
            fh.write(
                f"  {r.Instrument} {r.Segment} {r.EntryProxy}: "
                f"N={r.N}, Feasible={r.FeasibleRiskN}, RiskFiltered={r.RiskFilteredN}, "
                f"ReturnN={r.ReturnR_N}, ReturnR={r.MeanReturn_R:.3f}, "
                f"MAE_R={r.MeanMAE_R:.3f}, Hit1R={r.MeanHit1R:.3f}, "
                f"Slippage_R={r.MeanSlippage_R:.3f}\n"
            )
        fh.write("\nMissing forward bars:\n")
        for r in missing_summary[missing_summary["MissingForwardBars"] > 0].itertuples(index=False):
            fh.write(
                f"  {r.Instrument} {r.Segment} {r.EntryProxy}: "
                f"{r.MissingForwardBars}/{r.N} missing\n"
            )

    plot_entry_price_displacement(entries, plots_dir / "01_entry_price_displacement.png")
    plot_expectancy_intervals(outcome_summary, plots_dir / "02_expectancy_intervals.png")
    plot_r_distribution(outcomes, plots_dir / "03_r_distribution.png")
    plot_missing_forward_bars(missing_summary, plots_dir / "04_missing_forward_bars.png")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_experiment() -> None:
    """Execute the EXP-024 execution-timing isolation workflow."""
    plots_dir = EXP_DIR / "plots"
    results_dir = EXP_DIR / "results"
    plots_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Loading EXP-021 IFVG confirmation events …")
    ifvg_events = load_ifvg_entries()
    LOGGER.info("Loaded %d IFVG confirmation events", len(ifvg_events))

    LOGGER.info("Loading instrument bars …")
    bars_by_instrument: dict[str, pd.DataFrame] = {}
    for instrument in INSTRUMENTS:
        bars_by_instrument[instrument] = load_instrument_bars(instrument)
        LOGGER.info("%s: %d analysis bars", instrument, len(bars_by_instrument[instrument]))

    LOGGER.info("Simulating entry timing variants …")
    entries = build_timing_entries(ifvg_events, bars_by_instrument)
    LOGGER.info("Entry rows: %d", len(entries))

    LOGGER.info("Computing outcomes …")
    outcomes = append_outcomes(entries, bars_by_instrument)

    LOGGER.info("Running analysis …")
    bootstrap = run_bootstrap_comparisons(outcomes)
    outcome_summary = summarize_entry_outcomes(outcomes)
    missing_summary = summarize_missing_forward_bars(entries)
    verdict = evaluate_verdict(bootstrap, outcome_summary)

    LOGGER.info("Writing outputs …")
    write_outputs(
        outcomes, entries, outcome_summary, bootstrap, missing_summary, verdict,
        plots_dir, results_dir,
    )

    print("EXP-024 complete.")
    print(f"Verdict: {verdict['verdict']} ({verdict['instruments_passing']}/4 instruments)")
    print(f"Plots:   {plots_dir}")
    print(f"Results: {results_dir}")


def main() -> None:
    """Entry point for manual execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_experiment()


if __name__ == "__main__":
    main()
