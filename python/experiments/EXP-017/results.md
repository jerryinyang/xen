# Results: Experiment EXP-017

## Summary

EXP-017 does not show evidence that the prior-day midpoint premium/discount filter improves sweep quality enough to justify its sample-size cost. All four instruments retain adequate test-segment coverage, but none clears the predeclared support thresholds on hit rate or median MAE. Because the effects are small and several intervals remain wide, the scoped verdict stays INCONCLUSIVE rather than a clean negative refutation.

## Detailed Findings

### Retention Cost Is Low, So The Result Is Interpretable

- **Observation**: The midpoint filter retains most test-segment sweeps on every instrument.
- **Evidence**: Test retention is EURUSD `84/89` (`94.4%`), XAUUSD `121/131` (`92.4%`), BTCUSD `89/93` (`95.7%`), and USTEC `138/160` (`86.2%`). All four instruments satisfy the scoped event-floor rule.
- **Interpretation**: The experiment is not failing because the filter removes too many events. The verdict is driven by effect quality, not sample collapse.

### Primary Hit-Rate Improvement Is Absent

- **Observation**: No instrument reaches the predeclared `+5pp` test-segment `Hit1R_60m` improvement threshold.
- **Evidence**: Test hit differences (`filtered - all sweeps`) are EURUSD `-0.007`, CI `[-0.029, 0.015]`; XAUUSD `-0.001`, CI `[-0.026, 0.024]`; BTCUSD `-0.014`, CI `[-0.041, 0.008]`; USTEC `-0.036`, CI `[-0.072, -0.004]`.
- **Interpretation**: The midpoint filter does not improve the primary 60-minute 1R-before-stop outcome. On USTEC it is actively harmful on this metric.

### MAE Improvement Signals Are Too Weak And Inconsistent

- **Observation**: BTCUSD and USTEC show small positive median-MAE point estimates, but no instrument clears the scoped `0.25R` threshold with convincing uncertainty bounds.
- **Evidence**: Test median-MAE improvements (`all - filtered`) are EURUSD `-0.086`, CI `[-0.785, 0.640]`; XAUUSD `0.000`, CI `[-0.885, 0.378]`; BTCUSD `0.052`, CI `[-0.073, 0.354]`; USTEC `0.185`, CI `[-0.672, 0.591]`.
- **Interpretation**: The filter may modestly reduce adverse excursion on isolated instruments, but the evidence is too weak and too mixed to support a general location-filter claim.

## Hypothesis Verdict

**INCONCLUSIVE**

The prior-day midpoint premium/discount filter does not support the scoped hypothesis. No instrument reaches the predeclared support threshold on either primary metric, but the evidence is still best described as inconclusive rather than fully against because several intervals remain wide and the small positive MAE hints on BTCUSD and USTEC are not decisively ruled out.

## Limitations

- The experiment inherits outcome definitions from EXP-015, so it evaluates only the midpoint filter and not other location concepts such as VWAP or distance-from-open.
- The analysis uses 1-minute OHLC data only; no tick, bid/ask, spread, commission, or slippage data is available.
- Bootstrap intervals resample events and do not fully model temporal clustering.

## Alternative Explanations

- The midpoint may be too blunt a location filter for this sweep definition; a more selective concept could behave differently, but that would require a new scope.
- The small positive MAE hints on BTCUSD and USTEC may reflect instrument-specific path differences rather than a general premium/discount effect.

## Recommended Next Steps

1. Treat the midpoint filter as not yet justified for Phase 003 decision use.
2. Any follow-up should be a new experiment with one tighter, predeclared location rule rather than adding multiple location filters at once.
