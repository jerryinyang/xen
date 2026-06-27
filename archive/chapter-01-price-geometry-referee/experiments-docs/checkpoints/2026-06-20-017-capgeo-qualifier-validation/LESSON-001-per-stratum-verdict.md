# LESSON-001 — Per-stratum verdict representation (anti-reversion guard)

**Date:** 2026-06-20. **Origin:** EXP-076 (`ASS`/VAL-001) audit finding **C1**.
**Status:** BINDING for all subsequent experiments in this family (and the programme generally).
**Scope:** verdict *representation* — how `results/verdict.json` and the experiment's headline
PASS/FAIL are constructed. Not a new statistical rule; an enforcement of an existing doctrine.

---

## The doctrine (pre-existing — this is enforcement, not a new principle)

- `cf-capgeo-001.md:137` — "**Default to per-stratum adjudication;** any pooled statistic is a
  disclosure until cross-cell homogeneity is itself demonstrated."
- `cf-capgeo-001.md:204` — "No pooling across substrates (or across cells) without a
  demonstrated-homogeneity claim."
- `D0-predeclarations.md:139` — "Scoring outputs (all emitted, **none collapsed**)."
- `D0-predeclarations.md:171–173` — "exactly **one** verdict per stratum. (The Phase 018 verdict
  **conjunction** is a Phase 018 D0 item.)" → a cross-stratum conjunction is *reserved* and is not an
  experiment's to bake in unilaterally.
- Precedent that this masks real findings: **EXP-074** — "the disclosed pooled `NO_SEPARATOR` MASK
  the real finding" (a near-universal q05-tail separator hidden by an all-framing pooled gate).

## What went wrong in EXP-076 (the failure mode to prevent)

The estimator and data layer were **compliant** (`xen.ass` emits expectancy + median + tail, none
collapsed; every `(type, n)` cell is in `recovery/coverage/shrinkage.csv`). **No statistic was
pooled.** The violation was solely in the **orchestration's verdict object**:

```python
cov_pass = bool(cov_df["pass"].all())              # collapse across all 99 cells
overall  = rec_pass and monotone and ... and (cov_pass in (True, None))
verdict["overall_pass_literal"] = bool(overall)    # emitted as THE headline
```

`overall_pass_literal=false` was read as a blanket FAIL when in fact **194/198 cells passed** — the
collapse hid that the only issues were the n=15 expectancy sparse-stress floor and one predeclared
n=2000 shrinkage marginal. The entire Stage-5 verdict-forensics section existed only to *un-collapse*
the boolean back to per stratum — proof the collapsed object was the wrong verdict.

It slipped through because (1) `scope.md` phrased PASS as "all three hold on **every** (type,n) cell"
(reads like an `.all()` mandate), (2) Stage-4 pre-exec reviewed the bands but not the verdict's
*shape*, and (3) the Stage-5 audit initially under-classified it as a soft Warning.

## The binding rule (checkable)

For every experiment from here on:

1. **The binding verdict is reported per stratum** (per domain / instrument / cell / `n`). Each
   stratum carries its own PASS/FAIL/diagnostic. Coverage-type checks are resolved **per `n`**, never
   AND-ed across `n` into one boolean.
2. **No single collapsed cross-cell/cross-stratum PASS/FAIL is binding.** A collapsed conjunction
   (`.all()` over cells) or any pooled statistic is a **disclosure only** and must be **explicitly
   captioned non-binding** in the emitted artifact, unless cross-stratum homogeneity is itself
   demonstrated and recorded.
3. **The binding/diagnostic stratum boundary is a governance decision**, not an experiment's to
   prejudge — report the per-stratum facts and mark contested boundaries "PENDING D0-amendment".

Reference implementation: `python/experiments/EXP-076/code/run_experiment.py::build_verdict` (pure,
per-stratum) + the `collapsed_convenience_flag` pattern (value + explicit NON-BINDING caveat).

## Where this is now enforced (so it cannot silently revert)

- **Stage 4 (pre-execution) and Stage 8 (post-experiment) governance** — added to
  `research-pipeline/references/governance-constraints.md`:
  - Code-section check **"Verdict representation (per-stratum)"** (catches it proactively at Stage 4
    pre-exec, before the run);
  - a matching **REVISE trigger** in the Verdict Framework.
- This lesson file — cite it in future scope/design docs that define a PASS/FAIL verdict.

## Checklist for the next experiment author

- [ ] `verdict.json` has a per-stratum structure; no top-level `overall_pass_*` boolean treated as
      the verdict.
- [ ] Any collapsed/pooled field is named and captioned **non-binding**.
- [ ] Multi-`n` (or multi-cell) checks report per `n`/cell; binding boundaries that need governance
      are flagged "PENDING", not decided in code.
- [ ] `scope.md` PASS criteria are phrased as per-stratum adjudication, not a single `.all()` mandate.
