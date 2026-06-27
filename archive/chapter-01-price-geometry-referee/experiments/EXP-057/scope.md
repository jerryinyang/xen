# Experiment: EXP-057 — Adverse-Target Geometry (Conditioned HA Harami; `/ADV-EXTREME`, `/ADV-NONE` vs Benchmark 1:1)

> **Mandatory-reading precondition (014-B, binding).** `014-A-conditioning-gap-and-validation-lessons.md`
> was read in full before this scope was written. EXP-057 is the **adverse-target geometry** surface
> read (HYP-010, P14/P16). The four mandatory rules are honoured as follows, recorded so Stage 4 can
> check:
> - **(a) conditioning** — honoured. The object measured is the **live `/STRONG`-conditioned HA
>   harami** (the actual family signal, identical population to EXP-053/054/055/056), not the raw
>   harami or the unconditioned ZigZag substrate. `/STRONG-STAT` (P7, live magnitude-percentile) is
>   binding; `/STRONG-HA` (P8) is a disclosed secondary arm. Only the **adverse-target geometry** is
>   varied (OAT); the signal, anchor, favourable target, third barrier, and fills are held at benchmark.
> - **(b) harami-anchor** — honoured. Entry is the **harami confirmation-bar real close** `C`, the
>   family's claimed lead point — *not* the ZigZag trend-change confirmation (the EXP-049 anchor).
> - **(c) position-in-move descriptive-only / never a live filter** — honoured. EXP-050's position
>   metric is not used. The `/ADV-EXTREME` reference extreme is the **running extreme of the
>   in-progress (faded) move as-of entry** — a quantity known at the entry timestamp from completed
>   real bars — never an unconfirmed pivot or future bar.
> - **(d) expectancy / not first-hit `r`** — honoured. The binding endpoint is **median gross
>   per-event expectancy** (P14, ATR-normalised, P15 fills), with first-hit `r` retained as a
>   **disclosed secondary** only. (First-hit `r` is the quantity this lever is *expected* to move off
>   0.50, so it is reported prominently — but it never binds; see §"Metric Denominators".)
> EXP-057 does **not** treat the EXP-049 `r≈0.50` null or the EXP-050 front-loading as evidence
> against the family — those measured the *unconditioned* object.

**Phase / checkpoint:** `2026-06-14-014-ha-harami-substrate-and-capture` (014-B; G0-B PASS 2026-06-15).
**Family / candidate:** `CF-HA-HARAMI-001` (`REGISTERED`, OPEN) · `CF-HA-HARAMI-001/HYP-010` — EXP-057
(registered PLANNED, Phase 014-B batch, `multiplicity-registry.md` line 385). Exercises the registered
branches `CF-HA-HARAMI-001/ADV-EXTREME` and `CF-HA-HARAMI-001/ADV-NONE`.
**Surface role:** Surface read 2 of the 014-B post-lead slate — adverse-target geometry comparison
(the asymmetric lever that can move first-hit `r` off 0.50). Sibling of EXP-056 (favourable-target).
**Governing design:** `014-B-design.md` (§2/§3/§5 surface, §7, §8) + `014-B-D0-addendum.md`
(P14/P15/P16/P20); inherits Phase 014 `design.md` §8 D0 (P1–P13) and the family spec
`candidate-families/harami.md` (Adverse-target variants `/ADV-EXTREME`, `/ADV-NONE`).
**Operator scope decisions (2026-06-16, recorded before any data contact):** see §"Operator decisions".
**Reuses:** the EXP-053/056 conditioned-signal construction and P15/P14 resolver
(`xen.expectancy.live_in_progress_state`, `live_strong_stat`, `adaptive_time_caps_by_epoch`,
`benchmark_barriers`, `resolve_path_ordered`, `realised_returns`, `qualifying_mask`,
`bootstrap_median_distribution`, `median_ci`, `contrast_ci`); the paired-median contrast bootstrap
(`xen.favourable_targets.paired_median_contrast_ci`); ZigZag (`xen.zigzag`), harami (`xen.ha_harami`),
`/STRONG-HA` (`xen.strong_move.annotate_ha_impulse`), confirmation indices (`xen.capture_barriers`).

