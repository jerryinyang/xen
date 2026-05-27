# Retrospective: Phase 003 ICT One Setup Time-Bar Validation
**Checkpoint:** 2026-05-23-003-ict-one-setup-timebar-validation  
**Experiments:** EXP-012 through EXP-028  
**Design date:** 2026-05-23  
**Retrospective date:** 2026-05-26  
**Status:** Phase Completed - Broad ICT Chain Blocked Before Full-Model Validation  
**Planning spec:** [ict_one_setup_research_spec.md](../../../planning/ict_one_setup_research_spec.md)

---

## 1. Scope

This retrospective evaluates Phase 003 against its design objective: convert the ICT-style "macro + sweep + displacement + IFVG/breaker + second-candle-open + 1:2 risk/reward" thesis into objective, deterministic, time-bar-native experiments.

The phase deliberately did not inherit the prior event-chart thesis. It reused only the canonical 1-minute time-bar timeline, chronological holdout discipline, real-price outcome evaluation, and governance process. All completed Phase 003 experiments preserved the final 30 percent global holdout, used 1-minute time-bar prices for outcomes, avoided event-chart features, and received approved post-experiment governance.

The organizing research question from the checkpoint and planning spec was:

> Does a time-filtered failed-breakout model, confirmed by displacement and objective structure failure, produce evidence of robust post-signal edge after realistic constraints?

The phase answer is negative for the current broad chain. The project successfully translated most discretionary concepts into reproducible components, but the evidence did not promote those components into a full-model candidate.

---

## 2. Experiment Status Summary

| Experiment | Source role | Verdict | Key phase finding |
| --- | --- | --- | --- |
| EXP-012 | Data readiness | SUPPORTED | All 16 macro-family coverage rows exceeded the 0.80 threshold; cost fields were absent and proxy scenarios were documented. |
| EXP-013 | H1 macro windows | REFUTED | Fixed macro windows supported 0 of 4 instruments versus adjacent and random controls. |
| EXP-014 | H2 prerequisite | SUPPORTED | PDH/PDL and ONH/ONL levels were reproducible with train/test availability near or above 0.989 on all instruments. |
| EXP-015 | H2 sweep reversal | REFUTED | Sweep-only failed-breakout behavior supported only EURUSD Test; 1 of 4 instruments met the primary criterion. |
| EXP-016 | Macro-sweep interaction | INCONCLUSIVE | Matched macro-context comparison was underpowered; 0 of 4 instruments met train/test inside and matched-outside floors. |
| EXP-017 | Premium/discount filter | INCONCLUSIVE | Midpoint filter retained 86.2-95.7 percent of test sweeps but improved neither Hit1R nor median MAE on any instrument. |
| EXP-018 | H3 displacement | INCONCLUSIVE | Displacement retained 82.5-87.1 percent of test sweeps but no instrument cleared interval-based improvement thresholds. |
| EXP-019 | H3 swing-break variant | INCONCLUSIVE | Swing-break confirmation had adequate counts and acceptable delays, but did not beat EXP-018 displacement on any instrument. |
| EXP-020 | H4 FVG/IFVG prerequisite | INCONCLUSIVE | FVG/IFVG detection was deterministic, but IFVG inversion occurred on roughly 84-85 percent of FVGs. |
| EXP-021 | H4 IFVG entry quality | REFUTED | IFVG retained nearly the full displacement set and improved neither return nor drawdown enough to pass on any instrument. |
| EXP-022 | H5 breaker prerequisite | SUPPORTED | Candidate A breaker was deterministic and cleared train/test event floors everywhere; Candidate B missed two test floors. |
| EXP-023 | H5 breaker quality | REFUTED | Candidate A breaker passed outcome criteria only on USTEC, despite adequate feasible counts on all instruments. |
| EXP-024 | Execution timing | SUPPORTED | Second-candle-open passed non-inferiority on 4 of 4 instruments, mainly as preservation rather than improvement. |
| EXP-025 | H6 fixed 1:2 risk/reward | INCONCLUSIVE | 2R superiority appeared on 0 of 4 instruments despite full comparator coverage. |
| EXP-026 | Component ablation | INCONCLUSIVE | No optional component had positive Test MeanDiff with CI_Lo > 0; no full-model candidate was selected. |
| EXP-027 | Full-model test | INCONCLUSIVE | EXP-026 manifest was ineligible, so the full-model analysis-set test stopped at the gate. |
| EXP-028 | Robustness/falsification | INCONCLUSIVE | EXP-027 had no eligible candidate, so robustness checks did not open. |

