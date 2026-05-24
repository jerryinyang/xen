# Analysis Plan: Experiment EXP-014

## Objective

Verify that PDH/PDL and ONH/ONL liquidity levels can be computed reproducibly from approved time bars before sweep studies use them.

## Methodology

### Step 1: Eligible Date Construction

- **Method**: Use EXP-012-approved NY conversion to group bars by NY date, exclude the global holdout, and identify weekday dates with enough prior observed weekday and overnight bars to compute levels.
- **Why this method**: Liquidity levels must be defined before event outcomes are inspected.
- **Simpler alternative considered**: Using calendar days without coverage checks would silently create unreliable levels.
- **Assumptions**: Available bars represent the observed session; missing bars are classified rather than imputed.
- **Expected output**: Eligible-date and missing-reason table.

### Step 2: Level Computation and Reproducibility Checks

- **Method**: Compute PDH/PDL from the prior observed weekday NY date and ONH/ONL from 17:00 NY on the prior calendar date through 09:30 NY on the event date using CloseTimeNY boundary membership; rerun the computation to confirm deterministic equality.
- **Why this method**: It preserves the planning spec's initial liquidity levels and avoids unsupported swing/equal-high assumptions.
- **Simpler alternative considered**: Adding swing levels now would exceed the H2 prerequisite scope.
- **Assumptions**: Session caveats are acceptable only when documented by instrument.
- **Expected output**: Level table with availability, value ranges, and deterministic rerun check.

### Step 3: Readiness Classification

- **Method**: Compare level availability against the scoped >= 80 percent eligible-date and >= 50 date-per-segment thresholds.
- **Why this method**: Later sweep studies need enough observations in both train and test.
- **Simpler alternative considered**: A binary "levels exist" check does not measure sample adequacy.
- **Assumptions**: Counts are assessed per instrument and segment.
- **Expected output**: Reproducibility verdict by instrument.

## Visualisations

1. Level availability by instrument and train/test segment.
2. Missing-level reason counts.
3. Optional PDH/PDL/ONH/ONL timeline for diagnostic anomalies.

## Interpretation Guide

- Support: all usable instruments meet level availability and count thresholds with deterministic rerun equality.
- Against: definitions depend on unsupported calendars or produce sparse/ambiguous levels.
- Inconclusive: continuous instruments pass but session-bound instruments fail coverage.

## Complexity Check

- Statistical tests: 0 / 0-1
- Visualisations: 2-3 / 4
- New modules: 1 / 1
