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

- **Method**: Compare swing-break outcomes to the EXP-018 displacement baseline using the same stop/risk, entry proxy, and 60-minute primary outcome definitions. Return is compared using a paired *mean* bootstrap; MAE is compared using a paired *median* bootstrap (the scope criterion is stated on the median).
- **Why this method**: The question is whether the swing-break variant adds value beyond simpler displacement.
- **Criterion form**: A metric passes only when its bootstrap CI95-low clears the predeclared threshold (Return: 0.25R; median MAE improvement: 0.25R). A metric refutes when CI95-high is strictly below the threshold. Point estimates alone are insufficient. The retention floor is keyed off `MatchedN` — the actual sample feeding the bootstrap — not the raw swing-break count.
- **Cross-segment behaviour**: Usable swings from Train may confirm a Test break (and vice versa), matching production behaviour. The break event's segment is the break candle's segment; cross-segment cases are flagged.
- **Simpler alternative considered**: Comparing only to sweep-only would duplicate EXP-018.
- **Expected output**: Effect-size table with `MatchedN`, point estimate, CI95, and `*CriterionMet` / `*Refutes` flags per instrument/segment.

## Visualisations

1. Swing confirmation delay distribution.
2. Event count comparison: sweep-only, EXP-018 displacement, swing-break.
3. Primary outcome interval plot by displacement variant.
4. MAE distribution by variant.

## Interpretation Guide

- Support: swing-break improves 60-minute expectancy by >= 0.25R or lowers median 60-minute MAE by >= 0.25R on at least 3 instruments, with >= 50 confirmed swing-break events per train/test segment.
- Against: no improvement, median confirmation delay > 60 bars on at least 3 instruments, or < 50 confirmed swing-break events in train or test on at least 3 instruments.
- Inconclusive: reproducible definition but conflicting instrument effects.

## Complexity Check

- Statistical tests: 2-3 / 3
- Visualisations: 4 / 5
- New modules: 2 / 2
