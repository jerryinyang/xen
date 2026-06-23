# Experiment: EXP-089 — CF-MR-001 Mean-Reversion Entry Availability Screen (Phase 020)

> **AMENDED (2026-06-23) — `D0-amendment-001` is authoritative where it conflicts with this scope.** The first
> run was a deviation (audit C-1/C-2). Superseded here: the **per-event adaptive cap** (now a **causal MR-tempo
> cap** — RSI-2 reversion-episode tempo, not MA-segment trend tempo); the **matched-random control** (now
> **regime-matched + horizon-matched**, all-bars only for CORE/variants); and the **leg-2 beats-CORE
> conjunction + regime-membership null** (RETIRED — all 6 sub-screens are single-test leg-1, regime-dependence
> read from which regimes pass). The question, 46-cell member set, multiplicity budget, registry, and TRAIN-only
> accounting are unchanged. See the amendment file in the Phase-020 checkpoint.

**Phase:** 020 (Mean-Reversion Entry Availability Screen; checkpoint
`2026-06-23-020-mean-reversion-entry-availability`, **G0 RATIFIED 2026-06-23**, D2b admission-gate bite-check
**GREEN** — `bite-check/bite_check.py` → `bite_check_report.json`, sha256
`f01a000b1b230cd172cb4a6cde914014f1efb7ba6b5fc92d25376ee0b6ffab65`) · **Family:** **CF-MR-001 — RSI-2
mean-reversion entry + global `/VOLREGIME` partition** · **HYP:** `CF-MR-001/HYP-001` · **Registry:** Phase 020
batch (multiplicity-registry); CF-MR-001 `REGISTERED — FROZEN, G0-RATIFIED`
(`candidate-families/cf-mr-001.md`) · **Candidate slots:** 0 (availability screen; a slot is consumed only on
ADMIT at a future G0/D0) · **TEST reads:** 0 counted (TRAIN-only availability disclosure; no TEST stratum
sliced, no stratum-specific inference).

**This is NOT a candidate screen and NOT a tradability/edge claim.** It is an *availability* read whose only
deliverable is an **admit / exonerate / inconclusive** disposition for the CF-MR-001 mean-reversion family
(design §2), backed by cheap signed-Δ-over-random numbers. No slot is consumed; no batch 2 opens here (an
`ADMITTED` family opens batch 2 at its own future G0/D0). The binding admit/exonerate adjudication is
**G-020**, after EXP-089; this experiment produces the realized statistics the G-020 rubric reads.

**Provenance and the operator override (recorded):** CF-MR-001 is the first candidate family opened **after**
the Phase 019 terminal branch, by **explicit operator override** of the G-019 price→non-price routing
(`cf-mr-001.md` §0; design §1). The override rests on **two genuinely new levers** — (1) a **mean-reversion
(fade)** entry mechanism (every prior family was continuation/pullback), and (2) a **strategy-agnostic,
market-intrinsic volatility-regime partition** made a cell-differentiating part of the signal definition
(cell = `asset+domain+regime`) rather than a bolt-on plugin. The programme-level null is **availability ≈
random** — the hypothesis this screen tries to reject, not a prediction of failure. The analysis and
documentation read the realized numbers on their own terms; **no prior family's outcome is imported as a
biasing expectation** in either direction.

**D0 provenance (frozen):** D1–D7 ratified and frozen 2026-06-23 (`D0-predeclarations.md`); all entry,
filter, variant, control, endpoint, and gate definitions and the D2/D3 thresholds were frozen **before** any
result-producing code (G-020 checklist §7: no goalpost-moving). No amendment without a dated `D0-amendment-*`
file in the checkpoint directory.

**Counted-read precondition (Stage-1 check):** the INFR-003 5-year ledger
(`docs/signal-registry/test-read-ledger.md`, VAL-005 PASS) shows **all 16 instruments × {15m,1h,4h} = 48
strata at 0/2 counted reads, open**. **EXP-089 reads only the TRAIN sub-stratum** (`[0, train_cutoff)`,
`train_cutoff = int(int(total_rows·0.7)·0.7)` = first 70% of the analysis set; EXP-080/081/086/087
precedent): the nested analysis-TEST stratum (last 30% of analysis) and the final-30% global holdout are
**never sliced or materialized** (forward path resolution clips at the TRAIN edge). It makes **no
stratum-specific selection or inference** — a family availability disclosure over the full TRAIN region of
each cell — so it spends **0 counted TEST reads** and the ledger is **unchanged** (D4). The permuted-axis null
(D2b) shuffles conditioning labels *within* the same TRAIN region and reads no additional data.

