"""
Experiment EXP-007: Lenient-L5 Referee Variant.

Phase 002 lever-characterization. Measures the predeclared structurally-lenient L5
(``L5_lenient = ci_lower_bps > 0``) on the same frozen EXP-003 draws as the strict
gate, and reports whether it lowers the economic MDE at controlled FPR beyond the
EXP-006 threshold frontier, with the mandatory economically-sub-material pass-rate
accounting (design D-lenientL5).

Predeclared structural relationship (frozen harness, see scope): because the frozen
L5 is ``ci_lower_bps > materiality_bps`` and L3 already requires ``ci_lower_bps > 0``,
the lenient leg equals the EXP-006 ``tau=0`` endpoint and equals dropping L5
(``L1∧L2∧L3∧L4``). The experiment confirms this numerically; H-lenient's
structural-gain branch is expected to resolve FALSIFIED. Pure result-level
post-processing: no market data and no holdout are ever loaded.
"""
from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

from xen.referee_calibration import materiality_bps_for, wilson_interval, write_json

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-007"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXPERIMENT_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
GOVERNANCE_DIR = EXPERIMENT_DIR / "governance"
PRE_EXEC_REVIEW = GOVERNANCE_DIR / "pre-execution-review.md"

EXP001_METADATA = (
    PROJECT_ROOT / "python" / "experiments" / "EXP-001" / "results" / "run_metadata.json"
)
EXP003_DIR = PROJECT_ROOT / "python" / "experiments" / "EXP-003" / "results"
EXP003_METADATA = EXP003_DIR / "run_metadata.json"
EXP003_DRAWS = EXP003_DIR / "draw_verdicts.csv"
EXP003_MDE = EXP003_DIR / "mde_summary.csv"
EXP006_DIR = PROJECT_ROOT / "python" / "experiments" / "EXP-006" / "results"
EXP006_METADATA = EXP006_DIR / "run_metadata.json"
EXP006_MDE = EXP006_DIR / "threshold_mde_summary.csv"
EXP006_FPR = EXP006_DIR / "threshold_fpr_summary.csv"
EXP006_STRICT_CHECK = EXP006_DIR / "strict_reference_check.csv"
# EXP-006 per-draw tau-sweep verdicts; the tau=0 rows are the verdict-level
# reference for the lenient leg (structural-equivalence cross-check).
EXP006_DRAW_VERDICTS = EXP006_DIR / "threshold_draw_verdicts.csv"

# Draw-identity keys shared by the EXP-003 draws and the EXP-006 tau-sweep, used
# to join the two independent reconstructions for the verdict-level equivalence.
DRAW_KEY_COLS = ["instrument", "domain", "scenario", "generator", "edge_bps", "draw", "alpha"]

# Carried-forward Phase 001/002 invariants (P1-D-op, P1-D-prec).
ALPHA0 = 0.05
POWER_TARGET = 0.80
FPR_HALF_WIDTH_TARGET = 0.03
TPR_HALF_WIDTH_TARGET = 0.05
SUBMATERIAL_LIMIT = 0.50

# EXP-006 zero-buffer endpoint multiplier the lenient leg must coincide with.
TAU0_MULTIPLIER = 0.0
MDE_MATCH_TOL = 1e-9

# Operator predeclaration confirmation of D-lenientL5 must be recorded in this
# experiment's Stage 4 review before any measurement is produced (scope
# "Pre-execution confirmation"; mirrors EXP-005's gate).
PREDECLARATION_TOKEN = "PHASE002-PREDECLARATION-CONFIRMED"

LEG_SCHEMA = pl.Struct(
    [
        pl.Field("L1_readiness", pl.Boolean),
        pl.Field("L2_integrity", pl.Boolean),
        pl.Field("L3_outcome", pl.Boolean),
        pl.Field("L4_stability", pl.Boolean),
        pl.Field("materiality_bps", pl.Float64),
    ]
)
DRAW_COLS = [
    "instrument",
    "domain",
    "scenario",
    "generator",
    "edge_bps",
    "draw",
    "alpha",
    "passed",
    "effect_bps",
    "ci_lower_bps",
    "leg_results",
]

LOGGER = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Output helpers
# --------------------------------------------------------------------------- #
def configure_logging() -> None:
    """Configure concise INFO-level logging for the manual run."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def ensure_output_dirs() -> None:
    """Create the experiment ``results/`` and ``plots/`` directories."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write a list of result dicts to ``path`` as CSV."""
    pl.DataFrame(rows).write_csv(path)


