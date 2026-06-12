# Audit Report: Experiment EXP-045

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 3

Audit basis: full read of `scope.md`, `analysis-plan.md`, both code modules,
all five result files; an **independent from-raw-data recomputation** of one
cell's curves (EURUSD-1h, both families); and a full recomputation of every
stability plane, tunability classification, and cell verdict from the
published CSVs.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Holdout exclusion | PASS | F01 lazy scan, column projection, `head(train_rows)`; EXP-043 source-identity binding (file, rows, TRAIN-end ts); chronology asserted post-collect. TEST/holdout never scanned. |
| `code/run_experiment.py` | Dependency gates | PASS | EXP-044 CALIBRATION_DELIVERED + exactly 37 COVERED cells (read from `coverage_map.csv`, not hard-coded); per-cell event-count consistency vs EXP-043 `power_statement.csv`; replay-cell presence asserted (Rev-1 A/F06). |
| `code/run_experiment.py` | Frozen constants | PASS | FH/MAD grids, k=1, 1×SE separation, P4 floor, P5 rule, and the P2 cost table (EURUSD RT 3.0; all 17 instruments cross-checked against D0) transcribed exactly; no tuning levers. |
| `code/cell_exits.py` | Correctness | PASS | FH index arithmetic; MAD ladder scan guarded by `verify_mad_scan()` (200 fixtures); financing guarded by `verify_financing()` (ns-unit regression, Rev-1 A/F01) — both ran clean in this run's `main()`. |
| `code/cell_exits.py` | Look-ahead | PASS | Exits scan strictly forward over completed closes; targets/AVWAP/spread frozen at trigger; trend-change = next opposite confirmation strictly after the trigger (predeclared convention); FH uses no path info. |
| `code/cell_exits.py` | Endpoint rule | PASS | `endpoint_dominates()` (truncated-neighbourhood endpoint S > every interior S) checked first; endpoints never θ*-eligible. Fired in 42/74 family-cells — reachable and exercised. |
| `code/cell_exits.py` | NaN / no silent drops | PASS | Forced closes flagged + included (none occurred — see range checks); sentinel `n_bars` separates no-trend-change from last-bar exits; split-half fails closed below 10 events (never triggered: min half = 16). |
| both | Determinism | PASS | Bootstrap seeded via `seed_for`; both predeclared replay cells re-run and compared row-identically; `determinism_pass: true`. |
| both | Type safety / docstrings / organization | PASS | Typed dataclasses, sectioned, documented; output dirs only in `main()`; plots from bounded summary rows. |

## Numerical Validation

### Spot Checks (independent recomputation from raw 1-minute data)

Rebuilt EURUSD-1h end-to-end with a **naive** reference implementation
(per-event Python loop, per-target scan, no ladder optimization):

- FH(3) net mean: independent −3.5104978875450863 vs reported
  −3.5104978875450863 — **exact to full float precision** (243 events,
  0 forced closes, matching the reported `forced_close_frac` = 0).
- MAD(1.0) net mean: independent −4.486400271105182 vs reported
  −4.48640027110518 — agreement to 1e-14 (display rounding).

This validates in one pass: the loader, event regeneration, trend-change
lookup, ladder-scan equivalence, the ns financing convention, and the P2
cost application.

### Full-table recomputation (all 37 cells × 2 families)

- **Stability planes**: every S(θ) value re-derived from the published
  `net_mean_bps` (k=1, truncated endpoints) — 0 mismatches across 592 rows.
- **Classification**: θ*, endpoint-dominance, separation vs interior median,
  split-half agreement, and the failure-reason ordering re-derived for all
  74 family-cells — 0 mismatches against `exit_selection.csv`.
- **Cell verdicts**: family selection, FH tie-break, and the P4 floor
  re-derived — all 37 verdicts match (35 NON_TUNABLE, 2 FLOOR_FAIL,
  0 MEMBER).

### Range Checks

