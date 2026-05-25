# Pre-Execution Governance Review: EXP-015

**Reviewer:** Research Pipeline (Stage 4 Governance)
**Date:** 2026-05-25
**Artifacts reviewed:**
- `python/experiments/EXP-015/scope.md`
- `python/experiments/EXP-015/analysis-plan.md`
- `python/experiments/EXP-015/code/run_experiment.py`
- `python/src/ict_timebar.py` (modified: added `compute_price_precision_step`)

---

## Scope Review

| Check | Result |
|---|---|
| Hypothesis testable and falsifiable | PASS — "Failed breakouts show measurable opposite-direction behavior" is specific and falsifiable |
| Single question | PASS — Sweep-only event study; no full ICT model |
| Success criteria concrete | PASS — ≥3 instruments, CI excludes zero, event count thresholds defined |
| Data views explicit | PASS — 1-minute time bars only; no event charts |
| Holdout exclusion stated | PASS — Final 30% explicitly excluded |
| Real-price outcome rule stated | PASS — "All outcomes use real time-bar OHLC prices aligned by timestamp" |
| Complexity budget realistic | PASS — 3 tests / 5 plots / 2 modules |
| No scope creep | PASS — No macro, displacement, IFVG, or breaker logic |
| Prerequisite stated | PASS — EXP-014 reproducibility approval listed |

---

## Analysis Plan Review

| Check | Result |
|---|---|
| Step 1 method justified | PASS — ATR14 buffer, `price_precision_step` floor, single-bar definition documented |
| Step 2 method justified | PASS — MFE/MAE path-dependent tracking; close-to-close alternative documented and rejected |
| Step 3 method justified | PASS — Non-parametric bootstrap, stratified by instrument and segment |
| Assumptions listed | PASS — Ambiguous same-bar case excluded; price precision is proxy, not tick data |
| Visualization plan purposeful | PASS — 4 plots answer distinct sub-questions (counts, primary effect, MFE/MAE distributions, time diagnostics) |
| Interpretation guide predeclared | PASS — Support/Against/Inconclusive criteria pre-specified |
| Budget compliance | PASS — 2–3 tests / 4 plots / 2 modules, within scope budget |

---

## Code Review

### Organization and Side Effects

| Check | Result |
|---|---|
| Imports → path setup → constants → helpers → orchestration → `main()` | PASS |
| No directory creation at import time | PASS — `mkdir` calls are inside `run_experiment()` at lines 812–813 |
| No data loading at import time | PASS |
| No plotting at import time | PASS |

### Holdout Exclusion and Data Loading

| Check | Result |
|---|---|
| First 70% only loaded via `load_analysis_timebars` | PASS — Uses lazy Polars scan → sort by CloseTime → `slice(0, analysis_rows)` |
| No `.unique()` on loaders | PASS |
| No full-dataset collection before holdout split | PASS — `load_analysis_timebars` applies holdout cut before returning |
| Column projection used | PASS — `TIMEBAR_COLUMNS` selection in `load_analysis_timebars` |

### Look-Ahead Bias Prevention

| Check | Result |
|---|---|
| PDH/PDL use prior observed weekday | PASS — Inherited from EXP-014 `compute_liquidity_levels` definition |
| ATR14Prior shifted by 1 bar | PASS — `add_bar_diagnostics` uses `.shift(1)` |
| ONH/ONL restricted to bars at or after 09:30 NY | PASS — `ON_LEVEL_MIN_MINUTE = OVERNIGHT_END_MINUTE = 570`; applied in `_build_level_events` |
| Sweep detection uses bar's own High/Low/Close (known at CloseTime) | PASS |
| Event outcome measurement looks only forward from event CloseTime | PASS — `searchsorted(..., side="right")` excludes the event bar itself |

### Real-Price Outcome Discipline

| Check | Result |
|---|---|
| All MFE/MAE/1R computations use real time-bar High/Low | PASS |
| No HA prices or Renko brick prices | PASS — EXP-015 is time-bar-native |
| Outcome bars drawn from full analysis-set bars (not weekday-only) | PASS — `frame_pl.sort("CloseTime").to_pandas()` used for outcome arrays; weekday filter applied only for event detection |

### Statistical Correctness

| Check | Result |
|---|---|
| Bootstrap resamples events independently per (Instrument, Segment) | PASS — `_sweep_breach_arrays` filters by instrument and segment before resampling |
| Zero-risk guard prevents division by zero | PASS — `if risk <= 0: return nan_out` at line 351 |
| Ambiguous events excluded from hit-probability comparisons | PASS — `~events["Ambiguous60"].fillna(True)` filter in `_sweep_breach_arrays` |
| NaN propagation explicit | PASS — `fillna(0.0)` for ATR; `nan_out` returned for degenerate events |

### Code Quality

