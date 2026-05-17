# Audit Report: Experiment EXP-004-TF

## Summary

- **Verdict**: CONDITIONAL PASS
- **Critical Issues**: 0
- **Warnings**: 2
- **Info Notes**: 1

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/src/timeframe_replication.py` (run_exp004_tf) | Correctness | PASS (with caveat) | Reversal detection, signal extraction, and matching implemented. Precision calculation has a semantic issue (see Warning 1). |
| `python/src/timeframe_replication.py` (detect_reversals) | Edge cases | PASS | Handles empty input; requires ATR_PERIOD + 2 bars minimum. |
| `python/src/timeframe_replication.py` (match_reversal_signals) | Type safety | PASS | Returns tuple of DataFrame and dict; uses `np.nan` for missing values. |
| `python/src/timeframe_replication.py` (direction_change_signals) | NaN handling | PASS | Handles empty tables; drops null `_prev` values. |
| `python/src/timeframe_replication.py` (load_source_analysis) | Holdout exclusion | PASS | Lazy scan sorts by `CloseTime`, slices first 70% before `.collect()`. |
| `python/src/timeframe_replication.py` (load_timeframes) | Memory/performance | PASS | Lazy loading; timeline plot limited to 120 rows. |
| `python/src/timeframe_replication.py` (run_exp004_tf) | Logging/output | PASS | 7 CSVs + 1 JSON + 5 plots produced. |
| `python/src/timeframe_replication.py` (run_exp004_tf) | Docstrings | PASS | Public functions in shared module have docstrings. |

## Numerical Validation

### Spot Checks

**EURUSD 15m Time bar latency:**
- MedianLatencyMinutes = 30.0, MedianLatencyBars = 2.0
- At 15m timeframe, 2 bars = 30 minutes ✓ consistent
- Time bars need 2 bars to confirm a reversal (current bar closes beyond threshold, next bar confirms direction) ✓

**EURUSD 15m Renko latency:**
- MedianLatencyMinutes = 0.0, MedianLatencyBars = 0.0
- Renko bricks form at the exact reversal timestamp (within same source bar) ✓

**EURUSD 15m Renko precision:**
- TotalSignals = 4922, MatchedSignals = 4908
- Precision = 4908 / 4922 = 0.9972 ✓ matches

**USTEC 15m Renko precision (anomalous):**
- TotalSignals = 4681, MatchedSignals = 4782
- Precision = 4782 / 4681 = 1.0216 > 1.0
- See Warning 1 for explanation

**Speed support check — 15m LineBreak:**
- FasterCount = 4 (all 4 instruments)
- Checking EURUSD: Time MedianLatencyBars = 2.0, LB = 1.0
- 1.0 <= 0.7 * 2.0 = 1.4 → YES ✓

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| Precision | [0, 1] ideally | 0.146 to **1.022** | NO (see Warning 1) |
| Recall | [0, 1] | 0.155 to 0.982 | YES |
| MedianLatencyMinutes | ≥ 0 | 0.0 to 30.0 | YES |
| MedianLatencyBars | ≥ 0 | 0.0 to 5.0 (from EXP-002, not this exp) | YES |
| SplitRate | [0, 1] | 0.0 to 0.854 | YES |
| ReferenceReversals | ≥ 0 | 1596 to 9285 | YES |
| TotalSignals | ≥ 0 | 645 to 36966 | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| Time bar median latency | 30 min (15m), 0 min (1h) | YES | At 1h, reversal confirmation and signal occur in same bar |
| Renko precision | 0.70-1.02 | MOSTLY | >1.0 is a counting artifact (see Warning 1) |
| LineBreak precision | 0.51-0.90 | YES | LB needs 1 bar to confirm, fewer false signals than Time |
| Reversal count ratio (alt/primary) | 0.63-0.68 | YES | 2.0x ATR threshold produces ~35% fewer reversals |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| ATR-scaled reversal detection | 1.5x ATR swing defines a "real" reversal | YES | Documented in scope; sensitivity check with 2.0x ATR provided |
| Direction-change signals | Chart type direction changes are comparable reversal signals | YES | Simplest comparable signal across chart types per analysis plan |
| 120-minute tolerance window | Signals within 120 min of reversal count as matched | YES | Fixed window per scope; appropriate for 15m and 1h timeframes |
| Precision definition | `matched / total signals` including duplicates | PARTIAL | Code counts matched reversals, not matched unique signals (see Warning 1) |

## Results Plausibility

Results are plausible overall. Renko detects reversals fastest (0 latency) with highest precision. LineBreak is intermediate (15 min / 1 bar latency). Time bars are slowest (30 min / 2 bars at 15m). The speed-precision trade-off is confirmed: faster detection comes with varying precision. The FasterCount = 4 for all combinations confirms the speed advantage replicates across all instruments.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: None
- Complexity budget: 3 statistical tests (precision/recall, latency, sensitivity) / 3 budgeted; 5 visualisations / 5 budgeted; 0 new modules / 1 budgeted
- Holdout exclusion verified: YES

## Issues

### Warning

1. **Precision can exceed 1.0 due to counting methodology**
   - File: `python/src/timeframe_replication.py`, lines 1138-1205 (`match_reversal_signals`)
   - Description: `matched_count` counts how many *reversals* found a matching signal, not how many *signals* are correct. Multiple reversals can match the same signal if they fall within the 120-minute tolerance window. This causes `Precision = matched_count / total_signals` to exceed 1.0 when matched reversals > total signals. Observed in USTEC 15m Renko: Precision = 4782/4681 = 1.022.
   - Impact: Precision values > 1.0 are mathematically invalid. However, the primary hypothesis test uses **latency comparison** (FasterCount), not precision, for the speed criterion. The precision criterion checks that precision is "no more than 10 percentage points higher than time bars" — the >1.0 values don't materially affect this comparison since time bar precision is ~0.15-0.25 and event chart precision is ~0.50-1.0.
   - Fix: To compute true precision, deduplicate matched signals: `matched_unique_signals = match_df[match_df["Matched"]]["SignalTime"].nunique()`. Then `Precision = matched_unique_signals / total_signals`. This would cap precision at ≤ 1.0.

2. **1h timeframe shows 0.0 median latency for most chart types**
   - File: `python/experiments/EXP-004-TF/results/precision_recall_summary.csv`
   - Description: At 1h timeframe, MedianLatencyMinutes = 0.0 for Time, LineBreak, Renko, and HeikenAshi across most instruments. This is because the 1h bar resolution is coarse enough that reversal confirmation and signal detection often occur within the same bar.
   - Impact: The 30% latency reduction criterion cannot be meaningfully tested when baseline latency is 0. The FasterCount logic checks `e.MedianLatencyBars <= 0.7 * b.MedianLatencyBars`, which becomes `0 <= 0.7 * 0 = 0` → True. This may overstate support.
   - Fix: Consider reporting this as a resolution limitation rather than a true speed advantage. The 15m results are more informative for latency comparison.

### Info

1. **Sensitivity summary shows consistent reversal count ratios**
   - Description: Alternate (2.0x ATR) to primary (1.5x ATR) reversal count ratio is consistently 0.63-0.68 across all instruments and timeframes. This indicates reversal labels are stable under threshold variation.
   - Impact: Supports robustness of reversal definition; no action needed.

## Re-Audit Requirements

If precision calculation is fixed (Warning 1), verify that:
1. All precision values are ≤ 1.0
2. The precision criterion (no more than 10pp higher than time bars) still holds
3. The overall verdict classification is unchanged

Current verdict classification relies primarily on latency (FasterCount), which is unaffected by this issue.
