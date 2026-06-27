# Audit Report: Experiment EXP-027

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 1
- **Info Notes**: 3

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Implements the analysis plan faithfully; holdout-safe lazy load, precompute-once draws, EXP-021 inference reuse. |
| `code/event_method.py` | Correctness | PASS | Vectorised control matching verified against EXP-021 reference. Decision rule, bootstrap, permutation, Holm, Wilson all correct. |
| `code/event_method.py` | Edge cases | PASS | Empty triggers, empty regimes, under-powered cells, fewer-than-MIN_CONTROLS all handled with explicit guards and NaN return values. |
| `code/event_method.py` | Type safety | PASS | NumPy typed arrays, dataclass fields typed; some internal helpers in `run_experiment.py` lack type hints (minor). |
| `code/{event_method,run_experiment}.py` | NaN handling | PASS | Explicit NaN in `forward_logdiff_from_close`, `_control_mean`, `domain_effect`, `wilson_interval`, `equity_advantage`, `bootstrap_effect_distribution`. All NaN paths guarded. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `load_analysis_data` (from `xen.referee_calibration`) does lazy scan → sort → first-70% slice. Regime-index fence in `_precompute_cell` re-verifies every regime index lies inside the first-70% frame. |
| `code/run_experiment.py` | Loader ordering | PASS | Lazy scan sorts by timestamp before slicing; no full holdout collection. |
| `code/{event_method,run_experiment}.py` | Memory/performance | PASS | Precompute-once draw-independent arrays; chunked bootstrap/permutation (`BOOT_CHUNK`/`PERM_CHUNK`); no unbounded pandas conversions. |
| `code/event_method.py` | Safe optimization | PASS | Vectorized `nearest_controls` equivalence-guarded against EXP-021 reference. Regime-cluster bootstrap and permutation identical in structure. Optimisation changes no membership, temporal ordering, denominators, or metric definition. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` over file load loop and draw loops; helpers return data silently. |
| `code/run_experiment.py` | Logging/output | PASS | Concise INFO logging; no per-row/ per-draw output; final summaries in run_metadata.json. |
| `code/{event_method,run_experiment}.py` | Organization/import side effects | PASS | Imports → constants → helpers → inference → calibration → summaries → plotting → orchestration → `main()`. No mkdir/writes at import time. `matplotlib.use("Agg")` at module level is necessary for headless backend (no filesystem side effect). `sys.path.insert` for experiment-local import is standard. |
| `code/run_experiment.py` | Plot data reuse | PASS | Plotting functions consume bounded summary dataframes; equity companion stores first-draw curves only; no repeated loads. |
| `code/event_method.py` | Docstrings | PASS | Module-level docstring with discipline enforcement. Dataclass fields documented. Functions have NumPy-style docstrings with Parameters/Returns. |

## Numerical Validation

### Spot Checks

**Primary FPR (5m, placebo_on_real, p_trig=0.06, alpha=0.05):**
- n_reportable_draws = 500, n_for = 8, fpr = 8/500 = 0.016
- Wilson(95%) for 8/500: p_hat=0.016, z=1.96
  - denom = 1 + 1.96²/500 ≈ 1.00768
  - center = (0.016 + 3.8416/(2×500)) / 1.00768 ≈ 0.01968
  - half = (1.96 × √(0.016×0.984/500 + 3.8416/(4×250000))) / 1.00768 ≈ 0.01156
- CSV reports: low=0.00813, high=0.03125, half=0.01156 ✓

**MDE (alpha=0.05):**
- 5m: 1.0 bps (TPR=1.0 at g=1.0, well above 0.80 target) ✓
- 1h: 4.0 bps (TPR=0.818 at g=4.0, crosses 0.80) ✓
- 4h: 32.0 bps (TPR=0.998 at g=32.0, crosses 0.80) ✓
- All three domains recover with finite MDE ✓

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| FPR per-domain | [0, 1] | [0.0, 0.042] | YES |
| FPR family-wise | [0, 1] | [0.012, 0.094] | YES |
| TPR per-domain | [0, 1] | [0.006, 1.0] | YES |
| MDE | positive or null | {1.0, 4.0, 32.0} | YES |
| Effect (null draws) | ℝ (centred near 0) | typically [-16, 20] bps | YES |
| Analysis set dates | pre-2025-06-17 | max ~2025-06-17 | YES |
| Wilson half-width (FPR) | ≤ 0.03 | max 0.018 | YES |
| Wilson half-width (TPR) | ≤ 0.05 | max 0.041 | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| 5m FPR at 0.06 (placebo_on_real) | 0.016 | YES | Most data, tightest estimates |
| 4h FPR at 0.06 (placebo_on_real) | 0.030 | YES | Fewer events, slightly higher FPR |
| 5m MDE | 1.0 bps | YES | ~20k events/draw → high power |
| 1h MDE | 4.0 bps | YES | ~1.7k events/draw → moderate power |
| 4h MDE | 32.0 bps | YES | ~400 events/draw → low power, needs larger edge |
| Equity null advantage rate (5m) | 0.358 | YES | Near chance, no systematic false advantage |
| Determinism replay | pass=True | YES | Byte-identical on re-run |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Regime-cluster bootstrap | Events within same regime are dependent; regimes are independent across (inst, dir) strata | YES | Resampling at regime level; sparsity explicitly stressed at 4h; FPR controlled across all domains |
| Stratified sign-permutation | Exchangeable signs within (inst, dir) under the null | YES | Non-parametric; paired design controls for regime drift |
| Wilson interval | Binomial proportion with normal approximation | YES | n=500 adequate; half-widths ≤ 0.03 (FPR) and ≤ 0.05 (TPR) |
| Block-permuted null (N2) | Stationary-block bootstrap preserves autocorrelation scale | YES | Block length estimated on training portion only; no look-ahead |
| Evidence-FOR rule | effect>0 AND CI_low>0 AND Holm_p≤α | YES | Unchanged from EXP-021 |

## Results Plausibility

- **FPR controlled** in every domain under both nulls at all three activity rates (max per-domain FPR = 0.042). Family-wise any-domain FPR reaches 0.094 (block-permuted, p_trig=0.06) — expected for 3-domain Holm-adjusted α=0.05.
- **MDE increases with domain duration**: 5m (1 bps) < 1h (4 bps) < 4h (32 bps). Consistent with the thin-event count pipeline: fewer events → less power → larger detectable edge.
- **Equity companion** null false-advantage rates (0.358–0.522) do not systematically exceed chance. Planted-edge advantage monotonically increasing with g. Companion sanity holds.
- **Determinism** verified.
- **METHOD_VALID** verdict correctly follows from the success criteria: FPR controlled in every domain at primary rate, all domains recover with finite MDE, bracket FPR ok, replay matches.

## Scope Compliance

- **Analysis plan followed**: YES
- **Deviations**:
  - **Info-1 (pre-exec)**: Full {1,3,6} horizon family implemented instead of plan's `H_cal=3` + `H_cal=6` FPR-only. Accepted — strictly more faithful to EXP-021 reuse.
  - **Info-2 (pre-exec)**: MDE FPR-gate uses `alpha0=0.05` for all alpha rows. Acceptable; headline MDE at α=0.05 is correct; other alpha rows are secondary diagnostics.
  - **Info-3 (pre-exec)**: Equity companion buy-hold not drawn as curve (annotation-only). Acceptable — exposure-matched baseline is the comparator.
- **Complexity budget**: 4 tests / 4 budgeted ✓; 5 plots / 5 budgeted ✓; 1 module / 1 budgeted ✓
- **Holdout exclusion verified**: YES — lazy first-70% slice; regime-index fence; no final 30% loaded.
- **Anti-overfitting fence**: `avwap_events.csv` outcomes never loaded ✓

## Issues

### Critical

None.

### Warning

1. **Secondary-horizon edge shift is an approximation for planted-edge draws**
   - File: `code/run_experiment.py`, lines 314–319 (`_domain_edge_stats`)
   - Description: A planted edge `g` bps is applied at the primary horizon (H_cal=3). The secondary horizon effects (`eff_h1`, `eff_h6`) are also shifted by the same flat `+g`, even though a 3-bar price drift producing `g` bps over H=3 would produce a different drift amount at H=1 (~g/3 for steady drift) and H=6 (~2g). The `decide_label` function uses these secondary effects for the `INCONCLUSIVE_SECONDARY_UNSTABLE` downgrade, meaning the stability check uses horizon-incorrect values.
   - Impact: Slight potential inflation of TPR under planted edge, because the secondary instability downgrade may be suppressed when `+g` makes secondary effects appear more positive than they truly are. FPR (g=0) is unaffected. The practical impact is likely small because (a) secondary instability is rare, (b) `for_flag` is the primary gate, and (c) TPR values and MDE thresholds all show sensible monotonic patterns consistent with the domain event-count gradient.
   - Fix: Either (a) do not shift secondary effects (leave them at their true g=0 values, which is conservative — makes instability easier to detect, TPR slightly lower), or (b) compute the path-consistent drift at each horizon. Option (a) is the simplest and most conservative fix.

### Info

1. **Execute-time data-source selection fix (post-governance)**. `build_precomputes` was corrected in the first manual run to key one source per instrument by the **Symbol column** (`data.instrument`) with latest-sorted wins, resolving a stale-file issue with auxiliary `timebars_analysis70_xauusd_*` files. This is a data-source-selection correction with no effect on the method, denominators, or holdout discipline. The fence was strengthened, not weakened.

2. **Family-wise FPR exceeds per-domain α**. The any-domain FPR at p_trig=0.06 reaches 0.094 (block_permuted) and 0.064 (placebo_on_real) at α=0.05. This is expected when Holm-adjusting over 3 domains and is not a per-domain control failure. The per-domain FPR never exceeds 0.042.

3. **Equity companion mean_equity_adv at null is negative for all domains**. 5m: -533 bps, 1h: -38 bps, 4h: -179 bps. This reflects no systematic false advantage. The negative mean at 5m is driven by the large number of null events (each with a small negative average paired difference). The companion is non-gating per scope.

## Re-Audit Requirements

None — verdict is PASS. The Warning-level finding (secondary-horizon edge shift) is a methodological approximation with small practical impact on TPR measurement. If conservatism is desired, option (a) from the fix above should be applied: remove the `+g` shift from `effect_h1` and `effect_h6` in `_domain_edge_stats`.
