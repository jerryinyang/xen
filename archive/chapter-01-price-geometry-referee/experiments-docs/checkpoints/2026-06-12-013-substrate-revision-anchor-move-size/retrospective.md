# Phase 013 Retrospective — ANCHOR_MOVE_FLAT (The AVWAP Family Is Closed)

**Checkpoint:** `2026-06-12-013-substrate-revision-anchor-move-size`
**Status:** **CLOSED 2026-06-12** — Tracks A/B complete (EXP-047 audit PASS,
post-experiment governance APPROVE); G1a 51/51 READY, G1b adjudicated
ANCHOR_MOVE_FLAT ([G1-gate-review.md](G1-gate-review.md)).
**Outcome class:** **ANCHOR_MOVE_FLAT** (design §8.3/§9 — 0/51
SHIFTED_VIABLE against the ≥5/≥3 composition; 0 slots, 0 TEST reads, ledger
unchanged, holdouts sealed).
**Follows:** `2026-06-12-012-entry-side-gross-screen` (CLOSED —
ENTRY_GROSS_FLAT).
**Candidate family:** `CF-AVWAP-001` — **closed for new in-family phases by
this retrospective.** The programme routes to a new candidate family
(Phase 014, own design/D0).

---

## 1. Why this phase existed

Nine phases (004–012) exhausted every tuning lever on the AVWAP-bounce
substrate: exits reallocate gross but cannot raise it (010–011); entry
parameters move gross ~1–2 bps against 5–20 bps floors (012). The corrected
substrate framing (trend-continuation pullback entry; design §1.1) left one
registered lever that changes *move geometry* rather than reshuffling the
same events: the `/ANCHOR` significant-pivot anchor, deferred since
Phase 005. Before spending the expensive new-family pivot, the operator
opened the cheapest decisive read (design §1.3): a TRAIN-only, gross-only,
exit-agnostic move-size diagnostic distinguishing "thin move is an anchor
artifact (fixable in-family)" from "thin move is intrinsic to
MA(20,50)-regime trend legs (new family required)" — with routing
pre-committed for both outcomes (§1.5).

## 2. The items and their verdicts

| Item | Track | Verdict | Headline |
| --- | --- | --- | --- |
| D0 + G0 | Tier 0 | **G0 PASS 2026-06-12** | P1–P8 ratified; operator fixed k=1.0 (P1) and floor multiple M=2 (P5); registry amended (Phase 013 batch, 0 slots, 0 TEST reads). |
| **EXP-047** | A — readiness; B — move-size comparison | **REFUTED — ANCHOR_MOVE_FLAT (mechanical)** | G1a 51/51 READY. G1b leg 1 (MFE shift ≥1×SE_diff) 0/51 — Δ median MFE −2.7…+0.9 bps, 29/51 exactly 0.0; the ratified k=1.0 anchor coincides with the baseline running extreme 94.6–98.5% of regimes (13/51 identical event populations). Integrity clean: reconciliation 125/125 at diff 0.0, determinism everywhere, P8 gate 15/15 green, audit PASS 0C/2W (both interpretive). |
| G1a/G1b | gates | **ANCHOR_MOVE_FLAT → new candidate family** | Mechanical against P5/P6; operator pre-commitment (§1.5/§8.3) routes the programme; no further routing discussion needed. |

## 3. What the phase established

- **The ratified `/ANCHOR` lever is inert, and the family is therefore
  closed.** At k=1.0 the ATR-prominence rule is a near-vacuous filter at
  these timeframes: by MA(20,50) confirmation the segment extreme almost
  always carries a completed ≥1×ATR(14) counter-move, qualifies, and — being
  the most price-extreme candidate — is selected. The two arms' event
  populations are nearly or exactly identical, so no MFE shift exists
  outside noise in any cell. With exits, entry parameters, and now the
  anchor all measured flat, no registered lever on `CF-AVWAP-001` remains
  untested that could change the binding inequality.
- **The binding constraint was re-diagnosed: capture geometry, not move
  availability.** The unanticipated descriptive read (P5 leg 2, 51/51):
  median lifetime peak MFE ≈ 24/36/64 bps on 1h/2h/4h against binding
  floors ≈ 4.9/5.3/7.2 bps — **5–9× the cost floor in every cell, on both
  anchors** (censoring ≤3.1%). The Phase 011–013 narrative "available
  captured move < cost" is corrected: the *available* move clears cost
  comfortably; what nine phases could not build is a deterministic exit
  that converts a non-tradable peak into a realizable, net-of-cost capture.
  This is the primary input to the Phase 014 design brief.
- **The bounce trigger accesses no privileged move sizes.** Matched-control
  median MFE ≈ event median MFE on all three domains (1h 24.9 vs 24.0; 2h
  31.6 vs 35.9; 4h 59.1 vs 64.5 bps; descriptive, same-sub-segment
  circularity disclosed) — consistent with the established
  relative-not-absolute character of the bounce edge.
- **The fresh-readiness discipline paid for itself.** `/ANCHOR` events were
  gated by a fresh EXP-020-analog pass (51/51 READY, including JP225-2h,
  which failed the old-anchor EXP-043 coverage gate) rather than inheriting
  the 37-cell map — the cell universe was defined by the new event
  definition, as the design required.

## 4. What changed vs the original design

- Nothing. No threshold, grid, anchor parameter, or rule was touched after
  data contact; the phase closed mechanically on the predeclared rules in a
  single pipeline pass (no revision cycles at either governance gate).
