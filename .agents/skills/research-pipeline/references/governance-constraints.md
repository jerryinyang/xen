# Governance Constraints

The constraint framework enforced at both governance gates (pre-execution and post-experiment reviews). These constraints are non-negotiable and apply to all artifacts in the Xen research pipeline.

See `_pipeline-config.md` for programme principles, OOS rules, and project path conventions.

---

## Core Constraints

### 1. Simplicity Over Complexity

Always choose the simplest, most robust approach that answers the question. Justify complexity before using it.

| Check | What to Verify |
|-------|---------------|
| Simplest sufficient | Is there a simpler method that would produce equivalent results? |
| Complexity justified | If a complex method is used, is there a documented reason why simpler methods were insufficient? |
| No unnecessary computation | Are there calculations, models, or parameters that don't contribute to answering the question? |

### 2. No Academic-Finance Pitfalls

Reject techniques that rely on assumptions known to fail in real markets.

| Check | What to Verify |
|-------|---------------|
| No normality assumption | Does the method assume normally distributed returns? If so, is there a non-parametric cross-validation? |
| No stationarity assumption | Does the method assume stationary data? Financial time-series are not stationary. |
| No i.i.d. assumption | Does the method assume independent, identically distributed observations? Chart-type bar data has temporal structure. |
| No constant volatility | Does the method assume constant volatility? Financial volatility clusters and changes. |
| Method choice justified | Is the method used because it's practically useful, or because it's theoretically elegant? |

### 3. Strict Experiment Scoping

Every experiment must have a single hypothesis, defined boundaries, success/failure criteria, and a complexity budget.

| Check | What to Verify |
|-------|---------------|
| Single question | Does the experiment answer exactly one question? No compound questions. |
| Defined boundaries | Are chart types, instruments, timeframes, and exclusions all explicitly stated? |
| Concrete criteria | Are success/failure conditions measurable, not subjective? |
| Budget respected | Count actual tests, plots, modules vs budgeted limits. |
| No scope creep | Does the artifact stay within the stated scope and not add "bonus" analyses? |

### 4. Framework Principles

| Principle | Check |
|-----------|-------|
| Data-driven | Do conclusions emerge from data, not assumptions or preconceptions? |
| Non-conformational | Is data forced into predefined shapes or models, or does the analysis adapt to what the data shows? |
| Non-parametric | Are distribution-free methods used by default? If parametric, is there non-parametric cross-validation? |
| Synthetic price discipline | Are strategy returns always computed from real time-matched prices, never from Heiken Ashi prices or Renko brick prices? |
| Timestamp alignment | Are cross-chart-type comparisons always aligned by timestamp, never by bar count? |

### 5. OOS Holdout Rule

The final 30% of the dataset is a global holdout — never loaded, inspected, or used.

| Check | What to Verify |
|-------|---------------|
| Holdout untouched | Does any code path, analysis step, or scope boundary access data beyond the 70% cutoff? |
| Chronological split | Is the split ordered by CloseTime/SourceCloseTime, not random? (Financial data has temporal structure.) |
| Train/test within analysis set | If train/test split is used, is it within the 70% analysis set, not touching the holdout? |

### 6. Look-Ahead Bias Prevention

Chart-type generators process data sequentially. Analysis must respect this.

| Check | What to Verify |
|-------|---------------|
| Sequential generation | Do generators use only data available at or before each bar's timestamp? |
| No future data | Does any analysis use data from after the event timestamp? |
| SourceCloseTime alignment | For chart-type events, is SourceCloseTime used for temporal alignment? |
| Bar-index alignment ban | Are cross-chart-type comparisons aligned by timestamp, not by bar count? |

### 7. Synthetic Price Discipline

Heiken Ashi prices and Renko brick prices are synthetic chart-construction prices. Strategy P&L must use real time-matched prices.

| Check | What to Verify |
|-------|---------------|
| No HA returns | Are strategy returns computed from RealClose (or time-bar Close), never from HA-Close? |
| No HA signal validation via HA prices | Are signal quality metrics (like continuation, reversal) computed on real prices, not HA prices? |
| No Renko brick P&L | Are Renko signal returns computed from time-matched real prices, never from brick open/close levels? |
| Real price columns used | Does the code explicitly use RealOpen/RealHigh/RealLow/RealClose for all return calculations? |

---

## Artifact-Specific Checks

### Scope Document (scope.md)

| Check | Questions |
|-------|-----------|
| Hypothesis quality | Is it testable, falsifiable, specific? No weasel words. |
| Success criteria | Are they concrete and measurable, not subjective judgments? |
| Chart types defined | Are all chart types, their parameters, and timeframes explicitly stated? |
| Scope boundaries | Are instruments, time range, and exclusions all explicit? |
| Complexity budget | Does it match the scope? Is it realistic? |
| Holdout exclusion | Does the scope explicitly exclude the global holdout? |
| Synthetic price rule | If Heiken Ashi or Renko is in scope, does the scope explicitly state that strategy P&L uses real prices? |

### Analysis Plan (analysis-plan.md)

