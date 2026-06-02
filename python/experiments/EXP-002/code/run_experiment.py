"""
Experiment EXP-002: Referee Golden-Fixture Correctness.

This script evaluates deterministic fixtures against the two frozen referees.
It does not load raw market data and does not touch the global holdout.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

from xen.referee_calibration import (
    gate_stack_verdict,
    minimal_baseline_verdict,
    random_state_positions,
    seed_for,
    write_json,
)


LOGGER = logging.getLogger(__name__)

EXPERIMENT_ID = "EXP-002"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXPERIMENT_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
EXP001_METADATA = (
    PROJECT_ROOT / "python" / "experiments" / "EXP-001" / "results" / "run_metadata.json"
)

FIXTURE_INSTRUMENT = "EURUSD"
FIXTURE_DOMAIN = "5m"
ALPHA = 0.05
BOOTSTRAP_RESAMPLES = 1000


@dataclass(frozen=True)
class Fixture:
    name: str
    returns: np.ndarray
    positions: np.ndarray
    expected_minimal: str
    expected_gate: str
    required_gate_legs: dict[str, bool]


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


def require_exp001_pass() -> None:
    """Fail fast unless EXP-001 recorded an overall PASS substrate status."""
    if not EXP001_METADATA.exists():
        raise FileNotFoundError(f"EXP-001 metadata not found: {EXP001_METADATA}")
    metadata = json.loads(EXP001_METADATA.read_text(encoding="utf-8"))
    if metadata.get("overall_status") != "PASS":
        raise RuntimeError(f"EXP-001 did not pass: {metadata}")


# --------------------------------------------------------------------------- #
# Fixture construction
# --------------------------------------------------------------------------- #
def state_aligned_fixture(
    length: int, edge_bps: float, *, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    """Build a state-aligned (returns, positions) fixture with a known net edge.

    Parameters
    ----------
    length : int
        Number of bars.
    edge_bps : float
        Target net candidate effect (bps/trade) after the EURUSD/5m cost.
    seed : int
        Seed for the random state-position sequence.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        ``(returns, positions)`` arrays.
    """
    positions = random_state_positions(length, seed)
    # EURUSD/5m cost is 1 bps in the frozen defaults. The gross return is set so
    # the net candidate effect equals edge_bps.
    returns = positions * ((edge_bps + 1.0) / 10_000.0)
    return returns, positions


def build_fixtures() -> list[Fixture]:
    """Return the frozen golden-fixture registry exercised by both referees.

    Each fixture pins a deterministic (returns, positions) pair with the
    hand-reasoned verdict and gate-leg exposures it must reproduce.

    Returns
    -------
    list[Fixture]
        The five golden fixtures in evaluation order.
    """
    positive_returns, positive_positions = state_aligned_fixture(
        600,
        6.0,
        seed=seed_for(EXPERIMENT_ID, "positive_oracle"),
    )
    small_returns, small_positions = state_aligned_fixture(
        600,
        0.2,
        seed=seed_for(EXPERIMENT_ID, "sub_material"),
    )
    one_sided_returns = np.full(600, 0.0008)
    one_sided_positions = np.ones(600)

    negative_positions = random_state_positions(600, seed_for(EXPERIMENT_ID, "negative"))
    negative_returns = -negative_positions * 0.0002

    # Trending pattern with runs of length 3 so naive momentum is genuinely
    # profitable (gross +2.67 bps/bar). The candidate IS its own naive control,
    # so it clears the gross minimal-baseline test but fails gate L3: it cannot
    # beat the naive control it exactly equals. A 2-bar whipsaw would instead
    # make momentum unprofitable, which would (wrongly) fail the minimal test too.
    trend_returns = np.tile(np.array([0.0008, 0.0008, 0.0008, -0.0008, -0.0008, -0.0008]), 200)
    naive_equivalent_positions = np.zeros(len(trend_returns))
    naive_equivalent_positions[1:] = np.sign(trend_returns[:-1])

    return [
        Fixture(
            name="positive_oracle",
            returns=positive_returns,
            positions=positive_positions,
            expected_minimal="PASS",
            expected_gate="PASS",
            required_gate_legs={
                "L1_readiness": True,
                "L2_integrity": True,
                "L3_outcome": True,
                "L4_stability": True,
                "L5_materiality": True,
            },
        ),
        Fixture(
            name="null_negative_edge",
            returns=negative_returns,
            positions=negative_positions,
            expected_minimal="REJECT",
            expected_gate="REJECT",
            required_gate_legs={"L3_outcome": False, "L5_materiality": False},
        ),
        Fixture(
            name="readiness_one_sided",
            returns=one_sided_returns,
            positions=one_sided_positions,
            expected_minimal="PASS",
            expected_gate="REJECT",
            required_gate_legs={"L1_readiness": False},
        ),
        Fixture(
            name="materiality_too_small",
            returns=small_returns,
            positions=small_positions,
            expected_minimal="PASS",
            expected_gate="REJECT",
            required_gate_legs={"L5_materiality": False},
        ),
        Fixture(
            name="naive_equivalent",
            returns=trend_returns,
            positions=naive_equivalent_positions,
            expected_minimal="PASS",
            expected_gate="REJECT",
            required_gate_legs={"L3_outcome": False},
        ),
    ]


# --------------------------------------------------------------------------- #
# Check execution
# --------------------------------------------------------------------------- #
def evaluate_fixture(fixture: Fixture) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Evaluate one fixture against both referees and the gate-leg matrix.

    Parameters
    ----------
    fixture : Fixture
        The golden fixture to evaluate.

    Returns
    -------
    tuple[list[dict[str, Any]], list[dict[str, Any]]]
        ``(verdict_rows, leg_exposure_rows)`` for the fixture.
    """
    minimal = minimal_baseline_verdict(
        fixture.returns,
        fixture.positions,
        instrument=FIXTURE_INSTRUMENT,
        domain=FIXTURE_DOMAIN,
        alpha=ALPHA,
        n_bootstrap=BOOTSTRAP_RESAMPLES,
        seed=seed_for(EXPERIMENT_ID, fixture.name, "minimal"),
    )
    gate = gate_stack_verdict(
        fixture.returns,
        fixture.positions,
        instrument=FIXTURE_INSTRUMENT,
        domain=FIXTURE_DOMAIN,
        alpha=ALPHA,
        n_bootstrap=BOOTSTRAP_RESAMPLES,
        seed=seed_for(EXPERIMENT_ID, fixture.name, "gate"),
    )
    gate_legs = json.loads(gate["leg_results"])

    result_rows = []
    for referee_result, expected in (
        (minimal, fixture.expected_minimal),
        (gate, fixture.expected_gate),
    ):
        result_rows.append(
            {
                "fixture": fixture.name,
                "referee": referee_result["referee"],
                "expected_verdict": expected,
                "actual_verdict": referee_result["verdict"],
                "status": "PASS" if referee_result["verdict"] == expected else "FAIL",
                "effect_bps": referee_result["effect_bps"],
                "ci_lower_bps": referee_result["ci_lower_bps"],
                "ci_upper_bps": referee_result["ci_upper_bps"],
                "effective_n": referee_result["effective_n"],
                "block_length": referee_result["block_length"],
            }
        )

    leg_rows = []
    leg_names = (
        "L1_readiness",
        "L2_integrity",
        "L3_outcome",
        "L4_stability",
        "L5_materiality",
    )
    for leg_name in leg_names:
        actual = bool(gate_legs.get(leg_name))
        expected = fixture.required_gate_legs.get(leg_name)
        leg_rows.append(
            {
                "fixture": fixture.name,
                "leg": leg_name,
                "actual": actual,
                "expected_if_required": expected,
                "status": "PASS" if expected is None or actual == expected else "FAIL",
            }
        )
    return result_rows, leg_rows


