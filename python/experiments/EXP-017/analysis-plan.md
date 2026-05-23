# Analysis Plan: Experiment EXP-017

## Objective

Test whether the prior-day midpoint premium/discount filter improves EXP-015 sweep quality enough to justify its sample-size cost.

## Methodology

### Step 1: Premium/Discount Labeling

- **Method**: Use EXP-014 PDH/PDL to compute the prior-day midpoint, then label EXP-015 bearish high sweeps as premium only when sweep close is above midpoint and bullish low sweeps as discount only when sweep close is below midpoint.
- **Why this method**: It implements the planning spec's recommended initial location filter.
- **Simpler alternative considered**: VWAP or distance-from-open filters are reserved for later scopes.
- **Assumptions**: The midpoint is available only when PDH/PDL passed EXP-014 rules.
- **Expected output**: Filter pass/fail counts by instrument, side, and segment.

### Step 2: Outcome Reuse With Fixed Definitions

- **Method**: Reuse EXP-015 stop, risk, horizon, and primary outcome definitions for filtered and unfiltered sweeps.
- **Why this method**: The experiment isolates the location filter rather than changing the sweep study.
- **Simpler alternative considered**: Re-estimating risk after filtering would introduce a second change.
- **Assumptions**: The comparison is valid only where unfiltered event floors are met.
- **Expected output**: Filtered versus unfiltered outcome table.

### Step 3: Sample-Size Cost and Effect Comparison

- **Method**: Bootstrap differences in primary 60-minute 1R-before-stop probability and median MAE; report retained event percentage before effect interpretation.
- **Why this method**: The scope asks whether improvement is real or just sample-size pruning.
- **Simpler alternative considered**: Reporting only filtered performance would not measure the cost of the filter.
- **Assumptions**: Retained-event percentage is evaluated per instrument/segment.
- **Expected output**: Effect and retention table.

## Visualisations

1. Retained-event percentage by instrument and side.
2. Filtered versus unfiltered primary outcome interval plot.
3. MAE distribution by filter status.

## Interpretation Guide

- Support: filtered sweeps improve the primary outcome by >= 5 percentage points or median MAE by >= 0.25R on at least 3 instruments while meeting retention floors.
- Against: no improvement or excessive event removal.
- Inconclusive: mixed effects or wide intervals.

## Complexity Check

- Statistical tests: 2 / 2
- Visualisations: 3 / 4
- New modules: 1 / 1
