"""
Experiment EXP-013: Incremental Substrate Validation (Track B P0 gate).

The EXP-001 analogue for incremental edges. Validates the model-free marginal
net-P&L estimator (``xen.incremental_referee``) before any incremental-referee
calibration is attempted: it must (i) recover a planted marginal edge ``m`` within
``max(0.5 bps, 15% of m)`` on the C-change denominator, and critically (ii) read
incremental edge approximately zero for the REDUNDANCY NULL -- R and C that share
latent structure (overlap) where C adds no marginal edge -- with no phantom
POSITIVE edge. The redundancy null is the binding Track B control.

Real-price discipline: every incremental edge is computed from real domain
``Close`` next-step returns; no synthetic chart prices are used. Only the first 70%
analysis slice is loaded; the final 30% global holdout is never touched.

Pre-execution confirmation gate: the checkpoint requires operator confirmation or
override of D-incr-form / D-incr-substrate / D-incr-legs before EXP-013 executes.
This script BLOCKS (produces no measurement) until a governance artifact records the
token ``PHASE003-TRACKB-PREDECLARATION-CONFIRMED``. Manual execution gate: do not run
inside the pipeline.
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
from tqdm.auto import tqdm

from xen.incremental_referee import (
    EPISODE_LENGTHS,
    build_rc_substrate,
    incremental_edge_ci,
    marginal_net_series,
)
from xen.referee_calibration import (
    DOMAIN_SPECS,
    EDGE_GRID_BPS,
    build_domain_frames,
    list_timebar_files,
    load_analysis_data,
    materiality_bps_for,
    next_log_returns_from_bars,
    percentile_ci,
    seed_for,
    write_json,
)

LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants & paths
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-013"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data"
EXPERIMENTS_DIR = PROJECT_ROOT / "python" / "experiments"
EXPERIMENT_DIR = EXPERIMENTS_DIR / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
GOVERNANCE_DIR = EXPERIMENT_DIR / "governance"
EXP001_META = EXPERIMENTS_DIR / "EXP-001" / "results" / "run_metadata.json"

# Pre-execution confirmation token (D-incr-form / -substrate / -legs). The Stage 4
# gate records this in a governance artifact before any Track B measurement.
PREDECLARATION_TOKEN = "PHASE003-TRACKB-PREDECLARATION-CONFIRMED"

DOMAINS: tuple[str, ...] = ("5m", "1h", "4h")
POSITIVE_EDGES: tuple[float, ...] = tuple(e for e in EDGE_GRID_BPS if e > 0.0)
POSITIVE_DRAWS_PER_EDGE = 100
REDUNDANCY_DRAWS = 100
BOOTSTRAP_RESAMPLES = 1000
ALPHA = 0.05


def recovery_tolerance(edge_bps: float) -> float:
    """Planted-edge recovery tolerance ``max(0.5, 15% of m)`` (EXP-001 family)."""
    return max(0.5, 0.15 * float(edge_bps))


def null_tolerance(domain: str) -> float:
    """Redundancy-null point tolerance ``max(0.5, 15% of materiality)``."""
    return max(0.5, 0.15 * materiality_bps_for(domain))


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
# Step 1: governance freeze + dependency gate
# --------------------------------------------------------------------------- #
def find_predeclaration_token() -> dict[str, Any]:
    """Search the governance dir for the Track B predeclaration-confirmation token.

    The Stage 4 gate records the token in a dated governance artifact before any
    Track B measurement is produced. Returns the token status and the file that
    carries it (if any).
    """
    confirmed = False
    source: str | None = None
    if GOVERNANCE_DIR.exists():
        for path in sorted(GOVERNANCE_DIR.glob("*.md")):
            if PREDECLARATION_TOKEN in path.read_text(encoding="utf-8"):
                confirmed = True
                source = path.name
                break
    return {"token": PREDECLARATION_TOKEN, "confirmed": confirmed, "source": source}


def require_exp001_pass() -> str:
    """Fail fast unless EXP-001 recorded an overall PASS substrate status."""
    if not EXP001_META.exists():
        raise FileNotFoundError(f"EXP-001 metadata not found: {EXP001_META}")
    meta = json.loads(EXP001_META.read_text(encoding="utf-8"))
    if meta.get("overall_status") != "PASS":
        raise RuntimeError(f"EXP-001 did not PASS: {meta.get('overall_status')}")
    return str(meta.get("overall_status"))


def write_blocked_metadata(token_status: dict[str, Any]) -> None:
    """Record a BLOCKED run (predeclaration token absent) without any measurement."""
    write_json(
        RESULTS_DIR / "run_metadata.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "overall_status": "BLOCKED",
            "measurements_produced": False,
            "reason": (
                f"Track B predeclaration gate not satisfied: token "
                f"{PREDECLARATION_TOKEN!r} not found in {GOVERNANCE_DIR}. Record the "
                f"Stage 4 confirmation/amendment before producing any measurement."
            ),
            "predeclaration_gate": token_status,
        },
    )


# --------------------------------------------------------------------------- #
# Step 2-3: positive planted-edge recovery
# --------------------------------------------------------------------------- #
def positive_recovery_rows(
    *, instrument: str, domain: str, returns: np.ndarray
) -> list[dict[str, Any]]:
    """Across-draw recovery of each planted marginal edge on the C-change denominator.

    For each planted edge ``m`` the per-draw incremental edge is the mean net
    marginal P&L over the denominator; the across-draw mean is compared to ``m`` with
    the ``max(0.5, 15% of m)`` tolerance (EXP-001 family). Recovery FAIL is genuine
    substrate breakage.
    """
    rows: list[dict[str, Any]] = []
    for edge_bps in POSITIVE_EDGES:
        per_draw: list[float] = []
        denom_counts: list[int] = []
        for draw in range(POSITIVE_DRAWS_PER_EDGE):
            seed = seed_for(EXPERIMENT_ID, instrument, domain, "positive", edge_bps, draw)
            sub = build_rc_substrate(
                returns, domain=domain, instrument=instrument, seed=seed, planted_edge_bps=float(edge_bps)
            )
            marginal = marginal_net_series(
                sub.scoped_returns, sub.r_positions, sub.c_positions,
                cost_bps=sub.cost_bps, episode_length=sub.episode_length,
            )
            series = marginal["net_denominator"]
            if len(series):
                per_draw.append(float(np.mean(series)))
                denom_counts.append(marginal["denominator_count"])
        ci = percentile_ci(per_draw, alpha=ALPHA)
        tol = recovery_tolerance(edge_bps)
        recovered = bool(math.isfinite(ci.mean) and abs(ci.mean - float(edge_bps)) <= tol)
        rows.append(
            {
                "instrument": instrument,
                "domain": domain,
                "planted_edge_bps": float(edge_bps),
                "recovered_edge_bps": ci.mean,
                "ci_lower_bps": ci.lower,
                "ci_upper_bps": ci.upper,
                "abs_recovery_error_bps": abs(ci.mean - float(edge_bps)) if math.isfinite(ci.mean) else math.nan,
                "tolerance_bps": tol,
                "mean_denominator_count": float(np.mean(denom_counts)) if denom_counts else math.nan,
                "n_draws": ci.n,
                "status": "PASS" if recovered else "FAIL",
            }
        )
    return rows


# --------------------------------------------------------------------------- #
# Step 4: redundancy-null check
# --------------------------------------------------------------------------- #
def redundancy_null_rows(
    *, instrument: str, domain: str, returns: np.ndarray
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Redundancy-null incremental edge, verdicted on the ACROSS-DRAW distribution.

    Adversarial-review F01: the binding Track B control ("R and C share structure but
    C adds no marginal edge -> incremental edge ~ 0, no phantom POSITIVE edge") was
    previously verdicted on a SINGLE canonical draw's block-bootstrap CI. In
    cost-dominated / low-N cells (notably 4h and BTCUSD/1h) that single-draw CI is far
    too wide to detect a materiality-sized phantom edge, so the cell passed the binding
    control only because the test had no power -- and several single-draw point
    estimates landed materially POSITIVE purely from one-draw noise.

    The verdict now uses the across-draw distribution of the per-draw incremental
    reading (REDUNDANCY_DRAWS draws), whose percentile CI is far tighter and is the
    sampling distribution of the estimator under the redundancy construction:

    - ``PHANTOM_EDGE``: across-draw CI is entirely positive AND the point breaches the
      null tolerance -> a real shared-structure false edge (binding failure).
    - ``UNDER_POWERED``: the across-draw CI half-width is >= materiality, so the test
      cannot rule out a materiality-sized phantom -> reported as such, never counted as
      a clean pass (the honest "absence of evidence != evidence of absence" case).
    - ``PASS``: point within the null tolerance and CI lower bound <= 0, with the CI
      tight enough to have detected a phantom (clean zero).
    - ``NULL_COST_DOMINATED``: a powered, negative cost-drag reading beyond the tight
      band with no phantom positive (expected ~ -cost_bps/episode_length; not a failure).

    The single canonical draw's block-bootstrap CI (now with an autocorrelation-aware
    block length, F04) is retained as a DIAGNOSTIC only.
    """
    per_draw: list[float] = []
    for draw in range(REDUNDANCY_DRAWS):
        seed = seed_for(EXPERIMENT_ID, instrument, domain, "redundancy", draw)
        sub = build_rc_substrate(
            returns, domain=domain, instrument=instrument, seed=seed, planted_edge_bps=0.0
        )
        marginal = marginal_net_series(
            sub.scoped_returns, sub.r_positions, sub.c_positions,
            cost_bps=sub.cost_bps, episode_length=sub.episode_length,
        )
        series = marginal["net_denominator"]
        if len(series):
            per_draw.append(float(np.mean(series)))
    across_ci = percentile_ci(per_draw, alpha=ALPHA)

    # Canonical redundancy draw -> single-draw block-bootstrap CI, kept as a diagnostic
    # only. The block length is estimated on the contiguous full-length marginal series
    # (``net_full``) so within-episode autocorrelation is captured (F04).
    canonical_seed = seed_for(EXPERIMENT_ID, instrument, domain, "redundancy", 0)
    canonical = build_rc_substrate(
        returns, domain=domain, instrument=instrument, seed=canonical_seed, planted_edge_bps=0.0
    )
    canonical_marginal = marginal_net_series(
        canonical.scoped_returns, canonical.r_positions, canonical.c_positions,
        cost_bps=canonical.cost_bps, episode_length=canonical.episode_length,
    )
    boot_ci, block_length = incremental_edge_ci(
        canonical_marginal["net_denominator"],
        alpha=ALPHA,
        n_bootstrap=BOOTSTRAP_RESAMPLES,
        seed=seed_for(EXPERIMENT_ID, instrument, domain, "redundancy_boot"),
        block_series=canonical_marginal["net_full"],
    )

    materiality = materiality_bps_for(domain)
    tol = null_tolerance(domain)
    point = across_ci.mean
    across_hw = (
        (across_ci.upper - across_ci.lower) / 2.0
        if math.isfinite(across_ci.lower) and math.isfinite(across_ci.upper)
        else math.nan
    )
    phantom = bool(
        math.isfinite(across_ci.lower) and across_ci.lower > 0.0
        and math.isfinite(point) and point > tol
    )
    underpowered = (not math.isfinite(across_hw)) or across_hw >= materiality
    clean_zero = bool(
        math.isfinite(point) and abs(point) <= tol
        and math.isfinite(across_ci.lower) and across_ci.lower <= 0.0
    )
    if phantom:
        status = "PHANTOM_EDGE"
    elif underpowered:
        # CI too wide to exclude a materiality-sized phantom -> honest non-pass.
        status = "UNDER_POWERED"
    elif clean_zero:
        status = "PASS"
    else:
        # Powered negative cost drag beyond the tight band, no phantom positive ->
        # reported, not a substrate failure (binding control = no phantom POSITIVE edge).
        status = "NULL_COST_DOMINATED"

    summary = [
        {
            "instrument": instrument,
            "domain": domain,
            "across_draw_mean_bps": across_ci.mean,
            "across_draw_ci_lower_bps": across_ci.lower,
            "across_draw_ci_upper_bps": across_ci.upper,
            "across_draw_half_width_bps": across_hw,
            "boot_incremental_edge_bps": boot_ci.mean,
            "boot_ci_lower_bps": boot_ci.lower,
            "boot_ci_upper_bps": boot_ci.upper,
            "block_length": block_length,
            "expected_cost_drag_bps": -canonical_marginal["per_bar_cost_bps"],
            "materiality_bps": materiality,
            "null_tolerance_bps": tol,
            "n_draws": across_ci.n,
            "status": status,
        }
    ]
    return summary, []


