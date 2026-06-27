# Analysis Plan: Experiment EXP-060

**Title:** Combined Event System (Conditioned HA Harami; Best Per-Layer Geometry, 2×2 Favourable×Adverse Factorial + Champion)
**Phase / checkpoint:** `2026-06-14-014-ha-harami-substrate-and-capture` (014-B; G0-B PASS 2026-06-15)
**Family / HYP:** `CF-HA-HARAMI-001/HYP-013` — EXP-060 (PLANNED, Phase 014-B batch, `multiplicity-registry.md` line 390)
**Binding endpoint:** median per-event **position-weighted** gross expectancy `E_cell` (P14), ATR-normalised,
P15 fills, real prices, on the binding `/STRONG-STAT` arm; per-cell viable iff `CI_low > 0` (one-sided 95%
moving-block bootstrap) AND ≥30 qualifying events; composed by P11 (≥5 cells over ≥3 instruments).
**Binding candidate (operator decision 2):** the champion **A3 `V2A×ADV-NONE`** only. Its own P11 viability
**and** its dominance over **both** P13 baselines drive the PROCEED_TO_SCREEN / CHARACTERISED_NOT_VIABLE fork.
A0/A1/A2, the factorial decomposition, the `A3−A0` vs-BENCH read, and the A4 horizon sibling are **disclosed,
non-binding** attribution.
**Discipline:** gross; 0 candidate slots; 0 TEST reads; TRAIN only; holdouts sealed; detection on HA candles,
**all outcome metrics on real prices**. This plan does **not** expand `scope.md`; it specifies *how* the
5 predeclared arm configs are computed, validated, and read. No standalone governance (Stage 4 runs
consolidated).

---

## Objective

Determine whether the **combined event system that assembles the four measured per-layer winners** onto one
live `/STRONG-STAT`-conditioned, harami-anchored HA harami — **A3 = V2A 3-leg scaled favourable take-profits
`{1/3,2/3,1}×(0.50·M_sofar)` + no adverse stop (`/ADV-NONE`) + benchmark adaptive time cap** — produces a
gross per-event **median position-weighted expectancy** that clears the P11 quorum **and** beats **both** P13
baselines (matched-random, MA(20,50)). This is the single 014-B G2 PROCEED condition. Attributively (disclosed,
non-binding), decompose the champion across the **2×2 favourable×adverse factorial** (favourable main effect,
adverse main effect, interaction) vs the BENCH reference, and bound the **horizon confound** via the A4
disclosed sibling (champion at `/THIRD-TIME` floor=48). This is a characterization read feeding the single
014-B G2 — **never a closure or candidate registration here**.

**Predeclared arm set (5 configs; identical to `scope.md` §Predeclared arm set):**

| Arm | Favourable | Adverse | Cap | Role |
|-----|-----------|---------|-----|------|
| **A0 `BENCH`** | 50% (1 leg) | 1:1 | floor=6 | reference; reproduces EXP-053; the (50%,1:1) cell; **invariant anchor** |
| **A1 `50%×NONE`** | 50% (1 leg) | /ADV-NONE | floor=6 | adverse main-effect isolation; **disclosed** |
| **A2 `V2A×1:1`** | V2A {1/3,2/3,1} | 1:1 | floor=6 | favourable main-effect isolation (= EXP-059 V2A); **disclosed** |
| **A3 `V2A×NONE`** | V2A {1/3,2/3,1} | /ADV-NONE | floor=6 | **CHAMPION — the single binding G2 candidate** |
| **A4 `V2A×NONE@T48`** | V2A {1/3,2/3,1} | /ADV-NONE | floor=48 | champion at relaxed horizon; **DISCLOSED-only** |

Each runs on the binding `/STRONG-STAT` population; `/STRONG-HA` is a disclosed secondary arm; both P13
baselines (matched-count random in-regime timestamps; MA(20,50) segmentation) run through the identical per-arm
pipeline.

---

## Methodology

### Step 1: TRAIN-slice loading, domain construction, holdout fence

- **Method:** F01 file-order-prefix slicing per cell. Lazy `pl.scan_parquet`; `total_rows`;
  `analysis_rows = int(total_rows*0.7)`; `train_rows = int(analysis_rows*0.7)`; collect the first `train_rows`
  file-order 1-minute rows only; assert strictly increasing `CloseTime`; `train_end_ts = max(CloseTime)`.
  Aggregate each member domain (5m strict; 15m/30m/1h/2h/4h via `xen.bar_aggregator.aggregate_ohlc`,
  `min_coverage=0.90`); fence all derived series to `CloseTime ≤ train_end_ts`.
