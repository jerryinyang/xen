# Analysis Plan: Experiment EXP-065

**MA(20,50)-Substrate Third-Barrier Geometry (Hybrid Conditioned HA Harami; `/THIRD-TIME`, `/THIRD-EVENT` vs Benchmark Adaptive Cap)**
Phase 015 surface **S2** · `CF-HA-HARAMI-001/HYP-018` · forks EXP-061 + composes EXP-058 `xen.third_barrier` on MA segments.

> **Mandatory-reading precondition honoured.** `014-A-conditioning-gap-and-validation-lessons.md`
> was read in full (recorded in `scope.md`); this plan keeps the conditioning / harami-anchor /
> descriptive-position / median-endpoint rules. The matched-random-on-MA controls are deliberate
> **nulls** (binding per P5); every outcome metric is on real prices; no position-in-move metric is
> used; the `/THIRD-EVENT` MA-segment exit is a forward-confirmed event acted on at the confirmation
> bar, never an unconfirmed crossover.

## Objective

Decide, on the 99-cell TRAIN grid, whether **changing only the third barrier** of the hybrid
`/STRONG`-conditioned HA harami **on the MA(20,50) substrate** — extending the holding horizon by time
(`/THIRD-TIME` floor ∈ {12,24,48}) or by structural MA-segment event (`/THIRD-EVENT`, 8× backstop) —
improves gross per-event **median** expectancy over the benchmark floor-6 MA adaptive cap, and whether
any improvement is **signal-attributable** (beats its matched-random-on-MA null) and at what censoring
cost. The variant set is the EXP-058 grid reused unchanged on MA (D0 P8): benchmark + 3 `/THIRD-TIME` +
1 `/THIRD-EVENT` = 5 binding variants. For each variant the binding readout is the conjunction:

- **median-viable** per cell (one-sided 95% regime-clustered moving-block-bootstrap CI_low > 0, ≥ 30
  qualifying events), **AND**
- **beats its matched-random-on-MA null** (`variant − RM` independent-contrast median CI_low > 0; P5),
  **AND**
- **beats the benchmark MA variant** (`variant − benchmark` paired-median contrast CI_low > 0), **AND**
- clears **P11** (≥ 5 cells over ≥ 3 instruments) **with the P6 non-4h rule** (≥ 3 cells outside 4h).

Binding endpoint = **median** (P3/P14); the **mean** (raw + 10% trimmed + worst-5% tail-share, each
CI'd) is the **P4 diagnostic**. The **censoring fraction** is the binding *cost-side* disclosure (it
grows with horizon and bounds the qualifying denominator). The benchmark MA arm must **reconcile to
EXP-061 `M0` / EXP-060B `BENCH-MA`** to float tolerance (P12). A reconciliation/causality/determinism/
invariant failure is a **SUBSTRATE/METHOD_DEFECT** fixed before interpretation.

## Methodology

A **parameterised re-instrumentation of the frozen EXP-061 / EXP-060B pipeline composed with EXP-058's
`xen.third_barrier`** (the `/THIRD-TIME` floor re-call and the causal next-`rd`-confirm `/THIRD-EVENT`
locator), not new algorithms. The locator is pointed at **MA segments** (the EXP-058 MA-seg-baseline path
already implements this); `/THIRD-TIME` caps come from re-calling `adaptive_time_caps_by_epoch(floor=F)`
on MA-segment durations. New computations: (a) the per-variant matched-random-on-MA call (RM per variant),
(b) the trimmed-mean / tail-share statistic.

### Step 1 — Per-cell median expectancy + bootstrap CI (binding viability)

- **Method**: per-cell **median** of the per-event gross ATR-normalised return, **regime-clustered
  moving-block bootstrap** CI (`b = round(m^(1/3))`, `N_BOOT = 10_000`, one-sided 95% + two-sided), via
  `xen.expectancy.bootstrap_median_distribution` + `median_ci`. **Fixed per-cell-per-variant seed** (P3).
- **Why this method**: fat-tailed, serially dependent per-event returns; median is robust and is the
  binding programme endpoint (P14); block bootstrap respects within-regime dependence without a
  distributional assumption (methods-catalog bootstrap preference, ≥10,000 resamples).
- **Simpler alternative considered**: i.i.d. bootstrap or sign test — rejected (understates CI under
  dependence; discards magnitude). Block bootstrap is the inherited frozen choice.
- **Assumptions**: within-block exchangeability of regime-clustered events; non-parametric. Fits
  time-ordered financial data.
