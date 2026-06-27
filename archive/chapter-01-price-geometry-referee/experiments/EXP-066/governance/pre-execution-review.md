# Pre-Execution Governance Review — EXP-066

**Experiment:** EXP-066 — MA(20,50)-Substrate Position-Management Exits (dual-object, Phase 015 S3)  
**Family:** CF-HA-HARAMI-001  
**Phase:** 015 — MA-Substrate Conditioned Harami Full Surface  
**Checkpoint:** `2026-06-17-015-ma-substrate-conditioned-harami-full-surface`  
**Amendment:** D0-Amendment-001 (2026-06-17) — Dual Parallel Substrate  
**Reviewer:** research-pipeline (Stage 4)  
**Date:** 2026-06-18

---

```text
VERDICT: APPROVE
```

---

## Pre-Approval Correction

One bug was identified and corrected before this governance document was written. It is recorded here for full traceability.

**BUG: `last_train_idx` missing from `matched_random_arm` parameter list**

- **Location:** `code/run_experiment.py`, function `matched_random_arm` (declaration) and its call site inside `_resolve_objects`.
- **Defect:** `matched_random_arm` referenced `last_train_idx` inside its body (passed to `build_active_stops` when `arm.adv_mode == ADV_TRAIL`) but did not declare it as a parameter. The call site in `_resolve_objects` also did not pass it. This would have caused `NameError` at runtime for every TRAIL-PURE, TRAIL-TP-INIT, TRAIL-TP-NOINIT, COMBINED-V1, COMBINED-V2A, COMBINED-V2B, COMBINED-V2C, and any other arm whose `adv_mode == ADV_TRAIL` (8 of 11 alt arm types affected). The bug would have surfaced on the first TRAIL/COMBINED null-arm call in any non-empty cell.
- **Fix applied:** Added `last_train_idx: int` as the final parameter of `matched_random_arm`; updated the call in `_resolve_objects` to pass `last_train_idx` consistently with how `signal_arm` already received it.
- **Scope of fix:** Confined to the parameter declaration and one call site. Logic inside `matched_random_arm` was already correct.

No other issues were found.

---

## Scope Review

| Check | Status | Notes |
|---|---|---|
| Single falsifiable question | PASS | "Do position-management exit strategies improve gross median expectancy for MA-substrate conditioned haramis?" — one question, one axis. |
| Dual-object mandate (Amendment 001) | PASS | Native (`/STRONG-STAT p75` on MA segments, 8360-class) and hybrid (`/STRONG-STAT p75` on ZigZag moves, 3202-class) defined separately; never pooled. |
| 12-arm specification | PASS | BENCH + 11 alt arms (PARTIAL-V1/V2A/V2B/V2C; TRAIL-PURE/TP-INIT/TP-NOINIT; COMBINED-V1/V2A/V2B/V2C) fully declared with fraction tuples, leg types, adverse mode, and warmup logic. |
| Binding endpoint | PASS | P14: per-event position-weighted gross ATR-normalised median return. Real prices only. |
| P4 diagnostic | PASS | Raw mean + 10% trimmed mean + worst-5% tail-share; disclosed, never a viability gate. |
| P5 null | PASS | Matched-random-on-MA null per object per arm; same conditioning object as signal. |
| Reversal event definition | PASS | Next confirmed MA segment with `Direction == rd` OR opposing conditioned harami reversal after entry; first of the two; bounded by bench_N. Not ZigZag primary (corrected in Amendment 001 design). |
| Secondary ZigZag | PASS | `atr_mult=0.5` substrate-independent trailing-stop ratchet for TRAIL-*/COMBINED-* arms; warmup-excluded events disclosed per cell in `secondary_map.csv`. |
| MA adaptive cap | PASS | `k=1.5, window=20, floor=6, statistic=median, min_moves=5`. |
| TRAIN-only stratum | PASS | First 49% (F01 prefix). No TEST reads, no final-30% holdout access. |
| P11+P6 composition rule | PASS | ≥5 cells, ≥3 instruments, ≥3 cells outside 4h domain; per object, applied at arm level. |
| Success criteria | PASS | EVIDENCE_FOR / EVIDENCE_AGAINST / INCONCLUSIVE / SUBSTRATE_METHOD_DEFECT defined with unambiguous thresholds. |
| Signal registry | PASS | CF-HA-HARAMI-001 REGISTERED; HYP-019 in multiplicity registry; S3 arm variants listed under Phase 015 scope. No new candidate slots opened here. |
| No TEST stratum reads | PASS | Scope states TRAIN-only. No test-read-ledger entry required. |
| Complexity budget | PASS | 5 plots, 0 new xen/ modules, full reuse of EXP-064 pipeline fork. |

