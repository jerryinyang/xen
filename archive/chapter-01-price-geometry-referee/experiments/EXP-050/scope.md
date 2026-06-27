# Experiment: EXP-050 — Phase 014-A Harami-in-Context: Position-in-Move of HA Harami Signals vs Predeclared Baselines (ATR-ZigZag, 99 Cells)

**Phase:** 014 (HA-harami substrate & capture geometry; checkpoint
`2026-06-14-014-ha-harami-substrate-and-capture`, G0 PASS 2026-06-14) ·
**Sub-phase:** 014-A · **HYP:** HYP-003 · **Registry:**
`CF-HA-HARAMI-001/HYP-003` (multiplicity-registry Phase 014 batch) ·
**Candidate slots:** 0 (characterization) · **TEST reads:** 0 (TRAIN-only; no
ledger entry; nested analysis-set TEST stratum unread).

**Analog:** EXP-048 102-cell substrate/loader pattern (F01 prefix loader, per-cell
loop, determinism replay, bounded plots). **Reuse (frozen, unchanged):**
`xen.zigzag.generate_zigzag` (P1 substrate), `xen.ha_harami.detect_ha_harami`
(core detector), `xen.heiken_ashi_generator.generate_heiken_ashi`,
`xen.bar_aggregator.aggregate_ohlc`,
`xen.referee_calibration.ma_crossover_positions` (P13 baseline-2 segmentation).
**New module (≤1):** `python/src/xen/move_position.py` — causal/descriptive
position-in-move assignment (pivot-tiling) reusable across 014-B; if the
developer/analyst judge it not yet reusable it may instead live as an
experiment-local helper under `code/`.

**Gating precondition (satisfied):** EXP-050 consumes the per-cell readiness map
from **EXP-048 (HYP-001)**, which reached **READINESS_DELIVERED** with **audit
PASS** and post-experiment **APPROVE** (closed). Cell membership = EXP-048
**READY ∪ READY_FLAGGED** cells only (**99 cells**: 86 READY + 13 READY_FLAGGED);
the 3 **COVERAGE_EXCLUDED** cells (US500-4h, JP225-2h, JP225-4h) are excluded with
record. EXP-050 is **independent of EXP-049** (HYP-002): it uses no 3-barrier
capture geometry, so it does not wait on EXP-049 closure.

## Operator Framing Decisions (recorded 2026-06-15, pre-data-contact)

Two interpretive choices not fully pinned by D0 were put to the operator before
this scope was written; both are pre-data-contact and tune nothing against
outcomes:

1. **Binding baseline for P9 cluster-materiality = the RANDOM-timestamp baseline
   (P13.1).** The random matched-count baseline is the binding null for "near
   exhaustion is more frequent than chance" (the ≥10 pp rule). The MA(20,50)
   alternative-segmentation baseline (P13.2) is reported **in parallel as a
   disclosed robustness / artifact-attribution comparison** (does the clustering
   survive a different move segmentation?), **non-binding**.
2. **Containing-move assignment = PIVOT TILING.** A harami at time `t` belongs to
   the confirmed move with `StartTime < t ≤ EndTime` (pivot) — the in-progress
   move whose terminal pivot is the next pivot. Position lies in ≈(0, 1];
   near-exhaustion (≥ 0.67) means the harami sits in the final third before that
   move's own terminal extreme. This matches the "harami exhausting the move in
   progress" thesis.

**Defaults adopted (no separate confirmation; recorded here):** signal reference
price = `RealClose` at the harami's `HA0Time` (real price); **all** detected
haramis pooled with **no `/BARCFG` filter**; random baseline **stratified by
containing-move direction** with a **fixed seed**; position **primary by price
excursion**, **duration-fraction position as a disclosed secondary view** (per P9).

## Hypothesis

Exploratory harami-in-context question (gross, descriptive, no market-edge
*screen*): for every EXP-048-READY cell (17 instruments × {5m, 15m, 30m, 1h, 2h,
4h}), each HA harami signal can be deterministically and look-ahead-safely placed
within its containing confirmed ZigZag move, and its **position-in-move by price
excursion** is measured on **real prices**; the per-cell **final-third rate**
(fraction of haramis at position ≥ 0.67, P9 "near exhaustion") is compared against
the **random matched-count baseline** (P13.1, binding) and the **MA(20,50)
alternative-segmentation baseline** (P13.2, disclosed). The P9 cluster-materiality
rule (observed final-third rate ≥ random baseline rate + 10 pp) and the P11
composition rule (≥ 5 cells over ≥ 3 instruments) are applied mechanically as a
**readout**, not a self-adjudicated gate.

