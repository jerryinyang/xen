# Phase 012 Retrospective — ENTRY_GROSS_FLAT (The Entry Levers Don't Move the Gross Edge)

**Checkpoint:** `2026-06-12-012-entry-side-gross-screen`
**Status:** **CLOSED 2026-06-12** — Track A complete (EXP-046 audit PASS,
post-experiment governance APPROVE); G1 adjudicated ENTRY_GROSS_FLAT
([G1-gate-review.md](G1-gate-review.md)).
**Outcome class:** **ENTRY_GROSS_FLAT** (design §8.2/§9 — no non-baseline
variant meets the P6 composition threshold; 0 TEST reads, ledger unchanged,
holdouts sealed).
**Follows:** `2026-06-11-011-per-instrument-foundation` (CLOSED —
FOUNDATION_NON-TUNABLE; gross positive in 31/37 but costs consume it).
**Candidate family:** `CF-AVWAP-001`.

---

## 1. Why this phase existed

Phase 011 established that the binding inequality is `gross edge > cost
floor` and that the exit lever cannot raise gross edge — only reallocate
it. The untried gross-side levers were the entry parameters frozen since
the brainstorming document: tick-volume exponent α=0.75 and regime detector
MA(20,50) (`/ALPHA`, `/MA-DOMAIN`, registered since Phase 004, never
swept). The operator's §9 routing decision (Route 1, 2026-06-12) opened
them in the cheapest possible form — a TRAIN-only gross screen, no net
machinery, no TEST contact — with a pre-committed fallback: if flat, pivot
to substrate revision with no second entry-parameter phase.

## 2. The items and their verdicts

| Item | Track | Verdict | Headline |
| --- | --- | --- | --- |
| D0 + G0 | Tier 0 | **G0 PASS 2026-06-12** | P1–P8 ratified as drafted (no value changed draft→ratification); registry amended (0 slots, 0 TEST reads); variant count corrected 8→7 pre-data-contact. |
| **EXP-046** | A — gross screen | **SCREEN_DELIVERED — ENTRY_GROSS_FLAT (hypothesis REFUTED)** | 7 variants × 37 cells: best non-baseline clearing set 3 cells (alpha_1.0 3/3 instruments; ma_40_100 3/2) vs the ≥5/≥3 threshold. 14 CLEAR / 235 NO_CLEAR / 10 BELOW_FLOOR. Integrity clean: reconciliation 259/259 at 1e-9 bps, determinism 259/259, P8 gate green, audit PASS 0C/0W/3 Info. |
| G1 | gate | **ENTRY_GROSS_FLAT → substrate pivot** | Mechanical against P6; operator pre-commitment (§1.4.2) routes the programme; no further routing discussion needed. |

## 3. What the phase established

- **The entry-parameter lever is measured and exhausted on this substrate.**
  Across the full sampled ranges — α from 0.0 (unweighted anchor) to 1.0,
  detector from (10,25) to (60,150) — per-variant H=8 cross-cell medians
  move only between −2.35 and +0.28 bps around the baseline's −1.15 bps,
  against cost floors of ~5–20 bps. No variant adds clearing breadth over
  baseline (3 cells). The gross shortfall is a property of the AVWAP-bounce
  event definition, not of its parameterization.
- **Both remaining tuning levers are now closed with the same shape.**
  Exits (Phases 010–011): reallocate gross, cannot raise it. Entries
  (Phase 012): move gross ~1–2 bps, an order of magnitude short. The
  Phase 011 conclusion — only a stronger event definition (gross side) or
  cheaper execution (cost side) changes the inequality — is now exhaustive
  over the substrate's registered parameter space.
- **The predeclared false-positive channel behaved exactly as predicted.**
  12/14 CLEAR rows are 4h cells; 8 involve US index CFDs; US2000-4h clears
  under five variants including baseline, at SEs 6–28 bps and n = 33–66.
  The plan named this channel before data contact; the caveats (correlated
  bloc, calendar-day floor understatement, anti-conservative SE at low
  regime counts) all inflate the observed clearance count and therefore
  reinforce FLAT. US2000-4h is recorded as hypothesis-generating only.
- **The slow-detector trade-off is breadth-for-quality.** ma_60_150 posts
  the only positive median (+0.28 bps) but collapses 8 of its 4h cells
  below the 30-event floor — the lever thins the event population exactly
  where holding costs are highest.
- **The reconciliation-anchored harness is validated infrastructure.**
  Three blocking legs (EXP-043 count identity, EXP-045 FH-net anchor,
  internal gross-path cross-check) all passed at 1e-9 bps on every cell
  before any non-baseline row was read; determinism by full-frame replay
  everywhere. The harness (dependency gates, F01 loader binding, mechanical
  clearance) re-points cheaply at any revised substrate.

## 4. What changed vs the original design

- **Variant count corrected 8 → 7** (2026-06-12, pre-data-contact,
  design §11): an earlier draft double-counted α=0.0. Frozen P1/P2 grids
  unchanged.
