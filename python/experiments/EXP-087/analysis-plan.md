# Analysis Plan: Experiment EXP-087

**Screen X — cross-sectional relative-strength / directional-favourable availability (Phase 019 family-selection; EXP-081/EXP-086 clone, axis + endpoint swapped; TRAIN-only, gross).**

Phase 019 · Family-Selection Availability Screen · Axis **X** · `CF-XSECT-001/HYP-001` · 0 candidate slots · 0 counted TEST reads.
Companions: `scope.md`; Phase 019 D0 (`docs/experiments-docs/checkpoints/2026-06-22-019-family-selection-availability-screen/D0-predeclarations.md`, §D2b/§D3.X/§D4/§D5/§D6) + `D0-amendment-002-screen-x-conditioning-freeze.md` (COND-XSRANK + COND-XSDIV; 20-bar lookback, both tails; forward-filled union grid); GREEN bite-check (`…/bite-check/bite_check.py`, report sha256 `208dfb3f…`).

## Objective

Produce, per member cell and per frozen cross-sectional primitive, the **directional-favourable
availability statistic** that the G-019 rubric converts into an **admit / exonerate / inconclusive**
disposition for the **cross-sectional × directional** cell of the 2×2 — a **single read** (D3.X; the
cross-sectional anomaly is directional by construction, so unlike Screen M there is no split typical-range /
tail and no magnitude-budget):

- **Favourable-availability read** — per-cell Δ-over-matched-random of the directional-favourable median
  excursion `MFE_med` (ATR units), where the entry direction is the cross-sectional decile sign (LONG on
  relative strength, SHORT on relative weakness). This is exactly EXP-081's favourable-availability endpoint,
  re-pointed at the cross-sectional conditioning.

The binding decision rule is the **D2b multiplicity-adjusted permuted-axis admission gate** (reused from
EXP-086, `xen.availability_gate`); the binding **admit/exonerate adjudication is G-019**, not this
experiment. The experiment verdict is **`SCREEN_DELIVERED`** if the statistics + gate inputs are produced
deterministically for the whole member set; it HALTs only on non-determinism, a real-price/look-ahead/
holdout-fence violation, a matched-random count-reconciliation break, or a cross-sectional-alignment
(non-causal forward-fill) defect. A **provisional** single-axis disposition is reported, captioned
**NON-BINDING pending the G-019 cross-axis Holm step-down**.

All estimators are non-parametric / resampling-based (median, proportion, moving-block bootstrap,
label-permutation). No normality, stationarity, i.i.d., or constant-volatility assumption gates any verdict.
Per-stratum reporting throughout (LESSON-001); no pooled-as-verdict.

## Fixed inputs (frozen upstream — not re-derived here)

- **Member set:** **46 EXP-080-READY instrument×domain cells** (16 instruments × {15m,1h,4h} minus US500-4h,
  JP225-4h `COVERAGE_EXCLUDED`). Realized per-primitive cell count matches the bite-check `C=46`, so the
  calibrated gate applies as-is.
- **Conditioning primitives (two, frozen at D0-amendment-002; neither tuned):**
  - **`COND-XSRANK`** — at each domain timestamp on the forward-filled union grid, rank every instrument's
    trailing **20-domain-bar** real-price log return across the synchronized 16-instrument cross-section;
    entry fires LONG when the instrument is in the **top decile**, SHORT in the **bottom decile**.
  - **`COND-XSDIV`** — the same trailing 20-bar return **minus the equal-weight basket mean** across the
    cross-section; entry fires LONG/SHORT on the **top/bottom decile** of the divergence distribution.
  - Lookback **20** domain bars; both tails; causal (the 20-bar return, rank, and divergence at `t` use only
    bars completed strictly ≤ `t`); decile cutoff on the realized cross-sectional distribution at each
    timestamp.
- **Universe synchronization (frozen, D0-amendment-002):** the 16 VAL-005 instruments (no DE30), on a
  **forward-filled union timestamp grid** per domain — each instrument contributes its **last completed bar**
  (strictly causal forward-fill, never a future bar). A timestamp with fewer than `MIN_XS_INSTR` synchronized
  instruments to define a decile is excluded and disclosed (`MIN_XS_INSTR = 8` frozen — half the universe;
  never forced).
