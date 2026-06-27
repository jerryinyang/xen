# Experiment: EXP-055 — Long-Horizon Availability (Conditioned HA Harami; AVWAP-Analog Lifetime MFE/MAE)

> **Mandatory-reading precondition (014-B, binding).** `014-A-conditioning-gap-and-validation-lessons.md`
> was read in full before this scope was written. EXP-055 is the **long-horizon availability
> diagnostic** (HYP-008, P19) — the AVWAP EXP-047 analog the G1 desk flagged as *unestablished*
> (lessons §7). The four mandatory rules are honoured as follows, recorded so Stage 4 can check:
> - **(a) conditioning** — honoured. The object measured is the **live `/STRONG`-conditioned HA
>   harami** (the actual family signal), not the raw harami or the unconditioned ZigZag substrate.
>   `/STRONG-STAT` (P7, live magnitude-percentile) is binding; `/STRONG-HA` (P8) is a disclosed
>   secondary arm. This is the **same event population as EXP-053**.
> - **(b) harami-anchor** — honoured. The per-event window is anchored at the **harami
>   confirmation-bar real close**, the family's claimed lead point — *not* the ZigZag trend-change
>   confirmation (the EXP-049 anchor).
> - **(c) position-in-move descriptive-only / never a live filter** — honoured. EXP-050's position
>   metric is not used as a filter. The lifetime **window boundary** uses retroactively-confirmed
>   ZigZag pivots, which is permitted here because this is a **descriptive characterisation of
>   completed moves** (completed-move grouping; family doc lines 139–143; P19 explicit allowance),
>   not a live signal condition. No barrier, entry, or filter uses an unconfirmed pivot.
> - **(d) expectancy / not first-hit `r`** — honoured *with the P19-appropriate endpoint*. This is an
>   **availability** diagnostic, not a capture/expectancy read: the binding metrics are **lifetime
>   favourable MFE and adverse MAE** (gross, ATR-normalised), per P19 — an excursion endpoint, never
>   first-hit `r`. No trading rule, barrier, partial exit, or stop is applied (those are EXP-056–060);
>   measuring availability under first-hit `r` would foreordain the answer (lessons §8.6).
> EXP-055 does **not** treat the EXP-049 `r≈0.50` null or the EXP-050 front-loading as evidence
> against the family — those measured the *unconditioned* object. It settles the open AVWAP parallel
> (lessons §7): *move available + capture missing* (keep iterating geometry/exits) vs *no available
> move* (closure better-supported).

**Phase / checkpoint:** `2026-06-14-014-ha-harami-substrate-and-capture` (014-B; G0-B PASS 2026-06-15).
**Family / candidate:** `CF-HA-HARAMI-001` (`REGISTERED`) · `CF-HA-HARAMI-001/HYP-008` — EXP-055
(registered PLANNED, Phase 014-B batch, `multiplicity-registry.md` line 383).
**Lead role:** Lead 3 of the 014-B slate — the long-horizon availability read (AVWAP EXP-047 analog).
**Governing design:** `014-B-design.md` (§5 Lead 3, §7, §8) + `014-B-D0-addendum.md` (P19 + P14/P16/P20);
inherits Phase 014 `design.md` §8 D0 (P1–P13) and the family spec `candidate-families/harami.md`.
**Reuses:** EXP-047 `move_size.py` (lifetime-boundary / excursion / matched-control machinery, per P19
and the family-spec implementation path); the EXP-053 conditioned-signal construction
(`xen.expectancy.live_in_progress_state`, `live_strong_stat`).
**Operator scope decisions (2026-06-16, recorded before any data contact):**
- **Lifetime window end = end of the reversal move M_b** — `[harami entry+1 → the 2nd confirmed
  ZigZag pivot at/after the harami]`. The 1st confirmation ends the faded in-progress move M_a; the
  2nd ends the reversal move M_b the family predicts. Captures the full reversal swing.
- **Reference band = 0.5× ATR and 1.0× ATR** (two fixed reference lines; reference-only, never
  subtracted; disclosed as approximations).

