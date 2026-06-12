# Post-Experiment Governance Review — EXP-045

**Date:** 2026-06-11
**Artifacts reviewed:** `audit.md`, `results.md`, `report.md`,
`python/experiments/INDEX.md` (EXP-045 row), `docs/experiments-docs/INDEX.md`
(EXP-045 section + Phase 011 status row), result files under `results/`.

## Audit (`audit.md`)

- Exceptional depth for a selection experiment: an independent from-raw-data
  naive reimplementation of one cell reproduced the published FH(3) net mean
  to full float precision and MAD(1.0) to 1e-14 — validating the loader,
  event regeneration, trend-change lookup, ladder-scan equivalence, the ns
  financing convention (the Revision-1 critical fix), and the P2 cost
  application in one pass. All 592 stability values, all 74 family
  classifications, and all 37 cell verdicts re-derived with 0 mismatches.
  PASS.
- Every Revision-1 fix verified present and exercised in the run
  (`endpoint_argmax` fired 42 times — the previously unreachable failure
  mode did real work; `verify_financing`/`verify_mad_scan` ran clean; DE30
  disclosure on every DE30 row; replay-cell assertion held). PASS.
- Issue classification appropriate: 0 Critical / 0 Warning / 3 Info, each
  Info a genuine reading aid, none affecting trust. PASS.

## Interpretation (`results.md`)

- Anchored to the predeclared guide: TRAINING_DELIVERED is the deliverable
  criterion; the empty membership is reported as the honest substantive
  answer, with the G2 FOUNDATION_NON-TUNABLE consequence correctly framed
  as a pending governance act, not an experiment verdict. PASS.
- No goalpost movement and no rescue attempts: the 4h net-positive grid
  points are explicitly disqualified as winner's-curse bait using the
  EXP-044 power map; the cost-model and conservative-rule dependencies are
  stated as limitations without proposing in-phase relaxation (BASE costs
  and grid extension correctly identified as excluded). The "empty
  membership is *more* credible given upward TRAIN bias" reading is sound.
  PASS.
- Zero-baseline discipline: all values reported as bps levels with SEs;
  the gross proxy is an additive decomposition, not a ratio. PASS.
- Next steps are governance acts or future-phase scopes (`/ENTRY` route per
  design §9), not extensions. PASS.

## Report and indexes (`report.md`, INDEX files)

- Report self-contained, embeds 2 of 5 plots, links all artifacts, and
  introduces no claims absent from results/audit/raw outputs; the headline
  numbers (0/37, reason counts, plateau values, net medians, gross proxy
  31/37, 4h bests) all match the result files. PASS.
- Both index entries verified against `exit_selection.csv` /
  `run_metadata.json`; the Phase 011 status row records Track B complete
  and the FOUNDATION_NON-TUNABLE path as **pending G2 adjudication** —
  documentation does not pre-empt the gate. DE30 disclosure carried. PASS.

## Core constraints

- Holdout/TEST untouched (0 reads; fences asserted); look-ahead-safe;
  per-event denominators only; frozen constants untouched; no scope creep
  (2/2 tests, 5/5 plots, 1/1 module); negative result reported as a
  first-class finding. PASS on all.

## Verdict

```text
VERDICT: APPROVE
```
