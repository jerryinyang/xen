# Audit Report: Experiment EXP-039

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 1
- **Info Notes**: 3

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Implements scope.md and analysis-plan.md faithfully. All exit rules, containment, intersection populations, grid selection, and qualification logic match the predeclared design. |
| `code/run_experiment.py` | Edge cases | PASS | Empty cells/rows handled (write_rows empty-safe). Zero TRAIN bars raises ValueError. NaN/None propagated safely through bootstrap, power statement, qualification. Division by zero guarded in EURUSD share computation. Bootstrap returns NaN for empty subsets. |
| `code/run_experiment.py` | Type safety | PASS | Polars DataFrames throughout; explicit `int()`, `float()`, `bool()` casts; NumPy typed arrays for fire indices. |
| `code/run_experiment.py` | NaN handling | PASS | `np.isfinite()` guards in power statement fragility check and qualification; bootstrap returns `float("nan")` for empty frames; holding stats use None/nullable typed columns. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `load_analysis_data` loads only the analysis set (first 70% of total). Events filtered by `train_end_ts` (R1.3 1-minute-row convention). TEST events (trigger > train_cutoff_idx) never loaded. Global holdout (last 30% of total) never touched. |
| `code/run_experiment.py` | Loader ordering | PASS | `list_timebar_files` returns sorted paths. `load_analysis_data` sorts by `CloseTime` before slicing. Chronological ordering guaranteed before any TRAIN/TEST split. |
| `code/run_experiment.py` | Memory/performance | PASS | Processing per-file/per-instrument. Event evaluation loops 13 exits × ~2500 events = ~32K evaluations, each O(log n) or bounded scan. Bootstrap 1000 iterations on ~100-event cells. Long table (~7765 rows × 15 cols) materialized once. |
| `code/run_experiment.py` | Safe optimization | PASS | Fire index precomputation is vectorized but causally equivalent to sequential scan. HA recurrence is explicit sequential loop. Target-based rules scan bounded slices. `searchsorted` for first-fire-after. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` on rebuild domain bars, precompute fire indices, evaluate exits, screen statistics. |
| `code/run_experiment.py` | Logging/output | PASS | `configure_logging()` sets INFO level. Each major step logs completion. Failures raise `ValueError` with descriptive messages. |
| `code/run_experiment.py` | Organization/import side effects | PASS | Module-level constants, I/O helpers, integrity guards, then step functions, then `main()`. Output dirs created inside `main()` only (`ensure_output_dirs` at line 1046). `matplotlib.use("Agg")` at import time (required before pyplot import). |
| `code/run_experiment.py` | Plot data reuse | PASS | All 5 plots consume the already-computed `stats` list and `long` DataFrame. No additional data loading for visualisations. |
| `code/run_experiment.py` | Docstrings | PASS | All functions have docstrings. Module docstring (lines 1-30) describes purpose, key invariants, run command. |
| `src/xen/exit_rules.py` | Correctness | PASS | HA recurrence matches `xen.heiken_ashi_generator`. Harami, trailing, Last-X, target-based, and FH rules all implement scope definitions exactly. Bar-close semantics enforced. |
| `src/xen/exit_rules.py` | Edge cases | PASS | `n == 0` in HA trigger values. `n <= x` in Last-X returns empty. `UNRESOLVED` returned when no fire before `scan_end`. `last <= entry_idx` in target rules. `h_cap` time-stop at boundary edge. Direction validation. |
| `src/xen/exit_rules.py` | Docstrings | PASS | NumPy-style docstrings explaining parameters, returns, and edge behavior. |

## Numerical Validation

### Spot Checks

**Check 1: 4h E1 event-weighted pooled net**
```
net_EURUSD=-2.29, n=27  →  -2.29 × 27 = -61.83
net_USTEC=26.24, n=25   →  26.24 × 25 = 656.00
net_XAUUSD=21.51, n=34  →  21.51 × 34 = 731.34
Pooled = ( -61.83 + 656.00 + 731.34 ) / 86 = 1325.51 / 86 = 15.41 ✓
```

**Check 2: 4h E1 gap vs R_FH (better reference)**
```
gap = 15.4116 - 37.3144 = -21.9028 ✓
```

**Check 3: 4h R_FH pooled net (event-weighted)**
```
R_FH net_EURUSD=29.45, n=27
R_FH net_USTEC=63.73, n=25
R_FH net_XAUUSD=24.14, n=34
Pooled = (29.45×27 + 63.73×25 + 24.14×34) / 86 = 3209.3 / 86 = 37.31 ✓
```

**Check 4: R-BTC per-event max diff**
```
reconciliation.csv: max_abs_diff_bps = 0.0 ✓
```

**Check 5: R-FH(12) vs EXP-033 per-instrument nets**
```
BTCUSD: rebuilt=-33.809 vs exp033=-33.809, diff=2.1e-14 ✓
EURUSD: rebuilt=29.449 vs exp033=29.449, diff=0.0 ✓
USTEC: rebuilt=63.728 vs exp033=63.728, diff=1.4e-14 ✓
XAUUSD: rebuilt=24.139 vs exp033=24.139, diff=0.0 ✓
```

**Check 6: Grid selection — 1h E3**
```
E3(3): h1=3.65, h2=-10.52 → worst=-10.52
E3(5): h1=6.91, h2=-12.18 → worst=-12.18
E3(8): h1=6.26, h2=-7.98  → worst=-7.98
Selected: E3(8) (max-min worst-half) ✓
```

**Check 7: Grid selection — 4h E3**
```
E3(3): h1=66.26, h2=13.51 → worst=13.51
E3(5): h1=43.67, h2=21.44 → worst=21.44
E3(8): h1=31.70, h2=22.00 → worst=22.00
Selected: E3(8) (max-min worst-half) ✓
```

**Check 8: 1h E5(8) qualification — per-instrument positivity**
```
own_net_EURUSD=-4.50 (negative) → fails criterion (i) ✓
```

**Check 9: 4h E5(8) qualification — beats better reference**
```
gap = 11.30 - 37.31 = -26.01 (negative) → fails criterion (ii) ✓
```

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| Direction | {+1, -1} | {-1, +1} | YES |
| net_bps (1h candidates) | ℝ | [-6.07, -0.86] | YES (all negative on 1h, expected) |
| net_bps (4h candidates) | ℝ | [9.08, 39.89] | YES (range plausible for 4h AVWAP) |
| n_intersection (1h) | ≥ 0 | [442, 443] | YES |
| n_intersection (4h) | ≥ 0 | 86 for all | YES |
| Mean holding bars (4h) | ≥ 1 | [3.3, 20.8] | YES |
| Bootstrap SE (4h) | ≥ 0 | [7.2, 30.0] | YES (consistent with ~90-event cells) |
| Resolved fraction | [0, 1] | 1.0 for 1h; 1.0 for 4h | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| R-FH(12) 4h pooled net | +37.3 bps | YES | Consistent with EXP-033/037; strong positive on 4h |
| R-BTC 4h pooled net | +7.2 bps | YES | Consistent with EXP-030/022 TRAIN stratum |
| R-BTC 1h pooled net | -2.5 bps | YES | Near-zero/negative on 1h as expected |
| 4h E3(8) gap SE | 18.2 bps | YES | Large SE due to ~86 events ÷ 3 instruments ÷ 2 directions ≈ 14 per stratum; bootstrap correctly captures uncertainty |
| 4h E2 gap SE | 10.6 bps | YES | Moderate uncertainty; HA trailing has no parameters but wider dispersion |
| 1h all candidates gap | all negative or near-zero | YES | 1h is structurally weak for this substrate; R-BTC near zero makes beating it unlikely |
| Power fragility flags | 4 cells fragile | YES | Consistent with scope expectation that most 1h and some 4h cells lack stable selection signal |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| R-BTC reconciliation | Rebuilt event lifetimes match EXP-022 CSV within 0.01 bps | YES | max_abs_diff_bps = 0.0 (exact match) |
| R-FH(12) reconciliation | Per-instrument FH(12) net matches EXP-033 freeze within 0.01 bps | YES | max diff = 2.1e-14 bps |
| Domain rebuild | Domain bar counts match EXP-020 metadata | YES | validate_analysis_metadata passed |
| Frozen inference tail | EXP-027 function source hash matches pinned hash | YES | Hash `e50873d12a9f68d9` verified at runtime |
| Financing module | Self-check cases pass | YES | `verify_financing()` called at line 1051 |
| TRAIN boundary | `train_end_ts` from R1.3 1-minute row convention | YES | Uses `load_analysis_data` which computes analysis 70%, then TRAIN 70% |
| Deterministic bootstrap | Identical seed produces identical bootstrap statistics | YES | determinism_replay: max_drift = 0.0 |

## Results Plausibility

The FLAT outcome is correct and well-supported:

- **4h**: All candidates fail criterion (ii) — none beat R-FH(12) at +37.3 bps. The best-performing candidate (E2 at +31.9 bps) is ~5.4 bps short. This is consistent with the scope's expectation: "beating R-FH(12) (TRAIN grid max +45.79 bps) is a high bar — most candidates failing it is the honest prior."

- **1h**: All candidates produce negative pooled nets (range -6.1 to -0.9 bps), failing criterion (i). This aligns with the scope: "on 1h, any exit with all-instrument-positive net would already be new information."

- EURUSD disclosure columns confirm that EURUSD contribution fractions are within reasonable ranges (0.20–0.52 on 4h, 0.31–2.18 on 1h). The anomalous 2.18 on 1h E3(8) occurs because EURUSD net is positive while other instruments suppress the pooled net to near-zero, inflating the share fraction — this is correctly disclosed for desk-review.

- The power statement correctly identifies 4 of 10 evaluated cells as fragile (|gap| < SE), consistent with the limited event counts (~86 per 4h cell) and moderate dispersion.

## Scope Compliance

- **Analysis plan followed**: YES
- **TRAIN only**: YES — first 70% of analysis set (49% of total). No TEST or holdout contact.
- **Boundary containment**: YES — events unresolved at `train_end_ts` excluded; exclusion counts disclosed (0 for all cells — all events resolve within boundary under all candidates).
- **Intersection populations**: YES — all candidate-vs-reference gaps are same-events comparisons.
- **Real-price outcome discipline**: YES — all P&L uses `log_close` (real Close). HA values trigger-only in E1/E2.
- **Power statement ordering**: YES — `write_power_statement` called at line 1064, `qualify` at line 1065.
- **Grid selection before qualification**: YES — `select_grid_points` at line 1063 before `qualify` at line 1065.
- **`qualifying_set.json` written once before plots**: YES — written at lines 1099-1100, plots at lines 1126-1130.
- **Global holdout exclusion**: YES — the final 30% of every dataset is never loaded.
- **Deviations from analysis plan**: 
  - The analysis-plan mentions a "write-timestamp ordering assertion" (mtime check) for the power statement. The code uses sequential call ordering instead, which is functionally equivalent. Minor.
  - The FH(12) reconciliation uses EXP-033's bar-index containment rule (`floor(0.7 * n_bars)`) rather than the R1.3 timestamp convention. This is explicitly documented as an anchor-only rule and the reconciliation passed. Acceptable.
- **Complexity budget**: 0 binding tests / 0 budget ✓, 5 plots / 5 ✓, 2 modules / 2 ✓
- **Screen outcome**: FLAT (0 qualifiers) — correctly recorded in `run_metadata.json` and `qualifying_set.json`.

## Issues

### Critical

None.

### Warning

1. **Determinism replay checks only one cell's bootstrap drift, not full CSV byte-identity**
   - File: `code/run_experiment.py`, lines 877-887
   - Description: The analysis plan states "full same-seed replay of one domain must reproduce all binding CSVs byte-identically." The code replays only 4h/E4's bootstrap statistics and checks numerical drift (≤ 1e-12). It does not verify byte-identical CSV output via a full rerun comparison. Since the bootstrap is the only stochastic component and is seeded, practical determinism is assured, but the literal plan requirement is not met.
   - Impact: Low. No actual non-determinism observed (max_drift = 0.0). Any future non-determinism in non-bootstrap paths would be silently undetected.
   - Fix: Add a second-pass rerun that recomputes `screen_statistics` for one domain and compares the output CSV byte-for-byte against the persisted version.

### Info

1. **FH(12) reconciliation uses EXP-033 bar-index containment, not R1.3 timestamp convention**
   - File: `code/run_experiment.py`, lines 370-373
   - Description: The FH reproduction anchor uses `np.floor(0.7 * n_bars)` as cutoff and double-filters events (`start_idx + 24 <= cut033` AND `completion_idx <= cut033`). This differs from the main experiment's `train_end_ts` timestamp convention (R1.3). The reconciliation passed (max diff 2.1e-14 bps), confirming equivalence for FH(12) on 4h, but the dual-containment approach could mask a subtle discrepancy.
   - Impact: None (passed). Documented as anchor-only.

2. **EURUSD share computation returns None when pooled net is exactly 0**
   - File: `code/run_experiment.py`, lines 669-675
   - Description: The EURUSD contribution share formula divides by `pooled_net_bps`, guarded by `pooled != 0.0`. For the rare case where the event-weighted pooled net is exactly 0.0 bps (impossible in this run), the share is recorded as None. This is appropriate (division-by-zero avoidance), but the guard could be `abs(pooled) < 1e-12` for numerical stability.
   - Impact: None in practice (all pooled nets non-zero in this run).

3. **No mtime-based power-statement ordering assertion**
   - File: `code/run_experiment.py`, lines 718-740
   - Description: The analysis plan specifies "persisted to `power_statement.csv` with a write-timestamp ordering assertion (power file mtime < qualification read)." The code uses sequential function call ordering (`write_power_statement` at line 1064, `qualify` at line 1065) which guarantees ordering in the same process but does not assert filesystem timestamps.
   - Impact: None. The ordering guarantee holds within a single run.

## Re-Audit Requirements

Not applicable — PASS verdict with no critical issues.
