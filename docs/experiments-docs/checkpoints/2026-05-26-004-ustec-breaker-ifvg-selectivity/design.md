# Phase 004 Design: USTEC Breaker Validation and IFVG Selectivity Redesign

**Phase:** 004 - USTEC Breaker Validation and IFVG Selectivity Redesign  
**Date:** 2026-05-26  
**Status:** Active  
**Predecessor:** 2026-05-23-003-ict-one-setup-timebar-validation  

## Decision Status

Phase 003 is closed. The broad cross-instrument ICT chain did not earn full-model promotion and must not be reopened without a new candidate-forming result.

Phase 004 explores two deliberately narrow continuation branches:

1. **USTEC Candidate A breaker validation**: test whether the one clear Phase 003 local positive is stable enough to become a future candidate.
2. **IFVG/FVG selectivity redesign**: test whether a stricter objective IFVG rule can become selective before any renewed entry-quality claim.

Before those branches run, Phase 004 introduces a mandatory pre-phase that addresses a structural scope gap identified at Phase 003 close: all ICT component experiments were conducted at 1-minute bar resolution, while ICT concepts have their natural domain validity on 15-minute and higher timeframes. The pre-phase tests whether Phase 003 behavior at 1-minute replicates at 15-minute before branch conclusions are treated as final.

## Phase Structure

Phase 004 is organized into two sequential sub-phases.

**Phase 004A: Timeframe Feasibility (Pre-Phase)**  
Runs first. Three targeted experiments test whether Phase 003 ICT component behavior at 1-minute resolution replicates at 15-minute resolution. Results directly determine whether Phase 004B proceeds as written, is modified, or is redesigned. No Phase 004B experiment scope is created until a mid-checkpoint reflection issues a directive.

**Phase 004B: Branch Execution (Contingent)**  
Runs only after the Phase 004A reflection directive is issued. The two planned branches proceed as described if the pre-phase confirms 1-minute and 15-minute behavior is materially equivalent. If the pre-phase reveals material divergence, branch scopes are revised before any Phase 004B experiment is created. Branch plans below describe the baseline intent; specific experiment designs must incorporate pre-phase findings.

## Phase Objective

Turn the two most actionable Phase 003 follow-ups into a compact, falsification-first experiment batch. The aim is to answer:

> Is there a narrowly defensible candidate in USTEC breaker behavior or stricter IFVG selectivity that is worth a future holdout-preserving model validation checkpoint?

The phase prioritizes falsification over expansion. Each experiment should either eliminate a weak branch quickly or produce a sharper candidate definition with clear eligibility evidence.

## Evidence Inherited From Phase 003

Phase 004 inherits only completed, audited, time-bar-native findings:

- `EXP-022`: Candidate A breaker is deterministic and count-eligible on all four instruments.
- `EXP-023`: Candidate A breaker improves trade quality clearly only on USTEC; broad four-instrument H5 is refuted.
- `EXP-020`: FVG/IFVG mechanics are deterministic and abundant, but the current IFVG inversion rate is about 84-85 percent and too permissive.
- `EXP-021`: the current IFVG confirmation rule improves neither return nor drawdown enough to pass on any instrument.
- `EXP-024`: second-candle-open is an acceptable non-inferior execution timing rule, but not a standalone alpha source.
- `EXP-025`: fixed 2R is not justified for the prior entry source.
- `EXP-026`: the broad component chain produced no eligible full-model candidate.

No event-chart thesis, chart-type feature, broad ICT model claim, or current IFVG confirmation claim carries forward as positive evidence.

The timeframe concern is new post-phase synthesis: all Phase 003 ICT feature detectors ran on 1-minute bars. 15-minute behavior is uninspected and may be materially different, particularly for FVG/IFVG count and selectivity, displacement filtering stringency, and breaker structural reference length.

## Data Scope

Primary data view:

- 1-minute time bars from `data/timebars/`.

