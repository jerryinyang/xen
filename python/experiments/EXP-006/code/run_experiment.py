"""
Experiment EXP-006: L5 Materiality Threshold Sweep.

Phase 002 lever-characterization. Traces the frozen 5-check gate stack's economic
MDE and FPR as the L5 materiality threshold magnitude is swept per domain. This is
pure result-level post-processing of the EXP-003 draw-level verdicts: the frozen
harness mechanism is preserved and only the L5 threshold is changed, recomputed as
``L5_tau = ci_lower_bps > tau`` with ``tau = multiplier * materiality_bps(domain)``.
L1-L4 are taken unchanged from the recorded draws. No market data and no holdout
are ever loaded; the EXP-003 artifacts are already first-70%-only.
"""
from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import polars as pl

from xen.referee_calibration import wilson_interval, write_json

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-006"
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
EXP003_FPR = EXP003_DIR / "fpr_summary.csv"
EXP003_TPR = EXP003_DIR / "tpr_summary.csv"
EXP003_MDE = EXP003_DIR / "mde_summary.csv"

# Predeclared L5 threshold sweep (scope "Threshold sweep"). tau=1.0xmateriality is
# the frozen strict gate; tau=0 is the zero-buffer endpoint of the same mechanism.
MULTIPLIERS: tuple[float, ...] = (0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0)
STRICT_MULTIPLIER = 1.0

# Carried-forward Phase 001/002 invariants (P1-D-op, P1-D-prec).
ALPHA0 = 0.05
POWER_TARGET = 0.80
FPR_HALF_WIDTH_TARGET = 0.03
TPR_HALF_WIDTH_TARGET = 0.05

# Only the fields needed to reconstruct the conjoined gate verdict are decoded
# from the serialized leg_results; L5 is recomputed, the rest are taken as-is.
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
    for artifact in (EXP003_DRAWS, EXP003_FPR, EXP003_TPR, EXP003_MDE):
        if not artifact.exists():
            raise FileNotFoundError(f"Required EXP-003 artifact missing: {artifact}")
    return {
        "exp001_status": str(exp001.get("overall_status")),
        "exp003_status": str(exp003.get("overall_status")),
    }


# --------------------------------------------------------------------------- #
# Load and threshold-sweep reconstruction (pure, vectorized)
# --------------------------------------------------------------------------- #
def load_gate_draws() -> pl.DataFrame:
    """Load EXP-003 gate-stack draws and decode the legs needed for L5 reconstruction.

    Returns
    -------
    pl.DataFrame
        One row per recorded gate-stack draw verdict with L1-L4 booleans,
        ``materiality_bps``, ``ci_lower_bps``, and the frozen ``passed`` flag.
    """
    draws = (
        pl.scan_csv(EXP003_DRAWS)
        .filter(pl.col("referee") == "gate_stack")
        .select(DRAW_COLS)
        .with_columns(pl.col("leg_results").str.json_decode(LEG_SCHEMA).alias("legs"))
        .unnest("legs")
        .drop("leg_results")
        .collect()
    )
    if draws.is_empty():
        raise RuntimeError("No gate_stack rows found in EXP-003 draw_verdicts.csv")
    return draws


def sweep_thresholds(draws: pl.DataFrame) -> pl.DataFrame:
    """Reconstruct the conjoined gate verdict for every swept L5 threshold.

    The frozen mechanism is preserved: ``L5_tau = ci_lower_bps > tau`` with
    ``tau = multiplier * materiality_bps``; L1-L4 are unchanged. Sample membership,
    denominators, and the recorded effect/CI are never altered.

    Returns
    -------
    pl.DataFrame
        Long frame of ``len(draws) * len(MULTIPLIERS)`` rows with ``multiplier``,
        ``tau_bps``, and the reconstructed ``passed_tau``.
    """
    multiplier_frame = pl.DataFrame({"multiplier": list(MULTIPLIERS)})
    legs_pass = (
        pl.col("L1_readiness")
        & pl.col("L2_integrity")
        & pl.col("L3_outcome")
        & pl.col("L4_stability")
    )
    return (
        draws.join(multiplier_frame, how="cross")
        .with_columns((pl.col("multiplier") * pl.col("materiality_bps")).alias("tau_bps"))
        .with_columns(
            (legs_pass & (pl.col("ci_lower_bps") > pl.col("tau_bps"))).alias("passed_tau")
        )
    )


