# Governance Review: Experiment EXP-047 — Post-Experiment

**Date**: 2026-06-12
**Review Type**: Post-Experiment
**Artifacts Reviewed**: `audit.md`, `results.md`, `report.md`,
`python/experiments/INDEX.md` (EXP-047 row), `docs/experiments-docs/INDEX.md`
(Phase 013 checkpoint row + EXP-047 detailed section), against the bundled
governance constraints and the Phase 013 design/D0.

## Executive Summary

Clean negative delivered with the predeclared machinery intact and an
audit-discovered structural explanation honestly foregrounded. APPROVE.

## Constraint Checks

### Honest Reporting / Verdict Support

| Artifact | Verdict | Notes |
|----------|---------|-------|
| audit.md | PASS | Independent recomputes to full precision (manual pivot, medians, reconciliation diff 0.0); the qualification-collapse finding is quantified grid-wide and correctly classified as Warning (interpretive), not a code defect. The added `audit_anchor_coincidence.csv` is a verified audit artifact, not scope creep — it adds no binding statistic. |
| results.md | PASS | Verdict REFUTED is mechanically forced by 0/51 vs the P6 threshold; the conditional-on-k=1.0 framing follows audit W2 exactly; no goalpost movement (P5/P6 applied as ratified); negative treated as a complete, routable outcome. Finding 3 (leg 2 51/51) is correctly labelled descriptive and necessary-not-sufficient. |
| report.md | PASS | Self-contained, embeds 3 of 4 plots with captions, links all artifacts, limitations honest, follow-ups proposed as new scopes (new-family readiness; optional binding-k variant under a new D0), not extensions. |

### Scope / Multiplicity / Data Discipline

| Check | Verdict | Notes |
|-------|---------|-------|
| Holdout untouched | PASS | `head(train_rows)` slices only; metadata records 0 TEST reads, 0 holdout reads; ledger unchanged. |
| Predeclaration integrity | PASS | All thresholds applied as ratified; the one pre-data interpretive resolution (P1 multi-candidate reading) was disclosed in scope and flagged at the execution gate before the run. |
| No post-result re-parameterisation | PASS | No k change, threshold change, or cell re-selection after data contact; sensitivity flags were predeclared in the revised plan before the run. |
| Complexity budget | PASS | 0 binding tests / 0; 4 plots / 4; 1 new module / 1. |
| Index consistency | PASS | Brief row, checkpoint-status row, and five-field detailed section agree with results.md and audit.md figures. |

### Interpretation Quality

| Check | Verdict | Notes |
|-------|---------|-------|
| No overreach | PASS | "Closes the ratified definition, not anchor placement in general"; MFE explicitly a non-tradable upper bound. |
| Alternative explanations | PASS | Collapse mechanically verified rather than statistically inferred; no competing explanation exists. |
| Lessons recorded | PASS | Coincidence-vs-fallback disclosure lesson and capture-geometry reframing both captured for the retrospective and the Phase 014 design brief. |

## Findings

### Critical

None.

### Warnings

None.

### Info

1. G1b adjudication (ANCHOR_MOVE_FLAT → new-family routing per the operator
   pre-commitment) remains checkpoint desk work; the experiment artifacts
   provide the mechanical input only.
2. The optional binding-k `/ANCHOR` follow-up is correctly framed as a new
   D0 decision for the operator, not a recommendation to re-open this phase.

## Verdict

```
VERDICT: APPROVE
```
