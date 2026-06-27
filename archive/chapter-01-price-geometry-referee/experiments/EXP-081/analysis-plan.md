# Analysis Plan: Experiment EXP-081

**Per-substrate realized return-structure characterization (4 frozen substrates × 46 member cells; 5-year data; TRAIN-only, gross).**

Phase 018 · CF-CAPGEO-001 · HYP-002 · 0 candidate slots · 0 counted TEST reads.
Companion: `scope.md`; Phase 018 D0 (`docs/experiments-docs/checkpoints/2026-06-20-018-capgeo-exit-geometry/D0-predeclarations.md`, §D3/§D6/§D9).

## Objective

Produce, per member substrate-cell, the **frozen D3-input return-structure statistics** that EXP-082's
mechanical exit-derivation rule consumes — favourable-capture geometry (`MFE_med`, `MFE_q40`),
capture-time geometry (`TTP_med`, `TTP_q75`), adverse excursion (`MAE_q90`), the bimodality/catastrophe
boundary (`m_anti`), and the minority-mass / left-tail read (`tailmass`, `q05`) — plus a **non-binding
`ASS` discovery disclosure** (expectancy + median + tail). This is a **characterization**: there is no
edge/pass/viability verdict. The experiment verdict is **CHARACTERISATION_DELIVERED** if the statistics
are produced deterministically for every member cell; it HALTs only on non-determinism, a
real-price/look-ahead/holdout-fence violation, or an EXP-080 entry-count reconciliation break.

All estimators are non-parametric (quantile / KDE / bootstrap / Hartigan dip). No normality,
stationarity, i.i.d., or constant-volatility assumption is used anywhere.

## Fixed inputs (frozen upstream — not re-derived here)

- **Member set:** 4 substrates × 46 EXP-080-READY instrument×domain cells = **184 substrate-cells**
  (16 instruments × {15m,1h,4h} minus US500-4h, JP225-4h `COVERAGE_EXCLUDED`).
- **Frozen entry harness:** `xen.capgeo_substrates` unchanged (`avwap_entries`, `harami_native_entries`,
  `random_entries`); seed `SEED_RANDOM = 20260621`, draw key `np.random.default_rng([SEED_RANDOM,
  cell_index, n_target])` exactly as EXP-080.
- **Read region:** TRAIN sub-split `[0, train_cutoff)`, `train_cutoff = int(int(total_rows*0.7)*0.7)`.
  Analysis-TEST and final-30% holdout never sliced.
- **Per-event ATR:** Wilder ATR(14) (`ATR_PERIOD=14`) on real domain bars (reuse `xen.zigzag.wilder_atr`,
  already used by the harness).
- **Catastrophe boundary constant:** `K_tail = 3.0` (D9 frozen). **Event floor:** ≥ 30.

---

## Methodology

### Step 1 — Cohort construction & EXP-080 reconciliation (per cell)

- **Method:** Lazy `pl.scan_parquet` per instrument; slice the first `train_cutoff` 1-minute rows; assert
  `CloseTime` sorted; build 15m/1h/4h bars via `xen.domain_bars.build_domain_bars` (`min_coverage=0.90` +
  fence); generate HA candles (`xen.heiken_ashi_generator`) for harami. Reproduce each substrate's frozen
  entries via `xen.capgeo_substrates`. `SUB-RANDOM` = the **EXP-080 headline draw** (harami-count-matched,
  `n_target = harami_count`, key `[SEED_RANDOM, cell_index, harami_count]`).
- **Why:** EXP-081 characterizes the *same* frozen entry objects EXP-080 certified READY; it must not
  re-derive or perturb them. The harami substrates share one entry population (EXP-080
  `harami_entry_identity_all_cells=true`), so their geometry is identical by construction — characterized
  and reported separately, with the identity disclosed.
