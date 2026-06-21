# Governance Review: Experiment EXP-077 — Post-Experiment

**Date**: 2026-06-20
**Review Type**: Post-Experiment (Stage 8)
**Artifacts Reviewed**: `audit.md`, `results.md`, `report.md`, and index/registry updates
(`python/experiments/INDEX.md`; `docs/experiments-docs/families/cf-capgeo-001/INDEX.md`;
`docs/experiments-docs/INDEX.md`; `docs/signal-registry/` candidate-family, multiplicity-registry,
components, test-read-ledger)
**Governing checkpoint**: `2026-06-20-017-capgeo-qualifier-validation` (G0 PASS; D0 frozen)

## Executive Summary

**APPROVE.** EXP-077 is a faithful, fully-documented per-stratum methodology validation. The audit
(PASS, 0C/1W/3I) carries complete **verdict forensics** run autonomously — a per-stratum re-derivation
with an explicit masking check, a mechanism statement for each FAIL, and a gate-shape check — exactly
the artifacts Stage 8 requires. No verdict-material finding was documented-and-deferred; the two
leg-level FAILs are correctly computed against the frozen D0 gates and were neither retro-edited nor
re-classified. The signal-registry disposition is recorded and the four registry surfaces are updated
consistently; the TEST-read ledger is correctly unchanged (0 counted reads). No Critical or Warning
governance issues.

## Constraint Checks

### Verdict Forensics & Per-Stratum Doctrine (key check)

| Check | Verdict | Notes |
|-------|---------|-------|
| Verdict forensics present | PASS | `audit.md` re-derives every headline from the raw tables (0 mismatches once single_window-non-binding-by-design is applied); confirms `verdict.json` is a pure function of the tables. |
| Per-stratum masking check | PASS | Each leg adjudicated per stratum (FPR per (type,N,read), MDE per N, reliability per X, accounting per scenario, dogfood per cell). Audit affirmatively confirms the collapsed flag is NON-BINDING and masks nothing; the binding-fail set (5 cells) is correctly identified. |
| Mechanism statement | PASS | FPR-U0 = MC noise around a 0.05-calibrated margin (binomial P=0.36–0.43); FPR-B_zero = genuine mild bimodal small/mid-n under-coverage decaying by n≥120; reliability X=2.0 = ill-conditioned slope over compressed predicted P(>2R). Concrete drivers named, not just "missed the bar". |
| Gate-shape check | PASS | Audit distinguishes "no effect" from "gate cannot see the shape": the point-≤-0.05 FPR sub-gate is ill-posed for an estimator calibrated to 0.05 (Wilson-hi is the real test); the D2.4 slope sub-gate is inapplicable at compressed probabilities. Frozen gates not retro-edited; mismatches recorded for the interpreter. |
| Materiality & blocking | PASS | 0 Critical. The single Warning (reliability `shrink=False` vs plan wording) is shown unable to move the leg verdict (shrinkage would worsen, not repair, the X=2.0 slope; cannot flip the passing X). No verdict-material finding down-classified; no fix-and-rerun owed. |
| Code verdict per stratum | PASS | `build_verdict` emits per-stratum leg verdicts; `collapsed_convenience_flag` explicitly captioned NON-BINDING (honors LESSON-001 / EXP-076 C1). |

### Holdout / Look-Ahead / Real-Price

| Check | Verdict | Notes |
|-------|---------|-------|
| Holdout untouched | PASS | Synthetic legs touch no market data; dogfood lazy-slices the first-49% TRAIN region only (`train_cutoff=int(int(total·0.7)·0.7)`, read frac 0.4900 < 0.491, asserted in code and re-verified by audit). TEST stratum + final-30% holdout never sliced. |
| Look-ahead / causality | PASS | WF expanding folds causal; dogfood forward-H return drops trailing H bars, ATR(14) trailing; ordered by `CloseTime`; no bar-index alignment. |
| Real-price discipline | PASS | Dogfood returns on real `Close`/ATR only; no HA/Renko brick prices. Synthetic returns ATR-unit by construction. |
| Determinism | PASS | All 5 determinism flags True; persisted-CSV hashes reconcile with `integrity.json`; anchor diff 0.0. |

### Gate-Threshold Calibration

| Check | Verdict | Notes |
|-------|---------|-------|
| No magic constants | PASS | FPR margin `m=Q95(ci_low_1s\|null)` calibrated on independent TAG_CAL nulls; FPR/MDE/reliability bands are D0-predeclared (D2.2/D2.3/D2.4); accounting cap=2 from the TEST-read ledger rule. |

### Results / Report Honesty

| Check | Verdict | Notes |
|-------|---------|-------|
| Honest reporting | PASS | `results.md` and `report.md` lead with the per-stratum decomposition, label the leg flags faithful-to-D0 but not whole-qualifier failures, quantify uncertainty, and carry the audit caveats. No overreach. |
| Verdict supported | PASS | PARTIALLY SUPPORTED / VALIDATED_WITH_GUARDS is evidence-bound; explicitly FEEDS G-017, does not adjudicate it (terminal G-017 after EXP-078). |
| Next steps as new scopes | PASS | EXP-078 (slated), an FPR decision-rule refinement scope, and the two guards registered (not acted) — all new scopes, no extension of EXP-077. |

### Registry & Ledger Disposition

| Check | Verdict | Notes |
|-------|---------|-------|
| Disposition recorded | PASS | `report.md` Registry Disposition section present; result is registry-relevant. |
| Candidate-family advanced | PASS | `candidate-families/cf-capgeo-001.md` gate-row advanced to VALIDATED_WITH_GUARDS with both guards; family detail index card + status header updated. |
| Multiplicity outcome recorded | PASS | `multiplicity-registry.md` Phase 017 `ASS/VAL-002`/EXP-077 advanced from PENDING to VALIDATED_WITH_GUARDS; item retained, exceptions recorded not deleted. |
| Components updated | PASS | `components/global-techniques.md` carries the EXP-077 validation note for `ASS` and `WF-EXPANDING`. |
| TEST-read ledger | PASS | Correctly **UNCHANGED** — maintenance note added stating 0 counted reads (synthetic + first-49% TRAIN; accounting rule validated as a function, not exercised against any live stratum). |
| Index updates | PASS | `python/experiments/INDEX.md` row; family detail card; master live status + `Family Indexes` row all updated and mutually consistent. |

## Findings

### Critical
None.

### Warnings
None. (The audit's single Warning is an implementation/plan-wording note, shown non-material; it does
not rise to a governance Warning.)

### Info
1. The two recommended guards (defer-to-median at effective-n≤60 on bimodal mean-null strata; D2.4 slope
   inapplicable at compressed predicted-P) are **disclosures to terminal G-017**, to be ratified at the
   EXP-078/G-017 checkpoint — correctly not acted on in Phase 017.
2. EXP-078 (shape discrimination + `k`-sensitivity) remains owed before terminal G-017 `ASS_VALIDATED`.

## Verdict

```
VERDICT: APPROVE
```
