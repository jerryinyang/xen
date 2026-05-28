# Results: Experiment EXP-033

## Summary

None of the five predeclared IFVG/FVG rule families (R1 stricter size, R2 shorter lifecycle, R3 displacement-qualified FVG creation, R4 mitigation-before-inversion, R5 zone-location filter) simultaneously passes the six readiness checks on at least two of the four scoped instruments at 15-minute resolution. The aggregate verdict, applied mechanically per `scope.md` §"Aggregate Verdict", is **Branch B closes at EXP-033 with selectivity-gated no-go**. Per the analysis-plan interpretation guide, the experiment hypothesis is **REFUTED**. Audit verdict was PASS with 0 critical and 0 warning findings; baseline 15-minute FVG counts (3,391-9,283 per segment) and IFVG inversion rates (0.821-0.857) reproduce EXP-029's published reference exactly, and all 40 reproducibility digests match.

## Detailed Findings

### Finding 1: Baseline detection reproduces EXP-029 exactly

- **Observation**: The unfiltered 15-minute three-candle FVG detector with the 120-bar lifecycle produces 3,391-9,283 FVGs and 2,783-7,671 IFVGs per instrument-segment, with inversion rates of 0.821-0.857.
- **Evidence**: `baseline_counts.csv` matches both extremes of EXP-029's published FVG range (3,391 = XAUUSD Test minimum, 9,283 = BTCUSD Train maximum) and all four instruments fall inside the EXP-029 83-86 percent baseline inversion band. Per-instrument values: EURUSD `(8583, 0.853) / (3683, 0.857)`, XAUUSD `(7702, 0.842) / (3391, 0.821)`, BTCUSD `(9283, 0.826) / (4129, 0.845)`, USTEC `(8266, 0.848) / (3483, 0.846)` for `(FVG_count, inversion_rate)` Train / Test.
- **Interpretation**: The detector is operating on the same series and applying the same rule as the EXP-029 reference. Any subsequent rule-induced deviation is attributable to the rule modification, not to detector drift. The baseline also confirms that the count anchor for the selectivity check is well above any practical floor, so Check 4 failures cannot be attributed to baseline-anchor noise.

### Finding 2: Determinism holds across the full pipeline

- **Observation**: Every per-`(rule, instrument, segment)` cell (40 of 40) reports matching FVG and IFVG SHA-256 digests between the canonical pipeline pass and the shuffled-then-resorted-1-minute pass.
- **Evidence**: `reproducibility_digests.csv` shows `DigestsMatch = True` on all 40 rows. The shuffled pass permutes 1-minute rows deterministically with seed 42, re-sorts by `CloseTime` before aggregation, and re-runs the full 1m → 15m → levels → sweeps → FVG → IFVG pipeline.
- **Interpretation**: Aggregation, level computation, sweep detection, FVG/IFVG detection, and all five rule filters are deterministic functions of the canonical (CloseTime-sorted) input. Readiness check 1 (reproducibility) is satisfied on every cell, so any rule failure is a substantive selectivity or count failure rather than a numerical-ordering artifact.

### Finding 3: R1 (stricter size) narrowly misses selectivity on most cells

- **Observation**: A 5x stricter minimum FVG size (`0.10 * ATR_14_15m` vs the baseline `0.02 * ATR_14_15m`) retains 79-83 percent of baseline FVGs, just above the 80-percent ceiling on most cells, while preserving inversion rates of 0.81-0.85 — barely below the baseline.
- **Evidence**: `readiness_table.csv` R1 rows. Selectivity ratios: EURUSD Train 0.829 / Test 0.819, XAUUSD 0.825 / 0.824, BTCUSD 0.799 / 0.805, USTEC 0.826 / 0.821. Only BTCUSD Train (0.799) is at or below the 0.80 ceiling. Inversion rates remain in the 0.81-0.85 range, above the 0.75 upper band on every cell. `Check3InversionBand` and `Check4Selectivity` both fail or are at the boundary across all 8 cells; `PassesAllSixChecks = False` everywhere.
- **Interpretation**: The 0.10 * ATR threshold removes only the smallest gaps, which represent a minority of all FVGs and carry the same inversion propensity as larger gaps. The rule does not change the structural property the experiment is testing for. A meaningfully stricter size threshold would either need to be much larger (which would risk count-floor failure) or to be combined with a structurally different criterion; combinations are out of scope.

