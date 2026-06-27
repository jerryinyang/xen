# Analysis Plan: Experiment EXP-043

**Phase:** 011 (Track A, EXP-020-analog) · **Type:** descriptive/readiness ·
**Stat tests:** 0 · **Plots:** ≤3 · **TRAIN-only:** yes (no TEST or holdout
contact; projected TEST counts via the predeclared `TRAIN_count × (30/70)`
rule only)

## Objective

Produce, for each of the 51 instrument×domain cells (17 instruments ×
{1h, 2h, 4h}), a READY / NOT_READY / CONSTRUCTED_EMPTY verdict for the frozen
baseline AVWAP event substrate, plus the TRAIN event-rate / power table that
replaces the non-transferable EXP-042 power statement. No market-edge claim is
made or measurable here: every metric is a construction, invariant,
determinism, or counting check. The experiment verdict is
**READINESS_DELIVERED** when the 51-cell map and the rate table exist,
whatever the READY mix; the only substrate-level negative is a *systematic*
failure (non-determinism anywhere, or a recurring cross-instrument invariant
violation).

## Methodology

All steps are deterministic computations and exact comparisons — no sampling,
no inference, no statistical tests. Methods are listed in pipeline order; each
cell flows through Steps 1–5 inside a single 51-cell loop, then Step 6
aggregates.

### Step 1: TRAIN slice loading (per cell's instrument)

- **Method**: F01-compliant file-order slice — read the Parquet row count from
  metadata, take the first `int(int(total*0.7)*0.7)` rows with
  `pl.scan_parquet(path).slice(0, train_rows).collect()`, then assert
  `CloseTime` is strictly increasing on the collected slice and set
  `train_end_ts` = last `CloseTime`.
- **Why this method**: it is the predeclared R1.3 / VAL-001 rev. 3 convention
  and the EXP-042 F01 pattern; it never pulls TEST/holdout rows through the
  scan engine (a full-file sort would).
- **Simpler alternative considered**: `sort("CloseTime")` then slice — rejected
  because the sort materializes TEST/holdout rows (the F01 critical finding).
- **Assumptions**: source files are chronologically ordered — validated by
  VAL-001 rev. 3 (old universe) and VAL-003 (new universe); the strict-increase
  assertion re-verifies on the loaded slice.