# --------------------------------------------------------------------------- #
# Dependency and predeclaration gates
# --------------------------------------------------------------------------- #
def require_dependencies() -> dict[str, str]:
    """Fail fast unless EXP-001/003 and a valid EXP-006 frontier are available.

    EXP-006 must be COMPLETE with a passing strict-reference reproduction, since
    EXP-007 is interpreted only against the EXP-006 threshold frontier.

    Returns
    -------
    dict[str, str]
        Recorded upstream statuses for ``run_metadata.json``.
    """
    if not EXP001_METADATA.exists():
        raise FileNotFoundError(f"EXP-001 metadata not found: {EXP001_METADATA}")
    exp001 = json.loads(EXP001_METADATA.read_text(encoding="utf-8"))
    if exp001.get("overall_status") != "PASS":
        raise RuntimeError(f"EXP-001 did not PASS: {exp001.get('overall_status')}")

    if not EXP003_METADATA.exists():
        raise FileNotFoundError(f"EXP-003 metadata not found: {EXP003_METADATA}")
    exp003 = json.loads(EXP003_METADATA.read_text(encoding="utf-8"))
    if exp003.get("overall_status") != "COMPLETE":
        raise RuntimeError(f"EXP-003 is not COMPLETE: {exp003.get('overall_status')}")
    for artifact in (EXP003_DRAWS, EXP003_MDE):
        if not artifact.exists():
            raise FileNotFoundError(f"Required EXP-003 artifact missing: {artifact}")

    if not EXP006_METADATA.exists():
        raise FileNotFoundError(f"EXP-006 metadata not found: {EXP006_METADATA}")
    exp006 = json.loads(EXP006_METADATA.read_text(encoding="utf-8"))
    if exp006.get("overall_status") != "COMPLETE":
        raise RuntimeError(f"EXP-006 is not COMPLETE: {exp006.get('overall_status')}")
    if not exp006.get("strict_reference_pass"):
        raise RuntimeError("EXP-006 strict-reference reproduction did not pass; frontier invalid")
    for artifact in (EXP006_MDE, EXP006_FPR, EXP006_STRICT_CHECK, EXP006_DRAW_VERDICTS):
        if not artifact.exists():
            raise FileNotFoundError(f"Required EXP-006 artifact missing: {artifact}")
    return {
        "exp001_status": str(exp001.get("overall_status")),
        "exp003_status": str(exp003.get("overall_status")),
        "exp006_status": str(exp006.get("overall_status")),
        "exp006_strict_reference_pass": str(bool(exp006.get("strict_reference_pass"))),
    }


def require_predeclaration_confirmation() -> dict[str, str]:
    """Require the recorded operator confirmation of D-lenientL5 before measuring.

    Returns
    -------
    dict[str, str]
        Confirmation provenance for ``run_metadata.json``.
    """
    if not PRE_EXEC_REVIEW.exists():
        raise FileNotFoundError(
            "Stage 4 pre-execution review missing; operator D-lenientL5 "
            f"confirmation required before EXP-007 runs: {PRE_EXEC_REVIEW}"
        )
    text = PRE_EXEC_REVIEW.read_text(encoding="utf-8")
    if PREDECLARATION_TOKEN not in text:
        raise RuntimeError(
            f"Predeclaration token '{PREDECLARATION_TOKEN}' not found in "
            f"{PRE_EXEC_REVIEW}. Record operator confirmation of D-lenientL5 before running."
        )
    return {"predeclaration_confirmed": "true", "confirmation_source": PRE_EXEC_REVIEW.name}


# --------------------------------------------------------------------------- #
# Load and variant reconstruction (pure, vectorized)
# --------------------------------------------------------------------------- #
def load_gate_draws() -> pl.DataFrame:
    """Load EXP-003 gate-stack draws with strict, lenient, and drop-L5 verdicts.

    Returns
    -------
    pl.DataFrame
        One row per draw with ``passed`` (frozen strict), ``passed_lenient``
        (``ci_lower_bps > 0``), and ``passed_drop_l5`` (``L1∧L2∧L3∧L4``).
    """
    legs_pass = (
        pl.col("L1_readiness")
        & pl.col("L2_integrity")
        & pl.col("L3_outcome")
        & pl.col("L4_stability")
    )
    draws = (
        pl.scan_csv(EXP003_DRAWS)
        .filter(pl.col("referee") == "gate_stack")
        .select(DRAW_COLS)
        .with_columns(pl.col("leg_results").str.json_decode(LEG_SCHEMA).alias("legs"))
        .unnest("legs")
        .drop("leg_results")
        .with_columns(
            (legs_pass & (pl.col("ci_lower_bps") > 0.0)).alias("passed_lenient"),
            legs_pass.alias("passed_drop_l5"),
        )
        .collect()
    )
    if draws.is_empty():
        raise RuntimeError("No gate_stack rows found in EXP-003 draw_verdicts.csv")
    return draws


