# Audit Report: Experiment EXP-056

## Summary

- **Verdict**: PASS (0 Critical, 0 Warning, 0 Info)
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 0

Audited against `experiment-auditor/references/audit-checklists.md`, `governance-constraints.md`, and the shared pipeline config.

---

## Scope Compliance

| Check | Verdict | Notes |
|-------|---------|-------|
| Implementation matches plan | PASS | All 8 binding variants (BENCH, VP-POC, VP-NEAR, VP-FAR, MAG-0.5x5, MAG-1.0x5, MAG-0.5x20, MAG-1.0x20) + 1 disclosed (VP-POC-INPROG) match the analysis-plan specification §Step 3 and the scope's predeclared sweep. Paired variant-benchmark contrast (analysis-plan §Step 7) implemented correctly as a paired block bootstrap (`paired_median_contrast_ci` in `xen/favourable_targets.py`), not the independence-assuming `contrast_ci`. |
| Instruments / cells | PASS | 99-cell grid (17 instruments × 6 domains − 3 COVERAGE_EXCLUDED US500-4h, JP225-2h, JP225-4h) — matches scope. DE30 truncated-coverage disclosure carried. |
| Commitment slot / TEST-read accounting | PASS | 0 candidate slots, 0 TEST reads. `analysis-plan.md` §Slot & ledger accounting honoured — TEST stratum never read. |
| Complexity budget | PASS | 4 statistical methods (variant median CI, baseline median CI, paired variant-benchmark contrast CI, independent variant-baseline contrast CI) / 5 plots (forest, contrast heatmap, return distribution, win composition, exclusion fractions) / 1 new module (`xen/favourable_targets.py`). All within budget. |
| No extra analyses | PASS | No undocumented analyses found. Disclosed secondaries (`/STRONG-HA`, STAT-MAD, VP-POC-INPROG, matched-random and MA-seg baselines) match the analysis-plan's scope. |

---

## Data Handling

| Check | Verdict | Evidence |
|-------|---------|----------|
| Holdout exclusion | PASS | `load_train_1m()` reads total row count via lazy `scan_parquet().select(pl.len())`, then `slice(0, train_rows)` — never materializes the full file. `train_rows = int(int(total_rows * 0.7) * 0.7)`. Full file never sorted or collected. Domain aggregation fenced to `CloseTime ≤ train_end_epoch`. Forward scans clipped to the data edge. |
| Chronological ordering | PASS | `load_train_1m()` asserts `train.get_column("CloseTime").is_sorted()`. Domain bars aggregated from chronologically-ordered 1m source. All temporal alignment by `CloseTime` (searchsorted + equality assert), never bar index. |
| Real-price outcome discipline | PASS | HA prices enter only `detect_ha_harami` and `annotate_ha_impulse`. `C`, `M_sofar`, volume profile (real `Low/High` + `TickVolume`), trailing magnitudes, `ATR_entry`, fav/adv levels, P15 path-ordered fills, returns, `r`, win rate — all on real domain-bar OHLC. |
| Cross-view alignment | PASS | HA↔real and harami/VP-reference↔bar grid aligned by exact `CloseTime` epoch match (`_map_to_grid` — raises on any mismatch). |
| NaN handling | PASS | `fav_dist ≤ 0` / insufficient-profile / warmup events are **excluded-with-record** (disclosed per-variant counts), never silently dropped or clamped. `Data_CENSORED` events disclosed. Power floor (≥30 events) enforced before reporting median/CI. |

---

## Code Review