- **Expected output**: per cell × variant × {`/STRONG-STAT` binding, `/STRONG-HA` disclosed} — `median`,
  `ci_low_1s`, `ci_lo_2s`, `ci_hi_2s`, `m`, `median_viable`.

### Step 2 — Per-cell mean + 10% trimmed mean + worst-5% tail-share (P4 diagnostic, disclosed)

- **Method**: the **same** block bootstrap (dedicated RNG streams; median path untouched) on (a) the raw
  mean (`bootstrap_mean_distribution`), (b) the 10% symmetric trimmed mean, (c) the worst-5% tail-share
  (descriptive scalar, no CI). Each of (a)/(b) gets a bootstrap CI.
- **Why this method**: the P4 mandate — separate outlier-driven from structural negativity. Horizon
  extension changes the TIMECAP exit price and thus the tail; this step shows whether a longer hold
  thins or fattens the adverse tail. Disclosed, never a gate.
- **Simpler alternative considered**: raw mean only (EXP-058) — rejected, cannot distinguish tail from
  structural negativity (the P4 mandate).
- **Assumptions**: as Step 1; the mean's wider CI is the measurement, not a defect.
- **Expected output**: per cell × variant (binding arm) — `mean`, `mean_ci_*`, `trimmed_mean_10pct`,
  `trimmed_mean_ci_*`, `tail_share_worst5pct`. Never sets viability.

### Step 3 — Signal-vs-null contrast `variant − RM` (binding, P5) and lever contrast `variant − benchmark` (binding)

- **Method (3a, signal attribution):** independence-assuming `xen.expectancy.contrast_ci` on the stored
  bootstrap distributions of the variant signal arm and its **matched-random-on-MA** arm (RM, EXP-060B
  selection reused, matched-count). Disjoint event pools → independence is correct. `beats_rm` =
  (`variant − RM` median CI_low_1s > 0).
- **Method (3b, lever):** **paired** `xen.favourable_targets.paired_median_contrast_ci` on the **common
  qualifying-event subset** of the variant and the benchmark MA arm — both indexed over the same
  conditioned haramis, differing only in third-barrier window length, so paired is correct and tighter
  (a longer cap is the *same* event measured to a later exit). `beats_bench` = (`variant − benchmark`
  paired median CI_low_1s > 0).
- **Why these methods**: P5 signal attribution needs the RM null beaten, not just zero; the lever
  question compares two horizons on the same events (paired). Inherited EXP-058 + Phase-015-P5 design.
- **Simpler alternative considered**: pooled Mann-Whitney variant-vs-benchmark — rejected (ignores
  pairing and the RM attribution leg).
- **Assumptions**: 3a — independent bootstrap distributions (disjoint pools); 3b — common-subset pairing
  well-defined. Note the common subset shrinks as the longer-horizon variant censors more events — the
  paired contrast is computed on the events both variants resolve, and the differential censoring is
  reported alongside (the cost-side disclosure). `NaN` bounds when power-limited (handled).
- **Expected output**: per cell × variant — `var_rm_median_low_1s`, `var_rm_mean_low_1s`,
  `var_bench_paired_low_1s`, `beats_rm`, `beats_bench`, the composite `variant_wins`
  (`median_viable ∧ beats_rm ∧ beats_bench`), and the per-variant **censoring fraction** + `/THIRD-EVENT`
  event-vs-backstop split.

### Composition (mechanical, predeclared)

- Per-cell first; **P11** = ≥ 5 cells over ≥ 3 instruments on `variant_wins`, **with the P6 non-4h rule**
  (≥ 3 qualifying cells outside 4h). Reported per variant; secondary P11 tallies for `median_viable`,
  `beats_rm`, `beats_bench`. `fragile` flag at the quorum boundary.
- **Censoring is reported with every composition tally** — a variant that "wins" only by censoring its
  losers is flagged (its qualifying count and censoring fraction shown beside its win count).
- **Disclosed substrate contrast:** the benchmark MA arm vs the ZigZag-substrate benchmark (reconciling
  to EXP-058 benchmark) — does the longer MA segment change the third-barrier picture vs EXP-058's
  no-variant-cleared ZigZag result?

## Visualisations (5 / 5 budget)

1. **Per-variant median-expectancy forest vs benchmark** (headline) — per cell, each variant's median CI
   vs benchmark, sorted, coloured by `variant_wins`. Answers: does any longer horizon beat benchmark cell
   by cell and survive RM?
2. **Variant−benchmark and variant−RM contrast heatmap** (variants × cells) — two-panel; non-4h marked.
   Answers: where does horizon extension bite, and is it signal-attributable?
