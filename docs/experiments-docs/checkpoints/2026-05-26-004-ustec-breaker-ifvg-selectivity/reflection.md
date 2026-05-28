# Phase 004A Mid-Checkpoint Reflection

**Phase:** 004 — USTEC Breaker Validation and IFVG Selectivity Redesign
**Sub-phase:** 004A pre-phase (timeframe feasibility) + 004B Branch A 1-hour magnitude gate
**Date:** 2026-05-27 (original); amended 2026-05-27 after EXP-032 completion
**Status:** Reflection directive issued and amended twice. Branch A CLOSED after EXP-032 failed the binding 1-hour magnitude gate (§10). Branch B CLOSED after EXP-033 failed the rule-family readiness survey (§11). Phase 004 is complete with no candidate manifest; the Phase 004 [retrospective.md](retrospective.md) is the governing closure artifact and supersedes the forward-looking directives in §3–§5, §9, and §10.7.
**Predecessor:** [design.md](design.md)
**Phase 004A experiments:** EXP-029, EXP-030, EXP-031
**Phase 004B experiments:** EXP-032 (Branch A binding gate — REFUTED), EXP-033 (Branch B rule-family readiness survey — REFUTED)

---

## 1. Pre-Phase Result Summary

| EXP | Question | Predeclared verdict | Substantive reading |
| --- | --- | --- | --- |
| 029 | Is the IFVG non-selectivity problem a resolution artifact? | AGAINST | 120-bar IFVG rate 83–86% on all 4 instruments at 15m, within 2pp of the Phase 003 1-minute baseline; 8-bar (~2h) lifecycle sensitivity drops rates to 45–48% uniformly. Lifecycle window duration, not source-bar resolution, is the dominant driver of high inversion. |
| 030 | Does sweep-reversal behavior strengthen at 15m? | INCONCLUSIVE | No positive sweep-minus-breach Hit1R_60m on any instrument. EURUSD partial positive from EXP-015 (+0.134) reverses to −0.145 with CI [−0.255, −0.036] excluding zero negatively. BTCUSD consistently negative on both train and test. XAUUSD and USTEC null at both 1m and 15m. |
| 031 | Does the USTEC Candidate A breaker chain hold at 15m? | INCONCLUSIVE (binding: 44% of EXP-023 1m test magnitude vs predeclared 50% threshold) | Train CI [+0.235, +0.837] and test CI [+0.560, +3.636] both exclude zero positively. Train CI is sharper than EXP-023's 1-minute train CI (which included zero). MAE reduction −0.679R train, −1.331R test, both CIs exclude zero. Direction consistent with EXP-023 in both segments. Retention 1.059× vs 1m; counts adequate. |

All three pre-phase experiments received APPROVE at both pre-execution and post-experiment governance. Holdout discipline preserved. The shared `python/src/bar_aggregator.py` resampling module is the only new reusable code introduced.

---

## 2. Mapping to design.md Reflection Table

The combined evidence is closest to the design.md row:

> "15-min FVG inversion stays high near 84–85% AND USTEC breaker survives → Branch A: Proceed at 15-minute if event floors pass. Branch B: Continue as selectivity redesign; unmodified IFVG remains too permissive. Branch B redesign must not rely on return outcomes for rule selection."

The directive does not treat EXP-031 as a clean pass. EXP-031 is positive but still INCONCLUSIVE because it reached 44% of the EXP-023 1-minute test magnitude, below the predeclared 50% comparability threshold. The continuation rationale is narrower: both segments achieve CIs excluding zero positively, the 15m train CI is sharper than the 1m reference, MAE reduction is independently confirmed, direction is consistent with EXP-023, and event floors pass. EXP-032 therefore becomes a binding conditional gate before temporal segmentation, not a validation step after survival is already assumed.

EXP-030's negative sweep evidence does not match the design.md "new broad positive at 15m" row. The relevant consequence — closure of the EURUSD sweep deferral — is recorded below.

---

## 3. Branch Directives

### Branch A — USTEC Candidate A Breaker Validation: **CONDITIONAL PROCEED with one 1-hour pre-segmentation extension**

