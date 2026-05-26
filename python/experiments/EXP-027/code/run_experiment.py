"""
Experiment EXP-027: Predeclared Full ICT Model Analysis-Set Test

Applies the frozen model manifest from EXP-026 to analysis-set events,
computes after-cost performance, and evaluates five predeclared survival
criteria. Results feed EXP-028 robustness checks.

Survival criteria (all must pass for verdict FOR):
  1. Positive median expectancy after LIGHT_COST_PROXY on overall test
  2. >= 100 train AND >= 50 test trades overall (across all instruments)
  3. At least 3 instruments contributing (>= 10 test trades each)
  4. No single instrument > 60% of positive net R in test
  5. Train/test direction stable (both positive or both negative mean net R)
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

from ict_timebar import INSTRUMENTS  # noqa: E402

LOGGER = logging.getLogger(__name__)

EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-027"
EXP012_DIR = PYTHON_ROOT / "experiments" / "EXP-012" / "results"
EXP018_DIR = PYTHON_ROOT / "experiments" / "EXP-018" / "results"
EXP024_DIR = PYTHON_ROOT / "experiments" / "EXP-024" / "results"
EXP025_DIR = PYTHON_ROOT / "experiments" / "EXP-025" / "results"
EXP026_DIR = PYTHON_ROOT / "experiments" / "EXP-026" / "results"

BOOTSTRAP_REPS: int = 10_000
BOOTSTRAP_SEED: int = 42
TRAIN_FLOOR: int = 100
TEST_FLOOR: int = 50
MIN_CONTRIBUTING_INSTRUMENTS: int = 3
MIN_INSTRUMENT_TEST_TRADES: int = 10
MAX_INSTRUMENT_SHARE: float = 0.60
PRIMARY_COST_SCENARIO: str = "LIGHT_COST_PROXY"

MANIFEST_REQUIRED_FIELDS: set[str] = {
    "selected_components",
    "exit_variant",
    "stop_rule",
    "cost_scenario",
}
REQUIRED_SELECTION_RULE_VERSION: str = "positive_lower_ci_v2"


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_manifest() -> dict[str, Any]:
    """Load and validate the EXP-026 model manifest.

    Returns
    -------
    dict
        Validated manifest.

    Raises
    ------
    FileNotFoundError
        If model_manifest.json is absent.
    ValueError
        If required manifest fields are missing.
    """
    path = EXP026_DIR / "model_manifest.json"
    if not path.exists():
        raise FileNotFoundError(
            f"EXP-026 model manifest not found: {path}\n"
            "Run EXP-026 first and ensure it writes model_manifest.json."
        )
    with path.open() as fh:
        manifest = json.load(fh)
    missing = MANIFEST_REQUIRED_FIELDS.difference(manifest.keys())
    if missing:
        raise ValueError(f"Manifest is missing required fields: {sorted(missing)}")
    if "candidate_eligible" not in manifest:
        manifest["candidate_eligible"] = False
        manifest["gate_reason"] = "Manifest predates candidate eligibility contract."
    elif manifest.get("selection_rule_version") != REQUIRED_SELECTION_RULE_VERSION:
        manifest["candidate_eligible"] = False
        manifest["gate_reason"] = (
            "Manifest selection rule is missing or stale: "
            f"{manifest.get('selection_rule_version')}"
        )
    LOGGER.info("Manifest loaded: components=%s", manifest["selected_components"])
    return manifest


def load_cost_scenarios() -> dict[str, dict[str, float]]:
    """Load EXP-012 cost proxy scenarios.

    Returns
    -------
    dict
        Scenario name -> {SpreadBpsPerSide, SlippageBpsPerSide, CommissionBpsRoundTrip}.

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


def _bool_mask(df: pd.DataFrame, column: str, default: bool | None, label: str) -> pd.Series:
    """Return a boolean mask for a CSV boolean column."""
    if column not in df.columns:
        if default is None:
            raise ValueError(f"{label} is missing required column: {column}")
        return pd.Series(default, index=df.index, dtype=bool)
    mapped = df[column].map(
        {
            True: True,
            False: False,
            "True": True,
            "False": False,
            "true": True,
            "false": False,
            1: True,
            0: False,
            "1": True,
            "0": False,
        }
    )
    return mapped.where(mapped.notna(), default).astype(bool)


def _risk_feasible_mask(df: pd.DataFrame, label: str) -> pd.Series:
    """Return risk feasibility, accepting legacy RiskFeasible or Risk1R schema."""
    if "RiskFeasible" in df.columns:
        return _bool_mask(df, "RiskFeasible", default=False, label=label)
    if "Risk1R" in df.columns:
        return pd.to_numeric(df["Risk1R"], errors="coerce").gt(0)
    raise ValueError(f"{label} is missing RiskFeasible or Risk1R for feasibility filtering")


