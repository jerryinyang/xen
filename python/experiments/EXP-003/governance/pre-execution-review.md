# Governance Review: Experiment EXP-003 — Pre-Execution

**Date:** 2026-05-14
**Review Type:** Pre-Execution
**Artifacts Reviewed:** scope.md, analysis-plan.md, code/run_experiment.py

## Executive Summary

All critical constraints pass. Code implements the approved analysis plan with correct holdout exclusion, synthetic price discipline, and timestamp alignment. Minor Info notes on perturbation seed documentation and train/test split convention.

## Constraint Checks

### Simplicity Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | Single falsifiable hypothesis with concrete thresholds. |
| analysis-plan.md | PASS | Each step justifies method choice and simpler alternative. Bootstrap CI for small-n paired differences is the simplest sufficient approach. |
| code/run_experiment.py | PASS | No unnecessary computation. LZ complexity capped at 200K for performance. Perturbation is a direct bar-level operation with immediate OHLC repair. |

### Academic-Finance Pitfall Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | Explicitly non-parametric. No normality, stationarity, i.i.d., or constant-volatility assumptions. |
| analysis-plan.md | PASS | Bootstrap/permutation summaries with small-n. No parametric inference. |
| code/run_experiment.py | PASS | Bootstrap CIs for mean paired differences. No parametric distribution assumptions. |

### Scope Compliance Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | Single question, 4 chart types, 4 instruments, 4 noise levels, concrete success/failure thresholds, complexity budget stated. |
| analysis-plan.md | PASS | Exactly 3 analysis steps matching the 3-test budget. 5 purposeful plots. No scope creep. |
| code/run_experiment.py | PASS | Implements all 3 steps and all 5 plots. No bonus analyses. 0 new modules (under budget of 1). |

### Principles Check

| Artifact | Data-Driven | Non-Parametric | Phantom Price Discipline | Holdout Excluded |
|----------|------------|---------------|--------------------------|-----------------|
| scope.md | PASS | PASS | PASS | PASS |
| analysis-plan.md | PASS | PASS | PASS | PASS |
| code/run_experiment.py | PASS | PASS | PASS | PASS |

**Synthetic price discipline detail:**
- Heiken Ashi returns use `RealClose`, never `HAClose`.
- Line Break and Renko real-close returns are aligned via `SourceCloseTime` join to time-bar closes.
- Direction stability uses native chart-type directions (appropriate for signal-stability characterisation, not strategy P&L).
- No strategy P&L is computed anywhere in the script.

### Chart-Type Comparison Check

| Artifact | Timestamp Alignment | Bar Count Adjustment | Generator Determinism |
|----------|-------------------|---------------------|---------------------|
| code/run_experiment.py | PASS | PASS | PASS |

**Timestamp alignment detail:**
- Time bars use `CloseTime`; Line Break and Renko use `SourceCloseTime`.
- Real-close joins for event chart types align by timestamp, never by bar index.
- No bar-count normalisation is needed because each metric is computed within-chart-type (perturbed vs baseline), not across chart types.

### Quality Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| code/run_experiment.py | PASS | Type hints on all public functions. Docstrings present. NaN handling explicit (empty-input guards, division-by-zero protection). Polars/Parquet loading follows project pattern. Functions separated into pure analysis, plotting, and orchestration. |

## Findings

### Critical

None.

### Warnings

None.

### Info

1. **Perturbation seed derivation** (`code/run_experiment.py:188`)
   - The scope states "seed derived from instrument and timestamp."
   - The implementation uses an instrument-level seed (`hash(f"{instrument}_EXP003_noise")`) with vectorized RNG selection and magnitude sampling.
   - This is deterministic and reproducible for a given instrument and dataset. It does not incorporate per-bar timestamps into the seed.
   - **Rationale accepted:** Vectorized per-bar timestamp seeding would be significantly slower with no material benefit to reproducibility. The selection is still deterministic and documented.

2. **Train/test split not used** (`code/run_experiment.py:728`)
   - The scope document mentions the nested 70/30 train/test split within the analysis set.
   - The analysis plan and code use the full analysis set for baseline/perturbed comparison. No predictive model or out-of-sample testing is performed (this is a characterisation experiment).
   - **Rationale accepted:** Train/test split is not functionally required for descriptive robustness metrics. The global holdout (final 30%) is correctly excluded.

3. **LZ complexity truncation** (`code/run_experiment.py:361`)
   - Lempel-Ziv complexity is capped at 200K sequence length to keep computation bounded.
   - For very long datasets, the sequence is truncated at 200K rather than sampled, preserving prefix temporal structure.
   - **Rationale accepted:** Truncation is deterministic and preserves early-sequence structure. Drift is still comparable because the same truncation applies to both baseline and perturbed.

## Verdict

```
VERDICT: APPROVE
```