Status counts:

- Supported: 4 experiments (EXP-012, EXP-014, EXP-022, EXP-024), all readiness, definition, or timing-preservation claims.
- Refuted: 4 experiments (EXP-013, EXP-015, EXP-021, EXP-023), all direct outcome or standalone behavior claims.
- Inconclusive (substantive): 7 experiments (EXP-016, EXP-017, EXP-018, EXP-019, EXP-020, EXP-025, EXP-026) — weak effect, sparse matched controls, or non-selective events.
- Inconclusive (gated early exit): 2 experiments (EXP-027, EXP-028) — upstream ablation gate failed, so no model candidate was available for full-model or robustness tests.

The phase did not fail procedurally. All 17 experiments received APPROVE verdicts at both pre-execution and post-experiment governance. The phase completed the planned roadmap and produced a clean no-go decision for the broad model chain.

---

## 3. Thesis-Level Result

The original ICT thesis required a sequence of evidence:

1. Macro windows are special enough to matter.
2. Prior high/low sweeps show failed-breakout reversal behavior.
3. Premium/discount or macro context improves that sweep population.
4. Displacement, IFVG, or breaker confirmation adds measurable signal quality.
5. Second-candle-open execution and a fixed 2R target preserve or improve trade quality.
6. The combined chain earns a full-model analysis-set test and then robustness checks.

Phase 003 did not produce that sequence.

The data-readiness and definition gates passed: the repository has enough 1-minute time-bar coverage for deterministic NY-time experiments, PDH/PDL and ONH/ONL levels can be built, and one objective breaker candidate is reproducible. But the outcome-bearing gates did not pass. Fixed macro windows failed as standalone range-expansion windows; sweep-only failed-breakout behavior was not robust across instruments; midpoint, displacement, swing-break, IFVG, and breaker layers did not add broad validated value; 2R was not justified; and the ablation gate blocked full-model promotion.

The most accurate conclusion is:

> The current objective ICT translation is measurable and auditable, but the broad cross-instrument model chain is not supported by the analysis-set evidence.

---

## 4. Comparative Evaluation

### 4.1 Readiness Components Versus Predictive Components

The phase split cleanly into two classes.

Readiness and reproducibility components performed well:

- EXP-012 showed the current data can support NY-time macro-window presence studies. The weakest macro-family coverage row was USTEC Test PM at 0.9459, and all 16 family rows cleared the 0.80 threshold.
- EXP-014 showed PDH/PDL and ONH/ONL can be computed reproducibly. All-level availability was 0.989-1.000 in test and 0.993-0.994 in train across instruments.
- EXP-022 showed Candidate A breaker can be defined without ambiguity and with adequate counts: EURUSD 140/54, XAUUSD 172/79, BTCUSD 239/66, and USTEC 205/86 train/test.
- EXP-024 showed second-candle-open timing is not statistically worse than confirmation-close under the scoped non-inferiority rule on 4 of 4 instruments.

Predictive or quality-improvement components mostly failed:

- EXP-013, EXP-015, EXP-021, and EXP-023 were refuted.
- EXP-017, EXP-018, EXP-019, EXP-025, and EXP-026 did not clear support thresholds.
- EXP-027 and EXP-028 never opened their substantive tests because the ablation gate failed.

This distinction matters. Phase 003 produced useful infrastructure and definitions, but not a validated strategy model.

### 4.2 H1: Macro Windows

The planning spec expected predefined NY macro windows to show persistent differences in range, volatility, sweep probability, displacement probability, or forward-return shape versus controls.

EXP-013 refuted that expectation under the scoped control design. No instrument passed the primary criterion. Several effects were directionally opposite the macro-window thesis:

- BTCUSD Test vs AdjacentMean: mean difference -0.3547 ATR, CI [-0.5434, -0.1621].
- BTCUSD Test vs RandomControl: mean difference -0.3804 ATR, CI [-0.5853, -0.1745].
- USTEC Train vs RandomControl: mean difference -0.7439 ATR, CI [-0.9031, -0.5853].
- XAUUSD Train vs RandomControl: mean difference -0.5790 ATR, CI [-0.7270, -0.4380].

