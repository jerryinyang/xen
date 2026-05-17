# Analysis Plan: Experiment EXP-011

## Objective

Determine whether three pre-fixed Renko-native features produce volatility regime labels that reduce Renko boundary cost and missed transitions relative to time-bar-derived tercile regimes, without introducing parameter search.

## Methodology

### Step 1: Compute Fixed Event-Native Features

- **Method**: For each Renko event, compute: event density as brick count per 60-minute rolling window; source-bar count per brick as median source bars consumed per brick in a 60-minute rolling window; brick-to-ATR ratio as brick price move divided by train-segment ATR.
- **Why this method**: The features are explicitly fixed in the Phase 2 design and use Renko internal structure only.
- **Simpler alternative considered**: Clustering or composite scoring. Rejected because it would introduce parameter search and post-hoc feature selection.
- **Assumptions**: Rolling features can be computed with information available at or before each event timestamp.
- **Expected output**: Renko event table with three feature columns by instrument and timeframe.

### Step 2: Freeze Tercile Regime Boundaries

- **Method**: Compute tercile boundaries for each feature on the nested train segment only and apply them unchanged to the remaining analysis set.
- **Why this method**: It prevents leakage from test periods and avoids segmentation optimization.
- **Simpler alternative considered**: Full-analysis terciles. Rejected because it uses information outside the train segment for calibration.
- **Assumptions**: Train-segment feature distributions are sufficient to define fixed low/medium/high event-native regimes.
- **Expected output**: Boundary table by instrument, timeframe, and feature.

### Step 3: Compare Boundary Cost and Missed Transitions

- **Method**: Compute hybrid rate and missed-transition rate for each event-native feature label versus time-bar-derived tercile regimes applied to Renko events. Use bootstrap CIs (10,000 resamples, seed 42) for feature-specific differences.
- **Why this method**: Hybrid rate and missed transitions are the direct failure modes identified in EXP-002 and Block A.
- **Simpler alternative considered**: Agreement rate only. Rejected because agreement does not directly measure boundary cost.
- **Assumptions**: Time-bar regimes remain the reference, not the replacement; event-native regimes are evaluated as Renko-specific analytical strata.
- **Expected output**: Feature-specific boundary-cost table and verdict.

### Step 4: Describe Signal-Quality Stratification

- **Method**: Use the EXP-007 framework to summarize FE and AE distributions by each event-native tercile and compare descriptive separation with time-bar regime strata.
- **Why this method**: Event-native regimes are useful only if they also create interpretable signal-quality strata.
- **Simpler alternative considered**: Select the feature with the strongest FE separation. Rejected as post-hoc feature selection.
- **Assumptions**: This step is descriptive; it cannot override the pre-specified boundary-cost criteria.
- **Expected output**: Descriptive FE/AE separation table by feature, instrument, timeframe, and regime.

## Visualisations

1. Feature distribution histograms with frozen train tercile boundaries.
2. Hybrid-rate comparison bars for each feature versus time-bar regimes.
3. Missed-transition-rate comparison bars for each feature.
4. Agreement heatmap between event-native labels and time-bar regime labels.
5. FE/AE distribution by event-native tercile versus time-bar tercile.

## Interpretation Guide

- If one pre-fixed feature reduces hybrid or missed-transition rates on at least 3 of 4 instruments, that feature is supported as a Renko-specific regime stratifier.
- If multiple features work, report them independently; do not rank or combine them into a selected best feature.
- If boundary cost improves but signal-quality strata do not separate descriptively, event-native regimes may be useful for mechanics but not for Phase 3 signal design.
- If no feature improves boundary cost, keep time-bar regimes as the only regime reference for Renko signal analysis.

## Complexity Check

- Statistical tests: 3 / 3 feature-specific comparison families.
- Visualisations: 5 / 5.
- New modules: 0 / 0 shared modules, plus the experiment runner.

## Chart-Type Comparison Considerations

### Cross-Chart Alignment

- Align Renko events to time-bar regimes using `SourceCloseTime`.
- Never align by bar index.

### Synthetic Price Discipline

- Renko construction prices are not used for returns or excursions.
- Brick-to-ATR ratio is a regime diagnostic feature only.
- All signal-quality outcomes use real 1-minute time-bar prices.

### Bar Density Differences

- Report event counts per feature tercile and timeframe.
- Sparse strata are reported as low-power, not dropped silently.

### Regime Stratification

- Time-bar regimes remain the canonical reference.
- Event-native regimes are evaluated as additional Renko-specific strata, not replacements for return evaluation.