# --------------------------------------------------------------------------- #
# Rate summaries (Wilson) and MDE frontier (pure)
# --------------------------------------------------------------------------- #
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


def summarize_fpr(swept: pl.DataFrame) -> list[dict[str, Any]]:
    """Pooled FPR per (domain, alpha, multiplier) from null-scenario draws."""
    grouped = (
        swept.filter(pl.col("scenario") == "null")
        .group_by(["domain", "alpha", "multiplier"])
        .agg(pl.col("passed_tau").sum().alias("successes"), pl.len().alias("n"))
    )
    return wilson_rows_from_counts(
        grouped, id_cols=["domain", "alpha", "multiplier"], rate_name="fpr"
    )


def summarize_tpr(swept: pl.DataFrame) -> list[dict[str, Any]]:
    """Pooled TPR per (domain, alpha, multiplier, edge_bps) from positive draws."""
    grouped = (
        swept.filter(pl.col("scenario") == "positive")
        .group_by(["domain", "alpha", "multiplier", "edge_bps"])
        .agg(pl.col("passed_tau").sum().alias("successes"), pl.len().alias("n"))
    )
    return wilson_rows_from_counts(
        grouped,
        id_cols=["domain", "alpha", "multiplier", "edge_bps"],
        rate_name="tpr",
    )


def positive_edge_grid(swept: pl.DataFrame) -> list[float]:
    """Sorted distinct positive planted edges, used as the MDE search grid."""
    edges = (
        swept.filter(pl.col("scenario") == "positive")
        .get_column("edge_bps")
        .unique()
        .sort()
        .to_list()
    )
    return [float(edge) for edge in edges]


def compute_mde_frontier(
    fpr_rows: list[dict[str, Any]],
    tpr_rows: list[dict[str, Any]],
    edge_grid: list[float],
) -> list[dict[str, Any]]:
    """Trace MDE(threshold): smallest precise edge meeting power at controlled FPR.

    For each (domain, alpha, multiplier): the FPR must be controlled (``<= alpha``)
    with usable precision; the MDE is then the smallest planted edge whose TPR meets
    the 0.80 power target with precision. Grid uncertainty is the gap to the previous
    grid edge — never an interpolation.

    Returns
    -------
    list[dict[str, Any]]
        One frontier row per (domain, alpha, multiplier) with ``mde_bps`` and a
        predeclared ``status``.
    """
    prior_edge = {edge: (edge_grid[idx - 1] if idx > 0 else 0.0) for idx, edge in enumerate(edge_grid)}
    fpr_idx = {(row["domain"], row["alpha"], row["multiplier"]): row for row in fpr_rows}
    tpr_idx: dict[tuple[Any, Any, Any], list[dict[str, Any]]] = {}
    for row in tpr_rows:
        tpr_idx.setdefault((row["domain"], row["alpha"], row["multiplier"]), []).append(row)

    output: list[dict[str, Any]] = []
    for key in sorted(tpr_idx, key=lambda item: (str(item[0]), float(item[1]), float(item[2]))):
        domain, alpha, multiplier = key
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
                "referee": "gate_stack",
                "alpha": alpha,
                "multiplier": multiplier,
                "fpr": fpr_value,
                "fpr_wilson_half_width": fpr_hw,
                "mde_bps": mde_bps,
                "mde_grid_uncertainty_bps": grid_uncertainty,
                "status": status,
            }
        )
    return output


