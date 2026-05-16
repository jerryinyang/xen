# Audit Report: Experiment EXP-006

## Summary

- **Verdict**: CONDITIONAL PASS
- **Critical Issues**: 0
- **Warnings**: 1
- **Info Notes**: 2

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| run_experiment.py | Correctness | PASS | HA formulas match architecture.md spec. Compression ratios computed as `1 - ha/real`. |
| run_experiment.py | Edge cases | PASS | Bootstrap guards against insufficient data (line 219), undefined compression (line 229), regime insufficient data (line 374). |
| run_experiment.py | Type hints | PASS | All public functions have parameter and return type hints. |
| run_experiment.py | NaN handling | PASS | `rolling_std` with `min_periods=window` produces explicit nulls; regime labels null for calibration period; final filter drops null returns (lines 316-319). |
| run_experiment.py | Holdout exclusion | PASS | `load_and_holdout()` uses lazy scan, sorts by CloseTime, slices first 70% before collect (lines 83-86). Holdout never materialized. |
| run_experiment.py | Loader ordering | PASS | Lazy `scan_parquet` → column select → sort → slice → collect. No full-dataset collection. |
| run_experiment.py | Memory/performance | PASS | Column projection in scan (line 83); box plot subsamples to 20,000 (line 543); paired window plot uses 500-bar slice (line 434). |
| run_experiment.py | Logging/output | PASS | Concise per-instrument progress with key metrics summary (lines 711-716). |
| run_experiment.py | Organization/import side effects | PASS | Imports grouped (stdlib/third-party/local); `sns.set_theme` at module level is cosmetic only; `mkdir` calls in `main()` (lines 689-690). |
| run_experiment.py | Plot data reuse | PASS | `analyse_instrument` returns `plot_frame` bounded to 5 columns; no re-loading for plots. |
| run_experiment.py | Docstrings | PASS | All functions have docstrings with Parameters and Returns sections. |

## Numerical Validation

### Spot Checks

**EURUSD volatility compression:**
```
vol_real = 0.0001276603541437899
vol_ha   = 0.0000952979169968129
compression = 1 - vol_ha/vol_real = 1 - 0.7464958 = 0.2535042
Result: 0.2535042 ✓ (matches point_estimate)
```

**EURUSD median absolute return compression:**
```
mad_real = 4.672176721251531e-05
mad_ha   = 3.727935283477646e-05
compression = 1 - mad_ha/mad_real = 1 - 0.7979012 = 0.2020988
Result: 0.2020988 ✓ (matches point_estimate)
```

**BTCUSD volatility compression:**
```
vol_real = 0.0007502210857059131
vol_ha   = 0.0005560792075467911
compression = 1 - 0.7412204 = 0.2587796
Result: 0.2587796 ✓ (matches point_estimate)
```

**USTEC median absolute return compression:**
```
mad_real = 0.00010804193265734341
mad_ha   = 0.00008034336858564473
compression = 1 - 0.7436314 = 0.2563686
Result: 0.2563686 ✓ (matches point_estimate)
```

**Regime-stratified spot check (EURUSD High regime):**
```
vol_real = 0.00020624418734124529
vol_ha   = 0.00015495152328735864
compression = 1 - 0.7513019 = 0.2486981
```
High regime compression (0.249) is slightly below aggregate (0.254), consistent with HA smoothing being relatively less effective at higher volatility.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| Direction | {+1, -1} | Not directly validated (used internally by HA generator) | N/A |
| RealClose returns | Small values (~1e-6 to 1e-3 for 1-min) | EURUSD vol 1.28e-4, BTCUSD vol 7.50e-4 | YES |
| n_bars | > 0 | 830K-1.09M per instrument | YES |
| Compression ratios | [0, 1] for compression | 0.20-0.27 (vol), 0.20-0.27 (MAD) | YES |
| Bootstrap CIs | Contain point estimate | All CIs contain point estimates | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| EURUSD vol compression CI | [0.247, 0.259] | YES | Tight CI, n=872K bars, block bootstrap n=1000 |
| BTCUSD MAD compression CI | [0.268, 0.272] | YES | Very tight CI, largest sample (1.09M bars) |
| Bootstrap CI width | ~0.01-0.012 | YES | Consistent with large sample sizes |
| All 4 instruments vol compression | 0.254-0.260 | YES | Remarkably consistent across instruments |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Block bootstrap | Temporal clustering captured by block size | YES | Block size 100 bars (~100 min) reasonable for 1-min volatility clustering |
| Rolling volatility (30-bar window) | Window captures local volatility state | YES | 30 minutes is standard short-term vol window |
| Tercile regime classification | Three regimes sufficient | YES | Standard approach; scope specifies low/medium/high |
| HA generation deterministic | Same input → same output | YES | `generate_heiken_ashi` is a pure sequential function with no randomness |
| Compression ratio formula | `1 - ha/real` meaningful distortion metric | YES | Directly quantifies relative reduction |

