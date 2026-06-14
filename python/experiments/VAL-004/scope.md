# Experiment: VAL-004 — 15m/30m Domain Temporal-Integrity Validation (Phase 014 Gate)

## Validation Lineage

`VAL-004` is a VAL-series rerun of **VAL-001 (rev. 3)** — the data-architecture
temporal-integrity validation — applied to the **two new Phase 014 domains
(15m, 30m)** across the full 17-instrument universe, in the tolerant
`min_coverage=0.90` construction mode that Phase 014 will consume.

**Governing phase:** `docs/experiments-docs/checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/design.md` §5 (VAL gate).
**Authorization:** Phase 014 G0 PASS 2026-06-14 (`D0-predeclarations.md`).

### Prior coverage (do not redo; reconfirm only)

The VAL-001 rev. 3 suite validates `SOURCE_TIMEFRAMES = [1, 15, 60]` in **strict**
aggregation mode (a window retained only with exactly `period_minutes` source
bars). VAL-003 ran that unchanged suite across the 13 new-universe instruments;
VAL-001 covered the original 4. Therefore **15m strict-mode aggregation integrity
is already validated for all 17 instruments.** What is *not* yet validated:

1. **30m aggregation** at any coverage mode (period `30` is in no prior VAL
   timeframe set).
2. **Tolerant-mode (`min_coverage=0.90`) construction** of 15m and 30m — the mode
   Phase 014 uses — and its per-cell **dropped-fraction** disclosure.

### Changes from source (VAL-001 rev. 3)

1. **Timeframe set:** `SOURCE_TIMEFRAMES` extended to add **30**; **15** is
   re-included strictly as a **byte-for-byte determinism reconfirmation** against
   the VAL-001/VAL-003 record (anchor, not a new claim).
2. **Tolerant-mode pass added:** for periods {15, 30}, additionally construct
   `aggregate_ohlc(period_minutes=P, min_coverage=0.90)` and apply the **identical**
   integrity checks (future-timestamp, `SourceBars`/coverage semantics under tolerant
   retention, monotonic `CloseTime`, OHLC bounds, cross-view alignment, prefix
   stability, determinism) plus a per-cell **dropped-window-fraction** disclosure.

   **Tolerant `SourceBars` valid range (binding, do not reuse the strict check
   verbatim).** VAL-001's strict `SourceBars` check fails any window with
   `SourceBars != period_minutes`; reusing it under tolerant mode would falsely FAIL
   every legitimately-retained partial window. Under `min_coverage=0.90`,
   `aggregate_ohlc` retains a window iff
   `SourceBars >= max(2, ceil(0.90 * period_minutes))` and `SourceBars` can never
   exceed `period_minutes`. The tolerant integrity check therefore PASSES a retained
   window iff its `SourceBars` lies in the inclusive range
   `[max(2, ceil(0.90 * P)), P]` — **15m → [14, 15], 30m → [27, 30]** — and FAILS
   (wrong-`SourceBars` semantics) any retained window below the floor or above `P`.
   This range mirrors the `aggregate_ohlc` retention rule exactly; if the generator's
   `min_coverage` semantics change, this range tracks it. Strict-mode checks remain
   byte-identical to VAL-001 rev. 3 (`SourceBars == period_minutes`).
3. **Identity everywhere else.** All check logic, negative controls, probe bounds
   (`PREFIX_WINDOW_ROWS`, head/middle/tail positions, fractions {0.34, 0.67, 0.95},
   `DETERMINISM_ROWS`), chart parameters (Line Break level 3, Renko ATR 14), output
   schema, and pass/fail semantics are byte-identical to the approved VAL-001 rev. 3
   suite. No existing check is added, removed, or re-tuned; the only additions are
   period 30 and the tolerant-mode pass with its coverage disclosure. The sole
   parameterization of an existing check is the `SourceBars` valid range, which is
   `== period_minutes` in strict mode (byte-identical to VAL-001) and the tolerant
   range defined in change 2 above when `min_coverage=0.90`; all other check logic is
   unchanged in both modes.

**Role (binding):** 15m and 30m cells are admissible to Phase 014 (EXP-048 onward)
**only after** VAL-004 passes for that instrument×domain. A FAIL or INCONCLUSIVE on
any instrument×domain blocks that cell's admission (not the others'); a
dropped-fraction breach is a recorded exclusion (cf. JP225-2h in EXP-043), not a
suite defect.

## Hypothesis

The 15m and 30m domains, constructed by `xen.bar_aggregator.aggregate_ohlc` from the
first-70% analysis slice of each chronologically ordered 1-minute base file in both
strict and tolerant (`min_coverage=0.90`) modes, preserve temporal alignment across
the scoped time-bar, timeframe, and chart-type views — no future-timestamp or
cross-view misalignment in any emitted row, no structural look-ahead in prefix
stability probes at head/middle/tail — for every one of the 17 instruments.

## Question

For each instrument × {15m, 30m} × {strict, 0.90}: does the aggregated domain pass
all VAL-001 rev. 3 integrity checks, are all negative controls detected, does the
output reproduce deterministically, and what is the per-cell dropped-window fraction
under `min_coverage=0.90`?

## Scope

