# Audit Report: Experiment EXP-030

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 1
- **Info Notes**: 2

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Sweep/breach classification, first-touch groupby, stop/entry/risk1R derivation, and verdict logic are all correct. |
| `code/run_experiment.py` | Edge cases | PASS | Empty instrument frames handled; NaN ATR filled with 0.0 before buffer; zero/negative risk1R guarded before outcome computation. |
| `code/run_experiment.py` | Type safety | PASS | Public functions have type hints and docstrings. |
| `code/run_experiment.py` | NaN handling | PASS | ATR NaN filled with 0.0 for buffer; `np.isfinite(risk)` guarded; NaN outcome dicts returned for invalid events. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `load_analysis_timebars` uses lazy scan → sort by CloseTime → slice first 70% before collect. 15-minute aggregation applied to analysis-set 1-minute slice only. |
| `code/run_experiment.py` | Loader ordering | PASS | 70/30 train/test on 15-minute series uses `int(aggregated.height * 0.70)` chronological row cutoff. 1-minute outcome frame also inherits same analysis-set only. |
| `code/run_experiment.py` | Memory/performance | PASS | Lazy Polars scan for 1-minute loading; 15-minute frame kept in Polars until pandas conversion; outcome rows accumulated per event then collected. |
| `code/run_experiment.py` | Logging/output | PASS | `LOGGER.info` for per-instrument diagnostics; `print` at top-level completion only. |
| `code/run_experiment.py` | Organization/import side effects | PASS | `plots_dir.mkdir()` and `results_dir.mkdir()` inside `run_experiment()` only. |
| `code/run_experiment.py` | Plot data reuse | PASS | All four plots use pre-computed tables and the already-collected events DataFrame; no re-loads. |
| `code/run_experiment.py` | Docstrings | PASS | All public functions have docstrings. |

## Numerical Validation

### Spot Checks

**Sweep classification — manual verify**

High (PDH/ONH) sweep: `High > level + buffer AND Close < level`. For a bearish sweep, price wick above the level and close back below it. Entry = Close, Stop = High + buffer (above the wick top), Risk1R = abs(Stop - Entry). This matches EXP-015 convention. ✓

Low (PDL/ONL) sweep: `Low < level - buffer AND Close > level`. Entry = Close, Stop = Low - buffer, Risk1R = abs(Stop - Entry). ✓

**First-touch policy — verified**

`candidates.sort_values("CloseTime").groupby("NYDate", sort=False).head(1)` takes the chronologically first event per NYDate. ✓

**EURUSD Test sweep-minus-breach difference cross-check**

From `bootstrap_primary.csv`: EURUSD Test point = −0.1454, CI = [−0.2554, −0.0360]. Negative difference means sweeps have lower 1R-before-stop probability than breaches at 60 minutes. Direction is strongly opposite to the EXP-015 EURUSD partial positive (+0.134). This is internally consistent with the INCONCLUSIVE verdict — the EURUSD positive does not replicate.

**Verdict derivation — spot check**

- `floors_failing = 0` (all 8 instrument-segment combinations meet the 100-event floor)
- `positive_new_instruments = []` (no new positives vs EXP-015)
- `eurusd_replicates = False` (EURUSD test is negative; `EURUSDReplicatesTighterOrStronger = False`)
- `all_ci_includes_zero`: EURUSD test CI [−0.2554, −0.0360] excludes zero; BTCUSD test CI [−0.2660, −0.0465] excludes zero → `all_ci_includes_zero = False`
- Falls through to `else: verdict = "INCONCLUSIVE"` ✓

**BTCUSD consistency**

Train and test both show negative point diff with CIs excluding zero (Train: −0.120 [−0.181, −0.056]; Test: −0.154 [−0.266, −0.047]). Consistent signal; sweeps underperform breaches on BTCUSD.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| SweepCount per segment | ≥ 100 (floor) | [126, 427] — all pass floor | YES |
| BreachCount | > 0 | [173, 543] | YES |
| Risk1R | > 0 for all feasible | all risk-feasible sweeps > 0 (feasible = total here) | YES |
| Hit1R values | {0, 1, NaN} | as expected from binary hit flag | YES |
| Primary PointDiff | ℝ | [−0.154, +0.046] | YES |
| EXP-015 reference loaded | columns required | all required columns present | YES |

