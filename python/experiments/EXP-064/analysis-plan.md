# Analysis Plan: Experiment EXP-064

**MA(20,50)-Substrate Favourable-Target Geometry (Hybrid Conditioned HA Harami; `/VPTARGET`, `/MAGTARGET` vs Benchmark 50%)**
Phase 015 surface **S1** · `CF-HA-HARAMI-001/HYP-017` · forks EXP-061 + composes EXP-056 `xen.favourable_targets` on MA references.

> **Mandatory-reading precondition honoured.** `014-A-conditioning-gap-and-validation-lessons.md`
> was read in full (recorded in `scope.md`); this plan keeps the conditioning / harami-anchor /
> descriptive-position / median-endpoint rules. The matched-random-on-MA controls are deliberate
> **nulls** (binding per P5), not signal claims; every outcome metric is on real prices; no
> position-in-move metric is used.

## Objective

Decide, on the 99-cell TRAIN grid, whether **changing only the favourable target** of the hybrid
`/STRONG`-conditioned HA harami **on the MA(20,50) substrate** improves gross per-event **median**
expectancy over the benchmark 50%-of-`M_sofar` target — and whether any improvement is
**signal-attributable** (beats its matched-random-on-MA null). The variant set is the EXP-056 grid
reused unchanged on MA references (D0 P8): benchmark, three binding `/VPTARGET` (POC / near-VA / far-VA
of the prior *completed MA segment*), four `/MAGTARGET` (`frac ∈ {0.5,1.0} × W ∈ {5,20}` over trailing
MA-segment magnitudes). For each variant the binding readout is the conjunction:

- the variant is **median-viable** per cell (one-sided 95% regime-clustered moving-block-bootstrap
  CI_low > 0, ≥ 30 qualifying events), **AND**
- the variant **beats its own matched-random-on-MA null** (`variant − RM` independent-contrast median
  CI_low > 0; P5 signal-attribution), **AND**
- the variant **beats the benchmark MA variant** (`variant − benchmark` paired-median contrast
  CI_low > 0), **AND**
- this clears **P11** (≥ 5 cells over ≥ 3 instruments) **with the P6 non-4h rule** (≥ 3 qualifying
  cells outside 4h).

