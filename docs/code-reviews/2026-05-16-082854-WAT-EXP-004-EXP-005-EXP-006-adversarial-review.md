# Adversarial Review: EXP-004, EXP-005, EXP-006

**Date:** 2026-05-16 08:28:54 WAT  
**Reviewer:** Codex  
**Scope:** Static pre-execution review of scope, analysis plan, implementation, and pre-execution governance artifacts. `results/` artifacts are absent or empty for all three experiments, so this review does not claim numerical-result validation.

## Artifacts Reviewed

- `python/experiments/EXP-004/scope.md`
- `python/experiments/EXP-004/analysis-plan.md`
- `python/experiments/EXP-004/code/run_experiment.py`
- `python/experiments/EXP-004/governance/pre-execution-review.md`
- `python/experiments/EXP-005/scope.md`
- `python/experiments/EXP-005/analysis-plan.md`
- `python/experiments/EXP-005/code/run_experiment.py`
- `python/experiments/EXP-005/governance/pre-execution-review.md`
- `python/experiments/EXP-006/scope.md`
- `python/experiments/EXP-006/analysis-plan.md`
- `python/experiments/EXP-006/code/run_experiment.py`
- `python/experiments/EXP-006/governance/pre-execution-review.md`
- `docs/experiments-docs/checkpoints/2026-05-14-001-chart-type-validation/design.md`
- `.agents/skills/research-pipeline/_pipeline-config.md`
- `.agents/skills/research-pipeline/references/governance-constraints.md`
- `.agents/skills/experiment-developer/references/code-conventions.md`
- `python/src/linebreak_generator.py`
- `python/src/renko_generator.py`
- `python/src/heiken_ashi_generator.py`
- `python/src/time_alignment.py`

## EXP-004

**Content type:** Empirical-study implementation review  
**Review lenses:** Methodology correctness > scope/design compliance > code quality > performance/memory

```json
[
  {
    "id": "EXP004-F01",
    "severity": "Major",
    "title": "Precision excludes duplicate signals even though duplicates are part of the stated trade-off",
    "evidence": "`python/experiments/EXP-004/code/run_experiment.py` lines 398-422 count duplicate signals separately, but lines 481-485 define `Precision = matched / (matched + false_count)`. The scope's core decision rule is explicitly about latency versus precision in `scope.md` lines 24-26.",
    "impact": "Event-based chart types can emit many extra same-direction signals around one real reversal and still look artificially precise because those duplicate signals never enter the denominator. That biases the experiment toward concluding that a faster chart preserved precision when it may only have produced more redundant signals.",
    "fix": "Either redefine precision as `matched / (matched + false_count + duplicate_count)` for the main hypothesis test, or report two metrics with distinct names: one for match precision and one for total signal precision. The scope and interpretation logic should then reference the intended metric explicitly."
  },
  {
    "id": "EXP004-F02",
    "severity": "Major",
    "title": "The required reversal-label sensitivity check is computed only as a count printout",
    "evidence": "`scope.md` line 26 makes label instability a named inconclusive condition, and line 36 requires a documented thresholding rule. The code computes `alt_reversals` at lines 871-881 in `run_experiment.py`, but lines 1047-1053 only print primary versus alternate counts and never measure overlap, timing drift, or metric instability.",
    "impact": "The experiment cannot actually determine whether its reversal labels are stable enough to trust. A materially different reversal set under a modest threshold change could invalidate the speed/precision comparison, yet the current implementation would still proceed with no failing flag.",
    "fix": "Add an explicit stability check between primary and alternate reversal sets: overlap rate, unmatched rate, and downstream latency/precision deltas. If the stability rule fails, write a machine-readable inconclusive flag into the results."
  },
  {
    "id": "EXP004-F03",
    "severity": "Major",
    "title": "Bootstrap uncertainty is attached to the cross-instrument mean, not to the scope's 3-of-4 support rule",
    "evidence": "`scope.md` lines 24-25 define support in terms of instrument counts: at least 3 of 4 instruments meeting the latency and precision thresholds. But `bootstrap_paired_latency_ci()` in `run_experiment.py` lines 508-559 bootstraps the mean latency difference across instruments, and lines 996-1023 persist only that mean-difference interval.",
    "impact": "The reported interval does not quantify uncertainty around the actual decision rule the experiment uses. A mean effect can look clearly positive while fewer than 3 instruments satisfy the threshold, or the reverse. That makes the uncertainty output hard to reconcile with the stated hypothesis test.",
    "fix": "Tie inference to the stated rule. For example, report the raw per-instrument latency deltas plus an exact sign or permutation test over the four instruments, or bootstrap the fraction of instruments meeting the rule rather than the mean delta."
  },
  {
    "id": "EXP004-F04",
    "severity": "Minor",
    "title": "The zero-reversal early return misclassifies every signal as a duplicate instead of a false signal",
    "evidence": "In `run_experiment.py` lines 331-341, `match_signals_to_reversals()` returns `empty, 0, 0 if len(signals) == 0 else len(signals)` when either input is empty. When `len(real_reversals) == 0` and `len(signals) > 0`, that yields `false_count = 0` and `duplicate_count = len(signals)`.",
    "impact": "If an instrument produces no real reversals, the implementation understates false signals and overstates split/duplicate behaviour. That is an edge case, but it is a real correctness bug in the metric layer.",
    "fix": "Split the early return into explicit branches: no signals means `(0 false, 0 duplicate)`; no reversals but some signals means `(all false, 0 duplicate)`."
  }
]
```

