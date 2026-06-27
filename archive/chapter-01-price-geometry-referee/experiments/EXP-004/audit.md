# Audit Report: Experiment EXP-004

Real Dogfood Consistency Anchor — Donchian(20) and MA(20,50) verdicts vs the
EXP-003 calibrated MDE map.

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 4

The implementation matches the approved scope and analysis plan, excludes the
global holdout, preserves look-ahead safety and real-price discipline, loads the
EXP-003 MDE map correctly, and the consistency-classification logic reproduces
exactly under an independent re-implementation across all 48 cells. Results are
internally consistent and plausible. No issue blocks interpretation.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | MDE lookup, candidate generation, referee dispatch, and consistency scoring are correct; orchestration matches the plan's three steps. |
| `code/run_experiment.py` | Edge cases | PASS | Missing/non-finite MDE → `INCONCLUSIVE` (`consistency_status`, lines 137-138); empty file-list raises (line 346-347); `require_exp003_outputs` fails fast if the dependency artifacts are absent. |
| `code/run_experiment.py` | Type safety | PASS | Public functions carry type hints and Parameters/Returns docstrings. |
| `code/run_experiment.py` | NaN handling | PASS | `consistency_status` guards non-finite MDE and coerces non-finite uncertainty to 0.0; effects/CIs come from `finite_values`-filtered bootstrap. |
| `code/run_experiment.py` | Holdout exclusion | PASS | All loading goes through `load_analysis_data`, which slices the first 70% only. `analysis_metadata.csv` confirms `analysis_end` < source-file end date for every instrument (e.g. BTCUSD 2025-06-17 vs file end 2026-05-14). |
| `src/xen/referee_calibration.py` | Loader ordering | PASS | `load_analysis_data` lazily scans, projects `REQUIRED_TIMEBAR_COLUMNS`, sorts by `CloseTime`, then `slice(0, analysis_rows)` before `collect()`; final 30% never materialized. |
| `code/run_experiment.py` | Memory/performance | PASS | Only the 48-row `effect_rows`/`consistency_rows` (and a small aggregation) are converted to pandas for plotting; no full-frame conversions. |
| `src/xen/referee_calibration.py` | Safe optimization | PASS | Vectorized stationary block bootstrap and `int32` indices are documented as method-preserving; split is timestamp-driven (`domain_split_index`), so sample membership, temporal ordering, denominators, and interpretation are unchanged. |
| `code/run_experiment.py` | Progress tracking | PASS | Outer instrument loop wrapped in `tqdm`. (See Info 1 re: the inner Donchian loop.) |
| `code/run_experiment.py` | Logging/output | PASS | Concise INFO logging in `main()`; helpers return data. |
| `code/run_experiment.py` | Organization/import side effects | PASS | imports → path/constants → output helpers → lookup/consistency → candidate generation → plotting → `main()`; `ensure_output_dirs()` is called inside `main()`, not at import. |
| `code/run_experiment.py` | Plot data reuse | PASS | All three plots consume the in-memory `effect_rows`/`consistency_rows` from the single analysis pass; no data is reloaded or regenerated for plotting. |
| both | Docstrings | PASS | Present and accurate. |

## Numerical Validation

### Spot Checks

Independent re-derivation script (`/tmp/exp004_audit_check.py`) over the produced
CSVs, reading only results (no market data):

1. **Consistency classifier reproduced exactly.** Re-implementing
   `consistency_status` independently and re-classifying all 48 rows from
   `dogfood_effects.csv` → **0 mismatches** against `dogfood_consistency.csv`.
2. **MDE map loaded correctly.** Rebuilding the α=0.05 map from EXP-003
   `mde_summary.csv` and comparing to the `mde_bps`/`mde_grid_uncertainty_bps`
   columns in `dogfood_effects.csv` → **0 mismatches** (5m gate 1.0/0.25, 5m min
   0.5/0.25, 1h gate 4.0/1.0, 1h min 0.5/0.25, 4h gate 12.0/2.0, 4h min 2.0/0.5).
3. **Cost accounting verified.** `minimal_baseline.effect − gate_stack.effect`
   equals `cost × (active-bar fraction of the test segment)`. For always-active
   MA the difference equals the per-instrument round-trip cost exactly
   (EURUSD 1.0, USTEC 4.0, BTCUSD 10.0); the lone XAUUSD/5m MA case is
   2.99994 vs 3.0 — a 6e-5 gap = exactly ~1 test bar with `fast_ma == slow_ma`
   (flat, uncharged), which confirms cost is charged only on active bars. For
   Donchian (frequently flat) the gap lies in `[0, cost]` for every cell.

Worked example — BTCUSD/5m/ma_20_50: minimal (gross) effect = +0.01266 bps,
gate (net) effect = −9.98734 bps; difference = 10.0 = BTCUSD round-trip cost.
Gate verdict REJECT, effect −9.987 < MDE+unc (1.0+0.25); CI lower −10.108 <
MDE−unc (0.75) → expected REJECT → `matched_reject` → consistent.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| `effect_bps` | finite ℝ, near-zero gross for untuned strategies | [−12.199, +1.317] | YES |
| `effective_n` | > 0, ≈30% of domain rows | [902, 65144] | YES |
| `block_length` | ≥ 1 | {1} | YES |
| `mde_bps` | EXP-003 α=0.05 values | {0.5,1.0,2.0,4.0,12.0} | YES |
| Verdicts | {PASS, REJECT} | {REJECT} (48/48) | YES |
| `analysis_end` vs source-file end | strictly earlier (holdout reserved) | earlier for all 4 instruments | YES |

