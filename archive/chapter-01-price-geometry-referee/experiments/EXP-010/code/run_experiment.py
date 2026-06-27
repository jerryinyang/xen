"""
Experiment EXP-010: Split-Protocol Robustness of the Referee.

Phase 002 optional/context robustness test. Regenerates EXP-003-style known-null
and known-positive draws on the first-70% analysis slice and evaluates the frozen
referees under three within-analysis-set split protocols (single chronological,
anchored walk-forward, purged/embargoed CV). The referee stays frozen; only the
train/test partition changes (see ``split_protocols``). Reports pooled-by-domain
FPR/MDE per protocol, a reference-reproduction consistency check of the
single-split arm against EXP-003, and the frozen material-difference comparison.
Never loads the final 30% global holdout.
"""
from __future__ import annotations

import csv
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
    EDGE_GRID_BPS,
    build_domain_frames,
    cost_bps_for,
    domain_split_index,
    estimate_block_length,
    list_timebar_files,
    load_analysis_data,
    next_log_returns_from_bars,
    permuted_returns,
    plant_positive_edge,
    random_state_positions,
    seed_for,
    wilson_interval,
    write_json,
)

# Experiment-local helper. Insert script dir on path so the import resolves on a
# direct manual run and in spawned mp workers. (xen is installed editable.)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from split_protocols import (  # noqa: E402  (local helper; needs script dir on path)
    PROTOCOLS,
    PURGE_BARS,
    PURGED_CV_FOLDS,
    WALK_FORWARD_FOLDS,
    WALK_FORWARD_WARMUP_FRACTION,
    build_protocol_folds,
    evaluate_partition_referees,
    fold_summary,
)


LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-010"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data"
EXPERIMENT_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
EXP001_METADATA = (
    PROJECT_ROOT / "python" / "experiments" / "EXP-001" / "results" / "run_metadata.json"
)
EXP003_DIR = PROJECT_ROOT / "python" / "experiments" / "EXP-003" / "results"
EXP003_METADATA = EXP003_DIR / "run_metadata.json"
EXP003_MDE = EXP003_DIR / "mde_summary.csv"
EXP003_FPR = EXP003_DIR / "fpr_summary.csv"

# Reduced draw budget held identical across protocols (scope "Draw generation").
NULL_DRAWS_PER_GENERATOR = 250
POSITIVE_DRAWS_PER_EDGE = 250
NULL_GENERATORS: tuple[str, ...] = ("bar_permutation", "random_signal")
POSITIVE_EDGES: tuple[float, ...] = tuple(e for e in EDGE_GRID_BPS if e > 0.0)
BOOTSTRAP_RESAMPLES = 1000

# Carried-forward Phase 001/002 invariants.
ALPHA0 = 0.05
POWER_TARGET = 0.80
FPR_HALF_WIDTH_TARGET = 0.03
TPR_HALF_WIDTH_TARGET = 0.05

# Frozen material-difference criterion (scope). Restated before any result is read.
MATERIAL_ABS_FLOOR_BPS = 0.5
MATERIAL_REL_FRACTION = 0.20

# Parallelism knob: draws are seed-deterministic, so worker count never changes a
# verdict. Override with EXP010_WORKERS.
N_WORKERS = max(1, int(os.environ.get("EXP010_WORKERS", os.cpu_count() or 1)))
TASK_CHUNKSIZE = 8

# Read-only per-cell state installed in each worker by ``_init_worker``.
_WORKER_CELLS: dict[tuple[str, str], dict[str, Any]] = {}

# Streamed verdict-CSV columns (fixed schema; see ``evaluate_partition_referees``).
VERDICT_FIELDNAMES: tuple[str, ...] = (
    "instrument", "domain", "scenario", "generator", "edge_bps", "draw", "protocol",
    "referee", "alpha", "passed", "effect_bps", "ci_lower_bps", "ci_upper_bps",
    "effective_n", "block_length",
)


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
# Dependency gate
# --------------------------------------------------------------------------- #
def require_dependencies() -> dict[str, str]:
    """Fail fast unless EXP-001 PASSED and EXP-003 COMPLETE with its artifacts."""
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
    for artifact in (EXP003_MDE, EXP003_FPR):
        if not artifact.exists():
            raise FileNotFoundError(f"Required EXP-003 artifact missing: {artifact}")
    return {
        "exp001_status": str(exp001.get("overall_status")),
        "exp003_status": str(exp003.get("overall_status")),
    }


