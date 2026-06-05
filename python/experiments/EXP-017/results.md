# Results: Experiment EXP-017

## Summary

EXP-017 supports the revised incremental-referee logic gate. All seven seeded-deterministic fixtures reproduced their expected verdicts, all 28 retained-leg states were emitted and matched expectations, and L2 was absent from every revised gate output. The old standalone-L2 failure case now passes only because L2 is no longer part of the revised formula, which is the intended Phase 003b repair.

## Detailed Findings

### Fixture Verdicts Reproduced Exactly

- **Observation**: 7/7 fixture verdicts matched expected output.
- **Evidence**: `results/fixture_results.csv` has seven `verdict_status = PASS` rows and `results/mismatch_details.csv` is empty.
- **Interpretation**: The revised L1/L3/L4'/strict-L5 gate behaves as predeclared on the deterministic fixture matrix.

### Retained Legs Were Exposed Without Short-Circuit

- **Observation**: 28/28 retained-leg checks passed and every retained leg was emitted for every fixture.
- **Evidence**: `results/leg_exposure_matrix.csv` has four retained legs per fixture and all rows have `exposed = true`, `status = PASS`.
- **Interpretation**: The implementation records L1, L3, L4', and L5 independently, so downstream diagnostics can identify binding retained legs.

### L2 Is Absent From Revised-Gate Output

- **Observation**: 7/7 L2-absence checks passed.
- **Evidence**: `results/l2_absence_check.csv` emits only `L1_readiness`, `L3_reference_control`, `L4_no_material_sign_reversal`, `L5_strict_materiality`, and supporting numeric fields.
- **Interpretation**: The EXP-015 failure mechanism, the standalone-C significance leg, is removed from the revised portfolio-fitness gate.

### Legacy L2 Behavior Was Exercised

- **Observation**: `l2_absent_former_standalone_fail` has `legacy_l2_pass_diagnostic = false`, yet the revised actual verdict is PASS.
- **Evidence**: In `results/fixture_results.csv`, that fixture has `expected_verdict = PASS`, `actual_verdict = PASS`, and `legacy_l2_ci_lower_bps = -3.3855586505512987`.
- **Interpretation**: EXP-017 does not merely omit an unused column; it verifies that a case previously blocked by standalone L2 is accepted when the incremental evidence clears retained legs.

## Hypothesis Verdict

**SUPPORTED**

The revised incremental referee reproduces all predeclared fixture verdicts and retained-leg states, exposes retained legs without short-circuit, and omits L2 from revised-gate output. EXP-017 therefore clears the logic gate required before EXP-018 calibration.

## Limitations

- This is a deterministic logic fixture experiment, not an operating-characteristic calibration.
- Fixture expectations are fixed-seed, hand-reasoned outcomes against the fixed bootstrap draw, not closed-form analytic identities.
- Market behavior, dependence stress, and finite MDE are intentionally left to EXP-018.

## Alternative Explanations

- A fixture-only pass could miss power or false-positive problems under realistic dependence. That is why EXP-018 remains required before freezing the unit.

## Recommended Next Steps

1. Use EXP-017 as the dependency token for EXP-018 revised incremental referee calibration.
2. Keep the fixture suite as a regression target for any future change to `python/src/xen/incremental_referee.py`.