def load_events_from_manifest(manifest: dict[str, Any]) -> pd.DataFrame:
    """Load and filter the trade event table matching the manifest's component chain.

    Priority order for event source:
      1. RiskModel_2R in manifest and EXP-025 exit_outcomes.csv exists → use 2R_R col
      2. SecondCandleOpen in manifest → EXP-024 entry_timing_outcomes.csv
      3. Displacement in manifest (fallback) → EXP-018 entry_proxy_events.csv

    The exit_variant from the manifest determines gross return computation.

    Parameters
    ----------
    manifest : dict
        Validated model manifest from EXP-026.

    Returns
    -------
    pd.DataFrame
        Trade table with columns: Instrument, NYDate, Segment, LevelType, Side,
        EntryTime, Entry, Stop, Risk1R, GrossReturn_R.

    Raises
    ------
    FileNotFoundError
        If the required source file is absent.
    """
    components = manifest.get("selected_components", [])
    exit_variant = manifest.get("exit_variant", "2R")

    # Source 1: EXP-025 2R_R (highest fidelity — same-bar ambiguity handled)
    if "RiskModel_2R" in components:
        path = EXP025_DIR / "exit_outcomes.csv"
        if path.exists():
            df = pd.read_csv(path)
            if "2R_R" in df.columns:
                LOGGER.info("Using EXP-025 exit_outcomes.csv (2R_R) as trade source.")
                return _standardize_trade_table(df, gross_col="2R_R")
            LOGGER.warning("EXP-025 exit_outcomes.csv lacks '2R_R'; falling back to EXP-024.")

    # Source 2: EXP-024 SecondCandleOpen entries
    if "SecondCandleOpen" in components:
        path = EXP024_DIR / "entry_timing_outcomes.csv"
        if not path.exists():
            raise FileNotFoundError(f"EXP-024 entry_timing_outcomes.csv not found: {path}")
        df = pd.read_csv(path)
        df = df[
            (df["EntryProxy"] == "SecondCandleOpen")
            & _risk_feasible_mask(df, "EXP-024 entry_timing_outcomes.csv")
            & (~_bool_mask(df, "Ambiguous60", default=True, label="EXP-024 entry_timing_outcomes.csv"))
        ].copy()
        LOGGER.info("Using EXP-024 SecondCandleOpen entries; computing 2R gross return.")
        df["GrossReturn_R"] = _compute_2r_gross_return(df)
        return _standardize_trade_table(df, gross_col="GrossReturn_R")

    # Source 3: EXP-018 Displacement (fallback)
    path = EXP018_DIR / "entry_proxy_events.csv"
    if not path.exists():
        raise FileNotFoundError(f"EXP-018 entry_proxy_events.csv not found: {path}")
    df = pd.read_csv(path)
    df = df[
        (df["EntryProxy"] == "DisplacementClose")
        & _risk_feasible_mask(df, "EXP-018 entry_proxy_events.csv")
        & (~_bool_mask(df, "Ambiguous60", default=True, label="EXP-018 entry_proxy_events.csv"))
    ].copy()
    LOGGER.info("Using EXP-018 DisplacementClose entries; computing 2R gross return.")
    df["GrossReturn_R"] = _compute_2r_gross_return(df)
    return _standardize_trade_table(df, gross_col="GrossReturn_R")


def _compute_2r_gross_return(df: pd.DataFrame) -> pd.Series:
    """Compute gross 2R realized return from Hit2R_60m and MAE_R_60m columns.

    Rules:
      - Hit2R_60m == 1 → +2.0 R
      - Hit2R_60m == 0 and MAE_R_60m >= 1.0 → -1.0 R (stopped out)
      - Otherwise → Return_R_60m (time-stop exit)

    Parameters
    ----------
    df : pd.DataFrame
        Events with Hit2R_60m, MAE_R_60m, Return_R_60m columns.

    Returns
    -------
    pd.Series
        Gross realized R per trade.
    """
    hit2r = pd.to_numeric(df.get("Hit2R_60m", pd.Series(np.nan, index=df.index)), errors="coerce")
    mae = pd.to_numeric(df.get("MAE_R_60m", pd.Series(np.nan, index=df.index)), errors="coerce")
    time_r = pd.to_numeric(df.get("Return_R_60m", pd.Series(np.nan, index=df.index)), errors="coerce")
    result = pd.Series(np.nan, index=df.index)
    result = result.where(hit2r != 1, 2.0)
    stopped = (hit2r == 0) & (mae >= 1.0)
    result = result.where(~stopped, -1.0)
    time_exit = (hit2r == 0) & (mae < 1.0)
    result = result.where(~time_exit, time_r)
    return result