# --------------------------------------------------------------------------- #
# Strict-reference reproduction check
# --------------------------------------------------------------------------- #
def strict_reference_check(
    swept: pl.DataFrame, mde_rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool]:
    """Confirm the tau=1.0 reconstruction reproduces the frozen EXP-003 gate.

    Two layers: (1) the reconstructed ``passed_tau`` at tau=1.0xmateriality must
    equal the recorded frozen ``passed`` for every draw; (2) the reconstructed MDE
    at tau=1.0 must match the EXP-003 gate MDE per (domain, alpha).

    Returns
    -------
    tuple[list[dict[str, Any]], bool]
        ``(check_rows, strict_reference_pass)``.
    """
    strict = swept.filter(pl.col("multiplier") == STRICT_MULTIPLIER)
    draw_mismatch = (
        strict.with_columns((pl.col("passed_tau") != pl.col("passed")).alias("mismatch"))
        .group_by(["domain", "alpha"])
        .agg(pl.col("mismatch").sum().alias("draw_mismatch_count"))
    )
    mismatch_idx = {
        (row["domain"], row["alpha"]): int(row["draw_mismatch_count"])
        for row in draw_mismatch.iter_rows(named=True)
    }
    recon_mde = {
        (row["domain"], row["alpha"]): row["mde_bps"]
        for row in mde_rows
        if float(row["multiplier"]) == STRICT_MULTIPLIER
    }
    exp003_mde = pl.read_csv(EXP003_MDE).filter(pl.col("referee") == "gate_stack")

    rows: list[dict[str, Any]] = []
    overall_pass = True
    for record in exp003_mde.sort(["domain", "alpha"]).iter_rows(named=True):
        key = (record["domain"], float(record["alpha"]))
        recon = recon_mde.get(key, math.nan)
        reference = record["mde_bps"]
        mismatches = mismatch_idx.get(key, None)
        mde_match = (
            reference is not None
            and isinstance(recon, float)
            and math.isfinite(recon)
            and math.isclose(recon, float(reference), rel_tol=0.0, abs_tol=1e-9)
        )
        draws_ok = mismatches == 0
        overall_pass = overall_pass and draws_ok and mde_match
        rows.append(
            {
                "domain": record["domain"],
                "alpha": float(record["alpha"]),
                "draw_mismatch_count": mismatches if mismatches is not None else -1,
                "reconstructed_mde_bps": recon,
                "exp003_mde_bps": float(reference) if reference is not None else math.nan,
                "mde_match": bool(mde_match),
                "draws_match": bool(draws_ok),
            }
        )
    return rows, bool(overall_pass)


