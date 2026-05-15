# Governance Review: Experiment EXP-004 — Pre-Execution

**Date:** 2026-05-14
**Review Type:** Pre-Execution
**Artifacts Reviewed:**
- `python/experiments/EXP-004/scope.md`
- `python/experiments/EXP-004/analysis-plan.md`
- `python/experiments/EXP-004/code/run_experiment.py`

## Executive Summary

All artifacts comply with Xen governance constraints. The experiment scope is focused, the analysis plan is methodologically sound and non-parametric, and the code correctly excludes the global holdout, aligns by timestamp, and respects synthetic-price discipline. Approved for manual execution.

---

## Constraint Checks

### Simplicity Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | Single falsifiable hypothesis; concrete thresholds for success/failure/inconclusive |
| analysis-plan.md | PASS | ATR-scaled swing detector is the simplest viable reversal reference; direction changes are the simplest cross-chart-type signal |
| code/run_experiment.py | PASS | No unnecessary computation; event-matching logic is minimal and focused |

### Academic-Finance Pitfall Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | No normality, stationarity, i.i.d., or constant-volatility assumptions |
| analysis-plan.md | PASS | Bootstrap percentile intervals used instead of parametric tests; no distribution assumptions |
| code/run_experiment.py | PASS | Bootstrap resampling at instrument level preserves paired structure without parametric assumptions |

### Scope Compliance Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | Chart types, parameters, instruments, time range, exclusions, and complexity budget (3/5/1) all explicit |
| analysis-plan.md | PASS | Exactly 3 analysis steps, 5 visualisations, no new modules planned — within budget |
| code/run_experiment.py | PASS | Implements exactly the 3 steps in the plan; 5 plots generated; no new modules created |

### Principles Check

| Artifact | Data-Driven | Non-Parametric | Synthetic Price Discipline | Holdout Excluded |
|----------|-------------|---------------|---------------------------|-----------------|
| scope.md | PASS | PASS | PASS (no P&L; real prices for reference) | PASS (final 30% excluded) |
| analysis-plan.md | PASS | PASS | PASS | PASS |
| code/run_experiment.py | PASS | PASS | PASS (reversal reference uses real Close/High/Low; no strategy returns) | PASS (`slice(0, int(len*0.7))`) |

### Chart-Type Comparison Check

| Artifact | Timestamp Alignment | Bar Count Adjustment | Generator Determinism |
|----------|-------------------|---------------------|---------------------|
| scope.md | PASS (CloseTime / SourceCloseTime specified) | N/A | PASS |
| analysis-plan.md | PASS (explicit timestamp matching within tolerance window) | PASS (false/duplicate rates normalised per time) | PASS |
| code/run_experiment.py | PASS (events matched by `SignalTime >= ReversalTime` within `timedelta64` tolerance) | PASS (`FalsePerDay`, `DuplicatePerDay`) | PASS (generators called with fixed params) |

### Quality Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| code/run_experiment.py | PASS | Type hints on all public functions; docstrings with Parameters/Returns; explicit NaN and empty-DataFrame handling; constants at top; max ~100 char lines; function sizes reasonable |

---

## Findings

### Critical

None.

### Warnings

None.

### Info

1. **ATR method**: `compute_atr` uses a simple rolling mean of True Range rather than Wilder's smoothed ATR. This is acceptable because the scope describes the reference as "rolling ATR-scaled directional movement" without mandating a specific ATR variant, and the simpler method is sufficient for a reversal threshold.

2. **Tolerance window**: The code sets `TOLERANCE_MINUTES = 120`. This is not specified in scope.md or analysis-plan.md, but is a reasonable instrument-agnostic forward window for 1-minute reversal detection and is clearly documented as a constant.

3. **No train/test split within analysis set**: The code uses the full analysis set (first 70% of data) without a nested 70/30 split. This is appropriate because the experiment is pure characterisation (event detection and matching) with no model training, consistent with Phase 1 scope boundaries.

---

## Verdict

```text
VERDICT: APPROVE
```