def _standardize_trade_table(df: pd.DataFrame, gross_col: str) -> pd.DataFrame:
    """Extract and rename columns into the standard EXP-027 trade table format.

    Parameters
    ----------
    df : pd.DataFrame
        Source event DataFrame.
    gross_col : str
        Column name for gross realized R.

    Returns
    -------
    pd.DataFrame
        Standardized trade table.
    """
    keep = {
        "Instrument": "Instrument",
        "NYDate": "NYDate",
        "Segment": "Segment",
        "Side": "Side",
        "EntryTime": "EntryTime",
        "Entry": "Entry",
        "Stop": "Stop",
        "Risk1R": "Risk1R",
    }
    optional = ["LevelType", "SweepTime"]
    result: dict[str, Any] = {}
    for src, dst in keep.items():
        if src in df.columns:
            result[dst] = df[src].values
        else:
            result[dst] = np.full(len(df), np.nan)
    for col in optional:
        if col in df.columns:
            result[col] = df[col].values
    result["GrossReturn_R"] = pd.to_numeric(df[gross_col], errors="coerce").values
    out = pd.DataFrame(result).reset_index(drop=True)
    out["NYDate"] = pd.to_datetime(out["NYDate"])
    out["EntryTime"] = pd.to_datetime(out["EntryTime"])
    return out


# ---------------------------------------------------------------------------
# Pure computation
# ---------------------------------------------------------------------------

def apply_cost_haircut(
    trades: pd.DataFrame,
    scenarios: dict[str, dict[str, float]],
) -> pd.DataFrame:
    """Compute cost-haircut R for each cost scenario and add net return columns.

    Cost haircut (in R) = total_bps_roundtrip * Entry / (10000 * Risk1R)
    where total_bps_roundtrip = 2*SpreadBpsPerSide + 2*SlippageBpsPerSide +
                                 CommissionBpsRoundTrip.

    Parameters
    ----------
    trades : pd.DataFrame
        Trade table with GrossReturn_R, Entry, Risk1R columns.
    scenarios : dict
        Cost scenario definitions from EXP-012.

    Returns
    -------
    pd.DataFrame
        Trades with added CostHaircut_R_{scenario} and NetReturn_R_{scenario} columns.
    """
    df = trades.copy()
    entry = pd.to_numeric(df["Entry"], errors="coerce").to_numpy()
    risk = pd.to_numeric(df["Risk1R"], errors="coerce").to_numpy()
    valid_risk = risk > 0
    gross = pd.to_numeric(df["GrossReturn_R"], errors="coerce").to_numpy()
    for scenario_name, params in scenarios.items():
        total_bps = (
            2 * params["SpreadBpsPerSide"]
            + 2 * params["SlippageBpsPerSide"]
            + params["CommissionBpsRoundTrip"]
        )
        haircut = np.where(valid_risk, total_bps * entry / (10000 * np.where(valid_risk, risk, np.nan)), np.nan)
        df[f"CostHaircut_R_{scenario_name}"] = haircut
        df[f"NetReturn_R_{scenario_name}"] = gross - haircut
    return df


def aggregate_performance(
    trades: pd.DataFrame,
    cost_scenario: str,
) -> pd.DataFrame:
    """Aggregate trade-level performance by instrument and segment.

    Parameters
    ----------
    trades : pd.DataFrame
        Trade table with net return columns.
    cost_scenario : str
        Which cost scenario to use for net return (e.g. 'LIGHT_COST_PROXY').

    Returns
    -------
    pd.DataFrame
        Performance summary per instrument/segment.
    """
    net_col = f"NetReturn_R_{cost_scenario}"
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        for segment in ("Train", "Test"):
            grp = trades[(trades["Instrument"] == instrument) & (trades["Segment"] == segment)]
            n = len(grp)
            net_vals = pd.to_numeric(grp.get(net_col, pd.Series(dtype=float)), errors="coerce").dropna()
            gross_vals = pd.to_numeric(grp.get("GrossReturn_R", pd.Series(dtype=float)), errors="coerce").dropna()
            n_valid = len(net_vals)
            rows.append({
                "Instrument": instrument,
                "Segment": segment,
                "N_Trades": n,
                "N_ValidReturn": n_valid,
                "MeanGrossReturn_R": float(gross_vals.mean()) if len(gross_vals) > 0 else np.nan,
                "MeanNetReturn_R": float(net_vals.mean()) if n_valid > 0 else np.nan,
                "MedianNetReturn_R": float(net_vals.median()) if n_valid > 0 else np.nan,
                "SumNetReturn_R": float(net_vals.sum()) if n_valid > 0 else np.nan,
                "MeanCostHaircut_R": float(
                    pd.to_numeric(grp.get(f"CostHaircut_R_{cost_scenario}", pd.Series(dtype=float)), errors="coerce").dropna().mean()
                ) if n > 0 else np.nan,
            })
    return pd.DataFrame(rows)


