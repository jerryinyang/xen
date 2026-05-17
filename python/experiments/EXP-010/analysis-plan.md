# Analysis Plan: Experiment EXP-010

## Objective

Determine whether Line Break level 3 confirmation stratifies 15-minute Renko ATR-14 signals into a subset with a better coverage-adjusted AE-relative-to-FE trade-off on the real-price timeline. The 1-minute arm is exploratory only.

## Methodology

### Step 1: Construct Renko Primary and Line Break Confirmation Sets

- **Method**: Generate Renko ATR-14 and Line Break level 3 per instrument/timeframe. Mark each Renko signal as Line Break-confirmed if a Line Break event of matching direction occurred at or before the Renko signal timestamp within the fixed confirmation window.
- **Why this method**: It tests Line Break as a confirmation layer over Renko, not as a competing signal source.
- **Simpler alternative considered**: Compare Line Break alone against Renko alone. Rejected because Phase 2 asks whether Line Break selects a better Renko subset.
- **Assumptions**: Confirmation uses same-or-prior `SourceCloseTime` and direction only; construction prices are irrelevant for outcome measurement.
- **Expected output**: Renko signal table with confirmed and non-confirmed labels, with 15-minute rows flagged as confirmatory and 1-minute rows flagged as exploratory.

### Step 2: Compute Shared Signal-Quality Metrics

- **Method**: Use the EXP-007 framework to compute FE60, AE60, log FE/AE, precision, recall, run continuation, and multiplicity at Renko signal timestamps. FE60, AE60, and log FE/AE carry the hypothesis verdict; precision, recall, run continuation, and multiplicity are diagnostics.
- **Why this method**: It evaluates the same Renko timestamp regardless of Line Break confirmation status, isolating confirmation as a stratifier.
- **Simpler alternative considered**: Measure outcomes at Line Break timestamps. Rejected because the primary signal layer is Renko.
- **Assumptions**: Outcomes are real-price labels and may use forward windows; confirmation eligibility must not use future data.
- **Expected output**: Metric summaries for all Renko, Line Break-confirmed Renko, and non-confirmed Renko signals, including coverage-adjusted FE60 and AE60 over the full Renko signal population.

### Step 3: Compare Confirmed and Non-Confirmed Renko Signals

- **Method**: Bootstrap CIs (10,000 resamples, seed 42) for confirmed minus all-Renko and confirmed minus non-confirmed differences in FE60, AE60, and log FE/AE.
- **Why this method**: It quantifies whether Line Break confirmation selects a better AE/FE subset and whether the non-confirmed subset has materially different outcomes.
- **Simpler alternative considered**: Coverage-only analysis. Rejected because coverage selection only matters if the AE/FE trade-off changes.
- **Assumptions**: Sparse confirmed subsets must be reported as low-power rather than dropped; only 15-minute comparisons can support the hypothesis.
- **Expected output**: Quality and coverage table by instrument, timeframe, regime, and confirmation window, with confirmatory verdict columns populated only for 15-minute results.

### Step 4: Separate 1-Minute Directional Filtering From 15-Minute Coverage Selection

- **Method**: Report 15-minute results as confirmatory and 1-minute results as exploratory. At 15-minute, evaluate whether confirmation selects structurally different episodes despite expected perfect matched directional agreement.
- **Why this method**: Block A showed the interpretation differs by timeframe.
- **Simpler alternative considered**: Pool timeframes. Rejected because pooling hides the directional-filtering versus coverage-selection distinction.
- **Assumptions**: The 15-minute result should not be interpreted as directional disagreement filtering if matched LB/Renko agreement is 1.0.
- **Expected output**: Timeframe-specific interpretation table distinguishing 15-minute coverage selection from exploratory 1-minute behavior.

## Visualisations

1. Confirmed versus non-confirmed FE60, AE60, and log FE/AE distributions by timeframe.
2. Coverage-cost bars by instrument and tolerance window.
3. Coverage-adjusted FE60 and AE60 bars for all Renko, confirmed Renko, and non-confirmed Renko.
4. Regime-stratified AE/FE trade-off heatmap.
5. Timeframe interpretation panel: exploratory 1-minute versus confirmatory 15-minute coverage selection.

## Interpretation Guide

- If confirmed 15-minute Renko signals improve log FE/AE on at least 3 instruments and FE60/AE60 support the direction of that ratio, Line Break confirmation is supported as a coverage-selection stratifier.
- If confirmed and non-confirmed Renko signals have similar quality, Line Break adds coverage reduction without signal-quality value.
- If 15-minute confirmation improves quality despite perfect directional agreement, the value is coverage selection, not directional filtering.
- If sensitivity windows reverse the result, the confirmation effect is inconclusive.

## Complexity Check

- Statistical tests: 4 / 4 comparison families.
- Visualisations: 5 / 5.
- New modules: 0 / 0 shared modules, plus the experiment runner.

## Chart-Type Comparison Considerations

### Cross-Chart Alignment

- Use Renko `SourceCloseTime` for primary signal timestamps.
- Use same-or-prior Line Break `SourceCloseTime` for confirmation windows.
- Never align by bar index.

### Synthetic Price Discipline

- Renko and Line Break construction prices are not used for outcomes.
- All outcomes use 1-minute real time-bar prices aligned to Renko signal timestamps.

### Bar Density Differences

- Report confirmed, non-confirmed, and all-Renko signal counts.
- Do not drop missing Line Break confirmations; they are the non-confirmed state.

### Regime Stratification

- Use time-bar train-segment volatility terciles from the shared framework.
