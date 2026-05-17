# Analysis Plan: Experiment EXP-008

## Objective

Test whether Renko ATR-14 confirmation improves the coverage-adjusted AE-relative-to-FE trade-off of time-bar direction signals at the 15-minute source timeframe. The 1-minute arm is exploratory only.

## Methodology

### Step 1: Construct Candidate, Gate, and Comparator Signal Sets

- **Method**: Build three signal sets per instrument/timeframe: all time-bar direction signals, Renko-confirmed time-bar signals, and raw Renko signals.
- **Why this method**: It directly tests Renko as a gate rather than as a competing chart type.
- **Simpler alternative considered**: Compare Renko signals only against time bars. Rejected because the experiment asks whether Renko improves a time-bar candidate pool.
- **Assumptions**: Confirmation by same-or-prior timestamp within a fixed window is sufficient for gate membership; missing Renko confirmation is an explicit non-confirmed state.
- **Expected output**: Signal membership table with candidate, confirmed, non-confirmed, and raw Renko labels, with 15-minute rows flagged as confirmatory and 1-minute rows flagged as exploratory.

### Step 2: Compute Shared Signal-Quality Metrics

- **Method**: Use the EXP-007 framework to compute FE60, AE60, log FE/AE, signal-level precision, event-level recall, run continuation, and signal multiplicity. FE60, AE60, and log FE/AE carry the hypothesis verdict; precision, recall, run continuation, and multiplicity are diagnostics.
- **Why this method**: It keeps denominators and outcome definitions identical to EXP-007 while using only the metrics EXP-007 validated for downstream confirmation.
- **Simpler alternative considered**: Reuse EXP-004 reversal precision. Rejected because EXP-004 precision had a multiplicity artefact and was reversal-reference specific.
- **Assumptions**: Real-price outcomes are resolved from 1-minute time-bar prices at candidate signal timestamps.
- **Expected output**: Metric summaries for all time-bar, confirmed time-bar, non-confirmed time-bar, and raw Renko signal sets, including separate FE60, AE60, log FE/AE, and coverage-adjusted full-opportunity summaries.

### Step 3: Compare Quality and Coverage

- **Method**: Bootstrap CIs (10,000 resamples, seed 42) for confirmed minus all-time-bar and confirmed minus raw-Renko differences on FE60, AE60, and log FE/AE. Report coverage as the fraction of time-bar signals confirmed by Renko, plus expected FE60 and AE60 over the full time-bar opportunity population.
- **Why this method**: It quantifies the AE/FE trade-off and the coverage cost without assuming normality.
- **Simpler alternative considered**: Confirmed-subset-only comparisons. Rejected because EXP-007 showed missing-signal states dominate interpretation.
- **Assumptions**: Instrument-level consistency across at least 3 of 4 instruments at 15-minute is required for a supported finding.
- **Expected output**: Quality-coverage table by instrument, timeframe, regime, and tolerance window, with confirmatory verdict columns populated only for 15-minute results.

### Step 4: Tolerance and Timeframe Sensitivity

- **Method**: Treat 15 minutes as the primary confirmation window and 5/30 minutes as sensitivity checks. Report 15-minute results as confirmatory and 1-minute results as exploratory.
- **Why this method**: It prevents tolerance optimization while preserving robustness checks.
- **Simpler alternative considered**: Choose the best tolerance per instrument. Rejected as parameter optimization.
- **Assumptions**: Sensitivity windows can qualify confidence but cannot redefine the primary verdict.
- **Expected output**: Sensitivity table showing whether conclusions are stable across 5, 15, and 30 minutes.

## Visualisations

1. FE60, AE60, and log FE/AE distribution panels for all time-bar, Renko-confirmed, non-confirmed, and raw Renko signals.
2. Coverage-adjusted FE60 and AE60 plot for the full time-bar opportunity population.
3. Coverage-cost plot by tolerance window.
4. Regime-stratified AE/FE trade-off heatmap for 15-minute results.
5. Exploratory 1-minute versus confirmatory 15-minute contrast plot.

## Interpretation Guide

- If confirmed 15-minute signals improve log FE/AE over all time-bar signals on at least 3 instruments, and FE60/AE60 support the direction of that ratio, Renko gating is supported as an AE/FE trade-off filter.
- If the confirmed subset improves only because coverage removes most opportunities while the full-opportunity outcome worsens, the result is not supported.
- If 15-minute improves while 1-minute does not, report the 1-minute result as exploratory context only.
- If sensitivity windows reverse the conclusion, the result is inconclusive and must not be treated as a stable gate.

## Complexity Check

- Statistical tests: 4 / 4 comparison families.
- Visualisations: 5 / 5.
- New modules: 0 / 0 shared modules, plus the experiment runner.

## Chart-Type Comparison Considerations

### Cross-Chart Alignment

- Confirm Renko against time-bar candidate signals by same-or-prior timestamp window, never by bar index.
- Use Renko `SourceCloseTime` for confirmation timing.

### Synthetic Price Discipline

- Renko construction prices are not used for outcomes.
- All FE, AE, precision, recall, and run-continuation metrics use 1-minute real time-bar prices.

### Bar Density Differences

- Report confirmation coverage and raw Renko signal counts.
- Keep missing Renko confirmation as the non-confirmed state.

### Regime Stratification

- Use time-bar train-segment volatility terciles from the shared framework.