def _bootstrap_mean(
    vals: np.ndarray,
    rng: np.random.Generator,
    reps: int,
) -> tuple[float, float, float]:
    """Bootstrap mean with 95% CI.

    Parameters
    ----------
    vals : np.ndarray
        Sample values.
    rng : np.random.Generator
        Seeded generator.
    reps : int
        Bootstrap resamples.

    Returns
    -------
    tuple[float, float, float]
        (mean, ci_lo, ci_hi) — all NaN if vals is empty.
    """
    if len(vals) == 0:
        return np.nan, np.nan, np.nan
    n = len(vals)
    boot = np.array([rng.choice(vals, n, replace=True).mean() for _ in range(reps)])
    return float(np.mean(vals)), float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))


def run_bootstrap(
    trades: pd.DataFrame,
    cost_scenario: str,
) -> pd.DataFrame:
    """Bootstrap mean net Return_R for train and test per instrument and overall.

    Parameters
    ----------
    trades : pd.DataFrame
        Trade table with net return columns.
    cost_scenario : str
        Cost scenario to use.

    Returns
    -------
    pd.DataFrame
        Bootstrap results with columns Instrument, Segment, Mean, CI_Lo, CI_Hi.
    """
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    net_col = f"NetReturn_R_{cost_scenario}"
    rows: list[dict[str, Any]] = []
    for instrument in list(INSTRUMENTS) + ["ALL"]:
        for segment in ("Train", "Test"):
            if instrument == "ALL":
                grp = trades[trades["Segment"] == segment]
            else:
                grp = trades[(trades["Instrument"] == instrument) & (trades["Segment"] == segment)]
            vals = pd.to_numeric(grp.get(net_col, pd.Series(dtype=float)), errors="coerce").dropna().to_numpy()
            mean_r, ci_lo, ci_hi = _bootstrap_mean(vals, rng, BOOTSTRAP_REPS)
            rows.append({
                "Instrument": instrument,
                "Segment": segment,
                "N": len(vals),
                "Mean": mean_r,
                "CI_Lo": ci_lo,
                "CI_Hi": ci_hi,
            })
    return pd.DataFrame(rows)