## Slot & ledger accounting (binding)

- **0 candidate slots, 0 TEST reads.** Characterization/diagnostic per the 014-B D0 addendum
  (`014-B-D0-addendum.md` slot & ledger accounting). A candidate branch is registered only at G2
  PROCEED_TO_SCREEN — never inside 014-B.
- **No TEST stratum is read.** All work is on the **TRAIN** slice (first 70% of the first-70%
  analysis set), identical fence to EXP-049/EXP-053/EXP-054. No `test-read-ledger.md` tally applies;
  no entry is created. The nested analysis-set **TEST stratum is not read**; the final-30% **global
  holdout** is never loaded, inspected, or touched. The conditioned HA-harami event population already
  had its first new-universe TRAIN contact in EXP-053 (same definition); no new stratum is opened and
  the holdout seal carries forward unchanged.
- All work is **gross** (no costs). Detection on HA candles; **every outcome metric on real prices**
  (`RealOpen/High/Low/Close` domain-bar OHLC), never HA prices. The reference band is gross and
  ATR-normalised, never subtracted from any excursion.

---

## Question (exploratory / diagnostic)

For the live `/STRONG`-conditioned HA harami (anchored at the harami confirmation-bar close, faded
against the in-progress strong move), over the **full reversal move** that follows it
(harami → end of the reversal move M_b), what is the gross, ATR-normalised distribution of **lifetime
favourable excursion (MFE)** vs **lifetime adverse excursion (MAE)**, per cell and composed across the
grid — and does it look like the AVWAP situation (a meaningful favourable move is *available* but the
short-horizon benchmark capture missed it) or worse (no favourable reversal move is available at all)?

This is a **characterisation**, not a hypothesis test of an edge. There is no "success"/"failure" edge
claim; the deliverable is the availability map and the AVWAP-comparison fork readout. The falsifiable
sub-structure (correctness, not edge) is the monotone/causal/determinism set under §Correctness Gates.

---

## Scope Boundaries

### Data Views

- **Real domain bars** (5m strict; 15m/30m/1h/2h/4h via `xen.bar_aggregator.aggregate_ohlc`,
  `min_coverage=0.90` — identical to EXP-048/049/053/054/VAL-004) for the ZigZag substrate, confirmed
  moves, strong-move magnitudes, ATR normalisation, the lifetime window, and **all** excursion metrics.
- **Heiken Ashi candles** (`xen.heiken_ashi_generator`, from the same domain bars) for **harami
  detection only** (`xen.ha_harami.detect_ha_harami`, frozen EXP-048 detector). **No HA price enters
  any metric.**

### Event population (the live conditioned signal — identical to EXP-053)

- An HA harami (frozen detector) **AND** the live `/STRONG-STAT` magnitude-percentile filter: the
  in-progress confirmed-ZigZag move's **magnitude-so-far** `M_sofar = |C − start_pivot|` (last
  *confirmed* pivot → harami real close `C`) is **≥ p75** of the trailing-20 confirmed-move magnitudes
  (P7, binding). `/STRONG-HA` (P8: run of `X=3` large-body HA bars, no opposing wick) is a **disclosed
  secondary** arm run through the identical lifetime measurement.
- **Trade / reversal direction** `rd = −trend_direction` = the direction of the reversal the harami
  predicts (`= Direction_k` of the last confirmed move; `xen.expectancy.live_in_progress_state`). No
  `/BARCFG` isolation; all qualifying haramis count.
- Construction reuses `xen.expectancy.live_in_progress_state` (live in-progress state, causal as-of on
  `ConfirmTime`) and `live_strong_stat` (binding p75; MAD disclosed) — the **same functions EXP-053
  used**, so the population is byte-identical to EXP-053's conditioned events on the binding arm.

### Lifetime window (operator-confirmed: end of reversal move M_b)

For each qualifying harami at entry bar `e` (entry = harami confirmation-bar real close `C`, at the
real-bar index aligned by `CloseTime`):