# --------------------------------------------------------------------------- #
# Draw construction (mirrors the EXP-003 substrate; namespaced to EXP-010)
# --------------------------------------------------------------------------- #
def _scoped_returns_and_positions(
    task: tuple[str, str, str, str, float, int], returns: Any, cost_bps: float
) -> tuple[Any, Any]:
    """Regenerate one draw's scenario returns and candidate positions.

    Mirrors EXP-003's construction (random-state oracle positions; bar-permutation
    or raw-return nulls; state-aligned planted drift for positives), seeded under
    the EXP-010 namespace. Deterministic in the per-draw seed, so the worker count
    never changes a verdict.
    """
    instrument, domain, scenario, generator, edge_bps, draw = task
    if scenario == "null":
        seed = seed_for(EXPERIMENT_ID, instrument, domain, generator, draw)
        states = random_state_positions(len(returns), seed)
        scoped = permuted_returns(returns, seed + 1) if generator == "bar_permutation" else returns
    else:
        seed = seed_for(EXPERIMENT_ID, instrument, domain, "known_positive", edge_bps, draw)
        states = random_state_positions(len(returns), seed)
        scoped = plant_positive_edge(
            returns, states, net_edge_bps=float(edge_bps), cost_bps=cost_bps
        )
    return scoped, states


def _init_worker(cells: dict[tuple[str, str], dict[str, Any]]) -> None:
    """Pool initializer: install the read-only per-cell state in this worker."""
    global _WORKER_CELLS
    _WORKER_CELLS = cells


def _evaluate_draw_task(task: tuple[str, str, str, str, float, int]) -> list[dict[str, Any]]:
    """Evaluate all three protocols x both referees x alphas for a single draw.

    The per-draw returns/positions are generated once and reused across the three
    protocols (only the partition differs), and the referee bootstrap seed is held
    fixed across protocols so any FPR/MDE difference is attributable to the split
    alone.
    """
    instrument, domain, scenario, generator, edge_bps, draw = task
    cell = _WORKER_CELLS[(instrument, domain)]
    scoped, states = _scoped_returns_and_positions(task, cell["returns"], cell["cost_bps"])
    ref_seed = seed_for(EXPERIMENT_ID, instrument, domain, scenario, generator, edge_bps, draw, "r")
    rows: list[dict[str, Any]] = []
    for protocol in PROTOCOLS:
        base_label = {
            "instrument": instrument,
            "domain": domain,
            "scenario": scenario,
            "generator": generator,
            "edge_bps": edge_bps,
            "draw": draw,
            "protocol": protocol,
        }
        rows.extend(
            evaluate_partition_referees(
                scoped,
                states,
                instrument=instrument,
                domain=domain,
                folds=cell["folds"][protocol],
                alpha_values=ALPHA_GRID,
                n_bootstrap=BOOTSTRAP_RESAMPLES,
                seed=ref_seed,
                base_label=base_label,
            )
        )
    return rows


def build_draw_tasks(instrument: str, domain: str) -> list[tuple[str, str, str, str, float, int]]:
    """Enumerate every null and known-positive draw task for one cell."""
    tasks: list[tuple[str, str, str, str, float, int]] = []
    for generator in NULL_GENERATORS:
        for draw in range(NULL_DRAWS_PER_GENERATOR):
            tasks.append((instrument, domain, "null", generator, 0.0, draw))
    for edge_bps in POSITIVE_EDGES:
        for draw in range(POSITIVE_DRAWS_PER_EDGE):
            tasks.append((instrument, domain, "positive", "known_positive", float(edge_bps), draw))
    return tasks


def _ingest_rows(
    rows: list[dict[str, Any]],
    writer: "csv.DictWriter[str]",
    fpr_counts: dict[tuple[Any, ...], list[int]],
    tpr_counts: dict[tuple[Any, ...], list[int]],
) -> None:
    """Stream verdict rows to disk and fold them into bounded pass-count cells."""
    for row in rows:
        writer.writerow(row)
        passed = 1 if row["passed"] else 0
        if row["scenario"] == "null":
            cell = fpr_counts.setdefault(
                (row["protocol"], row["domain"], row["referee"], float(row["alpha"])), [0, 0]
            )
        elif row["scenario"] == "positive" and float(row["edge_bps"]) > 0.0:
            cell = tpr_counts.setdefault(
                (
                    row["protocol"], row["domain"], row["referee"],
                    float(row["alpha"]), float(row["edge_bps"]),
                ),
                [0, 0],
            )
        else:
            continue
        cell[0] += passed
        cell[1] += 1


