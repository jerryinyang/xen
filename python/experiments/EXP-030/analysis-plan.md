# Analysis Plan: Experiment EXP-030

## Objective

Determine whether first-touch PDH/PDL and ONH/ONL failed-breakout sweep behavior on synthetic 15-minute bars differs materially from the EXP-015 1-minute baseline in sign or magnitude of the sweep-vs-breach 60-minute 1R-before-stop probability difference, while preserving 1-minute real-price outcome discipline and reporting event counts before any effect size.

## Methodology

### Step 1: Holdout-Safe 15-Minute Aggregation and Level Loading

- **Method**: For each instrument, lazily scan the 1-minute Parquet, sort by `CloseTime`, slice the first 70 percent chronologically as the analysis set, and resample the analysis-set slice only into synthetic 15-minute OHLC via deterministic clock-aligned non-overlapping windows. Drop partial trailing 15-minute windows. Load the EXP-014 reproducible PDH/PDL/ONH/ONL daily levels covering the analysis-set date range. Retain the 1-minute analysis-set slice in memory for outcome evaluation.
- **Why this method**: Holdout exclusion must apply to the 1-minute series before aggregation per the design.md data-scope rule. Keeping the 1-minute analysis-set slice in memory avoids reloading for outcomes and satisfies the "no repeated heavy loads" code-conventions rule.
- **Simpler alternative considered**: Aggregating the full 1-minute series and re-slicing on the 15-minute side would be one line shorter but is a governance violation under the checkpoint's data-scope rule.
- **Assumptions**:
  - **Temporal structure**: 1-minute and 15-minute series are chronologically ordered by `CloseTime`; daily levels are timestamped at session boundaries.
  - **Cross-view alignment**: 15-minute bar `CloseTime` maps to 1-minute `CloseTime` for outcome evaluation; never bar index.
  - **Real-price outcomes**: Outcomes are evaluated on 1-minute real OHLC; 15-minute is detection-only.
- **Expected output**: One 15-minute DataFrame per instrument, one 1-minute analysis-set DataFrame per instrument, and a per-instrument levels table joined to NY-time session boundaries.

### Step 2: Sweep and Breach Detection on 15-Minute Bars

- **Method**: For each 15-minute bar in the analysis set, evaluate sweep and breach conditions against the active PDH/PDL/ONH/ONL levels using EXP-015's framework adapted to 15-minute body and wick: bearish high sweep when `High > level + buffer` AND `Close < level`; bullish low sweep when `Low < level - buffer` AND `Close > level`; bearish high breach when `Close > level + buffer`; bullish low breach when `Close < level - buffer`. Buffer is `max(price_precision_step, 0.05 * ATR_14_15m)` with `ATR_14_15m` computed on completed 15-minute bars only. Apply a first-touch policy: only the first qualifying 15-minute event in either direction against each daily level is retained per session.
- **Why this method**: Direct EXP-015 transfer at the rule level is the only fair test of "does behavior replicate at 15-minute." First-touch matches EXP-015 and prevents within-session redundancy.
- **Simpler alternative considered**: Allowing all touches would inflate counts but pollute the sample with within-session repeated events on the same level, breaking comparability with EXP-015.
- **Assumptions**:
  - **Temporal structure**: Sweeps and breaches use only the closing 15-minute bar and prior bars; no future data.
  - **Cross-view alignment**: Level activation windows are aligned to NY-time session boundaries already used in EXP-014.
  - **Real-price outcomes**: Not yet evaluated in this step.
- **Expected output**: Per-instrument event table with timestamp (`CloseTime` of confirming 15-minute candle), side (high/low), level type (PDH/PDL/ONH/ONL), classification (failed-sweep or breach), buffer, stop price, sweep-extreme price, level price, and segment label.

### Step 3: Outcome Evaluation on Real 1-Minute Prices

- **Method**: For each detected event, define the outcome clock to start at the close of the confirming 15-minute candle. Walk the 1-minute analysis-set series forward strictly after that timestamp up to the 30, 60, and 120-minute horizons. Compute, on real 1-minute OHLC: (a) 1R-before-stop probability at 60 minutes (primary), 30 minutes, and 120 minutes (secondary); (b) MAE in R; (c) MFE in R; (d) forward log return at 60 minutes; (e) flag whether stop was hit within the horizon. Initial risk is the absolute distance from the confirming 15-minute `Close` to the stop in real-price units. Events whose initial risk is below `price_precision_step` are marked risk-infeasible and excluded from R-based outcomes but retained in counts.
- **Why this method**: The checkpoint requires the outcome clock to start only after the confirming 15-minute candle closes and to use real 1-minute prices. R-multiple outcomes match EXP-015 for direct comparability.
- **Simpler alternative considered**: Evaluating outcomes on 15-minute bars would lose intrabar stop and target precision and would not match the EXP-015 1-minute outcome basis, breaking timeframe comparability.
- **Assumptions**:
  - **Temporal structure**: 1-minute outcome walk is strictly forward from the post-confirmation timestamp.
  - **Cross-view alignment**: 15-minute event `CloseTime` is matched to the first 1-minute bar with `CloseTime` strictly greater than the 15-minute event `CloseTime`.
  - **Real-price outcomes**: All outcome metrics use real 1-minute OHLC; no 15-minute outcome surrogate.
