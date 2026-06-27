# EXP-078 — Pre-Execution Governance Review (Stage 4)

**Experiment:** EXP-078 — Shape Discrimination + `k`-Sensitivity (`ASS/VAL-003`, Phase 017 CF-CAPGEO-001)
**Reviewer:** research-pipeline consolidated governance
**Date:** 2026-06-20
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, `xen.ass` extension
**Governing D0:** `checkpoints/2026-06-20-017-capgeo-qualifier-validation/D0-predeclarations.md` (RATIFIED/FROZEN)

---

## Constraint evaluation

### Core constraints
- **Simplicity over complexity** ✓ Shape discrimination = a Monte-Carlo false-positive/true-positive
  rate with binomial Wilson CIs (the simplest sufficient method on labelled synthetic populations);
  `k`-sensitivity = re-running existing EXP-076/077 dispositions across a pre-registered grid (no new
  endpoint). One new dependency (`diptest`) is justified: it wraps Hartigan's reference dip statistic
  — the literature-standard, auditable computation — rather than a hand-rolled bootstrap p-value for a
  binding gate.
- **No academic-finance pitfalls** ✓ Distribution-free dip-test + robust mean–median/MAD gap +
  percentile bootstrap; no normality/stationarity/i.i.d./constant-vol assumption. The synthetic DGPs
  are the *known-truth substrate*, not a market model.
- **Strict scoping** ✓ Single question (does the shape diagnostic discriminate + is `ASS` `k`-robust);
  boundaries explicit (synthetic only, frozen types/`n`/grid); concrete success/failure/inconclusive
  criteria; budget respected (see below); no bonus analyses.
- **Framework principles** ✓ Data-driven, non-parametric-by-default, per-stratum adjudication. Real-
  price discipline is **N/A (synthetic ATR units)** and is explicitly stated in scope, plan, and code;
  no HA/Renko prices anywhere.
- **OOS holdout** ✓ No market data, no Parquet loader, no holdout/TEST stratum touched. Verified: the
  code imports `from xen import ass` only — the standard first-70% timebars loader is absent by
  construction. The integrity anchor reads prior `results/integrity.json` (JSON metadata), not bars.
- **Look-ahead** ✓ N/A (no time-ordered market data). Determinism enforced; `k` never enters a draw
  seed (paired draws); the dip p-value is the analytic Hartigan value (no RNG).
- **Real-/synthetic-price discipline** ✓ N/A-synthetic, stated.
- **Safe performance** ✓ Bounded memory, `tqdm` over `(type,n)`/`(type,n,k)` cells, order-stable
  process-pool parallelism (byte-identical at any worker count), no causality breach (synthetic).

### Scope document
- Hypothesis falsifiable/specific ✓; success criteria measurable ✓; data views/boundaries/exclusions
  explicit ✓; complexity budget realistic ✓; holdout exclusion stated ✓; real-price rule stated
  (synthetic) ✓.
- **Gate-threshold calibration** ✓ `τ_gap = 0.30` is the D0 bite-check ROC operating point (feasible
  window [0.105, 0.435]; @0.30 false-flag 0.000 / detection 0.999); `FF_TARGET=0.05`/`DET_TARGET=0.80`
  are the frozen D2.5 values; the `k`-grid is a pre-registered sensitivity band shown routing-invariant.
  The `Wilson-hi ≤ 0.075` ceiling is disclosed as the EXP-077 FPR convention (borrowed, disclosed, and
  consistent with the programme standard). No unjustified magic constants.

### Analysis plan
- Method justification with "why / simpler alternative" on every step ✓; assumptions listed ✓;
  visualisations purposeful ✓; interpretation guide pre-registered (if-X-then-Y) ✓.
- **Per-stratum endpoints** ✓ Binding verdicts per type/`n`/`k`; pooled = disclosure-only.
- **Shape-aware read** ✓ This experiment *is* the predeclared shape-aware escape hatch closing the
  EXP-074 tail-shape-blind-guard gap (per-leg dip-vs-gap decomposition predeclared).
