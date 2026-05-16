# Results Interpretation: Experiment EXP-006

## Verdict

**REFUTED**

## Evidence Summary

### Primary Hypothesis Test

The hypothesis stated: *"Heiken Ashi synthetic prices compress realised return magnitude and volatility by at least 30% versus real 1-minute prices on all 4 Phase 1 instruments."*

**Volatility compression (30% threshold required):**

| Instrument | Point Estimate | 95% CI | Meets 30%? |
|------------|---------------|--------|------------|
| EURUSD | 0.254 | [0.247, 0.259] | NO |
| XAUUSD | 0.260 | [0.255, 0.265] | NO |
| BTCUSD | 0.259 | [0.251, 0.267] | NO |
| USTEC | 0.257 | [0.250, 0.262] | NO |

**Result**: Zero of 4 instruments meet the 30% volatility compression threshold. All bootstrap CIs are entirely below 0.30, with upper bounds ranging from 0.259 to 0.267. The compression is real and precisely estimated, but consistently ~4-5 percentage points below the hypothesized threshold.

**Median absolute return compression (20% threshold required):**

| Instrument | Point Estimate | 95% CI | Meets 20%? |
|------------|---------------|--------|------------|
| EURUSD | 0.202 | [0.194, 0.207] | Barely (CI includes < 0.20) |
| XAUUSD | 0.248 | [0.246, 0.251] | YES |
| BTCUSD | 0.270 | [0.268, 0.272] | YES |
| USTEC | 0.256 | [0.254, 0.259] | YES |

**Result**: 3 of 4 instruments clearly exceed the 20% threshold. EURUSD barely clears it at the point estimate (0.202) but its CI lower bound (0.194) falls below 0.20.

### Success/Failure Criteria Assessment

Per scope.md:
- **Evidence FOR** requires: all 4 instruments show ≥30% vol compression AND ≥20% median abs return compression. → **NOT MET** (0/4 meet vol threshold).
- **Evidence AGAINST**: fewer than 3 instruments meet either compression threshold. → **MET** (0/4 meet the vol threshold).
- **Inconclusive**: compression present but below threshold, regime effects dominate. → Not applicable — the failure is clear and consistent, not ambiguous.

### Secondary Findings

**Regime stratification**: Compression is present across all three volatility regimes (Low/Medium/High) on all instruments. The regime heatmap shows:
- Volatility compression: 0.24-0.27 across regimes, with slightly lower compression in High regimes.
- Median absolute return compression: 0.20-0.27, increasing with volatility regime.
- Range compression: HA mean range is **higher** than real mean range on all instruments and regimes (negative compression), because HAClose is an OHLC average that can produce wider apparent candle ranges even as close-to-close changes are smoothed.
- Direction change frequency: HA shows 30-35% fewer direction changes than real prices (0.37-0.40 vs 0.51-0.57), confirming the trend-smoothing property.

**Cross-instrument consistency**: Volatility compression is remarkably consistent at 25.4-26.0% across all four instruments spanning forex, commodity, crypto, and index. This suggests the compression level is a structural property of the HA formula rather than instrument-specific.

### Uncertainty and Limitations

1. **Bootstrap CIs are very tight** due to large sample sizes (830K-1.09M bars). The precision is high, so the finding that compression is ~25-26% (not 30%) is robust.
2. **Regime calibration**: Audit Warning 1 notes that regime thresholds were calibrated on 70% of the analysis set rather than the train segment (49% of full dataset). This does not affect the aggregate compression results, only the regime-stratified breakdown.
3. **Descriptive only**: This experiment quantifies distortion magnitude but does not assess whether the distortion is economically material for any specific use case. That is a separate question.
4. **HA formula is fixed**: The ~25-26% compression is specific to the standard HA formula (HAClose = (O+H+L+C)/4). Modified HA variants could produce different compression levels.

## Conclusion

The hypothesis is **refuted**. Heiken Ashi does compress both return volatility and median absolute return magnitude, but the compression is approximately 25-26% for volatility and 20-27% for median absolute returns — consistently below the 30% volatility threshold stated in the hypothesis. The finding is precise (tight bootstrap CIs), consistent across all four instruments, and present across all volatility regimes.

The practical implication is unchanged: HA-derived returns are unsuitable for strategy evaluation because they systematically understate real return magnitude and volatility. The exact compression factor (~25% rather than ≥30%) does not alter this conclusion — it merely quantifies it more precisely.

## Follow-Up Recommendations

These are new experiment scopes, not extensions to EXP-006:
1. **EXP-XXX**: Test whether a ~25% compression factor is sufficient to materially distort signal quality metrics (e.g., win rate, Sharpe ratio) when signals are generated on HA charts but evaluated on real prices.
2. **EXP-XXX**: Compare HA distortion to Renko and Line Break distortion on the same instruments to rank chart types by synthetic-price deviation magnitude.
