# Audit Report: Experiment EXP-007

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

The EXP-007 implementation and generated outputs are suitable for interpretation. The audit found no holdout, timestamp-alignment, synthetic-price, denominator, or numerical integrity issue that blocks results use.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/experiments/EXP-007/code/run_experiment.py` | Scope dispatch | PASS | Thin runner delegates only to `run_signal_quality_experiment("EXP-007")`. |
| `python/src/signal_quality.py` | Correctness | PASS | Implements FE, AE, precision, recall inputs, run continuation, multiplicity, missing-signal states, bootstrap comparisons, and proceed criteria. |
| `python/src/signal_quality.py` | Edge cases | PASS | Empty signal sets, absent future windows, non-finite ATR, and zero ATR are handled explicitly. |
| `python/src/signal_quality.py` | Type safety | PASS | Public helpers use type hints; dataclasses define instrument and real-price contexts. |
| `python/src/signal_quality.py` | NaN handling | PASS | Non-computable FE/AE/precision rows remain null rather than being imputed. |
| `python/src/signal_quality.py` | Holdout exclusion | PASS | `load_instrument_data()` sorts by `CloseTime`, computes the first 70 percent cutoff, and collects only `scan.slice(0, analysis_rows)`. |
| `python/src/signal_quality.py` | Loader ordering | PASS | Chronological sorting occurs before slicing; 15-minute aggregation is built only from holdout-excluded 1-minute analysis data. |
| `python/src/signal_quality.py` | Timestamp alignment | PASS | Time and Heiken Ashi signals use `CloseTime`; Line Break and Renko signals use `SourceCloseTime`. |
| `python/src/signal_quality.py` | Synthetic price discipline | PASS | All outcome metrics resolve from 1-minute real OHLC arrays in `RealPriceContext`; chart construction prices are not used for FE, AE, precision, recall, or continuation. |
| `python/src/signal_quality.py` | Memory/performance | PASS | Inputs are processed one instrument at a time; bootstrap and plotting use bounded deterministic sampling. |
| `python/src/signal_quality.py` | Logging/output | PASS | Manual-run output is concise; helper-level output is not noisy. |
| `python/src/signal_quality.py` | Organization/import side effects | PASS | Output directories are created inside experiment orchestration, not at import. |
| `python/src/signal_quality.py` | Plot data reuse | PASS | Plots use generated result tables rather than rerunning heavy loaders or chart generation. |
| `python/src/signal_quality.py` | Docstrings | PASS | Core public helpers include useful docstrings; small local helpers are readable without extra comments. |

## Numerical Validation

### Spot Checks

Manual FE/AE check for the first valid EURUSD 1-minute Time signal:

- Signal time: `2023-01-02 00:27:00`
- Direction: `+1`
- Base close: `1.07000`
- ATR at signal: `0.00009857142857142407`
- Future 60-minute high: `1.07092`
- Future 60-minute low: `1.06938`
- Manual FE: `(1.07092 - 1.07000) / ATR = 9.333333333334084`
- Stored FE_60m: `9.333333333334084`
- Manual AE: `(1.07000 - 1.06938) / ATR = 6.289855072464714`
- Stored AE_60m: `6.289855072464714`

The manual calculation matches the stored output exactly for this spot check.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|--------------|-------|
| Direction | {-1, +1} | [-1, +1] | YES |
| FE_60m | >= 0 or null | [0.0, 1281.0] | YES |
| AE_60m | >= 0 or null | [0.0, finite positive max] | YES |
| PrecisionHit_60m | {0, 1} or null | [0, 1] | YES |
| ATRAtSignal | > 0 when computable | [0.000001, 1217.287143] | YES |
| SignalMultiplicity | >= 0 | [0, 61] | YES |
| RealPriceResolved | recorded for every signal | 9,794,413 / 9,794,413 true | YES |

Null FE/AE/precision rows total 3,869 of 9,794,413 signals. These occur at early ATR warm-up or terminal forward-window boundaries and remain explicit nulls.

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|---------------------|-------|
| Bootstrap resamples | 10,000 | YES | Matches scope and analysis plan. |
| Bootstrap max sample size | 5,000 per side | YES | Bounded deterministic sampling is documented in the manifest and prevents excessive memory use. |
| Passing proceed criteria | 3 rows | YES | 15-minute Renko passes FE60 and AE60; 15-minute LineBreak passes AE60. |
| Signal-level precision | 0.818 to 0.838 weighted overall | YES | Bounded [0, 1] and close across chart types, consistent with precision criteria not driving the result. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|------------|--------|----------|
| Chronological split | First 70 percent of each source file is the analysis set | YES | `load_validation.parquet` shows expected analysis rows equal `floor(SourceRows * 0.70)` for all instruments. |
| Train calibration | Train rows are first 70 percent of analysis rows | YES | `TrainRows` equals `floor(AnalysisRows * 0.70)` for all instruments. |
| Real-price outcome measurement | Signals can resolve exactly to 1-minute real-price timestamps | YES | `RealPriceResolved` is true for all 9,794,413 signals. |
| Bootstrap comparison | Row-level samples are large enough for descriptive CIs | YES, with dependence caveat | Sample sizes are large; interpretation should avoid treating row-level bootstrap as fully independent market evidence. |
| Missing-signal accounting | Sparse event-chart emissions are represented explicitly | YES | `missing_signal_states.parquet` records missing source-bar shares for Line Break, Renko, and Heiken Ashi. |

## Results Plausibility

The outputs are plausible for the approved scope. Event charts emit far fewer signals than Time and Heiken Ashi: Line Break misses 73.7 percent of 1-minute source bars and 76.3 percent of 15-minute source bars; Renko misses 72.0 percent and 75.9 percent respectively. Weighted FE, AE, precision, and run-continuation values are finite and bounded where expected. The strongest differentiating evidence appears at 15 minutes, which is consistent with the checkpoint expectation that 1-minute and 15-minute signal profiles may differ materially.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none found
- Complexity budget: 4 comparison families / 4 budgeted, 6 plots / 6 budgeted, 1 shared module plus runner / 1 budgeted shared module plus runner
- Holdout exclusion verified: YES
- Synthetic price discipline verified: YES
- Timestamp alignment verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Proceed criteria establish differentiation, not automatic quality superiority**
   - Description: Passing criteria are driven by 15-minute FE and AE differences. Renko has lower FE and lower AE than Time at 15 minutes, so the result is a trade-off rather than a simple improvement.

2. **Row-level bootstrap dependence remains a standard interpretation caveat**
   - Description: Large overlapping forward windows mean rows are temporally dependent. This does not invalidate the pre-specified descriptive bootstrap use, but final interpretation should emphasize effect size and instrument consistency rather than treating CIs as independent-trial proof.

## Re-Audit Requirements

None.