- Let `confirm_idx` be the sorted ZigZag trend-change confirmation bar indices for the cell
  (`xen.capture_barriers.confirm_indices`).
- `pos = searchsorted(confirm_idx, e, side="right")` — the first confirmation **strictly after** `e`.
  - `c1 = confirm_idx[pos]` ends the in-progress move **M_a** (the faded move).
  - `c2 = confirm_idx[pos+1]` ends the **reversal move M_b** — the **window end** (operator decision).
- **Window** = real bars `[e+1, c2]` (inclusive of the M_b end pivot bar). Excursions are measured over
  this window on real OHLC.
- **DATA_CENSORED** (excluded from medians, disclosed as a count/fraction): fewer than **two**
  confirmations exist at/after `e` before the TRAIN edge (`pos+1 ≥ confirm_idx.size`), i.e. M_b does
  not complete inside TRAIN. Never silently clipped to the TRAIN edge for a censored event; censoring
  is a disclosed exclusion, not a truncated measurement.

This reuses the EXP-047 `move_size.lifetime_end` boundary logic, **extended by one confirmation** (to
M_b's end rather than M_a's end), per the operator decision. It is a **descriptive completed-move
grouping** (the retroactively-confirmed pivots `c1`,`c2` are future information relative to the bars
between them, used only as a descriptive lifetime boundary — never as a live signal/entry/filter;
family doc lines 139–143, P9 lines 113–118, P19).

### Metrics (gross, ATR-normalised, real prices)

For each qualifying, non-censored event, over the window `[e+1, c2]`:

- **Lifetime favourable MFE** = maximum favourable excursion in the reversal direction `rd`:
  - long reversal (`rd=+1`): `MFE = (max(High[e+1..c2]) − C) / ATR_entry`
  - short reversal (`rd=−1`): `MFE = (C − min(Low[e+1..c2])) / ATR_entry`
- **Lifetime adverse MAE** = maximum adverse excursion against `rd`:
  - long reversal: `MAE = (C − min(Low[e+1..c2])) / ATR_entry`
  - short reversal: `MAE = (max(High[e+1..c2]) − C) / ATR_entry`
- Both floored at `0.0` (standard excursion convention, as `move_size.excursions`); an empty window
  cannot occur for a non-censored event (`c2 > e`).
- **`ATR_entry` = Wilder ATR(14) at the harami confirmation (entry) bar** — the **same ATR-normalisation
  divisor as EXP-053** (P14), so EXP-055 excursions are directly comparable to the EXP-053 expectancy.
- Per-event `MFE`, `MAE`, and the derived `MFE − MAE` (favourable-availability asymmetry, ATR units).
- **Adaptation note vs `move_size.excursions`:** EXP-047 returned log-bps (`×10_000`); EXP-055 divides
  by `ATR_entry` instead, to match the 014-B ATR-normalised endpoint discipline (P14/P19). The
  window-scan and excursion-flooring structure are otherwise reused.

### Reference band (operator-confirmed: 0.5× and 1.0× ATR — reference-only, never subtracted)

Two fixed reference lines at **0.5 ATR-units** and **1.0 ATR-units** annotate every MFE/MAE
distribution and the per-cell median table. They are a **cost-floor analog** (the gross,
ATR-normalised stand-in for the EXP-047 frozen cost floor): a **declared, fixed ATR fraction**, used
**only as a comparison yardstick** (median MFE reported as a multiple of each line, exactly as EXP-047
reported "median lifetime peak MFE ≈5–9× the cost floor"). They are **never subtracted** from any
excursion and carry **no net-of-cost interpretation** (all work is gross). They are a **documented
approximation** with no inferential weight beyond the predeclared comparison in §Outcome readout.

### Parameters (all frozen D0; no tuning)

