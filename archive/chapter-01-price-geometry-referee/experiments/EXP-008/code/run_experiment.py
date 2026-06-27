"""
Experiment EXP-008: Per-Instrument MDE De-Pooling.

Phase 002 per-instrument map. Re-groups the frozen EXP-003 gate-stack draw
verdicts by instrument instead of pooling the four instruments, recomputes
Wilson FPR/TPR and the per-instrument economic MDE with the same definition
EXP-003 used, and compares each per-instrument MDE against its pooled domain MDE
under the frozen H-pool margin ``max(0.5 bps, 20% of pooled MDE)``. This is pure
result-level post-processing of the EXP-003 artifacts, which are already
first-70%-only; no market data and no holdout are ever loaded.
"""
from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import polars as pl

from xen.referee_calibration import EDGE_GRID_BPS, wilson_interval, write_json

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-008"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXPERIMENT_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"

EXP001_METADATA = (
    PROJECT_ROOT / "python" / "experiments" / "EXP-001" / "results" / "run_metadata.json"
)
EXP003_DIR = PROJECT_ROOT / "python" / "experiments" / "EXP-003" / "results"
EXP003_METADATA = EXP003_DIR / "run_metadata.json"
EXP003_DRAWS = EXP003_DIR / "draw_verdicts.csv"
EXP003_MDE = EXP003_DIR / "mde_summary.csv"

# Carried-forward Phase 001/002 invariants (P1-D-op, P1-D-prec).
ALPHA0 = 0.05
POWER_TARGET = 0.80
FPR_HALF_WIDTH_TARGET = 0.03
TPR_HALF_WIDTH_TARGET = 0.05

# Frozen H-pool material-difference margin (design section 4 / scope). Restated as
# code constants before any per-instrument MDE artifact is loaded.
MATERIAL_ABS_FLOOR_BPS = 0.5
MATERIAL_REL_FRACTION = 0.20

# Columns projected from the 142 MB draw file (bound memory; gate stack only).
DRAW_COLS = ["instrument", "domain", "scenario", "edge_bps", "alpha", "passed"]

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
# Dependency gate
# --------------------------------------------------------------------------- #
def require_dependencies() -> dict[str, str]:
    """Fail fast unless EXP-001 PASSED and EXP-003 COMPLETE with its artifacts.

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
    return {
        "exp001_status": str(exp001.get("overall_status")),
        "exp003_status": str(exp003.get("overall_status")),
    }


# --------------------------------------------------------------------------- #
# Load and per-instrument rate reconstruction (pure, vectorized)
# --------------------------------------------------------------------------- #
def load_gate_draws() -> pl.DataFrame:
    """Load EXP-003 gate-stack draw verdicts, projecting only what we re-group.

    Returns
    -------
    pl.DataFrame
        One row per recorded gate-stack draw verdict with instrument, domain,
        scenario, planted edge, alpha, and the frozen ``passed`` flag.
    """
    draws = (
        pl.scan_csv(EXP003_DRAWS)
        .filter(pl.col("referee") == "gate_stack")
        .select(DRAW_COLS)
        .collect()
    )
    if draws.is_empty():
        raise RuntimeError("No gate_stack rows found in EXP-003 draw_verdicts.csv")
    return draws


def wilson_rows_from_counts(
    grouped: pl.DataFrame, *, id_cols: list[str], rate_name: str
) -> list[dict[str, Any]]:
    """Attach Wilson-interval rates to an aggregated ``successes``/``n`` frame.

    Aggregation happens in Polars first (one row per rate cell), so the reused
    scalar :func:`wilson_interval` runs over a small frame, never the full draws.

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
                "referee": "gate_stack",
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


def per_instrument_fpr(draws: pl.DataFrame) -> list[dict[str, Any]]:
    """Per-instrument FPR per (instrument, domain, alpha) from null-scenario draws."""
    grouped = (
        draws.filter(pl.col("scenario") == "null")
        .group_by(["instrument", "domain", "alpha"])
        .agg(pl.col("passed").sum().alias("successes"), pl.len().alias("n"))
    )
    return wilson_rows_from_counts(
        grouped, id_cols=["instrument", "domain", "alpha"], rate_name="fpr"
    )