def run_and_stream_draws(
    tasks: list[tuple[str, str, str, str, float, int]],
    cell_data: dict[tuple[str, str], dict[str, Any]],
    verdicts_path: Path,
) -> tuple[dict[tuple[Any, ...], list[int]], dict[tuple[Any, ...], list[int]]]:
    """Evaluate all draw tasks, streaming verdicts to disk in bounded batches.

    Each task is a pure, seed-deterministic function of its tuple plus the
    read-only ``cell_data``; ordered ``imap`` preserves task order so the streamed
    CSV is deterministic regardless of worker count. Verdict rows are written
    immediately and folded into bounded FPR/TPR pass-count cells, so the full
    verdict list is never held in memory (scope "bounded/streamed to disk").

    Returns
    -------
    tuple[dict, dict]
        ``(fpr_counts, tpr_counts)``: ``key -> [successes, n]`` pooled-by-domain
        pass counts for the null and positive draws respectively.
    """
    fpr_counts: dict[tuple[Any, ...], list[int]] = {}
    tpr_counts: dict[tuple[Any, ...], list[int]] = {}
    with verdicts_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(VERDICT_FIELDNAMES))
        writer.writeheader()
        if N_WORKERS <= 1:
            _init_worker(cell_data)
            for task in tqdm(tasks, desc="EXP-010 draws (serial)"):
                _ingest_rows(_evaluate_draw_task(task), writer, fpr_counts, tpr_counts)
        else:
            with mp.Pool(
                processes=N_WORKERS, initializer=_init_worker, initargs=(cell_data,)
            ) as pool:
                for rows in tqdm(
                    pool.imap(_evaluate_draw_task, tasks, chunksize=TASK_CHUNKSIZE),
                    total=len(tasks),
                    desc=f"EXP-010 draws (x{N_WORKERS})",
                ):
                    _ingest_rows(rows, writer, fpr_counts, tpr_counts)
    return fpr_counts, tpr_counts


# --------------------------------------------------------------------------- #
# Pooled-by-domain summaries per protocol
# --------------------------------------------------------------------------- #
def _wilson_rate_row(
    group_cols: list[str],
    key: tuple[Any, ...],
    successes: int,
    n: int,
    rate_name: str,
) -> dict[str, Any]:
    """Build one Wilson-interval rate row (schema matches ``verdict_rate_rows``)."""
    center, lower, upper = wilson_interval(successes, n)
    row = dict(zip(group_cols, key, strict=True))
    row.update(
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
    return row


def summarize_fpr(fpr_counts: dict[tuple[Any, ...], list[int]]) -> list[dict[str, Any]]:
    """Pooled FPR per (protocol, domain, referee, alpha) from null-draw counts."""
    cols = ["protocol", "domain", "referee", "alpha"]
    return [
        _wilson_rate_row(cols, key, counts[0], counts[1], "fpr")
        for key, counts in sorted(
            fpr_counts.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]), str(kv[0][2]), float(kv[0][3]))
        )
    ]


def summarize_tpr(tpr_counts: dict[tuple[Any, ...], list[int]]) -> list[dict[str, Any]]:
    """Pooled TPR per (protocol, domain, referee, alpha, edge) from positive-draw counts."""
    cols = ["protocol", "domain", "referee", "alpha", "edge_bps"]
    return [
        _wilson_rate_row(cols, key, counts[0], counts[1], "tpr")
        for key, counts in sorted(
            tpr_counts.items(),
            key=lambda kv: (
                str(kv[0][0]), str(kv[0][1]), str(kv[0][2]), float(kv[0][3]), float(kv[0][4])
            ),
        )
    ]


def grid_half_step(edge_bps: float) -> float:
    """Half the smaller neighbouring gap around ``edge_bps`` (matches EXP-003)."""
    grid = sorted(float(value) for value in EDGE_GRID_BPS)
    if edge_bps not in grid:
        return math.nan
    index = grid.index(edge_bps)
    left = grid[index] - grid[index - 1] if index > 0 else grid[1] - grid[0]
    right = grid[index + 1] - grid[index] if index < len(grid) - 1 else left
    return min(left, right) / 2.0


