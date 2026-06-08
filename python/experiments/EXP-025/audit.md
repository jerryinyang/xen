# Audit Report: Experiment EXP-025

## Summary

- **Verdict**: CONDITIONAL PASS
- **Critical Issues**: 0
- **Warnings**: 2
- **Info Notes**: 6

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Formulas match scope; control selection deterministic; inference matches plan. |
| `code/run_experiment.py` | Edge cases | PASS | Empty frames, NaN scores, non-reportable events all handled. |
| `code/run_experiment.py` | Type safety | PASS | Direction as int, numeric arrays as float. |
| `code/run_experiment.py` | NaN handling | PASS | `valid_ohlc` + `np.isfinite` gates; NaN reason assignment; `_finite` helper for plots. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `load_analysis_data()` (line 120, `referee_calibration.py`) sorts by CloseTime, slices `int(total * 0.70)` before any domain aggregation. Domain reconstruction validates against EXP-020 metadata. |
| `code/run_experiment.py` | Loader ordering | PASS | Lazy scan sorts by CloseTime before slicing first 70%; no full-dataset collection or final-30% inspection. |
| `code/run_experiment.py` | Memory/performance | PASS | Large inputs use Polars lazy scan + column projection; plots reuse computed records; no pandas conversion of full data. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` wraps file-rebuild loop, cell processing loop, and domain inference loop. No noisy per-row output. |
| `code/run_experiment.py` | Logging/output | PASS | Concise INFO logging; hard-fail on reconstruction mismatch; clear final verdict output. |
| `code/run_experiment.py` | Organization/import side effects | PASS | Imports first, no output dirs at import time; `ensure_output_dirs` called in `run()`. |
| `code/run_experiment.py` | Plot data reuse | PASS | All 4 plots read from `records` (bounded list of dicts) and `domain_stats` — no second data pass. |
| `code/run_experiment.py` | Docstrings | PASS | Module docstring explains purpose and run command; key functions have docstrings. |
| `xen/referee_calibration.py` | Holdout exclusion | PASS | `load_analysis_data()`: scan → sort("CloseTime") → slice(0, int(total*0.70)) → collect. |
| `xen/avwap.py` | AVWAP replay | PASS | `compute_band_trace()` uses same `VOLUME_EXPONENT=0.75` and `BAND_MULTIPLIER=1.0` as frozen EXP-020 substrate. |

## Numerical Validation

### Spot Check (observation row 1 — BTCUSD, 5m, regime 2, direction=-1, trigger_idx=146)

**Event-level score** (bearish direction, from observations CSV line 2):
- `event_close_to_avwap_bps = 10000 * log(Close / AVWAP)` = -3.33
- `event_close_rebound_bps = 10000 * log(AVWAP / Close)` = -(-3.33) = 3.33 ✓
- `event_adverse_penetration_bps = max(0, 10000 * log(High / AVWAP))` = 1.30 ✓ (≥0)
- `event_line_rejection_score_bps = 3.33 - 1.30` = 2.03 ✓

**Control matching**:
- 5 controls selected (n_controls=5) ✓
- `control_mean_line_rejection_score_bps` = -3.86
- `paired_diff_bps = 2.03 - (-3.86)` = 5.89 ✓

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| Direction | {+1, -1} | {-1, 1} in all CSV outputs | YES |
| RealClose | Positive ℝ | Positive (all instruments in domain bars) | YES |
| High/Low/Close | High ≥ Low | Constraint enforced by `valid_ohlc()` | YES |
| event_line_rejection_score_bps | ℝ | [-120, 90] range in observations sample | YES |
| adverse_penetration_bps | ≥ 0 | Non-negative (enforced by `np.maximum(0, ...)`) | YES |
| reportable | {true, false} | {true, false} | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| 5m primary effect | -4.41 bps | YES | Negative — events score worse than controls |
| 5m 95% CI | [-4.85, -4.00] | YES | Tight, entirely negative; n=10,432 provides precision |
| 5m raw p (one-sided positive) | 1.0 | YES | Observed effect is strongly negative; ~100% of permuted means ≥ -4.41 |
| 1h primary effect | -16.94 bps | YES | Stronger negative; n=763, CI wider |
| 1h 95% CI | [-22.12, -11.77] | YES | Entirely negative, width ~10 bps with n=763 |
| 1h raw p | 1.0 | YES | Same logic as 5m — effect strongly negative |
| 4h primary effect | -6.77 bps | YES | n=120, high variance |
| 4h 95% CI | [-34.13, +22.80] | YES | Wide, spans zero; consistent with small n (120) across 3 instruments |
| 4h raw p | 0.715 | YES | ~28.5% of permuted means more negative than -6.77 — plausible under null |
| Holm p (all domains) | 1.0 | YES | All raw p >> 0.05; adjustment changes nothing |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Regime-cluster bootstrap | Regimes are independent clusters | PARTIAL | Reasonable for AVWAP state machine; 4h has few clusters per instrument |
| Stratified sign permutation | Exchangeability under null | YES | Paired diffs signed under null; correct one-sided test |
| Equal-weight domain estimator | Instruments equally informative | YES | Predeclared; prevents high-count cell dominance |
| Control matching | Matching on proximity creates comparable bars | WARNING | BTCUSD 5m controls are systematically farther from AVWAP (diff 3.7-4.8 bps), though domain median is 1.99 bps |

## Results Plausibility

The negative effects are **internally consistent and structurally expected**:

1. **Sign consistency**: Every instrument/domain/direction cell shows events with lower (more negative) mean line_rejection_score than their matched controls. This is not a fluke — it's a systematic pattern across all 24 reportable cells.

2. **Structural explanation**: AVWAP bounce triggers close through AVWAP (by definition). For a bullish trigger, close is above AVWAP but the intrabar low penetrates below AVWAP, producing `close_rebound - adverse_penetration` that is often negative because adverse penetration (low far below AVWAP) exceeds close rebound. Controls are near AVWAP (same absolute distance) but are NOT crossing through it, so their intrabar penetration is smaller.

3. **CI width scales with sample size**: 5m (n=10,432) → 0.85 bps CI width; 1h (n=763) → 10.35 bps width; 4h (n=120) → 56.93 bps width. Logarithmic scaling as expected.

4. **5m borderline balance**: 1.99 bps domain-level diff is just under the 2.0 threshold. BTCUSD 5m shows broken balance (3.67-4.81 bps), masked by domain-level median pooling.

## Scope Compliance

- **Analysis plan followed**: YES
- **Deviations**: None. All 6 steps from analysis-plan.md are implemented.
- **Complexity budget**: 2 tests / 2 budgeted, 4 plots / 4 budgeted, 0 modules / 0 budgeted
- **Holdout exclusion verified**: YES — `load_analysis_data()` at `referee_calibration.py:120-158` applies chronological first-70% slice; domain reconstruction validates against EXP-020 metadata; all 12 cells PASS.

## Issues

### Warning

1. **BTCUSD 5m proximity imbalance masked by median pooling**
   - File: `code/run_experiment.py`, lines 815-838 (`domain_balance`)
   - Description: The domain-level balance diagnostic pools events across all reportable instruments before computing the median absolute proximity diff. BTCUSD 5m shows instrument-level broken balance (bullish: 4.81 bps diff, bearish: 3.67 bps diff, both > 2.0). However, EURUSD (0.80-0.83), USTEC (1.67-1.81), and XAUUSD (1.54-1.67) are all below threshold, pulling the domain median to 1.99 bps — just under the 2.0 threshold.
   - Impact: BTCUSD 5m's event and control bars have systematically different line proximity, which could introduce bias in its per-instrument effect. Since all instruments show consistent negative effects, this does not change the overall conclusion. The implementation is faithful to the scope (which checks domain-level median).
   - Fix: Add per-instrument balance diagnostics to run_metadata.json for transparency. Consider a warning flag when any instrument in a domain has broken balance.

2. **4h regime-cluster bootstrap may have degenerate cluster counts**
   - File: `code/run_experiment.py`, lines 755-775 (`bootstrap_ci`)
   - Description: The 4h domain has only 120 events across 3 instruments (BTCUSD 51, EURUSD 37, USTEC 32). Per (instrument, direction) strata, the number of regimes (clusters) may be very small (e.g., 2-5 regimes per cell). Resampling with replacement from 2-5 clusters produces a coarse bootstrap distribution. The CI width of 57 bps reflects this uncertainty.
   - Impact: The 4h INCONCLUSIVE_SPANS_ZERO label is conservative and arguably correct given the uncertainty. The wide CI correctly signals insufficient precision.
   - Fix: No code change needed — the result is already labeled as inconclusive. For future experiments, consider a minimum regime-count guard.

### Info

1. **5m domain-level balance threshold borderline (1.99 bps vs 2.0)**: The threshold was specified in scope, but BTCUSD 5m having broken balance (3.67-4.81 bps) while the domain median is 1.99 bps is a close call. If the threshold were 1.99, 5m balance would be broken and (if all domains had broken balance) the verdict would change to INCONCLUSIVE_MATCHING_BALANCE. Since 4h already makes the overall verdict INCONCLUSIVE, material impact is zero.

2. **All non-reportable events are due to insufficient controls**: The control_match_diagnostics.csv shows zero events lost to `invalid_event_avwap` or `invalid_event_score` across all 24 instrument/domain/direction cells. Every non-reportable event is due to `insufficient_line_proximate_controls` (< 3 controls within band proximity). This indicates the AVWAP replay and OHLC data are clean, but the line-proximity rule is a binding constraint.

3. **Mean controls per reportable event is ~4.5-4.9**: Most reportable events get close to the maximum 5 controls, suggesting the candidate pool is adequate when proximity conditions are met.

4. **Systematic pattern across all cells**: Events have negative or near-zero mean scores; controls have positive mean scores in every reportable cell. This consistency across 24 cells (4 instruments × 3 domains × 2 directions) provides strong evidence that the effect is real, even though it's in the opposite direction from the scoped hypothesis.

5. **Permutation test correctly one-sided**: The `permutation_p` function tests for effect > 0 (positive advantage). With negative observed effects, raw p ≈ 1.0 for strongly negative domains is the expected correct behavior. The Holm adjustment produces p=1.0 for all domains.

6. **4h XAUUSD excluded at 26 events**: XAUUSD 4h has 26 reportable events (< 30), so it's correctly excluded from the 4h domain. The domain still has 3 instruments meeting the minimum (BTCUSD 51, EURUSD ~37, USTEC ~32).

## Re-Audit Requirements

No re-audit required. The two warnings do not affect the overall verdict (INCONCLUSIVE) and are transparency issues rather than correctness bugs. Apply the recommended fixes (per-instrument balance tracking, minimum regime-count guard for bootstrap) in future experiments.
