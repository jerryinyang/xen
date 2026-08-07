#!/usr/bin/env python3
"""SPDR-024 Stage-2 self-check: code-asserted, artifact-backed, count-reconciled.

L-52 / P-23 is the reason this file is shaped the way it is. Four declared checks silently did
not run in a prior build, and the only thing that caught it was manually counting HARD entries.
So:

* the DECLARED HARD list is written out here, by name, copied from design section 13;
* every check reads an EMITTED ARTIFACT. A missing or empty artifact FAILS - it never passes
  vacuously, which is how an empty in-memory panel passed every assertion over itself;
* the expected NUMBER of HARD checks is asserted, and the executed set is reconciled against
  the declared set by name. A declared-but-absent check is a failure, not a silence;
* nothing required lives in a manual post-step. This script is the only place checks run, and
  it writes its own artifacts atomically at the end;
* determinism executes unconditionally whenever the run used `--jobs > 1`, independent of
  whether the run was resumed - a resumed run is exactly the case it exists to catch.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

PYTHON_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PYTHON_ROOT / "src"))

import polars as pl  # noqa: E402

from xen.adaptive_management.contracts import (  # noqa: E402
    SIGNAL_DOMAIN_HOURS,
    build_management_lattice,
    build_native_lattice,
)
from xen.adaptive_management.integrity import run_integrity_checks  # noqa: E402
from xen.adaptive_management.spdr024_analysis import tripwire_collapse  # noqa: E402
from xen.adaptive_management.spdr024_emission import build_episode_table  # noqa: E402

# --------------------------------------------------------------------------- #
# The declared HARD set - design section 13, verbatim by name
# --------------------------------------------------------------------------- #

DECLARED_HARD_DESIGN = (
    "future_shift_tripwire_collapse",
    "train_holdout_fence",
    "causal_t_minus_1_provenance",
    "nautilus_order_fill_position_reconciliation",
    "estimand_reconciliation",
    "deterministic_rerun",
    "hard_check_count_reconciled_by_name",
)

# Implementation-level HARD checks. These are additions, never substitutions: they exist
# because the emission requirements are the point of this experiment, and an emission that
# silently lost one of them would be unreadable in exactly the way SPDR-021/022/023 were.
DECLARED_HARD_IMPLEMENTATION = (
    "golden_traces_match_design",
    "e1_regime_label_present",
    "e2_counterfactual_present_and_non_zero_fill",
    "e4_exit_reason_and_entry_ts_populated",
    "e5_hold_duration_and_cap_flag_present",
    "e6_capital_normalised_estimand_present",
    "arm_lattice_matches_design",
    "no_cost_charged",
    "train_only_band_and_domain",
    "time_derangement_absent",
)

EXPECTED_HARD_COUNT = len(DECLARED_HARD_DESIGN) + len(DECLARED_HARD_IMPLEMENTATION)

E1_COLUMNS = ("regime_state", "regime_episode_id")
E4_COLUMNS = ("exit_reason", "entry_ts")
E5_COLUMNS = ("hold_bars_realised", "hold_cap_bars", "hold_cap_binds")
E6_COLUMNS = ("capital_normalised_return_bps",)
PROHIBITED_CLAIMS = ("fully-net", "cost-complete", "tradable", "deployable")
#: E2 shape guards. A fill value would show up as a mostly-zero column, so the check is on the
#: population, never on the existence of one non-zero row.
MIN_COUNTERFACTUAL_ROWS = 30
MAX_COUNTERFACTUAL_ZERO_SHARE = 0.10


#: Fields that differ between two identical runs by construction: a wall-clock stamp and the
#: worker count, which `config.json` already excludes from the run's research identity. They
#: are normalised out by NAME and the normalisation is reported, never silently applied.
NON_RESEARCH_FIELDS = {
    "run_metadata.json": ["generated_utc"],
    "run_environment.json": ["jobs"],
}


def _replay_hashes_canonical(run_dir: Path) -> dict[str, str]:
    """Artifact hashes for an exact-parity comparison, with wall-clock stamps normalised."""
    import hashlib

    from xen.adaptive_management.integrity import replay_hashes

    hashes = dict(replay_hashes(run_dir))
    for relative, fields in NON_RESEARCH_FIELDS.items():
        for path in run_dir.rglob(relative):
            key = path.relative_to(run_dir).as_posix()
            if key not in hashes:
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            for field in fields:
                payload.pop(field, None)
            encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
            hashes[key] = hashlib.sha256(encoded).hexdigest()
    return hashes


class CheckFailure(Exception):
    """A check could not be evaluated. That is a failure, never a skip."""


def _require_artifact(path: Path) -> Path:
    if not path.exists():
        raise CheckFailure(f"required artifact missing: {path}")
    if path.stat().st_size == 0:
        raise CheckFailure(f"required artifact empty: {path}")
    return path


def _require_rows(frame: pl.DataFrame, what: str) -> pl.DataFrame:
    if frame.is_empty():
        raise CheckFailure(f"required table empty: {what}")
    return frame


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(_require_artifact(path).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #


def _check_golden_traces(golden_path: Path) -> dict[str, Any]:
    payload = _read_json(golden_path)
    traces = payload.get("traces") or []
    if len(traces) != 3:
        raise CheckFailure(f"expected 3 golden traces, found {len(traces)}")
    return {
        "pass": bool(payload.get("blocking_pass")),
        "n_traces": len(traces),
        "failed": [item["trace"] for item in traces if not item.get("pass")],
        "artifact": str(golden_path),
    }


def _check_emission_columns(
    episodes: pl.DataFrame,
    columns: tuple[str, ...],
    label: str,
    *,
    may_be_all_null: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Every declared column must exist and carry values.

    `may_be_all_null` names columns whose emptiness is itself a declared measurement - the
    common hold cap is null exactly when the section 7 cap rule returned NOT_APPLICABLE, and
    forcing a value there would be inventing the cap the rule declined to set.
    """
    _require_rows(episodes, "episode table")
    missing = [name for name in columns if name not in episodes.columns]
    # "Present" is not "populated". A column of NaNs is non-null on every row: a prior build
    # called `payoff_scale_ratio` fully populated while it was NaN on all 9,100 rows. Count
    # FINITE values for numerics, non-null for everything else.
    populated = {
        name: _finite_count(episodes, name)
        for name in columns
        if name in episodes.columns
    }
    empty = [
        name
        for name, count in populated.items()
        if count == 0 and name not in may_be_all_null
    ]
    return {
        "pass": not missing and not empty,
        "requirement": label,
        "missing_columns": missing,
        "unexpectedly_empty_columns": empty,
        "declared_nullable": list(may_be_all_null),
        "non_null_rows": populated,
    }


