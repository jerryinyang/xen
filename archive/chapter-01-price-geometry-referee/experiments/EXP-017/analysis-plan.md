# Analysis Plan: Experiment EXP-017

## Objective

Verify that the revised incremental referee exactly reproduces predeclared golden-fixture verdicts with retained legs L1, L3, L4', and L5, omits L2, and exposes all retained legs before EXP-018 calibration.

## Methodology

### Step 1: Dependency and Fixture Manifest Check

- **Method**: Deterministic dependency, estimator-touch, and fixture-manifest check.
- **Why this method**: EXP-017 is a correctness gate. It is valid only if EXP-013 remains the approved substrate or is re-run when shared estimator/CI code was touched, and if all expected fixture outcomes were predeclared before replay.
- **Simpler alternative considered**: Run fixture code and inspect final verdicts only. That would not verify dependency safety, predeclaration, or leg-level coverage.
- **Assumptions**: Fixture files contain complete expected outputs for the scoped matrix (`all_pass_revised`, `l1_readiness_fail`, `l2_absent_former_standalone_fail`, `l3_reference_control_fail`, `l4_material_sign_reversal_fail`, `l5_strict_materiality_fail`, `redundant_shared_structure`) and do not require market-data sampling.
- **Expected output**: Dependency manifest, estimator-touch report, fixture manifest, expected-output matrix, and `run_metadata.json`.

### Step 2: Revised Gate Composition Check

- **Method**: Exact structural check of emitted gate legs and final verdict formula.
- **Why this method**: The active checkpoint's repair is specifically leg-composition revision: L2 removed, L3 retained as incremental-beyond-R, L4' accepted, and L5 made strict.
- **Simpler alternative considered**: Infer leg composition from verdict outcomes. That could miss an emitted but ignored L2 leg or a hidden short-circuit path.
- **Assumptions**: The implementation exposes retained leg states and either omits L2 entirely or records it only as an explicit non-gating absence assertion. L5 strict materiality implies L3 on the marginal series.
- **Expected output**: Revised leg-composition table with L2 absence, retained-leg definitions, and verdict formula confirmation.

### Step 3: Verdict Reproduction

- **Method**: Exact equality comparison between observed revised-referee verdicts and hand-computed expected verdicts.
- **Why this method**: The hypothesis is deterministic logic correctness, not statistical uncertainty.
- **Simpler alternative considered**: Aggregate pass-rate summary only. It is useful as output but insufficient without row-level mismatch details.
- **Assumptions**: Fixture values are seeded-deterministic and expected values are the predeclared, hand-reasoned outcomes of the revised gate mapping on the fixed seed (verified against the fixed-seed block bootstrap, not closed-form analytic values).
- **Expected output**: Fixture verdict result table with match flags and mismatch details if any.

### Step 4: Retained-Leg Exposure Verification

- **Method**: Exact equality comparison for each retained leg state plus a retained-leg exposure matrix confirming all four retained legs are recorded for every fixture.
- **Why this method**: The checkpoint requires all retained legs to be exposed without short-circuiting.
- **Simpler alternative considered**: Check only the final gate verdict. That could miss broken leg accounting.
- **Assumptions**: Each fixture includes expected states for L1, L3, L4', and L5; expected denominators; marginal-P&L fields; reference-control comparison values; and materiality thresholds.
- **Expected output**: Retained leg-state result table, retained-leg exposure matrix, and L2-absence result table.

## Visualisations

1. Verdict match matrix by fixture - shows exact pass/fail reproduction.
2. Retained-leg exposure heatmap by fixture and leg - shows no short-circuit.
3. Incremental edge and materiality interval plot by fixture - shows how L3/L5 and L4' cases differ under the revised gate.

## Interpretation Guide

- If all verdicts and retained leg states match, all retained legs are exposed, and L2 is absent, EXP-017 supports revised incremental-referee correctness and EXP-018 may proceed.
- If any verdict or retained leg-state mismatch appears, EXP-017 is refuted until the failing logic or fixture expectation is corrected and re-governed.
- If L2 appears as a gating leg, EXP-017 is refuted because the checkpoint repair was not implemented.
- If fixtures are incomplete or EXP-013 dependency status is invalid, EXP-017 is inconclusive or blocked rather than executed.

## Complexity Check

- Statistical tests: 2 / 2
- Visualisations: 3 / 3
- New modules: 0-1 / 1

## Data-View Comparison Considerations

### Cross-View Alignment

- Fixture rows are deterministic and aligned by fixture timestamp or row identifier.
- Do not use market bar index alignment.

### Implementation Safety and Performance

- Keep fixture replay deterministic.
- Record every retained leg state even when an early retained leg fails.
- Preserve the EXP-013 estimator and CI paths unless a required EXP-013 re-run is explicitly triggered.
- Avoid helper-level noisy printing; output concise tables and metadata.

### Real-Price Outcome Discipline

- Fixture returns represent real-price return contributions.
- Synthetic chart prices are out of scope.

### Event Density Differences

- Report fixture counts, retained-leg exposure counts, and L2-absence counts; no event-density normalization is required.

### Regime Stratification

- No regime stratification is scoped for EXP-017.
