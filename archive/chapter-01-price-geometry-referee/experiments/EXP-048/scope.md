# Experiment: EXP-048 — Phase 014-A Substrate & Detector Readiness (ATR-ZigZag + HA Harami, 102 Cells)

**Phase:** 014 (HA-harami substrate & capture geometry; checkpoint
`2026-06-14-014-ha-harami-substrate-and-capture`, G0 PASS 2026-06-14) ·
**Sub-phase:** 014-A · **HYP:** HYP-001 · **Registry:**
`CF-HA-HARAMI-001/HYP-001` (multiplicity-registry Phase 014 batch) ·
**Candidate slots:** 0 (characterization/readiness) · **TEST reads:** 0
(TRAIN-only; no ledger entry; nested analysis-set TEST stratum unread).

**Analog:** EXP-020 / EXP-043 substrate-readiness pattern. **Gating
precondition:** §5 New-Domain VAL gate — **VAL-004 PASS 2026-06-14** (all 17
instruments × {15m, 30m} ADMITTED, dropped fractions 0.003–0.133, well below
the 0.25 admission gate); 5m/1h/2h/4h previously validated (VAL-001 rev. 3 /
VAL-003 / EXP-043). All 102 cells are therefore domain-eligible at scope time.

**Context:** First experiment of the new `CF-HA-HARAMI-001` family. Validates
**two independent primitives** — the ATR-ZigZag trend substrate (real bars) and
the HA harami detector (HA candles) — *separately*, before any combined
event definition. No combination of the two primitives is made here (that is
EXP-050+/014-B). No edge, return, capture, or P&L metric is computed.

## Hypothesis

Exploratory readiness question (no market-edge claim): for every one of the 102
cells (17 instruments × {5m, 15m, 30m, 1h, 2h, 4h}), the ATR-ZigZag trend
substrate (Wilder ATR-14, `ATR_MULT=1.0`, on real bars) **and** the HA harami
detector (on HA candles) can each be computed **deterministically**,
**look-ahead-safe**, and **invariant-clean** on the TRAIN analysis stratum; and
their measured per-cell move/event rates and `/BARCFG` coverage are produced as a
descriptive map that quantifies per-cell context for the downstream capture read
(EXP-049).

## Question

For each of the 102 cells: (a) does the domain-bar construction from 1-minute
source bars pass integrity checks on the TRAIN slice; (b) does the ATR-ZigZag
substrate produce alternating, causally-confirmed, deterministic, invariant-clean
confirmed moves; (c) does the HA harami detector produce invariant-clean,
deterministic harami events whose latest-body-inside-prior-body condition holds by
construction; (d) how many ZigZag confirmed moves and HA harami events does each
cell yield (rates per 1,000 domain bars), relative to the 30-event reporting floor
that informs EXP-049 capture power; and (e) what is the per-cell `/BARCFG`
coverage — the empirical distribution of the four `{HA_1 dir} × {HA_0 dir}`
configurations among harami events (measured, never assumed uniform)?

## Scope Boundaries

- **Data Views**: 1-minute time bars
  (`data/timebars/timebars_<SYMBOL>_*.parquet`), aggregated to 5m, 15m, 30m, 1h,
  2h, 4h clock-aligned domain bars via `xen.bar_aggregator.aggregate_ohlc`. **5m
  uses strict coverage** (`min_coverage=None`, the established 5m convention);
  **15m/30m/1h/2h/4h use `min_coverage=0.90`** (matching the EXP-004/009/043 and
  VAL-004 convention). Heiken Ashi candles are generated from the domain bars via
  `xen.heiken_ashi_generator.generate_heiken_ashi` (one HA candle per domain bar).
  No Line Break / Renko views.
- **Primitives (two, independent; both frozen at D0 defaults, none varied)**:
  1. **ATR-ZigZag trend substrate (real bars)** — P1 defaults: Wilder ATR
     estimator, `atr_period = 14`, `ATR_MULT = 1.0`. Warmup: no pivot/threshold
     until ATR is defined (≥14 completed real domain bars); pre-warmup bars carry
     no trend state. Seeding on the first defined bar: bullish bar
     (`Close > Open`) → trend Bullish, pivot `High`; bearish → trend Bearish,
     pivot `Low`. Trend-change confirmation: first completed bar closing beyond
     `pivot ∓ ATR_MULT × ATR` adversely to the current trend; moves alternate
     direction. Computed on **real** (non-HA) domain OHLC.
  2. **HA harami detector (HA candles)** — `BODY_MAX = max(HAOpen, HAClose)`,
     `BODY_MIN = min(HAOpen, HAClose)`; harami iff
     `BODY_MAX_1 > BODY_MAX_0 ∧ BODY_MIN_1 < BODY_MIN_0` (latest HA body strictly
     inside the prior HA body). Binding reduced form (family doc): since
     `HAOpen_0 = (HAOpen_1 + HAClose_1)/2` is the exact centre of the prior body,
     the condition reduces to `HAClose_0 ∈ (BODY_MIN_1, BODY_MAX_1)`. Detection is
     **independent of the ZigZag substrate**.
