# Results: Experiment EXP-022

## Summary

The AVWAP band-target/trend-change lifetime method produces more favorable completed-move outcomes for bounce events than matched non-event controls in all three domains. All three domains (5m, 1h, 4h) meet the predeclared Evidence-FOR criteria: rate differences of +23.9pp, +21.9pp, and +26.4pp respectively, with 95% CIs well above 0, Holm-adjusted p=0.0003, positive expectancy consistency, and volatility-context ratios near 1.0 confirming comparable target difficulty. The original lifetime operationalization is **SUPPORTED** on every EXP-020 ready domain.

## Detailed Findings

### Favorable Target-Completion Rate Advantage — All Domains

**Observation:** AVWAP bounce events complete favorably at a substantially higher rate than matched non-event controls drawn from the same regime, on every domain.

| Domain | Event Fav Rate | Control Fav Rate | Rate Diff (pp) | 95% CI | Holm p |
|--------|---------------|-----------------|----------------|--------|--------|
| 5m | 68.5% | 44.6% | +23.9 | [22.7, 25.1] | 0.0003 |
| 1h | 67.2% | 45.3% | +21.9 | [17.2, 26.6] | 0.0003 |
| 4h | 67.8% | 41.5% | +26.4 | [17.7, 35.3] | 0.0003 |

The instrument-averaged estimator gives equal weight to all 4 reportable instruments per domain. All three CIs are well above 0, and the Holm-adjusted p-values survive the 3-domain family correction.

**Interpretation:** Bounce events have a ~22–26 percentage point higher chance of reaching their favorable target than a comparable non-event bar facing the same target geometry. The 4h effect is largest in magnitude and widest in CI (fewest events/controls), but all three domains are clean.

### Lifetime Expectancy Advantage

**Observation:** Event target-completions realize larger direction-signed log returns than matched-control target-completions in every domain, confirming that the rate advantage is not bought by smaller favorable moves.

| Domain | Expectancy Diff (bps) | 95% CI |
|--------|---------------------|--------|
| 5m | +6.5 | [6.1, 7.0] |
| 1h | +27.0 | [20.4, 34.4] |
| 4h | +79.6 | [54.9, 105.8] |

Expectancy grows monotonically with domain width — wider targets at longer domains yield larger per-completion bps when events resolve favorably. The positive expectancy in all domains satisfies the predeclared consistency check.

### Trend-Change and Censoring

Trend-change completions (the regime flips before either target is reached) are a meaningful minority: ~15–20% of both event and control moves. Unfinished moves are <0.1% in every domain (the analysis set spans multiple years). This low censoring rate means the target-completion denominator is not meaningfully eroded by unresolved moves.

### Volatility-Context Diagnostic

All three domains have median matched-pair volatility-context ratios inside the predeclared `[0.5, 2.0]` bounds:

| Domain | Median Vol Ratio |
|--------|-----------------|
| 5m | 0.986 |
| 1h | 1.024 |
| 4h | 0.987 |

Values near 1.0 indicate matched controls face comparable local volatility to events — the favorable rate advantage is not confounded by event-vs-control volatility mismatch.

### Direction and Pyramid-Bounce Splits

The favorable rate advantage appears in both bullish and bearish directions and in both first-bounce and pyramid-bounce subtypes, with no single cell driving the headline result (see `direction_pyramid_diagnostics.png`). Event favorable rates are broadly elevated over controls across all instrument/direction/pyramid strata.

## Hypothesis Verdict

**SUPPORTED**

All predeclared Evidence-FOR criteria are met:
- EXP-020 dependency gate passes (SUPPORTED_FULL, all 3 domains ready, 0 invariant failures)
- All 3 domains are lifetime-reportable (4/4 instruments ≥30 target-completed events and controls)
- All 3 domains have event favorable-rate > matched-control rate, CI lower bound > 0 percentage points
- Holm-adjusted primary p ≤ 0.05 in all domains (family of 3)
- Event lifetime expectancy ≥ 0 in all domains on the point estimate
- No domain is volatility-context-confounded (all medians within [0.5, 2.0])
- No domain is censored (unfinished fraction 0.0)

## Limitations

- The result is specific to the CF-AVWAP-001 first-branch definition (MA(20,50) regime, TickVolume^0.75, MAD band 1.0). Other AVWAP branches or parameterizations may differ.
- Events with geometrically invalid targets (favorable_bps ≤ 0 or adverse_bps ≥ 0) — 4,604 across the analysis set — are excluded rather than repaired. This is correct but reduces the effective event pool in cells with very close A/VWAP prices.
- Target distances are event-frozen and transferred to controls in log-return bps. This assumes that a given bps target challenge is equally difficult regardless of the starting absolute price level — reasonable over short-to-medium horizons but not tested here.
- The matched-control design controls for regime state, anchor age, and timestamp proximity, but it cannot control for unmeasured confounders that might systematically differ between bounce-trigger bars and non-trigger bars within the same regime.
- The favorable rate advantage is a component result (lifetime method), not a strategy P&L result. EXP-023 (cTrader strategy-host screening through the frozen qualification suite) remains required before any strategy claim.

## Alternative Explanations

- Bounce events systematically occur at points of lower local volatility or tighter price clustering, making their targets more reachable. This is a selection-bias story, but the volatility-context ratios near 1.0 make it less plausible: control bars face comparable local volatility.
- The regime-direction-aligned target structure may be intrinsically biased upward for events versus same-regime non-events if events occur at more favorable anchor positions within the regime. The anchor-age matching partially controls for this.

## Recommended Next Steps

1. **EXP-023** — If the lifetime component signal supports proceeding in Phase 004 terms (which it does — all 3 domains EVIDENCE_FOR), proceed to the AVWAP baseline candidate screen through the frozen suite, requiring cTrader strategy-host generation.
2. **CF-AVWAP-001/LB** — The Line Break direction regime detector is the next registered non-baseline branch if EXP-023 completes and leaves open questions about regime-definition sensitivity.
