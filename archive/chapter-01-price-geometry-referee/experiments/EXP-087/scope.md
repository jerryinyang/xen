# Experiment: EXP-087 — Screen X: Cross-Sectional Relative-Strength Availability (Phase 019 Family-Selection)

**Phase:** 019 (Family-Selection Availability Screen; checkpoint
`2026-06-22-019-family-selection-availability-screen`, **G0 PASS 2026-06-22**, D2b admission-gate bite-check
**GREEN**) · **Axis:** **X — cross-sectional relative strength** · **HYP:** `CF-XSECT-001/HYP-001` ·
**Registry:** Phase 019 batch (multiplicity-registry, EXP-087 row); CF-XSECT-001 `DRAFT — PENDING-SELECTION`
(`candidate-families/family-selection-phase-019.md`) · **Candidate slots:** 0 (family selection, not
candidate screening) · **TEST reads:** 0 counted (TRAIN-only availability disclosure; no TEST stratum
sliced, no stratum-specific inference).

**This is NOT a candidate screen and NOT a tradability/edge claim.** It is a family-agnostic *availability*
read whose only deliverable is an **admit / exonerate / inconclusive** disposition for the **cross-sectional ×
directional** cell of the availability 2×2 (design §2), backed by cheap Δ-over-random numbers. No slot is
consumed; no family is opened here (an `ADMITTED` axis opens at its own future G0/D0). The binding
admit/exonerate adjudication is **G-019**, after the slate; EXP-087 produces the realized statistics the
G-019 rubric reads.

**D0 provenance (frozen):** D1–D6 ratified and frozen 2026-06-22 (`D0-predeclarations.md`); the Screen-X
cross-sectional conditioning (two primitives, lookback, cadence, universe synchronization) concretized by
operator at scoping in **`D0-amendment-002-screen-x-conditioning-freeze.md`**. Nothing in this scope tunes,
selects, or freezes any constant against data — all axis-conditioning definitions and the D2/D3
thresholds/endpoints were frozen before any result-producing code (G-019 checklist §7: no goalpost-moving).

**Counted-read precondition (Stage-1 check):** the INFR-003 5-year ledger
(`docs/signal-registry/test-read-ledger.md`, re-materialized 2026-06-21 on VAL-005 PASS) shows **all 16
instruments × {15m,1h,4h} = 48 strata at 0/2 counted reads, open**. **EXP-087 reads only the TRAIN
sub-stratum** (`[0, train_cutoff)`, `train_cutoff = int(int(total_rows·0.7)·0.7)` = first 70% of the analysis
set = first 49% of each 5-year file; EXP-074/075/080/081/086 precedent): the nested analysis-TEST stratum
(last 30% of analysis) and the final-30% global holdout are **never sliced or materialized** (forward path
resolution clips at the TRAIN edge; the cross-section is built only from TRAIN bars and the forward-fill
consults no TEST/holdout bar). It makes **no stratum-specific selection or inference** — a family-agnostic
availability disclosure over the full TRAIN region of each cell — so it spends **0 counted TEST reads** and
the ledger is **unchanged** (D4; EXP-080/081 convention). The permuted-axis null (D2b) shuffles conditioning
labels *within* the same TRAIN region and reads no additional data.

**Analog:** EXP-081 (per-substrate realized return-structure characterization), via the EXP-086 Screen-M
clone. Screen X is an **EXP-081/EXP-086 clone** with the *information axis* swapped (single-series
compression primitives → **cross-sectional relative-strength** conditioning) and the *availability endpoint*
set to the **directional-favourable** `MFE_med` Δ-over-random (D3.X — the cross-sectional anomaly is
directional by construction; not the split magnitude reads of Screen M), adjudicated by the **D2b
multiplicity-adjusted permuted-axis admission gate** rather than reported as raw geometry. **Gating
precondition:** EXP-080 `READINESS_DELIVERED` (re-audit PASS) — **member set = 46 instrument×domain cells**
(US500-4h, JP225-4h `COVERAGE_EXCLUDED`); the matched-random `SUB-RANDOM` scaffolding and the readiness frame
are reused unchanged. The admission-gate module built in EXP-086 (per-cell beats-random + permuted-axis null
+ `S*` + Holm) is reused unchanged.

