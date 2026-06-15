# Audit Report: Experiment EXP-049

Phase 014-A · `CF-HA-HARAMI-001` / HYP-002 · 3-Barrier Capture Readiness & Gross Capture Rate

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 4

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Scope, plan, and D0 constants implemented verbatim; barrier construction, resolution, and bootstrap match the spec. Determinism replay compares full inference tuples (r, CI bounds, degenerate frac, block length), not just r. |
| `code/run_experiment.py` | Edge cases | PASS | Zero-move cells → `_empty_geometry()` (r=None, resolved=0, NOT_VIABLE_BY_POWER); `M=0` excluded with record; warmup events excluded; G2 degenerate (`fav_dist<=0`) excluded and disclosed; degenerate bootstrap resamples discarded and counted; `resolved<30` → flagged, never `0/0`. |
| `code/run_experiment.py` | Type safety | PASS | Type hints on all public functions; NumPy/Polars types consistent; `GeometryResult` is a frozen dataclass. |
| `code/run_experiment.py` | NaN handling | PASS | Explicit `None` for undefined r/CI fields when resolved==0; `np.nan` never silently computed. |
| `code/run_experiment.py` | Holdout exclusion | PASS | F01 prefix loader: reads row count from Parquet metadata, then `slice(0, train_rows)` — never reads TEST or final-30% holdout. `train_rows = int(int(total_rows*0.7)*0.7)` = first 49%. Full file never sorted or collected. |
| `code/run_experiment.py` | Loader ordering | PASS | `CloseTime` sort asserted (`.is_sorted()`) on the TRAIN slice after collection, confirming file-order is chronological. |
| `code/run_experiment.py` | Memory/performance | PASS | Lazy scan with column projection; per-cell bounded memory (domain frames not retained across cells); 4 plots from summaries (no reloads); bootstrap batched at 2,000. |
| `code/run_experiment.py` | Safe optimization | PASS | ZigZag (causal streaming) and first-touch scan (sequential per-event loop) stay explicit bounded loops — not vectorized into unsafe batch operations. Bootstrap index math is vectorized but is summary statistics, not causal logic. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` on instrument outer loop; helpers return data, not print. |
| `code/run_experiment.py` | Logging/output | PASS | `logging` with concise `main()` summary; 8-line output appears on stdout. |
| `code/run_experiment.py` | Organization/import side effects | PASS | Imports → path setup → constants → I/O helpers → computation → plotting → orchestration → `main()`. `RESULTS_DIR.mkdir()` inside `run()`, not at import. VAL-001-style sectioning with `# ----` separators. |
| `code/run_experiment.py` | Plot data reuse | PASS | Plots built from the collected per-cell `records` list (in-memory summaries); no reloads or re-aggregation. |
| `code/run_experiment.py` | Docstrings | PASS | Module docstring and all public functions have Google-style docstrings with Parameters/Returns. |
| `python/src/xen/capture_barriers.py` | Correctness | PASS | Barrier formulas match scope §104-128 exactly. `_scan_window` checks ADV first (same-bar double-touch → ADVERSE, scope §137). MBB block length = `round(m^(1/3))` per analysis-plan §110. Block bootstrap batches at 2,000 for bounded memory. `confirm_indices` uses `searchsorted` with exact-match guard. |
| `python/src/xen/capture_barriers.py` | Edge cases | PASS | Zero-magnitude move (m0) excluded; warmup (<5 trailing moves) excluded; degenerate resamples discarded; empty-classes `GeometryResult` handled in callers. |
| `python/src/xen/capture_barriers.py` | Type safety | PASS | Type hints on all public functions; frozen dataclass for GeometryResult. |

### Numerical Validation

### Spot Check: BTCUSD-5m G1 capture rate

- `g1_fav = 10880`, `g1_adv = 11292` → `resolved = 22172`
- `r = 10880 / 22172 = 0.4907090023...`
- CSV reports: `0.4907090023453004` → **exact match**
- `ci_low_1s = 0.486166...` — one-sided 95% CI below the 0.50 null
- Block length = `round(31426^(1/3)) = round(31.6) = 32` → CSV `g1_block_len = 32` ✓
- Degenerate fraction = 0.0 ✓
- Bootstrapped CI replicates consistently below 0.50, which is expected given r ≈ 0.491 and the serial-dependence-aware MBB.

### Spot Check: AUDJPY-4h G1

- `g1_fav = 158`, `g1_adv = 161` → `resolved = 319`
- `r = 158 / 319 = 0.4952978...`
- CSV reports: `0.4952978056426332` → **exact match**
- Block length = `round(444^(1/3)) = round(7.63) = 8` → CSV `g1_block_len = 8` ✓

### Spot Check: EURUSD-5m G2 degeneracy

- `g2_defined = 9922`, `g2_degenerate_excluded = 14598`, denominator = 9922+14598 = 24520 = `g1_defined` ✓
- `g2_degenerate_frac = 14598/24520 = 0.59535...` → CSV `0.5953507340946166` ✓
- This ~59.5% G2 degeneracy rate means entry is already at/through the midpoint for most events — correctly disclosed per scope §112.

### Range checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| `g1_r` | [0, 1] or None | [0.4545, 0.5343] or None (excluded cells) | YES |
| `g1_resolved` | ≥ 0 | [128, 22172] | YES |
| `g1_boot_degenerate_frac` | [0, 1] | 0.0 everywhere | YES |
| `g1_ci_low_1s` | [0, 1] or None | [0.4106, 0.4957] | YES |
| `g1_defined` | ≥ 0 | [330, 31426] | YES |
| `n_moves` | ≥ 0 | [336, 31432] | YES |

