"""
Experiment EXP-005: Near-MDE Realistic-Candidate Detection Anchor (keystone).

Phase 002 spine. Measures whether the frozen Phase 001 5-check gate stack detects
a predeclared imperfect realistic candidate that carries a known expected net edge
near each domain's EXP-003 gate MDE. Reuses the frozen ``xen.referee_calibration``
harness unchanged; the realistic-candidate construction lives in the sibling
experiment-local ``candidate`` module. Never loads the final 30% global holdout.
"""
from __future__ import annotations

import json
import logging
import math
import multiprocessing as mp
import os
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from tqdm.auto import tqdm

from xen.referee_calibration import (
    ALPHA_GRID,
    build_domain_frames,
    cost_bps_for,
    domain_split_index,
    evaluate_referees,
    list_timebar_files,
    load_analysis_data,
    materiality_bps_for,
    next_log_returns_from_bars,
    permuted_returns,
    plant_positive_edge,
    random_state_positions,
    seed_for,
    verdict_rate_rows,
    write_json,
)

# Experiment-local helper. The script directory is sys.path[0] for a direct run;
# inserting it explicitly also makes the import resolve in spawned mp workers,
# which re-import this module by path. (xen is installed editable.)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from candidate import (  # noqa: E402  (local helper; needs script dir on path)
    calibrate_delta_bps,
    candidate_diagnostics,
    generate_realistic_candidate,
)


LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-005"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data"
EXPERIMENT_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
GOVERNANCE_DIR = EXPERIMENT_DIR / "governance"
PRE_EXEC_REVIEW = GOVERNANCE_DIR / "pre-execution-review.md"
EXP001_METADATA = (
    PROJECT_ROOT / "python" / "experiments" / "EXP-001" / "results" / "run_metadata.json"
)
EXP003_METADATA = (
    PROJECT_ROOT / "python" / "experiments" / "EXP-003" / "results" / "run_metadata.json"
)
EXP003_MDE = PROJECT_ROOT / "python" / "experiments" / "EXP-003" / "results" / "mde_summary.csv"

# Predeclared realistic-candidate construction (scope D-nearMDE). Fixed, not tuned.
P_ACTIVE = 0.80
Q_MATCH = 0.75
EDGE_MULTIPLIERS: tuple[float, ...] = (0.5, 1.0, 1.5, 2.0)
HEADLINE_MULTIPLIER = 1.0
NULL_GENERATORS: tuple[str, ...] = ("raw_returns", "bar_permutation")

NULL_DRAWS_PER_GENERATOR = 500
POSITIVE_DRAWS_PER_EDGE = 500
BOOTSTRAP_RESAMPLES = 1000

ALPHA0 = 0.05
POWER_TARGET = 0.80
FPR_HALF_WIDTH_TARGET = 0.03
TPR_HALF_WIDTH_TARGET = 0.05
ACTIVE_RATE_TARGET = 0.80
ACTIVE_RATE_TOL = 0.02
MATCH_RATE_TARGET = 0.75
MATCH_RATE_TOL = 0.02

# Token written into the Stage 4 pre-execution review once the operator confirms
# the Phase 002 predeclaration items (D-nearMDE / D-lenientL5 / D-loss). Required
# before any measurement is produced (scope "Pre-execution confirmation").
PREDECLARATION_TOKEN = "PHASE002-PREDECLARATION-CONFIRMED"

# Draws are embarrassingly parallel and fully seed-deterministic, so the worker
# count changes only scheduling, never any verdict. Override with EXP005_WORKERS.
N_WORKERS = max(1, int(os.environ.get("EXP005_WORKERS", os.cpu_count() or 1)))
TASK_CHUNKSIZE = 16

