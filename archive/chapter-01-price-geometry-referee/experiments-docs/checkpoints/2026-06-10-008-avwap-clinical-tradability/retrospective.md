# Phase 008 Retrospective — CLINICAL_TRADABLE (G2 Satisfied; Holdout Shot Subsequently Spent INCONCLUSIVE)

**Checkpoint:** `2026-06-10-008-avwap-clinical-tradability`
**Status:** **COMPLETED 2026-06-10** — all Tier-A/B experiments executed and
post-governance APPROVED; both gates adjudicated mechanically
([G1-gate-review.md](G1-gate-review.md), [G2-gate-review.md](G2-gate-review.md)).
**Outcome class:** `CLINICAL_TRADABLE` (design §9) — two cells passed the strict
phase-level G2 family; the holdout-release checkpoint (Phase 009 / EXP-032) became
admissible and was executed. Phase 009 subsequently returned
**HOLDOUT_INCONCLUSIVE, shot SPENT** (see
`../2026-06-10-009-avwap-holdout-release/retrospective.md`), so the phase's
CLINICAL_TRADABLE finding stands at TEST-stratum strength, **permanently
non-upgradable**.
**Follows:** `2026-06-09-007-avwap-tradability-and-isolation` (COMPLETED —
NOT_TRADABLE).
**Candidate family:** `CF-AVWAP-001` (Anchored VWAP on regime pivots).

---

## 1. Why this phase existed

Phase 007 closed NOT_TRADABLE: the edge is real but cost-dominated and relative —
net-negative on 5m/1h under CONSERVATIVE costs, power-unresolved on 4h, with one
descriptive survivor (EURUSD-4h net +12.38 bps, multiplicity-uncontrolled) and a
horizon-dependent exit attribution (EXP-031 UNRESOLVED). For a real-but-cost-dominated
edge the admissible levers are **selectivity** (fewer, better events),
**instrument selection** (cheaper venues), and **capture efficiency** (more gross
per position) — not new signal. Phase 008 tested all three on the existing entry
substrate under the frozen Phase 007 cost model plus a predeclared financing
layer, with the nested TRAIN/TEST split as the anti-overfitting backbone and a
two-speed gate structure: lenient G1 to keep exploring, strict G2 to spend the
one-shot holdout.

## 2. Experiments executed and gate outcomes

