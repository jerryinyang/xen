# Phase 011 Retrospective — FOUNDATION_NON-TUNABLE (The Fair Fight Was Held; Costs Won)

**Checkpoint:** `2026-06-11-011-per-instrument-foundation`
**Status:** **CLOSED 2026-06-11** — Tracks A and B complete (EXP-043/044/045
audits PASS); G2 adjudicated FAIL ([G2-gate-review.md](G2-gate-review.md));
Tracks C and D never opened.
**Outcome class:** **FOUNDATION_NON-TUNABLE** (design §8.3/§9 — membership
empty vs the P5 floor; no TEST read spent, 0 of ≤6).
**Follows:** `2026-06-10-010-exit-exploration-and-line-sr` (EXIT_FLAT /
HYP-001 INCONCLUSIVE; INFR-002 closed by VAL-003 PASS 2026-06-11).
**Candidate family:** `CF-AVWAP-001`.

---

## 1. Why this phase existed

Phases 001–010 ran the AVWAP strategy under universal placeholder parameters
(band 1.0, MA 20/50, exponent 0.75, FH H\*=12) that were never trained — a
silent assumption inherited from the brainstorming document. Phase 010's
EXIT_FLAT and the ~86-event 4h power wall said the existing universe could
not resolve further exit questions; VAL-003's admission of 13 new instruments
(2026-06-11) made a properly powered re-examination possible for the first
time. Phase 011 rescoped from MTF to the per-instrument foundation: give the
base strategy its fair fight — per-instrument×domain exit training across 17
instruments × {1h, 2h, 4h} — under an inverted-inference design (portfolio
membership on TRAIN; one EXP-018 portfolio TEST read as primary endpoint;
≤6 total TEST reads governed by the new TEST-read ledger).

## 2. The items and their verdicts

| Item | Track | Verdict | Headline |
| --- | --- | --- | --- |
| D0 + G0 | Tier 0 | **G0 PASS 2026-06-11** | All §8.5 predeclarations frozen before any TRAIN read (EXP-018 threshold first); 17-instrument cost model declared; TEST-read ledger materialized with verified backfill. |
| **EXP-042** | A0 (removed) | **MEASUREMENT_COMPLETE — FRAMING_ERROR (set aside)** | Arm-at-adverse-band entry rule applied the band multiplier as an entry filter; the band was always an **exit** parameter (registry `/BAND` is exit/structural). Track A0 removed; entry restored to the frozen baseline; zero weight in any decision; 0 slots, 0 TEST reads. |
| **EXP-043** | A — readiness | **READINESS_DELIVERED** | 50/51 cells READY (0 invariant violations, 0 determinism failures, no substrate alert); JP225-2h NOT_READY on the frozen >25% dropped-fraction gate. Realized TRAIN counts (1h 151–273, 2h 86–143, 4h 32–86) supersede design §7.4 planning figures. |
| **EXP-044** | A — calibration | **CALIBRATION_DELIVERED** | 37/50 cells COVERED; 13 NOT_COVERED (11 marginal FPR, USDCAD-2h material, BTCUSD-4h no finite MDE); median per-cell MDE 16/32/64 bps on 1h/2h/4h. Systematic N1>N2 FPR offset found (35/50 cells, sign-test p≈0.001). G1 CLOSED on the 37-cell grid. |
| **EXP-045** | B — exit training | **TRAINING_DELIVERED — EMPTY MEMBERSHIP** | 0/37 member cells: 35 NON_TUNABLE, 2 tunable-but-FLOOR_FAIL with *negative* plateaus (EURUSD-1h FH(3) −3.45 bps; US500-2h MAD(1.0) −0.37). Net medians −5 to −7 bps at every grid point of both families; gross proxy positive in 31/37. |
| G2 | gate | **FAIL → FOUNDATION_NON-TUNABLE** | Mechanical against P5 (≥5 cells over ≥3 instruments). Tracks C/D never open; EXP-018 threshold predeclaration unspent. |

## 3. What the phase established

- **The universal-parameter critique is answered, and the answer is "no".**
  The §1.1 diagnosis — that Phases 007–010's negatives might be artifacts of
  one untrained parameter set — was legitimate and is now tested: with
  per-instrument exits trained over two families × 8-point grids on 37
  calibrated cells, **no cell anywhere in the 17-instrument × 3-domain
  universe clears frozen CONSERVATIVE costs**. The "not tradable" reading no
  longer rests on a placeholder parameterization.
