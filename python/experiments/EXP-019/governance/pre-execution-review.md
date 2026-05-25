# Pre-Execution Review: EXP-019 — Micro Swing Break Confirmation After Sweep

**Reviewer:** Research Pipeline (Stage 4 Governance)
**Date:** 2026-05-25 (post-adversarial revision)
**Supersedes:** 2026-05-25 initial APPROVE (which did not catch F01/F02/F04/F05/F10 from `docs/code-reviews/2026-05-25-145710-WAT-EXP-017-EXP-020-adversarial-review.md`)
**Artifacts reviewed:**
- `python/experiments/EXP-019/scope.md`
- `python/experiments/EXP-019/analysis-plan.md` (revised)
- `python/experiments/EXP-019/code/run_experiment.py` (revised)
- `python/src/ict_timebar.py`
- `docs/experiments-docs/checkpoints/2026-05-23-003-ict-one-setup-timebar-validation/design.md`

## Background — what the adversarial review caught

| Finding | Issue | Resolution in revised code |
|---|---|---|
| F01 (Critical) | `*CriterionMet` used point estimates only. The initial FOR verdict held even when CI95 spanned zero on all four instruments. | Criteria now require `CI95Low >= threshold` (run_experiment.py:443-462). Refutation requires `CI95High < threshold`. Point estimates alone are insufficient. |
| F02 (Critical) | Scope/plan demanded *median* MAE; code computed *mean* via `paired_bootstrap_diff`. | `paired_bootstrap_diff` is now parameterised on `use_median`; the MAE call passes `use_median=True` (run_experiment.py:415-419). |
| F04 (Major) | Retention floor read raw `SwingBreakN`, but the bootstrap ran on the inner-joined `MatchedN`. An instrument could pass the floor on counts while inference ran on a small subset. | Floor is now derived from `MatchedN` inside `compute_primary_effects` (run_experiment.py:430-434); raw `SwingBreakN` is reported in `event_counts.csv` for transparency but does not gate the verdict. |
| F05 (Major) | `_latest_usable_swing` and `find_swing_break_for_sweep` enforced segment equality on swing source AND on candidate break bars; early-Test sweeps were systematically denied any usable swing. | Segment filter removed from `_latest_usable_swing`; candidate scan no longer halts at segment boundary. Break events are tagged by the break candle's segment and the `CrossSegment` flag is recorded for auditing (run_experiment.py:160-227). |
| F10 (Minor) | `add_ny_time_features` was called although no NY/macro column is read downstream. | `load_instrument_bars` now uses a minimal Polars `with_row_index` path for Segment only. |

## 1. Scope Document

| Check | Result | Notes |
|---|---|---|
| Single falsifiable question | PASS | One H3 variant test (causal micro swing-break confirmation vs EXP-018 displacement). |
| Criteria measurable | PASS | `>= 0.25R` return improvement OR `>= 0.25R` median MAE improvement on `>= 3` instruments; `>= 50` events per train/test segment. |
| Holdout exclusion | PASS | First-70% only via `load_analysis_timebars`. |
| Real-price outcome discipline | PASS | Outcomes via `compute_real_price_outcome` on real OHLC. |
| Dependency handling | PASS | EXP-018 `entry_proxy_events.csv` required; missing-file fast-fail (run_experiment.py:97-105). |

## 2. Analysis Plan (revised)

| Check | Result | Notes |
|---|---|---|
| Median MAE explicit | PASS | Step 3 declares 'MAE is compared using a paired *median* bootstrap'. |
| CI-based criteria explicit | PASS | Step 3 states 'A metric passes only when its bootstrap CI95-low clears the predeclared threshold... CI95-high strictly below the threshold counts as refutation'. |
| Cross-segment swing usage documented | PASS | Step 3 explicitly notes swings from Train can confirm a Test break and vice versa, with the break-candle's segment governing the event label. |
| Retention floor source | PASS | Step 3 declares floor is keyed off MatchedN, not raw SwingBreakN. |

