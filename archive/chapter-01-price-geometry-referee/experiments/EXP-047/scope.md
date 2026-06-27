# Experiment: EXP-047 — `/ANCHOR` Move-Size Diagnostic (ATR-Prominence Pivot vs Running-Extreme Anchor)

**Phase:** 013 (`docs/experiments-docs/checkpoints/2026-06-12-013-substrate-revision-anchor-move-size/design.md`)
**Registry:** `CF-AVWAP-001/DIAG-007` — 0 slots, 0 TEST reads (TRAIN-only diagnostic)
**Predeclarations:** all binding values frozen in the Phase 013 `D0-predeclarations.md`
(RATIFIED 2026-06-12, G0 PASS: `ATR_period=14`, `k=1.0`, `M=2`); this scope
restates them and adds nothing data-derived.
**Data-contact precondition (P8):** the regression-suite extension (baseline-anchor
fixture invariance at defaults, `/ANCHOR` look-ahead-safety + determinism smoke,
running-extreme fallback path) must be green before the first TRAIN read.

## Hypothesis

Replacing the frozen running-extreme AVWAP anchor with the ratified
ATR-prominence significant-pivot anchor (`/ANCHOR`, `ATR_period=14`, `k=1.0`)
materially shifts the TRAIN gross available favorable move-size (MFE)
distribution rightward — `median_MFE(/ANCHOR) ≥ median_MFE(baseline) + 1×SE_diff`
and `median_MFE(/ANCHOR) ≥ 2 × floor_i,d`, with the MAE shift not erasing the
MFE gain — in ≥5 READY cells spanning ≥3 distinct instruments of the
17-instrument × {1h, 2h, 4h} grid.

## Question

Is the thin captured move a property of anchor placement (fixable in-family
via `/ANCHOR`), or intrinsic to MA(20,50)-regime trend legs at these
timeframes (requiring a new candidate family)?

## Scope Boundaries

- **Data Views**: 1-minute time bars aggregated to 1h/2h/4h domain bars via
  the frozen `xen.bar_aggregator` conventions (2h: `period_minutes=120`,
  `min_coverage=0.90` — Phase 011 P7). AVWAP bounce events via the frozen
  `xen.avwap` machinery extended with a parameterised anchor rule; the
  default (running-extreme) anchor must reproduce the Phases 004–012
  baseline bit-for-bit (P8).
- **Parameters** (all frozen at D0):
  - `/ANCHOR` rule (P1): on a confirmed regime change, **every completed
    bar of the segment since the prior confirmed regime change is a
    candidate pivot** (its `Low` for an incoming bull regime / its `High`
    for bear). A candidate qualifies as a significant pivot iff a
    counter-move ≥ `k × ATR(14)` away from it has already completed on bars
    strictly after it, by the regime-confirmation bar (ATR on the same
    domain bars, completed bars only; `k = 1.0`). Selection: the most
    price-extreme qualifying pivot; exact price ties → most recent. Note
    the segment running extreme is itself the most extreme candidate, so
    whenever it qualifies the `/ANCHOR` anchor coincides with the baseline
    point. Fallback: if no candidate qualifies (or the ATR window is not
    yet full), anchor at the running extreme (baseline) and tag
    `anchor_fallback = true` (fallback rate is a disclosure column).
    *Interpretation note (flagged for operator confirmation at the
    execution gate):* the D0 P1 text names the segment extreme as "the
    candidate" while its tie-break clause contemplates "several segment
    pivots" clearing `k × ATR`; this scope adopts the multi-candidate
    reading, which is the design §5.1 reading ("a predeclared tie-break
    when multiple qualifying pivots exist in the segment") and the only
    reading under which `/ANCHOR` can ever differ from the baseline.
    Everything else frozen to baseline: MA(20,50) regime, typical-price
    source, `TickVolume**0.75` weight, 1.0-MAD band,
    arm/trigger-at-AVWAP-line event rule, pyramid handling.
  - Move-size statistics (P3): per cell × anchor, TRAIN events only, gross,
    real domain-bar prices — **MFE** (max favorable direction-signed
    excursion from the trigger close over the event lifetime; lifetime = to
    MA(20,50) trend-change or analysis-set end, EXP-022 boundary; unfinished
    events counted and disclosed; the lifetime path includes the entry
    point itself, so MFE and MAE are floored at 0 — standard excursion
    convention); **MAE** (matching max adverse excursion);
    **matched-control MFE** (same MFE on matched non-event bars,
    EXP-021/027 instrument/domain/regime-direction matching, descriptive).
    Reported as median + IQR + bootstrap SE of the median (frozen EXP-027
    resampling layer, descriptive).
  - Cost-floor reference (P4): `floor_i,d = RT_i + financing_i ×
    days(L_i,d, d)` with the Phase 011 P2 CONSERVATIVE table verbatim,
    `L_i,d` = the cell's median lifetime holding time in domain bars,
    `days(L, d) = L × hours(d)/24`, hours(d) ∈ {1, 2, 4}. Computed per
    anchor arm; the **binding floor for the P5 check is the maximum of the
    two arms' floors** (conservative — a lifetime shift can never soften
    leg 2), with both arms' floors disclosed. **Reference line only —
    never subtracted from any move-size value.**
  - Readiness criteria (P2): per cell on TRAIN — 0 invariant violations
    (EXP-020 invariant set, anchor-adapted), determinism replay drift 0, no
    look-ahead-safety failure, ≥30 TRAIN `/ANCHOR` events. NOT_READY cells
    excluded from the move-size comparison with the failing check recorded.
  - Shift classification (P5) and composition threshold (P6): restated
    under Success / Failure Criteria below.
