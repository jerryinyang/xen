# Audit Report: Experiment EXP-001

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 4

EXP-001 validates the Phase 001 synthetic substrate (known-null generators,
known-positive injection) and the P0 aggregation precondition for the 5m/240m
domains. The implementation matches the analysis plan, excludes the global
holdout, preserves real-price and temporal discipline, and its numerical
outputs reproduce the closed-form expectations. The recorded
`overall_status = PASS` with 5 per-cell under-powered INCONCLUSIVE cells (all on
the 4h domain) is faithful to the rev. 2 scope criteria and checkpoint design
§11/D-prec.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Draw generation, summarisation, and status logic match plan and scope. |
| `src/xen/referee_calibration.py` | Correctness | PASS | Injection/recovery, null, cost, and P0 helpers verified algebraically and by spot-check. |
| both | Edge cases | PASS | Empty-frame, `min_effective_n`, zero-denominator, and non-finite guards present. |
| both | Type safety | PASS | Public functions carry hints; dataclasses used for structured returns. |
| both | NaN handling | PASS | `finite_values()` filters non-finite before every summary; `drop_nulls` on the lead return. |
| both | Holdout exclusion | PASS | `load_analysis_data` sorts by `CloseTime`, slices `[0, int(total_rows*0.7)]`; holdout never collected. |
| `referee_calibration.py` | Loader ordering | PASS | Lazy `scan_parquet` → column projection → `sort("CloseTime")` → `slice` → `collect`. |
| both | Memory/performance | PASS | Only bounded summary/coverage/p0 row sets converted to pandas for plots. |
| both | Safe optimization | PASS | `int32` block indices and `finite_values` fast path are bit-identical; no membership/ordering change. |
| `run_experiment.py` | Progress tracking | PASS | Outer instrument loop wrapped in `tqdm`; helpers stay quiet. |
| both | Logging/output | PASS | Concise `logging` summary; per-cell results written to CSV. |
| both | Organization/import side effects | PASS | Imports→constants→helpers→plotting→`main()`; dirs created only in `ensure_output_dirs()` called from `main()`. |
| `run_experiment.py` | Plot data reuse | PASS | Plots reuse already-computed summary/coverage/p0 rows; no second data pass. |
| both | Docstrings | PASS | All public functions documented with Parameters/Returns. |

## Numerical Validation

### Spot Checks

Re-derived and reproduced the substrate math with `referee_calibration` on
synthetic returns (no project data / no holdout):

- **Known-positive recovery (closed form).** With `delta = (m + cost)/1e4`,
  `planted = r + s·delta`, oracle position `p = s`, `s ∈ {−1,+1}`:
  `strategy_bps = s·planted·1e4 − cost = s·r·1e4 + m`. Mean over a draw =
  `m + mean(s·r·1e4)`, and `E[s·r] ≈ 0` since `s` is state-independent. Spot-check
  recovered `m ∈ {0,0.5,1,4,32}` to within machine epsilon of `m + noise`
  (`|diff| ≤ 2.2e-16`). This matches `substrate_summary.csv`, e.g. EURUSD/5m
  recovers `0.5→0.5007`, `32→32.0005`.
- **Cost application.** `mean(net) − mean(gross) = −1.0` exactly for `cost=1.0`;
  every active bar (`|p|>0`, always true here) is charged once. Correct.
- **Nulls.** Gross oracle mean on bar-permutation and random-signal nulls is
  ≈ 0 (0.006, −0.020 bps on 50k synthetic samples), consistent with the
  near-zero null means in `substrate_summary.csv` (all `|mean| ≤ 0.1` bps).

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| Known-null `mean_effect_bps` | ≈ 0 (|·| ≤ 1.0 tol) | [−0.087, 0.103] | YES |
| Known-positive recovered vs planted | within `max(0.5, 0.15m)` | all within tolerance | YES |
| `n_draws` (null / positive) | 200 / 100 | 200 / 100 | YES |
| P0 check status | all PASS | 56/56 PASS | YES |
| Coverage `dropped_window_fraction` (4h, 0.90) | small positive | 0.025–0.131 | YES |
| `analysis_rows` vs VAL-001 | identical | BTC 1,088,960 / EUR 872,242 / USTEC 830,541 / XAU 830,671 | YES |

