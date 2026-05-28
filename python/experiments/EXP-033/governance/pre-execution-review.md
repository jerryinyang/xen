# Governance Review: Experiment EXP-033 — Pre-Execution

**Date**: 2026-05-27
**Review Type**: Pre-Execution
**Artifacts Reviewed**: `scope.md`, `analysis-plan.md`, `code/run_experiment.py`

## Executive Summary

All pre-execution governance constraints pass. The scope predeclares the rule menu and the readiness gates from `design.md` §"Candidate Rule Families" / §"Readiness Pattern" with mathematically attainable thresholds. The analysis plan operationalises every readiness check and the aggregate verdict mechanically and respects the complexity budget. The implementation reuses `bar_aggregator` and `ict_timebar`, applies holdout exclusion on the 1-minute series before aggregation, prevents look-ahead at every detection step, and excludes returns / excursions / P&L entirely per the design.md selectivity-before-outcome gate.

## Constraint Checks

### Simplicity Check

| Artifact | Verdict | Notes |
| --- | --- | --- |
| scope.md | PASS | Five rule families with one predeclared parameter set each. No combinations, no segmentation, no optimisation. |
| analysis-plan.md | PASS | One statistical test family (block bootstrap). Four plots. Verdict logic is mechanical (lowest inversion rate, tie-break by event count). |
| code/run_experiment.py | PASS | Pure-function helpers; orchestration centralised in `run_experiment`. No new analytical modules. |

### Academic-Finance Pitfall Check

| Artifact | Verdict | Notes |
| --- | --- | --- |
| scope.md | PASS | No normality, stationarity, or i.i.d. assumption. Block bootstrap is non-parametric. |
| analysis-plan.md | PASS | Block bootstrap chosen explicitly to preserve local temporal dependence; Wilson/Agresti-Coull explicitly rejected with reason. |
| code/run_experiment.py | PASS | Bootstrap implementation samples contiguous blocks; no parametric assumption. |

### Scope Compliance Check

| Artifact | Verdict | Notes |
| --- | --- | --- |
| scope.md | PASS | Single meta-question on rule readiness. Outcomes explicitly excluded. Branch B scope inherits from reflection §10 amendment. |
| analysis-plan.md | PASS | Maps 1:1 to scope: baseline + 5 rules × 4 instruments × 2 segments = 40 cells, six readiness checks, aggregate verdict. |
| code/run_experiment.py | PASS | Constants match scope parameter values exactly: `R1_SIZE_ATR_COEFF=0.10`, `R2_LIFECYCLE_BARS=24`, `R3_BODY_MULTIPLE=1.5` etc. No drift. |

### Principles Check

| Artifact | Data-Driven | Non-Parametric | Real-Price Discipline | Holdout Excluded |
| --- | --- | --- | --- | --- |
| scope.md | PASS | PASS | PASS (no outcomes in scope) | PASS |
| analysis-plan.md | PASS | PASS | PASS | PASS |
| code/run_experiment.py | PASS | PASS | PASS (no return/MAE/MFE/Hit code paths) | PASS (`load_analysis_timebars` slices 70% on the 1-minute series) |

### Phase-Alignment Check

| Artifact | Verdict | Notes |
| --- | --- | --- |
| All | PASS | Aligned with reflection §10.5/§10.7. Branch A is closed; this is the first Branch B experiment with renumbered IDs (was placeholder EXP-036). USTEC eligibility constraint preserved as documented for any future convergence reopen. |

### Look-Ahead Bias Check (code-specific)

| Source | Verdict | Notes |
| --- | --- | --- |
| ATR14Prior | PASS | `rolling_mean(...).shift(1)` ensures the value at bar i is knowable strictly before bar i closes. |
| BodyMedian100Prior | PASS | `rolling_median(window=100).shift(1)` same discipline. |
| IFVG inversion search | PASS | `start = creation_idx + 1` excludes the creation bar from inversion candidates. |
| R4 mitigation order | PASS | `_first_valid_inversion` requires `inv_positions > first_part` (strict). |
| R5 sweep window | PASS | Sweep window is `sweep_ns < formation_ns AND sweep_ns >= formation_ns - lookback_ns`. Strict on the upper bound. |
| R5 zone radius | PASS | Uses the FVG's own `ATR14Prior` (which is already shifted), not future ATR. |
| 15m aggregation | PASS | `bar_aggregator.aggregate_ohlc` drops partial trailing windows; analysis-set 1-minute slice is built before aggregation. |