# Read-only per-cell state installed in each worker by ``_init_worker``.
_WORKER_CELLS: dict[tuple[str, str], dict[str, Any]] = {}


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
    """Fail fast unless EXP-001 PASSED and EXP-003 produced its MDE artifact.

    EXP-003 is a measurement run that records ``overall_status == "COMPLETE"``
    (never ``"PASS"``), so its gate is artifact-based, mirroring EXP-004.

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
    if not EXP003_MDE.exists():
        raise FileNotFoundError(f"EXP-003 MDE summary not found: {EXP003_MDE}")
    return {
        "exp001_status": str(exp001.get("overall_status")),
        "exp003_status": str(exp003.get("overall_status")),
    }


def require_predeclaration_confirmation() -> dict[str, str]:
    """Require the recorded operator confirmation of the Phase 002 freeze items.

    The Stage 4 pre-execution review must carry ``PREDECLARATION_TOKEN`` to show
    that D-nearMDE / D-lenientL5 / D-loss were confirmed (or amended pre-results)
    before any EXP-005 measurement is read. No measurement is produced otherwise.

    Returns
    -------
    dict[str, str]
        Confirmation provenance for ``run_metadata.json``.
    """
    if not PRE_EXEC_REVIEW.exists():
        raise FileNotFoundError(
            "Stage 4 pre-execution review missing; operator predeclaration "
            f"confirmation required before EXP-005 runs: {PRE_EXEC_REVIEW}"
        )
    text = PRE_EXEC_REVIEW.read_text(encoding="utf-8")
    if PREDECLARATION_TOKEN not in text:
        raise RuntimeError(
            f"Predeclaration token '{PREDECLARATION_TOKEN}' not found in "
            f"{PRE_EXEC_REVIEW}. Record operator confirmation of "
            "D-nearMDE / D-lenientL5 / D-loss before running."
        )
    return {"predeclaration_confirmed": "true", "confirmation_source": PRE_EXEC_REVIEW.name}


def load_gate_mde_map() -> dict[str, float]:
    """Load the EXP-003 gate-stack MDE per domain at the operating alpha.

    Returns
    -------
    dict[str, float]
        ``{domain: mde_bps}`` for ``referee=gate_stack`` at ``alpha=ALPHA0``;
        ``nan`` where the artifact records no finite MDE for a domain.
    """
    frame = pl.read_csv(EXP003_MDE).filter(
        (pl.col("referee") == "gate_stack") & (pl.col("alpha") == ALPHA0)
    )
    out: dict[str, float] = {}
    for row in frame.iter_rows(named=True):
        mde = row["mde_bps"]
        out[str(row["domain"])] = float(mde) if mde is not None else math.nan
    return out


# --------------------------------------------------------------------------- #
# Draw evaluation
# --------------------------------------------------------------------------- #
def _scoped_returns_and_states(
    task: tuple[str, str, str, str, float, float, int],
    returns: np.ndarray,
    cost_bps: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build the latent state, candidate, and scenario returns for one draw.

    Deterministic in the per-draw seeds, so the result is independent of which
    worker (or no worker) runs the task. Positive draws plant the closed-form
    latent-state drift; null draws leave returns unmodified or bar-permuted.

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray]
        ``(states, candidate, scoped_returns)``.
    """
    instrument, domain, scenario, generator, _multiplier, edge_bps, draw = task
    label = generator if scenario == "null" else "known_positive"
    state_seed = seed_for(EXPERIMENT_ID, instrument, domain, scenario, label, edge_bps, draw, "s")
    cand_seed = seed_for(EXPERIMENT_ID, instrument, domain, scenario, label, edge_bps, draw, "c")

    states = random_state_positions(len(returns), state_seed)
    candidate = generate_realistic_candidate(
        states, p_active=P_ACTIVE, q_match=Q_MATCH, seed=cand_seed
    )
    if scenario == "null":
        if generator == "bar_permutation":
            perm_seed = seed_for(EXPERIMENT_ID, instrument, domain, "null", generator, draw, "p")
            scoped_returns = permuted_returns(returns, perm_seed)
        else:
            scoped_returns = returns
    else:
        delta_bps = calibrate_delta_bps(
            float(edge_bps), cost_bps, p_active=P_ACTIVE, q_match=Q_MATCH
        )
        scoped_returns = plant_positive_edge(
            returns, states, net_edge_bps=delta_bps, cost_bps=0.0
        )
    return states, candidate, scoped_returns