## Operator decisions (2026-06-16, recorded before any data contact)

- **This is a predeclared adverse-target *sweep*, not a single comparison.** All variants are
  predeclared here; **no post-result variant selection** — every variant is reported and composed by
  P11; final routing is the single 014-B G2.
- **`/ADV-EXTREME` reference = the running extreme of the in-progress (faded) move, as-of entry**
  (its lowest `Low` for a long fade `rd=+1`, its highest `High` for a short fade `rd=−1`, over the
  real domain bars from the in-progress move start through the entry bar inclusive), extended a fixed
  **`0.25 × ATR_entry` buffer** further in the adverse direction. Operator rationale (recorded): a
  reversal fade entered at exhaustion is wrong precisely when the move it fades makes a *new* extreme;
  the stop therefore sits just beyond the most-recent faded extreme. The buffer keeps the stop off the
  exact extreme and prevents a zero-distance degenerate barrier.
- **Both `/ADV-EXTREME` R:R forms run** (the family spec's "optional ≥1:1 R:R constraint"): a **raw**
  form (stop at the buffered extreme, R:R free — typically sub-1:1, tight) and a **≥1:1-constrained**
  form (`adv_dist = max(extreme_adv_dist, fav_dist)`, widened to at least the benchmark 1:1 distance).
  Both predeclared; both reported; composed by P11; no post-result selection between them.
- **Variant set (4):** `BENCH` (1:1 reference) · `ADV-EXTREME-raw` · `ADV-EXTREME-rr1` · `ADV-NONE`.
- **Favourable target is held at benchmark for every variant** (P2: `fav_dist = 0.50 × M_sofar`).
  This is pure OAT on the adverse leg. The favourable-target lever is EXP-056; combining levers is
  EXP-060.

## Slot & ledger accounting (binding)

- **0 candidate slots, 0 TEST reads.** Characterization/diagnostic per the 014-B D0 addendum
  (`014-B-D0-addendum.md` slot & ledger accounting). The `/ADV-EXTREME` and `/ADV-NONE` branches are
  registered but consume a slot only when a future scope activates one as a screening candidate —
  which, per P21, cannot happen before G2 PROCEED_TO_SCREEN.
- **No TEST stratum is read.** All work is on the **TRAIN** slice (first 70% of the first-70% analysis
  set), identical fence to EXP-049/053/054/055/056. No `test-read-ledger.md` tally applies; no entry is
  created. The conditioned HA-harami event population already had its first new-universe TRAIN contact
  in EXP-053 (same definition); no new stratum is opened and the global-holdout seal carries forward
  unchanged. The nested analysis-set **TEST stratum is not read**; the final-30% **global holdout** is
  never loaded, inspected, or touched.
- All work is **gross** (no costs). Detection on HA candles; **every outcome metric on real prices**
  (`RealOpen/High/Low/Close` domain-bar OHLC), never HA prices.

---

## Hypothesis

For the live `/STRONG`-conditioned HA harami (anchored at the harami confirmation-bar close, faded
against the in-progress strong move, favourable target held at the benchmark 50%-of-`M_sofar` level),
**at least one alternative adverse-target geometry** (`/ADV-EXTREME` raw or ≥1:1-constrained;
`/ADV-NONE`) produces **higher gross per-event median expectancy** (P14, ATR-normalised, P15 fills,
real prices) than the **benchmark 1:1 adverse target** (P3), on the binding `/STRONG-STAT` arm, with
the favourable target and third barrier held at benchmark (OAT on adverse geometry).

Falsifiable: if **no** alternative adverse-target variant clears the P11 quorum (≥5 cells over ≥3
instruments with CI_low > 0 on its own expectancy) **and** beats the benchmark variant (variant −
benchmark contrast CI_low > 0 in the quorum), then adverse-target geometry is **not** a lever that
improves conditioned capture on benchmark favourable/third geometry (a valid characterization result
that feeds G2 — never a closure inside 014-B).

## Question

Does changing only the **adverse target** — from the benchmark 1:1 model (`adv_dist = 0.50 × M_sofar`)
to a faded-move-extreme stop (`/ADV-EXTREME`, raw and ≥1:1-constrained) or to no stop at all
(`/ADV-NONE`, fav-target-or-timecap only) — improve the conditioned HA-harami's gross per-event median
expectancy vs the benchmark, per cell and composed across the grid, and which variant (if any) wins?
And does it move first-hit `r` off the EXP-049/053 ≈0.50 null (disclosed secondary, narrative only)?

---

## Scope Boundaries

### Data Views

- **Real domain bars** (5m strict; 15m/30m/1h/2h/4h via `xen.bar_aggregator.aggregate_ohlc`,
  `min_coverage=0.90` — identical to EXP-048/049/053/054/055/056/VAL-004) for the ZigZag substrate,
  confirmed moves, strong-move magnitudes, the in-progress-move extreme (`/ADV-EXTREME`), barriers,
  fills, ATR normalisation, and **all** outcome metrics.
- **Heiken Ashi candles** (`xen.heiken_ashi_generator`, from the same domain bars) for **harami
  detection only** (`xen.ha_harami.detect_ha_harami`, frozen EXP-048 detector). **No HA price enters
  any metric.**

### Event population (the live conditioned signal — identical to EXP-053/054/055/056)

- An HA harami (frozen detector) **AND** the live `/STRONG-STAT` magnitude-percentile filter: the
  in-progress confirmed-ZigZag move's **magnitude-so-far** `M_sofar = |C − start_pivot|` (last
  *confirmed* pivot → harami real close `C`) is **≥ p75** of the trailing-20 confirmed-move magnitudes
  (P7, binding). `/STRONG-HA` (P8: run of `X=3` large-body HA bars, no opposing wick) is a **disclosed
  secondary** arm run through the identical pipeline.