- **Why this method:** byte-identical fence to EXP-049/053–059 guarantees the conditioned population reconciles
  exactly with EXP-053 and that neither the nested TEST stratum nor the final-30% global holdout is touched.
- **Simpler alternative considered:** sort-then-slice on `CloseTime` — rejected; the F01 prefix is the
  established convention and avoids materialising the full file (bounded memory, holdout never collected).
- **Assumptions:** 1-minute base rows are in chronological file order (asserted). Holds — VAL-001/VAL-004.
- **Expected output:** per-cell TRAIN real domain bars + `train_end_ts`; the holdout-exclusion guard.

### Step 2: Substrate, detector, and the conditioned population (identical to EXP-053–059)

- **Method:** primary `xen.zigzag.generate_zigzag(bars, atr_period=14, atr_mult=1.0)` → confirmed moves +
  `xen.capture_barriers.confirm_indices`; HA candles (`xen.heiken_ashi_generator`) →
  `xen.ha_harami.detect_ha_harami` (frozen EXP-048 detector), aligned to real bars by `CloseTime`;
  `xen.expectancy.live_in_progress_state` (supplies `rd`, `start_pivot`/`start_idx`, `M_sofar`) +
  `live_strong_stat` (binding p75 retention; disclosed median+MAD); `/STRONG-HA` via
  `xen.strong_move.annotate_ha_impulse`. **No secondary 0.5×ATR ZigZag is generated** (no trailing arm here).
- **Why this method:** every primitive is frozen and validated (EXP-048/051); reusing the *same* functions is
  what makes the population reconcile with EXP-053 exactly (invariant ii).
- **Simpler alternative considered:** none — the conditioned-signal definition is fixed by P16.
- **Assumptions:** ZigZag/HA causality (pivots future-info until confirmed; HA detection uses only
  at-or-before-`t_i` data). Holds by construction (EXP-048 readiness PASS).
- **Expected output:** the binding `/STRONG-STAT` conditioned event set per cell (entry bar `C`, `rd`,
  `M_sofar`, `start_idx`, `ATR_entry = Wilder ATR(14)` at the entry bar); the `/STRONG-HA` arm.

### Step 3: Benchmark geometry + both adaptive time caps

- **Method:** `xen.expectancy.benchmark_barriers(C, rd, M_sofar)` → `fav_dist = 0.5·M_sofar`,
  `fav = C + rd·fav_dist`, `adv = C − rd·fav_dist`; `xen.expectancy.adaptive_time_caps_by_epoch(..., floor=6)`
  → `bench_N`, `warmup` (P4, for A0–A3); a **second** call `adaptive_time_caps_by_epoch(..., floor=48)` → `N48`,
  `warmup48` (P4 knobs `k=1.5, window=20, min_moves=5` unchanged; only the floor differs) for A4.
- **Why this method:** OAT cross-layer assembly — the favourable level, the 1:1 adverse (where present), and the
  cap come from the frozen benchmark machinery; only the arm's three layers are recombined. The floor=48 cap is
  the registered `/THIRD-TIME` grid maximum (EXP-058), not a new value.
- **Simpler alternative considered:** none; this is the EXP-053/058 machinery reused verbatim.
- **Assumptions:** `M_sofar > 0` for a valid target (gated). Holds for conditioned events by construction.
  `N48 ≥ bench_N` per event by construction (`max(48,·) ≥ max(6,·)`) — used in invariant (vii).
- **Expected output:** per-event `fav`, `adv`, `fav_dist`, `bench_N`, `N48`, `warmup`, `ATR_entry`.

### Step 4: Arm construction — five configs from existing resolvers (no new `xen/` module)

The combined system is a **recomposition of frozen resolvers**; there is **no new event geometry**. Per event,
each arm's forward scan is the existing bounded sequential P15 loop over real OHLC
`[entry+1, min(entry+N, last_train_idx)]` (N = `bench_N` for A0–A3, `N48` for A4). **These loops are the object
under test — never vectorize them** (they carry the causal/streaming semantics; same contract as
`xen.expectancy.resolve_path_ordered`).

- **A0 `BENCH`** — single leg `w=1`: `xen.expectancy.resolve_path_ordered(fav, adv, bench_N)`. Exactly
  EXP-053's benchmark. Reproduces EXP-053 per-cell median expectancy, qualifying count, and `r≈0.50`
  (invariant i).
