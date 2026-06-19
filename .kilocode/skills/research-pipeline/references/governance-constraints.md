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
| Defined boundaries | Are data views, instruments, timeframes, parameters, and exclusions all explicitly stated? |
| Concrete criteria | Are success/failure conditions measurable, not subjective? |
| Budget respected | Count actual tests, plots, modules vs budgeted limits. |
| No scope creep | Does the artifact stay within the stated scope and not add "bonus" analyses? |

### 4. Framework Principles

| Principle | Check |
|-----------|-------|
| Data-driven | Do conclusions emerge from data, not assumptions or preconceptions? |
| Non-conformational | Is data forced into predefined shapes or models, or does the analysis adapt to what the data shows? |
| Non-parametric | Are distribution-free methods used by default? If parametric, is there non-parametric cross-validation? |
| Real-price outcome discipline | Are strategy returns, signal returns, and excursion outcomes computed from real time-matched prices unless explicitly scoped as non-tradable diagnostics? |
| Timestamp alignment | Are cross-view comparisons always aligned by timestamp, never by bar count or row index? |

### 5. OOS Holdout Rule

The final 30% of the dataset is a global holdout — never loaded, inspected, or used.

| Check | What to Verify |
|-------|---------------|
| Holdout untouched | Does any code path, analysis step, or scope boundary access data beyond the 70% cutoff? |
| Chronological split | Is the split ordered by CloseTime/SourceCloseTime, not random? (Financial data has temporal structure.) |
| Train/test within analysis set | If train/test split is used, is it within the 70% analysis set, not touching the holdout? |

### 6. Look-Ahead Bias Prevention

Event and feature generation must use only information available at or before the event timestamp. Chart-type generators, when in scope, must process data sequentially.

| Check | What to Verify |
|-------|---------------|
| Sequential generation | Do generators use only data available at or before each bar's timestamp? |
| No future data | Does any analysis use data from after the event timestamp? |
| Event timestamp alignment | Are event timestamps, `CloseTime`, or `SourceCloseTime` used for temporal alignment as appropriate? |
| Bar-index alignment ban | Are cross-view comparisons aligned by timestamp, not by bar count? |

### 7. Real-Price and Synthetic-Price Discipline

Strategy P&L, signal returns, and excursion outcomes must use real time-matched prices. Heiken Ashi prices and Renko brick prices are synthetic chart-construction prices and are prohibited for strategy P&L.

| Check | What to Verify |
|-------|---------------|
| Real prices used | Are strategy and signal outcomes computed from time-bar OHLC prices? |
| No HA returns | If Heiken Ashi is in scope, are strategy returns computed from RealClose (or time-bar Close), never from HA-Close? |
| No HA signal validation via HA prices | If Heiken Ashi is in scope, are signal quality metrics computed on real prices, not HA prices? |
| No Renko brick P&L | If Renko is in scope, are Renko signal returns computed from time-matched real prices, never from brick open/close levels? |

### 8. Safe Performance and Memory Optimization

Large-dataset code must be proactively efficient, but never by changing the
research question or temporal semantics.

| Check | What to Verify |
|-------|---------------|
| Efficient Polars use | Are filters/projections pushed into lazy scans, with aggregation before collection where possible? |
| Bounded memory | Are plotting inputs, iteration outputs, and intermediate frames bounded or written once rather than accumulated unbounded? |
| Safe vectorization | Do vectorized joins, windows, or NumPy operations preserve the same sample membership, denominators, and timestamps as the explicit method? |
| No causality breach | Does optimization avoid future rows, batch-only shortcuts presented as streaming-safe, and look-ahead bias? |
| Progress visibility | Do multi-file, multi-instrument, parameter-grid, validation-window, or simulation loops show `tqdm` progress without noisy row-level logging? |

---

## Artifact-Specific Checks

### Scope Document (scope.md)

