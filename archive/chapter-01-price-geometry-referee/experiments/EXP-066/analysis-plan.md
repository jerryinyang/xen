# Analysis Plan: Experiment EXP-066

**MA(20,50)-Substrate Position-Management Exits (Conditioned HA Harami; `/EXIT-PARTIAL`, `/EXIT-TRAIL-STRUCT`, individually and combined; Dual Conditioning Object: Hybrid and Native)**
Phase 015 surface **S3** · `CF-HA-HARAMI-001/HYP-019` · forks EXP-064's **dual-object** harness; composes EXP-059 `xen.position_exits` on MA-substrate levels and the EXP-058/065 MA-segment reversal-event locator.

> **Re-run under `D0-amendment-001-dual-parallel-substrate.md` (2026-06-17).** The prior EXP-066 plan
> measured the 12-arm position-management exit grid labelled *hybrid* but reconciled its benchmark arm
> to EXP-061 `M0` — the **native** object (MA-segment `/STRONG-STAT`, 8360-class). The genuine
> **hybrid** object (ZigZag-`/STRONG-STAT`-conditioned × MA exit geometry) and the native object were
> not both computed. This plan emits the full 12-arm exit grid **for both objects individually**
> (separate arms, separate matched-random nulls, separate composition, separate EVIDENCE fork — never
> pooled) and corrects the reconciliation roles (native `M-BENCH` ↔ EXP-061 `M0`; hybrid `H-BENCH` ↔
> EXP-061 `H0`). EXP-066 was paused (no `results/`, no code), so resumption is dual-object from the
> start.

> **Mandatory-reading precondition honoured.** `014-A-conditioning-gap-and-validation-lessons.md` was
> read in full (recorded in `scope.md`); this plan keeps the conditioning / harami-anchor /
> descriptive-position / median-endpoint rules. The matched-random-on-MA controls are deliberate
> **nulls** (per object, binding per P5), not signal claims; every outcome metric is on real prices;
> MA(20,50) on real close; no position-in-move metric is used. The binding endpoint is the
> **position-weighted** per-event return — the metric P14 chose precisely because partial exits and
> trailing stops cannot express value under a first-hit rate.

## Objective

Decide, on the 99-cell TRAIN grid and the MA(20,50) substrate, **for each conditioning object individually
(hybrid, native; never pooled)**, whether **changing only the position-management exit machinery** of the
`/STRONG`-conditioned HA harami — favourable-side scaled exits (`/EXIT-PARTIAL` V1/V2A/V2B/V2C),
adverse-side structure trailing (`/EXIT-TRAIL-STRUCT` PURE/TP-INIT/TP-NOINIT), or their combination
(COMBINED-V1/V2A/V2B/V2C) — improves gross per-event **median** expectancy over that object's benchmark
single fixed exit (MA benchmark 50% fav / 1:1 stop / adaptive cap, single leg), whether any improvement is
**signal-attributable** (beats that object's matched-random-on-MA null), and — decisively for EXP-067/EXP-068
/ G-015 — whether any scheme also moves the **mean** toward positive. The 12-arm set is the EXP-059 grid
reused unchanged on MA (D0 P8; the one substrate-forced substitution is the reversal-event leg → next
confirmed MA segment in direction `rd`; the trailing structure stays the secondary 0.5 ZigZag per the EXP-059
baseline convention). For each arm type **of each object** the binding readout is the conjunction:

- the arm is **median-viable** per cell (one-sided 95% regime-clustered moving-block-bootstrap CI_low > 0,
  ≥ 30 qualifying events), **AND**
- the arm **beats its own same-object matched-random-on-MA null** (`arm − RM` independent-contrast median
  CI_low > 0; P5 signal-attribution), **AND**
- the arm **beats that object's benchmark MA arm** (`arm − benchmark` paired-median contrast CI_low > 0), **AND**
- this clears **P11** (≥ 5 cells over ≥ 3 instruments) **with the P6 non-4h rule** (≥ 3 qualifying cells
  outside 4h), **for that object**.

The two conditioning objects (P2):

- **Hybrid (`H-*`)** — `/STRONG-STAT` p75 on the **in-progress confirmed ZigZag move**; mask byte-identical to
  EXP-053/060/061's hybrid `H0` (population reconciles to EXP-053's 3202-class set). **Genuinely-new object**
  for the exit axis; internal-lineage anchor is EXP-061 `H0` (the `H-BENCH` arm reproduces it); no EXP-060B/059
  outcome anchor.