### Statistical Sanity

| Statistic | Value | Sense? | Notes |
|-----------|-------|--------|-------|
| 4h m=1,2 draw CI straddles 0 | ci_lower < 0 | YES | 4h has ~2,700–4,400 returns and large per-bar dispersion (BTC/XAU); sub-material edges are not separable from zero across draws → under-powered, not broken. |
| 5m/1h recovery CIs | tight, exclude 0 for m≥0.5 | YES | High effective sample on short domains. |
| Null CIs bracket 0 | `ci_lower ≤ 0 ≤ ci_upper` | YES | Both null generators behave as designed. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Percentile CI over draw means | draw-level effects need no parametric form | YES | Non-parametric percentile interval over 100/200 fixed-seed draws. |
| State independence of returns | `E[s·r] ≈ 0` | YES | `s` drawn from a fixed PRNG independent of price; spot-check confirms ~0 bias. |
| P0 oracle | strict pandas resample is an independent check of `aggregate_ohlc` | YES | 0 mismatches at {5,240}m for all four instruments; extends VAL-001 to the new periods. |

## Results Plausibility

Outputs sit in expected domains: nulls ~0, positives recover the planted edge,
P0 fully PASS with all four negative controls detected per period, and coverage
retention worsens monotonically from 5m→4h and improves as `min_coverage`
relaxes — all physically sensible. `analysis_rows` reproduce the VAL-001
post-slice counts exactly, strong evidence the holdout boundary is the validated
one.

## Scope Compliance

- Analysis plan followed: YES (P0 extension → known-null → known-positive).
- Deviations: none.
- Complexity budget: 2/2 tests, 3 plot files / 4 visualisations budgeted (the
  null-CI and positive-recovery panels share one figure), 1/1 new module.
- Holdout exclusion verified: YES.

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Under-powered cells are sub-material by construction.** The 5 INCONCLUSIVE
   cells (BTCUSD/USTEC 4h m=1,2; XAUUSD 4h m=1) all sit below the 4h economic
   materiality threshold (3.0 bps). Their non-separability from zero is therefore
   immaterial to the phase's economic reading; downstream interpretation (Stage 6)
   should note this rather than treat it as a capability gap. Recorded in
   `underpowered_cells.csv` and `run_metadata.json` (`underpowered_cells: 5`).

2. **"Significance" leg measures recovery precision, not single-series detectability.**
   The known-positive significance sub-test asks whether the *across-draw* mean
   distribution clears zero — i.e. Monte-Carlo recovery precision under random
   states — not whether one series' edge is statistically detectable. This is
   consistent with the scope's framing (`run_experiment.py:202–222`) but the
   distinction matters when reading EXP-003 power curves; flagged for the
   interpreter.

3. **`dropped_window_fraction` can be slightly negative.** `expected_full_windows
   = max(1, height // period_minutes)` is an integer-division approximation, so
   tolerant coverage that retains a partial trailing window yields a small
   negative fraction (e.g. BTCUSD 5m/0.80 = −0.00039 in `coverage_grid.csv`). It
   is a reporting artifact of the denominator approximation, not a data error.

4. **`min_effective_n` gate uses raw return count, not effective N.** In EXP-001
   the gate (`run_experiment.py:380`) only decides whether a cell has enough bars
   to run the draw protocol; it never gates the percentile-CI statistic. Raw
   counts (thousands) vastly exceed the floors (25–120), so it never triggers.
   Harmless here; noted because the same constant is reused as a true effective-N
   floor inside the gate-stack L1 leg downstream (EXP-002/003).

## Re-Audit Requirements

None. Verdict is PASS; no fixes required.
