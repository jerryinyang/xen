"""
Experiment EXP-012: Fresh-Draw Loose Referee Ratification (Track A spine).

Re-measures the EXP-011-recommended loose operating point (tau multipliers
0.75 / 0.25 / 0.5 on 5m / 1h / 4h) on FRESH synthetic draws -- new known-null and
known-positive seeds, disjoint from every Phase 001/002 draw, generated on the
SAME first-70% analysis slice of real prices (D-fresh: fresh = new seeds, not new
data; the final 30% global holdout is never loaded). The fixed tau point is
predeclared before the fresh draws are generated; the fresh draws CONFIRM its
operating characteristics, they never re-select tau.

Per domain the loose point is ADOPTED iff all predeclared conditions hold at
alpha0=0.05 and D-prec precision: (1) fresh gate FPR <= alpha0; (2) fresh MDE
within one edge-grid step of the Phase 002 MDE; (3) fresh sub-material pass rate at
the operating MDE within +/-0.10 of the Phase 002 value and <= 0.50. The 4h domain
additionally requires the single chronological split and an anchored walk-forward
K=5 protocol (corrected EXP-010 pooled-OOS estimator) to agree (MDEs within one
grid step, both FPR <= alpha0). Otherwise the domain falls back to strict.

The frozen ``xen.referee_calibration`` harness is reused unchanged; only the L5
threshold is swept to derive the loose verdict (see ``loose_referee``). Manual
execution gate: do not run inside the pipeline.
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
    EDGE_GRID_BPS,
    build_domain_frames,
    cost_bps_for,
    domain_split_index,
    gate_stack_core,
    list_timebar_files,
    load_analysis_data,
    materiality_bps_for,
    next_log_returns_from_bars,
    permuted_returns,
    plant_positive_edge,
    random_state_positions,
    seed_for,
    wilson_interval,
    write_json,
)

# Experiment-local helper. Insert script dir on path so the import resolves on a
# direct manual run and in spawned mp workers (xen is installed editable).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from loose_referee import (  # noqa: E402  (local helper; needs script dir on path)
    WALK_FORWARD_FOLDS,
    WALK_FORWARD_WARMUP_FRACTION,
    evaluate_partition_gate,
    gate_verdict_rows,
    mapped_fold_edges,
    single_split_folds,
    walk_forward_folds,
)

LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants & paths
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-012"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data"
EXPERIMENTS_DIR = PROJECT_ROOT / "python" / "experiments"
EXPERIMENT_DIR = EXPERIMENTS_DIR / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"


def _results(exp: str) -> Path:
    return EXPERIMENTS_DIR / exp / "results"


EXP001_META = _results("EXP-001") / "run_metadata.json"
EXP003_META = _results("EXP-003") / "run_metadata.json"
EXP010_META = _results("EXP-010") / "run_metadata.json"
EXP011_META = _results("EXP-011") / "run_metadata.json"
EXP011_RECOMMENDATION = _results("EXP-011") / "recommendation.csv"

# Fresh-draw discipline (D-fresh). The "fresh" salt makes every EXP-012 generator
# seed disjoint from the EXP-003 / EXP-010 draw seeds; disjointness is verified at
# runtime against those experiments' draw grids and recorded in run_metadata.json.
FRESH_SALT = "fresh"
PRIOR_PHASE_NAMESPACES: tuple[str, ...] = (
    "EXP-001", "EXP-002", "EXP-003", "EXP-005", "EXP-006", "EXP-007", "EXP-010",
)

# Draw budget -- matches the EXP-003/EXP-005 precision so the fresh MDE is
# comparable to the Phase 002 value (D-prec).
NULL_DRAWS_PER_GENERATOR = 500
POSITIVE_DRAWS_PER_EDGE = 500
NULL_GENERATORS: tuple[str, ...] = ("bar_permutation", "random_signal")
POSITIVE_EDGES: tuple[float, ...] = tuple(e for e in EDGE_GRID_BPS if e > 0.0)
BOOTSTRAP_RESAMPLES = 1000

# Carried-forward Phase 001/002 invariants (D-invariants / D-prec).
ALPHA0 = 0.05
DOMAINS: tuple[str, ...] = ("5m", "1h", "4h")
POWER_TARGET = 0.80
FPR_HALF_WIDTH_TARGET = 0.03
TPR_HALF_WIDTH_TARGET = 0.05

# Predeclared adoption thresholds (D-ratify-point / D-ratify-4h). Frozen before any
# fresh measurement is read.
SUBMATERIAL_TOL = 0.10        # |fresh_sub - phase002_sub| must be <= this
SUBMATERIAL_CEILING = 0.50    # fresh_sub must not exceed this (EXP-007 cutoff)
MDE_GRID_STEP_TOL = 1         # fresh MDE must be within this many edge-grid steps

# The 4h domain is the only one with the additional split-sensitivity gate.
SPLIT_GATE_DOMAIN = "4h"
SPLIT_PROTOCOLS: tuple[str, ...] = ("single", "walk_forward")

# Parallelism: draws are seed-deterministic, so worker count never changes a
# verdict. Override with EXP012_WORKERS.
N_WORKERS = max(1, int(os.environ.get("EXP012_WORKERS", os.cpu_count() or 1)))
TASK_CHUNKSIZE = 16

_WORKER_CELLS: dict[tuple[str, str], dict[str, Any]] = {}
_WORKER_TAU_BPS: dict[str, float] = {}


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
# Dependency gate + fixed-point manifest (Step 1)
# --------------------------------------------------------------------------- #
def _require(meta_path: Path, exp: str, *, status: str, extra_true: str | None = None) -> dict[str, Any]:
    """Load an upstream metadata file and assert its completion token."""
    if not meta_path.exists():
        raise FileNotFoundError(f"{exp} metadata not found: {meta_path}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("overall_status") != status:
        raise RuntimeError(f"{exp} overall_status != {status}: {meta.get('overall_status')}")
    if extra_true is not None and not meta.get(extra_true):
        raise RuntimeError(f"{exp} missing/false flag {extra_true!r}")
    return meta


def load_operating_points() -> dict[str, dict[str, float]]:
    """Load the predeclared per-domain loose operating point + Phase 002 references.

    The operating tau multiplier, the Phase 002 MDE, and the Phase 002 sub-material
    rate are read from EXP-011's frozen ``recommendation.csv`` -- the point is fixed
    going in, the fresh draws only confirm it. Returns one record per domain with
    ``tau_multiplier``, ``tau_bps`` (= multiplier * materiality), ``phase002_mde_bps``
    and ``phase002_sub_rate``.
    """
    frame = pl.read_csv(EXP011_RECOMMENDATION)
    points: dict[str, dict[str, float]] = {}
    for record in frame.iter_rows(named=True):
        domain = record["domain"]
        if domain not in DOMAINS:
            continue
        materiality = materiality_bps_for(domain)
        multiplier = float(record["tau_star_headline"])
        points[domain] = {
            "tau_multiplier": multiplier,
            "tau_bps": multiplier * materiality,
            "materiality_bps": materiality,
            "phase002_mde_bps": float(record["mde_bps"]),
            "phase002_sub_rate": float(record["sub_rate"]),
        }
    missing = [d for d in DOMAINS if d not in points]
    if missing:
        raise RuntimeError(f"EXP-011 recommendation.csv missing domains: {missing}")
    return points


def gate_dependencies() -> dict[str, str]:
    """Hard-gate every upstream dependency the ratification consumes."""
    tokens = {
        "EXP-001": _require(EXP001_META, "EXP-001", status="PASS")["overall_status"],
        "EXP-003": _require(EXP003_META, "EXP-003", status="COMPLETE")["overall_status"],
        "EXP-010": _require(
            EXP010_META, "EXP-010", status="COMPLETE", extra_true="reference_reproduction_pass"
        )["overall_status"],
        "EXP-011": _require(EXP011_META, "EXP-011", status="COMPLETE")["overall_status"],
    }
    return tokens


# --------------------------------------------------------------------------- #
# Fresh-seed construction + disjointness verification (D-fresh)
# --------------------------------------------------------------------------- #
def fresh_null_seed(instrument: str, domain: str, generator: str, draw: int) -> int:
    """Fresh construction seed for one known-null draw (EXP-012 namespace + salt)."""
    return seed_for(EXPERIMENT_ID, FRESH_SALT, instrument, domain, generator, draw)


def fresh_positive_seed(instrument: str, domain: str, edge_bps: float, draw: int) -> int:
    """Fresh construction seed for one known-positive draw."""
    return seed_for(EXPERIMENT_ID, FRESH_SALT, instrument, domain, "known_positive", edge_bps, draw)


def ref_seed(task: tuple[str, str, str, str, float, int]) -> int:
    """Fresh bootstrap seed for one draw's referee evaluation."""
    instrument, domain, scenario, generator, edge_bps, draw = task
    return seed_for(EXPERIMENT_ID, FRESH_SALT, instrument, domain, scenario, generator, edge_bps, draw, "ref")