- **Expected output**: Per-event outcome row joined to the Step 2 event table.

### Step 4: Counts, Comparison, and Verdict

- **Method (counts first)**: Report per-instrument and per-segment counts of failed-sweep and breach events, including risk-feasible counts. Compare against the predeclared floor (`>= 100` failed-sweep events per train/test segment). If the floor is missed on at least 3 of 4 instruments, mark the cross-instrument comparison as underpowered and classify the result as inconclusive before reporting any difference.
- **Method (primary comparison)**: For each instrument and segment, compute the difference in 60-minute 1R-before-stop probability between failed-sweep and breach events. Construct a 95 percent confidence interval via non-parametric stratified bootstrap (10,000 resamples, fixed seed 42, stratified by side and level type to preserve composition). Statistical test 1.
- **Method (secondary diagnostics)**: For each instrument and segment, compute the differences in MAE, MFE, and 60-minute forward log return between failed-sweep and breach events with the same bootstrap procedure. Statistical tests 2 and 3 (counted jointly as a single MAE/MFE/return diagnostic family).
- **Method (comparability to EXP-015)**: For each instrument, report the 15-minute primary effect side by side with the EXP-015 1-minute point estimate and CI. The reflection uses both rows; no statistical test is run on the cross-timeframe difference because the two samples are not independent.
- **Why this method**: Bootstrap is non-parametric, distribution-free, and the same family used in EXP-015, EXP-021, and EXP-023; using the same family preserves comparability.
- **Simpler alternative considered**: Reporting raw point estimates without intervals would be one line shorter but would not let the reflection distinguish material divergence from sample noise.
- **Assumptions**:
  - **Temporal structure**: Bootstrap resamples preserve event ordering only within strata; stratification by side and level type preserves event-type composition.
  - **Cross-view alignment**: 15-minute event timestamps are mapped to 1-minute outcome walks via `CloseTime`.
  - **Real-price outcomes**: All differences are computed on 1-minute real-price outcomes.
- **Expected output**: Per-instrument table with failed-sweep count, breach count, risk-feasible counts, primary 60-minute 1R difference and CI, secondary diagnostic differences and CIs, 15-minute-vs-1-minute side-by-side, and a verdict per the success criteria.

## Visualisations

1. **Event count by instrument, segment, and class** — grouped bar plot with horizontal reference at the `>= 100` failed-sweep floor.
2. **Primary 60-minute 1R-before-stop probability difference** (failed-sweep minus breach) by instrument with bootstrap CI bars, with the EXP-015 1-minute point and CI overlaid for direct comparison.
3. **MAE and MFE distributions** by instrument, failed-sweep vs breach, as paired violin or box plots.
4. **Per-instrument horizon sweep** (30/60/120 minutes) of the 1R-before-stop difference to confirm the 60-minute primary is not an isolated horizon artifact.

## Interpretation Guide

- **Support**: 15-minute failed-sweep beats breach on the primary 60-minute 1R difference with CI excluding zero on at least 1 instrument that did not show this at 1-minute, OR the EURUSD partial positive replicates with a tighter or stronger interval at 15-minute, with adequate counts. The reflection treats this as a "new broad positive not seen at 1-minute" trigger or as strengthened EURUSD support, depending on which case applies, and uses the matrix in the design.md to direct branches.
- **Against**: CIs include zero on all 4 instruments and the EURUSD partial 1-minute positive disappears, with adequate counts. The reflection treats this as a refutation of any sweep reversal effect at 15-minute and notes it does not alter Branches A or B.
- **Inconclusive**: Floor missed on at least 3 instruments, classified as underpowered before direction is interpreted. The reflection records the resolution cost and does not interpret direction.

## Complexity Check

- Statistical tests: 3 (primary 60-minute bootstrap; secondary MAE/MFE/return bootstrap family; horizon-sweep bootstrap diagnostic) / 3
- Visualisations: 4 / 4
- New modules: 0-1 (`python/src/bar_aggregator.py`, reused from EXP-029 if already created) / 1

## Data-View Comparison Considerations

### Cross-View Alignment
- Detection uses 15-minute `CloseTime`; outcome walks use 1-minute `CloseTime` strictly after the confirming 15-minute candle close.
- Cross-view alignment is always by timestamp, never by bar index.
- Coverage diagnostics report dropped partial 15-minute windows so the reflection can distinguish detection-coverage differences from event-rate differences.

### Real-Price Outcome Discipline
- All 1R, MAE, MFE, return, and stop-hit outcomes are computed on real 1-minute OHLC.
- The 15-minute view is detection-only and supplies no outcome prices.
- The buffer and stop are computed in real-price units, not 15-minute aggregate units; the 15-minute `Close` is a real 1-minute closing price by construction of the resampling rule.

### Event Density Differences
- 15-minute event counts are expected to be lower than 1-minute event counts; the count floor must be checked before interpreting any effect direction.
- First-touch policy is identical to EXP-015 and is the dominant factor in per-session event density.

### Regime Stratification
- This experiment does not stratify by volatility regime. The hypothesis is about sweep reversal behavior at 15-minute resolution as a whole. Regime stratification belongs to follow-up entry-quality experiments only if this pre-phase produces a new positive.