### Finding 4: R2 (shorter lifecycle) moves inversion into the band but cannot pass selectivity by construction

- **Observation**: Reducing the lifecycle window from 120 to 24 15-minute bars drops the inversion rate from 0.82-0.86 to 0.64-0.68 — squarely inside the predeclared `[0.55, 0.75]` band — but the rule does not modify FVG creation, so the rule-eligible FVG count equals the baseline (selectivity ratio = 1.0).
- **Evidence**: `readiness_table.csv` R2 rows. Inversion rates: EURUSD Train 0.665 / Test 0.680, XAUUSD 0.653 / 0.652, BTCUSD 0.642 / 0.667, USTEC 0.652 / 0.640. Median delays 4-5 bars (well within the 24-bar bound). `Check3InversionBand = True` on all 8 cells; `Check4Selectivity = False` on all 8 cells; `PassesAllSixChecks = False` everywhere.
- **Interpretation**: R2 successfully demotes the tautological 84-86 percent inversion rate to a meaningful 64-68 percent rate that sits inside the band, exactly matching EXP-029's earlier observation that "lifecycle window duration, not source-bar resolution, drives the high inversion rate". The selectivity check as predeclared in scope is defined on FVG count, not IFVG count, so R2 cannot satisfy it by construction. This is a known structural property of the rule menu (see audit info note 1); the readiness band the rule does satisfy is informative for any future rule-design discussion in a new checkpoint phase.

### Finding 5: R3 (displacement-qualified FVG creation) is the narrowest miss; BTCUSD Train passes all six checks, Test fails Check 3 by 0.017

- **Observation**: Requiring the third FVG candle to satisfy the EXP-018 displacement rule retains 16-22 percent of FVGs (Check 4 PASS) with inversion rates of 0.74-0.78 — at or just above the 0.75 upper bound on most cells. BTCUSD Train is the only cell in the entire 40-cell table that passes all six readiness checks; the matching BTCUSD Test cell narrowly fails Check 3 (inversion 0.767 vs 0.750 upper bound, a 0.017 excess).
- **Evidence**: `readiness_table.csv` R3 rows. Selectivity ratios: EURUSD 0.199 / 0.188, XAUUSD 0.197 / 0.215, BTCUSD 0.162 / 0.182, USTEC 0.196 / 0.209. Inversion rates: EURUSD 0.762 / 0.784, XAUUSD 0.780 / 0.753, BTCUSD **0.737 / 0.767**, USTEC 0.763 / 0.761. `PassesAllSixChecks = True` only on BTCUSD R3 Train; `Check3InversionBand = False` on the other seven cells. The bootstrap 95 percent CI on BTCUSD R3 Test (`bootstrap_inversion_rate.csv`) is `[0.740, 0.802]`, which straddles the 0.75 boundary.
- **Interpretation**: R3 is the only rule that passes the selectivity check while keeping inversion rate close to the upper band. The single-segment BTCUSD Train pass is consistent with the underlying displacement filter behaving as expected (about 20 percent of FVGs survive, with a roughly 10-percentage-point reduction in inversion rate). It does not qualify the instrument per scope, which requires both segments to pass. Across the four instruments, the rule sits structurally near the upper band edge; the band itself was predeclared, so band-narrow misses are negative evidence under the same definition the experiment was authorised to use.

### Finding 6: R4 (mitigation-before-inversion) barely changes inversion rates and cannot pass selectivity by construction

