# Audit Report: Experiment EXP-021

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 1

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `run_experiment.py` | Correctness | PASS | Formulas, joins, matched-control logic, event-alignment guards all verified; spot-checked paired differences match hand computation. |
| `run_experiment.py` | Edge cases | PASS | Empty cells produce empty schemas (through `write_rows`), zero-candidate regimes return `[]` controls, insufficient-future-bar events flagged `non-reportable`. |
| `run_experiment.py` | Type safety | PASS | Public functions have type hints; numeric columns cast to float64; time columns use `Datetime('us')` canonical form. |
| `run_experiment.py` | NaN handling | PASS | `NaN` logged as None in outputs; `paired_diff_bps` left None when controls unavailable; `control_mean_bps` None with zero controls. |
| `run_experiment.py` | Holdout exclusion | PASS | `load_analysis_data` sorts by `CloseTime` then slices first 70% before collection; `validate_event_join` hard-fails if any `trigger_idx` falls outside domain-bar range. `analysis_end` timestamps emit in metadata. |
| `run_experiment.py` | Loader ordering | PASS | Both `load_analysis_data` (via `referee_calibration`) and the direct `pl.scan_parquet → sort → slice` pattern sort by `CloseTime` before first-70% cutoff. |
| `run_experiment.py` | Memory/performance | PASS | Source loads are lazy until the 70% slice; domain reconstruction collects only first-70%; plotting converts only aggregated summary data. |
| `run_experiment.py` | Safe optimization | PASS | NumPy vectorization of log-return computation and bootstrap resampling preserves sample membership; control matching uses explicit loops with deterministic ordering. |
| `run_experiment.py` | Progress tracking | PASS | Outer loops over instrument/domain cells use `tqdm`; per-cell event iteration is bounded (max ~3000 events in BTCUSD/5m); domain inference loop also uses `tqdm`. |
| `run_experiment.py` | Logging/output | PASS | Concise INFO logging for gate status, `tqdm` desc labels, and final verdict. No noisy per-row output. |
| `run_experiment.py` | Organization/import side effects | PASS | Imports precede constants; output directories created only in `ensure_output_dirs()` called from `run()` orchestration; no side effects at import time. |
| `run_experiment.py` | Plot data reuse | PASS | Plots are fed from `records`/`diag_rows` already in memory from the analysis pass; no repeated heavy loads. |
| `run_experiment.py` | Docstrings | PASS | Module docstring, class-level (via `_AvwapResult`), and function docstrings describe purpose, parameters, and returns. |

## Numerical Validation

### Spot Checks

**EURUSD/5m bull h=3 paired diff:**
Row from `reaction_summary.csv`: mean_paired_diff_bps = 1.342
- Mean event return: 0.460 bps
- Mean control return: −0.882 bps
- Check: 0.460 − (−0.882) = 1.342 ✓

**BTCUSD/5m regime 2 bear h=3:**
Row from `reaction_observations.csv` (trigger_idx=146):
- event_return_bps = 2.9913
- control_returns_bps = "−2.2657|−1.9664|−4.9368|1.0701|−5.2078" → mean = −2.6613
- paired_diff = 2.9913 − (−2.6613) = 5.6526 ✓

**BTCUSD/5m regime 5 bull h=3 (first event at row 6):**
- event_return_bps = 2.7342
- control_mean_bps = −1.7423
- paired_diff = 2.7342 − (−1.7423) = 4.4765 ✓

**Domain effect computation (5m, h=3, verified manually):**
- BTCUSD: (2541×7.185 + 2535×7.349) / 5076 = 7.267
- EURUSD: (1885×1.342 + 1876×1.346) / 3761 = 1.344
- USTEC: (1832×3.541 + 1829×3.990) / 3661 = 3.765
- XAUUSD: (1914×2.841 + 1837×2.849) / 3751 = 2.845
- Domain effect = (7.267 + 1.344 + 3.765 + 2.845) / 4 = 3.805 ✓ (matches `domain_reaction_tests.csv`)

