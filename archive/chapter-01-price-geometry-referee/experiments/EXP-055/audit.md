# Audit Report: Experiment EXP-055 — Long-Horizon Availability (Conditioned HA Harami; AVWAP-Analog Lifetime MFE/MAE)

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Event population identical to EXP-053 (verified by reconciliation). Lifetime window `[entry+1, c2]` with `c2 = confirm_idx[pos+1]` implements the operator decision correctly. ATR-normalised MFE/MAE match the scope formula. |
| `code/run_experiment.py` | Edge cases | PASS | Empty harami/move populations handled (empty cells produce `_empty_metric_fields`). DATA_CENSORED events excluded from medians, disclosed as counts. COVERAGE_EXCLUDED cells recorded. |
| `code/run_experiment.py` | Type safety | PASS | NumPy typed arrays throughout; `AvailResult` dataclass with Optional fields for None-safe CIs. |
| `code/run_experiment.py` | NaN handling | PASS | Bootstrap returns NaN for empty inputs; `move_available` gates on `np.isfinite` checks; `_eq` helper handles NaN/None-aware scalar comparison for determinism replay. |
| `code/run_experiment.py` | Holdout exclusion | PASS | F01 file-order prefix only: `train_rows = int(int(total_rows*0.7)*0.7)`, `scan.slice(0, train_rows)`. Full file never sorted or collected. Domain bars fenced to `CloseTime <= train_end_ts`. |
| `code/run_experiment.py` | Loader ordering | PASS | `scan.slice(0, train_rows)` on pre-sorted file-order rows; `CloseTime` monotonic verified per instrument. |
| `code/run_experiment.py` | Memory/performance | PASS | Lazy Parquet scan with column projection; per-cell bounded memory (domain frame released via `del train_1m` after processing all domains); bootstrap batched at 2,000 resamples. |
| `code/run_experiment.py` | Safe optimization | PASS | Python row loop over excursions (`lifetime_excursions_atr`) is bounded (a few hundred events per cell) and causally clear — kept explicit per scope direction. Bootstrap vectorised in batches. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` over 17 instruments in outer loop; inner domain loop untracked (bounded at 6 per instrument, fast). |
| `code/run_experiment.py` | Logging/output | PASS | Concise stdout summary only (verdict, counts, defect status); all per-cell data to Parquet/CSV. |
| `code/run_experiment.py` | Organization/import side effects | PASS | `RESULTS_DIR`/`PLOTS_DIR` created inside `run()`, not at module import. Imports → constants → types → I/O → computation → plotting → orchestration → `main()` structure. |
| `code/run_experiment.py` | Plot data reuse | PASS | Plots use only the per-cell summary records + pooled per-event arrays collected during the single analysis pass; no reloads or re-generation. |
| `code/run_experiment.py` | Docstrings | PASS | Module-level docstring describes the full pipeline. All public functions have Parameters/Returns docstrings. |
| `code/availability.py` | Correctness | PASS | `end_of_mb_window` correctly implements `searchsorted(entry, "right")` for M_a end and `pos+1` for M_b end. `lifetime_excursions_atr` matches scope formula. `median_block_bootstrap` matches the EXP-049/053 resampling scheme with `np.median`. `move_available` implements all three legs. `composition_fork` implements the P11/POWER ladder. |
| `code/availability.py` | Edge cases | PASS | Empty confirm_idx → all censored. Empty entry_idx → empty arrays. Zero-powered cells → NaN bootstrap CIs → not MOVE_AVAILABLE. |
| `code/availability.py` | NaN handling | PASS | `median_block_bootstrap` returns NaN for empty input; `move_available` explicitly checks `isfinite` and `not None` on all three legs. |
| `code/availability.py` | Type safety | PASS | Full NumPy typing, return type annotations on all functions. |

## Numerical Validation

### Spot Check: BTCUSD-5m

- **Harami count**: 37,050
- **/STRONG-STAT retained**: 3,117
- **DATA_CENSORED**: 0 → qualifying m = 3,117
- **Median MFE**: 1.209 ATR units
- **Median MAE**: 0.806 ATR units
- **MFE CI_low_1s**: 1.153 ATR units

**MOVE_AVAILABLE legs:**
1. m = 3,117 ≥ 30 ✓
2. MFE CI_low (1.153) > 1.0 ✓
3. Median MFE (1.209) > Median MAE (0.806) ✓

→ MOVE_AVAILABLE = True. Consistent with scope formula.

### Spot Check: EURUSD-4h (NOT_AVAILABLE)

- **Qualifying m**: 69 ≥ 30 ✓
- **MFE CI_low_1s**: 0.893 ≤ 1.0 ✗ (fails leg 2)
- **Median MFE** (1.536) > Median MAE (1.344) ✓

→ NOT_AVAILABLE. Correct — CI_low does not clear the upper reference line.

### Composition Verification

P11 formula: MOVE_AVAILABLE ≥ 5 cells AND ≥ 3 instruments.
- MOVE_AVAILABLE: 74 cells, 17 instruments → composition_met = true ✓
- Powered: 99 cells, 17 instruments → quorum_formable = true ✓
- Verdict: AVAILABILITY_GOOD ✓

### Correctness Gates

| Gate | Result | Details |
|------|--------|---------|
| Determinism | PASS | 0 non-deterministic cells (every cell replayed and compared frame-identically) |
| Causality/window invariants | PASS | 0 causality failures (MFE/MAE ≥ 0, `entry+1 ≤ c2 ≤ train_last_idx`, `c2 = confirm_idx[pos+1]`) |
| EXP-053 population reconciliation | PASS | All 96 member cells match EXP-053 counts exactly (0 mismatches). Per-event digest recorded for provenance. |

### Statistical Sanity

| Statistic | Value | Makes sense? | Notes |
|-----------|-------|-------------|-------|
| Pooled MFE events | 89,378 | YES | All powered cells contribute qualifying events; magnitude consistent with 99 cells × median ~hundreds of events |
| MOVE_AVAILABLE fraction | 74/99 = 74.7% | YES | MFE systematically exceeds MAE and clears 1.0 ATR in most cells |
| NOT_AVAILABLE cells | 25 | YES | Concentrated in longer domains (1h/2h/4h) and index pairs — wider CIs from fewer events |
| Censored fraction | 0–2% | YES | Most events have ≥2 confirmations in TRAIN; consistent with scope expectation |
| Contrast_random_low | All negative | YES | Matched-control entries share the same reversal move — ambient regime property, not signal-specific |
| Contrast_ma_low | All negative | YES | MA(20,50) segments longer trends → larger M_b moves signal can't beat |

## Scope Compliance

- **Analysis plan followed**: YES
- **Deviations**: None detected.
- **Complexity budget**: 4 tests / 4 budgeted; 4 plots / 4 budgeted; 1 module (`availability.py`) / 1 budgeted
- **Holdout exclusion verified**: YES — F01 prefix loading; never sort/collect full file; TEST/holdout never read
- **Event population exactly EXP-053**: Verified by per-cell reconciliation (96/96 member cells match)

## Results Plausibility

All outputs are within expected ranges:
- MFE/MAE: typical range 0.6–2.0 ATR units, consistent with reversal move magnitudes
- Median MFE systematically > Median MAE in ~75% of cells — favourable excursion dominates adverse
- Higher-domain cells (2h, 4h) show larger CIs (fewer events) and higher NOT_AVAILABLE fraction — expected statistical pattern
- Index instruments (US500, US2000) show more NOT_AVAILABLE cells — consistent with EXP-053/054 patterns
- DE30 truncated history disclosed; DE30 results consistent (short-history, rates comparable)

No signs of data corruption, extreme outliers, or inverted patterns.

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Beats-both-mfe is empty** — The `beats_both_mfe` composition block shows 0 cells. This is expected: the matched-random control also measures lifetime MFE over the same reversal move, so the signal cannot beat its own ambient regime. The MA-segmented baseline shows even larger MFE because MA(20,50) selects longer, more persistent trends. Both are disclosed secondaries per scope — not a bug.

2. **Contrast bounds are negative** — All per-cell `contrast_random_low` and `contrast_ma_low` values are negative. This reflects the structural expectation: the conditioned harami's lifetime MFE does not exceed either baseline because both baselines share the same reversal move window. Scope pre-registered these as disclosed secondaries and never as binding MOVE_AVAILABLE legs.

## Re-Audit Requirements

None. Full PASS.