| Check | Result |
|---|---|
| Type hints on all public functions | PASS |
| Logging via `LOGGER`; `print()` only in `run_experiment()` summary | PASS |
| No magic numbers — buffer coeff, event-count thresholds, R-cap are named constants | PASS |
| Empty DataFrame guard before `pd.concat` in `detect_sweep_events` | PASS — `non_empty = [p for p in parts if not p.empty]` with early return |
| Plot inputs bounded | PASS — events table is a few-thousand rows max; R-multiples clipped at `PLOT_R_CAP=8.0` |
| No repeated heavy data loads for plots | PASS — `events` DataFrame reused for all 4 plots |

### Code Conventions Self-Check

| Convention | Status |
|---|---|
| Imports → path setup → constants → I/O helpers → computation → plotting → orchestration | ✓ |
| Output directories created in orchestration only | ✓ |
| Lazy Polars scan → timestamp sort → first-70% slice → collect | ✓ |
| No silent `.unique()` | ✓ |
| Plot inputs aggregated/clipped before pandas use | ✓ |
| No expensive data regenerated for plotting | ✓ |
| Zero-baseline metrics return NaN rather than ±∞ | ✓ |
| Duplicate-source denominator note | N/A — time bars only |
| HA synthetic returns | N/A — no HA in scope |

### Phase Alignment (Design.md)

EXP-015 is the H2 sweep-only event study per the Phase 003 roadmap. It:
- Uses 1-minute time bars, no event charts ✓
- Inherits PDH/PDL and ONH/ONL from EXP-014 (prerequisite satisfied) ✓
- Does not add macro, displacement, IFVG, or breaker logic ✓
- Does not pre-specify EXP-016 or later scope decisions ✓

---

## Information Notes (Non-Blocking)

**INFO-1 — Function length:** Several functions exceed ~30 lines due to multi-parameter docstrings (`_compute_horizon_outcomes` at 59 lines, `write_outputs` at 68 lines, `run_experiment` at 51 lines). EXP-013 set precedent for complex helper functions exceeding this guideline. Logic is correct; splitting further would not improve clarity for these cases.

**INFO-2 — INCONCLUSIVE threshold updated:** Following adversarial review, the verdict logic was updated from a raw row-count check (`n_count_pass < 6`) to an instrument-level test-segment check (`n_count_pass_test < 3`): INCONCLUSIVE when fewer than 3 instruments have adequate test-segment event counts. This is consistent with the new `InstrumentPass = test_pass` requirement.

**INFO-3 — Weekday filter for event detection vs. all bars for outcomes:** Event detection uses only weekday bars (consistent with PDH/PDL/ONH/ONL definitions). Outcome measurement uses all analysis-set bars, including any non-weekday bars in BTCUSD. This is the correct design: the forward price path for a Friday event should include any available overnight/weekend bars. Documented via the code comment at line ~839.

---

## Post-Adversarial-Review Code Amendments

An adversarial review (`docs/code-reviews/2026-05-25-051609-WAT-EXP-015-adversarial-review.md`) identified four issues after initial approval. All four were addressed before execution:

| Finding | Severity | Resolution |
|---|---|---|
| F01 — Sweep/Breach not mutually exclusive | Major | `_build_level_events` refactored: first touch per NYDate/LevelType classified as exactly one of Sweep or Breach |
| F02 — Missing post-execution artefacts | Major | Not applicable at pre-execution stage (expected post-execution) |
| F03 — Support verdict allowed train-only pass | Major | `InstrumentPass` changed to `test_pass`; INCONCLUSIVE threshold updated to instrument-level test-segment check |
| F04 — Secondary outcome artefacts missing | Major | `compute_secondary_effects` added; `secondary_effects.csv` written; `results.json` updated with secondary section and `support_verdict_rule` |
| F05 — Price precision proxy undocumented | Minor | `compute_price_precision_step` docstring updated to explicitly document close-to-close design choice; per-instrument steps written to `results.json` |

## Verdict

```
VERDICT: APPROVE
```

All scope, analysis plan, and code checks pass. Adversarial review findings resolved. The experiment is ready for manual execution.

---

## Execution Instructions

```
Pre-execution review: APPROVED

Experiment: EXP-015 — Prior High Low Sweep Reversal Behavior
Code:       python/experiments/EXP-015/code/run_experiment.py
Expected output: python/experiments/EXP-015/results/
                 python/experiments/EXP-015/plots/

Runs sweep and breach event detection across PDH/PDL/ONH/ONL levels for all 4
instruments, computes MFE/MAE and 1R/2R hit probabilities at 30/60/120-minute
horizons, then bootstrap-tests whether failed sweeps outperform non-failed
breaches on the primary 60-minute 1R-before-stop probability metric.

Please run the experiment code and confirm when complete.
```
