# Audit Report: Experiment EXP-031

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 1
- **Info Notes**: 3

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Sweep, displacement, Candidate A breaker, and outcome logic are all correctly implemented. Verified against EXP-015/018/022/023 conventions. |
| `code/run_experiment.py` | Edge cases | PASS | Empty entries DataFrame guarded before label_breaker; NaN body median guarded in `_is_directional_displacement`; zero-risk guarded before outcomes; insufficient bootstrap replicates checked (< n/4 finite). |
| `code/run_experiment.py` | Type safety | PASS | Public functions have type hints and docstrings. |
| `code/run_experiment.py` | NaN handling | PASS | `BodyMedian100Prior` NaN guarded explicitly; ATR NaN guarded with fillna(0.0); outcome returns nan_out for invalid risk. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `load_analysis_timebars` uses lazy scan → sort by CloseTime → slice first 70%. 15-minute aggregation applied only to analysis-set slice. |
| `code/run_experiment.py` | Loader ordering | PASS | Chronological 70/30 on 15-minute frame; 1-minute outcome bars inherit analysis-set ordering. |
| `code/run_experiment.py` | Memory/performance | PASS | Lazy Polars scan; pandas conversion bounded to the analysis-set bars; outcome rows accumulated per-event row. |
| `code/run_experiment.py` | Logging/output | PASS | `LOGGER.info` for diagnostics; `print` only at completion. |
| `code/run_experiment.py` | Organization/import side effects | PASS | `mkdir` calls inside `run_experiment()` only. `misses.to_csv` also inside orchestration. |
| `code/run_experiment.py` | Plot data reuse | PASS | Plots use pre-computed primary, secondary, waterfall, and entries DataFrames; no re-runs of the analysis pipeline. |
| `code/run_experiment.py` | Docstrings | PASS | All public functions have docstrings. |

## Numerical Validation

### Spot Checks

**Displacement detection — manual verify**

For Side = "High" (bearish setup): `Close < Open AND CloseLocation <= 0.25 AND BodySize >= 1.5 * BodyMedian100Prior`. A bearish displacement bar closes near the low of its range with a large body. ✓

**Candidate A breaker — manual verify**

`_find_last_opposite_candle` for Side = "High": scans backward up to 30 bars before displacement for a bullish candle (`Close > Open`). Returns [Low, High, CloseTime] of that candle as the order block.

