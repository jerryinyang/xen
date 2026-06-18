# Analysis Plan: Experiment EXP-064

**MA(20,50)-Substrate Favourable-Target Geometry (Conditioned HA Harami; `/VPTARGET`, `/MAGTARGET` vs Benchmark 50%; Dual Conditioning Object: Hybrid and Native)**
Phase 015 surface **S1** · `CF-HA-HARAMI-001/HYP-017` · forks EXP-063's **dual-object** harness (which forks EXP-061/060/060B); composes EXP-056 `xen.favourable_targets` on MA references.

> **Re-run under `D0-amendment-001-dual-parallel-substrate.md` (2026-06-17).** The prior EXP-064 plan
> measured a single MA favourable-target axis labelled *hybrid* but reconciled its benchmark arm to
> EXP-061 `M0` — the **native** object. The genuine **hybrid** object (ZigZag-`/STRONG-STAT`-conditioned ×
> MA favourable geometry) and the native object were not both computed. This plan emits the full 8-variant
> favourable axis **for both objects individually** (separate variant arms, separate matched-random nulls,
> separate composition, separate EVIDENCE fork — never pooled) and corrects the reconciliation roles
> (native `M-BENCH` ↔ EXP-061 `M0`; hybrid `H-BENCH` ↔ EXP-061 `H0`). EXP-064 was paused (no `results/`),
> so resumption is dual-object from the start.

> **Mandatory-reading precondition honoured.** `014-A-conditioning-gap-and-validation-lessons.md` was
> read in full (recorded in `scope.md`); this plan keeps the conditioning / harami-anchor /
> descriptive-position / median-endpoint rules. The matched-random-on-MA controls are deliberate **nulls**
> (per object, binding per P5), not signal claims; every outcome metric is on real prices; MA(20,50) on
> real close; no position-in-move metric is used; the VP/MAG references are **confirmed completed** MA
> segments known at entry, never an unconfirmed crossover.

## Objective

Decide, on the 99-cell TRAIN grid and the MA(20,50) substrate, **for each conditioning object individually
(hybrid, native; never pooled)**, whether **changing only the favourable target** of the `/STRONG`-conditioned
HA harami improves gross per-event **median** expectancy over that object's benchmark 50%-of-`M_sofar` target —
and whether any improvement is **signal-attributable** (beats that object's matched-random-on-MA null). The
variant set is the EXP-056 grid reused unchanged on MA references (D0 P8): benchmark, three binding `/VPTARGET`
(POC / near-VA / far-VA of the prior *completed MA segment*), four `/MAGTARGET` (`frac ∈ {0.5,1.0} × W ∈ {5,20}`
over trailing MA-segment magnitudes). For each variant **of each object** the binding readout is the
conjunction:

- the variant is **median-viable** per cell (one-sided 95% regime-clustered moving-block-bootstrap CI_low > 0,
  ≥ 30 qualifying events), **AND**
- the variant **beats its own same-object matched-random-on-MA null** (`variant − RM` independent-contrast
  median CI_low > 0; P5 signal-attribution), **AND**
- the variant **beats that object's benchmark MA variant** (`variant − benchmark` paired-median contrast
  CI_low > 0), **AND**
- this clears **P11** (≥ 5 cells over ≥ 3 instruments) **with the P6 non-4h rule** (≥ 3 qualifying cells
  outside 4h), **for that object**.

The two conditioning objects (P2):

- **Hybrid (`H-*`)** — `/STRONG-STAT` p75 on the **in-progress confirmed ZigZag move**; mask byte-identical to
  EXP-053/060/061's hybrid `H0` (population reconciles to EXP-053's 3202-class set). **Genuinely-new object**
  for the favourable axis; internal-lineage anchor is EXP-061 `H0` (the `H-BENCH` variant reproduces it); no
  EXP-060B/056 outcome anchor.
- **Native (`M-*`)** — `/STRONG-STAT` p75 recomputed on the **in-progress confirmed MA segment**; population
  byte-identical to EXP-061 native `M0` / EXP-060B `BENCH-MA` (8360-class); the `M-BENCH` variant reconciles to
  them (1e-9).