def _finite_count(frame: pl.DataFrame, name: str) -> int:
    """Rows carrying a usable value: finite for numerics, non-null otherwise."""
    column = frame[name]
    if column.dtype.is_numeric():
        return int(
            (column.is_not_null() & column.cast(pl.Float64, strict=False).is_finite())
            .fill_null(False)
            .sum()
        )
    return int(column.is_not_null().sum())


def _check_counterfactual(episodes: pl.DataFrame) -> dict[str, Any]:
    """E2 must emit a real counterfactual for rejected origins, not the old `0.0` fill."""
    _require_rows(episodes, "episode table")
    if "counterfactual_outcome_bps" not in episodes.columns:
        raise CheckFailure("E2 column absent from the episode table")
    rejected = episodes.filter(
        ~pl.col("admitted") & (pl.col("counterfactual_source") == "FIXED_ARM_REALISED_OUTCOME")
    )
    values = rejected["counterfactual_outcome_bps"].drop_nulls()
    non_zero = int((values != 0.0).sum())
    zero_share = float((values == 0.0).sum() / values.len()) if values.len() else None
    finite_share = (
        float(values.is_finite().sum() / values.len()) if values.len() else None
    )
    # The defect this guards against is a FILL VALUE standing in for a measurement, so the
    # test is on the shape of the whole population: a mostly-zero column is a fill even if one
    # row happens to be non-zero. Genuine zero-return trades exist, so a small share is fine.
    return {
        "pass": bool(
            values.len() >= MIN_COUNTERFACTUAL_ROWS
            and zero_share is not None
            and zero_share <= MAX_COUNTERFACTUAL_ZERO_SHARE
            and finite_share == 1.0
        ),
        "rejected_with_counterfactual": int(values.len()),
        "non_zero_counterfactuals": non_zero,
        "zero_fill_share": zero_share,
        "finite_share": finite_share,
        "max_allowed_zero_share": MAX_COUNTERFACTUAL_ZERO_SHARE,
        "min_rows_required": MIN_COUNTERFACTUAL_ROWS,
        "note": "a zero-filled counterfactual would void every selection read",
    }