- The USTEC Phase 003 local positive is directionally preserved at 15m with first-time-clean train CI and independently confirmed MAE reduction, but EXP-031 did not meet its predeclared magnitude-comparability gate.
- One targeted 1-hour analogue of EXP-031 runs before temporal segmentation as a binding magnitude-comparability check. Branch A proceeds to temporal segmentation only if the EXP-032 hard gates in §5 pass. If EXP-032 fails those gates, Branch A stops or is explicitly reframed before any further Branch A scope is created.
- Canonical entry timing remains displacement-close. Stop, risk-feasibility, and outcome conventions inherit from EXP-031 and EXP-023.
- The temporal-stability gate from design.md §"Success Pattern" (effect reverses in ≥2 contiguous non-overlapping analysis-set half-periods) remains the primary falsification dimension once Branch A reaches that stage.

### Branch B — IFVG/FVG Selectivity Redesign: **PROCEED as full rule-family survey at 15-minute**

- EXP-029 establishes that lifecycle window length is the structural driver of high inversion at the design.md rule, but Branch B does not pre-narrow to lifecycle-only.
- The EXP-035 rule-family survey runs the full predeclared menu from design.md §"Candidate Rule Families" (stricter min FVG size relative to prior ATR, shorter lifecycle window, displacement-qualified FVG creation, mitigation-before-inversion, zone-location filter). EXP-029 evidence informs the candidate set (the lifecycle variant is expected to be one of several tested) but does not pre-select.
- Selection rules from design.md remain binding: reproducibility, count floors, non-tautological inversion rate, selectivity, delay, overlap. Returns and excursion metrics must not break ties. If multiple families pass, select the lowest inversion rate; ties broken by absolute event count.
- A passing rule must qualify on at least 2 instruments before EXP-036 opens; USTEC qualification is required only for the optional convergence test (EXP-039 below).

### Closed and deferred items

- **EURUSD sweep deferral closed at 15m.** The deferred Phase 003 EXP-015 EURUSD partial positive (+0.134, CI barely excluded zero) is functionally invalidated at 15m by EXP-030's −0.145 reversal with CI [−0.255, −0.036]. The deferral does not carry into Phase 004B as a candidate target. Future re-opening requires new design evidence; it does not automatically reopen with a fresh checkpoint.
- **No cross-instrument sweep branch.** EXP-030 produced no positive instrument and no broad pattern. The BTCUSD consistent negative is recorded as a hypothesis-agnostic observation; it is not a candidate target because the design.md non-goal "no broad four-instrument ICT model backtest" still holds and a negative-edge inversion would constitute optimization against analysis-set returns.
- **No 1-minute Branch A continuation.** The conditional reading of EXP-031 supports testing the higher-timeframe structural path before segmentation. The 1-minute result is not reopened as a structural claim.

---

## 4. Phase 004B Roadmap (Revised)

design.md §"Phase 004B" explicitly anticipates ID adjustment in this document. The original placeholders shift by one slot to accommodate the EXP-032 1-hour extension.

| New ID | Original ID | Branch | Question | Decision use |
| --- | --- | --- | --- | --- |
| EXP-032 | — (new) | A | Does the USTEC Candidate A breaker chain at 1-hour resolution produce directionally consistent and magnitude-comparable Return_R_60m and MAE_R_60m results versus EXP-031 and EXP-023? | Tests whether EXP-031's 44% magnitude miss reflects 15m noise or evidence weakening. Binding gate before temporal segmentation; failure stops or reframes Branch A before EXP-033. |
| EXP-033 | EXP-032 | A | Does the USTEC Candidate A breaker advantage survive contiguous analysis-set half-period temporal stability, with direction, session, volatility-regime, and level-family segmentation as secondary descriptives? | Primary falsification gate for Branch A. |
| EXP-034 | EXP-033 | A | Does Candidate A add incremental value over displacement-only, same-count random-retained, and delay-matched controls? | Determines whether breaker logic is informative or just selects/delays events. |
| EXP-035 | EXP-034 | A | Is the USTEC breaker candidate robust to execution delay, entry-price perturbation, inherited-risk floor, stop perturbation, and proxy-cost stress? | Decides whether USTEC breaker becomes a future candidate manifest. |
| EXP-036 | EXP-035 | B | Which one stricter predeclared IFVG/FVG rule family, if any, is deterministic, non-tautological, count-eligible, and meaningfully selective on ≥2 instruments at 15-minute? | Blocks outcome testing unless a stricter rule passes readiness. |
| EXP-037 | EXP-036 | B | Does the selected stricter IFVG rule improve entry quality versus sweep-close and displacement baselines enough to justify delay and sample-size cost? | Tests whether stricter IFVG becomes an outcome-bearing component. |
| EXP-038 | EXP-037 | B | If EXP-037 supports the stricter rule, does it survive segment, overlap, delay, and proxy-cost stress without depending on one instrument or one event subtype? | Decides whether strict IFVG becomes a future candidate manifest. |
| EXP-039 | EXP-038 | Optional convergence | If both branches produce candidates and the selected IFVG rule is eligible on USTEC, do USTEC breaker and strict IFVG behave as redundant, complementary, or conflicting filters on USTEC? Structural overlap quantified first per design.md. | Opens only after independent branch eligibility, including USTEC eligibility for IFVG. |

