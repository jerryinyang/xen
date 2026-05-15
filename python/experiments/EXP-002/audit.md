# Audit Report: Experiment EXP-002

## Summary
- **Verdict**: CONDITIONAL PASS
- **Critical Issues**: 1
- **Warnings**: 3
- **Info Notes**: 4

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `run_experiment.py` | Correctness | PASS | Core metrics (hybrid rate, transition lag, bootstrap) implement the stated plan correctly. |
| `run_experiment.py` | Edge cases | PASS | Empty datasets, single-bar charts, no transitions, and null regimes are handled explicitly. |
| `run_experiment.py` | Type safety | PASS | Type hints on all public functions; consistent use of polars/pandas/numpy. |
| `run_experiment.py` | NaN handling | PASS | NaN regimes are dropped before metric computation; null volatility excluded from terciles. |
| `run_experiment.py` | Holdout exclusion | PASS | Final 30% is never loaded; `slice(0, int(source_rows * 0.7))` is applied before chart generation. |
| `run_experiment.py` | Docstrings | PASS | All public functions have Parameters and Returns sections. |
| `linebreak_generator.py` | Correctness | PASS | Stateful generation from completed closes; deterministic output. |
| `renko_generator.py` | Correctness | PASS | Close-based ATR Renko with sequential state; multiple bricks per bar handled correctly in generator. |
| `heiken_ashi_generator.py` | Correctness | PASS | Standard HA formulas with real prices preserved. |
| `time_alignment.py` | Correctness | PASS | Microsecond datetime normalization for joins. |

## Numerical Validation

### Spot Checks

**Hybrid rate mean diff (LineBreak3 vs Time)**
Differences = Time − LineBreak3, per instrument:
- EURUSD: 0.0 − 0.05726220928868132 = −0.05726220928868132
- XAUUSD: 0.0 − 0.05534391164546344 = −0.05534391164546344
- BTCUSD: 0.0 − 0.05490051334841323 = −0.05490051334841323
- USTEC: 0.0 − 0.04173017315714652 = −0.04173017315714652
Mean = (−0.2093098074397045) / 4 = **−0.05230920185992613**
→ Matches `bootstrap_results.csv` row 2 exactly.

**Lag mean diff (LineBreak3 vs Time)**
Differences = Time − LineBreak3, per instrument:
- EURUSD: 0 − 3 = −3
- XAUUSD: 0 − 2 = −2
- BTCUSD: 0 − 2 = −2
- USTEC: 0 − 2 = −2
Mean = −9 / 4 = **−2.25**
→ Matches `bootstrap_results.csv` row 3 exactly.

**Lag mean diff (Renko vs Time)**
Differences:
- EURUSD: 0 − 1 = −1
- XAUUSD: 0 − 2 = −2
- BTCUSD: 0 − 2 = −2
- USTEC: 0 − 2 = −2
Mean = −7 / 4 = **−1.75**
→ Matches `bootstrap_results.csv` row 5 exactly.

**Bootstrap CI sanity (LineBreak3 lag, n=4)**
Possible sample means with replacement from {−3, −2, −2, −2}:
- All −2 → mean = −2.0 (prob ≈ 0.316)
- One −3, three −2 → mean = −2.25 (prob ≈ 0.422)
- Two −3, two −2 → mean = −2.5 (prob ≈ 0.211)
- Three −3, one −2 → mean = −2.75 (prob ≈ 0.047)
- All −3 → mean = −3.0 (prob ≈ 0.004)