| Check | Questions |
|-------|-----------|
| Hypothesis quality | Is it testable, falsifiable, specific? No weasel words. |
| Success criteria | Are they concrete and measurable, not subjective judgments? |
| Data views defined | Are all data views, feature families, parameters, and timeframes explicitly stated? |
| Scope boundaries | Are instruments, time range, and exclusions all explicit? |
| Complexity budget | Does it match the scope? Is it realistic? |
| Holdout exclusion | Does the scope explicitly exclude the global holdout? |
| Real-price outcome rule | Does the scope explicitly state what prices are used for returns, excursions, P&L, stops, and targets? |
| Gate-threshold calibration | Is every binding gate/composition threshold either calibrated to the realized cell layout, data-derived/mechanically selected, or shipped with a pre-registered sensitivity band shown to leave routing invariant — not an unjustified magic constant? Borrowed/analogy constants must be disclosed as such and stress-tested. |

### Analysis Plan (analysis-plan.md)

| Check | Questions |
|-------|-----------|
| Method justification | Is each method choice justified with "why this method" and "simpler alternative considered"? |
| Assumptions listed | Does each method document its assumptions and whether they hold for time-ordered financial data? |
| Cross-view alignment | Does the plan specify how data views or event sets are aligned by timestamp, not bar count? |
| Visualisation plan | Are plots purposeful (answering specific sub-questions), not decorative? |
| Interpretation guide | Are outcomes pre-defined (if X then Y because Z) to prevent post-hoc rationalisation? |
| Per-stratum endpoints | Are binding endpoints adjudicated per stratum, with any pooled/aggregated figure declared disclosure-only unless cross-stratum homogeneity is itself tested? |
| Shape-aware reads | If the hypothesis admits a non-location effect shape (tails, bimodality, asymmetry), is a shape-aware read predeclared alongside the standard location guard, so a shape effect is caught in-experiment rather than forcing a follow-up? |
| Robust + raw endpoints | When the signal sits over asymmetric/bimodal geometry, are both a robust/median endpoint and the binding raw economic endpoint emitted, so the robust-vs-raw gap is available as a diagnostic? |
| Budget compliance | Do total tests, plots, modules stay within the complexity budget? |

### Code (code/run_experiment.py)

| Check | Questions |
|-------|-----------|
| Plan compliance | Does the code implement exactly what the analysis plan specifies — nothing more, nothing less? |
| Holdout exclusion | Is only the first 70% of time-ordered data loaded? No code path accesses the holdout. |
| Look-ahead bias prevention | Is all temporal ordering by CloseTime/SourceCloseTime? No use of future data relative to event time. |
| Real-price outcome check | Are returns and excursions computed from real prices unless explicitly scoped as non-tradable diagnostics? |
| Timestamp alignment | Are cross-view comparisons aligned by timestamp, not bar index? |
| Type safety | Are type hints on all public functions? Are types consistent? |
| NaN handling | Is NaN handling explicit — no silent propagation? |
| Edge cases | Are empty DataFrames, single-element arrays, division by zero handled? |
| Separation of concerns | Are analysis functions (pure computation) separated from plotting and orchestration? |
| No magic numbers | Are all thresholds derived from data or documented? |
| Code quality | PEP 8, docstrings, descriptive names, ~30 line function limit? |
| Data loading | Is Polars/Parquet used correctly? Are columns properly selected before `collect()`? |
| Organization | Are imports, path setup, constants, I/O helpers, computation helpers, plotting helpers, orchestration, and `main()` clearly separated? |
| Sectioning | Are non-trivial scripts sectioned in the VAL-001 style so constants, helpers, checks, plotting/output, orchestration, and `main()` are easy to review? |
| Import side effects | Does module import avoid creating directories, writing files, loading data, or plotting? |
| Logging/output | Is manual-run output concise and traceable, with helper functions returning data instead of printing? |
| Progress tracking | Do long-running outer loops use `tqdm` or equivalent progress without per-row noise? |
| Plot memory | Are plot inputs aggregated or sampled before pandas conversion? |
| Repeated heavy work | Does plotting reuse analysis outputs instead of reloading or regenerating large datasets? |
| Derived-view determinism | If generators or feature builders are called, are they deterministic or explicitly seeded? |
| Safe optimization | Do performance improvements preserve correctness, sample membership, temporal ordering, denominators, metric definitions, and streaming semantics? |
| Vectorization discipline | Are Python row loops replaced where safely possible, while genuinely sequential logic remains sequential and bounded? |

### Audit Report (audit.md)