- **Trade / reversal direction** `rd = Direction_k` of the last confirmed move
  (`xen.expectancy.live_in_progress_state`; in-progress trend `= −Direction_k`, so the reversal/fade
  trade is in `rd`). No `/BARCFG` isolation; all qualifying haramis count.
- Construction reuses `xen.expectancy.live_in_progress_state` + `live_strong_stat` — the **same
  functions EXP-053/056 used** — so the binding population is byte-identical to EXP-053's conditioned
  events (verified by population reconciliation).

### Entry anchor

The **harami confirmation-bar real close** `C` (real domain-bar close at the harami timestamp), strictly
before any ZigZag trend-change confirmation. Identical to EXP-053/055/056.

### Adverse-target variants (predeclared sweep; OAT on the adverse leg only)

For every variant the **favourable** target is the benchmark `fav = C + rd·fav_dist`,
`fav_dist = 0.50 × M_sofar` (P2; `xen.expectancy.benchmark_barriers`), and the **third barrier** is the
benchmark P4 adaptive time cap. Variants differ only in the **adverse** level `adv` (and therefore in
`adv_dist = rd·(C − adv)`, the distance from `C` to the stop in the adverse `−rd` direction). Fills are
P15. **Validity rule (all variants with a stop):** an event is *valid* iff `fav_dist > 0` (always true
for the conditioned population, `M_sofar > 0`) **and** `adv_dist ≥ ADV_FLOOR` (a disclosed degeneracy
floor, see §Parameters); events failing it are **excluded-with-record** (a disclosed degenerate count
per cell per variant, mirroring EXP-049/056 degenerate exclusions), never silently clamped.

1. **Benchmark (reference variant, P3 — 1:1):** `adv = C − rd·fav_dist`,
   `adv_dist = fav_dist = 0.50 × M_sofar`. Reproduces the EXP-053 benchmark adverse target via
   `xen.expectancy.benchmark_barriers` — the anchor every alternative is contrasted against. (`r ≈ 0.50`
   expected, replicating EXP-049/053.)