- **Instruments / cells**: the **full 17-instrument × {1h, 2h, 4h} grid**
  (51 cells, EXP-043 grid). Membership in the comparison is defined by
  `/ANCHOR` readiness (P2), **not** inherited from the old-anchor 37-cell
  COVERED map. DE30 coverage truncation (broker history ends 2026-01-16,
  VAL-003) carried as a per-cell disclosure.
- **Time range**: TRAIN only — first 70% of the first-70% analysis set per
  instrument, R1.3 1-minute-row timestamp boundary (`train_end_ts`),
  identical to EXP-043/044/045/046. Both anchors generated on the identical
  TRAIN slice. TEST rows are never read; **0 TEST-read ledger entries by
  construction** (prior counted reads per stratum: EURUSD-4h 2 [AT CAP],
  USTEC-4h 1, XAUUSD-4h 1, all others 0 — disclosed, untouched).
- **Global holdout**: the final 30% of each instrument file is never
  loaded, inspected, or used. All holdouts remain sealed.
- **Look-ahead bias prevention**: the anchor is selectable using only bars
  completed at or before the regime-confirmation bar; ATR is causal;
  events use only data at or before the event timestamp; generators run
  sequentially; temporal ordering by `CloseTime`.
- **Real-price outcome discipline**: all MFE/MAE excursions from real
  domain-bar OHLC prices, direction-signed. No synthetic prices in scope.
- **Exclusions**: any net or cost-adjusted move-size column (gross only —
  the floor is a reference line, never subtracted); exit training,
  selection, or portfolio machinery; inference calibration (EXP-027 analog)
  and cTrader parity (EXP-029 analog) — preconditions for a future net
  phase only; TEST or holdout contact; the other Stage-C detectors (`/LB`
  `/MB` `/ATR`); new-family design; grid extension, threshold change, or
  anchor re-parameterisation after any distribution is seen; 5m;
  cross-instrument pooling for per-cell verdicts; any binding p-value or
  significance claim; paired-test framing (the two anchors generate
  different event populations — the comparison is a distributional location
  shift and is reported as such).

## Success / Failure Criteria

Sub-step 1 — readiness (G1a, mechanical, per cell): a cell is **READY** iff
0 invariant violations, determinism replay drift 0, no look-ahead-safety
failure, and ≥30 TRAIN `/ANCHOR` events. NOT_READY cells are excluded from
the comparison with record.

Sub-step 2 — shift classification (P5, mechanical, per READY cell): a cell
is **SHIFTED_VIABLE** iff all of:
1. `median_MFE(/ANCHOR) ≥ median_MFE(baseline) + 1 × SE_diff` (bootstrap SE
   of the median difference — a **noise guard**, not the materiality gate;
   at typical cell sizes 1×SE is a few bps. The sole materiality gate is
   leg 2);