# --------------------------------------------------------------------------- #
# Step 5: substrate integrity summary
# --------------------------------------------------------------------------- #
def integrity_rows(*, instrument: str, domain: str, returns: np.ndarray) -> dict[str, Any]:
    """Descriptive substrate-mechanics check on one cell (masks, denominator, cost)."""
    seed = seed_for(EXPERIMENT_ID, instrument, domain, "integrity")
    sub = build_rc_substrate(
        returns, domain=domain, instrument=instrument, seed=seed, planted_edge_bps=0.0
    )
    marginal = marginal_net_series(
        sub.scoped_returns, sub.r_positions, sub.c_positions,
        cost_bps=sub.cost_bps, episode_length=sub.episode_length,
    )
    n = len(returns)
    return {
        "instrument": instrument,
        "domain": domain,
        "return_rows": n,
        "episode_length": sub.episode_length,
        "frac_R_only": sub.mask_fractions["R_only"],
        "frac_C_change": sub.mask_fractions["C_change"],
        "frac_overlap": sub.mask_fractions["overlap"],
        "frac_inactive": sub.mask_fractions["inactive"],
        "denominator_count": marginal["denominator_count"],
        "denominator_fraction": marginal["denominator_count"] / n if n else math.nan,
        "per_bar_cost_bps": marginal["per_bar_cost_bps"],
        "cost_bps": sub.cost_bps,
        "gross_marginal_mean_bps": float(np.mean(marginal["gross_denominator"]))
        if len(marginal["gross_denominator"]) else math.nan,
        "net_marginal_mean_bps": float(np.mean(marginal["net_denominator"]))
        if len(marginal["net_denominator"]) else math.nan,
    }


