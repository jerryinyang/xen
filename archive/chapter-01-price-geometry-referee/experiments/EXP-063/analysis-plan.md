# Analysis Plan: Experiment EXP-063

**MA(20,50)-Substrate Adverse Geometry & the Mean Investigation (Conditioned HA Harami; Benchmark 1:1, `/ADV-EXTREME-rr1`, `/ADV-NONE`, `/ADV-EXTREME-raw`; Dual Conditioning Object: Hybrid and Native)**
Phase 015 lead **L3** · `CF-HA-HARAMI-001/HYP-016` · forks EXP-061's **dual-object** harness (which forks EXP-060/060B); reuses `xen.adverse_targets` wholesale.

> **Re-run under `D0-amendment-001-dual-parallel-substrate.md` (2026-06-17).** The prior EXP-063 measured a
> single MA adverse surface labelled *hybrid* but actually conditioning on MA-segment `/STRONG-STAT` — the
> **native** object. The genuine **hybrid** object (ZigZag-`/STRONG-STAT`-conditioned × MA adverse geometry)
> was never computed. This plan emits the full 4-variant adverse axis **for both objects individually**
> (separate variant arms, separate matched-random nulls, separate mean decomposition, separate readout —
> never pooled) and supersedes the prior EXP-063 in place.

> **Mandatory-reading precondition honoured.** `014-A-conditioning-gap-and-validation-lessons.md` was
> read in full (recorded in `scope.md`); this plan keeps the conditioning / harami-anchor /
> descriptive-position / median-endpoint rules. The matched-random-on-MA controls are deliberate
> **nulls** (per object), not signal claims; every outcome metric is on real prices; MA(20,50) on real
> close; no position-in-move metric is used; the `/ADV-EXTREME` extreme is the **causal** running extreme of
> the in-progress (faded) MA segment, never an unconfirmed crossover.

## Objective

Decide, on the 99-cell TRAIN grid and the MA(20,50) substrate, **for each conditioning object individually
(hybrid, native; never pooled)**, the **two coupled questions** the L3 read exists to answer (design §3/§4):

1. **(Median lever)** Does varying **only the adverse target** — from the benchmark **1:1** stop to the
   extreme-anchored ≥1:1 stop (**`/ADV-EXTREME-rr1`**) — preserve a **median-viable, signal-attributable**
   conditioned-harami edge on MA *for that object*? Binding: a bounded-downside variant is **median-viable**
   per cell (one-sided 95% regime-clustered moving-block-bootstrap CI_low > 0, ≥ 30 events), **beats its own
   object's matched-random-on-MA null** (`variant − RM` contrast CI_low > 0), and **clears P11 with the P6
   non-4h rule** (≥ 5 cells / ≥ 3 instruments / ≥ 3 cells outside 4h).
