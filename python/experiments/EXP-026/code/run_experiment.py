"""
Experiment EXP-026: Incremental ICT Component Ablation

Builds an incremental chain from prior experiment result files to identify
which ICT components contribute net value, then freezes a model manifest
for EXP-027 only when the ablation gate produces positive evidence.

Sub-chain A (enrichment filters, proxy expectancy only):
  Step 1  Sweep             — EXP-015 sweep events (EventType==Sweep)
  Step 2  Sweep+Macro       — apply InMacro==True from EXP-016
  Step 3  Sweep+Macro+PD    — apply PassMidpointFilter==True from EXP-017

Sub-chain B (execution chain, Return_R_60m available):
  Step 4  Displacement      — EXP-018 DisplacementClose (independent of A)
  Step 5  +IFVG             — EXP-021 IFVGClose
  Step 6  +Breaker          — EXP-023 BreakerClose
  Step 7  +SecondCandleOpen — EXP-024 SecondCandleOpen, RiskFeasible
  Step 8  +RiskModel_2R     — EXP-025 exit_outcomes.csv 2R_R (if available)

Bootstrap marginal contribution: step_n mean – step_{n-1} mean for adjacent
nested pairs in sub-chain B where Return_R_60m is available (steps 4→5,
5→6, 6→7, 7→8). Candidate selection requires a positive point estimate and
positive lower confidence bound on at least three instruments.
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

EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-026"
EXP015_DIR = PYTHON_ROOT / "experiments" / "EXP-015" / "results"
EXP016_DIR = PYTHON_ROOT / "experiments" / "EXP-016" / "results"
EXP017_DIR = PYTHON_ROOT / "experiments" / "EXP-017" / "results"
EXP018_DIR = PYTHON_ROOT / "experiments" / "EXP-018" / "results"
EXP021_DIR = PYTHON_ROOT / "experiments" / "EXP-021" / "results"
EXP023_DIR = PYTHON_ROOT / "experiments" / "EXP-023" / "results"
EXP024_DIR = PYTHON_ROOT / "experiments" / "EXP-024" / "results"
EXP025_DIR = PYTHON_ROOT / "experiments" / "EXP-025" / "results"

BOOTSTRAP_REPS: int = 10_000
BOOTSTRAP_SEED: int = 42
MINIMUM_VIABLE_CHAIN: list[str] = ["Sweep", "Displacement", "SecondCandleOpen"]
MIN_COMPONENT_PASS_INSTRUMENTS: int = 3
SELECTION_RULE_VERSION: str = "positive_lower_ci_v2"
REQUIRED_EXP025_CRITERION_VERSION: str = "superiority_v2"
EVENT_ID_COLUMNS: list[str] = ["Instrument", "NYDate", "Segment", "LevelType", "Side", "SweepTime"]
ENTRY_ID_COLUMNS: list[str] = ["Instrument", "NYDate", "Segment", "LevelType", "Side", "EntryTime"]

# Eligibility table (verdicts from prior experiments; EXP-025 resolved at runtime)
_BASE_ELIGIBILITY: list[dict[str, Any]] = [
    {
        "ComponentLabel": "Sweep",
        "SourceEXP": "EXP-015",
        "Verdict": "REFUTED",
        "EligibleForChain": True,
        "EligibleForCandidate": True,
        "Step": 1,
        "Notes": "Baseline; mandatory",
    },
    {
        "ComponentLabel": "Macro",
        "SourceEXP": "EXP-016",
        "Verdict": "INCONCLUSIVE",
        "EligibleForChain": False,
        "EligibleForCandidate": False,
        "Step": 2,
        "Notes": "Negative control; not eligible for selection",
    },
    {
        "ComponentLabel": "PremiumDiscount",
        "SourceEXP": "EXP-017",
        "Verdict": "INCONCLUSIVE",
        "EligibleForChain": False,
        "EligibleForCandidate": False,
        "Step": 3,
        "Notes": "Negative control; not eligible for selection",
    },
    {
        "ComponentLabel": "Displacement",
        "SourceEXP": "EXP-018",
        "Verdict": "INCONCLUSIVE",
        "EligibleForChain": True,
        "EligibleForCandidate": True,
        "Step": 4,
        "Notes": "Chain anchor; always in minimum viable chain",
    },
    {
        "ComponentLabel": "SwingBreak",
        "SourceEXP": "EXP-019",
        "Verdict": "INCONCLUSIVE",
        "EligibleForChain": False,
        "EligibleForCandidate": False,
        "Step": None,
        "Notes": "Excluded; did not beat displacement in EXP-019",
    },
    {
        "ComponentLabel": "IFVG",
        "SourceEXP": "EXP-021",
        "Verdict": "REFUTED",
        "EligibleForChain": True,
        "EligibleForCandidate": False,
        "Step": 5,
        "Notes": "Negative control; not eligible for candidate selection",
    },
    {
        "ComponentLabel": "Breaker",
        "SourceEXP": "EXP-023",
        "Verdict": "REFUTED",
        "EligibleForChain": True,
        "EligibleForCandidate": False,
        "Step": 6,
        "Notes": "Negative control; not eligible for candidate selection",
    },
    {
        "ComponentLabel": "SecondCandleOpen",
        "SourceEXP": "EXP-024",
        "Verdict": "SUPPORTED",
        "EligibleForChain": True,
        "EligibleForCandidate": True,
        "Step": 7,
        "Notes": "Eligible; supported execution rule",
    },
    {
        "ComponentLabel": "RiskModel_2R",
        "SourceEXP": "EXP-025",
        "Verdict": "PLANNED",
        "EligibleForChain": None,
        "EligibleForCandidate": None,
        "Step": 8,
        "Notes": "Pending EXP-025 execution",
    },
]


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def _read_exp_result(path: Path) -> pd.DataFrame:
    """Load a CSV result file, raising FileNotFoundError with a descriptive message."""
    if not path.exists():
        raise FileNotFoundError(f"Required prerequisite not found: {path}")
    return pd.read_csv(path)


def resolve_exp025_status() -> tuple[str, bool]:
    """Return EXP-025 verdict and whether it uses the current criterion contract."""
    results_path = EXP025_DIR / "results.json"
    if not results_path.exists():
        return "PLANNED", False
    try:
        with results_path.open() as fh:
            data = json.load(fh)
        summary = data.get("verdict_summary", {})
        verdict = str(summary.get("verdict", "PLANNED"))
        current = summary.get("criterion_version") == REQUIRED_EXP025_CRITERION_VERSION
        return verdict, current
    except Exception:
        return "PLANNED", False


def build_eligibility_matrix(exp025_verdict: str, exp025_current: bool) -> pd.DataFrame:
    """Build component eligibility matrix with resolved EXP-025 verdict.

    Parameters
    ----------
    exp025_verdict : str
        Verdict string loaded from EXP-025 results.json or 'PLANNED'.
    exp025_current : bool
        True only when EXP-025 was produced by the current superiority criterion.

    Returns
    -------
    pd.DataFrame
        Component eligibility table.
    """
    rows = [dict(r) for r in _BASE_ELIGIBILITY]
    for row in rows:
        if row["ComponentLabel"] == "RiskModel_2R":
            row["Verdict"] = exp025_verdict
            eligible = exp025_current and exp025_verdict in ("FOR", "SUPPORTED")
            row["EligibleForChain"] = eligible
            row["EligibleForCandidate"] = eligible
            if not exp025_current:
                row["Notes"] = "Excluded until EXP-025 is rerun with superiority_v2 criterion"
    return pd.DataFrame(rows)


def load_step1_sweep() -> pd.DataFrame:
    """Load EXP-015 sweep events (EventType==Sweep, !Ambiguous60)."""
    df = _read_exp_result(EXP015_DIR / "sweep_events.csv")
    df = df[df["EventType"] == "Sweep"].copy()
    if "Ambiguous60" in df.columns:
        df = df[~df["Ambiguous60"].astype(bool)]
    return df.reset_index(drop=True)


def load_step2_macro(step1: pd.DataFrame) -> pd.DataFrame:
    """Join InMacro flag from EXP-016 onto step1 events; keep InMacro==True.

    Parameters
    ----------
    step1 : pd.DataFrame
        Step-1 sweep events.

    Returns
    -------
    pd.DataFrame
        Subset of step1 events that have macro context.
    """
    df16 = _read_exp_result(EXP016_DIR / "sweep_events.csv")
    df16 = df16[df16["EventType"] == "Sweep"][["Instrument", "Segment", "CloseTime", "InMacro"]].copy()
    merged = step1.merge(df16, on=["Instrument", "Segment", "CloseTime"], how="left")
    merged["InMacro"] = merged["InMacro"].fillna(False).astype(bool)
    return merged[merged["InMacro"]].reset_index(drop=True)


def load_step3_pd(step2: pd.DataFrame) -> pd.DataFrame:
    """Join PassMidpointFilter from EXP-017 onto step2 events; keep filter==True.

    Parameters
    ----------
    step2 : pd.DataFrame
        Step-2 macro-filtered sweep events.

    Returns
    -------
    pd.DataFrame
        Subset with PassMidpointFilter==True.
    """
    df17 = _read_exp_result(EXP017_DIR / "sweep_events_with_midpoint.csv")
    flag_cols = ["Instrument", "Segment", "CloseTime", "PassMidpointFilter"]
    df17 = df17[[c for c in flag_cols if c in df17.columns]].copy()
    merged = step2.merge(df17, on=["Instrument", "Segment", "CloseTime"], how="left")
    merged["PassMidpointFilter"] = merged["PassMidpointFilter"].fillna(False).astype(bool)
    return merged[merged["PassMidpointFilter"]].reset_index(drop=True)


def load_step4_displacement() -> pd.DataFrame:
    """Load EXP-018 DisplacementClose events (RiskFeasible, !Ambiguous60)."""
    df = _read_exp_result(EXP018_DIR / "entry_proxy_events.csv")
    df = df[df["EntryProxy"] == "DisplacementClose"].copy()
    if "RiskFeasible" in df.columns:
        df = df[df["RiskFeasible"].astype(bool)]
    if "Ambiguous60" in df.columns:
        df = df[~df["Ambiguous60"].astype(bool)]
    return df.reset_index(drop=True)


def load_step5_ifvg() -> pd.DataFrame:
    """Load EXP-021 IFVGClose events (RiskFeasible, !Ambiguous60)."""
    df = _read_exp_result(EXP021_DIR / "entry_outcomes.csv")
    df = df[df["EntryProxy"] == "IFVGClose"].copy()
    if "RiskFeasible" in df.columns:
        df = df[df["RiskFeasible"].astype(bool)]
    if "Ambiguous60" in df.columns:
        df = df[~df["Ambiguous60"].astype(bool)]
    return df.reset_index(drop=True)


def load_step6_breaker() -> pd.DataFrame:
    """Load EXP-023 BreakerClose events (RiskFeasible, !Ambiguous60)."""
    df = _read_exp_result(EXP023_DIR / "outcome_events.csv")
    df = df[df["EntryProxy"] == "BreakerClose"].copy()
    if "RiskFeasible" in df.columns:
        df = df[df["RiskFeasible"].astype(bool)]
    if "Ambiguous60" in df.columns:
        df = df[~df["Ambiguous60"].astype(bool)]
    return df.reset_index(drop=True)


def load_step7_execution() -> pd.DataFrame:
    """Load EXP-024 SecondCandleOpen events (RiskFeasible, !Ambiguous60)."""
    df = _read_exp_result(EXP024_DIR / "entry_timing_outcomes.csv")
    df = df[df["EntryProxy"] == "SecondCandleOpen"].copy()
    if "RiskFeasible" in df.columns:
        df = df[df["RiskFeasible"].astype(bool)]
    if "Ambiguous60" in df.columns:
        df = df[~df["Ambiguous60"].astype(bool)]
    return df.reset_index(drop=True)


def load_step8_risk_model() -> pd.DataFrame | None:
    """Load EXP-025 exit outcomes (2R_R column). Returns None if not available."""
    path = EXP025_DIR / "exit_outcomes.csv"
    if not path.exists():
        LOGGER.info("EXP-025 exit_outcomes.csv not found; skipping step 8.")
        return None
    df = pd.read_csv(path)
    if "2R_R" not in df.columns:
        LOGGER.warning("EXP-025 exit_outcomes.csv lacks '2R_R' column; skipping step 8.")
        return None
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Event identity helpers
# ---------------------------------------------------------------------------

def _stable_keys(df: pd.DataFrame, columns: list[str]) -> pd.Series:
    """Build stable string keys for matching nested event-chain rows."""
    key_frame = df[columns].copy()
    for col in columns:
        if col in {"NYDate", "SweepTime", "EntryTime"}:
            key_frame[col] = pd.to_datetime(key_frame[col], errors="coerce").astype("string")
        else:
            key_frame[col] = key_frame[col].astype("string")
    return key_frame.fillna("<NA>").agg("\x1f".join, axis=1)


def filter_to_previous_step(
    current: pd.DataFrame,
    previous: pd.DataFrame,
    label: str,
    preferred_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Keep only current-step rows with an identity present in the previous step.

    This enforces the EXP-026 ablation requirement that each component is added
    to the existing candidate set instead of comparing unrelated event pools.
    """
    if current.empty or previous.empty:
        LOGGER.info("%s nested retention: 0/%d rows", label, len(current))
        return current.iloc[0:0].copy()

    preferred = preferred_columns or EVENT_ID_COLUMNS
    common = [c for c in preferred if c in current.columns and c in previous.columns]
    if len(common) < 4:
        raise ValueError(
            f"{label} cannot be nested: insufficient common identity columns {common}"
        )

    previous_keys = set(_stable_keys(previous, common))
    mask = _stable_keys(current, common).isin(previous_keys)
    filtered = current[mask].copy().reset_index(drop=True)
    LOGGER.info(
        "%s nested retention: %d/%d rows using %s",
        label, len(filtered), len(current), ",".join(common),
    )
    return filtered


