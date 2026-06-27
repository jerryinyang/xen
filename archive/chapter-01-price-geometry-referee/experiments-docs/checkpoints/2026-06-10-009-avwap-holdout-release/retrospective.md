# Phase 009 Retrospective — HOLDOUT_INCONCLUSIVE (Shot Spent; Margin Did Its Job)

**Checkpoint:** `2026-06-10-009-avwap-holdout-release`
**Status:** **COMPLETED 2026-06-10** — EXP-032 executed once (two-invocation
protocol), audit PASS (0 critical, 0 warnings), post-governance APPROVE.
**Outcome class:** `HOLDOUT_INCONCLUSIVE` (design §6 binding rule; descriptive
label `INCONCLUSIVE_SPANS_ZERO`) — the programme's single sanctioned holdout
read is **SPENT** without confirmation or refutation.
**Follows:** `2026-06-10-008-avwap-clinical-tradability` (G2 SATISFIED →
CLINICAL_TRADABLE; operator selected Package B).
**Candidate family:** `CF-AVWAP-001`, registry slot `CF-AVWAP-001/HOLDOUT-B`
(1-of-1 programme-level holdout shot, consumed).

---

## 1. Why this phase existed

Phase 008 closed its strict gate: EURUSD-4h passed the binding phase-level
Holm-4 family on both admissible routes (EXP-037 FH H\*=12 exit, net +40.56 bps
on TEST, ci_low_1s 21.94 > margin 8.42; EXP-038 BTC-exit baseline, +24.27 bps,
ci_low_1s 15.43 > 3.78). That made exactly one holdout-release checkpoint
admissible, for one operator-selected package. The operator chose **Package B**
(FH H\*=12, all_legs, EXP-037 estimand) over Package A on 2026-06-10 — larger
TEST effect, mechanism understood across EXP-031/033/037 — a selection that was
exclusive and final because the two packages share events.

Phase 009 existed to answer one question, once: does the Package-B candidate
retain positive **net** per-event expectancy on the never-read final-30% holdout
stratum of EURUSD, under the frozen CONSERVATIVE costs (RT 3.0 bps) plus
predeclared financing (0.6 bps/day)? Every parameter was inherited frozen
(EXP-037 `frozen_selection.json`, hash-pinned; frozen EXP-027 inference tail
`e50873d12a9f68d9`); EXP-032 moved only the evaluation stratum. The shot was
declared spent on **any** outcome, with INCONCLUSIVE named in advance as an
expected, honest, power-limited result.

## 2. The experiment and its verdict

| EXP | Role | Verdict | Headline |
| --- | --- | --- | --- |
| **EXP-032** | One-shot holdout confirmation of Package B (EURUSD-4h, FH H\*=12, all_legs) | **HOLDOUT_INCONCLUSIVE — shot SPENT** | n = 27 holdout events (vs ≈15–18 expected). Net per-event expectancy **+20.60 bps**, two-sided 95% CI [−0.39, +42.15]. One-sided bootstrap p = 0.029 ≤ 0.05 (p-gate PASSED) but ci_low_1s = +2.71 bps ≤ predeclared calibration margin m_cell = 4.32 bps (margin condition FAILED). Decomposition: gross +25.26 − RT 3.00 − financing 1.67. Non-binding BTC-exit companion: +2.35 bps on the identical events. Audit PASS; freeze-before-outcome, no-second-read, and seal verified with persisted evidence. |

Against design §6 the verdict is mechanical and exact: not CONFIRMED (margin
failed), not REFUTED (CI upper bound +42.15 > 0), therefore INCONCLUSIVE. No
operator judgment entered the adjudication.

## 3. What the phase established

- **The verdict turned on the calibration margin, not the p-value — and that is
  the margin working as designed.** At the holdout's exact cluster layout (16
  direction×regime clusters, n = 27), the frozen bootstrap's uncorrected dual
  rule (`ci_low_1s > 0` AND p ≤ 0.05) had a *measured* null false-positive rate
  of 0.0715. An uncalibrated read would have "confirmed" at an FPR above
  nominal; the R1.2-analog margin restored 0.050 and correctly withheld the
  claim. The honest statement: positive evidence, insufficient to clear a
  properly calibrated bar at n = 27.
