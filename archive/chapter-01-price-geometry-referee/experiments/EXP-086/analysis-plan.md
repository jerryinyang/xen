# Analysis Plan: Experiment EXP-086

**Screen M — single-series magnitude / non-directional availability (Phase 019 family-selection; EXP-081 clone, axis + endpoint swapped; TRAIN-only, gross).**

Phase 019 · Family-Selection Availability Screen · Axis **M** · `CF-VOLEXP-001/HYP-001` · 0 candidate slots · 0 counted TEST reads.
Companions: `scope.md`; Phase 019 D0 (`docs/experiments-docs/checkpoints/2026-06-22-019-family-selection-availability-screen/D0-predeclarations.md`, §D2b/§D3.M/§D4/§D5/§D6) + `D0-amendment-001-screen-m-primitive-freeze.md` (raw HA harami + NR7); GREEN bite-check (`…/bite-check/bite_check.py`, report sha256 `208dfb3f…`).

## Objective

Produce, per member cell and per frozen compression primitive, the **availability statistics** that the
G-019 rubric converts into an **admit / exonerate / inconclusive** disposition for the single-series
**magnitude** cell of the 2×2 — kept as **two strictly-separate reads** (a pooled `|move|` number is
prohibited, D3.M):

1. **Typical-range read** — per-cell Δ-over-matched-random of the symmetric realized excursion
   `max(MFE, MAE)` (companion `MFE+MAE`), ATR units.
2. **Tail / bimodality read** — per-cell Δ-over-matched-random of `tailmass` (companion `q05`, dip-p) of the
   signed realized outcome, plus EXP-074's `msofar_atr`-as-predictable-magnitude (rank-biserial vs the q05
   tail; descriptive, non-binding context — the one non-trivial-prior place).

The binding decision rule is the **D2b multiplicity-adjusted permuted-axis admission gate**; the binding
**admit/exonerate adjudication is G-019**, not this experiment. The experiment verdict is **`SCREEN_DELIVERED`**
if the statistics + the gate inputs are produced deterministically for the whole member set; it HALTs only on
non-determinism, a real-price/look-ahead/holdout-fence violation, or a matched-random count-reconciliation
break. A **provisional** single-axis disposition is reported, captioned **NON-BINDING pending the G-019
cross-axis Holm step-down**.

All estimators are non-parametric / resampling-based (quantile, proportion, moving-block bootstrap, Hartigan
dip, label-permutation). No normality, stationarity, i.i.d., or constant-volatility assumption gates any
verdict. Per-stratum reporting throughout (LESSON-001); no pooled-as-verdict.

## Fixed inputs (frozen upstream — not re-derived here)

- **Member set:** **46 EXP-080-READY instrument×domain cells** (16 instruments × {15m,1h,4h} minus US500-4h,
  JP225-4h `COVERAGE_EXCLUDED`). Realized per-primitive cell count matches the bite-check `C=46`, so the
  calibrated gate applies as-is.
- **Conditioning primitives (two, frozen at D0-amendment-001; neither tuned):**
  - **`COND-HARAMI`** — raw direction-agnostic HA harami inside-bar (`xen.ha_harami.detect_ha_harami` on HA
    candles from `xen.heiken_ashi_generator`; HA for *detection only*).
  - **`COND-NR7`** — real-OHLC NR7: bar *i* fires iff `TrueRange(i) == min(TrueRange(i−6 … i))` (lookback 7,
    causal; `TrueRange = max(H,C_prev) − min(L,C_prev)`).
- **Matched-random control (`SUB-RANDOM`, frozen construction reused):** per cell **and per primitive**, a
  fixed-seed random-timing draw matched to that primitive's event count and same-regime-direction
  eligibility (EXP-080/081 `random_entries`; seed key `[SEED_RANDOM, cell_index, primitive_id, n_target]`).
  This is the **descriptive** baseline (D2a); the **binding** null is the permuted-axis gate (D2b), distinct.
