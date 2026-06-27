# Audit Report: Experiment EXP-068

**Title:** MA(20,50)-Substrate Native Combined Champion (Phase 015 S4/native; HYP-021)
**Audited:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, `results/`, and the reused
`xen.position_exits` / `xen.expectancy` modules (unchanged).
**Date:** 2026-06-18

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 3

The implementation reproduces all three frozen P12 anchors exactly (99/99 cells), passes
determinism, causality, and structural-invariant gates, honours the TRAIN-only holdout fence and
real-price discipline, and stays within the complexity budget. The G-015 conjunction is computed
correctly and is internally consistent. The result (`PROCEED_TO_SCREEN_CANDIDATE`, both champion
arms composing) is trustworthy as a *surface input*; its breadth/concentration caveats are flagged
for the analyst (Info 1–2), not as correctness defects. No new `xen/` module was added.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Forks the validated EXP-066 native pipeline; 3 native arms + hyb-BENCH P12 check. P12 reconciliation is the binding correctness proof (below). |
| `code/run_experiment.py` | Edge cases | PASS | Empty harami / empty MA-seg cells return `excluded`; `_empty_arm` for zero-draw nulls; `m<30` → unpowered (no CI); tail-share `0.0` on no-negative-mass. |
| `code/run_experiment.py` | Type safety | PASS | Public functions typed; `ArmResult`/`ArmSpec` frozen dataclasses. |
| `code/run_experiment.py` | NaN handling | PASS | `qualifying_mask`/`weighted_returns` require finite ATR>0 and all-leg finite exits; ADV-NONE NaN adverse is intentional and produces only FAV/TIMECAP/CENSORED. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `load_train_1m` slices first `train_rows = int(int(total*0.7)*0.7)` by file-order prefix; never sorts/collects the full file; asserts chronological; forward scans clipped to `last_train_idx`. TEST + final-30% never read. |
| `code/run_experiment.py` | Loader ordering | PASS | Lazy `scan_parquet` + column projection + `slice` before `collect`; chronological assertion on the slice. |
| `code/run_experiment.py` | Memory/performance | PASS | Per-cell `del cell`; forward scans bounded by `bench_n`; plots from collected per-cell dicts (no reloads, no large pandas conversion). |
| `code/run_experiment.py` | Safe optimization | PASS | ADV-NONE implemented by passing an all-`NaN` adverse level to `resolve_legs` — changes no sample membership, ordering, denominator, or metric; resolver loops kept sequential (causal object under test). |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` over the 17-instrument outer loop; per-instrument `ProcessPoolExecutor`. |
| `code/run_experiment.py` | Logging/output | PASS | `logging` in orchestration/`main()` only; helpers return data. |
| `code/run_experiment.py` | Organization / import side effects | PASS | VAL-001 sectioning; `results/` & `plots/` created in `run()` only; thread-pin before lib imports. |
| `code/run_experiment.py` | Plot data reuse | PASS | All 4 plots consume collected row dicts; no regeneration. |
| `code/run_experiment.py` | Docstrings | PASS | Module + reusable functions documented. |

## Numerical Validation

### Spot Checks

- **P12 reconciliation (the binding correctness proof).** Independently-computed frozen anchors are
  reproduced to `RECON_TOL = 1e-9` on per-cell `m` **and** median, for all 99 cells:
  - `nat BENCH ↔ EXP-061 M0`: 99/99 `m` match, 99/99 median match;
  - `hyb BENCH ↔ EXP-061 H0`: 99/99 / 99/99;
  - `nat PARTIAL-V2A ↔ EXP-066 native PARTIAL-V2A`: 99/99 / 99/99.
  `consistent = 99/99`; `recon_mismatch = []`; both anchor files available. This is a far stronger
  check than a manual median recompute — the entry population, MA geometry, P15 path model, and
  multi-leg resolver all match three prior frozen pipelines exactly.
- **G-015 conjunction logic.** Recomputed `median_viable & mean_positive & beats_rm` over all native
  member rows vs the emitted `g015_passes`: **0 mismatches**. No `g015_passes` cell has `m<30`.
- **ADV-NONE invariant.** `V2A-ADVNONE` signal `adv_count` max = 0, sum = 0 (no adverse stop-out;
  MA cap is the sole stop). Null arm likewise. `advnone_no_stopout` invariant held in all cells.
- **Determinism.** 17 first-usable cells replayed byte-identically (`determinism_ok = True`).

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| per-cell median (ATR units) | ℝ, O(1) | [−2.33, 2.19] | YES |
| per-cell mean (ATR units) | ℝ, O(1), ≤ median (left-skew) | [−1.60, 1.27] | YES |
| `tail_share_worst5` | [0, 1] | [0.160, 0.611] | YES |
| qualifying `m` (member cells) | ≥ 30 power floor | [108, 10667] | YES (all powered) |
| `win_rate` | (0, 1) | [0.368, 0.818] | YES |
| `adv_count` (V2A-ADVNONE) | 0 | 0 | YES |

### Statistical Sanity

| Statistic | Value | Sensible? | Notes |
|-----------|-------|-----------|-------|
| median ≫ mean gap | broad (e.g. GBPUSD-5m median 1.06 vs mean 0.18) | YES | Left-skewed fat-tail return distribution — exactly why the median is the binding endpoint and the mean is a co-primary stress test (P4). |
| mean-positive ⊂ median-viable | PARTIAL-V2A 11⊂45, V2A-ADVNONE 14⊂89 | YES | The mean co-primary is the binding bottleneck, as designed; median viability is broad. |
| ADV-NONE > PARTIAL-V2A on median-viable & beats-RM | 89 vs 45, 85 vs 41 | YES | Removing the adverse stop broadens median viability (no stop-induced negative-median cells) — consistent with the EXP-060B mechanism. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Regime-clustered moving-block bootstrap (median/mean/trim CI) | within-cell exchangeability within regime blocks; `m ≥ 30` | YES | All 99 native member cells powered (`m ≥ 108`); block `b = round(m^{1/3})` per EXP-061 convention; non-parametric (no normality/stationarity/IID assumption). |
| arm − RM-native independent contrast (P5) | RM pool excludes the object's own signal entries; matched count | YES | `matched_count_ok` invariant held (null draw target == signal m per cell); RM drawn on a dedicated stream excluding signal bars. |
| arm − BENCH paired contrast | common qualifying subset ≥ 30 | YES | `paired_n_common` gated at the power floor; disclosed secondary only (not a G-015 criterion). |

## Results Plausibility

Outputs are within domain ranges and patterns are coherent: a broad, strong **median** edge
(median-viable 45/89 of 99) with a much narrower **mean** edge (mean-positive 11/14), the
characteristic left-skew, and ADV-NONE broadening median viability while concentrating its
mean-positive composition in the 4h domain. The robust non-4h core (GBPJPY-30m, GBPUSD-1h,
GBPUSD-5m, NZDUSD-1h, NZDUSD-2h) is consistent across both champion arms and present at BENCH — a
plausible, internally consistent signal rather than a geometry artifact. No DE30-truncated cell
appears in any G-015-passing set.

## Scope Compliance

- Analysis plan followed: **YES** — Steps 0–7 implemented (P12 gate; median CI; mean+trim+tail CI;
  arm−RM contrast; arm−BENCH paired contrast; G-015 conjunction + P11/P6; P4 closure; disclosed
  hybrid). 3 native binding arms + hyb-BENCH P12 check, exactly as scoped.
- Deviations: none.
- Complexity budget: **4/4** statistical methods, **4/4** visualisations, **0/≤1** new modules.
- Holdout exclusion verified: **YES**.
- Hybrid confinement verified: `champion_map.csv` contains `object = ['nat']` only; the hyb-BENCH
  arm is present in the parquet/secondary map but excluded from every native composition, plot, and
  the G-015 readout — matches the scope's "P12 check only, not binding".

## Issues

### Critical
None.

### Warning
None.

### Info

1. **V2A-ADVNONE's G-015 composition is 4h-concentrated (analyst context, not a defect).**
   Its 14 G-015 cells are 8/14 in the 4h domain; the non-4h breadth is 6 (clears the P6 floor of 3
   but is the real load-bearing count). This echoes the EXP-060B "8/14 low-n 4h" concentration the
   Phase 015 P6 rule was written to guard against. The mechanical `fragile` flag is `False` (6>3
   non-4h, 9>3 instruments), but the gate should weight the non-4h breadth, not the headline cell
   count. The bounded-downside `PARTIAL-V2A` is cleaner (9 cells, 7 non-4h, 2 4h). Flagged for
   `results.md`.

2. **The mean co-primary is narrow; ADV-NONE's broad mean-negativity is TAIL_DRIVEN.** Mean-positive
   is 11/14 of 99 vs median-viable 45/89. The P4 closure classifies `PARTIAL-V2A` as
   `PARTIAL_RECOVERY` (51 mean-negative cells, only 1 structural, 0 tail-driven) and `V2A-ADVNONE`
   as `TAIL_DRIVEN` (63/99 tail-driven) — i.e. removing the adverse stop buys a few mean-positive
   cells at the cost of fat negative tails elsewhere, the EXP-060B skew tradeoff. This is the
   decisive interpretive nuance for `results.md`; it does not affect computational correctness.

3. **E402 lint on library imports is intentional.** Imports follow the native-thread-pin block
   (matches the frozen EXP-066 pattern); required so per-process thread pools are pinned before
   `polars`/`numpy` import. No fix needed.

## Re-Audit Requirements

None — PASS. No fixes required.
