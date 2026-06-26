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
6. Inspect existing `python/src/xen/` modules before creating new abstractions.

## Implementation Workflow

1. Map every analysis-plan requirement to code.
2. Decide file placement:
   - use `python/experiments/<ID>/code/run_experiment.py` for experiment orchestration;
   - use `python/src/xen/` (the installed `xen` package) only for reusable functions likely to serve multiple experiments;
   - avoid notebooks unless the user or plan explicitly requires them.
3. Load data with the standard project pattern from `code-conventions.md`.
4. Exclude the final 30 percent global holdout before analysis.
5. Preserve chronological ordering by `CloseTime` (time bars), event timestamp,
   or `SourceCloseTime` (chart-type bars).
6. For cross-view comparisons, align by timestamp — never by bar index.
7. Apply only filters approved in the scope.
8. Write focused, typed functions for reusable computations.
9. Save plots under `python/experiments/<ID>/plots/`.
10. Save machine-readable outputs under `python/experiments/<ID>/results/` when practical.
11. Keep stdout concise and useful for manual execution.
12. Add `tqdm` progress tracking for long-running outer loops or repeated
    iterations, using clean descriptions and no noisy per-row output.
13. Use safe performance and memory optimizations suitable for large datasets:
    efficient Polars lazy plans, column projection, aggregation before
    collection where possible, bounded plotting data, and vectorized
    Polars/NumPy logic when it is causally equivalent.
14. Run a code-standards self-check before completion using the bundled
    `code-conventions.md`; fix any violations unless the approved plan
    explicitly requires the exception.

## Code Requirements

- Use type hints for public functions.
- Use docstrings for reusable functions.
- Return data from functions; keep file I/O in orchestration code.
- Put imports first, then path setup, constants, small I/O helpers, pure
  computation helpers, plotting helpers, orchestration, and `main()`.
- Section non-trivial scripts with VAL-001-style separators so manual review
  can quickly distinguish constants, helpers, pure checks, plotting/output,
  orchestration, and `main()`.
- Create `plots/` and `results/` directories inside orchestration, not during
  module import.
- Prefer `logging.getLogger(__name__)` for new scripts. Legacy `print()` is
  acceptable only for concise manual-run summaries from `main()` or
  orchestration-level progress messages.
- Use `tqdm.auto.tqdm` for expensive loops over files, instruments, chart views,
  validation windows, parameter grids, or simulations. Use `tqdm.write()` or
  logging for occasional status lines; helper functions stay quiet.
- Use lazy Polars scans for large Parquet inputs, select only needed columns,
  sort by the governing timestamp before slicing, and collect only the analysis
  set.
- Prefer Polars expressions, joins, group/window operations, and NumPy
  vectorization over Python row loops for large frames when the replacement is
  causally equivalent and preserves streaming semantics.
- Keep explicit loops when the logic is genuinely sequential or stateful, such
  as chart generation, causal streaming validation, or bounded prefix probes.
  Bound the work and report the bounds.
- Do not optimize by changing sample membership, temporal ordering,
  denominators, metric definitions, or statistical interpretation. In
  particular, do not introduce look-ahead bias, batch-only streamed-data
  violations, silent sampling, or silent deduplication.
- Do not reload or regenerate large data solely for plotting when the analysis
  pass can return the sampled or aggregated plot inputs.
- Convert to pandas only after aggregation or deterministic sampling; do not
  convert millions of rows just to plot.
- Handle empty inputs, NaN values, insufficient sample size, and divide-by-zero cases.
- Use deterministic seeds when randomness is required.
- For derived-view generators and feature builders, same input + same
  parameters must produce identical output unless the approved scope explicitly
  requires seeded randomness.
- Never use synthetic chart prices for strategy P&L or signal-quality return
  evaluation. Heiken Ashi strategy returns use `RealOpen`, `RealHigh`,
  `RealLow`, `RealClose`; Renko and Line Break signals align through
  `SourceCloseTime` to real time-bar prices.
- If the approved scope is explicitly a Heiken Ashi synthetic-price distortion
  diagnostic, `HAClose`-based diagnostic returns are allowed only when labelled
  non-tradable and kept separate from strategy/P&L metrics.
- Avoid magic numbers unless the analysis plan defines them.
- Do not add exploratory analyses or extra plots outside the plan.

## Completion

After implementation, summarize:

- files created or modified;
- how to run `python/experiments/<ID>/code/run_experiment.py`;
- expected output files;
- code-standards self-check result;
- any deviation from the approved plan, if unavoidable.

Do not run the experiment code when acting inside `research-pipeline`; the pipeline has a manual execution gate. Outside the pipeline, run tests or lightweight checks when appropriate.

## References

| Resource | Read when |
| --- | --- |
| shared pipeline config in sibling `research-pipeline` skill | Always |
| `docs/references/dataset-reference.md` | Always |
| bundled code conventions | Before coding |
| `python/experiments/INDEX.md` | To find prior experiment patterns |