2.5th percentile ≈ −2.75; 97.5th percentile = −2.0.
→ Reported CI [−2.75, −2.0] is consistent with the discrete bootstrap distribution.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| HybridRate (all chart types) | [0, 1] | 0.0 to 0.0700 | YES |
| MedianLag (all chart types) | ≥ 0 | 0.0 to 3.0 | YES |
| Time bars HybridRate | 0.0 | 0.0 | YES |
| Time bars MedianLag | 0.0 | 0.0 | YES |
| Bootstrap MeanDiff HybridRate | (−1, 1) | −0.0619 to 0.0 | YES |
| Bootstrap MeanDiff Lag | ≥ −max(lag) | −2.75 to 0.0 | YES |
| SourceRows vs AnalysisRows | Analysis ≈ 70% | 69.9%–70.0% | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| Transitions per instrument (Time) | ~28 857 | YES | ~3.3% of ~870K bars; plausible for persistent 3-regime volatility. |
| LineBreak3 / Time bar ratio | ~0.24–0.27 | YES | Line Break level 3 compresses roughly 4×. |
| Renko / Time bar ratio | ~0.26–0.28 | YES | ATR-14 Renko yields similar density to Line Break 3. |
| HA / Time bar ratio | 1.0 | YES | Heiken Ashi is 1:1 with source bars. |
| Bootstrap CI width (LineBreak3 lag) | 0.75 bars | YES | Discrete support with n=4 produces narrow bounds. |
| Bootstrap CI width (Renko hybrid) | 0.0145 | YES | Tight because all 4 diffs are negative and similar in magnitude. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Train-derived terciles | Train set is representative of analysis-set volatility distribution | PARTIAL | Terciles are fixed thresholds; non-stationary volatility means regimes drift. This is acknowledged in the analysis plan. |
| Timestamp alignment | Cross-chart comparisons use time, not bar index | YES | All joins and metric computations use `CloseTime` / `SourceCloseTime`; no index-based alignment. |
| No look-ahead | Regime labels use only data available at or before each timestamp | YES | Rolling mean is backward-looking; terciles are fixed from train. |
| Bootstrap percentile CI | Bootstrap sampling distribution approximates the true sampling distribution | PARTIAL | n=4 instrument-level differences → very coarse bootstrap support; CIs are technically correct but have low resolution. |
| Holdout exclusion | Final 30% never loaded or inspected | YES | `slice(0, int(source_rows * 0.7))` applied before any chart generation; holdout never referenced. |

## Results Plausibility

- **Hybrid rates**: Event-based charts show small positive hybrid rates (~0.04–0.07), indicating roughly 4–7% of bars straddle regime boundaries. Time bars and HA are 0 by construction (1:1 mapping). This is internally consistent.
- **Median lags**: Event charts lag 1–3 time bars behind regime transitions, while Time and HA have 0 lag. This is expected because event charts are sparser.
- **Direction of effects**: Mean diffs are uniformly negative for both hybrid rate and lag, meaning event charts have **higher** (worse) hybrid rates and **higher** (worse) lags than the time-bar baseline. The CIs exclude zero in the negative direction, indicating the effect is systematic across the 4 instruments.
- **Improvement CSV**: Completely empty of values because baseline is zero (see Critical Issue 1).

## Scope Compliance

- **Analysis plan followed**: YES
- **Deviations**:
  1. `improvement_vs_time.csv` and the improvement heatmap are vacuous because percentage improvement against a zero baseline is undefined. This is a consequence of the metric design, not a deviation from the stated analysis steps.
  2. Metrics are computed on the **full analysis set** (train + test), not restricted to the test segment. The analysis plan does not explicitly mandate test-only evaluation, so this is acceptable.
- **Complexity budget**:
  - Statistical tests: 6 bootstrap CI computations (3 chart types × 2 metrics) vs budget of 3. If each bootstrap application counts as a test, this exceeds budget by 2×. If counted as 3 paired comparisons, it is within budget. Treat as borderline.
  - Visualisations: 4 / 4 (timeline, hybrid rate bars, lag boxplot, improvement heatmap).
  - New modules: 1 / 1 (`time_alignment.py` is the only new shared module used).
- **Holdout exclusion verified**: YES

## Issues

### Critical

1. **Improvement CSV and heatmap are entirely NaN due to division by zero**
   - File: `run_experiment.py`, lines 855–862
   - Description: Time bars have `HybridRate=0.0` and `MedianLag=0.0`. The improvement formula `(base_h - ev_h) / base_h` divides by zero for every instrument and every event chart type, producing `np.nan` for all rows in `improvement_vs_time.csv`. The improvement heatmap therefore shows no usable data.
   - Impact: One of the four planned visualisations is meaningless, and the improvement artifact cannot support the 20% threshold check required by the success criteria.
   - Fix: When the baseline is zero, compute absolute differences (`base - ev`) instead of percentage improvement, or emit a separate table with absolute reductions. Update `plot_improvement_heatmap` to handle negative absolute differences correctly.