2. **`/ADV-EXTREME` — faded-move running extreme + buffer (raw; R:R free).** Let `faded_extreme` =
   the running extreme of the **in-progress (faded) move** as-of entry, over real domain bars
   `[start_idx+1 … entry_idx]` inclusive (`start_idx` = the bar of the in-progress move start pivot,
   `EndTime_k` from `xen.expectancy.live_in_progress_state.start_epoch`; `entry_idx` = the harami bar):
   - `rd = +1` (long fade): `faded_extreme = min(Low)` over the span; `adv = faded_extreme − 0.25·ATR_entry`.
   - `rd = −1` (short fade): `faded_extreme = max(High)` over the span; `adv = faded_extreme + 0.25·ATR_entry`.
   - `adv_dist = rd·(C − adv) = rd·(C − faded_extreme) + 0.25·ATR_entry`. Because `faded_extreme` is the
     extreme in the adverse `−rd` direction, `rd·(C − faded_extreme) ≥ 0`, so `adv_dist ≥ 0.25·ATR_entry > 0`.
   - **Warmup/availability:** if `start_idx` cannot be located (no in-progress span; `InProgressState.valid`
     false) → event excluded-with-record. If the span has 0 intervening bars (entry bar == start bar) the
     extreme is the entry bar's own `Low`/`High` (still defined). `ATR_entry` non-finite/≤0 → excluded.
   - Typically a **tight** stop (`adv_dist ≪ fav_dist`), so R:R < 1:1 and `r` expected **well below 0.50**.

3. **`/ADV-EXTREME` — ≥1:1-constrained (rr1).** Identical construction, then widen to at least the
   benchmark 1:1 distance: `adv_dist = max(adv_dist_extreme, fav_dist)`; `adv = C − rd·adv_dist`.
   Isolates *where the stop sits* (extreme-anchored) from *how wide it is* — this form keeps R:R ≥ 1:1
   like the benchmark, so any expectancy difference vs benchmark is attributable to extreme-anchoring,
   not to a tighter stop.

4. **`/ADV-NONE` — no adverse target.** No adverse barrier exists; the trade can exit **only** at the
   favourable target (if touched within the cap) or at the **third-barrier time cap** (real close at the
   cap bar). Implemented by passing an **unreachable** adverse level to the P15 resolver (`adv = −∞` for
   `rd=+1`, `+∞` for `rd=−1`), so `adv_hit` is never true and the resolver returns `FAV` or `TIMECAP`
   only. No validity/degeneracy exclusion applies (there is no stop); only warmup/`ATR_entry`/censoring
   exclusions apply. This variant deliberately admits large negative timecap returns — that asymmetry is
   the object of measurement.

**Total predeclared adverse-target variants:** 1 benchmark + 2 `/ADV-EXTREME` (raw, rr1) + 1 `/ADV-NONE`
= **4 binding variants**. Each variant runs on the binding `/STRONG-STAT` arm (binding) and the
`/STRONG-HA` arm (disclosed), with both P13 baselines.

### Favourable target, third barrier, fills (benchmark; held fixed)

- **Favourable (P2, benchmark 50%):** `fav = C + rd·0.50·M_sofar` for every variant
  (`xen.expectancy.benchmark_barriers`).
- **Third barrier (P4, benchmark adaptive cap):** per-cell `N = max(6, round(1.5 × median(duration_bars
  of the trailing 20 moves confirmed strictly before the harami)))` real bars after entry;
  `< 5` trailing durations → warmup-excluded (no barrier). Reuse
  `xen.expectancy.adaptive_time_caps_by_epoch`.
- **Fill model (P15, method standard):** when a single domain bar could touch more than one level, fills
  resolve in path order — bullish bar (`Close ≥ Open`): `Open → Low → High → Close`; bearish
  (`Close < Open`): `Open → High → Low → Close`. TIMECAP exits at the cap bar's real close;
  `DATA_CENSORED` (window truncated by the TRAIN/data edge before resolution) carries no exit price and
  is excluded. Reuse `xen.expectancy.resolve_path_ordered`. Documented approximation; disclosed in every
  result.

