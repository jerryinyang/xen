# Results: Experiment EXP-052

**Phase 014-A · HYP-005 · `CF-HA-HARAMI-001/CONFIRM` · signal-interpretation characterisation, direct harami vs `/CONFIRM` entry · 99 cells · TRAIN-only · 0 TEST reads · 0 candidate slots.**

## Summary

The CONFIRM arm is deterministic, causal, and measurable across all 99 cells (17 instruments &times; 6 domains), but it systematically and universally underperforms the DIRECT arm on the gross excursion balance. Every single cell shows CONFIRM worse than DIRECT on median((MFE&minus;MAE)/ATR), with paired `CI_high < 0` in all 99 cells. The median shift is &minus;0.62 ATR units (range &minus;0.95 to &minus;0.35). The secondary symmetric-barrier readout corroborates: DIRECT `r ≈ 0.50` (replicating the EXP-049 null on a harami anchor), CONFIRM `r ≈ 0.34` (adverse bias). Fill rate is moderate (median ~33%, range 27&ndash;42%), meaning most haramis are not confirmed before the ZigZag's own trend-change confirmation fires. The verdict is **CONFIRM_CHARACTERISATION_DELIVERED** — the descriptive comparison is complete. The P11 readout flags a universal negative shift (99 cells, 17 instruments), signalling that the stop-order rule is structurally harmful on this substrate.

## Detailed Findings

### 1. Determinism and Construction Integrity

- **Determinism:** PASS — 0 non-deterministic cells across both passes.
- **Invariants:** all 4 battery items (event well-formedness, stop/fill validity, MFE/MAE validity, causality/TRAIN fence) pass on all 99 cells.
- **Exclusion fractions** (`results/excluded_fractions.csv`): very clean — `no_trend_context` 0&ndash;9, `p4_warmup` 3&ndash;15, `direct_censored` 0&ndash;3 per cell. Well-formedness confirmed.

### 2. Frequency: Fill Rate (moderate)

- **Median fill rate:** 32.8% (Q25&ndash;Q75: 30.8%&ndash;35.4%)
- **Range:** 27.2% (BTCUSD-5m) to 42.1% (US2000-2h)
- **Consistent across domains:** 5m ~28&ndash;30%, higher domains ~33&ndash;42%

Most haramis (~67%) are NOT confirmed before the ZigZag's own trend-change confirmation fires. The confirmation window is tight — the `next_confirm_idx` boundary usually arrives before the stop triggers. See `plots/fill_rate_heatmap.png`.

### 3. Timing: Lead Times Nearly Identical Between Arms

- **DIRECT lead** (`next_confirm_idx &minus; s`): median 3 bars, Q25&ndash;Q75 [3, 4], range [3, 4]
- **CONFIRM lead** (`next_confirm_idx &minus; trigger_idx`): median 3 bars, Q25&ndash;Q75 [3, 3], range [2, 4]
- **Time-to-fill** (`trigger_idx &minus; s`): median 1 bar across all cells (IQR mostly 0)

The confirmation fills happen within ~1 bar of the signal bar (time-to-fill = 1). Since `lead_direct` and `lead_confirm` are both ~3 bars, the confirmation typically fires ~2 bars before the ZigZag confirmation, fills immediately, and then has ~1 bar of remaining lead. The gap between arms is small (~0 bars median difference in lead). See `plots/lead_direct_vs_confirm.png`.

### 4. Primary Outcome: Universal Negative Shift

- **DIRECT** median((MFE&minus;MAE)/ATR): centered near zero (e.g., EURUSD-5m: +0.03, CI crosses 0). Replicates the expectation from EXP-049 — harami entry with random-direction assignment has no systematic edge in gross excursion balance.
- **CONFIRM** median((MFE&minus;MAE)/ATR): systematically negative (e.g., EURUSD-5m: &minus;0.63, CI_high < 0).
- **Paired &Delta; (CONFIRM &minus; DIRECT):** median &minus;0.62, Q25&ndash;Q75 [&minus;0.68, &minus;0.54], range [&minus;0.95, &minus;0.35].
- **P11 readout:** 0 positive-shift cells, 99 negative-shift cells over 17 instruments. `p11_neg_readout: true`.
- **Every single reportable cell (99/99)** has `CI_high < 0` — the negative shift is unanimous across all instruments and domains.

The magnitude is large: ~0.6 ATR units of lost excursion balance. The mechanism is structural: the stop level is at the signal bar's real extreme (High[s] for buy-stop), so entry requires trading through that level, systematically selecting for adverse entry timing. See `plots/mfe_mae_by_arm.png` and `plots/paired_shift_vs_fillrate.png`.

### 5. Secondary Outcome: Symmetric Fav-Before-Adv

