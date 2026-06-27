# Results: Experiment EXP-014

> **✓ Re-validated under amendment [A1](../../../docs/experiments-docs/checkpoints/2026-06-04-003-ratification-and-incremental-unit/amendments/2026-06-04-A1-incremental-unit-corrections.md) (F04).** EXP-014 was re-run after the contiguous-series block-length fix and reproduced **7/7 verdicts and 35/35 leg states** unchanged; `effective_n` now reflects episode-scale blocks (`276.9` for the coherent `all_pass` fixture, above the 120 floor). EXP-013 re-ran and stayed **PASS** (2026-06-04), so the EXP-013 dependency gate (`run_metadata.json` → `dependencies.EXP-013 = PASS`) is satisfied and this re-validation is **final** — no further re-confirmation is pending.

## Summary

EXP-014 supports the incremental referee logic. All seven deterministic golden fixtures reproduced their expected final verdicts, all 35 expected leg states matched, and every leg was exposed for every fixture without short-circuiting.

## Detailed Findings

### Fixture Verdicts Reproduced

- **Observation**: Every fixture's actual verdict matched the hand-computed expected verdict.
- **Evidence**: `fixture_results.csv` reports 7/7 `verdict_status = PASS`.
- **Interpretation**: The incremental referee's final pass/reject logic matches the predeclared fixture matrix.

### All Gate Legs Were Exposed

- **Observation**: Every fixture records L1 through L5.
- **Evidence**: `leg_exposure_matrix.csv` reports 35/35 `status = PASS`, and `run_metadata.json` records `all_legs_exposed_no_short_circuit = true`.
- **Interpretation**: The referee does not hide later-leg states behind early failures, preserving auditability.

### L3 Reference-Control Mapping Was Exercised

- **Observation**: Fixtures specifically isolate L3 reference-control failures.
- **Evidence**: `l3_reference_control_fail` rejects with L3 false while standalone edge is positive; `redundant_shared_structure` rejects with L2 false, L3 false, and L5 false.
- **Interpretation**: The generalized L3 condition is wired as incremental-beyond-R evidence, not standalone candidate evidence.

## Hypothesis Verdict

**SUPPORTED**

The incremental referee correctness gate passes. The logic is approved for EXP-015 operating-characteristic calibration.

## Limitations

- This is a deterministic logic test; it does not measure FPR, TPR, MDE, or dependence robustness.
- The fixture matrix validates the confirmed D-incr-legs mapping. A changed leg mapping would require new fixture expectations and a new correctness gate.

## Alternative Explanations

- None material. The hypothesis is exact deterministic reproduction, and the saved results have no mismatches.

## Recommended Next Steps

1. Proceed to EXP-015 dependence-grid calibration using the validated incremental referee.
2. Preserve the fixture matrix as a regression target if the incremental unit is later revised.
