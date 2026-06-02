"""
Experiment EXP-004: Real Dogfood Consistency Anchor.

Evaluates fixed Donchian and MA-crossover candidates against the calibrated MDE
map from EXP-003. The script uses only the first 70% analysis slice and never
loads the global holdout.
"""
from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from tqdm.auto import tqdm

from xen.referee_calibration import (
    ALPHA_GRID,
    build_domain_frames,
    domain_split_index,
    donchian_breakout_positions,
    evaluate_referees,
    list_timebar_files,
    load_analysis_data,
    ma_crossover_positions,
    next_log_returns_from_bars,
    seed_for,
    write_json,
)


LOGGER = logging.getLogger(__name__)

EXPERIMENT_ID = "EXP-004"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data"
EXPERIMENT_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
EXP003_METADATA = (
    PROJECT_ROOT / "python" / "experiments" / "EXP-003" / "results" / "run_metadata.json"
)
EXP003_MDE = PROJECT_ROOT / "python" / "experiments" / "EXP-003" / "results" / "mde_summary.csv"

ALPHA = 0.05
BOOTSTRAP_RESAMPLES = 1000
DONCHIAN_LOOKBACK = 20
MA_FAST = 20
MA_SLOW = 50


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


def require_exp003_outputs() -> None:
    """Fail fast unless the EXP-003 metadata and MDE summary both exist."""
    if not EXP003_METADATA.exists():
        raise FileNotFoundError(f"EXP-003 metadata not found: {EXP003_METADATA}")
    if not EXP003_MDE.exists():
        raise FileNotFoundError(f"EXP-003 MDE summary not found: {EXP003_MDE}")


# --------------------------------------------------------------------------- #
# MDE lookup and consistency
# --------------------------------------------------------------------------- #
def load_mde_map() -> dict[tuple[str, str], dict[str, float | str]]:
    """Load the EXP-003 MDE map at the operating alpha, keyed by (domain, referee).

    Returns
    -------
    dict[tuple[str, str], dict[str, float | str]]
        Per (domain, referee): ``mde_bps``, ``mde_grid_uncertainty_bps``, and
        the cell ``status``.
    """
    frame = pl.read_csv(EXP003_MDE).filter(pl.col("alpha") == ALPHA)
    output: dict[tuple[str, str], dict[str, float | str]] = {}
    for row in frame.iter_rows(named=True):
        output[(row["domain"], row["referee"])] = {
            "mde_bps": float(row["mde_bps"]) if row["mde_bps"] is not None else math.nan,
            "mde_grid_uncertainty_bps": (
                float(row["mde_grid_uncertainty_bps"])
                if row["mde_grid_uncertainty_bps"] is not None
                else math.nan
            ),
            "status": str(row["status"]),
        }
    return output


def consistency_status(
    *,
    verdict: str,
    effect_bps: float,
    ci_lower_bps: float,
    mde_bps: float,
    uncertainty_bps: float,
) -> tuple[str, str]:
    """Compare a candidate verdict to its domain MDE per the section 10 rule.

    Parameters
    ----------
    verdict : str
        The referee verdict (``PASS`` / ``REJECT``).
    effect_bps : float
        Candidate point-estimate net effect (bps/trade).
    ci_lower_bps : float
        Lower bound of the candidate effect CI.
    mde_bps : float
        The domain/referee empirical MDE.
    uncertainty_bps : float
        Grey-band half-width (grid MDE uncertainty).

    Returns
    -------
    tuple[str, str]
        ``(consistency_status, reason)``.
    """
    if not math.isfinite(mde_bps):
        return "INCONCLUSIVE", "missing_mde"
    uncertainty = uncertainty_bps if math.isfinite(uncertainty_bps) else 0.0
    if ci_lower_bps >= mde_bps - uncertainty:
        expected = "PASS"
    elif effect_bps < mde_bps + uncertainty:
        expected = "REJECT"
    else:
        expected = "GREY"

    if expected == "GREY":
        return "INCONCLUSIVE", "grey_band"
    if verdict == expected:
        return "PASS", f"matched_{expected.lower()}"
    return "FAIL", f"expected_{expected.lower()}_got_{verdict.lower()}"


