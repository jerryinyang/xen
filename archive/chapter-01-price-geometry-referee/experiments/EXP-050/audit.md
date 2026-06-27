# Audit Report: EXP-050

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 1

All invariants clean, all cells deterministic, all numerical checks pass. Results are internally consistent and match the generated plots and CSVs. No issues affecting trust.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | F01 loader, vectorized interval-join, MBB, FT/FT_rand formulas verified against plan |
| `code/run_experiment.py` | Edge cases | PASS | Zero-bar, empty-moves, zero-span, after-last, before-first all handled |
| `code/run_experiment.py` | Type safety | PASS | Public functions typed; mixed None/float guarded |
| `code/run_experiment.py` | NaN handling | PASS | NaN guards on FT/delta for n_assigned=0; direction_matched_rate NaN guarded at caller |
| `code/run_experiment.py` | Holdout exclusion | PASS | F01 prefix loader: only first train_rows collected; every HA0Time/ConfirmTime fenced |
| `code/run_experiment.py` | Real-price discipline | PASS | Signal price = `RealClose`; no HA price enters any metric |
| `code/run_experiment.py` | Memory/performance | PASS | Lazy scans, per-cell bounded memory, tqdm outer loop |
| `code/run_experiment.py` | Determinism | PASS | Two-pass replay frame-identical on all 99 cells |
| `code/run_experiment.py` | Organization | PASS | Imports/path/constants/IO/computation/plotting/orchestration clearly separated |
| `code/run_experiment.py` | Plot data reuse | PASS | Plots from collected per-cell scalars + 20-bin histograms; no data reload |
| `src/xen/move_position.py` | Correctness | PASS | Forward as-of join, left_strict guard, 4 exclusion classes |
| `src/xen/move_position.py` | Edge cases | PASS | Empty events/moves, zero-span degenerate, missing columns |

## Numerical Validation

### Spot Checks

| Cell | Check | Computed | CSV Value | Match |
|------|-------|----------|-----------|-------|
| BTCUSD-5m | FT_rand = w_up·q_up + w_down·q_down | 0.396904 | 0.396904 | ✓ |
| EURUSD-5m | FT_rand | 0.413444 | 0.413444 | ✓ |
| BTCUSD-5m | delta = FT − FT_rand | −0.150386 | −0.150386 | ✓ |
| BTCUSD-5m | Partition n_total = sum(exclusions) | 37050 = 2+0+0+0+37048 | 37050 | ✓ |
| BTCUSD-15m | Partition n_total = sum(exclusions) | 12620 = 1+2+0+0+12617 | 12620 | ✓ |

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| FT (99 cells) | [0, 1] | [0.2099, 0.3120] | ✓ |
| FT_rand (99 cells) | [0, 1] | [0.3338, 0.4317] | ✓ |
| delta (99 cells) | [−1, 1] | [−0.1760, −0.1164] | ✓ |
| block_len (99 cells) | ≥ 1 | [7, 33] | ✓ |
| n_assigned (99 cells) | ≥ 30 | [393, 37048] | ✓ |
| n_assigned_up + n_assigned_down | == n_assigned | all 99 match | ✓ |
| w_up + w_down | 1.0 | 1.0 to machine precision | ✓ |

### Invariant Checks

| Invariant | Pass? | Detail |
|-----------|-------|--------|
| inv_detector | PASS | 0 in all 99 cells (ReducedOK == original predicate) |
| inv_assignment | PASS | 0 in all 99 cells (no unmatched, no bad pos, clean partition) |
| inv_fence | PASS | 0 in all 99 cells (no timestamp beyond train_end_ts) |
| determinism_ok | PASS | True in all 99 cells (two-pass replay identical) |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| MBB CI on Δ | Within-cell stationarity over block scale | ✓ | MBB robust to moderate non-stationarity; cube-root block cap keeps blocks local |
| MBB CI on Δ | FT_rand ≈ fixed (population rate) | ✓ | FT_rand computed over thousands of in-move bars vs n_assigned=393-37048; population variance negligible |
| Exact FT_rand | In-move bars are direction-matched population | ✓ | All harami bars included in population (conservative); per-direction rates defined |

## Results Plausibility

Results are highly plausible and internally consistent:

1. **All 99 deltas negative** — FT_rand (random in-move timing) is 0.33-0.43 across cells, while FT (harami actual) is 0.21-0.31. Haramis systematically avoid the final third. This pattern is uniform across all 17 instruments and 6 domains.

2. **MA secondary confirms** — delta_ma_vs_rand ≈ 0 to −0.04. Haramis are essentially uniformly distributed within MA regimes. The front-loading is a ZigZag-segmentation-specific phenomenon (ZigZag moves capture directional runs; haramis tend to fire early in those runs).

3. **Duration measure consistent** — delta_dur also negative (−0.10 to −0.16), confirming the front-loading is not an artifact of the price-excursion metric.

4. **No cell is close to materiality** — the closest delta to 0 is −0.116 (US2000-2h). Even at the relaxed +5pp threshold or ±0 threshold, 0/99 cells qualify.

5. **Exclusion rates negligible** — warmup max 1.5%, forming-tail max 0.5%, degenerate 0%. Assignment is well-formed.

## Scope Compliance

- **Analysis plan followed**: YES
- **Deviations**: None. Code implements plan exactly (exact FT_rand, MBB CI on Δ, MA secondary, invariant battery, P9/P11 mechanical readout).
- **Complexity budget**: 1/1 stat tests, 4/4 plots, 1/1 new module (move_position.py).
- **Holdout exclusion verified**: YES — F01 prefix loader confirmed (train_rows ≈ 49% of total), all timestamps fenced.
- **Real-price discipline**: YES — `RealClose` is signal price. No HA price enters any metric.
- **Descriptive-allowance carve-out honored**: YES — no P&L, signal, or capture computation exists anywhere in the code.

## Issues

### Info

1. **inv_unmatched / inv_bad_pos / inv_partition sub-fields present in output** — the `per_cell_context.parquet` separately reports these sub-components of `inv_assignment` (in addition to the aggregated field), which improves diagnostic resolution beyond the code's explicit return dict. All are 0. No action needed.

## Re-Audit Requirements

None.