- **The binding constraint is gross edge vs the cost floor, not exit choice.**
  Gross-proxy positive in 31/37 cells but net medians −5 to −7 bps
  everywhere: the few-bps gross bounce edge is real and survives training,
  and the frozen costs consume it in full. Exit training reallocates the
  same gross edge; it cannot raise it. Only stronger entries (gross side) or
  cheaper execution (cost side) change the inequality.
- **The exit-side lever is now measured and exhausted on this substrate** —
  the per-instrument completion of Phase 010's pooled EXIT_FLAT. Both the FH
  family and the original MAD-band-target exit (finally given per-instrument
  parameters, the stated point of the phase) fail identically.
- **4h gross positives exist but are unverifiable at current power.** Median
  best-grid-point net +13.8 bps at 4h (US500 +76.7, US2000 +53.4, DE30
  +46.7) vs −2.0/−3.4 bps at 1h/2h — but 4h bootstrap SEs reach ~41 bps and
  the EXP-044 MDE map (32–128 bps) says these are indistinguishable from
  noise at 32–86 events. The tunability rule correctly refused them.
- **The stability-plane machinery worked as designed.** Its operational
  no-signal detection did what Phase 008's one-SE rule could not: it refused
  to certify noise (42 endpoint-argmax, 30 flat-plane family-cells; the
  Phase 008 symptom `h_star_stable=false` never recurred). A selection rule
  that can decline to select is what kept zero TEST reads at risk.
- **The inverted-inference structure paid for itself.** A fully negative
  phase consumed **0 of ≤6 TEST reads** and added zero ledger entries. Under
  the superseded per-cell-first structure the same negative would have
  burned dozens of stratum reads. The ledger, the portfolio-first endpoint,
  and the strict G2 composition gate are validated as governance.
- **A real methodological discovery: the N1>N2 FPR offset.** EXP-044 found
  the pooled-scale two-null agreement of EXP-027 does not replicate per
  cell (35/50 cells, p≈0.001; 11/12 FPR exclusions fail on N1 only). Any
  future per-cell calibration inherits this as prior knowledge; the
  predeclared both-nulls rule absorbed it conservatively this phase.
- **The new universe is operational.** 13 instruments admitted (VAL-003),
  51-cell grid built, readiness and per-cell calibration maps delivered —
  durable infrastructure independent of this phase's negative verdict.

## 4. What changed vs the original design

- **Track A0 removed (2026-06-11, FRAMING_ERROR; design §11).** The
  entry-level band-selection scan — and the arm-at-adverse-band entry rule
  invented to make it non-vacuous — was a framing error: the band multiplier
  was always an exit parameter. EXP-042 set aside with zero decision weight;
  entry restored to the frozen Phases 004–010 baseline; the band exercised
  only in Track B Family 2, where it always belonged. Caught after
  execution but before any decision consumed the result.
- **G1 split into two adjudications** (operator-ratified): the operator's
  proposal to close G1 on EXP-043 alone was flagged as a §8.2 conflict;
  the design-compliant path (G1 PARTIAL → EXP-044 → G1 CLOSED) was taken.
  No design amendment was needed; §8.2 stood as frozen.
- **Grid narrowed honestly by the gates:** 51 → 50 (JP225-2h readiness) →
  37 (calibration coverage), each exclusion recorded, nothing consumed.
- **Pre-execution adversarial reviews** fixed EXP-042 F01–F05 (TRAIN-slice
  loading, degenerate-floor adjudication, regression suite) and EXP-045
  items (financing units, explicit endpoint rule, DE30 disclosure) before
  any TRAIN read. Nothing was amended after any outcome was read.

## 5. Lessons learned

1. **Check a parameter's historical role before redefining its mechanism.**
   The A0 framing error survived design, scope, plan, implementation review,
   and an adversarial pre-execution review — every layer checked
   *implementation correctness* while the error was *semantic* (entry vs
   exit role). The registry branch definition (`/BAND` = exit/structural)
   held the truth the whole time: registry definitions are the authority,
   and design↔registry traceability belongs in Stage-1 scope review.
2. **An empty-membership outcome needs its gross companion to be useful.**
   The gross-proxy column is what turns "0/37 members" from a dead end into
   a direction: edge exists, costs eat it, go raise gross edge or cut costs.
   Negative verdicts should always carry the decomposition that locates the
   failure.
3. **Selection rules must be allowed to return "nothing."** The stability
   plane's tunability rule (endpoint ineligibility + separation + split-half
   agreement) is the phase's methodological keeper — adopted standard for
   any future grid selection.
4. **Spend predeclarations, not reads, on negative phases.** The full D0
   predeclaration stack (threshold-first ordering, frozen grids, composition
   floor) made the phase close mechanically with the entire TEST budget
   intact. The discipline's cost was paperwork; its value was six unspent
   one-shot reads.