**Synthetic 15-minute bars (Phase 004A and Phase 004B as directed by pre-phase):**  
Generated on demand from 1-minute base bars by deterministic OHLC aggregation: first Open, maximum High, minimum Low, last Close, summed TickVolume over contiguous 15-bar windows aligned to clock boundaries. Only complete 15-bar windows are used; partial trailing windows are dropped. The holdout exclusion is applied to the 1-minute series before aggregation; the full dataset must not be aggregated and re-split. The 15-minute series is not a chart-type generator variant; it is a simple resampling. Generated frames are not persisted unless EXP-029 establishes a frequently reused canonical form.

Branch-specific instruments:

- USTEC breaker branch: `USTEC` only.
- IFVG selectivity branch: start with `EURUSD`, `XAUUSD`, `BTCUSD`, and `USTEC` for readiness/selectivity. Outcome tests may narrow only through predeclared eligibility gates, not by return performance.
- Pre-phase experiments: all four instruments unless noted per experiment.

Mandatory exclusions:

- The final 30 percent global holdout remains excluded from all analysis, applied chronologically to the 1-minute series before any aggregation or derived view is generated.
- No tick, bid/ask, spread, commission, or slippage fields are assumed available.
- Cost-sensitive claims use explicit proxy scenarios only.

## Phase Gates

1. **Pre-phase gate**: Phase 004A experiments must complete and a mid-checkpoint reflection must issue a directive before any Phase 004B experiment scope is created.
2. **Mid-checkpoint reflection gate**: after EXP-031, a reflection document assesses whether 15-minute behavior is materially different from Phase 003 and issues branch-specific directives: proceed, modify, redesign, reframe, or close. No Phase 004B work begins until this directive is issued.
3. **Local-positive falsification gate**: USTEC breaker evidence must survive segmentation, concentration, and simpler-control tests before any candidate language is allowed.
4. **Selectivity-before-outcome gate**: IFVG redesign must first prove deterministic, non-tautological, count-eligible, and meaningfully selective. Outcome testing is blocked until this gate passes.
5. **Execution-friction gate**: any candidate branch must withstand delay, entry-price perturbation, stop perturbation, and proxy-cost stress before it can be recommended for a future validation phase.
6. **Convergence gate**: breaker and IFVG branches may be compared or combined only if both branches independently produce eligible candidates.
7. **Holdout gate**: no Phase 004 experiment may inspect or use the final 30 percent global holdout. A future checkpoint must decide whether a candidate is strong enough to spend holdout.

## Planned Experiment Roadmap

The next experiment ID is `EXP-029`.

Candidate IDs are planning placeholders. Actual scopes must still be created one at a time through the research pipeline and may be split if the concrete scope exceeds the complexity budget.

### Phase 004A: Timeframe Feasibility

| Candidate ID | Branch | Question | Decision Use |
| --- | --- | --- | --- |
| EXP-029 | Pre-phase | Does synthetic 15-minute FVG/IFVG detection produce a materially lower inversion rate than the Phase 003 84-85 percent baseline, and does FVG count and event coverage remain adequate for downstream testing? | Determines whether IFVG non-selectivity is a rule-design problem or a resolution problem. |
| EXP-030 | Pre-phase | Does first-touch PDH/PDL/ONH/ONL sweep reversal behavior at 15-minute bar resolution show a different or stronger failed-breakout pattern than Phase 003 found at 1-minute? | Tests whether the EXP-015 cross-instrument refutation and EURUSD partial positive replicate, strengthen, or change at 15-minute. |
| EXP-031 | Pre-phase | Does the USTEC Candidate A breaker chain — sweep, displacement, Candidate A — produce similar or improved trade-quality evidence at 15-minute bars compared to Phase 003 EXP-023 at 1-minute? | Tests whether the Phase 003 USTEC positive was genuine structure or a 1-minute resolution artifact. |

### Mid-Checkpoint Reflection

After EXP-031, a reflection document is issued before any Phase 004B scope is written. The directive must specify Branch A resolution, Branch B resolution, whether IFVG redesign is still needed, and whether any branch is closed.