### Statistical Sanity

| Statistic | Value | Sensible? | Notes |
|-----------|-------|-----------|-------|
| Gross minimal-baseline effects | clustered near 0 (≈[−2.2, +1.3]) | YES | Untuned Donchian/MA carry no recoverable gross edge — expected. |
| Net gate-stack effects | shifted down by cost×active | YES | All below domain MDE; gate correctly rejects. |
| Effective N per domain | 5m ~50–65k, 1h ~4–5k, 4h ~0.9–1.3k | YES | Tracks 30% test share of each domain; matches EXP-003 magnitudes. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Stationary block bootstrap | Block length estimated on train only | YES | `estimate_block_length` runs on the train segment inside the cores; `block_length=1` for all cells (lag-1 ACF < 1/e for per-bar strategy returns), reducing to i.i.d. resampling — honest and reported. |
| Shared timestamp split | Train/test cut shared across domains via 1m boundary | YES | `domain_split_index` counts `CloseTime ≤ train_end_ts`; not a per-timeframe row fraction (design §9; W2 remediation). |
| Consistency grey band | ±1 MDE grid half-step | YES | `uncertainty_bps` from EXP-003 (`mde_grid_uncertainty_bps`); applied symmetrically in `consistency_status`. |

## Results Plausibility

All 48 cells (4 instruments × 3 domains × 2 strategies × 2 referees) REJECT, and
all are classified consistent (`matched_reject`): each measured net effect sits
below its domain MDE, so both referees correctly reject and the verdicts agree
with the calibration map. This is the expected dogfood-anchor outcome — simple
untuned price strategies do not clear the calibrated detection floor — and it is
the empirical anchor the EXP-003 keystone reading consumes. Plausible and
internally coherent.

## Scope Compliance

- Analysis plan followed: YES (Step 1 dependency/MDE load; Step 2 fixed
  Donchian/MA evaluation; Step 3 consistency classification).
- Deviations: none.
- Complexity budget: 2/2 statistical tests (two referees), 3/3 visualisations
  (`dogfood_effects_vs_mde.png`, `dogfood_consistency_counts.png`,
  `candidate_verdict_matrix.png`), 0/0 new code modules (dogfood position
  generators live in the existing shared `referee_calibration.py` — see Info 3).
- Parameters fixed and untuned: Donchian lookback 20, MA fast 20 / slow 50,
  α=0.05 — matches scope; no optimization.
- Holdout exclusion verified: YES (first-70% slice only; `analysis_end` precedes
  each source file's end date).

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Donchian inner loop is vectorizable.**
   - File: `python/src/xen/referee_calibration.py`, `donchian_breakout_positions`
     (lines 572-591).
   - Description: the per-bar `for index in range(...)` with `np.max/np.min` over
     a rolling window is a Python row loop over up to ~217k bars (5m), and is not
     `tqdm`-tracked. It is **causally correct** (uses only prior bars
     `high[index-lookback:index]`) and bounded, and the run completed.
   - Impact: performance only — no effect on correctness, memory, reproducibility,
     or results. A rolling-window (shifted) max/min would be causally equivalent
     and faster.
   - Fix (optional, future): replace with a vectorized rolling max/min of the
     prior `lookback` bars.

2. **Block length collapsed to 1 for every cell.**
   - Description: `estimate_block_length` returns 1 for all 48 cells, so the
     stationary bootstrap reduces to i.i.d. resampling and `effective_n` equals
     the raw test-bar count. This reflects low lag-1 autocorrelation in per-bar
     Donchian/MA strategy returns and is reported transparently — not a defect,
     but the analyst/documenter should note that effective N here is not
     block-reduced.

3. **Dogfood generators added to the existing shared module.**
   - Description: `donchian_breakout_positions`, `ma_crossover_positions`, and
     `rolling_mean` were added to `python/src/xen/referee_calibration.py` rather
     than a new module file, consistent with the scope's 0-new-module budget and
     pre-execution approval. No standalone EXP-004 module was created.

4. **Grey-band branch is conservative and unexercised here.**
   - File: `code/run_experiment.py`, `consistency_status` (lines 140-148).
   - Description: when a point estimate is clearly above MDE (`effect ≥ MDE+unc`)
     but the CI lower bound is clearly below it (`ci_lower < MDE−unc`), the code
     returns `INCONCLUSIVE/grey_band` rather than treating a REJECT-with-large-
     effect as `FAIL`. This is a conservative operationalization of design §10's
     "reject with effect well above MDE" and is **moot for EXP-004** — every
     cell's point estimate is below MDE, so this branch is never taken (0/48).
     Worth awareness if this classifier is reused on strategies with large
     positive effects and wide CIs.

## Re-Audit Requirements

None — PASS. The four Info notes are advisory and do not require changes for
interpretation to proceed.
