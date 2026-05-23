# Analysis Plan: Experiment EXP-028

## Objective

Falsify the EXP-027 candidate through predeclared robustness checks across segment, delay, and cost stress without optimizing or creating regime-specific variants.

## Methodology

### Step 1: Candidate and Segment Eligibility

- **Method**: Load the approved EXP-027 candidate and segment its analysis-set trades by instrument, year, train/test, and ATR_14 volatility tercile computed inside the analysis set.
- **Why this method**: Robustness must test the same candidate under fixed, predeclared partitions.
- **Simpler alternative considered**: Ad hoc regime labels would invite post-hoc interpretation.
- **Assumptions**: Segments with fewer than 30 trades are labelled insufficient, not treated as failures.
- **Expected output**: Segment eligibility and trade-count table.

### Step 2: Execution Delay and Cost Stress

- **Method**: Re-evaluate the same candidate with 0/1/2-bar execution delays and EXP-012 cost scenarios, without changing stops, targets, or filters.
- **Why this method**: The planning spec explicitly calls for execution-delay and spread/slippage stress.
- **Simpler alternative considered**: Only year/instrument segmentation would miss practical execution fragility.
- **Assumptions**: Delayed entries that occur after invalidation are marked invalid and counted.
- **Expected output**: Stress-test outcome table.

### Step 3: Robustness Verdict

- **Method**: Summarize after-cost expectancy, median R, drawdown proxy, and positive-segment share; identify whether edge depends on one instrument, year, volatility tercile, delay, or cost scenario.
- **Why this method**: EXP-028 is falsification, not optimization.
- **Simpler alternative considered**: Selecting the best-performing segment would violate scope.
- **Assumptions**: Any proposed variant change is deferred to a later experiment.
- **Expected output**: Candidate robustness verdict and failure-mode table.

## Visualisations

1. Segment expectancy heatmap.
2. Execution-delay stress interval plot.
3. Cost-scenario stress plot.
4. Instrument/year contribution plot.
5. Positive-segment share summary.

## Interpretation Guide

- Support: candidate remains non-negative after costs in test overall, positive in at least two-thirds of populated segments, and survives 1-bar delay or base cost stress.
- Against: edge vanishes under plausible cost, delay, or segmentation.
- Inconclusive: EXP-027 candidate was not eligible or segment coverage is insufficient.

## Complexity Check

- Statistical tests: 2-3 / 3
- Visualisations: 5 / 5
- New modules: 2 / 2
