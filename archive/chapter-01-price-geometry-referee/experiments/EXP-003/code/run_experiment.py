"""
Experiment EXP-003: Referee Operating-Characteristic Calibration.

This is the Phase 001 keystone calibration run. It measures FPR, TPR, MDE, and
gate-leg pass rates using the validated synthetic substrate. It never loads the
final 30% global holdout.
"""
from __future__ import annotations

import json
import logging
import math
import multiprocessing as mp
import os
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from tqdm.auto import tqdm

from xen.referee_calibration import (
    ALPHA_GRID,
    EDGE_GRID_BPS,
    build_domain_frames,
    cost_bps_for,
    domain_split_index,
    evaluate_referees,
    list_timebar_files,
    load_analysis_data,
    next_log_returns_from_bars,
    permuted_returns,
    plant_positive_edge,
    random_state_positions,
    seed_for,
    verdict_rate_rows,
    wilson_interval,
    write_json,
)


LOGGER = logging.getLogger(__name__)

EXPERIMENT_ID = "EXP-003"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data"
EXPERIMENT_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
EXP001_METADATA = (
    PROJECT_ROOT / "python" / "experiments" / "EXP-001" / "results" / "run_metadata.json"
)
EXP002_METADATA = (
    PROJECT_ROOT / "python" / "experiments" / "EXP-002" / "results" / "run_metadata.json"
)

NULL_DRAWS_PER_GENERATOR = 500
POSITIVE_DRAWS_PER_EDGE = 500
BOOTSTRAP_RESAMPLES = 1000
POWER_TARGET = 0.80
FPR_HALF_WIDTH_TARGET = 0.03
TPR_HALF_WIDTH_TARGET = 0.05

# Draws are embarrassingly parallel and each is fully seed-deterministic, so the
# worker count changes only scheduling, never any verdict. Override with the
# EXP003_WORKERS env var (e.g. to leave cores free); default = all cores.
N_WORKERS = max(1, int(os.environ.get("EXP003_WORKERS", os.cpu_count() or 1)))
# Chunk size for parallel dispatch: large enough to amortize IPC, small enough
# that the heavy 5m tasks still load-balance across workers. Scheduling knob
# only (measured ~6x on 10 cores); it has no effect on results.
TASK_CHUNKSIZE = 16

# Read-only per-cell state installed in each worker by ``_init_worker``. Keyed by
# (instrument, domain) -> {"returns", "split_index", "cost_bps"}.
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


def require_dependency_pass(path: Path, experiment_id: str) -> None:
    """Fail fast unless the dependency experiment recorded an overall PASS."""
    if not path.exists():
        raise FileNotFoundError(f"{experiment_id} metadata not found: {path}")
    metadata = json.loads(path.read_text(encoding="utf-8"))
    if metadata.get("overall_status") != "PASS":
        raise RuntimeError(f"{experiment_id} did not pass: {metadata}")


# --------------------------------------------------------------------------- #
# Draw evaluation
# --------------------------------------------------------------------------- #
def add_referee_rows(
    rows: list[dict[str, Any]],
    *,
    instrument: str,
    domain: str,
    scenario: str,
    generator: str,
    edge_bps: float,
    draw: int,
    returns: np.ndarray,
    positions: np.ndarray,
    seed: int,
    split_index: int,
) -> None:
    """Evaluate both referees for one draw and append labelled verdict rows.

    Parameters
    ----------
    rows : list[dict[str, Any]]
        Accumulator mutated in place with one row per (referee, alpha).
    instrument, domain, scenario, generator : str
        Draw labels copied onto every emitted row.
    edge_bps : float
        Planted net edge (0.0 for nulls).
    draw : int
        Draw index within the cell.
    returns, positions : np.ndarray
        The scenario returns and candidate positions for this draw.
    seed : int
        Seed for the referee bootstraps.
    split_index : int
        Shared-timestamp train/test boundary for the domain.
    """
    for verdict in evaluate_referees(
        returns,
        positions,
        instrument=instrument,
        domain=domain,
        alpha_values=ALPHA_GRID,
        n_bootstrap=BOOTSTRAP_RESAMPLES,
        seed=seed,
        split_index=split_index,
    ):
        row = {
            "instrument": instrument,
            "domain": domain,
            "scenario": scenario,
            "generator": generator,
            "edge_bps": edge_bps,
            "draw": draw,
        }
        row.update(verdict)
        rows.append(row)


