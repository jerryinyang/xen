---
name: experiment-developer
description: Implement approved Xen experiment analysis plans in Python. Use when creating or modifying experiment scripts, reusable analysis utilities, result generation code, plots, or fixes requested by audit for files under python/experiments/<ID>/code or python/src. Trigger on implement, write code, create script, code the analysis, build module, implement the plan, or fix audited experiment code.
---

# Experiment Developer

Translate an approved scope and analysis plan into Python code. Implement only the approved plan.

## Start

1. Read the shared pipeline config from the sibling `research-pipeline` skill in
   the same skills root. If the file tool cannot resolve sibling skill paths,
   locate the file whose path ends with `/research-pipeline/_pipeline-config.md`.
2. Read `docs/references/dataset-reference.md`.
3. Read `python/experiments/<ID>/scope.md`.
4. Read `python/experiments/<ID>/analysis-plan.md`.
5. Read the bundled code conventions in this skill's `references` directory.
   If needed, locate the file ending with `/experiment-developer/references/code-conventions.md`.
6. Inspect existing `python/src/` modules before creating new abstractions.

## Implementation Workflow

1. Map every analysis-plan requirement to code.
2. Decide file placement:
   - use `python/experiments/<ID>/code/run_experiment.py` for experiment orchestration;
   - use `python/src/` only for reusable functions likely to serve multiple experiments;
   - avoid notebooks unless the user or plan explicitly requires them.
3. Load data with the standard project pattern from `code-conventions.md`.
4. Exclude the final 30 percent global holdout before analysis.
5. Preserve chronological ordering by `CloseTime` (time bars) or `SourceCloseTime` (chart-type bars).
6. For cross-chart-type comparisons, align by timestamp — never by bar index.
7. Apply only filters approved in the scope.
8. Write focused, typed functions for reusable computations.
9. Save plots under `python/experiments/<ID>/plots/`.
9. Save machine-readable outputs under `python/experiments/<ID>/results/` when practical.
10. Keep stdout concise and useful for manual execution.

## Code Requirements

- Use type hints for public functions.
- Use docstrings for reusable functions.
- Return data from functions; keep file I/O in orchestration code.
- Handle empty inputs, NaN values, insufficient sample size, and divide-by-zero cases.
- Use deterministic seeds when randomness is required.
- For chart-type generators, same input + same parameters must produce identical output.
- Never use synthetic chart prices for strategy P&L. Heiken Ashi returns use `RealOpen`, `RealHigh`, `RealLow`, `RealClose`; Renko and Line Break signals align through `SourceCloseTime` to real time-bar prices.
- Avoid magic numbers unless the analysis plan defines them.
- Do not add exploratory analyses or extra plots outside the plan.

## Completion

After implementation, summarize:

- files created or modified;
- how to run `python/experiments/<ID>/code/run_experiment.py`;
- expected output files;
- any deviation from the approved plan, if unavoidable.

Do not run the experiment code when acting inside `research-pipeline`; the pipeline has a manual execution gate. Outside the pipeline, run tests or lightweight checks when appropriate.

## References

| Resource | Read when |
| --- | --- |
| shared pipeline config in sibling `research-pipeline` skill | Always |
| `docs/references/dataset-reference.md` | Always |
| bundled code conventions | Before coding |
| `python/experiments/INDEX.md` | To find prior experiment patterns |
