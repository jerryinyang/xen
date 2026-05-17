# Results: Experiment EXP-005-TF

## Summary

The EXP-005 cross-chart agreement hypothesis was **refuted** when retested on 15-minute and 1-hour source bars. While Line Break and Renko show perfect direction agreement (100%) when their events align within a 5-minute tolerance window, the agreement improvement over each chart type's agreement with time bars is only 1-2 percentage points — far below the ≥10pp threshold required by the hypothesis. Both LB and Renko agree with time bars at 97-99%, meaning event charts preserve the underlying trend direction almost perfectly. The overlap rate between LB and Renko is only ~50% at 5-minute tolerance, meaning half of LB events do not have a Renko counterpart within the window.

## Detailed Findings

### LB<->Renko Agreement Is Perfect on Matched Events

- **Observation**: When Line Break and Renko events align within 5 minutes, they always agree on direction.
- **Evidence**: Agreement = 1.0 for all 8 instrument-timeframe combinations at 5-min tolerance. At 15-min tolerance, agreement remains near-perfect (0.987-0.991).
- **Interpretation**: Event charts capture the same trend direction when they emit events at similar times. This is a strong confirmation of directional consistency between LB and Renko.

### But Overlap Is Only ~50%

- **Observation**: Only about half of LB events find a Renko match within 5 minutes.
- **Evidence**: OverlapRate at 5-min tolerance: 0.495-0.531 across instruments/timeframes. At 15-min tolerance: 0.728-0.769. This means ~50% of LB events have no Renko counterpart within 5 minutes, and ~25% have no counterpart within 15 minutes.
- **Interpretation**: LB and Renko have different event densities and timing. While they agree when they overlap, the overlap itself is limited. This reduces the practical utility of the perfect agreement — it applies to only half of LB events.

### LB<->Time and Renko<->Time Agreement Is Very High

- **Observation**: Both event charts agree with time bars at 97-99%.
- **Evidence**: LB<->Time agreement at 5-min: 0.981-0.991. Renko<->Time agreement at 5-min: 0.977-0.993. These are near-perfect agreement rates.
- **Interpretation**: Event charts preserve the underlying trend direction almost perfectly. The small disagreement (1-3%) likely occurs at trend inflection points where the event chart's direction change lags or leads the time bar's direction change.

### Agreement Improvement Is Only 1-2pp, Not ≥10pp

- **Observation**: LB<->Renko agreement exceeds LB<->Time and Renko<->Time agreement by only 1-2 percentage points.
- **Evidence**: At 5-min tolerance, 15m timeframe: LB<->Renko = 1.0, LB<->Time = 0.986-0.991, Renko<->Time = 0.977-0.993. Improvement = 0.9-2.3pp. Bootstrap 95% CI for LB_Renko_minus_LB_Time at 15m 5-min: [0.008, 0.015] — statistically significant but practically small.
- **Interpretation**: The hypothesis expected LB/Renko to agree with each other substantially more than either agrees with time bars (≥10pp). The actual improvement is 1-2pp, which is statistically significant (CI excludes zero) but practically negligible. Event charts agree with time bars almost as well as they agree with each other.

### Time<->HA Agreement Is ~65%

- **Observation**: HA direction differs from time bar direction ~35% of the time.
- **Evidence**: Time<->HA agreement at 5-min: 0.636-0.661 across all instruments/timeframes. Consistent across regimes.
- **Interpretation**: HA's smoothing formula produces different direction signals than raw OHLC about one-third of the time. This is expected — HA's direction is based on HAClose vs HAOpen, which incorporates previous candle values and can differ from the current bar's Close vs Open.

### Regime Stratification Shows Consistent Patterns

- **Observation**: Agreement patterns are consistent across low, medium, and high volatility regimes.
- **Evidence**: LB<->Renko agreement = 1.0 in all regimes. LB<->Time agreement: 0.967-0.997 across regimes. Renko<->Time agreement: 0.969-1.0 across regimes. No regime shows materially different patterns.
- **Interpretation**: The agreement patterns are not regime-dependent. Event charts preserve trend direction consistently regardless of volatility level.

### Tolerance Sensitivity

- **Observation**: Increasing tolerance from 5 to 15 minutes increases overlap but does not materially change agreement rankings.
- **Evidence**: At 15-min tolerance, LB<->Renko overlap increases from ~50% to ~73-77%, but agreement drops slightly to 0.987-0.991 (from 1.0). LB<->Time and Renko<->Time agreement remain unchanged (exact timestamp match).
- **Interpretation**: The 5-min primary tolerance is appropriate. The 15-min sensitivity confirms that the agreement ranking is robust to tolerance choice.

## Hypothesis Verdict

**REFUTED**

The hypothesis required LB/Renko timestamp-aligned agreement to be ≥10pp higher than each chart type's agreement with time bars in medium/high regimes on ≥3 instruments, with bootstrap CIs excluding zero. The agreement improvement is only 1-2pp (far below 10pp), though the bootstrap CI at 5-min tolerance does exclude zero (statistically significant but practically small). At 15-min tolerance, the CI includes zero for the 15m timeframe.

The EXP-005 finding does not replicate at higher timeframes. Event charts agree with each other and with time bars at near-identical rates (97-100%), suggesting that trend direction is robustly captured by all chart types, not just event charts.

## Limitations

- Nearest-neighbor matching within a tolerance window may pair events that are not truly corresponding. A 5-minute window at 15m resolution is 1/3 of a bar width.
- Overlap rate of ~50% means the perfect LB<->Renko agreement applies to only half of LB events. The interpretation should not generalize to all LB or Renko events.
- Bootstrap operates on n=8 (4 instruments × 2 regimes), treating each combination as independent despite temporal dependence within instruments.
- Direction agreement is a binary measure (+1/-1). It does not capture the magnitude or timing of direction changes.

## Alternative Explanations

- The high agreement between all chart types (97-100%) suggests that trend direction is a robust property of price data, not specific to any chart type. All chart types capture the same underlying trend, just at different resolutions.
- The 1-2pp agreement advantage of LB<->Renko over LB<->Time may reflect that event charts filter out minor direction changes that time bars capture, making their remaining direction changes more aligned with each other.

## Recommended Next Steps

1. Complete the timeframe-replication series before drawing cross-experiment conclusions.
2. A follow-up experiment could test whether event charts' direction changes are more predictive of future price movement than time bar direction changes, rather than just measuring agreement.
3. Consider testing agreement at the 1-minute timeframe to compare with the original EXP-005 results.
