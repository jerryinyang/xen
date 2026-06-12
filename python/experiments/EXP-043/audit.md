# Audit Report: Experiment EXP-043

**Experiment:** Phase 011 Track A Substrate Readiness (Baseline Entry, 51 Cells)
**Audit date:** 2026-06-11
**Audit depth:** light-to-standard (descriptive/readiness experiment, 0 tests /
3 plots / 0 new modules), with independent numerical reproduction of two cells.

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 4

The run is trustworthy: boundary arithmetic reproduces the VAL-001/EXP-001
anchors exactly; two independently re-implemented cells reproduce every
recorded number; all 51 verdicts re-derive from the per-cell check table with
zero mismatches; all rate/projection arithmetic re-verifies to machine
precision; the single NOT_READY (JP225-2h) is the frozen >25% dropped-fraction
gate firing on a measured 0.2566 — correct application, not a bug.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Predicates verified against `xen.avwap`/`xen.bar_aggregator` semantics; independent re-implementation reproduces outputs exactly (see Spot Checks). |
| `code/run_experiment.py` | Edge cases | PASS | Empty event tables → zero violations; bars < 50 → CONSTRUCTED_EMPTY (none occurred); 0-event rate path guarded; NaN dropped-fraction guarded with `math.isfinite` before gating. |
| `code/run_experiment.py` | Type safety | PASS | Public functions typed; `TrainSlice` dataclass carries boundary metadata. |
| `code/run_experiment.py` | NaN handling | PASS | Null/NaN in event columns is itself a counted invariant (0 found); no silent propagation. |
| `code/run_experiment.py` | Holdout exclusion | PASS | F01 pattern: metadata row count → lazy `head(train_rows)` → collect; **no full-file sort**; TEST/holdout rows never materialized; strict order + uniqueness asserted on the collected slice. |
| `code/run_experiment.py` | Loader ordering | PASS | File-order slice per the R1.3 convention (VAL-001 rev. 3 / VAL-003 validated source order), re-asserted post-collect; `train_end_ts` = last TRAIN `CloseTime`. |
| `code/run_experiment.py` | Memory/performance | PASS | One instrument's 1m frame held at a time and dropped; checks are vectorized Polars selects; full run completed in ~2 s. |
| `code/run_experiment.py` | Safe optimization | PASS | The sequential generator is called as-is (defaults only); no vectorized re-implementation of stateful logic; denominators and membership unchanged by any optimization. |
| `code/run_experiment.py` | Progress tracking | PASS | Single `tqdm(total=51)`; helpers quiet. |
| `code/run_experiment.py` | Logging/output | PASS | Concise: verdict counts + per-NOT_READY lines (1) + output paths. |
| `code/run_experiment.py` | Organization/import side effects | PASS | VAL-001-style sections; directories created in `main()` only. |
| `code/run_experiment.py` | Plot data reuse | PASS | All three plots consume the 51-row summary; no reloads. |
| `code/run_experiment.py` | Docstrings | PASS | Present on all functions, including the frozen-threshold and timestamp-convention disclosures. |

Modified `python/src/xen/` modules: none (audited as consumed: `generate_avwap_events`
called with defaults only — the frozen Phase-004 baseline anchored by
`python/tests/test_avwap_band_param.py`; `aggregate_ohlc` at `min_coverage=0.90`).

## Numerical Validation

### Spot Checks (independent re-implementation, separate script)

Two cells recomputed from the raw Parquet with independently written loading,
aggregation, counting, and invariant code:

| Cell | Quantity | Recorded | Recomputed | Match |
|------|----------|----------|------------|-------|
| XAUUSD-4h | domain bars | 2108 | 2108 | YES |
| XAUUSD-4h | TRAIN events / bull / bear | 48 / 22 / 26 | 48 / 22 / 26 | YES |
| XAUUSD-4h | regimes | 45 | 45 | YES |
| XAUUSD-4h | dropped fraction | 0.200607 | 0.200607 | YES |
| XAUUSD-4h | rate per 1k / projection | 22.770398 / 20.571429 | 22.770398 / 20.571429 | YES |
| JP225-2h | domain bars / events | 3951 / 96 | 3951 / 96 | YES |
| JP225-2h | bull / bear / regimes | 60 / 36 / 89 | 60 / 36 / 89 | YES |
| JP225-2h | dropped fraction | 0.256632 | 0.256632 (> 0.25 → NOT_READY correct) | YES |

The full invariant battery (arm < trigger; all timestamps ≤ `train_end_ts`;
trigger on regime side; targets finite/correct sides; monotone trigger times;
zero nulls; regime segments contiguous, anchored, alternating) was re-asserted
independently on both cells: **all pass**. This also constitutes a third
generation pass, extending the in-run two-pass determinism result.

### Cross-table consistency (all 51 rows)

- Verdict re-derivation from raw check columns: **0 mismatches** (50 READY,
  1 NOT_READY, 0 CONSTRUCTED_EMPTY; min bars 1738 ≫ 50).
