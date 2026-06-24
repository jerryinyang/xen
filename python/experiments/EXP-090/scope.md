# Experiment: EXP-090 — Phase 021 Exit-Substrate Readiness & Per-Cell Inference Calibration (RSI-2 Fade, 16 × {15m,1h})

**Phase:** 021 (CF-MR-001 batch 2 — RSI-2 fade capture-geometry & tradability; checkpoint
`2026-06-23-021-mr-fade-capture-geometry`, **G0 RATIFIED 2026-06-23**, **D0 FROZEN**) · **Family:** **CF-MR-001
— bare RSI-2 mean-reversion fade (CORE)**, admitted at G-020 · **HYP:** `CF-MR-001/HYP-002` (tradability of the
admitted lever) · **Registry:** Phase 021 batch (`multiplicity-registry.md`); CF-MR-001 `ADMITTED (BINDING)`,
first candidate slot consumed at G-020 (`candidate-families/cf-mr-001.md`) · **Candidate slots:** 0 (readiness /
calibration; the first slot was consumed at G-020, Phase 021 consumes none) · **TEST reads:** 0 counted
(TRAIN-sub-split only; no analysis-TEST stratum sliced, no stratum-specific strategy inference; readiness/coverage
exposure = disclosure per the ledger).

**This is NOT an exit screen and NOT a tradability/edge claim.** It is the Phase 021 **readiness + per-cell
inference calibration** step (design §4, EXP-090 row; D8). Its only deliverables are (a) the **Phase 021 member
set** (which 15m/1h cells carry forward), (b) the demonstration that the **bare-fade entry substrate** and the
**1-minute intrabar exit-fill substrate** are constructible, deterministic, causal, and holdout-fenced, and (c)
the **per-cell event-level MDE / FPR-coverage** under the frozen referee's net-expectancy inference — the
**margin** the binding EXP-093 TEST rule consumes (D6 4c: margin = the cell's EXP-090-calibrated MDE). **No exit
is screened, no net or gross strategy expectancy is computed, and no cell is selected or ranked on an edge here**
(that is EXP-091/092). The binding tradability gate (the frozen referee suite, D4) and the screen/sequence/TEST
rules (D6) are inherited unchanged; EXP-090 only establishes that the machinery is constructible and powered on
the member cells.

**Analog:** EXP-080 (Phase 018 substrate readiness — determinism + causality + coverage + null-FPR sanity) **+**
EXP-044 / EXP-070 (per-cell event-level inference calibration — per-cell FPR control + finite event-level MDE on
synthetic null/planted-edge draws over the real TRAIN scaffolding, real event **outcomes never read for an
edge**). EXP-090 is those two patterns fused and specialized to the **bare RSI-2 fade** on **{15m,1h}**, with one
genuinely new readiness component: the **1-minute intrabar fill engine** (D2.5, new module `xen.intrabar_fill`)
that EXP-091's native targets and ATR-barrier arm depend on.

**Gating precondition (Stage-1 check):**
- **EXP-080 `READINESS_DELIVERED`** — the 15m/1h subset of the EXP-080 READY set is the member set: **all 16
  instruments × {15m,1h} = 32 cells are READY** (the only EXP-080 `COVERAGE_EXCLUDED` cells were US500-4h and
  JP225-4h, both **4h**, so none affects the 15m/1h member set; verified against
  `python/experiments/EXP-080/results/ready_map.csv`). No DE30 (dropped at INFR-003 §3.1).
- **Counted-read precondition:** the INFR-003 5-year ledger (`docs/signal-registry/test-read-ledger.md`,
  re-materialized 2026-06-21 on VAL-005 PASS) shows **all 16 instruments × {15m,1h,4h} = 48 strata at 0/2
  counted reads, open**. EXP-090 reads only the **TRAIN sub-stratum** (`[0, train_cutoff)`,
  `train_cutoff = int(int(total_rows·0.7)·0.7)`; EXP-080/089 precedent): the analysis-TEST stratum (last 30% of
  the analysis set) and the final-30% global holdout are **never sliced or materialized**. It makes **no
  stratum-specific strategy selection or inference** — readiness, determinism, look-ahead invariants, raw
  per-cell event counts, and a synthetic-substrate inference calibration — so it spends **0 counted TEST reads**
  and the ledger is **unchanged**.
- **D0 provenance (frozen):** all entry, exit-slate, adverse-side, cost, referee, and threshold definitions
  (D1–D9 + the ratified-parameter table) were frozen 2026-06-23 **before** any result-producing code, including
  the `D0-amendment-001` clarifications (ATR triple-barrier time barrier = MR-tempo cap; counted read attaches
  to the stratum). No new selection statistic is introduced ⇒ **no bite-check required** (D0 header).

---

## Hypothesis / Exploratory Question

**Exploratory readiness + calibration question (no market-edge claim):** for every one of the **32 member cells**
(16 instruments × {15m, 1h}), on the 5-year first-70%-of-analysis **TRAIN** slice under the holdout-fenced
`build_domain_bars` construction —

1. is the **bare RSI-2 fade (CORE)** entry detector computable **deterministically**, **look-ahead-safe**, and
   **invariant-clean**, with a realized event count meeting the D8 coverage floor (**≥ 15** non-warmup
   ATR-defined events; **no upper bound** — the dense-oscillator convention from EXP-089, which dropped the
   EXP-080 sparse-substrate 8000 ceiling); and
2. is the **1-minute intrabar exit-fill substrate** (the D2.5 engine + the D2.3 frozen adverse side) constructible
   on each cell — every frozen exit arm **resolves to a terminal (fill / stop / cap) per event, deterministically,
   causally (only 1m bars at/after entry), timestamp-aligned (never bar index), and holdout-fenced** (the 1m slice
   clipped by timestamp at the TRAIN edge) — establishing that EXP-091 can run, **without computing any net/gross
   expectancy or selecting any exit**; and
3. does the frozen referee's **per-event net-expectancy inference** (moving-block bootstrap one-sided lower bound,
   `Z=1.645`; the binding D6 figure) exhibit **controlled FPR (≤ α₀ = 0.05)** and a **finite per-cell event-level
   MDE** at that cell's **realized event count**, measured on **synthetic null / planted-edge draws over the real
   TRAIN scaffolding** (real event outcomes never read for an edge — the EXP-044 anti-overfitting fence)?

