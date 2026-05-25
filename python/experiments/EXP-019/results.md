# Results: Experiment EXP-019

## Summary

EXP-019 shows that the causal micro swing-break definition is reproducible and yields adequate event counts, but it does not provide decisive evidence of better signal quality than the simpler EXP-018 displacement baseline. All four instruments meet the test-segment event floor, and none is disqualified by excessive median delay, yet no instrument clears the predeclared interval-based return or MAE thresholds. The verdict is INCONCLUSIVE.

## Detailed Findings

### The Definition Is Usable And Not Excessively Slow

- **Observation**: Swing-break events are numerous enough to evaluate on all four instruments, and median confirmation delay stays below the scoped failure threshold.
- **Evidence**: Test matched counts are EURUSD `77`, XAUUSD `112`, BTCUSD `81`, and USTEC `132`, all above the `>= 50` floor. The summary flags excessive delay on `0/4` instruments.
- **Interpretation**: The experiment is not failing because the causal swing definition is too sparse or too delayed.

### Return Improvement Is Not Established

- **Observation**: Test-segment return differences versus EXP-018 displacement are noisy and do not clear the predeclared `0.25R` improvement threshold with CI support.
- **Evidence**: Test mean return differences are EURUSD `+0.252`, CI `[-7.542, 7.186]`; XAUUSD `+0.630`, CI `[-16.675, 16.508]`; BTCUSD `+1.477`, CI `[-4.050, 9.390]`; USTEC `+18.153`, CI `[-4.762, 58.643]`.
- **Interpretation**: The point estimates are unstable relative to their uncertainty, so the return side of the hypothesis is not supported.

### MAE Improvement Hints Exist But Are Not Strong Enough

- **Observation**: XAUUSD and USTEC show positive test-segment MAE point estimates versus EXP-018 displacement, but not with enough interval strength to pass.
- **Evidence**: Test median-MAE improvements are EURUSD `+0.114`, CI `[-0.097, 0.276]`; XAUUSD `+0.404`, CI `[0.022, 0.642]`; BTCUSD `+0.157`, CI `[0.000, 0.471]`; USTEC `+0.597`, CI `[0.186, 1.076]`. None has `CI95-low >= 0.25R`.
- **Interpretation**: The swing-break variant may reduce adverse excursion on some instruments, but the evidence is still too weak to justify calling it better than EXP-018.

### Audit Caveat Does Not Change The Verdict

- **Observation**: One BTCUSD confirmed event crosses the train/test boundary and is grouped under the sweep segment rather than the break segment.
- **Evidence**: `swing_break_detection.csv` contains one confirmed BTCUSD row with `Segment=Train`, `BreakSegment=Test`, `SweepTime=2024-10-31 13:50:00`, and `BreakTime=2024-10-31 14:38:00`. The audit shows only trivial changes to BTCUSD direct point estimates if that pair is relabeled.
- **Interpretation**: This is a bookkeeping caveat, not a trust-breaking error. The overall verdict remains INCONCLUSIVE.

## Hypothesis Verdict

**INCONCLUSIVE**

The micro swing-break confirmation does not beat the EXP-018 displacement baseline on the predeclared interval-based criteria, but it is not refuted either because event counts are adequate, delays are acceptable, and some MAE signals remain directionally positive. The current evidence is not strong enough to treat the swing-break variant as a validated improvement.

## Limitations

- The comparison is only against the completed EXP-018 displacement-close baseline; it does not revisit sweep-only or combine both confirmation rules.
- The analysis uses 1-minute OHLC data only; no tick or execution-cost data is available.
- One confirmed cross-segment case is grouped by sweep segment in the generated tables, though the measured effect on the verdict is immaterial.

## Alternative Explanations

- Swing-break confirmation may help mainly on selected regimes or instruments, but this scope intentionally avoided post-hoc segmentation.
- The longer confirmation path may improve MAE on some trades while still being too inconsistent on realized return to support general deployment.

## Recommended Next Steps

1. Consolidate EXP-018 and EXP-019 as a joint H3 assessment before adding any new confirmation layer.
2. If an H3 follow-up is opened, scope it as a single tighter rule or a clearly predeclared regime restriction rather than combining multiple confirmation concepts.