The EXP-038 / 039 convergence test still requires that the selected IFVG rule pass readiness on USTEC specifically (not only on the 2-instrument minimum). The reflection does not change this constraint.

---

## 5. Scope Notes for Upcoming Scopes

### EXP-032 (1-hour USTEC breaker chain)

- Instrument: USTEC only.
- Data view: synthetic 1-hour OHLC from 1-minute base via clock-aligned aggregation, using `python/src/bar_aggregator.py` with a 60-bar window aligned to clock boundaries. Holdout exclusion applied to the 1-minute series before aggregation; partial trailing windows dropped.
- Daily levels inherited from EXP-014.
- Chain unchanged at the rule-family level: sweep → displacement (1.5× body median, close-location filter) → Candidate A breaker. To keep EXP-032 comparable to EXP-031 by elapsed time rather than raw bar count, the Candidate A order-block lookback and breaker-confirmation lifecycle are scaled to 1-hour bar counts as predeclared in the scope.
- Outcome evaluation on real 1-minute prices starting strictly after the confirming 1-hour candle closes. The executable outcome clock must not use 1-minute movement inside the confirming 1-hour signal candle.
- Primary metric: breaker-minus-baseline Return_R_60m with label-stratified bootstrap CIs.
- Secondary metric: breaker-minus-baseline MAE_R_60m.
- Comparability test: same magnitude framework as EXP-031, with both EXP-031 (15m) and EXP-023 (1m) test diffs as references. EXP-032 passes only if all hard gates are met: `>=50` feasible breaker events in train and test; train and test Return_R_60m point estimates are positive; the test Return_R_60m CI excludes zero positively; and the test Return_R_60m point estimate is at least 50% of EXP-031's 15m test diff (`>=0.918R`). Report 50% of EXP-023's 1m test diff (`>=2.088R`) as a stricter reference band, but do not make it binding because EXP-031 already failed that band and EXP-023's reference CI was very wide.
- Event-count floor: ≥50 feasible breaker events on train and test, mirroring EXP-031.
- Stop condition for Branch A: if EXP-032 direction inverts in either segment, event floors fail, the test CI does not exclude zero positively, or the hard 50%-of-EXP-031 magnitude gate fails, Branch A stops before EXP-033 unless a new reflection explicitly reframes the branch.

### EXP-033 (temporal segmentation)

- Inherits the 15-minute USTEC data view from EXP-031 unchanged.
- Predeclared segmentation: contiguous non-overlapping halves of the analysis set, ordered by 1-minute `CloseTime` before aggregation. Direction, session, volatility-regime, and level-family segmentations remain secondary descriptives.
- Stop trigger from design.md remains binding: if the point estimate reverses (negative) in ≥2 contiguous non-overlapping half-periods, Branch A stops after EXP-033 regardless of other segmentation results.

### EXP-036 (IFVG rule-family survey)

- Full predeclared rule-family menu from design.md §"Candidate Rule Families".
- Each candidate rule produces: reproducibility digest, FVG count, IFVG count, train/test inversion rate, train/test event floor flag, overlap with displacement-confirmed events, and median confirmation delay.
- Selection by lowest inversion rate among rules passing all readiness gates on ≥2 instruments; ties broken by absolute event count after filtering. Return and excursion metrics must not influence selection.
- A rule that passes readiness on only one instrument is not eligible for EXP-037; Branch B stops at EXP-036 and records a selectivity-gated no-go in that case.

Remaining experiments inherit design.md scope and conventions without modification.

---

## 6. Complexity Budget Impact