A cell that passes all three is a **Phase 021 member** carrying its calibrated MDE as the EXP-093 margin. A cell
that fails the coverage floor, the exit-substrate determinism, **or** has no finite MDE under the frozen referee
is **`COVERAGE_EXCLUDED`** with record (it cannot bound a confirmation, à la EXP-044 BTCUSD-4h) — excluded from
EXP-091–093.

**Prior is not a target.** Some thin/fast cells may carry large finite MDEs or fail recovery; that is exactly the
power context EXP-091/092/093 need, not a defect. The verdict is the honest map (`READINESS_CALIBRATION_
DELIVERED`), however many cells qualify.

## Scope Boundaries

- **Data Views:** 1-minute time bars from the **VAL-005-admitted 5-year dataset**
  (`data/timebars/timebars_<SYMBOL>_*.parquet`, 2021-06-02 → 2026-06-21), aggregated to **{15m, 1h}** clock-aligned
  domain bars via the **holdout-fenced `xen.domain_bars.build_domain_bars`** (`min_coverage=0.90` **plus** drop any
  resample window whose label crosses the analysis-slice boundary — VAL-005 G1 fence). The **1-minute base series**
  is the intrabar fill source (D2.5), read **only within the TRAIN region** (clipped by timestamp at the TRAIN
  edge, never by 1m index). **No Heiken Ashi, Line Break, or Renko** (real-OHLC indicator family; synthetic prices
  never enter any metric).