- **Reconciliation guard (binding):** because EXP-080 read the full first-70%-of-analysis slice while
  EXP-081 reads the first-70%-of-analysis **TRAIN sub-split** (`[0, train_cutoff)` ⊂ EXP-080 slice), the
  EXP-081 entry set per substrate-cell must equal the **EXP-080 entries restricted to `[0,
  train_cutoff)`** (entry indices/epochs frame-identical). Assert this exactly; a mismatch is a HALT
  (indicates a construction or harness drift bug, not a data shape).
- **Simpler alternative considered:** regenerate entries on the TRAIN slice directly (no restriction
  check). Rejected — without the explicit restriction-equality assertion against EXP-080 we lose the
  audit anchor that the entries are the certified objects.
- **Assumptions:** deterministic generators (validated VAL-005 / EXP-080); holds.
- **Output:** per substrate-cell entry index/epoch arrays on TRAIN + a `recon_ok` flag.

### Step 2 — Per-event adaptive time cap (the lookforward window)

- **Method:** One **cap basis per cell**: `seg = xen.capgeo_substrates._ma_segment_moves(real_ohlc)` (the
  validated MA(20,50)-crossover confirmed-move set used by the harami substrate and by EXP-068). For each
  substrate, `n_event, warmup = xen.expectancy.adaptive_time_caps_by_epoch(entry_epoch=<substrate
  entries>, move_confirm_epoch=seg["confirm_epoch"], confirm_idx=seg["confirm_idx"])` with the frozen
  `TIMECAP_WINDOW/TIMECAP_K/TIMECAP_FLOOR/TIMECAP_MIN_MOVES`. The cap at an entry = `max(floor,
  round(k·median(trailing move durations confirmed strictly before the entry)))`; fewer than `min_moves`
  prior durations ⇒ `warmup=True` (no cap).