def per_instrument_tpr(draws: pl.DataFrame) -> list[dict[str, Any]]:
    """Per-instrument TPR per (instrument, domain, alpha, edge) from positive draws."""
    grouped = (
        draws.filter((pl.col("scenario") == "positive") & (pl.col("edge_bps") > 0.0))
        .group_by(["instrument", "domain", "alpha", "edge_bps"])
        .agg(pl.col("passed").sum().alias("successes"), pl.len().alias("n"))
    )
    return wilson_rows_from_counts(
        grouped, id_cols=["instrument", "domain", "alpha", "edge_bps"], rate_name="tpr"
    )


# --------------------------------------------------------------------------- #
# Per-instrument MDE (same definition as EXP-003, restricted to one instrument)
# --------------------------------------------------------------------------- #
def grid_half_step(edge_bps: float) -> float:
    """Half the smaller neighbouring gap around ``edge_bps`` on the edge grid.

    Identical to the EXP-003 ``grid_half_step`` so per-instrument and pooled MDE
    uncertainties are computed the same way.

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


def grid_full_step(edge_bps: float) -> float:
    """Smaller neighbouring gap (the full local grid spacing) around ``edge_bps``.

    Used for the ``within_grid_resolution`` band so that the guard tests against the
    plan's "local grid spacing" (analysis-plan.md Step 5), not the half-step MDE
    uncertainty. ``grid_half_step`` remains the published MDE-uncertainty convention
    reused from EXP-003 / by downstream experiments.
    """
    grid = sorted(float(value) for value in EDGE_GRID_BPS)
    if edge_bps not in grid:
        return math.nan
    index = grid.index(edge_bps)
    left = grid[index] - grid[index - 1] if index > 0 else grid[1] - grid[0]
    right = grid[index + 1] - grid[index] if index < len(grid) - 1 else left
    return float(min(left, right))


def per_instrument_mde(
    fpr_rows: list[dict[str, Any]], tpr_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Locate each per-instrument cell's empirical MDE across the alpha grid.

    Mirrors the EXP-003 MDE rule: the FPR must be controlled (``<= alpha``) with
    usable precision, then the MDE is the smallest planted edge whose TPR meets the
    0.80 power target with precision. Grid uncertainty is :func:`grid_half_step`.

    Parameters
    ----------
    fpr_rows, tpr_rows : list[dict[str, Any]]
        Per-instrument FPR and TPR summaries.

    Returns
    -------
    list[dict[str, Any]]
        One row per (instrument, domain, alpha) with status, MDE, and uncertainty.
    """
    fpr_idx = {(r["instrument"], r["domain"], float(r["alpha"])): r for r in fpr_rows}
    tpr_idx: dict[tuple[Any, Any, float], list[dict[str, Any]]] = {}
    for row in tpr_rows:
        key = (row["instrument"], row["domain"], float(row["alpha"]))
        tpr_idx.setdefault(key, []).append(row)

    output: list[dict[str, Any]] = []
    for key in sorted(tpr_idx, key=lambda item: (str(item[0]), str(item[1]), float(item[2]))):
        instrument, domain, alpha = key
        fpr = fpr_idx.get(key)
        mde_bps = math.nan
        grid_uncertainty = math.nan
        tpr_half_width = math.nan
        # Plan Step 4 promised to report any non-monotonicity beyond Monte-Carlo
        # precision rather than silently picking the first crossing. A drop is a
        # violation only if it exceeds the two cells' combined Wilson half-widths.
        cell_tpr = sorted(tpr_idx[key], key=lambda item: float(item["edge_bps"]))
        tpr_monotone = True
        for prev_row, next_row in zip(cell_tpr, cell_tpr[1:]):
            drop = float(prev_row["tpr"]) - float(next_row["tpr"])
            tol = float(prev_row["wilson_half_width"]) + float(next_row["wilson_half_width"])
            if drop > tol:
                tpr_monotone = False
                break
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
                "instrument": instrument,
                "domain": domain,
                "referee": "gate_stack",
                "alpha": alpha,
                "fpr": fpr["fpr"] if fpr else math.nan,
                "fpr_wilson_half_width": fpr["wilson_half_width"] if fpr else math.nan,
                "mde_bps": mde_bps,
                "mde_grid_uncertainty_bps": grid_uncertainty,
                "tpr_wilson_half_width_at_mde": tpr_half_width,
                "tpr_monotone": tpr_monotone,
                "status": status,
            }
        )
    return output