def _seed_payload(*parts: object) -> str:
    """Canonical seed payload string (mirrors ``xen.referee_calibration.seed_for``)."""
    return "|".join(str(part) for part in parts)


def verify_seed_disjointness(
    tasks: list[tuple[str, str, str, str, float, int]]
) -> dict[str, Any]:
    """Confirm the fresh seed *construction inputs* are disjoint from Phase 001/002.

    D-fresh requires the ratification draws to be generated from seed inputs never used
    to pick the operating point. The binding, auditable guarantee is therefore that no
    fresh seed *payload* (the namespaced string fed to ``seed_for``) equals any prior
    phase payload -- the ``fresh`` salt makes this hold by construction, so the
    adoption is confirmed on randomness disjoint from what selected the point.

    ``seed_for`` truncates SHA-256 to 32 bits, so a small number of *different* payloads
    inevitably collide to the same integer purely by the birthday paradox
    (~|fresh| * |prior| / 2**32). Those collisions are between disjoint inputs, are NOT
    seed reuse, and -- at ~7 of 66,000 fresh draws -- are statistically immaterial to
    the pooled per-cell FPR/MDE. They are reported as a benign diagnostic, never a
    failure; only a genuine payload-input overlap fails the gate.
    """
    fresh_payloads: set[str] = set()
    prior_payloads: set[str] = set()
    fresh_seeds: set[int] = set()
    prior_seeds: set[int] = set()
    for instrument, domain, scenario, generator, edge_bps, draw in tasks:
        if scenario == "null":
            fresh_payloads.add(_seed_payload(EXPERIMENT_ID, FRESH_SALT, instrument, domain, generator, draw))
            fresh_seeds.add(fresh_null_seed(instrument, domain, generator, draw))
            for ns in PRIOR_PHASE_NAMESPACES:
                prior_payloads.add(_seed_payload(ns, instrument, domain, generator, draw))
                prior_seeds.add(seed_for(ns, instrument, domain, generator, draw))
        else:
            fresh_payloads.add(
                _seed_payload(EXPERIMENT_ID, FRESH_SALT, instrument, domain, "known_positive", float(edge_bps), draw)
            )
            fresh_seeds.add(fresh_positive_seed(instrument, domain, float(edge_bps), draw))
            for ns in PRIOR_PHASE_NAMESPACES:
                prior_payloads.add(
                    _seed_payload(ns, instrument, domain, "known_positive", float(edge_bps), draw)
                )
                prior_seeds.add(seed_for(ns, instrument, domain, "known_positive", float(edge_bps), draw))
    payload_overlap = fresh_payloads & prior_payloads
    int_overlap = fresh_seeds & prior_seeds
    expected_int_collisions = len(fresh_seeds) * len(prior_seeds) / float(2 ** 32)
    return {
        "fresh_namespace": f"{EXPERIMENT_ID}|{FRESH_SALT}",
        "prior_namespaces": list(PRIOR_PHASE_NAMESPACES),
        "fresh_seed_count": len(fresh_seeds),
        "prior_seed_count": len(prior_seeds),
        "payload_overlap_count": len(payload_overlap),
        "benign_int_collision_count": len(int_overlap),
        "expected_int_collisions": expected_int_collisions,
        "seed_space_bits": 32,
        "disjoint": len(payload_overlap) == 0,
    }