3. **Expectancy distribution by variant (pooled)** — violin/box of per-event returns by variant. Answers:
   how does a longer hold reshape the distribution (esp. the adverse tail)?
4. **P11 (non-4h) composition / wins map** across variants. Answers: which variant (if any) clears the
   binding quorum, and is it carried by 4h cells (P6)?
5. **Censoring + TIMECAP composition by variant** (the horizon-vs-power trade-off) — per-variant censoring
   fraction, TIMECAP fraction, `/THIRD-EVENT` event-vs-backstop split, beside per-cell qualifying counts;
   median-vs-mean P4 preview overlaid for benchmark + best variant. Answers: at what censoring cost does
   any horizon gain come, and is any negative mean removable-tail-driven?

Secondary tables (`per_cell_expectancy`, `third_barrier_map`, `secondary_map`, `reconciliation`) to CSV.

## Interpretation Guide (predeclared; mirrors `scope.md` Success/Failure)

- **EVIDENCE_FOR (a third-barrier lever helps on MA)** — ≥1 alternative variant median-viable **AND**
  beats RM-on-MA **AND** beats benchmark, composed by P11 with the non-4h rule. The winning variant +
  margins + its censoring cost feed EXP-067 / G-015.
- **EVIDENCE_AGAINST (third-barrier geometry is not an MA lever)** — no alternative variant clears the
  combined (`median_viable ∧ beats_rm ∧ beats_bench`) P11 quorum. As on ZigZag (EXP-058), horizon is not
  the lever. **Family stays OPEN** — the surface runs regardless (P9).
- **INCONCLUSIVE (power-limited)** — fewer than the P11 quorum reach ≥30 qualifying events on the variants
  of interest, censoring/warmup exclusions depleting counts (the expected failure mode of the longest
  horizons), no correctness failure. Disclosed; never the default.
- **SUBSTRATE/METHOD_DEFECT** — checks: (i) benchmark variant reproduces EXP-061 `M0` / EXP-060B
  `BENCH-MA` per-cell median + count to `RECON_TOL = 1e-9`; (ii) `/THIRD-TIME` per-event cap monotone
  non-decreasing in floor (`N_BENCH ≤ N_T12 ≤ N_T24 ≤ N_T48`); (iii) `/THIRD-EVENT` per-event cap
  `1 ≤ n_event_evt ≤ 8 × bench_N` and any bound `rd` MA-segment confirm has `ConfirmTime > entry`;
  (iv) population reconciliation vs EXP-053 exact; (v) matched-count holds (RM count = variant signal-arm
  count); (vi) every exit price a real-bar P15 fill with `CloseTime ≤ train_end_ts`. Fix before reporting.

Deliverable label: **MA_THIRD_BARRIER_CHARACTERISED**. No phase closure, no candidate registration, no
gate adjudication here (single terminal G-015 after the full slate).

## Implementation Safety Constraints (for `experiment-developer`)

- **Holdout fence (binding).** TRAIN = first 70% of the first-70% analysis set, file-order prefix (F01);
  `analysis_rows = int(total*0.7)`, `train_rows = int(analysis_rows*0.7)`; collect only the first
  `train_rows` rows via `.slice(0, train_rows)`. **Never** sort/collect the full file; **never** read
  TEST/holdout. Assert chronological; `train_end_ts` = last `CloseTime`. Reuse EXP-061's `load_train_1m`.
  **Longer horizons and the `/THIRD-EVENT` backstop are clipped to `train_end_ts`** — a window that would
  extend past it is `DATA_CENSORED`, never resolved against TEST/holdout rows.
- **Temporal ordering & alignment.** Order by `CloseTime`; align HA/ZigZag/MA events to real bars by
  exact `CloseTime`-epoch match, never by bar index. Domain aggregation: 5m strict, others
  `min_coverage=0.90`; fence every bar to `CloseTime ≤ train_end_ts`.
- **Causality / no look-ahead.** MA(20,50) `_sma` trailing only; MA segments bounded by crossovers
  confirmed before entry; `M_sofar`, benchmark fav/adv, and the `/THIRD-TIME` caps use only MA segments
  confirmed strictly before entry. The `/THIRD-EVENT` exit uses the **next** MA segment confirmed with
  `ConfirmTime > entry` (forward-known, acted on at the confirmation bar) — never the retroactive
  crossover, never an unconfirmed one. Matched-random-on-MA entries causal with the identical
  pre-entry-only state. Forward scan reads only `[entry_idx+1, min(entry_idx+n_event, last_train_idx)]`.
  Keep EXP-061's `_causality_ok` gate.
