"""
Experiment EXP-018: Revised Incremental Referee Portfolio-Fitness Calibration.

Measures the revised incremental referee's portfolio-fitness MDE under the
unchanged P3-D-dependence grid. The revised gate removes L2 and retains L1, L3,
L4_prime, and strict L5. The implementation uses only the first 70%
chronological analysis slice, aligns by CloseTime, and evaluates every marginal
return on real OHLC domain prices.

Manual execution gate: do not run inside the research pipeline.
"""
from __future__ import annotations

import json
import logging
import math
import multiprocessing as mp
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from tqdm.auto import tqdm

from xen.incremental_referee import (
    EPISODE_LENGTHS,
    combine_positions,
    incremental_gate_core,
    marginal_net_series,
    per_bar_incremental_cost,
    revised_incremental_gate_row,
)
from xen.referee_calibration import (
    ALPHA_GRID,
    EDGE_GRID_BPS,
    build_domain_frames,
    cost_bps_for,
    domain_split_index,
    list_timebar_files,
    load_analysis_data,
    next_log_returns_from_bars,
    seed_for,
    wilson_interval,
    write_json,
)

LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants & paths
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-018"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data"
EXPERIMENTS_DIR = PROJECT_ROOT / "python" / "experiments"
EXPERIMENT_DIR = EXPERIMENTS_DIR / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"


def _results(exp_id: str) -> Path:
    return EXPERIMENTS_DIR / exp_id / "results"


EXP003_MDE = _results("EXP-003") / "mde_summary.csv"
EXP013_META = _results("EXP-013") / "run_metadata.json"
EXP017_META = _results("EXP-017") / "run_metadata.json"

DOMAINS: tuple[str, ...] = ("5m", "1h", "4h")
ALPHA0 = 0.05
POWER_TARGET = 0.80
FPR_HALF_WIDTH_TARGET = 0.03
TPR_HALF_WIDTH_TARGET = 0.05
BOOTSTRAP_RESAMPLES = 1000

# Per-domain/dependence-cell denominators target EXP-003/012 precision. Draws are
# split evenly across the four instruments, then summarized by domain/grid cell.
NULL_DRAWS_PER_INSTRUMENT_CELL = 125
POSITIVE_DRAWS_PER_EDGE_PER_INSTRUMENT_CELL = 125
POSITIVE_EDGES: tuple[float, ...] = tuple(edge for edge in EDGE_GRID_BPS if edge > 0.0)

RHO_TARGETS: dict[str, float] = {
    "independent": 0.0,
    "moderate": 0.40,
    "high": 0.80,
}
RHO_BANDS: dict[str, tuple[float, float]] = {
    "independent": (-0.05, 0.05),
    "moderate": (0.35, 0.45),
    "high": (0.75, 0.85),
}
OVERLAP_TARGETS: dict[str, float] = {
    "low": 0.20,
    "medium": 0.50,
    "high": 0.80,
}
OVERLAP_BAND = 0.05
LAG_LABELS: tuple[str, ...] = ("synchronous", "c_lags_r_1", "c_leads_r_1")
REFERENCE_STRENGTHS: tuple[str, ...] = ("null_R", "R_at_strict_mde")
CONSTRUCTION_ATTEMPTS = 32
C_ACTIVE_FRACTION = 0.50

N_WORKERS = max(1, int(os.environ.get("EXP018_WORKERS", os.cpu_count() or 1)))
TASK_CHUNKSIZE = 8

_WORKER_CELLS: dict[tuple[str, str], dict[str, Any]] = {}
_WORKER_STRICT_MDE: dict[str, float] = {}


@dataclass(frozen=True)
class Construction:
    """Accepted dependence-grid R/C positions and diagnostics."""

    r_positions: np.ndarray
    c_positions: np.ndarray
    realized_rho: float
    realized_overlap: float
    union_active_count: int
    r_active_count: int
    c_active_count: int
    both_active_count: int
    accepted: bool
    reason: str


# --------------------------------------------------------------------------- #
# Output helpers
# --------------------------------------------------------------------------- #
def configure_logging() -> None:
    """Configure concise INFO-level logging for the manual run."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def ensure_output_dirs() -> None:
    """Create experiment output directories during orchestration only."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write result rows to CSV, preserving an empty artifact when no rows exist."""
    if rows:
        pl.DataFrame(rows).write_csv(path)
    else:
        path.write_text("", encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from ``path``."""
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Dependency gate
# --------------------------------------------------------------------------- #
def dependency_manifest() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Check required upstream artifacts and return ``(manifest, blockers)``."""
    manifest: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []

    def add_json(exp_id: str, path: Path, required_status: str) -> None:
        if not path.exists():
            blockers.append({"artifact": str(path), "reason": "missing"})
            manifest.append({"dependency": exp_id, "artifact": str(path), "status": "MISSING"})
            return
        meta = _load_json(path)
        status = str(meta.get("overall_status"))
        manifest.append({"dependency": exp_id, "artifact": str(path), "status": status})
        if status != required_status:
            blockers.append(
                {
                    "artifact": str(path),
                    "reason": f"overall_status={status!r}, required {required_status!r}",
                }
            )

    add_json("EXP-013", EXP013_META, "PASS")
    add_json("EXP-017", EXP017_META, "PASS")
    if not EXP003_MDE.exists():
        blockers.append({"artifact": str(EXP003_MDE), "reason": "missing strict MDE map"})
        manifest.append({"dependency": "EXP-003", "artifact": str(EXP003_MDE), "status": "MISSING"})
    else:
        manifest.append({"dependency": "EXP-003", "artifact": str(EXP003_MDE), "status": "FOUND"})
    return manifest, blockers


def load_strict_mde_map() -> dict[str, float]:
    """Load inherited strict gate-stack MDEs at alpha0 from EXP-003."""
    frame = pl.read_csv(EXP003_MDE).filter(
        (pl.col("alpha") == ALPHA0) & (pl.col("referee") == "gate_stack")
    )
    out: dict[str, float] = {}
    for row in frame.iter_rows(named=True):
        domain = str(row["domain"])
        value = float(row["mde_bps"]) if row["mde_bps"] is not None else math.nan
        if domain in DOMAINS and math.isfinite(value):
            out[domain] = value
    missing = [domain for domain in DOMAINS if domain not in out]
    if missing:
        raise RuntimeError(f"EXP-003 strict gate-stack alpha0 MDE missing domains: {missing}")
    return out


def write_blocked_metadata(
    manifest_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
) -> None:
    """Record a BLOCKED run without producing measurements."""
    write_rows(RESULTS_DIR / "dependency_manifest.csv", manifest_rows)
    write_rows(RESULTS_DIR / "blocker_report.csv", blocker_rows)
    write_json(
        RESULTS_DIR / "run_metadata.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "overall_status": "BLOCKED",
            "measurements_produced": False,
            "reason": "Required Phase 003b artifacts are not approved/present.",
            "blockers": blocker_rows,
        },
    )