# --------------------------------------------------------------------------- #
# Rate summaries (Wilson) and MDE (pure)
# --------------------------------------------------------------------------- #
def wilson_rows_from_counts(
    grouped: pl.DataFrame, *, id_cols: list[str], rate_name: str
) -> list[dict[str, Any]]:
    """Attach Wilson-interval rates to an aggregated ``successes``/``n`` frame.

    Parameters
    ----------
    grouped : pl.DataFrame
        Frame with ``id_cols`` plus integer ``successes`` and ``n`` columns.
    id_cols : list[str]
        Columns identifying each rate cell.
    rate_name : str
        Output key for the pass rate (``"fpr"`` / ``"tpr"``).

    Returns
    -------
    list[dict[str, Any]]
        One rate row per cell, schema-compatible with the EXP-003 summaries.
    """
    rows: list[dict[str, Any]] = []
    for record in grouped.sort(id_cols).iter_rows(named=True):
        successes = int(record["successes"])
        n = int(record["n"])
        center, lower, upper = wilson_interval(successes, n)
        out = {col: record[col] for col in id_cols}
        out.update(
            {
                rate_name: successes / n if n else math.nan,
                "wilson_center": center,
                "wilson_lower": lower,
                "wilson_upper": upper,
                "wilson_half_width": (upper - lower) / 2.0 if n else math.nan,
                "successes": successes,
                "n": n,
            }
        )
        rows.append(out)
    return rows


def summarize_fpr(draws: pl.DataFrame, pass_col: str, variant: str) -> list[dict[str, Any]]:
    """Pooled FPR per (domain, alpha) for one variant from null-scenario draws."""
    grouped = (
        draws.filter(pl.col("scenario") == "null")
        .group_by(["domain", "alpha"])
        .agg(pl.col(pass_col).sum().alias("successes"), pl.len().alias("n"))
    )
    rows = wilson_rows_from_counts(grouped, id_cols=["domain", "alpha"], rate_name="fpr")
    for row in rows:
        row["variant"] = variant
    return rows


def summarize_tpr(draws: pl.DataFrame, pass_col: str, variant: str) -> list[dict[str, Any]]:
    """Pooled TPR per (domain, alpha, edge_bps) for one variant from positive draws."""
    grouped = (
        draws.filter(pl.col("scenario") == "positive")
        .group_by(["domain", "alpha", "edge_bps"])
        .agg(pl.col(pass_col).sum().alias("successes"), pl.len().alias("n"))
    )
    rows = wilson_rows_from_counts(
        grouped, id_cols=["domain", "alpha", "edge_bps"], rate_name="tpr"
    )
    for row in rows:
        row["variant"] = variant
    return rows


def positive_edge_grid(draws: pl.DataFrame) -> list[float]:
    """Sorted distinct positive planted edges, used as the MDE search grid."""
    edges = (
        draws.filter(pl.col("scenario") == "positive")
        .get_column("edge_bps")
        .unique()
        .sort()
        .to_list()
    )
    return [float(edge) for edge in edges]


def compute_variant_mde(
    fpr_rows: list[dict[str, Any]],
    tpr_rows: list[dict[str, Any]],
    edge_grid: list[float],
    variant: str,
) -> list[dict[str, Any]]:
    """Smallest precise edge meeting the power target at controlled FPR, per (domain, alpha)."""
    prior_edge = {
        edge: (edge_grid[idx - 1] if idx > 0 else 0.0) for idx, edge in enumerate(edge_grid)
    }
    fpr_idx = {(row["domain"], row["alpha"]): row for row in fpr_rows}
    tpr_idx: dict[tuple[Any, Any], list[dict[str, Any]]] = {}
    for row in tpr_rows:
        tpr_idx.setdefault((row["domain"], row["alpha"]), []).append(row)

    output: list[dict[str, Any]] = []
    for key in sorted(tpr_idx, key=lambda item: (str(item[0]), float(item[1]))):
        domain, alpha = key
        fpr_row = fpr_idx.get(key)
        fpr_value = fpr_row["fpr"] if fpr_row else math.nan
        fpr_hw = fpr_row["wilson_half_width"] if fpr_row else math.nan
        fpr_precise = bool(fpr_row) and fpr_hw <= FPR_HALF_WIDTH_TARGET
        fpr_controlled = bool(fpr_row) and fpr_value <= float(alpha)

        mde_bps = math.nan
        grid_uncertainty = math.nan
        status = "PASS"
        if not fpr_row:
            status = "INCONCLUSIVE_MISSING_FPR"
        elif not fpr_precise:
            status = "INCONCLUSIVE_FPR_PRECISION"
        elif not fpr_controlled:
            status = "FPR_UNCONTROLLED"
        else:
            for tpr_row in sorted(tpr_idx[key], key=lambda item: float(item["edge_bps"])):
                if (
                    tpr_row["tpr"] >= POWER_TARGET
                    and tpr_row["wilson_half_width"] <= TPR_HALF_WIDTH_TARGET
                ):
                    mde_bps = float(tpr_row["edge_bps"])
                    grid_uncertainty = mde_bps - prior_edge.get(mde_bps, 0.0)
                    break
            if not math.isfinite(mde_bps):
                status = "INCONCLUSIVE_NO_CROSSING"

        output.append(
            {
                "domain": domain,
                "variant": variant,
                "alpha": alpha,
                "fpr": fpr_value,
                "fpr_wilson_half_width": fpr_hw,
                "mde_bps": mde_bps,
                "mde_grid_uncertainty_bps": grid_uncertainty,
                "status": status,
            }
        )
    return output


