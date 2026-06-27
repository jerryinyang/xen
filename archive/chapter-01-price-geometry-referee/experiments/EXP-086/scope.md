# Experiment: EXP-086 — Screen M: Single-Series Magnitude / Non-Directional Availability (Phase 019 Family-Selection)

**Phase:** 019 (Family-Selection Availability Screen; checkpoint
`2026-06-22-019-family-selection-availability-screen`, **G0 PASS 2026-06-22**, D2b admission-gate bite-check
**GREEN**) · **Axis:** **M — single-series magnitude** · **HYP:** `CF-VOLEXP-001/HYP-001` ·
**Registry:** Phase 019 batch (multiplicity-registry); CF-VOLEXP-001 `DRAFT — PENDING-SELECTION`
(`candidate-families/family-selection-phase-019.md`) · **Candidate slots:** 0 (family selection, not
candidate screening) · **TEST reads:** 0 counted (TRAIN-only availability disclosure; no TEST stratum
sliced, no stratum-specific inference).

**This is NOT a candidate screen and NOT a tradability/edge claim.** It is a family-agnostic *availability*
read whose only deliverable is an **admit / exonerate / inconclusive** disposition for the single-series
**magnitude** cell of the availability 2×2 (design §2), backed by cheap Δ-over-random numbers. No slot is
consumed; no family is opened here (an `ADMITTED` axis opens at its own future G0/D0). The binding
admit/exonerate adjudication is **G-019**, after the slate; EXP-086 produces the realized statistics the
G-019 rubric reads.

**D0 provenance (frozen):** D1–D6 ratified and frozen 2026-06-22 (`D0-predeclarations.md`); the two Screen-M
conditioning primitives concretized by operator at scoping in **`D0-amendment-001-screen-m-primitive-freeze.md`**
(raw direction-agnostic HA harami + NR7). Nothing in this scope tunes, selects, or freezes any constant
against data — all axis-conditioning definitions and the D2/D3 thresholds/endpoints were frozen before any
result-producing code (G-019 checklist §7: no goalpost-moving).

**Counted-read precondition (Stage-1 check):** the INFR-003 5-year ledger
(`docs/signal-registry/test-read-ledger.md`, re-materialized 2026-06-21 on VAL-005 PASS) shows **all 16
instruments × {15m,1h,4h} = 48 strata at 0/2 counted reads, open**. **EXP-086 reads only the TRAIN
sub-stratum** (`[0, train_cutoff)`, `train_cutoff = int(int(total_rows·0.7)·0.7)` = first 70% of the analysis
set = first 49% of each 5-year file; EXP-074/075/080/081 precedent): the nested analysis-TEST stratum (last
30% of analysis) and the final-30% global holdout are **never sliced or materialized** (forward path
resolution clips at the TRAIN edge). It makes **no stratum-specific selection or inference** — a
family-agnostic availability disclosure over the full TRAIN region of each cell — so it spends **0 counted
TEST reads** and the ledger is **unchanged** (D4; EXP-080/081 convention). The permuted-axis null (D2b)
shuffles conditioning labels *within* the same TRAIN region and reads no additional data.

**Analog:** EXP-081 (per-substrate realized return-structure characterization) — Screen M is an **EXP-081
clone** with the *information axis* swapped (frozen directional substrates → single-series **compression
primitives**) and the *availability endpoint* swapped (favourable `MFE_med` → the **split** typical-range +
tail/bimodality reads + the two-sided magnitude-budget check), adjudicated by the **D2b multiplicity-adjusted
permuted-axis admission gate** rather than reported as raw geometry. **Gating precondition:** EXP-080
`READINESS_DELIVERED` (re-audit PASS) — **member set = 46 instrument×domain cells** (US500-4h, JP225-4h
`COVERAGE_EXCLUDED`); the matched-random `SUB-RANDOM` scaffolding and the readiness frame are reused
unchanged.

---

## Hypothesis / Exploratory Question

**Single falsifiable question (design §3, the magnitude cell of the 2×2):**