**Analog:** EXP-086/087 (Phase 019 availability screens) — EXP-089 is an **EXP-086 clone** with the
*information axis* swapped (single-series compression / cross-sectional → a **mean-reversion entry + intrinsic
volatility-regime partition**) and the *availability endpoint* swapped (symmetric magnitude → **directional
signed `MFE_med`** in the entry-signed direction), adjudicated by the **same D2b multiplicity-adjusted
permuted-axis admission gate**, here combined as the **joint max over 6 sub-screens** (no cross-axis Holm —
single family). **Gating precondition:** EXP-080 `READINESS_DELIVERED` — **member set = 46 instrument×domain
cells** (US500-4h, JP225-4h `COVERAGE_EXCLUDED`); the matched-random `SUB-RANDOM` scaffolding and the
readiness frame are reused **unchanged** — the random control is the established **direction-matched
`SUB-RANDOM`** for every sub-screen (no regime-matching; see §control). Leg 2 (the vol-regime partition as a
signal-defining factor) is tested by a **binding additive-edge differential vs the pooled CORE**, not by
altering the control.

---

## Hypothesis / Exploratory Question

**Single falsifiable question (design §2):**

> Does the RSI-2 mean-reversion entry — **bare**, **partitioned by a strategy-agnostic ATR volatility
> regime**, or with a **trend / RSI filter** variant — produce **signal-conditional favourable excursion** (in
> the entry-signed direction) beyond a **regime- and direction-matched** random control by more than the
> **multiplicity-adjusted joint-max permuted-axis null** (D2b) would produce at the realized cell count, on
> **any** of the 6 sub-screens?

The 6 sub-screens are read separately and combined only by the **joint max** of the permuted-axis null (a
pooled across-sub-screen number is **non-binding** — per-stratum doctrine, LESSON-001):

`CORE`, `CORE-VOL-LOW`, `CORE-VOL-MED`, `CORE-VOL-HIGH`, `CORE+TREND`, `CORE+FILTER`.

**Prior is availability ≈ random** (design §1, the programme-level null). **There is no edge/pass/viability
verdict and no candidate adjudication here.** The experiment verdict is **`SCREEN_DELIVERED`** — the per-cell
signed-Δ-over-random tables, the per-sub-screen `S` (beats-random for CORE/variants; beats-random ∧ beats-CORE for `/VOLREGIME`), the family statistic
`S_fam = max_sub S`, the **joint** permuted-axis null (`S*`, axis perm-p), and the descriptive D2a band are
produced deterministically; **admit / exonerate / inconclusive is adjudicated at G-020** under the frozen D5
rule. EXP-089 additionally reports a **provisional** family disposition (realized `S_fam` vs `S*` and the axis
perm-p, plus the argmax sub-screen naming the candidate lever) for transparency, captioned **non-binding
pending G-020**.

## Questions (per sub-screen, family availability)

For each member cell, over the per-event adaptive-cap lookforward window on real prices, conditioned on the
sub-screen's frozen entry definition and the matched control:

1. **Per-cell beats-random (leg 1; all 6 sub-screens):** signed `MFE_med` in the entry-signed direction
   (long → upward MFE, short → downward MFE), ATR(14)-normalised, per-cell `Δ̂_rand = MFE_med(signal) −
   MFE_med(SUB-RANDOM)`; per-cell pass = one-sided lower confidence bound of `Δ̂_rand > 0`.
2. **Per-cell beats-CORE additive edge (leg 2; the three `/VOLREGIME` sub-screens only — BINDING):** signed
   `Δ̂_core = MFE_med(regime subset) − MFE_med(pooled CORE)` in the same cell; per-cell pass = one-sided lower
   bound of `Δ̂_core > 0`. This is the operationalization of leg 2 — *the regime partition, as a
   signal-defining factor, adds favourable availability the unconditioned entry lacks* — tested at **full
   strength in batch 1, no deferral**. (For the two variant sub-screens the analogous vs-CORE differential is
   reported **descriptively, non-binding** — does the native toggle add over bare MR.)
