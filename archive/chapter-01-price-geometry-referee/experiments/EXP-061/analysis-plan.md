# Analysis Plan: Experiment EXP-061

**MA(20,50)-Substrate Capture Readiness & Benchmark-Geometry Conditioned Efficacy (Dual Conditioning Object: Hybrid **and** Native)**
Phase 015 lead **L1** · `CF-HA-HARAMI-001/HYP-014` · forks the prior EXP-061 / EXP-060B per-cell pipeline.

> **Re-run under `D0-amendment-001-dual-parallel-substrate.md` (2026-06-17).** The prior plan treated a
> single MA arm (`M0`) as the *hybrid* object; in fact `M0` conditions on MA-segment `/STRONG-STAT` and
> is the **native** object. This plan emits **both** objects **individually** — never pooled — and adds
> the genuinely-new hybrid arm (`H0`) and its null (`RH0`).

> **Mandatory-reading precondition honoured.** `014-A-conditioning-gap-and-validation-lessons.md`
> was read in full (recorded in `scope.md`); this plan keeps the conditioning / harami-anchor /
> descriptive-position / median-endpoint rules. The matched-random controls are deliberate **nulls**,
> not signal claims; every outcome metric is on real prices; no position-in-move metric is used.

## Objective

Decide, on the 99-cell TRAIN grid and **separately for each conditioning object**, whether the
EXP-060B MA-substrate signal edge **generalises to the benchmark 3-barrier geometry** (favourable =
`0.50·M_sofar`, adverse 1:1, MA-defined adaptive cap), or whether it is specific to the V2A ×
`/ADV-NONE` champion — and whether generalisation depends on **where the strong-move filter is
computed** (ZigZag move = hybrid, vs MA segment = native). The two objects are reported **individually**
(no pooling); each yields its own EVIDENCE_* classification, and the phase outcome at G-015 is the
stronger object's.

The two binding discriminators are each object's benchmark MA signal arm against its **own-object**
matched-random-on-MA null:

- **Hybrid:** `H0` (`BENCH-MA-hybrid`) vs `RH0` (`BENCH-MA-hybrid-random`).
- **Native:** `M0` (`BENCH-MA-native`) vs `RM0` (`BENCH-MA-native-random`).

For **each** object independently: the signal arm is **median-viable** per cell (one-sided 95%
regime-clustered moving-block-bootstrap CI_low > 0, ≥ 30 qualifying events) **AND beats its own null**
(`signal − null` independent-contrast median CI_low > 0) **AND clears P11** (≥ 5 viable, null-beating
cells over ≥ 3 instruments) **with the P6 non-4h rule** (≥ 3 qualifying cells outside the 4h domain).