# --------------------------------------------------------------------------- #
# Material-difference comparison vs the pooled domain MDE
# --------------------------------------------------------------------------- #
def load_pooled_gate_mde() -> dict[tuple[str, float], dict[str, float]]:
    """Load the EXP-003 pooled gate-stack MDE per (domain, alpha).

    Returns
    -------
    dict[tuple[str, float], dict[str, float]]
        ``{(domain, alpha): {"mde_bps", "mde_grid_uncertainty_bps"}}``.
    """
    frame = pl.read_csv(EXP003_MDE).filter(pl.col("referee") == "gate_stack")
    out: dict[tuple[str, float], dict[str, float]] = {}
    for row in frame.iter_rows(named=True):
        mde = row["mde_bps"]
        unc = row["mde_grid_uncertainty_bps"]
        out[(str(row["domain"]), float(row["alpha"]))] = {
            "mde_bps": float(mde) if mde is not None else math.nan,
            "mde_grid_uncertainty_bps": float(unc) if unc is not None else math.nan,
        }
    return out


def compare_to_pool(
    mde_rows: list[dict[str, Any]],
    pooled: dict[tuple[str, float], dict[str, float]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Flag per-instrument vs pooled MDE differences against the frozen margin.

    Parameters
    ----------
    mde_rows : list[dict[str, Any]]
        Per-instrument MDE rows from :func:`per_instrument_mde`.
    pooled : dict[tuple[str, float], dict[str, float]]
        Pooled gate MDE keyed by (domain, alpha).

    Returns
    -------
    tuple[list[dict[str, Any]], dict[str, Any]]
        ``(comparison_rows, hpool_rollup)``. Only ``alpha0`` cells drive the
        H-pool roll-up; other alphas are emitted for context.
    """
    rows: list[dict[str, Any]] = []
    material_cells = 0
    reportable_cells = 0
    for row in mde_rows:
        domain = str(row["domain"])
        alpha = float(row["alpha"])
        pool = pooled.get((domain, alpha))
        pooled_mde = pool["mde_bps"] if pool else math.nan
        inst_mde = float(row["mde_bps"])
        reportable = row["status"] == "PASS" and math.isfinite(pooled_mde)
        delta = inst_mde - pooled_mde if reportable else math.nan
        margin = (
            max(MATERIAL_ABS_FLOOR_BPS, MATERIAL_REL_FRACTION * pooled_mde)
            if math.isfinite(pooled_mde)
            else math.nan
        )
        # within_grid_resolution uses the full local grid spacing (plan Step 5
        # "local grid spacing"), not the half-step MDE uncertainty, so a sub-grid
        # difference is judged against the real grid resolution.
        inst_full = grid_full_step(inst_mde) if math.isfinite(inst_mde) else math.nan
        pooled_full = grid_full_step(pooled_mde) if math.isfinite(pooled_mde) else math.nan
        grid_band = max(
            inst_full if math.isfinite(inst_full) else 0.0,
            pooled_full if math.isfinite(pooled_full) else 0.0,
        )
        material = bool(reportable and abs(delta) >= margin)
        within_grid = bool(reportable and abs(delta) < grid_band)
        if reportable and alpha == ALPHA0:
            reportable_cells += 1
            material_cells += int(material)
        rows.append(
            {
                "instrument": row["instrument"],
                "domain": domain,
                "referee": "gate_stack",
                "alpha": alpha,
                "per_instrument_mde_bps": inst_mde,
                "per_instrument_status": row["status"],
                "pooled_mde_bps": pooled_mde,
                "delta_bps": delta,
                "margin_bps": margin,
                "material": material,
                "within_grid_resolution": within_grid,
                "reportable": reportable,
            }
        )
    if reportable_cells == 0:
        hpool = "INCONCLUSIVE"
    elif material_cells > 0:
        hpool = "SUPPORTED"
    else:
        hpool = "REFUTED"
    rollup = {
        "hpool_verdict": hpool,
        "reportable_cells_alpha0": reportable_cells,
        "material_cells_alpha0": material_cells,
    }
    return rows, rollup


# --------------------------------------------------------------------------- #
# Plotting (bounded summary inputs only)
# --------------------------------------------------------------------------- #
def plot_mde_vs_pool(comparison_rows: list[dict[str, Any]]) -> None:
    """Per-instrument vs pooled MDE at alpha0, faceted by domain, with margin band."""
    pdf = pl.DataFrame(comparison_rows).filter(pl.col("alpha") == ALPHA0).to_pandas()
    domains = sorted(pdf["domain"].unique())
    fig, axes = plt.subplots(1, len(domains), figsize=(5 * len(domains), 5), sharey=False)
    axes = axes if len(domains) > 1 else [axes]
    for ax, domain in zip(axes, domains):
        sub = pdf[pdf["domain"] == domain].sort_values("instrument")
        pooled = sub["pooled_mde_bps"].iloc[0] if len(sub) else math.nan
        margin = sub["margin_bps"].iloc[0] if len(sub) else math.nan
        ax.bar(range(len(sub)), sub["per_instrument_mde_bps"], color="steelblue")
        if math.isfinite(pooled):
            ax.axhline(pooled, color="black", linewidth=1, label="pooled MDE")
            ax.axhspan(pooled - margin, pooled + margin, color="grey", alpha=0.2, label="margin")
        ax.set_xticks(range(len(sub)), sub["instrument"], rotation=45, ha="right", fontsize=7)
        ax.set_title(str(domain))
        ax.set_ylabel("MDE (bps)")
        ax.legend(fontsize=7)
    fig.suptitle("Per-instrument vs pooled gate MDE at alpha=0.05")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "per_instrument_vs_pooled_mde.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_tpr_curves(tpr_rows: list[dict[str, Any]]) -> None:
    """Per-instrument TPR vs planted edge at alpha0, faceted by domain."""
    pdf = pl.DataFrame(tpr_rows).filter(pl.col("alpha") == ALPHA0).to_pandas()
    domains = sorted(pdf["domain"].unique())
    fig, axes = plt.subplots(1, len(domains), figsize=(5 * len(domains), 5), sharey=True)
    axes = axes if len(domains) > 1 else [axes]
    for ax, domain in zip(axes, domains):
        sub = pdf[pdf["domain"] == domain]
        for instrument, group in sub.groupby("instrument"):
            group = group.sort_values("edge_bps")
            ax.plot(group["edge_bps"], group["tpr"], marker=".", label=str(instrument))
        ax.axhline(POWER_TARGET, color="black", linewidth=1)
        ax.set_xscale("log")
        ax.set_xlabel("Planted edge (bps, log)")
        ax.set_title(str(domain))
    axes[0].set_ylabel("TPR (gate stack)")
    axes[-1].legend(fontsize=7, title="instrument")
    fig.suptitle("Per-instrument TPR vs planted edge at alpha=0.05")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "per_instrument_tpr_curves.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_fpr(fpr_rows: list[dict[str, Any]]) -> None:
    """Per-instrument FPR at alpha0 by domain against the alpha0 line."""
    pdf = pl.DataFrame(fpr_rows).filter(pl.col("alpha") == ALPHA0).to_pandas()
    pdf = pdf.sort_values(["domain", "instrument"])
    fig, ax = plt.subplots(figsize=(9, 5))
    labels = pdf["domain"] + " " + pdf["instrument"]
    ax.bar(range(len(pdf)), pdf["fpr"])
    ax.axhline(ALPHA0, color="red", linewidth=1, label="alpha0 = 0.05")
    ax.set_xticks(range(len(pdf)), labels, rotation=90, fontsize=6)
    ax.set_ylabel("FPR (gate stack)")
    ax.set_title("Per-instrument false-positive rate at alpha=0.05")
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "per_instrument_fpr.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_material_matrix(comparison_rows: list[dict[str, Any]]) -> None:
    """Instrument x domain matrix of the material-difference classification at alpha0."""
    pdf = pl.DataFrame(comparison_rows).filter(pl.col("alpha") == ALPHA0).to_pandas()

    def code(row: Any) -> float:
        if not row["reportable"]:
            return 0.0  # under-powered / not reportable
        if row["material"]:
            return 2.0  # material difference
        if row["within_grid_resolution"]:
            return 1.0  # within grid resolution
        return 1.0  # within margin

    pdf["code"] = pdf.apply(code, axis=1)
    pivot = pdf.pivot_table(index="instrument", columns="domain", values="code", aggfunc="max")
    fig, ax = plt.subplots(figsize=(7, 5))
    im = ax.imshow(pivot.values, aspect="auto", cmap="RdYlGn_r", vmin=0, vmax=2)
    ax.set_xticks(range(len(pivot.columns)), list(pivot.columns))
    ax.set_yticks(range(len(pivot.index)), list(pivot.index))
    for r in range(pivot.shape[0]):
        for c in range(pivot.shape[1]):
            ax.text(c, r, f"{pivot.values[r, c]:.0f}", ha="center", va="center", fontsize=8)
    ax.set_title("Material flag (0=under-powered, 1=within margin, 2=material)")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "material_flag_matrix.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run the EXP-008 per-instrument MDE de-pooling and write summaries/plots."""
    configure_logging()
    ensure_output_dirs()
    dependency_status = require_dependencies()

    draws = load_gate_draws()
    fpr_rows = per_instrument_fpr(draws)
    tpr_rows = per_instrument_tpr(draws)
    mde_rows = per_instrument_mde(fpr_rows, tpr_rows)
    pooled = load_pooled_gate_mde()
    comparison_rows, hpool_rollup = compare_to_pool(mde_rows, pooled)

    measurements_produced = bool(fpr_rows) and bool(tpr_rows) and bool(mde_rows)
    overall_status = "COMPLETE" if measurements_produced else "INCONCLUSIVE"

    write_rows(RESULTS_DIR / "per_instrument_fpr_summary.csv", fpr_rows)
    write_rows(RESULTS_DIR / "per_instrument_tpr_summary.csv", tpr_rows)
    write_rows(RESULTS_DIR / "per_instrument_mde_summary.csv", mde_rows)
    write_rows(RESULTS_DIR / "mde_pool_comparison.csv", comparison_rows)
    write_json(
        RESULTS_DIR / "run_metadata.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "overall_status": overall_status,
            "measurements_produced": measurements_produced,
            "dependencies": dependency_status,
            "hpool_rollup": hpool_rollup,
            "gate_draw_rows": int(draws.height),
            "alpha0": ALPHA0,
            "power_target": POWER_TARGET,
            "fpr_half_width_target": FPR_HALF_WIDTH_TARGET,
            "tpr_half_width_target": TPR_HALF_WIDTH_TARGET,
            "material_abs_floor_bps": MATERIAL_ABS_FLOOR_BPS,
            "material_rel_fraction": MATERIAL_REL_FRACTION,
            "alpha_grid": sorted({float(row["alpha"]) for row in fpr_rows}),
        },
    )

    plot_mde_vs_pool(comparison_rows)
    plot_tpr_curves(tpr_rows)
    plot_fpr(fpr_rows)
    plot_material_matrix(comparison_rows)

    LOGGER.info("EXP-008 complete: %s", overall_status)
    LOGGER.info("H-pool roll-up: %s", hpool_rollup)
    LOGGER.info("Results: %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
