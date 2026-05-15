# EXP-002 Adversarial Review

**Timestamp:** 2026-05-14 23:42:01 WAT  
**Review skill:** `bmad-review-adversarial-general`  
**Pipeline context:** `research-pipeline`  
**Experiment:** EXP-002 - Volatility & Trend Regime Representation

## Scope Reviewed

This is a pre-execution review. The EXP-002 directory contains `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, and `governance/pre-execution-review.md`. It does not contain `results/`, `audit.md`, `results.md`, `report.md`, or post-experiment governance artifacts, so post-execution result integrity cannot be reviewed.

References consulted:

- `docs/references/dataset-reference.md`
- `docs/references/architecture.md`
- `python/experiments/INDEX.md`
- `docs/experiments-docs/INDEX.md`
- `docs/experiments-docs/checkpoints/2026-05-14-001-chart-type-validation/design.md`
- `python/experiments/EXP-002/scope.md`
- `python/experiments/EXP-002/analysis-plan.md`
- `python/experiments/EXP-002/code/run_experiment.py`
- `python/experiments/EXP-002/governance/pre-execution-review.md`
- `python/src/linebreak_generator.py`
- `python/src/renko_generator.py`
- `python/src/heiken_ashi_generator.py`
- `python/tests/test_chart_generators.py`

## Review Lens

Content type: empirical experiment plan plus Python implementation.  
Primary lenses: statistical validity, reproducibility, implementation correctness, and governance compliance.

```json
[
  {
    "id": "F01",
    "severity": "Critical",
    "title": "Primary success criteria are mathematically unachievable against the implemented time-bar baseline",
    "evidence": "EXP-002 success requires Line Break or Renko to have at least 20% lower hybrid rate and median transition lag than time bars (`python/experiments/EXP-002/scope.md:24`, `python/experiments/EXP-002/analysis-plan.md:42`). The implementation defines time bars and Heiken Ashi as 1:1 mappings with hybrid rate 0 by construction (`python/experiments/EXP-002/code/run_experiment.py:202-207`, `python/experiments/EXP-002/code/run_experiment.py:234-237`). For time bars, transition lag is also 0 because the first chart bar at or after a time-bar transition is the transition bar itself (`python/experiments/EXP-002/code/run_experiment.py:306-314`). Percentage improvement is set to NaN when the baseline is 0 (`python/experiments/EXP-002/code/run_experiment.py:782-788`).",
    "impact": "The experiment cannot produce SUPPORT under its stated criteria because event-based charts cannot be 20% lower than a zero baseline. Hybrid-rate and lag improvement outputs will be NaN or non-supporting for the baseline comparison, regardless of the actual chart behavior. This invalidates the core inference target before execution.",
    "fix": "Redefine the baseline metrics so the time-bar comparator can have nonzero boundary impurity and lag, or revise the hypothesis to compare event bars against a meaningful time-bar aggregation window. For example, measure purity over fixed post-transition windows, time-normalized detection delay, or event alignment quality rather than percentage reduction from a structurally zero baseline."
  },
  {
    "id": "F02",
    "severity": "Critical",
    "title": "Bootstrap output for Line Break and Renko is overwritten before saving",
    "evidence": "`bootstrap_records` is initialized inside the loop over `event_types` (`python/experiments/EXP-002/code/run_experiment.py:745-810`) and converted to `bootstrap_df` after the loop (`python/experiments/EXP-002/code/run_experiment.py:839-844`). Because the final event type is `HeikenAshi` (`python/experiments/EXP-002/code/run_experiment.py:746`), previously appended LineBreak3 and Renko bootstrap rows are discarded.",
    "impact": "The saved `bootstrap_results.csv` will omit the confidence intervals needed to evaluate the actual EXP-002 hypothesis for Line Break and Renko. This directly conflicts with the scope requirement for paired bootstrap 95% confidence intervals (`python/experiments/EXP-002/scope.md:24`) and can make the experiment appear complete while missing decisive evidence.",
    "fix": "Move `bootstrap_records: list[dict[str, Any]] = []` before the `for event_type in event_types` loop, append all event-type rows into the same list, and add a test or assertion that the output contains both `LineBreak3 vs Time` and `Renko vs Time` rows for HybridRateReduction and LagReduction."
  },
  {
    "id": "F03",
    "severity": "Major",
    "title": "Metrics are evaluated on the full analysis set, not the reserved test segment",
    "evidence": "The scope defines a nested chronological split: first 70% analysis set, then first 70% train and last 30% test (`python/experiments/EXP-002/scope.md:16`). The code creates `train_df` and `test_df` (`python/experiments/EXP-002/code/run_experiment.py:621-626`) but computes regimes and all chart metrics on `analysis_df` (`python/experiments/EXP-002/code/run_experiment.py:628-679`). `test_df` is only reported as a row count (`python/experiments/EXP-002/code/run_experiment.py:697-700`).",
    "impact": "The train/test split is not used as an out-of-sample check within the allowed analysis set. Results would mix the threshold-calibration segment with the evaluation segment, weakening the claim that observed effects generalize beyond the calibration window.",
    "fix": "Keep train-derived tercile thresholds, but compute headline hybrid-rate, lag, bootstrap, and interpretation metrics on the test segment only. If train-plus-test descriptive tables are useful, label them explicitly as exploratory and keep the success verdict tied to test-segment metrics."
  },
  {
    "id": "F04",
    "severity": "Major",
    "title": "Unmatched event mappings are silently dropped instead of reported",
    "evidence": "The analysis plan states that missing mappings are reported and excluded from denominators (`python/experiments/EXP-002/analysis-plan.md:22`) and that unmatched event counts must be reported (`python/experiments/EXP-002/analysis-plan.md:56-57`). The implementation left-joins regimes and then drops null regimes (`python/experiments/EXP-002/code/run_experiment.py:652-672`) without recording pre-drop counts, unmatched counts, or exclusion rates in `validation_records` (`python/experiments/EXP-002/code/run_experiment.py:705-714`).",
    "impact": "If generator timestamps fail to map cleanly to time-bar regimes, the metric denominators shrink invisibly. This can bias hybrid-rate and lag estimates and makes reproducibility checks harder because the output cannot distinguish clean alignment from heavy exclusion.",
    "fix": "Record generated row count before the regime join, matched row count after the join, unmatched row count, and unmatched percentage per instrument/chart type. Fail or warn prominently if unmatched rates exceed a small predefined threshold."
  },
  {
    "id": "F05",
    "severity": "Major",
    "title": "Initial rolling-volatility nulls are assigned to the high-volatility regime",
    "evidence": "`compute_realised_volatility` produces rolling means with an initial null window (`python/experiments/EXP-002/code/run_experiment.py:152-155`). `assign_regime_terciles` then assigns regimes with `when RealisedVol <= q33`, `when RealisedVol <= q66`, `otherwise(3)` (`python/experiments/EXP-002/code/run_experiment.py:183-190`). Null `RealisedVol` values fall through to regime 3 rather than remaining null or excluded.",
    "impact": "The first rolling window can be mislabeled as high volatility, creating artificial regime transitions and contaminating transition-lag and hybrid-rate metrics near the start of each instrument's analysis window.",
    "fix": "Preserve null regimes where `RealisedVol` is null, then drop or explicitly exclude those warmup rows before transition detection and metric denominators. Add a regression test that the first `ROLLING_VOL_WINDOW - 1` rows have null regime labels."
  },
  {
    "id": "F06",
    "severity": "Major",
    "title": "The implementation does not measure the trend-regime part of the stated question",
    "evidence": "The experiment title and objective cover volatility and trend regime representation (`python/experiments/EXP-002/scope.md:1-9`, `python/experiments/EXP-002/analysis-plan.md:5`). The scope requires trend direction to be defined consistently (`python/experiments/EXP-002/scope.md:36`). The code creates `Direction` for time bars (`python/experiments/EXP-002/code/run_experiment.py:642-650`), but the metrics, bootstrap outputs, and plots use only `Regime`, `HybridRate`, and `MedianLag` (`python/experiments/EXP-002/code/run_experiment.py:674-701`, `python/experiments/EXP-002/code/run_experiment.py:745-857`).",
    "impact": "The experiment can only answer a volatility-regime boundary question. Any conclusion about trend-regime representation would be unsupported by the implemented metrics.",
    "fix": "Either narrow the scope/title/question to volatility-regime boundary representation only, or add predefined trend-transition metrics that use `Direction` without expanding beyond the complexity budget."
  },
  {
    "id": "F07",
    "severity": "Minor",
    "title": "Generator tests do not fully cover the design prerequisite for look-ahead prevention",
    "evidence": "The active phase design requires generator unit tests for determinism, streaming compatibility, and look-ahead bias prevention (`docs/experiments-docs/checkpoints/2026-05-14-001-chart-type-validation/design.md:31-50`). Existing tests cover determinism and batch-vs-streaming (`python/tests/test_chart_generators.py:85-98`) and include a limited Renko timing assertion (`python/tests/test_chart_generators.py:120-127`), but there are no focused look-ahead tests for Line Break or Heiken Ashi and no mutation-style tests proving future rows cannot alter prior emitted outputs.",
    "impact": "This does not by itself prove look-ahead exists, but the test evidence is weaker than the phase prerequisite. A later generator regression could affect EXP-002 without being caught.",
    "fix": "Add tests that compare outputs emitted up to timestamp T when running on data truncated at T versus running on the full dataset, for each generator. Assert all rows with `SourceCloseTime` or `CloseTime` <= T are identical."
  }
]
```

## Summary

EXP-002 should not be relied on in its current pre-execution form. The largest issue is not a coding style problem: the stated success criteria compare event-based charts against time-bar metrics that the implementation defines as zero by construction, making the primary hypothesis impossible to support. Separately, the bootstrap-saving bug would drop the Line Break and Renko confidence intervals even if the metric definition were repaired.

## Verification Performed

- Did not execute `python/experiments/EXP-002/code/run_experiment.py`, preserving the research-pipeline manual execution gate.
- Ran generator tests as a reference check:

```text
PYTHONPATH=python/src pytest -q python/tests/test_chart_generators.py
6 passed in 0.42s
```