---

## Analysis Plan Review

| Check | Status | Notes |
|---|---|---|
| Method 1 — Median CI (binding) | PASS | `bootstrap_median_distribution` + `median_ci`; per arm, per object, per cell. Declared primary metric. |
| Method 2 — Mean diagnostic (P4) | PASS | `bootstrap_stat_distribution` for raw mean + 10% trimmed; worst-5% tail-share; all CI'd; never gates viability. |
| Method 3 — Arm-RM contrast | PASS | Independent bootstrap contrast `arm − own-object RM-on-MA median`; binding signal attribution; per arm per object. |
| Method 4 — Arm-BENCH paired contrast | PASS | Paired median contrast on common qualifying subset; binding lever assessment; per alt arm per object. |
| Composition logic | PASS | `median_viable AND beats_rm AND beats_bench → arm_wins`; P11+P6 quorum; per-object verdict; phase verdict aggregation. |
| Implementation safety constraints | PASS | Holdout fence, temporal ordering, causality, real-price discipline, denominator/zero-baseline, determinism, vectorization, performance/parallelism — all stated. |
| Plot definitions | PASS | 5 plots declared and bounded: forest scatter, contrast heatmap, expectancy box, wins map, median-vs-mean skew preview. |
| No new modules | PASS | Zero new `xen/` modules; all analysis uses existing `xen.expectancy`, `xen.position_exits`, `xen.zigzag`, `xen.indicators`. |
| Dual-object reporting | PASS | Native and hybrid reported separately in all analysis methods and in composition readout. |

---

## Code Review

### Organisation and structure