- **Read region:** TRAIN sub-split `[0, train_cutoff)`, `train_cutoff = int(int(total_rows·0.7)·0.7)`.
  Analysis-TEST and final-30% holdout never sliced.
- **Per-event ATR:** Wilder ATR(14) (`ATR_PERIOD=14`) on real domain bars (`xen.zigzag.wilder_atr`).
- **Adaptive cap:** `xen.expectancy.adaptive_time_caps_by_epoch`, frozen `TIMECAP_*` (EXP-068/070), the same
  cap EXP-081 used (cell MA-segment move-duration tempo, applied to every primitive + its matched-random by
  entry epoch). No cap tuning.
- **Tail constants:** catastrophe boundary `K_tail = 3.0`; dip α = `DIP_ALPHA` (EXP-081); event floor **≥ 30**.
- **Gate constants (GREEN bite-check, unchanged):** per-cell one-sided lower-bound test at `z = 1.645`;
  axis FWER `0.05`; `S* = Q95` of the permuted-axis null; sensitivity band FWER ∈ {0.025, 0.05, 0.10}; Holm
  step-down across axes **applied at G-019**.

---

## Methodology

### Step 1 — Cohort construction (per cell, per primitive)

- **Method:** lazy `pl.scan_parquet` per instrument; slice the first `train_cutoff` 1-minute rows; assert
  `CloseTime` sorted; build 15m/1h/4h bars via `xen.domain_bars.build_domain_bars` (`min_coverage=0.90` +
  analysis-boundary fence). Generate HA candles → `COND-HARAMI` entry indices via `detect_ha_harami`
  (aligned to the domain bar that *confirms* each harami, by `CloseTime`). Compute `COND-NR7` entry indices
  on real OHLC. For each primitive, draw the count-matched `SUB-RANDOM` set (`n_target` = that primitive's
  event count; same regime/direction eligibility as EXP-081's random control).
- **Why:** Screen M reuses the *certified* readiness scaffolding (EXP-080 member set, `random_entries`
  construction, domain/HA generation) and only swaps the conditioning. Aligning harami events to the
  confirming domain bar (not the HA index) keeps every downstream metric on the real domain-bar timeline.
- **Reconciliation guard (binding):** assert per cell, per primitive, that the matched-random count equals
  the conditioned count (`n_random == n_cond`) and that both index arrays lie within `[0, train_edge_idx]`.
  A mismatch is a HALT (construction/harness bug, not a data shape).
- **Simpler alternative considered:** reuse EXP-080's MA-conditioned harami substrate. Rejected — that is the
  *directional* dead-cell entry; Screen M is a non-directional magnitude axis (D0-amendment-001).
- **Assumptions:** deterministic generators (VAL-005/EXP-080 validated); holds.
- **Output:** per (cell, primitive) conditioned + matched-random entry index/epoch arrays + `recon_ok`.

### Step 2 — Per-event adaptive cap + regime direction

- **Method:** identical to EXP-081 Step 2/3 — one cap basis per cell from `_ma_segment_moves(real_ohlc)` →
  `adaptive_time_caps_by_epoch(entry_epoch, confirm_epoch, confirm_idx)` with frozen `TIMECAP_*`, applied to
  the conditioned set, the matched-random set, **and** the permutation pseudo-signal pool (Step 6) by entry
  epoch. Warmup events (fewer than `min_moves` prior durations) are **disclosed and excluded**, never
  silently capped. Regime direction `d ∈ {+1,−1}` per event = the in-progress MA-segment direction at entry
  (`live_in_progress_state`); direction-undefined entries are warmup-equivalent and excluded.
- **Why:** keeps the lookforward window and the matched-random control on the *same* validated cell-tempo cap
  as EXP-081 (fair attribution; the random null inherits the identical cap-by-time step function). The regime
  direction is used **only** in the tail read's signed outcome and `msofar_atr` (Step 5b); the typical-range
  read is direction-agnostic (Step 5a).
- **Methodology decision (flag for Stage-4 governance):** the cap basis is the cell MA-segment tempo, applied
  uniformly to both compression primitives and their controls — the EXP-081 precedent, reused unchanged (not
  a new free choice).
- **Output:** per-event integer cap, `warmup` mask, `d`, per (cell, primitive, set).

### Step 3 — Realized path geometry on real OHLC (reuse `xen.capgeo_geometry`)

- **Method:** for each non-warmup, ATR-defined event with entry index `i`, cap `c`, window
  `W = [i+1, min(i+c, train_edge_idx)]` on **real** domain OHLC, via `lifetime_path_geometry`:
  - **Typical-range read (direction-agnostic):** call with `d = +1` for *all* events, so
    `MFE = max_{t∈W}(H_t − C_i)/ATR_i` = up-excursion and `MAE = max_{t∈W}(C_i − L_t)/ATR_i` = down-excursion.
    Per event: `range_sym = max(MFE, MAE)` (the larger one-sided excursion) and `range_tot = MFE + MAE`
    (total realized range). **No position direction enters this read.**
  - **Tail read (signed):** realized outcome `outcome = d·(C_{last(W)} − C_i)/ATR_i` using the regime `d`
    (Step 2) — identical to EXP-081's outcome; its left tail is the catastrophe the harvest model targets.
  - Events whose window is empty after TRAIN-edge clipping are excluded with a `clipped_empty` count.
- **Why:** standard MFE/MAE path geometry, reused module, no exit applied. The direction-agnostic `d=+1`
  trick gives the genuine non-directional realized range for the magnitude read without inventing a new
  primitive; the signed outcome (regime `d`) gives the adverse tail for the tail read. Real prices only; HA
  used solely for harami detection.
- **Vectorization discipline:** intra-window max/argmax vectorized with NumPy; outer event loop explicit and
  cap-bounded (causal, no look-ahead). `tqdm` over the (cell × primitive) loop.
- **Output:** per-event `(range_sym, range_tot, outcome, msofar_atr)` arrays per (cell, primitive, set), where
  `msofar_atr` = the in-progress MA-segment move magnitude at entry in ATR units (EXP-074 definition;
  `|C_i − segment_start_price|/ATR_i`), used only in Step 5b.

### Step 4 — Per-cell read statistics (per cell, per primitive)

Over each set's non-warmup/ATR-defined/non-clipped events:

- **Typical-range statistic (binding for the typical-range sub-screen):** `R_med = Q50(range_sym)` (ATR).
  Companion: `Q50(range_tot)`. (Median, not mean — the family's binding lesson is that the catastrophe tail
  corrupts means; the range is also heavy-tailed.)
- **Tail statistic (binding for the tail sub-screen):** `tailmass = #{outcome < b}/n`, boundary
  `b = median(outcome) − K_tail·MAD(outcome)`, `K_tail = 3.0`; `MAD = 0` → `tailmass = 0.0` with a
  `mad_zero` disclosure (never `0/0`). Companions: `q05 = Q05(outcome)`; Hartigan `dip_p` of `outcome`
  (`diptest`, deterministic) — reported, not binding.
- **`msofar_atr`-as-magnitude (descriptive, NON-BINDING context):** rank-biserial correlation of
  `msofar_atr` vs the q05-tail indicator (`outcome < Q05(outcome)`) **within the conditioned set** —
  EXP-074's separation re-examined as predictable magnitude. Reported per cell as an effect size with the
  explicit caveat that it is a **within-sample conditional** separation (not a vs-random availability), so it
  does **not** enter any binding `S` count (candidate-family evidence note).
- **Per-cell event-count denominators** (conditioned + matched-random, separately) disclosed; a cell with
  `< 30` usable events on a primitive is `UNDERPOWERED_DISCLOSED` and **excluded from that primitive's `S`
  count** (it cannot reliably beat random) — recorded, never dropped.
- **Output:** per (cell, primitive) `(R_med, range_tot_med, tailmass, q05, dip_p, mad_zero, rb_msofar,
  n_cond, n_rand, underpowered)` for the conditioned set and the matched-random set.

### Step 5 — Per-cell "beats-random" test (the per-cell gate input)

- **Method (generalizes the bite-check per-cell test):** for each read metric `θ ∈ {R_med, tailmass}`, the
  per-cell Δ-over-random and its one-sided lower bound:
  - point estimate `Δ̂ = θ_cond − θ_rand`;
  - **SE `s_cell` estimated ONCE per cell** by a **moving-block bootstrap** over the *conditioned* and
    *matched-random* event series (block length `xen.ass.default_block_length(n)`, `B_SE = 2000` resamples,
    fixed seed): `s_cell = sd(Δ̂*_b)`. The moving block accounts for temporal clustering of compression
    events (compression states cluster → naive `σ/√n` understates uncertainty);
  - **beats-random ⇔ `Δ̂ − 1.645·s_cell > 0`** (one-sided 95% lower bound > 0).
  - **Direction of "beats":** typical-range — conditioned range **larger** than random (`Δ̂_R > 0`); tail —
    conditioned `tailmass` **larger** than random (`Δ̂_tail > 0`, the "compression predicts the rare large
    excursion" hint, EXP-081 31/46). `q05` companion reported as `q05_rand − q05_cond` (deeper-under-cond)
    for context only.
- **Why this estimator (the genuine methodology decision — flag for Stage-4 governance):** it is the
  **faithful, feasible generalization of the GREEN bite-check**, which computes a per-cell `se` once and then
  varies only the point estimate under permutation (`empirical_permutation`: `se = delta.std/sqrt(n)` fixed,
  permuted means compared to `z·se`). We (i) replace the bite's independence-assuming `σ/√n` with a
  **moving-block bootstrap SE** (temporal-dependence-aware, conservative under positive autocorrelation —
  `s_cell ≥` naive SE), and (ii) hold `s_cell` fixed across permutations exactly as the bite does. The D2b
  gate is **self-calibrating** (bite §C): because `S*` is computed from the *same* per-cell test, any residual
  per-cell FP miscalibration is absorbed by the permuted-axis null. A two-sample (not paired) construction is
  used because conditioned and matched-random events are different timestamps (no natural pairing).
- **Simpler alternative considered:** nest a full bootstrap CI inside every permutation. Rejected — `N_PERM ×
  B` per cell is infeasible and the bite-check already establishes that fixing `s_cell` and permuting the
  point estimate is the calibrated construction.
- **Assumptions:** the dispersion `s_cell` is approximately invariant under the random-timing null (the null
  shifts the *mean* difference, not the cell's intrinsic outcome dispersion) — the same assumption the bite
  makes; reasonable and conservative.
- **Output:** per (cell, primitive, read) `(Δ̂, s_cell, ci_low, beats_random)`.

### Step 6 — Permuted-axis admission null (D2b — the binding gate; Stat test 3)

- **Realized axis statistics:** for each of the **4 sub-screens** `(primitive ∈ {HARAMI, NR7}) × (read ∈
  {typical-range, tail})`, `S = #cells-beat-random` over the ≤46 powered cells.
- **Permuted-axis null construction (faithful to D0 §D2b: "shuffle which timestamps are signal, preserving
  per-cell event counts and the regime/direction match"):**
  1. **Precompute a random-timing pool per (cell, primitive)** — draw a pool of
     `P_raw = min(n_bars, max(3000, 8·n_entries), 30000)` random-timing, same-regime-direction-eligible
     entries once (raw draw count, where `n_entries` = the cell's raw conditioned entries) and compute their
     per-event read metrics via Step 3 (one-time cost; no per-permutation path scan). The usable pool is what
     survives the Step-2/Step-3 warmup/ATR/clip filters. The floor (3000 raw) guarantees a representative
     random-timing law for every powered cell; the cap (30000 raw, and `n_bars` for small 4h cells) bounds
     memory; the `8·n_entries` scale keeps the pool comfortably larger than any `n_cond`-sized draw. (Frozen
     constants `POOL_RAW_MIN=3000`, `POOL_RAW_MULT=8`, `POOL_RAW_CAP=30000`.)
  2. **Each permutation `p` (of `N_PERM`):** per cell, draw a **fresh pseudo-signal** = an `n_cond`-sized
     **with-replacement** subsample from that cell's random pool (preserves the per-cell event count and the
     regime/direction match; the pseudo-signal is pure-noise conditioning run through the identical pipeline).
     Compute `Δ̂_p = θ_pseudo − θ_rand` and `beats_p = (Δ̂_p − 1.645·s_cell) > 0` using the **same fixed
     `s_cell`** (Step 5). `S_perm[p, sub] = Σ_cells beats_p`. **With-replacement is a deliberate vectorization
     choice** (it makes the permutation stream fully vectorized and deterministic); the ~10% within-draw
     repeats it induces are statistically immaterial for a *null* calibration over a pool of thousands, and
     the self-calibrating gate (bite §C) absorbs any residual per-cell test variation. This is the production
     realization of the D0 §D2b "shuffle which timestamps are signal" null — drawing `n_cond` random
     same-regime-eligible timestamps as the pseudo-signal is the faithful, scan-free instantiation of relabel
     ling `n_cond` timestamps as "signal," and is closer to D0 §D2b than the bite-check's idealized sign-flip
     abstraction (which only certified the gate is not vacuous / not impossible at `C=46`).
  3. **Within-axis multiplicity (the "screen 2 primitives × 2 reads, keep the best" risk):** the axis-level
     statistic is the **max across the 4 sub-screens**, `S_M = max_sub S`, with a **joint (max-statistic)
     permutation null** `S_perm_max[p] = max_sub S_perm[p, sub]` (same permutation index across sub-screens).
     `S* = Q95(S_perm_max)`; axis permutation p `p_M = (1 + #{S_perm_max ≥ S_M}) / (1 + N_PERM)`.
  4. **Per-sub-screen transparency (LESSON-001):** also report each sub-screen's own `S`, single-sub `S*` =
     `Q95(S_perm[·,sub])`, and single-sub perm-p — per-stratum, captioned, so no collapsed flag hides a
     per-read result.
- **`N_PERM`:** **5000** (production), with a **1000-vs-5000 MC-stability disclosure** (report `S*` and `p_M`
  at both; the routing must be invariant). Sensitivity band: `S*` at FWER ∈ {0.025, 0.05, 0.10}
  (`Q975/Q95/Q90` of `S_perm_max`); report the disposition at each — a pre-registered robustness sweep, not a
  selection.
- **Why max-statistic:** it is the exact multiplicity control for the D5 "typical-range **OR** tail may
  satisfy admission" across both primitives — generalizing the bite-checked single-read gate (which the joint
  null only *tightens*; the bite's "not impossible" still holds for the driving sub-screen). Flag for
  Stage-4 governance.
- **`INCONCLUSIVE` (no power):** if `S* ≥` the maximum attainable `S` at the realized powered-cell count (the
  permuted null cannot separate), the axis read is `INCONCLUSIVE` — disclosed, neither admit nor exonerate.
- **Output:** per sub-screen `(S, S*_sub, perm_p_sub)`; axis `(S_M, S*, p_M)`; the FWER band; the
  MC-stability table; the **frozen ranking metric** `z_M = (S_M − mean(S_perm_max)) / sd(S_perm_max)`
  (tie-break: trimmed-mean per-cell Δ of the driving sub-screen) — used at G-019.

### Step 7 — Magnitude-budget two-sided-cost check (binding for any magnitude admission; reuse `xen.capgeo_cost`)

- **Method:** for any read whose `S` clears its `S*`, test whether the **predictable range clears a two-sided
  cost**, per cell, in ATR units:
  - **harvestable range** = the conditioned read magnitude: typical-range → `R_med` (median symmetric
    excursion); tail → the conditioned tail magnitude `|q05|` (the rare large move the long-vol harvest
    targets).
  - **two-sided cost (ATR)** `cost2 = 2 · rt_cost_atr + fin_atr`, where `rt_cost_atr` = the EXP-085
    CONSERVATIVE per-instrument round-trip cost expressed in ATR (the straddle pays a round-trip on **each**
    of the two legs → ×2) and `fin_atr` = the EXP-085 bar-count financing over the cell's median holding time
    `TTP`/cap (per-instrument financing rate × median holding bars). Constants pulled from the EXP-085 cost
    table via `xen.capgeo_cost`, **not tuned**.
  - **per-cell budget** `net_atr = harvestable_range − cost2`; report per cell and the count `net_atr > 0`.
- **Interpretation (binding routing, recorded — not adjudicated here):** a **typical-range** admission whose
  `net_atr > 0` in a cell quorum is a directional/range-family candidate; a **tail-only** admission is a
  **long-vol** finding regardless of sign (routes to CF-VOLEXP-001 under the two-sided-cost harvest model,
  never a directional edge — design §8 guard). The magnitude-budget never *creates* an admission; it
  qualifies its economic meaning for G-019.
- **Why:** the reconciliation §3 harvest model requires any magnitude pass to clear a two-sided cost (the
  gross→net trap that ate AVWAP must not recur); reusing the EXP-085 cost overlay keeps the cost model frozen
  and consistent with Phase 018.
- **Output:** per-cell `(harvestable_range, cost2, net_atr)` and the per-read budget summary.

### Step 8 — Determinism & integrity guards

- **Method:** a second full pass (including the permutation stream at its fixed seed); assert the per-cell
  statistics table **and** the `(S, S*, p_M)` axis statistics are frame-identical (exact). Assert: holdout
  never sliced (metadata only); no domain-bar label crosses the analysis-slice boundary (fence, inherited);
  every path window's last index ≤ `train_edge_idx`; the Step-1 matched-random count reconciliation holds for
  all (cell, primitive). Record all seeds (`SEED_RANDOM`, `B_SE` seed, permutation seed-stream).
- **Why:** determinism + reconciliation + holdout-fence are the binding HALT conditions (scope; D6).
- **Output:** `determinism_ok`, `recon_all_ok`, `holdout_untouched` in `run_metadata.json`.

---

## Visualisations (≤ 5)

1. **Typical-range Δ-over-random heatmap** — per primitive (2 panels), 16×3 instrument×domain small-multiple
   of `Δ̂_R` with beats-random cells marked; shows where conditioned range exceeds random across the member set.
2. **Tail Δ-over-random heatmap** — per primitive (2 panels) of `Δ̂_tail` (with `q05` Δ annotation),
   beats-random cells marked; the formalization of the EXP-081 "31/46" tail hint.
3. **Permuted-axis null distribution** — histogram of `S_perm_max` with realized `S_M`, `S*` (Q95), and the
   FWER-band thresholds overlaid; the single most important plot — it *is* the admission decision.
4. **Representative conditioned-vs-random outcome distributions** — densest cells per domain per primitive,
   conditioned vs matched-random `outcome` overlaid, with the catastrophe boundary and (where `dip_p<0.05`)
   the bimodality flagged; the `msofar_atr` rank-biserial annotated.
5. **Magnitude-budget panel** — per cell `harvestable_range` vs `cost2` (ATR), `net_atr` sign-coded, per read
   that cleared `S*` (or, if none cleared, the typical-range read as the closest); the economic-meaning check.

All plots from the single analysis pass's bounded summaries (and bounded per-event arrays for plot 4) — no
data reloads or re-generation for plotting.

## Interpretation Guide (pre-defined, before results exist)

The experiment verdict is about completeness + integrity; the **admit/exonerate is G-019**. EXP-086 reports a
**provisional, NON-BINDING** disposition under the frozen D5 rule.

- **`SCREEN_DELIVERED`** iff, for both primitives across all 46 member cells, the per-cell two reads, the
  per-cell beats-random tests, the 4 sub-screen `S`/`S*`/perm-p, the axis `S_M`/`S*`/`p_M`, the FWER band, the
  magnitude-budget, and the descriptive D2a band are produced; determinism passes; matched-random
  reconciliation holds; holdout untouched — *whatever* the numbers look like.
- **Provisional `ADMITTED (NON-BINDING)`** iff `S_M > S*` **and** `p_M ≤ 0.05` (single-axis; G-019 applies the
  cross-axis Holm step-down over {M, X, (F)} that can only *raise* the adjusted p). Record **which** sub-screen
  drove it: a **tail-only** drive ⇒ flag **LONG-VOL** (CF-VOLEXP-001 harvest model); a **typical-range** drive
  ⇒ range/directional-family candidate; carry the Step-7 magnitude-budget result.
- **Provisional `EXONERATED (NON-BINDING)`** iff `S_M` falls within the D2a null band (≈17/46–28/46
  cells-beat-random) on **every** sub-screen (both primitives, both reads) — the single-series-magnitude cell
  is then provisionally dead (terminal-branch input to G-019).
- **`INCONCLUSIVE`** iff the permuted null cannot separate at the realized powered-cell count (no power) — a
  read/axis disclosed as neither admit nor exonerate.
- **HALT (process-level, route to developer)** iff *any*: second-pass statistics or axis statistics differ
  (non-determinism); a real-price/look-ahead/holdout-fence violation; or a matched-random count-reconciliation
  break. These are implementation bugs, not data shapes.
- **Descriptive disclosures (reported, NON-BINDING):** the D2a cells-beat-random count per sub-screen vs the
  EXP-081 coin-flip baseline; the `msofar_atr` rank-biserial per cell (within-sample conditional, **not** a
  vs-random availability); the `q05`/dip-p companions. None gates the verdict.
- **Prior (stated, does not move goalposts):** EXP-081 puts the prior **low** (typical range below random:
  `MAE_q90` Δ −0.719, 9/46) with the **only** positive hint tail-concentrated (`tailmass` 0.0526 vs 0.0437,
  31/46). A typical-range admission would be surprising; a tail-read admission is the pre-registered
  most-likely (still low-prior) positive outcome and is **long-vol**, never directional.
- **No goalpost movement:** the read definitions, `K_tail=3.0`, the ≥30 floor, the cap basis, the gate
  constants (`z=1.645`, `S*=Q95`, FWER band), `N_PERM=5000`, and the max-statistic within-axis control are
  frozen by this plan + D0; G-019 freezes the *rule*, not the story the numbers tell.

## Implementation Safety Constraints (for `experiment-developer`)

- **Imports → path setup → constants → I/O helpers → pure computation → plotting → orchestration → `main()`**
  (VAL-001-style sectioning). No directory creation / file writes / data loads / plotting at import time.
- **Temporal ordering:** all ordering/alignment by `CloseTime`/epoch, never bar index for cross-view
  alignment; assert `CloseTime` sorted after slicing; align harami events to the confirming domain bar.
- **Holdout discipline:** read only the first `train_cutoff` 1-minute rows
  (`train_cutoff = int(int(total_rows·0.7)·0.7)`); locate the split via Parquet metadata only; never
  materialize a row at/beyond `analysis_rows`; forward path windows clip at `train_edge_idx`; the random pool
  and permutation draw only from `[0, train_edge_idx]`.
- **Real-price discipline:** every `range_sym/range_tot/outcome/msofar_atr/ATR` on real domain OHLC; HA only
  for harami entry detection. NR7 on real OHLC.
- **Reuse, don't edit:** `xen.domain_bars`, `xen.heiken_ashi_generator`, `xen.ha_harami`,
  `xen.capgeo_substrates` (`random_entries`, `_real_ohlc`, `_ma_segment_moves`, `live_in_progress_state`
  bridge, `ATR_PERIOD`), `xen.capgeo_geometry` (`lifetime_path_geometry`, `tail_stats`, `K_TAIL`,
  `DIP_ALPHA`), `xen.expectancy` (`adaptive_time_caps_by_epoch`), `xen.capgeo_cost` (two-sided cost overlay),
  `xen.ass` (`default_block_length`, moving-block bootstrap), `xen.zigzag` (`wilder_atr`) — all unchanged.
- **New code only in two modules (≤2):** `xen.compression_primitives` (raw-harami-inside-bar + NR7 entry
  indices, returning EXP-080-compatible `EntrySet`-style structures) and `xen.availability_gate` (per-cell
  beats-random test + the precomputed-pool permuted-axis null + `S*`/`p_M` + max-statistic within-axis control
  + Holm helper), reusable by EXP-087/088.
- **Denominators / zero-baseline:** beats-random denominators = per-cell usable-event counts (disclosed,
  conditioned + random separately); `tailmass` zero-tail → `0.0` with denominator (never `0/0`); `mad_zero`
  flagged; warmup/ATR-undefined/clipped-empty counted and excluded (never folded into a statistic); permuted-p
  uses the `(1+·)/(1+N_PERM)` add-one form; no metric as a percentage over a zero baseline.
- **Bounded iteration / progress / performance:** `tqdm` over the (cell × primitive) outer loop; the random
  pool computed **once** per (cell, primitive) (raw draw `min(n_bars, max(3000, 8·n_entries), 30000)`;
  `POOL_RAW_MIN=3000`/`POOL_RAW_MULT=8`/`POOL_RAW_CAP=30000`); permutations draw an `n_cond`-sized
  **with-replacement** pseudo-signal subsample of the precomputed pool (no per-permutation path scan; the
  with-replacement device is justified in Step 6.2 and the `availability_gate._perm_beats` docstring); per-cell
  memory bounded (do not retain all domain frames);
  `N_PERM=5000`, `B_SE=2000`, all seeds recorded in `run_metadata.json`.
- **Vectorization discipline:** vectorize intra-window max/argmax and the subsample-and-aggregate permutation
  inner loop with NumPy; keep the outer event loop and any causal step explicit — no transformation that
  changes sample membership, temporal ordering, denominators, metric definitions, or causal/streaming
  semantics. The permuted-axis null preserves per-cell counts + regime/direction match by construction.
- **Outputs:** `results/cell_availability.parquet`/`.csv` (per cell × primitive: both reads, conditioned +
  random stats, `Δ̂`, `s_cell`, `ci_low`, `beats_random`, `n_cond`, `n_rand`, `underpowered`, `rb_msofar`,
  `dip_p`, `mad_zero`, magnitude-budget); `results/axis_admission.json` (per sub-screen `S`/`S*`/perm-p; axis
  `S_M`/`S*`/`p_M`; FWER band; MC-stability 1000-vs-5000; ranking `z_M`; provisional disposition captioned
  NON-BINDING); `results/per_event_geometry.parquet` (bounded, for plot 4); `results/run_metadata.json`
  (seeds, module hashes, frozen constants, determinism/recon/holdout flags, `holdout_untouched=true`,
  `counted_test_reads=0`, `candidate_slots=0`); the ≤5 plots under `plots/`.

## Complexity Check

- **Statistical tests: 3 / 3** — (1) per-cell Δ-over-random beats-random test (moving-block bootstrap SE +
  one-sided lower bound); (2) Hartigan dip test (tail bimodality companion); (3) permuted-axis admission null
  (the binding D2b gate). The `msofar_atr` rank-biserial is a descriptive effect size; the magnitude-budget is
  arithmetic.
- **Visualisations: 5 / 5.**
- **New modules: 2 / 2** — `xen.compression_primitives`, `xen.availability_gate`. All other logic reuses
  existing frozen modules.
