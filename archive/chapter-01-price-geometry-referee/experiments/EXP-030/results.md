# Results: Experiment EXP-030 — Cost-Bearing Tradability of the Faithful Selective AVWAP Strategy

## Summary

Under the predeclared cost model (CONSERVATIVE binding variant: per-instrument RT = EURUSD 3.0 / USTEC 5.0 / XAUUSD 6.0 / BTCUSD 16.0 bps), the faithful AVWAP strategy does **not** retain positive net per-event expectancy on any domain under the equal-weight cross-instrument binding metric. The phase outcome is **INCONCLUSIVE**: 5m and 1h are cleanly **EVIDENCE_AGAINST** (net CIs entirely below 0), while 4h is **INCONCLUSIVE_SPANS_ZERO** (CI spans 0, power-limited at n=187). The cost-bearing tradability gate for the global holdout (EXP-032) is **not passed**. The non-binding attribution companion (net matched-control excess) remains EVIDENCE_FOR on 1h/4h, confirming the Phase-006 gross edge survives costs on that alternative estimand, but the binding absolute P&L question is unresolved-to-negative.

## Detailed Findings

### Finding 1: Phase outcome INCONCLUSIVE — no domain clears the tradability gate

- **Observation**: The predeclared binding metric (equal-weight cross-instrument absolute net per-event expectancy under CONSERVATIVE costs) produces:
  - **5m**: −6.74 bps [−7.04, −6.38], Holm p=1.000 → **EVIDENCE_AGAINST**
  - **1h**: −6.04 bps [−11.02, −1.53], Holm p=1.000 → **EVIDENCE_AGAINST**
  - **4h**: +2.60 bps [−14.87, +19.28], Holm p=1.000 → **INCONCLUSIVE_SPANS_ZERO**
- **Evidence**: `net_expectancy_results.csv` (CONSERVATIVE rows), `plots/net_expectancy.png`, `plots/verdict_summary.png`
- **Interpretation**: The equal-weight domain aggregate is dominated by BTCUSD (RT_cons=16.0 bps, comprising 4.0 of the 7.5 bps mean cross-instrument drag). 5m gross absolute (+0.76 bps) is far below even the lowest RT_cons, confirming the scope's stated expectation that 5m is the stress case. 1h gross absolute (+1.46 bps) is similarly dominated. 4h would need to show net > 0 with CI_low > 0 to clear the gate; the point estimate is positive (+2.60) but the CI is too wide (half-width ~17 bps, n=187) to resolve. No domain meets the Evidence-FOR criteria, so the phase outcome is INCONCLUSIVE.

### Finding 2: BTCUSD cost dominates the equal-weight aggregate; per-instrument heterogeneity is large

- **Observation**: The per-instrument breakout (`net_by_instrument.csv`) reveals stark heterogeneity:
  - **EURUSD-4h**: net_cons = +12.38 bps [CI: +2.67, +21.46], headroom_cons = +12.38 bps, **survives CONSERVATIVE costs** (non-binding flag)
  - **XAUUSD-4h**: net_cons = −0.69 bps [CI: −22.53, +25.63], headroom = −0.69 bps
  - **USTEC-4h**: net_cons = +10.38 bps [CI: −19.43, +36.28], headroom = +10.38 bps
  - **BTCUSD-4h**: net_cons = −11.67 bps [CI: −72.89, +42.14], headroom = −11.67 bps
  - All 5m and 1h cells have negative net_cons with CI entirely below 0 (except XAUUSD-1h where CI spans 0).
- **Evidence**: `net_by_instrument.csv`, `plots/breakeven_heatmap.png`, `plots/gross_to_net_waterfall.png`
- **Interpretation**: EURUSD (RT_cons=3.0 bps) has sufficient gross absolute edge on 4h to survive costs, and this is statistically detectable at the per-instrument level. BTCUSD (RT_cons=16.0 bps) is a dominant drag on the equal-weight mean. The equal-weight aggregation faithfully reproduces the EXP-028 PRIMARY structure but conflates instruments with very different cost profiles. This is a stated, predeclared limitation; per-instrument tradability requires a separately scoped experiment with multiplicity control.

### Finding 3: The absolute-vs-relative distinction drives the verdict

- **Observation**: The non-binding attribution companion (net matched-control excess = gross excess − RT_i) remains EVIDENCE_FOR on 1h and 4h:
  - **5m CONSERVATIVE**: −1.72 bps [−2.09, −1.34], Holm p=1.000 → EVIDENCE_AGAINST
  - **1h CONSERVATIVE**: +15.88 bps [CI: +10.23, +22.00], Holm p=0.003 → **EVIDENCE_FOR**
  - **4h CONSERVATIVE**: +61.52 bps [CI: +40.17, +83.75], Holm p=0.003 → **EVIDENCE_FOR**