EURUSD had some positive test medians, but intervals included zero and train/test support was absent. Macro-window sweep frequency was 0.0 under the scoped window-level reclaim definition.

EXP-016 then tested whether macro context improved sweep outcomes. It was inconclusive because the matched comparison collapsed: test inside-window sweep counts were only EURUSD 24, XAUUSD 27, BTCUSD 21, and USTEC 34, while matched outside counts were 2, 4, 1, and 12 respectively.

Assessment: fixed macro windows should not be promoted as a standalone filter or required ICT condition from this phase. Macro context remains unproven, and the matched-control design must be redesigned before any retest.

### 4.3 H2: Liquidity Sweeps

EXP-014 validated level construction, but EXP-015 refuted broad sweep reversal behavior.

The primary 60-minute 1R-before-stop sweep-minus-breach test supported only EURUSD Test:

| Instrument | Test sweep hit | Test breach hit | Bootstrap diff | 95% CI | Supports primary |
| --- | ---: | ---: | ---: | --- | --- |
| EURUSD | 0.607 | 0.472 | +0.134 | [0.001, 0.267] | True |
| XAUUSD | 0.491 | 0.519 | -0.029 | [-0.151, 0.095] | False |
| BTCUSD | 0.453 | 0.570 | -0.117 | [-0.250, 0.018] | False |
| USTEC | 0.444 | 0.396 | +0.048 | [-0.063, 0.160] | False |

Event counts were adequate, so the failure was substantive rather than sample-limited. Test sweep counts were EURUSD 89, XAUUSD 131, BTCUSD 93, and USTEC 160. Weighted test MFE_R means were lower for sweeps than breaches on all four instruments, for example EURUSD 6.788 versus 29.085 and BTCUSD 8.505 versus 34.251.

Assessment: prior high/low sweeps are measurable, but the current sweep-only failed-breakout effect is weak and not portable across instruments. EURUSD may deserve a future instrument-specific branch, but the broad H2 claim does not survive.

### 4.4 Premium/Discount Location

EXP-017 tested the simplest source-spec location rule: high-side sweeps above the previous-day midpoint and low-side sweeps below it.

The midpoint filter was cheap but not useful:

- Retention remained high: 84/89 for EURUSD, 121/131 for XAUUSD, 89/93 for BTCUSD, and 138/160 for USTEC in test.
- Hit-rate differences were negative or near zero on all instruments: EURUSD -0.007, XAUUSD -0.001, BTCUSD -0.014, USTEC -0.036.
- Median MAE improvement did not clear thresholds on any instrument.

Assessment: the prior-day midpoint is not a justified location filter for the current sweep definition. It neither sharpens the population meaningfully nor removes enough poor events to change the decision.

### 4.5 H3: Displacement and Swing-Break Confirmation

EXP-018 tested deterministic candle-body displacement after sweeps. It retained most events but did not establish improvement:

- Test retention was 86.5 percent for EURUSD, 85.5 percent for XAUUSD, 87.1 percent for BTCUSD, and 82.5 percent for USTEC.
- Test hit-rate differences were small: +0.023, +0.024, +0.027, and +0.001.
- Median MAE point estimates were sometimes favorable, but all intervals failed the pass bar.
- The paired delay-cost diagnostic was negative for EURUSD and XAUUSD: DisplacementClose minus SweepClose hit differences were -0.159 and -0.140 with intervals excluding zero on the negative side.

EXP-019 tested causal micro swing-break confirmation against EXP-018. It was operationally feasible:

- Test matched counts were EURUSD 77, XAUUSD 112, BTCUSD 81, and USTEC 132.
- No instrument was flagged for excessive median delay.

But it did not beat displacement on the scoped criteria. Return intervals were extremely wide, and even the better MAE signals did not clear the required lower-bound threshold. XAUUSD and USTEC had positive median-MAE intervals, but their CI lows were 0.022R and 0.186R, below the 0.25R pass rule.

Assessment: H3 remains unresolved in the narrow sense but unsupported for model promotion. Displacement and swing-break rules are computable and not too sparse, but their benefit is too weak or uncertain relative to delay cost.