- **Matched-random control (`SUB-RANDOM`, frozen construction reused):** per cell **and per primitive**, a
  fixed-seed random-timing draw matched to that primitive's event count **and the conditioned set's per-cell
  LONG/SHORT proportion** (so the random direction labels mirror the conditioned mix and the Δ isolates the
  cross-sectional *timing/conditioning*, not the direction). Reuses the EXP-080/081 `random_entries`
  construction; seed key `[SEED_RANDOM, cell_index, primitive_id, n_target]`. This is the **descriptive**
  baseline (D2a); the **binding** null is the permuted-axis gate (D2b), distinct.
- **Read region:** TRAIN sub-split `[0, train_cutoff)`, `train_cutoff = int(int(total_rows·0.7)·0.7)`.
  Analysis-TEST and final-30% holdout never sliced; the union grid is built from TRAIN-only domain-bar
  `CloseTime`s and the forward-fill consults no TEST/holdout bar.
- **Per-event ATR:** Wilder ATR(14) (`ATR_PERIOD=14`) on real domain bars (`xen.zigzag.wilder_atr`).
- **Adaptive cap:** `xen.expectancy.adaptive_time_caps_by_epoch`, frozen `TIMECAP_*` (EXP-068/070), the same
  cap basis EXP-081/086 used (cell MA-segment move-duration tempo, applied to every primitive + its
  matched-random + the permutation pool by entry epoch). No cap tuning.
- **Event floor:** ≥ **30** usable events per cell for binding-gate inclusion.
- **Gate constants (GREEN bite-check, unchanged; `xen.availability_gate`):** per-cell one-sided lower-bound
  test at `z = 1.645`; axis FWER `0.05`; `S* = Q95` of the permuted-axis null; sensitivity band
  FWER ∈ {0.025, 0.05, 0.10}; `N_PERM = 5000` (with 1000-vs-5000 MC-stability disclosure); Holm step-down
  across axes **applied at G-019**.

---

## Methodology

### Step 1 — Cross-section construction & cohort (per domain, then per cell, per primitive)

- **Method:** lazy `pl.scan_parquet` per instrument; slice the first `train_cutoff` 1-minute rows; assert
  `CloseTime` sorted; build 15m/1h/4h bars via `xen.domain_bars.build_domain_bars` (`min_coverage=0.90` +
  analysis-boundary fence). **Per domain:** form the **union** `CloseTime` grid across all 16 instruments'
  TRAIN domain bars; forward-fill each instrument's last completed bar onto the grid (causal `join_asof`
  backward / `merge_asof` direction='backward'); compute each instrument's trailing 20-bar real-price log
  return on its own completed bars; at each grid timestamp form the cross-sectional `COND-XSRANK` rank and
  `COND-XSDIV` divergence-from-basket-mean across instruments present (≥ `MIN_XS_INSTR`); mark top/bottom
  decile membership with direction `d ∈ {+1 (LONG), −1 (SHORT)}`. Map each fired event back to the
  instrument's own domain-bar index (the bar whose `CloseTime` == the grid timestamp; forward-filled
  timestamps where the instrument has no completed bar at that grid point do **not** generate that
  instrument's events). For each (cell, primitive) draw the count-and-direction-matched `SUB-RANDOM` set.
- **Why:** Screen X reuses the certified readiness scaffolding (EXP-080 member set, `random_entries`, domain
  generation) and the EXP-086 gate module, swapping only the conditioning to the cross-section. Building the
  cross-section on the union grid with a causal forward-fill is the frozen D0-amendment-002 synchronization;
  mapping events to each instrument's own domain bar keeps every downstream metric on the real domain-bar
  timeline (no bar-index cross-view alignment — alignment is by `CloseTime`).
- **Reconciliation guard (binding):** assert per cell, per primitive, that the matched-random count equals the
  conditioned count (`n_random == n_cond`), that the random LONG/SHORT split matches the conditioned split
  within rounding, and that both index arrays lie within `[0, train_edge_idx]`. A mismatch is a HALT
  (construction/harness bug, not a data shape).
- **Look-ahead guard (binding):** assert the forward-fill is backward-only (every filled value's source
  `CloseTime` ≤ grid timestamp) and the 20-bar return window ends at or before the grid timestamp. A
  forward-looking fill or window is a HALT.
- **Simpler alternative considered:** intersection-only grid (timestamps where all 16 instruments have a
  completed bar). Rejected at D0-amendment-002 — it discards crypto-weekend / off-session bars and shrinks 4h
  cells below the ≥30 floor, breaking the `C=46` calibration.
