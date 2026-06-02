# Experiment Templates

Standard templates for all Xen experiment artifacts. Use these templates consistently — do not invent custom formats.

---

## Scope Document Template

Save to: `python/experiments/<EXP-ID>/scope.md`

```markdown
# Experiment: <EXP-ID> — <Title>

## Hypothesis

<One clear, testable, falsifiable statement. Or an explicit exploratory question.>

## Question

<The plain-language question this experiment answers.>

## Scope Boundaries

- **Data Views**: <Time bars, derived feature tables, or chart types if explicitly included>
- **Parameters**: <timeframe(s), windows, thresholds, chart-type parameters, or other scoped constants>
- **Instruments**: <EURUSD, XAUUSD, BTCUSD, USTEC — which and why>
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set (split 70/30 for train/test); final 30% = global holdout (never used).
- **Global holdout**: The final 30% of the full dataset must not be loaded, inspected, or used in any capacity.
- **Look-ahead bias prevention**: Features and events use only data available at or before the event timestamp. Chart-type generators, if in scope, process data sequentially and use `SourceCloseTime` for temporal alignment.
- **Real-price outcome discipline**: Strategy and signal-return metrics use time-bar OHLC prices aligned by timestamp. No strategy P&L from Heiken Ashi prices or Renko brick prices. HA synthetic returns are allowed only for explicitly scoped, non-tradable distortion diagnostics.
- **Exclusions**: <what is explicitly NOT in scope>

## Success / Failure Criteria

- **Evidence FOR**: <concrete, measurable condition with threshold and significance>
- **Evidence AGAINST**: <concrete, measurable condition>
- **Inconclusive**: <when do we declare "can't tell">

## Complexity Budget

- Max statistical tests: <N>
- Max visualisations: <N>
- Max new code modules: <N>

## Data Requirements

<Pre-processing, filtering, transformations needed before analysis. Which chart types, which generators, which parameters.>

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]

scan = pl.scan_parquet(path).sort("CloseTime")
total_rows = int(scan.select(pl.len()).collect().item())
analysis_cutoff = int(total_rows * 0.7)
bars = scan.slice(0, analysis_cutoff).collect()
```

## Suggested Direction

<Brief, non-binding suggestion of analytical approach.>
```

---

## Analysis Plan Template

Save to: `python/experiments/<EXP-ID>/analysis-plan.md`

```markdown
# Analysis Plan: Experiment <EXP-ID>

## Objective

<Restate the hypothesis/question and what we need to determine.>

## Methodology

### Step 1: <Step Name>

- **Method**: <name of statistical/computational method>
- **Why this method**: <justification, especially re: simplicity>
- **Simpler alternative considered**: <what and why it doesn't suffice, or is equivalent>
- **Assumptions**: <what this method assumes; whether it holds for time-ordered financial data>
  - **Temporal structure**: Data has chronological ordering by `CloseTime` or event timestamp.
  - **Cross-view alignment**: Comparisons are by timestamp, not bar index.
  - **Real-price outcomes**: Strategy and signal metrics use real time-bar prices. Synthetic chart prices appear only in explicit non-tradable diagnostics.
- **Expected output**: <what this step produces — a number, a plot, a table>

### Step 2: ...

## Visualisations

1. <Plot type> of <what> — <what it shows and why>
2. ...

## Interpretation Guide

- If we observe <X>, it means <Y> because <Z>.
- If we observe <A>, it means <B> because <C>.
- If we observe <C>, the result is inconclusive because <D>.

## Complexity Check

- Statistical tests: <planned> / <budget>
- Visualisations: <planned> / <budget>
- New modules: <planned> / <budget>

## Data-View Comparison Considerations

### Cross-View Alignment
- Different data views or event detectors may produce different numbers of observations for the same time period.
- Always align by timestamp (`CloseTime`, event timestamp, or `SourceCloseTime`), never by bar index.
- Report alignment or coverage rates where event detectors emit sparse events.

### Implementation Safety and Performance
- Use lazy Polars scans, column projection, and aggregation before collection
  where possible.
