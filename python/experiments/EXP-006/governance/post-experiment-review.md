# EXP-006 - Post-Experiment Governance Review

**Experiment:** EXP-006 - L5 Materiality Threshold Sweep
**Stage:** 8 (post-experiment)
**Reviewed artifacts:** `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`
**Checkpoint:** `2026-06-03-002-referee-refinement-and-stringency` (ACTIVE)
**Date:** 2026-06-03

```text
VERDICT: APPROVE
```

## Scope And Phase Alignment

EXP-006 matches the active checkpoint's planned L5 threshold-sweep lever curve. The completed artifacts keep the experiment as a characterization measurement and do not recommend or adopt a threshold.

| Check | Result |
| --- | --- |
| Single question | PASS - all post-execution artifacts answer the L5 threshold frontier question only. |
| No scope creep | PASS - no lenient-L5 policy decision, per-instrument de-pooling, loss function, chart-type signal, or adoption claim was added. |
| Holdout discipline | PASS - audit verifies result-level post-processing of EXP-003 artifacts only; no source market data or holdout path was used. |
| Real-price discipline | PASS - reused EXP-003 effect and CI fields are real-price `Close` outcomes; no synthetic prices are in scope. |
| Phase alignment | PASS - EXP-006 feeds EXP-007/EXP-011 as a frontier, consistent with Phase 002's characterize-and-recommend posture. |

## Artifact Review

### Audit (`audit.md`)

| Check | Result |
| --- | --- |
| Thoroughness | PASS - covers scope compliance, code correctness, holdout exclusion, safe vectorization, denominators, strict-reference reproduction, and numerical spot checks. |
| Evidence | PASS - includes code line references and independent aggregation checks from result CSVs. |
| Severity classification | PASS - 0 Critical, 0 Warning, 2 Info notes. |
| Numerical validation | PASS - independently verifies row count `1,512,000`, denominators, selected FPR/TPR cells, and strict-reference mismatch count. |

### Results Interpretation (`results.md`)

| Check | Result |
| --- | --- |
| Honest reporting | PASS - describes EXP-006 as exploratory characterization, not policy adoption. |
| Uncertainty acknowledged | PASS - reports Wilson precision and grid-resolution limitations. |
| Verdict supported | PASS - `SUPPORTED` is tied to the Evidence-FOR measurement deliverable and strict-reference reproduction. |
| No overreach | PASS - explicitly defers operating-point recommendation to EXP-011 and fresh-draw adoption to Phase 003. |

### Final Report (`report.md`)

| Check | Result |
| --- | --- |
| Self-contained | PASS - includes question, method, key findings, conclusion, limitations, and artifact links. |
| Key visualisations | PASS - embeds MDE-vs-threshold and TPR-curve plots, the two most relevant visuals for the conclusion. |
| Honest limitations | PASS - notes pooled-domain scope, grid limits, and draw-substrate specificity. |
| Artifacts linked | PASS - links scope, plan, code, audit, results, governance, raw results, and plots. |

### Index Updates

| Check | Result |
| --- | --- |
| Short index | PASS - `python/experiments/INDEX.md` includes EXP-006 with status `SUPPORTED`, date `2026-06-03`, and a concise key finding. |
| Comprehensive index | PASS - `docs/experiments-docs/INDEX.md` includes the required Hypothesis Tests, Scope, Results / Observations, Hypothesis-Specific Conclusion, and Hypothesis-Agnostic Observations fields. |
| Checkpoint status | PASS - active checkpoint row now reflects EXP-006 completion as part of the Phase 002 lever characterization. |

## Issues

### Critical

None.

### Warning

None.

### Info

1. EXP-006's `SUPPORTED` status means the characterization deliverable succeeded. It does not mean a lower L5 threshold is adopted.

## Conclusion

All post-experiment artifacts satisfy governance constraints. EXP-006 is approved as a completed Phase 002 characterization experiment.
