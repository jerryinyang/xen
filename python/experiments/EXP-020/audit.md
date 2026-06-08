# Audit Report: Experiment EXP-020

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 1

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Sequential AVWAP state machine, MA(20,50) crossover, anchor selection, arm/trigger logic, re-arm enforcement, zero-weight protection all correct. |
| `code/run_experiment.py` | Edge cases | PASS | Empty frame, insufficient bars (< SLOW_MA), zero cumulative weight, zero total events, zero direction counts — all handled explicitly. |
| `code/run_experiment.py` | Type safety | PASS | Type hints on all public functions; `EVENT_SCHEMA`/`REGIME_SCHEMA` dicts enforce output column types. |
| `code/run_experiment.py` | NaN handling | PASS | `finite_values` invariant check validates no NaN in avwap/band/close columns; avwap undefined while `cum_w <= 0.0` skipped with continue. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `load_analysis_data()` lazy-scans, sorts by `CloseTime`, slices first 70% before collection. 0 holdout violations in results. |
| `code/run_experiment.py` | Loader ordering | PASS | Lazy scan sorts by CloseTime before slicing first 70%; no full holdout collection. |
| `code/run_experiment.py` | Memory/performance | PASS | Large inputs stay lazy until first-70% slice; AVWAP state machine runs sequentially per cell; plotting uses bounded summary tables or a single 400-bar trace window. |
| `code/run_experiment.py` | Safe optimization | PASS | No vectorized shortcuts that breach causality; the state machine is genuinely streaming-safe; `_causal_sma` uses only current and prior values. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` over instrument/domain loops for both generate and replay passes. |
| `code/run_experiment.py` | Logging/output | PASS | Concise INFO-level output; helper functions return data instead of printing; summary line after completion. |
| `code/run_experiment.py` | Organization/import side effects | PASS | Imports → paths → constants → helpers → plotting → orchestration → main(); output directories created in `main()` only. |
| `code/run_experiment.py` | Plot data reuse | PASS | Bounded `select_sample_window()` and `compute_band_trace()` reuse the already-generated `AvwapResult` and domain frame; no second generator pass for plots. |
| `code/run_experiment.py` | Docstrings | PASS | All public functions have Parameters/Returns sections. |
| `python/src/xen/avwap.py` | Correctness | PASS | `_causal_sma` uses cumsum-based trailing SMA correctly; `_StreamingMedian` uses dual-heap algorithm; regime detection, anchor selection, arm/trigger logic match scope. |
| `python/src/xen/avwap.py` | Edge cases | PASS | Empty frame → empty `AvwapResult`; n < SLOW_MA → empty frames; zero TickVolume → zero weight → skipped with continue. |
| `python/src/xen/avwap.py` | NaN handling | PASS | `_validate_domain_frame` raises on null TickVolume; `_StreamingMedian.median()` returns NaN when empty; `cum_w <= 0.0` skipped before AVWAP division. |
| `python/src/xen/avwap.py` | Determinism | PASS | All randomness sources absent; `_StreamingMedian` is deterministic for any push order; sequential state machine with no random seeds. |

## Numerical Validation

### Spot Checks

- **BTCUSD 5m density**: 5978 / 216982 × 10000 = 275.507 — matches output 275.5067.
- **Holdout split**: all four instruments at exactly 70.00% analysis rows (1088960/1555658 BTCUSD; 872242/1246061 EURUSD; 830541/1186488 USTEC; 830671/1186674 XAUUSD).
- **Direction balance**: all 12 cells have bull ≥ 28 and bear ≥ 31, well above the 8-event floor.
- **Deterministic replay**: 12/12 event-table hashes and 12/12 regime-table hashes identical between main and replay pass.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| Direction | {+1, -1} | [-1, 1] | YES |
| TickVolume | ≥ 0 | ≥ 0 (validated by `_validate_domain_frame`) | YES |
| Event timestamps | Monotonically increasing per regime | Verified by `temporal_order` invariant (0 violations) | YES |
| anchor_age_bars | > 0 | Verified by `anchor_age_positive` invariant (0 violations) | YES |
| holdout_fence | trigger_time ≤ analysis_end | 0 violations across all cells | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| Total events across 12 cells | 20,911 | YES | ~5k-6k on 5m per instrument, ~100-400 on 4h — expected given MA crossover regime lengths |
| Events per regime (5m) | ~1.17 | YES | Most regimes produce 0-1 bounces before reversal; median regime ~35 bars on 5m for MA(20,50) |
| Median anchor age | 33-39 bars | YES | Anchor established at regime confirmation, events occur ~1-2 regimes later |
| Direction imbalance | 0.46-0.56 bull fraction | YES | No severe imbalance; max imbalance EURUSD/4h 0.557 bull → still reportable (39 bull, 31 bear) |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| `_causal_sma` | Trailing SMA uses only current and prior closes | YES | `np.cumsum` with lag difference; validated by code review of `_causal_sma` |
| Anchor selection | Bullish anchor = min Low in bearish segment; bearish anchor = max High | YES | Verified by `anchor_selection` invariant (0/5094 violations on BTCUSD 5m) |
| Arm/trigger causality | Arm happens before trigger; trigger does not precede confirm | YES | Verified by `event_timestamp_index` and `temporal_order` invariants (0 violations) |
| Re-arm after trigger | bounce_index_in_regime is 1,2,... without gaps | YES | `rearm_monotonic` invariant (0 violations across all cells) |
| Deterministic replay | Identical output for identical input | YES | All 12 cells match event and regime hashes |

## Results Plausibility

All outputs are within expected ranges:
- Event counts scale with domain bar count: 5m ~4-6k events, 1h ~300-400, 4h ~60-110.
- Direction balance is reasonable across all cells (no domain or instrument shows degenerate single-direction coverage).
- Median anchor ages (33-39 bars) are consistent with MA(20,50) regime length distributions.
- 20,911 total events across 12 cells and 3 domains provides a substantial substrate for follow-up reaction studies.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 1 readiness table / 1 budgeted, 4 plots / 4 budgeted, 1 new module (avwap.py) / 1 budgeted
- Holdout exclusion verified: YES (all four instruments at exactly 70% analysis rows; 0 holdout violations)
- Instruments: BTCUSD, EURUSD, USTEC, XAUUSD — all four scoped instruments present
- Domains: 5m, 1h, 4h — all three scoped domains present
- Parameters: MA(20,50), TickVolume^0.75, MAD band multiplier 1.0 — match scope
- Registry: CF-AVWAP-001 — matches multiplicity registry

## Issues

### Info

1. **EURUSD/4h moderate direction imbalance**
   - File: `results/direction_balance.csv`, row 7
   - Description: EURUSD/4h has bull_fraction 0.557 vs bear_fraction 0.443 (39 bull, 31 bear). Both directions remain above the 8-event floor, but the gap is the widest among all cells at 8 events.
   - Impact: None. Both directions are reportable. Follow-up reaction studies may prefer pooled or direction-balanced designs; this is a descriptive note for scoping EXP-021.

## Re-Audit Requirements

None.
