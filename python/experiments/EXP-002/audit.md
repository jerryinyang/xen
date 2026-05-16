# Audit Report: Experiment EXP-002

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 3

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `run_experiment.py` | Correctness | PASS | Hybrid rate, transition lag, bootstrap, and verdict logic all implement the analysis plan correctly. |
| `run_experiment.py` | Edge cases | PASS | Empty DataFrame guards (`len <= 1`), NaN checks (`np.isnan`, `np.isfinite`), zero-eligible-count returns 0.0. |
| `run_experiment.py` | Type safety | PASS | All public functions have type hints; `dict[str, Any]`, `pl.DataFrame`, `np.ndarray`, `tuple` returns correct. |
| `run_experiment.py` | NaN handling | PASS | `drop_nulls(subset=["Regime"])` before metrics; `np.nan` returned when no transitions; `np.isfinite` guards in verdict logic. |
| `run_experiment.py` | Holdout exclusion | PASS | `load_analysis_timebar_data()` computes `source_rows` from lazy scan, then `.slice(0, int(source_rows * 0.7))` before `.collect()`. Holdout rows are never materialized. |
| `run_experiment.py` | Loader ordering | PASS | Lazy `pl.scan_parquet` with column projection (`TIMEBAR_COLUMNS`), `sort("CloseTime")`, then slice first 70%, then collect. |
| `run_experiment.py` | Memory/performance | PASS | Regime lookup normalization cached per timestamp column; timeline plot reuses first instrument's prepared data; `sample_for_timeline_plot` caps at 5,000 rows before pandas conversion. |
| `run_experiment.py` | Logging/output | PASS | Concise progress output per instrument; exception traceback on failure; all result files logged with row counts. |
| `run_experiment.py` | Organization/import side effects | PASS | Follows prescribed order: imports → path setup → constants → I/O helpers → pure computation → plotting → orchestration → `main()`. No directory creation at import time. |
| `run_experiment.py` | Plot data reuse | PASS | Timeline plot uses `timeline_time_bars` and `timeline_events` populated during the analysis pass; other plots use already-built summary/lag/improvement DataFrames. |
| `run_experiment.py` | Docstrings | PASS | All public functions have docstrings with Parameters and Returns sections. |

## Numerical Validation

### Spot Checks

**EURUSD LineBreak3 Hybrid Rate** (summary_metrics.csv: 0.08587):
- Time-bar baseline hybrid rate = 0.0 (by construction, 1:1 mapping fast path).
- LineBreak3 hybrid rate 0.0859 > 0.05 bound → exceeds threshold. Confirmed.

**EURUSD LineBreak3 Median Lag** (summary_metrics.csv: 0.0):
- 41,673 time-bar transitions; 27,115 matched, 14,558 missed.
- Median of confirmed lags = 0.0 means most confirming events occur at the transition timestamp itself. P95 = 13.0 bars, Max = 201.0 bars confirm non-zero tail. Consistent.

**Bootstrap HybridRateReduction** (bootstrap_results.csv: LineBreak3 vs Time, MeanDiff = -0.0776):
- Time baseline = 0.0, LB3 = 0.0859 → diff = 0.0 - 0.0859 = -0.0859 for EURUSD.
- Negative mean across 4 instruments (all 0/4 positive) → CI [-0.0845, -0.0691] excludes zero. Correct: event charts have higher hybrid rate (worse).

**Verdict** (hypothesis_verdict.csv: REFUTED):
- LineBreak3 hybrid rate > 0.05 on all 4 instruments (0.064–0.086).
- Renko hybrid rate > 0.05 on all 4 instruments (0.092–0.119).
- Both exceed on 4 ≥ 3 instruments → REFUTED per scope failure criteria. Correct.

