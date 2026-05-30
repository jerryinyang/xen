# Audit Report: Experiment EXP-036

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

EXP-036 is auditable as executed. The code follows the approved scope: strict `1h`/`4h` aggregation, Prior-Range Location fixed at lookback `20` and buckets `0.20/0.80`, real-OHLC executable returns, middle-bucket `mu_mid` as the neutral baseline, prior-bar momentum sign as the matched control, and episode-level bootstrap inference. The result files support the mechanical `AGAINST` verdict.

## Code Review

| File | Check | Verdict | Notes |
| --- | --- | --- | --- |
| `python/experiments/EXP-036/code/run_experiment.py` | Correctness | PASS | `_build_cell` loads holdout-excluded bars, strict-aggregates, features, and return columns in the planned order (lines 188-202). |
| `python/experiments/EXP-036/code/run_experiment.py` | Edge cases | PASS | Empty aggregated frames, missing forward bars, first-20 prior-range rows, and nonpositive range denominators are handled explicitly. |
| `python/experiments/EXP-036/code/run_experiment.py` | Type safety | PASS | Public helpers carry useful type hints; dataclasses define the cell and episode aggregate contracts. |
| `python/experiments/EXP-036/code/run_experiment.py` | NaN handling | PASS | Return eligibility requires finite forward returns; degenerate prior ranges are assigned null buckets and excluded from episodes. |
| `python/experiments/EXP-036/code/run_experiment.py` | Holdout exclusion | PASS | Uses `load_analysis_timebars`; `python/src/ict_timebar.py` sorts by `CloseTime`, slices first 70%, then collects analysis rows (lines 84-95). |
| `python/experiments/EXP-036/code/run_experiment.py` | Loader ordering | PASS | `aggregate_ohlc` receives only the holdout-excluded 1-minute frame and sorts by `CloseTime` internally. |
| `python/experiments/EXP-036/code/run_experiment.py` | Memory/performance | PASS | Bootstrap is chunked by `BOOTSTRAP_CELL_BUDGET`; plots use bounded summary metrics only. |
| `python/experiments/EXP-036/code/run_experiment.py` | Logging/output | PASS | Logging is concise and outputs only `metrics_table.csv`, `gap_diagnostics.csv`, `verdict.json`, and four plots. |
| `python/experiments/EXP-036/code/run_experiment.py` | Organization/import side effects | PASS | Imports/path setup/constants/helpers/orchestration are separated; output directories are created inside `run_experiment()` only (lines 691-694). |
| `python/experiments/EXP-036/code/run_experiment.py` | Plot data reuse | PASS | Plot helpers reuse computed `metrics`; no reload or reaggregation for plotting. |
| `python/experiments/EXP-036/code/run_experiment.py` | Docstrings | PASS | Core computation and orchestration helpers have orienting docstrings. |

## Numerical Validation

### Spot Checks

1. **Neutral contrast recomposition**: For `XAUUSD 1h Test next_bar`, `metrics_table.csv` reports:
   - `Rows_top = 1224`, `top_excess_pt = 0.0001925052`
   - `Rows_bottom = 525`, `bottom_excess_pt = -0.0000682894`
   - Reported `neutral_pt = 0.0001142221`

   Recomputed pooled neutral contrast:

   ```text
   (1224 * 0.0001925052 + 525 * -0.0000682894) / (1224 + 525)
   = 0.0001142221
   ```

   This matches the table to numerical precision.

2. **Adjudicability floors**: All 32 `(instrument, timeframe, segment, horizon)` rows have `neutral_adjudicable=True` and `control_adjudicable=True`. Minimum post-filter counts are above the predeclared floors:
   - Train: minimum state rows `326`, minimum state episodes `89`
   - Test: minimum state rows `118`, minimum state episodes `35`

3. **Mechanical verdict check**:
   - Next-bar: no test-segment `Delta_neutral` CI has lower bound above zero.
   - Next-bar matched control: only `XAUUSD 1h` has positive test CI and positive train point estimate.
   - Four-bar: only `XAUUSD 1h` passes both `Delta_neutral` and `Delta_control`.
   - Therefore neither next-bar edge nor horizon-dependent differentiation reaches the `>=2` distinct-instrument gate.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