# --------------------------------------------------------------------------- #
# Dependence-grid construction
# --------------------------------------------------------------------------- #
def _diagnostic_arrays(
    r_positions: np.ndarray, c_positions: np.ndarray, lag_label: str
) -> tuple[np.ndarray, np.ndarray]:
    """Return arrays used for the predeclared lead/lag diagnostics."""
    if lag_label == "synchronous":
        return r_positions, c_positions
    if lag_label == "c_lags_r_1":
        return r_positions[:-1], c_positions[1:]
    if lag_label == "c_leads_r_1":
        return r_positions[1:], c_positions[:-1]
    raise ValueError(f"Unknown lag label: {lag_label}")


def _signed_corr_over_union(r_positions: np.ndarray, c_positions: np.ndarray) -> float:
    """Signed R/C correlation over rows where either signal is active."""
    union = (np.abs(r_positions) > 0.0) | (np.abs(c_positions) > 0.0)
    if int(np.count_nonzero(union)) < 2:
        return math.nan
    r = np.asarray(r_positions[union], dtype=float)
    c = np.asarray(c_positions[union], dtype=float)
    if float(np.std(r)) == 0.0 or float(np.std(c)) == 0.0:
        return math.nan
    return float(np.corrcoef(r, c)[0, 1])


def _overlap_fraction(r_positions: np.ndarray, c_positions: np.ndarray) -> float:
    """``both_active / max(C_active, 1)`` active-overlap diagnostic."""
    c_active = np.abs(c_positions) > 0.0
    both_active = c_active & (np.abs(r_positions) > 0.0)
    return float(np.count_nonzero(both_active) / max(int(np.count_nonzero(c_active)), 1))


def _apply_lag(c_positions: np.ndarray, lag_label: str) -> np.ndarray:
    """Apply the scoped lead/lag relation to C without using future returns."""
    c = np.asarray(c_positions, dtype=float)
    shifted = np.zeros_like(c)
    if lag_label == "synchronous":
        return c.copy()
    if lag_label == "c_lags_r_1":
        shifted[1:] = c[:-1]
        return shifted
    if lag_label == "c_leads_r_1":
        shifted[:-1] = c[1:]
        return shifted
    raise ValueError(f"Unknown lag label: {lag_label}")


def _build_candidate_core(
    n: int,
    *,
    rho_target: float,
    overlap_target: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, str]:
    """Build unshifted R/C positions for a target rho and active-overlap cell."""
    if n < 20:
        return np.zeros(n), np.zeros(n), "too_few_rows"

    rng = np.random.default_rng(seed)
    c_count = max(4, min(n - 2, int(round(n * C_ACTIVE_FRACTION))))
    both_count = max(1, min(c_count, int(round(c_count * overlap_target))))
    min_r_count = both_count
    max_r_count = n - c_count + both_count

    if rho_target > 0.0:
        max_corr = both_count / math.sqrt(max(min_r_count * c_count, 1))
        if max_corr + 1e-12 < rho_target:
            return np.zeros(n), np.zeros(n), "target_rho_infeasible_for_overlap"
        desired_r = int(round((both_count / (rho_target * math.sqrt(c_count))) ** 2))
        r_count = max(min_r_count, min(max_r_count, desired_r))
        max_corr = both_count / math.sqrt(max(r_count * c_count, 1))
        sign_corr = max(-1.0, min(1.0, rho_target / max(max_corr, 1e-12)))
    else:
        r_count = max(min(max_r_count, c_count), min_r_count)
        sign_corr = 0.0

    r_only_count = r_count - both_count
    if r_only_count > n - c_count:
        return np.zeros(n), np.zeros(n), "not_enough_rows_for_masks"

    all_idx = np.arange(n)
    c_idx = rng.choice(all_idx, size=c_count, replace=False)
    both_idx = rng.choice(c_idx, size=both_count, replace=False)
    outside_c = np.setdiff1d(all_idx, c_idx, assume_unique=False)
    r_only_idx = rng.choice(outside_c, size=r_only_count, replace=False) if r_only_count else np.array([], dtype=int)

    r_positions = np.zeros(n, dtype=float)
    c_positions = np.zeros(n, dtype=float)
    base_state = rng.choice(np.array([-1.0, 1.0]), size=n)
    r_positions[np.concatenate([both_idx, r_only_idx])] = base_state[
        np.concatenate([both_idx, r_only_idx])
    ]

    agree_probability = (sign_corr + 1.0) / 2.0
    signs = np.where(rng.random(both_count) <= agree_probability, 1.0, -1.0)
    c_positions[both_idx] = r_positions[both_idx] * signs
    c_only_idx = np.setdiff1d(c_idx, both_idx, assume_unique=False)
    c_positions[c_only_idx] = rng.choice(np.array([-1.0, 1.0]), size=len(c_only_idx))
    return r_positions, c_positions, "constructed"


