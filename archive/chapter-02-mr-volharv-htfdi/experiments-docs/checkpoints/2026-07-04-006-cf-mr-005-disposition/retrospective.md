# Checkpoint 006 Retrospective — CF-MR-005 Disposition (2026-07-04)

**Family disposition: CF-MR-005 RETIRED** — operator-signed, 2026-07-04, on tested evidence
(EXP-018 NOT SUPPORTED), not upstream disqualification. The phase objective — at least one
validly-tested, exposure-honest read of the VAL-006 residue clusters, in either direction — is
met.

## Phase outcome vs objectives

| Objective | Outcome |
|---|---|
| EXP-018 disposition probe | **COMPLETE — NOT SUPPORTED** (operator verdict 2026-07-04; `python/experiments/EXP-018/report.md`) |
| Follow-up probes | none ordered; three candidate probes recorded in the report as future experiments |
| Retrospective family decision | **RETIRED** (this document) |

## Basis for retirement

1. **The predeclared primary (episode net at frozen cost) is a wash in every residue cell**,
   including a well-powered zero on the US500 both-leg cluster (−2.5 bps/ep, CI [−26, +24],
   MDE 24) where VAL-006 saw positives in all 4 variants.
2. **The dislocation-conditioning claim failed its kill test**: random-timing matched-cadence/
   matched-hold ladders earn comparably (US2000 collapse fraction 0.49, diff CI straddles 0);
   on NZDUSD a random ladder is per-leg CI-positive (+31.5 [+13.7, +49.9]) while the
   dislocation-timed arm loses — the residue's per-leg evidentiary form is producible with no
   signal at all.
3. **What P&L exists is 2022-concentrated, long-side index drift, top-5-episode-funded (82%),
   and inventory-heavy** (peak 43 legs; return on peak exposure ≈ exposure-matched B&H). The
   braked arm dies. This is unconditioned ladder carry, not a harvest mechanism.
4. The negative control (NZDUSD) behaved exactly as predeclared, validating the vehicle; the
   entry-delay tripwire was graceful everywhere (no timing artifact); accounting reconciled to
   1e-12 bps under the post-critical-017 contract.

Family arc for the record: EXP-014b/c field discovery → EXP-015 per-event characterisation
NO_MECHANISM_EVIDENCE (L-16 object-mismatch caveat) → EXP-016 TEST retention VOIDED
(critical-017; 3 TEST reads SPENT_ON_DEFECT, strata 1/2, not refunded) → VAL-006 residue →
EXP-018 deliberate re-specification: **residue does not survive**. Retirement rests on EXP-018
+ VAL-006, with EXP-015's per-event null consistent once re-scoped.

## Lessons (carried; KB lesson-candidate flagged)

- **Lesson-candidate (for KB intake):** a per-leg CI_low>0 on a multi-leg ladder object is not
  evidence of conditioning — an unconditioned random-timing matched-hold ladder reproduced it
  outright (NZDUSD). Any ladder/scale-in positive requires an episode-level, cadence-matched
  random-timing control before it is treated as a candidate signal. (Extends L-15/L-16; the
  matched-hold exit design — never re-import the anchor into the null's exits — is the L-08
  corollary that made this readable.)
- INFR-001 pipeline first full pass worked as designed: pre-code operator elicitation caught 4
  design ambiguities (design.md A1); fresh-context QA APPROVE with an independently computed
  golden trace; integrity-only hard gates; operator judged the value reads. No auto-verdicts.
- The random-timing rt twins merge overlapping templates into fewer episodes (leg-level, not
  episode-level cadence matching) — a successor control should match at episode level.

## What is closed / what remains open

- **Closed:** CF-MR-005 (this family), and with it the cross-instrument-MR arc's last open
  branch: CF-MR-002 exonerated-not-tradable, CF-MR-003 retired (cost/capture), CF-MR-004
  retired (entry-seam), CF-MR-005 retired (carry attribution).
- **Open, unregistered:** the NZDUSD random-ladder anomaly (two-sided vol/rebound harvest from
  unconditioned matched-hold ladders) — explicitly NOT mean reversion; pursuing it requires a
  fresh family registration. Operator's side-read (2026-07-04): cross-instrument MR in the
  tested form-space is exhausted; only a substrate change (genuinely cointegrated pairs), a
  cost-structure change at 1h, or the vol-harvest reframing would justify a new family.

## Registry actions (sanctioned by this retrospective)

- `candidate-families/cf-mr-005.md` status → **RETIRED (2026-07-04, operator-signed,
  checkpoint-006)**; HYP-003/EXP-018 evidence row appended (no refunds, no new reads/slots).
- `multiplicity-registry.md`: CF-MR-005/HYP-003 row → COMPLETE, NOT SUPPORTED.
- Master index Phase-006 status updated; family index card added.

**Signed:** operator (verdict + closure instruction, 2026-07-04); recorded by
experiment-documenter.