- **Entry — bare RSI-2 fade (CORE), inherited frozen (D1; NO re-tuning):** `RSI(2)` Wilder on domain `Close`;
  **long `RSI₂(t) < 10`**, **short `RSI₂(t) > 90`** (period 2, extremes 10/90). Favourable = long→up, short→down.
  The CORE population only — **the `/VOLREGIME` partition, TREND, and RSI-FILTER variants are NOT carried**
  (inert / dead at EXP-089; registered-but-deferred, each needs its own `D0-amendment-*`). Reuse
  `xen.mean_reversion.mean_reversion_entries(...)["CORE"]` unchanged.
- **Exit slate (frozen, D2) — built for readiness only, NOT screened.** All arms share the **same adverse side**
  (D2.3: stop `2.0×ATR(14)` from entry + the EXP-089 causal MR-tempo cap `mr_tempo_caps`, exit-on-close at cap)
  and the **same 1m intrabar fill engine** (D2.5):
  - **Native (primary hypothesis at EXP-091):** **EXIT-RCT** — reversion-completion target
    `P*_t = Close_t + (AL_t − AG_t)` long / `Close_t − (AG_t − AL_t)` short, from the Wilder period-2 average
    gain/loss, recomputed each domain bar after entry (trailing limit); **EXIT-ERT** — equilibrium-return target
    `M_t = wilder_ema(Close, 10)`, recomputed each domain bar (trailing limit).
  - **Conventional contrast (tested at EXP-091, not expected to dominate):** RSI-revert-on-close (exit at domain
    close when RSI₂ crosses 50); fixed-bar (close at the MR-tempo-cap horizon); ATR triple-barrier (`1.0×ATR`
    favourable / `2.0×ATR` adverse, **time barrier = the same MR-tempo cap** per `D0-amendment-001`);
    favourable partial/trail (EXP-059 V2A-style, as `xen.capgeo_cost.partial_two_leg_exit` allows).
  - **EXP-090's use of the slate is readiness only:** confirm each arm **resolves a terminal per event**
    deterministically, causally, and holdout-fenced. **No net/gross expectancy, no cost overlay, no exit
    selection, no quorum** — those are EXP-091 (gross+cost screen) and EXP-085's cost model.
- **Per-cell inference calibration object (frozen referee; D4/D6):** the **per-event net-expectancy moving-block
  bootstrap one-sided lower bound** (`Z=1.645`) — the binding D6 figure for advancement — is the object whose
  per-cell FPR and MDE are calibrated. The full frozen qualification suite (strict gate stack + EXP-012
  ratified-loose + EXP-018 revised incremental/fitness unit, `xen.incremental_referee` / `xen.referee_calibration`)
  remains the binding gate downstream; the `ASS` qualifier is **non-binding discovery overlay** (G-017) and may be
  reported, never gates. **No referee is built or tuned.**
- **Calibration substrates (synthetic; EXP-044/EXP-070 pattern):**
  - **Null generators (2, structurally different — EXP-001/027/044 precedent):** (1) placebo events at the cell's
    realized event rate placed within the real TRAIN return scaffolding with **no planted edge**; (2) a second
    structurally different null (e.g. block-permuted real returns under matched placebo placement). Exact
    generators fixed in Stage 2. Null per-event net expectancy = exactly **0 ATR units**.
  - **Planted-edge mechanism:** known direction-signed per-event drift added to placebo-event **outcomes** over a
    predeclared ATR-unit grid spanning the per-cell-plausible range (grid fixed in Stage 2, before any
    measurement), outcome window matching the Phase 021 exit-hold semantics (the MR-tempo cap; representative
    fixed-resolution window fixed in Stage 2). Drift is added to **outcomes**, never to placement or matching.
  - **Anti-overfitting fence (binding):** the real fade-event **outcomes** (excursions, target hits, net
    expectancy) are **never read** by EXP-090; only realized event **rates/locations** and the readiness/coverage
    map come from the real scaffolding. The calibration is frozen before EXP-091 reads any real exit result. A
    failed calibration is a valid result, not license to re-pick the method.