2. **(The mean investigation — decisive, P4)** EXP-060B found the MA edge is **median-only**; EXP-062 sized
   the adverse tail per object. EXP-063 determines, **per object**, **why the mean is negative and whether
   bounding the downside fixes it**: per variant, the **raw mean + 10% trimmed mean + worst-5% tail-share**
   (each CI'd as relevant), and the **bounded-downside recovery contrast** `mean(bounded) − mean(/ADV-NONE)`
   per cell and composed.

The two conditioning objects (P2):

- **Hybrid (`H-*`)** — `/STRONG-STAT` p75 on the **in-progress confirmed ZigZag move**; mask byte-identical to
  EXP-053/060/061's hybrid `H0`. **Genuinely-new object** for the adverse axis; internal-lineage anchor is
  EXP-061 `H0` (the `H-BENCH` variant reproduces it); no EXP-060B/057 anchor.
- **Native (`M-*`)** — `/STRONG-STAT` p75 recomputed on the **in-progress confirmed MA segment**; population
  byte-identical to EXP-061 native `M0` / EXP-060B `BENCH-MA`; the `M-BENCH` variant reconciles to them (1e-9).

Both objects score on the **same** MA outcome geometry (`rd` / `M_sofar` / fav level / cap / `/ADV-EXTREME`
MA-segment extreme — all from the shared MA in-progress state); they differ only in *which haramis qualify*.

Binding endpoint = **median** per-event gross ATR-normalised return (P3/P14), per object. The **mean** is the
**P4 diagnostic co-primary** and the decisive content of this read — but **never a blind disqualifier**: the
**closure-on-mean rule** (P4) requires a *positive* demonstration of structural irrecoverability **on the
expressing object** (trimmed mean also negative **and** persists under bounded-downside **and** not
removable-tail-driven). `/ADV-NONE` is the **disclosed unbounded reference** (the skew source under study), not
a viability candidate; `/ADV-EXTREME-raw` is a disclosed secondary. EXP-063 **emits** the readout per object —
the single terminal **G-015** adjudicates closure/proceed after the full slate (no early-closure, P9). The
phase-level reading of this lever is the **stronger object's** (per EXP-061, native is the expressing object),
with the other documented in parallel.

The MA-substrate machinery is the same frozen pipeline EXP-061 reconciled: **`M-BENCH` (native 1:1) must
reproduce EXP-061 `M0` / EXP-060B `BENCH-MA`** and **`H-BENCH` (hybrid 1:1) must reproduce EXP-061 `H0`**
per-cell median + qualifying count to `RECON_TOL = 1e-9` (P12); and **each object's `*-NONE` MAE/tail behaviour
must be consistent with EXP-062's per-object `mae_tail_decomposition.csv`** (the L2→L3 hand-off; disclosed
cross-check). A reconciliation/causality/determinism/invariant failure is a **SUBSTRATE/METHOD_DEFECT** fixed
before any verdict. **The two objects are never pooled.**

## Methodology

A **parameterised re-instrumentation** of the frozen EXP-061 dual-object / EXP-057 machinery, not new
algorithms. The adverse-leg primitives are `xen.adverse_targets` (already substrate-generic — it takes
`start_idx`/`entry_idx`/`rd`/`atr` arrays); the favourable target, MA adaptive cap, P15 resolver, realised
returns, qualifying mask, median/mean/trim/tail bootstrap, and matched-random selector are reused from EXP-061
verbatim. EXP-061 already builds **both** conditioned populations (`H0` via the `bench_signal_arm` `cond_mask`
override with the ZigZag mask through the MA context; `M0` via the MA-segment mask) and **both** matched-random
nulls (`RH0`, `RM0`). The orchestration changes are: (a) a **per-variant loop** over the 4 adverse models; (b)
running each variant on **both** object populations; (c) a per-object per-variant matched-random null; (d) the
per-object bounded-downside **recovery contrast**.

The arms per cell: for each object O ∈ {native `M`, hybrid `H`} and each variant V ∈ {BENCH, RR1, NONE, RAW}:
the signal arm `{O}-{V}` and its own-object null `R{O}-{V}` (native nulls `RM-*`, hybrid nulls `RH-*`). Native
arms condition on `ma["stat"]["retained_p75"]`; hybrid arms condition on `zz["stat"]["retained_p75"]` (the same
mask EXP-061 used for `H0`, applied through the MA context). Plus a disclosed ZigZag `Z-BENCH` contrast. **The
two objects are reported individually; no arm sums or averages across objects.**

### Step 1 — Per-cell median expectancy + bootstrap CI, per variant **per object** (binding viability)

- **Method**: per-cell **median** of the per-event gross ATR-normalised return, with a **regime-clustered
  moving-block bootstrap** CI (`b = max(1, round(m^(1/3)))`, `N_BOOT = 10_000`, one-sided 95% lower bound +
  two-sided bounds), via `xen.expectancy.bootstrap_median_distribution` + `median_ci`. Computed for each of the
  4 variants on **each** object's binding `/STRONG-STAT` signal arm (8 signal arms per cell). **Fixed per-cell
  seed** (`(BASE_SEED, cell_index, purpose)`, P3) with a **distinct purpose per object/variant/statistic**, so
  the **`M-BENCH` median path stays byte-identical to EXP-061 `M0`** and the **`H-BENCH` median path stays
  byte-identical to EXP-061 `H0`** (the two reconciliation anchors).