Both objects score on the **same** MA outcome geometry (`rd` / `M_sofar` / favourable references / cap — all
from the shared MA in-progress state); they differ only in *which haramis qualify*. Binding endpoint =
**median** per-event gross ATR-normalised return (P3/P14), per object. The **mean** (raw + 10% trimmed +
worst-5% tail-share, each CI'd) is the **P4 diagnostic co-primary** — disclosed, never a viability gate. The
phase-level reading of this lever is the **stronger object's** outcome (per EXP-061, native is the expressing
object), with the other documented in parallel.

This is also the favourable-target readiness/reconciliation precondition: **`M-BENCH` (native 1:1) must
reproduce EXP-061 `M0` / EXP-060B `BENCH-MA`** and **`H-BENCH` (hybrid 1:1) must reproduce EXP-061 `H0`**
per-cell median + qualifying count to `RECON_TOL = 1e-9` (P12). A reconciliation/causality/determinism/invariant
failure is a **SUBSTRATE/METHOD_DEFECT** fixed before any efficacy read is interpreted. **The two objects are
never pooled.**

## Methodology

A **parameterised re-instrumentation** of the frozen EXP-061 dual-object pipeline composed with EXP-056's
`xen.favourable_targets`, not new algorithms. The favourable-target builder (volume profile, trailing-magnitude
target, `barriers_from_fav`) and the four contrast/bootstrap methods already exist; EXP-063 already provides the
dual-object per-variant OAT loop, per-object matched-random nulls, and the P4 mean/trim/tail bootstrap. The
orchestration changes vs EXP-063 are: (a) the per-variant axis becomes the **8-variant favourable-target grid**
(replacing EXP-063's 4-variant adverse grid), built by `xen.favourable_targets` pointed at **MA-segment
references**, with adverse held at benchmark 1:1 and the third barrier at the MA adaptive cap; (b) the binding
lever is the **variant − benchmark** paired contrast (EXP-056's question) alongside the **variant − RM** signal
attribution.

The arms per cell: for each object O ∈ {native `M`, hybrid `H`} and each variant V ∈ {BENCH, VP-POC, VP-near-VA,
VP-far-VA, MAG-0.5×5, MAG-1.0×5, MAG-0.5×20, MAG-1.0×20}: the signal arm `{O}-{V}` and its own-object null
`R{O}-{V}` (native nulls `RM-*`, hybrid nulls `RH-*`). Native arms condition on `ma["stat"]["retained_p75"]`;
hybrid arms condition on `zz["stat"]["retained_p75"]` (the same mask EXP-061 used for `H0`, applied through the
MA context). Plus a disclosed ZigZag `Z-BENCH` contrast and a disclosed in-progress VP-POC, per object. **The
two objects are reported individually; no arm sums or averages across objects.**

### Step 1 — Per-cell median expectancy + bootstrap CI, per variant **per object** (binding viability)

- **Method**: per-cell **median** of the per-event gross ATR-normalised return, with a **regime-clustered
  moving-block bootstrap** CI (`b = max(1, round(m^(1/3)))`, `N_BOOT = 10_000`, one-sided 95% lower bound +
  two-sided bounds), via `xen.expectancy.bootstrap_median_distribution` + `median_ci`. Computed for each of the
  8 favourable variants on **each** object's binding `/STRONG-STAT` signal arm (16 signal arms per cell).
  **Fixed per-cell seed** (`(BASE_SEED, cell_index, purpose)`, P3) with a **distinct purpose per
  object/variant/statistic**, so the **`M-BENCH` median path stays byte-identical to EXP-061 `M0`** and the
  **`H-BENCH` median path stays byte-identical to EXP-061 `H0`** (the two reconciliation anchors).
- **Why this method**: the per-event return distribution is fat-tailed and serially dependent within a regime;
  the median is robust to the left tail and is the binding programme endpoint (P14). The moving-block bootstrap
  respects within-regime serial dependence without assuming a distribution (methods-catalog: bootstrap CI
  preferred over parametric; ≥ 10,000 resamples; inherited, programme-frozen).
- **Simpler alternative considered**: i.i.d. percentile bootstrap or a sign test on the median. Rejected —
  i.i.d. resampling understates the CI under serial dependence; the sign test discards magnitude.
- **Assumptions**: within-block exchangeability of regime-clustered events; no distributional shape assumed
  (non-parametric). Fits time-ordered financial data far better than any normal-theory CI.
- **Expected output**: per cell × object × variant × {`/STRONG-STAT` binding} — `median`, `ci_low_1s`,
  `ci_lo_2s`, `ci_hi_2s`, `m` (qualifying count), `median_viable` flag (CI_low>0 ∧ m≥30).

### Step 2 — Per-cell mean + 10% trimmed mean + worst-5% tail-share, per variant **per object** (P4 diagnostic, disclosed)

- **Method**: the **same** moving-block bootstrap (byte-identical block construction; **dedicated RNG streams**
  so the median path is untouched) applied to (a) the **raw mean** and (b) the **10% symmetric trimmed mean** via
  EXP-061's `bootstrap_stat_distribution(values, rng, "mean"|"trim")` + `median_ci` for percentile bounds; plus
  (c) the **worst-5% tail-share** = fraction of total negative return contributed by the worst 5% of events
  (`_tail_share_worst5`; descriptive scalar per cell, no CI). Computed per variant **per object**. Each of
  (a)/(b) gets a bootstrap CI. The trim fraction **10%** and tail fraction **worst-5%** are D0-ratified (P4),
  frozen, never switched post-result.
- **Why this method**: the Phase 015 mean-diagnostic mandate (D0 P4) requires every outcome read to separate
  outlier-driven from structural negativity. At the MA benchmark 1:1 adverse geometry, a favourable-target
  change can shift either the median or the tail; this step shows which, per object. It is disclosed, never a
  viability gate (P4 closure-on-mean rule: a raw-mean-CI miss never closes anything here).
- **Simpler alternative considered**: report the raw mean only (as EXP-056 did). Rejected — the raw mean alone
  cannot distinguish removable-tail from structural negativity, the entire P4 mandate.
- **Assumptions**: same as Step 1; the mean/trimmed mean are tail-sensitive so their CIs are wider — that width
  *is* the measurement, not a defect.
- **Expected output**: per cell × object × variant (binding arm) — `mean`, `mean_ci_*`, `trimmed_mean_10pct`,
  `trimmed_mean_ci_*`, `tail_share_worst5pct`, `gap = median − mean`. A disclosed `mean_viable` flag is reported
  but **never** sets a viability flag (P4 closure rule).

### Step 3 — Per-variant signal-vs-null contrast `variant − RM-on-MA`, **per object** (binding signal attribution, P5)

- **Method**: for each variant **of each object** build a **matched-count random-in-regime** control (native:
  `RM-BENCH/RM-VP-*/RM-MAG-*`; hybrid: `RH-BENCH/RH-VP-*/RH-MAG-*`) via the EXP-061 `matched_random_arm` run
  through that variant's **identical** favourable + adverse + cap + P15 pipeline. The eligible pool = valid live
  MA state, `m_sofar > 0`, finite positive ATR, not-in-warmup, **excluding that object's conditioned-harami
  entries**; matched-count to **that object's** variant qualifying count; **fresh dedicated RNG purposes per
  object per variant** so no existing stream shifts and the hybrid/native nulls are disjoint. Then the
  **independence-assuming** `xen.expectancy.contrast_ci` on the stored bootstrap distributions of the variant
  signal arm and its RM arm — **median** (binding) and **mean** (disclosed) — gives `variant − RM`. `beats_rm` =
  (`variant − RM` median CI_low_1s > 0), per object.
- **Why this method**: P5 mandates the own-substrate random control in *every* read **per object** — the test
  that disentangled signal from MA-geometry drift in EXP-060B. A variant median-positive only because the MA
  substrate drifts is not a harami edge. The variant (indexed over haramis) and RM (indexed over disjoint random
  in-regime draws) are **independent samples** with no common per-event subset to pair — exactly as
  EXP-060/060B/061 treat signal-vs-matched-random. The hybrid and native objects must each beat *their own* null
  (matched to their own count, excluding their own entries); a shared null would mis-attribute the lower-count
  hybrid object.
- **Simpler alternative considered**: a single Mann-Whitney on variant-vs-RM pooled, or one shared null for both
  objects. Rejected — the matched-random draws are not paired (disjoint pools), so an independence-assuming
  bootstrap contrast is the inherited construction (EXP-060B I2); a shared null violates P5.
- **Assumptions**: the two bootstrap distributions are independent (true by construction, disjoint pools).
  `NaN` bounds when an arm is power-limited (handled, never defaulted).
- **Expected output**: per cell × object × variant — `var_rm_median_low_1s`, `var_rm_mean_low_1s`, the `beats_rm`
  flag.

### Step 4 — Lever contrast `variant − benchmark`, **per object** (binding lever)

- **Method**: the **paired** `xen.favourable_targets.paired_median_contrast_ci` on the **common
  qualifying-event subset** of the variant and that object's benchmark MA arm (both indexed over the same
  object's conditioned haramis, so paired is correct and tighter). `beats_bench` = (`variant − benchmark` paired
  median CI_low_1s > 0), per object. The composite `variant_wins` flag = `median_viable ∧ beats_rm ∧
  beats_bench`, per object.
- **Why this method**: the lever question (does this favourable geometry beat the object's benchmark?) compares
  two geometries on the *same* events, so a paired contrast is correct and more powerful (methods-catalog:
  Wilcoxon/paired for matched observations; bootstrap variant here). This is the EXP-056 question, re-instrumented
  per object.
- **Simpler alternative considered**: a single Mann-Whitney on variant-vs-benchmark pooled. Rejected — it
  ignores the pairing (same events) and the RM attribution leg; the two-contrast design is the inherited EXP-056
  + Phase-015-P5 construction.
- **Assumptions**: common-subset pairing well-defined (both arms qualify the event), within the object.
  `NaN` bounds when power-limited (handled, never defaulted).
- **Expected output**: per cell × object × variant — `var_bench_paired_low_1s`, the `beats_bench` flag, the
  composite `variant_wins` flag.

### Composition (mechanical, predeclared), per object — never pooled

- Per-cell first; then **P11** = ≥ 5 cells over ≥ 3 instruments on `variant_wins`, **with the P6 non-4h rule**
  (≥ 3 qualifying cells outside 4h), **computed separately for each object**. Reported per variant per object.
  Secondary P11 tallies for `median_viable`, `beats_rm`, `beats_bench` separately (diagnostic), per object.
- `fragile` flag when a tally composes at exactly the quorum boundary (5 cells / 3 instruments / 3 non-4h cells),
  so the readout discloses thin composition.
- **Disclosed substrate contrast (deferred):** a direct ZigZag-substrate benchmark contrast (EXP-056's 0/8
  ZigZag result, reconciling to EXP-056 benchmark) is a **deferred** disclosed secondary (runtime/budget; the
  ZigZag substrate carries its own M_sofar/cap pipeline), recorded in `run_metadata.json` — exactly the EXP-063
  dual-object deferral pattern. The per-object MA EVIDENCE_* readout vs EXP-056's ZigZag 0/8 is the comparison
  retained here; a full ZigZag-favourable surface is a bounded follow-up if G-015 needs it.

## Visualisations (5 / 5 budget) — each carries both objects (hybrid + native), never pooled

1. **Per-variant median-expectancy forest vs benchmark** (headline) — per cell, each variant's median CI
   alongside that object's benchmark, sorted; coloured by `variant_wins`; **native and hybrid as distinct
   panels/series**. Answers: does any favourable-target variant beat benchmark cell by cell, and is it
   signal-attributable — per object?
2. **Variant−benchmark and variant−RM contrast heatmap** (variants × cells) — two-panel; non-4h cells marked;
   **per object**. Answers: where on the grid does each lever bite, and does it survive the RM null — per object?
3. **Expectancy distribution by variant (pooled within object)** — violin/box of per-event returns by variant,
   **native and hybrid panels**. Answers: how does each favourable geometry reshape the return distribution (not
   just the median) — per object?
4. **P11 (non-4h) composition / wins map** across variants — per-variant tally of `variant_wins`,
   `median_viable`, `beats_rm`, `beats_bench`; quorum line drawn; **native and hybrid side-by-side**. Answers:
   which variant (if any) clears the binding quorum, and is composition carried by 4h cells (the P6 concern) —
   per object?
5. **Median-vs-mean (P4 skew preview)** for benchmark + best variant — per-cell median vs raw mean vs 10%
   trimmed mean, worst-5% tail-share annotated, **native and hybrid panels**. Answers: at the MA 1:1 adverse
   geometry, is any negative mean removable-tail-driven or structural — per object?

Both objects are carried within the 5-plot budget (panels/series within each figure). Secondary tables
(`per_cell_expectancy`, `favourable_target_map`, `secondary_map`, `reconciliation`) go to CSV/parquet, not plots.

## Interpretation Guide (predeclared; mirrors `scope.md` Success/Failure), per object

- **EVIDENCE_FOR (a favourable-target lever helps on MA, for that object)** — ≥ 1 alternative variant is
  median-viable **AND** beats its same-object RM-on-MA null **AND** beats that object's benchmark MA variant,
  composed by P11 with the non-4h rule. Means: favourable-target geometry is an MA-substrate lever for that
  object; the winning variant + its margins feed EXP-067 (hybrid) / EXP-068 (native) / G-015.
- **EVIDENCE_AGAINST (favourable geometry is not an MA lever for that object)** — no alternative variant clears
  the combined (`median_viable ∧ beats_rm ∧ beats_bench`) P11 quorum for that object. Means: as on ZigZag
  (EXP-056 0/8), the favourable target is not the lever on MA for that object. **Family stays OPEN** — the
  surface (S2/S3/S4) runs regardless (P9 no-early-closure).
- **INCONCLUSIVE (power-limited)** — fewer than the P11 quorum of cells reach ≥ 30 qualifying events on the
  variants of interest for that object (validity/warmup exclusions deplete counts; the hybrid 3202-class object
  is expected more power-limited than native 8360-class), no correctness failure. Disclosed explicitly; never
  the default. (An INCONCLUSIVE hybrid + an expressing native is itself a deliverable.)
- **Hybrid vs native divergence (the central new fact):** EXP-061 found native generalises while hybrid does not
  at the benchmark geometry. If native is EVIDENCE_FOR while hybrid is EVIDENCE_AGAINST/INCONCLUSIVE, the
  favourable-target behaviour is a matched-substrate conditioning property; convergence would broaden the claim.
  The divergence is the deliverable, not a defect.
- **SUBSTRATE/METHOD_DEFECT** — any reconciliation/determinism/causality/invariant failure. Checks: (i) **native
  `M-BENCH` reproduces EXP-061 `M0` / EXP-060B `BENCH-MA`** and **hybrid `H-BENCH` reproduces EXP-061 `H0`**
  per-cell median + count to `RECON_TOL = 1e-9`; (ii) population reconciliation: hybrid ↔ EXP-053/060/061 `H0`
  (3202-class), native ↔ EXP-060B/061 `M0` (8360-class), exact; (iii) **matched-count holds per object** — each
  variant's RM/RH count equals that object's cell variant signal-arm count; (iv) the 1:1 adverse stop, when it
  binds, closes at the same bar/level; (v) every exit price is a real-bar P15 fill with `CloseTime ≤
  train_end_ts`; (vi) `fav_dist > 0` for every counted event. Fix before reporting any efficacy verdict.

Deliverable label: **MA_FAVOURABLE_TARGET_CHARACTERISED (dual-object)**. No phase closure, no candidate
registration, no gate adjudication here (single terminal G-015 after the full slate).

## Implementation Safety Constraints (for `experiment-developer`)

- **Holdout fence (binding).** TRAIN = first 70% of the first-70% analysis set, by **file-order prefix** (F01):
  `analysis_rows = int(total*0.7)`, `train_rows = int(analysis_rows*0.7)`, collect only the first `train_rows`
  rows via `pl.scan_parquet(...).slice(0, train_rows)`. **Never** sort/collect the full file; **never** read
  TEST or the final-30% global holdout. Assert chronological; `train_end_ts` = last `CloseTime`. Reuse EXP-061's
  `load_train_1m` unchanged.
- **Temporal ordering & alignment.** Order by `CloseTime`; align HA/ZigZag/MA events to real domain bars by
  exact `CloseTime`-epoch match (`_map_to_grid`), never by bar index. The **same** harami `entry_idx` feeds both
  objects; verify `ma["entry_idx"]` and `zz["entry_idx"]` are the identical array before applying the
  cross-substrate hybrid mask through the MA context (EXP-061 already does this for `H0`). Domain aggregation:
  5m strict, others `min_coverage=0.90` (`xen.bar_aggregator.aggregate_ohlc`, carrying `TickVolume` for
  `/VPTARGET`), then fence every bar to `CloseTime ≤ train_end_ts`.
- **Causality / no look-ahead.** MA(20,50) `_sma` trailing only; MA segments bounded by crossovers confirmed
  **before** entry; `M_sofar`, the VP reference (prior *completed* MA segment), `/MAGTARGET` trailing-W
  MA-segment magnitudes, the benchmark/variant favourable levels, and the MA adaptive cap use only pre-entry
  confirmed segments and bars at/before the entry bar (via `live_in_progress_state` /
  `adaptive_time_caps_by_epoch`). The native `/STRONG-STAT` filter references only confirmed prior MA segments.
  The VP reference segment's bars are all `CloseTime ≤ C`'s bar. **The MA in-progress state — hence `rd`,
  `M_sofar`, the fav references, and the cap — is shared by both objects**; only the qualifying mask differs.
  Matched-random-on-MA entries (both objects) constructed causally with the identical pre-entry-only state.
  Forward scan reads only `[entry_idx+1, min(entry_idx+N, last_train_idx)]`. Keep EXP-061's `_causality_ok` gate.
- **Real-price discipline.** Detection on HA candles only; **every** outcome metric (returns, `M_sofar`, volume
  profile, trailing magnitudes, levels, fills, ATR-normalisation, mean/trim/tail) on real OHLC. MA(20,50) on
  **real close**. `/VPTARGET` volume input = `TickVolume` (broker tick count, proxy — disclosed). No HA price
  enters any metric.
- **Denominators / zero-baseline.** Per-event return defined only for **qualifying** events (`fav_dist > 0`,
  valid profile/warmup, finite positive `ATR_entry`, finite P15 fill in the TRAIN-fenced window).
  `DATA_CENSORED` + warmup/validity-excluded events **excluded** from median/mean/trim and **disclosed as
  counts** per cell per variant per object. A cell with **< 30 qualifying events** on a variant/object is
  `NOT_VIABLE-by-power` (non-reportable) — never an undefined/infinite ratio. Worst-5% tail-share with 0
  negative mass → 0.0 (finite), not NaN/inf.
- **Determinism (P12).** Fixed per-cell seed throughout; **distinct RNG purpose per object/variant/statistic** so
  the `M-BENCH` median path is byte-identical to EXP-061 `M0`, the `H-BENCH` path byte-identical to EXP-061 `H0`,
  and no arm's stream perturbs another. Second full pass (or per-instrument first-cell replay, as EXP-061)
  asserting byte-identical per-object per-variant returns, medians, CIs, RM returns, and the contrasts. Output
  must be **byte-identical across worker counts** (order-independent RNG + fixed merge order).
- **Vectorization discipline.** Reuse EXP-061/EXP-063/EXP-056 vectorized resolvers and the `xen.favourable_targets`
  builder verbatim; do not rewrite the sequential causal state construction. New code paths vs EXP-063: the
  favourable-target builder pointed at MA segments (replacing EXP-063's adverse build), the per-variant
  matched-random call (**new dedicated RNG purpose offsets** so no existing median/RM stream shifts), and (already
  present in EXP-063) the trimmed-mean/tail-share statistic.
- **Performance / parallelism (integrity-preserving).** Keep EXP-061/EXP-063's per-instrument
  `ProcessPoolExecutor` with per-process native-thread pinning (`POLARS_MAX_THREADS=1` etc., set before importing
  polars/numpy) and fixed-order reassembly. Parallelism must **not** alter sample membership, ordering,
  denominators, metric definitions, seeds, or causal/streaming semantics — byte-identical output for any
  `--workers`. (Eight favourable variants × two objects × the RM controls per cell is a heavy read; the
  per-instrument process pool plus bounded per-cell memory is the integrity-preserving way to absorb it — and is
  why the `/STRONG-HA` and full ZigZag-favourable secondaries are deferred, see scope Exclusions.)
- **Reconciliation sources.** Load EXP-061's `per_cell_expectancy.parquet` (the `M0` **and** `H0` per-cell
  median + count) as the `M-BENCH` / `H-BENCH` P12 anchors — EXP-060B's available as the upstream native anchor.
  EXP-056's MA-seg baseline arms available as a *secondary cross-check* (disclosed; may differ if the MA
  construction differs from `ma_seg_arm` — note any difference, do not treat as a defect). A missing/zero anchor
  on checked cells ⇒ SUBSTRATE/METHOD_DEFECT.
- **Bounded memory / progress.** `tqdm` over the 99-cell grid (per-instrument worker); forward scans bounded by
  the MA cap; per-cell arrays released after summarisation. Plots from collected per-cell summaries only — **no**
  data reloads or chart regeneration for plotting.
- **Outputs (`results/`).** `per_cell_expectancy.parquet` (per cell × variant × **object**); `favourable_target_map.csv`
  (binding `/STRONG-STAT` summary per variant per object + P11 non-4h tally); `secondary_map.csv` (in-progress
  VP-POC, `r`, win rate, exit composition, censoring — per object; the `/STRONG-HA` arm and the full
  ZigZag-favourable surface **including the single ZigZag benchmark contrast** are **deferred**, recorded in
  `run_metadata.json`); `reconciliation.csv` (native
  `M-BENCH` ↔ EXP-061 M0 / EXP-060B BENCH-MA; hybrid `H-BENCH` ↔ EXP-061 H0; populations vs EXP-053/060/061, per
  object); `composition_readout.json` (per-object per-variant P11 non-4h, wins, EVIDENCE_* fork → G-015 input);
  `run_metadata.json` (seed, frozen + new constants, EXP-056/060/060B/061/063 source paths/hashes, parallelism
  note, holdout fence, `disclosed_secondaries_not_computed`). Output dirs created only in orchestration. Every
  per-cell record carries an `object` tag; per-object CSV/JSON keys separate hybrid and native; **no pooled
  aggregate is emitted**.

## Complexity Check

- **Statistical methods: 4 / 4** — (1) median moving-block bootstrap CI (binding, per variant per object); (2)
  mean + 10% trimmed-mean bootstrap CI + worst-5% tail-share (P4 diagnostic, per variant per object); (3)
  independent `variant − RM-on-MA` contrast CI (binding signal attribution, per variant per object); (4)
  `variant − benchmark` paired-median contrast CI (binding lever, per variant per object). **Running these four
  methods on the second (hybrid) object adds no distinct method** — same estimators, different population. A
  re-instrumentation of EXP-056 + EXP-061/063, not new methods.
- **Visualisations: 5 / 5** — per-variant forest; variant−benchmark/−RM contrast heatmap; expectancy
  distribution by variant; P11 (non-4h) wins map; median-vs-mean P4 preview. Each carries both objects within the
  5-plot budget.
- **New modules: 0 / ≤ 1** — reuses `xen.favourable_targets`, `xen.expectancy`, and the EXP-060/061/063
  dual-object MA pipeline; additions are MA-segment references into the existing favourable builder (replacing
  EXP-063's adverse build), the per-object per-variant RM call (new RNG purposes), and (already present) the
  trimmed-mean/tail-share statistic. At most one thin orchestration wrapper under `code/`; **no new `xen/`
  analysis module**.

Plan fits the scope's complexity budget exactly; the dual-object structure doubles arms/columns/series, not
methods or plots.