---

## Hypothesis / Exploratory Question

**Single falsifiable question (design §3, the cross-sectional × directional cell of the 2×2):**

> Conditioned on **cross-sectional relative strength** (basket-relative momentum / divergence rank across the
> synchronized 16-instrument universe), does an entry's signal-conditional **directional-favourable**
> availability (`MFE_med`, ATR-normalised, on real prices) beat a matched within-instrument random control by
> more than the **multiplicity-adjusted permuted-axis null** (D2b) would produce at the realized cell count?

**Prior is a mechanism bet, not in-programme evidence** (candidate-family §CF-XSECT-001, design §5.X): every
family so far was **single-series** ("does *this* instrument move after the signal"); the dead 2×2 cell is
specifically single-series price geometry. Cross-sectional relative strength sources its information from the
**relationship between instruments** — the one axis the programme has never varied, constructible from the
existing VAL-005 dataset at **zero new collection**. It is the a-priori favourite on mechanism grounds but
must **earn** admission on the screen like any other axis. **Multiplicity caution (binding):** ranking over 16
instruments manufactures the **most** cells of any screen → the D2b permuted-axis gate matters most here; a
lucky single cell must not admit the axis.

**There is no edge/pass/viability verdict and no candidate adjudication here.** The experiment verdict is
**`SCREEN_DELIVERED`** — the per-cell `MFE_med` Δ-over-random table, the axis-level permuted-null statistic
(`S_X`, `S*`, axis permutation p), the ranking z-score, and the descriptive D2a band are produced
deterministically for the cross-sectional axis; **admit / exonerate / inconclusive is adjudicated at G-019**
under the frozen D5 rule (with the cross-axis Holm step-down applied over the {M, X, (F)} slate). EXP-087
additionally reports a **provisional single-axis** disposition (realized `S_X` vs `S*` and the unadjusted axis
p) for transparency, captioned **non-binding** pending G-019.

## Questions (per primitive, family-agnostic directional-favourable availability)

For each member cell, over the per-event adaptive-cap lookforward window on real prices, conditioned on each
of the two frozen cross-sectional primitives (`COND-XSRANK`, `COND-XSDIV`) and the matched `SUB-RANDOM`
control:

1. **Favourable availability:** per-cell Δ-over-random of the directional-favourable `MFE_med` (ATR), where
   the entry direction is the cross-sectional sign (LONG on relative strength / SHORT on relative weakness);
   per-cell "beats random" = one-sided lower confidence bound of the Δ > 0 (the binding per-cell test that the
   D2b gate aggregates — bite-check §A).
2. **Axis-level admission statistic (D2b, binding input to G-019):** `S_X = #cells-beat-random`; the
   **permuted-axis null** (shuffle which TRAIN timestamps are "extreme-decile signal" vs not, preserving
   per-cell event counts and the regime/direction match, recompute the full per-cell Δ table) → `S*` = the
   `Q95` permutation ceiling and the axis permutation p-value; ranking z-score
   `(S_X − mean(S_perm)) / sd(S_perm)`.
3. **Descriptive D2a band (reporting only, NON-BINDING):** the cells-beat-random count vs the EXP-081
   coin-flip baseline (≈17/46–28/46).

**No magnitude-budget / two-sided-cost check** (that is a Screen-M magnitude-admission gate, D3.M): Screen X's
endpoint is directional-favourable availability, so a Screen-X admission routes to a **directional**
cross-sectional family (CF-XSECT-001), not the long-vol harvest model.

## Scope Boundaries

- **Data Views:** 1-minute time bars from the **VAL-005-admitted 5-year dataset**
  (`data/timebars/timebars_<SYMBOL>_*.parquet`, 2021-06-02 → 2026-06-21), aggregated to **15m, 1h, 4h** via
  the **holdout-fenced `xen.domain_bars.build_domain_bars`** (`min_coverage=0.90` + analysis-slice boundary
  fence, VAL-005 G1). No Heiken Ashi / Line Break / Renko (the cross-sectional conditioning is computed from
  real domain-bar returns; no synthetic chart type is involved).
