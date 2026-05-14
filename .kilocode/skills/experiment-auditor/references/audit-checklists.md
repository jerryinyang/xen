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
| Direction | {+1, -1} | [<min>, <max>] | YES/NO |
| RealClose returns | ℝ (check for extreme outliers) | [<min>, <max>] | YES/NO |
| TickVolume / SourceCount | ≥ 0 | [<min>, <max>] | YES/NO |
| SourceCloseTime | Monotonically increasing | [<first>, <last>] | YES/NO |

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
| String/numeric confusion | `Direction` column comparisons | Verify `Direction` is `+1/-1` (int), not string |
| Look-ahead bias | Temporal ordering code | Verify `CloseTime` or `SourceCloseTime` used for sorting, never bar index |
| Synthetic price returns | Any return computation on HA or Renko-derived signals | Verify returns use real time-matched prices, never `HAClose` or Renko brick prices |
| Cross-chart-type alignment | Any comparison across chart types | Verify alignment by timestamp, not by bar count or index |
| Chart-type generator determinism | Any generator output | Verify same input + parameters produces identical output |
| Division by zero | Any ratio computation | Check for denominator > 0 guard |
| Wrong sample size in CI | Bootstrap or statistical test calls | Verify the `n=` passed matches actual data size |

### Value Range Reference

Use these ranges for plausibility checks (from `_pipeline-config.md` and `dataset-reference.md`):

| Column | Source | Expected Range | Notes |
|--------|--------|---------------|-------|
| `Open`, `High`, `Low`, `Close` | Time bars, LB, Renko | Positive real (price domain) | OHLC prices, typical forex/commodity range |
| `HAOpen`, `HAHigh`, `HALow`, `HAClose` | Heiken Ashi | real-valued | Synthetic prices — never use for strategy P&L |
| `RealOpen`, `RealHigh`, `RealLow`, `RealClose` | Heiken Ashi | Positive real (price domain) | Actual prices, use for returns |
| `Direction` | All chart types | {+1, -1} | Up or Down, int32 |
| `Level` | Line Break | Positive int | Line Break level parameter (default: 3) |
| `BrickSize` | Renko | Positive real | ATR-derived brick size |
| `ATRPeriod` | Renko | Positive int | ATR period used (default: 14) |
| `TickVolume` | Time bars | ≥ 0 | Broker-reported tick volume, if available |
| `SourceCount` | Line Break, Renko, Heiken Ashi | ≥ 0 | Number of source 1-minute bars consumed since prior confirmed event |
| `SourceCloseTime` | LB, Renko | datetime | Time-matched real bar close timestamp |
| `CloseTime` / `OpenTime` | Time bars, LB, Renko | datetime | Bar open/close timestamps |
| `DurationSeconds` | Time bars | ≥ 0 | Bar duration in seconds |
| `SumAbsDelta` | Time bars | ≥ 0 | Sum of absolute price changes |

### Audit Proportionality Guide

| Experiment Complexity | Audit Depth |
|----------------------|-------------|
| Descriptive / EDA (0-1 tests, 2-4 plots) | Light: check holdout exclusion, synthetic price discipline, value ranges, scope compliance |
| Single hypothesis test (1-2 tests, 2-3 plots) | Standard: all dimensions, check timestamp alignment |
| Comparative across chart types (2-4 tests, 3-5 plots) | Thorough: all dimensions + cross-chart-type consistency and alignment |
| Multi-feature relationship (2-3 tests, 3-5 plots) | Thorough: all dimensions + interaction checks, synthetic price and alignment checks |
