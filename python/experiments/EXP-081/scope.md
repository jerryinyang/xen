# Experiment: EXP-081 — Per-Substrate Realized Return-Structure Characterization (4 Frozen Substrates × 46 Member Cells, 5-Year Data)

**Phase:** 018 (CF-CAPGEO-001 data-derived exit / capture geometry; checkpoint
`2026-06-20-018-capgeo-exit-geometry`, **G0 PASS 2026-06-21**) · **HYP:** HYP-002 ·
**Registry:** `CF-CAPGEO-001` Phase 018 batch (multiplicity-registry) ·
**Candidate slots:** 0 (characterization) · **TEST reads:** 0 counted (TRAIN-only descriptive read;
no TEST stratum sliced, no stratum-specific strategy inference).

**Counted-read precondition (Stage-1 check):** the INFR-003 5-year ledger
(`docs/signal-registry/test-read-ledger.md`, re-materialized 2026-06-21 on VAL-005 PASS) shows **all
16 instruments × {15m,1h,4h} = 48 strata at 0/2 counted reads, open** (EURUSD fully eligible, clean
slate — D8). **EXP-081 reads only the TRAIN sub-stratum** (`[0, train_cutoff)` = first 70% of the
analysis set = first 49% of the full 5-year file; EXP-074/075/077 precedent, operator decision
2026-06-22): the nested analysis-TEST stratum (last 30% of analysis) and the final-30% global holdout
are **never sliced or materialized**. It computes only TRAIN-only descriptive return-structure
geometry (no exit applied, no closed-trade screen, no stratum-specific selection or inference), so it
spends **0 counted TEST reads** and the ledger is **unchanged** (a TRAIN-only diagnostic, like
EXP-074/075). No TEST stratum is read, so no per-stratum tally is consumed.

**Analog:** EXP-047 (gross TRAIN-only move-size diagnostic) / EXP-055 (lifetime MFE/MAE availability) /
EXP-074 (TRAIN-only loss-tail characterization, 99-cell substrate). **Gating precondition:** **EXP-080
READINESS_DELIVERED 2026-06-22 (re-audit PASS)** — 184/192 substrate-cells READY; **member set =
46 instrument×domain cells** (US500-4h, JP225-4h `COVERAGE_EXCLUDED`, excluded with record); all member
cells `IN_BRACKET [15,8000]`; harami entry-identity holds ∀ cells.

**Context:** Second experiment of Phase 018, the **characterize** step of the
characterize → derive → test slate (design §2/§3, D0 §D2). Reads each frozen-entry substrate's
**realized post-entry path** on TRAIN to expose the return-structure features that define *what exit
fits* — capture-time geometry, time-to-peak, exhaustion magnitude, and (the inherited binding lesson)
**bimodality / left-tail shape**. Its per-cell statistics are the **frozen D3 inputs** that EXP-082's
mechanical exit-derivation rule consumes. **No exit, barrier, or P&L is applied here** (those are
EXP-082/083); the only outcomes are descriptive path-geometry distributions on real prices. The
binding referee suite is **not** invoked here (design §3); `ASS` expectancy/median/tail are reported
per cell **as non-binding discovery disclosure only**.

---

## Hypothesis / Exploratory Question

Exploratory characterization (no market-edge claim, no candidate screen): for each member
substrate-cell (4 substrates × 46 instrument×domain cells), the realized post-entry path of each
frozen-entry event — measured over a per-event **adaptive time cap** on **real prices**,
ATR-normalized — has a stable, estimable return-structure signature (favourable-capture geometry,
time-to-peak, adverse excursion, and minority-mass / left-tail shape) sufficient to **mechanically
derive** exit candidates (EXP-082) and to **disclose** whether the catastrophic-minority shape that
killed CF-HA-HARAMI-001 is present per cell.

There is **no pass/fail edge verdict**; the experiment verdict is **CHARACTERISATION_DELIVERED** — the
per-cell D3-input statistics, the minority-mass / left-tail companion read, the bimodality diagnostic,
and the `ASS` discovery disclosure are produced for every member substrate-cell, whatever their shape.