- **Conditioning primitives (two, frozen at D0-amendment-002; neither tuned):**
  1. **`COND-XSRANK`** — at each domain timestamp on the forward-filled union grid, rank every instrument's
     trailing **20-domain-bar** real-price log return across the synchronized 16-instrument cross-section;
     entry fires LONG on **top-decile** relative strength, SHORT on **bottom-decile** relative weakness.
  2. **`COND-XSDIV`** — the same trailing 20-bar return **minus the equal-weight basket mean** across the
     cross-section; entry fires LONG/SHORT on **top/bottom decile** of the divergence distribution.
  Both directional by construction; lookback **20 frozen**; both tails; causal (rank/divergence at `t` uses
  only returns over bars completed strictly ≤ `t`).
- **Universe synchronization (frozen):** the cross-section is the **16 VAL-005 instruments** (no DE30),
  evaluated on a **forward-filled union timestamp grid** per domain — each instrument contributes its **last
  completed bar** (strictly causal forward-fill, no future bar) when a union timestamp falls between its own
  bar closes; the decile membership read per (instrument, domain) cell so the cell count matches the
  single-series screens for like-for-like admission-gate calibration (`C=46`). The forward-fill never crosses
  the TRAIN edge.
- **Matched-random control (frozen, reused):** `SUB-RANDOM` — fixed-seed random-timing entries on the same
  regime/direction within the same cell, matched count, reproduced from the EXP-080/081 `SEED_RANDOM`
  construction. The random control inherits the **same per-cell directional mix** as the conditioned set (so
  the Δ isolates conditioning, not direction). This is the **descriptive** per-cell baseline (D2a); the
  **binding** null is the permuted-axis gate (D2b), distinct.
- **Grid (member set):** 2 conditioning primitives × **46 instrument×domain member cells** = 92 conditioned
  cells (plus the matched `SUB-RANDOM` per cell). The 46 cells are the EXP-080 READY member set (16
  instruments × {15m,1h,4h} **minus** US500-4h and JP225-4h, both `COVERAGE_EXCLUDED`). No DE30. The realized
  cell count per axis matches the bite-check `C=46`, so the frozen admission gate applies as calibrated.
- **Lookforward window (per-event adaptive time cap — reused, FROZEN):** each event's realized path is
  measured over `[entry, entry + cap]` with the **validated** `xen.expectancy.adaptive_time_caps_by_epoch`
  duration semantics (EXP-068/070 frozen `TIMECAP_*`), the same cap EXP-081/086 used (`SUB-RANDOM` inherits
  its matched cell's cap distribution). The **principle** (adaptive per-move cap, validated semantics, no grid
  search) is frozen here; the cap never reads beyond the TRAIN sub-stratum (forward resolution clips at the
  TRAIN edge; no TEST/holdout row is touched).
- **Time range:** **first 70% of the analysis set only** (`[0, train_cutoff)`,
  `train_cutoff = int(analysis_rows · 0.7)`, `analysis_rows = int(total_rows · 0.7)`) — the nested TRAIN
  sub-split, **per instrument** (the cross-section is built from each instrument's own TRAIN region; the union
  grid is the union of TRAIN-only timestamps). The analysis-TEST stratum is **not sliced**; the final-30%
  global holdout is **never** loaded, inspected, counted, plotted, or used (only Parquet metadata locates the
  split).
- **Global holdout:** excluded from all analysis (mandatory). Never a fold; not read here.
- **Look-ahead bias prevention:** domain aggregation emits completed windows only; the 20-bar return, rank,
  and divergence at `t` use only bars completed strictly ≤ `t`; the union-grid forward-fill uses each
  instrument's last *completed* bar (never a future bar); the adaptive cap at `t_i` uses only move durations
  confirmed strictly before `t_i`; the realized path uses only bars at or after entry within the cap; all
  ordering/alignment by `CloseTime` (real time), never bar index; `SUB-RANDOM` and the permutation RNG never
  consult future data.
- **Real-price discipline (binding):** every return / MFE / outcome / ATR figure — the cross-sectional 20-bar
  return, the basket mean, and the `MFE_med` endpoint — is on **real** domain OHLC (`RealOpen/High/Low/Close`
  equivalent for time bars). No synthetic (HA/Renko) price enters any conditioning or availability metric (D6).
