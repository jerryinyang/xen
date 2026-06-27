"""
Experiment EXP-001: Synthetic Substrate Validation.

Implements the analysis plan from ``analysis-plan.md``. The script validates
the P0 aggregation precondition and the known-null / known-positive substrate
used by later referee-calibration experiments. It never loads the final 30%
global holdout.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from tqdm.auto import tqdm

from xen.referee_calibration import (
    EDGE_GRID_BPS,
    DOMAIN_SPECS,
    build_domain_frames,
    cost_bps_for,
    coverage_grid_rows,
    list_timebar_files,
    load_analysis_data,
    next_log_returns_from_bars,
    p0_aggregation_checks,
    percentile_ci,
    permuted_returns,
    plant_positive_edge,
    random_state_positions,
    seed_for,
    strategy_return_bps,
    write_json,
)


LOGGER = logging.getLogger(__name__)

EXPERIMENT_ID = "EXP-001"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data"
EXPERIMENT_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"

NULL_DRAWS_PER_GENERATOR = 200
POSITIVE_DRAWS_PER_EDGE = 100
NULL_TOLERANCE_BPS = 1.0
SUMMARY_ALPHA = 0.05


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
# Substrate draw generation
# --------------------------------------------------------------------------- #
def null_draw_rows(
    *,
    instrument: str,
    domain: str,
    returns: np.ndarray,
    generator: str,
    draws: int,
) -> list[dict[str, Any]]:
    """Generate known-null oracle effects for one instrument/domain cell.

    Parameters
    ----------
    instrument, domain : str
        Cell identifiers used for seeding and labelling.
    returns : np.ndarray
        Real Close-to-Close next-step returns for the domain.
    generator : str
        ``"bar_permutation"`` (permutes returns) or ``"random_signal"``.
    draws : int
        Number of independent null draws.

    Returns
    -------
    list[dict[str, Any]]
        One row per draw with the gross oracle ``effect_bps`` (cost-free).
    """
    rows: list[dict[str, Any]] = []
    cost_bps = cost_bps_for(instrument, domain)
    for draw in range(draws):
        seed = seed_for(EXPERIMENT_ID, instrument, domain, generator, draw)
        states = random_state_positions(len(returns), seed)
        scoped_returns = (
            permuted_returns(returns, seed + 1) if generator == "bar_permutation" else returns
        )
        # Known-null validation checks for zero oracle-recoverable gross edge.
        # Costs are applied when validating planted net positives and when the
        # referees measure false positives in EXP-003.
        effect = strategy_return_bps(scoped_returns, states, cost_bps=0.0).mean()
        rows.append(
            {
                "instrument": instrument,
                "domain": domain,
                "generator": generator,
                "edge_bps": 0.0,
                "draw": draw,
                "effect_bps": float(effect),
                "cost_bps": cost_bps,
            }
        )
    return rows


def positive_draw_rows(
    *,
    instrument: str,
    domain: str,
    returns: np.ndarray,
    edge_bps: float,
    draws: int,
) -> list[dict[str, Any]]:
    """Generate known-positive oracle effects for one instrument/domain cell.

    Parameters
    ----------
    instrument, domain : str
        Cell identifiers used for seeding and labelling.
    returns : np.ndarray
        Real Close-to-Close next-step returns for the domain.
    edge_bps : float
        Planted net edge magnitude (bps/trade) injected before cost.
    draws : int
        Number of independent positive draws.

    Returns
    -------
    list[dict[str, Any]]
        One row per draw with the recovered net ``effect_bps``.
    """
    rows: list[dict[str, Any]] = []
    cost_bps = cost_bps_for(instrument, domain)
    for draw in range(draws):
        seed = seed_for(EXPERIMENT_ID, instrument, domain, "known_positive", edge_bps, draw)
        states = random_state_positions(len(returns), seed)
        planted = plant_positive_edge(
            returns,
            states,
            net_edge_bps=edge_bps,
            cost_bps=cost_bps,
        )
        effect = strategy_return_bps(planted, states, cost_bps=cost_bps).mean()
        rows.append(
            {
                "instrument": instrument,
                "domain": domain,
                "generator": "known_positive",
                "edge_bps": edge_bps,
                "draw": draw,
                "effect_bps": float(effect),
                "cost_bps": cost_bps,
            }
        )
    return rows


def summarize_draws(draw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate per-draw effects into per-cell PASS/INCONCLUSIVE/FAIL summaries.

    Parameters
    ----------
    draw_rows : list[dict[str, Any]]
        Per-draw rows from :func:`null_draw_rows` / :func:`positive_draw_rows`.

    Returns
    -------
    list[dict[str, Any]]
        One summary row per (instrument, domain, generator, edge_bps) with a
        percentile CI on the mean effect and a PASS/INCONCLUSIVE/FAIL status
        (INCONCLUSIVE = recovered but under-powered; see body).
    """
    frame = pl.DataFrame(draw_rows)
    summaries: list[dict[str, Any]] = []
    group_cols = ["instrument", "domain", "generator", "edge_bps"]
    for key_values, group in frame.group_by(group_cols, maintain_order=True):
        ci = percentile_ci(group.get_column("effect_bps").to_list(), alpha=SUMMARY_ALPHA)
        instrument, domain, generator, edge_bps = key_values
        if generator == "known_positive" and edge_bps > 0.0:
            # Two distinct sub-tests, separated per checkpoint design Sec. 11 / D-prec:
            #   1. RECOVERY (correctness of the injection): the per-draw mean must
            #      land within tolerance of the planted edge. A recovery miss is
            #      genuine substrate breakage -> FAIL.
            #   2. SIGNIFICANCE (precision / power): for m >= 1.0 the per-draw
            #      effect distribution should sit clear of zero (ci.lower > 0).
            #      When recovery holds but the draw distribution is too wide to
            #      clear zero, the cell is UNDER-POWERED, not broken -> INCONCLUSIVE.
            #      Sec. 11 predeclares this case (expected on the short 4h domain)
            #      as a first-class measured result, never a failure. The split is
            #      applied uniformly to every cell; only under-powered cells differ.
            tolerance = max(0.5, 0.15 * float(edge_bps))
            recovered = abs(ci.mean - float(edge_bps)) <= tolerance
            significant = edge_bps < 1.0 or ci.lower > 0.0
            if not recovered:
                status = "FAIL"
            elif significant:
                status = "PASS"
            else:
                status = "INCONCLUSIVE"
        else:
            status = (
                "PASS"
                if abs(ci.mean) <= NULL_TOLERANCE_BPS and ci.lower <= 0.0 <= ci.upper
                else "FAIL"
            )
        summaries.append(
            {
                "instrument": instrument,
                "domain": domain,
                "generator": generator,
                "edge_bps": float(edge_bps),
                "mean_effect_bps": ci.mean,
                "ci_lower_bps": ci.lower,
                "ci_upper_bps": ci.upper,
                "n_draws": ci.n,
                "status": status,
            }
        )
    return summaries


