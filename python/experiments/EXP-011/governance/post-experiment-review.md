# Governance Review: Experiment EXP-011 - Post-Experiment

**Date**: 2026-06-04
**Review Type**: Post-Experiment (consolidated; Stage 8)
**Checkpoint**: `2026-06-03-002-referee-refinement-and-stringency` (ACTIVE)
**Artifacts Reviewed**: `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`, result tables and plots under `results/` and `plots/`

VERDICT: APPROVE

## Executive Summary

EXP-011 completed the Phase 002 synthesis deliverable after the dependency hard-gate and data-derived adoption-caveat corrections. The audit passes with no critical or warning issues, the interpretation stays within the predeclared exploratory question, the report records recommendation rather than adoption, all scoped dependencies are complete, and both indexes reflect the corrected recommendation context: 5m tau 0.75, 1h tau 0.25, 4h tau 0.5; 1h cross-loss robust; 5m/4h loss-sensitive; only 4h split-sensitive under corrected EXP-010.

## Constraint Checks

| Check | Verdict | Notes |
|-------|---------|-------|
| Scope compliance | PASS | Artifacts answer the single scoped question: recommend per-domain tau under the predeclared loss and report robustness/caveats. No new loss, threshold, referee, or adoption decision was introduced. |
| Holdout exclusion | PASS | EXP-011 reads only result-level artifacts; audit confirmed no raw market-data or holdout path is loaded. |
| Dependency governance | PASS | `gate_dependencies()` hard-gates EXP-003/005/006/007/008/009/010 to COMPLETE; `run_metadata.json` records all complete and `scoped_overlays_complete = true`. |
| Predeclaration discipline | PASS | `results.md` and `report.md` treat the Loss A/B/C read as mechanical and do not reweight terms after seeing outcomes. |
| D-posture | PASS | The report and indexes state recommendation only; Phase 003 fresh-draw ratification is required before adoption. |
| Audit quality | PASS | `audit.md` independently recomputes Loss A/B/C selections, validates output dimensions/ranges, checks overlay consistency, and records no critical or warning issues. |
| Results interpretation | PASS | `results.md` separates factual values, interpretation, limitations, and next steps; it uses "recommendation delivered" rather than inventing a pass/fail hypothesis. |
| Final report | PASS | `report.md` includes question, method, key quantitative findings, caveats, plots, conclusion, and artifact links. |
| Index updates | PASS | `python/experiments/INDEX.md` has the corrected EXP-011 row; `docs/experiments-docs/INDEX.md` has the detailed five-field section and updated active checkpoint summary. |
| Phase alignment | PASS | Findings match active checkpoint section 8/9: EXP-011 yields a recommended operating point per domain plus conditional adoption rule; it does not close Phase 003 decisions. |

## Findings

### Critical

None.

### Warnings

None.

### Info

1. The recommendation is Goodhart-sensitive by design; adoption remains deferred to Phase 003 fresh synthetic draws.
2. 5m carries a non-trivial sub-material trade-off at tau 0.75 (`sub_rate = 0.39759036144578314`), below the predeclared cap but important adoption context.
3. Loss C is weakly independent on this zero-FPR substrate, and the report/results disclose that limitation.
4. Corrected EXP-010 makes only 4h split-sensitive; 5m and 1h are split-robust.

## Decision

Post-experiment governance approves EXP-011 as complete. No Phase 002 referee or threshold adoption is approved by this review.
