# Audit Checklists

Templates and checklists for the Research Auditor.

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
| <file> | Holdout exclusion | PASS/FAIL | <details> |
| <file> | Docstrings | PASS/FAIL | <details> |

## Numerical Validation

### Spot Checks

<Manual computation results vs code output. Show the math for at least one example.>

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| Correlation values | [-1, 1] | [<min>, <max>] | YES/NO |
| Percentages | [0, 100] or [0, 1] | [<min>, <max>] | YES/NO |
| Counts | ≥ 0 | [<min>, <max>] | YES/NO |
| ConfirmationStrength | ≥ 0 | [<min>, <max>] | YES/NO |
| PriceMomentum | {-1, 0, +1} | [<min>, <max>] | YES/NO |
| BarReturn / BarRange | ℝ (check for extreme outliers) | [<min>, <max>] | YES/NO |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| <p-value 1> | <value> | YES/NO | <rationale> |
| <CI 1> | <value> | YES/NO | <rationale> |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| <method> | <assumption> | YES/NO/PARTIAL | <evidence> |

## Results Plausibility

<Are outputs within expected domain ranges? Do patterns make sense?>

## Scope Compliance

- Analysis plan followed: YES / NO
- Deviations: <list or "none">
- Complexity budget: <actual tests> / <budgeted>, <actual plots> / <budgeted>, <actual modules> / <budgeted>
- Holdout exclusion verified: YES / NO

## Issues

### Critical

<Number>. **<Issue title>**
   - File: `<path>`, line <N>
   - Description: <what's wrong>
   - Impact: <what could go wrong>
   - Fix: <how to fix it>

### Warning

<Number>. **<Issue title>**
   - File: `<path>`, line <N>
   - Description: <what's wrong>
   - Impact: <what could go wrong>
   - Fix: <how to fix it>

### Info

<Number>. **<Issue title>**
   - Description: <note for awareness>

## Re-Audit Requirements

<If CONDITIONAL PASS, what must be fixed and how to verify the fix.>
```

---

## Quick Checklists

### Common Bug Patterns to Look For

| Pattern | Where to Look | How to Check |
|---------|--------------|-------------|
| Off-by-one in lagged features | Any `shift()` or index-1 operations | Verify the shift direction and magnitude |
| NaN silent propagation | Any computation on DataFrame columns | Check for `isna()` checks or `dropna()` calls |
| Wrong split (random vs chronological) | Data splitting code | Verify `.iloc[:N]` not `train_test_split` |
| Holdout contamination | Any data loading | Verify `int(len(df) * 0.7)` cutoff is applied before any analysis |
| String/numeric confusion | `Label` or `Regime` column comparisons | Verify `"HH"/"HL"/"LH"/"LL"` and `"Low"/"Medium"/"High"` string comparisons, not numeric |
| Look-ahead bias | Temporal ordering code | Verify `ConfirmTime` used for sorting, not `PeakTime` |
| Validation status filter | Data loading code | Verify `ValidationStatus` filter matches scope specification |
| Division by zero | Any ratio computation | Check for denominator > 0 guard |
| Wrong sample size in CI | Bootstrap or statistical test calls | Verify the `n=` passed matches actual data size |

### Value Range Reference

Use these ranges for plausibility checks (from `_pipeline-config.md`):

| Feature | Expected Range | Notes |
|---------|---------------|-------|
| `BarReturn`, `BarRange` | ℝ | Can be positive or negative (price returns/ranges) |
| `TickDensity` | ≥ 0 | Ticks per second |
| `VolatilityProxy` | ≥ 0 | EMSTD of bar returns |
| `PriceDistanceToPrior` | ≥ 0 or null | Absolute price change from previous pivot |
| `TimeDistanceToPrior` | ≥ 0 or null | Seconds since previous pivot |
| `Slope` | ℝ | Price distance / time distance |
| `ConfirmationStrength` | ≥ 0 | Reversal magnitude at confirmation |
| `Label` | "HH", "HL", "LH", "LL", "Ambiguous" | Structure labeling, string column |
| `Regime` | "Low", "Medium", "High" | Volatility regime, string column |
| `ValidationStatus` | "Valid", "Artifact", "Pending" | Cross-representation validation result |
| `IsAmbiguous` | {true, false} | Boolean flag for ambiguous structure |
| `IsTrainingTarget` | {true, false} | Boolean flag for time-triggered low-confidence |

### Audit Proportionality Guide

| Experiment Complexity | Audit Depth |
|----------------------|-------------|
| Descriptive / EDA (0-1 tests, 2-4 plots) | Light: check holdout exclusion, value ranges, scope compliance |
| Single hypothesis (1-2 tests, 2-3 plots) | Standard: all six dimensions |
| Comparative across instruments (2-4 tests, 3-5 plots) | Thorough: all six dimensions + cross-instrument consistency |
| Multi-feature relationship (2-3 tests, 3-5 plots) | Thorough: all six dimensions + interaction checks |
