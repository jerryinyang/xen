# Analysis Plan: Experiment EXP-048

**Phase 014-A · HYP-001 · `CF-HA-HARAMI-001` · readiness/characterization ·
TRAIN-only · 0 candidate slots · 0 TEST reads · gross · no outcome metrics.**

## Objective

Determine, for each of the 102 cells (17 instruments × {5m, 15m, 30m, 1h, 2h,
4h}) on the **TRAIN** analysis stratum, whether **two independent primitives** —
the ATR-ZigZag trend substrate (real bars; Wilder ATR-14, `ATR_MULT=1.0`) and the
HA harami detector (HA candles) — can each be computed **deterministically**,
**look-ahead-safe**, and **invariant-clean**, and to deliver a descriptive map of
per-cell move/event rates and `/BARCFG` coverage that quantifies context for the
downstream capture read (EXP-049).

This is a **correctness-and-coverage** experiment, not an inferential one. It
computes **no statistical test, no return, no edge, and no combined harami-at-
exhaustion event** — the two primitives are validated *separately* (combination is
EXP-050+/014-B). The verdict is mechanical (READINESS_DELIVERED vs
SUBSTRATE_REFUTED), driven by invariant/determinism checks, not by any effect size.

There are no statistical assumptions to defend because no statistical method is
used; the "methods" below are deterministic construction, exact-equality
verification, and descriptive counting with predeclared denominators.

## Methodology

### Step 1: Per-instrument TRAIN slice (F01, holdout-safe)

- **Method**: lazy `pl.scan_parquet` of the single validated timebars file per
  instrument; read `total_rows` from metadata (`scan.select(pl.len())`); compute
  `analysis_rows = int(total_rows * 0.7)` then `train_rows = int(analysis_rows *
  0.7)`; `collect` only the first `train_rows` file-order 1-minute rows
  (`scan.slice(0, train_rows)`); assert the collected slice is sorted by
  `CloseTime`; set `train_end_ts` = its last `CloseTime`.
- **Why this method**: the Parquet rows are already in validated chronological
  order (VAL-001 rev. 3 / VAL-003); taking the file-order prefix avoids sorting the
  full file and never touches the nested analysis-set TEST stratum or the final-30%
  global holdout. Only metadata (row count) of the unread region is read.
- **Simpler alternative considered**: `sort("CloseTime")` then slice — rejected; it
  materializes the whole file (including holdout rows) before slicing. The F01
  prefix pattern is strictly safer and is the established EXP-043 convention.
- **Assumptions**: file-order == chronological order (validated by the cited VALs;
  re-asserted here via `is_sorted()` on the collected slice — a hard failure if
  violated).
- **Expected output**: per instrument, a sorted TRAIN 1-minute frame and
  `train_end_ts`; recorded `total_rows`, `analysis_rows`, `train_rows` in metadata.

### Step 2: Domain-bar construction (6 domains per instrument)

- **Method**: `xen.bar_aggregator.aggregate_ohlc(train_1m, period_minutes=P,
  min_coverage=mc)` for `P ∈ {5,15,30,60,120,240}`, with **`mc=None` (strict) for
  5m** and **`mc=0.90` for 15m/30m/1h/2h/4h**. Drop any domain bar whose
  `CloseTime > train_end_ts` (the aggregator only emits completed windows; this is a
  belt-and-braces TRAIN fence). Record, per cell, the dropped-window fraction from
  `coverage_summary` (15m/30m/1h/2h/4h only).
- **Why this method**: reuses the validated, deterministic, holdout-agnostic
  aggregator unchanged; coverage modes match the family/VAL-004 convention exactly.
- **Simpler alternative considered**: none — this is the single project aggregation
  primitive.
- **Assumptions**: clock-aligned windows; `min_coverage=0.90` retention semantics
  as validated by VAL-004 (`SourceBars ∈ [ceil(0.9·P), P]`).
- **Expected output**: per cell, a domain OHLC(+TickVolume, SourceBars) frame and a
  dropped-window-fraction scalar.

### Step 3: Construction-integrity checks + dropped-fraction gate

- **Method**: per cell, assert `High ≥ max(Open, Close)`, `Low ≤ min(Open, Close)`,
  strictly increasing `CloseTime`, and grid-aligned `CloseTime` (epoch divisible by
  `P·60`). Apply the **frozen dropped-fraction thresholds** (predeclared,
  pre-data): `< 0.10` clean · `0.10–0.25` flagged disclosure (READY-eligible) ·
  `> 0.25` → `COVERAGE_EXCLUDED` (NOT_READY for that cell only, recorded). Bar-count
  plausibility (e.g. 2h ≈ ½·1h) is disclosure-only and cannot change READY.