### Parameters (all frozen D0; no tuning)

ZigZag Wilder ATR(14), `ATR_MULT = 1.0` (P1); `/STRONG-STAT` trailing-20, ≥p75 (P7); `/STRONG-HA` `X=3`
(P8); benchmark favourable `X = 50%` of `M_sofar` (P2); benchmark adverse 1:1 (P3); time-cap `(k=1.5,
window=20, floor=6, statistic=median)` (P4); ATR-normalisation divisor = Wilder ATR(14) at the harami
entry bar (P14); bootstrap `b = round(m^(1/3))`, `N_BOOT = 10_000`, fixed seed (P14). **New predeclared
adverse-target parameters (this scope):** `/ADV-EXTREME` buffer `= 0.25 × ATR_entry`; degeneracy floor
`ADV_FLOOR = 0.10 × ATR_entry` (a stop closer than 0.1 ATR to `C` is excluded-with-record — applies to
the raw `/ADV-EXTREME` form only, since `BENCH`/`rr1` are ≥ `fav_dist` and `/ADV-NONE` has no stop);
`/ADV-NONE` unreachable-stop sentinel `∓∞` by direction. None is tuned against outcomes; sensitivity is
not swept beyond the predeclared variant set.

### Instruments / cells

The **99-cell EXP-049/053/054/055/056 member grid**: 17 instruments × {5m,15m,30m,1h,2h,4h} minus the 3
COVERAGE_EXCLUDED cells (US500-4h, JP225-2h, JP225-4h). Per-cell first, then **P11** composition (≥5
cells over ≥3 instruments) for any "winning variant" claim. Full-grid breadth required by P11 and the
"no blanket assumptions" principle. DE30 carries the truncated-coverage disclosure.

### Time range

Full dataset, nested chronological split. **TRAIN only** = first 70% of the first-70% analysis set (per
cell, F01 file-order-prefix convention identical to EXP-049/053/054/055/056:
`train_end_ts` = last `CloseTime` of the first `int(int(total_rows*0.7)*0.7)` file-order 1-minute rows).
TEST (last 30% of the analysis set) and the final-30% **global holdout** are **not** read.

### Baselines (P13 / P20 — disclosed secondaries)

- **Matched-count random in-regime timestamps** (same cell/regime/direction, EXP-021/027 exclusion
  convention) run through the **identical adverse-target + barrier + resolver pipeline** for each
  variant — does a given adverse geometry beat random entries under the same geometry?
- **MA(20,50) segmentation** (alternative trend substrate, EXP-050/053 baseline): conditioned-harami
  expectancy under MA-segmented moves for each variant, disclosed.
- Baselines are disclosed secondaries; the binding readout is each variant's own expectancy and the
  variant − benchmark contrast.

### Look-ahead / causality discipline (binding)

- ZigZag pivots are future information until confirmed. The signal (harami + `/STRONG-STAT`), `M_sofar`,
  the favourable target, the time cap, and the `/ADV-EXTREME` faded-move extreme use **only** confirmed,
  completed prior moves and **real bars at or before the entry bar** — never an unconfirmed pivot or any
  future bar. The in-progress-move extreme spans `[start_idx+1 … entry_idx]`, all `CloseTime ≤ C`'s bar
  (the start pivot `EndTime_k` is the terminal pivot of a move *confirmed* at or before entry); it is a
  causal running extreme, not the descriptive position-in-move metric (EXP-050) and not an unconfirmed
  end pivot.
- Excursion scans read only bars `[entry_idx+1, cap]`, fenced `CloseTime ≤ train_end_ts`; an event whose
  window is truncated by the TRAIN edge before resolution is `DATA_CENSORED` (excluded, disclosed),
  never measured against truncated data.
- Ordering/alignment by `CloseTime`, never bar index across views.

### Real-price outcome discipline

Harami detected on HA candles; `M_sofar`, the in-progress-move extreme, ATR normalisation, fav/adv
levels, fills, expectancy, `r`, win rate, and censoring all on real domain-bar OHLC. **No HA price in
any metric.**