- **Grid (member set):** **32 instrument×domain cells** = 16 instruments × {15m, 1h}. **Instruments (16):**
  EURUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, XAUUSD, BTCUSD, USTEC, US500,
  US2000, JP225 (VAL-003 universe **minus DE30**). **4h excluded** (dead-by-absence at EXP-089, 1/14; not carried
  — carrying it would reopen an empty cell, design §0).
- **Time range:** **first 70% of the analysis set only** (`[0, train_cutoff)`,
  `train_cutoff = int(analysis_rows · 0.7)`, `analysis_rows = int(total_rows · 0.7)`) — the nested TRAIN
  sub-split (EXP-080/089 convention). The analysis-TEST stratum is **not sliced**; readiness, counts, and
  calibration are on TRAIN; no strategy inference ⇒ 0 counted reads.
- **Global holdout:** the final 30% of each file is **never** loaded, inspected, counted, plotted, or used
  (including its 1m bars). Only Parquet **metadata** (`scan.select(pl.len())`) locates the split. The holdout
  fence (no domain-bar label and no intrabar-fill 1m bar crosses the TRAIN edge) is itself a checked readiness
  invariant.
- **Look-ahead bias prevention:**
  - Domain aggregation emits completed windows only; RSI(2)/RSI(5-unused)/EMA(10) and ATR(14) are sequential/causal
    (use only bars `≤ i`).
  - The RCT target uses the Wilder average gain/loss state through bar *t* only; the ERT target uses EMA-10 through
    bar *t* only; both recompute each domain bar after entry with no future bar.
  - The 1m intrabar fill walks 1-minute bars **forward from entry in chronological order**; within each 1m bar the
    favourable target / adverse stop touch is read off `[Low, High]` with the **conservative adverse-first
    tie-break** (D2.5, the EXP-054 fill-model question at 1m granularity); fill price = the target/stop **level**
    (a real touched price), never the 1m close, never synthetic.
  - All ordering/alignment use `CloseTime` / `SourceCloseTime` (real time), never bar index; the 1m→domain mapping
    is by timestamp. Synthetic null/planted placement and the RNG never consult future data.
- **Real-price discipline (binding):** every excursion, fill, stop, ATR, and calibration-outcome figure is on
  **real** OHLC (`RealOpen/High/Low/Close`; real 1m OHLC for fills). No HA/Renko synthetic-price metric anywhere.
- **Exclusions:** no net or gross strategy expectancy, no cost overlay (`xen.capgeo_cost`/`xen.financing` enter at
  EXP-091), no exit screening / quorum / selection / ranking, no candidate set or Holm rule (EXP-092), no TEST
  read or holdout contact (EXP-093); no `/VOLREGIME`, TREND, RSI-FILTER, contrarian, 25/75, regime×variant, or 4h
  expansion (registered-but-deferred); no parameter sweep or tuning of any frozen constant (RSI 2/10/90, ERT
  EMA-10, adverse 2.0×ATR, MR-tempo cap, ATR-barrier 1.0/2.0×ATR, D6 thresholds); no cross-instrument /
  cross-domain pooling as a binding statistic (per-stratum, LESSON-001 — any pooled figure is disclosure only);
  nothing tuned or frozen against any EXP-090 output.

## Per-Cell Checks (the measurement)

1. **Construction integrity** (per instrument × domain, TRAIN slice): OHLC consistency
   (`High ≥ max(Open,Close)`, `Low ≤ min(Open,Close)`); strictly increasing `CloseTime`; clock-aligned window
   boundaries; **holdout-fence** (no emitted window label crosses the TRAIN edge); **dropped-window fraction**.
   Frozen thresholds (carried from EXP-043/080/VAL-005): dropped `< 0.10` clean; `0.10–0.25` flagged disclosure
   (READY-eligible); `> 0.25` construction FAIL → cell `COVERAGE_EXCLUDED`.
2. **Entry-detector invariant battery** (CORE fade): all entry timestamps strictly within the TRAIN span; entries
   on completed bar closes only; RSI₂ threshold conditions hold (long `RSI₂<10`, short `RSI₂>90`); no entry uses
   post-entry data (causality); no NaN/null in any emitted entry field; events ordered monotone in `CloseTime`.
