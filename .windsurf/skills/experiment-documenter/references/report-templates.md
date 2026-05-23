# Report Templates

Templates for experiment reports and index entries.

---

## Experiment Report Template

Save to: `python/experiments/<EXP-ID>/report.md`

```markdown
# Experiment Report: <EXP-ID> — <Title>

## Status: COMPLETED / INCONCLUSIVE / FAILED

**Date**: <completion date>
**Instruments**: <which>
**Data Views / Feature Categories**: <which, e.g. time bars, macro windows, sweeps, chart types if scoped>

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

- <Limitation 1: e.g., tested on one instrument only>
- <Limitation 2: e.g., sample size for low-volatility regime events was small>

## Implications for Future Research

- <What new questions does this raise?>
- <What ideas from docs/ideas.md should be prioritised/deprioritised based on this?>

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

## Experiment Index Template

File: `python/experiments/INDEX.md`

```markdown
# Experiment Index

| ID | Title | Status | Key Finding | Date |
|----|-------|--------|-------------|------|
| EXP-001 | ... | COMPLETED | <one-line finding> | YYYY-MM-DD |
| EXP-002 | ... | INCONCLUSIVE | <one-line finding> | YYYY-MM-DD |
| EXP-003 | ... | FAILED | <reason> | YYYY-MM-DD |
```

### Status Values

| Status | Meaning |
|--------|---------|
| `COMPLETED` | All stages passed governance. Definitive finding. |
| `INCONCLUSIVE` | Results were ambiguous or effect was too weak to conclude. Not a failure — we learned we can't tell. |
| `FAILED` | Critical issues found that invalidate results. Document the reason. |
| `ABANDONED` | Experiment was not completed (e.g., superseded, scope changed). |

---

## Comprehensive Experiment Index Template

File: `docs/experiments-docs/INDEX.md`

This is the authoritative detailed catalog of all experiments. Append each experiment as a new section when the experiment completes.

```markdown
## <EXP-ID> — <Title>

**Status**: COMPLETED / INCONCLUSIVE / FAILED
**Date**: YYYY-MM-DD
**Instruments**: <which>
**Data Views / Feature Categories**: <which>

### Hypothesis Tests

1. **Hypothesis**: <exact formulation from scope.md>
   - If sub-hypotheses exist, list them separately.

### Scope

- **Instruments**: <tested instruments>
- **Data Views / Feature Categories**: <which categories used>
- **Features**: <specific Xen features used, e.g. macro-window flag, sweep event, Direction, SourceCount, RealClose returns>
- **Parameter ranges**: <ranges tested>
- **Exclusions**: <what was explicitly excluded>
- **Constraints**: <key assumptions and constraints>

### Results / Observations

- <Key metric with value, e.g., `E_norm_cost = +0.677`, `WR_TP = 30.5%`>
- <Reproduce essential tables here if they contain critical data>

> Note: No interpretation — preserve what the data shows.

### Hypothesis-Specific Conclusion

**<SUPPORTED / REFUTED / INCONCLUSIVE / PARTIALLY SUPPORTED / MARGINAL>**

<1–3 sentences referencing any predefined success thresholds.>

### Hypothesis-Agnostic Observations

- <Trade-off revealed, e.g., "circuit breaker reduces drawdown but also reduces return">
- <Secondary finding that could inform future experiments>
- <Practical implication regardless of verdict>
```

**Guidelines for five-field extraction:**

- **Results / Observations**: Extract factual outputs only — no interpretation. Reproduce tables where they contain essential data.
- **Hypothesis-Specific Conclusion**: Keep to 1–3 sentences. Reference predefined success thresholds if defined in scope.
- **Hypothesis-Agnostic Observations**: Apply selectively — only when unambiguous in the data. Do not speculate or contradict the hypothesis-specific conclusion.

---

## Writing Examples

### Good: Specific and Honest

```
## Conclusion

**Hypothesis REFUTED.**

The data shows no evidence that the scoped signal predicts
next-bar RealClose return (Spearman rho = 0.02, 95% CI [-0.01, 0.05],
p = 0.18). The effect, if it exists, is smaller than our minimum
detectable effect size of 0.10 given our sample of 14,233 valid EURUSD
events.

This means that direction agreement does not reliably predict subsequent
bar returns in this dataset. We should deprioritise this line of research
and focus on features with stronger predictive signals.
```

### Bad: Vague and Overreaching

```
## Conclusion

The hypothesis was not supported. There doesn't seem to be much of a
relationship. Maybe other features would work better.
```

---

## Plot Selection Guide

| Experiment Type | Recommended Plots to Include |
|----------------|----------------------------|
| Descriptive | Distribution histogram, summary table |
| Correlation | Scatter plot with regression line, correlation coefficient with CI |
| Comparative | Side-by-side box plots or violin plots |
| Temporal | Time-series plot with key events annotated |

Include 2-4 plots maximum. The report should be readable without viewing all plots — the plots support the key findings, they are not the findings themselves.