- **Why this method**: these are the binding integrity predicates; the
  dropped-fraction gate is the same mechanical rule that excluded JP225-2h in
  EXP-043 and admitted all 15m/30m in VAL-004.
- **Assumptions**: none beyond the OHLC schema.
- **Expected output**: per cell, a construction PASS/FAIL flag, the dropped
  fraction, and a coverage-class label.

### Step 4: Primitive A — ATR-ZigZag trend substrate (real bars, streaming)

- **Method**: an explicit **sequential state machine** over completed real domain
  bars (new module `xen.zigzag` if it does not fit cleanly in the script):
  1. **Wilder ATR-14** maintained incrementally — `TR_t = max(High_t−Low_t,
     |High_t−Close_{t−1}|, |Low_t−Close_{t−1}|)`; seed `ATR` as the simple mean of
     the first 14 `TR` values; thereafter `ATR_t = (ATR_{t−1}·13 + TR_t)/14`. No
     pivot/threshold defined until ATR is defined (≥14 completed bars); pre-warmup
     bars carry no trend state.
  2. **Seeding** on the first ATR-defined bar: `Close>Open` → trend Bullish, pivot
     `High`; else → Bearish, pivot `Low`.
  3. **Tracking/confirmation**: in a Bullish trend maintain the running pivot
     `High` and threshold `pivot − ATR_MULT·ATR`; a **trend-change confirmation**
     fires at the first completed bar whose `Close <` threshold (symmetric for
     Bearish with `+`). At confirmation, emit a confirmed move (prior pivot → new
     extreme), flip trend, and reset the pivot to the confirming side. Moves
     **alternate** in direction by construction.
  - ATR at bar *N* uses only bars ≤ *N*; the threshold updates only on completed
    bars; confirmation uses only the completed bar's close. The retroactively
    located pivot is used **only** to label the *boundaries of an already-completed
    move*, never as a point-in-time signal.
- **Why this method**: the streaming/causal property is the object under test;
  Wilder ATR and the `pivot ∓ ATR_MULT·ATR` rule are the D0/P1-frozen definitions.
- **Simpler alternative considered**: a vectorized peak/trough ZigZag — rejected;
  it is non-causal (uses future bars to confirm a pivot) and cannot demonstrate the
  look-ahead-safety this experiment must verify.
- **Assumptions**: deterministic from sequential bar input; no randomness.
- **Expected output**: per cell, a confirmed-move table (`start_time`, `end_time` =
  pivot time, `confirm_time`, `direction`, `start_price`, `end_price`, plus the
  ATR/threshold at confirmation) ordered by `confirm_time`.

### Step 5: Primitive B — HA harami detector (HA candles, independent)

- **Method**: generate HA candles per cell via
  `xen.heiken_ashi_generator.generate_heiken_ashi(domain_bars)` (one HA candle per
  domain bar). Then a **bounded, causally-equivalent** detector (new module
  `xen.ha_harami` if needed): for each adjacent pair `(HA_1, HA_0)` in `CloseTime`
  order, with `BODY_MAX = max(HAOpen, HAClose)`, `BODY_MIN = min(HAOpen, HAClose)`,
  flag a harami iff `BODY_MAX_1 > BODY_MAX_0 ∧ BODY_MIN_1 < BODY_MIN_0`; degenerate
  prior body (`BODY_MAX_1 == BODY_MIN_1`) yields **no** harami. Each event records
  `(HA_1 Direction, HA_0 Direction)` for `/BARCFG`. Detection uses only the current
  and immediately prior HA candle — vectorizing this with a one-row shift is
  causally identical to a sequential pass (no look-ahead).
- **Why this method**: the harami condition is a pure two-candle predicate; a
  shifted-column vector implementation is exactly equivalent and bounded.
- **Simpler alternative considered**: a Python row loop — equivalent result but
  slower; the vectorized shift is preferred and causally identical.
- **Assumptions**: HA generator is the validated rolling transform; detection is
  independent of the ZigZag substrate (no cross-input).
- **Expected output**: per cell, a harami-event table (`ha1_time`, `ha0_time`,
  `ha1_dir`, `ha0_dir`, the four body bounds) ordered by `ha0_time`.

### Step 6: Invariant batteries (both primitives)

- **ZigZag invariants** (per cell): confirmed moves strictly **alternate**
  direction; every `confirm_time` strictly later than its pivot `end_time`
  (causality); every `confirm_time ≤ train_end_ts`; the confirming close is beyond
  `pivot ∓ ATR_MULT·ATR` on the adverse side (re-checked from stored values);
  `confirm_time` strictly monotone increasing; no NaN/null in any emitted field;
  pre-warmup bars carry no trend state.