### Statistical Sanity

| Statistic | Value | Makes sense? | Notes |
|-----------|-------|-------------|-------|
| EURUSD Train CI [−0.195, −0.054] | Narrow (0.14pp) vs Test [−0.255, −0.036] (wider, 0.22pp) | YES | Larger train N (327/456) vs test (126/195) drives tighter CI. |
| XAUUSD Test CI [−0.101, 0.122] (includes zero) | 152/173 events | YES | Smaller and more balanced counts, zero-including CI expected. |
| BTCUSD: both train and test CIs exclude zero negatively | Consistent sign | YES | Clearest signal in the experiment. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Outcome evaluation | Starts strictly after confirming 15m candle close | YES | `np.searchsorted(close_ns, event_ns, side="right")` skips bars ≤ event CloseTime |
| ATR | No look-ahead | YES | `rolling_mean(14).shift(1)` — only prior bars |
| First-touch policy | Preserved from EXP-015 framework | YES | `groupby("NYDate").head(1)` after `sort_values("CloseTime")` |
| ONH/ONL timing gate | Only bars at or after session open | YES | `NYMinuteOfDay >= ON_LEVEL_MIN_MINUTE` filter applied |
| Stratified bootstrap | Preserves side/level-type mix | YES | Strata defined by `LevelType + "/" + Side` |

## Results Plausibility

All 4 instruments pass the 100-event floor with comfortable margins (126–427 sweep test events). This is a genuine sampling, not a count collapse.

The EURUSD result (sweeps −0.145 vs EXP-015 +0.134) is the most striking finding: the EXP-015 partial positive disappears and reverses at 15-minute resolution. At 15-minute bars, EURUSD sweeps show distinctly negative outcomes vs breaches. This is internally consistent: 15-minute sweep candles aggregate multiple 1-minute bars, so the confirming bar already contains much of the post-sweep price action, leaving less favorable follow-through in the 60-minute outcome window.

BTCUSD shows a consistent negative pattern (both train and test CI exclude zero negatively). XAUUSD and USTEC results are centered near zero with CIs including zero.

INCONCLUSIVE verdict is correctly derived: floors pass everywhere, but no instrument produces a positive new finding and the EURUSD partial positive does not replicate.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 3 statistical tests (primary, secondary, horizon) / 3 budgeted; 4 visualisations / 4; 0 new modules (bar_aggregator.py reused from EXP-029) / 1 max
- Holdout exclusion verified: YES

## Issues

### Critical

None.

### Warning

1. **EURUSD partial positive from EXP-015 reverses direction at 15-minute resolution — ensure this is correctly surfaced in interpretation**
   - File: `results/exp015_reference_comparison.csv`
   - Description: EXP-015 EURUSD Test showed +0.134 [0.001, 0.267] supporting the sweep-reversal hypothesis. EXP-030 EURUSD Test shows −0.145 [−0.255, −0.036], directionally reversed. This is not a code error but a strong finding that must be explicitly stated in results.md and the reflection: the 15-minute resolution does not merely fail to replicate the EXP-015 EURUSD positive — it actively contradicts it.
   - Impact: If this reversal is missed during interpretation, the reflection may understate the evidence against the sweep-at-15-minute thesis.
   - Fix: No code change needed. Flag explicitly in interpretation.

### Info

1. **ATR NaN fills with 0.0 for early bars — buffer falls back to precision_step**
   - Description: Same as EXP-029: first 14 15-minute bars have NaN ATR14Prior, so buffer = precision_step. This affects a small number of early events and is the correct fallback.

2. **Stratified bootstrap strata may be singleton for some instrument/segment combinations**
   - Description: For instruments with only one level type or one side represented in a given segment, the stratum has a single group. The bootstrap still runs correctly — `rng.choice(idx, size=idx.size, replace=True)` works for size-1 arrays. No bias is introduced.