# --------------------------------------------------------------------------- #
# Structural equivalence, sub-material accounting, frontier comparison (pure)
# --------------------------------------------------------------------------- #
def exp006_tau0_verdict_mismatch(draws: pl.DataFrame) -> dict[tuple[Any, float], tuple[int, int]]:
    """Per (domain, alpha) verdict-level disagreement between EXP-007 lenient passes
    and EXP-006's independently reconstructed tau=0 (zero-buffer) gate verdicts.

    Reads EXP-006 ``threshold_draw_verdicts.csv`` at ``multiplier == 0`` and joins it
    to the EXP-007 draws on the shared draw-identity keys, so a defect in *either*
    reconstruction (sample membership, per-draw pass flags) is caught at the verdict
    level rather than hidden by a coincidental MDE-summary match.

    Returns
    -------
    dict[tuple[Any, float], tuple[int, int]]
        ``(domain, alpha) -> (pass_flag_mismatch_count, unmatched_draw_count)``.
    """
    tau0 = (
        pl.scan_csv(EXP006_DRAW_VERDICTS)
        .filter(pl.col("multiplier") == TAU0_MULTIPLIER)
        .select([*DRAW_KEY_COLS, "passed_tau"])
        .collect()
    )
    joined = draws.select([*DRAW_KEY_COLS, "passed_lenient"]).join(
        tau0, on=DRAW_KEY_COLS, how="left"
    )
    agg = (
        joined.with_columns(
            pl.col("passed_tau").is_null().alias("unmatched"),
            (
                pl.col("passed_tau").is_not_null()
                & (pl.col("passed_lenient") != pl.col("passed_tau"))
            ).alias("mismatch"),
        )
        .group_by(["domain", "alpha"])
        .agg(
            pl.col("mismatch").sum().alias("mismatch"),
            pl.col("unmatched").sum().alias("unmatched"),
        )
    )
    return {
        (row["domain"], float(row["alpha"])): (int(row["mismatch"]), int(row["unmatched"]))
        for row in agg.iter_rows(named=True)
    }