| Item | Role | Verdict | Headline |
| --- | --- | --- | --- |
| **D0** | Tier-0 disclosure-synthesis memo (desk) | DELIVERED | Fixed the A1 declared cell set mechanically (EXP-030 disclosure net_cons > 0): EURUSD-4h (primary), USTEC-4h, XAUUSD-1h, fixed-sequence order; recorded every data-dependent design choice. |
| **EXP-034** (A1) | Per-instrument cost-bearing tradability screen (verdict-grade) | **A1_STRICT_PASS (TEST REQUIRED)** | EURUSD-4h SEQUENCE_PASS_ALPHA05: net +11.77 bps, ci_low_1s +3.90, boot_p 0.009. USTEC-4h INCONCLUSIVE_SPANS_ZERO (predeclared power-limited); XAUUSD-1h NOT_TESTED (sequence stopped). Per the F02 amendment, the strict pass routed to a TEST confirmation rather than opening the holdout. |
| **EXP-033** (A2) | TRAIN-only horizon sweep: s_entry(H) + FH(H) net curve (DIAG-004, 0 slots) | MEASUREMENT_COMPLETE | Closed EXP-031's unresolved attribution: stable crossover at 5m H=3, 1h H=4. FH net grid max ≤ 0 on 5m/1h (B2 ineligible); 4h eligible (grid max +45.79 bps) with **H\* fragile** (split-half argmax 24 vs 12) — disclosed, triggering the R1.4 robustness tie-break. |
| **EXP-035** (A3) | TRAIN-only conditioning characterisation (DIAG-005, 0 slots) | CHARACTERISATION_DELIVERED | **Zero of 9 domain×dimension cells G1-qualify** — binding leg is materiality: no bin reaches positive absolute net under frozen costs + financing (closest: 5m %completion, SNR 1.42, structured + stable, but candidate-bin net −7.07 bps). The selectivity lever is empty on this substrate. |
| **G1** | Lenient gate (Tier A → Tier B) | **QUALIFIED** | Tier B opened for exactly two 4h reads: the EURUSD-4h A1-cell TEST confirmation (0 slots) and EXP-037 `/EXIT-FH` (1 slot). `/COND` closed; 5m and 1h closed for Tier B. FLAT unreachable from here. |
| **EXP-036** (B1) | `/COND` conditioned variant | **NOT_EXECUTED** | Precondition not met (zero qualified dimensions); slot not consumed. |
| **EXP-037** (B2) | `/EXIT-FH` fixed-horizon exit, 4h, one-shot TEST (1 slot) | **EXIT_FH_TEST_PASS (G2 binding, EURUSD-4h)** | TRAIN-frozen H\*=12, all_legs (R1.4 tie-break over H ∈ {4,6,8,12}). TEST: EURUSD-4h net +40.56 bps, ci_low_1s 21.94 > margin 8.42, phase Holm-4 adj_p ≈ 0.004 — PASS. XAUUSD-4h margin-bound fail (11.45 < 54.2); USTEC-4h fail (boot_p 0.244). |
| **EXP-038** | EURUSD-4h A1-cell TEST-stratum temporal-stability subsample check (0 slots) | **A1_CELL_TEST_PASS (G2 binding)** | BTC-exit baseline estimand on TEST: net +24.27 bps, ci_low_1s 15.43 > margin 3.78, adj_p ≈ 0.004 — PASS. LOCO robust (min ci_low_1s 13.25), seed-stable, TRAIN-stratum nomination precondition met. Relabeled per R1.7: a dependent subsample check, weaker than "out-of-sample". |
| **G2** | Strict gate (phase-level Holm-4 family + R1.2 margins) | **SATISFIED → CLINICAL_TRADABLE** | 2 of 4 family members pass both conditions (both EURUSD-4h). EXP-032 became admissible; the operator selected **Package B** (FH H\*=12, all_legs; EXP-037 estimand) — exclusive and final, since the packages share events. |

Against design §9 the CLINICAL_TRADABLE row is met exactly: ≥1 Tier-B variant
passed strict G2.

## 3. What the phase established

- **Of the three levers, only capture efficiency (and only on EURUSD-4h)
  delivered.** Selectivity is empty — no conditioning dimension produces a
  positive-net stratum anywhere (EXP-035, 0/9). Instrument selection alone is
  insufficient — the A1 strict pass needed TEST confirmation, and the other two
  declared cells failed or were power-limited. Capture efficiency is real on 4h:
  replacing the trend-truncating BTC exit with a TRAIN-frozen fixed horizon
  raised EURUSD-4h TEST net from +24.27 (BTC exit) to +40.56 bps (FH H\*=12) on
  essentially the same events.
- **The EXP-031 attribution puzzle is closed.** The s_entry(H) crossover is
  located and stable (5m H=3, 1h H=4); the long-horizon exit drag EXP-031
  flagged is confirmed as the mechanism the FH exit removes — measured on TRAIN
  (EXP-033), confirmed one-shot on TEST (EXP-037), and later replicated
  descriptively on the holdout stratum (EXP-032 companion: BTC +2.35 vs FH
  +20.60 bps).
