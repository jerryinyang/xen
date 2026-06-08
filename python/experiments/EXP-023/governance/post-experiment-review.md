# EXP-023 Post-Experiment Governance Review

**Stage:** 8 (post-experiment, consolidated pipeline governance)
**Date:** 2026-06-08
**Artifacts reviewed:** `audit.md`, `results.md`, `report.md`,
`python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`,
`docs/signal-registry/multiplicity-registry.md`.

```text
VERDICT: APPROVE
```

Final verdict after one revision cycle. The initial Stage 8 review issued
`REVISE` (file-drawer ledger not updated for completed experiments); the
revision was implemented and re-reviewed — see "Revision cycle 1" below.

## Checks (all PASS)

- **Audit (`audit.md`)** — Thorough across correctness, edge cases, type safety,
  NaN handling, holdout exclusion, look-ahead, real-price, and timestamp
  alignment; evidence-based with line numbers and a bit-exact BTCUSD/5m
  recomputation; severity classification appropriate (0 Critical / 0 Warning /
  6 Info). PASS.
- **Results (`results.md`)** — Honest, non-overreaching REFUTED interpretation
  anchored to the predeclared Evidence-AGAINST criteria; effects quantified vs
  frozen floors with CIs; explicitly declines to read the sub-floor 4h positives
  as edge; limitations and alternative explanations present; next steps framed
  as new scoped experiments. PASS.
- **Report (`report.md`)** — Self-contained; key plots referenced with captions;
  honest about the negative result and limitations; artifacts linked by relative
  path; correctly frames a baseline-branch negative, not a family retirement.
  PASS.
- **Experiment indexes** — Brief `INDEX.md` row and comprehensive
  `docs/experiments-docs/INDEX.md` five-field section + updated active-checkpoint
  status row are present, accurate, and consistent with the results. PASS.
- **Multiplicity / file-drawer registry** — Updated this cycle: Candidate Ledger
  HYP-002/HYP-003/HYP-004 now SCREENED with correct outcomes, File-Drawer Ledger
  carries the EXP-021/022/023 rows (including the first FULL screen, EXP-023
  REFUTED), and the header reflects the screened-and-refuted state. The Frozen
  Qualification Suite floors, Batch 004-A budget, and Amendment Rules are
  unchanged. PASS.
- **Core constraints** — Single hypothesis; holdout sealed and fence verified;
  real-price `RealClose` discipline; `SourceCloseTime` alignment; complexity
  budget respected (4/4 tests, 5/5 plots, 3/3 modules); no scope creep (the
  post-execution metric-book fix was scope-faithful, no amendment); phase-aligned
  — EXP-023 is the planned terminal baseline-chain screen and REFUTED is a valid
  Phase 004 outcome, correctly recorded as a baseline-branch negative rather than
  COMPONENT_REFUTED of CF-AVWAP-001 (`design.md` §8). PASS.

## Revision cycle 1 (resolved)

- **Issue:** the Phase 004 file-drawer ledger
  (`docs/signal-registry/multiplicity-registry.md`) had not recorded the
  completed EXP-021/022/023 outcomes; CF-AVWAP-001/HYP-004 (EXP-023) sat at
  PLANNED and the header read "no full candidate screened," contradicting
  `design.md` §3 and the registry's binding file-drawer purpose.
- **Resolution (experiment-documenter):** header status line, Candidate Ledger
  rows HYP-002/003/004, and the File-Drawer Ledger (note line + three 2026-06-08
  rows) updated to the recorded outcomes; protected sections (suite floors,
  budget, amendment rules) verified unchanged; no `PLANNED` rows remain.
- **Re-review:** the routed issue is fully addressed with no collateral change.
  APPROVE.

## Disposition

EXP-023 is complete and governance-approved. The science, audit, interpretation,
report, experiment indexes, and the programme-level file-drawer ledger are all
sound and consistent. The baseline CF-AVWAP-001/HYP-004 screen is a clean,
admissible REFUTED on the first-70% analysis set. No further action required for
EXP-023; any follow-up is a new scoped experiment on a registered non-baseline
branch.
