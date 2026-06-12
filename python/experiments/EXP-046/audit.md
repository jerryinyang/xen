# Audit Report: Experiment EXP-046

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 3

Audited artifacts: `scope.md`, `analysis-plan.md`, `code/run_experiment.py`,
`code/variant_screen.py`, modified `python/src/xen/avwap.py`, new
`python/tests/test_avwap_band_param.py` additions, and all six files under
`results/`. The run delivered `SCREEN_DELIVERED` with mechanical G1 readout
`ENTRY_GROSS_FLAT`; this audit independently reproduced the mechanical
clearance rule, floors, margins, and rollup with zero discrepancies.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Orchestration matches the plan step-for-step; dependency gates (EXP-044 verdict, EXP-043 boundaries/counts, EXP-045 FH anchor) enforced before any TRAIN read. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `load_train_frame` takes the first `int(int(0.7N)·0.7)` file-order rows via lazy `.head(train_rows)` (EXP-045 F01 pattern); row count, total count, and `train_end_ts` all asserted against the EXP-043 certified boundary record. TEST/holdout rows never materialize. |
| `code/run_experiment.py` | Loader ordering | PASS | No full-file sort (per plan); strict chronological order re-asserted on the collected slice (`is_sorted()` + uniqueness, lines 139–141). |
| `code/run_experiment.py` | Memory/performance | PASS | Lazy scans, column projection, per-instrument frame reuse across that instrument's cells, `del` of frames after use; plots read only the bounded result rows. |
| `code/run_experiment.py` | Safe optimization | PASS | Fixed-offset horizon indexing operates within one chronologically sorted domain frame (explicitly sanctioned by the plan); event generation stays sequential in the frozen generator. |
| `code/run_experiment.py` | Progress tracking | PASS | Single `tqdm` over 259 variant×cell units with postfix; helpers are quiet. |
| `code/run_experiment.py` | Logging/output | PASS | Three concise INFO lines; all detail goes to CSV/JSON. |
| `code/run_experiment.py` | Organization/import side effects | PASS | Imports → path setup → constants → I/O → pure computation → plotting → orchestration → `main()`; directories created only inside `main()`. |
| `code/run_experiment.py` | Plot data reuse | PASS | All four plots consume the in-memory result rows; no reloads or regeneration. |
| `code/variant_screen.py` | Correctness | PASS | Frozen D0 constants; clearance rule implements all four legs exactly (margin ≥ 0, sign at H=4/16, ≥30 evaluable, determinism). `evaluable_mask` (`trigger + 16 ≤ n−1`) fixes one population per cell×variant before any horizon metric. |
| `code/variant_screen.py` | Edge cases | PASS | `n=0` → no means (nulls in CSV, no NaN propagation); `n<30` → `BELOW_FLOOR` with `margin=NaN→null`; non-finite SE blocks CLEAR; `den>0` guard in the bootstrap; determinism failure short-circuits to `DETERMINISM_FAIL`. |
| `code/variant_screen.py` | Type safety / Docstrings | PASS | Full type hints and docstrings on all public functions. |
| `code/variant_screen.py` | NaN handling | PASS | Explicit `np.divide(..., where=den>0)` and finite-filtering in the bootstrap; `math.isfinite` gating before CSV emission. |
| `python/src/xen/avwap.py` | Correctness / determinism | PASS | α/MA exposed behind default-preserving parameters only (`volume_exponent=VOLUME_EXPONENT`, `fast_ma/slow_ma=FAST_MA/SLOW_MA`); input validation (`0 < fast_ma < slow_ma`, `volume_exponent ≥ 0`); warmup fence generalized to `n < slow_ma`. No change to arm/trigger, band, anchor, or pyramid logic. |
| `python/tests/test_avwap_band_param.py` | P8 gate | PASS | 9 avwap tests and the full suite (24 tests) pass, including baseline-fixture invariance at default α/MA — the scope's precondition for any TRAIN read. |

## Numerical Validation

### Spot Checks

Independently recomputed for all 259 clearance rows from `gross_table.csv` +
the frozen P2 cost table:

- **Floor**: `RT + financing × (8·hours(d)/24)` reproduced for all rows to
  <1e-9 bps (e.g. AUDJPY-1h: 5.2 + 0.9×(8/24) = 5.5 bps — matches `floor_bps`).
- **Margin**: `gross(H=8) − floor − 1×SE` reproduced for all eligible rows to
  <1e-9 bps.