### Exclusions

- No costs (gross only).
- **Adverse-target geometry only.** No `/VPTARGET`/`/MAGTARGET` (EXP-056 — favourable held at benchmark
  50%), no `/THIRD-EVENT`/`/THIRD-TIME` (EXP-058), no `/EXIT-PARTIAL`/`/EXIT-TRAIL-STRUCT` (EXP-059), no
  combined system (EXP-060). No `/BARCFG`/`/CONFIRM` overlays; no position-in-move *filter*.
- No parameter tuning; **no post-result variant selection** (all predeclared variants reported); no gate
  adjudication (single G2 after the full 014-B slate — EXP-057 emits a characterization readout only).
- No TEST or holdout contact; no candidate slot; no TEST read.

## Success / Failure Criteria

All criteria are **gross**, per-cell first, composed by **P11** (≥5 cells over ≥3 instruments). The
binding endpoint is **median per-event gross expectancy** `E_cell` (ATR units, P15 fills), on the
**`/STRONG-STAT` arm**; per-cell viable iff **CI_low > 0** (regime-clustered moving-block bootstrap,
one-sided 95%) **AND ≥ 30 qualifying events**.

- **EVIDENCE_FOR (an adverse-target lever helps):** ≥1 alternative variant **(a)** clears P11 on its own
  median expectancy **AND (b)** beats the benchmark variant on the **variant − benchmark contrast**
  (paired contrast CI_low > 0 on the common qualifying-event subset) within the P11 quorum (matched
  cells). The winning variant(s) and their margin over benchmark are the deliverable; no candidate
  registration (G2 only).
- **EVIDENCE_AGAINST (adverse geometry is not a lever):** no alternative variant both clears P11 and
  beats the benchmark contrast. Recorded as a measured-negative characterization; routing deferred to
  G2 across the full slate.
- **INCONCLUSIVE (power-limited):** fewer than the P11 quorum of cells reach ≥30 qualifying events on
  the variants of interest (degeneracy/warmup/censoring exclusions deplete counts), no correctness
  failure. Disclosed; never defaulted to a ratio.
- **SUBSTRATE/METHOD_DEFECT:** any determinism, causality, or invariant failure → fix before reporting.
  (Invariant checks include: benchmark variant reproduces EXP-053 per-cell expectancy and `r≈0.50`
  to tolerance; `ADV-EXTREME-raw` `adv_dist ≤ ADV-EXTREME-rr1` `adv_dist` event-wise; `/ADV-NONE`
  produces 0 ADV outcomes; population reconciliation vs EXP-053 exact.)

The deliverable label is **ADVERSE_TARGET_CHARACTERISED** carrying the per-cell + P11 readout for every
variant, the EVIDENCE_* classification, the benchmark contrast per variant, both filter arms, both P13
baselines, and all disclosed secondaries (first-hit `r` per variant — the off-0.50 narrative, win rate,
mean, TIMECAP/censoring fraction, degeneracy/warmup exclusion counts, `/STRONG-HA` arm, MAD arm). No
phase closure or candidate registration here.

## Complexity Budget

- **Max distinct statistical methods: 4** — (1) regime-clustered moving-block bootstrap CI on a
  variant's median expectancy per cell (`xen.expectancy.bootstrap_median_distribution` + `median_ci`);
  (2) same on each P13 baseline; (3) variant − benchmark paired-median contrast CI
  (`xen.favourable_targets.paired_median_contrast_ci`, common qualifying-event subset); (4) variant −
  baseline contrast CI (`xen.expectancy.contrast_ci`). These four methods are applied across the
  predeclared adverse-target variant set (a parameterised sweep over one experiment, not new methods
  per variant) — consistent with the 014-B surface design and the EXP-056 precedent.
