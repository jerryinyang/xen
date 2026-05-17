# Analysis Plan: Experiment EXP-008

## Objective

Test whether Renko ATR-14 confirmation improves the real-price quality of time-bar direction signals at 1-minute and 15-minute source timeframes.

## Methodology

### Step 1: Construct Candidate, Gate, and Comparator Signal Sets

- **Method**: Build three signal sets per instrument/timeframe: all time-bar direction signals, Renko-confirmed time-bar signals, and raw Renko signals.
- **Why this method**: It directly tests Renko as a gate rather than as a competing chart type.
- **Simpler alternative considered**: Compare Renko signals only against time bars. Rejected because the experiment asks whether Renko improves a time-bar candidate pool.
- **Assumptions**: Confirmation by timestamp within a fixed window is sufficient for gate membership; missing Renko confirmation is an explicit non-confirmed state.
- **Expected output**: Signal membership table with candidate, confirmed, non-confirmed, and raw Renko labels.

### Step 2: Compute Shared Signal-Quality Metrics

- **Method**: Use the EXP-007 framework to compute FE, AE, log FE/AE, signal-level precision, event-level recall, run continuation, and signal multiplicity.
- **Why this method**: It keeps denominators and outcome definitions identical to the Block B baseline.
- **Simpler alternative considered**: Reuse EXP-004 reversal precision. Rejected because EXP-004 precision had a multiplicity artefact and was reversal-reference specific.
- **Assumptions**: Real-price outcomes are resolved from 1-minute time-bar prices at candidate signal timestamps.
- **Expected output**: Metric summaries for all time-bar, confirmed time-bar, non-confirmed time-bar, and raw Renko signal sets.

### Step 3: Compare Quality and Coverage

- **Method**: Bootstrap CIs (10,000 resamples, seed 42) for confirmed minus all-time-bar and confirmed minus raw-Renko differences. Report coverage as the fraction of time-bar signals confirmed by Renko.
- **Why this method**: It quantifies both the quality gain and the coverage cost without assuming normality.
- **Simpler alternative considered**: Point estimates only. Rejected because coverage-selection effects can be instrument-specific.
- **Assumptions**: Instrument-level consistency across at least 3 of 4 instruments is required for a supported finding.
- **Expected output**: Quality-coverage table by instrument, timeframe, regime, and tolerance window.

### Step 4: Tolerance and Timeframe Sensitivity

- **Method**: Treat 15 minutes as the primary confirmation window and 5/30 minutes as sensitivity checks. Report 1-minute and 15-minute results separately, then compare descriptively.
- **Why this method**: It prevents tolerance optimization while preserving robustness checks.
- **Simpler alternative considered**: Choose the best tolerance per instrument. Rejected as parameter optimization.
- **Assumptions**: Sensitivity windows can qualify confidence but cannot redefine the primary verdict.
- **Expected output**: Sensitivity table showing whether conclusions are stable across 5, 15, and 30 minutes.

## Visualisations

1. FE/AE distribution panels for all time-bar, Renko-confirmed, non-confirmed, and raw Renko signals.
2. Precision-recall bars by timeframe and instrument.
3. Coverage-cost plot by tolerance window.
4. Regime-stratified quality heatmap.
5. Timeframe contrast plot for 1-minute versus 15-minute confirmed-signal quality.

## Interpretation Guide

- If confirmed signals improve over all time-bar signals and remain comparable to raw Renko, Renko gating is supported.
- If confirmed signals improve quality but sharply reduce recall, the result is a precision-coverage trade-off rather than a complete signal improvement.
- If 15-minute improves while 1-minute does not, the Block A speed-and-precision inversion carries into signal quality only at 15-minute.
- If sensitivity windows reverse the conclusion, the result is inconclusive and must not be treated as a stable gate.

## Complexity Check

- Statistical tests: 4 / 4 comparison families.
- Visualisations: 5 / 5.
- New modules: 0 / 0 shared modules, plus the experiment runner.

## Chart-Type Comparison Considerations

### Cross-Chart Alignment

- Confirm Renko against time-bar candidate signals by timestamp window, never by bar index.
- Use Renko `SourceCloseTime` for confirmation timing.

### Synthetic Price Discipline

- Renko construction prices are not used for outcomes.
- All FE, AE, precision, recall, and run-continuation metrics use 1-minute real time-bar prices.

### Bar Density Differences

- Report confirmation coverage and raw Renko signal counts.
- Keep missing Renko confirmation as the non-confirmed state.

### Regime Stratification

- Use time-bar train-segment volatility terciles from the shared framework.
