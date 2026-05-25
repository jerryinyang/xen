# Results: Experiment EXP-018

## Summary

EXP-018 does not show decisive evidence that adding a deterministic displacement confirmation improves sweep-only outcomes. All four instruments retain adequate confirmed-event counts in the test segment, but none clears the predeclared interval-based support thresholds against the full EXP-015 sweep baseline. The result remains INCONCLUSIVE because the point estimates are sometimes positive while the uncertainty bounds stay wide, and the paired delay-cost diagnostic is often negative.

## Detailed Findings

### Confirmation Retains Most Sweeps

- **Observation**: The displacement rule keeps a large majority of test-segment sweeps on every instrument.
- **Evidence**: Test confirmed-sweep counts are EURUSD `77/89` (`86.5%`), XAUUSD `112/131` (`85.5%`), BTCUSD `81/93` (`87.1%`), and USTEC `132/160` (`82.5%`). All four meet the scoped event floor.
- **Interpretation**: The experiment is not underpowered because of confirmation scarcity. The open question is whether the retained subset is meaningfully better.

### Confirmed-Sweep Outcomes Improve Only Marginally

- **Observation**: Test-segment point estimates versus the full EXP-015 sweep population are mostly positive, but none is strong enough to clear the scoped thresholds with CI support.
- **Evidence**: Test hit-rate differences (`confirmed - all sweeps`) are EURUSD `+0.023`, XAUUSD `+0.024`, BTCUSD `+0.027`, and USTEC `+0.001`, with all 95% intervals crossing the `+0.05` threshold. Test median-MAE improvements are EURUSD `+0.405`, XAUUSD `+0.345`, BTCUSD `+0.052`, and USTEC `+0.404`, but every 95% interval still includes values below the `0.25R` pass bar.
- **Interpretation**: Displacement confirmation may prune toward slightly better sweeps, but the evidence is too uncertain to claim a reliable improvement.

### Waiting For Confirmation Often Carries A Delay Cost

- **Observation**: On the matched confirmed-event subset, waiting for displacement often worsens realized return and hit probability versus entering at sweep close.
- **Evidence**: EURUSD Test paired `DisplacementClose - SweepClose` hit difference is `-0.159`, CI `[-0.304, -0.014]`; XAUUSD Test is `-0.140`, CI `[-0.269, -0.011]`. Return differences are also negative on EURUSD, XAUUSD, and USTEC, though with wider intervals.
- **Interpretation**: Even if the confirmed subset looks slightly cleaner than the full sweep population, the act of waiting for confirmation can consume much of the candidate edge.

## Hypothesis Verdict

**INCONCLUSIVE**

The displacement rule does not clear the predeclared support bar on any test instrument, but it is not cleanly refuted either because the confidence intervals remain broad and some MAE point estimates are directionally positive. The evidence does not justify promoting this confirmation step as a robust improvement over sweep-only behavior.

## Limitations

- The analysis uses one scoped displacement definition only; it does not test alternative body multipliers, windows, or close-location rules.
- Outcomes are measured on 1-minute OHLC prices only; no transaction-cost data is available.
- One raw `NextOpen` row has zero risk and is excluded from effect calculations, though it does not affect the verdict.

## Alternative Explanations

- Displacement may be identifying higher-quality setups, but the gain could be too small relative to the entry delay to show a clear advantage under this risk convention.
- The effect may depend on regime or instrument-specific structure that this scope intentionally did not segment.

## Recommended Next Steps

1. Compare this result directly with the completed EXP-019 swing-break variant before opening any new H3 confirmation scope.
2. If a follow-up is created, test exactly one stricter confirmation rule with predeclared regime or instrument limits rather than stacking extra filters.