- **Assumptions:** deterministic generators (VAL-005/EXP-080 validated); causal `join_asof` (standard); holds.
- **Output:** per (cell, primitive) conditioned + matched-random entry index / epoch / direction arrays +
  `recon_ok`, plus per-(domain) excluded-timestamp counts (`< MIN_XS_INSTR`).

### Step 2 — Per-event adaptive cap

- **Method:** identical cap basis to EXP-081/086 — one cap basis per cell from
  `_ma_segment_moves(real_ohlc)` → `adaptive_time_caps_by_epoch(entry_epoch, …)` with frozen `TIMECAP_*`,
  applied to the conditioned set, the matched-random set, **and** the permutation random pool (Step 5) by
  entry epoch. Warmup events (fewer than `min_moves` prior durations) are **disclosed and excluded**, never
  silently capped.
- **Why:** keeps the lookforward window and the matched-random control on the same validated cell-tempo cap as
  EXP-081/086 (fair attribution; the null inherits the identical cap-by-time step function). The cap basis is
  the cell MA-segment tempo reused unchanged — **not** a new free choice (flag for Stage-4 governance, same as
  EXP-086 Step 2).
- **Output:** per-event integer cap, `warmup` mask, per (cell, primitive, set).

### Step 3 — Directional-favourable realized geometry on real OHLC (reuse `xen.capgeo_geometry`)

- **Method:** for each non-warmup, ATR-defined event with entry index `i`, cap `c`, **direction `d`** (the
  cross-sectional decile sign), window `W = [i+1, min(i+c, train_edge_idx)]` on **real** domain OHLC, via
  `lifetime_path_geometry(..., direction=d)`: take the **directional-favourable** excursion
  `MFE = max_{t∈W} d·(price_extreme_t − C_i)/ATR_i` (the favourable side in the entry direction — for LONG the
  up-excursion, for SHORT the down-excursion). The per-cell endpoint is `MFE` per event (median taken in Step
  4). Events whose window is empty after TRAIN-edge clipping are excluded with a `clipped_empty` count.