### 4.6 H4: FVG and IFVG

EXP-020 showed that FVG/IFVG detection is deterministic and abundant, but the IFVG rule is too permissive:

- Reproducibility passed on all four instruments.
- Test counts were very large, including EURUSD 76,629 FVGs / 65,339 IFVGs and BTCUSD 86,626 / 73,784.
- IFVG rates were 0.842-0.853 across every instrument and segment.

That inversion rate means the current close-through lifecycle rule is not selective. It behaves like a common FVG lifecycle state, not a discriminating confirmation event.

EXP-021 confirmed the practical consequence. IFVG retained almost the entire displacement sample: 7 of 8 displacement-to-IFVG rows had identical counts, with only BTCUSD Train dropping from 345 to 344. After feasible-risk cleanup, 0 of 4 instruments passed the support rule. Example test means showed the delay cost clearly: EURUSD IFVG return was -0.823R versus sweep-close +0.791R; XAUUSD IFVG was -0.551R versus sweep-close +0.623R.

Assessment: the current IFVG path is refuted for broad H4 entry-quality use. Future IFVG work must first create a stricter, predeclared selectivity rule; it should not reuse the current rule as a confirmation layer.

### 4.7 H5: Breaker Confirmation

EXP-022 validated Candidate A as the broad objective breaker definition. That was an important definitional success: Candidate A was deterministic, count-eligible, and had zero ambiguity.

EXP-023 then tested Candidate A outcome quality and refuted broad H5:

- Feasible event floors were met on every instrument.
- Only USTEC passed the return, drawdown-adjusted, and MAE gate.
- USTEC Test breaker return was +1.756R versus displacement -2.414R.
- EURUSD and XAUUSD had better point estimates and MAE, but return and drawdown-adjusted intervals crossed zero.
- BTCUSD was largely flat versus baseline.

Assessment: Candidate A is real and testable, but its value is not portable across the four-instrument phase gate. USTEC is the only credible positive branch from this experiment.

### 4.8 Execution Timing and H6 Risk/Reward

EXP-024 is the cleanest positive outcome-bearing result, but its support is intentionally narrow. Second-candle-open cleared non-inferiority on 4 of 4 instruments with adequate counts and no missing-forward-bar failures. This validates the execution timing as acceptable, not as a source of edge.

The point estimates were mixed:

- EURUSD Train improved from -0.329R at confirmation-close to +0.178R at second-candle-open.
- USTEC Test improved from -0.524R to +0.718R.
- BTCUSD Test worsened from -0.055R to -2.670R.
- Hit-rate intervals crossed zero.

EXP-025 then tested fixed 2R. It did not justify the source-spec risk/reward assumption:

- All four instruments were fully comparable.
- Test 2R counts were EURUSD 70, XAUUSD 100, BTCUSD 77, and USTEC 125.
- 2R superiority appeared on 0 of 4 instruments.
- Test mean returns were weaker for 2R than TimeStop60 on all instruments: EURUSD -0.815R versus -0.297R, XAUUSD -0.810R versus -0.092R, BTCUSD -0.474R versus -0.257R, and USTEC -0.918R versus -0.233R.

Assessment: second-candle-open can remain an allowed timing convention, but 2R should not be promoted as a default for this chain.

### 4.9 Component Ablation, Full Model, and Robustness

EXP-026 was the decisive phase gate.

The chain existed:

- Sweep Test counts were EURUSD 84, XAUUSD 116, BTCUSD 86, and USTEC 144.
- Displacement Test counts were EURUSD 72, XAUUSD 105, BTCUSD 71, and USTEC 115.

But no optional component produced robust positive marginal contribution:

- `bootstrap_marginal.csv` contained 0 Test rows with both MeanDiff > 0 and CI_Lo > 0.
- Step 7 second-candle-open ablation rows were negative in point estimate on all four instruments: EURUSD -0.419, XAUUSD -0.121, BTCUSD -0.984, and USTEC -0.101.
- The manifest selected only `["Sweep", "Displacement"]` and set `candidate_eligible = false`.

EXP-027 and EXP-028 correctly stopped at their gates. They should not be cited as model-performance or robustness failures; no model candidate existed to test.

Assessment: the broad Phase 003 model chain is blocked before full-model validation. That is the right outcome under the design rules.