- **Evidence**: `attribution_companion.csv`, `plots/verdict_summary.png`
- **Interpretation**: The Phase-006 matched-control structure absorbs a negative control discount — returns are `event − matched_control`, not raw event P&L. The absolute binding metric charges costs against the raw event leg (the deployable quantity), which must carry that full control discount. The companion's FOR on 1h/4h shows the excess survives costs, confirming the Phase-006 result is not overturned. The binding AGN/INCONCLUSIVE on the absolute metric shows that the edge's economic magnitude, net of the control discount and costs, is not reliably positive. Both statements are defensible and non-contradictory — they measure different estimands.

### Finding 4: 4h power is limited for the absolute estimand

- **Observation**: The 4h CONSERVATIVE CI has a half-width of ~17 bps (n=187 events across 4 instruments). The seed-robustness check shows ci_low consistently negative (−15.6 to −13.7) and ci_high consistently positive (+18.1 to +20.1) across 8 seeds — the verdict is stable in its INCONCLUSIVE classification, not a seed artifact.
- **Evidence**: `run_metadata.json` (`4h ci_half_width: 17.08`, `seed_robustness_net_cons.4h`)
- **Interpretation**: The absolute estimand has higher variance than the matched-control excess (no control-differencing). With n=187 and per-instrument counts of 36-70, the 4h domain lacks the power to resolve a net effect near zero. This is an honest limitation — the CI width reflects uncertainty, not a positive or negative finding.

## Hypothesis Verdict

**NOT_TRADABLE / INCONCLUSIVE** (per scope definition: phase outcome INCONCLUSIVE because 4h is unresolved).

The cost-bearing tradability gate for EXP-032 (holdout release) is **not passed**. The faithful AVWAP strategy does not show reliable positive net per-event expectancy under the predeclared CONSERVATIVE cost model on the equal-weight cross-instrument binding metric.

## Limitations

1. **BTCUSD cost dominance**: The equal-weight cross-instrument mean is heavily weighted by BTCUSD's 16 bps RT_cons. EURUSD-4h survives costs individually, but this per-instrument result is uncontrolled for multiplicity and cannot be promoted to a binding verdict without a pre-registered experiment.
2. **4h power**: Low event count (n=187) limits the absolute estimand's precision. The INCONCLUSIVE verdict on 4h reflects non-resolution, not absence of signal. A predeclared resolvable-effect threshold was not specified.
3. **Financing/swap excluded**: The scope explicitly excludes financing costs, which are duration-correlated and would be most material on 1h/4h lifetime holds (per the Stage-4 carry-forward note). A positive tradability finding would have required a separate financing-inclusive check before holdout release.
4. **Cost model is not data-derived**: The per-instrument costs are operator-declared constants from typical cTrader retail CFD costs. Real execution may differ, especially for slippage on volatile instruments like BTCUSD.
5. **Absolute estimand has no null calibration**: Unlike the EXP-028 matched-control excess (which uses sign-permutation p-values), the absolute net metric uses a one-sided bootstrap p derived from the bootstrap CDF at zero. This is a CI-equivalent annotation, not a null-calibrated p-value. The binding gate is CI_low > 0, which is assumption-light.

## Alternative Explanations

- **The control discount, not the event edge, costs the strategy**: The matched-control excess is large (+5.78/+23.38/+69.02 bps) while the gross absolute is small (+0.76/+1.46/+10.10 bps). On 5m and 1h, the strategy's raw per-event return barely exceeds the matched control's, so subtracting a round-trip cost from the raw return leaves a large negative. The edge may exist primarily in avoiding bad outcomes (negative control selection), not in generating positive raw P&L.
- **Pyramid legs inflate event counts without proportional edge**: 49% of 5m events and 45% of 4h events are pyramid legs. Each pays a full round-trip cost but may have lower individual edge than the trigger bounce, increasing the per-event cost burden.

## Recommended Next Steps

1. **EXP-031 (edge isolation)**: Run the parallel edge-isolation experiment to decompose the excess into entry-timing vs exit-rule contributions. This runs independently of EXP-030's outcome and delivers mechanism information regardless.
2. **Per-instrument tradability test (new EXP)**: If EURUSD-4h's individual net-positive is worth investigating, a pre-registered experiment with multiplicity control could test tradability on low-cost instruments specifically.
3. **Family review per Phase 007 design §9**: With the tradability gate not passed, the Phase-007 path leads to a family review considering Stage-C branches (/LB /MB /ATR detectors), HYP-001 S/R test, or alternative strategy framings. No holdout release.
