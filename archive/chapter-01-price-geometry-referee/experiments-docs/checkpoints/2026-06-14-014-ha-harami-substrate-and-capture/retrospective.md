# Phase 014 Retrospective — CF-HA-HARAMI-001 Substrate, Capture & Conditioned Surface

**Date:** 2026-06-17
**Phase:** 014 (014-A substrate/primitives + 014-B conditioned surface), candidate family
`CF-HA-HARAMI-001` (Heiken Ashi harami at trend exhaustion).
**Outcome:** **CHARACTERISED_NOT_VIABLE on the ZigZag substrate; family carried OPEN on a real
MA-substrate median edge.** G2 adjudicated 2026-06-17 (`G2-gate-review.md`); routing ratified
by the operator (open an MA-substrate follow-up).
**Gates:** G0 PASS 2026-06-14 · 014-A G1 adjudicated 2026-06-15 (primitives READY, benchmark
`CHARACTERISED_NOT_VIABLE` on the unconditioned object only → family OPEN, proceed 014-B) ·
G0-B PASS 2026-06-15 · **G2 (terminal) 2026-06-17 — NO_PROCEED, family OPEN.**
**Slot/ledger:** 0 candidate slots, 0 TEST reads spent across the entire phase; holdouts
sealed; no new-universe row read under the HA-harami event definition; `test-read-ledger.md`
unchanged.

---

## 1. Objective vs outcome

The phase set out to test the family thesis — *a strong-move-qualified HA harami, anchored at
the harami, marks a reversal a non-symmetric capture geometry can convert to gross-positive
expectancy* — by building each primitive from scratch (014-A) and then measuring the
**conditioned** signal across the full barrier + position-management surface (014-B), with a
single terminal G2 on the complete surface.

**It did exactly that, and the answer is two-sided:**

- On the **registered ZigZag substrate**, the combined best-per-layer event system cannot reach
  the MA(20,50) baseline from a single-point reversal entry — `CHARACTERISED_NOT_VIABLE`.
- On the **MA(20,50) substrate**, the same conditioned harami expresses a **genuine,
  signal-attributable median edge** (beats matched-random 85/99) — but it is **median-only**,
  with a gross mean ≈ 0 driven by the uncapped-downside geometry. The family is therefore not
  closed; the binding obstacle has shifted from the signal to the skew/mean.

## 2. What each sub-phase delivered

**014-A (EXP-048–052) — primitives + unconditioned characterisation.** ATR-ZigZag substrate
and HA-harami detector validated (EXP-048: 99/102 cells READY, 0 invariant/determinism
failures); benchmark 3-barrier capture read `r ≈ 0.50` null (EXP-049); raw haramis front-loaded
in moves, not at exhaustion (EXP-050); the `/STRONG` filters carve a materially different
population (EXP-051); `/CONFIRM` universally worse than DIRECT (EXP-052). **The G1 lesson that
shaped everything after:** these reads ran with `/STRONG` **OFF** (and EXP-049 used no harami
at all), so they characterised the *unconditioned* object — they never tested the family's
actual conjunction. Closure at G1 was correctly refused
(`014-A-conditioning-gap-and-validation-lessons.md`).

**014-B (EXP-053–060 + 059B, 060B) — the conditioned surface.** Conditioned efficacy is real
(EXP-053 EVIDENCE_FOR); the fill-model correction is immaterial, so the benchmark null is not a
tie-break artifact (EXP-054); the move is available over the lifetime (EXP-055); of the four
geometric levers, **adverse-target `/ADV-NONE`** (EXP-057) and **V2A partial favourable exits**
(EXP-059) improve expectancy, while favourable-target (EXP-056), third-barrier (EXP-058) and
trailing (EXP-059/059B) do not. The combined champion (EXP-060) is individually viable in 69/99
cells but beats MA(20,50) in **0/99** — the two-baseline conjunction is the binding wall.
EXP-060B then showed that wall is **substrate-specific**: swap ZigZag for MA(20,50) and the
harami beats its own-substrate random in 85/99 (vs 3/99 on ZigZag), so MA dominance is *partly a
real signal effect*, not solely geometry/drift.

## 3. The central finding

**The conditioned HA harami is a real signal whose value is substrate-dependent and currently
trapped by exit geometry, not by the signal or by move availability.** Three legs support this:

1. **Signal exists.** EXP-053 (benchmark, conditioned) is EVIDENCE_FOR, and EXP-060B's
   matched-random control on the MA substrate is beaten 85/99 — the harami+`/STRONG-STAT`
   conjunction adds ~0.78 ATR of median over random on MA.
