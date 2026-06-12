# Experiment: EXP-043 — Phase 011 Track A Substrate Readiness (Baseline Entry, 51 Cells)

**Phase:** 011 (per-instrument foundation; checkpoint
`2026-06-11-011-per-instrument-foundation`, G0 PASS) · **Track:** A
(EXP-020-analog) · **Slots:** 0 (diagnostic/readiness) · **TEST reads:** 0
(TRAIN-only; no ledger entry)

**Context:** First Track A item after the 2026-06-11 Track A0 removal
(EXP-042 set aside, FRAMING_ERROR — see
`docs/code-reviews/2026-06-11-band-multiplier-framing-error.md`). Entry is
the **frozen baseline** AVWAP arm/trigger at the line (Phases 004–010,
unchanged); the band multiplier is an exit parameter and is **not** varied
here. This experiment feeds gate G1 (design §8.2, lenient, per cell) and
supplies the baseline per-cell event rates that replace the non-transferable
EXP-042 power statement.

## Hypothesis

Exploratory readiness question (no market-edge claim): the frozen baseline
AVWAP event substrate is deterministic, invariant-clean, and constructible
on all 51 instrument×domain cells (17 instruments × {1h, 2h, 4h}), and its
measured TRAIN event rates quantify per-cell power for Track B exit
training.

## Question

For each of the 51 cells: (a) does the 2h/1h/4h domain-bar construction from
1-minute source bars pass integrity checks (including the first-ever 2h
construction at `min_coverage=0.90`); (b) does the frozen baseline event
generator produce invariant-clean, deterministic events; and (c) how many
TRAIN events does each cell yield (events per 1,000 domain bars, projected
TEST counts), relative to the 30-event reporting floor used for Track B
power planning?

## Scope Boundaries

- **Data Views**: 1-minute time bars (`data/timebars/timebars_<SYMBOL>_*.parquet`),
  aggregated to 1h, 2h, and 4h clock-aligned domain bars via
  `xen.bar_aggregator`. 2h uses the P7 predeclared `min_coverage = 0.90`;
  1h/4h use the established construction. No chart-type views.
- **Parameters (all frozen, none varied)**: baseline AVWAP substrate —
  MA(20,50) regime detector on domain `Close`; typical price;
  `TickVolume ** 0.75` weights; MAD band multiplier 1.0 for the event-row
  band/target columns (exit context only); EXP-020 bounce definition (arm on
  completed close on the opposite side of AVWAP; trigger on completed close
  recrossing the AVWAP in the regime direction).
  `xen.avwap.generate_avwap_events` is called with **defaults only**
  (`arm_at_adverse_band=False`, `band_multiplier=1.0`), which reproduce the
  frozen Phase-004 baseline bit-for-bit
  (`python/tests/test_avwap_band_param.py` anchors this).
- **Instruments (17)**: BTCUSD, EURUSD, USTEC, XAUUSD (old universe) +
  GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY,
  US500, US2000, DE30, JP225 (new universe, VAL-003 PASS). **DE30
  disclosure (P8):** coverage truncated — history ends 2026-01-16;
  boundaries derive from its own realized timeline; carried verbatim in all
  outputs. The power statement additionally carries a DE30-specific note:
  its projected counts derive from a ~5-months-shorter span and are
  optimistic by ~15–20% relative to full-span instruments; Track B power
  planning for DE30 must use its realized span.
- **Time range**: TRAIN stratum only — the first 70% of each instrument's
  first-70% analysis slice, by the R1.3 1-minute-row timestamp convention
  (`train_end_ts` derived from the file's chronological row order, validated
  by VAL-001 rev. 3 / VAL-003). Domain bars whose source rows extend past
  `train_end_ts` are excluded.
- **Global holdout**: the final 30% of each file is never loaded, inspected,
  or used. TEST rows are likewise never read: projected TEST event counts
  are computed as `TRAIN_count × (30/70)` (predeclared projection rule — no
  TEST data contact, including row counts). The projection is labeled a
  **uniformity heuristic, not an estimate** in all outputs: regime-dependent
  AVWAP events do not distribute uniformly in time, so realized TEST counts
  depend on the TEST stratum's regime distribution.
- **Look-ahead bias prevention**: `generate_avwap_events` is sequential and
  never reads beyond the current bar; aggregation emits only completed
  domain bars; all checks use event/bar timestamps, never indices.
- **Real-price outcome discipline**: not applicable — no return, P&L, or
  edge metric of any kind is computed in this experiment.
- **Exclusions**: no TEST or holdout contact; no forward returns, expectancy,
  or edge measurement; no exit training or parameter selection of any kind;
  no band-multiplier variation (exit parameter, Track B); no inference-method
  calibration (EXP-027-analog, separate experiment); no C#/Python parity
  (EXP-029-analog, separate experiment); no cross-instrument pooling; no
  tuning of `min_coverage`, MA windows, or any substrate constant.