## Question

For each EXP-048-READY cell, taking every detected HA harami as one event:

a. Can each harami be assigned **deterministically** to exactly one containing
   confirmed ZigZag move under pivot tiling (`StartTime < HA0Time ≤ EndTime`), and
   its position-in-move `pos = (RealClose − StartPrice) / (EndPrice − StartPrice)`
   computed on real prices, using only confirmed-move boundaries (descriptive
   completed-move grouping, P9) — with a deterministic second-pass replay?
b. What is the per-cell **final-third rate** `FT = P(pos ≥ 0.67)` over assigned
   haramis, and the full position-in-move distribution (median, IQR)?
c. What is the **random matched-count baseline** final-third rate `FT_rand`
   (direction-stratified, fixed-seed resample of in-move bars) and the
   gap `Δ = FT − FT_rand` with its resample CI?
d. Which cells are **materially clustered near exhaustion** by P9
   (`Δ ≥ 0.10` ∧ assigned haramis ≥ 30), and does the family meet P11 (≥ 5 cells
   over ≥ 3 instruments) on the binding random baseline?
e. Disclosed secondaries: the **MA(20,50) alternative-segmentation** final-third
   rate `FT_MA` and gap `Δ_MA = FT − FT_MA`; the **duration-fraction** position
   final-third rate; and the **excluded-event fractions** (ZigZag warmup /
   unconfirmed-forming-tail / degenerate-move).

## Scope Boundaries

### Data Views

- 1-minute time bars (`data/timebars/timebars_<SYMBOL>_*.parquet`), aggregated to
  5m, 15m, 30m, 1h, 2h, 4h via `xen.bar_aggregator.aggregate_ohlc`. **5m strict
  coverage** (`min_coverage=None`); **15m/30m/1h/2h/4h at `min_coverage=0.90`** —
  identical to EXP-048/EXP-049/VAL-004.
- **ZigZag substrate and position metric are computed on real domain OHLC.** The
  **harami detector runs on Heiken Ashi candles** (`generate_heiken_ashi` of the
  same real domain bars) — detection only. The HA frame's `RealClose` column
  supplies the signal price. **No metric uses HA prices.** No Line Break / Renko
  views.

### Harami Signal Events (detected on HA candles)

- Generate HA candles from each cell's real domain bars (TRAIN-only), run
  `xen.ha_harami.detect_ha_harami` (frozen). Each emitted row is one harami event
  at `HA0Time` (the latest HA candle's `CloseTime`).
- **Signal price** `P_sig` = `RealClose` at `HA0Time` (real price, joined from the
  HA frame on `CloseTime == HA0Time`).
- **No `/BARCFG` filter, no strong-move filter, no `/CONFIRM` entry model.** All
  detected haramis are pooled (the unfiltered base signal, P6 OFF). `ReducedOK`
  is checked equal to the original predicate on every row (detector self-check).

### ZigZag Move Segmentation (primary) — confirmed moves, real bars

- Run `xen.zigzag.generate_zigzag(bars, atr_period=14, atr_mult=1.0)` (P1, frozen)
  on each cell's real domain bars (TRAIN-only). Each confirmed move carries
  `StartTime`, `EndTime` (pivot), `ConfirmTime`, `Direction d`, `StartPrice S`,
  `EndPrice E`.
- **Pivot tiling.** Confirmed moves tile time by their pivots: move `i` covers
  `(StartTime_i, EndTime_i]`, and `EndTime_i = StartTime_{i+1}`. A harami at
  `HA0Time = t` is assigned to the unique move with `StartTime_i < t ≤ EndTime_i`.
- **Position-in-move (primary, price excursion):**
  `pos = (P_sig − S_i) / (E_i − S_i)`. The denominator `(E_i − S_i)` carries the
  move's sign, so `pos` is direction-signed for both up- and down-moves; **a
  degenerate move `E_i = S_i` is excluded** with record (mirrors EXP-049 `M > 0`).
- **Near-exhaustion (P9):** `pos ≥ 0.67` (final third). **Duration-fraction
  position** (`(barindex(t) − barindex(StartTime_i)) / (barindex(EndTime_i) −
  barindex(StartTime_i))`) is computed as a **disclosed secondary** view only.
- **Excluded events (disclosed, not defaulted):** a harami whose `t` precedes the
  first confirmed move's `StartTime` (ZigZag warmup) or follows the **last**
  confirmed move's `EndTime` (an unconfirmed forming tail with no completed
  containing move) has **no** defined position and is excluded with a per-cell
  count + fraction.