- **Observation**: Requiring at least one bar entering the FVG zone before the inversion bar reduces IFVG counts by about 0.5-2.0 percent versus baseline; the inversion rate drops by at most a few percentage points and stays at 0.80-0.85. FVG count equals baseline (selectivity ratio = 1.0).
- **Evidence**: `readiness_table.csv` R4 rows. Inversion rates: EURUSD Train 0.846 / Test 0.849, XAUUSD 0.834 / 0.808, BTCUSD 0.817 / 0.837, USTEC 0.842 / 0.841. `Check3InversionBand = False` and `Check4Selectivity = False` on all 8 cells; `PassesAllSixChecks = False` everywhere.
- **Interpretation**: Almost every baseline IFVG already passes through a partial-fill state before the inversion candle under the EXP-020 lifecycle definition, so the explicit mitigation requirement is mostly redundant. R4 neither lowers the inversion rate enough to enter the band nor reduces the FVG count (by construction). The rule is not informative under the predeclared readiness framework.

### Finding 7: R5 (zone-location) is the most restrictive filter but does not move inversion rate

- **Observation**: Requiring a prior 15-minute first-touch sweep of PDH/PDL/ONH/ONL within 24 bars AND FVG midpoint within `1.0 * ATR_14_15m` of the swept level retains 11-17 percent of FVGs (smallest retention of any rule, Check 4 PASS) but inversion rates remain at 0.80-0.85.
- **Evidence**: `readiness_table.csv` R5 rows. Selectivity ratios: EURUSD 0.150 / 0.133, XAUUSD 0.139 / 0.148, BTCUSD 0.123 / 0.114, USTEC 0.163 / 0.166. Inversion rates: EURUSD 0.835 / 0.851, XAUUSD 0.830 / 0.810, BTCUSD 0.800 / 0.808, USTEC 0.811 / 0.820. `Check3InversionBand = False` on all 8 cells; `PassesAllSixChecks = False` everywhere.
- **Interpretation**: Proximity to a swept liquidity level does not materially change the inversion propensity of a 15-minute FVG. The rule successfully narrows the event set but inherits essentially the same tautological inversion rate as the baseline. The zone-location filter is not informative under the predeclared readiness framework.

### Finding 8: Aggregate verdict — Branch B closes at EXP-033

- **Observation**: For all five rules, `qualifying_instrument_count = 0`; consequently `rules_in_contention = []` and `selected_rule = null`.
- **Evidence**: `verdict.json` records the verdict string `"Branch B closes at EXP-033 with selectivity-gated no-go"` and the empty contention list. `readiness_table.csv` shows exactly one cell with `PassesAllSixChecks = True` (BTCUSD R3 Train); no instrument has both Train and Test passing under any rule.
- **Interpretation**: Applied mechanically per `scope.md` §"Aggregate Verdict" branch 0 (no rules in contention), the verdict matches the predeclared "no rule is both selective and count-eligible" outcome from `design.md` §"Stop Conditions" for Branch B. The experiment hypothesis is REFUTED. No new EXP-034 entry-quality scope may be created from this experiment under the present readiness framework.

## Hypothesis Verdict

**REFUTED.**

The hypothesis required at least one of the five predeclared rule families to pass all six readiness checks on at least two instruments in both train and test segments. None did. The closest cell (BTCUSD R3 Train) passes all checks at an inversion rate of 0.737, but its matching Test cell narrowly fails Check 3 at 0.767 versus the 0.750 upper band. No single-instrument near-miss authorises advancement under the predeclared 2-instrument floor. The verdict is mechanical and matches the language predeclared in scope.

## Limitations