- Branch A: 4 experiments (EXP-032 through EXP-035), one more than design.md baseline.
- Branch B: 3 experiments (EXP-036 through EXP-038), unchanged.
- Optional convergence: 1 experiment (EXP-039), unchanged.
- Total Phase 004B target after reflection: 8 experiments + 1 optional = 9 maximum.
- Per-experiment complexity budgets (max 3 statistical test families, max 4 primary plots, max 1 new reusable module) remain binding per design.md §"Complexity Budget".
- No additional new reusable modules are anticipated; the existing `python/src/bar_aggregator.py` covers 1-hour and 15-minute aggregation for EXP-032 and downstream.

---

## 7. Phase Gates Status

| design.md gate | Status after reflection |
| --- | --- |
| Pre-phase gate | SATISFIED. EXP-029 through EXP-031 complete and audited; reflection issued. |
| Mid-checkpoint reflection gate | SATISFIED by this document. |
| Local-positive falsification gate | PARTIALLY ACTIVE. EXP-032 is a binding magnitude-comparability gate before temporal stability; EXP-033 and EXP-034 remain the segmentation and control falsification gates if EXP-032 passes. |
| Selectivity-before-outcome gate | NOT YET REACHED. Activates in EXP-036. |
| Execution-friction gate | NOT YET REACHED. Activates in EXP-035 and EXP-038. |
| Convergence gate | NOT YET REACHED. Activates in EXP-039 (optional). |
| Holdout gate | INTACT. No Phase 004A experiment touched the final 30% holdout. |

---

## 8. Hypothesis-Agnostic Observations Carried Forward

- The `python/src/bar_aggregator.py` deterministic clock-aligned resampling module is the shared infrastructure for Phase 004A and Phase 004B. Holdout exclusion is applied to the 1-minute series before aggregation everywhere it is used.
- 15-minute IFVG event counts (3,391–9,283 FVGs per segment) are abundant enough to support a full rule-family survey without count-floor pressure on the rule survey itself.
- The 8-bar lifecycle drop (45–48% inversion rate) is unlikely to qualify as a final rule design because it approaches the symmetric midpoint; predeclared selectivity in EXP-036 must define a meaningful inversion floor above zero, not just a maximum.
- 15-minute analysis is expected to have an executable outcome clock that excludes 1-minute movement inside the confirming 15-minute signal candle. This convention from EXP-030 and EXP-031 carries to all 15-minute Phase 004B experiments and to EXP-032's 1-hour analogue.

---

## 9. Immediate Next Step

Scope `EXP-032` as the 1-hour USTEC Candidate A breaker chain analogue of EXP-031, with the constraints specified in §5. The Branch A stop condition in §5 must be applied before any Branch A scope beyond EXP-032 is created.

> **Superseded by §10.** EXP-032 has since been completed and the Branch A stop condition triggered. The current immediate next step is in §10.7.

---

## 10. Amendment — EXP-032 Outcome and Branch A Closure

**Amendment date:** 2026-05-27
**Trigger:** EXP-032 completed with audit PASS and post-experiment governance APPROVE. The predeclared Branch A magnitude gate failed.
**Effect:** Branch A is **closed**. Branch B continues unchanged. Phase 004B IDs renumber. This section supersedes the conditional Branch A directives in §3, §4, §5, and §9 wherever they conflict.

### 10.1 EXP-032 Result Summary

| Aspect | Result | Reference |
| --- | --- | --- |
| Verdict | REFUTED / AGAINST Branch A continuation | [EXP-032 report](../../../python/experiments/EXP-032/report.md) |
| Train risk-feasible breaker events | 143 (floor 50: PASS) | [results.md](../../../python/experiments/EXP-032/results.md) |
| Test risk-feasible breaker events | 62 (floor 50: PASS) | [results.md](../../../python/experiments/EXP-032/results.md) |
| Displacement retention vs EXP-031 | 0.568 (above 0.30 floor) | [results.md](../../../python/experiments/EXP-032/results.md) |
| Train Return_R_60m diff | +0.216R, CI [+0.144, +0.298] | [results.md](../../../python/experiments/EXP-032/results.md) |
| Test Return_R_60m diff | +0.116R, CI [+0.039, +0.220] | [results.md](../../../python/experiments/EXP-032/results.md) |
| Binding gate (>= +0.918R test) | FAIL (~6% of EXP-031 15m test diff) | [scope.md](../../../python/experiments/EXP-032/scope.md) §"Success / Failure Criteria" |
| Train MAE_R_60m diff | −0.157R, CI [−0.226, −0.096] | [results.md](../../../python/experiments/EXP-032/results.md) |
| Test MAE_R_60m diff | −0.159R, CI [−0.327, −0.029] | [results.md](../../../python/experiments/EXP-032/results.md) |
| MFE_R_60m diffs | CIs cross zero in both segments | [results.md](../../../python/experiments/EXP-032/results.md) |