- **A1 `50%×NONE`** — single leg `w=1`, favourable level `fav`; adverse from
  `xen.adverse_targets.adverse_none_sentinel(C, rd, fav_dist)` (`adv = ∓inf`, `has_stop=False`) so the shared
  resolver can only fire `FAV`/`TIMECAP`/`DATA_CENSORED`. Resolve via `xen.position_exits.resolve_legs` with one
  leg at `fav` (`adv_mode=ADV_FIXED`, `adv_level=±inf`, `n_event=bench_N`).
- **A2 `V2A×1:1`** — 3 equal legs at `{1/3,2/3,1}×fav_dist` via
  `xen.position_exits.leg_levels_from_fracs((1/3,2/3,1), C, rd, fav_dist)`; shared 1:1 adverse `adv` (binds all
  still-open legs at the same bar/level on the P15 path — invariant vi); `resolve_legs` (`adv_mode=ADV_FIXED`,
  `adv_level=adv`, `n_event=bench_N`). Identical to EXP-059 PARTIAL-V2A.
- **A3 `V2A×NONE` (champion)** — 3 equal legs at `{1/3,2/3,1}×fav_dist`; shared adverse = the ADV-NONE sentinel
  (`adv_level=±inf`, never binds); `resolve_legs` (`adv_mode=ADV_FIXED`, `n_event=bench_N`). Still-open legs run
  to their favourable target or exit `TIMECAP` at the cap bar's real close. **The only novel cross-layer cell**
  (V2A validated under 1:1; ADV-NONE validated under a single 50% leg — their conjunction is unmeasured).
- **A4 `V2A×NONE@T48`** — identical to A3 but `n_event=N48` (floor=48 cap). Disclosed-only.

- **Why this method:** every leg/level/stop/cap primitive already exists and is frozen (EXP-053/057/058/059).
  The champion and all factorial cells are exact recompositions — `resolve_legs` already supports the
  single-leg, multi-leg, fixed-adverse, and ±inf-adverse cases. No `/EXIT-TRAIL-STRUCT` (no trailing builder),
  no reversal-event legs (V2A is pure fractional targets) → none of EXP-059's trailing/reversal machinery is
  exercised here.
- **Expected output:** per event per arm: per-leg exit class ∈ {`FAV`, `ADV` (A0/A2 only), `TIMECAP`,
  `DATA_CENSORED`} and exit price; the per-leg tags feed the exit-reason composition.

### Step 5: Position-weighted realised return + qualifying mask

- **Method:** `R_event = Σ_l w_l · rd·(exit_px_l − C)/ATR_entry`, `Σ_l w_l = 1` (3 legs `w=1/3` for V2A arms;
  1 leg `w=1` for A0/A1) via `xen.position_exits.weighted_returns` (per-leg sign/normalisation matches
  `xen.expectancy.realised_returns`, then weight-sum). **Qualifying** (the P14 denominator): `fav_dist > 0`,
  finite `ATR_entry > 0`, and **every** leg reaches a finite P15 exit (favourable level, shared 1:1 stop where
  present, or cap close) within the TRAIN-fenced window; any leg left `DATA_CENSORED` (window truncated by the
  TRAIN edge) → the **event** is `DATA_CENSORED`, excluded from the median and **disclosed as a count** per cell
  per arm.
- **Why this method:** the weighted realised return is exactly the mechanism's gross P&L; it is the only
  endpoint that credits scaled exits (P14). The qualifying rule mirrors EXP-053–059 (built window, finite exit),
  generalised to "all legs resolved".
- **Simpler alternative considered:** first-hit `r` — rejected by P14 (blind to multi-leg exits); retained as a
  disclosed secondary for the single-leg A0/A1 arms only.
- **Assumptions:** ATR-normalisation makes cells comparable (P14). Leg weights are a fixed governance constant
  (not tuned). Because A0–A3 share the **same** `bench_N` window, their qualifying sets differ only in *where*
  (not *whether*) events resolve → the common 4-arm subset (Step 8) ≈ each arm's set, so the factorial is
  well-powered; A4's longer `N48` window raises `DATA_CENSORED` near the TRAIN edge → A4's qualifying set ⊆ A3's
  (the `A4−A3` contrast uses their common subset).
- **Expected output:** per cell per arm, the qualifying-event `R_event` population (entry-time order).