## Question

For each member substrate-cell, over the per-event adaptive-cap lookforward window on real prices:

1. **Favourable-capture geometry:** the lifetime MFE distribution (`MFE_med`, `MFE_q40`, ATR units).
2. **Capture-time geometry:** bars-to-peak-MFE distribution (`TTP_med`, `TTP_q75`).
3. **Adverse excursion:** the lifetime MAE distribution (`MAE_q90`, ATR units).
4. **Bimodality / catastrophe boundary:** the antimode/dip location `m_anti` of the MAE distribution
   (dominant-vs-catastrophic-minority split; `NaN` if unimodal) via Hartigan dip + robust 2-component
   split.
5. **Minority-mass / left-tail read (the detector `ASS` lacks):** left-tail-mass `tailmass` (fraction of
   per-event outcomes below the catastrophe boundary) and `q05` of the per-event realized outcome.
6. **`ASS` discovery disclosure (non-binding):** per-cell `ASS` expectancy + median + tail readout on
   the per-event gross realized outcome (real prices), reported alongside as interpretation only —
   honoring D6 Guard (i) (defer to median at effective-n ≤ 60 on bimodal/asymmetric strata) and the D7
   bracket (all member cells `IN_BRACKET`).
7. **Harami entry identity (disclosure):** confirm `SUB-HARAMI-PARTIAL-V2A` and `SUB-HARAMI-V2A-ADVNONE`
   characterizations coincide per cell (they share one entry population — EXP-080), so their geometry is
   identical by construction.

## Scope Boundaries

- **Data Views:** 1-minute time bars from the **VAL-005-admitted 5-year dataset**
  (`data/timebars/timebars_<SYMBOL>_*.parquet`, 2021-06-02 → 2026-06-21), aggregated to **15m, 1h, 4h**
  via the **holdout-fenced `xen.domain_bars.build_domain_bars`** (`min_coverage=0.90` + analysis-slice
  boundary fence, VAL-005 G1). Heiken Ashi candles (harami substrates) via `xen.heiken_ashi_generator`.
  No Line Break / Renko.
- **Substrates (four, frozen at D1; none tuned)** — reuse the EXP-080 frozen harness
  `xen.capgeo_substrates` unchanged (entry events only):
  1. **`SUB-AVWAP`** — CF-AVWAP-001 final (EXP-028/029 frozen; `xen.avwap`).
  2. **`SUB-HARAMI-PARTIAL-V2A`** — CF-HA-HARAMI-001 `N-PARTIAL-V2A` entry (MA(20,50)-native
     `/STRONG-STAT`-conditioned HA harami; EXP-068 frozen).
  3. **`SUB-HARAMI-V2A-ADVNONE`** — same conditioned-harami entry population (identical to (2) per
     EXP-080; reported separately, geometry coincides by construction).
  4. **`SUB-RANDOM`** — fixed-seed matched-random entry (the attribution null), matched per cell to
     each real substrate's count, reproduced byte-identically from the EXP-080 `SEED_RANDOM`.
- **Grid (member set):** 4 substrates × **46 instrument×domain member cells** = **184 substrate-cells**.
  The 46 cells are the EXP-080 READY member set (16 instruments × {15m,1h,4h} **minus** US500-4h and
  JP225-4h, both `COVERAGE_EXCLUDED`). No DE30.
