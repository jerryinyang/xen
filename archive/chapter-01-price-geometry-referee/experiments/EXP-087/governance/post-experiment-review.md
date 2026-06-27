# EXP-087 — Post-Experiment Governance Review (Stage 8)

**Reviewed:** `audit.md`, `results.md`, `report.md`, and index/registry updates.
**Against:** `research-pipeline/references/governance-constraints.md`, `_pipeline-config.md`, Phase 019 checkpoint design + D0/D0-amendment-002.
**Date:** 2026-06-22

---

## Audit completeness — PASS

The audit (`audit.md`) is thorough and carries the mandatory **verdict forensics**, run autonomously (not
contingent on anyone questioning the result):

- **Per-stratum re-derivation + masking check (PASS):** the audit re-derived the verdict per (domain ×
  primitive) — 15m mean Δ̂ −0.279/−0.244, 1h −0.152/−0.140, 4h −0.024/+0.084 — and **affirmatively confirms
  the pooled `S_X=1` headline is not masking heterogeneity**: the per-stratum picture is uniformly negative,
  degrading at fast domains, with no separating stratum being averaged away. This is exactly the per-stratum
  masking check the constraint framework requires.
- **Mechanism statement (PASS):** late entry — the decile fires *after* the trailing-20-bar relative move, so
  the conditioned entry shows no favourable continuation beyond a direction-matched random clock
  (short-horizon mean-reversion/exhaustion). A concrete driver, not a re-statement that the number missed the
  bar.
- **Gate-shape check (PASS):** location read on a location effect, shape-appropriate; unsaturated (max
  attainable S=46, S*=1 ≪ 46) → genuine "no effect," explicitly distinguished from "an effect the gate
  cannot see." The two beats are correctly diagnosed as small-cell multiplicity artefacts the joint null
  absorbs.

Numerical validation is present (per_event rows 617,446 == Σ n_cond exact; direction-mix exact match all 92
cells; fav_mfe ≥ 0; event floor correctly applied). Holdout exclusion, look-ahead/causal-fill, and real-price
discipline are all verified with line references.

## Materiality discipline — PASS

The audit found **0 Critical, 0 Warning, 2 Info**. Both Info findings carry explicit materiality reasoning
showing they cannot move any verdict-bearing number:
- the stale `S_M` label in the disposition *string* is display-only (binding JSON fields correctly labelled
  `S_X`); the gate module is the frozen, hash-recorded EXP-086 artifact and must **not** be retro-edited;
- `causal_fill_ok=True` is a statically-true constant justified by the searchsorted construction.

No verdict-material finding was documented-and-down-classified. No fix-and-rerun was required, correctly.

## Per-stratum verdict doctrine — PASS

The binding research output is the per-cell beats-random table plus the predeclared D2b axis gate
(`S_X` vs `S*`), emitted in full (`cell_availability.*`). The only `.all()` collapses (`recon_all`,
`determinism_ok`) are process-integrity HALT gates, explicitly non-binding — not the research verdict.
The provisional axis disposition is captioned NON-BINDING throughout (G-019 is binding). Consistent with
LESSON-001 and the EXP-076 C1 precedent.

## Results interpretation — PASS

`results.md` reports honestly: a clean negative, with uncertainty (perm-p, ranking z, FWER band, MC
stability) and sample sizes throughout. It correctly distinguishes **`NOT_ADMITTED` (dead-by-absence, S=1
below the [17,28] band) from `EXONERATED` (S inside the coin-flip band)** and states precisely what G-019
reads (axis perm-p + ranking z into the cross-axis Holm). Next steps are framed as a separate future scope
(cross-sectional *reversion*), not a scope extension. No overreach.

## Signal-registry disposition — PASS

A registry disposition is recorded, and the result is registry-relevant — all updates applied in the same
change:
- **candidate-family** (`family-selection-phase-019.md`): CF-XSECT-001 advanced to `DRAFT — SCREEN-X-DELIVERED,
  PROVISIONALLY NOT_ADMITTED (NON-BINDING, BELOW D2a BAND), PENDING-G-019` with realized statistics. The
  family is **not** finally exonerated/screened here — correctly deferred to G-019.
- **multiplicity-registry**: the EXP-087 row records the outcome for both countable primitives
  (`COND-XSRANK` + `COND-XSDIV`: provisional NOT_ADMITTED, below band); items **retained**, not deleted or
  renamed; the Phase 019 summary line updated.
- **test-read-ledger**: EXP-087 disclosure entry added; **0 counted TEST reads** (TRAIN-only availability
  disclosure, no stratum-specific inference); all 48 strata remain 0/2 open, tallies unchanged.

## Index updates — PASS

`python/experiments/INDEX.md` row added; the detailed five-field card added to
`docs/experiments-docs/families/family-selection-phase-019/INDEX.md` with its ToC entry; the master
`docs/experiments-docs/INDEX.md` live-status (`Current Checkpoint Status`) and `Family Indexes` table updated
with **no per-experiment card** added to the master. Correct division per convention.

## Core-constraint spot checks — PASS

Holdout untouched (TRAIN sub-split only, `counted_test_reads=0`); causal cross-sectional construction
(backward-only forward-fill, alignment by `CloseTime`); real-price discipline (every figure on real domain
OHLC, no synthetic price); non-parametric throughout (median, proportion, moving-block bootstrap,
label-permutation); complexity budget honoured (2/2 tests, 4/4 plots, 1/1 module); gate thresholds frozen
pre-data with a pre-registered FWER sensitivity band shown routing-invariant.

---

## VERDICT

```text
VERDICT: APPROVE
```

The audit carried verdict forensics with an affirmative per-stratum masking check, a concrete mechanism
statement, and a gate-shape check; no verdict-material finding was down-classified; a signal-registry
disposition was recorded with all registry-relevant files advanced in the same change (items retained, 0
counted reads, holdout untouched); indexes are correctly updated. EXP-087 is complete.