- Nothing else. No threshold, grid, or rule was touched after data contact;
  the phase closed mechanically on the predeclared rules in a single
  pipeline pass (no revision cycles at either governance gate).

## 5. Lessons learned

1. **A cheap gross screen before net machinery is the right ordering.**
   One TRAIN-only diagnostic (5-second runtime, 0 slots, 0 TEST reads)
   definitively closed a lever that a full net/exit/portfolio rebuild would
   have spent a phase discovering. The Phase 011 retrospective's §8.2
   suggestion is validated as a pattern: screen gross first, build net
   machinery only behind a viable gross readout.
2. **Pre-committed routing removes post-result temptation.** With 14
   scattered clearances and US2000-4h clearing repeatedly, an un-committed
   adjudication would have invited a "partial signal" debate. The §1.4.2
   pre-commitment (FLAT → pivot, no second entry phase) plus the
   predeclared caveat channel made the close friction-free.
3. **Predeclaring the false-positive channel is as valuable as
   predeclaring the threshold.** Naming the 4h/index channel before data
   contact converted the most tempting post-hoc narrative ("the index
   cells are real!") into a pre-filed caveat with the correct sign
   (inflationary, pro-FLAT).
4. **External anchors at float precision are cheap and decisive.** The
   1e-9 bps reconciliation against EXP-043/045 cost a few lines of code
   and made the baseline row's validity — and hence every variant row's
   machinery — non-debatable.

## 6. Consequences and open items

- **Routing (operator pre-decision, executed):** programme pivots to
  **substrate-level revision**. Per design §10, the pivot phase starts
  from the Stage-C registered branches — `/LB` `/MB` `/ATR` `/ANCHOR`,
  deferred since Phase 005 — and the Phase 011 gross decomposition, or a
  new candidate family. Any new event definition requires fresh
  readiness/calibration/parity passes (EXP-020/027/029 analogs) under its
  own design/D0.
- **The cost side remains the other valid lever** (design §10): a
  broker-verified cost-model refresh may be declared at a future D0, never
  retroactively. The 2026-06-12 broker review found the frozen model
  realistic-to-conservative, so this is not the expected path.
- **Optional future scopes recorded, none scheduled:** gross-structure
  characterisation of the US index 4h cells at an honest power budget
  (hypothesis-generating clearances); the Phase 011 carry-overs (EXP-044
  precision-only re-run; N1>N2 dependence diagnostic; E1–E5 on the new
  universe). HYP-001 (line S/R) remains OPEN from Phase 010.
- **Standing constraints unchanged:** no holdout read exists for any
  package; EURUSD-4h at the 2-read ledger cap; TEST ledger unchanged
  (0 added); costs and financing frozen; 5m retired; EXP-029-analog parity
  re-binds before any future 2h/new-universe TEST read; the 14 excluded
  cells stay excluded pending new readiness/calibration.

## 7. Disposition of artifacts

| Item | Status | Disposition |
| --- | --- | --- |
| EXP-046 | SCREEN_DELIVERED — REFUTED | Full 259-row gross-vs-floor decomposition, clearance and rollup tables, reconciliation record persisted; the entry-parameter negative is final for this substrate at these costs. |
| `xen.avwap` α/MA parameterization | RETAINED | Default-preserving (baseline bit-for-bit, regression-tested 24/24); available to any future scope; non-default values carry no candidate status. |
| EXP-046 harness (`variant_screen.py` + loader/reconciliation pattern) | VALIDATED IN USE | Re-usable against a revised substrate; mechanical clearance rule + 1e-9 anchoring adopted precedent for future screens. |
| `/ALPHA`, `/MA-DOMAIN` branches | CLOSED-MEASURED | Swept and flat on this substrate; no slot ever consumed; re-opening requires a new substrate. |
| Stage-C branches (`/LB` `/MB` `/ATR` `/ANCHOR`) | NEXT | Input to the Phase 013 substrate-revision design. |
| TEST-read ledger | UNCHANGED | 0 reads, 0 disclosures added. |

## 8. Redirect — next steps

1. **Phase 013 design (substrate revision):** choose the revision path —
   Stage-C detector branches on the existing AVWAP machinery (`/LB` `/MB`
   `/ATR` `/ANCHOR`), a different event definition on the AVWAP anchor
   concept, or a new candidate family. This is an operator direction
   decision at the next design's §1, informed by the Phase 011 gross
   decomposition (the edge is real but thin and cost-dominated).
2. **Whatever substrate is chosen:** EXP-020/027/029-analog
   readiness/calibration/parity passes precede any screen; the EXP-046
   gross-screen pattern (TRAIN-only, floor + 1×SE, composition threshold,
   pre-committed routing) is the validated template for its first
   viability question.

No tuning occurred; no TEST or holdout row was read; every verdict was
computed mechanically from predeclared rules ratified before data contact.
The books are honest, the TEST budget is intact at 0 of ≤6, and the
programme now knows — rather than assumes — that neither exit choice nor
entry parameterization can make this substrate pay frozen conservative
costs.
