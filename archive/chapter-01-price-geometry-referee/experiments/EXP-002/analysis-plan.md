# Analysis Plan: Experiment EXP-002

## Objective

Validate that the two Phase 001 referees reproduce golden-fixture expectations and expose each 5-check gate leg independently before calibration.

## Methodology

### Step 1: Dependency Gate

- **Method**: Read EXP-001 metadata and require `overall_status == "PASS"`.
- **Why this method**: `design.md` declares EXP-002 depends on EXP-001.
- **Simpler alternative considered**: Running fixtures without the dependency would test code but violate phase order.
- **Assumptions**: EXP-001 metadata is a sufficient dependency signal for this pre-calibration correctness check.
- **Expected output**: Dependency status in `run_metadata.json`.

### Step 2: Golden-Fixture Verdict Check

- **Method**: Evaluate both referees on deterministic fixtures with predeclared expected verdicts and required gate-leg states.
- **Why this method**: Golden fixtures are the simplest way to catch inverted signs, missing leg outputs, short-circuiting, and cost/materiality mistakes.
- **Simpler alternative considered**: Unit tests inside the shared module would not create experiment artifacts or dependency traceability.
- **Assumptions**: Fixture margins are intentionally large enough that bootstrap uncertainty does not decide the result.
- **Expected output**: `golden_fixture_results.csv`.

### Step 3: Leg Exposure Check

- **Method**: Parse gate-stack `leg_results` and verify every fixture records L1 through L5.
- **Why this method**: EXP-003 needs per-leg pass rates; a conjunctive short-circuit would make false-negative attribution impossible.
- **Simpler alternative considered**: Inspecting code manually is less reliable than checking emitted artifacts.
- **Assumptions**: Presence and truth values of leg keys are sufficient for this correctness fixture.
- **Expected output**: `leg_exposure_matrix.csv`.

## Visualisations

1. Fixture verdict pass/fail matrix.
2. Gate-leg exposure matrix.

## Interpretation Guide

- If every expected verdict and required leg state matches, referee logic is approved for EXP-003 calibration.
- If any fixture fails, EXP-003 must not run until the failing logic is revised.
- If EXP-001 has not passed, EXP-002 is inconclusive by dependency order.

## Complexity Check

- Statistical tests: 1 / 1
- Visualisations: 2 / 2
- New modules: 0 / 0

## Implementation Safety and Performance

- No raw market data is loaded.
- Fixed deterministic seeds are used for pseudo-random fixture positions.
- The gate-stack implementation must evaluate and record all five legs without short-circuiting.
- Zero-baseline comparisons use absolute bps/trade effects, not percentage improvement.

