# Analysis Plan: Experiment EXP-009

## Objective

Determine whether 15-minute Heiken Ashi direction changes, evaluated strictly on real 1-minute time-bar prices, improve the coverage-adjusted AE-relative-to-FE trade-off relative to raw 15-minute time-bar direction changes.

## Methodology

### Step 1: Generate Time-Bar and HA Direction-Change Signals

- **Method**: Generate 15-minute time bars from holdout-excluded 1-minute analysis data, generate HA candles from those 15-minute bars, derive HA direction from HAClose versus HAOpen, and mark direction-change events. Build the matching 15-minute time-bar direction-change signal set from real close movement.
- **Why this method**: HA's legitimate role in Phase 2 is smoothing signal state, not return evaluation.
- **Simpler alternative considered**: Compare all HA bars and all time bars. Rejected because the hypothesis concerns direction-change signals.
- **Assumptions**: HA direction is available at the same `CloseTime` as the source bar and uses no future data.
- **Expected output**: 15-minute signal table with time-bar and HA direction-change events by instrument and volatility regime.

### Step 2: Compute Shared Signal-Quality Metrics

- **Method**: Use the EXP-007 framework to compute FE60, AE60, log FE/AE, precision, recall, run continuation, and multiplicity from real 1-minute time-bar prices. FE60, AE60, and log FE/AE carry the hypothesis verdict; precision, recall, run continuation, and multiplicity are diagnostics.
- **Why this method**: It enforces synthetic-price discipline and keeps results comparable with EXP-007.
- **Simpler alternative considered**: HAClose return comparison. Rejected because this is a signal-quality experiment, not a distortion diagnostic.
- **Assumptions**: HA construction prices are allowed only for signal direction classification, never for outcome magnitude.
- **Expected output**: Metric summaries for 15-minute time-bar and HA signal sets, including coverage-adjusted FE60 and AE60 over the full time-bar direction-change reference population.

### Step 3: Compare HA Against Time Bars

- **Method**: Bootstrap CIs (10,000 resamples, seed 42) for HA minus time-bar differences in FE60, AE60, and log FE/AE. Precision, event-level recall, and run continuation are summarized descriptively.
- **Why this method**: Bootstrap intervals handle non-normal signal-quality distributions and match prior Xen discipline.
- **Simpler alternative considered**: Mann-Whitney tests only. Rejected because the primary question needs effect sizes and CIs, not only rank differences.
- **Assumptions**: Instrument-level consistency is required before treating HA smoothing as broadly useful.
- **Expected output**: Comparison table by instrument and volatility regime, with verdict columns based only on 15-minute FE60/AE60/log FE/AE.

### Step 4: Quantify Signal-Count and Alignment Trade-Offs

- **Method**: Report HA/time signal-count ratio and the fraction of HA direction changes occurring within a one-bar, 15-minute tolerance window of time-bar direction changes.
- **Why this method**: HA may improve quality by reducing signal frequency; the coverage cost must be explicit.
- **Simpler alternative considered**: Ignore signal count and report quality only. Rejected because fewer signals can mechanically improve precision.
- **Assumptions**: Reduced frequency is acceptable only if quality gains are measurable and denominators remain explicit.
- **Expected output**: Signal-count and direction-change alignment diagnostics.

## Visualisations

1. FE and AE distributions for time-bar versus HA signals.
2. Coverage-adjusted FE60 and AE60 bars by instrument.
3. Signal-count and coverage-fraction plot by instrument and regime.
4. HA/time direction-change alignment heatmap.

## Interpretation Guide

- If HA improves 15-minute log FE/AE on at least 3 of 4 instruments and FE60/AE60 support the direction of that ratio, HA smoothing is supported as a signal-quality feature.
- If HA only reduces signal count without improving the AE-relative-to-FE trade-off, HA smoothing is not supported as a standalone signal generator.
- If HA improves low-volatility regimes only, the finding should be treated as regime-conditional.

## Complexity Check

- Statistical tests: 3 / 3 comparison families.
- Visualisations: 4 / 4.
- New modules: 0 / 0 shared modules, plus the experiment runner.

## Chart-Type Comparison Considerations

### Cross-Chart Alignment

- HA and time bars share `CloseTime`; no bar-index alignment is needed or allowed.

### Synthetic Price Discipline

- HAOpen and HAClose define HA direction only.
- All returns, excursions, and signal-quality metrics use real time-bar prices.

### Bar Density Differences

- HA is 1:1 with time bars, but direction-change frequency differs. Report direction-change count ratios.

### Regime Stratification

- Use time-bar train-segment volatility terciles from the shared framework.