- **Why this method**: the per-event return distribution is fat-tailed and serially dependent within a regime;
  the median is robust to the left tail and is the binding programme endpoint (P14). The moving-block bootstrap
  respects within-regime serial dependence without assuming a distribution (inherited, programme-frozen).
- **Simpler alternative considered**: i.i.d. percentile bootstrap or a sign test on the median. Rejected —
  i.i.d. understates the CI under serial dependence; the sign test discards magnitude.
- **Assumptions**: within-block exchangeability of regime-clustered events; non-parametric.
- **Expected output**: per cell × object × variant — `median`, `ci_low_1s`, `ci_lo_2s`, `ci_hi_2s`, `m`,
  `median_viable` flag.

### Step 2 — Per-cell raw mean + 10% trimmed mean + worst-5% tail-share, per variant **per object** (the P4 investigation — decisive)

- **Method**: the **same** moving-block bootstrap (byte-identical block construction; **dedicated RNG streams**
  so the median path is untouched) applied to (a) the **raw mean** and (b) the **10% symmetric trimmed mean** via
  EXP-061's `bootstrap_stat_distribution(values, rng, "mean"|"trim")` + `median_ci` for percentile bounds; plus
  (c) the **worst-5% tail-share** point estimate (`_tail_share_worst5`: fraction of total negative return
  contributed by the worst 5% of events). Computed per variant **per object**. The **trim fraction 10%** and
  **tail fraction worst-5%** are D0-ratified (P4), frozen, never switched post-result.
- **Why this method**: this is the core of the L3 mandate, now resolved on the object that actually expresses
  the edge (native) **and** on the new hybrid object. The decomposition separates **outlier-driven** negativity
  (trimmed mean crosses positive while raw mean does not; thin top-heavy tail-share) from **structural**
  negativity (trimmed mean *also* negative). Reporting it **per variant per object** lets us see whether the
  bounded models carry a less-negative mean than `/ADV-NONE`, *for that object*.
- **Simpler alternative considered**: report the raw mean only. Rejected — cannot distinguish removable-tail
  from structural negativity, the entire P4 mandate.
- **Assumptions**: same as Step 1; the mean/trimmed mean are tail-sensitive so their CIs are wider — that width
  *is* the skew measurement.
- **Expected output**: per cell × object × variant — `mean`, `mean_ci_*`, `trimmed_mean`, `trim_ci_*`,
  `tail_share_worst5`, `gap = median − mean`. A disclosed `mean_viable` flag (raw-mean CI_low_1s > 0) is reported
  but **never** gates viability (P4 closure rule).

### Step 3 — Per-variant signal-vs-null contrast `variant − RM-on-MA`, **per object** (binding signal attribution)

- **Method**: for each variant **of each object** build a **matched-count random-in-regime** control (native:
  RM-BENCH/RM-RR1/RM-NONE/RM-RAW; hybrid: RH-BENCH/RH-RR1/RH-NONE/RH-RAW) via the EXP-061 `matched_random_arm`
  run through that variant's **identical** adverse + favourable + cap + P15 pipeline. The eligible pool = valid
  live MA state, `m_sofar > 0`, finite positive ATR, not-in-warmup, **excluding that object's conditioned-harami
  entries**; matched-count to **that object's** variant qualifying count; **fresh dedicated RNG purposes per
  object per variant** so no existing stream shifts and the hybrid/native nulls are disjoint. Then the
  **independence-assuming** `xen.expectancy.contrast_ci` on the stored bootstrap distributions — **median**
  (binding) and **mean** (disclosed) — gives `variant − RM`. `variant_beats_rm` = (`variant − RM` median CI_low_1s
  > 0), per object.