| Pre-phase finding | Branch A directive | Branch B directive | Notes |
| --- | --- | --- | --- |
| 15-min FVG inversion drops materially below 50% on >=2 instruments AND USTEC breaker positive survives | Proceed at 15-minute. | Proceed at 15-minute, starting with the existing IFVG rule before trying redesigned rules. | Timeframe change may solve IFVG selectivity without rule redesign. |
| 15-min FVG inversion drops materially AND USTEC breaker disappears | Close or reframe Branch A before any further scope. | May proceed at 15-minute if counts and selectivity gates pass. | A 1-minute Branch A continuation would be a weaker microstructure/entry-trigger proxy, not structural breaker validation. |
| 15-min FVG inversion stays high near 84-85% AND USTEC breaker survives | Proceed at 15-minute if event floors pass. | Continue as selectivity redesign; unmodified IFVG remains too permissive. | Branch B redesign must not rely on return outcomes for rule selection. |
| 15-min FVG inversion stays high AND USTEC breaker disappears | Close or reframe Branch A. | Proceed only if the reflection finds a still-defensible selectivity redesign question; otherwise close early. | Both original branch rationales are weakened. |
| 15-min sweep reversal shows new broad positive not seen at 1-minute | Pause Branch A unless still independently supported. | Pause Branch B unless still independently supported. | New sweep evidence triggers redesign before any Phase 004B scope is created. |
| Event counts are inadequate at 15-minute for a critical structural test | Close the affected structural branch or reframe it explicitly as a 1-minute microstructure/entry-trigger proxy with weaker claims. | Same rule for affected IFVG work. | Inadequate 15-minute counts do not automatically justify returning to 1-minute structural claims. |

If 15-minute results are promising and count-eligible, the reflection may open a targeted 1-hour extension for the surviving branch before Phase 004B. This extension must be branch-specific and must not become a broad timeframe sweep.

### Phase 004B: Branch Execution (Contingent on Pre-Phase Directive)

IDs below assume the pre-phase reflection authorizes Phase 004B branch execution without changing the dependency order. If the directive is modify, redesign, reframe, or close, IDs and scopes are adjusted in the reflection document before any of these are created.

| Candidate ID | Branch | Question | Decision Use |
| --- | --- | --- | --- |
| EXP-032 | USTEC breaker | Does the USTEC Candidate A breaker advantage survive time, direction, session, volatility-regime, and level-family segmentation without being concentrated in one narrow pocket? Temporal stability across contiguous analysis-set half-periods is the primary pass/fail criterion; all other dimensions are secondary descriptives. | Fast falsification of the Phase 003 local positive. |
| EXP-033 | USTEC breaker | Does Candidate A add incremental value versus simpler matched controls, including displacement-only, same-count random retained controls, and delay-matched controls? | Determines whether breaker logic adds information or just selects/delays events. |
| EXP-034 | USTEC breaker | Is the USTEC breaker candidate robust to execution delay, entry-price perturbation, inherited-risk floor, stop perturbation, and proxy-cost stress? | Decides whether USTEC breaker can become a future candidate manifest. |
| EXP-035 | IFVG selectivity | Which one stricter predeclared IFVG/FVG rule family, if any, is deterministic, non-tautological, count-eligible, and meaningfully selective? | Blocks outcome testing unless a stricter rule passes readiness. |
| EXP-036 | IFVG selectivity | Does the selected stricter IFVG rule improve entry quality versus sweep-close and displacement baselines enough to justify delay and sample-size cost? | Tests whether stricter IFVG becomes an outcome-bearing component. |
| EXP-037 | IFVG selectivity | If EXP-036 supports the stricter IFVG rule, does that rule survive segment, overlap, delay, and proxy-cost stress without depending on one instrument or one event subtype? | Decides whether strict IFVG can become a future candidate manifest. |
| EXP-038 | Optional convergence | If both branches produce candidates and the selected IFVG rule is eligible on USTEC, do USTEC breaker and strict IFVG behave as redundant, complementary, or conflicting filters on USTEC? Structural overlap must be quantified first: if Candidate A breaker confirmation already subsumes the selected IFVG rule's events in its upstream chain, redundancy is structural rather than empirical and the experiment must account for this before interpreting filter interaction. | Opens only after independent branch eligibility, including USTEC eligibility for IFVG; otherwise skipped. |