3. **Exit-substrate readiness** (the new D2.5 component — readiness only): for every member cell and every frozen
   exit arm (RCT, ERT, RSI-revert-on-close, fixed-bar, ATR-barrier, partial/trail), each entry event **resolves to
   exactly one terminal outcome** (favourable fill / adverse stop / cap exit) via the 1m engine; the 1m→domain
   mapping is **timestamp-aligned** (assert no bar-index alignment); resolution is **causal** (only 1m bars at/after
   entry; clipped at the TRAIN edge); **conservative adverse-first tie-break** applied when both barriers lie in
   one 1m bar; **tie-break incidence recorded per cell**; fill prices are real touched levels (assert ∈
   `[Low, High]` of the touching 1m bar). **No expectancy/cost/selection.**
4. **Determinism:** a full second regeneration of every cell's domain bars, entry events, and the complete 1m
   intrabar exit resolution for all arms; the entry-event table and the exit-resolution table compare
   **frame-identical** (exact) to the first pass. The synthetic calibration draws are byte-identical from their
   fixed seeds.
5. **Entry coverage & D8 bracket** (descriptive; denominators fixed below): per cell — entry count, entries per
   1,000 domain bars, and the non-warmup ATR-defined count; **coverage flag** `IN_FLOOR` iff count `≥ 15`, else
   `OUT_LOW` (`< 15`) → `COVERAGE_EXCLUDED`. **No upper bound** (dense-oscillator convention, EXP-089).
6. **Per-cell event-level inference calibration** (EXP-044/EXP-070 analog; the binding deliverable): at each
   member cell's **realized event count**, on **both** null generators and the planted-edge grid, measure —
   - **FPR** = fraction of null draws with net-expectancy bootstrap `ci_low_1s > 0` (target ≤ α₀ = 0.05; Wilson
     95% bound reported); and
   - **per-cell event-level MDE** = the smallest planted drift at which TPR ≥ 0.80 while FPR ≤ α₀ (finite MDE
     required for `IN_FLOOR` cells to remain members; **no finite MDE ⇒ `COVERAGE_EXCLUDED`**, à la EXP-044
     BTCUSD-4h).
   Precision (EXP-027/044 precedent): a calibration cell is usable only if FPR Wilson half-width ≤ 0.03 and TPR
   Wilson half-width ≤ 0.05; cells failing precision are `CALIBRATION_UNDERPOWERED` (operator precision-only
   re-run decision; draw-count increase only, no object change).
7. **Moving-block null-FPR machinery sanity** (readiness, no strategy estimand): confirm the moving-block
   bootstrap `ci_low_1s > 0` FPR is controlled (≤ 0.05, Wilson-hi ≤ 0.075) on a 5-year null slice at the new data
   scale, **binding only in the operating regime `n ≥ 120`** (rows at `n < 120` disclosed `small_n_disclosed`,
   the ratified EXP-077/078 small-n property, not a control failure). This is the EXP-080 readiness-level sanity,
   subsumed by check 6 at the per-cell level.

## Metric Denominators & Zero-Baseline (predeclared, before implementation)

- **Entry rate** = entry events / 1,000 TRAIN domain bars; denominator = the cell's TRAIN domain-bar count
  (disclosed). A cell with 0 entries reports rate `0.0` with its denominator shown — never `0/0`.
- **D8 coverage** = non-warmup ATR-defined count compared to the `≥ 15` floor; reported `IN_FLOOR / OUT_LOW` with
  count and denominator. Never a percentage over a baseline.
- **Exit-resolution rate** = resolved events / member events, per arm; an unresolved event (no fill/stop within
  the cap, before exit-on-close fallback) is itself a readiness flag, reported with its denominator, not silently
  dropped.
- **Tie-break incidence** = (count of events whose terminal 1m bar contained both barriers) / member events, per
  arm; denominator disclosed.
