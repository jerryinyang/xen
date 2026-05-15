# Governance Review: Experiment EXP-006 — Pre-Execution

**Date**: 2026-05-14
**Review Type**: Pre-Execution
**Artifacts Reviewed**:
- `python/experiments/EXP-006/scope.md`
- `python/experiments/EXP-006/analysis-plan.md`
- `python/experiments/EXP-006/code/run_experiment.py`

---

## Executive Summary

All core constraints pass. The experiment is tightly scoped, uses non-parametric methods, respects the global holdout, and contains no look-ahead bias. One Info note is recorded regarding the diagnostic use of HA-derived returns, which is explicitly authorized by the scope.

---

## Constraint Checks

### Simplicity Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | Single falsifiable hypothesis; no compound questions. |
| analysis-plan.md | PASS | Descriptive ratios + block bootstrap; simplest sufficient approach. |
| code/run_experiment.py | PASS | No unnecessary computation or unused parameters. |

### Academic-Finance Pitfall Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | No normality, stationarity, i.i.d., or constant-volatility assumptions stated. |
| analysis-plan.md | PASS | Block bootstrap chosen specifically to avoid parametric assumptions. |
| code/run_experiment.py | PASS | Bootstrap implementation respects temporal structure. |

### Scope Compliance Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | One question (HA distortion magnitude and regime dependence). Boundaries explicit. |
| analysis-plan.md | PASS | Exactly 2 statistical tests and 4 visualisations; matches complexity budget. |
| code/run_experiment.py | PASS | Implements only the approved plan; no extra analyses or plots. |

### Principles Check

| Artifact | Data-Driven | Non-Parametric | Phantom Price Discipline | Holdout Excluded |
|----------|------------|---------------|--------------------------|-----------------|
| scope.md | PASS | PASS | PASS | PASS |
| analysis-plan.md | PASS | PASS | PASS | PASS |
| code/run_experiment.py | PASS | PASS | PASS | PASS |

**Phantom Price Discipline detail:**
The code computes HA close-to-close returns (`ha_return`) solely to quantify synthetic-price distortion against real returns. No strategy P&L, signal evaluation, or tradable-return metric is derived from HA prices. This diagnostic use is explicitly authorized by the scope: *"This experiment intentionally measures HA synthetic-price distortion. It must not treat HA returns as tradable returns or use them for strategy P&L."*

### Chart-Type Comparison Check

| Artifact | Timestamp Alignment | Bar Count Adjustment | Generator Determinism |
|----------|-------------------|---------------------|---------------------|
| scope.md | PASS | N/A (HA 1:1 with source bars) | N/A |
| analysis-plan.md | PASS | N/A | N/A |
| code/run_experiment.py | PASS | N/A | PASS (uses deterministic `generate_heiken_ashi`) |

### Quality Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | Concrete thresholds (30 % vol, 20 % median abs return). |
| analysis-plan.md | PASS | Interpretation guide pre-defines outcomes. |
| code/run_experiment.py | PASS | Type hints, docstrings, NaN handling, edge-case guards, no magic numbers, PEP 8 style, functions ≤ ~30 lines. |

---

## Findings

### Critical

None.

### Warnings

None.

### Info

1. **Diagnostic HA returns**
   - The hard constraint states: *"For Heiken Ashi experiments: never compute returns from HA prices."*
   - In this experiment, HA returns are computed strictly for diagnostic distortion measurement (compression ratios vs real returns). No strategy P&L or signal quality metric uses HA prices. The scope explicitly authorizes this diagnostic use. If future experiments repurpose this code for strategy evaluation, the HA-return paths must be removed or gated.

---

## Verdict

```text
VERDICT: APPROVE
```
