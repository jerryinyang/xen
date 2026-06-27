"""
Experiment EXP-014: Incremental Referee Golden-Fixture Correctness (Track B logic gate).

Deterministic correctness gate for the incremental referee (``xen.incremental_referee``)
before EXP-015 operating-characteristic calibration. It replays a frozen registry of
seven golden fixtures -- one per row of the predeclared coverage matrix -- and
confirms that the referee (i) reproduces every hand-reasoned verdict, (ii) reproduces
every predeclared L1-L5 leg state, and (iii) exposes ALL FIVE legs for every fixture
with no short-circuit, including the L3 -> reference-control generalization.

This is a logic test on deterministic in-memory return/position fixtures: no market
Parquet is read and the global holdout is never touched. The fixture returns
represent real-price return contributions (no synthetic chart prices).

Pre-execution confirmation gate: EXP-013 must have PASSED and the Track B
predeclaration token ``PHASE003-TRACKB-PREDECLARATION-CONFIRMED`` (covering D-incr-legs)
must be recorded in governance before fixtures are replayed. Manual execution gate:
do not run inside the pipeline.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

from xen.incremental_referee import EPISODE_LENGTHS, RC_MASKS, incremental_gate_verdict
from xen.referee_calibration import write_json

LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants & paths
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-014"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXPERIMENTS_DIR = PROJECT_ROOT / "python" / "experiments"
EXPERIMENT_DIR = EXPERIMENTS_DIR / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
GOVERNANCE_DIR = EXPERIMENT_DIR / "governance"
EXP013_META = EXPERIMENTS_DIR / "EXP-013" / "results" / "run_metadata.json"

PREDECLARATION_TOKEN = "PHASE003-TRACKB-PREDECLARATION-CONFIRMED"

# Fixture cell: EURUSD/5m (cost 1.0 bps, materiality 0.5 bps, episode length 24).
FIXTURE_INSTRUMENT = "EURUSD"
FIXTURE_DOMAIN = "5m"
ALPHA = 0.05
BOOTSTRAP_RESAMPLES = 1000
BOOTSTRAP_SEED = 7
N_EPISODES = 2000  # large enough that L1 episode counts clear min_state_count
BASE_NOISE_BPS = 2.0
LEG_NAMES: tuple[str, ...] = (
    "L1_readiness",
    "L2_significance",
    "L3_reference_control",
    "L4_cross_market",
    "L5_materiality",
)


@dataclass(frozen=True)
class Fixture:
    """A frozen golden fixture: construction parameters + hand-reasoned expectations."""

    name: str
    purpose: str
    seed: int
    expected_verdict: str
    expected_legs: dict[str, bool]
    cc_drift_bps: float
    overlap_drift_bps: float = 0.0
    r_only_drift_bps: float = 0.0
    cc_noise_bps: float = 0.0
    one_directional_cc: bool = False
    reversal_cc: bool = False
    notes: str = field(default="")


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
# Governance + dependency gate
# --------------------------------------------------------------------------- #
def find_predeclaration_token() -> dict[str, Any]:
    """Search the governance dir for the Track B predeclaration-confirmation token."""
    confirmed = False
    source: str | None = None
    if GOVERNANCE_DIR.exists():
        for path in sorted(GOVERNANCE_DIR.glob("*.md")):
            if PREDECLARATION_TOKEN in path.read_text(encoding="utf-8"):
                confirmed = True
                source = path.name
                break
    return {"token": PREDECLARATION_TOKEN, "confirmed": confirmed, "source": source}


def require_exp013_pass() -> str:
    """Fail fast unless EXP-013 recorded an overall PASS substrate status."""
    if not EXP013_META.exists():
        raise FileNotFoundError(f"EXP-013 metadata not found: {EXP013_META}")
    meta = json.loads(EXP013_META.read_text(encoding="utf-8"))
    if meta.get("overall_status") != "PASS":
        raise RuntimeError(f"EXP-013 did not PASS: {meta.get('overall_status')}")
    return str(meta.get("overall_status"))


def write_blocked_metadata(token_status: dict[str, Any], reason: str) -> None:
    """Record a BLOCKED run (gate unsatisfied) without replaying fixtures."""
    write_json(
        RESULTS_DIR / "run_metadata.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "overall_status": "BLOCKED",
            "measurements_produced": False,
            "reason": reason,
            "predeclaration_gate": token_status,
        },
    )


# --------------------------------------------------------------------------- #
# Fixture construction (deterministic, in-memory; real-price return contributions)
# --------------------------------------------------------------------------- #
def build_fixture_arrays(fixture: Fixture) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Construct deterministic ``(returns, R_positions, C_positions)`` for a fixture.

    A blockwise latent state (episode length = the 5m episode length) is partitioned
    into the four R/C masks. ``R = state`` on R-only/overlap, ``C = state`` on
    C-change/overlap. Per-region drift sets the marginal (C-change) edge, the overlap
    edge (which feeds C's standalone edge and R), and the R-only edge. Optional
    switches force a one-directional incremental position (L1) or a train/test sign
    reversal of the marginal edge (L4). Returns carry small symmetric noise so the
    block bootstrap has genuine variance.
    """
    episode_length = EPISODE_LENGTHS[FIXTURE_DOMAIN]
    rng = np.random.default_rng(fixture.seed)
    signs = rng.choice(np.array([-1.0, 1.0]), size=N_EPISODES)
    mask_by_episode = np.array(RC_MASKS)[rng.permutation(N_EPISODES) % len(RC_MASKS)]
    state = np.repeat(signs, episode_length)
    masks = np.repeat(mask_by_episode, episode_length)
    n = len(state)
    c_change = masks == "C_change"
    overlap = masks == "overlap"
    r_only = masks == "R_only"

    if fixture.one_directional_cc:
        state = state.copy()
        state[c_change] = 1.0

    r_positions = np.where(np.isin(masks, ["R_only", "overlap"]), state, 0.0)
    c_positions = np.where(np.isin(masks, ["C_change", "overlap"]), state, 0.0)

    returns = rng.normal(0.0, BASE_NOISE_BPS / 10_000.0, n)
    if fixture.reversal_cc:
        half = int(n * 0.7)
        drift = np.where(np.arange(n) < half, -fixture.cc_drift_bps, fixture.cc_drift_bps)
        returns = returns + np.where(c_change, state * drift / 10_000.0, 0.0)
    else:
        returns = returns + np.where(c_change, state * fixture.cc_drift_bps / 10_000.0, 0.0)
    returns = returns + np.where(overlap, state * fixture.overlap_drift_bps / 10_000.0, 0.0)
    returns = returns + np.where(r_only, state * fixture.r_only_drift_bps / 10_000.0, 0.0)
    if fixture.cc_noise_bps > 0.0:
        returns = returns + np.where(
            c_change, rng.normal(0.0, fixture.cc_noise_bps / 10_000.0, n), 0.0
        )
    return returns, r_positions, c_positions