3. **Per-sub-screen admission statistic `S` (over powered cells):** for `CORE`, `CORE+TREND`, `CORE+FILTER`,
   `S = #cells passing beats-random`. For `CORE-VOL-LOW/MED/HIGH`, `S = #cells passing (beats-random AND
   beats-CORE)` — the leg-2 conjunction. A regime cell that beats random but **not** CORE does not count: the
   regime must *add* edge, not merely inherit the core's.
4. **Family admission statistic (D2b, binding input to G-020):** `S_fam = max_sub S` over the 6 sub-screens;
   the **joint** permuted-axis null (`combine_axis`) is the per-permutation max of `S_perm` across the 6
   sub-screens at a shared permutation index. **Per-sub-screen null:** `CORE`/`CORE+TREND`/`CORE+FILTER`
   shuffle which timestamps are signal (preserving per-cell count + direction — the established EXP-086/087
   null); the three `/VOLREGIME` sub-screens **shuffle regime membership within each cell's CORE entry
   population** (preserving per-regime counts) and recompute the beats-random ∧ beats-CORE conjunction — so
   under the null a regime is a random subset of CORE and `Δ̂_core ≈ 0`. → `S* = Q95(joint S_perm)`, axis
   permutation p. `ADMITTED iff S_fam > S* ∧ axis perm_p ≤ 0.05` (FWER 0.05). **No cross-axis Holm** (single
   family — the joint max absorbs the within-family multiplicity over 6 sub-screens).
5. **Argmax sub-screen (lever naming, on admit):** the sub-screen attaining `S_fam` names the lever (bare MR /
   a specific vol regime [leg 2] / a variant), ranked by the sub-screen-level permutation z-score
   `(S_ss − mean(S_perm_ss)) / sd(S_perm_ss)`, tie-broken by trimmed-mean per-cell Δ (D5).
6. **Descriptive D2a band (reporting only, NON-BINDING):** the beats-random count vs the C=46 noise reference
   — median-sign coin-flip band Binomial(46,0.5) ≈ [17,29]; beats-random (CI_low>0) noise ceiling
   Binomial(46,0.05) Q95 ≈ 5.

## Scope Boundaries

- **Data Views:** 1-minute time bars from the **VAL-005-admitted 5-year dataset**
  (`data/timebars/timebars_<SYMBOL>_*.parquet`), aggregated to **15m, 1h, 4h** via the **holdout-fenced
  `xen.domain_bars.build_domain_bars`** (`min_coverage=0.90` + analysis-slice boundary fence). No Heiken Ashi,
  Line Break, or Renko (this is a real-OHLC indicator family; HA/Renko synthetic prices never enter).
- **Entry — RSI-2 mean reversion (frozen, D1):** `RSI(2)` Wilder on domain `Close`; **long `RSI₂(t) < 10`**,
  **short `RSI₂(t) > 90`** (period 2, extremes 10/90 frozen). Favourable direction = long→up, short→down. The
  RSI exit is **not used** (availability is excursion-based; the exit is deferred capture geometry, §exclusions).
- **Global filter `/VOLREGIME` (frozen, D1):** `ATR(14)` Wilder on domain bars; **causal trailing rolling-50
  percentile** of current ATR; cuts **33/66** → `LOW (<p33) / MED / HIGH (>p66)`. Thresholds computed
  **per (instrument, domain) from past bars only** (no future bar enters a regime label — streaming-safe).
  Window **50**, scheme **33/66**, **no tuning**. **Applied as a partition on the bare core only** (batch 1).
- **Variant toggles (frozen, D1; pooled sub-screens only in batch 1):** **TREND** — long `∧ Close>EMA₂₀`,
  short `∧ Close<EMA₂₀`; **RSI-FILTER** — long `∧ RSI₅>50`, short `∧ RSI₅<50` (`EMA(20)`, `RSI(5)` Wilder).