- **Attenuation, not reversal, out of sample.** The holdout point estimate
  (+20.60) landed between the EXP-038 baseline scale (+24.27) and zero, well
  below the EXP-037 TEST point (+40.56) — consistent with ordinary
  winner's-curse attenuation of a selected cell. By design this is
  indistinguishable from a zero-effect process with a lucky stratum (that world
  produces ci_low_1s > 0 with probability ≈ 0.07 here); the predeclared answer
  to that ambiguity is the verdict label itself.
- **Power, not luck, was the limit.** The stratum held 27 events — ~50% more
  than the predeclared 15–18 expectation — and still could not clear the
  margin. Per-event dispersion (~60–70 bps against a +20 bps mean) means this
  design could only confirm effects well above roughly +25 bps net. The design
  §7 power statement anticipated exactly this INCONCLUSIVE zone.
- **The exit-mechanism finding replicated descriptively out of sample.** On the
  identical 27 events the BTC-exit net (+2.35 bps) is again far below the
  FH(12) net (+20.60) — directionally consistent with EXP-031/033/037's
  long-horizon trend-truncation drag. Non-binding, never promotable.
- **The one-shot machinery held end to end.** Two-invocation execution (H1
  freeze → mechanical verification → H2), freeze-before-outcome (manifest
  hash-verified, written 41 s before any H2 artifact, never rewritten),
  verdict-file-last persistence, no-second-read guard active, exactly one
  holdout file opened (EURUSD), BTCUSD/USTEC/XAUUSD seal verifiably intact,
  H2 run regardless of H1 attributes (no selection lever). The audit and all
  post-verdict stages read only persisted artifacts.

## 4. What changed vs the original design

- **Execution addendum (adopted 2026-06-10, pre-execution, via the design §10
  Stage-4 REVISE route).** An external pre-execution review (F01–F05) added:
  a predeclared hard-stop taxonomy (lineage mismatch = blocked / benign
  reportability-flag drift = repairable / environment drift = rebuild — none
  spends the shot before H2 outcome contact); the two-invocation protocol with
  cross-process hash reproduction; verdict-file-last persistence ordering; the
  F04 ex-post-reportability disclosure mandate; and the F05
  calibration-fidelity caveat. **No frozen parameter was touched.**
- **Stage-2 analysis-plan Revision 1** was absorbed before execution under the
  same route. After the freeze, nothing changed: no amendment of any kind
  occurred post-freeze, no hard stop fired, and the run completed first pass.
- Mandatory disclosures landed as required: F04 — the binding population rule
  (`reportable_event`) is ex-post and not identifiable at entry time by a live
  trader (it happened to bind nothing here: 27 events pre- and
  post-reportability); F05 — the margin transports analysis-era variance scale
  (σ_b 57.85, σ_w 29.98 bps) onto the holdout layout, load-bearing only for a
  CONFIRMED verdict, which did not occur; holdout dispersion was visually
  comparable anyway.

## 5. Lessons learned

1. **Calibrate the verdict rule to the realized cell structure, then let it
   bind.** The naive dual rule was measurably anti-conservative (FPR 0.0715 at
   n = 27); the H1-computed margin is what made the verdict honest. Any future
   small-n one-shot read must compute its margin from the realized stratum's
   layout *before* outcome contact — and accept that the margin, not the
   p-value, may decide.
2. **Quote small-n bootstrap p-values only with their measured calibration.**
   boot_p = 0.029 standing alone overstates the evidence; the same machinery's
   null FPR at this structure was 0.0715. This wording rule is now embedded in
   results.md/report.md and should be standard for any sparse-cell inference.
3. **Predeclaring INCONCLUSIVE as an expected outcome bought honesty cheaply.**
   The design §7 power statement, the operator's advance acceptance, and the
   no-refund rule removed every incentive to argue the near-miss. The phase
   closed in one pass with no goalpost movement.
4. **The no-selection-lever rule (H2 runs regardless of H1 attributes) is
   load-bearing.** With 27 events and a computed margin visible after H1, an
   operator with discretion could have declined an unattractive read.
   Predeclaring that declining is not an available action is what keeps the H1
   freeze from becoming a peek.