ZigZag Wilder ATR(14), `ATR_MULT = 1.0` (P1); `LOOKBACK = 1` (P5) for the in-progress reference;
`/STRONG-STAT` trailing-20, ≥p75 (P7); `/STRONG-HA` `X=3` (P8); ATR-normalisation divisor = Wilder
ATR(14) at the harami entry bar (P14); reference band `{0.5, 1.0}` ATR (operator-declared, reference
only); bootstrap `b = round(m^(1/3))`, `N_BOOT = 10_000`, fixed seed (P14;
`xen.capture_barriers.block_bootstrap_ci` / `move_size` median-bootstrap machinery). No barrier model,
no time cap, no partial exit, no trailing stop (no capture rule is applied in an availability read).

### Instruments / cells

The **99-cell EXP-049/EXP-053/EXP-054 member grid**: 17 instruments × {5m,15m,30m,1h,2h,4h} minus the
3 COVERAGE_EXCLUDED cells (US500-4h, JP225-2h, JP225-4h). Per-cell first, then **P11** composition
(≥5 cells over ≥3 instruments) for any family-level availability claim. Full-grid breadth is required
by P11 and the "no blanket assumptions" principle. DE30 carries the truncated-coverage disclosure
(broker history ends 2026-01-16); counts derive from its own realized timeline.

### Time range

Full dataset, nested chronological split. **TRAIN only** = first 70% of the first-70% analysis set
(per cell, F01 file-order-prefix convention identical to EXP-049/053/054: `train_end_ts` = last
`CloseTime` of the first `int(int(total_rows*0.7)*0.7)` file-order 1-minute rows). TEST (last 30% of
the analysis set) and the final-30% **global holdout** are **not** read.

### Baselines (P13 / P20 — disclosed secondaries)