- **Matched-random control (frozen, reused unchanged):** the established `SUB-RANDOM` construction
  (EXP-080/081 `SEED_RANDOM`) — random-timing entries matched on **count and direction** within the same cell,
  **identical to EXP-086/087** for every sub-screen including the three `/VOLREGIME` partitions. **No
  regime-matching** (it is not part of the established machinery and is unnecessary here): because the endpoint
  is **ATR(14)-normalised**, a regime's larger *absolute* moves are already divided out, so the all-bars
  direction-matched control is the correct, non-confounded baseline. The regime's *additive* contribution is
  isolated separately by the **binding leg-2 beats-CORE differential** (`Δ̂_core`), not by altering the
  control. This `SUB-RANDOM` is the descriptive per-cell baseline (D2a); the **binding** null is the joint-max
  permuted-axis gate (D2b), distinct.
- **Grid (member set):** 6 sub-screens × **46 instrument×domain member cells**. The 46 cells are the EXP-080
  READY member set (16 instruments × {15m,1h,4h} **minus** US500-4h and JP225-4h, both `COVERAGE_EXCLUDED`).
  No DE30. The realized cell count matches the bite-check `C=46`, so the frozen admission gate applies as
  calibrated (the gate self-recalibrates `S*` to the realized C at run time if D7 coverage excludes cells).
- **Lookforward window (per-event adaptive time cap — reused, FROZEN):** each event's realized path is
  measured over `[entry, entry + cap]` with the **validated** `xen.expectancy.adaptive_time_caps_by_epoch`
  duration semantics (EXP-068/070 frozen `TIMECAP_*`), the same cap EXP-081/086 used; `SUB-RANDOM` inherits
  its matched cell's cap distribution. The cap never reads beyond the TRAIN sub-stratum (forward resolution
  clips at the TRAIN edge; no TEST/holdout row is touched).
- **Time range:** **first 70% of the analysis set only** (`[0, train_cutoff)`,
  `train_cutoff = int(analysis_rows · 0.7)`, `analysis_rows = int(total_rows · 0.7)`) — the nested TRAIN
  sub-split. The analysis-TEST stratum is **not sliced**; the final-30% global holdout is **never** loaded,
  inspected, counted, plotted, or used (only Parquet metadata locates the split).
- **Global holdout:** excluded from all analysis (mandatory). Never a fold; not read here.
- **Look-ahead bias prevention:** domain aggregation emits completed windows only; RSI(2)/RSI(5)/EMA(20) and
  the ATR(14) regime percentile are sequential/causal (use only bars `≤ i`; the rolling-50 percentile uses
  only the trailing 50 completed bars, no future bar in any regime label); the adaptive cap at `t_i` uses only
  move durations confirmed strictly before `t_i`; the realized path uses only bars at or after entry within
  the cap; all ordering/alignment by `CloseTime` (real time), never bar index; `SUB-RANDOM` and the
  permutation RNG never consult future data.
- **Real-price discipline (binding):** every MFE / MAE / outcome / ATR / regime figure is on **real** domain
  OHLC (`RealOpen/High/Low/Close`). No HA/Renko synthetic-price return, range, excursion, or availability
  metric anywhere (D6).
- **Exclusions:** no exit / barrier / target / stop / trailing and no exit derivation (out of phase — this is
  availability only); the RSI mean-reversion exit, parameter tuning (RSI/EMA/ATR/window), the **25/75** regime
  scheme, the **contrarian** arm, and any **regime × variant** cross-cut are **registered-but-deferred**
  (multiplicity ledger) — opening any requires a dated `D0-amendment-*` stating whether it consumes a slot; no
  parameter sweep of any frozen constant; no cross-instrument/cross-domain pooling as a binding statistic
  (per-stratum default, LESSON-001; any pooled figure is disclosure only); no TEST-stratum-specific inference
  or holdout contact; no magnitude/two-sided read (this is a directional family; magnitude is the closed
  CF-VOLEXP-001 surface and is not reopened); a regime partition earns a leg-2 win only by the **binding
  beats-random ∧ beats-CORE conjunction** (it must *add* edge over the unconditioned entry, not inherit it).

## The Measurement (per sub-screen, per cell, per event, over the adaptive cap)

For every member cell, for each conditioned event and each matched-random event whose cap is non-warmup:

1. **Per-event ATR normalization:** Wilder ATR(14) (`ATR_PERIOD=14`, frozen) on real domain bars at the entry
   bar; all distances divided by that ATR. ATR-undefined (warmup) events are disclosed and excluded.
2. **Signed lifetime MFE (ATR):** the maximum favourable excursion of the real domain OHLC over
   `[entry+1, entry+cap]` **in the entry-signed direction** (long → upward MFE from entry; short → downward
   MFE from entry). The availability endpoint is the per-cell **median** of this signed favourable excursion
   (`MFE_med`).
