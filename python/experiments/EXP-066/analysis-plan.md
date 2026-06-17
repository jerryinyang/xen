# Analysis Plan: Experiment EXP-066

**MA(20,50)-Substrate Position-Management Exits (Hybrid Conditioned HA Harami; `/EXIT-PARTIAL`, `/EXIT-TRAIL-STRUCT`, individually and combined)**
Phase 015 surface **S3** · `CF-HA-HARAMI-001/HYP-019` · forks EXP-061 + composes EXP-059 `xen.position_exits` on MA-substrate levels.

> **Mandatory-reading precondition honoured.** `014-A-conditioning-gap-and-validation-lessons.md`
> was read in full (recorded in `scope.md`); this plan keeps the conditioning / harami-anchor /
> descriptive-position / median-endpoint rules. The matched-random-on-MA controls are deliberate
> **nulls** (binding per P5); every outcome metric is on real prices; no position-in-move metric is
> used. The binding endpoint is the **position-weighted** per-event return — the metric P14 chose
> precisely because partial exits and trailing stops cannot express value under a first-hit rate.

## Objective

Decide, on the 99-cell TRAIN grid, whether **changing only the position-management exit machinery** of
the hybrid `/STRONG`-conditioned HA harami **on the MA(20,50) substrate** — favourable-side scaled exits
(`/EXIT-PARTIAL` V1/V2A/V2B/V2C), adverse-side structure trailing (`/EXIT-TRAIL-STRUCT` PURE/TP-INIT/
TP-NOINIT), or their combination (COMBINED-V1/V2A/V2B/V2C) — improves gross per-event **median**
expectancy over the MA benchmark single fixed exit, whether any improvement is **signal-attributable**
(beats its matched-random-on-MA null), and — decisively for EXP-067 / G-015 — whether any scheme also
moves the **mean** toward positive. The 12-arm set is the EXP-059 grid reused unchanged on MA (D0 P8;
the one substrate-forced substitution is the reversal-event leg → next confirmed MA segment in direction
`rd`; the trailing structure stays the secondary 0.5 ZigZag per the EXP-059 baseline convention). For
each arm the binding readout is the conjunction:

- **median-viable** per cell (one-sided 95% regime-clustered moving-block-bootstrap CI_low > 0, ≥ 30
  qualifying events), **AND**
- **beats its matched-random-on-MA null** (`arm − RM` independent-contrast median CI_low > 0; P5), **AND**
- **beats the benchmark MA arm** (`arm − benchmark` paired-median contrast CI_low > 0), **AND**
- clears **P11** (≥ 5 cells over ≥ 3 instruments) **with the P6 non-4h rule** (≥ 3 cells outside 4h).

