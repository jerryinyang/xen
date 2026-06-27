# Audit Report: Experiment EXP-051

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 3

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Formulas, joins, groupings, lag logic, and index arithmetic verified correct. |
| `code/run_experiment.py` | Edge cases | PASS | Zero-move cells, zero-retained (ρ=null, f=0), degenerate moves, empty runs/haramis handled. Length-consistency guard at `_form_stats:254`. |
| `code/run_experiment.py` | Type safety | PASS | `numpy.quantile(..., method="linear")` pinned explicitly; `float64` throughout; `np.random.SeedSequence` spawn per (cell,form). |
| `code/run_experiment.py` | NaN handling | PASS | Bootstrap ρ* = NaN dropped with disclosed count; `f = 0` (not NaN) when zero-retained; overlap denominators guarded. |
| `code/run_experiment.py` | Holdout exclusion | PASS | F01 prefix: `train_rows = int(int(total * 0.7) * 0.7)` file-order rows; `scan_parquet(...).slice(0, train_rows)`; full file never sorted/collected; every timestamp fenced to `≤ train_end_ts`. |
| `code/run_experiment.py` | Loader ordering | PASS | F01 loader: no pre-sort (deliberate EXP-043/048/050 convention); hard-fail if slice is non-chronological; `CloseTime` ordering used for aggregation/ZigZag/move sequence. |
| `code/run_experiment.py` | Memory/performance | PASS | Lazy `scan_parquet` with column projection; bounded per-cell memory; bootstrap batched via `BOOT_MAX_ELEMS`. |
| `code/run_experiment.py` | Safe optimization | PASS | `strong_stat_decisions` sequential loop (variable-window quantile cannot be trivially vectorised); `find_impulse_runs` vectorised via cumsum (causally equivalent); `map_runs_to_moves` uses `searchsorted` on completed segmentation. No sample-membership/denominator/ordering changes. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` over the instrument outer loop (~17 iterations × 6 domains × 2 passes). |
| `code/run_experiment.py` | Logging/output | PASS | Concise summary with verdict, form-level material counts, non-deterministic/invariant failures if any. |
| `code/run_experiment.py` | Organization/import side effects | PASS | Imports are block-separated (`path setup`, `xen.*`, `constants`); no output directories created at import time (`mkdir` in `run()` only). |
| `code/run_experiment.py` | Plot data reuse | PASS | Four plots built from the bounded per-cell summary dict (no reloads from Parquet). |
| `code/run_experiment.py` | Docstrings | PASS | Public functions have useful docstrings; threshold constants are D0-frozen named globals. |
| `python/src/xen/strong_move.py` | Correctness | PASS | Type-7 quantile (`_quantile_sorted`), MAD (raw, no 1.4826), rolling window logic (`mags[lo:i]` strictly prior), HA bar qualification, 3-bar run detection, run→move interval mapping all verified correct. |
| `python/src/xen/strong_move.py` | Edge cases | PASS | Zero-length arrays, short HA frames (no runs possible), empty moves, degenerate moves retained in window but excluded by caller. |
| `python/src/xen/strong_move.py` | NaN handling | PASS | No NaN in magnitude series (vectorised `np.abs(end - start)`); `median_body` uses `rolling_median` with `min_periods` → `is_not_null` check. |
| `python/src/xen/strong_move.py` | Docstrings | PASS | Module docstring with causality discipline note; per-function docstrings with parameter/return specs. |

## Numerical Validation

### Spot Checks

**BTCUSD-5m stat_p75:**
- `med_all = 185.42`, `med_ret = 357.71` → `ρ = 357.71 / 185.42 = 1.92919` → reported `1.9291877898823668` ✓
- `n_defined = 31427`, `n_retained = 8757` → `f = 8757/31427 = 0.27865` → reported `0.27864575046934165` ✓
- Block bootstrap CI: `(1.884, 1.982)` spans ρ=1.93; `block_len = max(1, round(31427^(1/3))) = 32` → reported `32` ✓

**BTCUSD-5m ha_primary:**
- `med_all = 185.39`, `med_ret = 328.58` → `ρ = 328.58/185.39 = 1.77240` → reported `1.7723987270079105` ✓
- `n_defined = 31431`, `n_retained = 6018` → `f = 6018/31431 = 0.19147` → reported `0.19146702300276797` ✓

**DE30-4h stat_p75 (smallest n):**
- `n_defined = 331`, `block_len = max(1, round(331^(1/3))) = max(1, round(6.92)) = 7` → reported `7` ✓

**Warmup NO_DECISION (BTCUSD-5m):**
- `n_moves = 31432`, `n_degenerate = 1`, `n_no_decision_stat = 4` → first 5 moves, one is degenerate → `5 - 1 = 4` ✓
- `n_no_decision_ha = 0` → all moves past HA run-warmup boundary ✓

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| stat_p75 ρ | ≥ 1.5 for MATERIAL cells | [1.719, 2.187] (all 99 MATERIAL) | YES |
| stat_p75 f | [0.10, 0.50] for MATERIAL cells | [0.250, 0.320] (all 99 in band) | YES |
| ha_primary ρ | ≥ 1.5 for MATERIAL cells | [1.620, 2.081] (all 99 MATERIAL) | YES |
| ha_primary f | [0.10, 0.50] for MATERIAL cells | [0.151, 0.237] (all 99 in band) | YES |
| n_defined | ≥ 30 (power floor) | [331, 31431] (all 99 reportable) | YES |
| Block length `L` | max(1, round(n^(1/3))) | [7, 32] | YES |
| Bootstrap NaN dropped | ≥ 0 | 0 (all finite) | YES |
| Degenerate moves | ≥ 0, disclosed | 0-1 per cell | YES |
| COVERAGE_EXCLUDED | 3 cells: US500-4h, JP225-2h, JP225-4h | 3 cells confirmed | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| stat_p75 ρ median (99 cells) | 1.92 | YES | p75 threshold selects top ~25% of moves; median ~1.9× total median is plausible (heavy-tailed magnitude distribution) |
| ha_primary ρ median (99 cells) | 1.80 | YES | HA impulse runs select even larger moves (~1.8×) but from a smaller retained fraction (~20%) |
| stat_p75 f median (99 cells) | 0.27 | YES | Slightly above 0.25 due to ties (`>=`) and variable window; entirely expected |
| ha_primary f median (99 cells) | 0.20 | YES | HA impulse runs (~3 consecutive bars within 20-bar lookback) naturally retain ~20% of moves |
| p75↔MAD flips | 0 | YES | Both thresholds select similar populations; neither is `f`-constrained |
| primary↔sensitivity flips | 0 | YES | Direction-match constraint rarely eliminates an already-qualifying run at these thresholds |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| MBB bootstrap CI | Approximate stationarity at block scale | PARTIAL | Non-binding; disclosed as colour only. Block bootstrap is robust to mild non-stationarity at the block scale (~7–32 moves). |
| P10 point criterion | None on distribution shape | YES | Rank-based (median, percentile). No distributional assumptions. |
| P10 retained-fraction band | Predeclared [0.10, 0.50] | YES | All 99 cells for both binding forms satisfy this band. |
| Moving-block block length | L = max(1, round(n^(1/3))) | YES | Standard MBB rate; consistently applied across all cells. |

## Results Plausibility

- **ρ values (1.62–2.19)** are consistent with a strong-move filter selecting larger-than-median moves. For p75, ρ ≈ 1.9 is expected since the top quartile of a right-skewed magnitude distribution has median ~2× the full median. For HA-primary, the slightly lower ρ (~1.8) reflects that HA impulse runs identify a different (though also large) move subset.
- **f values**: stat_p75 f ≈ 0.27 (slightly above 0.25 due to ties) and ha_primary f ≈ 0.20 are in the expected range.
- **Cross-cell consistency**: All 99 member cells are MATERIAL for both binding forms — an extraordinarily consistent result that suggests the filters select genuinely larger moves across all instruments and domains. ρ and f show narrow IQRs (ρ: ~0.06-0.10, f: ~0.01-0.02 within each form).
- **DE30** has truncated history (train ends 2026-01-16) but still shows similar ρ/f ranges — the filter behaviour is robust to shorter history.
- **Bootstrap CIs** are narrow for large-n cells (BTCUSD-5m: ±0.05) and wider for small-n (DE30-4h: ±0.20), consistent with sampling variability.
- **Zero flips** between p75↔MAD and primary↔sensitivity — the disclosed alternatives agree exactly with binding forms on materiality, suggesting the threshold choice within each family does not change the qualitative conclusion.

## Scope Compliance

- Analysis plan followed: **YES**
- Deviations: **none**
- Complexity budget: 1 statistical test / 1 (MBB CI on ρ); 4 plots / 4 (STAT-ρ heatmap, HA-ρ heatmap, f small-multiple, materiality composition map); 1 new module / 1 (`strong_move.py`)
- Holdout exclusion verified: **YES** (F01 prefix loader; full file never sorted/collected; every timestamp fenced to `CloseTime ≤ train_end_ts`)
- Undocumented extra analyses: **none detected**

## Issues

### Critical

None.

### Warning

None.

### Info

1. **F01 file-order convention (non-chronological split).**
   - Description: Like EXP-043/048/050, the loader uses file-order prefix (first `int(int(total*0.7)*0.7)` rows) rather than sorting by `CloseTime` before slicing. This is a deliberate divergence from the generic sort-before-slice loader, documented and pre-approved in the governance review (F05 disposition). The hard-fail on non-chronological slices catches gross corruption. For near-chronological files the first 49% by file order ≈ first 49% by clock order. No action required.

2. **`retained & defined` masking in `_form_stats`.**
   - Description: The per-form stats intentionally mask `retained = retained & defined` before computing P10 statistics. The comment explains this handles the edge case where a degenerate move (E=S, mag=0, excluded from the denominator) technically contains a HA impulse run. The invariant battery separately verifies that no **non-degenerate** move is retained outside the defined-decision set. The masking matches the scope denominator definition. No action required.

3. **DE30 truncated history.**
   - Description: DE30 broker 1-minute history ends 2026-01-16; `train_end_ts = 2024-06-28` (vs ~2024-08 to 2024-10 for other instruments). Disclosed in scope (`scope.md:210`), metadata (`run_metadata.json:677`), and CSV outputs. DE30 ρ/f values are within the cross-cell range and do not distort composition tallies. No action required.

## Re-Audit Requirements

None — **PASS** with 0 critical, 0 warnings, 3 info notes. The implementation is correct, deterministic, holdout-safe, and produces plausible outputs consistent with the predeclared scope and analysis plan. The experiment verdict `STRONG_FILTER_CHARACTERISATION_DELIVERED` is sound.
