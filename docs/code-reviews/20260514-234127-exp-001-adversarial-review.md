# EXP-001 Adversarial Review

**Timestamp:** 2026-05-14 23:41:27 Africa/Lagos
**Scope:** EXP-001 artifacts and code available before execution.
**Review lens:** Empirical study plus implementation review, prioritizing statistical validity, governance compliance, reproducibility, and failure modes.

## Context Reviewed

- `python/experiments/EXP-001/scope.md`
- `python/experiments/EXP-001/analysis-plan.md`
- `python/experiments/EXP-001/code/run_experiment.py`
- `python/experiments/EXP-001/governance/pre-execution-review.md`
- `python/src/linebreak_generator.py`
- `python/src/renko_generator.py`
- `python/src/heiken_ashi_generator.py`
- `python/tests/test_chart_generators.py`
- `.agents/skills/research-pipeline/_pipeline-config.md`
- `docs/references/dataset-reference.md`
- `docs/references/architecture.md`
- `python/experiments/INDEX.md`
- `docs/experiments-docs/INDEX.md`
- `docs/experiments-docs/checkpoints/2026-05-14-001-chart-type-validation/design.md`

No completed EXP-001 result artifacts were present at review time: `results/`, `plots/`, `audit.md`, `results.md`, and `report.md` contain no completed outputs for this experiment.

## Findings

```json
[
  {
    "id": "F01",
    "severity": "Critical",
    "title": "Implementation loads and summarizes the global holdout before slicing",
    "evidence": "Pipeline config lines 123-129: \"Never load, inspect, or use the final 30%\" and \"Any experiment that touches the holdout set is a governance violation.\" Scope lines 16-17 also state the final 30% must not be loaded, inspected, summarized, plotted, or used. In run_experiment.py lines 631-636, `full_df = load_timebar_data(instrument)` is collected first and only then sliced to 70%; load_timebar_data collects all matched rows at lines 93-98. The validation output also records `SourceRows: len(full_df)` at line 741.",
    "impact": "This violates a non-negotiable governance rule before any metrics are computed. Even if the later chart generation uses `analysis_df`, the script has already materialized and summarized holdout rows, so resulting artifacts should not be relied on as governance-compliant.",
    "fix": "Change data loading so only the first 70% chronological rows are materialized for each instrument. Use row-count metadata or a streaming/lazy file plan to determine the analysis-row boundary, then collect only analysis rows. Do not emit `SourceRows` for the full dataset if that value includes holdout rows; report only analysis rows and non-sensitive metadata needed for reproducibility."
  },
  {
    "id": "F02",
    "severity": "Major",
    "title": "Success criteria are not implemented, so the script cannot produce the required verdict",
    "evidence": "Scope lines 24-26 define evidence FOR/AGAINST/INCONCLUSIVE using per-instrument 25% ghost-rate reduction, 10% entropy increase, at least 3 instruments, and bootstrap intervals excluding zero. Analysis plan lines 40-44 repeat the interpretation guide. In run_experiment.py lines 791-843, the code computes only absolute instrument-level mean differences, sign counts, and CI exclusion flags; it does not compute the relative 25% and 10% thresholds, does not count instruments meeting both thresholds, and does not emit a supported/refuted/inconclusive verdict.",
    "impact": "A completed run could produce tables and plots while leaving the central hypothesis unresolved or incorrectly interpreted by a later manual reviewer. This is especially risky because absolute entropy differences are not equivalent to a 10% relative entropy increase.",
    "fix": "Add a verdict table or summary artifact that computes, per event chart type and instrument, relative ghost reduction and relative entropy increase versus time bars. Then apply the exact scope rules: count instruments meeting both thresholds, combine that with CI exclusion status, and write an explicit SUPPORTED / REFUTED / INCONCLUSIVE decision."
  },
  {
    "id": "F03",
    "severity": "Major",
    "title": "Instrument processing failures are swallowed and can still yield a nominally complete experiment",
    "evidence": "run_experiment.py lines 784-786 catch any exception per instrument, print a warning, and continue. Lines 851-857 save CSV files regardless of how many instruments succeeded, and line 884 prints \"EXP-001 complete.\" Scope line 26 says insufficient valid data for at least 3 instruments is inconclusive, but the code does not enforce that minimum.",
    "impact": "If one or more instruments fail due to missing data, schema drift, generator errors, or plotting issues, the bootstrap and summary outputs may silently use fewer than the required instruments. A partial or empty run could be mistaken for a valid completed experiment.",
    "fix": "Track instrument failures in a machine-readable output. Require at least 3 successfully processed instruments before hypothesis evaluation. If the threshold is not met, emit an INCONCLUSIVE status and exit non-zero or clearly mark the run incomplete instead of printing a generic completion message."
  },
  {
    "id": "F04",
    "severity": "Major",
    "title": "Train/test chart counts reset event-generator state at the split boundary",
    "evidence": "Scope line 16 defines a nested chronological split within the analysis set. run_experiment.py lines 636-637 split `analysis_df` into `train_df` and `test_df`, then lines 704-705 independently call `generate_chart(train_df, config)` and `generate_chart(test_df, config)`. This restarts Line Break history, Renko ATR/anchor state, and Heiken Ashi state at the test segment boundary.",
    "impact": "The reported `TrainBars` and `TestBars` in lines 711-713 are not counts from a continuous chronological chart process. For event-based charts this can distort test-segment generated rows, especially near the split where Renko ATR warmup and Line Break reversal history are lost.",
    "fix": "Generate each chart type once over the analysis set, then classify generated rows into train/test by `CloseTime` or `SourceCloseTime` relative to the analysis-set train cutoff timestamp. This preserves streaming state while still reporting nested split counts."
  },
  {
    "id": "F05",
    "severity": "Minor",
    "title": "Volatility terciles use single-bar high-low range rather than realised volatility",
    "evidence": "Analysis plan lines 71-74 specify realised-volatility terciles from the 1-minute analysis set. run_experiment.py lines 284-311 define volatility terciles directly from `High - Low` for each bar.",
    "impact": "The CV-by-regime outputs may not match the planned regime stratification. This is less central than the ghost-rate and entropy tests, but it weakens consistency between the methodology and reported regime-related metrics.",
    "fix": "Either revise the plan/scope to state that regime terciles are based on single-bar range, or implement a realised-volatility proxy explicitly, such as rolling absolute/log returns or rolling range volatility computed only from past and current analysis-set bars."
  }
]
```

## Summary

EXP-001 should not be executed or relied on until F01 is fixed; the current loader violates the project-level holdout rule before any analysis begins. The pre-execution governance approval missed that issue, likely because it checked that generation happens after slicing but did not account for `collect()` materializing all rows first. After the holdout fix, the next priority is making the script emit the exact hypothesis verdict required by the scope and fail clearly when fewer than three instruments are valid.
