# Audit Report: Experiment EXP-065

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Formulas match scope. MA segmentation via SMA diff → zero-crossing, correct. HA harami detection (xen.ha_harami). ZZ generation (xen.zigzag). Third-barrier caps (xen.third_barrier: adaptive_time_caps_by_epoch floor re-call + causal next-rd-confirm locator). Bootstrap (moving-block, b=m^(1/3), N_BOOT=10,000). Contrasts (independent contrast_ci for signal-vs-RM, paired_median_contrast_ci for variant-vs-bench). All reuse existing frozen modules. |
| `code/run_experiment.py` | Edge cases | PASS | No-haramis → empty arm. No MA segments → empty context (both objects). No ZZ moves → empty context with all-zero retained_p75. Power floor (m>=30) enforced. RNG purpose isolation prevents stream collision. Division by zero guarded (_firsthit denominator check, _tail_share_worst5 total_neg≥0 guard, _trimmed_mean empty check). NaN treated explicitly (nan_eq for power-limited contrasts, float_match with RECON_TOL). |
| `code/run_experiment.py` | Type safety | PASS | All public functions have type hints. Dataclasses used for structured types (VariantSpec, ArmResult). |
| `code/run_experiment.py` | NaN handling | PASS | SMA returns NaN until window elements. _nan_eq treats NaN==NaN as True (power-limited contrasts). _float_match uses RECON_TOL=1e-9. Arithmetic guarded by np.isfinite checks. Missing EXP-061 anchor handled (empty dict → is_defect). |
| `code/run_experiment.py` | Holdout exclusion | PASS | TRAIN-only loader: scan metadata for row count → compute analysis_cutoff (0.7) → train_cutoff (0.7) → slice(0, train_rows) → collect. Never sorts/collects the full file. find_source_file filters derivative markers. Domain bars fenced to train_end_epoch. Forward exit scans clipped to data edge → DATA_CENSORED. |
| `code/run_experiment.py` | Loader ordering | PASS | `pl.scan_parquet(path).slice(0, train_rows).collect()` — no sort before slice. File-order is chronological (CloseTime strictly increasing per file). Assert chronological after collect. |
| `code/run_experiment.py` | Memory/performance | PASS | Lazy scan for row count, column-projected TRAIN slice. Process-level parallelism with pinned native threads (POLARS_MAX_THREADS=1 etc. set before import). Per-cell forward scans bounded by cap (THIRD-EVENT: 8*bench_N). Per-cell arrays released after summarisation (del cell, del train_1m per instrument). Plots from collected summaries only. |
| `code/run_experiment.py` | Safe optimization | PASS | Multiprocessing uses ProcessPoolExecutor, per-process thread pinning, deterministic merge order (INSTRUMENTS). RNG seeded by (BASE_SEED, cell_index, purpose) — order-independent. Output stated byte-identical across worker counts. |
| `code/run_experiment.py` | Progress tracking | PASS | tqdm on instrument loop (process_instrument grid). No per-row logging in helpers. |
| `code/run_experiment.py` | Logging/output | PASS | LOGGER.info for summary only. ArmResult internal (no printed side-effects). Per-cell results returned, not printed. |
| `code/run_experiment.py` | Organization/import side effects | PASS | Imports → path → constants → types → I/O → pure computation → plotting → orchestration → main(). No mkdir/plot at import time — directories created in run(). |
| `code/run_experiment.py` | Plot data reuse | PASS | All 5 plots render from pre-collected per-cell rows list (make_plots(rows)). No data reloads or chart regeneration. |
| `code/run_experiment.py` | Docstrings | PASS | Module docstring (detailed, covers re-run context, question, method, output). Public functions have docstrings. |

## Numerical Validation

### Spot Checks

**Reconciliation — native BENCH vs EXP-061 M0 (99 cells, all match):**

| Cell | EXP-065 BENCH m | EXP-061 M0 m | BENCH median | M0 median |
|------|-----------------|--------------|-------------|-----------|
| BTCUSD-5m | 10667 | 10667 | 0.055249410758157674 | 0.055249410758157674 |
| EURUSD-5m | 8360 | 8360 | 0.1369439861997691 | 0.1369439861997691 |
| GBPUSD-5m | 8586 | 8586 | 0.22260169962875792 | 0.22260169962875792 |

All 99 pairs match to full printed precision (>> 1e-9 tolerance).

**Reconciliation — hybrid BENCH vs EXP-061 H0 (99 cells, all match):**

| Cell | EXP-065 BENCH m | EXP-061 H0 m | BENCH median | H0 median |
|------|-----------------|--------------|-------------|-----------|
| BTCUSD-5m | 3044 | 3044 | -0.053125795483862495 | -0.053125795483862495 |
| EURUSD-5m | 3089 | 3089 | 0.04645889672710926 | 0.04645889672710926 |
| EURUSD-15m | 1079 | 1079 | 0.028943495362424274 | 0.028943495362424274 |

All 99 pairs match.

**Readiness — all 99 member cells pass construction:**

All `construction_pass: true`, `causality_ok: true`, all 7 per-object invariant checks true (`exit_ok`, `matched_count_ok`, `bench_cap_ok`, `cap_monotone`, `event_bounds`, `warmup_identity`, `fav_dist_positive`).

**Determinism — 17 cells replayed byte-identically (one per instrument):**
0 non-deterministic cells. Gate checks per-object per-variant signal/null returns/median/CIs + contrast median/mean CI_low.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| `m` (qualifying count) | ≥ 0 | [0, 10667] | YES |
| Median | ℝ (ATR units) | [-2.33, 2.19] | YES — plausible ATR-normalised range |
| Mean | ℝ | plausible range | YES |
| Censored fraction | [0, 1] | [0, ~0.15] | YES — natural for TRAIN-edge truncation |
| Direction | {+1, -1} | inferred from move_arrays | YES |
| Exit weights sum | 1.0 ± 1e-9 | all pass invariant | YES |