def _check_arm_lattice(run_dir: Path, config: dict[str, Any]) -> dict[str, Any]:
    native = pl.read_parquet(run_dir / "native_parameter_schedule.parquet", columns=["arm_id"])
    policy = pl.read_parquet(
        run_dir / "policy_schedule.parquet", columns=["arm_id", "device"]
    )
    # Read the refuted devices off the emitted `device` column, never off arm names. The
    # safety-ceiling arm's id contains "HOLD" while its device is NONE: it is measurement
    # apparatus, and conflating it with the refuted hold-length device would reinstate a
    # lever OD-11 removed.
    refuted_present = sorted(
        set(policy["device"].cast(pl.Utf8).to_list())
        & {"TARGET", "STOP", "TRAIL", "HOLD"}
    )
    observed = set(native["arm_id"].to_list()) | set(policy["arm_id"].to_list())
    declared = {arm.native_arm_id for arm in build_native_lattice("SPDR-024")} | {
        arm.policy_id for arm in build_management_lattice("SPDR-024")
    }
    arm_filter = config.get("arm_filter")
    expected = declared if arm_filter is None else {
        name
        for name in declared
        if name in set(arm_filter)
        or name in {"FIXED_NATIVE_BREAKOUT"}
    }
    return {
        "pass": observed == expected and not refuted_present,
        "declared_arms": len(declared),
        "expected_arms": len(expected),
        "observed_arms": len(observed),
        "unexpected": sorted(observed - expected),
        "absent": sorted(expected - observed),
        "reverse_arms_present": sorted(
            name for name in observed if name.endswith("REVERSE") or "_REVERSE" in name
        ),
        "refuted_devices_present": refuted_present,
        "device_note": (
            "devices read from the emitted column; the safety ceiling is device NONE and is "
            "apparatus, not a hold-length arm"
        ),
    }


def _strip_prohibition_lists(payload: Any) -> Any:
    """Drop the disclosure's own `prohibited_claims` list before scanning for claims.

    The block that FORBIDS a word necessarily contains it; scanning it would report the
    prohibition as a violation of itself.
    """
    if isinstance(payload, dict):
        return {
            key: _strip_prohibition_lists(value)
            for key, value in payload.items()
            if key != "prohibited_claims"
        }
    if isinstance(payload, list):
        return [_strip_prohibition_lists(item) for item in payload]
    return payload


def _check_no_cost(run_dir: Path, config: dict[str, Any], episodes: pl.DataFrame) -> dict[str, Any]:
    disclosure = config.get("spread_cost_disclosure") or {}
    summary = _read_json(run_dir / "run_summary.json")
    text = json.dumps(
        _strip_prohibition_lists({"config": config, "summary": summary})
    ).lower()
    claimed = [claim for claim in PROHIBITED_CLAIMS if claim in text]
    carried = (
        "spread_cost_status" in episodes.columns
        and int(episodes["spread_cost_status"].is_not_null().sum()) == episodes.height
    )
    return {
        "pass": bool(
            disclosure.get("spread_cost_status") == "UNAVAILABLE_NOT_CHARGED"
            and disclosure.get("spread_rt_bps") is None
            and not claimed
            and carried
        ),
        "spread_cost_status": disclosure.get("spread_cost_status"),
        "prohibited_claims_found": claimed,
        "cost_scope_carried_into_analysis_artifact": carried,
    }


def _check_fence_attestation(
    run_dir: Path,
    integrity_hard: dict[str, Any],
) -> dict[str, Any]:
    """The fence itself: a pinned, non-STUB attestation whose manifest hash still matches, and
    no emitted bar beyond the TRAIN end. Distinct from the config's declared band - a run can
    say TRAIN in its config and still carry an unpinned attestation, which is the case this
    check exists to catch."""
    attestation = _read_json(run_dir / "fence_attestation.json")
    status = str(attestation.get("status", "")).upper()
    return {
        "pass": bool(integrity_hard.get("fence") and status == "PINNED"),
        "source": "integrity_selfcheck.json:hard_checks.fence (manifest hash + bar marks)",
        "attestation_status": attestation.get("status"),
        "manifest_sha256": attestation.get("manifest_sha256"),
        "train_end_utc": attestation.get("train_end_utc"),
        "stub_rejected": status not in {"", "STUB", "UNPINNED"},
    }


