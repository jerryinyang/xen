# Results: Experiment EXP-001-TF

## Summary

The EXP-001 information-density hypothesis was **refuted** when retested on 15-minute and 1-hour source bars. While Line Break and Renko achieved substantial ghost-rate reductions (70-100%) relative to same-timeframe time bars, directional entropy gains were uniformly negative across all instruments and timeframes. No instrument met all three thresholds (ghost reduction ≥25%, headroom capture ≥50%, entropy gain ≥0.005 bits) for any event chart type at either timeframe. The finding that event charts reduce ghost bars replicates, but the claim that they better use directional-entropy headroom does not.

## Detailed Findings

### Ghost Rate Reduction Replicates Strongly

- **Observation**: Event charts have substantially lower ghost rates than same-timeframe time bars across all instruments.
- **Evidence**: Ghost reduction ranges from 70.5% (EURUSD 15m LB3) to 100% (BTCUSD/USTEC 1h Renko). Bootstrap 95% CI for 15m LB3 ghost reduction: [0.742, 0.988], n=4 instruments. Renko ghost reduction bootstrap CI at 1h: [1.0, 1.0] — zero ghost bars across all instruments.
- **Interpretation**: The ghost-reduction component of the EXP-001 hypothesis replicates robustly at higher timeframes. Event charts filter near-zero-movement bars more effectively than time bars.

### Directional Entropy Gains Are Uniformly Negative

- **Observation**: All event charts have lower directional entropy than same-timeframe time bars.
- **Evidence**: Entropy gains range from -0.0124 (XAUUSD 1h LB3) to +0.00025 (EURUSD 15m LB3). Bootstrap 95% CI for 15m LB3 entropy gain: [-0.0058, -0.0010] — entirely negative. For Renko at 1h: [-0.0069, -0.0014].
- **Interpretation**: Event charts produce more directionally homogeneous sequences than time bars. Fewer bars means fewer direction changes, reducing entropy. This contradicts the hypothesis that event charts "better use remaining directional-entropy headroom."

### Headroom Capture Fails Threshold

- **Observation**: No instrument meets the ≥50% headroom capture threshold.
- **Evidence**: Maximum headroom capture is 40.6% (EURUSD 15m LB3). All other values are negative (because entropy decreased rather than increased).
- **Interpretation**: The entropy headroom criterion cannot be met when entropy gains are negative.

### Heiken Ashi Does Not Reduce Bar Count

- **Observation**: HA has identical row counts and ghost rates as time bars at each timeframe.
- **Evidence**: EURUSD 15m: Time = 55,230 rows, HA = 55,230 rows, both ghost rate = 0.0218. HA DirectionalEntropy is marginally higher (0.99960 vs 0.99938) due to HAClose-based direction calculation.
- **Interpretation**: As expected, HA is a 1:1 transformation of time bars and does not reduce bar count. Its slight entropy difference is an artifact of the HA direction formula.

### Distinct-Source Sensitivity

- **Observation**: Renko produces 12-21% duplicate SourceCloseTime rows; Line Break produces 0%.
- **Evidence**: EURUSD 15m Renko: 12.0% duplicate share; USTEC 1h Renko: 20.7%. Line Break has 0% duplicates at all combinations.
- **Interpretation**: Renko's duplicate-source rows are a known artifact of close-based Renko from 1-minute bars. Using distinct-source rows for entropy verdicts (as done in this experiment) correctly avoids counting these duplicates.

## Hypothesis Verdict

**REFUTED**

The hypothesis required Line Break or Renko to meet all three thresholds (ghost reduction ≥25%, headroom capture ≥50%, entropy gain ≥0.005 bits) on at least 3 of 4 instruments. While ghost reduction was achieved (100% of instrument-timeframe combinations exceeded 25%), entropy gains were uniformly negative and headroom capture was below 50% for all combinations. SupportCount = 0/4 for all chart type and timeframe combinations.

The EXP-001 conclusion does not replicate at higher timeframes. Event charts reduce ghost bars but also reduce directional entropy, suggesting they filter noise at the cost of directional information diversity.

## Limitations

- Bootstrap operates on n=4 instrument-level differences, producing wide confidence intervals. CIs are descriptive, not inferential.
- Directional entropy is a simple binary measure (up/down). It does not capture magnitude or duration of trends.
- The analysis uses a single Line Break level (3) and Renko ATR period (14). Different parameters might yield different entropy profiles.
- Ghost bar definition uses an instrument-specific min-tick proxy, which may not perfectly capture "near-zero movement" for all instruments.

## Alternative Explanations

- Event charts may have lower entropy precisely because they filter noise — removing small direction changes that contribute to entropy but carry little information. This is not necessarily a negative finding; it depends on whether the filtered direction changes are signal or noise.
- The entropy metric treats all direction changes equally. A chart type with fewer but more meaningful direction changes could have lower entropy but higher predictive value — this experiment does not test predictive value.

## Recommended Next Steps

1. The timeframe-replication series (EXP-001-TF through EXP-006-TF) should be completed before drawing cross-experiment conclusions.
2. A follow-up experiment could test whether lower entropy in event charts correlates with better signal-to-noise ratio for trend detection, rather than treating entropy reduction as inherently negative.