### Step 6: Per-cell median bootstrap CI (binding viability) — statistical method (1)

- **Method:** `xen.expectancy.bootstrap_median_distribution(R_event, rng, n_boot=10_000)` (moving-block,
  `b = max(1, round(m^{1/3}))`, `ceil(m/b)` contiguous blocks in entry-time order — regime/serial-dependence
  preserving, identical block ctor to `xen.capture_barriers.block_bootstrap_ci`) → `xen.expectancy.median_ci`
  → `E_cell` (median), `ci_low_1s` (5th pct, the binding one-sided 95% lower bound), two-sided (2.5/97.5)
  bounds. Per-cell viable iff `ci_low_1s > 0` AND `m ≥ 30`.
- **Why this method:** the per-event return distribution is fat-tailed (P14 chose the median); a non-parametric
  moving-block bootstrap respects serial/regime dependence without distributional assumptions (programme
  principle: non-parametric by default). Identical to EXP-053–059.
- **Simpler alternative considered:** i.i.d. bootstrap / normal CI — rejected (ignores serial dependence;
  normality fails for these returns).
- **Assumptions:** approximate within-cell stationarity over the TRAIN block structure; block length absorbs
  short-range dependence. Acknowledged-weak, mitigated by the block bootstrap (no stronger claim made).
- **Expected output:** per cell per arm: `E_cell`, `ci_low_1s`, two-sided CI, `m`, viability flag.

### Step 7: Champion-vs-baseline contrasts (BINDING for A3) — statistical methods (1) on baselines + (4) contrast