| Metric | Expected | Actual | Pass? |
|--------|----------|--------|-------|
| Cells / curve rows / family rows | 37 / 592 / 74 | 37 / 592 / 74 | YES |
| Forced-close disclosure points (>20%) | small | 0 | YES |
| `net_mean_bps` | bps scale | [−49.0, +76.7] | YES |
| Bootstrap SE | positive, wider at 4h | FH [0.92, 40.8]; MAD [1.04, 34.0] | YES |
| Split-half halves | ≥10 events everywhere | min 16 (JP225-4h) | YES |
| DE30 disclosure | verbatim on every DE30 row + metadata + plot | present | YES |

### Statistical Sanity

| Statistic | Value | Makes sense? | Notes |
|-----------|-------|--------------|-------|
| Median net at every grid point | ≈ −5 to −7 bps | YES | Consistent with EXP-030/033/039: gross bounce edge of a few bps at 1h is consumed by CONSERVATIVE RT (3–16 bps) + financing. 20/37 cells are net-negative at **all 16** grid points. |
| `endpoint_argmax` 42/74 family-cells | — | YES | Dominance side is mixed (FH: 12 low / 8 high; MAD: 11/11) — the signature of noisy, flat, mostly-negative planes whose best point wanders to an edge, **not** of a systematically too-narrow grid on one side. |
| `flat_plane` 30/74 | — | YES | Separation requires max S − median S > 1×SE; with planes this flat and SEs of 1–40 bps, failure is the expected outcome. |
| The 2 tunable cells fail P4 with S(θ*) < 0 | EURUSD-1h FH(3) S=−3.45; US500-2h MAD(1.0) S=−0.37 | YES | A tunable-but-negative plateau is exactly what P4 exists to exclude. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Ladder scan ≡ naive scan | causal equivalence | YES | `verify_mad_scan()` + the independent naive recomputation above. |
| Financing units | ns timestamps | YES | `verify_financing()` + spot-check magnitudes (1h-domain FH(3) financing ≈ 0.1 bps at 0.6 bps/day). |
| Split-half minimum | ≥10 events/half | YES | Min realized half = 16. |
| Cluster bootstrap SE | regimes within direction strata | YES | Structure identical to EXP-027/044 lineage; seeded. |

## Results Plausibility

The wipe-out is internally consistent and consistent with prior phases: the
frozen CONSERVATIVE cost model alone exceeds the gross per-event edge at
these domains for most instruments (Phase 008/010 lesson), so net score
curves sit below zero nearly everywhere, planes are flat or edge-wandering,
and no cell clears tunability + floor. Nothing in the failure pattern
suggests an implementation artifact: the two cells that *do* pass tunability
have coherent interior plateaus that simply sit below zero, and the
EURUSD-1h FH plateau at H=3 echoes EXP-033's 1h crossover at H=4.

## Scope Compliance

- Analysis plan followed: YES (including all Revision-1 items: ns financing,
  explicit endpoint rule, DE30 disclosure, direct agree flag, trend
  sentinel, replay assertion — all verified present and exercised).
- Deviations: none.
- Complexity budget: 2 / 2 tests, 5 / 5 plots, 1 / 1 module.
- Holdout exclusion verified: YES. 0 TEST reads.

## Issues

### Critical

None.

### Warning

None.

### Info

1. **`split_half.csv` `agree` is informative, not binding, for
   endpoint/flat cells**: 42 family-cells show `agree=false`, but for most
   the binding failure was `endpoint_argmax` or `flat_plane`; the agree flag
   correctly reports the half-position geometry independently (Rev-1 A/F04
   behaviour, working as designed). Readers should not interpret
   `agree=false` counts as "split-half failures".
2. **SE magnitudes at 4h (up to ~41 bps)** make the separation rule nearly
   unpassable there — consistent with the EXP-044 MDE map (32–128 bps) and
   the plan's predeclared conservative-bias caveat. This is the design
   operating as frozen, not a defect.
3. **`selected_theta` ties to prior evidence**: EURUSD-1h's tunable FH
   plateau at H=3 (S=−3.45 bps) is the net-negative analog of EXP-033's
   gross crossover finding; informational continuity, no action.

## Re-Audit Requirements

None — PASS.