# --------------------------------------------------------------------------- #
# Plotting (bounded summary inputs only)
# --------------------------------------------------------------------------- #
def plot_fpr_vs_threshold(fpr_rows: list[dict[str, Any]]) -> None:
    """FPR vs L5 threshold multiplier by domain at alpha0, against the alpha0 line."""
    pdf = pl.DataFrame(fpr_rows).filter(pl.col("alpha") == ALPHA0).to_pandas()
    fig, ax = plt.subplots(figsize=(8, 5))
    for domain, group in pdf.groupby("domain"):
        group = group.sort_values("multiplier")
        ax.plot(group["multiplier"], group["fpr"], marker="o", label=str(domain))
    ax.axhline(ALPHA0, color="red", linewidth=1, label="alpha0 = 0.05")
    ax.axvline(STRICT_MULTIPLIER, color="grey", linestyle="--", linewidth=1, label="strict (tau=1.0)")
    ax.set_xlabel("L5 threshold multiplier (tau / materiality)")
    ax.set_ylabel("Gate-stack FPR")
    ax.set_title("False-positive rate vs L5 threshold at alpha=0.05")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "fpr_vs_threshold.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_mde_vs_threshold(mde_rows: list[dict[str, Any]]) -> None:
    """MDE vs L5 threshold multiplier by domain at alpha0 (finite MDE points only)."""
    pdf = pl.DataFrame(mde_rows).filter(pl.col("alpha") == ALPHA0).to_pandas()
    fig, ax = plt.subplots(figsize=(8, 5))
    for domain, group in pdf.groupby("domain"):
        group = group.sort_values("multiplier")
        ax.plot(group["multiplier"], group["mde_bps"], marker="o", label=str(domain))
    ax.axvline(STRICT_MULTIPLIER, color="grey", linestyle="--", linewidth=1, label="strict (tau=1.0)")
    ax.set_xlabel("L5 threshold multiplier (tau / materiality)")
    ax.set_ylabel("Economic MDE (bps)")
    ax.set_title("Gate-stack economic MDE vs L5 threshold at alpha=0.05")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "mde_vs_threshold.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_tpr_curves(tpr_rows: list[dict[str, Any]]) -> None:
    """Per-domain TPR vs planted edge at alpha0, one line per threshold multiplier."""
    pdf = pl.DataFrame(tpr_rows).filter(pl.col("alpha") == ALPHA0).to_pandas()
    domains = sorted(pdf["domain"].unique())
    fig, axes = plt.subplots(1, len(domains), figsize=(5 * len(domains), 5), sharey=True)
    axes = axes if len(domains) > 1 else [axes]
    for ax, domain in zip(axes, domains):
        sub = pdf[pdf["domain"] == domain]
        for multiplier, group in sub.groupby("multiplier"):
            group = group.sort_values("edge_bps")
            ax.plot(group["edge_bps"], group["tpr"], marker=".", label=f"tau={multiplier:g}x")
        ax.axhline(POWER_TARGET, color="black", linewidth=1)
        ax.set_xscale("log")
        ax.set_xlabel("Planted edge (bps, log)")
        ax.set_title(str(domain))
    axes[0].set_ylabel("TPR (gate stack)")
    axes[-1].legend(fontsize=7, title="L5 threshold")
    fig.suptitle("TPR vs planted edge by L5 threshold at alpha=0.05")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "tpr_curves_by_threshold.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_mde_fpr_frontier(mde_rows: list[dict[str, Any]]) -> None:
    """MDE-vs-FPR lever frontier by domain at alpha0, annotated by threshold."""
    pdf = pl.DataFrame(mde_rows).filter(pl.col("alpha") == ALPHA0).to_pandas()
    fig, ax = plt.subplots(figsize=(8, 5))
    for domain, group in pdf.groupby("domain"):
        group = group.sort_values("multiplier")
        ax.plot(group["fpr"], group["mde_bps"], marker="o", label=str(domain))
        for _, row in group.iterrows():
            ax.annotate(
                f"{row['multiplier']:g}", (row["fpr"], row["mde_bps"]), fontsize=6,
                textcoords="offset points", xytext=(3, 3),
            )
    ax.axvline(ALPHA0, color="red", linewidth=1, label="alpha0 = 0.05")
    ax.set_xlabel("Gate-stack FPR")
    ax.set_ylabel("Economic MDE (bps)")
    ax.set_title("L5 lever frontier: MDE vs FPR at alpha=0.05 (label = tau multiplier)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "mde_fpr_frontier.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run the EXP-006 L5 threshold sweep and write summaries, frontier, and plots."""
    configure_logging()
    ensure_output_dirs()
    dependency_status = require_dependencies()

    draws = load_gate_draws()
    swept = sweep_thresholds(draws)

    fpr_rows = summarize_fpr(swept)
    tpr_rows = summarize_tpr(swept)
    edge_grid = positive_edge_grid(swept)
    mde_rows = compute_mde_frontier(fpr_rows, tpr_rows, edge_grid)
    check_rows, strict_reference_pass = strict_reference_check(swept, mde_rows)

    measurements_produced = bool(fpr_rows) and bool(tpr_rows) and bool(mde_rows)
    overall_status = (
        "COMPLETE" if measurements_produced and strict_reference_pass else "FAILED_REPRODUCTION"
    )

    # Per-draw reconstruction (~1.5M rows): write the Polars frame directly rather
    # than materialising a list[dict], keeping the large output bounded in memory.
    swept.select(
        "instrument", "domain", "scenario", "generator", "edge_bps", "draw",
        "alpha", "multiplier", "tau_bps", "ci_lower_bps", "passed_tau",
    ).write_csv(RESULTS_DIR / "threshold_draw_verdicts.csv")
    write_rows(RESULTS_DIR / "threshold_fpr_summary.csv", fpr_rows)
    write_rows(RESULTS_DIR / "threshold_tpr_summary.csv", tpr_rows)
    write_rows(RESULTS_DIR / "threshold_mde_summary.csv", mde_rows)
    write_rows(RESULTS_DIR / "strict_reference_check.csv", check_rows)
    write_json(
        RESULTS_DIR / "run_metadata.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "overall_status": overall_status,
            "measurements_produced": measurements_produced,
            "strict_reference_pass": strict_reference_pass,
            "dependencies": dependency_status,
            "multipliers": list(MULTIPLIERS),
            "strict_multiplier": STRICT_MULTIPLIER,
            "alpha_grid": sorted({float(row["alpha"]) for row in fpr_rows}),
            "alpha0": ALPHA0,
            "positive_edge_grid_bps": edge_grid,
            "gate_draw_rows": int(draws.height),
            "power_target": POWER_TARGET,
            "fpr_half_width_target": FPR_HALF_WIDTH_TARGET,
            "tpr_half_width_target": TPR_HALF_WIDTH_TARGET,
        },
    )

    plot_fpr_vs_threshold(fpr_rows)
    plot_mde_vs_threshold(mde_rows)
    plot_tpr_curves(tpr_rows)
    plot_mde_fpr_frontier(mde_rows)

    LOGGER.info("EXP-006 complete: %s", overall_status)
    LOGGER.info("Strict-reference reproduction of EXP-003 gate: %s", strict_reference_pass)
    LOGGER.info("Results: %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
