# Governance Review: Experiment EXP-020 — Post-Experiment

**Date**: 2026-06-08
**Review Type**: Post-Experiment (consolidated, Stage 8)
**Artifacts Reviewed**: `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`, `governance/pre-execution-review.md`

## Executive Summary

EXP-020 completed all pipeline stages successfully. The audit found 0 critical issues and 0 warnings. Results interpretation is honest and bounded. Documentation is complete and both indexes are updated. Phase alignment with the active checkpoint `2026-06-07-004-avwap-signal-exploration` is confirmed. The experiment is APPROVE-ready.

## Constraint Checks

### Core Constraints

| Check | Verdict | Notes |
|-------|---------|-------|
| Simplicity over complexity | PASS | Sequential state machine is the simplest sufficient approach; vectorized alternatives were considered and rejected for causality-audit reasons. |
| No academic-finance pitfalls | PASS | No parametric assumptions, normality, stationarity, or i.i.d. assumptions. Readiness thresholds are deterministic. |
| Strict experiment scoping | PASS | Single hypothesis (substrate readiness). All boundaries, instruments, parameters, and exclusions match scope. Complexity budget: 0/1 tests, 4/4 plots, 1/1 module. |
| OOS holdout rule | PASS | 0 holdout violations across all cells. Each instrument at exactly 70% analysis rows. Lazy scan → sort → slice → collect pattern. |
| Look-ahead bias prevention | PASS | Sequential state machine using only completed bars; causal SMA via cumsum; regime changes confirmed only after bar close; arm/trigger uses only completed closes. Invariant checks independently validate temporal causality. |
| Real-price discipline | PASS | EXP-020 computes no returns, P&L, or excursions (readiness experiment per scope). |
| Safe performance | PASS | Lazy Polars scans; bounded plotting via summary tables or 400-bar trace window; `tqdm` over instrument/domain loops; no Python row loops over large unbounded frames. |

### Artifact-Specific Checks

| Artifact | Check | Verdict | Notes |
|----------|-------|---------|-------|
| `audit.md` | Thoroughness | PASS | Covers correctness, edge cases, type safety, NaN handling, holdout exclusion, determinism, look-ahead bias, scope compliance. |
| `audit.md` | Evidence | PASS | All findings include specific file paths, function names, and numerical values. |
| `audit.md` | Severity | PASS | Findings classified as 0 critical, 0 warnings, 1 info. |
| `results.md` | Honest reporting | PASS | States what data shows without overclaiming. Explicitly notes readiness ≠ signal quality. |
| `results.md` | Uncertainty acknowledged | PASS | EURUSD/4h direction gap noted; limitations documented. |
| `results.md` | Verdict justified | PASS | SUPPORTED_FULL directly matches scope's Evidence-FOR criteria. |
| `results.md` | Next steps reasonable | PASS | Recommends EXP-021 (reaction) and EXP-022 (lifetime move) as separate scopes. |
| `report.md` | Self-contained | PASS | Can be understood without reading other artifacts. |
| `report.md` | Key visualisations | PASS | Includes event-density heatmap and direction balance plot; not all 4 plots embedded. |
| `report.md` | Limitations | PASS | Readiness ≠ signal quality; determinism within one environment; EURUSD/4h marginal. |
| `report.md` | Artifacts linked | PASS | All artifacts referenced by relative path. |
| `python/experiments/INDEX.md` | Entry correct | PASS | Row updated: SUPPORTED_FULL with accurate one-line finding. |
| `docs/experiments-docs/INDEX.md` | Section correct | PASS | Full five-field schema appended with all required sections. |

### Phase Alignment

| Check | Verdict | Notes |
|-------|---------|-------|
| Active checkpoint | PASS | `2026-06-07-004-avwap-signal-exploration` is ACTIVE. |
| EXP-020 role in checkpoint | PASS | Design.md §5 lists EXP-020 as the first experiment ("substrate readiness"), which aligns with this completed result. |
| Phase outcome criteria | PASS | Per §8, EXP-020 achieves criteria for PROCEED_TO_SCREEN's precondition: substrate readiness is SUPPORTED_FULL. Follow-up EXP-021/022 are required before EXP-023 screening. |

### Verdict Framework

| Check | Verdict | Notes |
|-------|---------|-------|
| No critical issues | PASS | 0 critical findings across all reviews. |
| No holdout contamination | PASS | 0 holdout violations. |
| No look-ahead bias | PASS | Sequential state machine; causal SMA; independent invariant validation. |
| No synthetic price violation | PASS | No returns computed. |
| No unsafe optimization | PASS | State machine is explicit and streaming-safe; no vectorized shortcuts that breach causality. |
| No scope creep | PASS | Exactly one question answered. |
| Budget respected | PASS | 0/1 tests, 4/4 plots, 1/1 modules. |

## Residual Notes

1. The moderate EURUSD/4h direction imbalance (0.557 bull fraction) is documented in audit and results as an info-level note. Both directions remain reportable. This is a scoping consideration for EXP-021, not a governance issue.
2. The pre-execution review's residual note about `load_instruments()` potentially consuming files beyond the four scoped instruments is not triggered — results confirm exactly BTCUSD, EURUSD, USTEC, XAUUSD were processed.

## Verdict

```text
VERDICT: APPROVE
```