def _evaluate_draw_task(
    task: tuple[str, str, str, str, float, float, int],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Evaluate both referees and the candidate diagnostics for a single draw.

    A task is
    ``(instrument, domain, scenario, generator, multiplier, edge_bps, draw)``.
    The state/candidate/returns are regenerated deterministically from the
    per-draw seeds, so the output is reproducible regardless of worker count.

    Returns
    -------
    tuple[list[dict[str, Any]], dict[str, Any]]
        ``(verdict_rows, sanity_row)`` for this draw.
    """
    instrument, domain, scenario, generator, multiplier, edge_bps, draw = task
    cell = _WORKER_CELLS[(instrument, domain)]
    returns = cell["returns"]
    split_index = cell["split_index"]
    cost_bps = cell["cost_bps"]

    states, candidate, scoped_returns = _scoped_returns_and_states(task, returns, cost_bps)
    ref_seed = seed_for(
        EXPERIMENT_ID, instrument, domain, scenario, generator, edge_bps, draw, "r"
    )
    labels = {
        "instrument": instrument,
        "domain": domain,
        "scenario": scenario,
        "generator": generator,
        "multiplier": multiplier,
        "edge_bps": edge_bps,
        "draw": draw,
    }
    rows: list[dict[str, Any]] = []
    for verdict in evaluate_referees(
        scoped_returns,
        candidate,
        instrument=instrument,
        domain=domain,
        alpha_values=ALPHA_GRID,
        n_bootstrap=BOOTSTRAP_RESAMPLES,
        seed=ref_seed,
        split_index=split_index,
    ):
        row = dict(labels)
        row.update(verdict)
        rows.append(row)

    sanity = dict(labels)
    sanity.update(
        candidate_diagnostics(
            states, candidate, scoped_returns, split_index=split_index, cost_bps=cost_bps
        )
    )
    return rows, sanity


def build_draw_tasks(
    instrument: str, domain: str, gate_mde: float
) -> list[tuple[str, str, str, str, float, float, int]]:
    """Enumerate every null and known-positive draw task for one cell."""
    tasks: list[tuple[str, str, str, str, float, float, int]] = []
    for generator in NULL_GENERATORS:
        for draw in range(NULL_DRAWS_PER_GENERATOR):
            tasks.append((instrument, domain, "null", generator, 0.0, 0.0, draw))
    for multiplier in EDGE_MULTIPLIERS:
        edge_bps = float(multiplier) * gate_mde
        for draw in range(POSITIVE_DRAWS_PER_EDGE):
            tasks.append(
                (instrument, domain, "positive", "known_positive",
                 float(multiplier), edge_bps, draw)
            )
    return tasks


def _init_worker(cells: dict[tuple[str, str], dict[str, Any]]) -> None:
    """Pool initializer: install the read-only per-cell state in this worker."""
    global _WORKER_CELLS
    _WORKER_CELLS = cells


def run_draw_tasks(
    tasks: list[tuple[str, str, str, str, float, float, int]],
    cell_data: dict[tuple[str, str], dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Evaluate all draw tasks, in parallel when ``N_WORKERS > 1``.

    Each task is a pure, seed-deterministic function of its tuple plus the
    read-only ``cell_data``, so collected rows are content-identical to a serial
    run regardless of worker count. The caller sorts rows into a canonical order.

    Returns
    -------
    tuple[list[dict[str, Any]], list[dict[str, Any]]]
        ``(verdict_rows, sanity_rows)``.
    """
    verdict_rows: list[dict[str, Any]] = []
    sanity_rows: list[dict[str, Any]] = []
    if N_WORKERS <= 1:
        _init_worker(cell_data)
        for task in tqdm(tasks, desc="EXP-005 draws (serial)"):
            rows, sanity = _evaluate_draw_task(task)
            verdict_rows.extend(rows)
            sanity_rows.append(sanity)
        return verdict_rows, sanity_rows

    with mp.Pool(
        processes=N_WORKERS, initializer=_init_worker, initargs=(cell_data,)
    ) as pool:
        for rows, sanity in tqdm(
            pool.imap_unordered(_evaluate_draw_task, tasks, chunksize=TASK_CHUNKSIZE),
            total=len(tasks),
            desc=f"EXP-005 draws (x{N_WORKERS})",
        ):
            verdict_rows.extend(rows)
            sanity_rows.append(sanity)
    return verdict_rows, sanity_rows


# --------------------------------------------------------------------------- #
# Summaries
# --------------------------------------------------------------------------- #
def summarize_rates(
    verdict_rows: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]
]:
    """Compute pooled and per-instrument FPR (nulls) and TPR (positives) rows."""
    null_rows = [row for row in verdict_rows if row["scenario"] == "null"]
    positive_rows = [row for row in verdict_rows if row["scenario"] == "positive"]
    fpr = verdict_rate_rows(null_rows, group_cols=["domain", "referee", "alpha"], rate_name="fpr")
    tpr = verdict_rate_rows(
        positive_rows,
        group_cols=["domain", "referee", "alpha", "multiplier", "edge_bps"],
        rate_name="tpr",
    )
    fpr_inst = verdict_rate_rows(
        null_rows, group_cols=["instrument", "domain", "referee", "alpha"], rate_name="fpr"
    )
    tpr_inst = verdict_rate_rows(
        positive_rows,
        group_cols=["instrument", "domain", "referee", "alpha", "multiplier", "edge_bps"],
        rate_name="tpr",
    )
    return fpr, tpr, fpr_inst, tpr_inst