# ---------------------------------------------------------------------------
# Pure computation
# ---------------------------------------------------------------------------

def _aggregate_step_metrics(
    df: pd.DataFrame,
    step_num: int,
    step_label: str,
    sub_chain: str,
    hit1r_col: str | None,
    return_r_col: str | None,
) -> list[dict[str, Any]]:
    """Compute per-instrument/segment metrics for one chain step.

    Parameters
    ----------
    df : pd.DataFrame
        Events for this step.
    step_num : int
        Chain step number (1-8).
    step_label : str
        Human-readable step label.
    sub_chain : str
        'A' or 'B'.
    hit1r_col : str or None
        Column name for hit-rate (used for proxy expectancy in steps 1-3).
    return_r_col : str or None
        Column name for realized return (steps 4-8).

    Returns
    -------
    list[dict]
        One row per instrument/segment.
    """
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        for segment in ("Train", "Test"):
            grp = df[(df["Instrument"] == instrument) & (df["Segment"] == segment)]
            n = len(grp)
            mean_hit = np.nan
            mean_return = np.nan
            proxy_exp = np.nan
            if hit1r_col and hit1r_col in grp.columns:
                vals = pd.to_numeric(grp[hit1r_col], errors="coerce").dropna()
                mean_hit = float(vals.mean()) if len(vals) > 0 else np.nan
            if return_r_col and return_r_col in grp.columns:
                rvals = pd.to_numeric(grp[return_r_col], errors="coerce").dropna()
                mean_return = float(rvals.mean()) if len(rvals) > 0 else np.nan
            if not np.isnan(mean_return):
                proxy_exp = mean_return
            elif not np.isnan(mean_hit):
                proxy_exp = 2 * mean_hit - 1
            rows.append({
                "Step": step_num,
                "StepLabel": step_label,
                "SubChain": sub_chain,
                "Instrument": instrument,
                "Segment": segment,
                "EventCount": n,
                "MeanHit1R": mean_hit,
                "MeanReturn_R": mean_return,
                "ProxyExpectancy": proxy_exp,
            })
    return rows


