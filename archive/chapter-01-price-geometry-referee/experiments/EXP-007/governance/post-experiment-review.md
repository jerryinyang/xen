# EXP-007 - Post-Experiment Governance Review

**Experiment:** EXP-007 - Lenient-L5 Referee Variant
**Stage:** 8 (post-experiment)
**Reviewed artifacts:** `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`
**Checkpoint:** `2026-06-03-002-referee-refinement-and-stringency` (ACTIVE)
**Date:** 2026-06-03

```text
VERDICT: APPROVE
```

## Scope And Phase Alignment

EXP-007 matches the active checkpoint's planned lenient-L5 variant measurement after the pre-results frozen-harness clarification. The result refutes the structural-gain claim while completing the required operating-characteristic, equivalence, and sub-material accounting deliverables.

| Check | Result |
| --- | --- |
| Single question | PASS - all post-execution artifacts answer whether lenient L5 improves beyond the EXP-006 threshold frontier. |
| No scope creep | PASS - no new threshold, loss function, adoption decision, per-instrument analysis, or chart-type signal was added. |
| Holdout discipline | PASS - audit verifies EXP-003/EXP-006 result-level post-processing only; no source market data or holdout path was used. |
| Real-price discipline | PASS - reused EXP-003 effect and CI fields are real-price `Close` outcomes; no synthetic prices are in scope. |
| Phase alignment | PASS - result sharpens the Phase 002 lever characterization and defers adoption to Phase 003. |

## Artifact Review

### Audit (`audit.md`)

| Check | Result |
| --- | --- |
| Thoroughness | PASS - covers dependency gates, predeclaration gate, code correctness, holdout exclusion, structural equivalence, sub-material denominators, and numerical checks. |
| Evidence | PASS - includes code line references, frozen harness line references, and independent CSV aggregation checks. |
| Severity classification | PASS - 0 Critical, 0 Warning, 2 Info notes. |
| Numerical validation | PASS - independently verifies 216,000 draw rows, selected FPR/TPR rates, zero structural mismatches, and sub-material rates. |

### Results Interpretation (`results.md`)

| Check | Result |
| --- | --- |
| Honest reporting | PASS - reports the hypothesis as refuted rather than treating lower strict MDE as a structural win. |
| Uncertainty acknowledged | PASS - reports Wilson precision, grid limitations, shared-draw limitation, and 5m sub-material caveat. |
| Verdict supported | PASS - `REFUTED` follows the predeclared Evidence-AGAINST criterion: lenient equals EXP-006 `tau=0` and drop-L5. |
| No overreach | PASS - explicitly states that no Phase 002 adoption occurs and EXP-011/Phase 003 must handle recommendation/ratification. |

### Final Report (`report.md`)

| Check | Result |
| --- | --- |
| Self-contained | PASS - includes question, hypothesis, method, key findings, conclusion, limitations, and artifact links. |
| Key visualisations | PASS - embeds MDE comparison and sub-material heatmap, the two most relevant visuals for the conclusion. |
| Honest limitations | PASS - notes shared synthetic draw substrate, grid limits, 5m sub-material proximity, and deferred adoption. |
| Artifacts linked | PASS - links scope, plan, code, audit, results, governance, raw results, and plots. |

### Index Updates

| Check | Result |
| --- | --- |
| Short index | PASS - `python/experiments/INDEX.md` includes EXP-007 with status `REFUTED`, date `2026-06-03`, and a concise key finding. |
| Comprehensive index | PASS - `docs/experiments-docs/INDEX.md` includes the required Hypothesis Tests, Scope, Results / Observations, Hypothesis-Specific Conclusion, and Hypothesis-Agnostic Observations fields. |
| Checkpoint status | PASS - active checkpoint row now reflects the EXP-007 refutation as part of the Phase 002 lever characterization. |

## Issues

### Critical

None.

### Warning

None.

### Info

1. The EXP-007 refutation is a valid completed result, not a failed experiment run. It rules out the distinct-mechanism claim and leaves the zero-buffer endpoint for EXP-011 synthesis.

## Conclusion

All post-experiment artifacts satisfy governance constraints. EXP-007 is approved as a completed Phase 002 experiment with H-lenient refuted.