def extract_effect_points_1x(verdict_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Bounded per-domain gate-stack effect points at the 1.0x MDE grid point.

    Returns only the plot-ready subset (gate stack, positive, alpha0, 1.0x) in a
    single pass over the in-memory verdict rows, so the plotting pass receives
    bounded inputs instead of the full draw set.

    Parameters
    ----------
    verdict_rows : list[dict[str, Any]]
        All referee verdict rows from the analysis pass.

    Returns
    -------
    dict[str, Any]
        ``{"points": {domain: [effect_bps, ...]}, "edges": {domain: target_bps}}``.
    """
    points: dict[str, list[float]] = {}
    edges: dict[str, float] = {}
    for row in verdict_rows:
        if (
            row["referee"] == "gate_stack"
            and row["scenario"] == "positive"
            and float(row["alpha"]) == ALPHA0
            and float(row["multiplier"]) == HEADLINE_MULTIPLIER
        ):
            domain = str(row["domain"])
            points.setdefault(domain, []).append(float(row["effect_bps"]))
            edges[domain] = float(row["edge_bps"])
    return {"points": points, "edges": edges}


def _detection_multiplier(tpr_rows_sorted: list[dict[str, Any]]) -> float:
    """Smallest multiplier whose TPR meets the power target with precision."""
    for row in tpr_rows_sorted:
        if row["tpr"] >= POWER_TARGET and row["wilson_half_width"] <= TPR_HALF_WIDTH_TARGET:
            return float(row["multiplier"])
    return math.nan


def _domain_status(
    fpr_row: dict[str, Any] | None, headline_tpr: dict[str, Any] | None
) -> str:
    """Classify a (domain[/instrument]) cell from its FPR and 1.0x-MDE TPR.

    Predeclared logic: FPR must be controlled (<= alpha0) with usable precision,
    then the headline (1.0x MDE) TPR decides DETECTED_FLOOR vs STRUCTURALLY_BLIND.
    """
    if fpr_row is None or headline_tpr is None:
        return "INCONCLUSIVE_MISSING"
    if fpr_row["wilson_half_width"] > FPR_HALF_WIDTH_TARGET:
        return "INCONCLUSIVE_FPR_PRECISION"
    if fpr_row["fpr"] > ALPHA0:
        return "EVIDENCE_AGAINST_FPR"
    if headline_tpr["wilson_half_width"] > TPR_HALF_WIDTH_TARGET:
        return "INCONCLUSIVE_TPR_PRECISION"
    if headline_tpr["tpr"] >= POWER_TARGET:
        return "DETECTED_FLOOR"
    return "STRUCTURALLY_BLIND"


def build_detection(
    fpr_rows: list[dict[str, Any]],
    tpr_rows: list[dict[str, Any]],
    mde_map: dict[str, float],
    *,
    id_cols: list[str],
) -> list[dict[str, Any]]:
    """Assemble gate-stack detection rows (one per cell x multiplier) at alpha0.

    Parameters
    ----------
    fpr_rows, tpr_rows : list[dict[str, Any]]
        Rate rows grouped by ``id_cols`` (+ referee/alpha[/multiplier/edge]).
    mde_map : dict[str, float]
        Domain gate MDE used to label rows.
    id_cols : list[str]
        ``["domain"]`` for pooled or ``["instrument", "domain"]`` per instrument.

    Returns
    -------
    list[dict[str, Any]]
        Detection rows with per-cell ``status`` and ``detection_multiplier``;
        per-instrument cells also carry an ``under_powered`` flag.
    """
    domain_pos = id_cols.index("domain")
    per_instrument = "instrument" in id_cols
    fpr_idx = {
        tuple(row[col] for col in id_cols): row
        for row in fpr_rows
        if row["referee"] == "gate_stack" and float(row["alpha"]) == ALPHA0
    }
    tpr_idx: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in tpr_rows:
        if row["referee"] == "gate_stack" and float(row["alpha"]) == ALPHA0:
            tpr_idx.setdefault(tuple(row[col] for col in id_cols), []).append(row)

    output: list[dict[str, Any]] = []
    for key in sorted(tpr_idx, key=lambda item: tuple(str(part) for part in item)):
        sorted_tpr = sorted(tpr_idx[key], key=lambda item: float(item["multiplier"]))
        fpr_row = fpr_idx.get(key)
        headline = next(
            (t for t in sorted_tpr if float(t["multiplier"]) == HEADLINE_MULTIPLIER), None
        )
        status = _domain_status(fpr_row, headline)
        det_mult = _detection_multiplier(sorted_tpr)
        domain = key[domain_pos]
        for tpr_row in sorted_tpr:
            tpr_precise = tpr_row["wilson_half_width"] <= TPR_HALF_WIDTH_TARGET
            row = dict(zip(id_cols, key, strict=True))
            row.update(
                {
                    "referee": "gate_stack",
                    "alpha": ALPHA0,
                    "multiplier": tpr_row["multiplier"],
                    "edge_bps": tpr_row["edge_bps"],
                    "mde_bps": mde_map.get(str(domain), math.nan),
                    "fpr": fpr_row["fpr"] if fpr_row else math.nan,
                    "fpr_wilson_half_width": fpr_row["wilson_half_width"] if fpr_row else math.nan,
                    "tpr": tpr_row["tpr"],
                    "tpr_wilson_half_width": tpr_row["wilson_half_width"],
                    "tpr_meets_target": bool(tpr_row["tpr"] >= POWER_TARGET and tpr_precise),
                    "detection_multiplier": det_mult,
                    "status": status,
                }
            )
            if per_instrument:
                row["under_powered"] = bool(
                    fpr_row is None
                    or fpr_row["wilson_half_width"] > FPR_HALF_WIDTH_TARGET
                    or not tpr_precise
                )
            output.append(row)
    return output


def summarize_candidate_sanity(
    sanity_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Aggregate per-draw diagnostics into per-cell sanity rows + an overall gate.

    Returns
    -------
    tuple[list[dict[str, Any]], dict[str, Any]]
        ``(sanity_summary_rows, overall_sanity)`` where ``overall_sanity`` holds
        the pooled active/match rates and the predeclared pass flags.
    """
    frame = pl.DataFrame(sanity_rows)
    grouped = (
        frame.group_by(
            ["instrument", "domain", "scenario", "multiplier", "edge_bps"], maintain_order=True
        )
        .agg(
            pl.len().alias("n_draws"),
            pl.col("active_bars").sum().alias("sum_active"),
            pl.col("eligible_rows").sum().alias("sum_eligible"),
            pl.col("active_train").sum().alias("sum_active_train"),
            pl.col("eligible_train").sum().alias("sum_eligible_train"),
            pl.col("active_test").sum().alias("sum_active_test"),
            pl.col("eligible_test").sum().alias("sum_eligible_test"),
            pl.col("matched_active").sum().alias("sum_matched"),
            pl.col("up_episodes").mean().alias("mean_up_episodes"),
            pl.col("down_episodes").mean().alias("mean_down_episodes"),
            pl.col("realized_gross_bps").mean().alias("mean_realized_gross_bps"),
            pl.col("realized_net_bps").mean().alias("mean_realized_net_bps"),
        )
        .with_columns(
            (pl.col("sum_active") / pl.col("sum_eligible")).alias("active_rate_overall"),
            (pl.col("sum_active_train") / pl.col("sum_eligible_train")).alias("active_rate_train"),
            (pl.col("sum_active_test") / pl.col("sum_eligible_test")).alias("active_rate_test"),
            (pl.col("sum_matched") / pl.col("sum_active")).alias("match_rate"),
        )
        .with_columns(
            ((pl.col("active_rate_overall") - ACTIVE_RATE_TARGET).abs() <= ACTIVE_RATE_TOL).alias(
                "active_rate_ok"
            ),
            ((pl.col("match_rate") - MATCH_RATE_TARGET).abs() <= MATCH_RATE_TOL).alias(
                "match_rate_ok"
            ),
            pl.when(pl.col("scenario") == "positive")
            .then((pl.col("mean_realized_net_bps") - pl.col("edge_bps")).abs())
            .otherwise(None)
            .alias("calibration_abs_error_bps"),
        )
        .sort(["domain", "instrument", "scenario", "multiplier"])
    )
    totals = frame.select(
        pl.col("active_bars").sum().alias("active"),
        pl.col("eligible_rows").sum().alias("eligible"),
        pl.col("matched_active").sum().alias("matched"),
    ).row(0, named=True)
    overall_active = totals["active"] / totals["eligible"] if totals["eligible"] else math.nan
    overall_match = totals["matched"] / totals["active"] if totals["active"] else math.nan
    overall = {
        "overall_active_rate": float(overall_active),
        "overall_match_rate": float(overall_match),
        "active_rate_ok": bool(abs(overall_active - ACTIVE_RATE_TARGET) <= ACTIVE_RATE_TOL),
        "match_rate_ok": bool(abs(overall_match - MATCH_RATE_TARGET) <= MATCH_RATE_TOL),
    }
    overall["sanity_pass"] = bool(overall["active_rate_ok"] and overall["match_rate_ok"])
    return grouped.to_dicts(), overall


# --------------------------------------------------------------------------- #
# Plotting
# --------------------------------------------------------------------------- #
def plot_tpr_curves(tpr_rows: list[dict[str, Any]]) -> None:
    """Gate-stack TPR vs edge multiplier per domain at alpha0, with 0.80 line."""
    pdf = pl.DataFrame(tpr_rows).to_pandas()
    pdf = pdf[(pdf["referee"] == "gate_stack") & (pdf["alpha"] == ALPHA0)]
    fig, ax = plt.subplots(figsize=(8, 5))
    for domain, group in pdf.groupby("domain"):
        group = group.sort_values("multiplier")
        ax.plot(group["multiplier"], group["tpr"], marker="o", label=f"{domain}")
    ax.axhline(POWER_TARGET, color="black", linewidth=1, label="TPR target 0.80")
    ax.axvline(HEADLINE_MULTIPLIER, color="grey", linestyle="--", linewidth=1)
    ax.set_xlabel("Target edge (x domain gate MDE)")
    ax.set_ylabel("TPR (gate stack)")
    ax.set_title("Realistic-candidate TPR vs near-MDE edge at alpha=0.05")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "tpr_vs_multiplier.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_fpr(fpr_rows: list[dict[str, Any]]) -> None:
    """FPR by domain/referee at alpha0 against the alpha0 target marker."""
    pdf = pl.DataFrame(fpr_rows).to_pandas()
    pdf = pdf[pdf["alpha"] == ALPHA0].sort_values(["domain", "referee"])
    fig, ax = plt.subplots(figsize=(8, 5))
    labels = pdf["domain"] + " " + pdf["referee"]
    ax.bar(range(len(pdf)), pdf["fpr"])
    ax.axhline(ALPHA0, color="red", linewidth=1, label="alpha0 = 0.05")
    ax.set_xticks(range(len(pdf)), labels, rotation=45, ha="right")
    ax.set_ylabel("FPR")
    ax.set_title("Realistic-candidate false-positive rate at alpha=0.05")
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "fpr_by_domain_referee.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_candidate_diagnostics(sanity_summary: list[dict[str, Any]]) -> None:
    """Candidate active-rate and match-rate by domain/instrument vs targets."""
    pdf = pl.DataFrame(sanity_summary).to_pandas()
    agg = (
        pdf.groupby(["domain", "instrument"], as_index=False)
        .agg(active_rate=("active_rate_overall", "mean"), match_rate=("match_rate", "mean"))
        .sort_values(["domain", "instrument"])
    )
    labels = agg["domain"] + " " + agg["instrument"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].bar(range(len(agg)), agg["active_rate"])
    axes[0].axhline(ACTIVE_RATE_TARGET, color="red", linewidth=1, label="target 0.80")
    axes[0].set_xticks(range(len(agg)), labels, rotation=90, fontsize=6)
    axes[0].set_ylabel("Active rate")
    axes[0].set_title("Candidate active rate")
    axes[0].legend()
    axes[1].bar(range(len(agg)), agg["match_rate"])
    axes[1].axhline(MATCH_RATE_TARGET, color="red", linewidth=1, label="target 0.75")
    axes[1].set_xticks(range(len(agg)), labels, rotation=90, fontsize=6)
    axes[1].set_ylabel("Match rate (active bars)")
    axes[1].set_title("Candidate match rate")
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "candidate_diagnostics.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_pooled_vs_instrument_tpr(
    tpr_rows: list[dict[str, Any]], tpr_inst_rows: list[dict[str, Any]]
) -> None:
    """Heatmap of gate-stack TPR at the 1.0x MDE grid point: pooled + instruments."""
    pooled = pl.DataFrame(tpr_rows).filter(
        (pl.col("referee") == "gate_stack")
        & (pl.col("alpha") == ALPHA0)
        & (pl.col("multiplier") == HEADLINE_MULTIPLIER)
    )
    inst = pl.DataFrame(tpr_inst_rows).filter(
        (pl.col("referee") == "gate_stack")
        & (pl.col("alpha") == ALPHA0)
        & (pl.col("multiplier") == HEADLINE_MULTIPLIER)
    )
    domains = sorted(pooled.get_column("domain").to_list())
    instruments = sorted(inst.get_column("instrument").unique().to_list())
    rows = ["POOLED"] + instruments
    matrix = np.full((len(rows), len(domains)), np.nan)
    pooled_map = {d: t for d, t in zip(pooled["domain"], pooled["tpr"])}
    inst_map = {(i, d): t for i, d, t in zip(inst["instrument"], inst["domain"], inst["tpr"])}
    for col, domain in enumerate(domains):
        matrix[0, col] = pooled_map.get(domain, np.nan)
        for r, instrument in enumerate(instruments, start=1):
            matrix[r, col] = inst_map.get((instrument, domain), np.nan)

    fig, ax = plt.subplots(figsize=(7, 5))
    im = ax.imshow(matrix, aspect="auto", cmap="RdYlGn", vmin=0.0, vmax=1.0)
    ax.set_xticks(range(len(domains)), domains)
    ax.set_yticks(range(len(rows)), rows)
    for r in range(len(rows)):
        for c in range(len(domains)):
            if np.isfinite(matrix[r, c]):
                ax.text(c, r, f"{matrix[r, c]:.2f}", ha="center", va="center", fontsize=7)
    ax.set_title("Gate-stack TPR at 1.0x MDE (pooled vs per-instrument)")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "pooled_vs_instrument_tpr.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_effect_distribution(effect_points: dict[str, Any]) -> None:
    """Per-draw gate-stack effect distribution at the 1.0x MDE point, by domain.

    Consumes only the bounded points pre-extracted by
    :func:`extract_effect_points_1x` (at most ``POSITIVE_DRAWS_PER_EDGE`` x
    instruments per domain), so the plotting pass never re-materialises the full
    verdict set.

    Parameters
    ----------
    effect_points : dict[str, Any]
        ``{"points": {domain: [effect_bps, ...]}, "edges": {domain: target_bps}}``.
    """
    points = effect_points["points"]
    edges = effect_points["edges"]
    domains = sorted(points)
    data = [points[domain] for domain in domains]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.boxplot(data, tick_labels=domains, showfliers=False)
    for idx, domain in enumerate(domains, start=1):
        ax.scatter([idx], [edges[domain]], color="red", marker="D", zorder=3)
        ax.scatter([idx], [materiality_bps_for(domain)], color="blue", marker="_", s=200, zorder=3)
    ax.axhline(0.0, color="grey", linewidth=1)
    ax.set_ylabel("Gate-stack net effect (bps)")
    ax.set_title("Per-draw effect at 1.0x MDE (red=target edge, blue=materiality)")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "effect_distribution_1x.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def build_cells_and_tasks(
    files: list[Path], mde_map: dict[str, float]
) -> tuple[
    dict[tuple[str, str], dict[str, Any]],
    list[tuple[str, str, str, str, float, float, int]],
    list[dict[str, Any]],
    list[str],
]:
    """Load holdout-safe analysis slices, build domains, enumerate draw tasks.

    Domains whose gate MDE is missing or non-finite are skipped (reported
    inconclusive), never hardcoded.

    Returns
    -------
    tuple
        ``(cell_data, tasks, analysis_rows, inconclusive_domains)``.
    """
    cell_data: dict[tuple[str, str], dict[str, Any]] = {}
    tasks: list[tuple[str, str, str, str, float, float, int]] = []
    analysis_rows: list[dict[str, Any]] = []
    inconclusive: set[str] = set()
    for path in tqdm(files, desc="EXP-005 load/domains"):
        data = load_analysis_data(path)
        for domain, frame in build_domain_frames(data.frame).items():
            gate_mde = mde_map.get(domain, math.nan)
            returns, aligned = next_log_returns_from_bars(frame)
            split_index = domain_split_index(aligned, data.train_end_ts)
            cell_data[(data.instrument, domain)] = {
                "returns": returns,
                "split_index": split_index,
                "cost_bps": cost_bps_for(data.instrument, domain),
            }
            analysis_rows.append(
                {
                    "instrument": data.instrument,
                    "source_file": data.source_file,
                    "domain": domain,
                    "domain_rows": frame.height,
                    "return_rows": len(returns),
                    "split_index": split_index,
                    "gate_mde_bps": gate_mde,
                    "train_end": data.train_end,
                    "analysis_start": data.analysis_start,
                    "analysis_end": data.analysis_end,
                }
            )
            if not math.isfinite(gate_mde):
                inconclusive.add(domain)
                continue
            tasks.extend(build_draw_tasks(data.instrument, domain, gate_mde))
    return cell_data, tasks, analysis_rows, sorted(inconclusive)


