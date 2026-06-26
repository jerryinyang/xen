---
name: experiment-quant-analyst
description: Design experiment analysis plans and interpret completed experiment results for Xen research. Use when selecting statistical methods, writing an analysis-plan.md, defining interpretation criteria, interpreting result tables or plots, explaining statistical trade-offs, or responding to methodology prompts such as analysis plan, statistical method, what test, interpret results, or what do these results mean.
---

# Experiment Quant Analyst

Design methodology and interpret results. Do not implement production code; hand implementation to `experiment-developer`.

## Start

1. Read the shared pipeline config from the sibling `research-pipeline` skill in
   the same skills root. If the file tool cannot resolve sibling skill paths,
   locate the file whose path ends with `/research-pipeline/_pipeline-config.md`.
2. Read `docs/references/dataset-reference.md`.
3. Identify mode:
   - plan mode: scope is present and `analysis-plan.md` is needed;
   - interpretation mode: plan, code outputs, and audit are present and `results.md` is needed.

## Plan Mode

Create `python/experiments/<ID>/analysis-plan.md`.

1. Read `python/experiments/<ID>/scope.md`.
2. Extract the hypothesis or question, data scope, feature set, filters, holdout exclusion, and complexity budget.
3. Read the bundled methods catalog in this skill's `references` directory.
   If needed, locate the file ending with `/experiment-quant-analyst/references/methods-catalog.md`.
4. Select the simplest sufficient methods in this order:
   - descriptive statistics and visual checks;
   - non-parametric rank or permutation tests;
   - bootstrap or resampling intervals;
   - robust parametric methods only when justified and cross-checked.
5. For each selected method, document:
   - question answered;
   - reason it is sufficient;
   - simpler alternative considered;
   - assumptions and whether they fit time-ordered financial data;
   - expected table, metric, or plot.
6. Define plots that answer specific sub-questions. Include distribution, relationship, and sequence context plots when relevant.
7. Predefine interpretation criteria before results exist:
   - supports the hypothesis if...
   - contradicts the hypothesis if...
   - inconclusive if...
8. Define implementation safety constraints needed by `experiment-developer`:
   timestamp ordering, denominators, zero-baseline behavior, bounded iteration
   counts, progress expectations for long loops, and where Polars/NumPy
   vectorization is safe or where sequential logic must remain explicit.
9. Confirm the plan fits the complexity budget.
10. Use the bundled interpretation guides for the output structure.
   If needed, locate the file ending with `/experiment-quant-analyst/references/interpretation-guides.md`.

## Interpretation Mode

Create `python/experiments/<ID>/results.md`.

1. Read `scope.md`, `analysis-plan.md`, `audit.md`, code outputs, tables, and plots.
2. Anchor interpretation to the pre-defined interpretation guide.
3. State observed values, effect sizes, uncertainty, and sample sizes.
4. Treat negative and inconclusive results as valid findings.
5. Separate evidence from speculation.
6. Include caveats from the audit.
7. Recommend follow-up experiments only as new scopes, not as extensions to the current scope.
8. Use the bundled interpretation guides for the output structure.
   If needed, locate the file ending with `/experiment-quant-analyst/references/interpretation-guides.md`.

## Constraints

- Do not inspect the final 30 percent global holdout.
- Do not move goalposts after seeing results.
- Do not add methods outside the approved scope without routing back to the pipeline.
- Prefer robust, explainable analyses over complex modeling.
- Be explicit when assumptions are weak or violated.
- Strategy, signal-quality, and return-evaluation metrics use real time-bar
  prices unless the approved scope explicitly defines a non-tradable diagnostic.
  Never compute strategy P&L from synthetic chart prices. If Heiken Ashi is in
  scope, strategy metrics use RealOpen/RealHigh/RealLow/RealClose. If Renko or
  Line Break is in scope, signals align through SourceCloseTime to real
  time-bar prices.
- For explicitly scoped Heiken Ashi synthetic-price distortion diagnostics,
  `HAClose` returns may be planned only as non-tradable diagnostic metrics and
  must be compared against real prices at identical `CloseTime`.
- Align cross-view comparisons by timestamp (CloseTime, event timestamp, or SourceCloseTime), never by bar index.
- Acknowledge that different event definitions or data views may produce different observation counts for the same time period.

## References

| Resource | Read when |
| --- | --- |
| shared pipeline config in sibling `research-pipeline` skill | Always |
| `docs/references/dataset-reference.md` | Always |
| bundled methods catalog | Plan mode |
| bundled interpretation guides | Writing `analysis-plan.md` or `results.md` |