### Statistical Sanity

| Statistic | Value | Makes sense? | Notes |
|-----------|-------|-------------|-------|
| Native BENCH median-viable cells | 8 (6 instr, all non-4h) | YES — consistent with EXP-061 M0 (8 cells) | Population: 8360-class MA-native |
| Native alt-variant `variant_wins` | 0/4 compose at P11 | YES — consistent with EXP-058 (ZigZag third-barrier also EVIDENCE_AGAINST) | T48: 1 win (EURUSD-4h, single low-n cell). EVENT: 2 wins (GBPUSD-1h, US2000-4h) — neither P11 |
| Hybrid BENCH median-viable cells | 3 (2 instr, all non-4h) | YES — consistent with EXP-061 H0 power profile | Population: 3202-class ZigZag-native |
| Hybrid verdict | INCONCLUSIVE_POWER_LIMITED | YES — 3-4 powered cells per variant, below P11 quorum | Expected for 3202-class on longer-horizon variants |
| Phase verdict | EVIDENCE_AGAINST (native stronger) | YES — native EVIDENCE_AGAINST > hybrid INCONCLUSIVE | No alt variant composes for either object |
| Reconciliation | 99/99 cells both objects match | YES | Full FP precision match to EXP-061 |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Moving-block bootstrap | Within-block exchangeability of regime-clustered events | YES | Block size b=m^(1/3) standard for time-series bootstrap. Per-cell, per-variant, per-object — no cross-contamination. |
| Independent contrast (variant - RM) | Two bootstrap distributions independent | YES | Signal (conditioned haramis) and RM (random in-regime, signal entries excluded) are disjoint samples. No common subset. |
| Paired contrast (variant - benchmark) | Common qualifying subset well-defined | YES | Both arms index the same object's conditioned haramis. Same entry_idx, differing only in per-event n_event window. Common subset naturally shrinks (reported via n_common). |
| Per-cell median binding | Median robust to fat tails | HOLDS | Fat tails visible in mean/trim divergence (P4 diagnostic disclosed). Median is programme endpoint. |

## Results Plausibility

- **Native EVIDENCE_AGAINST** is structurally coherent: the same 8 median-viable cells (EURUSD-15m/30m, GBPUSD-1h, USDCHF-2h, AUDUSD-30m, NZDUSD-1h/2h, GBPJPY-30m) that drive EXP-061's M0 signal also drive the third-barrier variants' median-viable and beats-RM flags. But **none** beats-its-own-benchmark at P11: `beats_bench` maxes at 3 cells (T48: EURUSD-5m/EURUSD-4h/GBPJPY-5m; EVENT: GBPUSD-1h/GBPJPY-2h/US2000-4h) — all below the P11 quorum of 5. A longer holding horizon does not improve the benchmark median on MA for the native object.

- **Hybrid INCONCLUSIVE_POWER_LIMITED** is structurally correct: only 3–4 powered cells per variant (< P11 quorum). The hybrid object (3202-class) has always been power-constrained — EXP-061 H0 had only 1 generalising cell. The third-barrier axis pairs each entry with a longer holding window, which further depletes the qualifying count (censoring, TIMECAP exits). Result: not enough events to reach the 30-event power floor across enough cells.

- **The censoring cost is bounded**: mean censored fraction across variants stays < ~0.15. The cost-side disclosure is delivered (secondary_map.csv, censoring timecap composition plot).

- **Phase verdict = EVIDENCE_AGAINST (native stronger)**: same pattern as EXP-058 (ZigZag third-barrier) which was also EVIDENCE_AGAINST. The third barrier is not the lever — on either substrate, for either object.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 4 methods / 4 budget, 5 plots / 5 budget, 0 new modules / ≤1 budget
- Holdout exclusion verified: YES (TRAIN-only, first 49% file-order, never sort/collect full file)
- Instruments: 17/17 (3 COVERAGE_EXCLUDED cells: US500-4h, JP225-2h, JP225-4h) — matches scope
- Domains: 6 (5m,15m,30m,1h,2h,4h) — matches scope
- Objects: 2 (nat, hyb), reported individually, never pooled — matches Amendment 001
- Variants: 5 (BENCH, THIRD-TIME-T12/T24/T48, THIRD-EVENT) — matches scope
- Deferred secondaries: documented in run_metadata.json (/STRONG-HA + full ZZ third-barrier surface not computed) — matches Exclusions
- No G-015 adjudication — matches scope

## Issues

### Critical

None.

### Warning

None.

### Info

1. **DE30 truncated history disclosure.**
   - File: `code/run_experiment.py:165`, also in `run_metadata.json`
   - Description: DE30's broker history ends 2026-01-16; its counts derive from its own timeline and are not span-comparable. This is acknowledged in both the code and metadata. Cells run and report normally; the disclosure notes the shorter span for interpretive context.
   - No action needed — correctly noted.

2. **Reconciliation precision.** The printed medians in reconciliation.csv match EXP-061 to full floating-point precision (~17 decimal digits), far exceeding the RECON_TOL=1e-9. This is expected given RNG-purpose reuse (native BENCH uses EXP-061's M0 purposes, hybrid BENCH uses EXP-061's H0 purposes) — the exact same RNG path produces exact same draws. The actual comparison in code correctly uses tolerance-based comparison (_float_match with RECON_TOL); the extra precision in output is a display artifact, not a concern.

## Re-Audit Requirements

None — this is a PASS with no conditional items.