### Baseline 1 — Random matched-count timestamps (P13.1, BINDING)

- The eligible population = all real domain bars whose `CloseTime` falls strictly
  inside a confirmed, non-degenerate move under pivot tiling (i.e., bars that have
  a defined `pos`), labelled by their containing move's direction `d`.
- **Direction-stratified, matched-count draw (fixed seed):** for each direction,
  draw the same number of eligible bars as the number of **assigned** haramis in
  that direction; score each draw's `pos` and final-third indicator through the
  identical metric. Repeat for `R` fixed-seed resamples to obtain the baseline
  final-third-rate distribution `FT_rand` (point = mean across draws) and a
  resample CI on the gap `Δ = FT − FT_rand`. (`R`, the resampling unit/CI form,
  and serial-dependence handling are fixed in the analysis plan; fixed seed.)
- **Binding null:** symmetric "harami timing is exchangeable with random in-move
  timing of matched direction." Materiality threshold is the P9 ≥ 10 pp gap.

### Baseline 2 — MA(20,50) alternative segmentation (P13.2, DISCLOSED)

- Compute `xen.referee_calibration.ma_crossover_positions(close, fast=20,
  slow=50)` on each cell's real domain closes (TRAIN-only). A **regime/move** is a
  maximal contiguous run of constant non-zero position; `move_start`/`move_end`
  prices = the `Close` at the regime's first/last bar, direction = the regime's
  sign. Flat (position 0) warmup bars carry no regime.
- **Score the SAME harami events** under this segmentation: assign each harami to
  the MA regime whose `[start, end]` time interval contains `HA0Time`, compute
  `pos` identically, and report `FT_MA` and `Δ_MA = FT − FT_MA`. Haramis in a flat
  region or degenerate MA regime are excluded with record. This is **disclosed,
  non-binding** — it tests whether near-exhaustion clustering is a property of
  harami timing rather than an artifact of ZigZag segmentation.

### Look-ahead / Causality Discipline (binding)

- **Detection and segmentation are causal.** The harami detector uses only the
  current + immediately prior HA candle (frozen one-row-shift form). The ZigZag is
  the frozen streaming state machine (ATR at bar `N` uses bars ≤ `N`; `ConfirmTime`
  strictly later than the pivot it confirms). MA-crossover positions are known at
  bar `t`.