- **Why this instantiation (the one genuine methodology decision — flagged for Stage-4 governance):** the
  cap basis is the **cell's MA-segment move-duration tempo**, applied **uniformly to all four substrates**
  by entry epoch. This (a) reuses only validated machinery (`adaptive_time_caps_by_epoch` is the exact
  EXP-068/070 cap, already cell-level MA-tempo evaluated at entry epochs — for harami this *is* its
  existing cap, unchanged); (b) gives a single, substrate-neutral "how long do moves last here" lookforward
  bound, so cross-substrate comparison is fair and the `SUB-RANDOM` null **inherits the identical cap-by-time
  function** by construction (its caps are draws of the same step function at random entry epochs — the
  scope's "SUB-RANDOM inherits its matched real substrate's per-cell cap distribution"); (c) avoids
  inventing an unvalidated AVWAP-specific move-duration structure (AVWAP's `EntrySet` exposes only
  anchor/armed/trigger epochs, no confirmed-move duration series).
- **Simpler / alternative considered:** a per-substrate move structure (harami=MA segments; AVWAP=an
  AVWAP-specific lifetime structure; SUB-RANDOM=resample caps from the matched real substrate). Rejected —
  AVWAP has no validated duration-series analog, so this introduces an unvalidated free choice and makes
  the random null's cap basis differ from the real substrates' (unfair attribution). The uniform cell-level
  MA-tempo is strictly more defensible and is what the harami cap already is.
- **Assumptions:** the MA-segment tempo is a reasonable lookforward bound for any entry in that
  instrument×domain. Reasonable for trend-continuation substrates; for AVWAP/RANDOM it is a regime-tempo
  bound, not a claim about their own structure — appropriate for a *capture-window* cap.
- **Warmup handling:** warmup events are **disclosed and excluded** from all quantiles/shape stats (never
  silently capped); per-cell warmup count and fraction reported.
- **Output:** per-event integer cap `c` (bars) and `warmup` flag, per substrate-cell.

### Step 3 — Direction assignment (per substrate; for signed MFE/MAE)

- **Method:** position direction `d ∈ {+1,-1}` per event:
  - **`SUB-AVWAP`:** the event `direction` column from `generate_avwap_events` (the actual bounce/regime
    position direction).
  - **harami substrates:** the in-progress MA-segment direction at entry, `seg["direction"]` at the entry's
    in-progress move `k` (the trend-continuation position direction; `state.k` from
    `live_in_progress_state`, as the harness already computes).
  - **`SUB-RANDOM`:** the prevailing MA-segment direction at the random entry bar (same `seg["direction"]`
    mapping) — the regime-direction a trend-continuation strategy would take; a random entry bar with no
    active/valid segment (warmup) is excluded as warmup.
- **Why:** signed MFE/MAE/outcome require the position direction each substrate would actually hold; using
  the regime direction for the random null keeps it a "random-timing, same-regime-direction" matched
  control (only timing is randomized), which is the cleanest attribution null.
- **Assumptions:** none distributional.
- **Output:** per-event `d`.

### Step 4 — Realized path geometry on real OHLC (the per-event measurement)

- **Method (new module `xen.capgeo_geometry`, pure/vectorized-where-causal):** for each non-warmup,
  ATR-defined event with entry index `i`, direction `d`, cap `c`, window `W = [i+1, min(i+c,
  train_edge_idx)]` on **real** domain OHLC (`train_edge_idx = train domain-bar count − 1`; forward
  resolution clips at the TRAIN edge — never reads beyond):
  - `fav_t  = (H_t − C_i) if d=+1 else (C_i − L_t)`  (favourable excursion, ≥ can be negative early)
  - `adv_t  = (C_i − L_t) if d=+1 else (H_t − C_i)`  (adverse excursion magnitude)
  - **`MFE` (ATR)** `= max_{t∈W} fav_t / ATR_i`; **`MAE` (ATR)** `= max_{t∈W} adv_t / ATR_i`
  - **`TTP` (bars)** `= (argmax_{t∈W} fav_t) − i`, first bar attaining the MFE peak (ties → earliest)
  - **realized outcome (ATR)** `= d·(C_{last(W)} − C_i) / ATR_i` (signed close-to-close at the cap/TRAIN-edge
    bar) — the readout `tailmass`, `q05`, and `ASS` summarize.
  - An event whose window is empty after clipping (entry at/after `train_edge_idx`) is excluded with a
    `clipped_empty` disclosure count.
- **Why:** standard MFE/MAE/TTP path geometry, identical in spirit to `xen.capture_barriers` /EXP-055/068
  but with **no target/stop** (no exit is applied — EXP-082/083). A dedicated path-geometry pass is
  clearer and lighter than abusing the first-touch resolver (`resolve_path_ordered`) with null targets.
- **Vectorization discipline:** the per-event window scan is bounded by the adaptive cap; vectorize the
  intra-window max/argmax with NumPy slices but keep the outer event loop explicit (causal, bounded). No
  cross-event look-ahead. `tqdm` over the 184-substrate-cell outer loop.
- **Real-price discipline:** every quantity uses real domain OHLC and real-bar ATR; HA prices are used
  only for harami *entry detection* (Step 1), never here.
- **Output:** per-event `(MFE, MAE, TTP, outcome)` arrays (ATR units), per substrate-cell.

### Step 5 — D3-input distribution statistics (per substrate-cell)

- **Method:** over each cell's non-warmup, ATR-defined, non-clipped events:
  `MFE_med = Q50(MFE)`, `MFE_q40 = Q40(MFE)`; `TTP_med = Q50(TTP)`, `TTP_q75 = Q75(TTP)`;
  `MAE_q90 = Q90(MAE)`. Quantiles via `numpy.quantile(..., method="linear")` (the project default; matches
  `xen.expectancy._weighted_quantile` linear convention).
- **Why:** D3 specifies these exact quantiles; quantiles are distribution-free and robust to the
  asymmetric/heavy-tailed geometry expected here. **Simpler alternative (means):** rejected — the family's
  binding lesson is that means are corrupted by the minority-catastrophe tail (CF-HA-HARAMI-001); D3 is
  deliberately quantile-based.
- **Floor:** a cell with < 30 usable events → `UNDERPOWERED_DISCLOSED`; statistics still reported
  (flagged), but the cell forms **no** EXP-082 derived candidate (D9). Never dropped.
- **Output:** the per-cell D3-input row.

### Step 6 — Shape diagnostics: `m_anti`, `tailmass`, `q05` (per substrate-cell)

- **Method (Stat test 1 = Hartigan dip; reuse `xen.ass`):**
  - **`m_anti` (antimode of the MAE distribution):** run `diptest.diptest(MAE)` → `(dip_stat, dip_p)`
    (analytic Hartigan p-value, deterministic; the same call `xen.ass.shape_diagnostic` uses). **If
    `dip_p < 0.05` (bimodal):** locate the antimode as the **minimum-density grid point between the two
    highest KDE modes** using the validated adaptive KDE (`xen.ass.make_grid` + `xen.ass.adaptive_kde_pdf`
    on the MAE sample) — a robust, non-parametric 2-component split (no Gaussian-mixture assumption).
    **Else `m_anti = NaN`** (unimodal). Report `dip_stat`, `dip_p`, and `m_anti` per cell.
  - **`tailmass`:** catastrophe boundary `b = median(outcome) − K_tail · MAD(outcome)` (`K_tail = 3.0`;
    MAD = median absolute deviation). `tailmass = #{outcome < b} / n_events`. `MAD = 0` (degenerate) →
    `tailmass` reported `0.0` with a `mad_zero` disclosure (boundary collapses to the median; matches the
    `xen.ass` `mad_zero` convention).
  - **`q05`:** `Q05(outcome)`.
- **Why:** `m_anti` is the D3 adverse-leg input (dominant-vs-catastrophic-minority boundary); the dip test
  is the validated bimodality detector (EXP-074/078); the KDE antimode gives its *location* where bimodal.
  `tailmass`/`q05` are the **minority-mass / left-tail read `ASS` structurally lacks** (D9; design §8.3) —
  the descriptive companion that makes the subtle median-positive minority-catastrophe shape visible to the
  human and to EXP-083's separability argument.
- **`m_anti` power disclosure (D9):** the dip is power-limited at realistic cell sizes (finite-rate
  ~0.02/0.45/0.95 at n=30/250/500); most cells will return `NaN` and EXP-082's adverse leg will use the
  `MAE_q90` fallback. This is expected and disclosed, not a defect.
- **Output:** per-cell `(dip_stat, dip_p, m_anti, tailmass, q05, mad_zero)`.

### Step 7 — `ASS` discovery disclosure (non-binding; Stat test 2 = ASS bootstrap)

- **Method (reuse `xen.ass` unchanged):** per substrate-cell, on the per-event realized-outcome sample,
  compute the `ASS` readout — expectancy (`score`/`kde_expectancy`), median (`weighted_median`), and the
  tail diagnostic (`prob_gt` / `shape_diagnostic`) — with `moving_block_bootstrap_cis` (block length
  `default_block_length(n)`, `N_BOOT = 10_000`, fixed seed) for the expectancy/median/tail CIs.
- **D6 Guard (i) (binding on the disclosure):** at **effective-n ≤ 60** on bimodal/asymmetric strata
  (`shape_diagnostic.flag = True`), **defer the expectancy read to the median** — report expectancy as
  `disclosed_low_n`, median as the primary `ASS` central read. (`WF-EXPANDING` is not run here; "effective-n"
  = the cell's usable event count, which is ≥ the per-fold count, so this is conservative.)
- **D7 bracket:** all member cells are `IN_BRACKET [15,8000]` (EXP-080); any cell that nonetheless fell
  outside would have its `ASS` disclosure excluded with a note (not expected).
- **Why:** the design mandates `ASS` expectancy+median+tail be reported alongside every read **as
  discovery disclosure only** — no binding decision rests on it (G-017 `DISCOVERY_ONLY`). Reusing the
  frozen `xen.ass` keeps it the exact Phase-017-validated estimator.
- **Non-binding status (explicit):** nothing in EXP-081 (or its downstream use) gates on the `ASS` numbers;
  they are interpretation/disclosure inputs to the human and to the EXP-083 separability argument.
- **Output:** per-cell `ASS` expectancy/median/tail + CIs + the guard-(i) flag.

### Step 8 — Determinism & integrity guards

- **Method:** a second full pass over every substrate-cell; assert the per-cell statistics table is
  **frame-identical** (exact) to the first pass (all seeds fixed: `SEED_RANDOM`, the ASS bootstrap seed).
  Assert: holdout never sliced (only metadata read); no domain-bar label crosses the analysis-slice
  boundary (fence, inherited from `build_domain_bars`); every path window's last index ≤ `train_edge_idx`;
  the Step-1 EXP-080 reconciliation `recon_ok` holds for all cells.
- **Why:** determinism + reconciliation + holdout-fence are the binding HALT conditions (scope).
- **Output:** `determinism_ok`, `recon_all_ok`, `holdout_untouched` flags in `run_metadata.json`.

---

## Visualisations (≤ 5)

1. **Per-substrate `MFE_med` heatmap** (4 panels, 16×3 instrument×domain small-multiple) — favourable
   capture geometry across the member set; exposes where the move is large vs the cost scale.
2. **Capture-time heatmap** (`TTP_med` with `TTP_q75` annotation, by substrate) — *when* the peak lands;
   `TTP_q75` is EXP-082's `H_cap`, so its spread across cells is the key derivation input.
3. **MAE distribution panels for representative cells** (one dense cell per domain per real substrate) with
   the KDE, the catastrophe boundary `median−3·MAD`, and the `m_anti` antimode overlaid where bimodal —
   shows the dominant-vs-minority split the adverse leg targets.
4. **`tailmass` heatmap by substrate incl. `SUB-RANDOM`** — the minority-mass read across the member set;
   real-substrate vs random-null tail mass side by side flags catastrophe-minority concentration.
5. **Per-substrate realized-outcome distribution small-multiples** flagging cells with `dip_p < 0.05`
   (bimodal) — makes the median-positive/minority-catastrophe shape visible per cell.

All plots are built from the single analysis pass's bounded per-cell summaries (and bounded per-event
arrays for the four representative-cell MAE panels) — **no data reloads or re-generation for plotting**.

## Interpretation Guide (pre-defined, before results exist)

This is a characterization; the "verdict" is about completeness and integrity, not an edge.

- **CHARACTERISATION_DELIVERED** iff the per-cell D3-input + shape + `ASS`-disclosure tables are produced
  for all 184 member substrate-cells, determinism passes, EXP-080 reconciliation holds, and the holdout is
  untouched — *whatever* the shapes look like.
- **Cell-level `UNDERPOWERED_DISCLOSED`** iff a cell has < 30 usable events — recorded, statistics still
  shown, forms no EXP-082 derived candidate. (Some 4h cells likely.)
- **HALT (process-level, route back to developer)** iff *any*: second-pass statistics differ from the
  first (non-determinism); a real-price/look-ahead/holdout-fence violation; or an EXP-080 entry-count
  reconciliation break. These indicate an implementation bug, not a data shape.
- **Descriptive shape disclosures (reported, not adjudicated):**
  - A cell with `dip_p < 0.05` and a left-`m_anti` (catastrophe minority below the bulk) **and**
    `tailmass > 0` exhibits the CF-HA-HARAMI-001-style minority-catastrophe shape — flag it for EXP-083's
    separability attention. This is a *disclosure*, carries no pass/fail weight.
  - `TTP_q75` clustering tight vs wide across a substrate's cells indicates whether one `H_cap` generalizes
    or must be per-cell — informs EXP-082 only descriptively.
  - `SUB-RANDOM` `MFE_med`/`tailmass` vs the real substrates is the **attribution baseline** the EXP-083
    matched-null will formalize; here it is descriptive context only (no CI comparison binds).
- **No goalpost movement:** the D3 statistic definitions, `K_tail=3.0`, the ≥30 floor, and the cap basis
  are frozen by this plan; EXP-082 freezes the *rule*, not the story EXP-081's numbers tell.

## Implementation Safety Constraints (for `experiment-developer`)

- **Imports → path setup → constants → I/O helpers → pure computation → plotting → orchestration →
  `main()`** (VAL-001-style sectioning). No directory creation / file writes / data loads / plotting at
  import time.
- **Temporal ordering:** all ordering/alignment by `CloseTime` (real time) and epoch, never bar index for
  cross-view alignment; assert `CloseTime` sorted after slicing.
- **Holdout discipline:** read only the first `train_cutoff` 1-minute rows (`train_cutoff =
  int(int(total_rows*0.7)*0.7)`); locate the split via Parquet metadata only; never materialize a row at
  or beyond `analysis_rows`; forward path windows must clip at `train_edge_idx`.
- **Real-price discipline:** every MFE/MAE/TTP/outcome/ATR on real domain OHLC; HA only for harami entry
  detection.
- **Reuse, don't edit:** `xen.domain_bars`, `xen.capgeo_substrates`, `xen.heiken_ashi_generator`,
  `xen.expectancy` (`adaptive_time_caps_by_epoch`), `xen.zigzag` (`wilder_atr`), `xen.ass` (KDE/dip/score/
  bootstrap) — all unchanged. New code only in `xen.capgeo_geometry` (path geometry) and a thin
  shape-diagnostic helper (`m_anti` antimode locator + `tailmass`/`q05`), which itself reuses
  `xen.ass.make_grid`/`adaptive_kde_pdf`/`shape_diagnostic` + `diptest`.
- **Denominators / zero-baseline:** quantile/shape denominators = per-cell usable-event count (disclosed);
  `tailmass` zero-tail → `0.0` with denominator (never `0/0`); `m_anti` unimodal → `NaN` (not 0);
  warmup/ATR-undefined/clipped-empty events counted and excluded, never folded into a quantile; no metric
  expressed as a percentage over a zero baseline.
- **Bounded iteration / progress:** outer loop over 184 substrate-cells with `tqdm`; per-event window scans
  bounded by the adaptive cap; per-cell memory bounded (do not retain all domain frames simultaneously);
  `N_BOOT = 10_000` for the ASS CIs; fixed seeds recorded in `run_metadata.json`.
- **Vectorization discipline:** vectorize intra-window max/argmax with NumPy; keep the outer event loop and
  any causal/sequential step explicit — no transformation that changes sample membership, ordering,
  denominators, or causal semantics.
- **Outputs:** `results/substrate_cell_summary.parquet` (per-cell D3 + shape + ASS rows),
  `results/per_event_geometry.parquet` (bounded per-event arrays for reproducibility/representative plots),
  `results/ass_discovery.json`, `results/run_metadata.json` (seeds, hashes, frozen-constant versions,
  EXP-080 reconciliation, determinism/holdout flags), and the ≤5 plots under `plots/`.

## Complexity Check

- **Statistical tests: 2 / 2** — Hartigan dip test (`m_anti`/bimodality); `ASS` moving-block bootstrap
  (discovery disclosure). Quantiles, `tailmass`, `q05` are descriptive.
- **Visualisations: 5 / 5.**
- **New modules: 2 / 2** — `xen.capgeo_geometry` (adaptive-cap path geometry: MFE/MAE/TTP/outcome) and a
  thin shape-diagnostic helper (antimode locator + tail-mass), the latter built on `xen.ass`. All other
  logic reuses existing frozen modules.
