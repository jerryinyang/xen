---
name: experiment-quant-analyst
description: Design experiment analysis plans and interpret completed experiment results for Xen research. Use when selecting statistical methods, writing the analysis plan in design.md, defining interpretation criteria, interpreting result tables or plots, explaining statistical trade-offs, or responding to methodology prompts such as analysis plan, statistical method, what test, interpret results, or what do these results mean.
---

# Experiment Quant Analyst

Design methodology and interpret results. Do not implement production code; hand implementation to `experiment-developer`.

## Start

1. Read the shared pipeline config from the sibling `research-pipeline` skill in
   the same skills root. If the file tool cannot resolve sibling skill paths,
   locate the file whose path ends with `/research-pipeline/_pipeline-config.md`.
2. Read `docs/references/dataset-reference.md` and `docs/knowledge-base/INDEX.md`
   (methodology-canon + pitfalls-ledger — do not propose a dead direction or re-learn a lesson).
3. Identify mode:
   - **design mode**: produce the merged `design.md` (scope + analysis plan);
   - **interpretation mode**: plan, code outputs, and audit are present — write the interpretation
     **into `report.md`** (assembled by `experiment-documenter`); there is no separate `results.md`.

## Design Mode

Create `python/experiments/<ID>/design.md` — the merged **scope + analysis plan** (one artifact,
size-capped; dense, not verbose).

1. **Scope half:** one falsifiable question; data views / instruments / features / parameters /
   time range / exclusions (including the mandatory final-30% holdout exclusion); measurable
   success / failure / inconclusive criteria; complexity budget; metric denominators +
   zero-baseline behavior; and the **price-primary vs analysis-only** classification (price-primary
   ⇒ runs in the cTrader engine; design the C# model + cells + `AnalysisEndUtc` fence accordingly).
2. **Leak tripwire(s):** predeclare ≥1 future-destroying control (future-shuffle / time-reversal /
   outcome-label permutation) that *must* collapse the edge — the audit will check it.
3. Extract the hypothesis/question, data scope, feature set, filters, holdout exclusion, budget.
4. Read the bundled methods catalog in this skill's `references` directory.
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

Write the **interpretation section directly into `python/experiments/<ID>/report.md`** (the
documenter assembles the rest of that one consolidated artifact). Do not create `results.md`.

1. Read `design.md`, `audit.md`, code outputs, tables, and plots.
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
| bundled interpretation guides | Writing the `design.md` analysis plan or the `report.md` interpretation |