- **`/BARCFG` taxonomy (coverage measured, not assumed)**: each harami event is
  labelled by `(HA_1 Direction, HA_0 Direction) ∈ {(+1,+1), (+1,-1), (-1,+1),
  (-1,-1)}`. The per-cell empirical frequency of each of the four configurations
  is reported. `HA_0` colour is the deterministic function of where `HAClose_0`
  lands relative to the prior-body centre (family doc); coverage is an outcome of
  the data, never assumed uniform.
- **Instruments (17)**: BTCUSD, EURUSD, USTEC, XAUUSD (core) + GBPUSD, USDJPY,
  USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30,
  JP225 (new universe, VAL-003 PASS; 15m/30m additionally VAL-004 PASS). **DE30
  disclosure:** broker history ends 2026-01-16 (~5 months short of the rest);
  boundaries derive from its own realized timeline; all DE30 counts/rates carry a
  shorter-span note and are not span-comparable to full-history instruments.
- **Time range**: **TRAIN stratum only** — the first 70% of each instrument's
  first-70% analysis slice (i.e. first 49% of the full file), derived from the
  1-minute-row chronological order via the R1.3 / EXP-043 F01 convention
  (`train_end_ts` = last `CloseTime` of the first `int(int(total_rows*0.7)*0.7)`
  file-order 1-minute rows). Domain bars whose source rows extend past
  `train_end_ts` are excluded. **The nested analysis-set TEST stratum is not read**
  (operator decision 2026-06-14): readiness, rates, and coverage are TRAIN-only,
  preserving TEST for a future EXP-027-analog event-level calibration.
- **Global holdout**: the final 30% of each file is never loaded, inspected,
  counted, plotted, or used in any capacity. Only Parquet **metadata** (schema +
  total row count via `scan.select(pl.len())`) is read to locate the split; no
  holdout row value is materialized. No TEST-stratum rows are read either; no TEST
  event counts are projected (this experiment makes no power *projection* — it
  reports realized TRAIN counts only).
- **Look-ahead bias prevention**:
  - Domain aggregation emits only completed windows; HA generation is a sequential
    rolling transform (prior HA-Open/Close state only).
  - The ZigZag substrate is implemented as a **sequential streaming** state machine
    over completed domain bars: ATR at bar *N* uses only bars ≤ *N*; the tracked
    threshold `pivot ∓ ATR_MULT × ATR` updates only on completed bars; a
    trend-change is confirmed only at the completed bar that closes beyond the
    threshold. The retroactively-located pivot is **future information** relative to
    the bars between it and the prior confirmed pivot and is used **only** for
    grouping already-completed moves — never as a point-in-time signal. The
    operative point-in-time reference is the **confirmation bar**, whose timestamp
    is strictly later than the pivot it confirms (a checked invariant).
  - All ordering and alignment use `CloseTime`, never bar index.
- **Real-price discipline**: the ZigZag substrate and all its thresholds are
  computed on **real** domain OHLC. The harami detector runs on HA (synthetic)
  candles — permitted because EXP-048 computes **no** return, capture, excursion,
  or P&L metric of any kind. (Every *outcome* metric in this family, from EXP-049
  on, is computed on real prices; none appears here.)
- **Exclusions**: no combined harami-at-trend-exhaustion event definition (014-B /
  EXP-050+); no 3-barrier capture, favourable/adverse targets, third barrier, or
  capture-rate read (EXP-049); no returns, MFE/MAE, expectancy, or edge of any
  kind; no strong-move filters (`/STRONG-STAT`, `/STRONG-HA` — EXP-051); no
  signal-vs-confirmation comparison (`/CONFIRM` — EXP-052); no near-exhaustion /
  position-in-move characterization (EXP-050); no `ATR_MULT`, `LOOKBACK`, MA, or
  `min_coverage` sweep or selection; no cost model; no cross-instrument or
  cross-domain pooling; no TEST or holdout contact; no parameter tuned or frozen
  against any EXP-048 output.