- **Exclusions:** no exit / barrier / target / stop / trailing and no exit derivation (out of phase — this is
  availability only); no portfolio / market-neutral / rebalanced-basket construction (deferred to the
  family's own post-admission G0/D0 — Screen X is the cheap per-event availability read, candidate-family
  §CF-XSECT-001 exclusions); no frozen referee suite, separability gate, or binding `ASS` adjudication (no
  pass/reject/admit decision rests on anything *here*; admission is G-019 mechanical); no parameter sweep or
  tuning of either primitive, the lookback, the decile threshold, the cap, or the gate (all frozen); no
  cross-instrument / cross-domain pooling as a binding statistic (per-stratum default, LESSON-001; any pooled
  figure is disclosure only); no TEST-stratum-specific inference or holdout contact; no Screen-M split
  magnitude reads or magnitude-budget (Screen X is directional-favourable only).

## The Measurement (per conditioning primitive, per cell, per event, over the adaptive cap)

For every member cell, for each conditioned event and each matched-random event whose cap is non-warmup:

1. **Cross-sectional conditioning (per primitive):** at each TRAIN union-grid domain timestamp, compute every
   instrument's trailing 20-bar real-price log return; form the cross-sectional rank (`COND-XSRANK`) or the
   divergence-from-basket-mean (`COND-XSDIV`); an event fires for (instrument, domain, timestamp) when that
   instrument is in the top decile (LONG) or bottom decile (SHORT). Entry direction = the decile sign.
2. **Per-event ATR normalization:** Wilder ATR(14) (`ATR_PERIOD=14`, frozen) on real domain bars at the entry
   bar; all distances divided by that ATR. ATR-undefined (warmup) events are disclosed and excluded.
3. **Directional-favourable `MFE` (ATR):** maximum favourable excursion in the entry direction of the real
   domain OHLC over `[entry+1, entry+cap]`; the per-cell endpoint is `MFE_med` (median), as EXP-081's
   favourable-availability read.
4. **Matched random:** `SUB-RANDOM` events drawn at the cell's matched count with the same per-cell
   directional mix; their `MFE` measured identically over the matched cap distribution.

Then per cell the **availability statistic** (frozen, D3.X): `MFE_med` Δ-over-random with its one-sided
bootstrap lower bound ("beats random"). Then per axis: `S_X = #cells-beat-random`, the permuted-axis null,
`S*`, axis permutation p, and the ranking z-score.

## Metric Denominators & Zero-Baseline (predeclared, before implementation)

