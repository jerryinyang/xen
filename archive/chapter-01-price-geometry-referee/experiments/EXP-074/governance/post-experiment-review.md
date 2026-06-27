# EXP-074 — Post-Experiment Governance Review (consolidated Stage 8)

**Date:** 2026-06-19
**Reviewer:** research-pipeline (consolidated Stage 8)
**Artifacts reviewed:** `audit.md`, `results.md`, `report.md`, index updates
(`python/experiments/INDEX.md`, `docs/experiments-docs/families/cf-ha-harami-001/INDEX.md`,
`docs/experiments-docs/INDEX.md`), and signal-registry updates
(`candidate-families/harami.md`, `multiplicity-registry.md`, `test-read-ledger.md`).

## Checks

**Holdout & TEST fence.**
- Audit confirmed `load_train_1m` slices `[0, train_cutoff)` only; the next-21% TEST stratum and
  the final-30% holdout are never sliced/materialized; forward resolution clips at the TRAIN edge.
  **0 counted TEST reads, holdout untouched.** ✓
- `test-read-ledger.md` explicitly records EXP-074 as a TRAIN-only diagnostic that moves no tally. ✓

**Real-price discipline.** `r_e` is the certified EXP-068 `N-PARTIAL-V2A` real-price arm; HA used
only for harami detection. ✓

**Audit integrity.** CONDITIONAL PASS (0 Critical, 2 Warnings, 3 Info). Both Warnings are
interpretation findings, not code defects, and were carried verbatim into `results.md` and
`report.md`:
- W1 `favdist_atr` ≡ 0.5·`msofar_atr` (V2A geometry; effective surface 13). ✓ disclosed.
- W2 the all-framing consistency gate masks the H1 tail-shape signal. ✓ led the interpretation.
The orphan plot `02_separator_share.png` (Info I1) was removed; 6 plots remain. ✓

**Interpretation soundness.**
- `results.md` leads with the gate-masking finding and the stratified read, not the pooled
  NO_SEPARATOR, per the binding emphasis. ✓
- No goalpost-moving: the binding per-domain verdict is **retained as written** and explicitly
  relabelled "no location-monotone uniform lever"; the consistency gate is **not** retro-edited; the
  gate-collapse decision is routed forward into EXP-075's own pre-registration (`D0-amendment-007`).
  This is the correct governance posture for a post-hoc methodological observation. ✓
- H2 refutation, the 13-vs-14 feature correction, and the per-domain power handling (2h/4h
  INCONCLUSIVE) are all stated with their numbers. ✓
- No filter selected, no parameter tuned, no candidate slot consumed, no scope expansion. ✓

**Signal-registry disposition (required).** Result is registry-relevant; updates applied in this
change:
- `candidate-families/harami.md`: CF-HA-HARAMI-001 stays REGISTERED / OPEN; CAND-001 path **not
  closed**; EXP-074 disposition + gate-masking note recorded; routes to EXP-075. ✓
- `multiplicity-registry.md`: HYP-027 / EXP-074 outcome recorded (CHARACTERISATION_DELIVERED; no
  location-monotone uniform lever; H1 strong on q05 tail; H2 refuted; `favdist_atr` redundant; item
  retained, not deleted). HYP-028 / EXP-075 conditional row updated to ACTIVATED with the
  tail-framing pre-registration requirement. ✓
- `test-read-ledger.md`: unchanged tallies; explicit 0-counted-read disclosure added. ✓

**Index updates.** `python/experiments/INDEX.md` row added; family detail card + ToC entry added to
`families/cf-ha-harami-001/INDEX.md`; master `INDEX.md` live status + Family Indexes table updated
(no per-experiment card added to master). ✓

## Verdict

```text
VERDICT: APPROVE
```

EXP-074 is complete and trustworthy. The binding verdict stands as registered; the
operator-emphasized stratified, tail-framing finding (H1 separates the q05 loss tail near-universally
but is masked by the consistency gate) is correctly surfaced as the headline and routed — without
retroactive criterion changes — into EXP-075's pre-registration. Registry disposition recorded; no
TEST/holdout contact. G-016 desk adjudication pending (separate gate).