- `events_per_1k_train_bars` and `projected_test_events_heuristic` arithmetic:
  **0 mismatches** at 1e-9 tolerance.
- Invariant violations: **0 across all cells**; determinism failures: **0**;
  substrate alert correctly `false` (threshold ≥3 instruments, frozen).
- Flag semantics: 10–25% flagged cells = DE30-2h (0.163), US2000-2h (0.103),
  US500-2h (0.196) — all correctly READY-eligible; JP225-2h correctly FAIL
  (not flagged — fail and flag are disjoint by construction).
- Boundary arithmetic: BTCUSD/EURUSD/USTEC/XAUUSD `analysis_rows_1m`
  (1,088,960 / 872,242 / 830,541 / 830,671) reproduce VAL-001/EXP-001
  **exactly** — strong cross-experiment anchor.
- DE30 disclosure present in all four result files and all three plots;
  `power_note` on all 3 DE30 rows.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| direction (events) | {+1, −1} | bull+bear = train_events in all 51 cells | YES |
| train_events | ≥ 0 | [32, 273] | YES |
| events_per_1k_train_bars | ≥ 0, same order across domains | [16.5, 34.0] | YES |
| bar_ratio_2h_over_1h | ≈ 0.5, disclosure band [0.45, 0.55] | [0.4754, 0.4979], 0 flagged | YES |
| dropped_window_fraction | [0, 1] | [0.0026, 0.2971] | YES |
| train_end_ts vs file end | strictly earlier (TRAIN ≈ 49% of rows) | 2024-06..09 vs 2026-01..06 file ends | YES |
| below_30_event_floor | descriptive | 0 cells (min 32, JP225-4h) | YES |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| F01 file-order TRAIN slice | Source files chronologically ordered | YES | VAL-001 rev. 3 / VAL-003 validation; strict-increase + uniqueness re-asserted on every collected slice (would raise otherwise) |
| 30/70 TEST projection | Uniform event distribution (heuristic) | DISCLOSED | Labeled "uniformity heuristic, not an estimate" in column name, scope, and metadata |
| Determinism via 2 in-run passes | Same-process regeneration suffices | YES (strengthened) | Audit's independent third pass in a separate process reproduces counts exactly |

## Results Plausibility

Event rates are remarkably stable across domains (~17–34 per 1,000 bars in
every cell), consistent with the scale-free character of the MA(20,50)-regime
bounce definition. 1h counts (151–273) and 4h counts (32–86) bracket the
old-universe priors (EXP-039 cited ~86 4h TRAIN events on the pooled existing
substrate; AUDJPY-4h measures 86). Forex instruments show low dropped
fractions (0.003–0.08); index instruments show session-gap-driven retention
loss growing with window size (up to 0.297 at JP225-4h) — structurally
expected under clock-aligned windows with `min_coverage=0.90`.

## Scope Compliance

- Analysis plan followed: YES (including all Revision 1 items: frozen 2h
  thresholds, ≥3-instrument systematic rule, heuristic-labeled projection,
  DE30 power note, disclosure-only bar ratio, bucket-membership alignment)
- Deviations: none
- Complexity budget: 0 / 0 tests, 3 / 3 plots, 0 / 1 new modules
- Holdout exclusion verified: YES (loader inspection + boundary metadata +
  2024-era `train_end_ts` vs 2026-era file ends; TEST never read, projections
  arithmetic-only)

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Index-instrument 4h dropped fractions exceed the EXP-001 historical range.**
   - JP225-4h 0.297, US500-4h 0.286, XAUUSD/USTEC/US2000-4h ≈ 0.20 vs the
     old-universe 4h/0.90 range 0.025–0.131 (which covered only 4
     instruments). The 2h-only gate is per the frozen predeclaration; 4h
     fractions are disclosures. Track B scoping should be aware that index 4h
     bars sit on thinner window retention (understated High/Low on partial
     windows per `aggregate_ohlc` docs).
2. **Realized event counts supersede the design §7.4 power expectations.**
   - Per-instrument 1h counts (151–273) are below the design's "~350–400"
     planning figure and 4h counts (32–86) bracket "~90". This is the
     intended Track A measurement (the EXP-042 power statement did not
     transfer); Track B power planning must use this table.
3. **JP225-2h NOT_READY is a coverage outcome, not a generator defect.**
   - All its invariants pass, determinism passes, and its 96 events are
     recorded; the cell fails only the frozen dropped-fraction gate (0.2566 >
     0.25). Its exclusion from Track B is per design §8.2; any revisit (e.g.,
     a different `min_coverage` for JP225) would be a new scoped experiment,
     not a rerun.
4. **DE30-2h sits in the flagged band (0.163), READY with disclosure** — the
   flag, truncation column, and power note all travel together on its rows.

## Re-Audit Requirements

None — PASS.