- **Why this method**: P5 mandates the own-substrate random control in *every* read **per object** — the test
  that disentangled signal from MA-geometry drift in EXP-060B. A bounded variant median-positive only because the
  MA substrate drifts is not a harami edge. The hybrid and native objects must each beat *their own* null
  (matched to their own count, excluding their own entries); a shared null would mis-attribute the lower-count
  hybrid object.
- **Simpler alternative considered**: a paired Wilcoxon on matched events. Rejected — the matched-random draws
  are not paired (disjoint event sets), so an independence-assuming contrast on the bootstrap distributions is
  the correct inherited construction (EXP-060B I2). One shared null for both objects — rejected (P5).
- **Assumptions**: the two bootstrap distributions are independent (disjoint pools). `NaN` bounds when
  power-limited (handled, never defaulted).
- **Expected output**: per cell × object × variant — `var_rm_median_low_1s/hi_2s`, `var_rm_mean_low_1s`,
  `variant_beats_rm` flag, the composite `variant_generalises = median_viable ∧ variant_beats_rm`.

### Step 4 — Bounded-downside recovery contrast + variant−benchmark contrast, **per object** (the "can we fix it" read)

- **Method**: two contrasts per object, both feeding the §4 verdict:
  - **Bounded-downside recovery (mean):** `mean({O}-BENCH) − mean({O}-NONE)` and `mean({O}-RR1) − mean({O}-NONE)`
    per cell, via `xen.expectancy.contrast_ci` on the stored per-variant **mean** bootstrap distributions of
    **that object**. These variants resolve disjoint *exits* on the **same** entry population of the object (only
    the stop differs), so the contrast is the **recovery delta with its independent-bootstrap CI**:
    "does bounding the downside lift the average trade for this object?" `recovery_positive` = (recovery contrast
    CI_low_1s > 0), per object.
  - **Variant − benchmark (median, paired):** `xen.favourable_targets.paired_median_contrast_ci` on the
    **common qualifying-event subset** of {`{O}-RR1`, `{O}-RAW`, `{O}-NONE`} vs **`{O}-BENCH`** within the object
    — does an alternative adverse geometry beat the benchmark 1:1 *median* for that object? (The EXP-057 contrast,
    retained as a disclosed median-lever readout, per object.)
- **Why this method**: Step 4 is the mechanistic bridge from "the mean is negative" (EXP-060B) to "bounding the
  downside repairs it / does not", resolved per object. The recovery contrast is the direct measurement of the P4
  question; the variant−benchmark median contrast keeps the EXP-057 median-lever readout for continuity.
- **Simpler alternative considered**: compare raw mean point estimates without a CI. Rejected — a point-estimate
  difference cannot support the "materially lifted" / "structural" P4 verdict.
- **Assumptions**: recovery contrast — independence-assuming on the stored mean distributions; variant−benchmark
  — paired on the common qualifying subset (same entries, different exit), within the object.
  `NaN`/power-limited handled, never defaulted.
- **Expected output**: per cell × object — `recovery_bench_low_1s`, `recovery_rr1_low_1s`, `recovery_positive`
  flags; per variant × object — `var_bench_median_paired_low_1s`.

### The mean-concentration table (P4, descriptive — confronts the EXP-060B 4h concentration), per object

Tabulate per-variant `mean`, `trimmed_mean`, `tail_share_worst5`, and `recovery` **by instrument, domain, and
the low-n-4h flag** (a cell is `low_n_4h` if domain == 4h and `m < 60`), **per object**. Answers: is the negative
mean concentrated in specific instruments/domains (esp. the 8/14-low-n-4h cells that carried the EXP-060B lead),
or pervasive — and does the pattern differ between the native and hybrid objects? Descriptive — no CI, no gate.

### Composition (mechanical, predeclared), per object — never pooled

