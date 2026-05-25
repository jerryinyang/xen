# Pre-Execution Review: EXP-016 — Macro Window Interaction With Sweep Outcomes

**Reviewer:** Research Pipeline (Stage 4 Governance)
**Date:** 2026-05-25
**Artifacts reviewed:** scope.md, analysis-plan.md, code/run_experiment.py

---

## 1. Scope Document

| Check | Result | Notes |
|-------|--------|-------|
| Single falsifiable question | PASS | "Are sweep outcomes materially different inside macro windows versus outside?" — one question, one comparison |
| Hypothesis testable | PASS | Interaction between H1 and H2 framed as effect-size comparison with pre-specified thresholds |
| Success criteria concrete | PASS | ≥5pp Hit1R improvement OR ≥0.25R MAE reduction on ≥3 instruments with ≥50 inside events per segment |
| Failure criteria concrete | PASS | No improvement or only sample reduction = AGAINST |
| Inconclusive criterion | PASS | Inside counts below event floor = INCONCLUSIVE |
| Data views defined | PASS | 1-minute time bars only; no LB/Renko/HA (phase non-inheritance respected) |
| Instruments stated | PASS | EURUSD, XAUUSD, BTCUSD, USTEC |
| Time range and split | PASS | First 70% = analysis set; final 30% = global holdout, never loaded |
| Look-ahead rule stated | PASS | "Features and events use only bars with CloseTime at or before the event timestamp" |
| Real-price discipline | PASS | "All outcomes use real time-bar OHLC prices aligned by timestamp" |
| Exclusions stated | PASS | No full ICT model, no parameter tuning, no event-chart features |
| Complexity budget | PASS | 2 stat tests, 4 visualisations, 1 new module — realistic and sufficient |
| Phase alignment | PASS | EXP-016 is EXP-016 (H2 context) in the Phase 003 roadmap; macro×sweep interaction explicitly planned |

**Scope verdict: PASS** — No issues.

---

## 2. Analysis Plan

| Check | Result | Notes |
|-------|--------|-------|
| Method justification | PASS | Each step includes "Why this method" and "Simpler alternative considered" |
| No normality assumption | PASS | Non-parametric bootstrap throughout |
| No look-ahead | PASS | Macro membership assigned from event bar's own CloseTime; forward outcomes use only post-event bars |
| Matching approach justified | PASS | Date-level matching documented; unmatched outside events go to sensitivity summary |
| Interpretation pre-defined | PASS | FOR/AGAINST/INCONCLUSIVE mapped to specific quantitative thresholds before results |
| Cross-view alignment | PASS | Join by CloseTime in NY time; no bar-index alignment |
| Visualisations purposeful | PASS | Each of 4 plots answers a distinct sub-question (counts, effect intervals, MAE shape, window distribution) |
| Budget compliance | PASS | 2 tests / 2 max; 3–4 plots / 4 max; 1 module / 1 max |

**Analysis plan verdict: PASS** — No issues.

---

## 3. Code Review

### Organization

| Check | Result | Notes |
|-------|--------|-------|
| Import → path setup → constants → I/O → computation → plotting → orchestration → main | PASS | Sections clearly delineated with comment headers |
| No import-time side effects | PASS | No directory creation, file writes, data loads, or plotting outside functions |
| Directories created only in orchestration | PASS | `plots_dir.mkdir` / `results_dir.mkdir` called only inside `run_experiment()` |

### Holdout and Data Loading

| Check | Result | Notes |
|-------|--------|-------|
| Holdout excluded | PASS | `load_analysis_timebars` slices to first 70% chronologically; no code path references the remainder |
| Lazy scan used | PASS | `pl.scan_parquet` inside `load_analysis_timebars`; column projection applied |
| Chronological sort before split | PASS | `.sort("CloseTime").slice(0, analysis_rows)` in `ict_timebar.load_analysis_timebars` |
| Train/test split inside analysis set | PASS | `train_cutoff_time` derived from first 70% of analysis rows; `Segment` column assigned via `add_ny_time_features` |

### Look-Ahead Bias

| Check | Result | Notes |
|-------|--------|-------|
| Forward outcomes use post-event bars only | PASS | `start_idx = searchsorted(ct_ns, event_ns, side="right")` correctly excludes the event bar itself |
| Macro window assignment uses event bar's own CloseTime | PASS | `MacroWindow` column carried from the merged bar (the event bar), not from a future bar |
| ONH/ONL restricted to NY minute ≥ 570 | PASS | `ON_LEVEL_MIN_MINUTE = OVERNIGHT_END_MINUTE = 570` applied in `_build_level_events` |
| PDH/PDL computed from prior observed weekday | PASS | Inherited from `ict_timebar.compute_liquidity_levels` (EXP-015 approved definition) |

### Real-Price Discipline

| Check | Result | Notes |
|-------|--------|-------|
| Outcomes from time-bar High/Low/Close | PASS | `ct_ns`, `highs`, `lows` from `frame_sorted` (time-bar frame); no synthetic prices involved |
| No HA or Renko prices | PASS | Chart-type generators not called; scope explicitly excludes them |

### Statistical Methods