- **Robust + raw endpoints** ✓ The diagnostic emits both legs; the `k`-sweep exercises the raw
  expectancy edge-call. Cross-leg tensions (skew routing; `k`↔shape independence; FPR↔margin
  non-circularity) are resolved concretely, not hand-waved.
- Budget: 3 validation checks / 4 plots / 0 new modules + 1 in-family `xen.ass` extension ✓.

### Code (`code/run_experiment.py` + `xen.ass.shape_diagnostic`)
- **Plan compliance** ✓ Implements exactly the 3 checks + integrity anchor + determinism + 4 plots;
  nothing extra.
- **Holdout/look-ahead/real-price** ✓ N/A-synthetic; no loader path exists.
- **Type hints / docstrings / PEP8 ≤100 / ruff** ✓ (ruff clean; 0 lines >100; functions focused).
- **NaN/edge cases** ✓ `MAD==0` branch explicit (`g=0`, `gap_flag=False`, `mad_zero` counted) with a
  hard `assert mad_zero_total == 0`; `shape_diagnostic` guards `n<4`.
- **No magic numbers** ✓ All thresholds sourced from D0 (`ass.TAU_GAP/DIP_ALPHA`, D2.5 targets, D3
  grid); the one borrowed constant (Wilson 0.075) is documented.
- **Verdict representation (per-stratum)** ✓ — the EXP-076 audit-C1 precedent is honored directly: the
  verdict is a per-stratum `strata` dict (shape U/B per `n`; k-sensitivity per `(null,n)`); the single
  `collapsed_convenience_flag` is explicitly labelled **NON-BINDING**.
- **Organization/sectioning/import-side-effects/logging/progress/plot-memory/determinism** ✓ All pass;
  output dirs created in `main()` only; analytic-dip + seeded draws give a byte-identical second pass
  (`--verify-determinism`); plots consume bounded result tables.

## Disclosed design decisions (Info — accepted, D0-faithful)

1. **Deployed `k` = median(SP population n) = 120**, not median(`N_GRID`) = 250. This is the correct
   reading of D0 §D3 ("k default = median **sample size across signal types**") and equals EXP-076's
   actual `k_shrink`, so `1×` is the true deployed operating point the sweep must probe. Both medians
   are recorded in `integrity.json`. The analysis-plan's looser "median of N_GRID" phrasing is
   superseded by this D0-faithful choice; **disclosed, not a parameter change**.
2. **K1 binding label = monotone ∧ sparse-pull ≥ 0.25**, with the rich-pull `<0.05` bound reported as
   a disclosed k-dependent marginal (not a gating flip). This mirrors EXP-076's existing disposition,
   which predeclared the n=2000 marginal (0.0566 at k=120) as "not a fail"; folding it into a hard
   label would manufacture a spurious routing flip. **Correct and disclosed.**

Both are faithful refinements within the frozen D0, surfaced for the post-experiment audit to confirm.

## Integrity pre-checks (lightweight, no binding artifacts written)
- Cross-experiment anchor reconciles to **both** EXP-076 (0.07605…) and EXP-077 (0.12788…) at diff
  **0.0** — the shape extension did not perturb the `xen.ass` core or the seed scheme.
- `shape_diagnostic` behaves as designed (U not flagged; B flagged via the gap leg with dip≈0 — the
  per-leg decomposition will surface this substantive finding, not a defect).
- Full `k`-sensitivity routing path assembles (`ROUTING_INVARIANT` at tiny scale); `results/`/`plots/`
  remain empty (manual execution gate intact).

---

## Verdict

```text
VERDICT: APPROVE
```

All core and artifact-specific constraints pass. No Critical or Warning findings. Two Info-level
disclosed design decisions (deployed-`k` = SP median; K1 rich-pull disclosed-not-gating), both
D0-faithful and recorded for the Stage-5 audit. The per-stratum verdict doctrine (LESSON-001 /
EXP-076 audit C1) is correctly implemented. Proceed to the manual execution gate.
