# Post-Experiment Governance Review — EXP-044

**Date:** 2026-06-11
**Artifacts reviewed:** `audit.md`, `results.md`, `report.md`,
`python/experiments/INDEX.md` (EXP-044 row), `docs/experiments-docs/INDEX.md`
(EXP-044 section + Phase 011 status row), result files under `results/`.

## Audit (`audit.md`)

- Thorough across all required dimensions: correctness, holdout exclusion
  (F01 file-order TRAIN slice with post-collect chronology assertion —
  scoped convention, verified), look-ahead, anti-overfitting fence
  (NaN-masked real-trigger outcomes in both null paths), NaN handling, safe
  optimization (CI-shift algebra verified), determinism, code standards. PASS.
- Independent numerical validation is strong: all 100 cell×generator FPRs and
  all 50 coverage classifications recomputed from `draw_verdicts.parquet`
  with 0 mismatches; Wilson interval reproduced to full precision; substrate
  triggers, TPR monotonicity, and precision thresholds re-derived. PASS.
- One Warning is correctly classified as **latent**: the `tpr_usable` branch
  admitting an imprecise TPR point at point estimate ≥ 0.80 never fired
  (100% completion; max TPR half-width 0.0436 < 0.05), so no measured object
  is affected. Disclosed in `results.md` limitations and `report.md`. The fix
  is required only in a rerun scope — non-blocking here. PASS.

## Interpretation (`results.md`)

- Anchored to the predeclared interpretation guide: CALIBRATION_DELIVERED is
  the deliverable criterion exactly as scoped; METHOD_NOT_TRANSFERABLE and
  the >1/3-underpowered INCONCLUSIVE triggers checked and not met. PASS.
- Honest and non-overreaching: the marginal/material NOT_COVERED grading is
  preserved; the Monte-Carlo-noise alternative explanation for the 11
  marginal cells is stated alongside the conservative predeclared rule —
  no goalpost movement; the secondary α = 0.01 anti-conservatism, H_cal = 8
  horizon-transfer caveat, block-length-1 N2 weakness, and the 128 bps grid
  endpoint are all surfaced as limitations. Zero-baseline discipline held
  (bps differences and rates with Wilson CIs throughout). PASS.
- Next steps are new scopes or operator/governance actions, not extensions
  (the precision-only re-run is the predeclared draw-count lever). PASS.

## Report and indexes (`report.md`, INDEX files)

- Report is self-contained, embeds 2 of 5 plots (within guidance), links all
  artifacts by relative path, and introduces no claims absent from
  `results.md`/`audit.md`/raw outputs. PASS.
- `python/experiments/INDEX.md` row and `docs/experiments-docs/INDEX.md`
  five-field section verified against the result files (coverage counts,
  NOT_COVERED cell list, MDE medians, substrate-check values match
  `coverage_map.csv` / `run_metadata.json`). The Phase 011 status row
  correctly records leg (ii) as *measured* with G1 closure adjudication
  pending in `G1-gate-review.md` — documentation does not pre-empt the gate
  decision. PASS.

## Core constraints

- Holdout/TEST untouched; look-ahead-safe; per-event denominators only;
  no real event outcomes read (fence literal); non-parametric throughout;
  no scope creep (4/4 tests, 5/5 plots, 1/1 module; predeclared deviations
  only); honest negative tail (13 NOT_COVERED) reported as information.
  PASS on all.

## Verdict

```text
VERDICT: APPROVE
```

Note for any rerun scope: implement the audit's latent-warning fix
(classify cells whose MDE-defining TPR point fails precision as
CALIBRATION_UNDERPOWERED) before drawing.

---

## Revision 1 — 2026-06-11 (post-experiment adversarial review; re-approved)

Five findings assessed against the result files (recomputation from
`fpr_per_cell.csv` / `coverage_map.csv` / `draw_verdicts.parquet`):

- **F03 (Major, validated with corrected fix)**: the N1 > N2 FPR pattern is
  systematic — 35/50 cells (one-sided sign-test p ≈ 0.001), medians 0.041 vs
  0.030; 11/12 FPR exclusions fail on N1 only (USDJPY-4h is an N2-only
  failure, slightly miscounted in the finding as "only USDCAD" on N2 — it is
  the lone N2 failure). The Wilson non-overlap trigger is structurally
  insensitive to a ~0.01 offset at n = 500; "trigger not fired" ≠ "nulls
  agree". **Documented** in results.md Finding 4, report.md Finding 3, and
  both indexes. The finding's recommendation to *choose* a binding null is
  rejected as framed: the predeclared rule already requires both nulls, so
  the stricter N1 is binding by construction and no operator choice exists —
  re-basing on N2 would be post-hoc metric reselection, excluded by scope.
  The 12 exclusions stand.
- **F01 (Minor, validated)**: confirmed — all 11 marginal cells' Wilson 95%
  intervals include α₀ (only USDCAD-2h sits entirely above; USDJPY-4h's N2
  interval [0.037, 0.077] also includes α₀). Borderline-not-clear-excess
  note added to results.md Finding 1 for G1 interpretation. Classification
  itself correct per plan; no code change.
- **F04 (Minor, validated, no action)**: mitigated by results as stated —
  min 17–18 regimes per direction, 100% completion; BTCUSD-4h's MDE failure
  is count/volatility, not bootstrap coverage. No change.
- **F07 (retracted by reviewer)**: no action.
- **NEW-N1-FPR-PATTERN (Major, validated with corrected diagnosis)**: the
  domain spread (1h 3 / 2h 4 / 4h 5) and count-independence of N1 excess
  (Spearman ρ = 0.06 vs train_events; BTCUSD-1h at 273 events fails) are
  confirmed. The finding's control-pool-sparsity mechanism is **not**
  supported by the data: the N1−N2 gap correlates *positively* with regime
  count (ρ ≈ 0.40) and negatively with events-per-regime (ρ ≈ −0.32) — the
  sparsity story predicts the opposite sign. The documented diagnosis is
  within-regime real-return dependence (retained by N1, destroyed by the
  block-length-1 N2). The suggested investigation is recorded as an optional
  new diagnostic scope (results.md next step 4), not an in-scope analysis —
  per the no-post-hoc-analysis constraint.

All changes are documentation-only (results.md, report.md, both INDEX files);
no result file, classification, or code object was altered.

```text
VERDICT: APPROVE (Revision 1)
```