- **Verdicts**: re-applied all four CLEAR legs row-by-row → identical
  14 CLEAR / 235 NO_CLEAR / 10 BELOW_FLOOR partition; `gross_h8_bps` in
  `clearance_table.csv` matches the H=8 rows of `gross_table.csv` exactly.
- **Rollup**: recomputed per-variant clearing counts, distinct instruments,
  and Σ margins — identical to `variant_rollup.csv`. Best non-baseline
  variant clears 3 cells (ma_40_100, alpha_1.0) < 5 required, so
  `composition_met=false` everywhere and `ENTRY_GROSS_FLAT` is the correct
  mechanical readout.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| gross(H=8) means | bps, plausibly ±100 | [−52.5, 59.9] | YES |
| SE(H=8) | > 0, larger on 4h | [1.52, 52.4] (max at sparse 4h cells) | YES |
| n_evaluable | ≥ 0; ≥30 for eligibility | [12, 318]; 10 rows < 30 → BELOW_FLOOR | YES |
| Row counts | 7×37 = 259 per table | 259 (events/clearance), 777 gross (259×3), 259 recon (37×7 legs) | YES |
| determinism_pass | all true | 259/259 true | YES |

### Statistical Sanity

No binding statistical tests (0/0 budget). Bootstrap SEs are descriptive,
seeded via `seed_for(...)` per cell×variant — deterministic and 4h SEs (~40–52
bps) consistent with the plan's stated MDE context.

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| F01 file-order TRAIN slice | Source files chronologically ordered | YES | Strict sortedness + uniqueness asserted on every collected slice; `train_end_ts` matches EXP-043 record. |
| Regime-cluster bootstrap SE | Within-regime dependence captured; inter-regime overlap not | DISCLOSED | `n_regimes_evaluable` reported per row as planned; limitation carried in `run_metadata.json` `se_disclosure`. |
| Baseline reconciliation | Regenerated baseline ≡ EXP-043/045 | YES | 259/259 recon legs pass at 1e-9 bps: 37 event-count identities, 111 FH-net anchors (θ∈{4,8,16}), 111 internal gross/evaluable cross-checks. |
| Determinism | Same input+params → identical output | YES | Full-frame equality of a second generation pass per cell×variant, all 259 pass. |

## Results Plausibility

Baseline clears 3 cells — consistent with EXP-045's "positive gross in 31/37
cells but ~5–7 bps short" picture (a handful of cells were expected to sit
near the floor). Clearances concentrate at 4h and in index CFDs
(US2000/US500/DE30), which is precisely the predeclared false-positive
channel (large SEs, calendar-day floor understatement); none of this affects
the mechanical FLAT readout since no variant approaches the 5-cell threshold.
`reconciliation.csv` anchors the baseline row externally before any
non-baseline row is read, as required.

## Scope Compliance

- Analysis plan followed: YES (Steps 1–5 implemented verbatim)
- Deviations: none
- Complexity budget: 0/0 binding tests, 4/4 plots, 1/1 new module
  (`variant_screen.py`; the avwap change is a default-preserving extension of
  the existing module, as budgeted)
- Holdout exclusion verified: YES (TRAIN-only, 0 TEST reads by construction,
  final 30% never scanned into output)
- No net/cost-adjusted return columns anywhere; the floor enters only as a
  comparison constant (exclusion respected)

## Issues

### Critical

None.

### Warning

None.

### Info

1. **`0**0 = 1` under α=0.0**
   - NumPy evaluates `0.0**0.0 = 1.0`, so zero-TickVolume bars get weight 1
     under `alpha_0.0` — exactly the intended TWAP-like anchor; noted so the
     convention is on record.
2. **Internal cross-check shares `evaluable_mask`**
   - Reconciliation leg 3 independently re-indexes the gross computation but
     reuses `vs.evaluable_mask` for population selection. The population
     itself is anchored externally by legs 1–2 (count identity + FH net on
     the full population), so coverage is adequate; flagged for transparency.
3. **CLEAR concentration in correlated 4h index cells**
   - 11 of 14 CLEAR rows are 4h, mostly US2000/US500/DE30 — the exact
     correlated-bloc / calendar-floor caveat channel the plan predeclares.
     Interpretation belongs to Stage 6; no clearance pattern changes the
     FLAT mechanical readout.

## Re-Audit Requirements

None — verdict PASS.