| Check | Questions |
|-------|-----------|
| Thoroughness | Are correctness, edge cases, type safety, NaN handling, holdout exclusion, look-ahead bias, and synthetic price discipline all checked? |
| Evidence | Does every finding include specific line numbers, values, or code excerpts? |
| Severity classification | Are issues classified as Critical, Warning, or Info appropriately? |
| Numerical validation | Are spot checks, boundary checks, statistical sanity checks included? |
| Scope compliance | Does the audit verify that code matches the analysis plan? |
| Real-price outcome audit | Does audit verify that strategy and signal outcomes use scoped real prices? |
| Timestamp alignment audit | Does audit verify cross-view alignment by timestamp? |
| Verdict forensics present | Does the audit explain *why* the verdict came out — a mechanism statement, not just a numeric confirmation? Was it run autonomously, not only after an operator questioned the result? |
| Per-stratum masking check | Does the audit re-derive the verdict per domain/instrument/cell and affirmatively confirm any pooled/aggregated/equal-weight headline is not masking heterogeneity? |
| Gate-shape check | Does the audit check whether the binding gate can see the effect's shape (location vs tail/bimodal/asymmetric), and distinguish "no effect" from "wrong instrument for the shape"? |
| Materiality & blocking | Is every Critical finding tied to the verdict-bearing number it moves (forcing fix + rerun), and every Warning/Info justified as unable to move any verdict-bearing number? |

### Results Interpretation (results.md)

| Check | Questions |
|-------|-----------|
| Honest reporting | Does it state what the data shows, not what was expected? |
| Uncertainty acknowledged | Are limitations, confidence intervals, and alternative explanations included? |
| No overreaching | If effect sizes are small, does it say so? No inflating weak findings. |
| Verdict supported | Is the SUPPORTED/REFUTED/INCONCLUSIVE conclusion justified by the evidence? |
| Next steps reasonable | Are follow-up suggestions specific new experiments, not scope extensions? |
| Real-price outcome results | Are all strategy P&L and signal metrics computed on scoped real prices? |

### Final Report (report.md)

| Check | Questions |
|-------|-----------|
| Self-contained | Can a reader with project context but no experiment knowledge understand it? |
| Key visualisations included | Are the most important plots embedded with captions? |
| Honest about limitations | Are negative results, inconclusive findings, and caveats included? |
| Artifacts linked | Are all experiment artifacts referenced by relative path? |
| Index updated | Is `python/experiments/INDEX.md` entry correct? Is the detailed card added to the relevant `docs/experiments-docs/families/<family>/INDEX.md`, and is `docs/experiments-docs/INDEX.md` (master) live status / `Family Indexes` table updated? |
| Registry & ledger disposition | Is a signal-registry disposition recorded for this experiment? If registry-relevant: candidate-family status advanced in `docs/signal-registry/candidate-families/<family>.md`, item outcome recorded in `multiplicity-registry.md` (refuted/blocked/inconclusive retained), and any counted TEST read or disclosure entered in `test-read-ledger.md`? If not registry-relevant: is the reason noted? |

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

Issues that warrant REVISE include: an audit lacking verdict forensics or the per-stratum masking check; an audit that accepted a pooled/aggregated verdict without re-deriving it per stratum; a verdict-material finding documented but not fixed-and-rerun; and a binding gate threshold that is an unjustified magic constant (not calibrated, data-derived, or sensitivity-banded).

### REJECT

Fundamental, unfixable issues. Examples:
- Holdout contamination (data from the 30% reserve was used)
- Look-ahead bias (using data from after the event timestamp when analyzing an event)
- Synthetic price violation (computing strategy P&L from Heiken Ashi prices or
  Renko brick prices instead of real prices; `HAClose` diagnostic returns are
  allowed only for explicitly scoped HA distortion experiments that label them
  non-tradable)
- Unsafe optimization (vectorized or cached implementation changes sample
  membership, temporal ordering, denominators, metric definitions,
  interpretation, or streaming/causal semantics)
- Bar-index alignment (comparing chart types by bar index instead of timestamp)
- Scope creep beyond what can be fixed with revision
- Method fundamentally violates core constraints (e.g., assumes normality with no cross-validation)
- Dishonest or fabricated results

Hard stop. Cannot be overridden.
