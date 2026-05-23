# Analysis Plan: Experiment EXP-013

## Objective

Test H1: whether fixed NY macro windows have different time-bar behavior than adjacent and randomized control windows on the approved analysis set.

## Methodology

### Step 1: Window and Control Construction

- **Method**: Use EXP-012-approved NY timestamps to label fixed macro windows, adjacent equal-duration controls, and 100 fixed-seed randomized same-day controls that do not overlap macro windows.
- **Why this method**: It tests the source hypothesis without optimizing window locations.
- **Simpler alternative considered**: Comparing macro windows only to all non-macro bars would confound time-of-day and session effects.
- **Assumptions**: Random controls are exchangeable only within the same instrument, date, and segment.
- **Expected output**: Window/control count table by instrument and train/test segment.

### Step 2: Primary and Secondary Metric Measurement

- **Method**: Compute primary metric, window true range normalized by ATR_14, plus secondary absolute return, sweep frequency, displacement frequency, and 10/20/60-minute forward returns.
- **Why this method**: The primary metric directly tests volatility/range behavior while secondary metrics preserve the source-spec H1 context.
- **Simpler alternative considered**: Treating all metrics as equal would invite metric shopping.
- **Assumptions**: ATR_14 uses only prior completed bars.
- **Expected output**: Metric summary table by window type, instrument, and segment.

### Step 3: Non-Parametric Comparison

- **Method**: Bootstrap paired differences between macro windows and each control family for the primary metric; secondary metrics are descriptive unless the primary result passes.
- **Why this method**: Bootstrap intervals avoid normality assumptions and keep the statistical budget focused.
- **Simpler alternative considered**: A single p-value across pooled instruments would hide instrument dependence.
- **Assumptions**: Resampling unit is the NY date/window observation, not individual bars.
- **Expected output**: Primary effect sizes and confidence intervals by instrument.

## Visualisations

1. Primary metric distribution by macro versus control family.
2. Instrument-level effect-size interval plot.
3. Macro-window coverage/count plot.
4. Optional secondary metric heatmap if the primary test supports H1.

## Interpretation Guide

- Support: primary metric beats both controls on at least 3 of 4 instruments with CI excluding zero and median effect >= 0.10 ATR.
- Against: primary metric is mixed, near zero, or fails either control on at least 3 instruments.
- Inconclusive: EXP-012 coverage thresholds are not met or intervals are too wide.

## Complexity Check

- Statistical tests: 2 / 2
- Visualisations: 3-4 / 4
- New modules: 1 / 1