> Conditioned on existing single-series **compression** primitives, does forward **non-directional**
> availability beat a matched within-instrument random control by more than the **multiplicity-adjusted
> permuted-axis null** (D2b) would produce at the realized cell count — on **either** of two
> separately-reported reads — and does any predictable range clear a **two-sided** cost?

The two reads are kept strictly separate (a pooled `|move|` number is **prohibited** — D3.M; EXP-081 already
shows it is null):

1. **Typical-range read:** forward realized symmetric excursion `max(MFE, MAE)` (with `MFE+MAE` as a
   companion), ATR-normalised, Δ-over-matched-random per cell.
2. **Tail / bimodality read:** `tailmass`, `q05`, Hartigan dip-p of the per-event realized outcome, **plus**
   a direct re-examination of EXP-074's `msofar_atr` adverse-tail separation **expressed as predictable
   magnitude** (rank-biserial of the conditioning vs the q05 tail) — the one place the prior is non-trivial.

**Prior is low and tail-concentrated** (design §5, candidate-family evidence basis): EXP-081 `MAE_q90`
Δ-over-random −0.719 (real>random 9/46) and `MFE_med` −0.140 (17/46) → *typical* range is not elevated; the
only positive hint is the rare tail (`tailmass` 0.0526 vs random 0.0437).

**There is no edge/pass/viability verdict and no candidate adjudication here.** The experiment verdict is
**`SCREEN_DELIVERED`** — the per-cell Δ-over-random tables for both reads, the axis-level permuted-null
statistic (`S_M`, `S*`, axis permutation p), the magnitude-budget two-sided-cost result, and the descriptive
D2a band are produced deterministically for the magnitude axis; **admit / exonerate / inconclusive is
adjudicated at G-019** under the frozen D5 rule (with the cross-axis Holm step-down applied over the
{M, X, (F)} slate). EXP-086 additionally reports a **provisional single-axis** disposition (realized
`S_M` vs `S*` and the unadjusted axis p) for transparency, captioned **non-binding** pending G-019.

## Questions (per read, family-agnostic availability)

For each member cell, over the per-event adaptive-cap lookforward window on real prices, conditioned on each
of the two frozen compression primitives (raw HA harami; NR7) and the matched `SUB-RANDOM` control:

1. **Typical-range availability:** per-cell Δ-over-random of `max(MFE, MAE)` (ATR) and of `MFE+MAE` (ATR);
   per-cell "beats random" = one-sided lower confidence bound of the Δ > 0 (the binding per-cell test that
   the D2b gate aggregates — bite-check §A).
2. **Tail / bimodality availability:** per-cell Δ-over-random of `tailmass` and `q05`; Hartigan dip-p of the
   conditioned realized-outcome distribution; and the `msofar_atr`-as-magnitude rank-biserial vs the q05
   tail (within the conditioned set, with the random control as the null comparator).
3. **Axis-level admission statistic (D2b, binding input to G-019):** `S_M = #cells-beat-random` per read; the
   **permuted-axis null** (shuffle which TRAIN timestamps are "signal" vs not, preserving per-cell event
   counts and the regime/direction match, recompute the full per-cell Δ table) → `S*` = the
   `Q95` permutation ceiling and the axis permutation p-value.
4. **Magnitude-budget two-sided-cost check (binding for any magnitude admission):** does the predictable
   range clear a **two-sided** cost (CONSERVATIVE round-trip × 2 sides + financing, EXP-030/085 convention)?
   A tail-only admission is recorded as a **long-vol** finding (routes to CF-VOLEXP-001 under the harvest
   model), never a directional edge.
5. **Descriptive D2a band (reporting only, NON-BINDING):** the cells-beat-random count vs the EXP-081
   coin-flip baseline (≈17/46–28/46) per read.

## Scope Boundaries