def summarize_mde(
    fpr_rows: list[dict[str, Any]], tpr_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Gate-stack MDE per (protocol, domain, alpha) using the EXP-003 rule."""
    fpr_idx = {
        (r["protocol"], r["domain"], float(r["alpha"])): r
        for r in fpr_rows
        if r["referee"] == "gate_stack"
    }
    tpr_idx: dict[tuple[Any, Any, float], list[dict[str, Any]]] = {}
    for row in tpr_rows:
        if row["referee"] != "gate_stack":
            continue
        tpr_idx.setdefault((row["protocol"], row["domain"], float(row["alpha"])), []).append(row)

    output: list[dict[str, Any]] = []
    for key in sorted(tpr_idx, key=lambda i: (str(i[0]), str(i[1]), float(i[2]))):
        protocol, domain, alpha = key
        fpr = fpr_idx.get(key)
        mde_bps = math.nan
        grid_uncertainty = math.nan
        tpr_half_width = math.nan
        if fpr is None:
            status = "INCONCLUSIVE_MISSING_FPR"
        elif fpr["wilson_half_width"] > FPR_HALF_WIDTH_TARGET:
            status = "INCONCLUSIVE_FPR_PRECISION"
        elif fpr["fpr"] > alpha:
            status = "FPR_UNCONTROLLED"
        else:
            status = "INCONCLUSIVE_NO_CROSSING"
            for tpr_row in sorted(tpr_idx[key], key=lambda item: float(item["edge_bps"])):
                if (
                    tpr_row["tpr"] >= POWER_TARGET
                    and tpr_row["wilson_half_width"] <= TPR_HALF_WIDTH_TARGET
                ):
                    mde_bps = float(tpr_row["edge_bps"])
                    grid_uncertainty = grid_half_step(mde_bps)
                    tpr_half_width = float(tpr_row["wilson_half_width"])
                    status = "PASS"
                    break
        output.append(
            {
                "protocol": protocol,
                "domain": domain,
                "referee": "gate_stack",
                "alpha": alpha,
                "fpr": fpr["fpr"] if fpr else math.nan,
                "fpr_wilson_half_width": fpr["wilson_half_width"] if fpr else math.nan,
                "mde_bps": mde_bps,
                "mde_grid_uncertainty_bps": grid_uncertainty,
                "tpr_wilson_half_width_at_mde": tpr_half_width,
                "status": status,
            }
        )
    return output


# --------------------------------------------------------------------------- #
# Reference-reproduction check and material-difference comparison
# --------------------------------------------------------------------------- #
def _intervals_overlap(lo1: float, hi1: float, lo2: float, hi2: float) -> bool:
    """True if the two closed intervals overlap."""
    return not (hi1 < lo2 or hi2 < lo1)


def reference_reproduction(
    fpr_rows: list[dict[str, Any]], mde_rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool]:
    """Check the single-split arm reproduces EXP-003 FPR/MDE (statistical consistency).

    Returns
    -------
    tuple[list[dict[str, Any]], bool]
        ``(check_rows, reference_pass)``.
    """
    exp003_fpr_frame = pl.read_csv(EXP003_FPR).filter(pl.col("referee") == "gate_stack")
    exp003_mde_frame = pl.read_csv(EXP003_MDE).filter(pl.col("referee") == "gate_stack")
    exp003_fpr = {
        (r["domain"], float(r["alpha"])): r for r in exp003_fpr_frame.iter_rows(named=True)
    }
    exp003_mde = {
        (r["domain"], float(r["alpha"])): r for r in exp003_mde_frame.iter_rows(named=True)
    }
    single_fpr = {
        (r["domain"], float(r["alpha"])): r
        for r in fpr_rows
        if r["protocol"] == "single" and r["referee"] == "gate_stack"
    }
    single_mde = {
        (r["domain"], float(r["alpha"])): r for r in mde_rows if r["protocol"] == "single"
    }
    rows: list[dict[str, Any]] = []
    overall_pass = True
    for key in sorted(exp003_mde, key=lambda i: (str(i[0]), float(i[1]))):
        domain, alpha = key
        ref_fpr = exp003_fpr.get(key)
        ours_fpr = single_fpr.get(key)
        ref_mde = exp003_mde.get(key)
        ours_mde = single_mde.get(key)
        fpr_ok = bool(
            ref_fpr
            and ours_fpr
            and _intervals_overlap(
                ref_fpr["wilson_lower"], ref_fpr["wilson_upper"],
                ours_fpr["wilson_lower"], ours_fpr["wilson_upper"],
            )
        )
        ref_mde_bps = (
            float(ref_mde["mde_bps"]) if ref_mde and ref_mde["mde_bps"] is not None else math.nan
        )
        ours_mde_bps = float(ours_mde["mde_bps"]) if ours_mde else math.nan
        unc = grid_half_step(ref_mde_bps) if math.isfinite(ref_mde_bps) else math.nan
        band = unc if math.isfinite(unc) else 0.0
        mde_ok = bool(
            math.isfinite(ref_mde_bps)
            and math.isfinite(ours_mde_bps)
            and abs(ours_mde_bps - ref_mde_bps) <= band
        )
        overall_pass = overall_pass and fpr_ok and mde_ok
        rows.append(
            {
                "domain": domain,
                "alpha": alpha,
                "exp003_fpr": ref_fpr["fpr"] if ref_fpr else math.nan,
                "single_fpr": ours_fpr["fpr"] if ours_fpr else math.nan,
                "fpr_consistent": fpr_ok,
                "exp003_mde_bps": ref_mde_bps,
                "single_mde_bps": ours_mde_bps,
                "mde_consistent": mde_ok,
            }
        )
    return rows, bool(overall_pass)


def compare_protocols(
    fpr_rows: list[dict[str, Any]], mde_rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Apply the frozen material criterion to each protocol vs single per domain.

    Returns
    -------
    tuple[list[dict[str, Any]], dict[str, str]]
        ``(comparison_rows, per_domain_hsplit_verdict)`` at alpha0.
    """
    fpr_idx = {
        (r["protocol"], r["domain"]): r
        for r in fpr_rows
        if r["referee"] == "gate_stack" and float(r["alpha"]) == ALPHA0
    }
    mde_idx = {
        (r["protocol"], r["domain"]): r for r in mde_rows if float(r["alpha"]) == ALPHA0
    }
    domains = sorted({d for (_p, d) in mde_idx})
    rows: list[dict[str, Any]] = []
    verdict: dict[str, str] = {}
    for domain in domains:
        single_mde = mde_idx.get(("single", domain))
        single_fpr = fpr_idx.get(("single", domain))
        single_mde_bps = float(single_mde["mde_bps"]) if single_mde else math.nan
        single_mde_reportable = bool(single_mde and single_mde["status"] == "PASS")
        domain_material = False
        domain_evaluable = False
        for protocol in PROTOCOLS:
            if protocol == "single":
                continue
            p_mde = mde_idx.get((protocol, domain))
            p_fpr = fpr_idx.get((protocol, domain))
            p_mde_bps = float(p_mde["mde_bps"]) if p_mde else math.nan
            # MDE materiality requires both single and protocol MDE estimable.
            mde_reportable = bool(
                single_mde_reportable and p_mde and p_mde["status"] == "PASS"
            )
            margin = (
                max(MATERIAL_ABS_FLOOR_BPS, MATERIAL_REL_FRACTION * single_mde_bps)
                if math.isfinite(single_mde_bps)
                else math.nan
            )
            mde_material = bool(
                mde_reportable and abs(p_mde_bps - single_mde_bps) >= margin
            )
            # FPR materiality is INDEPENDENT of MDE reportability (frozen criterion
            # is an OR of three sub-conditions). It is gated only on FPR precision
            # (D-prec), so an uncontrolled or shifted FPR is flagged even when the
            # protocol's MDE is not estimable (e.g. status FPR_UNCONTROLLED).
            fpr_precise = bool(
                single_fpr
                and p_fpr
                and single_fpr["wilson_half_width"] <= FPR_HALF_WIDTH_TARGET
                and p_fpr["wilson_half_width"] <= FPR_HALF_WIDTH_TARGET
            )
            fpr_disjoint = bool(
                single_fpr
                and p_fpr
                and not _intervals_overlap(
                    single_fpr["wilson_lower"], single_fpr["wilson_upper"],
                    p_fpr["wilson_lower"], p_fpr["wilson_upper"],
                )
            )
            fpr_uncontrolled = bool(p_fpr and p_fpr["wilson_lower"] > ALPHA0)
            fpr_material = bool(fpr_precise and (fpr_disjoint or fpr_uncontrolled))
            material = bool(mde_material or fpr_material)
            evaluable = bool(mde_reportable or fpr_precise)
            domain_material = domain_material or material
            domain_evaluable = domain_evaluable or evaluable
            rows.append(
                {
                    "domain": domain,
                    "protocol": protocol,
                    "alpha": ALPHA0,
                    "single_mde_bps": single_mde_bps,
                    "protocol_mde_bps": p_mde_bps,
                    "delta_mde_bps": (
                        (p_mde_bps - single_mde_bps) if mde_reportable else math.nan
                    ),
                    "margin_bps": margin,
                    "single_fpr": single_fpr["fpr"] if single_fpr else math.nan,
                    "protocol_fpr": p_fpr["fpr"] if p_fpr else math.nan,
                    "mde_reportable": mde_reportable,
                    "fpr_precise": fpr_precise,
                    "mde_material": mde_material,
                    "fpr_disjoint": fpr_disjoint,
                    "fpr_uncontrolled": fpr_uncontrolled,
                    "fpr_material": fpr_material,
                    "material": material,
                    "evaluable": evaluable,
                }
            )
        # FALSIFIED if any alternative protocol is material (via MDE or FPR);
        # SUPPORTED if at least one comparison was assessable with usable
        # precision and none was material; else INCONCLUSIVE.
        if domain_material:
            verdict[domain] = "FALSIFIED"
        elif domain_evaluable:
            verdict[domain] = "SUPPORTED"
        else:
            verdict[domain] = "INCONCLUSIVE"
    return rows, verdict


# --------------------------------------------------------------------------- #
# Plotting (bounded summary inputs only)
# --------------------------------------------------------------------------- #
def plot_mde_by_protocol(
    mde_rows: list[dict[str, Any]], comparison_rows: list[dict[str, Any]]
) -> None:
    """Gate MDE per protocol, faceted by domain, with single-split margin band."""
    pdf = pl.DataFrame(mde_rows).filter(pl.col("alpha") == ALPHA0).to_pandas()
    cmp = pl.DataFrame(comparison_rows).to_pandas() if comparison_rows else None
    domains = sorted(pdf["domain"].unique())
    fig, axes = plt.subplots(1, len(domains), figsize=(5 * len(domains), 5), sharey=False)
    axes = axes if len(domains) > 1 else [axes]
    for ax, domain in zip(axes, domains):
        sub = pdf[pdf["domain"] == domain].set_index("protocol").reindex(PROTOCOLS)
        ax.bar(range(len(PROTOCOLS)), sub["mde_bps"], color="steelblue")
        single = sub.loc["single", "mde_bps"] if "single" in sub.index else math.nan
        if cmp is not None and math.isfinite(single):
            margin = cmp[cmp["domain"] == domain]["margin_bps"]
            margin = float(margin.iloc[0]) if len(margin) else math.nan
            if math.isfinite(margin):
                ax.axhspan(
                    single - margin, single + margin, color="grey", alpha=0.2, label="margin"
                )
            ax.axhline(single, color="black", linewidth=1, label="single")
        ax.set_xticks(range(len(PROTOCOLS)), PROTOCOLS, rotation=30, ha="right", fontsize=8)
        ax.set_title(str(domain))
        ax.set_ylabel("Gate MDE (bps)")
        ax.legend(fontsize=7)
    fig.suptitle("Gate MDE by split protocol at alpha=0.05")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "mde_by_protocol.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_fpr_by_protocol(fpr_rows: list[dict[str, Any]]) -> None:
    """Gate FPR per protocol at alpha0, faceted by domain, with the alpha0 line."""
    pdf = pl.DataFrame(fpr_rows).filter(
        (pl.col("alpha") == ALPHA0) & (pl.col("referee") == "gate_stack")
    ).to_pandas()
    domains = sorted(pdf["domain"].unique())
    fig, axes = plt.subplots(1, len(domains), figsize=(5 * len(domains), 5), sharey=True)
    axes = axes if len(domains) > 1 else [axes]
    for ax, domain in zip(axes, domains):
        sub = pdf[pdf["domain"] == domain].set_index("protocol").reindex(PROTOCOLS)
        yerr = sub["wilson_half_width"].to_numpy()
        ax.bar(range(len(PROTOCOLS)), sub["fpr"], yerr=yerr, capsize=3, color="steelblue")
        ax.axhline(ALPHA0, color="red", linewidth=1, label="alpha0 = 0.05")
        ax.set_xticks(range(len(PROTOCOLS)), PROTOCOLS, rotation=30, ha="right", fontsize=8)
        ax.set_title(str(domain))
        ax.legend(fontsize=7)
    axes[0].set_ylabel("Gate FPR")
    fig.suptitle("Gate FPR by split protocol at alpha=0.05")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "fpr_by_protocol.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_tpr_curves(tpr_rows: list[dict[str, Any]]) -> None:
    """Gate TPR vs planted edge per protocol at alpha0, faceted by domain."""
    pdf = pl.DataFrame(tpr_rows).filter(
        (pl.col("alpha") == ALPHA0) & (pl.col("referee") == "gate_stack")
    ).to_pandas()
    domains = sorted(pdf["domain"].unique())
    fig, axes = plt.subplots(1, len(domains), figsize=(5 * len(domains), 5), sharey=True)
    axes = axes if len(domains) > 1 else [axes]
    for ax, domain in zip(axes, domains):
        sub = pdf[pdf["domain"] == domain]
        for protocol, group in sub.groupby("protocol"):
            group = group.sort_values("edge_bps")
            ax.plot(group["edge_bps"], group["tpr"], marker=".", label=str(protocol))
        ax.axhline(POWER_TARGET, color="black", linewidth=1)
        ax.set_xscale("log")
        ax.set_xlabel("Planted edge (bps, log)")
        ax.set_title(str(domain))
    axes[0].set_ylabel("Gate TPR")
    axes[-1].legend(fontsize=7, title="protocol")
    fig.suptitle("Gate TPR vs planted edge by split protocol at alpha=0.05")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "tpr_curves_by_protocol.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_material_matrix(
    comparison_rows: list[dict[str, Any]], reference_pass: bool
) -> None:
    """Protocol x domain material-flag matrix annotated with the reference-check status."""
    pdf = pl.DataFrame(comparison_rows).to_pandas()
    pivot = pdf.pivot_table(
        index="protocol", columns="domain", values="material", aggfunc="max"
    ).astype(float)
    fig, ax = plt.subplots(figsize=(7, 4))
    im = ax.imshow(pivot.values, aspect="auto", cmap="RdYlGn_r", vmin=0, vmax=1)
    ax.set_xticks(range(len(pivot.columns)), list(pivot.columns))
    ax.set_yticks(range(len(pivot.index)), list(pivot.index))
    for r in range(pivot.shape[0]):
        for c in range(pivot.shape[1]):
            text = "MAT" if pivot.values[r, c] >= 0.5 else "ok"
            ax.text(c, r, text, ha="center", va="center", fontsize=8)
    ref_status = "PASS" if reference_pass else "FAIL"
    ax.set_title(f"Material vs single (reference reproduction: {ref_status})")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "material_flag_matrix.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _mapped_fold_edges(
    base_times: np.ndarray, aligned_times: np.ndarray, fractions: np.ndarray, n: int
) -> list[int]:
    """Map canonical 1-minute ``CloseTime`` boundary fractions into domain indices.

    A boundary at fraction ``f`` is the timestamp of 1-minute base row
    ``floor(f * n_base)`` (the canonical shared reference, exactly as the mandated
    70/30 train/test boundary is derived); that timestamp is mapped into this
    domain by counting domain return rows at or before it — identical to
    ``domain_split_index``. This keeps fold boundaries shared across domains as
    ``CloseTime`` timestamps (design section 7), never per-timeframe row fractions.

    Returns a monotone list of domain row indices in ``[0, n]``.
    """
    n_base = len(base_times)
    edges: list[int] = []
    for fraction in fractions:
        if fraction <= 0.0:
            edges.append(0)
            continue
        if fraction >= 1.0:
            edges.append(n)
            continue
        base_pos = min(int(fraction * n_base), n_base - 1)
        boundary_ts = base_times[base_pos]
        index = int(np.count_nonzero(aligned_times <= boundary_ts))
        edges.append(max(0, min(index, n)))
    return edges