# --------------------------------------------------------------------------- #
# Draw construction (mirrors the EXP-003 substrate; fresh EXP-012 seeds)
# --------------------------------------------------------------------------- #
def _scoped_returns_and_positions(
    task: tuple[str, str, str, str, float, int], returns: np.ndarray, cost_bps: float
) -> tuple[np.ndarray, np.ndarray]:
    """Regenerate one draw's scenario returns and candidate positions (fresh seed)."""
    instrument, domain, scenario, generator, edge_bps, draw = task
    if scenario == "null":
        seed = fresh_null_seed(instrument, domain, generator, draw)
        states = random_state_positions(len(returns), seed)
        scoped = permuted_returns(returns, seed + 1) if generator == "bar_permutation" else returns
    else:
        seed = fresh_positive_seed(instrument, domain, float(edge_bps), draw)
        states = random_state_positions(len(returns), seed)
        scoped = plant_positive_edge(returns, states, net_edge_bps=float(edge_bps), cost_bps=cost_bps)
    return scoped, states


def build_draw_tasks(instrument: str, domain: str) -> list[tuple[str, str, str, str, float, int]]:
    """Enumerate every fresh null and known-positive draw task for one cell."""
    tasks: list[tuple[str, str, str, str, float, int]] = []
    for generator in NULL_GENERATORS:
        for draw in range(NULL_DRAWS_PER_GENERATOR):
            tasks.append((instrument, domain, "null", generator, 0.0, draw))
    for edge_bps in POSITIVE_EDGES:
        for draw in range(POSITIVE_DRAWS_PER_EDGE):
            tasks.append((instrument, domain, "positive", "known_positive", float(edge_bps), draw))
    return tasks


def _init_worker(cells: dict[tuple[str, str], dict[str, Any]], tau_bps: dict[str, float]) -> None:
    """Pool initializer: install read-only per-cell state and tau thresholds."""
    global _WORKER_CELLS, _WORKER_TAU_BPS
    _WORKER_CELLS = cells
    _WORKER_TAU_BPS = tau_bps


def _evaluate_draw_task(task: tuple[str, str, str, str, float, int]) -> list[dict[str, Any]]:
    """Single-split loose + strict gate verdicts for one fresh draw (all alphas)."""
    instrument, domain, scenario, generator, edge_bps, draw = task
    cell = _WORKER_CELLS[(instrument, domain)]
    scoped, states = _scoped_returns_and_positions(task, cell["returns"], cell["cost_bps"])
    core = gate_stack_core(
        scoped,
        states,
        instrument=instrument,
        domain=domain,
        n_bootstrap=BOOTSTRAP_RESAMPLES,
        seed=ref_seed(task),
        split_index=cell["split_index"],
    )
    base_label = {
        "instrument": instrument,
        "domain": domain,
        "scenario": scenario,
        "generator": generator,
        "edge_bps": edge_bps,
        "draw": draw,
    }
    return gate_verdict_rows(
        core, alpha_values=ALPHA_GRID, tau_bps=_WORKER_TAU_BPS[domain], base_label=base_label
    )


def run_draw_tasks(
    tasks: list[tuple[str, str, str, str, float, int]],
    cell_data: dict[tuple[str, str], dict[str, Any]],
    tau_bps: dict[str, float],
) -> list[dict[str, Any]]:
    """Evaluate every fresh draw (single split), in parallel when ``N_WORKERS > 1``."""
    rows: list[dict[str, Any]] = []
    if N_WORKERS <= 1:
        _init_worker(cell_data, tau_bps)
        for task in tqdm(tasks, desc="EXP-012 draws (serial)"):
            rows.extend(_evaluate_draw_task(task))
        return rows
    with mp.Pool(
        processes=N_WORKERS, initializer=_init_worker, initargs=(cell_data, tau_bps)
    ) as pool:
        for out in tqdm(
            pool.imap_unordered(_evaluate_draw_task, tasks, chunksize=TASK_CHUNKSIZE),
            total=len(tasks),
            desc=f"EXP-012 draws (x{N_WORKERS})",
        ):
            rows.extend(out)
    return rows


# --------------------------------------------------------------------------- #
# Rate / MDE summaries (pooled by domain, like EXP-003)
# --------------------------------------------------------------------------- #
def _wilson_rate_rows(
    frame: pl.DataFrame, *, group_cols: list[str], rate_name: str
) -> list[dict[str, Any]]:
    """Aggregate ``passed`` into a Wilson-interval rate per group (Polars-first)."""
    grouped = frame.group_by(group_cols).agg(
        pl.col("passed").sum().alias("successes"), pl.len().alias("n")
    )
    rows: list[dict[str, Any]] = []
    for record in grouped.sort(group_cols).iter_rows(named=True):
        successes, n = int(record["successes"]), int(record["n"])
        center, lower, upper = wilson_interval(successes, n)
        out = {col: record[col] for col in group_cols}
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


def summarize_fpr(verdicts: pl.DataFrame) -> list[dict[str, Any]]:
    """Pooled FPR per (domain, referee, alpha) from null-scenario draws."""
    nulls = verdicts.filter(pl.col("scenario") == "null")
    return _wilson_rate_rows(nulls, group_cols=["domain", "referee", "alpha"], rate_name="fpr")