## Phase 004A Experiment Summaries

### EXP-029: 15-Minute FVG/IFVG Selectivity Check

- Instruments: all four.
- Data: synthetic 15-minute OHLC from 1-minute base, holdout excluded before aggregation.
- Detector: the same three-candle FVG and 120-bar lifecycle IFVG rule from EXP-020, applied to 15-minute bars without modification.
- Primary metric: IFVG inversion rate at 15-minute versus Phase 003 84-85 percent baseline.
- Secondary metrics: FVG count per instrument, train/test event floors, overlap with displacement-confirmed events.
- Lifecycle sensitivity: the primary comparison uses the same 120-bar lifecycle to test direct timeframe transfer; a secondary 8-bar 15-minute lifecycle sensitivity approximates the original 120-minute elapsed-time window and separates timeframe effects from lifecycle-duration effects.
- Selectivity threshold: inversion rate materially below 50 percent on at least two instruments constitutes a meaningful drop. The reflection uses the actual value, not a binary pass/fail, to calibrate the Branch B directive.
- Selection must not use return or excursion outcomes.

### EXP-030: 15-Minute Sweep Reversal Behavior

- Instruments: all four.
- Data: synthetic 15-minute OHLC. PDH/PDL/ONH/ONL levels inherited from EXP-014 (daily levels are resolution-independent).
- Detection: first-touch sweep and breach events on 15-minute bars, using the same definitional framework as EXP-015 adapted to 15-minute bar close and body logic.
- Primary metric: sweep vs. breach 60-minute 1R-before-stop probability difference, directly comparable to EXP-015.
- Event count gate: report counts before effects; if floors are not met at 15-minute resolution, document the resolution cost and classify the statistical comparison as underpowered before interpreting direction.

### EXP-031: 15-Minute USTEC Breaker Chain

- Instrument: USTEC only.
- Data: synthetic 15-minute OHLC, holdout excluded before aggregation.
- Chain: sweep detection, displacement confirmation, Candidate A breaker — all applied to 15-minute bars.
- Primary metric: Candidate A breaker vs. displacement-baseline expectancy, directly comparable to EXP-023.
- Canonical entry timing: displacement-close at 15-minute resolution.
- Event count gate: if Candidate A breaker train/test floors are not met at 15-minute resolution, the experiment documents the resolution cost and closes the 15-minute path for Branch A without implying the 1-minute result is invalid.

## Branch A: USTEC Candidate A Breaker Validation

*IDs assume pre-phase directive is "proceed." Adjust per reflection if directive is "modify."*

### Rationale

Phase 003 produced one credible local positive: USTEC Candidate A breaker behavior. This does not justify broad ICT promotion, but it is strong enough to test narrowly.

### Success Pattern

This branch is promising only if:

- USTEC effect is not dominated by a single year, month cluster, direction, level family, or volatility regime;
- Candidate A beats delay-matched and same-count controls, not only the original displacement baseline;
- point estimates remain positive after reasonable execution-delay and proxy-cost stress;
- event counts remain adequate after feasible-risk filtering.

**Primary falsification dimension**: temporal stability is the single most important segmentation check. If the effect reverses (negative point estimate) in two or more contiguous non-overlapping half-periods of the analysis set, the branch stops after EXP-032 regardless of other segmentation results. Direction, session, volatility-regime, and level-family segmentation results are secondary descriptives and do not override the temporal-stability decision.

**Canonical entry timing**: EXP-023 measured Candidate A breaker outcomes at displacement-close. EXP-032 and EXP-033 inherit displacement-close as the canonical entry timestamp. EXP-034 may include second-candle-open as a stress variant but must not use it as the primary comparison baseline.

