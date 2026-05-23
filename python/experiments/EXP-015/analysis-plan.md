# Analysis Plan: Experiment EXP-015

## Objective

Test H2: whether failed breaches of EXP-014 PDH/PDL or ONH/ONL levels show measurable opposite-direction behavior versus non-failed breaches.

## Methodology

### Step 1: Sweep and Breach Event Detection

- **Method**: Apply the scoped high/low sweep definitions with `price_precision_step` and ATR_14 buffers, using only prior completed bars for ATR and levels.
- **Why this method**: It implements the planning spec's failed-breakout definition without unsupported tick data.
- **Simpler alternative considered**: No-buffer sweeps are source-valid but less robust to price precision noise.
- **Assumptions**: Observed price increment is a proxy for minimum price step, not actual tick data.
- **Expected output**: Failed-sweep and non-failed-breach event table by level type, side, instrument, and segment.

### Step 2: Real-Price Outcome Measurement

- **Method**: For each event, compute stop/invalidation at the sweep extreme plus/minus buffer, initial risk from sweep close to stop, MFE/MAE, time-to-stop, and 1R/2R-before-stop probabilities over 30/60/120 minutes.
- **Why this method**: These are the source-spec failed-breakout outcomes and use real time-bar OHLC prices.
- **Simpler alternative considered**: Close-to-close return alone would miss path-dependent target/stop behavior.
- **Assumptions**: If stop and target occur in the same 1-minute bar, report the event as ambiguous and exclude it from hit-probability comparisons while retaining counts.
- **Expected output**: Outcome table by event type and horizon.

### Step 3: Failed Sweep Versus Breach Comparison

- **Method**: Use bootstrap confidence intervals for the primary difference in 60-minute 1R-before-stop probability and descriptive intervals for secondary MFE/MAE and 2R outcomes.
- **Why this method**: It avoids normality assumptions and keeps H2 focused on one primary endpoint.
- **Simpler alternative considered**: Comparing win rates without risk normalization would not test the ICT claim.
- **Assumptions**: Resampling unit is the event, stratified by instrument and segment.
- **Expected output**: Primary and secondary effect table with event counts.

## Visualisations

1. Event-count waterfall by instrument, level type, and side.
2. 60-minute 1R-before-stop difference interval plot.
3. MFE/MAE distribution by failed sweep versus non-failed breach.
4. Time-to-stop/target diagnostic plot.

## Interpretation Guide

- Support: primary 1R-before-stop probability improves on at least 3 instruments with required event counts.
- Against: failed sweeps do not outperform breaches or adverse excursion dominates.
- Inconclusive: event counts are below thresholds or confidence intervals cross zero on most instruments.

## Complexity Check

- Statistical tests: 2-3 / 3
- Visualisations: 4 / 5
- New modules: 2 / 2
