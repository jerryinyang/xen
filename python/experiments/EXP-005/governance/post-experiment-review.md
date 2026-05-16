# Governance Review: Experiment EXP-005 — Post-Experiment

**Date**: 2026-05-16
**Review Type**: Post-Experiment
**Artifacts Reviewed**:
- `python/experiments/EXP-005/audit.md`
- `python/experiments/EXP-005/results.md`
- `python/experiments/EXP-005/report.md`
- `python/experiments/INDEX.md` (updated)
- `docs/experiments-docs/INDEX.md` (updated)

## Executive Summary

All governance checks pass. Two warnings from the audit are documentation-level issues correctly addressed in results.md and report.md. Index files updated correctly. Verdict: APPROVE.

## Constraint Checks

### Holdout Exclusion

| Check | Verdict | Notes |
|-------|---------|-------|
| No code path accesses final 30% | PASS | `load_time_bars` slices to 70% after lazy scan, sort, column projection. Verified in audit.md. |
| No holdout data in results | PASS | All results derived from first 70% of analysis set. |
| Holdout mentioned in scope | PASS | Explicitly excluded in scope.md line 17. |

### Synthetic Price Discipline

| Check | Verdict | Notes |
|-------|---------|-------|
| No HA prices used for P&L | PASS | Experiment uses direction labels only, no return computation. |
| No Renko brick prices used for P&L | PASS | Same — direction labels only. |
| Synthetic price rule in scope | PASS | scope.md line 19 explicitly states no strategy P&L. |

### Timestamp Alignment

| Check | Verdict | Notes |
|-------|---------|-------|
| Cross-chart alignment by timestamp | PASS | CloseTime for timebars/HA, SourceCloseTime for LB/Renko. Verified in code lines 94-102. |
| No bar-index alignment | PASS | All joins use timestamp columns; no bar count or index used. |
| Tolerance window pre-declared | PASS | 5m base, 15m sensitivity — both declared in scope and code constants. |

### Scope Compliance

| Check | Verdict | Notes |
|-------|---------|-------|
| Single hypothesis | PASS | One question about cross-chart-type agreement and regime correspondence. |
| No scope creep | PASS | Code implements exactly the 3 analysis steps and 5 plots from the plan. |
| Complexity budget respected | PASS | 3 tests / 3, 5 plots / 5, 0 new modules / 1. |
| Chart types and parameters match scope | PASS | LB level 3, Renko ATR 14, HA from 1-min bars, 1-min time bars baseline. |
| Instruments match scope | PASS | EURUSD, XAUUSD, BTCUSD, USTEC. |

### Phase 1 Characterisation Boundaries

| Check | Verdict | Notes |
|-------|---------|-------|
| No strategy optimisation | PASS | No parameter tuning, no predictive modelling, no strategy returns. |
| No out-of-sample strategy validation | PASS | Purely descriptive/comparative analysis. |
| Parameters are research decisions | PASS | LB level=3, Renko ATR=14 declared as governance parameters, not optimised. |

### Code Conventions

| Check | Verdict | Notes |
|-------|---------|-------|
| Lazy loading with column projection | PASS | `pl.scan_parquet` with `.select()` before `.sort()` and `.slice()`. |
| Concise logging | PASS | `print(..., flush=True)` progress messages only. |
| Plot reuse | PASS | Direction tables collected once and reused for all plots. |
| Import side effects | PASS | Directory creation only in `main()`. |
| Type hints and docstrings | PASS | All public functions documented. |
| NaN handling | PASS | Explicit `float("nan")` guards, `np.nanmean` for averaging. |

### Audit Warnings Addressed

| Warning | Addressed in | Verdict |
|---------|-------------|---------|
| Bootstrap denominator differs from pairwise | results.md (Hypothesis Verdict section), report.md (Finding 2) | PASS — clearly documented |
| Regime labels missing for calibration period | results.md (Limitations section), report.md (Limitations) | PASS — clearly documented |

### Index Updates

| Index | Updated | Verdict | Notes |
|-------|---------|---------|-------|
| `python/experiments/INDEX.md` | PASS | Correct | Status changed from PLANNED to COMPLETED with accurate one-line finding. |
| `docs/experiments-docs/INDEX.md` | PASS | Correct | All five fields populated: hypothesis tests, scope, results, conclusion, agnostic observations. |

## Verdict

```text
VERDICT: APPROVE
```

All governance constraints satisfied. Audit warnings are documentation-level and correctly addressed in the interpretation artifacts. Index files updated with accurate status and findings. The REFUTED verdict is honest and well-supported by the bootstrap evidence.