- One framing note for the record: the §1.5 pre-commitment's literal
  premise for the FLAT branch ("distribution remains capped near the cost
  floor") was itself refuted by leg 2 — the move is not capped near the
  floor. The operative frozen rule (§8.3 SHIFTED_VIABLE composition) was
  unambiguous and the routing is unaffected; the lesson is recorded in §5.

## 5. Lessons learned

1. **Collapse-toward-baseline disclosures must measure outcome coincidence,
   not mechanism.** The predeclared `fallback_rate` column read ~0–2% while
   the rule was ~95–99% inert — the dominant collapse path was
   *qualification* (the baseline extreme passing the new filter), not the
   explicit fallback branch. Any future parameterised event definition must
   predeclare an **outcome-coincidence rate** (here: anchor coincidence)
   with the baseline as a first-class disclosure.
2. **Calibrate a new rule's bite on synthetic fixtures before ratifying its
   parameter.** k=1.0 was ratified at G0 without measuring its
   anchor-displacement rate; a cheap pre-G0 fixture check would have shown
   the threshold does not bind and either re-anchored k or redirected the
   phase. The diagnostic still answered its question, but one of its two
   arms was nearly the control arm.
3. **Pre-committed routing survives even a refuted premise.** The FLAT
   branch's narrative premise (move capped near floor) was wrong, yet the
   frozen mechanical rule (no shift → in-family lever closed → new family)
   produced a clean, debate-free close. Freezing the *rule* rather than the
   *story* is what made this robust.
4. **Cheap diagnostics keep relocating the constraint.** Phase 012's screen
   closed the entry lever for ~5 seconds of compute; this phase closed the
   anchor lever and overturned the "move too small" diagnosis for one
   TRAIN-only pass. The screen-before-machinery ordering is now validated
   three times (011→012→013) and is the standing pattern for Phase 014's
   first viability question.

## 6. Consequences and open items

- **Routing (operator pre-decision, executed):** programme routes to a
  **new candidate family** — Phase 014, own design/D0, fresh
  EXP-020/027/029-analog readiness/calibration/parity scaffolding.
  Per design §10 the new-family design starts from the Phase 011/012 gross
  decomposition *as corrected by this phase*: entry direction sound,
  available move 5–9× floor, **capture geometry is the unsolved problem** —
  the mechanism chosen must make the peak→realizable-exit conversion
  structurally cheaper, not the raw move bigger.
- **`CF-AVWAP-001` disposition:** closed for new in-family phases. The
  registered branches stand: `/EXIT` family CLOSED-MEASURED (010–011),
  `/ALPHA` `/MA-DOMAIN` CLOSED-MEASURED (012), `/ANCHOR` CLOSED-MEASURED as
  ratified (013), `/LB` `/MB` `/ATR` DEFERRED with no candidate status.
  The two TEST-pass results (EXP-037/038, EURUSD-4h) remain on the books as
  TEST evidence, permanently non-upgradable (EXP-032 shot spent).
- **Optional in-family scope recorded, not scheduled:** a binding-k
  `/ANCHOR` variant (synthetic-fixture-calibrated prominence threshold with
  a predeclared anchor-displacement rate) is a legitimate new D0 motivated
  by the collapse finding (EXP-047 report §Implications). It does not block
  or delay the new-family pivot.
- **Standing constraints unchanged:** no holdout read exists for any
  package (EURUSD contaminated-by-disclosure; Phase 009 shot spent);
  TEST-read ledger unchanged (EURUSD-4h AT CAP 2, USTEC-4h 1, XAUUSD-4h 1,
  all else 0); costs and financing frozen (broker-verified 2026-06-12);
  5m retired; HYP-001 (line S/R) remains OPEN from Phase 010; the
  Phase 011 carry-overs (EXP-044 precision-only re-run; N1>N2 dependence
  diagnostic) remain optional and unscheduled.

## 7. Disposition of artifacts

| Item | Status | Disposition |
| --- | --- | --- |
| EXP-047 | REFUTED — ANCHOR_MOVE_FLAT | Full per-cell MFE/MAE-vs-floor decomposition for both anchors, coincidence table, reconciliation record persisted; the anchor negative is final for the ratified definition. |
| `xen.avwap` anchor parameterisation | RETAINED | Default-preserving (baseline bit-for-bit, regression suite 15/15); available to any future scope; non-default values carry no candidate status. |
| EXP-047 move-size harness (`move_size.py`) | VALIDATED IN USE | MFE/MAE/matched-control machinery and the coincidence-rate audit pattern re-usable for the new family's first gross diagnostic. |
| `CF-AVWAP-001` | CLOSED for new in-family phases | See §6; re-opening any branch requires a new D0 with an explicit justification against this retrospective. |
| TEST-read ledger | UNCHANGED | 0 reads, 0 disclosures added; holdouts sealed. |

## 8. Redirect — next steps

1. **Phase 014 design (new candidate family):** operator direction decision
   at the design's §1 — select a mechanism whose *capture geometry* is
   structurally favourable (the available move already clears cost 5–9×;
   the unsolved step is peak → realizable exit net of cost). Candidate
   selection is unconstrained by AVWAP machinery but inherits the validated
   process stack: D0 predeclaration, EXP-020-analog readiness,
   EXP-027-analog calibration, EXP-029-analog parity, TRAIN-only gross
   screen with pre-committed routing before any net machinery.
2. **First item of Phase 014:** EXP-020-analog substrate validation for the
   selected family (EXP-047 report, Recommended Next Experiments #1).

No tuning occurred; no TEST or holdout row was read; every verdict was
computed mechanically from predeclared rules ratified before data contact.
The books are honest, the TEST budget is intact, and the programme now
knows — rather than assumes — that the AVWAP-bounce family cannot pay
frozen conservative costs under any registered lever, while the moves it
enters are 5–9× larger than cost: the next family must be chosen for how
it *exits*, not how it enters.