2. **Move exists.** EXP-055 AVAILABILITY_GOOD — this is the AVWAP situation (move available,
   capture missing), not the worse "no move" case.
3. **Capture is the constraint — and now specifically the *mean/skew*.** The geometry that
   maximises the median (capped V2A upside + uncapped `/ADV-NONE` downside) manufactures a fat
   left tail (skew gap 1.20 ATR on MA) that zeroes the mean. The median-positive / mean-≈0 split
   is the binding obstacle the follow-up must attack.

## 4. Process lessons (carry forward)

1. **Never let an unconditioned characterisation stand in for a conditioned hypothesis.** 014-A
   nearly closed the family on `r ≈ 0.50` and front-loading reads that the live signal never
   touches. The G1 desk's "premise strike" was withdrawn only after verifying `/STRONG` was OFF
   in the efficacy reads. (Recorded in full in the conditioning-gap doc; it worked — 014-B
   exists because of it.)
2. **Match the binding metric to the mechanism — then check it for skew.** P14 chose the median
   for fat-tail robustness, which was right for ranking geometries, but the median **masked** a
   mean-≈0 strategy (EXP-060 emitted MA's median only). EXP-060B caught it post-hoc. *Lesson: when
   the binding endpoint is the median and the geometry is asymmetric (capped one side, uncapped
   the other), emit and inspect the mean from the start — a positive median with a zero mean is
   not a tradeable edge.*
3. **A baseline can be a substrate, not just a null.** EXP-060's MA(20,50) "baseline" was
   silently a *different substrate* (different direction, qualifying subset, targets, and cap).
   Treating its dominance as "ZigZag entries are weak" was a category slip; the matched-random
   control *on the MA substrate* (EXP-060B RM3) was the test that disentangled signal from
   substrate. *Lesson: a baseline that changes the move definition needs its own matched-random
   control before its dominance is attributed to anything.*
4. **No-early-closure on a single geometry paid off.** The single-G2-after-full-slate design
   meant the EXP-056/058/059B negatives never short-circuited the EXP-057/059 positives, and the
   combined read (EXP-060) plus its gap-fill (EXP-060B) produced a far more accurate verdict than
   any one lever would have.
5. **Gap-fills before the gate, not after.** EXP-059B (uncapped trailing) and EXP-060B
   (MA-substrate) were both registered gap-fills that ran *before* G2. Both materially changed
   the readout (059B closed a lever cleanly; 060B blocked a wrong closure). *Lesson: when a
   terminal gate looms and a result rests on an unmeasured confound, fill the gap before
   adjudicating — the cost is one diagnostic, the alternative is a wrong closure.*

## 5. Routing — next phase (operator-ratified)

Open a **scoped MA-substrate follow-up** (new checkpoint, own design/D0/G0). The follow-up
re-screens the MA-conditioned harami against the skew/mean obstacle:

- **mean as a co-primary endpoint** alongside the P14 median;
- **bounded-downside adverse geometry** (benchmark 1:1, `/ADV-EXTREME-rr1`) instead of
  `/ADV-NONE` — EXP-060B D1 shows the MA 1:1 skew gap (0.49) is < half the ADV-NONE gap (1.20),
  so a bounded downside may recover the mean at some median cost;
- **confront the 4h-concentration caveat** (8/14 lead cells low-n 4h) so the verdict is not a 4h
  artifact;
- **MA-substrate signal-component attribution** (harami-only / strong-only) only if the
  bounded-downside re-screen survives.

A draft design has been started at the new checkpoint; **D0 predeclarations and a G0 ratification
are the next operator gate** before any follow-up data contact. The MA-substrate follow-up makes
no TEST or holdout contact and registers a candidate only at its own PROCEED gate.

## 6. Standing records

- Family `CF-HA-HARAMI-001` stays **REGISTERED / OPEN**; the ZigZag-substrate combined surface
  is measured-negative and retained; all 014-B branch dispositions are in
  `multiplicity-registry.md` (Phase 014 / 014-B batches) and `candidate-families/harami.md`.
- 0 candidate slots, 0 TEST reads spent in the entire phase; `test-read-ledger.md` unchanged;
  global holdout and new-universe HA-harami strata sealed.
- Validated infrastructure carried forward: VAL-004 15m/30m domains; the ATR-ZigZag + HA-harami
  primitives; the P15 intrabar fill standard; the EXP-047 `move_size.py` MFE/MAE/matched-control
  machinery; the conditioned `/STRONG-STAT` population and the MA(20,50) substrate harness
  (EXP-060/060B) the follow-up reuses directly.
