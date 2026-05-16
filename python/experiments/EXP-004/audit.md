# Audit Report: Experiment EXP-004

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 1
- **Info Notes**: 3

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| run_experiment.py | Correctness | PASS | Event-matching logic processes each reversal once per direction; latency computed as `(SignalTime - ReversalTime) / timedelta64(1, "m")` |
| run_experiment.py | Edge cases | PASS | Empty DataFrames handled in `match_signals_to_reversals`, `extract_direction_changes`, `compute_metrics`; zero-denominator guards present |
| run_experiment.py | Type safety | PASS | Public functions have type hints; `np.ndarray | None` for optional ATR |
| run_experiment.py | NaN handling | PASS | `np.isnan` checks in latency loop; `drop_nulls()` before latency numpy conversion; zero-baseline returns 0.0 not NaN for precision |
| run_experiment.py | Holdout exclusion | PASS | `scan.slice(0, int(total_rows * 0.7))` — lazy scan, sort, then slice; holdout never materialized |
| run_experiment.py | Loader ordering | PASS | `pl.scan_parquet` with column projection (`TIMEBAR_COLUMNS`), sorted by `CloseTime`, sliced before `.collect()` |
| run_experiment.py | Memory/performance | PASS | Lazy scan with column projection; plotting uses aggregated summaries (latency_records, pr_df) not raw event tables; timeline plot bounded to a single cluster window |
| run_experiment.py | Logging/output | PASS | Concise per-instrument progress; hypothesis summary printed with all decision-relevant numbers |
| run_experiment.py | Organization/import side effects | PASS | Imports grouped (stdlib → third-party → local); constants at top; `PLOTS_DIR`/`RESULTS_DIR` created only in `main()` |
| run_experiment.py | Plot data reuse | PASS | All 5 plots built from records accumulated during the analysis pass; no repeated generator calls or data loads |
| run_experiment.py | Docstrings | PASS | All public functions have docstrings with Parameters and Returns sections |

## Numerical Validation

### Spot Checks

**EURUSD Time precision**: `Matched=119162, SignalCount=431323`. Precision = 119162/431323 = 0.27627. Matches output 0.2762709153001347. PASS.

**EURUSD LineBreak precision**: `Matched=40859, SignalCount=40885, False=25`. Precision = 40859/40885 = 0.999364. Matches output. PASS.

**EURUSD Renko recall**: `Matched=89405`. Total real reversals = 119207 (from sensitivity PrimaryCount). Recall = 89405/119207 = 0.749998. Matches output 0.749997902807721. PASS.

**Latency improvement sign**: Time median = 2.0 min, Renko median = 103.0 min. Improvement = (2.0 - 103.0) / 2.0 = -50.5 (negative = slower). Support summary correctly shows `FasterCount=0`. PASS.

**False count arithmetic** (EURUSD Time): `SignalCount=431323, Matched=119162, Duplicates=311859`. False = 431323 - 119162 - 311859 = 302. Matches output. PASS.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| Direction | {+1, -1} | {-1, 1} | YES |
| Precision | [0, 1] | [0.256, 0.9997] | YES |
| Recall | [0, 1] | [0.343, 1.0] | YES |
| MedianLatency | >= 0 | [2.0, 111.0] | YES |
| SplitRate | [0, 1] | [0.0, 0.851] | YES |
| SourceCount | >= 0 | Verified via generator schemas | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| Tail probability (LineBreak combined) | 1.0 | YES | 0 of 4 instruments meet combined rule; P(X >= 0 | n=4, p=0.5) = 1.0 |
| Sensitivity overlap (all instruments) | 1.0 | YES | 120-min tolerance is wide; 1.5x and 2.0x ATR reversals occur on same underlying price series |
| Median confirmation shift | 1.0 min | YES | Alternate reversals typically confirm 1 min after primary (next bar) |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| ATR-scaled swing detector | ATR > 0 for valid reversal detection | YES | `compute_atr` returns NaN for first `period-1` values; loop skips NaN/<=0 ATR |
| Event matching within 120-min window | Tolerance is wide enough for cross-chart-type comparison | YES | All chart types produce signals within window; unmatched reversals tracked |
| Direction-change as reversal signal | Direction column is int {+1, -1} | YES | Verified in generator schemas and `extract_direction_changes` output |
| Exact binomial tail for decision rule | Instruments are exchangeable under null | PARTIAL | Instruments differ in volatility/liquidity; tail probability is conservative upper bound |

## Results Plausibility

The results are internally consistent and domain-plausible:

1. **Time bars have very low median latency (2.0 min)** because the swing reversal detector on 1-minute bars confirms reversals on nearly every bar — the ATR-scaled threshold is crossed frequently on 1-minute data.
2. **Event-based charts have much higher latency (101-111 min)** because they emit fewer direction-change events; a direction change on a LineBreak or Renko chart requires a larger price move, so signals lag behind the 1-minute reversal reference.
3. **Event-based charts have much higher precision (~99.9%)** because they emit far fewer signals relative to the reversal count — most signals do match a reversal, but many reversals go unmatched (low recall).
4. **Heiken Ashi is intermediate** — every source bar produces an HA candle, so direction changes are more frequent than event charts but less frequent than time bars.

These patterns are consistent with the known characteristics of each chart type.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: None material. Analysis plan mentions "bootstrap percentile intervals" but code uses exact binomial tail probabilities for the discrete 3-of-4 decision rule — this is a more rigorous approach for the specific hypothesis test.
- Complexity budget: 3 statistical evaluations / 3 budgeted (event matching + precision/recall + sensitivity), 5 plots / 5 budgeted, 0 new modules / 1 budgeted (all code in single run_experiment.py)
- Holdout exclusion verified: YES

## Issues

### Critical

None.

### Warning

1. **Sensitivity check has limited discriminative power**
   - File: `run_experiment.py`, `evaluate_reversal_stability()` (line 592-629)
   - Description: All four instruments show `PrimaryOverlapRate=1.0`, `AlternateOverlapRate>=0.99999`, and `MedianConfirmationShiftMinutes=1.0`. The 120-minute tolerance window is so wide relative to 1-minute bar spacing that nearly every reversal at one threshold finds a match at the other threshold.
   - Impact: The sensitivity check does not meaningfully test whether reversal labels are stable — it confirms only that both thresholds detect reversals in the same general time regions. A narrower tolerance (e.g., 10-30 minutes) would provide a more discriminative stability test.
   - Fix: Consider reducing the tolerance for the sensitivity overlap check, or report the distribution of time gaps between primary and alternate reversals rather than a binary overlap rate.

### Info

1. **ATR method differs from Wilder's smoothed ATR** — `compute_atr` uses a simple rolling mean of True Range. This is acceptable per scope.md which specifies "rolling ATR-scaled directional movement" without mandating a specific ATR variant. The simpler method is sufficient for a reversal threshold.

2. **Analysis plan mentions bootstrap intervals but code uses exact binomial tail** — The analysis-plan.md references "bootstrap percentile intervals" for latency uncertainty, but the implementation uses `exact_tail_probability_at_least()` for the discrete 3-of-4 instrument decision rule. This is a defensible substitution: the decision rule is a count-of-successes test, and the exact binomial tail is more appropriate than bootstrap for this discrete hypothesis.

3. **No train/test split within analysis set** — The code uses the full analysis set (first 70% of data) without a nested 70/30 split. This is correct and consistent with scope.md: "No nested train/test split is used because this experiment fits no predictive model."

## Re-Audit Requirements

None — verdict is PASS. No fixes required.
