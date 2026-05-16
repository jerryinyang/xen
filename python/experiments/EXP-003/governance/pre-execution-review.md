# Governance Review: Experiment EXP-003 — Pre-Execution

**Date:** 2026-05-14
**Review Type:** Pre-Execution
**Artifacts Reviewed:** scope.md, analysis-plan.md, code/run_experiment.py

## Executive Summary

All critical constraints pass. Code implements the approved analysis plan with correct holdout exclusion, synthetic price discipline (HA uses HAClose as distortion diagnostic per scope), and timestamp alignment. Post-adversarial-review fixes applied: standard LZ76 with log2(n) normalization, complete OHLC repair, 5% invalid-bar threshold, HA variance metric correction, and metric renaming.

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
- Heiken Ashi return variance uses `HAClose` (synthetic smoothed price) as a distortion diagnostic, per scope allowance for HA distortion measurement. `HAClose` returns measure stability of HA's smoothing transformation under noise — this is explicitly not a tradable return.
- `RealClose` for HA would be identical to time-bar `Close`, making the HA vs Time variance comparison degenerate. Using `HAClose` gives a meaningful measure of HA's noise filtering.
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

1. **Perturbation seed derivation** (`code/run_experiment.py`)
   - The scope originally stated "seed derived from instrument and timestamp."
   - The implementation uses an instrument-level seed (`hash(f"{instrument}_EXP003_noise")`) with vectorized RNG selection and magnitude sampling.
   - This is deterministic and reproducible for a given instrument and dataset. It does not incorporate per-bar timestamps into the seed.
   - **Updated scope** documents the actual implementation: instrumental-level deterministic seed with vectorized bar selection. The scope now correctly describes what the code does.

2. **Train/test split not used** (`code/run_experiment.py`)
   - The scope document mentions the nested 70/30 train/test split within the analysis set.
   - The analysis plan and code use the full analysis set for baseline/perturbed comparison. No predictive model or out-of-sample testing is performed (this is a characterisation experiment).
   - **Rationale accepted:** Train/test split is not functionally required for descriptive robustness metrics. The global holdout (final 30%) is correctly excluded.

3. **LZ complexity — standard LZ76 implemented** (`code/run_experiment.py`)
   - The previous implementation used shortest-novel-substring counting, which does not match the standard LZ76 definition and overcounted factors.
   - **Fixed:** Replaced with standard LZ76 factorization (longest match in parsed prefix + extension). Normalised by log2(n) to make values comparable across sequences of different lengths (addresses length confound in complexity drift for event-based chart types that change bar count under perturbation).

4. **OHLC repair completeness** (`code/run_experiment.py`)
   - Previous repair only ensured High >= Close and Low <= Close, leaving Open potentially outside [Low, High].
   - **Fixed:** Repair now ensures High >= max(Open, Close) and Low <= min(Open, Close). Validation pass counts remaining violations and flags results as inconclusive if >5% invalid per the scope criterion.

5. **Heiken Ashi variance metric** (`code/run_experiment.py`)
   - Previous code used `RealClose` for HA variance, which is numerically identical to time-bar Close, making the HA vs Time variance comparison degenerate.
   - **Fixed:** HA now uses `HAClose` for return variance, measuring stability of HA's smoothing transformation under noise. This is a synthetic-price distortion diagnostic per scope, not a tradable return.

6. **Direction-sign perturbation scope narrowing**
   - The scope mentioned "close values or direction signs" but only price-level perturbation is implemented. This is documented in the code and updated scope as a scope narrowing.

7. **Metric naming — VarianceDrift renamed to ReturnVarianceDrift**
   - Renamed to avoid confusion with the Variance Ratio (VR) test from academic finance. The metric measures relative drift in return variance, not a VR test statistic.

## Verdict

```
VERDICT: APPROVE
```