- **Method:** run the **A3 pipeline** (and every arm's, for disclosure) on the two P13 baselines:
  (a) **matched-count random in-regime timestamps** (same cell/regime/direction, EXP-021/027 exclusion
  convention, fixed seed) through the identical exit machinery; (b) **MA(20,50)** segmentation (alternative
  trend substrate; conditioned-harami expectancy under MA-segmented moves). Bootstrap each baseline median
  (method 1) and form the **A3 − baseline** median difference via `xen.expectancy.contrast_ci` (independent
  RNG streams; resample-index pairing is a Monte-Carlo convenience, as documented in `contrast_ci`). A3 **beats
  a baseline** in a cell iff that contrast's `ci_low_1s > 0`.
- **Binding rule (operator decision 2 — the two-baseline conjunction):** for the champion A3, beating **both**
  baselines is **binding** (a per-cell champion win requires A3 viable **AND** `A3−matched-random` `ci_low_1s>0`
  **AND** `A3−MA(20,50)` `ci_low_1s>0`). For A0/A1/A2/A4 the baseline contrasts are **disclosed only**.
- **Why this method:** baselines test specificity — "does the combined scheme beat random/alternative-
  segmentation entries under the *same* scheme", i.e. the champion edge is the *conditioned harami*, not the
  exit machinery or the ZigZag segmentation. Identical estimator to EXP-053–059; only the binding status of the
  two baseline contrasts is elevated for the champion (per the scope).
- **Simpler alternative considered:** vs-BENCH only as the binding contrast — rejected: BENCH shares the
  conditioned events, so `A3−A0` measures the *exit/adverse geometry's* value, not whether the *conditioned
  signal* has an edge. The P13 baselines (different entries / different segmentation) are the correct
  specificity gate, hence binding here; `A3−A0` is retained as the disclosed "value of the combined system".
- **Assumptions:** independence between signal and baseline draws (`contrast_ci` Monte-Carlo pairing). Disclosed
  where a baseline's `m < 30` (NOT_VIABLE-by-power, the contrast non-reportable for that cell).
- **Expected output:** per cell per arm: baseline medians + arm−baseline contrast; for A3 the binding
  both-baseline-beat flag.

### Step 8: Factorial decomposition + vs-BENCH + horizon (DISCLOSED) — statistical method (3, paired)

All contrasts on the **common qualifying-event subset** (events qualifying under *both* compared arms,
entry-time order, equal length `m`) via `xen.favourable_targets.paired_median_contrast_ci` (one block-index
draw applied to **both** series per resample, so shared event/regime noise cancels — the tighter paired
difference). A contrast is "positive" iff its `ci_low_1s > 0`.

- **Favourable main effect:** `A2 − A0` (under 1:1) and `A3 − A1` (under ADV-NONE).
- **Adverse main effect:** `A1 − A0` (single 50% leg) and `A3 − A2` (V2A legs).
- **Champion value (vs benchmark):** `A3 − A0` — the headline "value of the combined system" (disclosed; the
  *binding* G2 readout is Step 7, A3 vs the two P13 baselines).
- **Horizon sensitivity:** `A4 − A3` — does relaxing the 6-bar floor to floor=48 change the champion (on the
  A4∩A3 common subset; the difference is admissible only via fewer cap-truncations, invariant vii).
- **Interaction `(A3 − A2) − (A1 − A0)`** — does V2A-scaled-exits and no-stop combine super-/sub-additively?
  **CI construction (the one composition the existing two-series helper does not cover):** on the **common
  4-arm qualifying subset** (events qualifying under A0∧A1∧A2∧A3, aligned in entry-time order), draw **one** set
  of block start indices (same block ctor `b=max(1,round(m^{1/3}))`, `ceil(m/b)` blocks as
  `paired_median_contrast_ci`) and apply it to **all four** aligned `R_event` series per resample; compute the
  composite statistic `(median(A3*) − median(A2*)) − (median(A1*) − median(A0*))` per resample; the interaction
  CI = its (5th, 2.5/97.5) percentiles. This is a **direct generalization of method (3)** to four series (same
  block bootstrap, same median-difference statistic, one shared block draw), **not** a new statistical method —
  it lives in the permitted thin `code/`-level combined-arm wrapper, **no new `xen/` module**. Reported as a
  **disclosed point estimate + CI**; if the common 4-arm `m < 30` the interaction is reported as a point
  estimate with a power disclosure (never defaulted).
- **Why this method:** the factorial is the operator's chosen high-information-density decomposition; paired
  contrasts on shared events are the correct, tighter tests (the arms share the conditioned population). All of
  it is **disclosed attribution** — it explains *why* the champion does/doesn't work, never *whether* (Step 9).
- **Expected output:** per cell + pooled: the four main-effect/vs-BENCH/horizon paired contrasts and the
  composite interaction (median Δ, `ci_low_1s`, two-sided CI, common `m`).

### Step 9: P11 composition + the binding champion fork

- **Per-cell champion win (binding):** cell is an A3 win iff **(a)** A3 viable (`E_cell` `ci_low_1s>0` AND
  `m≥30`, Step 6) **AND (b)** `A3−matched-random` `ci_low_1s>0` **AND (c)** `A3−MA(20,50)` `ci_low_1s>0`
  (Step 7). (The two-baseline requirement is a **conjunction** — see Multiplicity Posture.)
- **P11 composition:** A3 clears P11 iff its wins span **≥5 cells over ≥3 instruments**.
- **Fork (predeclared, mechanical; EXP-060 emits the readout — the operator adjudicates at G2):**
  - **PROCEED_TO_SCREEN-eligible** iff A3 clears P11 (champion wins ≥5 cells / ≥3 instruments). The champion
    definition + its viable cells + margins-over-baselines are the deliverable for G2 candidate registration.
  - **CHARACTERISED_NOT_VIABLE-eligible** iff A3 does **not** clear P11 **and** ≥ the P11 quorum of cells reached
    `m≥30` on A3 (i.e. a genuine negative, not a power failure). The full conditioned best-per-layer surface is
    measured-negative; closure well-supported (adjudicated at G2, not here).
  - **INCONCLUSIVE (power-limited)** iff fewer than the P11 quorum of cells reach `m≥30` on A3 (conditioning +
    ADV-NONE/cap censoring deplete counts), no correctness failure. Disclosed; never defaulted to a ratio.
  - **SUBSTRATE/METHOD_DEFECT** iff any invariant/determinism check (Step 11) fails → fix and re-run before any
    reading (no result-aware threshold change).
- **Expected output:** `composition_readout.json` (champion P11 status, per-cell win map vs both baselines,
  fork label as an *eligibility* flag; the disclosed factorial summary).

### Step 10: Disclosed secondaries

- **Exit-reason composition (binding mechanism diagnostic, disclosed, never viability):** per arm, the fraction
  of position weight exiting via each V2A leg's favourable target, the shared 1:1 stop (A0/A2 only), and the
  time cap. This is the primary interpretive lens for *why* the champion wins or loses (e.g. a positive
  `E_cell` whose weight exits overwhelmingly at the cap means the **cap** — the EXP-058 horizon lever — drove
  it, not the V2A/ADV-NONE geometry; the A4 sibling then disambiguates).
- **Others:** `/STRONG-HA` arm (champion + all arms through the identical pipeline); per-arm qualifying count +
  `DATA_CENSORED`/warmup counts; win rate (fraction with `R_event>0`); mean per-event return; **first-hit `r`
  for the single-leg A0/A1 arms only** (A0: `n_FAV/(n_FAV+n_ADV)`, TIMECAP excluded, expected ≈0.50 replicating
  EXP-049/053; A1: a `FAV`-vs-cap descriptive only, no adverse class); both P13 baselines on the non-champion
  arms; the full factorial and `A4−A3` reads. None enters viability.

### Step 11: Determinism + predeclared invariant checks (correctness gate)

Two full passes (fixed seed) must produce byte-identical outputs. The seven predeclared invariants (scope
§Success/Failure) are asserted in-code and reported:
1. **A0 BENCH reproduces EXP-053** per-cell median expectancy, qualifying count, and first-hit `r` to tolerance.
2. **Population reconciliation vs EXP-053 exact** — the binding `/STRONG-STAT` conditioned population is
   identical (entry timestamps, `rd`, `M_sofar`).
3. **Leg weights sum to 1.0** for every arm; a **degenerate V2A** (all 3 legs forced to the same `fav` level)
   reproduces the single-leg 50% arm's `R_event` to float precision.
4. **ADV-NONE never fires an adverse exit** — A1/A3/A4 emit **no** `ADV` exit class (only `FAV`/`TIMECAP`/
   `DATA_CENSORED`); the sentinel `adv = ∓inf` is verified unreachable.
5. **Every exit is a real-bar P15 fill** with `CloseTime ≤ train_end_ts` (no exit past the TRAIN edge).
6. **Shared 1:1 stop (A0/A2) closes all still-open legs** at the same bar/level when it binds.
7. **A4 differs from A3 only by the cap:** identical population and leg levels; `N48 ≥ bench_N` per event; any
   A3-resolved event whose A4 resolution differs must differ *only* because A4's longer window postponed a
   `TIMECAP`/avoided a censor — any other divergence is a defect.

Any failure → SUBSTRATE/METHOD_DEFECT, fix before reporting.

---

## Multiplicity Posture (explicit)

- **One binding definition.** Only the champion **A3** is binding (operator decision 2). A0/A1/A2/A4, the
  factorial main effects/interaction, and `A3−A0` are **disclosed, non-binding**. There is therefore **no
  across-arm selection** and **no Holm/FWER correction across arms** — the family of binding hypotheses has a
  single pre-registered member.
- **P11 is the multiplicity control across cells.** Per-cell one-sided CIs are **not** Holm-corrected across the
  99 cells; the frozen programme convention (EXP-012/013 P5/P6; EXP-056/057/058/059) controls programme risk by
  the **composition quorum** (≥5 cells over ≥3 instruments) applied *after* per-cell adjudication, not by a
  per-cell FWER correction. EXP-060 follows that convention unchanged.
- **The two-baseline requirement is an intersection-union test (IUT), not a multiple-testing inflation.** The
  champion must beat **both** matched-random **and** MA(20,50) (a logical **AND** of two one-sided conditions).
  An IUT rejects the global null only when *every* sub-condition rejects, so its size is **≤ α** automatically
  (it is conservative) — **no Holm correction is needed or appropriate**; adding the second baseline makes
  passing *harder*, not the test more permissive. This is the correct, self-correcting posture for a conjunction
  of binding conditions.
- **Net:** zero formal multiplicity corrections are applied; the controls are (i) a single pre-registered
  binding definition, (ii) P11 composition across cells, (iii) a conservative two-baseline conjunction. All
  other reads are explicitly disclosed/non-binding. This matches the 014-B design §8 ("≥1 combined event
  definition clears P11") read with the operator's single-champion choice.

---

## Visualisations (5 / 5)

1. **Per-arm median-expectancy forest/CI per cell (champion A3 highlighted vs BENCH A0)** — does A3's `E_cell`
   sit above 0 and above BENCH, per cell? The five arms side by side.
2. **2×2 factorial decomposition** — favourable main effect (`A2−A0`, `A3−A1`), adverse main effect (`A1−A0`,
   `A3−A2`), and interaction `(A3−A2)−(A1−A0)`: pooled bar/whisker + a per-cell heatmap. The attribution view.
3. **Champion A3 binding read** — per-cell `E_cell` CI vs 0 **and** the two baseline contrasts (`A3−matched-
   random`, `A3−MA(20,50)`), with the P11 win map (which cells satisfy viable ∧ beats-both-baselines, over which
   instruments) — the binding G2 readout at a glance.
4. **Exit-reason composition by arm** (stacked: V2A legs / 1:1 stop / time cap, with per-cell qualifying counts
   annotated) — the binding mechanism diagnostic: how each arm realises P&L and how censoring depletes counts.
5. **Horizon sensitivity `A4 − A3` per cell** (champion at floor=6 vs floor=48) alongside each arm's cap-exit
   weight — isolates mechanism vs horizon-truncation (the operator's reason for the A4 sibling).

Secondary tables (`/STRONG-HA`, A0/A1 `r`, both baselines on non-champion arms, full factorial) to CSV.

---

## Interpretation Guide (predeclared, before results)

- If **A3 clears P11** (≥5 cells / ≥3 instruments with `E_cell` `ci_low_1s>0`, `m≥30`) **AND in those cells
  beats both P13 baselines** (`A3−matched-random` and `A3−MA(20,50)` `ci_low_1s>0`) → **PROCEED_TO_SCREEN-
  eligible**: the assembled best-per-layer combined event system is a viable candidate; its viable cells +
  margins are the G2 deliverable (candidate registration happens at G2, not here). Read the factorial (Viz 2) +
  exit-reason composition (Viz 4) to attribute the edge (favourable vs adverse vs interaction; legs vs cap).
- If **A3 does not clear P11** (with ≥ the quorum of cells powered) → **CHARACTERISED_NOT_VIABLE-eligible**: the
  full conditioned best-per-layer surface is measured-negative. Cross-check: EXP-053 (conditioned signal real),
  EXP-055 (move available), EXP-056/058 (favourable/horizon benchmark-best), EXP-057 (ADV-NONE best),
  EXP-059 (V2A best) — if the move is available and each layer's best was assembled yet the system still does
  not clear vs baselines, capture is geometry-limited on this substrate; closure is well-supported (adjudicated
  at G2 across the full slate).
- If **fewer than the P11 quorum of cells reach `m≥30` on A3** → **INCONCLUSIVE (power-limited)**; disclose the
  depletion (ADV-NONE/cap censoring + conditioning), never default to a ratio.
- If **any invariant (Step 11) fails** → **SUBSTRATE/METHOD_DEFECT**; fix and re-run before any reading.
- **Attribution reads (disclosed, never change the verdict):** the interaction sign tells whether combining the
  two EVIDENCE_FOR winners (V2A, ADV-NONE) is super-additive (`>0`), additive (`≈0`), or sub-additive (`<0`);
  `A3−A0` is the "value over benchmark"; `A4−A3` tells whether a flat/negative champion is mechanism-limited
  (A4≈A3) or horizon-truncated (A4≫A3 — would motivate a *future* scope pairing V2A/ADV-NONE with a longer
  third barrier, **not** a re-read here). First-hit `r` is interpreted **only** for A0 (≈0.50 expected;
  meaningless for multi-leg arms by construction — the P14 rationale).

---

## Implementation Safety Constraints (for `experiment-developer`)

- **Temporal ordering / causality:** all alignment by `CloseTime`, never bar index across the primary ZigZag,
  HA, and real-bar views. The Step 4 resolvers read only bars with index `> entry_idx` and
  `CloseTime ≤ train_end_ts`; the leg levels, `adv`, `bench_N`, `N48` are fixed at entry.
- **Do NOT vectorize the resolvers (Step 4).** They are explicit bounded sequential P15 loops over real OHLC —
  their causal/streaming semantics are the object under test (the `resolve_path_ordered`/`resolve_legs` "do not
  vectorize" contract). Bound per-event work by `bench_N` (≈6 bars in 96/99 cells) and by `N48` for A4 only.
- **Reuse, do not re-implement:** A0 via `resolve_path_ordered`; A1–A4 via `resolve_legs` +
  `adverse_none_sentinel`/1:1 + `leg_levels_from_fracs`; medians/contrasts via
  `bootstrap_median_distribution`/`median_ci`/`paired_median_contrast_ci`/`contrast_ci`. The **only** new code is
  the thin `code/`-level combined-arm wrapper (assemble the 5 arm configs; the factorial-contrast table; the
  4-series composite interaction bootstrap). **No new `xen/` analysis module.**
- **Denominators / zero-baseline:** a cell with `<30` qualifying events for an arm is NOT_VIABLE-by-power
  (non-reportable), never an undefined/infinite ratio; `DATA_CENSORED`/warmup excluded-with-record, disclosed.
  The interaction's common 4-arm subset and each paired contrast's common subset follow the same `<30` rule.
- **Real prices only:** every exit price is real-bar OHLC; HA candles only *detect* the harami and run the
  `/STRONG-HA` impulse. No HA price in any metric.
- **Bounded memory + progress:** `tqdm` over the 99-cell grid; do not retain all domain frames or all bootstrap
  draws (`BOOT_BATCH` batching as in `xen.expectancy`); per-cell bounded.
- **Determinism:** fixed seed; two full passes byte-identical (Step 11). No output directory creation at import
  time; helper functions return data (no helper-level prints); concise orchestration logging only.
- **No safe-optimization that changes membership/order/denominators:** leg-resolution order, the P15 path, the
  qualifying rule, the common-subset construction, and the regime-cluster bootstrap block construction are fixed.

---

## Complexity Check

- **Statistical methods: 4 / 4** — (1) moving-block bootstrap median CI on an arm's `E_cell` per cell; (2) the
  same on each P13 baseline; (3) paired-median contrast CI for the factorial main effects / vs-BENCH / horizon /
  **and** the 4-series composite interaction (a generalization of the same paired block bootstrap, not a new
  method); (4) arm − baseline contrast CI (`contrast_ci`). Applied across the 5-arm assembly (a parameterised
  recomposition over one experiment, **not** new methods per arm) — identical method set to EXP-056/057/058/059.
- **Visualisations: 5 / 5** (listed above).
- **New code modules: ≤1 / 1 — *0 new `xen/` modules*.** The arm set composes existing frozen resolvers; the
  only new code is a thin `code/`-level combined-arm wrapper (5 arm configs + the factorial-contrast table + the
  composite interaction bootstrap). Orchestration in `code/run_experiment.py`.

---

## Data-View Comparison Considerations

- **Cross-view alignment:** primary ZigZag, HA candles, and real bars align by `CloseTime`. The conditioned
  harami population must reconcile **exactly** with EXP-053 (invariant ii); different arms produce slightly
  different *qualifying* counts only via `DATA_CENSORED` near the TRAIN edge (A4's longer window) — the
  underlying signal set is identical.
- **Event-count differences:** A0–A3 share `bench_N`, so their qualifying sets are near-identical (the factorial
  is well-powered); A4's floor=48 window depletes late-TRAIN cells (disclosed). Compose only over cells reaching
  `m≥30`.
- **Real-price discipline:** all P&L/excursion on `RealOpen/High/Low/Close`; HA only for detection/`/STRONG-HA`.

---

## Limitations (predeclared)

- **Best-per-layer ≠ globally optimal.** The champion assembles each layer's OAT winner; the 2×2 factorial +
  interaction is the predeclared guard against the assumption that combining single-layer winners is best
  (the interaction quantifies any sub-additivity). Broader cross-layer alternatives (V2C, MAG-0.5, other floors)
  were declined by the operator to keep the focused "best per-layer" intent — so a sub-additive interaction is a
  *disclosed* caveat, not a trigger to search further within EXP-060.
- **Benchmark cap may bound the combined favourable mechanism.** The P4 cap collapsed to the 6-bar floor in
  96/99 cells (014-A G1); V2A's scaled legs and ADV-NONE's "let it run" adverse both want horizon. The A4
  (floor=48) disclosed sibling bounds how much of any champion shortfall is horizon-truncation vs mechanism —
  but A4 is **non-binding**; a strong `A4−A3` would motivate a *future* scope (V2A/ADV-NONE × longer third
  barrier), not a re-read here.
- **ADV-NONE means unbounded adverse within the cap.** With no stop, a champion event that goes adverse rides to
  the cap; the median endpoint (P14) is robust to the resulting fat left tail, but the **mean** (disclosed) may
  diverge from the median — reported, not reconciled (gross-only, no risk model in 014-B).
- **Gross only**; the cost model enters only at a future tradability screen of a registered candidate branch
  (only if G2 returns PROCEED_TO_SCREEN). ADV-NONE's unbounded adverse will matter materially under costs — out
  of 014-B scope, flagged for the screen.
- Standard moving-block bootstrap caveats (approximate within-cell stationarity) apply, mitigated by the block
  construction; no stronger statistical claim is made.
```