## 3. Code Review

### Causal Swing Confirmation

| Check | Result | Notes |
|---|---|---|
| Two-left/two-right pivot detection | PASS | `detect_confirmed_swings` (run_experiment.py:121-156); pivot must strictly exceed left and right windows. |
| Usable timestamp is right-side confirmation bar | PASS | `UsableIndex = idx + SWING_LEFT_RIGHT` (run_experiment.py:129); `UsableTime` is the corresponding `CloseTime`. |
| No look-ahead at break detection | PASS | `_latest_usable_swing` filters `UsableTime < close_time` of the candidate (run_experiment.py:170-175). |

### Break Detection and Segmentation

| Check | Result | Notes |
|---|---|---|
| Cross-segment swing usage allowed | PASS | Segment filter removed from `_latest_usable_swing`. Production parity restored. |
| Break candidates not halted at segment boundary | PASS | `find_swing_break_for_sweep` scans through `len(bars)` without an early return on segment change (run_experiment.py:191-227). |
| Cross-segment cases flagged | PASS | `CrossSegment` boolean recorded on the miss row when `BreakSegment != sweep_segment` (run_experiment.py:218-219). |

### Statistical Correctness

| Check | Result | Notes |
|---|---|---|
| MAE bootstrap uses median statistic | PASS | `use_median=True` on the MAE call (run_experiment.py:419). |
| Criteria require CI95-low to clear threshold | PASS | `ReturnCriterionMet` and `MAECriterionMet` (run_experiment.py:443-462). |
| Refutation criteria | PASS | `ReturnRefutes` / `MAERefutes` require CI95-high below threshold (run_experiment.py:463-476). |
| Floor keyed off MatchedN | PASS | `matched_n = int(ret_stats["N"])`; `floor = matched_n >= MIN_CONFIRMED_EVENTS` (run_experiment.py:430-434). |
| Lenient INCONCLUSIVE escape removed | PASS | The old `PositiveBelowThreshold` rescue is gone; INCONCLUSIVE only fires when intervals genuinely neither pass nor refute. |
| Matched-pair join is 1:1 | PASS | `validate="1:1"` on the sweep-key inner merge (run_experiment.py:386). |

### Code Quality

| Check | Result | Notes |
|---|---|---|
| Imports unused module dropped | PASS | `add_ny_time_features` / `train_cutoff_time` removed; `polars` added for minimal Segment labelling. |
| NaN handling explicit | PASS | `paired_bootstrap_diff` filters `np.isfinite(base) & np.isfinite(variant)` before computing diffs. |
| No look-ahead in MAE comparison | PASS | Match is by sweep key; outcomes are precomputed from the entry timestamp forward. |

## 4. Verification

- `python3 -m py_compile python/experiments/EXP-019/code/run_experiment.py` passed.
- Experiment code was not executed by the reviewer.

## 5. Required Re-Execution

`python/experiments/EXP-019/results/` reflects the pre-revision code which produced `FOR (4/4)` on point estimates with CIs spanning zero. It must be regenerated under the revised criteria. EXP-019 still consumes EXP-018's `entry_proxy_events.csv`; if EXP-018 is re-run first, EXP-019's matched comparison will pick up the unchanged baseline rows.

## Verdict

```text
VERDICT: APPROVE
```

The revised implementation addresses F01/F02/F04/F05/F10. The new verdict will not declare FOR on point estimates alone, will use the correct statistic for MAE, and will not pretend an instrument met the floor when its matched sample did not.

## Execution Instructions

```text
Pre-execution review: APPROVED (post-adversarial revision)

Experiment: EXP-019 — Micro Swing Break Confirmation After Sweep
Code:       python/experiments/EXP-019/code/run_experiment.py
Expected output: python/experiments/EXP-019/results/
                 python/experiments/EXP-019/plots/

Required prerequisite: EXP-018 results from the revised run.

Please run the experiment code and confirm when complete.
```