- **Data Views:** 1-minute time bars from the **VAL-005-admitted 5-year dataset**
  (`data/timebars/timebars_<SYMBOL>_*.parquet`, 2021-06-02 → 2026-06-21), aggregated to **15m, 1h, 4h** via
  the **holdout-fenced `xen.domain_bars.build_domain_bars`** (`min_coverage=0.90` + analysis-slice boundary
  fence, VAL-005 G1). Heiken Ashi candles (raw-harami detection) via `xen.heiken_ashi_generator`. No Line
  Break / Renko.
- **Conditioning primitives (two, frozen at D0-amendment-001; neither tuned):**
  1. **`COND-HARAMI`** — raw direction-agnostic HA harami inside-bar (`xen.ha_harami.detect_ha_harami`); HA
     candles for **detection only**; a single-series compression state, **no** MA/`STRONG` conditioning.
  2. **`COND-NR7`** — NR7 on real OHLC: bar *i* fires iff `TrueRange(i) == min(TrueRange(i−6 … i))`;
     lookback 7 frozen, causal, deterministic.
- **Matched-random control (frozen, reused):** `SUB-RANDOM` — fixed-seed random-timing entries on the same
  regime/direction within the same cell, matched count, reproduced from the EXP-080/081 `SEED_RANDOM`
  construction. This is the **descriptive** per-cell baseline (D2a); the **binding** null is the permuted-axis
  gate (D2b), distinct.
- **Grid (member set):** 2 conditioning primitives × **46 instrument×domain member cells** = 92
  conditioned cells (plus the matched `SUB-RANDOM` per cell). The 46 cells are the EXP-080 READY member set
  (16 instruments × {15m,1h,4h} **minus** US500-4h and JP225-4h, both `COVERAGE_EXCLUDED`). No DE30. The
  realized cell count per axis matches the bite-check `C=46`, so the frozen admission gate applies as
  calibrated.
- **Lookforward window (per-event adaptive time cap — reused, FROZEN):** each event's realized path is
  measured over `[entry, entry + cap]` with the **validated** `xen.expectancy.adaptive_time_caps_by_epoch`
  duration semantics (EXP-068/070 frozen `TIMECAP_*`), the same cap EXP-081 used. The per-primitive
  instantiation of the move structure feeding the cap (and `SUB-RANDOM` inheriting its matched cell's cap
  distribution) is fixed in the Stage-2 analysis plan; the **principle** (adaptive per-move cap, validated
  semantics, no grid search) is frozen here. The cap never reads beyond the TRAIN sub-stratum (forward
  resolution clips at the TRAIN edge; no TEST/holdout row is touched).
- **Time range:** **first 70% of the analysis set only** (`[0, train_cutoff)`,
  `train_cutoff = int(analysis_rows · 0.7)`, `analysis_rows = int(total_rows · 0.7)`) — the nested TRAIN
  sub-split. The analysis-TEST stratum is **not sliced**; the final-30% global holdout is **never** loaded,
  inspected, counted, plotted, or used (only Parquet metadata locates the split).
- **Global holdout:** excluded from all analysis (mandatory). Never a fold; not read here.
- **Look-ahead bias prevention:** domain aggregation emits completed windows only; HA generation, raw-harami
  detection, and NR7 are sequential/causal (NR7 uses only bars `≤ i`); the adaptive cap at `t_i` uses only
  move durations confirmed strictly before `t_i`; the realized path uses only bars at or after entry within
  the cap; all ordering/alignment by `CloseTime` (real time), never bar index; `SUB-RANDOM` and the
  permutation RNG never consult future data.
- **Real-price discipline (binding):** every MFE / MAE / outcome / range / ATR figure is on **real** domain
  OHLC. The raw-harami detector runs on HA (synthetic) candles for *entry detection only*; **no return,
  range, excursion, tail, or availability metric uses HA or any synthetic price** (D6).