def evaluate_survival_criteria(
    perf: pd.DataFrame,
    bootstrap: pd.DataFrame,
    cost_scenario: str,
) -> dict[str, Any]:
    """Evaluate the five predeclared survival criteria.

    Parameters
    ----------
    perf : pd.DataFrame
        Aggregated performance by instrument/segment.
    bootstrap : pd.DataFrame
        Bootstrap results from run_bootstrap.
    cost_scenario : str
        Cost scenario used (for reporting).

    Returns
    -------
    dict
        {verdict, criteria (dict of name→bool), per_instrument, reason}.
    """
    test_perf = perf[perf["Segment"] == "Test"]
    train_perf = perf[perf["Segment"] == "Train"]
    all_test_bs = bootstrap[(bootstrap["Instrument"] == "ALL") & (bootstrap["Segment"] == "Test")]
    all_train_bs = bootstrap[(bootstrap["Instrument"] == "ALL") & (bootstrap["Segment"] == "Train")]

    overall_test_median = float(
        test_perf["MedianNetReturn_R"].mean()
    ) if not test_perf.empty else np.nan
    overall_test_mean = float(all_test_bs["Mean"].iloc[0]) if not all_test_bs.empty else np.nan
    overall_train_mean = float(all_train_bs["Mean"].iloc[0]) if not all_train_bs.empty else np.nan

    total_train = int(train_perf["N_Trades"].sum())
    total_test = int(test_perf["N_Trades"].sum())

    instruments_contributing = int(
        (test_perf["N_Trades"] >= MIN_INSTRUMENT_TEST_TRADES).sum()
    )

    # Criterion 4: no single instrument > 60% of positive net R
    sum_net_r = float(test_perf["SumNetReturn_R"].sum()) if not test_perf.empty else np.nan
    max_instrument_share = np.nan
    if not test_perf.empty and np.isfinite(sum_net_r) and sum_net_r > 0:
        pos_sums = test_perf["SumNetReturn_R"].clip(lower=0)
        pos_total = float(pos_sums.sum())
        if pos_total > 0:
            max_instrument_share = float(pos_sums.max() / pos_total)

    criteria: dict[str, bool] = {}
    reasons: list[str] = []

    # Criterion 1
    c1 = np.isfinite(overall_test_median) and overall_test_median > 0
    criteria["PositiveMedianExpectancy_Test"] = c1
    if not c1:
        reasons.append(f"Median test net Return_R = {overall_test_median:.3f} (not positive)")

    # Criterion 2
    c2 = (total_train >= TRAIN_FLOOR) and (total_test >= TEST_FLOOR)
    criteria["TradeCounts_Met"] = c2
    if not c2:
        reasons.append(f"Train={total_train} (need {TRAIN_FLOOR}), Test={total_test} (need {TEST_FLOOR})")

    # Criterion 3
    c3 = instruments_contributing >= MIN_CONTRIBUTING_INSTRUMENTS
    criteria["InstrumentsContributing"] = c3
    if not c3:
        reasons.append(f"Only {instruments_contributing} instruments with >= {MIN_INSTRUMENT_TEST_TRADES} test trades")

    # Criterion 4
    c4 = np.isnan(max_instrument_share) or (max_instrument_share <= MAX_INSTRUMENT_SHARE)
    criteria["NoSingleInstrumentDominance"] = c4
    if not c4:
        reasons.append(f"Max instrument share = {max_instrument_share:.1%} (> {MAX_INSTRUMENT_SHARE:.0%})")

    # Criterion 5
    c5 = (
        (np.isfinite(overall_train_mean) and np.isfinite(overall_test_mean))
        and (
            (overall_train_mean > 0 and overall_test_mean > 0)
            or (overall_train_mean < 0 and overall_test_mean < 0)
        )
    )
    criteria["TrainTestDirectionStable"] = c5
    if not c5:
        reasons.append(
            f"Train mean={overall_train_mean:.3f}, Test mean={overall_test_mean:.3f} (direction unstable)"
        )

    all_pass = all(criteria.values())
    if total_test < TEST_FLOOR:
        verdict = "INCONCLUSIVE"
    elif all_pass:
        verdict = "FOR"
    else:
        verdict = "AGAINST"

    per_instrument = []
    for instrument in INSTRUMENTS:
        t_row = test_perf[test_perf["Instrument"] == instrument]
        n_t = int(t_row["N_Trades"].iloc[0]) if not t_row.empty else 0
        net_r = float(t_row["MeanNetReturn_R"].iloc[0]) if not t_row.empty else np.nan
        sum_r = float(t_row["SumNetReturn_R"].iloc[0]) if not t_row.empty else np.nan
        per_instrument.append({
            "Instrument": instrument,
            "N_Test": n_t,
            "MeanNetReturn_R_Test": net_r,
            "SumNetReturn_R_Test": sum_r,
        })

    return {
        "verdict": verdict,
        "criteria": criteria,
        "per_instrument": per_instrument,
        "reason": "; ".join(reasons) if reasons else "All criteria passed.",
        "overall_test_median": overall_test_median,
        "overall_test_mean": overall_test_mean,
        "total_train": total_train,
        "total_test": total_test,
    }


# ---------------------------------------------------------------------------
# Plotting helpers
# ---------------------------------------------------------------------------