def build_fixtures() -> list[Fixture]:
    """Return the frozen golden-fixture registry (one per coverage-matrix row).

    Parameters are predeclared so each fixture deterministically exercises exactly
    one failing leg (or all-pass), reproducing the EXP-014 coverage matrix. Any
    fixture added here requires a dated pre-results amendment.
    """
    return [
        Fixture(
            name="all_pass_incremental",
            purpose="Positive marginal edge: sufficient denominator, significance, "
            "reference-control improvement, cross-market support, materiality.",
            seed=100, expected_verdict="PASS",
            expected_legs={"L1_readiness": True, "L2_significance": True,
                           "L3_reference_control": True, "L4_cross_market": True,
                           "L5_materiality": True},
            cc_drift_bps=4.0, overlap_drift_bps=4.0,
        ),
        Fixture(
            name="l1_readiness_fail",
            purpose="One-directional incremental position -> no down-episodes -> "
            "insufficient incremental readiness while other quantities are favorable.",
            seed=101, expected_verdict="REJECT",
            expected_legs={"L1_readiness": False, "L2_significance": True,
                           "L3_reference_control": True, "L4_cross_market": True,
                           "L5_materiality": True},
            cc_drift_bps=4.0, overlap_drift_bps=4.0, one_directional_cc=True,
        ),
        Fixture(
            name="l2_significance_fail",
            purpose="C loses materially on overlap so the standalone candidate edge "
            "CI lower bound fails, though its marginal edge beyond R is fine.",
            seed=102, expected_verdict="REJECT",
            expected_legs={"L1_readiness": True, "L2_significance": False,
                           "L3_reference_control": True, "L4_cross_market": True,
                           "L5_materiality": True},
            cc_drift_bps=4.0, overlap_drift_bps=-12.0,
        ),
        Fixture(
            name="l3_reference_control_fail",
            purpose="Standalone-looking edge (via overlap) but the marginal edge "
            "beyond R is too noisy to exclude zero -- adds no significant edge beyond R.",
            seed=103, expected_verdict="REJECT",
            expected_legs={"L1_readiness": True, "L2_significance": True,
                           "L3_reference_control": False, "L4_cross_market": True,
                           "L5_materiality": True},
            cc_drift_bps=6.0, overlap_drift_bps=8.0, cc_noise_bps=150.0,
        ),
        Fixture(
            name="l4_cross_market_fail",
            purpose="Marginal edge reverses sign across the two segments -> required "
            "cross-market confirmation is absent, though the test segment passes locally.",
            seed=104, expected_verdict="REJECT",
            expected_legs={"L1_readiness": True, "L2_significance": True,
                           "L3_reference_control": True, "L4_cross_market": False,
                           "L5_materiality": True},
            cc_drift_bps=6.0, overlap_drift_bps=6.0, reversal_cc=True,
        ),
        Fixture(
            name="l5_materiality_fail",
            purpose="Marginal edge is positive and significant but its magnitude sits "
            "below the materiality buffer.",
            seed=105, expected_verdict="REJECT",
            expected_legs={"L1_readiness": True, "L2_significance": True,
                           "L3_reference_control": True, "L4_cross_market": True,
                           "L5_materiality": False},
            cc_drift_bps=0.45, overlap_drift_bps=4.0,
        ),
        Fixture(
            name="redundant_shared_structure",
            purpose="R and C share latent structure (overlap) with no marginal edge: "
            "guards against a phantom incremental pass from shared structure.",
            seed=106, expected_verdict="REJECT",
            expected_legs={"L1_readiness": True, "L2_significance": False,
                           "L3_reference_control": False, "L4_cross_market": True,
                           "L5_materiality": False},
            cc_drift_bps=0.0, overlap_drift_bps=0.0,
        ),
    ]


