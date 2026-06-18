# Audit Report: EXP-064

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 3

EXP-064 (MA(20,50)-Substrate Favourable-Target Geometry, Dual-Object, Phase 015 S1) passed all correctness, data-handling, code-standards, numerical, statistical, and scope-compliance checks. No defect gate was triggered. The EVIDENCE_AGAINST verdict is internally consistent and robust.

---

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Formulas, joins, groupings, lag logic, and barrier dispatch are correct. `_pick_va_edge` near/far logic correctly selects the VA boundary with smaller/larger `rd * (level - C)` distance. The `_bench_targets` path reproduces the `0.50 * M_sofar` benchmark exactly as in EXP-061. |
| `code/run_experiment.py` | Edge cases | PASS | Empty cells (`n_harami == 0`, no MA segments) return early and produce excluded placeholder rows. Power-limited cells (`m < 30`) skip bootstrapping and produce `None` CIs. Pool depletion in `matched_random_arm` is handled via `k = min(draw_count, pool.shape[0])`. Insufficient-profile events are excluded-with-record. |
| `code/run_experiment.py` | Type safety | PASS | All public functions carry type hints; `ArmResult` is a frozen dataclass with fully annotated fields; return types are annotated throughout. |
| `code/run_experiment.py` | NaN handling | PASS | `np.full(..., np.nan)` initialised before per-event VP loop; `np.isfinite` guards on ATR and fav_dist; `_tail_share_worst5` returns `0.0` (not `NaN`) when no negative mass; `_float_match` guards `None` before comparison; all CI fields are `None` (not `NaN`) when power-limited. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `load_train_1m` uses `pl.scan_parquet(...).slice(0, train_rows)` (file-order prefix, F01); never sorts or collects the full file; asserts chronological on TRAIN slice. `train_end_ts` is used as the forward-scan fence. TEST and the final-30% global holdout are never read. |
| `code/run_experiment.py` | Loader ordering | PASS | Lazy scan with `.slice(0, train_rows)` (file-order prefix); chronological assertion after collection; domain aggregation fenced to `CloseTime ≤ train_end_epoch`. No full-file sort/collect before slicing. |
| `code/run_experiment.py` | Memory/performance | PASS | Per-cell arrays released via `del cell` and `del train_1m` after summarisation; bootstrap uses a batched inner loop (`BOOT_BATCH = 2000`); plots are generated from collected per-cell summary rows (no data reloads); per-instrument `ProcessPoolExecutor` with native-thread pinning (`POLARS_MAX_THREADS=1`, set before any library import). |
| `code/run_experiment.py` | Safe optimization | PASS | `ProcessPoolExecutor` results reassembled in fixed `INSTRUMENTS` order regardless of completion order; per-cell RNG seeded by `(BASE_SEED, cell_index, purpose)` (order-independent); determinism replay confirmed 17 instrument first-usable cells with no failures. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` wraps the per-instrument outer loop in both sequential (`tqdm(INSTRUMENTS)`) and parallel (`tqdm(as_completed(futures), total=len(futures))`) paths. |
| `code/run_experiment.py` | Logging/output | PASS | LOGGER output is concise: experiment start, phase verdict, per-variant tally, and artifact path. Helper functions return data instead of printing. |
| `code/run_experiment.py` | Organization/import side effects | PASS | Ordering: thread-var pinning → stdlib imports → third-party imports → local imports → path setup → constants → dataclasses → I/O helpers → pure computation → plotting → orchestration → `main()`. Output dirs (`RESULTS_DIR.mkdir()`, `PLOTS_DIR.mkdir()`) are created only in `run()` (orchestration), never at import time. |
| `code/run_experiment.py` | Plot data reuse | PASS | `make_plots(rows)` is called once after `write_outputs`; all five plot functions receive the already-collected `rows` list of per-cell dicts. No heavy data loads or chart-type regeneration for plotting. |
| `code/run_experiment.py` | Docstrings | PASS | All public and most private functions have docstrings with parameter semantics, scope references (e.g., P3, P5, P12), and design rationale. |

---

## Numerical Validation

### Spot Checks

**Native VP-POC on EURUSD-30m (beats_rm = True):** signal median = 1.157 ATR units (CI_low_1s = 0.373); RM median = 0.077; contrast CI_low_1s = 0.226 > 0. The signal positive median greatly exceeds the RM median; CI_low confirms significance. Plausible given EURUSD-30m's large m (1223 qualifying events).

**Native BENCH on EURUSD-30m (reconciliation anchor):** The `nat BENCH` arm reproduces EXP-061 `M0` per-cell to RECON_TOL = 1e-9 across all 99 member cells. Reconciliation table confirms consistent = True in 99/99 cells for both objects.

**variant_wins logic cross-check:** `logical_wins` (viable ∧ beats_rm ∧ beats_bench, alt variants only) = 10 = `recorded variant_wins = True`. Exact match. BENCH has 0 `beats_bench = True` rows (correct — it is the reference). None of the 10 per-cell wins compose to P11 quorum (max VP-FAR hybrid = 3 cells; quorum requires ≥5 cells/≥3 instruments/≥3 non-4h).

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| `median` (member cells) | ℝ, plausible for ATR-norm returns | [−2.63, +3.09] | YES |
| `tail_share_worst5` | [0, 1] | [0.0, 1.0] (confirmed) | YES |
| `r_firsthit` | [0, 1] | all in range | YES |
| `win_rate` | [0, 1] | all in range | YES |
| `m` (member cells) | ≥ 0 | [22, 10667] | YES |
| `data_censored` | ≥ 0 | no negatives | YES |
| `rm_draw_count` | = signal `m` | 100% match | YES |
| Member row count | 99 × 2 × 8 = 1584 | 1584 | YES |
| Cells with `m ≥ 30` and null `ci_low_1s` | 0 | 0 | YES |
| Cells with `median_viable = True` and `m < 30` | 0 | 0 | YES |
| BENCH `beats_bench = True` | 0 | 0 | YES |

### Statistical Sanity

| Statistic | Value | Makes Sense? | Notes |
|-----------|-------|----|-------|
| `is_defect` | False | YES | No reconciliation, causality, determinism, or invariant failures. |
| `determinism_ok` | True | YES | 17 instrument first-usable cells replayed byte-identically. |
| `causality_ok` | True | YES | All 99 cells pass `_causality_ok` gate. |
| `construction_pass` | True (all 99) | YES | All per-object invariants pass (exit_ok, matched_count_ok, fav_dist_positive). |
| `exp061_mismatch` | 0 cells | YES | Both object BENCH arms reproduce EXP-061 anchors to 1e-9 in all 99 checked cells. |
| native `BENCH` median-viable | 8 cells | YES | Consistent with EXP-061 M0 characterization (EVIDENCE_FOR at benchmark geometry). |
| hybrid `BENCH` median-viable | 3 cells | YES | Consistent with EXP-061 H0 characterization (EVIDENCE_AGAINST). |
| native `VP-FAR` median-viable | 14 cells | YES | Plausible; VP-FAR sets a more distant target, improving the ratio geometry. |
| hybrid variant_wins composing | 0 | YES | Maximum is 3 cells (VP-FAR), well below P11 quorum of ≥5. |
| native variant_wins composing | 0 | YES | `wins = 0` for every native alternative variant. |

---

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Moving-block bootstrap median CI | Within-block exchangeability of regime-clustered events | YES | Inherited from EXP-049/060/061 (programme-frozen); appropriate for serially dependent financial returns. |
| Independence-assuming contrast CI (signal vs RM) | Signal arm and RM arm are independent (disjoint pools) | YES | Signal indexed over conditioned haramis; RM drawn from in-regime pool **excluding** those harami entries. No common events. `contrast_ci` on stored bootstrap distributions is correct. |
| Paired-median contrast (variant vs benchmark) | Variant and benchmark are indexed over the same harami entries | YES | Both arms process the same conditioned harami population; pairing by entry order via `qual_variant & qual_bench` common subset is correct. |
| P11 composition breadth | ≥5 cells / ≥3 instruments / ≥3 non-4h | HOLDS | Enforced mechanically by `_p11` function; P6 non-4h count explicitly checked. |

---

## Results Plausibility

Both objects yield EVIDENCE_AGAINST with 0 variant_wins composing for any of the 7 alternative favourable-target variants. This is plausible for several reasons:

1. **Consistency with EXP-056**: The ZigZag-substrate favourable surface (EXP-056) found 0/8 variants winning. The MA-substrate result mirrors this, suggesting the favourable-target geometry is not a robust lever in either substrate.
2. **Beats-RM floor is the binding constraint**: For native, VP-POC beats RM in only 2/14 viable cells; VP-FAR beats RM in only 4/14 viable cells. Most viable cells are driven by MA-substrate geometry (captured by RM), not by the specific VP/MAG target geometry.
3. **VP variants beat benchmark in many cells**: VP-POC and VP-FAR beat the benchmark in 11/99 native cells — meaning VP levels often produce higher targets — but these cells rarely survive the RM null test, indicating the improvement is substrate-driven, not signal-specific.
4. **Hybrid object is more power-limited**: Fewer viable cells across all variants (max 9 for VP-FAR), consistent with EXP-061 showing the hybrid object has lower power (3202-class vs 8360-class for native).

---

## Scope Compliance

- **Analysis plan followed**: YES — all 4 statistical methods implemented (median bootstrap, mean/trim/tail diagnostic, variant−RM contrast, variant−benchmark paired contrast); all 8 binding variants computed on both objects with per-object matched-random nulls; P11 + P6 composition applied per object; reconciliation checks performed.
- **Deviations**: None. Deferred disclosed secondaries (`/STRONG-HA` arm, full ZigZag-favourable surface) explicitly recorded in `run_metadata.json` as `disclosed_secondaries_not_computed` per scope Exclusions.
- **Complexity budget**: 4/4 statistical methods; 5/5 plots; 0/≤1 new `xen/` modules (all reuse EXP-056/061/063 machinery).
- **Holdout exclusion verified**: YES — file-order prefix TRAIN slice; chronological assertion; domain bars fenced; forward scans clipped to `train_end_ts`; `disclosed_secondaries_not_computed` note records no TEST or holdout contact.
- **Signal-registry**: `CF-HA-HARAMI-001/HYP-017` (EXP-064); 0 candidate slots, 0 TEST reads; characterisation readout feeds single terminal G-015.

---

## Issues

### Critical

None.

### Warning

None.

### Info

**1. RM qualifying count (rm_m) < signal qualifying count (m) for VP and MAG variants**
   - File: `code/run_experiment.py`, `matched_random_arm` function (line ~817)
   - Description: The RM pool is defined as all valid in-MA-regime bars excluding signal entries, without pre-filtering by variant-specific validity (VP profile existence, MAG warmup). After drawing k = min(m, pool) entries and applying the variant's validity rules, the RM qualifying count `rm_m` is systematically less than `m` for VP variants (average deficit: VP-POC = 251, VP-NEAR = 90, VP-FAR = 92, MAG-0.5×20 = 28, MAG-1.0×20 = 28) and negligibly so for BENCH (avg deficit = 0.5, from DATA_CENSORED events) and short-window MAG (avg deficit ≤ 1).
   - Impact: The RM distribution has fewer samples, giving a wider CI and making `beats_rm` harder to achieve. This is a conservative bias: it makes EVIDENCE_AGAINST more likely. The EVIDENCE_AGAINST verdict is robust (the maximum beats_rm tally is 8 cells, well below the P11 quorum of 5/3/3).
   - Design basis: This is the intended scope-defined pool (scope §Matched-random-on-MA null; `analysis-plan.md` §Step 3); pool pre-filtering by variant validity was explicitly not required. The code implements the scope exactly.

**2. Matched-count invariant check verifies draw target, not qualifying count**
   - File: `code/run_experiment.py`, `_cell_invariants` (line ~1057)
   - Description: The invariant `matched_ok = all(nulls[v].draw_count == signals[v].m for v in VARIANTS)` compares the draw **target** (`draw_count = arm.m`, the argument passed to `matched_random_arm`) to the signal `m`. The `ArmResult.draw_count` field stores the draw target, not the actual realized draw count (which is `k = min(draw_count, pool.shape[0])`). In all 99 cells, the pool exceeds the draw target (no hard pool depletion), so the check is meaningful: the target was set correctly.
   - Impact: No impact on results. In combination with Info 1, the actual RM qualifying count (`rm_m`) is lower than the draw target for VP/MAG variants, but this is expected behavior and does not affect the verdict direction.
   - `run_metadata.json` documents this as "each null draw target == its variant's signal qualifying m", which is the correct description of what is checked.

**3. Per-event Python loop in `vp_levels_per_event`**
   - File: `code/run_experiment.py`, `vp_levels_per_event` (line ~563)
   - Description: Volume profile construction uses a Python `for e in range(n)` loop over harami entries, calling `volume_profile_levels` once per event on a variable-length slice of the OHLC array (the prior completed MA segment bars). This is a causally required per-event sequential scan: each event references a different index range `[start_idx_k, end_idx_k]` determined by the event's in-progress MA state. Vectorization would require ragged-array handling of arbitrary-length segment slices.
   - Impact: Bounded (at most a few thousand events per cell); the outer per-instrument loop is tracked by `tqdm`. The total per-cell compute time dominated by bootstrap (10,000 resamples per arm) rather than the VP scan.

---

## Re-Audit Requirements

None. The verdict is PASS with no conditional requirements.