### Warning

2. **Renko multi-brick source bars artificially deflate hybrid rate**
   - File: `run_experiment.py`, lines 296–310 (inside `compute_hybrid_rate`)
   - Description: A single source bar can produce multiple Renko bricks with identical `SourceCloseTime`. For bricks after the first from that bar, `starts == ends` in the hybrid-rate interval check, giving zero coverage. These bricks can never be hybrid but still count in the denominator.
   - Impact: Renko’s reported hybrid rate may be slightly lower than the intended metric (fraction of bars spanning boundaries), because zero-coverage bricks are included in the total bar count.
   - Fix: In `compute_hybrid_rate`, either exclude zero-coverage bricks from the denominator or merge consecutive bricks sharing the same `SourceCloseTime` into a single interval.

3. **Bootstrap on n=4 instrument-level differences has very low resolution**
   - File: `run_experiment.py`, lines 409–447 (`bootstrap_mean_ci`)
   - Description: The bootstrap samples from only 4 paired differences. The resulting sampling distribution is extremely coarse (e.g., for LineBreak3 lag, only 5 distinct means are possible). The CIs exclude zero, but the width and granularity are driven by sample size, not data variability.
   - Impact: Confidence intervals are technically correct but convey a false sense of precision; interpretation should treat them as indicative, not conclusive.
   - Fix: Document the small-n limitation in results interpretation; consider expanding the instrument set in follow-up work if the metric is retained.

4. **First chart bar excluded from hybrid rate without explicit rationale**
   - File: `run_experiment.py`, lines 296–301
   - Description: `starts[0] = ends[0]` forces the first bar’s interval length to zero, so it is skipped in the hybrid count. For event-based charts, the first bar may cover multiple initial time bars and could legitimately be hybrid.
   - Impact: Minor downward bias in hybrid rate; effect is small because the first bar is 1/N of the total.
   - Fix: Define the first bar’s start boundary as the first time bar’s `CloseTime` (or `analysis_df[0, "CloseTime"]`) rather than its own timestamp.

### Info

5. **Hypothesis is structurally disadvantaged against the time-bar baseline**
   - Description: Because regime labels are derived directly from 1-minute time bars, Time bars inherently have `HybridRate=0` and `MedianLag=0`. Event-based charts, being sparser, will always have non-negative hybrid rates and lags. The success criterion (“20% lower than time bars”) is mathematically impossible to satisfy with these metrics.
   - This is a methodology-design observation, not a code bug. The code correctly computes the metrics as specified.

6. **`CHART_CONFIG` fields `close_col` and `direction_col` are unused**
   - Description: These fields are defined in the configuration dict but never referenced in the orchestration or metric functions. They are dead configuration.
   - No impact on results.

7. **Complexity budget edge case**
   - Description: The analysis plan budgets 3 statistical tests, but the code computes 6 bootstrap CIs (3 event chart types × 2 metrics). Whether this exceeds budget depends on whether each metric application counts as a separate test or the bootstrap procedure counts as one test applied repeatedly.
   - Recommend clarifying counting rules in future analysis plans.

8. **Metrics computed on full analysis set rather than test segment only**
   - Description: The train/test split within the analysis set is created, but hybrid rate and lag are evaluated on the combined train+test data. The analysis plan does not explicitly restrict evaluation to the test set, so this is acceptable. Future plans should state the intended evaluation window explicitly.

## Re-Audit Requirements

To move from **CONDITIONAL PASS** to **PASS**, the following must be addressed:

1. **Fix the improvement calculation**
   - Modify `run_experiment.py` lines 855–862 to compute absolute differences (`base_h - ev_h` and `base_l - ev_l`) when the baseline is zero, or emit a separate `absolute_improvement` column.
   - Re-run the experiment to produce a non-empty `improvement_vs_time.csv` and a meaningful improvement heatmap.
   - Verify: `improvement_vs_time.csv` contains finite numeric values for all rows; the heatmap renders without empty panels.

No other changes are required for audit clearance.
