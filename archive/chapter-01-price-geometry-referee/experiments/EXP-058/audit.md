# Audit Report: Experiment EXP-058

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Implements the 5 predeclared variants (BENCH, THIRD-TIME-T12/24/48, THIRD-EVENT) over the 99-cell grid. All frozen D0 constants match scope. Population construction is byte-identical to EXP-053. |
| `code/run_experiment.py` | Edge cases | PASS | Empty cells, no-move cells, COVERAGE_EXCLUDED cells handled (3 EXCLUDED cells). Zero-harami cells short-circuit cleanly. |
| `code/run_experiment.py` | Type safety | PASS | Public functions have type hints. `@dataclass`-based `ArmResult`/`VariantSpec` typed explicitly. `np.ndarray` dtypes are explicit (`np.int64`, `np.float64`). |
| `code/run_experiment.py` | NaN handling | PASS | `qualifying_mask` filters for `ATR_entry > 0` before any metric. `catch_nan` is not needed — returns missing under conditional logic (lines 435-440). |
| `code/run_experiment.py` | Holdout exclusion | PASS | Lines 208-224: lazy `pl.scan_parquet` -> `slice(0, train_rows)` -> `collect()`. Full file never sorted/collected. `train_end_ts` is the last row of the first-49% slice. No TEST or holdout rows ever materialized. |
| `code/run_experiment.py` | Loader ordering | PASS | `load_train_1m` asserts `CloseTime` is already sorted in the collected slice (line 216). F01 file-order prefix convention means the first N file-order rows are the earliest chronologically. |
| `code/run_experiment.py` | Memory/performance | PASS | Per-cell bounded: process, persist summaries, `del cell`. Large bootstrap matrices are per-cell, not accumulated. Plots from aggregated summaries + pooled per-event sample only. |
| `code/run_experiment.py` | Safe optimization | PASS | P15 resolver (`resolve_path_ordered`) is an explicit bounded sequential scan — not vectorized (the causal semantics are the object under test). The `/THIRD-EVENT` cap helper uses `searchsorted` + bounded forward scan (not a full vectorized pass across all moves). Flag-bearer sections are kept explicit per plan. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` over `instruments` outer loop (line 1217). Bounded per-cell processing, no per-row log noise. |
| `code/run_experiment.py` | Logging/output | PASS | `run()` returns a concise summary; `main()` logs verdict, passers, status counts. All helper functions return data rather than print. |
| `code/run_experiment.py` | Organization/import side effects | PASS | Imports -> path setup -> constants -> types -> I/O -> pure computation -> per-cell pipeline -> composition -> determinism -> plotting -> orchestration -> `main()`. Output directories created inside `run()` (lines 1202-1203), not at import time. |
| `code/run_experiment.py` | Plot data reuse | PASS | Plots consume `records` (aggregated per-cell summaries) and `pooled` (collected per-event returns from viable cells during the main pass). No reload or regeneration for plotting. |
| `code/run_experiment.py` | Docstrings | PASS | Module-level docstring covers purpose, usage, and constraints (lines 1-37). Public functions have docstrings with Parameters/Returns. |
| `third_barrier.py` | Correctness | PASS | `third_event_caps` performs causal forward `searchsorted` + bounded linear scan for next `rd`-confirmed move. `variant_caps` delegates time variants to `adaptive_time_caps_by_epoch` with variant's floor, event variant to `third_event_caps`. |
| `third_barrier.py` | Edge cases | PASS | Zero entries handled (line 105-106). No `rd`-confirm within backstop falls through to backstop (line 127). BENCH-warmup entries excluded with `avail=False` (lines 110-111). |
| `third_barrier.py` | NaN handling | PASS | No NaN-producing operations. `bench_n_event` and `move_direction` are int arrays; `entry_epoch`/`move_confirm_epoch` are int64 epochs. |
| `third_barrier.py` | Type safety | PASS | All function signatures typed. Return dict has typed `np.ndarray` values. |

## Numerical Validation

### Spot Checks

**BENCH vs EXP-053 reconciliation (BIT-EXACT to 1e-9):** 99/99 cells match on `m`, `median`, and `r_firsthit`. Representative sample (BTCUSD-5m):

| Metric | EXP-058 (BENCH) | EXP-053 | Δ |
|--------|-----------------|---------|---|
| m | 3117 | 3117 | 0 |
| Median | 0.05697336449019767 | 0.05697336449019767 | < 1e-16 |
| r_firsthit | 0.5057705363204344 | 0.5057705363204344 | < 1e-16 |

EURUSD-5m: (m=3202, median=0.016051747334353203, r=0.49406620861961276) — identical on both sides. Full 99-cell table at `results/population_reconciliation.csv`.

**Determinism replay:** All 17 instruments' first usable cell (5m domain, the agreed determinism sample) produced byte-identical outputs on re-run across all 5 binding variants and both baselines.

**Causality/invariants:** 0 violations. Cap monotonicity holds (BENCH ≤ T12 ≤ T24 ≤ T48 event-wise) across the conditioned set. `/THIRD-EVENT` cap bounds satisfied (`1 ≤ n_event_evt ≤ 8×bench_N`) with forward `rd`-confirm exit. Warmup masks identical across time variants.

### Factual Counts (from `composition_readout.json`)

| Metric | BENCH | T12 | T24 | T48 | THIRD-EVENT |
|--------|-------|-----|-----|-----|-------------|
| Powered cells (m≥30) | 99 | 99 | 99 | 99 | 99 |
| Viable cells (CI_low>0) | 8 | 6 | 4 | 2 | 1 |
| Win cells (viable + beats_bench) | 0 (N/A) | 3 | 2 | 2 | 0 |
| P11 pass? | N/A | No (3<5) | No (2<5) | No (2<5) | No (0<5) |

All 99 cells completed. 3 COVERAGE_EXCLUDED cells as expected (US500-4h, JP225-2h, JP225-4h). All 5 binding variants' per-variant compositions are reported — no file-drawered variant.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| Qualifying events per cell (BENCH) | >0, ≥30 for powered | min=45 (XAUUSD-4h), max=3754 (USTEC-5m) | YES |
| Qualifying events per cell (T48) | ≥0 (depleted expected) | 99/99 powered | YES |
| First-hit `r` (BENCH) | ~0.50 (1:1 benchmark) | 0.32–0.67 across cells, median ≈ 0.50 | YES |
| Determinism checks | 17 cells, all pass | 17/17 pass | YES |
| EXP-053 reconciliation | 99/99 cells match | 99/99 cells match | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| BENCH viable cells | 8/99 | YES | Replicates EXP-053: the hybrid signal is modestly positive on ~8 cells with benchmark 1:1 fav/adv |
| Alternative variants win cells | 3 max (T12) | YES | Horizon extension does not systematically improve expectancy — consistent with censoring eroding the signal at longer windows |
| THIRD-EVENT win cells | 0 | YES | The ZigZag event barrier is the weakest performer — the expected `rd`-confirm event is often too far out, pushing the exit into the backstop (a time cap) or DATA_CENSORED |
| EVIDENCE_AGAINST verdict | EVIDENCE_AGAINST | YES | `EVIDENCE_AGAINST` fires because `bench_pow=True` AND `alt_pow=True` AND `passers=[]` — adequate power exists but no alternative beats the benchmark at P11 quorum. This is a measured-negative characterization, not a power failure. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Regime-clustered moving-block bootstrap | Block resampling preserves local dependence | YES  | Block length `b = round(m^(1/3))` per cell, median block length ~15 for typical m~3000. Fixed seed per cell/variant ensures reproducibility. |
| Paired contrast (variant vs BENCH) | Common qualifying subset S is sufficient | YES  | Events early-resolved as FAV/ADV pair by construction; the signal lives in events BENCH TIMECAP'd that the longer window resolves differently. `\|S\|` reported per cell. |
| Non-parametric bootstrap | No distributional assumption | YES  | Bootstrap of the median — no normality, stationarity, or i.i.d. assumed. The blocking accounts for serial dependence. |
| Power adequacy | ≥30 qualifying events per cell for reportability | YES  | All 99 cells reach ≥30 events for every variant (POWER_FLOOR=30). The INCONCLUSIVE path (power-limited by censoring) does not apply here. |

## Results Plausibility

The `EVIDENCE_AGAINST` verdict is consistent with the broader 014-B surface pattern:

- **EXP-056 (favourable-target OAT)**: EVIDENCE_AGAINST — no `/VPTARGET`/`/MAGTARGET` combination beat the benchmark 50% favourable configuration at P11 quorum.
- **EXP-058 (third-barrier OAT)**: EVIDENCE_AGAINST — no `/THIRD-TIME` floor or `/THIRD-EVENT` structural barrier beats the benchmark adaptive cap at P11 quorum.

The economic mechanism is coherent: extending the holding horizon (time or structural event) admits more symmetric noise. First-hit `r` stays near 0.50 across all variants (as expected under fixed 1:1 fav/adv geometry), confirming the third-barrier lever does **not** move expectancy through the FAV/ADV ratio — it moves through the TIMECAP exit price. The data show that longer TIMECAP exits do not systematically land favourably enough to overcome the horizon cost.

The BENCH variant's 8 viable cells (BTCUSD-5m/30m, EURUSD-1h, GBPUSD-4h, USDCHF-4h, USDCAD-15m, AUDUSD-4h, EURJPY-15m) replicate EXP-053's result on the same grid — confirming the benchmark anchor.

All disclosed secondaries (censoring fraction, TIMECAP fraction, `/STRONG-HA` arm, STAT-MAD, P13 baselines, first-hit `r`) are reported as specified in the scope and analysis plan.

## Scope Compliance

- **Analysis plan followed**: YES
- **Variant sweep**: All 5 predeclared binding variants implemented and reported (BENCH, THIRD-TIME-T12, THIRD-TIME-T24, THIRD-TIME-T48, THIRD-EVENT). Both `/STRONG-STAT` (binding) and `/STRONG-HA`/STAT-MAD (disclosed) arms run through the identical pipeline.
- **Deviations**: None
- **Complexity budget**: 4/4 statistical methods used, 5/5 visualisations implemented, 1/1 new module (`third_barrier.py`)
- **Holdout exclusion verified**: YES — lazy scan + file-order prefix slice; full file never sorted/collected. Per-cell `train_end_ts` fence. Forward scans clipped to the TRAIN edge.
- **Slot/ledger accounting**: 0 candidate slots consumed, 0 TEST reads (confirmed in `composition_readout.json` and `run_metadata.json`).
- **Pre-execution operator decisions honoured**: YES — floor-only sweep (k=1.5, window=20 fixed), `/THIRD-EVENT` definition (next `rd`-confirm + 8× backstop), all post-result variant selection prohibited.

## Issues

### Critical

None.

### Warning

None.

### Info

1. **DE30 truncated history disclosure.**
   - Description: DE30 broker history ends 2026-01-16, per VAL-003 disclosure. DE30 counts derive from its realised timeline and are not span-comparable to other instruments. Disclosed in `run_metadata.json` and DE30 results are presented alongside other cells. This is a known constraint, not a defect.
   - Impact: None — DE30 results are valid within its own coverage period. Per-cell composition counts are fair.

2. **P15 fill approximation is a documented limitation.**
   - Description: The P15 intrabar path (`O→L→H→C` for bullish, `O→H→L→C` for bearish) is an approximation of unobserved intrabar motion, not a full 1-minute tick replay. Documented in scope, analysis plan, and metadata. EXP-054 bounded its median impact at Δr ≈ 0.010 ATR units.
   - Impact: Negligible for the OAT/variant comparison — the same fill model applies identically to all variants, so the contrast is unbiased. Not a defect.

## Re-Audit Requirements

None. This is a clean PASS with no issues requiring remediation.