| Check | Questions |
|-------|-----------|
| Method justification | Is each method choice justified with "why this method" and "simpler alternative considered"? |
| Assumptions listed | Does each method document its assumptions and whether they hold for chart-type comparison data? |
| Cross-chart alignment | Does the plan specify how chart types are aligned (by timestamp, not bar count)? |
| Visualisation plan | Are plots purposeful (answering specific sub-questions), not decorative? |
| Interpretation guide | Are outcomes pre-defined (if X then Y because Z) to prevent post-hoc rationalisation? |
| Budget compliance | Do total tests, plots, modules stay within the complexity budget? |

### Code (code/run_experiment.py)

| Check | Questions |
|-------|-----------|
| Plan compliance | Does the code implement exactly what the analysis plan specifies — nothing more, nothing less? |
| Holdout exclusion | Is only the first 70% of time-ordered data loaded? No code path accesses the holdout. |
| Look-ahead bias prevention | Is all temporal ordering by CloseTime/SourceCloseTime? No use of future data relative to event time. |
| Synthetic price check | Are returns computed from real prices, never HA prices or Renko brick prices? |
| Timestamp alignment | Are cross-chart-type comparisons aligned by timestamp, not bar index? |
| Type safety | Are type hints on all public functions? Are types consistent? |
| NaN handling | Is NaN handling explicit — no silent propagation? |
| Edge cases | Are empty DataFrames, single-element arrays, division by zero handled? |
| Separation of concerns | Are analysis functions (pure computation) separated from plotting and orchestration? |
| No magic numbers | Are all thresholds derived from data or documented? |
| Code quality | PEP 8, docstrings, descriptive names, ~30 line function limit? |
| Data loading | Is Polars/Parquet used correctly? Are columns properly selected before `collect()`? |
| Organization | Are imports, path setup, constants, I/O helpers, computation helpers, plotting helpers, orchestration, and `main()` clearly separated? |
| Import side effects | Does module import avoid creating directories, writing files, loading data, or plotting? |
| Logging/output | Is manual-run output concise and traceable, with helper functions returning data instead of printing? |
| Plot memory | Are plot inputs aggregated or sampled before pandas conversion? |
| Repeated heavy work | Does plotting reuse analysis outputs instead of reloading or regenerating large datasets? |
| Generator determinism | If chart-type generators are called, are they deterministic? No random seeds? |

### Audit Report (audit.md)

| Check | Questions |
|-------|-----------|
| Thoroughness | Are correctness, edge cases, type safety, NaN handling, holdout exclusion, look-ahead bias, and synthetic price discipline all checked? |
| Evidence | Does every finding include specific line numbers, values, or code excerpts? |
| Severity classification | Are issues classified as Critical, Warning, or Info appropriately? |
| Numerical validation | Are spot checks, boundary checks, statistical sanity checks included? |
| Scope compliance | Does the audit verify that code matches the analysis plan? |
| Synthetic price audit | Does audit verify that no strategy P&L uses HA prices or Renko brick prices? |
| Timestamp alignment audit | Does audit verify cross-chart-type alignment by timestamp? |

### Results Interpretation (results.md)

| Check | Questions |
|-------|-----------|
| Honest reporting | Does it state what the data shows, not what was expected? |
| Uncertainty acknowledged | Are limitations, confidence intervals, and alternative explanations included? |
| No overreaching | If effect sizes are small, does it say so? No inflating weak findings. |
| Verdict supported | Is the SUPPORTED/REFUTED/INCONCLUSIVE conclusion justified by the evidence? |
| Next steps reasonable | Are follow-up suggestions specific new experiments, not scope extensions? |
| Synthetic price results | If Heiken Ashi or Renko is involved, are all strategy P&L metrics computed on real prices? |

### Final Report (report.md)

| Check | Questions |
|-------|-----------|
| Self-contained | Can a reader with project context but no experiment knowledge understand it? |
| Key visualisations included | Are the most important plots embedded with captions? |
| Honest about limitations | Are negative results, inconclusive findings, and caveats included? |
| Artifacts linked | Are all experiment artifacts referenced by relative path? |
| Index updated | Is `python/experiments/INDEX.md` entry correct? Is `docs/experiments-docs/INDEX.md` updated? |

---

## Verdict Framework

After applying all checks, produce a verdict:

### APPROVE
All checks pass. No Critical or Warning issues. Minor Info notes may be present.

### REVISE
One or more issues found. Specify:
- `FAILING_ARTIFACT`: which file needs fixing
- `REQUIRED_SKILL`: which skill should fix it
- `ISSUES`: specific issues with line references and remediation suggestions

Allow up to 2 revision cycles.

### REJECT

Fundamental, unfixable issues. Examples:
- Holdout contamination (data from the 30% reserve was used)
- Look-ahead bias (using data from after the event timestamp when analyzing an event)
- Synthetic price violation (computing strategy P&L from Heiken Ashi prices or
  Renko brick prices instead of real prices; `HAClose` diagnostic returns are
  allowed only for explicitly scoped HA distortion experiments that label them
  non-tradable)
- Bar-index alignment (comparing chart types by bar index instead of timestamp)
- Scope creep beyond what can be fixed with revision
- Method fundamentally violates core constraints (e.g., assumes normality with no cross-validation)
- Dishonest or fabricated results

Hard stop. Cannot be overridden.