5. **Per-cell calibration before training is not bureaucracy.** Without
   EXP-044, Track B would have trained on 13 cells whose inference layer
   was anti-conservative — and the N1>N2 offset would have surfaced *after*
   a binding read instead of before one.
6. **Realized power supersedes planned power, in writing.** EXP-043's
   realized-count table replacing design §7.4 mid-phase (and the set-aside
   EXP-042 power statement before it) kept every downstream artifact honest
   about what could actually be resolved.

## 6. Consequences and open items

- **The phase outcome routes per design §9:** the AVWAP baseline-entry
  substrate with per-instrument exits is not tunable at frozen CONSERVATIVE
  costs. The untried levers are the entry side — `/ENTRY`, `/ALPHA`,
  `/MA-DOMAIN`, deliberately frozen since Phase 004 and never swept — or a
  substrate-level revision; a cheaper execution layer attacks the other side
  of the inequality. Direction-setting is the next phase design's job.
- **MTF remains deferred and is now weaker as a premise:** it was admissible
  on tradable cells (design §9 PORTFOLIO_PASS row), and there are none. Any
  MTF revival first needs a substrate that clears costs somewhere.
- **The Phase 008 frozen package** (EURUSD-4h, FH H\*=12, all_legs,
  TEST-capped) is unaffected and remains the family's standing record.
- **Optional future scopes recorded, none scheduled:** gross-structure
  characterisation of the US500/US2000/DE30 4h cells at an honest power
  budget; EXP-044 precision-only re-run (operator option if the 37-cell
  map limits a future phase); N1>N2 dependence diagnostic; E1–E5 re-test on
  the new universe. HYP-001 (line S/R) remains OPEN from Phase 010.
- **Standing constraints unchanged:** no holdout read exists for any
  package; EURUSD permanently TEST-capped, EURUSD-4h at the 2-read ledger
  cap; all other holdouts sealed; costs and financing frozen; 5m retired;
  EXP-029-analog parity re-binds before any future 2h/new-universe TEST
  read.

## 7. Disposition of artifacts

| Item | Status | Disposition |
| --- | --- | --- |
| EXP-042 | SET ASIDE — FRAMING_ERROR | Negative-process record (file drawer); code/results retained; `xen.avwap` parameterization + regression suite retained (defaults = baseline bit-for-bit; non-default arm rule unused). |
| EXP-043 | READINESS_DELIVERED | 51-cell readiness map + realized power table persisted; the binding event-rate reference for any future phase on this substrate. |
| EXP-044 | CALIBRATION_DELIVERED | 37-cell coverage map + per-cell MDE table persisted; binding power context for any future per-cell work; N1>N2 offset recorded as prior knowledge. |
| EXP-045 | TRAINING_DELIVERED — EMPTY MEMBERSHIP | Full selection/score/split-half tables persisted; the per-instrument exit-training negative is final for this substrate at these costs. No rerun within scope. |
| EXP-018 P1 threshold | UNSPENT | Frozen predeclaration record only; never consumed; a future portfolio read requires its own predeclaration. |
| TEST-read ledger | UNCHANGED | 0 reads, 0 disclosures added; backfilled state stands. |
| JP225-2h + 13 NOT_COVERED cells | EXCLUDED WITH RECORD | Re-entry requires a new readiness/calibration pass under a future design. |
| Stability-plane selection method (design §6) | VALIDATED IN USE | Adopted precedent for future grid selections. |
| New-universe infrastructure (VAL-003, 17×3 grid) | OPERATIONAL | Carries forward independent of the phase verdict. |

## 8. Redirect — next steps

1. **Operator direction decision:** entry-side exploration (`/ENTRY` /
   `/ALPHA` / `/MA-DOMAIN`) vs substrate-level revision vs execution-cost
   work — the §9 FOUNDATION_NON-TUNABLE routing. This is a new phase design
   with its own D0/predeclarations.
2. If entry-side is chosen: the first question is whether any entry variant
   raises **gross** per-event edge materially above the P2 cost floor on
   TRAIN — a gross-side screen, cheap, before any net machinery is rebuilt.
3. The optional 4h index-CFD gross characterisation only makes sense behind
   whichever lever is chosen first (report.md, Implications).

No tuning occurred; no TEST or holdout row was read; every verdict was
computed mechanically from predeclared rules. The books are honest, the
TEST budget is intact at 0 of ≤6, and the programme now knows — rather than
assumes — that this substrate's exits cannot pay these costs.