### Control Definitions

The EXP-033 delay-matched control is defined as follows: from the displacement-confirmed event set, retain a deterministic random sample equal in count to the Candidate A breaker subset, drawn to match the breaker's confirmation-delay distribution (same median bars between sweep and entry). The sample must be fixed by a predeclared seed and constructed before results are inspected. This control isolates whether Candidate A breaker logic adds information beyond selecting similarly-delayed displacement events.

### Stop Conditions

Stop the branch after EXP-032 if:

- the USTEC effect reverses (negative point estimate) in two or more contiguous non-overlapping half-periods of the analysis set; this is the primary stop trigger.

Stop the branch after EXP-033 if:

- the delay-matched control matches or exceeds Candidate A's test expectancy, defined as: breaker-minus-delay-control mean return ≤ 0 with a bootstrap CI that does not exclude zero from below;
- same-count random-retention controls explain most of the apparent advantage by the same criterion.

Stop the branch after EXP-034 if:

- proxy-cost or delay stress removes the effect (point estimate turns negative);
- denominator or feasible-risk filters collapse usable counts below the predeclared event floor.

## Branch B: IFVG/FVG Selectivity Redesign

*If the pre-phase directive is "proceed at 15-minute," Branch B tests the existing IFVG rule on 15-minute bars as EXP-035's starting point. The rule family survey below runs only if the unmodified 15-minute rule still fails the selectivity gate.*

### Rationale

The existing IFVG detector is reproducible but too permissive. A redesigned IFVG path must first become selective; otherwise entry-quality tests mainly measure delayed execution on almost the same event set.

### Candidate Rule Families

`EXP-035` may compare a small, predeclared set of rule families for readiness only:

- stricter minimum FVG size relative to prior ATR;
- shorter lifecycle window before inversion;
- displacement-qualified FVG creation;
- mitigation-before-inversion requirement;
- zone-location filter relative to the swept level.

The experiment must not select a rule based on return performance. Selection is allowed only on reproducibility, count floors, non-tautological inversion rate, selectivity, delay, and overlap with simpler baselines. If more than one rule family passes all readiness gates, select the family with the lowest inversion rate. If two families tie on inversion rate, select the one with the higher absolute event count after filtering. Return and excursion metrics must not break ties.

### Readiness Pattern

A stricter IFVG rule is eligible for outcome testing only if it:

- reproduces deterministically on fresh load and shuffled-resorted input;
- reduces the current tautological inversion rate materially below the Phase 003 84-85 percent level;
- preserves enough train/test events for the scoped instrument set;
- filters a meaningful share of upstream events rather than retaining nearly everything;
- has bounded median confirmation delay;
- defines risk denominators without zero-baseline or infeasible-risk collapse.

A stricter rule that passes all readiness gates on only one instrument does not qualify for EXP-036; Branch B stops at EXP-035 and records a selectivity-gated no-go. EXP-036 proceeds only if the same selected rule family passes readiness on at least two instruments.

For optional convergence, the selected IFVG rule must also pass readiness on `USTEC`. A two-instrument pass that excludes `USTEC` may support Branch B generally but cannot open `EXP-038`.

### Stop Conditions

Stop the branch if:

- no rule is both selective and count-eligible;
- the selected rule still overlaps almost entirely with displacement-confirmed events;
- outcome evidence in EXP-036 is explained by delay, risk denominator artifacts, or one unstable segment;
- cost or delay stress removes the effect before candidate-manifest eligibility.

## Methods Standards