- **Lookforward window (per-event adaptive time cap — operator decision 2026-06-22, FROZEN here):**
  each event's realized path is measured over `[entry, entry + cap]` where `cap` is the **adaptive
  per-move time cap** computed from the substrate's own trailing move-duration structure, reusing the
  **validated** `xen.expectancy.adaptive_time_caps_by_epoch` (≡ `xen.capture_barriers.time_caps`
  duration semantics; EXP-068/070 frozen constants `TIMECAP_*`). Warmup events (fewer than `min_moves`
  prior durations → no cap) are disclosed and excluded from quantiles, never silently capped. The
  per-substrate instantiation of the move structure feeding the cap (and `SUB-RANDOM` inheriting its
  matched real substrate's per-cell cap distribution) is specified and frozen in the Stage-2 analysis
  plan; the **principle** (adaptive per-move cap, validated semantics, no grid search) is frozen by
  this scope. The cap never reads beyond the TRAIN sub-stratum (forward resolution clips at the TRAIN
  edge; no TEST/holdout row is touched).
- **Time range:** **first 70% of the analysis set only** (`[0, train_cutoff)`,
  `train_cutoff = int(analysis_rows * 0.7)`, `analysis_rows = int(total_rows * 0.7)`) — the nested
  TRAIN sub-split. The analysis-TEST stratum (last 30% of analysis) is **not sliced**; the final-30%
  global holdout is **never** loaded, inspected, counted, plotted, or used (only Parquet metadata
  locates the split). Forward path resolution clips at the TRAIN edge.
- **Global holdout:** excluded from all analysis (mandatory). Never a fold; not read here.
- **Look-ahead bias prevention:** domain aggregation emits completed windows only; HA generation and
  the ported detectors are sequential/causal; the adaptive cap at `t_i` uses only move durations
  confirmed strictly before `t_i`; the realized path uses only bars at or after entry within the cap;
  all ordering/alignment by `CloseTime` (real time), never bar index. `SUB-RANDOM` RNG never consults
  future data.
- **Real-price discipline (binding):** every MFE / MAE / TTP / outcome / ATR figure is on **real**
  domain OHLC (`RealOpen/High/Low/Close` ≡ the real domain bars). The harami detector runs on HA
  (synthetic) candles for *entry detection only*; **no return, capture, excursion, or outcome metric
  uses HA or any synthetic price**.
- **Exclusions:** no exit / barrier / target / stop / trailing applied (EXP-082/083); no exit
  derivation (EXP-082); no separability gate, frozen referee suite, or binding `ASS` adjudication (no
  pass/reject/admit decision rests on anything here — design §3/§5); no parameter sweep or tuning of
  any substrate or of the cap (all frozen); no cross-instrument / cross-domain / cross-substrate
  pooling as a binding statistic (per-stratum default, LESSON-001; any pooled figure is disclosure
  only); no TEST-stratum-specific inference or holdout contact; nothing is tuned or frozen against any
  EXP-081 output beyond the predeclared mechanical D3 mapping (EXP-082 freezes the rule, not the story).

## The Measurement (per substrate-cell, per event, over the adaptive cap)

For every member substrate-cell, for each frozen-entry event whose cap is non-warmup:

1. **Per-event ATR normalization:** Wilder ATR(14) (`ATR_PERIOD=14`, frozen) on real domain bars,
   sampled at the entry bar; all distances divided by that ATR. ATR-undefined (warmup) events are
   disclosed and excluded.
2. **Lifetime MFE / MAE (ATR):** the maximum favourable and maximum adverse excursion of the real
   domain OHLC over `[entry+1, entry+cap]`, direction-signed by the substrate's entry direction.
3. **Time-to-peak (TTP, bars):** the number of domain bars from entry to the bar realizing the lifetime
   MFE peak.
4. **Per-event realized outcome (ATR):** the real-price return at the cap bar's close
   (direction-signed), the readout the minority-mass / `q05` / `ASS` discovery statistics summarize.

Then per substrate-cell, the **D3-input distribution statistics** (frozen list, D0 §D3):
`MFE_med`, `MFE_q40` (quantiles); `TTP_med`, `TTP_q75` (quantiles); `MAE_q90` (quantile); `m_anti`
(Hartigan dip + robust 2-component split of the MAE distribution; `NaN` if unimodal); `tailmass`
(fraction of realized outcomes below the catastrophe boundary `median − K_tail·MAD`, `K_tail = 3.0`
frozen at the D9 bite-check), `q05` (q05 of the realized outcome). Plus the **`ASS` discovery readout**
(expectancy + median + tail) per cell as non-binding disclosure.

## Metric Denominators & Zero-Baseline (predeclared, before implementation)

- **Quantiles / shape statistics:** denominator = the cell's count of **non-warmup, ATR-defined
  events** within TRAIN (disclosed per cell). A cell below the **≥30-event floor** (D9 §D3) reports its
  statistics as `UNDERPOWERED_DISCLOSED` and **forms no derived candidate** at EXP-082 for that cell
  (D9); it is never silently dropped.
- **`tailmass`:** (count of events with realized outcome < catastrophe boundary) / (cell event count);
  a cell with zero tail events reports `0.0` with its denominator shown, never `0/0`.
- **`m_anti`:** reported as `NaN` (unimodal / dip not resolved) with the dip statistic and p-value
  disclosed; the D3 adverse leg falls back to `MAE_q90` wherever `m_anti` is `NaN` (D9 disclosure —
  `m_anti` is power-limited at realistic cell sizes; `MAE_q90` fallback always well-defined).
- **`ASS` discovery expectancy:** reported with its bootstrap CI; **deferred to the median** at
  effective-n ≤ 60 on bimodal/asymmetric strata (D6 Guard (i)); excluded with disclosure for any
  out-of-bracket cell (none expected — EXP-080 all `IN_BRACKET`). Never expressed as a percentage over a
  zero baseline.
- **Warmup / undefined:** warmup-cap and ATR-undefined events are counted and disclosed per cell, not
  folded into any quantile.

## Frozen Constants (predeclared at D0/G0; recorded here pre-data-contact)

- **Substrate parameters:** AVWAP — CF-AVWAP-001 final (EXP-028/029); harami — MA(20,50)-native
  `/STRONG-STAT`-conditioned HA harami (EXP-068). No substrate parameter varied (`xen.capgeo_substrates`
  unchanged).
- **Adaptive cap:** `xen.expectancy.adaptive_time_caps_by_epoch` with the frozen `TIMECAP_WINDOW`,
  `TIMECAP_K`, `TIMECAP_FLOOR`, `TIMECAP_MIN_MOVES` (EXP-068/070); no cap tuning.
- **ATR:** Wilder ATR period **14** (`ATR_PERIOD`, frozen).
- **Catastrophe boundary:** `K_tail = 3.0` (D9 bite-check frozen); event floor **≥ 30**.
- **Seeds:** `SEED_RANDOM` (the `SUB-RANDOM` seed) and any bootstrap seed fixed and recorded in
  `run_metadata.json`; a second full pass is byte-identical (D10).

## Success / Failure / Inconclusive Criteria

- **CHARACTERISATION_DELIVERED (experiment verdict):** for all 184 member substrate-cells the per-cell
  D3-input statistics, the minority-mass / `q05` companion read, the `m_anti` bimodality diagnostic, the
  `ASS` discovery disclosure, and the harami entry-identity disclosure are produced (with per-cell event
  counts, warmup/undefined disclosures, and `UNDERPOWERED_DISCLOSED` flags), deterministically.
- **Cell-level INCONCLUSIVE:** a cell below the ≥30-event floor is `UNDERPOWERED_DISCLOSED` (recorded,
  forms no EXP-082 derived candidate), not a failure.
- **Evidence AGAINST (process-level — HALT):** non-determinism on **any** cell (second-pass statistics
  not frame-identical), or a real-price-discipline / look-ahead / holdout-fence violation, or a
  reconciliation break of the reused EXP-080 frozen entry populations (entry counts must match EXP-080
  exactly per cell). Any of these halts and routes to a fix — they indicate an implementation bug, not
  a data shape.
- There is **no edge / pass / viability verdict** (0 slots, gross, TRAIN-only); shape is reported, not
  adjudicated.

## Complexity Budget

- **Max statistical tests: 2** — the Hartigan dip test (`m_anti` / bimodality) and the `ASS` discovery
  bootstrap (disclosure). Everything else descriptive (quantiles, tail-mass).
- **Max visualisations: 5** — (i) per-substrate MFE_med heatmap (46-cell, small-multiple by domain);
  (ii) TTP_med/TTP_q75 capture-time heatmap; (iii) MAE distribution with `m_anti` / catastrophe-boundary
  overlay for representative cells; (iv) `tailmass` heatmap by substrate (incl. `SUB-RANDOM` baseline);
  (v) per-substrate realized-outcome distribution small-multiples flagging bimodal cells. All from the
  single analysis pass's bounded plot inputs (no reloads).
- **Max new code modules: ≤ 2** under `python/src/xen/` — only if logic does not fit cleanly in the
  experiment script: a reusable **path-geometry** computation (lifetime MFE/MAE + TTP over an adaptive
  cap on real OHLC) and a **shape-diagnostic** helper (`m_anti` dip/2-component split + `tailmass`/`q05`
  + catastrophe boundary). **Reuse** `xen.domain_bars`, `xen.capgeo_substrates`,
  `xen.heiken_ashi_generator`, `xen.expectancy` (adaptive cap), `xen.capture_barriers`, `xen.wf`
  unchanged (no edits to frozen generators/detectors).

## Data Requirements

Per instrument: lazy `pl.scan_parquet` of the single VAL-005-admitted 5-year file; read total row
count from metadata; `analysis_rows = int(total_rows * 0.7)`; `train_cutoff = int(analysis_rows * 0.7)`;
collect only the first `train_cutoff` file-order 1-minute rows; assert sorted by `CloseTime`; build
domain bars via `build_domain_bars`; generate HA candles (harami); reproduce the frozen entry events
via `xen.capgeo_substrates` (assert per-cell entry counts reconcile to EXP-080 on the TRAIN slice);
compute per-event adaptive caps and realized path geometry on real OHLC; aggregate per-cell D3 inputs +
companion shape read + `ASS` discovery disclosure; run the bounded determinism second pass. Outputs: a
results parquet (per-substrate-cell D3-input + shape table), a per-event geometry parquet (bounded,
for reproducibility), an `ASS`-discovery JSON, `run_metadata.json` (seeds, hashes, frozen-constant
versions, EXP-080 reconciliation), and the ≤5 bounded plots from collected summaries. `tqdm` over the
184-substrate-cell outer loop; per-cell memory bounded (do not retain all domain frames). Expected
runtime: minutes–tens-of-minutes.

### Standard Loading Pattern (TRAIN sub-stratum, holdout-fenced)

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob(f"timebars/timebars_{symbol}_*.parquet"))[-1]