| --- | --- | --- | --- |
| State counts | Above scoped floors where adjudicated | All rows adjudicable; min test rows `118`, min test episodes `35` | YES |
| `Delta_neutral` / `Delta_control` | Finite real-valued log-return differences | All reported point estimates and CIs finite | YES |
| Bootstrap intervals | Lower <= point <= upper | Verified by table scan; no inverted intervals found | YES |
| Entry gaps | Nonnegative minutes; nominal median expected | Median gaps are nominal (`60` or `240`); max gaps finite | YES |
| Plot files | Nonempty PNGs | Four PNGs render with nonzero dimensions | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
| --- | ---: | --- | --- |
| `XAUUSD 1h Test next_bar Delta_control` | `+0.000153`, CI `[+0.000052, +0.000252]` | YES | The only next-bar matched-control positive test result; it fails edge status because `Delta_neutral` does not pass. |
| `XAUUSD 1h Test four_bar Delta_neutral` | `+0.000482`, CI `[+0.000088, +0.000855]` | YES | Supports one horizon-dependent cell only, below the distinct-instrument gate. |
| `BTCUSD 4h Train next_bar Delta_control` | `+0.000864`, CI `[+0.000152, +0.001590]` | YES | Strong train result does not replicate in test; train-only positives do not gate. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
| --- | --- | --- | --- |
| Chronological split | Financial data must be split by time, not randomly | YES | `_add_segment` labels sorted aggregated rows by chronological position; pre-execution review accepted equivalence to cutoff timestamp assignment. |
| Prior-range feature | Uses only information available at bar close | YES | `rolling_max/min(...).shift(1)` uses the prior 20 completed same-timeframe bars, then bar `i` close assigns the state. |
| Executable returns | Entry occurs after descriptor observation | YES | Returns use `Open_{i+1}` to `Close_{i+1}` or `Close_{i+4}`, never `Close_i` as an entry price. |
| Episode bootstrap | Rows inside persistent states are serially dependent | YES | Resampling unit is independent state episodes; row bootstrap is diagnostic only. |
| Real-price outcome discipline | Returns must use real OHLC | YES | No HA/Renko chart prices are in scope or loaded; returns are from strict aggregated real `Open`/`Close`. |

## Results Plausibility

The signs and uncertainty are plausible for executable `1h`/`4h` open-to-close log returns. Effects are small in absolute return terms, and CIs widen materially at `4h` where fewer episodes are available. Gap-spanning entries are material at `4h` (`20.6%` to `25.2%`) and should be treated as an executability caveat, but the scope predeclared retaining them for EXP-036 and deferring gap-exclusion robustness to a future robustness experiment only if a descriptor survived.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: one non-blocking presentation deviation. The fourth plot visualizes the 4-bar `Delta_neutral` panel only; 4-bar `Delta_control` is still fully present in `metrics_table.csv`, reflected in `verdict.json`, and used by the mechanical verdict.
- Complexity budget: 2 statistical test families / 3 allowed, 4 plots / 4 allowed, 0 new modules / 1 allowed.
- Holdout exclusion verified: YES
- Real-price outcome discipline verified: YES
- Timestamp alignment verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **4-bar control visualization is tabular/verdict-only.**
   - File: `python/experiments/EXP-036/code/run_experiment.py`, lines 741-743
   - Description: Plot 4 renders the 4-bar `Delta_neutral` panel. The planned 4-bar `Delta_control` visual is not a separate figure.
   - Impact: No impact on results or verdict; the four-bar control gate is in `metrics_table.csv` and `verdict.json`.

2. **Gap-spanning entries are nontrivial at 4h.**
   - File: `python/experiments/EXP-036/results/gap_diagnostics.csv`
   - Description: `4h` gap-spanning shares range from `0.206` to `0.252`.
   - Impact: This is a scoped executability caveat, not a defect. EXP-036 retained gap-spanning entries by predeclaration.

## Re-Audit Requirements

None. No critical or warning issues block interpretation.
