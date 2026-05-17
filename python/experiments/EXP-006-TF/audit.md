# Audit Report: Experiment EXP-006-TF

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/src/timeframe_replication.py` (run_exp006_tf) | Correctness | PASS | HA generation, distortion metrics, regime stratification, and block bootstrap implemented correctly. |
| `python/src/timeframe_replication.py` (block_bootstrap_compression) | Edge cases | PASS | Handles n < 100 by returning empty dict; uses block size = min(100, max(10, n//20)). |
| `python/src/timeframe_replication.py` (run_exp006_tf) | Type safety | PASS | Uses `pl.DataFrame` operations; JSON serialization with `default=str`. |
| `python/src/timeframe_replication.py` (run_exp006_tf) | NaN handling | PASS | `drop_nulls(["RealReturn", "HAReturn"])` removes rows with NaN returns. |
| `python/src/timeframe_replication.py` (load_source_analysis) | Holdout exclusion | PASS | Lazy scan sorts by `CloseTime`, slices first 70% before `.collect()`. |
| `python/src/timeframe_replication.py` (load_timeframes) | Memory/performance | PASS | Lazy loading; plot samples capped at `PLOT_SAMPLE_N`. |
| `python/src/timeframe_replication.py` (run_exp006_tf) | Logging/output | PASS | 5 CSVs + 1 JSON + 4 plots produced. |
| `python/src/timeframe_replication.py` (run_exp006_tf) | Docstrings | PASS | Public functions in shared module have docstrings. |

## Numerical Validation

### Spot Checks

**EURUSD 15m VolatilityCompression:**
- RealVolatility = 0.0004921, HAVolatility = 0.0003618
- Compression = 1.0 - 0.0003618/0.0004921 = 1.0 - 0.7352 = 0.2648 ✓ matches

**EURUSD 15m MedianAbsReturnCompression:**
- RealMedianAbsReturn = 0.0002049, HAMedianAbsReturn = 0.0001531
- Compression = 1.0 - 0.0001531/0.0002049 = 1.0 - 0.7471 = 0.2529 ✓ matches

**Hypothesis thresholds:**
- Volatility compression threshold: ≥ 30% (0.30)
- Median absolute return compression threshold: ≥ 20% (0.20)
- EURUSD 15m: VolCompression = 0.265 < 0.30 → FAILS volatility threshold
- EURUSD 15m: MADCompression = 0.253 ≥ 0.20 → PASSES return threshold
- All instruments fail the 30% volatility compression threshold (range: 0.235-0.265)
- All instruments pass the 20% median return compression threshold (range: 0.233-0.286)
- Verdict: REFUTED (fewer than 3 instruments meet BOTH thresholds) ✓

**Block bootstrap parameters:**
- n = min(len(real), len(ha)) — for EURUSD 15m: n = 55229
- block = min(100, max(10, 55229//20)) = min(100, 2761) = 100
- BOOTSTRAP_N = 1000 resamples
- Appropriate block size for temporal data ✓

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| VolatilityCompression | [0, 1] ideally | 0.2346 to 0.2648 | YES |
| MedianAbsReturnCompression | [0, 1] ideally | 0.2327 to 0.2861 | YES |
| DirectionChangeCompression | [0, 1] ideally | 0.2667 to 0.2852 | YES |
| RealVolatility | > 0 | 0.00049 to 0.00590 | YES |
| HAVolatility | > 0 | 0.00036 to 0.00452 | YES |
| Rows | ≥ 0 | 12615 to 71201 | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| Volatility compression | 23-26% across all instruments/timeframes | YES | HA smoothing reduces volatility consistently |
| Median return compression | 23-29% | YES | Similar magnitude to volatility compression |
| Direction change compression | 27-29% | YES | HA reduces direction changes by similar amount |
| Regime stratification | Compression slightly higher in Low regime | YES | HA smoothing has proportionally larger effect in low-volatility periods |
| BTCUSD highest volatility | RealVol = 0.0059 (1h) | YES | Crypto is most volatile instrument |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| HA generation | Deterministic, sequential from completed bars | YES | `generate_heiken_ashi` is stateful and deterministic |
| Log returns | Close-to-close log returns are appropriate for compression measurement | YES | Standard approach; paired at identical timestamps |
| Block bootstrap | Block size of 100 captures temporal dependence | YES | 100 bars = ~25 hours at 15m, ~4 days at 1h; reasonable block length |
| Regime stratification | Train-calibrated terciles applied to evaluation segment | YES | `add_timebar_regimes` ensures no look-ahead |

## Results Plausibility

Results are highly plausible. Heiken Ashi consistently compresses volatility by 23-26% and median absolute returns by 23-29% across all instruments and timeframes. These values are below the 30% volatility threshold specified in the hypothesis, leading to a REFUTED verdict. The compression is consistent across regimes, with slightly higher compression in low-volatility regimes. The direction change frequency is also compressed by 27-29%, confirming HA's smoothing effect on both magnitude and direction.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: None
- Complexity budget: 2 statistical tests (distortion metrics, block bootstrap) / 2 budgeted; 4 visualisations / 4 budgeted; 0 new modules / 1 budgeted
- Holdout exclusion verified: YES
- Synthetic price discipline: YES — HA returns explicitly labelled as synthetic diagnostic returns

## Issues

### Warning

None.

### Info

1. **Compression is below 30% threshold but still substantial**
   - Description: Volatility compression of 23-26% is meaningful — HA does significantly distort return magnitude. The 30% threshold in the hypothesis may have been conservative. The conclusion that "HA-price-derived returns are unsuitable for strategy evaluation" remains valid even at 23-26% compression.
   - Impact: The hypothesis is technically refuted, but the practical warning about HA synthetic prices remains valid.

2. **Regime distortion metrics show consistent patterns**
   - Description: Compression is slightly higher in Low regimes (25-27%) than High regimes (24-26%) for most instruments. This suggests HA smoothing has a proportionally larger effect when market volatility is low.
   - Impact: Informational; not required by scope but adds useful context.

## Re-Audit Requirements

None. Verdict is PASS.