| Check | Status | Notes |
|---|---|---|
| Thread vars before any import | PASS | `POLARS_MAX_THREADS`, `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `NUMEXPR_NUM_THREADS` set via `os.environ.setdefault` in the preamble before `numpy`/`polars` imports. |
| Import ordering | PASS | stdlib → third-party → `sys.path.insert` → xen modules. Path insert deferred past initial imports. |
| VAL-001-style section separators | PASS | Clearly delimited sections: constants, I/O helpers, pure-computation functions, plotting, orchestration, main. |
| Output dirs created only in orchestration | PASS | `RESULTS_DIR.mkdir(parents=True, exist_ok=True)` and `PLOTS_DIR.mkdir(...)` called only inside `run()`. |
| No module-level side effects | PASS | No prints, no file writes, no heavy computation at import time. |
| `tqdm` for multi-minute loops | PASS | `tqdm(INSTRUMENTS, ...)` wraps the outer instrument loop in both sequential and parallel modes. |
| Concise logging | PASS | `LOGGER.info()` used only in `main()`; all helpers return data or write to structured outputs. |

### Holdout exclusion and temporal ordering

| Check | Status | Notes |
|---|---|---|
| Analysis/TRAIN split | PASS | `analysis_rows = int(total_rows * 0.7)`; `train_rows = int(analysis_rows * 0.7)`. Slice by row count on file-order prefix — never sorts full file. |
| No full-file materialisation | PASS | `pl.scan_parquet(path).select(cols).slice(0, train_rows).collect()` — only TRAIN rows collected. |
| Holdout fence on forward scans | PASS | All forward-scan helpers (`harami_entry_indices`, `ma_segment_moves`, `generate_zigzag`, `reversal_event_targets`) receive `train_end_epoch_s`; post-horizon data tagged `DATA_CENSORED` and excluded from outcomes. |
| TEST and OOS never loaded | PASS | No code path reads beyond `train_rows` file-order prefix. |

### Real-price discipline

| Check | Status | Notes |
|---|---|---|
| HA used for detection only | PASS | `harami_entry_indices` operates on HA bars; all return computation uses `real_ohlc(bars)` which extracts `RealOpen/High/Low/Close`. |
| No HA prices in P&L | PASS | `resolve_legs`, `resolve_legs_uncapped`, and `weighted_returns` receive real OHLC arrays exclusively. |
| ATR computed on real prices | PASS | `wilder_atr` called on `ohlc["high"]`, `ohlc["low"]`, `ohlc["close"]` (real prices). |

### Causality and look-ahead bias

| Check | Status | Notes |
|---|---|---|
| In-progress state at entry | PASS | `live_in_progress_state(entry_epoch, ...)` uses `np.searchsorted` with `side='right'` to obtain the MA segment active at (strictly before) each harami bar. |
| MA segment history at entry | PASS | `adaptive_time_caps_by_epoch` computes `bench_N` from MA segments confirmed before entry epoch. |
| Causality check in `_causality_ok` | PASS | Asserts `ma["seg"]["end_idx"][kk] <= entry_idx[valid]` — every segment used was fully confirmed before the entry bar. |
| Reversal event uses confirmed MA segments | PASS | `reversal_event_targets` searches `seg["confirm_epoch"]` for the next segment whose `ConfirmTime > entry`; uses `seg["confirm_idx"]` (bar of confirmation) as exit bar. |
| Secondary ZigZag history gating | PASS | `secondary_history(sec, ...)` gates trailing-stop eligibility; events without prior secondary ZigZag history after entry are warmup-excluded (disclosed, not silently dropped). |

### Statistical correctness

| Check | Status | Notes |
|---|---|---|
| P3 fixed seed | PASS | `np.random.default_rng([BASE_SEED, cell_index, purpose])` — deterministic per (experiment, cell, purpose) tuple. |
| EXP-061 BENCH purposes reused (P12) | PASS | Native `BENCH_PB["nat"]` uses purposes 9000/23000/43000/61000/62000/63000/64000 — identical to EXP-061 M0/RM0. Hybrid uses 81000/83000/85000/71000/72000/73000/74000 — identical to EXP-061 H0/RH0. |
| Non-BENCH purposes fresh (P12) | PASS | `OBJ_BLOCK = {"nat": 100_000, "hyb": 200_000}`; all non-BENCH arms use `OBJ_BLOCK[obj] + arm.idx * 10 + off` — no overlap with EXP-061 stream space (max 87000). |
| Zero-baseline / denominator safety | PASS | `tail_share_worst5` returns `0.0` when no negative-return mass. `_fraction_negative` returns `0.0` for empty arrays. Denominators guarded throughout. |
| Matched-random draw count | PASS | Each null arm draws exactly `signals[arm.aid].m` events — matched by construction; `matched_count_ok` invariant asserted per cell. |
| P15 fill model | PASS | `resolve_legs` uses `PX_FAV/PX_ADV/PX_TIMECAP/PX_TRAIL` path codes; bullish `O→L→H→C`, bearish `O→H→L→C` intrabar touch ordering consistent with EXP-054 approximation bounds. |
| No bootstrap on unpowered cells | PASS | `_summarize_arm` returns empty distributions (`np.empty(0)`) when `m < POWER_FLOOR` and does not compute CIs; powered flag propagates correctly into composition. |

### Invariant and reconciliation gates (P12, Amendment 001)

| Check | Status | Notes |
|---|---|---|
| Native BENCH reconciles to EXP-061 M0 | PASS | `exp061_reconciliation` loads `EXP-061 per_cell_expectancy.parquet`; compares native BENCH `m` and `median` to EXP-061 M0 anchor to `RECON_TOL = 1e-9` per cell. |
| Hybrid BENCH reconciles to EXP-061 H0 | PASS | Same reconciliation checks hybrid BENCH `m` and `median` against EXP-061 H0 anchor. |
| Mismatch → defect | PASS | Any reconciliation mismatch or missing anchor sets `defect["is_defect"] = True` → `SUBSTRATE_METHOD_DEFECT` verdict. |
| Exit-reason weights sum to 1.0 | PASS | `exit_reason_weights` invariant checked per arm per object per cell; failure sets invariant flag → defect. |
| `fav_dist > 0` for every BENCH event | PASS | `fav_dist_positive` asserted per cell; failure → defect. |
| `matched_count_ok` | PASS | Null-draw count asserted to equal signal qualifying `m`; failure → defect. |

### Parallelism and determinism

| Check | Status | Notes |
|---|---|---|
| `ProcessPoolExecutor` per-instrument | PASS | Worker pool with `max_workers=workers`; results reassembled in fixed `INSTRUMENTS` order via `by_inst[futures[fut]] = fut.result()` dict. |
| Per-process thread pinning | PASS | Thread env vars set before imports propagate into worker processes. |
| RNG order-independence | PASS | Every RNG is seeded by `(BASE_SEED, cell_index, purpose)`; draws are independent across workers. |
| Determinism replay | PASS | First usable cell per instrument recomputed and asserted byte-identical; non-determinism → defect flag. |

### Memory management and plot safety

| Check | Status | Notes |
|---|---|---|
| Per-cell data released | PASS | `del cell` after `arm_rows` extraction; `del train_1m` at end of `process_instrument`. |
| Plots rendered from summary rows only | PASS | All 5 plot functions receive the already-collected `rows: list[dict]`; no data file re-reads inside plotting. |
| `plt.close(fig)` after each save | PASS | Every plot function closes its figure immediately after `fig.savefig(...)`. |

### Output completeness

| Check | Status | Notes |
|---|---|---|
| `per_cell_expectancy.parquet` | PASS | Written via `pl.DataFrame(rows, strict=False).write_parquet(...)`. |
| `position_mgmt_map.csv` | PASS | Member rows filtered; all binding columns included. |
| `secondary_map.csv` | PASS | Exit-reason weight columns (`ew_*`) included per arm per object per cell. |
| `readiness.csv` | PASS | Per-cell N/fav_dist readiness snapshot. |
| `reconciliation.csv` | PASS | Checked cells written (per-object m + median vs EXP-061 anchor). |
| `composition_readout.json` | PASS | Per-object per-arm composition flags + phase verdict + `phase_stronger_object`. |
| `run_metadata.json` | PASS | Full provenance: checkpoint, amendment, objects, arms, seed, params, methods, defect state, reconciliation, holdout fence, fill approximation disclosure, reproduction-safety narrative. |
| 5 plots | PASS | `per_arm_median_forest.png`, `arm_contrast_heatmap.png`, `expectancy_distribution_by_arm.png`, `p11_wins_map.png`, `median_vs_mean_p4_preview.png`. |

### Phase 015 binding inheritances

| Inheritance | Status | Notes |
|---|---|---|
| B1 — Fixed MA(20,50) | PASS | `MA_FAST=20, MA_SLOW=50` constants; not swept. |
| B2 — Median binding endpoint (P14) | PASS | `bootstrap_median_distribution` + `median_ci` as primary; not mean. |
| B3 — RM3-on-MA null per object | PASS | `matched_random_arm` draws on full-bar MA-in-progress pool per object independently. |
| B4 — Non-4h composition (P6) | PASS | `P6_MIN_NON_4H=3`; `non4h_composes` checked in `_arm_composition`. |
| B5 — Fixed seed (P3) | PASS | `BASE_SEED = 20260616`; `np.random.default_rng([BASE_SEED, cell_index, purpose])`. |
| B6 — EXP-061 code reuse / 014-B swap | PASS | `exp061_reconciliation` verifies byte identity to 1e-9; all BENCH purposes identical to EXP-061. |

### Amendment 001 specific checks

| Check | Status | Notes |
|---|---|---|
| Two parallel objects, never pooled | PASS | `OBJECTS = ("nat", "hyb")`; all metrics, composition, and readout are per-object. |
| Native defined as MA-segment /STRONG-STAT p75 | PASS | `cond_masks["nat"] = ma["stat"]["retained_p75"]` (8360-class). |
| Hybrid defined as ZigZag /STRONG-STAT p75 | PASS | `cond_masks["hyb"] = zz["retained_p75"]` (3202-class). |
| Metadata records amendment | PASS | `"amendment": "D0-amendment-001-dual-parallel-substrate (2026-06-17); supersedes prior EXP-066 scope"` in `run_metadata.json`. |
| EXP-067 / EXP-068 champion slots not adjudicated here | PASS | G-015 gate not invoked inside EXP-066; `registry` metadata note confirms no candidate slots opened. |

---

## Summary

All scope, analysis-plan, and code checks pass. One runtime bug (`last_train_idx` missing from `matched_random_arm`) was identified during code review and corrected before this verdict was issued. No outstanding issues remain. The implementation is ready for manual execution.
