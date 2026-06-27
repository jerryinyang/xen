# Phase 016 Retrospective — CF-HA-HARAMI-001 Candidate Screening

**Phase:** 2026-06-18-016-harami-candidate-screening
**Opened:** 2026-06-18 (G-015 PROCEED_TO_SCREEN; first candidate slot consumed)
**Closed:** 2026-06-19 at **G-016 → CLOSE_FAMILY** (operator-directed; see `G-016-gate-review.md`)
**Net result:** CF-HA-HARAMI-001 **CLOSED**, CAND-001 retired. Holdout never touched.

---

## 1. Objective vs outcome

**Objective.** Carry CF-HA-HARAMI-001/CAND-001 (the MA(20,50)-native conditioned HA harami,
`N-PARTIAL-V2A` lead) to its first counted TEST contact and adjudicate whether it confirms as a
tradable candidate.

**Outcome.** The candidate **did not confirm** and the family is **closed**. The first TEST contact
(EXP-071) returned a systematic negative on the binding raw-mean leg; two in-phase follow-ups
(EXP-074 diagnostic, EXP-075 design) then established that the failure is structural and not fixable
with the registered surface. The screening question is answered: the conditioned harami carries a
real median edge on the MA substrate but **no TEST-confirmable tradable edge**, because its mean is
sunk by an exhaustion-driven bimodal loss tail that cannot be removed without erasing the median.

## 2. Experiment slate (as run)

| EXP | HYP | Result | Counted TEST reads |
| --- | --- | --- | --- |
| EXP-070 | HYP-023 | CALIBRATION_DELIVERED (method FPR-controlled; Null-B demoted to advisory, amendments 003/004) | 0 |
| EXP-071 | HYP-024 | **TEST_NOT_CONFIRMED** (0/6 binding cells; 4/6 median CI_low ≤ 0) | **6** (each binding stratum 1/2) |
| EXP-074 | HYP-027 | CHARACTERISATION_DELIVERED (exhaustion magnitude separates the q05 tail; gate-masked; amendments 005/006) | 0 (TRAIN-only) |
| EXP-075 | HYP-028 | **FILTER_INEFFECTIVE** (exhaustion cap is not a lever; amendment 007) | 0 (TRAIN-only) |

EXP-072/EXP-073 (portfolio + cost-bearing tradability) were conditional on TEST_CONFIRMED and were
**never opened**. No holdout experiment was opened.

## 3. The closed arc (why the family closes)

1. **EXP-071** — the candidate fails the one-shot TEST on the **raw-mean** leg (median and beats-RM
   pass on the lone survivor GBPUSD-5m, but the mean is tail-dragged; `mean_recoverable=false` ⇒ the
   loss tail is entry-structural).
2. **EXP-074** — the driver of that tail is **entry exhaustion magnitude** (`msofar_atr`): it
   separates the extreme q05 loss tail near-universally, but the effect is **tail-shaped/bimodal**,
   not location-monotone (high exhaustion produces both catastrophic losers *and* large winners).
3. **EXP-075** — the natural lever, an entry-time exhaustion **cap**, is **ineffective**: removing
   high-exhaustion entries strips the winners with the losers, so no cap lifts the mean without
   eroding the median edge or gutting event count, in any band-core domain, across the whole grid.

The median edge is real but **not convertible** into a confirmable tradable candidate. The
registered surface is exhausted (Phases 014–016). Closure is correct.

## 4. Lessons learned

**L1 — Pooled/unstratified evaluation masks structure (carried from EXP-074, held end-to-end).**
EXP-074's single pooled verdict hid that 15m/30m/1h are the separable core while 5m is noisy and
2h/4h underpowered. Every binding read in EXP-074/075 was per-domain; the band-pooled number stayed
disclosed-only. The masking risk recurred one level up in EXP-075 (M-GLOBAL is a pooled-quantile
rule) and was caught by reporting the cap's effect per domain. **Rule:** judge global rules per
stratum, never on a pooled average.

**L2 — A guard must fit the shape of the observation (carried from EXP-074, held end-to-end).**
EXP-074's all-framing consistency gate is the right anti-p-hacking guard for *location* effects but
is structurally blind to *tail-shape* effects, so it vetoed the strong q05-tail signal. The
disciplined resolution — verdict stands as written, gate not retro-edited, question re-posed a
priori in a new design (EXP-075) with operator ratification of the "SEPARATOR_FOUND not literally
met" conflict — avoided goalpost-moving while still pursuing the real finding. **Rule:** when a
guard rejects an observation, check whether the guard is the wrong instrument for the observation's
shape before discarding it; never retro-edit a guard on the experiment it just judged.

**L3 — The joint economic criterion is the correct instrument for a bimodal mechanism (new).**
EXP-075 judged the cap on the strategy's own legs via a joint four-leg `improved` criterion
(raw-mean ∧ median ∧ beats-RM ∧ retention), not a separation screen. This was decisive: a separation
screen on the q05 tail would have looked promising (the cap *does* suppress the tail), but the joint
criterion correctly returned a negative because the suppression costs the median/winners just as
much. **Rule:** for a bimodal mechanism, credit a lever only on the full economic net, simultaneously
on every leg — a single-leg or separation-only read will mislead.

**L4 — A median edge is not a candidate if its mean cannot be lifted (new, family-level).** The most
important programme lesson: CF-HA-HARAMI-001 produced a genuine, replicated median edge that
nonetheless yielded no tradable candidate, because the binding TEST leg (raw mean) and the median
edge share a single driver (entry bimodality) that cannot be separated at entry. Future candidates
should establish early — before a TEST read — that the binding outcome leg and the favourable signal
are not driven by the same unfilterable mechanism.

## 5. Integrity ledger

- **Holdout:** sealed throughout; never loaded. The single sanctioned shot remains SPENT only on the
  unrelated EXP-032 (EURUSD-4h).
- **TEST reads:** 6 counted (EXP-071), each binding stratum at 1/2 lifetime; EXP-070/074/075 spent 0.
  EURUSD excluded instrument-wide.
- **File-drawer:** all HYP rows and variants retained with their outcomes; nothing deleted or reused.
- **No goalpost-moving, no post-result cell selection, no parameter tuning beyond the pre-registered
  EXP-075 `U` (mechanically selected).** All four experiments audited (PASS / CONDITIONAL PASS) with
  APPROVE post-experiment governance.

## 6. Proposed next direction (operator decision, outside this gate)

This gate closes CF-HA-HARAMI-001; it makes **no** claim on the next research direction. Options for
the operator:
- Open a **new candidate family** from the backlog (the data layer and event-level method
  infrastructure — EXP-027/070 calibration, the frozen suite — are reusable).
- The harami family is reopenable only by a **genuinely new lever** not on the exhausted registered
  surface (a different conditioning object, a non-entry mechanism for the bimodality, or a new
  substrate), under its own scope/D0/G0 — a high bar, deliberately.

CF-AVWAP-001 closed on capture geometry (Phase 013); CF-HA-HARAMI-001 closes on entry bimodality
(Phase 016). Both reached closure with the holdout intact — the file-drawer discipline and TEST-read
cap held across the full programme.