def structural_equivalence_check(
    draws: pl.DataFrame, lenient_mde: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool]:
    """Confirm lenient == drop-L5 and lenient == EXP-006 tau=0, both verdict-level.

    Three layers are folded into ``equivalence_pass``: (1) lenient == drop-L5 per
    draw (internal); (2) lenient == EXP-006 tau=0 per draw, cross-checked against
    EXP-006's ``threshold_draw_verdicts.csv`` (catches reconstruction drift between
    the two experiments); (3) lenient MDE == EXP-006 tau=0 MDE as a secondary summary
    check.

    Returns
    -------
    tuple[list[dict[str, Any]], bool]
        ``(check_rows, equivalence_pass)``.
    """
    per_draw = (
        draws.with_columns(
            (pl.col("passed_lenient") != pl.col("passed_drop_l5")).alias("mismatch")
        )
        .group_by(["domain", "alpha"])
        .agg(pl.col("mismatch").sum().alias("lenient_vs_dropl5_mismatch"))
    )
    mismatch_idx = {
        (row["domain"], row["alpha"]): int(row["lenient_vs_dropl5_mismatch"])
        for row in per_draw.iter_rows(named=True)
    }
    lenient_idx = {(row["domain"], row["alpha"]): row for row in lenient_mde}
    tau0_verdict_idx = exp006_tau0_verdict_mismatch(draws)

    tau0 = pl.read_csv(EXP006_MDE).filter(pl.col("multiplier") == TAU0_MULTIPLIER)
    rows: list[dict[str, Any]] = []
    equivalence_pass = True
    for record in tau0.sort(["domain", "alpha"]).iter_rows(named=True):
        key = (record["domain"], float(record["alpha"]))
        lenient_row = lenient_idx.get(key)
        lenient_mde_bps = lenient_row["mde_bps"] if lenient_row else math.nan
        tau0_mde_bps = record["mde_bps"]
        mde_match = _mde_equal(lenient_mde_bps, tau0_mde_bps)
        draw_mismatch = mismatch_idx.get(key, -1)
        draws_match = draw_mismatch == 0
        tau0_draw_mismatch, tau0_unmatched = tau0_verdict_idx.get(key, (-1, -1))
        tau0_draws_match = tau0_draw_mismatch == 0 and tau0_unmatched == 0
        equivalence_pass = equivalence_pass and draws_match and tau0_draws_match and mde_match
        rows.append(
            {
                "domain": record["domain"],
                "alpha": float(record["alpha"]),
                "lenient_vs_dropl5_mismatch": draw_mismatch,
                "lenient_vs_exp006_tau0_mismatch": tau0_draw_mismatch,
                "lenient_vs_exp006_tau0_unmatched": tau0_unmatched,
                "lenient_mde_bps": lenient_mde_bps,
                "exp006_tau0_mde_bps": tau0_mde_bps if tau0_mde_bps is not None else math.nan,
                "lenient_eq_tau0_mde": bool(mde_match),
                "draws_match_dropl5": bool(draws_match),
                "draws_match_exp006_tau0": bool(tau0_draws_match),
            }
        )
    return rows, bool(equivalence_pass)


def _mde_equal(value: float, reference: Any) -> bool:
    """True when two (possibly NaN/None) MDE values agree within tolerance."""
    if reference is None:
        return isinstance(value, float) and math.isnan(value)
    if isinstance(value, float) and math.isnan(value):
        return False
    return math.isclose(float(value), float(reference), rel_tol=0.0, abs_tol=MDE_MATCH_TOL)


def submaterial_accounting(draws: pl.DataFrame) -> list[dict[str, Any]]:
    """Economically sub-material pass rate among lenient positive passes.

    A lenient pass is sub-material when ``effect_bps < materiality_bps(domain)``
    (net-of-cost point estimate below the frozen materiality buffer). Rates are
    reported per (domain, alpha, edge_bps); zero lenient passes give NaN, never 0.

    Returns
    -------
    list[dict[str, Any]]
        Per (domain, alpha, edge_bps) lenient-pass and sub-material counts/rate.
    """
    positives = draws.filter(pl.col("scenario") == "positive")
    # Full positive (domain, alpha, edge_bps) grid so zero-lenient-pass cells are
    # emitted with lenient_pass_count=0 and submaterial_rate=NaN rather than dropped
    # (a missing row must not be mistaken for missing data on edge grids / reruns).
    grid = positives.select(["domain", "alpha", "edge_bps"]).unique()
    pass_counts = (
        positives.filter(pl.col("passed_lenient"))
        .with_columns((pl.col("effect_bps") < pl.col("materiality_bps")).alias("submaterial"))
        .group_by(["domain", "alpha", "edge_bps"])
        .agg(
            pl.len().alias("lenient_pass_count"),
            pl.col("submaterial").sum().alias("submaterial_count"),
        )
    )
    grouped = (
        grid.join(pass_counts, on=["domain", "alpha", "edge_bps"], how="left")
        .with_columns(
            pl.col("lenient_pass_count").fill_null(0),
            pl.col("submaterial_count").fill_null(0),
        )
        .sort(["domain", "alpha", "edge_bps"])
    )
    rows: list[dict[str, Any]] = []
    for record in grouped.iter_rows(named=True):
        passes = int(record["lenient_pass_count"])
        sub = int(record["submaterial_count"])
        rows.append(
            {
                "domain": record["domain"],
                "alpha": float(record["alpha"]),
                "edge_bps": float(record["edge_bps"]),
                "lenient_pass_count": passes,
                "submaterial_count": sub,
                "submaterial_rate": sub / passes if passes else math.nan,
            }
        )
    return rows


def best_acceptable_frontier_mde() -> dict[tuple[Any, float], float]:
    """Min finite MDE per (domain, alpha) among EXP-006 thresholds with controlled FPR.

    Uses the EXP-006 ``status == "PASS"`` rows, which already encode FPR control,
    FPR precision, and a finite MDE.
    """
    frontier = pl.read_csv(EXP006_MDE).filter(pl.col("status") == "PASS")
    out: dict[tuple[Any, float], float] = {}
    for record in frontier.iter_rows(named=True):
        key = (record["domain"], float(record["alpha"]))
        mde = float(record["mde_bps"])
        if key not in out or mde < out[key]:
            out[key] = mde
    return out


