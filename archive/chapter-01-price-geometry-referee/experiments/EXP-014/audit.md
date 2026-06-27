# Audit Report: Experiment EXP-014

> **Re-audited 2026-06-04 after the amendment [A1](../../../docs/experiments-docs/checkpoints/2026-06-04-003-ratification-and-incremental-unit/amendments/2026-06-04-A1-incremental-unit-corrections.md) re-run (F04 contiguous block length).** Verdict unchanged: PASS. The deterministic fixtures reproduced 7/7 verdicts and 35/35 leg states; the F04 fix made `effective_n` episode-aware (`276.9` on the `all_pass` fixture, above the 120 floor) without changing any verdict. The EXP-013 dependency gate re-ran PASS, so this re-validation is final.

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 1

EXP-014 can be trusted for interpretation. The deterministic fixture replay reproduced every expected verdict and all 35 expected leg states, and all five legs were exposed for every fixture with no short-circuit.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Predeclaration gate | PASS | `find_predeclaration_token()` checks the Track B token at lines 108-118; `main()` blocks if absent at lines 382-390. |
| `code/run_experiment.py` | Dependency gate | PASS | `require_exp013_pass()` requires EXP-013 PASS at lines 121-128. |
| `code/run_experiment.py` | Fixture replay | PASS | `evaluate_fixture()` evaluates each fixture with the incremental referee and compares expected versus actual verdicts at lines 277-296. |
| `code/run_experiment.py` | Leg exposure | PASS | The evaluator iterates all `LEG_NAMES` and records every leg state at lines 298-312. |
| `code/run_experiment.py` | Output integrity | PASS | `main()` computes `overall_status = PASS` only when verdicts, leg states, and exposure all pass at lines 401-404. |
| `python/src/xen/incremental_referee.py` | Leg mapping | PASS | `incremental_gate_row()` maps L1-L5 to readiness, standalone significance, incremental reference control, cross-market sign consistency, and materiality at lines 412-437. |

## Numerical Validation

### Spot Checks

- `fixture_results.csv`: 7/7 verdicts match expected.
- `leg_exposure_matrix.csv`: 35/35 leg checks PASS.
- `run_metadata.json`: `all_legs_exposed_no_short_circuit = true`, `verdicts_reproduced = true`, and `leg_states_reproduced = true`.
- The `redundant_shared_structure` fixture correctly rejects with L2=false, L3=false, L5=false, guarding the shared-structure false-positive path.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|----------------|--------------|-------|
| Fixture count | 7 | 7 | YES |
| Leg checks | 7 fixtures x 5 legs | 35 | YES |
| Denominator count | positive finite | 12000 all fixtures | YES |
| Actual verdicts | PASS/REJECT | all expected | YES |

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none found
- Complexity budget: 2 checks / 2 budgeted, 3 plots / 3 budgeted, 0 new modules / 1 budgeted
- Holdout exclusion verified: YES; this is an in-memory fixture test and no market Parquet file is read

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Fixture correctness depends on the confirmed orthogonal leg mapping**
   - Description: EXP-014 validates the D-incr-legs mapping confirmed in pre-execution governance; changing that mapping would require a new fixture gate.

## Re-Audit Requirements

None.
