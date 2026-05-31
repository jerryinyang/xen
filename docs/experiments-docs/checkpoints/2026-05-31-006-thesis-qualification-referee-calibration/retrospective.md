# Retrospective: Phase 006 Thesis-Qualification Referee Calibration

**Checkpoint:** 2026-05-31-006-thesis-qualification-referee-calibration
**Experiments:** EXP-037
**Design date:** 2026-05-31
**Mid-phase reflection:** 2026-05-31
**Retrospective date:** 2026-05-31
**Status:** Phase Completed - Referee Calibration Closed After Null-Validity Failure
**Predecessor:** [2026-05-28-005-htf-state-descriptor-differentiation](../2026-05-28-005-htf-state-descriptor-differentiation/retrospective.md)

---

## 1. Scope

Phase 006 changed Xen's object of study from a market thesis to the referee that qualifies trading theses. The motivating problem was real: three major research paths had closed with no candidate manifest, and every rejection was issued by a gate stack whose own error profile had not been measured.

The locked founding question was:

> Can the existing Xen qualification stack's operating characteristics - false-positive rate, power surface, and per-leg pass rates - be measured with enough fidelity that a reject verdict carries trustworthy meaning?

The checkpoint opened with a strict boundary: calibrate the existing EXP-036 closure stack first, do not loosen any gate before measurement, do not re-score closed theses, do not spend the global holdout, and do not design a successor stack until the referee measurement is interpretable.

The phase is now closed after EXP-037. The closure is not a stack-passability ruling and not a market-thesis ruling. It is a methodology result: the first null-calibration attempt validated the harness but failed to produce any trusted operating characteristic, and continuing into amended-null engineering would shift the checkpoint from a useful referee sanity check into a recursive calibration project. That is not proportionate to Xen's research objective.

No EXP-040 scope is created. Stage B power experiments are not opened. EXP-038, EXP-039, and EXP-040 were never instantiated in `python/experiments/`; the authoritative experiment index consumes no ID beyond EXP-037.

---

## 2. Experiment Status Summary

| Experiment | Role | Verdict | Key phase finding |
| --- | --- | --- | --- |
| EXP-037 | Part A null calibration of the frozen EXP-036 reference stack | REFUTED | The harness faithfully reproduces EXP-036, but the predeclared kappa=0 null fails its own realism diagnostics on every realization (`DescriptorPass = 0/450`, `ReturnAutocorrPass = 0/450`), so no trusted FPR or per-leg operating profile exists. |

EXP-037 received post-experiment governance approval. The audit found no critical issues and confirmed holdout exclusion, causal feature timing, real-price returns, deterministic execution, finite zero-denominator handling, and faithful transcription of the EXP-036 stack.

---

## 3. What EXP-037 Established

### 3.1 The harness measured the intended stack

With `seed_index = 0`, EXP-037 reproduced EXP-036's observed verdict field-for-field: `outcome = AGAINST`, `four_bar_neutral_and_control = {1h:[XAUUSD], 4h:[]}`, and control adjudicability on all four instruments at both scoped timeframes. This validates the transcription and preserves the main useful artifact of the phase: `python/src/referee_calibration.py` can run the EXP-036 stack faithfully.

### 3.2 The predeclared null was invalid

The null failed both key realism gates:

- `DescriptorPass = 0/450`. Episode-block resampling created adjacent same-bucket episodes, which the stack then merged. The descriptor episode count collapsed by 35-56%, with `descriptor_max_count_rel_diff` in `[0.39, 0.56]` against a `0.05` tolerance.
- `ReturnAutocorrPass = 0/450`. The gate required zero sign mismatches across 64 lag-1/lag-5 return-autocorrelation cells. Because those autocorrelations are near zero, their signs behave like noise and flip readily under resampling.

Therefore every block length `L in {20, 60, 240}` had `trusted_denominator = 0`. The correct conclusion is no trusted FPR, not low FPR.

### 3.3 The raw rates are not operating characteristics

The untrusted raw run produced `FOR = 0/450`, with cell-level false-pass rates around 4.7-6.0% for the matched-control leg, 1.0-2.0% for the neutral leg, and 0.3-1.2% for both together. EXP-037 correctly labels these as descriptive context only. The invalid descriptor null likely widened bootstrap intervals by reducing independent episode counts, biasing the full-stack pass rate downward.

---

## 4. Phase-Level Decision

The mid-phase reflection responded to EXP-037 by authorizing one amended Stage-A rerun (`EXP-040`) using a first-order Markov episode-label descriptor null and a noise-floored autocorrelation gate. That was internally disciplined: it did not change the frozen evidentiary stack and it bounded the regress to one correction.