- **The position-in-move metric is a predeclared, non-tradable descriptive
  characterization** (P9's explicit "completed-move grouping" allowance): it uses
  the confirmed move's terminal pivot `E_i`, which is future information relative
  to a mid-move harami. This is permitted **only** because HYP-003 characterizes
  **completed** moves and **no trading, signal, capture, or P&L decision uses
  `pos` or the unconfirmed pivot.** The metric never enters a live signal,
  entry/exit rule, or return computation; the same allowance applies to the random
  baseline's in-move draws and the MA-segmentation scoring. This carve-out is
  bounded to the descriptive position readout and is disclosed in every result.
- **TRAIN fence:** every harami `HA0Time`, every move `ConfirmTime`, and every
  eligible in-move bar has `CloseTime ≤ train_end_ts`; no row beyond the TRAIN edge
  is read. Ordering/alignment by `CloseTime`, never bar index across views.

### Instruments (17)

BTCUSD, EURUSD, USTEC, XAUUSD (core) + GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD,
NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225. **DE30 disclosure:**
truncated broker history (ends 2026-01-16); counts/rates derive from its own
realized timeline, not span-comparable. Cells included only if EXP-048 marked them
READY/READY_FLAGGED (99 cells; 3 COVERAGE_EXCLUDED dropped).

### Time range

**TRAIN stratum only** — the first 70% of each instrument's first-70% analysis
slice (first 49% of the file), by the EXP-043/EXP-048 F01 file-order-prefix
convention (`train_end_ts` = last `CloseTime` of the first
`int(int(total_rows*0.7)*0.7)` file-order 1-minute rows). The nested analysis-set
**TEST stratum is not read**; the final-30% **global holdout** is never loaded,
counted, or touched (only Parquet metadata + the TRAIN prefix are read).

## Readiness / Invariant Battery (the HYP-003 "computable and causal" half)

Per cell, an invariant battery (mirrors EXP-048/EXP-049, keyed by invariant name;
all counts must be 0 unless noted as disclosed):

1. **Detector self-check:** `ReducedOK == original-harami-predicate` on every
   emitted harami row (HA-generator/detector consistency).
2. **Assignment well-formedness:** every **assigned** harami maps to exactly one
   containing confirmed move under pivot tiling; `pos` is finite; the containing
   move is non-degenerate (`E_i ≠ S_i`). Warmup / forming-tail / degenerate
   exclusions are counted and disclosed (not silently defaulted).
3. **Causality / TRAIN fence:** every harami `HA0Time`, move `ConfirmTime`, and
   eligible in-move bar has `CloseTime ≤ train_end_ts`; the position metric
   references only confirmed-move boundaries (descriptive allowance, declared); no
   future-bar read beyond the metric's predeclared completed-move grouping.
4. **Determinism:** a full second pass (re-aggregate, re-HA, re-detect, re-ZigZag,
   re-assign, re-resample baselines with the same fixed seed) compares
   **frame-identical** to the first pass.

## Metric Denominators & Zero-Baseline (predeclared, before implementation)

- **Primary endpoint (per cell):** `FT = (#haramis with pos ≥ 0.67) / (#assigned
  haramis)`. Denominator = **assigned** haramis (defined containing completed move,
  non-degenerate); warmup/forming-tail/degenerate haramis are excluded from the
  denominator and disclosed separately.
- **Random baseline:** `FT_rand` (direction-matched resample), gap `Δ = FT −
  FT_rand`. **Materially clustered (P9, binding):** `Δ ≥ 0.10` (10 pp) **and**
  `#assigned haramis ≥ 30` (power floor).
- **Zero-baseline / power:** a cell with `#assigned haramis < 30` is
  **NOT_REPORTABLE-by-power** — non-reportable for the P11 numerator, never an
  undefined or infinite ratio; `#assigned = 0` ⇒ NOT_REPORTABLE-by-power, not
  `0/0`.
- **Disclosed secondaries (never the binding endpoint):** `FT_MA` and `Δ_MA`
  (MA-segmentation); the duration-fraction final-third rate; the
  warmup/forming-tail/degenerate excluded fractions; the position distribution
  summary (median, IQR). No metric is expressed as a percentage improvement over a
  zero baseline; the null is the explicit random-timing reference rate.

## Viability & Composition (P9 / P11 — mechanical readout, not the gate)

- **Materially-clustered cell (P9, binding random baseline):** `Δ ≥ 0.10` **and**
  `#assigned ≥ 30`. A fixed-seed resample CI on `Δ` is reported as **disclosed
  support** (not an added binding threshold beyond D0 P9).
- **Composition readout (P11):** count materially-clustered cells and distinct
  instruments; the family-level "harami clusters near exhaustion" claim holds iff
  **≥ 5 cells over ≥ 3 instruments** on the binding random baseline. The
  MA-segmentation composition is reported in parallel, disclosed, non-binding.
- The experiment **emits** this readout; the 014-A **G1 adjudication** (informing
  combined-event registration, design §10) is checkpoint desk work, never
  self-declared by the experiment.

## Success / Failure / Inconclusive Criteria

- **Experiment verdict — CONTEXT_CHARACTERISATION_DELIVERED:** the per-cell
  position-in-move distribution, the `FT` / assigned-count map, the random-baseline
  `Δ` / materiality map (binding), the MA-segmentation disclosed comparison, the
  excluded-fraction disclosure, and the P9/P11 composition readout are produced —
  whatever the clustered/not-clustered mix.
- **Evidence AGAINST (CONTEXT_REFUTED — halts 014-A pending a fix):** a
  **systematic** construction defect, predeclared threshold: **non-determinism on
  any cell**, **or** a causality/TRAIN-fence/assignment invariant (battery items
  1–3) violated on **≥ 3 instruments**. Harami-in-context cannot be read on a
  broken assignment.
- **Inconclusive (cell-level only):** a cell with `#assigned < 30`
  (NOT_REPORTABLE-by-power); recorded, excluded from the P11 numerator, not a
  failure.
- The **clustering outcome** (clustered vs not) is **not** an experiment verdict —
  it is the §10 G1 adjudication on this experiment's readout.

## Complexity Budget

- **Max statistical tests: 1** — the fixed-seed resampling procedure for the
  random baseline final-third rate distribution + the CI on the gap `Δ`
  (descriptive inference; one method). The MA-segmentation comparison reuses the
  identical position metric (a descriptive rate gap, no separate test).
- **Max visualisations: 4** — (i) per-cell observed final-third-rate `FT` heatmap
  (17×6); (ii) `Δ = FT − FT_rand` gap heatmap with the ≥ 10 pp materiality
  threshold highlighted; (iii) a bounded position-in-move distribution view
  (haramis vs random baseline, pooled or small-multiple — bounded inputs from the
  analysis pass, no reloads); (iv) assigned-harami-count / excluded-fraction
  heatmap. `FT_MA`, `Δ_MA`, duration-fraction secondary, and all censoring
  breakdowns go to CSV.
- **Max new code modules: 1** under `python/src/xen/` — `move_position.py` (causal
  pivot-tiling assignment + price-excursion position; reusable in 014-B), **or** an
  experiment-local helper under `code/` if not yet reusable. Reuse `xen.zigzag`,
  `xen.ha_harami`, `xen.heiken_ashi_generator`, `xen.bar_aggregator`,
  `xen.referee_calibration.ma_crossover_positions` unchanged (no edits).

## Data Requirements

Per instrument: lazy `pl.scan_parquet`; read total row count from metadata;
`analysis_rows = int(total_rows*0.7)`, `train_rows = int(analysis_rows*0.7)`;
collect only the first `train_rows` file-order 1-minute rows (F01 prefix; never
sort/collect the full file, never read TEST or holdout); assert chronological;
`train_end_ts` = last `CloseTime`. Aggregate each EXP-048-READY domain (5m strict;
others `min_coverage=0.90`); fence domain bars to `CloseTime ≤ train_end_ts`;
generate HA candles + detect haramis; run `xen.zigzag`; assign haramis to moves
(pivot tiling) and compute `pos`; resample the random baseline (fixed seed);
score the MA-segmentation baseline; collect per-cell records; second full pass for
determinism. Outputs (`results/`): `per_cell_context.parquet`,
`final_third_rate_map.csv` (FT, FT_rand, Δ, CI, assigned, clustered flag),
`secondary_disclosure.csv` (FT_MA, Δ_MA, duration-fraction FT, excluded fractions,
position median/IQR), `composition_readout.json`, `run_metadata.json`; four bounded
plots from the collected per-cell summaries (no reloads). `tqdm` over the
instrument/cell outer loop; per-cell bounded memory (do not retain all domain
frames). Expected runtime: minutes (READY cells × 2 passes).

## Exclusions

- No 3-barrier capture geometry (EXP-049 / HYP-002), no `/CONFIRM` entry model, no
  combined harami-at-exhaustion *capture* event (EXP-052 / 014-B). No strong-move
  filters (`/STRONG-STAT`, `/STRONG-HA`; EXP-051), no `/BARCFG` isolation/filtering
  (all haramis pooled). No `/ATRMULT`, `/LOOKBACK`, or any barrier-model variant.
- No costs (gross throughout); no exit rule; no net P&L, expectancy, or return
  computation of any kind. The position-in-move metric is **non-tradable
  descriptive** (uses the future pivot under the predeclared completed-move
  allowance) and feeds **no** strategy, signal, or P&L.
- No returns or prices from HA/Renko construction values; the signal price is real
  (`RealClose`) and all move boundaries are real-bar pivots.
- No parameter tuned, selected, or frozen against any EXP-050 output; no
  cross-instrument or cross-domain pooling for the binding endpoint; no TEST or
  holdout contact; no candidate slot consumed; no TEST read.

## Suggested Direction (non-binding)

Mirror the EXP-048/EXP-049 orchestration (F01 loader, per-cell loop, determinism
replay, bounded plots). Implement the pivot-tiling assignment as a vectorized
interval join (`HA0Time` into `(StartTime, EndTime]`) — safe because the moves are
a precomputed completed segmentation, not a sequential causal scan. Keep the
ZigZag/HA/harami generation calls frozen and unedited. Build the random baseline as
a direction-stratified fixed-seed resample over the eligible in-move bar index set;
build the MA-segmentation baseline by re-scoring the same harami `HA0Time` set
against MA-regime intervals. Emit the P9/P11 readout; do **not** self-adjudicate
G1.
