# Audit Report: Experiment EXP-053

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 1

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | All formulas, joins, alignments, and indices verified. Live in-progress state uses causal as-of (`searchsorted side="right"-1`). P15 path resolver is explicit bounded loop. |
| `code/run_experiment.py` | Edge cases | PASS | Empty harami/move cells handled via early-return and `_empty_metric_fields`. Zero-magnitude, NaN ATR, warmup, DATA_CENSORED all explicitly excluded. POWER_FLOOR=30 guard prevents undefined ratios. |
| `code/run_experiment.py` | Type safety | PASS | All public functions typed; numpy/polars conversions explicit. |
| `code/run_experiment.py` | NaN handling | PASS | `np.isfinite` checks on ATR, exit_price; `qualifying_mask` filters non-finite entries. `np.errstate(invalid="ignore")` on division. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `pl.scan_parquet` → `select(cols)` → `slice(0, train_rows)` → `collect()` — full file never sorted/collected. `train_rows = int(int(total_rows * 0.7) * 0.7)` → first 49%. |
| `code/run_experiment.py` | Loader ordering | PASS | `is_sorted()` asserted on CloseTime after slice. File-order is chronological per VAL-001 integrity rule. |
| `code/run_experiment.py` | Memory/performance | PASS | Lazy Polars with column projection (`select(cols)`). Per-cell memory bounded (`del train_1m`). Plotting uses aggregated summaries + pooled per-event sample (bounded). |
| `code/run_experiment.py` | Safe optimization | PASS | Vectorized operations (searchsorted, bootstrap) are causally equivalent. The P15 path resolver and `/STRONG-STAT` per-entry loop are explicit bounded loops — their causal semantics are the object under test (never vectorized). |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` on outer instrument loop (17 instruments × 6 domains). No noisy per-row output. LOGGER for summary only. |
| `code/run_experiment.py` | Logging/output | PASS | Concise — one line per verdict element. No per-cell prints. |
| `code/run_experiment.py` | Organization/import side effects | PASS | imports → path → constants → types → I/O → computation → plotting → orchestration → main(). `mkdir` only inside `run()`. No import-time side effects. |
| `code/run_experiment.py` | Plot data reuse | PASS | Plots drawn from collected `records` list and pooled per-event arrays accumulated during the analysis pass. No reload/generation for plotting. |
| `code/run_experiment.py` | Docstrings | PASS | Every public function has Parameters/Returns docstrings. |
| `python/src/xen/expectancy.py` | Correctness | PASS | Block bootstrap replicates `capture_barriers.block_bootstrap_ci` block construction identically (same `b = max(1, round(m^(1/3)))`, `ceil(m/b)` blocks, truncated). Only the statistic differs (`np.median` vs proportion). |
| `python/src/xen/expectancy.py` | Causality | PASS | In-progress state: only moves with `ConfirmTime <= t_i`. Time cap: moves confirmed *strictly before* t_i (`side="left"-1`). P15 scan starts at `entry_idx+1`. Causality assert on line 119-120 confirms as-of. |

## Numerical Validation

### Spot Checks (from reconciliation anchor results in composition_readout.json)

| Cell | fav | adv | timecap | m | pos_returns | neg_returns | fav+adv+timecap==m | Consistent |
|------|-----|-----|---------|---|-------------|-------------|-------------------|------------|
| BTCUSD-5m#0 | 745 | 728 | 1644 | 3117 | 1613 | 1504 | 745+728+1644=3117 ✅ | ✅ |
| EURUSD-5m#6 | 791 | 810 | 1601 | 3202 | 1602 | 1583 | 791+810+1601=3202 ✅ | ✅ |
| USTEC-5m#12 | 998 | 994 | 1762 | 3754 | 1828 | 1918 | 998+994+1762=3754 ✅ | ✅ |
| GBPUSD-5m#24 | 843 | 780 | 1628 | 3251 | 1615 | 1620 | 843+780+1628=3251 ✅ | ✅ |
| USDCHF-5m#36 | 789 | 740 | 1560 | 3089 | 1573 | 1492 | 789+740+1560=3089 ✅ | ✅ |

All 17 reconciliations pass. The independent check verifies: `n_pos >= fav` (FAV guarantees positive return), `n_neg >= adv` (ADV guarantees negative return), and `fav+adv+timecap == m` (partition integrity).

### Range Checks

| Metric | Expected Range | Observed | Pass? |
|--------|---------------|----------|-------|
| Direction | {+1, -1} | {-1, +1} | YES |
| stat_median (viable cells) | ℝ (any) | [+0.057, +0.774] | YES — all positive as expected |
| stat_ci_low_1s (viable cells) | > 0.0 | [+0.00097, +0.0949] | YES |
| Win rate | [0, 1] | [0.462, 0.627] | YES — ~0.50 as expected for symmetric 1:1 barriers |
| Timecap fraction | [0, 1] | [0.149, 0.816] | YES — varies by domain as expected |
| r_firsthit | [0, 1] | [0.326, 0.607] | YES |

### Statistical Sanity

| Statistic | Value | Pass? | Notes |
|-----------|-------|-------|-------|
| Viable cells (P11) | 7 cells, 6 instruments | ✅ | ≥5 cells, ≥3 instruments — threshold cleared |
| Beat both baselines (P11) | 6 cells, 5 instruments | ✅ | ≥5 cells, ≥3 instruments — threshold cleared |
| Powered cells | 99/99 | ✅ | All cells have ≥30 qualifying events — conditioning did not deplete power |
| Non-viable (CI_SPANS_0) | 92/99 | ✅ | Expected — most cells have effects indistinguishable from zero individually; P11 composition is the binding test |
| Defect | False | ✅ | Determinism OK (17 replays), reconciliation OK (17/17) |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Regime-clustered moving-block bootstrap | Events within a block share regime context (local time contiguity) | YES | Events ordered by entry time; block length = `max(1, round(m^(1/3)))` ≈ 14–16 per cell; each block spans contiguous time. Non-parametric — no normality/i.i.d. assumed. |
| Median as location estimator | The median is robust to fat-tailed return distributions | YES | FAV/ADV cluster at ±`0.5*M_sofar/ATR`, TIMECAP spreads — justifies median over mean. |
| Matched-random baseline | Eligible non-signal bar pool is a fair regime-matched null | YES | Same instrument, domain, TRAIN window, direction rule, and geometry. Only the "harami + /STRONG-STAT" condition is removed. |
| Contrast CI (independent bootstrap) | Signal and baseline event sets are independent | YES | Different timestamps, different RNG streams per purpose offset. No overlapping entries (signal bars excluded from pool). |
| P15 path-ordered fill model | Bullish bar `O→L→H→C`; bearish `O→H→L→C` | Documented approximation | 1-minute bars are not replayed inside the domain bar. EXP-054 bounds this effect. Disclosed in every result. |

## Results Plausibility

All outputs are within expected ranges. The 7 viable cells cluster in specific instrument–domain pockets (BTCUSD short-term, EURUSD-1h, GBPUSD/USDCHF/EURJPY longer-term), consistent with the conditioned signal having non-uniform efficacy across the grid. The 92 non-viable cells have CI spanning zero — expected for a small-effect signal on symmetric 1:1 barriers. The power floor of 30 qualifying events is met by every cell, so the EVIDENCE_FOR verdict is not power-limited. Matched-random baseline medians are generally near-zero or negative (confirming the signal adds value), and MA-segmentation baselines show larger variance (consistent with segmentation being noisier).

## Scope Compliance

- **Analysis plan followed**: YES — all 8 steps of the plan are faithfully implemented.
- **Deviations**: None.
- **Complexity budget**: 4 statistical tests / 4 budgeted (signal bootstrap, matched-random bootstrap, MA-seg bootstrap, contrast CI); 4 plots / 4 budgeted (forest, composition heatmap, return distributions, retained fraction); 1 new module / 1 budgeted (`xen/expectancy.py`). ✓
- **Holdout exclusion verified**: YES — lazy scan+slice before collect; full file never materialized. `train_rows = int(int(total_rows * 0.7) * 0.7)`. Forward scans clipped to `n_bars - 1`; DATA_CENSORED when truncated by data edge.
- **Real-price discipline**: YES — HA prices only in `detect_ha_harami` and `annotate_ha_impulse`. All metrics on real OHLC.
- **Timestamp alignment**: YES — HA↔real by exact CloseTime epoch match with equality assert; move ConfirmTime/EndTime mapped by searchsorted.

## Issues

### Critical

None.

### Warning

None.

### Info

1. **DE30 truncated history disclosure**
   - File: `code/run_experiment.py`, line 119–121
   - Description: DE30 broker m1 history ends 2026-01-16. Counts derive from its own realized timeline and are not span-comparable with other instruments. This is disclosed in `run_metadata.json` and the pre-execution review, and DE30 is not among the viable cells — so the disclosure is immaterial to the verdict.

## Re-Audit Requirements

None — full PASS.

---

**Auditor conclusion**: Implementation is correct, deterministic, and faithful to the scope and analysis plan. Holdout exclusion is sound. All reconciliation checks pass. The EVIDENCE_FOR verdict is mechanically correct under the pre-defined interpretation criteria. No issues block interpretation.
