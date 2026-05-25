# Analysis Plan: Experiment EXP-018

## Objective

Test H3 using one deterministic candle/body displacement definition after EXP-015 failed sweeps.

## Methodology

### Step 1: Displacement Detection

- **Method**: For each EXP-015 failed sweep, search the next 10 bars for a directional candle whose body is >= 1.5 times the rolling median absolute body over the prior 100 completed bars and whose close is in the directional quartile.
- **Why this method**: It follows the planning spec's recommended initial displacement parameters without adding swing-break logic.
- **Simpler alternative considered**: Visual displacement labels are not reproducible.
- **Assumptions**: Rolling median and close-location values use only bars known by the displacement close.
- **Expected output**: Displacement-confirmed event table and missed-sweep table.

### Step 2: Entry Proxy and Outcome Measurement

- **Method**: Compare sweep-close entry proxy, displacement-close entry proxy, and next-open after displacement using EXP-015 stop/risk conventions and 60-minute outcomes from each entry timestamp.
- **Why this method**: It tests whether waiting for displacement improves or delays the signal.
- **Simpler alternative considered**: Only counting displacement frequency would not test H3's expectancy claim.
- **Assumptions**: Events without enough forward bars are excluded with reason codes.
- **Expected output**: Outcome table by entry proxy and instrument.

### Step 3: Sweep-Only Versus Displacement Comparison (PRIMARY)

- **Method**: Nested-subset bootstrap on the FULL EXP-015 sweep population: compute mean Hit1R_60m and median MAE_R_60m on (a) all sweeps and (b) the displacement-confirmed subset. Each bootstrap resample draws from the full baseline and recomputes the confirmed-subset statistic inside the resample, preserving the subset/superset dependence. Report retained-event percentage first.
- **Why this method**: The scope asks whether *adding* displacement improves outcomes versus sweep-only. That requires comparing the confirmed-sweep outcome distribution against the full sweep population, not against the same confirmed events entered at sweep close.
- **Criterion form**: Bootstrap CI95-low must clear the predeclared threshold (Hit1R: 0.05; median MAE improvement: 0.25R) before `*CriterionMet` is True. CI95-high below the threshold counts as refutation on that metric. Point estimates alone are insufficient.
- **Secondary diagnostic**: A paired DisplacementClose-vs-SweepClose bootstrap on the same displacement-confirmed events is retained as a delay-cost diagnostic. It does NOT drive the verdict.
- **Expected output**: `filter_effects.csv` (primary), `primary_effects.csv` (paired delay-cost diagnostic), and a count table.

## Visualisations

1. Sweep-to-displacement count waterfall.
2. Entry proxy expectancy interval plot.
3. MFE/MAE distribution for sweep-only versus displacement-confirmed events.
4. Delay distribution from sweep to displacement.

## Interpretation Guide

- Support: displacement improves 60-minute expectancy by >= 0.05R or 1R-before-stop probability by >= 5 percentage points on at least 3 instruments with event floors met.
- Against: entries are delayed without quality improvement or samples collapse.
- Inconclusive: train improvement does not persist in test.

## Complexity Check

- Statistical tests: 2-3 / 3
- Visualisations: 4 / 5
- New modules: 2 / 2