- **Real-price discipline.** Detection on HA candles only; every outcome metric (returns, M_sofar, levels,
  all caps, fills, ATR-normalisation) on real OHLC; MA(20,50) on real close. No HA price in any metric.
- **Denominators / zero-baseline.** Per-event return defined only for **qualifying** events (built-window
  FAV/ADV/TIMECAP, finite positive `ATR_entry`, finite P15 fill in the TRAIN-fenced window).
  `DATA_CENSORED` + warmup-excluded events **excluded** from median/mean/trim and **disclosed as counts**
  per cell per variant; the censoring fraction is reported prominently. A cell with **< 30 qualifying
  events** on a variant is `NOT_VIABLE-by-power` — never an undefined/infinite ratio. Worst-5% tail-share
  with 0 negative mass → 0.0 (finite). First-hit `r` = `n_FAV/(n_FAV+n_ADV)`, TIMECAP excluded
  (EXP-049 convention), disclosed; expected ≈0.50 (fav/adv held at MA benchmark) — never binding.
- **Determinism (P12).** Fixed per-cell-per-variant seed; second full pass (or per-instrument first-cell
  replay) asserting byte-identical returns, medians, CIs, RM returns, contrasts, and per-event caps.
  Byte-identical output across worker counts.
- **Vectorization discipline.** Reuse EXP-058/EXP-061 vectorized resolvers and the `third_event_caps`
  forward-locator verbatim (pointed at MA segments); do not rewrite the sequential causal state
  construction. New code paths: `/THIRD-TIME` floor re-calls on MA-segment durations, the per-variant RM
  call (**new dedicated RNG purpose offsets**), the trimmed-mean/tail-share statistic.
- **Performance / parallelism.** Keep EXP-061's per-instrument `ProcessPoolExecutor` with native-thread
  pinning and fixed-order reassembly; byte-identical output for any `--workers`; never alter sample
  membership, ordering, denominators, metric definitions, seeds, or causal/streaming semantics.
- **Reconciliation source.** Load EXP-061's `per_cell_expectancy.parquet` (`BENCH-MA` M0 per-cell median +
  count) as the P12 anchor; EXP-060B available upstream; EXP-058's MA-seg baseline arms a *secondary
  cross-check* (disclosed; may differ if the MA construction differs from `ma_seg_arm` — note, do not
  treat as a defect). Reconciliation absent/zero checked cells ⇒ SUBSTRATE/METHOD_DEFECT.
- **Bounded memory / progress.** `tqdm` over the 99-cell grid; per-event forward scans bounded by the cap
  (`/THIRD-EVENT` by `8 × bench_N`); per-cell arrays released after summarisation. Plots from collected
  per-cell summaries only — no reloads.
- **Outputs (`results/`).** `per_cell_expectancy.parquet`, `third_barrier_map.csv` (binding summary + P11
  non-4h tally), `secondary_map.csv` (`/STRONG-HA`, ZigZag benchmark contrast, `r`, censoring),
  `reconciliation.csv` (benchmark MA arm ↔ EXP-061 M0 / EXP-060B BENCH-MA; population vs EXP-053),
  `composition_readout.json` (per-variant P11 non-4h, wins, censoring summary, EVIDENCE_* → G-015 input),
  `run_metadata.json` (seed, frozen + new constants, EXP-058/060/060B/061 source paths/hashes, holdout
  fence). Output dirs created only in orchestration.

## Complexity Check

- **Statistical methods: 4 / 4** — (1) median moving-block bootstrap CI (binding); (2) mean + 10% trimmed
  mean bootstrap CI + worst-5% tail-share (P4); (3) `variant − RM` independent contrast (P5); (4)
  `variant − benchmark` paired-median contrast (lever). A re-instrumentation of EXP-058 + EXP-061.
- **Visualisations: 5 / 5** — per-variant forest; variant−benchmark/−RM contrast heatmap; expectancy
  distribution by variant; P11 (non-4h) wins map; censoring + TIMECAP composition (with median-vs-mean P4
  overlay).
- **New modules: 0 / ≤1** — reuses `xen.third_barrier` (MA-segment locator), `xen.expectancy`,
  `xen.favourable_targets`, and the EXP-060/061 MA pipeline; additions are MA-segment-duration floor
  re-calls, the per-variant RM call, and the trimmed-mean/tail-share statistic. At most one thin
  orchestration wrapper under `code/`; **no new `xen/` analysis module**.

Plan fits the scope's complexity budget exactly.
