# Pre-Execution Governance Review: EXP-002

## Artifacts Reviewed

- `python/experiments/EXP-002/scope.md`
- `python/experiments/EXP-002/analysis-plan.md`
- `python/experiments/EXP-002/code/run_experiment.py` (post-revision and post-optimization)

## Governance Checks Applied

### Core Constraints

| Constraint | Status | Notes |
|---|---|---|
| Simplicity Over Complexity | PASS | Descriptive metrics (hybrid rate, transition lag) and bootstrap intervals are the simplest sufficient approach. |
| No Academic-Finance Pitfalls | PASS | Non-parametric bootstrap used; no normality/stationarity/i.i.d. assumptions. |
| Strict Experiment Scoping | PASS | Single hypothesis, defined boundaries, concrete success/failure criteria, complexity budget respected. |
| Framework Principles | PASS | Data-driven, non-parametric, synthetic price discipline observed, timestamp alignment used. |
| OOS Holdout Rule | PASS | Code computes the source row count, then materializes only the first 70% analysis slice through `load_analysis_timebar_data()`. The experiment no longer stores a full `full_df` before slicing. |
| Look-Ahead Bias Prevention | PASS | Regime labels computed from train-derived terciles; no future data used relative to event timestamps. |
| Synthetic Price Discipline | PASS | No P&L computed. Heiken Ashi uses `RealClose` for regime alignment where needed. |

### Artifact-Specific Checks

**Scope Document**
- Hypothesis is testable and specific: "Line Break level 3 and Renko ATR-14 represent volatility regime boundaries more cleanly than 1-minute time bars on at least 3 of 4 instruments, measured by lower hybrid rate and lower regime transition lag."
- Success/failure criteria are measurable with explicit thresholds (20% improvement, 3 of 4 instruments, bootstrap 95% CIs).
- Chart types, instruments, time range, exclusions all explicit.
- Complexity budget: 3 tests, 4 plots, 1 module — matches plan and code.
- Holdout exclusion and synthetic price rule explicitly stated.

**Analysis Plan**
- Methods justified with "why this method" and "simpler alternative considered" for each step.
- Assumptions documented.
- Cross-chart alignment specified by timestamp (`CloseTime` / `SourceCloseTime`).
- Visualisations are purposeful and within budget.
- Interpretation guide pre-defines outcomes.

**Code**
- Type hints present on all public functions.
- Docstrings with Parameters and Returns sections.
- NaN and edge-case handling explicit (`drop_nulls`, `np.isnan`, `np.isfinite`, empty DataFrame guards).
- Analysis, plotting, and orchestration separated.
- Data loading uses Polars `scan_parquet` with `sort("CloseTime")` and deduplication.
- Metric computation now uses timestamp-array search and prefix counts instead of repeated pandas filtering, preserving timestamp alignment while removing the dominant nested-loop bottleneck.
- Bootstrap uses deterministic seed.
- Holdout exclusion verified: first 70% slice only; no code path accesses holdout.

## Issues Found

### Critical

None.

### Warning

None.

### Info

None.

## Revision Summary

During initial code review, two metric implementation issues were identified and corrected before this governance review:

1. **Transition lag metric** (original `compute_transition_lags`): The initial implementation returned `np.ones()` for all transitions, making the lag metric uninformative. It was rewritten to compute actual time-bar lag from time-bar regime transition timestamps to the first subsequent chart bar timestamp.

2. **Hybrid rate metric** (original `compute_hybrid_rate`): The initial implementation measured regime transition density between consecutive chart bars rather than "fraction of bars spanning regime boundaries" as defined in the scope. It was rewritten to check whether any time bar covered by an event bar has a different regime label, with a fast-path returning 0 for 1:1 mappings (Time bars, Heiken Ashi).

3. **Improvement heatmap**: Identified that `improvement_df` contained multiple chart types per instrument-metric pair, which would cause `pivot()` to raise `ValueError`. The `plot_improvement_heatmap` function was updated to create one panel per chart type within a single figure.

4. **Performance and output completeness fixes** (post-optimization): The dominant hybrid-rate and transition-lag bottlenecks were replaced with vectorized timestamp-index computations; transition lags are computed once per chart type and reused for median lag and plot records; the first instrument's prepared analysis data is reused for the timeline plot; regime lookup normalization is cached per timestamp column; and bootstrap records are accumulated across all event chart types instead of being reset inside the event-type loop.

5. **Plot execution fixes**: The timeline plot now selects `SourceCloseTime` when present and falls back to `CloseTime` for Heiken Ashi, preserving the approved timestamp-alignment rule. Heatmap panels with no defined improvement values are rendered explicitly instead of passing all-NaN data into seaborn.

All corrections maintain holdout exclusion, timestamp alignment, and synthetic price discipline.

---

VERDICT: APPROVE