- Use `tqdm` progress tracking for long-running file, instrument, chart-view,
  parameter-grid, validation-window, or simulation loops.
- Replace Python row loops with Polars/NumPy/vectorized logic only when the
  replacement preserves temporal causality and streaming semantics.
- Keep genuinely sequential logic explicit and bounded.
- Do not optimize by changing sample membership, temporal ordering,
  denominators, metric definitions, statistical interpretation, or
  reproducibility.

### Real-Price Outcome Discipline
- Compute strategy P&L, signal returns, and excursion outcomes from real time-bar prices.
- Never compute strategy P&L from Heiken Ashi HA prices or Renko brick prices.
- Use `HAClose` returns only when the approved scope is an HA synthetic-price distortion diagnostic and labels them non-tradable.
- For Line Break and Renko, use `SourceCloseTime`-aligned time-bar prices.

### Event Density Differences
- Event detectors may emit far fewer observations than the time-bar baseline.
- Statistical comparison must account for different sample sizes and coverage.
- Consider density-normalised metrics where appropriate.

### Regime Stratification
- Consider analyzing low/medium/high volatility regimes separately
- Regime labels are derived from time-bar realised volatility, applied uniformly across chart types
```

---

## Audit Report Template

Save to: `python/experiments/<EXP-ID>/audit.md`

```markdown
# Audit Report: Experiment <EXP-ID>

## Summary

- **Verdict**: PASS / FAIL / CONDITIONAL PASS
- **Critical Issues**: <count>
- **Warnings**: <count>
- **Info Notes**: <count>

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| <file> | Correctness | PASS/FAIL | <details> |
| <file> | Edge cases | PASS/FAIL | <details> |
| <file> | Type safety | PASS/FAIL | <details> |
| <file> | NaN handling | PASS/FAIL | <details> |
| <file> | Holdout exclusion | PASS/FAIL | <verify only first 70% of time-ordered data is used> |
| <file> | Look-ahead bias | PASS/FAIL | <verify SourceCloseTime used for temporal alignment> |
| <file> | Synthetic price discipline | PASS/FAIL | <verify no strategy P&L computed from HA prices or Renko brick prices> |
| <file> | Chart-type alignment | PASS/FAIL | <verify alignment by timestamp, not bar index> |
| <file> | Generator determinism | PASS/FAIL | <verify generators produce identical output from identical input> |
| <file> | Safe optimization | PASS/FAIL | <verify performance choices preserve causality, denominators, and interpretation> |
| <file> | Progress tracking | PASS/FAIL | <verify long-running loops use tqdm or equivalent clean progress> |
| <file> | Logging/output | PASS/FAIL | <verify output is concise and traceable> |
| <file> | Docstrings | PASS/FAIL | <details> |

## Numerical Validation

### Spot Checks

<Manual computation results vs code output.>

### Statistical Checks

<Sanity of p-values, CIs, effect sizes, correlation ranges.>

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| <method> | <assumption> | YES/NO/PARTIAL | <evidence> |

## Results Plausibility

<Are outputs within expected domain ranges? Do patterns make sense?>

## Scope Compliance

- Analysis plan followed: YES / NO
- Deviations: <list or "none">
- Complexity budget: <actual> / <budgeted>
- Holdout exclusion verified: YES / NO

## Issues

### Critical

<Number>. **<Issue title>**
   - File: `<path>`, line <N>
   - Description: <what's wrong>
   - Impact: <what could go wrong>
   - Fix: <how to fix it>

### Warning

...

### Info

...

## Re-Audit Requirements

<If CONDITIONAL PASS, what must be fixed before re-audit.>
```

---

## Results Interpretation Template

Save to: `python/experiments/<EXP-ID>/results.md`

```markdown
# Results: Experiment <EXP-ID>

## Summary

<One-paragraph summary of findings.>

## Detailed Findings

### <Finding 1>

- **Observation**: <what the data shows>
- **Evidence**: <specific numbers, plot references>
- **Interpretation**: <what it means for the hypothesis>

### <Finding 2>

...

## Hypothesis Verdict

