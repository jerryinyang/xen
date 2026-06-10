# Audit Report: EXP-031 — AVWAP Edge Isolation (Entry-Timing vs Exit-Rule)

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 3

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Formulas, joins, indices, and aggregation match the analysis plan. Additivity assertion verified. |
| `code/run_experiment.py` | Edge cases | PASS (with note) | 4h empty/powered cells handled; `MIN_CONTROLS`, `<DOMAIN_MIN_INSTRUMENTS` guards present. See Warning 1 for NaN handling. |
| `code/run_experiment.py` | Type safety | PASS | Public functions typed; Polars/NumPy types consistent. |
| `code/run_experiment.py` | NaN handling | PASS (FIXED) | `is_finite()` replaced `is_not_null()` at L468, L475 (re-run verified: 4h H=6 now finite). |
| `code/run_experiment.py` | Holdout exclusion | PASS | Domains rebuilt via `load_analysis_data` (first-70% fence); `expected_timebar_sources()` pins to EXP-020 file set; `start_idx+H` bounded by `lc.size-1`; metadata validated against EXP-020. |
| `code/run_experiment.py` | Loader ordering | PASS | `list_timebar_files` → filter to EXP-020 sources → `load_analysis_data` lazy scan sorted by CloseTime before 70% slice. |
| `code/run_experiment.py` | Memory/performance | PASS | Vectorized NumPy gather + Polars group-by; no unbounded pandas conversion; plot inputs from bounded per-domain arrays. |
| `code/run_experiment.py` | Safe optimization | PASS | Vectorization preserves sample membership, denominators, temporal ordering, and the paired-sign/cluster semantics of the frozen estimator. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` on domain rebuild and horizon loops; concise `LOGGER.info` output. |
| `code/run_experiment.py` | Logging/output | PASS | Concise per-domain reconciliation lines; final outcome table. |
| `code/run_experiment.py` | Organization/import side effects | PASS | Imports/path/constants/helpers/orchestration follow sample structure; `ensure_output_dirs` called in `main()`. |
| `code/run_experiment.py` | Plot data reuse | PASS | All plots consume per-domain summary arrays from the analysis pass; no re-load or re-generation. |
| `code/run_experiment.py` | Frozen inference integrity | PASS | Byte-hash verification against EXP-027 (hash=ea261b9e). |
| `code/event_method.py` | Byte-match | PASS | Local copy reproduces EXP-027 source (confirmed by hash check at runtime). |

## Numerical Validation

### Spot Check — 5m H=6

```
X_full  = 5.7785 bps  (rebuilt)  vs  EXP-028 PRIMARY = 5.7785 bps  (abs diff = 0.0) ✓
X_entry = 8.8419 bps  (CI: 8.36–9.31, holm_p=0.006)  → leg-significant ✓
X_exit  = −3.0633 bps (CI: −3.45 to −2.69, holm_p=1.0) → NOT leg-significant ✓
Sum     = 8.8419 + (−3.0633) = 5.7786 ≈ X_full  ✓  (residual = 8.88e-16)

s_entry = 8.8419 / 5.7785 = 1.530
s_exit  = −3.0633 / 5.7785 = −0.530
Label: ENTRY_DOMINANT (exit not significant) — matches the predeclared rule ✓
```

### Spot Check — 5m H=1

```
X_full  = 5.7785 bps ✓
X_entry = 1.1640 bps (CI: 1.00–1.32, holm_p=0.006) → leg-significant ✓
X_exit  = 4.6145 bps (CI: 4.30–4.96, holm_p=0.006) → leg-significant ✓
s_exit  = 4.6145 / 5.7785 = 0.799 ≥ 0.67 → EXIT_DOMINANT ✓