Counts passed and direction stayed positive in both segments. The mechanical failure is on magnitude, not on count collapse or direction reversal. The residual structural finding is a small, consistent MAE reduction of about 0.16R.

### 10.2 Cross-Resolution Magnitude Trajectory

The full Candidate A breaker test-segment trajectory across resolutions, holding USTEC and the same rule family constant:

| Source | Resolution | Test Return_R diff | Comparator predeclared in scope | Gate verdict |
| --- | --- | --- | --- | --- |
| EXP-023 | 1-minute | +4.176R (wide CI, single-instrument positive) | Cross-instrument H5 — REFUTED elsewhere | Local positive only |
| EXP-031 | 15-minute | +1.836R, CI [+0.560, +3.636] | 50% of EXP-023 1m (+2.088R) | FAIL (44%) — INCONCLUSIVE |
| EXP-032 | 1-hour | +0.116R, CI [+0.039, +0.220] | 50% of EXP-031 15m (+0.918R) | FAIL (~6%) — REFUTED |

Magnitude decays by roughly an order of magnitude at each resolution coarsening while direction is preserved. This is consistent with a microstructure-sensitive effect rather than a structural breaker advantage that survives the elapsed-time-scaled chain. A structural breaker effect should not lose this much magnitude under deterministic clock-aligned aggregation when event counts and retention remain adequate.

### 10.3 Branch A Decision: CLOSE

Per scope §"Evidence AGAINST Branch A continuation", failure of the test magnitude gate stops Branch A "unless a new reflection explicitly reframes the branch with weaker claims." The reframe options were considered and rejected:

| Candidate reframe | Substance | Why rejected |
| --- | --- | --- |
| Drawdown-only filter scope | Use Candidate A as an MAE-reducing label rather than a Return_R-enhancing one. | The 1-hour MAE diff is −0.157R / −0.159R (train/test). This is too small to carry a future candidate manifest by itself: it cannot offset the magnitude collapse, and a drawdown-only branch would still depend on selecting an entry path elsewhere. Sustaining 3-4 follow-on experiments for a +0.16R MAE finding violates the design.md preference for falsification over expansion. |
| Microstructure/execution-timing scope | Reopen 1-minute Candidate A as a microstructure entry proxy. | Explicitly forbidden by §3 ("No 1-minute Branch A continuation"). The trajectory in §10.2 also weakens, rather than strengthens, the 1-minute structural claim — the effect concentrates at high resolution, exactly the pattern the original design treated as suspect. |
| New chain redefinition (longer lookback, different breaker definition) | Re-engineer Candidate A on 1-hour data. | This would be parameter tuning against analysis-set return performance, prohibited by design.md "no optimization of windows, buffers, stops, or targets against analysis-set return performance" and Programme Principle "No premature optimisation". |

**Decision:** Branch A is CLOSED at EXP-032. No EXP-033 temporal segmentation (Branch A) is scoped. No follow-on Branch A experiment is scoped. The USTEC Candidate A breaker line of investigation concludes without a candidate manifest.

The MAE reduction is recorded as a hypothesis-agnostic observation (§10.6); it is not a basis for branch continuation.

### 10.4 Branch B Status: PROCEED — UNCHANGED

Branch B (IFVG/FVG selectivity redesign) is independent of the Branch A outcome and proceeds as authorized in §3 and §4. EXP-029's evidence that lifecycle window length drives high inversion still informs the candidate menu without pre-selection.

### 10.5 Phase 004B Roadmap — Revised After EXP-032

The remaining Phase 004B work is Branch B only. Branch A continuation IDs (EXP-033 / 034 / 035 in the §4 table) are not created. Branch B placeholder IDs slide down to fill the next sequence position. The optional convergence experiment is removed because it requires an eligible USTEC breaker candidate.