### Complexity Budget Check

| Item | Budget | Planned | Actual in code | Verdict |
| --- | --- | --- | --- | --- |
| Statistical test families | 1 | 1 (block bootstrap on inversion rate) | 1 (`_block_bootstrap_inversion_rate`) | PASS |
| Primary plots | 4 | 4 | 4 (`_plot_fvg_count_waterfall`, `_plot_inversion_rate_matrix`, `_plot_median_delay_matrix`, `_plot_readiness_grid`) | PASS |
| New reusable modules | 0 | 0 | 0 (only `bar_aggregator` and `ict_timebar` imports; no `python/src/` additions) | PASS |

### Selection-Discipline Check

| Item | Verdict | Notes |
| --- | --- | --- |
| No return/excursion/P&L in selection | PASS | `_qualifying_instruments_per_rule`, `_rule_contention_metrics`, and `_select_winning_rule` reference only `InversionRate`, `RuleEligibleIFVGCount`, and `PassesAllSixChecks`. |
| Tie-break order matches scope | PASS | (1) lowest combined inversion rate, (2) largest IFVG count, (3) explicit tie-break failure routes to reflection. |
| Mechanical verdict | PASS | `_select_winning_rule` is deterministic given the readiness table. |

### Predeclared-Constants Audit

| Scope value | Code constant | Match |
| --- | --- | --- |
| Baseline size 0.02 × ATR | `BASELINE_SIZE_ATR_COEFF = 0.02` | YES |
| Baseline lifecycle 120 bars | `BASELINE_LIFECYCLE_BARS = 120` | YES |
| R1 size 0.10 × ATR | `R1_SIZE_ATR_COEFF = 0.10` | YES |
| R2 lifecycle 24 bars | `R2_LIFECYCLE_BARS = 24` | YES |
| R3 body window 100 / multiple 1.5 | `R3_BODY_WINDOW = 100`, `R3_BODY_MULTIPLE = 1.5` | YES |
| R3 close-location 0.25 / 0.75 | `R3_LOWER_CLOSE_QUARTILE = 0.25`, `R3_UPPER_CLOSE_QUARTILE = 0.75` | YES |
| R5 lookback 24 bars / radius 1.0 × ATR | `R5_SWEEP_LOOKBACK_BARS = 24`, `R5_ZONE_ATR_COEFF = 1.0` | YES |
| Inversion band [0.55, 0.75] | `INVERSION_BAND_LOW = 0.55`, `INVERSION_BAND_HIGH = 0.75` | YES |
| Selectivity ceiling 0.80 | `SELECTIVITY_MAX_RETENTION = 0.80` | YES |
| Median delay bound 24 | `MAX_MEDIAN_DELAY_BARS = 24` | YES |
| Count floors 100 / 50 | `MIN_FVG_PER_SEGMENT = 100`, `MIN_IFVG_PER_SEGMENT = 50` | YES |
| Bootstrap block / reps / seed (EXP-029 convention) | `BOOTSTRAP_BLOCK = 50`, `BOOTSTRAP_REPS = 2_000`, `BOOTSTRAP_SEED = 42` | YES |

## Findings

### Critical

None.

### Warnings

None.

### Info

1. The pipeline re-derives the 1-minute → 15-minute frame twice per instrument per pass (once for `_load_instrument_15m`, once for `_instrument_levels_frame`). This is a minor efficiency cost only — every load goes through `load_analysis_timebars`, so holdout discipline is intact and determinism is unaffected. No remediation required.
2. `_aggregate_to_15m_with_features` writes the row-derived `Segment` column; `_attach_ny_features` drops and re-adds it to keep the row-based convention used by EXP-029. The two segment definitions are equivalent under the shared `ANALYSIS_TRAIN_FRACTION = 0.70` and `train_cutoff_time` boundary, so no aliasing exists.

## Verdict

```
VERDICT: APPROVE
```
