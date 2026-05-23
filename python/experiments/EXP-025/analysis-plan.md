# Analysis Plan: Experiment EXP-025

## Objective

Test H6: whether the fixed 2R target is justified versus simpler target and exit alternatives for one approved entry definition.

## Methodology

### Step 1: Eligible Entry Set and Stop Anchoring

- **Method**: Use the approved entry definition from EXP-021, EXP-023, or EXP-024 and verify event floors before target comparison. Fix stops using the approved sweep, IFVG, or breaker logic.
- **Why this method**: Exit evaluation is meaningful only after entry events meet the scoped >= 100 train and >= 50 test event floor on at least 3 instruments.
- **Simpler alternative considered**: Testing exits on all sweeps would not represent post-confirmation ICT entries.
- **Assumptions**: Entry and stop rules are frozen before target outcomes.
- **Expected output**: Eligible entry and stop-risk table.

### Step 2: Exit Variant Simulation

- **Method**: Simulate 1R, 1.5R, 2R, 3R, 60-minute time stop, and nearest opposing EXP-014 liquidity target using real time-bar OHLC path after entry.
- **Why this method**: It covers the planning spec's fixed-R and liquidity-target alternatives without optimizing targets.
- **Simpler alternative considered**: Testing only 2R would not justify the 1:2 claim.
- **Assumptions**: Same-bar target/stop ambiguity is reported and excluded from primary hit comparisons.
- **Expected output**: Exit outcome table by variant, instrument, and segment.

### Step 3: 2R Justification Test

- **Method**: Compare expectancy, median R, drawdown proxy, hit rate, and robustness across train/test for 2R versus alternatives using bootstrap intervals.
- **Why this method**: H6 requires 2R to be better or more robust, not merely profitable.
- **Simpler alternative considered**: Selecting the best target by train performance would be optimization.
- **Assumptions**: No target parameters are tuned after seeing results.
- **Expected output**: Fixed-R comparison and H6 verdict.

## Visualisations

1. R distribution by exit variant.
2. Expectancy interval plot by target.
3. Target/stop hit probability by variant.
4. Hold-time distribution by exit variant.
5. Instrument contribution table or plot.

## Interpretation Guide

- Support: 2R has better expectancy or robustness than alternatives on at least 3 instruments with acceptable drawdown.
- Against: 2R is dominated by simpler targets or unstable across train/test.
- Inconclusive: no approved entry definition has enough sample size.

## Complexity Check

- Statistical tests: 3 / 3
- Visualisations: 5 / 5
- New modules: 2 / 2
