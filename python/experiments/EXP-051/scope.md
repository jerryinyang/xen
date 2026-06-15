# Experiment: EXP-051 — Phase 014-A Strong-Move Filter Characterisation: Do `/STRONG-STAT` and `/STRONG-HA` Identify Materially Different Confirmed-Move Populations (ATR-ZigZag, 99 Cells)

**Phase:** 014 (HA-harami substrate & capture geometry; checkpoint
`2026-06-14-014-ha-harami-substrate-and-capture`, G0 PASS 2026-06-14) ·
**Sub-phase:** 014-A · **HYP:** HYP-004 · **Registry:**
`CF-HA-HARAMI-001/HYP-004`, variants `CF-HA-HARAMI-001/STRONG-STAT` and
`CF-HA-HARAMI-001/STRONG-HA` (multiplicity-registry Phase 014 batch) ·
**Candidate slots:** 0 (characterization) · **TEST reads:** 0 (TRAIN-only; no
ledger entry; nested analysis-set TEST stratum unread).

**Analog:** EXP-050 99-cell substrate/loader pattern (F01 prefix loader, per-cell
loop, determinism replay, bounded plots). **Reuse (frozen, unchanged):**
`xen.zigzag.generate_zigzag` (P1 substrate, confirmed moves),
`xen.heiken_ashi_generator.generate_heiken_ashi` (HA candles for `/STRONG-HA`
detection only), `xen.ha_harami.detect_ha_harami` (used **only** for the disclosed
harami-overlap secondary), `xen.bar_aggregator.aggregate_ohlc`. **New module
(≤1):** `python/src/xen/strong_move.py` — causal `/STRONG-STAT` rolling-window
move filter and `/STRONG-HA` impulse-run detector + run→move mapping (reusable in
014-B); if the developer/analyst judge it not yet reusable it may instead live as
an experiment-local helper under `code/`.

**Gating precondition (satisfied):** EXP-051 consumes the per-cell readiness map
from **EXP-048 (HYP-001)**, which reached **READINESS_DELIVERED** with **audit
PASS** and post-experiment **APPROVE** (closed). Cell membership = EXP-048
**READY ∪ READY_FLAGGED** cells only (**99 cells**: 86 READY + 13 READY_FLAGGED);
the 3 **COVERAGE_EXCLUDED** cells (US500-4h, JP225-2h, JP225-4h) are excluded with
record. EXP-051 is **independent of EXP-049 / EXP-050**: it uses no 3-barrier
capture geometry and no position-in-move metric, so it waits on neither.

## Operator Framing Decisions (recorded 2026-06-15, pre-data-contact)

Two interpretive choices not fully pinned by D0 were put to the operator before
this scope was written; both are pre-data-contact and tune nothing against
outcomes:

1. **`/STRONG-HA` run→move mapping = run BOTH forms, primary + sensitivity.**
   `/STRONG-STAT` is natively a move filter (magnitude vs trailing-window
   percentile). `/STRONG-HA` is a run of `X` consecutive strong HA impulse bars
   and must be mapped to a retained-move population to be P10-adjudicable. The
   experiment computes the full P10 endpoint under **two** parallel mappings:
   - **PRIMARY (binding for P10/P11):** a confirmed move `M` (direction `d_M`) is
     retained iff there exists a qualifying impulse run whose direction equals
     `d_M`, with all `X` run bars' `CloseTime ∈ (StartTime_M, EndTime_M]`.
   - **SENSITIVITY (disclosed, non-binding):** identical, but the direction-match
     requirement is dropped (a qualifying run of *either* direction inside the
     span retains the move). This isolates the contribution of the
     direction-match constraint.
2. **Harami-overlap disclosed secondary = INCLUDED.** A disclosed, non-binding
   CSV reports the overlap between detected HA haramis and each filter's retained
   moves (fraction of retained strong moves containing ≥1 harami; fraction of
   haramis sitting on a retained move). It reuses the frozen detector already in
   the pipeline and directly informs 014-B combined-event registration. It adds
   **no** binding claim; the P10/P11 endpoint is purely about move populations.