# --------------------------------------------------------------------------- #
# Plotting
# --------------------------------------------------------------------------- #
def plot_results(result_rows: list[dict[str, Any]], leg_rows: list[dict[str, Any]]) -> None:
    """Plot fixture verdict checks and gate-leg exposure checks side by side.

    Parameters
    ----------
    result_rows : list[dict[str, Any]]
        Per-fixture verdict-check rows.
    leg_rows : list[dict[str, Any]]
        Per-fixture gate-leg exposure rows.
    """
    result_pdf = pl.DataFrame(result_rows).to_pandas()
    leg_pdf = pl.DataFrame(leg_rows).to_pandas()

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    result_status = result_pdf.assign(ok=result_pdf["status"].eq("PASS").astype(int))
    axes[0].bar(range(len(result_status)), result_status["ok"])
    axes[0].set_xticks(
        range(len(result_status)),
        result_status["fixture"] + " " + result_status["referee"],
        rotation=90,
        fontsize=7,
    )
    axes[0].set_ylim(0, 1.1)
    axes[0].set_title("Fixture verdict checks")

    leg_status = leg_pdf.assign(ok=leg_pdf["status"].eq("PASS").astype(int))
    axes[1].bar(range(len(leg_status)), leg_status["ok"])
    axes[1].set_xticks(
        range(len(leg_status)),
        leg_status["fixture"] + " " + leg_status["leg"],
        rotation=90,
        fontsize=6,
    )
    axes[1].set_ylim(0, 1.1)
    axes[1].set_title("Gate-leg exposure checks")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "golden_fixture_checks.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run the EXP-002 golden-fixture correctness checks and write outputs."""
    configure_logging()
    ensure_output_dirs()
    require_exp001_pass()

    result_rows: list[dict[str, Any]] = []
    leg_rows: list[dict[str, Any]] = []
    for fixture in build_fixtures():
        fixture_results, fixture_legs = evaluate_fixture(fixture)
        result_rows.extend(fixture_results)
        leg_rows.extend(fixture_legs)

    overall_status = (
        "PASS"
        if all(row["status"] == "PASS" for row in result_rows)
        and all(row["status"] == "PASS" for row in leg_rows)
        else "FAIL"
    )
    write_rows(RESULTS_DIR / "golden_fixture_results.csv", result_rows)
    write_rows(RESULTS_DIR / "leg_exposure_matrix.csv", leg_rows)
    write_json(
        RESULTS_DIR / "run_metadata.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "overall_status": overall_status,
            "fixtures": [fixture.name for fixture in build_fixtures()],
            "alpha": ALPHA,
            "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        },
    )
    plot_results(result_rows, leg_rows)

    LOGGER.info("EXP-002 complete: %s", overall_status)
    LOGGER.info("Results: %s", RESULTS_DIR)


if __name__ == "__main__":
    main()

