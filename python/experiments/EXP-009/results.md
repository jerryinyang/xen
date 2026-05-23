# Results: Experiment EXP-009

## Summary

EXP-009 refutes the hypothesis that 15-minute Heiken Ashi direction changes select a better AE-relative-to-FE subset than raw 15-minute time-bar direction changes. HA cuts the direction-change count roughly in half, but the primary log FE/AE comparison does not improve on any instrument with a CI excluding zero.

## Detailed Findings

### HA Reduces Signal Count Without Primary Quality Improvement

- **Observation**: HA direction changes are `47.7-49.3%` of time-bar direction-change counts.
- **Evidence**: HA/time count ratios are EURUSD `0.493`, XAUUSD `0.484`, BTCUSD `0.492`, and USTEC `0.477`.
- **Interpretation**: HA smoothing is a strong coverage filter at 15 minutes, but the filter does not produce the pre-specified AE/FE improvement.

### Log FE/AE Does Not Improve

- **Observation**: HA minus time-bar log FE/AE differences do not exclude zero on any instrument.
- **Evidence**: Mean differences are BTCUSD `-0.040`, EURUSD `-0.017`, USTEC `+0.013`, and XAUUSD `+0.012`; all bootstrap CIs include zero.
- **Interpretation**: The central hypothesis fails. HA does not provide a reliable AE-relative-to-FE advantage over raw time-bar direction changes.

### FE60/AE60 Components Are Mixed

- **Observation**: FE60 and AE60 component effects are small and inconsistent.
- **Evidence**: Only XAUUSD FE60 is significantly positive (`+0.034`, CI `[+0.019, +0.397]`). AE60 has no instrument with a CI excluding zero.
- **Interpretation**: Any apparent ratio movement would not be backed by a coherent favourable/adverse excursion pattern.

### Coverage-Adjusted Outcomes Do Not Rescue the Hypothesis

- **Observation**: Coverage-adjusted FE60 and AE60 are necessarily much smaller than full time-bar reference means because HA selects only about half the reference events.
- **Evidence**: Coverage by regime ranges from `0.436` to `0.534`.
- **Interpretation**: The missing-signal cost dominates; HA is not a standalone 15-minute signal generator under the approved criteria.

## Hypothesis Verdict

**REFUTED**

The hypothesis required log FE/AE improvement on at least 3 of 4 instruments with CIs excluding zero and supporting FE60/AE60 component evidence. It achieved 0 of 4 on the primary log FE/AE criterion.

## Limitations

- The result applies only to 15-minute HA direction changes, as scoped.
- HA construction prices were not evaluated as returns, by design.
- Extreme FE/AE outliers exist, so distributional interpretation should stay anchored to the pre-specified bootstrap comparisons.

## Alternative Explanations

- HA may be useful as a smoothing feature inside a larger time-bar-native filter, but it is not supported here as a standalone direction-change signal generator.
- The stronger-than-expected signal-count reduction suggests HA delay/filtering is substantial, but it appears to remove favourable and adverse opportunities together.

## Recommended Next Steps

1. Treat HA as a candidate feature in a future time-bar-native filter experiment, not as an independent signal source.
2. Keep FE60 and AE60 separate in future HA work; the log ratio alone is not supported as a sufficient diagnostic.