def construct_grid_positions(
    n: int,
    *,
    rho_label: str,
    overlap_label: str,
    lag_label: str,
    seed: int,
) -> Construction:
    """Construct R/C positions that meet the predeclared grid acceptance bands."""
    rho_target = RHO_TARGETS[rho_label]
    overlap_target = OVERLAP_TARGETS[overlap_label]
    rho_low, rho_high = RHO_BANDS[rho_label]
    overlap_low = overlap_target - OVERLAP_BAND
    overlap_high = overlap_target + OVERLAP_BAND
    last_reason = "not_attempted"

    for attempt in range(CONSTRUCTION_ATTEMPTS):
        r_raw, c_raw, reason = _build_candidate_core(
            n,
            rho_target=rho_target,
            overlap_target=overlap_target,
            seed=seed + attempt,
        )
        if reason != "constructed":
            last_reason = reason
            break
        c_positions = _apply_lag(c_raw, lag_label)
        r_diag, c_diag = _diagnostic_arrays(r_raw, c_positions, lag_label)
        realized_rho = _signed_corr_over_union(r_diag, c_diag)
        realized_overlap = _overlap_fraction(r_diag, c_diag)
        accepted = bool(
            math.isfinite(realized_rho)
            and rho_low <= realized_rho <= rho_high
            and overlap_low <= realized_overlap <= overlap_high
        )
        if accepted:
            union = (np.abs(r_diag) > 0.0) | (np.abs(c_diag) > 0.0)
            r_active = np.abs(r_diag) > 0.0
            c_active = np.abs(c_diag) > 0.0
            both = r_active & c_active
            return Construction(
                r_positions=r_raw,
                c_positions=c_positions,
                realized_rho=realized_rho,
                realized_overlap=realized_overlap,
                union_active_count=int(np.count_nonzero(union)),
                r_active_count=int(np.count_nonzero(r_active)),
                c_active_count=int(np.count_nonzero(c_active)),
                both_active_count=int(np.count_nonzero(both)),
                accepted=True,
                reason="accepted",
            )
        last_reason = (
            f"diagnostics_outside_band rho={realized_rho:.4f} "
            f"overlap={realized_overlap:.4f}"
        )

    return Construction(
        r_positions=np.zeros(n, dtype=float),
        c_positions=np.zeros(n, dtype=float),
        realized_rho=math.nan,
        realized_overlap=math.nan,
        union_active_count=0,
        r_active_count=0,
        c_active_count=0,
        both_active_count=0,
        accepted=False,
        reason=last_reason,
    )


def plant_reference_and_incremental_edges(
    returns: np.ndarray,
    r_positions: np.ndarray,
    c_positions: np.ndarray,
    *,
    instrument: str,
    domain: str,
    reference_edge_bps: float,
    incremental_edge_bps: float,
) -> np.ndarray:
    """Plant R-alone and marginal C-beyond-R net edges on real-price returns."""
    scoped = np.asarray(returns, dtype=float).copy()
    cost = cost_bps_for(instrument, domain)
    r_active = np.abs(r_positions) > 0.0
    if reference_edge_bps > 0.0 and int(np.count_nonzero(r_active)) > 0:
        scoped[r_active] += r_positions[r_active] * ((reference_edge_bps + cost) / 10_000.0)

    combined = combine_positions(r_positions, c_positions)
    marginal = combined - r_positions
    denominator = marginal != 0.0
    if incremental_edge_bps > 0.0 and int(np.count_nonzero(denominator)) > 0:
        inc_cost = per_bar_incremental_cost(cost, EPISODE_LENGTHS[domain])
        scoped[denominator] += np.sign(marginal[denominator]) * (
            (incremental_edge_bps + inc_cost) / 10_000.0
        )
    return scoped


# --------------------------------------------------------------------------- #
# Worker evaluation
# --------------------------------------------------------------------------- #
Task = tuple[str, str, str, str, str, str, str, float, int]


def _init_worker(
    cells: dict[tuple[str, str], dict[str, Any]], strict_mde_map: dict[str, float]
) -> None:
    """Initialize multiprocessing worker globals."""
    global _WORKER_CELLS, _WORKER_STRICT_MDE
    _WORKER_CELLS = cells
    _WORKER_STRICT_MDE = strict_mde_map


def _construction_row(
    task: Task, construction: Construction, denominator_count: int | None = None
) -> dict[str, Any]:
    """Build the construction-diagnostic row for one draw task."""
    draw_kind, instrument, domain, rho_label, overlap_label, lag_label, ref_label, edge_bps, draw = task
    return {
        "draw_kind": draw_kind,
        "instrument": instrument,
        "domain": domain,
        "rho_label": rho_label,
        "overlap_label": overlap_label,
        "lag_label": lag_label,
        "reference_strength": ref_label,
        "planted_edge_bps": edge_bps,
        "draw_index": draw,
        "accepted": construction.accepted,
        "reason": construction.reason,
        "realized_rho": construction.realized_rho,
        "realized_overlap": construction.realized_overlap,
        "union_active_count": construction.union_active_count,
        "r_active_count": construction.r_active_count,
        "c_active_count": construction.c_active_count,
        "both_active_count": construction.both_active_count,
        "denominator_count": denominator_count if denominator_count is not None else 0,
    }