### Statistical Sanity

| Statistic | Value | Sensible? | Notes |
|-----------|-------|-----------|-------|
| G1 r across all cells | 0.4545–0.5343 | YES | Clusters around the 0.50 null, as expected for symmetric 1:1 barriers on a near-random-walk substrate. No cell exceeds the 0.55 viability bar. |
| G2 r across all cells | 0.3257–0.4389 | YES | Lower than G1 because G2 excludes all degeneracies (midpoint-level crossings), leaving events where reversal must retrace through a tighter window. |
| G2 degenerate fraction | 0.520–0.600 | YES | Most events have the entry bar close already at/through the midpoint — expected when the reference move is small relative to the ATR scale. |
| `g1_ci_low_1s` relative to r | all `ci_low_1s < r` | YES | Bootstrap CI always below the point estimate (one-sided 95% = 5th percentile). |
| `n_event_median` | 6.0 for 96/99 cells, 7.0 for 3 cells | YES | Adaptive cap floor (6 bars) is binding for most cells. 3 cells (GBPUSD-4h, USDCHF-4h, AUDUSD-4h) reach median 7.0 — longer confirmation-to-confirmation durations at 4h. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| MBB for `r` | Approximate stationarity within a cell's TRAIN span at the block scale | YES | TRAIN spans ~18-24 months of 5m-4h data; moderate non-stationarity is acceptable for MBB with block lengths of 7-32. |
| MBB for `r` | No independence required | YES | MBB is specifically chosen because events are serially dependent. |
| Ratio `r` | Symmetric barriers → null = 0.50 | YES | G1 is symmetric by construction (1:1 fav:adv distance). G2 shares the same adverse distance. |

## Results Plausibility

All outputs are within expected ranges:
- G1 `r` clusters tightly around 0.50 (null) with no cell crossing 0.55 — consistent with symmetric 1:1 barriers on a statistically flat substrate.
- G2 `r` is systematically lower (0.33–0.44) because degenerate events (entry at/through midpoint) are excluded, removing the cases where a favourable bias would be strongest.
- Time-cap censoring fraction ~24-33% — the adaptive floor of 6 bars cuts a predictable fraction; higher at slower domains.
- Data-truncation censoring is below 0.5% everywhere — the TRAIN fence barely bites.
- VERDICT is `CAPTURE_READINESS_DELIVERED` with zero invariant failures and perfect determinism — the barrier system is mechanically sound.
- Composition: 0 VIABLE cells on either geometry across 99 member cells — clean negative.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none detected
- Complexity budget: 1 test / 4 plots / 1 module — exactly as budgeted
- Holdout exclusion verified: YES — F01 prefix loader; full 30% global holdout and nested TEST stratum never read
- Real-price discipline: YES — all barriers/excursions on real domain OHLC; no HA/Renko price enters any metric
- Determinism: PASS — second full-pass replay confirms frame-identical output

## Issues

### Critical

None.

### Warning

None.

### Info

1. **All 99 member cells are BELOW_R on G1 — capture geometry CHARACTERISED_NOT_VIABLE per P12.**
   - File: `results/composition_readout.json`
   - Description: G1 `composition_met = false` (0 VIABLE cells). G2 also 0 VIABLE. Every member cell has `r < 0.55`. The barrier system is construction-valid (CAPTURE_READINESS_DELIVERED) but the favourable-before-adverse rate does not exceed 0.55 in any cell under the default 50% barrier distance.
   - Impact: Readout is consistent with design §10 CHARACTERISED_NOT_VIABLE. The G1 desk adjudication makes the routing call; this audit does not change it.

2. **G2 degeneracy rate is 52-60% across all cells — correctly disclosed.**
   - File: `results/capture_rate_secondary.csv`
   - Description: Most events have entry already at/through the move midpoint, correctly excluded from G2 per scope §112. Degeneracy fractions match `g2_degenerate_excluded / (g2_defined + g2_degenerate_excluded)`.
   - Impact: G2 is inherently under-powered relative to G1. The predeclared G1-primary designation (info note 3 of pre-execution review) is correct.

3. **Adaptive P4 time cap binds at the `THIRD_BARRIER_FLOOR=6` for 96/99 cells.**
   - File: `results/censoring_disclosure.csv`, column `n_event_median`
   - Description: Median N_event is 6.0 for 96 cells; only GBPUSD-4h, USDCHF-4h, and AUDUSD-4h reach 7.0. The trailing-duration median mostly falls below the floor, so the cap defaults to 6.
   - Impact: Time-cap censoring rates (24-33%) are driven wholly by the floor, not adaptive variation. The `/THIRD-TIME` branch (k/window/floor sensitivity) would be needed to assess this.

4. **Zero bootstrap degeneracy across all cells.**
   - File: `results/capture_rate_map.csv`, column `g1_boot_degenerate_frac`
   - Description: Every cell reports 0.0 degenerate fraction. `resolved ≥ 128` in every member cell; MBB with 10,000 draws never drew an all-unresolved resample.
   - Impact: No bootstrap instability at the achieved power levels. The 30-event floor (P12) is well clear of zero for all cells.

## Re-Audit Requirements

None. All checks pass with 0 critical issues and 0 warnings.