**Holm adjustment (3 domains, raw_p = 0.0001 each):**
- rank 0: min(1.0, 3×0.0001) = 0.0003
- rank 1: max(0.0003, min(1.0, 2×0.0001)) = 0.0003
- rank 2: max(0.0003, min(1.0, 1×0.0001)) = 0.0003
- All three adj. p = 0.0003 ✓ (matches `domain_reaction_tests.csv`)

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| Direction | {+1, -1} | [−1, +1] | YES |
| Control returns (bps) | ℝ | ≈[−235, +74] (BTCUSD/4h) | YES |
| event_return_bps | ℝ | ≈[−51, +43] (full set) | YES |
| paired_diff_bps | ℝ | ≈[−18, +185] (4h BTCUSD) | YES |
| n_controls | [0, 5] | [0, 5] | YES |
| Reportable event counts (h=3) | ≥ 0 per cell | [24, 2541] | YES |

### Statistical Sanity

| Statistic | Value | Makes sense? | Notes |
|-----------|-------|-------------|-------|
| 5m primary effect | +3.8 bps, CI [3.5, 4.2], p < 0.001 | YES | Strong, consistent across all 4 instruments (range 1.3–7.3 bps per instrument). Large sample (16,249 events). |
| 1h primary effect | +9.1 bps, CI [5.1, 13.3], p < 0.001 | YES | Plausible: bounce events outperform same-regime controls. BTCUSD dominates (avg ~18 bps). |
| 4h primary effect | +37.6 bps, CI [22.3, 52.7], p < 0.001 | YES | Large but plausible: same-regime controls have extreme negative means (−94 bps bear BTCUSD), events near zero. Small sample (246 events) widens CI. |
| 1h h=1 CI | [−1.4, 3.0] spans zero | YES | Consistent with shorter horizon having more noise; primary h=3 cleanly above zero. |
| Regime-cluster bootstrap | N_BOOT = 10,000 | YES | Sufficient for 95% CI; percentile method appropriate. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Regime-cluster bootstrap | Regime clusters are independent | YES | Exact matching: each control bar belongs to exactly one regime through `regime_id` scoping. Cross-cluster independence holds by construction. |
| Stratified sign-permutation test | Exchangeability within instrument/direction strata | YES | Sign-flip within strata preserves regime-direction structure; paired differences within stratum are exchangeable under H0. |
| Direction-signed log returns | Sufficient for event-reaction measurement | YES | Standard approach for direction-conditional price reaction. |
| Same-regime control matching | Controls capture counterfactual within regime | YES | Conservative: matched on anchor age and timestamp within same instrument/domain/regime. |

## Results Plausibility

The effect sizes are economically meaningful and internally consistent:

- **5m** (+3.8 bps, CI [3.5, 4.2]): The tightest estimate, reflecting 16,249 events and stable ~1–7 bps per-instrument effects. Consistent with AVWAP bounce capturing intra-regime reversion/continuation at high frequency.
- **1h** (+9.1 bps, CI [5.1, 13.3]): Larger effect, wider uncertainty. BTCUSD contributes the bulk (increasing effect from roughly 2–8 bps to ~18 bps averaged).
- **4h** (+37.6 bps, CI [22.3, 52.7]): Largest point estimate. The same-regime controls have large negative returns (BTCUSD bear controls average −94 bps over 3 bars), while event returns cluster near zero. This is mechanical: bounce events filter for regime-direction confirmation, while random same-regime bars include trend-capturing moves that extend through the pivot. The wide CI reflects only 246 events.

No evidence of look-ahead bias: events are locked at trigger timestamp, controls are selected from past-only information, and all outcomes use future-realized closes.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 2 tests / 2 budgeted, 4 plots / 4 budgeted, 0 new shared modules / 1 budgeted
- Holdout exclusion verified: YES (`analysis_end_by_instrument` confirmed in metadata, event join guard hard-fails on out-of-range indices)
- Dependency gate: PASS (EXP-020 SUPPORTED_FULL with 0 invariant violations)

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Large 4h effect driven by BTCUSD control means**
   - Description: The 4h domain primary effect (37.6 bps) is heavily influenced by BTCUSD, where same-regime control 3-bar returns average −94 bps (bearish) and −75 bps (bullish). These extreme negative control means inflate the paired difference for events that have near-zero returns. This is a genuine feature of the same-regime-matching design — the unmatched return baseline is more negative than the bounce-filtered events — but readers should note the effect is asymmetric across instruments.
   - Impact: Interpretive, not correctness. The per-instrument breakdown in `reaction_summary.csv` makes this visible. The equal-weight domain estimator mitigates single-instrument dominance (BTCUSD contributes 1/4 of the domain effect, not more).

## Re-Audit Requirements

None. Verdict stands without conditions.