- **Instruments:** all 17 VAL-003-admitted instruments (BTCUSD, EURUSD, USTEC,
  XAUUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY,
  US500, US2000, DE30, JP225). DE30 truncated-coverage disclosure (broker history
  ends 2026-01-16) carries forward.
- **Data views / periods:** time bars (1m base, sanity anchor) → aggregated 15m and
  30m, each in strict and tolerant (`0.90`) modes; chart-type alignment checks
  (Line Break level 3, Renko ATR 14, Heiken Ashi) over the new domains exactly as
  VAL-001 applies them to its timeframes.
- **Features:** the VAL-001 rev. 3 check battery — future-timestamp, monotonic
  `CloseTime`, `SourceBars`/coverage semantics, OHLC bounds, cross-view timestamp
  alignment, head/middle/tail prefix-stability probes, determinism replay, negative
  controls — plus a per-cell dropped-window-fraction metric for tolerant mode.
- **Parameters:** `SOURCE_TIMEFRAMES = [15, 30]` (15 = determinism anchor);
  `min_coverage ∈ {None (strict), 0.90}`; all other VAL-001 rev. 3 probe bounds and
  chart parameters unchanged.
- **Time range:** first 70% analysis slice of each base file, chronologically
  ordered by `CloseTime`. Derived views generated only from that slice.
- **Exclusions:** the final 30% global holdout is **sealed at first touch** and
  never inspected; no Phase 014 signal/harami logic; no strategy or edge claim; no
  parameter tuning; the existing-universe 1/15/60 strict results are not recomputed
  except the 15m determinism anchor.
- **Constraints:** byte-identical check logic to VAL-001 rev. 3 in strict mode; in
  tolerant mode the only change is the `SourceBars` valid range (Changes §2); all
  other check logic, probe bounds, and pass/fail semantics unchanged; deterministic
  generation; real timestamps only; `tqdm` over the 17-instrument outer loop;
  holdout fence re-asserted in code.

## Success / Failure / Inconclusive Criteria

- **PASS (per instrument × domain × mode):** all integrity checks PASS, all negative
  controls detected, determinism replay reproduces output exactly; tolerant-mode
  dropped fraction disclosed (a value ≤ 0.25 admits the cell; > 0.25 is a recorded
  exclusion, not a FAIL of the suite — mirrors the 2h dropped-fraction gate
  convention).
- **Universe enforcement (binding):** the run reconciles the files present against
  the scoped 17 instruments — each expected instrument must map to exactly one file
  (missing or duplicate ⇒ FAIL, mirroring the VAL-003 duplicate-file resolution);
  files inferred outside the set are disclosed and not processed. The
  reconciliation is recorded in `run_metadata.json`.
- **15m anchor (in-code):** the 15m strict rows are reconciled **within the run**
  against the pinned VAL-001 (4 core) / VAL-003 (13 new) `15m` record — every prior
  `(instrument, view, check)` key must be present and PASS in VAL-004; a divergence
  is a FAIL. (Within-run determinism + a fingerprint are also recorded.)
- **Suite PASS (exit 0):** universe reconciliation PASS; the 15m anchor reconciles
  on all 17 instruments; every cell is ADMITTED or a recorded COVERAGE_EXCLUDED; zero
  integrity failures; all negative controls detected and both must-not-overfire
  assertions hold — i.e. **no FAIL and no INCONCLUSIVE check**.
- **FAIL (exit 1):** any integrity check fails, any negative control is missed, the
  anchor diverges, or the universe does not reconcile → the offending cell is blocked
  from Phase 014 admission (a universe/anchor FAIL blocks the whole gate).
- **INCONCLUSIVE / PASS-with-deferrals (exit 2):** no FAIL, but ≥1 INCONCLUSIVE check
  (e.g. a cell with too few rows to power a probe, or zero candidate windows) → that
  cell is **deferred and recorded**; ADMITTED cells remain individually valid for
  EXP-048. A COVERAGE_EXCLUDED cell (dropped > 0.25) is a recorded exclusion, **not**
  a check FAIL, and does not by itself prevent exit 0.

## Complexity Budget

VAL-class (data-integrity rerun): **0 new statistical tests**; **2 plots** (per-cell
dropped-fraction map for 15m/30m; check-pass heatmap); **0–1 new code modules**
(reuse the VAL-001 rev. 3 harness verbatim; the only new code is the timeframe-set
extension, the tolerant-mode pass, and the coverage-disclosure metric).

## Denominators / Zero-Baseline

- Check-pass rate denominator = number of checks attempted per cell; a cell with
  insufficient rows for a probe is INCONCLUSIVE for that probe, never counted as a
  silent pass.
- Dropped-window fraction = dropped windows / candidate windows at `min_coverage=0.90`;
  a cell with zero candidate windows (degenerate) is INCONCLUSIVE, never `0/0`.

## Holdout Discipline

Final 30% of each base file is the global holdout. **Row contents** — timestamps,
prices, and any derived view — of the final 30% are sealed at first touch and never
loaded or inspected. File-level **metadata** access is permitted and required to
locate the split: the lazy scan reads the Parquet schema and the total row count
(`scan.select(pl.len())`, the sanctioned `_pipeline-config.md` pattern) to compute
`int(total_rows * 0.7)`, then collects only that first-70% chronological slice. No
holdout row value is ever materialized. All construction and validation use only the
first 70% analysis slice. The holdout fence is asserted in code and re-checked in
audit.
