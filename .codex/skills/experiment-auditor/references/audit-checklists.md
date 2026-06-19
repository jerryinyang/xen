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
| <file> | Loader ordering | PASS/FAIL | Lazy scan sorts by timestamp before slicing first 70%; no full holdout collection. |
| <file> | Memory/performance | PASS/FAIL | Large inputs stay lazy/column-pruned; plotting samples or aggregates before pandas conversion. |
| <file> | Safe optimization | PASS/FAIL | Vectorization/performance changes preserve sample membership, temporal causality, denominators, and interpretation. |
| <file> | Progress tracking | PASS/FAIL | Long-running loops use `tqdm` or equivalent progress without noisy per-row output. |
| <file> | Logging/output | PASS/FAIL | Manual-run output is concise and failures are traceable. |
| <file> | Organization/import side effects | PASS/FAIL | Imports/path/constants/helpers/orchestration follow sample structure; no output directories are created at import time. |
| <file> | Plot data reuse | PASS/FAIL | Heavy data loads and chart generation are not repeated solely for visualisations. |
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
| Event timestamps | Monotonically increasing where required | [<first>, <last>] | YES/NO |

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

## Verdict Forensics (mandatory — run autonomously on every verdict)

### Per-stratum re-derivation & masking check

| Stratum (domain/instrument/cell) | Per-stratum verdict | Agrees with pooled headline? | Notes |
|----------------------------------|---------------------|------------------------------|-------|
| <stratum> | <verdict> | YES/NO | <if NO, what the pooled number is masking> |

- Pooled/aggregated headline: <value>. **Is it masking heterogeneity?** YES/NO — <evidence>. (A pooled number is a disclosure, not a verdict, until cross-stratum homogeneity is shown.)

### Mechanism

<Why did the verdict come out this way? Name the binding leg, the driving cells, the tail/feature. Not "the number missed the bar" — *what produced* the number.>

### Gate-shape check

- Binding gate: <gate>. Effect shape: <location / tail / bimodal / asymmetric>.
- Is the gate the wrong instrument for this effect's shape? YES/NO — <if YES, distinguish "no effect" from "effect of a shape this gate cannot see"; record for the interpreter; do NOT retro-edit the gate>.

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

## Materiality & Re-Audit Requirements

- **Materiality of each finding**: for every Critical, state the verdict-bearing number it could move (blocking → fix + rerun before Stage 6). For every Warning/Info, state the explicit reasoning that it **cannot** move any verdict-bearing number (the only justification for document-and-proceed).
- **Re-audit**: <If a blocking finding exists, what must be fixed, re-run, and how to verify the fix. If no rerun is required, the materiality reasoning above is the justification.>
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
| Full-data collection before holdout split | Any `read_parquet()` or `.collect()` before `.slice()` / `.head()` | Verify the code does not materialize or inspect final 30% rows |
| Physical-row cutoff before chronological sort | Any `.head()` / `.slice()` before `.sort("CloseTime")` | Sort by `CloseTime` or `SourceCloseTime` before taking the first 70% |
| Import-time side effects | Module-level `mkdir()`, file writes, plotting setup with filesystem effects | Move effects into `main()` or orchestration |
| Repeated heavy analysis pass | Loading/generating the same large data again for plots | Return bounded plot inputs from the analysis pass |
| Unbounded pandas conversion | `.to_pandas()` on full analysis/event sets | Aggregate or deterministically sample first |
| Unbounded Python row loop | `iter_rows()`, row-wise `for`, or per-row Python callbacks on large frames | Use Polars/NumPy/vectorized logic when it is causally equivalent |
| Unsafe vectorized shortcut | Batch vectorization of sequential or streaming logic | Verify each row uses only information available at or before its timestamp |
| Missing long-run progress | Multi-file, multi-instrument, parameter-grid, or repeated validation loops | Wrap expensive outer loops in `tqdm` and keep helper functions quiet |
| Silent deduplication drift | Any `.unique()` in loaders | Require a scope reason and pre/post row-count reporting |
| Zero-baseline percentage improvement | Any `(baseline - value) / baseline` | When baseline is zero, emit absolute difference or mark the relative metric undefined |
| String/numeric confusion | `Direction` column comparisons | Verify `Direction` is `+1/-1` (int), not string |
| Look-ahead bias | Temporal ordering code | Verify `CloseTime`, event timestamp, or `SourceCloseTime` used for sorting/alignment, never bar index |
| Synthetic price returns | Any return computation on HA or Renko-derived signals | Verify strategy/P&L/signal returns use real time-matched prices, never `HAClose` or Renko brick prices. `HAClose` returns are allowed only for explicit HA distortion diagnostics labelled non-tradable. |
| Cross-view alignment | Any comparison across event sets or data views | Verify alignment by timestamp, not by bar count or index |
| Derived-view determinism | Any generator or feature-builder output | Verify same input + parameters produces identical output, or fixed seed if randomness is scoped |
| Division by zero | Any ratio computation | Check for denominator > 0 guard |
| Wrong sample size in CI | Bootstrap or statistical test calls | Verify the `n=` passed matches actual data size |
| Duplicate-event denominator bias | Event streams with repeated timestamps | Verify duplicate rows are excluded, merged, or explicitly counted by design |
| Pooled verdict masks per-stratum structure | Any aggregated/equal-weight headline (pooled NO_SEPARATOR, cross-cell mean, portfolio composite) | Re-derive per domain/instrument/cell; confirm the pooled number is not hiding a stratum that flips the verdict or one outlier vetoing the rest |
| Gate blind to the effect's shape | Any binding gate applied to a tail/bimodal/asymmetric effect | Check the gate measures the shape present (e.g. a location/consistency gate cannot see a tail-only separator); distinguish "no effect" from "wrong instrument" |
| Verdict-material finding down-classified | Any Warning/Info on a result-bearing path | Confirm the finding genuinely cannot move sample membership, a denominator, a metric, causality, or the verdict; if it can, it is Critical and forces a rerun |

### Value Range Reference

Use these ranges for plausibility checks (from `_pipeline-config.md` and `dataset-reference.md`):

| Column | Source | Expected Range | Notes |
|--------|--------|---------------|-------|
| `Open`, `High`, `Low`, `Close` | Time bars, LB, Renko | Positive real (price domain) | OHLC prices, typical forex/commodity range |
| `HAOpen`, `HAHigh`, `HALow`, `HAClose` | Heiken Ashi | real-valued | Synthetic prices — never use for strategy P&L |
| `RealOpen`, `RealHigh`, `RealLow`, `RealClose` | Heiken Ashi | Positive real (price domain) | Actual prices, use for returns |
| `Direction` | Directional features/events | {+1, -1} | Up or Down, int32 when present |
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
| Descriptive / EDA (0-1 tests, 2-4 plots) | Light: check holdout exclusion, real-price outcome discipline, value ranges, scope compliance |
| Single hypothesis test (1-2 tests, 2-3 plots) | Standard: all dimensions, check timestamp alignment |
| Comparative across data views (2-4 tests, 3-5 plots) | Thorough: all dimensions + cross-view consistency and alignment |
| Multi-feature relationship (2-3 tests, 3-5 plots) | Thorough: all dimensions + interaction checks, real-price outcome and alignment checks |