# --------------------------------------------------------------------------- #
# Plotting (bounded summary inputs only)
# --------------------------------------------------------------------------- #
def plot_recovery(recovery: list[dict[str, Any]]) -> None:
    """Plot 1 -- recovered vs planted marginal edge by domain (identity reference)."""
    pdf = pl.DataFrame(recovery).to_pandas()
    fig, ax = plt.subplots(figsize=(8, 5))
    for domain, group in pdf.groupby("domain"):
        group = group.sort_values("planted_edge_bps")
        ax.plot(group["planted_edge_bps"], group["recovered_edge_bps"], marker="o", label=str(domain))
    lims = [0, max(POSITIVE_EDGES)]
    ax.plot(lims, lims, color="black", linewidth=1, label="identity")
    ax.set_xlabel("Planted marginal edge (bps)")
    ax.set_ylabel("Recovered marginal edge (bps)")
    ax.set_title("EXP-013 Plot 1 -- marginal-edge recovery by domain")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "marginal_recovery.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_recovery_error(recovery: list[dict[str, Any]]) -> None:
    """Plot 2 -- absolute recovery error vs tolerance band by domain."""
    pdf = pl.DataFrame(recovery).to_pandas()
    fig, ax = plt.subplots(figsize=(8, 5))
    for domain, group in pdf.groupby("domain"):
        group = group.sort_values("planted_edge_bps")
        ax.plot(group["planted_edge_bps"], group["abs_recovery_error_bps"], marker="o", label=f"{domain} error")
    grid = sorted(POSITIVE_EDGES)
    ax.plot(grid, [recovery_tolerance(e) for e in grid], color="red", linestyle="--", label="tolerance")
    ax.set_xlabel("Planted marginal edge (bps)")
    ax.set_ylabel("Absolute recovery error (bps)")
    ax.set_title("EXP-013 Plot 2 -- recovery error vs tolerance")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "recovery_error.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_redundancy(redundancy: list[dict[str, Any]]) -> None:
    """Plot 3 -- redundancy-null ACROSS-DRAW intervals (verdict basis) vs materiality.

    Plots the across-draw incremental-edge interval -- the actual verdict basis after
    adversarial-review F01 -- with markers coloured by status so under-powered cells
    (CI half-width >= materiality) are visually distinct from clean passes.
    """
    pdf = pl.DataFrame(redundancy).to_pandas()
    labels = pdf["instrument"] + " " + pdf["domain"]
    status_color = {
        "PASS": "seagreen",
        "NULL_COST_DOMINATED": "slategrey",
        "UNDER_POWERED": "darkorange",
        "PHANTOM_EDGE": "firebrick",
    }
    colors = [status_color.get(s, "black") for s in pdf["status"]]
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(pdf))
    ax.errorbar(
        x,
        pdf["across_draw_mean_bps"],
        yerr=[
            pdf["across_draw_mean_bps"] - pdf["across_draw_ci_lower_bps"],
            pdf["across_draw_ci_upper_bps"] - pdf["across_draw_mean_bps"],
        ],
        fmt="none", ecolor="lightgrey", capsize=3, zorder=1,
    )
    ax.scatter(x, pdf["across_draw_mean_bps"], c=colors, zorder=2, s=25)
    ax.axhline(0.0, color="black", linewidth=1)
    for xi, mat in enumerate(pdf["materiality_bps"]):
        ax.hlines(mat, xi - 0.3, xi + 0.3, color="red", linewidth=1)
    handles = [
        plt.Line2D([0], [0], marker="o", linestyle="", color=c, label=s)
        for s, c in status_color.items()
    ]
    ax.legend(handles=handles, fontsize=7, title="status")
    ax.set_xticks(x, labels, rotation=90, fontsize=6)
    ax.set_ylabel("Redundancy-null incremental edge (bps, across-draw)")
    ax.set_title("EXP-013 Plot 3 -- redundancy null across-draw CI (red = materiality; orange = under-powered)")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "redundancy_null.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_integrity(integrity: list[dict[str, Any]]) -> None:
    """Plot 4 -- denominator fraction and incremental turnover/cost by cell."""
    pdf = pl.DataFrame(integrity).to_pandas()
    labels = pdf["instrument"] + " " + pdf["domain"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    axes[0].bar(range(len(pdf)), pdf["denominator_fraction"], color="steelblue")
    axes[0].axhline(0.25, color="red", linewidth=1, label="target 0.25")
    axes[0].set_xticks(range(len(pdf)), labels, rotation=90, fontsize=6)
    axes[0].set_ylabel("C-change denominator fraction")
    axes[0].set_title("Denominator fraction by cell")
    axes[0].legend()
    axes[1].bar(range(len(pdf)), pdf["per_bar_cost_bps"], color="darkorange")
    axes[1].set_xticks(range(len(pdf)), labels, rotation=90, fontsize=6)
    axes[1].set_ylabel("Amortised incremental cost (bps/denominator bar)")
    axes[1].set_title("Incremental cost drag by cell")
    fig.suptitle("EXP-013 Plot 4 -- substrate integrity")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "substrate_integrity.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def build_substrate_manifest(exp001_status: str, token_status: dict[str, Any]) -> dict[str, Any]:
    """Record the frozen substrate construction parameters (Step 1 manifest)."""
    return {
        "predeclaration_gate": token_status,
        "exp001_status": exp001_status,
        "estimator": "model_free_marginal_net_pnl",
        "position_bound": 1.0,
        "episode_lengths": EPISODE_LENGTHS,
        "masks": ["R_only", "C_change", "overlap", "inactive"],
        "mask_target_fraction": 0.25,
        "denominator": "bars where combined position differs from R-alone (m != 0)",
        "incremental_cost_model": "amortised per-episode round-trip = cost_bps / episode_length",
        "positive_edges_bps": list(POSITIVE_EDGES),
        "positive_draws_per_edge": POSITIVE_DRAWS_PER_EDGE,
        "redundancy_draws": REDUNDANCY_DRAWS,
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "alpha": ALPHA,
    }


def main() -> None:
    """Run the EXP-013 incremental substrate validation and write outputs."""
    configure_logging()
    ensure_output_dirs()

    # Step 1: governance freeze gate. Without the predeclaration token, BLOCK and
    # produce no measurement (the run is blocked, not inconclusive).
    token_status = find_predeclaration_token()
    if not token_status["confirmed"]:
        write_blocked_metadata(token_status)
        LOGGER.warning(
            "EXP-013 BLOCKED: predeclaration token %r not found under %s. "
            "Record the Stage 4 Track B confirmation before running.",
            PREDECLARATION_TOKEN, GOVERNANCE_DIR,
        )
        return
    exp001_status = require_exp001_pass()

    files = list_timebar_files(DATA_DIR)
    if not files:
        raise FileNotFoundError(f"No time-bar files found under {DATA_DIR / 'timebars'}")

    recovery: list[dict[str, Any]] = []
    redundancy: list[dict[str, Any]] = []
    integrity: list[dict[str, Any]] = []
    analysis_rows: list[dict[str, Any]] = []
    underpowered: list[dict[str, Any]] = []

    for path in tqdm(files, desc="EXP-013 instruments"):
        data = load_analysis_data(path)
        analysis_rows.append(
            {
                "instrument": data.instrument,
                "source_file": data.source_file,
                "total_rows": data.total_rows,
                "analysis_rows": data.analysis_rows,
                "analysis_start": data.analysis_start,
                "analysis_end": data.analysis_end,
            }
        )
        for domain, frame in build_domain_frames(data.frame).items():
            returns, _ = next_log_returns_from_bars(frame)
            if len(returns) < DOMAIN_SPECS[domain].min_effective_n:
                underpowered.append(
                    {
                        "instrument": data.instrument,
                        "domain": domain,
                        "return_rows": len(returns),
                        "min_effective_n": DOMAIN_SPECS[domain].min_effective_n,
                        "reason": "insufficient_returns_for_substrate",
                    }
                )
                continue
            recovery.extend(positive_recovery_rows(instrument=data.instrument, domain=domain, returns=returns))
            red_rows, _ = redundancy_null_rows(instrument=data.instrument, domain=domain, returns=returns)
            redundancy.extend(red_rows)
            integrity.append(integrity_rows(instrument=data.instrument, domain=domain, returns=returns))

    # Verdict: substrate validated iff every positive cell recovers (no FAIL) and no
    # redundancy cell shows phantom edge, AND the binding redundancy control is
    # POWERED in at least one cell (adversarial-review F01). Cost-dominated and
    # under-powered redundancy cells are reported but do not break the substrate
    # (binding control = no phantom positive). If EVERY redundancy cell is
    # under-powered the binding control was never actually exercised -> INCONCLUSIVE.
    recovery_fail = any(r["status"] == "FAIL" for r in recovery)
    phantom = any(r["status"] == "PHANTOM_EDGE" for r in redundancy)
    powered_null_cells = [r for r in redundancy if r["status"] in ("PASS", "NULL_COST_DOMINATED")]
    underpowered_null_cells = [r for r in redundancy if r["status"] == "UNDER_POWERED"]
    if recovery_fail or phantom:
        overall_status = "FAIL"
    elif not recovery or not redundancy:
        overall_status = "INCONCLUSIVE"
    elif not powered_null_cells:
        # Binding control never had power in any cell -> not a validated substrate.
        overall_status = "INCONCLUSIVE"
    else:
        overall_status = "PASS"

    write_rows(RESULTS_DIR / "analysis_metadata.csv", analysis_rows)
    write_rows(RESULTS_DIR / "positive_recovery.csv", recovery)
    write_rows(RESULTS_DIR / "redundancy_null.csv", redundancy)
    write_rows(RESULTS_DIR / "substrate_integrity.csv", integrity)
    if underpowered:
        write_rows(RESULTS_DIR / "underpowered_cells.csv", underpowered)
    write_json(
        RESULTS_DIR / "run_metadata.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "overall_status": overall_status,
            "measurements_produced": True,
            "recovery_fail": recovery_fail,
            "phantom_edge": phantom,
            "powered_null_cells": len(powered_null_cells),
            "cost_dominated_null_cells": [
                f"{r['instrument']}/{r['domain']}" for r in redundancy if r["status"] == "NULL_COST_DOMINATED"
            ],
            "underpowered_null_cells": [
                f"{r['instrument']}/{r['domain']}" for r in underpowered_null_cells
            ],
            "redundancy_verdict_basis": "across_draw_distribution",
            "insufficient_return_cells": len(underpowered),
            "substrate_manifest": build_substrate_manifest(exp001_status, token_status),
        },
    )

    plot_recovery(recovery)
    plot_recovery_error(recovery)
    plot_redundancy(redundancy)
    plot_integrity(integrity)

    LOGGER.info("EXP-013 complete: %s", overall_status)
    LOGGER.info("Results: %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