- The selectivity check (`scope.md` Check 4) is defined on the rule-eligible FVG count relative to baseline FVG count. R2 and R4 modify only the inversion criterion, so they cannot pass Check 4 by construction, regardless of how much they reduce IFVG counts. This is a known scope-formulation property recorded in `audit.md` info note 1; it is not an implementation bug and the readiness framework is not changed post-hoc to accommodate it.
- The inversion-rate band `[0.55, 0.75]` was predeclared in scope to operationalise the "materially below 84-85 percent" and "meaningfully above the symmetric midpoint" requirements from the reflection. R3 sits structurally near the upper band edge; a band that excluded the 0.75-0.80 region by a smaller margin would have produced more cells in band but is not the predeclared rule.
- The experiment evaluates rules independently. Combinations (e.g., R3 ∧ R5, or R2 ∧ R3) are out of scope. A combination that passed all six checks could theoretically exist but would require a separately scoped, separately predeclared experiment.
- The R5 sweep detection uses the EXP-015 first-touch convention adapted to 15-minute bars, which inherits the same buffer and direction rules as the 1-minute version. Tighter or looser sweep definitions are out of scope.
- The block bootstrap is descriptive uncertainty quantification; the readiness verdict uses point estimates per scope. CIs are reported but do not affect the verdict.
- Only four instruments are in scope. The qualifying-instrument floor of 2 is approximately half of the available instrument set; a different instrument set would change the absolute pass threshold while preserving the proportional rule.

## Alternative Explanations

- **The 84-85 percent baseline inversion rate may be a fundamental property of three-candle FVGs over 30-hour lifecycles, not a rule-design accident.** Three of the five rule modifications (R1, R3, R5) reduce the event count without changing the inversion rate; R2 reduces the rate only by truncating the observation window; R4 changes neither dimension materially. If three-candle FVGs are intrinsically prone to eventual close-through given enough time, no plausible rule modification within this family will produce a selective non-tautological IFVG.
- **Zone-location proximity to swept levels (R5) may be a poor selectivity criterion at 15-minute resolution.** Most FVGs near swept levels still inherit the baseline inversion structure. A different zone definition (e.g., proximity to the FVG's own midpoint after a mitigation event, or alignment with displacement-direction) might behave differently but is out of scope.
- **The displacement-qualified FVG (R3) is the only candidate that meaningfully restructures the event set.** Its inversion rate is 8-12 percentage points below baseline. A slightly stricter displacement criterion or a different lifecycle (in combination with R3) might push the rate into the band on more instruments. This is a hypothesis for a future checkpoint, not a re-interpretation of EXP-033.

## Recommended Next Steps

These recommendations are framed as new experiment or checkpoint scopes, not as extensions to EXP-033.

1. **Phase 004 retrospective and Phase 005 design**. Branch A closed at EXP-032 (reflection §10) and Branch B closes at EXP-033. The complete Phase 004 outcome is now defensible: neither the USTEC Candidate A breaker nor any predeclared IFVG rule modification produced an eligible candidate at 15-minute resolution. The natural next step is to write the Phase 004 retrospective and a fresh `design.md` for the next phase before any new EXP scope. The retrospective should explicitly record that both branches closed without a candidate manifest.
2. **New EXP-034 (hypothetical Phase 005)** — IFVG selectivity reframed at the IFVG-event level. A new scope could define the selectivity check on `rule_eligible_ifvg_count / baseline_ifvg_count` rather than on the FVG count, which would credit R2-style rules that reduce inversions without modifying FVG creation. This is a fresh experiment and requires a fresh design.md authorisation; it does not modify EXP-033's readiness framework.
3. **New EXP-035 (hypothetical Phase 005)** — predeclared rule combinations on the same instruments. The most plausible combinations from this experiment's evidence are R3 ∧ R2 (displacement filter with shorter lifecycle) and R3 ∧ R5 (displacement filter with zone proximity). Combinations require their own predeclared parameter sets and their own readiness gates; they cannot be authorised from EXP-033 results alone.
4. **Defer EURUSD sweep deferral re-evaluation**. Reflection §3 already closed the EURUSD sweep deferral at 15-minute via EXP-030's negative evidence. No action is required here.

The preferred outcome per `design.md` §"Expected Phase Outcomes" branch 4 is "Phase 004 closes both branches before holdout and records a clean no-go". EXP-033 produces exactly that outcome on Branch B. The retrospective should record both the no-go and the structural observation that the high inversion rate is intrinsic to the lifecycle-windowed three-candle definition rather than a rule-design problem solvable within the predeclared rule menu.