---

## 5. Performance Insights

### 5.1 The Dataset Was Good Enough for Component Research

EXP-012 and EXP-014 removed the most basic feasibility objection. NY-time conversion, macro-family coverage, missing-bar rates, and liquidity-level readiness were sufficient for deterministic component studies. The phase was not invalidated by coverage gaps.

The largest data limitation is transaction cost. The time-bar schema lacks Bid, Ask, Spread, Commission, and Slippage fields. Later cost-sensitive work must use explicit proxy scenarios or collect new data. Because no full candidate survived, the phase did not need to spend robustness work on cost stress.

### 5.2 Sample Size Was Usually Not the Main Failure

Some tests were underpowered by design interaction, especially EXP-016's narrow macro-window plus same-day matched outside control. But most important negative results had adequate counts:

- EXP-015 sweep-only counts cleared test floors on all instruments.
- EXP-017 retained 86.2-95.7 percent of test sweeps.
- EXP-018 retained 82.5-87.1 percent of test sweeps.
- EXP-019 had 77-132 matched test events.
- EXP-021 and EXP-023 cleared feasible-event floors after denominator fixes.
- EXP-025 had full comparator coverage.

The repeated pattern is not "no data." It is "enough data, weak or inconsistent effect."

### 5.3 Several ICT Labels Were Measurable but Not Selective

The most important structural insight is selectivity failure.

- The midpoint filter retained most sweeps and did not improve outcomes.
- Displacement retained most sweeps and produced only small, uncertain improvements.
- IFVG retained almost the entire displacement set because the upstream IFVG inversion rate was 84-85 percent.
- Candidate A breaker retained enough events and helped USTEC, but did not create broad outcome separation.

In practical terms, objective definitions can turn discretionary labels into code, but that does not guarantee they become useful filters. A filter that keeps almost everything is mostly an entry-delay rule.

### 5.4 Confirmation Delay Was a Real Cost

The planning spec treats confirmation as a way to improve entry quality. Phase 003 shows the cost side directly.

EXP-018 found that waiting for displacement worsened matched hit probability versus sweep-close on EURUSD and XAUUSD. EXP-021 found IFVG confirmation often paid delay without selectivity. EXP-025 found fixed 2R exits under the delayed entry source were weaker than simpler time stops in point estimate across all four instruments.

The performance lesson is not that confirmation is always bad. It is that every confirmation layer must be judged as a trade-off between filtering benefit and delay cost. In this phase, the benefit usually did not clear the cost.

### 5.5 Instrument Effects Are Real but Not Enough for Broad Claims

EURUSD and USTEC produced the most interesting isolated positives:

- EURUSD was the only EXP-015 sweep-only support case.
- USTEC was the only EXP-023 breaker-quality support case and had favorable EXP-024 timing point estimates.

XAUUSD and BTCUSD mostly failed broad support gates. BTCUSD in particular was negative in EXP-015 test sweep behavior and weak in breaker outcome comparison.

The correct implication is not to generalize EURUSD or USTEC to all instruments. It is to decide whether a future checkpoint should explicitly become instrument-specific, with narrower success criteria and a fresh scope.

### 5.6 Audit-Driven Fixes Improved Trust

Several later experiments reran or cleaned outputs after denominator and stale-artifact issues:

- EXP-021 filtered 53 of 6,030 delayed-entry rows as infeasible.
- EXP-023 filtered 24 of 2,549 rows as infeasible.
- EXP-024 filtered 61 of 5,526 timing rows as infeasible and confirmed 0 missing-forward-bar cases.
- EXP-027 and EXP-028 removed stale full-run/robustness artifacts and left only early-exit contracts.

These fixes did not manufacture positive results. They made the negative and inconclusive results more trustworthy.

---

## 6. Model Implications

### 6.1 Time-Bar-Native Architecture Is the Correct Base

The phase validates the checkpoint's non-inheritance rule. No event-chart infrastructure was needed. All ICT concepts were tested on the canonical 1-minute real-price timeline, using `CloseTime`, NY-time conversion, and real OHLC path outcomes.

The architecture implication is simple: keep ICT research time-bar-native unless a future scope gives a specific reason to add another view. The previous event-chart thesis remains closed.

