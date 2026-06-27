# Experiment Report: EXP-014 - Incremental Referee Golden-Fixture Correctness

## Status: SUPPORTED

**Date**: 2026-06-04 (re-validated under amendment [A1](../../../docs/experiments-docs/checkpoints/2026-06-04-003-ratification-and-incremental-unit/amendments/2026-06-04-A1-incremental-unit-corrections.md), F04; EXP-013 dependency re-confirmed PASS)
**Instruments**: Fixture labels only; no market data read
**Data Views / Feature Categories**: Deterministic in-memory return-space and R/C position fixtures

---

## Question

Does the incremental referee logic behave exactly as specified before operating-characteristic calibration?

## Hypothesis

The incremental referee reproduces predeclared hand-computed verdicts, exposes all legs without short-circuiting, and correctly generalizes L3 to reference control.

## Method Summary

Seven deterministic fixtures were replayed through the incremental referee. Each fixture had an expected final verdict and expected states for L1 through L5.

## Key Findings

### Finding 1: Verdicts Reproduced

`results/fixture_results.csv` reports 7/7 verdict matches. The all-pass fixture passed; the L1-L5 failure fixtures and redundancy fixture rejected as expected.

### Finding 2: All Legs Were Exposed

`results/leg_exposure_matrix.csv` reports 35/35 PASS leg checks, and `run_metadata.json` records `all_legs_exposed_no_short_circuit = true`.

### Finding 3: L3 Reference Control Was Isolated

The `l3_reference_control_fail` fixture rejected with a positive standalone-looking edge but no incremental-beyond-R significance, confirming L3's reference-control role.

## Conclusion

**Hypothesis SUPPORTED.**

The incremental referee logic is correct under the confirmed D-incr-legs mapping and is approved for EXP-015 calibration.

## Limitations

- This is a logic-correctness gate, not an operating-characteristic measurement.
- Any future leg-mapping change requires a new fixture matrix and correctness gate.

## Implications for Future Research

- EXP-015 can attribute calibration failure or success to operating-characteristic behavior, not fixture wiring errors.

## Recommended Next Experiments

1. **EXP-015**: Incremental referee portfolio-fitness calibration under dependence stress.

## Artifacts

| Artifact | Path |
|----------|------|
| Scope | [scope.md](scope.md) |
| Analysis Plan | [analysis-plan.md](analysis-plan.md) |
| Code | [code/](code/) |
| Audit | [audit.md](audit.md) |
| Results | [results.md](results.md) |
| Governance Reviews | [governance/](governance/) |
| Plots | [plots/](plots/) |