def _check_band_and_domain(run_dir: Path, config: dict[str, Any]) -> dict[str, Any]:
    """The run's declared identity: TRAIN band and a declared signal domain. Distinct from the
    fence attestation above; both are required and neither implies the other."""
    del run_dir
    domain = config.get("signal_domain")
    return {
        "pass": bool(config.get("band") == "TRAIN" and domain in SIGNAL_DOMAIN_HOURS),
        "band": config.get("band"),
        "signal_domain": domain,
        "declared_domains": sorted(SIGNAL_DOMAIN_HOURS),
    }


def _check_derangement_absent(integrity: dict[str, Any]) -> dict[str, Any]:
    controls = (integrity.get("informative") or {}).get("time_derangement") or {}
    return {
        "pass": controls.get("status") == "REMOVED_OD17",
        "status": controls.get("status"),
        "note": "OD-17 removed time derangement; the future-destroy tripwire is NOT removed",
    }


def _check_determinism(run_dir: Path, replay_dir: Path | None) -> dict[str, Any]:
    """Exact artifact parity against an independent replay. Never sampled."""
    environment = _read_json(run_dir / "run_environment.json")
    jobs = int(environment.get("jobs", 1))
    reference_path = run_dir / "determinism_reference.json"
    if replay_dir is None and not reference_path.exists():
        raise CheckFailure(
            "determinism requires an independent replay artifact; it runs unconditionally "
            f"whenever jobs > 1 (this run used jobs={jobs}) and is independent of --resume"
        )
    observed = _replay_hashes_canonical(run_dir)
    expected = (
        _replay_hashes_canonical(Path(replay_dir))
        if replay_dir is not None
        else _read_json(reference_path).get("replay_hashes", {})
    )
    differing = sorted(
        name for name in set(observed) | set(expected) if observed.get(name) != expected.get(name)
    )
    return {
        "pass": bool(expected and not differing),
        "jobs": jobs,
        "artifacts_compared": len(observed),
        "differing_artifacts": differing,
        "replay_source": str(replay_dir) if replay_dir else str(reference_path),
        "normalised_before_hashing": NON_RESEARCH_FIELDS,
        "note": (
            "only wall-clock stamps and the declared worker count are normalised; every "
            "research artifact is compared byte for byte"
        ),
    }


def _check_estimand(run_dir: Path, estimand_path: Path | None) -> dict[str, Any]:
    path = estimand_path or (run_dir / "estimand_validation.json")
    payload = _read_json(path)
    return {
        "pass": bool(payload.get("blocking_pass")),
        "artifact": str(path),
        "checks": payload.get("checks") if isinstance(payload.get("checks"), dict) else None,
    }


def _check_tripwire(
    episodes: pl.DataFrame,
    shifted_run: Path | None,
    domain_hours: int,
) -> dict[str, Any]:
    if shifted_run is None:
        raise CheckFailure(
            "the future-shift tripwire is HARD and requires its own emission "
            "(run_screen.py --future-shift 1); it is never assumed to have passed"
        )
    shifted = _require_rows(build_episode_table(Path(shifted_run)), "shifted episode table")
    return tripwire_collapse(episodes, shifted, domain_hours=domain_hours)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #


def run_selfcheck(
    run_dir: Path,
    *,
    golden_traces: Path,
    shifted_run: Path | None,
    replay_dir: Path | None,
    estimand_validation: Path | None,
    out_dir: Path,
) -> dict[str, Any]:
    run_dir = Path(run_dir)
    config = _read_json(run_dir / "config.json")
    domain_hours = SIGNAL_DOMAIN_HOURS[str(config.get("signal_domain", "H1"))]
    episodes = _require_rows(build_episode_table(run_dir), "episode table")
    integrity = run_integrity_checks(run_dir, out_dir)
    integrity_hard = integrity["hard_checks"]

    executed: dict[str, dict[str, Any]] = {}
    errors: dict[str, str] = {}

    def _run(name: str, function) -> None:
        try:
            executed[name] = function()
        except CheckFailure as failure:
            executed[name] = {"pass": False, "error": str(failure)}
            errors[name] = str(failure)
        except Exception as failure:  # a check that cannot evaluate has FAILED
            executed[name] = {"pass": False, "error": repr(failure)}
            errors[name] = repr(failure)

    _run("future_shift_tripwire_collapse", lambda: _check_tripwire(episodes, shifted_run, domain_hours))
    _run(
        "train_holdout_fence",
        lambda: _check_fence_attestation(run_dir, integrity_hard),
    )
    _run(
        "causal_t_minus_1_provenance",
        lambda: {
            "pass": bool(integrity_hard.get("causality") and integrity_hard.get("provenance")),
            "source": "integrity_selfcheck.json:hard_checks.causality",
        },
    )
    _run(
        "nautilus_order_fill_position_reconciliation",
        lambda: {
            "pass": bool(integrity_hard.get("order_fill_position_reconciliation")),
            "source": "integrity_selfcheck.json:hard_checks.order_fill_position_reconciliation",
        },
    )
    _run("estimand_reconciliation", lambda: _check_estimand(run_dir, estimand_validation))
    _run("deterministic_rerun", lambda: _check_determinism(run_dir, replay_dir))
    _run("golden_traces_match_design", lambda: _check_golden_traces(Path(golden_traces)))
    _run("e1_regime_label_present", lambda: _check_emission_columns(episodes, E1_COLUMNS, "E1"))
    _run("e2_counterfactual_present_and_non_zero_fill", lambda: _check_counterfactual(episodes))
    _run(
        "e4_exit_reason_and_entry_ts_populated",
        lambda: _check_emission_columns(episodes, E4_COLUMNS, "E4"),
    )
    _run(
        "e5_hold_duration_and_cap_flag_present",
        lambda: _check_emission_columns(
            episodes, E5_COLUMNS, "E5", may_be_all_null=("hold_cap_bars",)
        ),
    )
    _run(
        "e6_capital_normalised_estimand_present",
        lambda: _check_emission_columns(episodes, E6_COLUMNS, "E6"),
    )
    _run("arm_lattice_matches_design", lambda: _check_arm_lattice(run_dir, config))
    _run("no_cost_charged", lambda: _check_no_cost(run_dir, config, episodes))
    _run("train_only_band_and_domain", lambda: _check_band_and_domain(run_dir, config))
    _run("time_derangement_absent", lambda: _check_derangement_absent(integrity))

    # P-23: the count is itself a check, and the executed set is reconciled by NAME.
    declared = set(DECLARED_HARD_DESIGN) | set(DECLARED_HARD_IMPLEMENTATION)
    missing = sorted(declared - set(executed) - {"hard_check_count_reconciled_by_name"})
    unexpected = sorted(set(executed) - declared)
    counted = len(executed) + 1  # + this reconciliation check itself
    reconciliation = {
        "pass": bool(not missing and not unexpected and counted == EXPECTED_HARD_COUNT),
        "expected_hard_checks": EXPECTED_HARD_COUNT,
        "executed_hard_checks": counted,
        "declared_design_section_13": list(DECLARED_HARD_DESIGN),
        "declared_implementation": list(DECLARED_HARD_IMPLEMENTATION),
        "declared_but_absent": missing,
        "executed_but_undeclared": unexpected,
        "lesson": "L-52 / P-23: a declared-but-absent check is a failure, not a silence",
    }
    executed["hard_check_count_reconciled_by_name"] = reconciliation

    failed = sorted(name for name, item in executed.items() if not item.get("pass"))
    payload = {
        "experiment_id": "SPDR-024",
        "universe": config.get("universe"),
        "signal_domain": config.get("signal_domain"),
        "run_path": str(run_dir.resolve()),
        "blocking_pass": not failed,
        "hard_check_count": counted,
        "failed_checks": failed,
        "evaluation_errors": errors,
        "hard_checks": executed,
        "inherited_integrity_hard_checks": integrity_hard,
        "inherited_blocking_pass": integrity["blocking_pass"],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "spdr024_selfcheck.json"
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
    temporary.replace(target)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--golden-traces", required=True, type=Path)
    parser.add_argument("--shifted-run", type=Path, default=None)
    parser.add_argument("--replay-run", type=Path, default=None)
    parser.add_argument("--estimand-validation", type=Path, default=None)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    payload = run_selfcheck(
        args.run,
        golden_traces=args.golden_traces,
        shifted_run=args.shifted_run,
        replay_dir=args.replay_run,
        estimand_validation=args.estimand_validation,
        out_dir=args.out,
    )
    print(
        json.dumps(
            {
                "blocking_pass": payload["blocking_pass"],
                "hard_check_count": payload["hard_check_count"],
                "failed_checks": payload["failed_checks"],
            },
            indent=2,
        )
    )
    return 0 if payload["blocking_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