- **HA harami invariants** (per cell): every event satisfies **both** the original
  inequality and the reduced form `HAClose_0 ∈ (BODY_MIN_1, BODY_MAX_1)` and the
  two **agree** (a disagreement is a violation); `HA_1` immediately precedes `HA_0`
  in `CloseTime`; all event times `≤ train_end_ts`; events monotone in `ha0_time`;
  no NaN/null in any emitted field.
- **Method**: boolean assertions returning a per-cell violation count keyed by
  invariant name (so the SUBSTRATE_REFUTED "same invariant on ≥3 instruments" rule
  is computable from the recorded keys).
- **Expected output**: per cell, a dict of `{invariant_name: violation_count}` for
  each primitive; a cell is invariant-clean iff all counts are 0.

### Step 7: Determinism replay

- **Method**: a full **second pass** per cell (re-aggregate, re-generate HA,
  re-run both primitives) and compare the move table and harami-event table to the
  first pass with `DataFrame.equals` (frame-identical, exact). Any mismatch on any
  cell is a determinism FAILURE.
- **Why this method**: exact frame equality is the strongest determinism check and
  matches EXP-020/043/047 precedent.
- **Expected output**: per cell, a determinism PASS/FAIL boolean.

### Step 8: Descriptive move/event rates + `/BARCFG` coverage (predeclared denominators)

- **Method** (counting only; **no statistical test**): per cell —
  - **ZigZag move rate** = `confirmed_moves / 1000 TRAIN domain bars`; denominator
    = TRAIN domain-bar count (disclosed). 0 moves → rate `0.0` with denominator
    shown (never `0/0`).
  - **Harami event rate** = `harami_events / 1000 HA candles`; denominator =
    HA-candle count (= TRAIN domain-bar count, disclosed). 0 events → rate `0.0`.
  - **`/BARCFG` coverage** = `config_k_events / total_harami_events`; denominator =
    total harami events in the cell. A cell with **0 harami events** reports all
    four configs **non-reportable (null)** — never `0/0`, never 0%. Coverage is a
    raw distribution, never a percentage improvement over a baseline.
  - **Reporting floor flag**: mark cells with `< 30` confirmed moves and/or `< 30`
    harami events (descriptive context for EXP-049 capture power; **not** a READY
    criterion).
  - **Empty-construction guard**: TRAIN domain bars `< 14` (ATR warmup) →
    `CONSTRUCTED_EMPTY` (Inconclusive, not NOT_READY).
- **Expected output**: a per-cell rate table (CSV) and a per-cell `/BARCFG`
  coverage table (CSV) with denominators and zero-baseline classes explicit.

### Step 9: Per-cell READY adjudication + verdict

- **Method** (mechanical): a cell is **READY** iff construction PASS (dropped
  ≤ 0.25) ∧ all ZigZag invariants clean ∧ all HA harami invariants clean ∧
  determinism PASS. Else **NOT_READY** (incl. `COVERAGE_EXCLUDED`), recorded with
  the failing check; or `CONSTRUCTED_EMPTY` if guarded out at Step 8. Experiment
  verdict **READINESS_DELIVERED** if the 102-cell map + rate + coverage tables are
  produced. **SUBSTRATE_REFUTED** iff non-determinism on **any** cell **or** the
  same named invariant violated on **≥ 3 instruments** (either primitive).
- **Expected output**: the 102-cell READY-map CSV, `run_metadata.json` (counts of
  each status, the SUBSTRATE_REFUTED test result, all denominators, parameters,
  `train_end_ts` per instrument, holdout-fence assertions), and the verdict string.

## Visualisations

1. **READY-status heatmap (17×6)** — cell colour by status {READY, flagged-
   disclosure, COVERAGE_EXCLUDED, CONSTRUCTED_EMPTY, NOT_READY-invariant,
   NOT_READY-determinism}. Answers "is either primitive systematically broken on a
   domain or instrument?" (the SUBSTRATE_REFUTED visual).
2. **ZigZag moves-per-1,000-bars heatmap (17×6)** — substrate event density;
   answers "which cells have enough confirmed moves to power EXP-049?"
3. **Harami events-per-1,000-candles heatmap (17×6)** — detector density; answers
   "where is the core signal sparse vs dense?"
4. **`/BARCFG` coverage composition by domain** — stacked bars of the four
   `{HA_1,HA_0}` configuration fractions, **event-pooled within each domain**
   (sum config_k over harami-bearing cells / sum total harami over those cells),
   with the per-domain pooled event count annotated so event-sparse domains are
   visually distinguishable from dense ones. Pooling (rather than an unweighted
   mean of per-cell fractions) prevents event-sparse cells from over-weighting
   noisy estimates. Answers "is the configuration mix uniform, or is one
   configuration dominant — and does it vary by timeframe?" (the family's
   measured-not-assumed `/BARCFG` question).

