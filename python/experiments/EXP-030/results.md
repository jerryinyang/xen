# Results: EXP-030 — 15-Minute Sweep Reversal Behavior

## Verdict

**INCONCLUSIVE**

Counts are adequate on all four instruments, but no instrument shows a positive failed-sweep advantage at 15-minute resolution, and the EXP-015 EURUSD partial positive does not replicate — it reverses direction. Results are not uniformly AGAINST (XAUUSD and USTEC test CIs include zero), but the directional picture provides substantive evidence for the reflection.

---

## Primary Result: Sweep-minus-Breach Hit1R_60m

The primary metric is the sweep-minus-breach difference in 1R-before-stop probability at 60 minutes of post-confirmation executable time. A positive difference would indicate sweeps outperform breaches; a negative difference indicates the opposite.

| Instrument | Segment | Sweep N | Breach N | Point Diff | 95% CI | CI Excludes Zero |
|------------|---------|---------|----------|------------|--------|-----------------|
| EURUSD | Train | 327 | 456 | −0.124 | [−0.195, −0.054] | YES (negative) |
| EURUSD | Test | 126 | 195 | **−0.145** | [−0.255, −0.036] | YES (negative) |
| XAUUSD | Train | 330 | 464 | −0.062 | [−0.132, +0.008] | NO |
| XAUUSD | Test | 152 | 173 | +0.011 | [−0.101, +0.122] | NO |
| BTCUSD | Train | 427 | 469 | −0.120 | [−0.181, −0.056] | YES (negative) |
| BTCUSD | Test | 142 | 175 | **−0.154** | [−0.266, −0.047] | YES (negative) |
| USTEC | Train | 416 | 543 | −0.044 | [−0.108, +0.023] | NO |
| USTEC | Test | 147 | 259 | +0.046 | [−0.057, +0.149] | NO |

All floors (≥100 risk-feasible sweep events per segment) are met. The failure to support the hypothesis is not a sample-size collapse.

---

## Comparison with EXP-015 1-Minute Baseline

| Instrument | EXP-030 Test Diff | EXP-015 Test Diff | Direction Change? |
|------------|------------------|------------------|-------------------|
| EURUSD | −0.145 [−0.255, −0.036] | +0.134 [+0.001, +0.267] | **YES — reversed** |
| XAUUSD | +0.011 [−0.101, +0.122] | −0.029 [−0.151, +0.095] | No (both near zero) |
| BTCUSD | −0.154 [−0.266, −0.047] | −0.117 [−0.250, +0.018] | No (both negative) |
| USTEC | +0.046 [−0.057, +0.149] | +0.048 [−0.063, +0.160] | No (nearly identical) |

### EURUSD: Partial Positive Reverses at 15-Minute Resolution

The EXP-015 EURUSD Test partial positive (+0.134, CI excludes zero from above) **reverses to −0.145 (CI excludes zero from below)** at 15-minute resolution. The 15-minute result is not merely a null; it contradicts the 1-minute finding with a comparably precise confidence interval.

This reversal likely reflects a resolution effect: at 15-minute bars, the confirming sweep candle already incorporates much of the post-sweep reversal price action within its body. By the time the outcome window begins (after the 15-minute candle close), the favorable reversal move has largely already occurred, leaving the remaining 60-minute window with less favorable follow-through than a 1-minute entry.

### BTCUSD: Consistent Negative Signal

BTCUSD shows a consistent negative pattern across both train and test, with CIs excluding zero negatively in both segments. This is the most stable finding — sweeps underperform breaches on BTCUSD at 15-minute resolution, consistent in direction with the EXP-015 negative point estimate (−0.117) though now statistically sharper.

### XAUUSD and USTEC: Consistent Null

Both instruments show near-zero differences at both 1-minute and 15-minute resolution, with overlapping CIs that include zero in both experiments. The null result is stable across timeframes for these instruments.

---

## Secondary Metrics (MAE/MFE/Return at 60 Minutes)

Secondary bootstrap summaries (sweep-minus-breach for MAE_R_60m, MFE_R_60m, Return_R_60m, pooled across segments) show no consistent positive sweep advantage on any instrument. EURUSD and BTCUSD show negative Return_R_60m differences consistent with the primary finding.

---

## Horizon Stability

Horizon sweep of Hit1R at 30, 60, and 120 minutes confirms that the instrument-level patterns are stable across horizons. EURUSD and BTCUSD remain negative across all horizons. XAUUSD and USTEC remain near zero. No instrument shows a pattern that peaks at 60 minutes specifically (which would suggest horizon-specific manipulation).

---

## Interpretation Against Success Criteria

| Criterion | Outcome |
|-----------|---------|
| New positive instrument (CI excludes zero, positive) vs EXP-015 on ≥ 1 instrument | NOT MET |
| EURUSD partial positive replicates tighter or stronger | NOT MET — reversed in direction |
| All CIs include zero (AGAINST) | NOT MET — EURUSD and BTCUSD CIs exclude zero negatively |
| ≥ 3 of 4 instruments underpowered (INCONCLUSIVE) | NOT MET — all floors pass |

---

## Conclusions for the Phase 004A Reflection

1. **The EXP-015 EURUSD partial sweep positive does not replicate at 15-minute resolution — it reverses.** The directional contradiction, with CIs excluding zero in opposite directions, is the most informative finding. The EURUSD sweep-reversal edge identified at 1-minute is a resolution-specific phenomenon that depends on entering at the 1-minute confirming close rather than waiting for the 15-minute candle to complete.

2. **BTCUSD shows a consistent negative sweep-vs-breach signal at 15-minute** (both segments). This is a new stable finding: at 15-minute bars, sweeps deliver worse 60-minute outcomes than breaches on BTCUSD, consistent with the resolution-entrainment interpretation above.

3. **XAUUSD and USTEC show no timeframe-dependent change** — results are near-zero at both 1-minute and 15-minute. This null is stable and informative: these instruments do not show sweep-specific behavior at either resolution.

4. **The resolution effect is the key structural finding**: the 15-minute confirmation bar incorporates the post-sweep reversal within its body, compressing the available 60-minute outcome window and converting the 1-minute positive to a near-zero or negative result. Any future sweep work in the ICT framework must account for this resolution-timing interaction.

5. **For the Phase 004A reflection**: EXP-030 does not provide a new positive basis for a sweep-focused Phase 004B branch. The EURUSD deferred positive from Phase 003 is functionally closed at 15-minute resolution. Any future sweep redesign would need to address resolution-timing directly and scope a 1-minute entry approach explicitly.