def build_chain_steps(
    step1: pd.DataFrame,
    step2: pd.DataFrame,
    step3: pd.DataFrame,
    step4: pd.DataFrame,
    step5: pd.DataFrame,
    step6: pd.DataFrame,
    step7: pd.DataFrame,
    step8: pd.DataFrame | None,
) -> pd.DataFrame:
    """Aggregate metrics across all chain steps.

    Parameters
    ----------
    step1-step8 : pd.DataFrame or None
        Loaded event sets per chain step.

    Returns
    -------
    pd.DataFrame
        Chain summary with one row per step/instrument/segment.
    """
    all_rows: list[dict[str, Any]] = []
    # Sub-chain A: proxy expectancy from Hit1R_60m
    for step_num, df, label in [
        (1, step1, "Sweep"),
        (2, step2, "Sweep+Macro"),
        (3, step3, "Sweep+Macro+PD"),
    ]:
        all_rows.extend(_aggregate_step_metrics(df, step_num, label, "A", "Hit1R_60m", None))
    # Sub-chain B: Return_R_60m available
    b_steps = [
        (4, step4, "Displacement"),
        (5, step5, "Disp+IFVG"),
        (6, step6, "Disp+Breaker"),
        (7, step7, "Disp+SCO"),
    ]
    for step_num, df, label in b_steps:
        all_rows.extend(_aggregate_step_metrics(df, step_num, label, "B", "Hit1R_60m", "Return_R_60m"))
    if step8 is not None:
        all_rows.extend(_aggregate_step_metrics(step8, 8, "Disp+SCO+2R", "B", None, "2R_R"))
    return pd.DataFrame(all_rows)