- Per-cell first; then **P11** = ≥ 5 cells over ≥ 3 instruments on a per-cell boolean, **with the P6 non-4h
  rule** (≥ 3 qualifying cells outside 4h), **computed separately for each object**. The binding flag is
  `variant_generalises` (median-viable ∧ beats own-object RM) per bounded-downside variant. Secondary P11
  tallies: `median_viable`, `variant_beats_rm`, `mean_viable` (disclosed), `recovery_positive` (disclosed). A
  `fragile` flag when a tally composes at exactly the quorum boundary.
- **The §4 verdict per the P4 closure rule** is composed from the bounded-downside variants **per object**:
  - **EVIDENCE_FOR** if a bounded variant `generalises` (P11 + non-4h) **and** the mean is materially lifted
    (recovery contrast CI_low > 0 in the quorum and/or the bounded variant's raw or trimmed mean clears 0 where
    `{O}-NONE`'s does not);
  - **MEDIAN_ONLY** if a bounded variant `generalises` but the raw mean stays negative, the **trimmed mean also**
    stays negative, **and** the recovery contrast does not lift the mean materially;
  - **EVIDENCE_AGAINST** if no bounded variant both clears P11 viability and beats its own-object RM;
  - **INCONCLUSIVE** if power-limited (< P11 quorum at ≥ 30 events) with no correctness failure (the hybrid
    object is expected the more power-limited per EXP-061).
  The phase-level reading is the **stronger object's** verdict; both are emitted.

## Visualisations (5 / 5 budget) — each carries both objects (hybrid + native), never pooled

1. **Per-variant median-expectancy forest** per cell vs benchmark — bounded-downside binding (`*-BENCH`,
   `*-RR1`) solid, `*-NONE` + `*-RAW` disclosed; **native and hybrid as distinct panels/series**, coloured by
   `median_viable`. Answers: does a stop-bearing geometry keep the median edge, per object?
2. **Per-variant `variant − RM-on-MA` signal-attribution forest** (non-4h cells marked), **per object**. Answers:
   is each variant's median attributable to the harami signal vs MA drift, for each object?
3. **The mean investigation (headline)** — per cell, per variant: raw mean vs 10%-trimmed mean with the worst-5%
   tail-share annotated, `*-NONE` vs the bounded variants side-by-side, **native and hybrid panels**. Answers: is
   the `*-NONE` mean negativity removable-tail-driven or structural, and do the bounded variants carry a
   less-negative mean — per object?
4. **Bounded-downside recovery map** — `mean(*-BENCH) − mean(*-NONE)` and `mean(*-RR1) − mean(*-NONE)` across
   cells (CI_low coloured), low-n-4h cells flagged, **per object**. Answers: does bounding the downside lift the
   mean, and is any lift concentrated in thin 4h cells — per object?
5. **P11 composition / verdict map** across variants — `median_viable`, `variant_beats_rm`, `variant_generalises`,
   `recovery_positive`, `mean_viable` per cell (heatmap, non-4h marked), **native and hybrid side-by-side**.
   Answers: where on the grid does the bounded-downside lever hold for each object, and which §4 verdict does each
   compose to?

Both objects are carried within the 5-plot budget (panels/series within each figure). Secondary tables
(`per_cell_expectancy`, `mean_investigation`, `signal_attribution`, `secondary_map`, `reconciliation`) go to
CSV/parquet, not plots.

## Interpretation Guide (predeclared; mirrors `scope.md` Success/Failure and the P4 closure rule), per object

- **EVIDENCE_FOR (bounded-downside lever helps + mean recoverable)** — for an object, a bounded-downside variant
  (`*-BENCH` or `*-RR1`) is median-viable, beats its own-object RM-on-MA null, clears P11 with non-4h breadth,
  **and** the §4 decomposition shows the mean is materially lifted by bounding. Means: a bounded-downside MA
  geometry both preserves the median edge and repairs the skew for that object — the strongest input toward a
  G-015 PROCEED_TO_SCREEN / MEAN_RECOVERABLE (tagged with the object).
- **MEDIAN_ONLY (median survives, mean structurally negative)** — for an object, a bounded variant generalises,
  but its raw mean stays negative, its **trimmed mean also** stays negative, and the recovery contrast does not
  lift the mean materially. Means: the negativity is **structural on the bounded-downside axis** for that object —
  the *positive* structural-irrecoverability demonstration the P4 closure rule requires (feeds a well-supported
  G-015 CHARACTERISED_NOT_VIABLE; never a closure here).
- **EVIDENCE_AGAINST (adverse geometry is not a median lever)** — for an object, no bounded-downside variant both
  clears P11 viability and beats its own RM null. Means: that object's MA median edge may require the `/ADV-NONE`
  asymmetry. **Family stays OPEN** — the surface (S1–S3, combined champions EXP-067 hybrid / EXP-068 native) runs
  regardless (P9).
- **INCONCLUSIVE (power-limited)** — for an object, fewer than the P11 quorum of cells reach ≥ 30 qualifying
  events on the variants/contrasts of interest; no correctness failure. Disclosed; never the default. (The hybrid
  object is expected the more power-limited per EXP-061's 1-cell benchmark result; an INCONCLUSIVE hybrid + an
  expressing native is itself a deliverable.)
- **Hybrid vs native divergence (the central new fact):** EXP-061 found native generalises while hybrid does not
  at the benchmark geometry. If native is EVIDENCE_FOR/MEDIAN_ONLY while hybrid is EVIDENCE_AGAINST/INCONCLUSIVE,
  the adverse/mean behaviour is a matched-substrate conditioning property; convergence would broaden the claim.
  The divergence is the deliverable, not a defect.
- **SUBSTRATE/METHOD_DEFECT** — any reconciliation/determinism/causality/invariant failure. Mechanical checks:
  (i) **`M-BENCH` reproduces EXP-061 `M0` / EXP-060B `BENCH-MA`** and **`H-BENCH` reproduces EXP-061 `H0`** per-cell
  median + qualifying count to `1e-9`; (ii) **`*-RAW` `adv_dist` ≤ `*-RR1` `adv_dist`** event-wise, each object;
  (iii) **`*-NONE` produces 0 ADV outcomes**, each object; (iv) population reconciliation: hybrid ↔
  EXP-053/060/061 `H0`, native ↔ EXP-060B/061 `M0`, exact; (v) **matched-count holds per object** — each RM/RH
  draw target equals its object's variant qualifying count; (vi) every exit price a real-bar P15 fill,
  `CloseTime ≤ train_end_ts`; (vii) **each object's `*-NONE` MAE/tail consistent with EXP-062's per-object
  `mae_tail_decomposition.csv`** (disclosed cross-check, not a hard gate). Fix before reporting any verdict.

Deliverable label: **MA_ADVERSE_GEOMETRY_AND_MEAN_CHARACTERISED (dual-object)**. No phase closure, no candidate
registration, no gate adjudication here (single terminal G-015 after the full slate).

## Implementation Safety Constraints (for `experiment-developer`)

- **Holdout fence (binding).** TRAIN = first 70% of the first-70% analysis set by **file-order prefix** (F01):
  `analysis_rows = int(total*0.7)`, `train_rows = int(analysis_rows*0.7)`, collect only the first `train_rows`
  rows via `pl.scan_parquet(...).slice(0, train_rows)`. **Never** sort/collect the full file; **never** read TEST
  or the final-30% global holdout. Assert chronological; `train_end_ts` = last `CloseTime`. Reuse EXP-061's
  `load_train_1m` unchanged.
- **Temporal ordering & alignment.** Order by `CloseTime`; align HA/ZigZag/MA events to real domain bars by exact
  `CloseTime`-epoch match (`_map_to_grid`), never by bar index. The **same** harami `entry_idx` feeds both objects;
  verify `ma["entry_idx"]` and `zz["entry_idx"]` are the identical array before applying the cross-substrate hybrid
  mask through the MA context (EXP-061 already does this for `H0`). Domain aggregation: 5m strict, others
  `min_coverage=0.90`, then fence every bar to `CloseTime ≤ train_end_ts`.
- **Causality / no look-ahead.** MA(20,50) `_sma` trailing only; MA segments bounded by crossovers confirmed
  **before** entry; `M_sofar`, the favourable level, and the adaptive cap from `live_in_progress_state` /
  `adaptive_time_caps_by_epoch` use only pre-entry confirmed segments and bars at/before entry. **The
  `/ADV-EXTREME` faded extreme is the in-progress MA segment's running extreme over `[ma_start_idx+1 …
  entry_idx]`** — `ma_start_idx` from the MA `live_in_progress_state.start_epoch` mapped to the grid (the last
  confirmed MA crossover at/before entry, P7 Q5); pass it to `xen.adverse_targets.faded_move_extreme`. **The MA
  in-progress state, hence the faded extreme and all geometry, is shared by both objects** — only the qualifying
  mask differs. Every scanned bar has `CloseTime ≤ C`'s bar. Matched-random entries (both objects) constructed
  causally with the identical pre-entry-only state. Forward scan reads only `[entry_idx+1, min(entry_idx+N,
  last_train_idx)]`. Keep EXP-061's `_causality_ok` gate (extend to assert the faded-extreme span end ≤ entry).
- **Real-price discipline.** Detection on HA candles only; **every** outcome metric (returns, `M_sofar`, fav/adv
  levels, faded extreme, ATR-normalisation, fills, mean/trim/tail) on real OHLC. MA(20,50) on **real close**. No
  HA price enters any metric.
- **Denominators / zero-baseline.** Per-event gross return defined only for **qualifying** events of a variant
  (of an object) — built barrier (valid `adv_dist ≥ ADV_FLOOR` for stopped variants, `*-NONE` always built; exit
  reaches a finite P15 fill in the TRAIN-fenced window). `DATA_CENSORED` + warmup + degeneracy events
  **excluded** from median/mean/trim/tail and **disclosed as counts** per cell per variant per object. A cell with
  **< 30 qualifying events** on a variant/object is `NOT_VIABLE-by-power` for that variant/object (non-reportable)
  — never an undefined/infinite ratio. Worst-5% tail-share: 0 negative mass → tail-share = 0.0 (finite), not
  NaN/inf. Recovery contrast defined only where both `*-NONE` and the bounded variant are powered on the **same**
  object; else disclosed power-limited, never defaulted. First-hit `r` for `*-NONE` degenerate (`n_ADV = 0` ⇒
  `r = 1.0` where any FAV) — report with the caveat; never binding.
- **Determinism (P12).** Fixed per-cell seed throughout; **distinct RNG purpose per object/variant/statistic** so
  the `M-BENCH` median path is byte-identical to EXP-061 `M0`, the `H-BENCH` path byte-identical to EXP-061 `H0`,
  and no arm's stream perturbs another. Second full pass (or per-instrument first-cell replay, as EXP-061)
  asserting byte-identical per-object per-variant returns, medians, means, trims, tail-shares, RM returns, and all
  contrasts. Output **byte-identical across worker counts** (order-independent RNG + fixed merge order).
- **Vectorization discipline.** Reuse EXP-061's NumPy/Polars vectorized resolvers and `xen.adverse_targets`
  builders verbatim; do not rewrite the sequential causal state construction or the bounded per-event
  `faded_move_extreme` scan. The only new code paths are the per-variant adverse-level build (existing
  `xen.adverse_targets`, fed the MA start index), running each variant on the second (hybrid) population (a mask
  swap — no new sequential algorithm), the per-object per-variant `matched_random_arm` call (new dedicated RNG
  purposes), and the recovery `contrast_ci`.
- **Performance / parallelism (integrity-preserving).** Keep EXP-061's per-instrument `ProcessPoolExecutor` with
  per-process native-thread pinning (`POLARS_MAX_THREADS=1`, etc., set before importing polars/numpy) and
  fixed-order reassembly. Parallelism must **not** alter sample membership, ordering, denominators, metric
  definitions, seeds, or causal/streaming semantics — byte-identical output for any `--workers`. (Four variants ×
  two objects × the RM controls per cell is the heaviest read in the slate; the per-instrument process pool plus
  bounded per-cell memory is the integrity-preserving way to absorb it — and is exactly why the `/STRONG-HA`/MAD/
  ZigZag-adverse secondaries are deferred, see scope Exclusions.)
- **Reconciliation sources.** Load EXP-061's `per_cell_expectancy.parquet` (the `M0` **and** `H0` per-cell median +
  count) as the `M-BENCH` / `H-BENCH` P12 anchors — or EXP-060B's for native; load EXP-062's per-object
  `mae_tail_decomposition.csv` for the per-object `*-NONE` MAE/tail disclosed cross-check. A missing/zero anchor on
  checked cells ⇒ SUBSTRATE/METHOD_DEFECT; the EXP-062 cross-check is disclosed, not a hard gate.
- **Bounded memory / progress.** `tqdm` over the 99-cell grid (per-instrument worker); forward scans bounded by
  `bench_n`; per-cell arrays released after summarisation. Plots built from collected per-cell summaries only — **no**
  data reloads or chart regeneration for plotting.
- **Outputs (`results/`).** `per_cell_expectancy.parquet` (per cell × variant × **object**); `adverse_map.csv`
  (binding `/STRONG-STAT` summary per variant per object + P11 non-4h tally); `mean_investigation.csv` (the §4
  decomposition per object — the headline deliverable); `signal_attribution.csv` (`variant − RM-on-MA` per variant
  per object); `secondary_map.csv` (per-variant per-object `r`, win rate, exit composition, censoring; disclosed
  `Z-BENCH`; `/STRONG-HA`/MAD/ZigZag-adverse arms **deferred** — runtime/budget, recorded in `run_metadata.json`);
  `reconciliation.csv` (native `M-BENCH` ↔ EXP-061 `M0` / EXP-060B; hybrid `H-BENCH` ↔ EXP-061 `H0`; `*-NONE` ↔
  EXP-062 tail; population vs EXP-053/060/061, per object); `composition_readout.json` (per-object per-variant P11 +
  non-4h, the EVIDENCE_FOR / MEDIAN_ONLY / EVIDENCE_AGAINST / INCONCLUSIVE fork per the P4 closure rule, per object
  → G-015 input); `run_metadata.json` (seed, frozen constants, EXP-061/EXP-062/EXP-060B source paths/hashes,
  parallelism note, holdout fence, `disclosed_secondaries_not_computed`). Output dirs created only in
  orchestration. Every per-cell record carries an `object` tag; per-object CSV/JSON keys separate hybrid and
  native; **no pooled aggregate is emitted**.

## Complexity Check

- **Statistical methods: 4 / 4** — (1) median moving-block bootstrap CI (binding, per variant); (2) raw mean +
  10% trimmed-mean bootstrap CI + worst-5% tail-share (P4, per variant); (3) independent `variant − RM-on-MA`
  contrast CI (binding signal attribution, per variant); (4) bounded-downside recovery contrast `mean(bounded) −
  mean(*-NONE)` + the variant−benchmark paired-median contrast. **Running these four methods on the second
  (hybrid) object adds no distinct method** — same estimators, different population. A parameterised
  re-instrumentation of EXP-057/EXP-061, not new methods.
- **Visualisations: 5 / 5** — per-variant median forest; per-variant `variant − RM` forest; the mean
  investigation (headline); bounded-downside recovery map; P11/verdict composition map. Each carries both objects
  within the 5-plot budget.
- **New modules: 0 / ≤ 1** — reuses `xen.adverse_targets` wholesale and the EXP-061 dual-object MA pipeline + P4
  functions; the only additions are the per-variant loop, running variants on the second object population, the
  per-object per-variant RM call (new RNG purposes), and the recovery `contrast_ci`. At most one thin
  orchestration wrapper under `code/`; **no new `xen/` analysis module**.

Plan fits the scope's complexity budget exactly; the dual-object structure doubles arms/columns/series, not
methods or plots.