| Check | Result | Notes |
|-------|--------|-------|
| Non-parametric bootstrap | PASS | `_bootstrap_metric_diff` uses `rng.choice` with replacement; no distributional assumptions |
| Seed fixed | PASS | `BOOTSTRAP_SEED = 42`; `np.random.default_rng(BOOTSTRAP_SEED)` in orchestration |
| Ambiguous events excluded from Hit1R | PASS | `~df["Ambiguous60"].fillna(True).astype(bool)` in `_filter_hit_vals` |
| MAE improvement sign convention documented | PASS | Comment in code and in JSON output: positive = inside has less adverse excursion |
| MAE CI correctly inverted | PASS | `mae_ci_lo = -mae["CI95High"]`; `mae_ci_hi = -mae["CI95Low"]` — correct sign flip |
| Event floor applied per segment | PASS | `InsideSweepN >= MIN_INSIDE_EVENTS` and `MatchedOutsideN >= MIN_MATCHED_OUTSIDE_EVENTS` per (Instrument, Segment) |
| Verdict enforces train/test floors | PASS | `evaluate_verdict()` requires both train and test event/comparator floors before an instrument can satisfy the support criterion |

### Code Quality

| Check | Result | Notes |
|-------|--------|-------|
| Type hints on all public functions | PASS | All functions have typed parameters and return types |
| Docstrings with Parameters and Returns | PASS | All functions documented |
| NaN handling explicit | PASS | `.fillna()` for ATR14Prior, Ambiguous60; `.notna()` guards before bootstrap; `risk <= 0` guard |
| Edge cases handled | PASS | Empty DataFrame guards in detection; `h_highs.size == 0` guard; min count check before bootstrap |
| Function length | PASS | Longest pure-computation functions (~30 lines); `write_outputs` is an output-sink function, acceptable |
| Helper functions return data | PASS | No printing in helpers; only `run_experiment()` calls `print()` |
| Log output concise | PASS | Four LOGGER.info/warning calls per instrument in orchestration only |

### Plot and Memory

| Check | Result | Notes |
|-------|--------|-------|
| No heavy re-load for plotting | PASS | `count_data`, `mae_data`, `heatmap_data` derived from `all_events` in orchestration; passed directly to plot functions |
| Bounded plot inputs | PASS | `mae_data[MAE_COL].clip(upper=PLOT_R_CAP)` applied before plotting; count/heatmap aggregations are small |
| Full-data arrays not converted to pandas for plotting | PASS | Only aggregated DataFrames passed to seaborn; raw `highs`/`lows` numpy arrays not exposed to plot layer |

### Plan Compliance

| Analysis plan step | Code implementation | Result |
|---|---|---|
| Step 1: Join sweep events to macro labels by CloseTime NY time | `MacroWindow` carried from merged weekday bars in `_build_level_events`; `InMacro = MacroWindow.notna()` in `detect_sweep_events` | PASS |
| Step 2: Matched outside-window baseline by instrument, side, segment, NY date | `build_matched_outside` inner-joins outside sweeps to inside event keys | PASS |
| Step 3: Bootstrap Hit1R_60m and MAE_R_60m difference | `_bootstrap_metric_diff` with `use_median=False` for Hit1R and `True` for MAE; called in `_instrument_segment_effects` | PASS |
| Visualisation 1: Inside vs outside counts | `plot_inside_outside_counts` — grouped bar chart by Instrument, Segment, InMacro | PASS |
| Visualisation 2: Effect-size interval plot | `plot_effect_intervals` — forest plot of HitDiff with 95% CI and threshold line | PASS |
| Visualisation 3: MAE distribution by macro membership | `plot_mae_distributions` — boxplot of clipped MAE_R_60m | PASS |
| Visualisation 4: Per-window count heatmap | `plot_window_heatmap` — heatmap of inside sweep counts by MacroWindow × Instrument | PASS |

---

## 4. Governance Constraints Summary

| Constraint | Status |
|-----------|--------|
| Simplest sufficient approach | PASS — matched bootstrap is the minimum viable test for the interaction; no model complexity added |
| No academic-finance pitfalls | PASS — bootstrap only; no normality, stationarity, or i.i.d. assumptions |
| Single hypothesis per experiment | PASS — one interaction question; primary and secondary metrics both predeclared |
| OOS holdout untouched | PASS — `load_analysis_timebars` enforces 70% ceiling; no code path reaches holdout |
| Look-ahead bias prevented | PASS — event bar carries its own contemporaneous MacroWindow; forward outcomes use strict post-event slice |
| Real-price discipline | PASS — no synthetic chart prices; all outcomes from time-bar OHLC |
| Timestamp alignment | PASS — CloseTime used for all joins and temporal ordering |
| Complexity budget | PASS — 2 tests, 4 plots, 0 new modules (within budget of 1) |
| Phase 003 alignment | PASS — tests H2 context as planned in design.md roadmap |

---

## Verdict

```text
VERDICT: APPROVE
```

All scope, plan, and code checks pass. No Critical or Warning issues. The implementation faithfully reproduces the EXP-015 sweep definition, applies EXP-012 macro-window labels from the approved `ict_timebar` module, constructs a date-matched outside baseline, and bootstraps the interaction effect within the predeclared complexity budget. The holdout exclusion, look-ahead prevention, and real-price discipline are all correctly enforced.
