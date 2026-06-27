# Post-Experiment Governance Review: EXP-046

**Date**: 2026-06-12
**Artifacts reviewed**: `audit.md`, `results.md`, `report.md`,
`python/experiments/INDEX.md` (EXP-046 row), `docs/experiments-docs/INDEX.md`
(EXP-046 section), against `references/governance-constraints.md`.

## Checks

### Audit (`audit.md`)

- Thoroughness: PASS — correctness, edge cases, NaN handling, holdout
  exclusion, loader ordering, safe optimization, organization, plot reuse,
  and the modified `xen.avwap` parameterization all covered with file/line
  evidence.
- Numerical validation: PASS — all 259 floors, margins, verdicts, the
  H8 cross-table consistency, and the rollup independently recomputed with
  zero discrepancies; ranges and row counts verified; P8 regression gate
  re-run green (24/24 tests).
- Severity classification: PASS — 0 Critical / 0 Warning / 3 Info, each
  Info note appropriate (0**0 convention, shared-mask transparency,
  predeclared CLEAR-concentration channel).
- Real-price / timestamp discipline: PASS — domain-bar real closes only;
  single data view, fixed-offset indexing within one sorted frame as the
  plan explicitly sanctioned.

### Results (`results.md`)

- Honest reporting: PASS — REFUTED stated plainly; FLAT not softened by the
  14 clearances; effect sizes (~1–2 bps medians vs 5–20 bps floors) given
  with n.
- Uncertainty/caveats: PASS — the three G1-adjudication caveats carried
  verbatim from the analysis plan, plus descriptive-SE, unmatched-population,
  and TRAIN-only limitations.
- Verdict supported: PASS — mechanical count (best 3 cells vs ≥5/≥3
  threshold) on a clean integrity grid (259/259 reconciliation at 1e-9 bps,
  259/259 determinism).
- No goalpost movement: PASS — frozen D0 rules applied verbatim;
  near-misses and the margin-pass/sign-fail row reported but not promoted.
- Next steps: PASS — substrate pivot as a new phase design and a
  conditional new EXP; no scope extensions.

### Report (`report.md`)

- Self-contained, honest, key plots only (3 of 4 embedded), all artifacts
  linked by relative path: PASS.
- No claims absent from `results.md`/`audit.md`/raw outputs: PASS.

### Indexes

- `python/experiments/INDEX.md`: EXP-046 row inserted after EXP-045, before
  the VAL block; status REFUTED with a one-line finding consistent with the
  report: PASS.
- `docs/experiments-docs/INDEX.md`: five-field section appended
  (Hypothesis Tests / Scope / Results / Hypothesis-Specific Conclusion /
  Hypothesis-Agnostic Observations); observations are direct and
  unambiguous: PASS.

### Core constraints

- Holdout: never loaded (F01 TRAIN-only slice, boundaries asserted against
  EXP-043); 0 TEST reads — PASS.
- Look-ahead: sequential frozen generator; evaluability fence excludes
  windows crossing `train_end_ts` — PASS.
- Scope/complexity: 0/0 binding tests, 4/4 plots, 1/1 new module; no bonus
  analyses — PASS.
- Non-parametric/data-driven: descriptive cluster bootstrap only, no
  distributional assumptions, no significance claims — PASS.

## Verdict

```text
VERDICT: APPROVE
```

EXP-046 closes as COMPLETED (hypothesis REFUTED — ENTRY_GROSS_FLAT). G1
adjudication proceeds in the Phase 012 checkpoint `G1-gate-review.md`.