The implementation is otherwise reasonably disciplined on holdout handling and data loading: it slices the first 70% lazily before collection and does not reload data solely for plotting. The main problems are metric semantics and incomplete implementation of the scope's own instability guard, not memory abuse.

## EXP-005

**Content type:** Empirical-study implementation review  
**Review lenses:** Methodology correctness > scope/design compliance > code quality > performance/memory

```json
[
  {
    "id": "EXP005-F01",
    "severity": "Major",
    "title": "The bootstrap intervals do not test the medium/high-regime hypothesis they are supposed to support",
    "evidence": "`scope.md` lines 24-26 and `analysis-plan.md` lines 27-31 make the main claim regime-specific: Line Break/Renko agreement should exceed time-bar agreement in medium and high volatility regimes. But `run_experiment.py` lines 675-686 call `bootstrap_agreement_diff()` on the full `direction_tables` without any regime filter, so the only stored intervals are aggregate intervals.",
    "impact": "The code can produce confidence intervals that look supportive even if the medium/high-regime claim fails, because the inference layer is not attached to the actual scoped hypothesis. The experiment's central decision rule is therefore under-implemented.",
    "fix": "Run `bootstrap_agreement_diff()` on regime-filtered tables for `medium` and `high`, or explicitly compute separate interval outputs per regime and use those in the support/refutation logic."
  },
  {
    "id": "EXP005-F02",
    "severity": "Major",
    "title": "Volatility regime labels use full-sample quantiles, so early labels depend on future data",
    "evidence": "`scope.md` line 18 says regime labels should use information known at or before each event timestamp. In `run_experiment.py` lines 130-153, rolling volatility is past-only, but lines 138-142 compute `q33` and `q66` from the full non-null `vol_series` across the entire analysis set before assigning low/medium/high labels.",
    "impact": "The stratification layer for the main hypothesis is contaminated by future information. Earlier events are classified using thresholds learned from later volatility observations, which breaks the stated look-ahead discipline for regime-dependent conclusions.",
    "fix": "Set tercile thresholds from a predeclared calibration segment, or use an expanding-window/rolling-threshold approach so each event's regime label is based only on information available up to that timestamp."
  },
  {
    "id": "EXP005-F03",
    "severity": "Major",
    "title": "Event alignment does not define duplicate-source denominators and allows repeated reuse of one timestamp",
    "evidence": "`python/src/renko_generator.py` lines 61-66 can emit multiple bricks for the same source bar, all carrying the same `SourceCloseTime` at lines 91-92. `build_direction_table()` in `run_experiment.py` lines 104-109 keeps every row, and `align_pairwise()` lines 228-259 matches each left-side row independently with no one-to-one constraint. The pipeline code conventions explicitly require duplicate-source event denominators to be defined.",
    "impact": "One real source minute can contribute multiple Renko observations and multiple pairwise matches, which overweights bursty event charts and makes the agreement denominator chart-type-dependent in a way the scope never defines. That weakens both methodological comparability and pipeline-compliance claims.",
    "fix": "Before pairwise comparison, collapse duplicate `SourceCloseTime` rows to one direction state per source timestamp, or at minimum report a second metric that weights each source timestamp once. If repeated same-source events are intentionally retained, the scope and results must define and defend that denominator."
  },
  {
    "id": "EXP005-F04",
    "severity": "Minor",
    "title": "Uniform 5m/15m tolerance is applied even where exact alignment is available",
    "evidence": "`scope.md` line 36 allows nearest-event matching for sparse event charts but calls for exact `CloseTime` comparisons for time-bar and Heiken Ashi alignments where possible. In `run_experiment.py`, the global tolerances at lines 37-38 are applied uniformly to every pair in lines 651-663 with no exact-match branch.",
    "impact": "For dense pairs such as time bars versus Heiken Ashi, the implementation is looser than the scoped design. In practice the impact is probably limited because those timestamps should already align exactly, but the current code does not enforce that stronger guarantee.",
    "fix": "Special-case pairs that share exact bar timestamps and use equality joins for them. Reserve nearest-neighbour tolerance windows for sparse event-based comparisons only."
  }
]
```

