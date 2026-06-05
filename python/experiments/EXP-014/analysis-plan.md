# Analysis Plan: Experiment EXP-014

## Objective

Verify that the incremental referee exactly reproduces predeclared golden-fixture verdicts and exposes all legs, with L3 generalized to reference control, before EXP-015 calibration.

## Methodology

### Step 1: Dependency and Fixture Manifest Check

- **Method**: Deterministic dependency, governance-token, and fixture-manifest check.
- **Why this method**: EXP-014 is a correctness gate. It must confirm EXP-013 passed, the Track B predeclaration token exists, and all fixture expected verdicts and leg states were predeclared before replay.
- **Simpler alternative considered**: Run fixture code and inspect final verdicts only. That would not verify predeclaration or leg-level coverage.
- **Assumptions**: Fixture files contain complete expected outputs for the scoped matrix (`all_pass_incremental`, `l1_readiness_fail`, `l2_significance_fail`, `l3_reference_control_fail`, `l4_cross_market_fail`, `l5_materiality_fail`, `redundant_shared_structure`) and do not require market-data sampling.
- **Expected output**: Fixture manifest, dependency status, `PHASE003-TRACKB-PREDECLARATION-CONFIRMED` status, and `run_metadata.json`.

### Step 2: Verdict Reproduction

- **Method**: Exact equality comparison between observed incremental referee verdicts and hand-computed expected verdicts.
- **Why this method**: The hypothesis is about deterministic logic correctness, not statistical uncertainty.
- **Simpler alternative considered**: Aggregate pass-rate summary only. It is useful as output but insufficient without row-level mismatch details.
- **Assumptions**: Fixture values are deterministic and expected values are hand-computed from the scoped leg mapping.
- **Expected output**: Fixture verdict result table with match flags and mismatch details if any.

### Step 3: Leg Exposure and L3 Reference-Control Verification

- **Method**: Exact equality comparison for each leg state plus a leg-exposure matrix confirming all five legs are recorded for every fixture.
- **Why this method**: The checkpoint requires all legs to be exposed without short-circuiting and specifically requires L3 to generalize to reference control.
- **Simpler alternative considered**: Check only the final gate verdict. That could miss broken leg accounting or hidden short-circuit behavior.
- **Assumptions**: Each fixture includes expected states for L1-L5, expected denominators, marginal-P&L fields, reference-control comparison values, and materiality thresholds.
- **Expected output**: Leg-state result table and leg-exposure matrix.

## Visualisations

1. Verdict match matrix by fixture - shows exact pass/fail reproduction.
2. Leg exposure heatmap by fixture and leg - shows no short-circuit.
3. Fixture effect and control summary plot - shows how L3 reference-control fixtures differ from all-pass and other fail cases.

## Interpretation Guide

- If all verdicts and leg states match and all legs are exposed, EXP-014 supports incremental referee correctness and EXP-015 may proceed.
- If any verdict or leg-state mismatch appears, EXP-014 is refuted until the failing logic or fixture expectation is corrected and re-governed.
- If fixtures are incomplete or EXP-013 did not pass, EXP-014 is inconclusive or blocked rather than executed.

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
- Record all leg states even when an early leg fails.
- Avoid helper-level noisy printing; output concise tables and metadata.

### Real-Price Outcome Discipline

- Fixture returns represent real-price return contributions.
- Synthetic chart prices are out of scope.

### Event Density Differences

- Report fixture counts and leg-exposure counts; no event-density normalization is required.

### Regime Stratification

- No regime stratification is scoped for EXP-014.