def _init_worker(cells: dict[tuple[str, str], dict[str, Any]]) -> None:
    """Pool initializer: install the read-only per-cell state in this worker."""
    global _WORKER_CELLS
    _WORKER_CELLS = cells


def _evaluate_draw_task(
    task: tuple[str, str, str, str, float, int]
) -> list[dict[str, Any]]:
    """Evaluate both referees for a single draw described by ``task``.

    A task is ``(instrument, domain, scenario, generator, edge_bps, draw)``. The
    candidate positions and scenario returns are regenerated deterministically
    from the per-draw seed, so the output is independent of which worker (or no
    worker) runs the task. This reproduces the prior serial loop exactly; only
    the iteration is now distributable.

    Parameters
    ----------
    task : tuple
        ``(instrument, domain, scenario, generator, edge_bps, draw)``.

    Returns
    -------
    list[dict[str, Any]]
        The labelled verdict rows for this draw (one per referee x alpha).
    """
    instrument, domain, scenario, generator, edge_bps, draw = task
    cell = _WORKER_CELLS[(instrument, domain)]
    returns = cell["returns"]
    split_index = cell["split_index"]
    cost_bps = cell["cost_bps"]

    if scenario == "null":
        seed = seed_for(EXPERIMENT_ID, instrument, domain, generator, draw)
        states = random_state_positions(len(returns), seed)
        scoped_returns = (
            permuted_returns(returns, seed + 1) if generator == "bar_permutation" else returns
        )
    else:
        seed = seed_for(EXPERIMENT_ID, instrument, domain, "known_positive", edge_bps, draw)
        states = random_state_positions(len(returns), seed)
        scoped_returns = plant_positive_edge(
            returns, states, net_edge_bps=float(edge_bps), cost_bps=cost_bps
        )

    rows: list[dict[str, Any]] = []
    add_referee_rows(
        rows,
        instrument=instrument,
        domain=domain,
        scenario=scenario,
        generator=generator,
        edge_bps=edge_bps,
        draw=draw,
        returns=scoped_returns,
        positions=states,
        seed=seed,
        split_index=split_index,
    )
    return rows


def build_draw_tasks(
    instrument: str, domain: str
) -> list[tuple[str, str, str, str, float, int]]:
    """Enumerate every null and known-positive draw task for one cell.

    Parameters
    ----------
    instrument, domain : str
        Cell identifiers used for seeding and labelling.

    Returns
    -------
    list[tuple]
        ``(instrument, domain, scenario, generator, edge_bps, draw)`` tuples for
        both null generators and the full positive edge grid (including 0.0).
    """
    tasks: list[tuple[str, str, str, str, float, int]] = []
    for generator in ("bar_permutation", "random_signal"):
        for draw in range(NULL_DRAWS_PER_GENERATOR):
            tasks.append((instrument, domain, "null", generator, 0.0, draw))
    for edge_bps in EDGE_GRID_BPS:
        for draw in range(POSITIVE_DRAWS_PER_EDGE):
            tasks.append(
                (instrument, domain, "positive", "known_positive", float(edge_bps), draw)
            )
    return tasks