def _bootstrap_mean_diff(
    a: np.ndarray,
    b: np.ndarray,
    rng: np.random.Generator,
    reps: int,
) -> tuple[float, float, float]:
    """Bootstrap mean(a) – mean(b) with 95% CI.

    Parameters
    ----------
    a, b : np.ndarray
        Realized-R arrays for two adjacent chain steps.
    rng : np.random.Generator
        Seeded random generator.
    reps : int
        Bootstrap resamples.

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


def compute_marginal_bootstrap(
    chain_steps_df: pd.DataFrame,
    steps_data: dict[int, pd.DataFrame],
) -> pd.DataFrame:
    """Bootstrap marginal contribution between adjacent sub-chain B steps.

    Computes mean(step_n) – mean(step_{n-1}) for Return_R_60m or 2R_R.

    Parameters
    ----------
    chain_steps_df : pd.DataFrame
        Aggregated chain-step metrics.
    steps_data : dict[int, pd.DataFrame]
        Raw event DataFrames keyed by step number (4-8).

    Returns
    -------
    pd.DataFrame
        Bootstrap results with columns Instrument, Segment, StepN, StepNm1,
        MeanDiff, CI_Lo, CI_Hi, CI_Hi_Positive.
    """
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    # map step → return column
    step_return_col = {4: "Return_R_60m", 5: "Return_R_60m", 6: "Return_R_60m",
                       7: "Return_R_60m", 8: "2R_R"}
    adjacent_pairs = [(5, 4), (6, 5), (7, 6), (8, 7)]
    rows: list[dict[str, Any]] = []
    for step_n, step_nm1 in adjacent_pairs:
        if step_n not in steps_data or step_nm1 not in steps_data:
            continue
        df_n = steps_data[step_n]
        df_nm1 = steps_data[step_nm1]
        col_n = step_return_col[step_n]
        col_nm1 = step_return_col[step_nm1]
        if col_n not in df_n.columns or col_nm1 not in df_nm1.columns:
            continue
        for instrument in INSTRUMENTS:
            for segment in ("Train", "Test"):
                a = pd.to_numeric(
                    df_n[(df_n["Instrument"] == instrument) & (df_n["Segment"] == segment)][col_n],
                    errors="coerce",
                ).dropna().to_numpy()
                b = pd.to_numeric(
                    df_nm1[(df_nm1["Instrument"] == instrument) & (df_nm1["Segment"] == segment)][col_nm1],
                    errors="coerce",
                ).dropna().to_numpy()
                mean_diff, ci_lo, ci_hi = _bootstrap_mean_diff(a, b, rng, BOOTSTRAP_REPS)
                step_label_n = chain_steps_df[chain_steps_df["Step"] == step_n]["StepLabel"].iloc[0] if not chain_steps_df[chain_steps_df["Step"] == step_n].empty else str(step_n)
                rows.append({
                    "Instrument": instrument,
                    "Segment": segment,
                    "StepN": step_n,
                    "StepNm1": step_nm1,
                    "StepLabel": step_label_n,
                    "N_n": len(a),
                    "N_nm1": len(b),
                    "MeanDiff": mean_diff,
                    "CI_Lo": ci_lo,
                    "CI_Hi": ci_hi,
                    "CI_Hi_Positive": bool(np.isfinite(ci_hi) and ci_hi > 0),
                })
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def select_manifest_components(
    bootstrap_marginal: pd.DataFrame,
    eligibility: pd.DataFrame,
    exp025_verdict: str,
) -> dict[str, Any]:
    """Select components for the frozen model manifest based on test marginal CIs.

    A component is selected only if it is eligible for candidate selection and
    at least MIN_COMPONENT_PASS_INSTRUMENTS instruments have a positive test
    point estimate with a bootstrap lower bound above zero.

    Parameters
    ----------
    bootstrap_marginal : pd.DataFrame
        Marginal bootstrap results from compute_marginal_bootstrap.
    eligibility : pd.DataFrame
        Component eligibility matrix.
    exp025_verdict : str
        EXP-025 verdict (for RiskModel_2R eligibility).

    Returns
    -------
    dict
        Manifest with selected_components, exit_variant, stop_rule,
        cost_scenario, excluded_components, notes.
    """
    step_to_component = {5: "IFVG", 6: "Breaker", 7: "SecondCandleOpen", 8: "RiskModel_2R"}
    selected: list[str] = ["Sweep", "Displacement"]
    excluded: dict[str, str] = {}
    evidence: dict[str, Any] = {}

    candidate_eligible_map = {
        str(row["ComponentLabel"]): bool(row["EligibleForCandidate"])
        for _, row in eligibility.fillna(False).iterrows()
    }

    if bootstrap_marginal.empty:
        notes = "No bootstrap data; no eligible full-model candidate selected."
    else:
        for step_n, component in step_to_component.items():
            if not candidate_eligible_map.get(component, False):
                excluded[component] = "Not eligible for candidate selection"
                continue
            if component == "RiskModel_2R" and exp025_verdict not in ("FOR", "SUPPORTED"):
                excluded[component] = f"EXP-025 verdict is {exp025_verdict}"
                continue
            test_rows = bootstrap_marginal[
                (bootstrap_marginal["StepN"] == step_n)
                & (bootstrap_marginal["Segment"] == "Test")
            ]
            if test_rows.empty:
                excluded[component] = "No bootstrap data for this step"
                continue
            pass_rows = test_rows[
                test_rows["MeanDiff"].gt(0) & test_rows["CI_Lo"].gt(0)
            ]
            n_pass = int(pass_rows["Instrument"].nunique())
            evidence[component] = {
                "passing_instruments": n_pass,
                "required_instruments": MIN_COMPONENT_PASS_INSTRUMENTS,
                "rule": "MeanDiff > 0 and CI_Lo > 0 on test segment",
            }
            if n_pass >= MIN_COMPONENT_PASS_INSTRUMENTS:
                selected.append(component)
            else:
                mean_diff = test_rows["MeanDiff"].mean()
                excluded[component] = (
                    f"Insufficient positive evidence: {n_pass}/"
                    f"{MIN_COMPONENT_PASS_INSTRUMENTS} instruments pass "
                    f"(mean_diff={mean_diff:.3f})"
                )

        if len(selected) <= 2:
            notes = "No optional component met the positive lower-CI rule; no full-model candidate selected."
        else:
            notes = f"Components selected by positive lower-CI evidence: {selected}"

    candidate_eligible = len(selected) > 2

    return {
        "selected_components": selected,
        "exit_variant": "2R",
        "stop_rule": "EXP-015 original stop (inherited via EXP-018/EXP-021/EXP-024 chain)",
        "cost_scenario": "LIGHT_COST_PROXY",
        "candidate_eligible": candidate_eligible,
        "source_verdict": "SUPPORTED" if candidate_eligible else "INCONCLUSIVE",
        "selection_rule_version": SELECTION_RULE_VERSION,
        "selection_evidence": evidence,
        "excluded_components": excluded,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# Plotting helpers
# ---------------------------------------------------------------------------

def plot_event_count_waterfall(chain_df: pd.DataFrame, save_path: Path) -> None:
    """Plot event counts by chain step, with train/test breakdown.

    Parameters
    ----------
    chain_df : pd.DataFrame
        Aggregated chain-step metrics.
    save_path : Path
        Output PNG path.
    """
    agg = chain_df.groupby(["Step", "StepLabel", "Segment"])["EventCount"].sum().reset_index()
    steps = chain_df[["Step", "StepLabel"]].drop_duplicates().sort_values("Step")
    labels = [f"S{r['Step']}: {r['StepLabel']}" for _, r in steps.iterrows()]
    x = np.arange(len(labels))
    width = 0.35
    train = agg[agg["Segment"] == "Train"].set_index("Step")["EventCount"]
    test = agg[agg["Segment"] == "Test"].set_index("Step")["EventCount"]
    step_nums = steps["Step"].tolist()
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.bar(x - width / 2, [train.get(s, 0) for s in step_nums], width, label="Train", alpha=0.8)
    ax.bar(x + width / 2, [test.get(s, 0) for s in step_nums], width, label="Test", alpha=0.8)
    ax.axvline(2.5, color="grey", linestyle="--", linewidth=0.8, label="Sub-chain B starts")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=8)
    ax.set_ylabel("Event Count")
    ax.set_title("EXP-026 Event-Count Waterfall by Chain Step")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_marginal_expectancy(bootstrap_marginal: pd.DataFrame, save_path: Path) -> None:
    """Plot bootstrap 95% CI for marginal expectancy gain (step_n vs step_{n-1}).

    Parameters
    ----------
    bootstrap_marginal : pd.DataFrame
        Bootstrap marginal results.
    save_path : Path
        Output PNG path.
    """
    if bootstrap_marginal.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No bootstrap data", ha="center", va="center", transform=ax.transAxes)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return
    test_df = bootstrap_marginal[bootstrap_marginal["Segment"] == "Test"].copy()
    fig, ax = plt.subplots(figsize=(12, 5))
    y_pos = np.arange(len(test_df))
    positive_lower_ci = test_df["MeanDiff"].gt(0) & test_df["CI_Lo"].gt(0)
    ax.barh(y_pos, test_df["MeanDiff"].values, xerr=[
        test_df["MeanDiff"].values - test_df["CI_Lo"].values,
        test_df["CI_Hi"].values - test_df["MeanDiff"].values,
    ], align="center", alpha=0.7, capsize=4, color=[
        "green" if v else "red" for v in positive_lower_ci
    ])
    ax.axvline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_yticks(y_pos)
    ax.set_yticklabels([
        f"{r['StepLabel']} ({r['Instrument']})" for _, r in test_df.iterrows()
    ], fontsize=7)
    ax.set_xlabel("Mean Diff in Return_R (step_n – step_{n-1})")
    ax.set_title("EXP-026 Marginal Expectancy Gain (Bootstrap 95% CI, Test Segment)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_retention_percentage(chain_df: pd.DataFrame, save_path: Path) -> None:
    """Plot event retention (%) relative to sub-chain baseline per segment.

    Sub-chain A baseline = Step 1; Sub-chain B baseline = Step 4.

    Parameters
    ----------
    chain_df : pd.DataFrame
        Aggregated chain-step metrics.
    save_path : Path
        Output PNG path.
    """
    baselines = {"A": 1, "B": 4}
    rows: list[dict[str, Any]] = []
    for segment in ("Train", "Test"):
        seg_df = chain_df[chain_df["Segment"] == segment]
        for sub_chain, base_step in baselines.items():
            base_row = seg_df[(seg_df["SubChain"] == sub_chain) & (seg_df["Step"] == base_step)]
            if base_row.empty:
                continue
            base_count = base_row["EventCount"].sum()
            if base_count == 0:
                continue
            sub_df = seg_df[seg_df["SubChain"] == sub_chain].copy()
            sub_df["RetentionPct"] = 100 * sub_df["EventCount"] / base_count
            sub_df["Segment"] = segment
            rows.append(sub_df)
    if not rows:
        return
    ret_df = pd.concat(rows, ignore_index=True)
    agg = ret_df.groupby(["Step", "StepLabel", "SubChain", "Segment"])["RetentionPct"].mean().reset_index()
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
    for ax, segment in zip(axes, ("Train", "Test")):
        sub_df = agg[agg["Segment"] == segment]
        for sub_chain in ("A", "B"):
            s = sub_df[sub_df["SubChain"] == sub_chain].sort_values("Step")
            ax.plot(s["StepLabel"], s["RetentionPct"], marker="o", label=f"Chain {sub_chain}")
        ax.axhline(100, color="grey", linestyle="--", linewidth=0.8)
        ax.set_title(f"EXP-026 Retention % vs Baseline — {segment}")
        ax.set_xlabel("Step Label")
        ax.set_ylabel("Retention %")
        ax.tick_params(axis="x", rotation=20)
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_contribution_heatmap(chain_df: pd.DataFrame, save_path: Path) -> None:
    """Plot train/test mean ProxyExpectancy heatmap by step and instrument.

    Parameters
    ----------
    chain_df : pd.DataFrame
        Aggregated chain-step metrics.
    save_path : Path
        Output PNG path.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for ax, segment in zip(axes, ("Train", "Test")):
        pivot = chain_df[chain_df["Segment"] == segment].pivot_table(
            index="Instrument", columns="StepLabel", values="ProxyExpectancy", aggfunc="mean"
        )
        step_order = chain_df.sort_values("Step")["StepLabel"].unique().tolist()
        pivot = pivot.reindex(index=INSTRUMENTS, columns=[c for c in step_order if c in pivot.columns])
        sns.heatmap(pivot, annot=True, fmt=".2f", center=0, cmap="RdYlGn",
                    linewidths=0.4, ax=ax, vmin=-1, vmax=2)
        ax.set_title(f"EXP-026 Proxy Expectancy by Step × Instrument — {segment}")
        ax.set_xlabel("Chain Step")
        ax.set_ylabel("Instrument")
        ax.tick_params(axis="x", rotation=25)
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


