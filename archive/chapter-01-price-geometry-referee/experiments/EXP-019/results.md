# Results: Experiment EXP-019

## Summary

EXP-019 supports integration completeness for the assembled qualification suite. The strict gate stack, EXP-012 ratified-loose referee, and EXP-018 revised incremental unit compose end to end on both scoped paths: the EXP-009 dogfood path exercises rejection in every domain, and the synthetic positive fixture exercises pass wiring in every domain.

## Detailed Findings

### Suite Dependencies and Reference Book Were Available

- **Observation**: All dependencies and inputs required for measurement were present.
- **Evidence**: `results/dependency_manifest.csv` records EXP-009, EXP-012, and EXP-018 metadata as COMPLETE; strict MDE, dogfood effects/verdicts, adoption decisions, fresh MDE summary, EXP-018 domain MDE summary, dogfood reference book, and dogfood reference manifest as FOUND.
- **Interpretation**: EXP-019 measured composition rather than a blocked state.

### Dogfood Negative Path Was Exercised

- **Observation**: The dogfood path rejected in every domain.
- **Evidence**: `results/suite_composition_summary.csv` reports 0 strict passes, 0 loose/fallback passes, and 0 incremental passes for 5m, 1h, and 4h; each domain status is `REJECT_PATH_EXERCISED`.
- **Interpretation**: The assembled suite handles the expected real dogfood negative path without undefined or unexpected positive outputs.

### Synthetic Positive Path Was Exercised

- **Observation**: The positive fixture passed every suite component in every domain.
- **Evidence**: `results/suite_composition_summary.csv` reports one strict pass, one loose/fallback pass, and one incremental pass for each of 5m, 1h, and 4h; each domain status is `PASS_PATH_EXERCISED`.
- **Interpretation**: The suite can route positive standalone and positive incremental evidence through the pass path.

### Positive Fixture Is Nonredundant

- **Observation**: 3/3 positive fixture rows have `nonredundancy_ok = true`.
- **Evidence**: `results/positive_fixture_manifest.csv` records active overlap fraction `0.0` in all domains and signed R-C rho near zero.
- **Interpretation**: The pass path is not a redundant-reference artifact.

### Current Completed Artifacts Supersede a Stale Blocker Report

- **Observation**: `results/blocker_report.csv` still contains a prior missing-reference-book message, but current measurement artifacts show completion.
- **Evidence**: `results/run_metadata.json` has `overall_status = COMPLETE` and records the dogfood reference book path and manifest; `results/dependency_manifest.csv` marks the book FOUND.
- **Interpretation**: The stale blocker file is artifact hygiene debt, not a measurement blocker.

## Hypothesis Verdict

**SUPPORTED**

The exploratory composition anchor demonstrates both reject and pass suite wiring. The dogfood negative path rejects across all domains, and the synthetic positive path passes strict, ratified-loose, and revised incremental components across all domains. EXP-019 therefore completes the Phase 003b suite-composition requirement.

## Limitations

- EXP-019 is an integration anchor, not a Phase 004 real signal exploration result.
- The dogfood path reuses the EXP-009 simple-strategy family and confirmed `donchian_20` reference book; it does not test new candidate families.
- The positive path is synthetic and validates wiring, not market edge.

## Alternative Explanations

- Dogfood rejection is consistent with EXP-009's lower-anchor result and should not be read as new evidence that all future real candidates will reject.
- Positive fixture success proves the pass path can work; it does not estimate real-world discovery rates.

## Recommended Next Steps

1. Record Phase 003b outcome as revised-unit validated and suite composition complete.
2. Open Phase 004 only after the programme-level multiplicity registry precondition is documented.
