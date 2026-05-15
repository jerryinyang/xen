# Audit Report: Experiment EXP-001

## Summary
- **Verdict**: CONDITIONAL PASS
- **Critical Issues**: 2
- **Warnings**: 4
- **Info Notes**: 4

## Code Review
| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `run_experiment.py` | Correctness | PASS | Ghost-rate, entropy, bootstrap, and verdict logic arithmetically correct. |
| `run_experiment.py` | Edge cases | PASS | Empty DataFrames, all-identical closes, and single-row cases handled with explicit guards. |
| `run_experiment.py` | Type safety | PASS | Type hints present on all public functions; pandas/polars/numpy types used consistently. |
| `run_experiment.py` | NaN handling | PASS | `fill_null`, `drop_nulls`, and `np.isfinite` checks prevent silent NaN propagation. |
| `run_experiment.py` | Holdout exclusion | PASS | Only `scan.head(analysis_rows)` is collected; final 30 % is never loaded or inspected. |
| `run_experiment.py` | Docstrings | PASS | All public functions have Parameters/Returns docstrings. |
| `linebreak_generator.py` | Correctness | PASS | Deterministic, streaming-compatible, produces `SourceCloseTime`. |
| `renko_generator.py` | Correctness | PASS | Deterministic, uses real ATR, produces `SourceCloseTime`; multi-brick-per-bar behaviour is by design. |
| `heiken_ashi_generator.py` | Correctness | PASS | Exposes `RealClose`/`RealHigh`/`RealLow`; synthetic-price discipline observed by caller. |
| `time_alignment.py` | Correctness | PASS | Microsecond cast ensures join compatibility across datetime precisions. |

## Numerical Validation

### Spot Checks

**Spot check 1 — EURUSD LineBreak3 ghost rate (0.0)**  
The LineBreak generator creates a new line only when the source `Close` strictly exceeds the previous line’s `Close` (uptrend) or strictly falls below it (downtrend), or on a reversal. Therefore the `RealClose` difference between any two consecutive LineBreak lines is always strictly positive. With `min_tick` > 0, the condition `close_diff < min_tick` is never satisfied, so the ghost rate must be exactly 0.0. The CSV reports 0.0. **Match.**

**Spot check 2 — LineBreak3 vs Time ghost-rate reduction mean**  
Ghost diffs (Time − LineBreak3) per instrument:  
- EURUSD: 0.0899108275 − 0.0 = 0.0899108275  
- XAUUSD: 0.0179023946 − 0.0 = 0.0179023946  
- BTCUSD: 0.0034528357 − 0.0 = 0.0034528357  
- USTEC: 0.0261251401 − 0.0000093221 = 0.0261158180  
Mean = (0.0899108275 + 0.0179023946 + 0.0034528357 + 0.0261158180) / 4 = **0.0343454690**.  
`bootstrap_results.csv` reports `MeanDiff = 0.03434546896723027`. **Match to 1e-15.**

**Spot check 3 — Renko EURUSD ghost-reduction relative**  
Time ghost = 0.0899108275; Renko ghost = 0.1335562731.  
Relative reduction = (0.0899108275 − 0.1335562731) / 0.0899108275 = **−0.4854303622**.  
`threshold_evaluation.csv` reports `−0.4854303622460253`. **Match.**

### Range Checks
| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| GhostRate | [0, 1] | 0.0 – 0.1336 | YES |
| DirectionalEntropy | [0, 1] | 0.9970 – 0.99998 | YES |
| MedianAbsMovement | ≥ 0 | 5.0e-05 – 39.59 | YES |
| BarsPerDay | ≥ 0 | 147.4 – 1212.7 | YES |
| GhostReductionRelative | (−∞, 1] | −33.31 – 1.0 | YES |
| EntropyIncreaseRelative | (−∞, ∞) | −0.0020 – 0.0058 | YES |