3. **Δ-over-random (leg 1; all sub-screens):** `Δ̂_rand = MFE_med(signal) − MFE_med(SUB-RANDOM)` per cell;
   per-cell beats-random = one-sided lower bound of `Δ̂_rand > 0` (moving-block bootstrap on the conditioned
   series + iid bootstrap on the control, `xen.availability_gate.cell_se` / the production analog of the bite
   normal test).
4. **Δ-over-CORE (leg 2; `/VOLREGIME` sub-screens BINDING, variants descriptive):** `Δ̂_core = MFE_med(regime
   subset) − MFE_med(pooled CORE)` per cell; per-cell beats-CORE = one-sided lower bound of `Δ̂_core > 0`
   (paired moving-block bootstrap over the same cell). A regime cell counts toward `S` only if it passes
   **both** `Δ̂_rand > 0` AND `Δ̂_core > 0`.

Then per sub-screen: `S` over powered cells (= `#beats-random` for CORE/variants; = `#(beats-random ∧
beats-CORE)` for the `/VOLREGIME` sub-screens); the permuted-axis `S_perm` array (signal-shuffle null for
CORE/variants; regime-membership-shuffle-within-CORE null for `/VOLREGIME`). Then per family (`combine_axis`):
`S_fam = max_sub S`, the joint `S_perm_max` at the shared permutation index, `S* = Q95`, axis perm-p, the FWER
sensitivity band {0.025,0.05,0.10}, the provisional disposition, and the argmax sub-screen + ranking z-score.

## Metric Denominators & Zero-Baseline (predeclared, before implementation)

- **Per-cell summary / Δ statistics:** denominator = the cell's count of **non-warmup, ATR-defined** RSI-MR
  events within TRAIN (disclosed per cell, separately for the conditioned set and the matched-random set), and
  for the partitioned sub-screens the per-regime event count. A cell **below the D7 coverage floor (<15
  non-warmup ATR-defined events)** reports `COVERAGE_EXCLUDED`, contributes its descriptive numbers, and is
  **excluded from the `S` count** for the binding gate — recorded, never silently dropped. **No upper
  exclusion** (the EXP-080 `8000` ceiling was a sparse-substrate sanity cap, inappropriate for a dense
  oscillator entry).
- **"Beats random" per cell:** one-sided lower confidence bound of the per-cell Δ-over-random > 0 (bootstrap);
  reported with the bound; never a percentage over a zero baseline.
- **`MFE_med`:** the per-cell median signed favourable excursion in ATR units over the cap; a cell with a
  degenerate (all-zero or single-event) excursion distribution is flagged and treated under the coverage
  bracket, never `0/0`.
- **Permutation null:** `S*` and the axis p-value are computed at the **realized** cell count (post
  `COVERAGE_EXCLUDED`); if the joint permuted null cannot separate at that count (`S*` ≥ the max attainable
  `S`), the family read is `INCONCLUSIVE` (no power) — a disclosed outcome, not an admission.
- **Warmup / undefined:** warmup-cap, ATR-undefined, and regime-warmup (first <50 bars, no percentile) events
  are counted and disclosed per cell, not folded into any statistic.

## Frozen Constants (predeclared at D0/G0; recorded here pre-data-contact)

- **Entry:** `RSI(2)` Wilder, extremes 10/90; variants `EMA(20)` (TREND), `RSI(5)` 50-cross (RSI-FILTER). None
  varied.
- **Filter `/VOLREGIME`:** `ATR(14)` Wilder, rolling-50 trailing percentile, cuts 33/66 → LOW/MED/HIGH,
  per-(instrument,domain), past-bars-only. None varied.
- **Matched-random:** `SUB-RANDOM` (EXP-080/081 construction, `SEED_RANDOM`), matched count + direction per
  cell — **the same all-bars control for every sub-screen** (no regime-matching; ATR-normalisation removes the
  regime scale, D1/§control).
- **Adaptive cap:** `xen.expectancy.adaptive_time_caps_by_epoch` with frozen `TIMECAP_*` (EXP-068/070); no cap
  tuning.
