# Analysis Plan: Experiment EXP-007

## Objective

Determine whether the Phase 2 real-price signal-quality framework differentiates chart types beyond binary direction entropy, and decide whether Block B has a valid measurement language for EXP-008 through EXP-011.

## Methodology

### Step 1: Build and Validate the Shared Signal-Quality Framework

- **Method**: Deterministic signal-outcome computation with explicit denominator accounting.
- **Why this method**: All Block B experiments depend on one common measurement substrate. Validating it once reduces downstream inconsistency.
- **Simpler alternative considered**: Per-experiment metric code. Rejected because it increases denominator and look-ahead drift across experiments.
- **Assumptions**: Signal timestamps can be mapped to 1-minute real time-bar prices by `CloseTime` or `SourceCloseTime`; forward outcome windows are labels, not signal inputs.
- **Expected output**: Framework validation table covering determinism, fixed denominators, AE=0 preservation, bounded signal-level precision, multiplicity diagnostic, and no-lookahead in signal construction.

### Step 2: Generate Signal Sets

- **Method**: Extract direction-change or event-emission signals from Time Bars, Line Break level 3, Renko ATR-14, and Heiken Ashi at 1-minute and 15-minute source timeframes.
- **Why this method**: It directly follows the Phase 2 design and preserves chart-type native event timing.
- **Simpler alternative considered**: Use only reversal labels from EXP-004. Rejected because EXP-007 needs a general signal-quality distribution, not a reversal-detection-only metric.
- **Assumptions**: Chart types produce different event counts; comparisons must report signal-count ratios and missing-signal states.
- **Expected output**: Signal table by instrument, timeframe, chart type, timestamp, direction, volatility regime, and source identifier.

### Step 3: Compute Real-Price Signal-Quality Metrics

- **Method**: For each signal, compute FE and AE over 30, 60, 120, and 240 minutes in ATR units; signal-level precision at the 60-minute FE >= 1.0 ATR threshold; event-level recall over qualifying real-price moves; run continuation over 30 minutes; log FE/AE as secondary.
- **Why this method**: These metrics separate magnitude, adverse movement, coverage, and continuation while staying outside strategy P&L.
- **Simpler alternative considered**: Binary direction agreement. Rejected because Phase 1 and Block A showed binary direction is not sufficient.
- **Assumptions**: ATR and regime labels are calibrated on the nested train segment only and applied forward within the analysis set.
- **Expected output**: Per-signal metric table and per-stratum summaries by instrument, timeframe, chart type, and regime.

### Step 4: Evaluate Proceed Criteria

- **Method**: Bootstrap CIs (10,000 resamples, seed 42) for event-chart minus time-bar differences on FE, AE, signal-level precision, and run-continuation rate. Evaluate the three pre-specified proceed criteria.
- **Why this method**: Bootstrap intervals match prior Xen experiment discipline and avoid parametric distribution assumptions.
- **Simpler alternative considered**: Raw mean differences only. Rejected because uncertainty must be quantified before downstream experiments proceed.
- **Assumptions**: Instrument-level consistency is more important than a pooled average; time dependence weakens naive row-level independence, so interpretation emphasizes effect size and instrument consistency.
- **Expected output**: Proceed-criteria table with PASS/FAIL per metric, chart type, timeframe, and instrument count.

## Visualisations

1. FE distribution by chart type and timeframe - shows whether real-price favourable movement differs beyond binary direction.
2. AE distribution by chart type and timeframe - shows adverse-move trade-offs.
3. Signal-level precision and event-level recall bars - separates hit quality from coverage.
4. Run-continuation heatmap by chart type, timeframe, and regime - shows regime-specific continuation.
5. Signal-count ratio plot - shows compression/coverage differences.
6. Entropy versus FE differentiation summary - shows why binary direction is insufficient or sufficient.

## Interpretation Guide

- If any proceed criterion is met at either timeframe, Block B may continue using only the metrics that met or materially supported differentiation.
- If no proceed criterion is met, Block B chart-type combination experiments stop and the Phase 2 failure-path redirect applies.
- If FE improves but AE worsens, the result is not a simple quality gain; downstream experiments must carry both metrics separately.
- If log FE/AE is flagged because AE=0 exceeds 20% in a stratum, FE and AE distributions are the primary evidence for that stratum.

## Complexity Check

- Statistical tests: 4 / 4 primary comparison families.
- Visualisations: 6 / 6.
- New modules: 1 / 1 shared reusable module, plus the experiment runner.

## Chart-Type Comparison Considerations

### Cross-Chart Alignment

- Align event charts by `SourceCloseTime`; align time bars and Heiken Ashi by `CloseTime`.
- Never compare by bar index or bar count.
- Report signal counts and missing-signal states instead of dropping sparse chart-type periods.

### Synthetic Price Discipline

- Heiken Ashi prices are never used for returns, excursions, or P&L.
- Renko and Line Break construction prices are never used for returns, excursions, or P&L.
- All outcomes are resolved from aligned 1-minute real time-bar prices.

### Bar Density Differences

- Report signal-count ratios by chart type and timeframe.
- Interpret precision and recall separately because event charts emit fewer signals.

### Regime Stratification

- Volatility regimes are derived from time-bar realised volatility using train-segment terciles and applied uniformly across chart types.