- **Matched-count random in-regime timestamps** (`move_size.matched_controls`, same cell/regime/
  direction, EXP-021/027 exclusion convention) run through the **identical lifetime-MFE/MAE
  measurement** (window to the same regime's M_b-analog end). This is the **EXP-047-analog comparison**:
  does the conditioned harami have *more favourable availability* than random entries in the same
  regimes, or is the favourable move a generic regime property?
- **MA(20,50) segmentation** (the alternative trend substrate, EXP-050/053 baseline): conditioned-harami
  lifetime MFE/MAE under MA-segmented moves, disclosed — addresses whether availability is
  ZigZag-specific.
- Baselines are **disclosed secondaries**; the binding readout is the conditioned signal's own
  MFE/MAE vs the reference band and the MFE-vs-MAE asymmetry.

### Look-ahead / causality discipline (binding)

- ZigZag pivots are future information until confirmed. The **signal** (harami + `/STRONG-STAT`) and
  `M_sofar` use only the **confirmed start pivot** (known) and the entry bar's own real close (known) —
  reused causal construction from `xen.expectancy.live_in_progress_state` / `live_strong_stat`.
- The lifetime **window boundary** (`c1`,`c2`) uses retroactively-confirmed pivots **only as a
  descriptive completed-move grouping** (P19; family doc lines 139–143). No entry, filter, barrier, or
  excursion threshold references an unconfirmed pivot or any future bar beyond the excursion window
  itself.
- Excursions read only bars `[e+1, c2]`, fenced `CloseTime ≤ train_end_ts` (a censored event whose M_b
  would complete past the TRAIN edge is DATA_CENSORED-excluded, never measured against truncated data).
- Ordering/alignment by `CloseTime`, never bar index across views.

### Real-price outcome discipline

Harami detected on HA candles; `M_sofar`, ATR normalisation, MFE, MAE, the reference band, matched
controls, and all distributions on real domain-bar OHLC. **No HA price in any metric.**

### Exclusions

- No costs (gross only); the reference band is never subtracted and carries no net interpretation.
- **No capture rule of any kind** — no 3-barrier geometry, no favourable/adverse target, no time cap,
  no first-hit `r`, no `/EXIT-PARTIAL`/`/EXIT-TRAIL-STRUCT`. EXP-055 measures *available* excursion,
  not *captured* return (capture is EXP-053/056–060).
- No `/BARCFG`/`/CONFIRM` overlays; no alternative barrier geometries; no position-in-move *filter*.
- No parameter tuning, no post-result variant or reference-line selection; no gate adjudication (single
  G2 after the full 014-B slate — EXP-055 emits a characterization readout only).
- No TEST or holdout contact; no candidate slot; no TEST read.

## Outcome readout (predeclared, mechanical; EXP-055 emits — it does not self-adjudicate §8)

Like EXP-054, EXP-055 **emits** the readout; phase routing is the single **G2** desk adjudication. All
readouts are gross, per-cell first, composed by **P11** (≥5 cells over ≥3 instruments). Power floor:
a cell with **< 30 qualifying non-censored events** is **NOT_VIABLE-by-power** (non-reportable for the
composition, disclosed, never an undefined ratio).

- **Per-cell `MOVE_AVAILABLE` (graded, mechanical):** a reportable cell is flagged `MOVE_AVAILABLE`
  iff **(i)** ≥30 qualifying events, **(ii)** the regime-clustered moving-block bootstrap **CI_low of
  median MFE > 1.0** (the upper reference line — a *comparison threshold*, never a subtraction, mirroring
  EXP-047 `leg2_floor`), **AND (iii)** median MFE > median MAE (favourable availability dominates
  adverse). Each cell additionally reports median MFE as a **multiple of both reference lines**
  (×0.5-ATR and ×1.0-ATR) and median MAE, with CIs.
- **Family-level fork (the deliverable label, descriptive — final routing is G2):**
  - **AVAILABILITY_GOOD** (the AVWAP situation — *move available, capture missing*): `MOVE_AVAILABLE`
    clears **P11** (≥5 cells over ≥3 instruments). Reading: a meaningful favourable reversal move is
    available that the short-horizon benchmark (EXP-049/053) capture missed → continuing to iterate
    capture geometry/exits across the 014-B surface (EXP-056–060) is justified.
  - **AVAILABILITY_POOR** (worse than AVWAP — *no available favourable move*): `MOVE_AVAILABLE` does
    **not** clear P11 (favourable excursion does not robustly exceed the upper reference line and/or
    does not exceed MAE across the quorum). Reading: closure is **better-supported** than for AVWAP —
    but **no closure occurs inside 014-B** (G2 only, on the full surface).
  - **INCONCLUSIVE** (power-limited): fewer than the P11 quorum of cells reach ≥30 qualifying events
    (conditioning + the 2-confirmation window deplete counts), with no correctness failure.
  - **SUBSTRATE/METHOD_DEFECT:** any determinism, causality, or invariant failure (§Correctness Gates)
    → fix before reporting.
- Disclosed in parallel: the `/STRONG-HA` arm and both baselines (matched-random, MA-segmentation) under
  the identical pipeline; the DATA_CENSORED fraction per cell; the MFE/MAE distributions; the
  median `MFE − MAE` asymmetry map.

The deliverable label is **AVAILABILITY_CHARACTERISED** carrying the per-cell `MOVE_AVAILABLE` map, the
P11 composition, the AVAILABILITY_* fork, both reference-line multiples, the `/STRONG-HA` and baseline
disclosures, and all censoring counts. No phase closure or candidate registration occurs here.

## Correctness Gates (falsifiable sub-structure; binding)

- **Determinism:** a full second pass (re-aggregate, re-run ZigZag, re-detect haramis, re-condition,
  re-measure excursions) reproduces every per-cell figure frame-identically. Any mismatch →
  SUBSTRATE/METHOD_DEFECT.
- **Causality / window invariants:** `MFE ≥ 0`, `MAE ≥ 0`, every excursion window satisfies
  `e+1 ≤ c2 ≤ train_last_idx`, `c2 = confirm_idx[pos+1]` with `confirm_idx[pos] > e`; no event reads a
  bar with `CloseTime > train_end_ts`. Violation on ≥3 instruments → SUBSTRATE/METHOD_DEFECT.
- **Population reconciliation:** the binding `/STRONG-STAT` conditioned-event set (count + a
  `trigger_idx/time/rd` digest per cell) matches the EXP-053 conditioned population on the same grid
  (same detector, same filter, same TRAIN fence) — a cross-experiment consistency check that the same
  signal is being measured. Mismatch is disclosed and investigated before the readout is trusted.

## Complexity Budget

- **Max statistical tests: 4** — (1) regime-clustered moving-block bootstrap CI on median MFE per cell;
  (2) same on median MAE; (3) matched-random baseline median-MFE contrast (signal − control);
  (4) MA(20,50)-segmentation baseline median-MFE contrast. (Comparative experiment per the budget table.)
- **Max visualisations: 4** — (i) per-cell median MFE & MAE forest/CI plot with the 0.5/1.0-ATR
  reference band; (ii) median `MFE − MAE` asymmetry heatmap (17×6); (iii) pooled MFE (and MAE)
  distribution with the reference band and the median markers; (iv) `MOVE_AVAILABLE` / P11 composition
  map (with NOT_VIABLE-by-power and COVERAGE_EXCLUDED cells marked). Baseline and `/STRONG-HA` tables,
  censoring counts, and reference-line multiples go to CSV.
- **Max new code modules: 1** — a thin EXP-055 lifetime-availability helper (analogous to EXP-047
  `move_size.py`): the **end-of-M_b window boundary** (`c2`) and the **ATR-normalised lifetime
  excursion** computation, plus the mechanical `MOVE_AVAILABLE` / composition readout. All conditioned-
  signal construction (`xen.expectancy.live_in_progress_state`, `live_strong_stat`), ZigZag
  (`xen.zigzag`), harami detection (`xen.ha_harami`), `/STRONG-HA` (`xen.strong_move.annotate_ha_impulse`),
  confirmation indices (`xen.capture_barriers.confirm_indices`), the median bootstrap
  (`xen.capture_barriers.block_bootstrap_ci`), and the matched-control machinery
  (`move_size.matched_controls`) are **reused**. Orchestration lives in `code/run_experiment.py`.

## Metric Denominators & Zero-Baseline

- **Qualifying-event population** (the MFE/MAE denominator): events that (a) pass the binding
  `/STRONG-STAT` filter (`defined ∧ retained_p75`) with a valid live in-progress move
  (`InProgressState.valid`), (b) have `ATR_entry` defined (post-Wilder-ATR-warmup), and (c) are
  **not DATA_CENSORED** (M_b completes inside TRAIN: `confirm_idx[pos+1]` exists). Warmup-excluded and
  DATA_CENSORED events are **excluded** from medians and **disclosed as counts/fractions**.
- **Per-cell endpoint:** `median` over the qualifying-event MFE (and, separately, MAE) population.
- **Zero-baseline / power:** a cell with **< 30 qualifying events** is **NOT_VIABLE-by-power**
  (non-reportable for the composition), never an undefined or infinite ratio. Conditioning + the
  2-confirmation window reduce counts vs the unconditioned base; cells dropping below 30 are disclosed.
- **Reference band:** fixed `{0.5, 1.0}` ATR-units; median MFE/MAE reported as multiples of each;
  never a denominator, never subtracted.
- **Disclosed secondaries (never the binding availability readout):** mean MFE/MAE; the median
  `MFE − MAE`; the DATA_CENSORED and warmup fractions; the `/STRONG-HA` arm; both P13 baselines; the
  MAD `/STRONG-STAT` sensitivity arm (`retained_mad`).

## Data Requirements

Per cell (instrument × domain), TRAIN slice only: lazy `pl.scan_parquet`; read total row count from
metadata; `analysis_rows = int(total_rows*0.7)`, `train_rows = int(analysis_rows*0.7)`; collect only
the first `train_rows` file-order 1-minute rows (F01 prefix; never sort/collect the full file, never
read TEST or holdout); assert chronological; `train_end_ts` = last `CloseTime`. Aggregate each member
domain (5m strict; others `min_coverage=0.90`); fence domain bars to `CloseTime ≤ train_end_ts`;
generate HA candles; run `xen.zigzag.generate_zigzag(bars, atr_period=14, atr_mult=1.0)` → confirmed
moves; detect haramis on HA candles aligned by `CloseTime` to real bars; build the live in-progress
state + `/STRONG-STAT`/`/STRONG-HA` conditioning (`xen.expectancy`); compute `confirm_idx`
(`xen.capture_barriers.confirm_indices`); for each qualifying harami resolve the end-of-M_b window
(`c2`) and compute ATR-normalised lifetime MFE/MAE; bootstrap the per-cell medians; compute the
matched-random and MA-segmentation baselines through the identical measurement; second full pass for
determinism. `tqdm` over the 99-cell grid; bounded per-cell memory (do not retain all domain frames);
fixed seed; deterministic. Outputs (`results/`): `per_cell_availability.parquet` (per cell: median/CI
MFE, median/CI MAE, MFE−MAE, ×0.5/×1.0 reference multiples, n_qualifying, n_censored, MOVE_AVAILABLE
flag, baseline medians/contrasts); `availability_map.csv` (binding `/STRONG-STAT` summary);
`availability_secondary.csv` (`/STRONG-HA`, MAD arm, baselines, censoring); `composition_readout.json`
(P11, AVAILABILITY_* fork, reference-line multiples); `population_reconciliation.csv` (vs EXP-053
conditioned population); `run_metadata.json` (seed, frozen constants, reference band, EXP-053 source
paths/hashes). Four bounded plots from the collected per-cell summaries (no reloads).

### Standard Loading Pattern (TRAIN slice, per cell)

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob(f"timebars/timebars_{symbol}_*.parquet"))[-1]

