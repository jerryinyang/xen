# Pre-Execution Review: EXP-018 — Displacement Confirmation Added to Sweeps

**Reviewer:** Research Pipeline (Stage 4 Governance)
**Date:** 2026-05-25 (post-adversarial revision)
**Supersedes:** 2026-05-25 initial APPROVE (which did not catch F03/F09/F10 from `docs/code-reviews/2026-05-25-145710-WAT-EXP-017-EXP-020-adversarial-review.md`)
**Artifacts reviewed:**
- `python/experiments/EXP-018/scope.md`
- `python/experiments/EXP-018/analysis-plan.md` (revised)
- `python/experiments/EXP-018/code/run_experiment.py` (revised)
- `python/src/ict_timebar.py`
- `docs/experiments-docs/checkpoints/2026-05-23-003-ict-one-setup-timebar-validation/design.md`

## Background — what the adversarial review caught

| Finding | Issue | Resolution in revised code |
|---|---|---|
| F03 (Major) | The original paired SweepClose-vs-DisplacementClose comparison did not answer the scope question ('does adding displacement improve sweep-only outcomes?'). It compared the same confirmed-sweep events to themselves at different entry timestamps, i.e., delay cost, not filter quality. | New primary test: `compute_filter_effects` (run_experiment.py:332-470) uses a nested-subset bootstrap to compare displacement-confirmed-sweep Hit1R_60m and median MAE_R_60m against the full EXP-015 sweep population. The paired test is retained as a delay-cost diagnostic only. |
| F09 (Major) | Verdict logic could not produce AGAINST whenever any instrument was train-positive but test-negative, even with strong test-side refutation. | Revised `evaluate_verdict` (run_experiment.py:550-605) declares AGAINST when >= 3 instruments refute on both Hit and MAE intervals on the test segment. Train-only positives no longer veto AGAINST. |
| F10 (Minor) | `add_ny_time_features` was called although no NY/macro column is read downstream. | `load_instrument_bars` (run_experiment.py:104-119) now adds Segment only via a minimal Polars `with_row_index` path. |

## 1. Scope Document

| Check | Result | Notes |
|---|---|---|
| Single falsifiable question | PASS | One H3 component test (deterministic candle/body displacement after EXP-015 failed sweeps). |
| Criteria measurable | PASS | Hit1R >= 5pp OR median MAE improvement >= 0.25R on >= 3 instruments; retention floor explicit. |
| Holdout exclusion | PASS | Scope inherits the analysis-set-only requirement; the code reads only EXP-015 outcomes and first-70% bars. |
| Real-price outcome discipline | PASS | All outcomes flow through `compute_real_price_outcome`, which uses real time-bar OHLC. |
| Phase 003 alignment | PASS | Time-bar-native H3 component test; no event-chart features, IFVG/breaker, or full-model logic. |
| Complexity budget | PASS | Two bootstrap comparison families (filter effect, paired delay), five plots, no new shared module. |

**Scope verdict: PASS**

## 2. Analysis Plan (revised)

| Check | Result | Notes |
|---|---|---|
| Comparison baseline matches scope question | PASS | Step 3 (revised) declares the full EXP-015 sweep population as the unpaired baseline and the paired DisplacementClose-vs-SweepClose as a secondary delay-cost diagnostic. This was the F03 gap. |
| Criterion form | PASS | Criteria are explicitly stated on bootstrap CI95-low, not point estimates (Hit >= 5pp, median MAE improvement >= 0.25R). |
| Sample-size cost reported before effect interpretation | PASS | Retention pct and `RetentionFloorMet` reported alongside effect sizes in `filter_effects.csv`. |
| Non-parametric methods | PASS | Bootstrap intervals only; no normality or stationarity assumptions. |
| Budget compliance | PASS | Two test families / 3 allowed, five plots / 5 allowed, one shared module unchanged. |

**Analysis-plan verdict: PASS**

## 3. Code Review

### Organization and Side Effects

| Check | Result | Notes |
|---|---|---|
| Imports → constants → helpers → plots → orchestration → `main()` | PASS | Layout consistent with EXP-017. |
| No import-time I/O side effects | PASS | Output directories created only inside `run_experiment` (run_experiment.py:740). |
| Output directories created only in orchestration | PASS | `plots_dir.mkdir` / `results_dir.mkdir` are in `run_experiment` (run_experiment.py:740-743). |

