# Audit Report: Experiment EXP-017

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 0

EXP-017 is a deterministic fixture gate for the Phase 003b revised incremental referee. The result artifacts support interpretation: all scoped fixture verdicts reproduced, all retained leg states were exposed and matched, L2 was absent from revised-gate output, and no market data was read.

## Code Review

| File | Check | Verdict | Notes |
| --- | --- | --- | --- |
| `python/experiments/EXP-017/code/run_experiment.py` | Scope compliance | PASS | Implements dependency/design checks, fixture replay, verdict equality, retained-leg exposure, L2 absence, and plots only; see `dependency_manifest()` at lines 128-176 and `main()` at lines 493-582. |
| `python/experiments/EXP-017/code/run_experiment.py` | Holdout exclusion | PASS | Uses in-memory fixtures only. Dependency checks read JSON/design metadata, not market Parquet. |
| `python/experiments/EXP-017/code/run_experiment.py` | Revised gate wiring | PASS | `evaluate_fixture()` calls `revised_incremental_gate_row()` and verifies emitted leg keys contain no `L2` at lines 367-429. |
| `python/src/xen/incremental_referee.py` | Revised leg formula | PASS | `revised_incremental_gate_row()` removes L2 and gates on L1/L3/L4'/strict-L5 at lines 535-574. |
| `python/experiments/EXP-017/code/run_experiment.py` | Organization/import side effects | PASS | Output directories are created only inside orchestration (`ensure_output_dirs()`, lines 106-109); module import does not write files. |
| `python/experiments/EXP-017/code/run_experiment.py` | Memory/performance | PASS | Small fixture tables only; plot conversion to pandas is bounded to seven fixtures and 28 leg rows. |
| `python/experiments/EXP-017/code/run_experiment.py` | Determinism | PASS | Fixed fixture definitions and fixed bootstrap seed; no random process is unseeded. |

## Numerical Validation

### Spot Checks

- `fixture_results.csv`: 7 rows, all `verdict_status = PASS`.
- `leg_exposure_matrix.csv`: 28 rows = 7 fixtures x 4 retained legs, all `status = PASS`, all `exposed = true`.
- `l2_absence_check.csv`: 7 rows, all `status = PASS`, all `l2_absent = true`.
- `mismatch_details.csv`: empty, as expected when no verdict, retained-leg, or L2-absence mismatches exist.
- `run_metadata.json`: `overall_status = PASS`, `verdicts_reproduced = true`, `retained_leg_states_reproduced = true`, `all_retained_legs_exposed_no_short_circuit = true`, `l2_absent_from_revised_gate_output = true`.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
| --- | --- | --- | --- |
| Fixture count | 7 | 7 | YES |
| Retained-leg checks | 28 | 28 | YES |
| L2-absence checks | 7 | 7 | YES |
| Denominator count | positive finite count | 12,000 in all fixture rows | YES |
| Effective N | positive finite value | 276.923 to 3,600.0 | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
| --- | --- | --- | --- |
| Legacy L2 diagnostic | 7/7 checks PASS | YES | The former standalone-L2 failure fixture has `legacy_l2_pass_diagnostic = false` and still revised-gate PASS, proving the L2-removal behavior is exercised. |
| Strict materiality fixture | `l5_strict_materiality_fail` verdict REJECT | YES | Confirms strict `ci_lower_bps > materiality` is enforced, not point-estimate materiality. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
| --- | --- | --- | --- |
| Deterministic fixture replay | Fixture expectations were predeclared and complete | YES | `fixture_manifest.csv` contains the seven scoped fixtures and expected retained-leg states. |
| Revised gate formula | L2 is absent and retained legs are exposed without short-circuit | YES | `l2_absence_check.csv` all PASS; `leg_exposure_matrix.csv` all retained legs exposed. |
| Holdout discipline | No final 30 percent global holdout access | YES | No market Parquet path is loaded by this experiment. |

## Results Plausibility

The observed outcomes match the active checkpoint's Phase 003b repair: fixtures that should fail retained legs reject, the fixture designed to fail only legacy standalone L2 passes under the revised gate, and every emitted revised-gate leg belongs to the retained L1/L3/L4'/L5 set.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 2 checks / 2 budgeted, 3 plots / 3 budgeted, 0 new modules / 1 budgeted
- Holdout exclusion verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

None.

## Re-Audit Requirements

None. The EXP-017 artifacts are suitable for interpretation and downstream EXP-018 dependency use.
