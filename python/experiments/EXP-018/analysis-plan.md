# Analysis Plan: Experiment EXP-018

## Objective

Test H3 using one deterministic candle/body displacement definition after EXP-015 failed sweeps.

## Methodology

### Step 1: Displacement Detection

- **Method**: For each EXP-015 failed sweep, search the next 10 bars for a directional candle whose body is >= 1.5 times the rolling median absolute body over the prior 100 completed bars and whose close is in the directional quartile.
- **Why this method**: It follows the planning spec's recommended initial displacement parameters without adding swing-break logic.
- **Simpler alternative considered**: Visual displacement labels are not reproducible.
- **Assumptions**: Rolling median and close-location values use only bars known by the displacement close.
- **Expected output**: Displacement-confirmed event table and missed-sweep table.

### Step 2: Entry Proxy and Outcome Measurement

- **Method**: Compare sweep-close entry proxy, displacement-close entry proxy, and next-open after displacement using EXP-015 stop/risk conventions and 60-minute outcomes from each entry timestamp.
- **Why this method**: It tests whether waiting for displacement improves or delays the signal.
- **Simpler alternative considered**: Only counting displacement frequency would not test H3's expectancy claim.
- **Assumptions**: Events without enough forward bars are excluded with reason codes.
- **Expected output**: Outcome table by entry proxy and instrument.

### Step 3: Sweep-Only Versus Displacement Comparison

- **Method**: Bootstrap differences in 60-minute expectancy in R and 1R-before-stop probability; report retained-event percentage first.
- **Why this method**: It measures benefit after sample-size loss.
- **Simpler alternative considered**: Mean expectancy alone is sensitive to outliers.
- **Assumptions**: Interpretation requires both train and test direction, not train-only improvement.
- **Expected output**: Effect-size and count table.

## Visualisations

1. Sweep-to-displacement count waterfall.
2. Entry proxy expectancy interval plot.
3. MFE/MAE distribution for sweep-only versus displacement-confirmed events.
4. Delay distribution from sweep to displacement.

## Interpretation Guide

- Support: displacement improves expectancy in R or 1R-before-stop probability by scoped thresholds on at least 3 instruments with event floors met.
- Against: entries are delayed without quality improvement or samples collapse.
- Inconclusive: train improvement does not persist in test.

## Complexity Check

- Statistical tests: 2-3 / 3
- Visualisations: 4 / 5
- New modules: 2 / 2