def summarize_tpr(verdicts: pl.DataFrame) -> list[dict[str, Any]]:
    """Pooled TPR per (domain, referee, alpha, edge_bps) from positive draws."""
    positives = verdicts.filter((pl.col("scenario") == "positive") & (pl.col("edge_bps") > 0.0))
    return _wilson_rate_rows(
        positives, group_cols=["domain", "referee", "alpha", "edge_bps"], rate_name="tpr"
    )


def grid_index(edge_bps: float) -> int | None:
    """Index of ``edge_bps`` on the sorted positive edge grid, or ``None``."""
    grid = sorted(float(e) for e in POSITIVE_EDGES)
    return grid.index(float(edge_bps)) if float(edge_bps) in grid else None


def grid_half_step(edge_bps: float) -> float:
    """Half the smaller neighbouring gap around ``edge_bps`` (matches EXP-003)."""
    grid = sorted(float(value) for value in EDGE_GRID_BPS)
    if edge_bps not in grid:
        return math.nan
    idx = grid.index(edge_bps)
    left = grid[idx] - grid[idx - 1] if idx > 0 else grid[1] - grid[0]
    right = grid[idx + 1] - grid[idx] if idx < len(grid) - 1 else left
    return min(left, right) / 2.0


def _locate_mde(
    fpr_row: dict[str, Any] | None, tpr_rows: list[dict[str, Any]], alpha: float
) -> tuple[str, float, float]:
    """Smallest precise edge meeting power at controlled, precise FPR (EXP-003 rule)."""
    if fpr_row is None:
        return "INCONCLUSIVE_MISSING_FPR", math.nan, math.nan
    if fpr_row["wilson_half_width"] > FPR_HALF_WIDTH_TARGET:
        return "INCONCLUSIVE_FPR_PRECISION", math.nan, math.nan
    if fpr_row["fpr"] > alpha:
        return "FPR_UNCONTROLLED", math.nan, math.nan
    for tpr_row in sorted(tpr_rows, key=lambda r: float(r["edge_bps"])):
        if tpr_row["tpr"] >= POWER_TARGET and tpr_row["wilson_half_width"] <= TPR_HALF_WIDTH_TARGET:
            return "PASS", float(tpr_row["edge_bps"]), float(tpr_row["wilson_half_width"])
    return "INCONCLUSIVE_NO_CROSSING", math.nan, math.nan