- **Expected output**: one TRAIN 1-minute frame per instrument (17 loads, each
  shared by that instrument's three domain cells) + `train_end_ts` per
  instrument, recorded in the run metadata.

### Step 2: Domain-bar construction + integrity checks

- **Method**: `xen.bar_aggregator.aggregate_ohlc` per cell — 1h and 4h with the
  established construction, 2h with the P7 predeclared `min_coverage=0.90` —
  followed by exclusion of any domain bar whose window extends past
  `train_end_ts`, then exact boolean checks: OHLC consistency
  (`High ≥ max(Open, Close)`, `Low ≤ min(Open, Close)`), strictly increasing
  `CloseTime`, clock alignment of bar boundaries (each bar's source window
  lies within exactly one clock-grid window: strictly increasing grid buckets
  with `OpenTime`/`CloseTime` inside the bucket; **timestamp convention
  disclosed:** the aggregator's domain-bar `CloseTime` is the *last observed
  source close* within its window, so coverage-tolerant windows may close
  before the grid boundary — a modulo-period predicate would false-fail
  legitimate retained windows and is deliberately not used), bar-count
  plausibility (2h count within a tolerance band of half the 1h count on the
  same span — reported as a ratio, flagged if outside [0.45, 0.55];
  **disclosure-only, cannot affect READY**: session-gap structure makes the
  ratio instrument-dependent, and the per-window coverage/alignment
  predicates are the binding checks), and the 2h dropped-window fraction per
  instrument (denominator = number of candidate 2h windows; reported even
  when 0) with **frozen thresholds** (predeclared before any data contact):
  < 10% clean PASS; 10–25% flagged disclosure (READY-eligible, recorded);
  > 25% construction FAIL → NOT_READY for that 2h cell (named check
  `dropped_fraction`).
- **Why this method**: these are the scope's enumerated construction-integrity
  checks; exact predicates need no statistics.
- **Simpler alternative considered**: trusting VAL-001/VAL-003 — insufficient
  because 2h construction has never been run anywhere (first-ever per scope)
  and TRAIN-slicing of domain bars at `train_end_ts` is cell-specific.
- **Assumptions**: none beyond Step 1's ordering guarantee; `aggregate_ohlc` is
  a pure function (stateless, documented).
- **Expected output**: per-cell domain frame + a per-cell construction-check
  record (pass/fail per check, bar counts, 2h dropped fraction).

### Step 3: Baseline event generation

- **Method**: `xen.avwap.generate_avwap_events(frame, instrument=…, domain=…)`
  with **defaults only** (`band_multiplier=1.0`, `arm_at_adverse_band=False`),
  reproducing the frozen Phase-004 baseline (anchored by
  `python/tests/test_avwap_band_param.py`).
- **Why this method**: the scope freezes every parameter; defaults are the
  frozen baseline bit-for-bit.
- **Simpler alternative considered**: none — this is the substrate under test.
- **Assumptions**: the generator is sequential/streaming-safe (documented and
  previously validated in EXP-020); cells with fewer than `SLOW_MA=50` domain
  bars return well-typed empty tables — classified CONSTRUCTED_EMPTY, not
  NOT_READY.
- **Expected output**: per-cell `AvwapResult` (events table per
  `EVENT_SCHEMA`, regimes table per `REGIME_SCHEMA`, `n_domain_bars`,
  `analysis_end`).

### Step 4: Invariant battery (exact predicates on event/regime rows)

- **Method**: per-cell boolean checks over the events and regimes tables:
  1. `armed_time < trigger_time` for every event;
  2. all event timestamps (`anchor_time`, `armed_time`, `trigger_time`) ≤
     `train_end_ts` (and ≤ the cell's `analysis_end`);
  3. trigger close on the regime side of AVWAP:
     `direction × (trigger_close − avwap_at_trigger) ≥ 0`;
  4. favorable/adverse targets finite and on the correct sides:
     for `direction=+1`, `favorable_target_at_trigger > avwap_at_trigger` and
     `adverse_target_at_trigger < avwap_at_trigger` (mirrored for −1), all
     band/target columns finite and non-null;
  5. event ordering monotone non-decreasing in `trigger_time`;
  6. no null/NaN in any required event column (`EVENT_SCHEMA` columns);
  7. regime segments well-formed: non-overlapping
     (`regime_start_idx ≤ regime_end_idx`, consecutive segments
     non-overlapping in index space), anchored (`anchor_idx ≤ confirm_idx`,
     finite `anchor_price`), alternating `direction` signs across consecutive
     regimes;
  8. bull/bear event counts reported descriptively (no threshold).
- **Why this method**: invariants are definitional properties of the frozen
  state machine; a single violating row is a NOT_READY fact, not a sample
  statistic.
- **Simpler alternative considered**: spot-checking a subset of rows —
  rejected; full-table predicates are cheap (vectorized) and the point is an
  exhaustive guarantee.
- **Assumptions**: none.
- **Expected output**: per-cell invariant record — violation count per
  invariant (must be 0 for READY), bull/bear counts.

### Step 5: Determinism (full second regeneration)

- **Method**: regenerate every cell end-to-end (Steps 2–3 from the same loaded
  TRAIN frame) and compare with `DataFrame.equals` (frame-identical: schema,
  order, values) on both the events and regimes tables, plus equality of
  `n_domain_bars` and `analysis_end`.
- **Why this method**: scope mandates a full second pass with exact
  frame-identity; `equals` is the strictest cheap comparison.
- **Simpler alternative considered**: hashing serialized output — equivalent
  strength but `equals` localizes a mismatch for diagnosis; chosen for
  diagnosability at equal cost.
- **Assumptions**: none (determinism is exactly what is being measured).
- **Expected output**: per-cell determinism PASS/FAIL.

### Step 6: Event rates, power table, READY map (aggregation)

- **Method**: per cell — TRAIN event count; events per 1,000 TRAIN domain bars
  with denominator = the cell's TRAIN domain-bar count (a 0-event cell reports
  rate 0.0 with the denominator disclosed; a 0-bar cell cannot occur because
  it would be CONSTRUCTED_EMPTY upstream — no division-by-zero path);
  projected TEST count = `TRAIN_count × (30/70)` (predeclared projection, no
  TEST contact of any kind, including row counts); flag
  `below_30_event_floor = TRAIN_count < 30` (descriptive disclosure only — it
  does not affect READY). Cell verdict: READY iff construction PASS ∧ zero
  invariant violations ∧ determinism PASS; CONSTRUCTED_EMPTY iff TRAIN domain
  bars < 50 (slow MA window); else NOT_READY with the failing check named.
- **Why this method**: these are the scope's predeclared definitions verbatim;
  counting and flagging only.
- **Simpler alternative considered**: none simpler exists.
- **Assumptions**: the 30/70 projection assumes uniform event distribution
  across TRAIN→TEST — regime-dependent AVWAP events do not distribute
  uniformly, so the output column is named
  `projected_test_events_heuristic` and the metadata labels it a
  **uniformity heuristic, not an estimate**; it makes no claim and reads no
  data.
- **Expected output**: `results/readiness_map.csv` (51 rows: cell, verdict,
  failing check if any, DE30 truncation column), `results/power_statement.csv`
  (51 rows: TRAIN events, TRAIN domain bars, rate per 1,000 bars, heuristic
  projected TEST count, floor flag, bull/bear counts, 2h dropped fraction
  where applicable, DE30 truncation disclosure column, and a DE30-specific
  `power_note` stating its projected counts are optimistic by ~15–20% vs
  full-span instruments given the ~5-months-shorter history),
  `results/per_cell_checks.parquet` (full check detail), `run_metadata.json`
  (parameters, file paths, row counts, `train_end_ts` per instrument,
  frozen thresholds, timestamp convention, overall verdict).

## Visualisations (3 / 3 budget)

1. **TRAIN event-count heatmap (17×3)** — instruments × domains, annotated
   with counts; shows at a glance where Track B has power and where the
   30-event floor binds.
2. **Events per 1,000 TRAIN domain bars by domain** — per-instrument points
   grouped by domain (strip/bar); answers whether event *rates* (not raw
   counts) are stable across 1h/2h/4h, i.e. whether 2h behaves as the expected
   middle ground.
3. **2h dropped-window fraction by instrument** — bar chart; the first-ever 2h
   construction at `min_coverage=0.90` needs its retention behaviour disclosed
   per instrument (DE30 annotated as truncated).

All three plots are drawn from the already-aggregated per-cell summary table —
no reloads, no second generation pass for plotting.

## Interpretation Guide (predeclared)

- **Cell READY** iff construction integrity PASS ∧ zero invariant violations ∧
  determinism PASS. Event count is irrelevant to READY (G1 is lenient).
- **Cell NOT_READY** iff any invariant violation, determinism failure, or
  construction failure — recorded with the failing check; excluded from
  Track B (design §8.2).
- **Cell CONSTRUCTED_EMPTY** iff TRAIN domain bars < 50 (no regime can form);
  not a failure.
- **Experiment READINESS_DELIVERED** iff the 51-cell map + rate/power table
  are produced, whatever the mix.
- **Evidence AGAINST (substrate-level halt)** iff non-determinism on *any*
  cell, or the *same* invariant violated on **≥ 3 instruments** (predeclared
  threshold) — a substrate or aggregation bug; Track A halts pending a fix
  cycle.
- **Power disclosures** (descriptive, non-binding): cells below the 30-event
  TRAIN floor are flagged for Track B planning; 4h cells are expected near
  ~30–90 events under §7.4 baseline expectations — sparse is informative, not
  bad.
- 2h dropped-window fraction is governed by the frozen Step-2 thresholds:
  < 10% clean PASS; 10–25% flagged disclosure (READY-eligible); > 25%
  construction FAIL → NOT_READY for that 2h cell. For context, EXP-001
  observed 0.025–0.131 at 4h/0.90. 1h/4h fractions remain disclosures under
  the established construction.

## Implementation Safety Constraints (for experiment-developer)

- **Loading**: F01 pattern only (metadata row count → `slice(0, train_rows)`);
  never sort the full file; assert strict `CloseTime` increase on the
  collected slice; one load per instrument reused across its three cells.
- **Holdout/TEST**: no TEST row, count, or timestamp is read; projections use
  the 30/70 multiplier only. The final 30% is never touched.
- **Temporal alignment**: all checks use timestamps (`CloseTime`,
  `trigger_time`, `train_end_ts`), never bar indices, except the generator's
  own internal index columns which are checked for internal consistency only.
- **Domain-bar TRAIN fence**: drop domain bars whose source window extends
  past `train_end_ts` (compare window end, not window start).
- **Denominators**: events-per-1,000-bars denominator is the cell's TRAIN
  domain-bar count; 0-event cells report 0.0 with denominator disclosed; the
  bar-count plausibility ratio uses the 1h count of the *same instrument and
  span* as denominator.
- **Sequential semantics**: `generate_avwap_events` is called as-is (defaults
  only) — no vectorized re-implementation, no generator changes.
- **Bounded iteration**: outer loop is exactly 51 cells × 2 passes
  (generation + determinism), wrapped in `tqdm`; plotting consumes only the
  per-cell summary (≤51 rows) — bounded pandas conversion permitted there.
- **Output discipline**: helpers return data; orchestration prints concise
  per-cell one-liners; output directories created only in orchestration.
- **NaN handling**: invariant 6 makes nulls/NaNs an explicit recorded
  violation — nothing propagates silently.
- **DE30**: carried verbatim with its truncation disclosure column in every
  output artifact; boundaries from its own realized timeline (the F01 pattern
  handles this automatically).
- **New module**: prefer keeping checks in the experiment script; create at
  most one helper module under `python/src/xen/` only if the check battery
  does not fit cleanly (budget ≤1).

## Complexity Check

- Statistical tests: 0 / 0
- Visualisations: 3 / 3
- New modules: 0–1 / 1