def write_outputs(
    eligibility: pd.DataFrame,
    chain_df: pd.DataFrame,
    bootstrap_marginal: pd.DataFrame,
    manifest: dict[str, Any],
    plots_dir: Path,
    results_dir: Path,
) -> None:
    """Write all EXP-026 result files, plots, and model manifest.

    Parameters
    ----------
    eligibility : pd.DataFrame
        Component eligibility matrix.
    chain_df : pd.DataFrame
        Aggregated chain-step metrics.
    bootstrap_marginal : pd.DataFrame
        Marginal contribution bootstrap results.
    manifest : dict
        Model manifest for EXP-027.
    plots_dir : Path
        Directory for PNG plots.
    results_dir : Path
        Directory for CSV/JSON/TXT outputs.
    """
    eligibility.to_csv(results_dir / "component_eligibility.csv", index=False)
    chain_df.to_csv(results_dir / "chain_steps.csv", index=False)
    if not bootstrap_marginal.empty:
        bootstrap_marginal.to_csv(results_dir / "bootstrap_marginal.csv", index=False)

    manifest_with_meta = {
        "experiment_id": "EXP-026",
        "title": "Incremental ICT Component Ablation",
        **manifest,
    }
    with (results_dir / "model_manifest.json").open("w", encoding="utf-8") as fh:
        json.dump(_json_safe(manifest_with_meta), fh, indent=2, default=str, allow_nan=False)

    verdict = manifest["source_verdict"]
    results_payload = {
        "experiment_id": "EXP-026",
        "verdict": verdict,
        "selected_components": manifest["selected_components"],
        "candidate_eligible": manifest["candidate_eligible"],
        "selection_rule_version": manifest["selection_rule_version"],
        "excluded_components": manifest["excluded_components"],
        "notes": manifest["notes"],
    }
    with (results_dir / "results.json").open("w", encoding="utf-8") as fh:
        json.dump(_json_safe(results_payload), fh, indent=2, default=str, allow_nan=False)

    with (results_dir / "numerical_summary.txt").open("w", encoding="utf-8") as fh:
        fh.write("EXP-026 Incremental ICT Component Ablation\n")
        fh.write(f"Verdict: {verdict}\n")
        fh.write(f"Selected components: {manifest['selected_components']}\n")
        fh.write(f"Candidate eligible: {manifest['candidate_eligible']}\n")
        fh.write(f"Notes: {manifest['notes']}\n\n")
        fh.write("Chain step summary (Test segment):\n")
        for _, r in chain_df[chain_df["Segment"] == "Test"].sort_values(["Instrument", "Step"]).iterrows():
            fh.write(
                f"  S{r['Step']:d} {r['StepLabel']:22s} {r['Instrument']:8s}: "
                f"N={r['EventCount']:4d}, ProxyExp={r['ProxyExpectancy']:.3f}, "
                f"MeanReturn_R={r['MeanReturn_R']:.3f}\n"
            )
        if not bootstrap_marginal.empty:
            fh.write("\nMarginal bootstrap (Test):\n")
            for _, r in bootstrap_marginal[bootstrap_marginal["Segment"] == "Test"].iterrows():
                fh.write(
                    f"  {r['StepLabel']:22s} {r['Instrument']:8s}: "
                    f"diff={r['MeanDiff']:.3f} CI=[{r['CI_Lo']:.3f},{r['CI_Hi']:.3f}] "
                    f"PositiveLowerCI={bool(r['MeanDiff'] > 0 and r['CI_Lo'] > 0)}\n"
                )

    plot_event_count_waterfall(chain_df, plots_dir / "01_event_count_waterfall.png")
    plot_marginal_expectancy(bootstrap_marginal, plots_dir / "02_marginal_expectancy.png")
    plot_retention_percentage(chain_df, plots_dir / "03_retention_percentage.png")
    plot_contribution_heatmap(chain_df, plots_dir / "04_contribution_heatmap.png")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_experiment() -> None:
    """Execute the EXP-026 incremental ICT component ablation workflow."""
    plots_dir = EXP_DIR / "plots"
    results_dir = EXP_DIR / "results"
    plots_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    exp025_verdict, exp025_current = resolve_exp025_status()
    LOGGER.info(
        "EXP-025 verdict: %s (current criterion=%s)",
        exp025_verdict, exp025_current,
    )

    eligibility = build_eligibility_matrix(exp025_verdict, exp025_current)
    LOGGER.info("Component eligibility matrix built (%d components)", len(eligibility))

    LOGGER.info("Loading chain step event sets …")
    step1 = load_step1_sweep()
    LOGGER.info("Step 1 (Sweep): %d events", len(step1))
    step2 = load_step2_macro(step1)
    LOGGER.info("Step 2 (Sweep+Macro): %d events", len(step2))
    step3 = load_step3_pd(step2)
    LOGGER.info("Step 3 (Sweep+Macro+PD): %d events", len(step3))
    step4 = load_step4_displacement()
    LOGGER.info("Step 4 (Displacement): %d events", len(step4))
    step5 = load_step5_ifvg()
    LOGGER.info("Step 5 (IFVG): %d events", len(step5))
    step6 = load_step6_breaker()
    LOGGER.info("Step 6 (Breaker): %d events", len(step6))
    step7 = load_step7_execution()
    LOGGER.info("Step 7 (SecondCandleOpen): %d events", len(step7))
    step8 = load_step8_risk_model()
    LOGGER.info("Step 8 (RiskModel_2R): %s", "loaded" if step8 is not None else "skipped")

    LOGGER.info("Enforcing nested event-chain identity for execution steps …")
    step5 = filter_to_previous_step(step5, step4, "Step 5 IFVG")
    step6 = filter_to_previous_step(step6, step5, "Step 6 Breaker")
    step7 = filter_to_previous_step(step7, step6, "Step 7 SecondCandleOpen")
    if step8 is not None:
        step8 = filter_to_previous_step(
            step8, step7, "Step 8 RiskModel_2R", ENTRY_ID_COLUMNS,
        )

    LOGGER.info("Building chain step aggregations …")
    chain_df = build_chain_steps(step1, step2, step3, step4, step5, step6, step7, step8)

    steps_data: dict[int, pd.DataFrame] = {
        4: step4, 5: step5, 6: step6, 7: step7,
    }
    if step8 is not None:
        steps_data[8] = step8

    LOGGER.info("Computing marginal bootstrap …")
    bootstrap_marginal = compute_marginal_bootstrap(chain_df, steps_data)

    manifest = select_manifest_components(bootstrap_marginal, eligibility, exp025_verdict)
    LOGGER.info("Model manifest: selected_components=%s", manifest["selected_components"])

    LOGGER.info("Writing outputs …")
    write_outputs(eligibility, chain_df, bootstrap_marginal, manifest, plots_dir, results_dir)

    print("EXP-026 complete.")
    print(f"Selected components: {manifest['selected_components']}")
    print(f"Notes: {manifest['notes']}")
    print(f"Manifest: {results_dir / 'model_manifest.json'}")
    print(f"Results: {results_dir}")


def main() -> None:
    """Entry point for manual execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_experiment()


if __name__ == "__main__":
    main()