- **Per-cell FPR** denominator = completed null draws for that cell × generator × α (predeclared count, Stage 2);
  **TPR** denominator = completed planted-edge draws for that cell × edge × α; **per-draw net-expectancy**
  denominator = reportable matched events in that draw (never a bar count). Draws below the reportability floor
  are recorded against a predeclared draw-completion floor (Stage 2), not silently dropped.
- **Null per-event net expectancy = exactly 0 ATR units**; all effects reported as ATR-unit differences with CIs.
  No ratios against zero baselines anywhere.
- **Empty-construction guard:** a cell whose TRAIN slice has fewer domain bars than the detector warmup
  (RSI/EMA/ATR/MR-tempo windows) — so no entry state can form — is reported `CONSTRUCTED_EMPTY`, **not**
  NOT_READY (a coverage outcome, not a failure).

## Frozen Constants (predeclared at D0/G0; recorded here pre-data-contact)

- **Entry:** `RSI(2)` Wilder, extremes 10/90 (CORE only). Not varied.
- **Native exit targets:** RCT from the Wilder period-2 average gain/loss `(AG_t, AL_t)`; ERT `M_t =
  wilder_ema(Close, 10)`. Not varied.
- **Adverse side (all arms):** stop `2.0 × ATR(14)` from entry; max-hold = the EXP-089 causal MR-tempo cap
  (`mr_tempo_caps`, mult 1.0, `MR_CAP_FLOOR=3`, `MR_CAP_MAX=40`, `MR_EPISODE_WINDOW=20`); exit-on-close at cap.
  ATR-barrier favourable `1.0×ATR`, time barrier = the same MR-tempo cap (`D0-amendment-001`).
- **ATR:** Wilder ATR period **14** (`ATR_PERIOD`). All distances in ATR(14) units.
- **Coverage floor:** RSI-MR events per cell **≥ 15** (D8); **no upper bound** (EXP-089 dense-oscillator
  convention; the EXP-080 8000 ceiling does not apply).
- **Calibration:** α₀ = 0.05 (one-sided, `Z=1.645`); 2 structurally different null generators; planted-edge grid
  and draw/bootstrap counts fixed in Stage 2 to meet the precision thresholds. `N_PERM` / draw counts MC-stable.
- **Seeds:** master seed `20260623`; per-draw seed = deterministic hash of `(check, instrument, domain, arm,
  replicate)`; the `SUB-RANDOM`/null/bootstrap seeds fixed and recorded in `run_metadata.json`; a second full pass
  (incl. the 1m walk and the calibration draws) is byte-identical (D9).
- **Domain construction:** `build_domain_bars`, `min_coverage=0.90` + TRAIN-edge boundary fence.

## Success / Failure / Inconclusive Criteria

- **Cell MEMBER** (carries to EXP-091): construction integrity PASS (dropped ≤ 0.25, fence held) ∧ zero entry
  invariant violations ∧ exit-substrate readiness PASS (all arms resolve, deterministic, causal, timestamp-aligned)
  ∧ coverage `IN_FLOOR` (≥15) ∧ a **finite per-cell event-level MDE** under the frozen referee. The MDE is
  recorded as the cell's EXP-093 margin.
- **Cell `COVERAGE_EXCLUDED`** (excluded from EXP-091–093, with record): construction FAIL (dropped > 0.25), or
  coverage `OUT_LOW` (< 15), or no finite MDE on the predeclared grid. Recorded with the failing check; consumes
  nothing.
- **Cell NOT_READY / HALT-flag**: any entry/exit invariant violation, non-deterministic output, timestamp-vs-index
  misalignment, look-ahead, holdout-fence breach, or a real-price-discipline violation — recorded with the failing
  check; these indicate an implementation bug, not a data shape (see process-level HALT below).
- **Cell `CALIBRATION_UNDERPOWERED`**: calibration precision thresholds unmet at the budgeted draw counts
  (operator precision-only re-run decision; draw-count increase only).