`_find_cand_a_breaker` for Side = "High": looks for first bar where `Close < ob_low` (close below the bullish OB's low) within 120 bars after displacement, stopping early if stop is crossed. ✓

**Retention ratio cross-check**

EXP-023 1-minute displacement count: 437 (Train + Test from `chain_waterfall.csv`). EXP-031 15-minute displacement count: 463 (Train 339 + Test 124). Ratio = 463/437 = 1.059. Code computes `fifteen_min_count / one_min_count = 463/437 = 1.059` ✓. `resolution_cost_limited = False` since 1.059 >= 0.30 ✓.

The fact that 15-minute analysis finds MORE displacement events than 1-minute is plausible: 15-minute bars aggregate 15 1-minute bars so the body and close-location criteria are evaluated on a coarser and often stronger apparent displacement bar.

**Verdict derivation — spot check**

From `bootstrap_primary.csv` (Test row): `Diff = 1.836, CILow = 0.560, CIHigh = 3.636`.
- `excludes_zero = True` (0.560 > 0) ✓
- `same_direction = True` (EXP-023 test point = 4.176 > 0; 1.836 > 0 → same sign) ✓
- `within_50pct_or_stronger`: 1.836 >= 0.5 × 4.176 = 2.088? → 1.836 < 2.088 → **False** ✓
- `train_improves = True` (train diff 0.517 × EXP-023 train 0.334 > 0) ✓
- `test_excludes_zero_same_direction = True` ✓
- Falls through to: `elif test_excludes_zero_same_direction and not within_50pct_or_stronger → INCONCLUSIVE, reason=TEST_POSITIVE_BUT_BELOW_EXP023_50PCT_REFERENCE_BAND` ✓

**`within_50pct_or_stronger` clarification**

The condition checks `|EXP-031 diff| >= 0.5 × |EXP-023 diff|`, which requires EXP-031 to be within 50% of EXP-023's magnitude or stronger. Since EXP-023 test = 4.176 and EXP-031 test = 1.836, the 15-minute result is at 44% of the 1-minute magnitude, just below the 50% threshold. The scope's "within ±50 percent of the EXP-023 1-minute USTEC point estimate or stronger" is intended to check whether the effect is comparable in size — a 44% replication does not meet this bar. ✓

**MFE/MAE directional correctness**

For bearish sweep (is_bearish = True):
- `mfe = entry_price - min(h_lows)` — maximum favorable excursion when price drops ✓
- `mae = max(h_highs) - entry_price` — maximum adverse excursion when price rises against short ✓
- `target_1r = entry_price - risk` (below entry for short) ✓
- `stop = sweep_stop` (above entry for short) ✓

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| Waterfall counts (sweep→displacement→breaker→feasible) | Monotonically non-increasing | 399→339→224→219 (train), 145→124→79→78 (test) ✓ | YES |
| BreakerFloorMet | True for both segments | Train: 219 ≥ 50 ✓; Test: 78 ≥ 50 ✓ | YES |
| RetentionRatio | ≥ 0.30 | 1.059 ✓ | YES |
| Diff (primary) | ℝ | Train 0.517, Test 1.836 — positive, plausible | YES |
| CI bounds | CILow < Diff < CIHigh | Train [0.235, 0.517, 0.837] ✓; Test [0.560, 1.836, 3.636] ✓ | YES |
| WinRateHit1R | [0, 1] | [0.208, 0.321] | YES |

### Statistical Sanity

| Statistic | Value | Makes sense? | Notes |
|-----------|-------|-------------|-------|
| Train bootstrap CI width (0.60R) vs Test width (3.08R) | YES | Test has 78 breaker events vs 219 in train; wider CI expected from smaller N. |
| EXP-023 Train CI width 2.88R (very wide) vs EXP-031 Train width 0.60R (narrow) | YES | EXP-023 1m Train CI included zero ([−1.08, 1.80]); EXP-031 15m Train CI excludes zero [0.23, 0.84] — 15-minute Train result is actually sharper. |
| Test breaker mean return 2.42R vs baseline 0.58R | Plausible | Breaker selects 78 of 120 risk-feasible events (65%); selection is non-trivial but sample is small enough for variance. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Outcome evaluation | No intrabar leakage from confirming 15m candle | YES | `searchsorted(entry_ns, side="right")` starts outcome path after displacement CloseTime |
| BodyMedian100Prior | No look-ahead | YES | `rolling_median(100).shift(1)` — only prior bars |
| Candidate A OB search | Backward-only, before displacement | YES | `range(before_idx - 1, search_start - 1, -1)` — scans backward from displacement |
| Stop invalidation check | Applied before breaker confirmation | YES | `_close_invalidates_setup` checked before breaker close-through in `_find_cand_a_breaker` |
| EXP-023 reference loaded correctly | Columns and USTEC rows present | YES | Schema validated; missing-column error would have raised before results were written |

## Results Plausibility

The event waterfall is internally consistent: 15-minute USTEC yields 463 displacement events vs EXP-023's 437 at 1-minute (retention ratio 1.06). Breaker confirmation retains 224/339 train events (66%) and 79/124 test events (64%), which is plausible — the Candidate A breaker at 15-minute bars sees fewer, larger bars, and the OB-close-through criterion fires at a reasonable rate.

The positive direction of both train (0.517R) and test (1.836R) breaker-minus-baseline Return_R_60m is consistent with the EXP-023 1-minute USTEC positive (+4.176R test). The 15-minute test magnitude (1.836R) is 44% of the 1-minute magnitude, which falls just below the predeclared 50% comparability threshold, producing an INCONCLUSIVE rather than FOR verdict.

The wider test CI ([0.560, 3.636]) reflects the smaller test breaker N (78 events). The directional consistency with EXP-023 is the key finding for the reflection.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 3 statistical tests (primary, secondary MAE, secondary Return) / 3 budgeted; 4 visualisations / 4; 0 new modules (bar_aggregator.py reused) / 1 max
- Holdout exclusion verified: YES
- Canonical entry timing (displacement-close at 15-minute resolution): YES
- Inherited-stop convention from EXP-015: YES — stop = sweep extreme + buffer

## Issues

### Critical

None.

### Warning

1. **EXP-023 Train CI ([−1.08, 1.80]) includes zero — the EXP-031 comparison uses this as a reference even though the 1-minute train result itself was underpowered**
   - File: `code/run_experiment.py`, `build_exp023_comparison`, and `evaluate_verdict`
   - Description: `train_improves` is set to True whenever `train_diff × EXP023_test_diff > 0`. The code compares EXP-031 train against EXP-023's **test** point (not train), so the direction test is against a meaningful reference. However, the EXP-031 train CI [0.23, 0.84] is notably sharper than EXP-023's train CI [−1.08, 1.80]. The interpretation should note this context: EXP-031's 15-minute train result is arguably more statistically definitive than EXP-023's 1-minute train result.
   - Impact: No code error; does not affect the verdict. Risk is that the INCONCLUSIVE verdict could be misread as "weaker than EXP-023" when in fact the 15-minute train is more definitively positive.
   - Fix: No code change. Surface this in results.md and report.md.

### Info

1. **BodyMedian100Prior NaN for first 100 bars disables displacement detection there**
   - Description: `rolling_median(100, min_samples=100).shift(1)` yields NaN for first 101 bars. `_is_directional_displacement` returns False when median_body is NaN. This excludes displacement events in the first ~1,500 minutes (25 hours) of the 15-minute analysis set, a negligible fraction of 54,787 bars.

2. **Bootstrap degrades gracefully when fewer than n/4 replicates are finite**
   - Description: The CI falls back to NaN when fewer than 25% of bootstrap replicates produce a finite diff (due to all-breaker-null resamples). This guard is correct and was not triggered (both train and test have sufficient BreakerN).

3. **Waterfall does not enforce date-based first-touch per-level across all four level types jointly**
   - Description: `_build_level_events` applies first-touch per NYDate within each level type independently (PDH, PDL, ONH, ONL run separately). If a date has both a PDH sweep and a PDL sweep, both are retained. This matches EXP-015 and EXP-023's denominator policy and is correct per scope.
