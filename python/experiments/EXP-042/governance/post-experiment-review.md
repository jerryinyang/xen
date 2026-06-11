# EXP-042 — Post-Experiment Governance Review (Stage 8)

**Date:** 2026-06-11
**Artifacts reviewed:** `audit.md`, `results.md`, `report.md`,
`python/experiments/INDEX.md` and `docs/experiments-docs/INDEX.md` updates,
against the governance constraints and the Phase 011 design + D0
predeclarations.

## Checks

- **Audit quality:** independent re-implementation of the selection rule
  (0 mismatches over 51 cells), full end-to-end regeneration of one cell
  (exact match), structural checks over all 255 rows, determinism replay,
  hash verification, and explicit verification of the F01 loader fix.
  Evidence is concrete (values, counts, file paths). PASS.
- **Honest reporting:** the interpretation explicitly states that wider
  bands lost on event starvation rather than measured gross, that the
  per-event-economics comparison is unpowered and open, and that the 4h
  domain is unpowered for Track B — no inflation of the selection into an
  edge claim; all means labeled gross/descriptive/selection-internal. PASS.
- **Verdict supported:** `BAND_SELECTED_DEGENERATE_FLOOR_PENDING_ADJUDICATION`
  follows mechanically from the recorded floor fractions (0.65–1.00 at
  bands ≥ 1.5 vs the predeclared 0.50 threshold) and the amended scope's
  freeze-withholding clause. No goalpost movement: the rule's selection
  (band 1.0) is reported unchanged; only the predeclared escalation path
  was taken. PASS.
- **No scope creep:** no additional analyses, no re-ranking, no grid
  extension, no cost overlays appeared post-results. Follow-ups in
  `results.md` are framed as new scopes. PASS.
- **Holdout/TEST:** 0 TEST reads; no ledger entry required (TRAIN-only
  descriptive scan; `test-read-ledger.md` unchanged — correct). Sealed rows
  never entered the scan engine (audited). PASS.
- **Indexes:** both indexes updated; entries match the artifacts (verdict,
  floor fractions, power statement, audit status). PASS.
- **Disclosures carried:** entry-rule population discontinuity, F02 proxy
  limitation, DE30 truncation, and the small-n extreme means all appear in
  report/results. PASS.

## Required follow-through (recorded, not blocking)

1. The **operator adjudication** of the DEGENERATE_FLOOR outcome is the next
   pipeline action; its decision (accept band 1.0 with disclosure vs early
   FOUNDATION_NON-TUNABLE) must be recorded in the Phase 011 design
   amendment log and the multiplicity registry before any Track A/B work.
2. If band 1.0 is accepted, the EXP-042 power statement supersedes all
   band-era power analyses for Phase 011 planning, and the 4h power wall
   must be reflected in the Track B scope (predeclared expectation of
   non-tunable 4h cells or a pre-registered 4h exclusion decision).

## Verdict

```text
VERDICT: APPROVE
```

---

## Addendum — 2026-06-11: experiment set aside (FRAMING_ERROR)

The APPROVE above certified pipeline-process compliance (audit, interpretation,
documentation) and remains valid for that purpose. It did not — and a
subsequent post-execution review found it should have — re-examine whether the
arm-at-adverse-band entry rule matched the band multiplier's historical role.
It did not: the band was always an **exit parameter** (Phases 004–010;
registry `/BAND` is exit/structural), so EXP-042 measured a filtered
deep-pullback subpopulation and its results carry zero weight.

Final disposition: **MEASUREMENT_COMPLETE — FRAMING_ERROR** (set aside;
0 slots, 0 TEST reads). The §"Next pipeline action" items above are moot:
no adjudication occurs, Track A0 is removed from Phase 011, the entry-rule
amendment is rescinded (baseline arm/trigger restored), the band moves
entirely to Track B exit training, and power planning reverts to the design
§7.4 baseline rates pending Track A readiness measurement.

Root-cause review: `docs/code-reviews/2026-06-11-band-multiplier-framing-error.md`.