- **Experiment verdict — `READINESS_CALIBRATION_DELIVERED`**: the 32-cell MEMBER / `COVERAGE_EXCLUDED` /
  `CALIBRATION_UNDERPOWERED` map, the per-cell entry-count + coverage table, the per-arm exit-resolution +
  tie-break table, the per-cell FPR + event-level MDE table, and the determinism replay are produced — whatever
  the mix. (Deliverable criterion, like EXP-080/044: success is the honest map, however many cells qualify.)
- **Evidence AGAINST (process-level — HALT):** a **systematic** failure indicating a detector / aggregation /
  fill-engine bug rather than a data quirk — **predeclared threshold:** non-determinism on **any** cell or on the
  calibration draws; **or** the same entry/exit invariant violated on **≥ 3 instruments**; **or** the two null
  generators disagree on FPR control beyond tolerance in **≥ 3 instruments**, or a systematic FPR excess across an
  entire domain in adequately powered cells (the per-cell EXP-027 machinery itself invalid, à la EXP-044
  METHOD_NOT_TRANSFERABLE); **or** the moving-block null-FPR uncontrolled (Wilson-hi > 0.075) at any `n ≥ 120` at
  the 5-year scale; **or** any timestamp-vs-index misalignment, look-ahead, or holdout-fence breach in the 1m
  engine. Any of these halts Phase 021 pending a fix (dated `D0-amendment-*` + hard-delete + full rerun if a
  frozen-design confound, programme norm).
- **Inconclusive (cell-level only):** a `CONSTRUCTED_EMPTY` cell; recorded, not counted NOT_READY.

## Complexity Budget

- **Max statistical tests: 1 binding** — none gate advancement (this is readiness/calibration, design §5 row
  "EXP-090 0"). The per-cell FPR/MDE determination uses the moving-block bootstrap CI + Wilson FPR/TPR intervals +
  grid-defined MDE; these are calibration measurements, not a hypothesis test on a market edge.
- **Max visualisations: ≤ 4** — (i) 16×2 MEMBER-status heatmap (15m/1h); (ii) entry-rate + coverage map
  (entries/1k bars vs the ≥15 floor); (iii) per-cell event-level MDE map (16×2) with `COVERAGE_EXCLUDED` marked;
  (iv) per-arm exit-resolution + tie-break-incidence summary. All from the single analysis pass's bounded plot
  inputs (no reloads).