def build_cells_and_tasks(
    files: list[Path],
) -> tuple[
    dict[tuple[str, str], dict[str, Any]],
    list[tuple[str, str, str, str, float, int]],
    list[dict[str, Any]],
]:
    """Load holdout-safe slices, build domains + protocol folds, enumerate draws.

    Fold boundaries (single split, walk-forward warmup + tiling, purged-CV folds)
    are timestamp-mapped from the shared 1-minute ``CloseTime`` base into each
    domain (never per-timeframe row fractions). The purged-CV embargo is the block
    length of the real domain returns (draw-independent), so all protocol folds are
    cell-level and reused across every draw and protocol.
    """
    walk_forward_fractions = np.linspace(
        WALK_FORWARD_WARMUP_FRACTION, 1.0, WALK_FORWARD_FOLDS + 1
    )
    purged_cv_fractions = np.linspace(0.0, 1.0, PURGED_CV_FOLDS + 1)

    cell_data: dict[tuple[str, str], dict[str, Any]] = {}
    tasks: list[tuple[str, str, str, str, float, int]] = []
    analysis_rows: list[dict[str, Any]] = []
    for path in tqdm(files, desc="EXP-010 load/domains"):
        data = load_analysis_data(path)
        base_times = data.frame.get_column("CloseTime").cast(pl.Int64).to_numpy()
        for domain, frame in build_domain_frames(data.frame).items():
            returns, aligned = next_log_returns_from_bars(frame)
            n = len(returns)
            aligned_times = aligned.get_column("CloseTime").cast(pl.Int64).to_numpy()
            split_index = domain_split_index(aligned, data.train_end_ts)
            embargo = max(1, estimate_block_length(returns))
            walk_forward_edges = _mapped_fold_edges(
                base_times, aligned_times, walk_forward_fractions, n
            )
            purged_cv_edges = _mapped_fold_edges(
                base_times, aligned_times, purged_cv_fractions, n
            )
            folds = build_protocol_folds(
                n,
                split_index=split_index,
                walk_forward_edges=walk_forward_edges,
                purged_cv_edges=purged_cv_edges,
                embargo=embargo,
            )
            cell_data[(data.instrument, domain)] = {
                "returns": returns,
                "cost_bps": cost_bps_for(data.instrument, domain),
                "folds": folds,
            }
            analysis_rows.append(
                {
                    "instrument": data.instrument,
                    "source_file": data.source_file,
                    "domain": domain,
                    "domain_rows": frame.height,
                    "return_rows": n,
                    "split_index": split_index,
                    "embargo_bars": embargo,
                    "walk_forward_edges": json.dumps(walk_forward_edges),
                    "purged_cv_edges": json.dumps(purged_cv_edges),
                    "folds": fold_summary(folds),
                    "train_end": data.train_end,
                    "analysis_start": data.analysis_start,
                    "analysis_end": data.analysis_end,
                }
            )
            tasks.extend(build_draw_tasks(data.instrument, domain))
    return cell_data, tasks, analysis_rows


