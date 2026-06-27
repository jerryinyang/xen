# Experiment: EXP-049 — Phase 014-A 3-Barrier Capture Readiness & Gross Capture Rate (ATR-ZigZag Reversals, 102 Cells)

**Phase:** 014 (HA-harami substrate & capture geometry; checkpoint
`2026-06-14-014-ha-harami-substrate-and-capture`, G0 PASS 2026-06-14) ·
**Sub-phase:** 014-A · **HYP:** HYP-002 · **Registry:**
`CF-HA-HARAMI-001/HYP-002` (multiplicity-registry Phase 014 batch) ·
**Candidate slots:** 0 (characterization/readiness) · **TEST reads:** 0
(TRAIN-only; no ledger entry; nested analysis-set TEST stratum unread).

**Analog:** EXP-047 capture/excursion machinery (`move_size.py` `lifetime_end`,
`excursions`, bootstrap helpers) + the EXP-048 102-cell substrate/loader pattern.
**Reuse:** `xen.zigzag.generate_zigzag` (frozen, unchanged), `xen.bar_aggregator`,
EXP-047 `move_size.py` pure helpers. **New module (1):**
`python/src/xen/capture_barriers.py` — causal triple-barrier touch resolution on
real OHLC (reusable across 014-B).

**Gating precondition (hard):** EXP-049 consumes the per-cell readiness map from
**EXP-048 (HYP-001)**. EXP-048 must reach verdict **READINESS_DELIVERED** with an
**audit PASS** before EXP-049 executes. Cell membership for EXP-049 = the EXP-048
**READY ∪ READY_FLAGGED** cells only; `NOT_READY_*`, `COVERAGE_EXCLUDED`, and
`CONSTRUCTED_EMPTY` cells are excluded with record. (EXP-048 currently has
`results/` but is not yet audited/closed; this scope, plan, and code may be
prepared now, but the manual execution gate is blocked until EXP-048 is closed.)

## Operator Framing Decisions (recorded 2026-06-14, pre-data-contact)

Four scope-shaping choices were put to the operator before this scope was written;
all are pre-data-contact and tune nothing against outcomes:

1. **Barrier anchor = ZigZag trend-change confirmation only** (the clean
   capture-geometry primitive / substrate capture ceiling). The HA harami signal
   and the `/CONFIRM` entry model are **not** used in EXP-049; harami-conditioned
   capture and entry-model comparison remain in EXP-050 / EXP-052 / 014-B. This
   matches the registered HYP-002 and requires no D0 amendment.
2. **Favourable-target geometry: test BOTH** — distance-based (primary) and
   retracement-level (disclosed secondary), side by side. Nothing is frozen.
3. **Same-bar double-touch resolves to ADVERSE** (conservative triple-barrier
   convention; intrabar order is unknown from OHLC).
