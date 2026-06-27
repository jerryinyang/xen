# EXP-075 — Post-Experiment Governance Review (consolidated Stage 8)

**Date:** 2026-06-19
**Reviewer:** research-pipeline (consolidated Stage 8)
**Artifacts reviewed:** `audit.md`, `results.md`, `report.md`, index updates
(`python/experiments/INDEX.md`, `docs/experiments-docs/families/cf-ha-harami-001/INDEX.md`,
`docs/experiments-docs/INDEX.md`), and signal-registry updates
(`candidate-families/harami.md`, `multiplicity-registry.md`, `test-read-ledger.md`).

## Checks

**Holdout & TEST fence.**
- Audit confirmed `load_train_1m` slices `[0, train_cutoff)` only; the cap is a causal entry-only
  boolean subset (removes entries, never reaches forward); the next-21% TEST stratum and final-30%
  holdout are never sliced/materialized. **0 counted TEST reads, holdout untouched.** ✓
- `test-read-ledger.md` explicitly records EXP-075 as a TRAIN-only design that moves no tally. ✓
- The locked filter is frozen but **non-confirmatory** (`deployable=false`); FILTER_INEFFECTIVE
  explicitly routes **away** from any holdout read. No premature holdout contact. ✓

**Real-price discipline.** `r_e` is the certified EXP-068 `N-PARTIAL-V2A` real-price arm, reconciled
to EXP-074 at 1e-9 (hard-fail assert did not trip); HA used only for harami detection. ✓

**Audit integrity.** CONDITIONAL PASS (0 Critical, 1 Warning, 2 Info). The single Warning (the run
narrowly predated the F4 `undef_share` instrumentation) has **zero verdict impact** — F4 only records
a column; the disclosure was reconstructed from EXP-074 parquets (`undef_share ≡ 0.0`) and carried
into `results.md`. The two Info notes (matplotlib categorical-units warning; run cost) are cosmetic.
No code defect. ✓

**Interpretation soundness.**
- `results.md` leads with the binding `FILTER_INEFFECTIVE` and the per-band-core-domain vector, not
  a band-pooled average (EXP-074 Lesson 1 honored). ✓
- The mechanism (EXP-074 bimodality, shown economically — the cap strips winners with losers) is
  stated with concrete cell evidence (USTEC-1h +0.167→−0.089) and tied back to the joint four-leg
  criterion that was designed to catch exactly this (EXP-074 Lesson 2 honored). ✓
- **Bar-sensitivity disclosed and correctly bounded:** the verdict *tier* depends on the pinned 0.15
  `UPLIFT_BAR` (30m's +0.118 would flip to FILTER_OVERFIT at 0.10), but the *disposition* (do not
  spend the holdout; route toward closing CAND-001) is identical under both tiers. The 0.15 is
  correctly described as a pre-registered, analogy-borrowed bar, not a calibrated value. This is the
  right disclosure posture — no post-hoc bar tuning, and the decision is shown robust. ✓
- No candidate slot consumed, no parameter tuned beyond the pre-registered `U` selection, no scope
  expansion, no holdout/TEST contact. ✓

**Signal-registry disposition (required).** Result is registry-relevant; updates applied in this
change:
- `candidate-families/harami.md`: CF-HA-HARAMI-001 stays REGISTERED / OPEN; EXP-075 disposition +
  mechanism recorded; **exhaustion-cap route closed**; family-closure decision routed to G-016. ✓
- `multiplicity-registry.md`: HYP-028 / EXP-075 row advanced from CONDITIONAL—ACTIVATED to
  **FILTER_INEFFECTIVE** with the full outcome; no candidate branch registered; item retained
  (refuted outcome — never deleted/reused). ✓
- `test-read-ledger.md`: unchanged tallies; explicit 0-counted-read disclosure added for EXP-075. ✓

**Index updates.** `python/experiments/INDEX.md` row added; family detail card + ToC entry added to
`families/cf-ha-harami-001/INDEX.md` and its status header updated; master `INDEX.md` family-row live
status + checkpoint-row live status updated (no per-experiment card added to master). ✓

**Process note (carried, not blocking).** EXP-075's pre-execution review was issued as the consolidated
Stage-4 verdict APPROVE with the "formal SEPARATOR_FOUND not literally met" conflict in full view and
operator ratification of the revised `D0-amendment-007`. The completed result (FILTER_INEFFECTIVE)
vindicates the disciplined posture: the framing-resolved proceed did not over-commit — it ran a
TRAIN-design that cleanly refuted the cap without spending the holdout. No goalpost-moving occurred;
EXP-074's gate was never retro-edited, and EXP-075 re-ran no separation gate (it judged the cap on the
strategy's own economic legs).

## Verdict

```text
VERDICT: APPROVE
```

EXP-075 is complete and trustworthy. The exhaustion-cap lever is refuted on TRAIN, on the strategy's
own legs, across both cap forms and the full pre-declared percentile grid; the result is robust to the
pinned uplift bar at the disposition level. Registry disposition recorded; no TEST/holdout contact; the
locked filter is non-confirmatory and carried nowhere. The exhaustion-cap route is closed; the
CF-HA-HARAMI-001/CAND-001 family-closure decision is the pending **G-016** desk adjudication (separate
gate).