### Scope and Design Compliance

| Check | Result | Notes |
|---|---|---|
| Primary test compares against full EXP-015 sweep population | PASS | `sweeps_with_confirm` is built by left-joining a `DisplacementConfirmed` flag from `misses` onto every sweep, then `compute_filter_effects` bootstraps confirmed-subset vs full baseline (run_experiment.py:332-470, 760-775). |
| Paired test is documented as secondary diagnostic | PASS | `payload['secondary_test_definition']` (run_experiment.py:660-665) and `numerical_summary.txt` clearly label it as delay-cost, not the verdict driver. |
| Time-bar-native ICT path preserved | PASS | No Line Break, Renko, Heiken Ashi, or chart-type features. |
| No compounding with later roadmap items | PASS | No macro, FVG/IFVG, breaker, or execution-timing logic. |

### Holdout and Temporal Discipline

| Check | Result | Notes |
|---|---|---|
| Analysis-set-only loading | PASS | `load_instrument_bars` uses `load_analysis_timebars` which slices first 70% chronologically (`ict_timebar.py:84-95`). |
| Look-ahead prevention in displacement | PASS | `BodyMedian100Prior` is shifted by one bar; displacement search starts at `searchsorted(close_ns, event_ns, side="right")` (run_experiment.py:126-131). |
| Outcome window starts after entry | PASS | `compute_real_price_outcome` uses `close_ns > entry_ns` selection (`ict_timebar.py:386`). |

### Statistical Correctness

| Check | Result | Notes |
|---|---|---|
| Nested-subset dependence handled | PASS | `bootstrap_nested_difference` resamples the full baseline and recomputes the confirmed-subset statistic inside each resample (run_experiment.py:332-388). Matches the EXP-017 pattern. |
| MAE uses median statistic | PASS | `bootstrap_nested_difference(..., use_median=True)` (run_experiment.py:421). Scope criterion is on the median. |
| CI-based criteria | PASS | `HitCriterionMet` requires `CI95Low >= HIT_THRESHOLD`; `MAECriterionMet` requires `mae_ci_low >= MAE_IMPROVEMENT_THRESHOLD` (run_experiment.py:464-475). Point estimates alone cannot pass. |
| Refutation criteria | PASS | `HitNegativeRefutes` / `MAENegativeRefutes` require CI95-high strictly below threshold (run_experiment.py:476-485). |
| Ambiguous Hit1R rows excluded | PASS | `hit_group = group.loc[~group["Ambiguous60"] & ...]` (run_experiment.py:408-411). |

### Code Quality

| Check | Result | Notes |
|---|---|---|
| Public functions typed and documented | PASS | All new helpers have type hints and docstrings. |
| NaN handling explicit | PASS | Empty groups return NaN diffs; bootstrap returns NaN CIs when n < 2. |
| Plot reuse | PASS | New `plot_filter_effect_intervals` reads `filter_effects` already computed; no heavy reloads. |

## 4. Verification

- `python3 -m py_compile python/experiments/EXP-018/code/run_experiment.py` passed after revision.
- Experiment code was not executed by the reviewer.

## 5. Required Re-Execution

The previously written `python/experiments/EXP-018/results/` reflects the pre-revision code (which measured delay cost, not filter quality, and used the F09 verdict logic). It must be regenerated by running the revised `run_experiment.py` before any downstream experiment (EXP-019 in particular reads `entry_proxy_events.csv`, which is unchanged in structure but should be regenerated for consistency).

## Verdict

```text
VERDICT: APPROVE
```

The revised implementation addresses F03/F09/F10. It is scope-faithful, holdout-safe, statistically defensible on the primary metric, and consistent with the EXP-017 governance template.

## Execution Instructions

```text
Pre-execution review: APPROVED (post-adversarial revision)

Experiment: EXP-018 — Displacement Confirmation Added to Sweeps
Code:       python/experiments/EXP-018/code/run_experiment.py
Expected output: python/experiments/EXP-018/results/
                 python/experiments/EXP-018/plots/

The primary test is now an unpaired nested-subset bootstrap comparing
displacement-confirmed sweep outcomes against the full EXP-015 sweep
population on Hit1R (mean) and MAE_R (median). The paired delay-cost
diagnostic remains for reference but does not drive the verdict.

Please run the experiment code and confirm when complete.
```