scan = pl.scan_parquet(path)                      # F01 file-order prefix; no full sort/collect
total_rows = int(scan.select(pl.len()).collect().item())
analysis_rows = int(total_rows * 0.7)             # first 70% = analysis set
train_rows = int(analysis_rows * 0.7)             # first 70% of analysis = TRAIN
train_bars = scan.slice(0, train_rows).collect()  # TEST + holdout never sliced
# assert chronological; train_end_ts = train_bars["CloseTime"].max()
# domain aggregation (xen.bar_aggregator) for 5m strict / 15m+/30m+/1h+/2h+/4h at min_coverage=0.90
```

## Suggested Direction

Compose existing primitives; the only new code is the end-of-M_b window + ATR-normalised excursion +
readout helper (mirroring `move_size.py`). Pipeline per cell:
`xen.zigzag.generate_zigzag` → confirmed moves and `xen.capture_barriers.confirm_indices` → `confirm_idx`;
`xen.heiken_ashi_generator` + `xen.ha_harami.detect_ha_harami` → harami entry bars (aligned by
`CloseTime`); `xen.expectancy.live_in_progress_state` + `live_strong_stat` → the binding conditioned
population and `rd` (identical to EXP-053; cross-checked by `population_reconciliation`);
`xen.strong_move.annotate_ha_impulse` → the `/STRONG-HA` disclosed arm. For each qualifying harami,
`pos = searchsorted(confirm_idx, e, "right")`; `c2 = confirm_idx[pos+1]` (else DATA_CENSORED); scan
real OHLC `[e+1, c2]` for the rd-aware favourable/adverse extremes and divide by `ATR_entry`
(Wilder ATR(14) at `e`, from `xen.zigzag.wilder_atr` reused on the cell's real bars). Bootstrap the
per-cell median MFE/MAE with `xen.capture_barriers.block_bootstrap_ci` (regime-clustered moving block,
`N_BOOT=10_000`, fixed seed). Run `move_size.matched_controls` for the matched-random baseline through
the same excursion measurement; MA(20,50)-segmentation baseline swaps the substrate. Emit the layered
`MOVE_AVAILABLE` / P11 / AVAILABILITY_* readout; **do not adjudicate §8**.