### 6.2 The Broad ICT Chain Should Not Become a Model

The current chain fails before model testing. That is stronger than "needs tuning." The phase tested each core component in sequence and found no optional component with robust positive marginal contribution.

Promoting the current chain into a full backtest would violate the checkpoint design. It would amount to treating deterministic definitions as evidence of edge. EXP-026 correctly prevents that.

### 6.3 The Minimum Measurable Baseline Is Sweep + Displacement, Not a Strategy

EXP-026 selected `["Sweep", "Displacement"]` as the remaining baseline, but marked it ineligible. This should be interpreted carefully.

Sweep + Displacement is the minimum measurable event chain that remains available for future comparison. It is not a validated entry model. Any future work that starts from it must add a new predeclared component or restriction and then earn promotion through fresh evidence.

### 6.4 Structural Concepts Need Selectivity Gates Before Outcome Tests

EXP-020 and EXP-021 show why prerequisite selectivity matters. A mechanically reproducible detector can still be useless as confirmation if it triggers too often.

Future component design should include selectivity diagnostics before outcome testing:

- retention rate versus upstream event population;
- event floor after filtering;
- non-tautological rate bounds;
- delay distribution;
- overlap with simpler baselines;
- feasibility of risk denominator after delayed entry.

Without these gates, outcome tests may mostly measure delayed execution on nearly identical events.

### 6.5 Second-Candle-Open Is Allowed but Not Alpha

The second-candle-open rule survived as a timing-preservation result. It can be retained as a practical execution convention when a stronger confirmation event exists.

It should not be used to rescue a weak confirmation event. EXP-024 does not rehabilitate IFVG, breaker, or the full chain.

### 6.6 Fixed 2R Is Not a Default

The planning spec treats 1:2 as the common cited target to validate. EXP-025 did not validate it for the approved entry source. Since 2R showed no superiority on any instrument and had weaker point estimates than TimeStop60 across all four instruments, future models should not inherit 2R by default.

Exit logic should be retested only after a materially stronger entry candidate exists.

### 6.7 The Global Holdout Should Remain Untouched

No Phase 003 candidate survived analysis-set gates. There is no reason to spend the final 30 percent global holdout. The holdout remains reserved for a future model candidate that first earns validation on the analysis set.

---

## 7. Practical Conclusions

### 7.1 Actionable Insights

1. Keep the time-bar-native ICT utilities and approved definitions, but treat them as research infrastructure.
2. Do not promote fixed macro windows as a required model filter.
3. Do not treat PDH/PDL or ONH/ONL sweeps alone as broad reversal edge.
4. Do not carry the prior-day midpoint filter into model selection without a new, tighter location hypothesis.
5. Do not carry the current IFVG rule forward; it is too common to function as confirmation.
6. Do not carry Candidate A breaker as a broad cross-instrument confirmation layer, though USTEC may justify a separate branch.
7. Allow second-candle-open timing only as a non-inferior execution convention paired with a separately validated signal.
8. Do not use fixed 2R as the default exit for this chain.
9. Do not run full-model or robustness tests until a new component earns manifest eligibility.
10. Preserve the global holdout.

### 7.2 Weaknesses, Limitations, and Gaps

- **Transaction costs are not observed.** The current schema lacks bid/ask, spread, commission, and slippage fields. Proxy scenarios exist, but a tradeable model would need explicit cost stress or better data.
- **Macro context remains under-characterized after EXP-016.** H1 was refuted for standalone range behavior, but macro-sweep interaction was underpowered by the matched-control design.
- **Location filtering was too simple.** The midpoint rule was a useful first test but may be too blunt to represent all premium/discount concepts from the planning spec.
- **IFVG selectivity failed before entry quality.** The three-candle FVG plus 120-bar close-through inversion rule was deterministic but too permissive.
- **Breaker evidence was instrument-specific.** USTEC looked different from the other instruments, but the phase was scoped for broad four-instrument support.
- **Outcome horizons were intentionally bounded.** Many experiments used 60-minute outcomes. Longer holds or different exits may behave differently, but should not be added post hoc to this chain.
- **Bootstrap event resampling does not fully model temporal clustering.** The phase used robust simple methods, but future candidate-level work may need stricter temporal block designs.
- **The preferred instruments from the planning spec are not all present.** The phase used EURUSD, XAUUSD, BTCUSD, and USTEC because those were the available repository instruments, not because they fully match the source spec's preferred universe.