# --------------------------------------------------------------------------- #
# Candidate generation
# --------------------------------------------------------------------------- #
def candidate_positions(domain_frame: pl.DataFrame) -> dict[str, np.ndarray]:
    """Compute Donchian and MA-crossover positions aligned to next returns.

    Parameters
    ----------
    domain_frame : pl.DataFrame
        Resampled OHLC bars for one domain.

    Returns
    -------
    dict[str, np.ndarray]
        ``{"donchian_20": ..., "ma_20_50": ...}`` position arrays.
    """
    ordered = domain_frame.sort("CloseTime")
    high = np.asarray(ordered.get_column("High"), dtype=float)
    low = np.asarray(ordered.get_column("Low"), dtype=float)
    close = np.asarray(ordered.get_column("Close"), dtype=float)
    return {
        "donchian_20": donchian_breakout_positions(
            high,
            low,
            close,
            lookback=DONCHIAN_LOOKBACK,
        ),
        "ma_20_50": ma_crossover_positions(close, fast=MA_FAST, slow=MA_SLOW),
    }


def evaluate_candidates(
    *,
    instrument: str,
    domain: str,
    domain_frame: pl.DataFrame,
    train_end_ts: Any,
    mde_map: dict[tuple[str, str], dict[str, float | str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Evaluate both dogfood candidates and score MDE-map consistency.

    Parameters
    ----------
    instrument, domain : str
        Cell identifiers used for seeding and labelling.
    domain_frame : pl.DataFrame
        Resampled OHLC bars for the domain.
    train_end_ts : Any
        Shared 1-minute train/test boundary timestamp.
    mde_map : dict[tuple[str, str], dict[str, float | str]]
        EXP-003 MDE map keyed by (domain, referee).

    Returns
    -------
    tuple[list[dict[str, Any]], list[dict[str, Any]]]
        ``(effect_rows, consistency_rows)``.
    """
    returns, aligned = next_log_returns_from_bars(domain_frame)
    # Train/test cut shared across domains via the 1m boundary timestamp.
    split_index = domain_split_index(aligned, train_end_ts)
    effect_rows: list[dict[str, Any]] = []
    consistency_rows: list[dict[str, Any]] = []
    for strategy_name, positions in candidate_positions(domain_frame).items():
        for verdict in evaluate_referees(
            returns,
            positions,
            instrument=instrument,
            domain=domain,
            alpha_values=(ALPHA,),
            n_bootstrap=BOOTSTRAP_RESAMPLES,
            seed=seed_for(EXPERIMENT_ID, instrument, domain, strategy_name),
            split_index=split_index,
        ):
            mde = mde_map.get((domain, verdict["referee"]), {})
            mde_bps = float(mde.get("mde_bps", math.nan))
            uncertainty_bps = float(mde.get("mde_grid_uncertainty_bps", math.nan))
            status, reason = consistency_status(
                verdict=verdict["verdict"],
                effect_bps=float(verdict["effect_bps"]),
                ci_lower_bps=float(verdict["ci_lower_bps"]),
                mde_bps=mde_bps,
                uncertainty_bps=uncertainty_bps,
            )
            base = {
                "instrument": instrument,
                "domain": domain,
                "strategy": strategy_name,
                "referee": verdict["referee"],
                "alpha": ALPHA,
                "verdict": verdict["verdict"],
                "effect_bps": verdict["effect_bps"],
                "ci_lower_bps": verdict["ci_lower_bps"],
                "ci_upper_bps": verdict["ci_upper_bps"],
                "effective_n": verdict["effective_n"],
                "block_length": verdict["block_length"],
                "mde_bps": mde_bps,
                "mde_grid_uncertainty_bps": uncertainty_bps,
            }
            effect_rows.append(base)
            consistency = dict(base)
            consistency.update({"consistency_status": status, "reason": reason})
            consistency_rows.append(consistency)
    return effect_rows, consistency_rows


# --------------------------------------------------------------------------- #
# Plotting
# --------------------------------------------------------------------------- #
def plot_effects(effect_rows: list[dict[str, Any]]) -> None:
    """Plot dogfood net effects with CIs against the MDE markers.

    Parameters
    ----------
    effect_rows : list[dict[str, Any]]
        Per-candidate effect rows from :func:`evaluate_candidates`.
    """
    pdf = pl.DataFrame(effect_rows).to_pandas()
    fig, ax = plt.subplots(figsize=(10, 5))
    labels = pdf["instrument"] + " " + pdf["domain"] + " " + pdf["strategy"] + " " + pdf["referee"]
    ax.errorbar(
        range(len(pdf)),
        pdf["effect_bps"],
        yerr=[pdf["effect_bps"] - pdf["ci_lower_bps"], pdf["ci_upper_bps"] - pdf["effect_bps"]],
        fmt="o",
        markersize=3,
    )
    ax.scatter(range(len(pdf)), pdf["mde_bps"], marker="_", color="red", label="MDE")
    ax.set_xticks(range(len(pdf)), labels, rotation=90, fontsize=5)
    ax.set_ylabel("Net bps/trade")
    ax.set_title("Dogfood effects vs MDE")
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "dogfood_effects_vs_mde.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_consistency(consistency_rows: list[dict[str, Any]]) -> None:
    """Plot dogfood consistency-status counts per domain.

    Parameters
    ----------
    consistency_rows : list[dict[str, Any]]
        Per-candidate consistency rows from :func:`evaluate_candidates`.
    """
    frame = pl.DataFrame(consistency_rows)
    summary = frame.group_by(["domain", "consistency_status"]).agg(pl.len().alias("count"))
    pdf = summary.to_pandas()
    fig, ax = plt.subplots(figsize=(7, 4))
    labels = pdf["domain"] + " " + pdf["consistency_status"]
    ax.bar(range(len(pdf)), pdf["count"])
    ax.set_xticks(range(len(pdf)), labels, rotation=45, ha="right")
    ax.set_ylabel("Cells")
    ax.set_title("Dogfood consistency status")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "dogfood_consistency_counts.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_verdict_matrix(effect_rows: list[dict[str, Any]]) -> None:
    """Plot a candidate-by-referee PASS/REJECT verdict heatmap.

    Parameters
    ----------
    effect_rows : list[dict[str, Any]]
        Per-candidate effect rows from :func:`evaluate_candidates`.
    """
    pdf = pl.DataFrame(effect_rows).to_pandas()
    pdf["ok"] = (pdf["verdict"] == "PASS").astype(int)
    pdf["row"] = pdf["instrument"] + " " + pdf["domain"] + " " + pdf["strategy"]
    pivot = pdf.pivot_table(index="row", columns="referee", values="ok", aggfunc="max")
    fig, ax = plt.subplots(figsize=(7, max(4.0, 0.3 * len(pivot))))
    im = ax.imshow(pivot.values, aspect="auto", cmap="RdYlGn", vmin=0, vmax=1)
    ax.set_xticks(range(len(pivot.columns)), list(pivot.columns), rotation=45, ha="right")
    ax.set_yticks(range(len(pivot.index)), list(pivot.index), fontsize=6)
    ax.set_title("Candidate verdicts (green=PASS, red=REJECT)")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "candidate_verdict_matrix.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run the EXP-004 dogfood consistency anchor and write results/plots."""
    configure_logging()
    ensure_output_dirs()
    require_exp003_outputs()
    mde_map = load_mde_map()

    files = list_timebar_files(DATA_DIR)
    if not files:
        raise FileNotFoundError(f"No time-bar files found under {DATA_DIR / 'timebars'}")

    effect_rows: list[dict[str, Any]] = []
    consistency_rows: list[dict[str, Any]] = []
    analysis_rows: list[dict[str, Any]] = []
    for path in tqdm(files, desc="EXP-004 instruments"):
        data = load_analysis_data(path)
        for domain, frame in build_domain_frames(data.frame).items():
            analysis_rows.append(
                {
                    "instrument": data.instrument,
                    "source_file": data.source_file,
                    "domain": domain,
                    "domain_rows": frame.height,
                    "analysis_start": data.analysis_start,
                    "analysis_end": data.analysis_end,
                }
            )
            effects, consistency = evaluate_candidates(
                instrument=data.instrument,
                domain=domain,
                domain_frame=frame,
                train_end_ts=data.train_end_ts,
                mde_map=mde_map,
            )
            effect_rows.extend(effects)
            consistency_rows.extend(consistency)

    failed = any(row["consistency_status"] == "FAIL" for row in consistency_rows)
    inconclusive = any(row["consistency_status"] == "INCONCLUSIVE" for row in consistency_rows)
    overall_status = "FAIL" if failed else "INCONCLUSIVE" if inconclusive else "PASS"

    write_rows(RESULTS_DIR / "analysis_metadata.csv", analysis_rows)
    write_rows(RESULTS_DIR / "dogfood_effects.csv", effect_rows)
    write_rows(RESULTS_DIR / "dogfood_consistency.csv", consistency_rows)
    write_json(
        RESULTS_DIR / "run_metadata.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "overall_status": overall_status,
            "alpha": ALPHA,
            "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
            "donchian_lookback": DONCHIAN_LOOKBACK,
            "ma_fast": MA_FAST,
            "ma_slow": MA_SLOW,
            "alpha_grid_reference": list(ALPHA_GRID),
        },
    )
    plot_effects(effect_rows)
    plot_consistency(consistency_rows)
    plot_verdict_matrix(effect_rows)

    LOGGER.info("EXP-004 complete: %s", overall_status)
    LOGGER.info("Results: %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