# --------------------------------------------------------------------------- #
# Fixture evaluation
# --------------------------------------------------------------------------- #
def evaluate_fixture(fixture: Fixture) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Evaluate one fixture: verdict reproduction + exposed leg-state reproduction."""
    returns, r_positions, c_positions = build_fixture_arrays(fixture)
    verdict = incremental_gate_verdict(
        returns, r_positions, c_positions,
        instrument=FIXTURE_INSTRUMENT, domain=FIXTURE_DOMAIN, alpha=ALPHA,
        n_bootstrap=BOOTSTRAP_RESAMPLES, seed=BOOTSTRAP_SEED, split_index=None,
    )
    legs = json.loads(verdict["leg_results"])
    verdict_row = {
        "fixture": fixture.name,
        "expected_verdict": fixture.expected_verdict,
        "actual_verdict": verdict["verdict"],
        "verdict_status": "PASS" if verdict["verdict"] == fixture.expected_verdict else "FAIL",
        "incremental_edge_bps": verdict["incremental_edge_bps"],
        "incremental_ci_lower_bps": verdict["incremental_ci_lower_bps"],
        "standalone_edge_bps": verdict["standalone_edge_bps"],
        "standalone_ci_lower_bps": verdict["standalone_ci_lower_bps"],
        "effective_n": verdict["effective_n"],
        "denominator_count": verdict["denominator_count"],
    }
    leg_rows: list[dict[str, Any]] = []
    for leg in LEG_NAMES:
        exposed = leg in legs
        actual = bool(legs.get(leg))
        expected = fixture.expected_legs[leg]
        leg_rows.append(
            {
                "fixture": fixture.name,
                "leg": leg,
                "exposed": exposed,
                "expected_state": expected,
                "actual_state": actual,
                "status": "PASS" if (exposed and actual == expected) else "FAIL",
            }
        )
    return verdict_row, leg_rows


# --------------------------------------------------------------------------- #
# Plotting
# --------------------------------------------------------------------------- #
def plot_verdict_matrix(verdict_rows: list[dict[str, Any]]) -> None:
    """Plot 1 -- verdict reproduction status by fixture."""
    pdf = pl.DataFrame(verdict_rows).to_pandas()
    fig, ax = plt.subplots(figsize=(9, 4))
    ok = pdf["verdict_status"].eq("PASS").astype(int)
    ax.bar(range(len(pdf)), ok, color=["seagreen" if v else "firebrick" for v in ok])
    ax.set_ylim(0, 1.2)
    ax.set_xticks(range(len(pdf)), pdf["fixture"], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("verdict reproduced (1 = PASS)")
    ax.set_title("EXP-014 Plot 1 -- incremental verdict reproduction by fixture")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "verdict_matrix.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_leg_exposure(leg_rows: list[dict[str, Any]]) -> None:
    """Plot 2 -- leg-exposure heatmap (all five legs recorded; no short-circuit)."""
    pdf = pl.DataFrame(leg_rows).to_pandas()
    fixtures = list(dict.fromkeys(pdf["fixture"]))
    grid = np.zeros((len(fixtures), len(LEG_NAMES)))
    for i, fx in enumerate(fixtures):
        for j, leg in enumerate(LEG_NAMES):
            row = pdf[(pdf["fixture"] == fx) & (pdf["leg"] == leg)].iloc[0]
            grid[i, j] = 1.0 if row["actual_state"] else 0.0
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.imshow(grid, aspect="auto", cmap="Greens", vmin=0, vmax=1)
    ax.set_xticks(range(len(LEG_NAMES)), [l.replace("_", "\n") for l in LEG_NAMES], fontsize=8)
    ax.set_yticks(range(len(fixtures)), fixtures, fontsize=8)
    for i in range(len(fixtures)):
        for j in range(len(LEG_NAMES)):
            ax.text(j, i, "T" if grid[i, j] else "F", ha="center", va="center", fontsize=9)
    ax.set_title("EXP-014 Plot 2 -- gate-leg states (all 5 exposed for every fixture)")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "leg_exposure.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_effect_summary(verdict_rows: list[dict[str, Any]]) -> None:
    """Plot 3 -- incremental vs standalone edge by fixture (how L3 cases differ)."""
    pdf = pl.DataFrame(verdict_rows).to_pandas()
    x = np.arange(len(pdf))
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - 0.2, pdf["incremental_edge_bps"], width=0.4, label="incremental edge", color="steelblue")
    ax.bar(x + 0.2, pdf["standalone_edge_bps"], width=0.4, label="standalone C edge", color="darkorange")
    ax.axhline(0.5, color="red", linestyle=":", linewidth=1, label="materiality (0.5)")
    ax.axhline(0.0, color="black", linewidth=1)
    ax.set_xticks(x, pdf["fixture"], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("edge (bps)")
    ax.set_title("EXP-014 Plot 3 -- incremental vs standalone edge by fixture")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "effect_summary.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run the EXP-014 incremental golden-fixture correctness checks and write outputs."""
    configure_logging()
    ensure_output_dirs()

    token_status = find_predeclaration_token()
    if not token_status["confirmed"]:
        write_blocked_metadata(
            token_status,
            f"Track B predeclaration token {PREDECLARATION_TOKEN!r} (D-incr-legs) not "
            f"found under {GOVERNANCE_DIR}; record the Stage 4 confirmation before replay.",
        )
        LOGGER.warning("EXP-014 BLOCKED: predeclaration token not found under %s", GOVERNANCE_DIR)
        return
    exp013_status = require_exp013_pass()

    fixtures = build_fixtures()
    verdict_rows: list[dict[str, Any]] = []
    leg_rows: list[dict[str, Any]] = []
    for fixture in fixtures:
        v_row, l_rows = evaluate_fixture(fixture)
        verdict_rows.append(v_row)
        leg_rows.extend(l_rows)

    verdicts_ok = all(r["verdict_status"] == "PASS" for r in verdict_rows)
    legs_ok = all(r["status"] == "PASS" for r in leg_rows)
    all_exposed = all(r["exposed"] for r in leg_rows)
    overall_status = "PASS" if (verdicts_ok and legs_ok and all_exposed) else "FAIL"

    write_rows(RESULTS_DIR / "fixture_results.csv", verdict_rows)
    write_rows(RESULTS_DIR / "leg_exposure_matrix.csv", leg_rows)
    mismatches = [
        r for r in leg_rows if r["status"] == "FAIL"
    ] + [
        {"fixture": r["fixture"], "leg": "VERDICT", "exposed": True,
         "expected_state": r["expected_verdict"], "actual_state": r["actual_verdict"],
         "status": r["verdict_status"]}
        for r in verdict_rows if r["verdict_status"] == "FAIL"
    ]
    if mismatches:
        write_rows(RESULTS_DIR / "mismatch_details.csv", mismatches)
    write_json(
        RESULTS_DIR / "run_metadata.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "overall_status": overall_status,
            "measurements_produced": True,
            "verdicts_reproduced": verdicts_ok,
            "leg_states_reproduced": legs_ok,
            "all_legs_exposed_no_short_circuit": all_exposed,
            "n_fixtures": len(fixtures),
            "n_leg_checks": len(leg_rows),
            "fixtures": [f.name for f in fixtures],
            "leg_mapping": {
                "L1_readiness": "incremental denominator effective-n and up/down episodes",
                "L2_significance": "standalone candidate net edge CI lower > 0",
                "L3_reference_control": "incremental-beyond-R edge CI lower > 0",
                "L4_cross_market": "no material sign reversal across the two segments",
                "L5_materiality": "incremental edge point estimate > materiality buffer",
            },
            "alpha": ALPHA,
            "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
            "dependencies": {"EXP-013": exp013_status},
            "predeclaration_gate": token_status,
        },
    )

    plot_verdict_matrix(verdict_rows)
    plot_leg_exposure(leg_rows)
    plot_effect_summary(verdict_rows)

    LOGGER.info("EXP-014 complete: %s", overall_status)
    LOGGER.info("Verdicts reproduced: %s | leg states reproduced: %s | all legs exposed: %s",
                verdicts_ok, legs_ok, all_exposed)
    LOGGER.info("Results: %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
