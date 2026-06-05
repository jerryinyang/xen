"""
Experiment EXP-017: Revised Incremental Referee Golden-Fixture Correctness.

Deterministic correctness gate for the Phase 003b revised incremental referee:
L2 is removed, retained legs are L1, L3, L4_prime, and strict L5, and every
retained leg is exposed without short-circuiting.

The fixtures are *seeded-deterministic* (B1/F04): returns are drawn from a fixed
per-fixture seed and the expected retained-leg states are the predeclared,
hand-reasoned outcomes of the revised gate on that fixed draw, verified against the
fixed-seed block bootstrap rather than computed in closed form. The construction is
adapted from the EXP-014 fixture builder (B1/F05); under the strict-L5 form L5 (not
L3) is the operationally binding leg, with L3 exposed as its precondition (B1/F01).

This script uses in-memory return/position fixtures only. It reads no market
Parquet files, so the global holdout is never loaded or inspected.

Manual execution gate: do not run inside the research pipeline.
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

from xen.incremental_referee import (
    EPISODE_LENGTHS,
    RC_MASKS,
    incremental_gate_core,
    revised_incremental_gate_row,
)
from xen.referee_calibration import ci_from_means, write_json

LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants and paths
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-017"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXPERIMENTS_DIR = PROJECT_ROOT / "python" / "experiments"
EXPERIMENT_DIR = EXPERIMENTS_DIR / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"

EXP013_META = EXPERIMENTS_DIR / "EXP-013" / "results" / "run_metadata.json"
EXP014_META = EXPERIMENTS_DIR / "EXP-014" / "results" / "run_metadata.json"
DESIGN_DOC = (
    PROJECT_ROOT
    / "docs"
    / "experiments-docs"
    / "checkpoints"
    / "2026-06-05-003b-incremental-unit-redesign"
    / "design.md"
)

FIXTURE_INSTRUMENT = "EURUSD"
FIXTURE_DOMAIN = "5m"
ALPHA = 0.05
BOOTSTRAP_RESAMPLES = 1000
BOOTSTRAP_SEED = 17
N_EPISODES = 2000
BASE_NOISE_BPS = 2.0

LEG_NAMES: tuple[str, ...] = (
    "L1_readiness",
    "L3_reference_control",
    "L4_no_material_sign_reversal",
    "L5_strict_materiality",
)


@dataclass(frozen=True)
class Fixture:
    """A frozen revised-gate fixture with hand-reasoned expectations."""

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
    expect_legacy_standalone_fail: bool = False
    notes: str = field(default="")


# --------------------------------------------------------------------------- #
# Output helpers
# --------------------------------------------------------------------------- #
def configure_logging() -> None:
    """Configure concise INFO-level logging for manual execution."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def ensure_output_dirs() -> None:
    """Create output directories during orchestration only."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write rows to CSV, preserving an empty artifact if needed."""
    if rows:
        pl.DataFrame(rows).write_csv(path)
    else:
        path.write_text("", encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from ``path``."""
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Dependency and design gate
# --------------------------------------------------------------------------- #
def dependency_manifest() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Check EXP-013/014 dependencies and the active design confirmations."""
    manifest: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []

    for exp_id, path, required_status in (
        ("EXP-013", EXP013_META, "PASS"),
        ("EXP-014", EXP014_META, "PASS"),
    ):
        if not path.exists():
            manifest.append({"dependency": exp_id, "artifact": str(path), "status": "MISSING"})
            blockers.append({"artifact": str(path), "reason": "missing"})
            continue
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

    if not DESIGN_DOC.exists():
        manifest.append({"dependency": "active design", "artifact": str(DESIGN_DOC), "status": "MISSING"})
        blockers.append({"artifact": str(DESIGN_DOC), "reason": "missing"})
    else:
        text = DESIGN_DOC.read_text(encoding="utf-8")
        confirmed = (
            "D-revised-legs" in text
            and "D-l4l5-freeze" in text
            and "CONFIRMED by operator 2026-06-05" in text
        )
        manifest.append(
            {
                "dependency": "active design",
                "artifact": str(DESIGN_DOC),
                "status": "CONFIRMED" if confirmed else "UNCONFIRMED",
            }
        )
        if not confirmed:
            blockers.append(
                {
                    "artifact": str(DESIGN_DOC),
                    "reason": "D-revised-legs/D-l4l5-freeze confirmations not found",
                }
            )
    return manifest, blockers


def write_blocked_metadata(
    manifest_rows: list[dict[str, Any]], blocker_rows: list[dict[str, Any]]
) -> None:
    """Record a BLOCKED run without replaying fixtures."""
    write_rows(RESULTS_DIR / "dependency_manifest.csv", manifest_rows)
    write_rows(RESULTS_DIR / "blocker_report.csv", blocker_rows)
    write_json(
        RESULTS_DIR / "run_metadata.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "overall_status": "BLOCKED",
            "measurements_produced": False,
            "reason": "Required Phase 003b dependencies or confirmations are unavailable.",
            "blockers": blocker_rows,
        },
    )


