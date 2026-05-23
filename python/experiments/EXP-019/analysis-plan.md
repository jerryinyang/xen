# Analysis Plan: Experiment EXP-019

## Objective

Test whether a causally confirmed micro swing break after a sweep improves signal quality beyond the EXP-018 candle/body displacement variant.

## Methodology

### Step 1: Causal Swing Confirmation

- **Method**: Identify swing highs/lows with two bars on each side, but assign the usable swing timestamp to the right-side confirmation bar; only swings confirmed before the break bar may be used.
- **Why this method**: It avoids look-ahead while preserving the scoped swing definition.
- **Simpler alternative considered**: Using pivot timestamps directly would use future bars at the event time.
- **Assumptions**: Confirmation delay is part of the signal and must be measured.
- **Expected output**: Confirmed-swing table with pivot time, usable time, and break time.

### Step 2: Post-Sweep Break Detection

- **Method**: After each EXP-015 failed sweep, detect bearish closes below the most recent usable confirmed swing low or bullish closes above the most recent usable confirmed swing high.
- **Why this method**: It isolates the swing-break variant from EXP-018's candle/body displacement.
- **Simpler alternative considered**: Combining both displacement definitions would conflate H3 variants.
- **Assumptions**: A sweep can produce at most one first qualifying swing-break event per side for this study.
- **Expected output**: Swing-break event table and unconfirmed-sweep reason counts.

### Step 3: Comparison to EXP-018 Baseline

- **Method**: Compare swing-break outcomes to the EXP-018 displacement baseline using the same stop/risk, entry proxy, and 60-minute primary outcome definitions.
- **Why this method**: The question is whether the swing-break variant adds value beyond simpler displacement.
- **Simpler alternative considered**: Comparing only to sweep-only would duplicate EXP-018.
- **Assumptions**: Baseline choice is fixed before execution.
- **Expected output**: Effect-size table for swing-break versus candle/body displacement.

## Visualisations

1. Swing confirmation delay distribution.
2. Event count comparison: sweep-only, EXP-018 displacement, swing-break.
3. Primary outcome interval plot by displacement variant.
4. MAE distribution by variant.

## Interpretation Guide

- Support: swing-break improves the primary outcome by >= 0.25R or materially lowers MAE on at least 3 instruments without look-ahead or sparse counts.
- Against: no improvement, excessive delay, or sparse events.
- Inconclusive: reproducible definition but conflicting instrument effects.

## Complexity Check

- Statistical tests: 2-3 / 3
- Visualisations: 4 / 5
- New modules: 2 / 2