- **Per-cell summary / Δ statistics:** denominator = the cell's count of **non-warmup, ATR-defined** events
  within TRAIN (disclosed per cell, separately for the conditioned set and the matched-random set). A cell
  below the **≥30-event floor** reports `UNDERPOWERED_DISCLOSED`, contributes its descriptive numbers, and is
  **excluded from the `S = #cells-beat-random` count** for the binding gate (it cannot reliably "beat
  random") — recorded, never silently dropped.
- **"Beats random" per cell:** one-sided lower confidence bound of the per-cell `MFE_med` Δ-over-random > 0
  (bootstrap; the production analog of the bite-check normal-approx test). Reported with the bound; never a
  percentage over a zero baseline.
- **Permutation null:** `S*` and the axis p-value are computed at the **realized** cell count (post
  `UNDERPOWERED` exclusion); if the permuted null cannot separate at that count (`S*` ≥ the max attainable
  `S`), the axis read is `INCONCLUSIVE` (no power) — a disclosed outcome, not an admission.
- **Decile membership / ties:** the top/bottom-decile cutoff is computed on the realized cross-sectional
  distribution at each timestamp; tie-handling (rank ties at the decile boundary) is resolved by a frozen,
  deterministic rule (fixed in the Stage-2 analysis plan — e.g. `<=`/`>=` inclusive boundary), disclosed, not
  tuned. A timestamp with fewer than a minimum number of synchronized instruments to define a decile is
  excluded and disclosed (never forced).
- **Warmup / undefined:** warmup-cap, ATR-undefined, and insufficient-cross-section events are counted and
  disclosed per cell, not folded into any statistic.

## Frozen Constants (predeclared at D0/G0 + D0-amendment-002; recorded here pre-data-contact)

- **Conditioning primitives:** `COND-XSRANK` (cross-sectional 20-bar-return rank, top/bottom decile LONG/SHORT)
  and `COND-XSDIV` (20-bar return minus equal-weight basket mean, top/bottom decile). Lookback **20** domain
  bars; both tails; neither varied.
- **Universe:** 16 VAL-005 instruments (no DE30); forward-filled union timestamp grid per domain; causal
  last-completed-bar fill.
- **Matched-random:** `SUB-RANDOM` (EXP-080/081 construction, `SEED_RANDOM`), matched count per cell, same
  directional mix.
- **Adaptive cap:** `xen.expectancy.adaptive_time_caps_by_epoch` with frozen `TIMECAP_*` (EXP-068/070); no
  cap tuning.
- **ATR:** Wilder ATR period **14** (`ATR_PERIOD`).
- **Event floor:** ≥ 30 non-warmup ATR-defined events per cell for binding-gate inclusion.
- **Admission gate (D2b, GREEN bite-check, unchanged):** per-cell CI_low>0 → `S = #cells-beat-random` →
  permuted-axis null (`N_PERM` at production scale, candidate 1000 → confirm/lift in Stage 2) → `S* = Q95`
  (axis FWER 0.05) → **cross-axis Holm** over {M, X, (F)} **applied at G-019** (EXP-087 emits the per-axis p).
  Sensitivity band FWER ∈ {0.025, 0.05, 0.10} reported as a pre-registered robustness sweep, not a selection.
- **Seeds:** `SEED_RANDOM`, the bootstrap seed, and the permutation seed-stream fixed and recorded in
  `run_metadata.json`; a second full pass (including the permutation null) is byte-identical (D6).
- **Ranking metric (frozen, used at G-019):** axis-level permutation z-score
  `(S_X − mean(S_perm)) / sd(S_perm)`, tie-broken by trimmed-mean per-cell Δ.

## Success / Failure / Inconclusive Criteria

- **`SCREEN_DELIVERED` (experiment verdict):** for both conditioning primitives across all 46 member cells,
  the per-cell `MFE_med` Δ-over-random table, the per-cell event-count / warmup / `UNDERPOWERED_DISCLOSED`
  disclosures, the axis-level `S` / `S*` / permutation-p / ranking z-score, and the descriptive D2a band are
  produced deterministically for the cross-sectional axis. The **provisional** single-axis
  admit/exonerate/inconclusive disposition is reported, captioned **non-binding pending the G-019 cross-axis
  Holm adjudication**.
- **Axis-read `INCONCLUSIVE`:** the permuted null cannot separate at the realized cell count (no power) —
  disclosed; neither admit nor exonerate.
- **Evidence AGAINST (process-level — HALT):** non-determinism on **any** cell or on the permutation null
  (second-pass statistics not frame-identical), or a real-price-discipline / look-ahead / holdout-fence
  violation, or a reconciliation break of the reused `SUB-RANDOM` matched-count construction, or a
  cross-sectional alignment defect (a non-causal forward-fill / future-bar leak). Any of these halts and
  routes to a fix — they indicate an implementation bug, not a data shape.
- There is **no edge / tradability / candidate verdict** (0 slots, gross, TRAIN-only); availability is
  reported, admission is adjudicated at G-019.

## Complexity Budget

- **Max statistical tests: 2** — (i) the per-cell `MFE_med` Δ-over-random bootstrap lower bound ("beats
  random"); (ii) the permuted-axis admission null (the binding D2b gate). (Screen X has no dip test or
  magnitude-budget — it is the directional-favourable single-read clone, lighter than Screen M.)
- **Max visualisations: 4** — (i) `MFE_med` Δ-over-random heatmap (46-cell, by domain) per primitive;
  (ii) the permuted-axis null distribution with realized `S_X` and `S*` overlaid; (iii) representative
  conditioned-vs-random favourable-excursion distributions for the densest cells; (iv) cells-beat-random count
  vs the D2a coin-flip band, per primitive. All from the single analysis pass's bounded plot inputs (no
  reloads).
