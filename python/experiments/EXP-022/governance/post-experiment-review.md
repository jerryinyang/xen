# EXP-022 — Post-Experiment Governance Review

**Stage:** 8 (post-experiment)
**Date:** 2026-06-08
**Artifacts reviewed:** `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`
**References:** governance-constraints.md, checkpoint `2026-06-07-004-avwap-signal-exploration/design.md`

```text
VERDICT: APPROVE
```

## Core Constraint Checks

### 1. Simplicity Over Complexity
The analysis uses the simplest sufficient approach: regime-cluster bootstrap for CIs, stratified paired permutation for p-values, equal-weight instrument averaging. Each method is justified in the analysis plan with simpler alternatives considered. No unnecessary computation.

### 2. No Academic-Finance Pitfalls
All methods are non-parametric (bootstrap, permutation, median-based diagnostics). No normality, stationarity, i.i.d., or constant-volatility assumptions. Method choices are practically motivated.

### 3. Experiment Scoping
Single hypothesis (lifetime method favorable outcome advantage). Boundaries, parameters, and exclusions explicit in scope. Complexity budget respected: 3/3 tests, 5/5 plots, 0/1 modules. No scope creep.

### 4. Framework Principles
- Data-driven: conclusions emerge directly from observed rate differences and CIs.
- Non-parametric: bootstrap CI and permutation test used throughout.
- Real-price discipline: all outcomes use real domain `Close` prices.
- Timestamp alignment: events/regimes aligned by `CloseTime`; cross-view joins validated by both timestamp and price.

### 5. OOS Holdout Rule
Verified in audit: first-70% lazy slice before collection; event/regime index checks hard-fail on holdout fence breach; completion scans bounded by analysis-set end. Holdout untouched.

### 6. Look-Ahead Bias Prevention
Targets frozen at trigger time. Trend-change is nearest later opposite-regime confirmation. Local volatility uses only past returns. Control selection uses no future outcomes.

### 7. Real-Price/Synthetic-Price Discipline
All completions and expectancy use real domain `Close`. No chart-type views or synthetic prices in scope.

### 8. Safe Optimization
Vectorized first-hit preserves temporal ordering. Bootstrap/permutation chunked. No sample-membership, denominator, or causation changes.

## Artifact-Specific Checks

### Audit (`audit.md`)
Thorough: covers correctness, edge cases, holdout, look-ahead, NaN handling, statistical sanity, scope compliance. All findings supported with specific values. Verdict PASS.

### Results Interpretation (`results.md`)
Honest and specific: reports exact effect sizes, CIs, p-values, sample sizes. Limitations acknowledged (single branch, invalid-target exclusion, matched-control design). No overreaching. Verdict SUPPORTED is fully justified by evidence.

### Final Report (`report.md`)
Self-contained, includes key finding tables and plot reference. Limitations stated. All artifacts linked by relative path.

### Index Updates
- `python/experiments/INDEX.md`: updated with concise row.
- `docs/experiments-docs/INDEX.md`: updated with full five-field entry.

## Checkpoint Alignment

EXP-022 is the planned **AVWAP Original Lifetime Move Study** in the Phase 004 experiment chain (design §5), gated on EXP-020 SUPPORTED_FULL. The result (SUPPORTED on all 3 domains) aligns with the PROCEED_TO_SCREEN pathway (design §8). A favorable lifetime result is measured against a look-ahead-safe benchmark (matched same-regime control), satisfying the checkpoint's benchmark requirement (§7).

## Decision

All governance checks pass. No Critical or Warning issues. Implementation, results, documentation, and indexes are complete and correct.
**APPROVE** — experiment complete.