4. **Confirmation-entry trigger:** N/A under decision 1 (recorded as "stop at
   signal-bar real extreme" for any future harami arm, not used here).

## Hypothesis

Exploratory capture-geometry question (gross, exit-agnostic, no market-edge
*screen*): for every EXP-048-READY cell (17 instruments × {5m, 15m, 30m, 1h, 2h,
4h}), the 3-barrier capture system (P2 favourable, P3 adverse, P4 third barrier,
P5 `LOOKBACK=1`) can be constructed **deterministically** and **causally**
(every barrier threshold derived only from moves confirmed at or before the
capture event), evaluated entirely on **real prices**; and the per-cell gross
favourable-before-adverse capture rate `r = P(fav before adv | resolved)` is
measured under the predeclared default barriers, with the P12 viability rule and
P11 composition applied mechanically as a routing **readout** (not a gate
decision).

## Question

For each EXP-048-READY cell, taking every confirmed ZigZag trend-change as one
capture event:

a. Can the favourable target (P2), adverse target (P3, 1:1), and the per-cell
   adaptive third-barrier time cap (P4) be computed using only information known
   at the confirmation bar, with a deterministic second-pass replay?
b. Under the **distance-based** favourable geometry (primary), what fraction of
   *resolved* events reach the favourable target before the adverse target,
   per cell — `r`, its regime-clustered bootstrap CI, and the resolved count?
c. Under the **retracement-level** favourable geometry (secondary, disclosed),
   what is the same `r`, with degenerate events (entry already at/through the
   level) excluded and disclosed?
d. Which cells are **VIABLE** by P12 (`r ≥ 0.55` ∧ bootstrap CI_low > 0.50 ∧
   ≥ 30 resolved), and does the family meet P11 (≥ 5 cells over ≥ 3 instruments)
   on the primary geometry?
e. Disclosed secondaries: `fav / all events`, the third-barrier (time-cap)
   censoring fraction, and the data-truncation (TRAIN-edge) censoring fraction.

## Scope Boundaries

### Data Views

- 1-minute time bars (`data/timebars/timebars_<SYMBOL>_*.parquet`), aggregated to
  5m, 15m, 30m, 1h, 2h, 4h clock-aligned domain bars via
  `xen.bar_aggregator.aggregate_ohlc`. **5m strict coverage** (`min_coverage=None`);
  **15m/30m/1h/2h/4h at `min_coverage=0.90`** — identical to EXP-048/VAL-004. No
  Line Break / Renko / Heiken Ashi views (the harami detector is **not** used).
- All barriers and outcomes are computed on **real** domain OHLC. No synthetic
  (HA/Renko) price touches any metric.

### Capture Event (ZigZag trend-change confirmation)

- Run `xen.zigzag.generate_zigzag(bars, atr_period=14, atr_mult=1.0)` (P1, frozen)
  on each cell's real domain bars (TRAIN-only). Each emitted **confirmed move** is
  one capture event.
- **Entry** = the confirmation bar's real close `ConfirmClose` (`C`), at index
  `ConfirmIdx` (the domain-bar index of `ConfirmTime`).
- **Reference move (P5 `LOOKBACK=1`)** = the just-confirmed move itself
  (`StartPrice S`, `EndPrice E`, `Direction d`). Move magnitude `M = |E − S|`
  (`M > 0`; a degenerate `M = 0` move is excluded with record).
- **Reversal direction** `rd = −d` (a confirmed up-move ⇒ short reversal; a
  confirmed down-move ⇒ long reversal). Favourable = the `rd` side.

### Barrier Definitions (frozen at the confirmation bar; real prices)

**P2/P3 — favourable & adverse targets, both geometries (`X = 50%`):**

- **G1 — distance-based (PRIMARY / binding for P12 routing).** Internally
  consistent with P3's literal 1:1 and free of degeneracy:
  - `fav_distance = 0.50 × M`
  - `fav_target = C + rd × fav_distance`
  - `adv_target = C − rd × fav_distance` (1:1).
- **G2 — retracement-level (SECONDARY / disclosed).** Most literal reading of
  P2 ("retrace 50% of the move"):
  - `retrace_level = E − d × 0.50 × M` (the move's midpoint)
  - `fav_distance = rd × (retrace_level − C)`; **degenerate if `fav_distance ≤ 0`**
    (entry already at/through the level — happens when `M < 2·ATR`-scale giveback):
    such events are **excluded from G2** and disclosed (count + fraction per cell),
    never silently defaulted.
  - `fav_target = retrace_level`; `adv_target = C − rd × fav_distance` (1:1 of the
    favourable distance).

**P4 — third barrier (per-cell adaptive time cap):**
`N_event = max(6, round(1.5 × median(duration_bars of the trailing 20 confirmed
moves in this cell)))` completed domain bars after `ConfirmIdx`, where
`duration_bars(move_i) = barindex(ConfirmTime_i) − barindex(ConfirmTime_{i−1})`
(the move's realized confirmation-to-confirmation length). The trailing window uses
only moves with `ConfirmTime` **strictly before** this event's `ConfirmTime`.
**Warmup (P4):** an event whose trailing window holds **< 5** confirmed moves has
no defined cap and is **excluded from the capture read** (insufficient context,
disclosed) — never defaulted. `(window=20, k=1.5, floor=6, statistic=median)` are
frozen governance knobs (k-sensitivity is the `/THIRD-TIME` branch).

### Forward Resolution (causal, conservative, TRAIN-fenced)

- Evaluation window = real domain bars `i ∈ [ConfirmIdx + 1, min(ConfirmIdx +
  N_event, train_last_idx)]` (strictly after the confirmation bar; clipped to the
  TRAIN edge — never reads TEST or the holdout).
- Per bar, using real `High_i`/`Low_i`:
  - `fav_hit` iff (`rd = +1` ∧ `High_i ≥ fav_target`) or (`rd = −1` ∧ `Low_i ≤ fav_target`);
  - `adv_hit` iff (`rd = +1` ∧ `Low_i ≤ adv_target`) or (`rd = −1` ∧ `High_i ≥ adv_target`).
- The **first** bar with either hit resolves the event. **Same-bar double-touch
  (both fav and adv on bar `i`) ⇒ ADVERSE** (conservative; operator decision 3).
- **Outcome class per event:** `FAV`, `ADV`, `TIMECAP` (neither by `N_event`),
  or `DATA_CENSORED` (window truncated by `train_last_idx` before `N_event` and
  before any hit). `TIMECAP` and `DATA_CENSORED` are **unresolved**.

### Look-ahead / causality discipline (binding)

- Every barrier threshold (`fav_target`, `adv_target`, `N_event`) uses only the
  just-confirmed move and strictly-prior confirmed moves — all with
  `ConfirmTime ≤` the event `ConfirmTime`. No unconfirmed pivot, no future bar.
- Forward resolution uses only bars strictly after `ConfirmIdx`, fenced to
  `CloseTime ≤ train_end_ts`. Ordering/alignment by `CloseTime`, never bar index
  across views.
- The ZigZag substrate is the frozen `xen.zigzag` streaming state machine
  (ATR at bar N uses bars ≤ N; `ConfirmTime` strictly later than the pivot it
  confirms — an invariant already enforced and re-checked here).

### Instruments (17)

BTCUSD, EURUSD, USTEC, XAUUSD (core) + GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD,
NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225. **DE30 disclosure:**
truncated broker history (ends 2026-01-16); counts/rates derive from its own
realized timeline, not span-comparable. Cells are included only if EXP-048 marked
them READY/READY_FLAGGED.

### Time range

**TRAIN stratum only** — the first 70% of each instrument's first-70% analysis
slice (first 49% of the file), by the EXP-043/EXP-048 F01 file-order-prefix
convention (`train_end_ts` = last `CloseTime` of the first
`int(int(total_rows*0.7)*0.7)` file-order 1-minute rows). The nested analysis-set
**TEST stratum is not read** (preserved for a future EXP-027-analog event-level
calibration); the final-30% **global holdout** is never loaded, counted, or
touched (only Parquet metadata + the TRAIN prefix are read).

## Barrier-Construction Readiness (the HYP-002 "computable and causal" half)

Per cell, an invariant battery on the constructed barriers (mirrors the EXP-048
pattern, keyed by invariant name; all counts must be 0):

1. **Causality:** for every event, the reference move and all trailing-window
   moves have `ConfirmTime ≤` event `ConfirmTime`; `N_event ≥ 6`; no barrier field
   NaN/null; `M > 0`; warmup (< 5 trailing moves) events carry **no** barrier and
   are excluded (not silently capped).
2. **TRAIN fence:** every evaluated forward bar has `CloseTime ≤ train_end_ts`; no
   event references a bar beyond the TRAIN edge.
3. **Geometry well-formedness:** G1 `fav_distance > 0` always (since `M > 0`); G2
   degenerate (`fav_distance ≤ 0`) events flagged + excluded, count disclosed.
4. **Determinism:** a full second pass (re-aggregate, re-run ZigZag, re-build
   barriers, re-resolve) compares **frame-identical** to the first pass.

## Metric Denominators & Zero-Baseline (predeclared, before implementation)

- **Primary endpoint (per cell, per geometry):** `r = FAV / (FAV + ADV)` over
  **resolved** events. `resolved = FAV + ADV`; `TIMECAP` and `DATA_CENSORED` are
  excluded from the denominator. Symmetric 1:1 barriers ⇒ zero-edge null `r = 0.50`.
- **Zero-baseline / power (P12):** a cell with **`resolved < 30`** is
  **NOT_VIABLE-by-power** — non-reportable for routing, never an undefined or
  infinite ratio; `resolved = 0` ⇒ NOT_VIABLE-by-power, not `0/0`.
- **Disclosed secondaries (never the binding endpoint):**
  `fav_all = FAV / (all events with a defined barrier)` (counts time-cap and
  data-censored as non-favourable); **time-cap censoring fraction** =
  `TIMECAP / defined`; **data-truncation censoring fraction** =
  `DATA_CENSORED / defined`; warmup-excluded and (G2) degenerate-excluded counts.
- No metric is expressed as a percentage improvement over a zero baseline; the
  null is the explicit `r = 0.50` symmetric-barrier reference.

## Viability & Composition (P12 / P11 — mechanical readout, not the gate)

- **VIABLE cell (P12, primary geometry G1):** `r ≥ 0.55` **and** regime-clustered
  bootstrap **CI_low > 0.50** **and** `resolved ≥ 30`. (Bootstrap design — cluster
  unit, block length, reps, seed, one-sided 95% CI_low — is fixed in the analysis
  plan; intent: respect serial dependence of sequential alternating moves; fixed
  seed; `N_BOOT = 10_000`.)
- **Composition readout (P11):** count VIABLE cells and distinct instruments;
  family-level capture geometry is VIABLE iff **≥ 5 VIABLE cells over ≥ 3
  instruments** on the primary geometry. The secondary geometry's composition is
  reported in parallel, disclosed, non-binding.
- The experiment **emits** this readout; the **G1 routing adjudication**
  (PROCEED_TO_SCREEN vs CHARACTERISED_NOT_VIABLE, design §10) is checkpoint desk
  work, never self-declared by the experiment.

## Success / Failure / Inconclusive Criteria

- **Experiment verdict — CAPTURE_READINESS_DELIVERED:** the per-cell
  barrier-readiness map (causal + deterministic), the per-cell `r` / resolved /
  CI / VIABLE map (primary G1), the secondary G2 table, the disclosed-censoring
  table, and the P12/P11 composition readout are produced — whatever the
  viable/non-viable mix.
- **Evidence AGAINST (BARRIER_REFUTED — halts 014-A pending a fix):** a
  **systematic** construction defect, predeclared threshold: **non-determinism on
  any cell**, **or** a causality/TRAIN-fence invariant (battery items 1–2)
  violated on **≥ 3 instruments**. Capture geometry cannot be read on a broken
  barrier system.
- **Inconclusive (cell-level only):** a cell with `resolved < 30`
  (NOT_VIABLE-by-power); recorded, excluded from the P11 numerator, not a failure.
- The **routing outcome** (capture VIABLE vs CHARACTERISED_NOT_VIABLE) is **not**
  an experiment verdict — it is the §10 G1 adjudication on this experiment's
  readout.

## Complexity Budget

- Max statistical tests: **1** — the regime-clustered bootstrap CI for `r`
  (descriptive inference, frozen layer; applied to both geometries, one method).
- Max visualisations: **4** — (i) primary-geometry capture-rate `r` heatmap
  (17×6); (ii) VIABLE-status heatmap (VIABLE / r<0.55 / CI-spans-0.50 /
  NOT_VIABLE-by-power / excluded); (iii) resolved-event-count heatmap; (iv)
  unresolved-fraction (time-cap + data-truncation) heatmap. Secondary-geometry `r`
  and all censoring breakdowns go to CSV, not extra plots.
- Max new code modules: **1** under `python/src/xen/` — `capture_barriers.py`
  (causal triple-barrier touch resolution; conservative tie-break). Reuse
  `xen.zigzag`, `xen.bar_aggregator`, and EXP-047 `move_size.py` helpers unchanged
  (no generator edits). A per-cell capture-read helper may live in the experiment
  script.

## Data Requirements

Per instrument: lazy `pl.scan_parquet`; read total row count from metadata;
`analysis_rows = int(total_rows*0.7)`, `train_rows = int(analysis_rows*0.7)`;
collect only the first `train_rows` file-order 1-minute rows (F01 prefix; never
sort/collect the full file, never read TEST or holdout); assert chronological;
`train_end_ts` = last `CloseTime`. Aggregate each EXP-048-READY domain (5m strict;
others `min_coverage=0.90`); fence domain bars to `CloseTime ≤ train_end_ts`; run
`xen.zigzag`; build barriers (both geometries) and resolve forward; collect per-cell
records; second full pass for determinism. Outputs (`results/`):
`per_cell_capture.parquet`, `capture_rate_map.csv` (primary G1: r, CI_low, CI_high,
resolved, FAV/ADV, VIABLE), `capture_rate_secondary.csv` (G2 + degenerate counts),
`censoring_disclosure.csv` (time-cap / data-trunc / warmup-excluded fractions),
`composition_readout.json`, `run_metadata.json`; four bounded plots from the
collected per-cell summaries (no reloads). `tqdm` over the instrument/cell outer
loop; per-cell bounded memory (do not retain all domain frames). Expected runtime:
minutes (READY cells × 2 passes).

## Exclusions

- No HA harami detector, no `/CONFIRM` entry model, no combined harami-at-exhaustion
  event (EXP-050 / EXP-052 / 014-B). No strong-move filters, no `/BARCFG` analysis.
- No alternative barrier models (`/VPTARGET`, `/MAGTARGET`, `/ADV-EXTREME`,
  `/ADV-NONE`, `/THIRD-EVENT`, `/THIRD-TIME`, `/ATRMULT`, `/LOOKBACK` sweeps) — those
  are 014-B variants with their own scopes. Only the P1–P5 benchmark defaults here,
  with the two favourable geometries the operator authorized.
- No costs (gross throughout); no exit rule (exit-agnostic — barriers measure
  geometry, they are not a strategy exit); no net P&L, no expectancy screen.
- No returns from HA/Renko prices; every metric on real prices.
- No parameter tuned, selected, or frozen against any EXP-049 output; no
  cross-instrument or cross-domain pooling for the binding endpoint; no TEST or
  holdout contact; no candidate slot consumed; no TEST read.

## Suggested Direction (non-binding)

Mirror the EXP-048 orchestration (F01 loader, per-cell loop, determinism replay,
bounded plots). Implement `capture_barriers.py` as a bounded per-event Python loop
over a cell's confirmed moves (a few hundred per cell) — the first-touch scan is
genuinely sequential within an event window and mirrors EXP-047 `excursions`;
vectorize only safe loading/aggregation/summary. Build both geometries in one pass
(shared resolution scan, two target sets). Keep the binding routing input to G1;
carry G2 and all censoring as disclosed columns. Emit the P12/P11 readout; do not
adjudicate G1.