## Per-Cell Checks (the measurement)

1. **Construction integrity** (per instrument×domain): OHLC consistency
   (`High ≥ max(Open, Close)`, `Low ≤ min(Open, Close)`); strictly
   increasing `CloseTime`; clock alignment of bar boundaries; bar-count
   plausibility (2h count ≈ half the 1h count on the same span;
   **disclosure-only, cannot affect READY** — session-gap structure makes
   the ratio instrument-dependent and the exact per-window coverage/alignment
   predicates are the binding checks); 2h dropped-window fraction under
   `min_coverage=0.90` reported per instrument with **frozen thresholds**
   (predeclared here, before any data contact): fraction < 10% = clean PASS;
   10–25% = flagged disclosure (READY-eligible, recorded); > 25% =
   construction FAIL → NOT_READY for that 2h cell.
2. **Invariant battery** (per event row / cell): `arm_time < trigger_time`;
   all event timestamps within the TRAIN span; trigger close on the regime
   side of AVWAP at trigger; favorable/adverse targets finite and on the
   correct sides of the trigger AVWAP; event ordering monotone in
   `trigger_time`; no NaN/null in any required event column; regime segments
   well-formed (non-overlapping, anchored, alternating signs); bull/bear
   event counts reported descriptively.
3. **Determinism**: full second regeneration of every cell; events and
   regime tables must compare exactly (frame-identical) to the first pass.
4. **Event rates / power reporting**: TRAIN event count per cell; events per
   1,000 TRAIN domain bars (denominator = the cell's TRAIN domain-bar
   count; a 0-event cell reports rate 0.0 with its denominator disclosed —
   no division-by-zero path); projected TEST count = `TRAIN_count × (30/70)`
   (uniformity heuristic, labeled as such in outputs);
   flag cells below the **30-TRAIN-event reporting floor** (descriptive
   threshold carried from prior power conventions — it informs Track B
   power expectations and is **not** a readiness pass/fail criterion).

## Success / Failure Criteria

- **Cell-level READY**: construction integrity PASS ∧ zero invariant
  violations ∧ determinism PASS. Event count does **not** affect READY
  (G1 is lenient; sparse cells are a power disclosure, not a failure).
- **Cell-level NOT_READY**: any invariant violation, non-deterministic
  output, or construction-integrity failure; recorded with the failing
  check. NOT_READY cells are excluded from Track B per design §8.2.
- **Experiment verdict — READINESS_DELIVERED**: the 51-cell READY/NOT_READY
  map plus the event-rate/power table is produced, whatever the mix.
- **Evidence AGAINST (substrate-level)**: a *systematic* failure —
  **predeclared threshold:** non-determinism on any cell, or the same
  invariant violated on ≥ 3 instruments — indicating a substrate or
  aggregation bug rather than a data quirk; this halts Track A pending a
  fix (new VAL/fix cycle), since Track B cannot train on a broken substrate.
- **Inconclusive (cell-level only)**: a cell whose TRAIN slice has fewer
  domain bars than the slow MA window (no regime can form) is reported
  CONSTRUCTED_EMPTY, not NOT_READY.

## Complexity Budget

- Max statistical tests: 0 (descriptive/readiness)
- Max visualisations: 3 (TRAIN event-count heatmap 17×3; events-per-1,000-bars
  by domain; 2h dropped-bar fraction by instrument)
- Max new code modules: 1 (a readiness-check helper under `python/src/xen/`
  only if the checks don't fit cleanly in the experiment script; reuse
  `xen.avwap` and `xen.bar_aggregator` — no generator changes permitted)

## Data Requirements

Per instrument: lazy scan of the single validated timebars file; assert
chronological order on the collected TRAIN slice (VAL-001 rev. 3 / VAL-003
validated source order; follow the EXP-042 F01 pattern — take the first
TRAIN file-order rows from Parquet metadata counts, never sort the full
file); aggregate to 1h/2h/4h; slice domain bars to `train_end_ts`.

### Standard Loading Pattern (adapted, F01-compliant)

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob(f"timebars/timebars_{symbol}_*.parquet"))[-1]

total_rows = pl.scan_parquet(path).select(pl.len()).collect().item()
analysis_rows = int(total_rows * 0.7)          # first 70% = analysis set
train_rows = int(analysis_rows * 0.7)          # first 70% of that = TRAIN
train = pl.scan_parquet(path).slice(0, train_rows).collect()
# assert sortedness on the collected slice; train_end_ts = last CloseTime
```

## Suggested Direction (non-binding)

Mirror EXP-020's structure: one pass per cell (tqdm over 51 cells) producing
a per-cell check record and the event/regime tables; a second full pass for
the determinism comparison; a single results parquet + power-statement CSV +
READY map CSV; three bounded plots from the already-collected per-cell
summary (no reloads). Expected runtime is minutes, not hours.