- **Max new code modules: ≤ 1** under `python/src/xen/` — a **cross-sectional-conditioning** entry module
  (`COND-XSRANK` + `COND-XSDIV` over the forward-filled union grid, returning EXP-080-compatible `EntrySet`
  structures with entry direction). **Reuse unchanged:** the EXP-086 availability-admission-gate module
  (per-cell beats-random + permuted-axis null + `S*` + Holm), `xen.domain_bars`, `xen.capgeo_substrates`
  (`SUB-RANDOM`, `_real_ohlc`, `ATR_PERIOD`), `xen.capgeo_geometry` (`lifetime_path_geometry` for directional
  `MFE`), `xen.expectancy` (adaptive cap), `xen.ass` (bootstrap CIs), `xen.zigzag` (`wilder_atr`). No edits to
  frozen generators/detectors or the EXP-086 gate module.

## Data Requirements

Per instrument: lazy `pl.scan_parquet` of the single VAL-005-admitted 5-year file; read total row count from
metadata; `analysis_rows = int(total_rows · 0.7)`; `train_cutoff = int(analysis_rows · 0.7)`; collect only
the first `train_cutoff` file-order 1-minute rows; assert sorted by `CloseTime`; build domain bars via
`build_domain_bars`. **Cross-section build:** for each domain, form the forward-filled union timestamp grid
across all 16 instruments' TRAIN domain bars; compute per-instrument trailing 20-bar returns; form
`COND-XSRANK` rank and `COND-XSDIV` divergence; mark top/bottom-decile events with direction. Reproduce the
matched `SUB-RANDOM` events per cell (matched count, same directional mix); compute per-event adaptive caps
and directional `MFE` on real OHLC; aggregate per-cell `MFE_med` Δ-over-random; build the permuted-axis null
and `S` / `S*` / axis-p / ranking z-score; run the bounded determinism second pass (including the permutation
stream). Outputs: a per-cell availability parquet/CSV (both primitives, with denominators + `UNDERPOWERED`
flags), a per-axis admission-statistic JSON (`S`, `S*`, perm-p, sensitivity band, provisional disposition,
ranking z-score), a bounded per-event geometry parquet (reproducibility), `run_metadata.json` (seeds, hashes,
frozen-constant versions, `holdout_untouched=true`, `counted_test_reads=0`, `candidate_slots=0`), and the ≤4
bounded plots. `tqdm` over the member-cell × primitive outer loop; per-cell memory bounded (do not retain all
domain frames; the union grid is built per domain, then released). Expected runtime:
minutes–tens-of-minutes (the permutation null at production `N_PERM` is the main cost — confirm MC stability
at the bite scale, then lift before the binding read).

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
# build_domain_bars(train, period, min_coverage=0.90)  # forward path clips at TRAIN edge
# cross-section: union grid is the union of TRAIN-only domain-bar CloseTimes across instruments
```

## Suggested Direction (non-binding)

Mirror EXP-086's TRAIN-only structure and reuse its admission-gate module unchanged. Build the cross-section
**per domain**: collect all 16 instruments' TRAIN domain bars, form the forward-filled union `CloseTime` grid
(causal last-completed-bar fill), compute the 20-bar return per instrument, then `COND-XSRANK` /
`COND-XSDIV` decile membership with direction. Drive a 46-cell × 2-primitive loop, reconciling per-cell
matched-random counts and directional mix to the conditioned events before any availability read. Reuse
`lifetime_path_geometry` for the directional `MFE`, with the adaptive cap from `adaptive_time_caps_by_epoch`.
Build the D2b permuted-axis null by shuffling which TRAIN timestamps are "extreme-decile signal" within each
cell at the realized cell count and recomputing the full per-cell Δ table; emit `S`, `S* = Q95`, the axis
permutation p, the ranking z-score, and the FWER sensitivity band. Emit the provisional per-axis disposition
captioned **non-binding pending G-019**. Everything gross, TRAIN-only, real-price: no exit, no portfolio
build, no edge verdict — only the availability numbers G-019 will convert into an admit/exonerate disposition
for the cross-sectional × directional cell.