- **Exclusions:** no exit / barrier / target / stop / trailing and no exit derivation (out of phase — this is
  availability only); no frozen referee suite, separability gate, or binding `ASS` adjudication (no
  pass/reject/admit decision rests on anything *here*; admission is G-019 mechanical); no parameter sweep or
  tuning of either primitive, the cap, the gate, or the cost model (all frozen); no cross-instrument /
  cross-domain pooling as a binding statistic (per-stratum default, LESSON-001; any pooled figure is
  disclosure only); no TEST-stratum-specific inference or holdout contact; **no directional re-use of a
  tail-only result** (the magnitude harvest-model guard, design §8 — binding); no pooled `|move|` endpoint
  (D3.M — prohibited).

## The Measurement (per conditioning primitive, per cell, per event, over the adaptive cap)

For every member cell, for each conditioned event and each matched-random event whose cap is non-warmup:

1. **Per-event ATR normalization:** Wilder ATR(14) (`ATR_PERIOD=14`, frozen) on real domain bars at the entry
   bar; all distances divided by that ATR. ATR-undefined (warmup) events are disclosed and excluded.
2. **Lifetime MFE / MAE (ATR):** maximum favourable and maximum adverse excursion of the real domain OHLC
   over `[entry+1, entry+cap]`. **Typical-range read** uses the direction-agnostic symmetric excursion
   `max(MFE, MAE)` and companion `MFE+MAE` (no entry direction needed — magnitude axis).
3. **Per-event realized outcome (ATR):** the real-price return at the cap bar's close, the readout the
   `tailmass` / `q05` / dip statistics summarize. (Direction for the signed outcome and for `msofar_atr` is
   taken from the cell's regime state, as in EXP-081/074, used only inside the tail read; it never enters the
   typical-range read.)
4. **`msofar_atr` (exhaustion magnitude):** recomputed as in EXP-074, read as *predictable magnitude*
   (rank-biserial vs the q05 tail) — the tail read's third, non-trivial-prior component.

Then per cell the **availability statistics** (frozen, D3.M): typical-range Δ-over-random of `max(MFE,MAE)`
and `MFE+MAE`; tail Δ-over-random of `tailmass` and `q05`; dip-p; `msofar_atr` rank-biserial. Then per axis
(per read): `S = #cells-beat-random`, the permuted-axis null, `S*`, axis permutation p; and the
magnitude-budget two-sided-cost result on any read whose `S` clears `S*`.

## Metric Denominators & Zero-Baseline (predeclared, before implementation)