All four are built from the already-collected per-cell summary frames (no data
reloads, no regeneration).

## Interpretation Guide

- If **all 102 cells (minus any CONSTRUCTED_EMPTY) are READY and determinism passes
  everywhere**, both primitives are validated for the whole grid → READINESS_
  DELIVERED; EXP-049 may proceed on every READY cell. Sparse or `/BARCFG`-skewed
  cells are a **power/coverage disclosure**, not a failure.
- If **a handful of cells are `COVERAGE_EXCLUDED`** (dropped > 0.25, expected
  candidates: JP225-2h and possibly DE30 fast domains given its short span), that is
  a per-cell coverage outcome → those cells excluded from EXP-049 with record; the
  verdict stays READINESS_DELIVERED.
- If **the same named invariant fails on ≥ 3 instruments, or any cell is
  non-deterministic**, that signals a primitive/aggregation **bug** (not a data
  quirk) → SUBSTRATE_REFUTED; halt 014-A and fix the failing primitive before
  EXP-049. This is the predeclared substrate-level Evidence AGAINST.
- If **`/BARCFG` coverage shows a strongly dominant configuration** (e.g. one
  `{HA_1,HA_0}` pair ≫ others), that is the *expected* consequence of the family's
  construction-derived reduction (`HAClose_0` distribution given trend context), to
  be **reported descriptively** and carried into the EXP-050/`/BARCFG` scope — it is
  not a readiness pass/fail signal.
- A cell flagged below the **30-event reporting floor** means EXP-049's capture read
  (which requires ≥30 *resolved* events under P12) is likely power-limited there;
  recorded as context, never as an EXP-048 failure.

No result here can "support" or "refute" a market edge — EXP-048 makes no edge
claim. The only falsifiable content is correctness (determinism, look-ahead safety,
invariants) and constructibility (coverage).

## Complexity Check

- Statistical tests: **0 / 0** (descriptive + invariant verification only).
- Visualisations: **4 / 4**.
- New modules: **≤ 2 / 2** (`xen.zigzag` streaming substrate; `xen.ha_harami`
  detector — only if they do not fit cleanly in the experiment script; reuse
  `xen.bar_aggregator` and `xen.heiken_ashi_generator` unchanged).

## Implementation Safety Constraints (for experiment-developer)

- **Timestamp ordering**: all ordering/alignment by `CloseTime`; never bar index.
  Assert `is_sorted()` on the collected TRAIN slice; derive `train_end_ts` from it.
- **Holdout/TEST fence**: read only Parquet metadata + the first `train_rows`
  file-order rows; never sort or collect the full file; never read TEST or holdout
  rows; assert in code that every emitted domain bar / move / event has `CloseTime
  ≤ train_end_ts`. Record the fence assertions in `run_metadata.json`.
- **Denominators / zero-baseline**: implement the Step 8 rules exactly — guard
  every rate and every `/BARCFG` fraction against a zero denominator (rate `0.0`
  with disclosed denominator; coverage `null`/non-reportable; never `0/0`, never a
  percentage-vs-zero-baseline).
- **Sequential vs vectorized**: the **ZigZag must stay an explicit sequential loop**
  (causality is under test — do not vectorize its confirmation logic). The **harami
  detector may use a bounded one-row-shift vectorized predicate** (causally
  identical) — but must not reach beyond the immediately prior candle. HA generation
  and aggregation are already safe vectorized/rolling primitives.
- **Bounded memory**: process one cell at a time inside the `tqdm` 102-cell outer
  loop; do not hold all 102 domain frames simultaneously; retain only the bounded
  per-cell summary rows and the small move/event tables needed for the determinism
  compare and the 4 plots.
- **Progress / logging**: `tqdm` over the 102-cell loop; concise per-instrument
  logging; helper functions return data rather than printing; output directories
  created only in the orchestration `main()`, never at import time.
- **Determinism**: fixed iteration order (instruments sorted, domains in the fixed
  `{5,15,30,60,120,240}` order); no randomness anywhere (no seed needed — there is
  no sampling in this experiment).

## Data-View / Coverage Notes

- The two primitives emit **different observation counts** for the same span (ZigZag
  moves are far sparser than HA candles, which are 1:1 with domain bars); all
  counting is per-cell with explicit denominators, never cross-view normalized.
- Cross-view comparison is **not** performed here (no harami-vs-ZigZag alignment);
  that is EXP-050. EXP-048 reports the two primitives side by side, independently.
- `TickVolume` is summed in aggregation but **unused** by either primitive in this
  experiment (no volume-profile target until `/VPTARGET` in 014-B).
