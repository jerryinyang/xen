# Governance Review: Experiment EXP-008 — Pre-Execution

**Date**: 2026-06-03
**Review Type**: Pre-Execution (consolidated, Stage 4)
**Artifacts Reviewed**: `scope.md`, `analysis-plan.md`, `code/run_experiment.py`

## Executive Summary

Per-instrument MDE de-pooling is a holdout-safe, result-level reprocessing of the
frozen EXP-003 artifacts with the H-pool margin frozen before any per-instrument
MDE is read. All constraint checks pass. **APPROVE.**

## Constraint Checks

### Simplicity Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| all | PASS | Pure CSV post-processing; 0 new modules; reuses `wilson_interval`. Simplest sufficient design (mirrors EXP-006). |

### Academic-Finance Pitfall Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| all | PASS | Non-parametric Wilson intervals + grid-defined MDE; no normality/stationarity/iid assumptions; reuses frozen EXP-003 draw verdicts. |

### Scope Compliance Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | Single question (H-pool); margin `max(0.5, 0.20·pooled)` restated and frozen pre-results per design §4 / §2 ⚠. |
| code | PASS | Budget honoured: 3 stat operations / 4 plots / 0 modules. No scope creep. |

### Principles Check

| Artifact | Data-Driven | Non-Parametric | Phantom Price Discipline | Holdout Excluded |
|----------|------------|---------------|--------------------------|-----------------|
| all | PASS | PASS | PASS (no chart prices; effects inherited from real-price EXP-003) | PASS (only EXP-003 artifacts read; no raw Parquet/holdout) |

### Quality Check (type-specific)

| Artifact | Verdict | Notes |
|----------|---------|-------|
| code | PASS | Lazy `scan_csv` projects 6 columns before collect; Polars `group_by` aggregation (no row loops); deterministic (no RNG); output dirs created in `ensure_output_dirs()` from `main()`; concise logging. ruff F/E9/E501 clean; compiles. |
| zero-baseline | PASS | Material margin floored at 0.5 bps; pooled MDE asserted finite before comparison — no zero-baseline ratio. |
| MDE definition | PASS | Per-instrument MDE uses the exact EXP-003 rule (smallest grid edge with TPR≥0.80 at FPR≤α, D-prec precision); `grid_half_step` matches EXP-003. |

## Findings

### Critical
None.

### Warnings
None.

### Info
1. Per-instrument 4h cells may miss D-prec and be reported `UNDER_POWERED` /
   `INCONCLUSIVE_*` — anticipated by design §9 and handled (not forced to a
   verdict).
2. `draw_verdicts.csv` is 142 MB; the projected 6-column scan keeps memory
   bounded. Acceptable.

## Verdict

```
VERDICT: APPROVE
```
