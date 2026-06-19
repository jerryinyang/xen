# D0-amendment-005 — TRAIN-only diagnostic follow-up authorized (EXP-074 / HYP-027)

**Date:** 2026-06-19
**Checkpoint:** `2026-06-18-016-harami-candidate-screening`
**Authority:** This amendment extends `D0-predeclarations.md` with one additional
in-phase experiment. It does not edit or supersede any prior clause; the EXP-070/EXP-071
slate stands as recorded.
**Trigger:** EXP-071 returned `TEST_NOT_CONFIRMED` (2026-06-18). GBPUSD-5m was the sole
survivor of the binding 6-cell family — median Holm-clear (p=0.0022), beats-RM, winsorized
mean positive — but failed the raw-mean leg (`pv_mean_ci_low_1s = −0.086`), and the
`mean_recoverable = false` diagnostic established the raw-mean failure **survives removal of
the adverse stop** (the loss tail is entry-structural, not exit-induced). Before the family
is closed, or any future tail-filter experiment spends the sealed holdout, the operator
directed a **TRAIN-only diagnostic** to characterize which causal entry features separate the
GBPUSD-5m loss tail. Operator direction recorded 2026-06-19.

---

## What this authorizes

A single additional Phase 016 experiment:

- **EXP-074 / HYP-027** — TRAIN-only loser-tail characterization of the GBPUSD-5m
  `N-PARTIAL-V2A` per-event return distribution, with the other five EXP-071 family cells as
  disclosed replication. Scope: `python/experiments/EXP-074/scope.md`; plan:
  `analysis-plan.md`. Registered in `multiplicity-registry.md` (Phase 016 diagnostic batch).

## Binding constraints (carried from Phase 016 D0; reaffirmed)

1. **No new TEST contact.** EXP-074 reads the **TRAIN** stratum only (`[0, train_cutoff)`).
   The next-21% TEST stratum — already consumed by EXP-071 — is **not re-read**; EXP-074
   incurs **0 counted TEST reads**. The `test-read-ledger.md` is unchanged by this experiment.
2. **Holdout sealed.** The final-30% global holdout is never loaded.
3. **No candidate slot.** CAND-001 remains the only consumed slot; EXP-074 consumes none.
   The candidate family stays `REGISTERED / OPEN`; CAND-001 disposition is **deferred** to the
   EXP-074 outcome.
4. **No parameter tuning, no filter committed.** EXP-074 *characterizes*; it selects no
   threshold and registers no variant. Any tail filter suggested by the result is a **separate
   future experiment** with its own EXP-ID and D0, designed on TRAIN and confirmed once on the
   sealed holdout — never on the consumed TEST stratum.
5. **Frozen machinery.** Reuse the certified EXP-068/EXP-071 resolution and inference machinery
   unchanged in semantics; the only departure is the evaluation-window mask flipped to TRAIN
   (`entry_epoch ≤ train_end`, the documented complement of EXP-071's TEST mask).

## Routing of the outcome (pre-stated)

- **SEPARATOR_FOUND** → a causal entry feature materially and consistently separates the loss
  tail → motivates (does not itself open) a future TRAIN-designed, holdout-confirmed tail-filter
  experiment under its own D0.
- **NO_SEPARATOR** → the loss tail is not distinguishable on causal entry information →
  supports closing CF-HA-HARAMI-001/CAND-001 at the Phase 016 gate without spending the holdout.
- **INCONCLUSIVE_POWER** → recorded; no routing change.

## Why this is in-scope for Phase 016 rather than a new phase

Phase 016's charter is candidate screening of CF-HA-HARAMI-001/CAND-001. EXP-071 delivered the
one-shot TEST verdict; EXP-074 is the **diagnostic that informs the candidate's disposition at
the same gate** (close vs. route to a follow-up). It introduces no new TEST contact, no new
candidate, and no new registered variant, so it is properly an in-phase diagnostic addendum
rather than a new phase. The G-016 gate review will adjudicate CAND-001 with both EXP-071 and
EXP-074 in evidence.