- **Max visualisations: 5** — (i) per-variant median-expectancy forest/CI per cell vs benchmark;
  (ii) variant − benchmark contrast heatmap (variants × cells, or a per-variant composition summary);
  (iii) expectancy distribution by variant (pooled); (iv) P11 composition / "wins-over-benchmark" map
  across variants; (v) per-variant first-hit `r` vs benchmark (the off-0.50 narrative) and per-cell
  qualifying-event / exclusion-fraction map. Secondary tables to CSV.
- **Max new code modules: 1** — a bounded **adverse-target geometry** helper (`adverse_targets.py` or a
  bounded extension of `xen.expectancy`/`xen.favourable_targets`) supplying: the causal faded-move
  running-extreme scan over `[start_idx+1 … entry_idx]`, the `/ADV-EXTREME` raw/rr1 adverse-level
  builders (buffer + degeneracy floor + ≥1:1 widen), and the `/ADV-NONE` unreachable-sentinel builder.
  The resolver, fills, realised returns, qualifying mask, median bootstrap, and contrasts are **reused**
  from `xen.expectancy`/`xen.favourable_targets`; ZigZag, harami, strong-move, time-cap, confirmation-
  index, and the in-progress-state machinery are reused. Orchestration in `code/run_experiment.py`.

## Metric Denominators & Zero-Baseline

- **Per-event realised gross return** (ATR units) is defined for every **qualifying** event of a variant
  — those with a built barrier (valid `adv_dist ≥ ADV_FLOOR` for stopped variants; `/ADV-NONE` always
  has a built window) whose outcome is `FAV`, `ADV`, or `TIMECAP`. Return = `rd·(exit_price − C)/ATR_entry`
  (`xen.expectancy.realised_returns`), where `exit_price` is the P15 path-ordered fill (target level for
  FAV/ADV; cap-bar real close for TIMECAP) and `ATR_entry` = Wilder ATR(14) at the harami entry bar.
- **Per-cell endpoint (binding):** `E_cell = median` over the variant's qualifying-event return
  population (`xen.expectancy.qualifying_mask`). `DATA_CENSORED`, warmup-excluded, and degeneracy-excluded
  (`adv_dist < ADV_FLOOR`) events are **excluded** from the median and **disclosed as counts** per cell
  per variant.
- **Zero-baseline / power:** a cell with **< 30 qualifying events** for a variant is
  **NOT_VIABLE-by-power** for that variant (non-reportable for its readout), never an undefined or
  infinite ratio. Conditioning + per-variant degeneracy/warmup exclusions reduce counts vs the
  unconditioned base; depleted cells are disclosed.
- **First-hit `r`** is computed and reported per variant as a **disclosed secondary** (the lever's
  expected effect): `r = n_FAV / (n_FAV + n_ADV)` over resolved FAV/ADV events, with TIMECAP excluded
  from the `r` denominator (EXP-049 convention). For `/ADV-NONE`, `n_ADV = 0` so `r = 1.0` by
  construction where any FAV occurs — reported with that explicit caveat (a degenerate `r`, which is
  exactly why `r` is non-binding and expectancy binds). `r` never enters viability.
- **Disclosed secondaries (never binding):** first-hit `r` per variant; mean per-event return; win rate
  (fraction with return > 0); TIMECAP/censoring fraction; per-variant degeneracy/warmup exclusion counts;
  the `/STRONG-HA` arm; both P13 baselines; the MAD `/STRONG-STAT` sensitivity arm.

## Data Requirements