Binding endpoint = **median** position-weighted per-event return (P3/P14); the **mean** (raw + 10%
trimmed + worst-5% tail-share, each CI'd) is the **P4 diagnostic co-primary** — reported as a decisive
input to EXP-067 / G-015 (does any scheme lift the mean?), but the EVIDENCE_FOR fork stays
median-binding. The BENCH arm must **reconcile to EXP-061 `M0` / EXP-060B `BENCH-MA`** to float tolerance
(P12). A reconciliation/causality/determinism/invariant failure is a **SUBSTRATE/METHOD_DEFECT** fixed
before interpretation.

## Methodology

A **parameterised re-instrumentation of the frozen EXP-061 / EXP-060B pipeline composed with EXP-059's
`xen.position_exits`** (multi-leg P15 partial-exit resolver + structure trailing-stop builder/resolver),
not new algorithms. The resolvers are fed the **MA-substrate** fav/adv levels and MA adaptive cap; the
reversal-event leg uses the EXP-058/065 `third_event_caps` forward-locator **pointed at MA segments**;
the trailing stop uses the secondary 0.5 ZigZag (real-bar construct, unchanged). The per-event value
construction (position-weighted `R_event`) changes; the four contrast/bootstrap methods are the same as
EXP-056/058/059/064/065. New computations: (a) the per-arm matched-random-on-MA call (RM per arm),
(b) the trimmed-mean / tail-share statistic.

### Step 1 — Per-cell median expectancy + bootstrap CI on the position-weighted `R_event` (binding viability)

- **Method**: per-cell **median** of the **position-weighted** per-event gross ATR-normalised return
  `R_event = Σ_l w_l · rd·(exit_px_l − C)/ATR_entry` (`Σ w_l = 1`), with a **regime-clustered
  moving-block bootstrap** CI (`b = round(m^(1/3))`, `N_BOOT = 10_000`, one-sided 95% + two-sided), via
  `xen.expectancy.bootstrap_median_distribution` + `median_ci`. **Fixed per-cell-per-arm seed** (P3).
- **Why this method**: multi-leg exits collapse to one per-event number (`R_event`); the per-event
  distribution is fat-tailed and serially dependent; the median is robust and the binding programme
  endpoint (P14, chosen for exactly this lever); block bootstrap respects within-regime dependence
  non-parametrically (methods-catalog bootstrap preference, ≥10,000 resamples).
- **Simpler alternative considered**: first-hit `r` or i.i.d. bootstrap. Rejected — first-hit `r` cannot
  express partial/trailing exits (the P14 rationale; this is the experiment the lever was built for);
  i.i.d. resampling understates the CI under dependence. Block bootstrap on `R_event` is the inherited
  frozen choice.
- **Assumptions**: within-block exchangeability of regime-clustered events; non-parametric. Fits
  time-ordered financial data.
- **Expected output**: per cell × arm × {`/STRONG-STAT` binding, `/STRONG-HA` disclosed} — `median`,
  `ci_low_1s`, `ci_lo_2s`, `ci_hi_2s`, `m`, `median_viable`.

### Step 2 — Per-cell mean + 10% trimmed mean + worst-5% tail-share (P4 diagnostic; decisive for EXP-067/G-015)

- **Method**: the **same** block bootstrap (dedicated RNG streams; median path untouched) on (a) the raw
  mean of `R_event` (`bootstrap_mean_distribution`), (b) the 10% symmetric trimmed mean, (c) the worst-5%
  tail-share (descriptive scalar). Each of (a)/(b) gets a bootstrap CI.
- **Why this method**: EXP-060B's champion was V2A × `/ADV-NONE`, median-positive / mean≈0 with an
  uncapped-downside skew gap of 1.20 ATR. The P4 mandate is to learn whether position-management exits —
  especially the partial favourable scaling (V2A) and the structure trailing stop (which *bounds the
  downside*, the skew source) — move the **mean** toward positive, and whether any residual negativity is
  removable-tail-driven (trimmed mean crosses positive; thin tail-share) or structural. This is the most
  decisive mean read of the surface; reported prominently, but never a viability gate (P4 closure rule).
- **Simpler alternative considered**: raw mean only (EXP-059) — rejected, cannot distinguish tail from
  structural negativity (the P4 mandate, and the explicit reason Phase 015 exists).
- **Assumptions**: as Step 1; the mean's wider CI is the measurement.
- **Expected output**: per cell × arm (binding arm) — `mean`, `mean_ci_*`, `trimmed_mean_10pct`,
  `trimmed_mean_ci_*`, `tail_share_worst5pct`, plus a per-arm mean-diagnostic summary for the G-015 input.

### Step 3 — Signal-vs-null contrast `arm − RM` (binding, P5) and lever contrast `arm − benchmark` (binding)

- **Method (3a, signal attribution):** independence-assuming `xen.expectancy.contrast_ci` on the stored
  bootstrap distributions of the arm signal population and its **matched-random-on-MA** arm (RM, EXP-060B
  selection reused, matched-count). Disjoint event pools → independence correct. `beats_rm` =
  (`arm − RM` median CI_low_1s > 0).
- **Method (3b, lever):** **paired** `xen.favourable_targets.paired_median_contrast_ci` on the **common
  qualifying-event subset** of the arm and the BENCH arm — both indexed over the same conditioned
  haramis, differing only in exit machinery, so paired is correct and tighter. `beats_bench` =
  (`arm − benchmark` paired median CI_low_1s > 0).
- **Why these methods**: P5 signal attribution needs the RM null beaten; the lever question compares two
  exit schemes on the same events (paired). Inherited EXP-059 + Phase-015-P5 design.
- **Simpler alternative considered**: pooled Mann-Whitney arm-vs-benchmark — rejected (ignores pairing and
  the RM attribution leg).
- **Assumptions**: 3a — independent bootstrap distributions (disjoint pools); 3b — common-subset pairing
  well-defined (both arms qualify the event; trailing arms additionally require secondary-ZigZag history,
  so the paired subset excludes trailing-warmup events for those arms, disclosed). `NaN` bounds when
  power-limited (handled).
- **Expected output**: per cell × arm — `arm_rm_median_low_1s`, `arm_rm_mean_low_1s`,
  `arm_bench_paired_low_1s`, `beats_rm`, `beats_bench`, the composite `arm_wins`
  (`median_viable ∧ beats_rm ∧ beats_bench`), and the per-arm **exit-reason composition** (fraction of
  weight via each leg trigger / shared stop / trailing stop / time cap).

### Composition (mechanical, predeclared)

- Per-cell first; **P11** = ≥ 5 cells over ≥ 3 instruments on `arm_wins`, **with the P6 non-4h rule**
  (≥ 3 qualifying cells outside 4h). Reported per arm; secondary P11 tallies for `median_viable`,
  `beats_rm`, `beats_bench`, and (disclosed) `mean_viable` (raw-mean CI_low>0 — the G-015 mean signal,
  never the gate). `fragile` flag at the quorum boundary.
- **Disclosed substrate contrast:** each arm vs the ZigZag-substrate arm (reconciling to EXP-059) — does
  the MA substrate reproduce EXP-059's `/EXIT-PARTIAL` V2A EVIDENCE_FOR, or change it?

## Visualisations (5 / 5 budget)

1. **Per-arm median-expectancy forest vs benchmark** (headline) — per cell, each arm's median CI vs
   BENCH, sorted, coloured by `arm_wins`. Answers: does any exit scheme beat benchmark cell by cell and
   survive RM?
2. **Arm−benchmark and arm−RM contrast heatmap** (arms × cells) — two-panel; non-4h marked. Answers:
   where does each scheme bite, and is it signal-attributable?
3. **Expectancy distribution by arm (pooled)** — violin/box of `R_event` by arm. Answers: how does each
   scheme reshape the distribution (esp. whether trailing/partial thins the adverse tail)?
4. **P11 (non-4h) composition / wins map** across arms — `arm_wins`, `median_viable`, `beats_rm`,
   `beats_bench`, and (disclosed) `mean_viable`; quorum line. Answers: which arm clears the binding
   quorum, is it 4h-carried (P6), and does any arm also clear the mean?
5. **Exit-reason composition by arm + median-vs-mean P4 preview** — per-arm fraction of weight via each
   exit reason (the mechanism diagnostic), beside per-cell qualifying counts, with the median vs raw mean
   vs 10% trimmed mean + worst-5% tail-share for the best arms. Answers: how does the winning scheme
   realise P&L, and does it move the mean toward positive (the decisive EXP-067/G-015 read)?

Secondary tables (`per_cell_expectancy`, `position_mgmt_map`, `secondary_map`, `reconciliation`) to CSV.

## Interpretation Guide (predeclared; mirrors `scope.md` Success/Failure)

- **EVIDENCE_FOR (a position-management scheme helps on MA)** — ≥1 arm median-viable **AND** beats
  RM-on-MA **AND** beats benchmark, composed by P11 with the non-4h rule. The winning arm + margins +
  its P4 mean diagnostic feed EXP-067 / G-015. (A scheme that is median-viable *and* raw-mean-positive is
  the strongest possible surface input to a G-015 PROCEED, but the EVIDENCE_FOR label itself is
  median-binding.)
- **EVIDENCE_AGAINST (position management is not an MA lever)** — no arm clears the combined
  (`median_viable ∧ beats_rm ∧ beats_bench`) P11 quorum. **Family stays OPEN** — the surface runs
  regardless (P9).
- **INCONCLUSIVE (power-limited)** — fewer than the P11 quorum reach ≥30 qualifying events on the arms of
  interest (scaling/trailing construction + warmup exclusions deplete counts), no correctness failure.
  Disclosed; never the default.
- **SUBSTRATE/METHOD_DEFECT** — checks: (i) BENCH arm reproduces EXP-061 `M0` / EXP-060B `BENCH-MA`
  per-cell median + count to `RECON_TOL = 1e-9`; (ii) population reconciliation vs EXP-053 exact;
  (iii) leg weights sum to 1.0 for every arm, and a degenerate single-trigger arm reproduces the
  equivalent single-leg `R_event` to float precision; (iv) the trailing stop is monotone (never loosens)
  and changes level only on secondary-ZigZag confirmation bars (`ConfirmTime ≤ CloseTime`); (v) every exit
  price a real-bar P15 fill with `CloseTime ≤ train_end_ts`; (vi) the shared adverse/trailing stop, when
  it binds, closes all still-open legs at the same bar/level; (vii) matched-count holds (RM count = arm
  signal-arm count). Fix before reporting.

Deliverable label: **MA_POSITION_MGMT_CHARACTERISED**. No phase closure, no candidate registration, no
gate adjudication here (single terminal G-015 after the full slate; this read's survivors feed EXP-067).

## Implementation Safety Constraints (for `experiment-developer`)

- **Holdout fence (binding).** TRAIN = first 70% of the first-70% analysis set, file-order prefix (F01);
  `analysis_rows = int(total*0.7)`, `train_rows = int(analysis_rows*0.7)`; collect only the first
  `train_rows` rows via `.slice(0, train_rows)`. **Never** sort/collect the full file; **never** read
  TEST/holdout. Assert chronological; `train_end_ts` = last `CloseTime`. Reuse EXP-061's `load_train_1m`.
  All forward windows (legs, reversal events, trailing ratchet, caps) clipped to `train_end_ts`; an
  unresolved truncated window is `DATA_CENSORED`, never resolved against TEST/holdout rows.
- **Temporal ordering & alignment.** Order by `CloseTime`; align primary ZigZag, secondary ZigZag, MA
  segments, HA candles, and real bars by exact `CloseTime`-epoch match, never by bar index. Domain
  aggregation: 5m strict, others `min_coverage=0.90`; fence every bar to `CloseTime ≤ train_end_ts`.
- **Causality / no look-ahead.** MA(20,50) `_sma` trailing only; MA segments bounded by crossovers
  confirmed before entry; `M_sofar`, the benchmark fav/adv levels, the leg targets, and the MA benchmark
  cap use only MA segments confirmed strictly before entry. Every exit is a forward event: first-profit
  close (bar close), fractional-target touch (intrabar P15), reversal event (next confirmed MA segment
  `Direction==rd` or opposing-harami confirm — at the confirmation bar's close, never an unconfirmed
  crossover/pivot), and the structure trailing stop (the stop in force at bar `t` uses only
  secondary-ZigZag moves with `ConfirmTime ≤ CloseTime(t)` — moves at the confirmation bar, never the
  retroactive pivot). The trailing ratchet is monotone (never loosens). Matched-random-on-MA entries
  causal with the identical pre-entry-only state. Forward scan reads only `[entry_idx+1,
  min(entry_idx+bench_N, last_train_idx)]`. Keep EXP-061's `_causality_ok` gate.
- **Real-price discipline.** Detection on HA candles only; every outcome metric (returns, M_sofar, all
  levels/legs/stops, the secondary trailing ZigZag, fills, weighted expectancy, exit-reason composition)
  on real OHLC; MA(20,50) on real close. The opposing-harami reversal arm uses HA candles only to *locate*
  the exit bar, then exits at that bar's **real** close. No HA price in any metric.
- **Denominators / zero-baseline.** Per-event `R_event` defined only for **qualifying** events (barriers/
  legs constructible — `fav_dist > 0`, finite positive `ATR_entry`, secondary ZigZag available for
  trailing arms — and every leg / the position reaching a finite P15 exit in the TRAIN-fenced window).
  `DATA_CENSORED` + construction/warmup-excluded events **excluded** from median/mean/trim and **disclosed
  as counts** per cell per arm. A cell with **< 30 qualifying events** on an arm is `NOT_VIABLE-by-power`
  — never an undefined/infinite ratio. Worst-5% tail-share with 0 negative mass → 0.0 (finite). First-hit
  `r` defined only for the single-leg BENCH arm (`n_FAV/(n_FAV+n_ADV)`, TIMECAP excluded), disclosed;
  undefined (not reported as viability) for multi-leg/trailing arms — the P14 rationale.
- **Determinism (P12).** Fixed per-cell-per-arm seed; second full pass (or per-instrument first-cell
  replay) asserting byte-identical `R_event`, medians, CIs, RM returns, contrasts, and exit-reason
  composition. Byte-identical output across worker counts.
- **Vectorization discipline.** Reuse EXP-059's `position_exits` multi-leg + trailing resolvers and the
  `third_event_caps` forward-locator verbatim (the latter pointed at MA segments); do not rewrite the
  sequential causal state construction (the trailing-stop step function and the per-leg P15 assignment are
  genuinely sequential — keep them explicit and bounded). New code paths: feeding MA-substrate levels into
  the resolvers, the per-arm RM call (**new dedicated RNG purpose offsets**), the trimmed-mean/tail-share
  statistic.
- **Performance / parallelism.** Keep EXP-061's per-instrument `ProcessPoolExecutor` with native-thread
  pinning and fixed-order reassembly; byte-identical output for any `--workers`; never alter sample
  membership, ordering, denominators, metric definitions, seeds, or causal/streaming semantics.
- **Reconciliation source.** Load EXP-061's `per_cell_expectancy.parquet` (`BENCH-MA` M0 per-cell median +
  count) as the P12 anchor; EXP-060B available upstream; EXP-059's MA-seg baseline arms a *secondary
  cross-check* (disclosed; may differ if the MA construction differs from `ma_seg_arm` — note, do not treat
  as a defect). Reconciliation absent/zero checked cells ⇒ SUBSTRATE/METHOD_DEFECT.
- **Bounded memory / progress.** `tqdm` over the 99-cell grid; per-event forward scans bounded by
  `bench_N`; per-cell arrays released after summarisation. Plots from collected per-cell summaries only —
  no reloads.
- **Outputs (`results/`).** `per_cell_expectancy.parquet`, `position_mgmt_map.csv` (binding summary + P11
  non-4h tally), `secondary_map.csv` (`/STRONG-HA`, ZigZag contrast, BENCH `r`, exit-reason composition),
  `reconciliation.csv` (BENCH arm ↔ EXP-061 M0 / EXP-060B BENCH-MA; population vs EXP-053),
  `composition_readout.json` (per-arm P11 non-4h, wins, mean-diagnostic summary, EVIDENCE_* → G-015
  input), `run_metadata.json` (seed, frozen + inherited constants, EXP-059/060/060B/061 source
  paths/hashes, holdout fence). Output dirs created only in orchestration.

## Complexity Check

- **Statistical methods: 4 / 4** — (1) median moving-block bootstrap CI on `R_event` (binding); (2) mean +
  10% trimmed mean bootstrap CI + worst-5% tail-share (P4); (3) `arm − RM` independent contrast (P5);
  (4) `arm − benchmark` paired-median contrast (lever). A re-instrumentation of EXP-059 + EXP-061.
- **Visualisations: 5 / 5** — per-arm forest; arm−benchmark/−RM contrast heatmap; expectancy distribution
  by arm; P11 (non-4h) wins map; exit-reason composition + median-vs-mean P4 preview.
- **New modules: 0 / ≤1** — reuses `xen.position_exits`, `xen.third_barrier` (MA-segment locator),
  `xen.expectancy`, `xen.favourable_targets`, and the EXP-060/061 MA pipeline; additions are MA-substrate
  levels into the resolvers, the per-arm RM call, and the trimmed-mean/tail-share statistic. At most one
  thin orchestration wrapper under `code/`; **no new `xen/` analysis module**.

Plan fits the scope's complexity budget exactly.