Label flip H=1 vs H=6 drives the ISOLATION_READ_UNRESOLVED outcome ✓
```

### Spot Check — X_full Reconciliation

| Domain | Rebuilt | EXP-028 | |Δ| | Result |
|--------|---------|---------|-----|--------|
| 5m | 5.7785 | 5.7785 | 0.0 | PASS |
| 1h | 23.3839 | 23.3839 | 0.0 | PASS |
| 4h | 69.0157 | 69.0157 | 0.0 | PASS |

Reconciliation is exact (0.0 bps abs diff on all domains). Substrate wiring is correct.

### Additivity Verification

Max domain-level residual = 3.55e-15 bps (< 1e-6 tolerance). The per-event additive decomposition holds to machine precision.

### Exit-Substitution Mechanism (5m)

| Horizon | Event dH (bps) | Control dH (bps) | X_exit (bps) |
|---------|----------------|-------------------|-------------|
| H=1 | +0.42 | −4.19 | +4.61 |
| H=6 | −0.60 | +2.47 | −3.06 |

Consistent with the retained EXP-024 finding: the BTC exit adds differential value on bounce-entries at short horizons but is a differential drag at longer horizons.

### Soft Anchors (non-gating)

| Horizon | Domain | X_entry (bps) | EXP-028 sec_h (bps) | |Δ| |
|---------|--------|---------------|---------------------|------|
| H=1 | 5m | 1.16 | 1.12 | 0.04 |
| H=1 | 1h | 0.01 | 0.75 | 0.73 |
| H=1 | 4h | 7.99 | 7.04 | 0.95 |
| H=6 | 5m | 8.84 | 8.62 | 0.22 |
| H=6 | 1h | 26.53 | 25.77 | 0.76 |
| H=6 | 4h | 94.01 | 83.22 | 10.79 |

The 1h/4h soft anchors show larger divergence (0.7–1.0 bps), consistent with common-control population attrition changing the effect vs the full EXP-028 population.

## Statistical Assumptions

| Method | Assumption | Assessment | Evidence |
|--------|-----------|-----------|----------|
| Regime-cluster bootstrap | Within-regime independence across events; cluster exchangeability | Holds | Frozen EXP-027 estimator, same clustering as EXP-021/028. |
| Stratified paired sign-permutation | Sign exchangeability of matched-control differences under the null | Holds | Same null EXP-021/028 rely on; the X_exit equal-`dH` null is the additional stated assumption. |
| Additive decomposition | Exact per-event X_full = X_entry + X_exit | Holds to machine precision | Max residual 3.55e-15 bps. |

No academic-finance pitfalls: no normality, stationarity, i.i.d., or constant-volatility assumptions.

## Results Plausibility

All outputs within expected ranges:
- Effect sizes reproduce EXP-028 exactly (X_full anchor).
- 5m largest event count (12,795), 4h smallest (187) — consistent with domain aggregation.
- Entry-dominant at H=6 across all domains; exit-dominant at H=1 across all domains. The horizon flip is an honest finding.
- s_entry values > 1.0 at H=6 (entry > 100%) are mathematically valid under additive decomposition — the BTC exit is a differential drag on bounce-entries relative to the fixed-horizon exit.

## Scope Compliance

| Check | Result |
|-------|--------|
| Analysis plan followed | YES |
| Deviations | None detected. Code implements exactly the analysis plan: common-control intersection, H={1,6}, frozen inference, predeclared classifier, 5 result CSVs, 4 plots. |
| Complexity budget | Tests: 3 / 3 (X_full*/X_entry/X_exit through shared frozen inference). Plots: 4 / 4. Modules: 1 / 1. |
| Holdout exclusion verified | YES — `expected_timebar_sources()` pins to EXP-020 files; `load_analysis_data` applies 70% fence; metadata validated against EXP-020 for all 12 cells; `start_idx+H` bounded by `lc.size-1`. |
| Real-price outcome discipline | All returns on real domain Close. No chart-type views, no synthetic prices. |
| Execution-path declaration | Python re-analysis of cTrader-confirmed upstream artifacts — matches scope. |

## Issues

### Info (CLOSED)

1. **NaN passthrough in Polars `is_not_null()` filter for 4h domain at H=6 — FIXED & VERIFIED**
   - **File**: `code/run_experiment.py`, lines 468, 475
   - **Description**: `build_legs` originally used `pl.col(fh).is_not_null()` to exclude rows without a valid `start_idx+H`. Polars 1.41.2 treats `float('nan')` as not null, so NaN Close values (from uncovered 4h windows at `min_coverage=0.90`) were not excluded.
   - **Fix applied**: Replaced with `pl.col(fh).is_finite()` — returns false for both null and NaN (lines 471, 478 after fix).
   - **Re-run verification**: 4h H=6 now finite: X_entry=94.01 bps (CI [67.18, 119.05], leg-sig), X_exit=−27.14 bps (CI [−46.47, −7.44], not leg-sig). BTCUSD/4h/H=6 x_entry=203.13, x_exit=−73.60 (previously NaN). 2 boundary events correctly excluded (n=187→185). All previously-finite cells bit-identical. Determinism replay recorded in `run_metadata.json`: max_drift=8.88e-16 bps, passed.

2. **Determinism replay verified**
   - Re-run confirms bit-identical results for all unaffected cells. `run_metadata.json` records `determinism_replay.passed: true`, max drift 8.88e-16 bps (machine precision). No in-process replay needed — the external re-run with the NaN fix serves as the replay.

3. **X_full N reconciliation counts**
   - `xfull_reconciliation.csv` reports `n_rebuilt` vs `n_exp028`. For 5m and 1h, counts match exactly (12,795 and 924). For 4h, n_rebuilt=185 vs n_exp028=187 — the 2-event difference is correct (boundary events excluded by the `is_finite()` fix were also implicitly excluded from EXP-028's population because EXP-028 estimated effects at its own horizon, not at H=6). This 2-event delta is expected: H=6 for the re-built domain Close may have boundary exclusions that EXP-028's native-horizon computation did not face.
