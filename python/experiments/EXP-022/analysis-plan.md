# Analysis Plan: Experiment EXP-022

## Objective

Determine which objective breaker candidate is reproducible enough for later H5 outcome testing.

## Methodology

### Step 1: Candidate A Order-Block Proxy Definition Check

- **Method**: After each eligible sweep plus displacement event, identify the last opposite-direction candle before displacement, store its high/low zone, and confirm a breaker on a later close through the relevant boundary.
- **Why this method**: It implements the planning spec's failed order-block proxy in a deterministic way.
- **Simpler alternative considered**: Manual order-block labels are not reproducible.
- **Assumptions**: The last opposite candle is selected using only bars before displacement close.
- **Expected output**: Candidate A boundary and confirmation table.

### Step 2: Candidate B Swing-Structure Break Check

- **Method**: Use the causal swing logic from EXP-019 to identify prior swing highs/lows and confirm a breaker on close through the relevant prior swing.
- **Why this method**: The planning spec says this candidate is easier to reproduce and should be tested separately.
- **Simpler alternative considered**: Treating all structure breaks as breakers would be too broad.
- **Assumptions**: Swing timestamps are usable only after confirmation.
- **Expected output**: Candidate B boundary and confirmation table.

### Step 3: Reproducibility and Selection for EXP-023

- **Method**: Compare deterministic rerun equality, ambiguity rates, duplicate handling, invalidation clarity, and occurrence counts. Select at most one candidate for EXP-023 using predeclared reproducibility and count criteria, not profitability.
- **Why this method**: EXP-023 must not choose a breaker based on outcome performance.
- **Simpler alternative considered**: Testing both profitability variants in EXP-023 would conflate definition validation and H5.
- **Assumptions**: Counts, not expectancy, decide eligibility here.
- **Expected output**: Breaker candidate selection table.

## Visualisations

1. Candidate occurrence counts by instrument and segment.
2. Ambiguity/invalidation reason counts.
3. Confirmation-delay distribution by candidate.

## Interpretation Guide

- Support: one candidate has deterministic boundaries, clear invalidation, and occurrence floors on at least 3 instruments.
- Against: candidates are ambiguous, discretionary, or sparse.
- Inconclusive: a candidate works only for a subset of instruments.

## Complexity Check

- Statistical tests: 0 / 0-1
- Visualisations: 3 / 4
- New modules: 1 / 1
