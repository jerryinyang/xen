# Audit Report: Experiment EXP-044

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 1
- **Info Notes**: 4

Audit basis: full read of `scope.md`, `analysis-plan.md`,
`code/run_experiment.py`, `code/cell_calibration.py`, all five result files,
and independent recomputation of every per-cell FPR, the classification logic
for all 50 cells, the substrate-check triggers, and the Wilson intervals from
the draw-level parquet.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Pipeline matches the plan: 500 N1 + 500 N2 null draws, edges {1..128} evaluated per N1 draw, frozen single-cell rule `effect>0 ∧ ci_low>0 ∧ p≤α`, no Holm, no pooling. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `load_train_frame` lazily scans, projects columns, `head(train_rows)` with `train_rows = floor(0.7·floor(0.7·total))` — TEST/holdout rows never collected. File-order slicing is the scoped F01 convention (identical to EXP-043); strict chronological order and uniqueness of `CloseTime` are asserted post-collect, and the TRAIN-end timestamp is bound to the EXP-043 boundary record. |
| `code/run_experiment.py` | Loader ordering | PASS | Per scope, F01 uses file-order rows (not a re-sort); the post-collect `is_sorted()` + `n_unique()` assertion makes any unsorted source a hard failure rather than silent contamination. |
| `code/run_experiment.py` | Dependency gates | PASS | EXP-043 verdict/`substrate_alert` gate, readiness↔power cross-check (50 cells, JP225-2h excluded), source-identity binding (file name, total/TRAIN rows, TRAIN-end ts), per-cell regenerated-event-count consistency gate — all hard-fail. |
| `code/run_experiment.py` | Safe optimization | PASS | Bootstrap-once/CI-shift is exact: the event-weighted mean and every cluster-bootstrap replicate (`num/den` with `num += g·cnt`) shift by exactly +g under a uniform per-event drift, so percentile CI endpoints shift by +g. The sign-permutation p is correctly *recomputed* per g (sign flips of shifted data are not a shift). |
| `code/run_experiment.py` | Progress / logging | PASS | `tqdm` over the 50-cell outer loop with per-cell postfix; helpers return data; output concise. |
| `code/run_experiment.py` | Import side effects / organization | PASS | `mkdir` only in `main()`; `matplotlib.use("Agg")` before pyplot; VAL-001-style sectioning throughout. |
| `code/run_experiment.py` | Plot data reuse | PASS | All five plots consume the aggregated summary rows; no reloads or re-generation. |
| `code/cell_calibration.py` | Correctness | PASS | Placement (largest-remainder allocation + exact-count in-pool placement with pool-restricted pyramids), control matching, segment-mean control averaging, regime-cluster bootstrap, and sign permutation verified by reading; vectorized control matching is additionally guarded at runtime by `verify_control_matching()` against the EXP-021-style reference (would raise before any draw). |
| `code/cell_calibration.py` | Look-ahead | PASS | Placement/matching use only regime intervals, pool membership, and bar indices; forward `H_CAL` returns enter only as outcomes; pools end at `n-1-H_CAL` so every event/control has a valid window. |
| `code/cell_calibration.py` | Anti-overfitting fence | PASS | Real trigger bars excluded from every pool **and** NaN-masked in both N1 and N2 outcome arrays (`dlog_real[real_trigger] = nan`, same mask re-applied to each N2 array) — an accidental gather would propagate loudly. No real event outcome is computed anywhere. |
| `code/cell_calibration.py` | NaN handling | PASS | NaN-masked outcomes propagate into paired diffs; `_control_mean` returns NaN at zero controls; reportability gate (≥30 events, ≥8/direction, ≥3 controls) excludes degenerate draws explicitly; non-finite MDE is `null`, never 0. |
| both | Type safety / docstrings | PASS | Typed dataclasses and signatures; docstrings with semantics on all public functions. |
| both | Determinism | PASS | All randomness flows through `seed_for(EXP-044, instrument, domain, generator/g, purpose, draw)`; two-cell replay (BTCUSD-1h, JP225-4h) is a full re-run compared frame-identically; `determinism_pass: true` recorded. |
| both | Memory/performance | PASS | Per-instrument 1-minute frame loaded once and freed; per-cell precompute once; chunked bootstrap/permutation (`BOOT_CHUNK`/`PERM_CHUNK`); 250,000 bounded draw rows persisted. |

## Numerical Validation

### Spot Checks (independent recomputation from `draw_verdicts.parquet`)

- **FPR**: recomputed FPR, reportable-draw counts, and total-draw counts for all
  100 (cell × generator) points at α₀ = 0.05 directly from the per-draw rows
  using the decision rule — **0 mismatches** against `fpr_per_cell.csv`.
- **Wilson interval** (AUDJPY-1h, N1, α₀): k = 18, n = 500 →
  (0.021334, 0.053772, half = 0.016219) — matches the CSV to full precision.
- **Classification**: re-derived the verdict and MDE for all 50 cells from
  `fpr_per_cell.csv` + `tpr_mde_per_cell.csv` using the predeclared rule order
  (completion/precision → material excess → point excess → finite MDE) —
  **0 mismatches** against `coverage_map.csv` (37 COVERED, 13 NOT_COVERED,
  0 UNDERPOWERED).
- **Substrate check**: recomputed two-null Wilson-interval disagreement
  ({AUDUSD, USDCAD} — 2 instruments, below the ≥3 trigger) and domain-wide
  excess (none in 1h/2h/4h) — matches `run_metadata.json`
  (`triggered: false`).

### Range Checks

