# Governance Review: Experiment EXP-009 — Pre-Execution

**Date**: 2026-06-03
**Review Type**: Pre-Execution (consolidated, Stage 4)
**Artifacts Reviewed**: `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, `code/strategies.py`

## Executive Summary

Exploratory effect-size distribution of six untuned, fixed-parameter strategies
evaluated on real prices via the frozen referees and located against the EXP-003
pooled domain MDE. Strategy set and parameters are predeclared and frozen;
indicators are causal; holdout untouched. All checks pass. **APPROVE.**

## Constraint Checks

### Simplicity Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| all | PASS | Donchian/MA reused from the harness; only four canonical indicators added in one experiment-local module; `evaluate_referees` reused unchanged. |

### Academic-Finance Pitfall Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| all | PASS | Block-bootstrap effect CIs (frozen estimator); robust median/IQR distribution summary; no normality/stationarity assumptions; effects anchored to the calibrated MDE, not to 0. |

### Scope Compliance Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | Single exploratory question; six strategies with fixed parameters predeclared and frozen; no tuning/selection in scope. |
| code | PASS | Budget honoured: 3 stat operations / 5 plots / 1 module. No pass/fail per-strategy verdict (measurement only), matching design §4. |

### Principles Check

| Artifact | Data-Driven | Non-Parametric | Phantom Price Discipline | Holdout Excluded |
|----------|------------|---------------|--------------------------|-----------------|
| all | PASS | PASS | PASS (real domain `Close` only; no HA/Renko prices; no chart types) | PASS (`load_analysis_data` first-70% slice; no holdout path) |

### Look-Ahead / Causality Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| strategies.py | PASS | Position at bar `t` uses only closes/highs/lows ≤ `t`; each generator returns `[:-1]` to align to `t→t+1` returns (matches harness Donchian/MA). Wilder RSI uses `gain[i-1]`/`loss[i-1]` (info ≤ `t`); EMA/Bollinger/ROC strictly trailing. Warmup → flat; NaN→0 explicit. |
| code | PASS | Block length estimated on train only inside the frozen harness; shared `CloseTime` split via `domain_split_index`. |

### Quality Check (type-specific)

| Artifact | Verdict | Notes |
|----------|---------|-------|
| code | PASS | Sectioned imports→constants→helpers→plotting→orchestration→`main()`; output dirs in `ensure_output_dirs()`; `tqdm` over instruments; bounded plot inputs (≤144 cells); deterministic seeds via `seed_for`. ruff F/E9/E501 clean; compiles. |
| determinism | PASS | Indicators are pure deterministic functions; `evaluate_referees` seeded. |

## Findings

### Critical
None.

### Warnings
None.

### Info
1. The Wilder-RSI and EMA(MACD) computations use explicit sequential recursions.
   These are genuinely sequential algorithms (permitted by code-conventions for
   stateful logic) and are bounded by the per-domain series length; not flagged
   as avoidable row loops.
2. 4h cells may be under-powered (wide effect CIs); reported as such and excluded
   from precision claims in the distribution roll-up (design §9).
3. EXP-008 per-instrument MDE is intentionally NOT a dependency (kept independent
   per design §8); comparison uses the pooled domain MDE only.

## Verdict

```
VERDICT: APPROVE
```

---

## Stage-4 Re-Review Addendum — 2026-06-03 (post adversarial review)

**Trigger.** Adversarial review
`docs/code-reviews/2026-06-03-194448-exp-008-010-adversarial-review.md` raised two EXP-009 findings
(F03, F04), validated in `docs/code-reviews/2026-06-03-exp-008-010-review-validation.md`. Both are
valid and now fixed pre-execution. This addendum supersedes the original APPROVE. Note: the
original review's Look-Ahead/Causality and Quality checks did not catch that the implemented
`classify_location` dropped the plan's CI-aware `below_MDE` rule (F03) or that the dependency gate
under-enforced the scope (F04) — these are the corrections below.

| Finding | Resolution |
|---------|------------|
| F03 (MDE-location label ignores the CI rule) | `classify_location` is now CI-aware: `below_MDE` requires `ci_upper_bps < mde_bps`; point-below-but-CI-crosses cells fall to `near_MDE`. The CI-aware label flows into `effect_distribution_summary.csv` and the plots. |
| F04 (dependency gate under-enforces upstream validity) | `require_dependencies` now requires EXP-004 `overall_status == "PASS"`; `load_mde_map` asserts a finite gate-stack α0 MDE row for every required domain and raises an explicit Evidence-AGAINST dependency failure otherwise. |

**Re-checks.** `py_compile` and `ruff` clean; pure-function check confirms the four-case CI-aware
classification. Scope, budget (3 stat ops / 5 plots / 1 module), holdout discipline, and frozen-harness
reuse are unchanged.

```
RE-REVIEW VERDICT: APPROVE (findings F03/F04 resolved)
```