def summarize_mde(
    fpr_rows: list[dict[str, Any]], tpr_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Locate each (domain, referee, alpha) MDE from the pooled FPR/TPR summaries."""
    fpr_idx = {(r["domain"], r["referee"], float(r["alpha"])): r for r in fpr_rows}
    tpr_idx: dict[tuple[str, str, float], list[dict[str, Any]]] = {}
    for r in tpr_rows:
        tpr_idx.setdefault((r["domain"], r["referee"], float(r["alpha"])), []).append(r)
    output: list[dict[str, Any]] = []
    for key in sorted(tpr_idx, key=lambda i: (str(i[0]), str(i[1]), float(i[2]))):
        domain, referee, alpha = key
        status, mde, tpr_hw = _locate_mde(fpr_idx.get(key), tpr_idx[key], alpha)
        fpr_row = fpr_idx.get(key)
        output.append(
            {
                "domain": domain,
                "referee": referee,
                "alpha": alpha,
                "fpr": fpr_row["fpr"] if fpr_row else math.nan,
                "fpr_wilson_half_width": fpr_row["wilson_half_width"] if fpr_row else math.nan,
                "mde_bps": mde,
                "mde_grid_uncertainty_bps": grid_half_step(mde) if math.isfinite(mde) else math.nan,
                "tpr_wilson_half_width_at_mde": tpr_hw,
                "status": status,
            }
        )
    return output


# --------------------------------------------------------------------------- #
# Sub-material reconstruction at the operating MDE (EXP-007 / EXP-011 definition)
# --------------------------------------------------------------------------- #
def submaterial_at_operating_mde(
    verdicts: pl.DataFrame, mde_rows: list[dict[str, Any]], points: dict[str, dict[str, float]]
) -> list[dict[str, Any]]:
    """Fraction of LOOSE positive passes at the operating MDE with effect < materiality.

    Sub-material = fraction of loose-gate-passing positive draws (alpha0) at
    ``edge == fresh loose MDE`` whose net point estimate ``effect_bps`` is below the
    domain materiality buffer (EXP-007 / EXP-011 definition). Zero-baseline (no
    passes) yields a finite ``0.0`` rate, never a percentage of zero.
    """
    mde_lookup = {
        (r["domain"], r["referee"], float(r["alpha"])): r for r in mde_rows
    }
    rows: list[dict[str, Any]] = []
    for domain in DOMAINS:
        materiality = points[domain]["materiality_bps"]
        mde_row = mde_lookup.get((domain, "loose", ALPHA0))
        operating_mde = mde_row["mde_bps"] if mde_row else math.nan
        passing = verdicts.filter(
            (pl.col("domain") == domain)
            & (pl.col("referee") == "loose")
            & (pl.col("alpha") == ALPHA0)
            & (pl.col("scenario") == "positive")
            & (pl.col("passed"))
        )
        if math.isfinite(operating_mde):
            passing = passing.filter(pl.col("edge_bps") == operating_mde)
        else:
            passing = passing.clear()
        pass_count = passing.height
        submaterial_count = (
            int(passing.filter(pl.col("effect_bps") < materiality).height) if pass_count else 0
        )
        sub_rate = (submaterial_count / pass_count) if pass_count else 0.0
        rows.append(
            {
                "domain": domain,
                "operating_mde_bps": operating_mde,
                "materiality_bps": materiality,
                "pass_count": pass_count,
                "submaterial_count": submaterial_count,
                "sub_rate": sub_rate,
                "phase002_sub_rate": points[domain]["phase002_sub_rate"],
            }
        )
    return rows


# --------------------------------------------------------------------------- #
# 4h split-sensitivity gate (single vs anchored walk-forward; corrected estimator)
# --------------------------------------------------------------------------- #
def _split_draw_rows(
    task: tuple[str, str, str, str, float, int],
    cell: dict[str, Any],
    tau_bps: float,
) -> list[dict[str, Any]]:
    """Evaluate the loose+strict gate under each split protocol for one 4h draw."""
    instrument, domain, scenario, generator, edge_bps, draw = task
    scoped, states = _scoped_returns_and_positions(task, cell["returns"], cell["cost_bps"])
    seed = ref_seed(task)
    rows: list[dict[str, Any]] = []
    for protocol in SPLIT_PROTOCOLS:
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
            evaluate_partition_gate(
                scoped,
                states,
                instrument=instrument,
                domain=domain,
                folds=cell["folds"][protocol],
                alpha_values=ALPHA_GRID,
                tau_bps=tau_bps,
                n_bootstrap=BOOTSTRAP_RESAMPLES,
                seed=seed,
                base_label=base_label,
            )
        )
    return rows


def run_split_gate(
    split_cells: dict[str, dict[str, Any]], tau_bps: float
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Run the 4h single-vs-walk-forward loose-gate measurement (serial; 4h is sparse).

    Returns ``(fpr_rows, mde_rows, comparison_rows)`` keyed by protocol. The 4h
    domain has the smallest sample, so this runs serially without a process pool.
    """
    verdict_rows: list[dict[str, Any]] = []
    for instrument, cell in tqdm(split_cells.items(), desc="EXP-012 4h split gate"):
        for task in build_draw_tasks(instrument, SPLIT_GATE_DOMAIN):
            verdict_rows.extend(_split_draw_rows(task, cell, tau_bps))
    verdicts = pl.DataFrame(verdict_rows)

    nulls = verdicts.filter(pl.col("scenario") == "null")
    positives = verdicts.filter((pl.col("scenario") == "positive") & (pl.col("edge_bps") > 0.0))
    fpr_rows = _wilson_rate_rows(
        nulls, group_cols=["protocol", "domain", "referee", "alpha"], rate_name="fpr"
    )
    tpr_rows = _wilson_rate_rows(
        positives, group_cols=["protocol", "domain", "referee", "alpha", "edge_bps"], rate_name="tpr"
    )

    fpr_idx = {
        (r["protocol"], r["referee"], float(r["alpha"])): r for r in fpr_rows
    }
    tpr_idx: dict[tuple[str, str, float], list[dict[str, Any]]] = {}
    for r in tpr_rows:
        tpr_idx.setdefault((r["protocol"], r["referee"], float(r["alpha"])), []).append(r)
    mde_rows: list[dict[str, Any]] = []
    for (protocol, referee, alpha), rows in tpr_idx.items():
        status, mde, tpr_hw = _locate_mde(fpr_idx.get((protocol, referee, alpha)), rows, alpha)
        fpr_row = fpr_idx.get((protocol, referee, alpha))
        mde_rows.append(
            {
                "protocol": protocol,
                "domain": SPLIT_GATE_DOMAIN,
                "referee": referee,
                "alpha": alpha,
                "fpr": fpr_row["fpr"] if fpr_row else math.nan,
                "fpr_wilson_half_width": fpr_row["wilson_half_width"] if fpr_row else math.nan,
                "mde_bps": mde,
                "tpr_wilson_half_width_at_mde": tpr_hw,
                "status": status,
            }
        )

    comparison_rows = _compare_split_protocols(fpr_idx, mde_rows)
    return fpr_rows, mde_rows, comparison_rows


def _compare_split_protocols(
    fpr_idx: dict[tuple[str, str, float], dict[str, Any]], mde_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Apply the predeclared 4h agreement rule (loose referee, alpha0)."""
    mde_idx = {
        (r["protocol"], r["referee"], float(r["alpha"])): r for r in mde_rows
    }
    single = mde_idx.get(("single", "loose", ALPHA0))
    walk = mde_idx.get(("walk_forward", "loose", ALPHA0))
    single_fpr = fpr_idx.get(("single", "loose", ALPHA0))
    walk_fpr = fpr_idx.get(("walk_forward", "loose", ALPHA0))

    single_mde = float(single["mde_bps"]) if single else math.nan
    walk_mde = float(walk["mde_bps"]) if walk else math.nan
    idx_single = grid_index(single_mde) if math.isfinite(single_mde) else None
    idx_walk = grid_index(walk_mde) if math.isfinite(walk_mde) else None
    mde_within_step = (
        idx_single is not None and idx_walk is not None and abs(idx_single - idx_walk) <= MDE_GRID_STEP_TOL
    )
    fpr_ok = bool(
        single_fpr
        and walk_fpr
        and single_fpr["fpr"] <= ALPHA0
        and walk_fpr["fpr"] <= ALPHA0
        and single_fpr["wilson_half_width"] <= FPR_HALF_WIDTH_TARGET
        and walk_fpr["wilson_half_width"] <= FPR_HALF_WIDTH_TARGET
    )
    return [
        {
            "domain": SPLIT_GATE_DOMAIN,
            "referee": "loose",
            "alpha": ALPHA0,
            "single_mde_bps": single_mde,
            "walk_forward_mde_bps": walk_mde,
            "mde_within_one_grid_step": bool(mde_within_step),
            "single_fpr": single_fpr["fpr"] if single_fpr else math.nan,
            "walk_forward_fpr": walk_fpr["fpr"] if walk_fpr else math.nan,
            "both_fpr_controlled_precise": fpr_ok,
            "protocols_agree": bool(mde_within_step and fpr_ok),
        }
    ]


# --------------------------------------------------------------------------- #
# Adoption decision (Step 3 + Step 4)
# --------------------------------------------------------------------------- #
def decide_adoption(
    fpr_rows: list[dict[str, Any]],
    mde_rows: list[dict[str, Any]],
    submaterial_rows: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
    points: dict[str, dict[str, float]],
) -> list[dict[str, Any]]:
    """Per-domain ADOPT_LOOSE / STRICT_FALLBACK / INCONCLUSIVE decision at alpha0.

    Applies the frozen checkpoint adoption rule (D-ratify-point, plus D-ratify-4h for
    4h). Every condition's components are recorded so the verdict is auditable.
    """
    fpr_idx = {(r["domain"], r["referee"], float(r["alpha"])): r for r in fpr_rows}
    mde_idx = {(r["domain"], r["referee"], float(r["alpha"])): r for r in mde_rows}
    sub_idx = {r["domain"]: r for r in submaterial_rows}
    split_idx = {r["domain"]: r for r in comparison_rows}

    decisions: list[dict[str, Any]] = []
    for domain in DOMAINS:
        point = points[domain]
        fpr_row = fpr_idx.get((domain, "loose", ALPHA0))
        mde_row = mde_idx.get((domain, "loose", ALPHA0))
        sub_row = sub_idx[domain]

        fresh_fpr = fpr_row["fpr"] if fpr_row else math.nan
        fresh_fpr_hw = fpr_row["wilson_half_width"] if fpr_row else math.nan
        fresh_mde = float(mde_row["mde_bps"]) if mde_row else math.nan
        mde_status = mde_row["status"] if mde_row else "MISSING"
        fresh_sub = sub_row["sub_rate"]
        phase002_mde = point["phase002_mde_bps"]
        phase002_sub = point["phase002_sub_rate"]

        # D-prec precision -> if not met, the domain is under-powered, not forced.
        fpr_precise = bool(fpr_row) and fresh_fpr_hw <= FPR_HALF_WIDTH_TARGET
        mde_precise = mde_status == "PASS" and math.isfinite(fresh_mde)
        underpowered = (not fpr_precise) or (
            mde_status in ("INCONCLUSIVE_FPR_PRECISION", "INCONCLUSIVE_NO_CROSSING", "MISSING")
        )

        cond_fpr = bool(fpr_precise and fresh_fpr <= ALPHA0)
        idx_fresh = grid_index(fresh_mde) if math.isfinite(fresh_mde) else None
        idx_phase002 = grid_index(phase002_mde)
        cond_mde = bool(
            mde_precise
            and idx_fresh is not None
            and idx_phase002 is not None
            and abs(idx_fresh - idx_phase002) <= MDE_GRID_STEP_TOL
        )
        cond_sub = bool(
            abs(fresh_sub - phase002_sub) <= SUBMATERIAL_TOL and fresh_sub <= SUBMATERIAL_CEILING
        )

        split_row = split_idx.get(domain)
        cond_split = bool(split_row["protocols_agree"]) if split_row is not None else True

        if underpowered:
            verdict = "INCONCLUSIVE"
        elif cond_fpr and cond_mde and cond_sub and cond_split:
            verdict = "ADOPT_LOOSE"
        else:
            verdict = "STRICT_FALLBACK"

        decisions.append(
            {
                "domain": domain,
                "tau_multiplier": point["tau_multiplier"],
                "tau_bps": point["tau_bps"],
                "fresh_fpr": fresh_fpr,
                "fresh_fpr_wilson_half_width": fresh_fpr_hw,
                "cond_fpr": cond_fpr,
                "fresh_mde_bps": fresh_mde,
                "phase002_mde_bps": phase002_mde,
                "mde_status": mde_status,
                "cond_mde": cond_mde,
                "fresh_sub_rate": fresh_sub,
                "phase002_sub_rate": phase002_sub,
                "cond_sub": cond_sub,
                "split_protocols_agree": (
                    bool(split_row["protocols_agree"]) if split_row is not None else None
                ),
                "cond_split": cond_split,
                "underpowered": underpowered,
                "verdict": verdict,
            }
        )
    return decisions


# --------------------------------------------------------------------------- #
# Plotting (bounded summary inputs only)
# --------------------------------------------------------------------------- #
def plot_fpr(fpr_rows: list[dict[str, Any]]) -> None:
    """Plot 1 -- fresh FPR with Wilson half-widths by domain/referee at alpha0."""
    pdf = pl.DataFrame(fpr_rows).filter(pl.col("alpha") == ALPHA0).to_pandas()
    pdf = pdf.sort_values(["domain", "referee"])
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(range(len(pdf)), pdf["fpr"], yerr=pdf["wilson_half_width"], capsize=3, color="steelblue")
    ax.axhline(ALPHA0, color="red", linewidth=1, label="alpha0 = 0.05")
    ax.set_xticks(range(len(pdf)), pdf["domain"] + " " + pdf["referee"], rotation=45, ha="right")
    ax.set_ylabel("Fresh-draw FPR")
    ax.set_title("EXP-012 Plot 1 -- fresh-draw FPR by domain / referee (alpha0)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "fresh_fpr.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_mde_comparison(mde_rows: list[dict[str, Any]], points: dict[str, dict[str, float]]) -> None:
    """Plot 2 -- Phase 002 vs fresh loose MDE by domain with one-grid-step bands."""
    loose = [r for r in mde_rows if r["referee"] == "loose" and float(r["alpha"]) == ALPHA0]
    loose = sorted(loose, key=lambda r: list(DOMAINS).index(r["domain"]))
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(loose))
    fresh = [r["mde_bps"] for r in loose]
    phase002 = [points[r["domain"]]["phase002_mde_bps"] for r in loose]
    ax.bar(x - 0.2, phase002, width=0.4, label="Phase 002 MDE", color="grey")
    ax.bar(x + 0.2, fresh, width=0.4, label="fresh MDE", color="steelblue")
    ax.set_xticks(x, [r["domain"] for r in loose])
    ax.set_ylabel("Economic MDE (bps)")
    ax.set_title("EXP-012 Plot 2 -- Phase 002 vs fresh loose MDE (alpha0)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "mde_comparison.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_submaterial(submaterial_rows: list[dict[str, Any]]) -> None:
    """Plot 3 -- fresh vs Phase 002 sub-material rate with +/-0.10 band and 0.50 ceiling."""
    rows = sorted(submaterial_rows, key=lambda r: list(DOMAINS).index(r["domain"]))
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(rows))
    fresh = [r["sub_rate"] for r in rows]
    phase002 = [r["phase002_sub_rate"] for r in rows]
    ax.bar(x - 0.2, phase002, width=0.4, label="Phase 002 sub-rate", color="grey")
    ax.bar(x + 0.2, fresh, width=0.4, label="fresh sub-rate", color="darkorange")
    for xi, p in zip(x, phase002):
        ax.fill_between([xi - 0.35, xi + 0.35], p - SUBMATERIAL_TOL, p + SUBMATERIAL_TOL,
                        color="grey", alpha=0.2)
    ax.axhline(SUBMATERIAL_CEILING, color="red", linewidth=1, label="0.50 ceiling")
    ax.set_xticks(x, [r["domain"] for r in rows])
    ax.set_ylabel("Sub-material pass rate at operating MDE")
    ax.set_title("EXP-012 Plot 3 -- sub-material rate vs Phase 002 (+/-0.10 band)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "submaterial_rate.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_split_gate(split_mde_rows: list[dict[str, Any]], split_fpr_rows: list[dict[str, Any]]) -> None:
    """Plot 4 -- 4h single vs walk-forward loose MDE and FPR (split-sensitivity gate)."""
    mde = pl.DataFrame(split_mde_rows).filter(
        (pl.col("referee") == "loose") & (pl.col("alpha") == ALPHA0)
    ).to_pandas()
    fpr = pl.DataFrame(split_fpr_rows).filter(
        (pl.col("referee") == "loose") & (pl.col("alpha") == ALPHA0)
    ).to_pandas()
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    mde = mde.set_index("protocol").reindex(SPLIT_PROTOCOLS)
    axes[0].bar(range(len(SPLIT_PROTOCOLS)), mde["mde_bps"], color="steelblue")
    axes[0].set_xticks(range(len(SPLIT_PROTOCOLS)), SPLIT_PROTOCOLS, rotation=20, ha="right")
    axes[0].set_ylabel("4h loose MDE (bps)")
    axes[0].set_title("4h MDE by split protocol")
    fpr = fpr.set_index("protocol").reindex(SPLIT_PROTOCOLS)
    axes[1].bar(range(len(SPLIT_PROTOCOLS)), fpr["fpr"], yerr=fpr["wilson_half_width"],
                capsize=3, color="darkorange")
    axes[1].axhline(ALPHA0, color="red", linewidth=1, label="alpha0")
    axes[1].set_xticks(range(len(SPLIT_PROTOCOLS)), SPLIT_PROTOCOLS, rotation=20, ha="right")
    axes[1].set_ylabel("4h loose FPR")
    axes[1].set_title("4h FPR by split protocol")
    axes[1].legend()
    fig.suptitle("EXP-012 Plot 4 -- 4h split-sensitivity gate (single vs walk-forward)")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "split_gate_4h.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def build_cells_and_tasks(
    files: list[Path], tau_bps: dict[str, float]
) -> tuple[
    dict[tuple[str, str], dict[str, Any]],
    dict[str, dict[str, Any]],
    list[tuple[str, str, str, str, float, int]],
    list[dict[str, Any]],
]:
    """Load holdout-safe slices, build domains, enumerate draws, build 4h split folds."""
    walk_forward_fractions = np.linspace(
        WALK_FORWARD_WARMUP_FRACTION, 1.0, WALK_FORWARD_FOLDS + 1
    )
    cell_data: dict[tuple[str, str], dict[str, Any]] = {}
    split_cells: dict[str, dict[str, Any]] = {}
    tasks: list[tuple[str, str, str, str, float, int]] = []
    analysis_rows: list[dict[str, Any]] = []
    for path in tqdm(files, desc="EXP-012 load/domains"):
        data = load_analysis_data(path)
        base_times = data.frame.get_column("CloseTime").cast(pl.Int64).to_numpy()
        for domain, frame in build_domain_frames(data.frame).items():
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
                    "train_end": data.train_end,
                    "analysis_start": data.analysis_start,
                    "analysis_end": data.analysis_end,
                }
            )
            tasks.extend(build_draw_tasks(data.instrument, domain))
            if domain == SPLIT_GATE_DOMAIN:
                n = len(returns)
                aligned_times = aligned.get_column("CloseTime").cast(pl.Int64).to_numpy()
                wf_edges = mapped_fold_edges(base_times, aligned_times, walk_forward_fractions, n)
                split_cells[data.instrument] = {
                    "returns": returns,
                    "cost_bps": cost_bps_for(data.instrument, domain),
                    "folds": {
                        "single": single_split_folds(n, split_index),
                        "walk_forward": walk_forward_folds(wf_edges),
                    },
                }
    return cell_data, split_cells, tasks, analysis_rows


def reference_reproduction_4h(
    main_mde_rows: list[dict[str, Any]], split_mde_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    """Single-split arm must reproduce the main-measurement 4h loose MDE (sanity).

    The split helper's single contiguous fold reduces exactly to the frozen gate, so
    its 4h single-split loose MDE must equal the main measurement's. A mismatch flags
    an estimator inconsistency before the agreement rule is trusted.
    """
    main = next(
        (r for r in main_mde_rows
         if r["domain"] == SPLIT_GATE_DOMAIN and r["referee"] == "loose" and float(r["alpha"]) == ALPHA0),
        None,
    )
    single = next(
        (r for r in split_mde_rows
         if r["protocol"] == "single" and r["referee"] == "loose" and float(r["alpha"]) == ALPHA0),
        None,
    )
    main_mde = float(main["mde_bps"]) if main and math.isfinite(main["mde_bps"]) else math.nan
    single_mde = float(single["mde_bps"]) if single and math.isfinite(single["mde_bps"]) else math.nan
    consistent = bool(
        (math.isnan(main_mde) and math.isnan(single_mde))
        or (math.isfinite(main_mde) and math.isfinite(single_mde)
            and math.isclose(main_mde, single_mde, rel_tol=0.0, abs_tol=1e-9))
    )
    return {"main_4h_loose_mde_bps": main_mde, "split_single_4h_loose_mde_bps": single_mde,
            "consistent": consistent}


def main() -> None:
    """Run the EXP-012 fresh-draw loose-referee ratification and write outputs."""
    configure_logging()
    ensure_output_dirs()
    tokens = gate_dependencies()
    points = load_operating_points()
    tau_bps = {d: points[d]["tau_bps"] for d in DOMAINS}
    LOGGER.info("Dependency tokens: %s", tokens)
    LOGGER.info("Operating points (tau multiplier): %s", {d: points[d]["tau_multiplier"] for d in DOMAINS})

    files = list_timebar_files(DATA_DIR)
    if not files:
        raise FileNotFoundError(f"No time-bar files found under {DATA_DIR / 'timebars'}")

    cell_data, split_cells, tasks, analysis_rows = build_cells_and_tasks(files, tau_bps)
    if not tasks:
        raise RuntimeError("No draw tasks were enumerated")

    seed_disjointness = verify_seed_disjointness(tasks)
    if not seed_disjointness["disjoint"]:
        raise RuntimeError(
            f"Fresh seed payloads overlap Phase 001/002 inputs (genuine reuse): {seed_disjointness}"
        )
    LOGGER.info(
        "Fresh-seed input disjointness: %s (benign 32-bit collisions: %d, expected ~%.1f)",
        seed_disjointness["disjoint"],
        seed_disjointness["benign_int_collision_count"],
        seed_disjointness["expected_int_collisions"],
    )

    # Single-split fresh-draw measurement (all domains).
    verdict_rows = run_draw_tasks(tasks, cell_data, tau_bps)
    verdicts = pl.DataFrame(verdict_rows)
    fpr_rows = summarize_fpr(verdicts)
    tpr_rows = summarize_tpr(verdicts)
    mde_rows = summarize_mde(fpr_rows, tpr_rows)
    submaterial_rows = submaterial_at_operating_mde(verdicts, mde_rows, points)

    # 4h split-sensitivity gate (single vs anchored walk-forward).
    split_fpr_rows, split_mde_rows, comparison_rows = run_split_gate(
        split_cells, tau_bps[SPLIT_GATE_DOMAIN]
    )
    split_reference = reference_reproduction_4h(mde_rows, split_mde_rows)

    decisions = decide_adoption(fpr_rows, mde_rows, submaterial_rows, comparison_rows, points)

    measurements_produced = bool(fpr_rows) and bool(tpr_rows) and bool(mde_rows)
    overall_status = "COMPLETE" if measurements_produced else "INCONCLUSIVE"
    verdict_by_domain = {d["domain"]: d["verdict"] for d in decisions}

    # --- write results ---
    write_rows(RESULTS_DIR / "analysis_metadata.csv", analysis_rows)
    verdicts.write_csv(RESULTS_DIR / "draw_verdicts.csv")
    write_rows(RESULTS_DIR / "fresh_fpr_summary.csv", fpr_rows)
    write_rows(RESULTS_DIR / "fresh_tpr_summary.csv", tpr_rows)
    write_rows(RESULTS_DIR / "fresh_mde_summary.csv", mde_rows)
    write_rows(RESULTS_DIR / "submaterial_summary.csv", submaterial_rows)
    write_rows(RESULTS_DIR / "split_gate_fpr_summary.csv", split_fpr_rows)
    write_rows(RESULTS_DIR / "split_gate_mde_summary.csv", split_mde_rows)
    write_rows(RESULTS_DIR / "split_gate_comparison.csv", comparison_rows)
    write_rows(RESULTS_DIR / "adoption_decisions.csv", decisions)
    write_json(
        RESULTS_DIR / "run_metadata.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "overall_status": overall_status,
            "measurements_produced": measurements_produced,
            "dependencies": tokens,
            "operating_points": points,
            "adoption_verdict_by_domain": verdict_by_domain,
            "fresh_seed_disjointness": seed_disjointness,
            "split_gate_reference_reproduction": split_reference,
            "null_draws_per_generator": NULL_DRAWS_PER_GENERATOR,
            "positive_draws_per_edge": POSITIVE_DRAWS_PER_EDGE,
            "null_generators": list(NULL_GENERATORS),
            "positive_edges_bps": list(POSITIVE_EDGES),
            "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
            "alpha_grid": list(ALPHA_GRID),
            "alpha0": ALPHA0,
            "power_target": POWER_TARGET,
            "fpr_half_width_target": FPR_HALF_WIDTH_TARGET,
            "tpr_half_width_target": TPR_HALF_WIDTH_TARGET,
            "submaterial_tol": SUBMATERIAL_TOL,
            "submaterial_ceiling": SUBMATERIAL_CEILING,
            "mde_grid_step_tol": MDE_GRID_STEP_TOL,
            "walk_forward_folds": WALK_FORWARD_FOLDS,
            "walk_forward_warmup_fraction": WALK_FORWARD_WARMUP_FRACTION,
            "n_workers": N_WORKERS,
        },
    )

    plot_fpr(fpr_rows)
    plot_mde_comparison(mde_rows, points)
    plot_submaterial(submaterial_rows)
    plot_split_gate(split_mde_rows, split_fpr_rows)

    LOGGER.info("EXP-012 complete: %s", overall_status)
    LOGGER.info("Adoption by domain: %s", verdict_by_domain)
    LOGGER.info("4h split reference reproduction: %s", split_reference["consistent"])
    LOGGER.info("Results: %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