**Defaults adopted (no separate confirmation; recorded here, all P7/P8/P4-analog,
nothing tuned):**

- **Move magnitude** `mag_M = |EndPrice_M − StartPrice_M|` — absolute price
  excursion of the confirmed move on **real prices** (P7). Scale-free *within*
  instrument; no cross-instrument or cross-domain pooling.
- **Rolling window** = the most recent `min(20, available)` confirmed moves /
  HA bars **strictly prior** to the move/bar under test (causal). **Warmup
  floor = 5** (P4-analog): a move with `< 5` trailing confirmed moves (for
  `/STRONG-STAT`) or an HA bar with `< 5` prior HA bars (for the `/STRONG-HA`
  median) has **no defined threshold** → `NO_DECISION`, excluded from both
  numerator and denominator and disclosed; never silently defaulted.
- **`/STRONG-STAT` reports both registered forms** (P7): the **p75** percentile
  threshold is **binding**; the **median + 1×MAD** form is reported in parallel
  as a disclosed comparison. **No post-result selection** between forms.
- **Binding population = all confirmed ZigZag moves** with a defined filter
  decision per cell (the P10 "unfiltered" set); haramis are not required for the
  binding endpoint.
- **Power floor = 30** moves with a defined filter decision per cell
  (NOT_REPORTABLE-by-power below; mirrors EXP-049/EXP-050).
- **Degenerate move** (`EndPrice_M = StartPrice_M`, `mag_M = 0`) is excluded with
  record (mirrors EXP-049/EXP-050 `M > 0`).
- **Signal price for the overlap secondary** = `RealClose` at the harami's
  `HA0Time`; haramis assigned to moves by the same pivot-tiling
  (`StartTime < HA0Time ≤ EndTime`) as EXP-050. No HA price enters any metric.

## Hypothesis

Exploratory strong-move-filter characterisation (gross, descriptive, no
market-edge *screen*): for every EXP-048-READY cell (17 instruments × {5m, 15m,
30m, 1h, 2h, 4h}), each of the two strong-move filters can be computed
deterministically and look-ahead-safely (filter *decisions* use only confirmed
prior context), and the **median magnitude** and **retained fraction** of the
confirmed-move subset each filter selects are measured on **real prices** and
compared against the unfiltered confirmed-move population of the same cell. The
P10 "materially different" rule (filtered median magnitude `≥ 1.5×` unfiltered
median **and** retained fraction `∈ [0.10, 0.50]`, both required) and the P11
composition rule (`≥ 5` cells over `≥ 3` instruments) are applied mechanically as
a **readout**, not a self-adjudicated gate, per filter independently.

## Question

For each EXP-048-READY cell, taking every confirmed ZigZag move as one unit:

a. Can each confirmed move be assigned a **deterministic, causal** filter
   decision under `/STRONG-STAT` (`mag_M ≥` trailing-window p75, primary; `≥`
   median + 1×MAD, disclosed) and under `/STRONG-HA` (the move's span contains a
   qualifying same-direction impulse run, primary; any-direction, sensitivity) —
   with a deterministic second-pass replay?
b. What is each filter's per-cell **retained fraction**
   `f = #retained / #defined-decision moves` and the **median move magnitude**
   of the retained set vs the unfiltered (all defined-decision) set?
c. What is the per-cell **median-magnitude ratio**
   `ρ = median(mag | retained) / median(mag | all defined)` and is the cell
   **materially different** by P10 (`ρ ≥ 1.5` **and** `f ∈ [0.10, 0.50]`)?
d. Which cells are materially different per filter, and does each filter meet P11
   (`≥ 5` cells over `≥ 3` instruments)? Is the result **cross-cell consistent**
   (distribution of `ρ` and `f` across cells)?
e. Disclosed secondaries: the `/STRONG-STAT` **median + 1×MAD** form; the
   `/STRONG-HA` **any-direction** sensitivity mapping; the **harami↔retained-move
   overlap**; the **excluded fractions** (warmup `NO_DECISION` / degenerate); and
   the retained/unfiltered magnitude **distribution summaries** (median, IQR).