| New ID | §4 placeholder | Branch | Question | Decision use |
| --- | --- | --- | --- | --- |
| (not created) | EXP-033 | A | — | Branch A closed; temporal segmentation not pursued. |
| (not created) | EXP-034 | A | — | Branch A closed; control comparison not pursued. |
| (not created) | EXP-035 | A | — | Branch A closed; robustness stress not pursued. |
| EXP-033 | EXP-036 | B | Which one stricter predeclared IFVG/FVG rule family, if any, is deterministic, non-tautological, count-eligible, and meaningfully selective on >=2 instruments at 15-minute? | Blocks outcome testing unless a stricter rule passes readiness. |
| EXP-034 | EXP-037 | B | Does the selected stricter IFVG rule improve entry quality versus sweep-close and displacement baselines enough to justify delay and sample-size cost? | Tests whether stricter IFVG becomes an outcome-bearing component. |
| EXP-035 | EXP-038 | B | If EXP-034 supports the stricter rule, does it survive segment, overlap, delay, and proxy-cost stress without depending on one instrument or one event subtype? | Decides whether strict IFVG becomes a future candidate manifest. |
| (removed) | EXP-039 | Convergence | — | Convergence requires both branches; Branch A closed, so no convergence test is scoped. |

Selection rules, readiness gates, instrument-count requirements, and complexity budgets for the remaining Branch B experiments inherit unchanged from §3 and §4. The two-instrument minimum for EXP-034 eligibility and the USTEC-eligibility requirement that previously gated convergence are retained as written, even though convergence is no longer scoped — the USTEC-eligibility note carries forward only as a documented constraint should a future checkpoint reopen convergence under different evidence.

### 10.6 Hypothesis-Agnostic Observations Added by EXP-032

- Candidate A breaker MAE_R_60m reduction (~0.16R, CIs excluding zero in both segments at 1-hour) is consistent across resolutions but is too small in absolute terms to drive a future candidate manifest by itself. Carried forward as a structural observation only.
- The Return_R magnitude trajectory across 1m → 15m → 1h on the same instrument and rule family is order-of-magnitude decay. Future Xen work that detects effects only at high resolution should treat a similar decay pattern under elapsed-time-scaled aggregation as evidence of microstructure-sensitivity rather than structural edge.
- 1-hour displacement retention versus 15-minute remained above 0.50 with adequate breaker-label counts; the magnitude failure is not attributable to count collapse, supporting the elapsed-time-scaled chain as a valid comparability framework even when the substantive verdict is negative.

### 10.7 Updated Immediate Next Step

Scope the next Branch B experiment as the new `EXP-033` (rule-family survey, formerly placeholder EXP-036 in §4). Inherit the predeclared Candidate Rule Families and selectivity gates from design.md §"Candidate Rule Families" and §"Readiness Pattern" and the binding modifications recorded in §3 Branch B and §5 EXP-036.

> **Superseded by §11.** EXP-033 has since been completed and the Branch B stop condition triggered. Phase 004 is closed; the current next step is the Phase 004 retrospective (see §11 and [retrospective.md](retrospective.md)).

### 10.8 Phase Gates Status — Updated

| design.md gate | Status after EXP-032 |
| --- | --- |
| Pre-phase gate | SATISFIED (unchanged from §7). |
| Mid-checkpoint reflection gate | SATISFIED and amended by this section. |
| Local-positive falsification gate | RESOLVED for Branch A: the USTEC Phase 003 local positive does not survive the binding 1-hour magnitude gate; branch closed. Gate remains binding for any future branch that produces a local positive. |
| Selectivity-before-outcome gate | NOT YET REACHED. Activates in new EXP-033 (formerly placeholder EXP-036). |
| Execution-friction gate | NOT YET REACHED. Activates in new EXP-035 (formerly placeholder EXP-038) for Branch B. No Branch A activation will occur. |
| Convergence gate | DEACTIVATED for this phase. Convergence is impossible without a Branch A candidate; reopens only if a future checkpoint produces fresh evidence on both branches. |
| Holdout gate | INTACT. EXP-032 excluded the final 30% holdout before aggregation; no Phase 004 experiment has inspected it. |

---

## 11. Amendment — EXP-033 Outcome and Branch B Closure (Phase Complete)

