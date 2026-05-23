# Analysis Plan: Experiment EXP-016

## Objective

Determine whether EXP-015 sweep outcomes differ inside fixed NY macro windows versus outside those windows, without adding confirmation filters.

## Methodology

### Step 1: Macro Labeling of Sweep Events

- **Method**: Join EXP-015 sweep events to EXP-012 macro-window labels by event `CloseTime` in New York time.
- **Why this method**: It directly tests the H1/H2 interaction while preserving sweep definitions.
- **Simpler alternative considered**: Recomputing sweeps differently inside macro windows would confound the interaction.
- **Assumptions**: Macro membership is knowable at event close.
- **Expected output**: Inside/outside sweep counts by instrument, side, and segment.

### Step 2: Matched Outside-Window Baseline

- **Method**: Compare inside-window sweeps to outside-window sweeps matched by instrument, side, segment, and NY date where possible; unmatched outside sweeps remain in a sensitivity summary.
- **Why this method**: Matching reduces session and date-level confounding.
- **Simpler alternative considered**: All outside-window sweeps are a noisy control because sweep behavior can vary by date.
- **Assumptions**: Matching may reduce sample size and must be reported before interpretation.
- **Expected output**: Matched and unmatched baseline tables.

### Step 3: Primary Outcome Comparison

- **Method**: Bootstrap the difference in EXP-015's 60-minute 1R-before-stop probability and median MAE between inside and matched outside sweeps.
- **Why this method**: The scoped thresholds are effect-size based and non-parametric.
- **Simpler alternative considered**: Testing macro-window returns again would duplicate EXP-013 instead of testing sweep interaction.
- **Assumptions**: Event dependence within a day is acknowledged by date-level sensitivity summaries.
- **Expected output**: Effect-size intervals by instrument and segment.

## Visualisations

1. Inside versus outside sweep counts by instrument.
2. Primary effect-size interval plot.
3. MAE distribution by macro membership.
4. Optional per-window count heatmap.

## Interpretation Guide

- Support: inside-macro sweeps improve the primary outcome by >= 5 percentage points or median MAE by >= 0.25R on at least 3 instruments with event floors met.
- Against: macro filtering adds no improvement or mostly removes sample.
- Inconclusive: inside-window sweep counts are below floor.

## Complexity Check

- Statistical tests: 2 / 2
- Visualisations: 3-4 / 4
- New modules: 1 / 1