total_rows = pl.scan_parquet(path).select(pl.len()).collect().item()
analysis_rows = int(total_rows * 0.7)          # first 70% = analysis set
train_cutoff = int(analysis_rows * 0.7)        # first 70% of analysis = TRAIN sub-split
train = pl.scan_parquet(path).slice(0, train_cutoff).collect()
assert train.get_column("CloseTime").is_sorted()
# analysis-TEST stratum (last 30% of analysis) NOT sliced; final-30% holdout NEVER read
# build_domain_bars(train, tf, min_coverage=0.90)  # forward path resolution clips at TRAIN edge
```

## Suggested Direction (non-binding)

Mirror EXP-074's TRAIN-only characterization structure. Drive the 184-substrate-cell loop off the
EXP-080 frozen-entry harness, asserting entry-count reconciliation to EXP-080 on the TRAIN slice before
any geometry read. Compute the adaptive cap once per (substrate, cell) via the reused
`adaptive_time_caps_by_epoch`, then resolve lifetime MFE/MAE/TTP on real OHLC over each event's cap,
clipping forward resolution at the TRAIN edge. Emit the frozen D3 inputs, the minority-mass / `q05`
companion read, the `m_anti` dip diagnostic, and the non-binding `ASS` discovery readout per cell;
report the harami entry-identity coincidence explicitly. Everything gross, TRAIN-only, real-price: no
exit, no edge verdict — only the return-structure signature EXP-082 will mechanically convert into exit
candidates.