- **ATR:** Wilder ATR period **14** (`ATR_PERIOD`).
- **Coverage floor:** RSI-MR events per cell **≥ 15** (D7). **No upper bound** — the EXP-080 `8000` ceiling was
  a sparse-substrate sanity cap, dropped for this dense oscillator family (more events = more power).
- **Admission gate (D2b):** per-cell test → per-sub-screen `S` → joint-max permuted-axis null over the **6**
  sub-screens (`combine_axis`) → `S* = Q95` (family FWER 0.05) → **no cross-axis Holm**. Per-cell test =
  beats-random (CORE/variants) or beats-random ∧ beats-CORE (the three `/VOLREGIME` sub-screens, leg 2). Null =
  signal-shuffle (CORE/variants) or regime-membership-shuffle-within-CORE (`/VOLREGIME`). `N_PERM = 5000`
  production (MC-stable vs 1000). Sensitivity band FWER ∈ {0.025, 0.05, 0.10} reported as a pre-registered
  robustness sweep, not a selection. **Bite-check:** the single-test legs are GREEN (sha `f01a000b…`); the
  **leg-2 conjunctive statistic + regime-membership null are a new per-cell test → the bite-check is extended
  and re-confirmed GREEN before EXP-089 runs** (fixture: a noise regime adds 0 conjunctive wins; a planted
  additive-edge regime is detected; joint-max FWER holds across the band).
- **Seeds:** `SEED_RANDOM`, the bootstrap seed, and the permutation seed-stream fixed and recorded in
  `run_metadata.json`; a second full pass (including the permutation null) is byte-identical (D6). Master seed
  `20260623`; per-draw seed = deterministic hash of `(sub_screen, instrument, domain, replicate)`.
- **Ranking metric (frozen, used at G-020 on admit):** sub-screen-level permutation z-score
  `(S_ss − mean(S_perm_ss)) / sd(S_perm_ss)`, tie-broken by trimmed-mean per-cell Δ.

## Success / Failure / Inconclusive Criteria

- **`SCREEN_DELIVERED` (experiment verdict):** for all 6 sub-screens across all 46 member cells, the per-cell
  signed-Δ-over-random tables, the per-cell event-count / warmup / `COVERAGE_EXCLUDED` disclosures, the
  per-sub-screen `S`, the family `S_fam` / joint `S*` / axis permutation-p, the FWER sensitivity band, and the
  descriptive D2a band are produced deterministically. The **provisional** family
  admit/exonerate/inconclusive disposition + argmax sub-screen is reported, captioned **non-binding pending
  the G-020 adjudication**.
- **Family `INCONCLUSIVE`:** the joint permuted null cannot separate at the realized cell count (no power) —
  disclosed; neither admit nor exonerate.
- **Evidence AGAINST (process-level — HALT):** non-determinism on **any** cell or on the permutation null
  (second-pass statistics not frame-identical), or a real-price-discipline / look-ahead / holdout-fence
  violation, or a reconciliation break of the reused `SUB-RANDOM` matched-count construction or the leg-2
  beats-CORE differential / regime-membership null. Any of these halts and routes to a fix — they indicate an implementation bug, not a data shape.
- There is **no edge / tradability / candidate verdict** (0 slots, gross, TRAIN-only); availability is
  reported, admission is adjudicated at G-020.

## Complexity Budget

- **Max binding statistical tests: 1** — the D2b joint-max permuted-axis admission gate. Descriptive
  companions: the per-cell Δ-over-random bootstrap lower bound (the per-cell beats-random input the gate
  aggregates) and the descriptive D2a band. No dip test / magnitude-budget (directional family).
- **Max visualisations: ≤ 4** (design §4) — (i) per-cell signed-Δ map (46 cells × 6 sub-screens, by domain);
  (ii) the regime split (`CORE` vs `CORE-VOL-{LOW,MED,HIGH}`); (iii) per-sub-screen `S` vs `S*` with the
  argmax highlighted; (iv) the joint permuted-axis null distribution with realized `S_fam` and `S*` overlaid.
  All from the single analysis pass's bounded plot inputs (no reloads).