def build_lenient_vs_frontier(
    lenient_fpr: list[dict[str, Any]],
    lenient_mde: list[dict[str, Any]],
    strict_mde: list[dict[str, Any]],
    submaterial_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Assemble the per (domain, alpha) lenient-vs-frontier verdict rows.

    Records the lenient MDE/FPR, the strict-gate MDE, the best acceptable EXP-006
    frontier MDE, the EXP-006 tau=0 MDE, the sub-material rate at the lenient MDE,
    and the predeclared H-lenient verdict.
    """
    fpr_idx = {(row["domain"], row["alpha"]): row for row in lenient_fpr}
    strict_idx = {(row["domain"], row["alpha"]): row for row in strict_mde}
    sub_idx = {
        (row["domain"], row["alpha"], row["edge_bps"]): row["submaterial_rate"]
        for row in submaterial_rows
    }
    frontier_best = best_acceptable_frontier_mde()
    tau0_mde = {
        (row["domain"], float(row["alpha"])): (
            float(row["mde_bps"]) if row["mde_bps"] is not None else math.nan
        )
        for row in pl.read_csv(EXP006_MDE)
        .filter(pl.col("multiplier") == TAU0_MULTIPLIER)
        .iter_rows(named=True)
    }

    rows: list[dict[str, Any]] = []
    for lenient_row in sorted(lenient_mde, key=lambda r: (str(r["domain"]), float(r["alpha"]))):
        domain = lenient_row["domain"]
        alpha = float(lenient_row["alpha"])
        key = (domain, alpha)
        lenient_mde_bps = lenient_row["mde_bps"]
        fpr_row = fpr_idx.get(key)
        lenient_fpr_value = fpr_row["fpr"] if fpr_row else math.nan
        lenient_fpr_hw = fpr_row["wilson_half_width"] if fpr_row else math.nan
        fpr_precise = bool(fpr_row) and lenient_fpr_hw <= FPR_HALF_WIDTH_TARGET
        fpr_controlled = bool(fpr_row) and lenient_fpr_value <= alpha

        strict_mde_bps = strict_idx[key]["mde_bps"] if key in strict_idx else math.nan
        best_frontier = frontier_best.get(key, math.nan)
        tau0 = tau0_mde.get(key, math.nan)
        sub_rate = sub_idx.get((domain, alpha, lenient_mde_bps), math.nan)

        mde_finite = isinstance(lenient_mde_bps, float) and math.isfinite(lenient_mde_bps)
        equals_tau0 = _mde_equal(lenient_mde_bps, tau0)
        improves_frontier = bool(
            mde_finite
            and math.isfinite(best_frontier)
            and lenient_mde_bps < best_frontier - MDE_MATCH_TOL
            and fpr_controlled
            and fpr_precise
        )
        verdict = _lenient_verdict(
            fpr_controlled, fpr_precise, mde_finite, sub_rate, improves_frontier
        )
        rows.append(
            {
                "domain": domain,
                "alpha": alpha,
                "lenient_mde_bps": lenient_mde_bps,
                "lenient_fpr": lenient_fpr_value,
                "lenient_fpr_wilson_half_width": lenient_fpr_hw,
                "strict_mde_bps": strict_mde_bps,
                "best_acceptable_frontier_mde_bps": best_frontier,
                "exp006_tau0_mde_bps": tau0,
                "submaterial_rate_at_lenient_mde": sub_rate,
                "lenient_eq_tau0_mde": bool(equals_tau0),
                "improves_beyond_frontier": improves_frontier,
                "verdict": verdict,
            }
        )
    return rows


def _lenient_verdict(
    fpr_controlled: bool,
    fpr_precise: bool,
    mde_finite: bool,
    sub_rate: float,
    improves_frontier: bool,
) -> str:
    """Predeclared H-lenient verdict for one (domain, alpha) cell (see scope)."""
    if not fpr_controlled:
        return "EVIDENCE_AGAINST_FPR"
    if not fpr_precise:
        return "INCONCLUSIVE_FPR_PRECISION"
    if not mde_finite:
        return "EVIDENCE_AGAINST_NO_MDE"
    sub_known = isinstance(sub_rate, float) and math.isfinite(sub_rate)
    if sub_known and sub_rate > SUBMATERIAL_LIMIT:
        return "EVIDENCE_AGAINST_SUBMATERIAL"
    if improves_frontier:
        return "EVIDENCE_FOR"
    return "EVIDENCE_AGAINST_NO_STRUCTURAL_GAIN"


# --------------------------------------------------------------------------- #
# Plotting (bounded summary inputs only)
# --------------------------------------------------------------------------- #
def plot_mde_comparison(frontier_rows: list[dict[str, Any]]) -> None:
    """Grouped bars by domain at alpha0: strict gate, best frontier, lenient L5."""
    pdf = pl.DataFrame(frontier_rows).filter(pl.col("alpha") == ALPHA0).to_pandas()
    domains = list(pdf["domain"])
    x = np.arange(len(domains))
    width = 0.27
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - width, pdf["strict_mde_bps"], width, label="strict gate (EXP-003)")
    ax.bar(x, pdf["best_acceptable_frontier_mde_bps"], width, label="best acceptable EXP-006")
    ax.bar(x + width, pdf["lenient_mde_bps"], width, label="lenient L5")
    ax.set_xticks(x, domains)
    ax.set_ylabel("Economic MDE (bps)")
    ax.set_title("Economic MDE by domain at alpha=0.05")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "mde_comparison.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_fpr_comparison(fpr_rows: list[dict[str, Any]]) -> None:
    """Grouped bars by domain at alpha0: strict vs lenient FPR against the alpha0 line."""
    pdf = pl.DataFrame(fpr_rows).filter(pl.col("alpha") == ALPHA0).to_pandas()
    pivot = pdf.pivot(index="domain", columns="variant", values="fpr").reset_index()
    domains = list(pivot["domain"])
    x = np.arange(len(domains))
    width = 0.35
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - width / 2, pivot["strict"], width, label="strict gate")
    ax.bar(x + width / 2, pivot["lenient"], width, label="lenient L5")
    ax.axhline(ALPHA0, color="red", linewidth=1, label="alpha0 = 0.05")
    ax.set_xticks(x, domains)
    ax.set_ylabel("FPR")
    ax.set_title("False-positive rate by domain at alpha=0.05")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "fpr_comparison.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_tpr_curves(tpr_rows: list[dict[str, Any]]) -> None:
    """Per-domain TPR vs planted edge at alpha0: strict vs lenient, with the 0.80 line."""
    pdf = pl.DataFrame(tpr_rows).filter(pl.col("alpha") == ALPHA0).to_pandas()
    domains = sorted(pdf["domain"].unique())
    fig, axes = plt.subplots(1, len(domains), figsize=(5 * len(domains), 5), sharey=True)
    axes = axes if len(domains) > 1 else [axes]
    for ax, domain in zip(axes, domains):
        sub = pdf[pdf["domain"] == domain]
        for variant, group in sub.groupby("variant"):
            group = group.sort_values("edge_bps")
            ax.plot(group["edge_bps"], group["tpr"], marker=".", label=str(variant))
        ax.axhline(POWER_TARGET, color="black", linewidth=1)
        ax.set_xscale("log")
        ax.set_xlabel("Planted edge (bps, log)")
        ax.set_title(str(domain))
    axes[0].set_ylabel("TPR")
    axes[-1].legend(fontsize=8, title="variant")
    fig.suptitle("TPR vs planted edge: strict vs lenient L5 at alpha=0.05")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "tpr_strict_vs_lenient.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_submaterial_heatmap(submaterial_rows: list[dict[str, Any]]) -> None:
    """Heatmap of sub-material pass rate among lenient passes by domain and edge at alpha0."""
    pdf = pl.DataFrame(submaterial_rows).filter(pl.col("alpha") == ALPHA0).to_pandas()
    domains = sorted(pdf["domain"].unique())
    edges = sorted(pdf["edge_bps"].unique())
    matrix = np.full((len(domains), len(edges)), np.nan)
    rate_idx = {(row["domain"], row["edge_bps"]): row["submaterial_rate"] for _, row in pdf.iterrows()}
    for r, domain in enumerate(domains):
        for c, edge in enumerate(edges):
            matrix[r, c] = rate_idx.get((domain, edge), np.nan)
    fig, ax = plt.subplots(figsize=(9, 4))
    im = ax.imshow(matrix, aspect="auto", cmap="OrRd", vmin=0.0, vmax=1.0)
    ax.set_xticks(range(len(edges)), [f"{edge:g}" for edge in edges])
    ax.set_yticks(range(len(domains)), domains)
    for r in range(len(domains)):
        for c in range(len(edges)):
            if np.isfinite(matrix[r, c]):
                ax.text(c, r, f"{matrix[r, c]:.2f}", ha="center", va="center", fontsize=6)
    ax.set_xlabel("Planted edge (bps)")
    ax.set_title("Economically sub-material rate among lenient passes (alpha=0.05)")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "submaterial_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run the EXP-007 lenient-L5 variant measurement and write results and plots."""
    configure_logging()
    ensure_output_dirs()
    dependency_status = require_dependencies()
    predeclaration = require_predeclaration_confirmation()

    draws = load_gate_draws()
    edge_grid = positive_edge_grid(draws)

    # Persist the auditable draw-level reconstruction (one row per EXP-003 gate-stack
    # draw) before any summary aggregation: keys + strict/lenient/drop-L5 pass flags,
    # the unchanged effect/CI, materiality, and the unchanged L1-L4 legs. Row count
    # equals the EXP-003 gate-stack subset (recorded as gate_draw_rows).
    draws.select(
        *DRAW_KEY_COLS,
        "passed",
        "passed_lenient",
        "passed_drop_l5",
        "effect_bps",
        "ci_lower_bps",
        "materiality_bps",
        "L1_readiness",
        "L2_integrity",
        "L3_outcome",
        "L4_stability",
    ).write_csv(RESULTS_DIR / "lenient_draw_verdicts.csv")

    lenient_fpr = summarize_fpr(draws, "passed_lenient", "lenient")
    strict_fpr = summarize_fpr(draws, "passed", "strict")
    lenient_tpr = summarize_tpr(draws, "passed_lenient", "lenient")
    strict_tpr = summarize_tpr(draws, "passed", "strict")
    lenient_mde = compute_variant_mde(lenient_fpr, lenient_tpr, edge_grid, "lenient")
    strict_mde = compute_variant_mde(strict_fpr, strict_tpr, edge_grid, "strict")

    equivalence_rows, equivalence_pass = structural_equivalence_check(draws, lenient_mde)
    submaterial_rows = submaterial_accounting(draws)
    frontier_rows = build_lenient_vs_frontier(
        lenient_fpr, lenient_mde, strict_mde, submaterial_rows
    )

    fpr_rows = strict_fpr + lenient_fpr
    tpr_rows = strict_tpr + lenient_tpr
    mde_rows = strict_mde + lenient_mde

    headline = {
        str(row["domain"]): str(row["verdict"])
        for row in frontier_rows
        if float(row["alpha"]) == ALPHA0
    }
    measurements_produced = bool(frontier_rows) and bool(lenient_mde) and bool(submaterial_rows)
    overall_status = (
        "COMPLETE" if measurements_produced and equivalence_pass else "INCONCLUSIVE"
    )

    write_rows(RESULTS_DIR / "lenient_fpr_summary.csv", fpr_rows)
    write_rows(RESULTS_DIR / "lenient_tpr_summary.csv", tpr_rows)
    write_rows(RESULTS_DIR / "lenient_mde_summary.csv", mde_rows)
    write_rows(RESULTS_DIR / "structural_equivalence_check.csv", equivalence_rows)
    write_rows(RESULTS_DIR / "submaterial_pass_rates.csv", submaterial_rows)
    write_rows(RESULTS_DIR / "lenient_vs_frontier.csv", frontier_rows)
    write_json(
        RESULTS_DIR / "run_metadata.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "overall_status": overall_status,
            "measurements_produced": measurements_produced,
            "structural_equivalence_pass": equivalence_pass,
            "dependencies": dependency_status,
            "predeclaration": predeclaration,
            "headline_verdict_at_alpha0": headline,
            "lenient_definition": "ci_lower_bps > 0.0",
            "submaterial_definition": "effect_bps < materiality_bps(domain)",
            "domain_materiality_bps": {
                str(domain): materiality_bps_for(domain)
                for domain in sorted({str(row["domain"]) for row in lenient_mde})
            },
            "alpha0": ALPHA0,
            "submaterial_limit": SUBMATERIAL_LIMIT,
            "power_target": POWER_TARGET,
            "fpr_half_width_target": FPR_HALF_WIDTH_TARGET,
            "tpr_half_width_target": TPR_HALF_WIDTH_TARGET,
            "gate_draw_rows": int(draws.height),
            "positive_edge_grid_bps": edge_grid,
        },
    )

    plot_mde_comparison(frontier_rows)
    plot_fpr_comparison(fpr_rows)
    plot_tpr_curves(tpr_rows)
    plot_submaterial_heatmap(submaterial_rows)

    LOGGER.info("EXP-007 complete: %s", overall_status)
    LOGGER.info("Structural equivalence (lenient == drop-L5 == EXP-006 tau=0): %s", equivalence_pass)
    LOGGER.info("Headline H-lenient verdict at alpha0: %s", headline)
    LOGGER.info("Results: %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