def plot_trade_count_waterfall(perf: pd.DataFrame, save_path: Path) -> None:
    """Bar chart of trade counts by instrument and segment.

    Parameters
    ----------
    perf : pd.DataFrame
        Performance summary from aggregate_performance.
    save_path : Path
        Output PNG path.
    """
    fig, ax = plt.subplots(figsize=(11, 5))
    x = np.arange(len(INSTRUMENTS))
    width = 0.35
    train = perf[perf["Segment"] == "Train"].set_index("Instrument")["N_Trades"]
    test = perf[perf["Segment"] == "Test"].set_index("Instrument")["N_Trades"]
    ax.bar(x - width / 2, [train.get(i, 0) for i in INSTRUMENTS], width, label="Train", alpha=0.8)
    ax.bar(x + width / 2, [test.get(i, 0) for i in INSTRUMENTS], width, label="Test", alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(INSTRUMENTS)
    ax.set_ylabel("Trade Count")
    ax.set_title("EXP-027 Full-Model Trade Counts by Instrument")
    ax.legend()
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_cost_r_distribution(trades: pd.DataFrame, cost_scenario: str, save_path: Path) -> None:
    """Box plot of after-cost R distribution by instrument.

    Parameters
    ----------
    trades : pd.DataFrame
        Trade table with net return columns.
    cost_scenario : str
        Cost scenario column suffix.
    save_path : Path
        Output PNG path.
    """
    net_col = f"NetReturn_R_{cost_scenario}"
    if net_col not in trades.columns:
        return
    plot_df = trades[["Instrument", "Segment", net_col]].copy()
    plot_df[net_col] = plot_df[net_col].clip(-6, 6)
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(11, 5))
    sns.boxplot(data=plot_df, x="Instrument", y=net_col, hue="Segment",
                order=INSTRUMENTS, showfliers=False, ax=ax)
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_title(f"EXP-027 Net Return R Distribution ({cost_scenario}, capped ±6R)")
    ax.set_xlabel("Instrument")
    ax.set_ylabel("Net Return R")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_expectancy_intervals(bootstrap: pd.DataFrame, save_path: Path) -> None:
    """Train/test expectancy interval plot (bootstrap 95% CI).

    Parameters
    ----------
    bootstrap : pd.DataFrame
        Bootstrap results from run_bootstrap.
    save_path : Path
        Output PNG path.
    """
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    for ax, segment in zip(axes, ("Train", "Test")):
        sub = bootstrap[(bootstrap["Segment"] == segment) & (bootstrap["Instrument"] != "ALL")]
        y_pos = np.arange(len(sub))
        ax.barh(y_pos, sub["Mean"].values,
                xerr=[sub["Mean"].values - sub["CI_Lo"].values,
                      sub["CI_Hi"].values - sub["Mean"].values],
                align="center", alpha=0.7, capsize=4)
        ax.axvline(0, color="black", linewidth=0.8, linestyle="--")
        ax.set_yticks(y_pos)
        ax.set_yticklabels(sub["Instrument"].tolist(), fontsize=9)
        ax.set_xlabel("Mean Net Return R")
        ax.set_title(f"EXP-027 Expectancy Interval — {segment}")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_instrument_contribution(perf: pd.DataFrame, save_path: Path) -> None:
    """Bar chart of each instrument's % contribution to total positive net R (test).

    Parameters
    ----------
    perf : pd.DataFrame
        Performance summary from aggregate_performance.
    save_path : Path
        Output PNG path.
    """
    test_perf = perf[perf["Segment"] == "Test"].copy()
    pos_sums = test_perf["SumNetReturn_R"].clip(lower=0)
    total = float(pos_sums.sum())
    if total > 0:
        test_perf["ContributionPct"] = 100 * pos_sums / total
    else:
        test_perf["ContributionPct"] = 0
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(test_perf["Instrument"], test_perf["ContributionPct"], alpha=0.8)
    ax.axhline(60, color="red", linestyle="--", linewidth=0.8, label="60% threshold")
    ax.set_ylabel("Contribution % of Positive Net R")
    ax.set_title("EXP-027 Instrument Contribution to Net R (Test)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def load_displacement_baseline() -> dict[str, float]:
    """Load EXP-018 DisplacementClose test mean Return_R_60m per instrument.

    Returns
    -------
    dict
        Instrument -> mean Return_R_60m on test segment (NaN if unavailable).
    """
    base_means: dict[str, float] = {i: np.nan for i in INSTRUMENTS}
    base_path = EXP018_DIR / "entry_proxy_events.csv"
    if not base_path.exists():
        LOGGER.warning("EXP-018 baseline not found: %s", base_path)
        return base_means
    base_df = pd.read_csv(base_path)
    base_df = base_df[
        (base_df["EntryProxy"] == "DisplacementClose")
        & _risk_feasible_mask(base_df, "EXP-018 entry_proxy_events.csv")
        & (~_bool_mask(base_df, "Ambiguous60", default=True, label="EXP-018 entry_proxy_events.csv"))
    ]
    for instrument in INSTRUMENTS:
        grp = base_df[(base_df["Instrument"] == instrument) & (base_df["Segment"] == "Test")]
        vals = pd.to_numeric(grp.get("Return_R_60m", pd.Series(dtype=float)), errors="coerce").dropna()
        base_means[instrument] = float(vals.mean()) if len(vals) > 0 else np.nan
    return base_means


def plot_baseline_comparison(
    full_means: dict[str, float],
    base_means: dict[str, float],
    save_path: Path,
) -> None:
    """Compare full-model vs displacement-only baseline mean net Return_R (test).

    Parameters
    ----------
    full_means : dict
        Instrument -> full-model mean net Return_R on test (pre-computed).
    base_means : dict
        Instrument -> displacement-only mean gross Return_R on test (pre-computed).
    save_path : Path
        Output PNG path.
    """
    x = np.arange(len(INSTRUMENTS))
    width = 0.35
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(x - width / 2, [full_means.get(i, np.nan) for i in INSTRUMENTS], width,
           label="Full Model (net)", alpha=0.8)
    ax.bar(x + width / 2, [base_means.get(i, np.nan) for i in INSTRUMENTS], width,
           label="Displacement Only (gross)", alpha=0.6)
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_xticks(x)
    ax.set_xticklabels(INSTRUMENTS)
    ax.set_ylabel("Mean Return R")
    ax.set_title("EXP-027 Full Model vs Displacement-Only Baseline (Test, Mean Return R)")
    ax.legend(fontsize=8)
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


def write_inconclusive_result(
    manifest: dict[str, Any],
    reason: str,
    results_dir: Path,
    plots_dir: Path,
) -> None:
    """Write an INCONCLUSIVE result when the EXP-026 manifest fails the gate.

    Also removes stale full-run artifacts so the results directory matches the
    early-exit contract.
    """
    stale_result_files = [
        "trade_table.csv",
        "performance_summary.csv",
        "bootstrap_result.csv",
    ]
    results_dir.mkdir(parents=True, exist_ok=True)
    for name in stale_result_files:
        path = results_dir / name
        if path.exists():
            path.unlink()
    if plots_dir.exists():
        for path in plots_dir.glob("*.png"):
            path.unlink()

    payload = {
        "experiment_id": "EXP-027",
        "title": "Predeclared Full ICT Model Analysis-Set Test",
        "manifest": manifest,
        "verdict": "INCONCLUSIVE",
        "criteria": {
            "ManifestEligible": False,
        },
        "reason": reason,
        "per_instrument": [],
    }
    with (results_dir / "results.json").open("w", encoding="utf-8") as fh:
        json.dump(_json_safe(payload), fh, indent=2, default=str, allow_nan=False)

    model_verdict = {
        "verdict": "INCONCLUSIVE",
        "all_criteria": {
            "ManifestEligible": False,
        },
        "reason": reason,
        "manifest_components": manifest.get("selected_components", []),
    }
    with (results_dir / "model_verdict.json").open("w", encoding="utf-8") as fh:
        json.dump(_json_safe(model_verdict), fh, indent=2, default=str, allow_nan=False)

    with (results_dir / "numerical_summary.txt").open("w", encoding="utf-8") as fh:
        fh.write("EXP-027 Predeclared Full ICT Model Analysis-Set Test\n")
        fh.write("Verdict: INCONCLUSIVE\n")
        fh.write(f"Reason: {reason}\n")


def write_outputs(
    trades: pd.DataFrame,
    perf: pd.DataFrame,
    bootstrap: pd.DataFrame,
    verdict_dict: dict[str, Any],
    manifest: dict[str, Any],
    plots_dir: Path,
    results_dir: Path,
    cost_scenario: str,
    baseline_means: dict[str, float] | None = None,
) -> None:
    """Write all EXP-027 result files, model verdict, and plots.

    Parameters
    ----------
    trades : pd.DataFrame
        Full trade table.
    perf : pd.DataFrame
        Performance summary.
    bootstrap : pd.DataFrame
        Bootstrap results.
    verdict_dict : dict
        Survival criteria verdict.
    manifest : dict
        EXP-026 model manifest.
    plots_dir : Path
        Directory for PNG plots.
    results_dir : Path
        Directory for CSV/JSON/TXT outputs.
    cost_scenario : str
        Primary cost scenario used.
    baseline_means : dict or None
        Pre-computed EXP-018 displacement baseline means per instrument.
    """
    trades.to_csv(results_dir / "trade_table.csv", index=False)
    perf.to_csv(results_dir / "performance_summary.csv", index=False)
    bootstrap.to_csv(results_dir / "bootstrap_result.csv", index=False)

    results_payload = {
        "experiment_id": "EXP-027",
        "title": "Predeclared Full ICT Model Analysis-Set Test",
        "manifest": manifest,
        "verdict": verdict_dict["verdict"],
        "criteria": verdict_dict["criteria"],
        "reason": verdict_dict["reason"],
        "per_instrument": verdict_dict["per_instrument"],
    }
    with (results_dir / "results.json").open("w", encoding="utf-8") as fh:
        json.dump(_json_safe(results_payload), fh, indent=2, default=str, allow_nan=False)

    model_verdict = {
        "verdict": verdict_dict["verdict"],
        "all_criteria": verdict_dict["criteria"],
        "per_instrument_summary": verdict_dict["per_instrument"],
        "overall_test_median": verdict_dict["overall_test_median"],
        "overall_test_mean": verdict_dict["overall_test_mean"],
        "total_train": verdict_dict["total_train"],
        "total_test": verdict_dict["total_test"],
        "manifest_components": manifest.get("selected_components", []),
    }
    with (results_dir / "model_verdict.json").open("w", encoding="utf-8") as fh:
        json.dump(_json_safe(model_verdict), fh, indent=2, default=str, allow_nan=False)

    with (results_dir / "numerical_summary.txt").open("w", encoding="utf-8") as fh:
        fh.write("EXP-027 Predeclared Full ICT Model Analysis-Set Test\n")
        fh.write(f"Verdict: {verdict_dict['verdict']}\n")
        fh.write(f"Reason: {verdict_dict['reason']}\n")
        fh.write(f"Components: {manifest.get('selected_components')}\n")
        fh.write(f"Cost scenario: {cost_scenario}\n\n")
        fh.write("Survival criteria:\n")
        for k, v in verdict_dict["criteria"].items():
            fh.write(f"  {'PASS' if v else 'FAIL'} {k}\n")
        fh.write("\nPerformance summary (Test):\n")
        for _, r in perf[perf["Segment"] == "Test"].iterrows():
            fh.write(
                f"  {r['Instrument']:8s}: N={r['N_Trades']:4d}, "
                f"MeanGross={r['MeanGrossReturn_R']:.3f}, "
                f"MeanNet={r['MeanNetReturn_R']:.3f}, "
                f"Median={r['MedianNetReturn_R']:.3f}\n"
            )

    net_col = f"NetReturn_R_{cost_scenario}"
    full_means = {
        i: float(
            pd.to_numeric(
                trades[(trades["Instrument"] == i) & (trades["Segment"] == "Test")].get(
                    net_col, pd.Series(dtype=float)
                ), errors="coerce"
            ).dropna().mean()
        ) if len(trades[(trades["Instrument"] == i) & (trades["Segment"] == "Test")]) > 0 else np.nan
        for i in INSTRUMENTS
    }
    _baseline = baseline_means if baseline_means is not None else {i: np.nan for i in INSTRUMENTS}

    plot_trade_count_waterfall(perf, plots_dir / "01_trade_count_waterfall.png")
    plot_cost_r_distribution(trades, cost_scenario, plots_dir / "02_cost_r_distribution.png")
    plot_expectancy_intervals(bootstrap, plots_dir / "03_expectancy_intervals.png")
    plot_instrument_contribution(perf, plots_dir / "04_instrument_contribution.png")
    plot_baseline_comparison(full_means, _baseline, plots_dir / "05_baseline_comparison.png")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_experiment() -> None:
    """Execute the EXP-027 full ICT model analysis-set test workflow."""
    plots_dir = EXP_DIR / "plots"
    results_dir = EXP_DIR / "results"

    manifest = load_manifest()
    LOGGER.info("Manifest validated. Components: %s", manifest["selected_components"])
    if not bool(manifest.get("candidate_eligible", False)):
        reason = manifest.get(
            "gate_reason",
            "EXP-026 manifest did not identify an eligible full-model candidate.",
        )
        LOGGER.warning(reason)
        write_inconclusive_result(manifest, reason, results_dir, plots_dir)
        print("EXP-027 INCONCLUSIVE.")
        print(f"Reason:  {reason}")
        print(f"Results: {results_dir}")
        return

    plots_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    cost_scenario = manifest.get("cost_scenario", PRIMARY_COST_SCENARIO)
    LOGGER.info("Primary cost scenario: %s", cost_scenario)

    scenarios = load_cost_scenarios()
    LOGGER.info("Loaded %d cost scenarios from EXP-012.", len(scenarios))
    if cost_scenario not in scenarios:
        LOGGER.warning("Manifest cost_scenario '%s' not in EXP-012 scenarios; using %s.",
                       cost_scenario, PRIMARY_COST_SCENARIO)
        cost_scenario = PRIMARY_COST_SCENARIO

    LOGGER.info("Loading events from manifest component chain …")
    trades_raw = load_events_from_manifest(manifest)
    LOGGER.info("Loaded %d trades (train=%d, test=%d).",
                len(trades_raw),
                int((trades_raw["Segment"] == "Train").sum()),
                int((trades_raw["Segment"] == "Test").sum()))

    LOGGER.info("Applying cost haircuts …")
    trades = apply_cost_haircut(trades_raw, scenarios)

    LOGGER.info("Aggregating performance …")
    perf = aggregate_performance(trades, cost_scenario)

    LOGGER.info("Running bootstrap …")
    bootstrap = run_bootstrap(trades, cost_scenario)

    LOGGER.info("Evaluating survival criteria …")
    verdict_dict = evaluate_survival_criteria(perf, bootstrap, cost_scenario)

    LOGGER.info("Loading displacement baseline for plot comparison …")
    baseline_means = load_displacement_baseline()

    LOGGER.info("Writing outputs …")
    write_outputs(trades, perf, bootstrap, verdict_dict, manifest,
                  plots_dir, results_dir, cost_scenario, baseline_means)

    print("EXP-027 complete.")
    print(f"Verdict: {verdict_dict['verdict']}")
    print(f"Reason:  {verdict_dict['reason']}")
    print(f"Results: {results_dir}")


def main() -> None:
    """Entry point for manual execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_experiment()


if __name__ == "__main__":
    main()