**Amendment date:** 2026-05-28
**Trigger:** EXP-033 completed with audit PASS and post-experiment governance APPROVE. The predeclared Branch B readiness survey produced no qualifying rule.
**Effect:** Branch B is **closed** with a selectivity-gated no-go. Both Phase 004 branches are now closed; Phase 004 is complete with no candidate manifest. This section supersedes the §10.7 next step.

### 11.1 EXP-033 Result Summary

| Aspect | Result | Reference |
| --- | --- | --- |
| Verdict | REFUTED — "Branch B closes at EXP-033 with selectivity-gated no-go" | [EXP-033 report](../../../python/experiments/EXP-033/report.md) |
| Rule families surveyed | R1 stricter size, R2 shorter lifecycle, R3 displacement-qualified creation, R4 mitigation-before-inversion, R5 zone-location | [results.md](../../../python/experiments/EXP-033/results.md) |
| Qualifying instruments (≥2 floor) | 0 of 4 for every rule; `selected_rule = null` | [verdict.json](../../../python/experiments/EXP-033/results/verdict.json) |
| Cells passing all six readiness checks | 1 of 40 (BTCUSD R3 Train, inversion 0.737); BTCUSD R3 Test fails inversion band at 0.767 vs 0.750 | [readiness_table.csv](../../../python/experiments/EXP-033/results/readiness_table.csv) |
| Baseline reproduction | 15m FVG counts 3,391–9,283/segment and inversion 0.821–0.857 reproduce EXP-029 exactly; all 40 digests match | [results.md](../../../python/experiments/EXP-033/results.md) |

### 11.2 Structural Reading

EXP-033 confirms EXP-029 at the rule level: the ~84–85% inversion rate is intrinsic to the lifecycle-windowed three-candle FVG definition, not a rule-design accident solvable within the predeclared menu. R2 (shorter lifecycle) pulls inversion into the [0.55, 0.75] band but cannot pass selectivity by construction (it modifies the inversion criterion, not FVG creation). R3 (displacement-qualified) is the only rule that meaningfully restructures the event set, but it sits at the upper band edge and qualifies only one segment of one instrument. R1/R4/R5 narrow the count while leaving inversion at baseline.

### 11.3 Branch B Decision: CLOSE

Per design.md §"Readiness Pattern" and §"Stop Conditions", a rule that passes on only one instrument records a selectivity-gated no-go and does not authorize EXP-034. No EXP-034 entry-quality scope or EXP-035 stress scope is created. Branch B concludes without a candidate manifest. EXP-033's own report frames IFVG-event-level selectivity and rule combinations only as future-checkpoint hypotheses, not as authorized continuation.

### 11.4 Phase 004 Status: COMPLETE — Both Branches No-Go

With Branch A closed at EXP-032 (§10) and Branch B closed at EXP-033, Phase 004 reaches design.md Expected Outcome #4: both branches close before holdout with a clean no-go. No candidate manifest exists; the final 30% global holdout remains untouched. This also closes the broader ICT-as-alpha thesis when combined with Phase 003; see the Phase 004 [retrospective.md](retrospective.md) §4 for the thesis-level closure and the two reopenable-only-with-new-evidence corners (Daily/4h HTF structure; IFVG-event-level selectivity).

### 11.5 Updated Immediate Next Step

Phase 004 is closed. The governing closure artifact is the Phase 004 [retrospective.md](retrospective.md). No further Phase 004 scope is created. Phase 005 requires a fresh `design.md` starting from a new (non-ICT) thesis.

### 11.6 Phase Gates Status — Final

| design.md gate | Status after EXP-033 |
| --- | --- |
| Pre-phase gate | SATISFIED (unchanged). |
| Mid-checkpoint reflection gate | SATISFIED and amended by §10 and §11. |
| Local-positive falsification gate | RESOLVED for Branch A (§10.8); no other branch produced a local positive. |
| Selectivity-before-outcome gate | RESOLVED for Branch B: no IFVG rule passed readiness on ≥2 instruments; outcome testing correctly never opened. |
| Execution-friction gate | NOT REACHED. Neither branch produced a candidate to stress-test. |
| Convergence gate | DEACTIVATED (unchanged from §10.8). |
| Holdout gate | INTACT. No Phase 004 experiment inspected or used the final 30% holdout. |