def run_draw_tasks(
    tasks: list[tuple[str, str, str, str, float, int]],
    cell_data: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    """Evaluate all draw tasks, in parallel when ``N_WORKERS > 1``.

    Each task is a pure, seed-deterministic function of its tuple plus the
    read-only ``cell_data``, so the collected verdict rows are content-identical
    to a serial run regardless of worker count. The caller sorts the rows into a
    canonical order, so output is fully reproducible despite ``imap_unordered``.

    Parameters
    ----------
    tasks : list[tuple]
        Flattened per-draw task list across all cells.
    cell_data : dict
        Read-only per-cell returns/split/cost state shared with the workers.

    Returns
    -------
    list[dict[str, Any]]
        All referee verdict rows (unsorted).
    """
    verdict_rows: list[dict[str, Any]] = []
    if N_WORKERS <= 1:
        _init_worker(cell_data)
        for task in tqdm(tasks, desc="EXP-003 draws (serial)"):
            verdict_rows.extend(_evaluate_draw_task(task))
        return verdict_rows

    with mp.Pool(
        processes=N_WORKERS, initializer=_init_worker, initargs=(cell_data,)
    ) as pool:
        for rows in tqdm(
            pool.imap_unordered(_evaluate_draw_task, tasks, chunksize=TASK_CHUNKSIZE),
            total=len(tasks),
            desc=f"EXP-003 draws (x{N_WORKERS})",
        ):
            verdict_rows.extend(rows)
    return verdict_rows


# --------------------------------------------------------------------------- #
# Summaries
# --------------------------------------------------------------------------- #
def summarize_fpr_tpr(
    verdict_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Compute per-cell FPR (nulls) and TPR (positives) Wilson-interval rows.

    Parameters
    ----------
    verdict_rows : list[dict[str, Any]]
        All referee verdict rows from :func:`evaluate_domain_draws`.

    Returns
    -------
    tuple[list[dict[str, Any]], list[dict[str, Any]]]
        ``(fpr_rows, tpr_rows)``.
    """
    null_rows = [row for row in verdict_rows if row["scenario"] == "null"]
    positive_rows = [
        row for row in verdict_rows if row["scenario"] == "positive" and row["edge_bps"] > 0.0
    ]
    fpr_rows = verdict_rate_rows(
        null_rows,
        group_cols=["domain", "referee", "alpha"],
        rate_name="fpr",
    )
    tpr_rows = verdict_rate_rows(
        positive_rows,
        group_cols=["domain", "referee", "alpha", "edge_bps"],
        rate_name="tpr",
    )
    return fpr_rows, tpr_rows


def grid_half_step(edge_bps: float) -> float:
    """Half the smaller neighbouring gap around ``edge_bps`` on the edge grid.

    Parameters
    ----------
    edge_bps : float
        A grid value; returns ``nan`` if it is not on ``EDGE_GRID_BPS``.

    Returns
    -------
    float
        Grid-discretisation uncertainty for an MDE landing on ``edge_bps``.
    """
    grid = sorted(float(value) for value in EDGE_GRID_BPS)
    if edge_bps not in grid:
        return math.nan
    index = grid.index(edge_bps)
    left = grid[index] - grid[index - 1] if index > 0 else grid[1] - grid[0]
    right = grid[index + 1] - grid[index] if index < len(grid) - 1 else left
    return min(left, right) / 2.0


def _classify_mde_cell(
    *,
    fpr: dict[str, Any],
    alpha: float,
    tpr_rows: list[dict[str, Any]],
) -> tuple[str, float, float]:
    """Classify one (domain, referee, alpha) cell into a status and MDE.

    Parameters
    ----------
    fpr : dict[str, Any]
        The matching FPR row (rate + Wilson half-width).
    alpha : float
        The cell's operating point.
    tpr_rows : list[dict[str, Any]]
        TPR rows for the cell across the edge grid.

    Returns
    -------
    tuple[str, float, float]
        ``(status, mde_bps, tpr_half_width_at_mde)`` with ``nan`` where the
        cell yields no usable MDE.
    """
    fpr_controlled = fpr["fpr"] <= alpha
    fpr_precise = fpr["wilson_half_width"] <= FPR_HALF_WIDTH_TARGET
    sorted_rows = sorted(tpr_rows, key=lambda item: float(item["edge_bps"]))
    candidates = [
        row
        for row in sorted_rows
        if row["tpr"] >= POWER_TARGET and row["wilson_half_width"] <= TPR_HALF_WIDTH_TARGET
    ]
    if not fpr_controlled:
        return "FAIL_FPR", math.nan, math.nan
    if not fpr_precise:
        return "INCONCLUSIVE_FPR_PRECISION", math.nan, math.nan
    if not candidates:
        return "INCONCLUSIVE_NO_MDE", math.nan, math.nan
    return (
        "PASS",
        float(candidates[0]["edge_bps"]),
        float(candidates[0]["wilson_half_width"]),
    )


def summarize_mde(
    fpr_rows: list[dict[str, Any]],
    tpr_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Locate each cell's empirical MDE at the power target across the α grid.

    Parameters
    ----------
    fpr_rows, tpr_rows : list[dict[str, Any]]
        Per-cell FPR and TPR summaries from :func:`summarize_fpr_tpr`.

    Returns
    -------
    list[dict[str, Any]]
        One row per (domain, referee, alpha) with status, MDE, and the
        grid/TPR uncertainty at the MDE.
    """
    output: list[dict[str, Any]] = []
    fpr_lookup = {
        (row["domain"], row["referee"], float(row["alpha"])): row for row in fpr_rows
    }
    grouped_tpr: dict[tuple[str, str, float], list[dict[str, Any]]] = {}
    for row in tpr_rows:
        key = (row["domain"], row["referee"], float(row["alpha"]))
        grouped_tpr.setdefault(key, []).append(row)

    for key, rows in grouped_tpr.items():
        domain, referee, alpha = key
        fpr = fpr_lookup.get(key)
        if fpr is None:
            continue
        status, mde, tpr_half_width = _classify_mde_cell(
            fpr=fpr, alpha=alpha, tpr_rows=rows
        )
        output.append(
            {
                "domain": domain,
                "referee": referee,
                "alpha": alpha,
                "fpr": fpr["fpr"],
                "fpr_wilson_half_width": fpr["wilson_half_width"],
                "mde_bps": mde,
                "mde_grid_uncertainty_bps": grid_half_step(mde) if math.isfinite(mde) else math.nan,
                "tpr_wilson_half_width_at_mde": tpr_half_width,
                "status": status,
            }
        )
    return output


def summarize_leg_pass_rates(verdict_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compute gate-stack per-leg pass rates with Wilson intervals.

    Parameters
    ----------
    verdict_rows : list[dict[str, Any]]
        All referee verdict rows; only ``gate_stack`` rows contribute.

    Returns
    -------
    list[dict[str, Any]]
        One row per (domain, alpha, scenario, edge_bps, leg).
    """
    leg_rows: list[dict[str, Any]] = []
    for row in verdict_rows:
        if row["referee"] != "gate_stack":
            continue
        legs = json.loads(row["leg_results"])
        for leg in ("L1_readiness", "L2_integrity", "L3_outcome", "L4_stability", "L5_materiality"):
            leg_rows.append(
                {
                    "domain": row["domain"],
                    "alpha": row["alpha"],
                    "scenario": row["scenario"],
                    "edge_bps": row["edge_bps"],
                    "leg": leg,
                    "passed": bool(legs[leg]),
                }
            )
    if not leg_rows:
        return []
    output: list[dict[str, Any]] = []
    frame = pl.DataFrame(leg_rows)
    for key_values, group in frame.group_by(["domain", "alpha", "scenario", "edge_bps", "leg"]):
        domain, alpha, scenario, edge_bps, leg = key_values
        n = group.height
        successes = int(group.filter(pl.col("passed")).height)
        center, lower, upper = wilson_interval(successes, n)
        output.append(
            {
                "domain": domain,
                "alpha": alpha,
                "scenario": scenario,
                "edge_bps": edge_bps,
                "leg": leg,
                "pass_rate": successes / n if n else math.nan,
                "wilson_center": center,
                "wilson_lower": lower,
                "wilson_upper": upper,
                "wilson_half_width": (upper - lower) / 2.0 if n else math.nan,
                "successes": successes,
                "n": n,
            }
        )
    return output


# --------------------------------------------------------------------------- #
# Plotting
# --------------------------------------------------------------------------- #
def plot_power_curves(tpr_rows: list[dict[str, Any]]) -> None:
    """Plot TPR(edge) power curves per domain/referee at alpha=0.05.

    Parameters
    ----------
    tpr_rows : list[dict[str, Any]]
        Per-cell TPR summaries from :func:`summarize_fpr_tpr`.
    """
    pdf = pl.DataFrame(tpr_rows).to_pandas()
    fig, ax = plt.subplots(figsize=(9, 5))
    for (domain, referee, alpha), group in pdf.groupby(["domain", "referee", "alpha"]):
        if float(alpha) != 0.05:
            continue
        label = f"{domain} {referee}"
        group = group.sort_values("edge_bps")
        ax.plot(group["edge_bps"], group["tpr"], marker="o", label=label)
    ax.axhline(POWER_TARGET, color="black", linewidth=1)
    ax.set_xlabel("Planted net edge (bps/trade)")
    ax.set_ylabel("TPR")
    ax.set_title("TPR curves at alpha=0.05")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "tpr_curves_alpha_005.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_mde(mde_rows: list[dict[str, Any]]) -> None:
    """Plot the empirical MDE per domain/referee at alpha=0.05.

    Parameters
    ----------
    mde_rows : list[dict[str, Any]]
        Per-cell MDE summaries from :func:`summarize_mde`.
    """
    pdf = pl.DataFrame(mde_rows).filter(pl.col("alpha") == 0.05).to_pandas()
    fig, ax = plt.subplots(figsize=(8, 5))
    labels = pdf["domain"] + " " + pdf["referee"]
    ax.bar(range(len(pdf)), pdf["mde_bps"].fillna(0.0))
    ax.set_xticks(range(len(pdf)), labels, rotation=45, ha="right")
    ax.set_ylabel("MDE (bps/trade)")
    ax.set_title("Empirical MDE at alpha=0.05")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "mde_alpha_005.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_fpr(fpr_rows: list[dict[str, Any]]) -> None:
    """Plot FPR by domain/referee/alpha against the alpha target markers.

    Parameters
    ----------
    fpr_rows : list[dict[str, Any]]
        Per-cell FPR summaries from :func:`summarize_fpr_tpr`.
    """
    pdf = pl.DataFrame(fpr_rows).to_pandas().sort_values(["domain", "referee", "alpha"])
    fig, ax = plt.subplots(figsize=(10, 5))
    labels = pdf["domain"] + " " + pdf["referee"] + " a=" + pdf["alpha"].astype(str)
    ax.bar(range(len(pdf)), pdf["fpr"])
    ax.scatter(range(len(pdf)), pdf["alpha"], marker="_", color="red", label="alpha target")
    ax.set_xticks(range(len(pdf)), labels, rotation=90, fontsize=6)
    ax.set_ylabel("FPR")
    ax.set_title("False-positive rate by domain / referee / alpha")
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "fpr_by_domain_referee_alpha.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_leg_pass_rates(leg_rows: list[dict[str, Any]]) -> None:
    """Plot gate-leg null pass rates by domain at alpha=0.05.

    Parameters
    ----------
    leg_rows : list[dict[str, Any]]
        Per-leg pass-rate rows from :func:`summarize_leg_pass_rates`.
    """
    if not leg_rows:
        return
    pdf = pl.DataFrame(leg_rows).to_pandas()
    # Operating point: which legs reject the nulls at alpha = 0.05.
    sub = pdf[(pdf["scenario"] == "null") & (pdf["alpha"] == 0.05)]
    if sub.empty:
        sub = pdf
    pivot = sub.pivot_table(index="leg", columns="domain", values="pass_rate", aggfunc="mean")
    fig, ax = plt.subplots(figsize=(9, 5))
    pivot.plot(kind="bar", ax=ax)
    ax.set_ylabel("Leg pass rate (null, alpha=0.05)")
    ax.set_title("Gate-leg pass rates by domain")
    ax.legend(title="domain", fontsize=7)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "leg_pass_rates.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_effective_sample(verdict_rows: list[dict[str, Any]]) -> None:
    """Plot mean effective sample size (blocks) by domain/referee.

    Parameters
    ----------
    verdict_rows : list[dict[str, Any]]
        All referee verdict rows; aggregated in Polars before plotting.
    """
    # Aggregate in Polars first so only the small summary is converted to pandas.
    summary = (
        pl.DataFrame(verdict_rows)
        .group_by(["domain", "referee"])
        .agg(pl.col("effective_n").mean().alias("effective_n"))
        .sort(["domain", "referee"])
        .to_pandas()
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    labels = summary["domain"] + " " + summary["referee"]
    ax.bar(range(len(summary)), summary["effective_n"])
    ax.set_xticks(range(len(summary)), labels, rotation=45, ha="right")
    ax.set_ylabel("Mean effective N (blocks)")
    ax.set_title("Effective sample by domain / referee")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "effective_sample.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run the EXP-003 keystone calibration and write results/plots."""
    configure_logging()
    ensure_output_dirs()
    require_dependency_pass(EXP001_METADATA, "EXP-001")
    require_dependency_pass(EXP002_METADATA, "EXP-002")

    files = list_timebar_files(DATA_DIR)
    if not files:
        raise FileNotFoundError(f"No time-bar files found under {DATA_DIR / 'timebars'}")

    # Build phase (main process only): load each instrument's holdout-safe
    # analysis slice, construct domains, and enumerate the per-draw task list.
    cell_data: dict[tuple[str, str], dict[str, Any]] = {}
    analysis_rows: list[dict[str, Any]] = []
    tasks: list[tuple[str, str, str, str, float, int]] = []
    for path in tqdm(files, desc="EXP-003 load/domains"):
        data = load_analysis_data(path)
        domains = build_domain_frames(data.frame)
        for domain, frame in domains.items():
            returns, aligned = next_log_returns_from_bars(frame)
            # Train/test cut shared across domains via the 1m boundary timestamp.
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
                    "train_end": data.train_end,
                    "analysis_start": data.analysis_start,
                    "analysis_end": data.analysis_end,
                }
            )
            tasks.extend(build_draw_tasks(data.instrument, domain))

    # Evaluation phase: distribute the draws (seed-deterministic, so the worker
    # count never changes a verdict), then sort into a canonical order so the
    # written CSV is reproducible regardless of worker scheduling.
    verdict_rows = run_draw_tasks(tasks, cell_data)
    verdict_rows.sort(
        key=lambda row: (
            row["instrument"],
            row["domain"],
            row["scenario"],
            row["generator"],
            float(row["edge_bps"]),
            int(row["draw"]),
            row["referee"],
            float(row["alpha"]),
        )
    )

    fpr_rows, tpr_rows = summarize_fpr_tpr(verdict_rows)
    mde_rows = summarize_mde(fpr_rows, tpr_rows)
    leg_rows = summarize_leg_pass_rates(verdict_rows)
    # Success for this keystone is *producing* the operating-characteristic map
    # (design section 11), not every cell passing. Per-cell PASS / FAIL_FPR /
    # INCONCLUSIVE_* verdicts live in mde_summary.csv; an underpowered 4h cell is
    # a first-class measured result, not a run failure. Downstream EXP-004 gates
    # on the MDE artifact existing, not on this status being PASS.
    measurements_produced = bool(fpr_rows) and bool(tpr_rows) and bool(mde_rows)
    overall_status = "COMPLETE" if measurements_produced else "INCONCLUSIVE"
    mde_status_counts: dict[str, int] = {}
    for row in mde_rows:
        mde_status_counts[row["status"]] = mde_status_counts.get(row["status"], 0) + 1

    write_rows(RESULTS_DIR / "analysis_metadata.csv", analysis_rows)
    write_rows(RESULTS_DIR / "draw_verdicts.csv", verdict_rows)
    write_rows(RESULTS_DIR / "fpr_summary.csv", fpr_rows)
    write_rows(RESULTS_DIR / "tpr_summary.csv", tpr_rows)
    write_rows(RESULTS_DIR / "mde_summary.csv", mde_rows)
    write_rows(RESULTS_DIR / "leg_pass_rates.csv", leg_rows)
    write_json(
        RESULTS_DIR / "run_metadata.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "overall_status": overall_status,
            "measurements_produced": measurements_produced,
            "mde_cells": len(mde_rows),
            "mde_status_counts": mde_status_counts,
            "null_draws_per_generator": NULL_DRAWS_PER_GENERATOR,
            "positive_draws_per_edge": POSITIVE_DRAWS_PER_EDGE,
            "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
            "alpha_grid": list(ALPHA_GRID),
            "edge_grid_bps": list(EDGE_GRID_BPS),
        },
    )
    plot_power_curves(tpr_rows)
    plot_mde(mde_rows)
    plot_fpr(fpr_rows)
    plot_leg_pass_rates(leg_rows)
    plot_effective_sample(verdict_rows)

    LOGGER.info("EXP-003 complete: %s", overall_status)
    LOGGER.info("Results: %s", RESULTS_DIR)


if __name__ == "__main__":
    main()