## Per-Cell Checks (the measurement)

1. **Construction integrity** (per instrument × domain, on the TRAIN slice): OHLC
   consistency (`High ≥ max(Open, Close)`, `Low ≤ min(Open, Close)`); strictly
   increasing `CloseTime`; clock-aligned window boundaries; and the
   **dropped-window fraction** under `min_coverage=0.90` (15m/30m/1h/2h/4h only;
   5m strict has none). **Frozen thresholds (predeclared, pre-data-contact;
   carried verbatim from EXP-043 / VAL-004):** dropped fraction `< 0.10` = clean;
   `0.10–0.25` = flagged disclosure (READY-eligible, recorded); `> 0.25` =
   construction FAIL → the cell is `COVERAGE_EXCLUDED` (NOT_READY for that cell
   only, recorded — cf. JP225-2h in EXP-043), not a suite defect. Bar-count
   plausibility (e.g. 2h ≈ ½ of 1h on the same span) is disclosure-only and cannot
   change READY.
2. **ZigZag invariant battery** (per cell): confirmed moves strictly **alternate
   direction** (no two consecutive same-sign moves); every confirmation
   `CloseTime` is strictly later than the pivot it confirms (causality); every
   confirmation timestamp lies within the TRAIN span (`≤ train_end_ts`); the
   confirming bar's close is beyond `pivot ∓ ATR_MULT × ATR` on the adverse side;
   confirmation times are strictly monotone increasing; no NaN/null in any emitted
   substrate field; pre-warmup bars carry no trend state.
3. **HA harami invariant battery** (per cell): every flagged harami event
   satisfies `BODY_MAX_1 > BODY_MAX_0 ∧ BODY_MIN_1 < BODY_MIN_0` **and** the
   reduced form `HAClose_0 ∈ (BODY_MIN_1, BODY_MAX_1)` (both checked; they must
   agree); each event references two adjacent HA candles in `CloseTime` order
   (`HA_1` immediately precedes `HA_0`); all event timestamps within the TRAIN
   span; no NaN/null in any emitted detector field; events ordered monotone in
   `HA_0` `CloseTime`; the degenerate prior-body case (`BODY_MAX_1 == BODY_MIN_1`)
   produces **no** harami (documented, not an error).
4. **Determinism**: a full second regeneration of every cell's domain bars, HA
   candles, ZigZag moves, and harami events; the move table and harami-event table
   must compare **frame-identical** (exact) to the first pass.
5. **Move / event rates and `/BARCFG` coverage** (descriptive; denominators and
   zero-baseline fixed below): per cell — ZigZag confirmed-move count and moves per
   1,000 TRAIN domain bars; HA harami event count and harami events per 1,000 HA
   candles; the four `/BARCFG` configuration counts and fractions; flag cells below
   the **30-event reporting floor** (descriptive, informs EXP-049 capture power; it
   is **not** a READY criterion).

## Metric Denominators & Zero-Baseline (predeclared, before implementation)

- **ZigZag move rate** = confirmed moves / 1,000 TRAIN domain bars; denominator =
  the cell's TRAIN domain-bar count (disclosed). A cell with 0 confirmed moves
  reports rate `0.0` with its denominator shown — never `0/0`.
- **Harami event rate** = harami events / 1,000 HA candles; denominator = the
  cell's HA-candle count (= TRAIN domain-bar count, disclosed). 0 harami events →
  rate `0.0` with denominator shown.
- **`/BARCFG` coverage** = config-*k* events / total harami events in the cell;
  denominator = total harami events in the cell. A cell with **0 harami events**
  reports coverage as **non-reportable (null)** for all four configs — never a
  zero-percent or `0/0` value. Coverage is never expressed as a percentage
  improvement over a baseline (it is a raw descriptive distribution).
- **Empty-construction guard**: a cell whose TRAIN slice has fewer domain bars than
  the ATR warmup (14) — so no trend state can form — is reported
  `CONSTRUCTED_EMPTY`, **not** NOT_READY (it is a coverage outcome, not a failure).

## Success / Failure Criteria

- **Cell-level READY**: construction integrity PASS (dropped fraction ≤ 0.25) ∧
  zero ZigZag invariant violations ∧ zero HA harami invariant violations ∧
  determinism PASS. Move/event counts and `/BARCFG` coverage do **not** affect
  READY (lenient, per the Phase 014 §10 / EXP-043 readiness convention; sparse or
  skewed cells are a disclosure, not a failure).