- **Max new code modules: ≤ 2** under `python/src/xen/` (design §5: target 1–2) — (a) **`xen.intrabar_fill`**:
  the timestamp-aligned domain→1m intrabar fill engine with causal order-of-touch and the conservative
  adverse-first tie-break (the one justified new module; reused by EXP-091's native + ATR-barrier arms); (b) the
  two native targets as **small additions** to `xen.mean_reversion` (RCT closed-form from the Wilder
  `(AG_t, AL_t)` state — a deterministic additive helper `wilder_avg_gain_loss(close, 2)`) / `xen.exit_rules`
  (ERT from `wilder_ema(Close,10)`) — not a new module if they fit cleanly. **Reuse unchanged:**
  `xen.mean_reversion` (CORE entries, `mr_tempo_caps`, `wilder_rsi`, `wilder_ema`), `xen.domain_bars`
  (`build_domain_bars`), `xen.bar_aggregator`, `xen.expectancy`, `xen.position_exits` / `xen.exit_rules` /
  `xen.capture_barriers` / `xen.capgeo_cost.partial_two_leg_exit` (exit primitives), the frozen referee
  (`xen.incremental_referee`, `xen.referee_calibration`), and the EXP-044/EXP-070 calibration scaffolding (by
  copy or import). **No edits to frozen entry/exit generators; no new referee.** Drop any reuse that proves
  unnecessary on implementation.

## Data Requirements

Per instrument: lazy `pl.scan_parquet` of the single VAL-005-admitted 5-year file; read total row count from
metadata; `analysis_rows = int(total_rows · 0.7)`; `train_cutoff = int(analysis_rows · 0.7)`; collect only the
first `train_cutoff` file-order 1-minute rows (assert sorted by `CloseTime`); set the TRAIN-edge boundary
timestamp; build {15m,1h} domain bars via `build_domain_bars` (fence drops boundary-crossing windows); compute
RSI(2)/EMA(10)/ATR(14) and the MR-tempo cap on real OHLC (causal); derive the CORE fade entry population; build the
1m intrabar exit resolution for every arm (timestamp-mapped, causal, TRAIN-edge-clipped); collect per-cell
readiness/coverage records; run the per-cell synthetic null/planted-edge inference calibration at each realized
event count; run the bounded determinism second pass. **Read-only upstream artifact:**
`python/experiments/EXP-080/results/ready_map.csv` (dependency gate: the 15m/1h READY member set; hard-fail if
missing or if EXP-080 `run_metadata.json` does not record `READINESS_DELIVERED`).

**Outputs:**
```text
python/experiments/EXP-090/results/
- member_map.csv               # per-cell verdict: MEMBER / COVERAGE_EXCLUDED / CALIBRATION_UNDERPOWERED + reasons
- entry_coverage.csv           # entry count, entries/1k bars, non-warmup ATR-defined count, D8 flag, denominators
- exit_substrate_readiness.csv # per cell × arm: resolved fraction, tie-break incidence, determinism, fence flags
- fpr_mde_per_cell.csv         # per-cell FPR (×2 nulls × α, Wilson bounds) + event-level MDE (the EXP-093 margin)
- calibration_draws.parquet    # per-draw net-expectancy / Evidence rows (bounded columns)
- null_fpr_sanity.json         # moving-block null-FPR machinery sanity (n≥120 binding; small-n disclosed)
- run_metadata.json            # status, determinism, EXP-080 dependency gate, seeds/hashes, module versions,
                               #   holdout_untouched=true, counted_test_reads=0, candidate_slots=0
python/experiments/EXP-090/plots/   # ≤4 per the budget
```
`tqdm` over the 32-cell outer loop (and the calibration draw batches); per-cell memory bounded (do not retain all
domain frames simultaneously). Expected runtime: minutes–tens-of-minutes (the per-cell calibration draws are the
main cost — prefer conservative event-count tiers or vectorized draw batching over cutting draw counts below
precision).

### Standard Loading Pattern (TRAIN sub-stratum, holdout-fenced)

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob(f"timebars/timebars_{symbol}_*.parquet"))[-1]

total_rows = pl.scan_parquet(path).select(pl.len()).collect().item()
analysis_rows = int(total_rows * 0.7)          # first 70% = analysis set
train_cutoff = int(analysis_rows * 0.7)        # first 70% of analysis = TRAIN sub-split
train_1m = pl.scan_parquet(path).slice(0, train_cutoff).collect()
assert train_1m.get_column("CloseTime").is_sorted()
train_edge_ts = train_1m.get_column("CloseTime")[-1]
# build_domain_bars(train_1m, period, min_coverage=0.90)  # forward path + 1m fills clip at train_edge_ts
# analysis-TEST stratum (last 30% of analysis) NOT sliced; final-30% global holdout NEVER read
```

## Suggested Direction (non-binding)

Mirror EXP-080's readiness structure fused with EXP-044/EXP-070's per-cell calibration. Drive a single 32-cell
loop off the EXP-080 READY frame: (1) build CORE fade entries (reuse `mean_reversion_entries(...)["CORE"]`); (2)
build the new `xen.intrabar_fill` engine and resolve every frozen exit arm per event for readiness only
(determinism, causality, timestamp alignment, tie-break incidence — no expectancy); (3) run the per-cell synthetic
null/planted-edge calibration of the moving-block net-expectancy lower bound at each realized event count to emit
the per-cell FPR + finite-MDE map (the EXP-093 margin); then the determinism second pass and the ≤4 plots from
collected summaries. Everything gross-free and edge-free: **no exit screened, no expectancy computed on real
outcomes, no cell selected** — only that the bare-fade entry + the 1m exit-fill substrate reproduce, are causal
and holdout-fenced, and that the binding inference is powered (finite MDE) on each member cell EXP-091/092/093 will
rely on.