## Scope Boundaries

### Data Views

- 1-minute time bars (`data/timebars/timebars_<SYMBOL>_*.parquet`), aggregated to
  5m, 15m, 30m, 1h, 2h, 4h via `xen.bar_aggregator.aggregate_ohlc`. **5m strict
  coverage** (`min_coverage=None`); **15m/30m/1h/2h/4h at `min_coverage=0.90`** —
  identical to EXP-048/EXP-049/EXP-050/VAL-004.
- **The ZigZag substrate and all magnitude metrics are computed on real domain
  OHLC.** The **`/STRONG-HA` impulse-run detector runs on Heiken Ashi candles**
  (`generate_heiken_ashi` of the same real domain bars) — detection only;
  retained-move *magnitudes* are real-price excursions. The harami detector
  (overlap secondary only) also runs on HA candles. **No metric uses HA prices.**
  No Line Break / Renko views.

### Confirmed-Move Substrate (real bars) — the population under test

- Run `xen.zigzag.generate_zigzag(bars, atr_period=14, atr_mult=1.0)` (P1, frozen)
  on each cell's real domain bars (TRAIN-only). Each confirmed move carries
  `StartTime`, `EndTime` (pivot), `ConfirmTime`, `Direction d`, `StartPrice S`,
  `EndPrice E`. **Magnitude** `mag = |E − S|` (real-price excursion). A degenerate
  move `E = S` is excluded with record.
- **Descriptive completed-move allowance (binding, declared).** `mag` references
  the move's terminal pivot `E`, future information relative to a mid-move bar.
  This is permitted **only** because HYP-004 characterises **completed** moves'
  magnitudes — *no trading, signal, capture, or P&L decision uses `mag`, the
  retained-move set, or any unconfirmed pivot.* The filter *thresholds* are strictly
  causal (trailing confirmed-prior context only); the move being scored is a
  completed move. This carve-out is the same family allowance EXP-050 used and is
  disclosed in every result.

### `/STRONG-STAT` filter (P7) — primary p75, disclosed median+1×MAD

- For each confirmed move `M`, build the rolling window = magnitudes of the
  `min(20, available)` confirmed moves with `ConfirmTime < ConfirmTime_M`
  (strictly prior, causal). Warmup `< 5` trailing → `NO_DECISION` (excluded,
  disclosed).
- **Primary (binding):** `M` retained iff `mag_M ≥ p75` of the window magnitudes.
- **Disclosed alternative form:** `M` retained iff `mag_M ≥ median + 1×MAD` of the
  window (MAD = median absolute deviation about the window median). Reported in
  parallel; **never** selected against results.

### `/STRONG-HA` filter (P8) — primary same-direction, disclosed any-direction

- Generate HA candles from each cell's real domain bars (TRAIN-only). For each HA
  bar `b`: real body `= |HAClose_b − HAOpen_b|`, direction `+1` if
  `HAClose_b ≥ HAOpen_b` else `−1`. Trailing-window median HA body = causal median
  of the `min(20, available)` prior HA bars' bodies; warmup `< 5` prior HA bars →
  the bar cannot qualify (disclosed).
- A HA bar `b` **qualifies** iff (a) its real body `≥` its trailing median HA
  body, **and** (b) it has **no opposing wick**: bullish ⇒ `HALow == HAOpen`
  (no lower wick); bearish ⇒ `HAHigh == HAOpen` (no upper wick). (Equalities are
  exact in float for HA candles — `HALow = min(Low, HAOpen, HAClose)` collapses to
  `HAOpen` precisely when there is no lower wick.)
- A **qualifying impulse run** = `X = 3` consecutive HA bars, all the same
  direction, each qualifying.
- **Run → move retention (PRIMARY, binding):** move `M` (direction `d_M`) retained
  iff `∃` a qualifying run of direction `= d_M` with all 3 run bars'
  `CloseTime ∈ (StartTime_M, EndTime_M]`.
