# Adversarial Review — EXP-013 and EXP-014

**Date:** 2026-05-24 01:33:37
**Reviewer lens:** Empirical study (primary) + Algorithm / implementation correctness (secondary)
**Artefacts reviewed:**
- `python/experiments/EXP-013/{scope.md, analysis-plan.md, code/run_experiment.py, governance/pre-execution-review.md, results/*}`
- `python/experiments/EXP-014/{scope.md, analysis-plan.md, code/run_experiment.py, governance/pre-execution-review.md, results/*}`
- `python/src/ict_timebar.py` (shared module)
- Phase-003 design checkpoint and EXP-012 outputs (context only)

```json
[
  {
    "id": "F01",
    "severity": "Critical",
    "title": "PM-cluster adjacent controls overlap other macro windows, contaminating the AdjacentMean comparator",
    "evidence": "`ict_timebar.py` MACRO_WINDOW_SPECS: PM2=890–910, PM3=915–945 (30 min), PM4=950–970. In `run_experiment.py:build_window_observations`, AdjacentBefore = [start − duration, start), AdjacentAfter = [end, end + duration). For PM3 (duration=30): AdjacentBefore=885–915 overlaps PM2 (890–910) entirely; AdjacentAfter=945–975 overlaps PM4 (950–970). For PM4 (duration=20): AdjacentBefore=930–950 overlaps PM3 (915–945). No filter excludes other macro windows from adjacent neighbours.",
    "impact": "The AdjacentMean comparator for PM2/PM3/PM4 includes bars belonging to another macro window. Because macro windows tend to be high-range, the adjacent control is inflated by the very thing the test is supposed to measure against, biasing macro−adjacent toward zero or negative. This is consistent with the strongly negative USTEC and BTCUSD `Diff_AdjacentMean` and is a direct, mechanical confound in the primary test, not a finding about macro-window behaviour.",
    "fix": "Either (a) skip adjacent windows that overlap any other macro spec on the same date, (b) shift adjacents farther out (e.g., 2× duration, with documented overlap rule), or (c) restrict the AdjacentMean test to the AM cluster where neighbours are clean and report the PM cluster separately. Re-run primary effects after the change."
  },
  {
    "id": "F02",
    "severity": "Critical",
    "title": "Random controls draw from the full 24-hour NY day, conflating session structure with macro-window effect",
    "evidence": "`run_experiment.py:random_control_starts` sets `max_start = 24 * 60 - duration` and only excludes overlap with MACRO_WINDOW_SPECS. There is no constraint to active US session hours, premarket, or any other session-comparable window. Sample rows in `results/window_observations.csv` confirm this: e.g., EURUSD 2023-01-02 AM1 RandomMean start=790.34 (~13:10 NY) but other draws clearly land overnight given the 0–1440 candidate range. RandomMean `ObservedBars` is regularly < expected (e.g., 18.48 / 20), implying many draws hit periods with sparse bars (overnight/illiquid).",
    "impact": "The scope’s stated reason for using same-day random controls was to avoid the time-of-day confound that plain non-macro comparison would create. As implemented, the random comparator is dominated by off-session time-of-day, so the macro−random difference is largely a session-vs-non-session contrast, not a macro-window contrast. The pre-spec assumption that random controls are 'exchangeable within instrument/date/segment' is violated. All 8 `RandomMean` rows in `primary_effects.csv` show large negative diffs that are dominated by this confound rather than by macro-window structure.",
    "fix": "Restrict random control draws to a session-matched window (e.g., 07:00–17:00 NY) or to the union of AM and PM macro families, while still excluding macro-window minutes. Document the rule before re-running; do not tune the band against outcomes. Alternatively, replace RandomMean with a same-session random-control family and treat the full-day random sample as a separate diagnostic only."
  },
  {
    "id": "F03",
    "severity": "Major",
    "title": "Averaging 100 random controls into one row per (date, window) before bootstrap understates uncertainty",
    "evidence": "`build_window_observations` collapses 100 random draws to a single `RandomMean` row via `average_metric_rows`. `primary_effects` then bootstraps the per-pair diff series `Macro − RandomMean`. Bootstrap units are date×window pairs whose `RandomMean` is itself a mean of 100 partly correlated within-day samples.",
    "impact": "Averaging shrinks the per-pair noise of the control side, narrowing the macro−random difference distribution and producing CIs that look tighter than they should. Combined with F02, the negative-and-significant verdict for the RandomMean family is partly an artefact of variance compression in the comparator. Effect sign/size remain interpretable, but reported CI widths and any 'support / no-support' threshold derived from them are not trustworthy.",
    "fix": "Either (a) bootstrap over the raw random-draw pool with proper hierarchical resampling (resample dates, then resample draws within date), or (b) keep one representative random draw per date×window and bootstrap the resulting paired diff. Report PairedObservations consistent with the chosen resampling unit."
  },
  {
    "id": "F04",
    "severity": "Major",
    "title": "Hardcoded `SOURCE_TIMEZONE_ASSUMPTION = 'UTC'` is unverified; if wrong it invalidates every NY-time conclusion",
    "evidence": "`ict_timebar.py:26`. EXP-012 report explicitly notes: 'The UTC-to-New-York timestamp assumption is documented but not independently verifiable from repository metadata alone.' cTrader/cAlgo session output is commonly server-local (EET/EEST), not UTC, and the filename convention `<serverTime>_<localTime>` does not by itself constrain CloseTime to UTC.",
    "impact": "If CloseTime is actually EET (UTC+2/+3), every macro-window minute defined in NY time is shifted by 7 hours, so AM1 (07:50–08:10 NY) actually samples 00:50–01:10 NY in real terms. All downstream H1/H2/H3 macro-window conclusions, plus PDH/PDL/ONH/ONL boundary computations, become meaningless. The risk is binary: either the assumption is right and the work is fine, or it is wrong and the entire ICT phase is unsound.",
    "fix": "Add a one-off verification step that compares known high-liquidity NY events (e.g., 08:30 NY data releases) or the daily volume profile against expected NY-time peaks for one instrument with a known schedule (USTEC is best). If verification fails, refit `SOURCE_TIMEZONE_ASSUMPTION` and rerun EXP-012/013/014. Either way, the verification artefact should live next to the constant."
  },
  {
    "id": "F05",
    "severity": "Major",
    "title": "Weekday-only filter is applied uniformly, including BTCUSD; PDH for Monday uses Friday and silently drops weekend price action",
    "evidence": "`ict_timebar.py:weekday_filter` filters to weekday 1–5 for all instruments. `compute_liquidity_levels` shifts `DayHigh/DayLow` by one row inside `Instrument` after the weekday filter, so for BTCUSD Monday, PDH is Friday's high, ignoring Saturday and Sunday entirely. EXP-014 declares this instrument SUPPORTED with 99–100% all-level availability without flagging the BTC weekend gap.",
    "impact": "BTC is 24/7; the weekend often contains the week's most extreme moves. Treating Friday as the 'previous day' for Monday silently destroys liquidity-level fidelity exactly where ICT-style sweeps would care most. EXP-015 and any subsequent BTC sweep study built on EXP-014 will measure sweeps against a level that may have been broken twice over the weekend without being recorded as PDH. EXP-014's SUPPORTED verdict is overstated for BTCUSD.",
    "fix": "Either (a) define PDH/PDL using calendar-day previous date and apply the weekday filter only to event-eligible dates, (b) define a separate weekend-inclusive level for BTCUSD, or (c) explicitly down-scope EXP-014 to declare BTCUSD INCONCLUSIVE rather than SUPPORTED until a 24/7 convention is chosen. Whichever path, document the choice in EXP-014's scope before unblocking EXP-015/016."
  },
  {
    "id": "F06",
    "severity": "Major",
    "title": "Determinism check in EXP-014 cannot detect non-determinism",
    "evidence": "`run_experiment.py:run_experiment` calls `compute_liquidity_levels(ny_frame)` twice on the same in-memory frame in the same process, then asserts `levels.equals(rerun_levels)`. The function contains no RNG and no IO between calls. The check therefore passes by construction.",
    "impact": "EXP-014 claims `DeterministicRerunEqual=True` as part of its SUPPORTED verdict, but the test does not actually verify reproducibility across reloads, file ordering, or platform differences. A real non-determinism (e.g., dict ordering, dtype drift from cross-file Parquet concat, timezone library version) would not be caught here.",
    "fix": "Reload the levels from `liquidity_levels.csv` (or rerun the loader from scratch with a different file-glob order) and compare against the in-memory result. Optionally, also compare against a stored hash of the prior run's CSV."
  },
  {
    "id": "F07",
    "severity": "Major",
    "title": "Sweep diagnostic uses a single-bar Close < level rule that loses most legitimate sweeps",
    "evidence": "`run_experiment.py:level_sweep_occurred_fast` flags a high sweep only if some bar in the window satisfies `High > level` AND `Close < level` on the same bar. The scope text in EXP-013 matches this exactly. Nothing requires the close-back-below to occur within the window if the wick happens early in the window.",
    "impact": "An ICT 'sweep' is a wick beyond the level followed by reclaim by window/session close. The implemented rule needs a single 1-minute bar that both pierces and reclaims — a much narrower event than the conceptual sweep, and one that is dominated by 1-minute candle morphology, not window-level behaviour. Even though the scope correctly marks the metric as descriptive, the result will be near-zero for many windows (consistent with the sample CSV showing SweepOccurred=0 for nearly every row) and will not be a useful input to EXP-015/016 if those reuse the same definition. The current ‘descriptive only’ caveat may be carried forward as if it were a validated sweep operator.",
    "fix": "Either (a) define the sweep at the window level — `max(High) > level` AND `last Close < level` within the window — or (b) explicitly flag the current rule as a 'single-bar reclaim' diagnostic distinct from the H2 sweep definition that EXP-015 will need. Update EXP-014/EXP-015 scopes to specify which operator is being inherited."
  },
  {
    "id": "F08",
    "severity": "Minor",
    "title": "Per-call fixed bootstrap seed makes every CI estimate use identical RNG state",
    "evidence": "`run_experiment.py:bootstrap_ci` calls `np.random.default_rng(BOOTSTRAP_SEED)` on every invocation, so every comparison's resample indices share the same RNG pattern.",
    "impact": "Not a correctness bug — CIs are still valid bootstrap quantiles — but Monte-Carlo error is perfectly correlated across estimators, so cross-instrument 'agreement' in CI bounds is partly an RNG artefact and not extra evidence. Any future per-instrument power comparison will be misleading.",
    "fix": "Seed once outside the function (or pass a `numpy.random.Generator` in), or vary the seed per (instrument, segment, control) tuple with a documented derivation rule."
  },
  {
    "id": "F09",
    "severity": "Minor",
    "title": "ATR normalization uses the first valid ATR in the window, not the ATR known at window start",
    "evidence": "`summarize_window_metrics_fast`: `atr_values = arrays['atr14_prior'][window_slice]; valid_atr = atr_values[np.isfinite(atr_values)]; ... metrics['TrueRangeNormATR14'] = (high - low) / float(valid_atr[0])`. If the first bars in the window have NaN ATR14Prior (warm-up gap), the divisor is the ATR at a later bar inside the window. For coverage-reduced windows this differs from the pre-window ATR.",
    "impact": "Causes a small look-ahead within the window when early bars are missing. Effect size is usually negligible at minute resolution but is not strictly 'ATR known before the window' as documented in `results.json:macro_boundary_note` and the analysis plan.",
    "fix": "Compute ATR14 from `(start_idx − 1)` (last bar before window) and fall back to NaN if not available, rather than scanning into the window."
  },
  {
    "id": "F10",
    "severity": "Minor",
    "title": "Pivot-based `primary_effects` will silently drop or aggregate duplicate (date, window) rows without warning",
    "evidence": "`primary_effects` uses `pivot_table(..., aggfunc='first')` on (`Instrument`, `Segment`, `NYDate`, `Window`). The Segment label is derived from a single-`Segment` check per `NYDate` and falls back to `'Boundary'`; rows scoped only to `['Train', 'Test']`. If a date appears in both segments via a bug in `add_ny_time_features` (e.g., `train_end_time` exactly equal to a `CloseTime` shared by neighbours), duplicates would be silently aggregated.",
    "impact": "Low likelihood given current logic, but the failure mode is silent — a downstream regression would not surface. The complexity-budget claim that the test is non-parametric and assumption-light still depends on this invariant.",
    "fix": "Add an assertion (or warning) before the pivot that the (Instrument, Segment, NYDate, Window, ControlType) tuple is unique."
  }
]
```

## Summary

The most serious issues are structural in the primary comparator: PM-cluster adjacent windows overlap neighbouring macro windows (F01), and the random controls are drawn across the full 24-hour NY day rather than from a session-matched band (F02). Together these mean the strongly-negative `Macro − AdjacentMean` and `Macro − RandomMean` results in `primary_effects.csv` are at least partly driven by control contamination and session structure, not by macro-window behaviour. The pre-execution verdict of REFUTED is therefore probably right in direction but not for the stated reasons. The hardcoded UTC source-timezone assumption (F04) and the BTCUSD weekend treatment in EXP-014 (F05) are upstream risks that, if wrong, cascade through every Phase-003 experiment that inherits the shared module. F06 (vacuous determinism check) and F07 (narrow sweep operator) matter because EXP-014's SUPPORTED verdict and the sweep definition are about to be load-bearing for EXP-015/016. The remaining findings are easy to address but should be cleaned up before the H2 chain starts.
