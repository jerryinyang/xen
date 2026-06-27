# Governance Review: Experiment EXP-027 — Post-Experiment

**Date**: 2026-06-09
**Review Type**: Post-Experiment (consolidated, research-pipeline Stage 8)
**Artifacts Reviewed**: `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`
**Phase**: 2026-06-08-006-avwap-evaluation-correction (ACTIVE)

## Executive Summary

All artifacts are consistent and well-formed. The experiment delivers a validated event-level evaluation method (METHOD_VALID) with controlled FPR and finite MDE in every domain — exactly the binding gate EXP-028 depends on. The audit identifies one non-blocking warning (secondary-horizon edge shift approximation with small practical impact). Index updates are correct and in the standard format.

## Constraint Checks

### Core Constraints

| Constraint | Verdict | Notes |
|------------|---------|-------|
| Simplicity over complexity | PASS | Regime-cluster bootstrap + sign-permutation + Holm is the simplest sufficient reuse of EXP-021/022. No over-engineering. |
| No academic-finance pitfalls | PASS | Non-parametric throughout; no normality/stationarity/i.i.d./constant-vol assumptions. |
| Strict experiment scoping | PASS | Single falsifiable question; budget respected (4 tests, 5 plots, 1 module); no scope creep. |
| Framework principles | PASS | Data-driven, non-parametric, real-price (Close) discipline, timestamp alignment. |
| OOS holdout rule | PASS | First-70% lazy slice + regime-index fence; holdout never loaded. |
| Look-ahead bias prevention | PASS | Placement/matching use bar-time info only; forward returns are outcomes. |
| Real-price/synthetic-price discipline | PASS | Real Close returns; no synthetic chart prices. |
| Safe optimization | PASS | Vectorized control matching equivalence-guarded against EXP-021 reference. |

### Artifact-Specific Checks

| Artifact | Check | Verdict | Notes |
|----------|-------|---------|-------|
| audit.md | Thoroughness | PASS | Covers correctness, edge cases, holdout, look-ahead, real-price, NaN, determinism, numerical validation. |
| audit.md | Evidence specificity | PASS | Every finding includes file paths, line numbers, values. |
| audit.md | Severity classification | PASS | Critical/Warning/Info appropriately assigned. |
| audit.md | Scope compliance | PASS | Code matches plan; all deviations disclosed and accepted pre-execution. |
| results.md | Honest reporting | PASS | States what data shows; uncertainty acknowledged (secondary-horizon issue, thin 4h MDE). |
| results.md | Verdict supported | PASS | METHOD_VALID justified by explicit criteria table against scope targets. |
| results.md | No overreaching | PASS | Limitations honestly listed; synthetic-substrate-only caveat clear. |
| report.md | Self-contained | PASS | Question, method, key findings, conclusion, limitations, next steps all present. |
| report.md | Key visualizations | PASS | FPR plot, recovery/MDE plot, equity companion, precision diagnostic included with captions. |
| report.md | Honest about limitations | PASS | Four limitations explicitly listed and contextualized. |
| INDEX.md | Entry correct | PASS | Row added with METHOD_VALID status and one-line finding. |
| docs/experiments-docs/INDEX.md | Entry correct | PASS | Full five-field section appended after EXP-025. |

## Findings

### Critical

None.

### Warnings

1. **Secondary-horizon edge shift (carried from audit).** The `+g` shift applied to `effect_h1` and `effect_h6` for planted-edge draws is an approximation that could slightly inflate TPR. Documented in audit, results.md, and report.md. Acceptable for METHOD_VALID as the impact is small and FPR is unaffected. May be fixed before EXP-028 for conservatism.

### Info

1. **Synthetic-substrate-only calibration.** The method was validated on placebo and block-permuted nulls + additive planted drift. Transfer to real AVWAP event outcomes is untested until EXP-028. Properly noted as a limitation.
2. **4h MDE grid resolution.** The MDE jump from TPR=0.738 at 16 bps to 0.998 at 32 bps leaves an unresolved gap. A finer grid may be warranted if EXP-028 precision requires it.

## Verdict

```text
VERDICT: APPROVE
```
