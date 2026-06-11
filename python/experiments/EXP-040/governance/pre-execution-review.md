# Pre-Execution Governance Review: EXP-040

**Review date:** 2026-06-10
**Reviewer:** Pipeline (Stage 4)
**Artifacts reviewed:** scope.md, analysis-plan.md, code/run_experiment.py

## Summary

Mechanism science — HYP-001 direct AVWAP line S/R test. Scope, plan, and code are aligned with Phase 010 design (§5/B1, §8.3). All §11 amendment items implemented (Holm over 2 pooled domains, symmetrized immaterial-null, power statement ordering, censoring sensitivity, caveats). All governance constraints pass.

## Check Results

| Constraint | Status | Notes |
|---|---|---|
| Holdout exclusion | PASS | Analysis set only (first 70%). Holdout never loaded. |
| Look-ahead bias | PASS | All computations at or before bar close. Control levels snapshot at approach timestamp. |
| Real-price outcome | PASS | All distances/outcomes on real OHLC. No HA in any metric path. |
| No EXP-025 conflation | PASS | Bounce-trigger machinery absent from episode/outcome path (lint-assertable). |
| Import side effects | PASS | `ensure_output_dirs()` in `main()` only. |
| Sectioning | PASS | Clear sections. |
| Power statement ordering | PASS | Written before any contrast computation (counts-only). |
| Zero-baseline | PASS | Δ in percentage points. Never relative %. |
| Denominators | PASS | Episodes, not bars. Hysteresis as duplicate-source rule. |
| Complexity budget | PASS | 2 binding tests / 2 budget; 4 plots / 4; 2 modules / 2. |
| Phase alignment | PASS | Matches design §5/B1 (mechanism science, no gate consequence). |
| Censoring sensitivity | PASS | Non-binding companion implemented. |
| Caveats carried | PASS | Moving-vs-static kinematic confound + unmatched price-stretch regime disclosed. |
| Determinism | PASS | 4h bootstrap replay drift = 0.0. |

## Verdict

```text
VERDICT: APPROVE
```
