# Experiment Templates

Standard templates for all experiment artifacts. Use these templates consistently — do not invent custom formats.

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

- **Features**: <which TriLattice features are used, referencing the 30-column schema in `docs/references/dataset-reference.md`>
- **Feature Categories**: 
  - [ ] Pivot Metadata (Timestamp, PeakTime, ConfirmTime, etc.)
  - [ ] Structure Labeling (Label, Regime, IsAmbiguous, IsTrainingTarget)
  - [ ] Bar Features (BarReturn, BarRange, BarDuration, etc.)
  - [ ] Structure Features (PriceDistanceToPrior, TimeDistanceToPrior, Slope, etc.)
  - [ ] Context Features (SequenceContext, ContextRegime, Session, ImbalanceFlag, ValidationStatus)
- **Validation Filter**: <whether to use only `ValidationStatus == "Valid"` or include artifacts>
- **Instruments**: <which symbols (any cTrader-available instrument)>
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set (split 70/30 for train/test); final 30% = global holdout (never used).
- **Global holdout**: The final 30% of the full dataset must not be loaded, inspected, or used in any capacity.
- **Look-ahead bias prevention**: All labels assigned at `ConfirmTime` — analysis must respect this.
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

<Pre-processing, filtering, transformations needed before analysis.>

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("/Users/jerryinyang/cAlgo/Sources/Robots/TriLattice/TriLattice/data")
path = sorted(DATA_DIR.glob("features_*.parquet"))[-1]

df = (
    pl.scan_parquet(path)
    .select(["ConfirmTime", "Label", "Regime", "BarReturn", "ValidationStatus"])
    .filter(pl.col("ValidationStatus") == "Valid")  # Adjust as needed
    .sort("ConfirmTime")
    .collect()
)

df = df.drop_nulls().to_pandas()
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
- **Assumptions**: <what this method assumes; whether it holds for TriLattice data>
  - **Temporal structure**: Data has chronological ordering by ConfirmTime
  - **Label validity**: Consider ValidationStatus filter implications
  - **Regime conditioning**: May need to stratify by Regime/ContextRegime
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

## TriLattice-Specific Considerations

### Look-ahead Bias Prevention
- ConfirmTime is the authoritative timestamp for all temporal ordering
- Never use PeakTime for sorting or windowing (it represents detection, not confirmation)

### Validation Status Handling
- Default: Use only `ValidationStatus == "Valid"` pivots
- If including artifacts, document rationale and impact on results

### Regime Stratification
- Consider analyzing Low/Medium/High volatility regimes separately
- Use ContextRegime for the regime at feature emission time

### Feature Encoding
- String enums (Label, Regime, PivotType, etc.) may need numeric encoding for certain methods
- Use encoding from _pipeline-config.md Enum Encoding Reference
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
| <file> | Holdout exclusion | PASS/FAIL | <verify only first 70% of ConfirmTime-ordered data is used> |
| <file> | Look-ahead bias | PASS/FAIL | <verify ConfirmTime used for temporal ordering, not PeakTime> |
| <file> | Validation status | PASS/FAIL | <verify ValidationStatus handling matches scope> |
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
**Levels**: <which>

---

## Question

<The plain-language question this experiment answered.>

## Hypothesis

<The testable hypothesis.>

## Method Summary

<2–3 sentence description of the analytical approach. Reference analysis-plan.md for details.>

## Key Findings

### Finding 1: <Title>

<Description with supporting evidence.>

![Plot caption](plots/<filename>.png)

<Interpretation: what this means for the hypothesis.>

### Finding 2: <Title>

...

## Conclusion

<Clear statement: hypothesis SUPPORTED / REFUTED / INCONCLUSIVE.>

<1–2 paragraph explanation of what we learned and why it matters.>

## Limitations

- <Limitation 1>
- <Limitation 2>

## Implications for Future Research

- <What new questions does this raise?>
- <What ideas from docs/ideas.md should be prioritised/deprioritised?>

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

| Artifact | Data-Driven | Non-Parametric | Adaptive | Holdout Excluded |
|----------|------------|---------------|----------|-----------------|
| <artifact> | PASS/FAIL | PASS/FAIL | PASS/FAIL | PASS/FAIL |

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
```