- **5m and 1h are closed for this entry substrate.** FH grid maxima ≤ 0, no
  qualifying conditioning stratum, and Phase 007's net-negative verdicts —
  three independent reads agree. The design §7.8 expectation (5m survives only
  under extreme selectivity, which doesn't exist) was borne out.
- **The strict gate's calibration machinery changed verdicts.** The R1.2
  small-n margins were decisive twice: XAUUSD-4h had adj_p ≈ 0.004 and a
  positive lower bound (+11.45) yet failed its margin (54.2 — a thin, dispersed
  cell where the uncorrected bootstrap is severely anti-conservative); and the
  same machinery, inherited by Phase 009, later correctly withheld
  HOLDOUT_CONFIRMED. Without R1.2, Phase 008 would have promoted a fragile
  XAUUSD claim and Phase 009 would have over-claimed.
- **Final standing of the candidate:** Package B is TEST-confirmed
  (CLINICAL_TRADABLE) but holdout-inconclusive with the shot spent — the
  TEST-stratum evidence is the programme's final, permanently non-upgradable
  word on `CF-AVWAP-001` Package B. Package A was never released.

## 4. What changed vs the original design

All amendments were pre-execution, recorded in design §8.4/§11 before the reads
they governed:

- **F02 (pre-Tier-A):** A1 strict pass demoted to necessary-but-not-sufficient —
  the weakest evidential path (in-sample, disclosure-selected cells) no longer
  carries the most expensive consequence. This created the EXP-038 TEST
  confirmation route. Also F01 (A1 one-sided α clarified), F08 (EXP-033
  containment rule).
- **Revision R1 (pre-TEST, adversarial review of EXP-037/038):** R1.1 phase-level
  Holm-4 G2 family with desk adjudication in `G2-gate-review.md` (no experiment
  may self-declare `g2_satisfied`); R1.2 small-n null calibration with mechanical
  margins; R1.3 unified TRAIN/TEST boundary (1-minute-row timestamp); R1.4 H\*
  robustness tie-break after EXP-033 disclosed `h_star_stable = false`
  (second-generation data-dependent, registry-labeled); R1.5 spill containment;
  R1.6 freeze-recovery semantics; R1.7 EXP-038 relabel + nomination precondition
  + LOCO diagnostic.
- One in-adjudication correction: the G2 Holm computation was corrected during
  the binding desk review (monotonicity enforcement); no pass/fail state
  changed.

No cost or financing constant was iterated after freeze; no TEST stratum was
read more than once per registered variant; the slot budget closed at 1 of ≤2
Tier-B slots consumed.

## 5. Lessons learned

1. **Demote in-sample routes before they matter (F02).** The original §8.4 would
   have let a disclosure-selected, same-data A1 pass open the holdout. Catching
   this pre-execution converted it into the EXP-038 TEST check — which then
   passed, so the demotion cost nothing and bought genuine stratum-level
   evidence. Gate routes should be ranked by evidential strength, not
   convenience, before any result exists.
2. **Adjudicate multi-experiment gates once, at the phase level, on desk (R1.1).**
   Two G2 routes on overlapping events at independent α would have nearly
   doubled the false-pass probability of "holdout becomes admissible". A single
   predeclared Holm family with a desk artifact as the binding adjudicator — and
   experiments forbidden from self-declaring gate satisfaction — is the
   transferable pattern.
3. **Calibrate small-n inference at the realized cell structure, every time
   (R1.2).** The frozen bootstrap was honest at n≈187 and anti-conservative at
   n≈11–27. The mechanical margin flipped XAUUSD-4h to fail and later kept the
   holdout read honest. Any future per-cell verdict at n below ~30 must carry a
   matched-structure null calibration.
4. **Disclose selection fragility and handle it with a mechanical rule, not
   discretion (R1.4).** EXP-033's `h_star_stable = false` could have been waved
   through (pick H=24) or agonized over. The predeclared robustness tie-break
   (max-min over split halves, smaller-H tie rule) resolved it with zero
   discretion, and the chosen H\*=12 passed TEST. The honest cost — labeling the
   rule second-generation data-dependent in the registry — was paid explicitly.
5. **Lenient-continue / strict-promote two-speed gating worked as designed.**
   G1 kept USTEC-4h alive into the domain-level B2 read (where it cleanly
   failed) without ever risking promotion on a wide CI; G2 promoted only
   tight-CI, margin-cleared TEST results. No branch was closed on noise; none
   was promoted on it either.
6. **Honest power statements prevent post-hoc disappointment from becoming
   iteration.** USTEC-4h's INCONCLUSIVE was predeclared as the likely outcome at
   n≈47; XAUUSD's margin failure reflects dispersion the scope acknowledged.
   Neither triggered a cost-model or population revisit, because the design had
   already said what failure would look like.
7. **(Carried from Phase 009.)** Even a strict TEST gate at this n confirms
   point estimates subject to winner's-curse attenuation: the selected +40.56
   landed at +20.60 out of sample. Future G2-style thresholds should weigh
   expected attenuation when deciding what effect size justifies spending an
   irreversible read.

## 6. Open items

- **HYP-001 (AVWAP line as direct S/R) remains OPEN** — Tier C's parallel-science
  track, never opened in this phase. The Phase 007 design §8 confound-free
  framing is still the ready scope.
- **Stage-C branches** (`/LB` `/MB` `/ATR` `/ANCHOR`) remain registered and
  unexplored; Tier C is now the active path after the spent holdout shot.
- **`/COND` selectivity is closed for this substrate, not for the family** — a
  different entry substrate (Stage-C branch) could reopen conditioning with new
  dimensions, as a new registered scope.
- **cTrader parity of the FH exit** (EXP-029 covered only the BTC exit) is
  unvalidated; required (analysis-set only) before any live consideration of
  FH-exit machinery, though the holdout outcome removed the immediate driver.
- **XAUUSD-4h is margin-bound, not refuted** — positive lower bound, extreme
  small-n dispersion. Only a substantially larger event population (new data or
  a coarser-grain redesign) could resolve it; no second read of this TEST
  stratum is admissible.
- **5m/1h are closed for this entry substrate** under all three levers.

## 7. Disposition of artifacts

| Item | Status | Disposition |
| --- | --- | --- |
| D0 memo | DELIVERED | Declared-cell record and data-dependent-choice ledger; basis for A1 family. |
| EXP-033 | MEASUREMENT_COMPLETE | Crossover map (5m H=3, 1h H=4) and FH net curves retained; H\* fragility disclosure triggered R1.4. DIAG-004, 0 slots. |
| EXP-034 | A1_STRICT_PASS (TEST REQUIRED) | EURUSD-4h routed to EXP-038; USTEC power-limited; XAUUSD-1h not tested. 0 slots. |
| EXP-035 | CHARACTERISATION_DELIVERED | Selectivity lever measured empty (0/9). DIAG-005, 0 slots. |
| EXP-036 `/COND` | NOT_EXECUTED | Precondition never met; Tier-B slot not consumed. |
| EXP-037 `/EXIT-FH` | EXIT_FH_TEST_PASS (EURUSD-4h) | G2-binding pass; source of the Package-B estimand and `frozen_selection.json` (hash-pinned into EXP-032). 1 slot consumed. |
| EXP-038 | A1_CELL_TEST_PASS | G2-binding pass; Package-A evidence; not released to holdout. 0 slots. |
| G1 / G2 gate reviews | CLOSED | Mechanical adjudications on frozen results; G2 recorded the exclusive Package-B operator selection. |
| Package B | TEST-confirmed; holdout-inconclusive (shot SPENT in Phase 009) | Permanently non-upgradable; no second holdout read. |
| Package A | NOT RELEASED | Superseded by the exclusive Package-B selection. |
| Global holdout | EURUSD contaminated-by-disclosure (Phase 009); BTCUSD/USTEC/XAUUSD SEALED | Phase 008 itself never touched holdout rows. |

## 8. Redirect — Tier C is the path (operator-gated)

The design §9 consequence chain has fully resolved: CLINICAL_TRADABLE → holdout
release → INCONCLUSIVE, shot spent → return to characterisation. Tier C, ranked
by the programme's findings:

1. **HYP-001 direct S/R test** — the mechanism question that survives every
   strategy-form outcome, confound-free framing ready, analysis-set only.
2. **Stage-C detector/anchor branches** (`/LB` `/MB` `/ATR` `/ANCHOR`) — new
   entry substrates for the family, each a new registered scope; conditioning
   and FH-exit machinery (both now validated patterns) are reusable on top.
3. **Optional FH-exit cTrader parity** (analysis-set only) — only if FH-exit
   machinery is wanted for future candidates.

Phase 008 ran predeclared-once-measured-once throughout: every selection was
TRAIN-mechanical, every TEST stratum was read exactly once, every amendment
preceded the read it governed, and both gates were adjudicated from frozen
artifacts. The phase found the one thing that works (FH capture efficiency on
EURUSD-4h), promoted it honestly, and the programme spent its holdout shot on it
with eyes open.
