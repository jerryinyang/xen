# Analysis Plan: Experiment EXP-051

**Phase 014-A · HYP-004 · `CF-HA-HARAMI-001/STRONG-STAT`, `/STRONG-HA` ·
characterisation (0 candidate slots, 0 TEST reads) · gross · TRAIN-only · 99 cells.**

This plan operationalises `scope.md` without adding scope. Every threshold (P7,
P8, P10, P11, warmup floor 5, power floor 30) is D0-/operator-frozen and is treated
here as a fixed constant, never tuned. The binding P10 adjudication is a
**deterministic point criterion**; the only inferential method is a single,
explicitly **non-binding** bootstrap CI used as disclosed robustness colour.

## Objective

For each EXP-048-READY cell (instrument × domain), measure — on the population of
confirmed ZigZag moves, real-price magnitudes — whether `/STRONG-STAT` (P7) and
`/STRONG-HA` (P8) each carve a **materially different** move sub-population by P10
(`ρ = median(mag|retained)/median(mag|all defined) ≥ 1.5` **and** retained
fraction `f ∈ [0.10, 0.50]`), and whether that holds with cross-cell consistency
composed by P11 (≥5 cells over ≥3 instruments). Deliver the per-cell map, the
disclosed alternative-form / sensitivity / overlap / censoring tables, and the
mechanical P10/P11 readout — whatever the material/not-material mix. The experiment
emits the readout; it does not self-adjudicate G1.

## Unit of analysis, magnitude, and the per-cell denominator

- **Unit:** one confirmed ZigZag move from `xen.zigzag.generate_zigzag(bars,
  atr_period=14, atr_mult=1.0)` on the cell's real domain OHLC (TRAIN-fenced).
  Moves are ordered by `ConfirmTime` (the causal clock); `EndTime` (pivot) and
  `ConfirmTime` are distinct and `ConfirmTime > EndTime` by construction.
- **Magnitude:** `mag_M = |EndPrice_M − StartPrice_M|`, real-price excursion
  (P7). A **degenerate** move (`EndPrice = StartPrice ⇒ mag = 0`) is excluded with
  record (`DEGENERATE`).