The final checkpoint decision is stricter: stop here.

The reason is proportionality. The phase began to answer whether the existing gate stack was too strict or blind. EXP-037 showed that answering that question requires choosing and validating a new null model for descriptor labels, return dependence, control-leg construction, diagnostics, and second-order calibration holdouts. At that point the dominant risk is no longer look-ahead or a weak market thesis; it is academic-finance overengineering: the research starts optimizing the measurement apparatus instead of producing a usable, falsifiable research filter.

Phase 006 therefore closes with this conclusion:

> The existing referee cannot be assigned a trusted operating profile from EXP-037. The attempt to calibrate it exposed a recursive null-construction problem. Xen should keep the simple admissibility protections, but should not continue this checkpoint into amended-null and power-surface calibration.

This does not license loosening gates to rescue prior theses. It means the next research direction should design a simpler operational gate from first principles, or move to a materially different thesis/data source, rather than recursively calibrating the EXP-036 stack.

---

## 5. Lessons and Model Implications

### 5.1 The concern behind Phase 006 was valid

The Phase 005 retrospective correctly identified a real ambiguity: repeated thesis closures could reflect either a useful negative map or a near-impassable analysis-set gate stack. Asking that question was necessary.

### 5.2 Calibration did not become a practical answer

EXP-037 demonstrated that even the "trustworthy" null-calibration half depends on a delicate constructed null. Once the diagnostic gates and the null generator both need repair before any FPR exists, the program is measuring assumptions about the calibration design as much as the referee.

### 5.3 The durable protections are simpler than the referee stack

The parts worth carrying forward are the admissibility protections: holdout exclusion, causal timing, real-price outcomes, timestamp alignment, independent-event denominators, predeclared scope, and simple controls. These prevented false promotion across prior phases and should remain.

### 5.4 The evidentiary gate should be rebuilt smaller

Future gates should avoid nested meta-calibration unless a candidate is close enough to justify it. A practical default should first ask: enough independent events, no look-ahead, real executable prices, train/test sign preservation, improvement over neutral baseline and one naive control, and rough cost survival. Anything more should earn its complexity by changing a real decision.

### 5.5 The global holdout remains intact

No Phase 006 work inspected or spent the final 30 percent global market holdout. No candidate exists for holdout validation.

---

## 6. Phase Gate Assessment

| design.md gate | Assessment |
| --- | --- |
| Spec-before-experiment gate | Met. Deliverable #2 was approved and frozen before EXP-037 scope and code. |
| Species-tagging gate | Met. EXP-037 clearly labels the failed null as a measurement-validity result and never reports raw rates as FPR. |
| Admissibility-fixed gate | Met. No look-ahead, holdout, real-price, timestamp, or inference-unit rule was softened. |
| No-scalar-MDE gate | Met by non-execution. No Stage B power or MDE result was produced. |
| Second-order-holdout gate | Met. Trust was withheld because the second-order trusted denominator was zero. |
| Do-not-loosen gate | Met. No EXP-036 evidentiary threshold or leg was changed. |
| Holdout gate | Intact. The final 30 percent global holdout remains untouched. |
| Referee-only gate | Met. No closed thesis was re-run, re-scored, or rescued. |
| Reflection-before-power gate | Met and then superseded by closure. The reflection did not open Stage B; the retrospective closes the checkpoint before EXP-040 is instantiated. |

---

## 7. Recommended Next Steps

1. **Close Phase 006.** Do not create EXP-040 under this checkpoint. Do not open EXP-038 or EXP-039 Stage B power experiments.
2. **Preserve useful infrastructure.** Keep `python/src/referee_calibration.py` as a faithful EXP-036 stack runner and audit reference, but do not treat its current null calibration as trusted.
3. **Simplify the next gate design.** Start the next checkpoint with a lean admissibility-plus-evidence rule, not a calibrated referee project.
4. **Do not rescue prior theses.** Event-chart, ICT, higher-timeframe descriptor, and referee-calibration conclusions remain closed under their scoped evidence.
5. **Keep the holdout untouched.** Reserve the final 30 percent global holdout for a future candidate that first earns analysis-set validation under a simpler predeclared gate.

---

## 8. Final Phase Conclusion

Phase 006 answered the immediate governance concern negatively: the existing EXP-036 referee stack cannot be given a trusted operating-characteristic profile from the completed calibration attempt. The harness is valid, but the predeclared null is not, and the next step would be null-engineering rather than direct research progress.

The valid output is a boundary around the methodology: Xen should retain strict data and execution discipline, but close the recursive referee-calibration branch. The checkpoint ends with no Stage B, no successor stack, no candidate manifest, no holdout spend, and no trusted §5.6 ruling.
