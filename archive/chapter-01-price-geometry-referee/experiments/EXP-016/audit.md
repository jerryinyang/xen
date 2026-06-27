# Audit Report: Experiment EXP-016

## Summary

- **Verdict**: PASS (blocked-state audit)
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

EXP-016 did not produce integration measurements. That is the correct governed outcome for the current rerun: EXP-015 ended `REFUTED` rather than `COMPLETE`, and the required dogfood reference book is not defined. The blocker output is valid and should be interpreted as `BLOCKED`, not as suite-composition evidence.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Dependency gate | PASS | `dependency_manifest()` requires EXP-009 COMPLETE, EXP-012 COMPLETE, EXP-015 COMPLETE, required result tables, and the dogfood reference book at lines 139-210. |
| `code/run_experiment.py` | Reference-book discipline | PASS | Missing `inputs/dogfood_reference_book.csv` is recorded as a blocker at lines 177-193; the script does not invent R. |
| `code/run_experiment.py` | Blocked output | PASS | `write_blocked_metadata()` writes `dependency_manifest.csv`, `blocker_report.csv`, and BLOCKED metadata at lines 213-227. |
| `code/run_experiment.py` | No measurement on blockers | PASS | `main()` returns immediately when blockers exist at lines 821-825. |
| `code/run_experiment.py` | Future executable path | PASS | If unblocked later, `align_reference_positions()` joins by `CloseTime` and raises on incomplete alignment; no bar-index matching is used. |

## Numerical Validation

### Spot Checks

- `run_metadata.json`: `overall_status = BLOCKED`, `measurements_produced = false`.
- `blocker_report.csv`: exactly two blockers are present:
  - EXP-015 metadata reports `overall_status='REFUTED'`, required `COMPLETE`.
  - `python/experiments/EXP-016/inputs/dogfood_reference_book.csv` is missing.
- `dependency_manifest.csv` confirms EXP-009 COMPLETE and EXP-012 COMPLETE, and confirms that the upstream result files required for suite assembly are present.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|----------------|--------------|-------|
| Blocker count | `>= 1` when preconditions fail | 2 | YES |
| Measurements produced | false when blocked | false | YES |
| Missing reference book | explicit blocker | present | YES |

## Scope Compliance

- Analysis plan followed: YES for blocker handling
- Deviations: no integration measurement was produced because scoped preconditions were not met
- Complexity budget: no measurements executed
- Holdout exclusion verified: YES; no market data was loaded in the blocked run

## Issues

### Critical

None.

### Warning

None.

### Info

1. **EXP-016 remains unexecuted**
   - Description: The result set validates only the blocker gate, not assembled-suite composition.

2. **Two independent blockers exist**
   - Description: Even if a dogfood reference book were supplied, EXP-016 would remain blocked until the incremental unit has a COMPLETE upstream calibration or the phase is rescoped.

## Re-Audit Requirements

If EXP-016 is later unblocked and rerun, re-audit the newly produced suite manifest, positive fixture, dogfood path, and composition summaries.