### 7.3 Recommended Next Steps

1. **Close the broad Phase 003 chain.** Record that the current cross-instrument "macro + sweep + displacement + IFVG/breaker + second-candle-open + 2R" chain did not earn full-model promotion.
2. **Choose one of two continuation paths, not both at once.**
   - **Instrument-specific ICT branch:** start a new checkpoint focused on USTEC breaker behavior or EURUSD sweep behavior, with explicit instrument-specific success criteria and no claim of broad portability.
   - **Component redesign branch:** start a new checkpoint with one new component hypothesis, such as stricter IFVG selectivity, a different liquidity-level family, or a tighter location rule.
3. **Retest macro-sweep interaction only with a new control design.** If macro context remains important, replace the sparse same-day matched outside comparator with a predeclared less-sparse design.
4. **Require selectivity diagnostics before outcome tests.** Any new confirmation event should first prove it is deterministic, non-tautological, count-eligible, and meaningfully selective.
5. **Delay exit-model work.** Do not compare 2R, liquidity targets, or time stops again until a stronger entry population exists.
6. **Add cost data or formalize proxy stress before tradeability claims.** The project should not describe any ICT result as tradeable until spread/slippage/commission are modeled explicitly.
7. **Keep follow-up scopes small.** The phase showed that broad discretionary chains create many plausible branches. Future work should test one falsifiable improvement at a time.

---

## 8. Phase 003 Success Criteria Assessment

| Phase gate | Assessment |
| --- | --- |
| Data readiness gate | Met. EXP-012 supported coverage, NY-time feasibility, missing-bar diagnostics, and cost-proxy documentation. |
| Definition gate | Mostly met. EXP-014, EXP-020, and EXP-022 produced deterministic definitions, though IFVG selectivity failed. |
| Component characterization gate | Met. H1 through H6 components were tested or gated without collapsing into a premature full model. |
| Ablation gate | Met, negative. EXP-026 assembled the chain and correctly blocked promotion. |
| Full-model gate | Met procedurally. EXP-027 stopped because no eligible candidate existed. |
| Robustness gate | Met procedurally. EXP-028 stopped because no candidate reached falsification. |
| Original thesis alignment | Met. The phase stayed grounded in the planning spec and answered the core question with data-driven component evidence. |

---

## 9. Final Phase Conclusion

Phase 003 achieved its main research purpose: it translated an ICT-style discretionary setup into objective, auditable time-bar experiments and tested the component chain without spending the global holdout or moving the goalposts.

The empirical result is a disciplined no-go for the broad model. The repository can compute macro windows, liquidity levels, sweeps, displacement, FVG/IFVG zones, breaker candidates, second-candle-open entries, and fixed-R exits. But computation is not evidence of edge. The data does not show that the current components combine into a robust cross-instrument post-signal advantage.

The next checkpoint should not be a full-model ICT backtest. It should either narrow to a specific instrument/component signal that actually showed local promise, or redesign exactly one weak component with stronger selectivity criteria. Until then, the valid output of Phase 003 is not a strategy candidate, but a clearer boundary around what the current objective ICT translation does and does not support.

---

## 10. Independent Retrospective Audit

This retrospective was independently audited against source experiment artifacts after drafting. The audit verified the following.

### 10.1 Procedural integrity

- All 17 Phase 003 experiments (EXP-012 through EXP-028) have `governance/pre-execution-review.md` and `governance/post-experiment-review.md` with `VERDICT: APPROVE`.
- All 17 `scope.md` files reference the final 30 percent global holdout exclusion.
- EXP-027 and EXP-028 contain only their early-exit gate artifacts (`results.json`, `model_verdict.json` for EXP-027, `numerical_summary.txt`) and no full-run or robustness outputs, consistent with their gated INCONCLUSIVE status.
- Phase 003 did not inherit event-chart hypotheses or features. Approved time-bar-native infrastructure is the only reuse from prior phases.

### 10.2 Numerical accuracy spot-checks

Cross-checked retrospective claims against source `results.md`/`report.md` files:

- EXP-012 macro-family coverage extrema (USTEC Test PM `0.9459`, BTCUSD Test PM `0.9995`) match `macro_family_coverage_summary.csv` summary.
- EXP-013 ATR-normalized range bootstrap point estimates and CIs for BTCUSD Test (`-0.3547`, CI `[-0.5434, -0.1621]`), BTCUSD Test RandomControl (`-0.3804`, CI `[-0.5853, -0.1745]`), USTEC Train RandomControl (`-0.7439`, CI `[-0.9031, -0.5853]`), and XAUUSD Train RandomControl (`-0.5790`, CI `[-0.7270, -0.4380]`) match `results.md`.
- EXP-014 train all-level availability `0.993-0.994` and test `0.989-1.000` match the per-instrument table.
- EXP-015 EURUSD Test bootstrap diff `+0.134`, CI `[0.001, 0.267]` and per-instrument sweep/breach MFE_R means match the primary outcome table.
- EXP-016 inside/all-outside/matched-outside test counts (`24/65/2`, `27/104/4`, `21/72/1`, `34/126/12`) match the matched comparison coverage table.
- EXP-017 retention `86.2-95.7%`, test hit-rate differences (`-0.007`, `-0.001`, `-0.014`, `-0.036`) match the test-segment primary effects table.
- EXP-018 retention `82.5-87.1%`, test hit-rate differences (`+0.023`, `+0.024`, `+0.027`, `+0.001`), and paired delay-cost diagnostics (EURUSD `-0.159`, XAUUSD `-0.140`) match `report.md`.
- EXP-019 matched counts (`77`, `112`, `81`, `132`) and CI95-low MAE values (`0.022R`, `0.186R`) below the predeclared `0.25R` pass bar match `report.md`.
- EXP-020 IFVG rates `0.842-0.853` and example test counts (EURUSD `76,629` FVGs / `65,339` IFVGs, BTCUSD `86,626` / `73,784`) match `results.md`.
- EXP-021 IFVG-close test mean returns (EURUSD `-0.823R`, XAUUSD `-0.551R`, BTCUSD `-0.055R`, USTEC `-0.524R`) and matching sweep-close baselines (`+0.791R`, `+0.623R`) match `results.md`. Infeasible-row count `53/6030` matches `results.json`.
- EXP-022 Candidate A train/test counts (`140/54`, `172/79`, `239/66`, `205/86`) and Candidate B counts match the chain-waterfall summary, with zero ambiguity everywhere.
- EXP-023 USTEC Test breaker return `+1.756R` versus displacement `-2.414R` and the `1/4 instruments passing` verdict match `results.md`. Infeasible-row count `24/2549` matches.
- EXP-024 timing point-estimate movements (EURUSD Train `-0.329R -> +0.178R`, USTEC Test `-0.524R -> +0.718R`, BTCUSD Test `-0.055R -> -2.670R`) and `61/5526` infeasible-row count match `results.md` and `numerical_summary.txt`.
- EXP-025 fully comparable test counts (`70`, `100`, `77`, `125`) and `2R` versus `TimeStop60` mean differences match `report.md`.
- EXP-026 Sweep and Displacement test counts, the `0` Test rows with both `MeanDiff > 0` and `CI_Lo > 0`, the Step 7 SCO ablation point estimates (`-0.419`, `-0.121`, `-0.984`, `-0.101`), and `selected_components = ["Sweep", "Displacement"]` with `candidate_eligible = false` match `bootstrap_marginal.csv` and `model_manifest.json`.

### 10.3 Validated audit caveats not material to the retrospective

- EXP-019 contains one confirmed cross-segment swing-break event (BTCUSD sweep on Train, break on Test) that is grouped by the sweep segment. The point estimates shift trivially (for example BTCUSD Test direct return diff `1.4771` versus `1.4905`) and the INCONCLUSIVE verdict is unchanged. The retrospective does not need to surface this detail.
- EXP-007's earlier audit-driven cleanups predate Phase 003 and are not relevant to the current retrospective.

### 10.4 Audit verdict

The retrospective is accepted as a faithful and complete synthesis of Phase 003. Status counts, gate assessments, and numerical claims are consistent with the underlying experiment artifacts. The thesis-grounded narrative correctly reports the broad ICT chain as blocked before full-model promotion and identifies two predeclared continuation paths without scope expansion.