def _sort_verdicts(verdict_rows: list[dict[str, Any]]) -> None:
    """Sort verdict rows in place into a canonical, reproducible order."""
    verdict_rows.sort(
        key=lambda row: (
            row["instrument"],
            row["domain"],
            row["scenario"],
            row["generator"],
            float(row["multiplier"]),
            float(row["edge_bps"]),
            int(row["draw"]),
            row["referee"],
            float(row["alpha"]),
        )
    )


def main() -> None:
    """Run the EXP-005 keystone-closure detection anchor and write results/plots."""
    configure_logging()
    ensure_output_dirs()
    dependency_status = require_dependencies()
    predeclaration = require_predeclaration_confirmation()
    mde_map = load_gate_mde_map()

    files = list_timebar_files(DATA_DIR)
    if not files:
        raise FileNotFoundError(f"No time-bar files found under {DATA_DIR / 'timebars'}")

    cell_data, tasks, analysis_rows, inconclusive_domains = build_cells_and_tasks(files, mde_map)
    if not tasks:
        raise RuntimeError("No reportable domains: every gate MDE was missing or non-finite")

    verdict_rows, sanity_rows = run_draw_tasks(tasks, cell_data)
    _sort_verdicts(verdict_rows)

    fpr_rows, tpr_rows, fpr_inst_rows, tpr_inst_rows = summarize_rates(verdict_rows)
    detection_rows = build_detection(fpr_rows, tpr_rows, mde_map, id_cols=["domain"])
    per_instrument_rows = build_detection(
        fpr_inst_rows, tpr_inst_rows, mde_map, id_cols=["instrument", "domain"]
    )
    sanity_summary, overall_sanity = summarize_candidate_sanity(sanity_rows)
    effect_points = extract_effect_points_1x(verdict_rows)

    status_counts: dict[str, int] = {}
    domain_status: dict[str, str] = {}
    for row in detection_rows:
        if float(row["multiplier"]) == HEADLINE_MULTIPLIER:
            domain_status[str(row["domain"])] = str(row["status"])
            status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1

    measurements_produced = bool(detection_rows) and bool(tpr_rows) and bool(fpr_rows)
    overall_status = (
        "COMPLETE" if measurements_produced and overall_sanity["sanity_pass"] else "INCONCLUSIVE"
    )

    write_rows(RESULTS_DIR / "analysis_metadata.csv", analysis_rows)
    write_rows(RESULTS_DIR / "realistic_candidate_draws.csv", verdict_rows)
    write_rows(RESULTS_DIR / "candidate_sanity.csv", sanity_summary)
    write_rows(RESULTS_DIR / "fpr_summary.csv", fpr_rows)
    write_rows(RESULTS_DIR / "tpr_summary.csv", tpr_rows)
    write_rows(RESULTS_DIR / "detection_summary.csv", detection_rows)
    write_rows(RESULTS_DIR / "per_instrument_detection.csv", per_instrument_rows)
    write_json(
        RESULTS_DIR / "run_metadata.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "overall_status": overall_status,
            "measurements_produced": measurements_produced,
            "dependencies": dependency_status,
            "predeclaration": predeclaration,
            "gate_mde_map_bps": mde_map,
            "reportable_domains": sorted(domain_status),
            "inconclusive_domains_missing_mde": inconclusive_domains,
            "domain_status": domain_status,
            "detection_status_counts": status_counts,
            "candidate_construction": {
                "p_active": P_ACTIVE,
                "q_match": Q_MATCH,
                "edge_multipliers": list(EDGE_MULTIPLIERS),
                "headline_multiplier": HEADLINE_MULTIPLIER,
                "null_generators": list(NULL_GENERATORS),
                "null_draws_per_generator": NULL_DRAWS_PER_GENERATOR,
                "positive_draws_per_edge": POSITIVE_DRAWS_PER_EDGE,
                "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
                "alpha_grid": list(ALPHA_GRID),
                "alpha0": ALPHA0,
            },
            "candidate_sanity": overall_sanity,
        },
    )

    plot_tpr_curves(tpr_rows)
    plot_fpr(fpr_rows)
    plot_candidate_diagnostics(sanity_summary)
    plot_pooled_vs_instrument_tpr(tpr_rows, tpr_inst_rows)
    plot_effect_distribution(effect_points)

    LOGGER.info("EXP-005 complete: %s", overall_status)
    LOGGER.info("Domain status (gate stack, 1.0x MDE): %s", domain_status)
    LOGGER.info("Candidate sanity: %s", overall_sanity)
    LOGGER.info("Results: %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