| Metric | Expected Range | Actual | Pass? |
|--------|---------------|--------|-------|
| Draw rows | 50 cells × (500×9 N1 + 500 N2) = 250,000 | 250,000 | YES |
| `placement_exact` | 1.0 (pools ≥ targets) | 1.0 | YES |
| Reportability (null draws) | ~1.0 at these counts | 1.0 (no UNDER_POWERED draws) | YES |
| Null `effect_bps` (reportable) | bps scale, centered near 0 | [−193.2, +165.9] | YES |
| `p_value` | [1/1001, 1] | [0.000999, 1.0] | YES |
| FPR Wilson half-width | ≤ 0.03 | max 0.0225 | YES |
| TPR Wilson half-width | ≤ 0.05 | max 0.0436 | YES |
| TPR vs g (α₀) | non-decreasing (±MC noise) | no violations > 0.05 | YES |

### Statistical Sanity

| Statistic | Value | Makes sense? | Notes |
|-----------|-------|--------------|-------|
| Mean FPR at α = 0.10 | 0.036 | YES | Compound rule (CI_low > 0 ∧ p ≤ α) is conservative when the CI leg binds. |
| Mean FPR at α = 0.01 | 0.0225 | YES, with caveat | Exceeds nominal at the strict secondary α — consistent with independent sign flips being anti-conservative under within-regime dependence (see Info 2). α₀ = 0.05 is the binding operating point and is the one classified. |
| BTCUSD-4h TPR at g = 128 | 0.64 | YES | High-volatility instrument, 68 events — `no_finite_mde_on_grid` is the honest verdict, exactly the expected thin-cell outcome. |
| 11 of 13 NOT_COVERED via point estimates in (0.05, 0.07] | — | YES | Per the Revision-1 rule, point excess at adequate precision is NOT_COVERED even when not `material`; only USDCAD-2h (0.070, Wilson low > α₀) is material. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Wilson precision at 500 draws | half-widths ≤ 0.03 / 0.05 | YES | Max observed 0.0225 / 0.0436; completion 100%. |
| CI-shift under planted edge | uniform +g shifts mean and percentile CI exactly | YES | Verified algebraically against `bootstrap_cell_distribution` (num/den structure). |
| N2 block permutation | TRAIN-estimated block length; circular MBB | YES | `estimate_block_length` on per-bar TRAIN returns; per-cell `block_length` recorded for the predeclared diagnosis path. |
| Control-matching equivalence | vectorized = EXP-021 reference ordering | YES | `verify_control_matching()` runs before any draw and raises on mismatch. |
| Regime-cluster bootstrap / sign permutation | frozen EXP-027 structure, single-cell | YES | Same resampling within direction strata; aggregation and Holm steps removed exactly as predeclared. |

## Results Plausibility

The FPR map is tightly clustered around 0.02–0.06 with no domain-wide
pathology; MDEs fall from 8–16 bps at ~200–270 events (1h majors) to 32–128
bps at 32–86 events (4h), the expected power-vs-count shape; the only
non-finite MDE is BTCUSD-4h. The NOT_COVERED set is dominated by marginal FPR
point excesses (0.052–0.062), with one material case (USDCAD-2h N1 = 0.070).
This pattern matches the scope's honest prior and the plan's caveat 3
(small-cluster bootstrap degradation concentrating in thinner cells).

## Scope Compliance

- Analysis plan followed: YES (including the predeclared deviations: no tier
  mapping — realized-count placement; truncation rule unused with structural
  justification; both were declared pre-execution).
- Deviations: none beyond the predeclared items above.
- Complexity budget: 4 / 4 tests, 5 / 5 plots, 1 / 1 new module.
- Holdout exclusion verified: YES (F01 TRAIN slice; TEST and final-30% never
  scanned; no chart-type views; no real event outcomes computed).

## Issues

### Critical

None.

### Warning

1. **`tpr_usable` filter admits imprecise TPR points when `tpr >= TPR_TARGET`**
   - File: `python/experiments/EXP-044/code/run_experiment.py`, lines 420–421
   - Description: a TPR point failing the half-width ≤ 0.05 precision gate
     still counts toward the MDE if its point estimate is ≥ 0.80, so in
     principle an MDE could rest on an imprecise point.
   - Impact: **none in this run** — completion is 100% and the maximum
     realized TPR half-width is 0.0436, so the branch never fired. Latent
     only.
   - Fix: in any rerun, classify cells whose MDE-defining point fails
     precision as CALIBRATION_UNDERPOWERED instead.

### Info

1. **MDE values are recorded for NOT_COVERED cells** (e.g. AUDUSD-1h, 16 bps).
   This is intentional power context per the plan; interpreters must not read
   a recorded MDE as admission to Track B — the verdict column governs.
2. **FPR at the secondary α = 0.01 exceeds nominal broadly** (mean 0.0225).
   Consistent with the independent-sign-flip permutation being
   anti-conservative under within-regime dependence; the primary α₀ = 0.05
   operating point — the one G3 consumes — is the classified object. The
   analyst should note this when reporting the secondary-α columns.
3. **The 13-cell NOT_COVERED set is mostly marginal** (point estimates
   0.052–0.062 with Wilson lower bounds below α₀); only USDCAD-2h is flagged
   `material`. This grading is exactly the predeclared Revision-1 rule;
   reporting should preserve the marginal/material distinction.
4. **Two-null disagreement at 2 instruments (AUDUSD, USDCAD)** is below the
   ≥3-instrument METHOD_NOT_TRANSFERABLE trigger; in both cases N1 > N2,
   the direction the plan's caveat 4 predicts for a block-length artifact
   would be N2 > N1 — so this looks like genuine borderline N1 FPR excess,
   correctly absorbed by the per-cell verdicts.

## Re-Audit Requirements

None — PASS. The warning is latent (branch never exercised in this run) and
requires no re-run.
