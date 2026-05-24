# Results: Experiment EXP-013

## Summary

The predefined NY macro windows do not show the required ATR-normalized range advantage over both adjacent and randomized controls. No instrument passes the primary criterion in both train and test, so H1 is refuted under the approved scope.

## Detailed Findings

### Primary Criterion Fails on All Instruments

- **Observation**: `primary_effects.csv` reports `SupportsPrimaryCriterion=False` for every instrument, segment, and control family.
- **Evidence**: The support summary reports `0/4` supporting instruments.
- **Interpretation**: Fixed macro windows do not produce the predeclared practical and statistically supported range difference required for H1.

### Macro Windows Often Have Lower ATR-Normalized Range Than Controls

- **Observation**: Most primary mean differences are negative.
- **Evidence**:
  - BTCUSD test vs AdjacentMean: mean `-0.3547`, CI `[-0.5434, -0.1621]`
  - BTCUSD test vs RandomControl: mean `-0.3804`, CI `[-0.5853, -0.1745]`
  - USTEC train vs RandomControl: mean `-0.7439`, CI `[-0.9031, -0.5853]`
  - XAUUSD train vs RandomControl: mean `-0.5790`, CI `[-0.7270, -0.4380]`
- **Interpretation**: The dominant pattern contradicts a simple macro-window range expansion claim.

### EURUSD Has Some Positive Medians But Not Enough Evidence

- **Observation**: EURUSD test has positive median differences against both controls, but intervals do not exclude zero.
- **Evidence**:
  - EURUSD test vs AdjacentMean: median `0.1075`, mean CI `[-0.0727, 0.4136]`
  - EURUSD test vs RandomControl: median `0.1902`, mean CI `[-0.3375, 0.1726]`
- **Interpretation**: EURUSD does not meet the support rule because the uncertainty intervals include zero and train/test consistency is absent.

### Secondary Sweep Frequency Is Zero Under This Definition

- **Observation**: Macro-window `SweepOccurred` means are `0.0` for all instruments in train and test.
- **Evidence**: `metric_summary.csv` and spot checks on `window_observations.csv`.
- **Interpretation**: This does not decide H1, but it suggests the window-level reclaim sweep definition is strict and should be revisited only in a separately scoped sweep study.

## Hypothesis Verdict

**REFUTED**

The success criterion required the primary metric to differ from both adjacent and randomized controls on at least 3 of 4 instruments, with bootstrap confidence intervals excluding zero and median effect at least `0.10 ATR`. The rerun produces zero supporting instruments.

## Limitations

- Random controls are session-bounded but not matched to each macro-window family or exact time neighborhood.
- Secondary sweep and displacement metrics are descriptive only and do not rescue a failed primary H1 result.
- This experiment characterizes fixed macro windows; it does not optimize or test alternative windows.

## Recommended Next Steps

1. Continue to EXP-015 because the phase design requires direct sweep behavior characterization independent of H1.
2. Do not use fixed macro windows as a standalone range-expansion filter unless a future experiment scopes a different control design.