- Use chronological analysis-set slicing with the final 30 percent global holdout excluded.
- Apply holdout exclusion to the 1-minute series before aggregation; never aggregate the full dataset and re-split.
- Use the nested train/test split inside the analysis set.
- Prefer descriptive diagnostics, paired comparisons, bootstrap intervals, stratified summaries, and simple placebo/random-retention controls.
- Use real 1-minute OHLC prices for all return, MAE, MFE, stop, and target outcomes even when signals are detected on 15-minute bars. Map 15-minute bar `CloseTime` to the corresponding 1-minute bar for outcome evaluation.
- For 15-minute signal outcomes, the executable outcome clock starts only after the confirming 15-minute candle has closed. Stop, target, MFE, and MAE paths must not use any 1-minute movement inside the confirming 15-minute signal candle.
- Predefine segment labels before results are inspected.
- Treat transaction costs as proxy stress only; do not claim tradeability.
- Report event counts before effect sizes.
- Report retention, overlap, delay, and feasible-risk filtering before interpreting returns.
- Keep experiment-specific variants finite and predeclared. No parameter search against outcome performance.

## Complexity Budget

Per experiment:

- Maximum statistical test families: 3.
- Maximum primary plots: 4.
- Maximum new reusable modules: 1, and only if an existing `python/src/ict_timebar.py` helper or a new `python/src/bar_aggregator.py` resampling utility cannot support the scope cleanly.
- Outcome tests must use bounded tables and plots; do not materialize full holdout or unbounded event-detail tables for plotting.

For the checkpoint:

- Pre-phase target: 3 experiments (`EXP-029` through `EXP-031`).
- Core Phase 004B batch target: 6 experiments (`EXP-032` through `EXP-037`), contingent on pre-phase directive.
- Optional convergence: 1 experiment (`EXP-038`) only if both branches independently pass.
- No exit-model experiment unless a branch first produces a stronger entry candidate.
- No full-model experiment in this checkpoint.

## Explicit Non-Goals

- No broad four-instrument ICT model backtest.
- No reopening `EXP-027` or `EXP-028` without a new eligible manifest.
- No current-rule IFVG entry test at 1-minute.
- No fixed 2R retest.
- No macro-window revival except as a predeclared segment or diagnostic.
- No event-chart features.
- No EURUSD sweep branch in this checkpoint. The EXP-015 EURUSD Test positive (bootstrap diff +0.134, CI [0.001, 0.267]) is explicitly deferred, not closed; it remains available for scoping in a future checkpoint if Phase 004 closes both current branches.
- No optimization of windows, buffers, stops, or targets against analysis-set return performance.
- No timeframe sweep across Daily, 4-hour, 1-hour, and 30-minute bars. The pre-phase targets 15-minute specifically as the lowest ICT-valid structural timeframe with adequate event counts for statistical testing. A targeted 1-hour extension may open only after promising, count-eligible 15-minute results and only for the surviving branch. Other timeframes are out of scope unless the pre-phase reflection explicitly directs otherwise.

## Expected Phase Outcomes

### From Phase 004A

One of the following pre-phase conclusions:

1. **15-minute behavior matches 1-minute**: Phase 003 findings are resolution-stable. Phase 004B proceeds as designed.
2. **15-minute behavior diverges materially**: Phase 004B branch scopes are revised before execution.
3. **15-minute event counts are inadequate for testing**: noted as a resolution limitation; the affected structural branch closes, is redesigned, or is explicitly reframed as a weaker 1-minute microstructure/entry-trigger proxy before any Phase 004B scope is written.

### From Phase 004B

One of the following outcomes is sufficient and useful:

1. **USTEC breaker candidate survives**: Phase 004 creates a narrow USTEC candidate manifest for future validation.
2. **Strict IFVG candidate survives**: Phase 004 creates a redesigned IFVG candidate manifest for future validation.
3. **Both survive independently**: Phase 004 opens the optional convergence test and may recommend a future validation checkpoint.
4. **Neither survives**: Phase 004 closes both branches before holdout and records a clean no-go.

The preferred outcome is not a positive result. The preferred outcome is a defensible decision about whether either branch deserves future validation.

## Immediate Next Step

Scope `EXP-029` as the 15-minute FVG/IFVG selectivity check across all four instruments. The pre-phase must complete and a mid-checkpoint reflection must issue its directive before any Phase 004B scope is created.
