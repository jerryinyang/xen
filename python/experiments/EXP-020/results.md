# Results: Experiment EXP-020

## Summary

EXP-020 demonstrates that the registered CF-AVWAP-001 first-branch AVWAP state machine produces a deterministic, look-ahead-safe event substrate with usable bounce-event coverage. All 12 instrument/domain cells (4 instruments × 3 domains) are reportable, all 3 domains are ready, all invariant checks pass with zero violations, and the generator produces byte-identical output on replay. The substrate is cleared for follow-up reaction and lifetime-move studies on any of the scoped domains.

## Detailed Findings

### Finding 1: Full Domain Readiness

- **Observation**: All three scoped domains (5m, 1h, 4h) satisfy the ready-domain criterion of at least 3 reportable instruments.
- **Evidence**: `domain_readiness.csv` — 5m: 4/4 reportable instruments; 1h: 4/4; 4h: 4/4. Every instrument/domain cell has ≥30 total events and ≥8 events in each direction.
- **Interpretation**: The AVWAP bounce definition produces usable event counts across all instruments and timeframes. No domain is coverage-starved; no instrument degenerates to a single direction. EXP-021 and EXP-022 may scope all three domains.

### Finding 2: Deterministic and Look-Ahead-Safe

- **Observation**: The sequential state machine produces identical event and regime tables on a full replay pass.
- **Evidence**: `determinism_check.csv` — 12/12 cells match event-table hashes; 12/12 cells match regime-table hashes. All invariant checks pass with 0 violations across 192 check rows (16 checks × 12 cells).
- **Interpretation**: The generator is deterministic (no randomness, no path-dependent state leaks) and streaming-safe (each bar processed using only current and prior completed bars). The invariant framework independently validates anchor selection, arm/trigger causality, value consistency, and re-arm sequencing with zero failures across all cells.

### Finding 3: Substantial Event Coverage

- **Observation**: 20,911 total bounce events across 12 cells. Coverage scales with domain bar count.
- **Evidence**: `event_coverage.csv` —
  - 5m: 4,327–5,978 events per instrument (density ~260–276 per 10k bars)
  - 1h: 287–421 events per instrument (density ~207–242 per 10k bars)
  - 4h: 61–109 events per instrument (density ~199–246 per 10k bars)
- **Interpretation**: Event density is consistent across instruments and domains, with higher absolute counts on shorter timeframes (as expected from more total bars). The 4h domain's 61–109 events per instrument provide a viable but smaller substrate for follow-up studies; reaction experiments may need to pool across instruments or use direction-pooled metrics.

### Finding 4: Balanced Direction Coverage

- **Observation**: No cell shows severe directional imbalance.
- **Evidence**: `direction_balance.csv` — bull fractions range from 0.46 to 0.56 across all 12 cells. The widest gap is EURUSD/4h (39 bull, 31 bear; ρ_bull = 0.557).
- **Interpretation**: The AVWAP arm/trigger rule produces events in both market regimes without degenerating to a single direction for any instrument/domain. Follow-up reaction studies can analyze bull and bear events separately or pooled without concern for empty direction cells.

### Finding 5: Holdout Exclusion Verified

- **Observation**: All analyses use exactly the first 70% of chronologically ordered source data.
- **Evidence**: `analysis_metadata.csv` — each instrument's analysis rows are exactly 70.00% of source total rows (BTCUSD 1,088,960/1,555,658; EURUSD 872,242/1,246,061; USTEC 830,541/1,186,488; XAUUSD 830,671/1,186,674). `invariant_checks.csv` — 0 holdout_fence violations across all cells.
- **Interpretation**: The holdout rule is enforced at the loading layer and independently verified at the event level. No event references data beyond the analysis set.

## Hypothesis Verdict

**SUPPORTED_FULL**

The scoped hypothesis — that the Phase 004 CF-AVWAP-001 first branch can be implemented as a deterministic, look-ahead-safe event substrate with usable bounce-event coverage on at least one predeclared domain — is supported with full domain readiness. All three Evidence-FOR criteria are met:

1. All invariant checks pass for every instrument/domain (0 violations across 192 checks)
2. Deterministic replay produces identical event tables and summary hashes (12/12 cells match)
3. All three domains (5m, 1h, 4h) are ready (4/4 reportable instruments each)

Under the scope's classification, this is `SUPPORTED_FULL`: EXP-021 and EXP-022 may proceed on all three domains.

## Limitations

1. **Readiness is not signal quality.** A reportable cell means the event definition produces enough observations for a follow-up reaction study, not that those events have predictive value. The bounce events may be random crossings of a slow-moving average with no directional edge.
2. **Determinism verified on one run.** The replay check confirms byte-level reproducibility within the same execution environment. Cross-platform floating-point differences could produce divergent hashes but would not change event counts or direction labels.
3. **EURUSD/4h marginal bear count.** At 31 bear events, EURUSD/4h has the lowest single-direction count among all reportable cells, just above the 8-event floor. A reaction study on 4h may find wider confidence intervals for EURUSD bearish events.
4. **Anchor selection uses MA(20,50) regime detector only.** The substrate readiness result does not generalize to other regime detectors (Line Break, Market Bias, ATR pivot, etc.). Each branch requires a separate scope and experiment.

## Alternative Explanations

1. **MA(20,50) produces frequent regime changes.** The ~3,500–5,000 regimes on 5m across the analysis period (~2.5 years) imply regime changes every ~40-60 bars on average. This is mechanically unsurprising for a fast/slow crossover on intraday data. The bounce events may be predominantly driven by this regime-change frequency rather than a meaningful AVWAP reversion dynamic.

## Recommended Next Steps

1. **EXP-021**: Scope a fixed-horizon direction-signed reaction study using the generated event metadata. Test whether bounce events show better real-price outcomes than matched non-event controls, on any subset of the ready domains.
2. **EXP-022**: Scope the original band-target and trend-change lifetime-move study using the stored `favorable_target_at_trigger`, `adverse_target_at_trigger`, and `is_pyramid_bounce` fields.
3. **Note on 4h domain**: Consider pre-registering a pooled-instrument or direction-pooled design for 4h reaction metrics, since individual instrument/direction cells have the smallest counts.
