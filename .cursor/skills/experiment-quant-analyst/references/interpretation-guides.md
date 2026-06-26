# Interpretation Guides

Templates and guidance for writing analysis plans and results interpretations.

---

## Analysis Plan Template

Save to: `python/experiments/<EXP-ID>/analysis-plan.md`

```markdown
# Analysis Plan: Experiment <EXP-ID>

## Objective

<Restate the hypothesis/question and what we need to determine.>

## Methodology

### Step 1: <Step Name>

- **Method**: <name>
- **Why this method**: <justification, especially re: simplicity>
- **Simpler alternative considered**: <what and why it doesn't suffice, or is equivalent>
- **Assumptions**: <what this method assumes; whether it holds for time-ordered financial data>
- **Expected output**: <what this step produces>

### Step 2: ...

## Visualisations

1. <Plot type> of <what> — <what it shows and why>
2. ...

## Interpretation Guide

- If we observe <X>, it means <Y> because <Z>.
- If we observe <A>, it means <B> because <C>.

## Complexity Check

- Statistical tests: <planned> / <budget>
- Visualisations: <planned> / <budget>
- New modules: <planned> / <budget>
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

## Interpretation Writing Guidelines

### Be Honest

- Report what the data shows, not what you hoped.
- If the hypothesis is refuted, say so clearly. Refuted hypotheses are valuable — they eliminate wrong paths.
- If results are inconclusive, explain why (sample size too small? effect too weak? noise too high?).

### Quantify Uncertainty

- Always include confidence intervals or bootstrap ranges.
- Report effect sizes, not just p-values. A tiny effect with p < 0.001 is still tiny.
- Note the sample size (n) for every reported statistic.

### Consider Alternatives

- Could the observed pattern be explained by something other than the hypothesis?
- Are there confounding factors not controlled for?
- Is there a simpler explanation that fits the data equally well?

### Don't Overreach

- If the effect was found in one instrument only, don't generalise to all instruments.
- If the sample size is small, acknowledge limited power.
- If the analysis was exploratory (not pre-registered), note that findings are hypothesis-generating, not hypothesis-confirming.

### Structure for Clarity

- Lead with the most important finding.
- Use specific numbers, not vague descriptions.
- Reference plots by name.
- Keep it concise — 1-2 pages of content for a typical experiment.
