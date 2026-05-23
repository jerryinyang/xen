# Analysis Plan: Experiment EXP-021

## Objective

Test H4: whether IFVG confirmation improves entry quality enough to offset later entry timing and fewer signals.

## Methodology

### Step 1: Eligible Event Chain Construction

- **Method**: Build chains from EXP-015 sweeps, the preselected displacement prerequisite from EXP-018 or EXP-019, and EXP-020 IFVG rules. Record where each chain drops out.
- **Why this method**: H4 must be evaluated only after sweep, displacement, and IFVG definitions are deterministic.
- **Simpler alternative considered**: Testing all FVGs without sweep context would not answer the ICT setup question.
- **Assumptions**: The displacement prerequisite is fixed in config before outcomes are inspected.
- **Expected output**: Event-chain waterfall and eligibility table.

### Step 2: Fixed Entry Timestamp Comparison

- **Method**: For each eligible chain, compute outcomes for sweep rejection close, displacement confirmation close, IFVG close, and second-candle-open after IFVG close. Include retest only if a deterministic rule was frozen before execution.
- **Why this method**: It tests whether IFVG timing improves entry quality rather than only reducing samples.
- **Simpler alternative considered**: Comparing IFVG entries to no baseline would not test improvement.
- **Assumptions**: All entries use the same stop/risk convention except where IFVG zone stop is explicitly the scoped stop.
- **Expected output**: Entry-timing outcome table.

### Step 3: IFVG Versus Simpler Entries

- **Method**: Bootstrap differences in expectancy in R, drawdown proxy, MAE, and 1R/2R-before-stop probabilities for IFVG entries versus the simpler baseline entries.
- **Why this method**: H4 is about entry quality after delayed confirmation.
- **Simpler alternative considered**: Win rate alone can improve by discarding hard cases.
- **Assumptions**: Event counts are reported before interpreting expectancy.
- **Expected output**: IFVG contribution table by instrument and segment.

## Visualisations

1. Chain-count waterfall from sweep to IFVG entry.
2. Entry-timing expectancy interval plot.
3. Entry risk-distance distribution.
4. MFE/MAE distribution by entry timestamp.

## Interpretation Guide

- Support: IFVG-confirmed entries improve expectancy or drawdown-adjusted return on at least 3 instruments with >= 50 IFVG-confirmed events per train/test segment.
- Against: later entries degrade R distribution or sample size dominates.
- Inconclusive: too few IFVG confirmations after prerequisites.

## Complexity Check

- Statistical tests: 2-3 / 3
- Visualisations: 4 / 5
- New modules: 2 / 2