def _evaluate_task(task: Task) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Evaluate one null or positive draw task."""
    draw_kind, instrument, domain, rho_label, overlap_label, lag_label, ref_label, edge_bps, draw = task
    cell = _WORKER_CELLS[(instrument, domain)]
    returns = cell["returns"]
    split_index = int(cell["split_index"])
    seed = seed_for(
        EXPERIMENT_ID,
        instrument,
        domain,
        rho_label,
        overlap_label,
        lag_label,
        ref_label,
        draw_kind,
        edge_bps,
        draw,
    )
    construction = construct_grid_positions(
        len(returns),
        rho_label=rho_label,
        overlap_label=overlap_label,
        lag_label=lag_label,
        seed=seed,
    )
    if not construction.accepted:
        return [_construction_row(task, construction)], []

    reference_edge = _WORKER_STRICT_MDE[domain] if ref_label == "R_at_strict_mde" else 0.0
    scoped_returns = plant_reference_and_incremental_edges(
        returns,
        construction.r_positions,
        construction.c_positions,
        instrument=instrument,
        domain=domain,
        reference_edge_bps=reference_edge,
        incremental_edge_bps=float(edge_bps),
    )
    marginal = marginal_net_series(
        scoped_returns,
        construction.r_positions,
        construction.c_positions,
        cost_bps=cost_bps_for(instrument, domain),
        episode_length=EPISODE_LENGTHS[domain],
    )
    core = incremental_gate_core(
        scoped_returns,
        construction.r_positions,
        construction.c_positions,
        instrument=instrument,
        domain=domain,
        n_bootstrap=BOOTSTRAP_RESAMPLES,
        seed=seed,
        split_index=split_index,
        episode_length=EPISODE_LENGTHS[domain],
        # F07: the revised gate has no L2 leg, so skip the standalone bootstrap.
        compute_standalone=False,
    )

    base = {
        "draw_kind": draw_kind,
        "instrument": instrument,
        "domain": domain,
        "rho_label": rho_label,
        "overlap_label": overlap_label,
        "lag_label": lag_label,
        "reference_strength": ref_label,
        "planted_edge_bps": float(edge_bps),
        "reference_edge_bps": reference_edge,
        "draw_index": draw,
        "realized_rho": construction.realized_rho,
        "realized_overlap": construction.realized_overlap,
        "denominator_count": int(marginal["denominator_count"]),
    }
    verdict_rows: list[dict[str, Any]] = []
    for alpha in ALPHA_GRID:
        row = revised_incremental_gate_row(core, alpha=float(alpha))
        # Retain the per-leg states (adversarial-review F03) as boolean columns so a
        # refuted/under-powered cell can be attributed to a specific binding leg
        # instead of an opaque PASS/REJECT. The JSON blob itself is dropped to keep
        # the draw-level CSV lean.
        legs = json.loads(row.pop("leg_results"))
        row.update({leg: bool(legs[leg]) for leg in LEG_COLS})
        verdict_rows.append({**base, **row})
    return [_construction_row(task, construction, int(marginal["denominator_count"]))], verdict_rows


# --------------------------------------------------------------------------- #
# Loading and task enumeration
# --------------------------------------------------------------------------- #
def build_cells() -> tuple[dict[tuple[str, str], dict[str, Any]], list[dict[str, Any]]]:
    """Load first-70% analysis slices and build per-instrument domain returns."""
    files = list_timebar_files(DATA_DIR)
    if not files:
        raise FileNotFoundError(f"No time-bar files found under {DATA_DIR / 'timebars'}")

    cells: dict[tuple[str, str], dict[str, Any]] = {}
    analysis_rows: list[dict[str, Any]] = []
    for path in tqdm(files, desc="EXP-018 load/domains"):
        data = load_analysis_data(path)
        for domain, frame in build_domain_frames(data.frame).items():
            returns, aligned = next_log_returns_from_bars(frame)
            split_index = domain_split_index(aligned, data.train_end_ts)
            cells[(data.instrument, domain)] = {
                "returns": returns,
                "split_index": split_index,
            }
            analysis_rows.append(
                {
                    "instrument": data.instrument,
                    "source_file": data.source_file,
                    "domain": domain,
                    "domain_rows": frame.height,
                    "return_rows": len(returns),
                    "split_index": split_index,
                    "analysis_start": data.analysis_start,
                    "analysis_end": data.analysis_end,
                    "train_end": data.train_end,
                }
            )
    return cells, analysis_rows


def grid_manifest_rows(strict_mde_map: dict[str, float]) -> list[dict[str, Any]]:
    """Return the frozen dependence-grid manifest."""
    rows: list[dict[str, Any]] = []
    for domain in DOMAINS:
        for rho_label, rho_target in RHO_TARGETS.items():
            for overlap_label, overlap_target in OVERLAP_TARGETS.items():
                for lag_label in LAG_LABELS:
                    for ref_label in REFERENCE_STRENGTHS:
                        rows.append(
                            {
                                "domain": domain,
                                "rho_label": rho_label,
                                "rho_target": rho_target,
                                "rho_band_low": RHO_BANDS[rho_label][0],
                                "rho_band_high": RHO_BANDS[rho_label][1],
                                "overlap_label": overlap_label,
                                "overlap_target": overlap_target,
                                "overlap_band_low": overlap_target - OVERLAP_BAND,
                                "overlap_band_high": overlap_target + OVERLAP_BAND,
                                "lag_label": lag_label,
                                "reference_strength": ref_label,
                                "reference_edge_bps": (
                                    strict_mde_map[domain] if ref_label == "R_at_strict_mde" else 0.0
                                ),
                            }
                        )
    return rows


def build_tasks(cells: dict[tuple[str, str], dict[str, Any]]) -> list[Task]:
    """Enumerate draw tasks across instruments and the dependence grid."""
    tasks: list[Task] = []
    for instrument, domain in sorted(cells):
        for rho_label in RHO_TARGETS:
            for overlap_label in OVERLAP_TARGETS:
                for lag_label in LAG_LABELS:
                    for ref_label in REFERENCE_STRENGTHS:
                        for draw in range(NULL_DRAWS_PER_INSTRUMENT_CELL):
                            tasks.append(
                                (
                                    "redundancy_null",
                                    instrument,
                                    domain,
                                    rho_label,
                                    overlap_label,
                                    lag_label,
                                    ref_label,
                                    0.0,
                                    draw,
                                )
                            )
                        for edge_bps in POSITIVE_EDGES:
                            for draw in range(POSITIVE_DRAWS_PER_EDGE_PER_INSTRUMENT_CELL):
                                tasks.append(
                                    (
                                        "positive",
                                        instrument,
                                        domain,
                                        rho_label,
                                        overlap_label,
                                        lag_label,
                                        ref_label,
                                        float(edge_bps),
                                        draw,
                                    )
                                )
    return tasks


def run_tasks(
    tasks: list[Task], cells: dict[tuple[str, str], dict[str, Any]], strict_mde_map: dict[str, float]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Run all draw tasks with deterministic worker-local construction."""
    construction_rows: list[dict[str, Any]] = []
    verdict_rows: list[dict[str, Any]] = []
    if N_WORKERS == 1:
        _init_worker(cells, strict_mde_map)
        iterator = (_evaluate_task(task) for task in tasks)
        for c_rows, v_rows in tqdm(iterator, total=len(tasks), desc="EXP-018 draws"):
            construction_rows.extend(c_rows)
            verdict_rows.extend(v_rows)
        return construction_rows, verdict_rows

    with mp.Pool(
        processes=N_WORKERS,
        initializer=_init_worker,
        initargs=(cells, strict_mde_map),
    ) as pool:
        iterator = pool.imap_unordered(_evaluate_task, tasks, chunksize=TASK_CHUNKSIZE)
        for c_rows, v_rows in tqdm(iterator, total=len(tasks), desc="EXP-018 draws"):
            construction_rows.extend(c_rows)
            verdict_rows.extend(v_rows)
    return construction_rows, verdict_rows


# --------------------------------------------------------------------------- #
# Summaries
# --------------------------------------------------------------------------- #
GRID_COLS: list[str] = [
    "domain",
    "rho_label",
    "overlap_label",
    "lag_label",
    "reference_strength",
]

# The retained revised incremental-referee legs, kept per draw for failure attribution.
LEG_COLS: list[str] = [
    "L1_readiness",
    "L3_reference_control",
    "L4_no_material_sign_reversal",
    "L5_strict_materiality",
]

