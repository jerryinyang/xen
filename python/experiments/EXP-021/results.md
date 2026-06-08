# Results: Experiment EXP-021

## Summary

EXP-021 tested whether EXP-020 AVWAP bounce events show better fixed-horizon direction-signed real-price reaction than matched non-event controls from the same MA(20,50) regime. All three domains (5m, 1h, 4h) support the hypothesis with strong effects, tight CIs, and p < 0.001 after Holm adjustment. Evidence is not uniform across instruments (BTCUSD contributes the largest per-instrument effects, especially at 4h), but every instrument in every domain is reaction-reportable, and the equal-weight domain estimator confirms a positive signal across the board.

## Detailed Findings

### Finding 1: All three domains show statistically significant bounce reaction

**Observation**: The primary 3-bar domain-level effect is positive in every domain, with 95% regime-cluster bootstrap CIs entirely above zero and Holm-adjusted p-values well below 0.05.

| Domain | N events | Effect (bps) | 95% CI (bps) | Holm p | Decision |
|--------|----------|-------------|--------------|--------|----------|
| 5m | 16,249 | +3.8 | [+3.5, +4.1] | 0.0003 | EVIDENCE_FOR |
| 1h | 1,207 | +9.1 | [+5.1, +13.3] | 0.0003 | EVIDENCE_FOR |
| 4h | 246 | +37.6 | [+22.3, +52.7] | 0.0003 | EVIDENCE_FOR |

**Interpretation**: AVWAP bounce events consistently outperform same-regime non-event controls across all timeframes. The fixed-horizon reaction operationalization is supported. Effect sizes scale with domain (5m < 1h < 4h), consistent with larger per-bar moves at longer horizons. The secondary 1-bar and 6-bar horizons are also positive in every domain, ruling out horizon-specific artifacts (see `domain_reaction_forest.png`).

### Finding 2: Bounce reaction is positive in every instrument and direction

**Observation**: All 24 instrument×direction cells (4 instruments × 3 domains × 2 directions) have positive mean paired differences at the primary horizon (see `instrument_direction_heatmap.png`). The weakest cell is XAUUSD/1h/bull at +1.2 bps; the strongest is BTCUSD/4h/bull at +96.7 bps.

**Interpretation**: The bounce effect is broad, not concentrated in a single instrument or direction. No cell shows a negative mean reaction, which would signal a systematic bounce failure (e.g., momentum overwhelming the reversion). The domain estimators are representative, not artifact-driven.

### Finding 3: Within-regime matching controls for regime-phase confounds

**Observation**: The same-regime control restriction means each event's counterfactual is drawn from within its own `regime_id` (same instrument, domain, and direction), matched on anchor age and timestamp. Control counts are healthy: mean 4.5–5.0 controls per reportable event across all cells (see `control_match_diagnostics.png`). The regime-cluster bootstrap explicitly resamples at the regime level, so cross-regime independence is exact.

Non-reportable events are dominated by `insufficient_same_regime_controls` (e.g., BTCUSD/5m: ~400 non-reportable events per direction out of ~3000 total) and rare `insufficient_future_bars` (0–2 per cell). The same-regime restriction is binding but not crippling — all 3 domains have 4/4 instruments reaction-reportable.

**Interpretation**: The matching design works as intended. Control quality is high (near-maximum 5 controls for most reportable events), and the regime-level clustering captures the natural dependence structure of AVWAP state machines.

### Finding 4: Effect stability across secondary horizons

**Observation**: For all three domains, the 1-bar and 6-bar horizon effects are also positive and directionally consistent with the primary 3-bar effect (see `domain_reaction_forest.png` and `event_control_distributions.png`):

| Domain | h=1 (bps) | h=3 (bps) | h=6 (bps) |
|--------|-----------|-----------|-----------|
| 5m | +1.1 | +3.8 | +8.6 |
| 1h | +0.7 | +9.1 | +25.8 |
| 4h | +7.0 | +37.6 | +83.2 |