## Results Plausibility

Results are plausible and internally consistent:
- HA consistently compresses volatility by ~25-26% across all 4 instruments — this is expected given HA's averaging formula.
- HA mean range is **higher** than real mean range on all instruments (e.g., EURUSD: 0.0163 vs 0.0131). This is also expected: HAClose is an average of OHLC, so HA candles can have wider apparent ranges even though close-to-close changes are smoothed.
- Direction change frequency is substantially lower for HA (0.37-0.40) vs real (0.51-0.57), consistent with HA's trend-smoothing property.
- Bootstrap CIs are tight due to very large sample sizes (830K-1.09M bars per instrument).
- Compression is consistent across volatility regimes, with slightly lower compression in High regimes.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: None in code; however, regime calibration uses 70% of analysis set rather than the train segment (first 70% of analysis set) — see Warning 1.
- Complexity budget: 2 tests / 2, 4 plots / 4, 1 module / 1
- Holdout exclusion verified: YES

## Synthetic Price Discipline

- `ha_return` computed from `HAClose` (line 303-305): **Authorized** — scope explicitly permits HA returns for distortion diagnostics only.
- `real_return` computed from `RealClose` (line 300-302): **Correct** — uses real prices.
- No strategy P&L, signal validation, or tradable-return metric derived from HA prices: **Verified**.
- All real-return comparisons use `RealOpen/RealHigh/RealLow/RealClose`: **Verified**.
- Conclusions framed as synthetic-price distortion, not improved risk: **Verified** (scope enforces this).

## Issues

### Critical

None.

### Warning

1. **Regime calibration segment mismatch**
   - File: `python/experiments/EXP-006/code/run_experiment.py`, lines 120-124
   - Description: `REGIME_CALIBRATION_FRACTION = 0.7` calibrates tercile thresholds on 70% of the **analysis set**. The scope states: *"thresholds calibrated on the train segment and applied only to the later evaluation segment."* The train segment is the first 70% of the analysis set (i.e., 49% of the full dataset). The code uses 70% of the analysis set, meaning calibration extends further into the data than the scope specifies.
   - Impact: Regime thresholds are calibrated on a slightly larger segment than specified. Since HA distortion is relatively stable across regimes (heatmap shows consistent compression), this is unlikely to materially change conclusions. The evaluation segment starts later than intended, so fewer rows receive regime labels.
   - Fix: Either (a) change `REGIME_CALIBRATION_FRACTION` to `0.7 * 0.7 = 0.49` to calibrate on the train segment, or (b) update the scope to match the code's behavior. Given the small practical impact, option (b) may be preferable.

### Info

1. **Diagnostic HA returns** — Consistent with pre-execution review Info note 1. HA returns are computed strictly for distortion measurement. No strategy P&L uses HA prices. If future experiments repurpose this code for strategy evaluation, HA-return paths must be removed or gated.

2. **`sns.set_theme` at module level** — `seaborn.set_theme(style="whitegrid")` runs at import time (line 44). This is a cosmetic side effect with no data or filesystem impact, but technically violates the "no import-time side effects" convention. Moving it into `main()` or a plot-initialization function would be cleaner.

## Re-Audit Requirements

If Warning 1 is addressed by changing the calibration fraction, verify:
1. `REGIME_CALIBRATION_FRACTION` changed to 0.49 (or scope updated).
2. Regime row counts change (fewer labelled rows since evaluation segment shrinks).
3. Regime-stratified compression ratios remain qualitatively consistent.
4. Re-run experiment and confirm distortion_metrics.json updates.
