# Analysis Plan: Experiment EXP-023

## Objective

Test H5: whether one EXP-022-approved breaker confirmation improves trade quality beyond a predeclared pre-breaker baseline.

## Methodology

### Step 1: Baseline and Breaker Event Chain

- **Method**: Load the predeclared baseline from EXP-018/EXP-019 or EXP-021 and append only the single EXP-022-approved breaker candidate.
- **Why this method**: It isolates the breaker contribution and avoids post-hoc "best baseline" selection.
- **Simpler alternative considered**: Trying multiple baselines would consume the result to define the comparison.
- **Assumptions**: Baseline and breaker config are frozen before execution.
- **Expected output**: Baseline-to-breaker event-count waterfall.

### Step 2: Outcome Measurement

- **Method**: Compute expectancy in R, average R, drawdown proxy, win rate, MAE, and trade count for baseline versus breaker-confirmed entries using real time-bar prices.
- **Why this method**: The source H5 claim is about trade quality, not merely win rate.
- **Simpler alternative considered**: Counts-only validation was already handled in EXP-022.
- **Assumptions**: Stops and targets remain unchanged from the baseline unless the breaker zone is the predeclared stop anchor.
- **Expected output**: Baseline versus breaker outcome table.

### Step 3: Contribution Assessment

- **Method**: Bootstrap differences in expectancy and drawdown proxy; report event retention and win-rate changes as secondary.
- **Why this method**: It distinguishes true contribution from sample-size pruning.
- **Simpler alternative considered**: Profit factor alone is unstable with sparse samples.
- **Assumptions**: Event floors must be met before claiming support.
- **Expected output**: Breaker contribution verdict by instrument and segment.

## Visualisations

1. Baseline-to-breaker event-count waterfall.
2. Expectancy and drawdown-proxy interval plot.
3. R-multiple distribution by baseline versus breaker.
4. Event retention by instrument.

## Interpretation Guide

- Support: breaker confirmation improves expectancy or drawdown-adjusted return on at least 3 instruments while retaining >= 50 breaker-confirmed events per train/test segment.
- Against: win rate improves only through sample reduction, expectancy fails, or drawdown worsens.
- Inconclusive: breaker is reproducible but event count is too low.

## Complexity Check

- Statistical tests: 2-3 / 3
- Visualisations: 4 / 5
- New modules: 2 / 2
