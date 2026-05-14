# Governance Constraints

The constraint framework enforced at both governance gates (pre-execution and post-experiment reviews). These constraints are non-negotiable and apply to all artifacts in the research pipeline.

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
| No i.i.d. assumption | Does the method assume independent, identically distributed observations? Pivot sequence data has temporal structure. |
| No constant volatility | Does the method assume constant volatility? Financial volatility clusters and changes. |
| Method choice justified | Is the method used because it's practically useful, or because it's theoretically elegant? |

### 3. Strict Experiment Scoping

Every experiment must have a single hypothesis, defined boundaries, success/failure criteria, and a complexity budget.

| Check | What to Verify |
|-------|---------------|
| Single question | Does the experiment answer exactly one question? No compound questions. |
| Defined boundaries | Are features, feature categories, instruments, time range, and exclusions explicitly stated? |
| Concrete criteria | Are success/failure conditions measurable, not subjective? |
| Budget respected | Count actual tests, plots, modules vs budgeted limits. |
| No scope creep | Does the artifact stay within the stated scope and not add "bonus" analyses? |

### 4. Framework Principles

| Principle | Check |
|-----------|-------|
| Data-driven | Do conclusions emerge from data, not assumptions or preconceptions? |
| Non-conformational | Is data forced into predefined shapes or models, or does the analysis adapt to what the data shows? |
| Non-parametric | Are distribution-free methods used by default? If parametric, is there non-parametric cross-validation? |
| Adaptive | Are all parameters derived from data, not hardcoded? No magic numbers. |

### 5. OOS Holdout Rule

The final 30% of the dataset is a global holdout — never loaded, inspected, or used.

| Check | What to Verify |
|-------|---------------|
| Holdout untouched | Does any code path, analysis step, or scope boundary access data beyond the 70% cutoff? |
| Chronological split | Is the split ordered by ConfirmTime, not random? (Financial data has temporal structure.) |
| Train/test within analysis set | If train/test split is used, is it within the 70% analysis set, not touching the holdout? |

### 6. Look-Ahead Bias Prevention

TriLattice labels are assigned at `ConfirmTime`, not at the swing peak. This prevents look-ahead bias but must be explicitly respected in analysis.

| Check | What to Verify |
|-------|---------------|
| ConfirmTime ordering | Is all temporal ordering done by `ConfirmTime`, not `PeakTime` or `Timestamp`? |
| No future data | Does any analysis use data from after `ConfirmTime` when analyzing a pivot? |
| Proper windowing | Are rolling windows, lags, and leads calculated relative to `ConfirmTime`? |

### 7. Validation Status Integrity

TriLattice includes cross-representation validation. By default, only `ValidationStatus == "Valid"` pivots should be used.

| Check | What to Verify |
|-------|---------------|
| Validation filter | Does the code explicitly filter `ValidationStatus` as specified in the scope? |
| Artifact handling | If artifacts are included, is there documented rationale and impact assessment? |
| Status encoding | Is `ValidationStatus` properly encoded if used in models? (Valid=2, Pending=1, Artifact=0) |

---

## Artifact-Specific Checks

### Scope Document (scope.md)

| Check | Questions |
|-------|-----------|
| Hypothesis quality | Is it testable, falsifiable, specific? No weasel words. |
| Success criteria | Are they concrete and measurable, not subjective judgments? |
| Scope boundaries | Are features, levels, instruments, exclusions all explicit? |
| Complexity budget | Does it match the scope? Is it realistic? |
| Holdout exclusion | Does the scope explicitly exclude the global holdout? |

### Analysis Plan (analysis-plan.md)

| Check | Questions |
|-------|-----------|
| Method justification | Is each method choice justified with "why this method" and "simpler alternative considered"? |
| Assumptions listed | Does each method document its assumptions and whether they hold for TriLattice pivot sequence data? |
| Visualisation plan | Are plots purposeful (answering specific sub-questions), not decorative? |
| Interpretation guide | Are outcomes pre-defined (if X then Y because Z) to prevent post-hoc rationalisation? |
| Budget compliance | Do total tests, plots, modules stay within the complexity budget? |

### Code (code/run_experiment.py)

| Check | Questions |
|-------|-----------|
| Plan compliance | Does the code implement exactly what the analysis plan specifies — nothing more, nothing less? |
| Holdout exclusion | Is only the first 70% of ConfirmTime-ordered data loaded? No code path accesses the holdout. |
| Look-ahead bias prevention | Is all temporal ordering by `ConfirmTime`? No use of future data relative to pivot time. |
| Validation status filter | Is `ValidationStatus` filtered as specified in the scope? |
| Type safety | Are type hints on all public functions? Are types consistent? |
| NaN handling | Is NaN handling explicit — no silent propagation? |
| Edge cases | Are empty arrays, single elements, division by zero handled? |
| Separation of concerns | Are analysis functions (pure computation) separated from plotting and orchestration? |
| No magic numbers | Are all thresholds derived from data or documented? |
| Code quality | PEP 8, docstrings, descriptive names, ~30 line function limit? |
| Data loading | Is Polars/Parquet used correctly? Are columns properly selected before `collect()`? |

### Audit Report (audit.md)

| Check | Questions |
|-------|-----------|
| Thoroughness | Are correctness, edge cases, type safety, NaN handling, holdout exclusion, look-ahead bias, validation status all checked? |
| Evidence | Does every finding include specific line numbers, values, or code excerpts? |
| Severity classification | Are issues classified as Critical, Warning, or Info appropriately? |
| Numerical validation | Are spot checks, boundary checks, statistical sanity checks included? |
| Scope compliance | Does the audit verify that code matches the analysis plan? |
| Look-ahead bias check | Does audit verify `ConfirmTime` is used for temporal ordering? |
| Validation status check | Does audit verify `ValidationStatus` handling matches scope? |

### Results Interpretation (results.md)

| Check | Questions |
|-------|-----------|
| Honest reporting | Does it state what the data shows, not what was expected? |
| Uncertainty acknowledged | Are limitations, confidence intervals, and alternative explanations included? |
| No overreaching | If effect sizes are small, does it say so? No inflating weak findings. |
| Verdict supported | Is the SUPPORTED/REFUTED/INCONCLUSIVE conclusion justified by the evidence? |
| Next steps reasonable | Are follow-up suggestions specific new experiments, not scope extensions? |

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
- Look-ahead bias (using data from after `ConfirmTime` when analyzing a pivot)
- Validation status violation (ignoring `ValidationStatus` filter specified in scope without documented rationale)
- Scope creep beyond what can be fixed with revision
- Method fundamentally violates core constraints (e.g., assumes normality with no cross-validation)
- Dishonest or fabricated results

Hard stop. Cannot be overridden.