- **Why:** EXP-081's favourable-availability read, reused module, no exit applied; the direction is the
  cross-sectional sign (the axis's information), not the MA-regime sign used in EXP-086's tail read. Real
  prices only — the cross-sectional conditioning is itself computed from real returns, so no synthetic price
  enters anywhere.
- **Vectorization discipline:** intra-window max/argmax vectorized with NumPy; outer event loop explicit and
  cap-bounded (causal, no look-ahead). `tqdm` over the (cell × primitive) loop.
- **Output:** per-event `MFE` (ATR) arrays per (cell, primitive, set).

### Step 4 — Per-cell read statistic (per cell, per primitive)

Over each set's non-warmup / ATR-defined / non-clipped events:

- **Favourable-availability statistic (binding):** `MFE_med = Q50(MFE)` (ATR), conditioned and matched-random
  separately (median, not mean — the family's binding lesson is that the catastrophe tail corrupts means;
  EXP-081 used the median favourable read).
- **Per-cell event-count denominators** (conditioned + matched-random, separately) disclosed; a cell with
  `< 30` usable events on a primitive is `UNDERPOWERED_DISCLOSED` and **excluded from that primitive's `S`
  count** (it cannot reliably beat random) — recorded, never dropped.
- **Output:** per (cell, primitive) `(MFE_med_cond, MFE_med_rand, n_cond, n_rand, long_frac, underpowered)`.

### Step 5 — Per-cell "beats-random" test + permuted-axis admission null (reuse `xen.availability_gate`)

The binding gate is the EXP-086 module **unchanged**; Screen X supplies it the directional-`MFE`
per-event arrays. Two sub-screens (`COND-XSRANK`, `COND-XSDIV`), one read each (`STAT_MEDIAN` on `MFE`).

- **Per-cell beats-random (`run_sub_screen` → `cell_se`):** point estimate `Δ̂ = MFE_med_cond −
  MFE_med_rand`; SE `s_cell` estimated **once per cell** by the module's **moving-block bootstrap** over the
  conditioned and matched-random `MFE` series (`B_SE = 2000`, fixed seed, block length
  `xen.ass.default_block_length(n)` — accounts for temporal clustering of cross-sectional extremes);
  **beats-random ⇔ `Δ̂ − 1.645·s_cell > 0`** (one-sided 95% lower bound > 0; conditioned favourable
  availability **larger** than random). This is the faithful per-cell test the GREEN bite-check certified,
  reused verbatim.
- **Permuted-axis null (`run_sub_screen`, D2b — Stat test 2):** per cell, a **random-timing pool** matched to
  the conditioned LONG/SHORT mix is precomputed once (raw draw
  `min(n_bars, max(POOL_RAW_MIN, POOL_RAW_MULT·n_entries), POOL_RAW_CAP)`,
  `POOL_RAW_MIN=3000`/`POOL_RAW_MULT=8`/`POOL_RAW_CAP=30000` frozen, directional `MFE` via Step 3); each
  permutation draws an `n_cond`-sized with-replacement pseudo-signal subsample (preserving per-cell event
  count and direction mix — pure-noise cross-sectional conditioning run through the identical pipeline),
  recomputes `Δ̂_p` and `beats_p` with the **same fixed `s_cell`**; `S_perm[p, sub] = Σ_cells beats_p`. This
  is the production realization of D0 §D2b "shuffle which timestamps are signal, preserving per-cell event
  counts and the regime/direction match" — the same construction EXP-086 used and the bite-check certified;
  the with-replacement device and its immateriality for a null calibration are documented in
  `availability_gate._perm_beats`.
- **Within-axis multiplicity (`combine_axis`):** axis statistic `S_X = max_sub S` over the 2 sub-screens with
  the **joint (max-statistic) permutation null** `S_perm_max[p] = max_sub S_perm[p, sub]`; `S* =
  Q95(S_perm_max)`; axis permutation p `p_X = (1 + #{S_perm_max ≥ S_X}) / (1 + N_PERM)`. Per-sub-screen own
  `S`/`S*`/perm-p reported for transparency (per-stratum, LESSON-001). The max-statistic over the 2 primitives
  is the exact control for D5 "either primitive may satisfy admission" (it only *tightens* the bite-checked
  single-read gate). **Multiplicity caution (binding, candidate-family §CF-XSECT-001):** cross-sectional
  ranking manufactures the most cells of any screen → this joint null is the load-bearing control here.
- **`N_PERM = 5000`** (production) with the **1000-vs-5000 MC-stability disclosure** (routing must be
  invariant). Sensitivity band `S*` at FWER ∈ {0.025, 0.05, 0.10} (`Q975/Q95/Q90`) — a pre-registered
  robustness sweep, not a selection.
- **`INCONCLUSIVE` (no power):** if `S* ≥` the maximum attainable `S` at the realized powered-cell count, the
  axis is `INCONCLUSIVE` — disclosed, neither admit nor exonerate.
- **Output:** per sub-screen `(S, S*_sub, perm_p_sub)`; axis `(S_X, S*, p_X)`; FWER band; MC-stability table;
  the **frozen ranking metric** `z_X = (S_X − mean(S_perm_max)) / sd(S_perm_max)` (tie-break: trimmed-mean
  per-cell Δ of the driving sub-screen) — used at G-019.

### Step 6 — Determinism & integrity guards

- **Method:** a second full pass (including the permutation stream at its fixed seed); assert the per-cell
  statistics table **and** the `(S, S*, p_X)` axis statistics are frame-identical (exact). Assert: holdout
  never sliced (metadata only); no domain-bar label crosses the analysis-slice boundary (fence, inherited);
  every path window's last index ≤ `train_edge_idx`; the forward-fill is backward-only; the Step-1
  matched-random count + direction reconciliation holds for all (cell, primitive). Record all seeds
  (`SEED_RANDOM`, `B_SE` seed, permutation seed-stream).
- **Why:** determinism + reconciliation + holdout-fence + causal-fill are the binding HALT conditions (scope;
  D6).
- **Output:** `determinism_ok`, `recon_all_ok`, `causal_fill_ok`, `holdout_untouched` in `run_metadata.json`.

---

## Visualisations (≤ 4)

1. **Favourable-availability Δ-over-random heatmap** — per primitive (2 panels), 16×3 instrument×domain
   small-multiple of `Δ̂_MFE` with beats-random cells marked; where conditioned favourable availability
   exceeds random across the member set.
2. **Permuted-axis null distribution** — histogram of `S_perm_max` with realized `S_X`, `S*` (Q95), and the
   FWER-band thresholds overlaid; the single most important plot — it *is* the admission decision.
3. **Representative conditioned-vs-random favourable-excursion distributions** — densest cells per domain per
   primitive, conditioned vs matched-random `MFE` overlaid, medians marked.
4. **Cells-beat-random vs the D2a coin-flip band** — per primitive, realized `S` against the EXP-081
   ≈17/46–28/46 null band and `S*`; the descriptive context for the binding gate.

All plots from the single analysis pass's bounded summaries (and bounded per-event arrays for plot 3) — no
data reloads or re-generation for plotting.

## Interpretation Guide (pre-defined, before results exist)

The experiment verdict is about completeness + integrity; the **admit/exonerate is G-019**. EXP-087 reports a
**provisional, NON-BINDING** disposition under the frozen D5 rule.

- **`SCREEN_DELIVERED`** iff, for both primitives across all 46 member cells, the per-cell favourable-read
  statistic, the per-cell beats-random test, the 2 sub-screen `S`/`S*`/perm-p, the axis `S_X`/`S*`/`p_X`, the
  FWER band, the MC-stability table, and the descriptive D2a band are produced; determinism passes;
  matched-random reconciliation + causal-fill hold; holdout untouched — *whatever* the numbers look like.
- **Provisional `ADMITTED (NON-BINDING)`** iff `S_X > S*` **and** `p_X ≤ 0.05` (single-axis; G-019 applies the
  cross-axis Holm step-down over {M, X, (F)} that can only *raise* the adjusted p). Record **which** primitive
  drove it. A Screen-X admission routes to a **directional** cross-sectional family (CF-XSECT-001), not the
  long-vol harvest model (that is Screen M only).
- **Provisional `EXONERATED (NON-BINDING)`** iff `S_X` falls within the D2a null band (≈17/46–28/46
  cells-beat-random) on **every** sub-screen (both primitives) — the cross-sectional × directional cell is
  then provisionally dead, and (per design §7) **price-derived information, single-series *and* relational, is
  exhausted on this dataset** — the terminal-branch input to G-019.
- **`INCONCLUSIVE`** iff the permuted null cannot separate at the realized powered-cell count (no power) — the
  axis disclosed as neither admit nor exonerate.
- **HALT (process-level, route to developer)** iff *any*: second-pass statistics differ (non-determinism); a
  real-price/look-ahead/holdout-fence violation; a matched-random count/direction reconciliation break; or a
  non-causal forward-fill. These are implementation bugs, not data shapes.
- **Descriptive disclosures (reported, NON-BINDING):** the D2a cells-beat-random count per sub-screen vs the
  EXP-081 coin-flip baseline; per-cell `long_frac`; per-domain `< MIN_XS_INSTR` excluded-timestamp counts.
  None gates the verdict.
- **Prior (stated, does not move goalposts):** cross-sectional relative strength is the **a-priori favourite
  on mechanism grounds** (the one axis never varied; a demonstrably non-random anomaly elsewhere) but carries
  **no in-programme evidence** — it is explicitly a bet, and Screen X exists to kill it cheaply if wrong. The
  multiplicity gate matters most here (most manufactured cells); a lucky single cell must **not** admit the
  axis.
- **No goalpost movement:** the primitive definitions, lookback 20, both-tail deciles, `MIN_XS_INSTR=8`, the
  ≥30 floor, the cap basis, the gate constants (`z=1.645`, `S*=Q95`, FWER band), `N_PERM=5000`, and the
  max-statistic within-axis control are frozen by this plan + D0/D0-amendment-002; G-019 freezes the *rule*,
  not the story the numbers tell.

## Implementation Safety Constraints (for `experiment-developer`)

- **Imports → path setup → constants → I/O helpers → pure computation → plotting → orchestration → `main()`**
  (VAL-001-style sectioning). No directory creation / file writes / data loads / plotting at import time.
- **Temporal ordering / cross-sectional alignment:** all ordering/alignment by `CloseTime`/epoch, **never bar
  index** for cross-view alignment; build the union grid and forward-fill by `CloseTime`; the `join_asof` /
  `merge_asof` must be **backward-only** (causal); assert `CloseTime` sorted after slicing and before any
  asof-join.
- **Holdout discipline:** read only the first `train_cutoff` 1-minute rows
  (`train_cutoff = int(int(total_rows·0.7)·0.7)`); locate the split via Parquet metadata only; never
  materialize a row at/beyond `analysis_rows`; the union grid spans TRAIN domain bars only; forward path
  windows clip at `train_edge_idx`; the random pool and permutation draw only from `[0, train_edge_idx]`.
- **Real-price discipline:** every `MFE / ATR`, the 20-bar return, and the basket mean on **real** domain
  OHLC; no synthetic (HA/Renko) price anywhere (Screen X uses no chart-type generator).
- **Reuse, don't edit:** `xen.availability_gate` (`CellReadInput`, `run_sub_screen`, `combine_axis`,
  `holm_adjust`, `STAT_MEDIAN`, gate constants — **unchanged**), `xen.domain_bars`, `xen.capgeo_substrates`
  (`random_entries`, `_real_ohlc`, `_ma_segment_moves`, `ATR_PERIOD`), `xen.capgeo_geometry`
  (`lifetime_path_geometry`), `xen.expectancy` (`adaptive_time_caps_by_epoch`), `xen.ass`
  (`default_block_length`, moving-block bootstrap), `xen.zigzag` (`wilder_atr`) — all unchanged.