5. **A pre-execution adversarial review of an irreversible step is worth a
   REVISE cycle.** The addendum's hard-stop taxonomy (guard failures before H2
   never spend the shot) resolved in advance every ambiguity that could have
   forced an improvised — hence contestable — call mid-run. For one-shot
   designs, classify the failure modes before the run, not during it.
6. **Confirm-or-spend thresholds should be checked against realistic
   attenuation at selection time.** The cell could only confirm ≳ +25 bps net;
   ordinary winner's-curse shrinkage from a TEST point of +40.56 lands
   squarely in the INCONCLUSIVE zone. That was disclosed and accepted — but
   future release decisions should weigh "what effect size survives expected
   attenuation" as an explicit input to spending an irreversible read.

## 6. Consequences and open items

- **The holdout shot for `CF-AVWAP-001` Package B is spent, permanently.** No
  second read exists for any package, under any outcome. The Phase 008 TEST
  evidence (net +40.56 bps, adj_p ≈ 0.004) stands as the final word on Package
  B and is **never upgradable** to holdout-confirmed.
- **EURUSD holdout is contaminated-by-disclosure** for any EURUSD-4h
  event-level claim; recorded in all three indexes. The BTCUSD/USTEC/XAUUSD
  holdout seal remains intact and verifiably unread.
- **Routing follows the REFUTED path for resource purposes** (Phase 008 design
  §9 / Phase 009 design §8): return to characterisation, Tier C — Stage-C
  branches and HYP-001 (AVWAP line as direct S/R), which remains OPEN and
  untested with its confound-free framing preserved.
- **cTrader FH-exit parity** (EXP-029 covered only the BTC exit) was the named
  next step only under CONFIRMED; if FH-exit machinery is ever needed for other
  uses, it must be scoped as its own analysis-set-only experiment.
- **Live-tradability caveat stands:** even the unconfirmed estimand conditions
  on ex-post reportability (F04); any future tradability claim on this
  population inherits that conditioning.

## 7. Disposition of artifacts

| Item | Status | Disposition |
| --- | --- | --- |
| EXP-032 | HOLDOUT_INCONCLUSIVE, shot SPENT | Binding verdict final and mechanical; no rerun, sensitivity, or second read admissible. Persisted artifacts (`holdout_verdict.csv`, `holdout_events.csv`, `analysis_fh_nets.csv`, `frozen_holdout_manifest.json`, `run_metadata.json`) are the permanent record; no-second-read guard active. |
| `CF-AVWAP-001/HOLDOUT-B` | COMPLETE — SPENT | Registry row closed with locked consequences; 1-of-1 programme holdout slot consumed. |
| Package B (FH H\*=12, all_legs) | TEST-confirmed, holdout-inconclusive | Phase 008 G2 evidence stands, permanently non-upgradable. |
| Package A (BTC exit) | NOT RELEASED | Excluded by the exclusive operator selection; holdout companion read (+2.35 bps) is descriptive only, never promotable. |
| EURUSD holdout | CONTAMINATED-BY-DISCLOSURE | Closed to EURUSD-4h event-level claims. |
| BTCUSD / USTEC / XAUUSD holdout | SEALED | Never loaded; seal verified by audit (one file opened in H2). |
| HYP-001 (line S/R) | OPEN | Primary Tier-C candidate for the next characterisation phase. |
| Execution addendum | CLOSED (no hard stop fired) | Hard-stop taxonomy and two-invocation protocol retained as the template for any future irreversible read. |

## 8. Redirect — logical next steps (operator-gated)

Phase 008 design §9 Tier C governs. Candidate directions, ranked by the
programme's own findings:

1. **HYP-001 direct S/R test** — the mechanism-level question that survives all
   strategy-form outcomes, with a ready confound-free framing
   (`P(bounce | approach to AVWAP)` vs matched non-AVWAP levels). Analysis-set
   only; three instruments' holdout still sealed behind it.
2. **Stage-C detector/anchor branches** (`/LB` `/MB` `/ATR` `/ANCHOR`) — the
   wider family review if the operator judges the bounce-entry form exhausted.
3. **Optional FH-exit cTrader parity** (analysis-set only, own scope) — only if
   FH-exit machinery is wanted for future candidates.

No tuning was performed in Phase 009; nothing was amended after the scope
freeze; the verdict was computed once, mechanically, from predeclared
constants. The shot is spent, the books are honest, and the programme returns
to characterisation.