# --------------------------------------------------------------------------- #
# Fixture construction
# --------------------------------------------------------------------------- #
def build_fixture_arrays(fixture: Fixture) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Construct deterministic ``(returns, R_positions, C_positions)`` arrays."""
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
    """Return the frozen revised golden-fixture registry."""
    return [
        Fixture(
            name="all_pass_revised",
            purpose="Positive material marginal edge; all retained legs pass.",
            seed=1700,
            expected_verdict="PASS",
            expected_legs={
                "L1_readiness": True,
                "L3_reference_control": True,
                "L4_no_material_sign_reversal": True,
                "L5_strict_materiality": True,
            },
            cc_drift_bps=4.0,
            overlap_drift_bps=4.0,
        ),
        Fixture(
            name="l1_readiness_fail",
            purpose="One-directional incremental position fails readiness.",
            seed=1701,
            expected_verdict="REJECT",
            expected_legs={
                "L1_readiness": False,
                "L3_reference_control": True,
                "L4_no_material_sign_reversal": True,
                "L5_strict_materiality": True,
            },
            cc_drift_bps=4.0,
            overlap_drift_bps=4.0,
            one_directional_cc=True,
        ),
        Fixture(
            name="l2_absent_former_standalone_fail",
            purpose="Legacy standalone-C significance fails, but revised gate passes because L2 is absent.",
            seed=1702,
            expected_verdict="PASS",
            expected_legs={
                "L1_readiness": True,
                "L3_reference_control": True,
                "L4_no_material_sign_reversal": True,
                "L5_strict_materiality": True,
            },
            cc_drift_bps=4.0,
            overlap_drift_bps=-12.0,
            expect_legacy_standalone_fail=True,
        ),
        Fixture(
            name="l3_reference_control_fail",
            purpose="Standalone-looking edge via overlap but no significant marginal edge beyond R.",
            seed=1703,
            expected_verdict="REJECT",
            expected_legs={
                "L1_readiness": True,
                "L3_reference_control": False,
                "L4_no_material_sign_reversal": True,
                "L5_strict_materiality": False,
            },
            cc_drift_bps=6.0,
            overlap_drift_bps=8.0,
            cc_noise_bps=150.0,
        ),
        Fixture(
            name="l4_material_sign_reversal_fail",
            purpose="Marginal edge has a material train/test sign reversal.",
            seed=1704,
            expected_verdict="REJECT",
            expected_legs={
                "L1_readiness": True,
                "L3_reference_control": True,
                "L4_no_material_sign_reversal": False,
                "L5_strict_materiality": True,
            },
            cc_drift_bps=6.0,
            overlap_drift_bps=6.0,
            reversal_cc=True,
        ),
        Fixture(
            name="l5_strict_materiality_fail",
            purpose="Marginal CI lower clears zero but not the materiality threshold.",
            seed=1705,
            expected_verdict="REJECT",
            expected_legs={
                "L1_readiness": True,
                "L3_reference_control": True,
                "L4_no_material_sign_reversal": True,
                "L5_strict_materiality": False,
            },
            cc_drift_bps=0.45,
            overlap_drift_bps=4.0,
        ),
        Fixture(
            name="redundant_shared_structure",
            purpose="Shared R/C structure with no marginal edge guards against phantom incremental pass.",
            seed=1706,
            expected_verdict="REJECT",
            expected_legs={
                "L1_readiness": True,
                "L3_reference_control": False,
                "L4_no_material_sign_reversal": True,
                "L5_strict_materiality": False,
            },
            cc_drift_bps=0.0,
            overlap_drift_bps=0.0,
        ),
    ]


def fixture_manifest_rows(fixtures: list[Fixture]) -> list[dict[str, Any]]:
    """Return the predeclared fixture manifest as a table."""
    rows: list[dict[str, Any]] = []
    for fixture in fixtures:
        row = {
            "fixture": fixture.name,
            "purpose": fixture.purpose,
            "expected_verdict": fixture.expected_verdict,
            "cc_drift_bps": fixture.cc_drift_bps,
            "overlap_drift_bps": fixture.overlap_drift_bps,
            "cc_noise_bps": fixture.cc_noise_bps,
            "one_directional_cc": fixture.one_directional_cc,
            "reversal_cc": fixture.reversal_cc,
            "expect_legacy_standalone_fail": fixture.expect_legacy_standalone_fail,
        }
        row.update({f"expected_{leg}": state for leg, state in fixture.expected_legs.items()})
        rows.append(row)
    return rows


# --------------------------------------------------------------------------- #
# Fixture evaluation
# --------------------------------------------------------------------------- #
def evaluate_fixture(
    fixture: Fixture,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    """Evaluate one fixture against the revised gate and L2-absence rule."""
    returns, r_positions, c_positions = build_fixture_arrays(fixture)
    core = incremental_gate_core(
        returns,
        r_positions,
        c_positions,
        instrument=FIXTURE_INSTRUMENT,
        domain=FIXTURE_DOMAIN,
        n_bootstrap=BOOTSTRAP_RESAMPLES,
        seed=BOOTSTRAP_SEED,
        split_index=None,
    )
    verdict = revised_incremental_gate_row(core, alpha=ALPHA)
    legs = json.loads(verdict["leg_results"])
    standalone_ci = ci_from_means(
        core["standalone_mean"], core["standalone_means"], core["standalone_n"], alpha=ALPHA
    )
    legacy_l2_pass = bool(np.isfinite(standalone_ci.lower) and standalone_ci.lower > 0.0)
    legacy_l2_check = (
        "PASS"
        if (not fixture.expect_legacy_standalone_fail or not legacy_l2_pass)
        else "FAIL"
    )
    verdict_row = {
        "fixture": fixture.name,
        "expected_verdict": fixture.expected_verdict,
        "actual_verdict": verdict["verdict"],
        "verdict_status": "PASS" if verdict["verdict"] == fixture.expected_verdict else "FAIL",
        "legacy_l2_pass_diagnostic": legacy_l2_pass,
        "legacy_l2_ci_lower_bps": standalone_ci.lower,
        "legacy_l2_check_status": legacy_l2_check,
        "incremental_edge_bps": verdict["incremental_edge_bps"],
        "incremental_ci_lower_bps": verdict["incremental_ci_lower_bps"],
        "incremental_ci_upper_bps": verdict["incremental_ci_upper_bps"],
        "materiality_bps": core["materiality_bps"],
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
    l2_absence_row = {
        "fixture": fixture.name,
        "l2_absent": not any(str(key).startswith("L2") for key in legs),
        "emitted_legs": ",".join(sorted(legs)),
        "status": "PASS" if not any(str(key).startswith("L2") for key in legs) else "FAIL",
    }
    return verdict_row, leg_rows, l2_absence_row


# --------------------------------------------------------------------------- #
# Plotting
# --------------------------------------------------------------------------- #
def plot_verdict_matrix(verdict_rows: list[dict[str, Any]]) -> None:
    """Plot verdict reproduction status by fixture."""
    pdf = pl.DataFrame(verdict_rows).to_pandas()
    ok = pdf["verdict_status"].eq("PASS").astype(int)
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(range(len(pdf)), ok, color=["seagreen" if value else "firebrick" for value in ok])
    ax.set_ylim(0, 1.2)
    ax.set_xticks(range(len(pdf)), pdf["fixture"], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("verdict reproduced")
    ax.set_title("EXP-017 revised verdict reproduction")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "verdict_matrix.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_leg_exposure(leg_rows: list[dict[str, Any]]) -> None:
    """Plot retained-leg states for every fixture."""
    pdf = pl.DataFrame(leg_rows).to_pandas()
    fixtures = list(dict.fromkeys(pdf["fixture"]))
    grid = np.zeros((len(fixtures), len(LEG_NAMES)))
    for i, fixture in enumerate(fixtures):
        for j, leg in enumerate(LEG_NAMES):
            row = pdf[(pdf["fixture"] == fixture) & (pdf["leg"] == leg)].iloc[0]
            grid[i, j] = 1.0 if row["actual_state"] else 0.0
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.imshow(grid, aspect="auto", cmap="Greens", vmin=0, vmax=1)
    ax.set_xticks(range(len(LEG_NAMES)), [leg.replace("_", "\n") for leg in LEG_NAMES], fontsize=8)
    ax.set_yticks(range(len(fixtures)), fixtures, fontsize=8)
    for i in range(len(fixtures)):
        for j in range(len(LEG_NAMES)):
            ax.text(j, i, "T" if grid[i, j] else "F", ha="center", va="center", fontsize=9)
    ax.set_title("EXP-017 retained revised-leg states")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "leg_exposure.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_effect_summary(verdict_rows: list[dict[str, Any]]) -> None:
    """Plot incremental edge and strict-materiality CI lower by fixture."""
    pdf = pl.DataFrame(verdict_rows).to_pandas()
    x = np.arange(len(pdf))
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - 0.2, pdf["incremental_edge_bps"], width=0.4, label="incremental edge")
    ax.bar(x + 0.2, pdf["incremental_ci_lower_bps"], width=0.4, label="incremental CI lower")
    ax.axhline(0.5, color="red", linestyle=":", linewidth=1, label="materiality")
    ax.axhline(0.0, color="black", linewidth=1)
    ax.set_xticks(x, pdf["fixture"], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("bps")
    ax.set_title("EXP-017 incremental edge versus strict L5 threshold")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "effect_summary.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run EXP-017 fixture replay and write result artifacts."""
    configure_logging()
    ensure_output_dirs()
    manifest_rows, blocker_rows = dependency_manifest()
    if blocker_rows:
        write_blocked_metadata(manifest_rows, blocker_rows)
        LOGGER.warning("EXP-017 BLOCKED: %s", blocker_rows)
        return

    fixtures = build_fixtures()
    verdict_rows: list[dict[str, Any]] = []
    leg_rows: list[dict[str, Any]] = []
    l2_absence_rows: list[dict[str, Any]] = []
    for fixture in fixtures:
        verdict_row, fixture_leg_rows, l2_row = evaluate_fixture(fixture)
        verdict_rows.append(verdict_row)
        leg_rows.extend(fixture_leg_rows)
        l2_absence_rows.append(l2_row)

    verdicts_ok = all(row["verdict_status"] == "PASS" for row in verdict_rows)
    legacy_l2_ok = all(row["legacy_l2_check_status"] == "PASS" for row in verdict_rows)
    legs_ok = all(row["status"] == "PASS" for row in leg_rows)
    all_exposed = all(row["exposed"] for row in leg_rows)
    l2_absent = all(row["status"] == "PASS" for row in l2_absence_rows)
    overall_status = (
        "PASS"
        if verdicts_ok and legacy_l2_ok and legs_ok and all_exposed and l2_absent
        else "FAIL"
    )

    write_rows(RESULTS_DIR / "dependency_manifest.csv", manifest_rows)
    write_rows(RESULTS_DIR / "fixture_manifest.csv", fixture_manifest_rows(fixtures))
    write_rows(RESULTS_DIR / "fixture_results.csv", verdict_rows)
    write_rows(RESULTS_DIR / "leg_exposure_matrix.csv", leg_rows)
    write_rows(RESULTS_DIR / "l2_absence_check.csv", l2_absence_rows)

    mismatches = [
        row for row in leg_rows if row["status"] == "FAIL"
    ] + [
        {
            "fixture": row["fixture"],
            "leg": "VERDICT",
            "exposed": True,
            "expected_state": row["expected_verdict"],
            "actual_state": row["actual_verdict"],
            "status": row["verdict_status"],
        }
        for row in verdict_rows
        if row["verdict_status"] == "FAIL"
    ] + [
        {
            "fixture": row["fixture"],
            "leg": "L2_ABSENCE",
            "exposed": False,
            "expected_state": "ABSENT",
            "actual_state": row["emitted_legs"],
            "status": row["status"],
        }
        for row in l2_absence_rows
        if row["status"] == "FAIL"
    ]
    write_rows(RESULTS_DIR / "mismatch_details.csv", mismatches)

    write_json(
        RESULTS_DIR / "run_metadata.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "overall_status": overall_status,
            "measurements_produced": True,
            "verdicts_reproduced": verdicts_ok,
            "legacy_l2_diagnostic_reproduced": legacy_l2_ok,
            "retained_leg_states_reproduced": legs_ok,
            "all_retained_legs_exposed_no_short_circuit": all_exposed,
            "l2_absent_from_revised_gate_output": l2_absent,
            "n_fixtures": len(fixtures),
            "n_retained_leg_checks": len(leg_rows),
            "fixtures": [fixture.name for fixture in fixtures],
            "leg_mapping": {
                "L1_readiness": "incremental denominator effective-n and up/down episodes",
                "L3_reference_control": "incremental-beyond-R CI lower > 0",
                "L4_no_material_sign_reversal": "no material train/test sign reversal",
                "L5_strict_materiality": "incremental CI lower > materiality",
                "L2": "absent from revised gate output",
            },
            "alpha": ALPHA,
            "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
            "dependencies": {row["dependency"]: row["status"] for row in manifest_rows},
        },
    )

    plot_verdict_matrix(verdict_rows)
    plot_leg_exposure(leg_rows)
    plot_effect_summary(verdict_rows)

    LOGGER.info("EXP-017 complete: %s", overall_status)
    LOGGER.info(
        "Verdicts: %s | retained legs: %s | L2 absent: %s",
        verdicts_ok,
        legs_ok,
        l2_absent,
    )
    LOGGER.info("Results: %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