- **Per-cell summary / Δ statistics:** denominator = the cell's count of **non-warmup, ATR-defined** events
  within TRAIN (disclosed per cell, separately for the conditioned set and the matched-random set). A cell
  below the **≥30-event floor** reports `UNDERPOWERED_DISCLOSED`, contributes its descriptive numbers, and is
  **excluded from the `S = #cells-beat-random` count** for the binding gate (it cannot reliably "beat
  random") — recorded, never silently dropped.
- **"Beats random" per cell:** one-sided lower confidence bound of the per-cell Δ-over-random > 0 (bootstrap;
  the production analog of the bite-check normal-approx test). Reported with the bound; never a percentage
  over a zero baseline.
- **`tailmass`:** (count of events below the catastrophe boundary `median − K_tail·MAD`, `K_tail = 3.0`
  frozen) / (cell event count); a cell with zero tail events reports `0.0` with its denominator shown, never
  `0/0`. MAD-zero cells flagged.
- **Permutation null:** `S*` and the axis p-value are computed at the **realized** cell count (post
  `UNDERPOWERED` exclusion); if the permuted null cannot separate at that count (`S*` ≥ the max attainable
  `S`), the axis read is `INCONCLUSIVE` (no power) — a disclosed outcome, not an admission.
- **Magnitude-budget:** the predictable range is compared to the two-sided cost in ATR units (cost as a
  positive ATR magnitude); reported as range-minus-cost in ATR, never as a percentage of a zero baseline.
- **Warmup / undefined:** warmup-cap and ATR-undefined events are counted and disclosed per cell, not folded
  into any statistic.

## Frozen Constants (predeclared at D0/G0 + D0-amendment-001; recorded here pre-data-contact)

- **Conditioning primitives:** `COND-HARAMI` = raw `detect_ha_harami` (no MA/STRONG); `COND-NR7` = real-OHLC
  narrowest TR in 7 bars (lookback 7). Neither varied.
- **Matched-random:** `SUB-RANDOM` (EXP-080/081 construction, `SEED_RANDOM`), matched count per cell.
- **Adaptive cap:** `xen.expectancy.adaptive_time_caps_by_epoch` with frozen `TIMECAP_*` (EXP-068/070); no
  cap tuning.
- **ATR:** Wilder ATR period **14** (`ATR_PERIOD`).
- **Tail:** catastrophe boundary `K_tail = 3.0`; dip α as EXP-081 `DIP_ALPHA`; event floor **≥ 30**.
- **Admission gate (D2b, GREEN bite-check, unchanged):** per-cell CI_low>0 → `S = #cells-beat-random` →
  permuted-axis null (`N_PERM` at production scale, candidate 1000 → confirm/lift in Stage 2) → `S* = Q95`
  (axis FWER 0.05) → **cross-axis Holm** over {M, X, (F)} **applied at G-019** (EXP-086 emits the per-axis p).
  Sensitivity band FWER ∈ {0.025, 0.05, 0.10} reported as a pre-registered robustness sweep, not a selection.
- **Two-sided cost:** CONSERVATIVE round-trip × 2 sides + financing (EXP-030/085 convention; per-instrument
  constants frozen in the Stage-2 analysis plan from the EXP-085 cost table — not tuned).
- **Seeds:** `SEED_RANDOM`, the bootstrap seed, and the permutation seed-stream fixed and recorded in
  `run_metadata.json`; a second full pass (including the permutation null) is byte-identical (D6).
- **Ranking metric (frozen, used at G-019):** axis-level permutation z-score
  `(S_A − mean(S_perm)) / sd(S_perm)`, tie-broken by trimmed-mean per-cell Δ.

## Success / Failure / Inconclusive Criteria

- **`SCREEN_DELIVERED` (experiment verdict):** for both conditioning primitives across all 46 member cells,
  the per-cell Δ-over-random tables (typical-range and tail reads, separately), the per-cell event-count /
  warmup / `UNDERPOWERED_DISCLOSED` disclosures, the axis-level `S` / `S*` / permutation-p, the
  magnitude-budget two-sided-cost result, and the descriptive D2a band are produced deterministically. The
  **provisional** single-axis admit/exonerate/inconclusive disposition is reported, captioned **non-binding
  pending the G-019 cross-axis Holm adjudication**.
- **Axis-read `INCONCLUSIVE`:** the permuted null cannot separate at the realized cell count (no power) on a
  read — disclosed; neither admit nor exonerate for that read.
- **Evidence AGAINST (process-level — HALT):** non-determinism on **any** cell or on the permutation null
  (second-pass statistics not frame-identical), or a real-price-discipline / look-ahead / holdout-fence
  violation, or a reconciliation break of the reused `SUB-RANDOM` matched-count construction. Any of these
  halts and routes to a fix — they indicate an implementation bug, not a data shape.
- There is **no edge / tradability / candidate verdict** (0 slots, gross, TRAIN-only); availability is
  reported, admission is adjudicated at G-019.

## Complexity Budget

- **Max statistical tests: 3** — (i) the per-cell Δ-over-random bootstrap lower bound ("beats random"); (ii)
  the Hartigan dip test (tail bimodality); (iii) the permuted-axis admission null (the binding D2b gate). The
  `msofar_atr` rank-biserial is a descriptive effect size (no added test). The magnitude-budget is an
  arithmetic comparison.
- **Max visualisations: 5** — (i) typical-range Δ-over-random heatmap (46-cell, by domain) per primitive;
  (ii) tail (`tailmass`/`q05`) Δ-over-random heatmap per primitive; (iii) the permuted-axis null distribution
  with realized `S_M` and `S*` overlaid, per read; (iv) representative conditioned-vs-random outcome
  distributions for the densest cells (dip/`msofar_atr` overlay); (v) magnitude-budget range-vs-cost panel.
  All from the single analysis pass's bounded plot inputs (no reloads).
- **Max new code modules: ≤ 2** under `python/src/xen/` — (a) a **compression-primitive** entry module
  (raw-harami-inside-bar + NR7 entry indices returning EXP-080-compatible `EntrySet` structures) and (b) a
  reusable **availability-admission-gate** module (per-cell beats-random + permuted-axis null + `S*` + Holm),
  reusable by EXP-087/088. **Reuse unchanged:** `xen.domain_bars`, `xen.heiken_ashi_generator`,
  `xen.ha_harami`, `xen.capgeo_substrates` (`SUB-RANDOM`, `_real_ohlc`, `ATR_PERIOD`), `xen.capgeo_geometry`
  (`lifetime_path_geometry`, `tail_stats`, `antimode_mae`, `K_TAIL`, `DIP_ALPHA`), `xen.expectancy` (adaptive
  cap), `xen.capgeo_cost` (two-sided cost overlay, EXP-085), `xen.ass` (bootstrap CIs), `xen.zigzag`
  (`wilder_atr`). No edits to frozen generators/detectors.

## Data Requirements

Per instrument: lazy `pl.scan_parquet` of the single VAL-005-admitted 5-year file; read total row count from
metadata; `analysis_rows = int(total_rows · 0.7)`; `train_cutoff = int(analysis_rows · 0.7)`; collect only
the first `train_cutoff` file-order 1-minute rows; assert sorted by `CloseTime`; build domain bars via
`build_domain_bars`; generate HA candles (raw harami); compute NR7 on real OHLC; reproduce the matched
`SUB-RANDOM` events per cell (matched count); compute per-event adaptive caps and realized path geometry on
real OHLC; aggregate per-cell typical-range and tail Δ-over-random + dip-p + `msofar_atr` rank-biserial; build
the permuted-axis null and `S` / `S*` / axis-p per read; run the two-sided magnitude-budget; run the bounded
determinism second pass (including the permutation stream). Outputs: a per-cell availability parquet/CSV
(both reads, both primitives, with denominators + `UNDERPOWERED` flags), a per-axis admission-statistic JSON
(`S`, `S*`, perm-p, sensitivity band, provisional disposition, ranking z-score), a bounded per-event
geometry parquet (reproducibility), `run_metadata.json` (seeds, hashes, frozen-constant versions,
`holdout_untouched=true`, `counted_test_reads=0`, `candidate_slots=0`), and the ≤5 bounded plots. `tqdm` over
the member-cell × primitive outer loop; per-cell memory bounded (do not retain all domain frames). Expected
runtime: minutes–tens-of-minutes (the permutation null at production `N_PERM` is the main cost — confirm MC
stability at the bite scale, then lift before the binding read).

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
```

## Suggested Direction (non-binding)

Mirror EXP-081's TRAIN-only structure: drive a 46-cell × 2-primitive loop off the EXP-080 readiness frame and
the reused `SUB-RANDOM` scaffolding; reconcile per-cell matched-random counts to the conditioned counts before
any availability read. Reuse `lifetime_path_geometry` for `max(MFE,MAE)` / outcome and `tail_stats` /
`antimode_mae` for the tail read, with the adaptive cap from `adaptive_time_caps_by_epoch`. Compute the two
reads strictly separately (never a pooled `|move|`). Build the D2b permuted-axis null by shuffling the
conditioning labels within TRAIN at the realized cell count and recomputing the full per-cell Δ table; emit
`S`, `S* = Q95`, the axis permutation p, and the FWER sensitivity band per read; apply the two-sided
magnitude-budget to any read clearing `S*`. Emit the provisional per-axis disposition captioned **non-binding
pending G-019**. Everything gross, TRAIN-only, real-price: no exit, no edge verdict — only the availability
numbers G-019 will convert into an admit/exonerate disposition for the single-series-magnitude cell.