Binding endpoint = **median** per-event gross ATR-normalised return (P3/P14). The **mean** (raw + 10%
trimmed + worst-5% tail-share, each CI'd) is the **P4 diagnostic co-primary** — disclosed, never a
viability gate. This is also the favourable-target readiness/reconciliation precondition: the benchmark
MA arm must **reconcile to EXP-061 `M0` / EXP-060B `BENCH-MA`** per-cell median + count to float
tolerance (P12). A reconciliation/causality/determinism/invariant failure is a **SUBSTRATE/METHOD_DEFECT**
fixed before any efficacy read is interpreted.

## Methodology

The methods are a **parameterised re-instrumentation of the frozen EXP-061 / EXP-060B per-cell pipeline
composed with EXP-056's `xen.favourable_targets`**, not new algorithms. The favourable-target builder
(volume profile, trailing-magnitude target, `barriers_from_fav`) and the four contrast/bootstrap methods
already exist; the only new computation is (a) pointing the VP/MAG reference at **MA segments**, (b)
running the existing matched-random-on-MA selector through **each variant** geometry (RM per variant),
and (c) the 10% trimmed-mean / worst-5% tail-share diagnostic on the existing bootstrap.

### Step 1 — Per-cell median expectancy + bootstrap CI (binding viability)

- **Method**: per-cell **median** of the per-event gross ATR-normalised return, with a **regime-clustered
  moving-block bootstrap** CI (`b = round(m^(1/3))`, `N_BOOT = 10_000`, one-sided 95% lower bound +
  two-sided bounds), via `xen.expectancy.bootstrap_median_distribution` + `median_ci`. **Fixed per-cell
  seed** (`(BASE_SEED, cell_index, variant, purpose)`, P3) so absolute viability counts are stable across
  the slate.
- **Why this method**: the per-event return distribution is fat-tailed and serially dependent within a
  regime; the median is robust to the left tail and is the binding programme endpoint (P14). The
  moving-block bootstrap respects within-regime serial dependence without assuming a distribution
  (methods-catalog: bootstrap CI preferred over parametric; ≥10,000 resamples).
- **Simpler alternative considered**: i.i.d. percentile bootstrap or a sign test on the median. Rejected
  — i.i.d. resampling understates the CI under serial dependence; the sign test discards magnitude. The
  block bootstrap is the inherited, programme-frozen choice (EXP-049/053–063).
- **Assumptions**: within-block exchangeability of regime-clustered events; no distributional shape
  assumed (non-parametric). Fits time-ordered financial data far better than any normal-theory CI.
- **Expected output**: per cell × variant × {`/STRONG-STAT` (binding), `/STRONG-HA` (disclosed)} —
  `median`, `ci_low_1s`, `ci_lo_2s`, `ci_hi_2s`, `m` (qualifying count), `median_viable` flag (CI_low>0
  ∧ m≥30).

### Step 2 — Per-cell mean + 10% trimmed mean + worst-5% tail-share (P4 diagnostic, disclosed)

- **Method**: the **same** moving-block bootstrap (byte-identical block construction; dedicated RNG
  streams so the median path is untouched) applied to (a) the **raw mean**
  (`bootstrap_mean_distribution`), (b) the **10% symmetric trimmed mean** (new statistic on the same
  machinery), and (c) the **worst-5% tail-share** = fraction of total negative return contributed by the
  worst 5% of events (descriptive scalar per cell, reported without a CI). Each of (a)/(b) gets a
  bootstrap CI.
- **Why this method**: the Phase 015 mean-diagnostic mandate (D0 P4) requires every outcome read to
  separate outlier-driven from structural negativity. At the MA benchmark 1:1 geometry, a favourable-
  target change can shift either the median or the tail; this step shows which. It is disclosed, never a
  viability gate (P4 closure-on-mean rule: a raw-mean-CI miss never closes anything here).
- **Simpler alternative considered**: report the raw mean only (as EXP-056 did). Rejected — the raw mean
  alone cannot distinguish removable-tail from structural negativity, the entire P4 mandate.
- **Assumptions**: same as Step 1; the mean is tail-sensitive so its CI is wider — that width is the
  measurement, not a defect.
- **Expected output**: per cell × variant (binding arm) — `mean`, `mean_ci_*`, `trimmed_mean_10pct`,
  `trimmed_mean_ci_*`, `tail_share_worst5pct`. **Never** sets a viability flag.

### Step 3 — Signal-vs-null contrast `variant − RM` (binding, P5) and lever contrast `variant − benchmark` (binding)

- **Method (3a, signal attribution):** the **independence-assuming** `xen.expectancy.contrast_ci` on the
  stored bootstrap distributions of the variant signal arm and its **matched-random-on-MA** arm (RM, the
  EXP-060B selection reused, matched-count). The variant (indexed over haramis) and RM (indexed over
  disjoint random in-regime draws) are **independent samples** with no common per-event subset to pair —
  exactly as EXP-060/060B/061 treat signal-vs-matched-random. `beats_rm` = (`variant − RM` median
  CI_low_1s > 0).
- **Method (3b, lever):** the **paired** `xen.favourable_targets.paired_median_contrast_ci` on the
  **common qualifying-event subset** of the variant and the benchmark MA arm (both indexed over the same
  conditioned haramis, so paired is correct and tighter). `beats_bench` = (`variant − benchmark` paired
  median CI_low_1s > 0).
- **Why these methods**: signal attribution requires beating the own-substrate random control, not merely
  clearing zero (P5; the test that disentangled signal from substrate/drift in EXP-060B) — and the two
  arms are disjoint event pools, so an independence contrast is correct. The lever question (does this
  geometry beat benchmark?) compares two geometries on the *same* events, so a paired contrast is correct
  and more powerful (methods-catalog: Wilcoxon/paired for matched observations; bootstrap variant here).
- **Simpler alternative considered**: a single Mann-Whitney on variant-vs-benchmark pooled. Rejected —
  it ignores the pairing (same events) and the RM attribution leg; the two-contrast design is the
  inherited EXP-056 + Phase-015-P5 construction.
- **Assumptions**: 3a — the two bootstrap distributions are independent (true by construction, disjoint
  pools); 3b — common-subset pairing well-defined (both arms qualify the event). `NaN` bounds when an arm
  is power-limited (handled, never defaulted).
- **Expected output**: per cell × variant — `var_rm_median_low_1s`, `var_rm_mean_low_1s`,
  `var_bench_paired_low_1s`, the `beats_rm` and `beats_bench` flags, and the composite `variant_wins`
  flag (`median_viable ∧ beats_rm ∧ beats_bench`).

### Composition (mechanical, predeclared)

- Per-cell first; then **P11** = ≥ 5 cells over ≥ 3 instruments on `variant_wins`, **with the P6 non-4h
  rule**: ≥ 3 of the qualifying cells are **outside** the 4h domain. Reported per variant. Secondary P11
  tallies for `median_viable`, `beats_rm`, `beats_bench` separately (diagnostic).
- `fragile` flag when a tally composes at exactly the quorum boundary (5 cells / 3 instruments / 3 non-4h
  cells), so the readout discloses thin composition.
- **Disclosed substrate contrast:** the benchmark MA arm vs the disclosed ZigZag-substrate benchmark
  (reconciling to EXP-056 benchmark) — does the MA substrate change the favourable-target picture vs
  EXP-056's 0/8-variant ZigZag result?

## Visualisations (5 / 5 budget)

1. **Per-variant median-expectancy forest vs benchmark** (headline) — per cell, each variant's median CI
   alongside the benchmark, sorted; coloured by `variant_wins`. Answers: does any favourable-target
   variant beat benchmark cell by cell, and is it signal-attributable?
2. **Variant−benchmark and variant−RM contrast heatmap** (variants × cells) — two-panel; non-4h cells
   marked. Answers: where on the grid does each lever bite, and does it survive the RM null?
3. **Expectancy distribution by variant (pooled)** — violin/box of per-event returns by variant. Answers:
   how does each favourable geometry reshape the return distribution (not just the median)?
4. **P11 (non-4h) composition / wins map** across variants — per-variant tally of `variant_wins`,
   `median_viable`, `beats_rm`, `beats_bench`; quorum line drawn. Answers: which variant (if any) clears
   the binding quorum, and is composition carried by 4h cells (the P6 concern)?
5. **Median-vs-mean (P4 skew preview)** for benchmark + best variant — per-cell median vs raw mean vs 10%
   trimmed mean, worst-5% tail-share annotated. Answers: at the MA 1:1 geometry, is any negative mean
   removable-tail-driven or structural?

Secondary tables (`per_cell_expectancy`, `favourable_target_map`, `secondary_map`, `reconciliation`) to
CSV/parquet, not plots.

## Interpretation Guide (predeclared; mirrors `scope.md` Success/Failure)

- **EVIDENCE_FOR (a favourable-target lever helps on MA)** — if ≥1 alternative variant is median-viable
  **AND** beats its RM-on-MA null **AND** beats the benchmark MA variant, composed by P11 with the non-4h
  rule. Means: favourable-target geometry is an MA-substrate lever; the winning variant + its margins
  feed EXP-067 / G-015.
- **EVIDENCE_AGAINST (favourable geometry is not an MA lever)** — if no alternative variant clears the
  combined (`median_viable ∧ beats_rm ∧ beats_bench`) P11 quorum. Means: as on ZigZag (EXP-056 0/8), the
  favourable target is not the lever on MA. **Family stays OPEN** — the surface (S2/S3/S4, native) runs
  regardless (P9 no-early-closure).
- **INCONCLUSIVE (power-limited)** — if fewer than the P11 quorum of cells reach ≥30 qualifying events on
  the variants of interest (validity/warmup exclusions deplete counts), no correctness failure. Disclosed
  explicitly; never the default.
- **SUBSTRATE/METHOD_DEFECT** — any reconciliation, determinism, causality, or invariant failure. Checks:
  (i) benchmark MA arm reproduces EXP-061 `M0` / EXP-060B `BENCH-MA` per-cell median + count to
  `RECON_TOL = 1e-9`; (ii) population reconciliation vs EXP-053 exact; (iii) **matched-count holds** —
  each variant's RM count equals its cell's variant signal-arm count; (iv) the 1:1 stop, when it binds,
  closes at the same bar/level; (v) every exit price is a real-bar P15 fill with `CloseTime ≤
  train_end_ts`; (vi) `fav_dist > 0` for every counted event. Fix before reporting any efficacy verdict.

Deliverable label: **MA_FAVOURABLE_TARGET_CHARACTERISED**. No phase closure, no candidate registration,
no gate adjudication here (single terminal G-015 after the full slate).

## Implementation Safety Constraints (for `experiment-developer`)

- **Holdout fence (binding).** TRAIN = first 70% of the first-70% analysis set, by **file-order prefix**
  (F01): `analysis_rows = int(total*0.7)`, `train_rows = int(analysis_rows*0.7)`, collect only the first
  `train_rows` rows via `pl.scan_parquet(...).slice(0, train_rows)`. **Never** sort/collect the full
  file; **never** read TEST or the final-30% global holdout. Assert chronological; `train_end_ts` = last
  `CloseTime`. Reuse EXP-061's `load_train_1m` unchanged.
- **Temporal ordering & alignment.** Order by `CloseTime`; align HA/ZigZag/MA events to real domain bars
  by exact `CloseTime`-epoch match, never by bar index. Domain aggregation: 5m strict, others
  `min_coverage=0.90` (`xen.bar_aggregator.aggregate_ohlc`, carrying `TickVolume` for `/VPTARGET`), then
  fence every bar to `CloseTime ≤ train_end_ts`.
- **Causality / no look-ahead.** MA(20,50) `_sma` trailing only; MA segments bounded by crossovers
  confirmed **before** entry; `M_sofar`, the VP reference (prior *completed* MA segment), `/MAGTARGET`
  trailing-W MA-segment magnitudes, the benchmark levels, and the MA adaptive cap use only pre-entry
  confirmed segments and bars at/before the entry bar. Matched-random-on-MA entries constructed causally
  with the identical pre-entry-only state. Forward scan reads only `[entry_idx+1, min(entry_idx+N,
  last_train_idx)]`. Keep EXP-061's `_causality_ok` gate.
- **Real-price discipline.** Detection on HA candles only; **every** outcome metric (returns, M_sofar,
  volume profile, trailing magnitudes, levels, fills, ATR-normalisation) on real OHLC. MA(20,50) on
  **real close**. `/VPTARGET` volume input = `TickVolume` (broker tick count, proxy — disclosed). No HA
  price enters any metric.
- **Denominators / zero-baseline.** Per-event return defined only for **qualifying** events (`fav_dist >
  0`, valid profile/warmup, finite positive `ATR_entry`, finite P15 fill in the TRAIN-fenced window).
  `DATA_CENSORED` + warmup/validity-excluded events **excluded** from median/mean/trim and **disclosed as
  counts** per cell per variant. A cell with **< 30 qualifying events** on a variant is
  `NOT_VIABLE-by-power` (non-reportable) — never an undefined/infinite ratio. Worst-5% tail-share with 0
  negative mass → 0.0 (finite), not NaN/inf.
- **Determinism (P12).** Fixed per-cell-per-variant seed throughout; second full pass (or per-instrument
  first-cell replay, as EXP-061) asserting byte-identical returns, medians, CIs, RM returns, and the
  contrasts. Output must be **byte-identical across worker counts** (order-independent RNG + fixed merge
  order).
- **Vectorization discipline.** Reuse EXP-061/EXP-056 vectorized resolvers verbatim; do not rewrite the
  sequential causal state construction. New code paths: the favourable-target builder pointed at MA
  segments, the matched-random call per variant (**new dedicated RNG purpose offsets** so no existing
  median/RM stream shifts), and the trimmed-mean/tail-share statistic.
- **Performance / parallelism.** Keep EXP-061's per-instrument `ProcessPoolExecutor` with native-thread
  pinning (`POLARS_MAX_THREADS=1` etc.) and fixed-order reassembly. Parallelism must **not** alter sample
  membership, ordering, denominators, metric definitions, seeds, or causal/streaming semantics —
  byte-identical output for any `--workers`.
- **Reconciliation source.** Load EXP-061's `per_cell_expectancy.parquet` (the `BENCH-MA` M0 per-cell
  median + count) as the P12 anchor; EXP-060B `per_cell_expectancy.parquet` available as the upstream
  anchor. EXP-056's MA-seg baseline arms available as a *secondary cross-check* (disclosed; may differ if
  the MA construction differs from `ma_seg_arm` — note any difference, do not treat as a defect).
  Reconciliation absent/zero checked cells ⇒ SUBSTRATE/METHOD_DEFECT.