- **New code only in ONE module (≤1):** `xen.cross_sectional` — the forward-filled union-grid builder, the
  20-bar trailing-return computation, `COND-XSRANK` rank and `COND-XSDIV` divergence with top/bottom-decile
  directional membership, returning EXP-080-compatible `EntrySet`-style structures (entry index + epoch +
  direction per cell). No edits to the EXP-086 gate module or any frozen generator.
- **Denominators / zero-baseline:** beats-random denominators = per-cell usable-event counts (disclosed,
  conditioned + random separately); warmup / ATR-undefined / clipped-empty / `< MIN_XS_INSTR` counted and
  excluded (never folded into a statistic); permuted-p uses the `(1+·)/(1+N_PERM)` add-one form; no metric as
  a percentage over a zero baseline.
- **Bounded iteration / progress / performance:** `tqdm` over the (cell × primitive) outer loop; the union
  grid built **per domain** then released (do not retain all 16 instruments' domain frames across domains);
  the random pool computed **once** per (cell, primitive); permutations draw an `n_cond`-sized
  with-replacement pseudo-signal subsample (no per-permutation path scan); `N_PERM=5000`, `B_SE=2000`, all
  seeds recorded in `run_metadata.json`.
- **Vectorization discipline:** vectorize the asof-join, the trailing-return / rank / divergence computation,
  intra-window max/argmax, and the subsample-and-aggregate permutation inner loop with Polars/NumPy; keep the
  outer event loop and any causal step explicit — no transformation that changes sample membership, temporal
  ordering, denominators, metric definitions, or causal/streaming semantics. The permuted-axis null preserves
  per-cell counts + direction mix by construction.
- **Outputs:** `results/cell_availability.parquet`/`.csv` (per cell × primitive: `MFE_med` conditioned +
  random, `Δ̂`, `s_cell`, `ci_low`, `beats_random`, `n_cond`, `n_rand`, `long_frac`, `underpowered`);
  `results/axis_admission.json` (per sub-screen `S`/`S*`/perm-p; axis `S_X`/`S*`/`p_X`; FWER band;
  MC-stability 1000-vs-5000; ranking `z_X`; provisional disposition captioned NON-BINDING);
  `results/per_event_geometry.parquet` (bounded, for plot 3); `results/run_metadata.json` (seeds, module
  hashes, frozen constants, determinism/recon/causal-fill/holdout flags, `holdout_untouched=true`,
  `counted_test_reads=0`, `candidate_slots=0`); the ≤4 plots under `plots/`.

## Complexity Check

- **Statistical tests: 2 / 2** — (1) per-cell Δ-over-random beats-random test (moving-block bootstrap SE +
  one-sided lower bound, via `xen.availability_gate.cell_se`); (2) permuted-axis admission null (the binding
  D2b gate, via `run_sub_screen`/`combine_axis`). (Screen X has no dip test and no magnitude-budget — it is
  the directional-favourable single-read clone, lighter than Screen M's 3.)
- **Visualisations: 4 / 4.**
- **New modules: 1 / 1** — `xen.cross_sectional`. The binding gate (`xen.availability_gate`) and all geometry/
  substrate/cap logic reuse existing frozen modules.
