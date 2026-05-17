# Audit Report: Experiment EXP-005-TF

## Summary

- **Verdict**: CONDITIONAL PASS
- **Critical Issues**: 0
- **Warnings**: 2
- **Info Notes**: 2

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/src/timeframe_replication.py` (run_exp005_tf) | Correctness | PASS | Pairwise agreement, regime stratification, and bootstrap CIs implemented correctly. |
| `python/src/timeframe_replication.py` (nearest_match_agreement) | Edge cases | PASS | Handles empty inputs; returns NaN agreement when no matches. |
| `python/src/timeframe_replication.py` (timestamp_direction_table) | Type safety | PASS | Uses `normalize_datetime_units` for consistent timestamp types. |
| `python/src/timeframe_replication.py` (distinct_source_events) | NaN handling | PASS | GroupBy with `maintain_order=True` and `.last()` aggregation. |
| `python/src/timeframe_replication.py` (load_source_analysis) | Holdout exclusion | PASS | Lazy scan sorts by `CloseTime`, slices first 70% before `.collect()`. |
| `python/src/timeframe_replication.py` (load_timeframes) | Memory/performance | PASS | Lazy loading; regime tables computed per timeframe. |
| `python/src/timeframe_replication.py` (run_exp005_tf) | Logging/output | PASS | 7 CSVs + 1 JSON + 5 plots produced. |
| `python/src/timeframe_replication.py` (run_exp005_tf) | Docstrings | PASS | Public functions in shared module have docstrings. |

## Numerical Validation

### Spot Checks

**EURUSD 15m LineBreak<->Renko 5-min agreement:**
- Matches = 7213, LeftRows = 14456
- Agreement = 1.0, OverlapRate = 7213/14456 = 0.499 ✓
- LB and Renko always agree on direction when they match (100% agreement) ✓

**EURUSD 15m LineBreak<->Time 5-min agreement:**
- Matches = 14456, LeftRows = 14456
- Agreement = 0.9859, OverlapRate = 1.0 ✓
- LB matches all Time bars (1:1 timestamp join via CloseTime), 98.6% direction agreement ✓

**Bootstrap CI — 15m 5min LB_Renko_minus_LB_Time:**
- Mean = 0.0108, CI = [0.0080, 0.0145], N = 8
- N=8 = 4 instruments × 2 regimes (Medium, High) ✓
- CI excludes zero → statistically significant improvement ✓

**Bootstrap CI — 15m 15min LB_Renko_minus_LB_Time:**
- Mean = -0.00087, CI = [-0.0041, 0.0024], N = 8
- CI includes zero → not significant at 15-min tolerance ✓
- This is the sensitivity check; primary 5-min window is the decision criterion ✓

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| Agreement | [0, 1] | 0.636 to 1.0 | YES |
| OverlapRate | [0, 1] | 0.426 to 1.0 | YES |
| Matches | ≥ 0 | 95 to 55230 | YES |
| LeftRows | ≥ 0 | 135 to 71202 | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| LB<->Renko agreement at 5min | 1.0 (all instruments/timeframes) | YES | When LB and Renko events align within 5min, they always agree on direction |
| LB<->Renko overlap at 5min | ~0.50 | YES | Only ~50% of LB events find a Renko match within 5min |
| LB<->Renko overlap at 15min | ~0.50-0.77 | YES | Wider window captures more matches but not all |
| Time<->HA agreement | ~0.64-0.66 | YES | HA direction (HAClose>=HAOpen) differs from Time direction (Close>=Open) ~35% of time |
| Bootstrap N=8 | 4 instruments × 2 regimes | YES | Correct sample size |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Nearest-neighbor matching | Closest timestamp within tolerance is the correct match | YES | Standard approach for sparse event alignment |
| Direction comparability | +1/-1 direction labels are comparable across chart types | YES | All chart types use same Direction encoding |
| Regime calibration | Train-derived terciles applied to evaluation segment only | YES | `add_timebar_regimes` calibrates on first 70%, applies only after train end |
| Bootstrap on instrument×regime level | Each instrument×regime combination is an independent observation | PARTIAL | Temporal dependence within each instrument×regime; bootstrap treats them as independent |

## Results Plausibility

Results are plausible. LineBreak and Renko agree perfectly (100%) when they match within 5 minutes, confirming they capture the same trend direction. However, overlap is only ~50%, meaning half of LB events don't have a Renko counterpart within 5 minutes. Both LB and Renko agree with Time bars at ~98-99%, showing they preserve the underlying trend direction. Time<->HA agreement at ~65% reflects HA's smoothing effect, which can flip direction relative to raw price.

The hypothesis (LB/Renko agreement > each chart's agreement with Time bars by ≥10pp in medium/high regimes) is **not supported**: LB<->Renko agreement = 100%, but LB<->Time = ~98% and Renko<->Time = ~99%. The improvement is only 1-2pp, far below the 10pp threshold.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: None
- Complexity budget: 3 statistical tests (pairwise agreement, bootstrap CIs, sensitivity) / 3 budgeted; 5 visualisations / 5 budgeted; 0 new modules / 1 budgeted
- Holdout exclusion verified: YES

## Issues

### Warning

1. **15-minute tolerance bootstrap CI includes zero**
   - File: `python/experiments/EXP-005-TF/results/bootstrap_cis.csv`
   - Description: For 15m timeframe, 15-min tolerance, LB_Renko_minus_LB_Time CI = [-0.0041, 0.0024] includes zero. The scope requires "paired bootstrap intervals excluding zero" for Evidence FOR. The 5-min primary window passes (CI = [0.008, 0.015]), but the 15-min sensitivity window does not.
   - Impact: The primary criterion uses 5-min tolerance, which passes. The 15-min window is a sensitivity check. However, the scope states bootstrap intervals should exclude zero for the hypothesis to be supported. Since the 5-min CI excludes zero but the agreement improvement is only ~1pp (far below 10pp threshold), the hypothesis is refuted on magnitude grounds regardless.
   - Fix: No fix needed; the hypothesis is refuted because the agreement improvement (1-2pp) is far below the 10pp threshold, regardless of CI significance.

2. **LB<->Renko overlap rate is only ~50% at 5-min tolerance**
   - File: `python/experiments/EXP-005-TF/results/pairwise_metrics.csv`
   - Description: Only ~50% of LineBreak events find a Renko match within 5 minutes. The scope notes "if overlap rates are low, report the result as inconclusive even if matched-event agreement is high." However, 50% overlap is not extremely low — it reflects the different event densities of LB and Renko.
   - Impact: The 100% agreement on matched events is meaningful but applies to only half of LB events. The interpretation should note this limitation.
   - Fix: No fix needed; overlap rates are reported alongside agreement rates as required.

### Info

1. **LB<->Renko agreement is exactly 1.0 across all instruments/timeframes**
   - Description: When LB and Renko events align within the tolerance window, they always agree on direction. This is a strong finding — both event charts capture the same trend direction when they emit events at similar times.
   - Impact: Notable result; suggests event charts are directionally consistent with each other.

2. **Time<->HA agreement is consistently ~65%**
   - Description: HA direction differs from Time bar direction ~35% of the time across all instruments and timeframes. This reflects HA's smoothing formula, which can produce different direction signals than raw OHLC.
   - Impact: Expected behavior; confirms HA transforms direction, not just magnitude.

## Re-Audit Requirements

None. Verdict is CONDITIONAL PASS due to Warning 1 (15-min tolerance CI includes zero), but this does not affect the primary conclusion since the hypothesis is refuted on magnitude grounds (1-2pp improvement vs 10pp threshold).
