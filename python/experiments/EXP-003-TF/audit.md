# Audit Report: Experiment EXP-003-TF

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 1
- **Info Notes**: 1

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/src/timeframe_replication.py` (run_exp003_tf) | Correctness | PASS | Perturbation, stability metrics, and robustness ranking implemented correctly. |
| `python/src/timeframe_replication.py` (perturb_time_bars) | Edge cases | PASS | Returns clone for noise_level <= 0; OHLC repair ensures High >= max(Open,Close) and Low <= min(Open,Close). |
| `python/src/timeframe_replication.py` (stability_metrics) | Type safety | PASS | Returns dict with float values; handles empty arrays via `np.nan`. |
| `python/src/timeframe_replication.py` (lz_complexity) | NaN handling | PASS | Returns 0.0 for sequences < 2; caps at max_len=200,000. |
| `python/src/timeframe_replication.py` (load_source_analysis) | Holdout exclusion | PASS | Lazy scan sorts by `CloseTime`, slices first 70% before `.collect()`. |
| `python/src/timeframe_replication.py` (load_timeframes) | Memory/performance | PASS | Lazy loading; LZ complexity capped at 200k chars. |
| `python/src/timeframe_replication.py` (run_exp003_tf) | Logging/output | PASS | 5 CSVs + 1 JSON + 5 plots produced. |
| `python/src/timeframe_replication.py` (run_exp003_tf) | Docstrings | PASS | Public functions in shared module have docstrings. |

## Numerical Validation

### Spot Checks

**EURUSD 15m Time 20% noise DirectionDrift:**
- From stability_metrics.csv: 0.003061
- This is |pert_up - base_up| / max(|base_up|, 1e-9)
- base_up for Time bars ≈ 0.5 (roughly equal up/down), perturbation at 20% causes small shift
- 0.003061 = 0.3% relative drift — plausible for 20% noise on forex ✓

**EURUSD 15m Renko 20% noise ReturnVarianceDrift:**
- From stability_metrics.csv: 0.0755
- Renko is more robust than Time (0.1098) — 31% lower drift ✓
- This counts toward "at least 25% lower" criterion

**Robustness ranking — 15m LineBreak DirectionDrift:**
- InstrumentsWithAtLeast25PctLowerDrift = 2
- Checking: EURUSD LB(0.0016) vs Time(0.0031): 0.0016 <= 0.75*0.0031=0.0023 → YES
- XAUUSD LB(0.0015) vs Time(0.0009): 0.0015 <= 0.0007 → NO
- BTCUSD LB(0.0032) vs Time(0.0007): 0.0032 <= 0.0005 → NO
- USTEC LB(0.0014) vs Time(0.0035): 0.0014 <= 0.0026 → YES
- Count = 2 ✓ matches ranking

**Perturbation audit — InvalidRows:**
- All InvalidRows = 0 across all instruments/timeframes/noise levels ✓
- OHLC repair is fully effective

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| DirectionDrift | ≥ 0 | 0.0 to 0.0154 | YES |
| ReturnVarianceDrift | ≥ 0 | 0.0 to 0.3042 | YES |
| ComplexityDrift | ≥ 0 | 0.0 to 0.0558 | YES |
| InvalidPct | [0, 1] | 0.0 for all | YES |
| PerturbedRows | ≥ 0 | 0 to 21466 | YES (scales with noise level) |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| 0% noise drift | All 0.0 | YES | Baseline vs baseline = no drift |
| Drift increases with noise | Generally monotonic | YES | Most chart types show increasing drift from 10%→20%→30% |
| HA lowest drift | ReturnVarianceDrift consistently lowest | YES | HA smoothing absorbs noise, as expected |
| Renko moderate drift | Between Time and HA | YES | Renko brick filtering provides partial robustness |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Deterministic perturbation | Same instrument+timeframe+noise produces same perturbation | YES | SHA-256 seed derived from `f"{instrument}-{timeframe}-{noise_level}-EXP003TF"` |
| OHLC repair | Repair always produces valid OHLC | YES | InvalidRows = 0 for all combinations |
| LZ complexity | Direction sequence complexity is comparable across chart types | PARTIAL | Different chart types have different row counts; LZ is log-normalized but sequence length affects results |
| HAClose for HA variance stability | HAClose returns used as distortion diagnostic only | YES | `chart_returns` uses HAClose for HeikenAshi, documented as non-tradable |

## Results Plausibility

Results are plausible. Heiken Ashi consistently shows the lowest drift across all metrics, confirming its smoothing effect. Renko shows moderate robustness, often better than Time bars for return variance drift but worse for direction drift. LineBreak shows mixed results. The robustness ranking correctly shows that no chart type achieves ≥25% lower drift on ≥3 instruments for any metric (max count = 2).

## Scope Compliance

- Analysis plan followed: YES
- Deviations: None
- Complexity budget: 3 statistical tests (stability metrics, robustness ranking, perturbation audit) / 3 budgeted; 5 visualisations / 5 budgeted; 0 new modules / 1 budgeted
- Holdout exclusion verified: YES
- Perturbation applied after holdout exclusion and aggregation: YES

## Issues

### Warning

1. **LZ complexity comparison across chart types with different row counts**
   - File: `python/src/timeframe_replication.py`, line 896 (`lz_complexity`)
   - Description: LZ76 complexity is log-normalized (factors / log2(n)), but chart types have vastly different row counts (e.g., Time: 55,230 vs Renko: 13,754 for EURUSD 15m). The log normalization partially corrects for length, but residual length effects may remain.
   - Impact: ComplexityDrift comparisons between chart types may be confounded by row count differences. Within-chart-type comparisons (perturbed vs baseline) are more reliable.
   - Fix: No code fix needed; interpret ComplexityDrift as within-chart-type metric only.

### Info

1. **HA uses HAClose for return variance stability**
   - Description: Per scope and analysis plan, HA return variance stability uses HAClose returns as a non-tradable distortion diagnostic. This is correct per synthetic price discipline rules.
   - Impact: Intentional design; documented in scope.

## Re-Audit Requirements

None. Verdict is PASS.