2. `median_MFE(/ANCHOR) ≥ 2 × floor_i,d` (binding floor = max of the two
   arms' lifetime-derived floors);
3. `Δ median_MAE ≤ Δ median_MFE`;
4. ≥30 TRAIN `/ANCHOR` events;
5. determinism replay passes.
Otherwise **NOT_SHIFTED**.

Phase-level (G1b, adjudicated in the checkpoint, not inside this
experiment):
- **ANCHOR_MOVE_VIABLE (Evidence FOR)**: SHIFTED_VIABLE set spans ≥5 cells
  over ≥3 distinct instruments → route to an in-family `/ANCHOR` viability
  phase.
- **ANCHOR_MOVE_FLAT (Evidence AGAINST)**: composition threshold not met —
  a complete, routable outcome → route to a new candidate family per the
  operator pre-commitment.
- **Inconclusive**: only if integrity failures (P8 regression gate,
  baseline reconciliation, determinism, readiness collapse across most of
  the grid) prevent the mechanical count — partial-grid results do not
  soften the threshold.

Integrity anchor (blocking): the regenerated baseline-anchor events must
reconcile against the EXP-045/EXP-046 gross proxies on shared cells
(event-count identity vs EXP-043 realized counts on the 37-cell COVERED
grid; gross figures consistent with the persisted EXP-045/046 anchors per
the Phase 012 baseline-row convention). Any discrepancy is a blocking
integrity finding and suppresses the mechanical G1 readout.

## Metric Denominators and Zero-Baseline Behavior

- Denominator: per-event — each cell × anchor median/IQR/SE is over that
  cell × anchor's TRAIN events (count always reported alongside).
- The two anchor arms have different event populations by construction; no
  paired or matched anchor-vs-anchor comparison is made beyond the
  distributional location shift defined in P5. No ratio or
  percentage-improvement metrics; no zero baselines arise (floors are
  strictly positive; medians are compared by difference against `SE_diff`
  and by level against `M × floor`).
- Cells with zero or <30 `/ANCHOR` events report `n`, marked
  NOT_READY/BELOW_FLOOR descriptively (no NaN propagation; undefined
  medians are not computed).
- Fallback events (`anchor_fallback = true`) stay in the `/ANCHOR` arm (the
  rule includes its fallback); the per-cell fallback rate is a disclosure
  column.

## Complexity Budget

- Max statistical tests: 0 binding (bootstrap SEs are descriptive; the G1
  composition count is mechanical, not a test)
- Max visualisations: 4 (per-domain MFE-median vs floor comparison panels
  baseline vs `/ANCHOR`; MFE/MAE shift scatter; readiness/fallback-rate
  map; matched-control context panel)
- Max new code modules: 1 (move-size diagnostic utilities; the `xen.avwap`
  anchor parameterisation lives in the existing module behind
  default-preserving parameters, plus the P8 regression-suite extension in
  `python/tests/`)

## Data Requirements

- 17 instrument 1-minute Parquet files under `data/timebars/` (lazy scans,
  sorted by `CloseTime`, sliced to the analysis set then TRAIN before any
  collection).
- Domain aggregation 1h/2h/4h via `xen.bar_aggregator` (frozen Phase 011
  conventions).
- Event generation: `xen.avwap.generate_avwap_events` at frozen baseline
  defaults (running-extreme arm) and with the P1 ATR-prominence anchor
  (`/ANCHOR` arm) on the identical TRAIN slices.
- Phase 011 P2 CONSERVATIVE cost table (RT, financing per instrument) read
  as constants for the floor reference.
- Persisted EXP-043 counts and EXP-045/046 result files for the baseline
  reconciliation anchor (read-only).

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_EURUSD_*.parquet"))[-1]

scan = pl.scan_parquet(path).sort("CloseTime")
total_rows = int(scan.select(pl.len()).collect().item())
analysis_cutoff = int(total_rows * 0.7)
analysis = scan.slice(0, analysis_cutoff)
train_rows = int(analysis_cutoff * 0.7)
train = analysis.slice(0, train_rows).collect()  # 1-minute-row train_end_ts boundary
```

## Suggested Direction

Two sub-steps of one falsifiable question. Track A: extend `xen.avwap` with
the parameterised anchor, get the P8 regression suite green, then run the
EXP-020-analog readiness checks per cell on `/ANCHOR` events. Track B: on
READY cells, compute MFE/MAE/matched-control distributions identically for
both anchors, tabulate against floors, and emit the mechanical
SHIFTED_VIABLE classification per cell. All adjudication (G1a/G1b) is
checkpoint-level desk work on the emitted tables.