**Validation table row accounting** (validation_table.csv):
- EURUSD Time: SourceRows=1,246,061, AnalysisRows=872,242. Ratio: 872,242/1,246,061 = 0.7000. Correct 70% split.
- EURUSD Time: GeneratedRows=872,222, DroppedRegimeRows=20. These 20 rows correspond to the rolling volatility warm-up window (first 20 bars have null RealisedVol). Consistent.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| HybridRate | [0.0, 1.0] | [0.0, 0.119] | YES |
| MedianLag | ≥ 0 | [0.0, 0.0] | YES |
| P95Lag | ≥ 0 | [0.0, 14.0] | YES |
| MaxLag | ≥ 0 | [0.0, 660.0] | YES |
| TransitionCount | ≥ 0 | [31,900, 54,753] | YES |
| DroppedRegimeRate | [0.0, 1.0] | [1.3e-05, 6.1e-05] | YES |
| AnalysisRows / SourceRows | ~0.70 | 0.7000 (all instruments) | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| Bootstrap CI for HybridRateReduction (LB3) | [-0.0845, -0.0691] | YES | All 4 instruments negative; CI excludes zero correctly. |
| Bootstrap CI for LagReduction (LB3) | [0.0, 0.0] | YES | All instruments have 0.0 lag difference; degenerate but correct. |
| Bootstrap N_Instruments | 4 | YES | All 4 instruments present for both metrics. |
| Verdict logic | REFUTED | YES | Both chart types exceed bounds on 4/4 instruments. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Rolling volatility (window=20) | Sufficient warm-up bars | YES | Only ~20 rows dropped per instrument for null regime (< 0.003% of analysis set). |
| Train-derived terciles | Train segment has enough data for stable thresholds | YES | Train cutoff = 610K+ rows per instrument; tercile thresholds well-defined. |
| Bootstrap (10,000 resamples, seed=42) | N=4 instruments sufficient for instrument-level bootstrap | PARTIAL | Only 4 instruments; bootstrap resamples at instrument level. CI is descriptive, not inferential for a broader population. Acceptable for characterisation. |
| Transition lag definition | Chart events can confirm at transition timestamp | YES | Median lag = 0.0 confirms many events align exactly; P95/Max show tail behavior. |
| Hybrid rate prefix-count algorithm | O(1) per-bar check after sorting | YES | Uses `np.searchsorted` for interval boundaries and prefix sums for regime counts. Correct. |

## Results Plausibility

Results are plausible and internally consistent:
- Time bars have zero hybrid rate and zero lag by construction (regime labels defined on them).
- Event charts (LineBreak3, Renko) have non-zero hybrid rates (6–12%) because aggregated bars span multiple time bars that may cross regime boundaries.
- Event charts have median lag = 0.0 (most confirm at the transition timestamp) but substantial P95/Max lags (up to 660 bars for LineBreak3 on USTEC), indicating a long tail of delayed confirmations.
- Heiken Ashi mirrors Time bars exactly (1:1 transformation), as expected.
- Bootstrap CIs confirm event charts are consistently worse than time bars on hybrid rate (all CIs negative, excluding zero).

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 3 statistical tests (hybrid rate, transition lag, bootstrap) / 3 budgeted; 4 visualisations / 4 budgeted; 0 new modules beyond experiment script / 1 budgeted.
- Holdout exclusion verified: YES
- Chart types match scope: Time, LineBreak3 (level 3), Renko (ATR 14), Heiken Ashi. YES.
- Instruments match scope: EURUSD, XAUUSD, BTCUSD, USTEC. YES.
- No parameter search, no predictive models, no strategy validation. YES.

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Time bar lag records in lag_data.csv**: All 166,677 Time bar lag entries are 0.0 (41,673 per instrument × 4 instruments). This is correct by construction — Time bars define the regime timeline, so every transition is confirmed instantaneously. These rows add ~2 MB to the CSV but carry no information. Prior experiments may choose to exclude Time bar lags from this output.

2. **Existing index documents reference a different hypothesis**: `python/experiments/INDEX.md` and `docs/experiments-docs/INDEX.md` contain an earlier formulation of the EXP-002 hypothesis ("more homogeneous volatility regimes") that differs from the current scope.md ("boundary cost versus time-bar lower bound"). The documenter stage should update these to reflect the actual executed hypothesis.

3. **Bootstrap at instrument level (N=4)**: The bootstrap resamples 4 instrument-level differences. With such a small N, the bootstrap distribution is coarse (only 4^10,000 possible resamples, but effectively limited by the 4 unique values). The CIs are descriptive summaries, not population inference. This is acceptable for Phase 1 characterisation but should be noted.

## Re-Audit Requirements

None. Audit verdict is PASS.
