# Governance Review: Experiment EXP-005 — Pre-Execution

**Date**: 2026-05-14
**Review Type**: Pre-Execution
**Artifacts Reviewed**: 
- `python/experiments/EXP-005/scope.md`
- `python/experiments/EXP-005/analysis-plan.md`
- `python/experiments/EXP-005/code/run_experiment.py`

## Executive Summary

One fixable issue found in the sensitivity plot filter. All other checks pass.

## Constraint Checks

### Simplicity Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | Single hypothesis, clear boundaries. |
| analysis-plan.md | PASS | Methods justified, simpler alternatives considered. |
| code/run_experiment.py | PASS | Straightforward timestamp alignment, descriptive metrics, bootstrap CI. |

### Academic-Finance Pitfall Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | No normality/stationarity assumptions. |
| analysis-plan.md | PASS | Bootstrap CIs are non-parametric. |
| code/run_experiment.py | PASS | No parametric tests. |

### Scope Compliance Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| scope.md | PASS | Complexity budget respected. Holdout explicitly excluded. |
| analysis-plan.md | PASS | 3 tests, 5 plots, 1 module — within budget. |
| code/run_experiment.py | PASS | Implements exactly the 5 planned plots and 3 analysis steps. |

### Principles Check

| Artifact | Data-Driven | Non-Parametric | Phantom Price Discipline | Holdout Excluded |
|----------|------------|---------------|--------------------------|-----------------|
| scope.md | PASS | PASS | PASS | PASS |
| analysis-plan.md | PASS | PASS | PASS | PASS |
| code/run_experiment.py | PASS | PASS | PASS | PASS |

### Chart-Type Comparison Check

| Artifact | Timestamp Alignment | Bar Count Adjustment | Generator Determinism |
|----------|-------------------|---------------------|---------------------|
| code/run_experiment.py | PASS | PASS | PASS |

### Quality Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| code/run_experiment.py | PASS | Type hints, docstrings, explicit NaN handling, constants documented. |

## Findings

### Critical

None.

### Warnings

1. **Sensitivity plot filter misses key pairs**
   - File: `python/experiments/EXP-005/code/run_experiment.py`, lines 481–485
   - Description: The `is_key` filter in `plot_sensitivity` checks `(chart_a == "linebreak" & chart_b == "timebars")` and `(chart_a == "renko" & chart_b == "timebars")`, but because `compute_unordered_pair_metrics` always stores the earlier `CHART_TYPES` index as `chart_a`, the pairs with `timebars` are stored as `timebars-linebreak` and `timebars-renko`. Consequently, the filter only matches `linebreak-renko` and omits the two comparisons against time bars.
   - Impact: The sensitivity plot visualises only 1 of the 3 key comparisons, misleading the reader about robustness of the main finding.
   - Fix: Expand the filter to match both orderings for each unordered pair, e.g.:
     ```python
     is_key = (
         (((pl.col("chart_a") == "linebreak") & (pl.col("chart_b") == "renko"))
          | ((pl.col("chart_a") == "renko") & (pl.col("chart_b") == "linebreak")))
         | (((pl.col("chart_a") == "linebreak") & (pl.col("chart_b") == "timebars"))
          | ((pl.col("chart_a") == "timebars") & (pl.col("chart_b") == "linebreak")))
         | (((pl.col("chart_a") == "renko") & (pl.col("chart_b") == "timebars"))
          | ((pl.col("chart_a") == "timebars") & (pl.col("chart_b") == "renko")))
     )
     ```
     Or use a helper that checks unordered membership in `{"linebreak-renko", "linebreak-timebars", "renko-timebars"}`.

### Info

1. **Cohen's kappa omitted** — The analysis plan mentions kappa as an optional secondary sensitivity. The developer skipped it to stay within the 3-test budget. This is acceptable and documented.
2. **Regime method** — A 60-bar rolling standard deviation of log-returns is used. The plan left the exact method open. This is acceptable.
3. **EURUSD chosen for timeline raster** — The plan requests "one representative window"; EURUSD is used. Acceptable.

## Revision 1

**Date**: 2026-05-14
**Skill**: experiment-developer
**Change**: Expanded `is_key` filter in `plot_sensitivity` to match both orderings for each of the three key unordered pairs (`linebreak-renko`, `linebreak-timebars`, `renko-timebars`). Verified in code lines 481–488.

## Verdict

```text
VERDICT: APPROVE
```