- **Run → move retention (SENSITIVITY, disclosed):** identical but the run may be
  of *either* direction (drops `direction == d_M`). Isolates the direction-match
  contribution.

### Harami-overlap secondary (P6-OFF base signal; DISCLOSED, non-binding)

- Run `xen.ha_harami.detect_ha_harami` (frozen) on the same HA candles; assign each
  harami `HA0Time` to its containing confirmed move by pivot tiling
  (`StartTime < HA0Time ≤ EndTime`), identical to EXP-050. Report, per cell and per
  filter (primary mappings): the fraction of retained strong moves that contain
  `≥ 1` harami, and the fraction of assigned haramis that sit on a retained move.
  **Disclosed, non-binding**; informs 014-B combined-event registration only.

### Look-ahead / Causality Discipline (binding)

- **Filter decisions are causal.** `/STRONG-STAT` thresholds use only confirmed
  moves strictly prior to `M`. `/STRONG-HA` runs are causal by construction (each
  bar's body/wick and trailing median use bars `≤` that bar). The ZigZag is the
  frozen streaming state machine (ATR at bar `N` uses bars `≤ N`; `ConfirmTime`
  strictly later than the pivot it confirms).
- **The retained-move *magnitude* is a predeclared, non-tradable descriptive
  characterisation** (completed-move allowance above): it uses the confirmed
  pivot `E`. The metric never enters a live signal, entry/exit rule, capture, or
  return computation; the overlap secondary's harami assignment uses the same
  bounded allowance EXP-050 declared.
- **TRAIN fence:** every move `ConfirmTime`, every HA bar `CloseTime`, and every
  harami `HA0Time` has `CloseTime ≤ train_end_ts`; no row beyond the TRAIN edge is
  read. Ordering/alignment by `CloseTime`, never bar index across views.

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

## Readiness / Invariant Battery

Per cell, an invariant battery (mirrors EXP-048/049/050, keyed by invariant name;
all counts must be 0 unless noted as disclosed):

1. **Filter well-formedness:** every confirmed move with `≥ 5` trailing confirmed
   moves receives a defined `/STRONG-STAT` decision (both forms); every confirmed
   move receives a defined `/STRONG-HA` decision (run present/absent, both
   mappings) once past HA warmup. `NO_DECISION` (warmup) and `DEGENERATE` counts
   are disclosed, not silently defaulted. Retained ⊆ defined-decision moves.
2. **Magnitude validity:** `mag_M = |E_M − S_M|` is finite and `> 0` on every
   defined-decision move (degenerate moves excluded and counted).
3. **`/STRONG-HA` detector self-consistency:** every qualifying HA bar satisfies
   both the body and the no-opposing-wick predicate; every emitted run is exactly
   3 consecutive same-direction qualifying bars; primary retained moves ⊆
   sensitivity retained moves (direction-match is a strict sub-condition).
4. **Causality / TRAIN fence:** every move `ConfirmTime`, HA bar `CloseTime`, and
   harami `HA0Time` has `CloseTime ≤ train_end_ts`; filter thresholds reference
   only prior-confirmed context; no future-bar read beyond the predeclared
   completed-move magnitude allowance.
5. **Determinism:** a full second pass (re-aggregate, re-HA, re-detect runs,
   re-ZigZag, re-filter, re-map, re-assign overlap) compares **frame-identical**
   to the first pass.

## Metric Denominators & Zero-Baseline (predeclared, before implementation)

- **Per-cell denominator** = `#defined-decision moves` (non-degenerate confirmed
  moves with a defined filter decision). Warmup `NO_DECISION` and degenerate moves
  are excluded from both numerator and denominator and disclosed separately.
- **Retained fraction:** `f = #retained / #defined-decision`. **Median-magnitude
  ratio:** `ρ = median(mag | retained) / median(mag | all defined-decision)`.
- **Materially different (P10, binding):** `ρ ≥ 1.5` **and** `f ∈ [0.10, 0.50]`,
  both required, on the binding form (`/STRONG-STAT` p75; `/STRONG-HA` primary
  same-direction).
- **Zero-baseline / degenerate handling:** `#retained = 0` ⇒ `ρ` undefined
  (reported null), `f = 0 < 0.10` ⇒ not materially different (never `0/0` or
  infinite). A cell with `#defined-decision < 30` is **NOT_REPORTABLE-by-power** —
  excluded from the P11 numerator, never an undefined ratio. The unfiltered median
  is the explicit denominator/reference; no metric is expressed as a percentage
  improvement over a zero baseline.
- **Disclosed secondaries (never binding):** `/STRONG-STAT` median+1×MAD `ρ`/`f`;
  `/STRONG-HA` any-direction `ρ`/`f`; harami↔retained-move overlap fractions; the
  warmup/degenerate excluded fractions; retained vs unfiltered magnitude median/IQR.

## Viability & Composition (P10 / P11 — mechanical readout, not the gate)

- **Materially-different cell (P10, per filter, binding form):** `ρ ≥ 1.5` **and**
  `f ∈ [0.10, 0.50]` **and** `#defined-decision ≥ 30`. An optional fixed-seed
  moving-block bootstrap CI on `ρ` may be reported as **disclosed support** (not an
  added binding threshold beyond D0 P10).
- **Composition readout (P11, per filter independently):** count
  materially-different cells and distinct instruments; the family-level
  "this filter identifies a materially different move population" claim holds iff
  **≥ 5 cells over ≥ 3 instruments**. `/STRONG-HA` any-direction sensitivity and
  `/STRONG-STAT` median+1×MAD compositions are reported in parallel, disclosed,
  non-binding.
- The experiment **emits** this readout; the 014-A **G1 adjudication** (informing
  combined-event registration, design §10) is checkpoint desk work, never
  self-declared by the experiment.

## Success / Failure / Inconclusive Criteria

- **Experiment verdict — STRONG_FILTER_CHARACTERISATION_DELIVERED:** the per-cell
  `ρ` / `f` / materially-different map for each filter (binding form), the
  cross-cell consistency summary, the disclosed alternative-form / sensitivity /
  overlap / excluded-fraction tables, and the P10/P11 composition readout are
  produced — whatever the material/not-material mix.
- **Evidence AGAINST (CHARACTERISATION_REFUTED — halts 014-A pending a fix):** a
  **systematic** construction defect, predeclared threshold: **non-determinism on
  any cell**, **or** a filter-well-formedness / magnitude-validity / causality /
  TRAIN-fence invariant (battery items 1–4) violated on **≥ 3 instruments**. The
  move population cannot be characterised on a broken filter.
- **Inconclusive (cell-level only):** a cell with `#defined-decision < 30`
  (NOT_REPORTABLE-by-power); recorded, excluded from the P11 numerator, not a
  failure.
- The **materiality outcome** (which filters carve a materially-different
  population) is **not** an experiment verdict — it is the §10 G1 adjudication on
  this experiment's readout.

## Complexity Budget

- **Max statistical tests: 1** — an *optional* fixed-seed moving-block bootstrap CI
  on the per-cell median-magnitude ratio `ρ` (P10(a) robustness, disclosed
  support); the P10 adjudication itself is the deterministic point criterion. No
  other inferential test. (Mirrors EXP-050's CI-on-`Δ` as disclosed support.)
- **Max visualisations: 4** — (i) `/STRONG-STAT` (p75) per-cell median-ratio `ρ`
  heatmap (17×6) with the 1.5 threshold highlighted; (ii) `/STRONG-HA` (primary)
  per-cell `ρ` heatmap (17×6); (iii) retained-fraction `f` heatmap, small-multiple
  for the two binding filters, with the `[0.10, 0.50]` band marked; (iv)
  materially-different (both-conditions) composition map across the two binding
  filters. All disclosed forms (median+1×MAD, any-direction sensitivity, overlap,
  magnitude distributions, censoring) go to CSV. Bounded plot inputs from the
  analysis pass — no reloads.
- **Max new code modules: 1** under `python/src/xen/` — `strong_move.py`
  (`/STRONG-STAT` rolling-window move filter with p75 and median+1×MAD forms;
  `/STRONG-HA` impulse-run detection + run→move mapping with both
  direction-match modes; reusable in 014-B), **or** an experiment-local helper
  under `code/` if not yet reusable. Reuse `xen.zigzag`,
  `xen.heiken_ashi_generator`, `xen.ha_harami`, `xen.bar_aggregator` unchanged
  (no edits).

## Data Requirements

Per instrument: lazy `pl.scan_parquet`; read total row count from metadata;
`analysis_rows = int(total_rows*0.7)`, `train_rows = int(analysis_rows*0.7)`;
collect only the first `train_rows` file-order 1-minute rows (F01 prefix; never
sort/collect the full file, never read TEST or holdout); assert chronological;
`train_end_ts` = last `CloseTime`. Aggregate each EXP-048-READY domain (5m strict;
others `min_coverage=0.90`); fence domain bars to `CloseTime ≤ train_end_ts`; run
`xen.zigzag` (confirmed moves); compute `mag`; apply `/STRONG-STAT` (p75 +
median+1×MAD) and `/STRONG-HA` (primary + sensitivity) per-move decisions; generate
HA candles + detect haramis and assign to moves for the overlap secondary; collect
per-cell records; second full pass for determinism. Outputs (`results/`):
`per_cell_strong_move.parquet`, `p10_map.csv` (per filter binding form: `ρ`, `f`,
median magnitudes, both-pass flag, `#defined-decision`, reportable, optional CI),
`strong_stat_alt_disclosure.csv` (median+1×MAD `ρ`/`f`),
`strong_ha_sensitivity.csv` (any-direction `ρ`/`f`), `harami_overlap.csv`
(disclosed secondary), `excluded_fractions.csv` (warmup/degenerate),
`composition_readout.json`, `run_metadata.json`; four bounded plots from the
collected per-cell summaries (no reloads). `tqdm` over the instrument/cell outer
loop; per-cell bounded memory (do not retain all domain frames). Expected runtime:
minutes (READY cells × 2 passes).

## Exclusions

- No 3-barrier capture geometry (EXP-049 / HYP-002), no position-in-move metric
  (EXP-050 / HYP-003), no `/CONFIRM` entry model (EXP-052 / HYP-005), no `/BARCFG`
  isolation/filtering, no `/ATRMULT`, `/LOOKBACK`, or any barrier-model variant.
- No combined harami-at-strong-move *capture* event; the harami appears only in the
  disclosed, non-binding overlap secondary.
- No costs (gross throughout); no exit rule; no net P&L, expectancy, or return
  computation of any kind. Retained-move magnitude is **non-tradable descriptive**
  (uses the future pivot under the predeclared completed-move allowance) and feeds
  **no** strategy, signal, or P&L.
- No returns or prices from HA/Renko construction values; all magnitudes and move
  boundaries are real-bar prices; HA candles are used only for `/STRONG-HA` run
  detection and harami detection (detection only).
- No parameter tuned, selected, or frozen against any EXP-051 output (`/STRONG-STAT`
  reports both forms with no post-result selection; `/STRONG-HA` reports both
  mappings); no cross-instrument or cross-domain pooling for the binding endpoint;
  no TEST or holdout contact; no candidate slot consumed; no TEST read.

## Suggested Direction (non-binding)

Mirror the EXP-050 orchestration (F01 loader, per-cell loop, determinism replay,
bounded plots). Implement `/STRONG-STAT` as a causal rolling-window expression over
the confirmed-move magnitude series (trailing `min(20, available)`, `≥ 5` floor;
p75 and median+1×MAD); implement `/STRONG-HA` as a vectorised per-HA-bar qualify
predicate + a 3-bar same-direction run scan, then map runs to moves by an interval
test against `(StartTime, EndTime]` (safe — the moves are a precomputed completed
segmentation, not a sequential causal scan). Reuse `xen.move_position.assign_to_moves`
(pivot tiling) for the harami-overlap assignment. Keep the ZigZag / HA / harami
generation calls frozen and unedited. Emit the P10/P11 readout per filter; do
**not** self-adjudicate G1.
