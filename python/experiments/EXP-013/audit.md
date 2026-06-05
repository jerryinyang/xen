# Audit Report: Experiment EXP-013

> **Re-audited 2026-06-04 after the amendment [A1](../../../docs/experiments-docs/checkpoints/2026-06-04-003-ratification-and-incremental-unit/amendments/2026-06-04-A1-incremental-unit-corrections.md) re-run (F01 across-draw verdict, F04 contiguous block length).** Verdict unchanged: PASS. The redundancy spot checks and info notes below reflect the re-run outputs.

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

EXP-013 can be trusted for interpretation. The Track B predeclaration token is present, EXP-001 was hard-gated as PASS, all 108 positive known-truth recovery cells pass tolerance, and no redundancy-null cell shows a phantom positive incremental edge under the corrected across-draw verdict (binding control powered in 9/12 cells, 0 phantom positives).

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Predeclaration gate | PASS | `find_predeclaration_token()` searches governance files at lines 113-128; `main()` blocks before measurement if absent at lines 440-450. |
| `code/run_experiment.py` | Dependency gate | PASS | `require_exp001_pass()` requires EXP-001 `overall_status == PASS` at lines 131-138. |
| `python/src/xen/referee_calibration.py` | Holdout exclusion | PASS | `load_analysis_data()` sorts by `CloseTime` and collects only the first 70 percent analysis slice at lines 120-133. |
| `python/src/xen/incremental_referee.py` | Incremental estimator | PASS | `marginal_net_series()` computes combined-with-C minus R-alone on real returns and charges incremental cost only on denominator rows at lines 130-175. |
| `python/src/xen/incremental_referee.py` | Known-truth substrate | PASS | `build_rc_substrate()` plants drift only on `C_change` denominator rows and leaves planted-edge `0` as the redundancy null at lines 233-301. |
| `code/run_experiment.py` | Verdict logic | PASS | `main()` treats positive recovery FAIL or redundancy `PHANTOM_EDGE` as substrate failure; the redundancy verdict is drawn from the across-draw distribution with an explicit `UNDER_POWERED` class (F01) and requires `powered_null_cells >= 1`; cost-dominated and under-powered nulls are reported but not counted as phantom edge. |
| `python/src/xen/incremental_referee.py` | Block-length estimation | PASS | `_contiguous_block_length()` estimates the stationary block on the contiguous `net_full` series (F04), not the gap-extracted denominator, so within-episode autocorrelation is captured; the redundancy-null marginal series is per-row, so block length resolves to 1 as expected. |
| `code/run_experiment.py` | Progress/output | PASS | Instrument loop uses `tqdm`; outputs and plots are written from `main()` only at lines 505-530. |

## Numerical Validation

### Spot Checks

- `positive_recovery.csv`: 108/108 rows PASS. Maximum absolute recovery error is `0.396082` bps, below its `0.6` bps tolerance in BTCUSD/4h at planted `4.0` bps.
- `redundancy_null.csv`: 8 `PASS`, 3 `UNDER_POWERED` (BTCUSD/1h, BTCUSD/4h, USTEC/4h), and 1 `NULL_COST_DOMINATED` (XAUUSD/4h); 0 `PHANTOM_EDGE`. `run_metadata.json` reports `powered_null_cells = 9` and `phantom_edge = false`.
- Most positive across-draw mean across all 12 redundancy cells is `-0.041182` bps (EURUSD/5m); no cell has a positive point estimate, so none excludes zero positively. The 3 `UNDER_POWERED` cells have `across_draw_half_width_bps >= materiality_bps` (e.g. BTCUSD/4h half-width `7.02` vs materiality `3.0`), so they cannot bound a phantom and are disclosed rather than passed.
- `substrate_integrity.csv`: C-change denominator fraction stays near the predeclared 25 percent mask share in every instrument/domain cell (`0.249834` to `0.250452`).
- `analysis_metadata.csv` records first-70-percent analysis ends in 2025 while source files continue into 2026, consistent with holdout exclusion.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|----------------|--------------|-------|
| Positive recovery status | all PASS | 108 PASS | YES |
| Redundancy phantom edge | 0 cells | 0 cells | YES |
| Denominator fraction | about 0.25 | `0.249834` to `0.250452` | YES |
| Per-bar incremental cost | positive finite | `0.041667` to `2.5` bps | YES |

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none found; the pre-execution-confirmed cost-drag interpretation is recorded in governance
- Complexity budget: 3 checks / 3 budgeted, 4 plots / 4 budgeted, 1 module / 1 budgeted
- Holdout exclusion verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Under-powered controls are disclosed, not silently passed (F01)**
   - Description: Under the across-draw verdict, BTCUSD/1h, BTCUSD/4h, and USTEC/4h are `UNDER_POWERED` — their across-draw CI half-width meets or exceeds the cell materiality buffer, so a phantom edge could not be detected even if present. None reads positive. They are honestly flagged rather than counted as binding redundancy tests. XAUUSD/4h is the single adequately-powered `NULL_COST_DOMINATED` cell (point at the predeclared cost drag). EURUSD/4h, previously mislabeled cost-dominated on a single draw, now reads a clean across-draw `PASS`.

2. **Bootstrap block length is 1 in redundancy checks (expected under F04)**
   - Description: With the F04 fix, block length is estimated on the contiguous `net_full` marginal series. The redundancy-null construction is per-row (no within-episode persistence in the marginal series), so the estimate resolves to `block_length = 1`. This is correct for this construction; the same estimator yields episode-scale blocks for coherent candidates (e.g. EXP-014's `all_pass` fixture, effective-n 277).

## Re-Audit Requirements

None.
