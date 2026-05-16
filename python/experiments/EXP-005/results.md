# Results: Experiment EXP-005

## Summary

Line Break and Renko show high raw pairwise direction agreement (~90%) across all four instruments, but paired bootstrap confidence intervals — the pre-specified statistical test — reveal that this advantage does not hold when comparing the same reference events against both targets. On the paired subset, Line Break agrees with Time Bars slightly more than with Renko (diff ≈ -0.7 to -3.2 pp, all CIs excluding zero), and Renko agrees with Time Bars substantially more than with Line Break (diff ≈ -13 to -15 pp). The hypothesis is **REFUTED**.

## Detailed Findings

### 1. Raw pairwise agreement: LB↔Renko is highest across all instruments

- **Observation**: At 5m tolerance, LB↔Renko agreement ranges from 90.1% to 90.5% across instruments, exceeding both LB↔TimeBars (78.3-79.4%) and Renko↔TimeBars (80.7-81.7%).
- **Evidence**: `pairwise_metrics.csv`, `plots/agreement_heatmap.png`. EURUSD: 0.901 vs 0.783 vs 0.807. XAUUSD: 0.902 vs 0.792 vs 0.815. BTCUSD: 0.901 vs 0.794 vs 0.817. USTEC: 0.905 vs 0.791 vs 0.814.
- **Interpretation**: Two event-based trend-following charts naturally produce similar direction labels because they both filter noise and respond to sustained price moves. The high raw agreement is real but reflects shared methodology, not independent confirmation of trend direction.

### 2. Paired bootstrap CIs refute the hypothesis

- **Observation**: The pre-specified test — paired bootstrap on reference events that match both targets — shows negative differences for all instruments and regime scopes.
- **Evidence**: `bootstrap_cis.csv`. For ref=LineBreak, target_a=Renko, target_b=TimeBars, medium_high regime:
  - EURUSD: diff = -0.73 pp, CI = [-0.93, -0.53], n = 54,833
  - XAUUSD: diff = -2.80 pp, CI = [-2.99, -2.60], n = 58,460
  - BTCUSD: diff = -3.22 pp, CI = [-3.41, -3.04], n = 66,003
  - USTEC: diff = -2.75 pp, CI = [-2.95, -2.55], n = 54,052
  - All CIs exclude zero, all in the negative direction.
- **Interpretation**: On the subset of Line Break events that find matches in both Renko and Time Bars, Line Break direction agrees with Time Bars slightly MORE than with Renko. The effect is small (0.7-3.2 pp) but consistent and statistically significant across all instruments.

### 3. Renko agrees with Time Bars much more than with Line Break

- **Observation**: For ref=Renko, the bootstrap differences are large and negative (-13 to -15 pp).
- **Evidence**: `bootstrap_cis.csv`. EURUSD medium_high: diff = -14.7 pp, CI = [-15.1, -14.4], n = 45,231.
- **Interpretation**: Renko's ATR-based brick construction produces direction labels that align more closely with 1-minute time bars than with Line Break's level-based reversal logic. This is unsurprising: Renko bricks form on every price move of sufficient magnitude, while Line Break requires breaking previous line highs/lows — a stricter condition that produces fewer, more selective events.

### 4. Agreement increases with volatility regime

- **Observation**: For most chart-type pairs, agreement rates increase from low to medium to high volatility regimes.
- **Evidence**: `regime_metrics.csv`, `plots/regime_bars.png`. EURUSD LB↔Renko: 0.899 (low) → 0.899 (medium) → 0.905 (high). EURUSD LB↔TimeBars: 0.770 → 0.782 → 0.793.
- **Interpretation**: Stronger trends produce clearer directional signals across all chart types. The regime effect is consistent but small (1-2 pp per regime step).

### 5. Heiken Ashi shows lowest agreement with all other chart types

- **Observation**: TimeBars↔HeikenAshi agreement is consistently ~65%, the lowest of all pairs.
- **Evidence**: `pairwise_metrics.csv`. EURUSD: 0.650, XAUUSD: 0.658, BTCUSD: 0.662, USTEC: 0.657.
- **Interpretation**: HA's smoothing formula (averaging open/close) inverts direction labels on ranging bars where the real bar close is on the opposite side of the HA body. This is a known property of HA charts and confirms that HA direction is not directly comparable to raw bar direction.