- **Max new code modules: ≤ 2** under `python/src/xen/` (design §4) — (a) **`xen.mean_reversion`**: RSI(2)/
  RSI(5) Wilder, EMA(20), and the RSI-MR entry-signal generator (long/short indices + variant toggles)
  returning EXP-080-compatible `EntrySet` structures; (b) **`xen.vol_regime`**: the `ATR(14)` causal
  rolling-50-percentile regime labeller (33/66, per-(instrument,domain), past-bars-only), the **leg-2
  beats-CORE differential**, and the **regime-membership permutation** helper. ATR(14) Wilder is recomputed
  locally (cheap; no `xen.zigzag` import). **Reuse unchanged:** `xen.availability_gate` (`CellReadInput`,
  `run_sub_screen`, `combine_axis`, `cell_se`), `xen.domain_bars` / `xen.bar_aggregator`,
  `xen.capgeo_substrates` (`SUB-RANDOM`, `SEED_RANDOM`), `xen.capgeo_geometry` (`lifetime_path_geometry`),
  `xen.expectancy` (adaptive cap). The gate's per-cell test + permutation hooks take a thin extension for the
  leg-2 conjunction and regime null (covered by the re-confirmed bite-check); no edits to the entry frozen
  generators/detectors. Drop any reuse that proves unnecessary on implementation.

## Data Requirements

Per instrument: lazy `pl.scan_parquet` of the single VAL-005-admitted 5-year file; read total row count from
metadata; `analysis_rows = int(total_rows · 0.7)`; `train_cutoff = int(analysis_rows · 0.7)`; collect only the
first `train_cutoff` file-order 1-minute rows; assert sorted by `CloseTime`; build domain bars via
`build_domain_bars`; compute RSI(2)/RSI(5)/EMA(20) and the ATR(14) rolling-50 regime labels on real OHLC
(causal); derive the 6 sub-screen entry populations; reproduce the matched `SUB-RANDOM` events per cell
(matched count + direction — the same all-bars control for every sub-screen); compute per-event adaptive caps
and signed favourable path geometry on real OHLC; aggregate per-cell signed-`MFE_med` `Δ̂_rand` (all
sub-screens) and `Δ̂_core` (regime sub-screens binding, variants descriptive); build the joint-max
permuted-axis null (signal-shuffle for CORE/variants, regime-membership shuffle for `/VOLREGIME`) and `S` /
`S_fam` / `S*` / axis-p over the 6 sub-screens; run the bounded determinism
second pass (including the permutation stream). Outputs: a per-cell availability parquet/CSV (all 6
sub-screens, with denominators + `COVERAGE_EXCLUDED` flags), a family admission-statistic JSON (`S_ss`,
`S_fam`, `S*`, perm-p, sensitivity band, provisional disposition, argmax sub-screen, ranking z-scores), a
bounded per-event geometry parquet (reproducibility), `run_metadata.json` (seeds, hashes, frozen-constant
versions, bite report sha256, `holdout_untouched=true`, `counted_test_reads=0`, `candidate_slots=0`), and the
≤4 bounded plots. `tqdm` over the sub-screen × member-cell outer loop; per-cell memory bounded (do not retain
all domain frames). Expected runtime: minutes–tens-of-minutes (the joint permutation null at production
`N_PERM=5000` is the main cost — MC stability already confirmed at the bite scale).

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

Mirror EXP-086's TRAIN-only structure: drive a 6-sub-screen × 46-cell loop off the EXP-080 readiness frame and
the reused `SUB-RANDOM` scaffolding; reconcile per-cell matched-random counts (and regime labels for the
partitioned sub-screens) to the conditioned counts before any availability read. Build the entry populations
in `xen.mean_reversion` (RSI-2 long/short + TREND/RSI-FILTER variants) and the regime labels +
the beats-CORE differential + regime-membership permutation in `xen.vol_regime`; reuse `lifetime_path_geometry`
for the signed favourable excursion and `adaptive_time_caps_by_epoch` for the cap. Feed per-cell
`CellReadInput` to `run_sub_screen` for the 3 single-test sub-screens (CORE + 2 variants); for the 3
`/VOLREGIME` sub-screens apply the leg-2 conjunction (beats-random ∧ beats-CORE) with the regime-membership
null; then `combine_axis` (joint max, no Holm) for `S_fam` / `S*` / axis-p and the argmax lever.
Emit the provisional family disposition captioned **non-binding pending G-020**. Everything gross, TRAIN-only,
real-price: no exit, no edge verdict — only the availability numbers G-020 will convert into an
admit/exonerate disposition for the CF-MR-001 mean-reversion family.