The strongest issue here is not memory or raw performance; the loader is lazy and the plotting conversions are bounded. The problems are methodological: the regime-specific hypothesis is only partially implemented, and the event-count denominator is underspecified for duplicate-source timestamps.

## EXP-006

**Content type:** Empirical-study implementation review  
**Review lenses:** Methodology correctness > scope/design compliance > code quality > performance/memory

```json
[
  {
    "id": "EXP006-F01",
    "severity": "Major",
    "title": "Warm-up rows with undefined rolling volatility are silently labelled as `High` regime",
    "evidence": "In `run_experiment.py` lines 108-129, `add_regimes()` computes `rolling_vol` with `min_periods=window`, so the first `window - 1` rows are null. The subsequent `when(...).then(...).when(...).then(...).otherwise('High')` chain has no null branch, and the filtered output at lines 286-290 keeps non-null `regime` rows.",
    "impact": "The early warm-up segment is mis-stratified into the `High` bucket instead of being excluded or marked unknown. That biases the regime heatmap and any regime-level distortion summaries, especially if a dataset is short enough that the warm-up rows are a meaningful share of the analysis set.",
    "fix": "Add an explicit null branch before the threshold checks, e.g. `when(rolling_vol.is_null()).then(None)` or `then('Unknown')`, and exclude those rows from regime-dependent summaries."
  },
  {
    "id": "EXP006-F02",
    "severity": "Major",
    "title": "Regime thresholds are learned from the entire analysis set, which violates the experiment's timestamp-knowable regime rule",
    "evidence": "`scope.md` line 18 requires distortion to be evaluated at each source bar's `CloseTime`, and `analysis-plan.md` line 70 says regime labels are derived from real time-bar volatility and applied by `CloseTime`. But `run_experiment.py` lines 114-121 compute tercile cutoffs from all non-null rolling-vol values in the full analysis set before assigning regimes.",
    "impact": "The aggregate distortion metrics are still valid, but the claimed regime dependence is not purely point-in-time. Earlier bars are classified with thresholds informed by later volatility, so the regime-stratified conclusions are not as look-ahead-safe as the scope says they should be.",
    "fix": "Derive the regime cutoffs from a fixed calibration segment or from expanding-window quantiles so each row's regime label uses only information available up to that row."
  },
  {
    "id": "EXP006-F03",
    "severity": "Minor",
    "title": "The analysis frame performs a redundant full join that doubles real-price columns and increases memory pressure",
    "evidence": "`build_analysis_frame()` in `run_experiment.py` lines 261-267 loads time bars into `tb`, generates Heiken Ashi into `ha`, and then joins `tb` back onto `ha` on `CloseTime`. But `python/src/heiken_ashi_generator.py` lines 50-60 already include `RealOpen`, `RealHigh`, `RealLow`, and `RealClose` in every HA row.",
    "impact": "The join adds avoidable memory and CPU cost on the full analysis slice without adding new information. On larger datasets, that is exactly the kind of full-frame duplication the pipeline's bounded-memory rule tries to avoid.",
    "fix": "Generate the analysis frame directly from the HA output plus only the extra real columns that are genuinely missing. Here, the real-price range and return metrics can be computed from the `Real*` columns already present in the HA frame."
  }
]
```

EXP-006 is the cleanest of the three on overall structure and bounded plotting, but the regime layer is not trustworthy as written. The aggregate HA-versus-real distortion metrics are conceptually aligned with scope; the regime-specific heatmap is where the implementation drifts from the pipeline's look-ahead and correctness standards.

## Cross-Experiment Summary

- All three experiments respect the global holdout at the loader level and avoid the most serious synthetic-price violations.
- The main review failures are not generic style issues. They are design-to-code mismatches in the decision logic: EXP-004's precision and sensitivity checks, EXP-005's regime-specific hypothesis implementation, and EXP-006's regime construction.
- The pre-execution governance approvals are too optimistic. Each experiment has at least one substantive issue that should be fixed before the code is treated as pipeline-compliant.