- **Bounded memory / progress.** `tqdm` over the 99-cell grid (per-instrument worker); forward scans
  bounded by the MA cap; per-cell arrays released after summarisation. Plots from collected per-cell
  summaries only — **no** data reloads or chart regeneration for plotting.
- **Outputs (`results/`).** `per_cell_expectancy.parquet`, `favourable_target_map.csv` (binding summary +
  P11 non-4h tally), `secondary_map.csv` (`/STRONG-HA`, in-progress VP-POC, ZigZag benchmark contrast),
  `reconciliation.csv` (benchmark MA arm ↔ EXP-061 M0 / EXP-060B BENCH-MA; population vs EXP-053),
  `composition_readout.json` (per-variant P11 non-4h, wins, EVIDENCE_* → G-015 input), `run_metadata.json`
  (seed, frozen + new constants, EXP-056/060/060B/061 source paths/hashes, parallelism note, holdout
  fence). Output dirs created only in orchestration.

## Complexity Check

- **Statistical methods: 4 / 4** — (1) median moving-block bootstrap CI (binding); (2) mean + 10%
  trimmed-mean bootstrap CI + worst-5% tail-share (P4 diagnostic); (3) `variant − RM` independent contrast
  CI (P5 signal attribution); (4) `variant − benchmark` paired-median contrast CI (lever). A
  re-instrumentation of EXP-056 + EXP-061, not new methods.
- **Visualisations: 5 / 5** — per-variant forest; variant−benchmark/−RM contrast heatmap; expectancy
  distribution by variant; P11 (non-4h) wins map; median-vs-mean P4 preview.
- **New modules: 0 / ≤1** — reuses `xen.favourable_targets`, `xen.expectancy`, and the EXP-060/061 MA
  pipeline; additions are MA-segment references into the existing builder, the per-variant RM call, and
  the trimmed-mean/tail-share statistic. At most one thin orchestration wrapper under `code/`; **no new
  `xen/` analysis module**.

Plan fits the scope's complexity budget exactly.
