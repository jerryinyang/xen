# Audit Report: Experiment EXP-059

**Title:** Position-Management Exits (Conditioned HA Harami; `/EXIT-PARTIAL`, `/EXIT-TRAIL-STRUCT`, individually and combined)
**Phase:** 014-B (Surface read 4)
**Hypothesis:** HYP-012
**Family:** CF-HA-HARAMI-001

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 3

All governance constraints, correctness gates, and invariant checks pass. The code faithfully implements the 12-arm predeclared sweep, the conditioned population reconciles byte-identically with EXP-053, determinism holds across 17 replayed cells, and no causality or invariant violations are detected. The numerical outputs are internally consistent and plausible given the scoped limitation (benchmark 6-bar cap bounding runner/reversal legs). The EVIDENCE_FOR verdict on PARTIAL arms is supported by the data. Three minor info items are noted.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | BENCH reproduces EXP-053 per-cell to 1e-9 across all 99 cells; all 6 invariants pass. |
| `code/run_experiment.py` | Edge cases | PASS | Empty harami sets, zero moves, truncated forward windows handled; 3 COVERAGE_EXCLUDED cells produce excluded records. |
| `code/run_experiment.py` | Type safety | PASS | NumPy typed arrays throughout; leg kinds/adv modes use integer constants; PX_CLASS int codes. |
| `code/run_experiment.py` | NaN handling | PASS | Explicit `np.isfinite` guards on ATR entry; `np.errstate(invalid="ignore")` on division; NaN sentinel for unresolved legs. |
| `code/run_experiment.py` | Holdout exclusion | PASS | F01 file-order slice of first `train_rows` rows; no sort/collect of full file; every domain bar fenced `CloseTime <= train_end_ts`; forward scans clipped to `last_train_idx`. |
| `code/run_experiment.py` | Loader ordering | PASS (with note) | Uses file-order prefix (not `sort("CloseTime")`) — this is the established EXP-049/053–058 convention, explicitly scoped, and the chronological assertion (`is_sorted`) guards against ordering violations. |
| `code/run_experiment.py` | Memory/performance | PASS | Lazy `pl.scan_parquet` with column projection; per-cell `del cell`/`del train_1m`; bounded per-event scan `O(bench_N * n_legs)`; bootstrap batching. |
| `code/run_experiment.py` | Safe optimization | PASS | Resolvers are explicit sequential loops ("do not vectorize" contract); no optimization alters membership/order/denominators. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` on the instrument outer loop (17 iterations, ~6m per loop). |
| `code/run_experiment.py` | Logging/output | PASS | Concise `LOGGER.info` in `main()`; helpers return data (no side-effect prints). |
| `code/run_experiment.py` | Organization/import side effects | PASS | Imports → path setup → constants → types → I/O → pure computation → plotting → orchestration → `main()`; `results/` and `plots/` created in `run()`, not at import. |
| `code/run_experiment.py` | Plot data reuse | PASS | Plots consume collected per-cell summaries (`records`) and a pre-pooled `pooled` dict from the analysis pass; no second load. |
| `code/run_experiment.py` | Docstrings | PASS | Module-level docstring covers all 5 pipeline steps; public functions have Parameters/Returns. |
| `python/src/xen/position_exits.py` | Correctness | PASS | `resolve_legs` with `LEG_LEVEL@fav` reproduces `resolve_path_ordered` BENCH to 1e-12; degenerate 3-leg match passes; trailing monotone invariant passes. |
| `python/src/xen/position_exits.py` | Edge cases | PASS | Zero events → empty arrays; `LEG_NONE` arms (TRAIL-PURE) produce no fav-side exit; reversal_idx = -1 skips reversal check; `population` mask gates all computations. |
| `python/src/xen/position_exits.py` | Type safety | PASS | NumPy typed arrays; `adv_cls` set from `adv_mode` enum; `open_mask` bool per event. |
| `python/src/xen/position_exits.py` | NaN handling | PASS | Active-stops array seeded `np.nan` for inactive; `np.isfinite` check in `trail_is_monotone` and `_scan_event`; `weighted_returns` `np.errstate` guards division. |
| `python/src/xen/position_exits.py` | Holdout exclusion | N/A | No I/O in the module; `last_train_idx` bounds passed by caller. |
| `python/src/xen/position_exits.py` | Causal/streaming | PASS | `build_active_stops` uses only `ConfirmIdx <= i`; `_scan_event` scans forward only; reversal-event locator uses `side="right"` searchsort (strictly after entry). Directional encoding: `Direction == rd` for take-profit, not `-rd`. |

## Numerical Validation

### Spot Check — BTCUSD-5m, PARTIAL-V2A

The three-leg V2A scheme: levels at `C + rd * {1/3, 2/3, 1} * 0.5 * M_sofar`. Reported median = 0.277, BENCH median = 0.057, paired contrast CI_low = 0.195.

BENCH median of 0.057 ATR units for BTCUSD-5m reproduces EXP-053 exactly (0.05697). The PARTIAL-V2A median is 4.9× the benchmark, with a positive contrast lower bound — the fractional-target banking captures more value than the single 50% exit. Plausible: three equal legs at increasingly distant targets capture full-runner moves while banking earlier profits.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| Direction `rd` | {+1, -1} | {-1, 1} | YES |
| `retained_fraction` | [0, 1] | [0.12, 1.0] across arms | YES |
| Qualifying event count per cell | ≥ 30 or `NOT_VIABLE_BY_POWER` | [0, 3754] | YES |
| Benchmark first-hit `r` | ≈0.50 (EXP-049 anchor) | [0.32, 0.67] across 99 BENCH cells | YES |
| Win rate (BENCH) | ≈0.50 | [0.47, 0.55] | YES |
| Leg weights sum | 1.0 | Within 1e-12 | YES (invariant) |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| EVIDENCE verdict | EVIDENCE_FOR | YES | 4 PARTIAL arms clear P11 on wins-over-benchmark (≥5 cells / ≥3 instruments) |
| PARTIAL-V2A wins | 53 cells / 17 instruments | YES | Even-thirds fractional targets benefit from consistent mid-range profit capture; broadest adoption across the grid |
| PARTIAL-V1 wins | 25 cells / 14 instruments | YES | Event-trigger (first-profit + reversal) gives more selective but still broad coverage |
| PARTIAL-V2B wins | 27 cells / 14 instruments | YES | Runner to 1.5× fav_dist constrained by ~6-bar cap in 96/99 cells; still beats benchmark in subset |
| PARTIAL-V2C wins | 45 cells / 17 instruments | YES | V2C hybrid (fixed targets + reversal runner) performs between V2A and V2B — runner leg adds value vs V2B floor targets |
| TRAIL arms viable cells | 0 / 99 | YES (consistent with caveat) | None reach CI_low > 0; the structure trailing stop within the 6-bar cap is uniformly detrimental — consistent with the disclosed limitation ("EXP-060 defers the horizon interaction") |
| COMBINED arms viable cells | 0 / 99 | YES | Replacing the fixed 1:1 stop with a trailing stop on partial-leg arms destroys already-positive expectancy — the trailing stop binds before partial legs can realise their value |
| BENCH viable cells | 9/99 | YES | Consistent with EXP-053: conditioned signal has positive gross expectancy in ~9% of cells under the benchmark single-geometry exit |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| F01 file-order prefix | 1-minute rows are chronological in file order | YES | Asserted in-code (`CloseTime.is_sorted()`) — passes for all 17 data files. |
| P15 path model | Intrabar motion follows `O→L→H→C` (bullish) / `O→H→L→C` (bearish) | INHERENT | Documented approximation (see `run_metadata.json` "fill_approximation"); EXP-054 bounds the error. Not testable within this audit. |
| Moving-block bootstrap | Approximate within-cell stationarity; block length `b = round(m^{1/3})` absorbs short-range dependence | ACCEPTED | Standard programme caveat; no stronger claim is made. Block lengths: 4–15 per cell. |
| Paired contrast pairing | Common qualifying subset preserves event ordering | YES | Common subset is `res.qual & bench.qual`, order-preserving by construction (`order = np.argsort(entry_idx[common])`). |
| Equal-leg weighting | `w = 1/3` for each of 3 legs | YES (within 1e-12) | Float representation produces 0.9999999999999999 sum; invariant tolerance absorbs. |
| Secondary ZigZag availability | Trailing arms require ≥1 confirmation before entry | YES | `warmup_excluded` = 0 on all cells (conditioned population has sufficient history); the check is correctly implemented. |

## Results Plausibility

1. **PARTIAL arms > BENCH** — the partial-exit schemes bank profit at intermediate levels while the single-leg BENCH waits for the full 50% target. In a mean-reverting / cap-bound environment (96/99 cells at 6-bar floor), partial exits are expected to capture value before a reversal. V2A (three evenly-spaced levels) performs best (53 wins) because it is the most diverse across price-space. Plausible and consistent with the mechanism.

2. **TRAIL arms uniformly negative** — the structure trailing stop in a ~6-bar window tightens against the position before the favourable target is reached. The `ew_TRAIL` fraction (e.g., 55% for BTCUSD-5m TRAIL-PURE, 52% for TRAIL-TP-INIT) confirms the stop binds more often than not. Plausible: in short windows with choppy price action, a 0.5×ATR ZigZag retracement trigger fires frequently.

3. **COMBINED arms worse than standalone PARTIAL** — replacing the fixed 1:1 stop with a trailing stop destroys the partial-exit advantage (0 viable cells vs 25–53 wins). The trailing stop binds before the partial legs can realise their favourable exits. This is a clean OAT measurement: the adverse-side trailing mechanism is not helpful under the benchmark cap.

4. **BENCH `r ≈ 0.50`** — first-hit ratios across all 99 cells cluster near 0.50 (range 0.32–0.67), reproducing EXP-049/053. The occasional deviation (GBPUSD-2h r=0.34, NZDUSD-1h r=0.65) reflects cell-specific market structure, not a bug.

5. **V2B weaker than V2A** — 27 vs 53 wins. The 1.5× runner leg in V2B rarely fills within the 6-bar cap (evidenced by high `ew_TIMECAP` fraction: 48.5% for BTCUSD-5m V2B). This is the disclosed limitation.

## Scope Compliance

- **Analysis plan followed**: YES
- **Deviations**: None. All 12 predeclared arms computed, all 5 visualisations produced, all 6 invariants checked, all disclosed secondaries recorded.
- **Complexity budget**: 4 stat methods / 4 budgeted; 5 plots / 5 budgeted; 1 module (`position_exits.py`) / 1 budgeted.
- **Holdout exclusion verified**: YES — F01 file-order slice, assertion of chronological order, domain bars fenced, forward scans clipped to `last_train_idx`, `DATA_CENSORED` on truncated windows.
- **Determinism**: YES — 2-pass replay on 17 cells (first usable per instrument) passes all.
- **EXP-053 reconciliation**: YES — all 99 cells reproduce EXP-053 median, count, and first-hit `r` to 1e-9.
- **Invariants**: All 6 pass in every cell (weights, single-leg match, degenerate match, shared-stop, monotone, BENCH reconciliation).

## Issues

### Critical

None.

### Warning

None.

### Info

1. **F01 file-order vs sort-by-timestamp.** The loader uses `scan.slice(0, train_rows)` on the file-order Parquet prefix rather than `sort("CloseTime")` before slicing (the standard convention per `_pipeline-config.md`). This is the **established** EXP-049/053–058 convention, explicitly documented in `scope.md` §Data Requirements, and guarded by the `is_sorted` assertion. No correctness issue; noted for consistency awareness.

2. **TRAIL and COMBINED arms produce zero viable cells across all 99 cells (100% CI_SPANS_0).** This is not a code defect — it is a genuine measurement within the scoped limitation (benchmark cap collapsed to 6-bar floor in 96/99 cells). All 7 non-PARTIAL arms are uniformly negative on expectancy, consistent with the disclosed caveat that the horizon × position-management interaction is deferred to EXP-060. However, the completeness of the wipeout (0 viable cells on every trailing/combined arm, despite 99/99 powered) is striking and should be highlighted in the results interpretation to avoid misinterpretation as "trailing never helps" rather than "trailing does not help within ~6 bars."

3. **Float precision in leg weights.** Three equal legs produce `sum = 0.9999999999999999`. The `weights_sum_ok` invariant tolerance (1e-12) absorbs this, and the per-event `R_event = Σ w_l · ...` uses single-precision-appropriate accumulation. Immaterial — noted for audit transparency (previously flagged in pre-execution review).

## Re-Audit Requirements

None — PASS.