# F03 / design.md (D-dependence): the binding stress corner is synchronous lead/lag,
# high active-overlap, null reference. It "must be reported explicitly for every
# domain", so it is extracted into a dedicated artifact rather than left implicit in
# the full grid. A1/F03 attributes the EXP-015 refutation specifically to the
# moderate/high shared-latent-state (rho) cells, so all three rho levels at this corner
# are reported and the moderate/high-rho cells are flagged as the EXP-015 stress.
BINDING_CORNER: dict[str, str] = {
    "lag_label": "synchronous",
    "overlap_label": "high",
    "reference_strength": "null_R",
}
A1F03_STRESS_RHO: tuple[str, ...] = ("moderate", "high")


def _rate_row(base: dict[str, Any], successes: int, n: int, rate_name: str) -> dict[str, Any]:
    """Build a Wilson-rate summary row."""
    center, lower, upper = wilson_interval(successes, n)
    return {
        **base,
        rate_name: successes / n if n else math.nan,
        "wilson_center": center,
        "wilson_lower": lower,
        "wilson_upper": upper,
        "wilson_half_width": (upper - lower) / 2.0 if n else math.nan,
        "successes": successes,
        "n": n,
    }


def summarize_fpr(
    verdict_rows: list[dict[str, Any]], construction_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Summarize redundancy-null FPR by domain/dependence grid cell."""
    all_keys = {
        tuple(row[col] for col in GRID_COLS)
        for row in construction_rows
        if row["draw_kind"] == "redundancy_null"
    }
    if not verdict_rows:
        return [
            {
                **dict(zip(GRID_COLS, key, strict=True)),
                "fpr": math.nan,
                "wilson_center": math.nan,
                "wilson_lower": math.nan,
                "wilson_upper": math.nan,
                "wilson_half_width": math.nan,
                "successes": 0,
                "n": 0,
                "status": "CONSTRUCTION_INVALID",
            }
            for key in sorted(all_keys)
        ]
    frame = pl.DataFrame(verdict_rows).filter(
        (pl.col("draw_kind") == "redundancy_null") & (pl.col("alpha") == ALPHA0)
    )
    rows: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for key_values, group in frame.group_by(GRID_COLS, maintain_order=True):
        if not isinstance(key_values, tuple):
            key_values = (key_values,)
        seen.add(key_values)
        base = dict(zip(GRID_COLS, key_values, strict=True))
        n = group.height
        successes = int(group.filter(pl.col("passed")).height)
        row = _rate_row(base, successes, n, "fpr")
        if n == 0:
            status = "CONSTRUCTION_INVALID"
        elif row["wilson_half_width"] > FPR_HALF_WIDTH_TARGET:
            status = "UNDERPOWERED_FPR_PRECISION"
        elif row["fpr"] <= ALPHA0:
            status = "PASS"
        else:
            status = "FAIL_FPR_GT_ALPHA0"
        rows.append({**row, "status": status})
    for key in sorted(all_keys.difference(seen)):
        rows.append(
            {
                **dict(zip(GRID_COLS, key, strict=True)),
                "fpr": math.nan,
                "wilson_center": math.nan,
                "wilson_lower": math.nan,
                "wilson_upper": math.nan,
                "wilson_half_width": math.nan,
                "successes": 0,
                "n": 0,
                "status": "CONSTRUCTION_INVALID",
            }
        )
    return rows


def summarize_tpr(
    verdict_rows: list[dict[str, Any]], construction_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Summarize positive-edge TPR by domain/grid cell and planted edge."""
    all_keys = {
        tuple(row[col] for col in [*GRID_COLS, "planted_edge_bps"])
        for row in construction_rows
        if row["draw_kind"] == "positive"
    }
    if not verdict_rows:
        return [
            {
                **dict(zip([*GRID_COLS, "planted_edge_bps"], key, strict=True)),
                "tpr": math.nan,
                "wilson_center": math.nan,
                "wilson_lower": math.nan,
                "wilson_upper": math.nan,
                "wilson_half_width": math.nan,
                "successes": 0,
                "n": 0,
                "status": "CONSTRUCTION_INVALID",
            }
            for key in sorted(all_keys)
        ]
    frame = pl.DataFrame(verdict_rows).filter(
        (pl.col("draw_kind") == "positive") & (pl.col("alpha") == ALPHA0)
    )
    cols = [*GRID_COLS, "planted_edge_bps"]
    rows: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for key_values, group in frame.group_by(cols, maintain_order=True):
        if not isinstance(key_values, tuple):
            key_values = (key_values,)
        seen.add(key_values)
        base = dict(zip(cols, key_values, strict=True))
        n = group.height
        successes = int(group.filter(pl.col("passed")).height)
        row = _rate_row(base, successes, n, "tpr")
        if n == 0:
            status = "CONSTRUCTION_INVALID"
        elif row["wilson_half_width"] > TPR_HALF_WIDTH_TARGET:
            status = "UNDERPOWERED_TPR_PRECISION"
        elif row["tpr"] >= POWER_TARGET:
            status = "PASS"
        else:
            status = "FAIL_TPR_LT_TARGET"
        rows.append({**row, "status": status})
    for key in sorted(all_keys.difference(seen)):
        rows.append(
            {
                **dict(zip(cols, key, strict=True)),
                "tpr": math.nan,
                "wilson_center": math.nan,
                "wilson_lower": math.nan,
                "wilson_upper": math.nan,
                "wilson_half_width": math.nan,
                "successes": 0,
                "n": 0,
                "status": "CONSTRUCTION_INVALID",
            }
        )
    return rows


def summarize_denominators(construction_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Summarize incremental denominator counts for each grid cell."""
    accepted = [row for row in construction_rows if row["accepted"]]
    if not accepted:
        return []
    frame = pl.DataFrame(accepted)
    rows: list[dict[str, Any]] = []
    for record in (
        frame.group_by(GRID_COLS, maintain_order=True)
        .agg(
            pl.col("denominator_count").mean().alias("mean_denominator_count"),
            pl.col("denominator_count").median().alias("median_denominator_count"),
            pl.col("denominator_count").min().alias("min_denominator_count"),
            pl.col("denominator_count").max().alias("max_denominator_count"),
            pl.len().alias("accepted_draws"),
        )
        .iter_rows(named=True)
    ):
        rows.append(record)
    return rows


def summarize_leg_pass_rates(verdict_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per domain/grid cell/edge, the pass-rate of each gate leg among positive draws.

    Diagnoses WHICH leg caps TPR in a refuted cell (adversarial-review F03): a leg
    whose pass-rate plateaus below the power target across the largest edges is the
    binding constraint, distinguishing a genuine detectability limit from a leg or
    construction artifact.
    """
    if not verdict_rows:
        return []
    frame = pl.DataFrame(verdict_rows).filter(
        (pl.col("draw_kind") == "positive") & (pl.col("alpha") == ALPHA0)
    )
    if frame.is_empty():
        return []
    cols = [*GRID_COLS, "planted_edge_bps"]
    aggs = [pl.col(leg).mean().alias(f"{leg}_pass_rate") for leg in LEG_COLS]
    aggs += [pl.col("passed").mean().alias("verdict_pass_rate"), pl.len().alias("n")]
    return [
        record
        for record in frame.group_by(cols, maintain_order=True)
        .agg(aggs)
        .sort(cols)
        .iter_rows(named=True)
    ]


def summarize_tpr_by_instrument(verdict_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per domain/grid cell/instrument/edge TPR (adversarial-review F03).

    Surfaces single-instrument power caps that the instrument-pooled TPR hides -- e.g.
    a 0.75 pooled plateau driven by one of four instruments never clearing power.
    """
    if not verdict_rows:
        return []
    frame = pl.DataFrame(verdict_rows).filter(
        (pl.col("draw_kind") == "positive") & (pl.col("alpha") == ALPHA0)
    )
    if frame.is_empty():
        return []
    cols = [*GRID_COLS, "instrument", "planted_edge_bps"]
    return [
        record
        for record in frame.group_by(cols, maintain_order=True)
        .agg(pl.col("passed").mean().alias("tpr"), pl.len().alias("n"))
        .sort(cols)
        .iter_rows(named=True)
    ]


def summarize_cell_mde(
    fpr_rows: list[dict[str, Any]], tpr_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Derive one MDE row per domain/dependence grid cell."""
    fpr_by_cell = {tuple(row[col] for col in GRID_COLS): row for row in fpr_rows}
    tpr_by_cell: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in tpr_rows:
        key = tuple(row[col] for col in GRID_COLS)
        tpr_by_cell.setdefault(key, []).append(row)

    rows: list[dict[str, Any]] = []
    for key, fpr in fpr_by_cell.items():
        base = dict(zip(GRID_COLS, key, strict=True))
        cell_tprs = sorted(tpr_by_cell.get(key, []), key=lambda r: float(r["planted_edge_bps"]))
        if fpr["status"] != "PASS":
            status = "FPR_NOT_CONTROLLED" if fpr["status"].startswith("FAIL") else fpr["status"]
            rows.append({**base, "cell_mde_bps": math.nan, "status": status})
            continue

        pass_row = next((row for row in cell_tprs if row["status"] == "PASS"), None)
        if pass_row is not None:
            rows.append(
                {
                    **base,
                    "cell_mde_bps": float(pass_row["planted_edge_bps"]),
                    "status": "PASS",
                    "fpr": fpr["fpr"],
                    "fpr_wilson_half_width": fpr["wilson_half_width"],
                    "tpr_at_mde": pass_row["tpr"],
                    "tpr_wilson_half_width": pass_row["wilson_half_width"],
                }
            )
            continue

        any_invalid = any(row["status"] == "CONSTRUCTION_INVALID" for row in cell_tprs)
        any_underpowered = any(row["status"].startswith("UNDERPOWERED") for row in cell_tprs)
        rows.append(
            {
                **base,
                "cell_mde_bps": math.nan,
                "status": (
                    "CONSTRUCTION_INVALID"
                    if any_invalid
                    else "UNDERPOWERED_TPR_PRECISION"
                    if any_underpowered
                    else "FAIL_NO_FINITE_MDE"
                ),
                "fpr": fpr["fpr"],
                "fpr_wilson_half_width": fpr["wilson_half_width"],
                "tpr_at_mde": math.nan,
                "tpr_wilson_half_width": math.nan,
            }
        )
    return rows


def summarize_binding_corner(
    fpr_rows: list[dict[str, Any]], cell_mde_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Explicitly report the synchronous/high-overlap/null_R corner per domain (F03).

    design.md (D-dependence) requires the EXP-015 failure corner to be reported
    explicitly for every domain rather than left implicit in the full grid. This
    extracts the corner's redundancy-null FPR and finite MDE for each (domain, rho)
    and flags the moderate/high-rho cells A1/F03 identified as the actual EXP-015
    stress, so a second refutation is unambiguously attributable to this corner.
    """
    fpr_by_cell = {tuple(row[col] for col in GRID_COLS): row for row in fpr_rows}
    mde_by_cell = {tuple(row[col] for col in GRID_COLS): row for row in cell_mde_rows}
    rows: list[dict[str, Any]] = []
    for domain in DOMAINS:
        for rho_label in RHO_TARGETS:
            key = (
                domain,
                rho_label,
                BINDING_CORNER["overlap_label"],
                BINDING_CORNER["lag_label"],
                BINDING_CORNER["reference_strength"],
            )
            fpr = fpr_by_cell.get(key)
            mde = mde_by_cell.get(key)
            rows.append(
                {
                    "domain": domain,
                    "rho_label": rho_label,
                    "overlap_label": BINDING_CORNER["overlap_label"],
                    "lag_label": BINDING_CORNER["lag_label"],
                    "reference_strength": BINDING_CORNER["reference_strength"],
                    "a1f03_exp015_stress": rho_label in A1F03_STRESS_RHO,
                    "fpr": fpr["fpr"] if fpr is not None else math.nan,
                    "fpr_wilson_half_width": fpr["wilson_half_width"] if fpr is not None else math.nan,
                    "fpr_status": fpr["status"] if fpr is not None else "CONSTRUCTION_INVALID",
                    "cell_mde_bps": mde["cell_mde_bps"] if mde is not None else math.nan,
                    "cell_status": mde["status"] if mde is not None else "MISSING",
                }
            )
    return rows


def summarize_domain_mde(cell_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Worst-case finite domain MDE and domain verdict under dependence stress."""
    frame = pl.DataFrame(cell_rows) if cell_rows else pl.DataFrame()
    rows: list[dict[str, Any]] = []
    for domain in DOMAINS:
        if frame.is_empty():
            sub = pl.DataFrame()
        else:
            sub = frame.filter(pl.col("domain") == domain)
        if sub.is_empty():
            rows.append(
                {
                    "domain": domain,
                    "domain_mde_bps": math.nan,
                    "finite_mde_cells": 0,
                    "failing_cells": 0,
                    "underpowered_or_invalid_cells": 0,
                    "status": "INCONCLUSIVE_NO_CELLS",
                }
            )
            continue
        pass_rows = sub.filter(pl.col("status") == "PASS")
        finite_mdes = [
            float(value)
            for value in pass_rows.get_column("cell_mde_bps").to_list()
            if value is not None and math.isfinite(float(value))
        ]
        failing = sub.filter(pl.col("status").str.starts_with("FAIL") | (pl.col("status") == "FPR_NOT_CONTROLLED")).height
        underpowered = sub.height - pass_rows.height - failing
        if failing > 0:
            status = "REFUTED"
        elif finite_mdes:
            status = "SUPPORTED" if underpowered == 0 else "SUPPORTED_WITH_UNDERPOWERED_CELLS"
        else:
            status = "INCONCLUSIVE"
        rows.append(
            {
                "domain": domain,
                "domain_mde_bps": max(finite_mdes) if finite_mdes else math.nan,
                "finite_mde_cells": len(finite_mdes),
                "failing_cells": failing,
                "underpowered_or_invalid_cells": underpowered,
                "total_cells": sub.height,
                "status": status,
            }
        )
    return rows


def invalid_or_underpowered_rows(cell_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return cell rows that are not qualifying PASS cells."""
    return [row for row in cell_rows if row.get("status") != "PASS"]


# --------------------------------------------------------------------------- #
# Plotting
# --------------------------------------------------------------------------- #
def plot_fpr_heatmap(fpr_rows: list[dict[str, Any]]) -> None:
    """Plot FPR by domain/rho/overlap; lag/reference are encoded in labels."""
    if not fpr_rows:
        return
    pdf = pl.DataFrame(fpr_rows).to_pandas()
    pdf["cell"] = pdf["rho_label"] + "/" + pdf["overlap_label"] + "/" + pdf["lag_label"] + "/" + pdf["reference_strength"]
    domains = list(DOMAINS)
    fig, axes = plt.subplots(len(domains), 1, figsize=(14, 3.5 * len(domains)), sharex=True)
    axes = axes if len(domains) > 1 else [axes]
    for ax, domain in zip(axes, domains):
        sub = pdf[pdf["domain"] == domain].sort_values("cell")
        ax.bar(range(len(sub)), sub["fpr"], color="steelblue")
        ax.axhline(ALPHA0, color="red", linewidth=1)
        ax.set_ylabel(f"{domain} FPR")
        ax.set_title(f"Redundancy-null FPR ({domain})")
    axes[-1].set_xticks(range(len(sub)), sub["cell"], rotation=90, fontsize=5)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "fpr_dependence_grid.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_mde_summary(cell_rows: list[dict[str, Any]]) -> None:
    """Plot finite MDE cells by domain and dependence context."""
    finite = [row for row in cell_rows if row["status"] == "PASS"]
    if not finite:
        return
    pdf = pl.DataFrame(finite).to_pandas()
    pdf["cell"] = pdf["rho_label"] + "/" + pdf["overlap_label"] + "/" + pdf["lag_label"] + "/" + pdf["reference_strength"]
    fig, ax = plt.subplots(figsize=(14, 6))
    colors = {"5m": "steelblue", "1h": "darkorange", "4h": "seagreen"}
    x = np.arange(len(pdf))
    ax.bar(x, pdf["cell_mde_bps"], color=[colors.get(d, "grey") for d in pdf["domain"]])
    ax.set_xticks(x, pdf["domain"] + " " + pdf["cell"], rotation=90, fontsize=5)
    ax.set_ylabel("Cell MDE (bps)")
    ax.set_title("Finite portfolio-fitness MDE by qualifying dependence cell")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "cell_mde_summary.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_tpr_curves(tpr_rows: list[dict[str, Any]]) -> None:
    """Plot mean TPR over dependence cells by domain and planted edge."""
    if not tpr_rows:
        return
    frame = pl.DataFrame(tpr_rows)
    rows = (
        frame.group_by(["domain", "planted_edge_bps"], maintain_order=True)
        .agg(pl.col("tpr").mean().alias("mean_tpr"))
        .sort(["domain", "planted_edge_bps"])
    )
    pdf = rows.to_pandas()
    fig, ax = plt.subplots(figsize=(8, 5))
    for domain in DOMAINS:
        sub = pdf[pdf["domain"] == domain]
        ax.plot(sub["planted_edge_bps"], sub["mean_tpr"], marker="o", label=domain)
    ax.axhline(POWER_TARGET, color="red", linewidth=1, label="TPR target")
    ax.set_xlabel("Planted incremental edge (bps)")
    ax.set_ylabel("Mean TPR across grid cells")
    ax.set_title("TPR curve over planted incremental edge")
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "tpr_curves.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_cell_status(cell_rows: list[dict[str, Any]]) -> None:
    """Plot cell-status counts by domain."""
    if not cell_rows:
        return
    frame = pl.DataFrame(cell_rows)
    pdf = (
        frame.group_by(["domain", "status"], maintain_order=True)
        .agg(pl.len().alias("n"))
        .to_pandas()
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    statuses = sorted(pdf["status"].unique())
    bottom = np.zeros(len(DOMAINS))
    for status in statuses:
        values = [
            int(pdf[(pdf["domain"] == domain) & (pdf["status"] == status)]["n"].sum())
            for domain in DOMAINS
        ]
        ax.bar(DOMAINS, values, bottom=bottom, label=status)
        bottom += np.asarray(values)
    ax.set_ylabel("Dependence cells")
    ax.set_title("Qualifying, under-powered, and invalid dependence cells")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "cell_status_counts.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_denominator_distribution(denominator_rows: list[dict[str, Any]]) -> None:
    """Plot median incremental denominator count by domain/grid cell."""
    if not denominator_rows:
        return
    pdf = pl.DataFrame(denominator_rows).to_pandas()
    pdf["cell"] = pdf["rho_label"] + "/" + pdf["overlap_label"] + "/" + pdf["lag_label"] + "/" + pdf["reference_strength"]
    fig, ax = plt.subplots(figsize=(14, 5))
    ordered = pdf.sort_values(["domain", "cell"])
    ax.bar(range(len(ordered)), ordered["median_denominator_count"], color="slateblue")
    ax.set_xticks(range(len(ordered)), ordered["domain"] + " " + ordered["cell"], rotation=90, fontsize=5)
    ax.set_ylabel("Median denominator rows")
    ax.set_title("Incremental denominator distribution by dependence cell")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "denominator_distribution.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run EXP-018 and write draw-level, summary, and plot artifacts."""
    configure_logging()
    ensure_output_dirs()
    manifest_rows, blocker_rows = dependency_manifest()
    if blocker_rows:
        write_blocked_metadata(manifest_rows, blocker_rows)
        LOGGER.warning("EXP-018 BLOCKED: %s", blocker_rows)
        return

    strict_mde_map = load_strict_mde_map()
    cells, analysis_rows = build_cells()
    tasks = build_tasks(cells)
    if not tasks:
        raise RuntimeError("No EXP-018 draw tasks were enumerated")

    LOGGER.info("EXP-018 tasks: %s | workers: %s", len(tasks), N_WORKERS)
    construction_rows, verdict_rows = run_tasks(tasks, cells, strict_mde_map)

    fpr_rows = summarize_fpr(verdict_rows, construction_rows)
    tpr_rows = summarize_tpr(verdict_rows, construction_rows)
    denominator_rows = summarize_denominators(construction_rows)
    leg_pass_rate_rows = summarize_leg_pass_rates(verdict_rows)
    tpr_by_instrument_rows = summarize_tpr_by_instrument(verdict_rows)
    cell_mde_rows = summarize_cell_mde(fpr_rows, tpr_rows)
    binding_corner_rows = summarize_binding_corner(fpr_rows, cell_mde_rows)
    domain_rows = summarize_domain_mde(cell_mde_rows)
    blocker_or_power_rows = invalid_or_underpowered_rows(cell_mde_rows)

    measurements_produced = bool(verdict_rows) and bool(fpr_rows) and bool(tpr_rows)
    # F02 / design.md section 9: REVISED_UNIT_VALIDATED needs "a finite portfolio-fitness
    # MDE map across the grid" for EVERY in-scope domain. COMPLETE therefore requires
    # all domains to conclude SUPPORTED (a finite worst-case MDE, with or without some
    # under-powered cells). Any REFUTED domain -> REFUTED_AGAIN; any domain left
    # INCONCLUSIVE (no finite MDE anywhere, binding cells did not conclude) blocks
    # COMPLETE -> overall INCONCLUSIVE, so EXP-019 cannot unblock on a partially
    # validated unit and an operator must rule on the under-powered domain.
    domain_statuses = [str(row["status"]) for row in domain_rows]
    any_refuted = any(status == "REFUTED" for status in domain_statuses)
    all_supported = bool(domain_statuses) and all(
        status.startswith("SUPPORTED") for status in domain_statuses
    )
    if any_refuted:
        overall_status = "REFUTED"
    elif all_supported:
        overall_status = "COMPLETE"
    else:
        overall_status = "INCONCLUSIVE"

    write_rows(RESULTS_DIR / "dependency_manifest.csv", manifest_rows)
    write_rows(RESULTS_DIR / "grid_manifest.csv", grid_manifest_rows(strict_mde_map))
    write_rows(RESULTS_DIR / "analysis_metadata.csv", analysis_rows)
    write_rows(RESULTS_DIR / "construction_diagnostics.csv", construction_rows)
    write_rows(RESULTS_DIR / "draw_verdicts.csv", verdict_rows)
    write_rows(RESULTS_DIR / "fpr_summary.csv", fpr_rows)
    write_rows(RESULTS_DIR / "tpr_summary.csv", tpr_rows)
    write_rows(RESULTS_DIR / "denominator_summary.csv", denominator_rows)
    write_rows(RESULTS_DIR / "leg_pass_rates.csv", leg_pass_rate_rows)
    write_rows(RESULTS_DIR / "tpr_by_instrument.csv", tpr_by_instrument_rows)
    write_rows(RESULTS_DIR / "cell_mde_summary.csv", cell_mde_rows)
    write_rows(RESULTS_DIR / "binding_corner_summary.csv", binding_corner_rows)
    write_rows(RESULTS_DIR / "domain_mde_summary.csv", domain_rows)
    write_rows(RESULTS_DIR / "underpowered_or_invalid_cells.csv", blocker_or_power_rows)
    write_json(
        RESULTS_DIR / "run_metadata.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "overall_status": overall_status,
            "measurements_produced": measurements_produced,
            "dependencies": {row["dependency"]: row["status"] for row in manifest_rows},
            "strict_mde_map_alpha0": strict_mde_map,
            "alpha_grid": list(ALPHA_GRID),
            "alpha0": ALPHA0,
            "revised_gate_formula": "L1 and L3 and L4_prime and strict_L5; L2 absent",
            "retained_leg_columns": LEG_COLS,
            "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
            "null_draws_per_instrument_cell": NULL_DRAWS_PER_INSTRUMENT_CELL,
            "positive_draws_per_edge_per_instrument_cell": POSITIVE_DRAWS_PER_EDGE_PER_INSTRUMENT_CELL,
            "positive_edges_bps": list(POSITIVE_EDGES),
            "rho_targets": RHO_TARGETS,
            "rho_bands": RHO_BANDS,
            "overlap_targets": OVERLAP_TARGETS,
            "overlap_band": OVERLAP_BAND,
            "lag_labels": list(LAG_LABELS),
            "reference_strengths": list(REFERENCE_STRENGTHS),
            "domain_status": {row["domain"]: row["status"] for row in domain_rows},
            "domain_mde_bps": {row["domain"]: row["domain_mde_bps"] for row in domain_rows},
            "binding_corner": BINDING_CORNER,
            "binding_corner_status": {
                f"{row['domain']}|rho={row['rho_label']}": {
                    "fpr_status": row["fpr_status"],
                    "cell_status": row["cell_status"],
                    "a1f03_exp015_stress": row["a1f03_exp015_stress"],
                }
                for row in binding_corner_rows
            },
            "n_workers": N_WORKERS,
        },
    )

    plot_fpr_heatmap(fpr_rows)
    plot_mde_summary(cell_mde_rows)
    plot_tpr_curves(tpr_rows)
    plot_cell_status(cell_mde_rows)
    plot_denominator_distribution(denominator_rows)

    LOGGER.info("EXP-018 complete: %s", overall_status)
    LOGGER.info("Domain status: %s", {row["domain"]: row["status"] for row in domain_rows})
    LOGGER.info(
        "Binding corner (synchronous/high-overlap/null_R): %s",
        {
            f"{row['domain']}|rho={row['rho_label']}": row["fpr_status"]
            for row in binding_corner_rows
            if row["a1f03_exp015_stress"]
        },
    )
    LOGGER.info("Results: %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
