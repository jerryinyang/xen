# Analysis Plan: Experiment EXP-024

## Objective

Isolate whether the ICT second-candle-open execution rule improves or degrades entry quality versus simpler post-confirmation entries.

## Methodology

### Step 1: Approved Confirmation Event Set

- **Method**: Use one approved IFVG or breaker confirmation event set from EXP-021 or EXP-023 without changing filters, stops, or eligibility.
- **Why this method**: Execution timing must be isolated from confirmation quality.
- **Simpler alternative considered**: Creating a new confirmation set would add another component.
- **Assumptions**: Confirmation close is the first time the event is knowable.
- **Expected output**: Confirmation event table with zone and invalidation fields.

### Step 2: Entry Timing Simulation

- **Method**: Compute confirmation-close proxy, immediate next-open, second-candle-open, and first deterministic retest entry outcomes using the same stop/target rules and real time-bar prices.
- **Why this method**: It directly tests the execution timing claim from the planning spec.
- **Simpler alternative considered**: Comparing only next-open to second-open would omit the confirmation-close diagnostic.
- **Assumptions**: Retest is considered only after confirmation and before invalidation.
- **Expected output**: Entry-timing outcome table.

### Step 3: Timing Quality Comparison

- **Method**: Bootstrap differences in expectancy, MAE, hit rate, and entry slippage proxy relative to confirmation close.
- **Why this method**: It measures both signal quality and practical entry degradation.
- **Simpler alternative considered**: Entry price comparison alone would not measure trade outcome.
- **Assumptions**: Event counts are identical across entry variants except where later entries lack enough forward bars.
- **Expected output**: Second-candle-open verdict table.

## Visualisations

1. Entry-price displacement from confirmation close by timing rule.
2. Expectancy interval plot by timing rule.
3. R distribution by timing rule.
4. Missing-forward-bars count by timing rule.

## Interpretation Guide

- Support: second-candle-open has equal or better expectancy/MAE on at least 3 instruments without worse slippage proxy.
- Against: second-candle-open degrades entry price, R distribution, or hit rate.
- Inconclusive: differences are small with intervals crossing zero.

## Complexity Check

- Statistical tests: 2 / 2
- Visualisations: 4 / 4
- New modules: 1 / 1