**SUPPORTED / REFUTED / INCONCLUSIVE**

<Explanation with evidence summary.>

## Limitations

- <limitation 1>
- <limitation 2>

## Alternative Explanations

- <alternative interpretation of the data>

## Recommended Next Steps

1. <Next experiment suggestion as a new EXP-ID>
2. <Idea to explore>
```

---

## Experiment Report Template

Save to: `python/experiments/<EXP-ID>/report.md`

```markdown
# Experiment Report: <EXP-ID> — <Title>

## Status: COMPLETED / INCONCLUSIVE / FAILED

**Date**: <completion date>
**Instruments**: <which>
**Chart Types**: <which>

---

## Question

<The plain-language question this experiment answered.>

## Hypothesis

<The testable hypothesis.>

## Method Summary

<2-3 sentence description of the analytical approach. Reference analysis-plan.md for details.>

## Key Findings

### Finding 1: <Title>

<Description with supporting evidence.>

![Plot caption](plots/<filename>.png)

<Interpretation: what this means for the hypothesis.>

### Finding 2: <Title>

...

## Conclusion

<Clear statement: hypothesis SUPPORTED / REFUTED / INCONCLUSIVE.>

<1-2 paragraph explanation of what we learned and why it matters.>

## Limitations

- <Limitation 1>
- <Limitation 2>

## Implications for Future Research

- <What new questions does this raise?>
- <What chart-type comparisons should be prioritised/deprioritised?>

## Recommended Next Experiments

1. **EXP-XXX (proposed)**: <Brief description of follow-up>
2. ...

## Artifacts

| Artifact | Path |
|----------|------|
| Scope | [scope.md](scope.md) |
| Analysis Plan | [analysis-plan.md](analysis-plan.md) |
| Code | [code/](code/) |
| Audit | [audit.md](audit.md) |
| Results | [results.md](results.md) |
| Governance Reviews | [governance/](governance/) |
| Plots | [plots/](plots/) |
```

---

## Governance Review Template

Save to: `python/experiments/<EXP-ID>/governance/pre-execution-review.md` or `post-experiment-review.md`

```markdown
# Governance Review: Experiment <EXP-ID> — <Review Type>

**Date**: <date>
**Review Type**: Pre-Execution / Post-Experiment
**Artifacts Reviewed**: <list>

## Executive Summary

<One-line summary of the verdict.>

## Constraint Checks

### Simplicity Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| <artifact> | PASS/FLAG/FAIL | <rationale> |

### Academic-Finance Pitfall Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| <artifact> | PASS/FLAG/FAIL | <rationale> |

### Scope Compliance Check

| Artifact | Verdict | Notes |
|----------|---------|-------|
| <artifact> | PASS/FLAG/FAIL | <rationale> |

### Principles Check

| Artifact | Data-Driven | Non-Parametric | Phantom Price Discipline | Holdout Excluded |
|----------|------------|---------------|--------------------------|-----------------|
| <artifact> | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL |

### Chart-Type Comparison Check

| Artifact | Timestamp Alignment | Bar Count Adjustment | Generator Determinism |
|----------|-------------------|---------------------|---------------------|
| <artifact> | PASS/FAIL | PASS/FAIL | PASS/FAIL |

### Quality Check (type-specific)

| Artifact | Verdict | Notes |
|----------|---------|-------|
| <artifact> | PASS/FLAG/FAIL | <rationale> |

## Findings

### Critical (if any)

<Specific issues that block proceeding.>

### Warnings (if any)

<Issues that should be addressed but don't block.>

### Info (if any)

<Notes for awareness.>

## Verdict

```
VERDICT: APPROVE
```

or

```
VERDICT: REVISE
FAILING_ARTIFACT: <scope.md | analysis-plan.md | code/run_experiment.py | audit.md | results.md | report.md>
REQUIRED_SKILL: <scope-design | experiment-quant-analyst | experiment-developer | experiment-auditor | experiment-documenter>
ISSUES:
1. <specific issue with line reference and remediation>
2. ...
```

or

```
VERDICT: REJECT
REASON: <brief explanation>
```