# --------------------------------------------------------------------------- #
# Plotting
# --------------------------------------------------------------------------- #
def plot_summary(summary_rows: list[dict[str, Any]]) -> None:
    """Plot known-null oracle effects and known-positive recovery curves.

    Parameters
    ----------
    summary_rows : list[dict[str, Any]]
        Per-cell summaries from :func:`summarize_draws`.
    """
    frame = pl.DataFrame(summary_rows)
    pdf = frame.to_pandas()
    nulls = pdf[pdf["generator"] != "known_positive"]
    positives = pdf[pdf["generator"] == "known_positive"]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    if not nulls.empty:
        labels = nulls["instrument"] + " " + nulls["domain"] + " " + nulls["generator"]
        axes[0].errorbar(
            nulls["mean_effect_bps"],
            range(len(nulls)),
            xerr=[
                nulls["mean_effect_bps"] - nulls["ci_lower_bps"],
                nulls["ci_upper_bps"] - nulls["mean_effect_bps"],
            ],
            fmt="o",
        )
        axes[0].axvline(0.0, color="black", linewidth=1)
        axes[0].set_yticks(range(len(nulls)), labels, fontsize=6)
        axes[0].set_title("Known-null oracle effect")
        axes[0].set_xlabel("Net bps/trade")
    if not positives.empty:
        grouped = positives.groupby(["domain", "edge_bps"], as_index=False)[
            "mean_effect_bps"
        ].mean()
        for domain, domain_pdf in grouped.groupby("domain"):
            axes[1].plot(
                domain_pdf["edge_bps"],
                domain_pdf["mean_effect_bps"],
                marker="o",
                label=domain,
            )
        axes[1].plot(EDGE_GRID_BPS, EDGE_GRID_BPS, color="black", linewidth=1, label="target")
        axes[1].set_title("Known-positive recovery")
        axes[1].set_xlabel("Planted net bps/trade")
        axes[1].set_ylabel("Recovered net bps/trade")
        axes[1].legend()
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "substrate_validation_summary.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_coverage(coverage_rows: list[dict[str, Any]]) -> None:
    """Plot dropped-window fraction per (instrument, domain, coverage) cell.

    Parameters
    ----------
    coverage_rows : list[dict[str, Any]]
        Coverage-grid rows from ``coverage_grid_rows``.
    """
    pdf = pl.DataFrame(coverage_rows).to_pandas()
    fig, ax = plt.subplots(figsize=(10, 5))
    labels = pdf["instrument"] + " " + pdf["domain"] + " " + pdf["coverage"]
    ax.bar(range(len(pdf)), pdf["dropped_window_fraction"])
    ax.set_xticks(range(len(pdf)), labels, rotation=90, fontsize=6)
    ax.set_ylabel("Dropped-window fraction")
    ax.set_title("Coverage retention grid")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "coverage_grid.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_p0(p0_rows: list[dict[str, Any]]) -> None:
    """Plot P0 aggregation-check status counts by period (incl. controls).

    Parameters
    ----------
    p0_rows : list[dict[str, Any]]
        P0 check rows from ``p0_aggregation_checks``.
    """
    pdf = pl.DataFrame(p0_rows).to_pandas()
    counts = (
        pdf.groupby(["period_minutes", "status"]).size().unstack(fill_value=0)
    )
    fig, ax = plt.subplots(figsize=(7, 4))
    counts.plot(kind="bar", ax=ax)
    ax.set_xlabel("Aggregation period (minutes)")
    ax.set_ylabel("P0 checks")
    ax.set_title("P0 aggregation check status by period (incl. negative controls)")
    ax.legend(title="status")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "p0_status.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run the EXP-001 substrate validation and write results/plots."""
    configure_logging()
    ensure_output_dirs()

    files = list_timebar_files(DATA_DIR)
    if not files:
        raise FileNotFoundError(f"No time-bar files found under {DATA_DIR / 'timebars'}")

    p0_rows: list[dict[str, Any]] = []
    coverage_rows: list[dict[str, Any]] = []
    draw_rows: list[dict[str, Any]] = []
    analysis_metadata: list[dict[str, Any]] = []
    inconclusive_cells: list[dict[str, Any]] = []

    for path in tqdm(files, desc="EXP-001 instruments"):
        data = load_analysis_data(path)
        analysis_metadata.append(
            {
                "instrument": data.instrument,
                "source_file": data.source_file,
                "total_rows": data.total_rows,
                "analysis_rows": data.analysis_rows,
                "train_rows": data.train_rows,
                "test_rows": data.test_rows,
                "analysis_start": data.analysis_start,
                "analysis_end": data.analysis_end,
                "train_end": data.train_end,
            }
        )
        p0_rows.extend(p0_aggregation_checks(data))
        coverage_rows.extend(coverage_grid_rows(data))

        domains = build_domain_frames(data.frame)
        for domain, domain_frame in domains.items():
            returns, _ = next_log_returns_from_bars(domain_frame)
            if len(returns) < DOMAIN_SPECS[domain].min_effective_n:
                # Scope: insufficient domain bars => INCONCLUSIVE cell (recorded,
                # not a hard crash); downstream measurement for it is blocked.
                LOGGER.warning(
                    "%s/%s inconclusive: %d returns < min_effective_n=%d",
                    data.instrument,
                    domain,
                    len(returns),
                    DOMAIN_SPECS[domain].min_effective_n,
                )
                inconclusive_cells.append(
                    {
                        "instrument": data.instrument,
                        "domain": domain,
                        "return_rows": len(returns),
                        "min_effective_n": DOMAIN_SPECS[domain].min_effective_n,
                        "reason": "insufficient_returns_for_draw_counts",
                    }
                )
                continue
            draw_rows.extend(
                null_draw_rows(
                    instrument=data.instrument,
                    domain=domain,
                    returns=returns,
                    generator="bar_permutation",
                    draws=NULL_DRAWS_PER_GENERATOR,
                )
            )
            draw_rows.extend(
                null_draw_rows(
                    instrument=data.instrument,
                    domain=domain,
                    returns=returns,
                    generator="random_signal",
                    draws=NULL_DRAWS_PER_GENERATOR,
                )
            )
            for edge_bps in EDGE_GRID_BPS:
                draw_rows.extend(
                    positive_draw_rows(
                        instrument=data.instrument,
                        domain=domain,
                        returns=returns,
                        edge_bps=float(edge_bps),
                        draws=POSITIVE_DRAWS_PER_EDGE,
                    )
                )

    summary_rows = summarize_draws(draw_rows)
    p0_pass = all(row["status"] == "PASS" for row in p0_rows)
    # The substrate is "broken" only on a genuine FAIL cell (a planted positive
    # whose mean fails to recover, or a known-null carrying a non-zero edge).
    # Under-powered positive cells (per-cell INCONCLUSIVE) are reported but do
    # NOT break the substrate (checkpoint design Sec. 11): they are a first-class
    # measured result on the short domain, not a validation failure.
    underpowered_rows = [row for row in summary_rows if row["status"] == "INCONCLUSIVE"]
    substrate_fail = any(row["status"] == "FAIL" for row in summary_rows)
    substrate_pass = not substrate_fail
    if not p0_pass or substrate_fail:
        overall_status = "FAIL"
    elif inconclusive_cells:
        # A domain had too few bars to run the draw protocol at all -> no
        # substrate measurement exists for it -> genuinely inconclusive overall.
        overall_status = "INCONCLUSIVE"
    else:
        # Substrate validated: recovery and null-ness confirmed for every cell;
        # any remaining significance shortfalls are under-powered cells, reported
        # via substrate_summary.csv / underpowered_cells.csv and run_metadata.
        overall_status = "PASS"

    write_rows(RESULTS_DIR / "analysis_metadata.csv", analysis_metadata)
    write_rows(RESULTS_DIR / "p0_aggregation_checks.csv", p0_rows)
    write_rows(RESULTS_DIR / "coverage_grid.csv", coverage_rows)
    write_rows(RESULTS_DIR / "substrate_draws.csv", draw_rows)
    write_rows(RESULTS_DIR / "substrate_summary.csv", summary_rows)
    if inconclusive_cells:
        write_rows(RESULTS_DIR / "inconclusive_cells.csv", inconclusive_cells)
    if underpowered_rows:
        write_rows(RESULTS_DIR / "underpowered_cells.csv", underpowered_rows)
    write_json(
        RESULTS_DIR / "run_metadata.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "overall_status": overall_status,
            "p0_pass": p0_pass,
            "substrate_pass": substrate_pass,
            "inconclusive_cells": len(inconclusive_cells),
            "underpowered_cells": len(underpowered_rows),
            "null_draws_per_generator": NULL_DRAWS_PER_GENERATOR,
            "positive_draws_per_edge": POSITIVE_DRAWS_PER_EDGE,
            "edge_grid_bps": list(EDGE_GRID_BPS),
        },
    )
    plot_summary(summary_rows)
    plot_coverage(coverage_rows)
    plot_p0(p0_rows)

    LOGGER.info("EXP-001 complete: %s", overall_status)
    LOGGER.info("Results: %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