Binding endpoint = **median** per-event position-weighted gross ATR-normalised return (P3/P14). The
**mean** (raw + 10% trimmed + worst-5% tail-share, each CI'd) is the **P4 diagnostic co-primary** —
disclosed per arm, never a viability gate (the mean-recovery investigation is the L3 read, EXP-063).
Disclosed substrate contrast: `Z0 − RZ0` on ZigZag (expected: MA objects beat their nulls, `Z0 ⊁ RZ0`).

This is also the MA-substrate **readiness/reconciliation** precondition for the whole phase, under the
**corrected P12 roles**: the native arm `M0` and the ZigZag arm `Z0` must **reconcile to EXP-060B's
`BENCH-MA` (M0) / `BENCH-ZZ` (Z0)** per-cell median + qualifying count to `1e-9`; the hybrid arm `H0`
is a **new object with no outcome anchor** — its ZigZag-`/STRONG-STAT` conditioning mask must
reconcile **exactly** to EXP-053's retained set (by count, per cell), and it relies on determinism +
causality + invariants. A reconciliation/causality/determinism/invariant failure is a
**SUBSTRATE/METHOD_DEFECT** fixed before any efficacy read is interpreted.

## Methodology

The methods are a **parameterised re-instrumentation** of the existing per-cell pipeline (which already
computes `M0`/`RM0`/`Z0`/`RZ0`), not new algorithms. The one new computation is the **hybrid signal
arm `H0`** — the *ZigZag* `/STRONG-STAT` conditioning mask resolved through the *MA-segment* benchmark
geometry — and its matched-random null **`RH0`** (the existing matched-random-on-MA selector matched to
`H0`'s count, on independent dedicated RNG streams). Identical statistical machinery is applied to all
6 arms.

### Step 1 — Per-cell median expectancy + bootstrap CI (binding viability, per arm)

- **Method**: per-cell **median** of the per-event position-weighted gross ATR-normalised return, with
  a **regime-clustered moving-block bootstrap** CI (`b = round(m^(1/3))`, `N_BOOT = 10_000`, one-sided
  95% lower bound + two-sided bounds), via the frozen `xen.expectancy` `bootstrap_median_distribution`
  + `median_ci`. **Fixed per-cell seed** (`(BASE_SEED, cell_index, purpose)`, P3).
- **Why this method**: the per-event return distribution is fat-tailed and serially dependent within a
  regime; the median is robust to the left tail and is the binding programme endpoint (P14). The
  moving-block bootstrap respects within-regime serial dependence without a distributional assumption.
- **Simpler alternative considered**: i.i.d. percentile bootstrap or a sign test on the median.
  Rejected — i.i.d. resampling understates the CI under serial dependence; the sign test discards
  magnitude. The block bootstrap is the inherited, programme-frozen choice (EXP-049/053–060B).
- **Assumptions**: within-block exchangeability of regime-clustered events; non-parametric. Fits
  time-ordered financial data far better than any normal-theory CI.
- **Expected output**: per cell × arm — `object` tag (`hybrid`/`native`/`zigzag`), `role`
  (`signal`/`null`), `median`, `ci_low_1s`, `ci_lo_2s`, `ci_hi_2s`, `m` (qualifying count),
  `median_viable` flag. Arms: **H0, RH0, M0, RM0** (binding, two objects) + **Z0, RZ0** (disclosed).

### Step 2 — Per-cell mean + 10% trimmed mean + worst-5% tail-share (P4 diagnostic, disclosed, per arm)

- **Method**: the **same** moving-block bootstrap (byte-identical block construction; dedicated RNG
  streams so the median path is untouched) applied to (a) the **raw mean**, (b) the **10% symmetric
  trimmed mean**, and (c) the **worst-5% tail-share** = fraction of total negative return contributed by
  the worst 5% of events (descriptive scalar, finite). (a)/(b) each get a bootstrap CI.
- **Why this method**: it previews — at the **benchmark 1:1** geometry — whether any mean negativity is
  outlier-driven (trimmed mean crosses positive; thin tail-share) or structural (trimmed mean also
  negative), feeding the L3 recovery read, **separately for each object** (the hybrid and native
  populations may skew differently).
- **Simpler alternative considered**: raw mean only. Rejected — cannot distinguish removable-tail from
  structural negativity, the entire Phase 015 mean-diagnostic mandate (D0 P4).
- **Assumptions**: as Step 1; the mean is tail-sensitive so its CI is wider — that width is the
  measurement, not a defect.
- **Expected output**: per cell × arm (signal arms `H0`/`M0`/`Z0` primarily) — `mean`,
  `mean_ci_low_1s/lo_2s/hi_2s`, `trimmed_mean`, `trim_ci_low_1s/lo_2s/hi_2s`, `tail_share_worst5`.
  **Never** sets a viability flag (P4 closure-on-mean rule).

### Step 3 — Independent signal-vs-null contrasts, **per object** (binding) + ZigZag (disclosed)

- **Method**: the **independence-assuming** `xen.expectancy.contrast_ci` on the stored bootstrap
  distributions of the paired arms — median (binding) and mean (disclosed) — for **`H0 − RH0`**
  (hybrid, binding), **`M0 − RM0`** (native, binding), and **`Z0 − RZ0`** (ZigZag, disclosed). Each
  signal arm (indexed over haramis) and its null (indexed over disjoint random in-regime draws) are
  **independent samples** with no common per-event subset to pair — exactly as EXP-060/060B treat
  champion-vs-matched-random. The contrast is deterministic given the stored distributions (no fresh
  RNG). Per object: `beats_null` = (`signal − null` median CI_low_1s > 0).
- **Why this method**: signal attribution requires beating the **same-object** own-substrate random
  control, not merely clearing zero — the test that disentangled signal from substrate/drift in
  EXP-060B. **The hybrid and native contrasts are computed and reported separately; they are never
  pooled or differenced against each other** (cross-object comparison, if shown, is descriptive only).
- **Simpler alternative considered**: a paired Wilcoxon on matched events. Rejected — matched-random
  draws are **not paired** to specific haramis (disjoint event sets, matched only on
  count/regime/direction), so an independence-assuming contrast on the bootstrap distributions is the
  correct, inherited construction.
- **Assumptions**: each signal/null pair's bootstrap distributions are independent (true by
  construction — disjoint event pools). `NaN` bounds when either arm is power-limited (handled, never
  defaulted to a number).
- **Expected output**: per cell — `h0_rh0_median_low_1s/hi_2s`, `h0_rh0_mean_low_1s`,
  `m0_rm0_median_low_1s/hi_2s`, `m0_rm0_mean_low_1s`, `z0_rz0_median_low_1s`; the per-object
  `hybrid_beats_null` / `native_beats_null` flags; and the per-object composite generalisation flags
  `hybrid_generalises` (`H0 median_viable ∧ hybrid_beats_null`) and `native_generalises`
  (`M0 median_viable ∧ native_beats_null`).

### Composition (mechanical, predeclared, **per object**)

- Per-cell first; then **P11** = ≥ 5 cells over ≥ 3 instruments on a per-cell boolean flag, **with the
  P6 non-4h rule**: ≥ 3 of the qualifying cells **outside** the 4h domain. **Computed independently for
  each object** on its headline flag (`hybrid_generalises`, `native_generalises`). Secondary per-object
  P11 tallies for `*_median_viable`, `*_beats_null`, `*_mean_viable` (the last disclosed, never a gate).
- `fragile` flag (per object) when a tally composes at exactly the quorum boundary (5 cells / 3
  instruments / 3 non-4h cells), so the readout discloses thin composition.
- **No pooling across objects** at any composition step. Each object's EVIDENCE_* is independent.

## Visualisations (5 / 5 budget)

1. **Per-object signal-vs-null per-cell forest** (headline) — faceted hybrid (`H0 − RH0`) and native
   (`M0 − RM0`) per-cell median-contrast CI_low, sorted, coloured by `*_beats_null`. Answers: does each
   object's benchmark harami beat its own-substrate matched random, cell by cell?
2. **Hybrid-vs-native viability map** — heatmap across cells of each object's `*_median_viable`,
   `*_beats_null`, `*_generalises`; non-4h cells marked. Answers: where on the grid does each object
   generalise, and does the conditioning choice change the footprint?
3. **Substrate contrast by domain** — `H0 − RH0`, `M0 − RM0`, `Z0 − RZ0` grouped by domain
   (5m/15m/30m/1h/2h/4h). Answers: does the benchmark signal live on MA (both objects) but not ZigZag,
   and is that domain-dependent?
4. **Median vs mean (P4 skew preview)** — per-cell median vs raw mean vs 10% trimmed mean for `H0` and
   `M0`, worst-5% tail-share annotated. Answers: at the benchmark 1:1 geometry, is any negative mean
   removable-tail-driven or structural, per object?
5. **P11 (non-4h) composition per object** — per-object tally bars (`*_median_viable`, `*_beats_null`,
   `*_generalises`) with the quorum and non-4h thresholds marked. Answers: which object (if any) clears
   the breadth rule, and how thin is the margin?

Secondary tables (per_cell_expectancy, reconciliation, readiness, substrate_contrast, object_efficacy_map)
go to CSV/parquet, not plots.

## Interpretation Guide (predeclared; mirrors `scope.md` Success/Failure; **applied per object**)

Each object receives its own classification; the deliverable records both individually.

- **EVIDENCE_FOR (object's signal generalises to benchmark geometry on MA)** — the object's signal arm
  is median-viable **AND beats its own null** (`H0 − RH0` / `M0 − RM0` CI_low > 0) **AND its
  `*_generalises` flag clears P11 with the non-4h breadth rule**. Means: for that conditioning choice,
  the EXP-060B MA edge is **not** champion-geometry-specific.
- **EVIDENCE_AGAINST (object's edge is champion-geometry-specific)** — the object's arm **fails** P11
  viability **or** does **not** beat its own null in the quorum. **Family stays OPEN** — the surface
  runs regardless (P9 no-early-closure).
- **INCONCLUSIVE (power-limited)** — fewer than the P11 quorum of cells reach ≥ 30 qualifying events on
  the object's signal or null arm, no correctness failure. Disclosed; never the default.
- **SUBSTRATE/METHOD_DEFECT** — any reconciliation/determinism/causality/invariant failure. Mechanical
  invariant checks: (i) **`M0` reproduces EXP-060B `BENCH-MA` (M0)** per-cell median + count to
  `RECON_TOL = 1e-9`; (ii) **`Z0` reproduces EXP-053/060B `BENCH-ZZ` (Z0)** likewise; (iii) **`H0`'s
  ZigZag-`/STRONG-STAT` conditioning mask reconciles exactly to EXP-053** (same retained count per
  cell); `H0`'s qualifying count is disclosed (new, no anchor); (iv) the 1:1 stop, when it binds, closes
  at the same bar/level; (v) **matched-count holds per object** — `RH0.m_draw = H0.m`, `RM0.m_draw =
  M0.m`, `RZ0.m_draw = Z0.m`; (vi) every exit price is a real-bar P15 fill with `CloseTime ≤
  train_end_ts`. Fix before reporting any efficacy verdict.

Deliverable label: **MA_BENCHMARK_GENERALISATION_CHARACTERISED (dual-object)**. No phase closure, no
candidate registration, no gate adjudication here (single terminal G-015 after the full slate).

## Implementation Safety Constraints (for `experiment-developer`)

- **Holdout fence (binding).** TRAIN = first 70% of the first-70% analysis set, by **file-order prefix**
  (F01): `analysis_rows = int(total*0.7)`, `train_rows = int(analysis_rows*0.7)`, collect only the first
  `train_rows` rows via `pl.scan_parquet(...).slice(0, train_rows)`. **Never** sort/collect the full
  file; **never** read TEST or the final-30% global holdout. Assert chronological; `train_end_ts` = last
  `CloseTime`. Reuse the existing `load_train_1m` unchanged.
- **Temporal ordering & alignment.** Order by `CloseTime`; align HA/ZigZag/MA events to real domain bars
  by exact `CloseTime`-epoch match (`_map_to_grid`), never by bar index. Domain aggregation: 5m strict,
  others `min_coverage=0.90`, then fence every bar to `CloseTime ≤ train_end_ts`.
- **Causality / no look-ahead.** MA(20,50) `_sma` trailing only; both the **native** `/STRONG-STAT`
  filter (MA-segment magnitudes) and the **hybrid** `/STRONG-STAT` filter (ZigZag-move magnitudes)
  reference only moves/segments confirmed **before** entry; `M_sofar`, benchmark levels, and the
  adaptive cap (MA-segment) from `live_in_progress_state` / `adaptive_time_caps_by_epoch` use only
  pre-entry confirmed information and bars at/before the entry bar. Matched-random entries constructed
  causally. Forward scan reads only `[entry_idx+1, min(entry_idx+N, last_train_idx)]`. Keep the
  `_causality_ok` gate and extend it to assert the hybrid mask references only pre-entry ZigZag moves.
- **Hybrid arm construction (the one new path).** `H0` population = `ma["buildable"] &
  zz["stat"]["retained_p75"]` — the **MA-segment** benchmark geometry (`rd`/`M_sofar`/fav/adv/cap from
  the MA context) resolved over the events selected by the **ZigZag** `/STRONG-STAT` mask. Refactor
  `bench_signal_arm` to accept an explicit conditioning mask while taking geometry from the MA context;
  the native arm passes `ma["stat"]["retained_p75"]`, the hybrid arm passes `zz["stat"]["retained_p75"]`.
  Do **not** alter the native/Z arm computations (they must stay byte-identical for reconciliation).
- **Real-price discipline.** Detection on HA candles only; **every** outcome metric on real OHLC;
  MA(20,50) on **real close**. No HA price enters any metric.
- **Denominators / zero-baseline.** Per-event gross return defined only for **qualifying** events
  (`fav_dist > 0`, finite positive `ATR_entry`, finite P15 fill in the TRAIN-fenced window).
  `DATA_CENSORED` + warmup events **excluded** from median/mean/trim and **disclosed as counts** per
  cell per arm. A cell with **< 30 qualifying events** on an arm is `NOT_VIABLE-by-power` for that arm
  (non-reportable) — never an undefined/infinite ratio. Worst-5% tail-share with 0 negative mass = 0.0
  (finite), not NaN/inf.
- **RNG discipline (reproduction-safe).** The hybrid null `RH0` draw and its median/mean/trim bootstraps
  use **new dedicated RNG purpose offsets** distinct from every existing stream (`PB_RM0_*`, `PB_RZ0_*`,
  `PB_MASEG*`, `PB_STAT*`), so the existing `M0`/`RM0`/`Z0`/`RZ0` median/mean/trim streams remain
  **byte-identical** to the prior run (required for the `M0`/`Z0` reconciliation to hold). The hybrid
  signal arm `H0` shares no RNG with the null.
- **Determinism (P12).** Fixed per-cell seed throughout; second full pass asserting byte-identical
  per-arm returns/medians/CIs and the `H0−RH0` / `M0−RM0` / `Z0−RZ0` contrasts. Output byte-identical
  across worker counts (order-independent RNG + fixed merge order).
- **Vectorization discipline.** Reuse the existing NumPy/Polars vectorized resolvers verbatim; do not
  rewrite the sequential causal state construction. The only new code path is the hybrid-mask
  `bench_signal_arm` call (`H0`) and the BENCH-geometry `matched_random_arm` call matched to `H0`'s
  count (`RH0`), plus existing trimmed-mean/tail-share on the existing bootstrap.
- **Performance / parallelism (integrity-preserving).** Keep the per-instrument `ProcessPoolExecutor`
  with per-process native-thread pinning (`POLARS_MAX_THREADS=1` etc.) and fixed-order reassembly.
  Parallelism must **not** alter sample membership, ordering, denominators, metric definitions, seeds,
  or causal/streaming semantics — byte-identical output for any `--workers`.
- **Reconciliation source.** Load EXP-060B's `per_cell_expectancy.parquet` (`BENCH-MA` M0 / `BENCH-ZZ`
  Z0 per-cell median + count) as the P12 anchor for the **native** and **ZigZag** arms; load EXP-053's
  conditioned-population count (its `/STRONG-STAT` retained set) as the **hybrid conditioning-mask**
  anchor. A missing/zero-checked anchor ⇒ SUBSTRATE/METHOD_DEFECT.
- **Bounded memory / progress.** `tqdm` over the 99-cell grid (per-instrument worker); forward scans
  bounded by `bench_n ≈ 6`; per-cell arrays released after summarisation. Plots built from collected
  per-cell summaries only — **no** data reloads or chart regeneration for plotting.
- **Outputs (`results/`).** `per_cell_expectancy.parquet` (per cell × arm with `object`/`role` tags),
  `object_efficacy_map.csv` (per object: signal-vs-null discriminator + P11 non-4h tally + EVIDENCE_*),
  `substrate_contrast.csv` (`H0−RH0`, `M0−RM0`, `Z0−RZ0`), `reconciliation.csv` (`M0`↔EXP-060B M0,
  `Z0`↔EXP-060B Z0 median/count 1e-9; `H0` ZZ-conditioning↔EXP-053 count exact), `readiness.csv`
  (per-cell construction PASS / coverage / invariant flags), `generalisation_readout.json` (per-object
  EVIDENCE_FOR / EVIDENCE_AGAINST / INCONCLUSIVE / SUBSTRATE_METHOD_DEFECT → G-015 input),
  `run_metadata.json` (seed, frozen constants, EXP-053/060/060B source paths/hashes, parallelism note,
  holdout fence). Output dirs created only in orchestration.

## Complexity Check

- **Statistical tests/methods: 3 / 3** — (1) median moving-block bootstrap CI (binding); (2) mean +
  10% trimmed-mean bootstrap CI + worst-5% tail-share (P4 diagnostic); (3) independent same-object
  signal−null contrast CI (`H0−RH0`, `M0−RM0`, disclosed `Z0−RZ0`). A re-instrumentation across the
  6-arm set, not new methods.
- **Visualisations: 5 / 5** — per-object signal-vs-null forest; hybrid-vs-native viability map;
  substrate contrast by domain; median-vs-mean (P4 skew preview); per-object P11 composition.
- **New modules: 0 / ≤1** — reuses the existing `code/run_experiment.py` machinery and all `xen/`
  modules; the only additions are the hybrid-mask `bench_signal_arm` call (`H0`) and a BENCH-geometry
  `matched_random_arm` call matched to `H0`'s count (`RH0`) on new dedicated RNG offsets. At most one
  thin orchestration change under `code/`; **no new `xen/` analysis module**.

Plan fits the scope's complexity budget exactly.
</content>