- **Native (`M-*`)** — `/STRONG-STAT` p75 recomputed on the **in-progress confirmed MA segment**; population
  byte-identical to EXP-061 native `M0` / EXP-060B `BENCH-MA` (8360-class); the `M-BENCH` arm reconciles to
  them (1e-9). **This is the object the prior EXP-066 plan actually computed** — V2A × `/ADV-NONE` was the
  EXP-060B champion on this population.

Both objects score on the **same** MA outcome geometry (`rd` / `M_sofar` / favourable target 50% / adverse 1:1
/ MA adaptive cap — all from the shared MA in-progress state); they differ only in *which haramis qualify*.
Binding endpoint = **median** position-weighted per-event gross ATR-normalised return (P3/P14), **per object**.
The **mean** (raw + 10% trimmed + worst-5% tail-share, each CI'd) is the **P4 diagnostic co-primary** —
disclosed, never a viability gate. The phase-level reading of this lever is the **stronger object's** outcome
(per EXP-061, native is the expressing object), with the other documented in parallel.

This is also the position-management exit readiness/reconciliation precondition: **`M-BENCH` (native) must
reproduce EXP-061 `M0` / EXP-060B `BENCH-MA`** and **`H-BENCH` (hybrid) must reproduce EXP-061 `H0`** per-cell
median + qualifying count to `RECON_TOL = 1e-9` (P12). A reconciliation/causality/determinism/invariant failure
is a **SUBSTRATE/METHOD_DEFECT** fixed before any efficacy read is interpreted. **The two objects are never
pooled.**

## Methodology

A **parameterised re-instrumentation** of the frozen EXP-064 dual-object pipeline composed with EXP-059's
`xen.position_exits` (multi-leg P15 partial-exit resolver + structure trailing-stop builder/resolver), not new
algorithms. EXP-064 already provides the dual-object per-variant OAT loop, per-object matched-random nulls, and
the P4 mean/trim/tail bootstrap; the orchestration changes vs EXP-064 are: (a) the per-variant axis becomes the
**12-arm position-management exit grid** (replacing EXP-064's 8-variant favourable-target grid), built by
`xen.position_exits` fed the **MA-substrate** fav/adv levels, the secondary ZigZag for the trailing structure,
and the EXP-058/065 `third_event_caps` locator pointed at **MA segments** for the reversal-event leg; (b) the
binding lever is the **arm − benchmark** paired contrast (EXP-059's question) alongside the **arm − RM** signal
attribution; (c) the **exit-reason composition** (the fraction of position weight exiting via each leg trigger /
shared stop / trailing stop / time cap) is the binding mechanism diagnostic.

The arms per cell: for each object O ∈ {native `M`, hybrid `H`} and each arm type A ∈ {BENCH, PARTIAL-V1,
PARTIAL-V2A, PARTIAL-V2B, PARTIAL-V2C, TRAIL-PURE, TRAIL-TP-INIT, TRAIL-TP-NOINIT, COMBINED-V1,
COMBINED-V2A, COMBINED-V2B, COMBINED-V2C}: the signal arm `{O}-{A}` and its own-object null `R{O}-{A}`
(native nulls `RM-*`, hybrid nulls `RH-*`). Native arms condition on `ma["stat"]["retained_p75"]`; hybrid arms
condition on `zz["stat"]["retained_p75"]` (the same mask EXP-061 used for `H0`, applied through the MA
context). **The two objects are reported individually; no arm sums or averages across objects.**

### Step 1 — Per-cell median expectancy + bootstrap CI on the position-weighted `R_event`, per arm **per object** (binding viability)

- **Method**: per-cell **median** of the **position-weighted** per-event gross ATR-normalised return
  `R_event = Σ_l w_l · rd·(exit_px_l − C)/ATR_entry` (`Σ w_l = 1`), with a **regime-clustered
  moving-block bootstrap** CI (`b = max(1, round(m^(1/3)))`, `N_BOOT = 10_000`, one-sided 95% lower bound +
  two-sided bounds), via `xen.expectancy.bootstrap_median_distribution` + `median_ci`. Computed for each of
  the 12 arm types on **each** object's binding `/STRONG-STAT` signal arm (24 signal arms per cell).
  **Fixed per-cell seed** (`(BASE_SEED, cell_index, purpose)`, P3) with a **distinct purpose per
  object/arm/statistic**, so the **`M-BENCH` median path stays byte-identical to EXP-061 `M0`** and the
  **`H-BENCH` median path stays byte-identical to EXP-061 `H0`** (the two reconciliation anchors).
- **Why this method**: multi-leg exits collapse to one per-event number (`R_event`); the per-event
  distribution is fat-tailed and serially dependent within a regime; the median is robust to the left tail
  and is the binding programme endpoint (P14). The moving-block bootstrap respects within-regime serial
  dependence without assuming a distribution (methods-catalog: bootstrap CI preferred; ≥ 10,000 resamples;
  inherited, programme-frozen). P14 chose this metric precisely for partial-exit and trailing-stop arms whose
  value cannot be expressed under a first-hit rate.
- **Simpler alternative considered**: first-hit `r` or i.i.d. bootstrap. Rejected — first-hit `r` cannot
  express partial/trailing exits (the P14 rationale, this experiment's raison d'être); i.i.d. resampling
  understates the CI under serial dependence.
- **Assumptions**: within-block exchangeability of regime-clustered events; non-parametric. Fits
  time-ordered financial data.
- **Expected output**: per cell × object × arm × {`/STRONG-STAT` binding} — `median`, `ci_low_1s`,
  `ci_lo_2s`, `ci_hi_2s`, `m` (qualifying count), `median_viable` flag (CI_low>0 ∧ m≥30).

### Step 2 — Per-cell mean + 10% trimmed mean + worst-5% tail-share, per arm **per object** (P4 diagnostic; decisive for EXP-067/EXP-068/G-015)

- **Method**: the **same** moving-block bootstrap (byte-identical block construction; **dedicated RNG
  streams** so the median path is untouched) applied to (a) the **raw mean** and (b) the **10% symmetric
  trimmed mean** via `bootstrap_stat_distribution(values, rng, "mean"|"trim")` + `median_ci` for percentile
  bounds; plus (c) the **worst-5% tail-share** = fraction of total negative return contributed by the worst
  5% of events (`_tail_share_worst5`; descriptive scalar, no CI). Computed per arm **per object**. The trim
  fraction **10%** and tail fraction **worst-5%** are D0-ratified (P4), frozen.
- **Why this method**: EXP-060B's champion was V2A × `/ADV-NONE`, median-positive / mean≈0 with an
  uncapped-downside skew gap of 1.20 ATR. The P4 mandate is to learn whether position-management exits —
  especially the partial favourable scaling (V2A) and the structure trailing stop (which *bounds the
  downside*, the skew source) — move the **mean** toward positive **for each object**, and whether any
  residual negativity is removable-tail-driven (trimmed mean crosses positive; thin tail-share) or structural.
  This is the most decisive mean read of the surface. Disclosed per arm per object, reported prominently;
  never a viability gate (P4 closure rule).
- **Simpler alternative considered**: raw mean only (as EXP-059). Rejected — the raw mean alone cannot
  distinguish removable-tail from structural negativity, the entire P4 mandate.
- **Assumptions**: same as Step 1; the mean/trimmed mean are tail-sensitive so their CIs are wider — that
  width is the measurement.
- **Expected output**: per cell × object × arm (binding arm) — `mean`, `mean_ci_*`, `trimmed_mean_10pct`,
  `trimmed_mean_ci_*`, `tail_share_worst5pct`, a disclosed `mean_viable` flag (never gates viability).

### Step 3 — Per-arm signal-vs-null contrast `arm − RM-on-MA`, **per object** (binding signal attribution, P5)

- **Method (3a, signal attribution):** for each arm type **of each object** build a **matched-count
  random-in-regime** control (native: `RM-BENCH / RM-PARTIAL-V1 / ... / RM-COMBINED-V2C`; hybrid: `RH-BENCH /
  RH-PARTIAL-V1 / ... / RH-COMBINED-V2C`) via the EXP-061 `matched_random_arm` run through that arm's
  **identical exit pipeline** on MA. Eligible pool = valid live MA state, `m_sofar > 0`, finite positive ATR,
  not-in-warmup, **excluding that object's conditioned-harami entries**; matched-count to **that object's**
  arm qualifying count; **fresh dedicated RNG purposes per object/arm** so no existing stream shifts and the
  hybrid/native nulls are disjoint. Then the **independence-assuming** `xen.expectancy.contrast_ci` on the
  stored bootstrap distributions of the arm signal population and its RM arm — **median** (binding) and
  **mean** (disclosed) — gives `arm − RM`. `beats_rm` = (`arm − RM` median CI_low_1s > 0), per object.
- **Why this method**: P5 mandates the own-substrate random control in *every* read **per object** — the
  test that disentangled signal from MA-geometry drift in EXP-060B. An arm median-positive only because the
  MA substrate drifts is not a harami edge. The arm (indexed over haramis) and RM (indexed over disjoint
  random in-regime draws) are **independent samples** with no common per-event subset to pair — exactly as
  EXP-060B/061 treat signal-vs-matched-random. Each object must beat *its own* null (matched to its own
  count, excluding its own entries); a shared null would mis-attribute the lower-count hybrid object.
- **Simpler alternative considered**: a single Mann-Whitney on arm-vs-RM pooled, or one shared null for
  both objects. Rejected — the matched-random draws are not paired (disjoint pools), so independence-assuming
  bootstrap contrast is the inherited construction (EXP-060B I2); a shared null violates P5.
- **Assumptions**: the two bootstrap distributions are independent (true by construction, disjoint pools).
  `NaN` bounds when power-limited (handled, never defaulted).
- **Expected output**: per cell × object × arm — `arm_rm_median_low_1s`, `arm_rm_mean_low_1s`, the
  `beats_rm` flag.

### Step 4 — Lever contrast `arm − benchmark`, **per object** (binding lever)

- **Method (3b, lever):** the **paired** `xen.favourable_targets.paired_median_contrast_ci` on the
  **common qualifying-event subset** of the arm and that object's BENCH arm (both indexed over the same
  object's conditioned haramis, differing only in exit machinery, so paired is correct and tighter; events
  qualifying for the arm but not BENCH, or vice versa, are excluded from the paired subset). `beats_bench` =
  (`arm − benchmark` paired median CI_low_1s > 0), per object. The composite `arm_wins` flag =
  `median_viable ∧ beats_rm ∧ beats_bench`, per object.
- **Why this method**: the lever question (does this exit scheme beat the object's benchmark?) compares two
  exit configurations on the *same* events, so paired is correct and more powerful (the inherited EXP-059 +
  Phase-015-P5 design). Trailing arms additionally exclude events with no secondary-ZigZag history
  (warmup); the paired subset is the intersection of both arms' qualifying events. Differential warmup
  exclusions are reported alongside (`beats_bench` is on the common subset; the arm's absolute viability is
  on the arm's own qualifying set).
- **Simpler alternative considered**: pooled Mann-Whitney on arm-vs-benchmark. Rejected — ignores pairing
  (same events, different exits) and the RM attribution leg.
- **Assumptions**: common-subset pairing well-defined (both arms qualify and resolve the event), per object.
  `NaN` bounds when power-limited (handled, never defaulted).
- **Expected output**: per cell × object × arm — `arm_bench_paired_low_1s`, the `beats_bench` flag, the
  composite `arm_wins` flag, the per-arm **exit-reason composition** (fraction of weight via each exit
  reason), win rate.

### Composition (mechanical, predeclared), per object — never pooled

- Per-cell first; then **P11** = ≥ 5 cells over ≥ 3 instruments on `arm_wins`, **with the P6 non-4h rule**
  (≥ 3 qualifying cells outside 4h), **computed separately for each object**. Reported per arm type per
  object. Secondary P11 tallies for `median_viable`, `beats_rm`, `beats_bench`, and (disclosed)
  `mean_viable` (raw-mean CI_low>0 — the G-015 mean signal, never the gate) separately, per object.
- `fragile` flag when a tally composes at exactly the quorum boundary (5 cells / 3 instruments / 3 non-4h).
- **Exit-reason composition reported with every win count** — a scheme that "wins" by routing the majority
  through the time cap rather than the position-management exits is flagged (its composition shown beside
  its win count). This is the binding mechanism diagnostic for this lever.
- **Deferred secondaries (ZigZag substrate contrast):** a direct ZigZag-substrate benchmark arm contrast
  (EXP-059's position-management exit grid, reconciling to EXP-059 benchmark) is a **deferred** disclosed
  secondary (runtime/budget — 24 binding arm instances + their nulls per cell; the ZigZag substrate carries
  its own M_sofar/cap pipeline), recorded in `run_metadata.json` — the EXP-063/EXP-064/EXP-065 dual-object
  deferral pattern. The per-object MA EVIDENCE_* readout vs EXP-059's ZigZag result is the comparison
  retained here.

## Visualisations (5 / 5 budget) — each carries both objects (hybrid + native), never pooled

1. **Per-arm median-expectancy forest vs benchmark** (headline) — per cell, each arm's median CI alongside
   that object's benchmark, sorted, coloured by `arm_wins`; **native and hybrid as distinct panels/series**.
   Answers: does any exit scheme beat benchmark cell by cell, and is it signal-attributable — per object?
2. **Arm−benchmark and arm−RM contrast heatmap** (arm types × cells) — two-panel; non-4h cells marked;
   **per object**. Answers: where on the grid does each scheme bite, and does it survive the RM null — per
   object?
3. **Expectancy distribution by arm type (pooled within object)** — violin/box of `R_event` by arm type,
   **native and hybrid panels**. Answers: how does each scheme reshape the return distribution (esp. whether
   trailing/partial thins the adverse tail) — per object?
4. **P11 (non-4h) composition / wins map** across arm types — per-arm tally of `arm_wins`, `median_viable`,
   `beats_rm`, `beats_bench`, and (disclosed) `mean_viable`; quorum line drawn; **native and hybrid
   side-by-side**. Answers: which arm (if any) clears the binding quorum, is it 4h-carried (P6), and does
   any arm also clear the mean — per object?
5. **Exit-reason composition by arm type + median-vs-mean P4 preview** — per-arm fraction of weight via
   each exit reason (the mechanism diagnostic) alongside per-cell qualifying counts; median vs raw mean vs
   10% trimmed mean + worst-5% tail-share for the best arms; **native and hybrid panels**. Answers: how
   does the winning scheme realise P&L, and does it move the mean toward positive — per object?

Both objects are carried within the 5-plot budget (panels/series within each figure). Secondary tables
(`per_cell_expectancy`, `position_mgmt_map`, `secondary_map`, `reconciliation`) go to CSV/parquet, not plots.

## Interpretation Guide (predeclared; mirrors `scope.md` Success/Failure), per object

- **EVIDENCE_FOR (a position-management scheme helps on MA, for that object)** — ≥1 arm type
  median-viable **AND** beats its same-object RM-on-MA null **AND** beats that object's benchmark MA arm,
  composed by P11 with the non-4h rule. The winning arm + its margins + its exit-reason composition + its
  P4 mean diagnostic feed EXP-067 (hybrid) / EXP-068 (native) / G-015. (An arm that is also
  raw-mean-positive is the strongest possible surface input to a G-015 PROCEED, but the EVIDENCE_FOR label
  stays median-binding.)
- **EVIDENCE_AGAINST (position management is not an MA lever for that object)** — no arm clears the
  combined (`median_viable ∧ beats_rm ∧ beats_bench`) P11 quorum for that object. **Family stays OPEN** —
  the surface (S4/combined-champions) runs regardless (P9 no-early-closure).
- **INCONCLUSIVE (power-limited)** — fewer than the P11 quorum of cells reach ≥ 30 qualifying events on
  the arms of interest for that object (scaling/trailing construction + warmup exclusions deplete counts),
  no correctness failure. Disclosed explicitly; never the default. The hybrid 3202-class object is expected
  more power-limited than native 8360-class; an INCONCLUSIVE hybrid + an expressing native is itself a
  deliverable.
- **Hybrid vs native divergence (the central new fact):** EXP-061 found native generalises while hybrid
  does not at the benchmark geometry. If native is EVIDENCE_FOR while hybrid is
  EVIDENCE_AGAINST/INCONCLUSIVE, the exit-machinery benefit is a matched-substrate conditioning property;
  convergence would broaden the claim. The divergence is the deliverable, not a defect.
- **SUBSTRATE/METHOD_DEFECT** — checks: (i) **`M-BENCH` reproduces EXP-061 `M0` / EXP-060B `BENCH-MA`**
  and **`H-BENCH` reproduces EXP-061 `H0`** per-cell median + count to `RECON_TOL = 1e-9`; (ii)
  population reconciliation: hybrid ↔ EXP-053/060/061 `H0` (3202-class), native ↔ EXP-060B/061 `M0`
  (8360-class), exact; (iii) leg weights sum to 1.0 for every arm type, and a degenerate single-trigger arm
  reproduces the equivalent single-leg `R_event` to float precision; (iv) the trailing stop is monotone
  (never loosens) and changes level only on secondary-ZigZag confirmation bars (`ConfirmTime ≤ CloseTime`);
  (v) every exit price a real-bar P15 fill with `CloseTime ≤ train_end_ts`; (vi) the shared
  adverse/trailing stop, when it binds, closes all still-open legs at the same bar/level; (vii)
  **matched-count holds per object** — each arm's RM/RH count equals that object's cell arm signal count.
  Fix before reporting any efficacy verdict.

Deliverable label: **MA_POSITION_MGMT_CHARACTERISED (dual-object)**. No phase closure, no candidate
registration, no gate adjudication here (single terminal G-015 after the full slate; this read's survivors
feed EXP-067 hybrid / EXP-068 native).

## Implementation Safety Constraints (for `experiment-developer`)

- **Holdout fence (binding).** TRAIN = first 70% of the first-70% analysis set, **file-order prefix** (F01):
  `analysis_rows = int(total*0.7)`, `train_rows = int(analysis_rows*0.7)`, collect only the first
  `train_rows` rows via `pl.scan_parquet(...).slice(0, train_rows)`. **Never** sort/collect the full file;
  **never** read TEST or the final-30% global holdout. Assert chronological; `train_end_ts` = last
  `CloseTime`. Reuse EXP-064's `load_train_1m` unchanged. **All forward scans (legs, reversal events,
  trailing ratchet, time caps) are clipped to `train_end_ts`** — a window that would extend past it is
  `DATA_CENSORED`, never resolved against TEST/holdout rows.
- **Temporal ordering & alignment.** Order by `CloseTime`; align HA/ZigZag/MA events to real domain bars
  by exact `CloseTime`-epoch match (`_map_to_grid`), never by bar index. The **same** harami `entry_idx`
  feeds both objects; verify `ma["entry_idx"]` and `zz["entry_idx"]` are the identical array before
  applying the cross-substrate hybrid mask through the MA context (EXP-061/064 already does this for `H0`).
  The secondary ZigZag (`atr_mult=0.5`) trailing-structure pivots are also aligned by `CloseTime`. Domain
  aggregation: 5m strict, others `min_coverage=0.90`, then fence every bar to `CloseTime ≤ train_end_ts`.
- **Causality / no look-ahead.** MA(20,50) `_sma` trailing only; MA segments bounded by crossovers
  confirmed **before** entry; `M_sofar`, the benchmark fav/adv levels, the leg targets, and the MA
  benchmark cap use only MA segments confirmed strictly before entry. The native `/STRONG-STAT` filter
  references only confirmed prior MA segments. **The MA in-progress state — hence `rd`, `M_sofar`, the
  fav/adv levels, and the BENCH cap — is shared by both objects**; only the qualifying mask differs. Every
  exit is a forward event: first-profit close (bar close), fractional-target touch (intrabar P15), reversal
  event (next confirmed MA segment `Direction==rd` or opposing-harami confirm — at the confirmation bar's
  close, never an unconfirmed crossover/pivot), and the structure trailing stop (the stop in force at bar
  `t` uses only secondary-ZigZag moves with `ConfirmTime ≤ CloseTime(t)` — moves at the confirmation bar,
  never the retroactive pivot). The trailing ratchet is monotone (never loosens). Matched-random-on-MA
  entries (both objects) constructed causally. Forward scan reads only
  `[entry_idx+1, min(entry_idx+bench_N, last_train_idx)]`. Keep EXP-064's `_causality_ok` gate.
- **Real-price discipline.** Detection on HA candles only; **every** outcome metric (returns, `M_sofar`,
  all levels/legs/stops, the secondary trailing ZigZag, fills, weighted expectancy, exit-reason
  composition) on real OHLC; MA(20,50) on **real close**. The opposing-harami reversal arm uses HA candles
  only to *locate* the exit bar, then exits at that bar's **real** close. No HA price in any metric.
- **Denominators / zero-baseline.** Per-event `R_event` defined only for **qualifying** events (barriers/
  legs constructible — `fav_dist > 0`, finite positive `ATR_entry`, secondary ZigZag available for trailing
  arms — and every leg / the position reaching a finite P15 exit in the TRAIN-fenced window).
  `DATA_CENSORED` + construction/warmup-excluded events **excluded** from median/mean/trim and **disclosed
  as counts** per cell per arm per object. A cell with **< 30 qualifying events** on an arm (of an object)
  is `NOT_VIABLE-by-power` — never an undefined/infinite ratio. Worst-5% tail-share with 0 negative mass →
  0.0 (finite), not NaN/inf. First-hit `r` = `n_FAV/(n_FAV+n_ADV)`, TIMECAP excluded, disclosed **per
  object** for BENCH only; undefined (not reported as viability) for multi-leg/trailing arms — the P14
  rationale.
- **Determinism (P12).** Fixed per-cell seed throughout; **distinct RNG purpose per object/arm/statistic**
  so the `M-BENCH` median path is byte-identical to EXP-061 `M0`, the `H-BENCH` path byte-identical to
  EXP-061 `H0`, and no arm's stream perturbs another. Second full pass (or per-instrument first-cell
  replay, as EXP-061/064) asserting byte-identical per-object per-arm returns, medians, CIs, RM returns,
  contrasts, and exit-reason composition. Output **byte-identical across worker counts** (order-independent
  RNG + fixed merge order).
- **Vectorization discipline.** Reuse EXP-059's `position_exits` multi-leg + trailing resolvers and the
  EXP-058/065 `third_event_caps` forward-locator verbatim (pointed at MA segments for the reversal-event
  leg); do not rewrite the sequential causal state construction (the trailing-stop step function and the
  per-leg P15 assignment are genuinely sequential — keep them explicit and bounded). New code paths vs
  EXP-064: feeding MA-substrate levels into the position-exit resolvers (replacing EXP-064's
  favourable-target build), loading/running the secondary ZigZag (`atr_mult=0.5`), the per-arm-per-object
  RM call (**new dedicated RNG purpose offsets** so no existing median/RM stream shifts), and (already
  present) the trimmed-mean/tail-share statistic. **Never rewrite a sequential causal loop into a vectorized
  form that changes temporal ordering or look-ahead semantics.**
- **Performance / parallelism.** Keep EXP-064/EXP-061's per-instrument `ProcessPoolExecutor` with
  per-process native-thread pinning (`POLARS_MAX_THREADS=1` etc.) and fixed-order reassembly.
  Byte-identical output for any `--workers`; never alter sample membership, ordering, denominators, metric
  definitions, seeds, or causal/streaming semantics. (12 arm types × 2 objects × their RM controls per
  cell is a heavy read; the per-instrument process pool plus bounded per-cell memory is the
  integrity-preserving way to absorb it — and is why the `/STRONG-HA` and full ZigZag-exit secondaries
  are deferred, see scope Exclusions.)
- **Reconciliation sources.** Load EXP-061's `per_cell_expectancy.parquet` (both the `M0` **and** `H0`
  per-cell median + count) as the `M-BENCH` / `H-BENCH` P12 anchors — EXP-060B available as the upstream
  native anchor. EXP-059's MA-seg baseline arms available as a *secondary cross-check* (disclosed; may
  differ if the MA construction differs from `ma_seg_arm` — note any difference, do not treat as a
  defect). A missing/zero anchor on checked cells ⇒ SUBSTRATE/METHOD_DEFECT.
- **Bounded memory / progress.** `tqdm` over the 99-cell grid (per-instrument worker); per-event forward
  scans bounded by `bench_N`; per-cell arrays released after summarisation. Plots from collected per-cell
  summaries only — **no** data reloads or chart regeneration.
- **Outputs (`results/`).** `per_cell_expectancy.parquet` (per cell × arm × **object**); `position_mgmt_map.csv`
  (binding `/STRONG-STAT` summary per arm type per object + P11 non-4h tally); `secondary_map.csv`
  (`/STRONG-HA` deferred, ZigZag contrast deferred, BENCH `r` per object, exit-reason composition per
  object — all per the scope Exclusions deferral); `reconciliation.csv` (native `M-BENCH` ↔ EXP-061 M0 /
  EXP-060B BENCH-MA; hybrid `H-BENCH` ↔ EXP-061 H0; populations vs EXP-053/060/061, per object);
  `composition_readout.json` (per-object per-arm P11 non-4h, wins, EVIDENCE_* fork, mean-diagnostic
  summary → EXP-067/EXP-068/G-015 input); `run_metadata.json` (seed, frozen + inherited constants,
  EXP-059/060/060B/061/064 source paths/hashes, holdout fence, `disclosed_secondaries_not_computed`).
  Output dirs created only in orchestration. Every per-cell record carries an `object` tag; per-object
  CSV/JSON keys separate hybrid and native; **no pooled aggregate is emitted**.

## Complexity Check

- **Statistical methods: 4 / 4** — (1) median moving-block bootstrap CI on `R_event` (binding, per arm
  per object); (2) mean + 10% trimmed-mean bootstrap CI + worst-5% tail-share (P4 diagnostic, per arm per
  object); (3) independent `arm − RM-on-MA` contrast CI (binding signal attribution, per arm per object);
  (4) `arm − benchmark` paired-median contrast CI (binding lever, per arm per object). **Running these four
  methods on the second object adds no distinct method** — same estimators, different population. A
  re-instrumentation of EXP-059 + EXP-061/064, not new methods.
- **Visualisations: 5 / 5** — per-arm forest; arm−benchmark/−RM contrast heatmap; expectancy distribution
  by arm type; P11 (non-4h) wins map; exit-reason composition + median-vs-mean P4 preview. Each carries
  both objects within the 5-plot budget (panels/series within each figure).
- **New modules: 0 / ≤ 1** — reuses `xen.position_exits`, `xen.third_barrier` (MA-segment reversal-event
  locator), `xen.expectancy`, `xen.favourable_targets`, and the EXP-060/061/064 dual-object MA pipeline;
  additions vs EXP-064 are: loading/running the secondary ZigZag (`atr_mult=0.5`) for the trailing
  structure, feeding MA-substrate levels into the position-exit resolvers (replacing the favourable-target
  build), the per-arm-per-object RM call (new RNG purposes), and (already present) the trimmed-mean/
  tail-share statistic. At most one thin orchestration wrapper under `code/`; **no new `xen/` analysis
  module**.

Plan fits the scope's complexity budget exactly; the dual-object structure doubles arms/columns/series,
not methods or plots.
