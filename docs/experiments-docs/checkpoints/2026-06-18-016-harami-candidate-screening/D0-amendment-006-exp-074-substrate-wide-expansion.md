# D0-amendment-006 — EXP-074 expanded to the full 99-cell substrate (TRAIN-only)

**Date:** 2026-06-19
**Checkpoint:** `2026-06-18-016-harami-candidate-screening`
**Authority:** This amendment extends `D0-amendment-005` (which authorized EXP-074 as a
TRAIN-only diagnostic on GBPUSD-5m + 5 disclosed EXP-071 family cells). It **does not edit
or supersede** amendment-005; that authorization stands as recorded. This amendment widens
the evaluation surface of the **same** experiment (EXP-074 / HYP-027) and re-frames its
verdict object.
**Trigger:** Operator direction 2026-06-19: the EXP-074 TRAIN diagnostic should be run on
**all 99 cells of the MA-native harami substrate**, not the hand-picked EXP-071 survivors —
so that the loss-tail characterization distinguishes a substrate-wide property from a
GBPUSD-5m idiosyncrasy, and supplies the mechanism for the EXP-075 exhaustion-cap design on
the same 99-cell matrix.

---

## What this authorizes

The **same single Phase 016 diagnostic experiment**, EXP-074 / HYP-027, with two changes:

1. **Cell set widened** from the 6-cell EXP-071 family (GBPUSD-5m primary + 5 disclosed) to
   the **full 99-cell MA-substrate harami matrix** (the EXP-060B / EXP-068 grid). No cell is
   hand-picked or pre-excluded by prior outcome. GBPUSD-5m is retained only as a **named
   continuity cell** for comparison with EXP-071; it is no longer the binding object.
2. **Verdict object re-framed to per-domain, dual-metric (binding).** The verdict is emitted
   **per domain** (5m/15m/30m/1h/2h/4h), not as a single pooled number — pooling 5m noise and
   underpowered 2h/4h against the 15m–1h core masks domain structure (confirmed on the first
   run: per-cell separability 35%/88%/71%/94% for 5m/15m/30m/1h, 0 powered at 2h/4h). Each
   domain reports two metrics — the per-cell **any-feature separability rate** and the
   per-feature **single-lever breadth** (candidate in ≥ 50% of the domain's powered cells with a
   material, sign-consistent within-domain median CI) — and a four-tier verdict (SEPARATOR_FOUND
   / SEPARABLE_NO_UNIFORM_LEVER / NO_SEPARATOR / INCONCLUSIVE_POWER < 5 powered cells). The
   pooled substrate verdict is retained **disclosed-only**. The two pre-registered mechanism
   leads (H1 exhaustion magnitude, H2 polarity agreement) are unchanged; routing reads the
   domain verdicts jointly (a band-restricted EXP-075 vs feature-blended vs close).

## Binding constraints (carried from amendment-005 and Phase 016 D0; reaffirmed)

All amendment-005 constraints carry **unchanged**:

1. **No new TEST contact.** EXP-074 reads the **TRAIN** stratum only (`[0, train_cutoff)`),
   now across all 99 cells. The next-21% TEST stratum is **not read**; EXP-074 incurs
   **0 counted TEST reads**. `test-read-ledger.md` is unchanged.
2. **Holdout sealed.** The final-30% global holdout is never loaded.
3. **No candidate slot.** CAND-001 remains the only consumed slot; EXP-074 consumes none.
   Family stays `REGISTERED / OPEN`; CAND-001 disposition deferred to the EXP-074 outcome.
4. **No parameter tuning, no filter committed.** EXP-074 *characterizes*; it selects no
   threshold and registers no variant. The exhaustion-cap filter design is the **separate**
   experiment EXP-075 (its own D0 addendum), TRAIN-design only, sealed-holdout confirm later.
5. **Frozen machinery.** Reuse the certified EXP-068/EXP-071 resolution and inference machinery
   unchanged in semantics; the only departure is the evaluation-window mask flipped to TRAIN
   (`entry_epoch ≤ train_end`), now applied to all 99 cells.

## Multiplicity note (widened surface)

The comparison surface grows from 6 to 99 cells (14 features × 3 framings × 99 cells). The
file-drawer control is the **substrate-wide share rule + cross-cell median CI + the two
pre-registered leads** — not a per-(cell×feature) family-wise correction, because (a) no
confirmatory inference is drawn (any separator must be re-confirmed in EXP-075's TRAIN-design
→ sealed-holdout chain), and (b) the verdict is a breadth statistic (≥50% of powered cells),
which is itself the multiplicity guard: isolated cell-level hits cannot satisfy it. The
`multiplicity-registry.md` HYP-027 row is updated to record the 99-cell surface.

## Why this remains an in-phase TRAIN-only diagnostic

The widening adds no TEST contact, no candidate, no registered variant, and no parameter
tuning — it only enlarges the TRAIN evaluation set of an already-authorized diagnostic and
sharpens its verdict from cell-local to substrate-level. It remains properly an in-phase
diagnostic addendum, adjudicated at G-016 alongside EXP-071. EURUSD's instrument-wide TEST
cap is a TEST-stratum constraint and does not restrict a TRAIN-only diagnostic; EURUSD cells
are characterized and reported like any other, never screened.

## Operator ratification

The manual-execution gate stays closed until the operator ratifies this amendment (TRAIN-only,
no TEST contact, substrate-wide). Recorded here as the binding pre-execution condition.