The monotonic increase across horizons is consistent with a persistent directional reaction (bounce events continue in the bounce direction over at least 6 bars). No domain has both secondary horizons negative, so no inconclusive-secondary-unstable verdict applies.

**Interpretation**: The bounce effect is not a one-bar fluke or a reversal artifact. Events that trigger continue to show relative strength for at least 6 completed bars, suggesting the AVWAP bounce captures a genuine regime-directional signal, not short-lived noise.

## Hypothesis Verdict

**SUPPORTED**

All four Evidence-FOR criteria from the scope are met:

1. EXP-020 dependency gate passes (SUPPORTED_FULL, 0 invariant violations, ready domains {5m, 1h, 4h}).
2. All three domains are reaction-reportable (≥3 reportable instruments each, with ≥30 events and ≥8 per direction).
3. All three domains have a primary effect > 0 bps, 95% CI lower bound > 0 bps, and Holm-adjusted p ≤ 0.05.
4. No domain has secondary horizons both negative (all secondary effects are positive).

The fixed-horizon bounce reaction operationalization of CF-AVWAP-001/HYP-002 is supported across all three domains. AVWAP bounce events carry genuine directional information relative to within-regime non-event bars.

## Limitations

1. **Same-regime control restriction creates a conservative counterfactual but reduces coverage.** Events in short regimes (few bars beyond the 6-bar exclusion window) are non-reportable. This is most visible at 4h (8–14 non-reportable events per direction vs 24–45 reportable). The restriction is scoped and the cost is visible in diagnostics, but it means the result applies to regimes long enough to produce eligible controls, not all AVWAP regimes.

2. **Within-regime matching does not control for volatility clustering.** Controls matched on anchor age and timestamp within the same regime still differ from events in their return distribution shape. The `event_control_distributions.png` plots show event returns are tighter around zero while controls have heavier tails, particularly at 4h. This is consistent with bounce filtering selecting regime-direction-confirming bars, but alternative matching (e.g., volatility-matched) could produce different effect sizes.

3. **4h sample is small (246 events).** The 4h CI is wide (22–53 bps) and the BTCUSD controls have extreme negative means that inflate the paired difference. The effect is real (p < 0.001, CI above zero), but its magnitude is uncertain and the pairing mechanics may overstate economic relevance.

4. **These are event-reaction returns, not strategy P&L.** Direction-signed log returns measure relative price reaction, not tradeable edge. No transaction costs, slippage, execution lag, or position sizing are modeled. A positive reaction reading does not guarantee positive net P&L after frictions.

## Alternative Explanations

1. **Control mean reversion, not event bounce.** In regimes where controls drift away from the AVWAP anchor, the matched comparison assigns "positive" reaction to any event that does not drift as far. The large paired differences at 4h BTCUSD (controls averaging −75 to −94 bps) suggest this mechanism contributes significantly. It does not invalidate the bounce signal — knowing which bars bounce rather than drift is useful — but the headline effect mixes bounce continuation with control deterioration.

2. **Regime detector look-ahead interacts with event timing.** The MA(20,50) regime detector is causal but lagging. Regime changes are confirmed only after the crossover completes, which means early-regime events may occur close to the pivot. The matching design controls for this through anchor-age matching, and the bootstrap clusters by regime, but regime-early vs regime-late event differences are not separately tested.

## Recommended Next Steps

1. **EXP-022 (Lifetime Move Study):** Measure the registered band-target/trend-change move-completion method against a look-ahead-safe benchmark. This addresses a different operationalization of the AVWAP thesis (holding to target vs fixed-horizon reaction) and is the next required component gate before EXP-023 candidate screening can be considered.

2. **If the lifetime study also supports proceeding**, EXP-023 would register the baseline AVWAP signal through the cTrader strategy-host branch and run the frozen qualification suite (strict gate stack, ratified-loose referee, revised portfolio-fitness unit).

3. **No instrument-level or domain-level refinement is warranted by these results alone** — all domains and instruments support the hypothesis, and the predeclared scope does not authorize parameter tuning or variant selection after seeing outcomes.