### Statistical Sanity
| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| LineBreak3 ghost-rate reduction mean | 0.0343 | YES | Driven entirely by EURUSD (0.0899); other instruments have tiny baselines. |
| Renko ghost-rate reduction mean | −0.0830 | YES | Negative because Renko ghost rate is mechanically higher than Time (see Critical Issue #2). |
| Entropy increase mean (all types) | 0.0007–0.0018 | YES | Tiny because entropy is already near the binary maximum of 1.0. |
| Bootstrap CI width (n=4) | 0.003–0.060 | YES | Coarse but expected with only 4 instruments. |

## Assumption Validation
| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Bootstrap CI | Paired differences are exchangeable | PARTIAL | n=4 gives only 256 unique resamples; CI is valid but low-resolution. |
| Ghost-rate definition (Time/HA) | Range or close-diff < min_tick captures “empty” bars | YES | Implemented exactly as specified in scope. |
| Ghost-rate definition (Event) | Zero real-price movement between adjacent SourceCloseTime-aligned closes captures “empty” bars | NO | For Renko, multiple bricks per source bar share the same `RealClose`, making all but the first brick in the sequence “ghost” by construction. This is a structural artifact, not a measure of information content. |
| Entropy threshold | 10 % increase over Time bars is achievable | NO | Baseline entropy is 0.994–0.9998; a 10 % increase requires >1.09, which exceeds the binary Shannon maximum of 1.0. The success criterion is mathematically impossible. |

## Results Plausibility
All outputs fall within expected domain ranges. Directional entropy values are all near 1.0, reflecting balanced up/down sequences. Ghost rates for Line Break are exactly 0 (mechanically guaranteed by the generator). Renko ghost rates are elevated (~10–13 %) because consecutive bricks from the same source bar share an identical `RealClose`, producing zero real-price movement. Heiken Ashi ghost rates identically match Time-bar ghost rates because HA is a 1:1 real-price transformation. The `REFUTED` verdict is arithmetically consistent with the computed thresholds and bootstrap intervals.

## Scope Compliance
- Analysis plan followed: **YES**
- Deviations: **none**
- Complexity budget: 2 / 2 statistical metrics (ghost-rate reduction & entropy increase; applied across 3 event types), 4 / 4 visualisations, 1 / 1 new code module (`run_experiment.py`).
- Holdout exclusion verified: **YES** — only `head(analysis_rows)` is ever collected; final 30 % is never loaded, inspected, or summarised.

## Issues

### Critical
1. **Entropy success threshold is mathematically impossible**
   - File: `python/experiments/EXP-001/scope.md`
   - Description: The scope requires directional entropy per bar to be “at least 10 % higher than time bars.” Baseline time-bar entropy across all four instruments is 0.994–0.9998 (bits, base-2). A 10 % relative increase demands values of ~1.09–1.10, which exceeds the theoretical maximum of 1.0 for a binary variable. Consequently the “Evidence FOR” criterion can never be satisfied, structurally predetermining a REFUTED verdict regardless of data.
   - Impact: The experiment is designed with unattainable success criteria; the hypothesis is untestable as stated.
   - Fix: Redefine the entropy criterion to respect the [0,1] bound. Options: (a) absolute increase threshold (e.g., ≥ 0.01 bits), (b) percentage of remaining headroom (e.g., baseline + 0.5 × (1 − baseline)), or (c) remove entropy from the composite threshold and rely on ghost rate alone.

2. **Renko ghost-rate definition structurally inflates ghost count**
   - File: `python/experiments/EXP-001/scope.md` (definition), `python/experiments/EXP-001/code/run_experiment.py`, lines 232–243
   - Description: The scope defines event-bar ghosts as “zero real-price movement between adjacent SourceCloseTime-aligned closes.” Because the Renko generator can emit multiple bricks from a single source bar, all bricks after the first in such a sequence share the same `SourceCloseTime` and identical `RealClose`. Their consecutive real-price differences are therefore zero, and they are all counted as ghost bars. This is a construction artifact, not a reflection of low information density.
   - Impact: Renko is mechanically disadvantaged in the ghost-rate comparison, biasing the hypothesis verdict against it. The observed negative ghost-rate reduction for Renko is driven by this definition, not by market behaviour.
   - Fix: Clarify in the scope whether Renko ghosts should be evaluated per-source-bar (first brick only) or using construction-close differences for a Renko-specific ghost metric, while maintaining synthetic-price discipline for return-like quantities.

### Warning
1. **`head` applied before chronological sort in data loader**
   - File: `python/experiments/EXP-001/code/run_experiment.py`, line 111
   - Description: `load_analysis_timebar_data` calls `scan.head(analysis_rows).collect().unique().sort("CloseTime")`. The `head` is applied on the lazy scan before sorting. If the underlying Parquet file is not stored in strict chronological order, or if multiple files are read with interleaved row groups, the first 70 % of physical rows may not coincide with the first 70 % of chronological time.
   - Impact: Risk of non-chronological truncation or, in pathological cases, holdout leakage.
   - Fix: Add `.sort("CloseTime")` to the lazy plan before `.head(analysis_rows)`.

2. **`.unique()` silently alters analysis-set cardinality**
   - File: `python/experiments/EXP-001/code/run_experiment.py`, line 111
   - Description: After truncation, `.unique()` is called without subset columns. If duplicate rows exist, the analysis set shrinks below the mandated 70 % cutoff without warning.
   - Impact: Minor row-count drift; could violate holdout rules if late chronological rows are among the duplicates dropped.
   - Fix: Remove `.unique()` or explicitly justify and document why deduplication is safe.

3. **LineBreak5 evaluated but excluded from primary verdict**
   - File: `python/experiments/EXP-001/code/run_experiment.py`, line 929
   - Description: The scope and analysis plan designate LineBreak3 and Renko as the primary event types for the hypothesis verdict. LineBreak5 is generated, its metrics are computed, and it appears in the threshold table, but it is never considered in `decide_hypothesis_verdict`.
   - Impact: No impact on verdict correctness, but consumes complexity budget and cognitive overhead for a non-contributing chart type.
   - Fix: Either promote LineBreak5 to primary status or remove it to stay within the stated complexity budget.

4. **Bootstrap with n=4 yields coarse discrete intervals**
   - File: `python/experiments/EXP-001/code/run_experiment.py`, lines 412–450
   - Description: With only 4 instruments, there are 4⁴ = 256 possible bootstrap resamples. Running 10 000 iterations produces heavy duplication, so the percentile CIs are coarse and potentially unstable at the boundaries.
   - Impact: CI boundaries have limited resolution; small perturbations in data could shift the excludes-zero flag.
   - Fix: Document the limitation; consider exact enumeration or increasing `N_BOOTSTRAP` for smoother quantiles.

### Info
1. Heiken Ashi ghost rate identically equals Time-bar ghost rate because HA is a 1:1 transformation using the same real prices. This is expected behaviour.
2. All directional-entropy values exceed 0.997, indicating near-perfect up/down balance across every instrument and chart type.
3. No instrument processing failures occurred (`instrument_failures.csv` is empty).
4. The `REFUTED` verdict in `hypothesis_verdict.csv` is arithmetically correct given the computed thresholds and bootstrap intervals, even though the underlying scope makes a “SUPPORTED” outcome impossible.

## Re-Audit Requirements
To advance from CONDITIONAL PASS, the following must be addressed and verified:

1. **Revise the entropy success criterion in `scope.md`** so that it is mathematically attainable (e.g., absolute increase ≥ 0.01 bits or a relative threshold that respects the 1.0 ceiling). Re-run the experiment and confirm that the new threshold is satisfiable by at least one synthetic dataset where event-bar entropy is artificially set to 1.0.
2. **Clarify the Renko ghost-bar definition in `scope.md`**. Decide whether Renko ghosts should be counted (a) per-source-bar (only the first brick per timestamp), (b) by construction-close differences, or (c) left as-is with an explicit caveat. If the definition changes, re-run and verify that Renko ghost rates shift into a plausible range relative to Time bars.
3. **Fix data-loader ordering** by applying `.sort("CloseTime")` before `.head(analysis_rows)` in `load_analysis_timebar_data`. Re-run and verify that `validation_table.csv` shows identical `AnalysisRows` and chronological start/end times.
4. **Remove or justify `.unique()`** in the data loader. If removed, re-run and confirm no duplicate-related failures.

Once the scope revisions are approved and the code fixes are applied, re-execute the pipeline and produce a new audit request.