| File | Check | Verdict | Details |
|------|-------|---------|---------|
| `code/run_experiment.py` | Correctness | PASS | Variant targets built via `build_variant_targets` dispatches to `_bench_targets` (reuses `xen.expectancy.benchmark_barriers`), `_vp_targets` (VP levels from `xen.favourable_targets.volume_profile_levels`), and `_mag_targets` (trailing magnitude from `xen.favourable_targets.trailing_magnitude_distance`). Paired contrast `paired_contrasts_vs_bench` applies one set of bootstrap block indices to both variant and BENCH `r_e` on the common `qual` subset. Composition logic: `win = viable AND beats_bench`, P11 ≥5 cells ≥3 instruments, mechanical EVIDENCE_* per the Interpretation Guide. |
| `code/run_experiment.py` | Edge cases | PASS | Empty harami array → short-circuits with `empty: True`, all variants NOT_VIABLE_BY_POWER. `mv["confirm_epoch"].shape[0] == 0` → returns empty cell. Fewer than POWER_FLOOR qualifying events → NOT_VIABLE_BY_POWER. VP reference spans with `< VP_MIN_REF_BARS` → insufficient-profile exclusion. `/MAGTARGET` warmup (`< W` prior moves) → warmup-excluded. BENCH warmup (`<5` cap durations, NO_DECISION) inherits from `adaptive_time_caps_by_epoch`. COVERAGE_EXCLUDED cells populated with `excluded_records`. |
| `code/run_experiment.py` | Type safety | PASS | All public helpers have type hints. ArmResult dataclass typed. NumPy arrays enforce dtype. |
| `code/run_experiment.py` | Holdout exclusion | PASS | (See Data Handling). Lazy scan + file-order prefix. `DATA_CENSORED` guard on first-touch scan reaching TRAIN edge. |
| `code/run_experiment.py` | Memory/performance | PASS | Per-cell bounded memory: `compute_cell` → `del cell`. Per-cell summaries collected; per-event returns pooled only from viable cells (bounded). Bootstrap batched `BOOT_BATCH=2000`. Lazy Polars with column projection. |
| `code/run_experiment.py` | Safe optimization | PASS | Sequential causal kernels (`resolve_path_ordered`, in-progress walk, VP per-event builder, trailing-magnitude loop) kept explicit/bounded — not vectorized. Bootstrap index construction batched. VP binning loops (per-event) bounded by `range/ATR` ratio, guarded by `VP_MAX_BINS`. No change to sample membership, denominators, ordering, or streaming semantics. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` over INSTRUMENTS outer loop. Helper functions return data, don't print. Per-cell logging avoided. |
| `code/run_experiment.py` | Organization | PASS | Section order: imports → constants → VariantSpec dataclass → types → I/O helpers → pure computation → plotting → orchestration → `main()`. Output dirs created in `run()` orchestration, not at import. |
| `code/run_experiment.py` | Plot data reuse | PASS | Per-cell summaries (median, CI, m) collected during main loop; pooled per-event returns appended from viable cells. Plots rendered from collected data, no reload. |
| `code/run_experiment.py` | Determinism | PASS | Single `BASE_SEED`. Per-(cell,arm,variant,purpose) RNG via `default_rng([BASE_SEED, cell_index, purpose])` with distinct streams (PB_STAT/PB_HA/PB_RAND_DRAW/etc.). Determinism replay on first usable cell per instrument — 17/17 PASS. |
| `xen/favourable_targets.py` | Correctness | PASS | `volume_profile_levels`: TickVolume uniformly distributed across `[Low,High]` bins; POC = first (lowest-price) max bin; VA 70% grown with upper-first tie-break; volume conservation invariant asserted. `trailing_magnitude_distance`: searchsorted(`side="left"`)-1 for strictly-before. `paired_median_contrast_ci`: identical block construction (`b = m^(1/3)`) to `xen.expectancy.bootstrap_median_distribution`; paired statistic. `barriers_from_distance`/`barriers_from_fav_level`: 1:1 adverse. |
| `xen/favourable_targets.py` | Edge cases | PASS | n==0 or bin_width≤0 or total_v≤0 → `defined=False`. Single-bar degenerate span (n_bins=1). VP_MAX_BINS guard raises on runaway ratio (value range / ATR). Empty move arrays in `trailing_magnitude_distance` → all `defined=False`. `paired_median_contrast_ci` with m=0 → NaN. |
| `xen/favourable_targets.py` | Real-price discipline | PASS | All functions operate on price/volume arrays; no HA column enters this module. TickVolume proxy disclosed. |

---

## Numerical Validation

### Spot Checks

**BENCH cross-experiment anchor (BTCUSD-5m):** EXP-056 BENCH reports m=3117, median=0.05697336449019767. EXP-053 records (from `population_reconciliation.csv`): m=3117, median=0.05697336449019767. Match to machine precision (diff=0.0). **PASS.**

**BENCH class partition (BTCUSD-5m):** fav=745, adv=728, timecap=1644, total m=3117 = 745+728+1644. Positive returns 1613, negative 1504 — consistent with a near-symmetric distribution around the median. **PASS.**

**WIN cell spot check (MAG-0.5x5, USDCHF-4h):** median=0.858102 ATR units, contrast_bench_low=0.013447 (>0, so beats bench), m=69 ≥ 30. BENCH for this cell: m=69, median 0.500518. The paired contrast CI_low is positive as expected for a median diff of ~0.358. **PASS.**

**WIN cell spot check (MAG-1.0x20, USDCHF-5m):** median=0.084614, contrast_bench_low=0.000165 (barely positive), m=3089. BENCH for USDCHF-5m: median=0.049112. The tiny margin (0.000165 ATR units over 3089 events) is a marginal beat. **PASS — reported as fragile awareness.**

### Range Checks

| Metric | Expected | Actual | Pass? |
|--------|----------|--------|-------|
| Direction (rd) | {-1, +1} | {-1, +1} (from `live_in_progress_state`, unchanged EXP-053) | YES |
| Real Close returns | ℝ (finite) | All finite; dist centred near 0 | YES |
| TickVolume (in VP) | ≥ 0 | ≥ 0 (broker tick count) | YES |
| `pair_contrast_n` | [0, m] | ≤ m per cell | YES |
| CI_low_1s (viable cells) | > 0 | All 42+5 VIABLE/WIN cells have CI_low_1s > 0 | YES |

### Composition Sanity

- **BENCH viable**: 8 cells / 7 instruments — consistent with EXP-053's benchmark performance (conditioned signal has a modest gross edge in a subset of cells; most cells CI_SPANS_0 or negative).
- **Best alternative variant** (MAG-0.5x5 and MAG-0.5x20 each have 2 WIN cells / 2 instruments) — far below P11 (5 cells / 3 instruments). All VP variants have 0 WIN cells.
- **Verdict EVIDENCE_AGAINST** is mechanical: bench_pow=99 cells/17 instr (composition_met=true), alt_pow=99/17 for all variants (composition_met=true), no passer → EVIDENCE_AGAINST per the Interpretation Guide. **Correct.**

---

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Moving-block bootstrap | Blocks preserve local dependence | YES | Block length `b = m^(1/3)`, matches EXP-021/027/053 pattern. |
| Median as location | Robust to fat tails | YES | Per-event distributions are bounded within `[-fav_dist, +fav_dist]` + TIMECAP spread; median is the robust choice (P14). |
| TickVolume as volume proxy | Broker tick count approximates traded volume | DISCLOSED | Disclosed in every `/VPTARGET` output; proxy limitation noted. |
| P15 path-ordered fills | 1m bars not replayed | DISCLOSED | EXP-054 bounded the effect as immaterial (median Δr 0.010). |

---

## Results Plausibility

- **BENCH viable cells (8/99, all within POWER_FLOOR)** — consistent with EXP-053's conditioned-signal gross edge being modest and concentrated in slower-domain/instrument cells.
- **No VP variant beats BENCH** — VP profiles of the prior completed move do not systematically improve on the 50%-of-`M_sofar` benchmark. Plausible given the architecture — the 50% level is an adaptive anchor that already captures the move's central tendency.
- **MAG variants produce 5 sparse WIN cells** — mostly on USDCHF-4h and AUDJPY-30m, never concentrated enough to meet P11. Plausible as a noise-level scattered signal.
- **99/99 cells powered on all 8 variants** — the exclusion counts (validity/profile/warmup) are low enough that event counts remain ≥30. The VP insufficient-profile floor (3 bars) and MAG trailing-warmup (5/20 moves) are not heavily depleting the conditioned population.
- **EVIDENCE_AGAINST** verdict is well-supported: favourable geometry is not a lever that systematically improves conditioned capture on this grid.

---

## Derived-View Determinism

- Determinism re-run on 17 cells (first usable per instrument): byte-identical output across all binding variants and both baselines. **PASS.**
- BENCH reconciliation vs EXP-053: 99/99 cells m+median match to 1e-9 (seed-independent). **PASS.**
- Fixed seed per (cell, variant, purpose); no random process without seed.

---

## Issues

### Critical

None.

### Warning

None.

### Info

None.

---

## Audit Conclusion

**Verdict: PASS.** All scope compliance, data handling, code correctness, numerical, and statistical checks pass. 0 Critical/0 Warning/0 Info issues. Implementation is clean, deterministic, and faithfully reproduces the EXP-053 benchmark. The EVIDENCE_AGAINST verdict is mechanically correct per the predeclared rules. The experiment can proceed to Stage 6 (interpretation).