### 6. Tolerance sensitivity: wider window reduces agreement slightly

- **Observation**: Increasing tolerance from 5m to 15m reduces LB↔Renko agreement by ~2 pp and LB↔TimeBars by ~1 pp.
- **Evidence**: `sensitivity_metrics.csv`, `plots/sensitivity.png`. The ranking (LB↔Renko > Renko↔TimeBars > LB↔TimeBars > LB↔HA) is stable across both tolerance windows.
- **Interpretation**: The wider tolerance captures more distant matches, which are more likely to have different directions. The ranking stability suggests the findings are not an artifact of the tolerance choice.

## Hypothesis Verdict

**REFUTED**

The hypothesis stated that "Line Break level 3 and Renko ATR-14 show stronger trend-direction agreement with each other than either does with 1-minute time bars during medium- and high-volatility regimes." The pre-specified success criterion required "paired bootstrap intervals excluding zero" for the improvement.

The raw pairwise agreement rates do show LB↔Renko at ~90%, exceeding each chart type's agreement with time bars by 9-12 percentage points. However, the paired bootstrap — which controls for the denominator by comparing the same reference events against both targets — shows the opposite:

- Line Break agrees with Time Bars slightly MORE than with Renko (diff = -0.7 to -3.2 pp, all CIs excluding zero, negative direction).
- Renko agrees with Time Bars MUCH more than with Line Break (diff = -13 to -15 pp).

This pattern holds across all four instruments and all regime scopes (medium, high, medium_high). The bootstrap CIs exclude zero decisively, but in the direction opposite to the hypothesis.

The discrepancy between raw pairwise and bootstrap results arises from denominator differences: raw pairwise metrics average asymmetric comparisons (sparse event charts vs dense time bars), while the bootstrap restricts to events that match both targets. The bootstrap result is the more controlled comparison and is the pre-specified test.

## Limitations

- **Paired subset is smaller than full population**: The bootstrap operates on reference events that match both targets (n = 16K-66K), which is a subset of the full event population. Results apply to this intersection, not to all events.
- **Regime labels cover only the evaluation segment**: Volatility regime labels are assigned only to the last ~30% of the analysis set (after train-segment calibration). Regime-stratified results do not cover the full analysis period.
- **Direction labels are binary**: Reducing trend direction to +1/-1 loses nuance about trend strength, duration, and confidence.
- **Single tolerance window for main criterion**: Only the 5m tolerance was used for the main test; 15m was sensitivity only. Different tolerance choices could shift the paired subset composition.
- **One dataset per instrument**: Each instrument has one session file. Results may not generalise to other time periods or market conditions.

## Alternative Explanations

- **Shared noise filtering**: LB and Renko both filter small price moves, so their agreement may reflect shared noise rejection rather than independent trend confirmation. The bootstrap result suggests that when controlling for the same events, Time Bars (which include all moves) actually agree more with LB than Renko does.
- **Event density mismatch**: Renko produces more events than Line Break for the same period. The asymmetric event rates may drive the raw agreement patterns independently of trend-direction correspondence.
- **ATR vs level-based logic**: Renko's ATR-based brick sizing adapts to volatility, while Line Break's fixed level parameter does not. This structural difference may explain why Renko tracks Time Bars more closely than Line Break does.

## Recommended Next Steps

1. **EXP-007 (Event Density & Temporal Resolution)**: Quantify how event density (bars per unit time) varies across chart types and instruments, and whether density differences explain agreement patterns independently of trend direction.
2. **EXP-008 (Regime-Adaptive Parameters)**: Test whether Line Break with volatility-adaptive level (analogous to Renko's ATR-based sizing) improves LB↔Renko agreement on the paired subset.
3. **Follow-up on HA distortion**: EXP-006 (already planned) will quantify Heiken Ashi synthetic price distortion, which is relevant given the low HA↔other agreement found here.