Per cell (instrument × domain), TRAIN slice only: lazy `pl.scan_parquet`; read total row count;
`analysis_rows = int(total_rows*0.7)`, `train_rows = int(analysis_rows*0.7)`; collect only the first
`train_rows` file-order 1-minute rows (F01 prefix; never sort/collect the full file, never read TEST or
holdout); assert chronological; `train_end_ts` = last `CloseTime`. Aggregate each member domain (5m
strict; others `min_coverage=0.90`); fence to `CloseTime ≤ train_end_ts`; generate HA candles; run
`xen.zigzag.generate_zigzag(bars, atr_period=14, atr_mult=1.0)` → confirmed moves +
`xen.capture_barriers.confirm_indices`; detect haramis on HA candles aligned by `CloseTime`; build the
live in-progress state + `/STRONG-STAT`/`/STRONG-HA` conditioning (`xen.expectancy`); for each
qualifying harami compute the benchmark favourable target and adaptive cap, then each predeclared
adverse variant (BENCH 1:1, ADV-EXTREME-raw, ADV-EXTREME-rr1, ADV-NONE) — including the causal
faded-move extreme scan from the in-progress start index to the entry index — resolve each variant under
P15, compute ATR-normalised gross returns, bootstrap the per-cell median per variant, compute both P13
baselines through the identical per-variant pipeline, compose by P11; second full pass for determinism.
`tqdm` over the 99-cell grid; bounded per-cell memory (do not retain all domain frames or all bootstrap
draws); fixed seed; deterministic. Outputs (`results/`): `per_cell_expectancy.parquet` (per cell ×
variant: median/CI expectancy, paired contrast vs benchmark, n_qualifying, exclusion counts, `r`, win
rate, TIMECAP fraction, baseline medians/contrasts, viability flag); `adverse_target_map.csv` (binding
`/STRONG-STAT` summary per variant); `secondary_map.csv` (`/STRONG-HA`, MAD arm, baselines, `r`);
`composition_readout.json` (per-variant P11, wins-over-benchmark, EVIDENCE_* fork);
`population_reconciliation.csv` (binding conditioned population vs EXP-053; benchmark expectancy/`r` vs
EXP-053); `run_metadata.json` (seed, frozen + new predeclared constants, EXP-053 source paths/hashes).
Bounded plots from the collected per-cell summaries (no reloads).

### Standard Loading Pattern (TRAIN slice, per cell)

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob(f"timebars/timebars_{symbol}_*.parquet"))[-1]

scan = pl.scan_parquet(path)                      # F01 file-order prefix; no full sort/collect
total_rows = int(scan.select(pl.len()).collect().item())
analysis_rows = int(total_rows * 0.7)             # first 70% = analysis set
train_rows = int(analysis_rows * 0.7)             # first 70% of analysis = TRAIN
train_bars = scan.slice(0, train_rows).collect()  # TEST + holdout never sliced
# assert chronological; train_end_ts = train_bars["CloseTime"].max()
# domain aggregation (xen.bar_aggregator) for 5m strict / others min_coverage=0.90
```

## Suggested Direction

Compose existing primitives; the only new code is the bounded adverse-target geometry helper (causal
faded-move running-extreme scan + raw/rr1 adverse-level builders + `/ADV-NONE` sentinel). Pipeline per
cell: `xen.zigzag.generate_zigzag` → confirmed moves + `xen.capture_barriers.confirm_indices`;
`xen.heiken_ashi_generator` + `xen.ha_harami.detect_ha_harami` → harami entry bars (aligned by
`CloseTime`); `xen.expectancy.live_in_progress_state` (supplies `start_epoch`/`rd`/`m_sofar`) +
`live_strong_stat` → the binding conditioned population (identical to EXP-053; cross-checked by
`population_reconciliation`); `xen.strong_move.annotate_ha_impulse` → the `/STRONG-HA` arm. For each
qualifying harami: compute the benchmark favourable target + cap (`xen.expectancy.benchmark_barriers`,
`adaptive_time_caps_by_epoch`); compute each adverse variant's `adv` (new helper; faded-move extreme
located by mapping `start_epoch`/entry epoch to bar indices, scanned causally); resolve each variant via
`xen.expectancy.resolve_path_ordered` → `realised_returns` → `qualifying_mask`; bootstrap per-cell median
per variant (`xen.expectancy.bootstrap_median_distribution`, `median_ci`); paired contrast vs benchmark
(`xen.favourable_targets.paired_median_contrast_ci`) and vs baselines (`xen.expectancy.contrast_ci`).
Emit the layered per-variant P11 / wins-over-benchmark / EVIDENCE_* readout; **do not adjudicate §8**
(single 014-B G2 after the full slate).