def main() -> None:
    """Run the EXP-010 split-protocol robustness measurement and write outputs."""
    configure_logging()
    ensure_output_dirs()
    dependency_status = require_dependencies()

    files = list_timebar_files(DATA_DIR)
    if not files:
        raise FileNotFoundError(f"No time-bar files found under {DATA_DIR / 'timebars'}")

    cell_data, tasks, analysis_rows = build_cells_and_tasks(files)
    if not tasks:
        raise RuntimeError("No draw tasks were enumerated")

    verdicts_path = RESULTS_DIR / "protocol_draw_verdicts.csv"
    fpr_counts, tpr_counts = run_and_stream_draws(tasks, cell_data, verdicts_path)

    fpr_rows = summarize_fpr(fpr_counts)
    tpr_rows = summarize_tpr(tpr_counts)
    mde_rows = summarize_mde(fpr_rows, tpr_rows)
    reference_rows, reference_pass = reference_reproduction(fpr_rows, mde_rows)
    comparison_rows, hsplit_verdict = compare_protocols(fpr_rows, mde_rows)

    measurements_produced = bool(fpr_rows) and bool(tpr_rows) and bool(mde_rows)
    overall_status = (
        "COMPLETE" if measurements_produced and reference_pass else "FAILED_REPRODUCTION"
    )

    write_rows(RESULTS_DIR / "analysis_metadata.csv", analysis_rows)
    write_rows(RESULTS_DIR / "protocol_fpr_summary.csv", fpr_rows)
    write_rows(RESULTS_DIR / "protocol_mde_summary.csv", mde_rows)
    write_rows(RESULTS_DIR / "protocol_comparison.csv", comparison_rows)
    write_rows(RESULTS_DIR / "reference_reproduction_check.csv", reference_rows)
    write_json(
        RESULTS_DIR / "run_metadata.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "overall_status": overall_status,
            "measurements_produced": measurements_produced,
            "reference_reproduction_pass": reference_pass,
            "hsplit_verdict_by_domain": hsplit_verdict,
            "dependencies": dependency_status,
            "protocols": list(PROTOCOLS),
            "walk_forward_folds": WALK_FORWARD_FOLDS,
            "walk_forward_warmup_fraction": WALK_FORWARD_WARMUP_FRACTION,
            "purged_cv_folds": PURGED_CV_FOLDS,
            "purge_bars": PURGE_BARS,
            "fold_boundary_source": "shared_1m_closetime_mapped_per_domain",
            "multi_fold_aggregation": "per_fold_disjoint_pooled_oos",
            "null_draws_per_generator": NULL_DRAWS_PER_GENERATOR,
            "positive_draws_per_edge": POSITIVE_DRAWS_PER_EDGE,
            "null_generators": list(NULL_GENERATORS),
            "positive_edges_bps": list(POSITIVE_EDGES),
            "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
            "alpha_grid": list(ALPHA_GRID),
            "alpha0": ALPHA0,
            "power_target": POWER_TARGET,
            "material_abs_floor_bps": MATERIAL_ABS_FLOOR_BPS,
            "material_rel_fraction": MATERIAL_REL_FRACTION,
            "n_workers": N_WORKERS,
        },
    )

    plot_mde_by_protocol(mde_rows, comparison_rows)
    plot_fpr_by_protocol(fpr_rows)
    plot_tpr_curves(tpr_rows)
    plot_material_matrix(comparison_rows, reference_pass)

    LOGGER.info("EXP-010 complete: %s", overall_status)
    LOGGER.info("Reference reproduction of EXP-003 single split: %s", reference_pass)
    LOGGER.info("H-split verdict by domain: %s", hsplit_verdict)
    LOGGER.info("Results: %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