- **DIRECT `r`:** ~0.50 across most cells (e.g., EURUSD-5m: 0.504, BTCUSD-5m: 0.508). Replicates EXP-049's null finding — the 1:1 symmetric barrier on a harami anchor is a fair coin.
- **CONFIRM `r`:** ~0.32&ndash;0.35 across most cells (e.g., EURUSD-5m: 0.318, BTCUSD-5m: 0.347). Consistently below the null — the stop-entry shifts the fav-before-adv balance materially toward adverse.
- The `r` readout corroborates the primary finding: CONFIRM entry degrades the outcome distribution.

### 6. Cross-Cell Consistency

The shift is directionally unanimous (99/99 negative) across all 17 instruments and all 6 domains (5m&ndash;4h). No instrument or domain is spared. The per-domain breakdown (`composition_readout.json`) shows 0 positive and 0 flat cells in every domain. The effect is not driven by a subset of instruments or timeframes — it is a systematic property of the stop-order rule on this substrate.

## Verdict

**CONFIRM_CHARACTERISATION_DELIVERED**

The experiment produces complete per-cell frequency, timing, and outcome tables for both arms across all 99 cells with determinism PASS and zero invariant violations. The descriptive comparison is fully delivered.

**P11 readout (non-binding, descriptive only):** The paired `CI_high < 0` in 99/99 cells over 17/17 instruments triggers the negative-shift composition criterion. The CONFIRM arm is systematically harmful — not helpful — on the gross excursion balance versus DIRECT entry on the HA harami substrate.

This readout selects nothing and routes nothing per the scope boundaries. The outcome is input to the 014-B checkpoint desk.

## Limitations

- **Gross only:** MFE/MAE and fav-before-adv are gross excursion metrics. No costs, slippage, commission, or market impact are included. A net-P&L comparison might differ.
- **Descriptive only:** No viability gate, no selection, no hypothesis test. The P11 readout is non-binding colour.
- **TRAIN-only:** Results apply to the first 49% (file-order) of each instrument's history. No TEST or holdout contact.
- **Directional signal not incorporated:** Reversal direction is assigned mechanically from the preceding confirmed ZigZag move. No directional filter or market-regime selection is applied — all haramis enter the comparison regardless of trend strength, context quality, or signal confidence.
- **Single stop rule:** Only one CONFIRM rule was tested (stop at the signal bar's real extreme, fill-or-expire by `next_confirm_idx`). Alternative stop placements (e.g., ATR-based, fractional penetration) or alternative confirmation windows might produce different results.
- **Heiken Ashi substrate for detection only:** HA candles are used for harami detection but all entries, stops, and outcomes use real prices. The harami detection on HA candles is a specific design choice and results may differ with raw-candle harami detection.
- **DE30 coverage:** DE30 broker history ends 2026-01-16; train end is 2024-06-28. Counts derive from DE30's own timeline and are not span-comparable with other instruments.

## Alternative Explanations

1. **The stop level is too tight.** Setting the stop at the signal bar's extreme means entry requires a penetration beyond the harami's range. A softer stop (e.g., halfway through the signal bar, or a fractional ATR extension) might yield different frequency/timing properties. However, the structural property — requiring the market to exceed the harami's extreme — is inherent to any stop-order confirmation approach with a fixed level derived from the signal bar.

2. **The window is too short.** The `next_confirm_idx` cap, while descriptively interesting (it answers "does the harami confirm before the ZigZag flips?"), truncates the confirmation window. An unlimited window would increase fill rate but also change the timing and outcome characteristics — the results might shift if fills happen much later.

3. **Random-direction haramis are not tradeable.** The experiment uses all haramis regardless of directional quality. A directional filter (/STRONG-STAT, /STRONG-HA) could select haramis where the reversal-direction assignment has higher conviction, potentially altering the CONFIRM/DIRECT comparison. EXP-051 explores this.

## Recommended Next Steps

1. **014-B checkpoint desk** — This experiment's output (the universal negative readout) should be reviewed at the Phase 014 checkpoint. The scope explicitly prohibits self-declared routing; routing decisions belong to the desk.

2. **/STRONG variant (EXP-051 analog on CONFIRM):** Apply the STRONG-STAT or STRONG-HA filter to the harami set before comparing DIRECT vs CONFIRM. Does the negative shift persist on high-conviction haramis?

3. **Alternative stop rules:** Test stop levels at fractional penetration (e.g., 50% of the signal bar's range), trailing levels, or ATR-based levels to see if alternative stop placement can recover or improve the excursion balance.

4. **Net-P&L characterisation (014-C or later):** Add costs, slippage, and position sizing to assess whether the DIRECT arm's ~zero-gross-excursion outcome translates to a negative-net expectation, and whether any CONFIRM variant can compensate for its adverse excursion shift through improved timing or frequency.