- **Defined-decision set (the P10 "unfiltered" denominator), per filter
  independently:** non-degenerate moves that additionally satisfy the filter's
  warmup requirement:
  - `/STRONG-STAT`: ≥ 5 confirmed moves strictly prior (by `ConfirmTime`).
    Earlier moves are `NO_DECISION_STAT`.
  - `/STRONG-HA`: the move's span `(StartTime, EndTime]` can in principle contain a
    qualifying run — i.e. `EndTime_M ≥` the `CloseTime` of the earliest HA bar that
    can *complete* a run (the **8th** HA bar, 0-based index `min_window + run_len - 1
    = 7`; the 6th bar is the first *qualifiable* bar and a run of 3 ends two bars
    later — see §3 and `xen.strong_move.ha_run_warmup_end_time`). Moves ending before
    that bar are `NO_DECISION_HA`. (In practice this excludes only the first few HA
    bars' worth of moves; reported, never silently treated as "not retained".)
- The two filters therefore have **slightly different denominators** in the same
  cell (`/STRONG-STAT` drops the first ~5 moves; `/STRONG-HA` drops only the earliest
  HA-warmup moves). Each filter's `n_defined` is reported separately. **No pooling
  across cells** for any binding number.

## Methodology

### Step 1 — `/STRONG-STAT` causal rolling-window move filter (binding: p75)

- **Method:** for each move `M` (ordered by `ConfirmTime`), form the window =
  magnitudes of the most recent `min(20, available)` moves with
  `ConfirmTime < ConfirmTime_M` (strictly prior). If `< 5` available → `NO_DECISION_STAT`.
  Else compute `thr_p75 = quantile(window_mags, 0.75)` and retain `M` iff
  `mag_M ≥ thr_p75` (inclusive `≥`; ties retained).
- **Disclosed alternative form (P7, parallel, never selected against results):**
  `thr_mad = median(window_mags) + 1.0 × MAD(window_mags)`, where
  `MAD = median(|window_mags − median(window_mags)|)` (**raw** MAD, no 1.4826
  consistency constant — this is a threshold, not a dispersion estimate). Retain iff
  `mag_M ≥ thr_mad`.
- **Determinism pin:** percentile uses `numpy.quantile(..., method="linear")`
  (type-7, NumPy default) on `float64`; this fixed interpolation is recorded in
  `run_metadata.json`. The window is a trailing slice of the magnitude array — a
  causal expression (move `M` never sees its own or any later magnitude in its
  threshold).
- **Why sufficient / simpler alternative:** P7 specifies exactly these two forms;
  the rolling percentile is the simplest causal "is this move large vs its recent
  peers" statistic. A global (non-rolling) percentile was rejected — it is not
  causal and ignores within-cell regime drift.
- **Assumptions:** none on distribution shape (rank/percentile based). Serial
  dependence of magnitudes is *expected* and is exactly why the window is causal
  and why Step 5's CI uses a block (not iid) bootstrap. Fits time-ordered data.
- **Output:** per move, `mag`, `decision_stat_p75 ∈ {retained, not, NO_DECISION}`,
  `decision_stat_mad`.

### Step 2 — `/STRONG-HA` impulse-bar qualifier (HA candles; detection only)

- **Method:** generate HA candles from the cell's real domain bars
  (`xen.heiken_ashi_generator.generate_heiken_ashi`, frozen). For each HA bar `b`:
  - `body_b = |HAClose_b − HAOpen_b|`; `dir_b = +1 if HAClose_b ≥ HAOpen_b else −1`.
  - trailing median body `med_b = median(bodies of the min(20, available) HA bars
    with CloseTime < CloseTime_b)`; if `< 5` prior bars → `b` cannot qualify
    (undefined median).
  - **qualify_b** iff `body_b ≥ med_b` **and** no opposing wick:
    bullish (`dir_b = +1`) ⇒ `HALow_b == HAOpen_b`; bearish (`dir_b = −1`) ⇒
    `HAHigh_b == HAOpen_b`. (Exact float equality is valid for HA candles:
    `HALow = min(Low, HAOpen, HAClose)` equals `HAOpen` precisely when there is no
    lower protrusion; likewise `HAHigh`. The developer asserts this exactness in
    the invariant battery rather than applying a tolerance.)
- **HA prices are used for detection only.** No HA price enters `mag`, `ρ`, `f`, or
  any reported metric.
- **Output:** per HA bar, `dir`, `body`, `med`, `qualify` (and a `median_defined`
  flag for the warmup disclosure).

### Step 3 — `/STRONG-HA` run detection and run→move mapping

- **Qualifying run:** the maximal/any window of exactly `X = 3` **consecutive** HA
  bars (adjacent in CloseTime order) that are **all the same direction** and **all
  `qualify = True`**. Detect by a vectorised 3-bar rolling-AND over
  `qualify ∧ (dir == dir.shift(1) == dir.shift(2))` (or an explicit short scan).
  Each detected run carries its direction `d_run` and its three bars' `CloseTime`s.
  The "first qualifiable HA bar" is the 6th HA bar (≥5 prior for a defined median);
  the earliest possible run completes at the 8th HA bar — this fixes the
  `NO_DECISION_HA` boundary in §"denominator".
- **PRIMARY mapping (binding):** move `M` (direction `d_M`) is **retained** iff
  ∃ a qualifying run with `d_run == d_M` and **all three** run-bar `CloseTime`s lie
  in `(StartTime_M, EndTime_M]`.
- **SENSITIVITY mapping (disclosed, non-binding):** identical but **drop** the
  `d_run == d_M` requirement (any-direction run inside the span retains `M`). By
  construction primary-retained ⊆ sensitivity-retained (invariant-checked).
- **Implementation note:** map runs to moves by an interval test of each run's bar
  CloseTimes against the precomputed `(StartTime, EndTime]` move intervals — safe to
  vectorise because the moves are an **already-confirmed completed segmentation**,
  not a sequential causal scan. Requiring *all three* run bars inside the span (not
  merely overlap) keeps "the impulse occurred within this move" unambiguous.
- **Output:** per move, `decision_ha_primary`, `decision_ha_sensitivity ∈
  {retained, not, NO_DECISION_HA}`.

### Step 4 — Per-cell P10 statistics (deterministic point criterion = binding)

For each cell and each filter form (`/STRONG-STAT` p75 **[binding]**, `/STRONG-STAT`
median+1×MAD, `/STRONG-HA` primary **[binding]**, `/STRONG-HA` sensitivity):

- `n_defined` = # defined-decision moves (filter-specific denominator).
- `n_retained` = # retained ⊆ defined.
- `f = n_retained / n_defined` (retained fraction).
- `med_all = median(mag | defined)`, `med_ret = median(mag | retained)`,
  `ρ = med_ret / med_all`.
- **Reportable** iff `n_defined ≥ 30` (power floor); else `NOT_REPORTABLE_BY_POWER`.
- **Materially different (P10)** iff `reportable ∧ (ρ ≥ 1.5) ∧ (0.10 ≤ f ≤ 0.50)`,
  both conditions required.
- Also report `med_all`, `IQR_all`, `med_ret`, `IQR_ret` (distribution summary).

**Why no inferential test for the binding decision:** P10 is, by D0, a fixed
comparison of two medians and a fraction — a deterministic readout, not a
significance claim. Adding a hypothesis test would change the predeclared decision
rule. The point criterion *is* the method.

### Step 5 — Bootstrap CI on `ρ` (the single statistical method; NON-BINDING)

- **Question answered:** how much sampling uncertainty surrounds the per-cell point
  `ρ`? (Disclosed colour only; **does not** enter the P10/P11 decision.)
- **Method:** **moving-block bootstrap** over the `ConfirmTime`-ordered sequence of
  the cell's defined-decision moves, resampling `(mag, retained_flag)` tuples in
  contiguous blocks to preserve local serial dependence (volatility/size
  clustering). Block length `L = max(1, round(n_defined ** (1/3)))` (standard MBB
  rate); draw ⌈`n_defined`/`L`⌉ blocks, truncate to `n_defined`, recompute
  `ρ* = median(mag*|retained*)/median(mag*|all*)`; if a resample has zero retained,
  `ρ*` is recorded as `NaN` and excluded from the percentile (disclosed count).
  `B = 10_000` resamples, **fixed seed** (recorded in `run_metadata.json`). CI =
  (2.5, 97.5) percentiles of the finite `ρ*`.
- **Why this and not iid bootstrap / a rank test:** moves are serially dependent, so
  an iid bootstrap understates uncertainty; the block bootstrap is the simplest
  resampling honest about dependence. A Mann-Whitney test on retained vs not would
  test a *different* (stochastic-dominance) hypothesis than P10's median-ratio and
  would tempt goalpost drift — rejected.
- **Assumptions:** approximate stationarity within the block scale only; reported as
  support, never as a gate. Computed for both binding forms; **not** computed for
  the disclosed alternative/sensitivity forms (keeps the single-test budget). Only
  for reportable cells.
- **Determinism:** fixed seed + fixed `B`, `L`, percentile method ⇒ bit-identical CI
  across the two passes.

### Step 6 — Harami↔retained-move overlap (DISCLOSED secondary, non-binding)

- Detect haramis (`xen.ha_harami.detect_ha_harami`, frozen) on the same HA candles;
  assign each to its containing confirmed move by pivot tiling via
  `xen.move_position.assign_to_moves(events, moves, event_time="HA0Time",
  event_price="RealClose@HA0Time", left_strict=True)` (the EXP-050 path).
  `RealClose@HA0Time` = the real domain `Close` at the harami's `HA0Time`.
- Per cell, per **binding** filter form: `overlap_A = (# retained moves containing
  ≥1 ASSIGNED harami) / n_retained`; `overlap_B = (# ASSIGNED haramis on a retained
  move) / (# ASSIGNED haramis)`. If `n_retained = 0` → `overlap_A = null`; if 0
  assigned haramis → `overlap_B = null` (never `0/0`).
- Disclosed only; informs 014-B combined-event registration. No binding claim.

### Step 7 — Determinism replay + invariant battery

- **Determinism:** run the entire per-cell pipeline a second time (re-aggregate,
  re-HA, re-detect runs/haramis, re-ZigZag, re-filter, re-map, re-assign, re-bootstrap
  with the same seed). Assert the full `per_cell_strong_move` frame is
  **frame-identical** (`pl.DataFrame.equals`, exact — all integer counts, float
  `mag`/`ρ`/`f`/CI bit-identical). Any mismatch on any cell ⇒ `CHARACTERISATION_REFUTED`.
- **Invariant battery (scope §Readiness):** record counts (must be 0 unless a
  disclosed exclusion): filter well-formedness (retained ⊆ defined; decisions
  exhaustive over the trichotomy); magnitude validity (`mag` finite, `> 0` on every
  defined move); `/STRONG-HA` self-consistency (each emitted run = 3 consecutive
  same-direction qualifying bars; primary-retained ⊆ sensitivity-retained);
  causality/TRAIN-fence (every `ConfirmTime`, HA `CloseTime`, harami `HA0Time`
  `≤ train_end_ts`). A battery item (1–4) breached on **≥ 3 instruments**, or any
  non-determinism, ⇒ `CHARACTERISATION_REFUTED`.

### Step 8 — P11 composition + cross-cell consistency readout

- **P11 (per filter, per form):** `n_material_cells` = # reportable cells with P10
  true; `n_material_instruments` = # distinct instruments among them; family claim
  "this filter carves a materially different move population" holds iff
  `n_material_cells ≥ 5 ∧ n_material_instruments ≥ 3`. Emitted for both binding forms
  and, **in parallel and disclosed**, for the median+1×MAD and any-direction forms.
- **Cross-cell consistency (descriptive, no test):** across reportable cells, per
  filter, report the distribution of `ρ` and `f` (median, IQR, min, max), the
  per-domain breakdown of materiality (does it concentrate in a domain?), and the
  materiality **agreement counts** between (a) p75 vs median+1×MAD and (b)
  primary vs sensitivity (# cells that flip). These describe robustness; they are
  not gates.

## Visualisations (4 / 4 — bounded inputs from the analysis pass, no reloads)

1. **`/STRONG-STAT` (p75) `ρ` heatmap** — 17 instruments × 6 domains, colour = `ρ`,
   the 1.5 threshold marked (diverging colormap centred at 1.5); NOT_REPORTABLE and
   COVERAGE_EXCLUDED cells greyed/annotated. *Answers c/d for STAT.*
2. **`/STRONG-HA` (primary) `ρ` heatmap** — same layout, same 1.5 marking.
   *Answers c/d for HA.*
3. **Retained-fraction `f` heatmap, small-multiple (STAT-p75 | HA-primary)** — the
   `[0.10, 0.50]` admissible band marked (e.g. annotate cells inside vs outside).
   *Answers b and P10 condition (b).*
4. **Materially-different composition map** — 17×6 categorical panel per binding
   filter (small-multiple): material / reportable-not-material / NOT_REPORTABLE /
   COVERAGE_EXCLUDED; title carries the P11 tallies. *Answers d / P11.*

All disclosed forms (median+1×MAD, any-direction sensitivity, overlap, magnitude
median/IQR, censoring, bootstrap CIs) go to CSV/JSON, not plots.

## Output tables

- `per_cell_strong_move.parquet` — one row per (instrument, domain, filter_form):
  `n_moves_total, n_degenerate, n_no_decision, n_defined, n_retained, f, med_all,
  iqr_all, med_ret, iqr_ret, rho, ci_low, ci_high, reportable, material, status`.
- `p10_map.csv` — binding forms only (STAT-p75, HA-primary): `instrument, domain,
  rho, f, med_all, med_ret, n_defined, n_retained, reportable, material, ci_low,
  ci_high`.
- `strong_stat_alt_disclosure.csv` — STAT median+1×MAD: `rho, f, n_defined,
  n_retained, material`.
- `strong_ha_sensitivity.csv` — HA any-direction: `rho, f, n_defined, n_retained,
  material`.
- `harami_overlap.csv` — per binding filter: `n_retained, overlap_A, n_assigned_harami,
  overlap_B`.
- `excluded_fractions.csv` — `n_moves_total, n_degenerate, degenerate_frac,
  n_no_decision_stat, n_no_decision_ha, ha_warmup_bars`.
- `composition_readout.json` — per filter/form: `n_reportable, n_material,
  n_material_instruments, p11_pass`; consistency block (ρ/f distribution summaries,
  per-domain materiality, p75↔MAD and primary↔sensitivity agreement counts).
- `run_metadata.json` — instruments, domains+coverage, atr params, X=3, window=20,
  warmup floor 5, power floor 30, p75 interpolation method, MAD form, bootstrap
  `B`/`L`-rule/seed, train_end_ts per instrument, EXP-048 readiness source, library
  versions, two-pass determinism result.

## Interpretation Guide (pre-defined, before results exist)

- **Experiment verdict is delivery, not materiality.** If Steps 1–8 produce the
  per-cell maps and readouts with determinism PASS and no battery breach on ≥3
  instruments ⇒ `STRONG_FILTER_CHARACTERISATION_DELIVERED`, regardless of how many
  cells are material.
- **If a binding filter meets P11** (≥5 cells, ≥3 instruments with `ρ ≥ 1.5 ∧ f ∈
  [0.10,0.50]`): the readout supports "this filter carves a materially larger,
  selective move population" — input to G1 / 014-B combined-event registration. Not
  a tradability claim (gross, no capture, no costs).
- **If a binding filter fails P11:** the filter does **not** carve a materially
  different population per the predeclared bar — a valid negative characterisation.
  Distinguish the two failure modes per cell and report which dominates: (i)
  `ρ < 1.5` (retained moves not materially larger) vs (ii) `f` out of `[0.10,0.50]`
  (degenerate selectivity — e.g. p75 mechanically yields `f ≈ 0.25` so failures
  there will usually be the `ρ` leg, whereas `/STRONG-HA` may fail on `f` if runs
  are rare/common). This decomposition is descriptive and pre-registered.
- **Bootstrap CI** is read only as "is the point `ρ` fragile?" colour; a CI that
  straddles 1.5 does **not** overturn a point-`ρ ≥ 1.5` material flag (point
  criterion binding by D0).
- **Disclosed forms** (MAD, any-direction, overlap) are read for robustness and for
  014-B input; they never change the binding verdict and are reported even when they
  disagree with the binding form (disagreement is itself informative).
- **`CHARACTERISATION_REFUTED`** only on non-determinism or a construction-invariant
  breach on ≥3 instruments — never because filters are "not material."
- **No goalpost movement:** thresholds 1.5 / [0.10,0.50] / 30 / 5 / 20 / X=3 are
  fixed; no per-cell or post-hoc retuning.

## Implementation safety constraints (for `experiment-developer`)

- **Temporal order:** sort the 1-minute TRAIN prefix by `CloseTime` before
  aggregation; never reorder ZigZag/HA generator input; order moves by `ConfirmTime`
  for the rolling window and the block bootstrap; align all views by `CloseTime`,
  never bar index.
- **Holdout/TRAIN fence:** F01 prefix only — `train_rows = int(int(total*0.7)*0.7)`
  file-order 1-minute rows; never sort/collect the full file; never read TEST or the
  final-30% holdout (Parquet metadata + TRAIN prefix only). Assert every emitted
  timestamp `≤ train_end_ts`.
- **Denominators:** each filter's denominator is its **own** defined-decision set;
  degenerate and `NO_DECISION` moves excluded from numerator and denominator and
  counted separately. Never silently default a `NO_DECISION` to "not retained".
- **Zero-baseline / NaN:** `n_retained = 0 ⇒ ρ = null`, `f = 0` (material = False),
  never `0/0`/inf; `n_defined < 30 ⇒ NOT_REPORTABLE_BY_POWER`; bootstrap resamples
  with zero retained ⇒ `ρ* = NaN` dropped from the CI with a disclosed count;
  overlap denominators guarded (null when zero).
- **Vectorisation that is safe:** the `/STRONG-STAT` trailing window, the
  `/STRONG-HA` qualify predicate, the 3-bar run scan, and the run→move / harami→move
  interval mapping are all causal or operate on a completed segmentation — safe to
  vectorise (Polars/NumPy). The upstream ZigZag state machine stays the frozen
  sequential generator (do **not** vectorise it). Percentile/MAD/median use the
  pinned `numpy` methods for determinism.
- **Bounded iteration / progress:** `tqdm` over the (instrument × domain) outer loop
  (≤ 99 cells × 2 passes); `B = 10_000` bootstrap resamples per reportable
  cell-form (fixed); per-cell bounded memory — do not retain all domain frames or
  all bootstrap arrays; helpers return data, no helper-level prints.
- **Module budget:** one new `xen/strong_move.py` (STAT filter both forms; HA
  qualify/run/map both mappings), reusing `xen.zigzag`, `xen.heiken_ashi_generator`,
  `xen.ha_harami`, `xen.bar_aggregator`, `xen.move_position` unchanged. Output dirs
  created only in orchestration, never at import.

## Complexity Check

- **Statistical tests: 1 / 1** — moving-block bootstrap CI on `ρ` (disclosed,
  non-binding; binding P10 is a deterministic point criterion).
- **Visualisations: 4 / 4** — STAT-p75 `ρ` heatmap; HA-primary `ρ` heatmap;
  `f` heatmap (small-multiple); materiality composition map.
- **New modules: 1 / 1** — `python/src/xen/strong_move.py`.