- **Cell-level NOT_READY**: any invariant violation, non-deterministic output, or
  construction-integrity FAIL (incl. `COVERAGE_EXCLUDED` for dropped > 0.25);
  recorded with the failing check. NOT_READY / `COVERAGE_EXCLUDED` cells are
  excluded from EXP-049 with record.
- **Experiment verdict — READINESS_DELIVERED**: the 102-cell READY / NOT_READY /
  `COVERAGE_EXCLUDED` / `CONSTRUCTED_EMPTY` map, the per-cell move/event-rate table,
  and the `/BARCFG` coverage table are produced, whatever the mix.
- **Evidence AGAINST (substrate/detector-level — SUBSTRATE_REFUTED)**: a
  **systematic** failure indicating a primitive or aggregation bug rather than a
  data quirk — **predeclared threshold:** non-determinism on **any** cell, **or**
  the same invariant violated on **≥ 3 instruments** (for either primitive). This
  halts Phase 014-A pending a fix (new VAL/fix cycle), since EXP-049+ cannot build
  on a broken primitive.
- **Inconclusive (cell-level only)**: a `CONSTRUCTED_EMPTY` cell (TRAIN slice
  shorter than ATR warmup); recorded, not counted as NOT_READY.

## Complexity Budget

- Max statistical tests: **0** (descriptive/readiness).
- Max visualisations: **4** — (i) 17×6 READY-status heatmap; (ii) ZigZag
  moves-per-1,000-bars heatmap (17×6); (iii) harami events-per-1,000-candles
  heatmap (17×6); (iv) `/BARCFG` coverage stacked composition by domain.
- Max new code modules: **2** under `python/src/xen/` — a streaming ATR-ZigZag
  substrate generator and an HA harami detector — only if the logic does not fit
  cleanly inside the experiment script. Reuse `xen.bar_aggregator` and
  `xen.heiken_ashi_generator` unchanged (no generator edits permitted). A
  per-cell readiness-check helper may live in the experiment script.

## Data Requirements

Per instrument: lazy `pl.scan_parquet` of the single validated timebars file; read
total row count from metadata; compute `analysis_rows = int(total_rows * 0.7)` and
`train_rows = int(analysis_rows * 0.7)`; collect only the first `train_rows`
file-order 1-minute rows (EXP-043 F01 pattern — take the chronological prefix from
Parquet row order, never sort the full file); assert the collected slice is sorted
by `CloseTime`; set `train_end_ts` = its last `CloseTime`. Aggregate to each domain
(5m strict; 15m/30m/1h/2h/4h at `min_coverage=0.90`); generate HA candles; run the
two primitives; collect per-cell check records, move/event tables, and `/BARCFG`
counts. A second full pass per cell supplies the determinism comparison. Outputs: a
results parquet (per-cell summary), a READY-map CSV, a move/event-rate CSV, a
`/BARCFG` coverage CSV, `run_metadata.json`, and the four bounded plots built from
the already-collected per-cell summaries (no reloads). Expected runtime: minutes
(102 cells × 2 passes), `tqdm` over the 102-cell outer loop.

### Standard Loading Pattern (F01-compliant, TRAIN-only)

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob(f"timebars/timebars_{symbol}_*.parquet"))[-1]

total_rows = pl.scan_parquet(path).select(pl.len()).collect().item()
analysis_rows = int(total_rows * 0.7)        # first 70% = analysis set
train_rows = int(analysis_rows * 0.7)        # first 70% of that = TRAIN (≈49%)
train = pl.scan_parquet(path).slice(0, train_rows).collect()
assert train.get_column("CloseTime").is_sorted()
train_end_ts = train.get_column("CloseTime")[-1]
# nested analysis-set TEST and final-30% holdout never read
```

## Suggested Direction (non-binding)

Mirror EXP-020 / EXP-043 structure. Implement the ATR-ZigZag as an explicit
sequential state machine (the streaming/causality property is the object under
test; vectorize only safe loading, aggregation, and summary). Implement the harami
detector on the already-generated HA frame (a bounded vectorized body-containment
predicate is causally equivalent — each event uses only the current and immediately
prior HA candle). One characterization pass per cell (tqdm over 102 cells)
producing the check record + tables; one full determinism pass; then the four
plots from the collected summaries. Keep per-cell memory bounded; do not retain all
102 domain frames simultaneously.
