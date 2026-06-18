# Experiment: EXP-066 — MA(20,50)-Substrate Position-Management Exits (Conditioned HA Harami; `/EXIT-PARTIAL`, `/EXIT-TRAIL-STRUCT`, individually and combined; **Dual Conditioning Object: Hybrid and Native**, Phase 015 Surface S3)

> **Re-run under `D0-amendment-001-dual-parallel-substrate.md` (2026-06-17).** The prior EXP-066
> scope measured the 12-arm position-management exit grid labelled *hybrid* but reconciled its
> benchmark arm to EXP-061 `M0` — which is the **native** object (MA-segment `/STRONG-STAT`,
> 8360-class), not the hybrid object (ZigZag-`/STRONG-STAT`, 3202-class). That is the propagated
> labelling defect the amendment corrects, and its old Exclusions wrongly deferred *all* MA-native
> conditioning to EXP-068. This re-run emits the full 12-arm position-management exit grid **for
> both conditioning objects individually** (separate arms, separate matched-random nulls, separate
> per-cell viability, separate P11 composition, separate EVIDENCE fork — never pooled) and
> supersedes the prior single-object EXP-066 scope in place. EXP-066 was **paused** (no
> `results/`, no code); resumption is dual-object from the start, so no prior result is overturned
> — only the scope/plan.

> **Mandatory-reading precondition (Phase 015, binding — inherited from 014-B).**
> `../../docs/experiments-docs/checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/014-A-conditioning-gap-and-validation-lessons.md`
> was read in full before this scope was written. EXP-066 is the Phase 015 **position-management
> exits** surface read (S3; mirrors EXP-059) on the **MA(20,50) substrate**, on **both**
> conditioning objects. The four mandatory rules are honoured, recorded so Stage 4 can check:
> - **(a) conditioning** — honoured, **and now disambiguated** (Amendment 001). Two live
>   `/STRONG-STAT`-conditioned HA-harami objects are measured individually over the **same** MA(20,50)
>   favourable/adverse/cap geometry, varying **only the position-management exit machinery**
>   (favourable-side scaled exits and/or adverse-side structure trailing): **hybrid** (filter on
>   the in-progress confirmed *ZigZag* move — entry population byte-identical to
>   EXP-053/060/061's hybrid `H0`; the genuinely-new object for the exit axis) and **native**
>   (filter recomputed on the in-progress confirmed *MA segment* — the population EXP-061's `M0`
>   measured; reconciles to EXP-061 native `M0` / EXP-060B `BENCH-MA`). `/STRONG-STAT` (P7) is
>   binding in each; `/STRONG-HA` (P8) is a disclosed-secondary arm (deferred for runtime — see
>   Exclusions). Only the **position-management exit machinery** is varied (OAT); the signal,
>   anchor, **third barrier** (MA benchmark adaptive cap), and favourable/adverse MA benchmark
>   levels are held wherever an exit layer does not replace them. Each object's
>   matched-random-on-MA control is a deliberate **null** (binding per P5), not a signal claim.
>   The two objects are never pooled.
> - **(b) harami-anchor** — honoured. Entry is the **harami confirmation-bar real close** `C` in
>   both objects. A forward MA-segment confirmation (reversal-event leg) and the secondary-ZigZag
>   pivots (trailing stop) are used only as *exit* events, never as the entry, never an
>   unconfirmed pivot/crossover.
> - **(c) position-in-move descriptive-only / never a live filter** — honoured. EXP-050's
>   position metric is not used. Every exit trigger (first-profitable-close, fractional targets,
>   reversal event, structure trailing stop) is acted on at a bar known forward-in-time after
>   entry.
> - **(d) expectancy / not first-hit `r`** — honoured. The binding endpoint is the Phase 015
>   **median** gross per-event expectancy (P3/P14) of the **position-weighted realised return**
>   (multi-leg exits collapse to one per-event number), computed **per object individually**.
>   First-hit `r` is undefined/secondary for multi-leg exits and reported only for the single-leg
>   BENCH arm; win rate and exit-reason composition are disclosed secondaries. The **mean** (raw +
>   10% trimmed + worst-5% tail-share, each CI'd) is the P4 diagnostic co-primary. This is
>   exactly the metric P14 chose *because* partial exits and trailing stops cannot express value
>   under a first-hit rate (lessons §8.6) — the experiment that lever was designed for.
> EXP-066 does **not** treat the EXP-049 `r≈0.50` null or EXP-050 front-loading as evidence
> against the family — those measured the *unconditioned ZigZag* object.

**Phase / checkpoint:** `2026-06-17-015-ma-substrate-conditioned-harami-full-surface` (Phase 015; **G0 PASS 2026-06-17**).
**Family / candidate:** `CF-HA-HARAMI-001` (`REGISTERED`, OPEN) · Phase 015 surface **S3** ·
`CF-HA-HARAMI-001/HYP-019` — EXP-066 (Phase 015 batch, `multiplicity-registry.md` line 480, "hybrid + native (S3),
individually"). Exercises the registered branches `CF-HA-HARAMI-001/EXIT-PARTIAL` (P17) and `CF-HA-HARAMI-001/EXIT-TRAIL-STRUCT` (P18) on the
registered `CF-HA-HARAMI-001/MA-SUBSTRATE` (both modes `hybrid` and `native`, parallel first-class per
Amendment 001).
**Registry precondition (satisfied):** `MA-SUBSTRATE` + **both** conditioning modes (`hybrid`, `native`, parallel
first-class per `D0-amendment-001`) **REGISTERED** (Phase 015 batch, 2026-06-17, G0 PASS); `/EXIT-PARTIAL`,
`/EXIT-TRAIL-STRUCT`, the benchmark geometry, and the matched-random baseline pre-exist (Phase 014 / 014-B). HYP-019/EXP-066
is the listed plan. **No new countable item is introduced here.**
**Surface role:** Surface read 3 of the Phase 015 post-lead slate — position-management exits on MA, on **both**
objects. EXP-061 (L1) established the **native** MA benchmark geometry is signal-attributable (EVIDENCE_FOR;
`M0 ≻ RM0` generalised beyond the champion, 8 cells) while the **hybrid** object generalised in only 1 cell
(EVIDENCE_AGAINST) — so the exit question must be read **per object**. EXP-059 found `/EXIT-PARTIAL` V2A
EVIDENCE_FOR on ZigZag (53 wins/17 instruments), and EXP-060B's champion was V2A × `/ADV-NONE`. This experiment
asks, **per object**, whether scaling out of the favourable side and/or trailing the adverse side on MA structure
captures more of the MA-substrate available move than the single MA-benchmark exit, and whether any gain is
signal-attributable (beats its same-object RM-on-MA null, P5). Its survivors feed the combined-champion EXP-067
(hybrid) / EXP-068 (native) and G-015. The surface runs **regardless** of the lead (P9). **No closure or
candidate registration here.**
**Governing design / D0:** `design.md` (§3 objective; §5 slate S3; §7 G-015 criteria, judged per object) +
`D0-predeclarations.md` (P1 substrate; **P2 both objects parallel/individual**; P3 median binding + fixed seed;
P4 mean diagnostic; **P5 matched-null per object every read**; P6 non-4h composition; P8 OAT grids reused unchanged;
P9 slate; P10 power; **P12 reconciliation roles — native `M-BENCH`↔EXP-061 `M0`/EXP-060B 1e-9, hybrid `H-BENCH`↔EXP-061 `H0` 1e-9 +
EXP-053 population**) + `D0-amendment-001-dual-parallel-substrate.md`. Inherits 014-B P14/P15/P16/P17/P18/P20 and the family
spec `candidate-families/harami.md` (position-management branches).
**Reuses (no new `xen/` module expected):** **EXP-064's dual-object `code/run_experiment.py` is the closest
structural fork base** (it already runs per-variant OAT loops on **both** object populations — hybrid `H0` via
`bench_signal_arm`'s `cond_mask` override and native `M0` — with per-object RM nulls and the P4 mean/trim/tail
diagnostic). Changes: swap EXP-064's per-variant **favourable-target** axis for the per-arm **position-management
exit** axis — composing `xen.position_exits` (multi-leg P15 resolver + structure trailing builder/resolver) fed the
MA-substrate fav/adv levels and the EXP-058/065 `third_event_caps` forward-locator pointed at MA segments for the
reversal-event leg; `xen.expectancy.*` (`live_in_progress_state`, `live_strong_stat`, `adaptive_time_caps_by_epoch`,
`benchmark_barriers`, `resolve_path_ordered`, `realised_returns`, `qualifying_mask`, `bootstrap_median_distribution`,
`bootstrap_mean_distribution`, `median_ci`, `contrast_ci`); `xen.favourable_targets.paired_median_contrast_ci`;
ZigZag (`xen.zigzag` — primary `atr_mult=1.0` conditioning mask (hybrid) + secondary `atr_mult=0.5` trailing
structure), harami (`xen.ha_harami`), `/STRONG-HA` (`xen.strong_move.annotate_ha_impulse`), confirmation indices
(`xen.capture_barriers`).

## Operator-inherited design decisions (Phase 015 D0 P8: 014-B OAT grids reused unchanged on MA)

Per D0 P8, the EXP-059 exit-variant grid is reused **unchanged**; only the substrate that supplies the geometry
changes (ZigZag → MA(20,50)). The EXP-059 operator decisions therefore carry across **both objects**:

- **All exit schemes split the full entry weight into exactly 3 equal legs (`w = 1/3` each)** (P17); the
  single-leg benchmark is `w = 1` on one leg.
- **Substrate-dependent reversal-event definition (the one substitution P8 forces).** EXP-059's reversal-event
  leg used the next **primary-ZigZag** `Direction == rd` confirmation. On the MA substrate the analogous structural
  completion is the **next confirmed MA segment** with `Direction == rd` and `ConfirmTime > entry` (the
  EXP-058/EXP-065 MA-seg `/THIRD-EVENT` convention) — *or* the next `/STRONG`-conditioned HA harami whose reversal
  direction `== −rd` (the substrate-independent opposing-harami arm, unchanged). Reversal event = first of these
  two; exit at that confirmation bar's real close, bounded by the MA benchmark cap.
- **Trailing-stop structure is the secondary `atr_mult=0.5` ZigZag — a real-bar construct, substrate-independent
  (EXP-059 MA-seg-baseline convention).** The structure trailing stop stays the secondary `atr_mult=0.5` ZigZag
  for **both** objects (it is *not* re-defined as a faster MA). A secondary-MA trailing structure is **out of
  scope** — a future registered branch only if the surface earns it. Disclosed.
- **Favourable target and the third barrier (MA adaptive cap) are held at the MA benchmark for every arm.**
  Pure OAT on the position-management exit machinery. **Consequence disclosed:** because the benchmark cap bounds
  the forward scan, the reversal-event legs (V1 leg-3, V2C runner) and the runner target (V2B 1.5×) are bounded
  by the MA cap in most cells; many will exit at the time cap rather than the reversal/extended trigger. This is
  the intended clean-OAT measurement.
- **Combined arms (`/EXIT-PARTIAL` ⊕ `/EXIT-TRAIL-STRUCT`):** favourable side = the partial-exit legs, adverse
  side = the structure trailing stop (1:1 init, ratchet) replacing the benchmark 1:1 stop that binds open legs;
  third barrier at MA benchmark. Each of the 4 partial-favourable schemes (V1, V2A, V2B, V2C) combined with the
  trailing adverse → 4 combined arms.

**Full predeclared binding-arm set (12 arm types per object; 24 binding arm instances total; `H-*` = hybrid, `M-*` = native; each on that object's binding `/STRONG-STAT` population, with `/STRONG-HA` disclosed and that object's matched-random-on-MA null binding per P5):**

| # | Arm type | H-arm / M-arm id | Favourable side | Adverse side | Third barrier | Notes |
|---|----------|------------------|-----------------|--------------|---------------|-------|
| 1 | BENCH | `H-BENCH` / `M-BENCH` | 50% fav (1 leg) | 1:1 stop | MA adaptive cap | reference; `M-BENCH` reproduces EXP-061 `M0` / EXP-060B BENCH-MA; `H-BENCH` reproduces EXP-061 `H0` |
| 2 | PARTIAL-V1 | `H-PARTIAL-V1` / `M-PARTIAL-V1` | legs {first-profit-close, 50% fav, reversal-event} | 1:1 stop (all open legs) | MA adaptive cap | event-trigger partials |
| 3 | PARTIAL-V2A | `H-PARTIAL-V2A` / `M-PARTIAL-V2A` | legs at {1/3, 2/3, 3/3}×fav_dist | 1:1 stop | MA adaptive cap | even-thirds (the EXP-060B champion fav side) |
| 4 | PARTIAL-V2B | `H-PARTIAL-V2B` / `M-PARTIAL-V2B` | legs at {0.5, 1.0, 1.5}×fav_dist | 1:1 stop | MA adaptive cap | runner to 1.5× |
| 5 | PARTIAL-V2C | `H-PARTIAL-V2C` / `M-PARTIAL-V2C` | legs {1/3, 2/3}×fav_dist + reversal-event runner | 1:1 stop | MA adaptive cap | fixed+reversal runner |
| 6 | TRAIL-PURE | `H-TRAIL-PURE` / `M-TRAIL-PURE` | none (let it run, 1 leg) | structure trail (1:1 init) | MA adaptive cap | primary trailing intent |
| 7 | TRAIL-TP-INIT | `H-TRAIL-TP-INIT` / `M-TRAIL-TP-INIT` | 50% fav (1 leg) | structure trail (1:1 init) | MA adaptive cap | TP + trail |
| 8 | TRAIL-TP-NOINIT | `H-TRAIL-TP-NOINIT` / `M-TRAIL-TP-NOINIT` | 50% fav (1 leg) | structure trail (no init stop) | MA adaptive cap | TP + trail, unstopped early |
| 9 | COMBINED-V1 | `H-COMBINED-V1` / `M-COMBINED-V1` | V1 partial legs | structure trail (1:1 init) | MA adaptive cap | partial fav + trail adverse |
| 10 | COMBINED-V2A | `H-COMBINED-V2A` / `M-COMBINED-V2A` | V2A partial legs | structure trail (1:1 init) | MA adaptive cap | |
| 11 | COMBINED-V2B | `H-COMBINED-V2B` / `M-COMBINED-V2B` | V2B partial legs | structure trail (1:1 init) | MA adaptive cap | |
| 12 | COMBINED-V2C | `H-COMBINED-V2C` / `M-COMBINED-V2C` | V2C partial legs | structure trail (1:1 init) | MA adaptive cap | |

The trailing-stop monotone ratchet rule is the EXP-059 P18 rule, unchanged for both objects: for a long fade
(`rd=+1`) on a newly confirmed secondary-ZigZag **pivot high**, `stop ← max(stop, most-recent confirmed
secondary pivot low)`; for a short fade (`rd=−1`) on a newly confirmed **pivot low**, `stop ← min(stop,
most-recent confirmed secondary pivot high)`. The stop in force at any bar uses only secondary-ZigZag moves
with `ConfirmTime ≤ CloseTime` (causal — the stop moves at the confirmation bar, never the retroactive pivot
bar). This ratchet rule is **substrate-independent** and applies identically to both objects.

## Slot & ledger accounting (binding)

- **0 candidate slots, 0 TEST reads.** Characterization/diagnostic per the Phase 015 D0 (P11). No countable
  item is introduced: `MA-SUBSTRATE` + both `hybrid`/`native` modes are registered at G0; `/EXIT-PARTIAL`,
  `/EXIT-TRAIL-STRUCT`, the benchmark geometry, and the matched-random nulls pre-exist. A slot is consumed only
  at a G-015 PROCEED on a future scope.
- **No TEST stratum is read.** All work on the **TRAIN** slice (first 70% of the first-70% analysis set; F01
  file-order prefix; identical fence to EXP-049/053–065). Hybrid population byte-identical to EXP-053/060/061
  `H0`; native population byte-identical to EXP-060B/061 `M0`; no new stratum opened; `test-read-ledger.md`
  requires no entry; global-holdout seal carries forward. **Forward scans** (reversal-event legs, runner targets,
  trailing-stop ratchet, time caps) run only within the TRAIN slice and are clipped to the TRAIN data edge — a
  window extending past `train_end_ts` is `DATA_CENSORED`, never resolved against TEST/holdout rows.
- All work **gross**; detection on HA candles; **all outcome metrics on real-price OHLC**; MA(20,50) on **real
  close**. No HA price enters any metric (the opposing-harami reversal arm uses HA candles only to *locate* the
  exit bar, then exits at that bar's **real** close).

---

## Hypothesis

On the `/STRONG-STAT`-conditioned HA harami, **for each conditioning object individually** (hybrid and native;
never pooled), 99-cell TRAIN grid, MA(20,50) substrate, entered at the harami confirmation-bar real close `C`
and faded against the in-progress MA segment, third barrier held at the MA benchmark adaptive cap, favourable and
adverse targets at the MA benchmark (OAT on the **position-management exit machinery only**): **at least one
position-management exit scheme** — favourable-side scaled exits (`/EXIT-PARTIAL` V1, V2A, V2B, V2C), adverse-side
structure trailing (`/EXIT-TRAIL-STRUCT` PURE, TP-INIT, TP-NOINIT), or their combination (COMBINED-V1/V2A/V2B/V2C)
— produces **higher gross per-event median expectancy** (P3/P14, ATR-normalised, position-weighted realised return,
P15 fills, real prices) than the **MA benchmark single fixed exit** (50% fav / 1:1 stop / MA adaptive cap, single
leg) **for that object**, and that winning arm is **signal-attributable** (beats its own same-object
matched-random-on-MA null, P5).

The two objects are judged **individually, never pooled** (P2); the phase-level reading of this lever is the
**stronger object's** outcome (consistent with EXP-061: native is the object that expresses the edge), with the
other object's result documented in parallel.

**Falsifiable, per object:** if **no** position-management arm simultaneously (a) is median-viable per cell,
(b) beats its same-object matched-random-on-MA null (`arm − RM` contrast CI_low > 0), and (c) beats that
object's benchmark MA arm (`arm − benchmark` paired contrast CI_low > 0), all composed by P11 with the P6
non-4h breadth rule **for that object**, then position-management exit machinery is **not** an MA-substrate lever
that improves conditioned capture for that object (a valid characterization result feeding G-015 — never a
closure inside Phase 015; the surface runs regardless, P9).

## Question

On the MA substrate, **for each object (hybrid, native)**, does replacing the benchmark single fixed exit with
**scaled favourable take-profits** (event-trigger or fraction-of-target legs, with or without a reversal-event
runner) and/or an **adverse-side market-structure trailing stop** (0.5×ATR ZigZag, with or without a fixed
favourable target) raise the conditioned HA-harami's gross per-event median expectancy vs that object's MA
benchmark, per cell and composed across the grid, beat the same-object matched-random-on-MA null, and which
scheme (if any) wins — per object? Does the EXP-060B-champion favourable side (V2A) reproduce its EXP-059
ZigZag EVIDENCE_FOR on MA — for the **native** object (which expresses the edge) as well as the **hybrid**
object? Does any scheme also move the **mean** (P4 diagnostic) toward positive — per object? At what cost in
qualifying-event **count** and in **exit-reason composition** (disclosed secondaries)? Does the picture differ
between hybrid and native objects?

---

## Scope Boundaries

### Data Views

- **Real domain bars** (5m strict; 15m/30m/1h/2h/4h via `xen.bar_aggregator.aggregate_ohlc`,
  `min_coverage=0.90`) for the MA(20,50)-crossover substrate (`ma_segment_moves`), the **secondary trailing
  ZigZag** (`atr_mult=0.5`), the **primary ZigZag** (`atr_mult=1.0`, hybrid conditioning mask + disclosed
  contrast), confirmed moves/segments, `/STRONG-STAT` magnitudes (on ZigZag for hybrid / on MA segments for
  native), the MA benchmark third-barrier cap, all barrier/leg/stop levels, P15 fills, ATR normalisation, and
  **all** outcome metrics.
- **Heiken Ashi candles** for **harami detection only** (frozen EXP-048 detector) — including the
  opposing-harami arm of the reversal-event trigger. **No HA price enters any metric.**

### Event population (two conditioning objects, measured individually over the same 12-arm exit grid)

Both objects share the **same** frozen HA-harami detection, the **same** MA(20,50) outcome geometry
(`rd` / `M_sofar` / favourable target / adverse target / MA adaptive cap), and the **same** real bars; they
differ **only** in the `/STRONG-STAT` conditioning filter (P2):

- **Hybrid (`H-*`).** Qualifies iff the harami passes `/STRONG-STAT` p75 on the **in-progress confirmed
  ZigZag move** magnitude-so-far ≥ p75 of the trailing-20 confirmed-ZigZag-move magnitudes (hybrid mode). The
  conditioning mask is **byte-identical to EXP-053/060/061's hybrid `H0` set** (the same `live_in_progress_state`
  / `live_strong_stat` on the ZigZag move, applied through the MA context via the `bench_signal_arm` `cond_mask`
  override). MA supplies only the geometry. **This is the genuinely-new object** for the exit axis (a
  ZigZag-conditioned position-management-exit surface over MA geometry was never computed before Amendment 001).
  Its internal-lineage anchor is **EXP-061 `H0`** (the `H-BENCH` arm reproduces it); its conditioning population
  reconciles to **EXP-053's 3202-class ZigZag-`/STRONG-STAT` set**; it has **no EXP-060B/059 outcome
  back-reconciliation anchor**.
- **Native (`M-*`).** Qualifies iff the harami passes `/STRONG-STAT` p75 on the **in-progress confirmed MA
  segment** magnitude-so-far ≥ p75 of the trailing-20 confirmed-MA-segment magnitudes (recomputed on MA segments;
  causal — only segments confirmed at/before the harami bar). **Population byte-identical to EXP-061 native `M0`
  and EXP-060B `BENCH-MA`**; the `M-BENCH` arm **reconciles to them (1e-9)** — the object the prior (mislabelled)
  EXP-066 scope actually intended. The native MA-native conditioning is the **same** object that expressed the
  85/99 edge in EXP-060B; this is the object for which V2A × `/ADV-NONE` was the champion.

Entry anchor is the harami close `C` in both. The **trade / reversal direction** `rd` and the **MA-segment
magnitude-so-far** `M_sofar` (hence `fav_dist = 0.50·M_sofar`, the MA benchmark levels, and the MA adaptive
cap) come from the **MA(20,50) substrate** (`ma_seg_arm`), exactly the EXP-060/061 construction. The
conditioning filter differs by object but the geometry is the same. Each object's matched-random-on-MA nulls draw
**non-harami** in-MA-regime timestamps, **matched-count to that object's qualifying count per arm**, on
**independent dedicated RNG streams** distinct from the other object's.

### Entry anchor

The **harami confirmation-bar real close** `C`, strictly before any ZigZag/MA trend-change confirmation.
Identical to EXP-053/061.

### Position-management exit arms on MA (predeclared sweep; OAT on the exit machinery only; **per object**)

Notation: `C` = entry close; `rd` = trade direction; `M_sofar` = MA-segment magnitude-so-far;
`fav_dist = 0.50·M_sofar` (MA benchmark); `fav = C + rd·fav_dist`; `adv = C − rd·fav_dist` (MA benchmark 1:1);
`bench_N` = MA benchmark adaptive cap. Every leg/stop is evaluated on **real prices** under the **P15 path model**
(bullish bar `Close ≥ Open`: `O→L→H→C`; bearish: `O→H→L→C`). Every arm's forward scan runs
`[entry_idx+1, entry_idx + bench_N]`, TRAIN-fenced; a window truncated before all legs/the position resolve is
`DATA_CENSORED` (excluded-with-record, disclosed). **Each arm is built and resolved twice — once on the hybrid
population, once on the native population — and reported individually with an `object` tag.**

**Benchmark reference (arm 1) —** single leg, `w=1`: `resolve_path_ordered` with `(fav, adv, bench_N)`. This
arm is the P12 reconciliation target: **`M-BENCH` reproduces EXP-061's `M0` / EXP-060B `BENCH-MA`** per-cell
median + qualifying count to `RECON_TOL = 1e-9`; **`H-BENCH` reproduces EXP-061's `H0`** per-cell median +
qualifying count to `RECON_TOL = 1e-9`.

**`/EXIT-PARTIAL` (arm types 2–5) —** full weight in **3 equal legs** (`w=1/3`). All open legs share the **MA
benchmark 1:1 adverse stop** `adv` (if reached first along the P15 path, every still-open leg exits at `adv`)
and the **MA benchmark time cap** (still-open legs exit at the cap bar's real close). Each leg's favourable
trigger:
- **V1 (arm type 2):** leg-1 = first bar with `rd·(close − C) > 0` → exit at that `close`; leg-2 = `fav` (P15
  intrabar touch); leg-3 = reversal event = first of {**next confirmed MA segment** `Direction==rd` with
  `ConfirmTime>entry`; opposing conditioned harami reversal-dir `−rd` confirmed after entry} → exit at that
  confirmation bar's real `close` (bounded by the MA cap; reuses the `third_event_caps` forward-locator pattern
  pointed at MA segments for the structural arm).
- **V2A (arm type 3):** legs at `{1/3, 2/3, 1} × fav_dist` favourable distance → levels `C + rd·frac·fav_dist`
  (P15 intrabar touch). *(The EXP-060B champion favourable side.)*
- **V2B (arm type 4):** legs at `{0.5, 1.0, 1.5} × fav_dist` favourable distance (the 1.5× leg is a runner).
- **V2C (arm type 5):** legs 1–2 at `{1/3, 2/3} × fav_dist`; leg-3 runner = reversal event (V1 leg-3
  definition).

**`/EXIT-TRAIL-STRUCT` (arm types 6–8) —** single position (`w=1`); adverse side = the monotone structure
trailing stop on the **secondary `atr_mult=0.5` ZigZag** (ratchet rule above, substrate-independent); favourable/
initial-stop per arm:
- **TRAIL-PURE (arm type 6, primary):** no favourable target; initial stop `adv` (MA benchmark 1:1) until the
  first secondary pivot confirms after entry, then ratchet; exit on trailing-stop fill or MA time cap.
- **TRAIL-TP-INIT (arm type 7):** favourable target `fav`; initial stop `adv`; ratchet; exit on fav touch,
  trailing-stop fill, or time cap (P15 path order resolves same-bar fav-vs-stop).
- **TRAIL-TP-NOINIT (arm type 8):** favourable target `fav`; **no stop** until the first secondary pivot
  confirms, then ratchet; exit on fav touch, trailing-stop fill, or time cap.

**Combined (arm types 9–12) —** `/EXIT-PARTIAL` favourable legs (V1, V2A, V2B, V2C respectively) **⊕** the
structure trailing adverse stop (1:1 init, ratchet) replacing the MA benchmark 1:1 stop that binds open legs;
time cap at MA benchmark. Leg favourable triggers exactly as the corresponding partial arm.

**Total predeclared exit arm types per object:** 1 benchmark (BENCH) + 4 `/EXIT-PARTIAL` (V1, V2A, V2B, V2C) +
3 `/EXIT-TRAIL-STRUCT` (PURE, TP-INIT, TP-NOINIT) + 4 `COMBINED` (V1, V2A, V2B, V2C) = **12 binding arm types
per object**; **× 2 objects = 24 binding arm instances total** (reported individually, never pooled). Each arm
runs on the binding `/STRONG-STAT` arm of its object; the `/STRONG-HA` arm is a disclosed secondary (deferred —
see Exclusions). Each arm instance carries its own same-object matched-random-on-MA null (binding, P5).

**Per-event realised return (binding endpoint input).** For every arm instance the per-event realised gross return
is the **position-weighted** sum of leg returns: `R_event = Σ_l w_l · rd·(exit_px_l − C)/ATR_entry`, where each
leg's `exit_px_l` is its P15 fill (favourable level, shared adverse/trailing stop, reversal-event/cap close),
`Σ_l w_l = 1`, and `ATR_entry` = Wilder ATR(14) at the harami entry bar (P14). Single-leg arms (BENCH,
TRAIL-*) are the `w=1` special case. `R_event` is the per-event value fed to the median + mean bootstraps and
the paired contrast, **per object**.

### Matched-random-on-MA null (RM; **binding per P5**, per arm, **per object**)

For **each** arm type **of each object**, a **matched-count random in-regime** control (the EXP-060B
matched-random-in-MA-regime selection, reused unchanged; same cell / direction / regime, valid live MA state,
**matched-count to that object's qualifying count for the arm**, **excluding that object's conditioned-harami
entries**) is run through the **identical arm exit pipeline** on MA. Native nulls are `RM-BENCH / RM-PARTIAL-V1 /
... / RM-COMBINED-V2C`; hybrid nulls are `RH-BENCH / RH-PARTIAL-V1 / ... / RH-COMBINED-V2C`. **Signal-attribution
requires the arm beats its own same-object RM null** (`arm − RM` median contrast CI_low > 0; P5) — elevated from
the EXP-059 disclosed-secondary status to **binding** by Phase 015 P5. The RM draws are **independent** of the
harami events (no common subset). The hybrid and native nulls draw from the **same** MA in-regime pool but are
matched to **different counts** and exclude **different signal entries**, on **disjoint dedicated RNG streams**;
the two objects' contrasts are **never pooled**.

### Parameters (all frozen / predeclared; no tuning)

MA(20,50) on real close (fixed; P1); primary ZigZag Wilder ATR(14), `ATR_MULT=1.0` (hybrid conditioning mask +
disclosed contrast); **secondary trailing ZigZag Wilder ATR(14), `ATR_MULT_TRAIL = 0.5` (P18)**; `/STRONG-STAT`
trailing-20, ≥p75 (P7; on ZigZag for hybrid / on MA segments for native); `/STRONG-HA` `X=3` (P8; disclosed,
deferred); benchmark favourable `X = 50%` of `M_sofar`; benchmark adverse 1:1; benchmark MA adaptive cap
`(k=1.5, window=20, floor=6, statistic=median, min_moves=5)` for every arm; ATR-normalisation = Wilder ATR(14)
at the harami entry bar (P14); bootstrap `b = round(m^(1/3))`, `N_BOOT = 10_000`, **fixed per-cell seed (P3)** —
`np.random.default_rng([BASE_SEED, cell_index, purpose])` with dedicated purposes per object/arm/statistic so the
native `M-BENCH` median path stays byte-identical to EXP-061 `M0` and the hybrid `H-BENCH` path byte-identical to
EXP-061 `H0`. **Position-management parameters (inherited unchanged from EXP-059 P17/P18, applied to both
objects):** 3 equal legs (`w=1/3`); V1/V2C reversal-event = first of {next confirmed MA segment
`Direction==rd`; opposing conditioned harami reversal-dir `−rd`}, bounded by the MA benchmark cap; V2A fractions
`{1/3, 2/3, 1}`; V2B fractions `{0.5, 1.0, 1.5}`; trailing-stop monotone ratchet to the most-recent confirmed
secondary pivot; initial-stop treatments {1:1, none} per arm. None tuned against outcomes; no grid swept beyond
this predeclared set.

### Instruments / cells / time range

The **99-cell EXP-049/053–065 member grid** (17 instruments × {5m,15m,30m,1h,2h,4h} − 3 COVERAGE_EXCLUDED:
US500-4h, JP225-2h, JP225-4h). Per-cell first, then **P11** with the **P6 non-4h rule** (≥5 cells over ≥3
instruments, with ≥3 qualifying cells outside the 4h domain) for any "winning arm" claim, **per object**.
**TRAIN only** = first 70% of the first-70% analysis set (F01 file-order prefix; identical fence to
EXP-049/053–065). TEST and the final-30% **global holdout** are **not** read. All forward windows (legs,
reversal events, trailing ratchet, caps) clipped to `train_end_ts`; unresolved truncated windows `DATA_CENSORED`
(disclosed). DE30 carries the truncated-coverage disclosure.

### Look-ahead / causality discipline (binding)

- Primary/secondary ZigZag and MA(20,50) segmentation are future information until confirmed. The signal (harami
  + `/STRONG-STAT`, on the ZigZag move for hybrid / the MA segment for native), `rd`, `M_sofar`, the
  favourable/adverse MA benchmark levels, the leg targets, and the MA benchmark time cap use **only** confirmed,
  completed prior moves/segments and **real bars at or before the entry bar** for construction at entry. The
  native `/STRONG-STAT` filter references only confirmed prior MA segments.
- Every exit is a **forward** event acted on at a bar known going forward in real time: first-profitable close
  (at the bar close), fractional-target touch (intrabar P15), reversal event (next confirmed MA segment
  `Direction==rd` or opposing-harami confirm — at the confirmation bar's close, never an unconfirmed
  crossover/pivot), and the structure trailing stop (the stop in force at bar `t` uses only secondary-ZigZag
  moves with `ConfirmTime ≤ CloseTime(t)` — the stop moves at the confirmation bar, never the retroactive pivot
  bar).
- The trailing ratchet is monotone (never loosens) and uses only confirmed secondary pivots; the forward scan
  reads only bars `[entry_idx+1, min(entry_idx+bench_N, last_train_idx)]`, fenced `CloseTime ≤ train_end_ts`; a
  window truncated before resolution is `DATA_CENSORED`. Matched-random entries (both objects) constructed
  causally with the identical pre-entry-only state.
- Ordering/alignment by `CloseTime`, never bar index across views (primary ZigZag, secondary ZigZag, MA
  segments, HA candles, real bars all aligned by `CloseTime`). The **same** harami `entry_idx` feeds both
  objects; verify `ma["entry_idx"]` and `zz["entry_idx"]` are the identical array before applying the
  cross-substrate hybrid mask.

### Real-price outcome discipline

Harami detected on HA candles; `M_sofar`, ATR normalisation, all benchmark/leg/stop levels, the secondary
trailing ZigZag, P15 fills, weighted expectancy, win rate, and exit-reason composition on real domain-bar OHLC.
MA(20,50) on **real close**. **No HA price in any metric** (the opposing-harami reversal arm uses HA candles
only to *locate* the exit bar, then exits at that bar's **real** close).

### Exclusions

- No costs (gross only).
- **Position-management exits only, on both objects.** The favourable MA benchmark level (50%), adverse MA
  benchmark level (1:1 — except where the trailing stop replaces it), and the third barrier (MA adaptive cap) are
  held at benchmark; no `/VPTARGET`/`/MAGTARGET` (EXP-064), no `/ADV-EXTREME`/`/ADV-NONE` (EXP-063), no
  `/THIRD-TIME`/`/THIRD-EVENT` horizon change (EXP-065 — the third barrier is MA benchmark for every arm; the
  reversal-event leg is bounded by the MA benchmark cap), no combined-system optimisation across all layers
  (EXP-067 hybrid / EXP-068 native). No `/BARCFG`/`/CONFIRM` overlays; no position-in-move *filter*. No
  `ATR_MULT_TRAIL` sensitivity grid (`0.5` frozen P18 default). **No secondary-MA trailing structure** (the
  trailing structure is the secondary 0.5 ZigZag per the EXP-059 baseline convention; a secondary-MA trail is
  out of scope). **No MA-parameter sweep**.
- No parameter tuning; **no post-result arm or object selection** (all 12 predeclared arm types on **both**
  objects reported); no gate adjudication (single G-015 after the full slate). No TEST or holdout contact; no
  candidate slot; no TEST read.
- **Deferred disclosed secondaries (runtime/budget; NOT computed here, explicitly — not silently):** the
  `/STRONG-HA` conditioning arm and the full **ZigZag-substrate position-management exit surface** — including the
  single ZigZag benchmark arm contrast vs EXP-059. With the exit axis now run on **two** conditioning objects (24
  binding arm instances + their nulls per cell), computing it on further conditioning populations would multiply
  the per-cell arm count against the performance mandate while adding only non-binding robustness context —
  exactly the EXP-063/EXP-064/EXP-065 dual-object deferral pattern (governance-APPROVED). The deferral is
  recorded in `run_metadata.json` (`disclosed_secondaries_not_computed`); if G-015 needs the ZigZag comparison,
  it is a bounded follow-up.

## Success / Failure Criteria (per object, never pooled)

All **gross**, per-cell first, P11-composed with the **P6 non-4h rule** (≥5 cells over ≥3 instruments, ≥3
outside 4h). Binding endpoint = **median per-event position-weighted gross expectancy** `E_cell` (ATR units,
P15 fills), on the **`/STRONG-STAT` arm**; per-cell viable iff **CI_low > 0** (regime-clustered moving-block
bootstrap, one-sided 95%, fixed seed) **AND ≥ 30 qualifying events**. The **mean** (raw + 10% trimmed +
worst-5% tail-share, each CI'd) is the P4 disclosed diagnostic, never a viability gate. The fork is computed
**separately for each object**; the phase-level reading is the stronger object's, the other documented in
parallel.

- **EVIDENCE_FOR (a position-management scheme helps on MA, for that object):** ≥1 arm type (2–12) **(a)** is
  median-viable per cell **AND (b)** beats its same-object matched-random-on-MA null (`arm − RM` median contrast
  CI_low > 0; P5) **AND (c)** beats that object's benchmark MA arm (`arm − benchmark` paired contrast CI_low >
  0), all composed by **P11 with the non-4h breadth rule**, **for that object**. The winning arm(s), their RM
  margin, and their benchmark margin are the deliverable; no candidate registration (G-015 only). The arm's P4
  mean diagnostic (does it also lift the mean toward positive?) is reported as a decisive input to EXP-067 /
  EXP-068 / G-015.
- **EVIDENCE_AGAINST (position management is not an MA lever for that object):** no alternative arm clears the
  combined (viable ∧ beats-RM ∧ beats-benchmark) P11 quorum for that object. Recorded as a measured-negative
  characterization; routing deferred to G-015. **Family stays OPEN** — the surface runs regardless (P9).
- **INCONCLUSIVE (power-limited):** fewer than the P11 quorum reach ≥30 qualifying events on the arms of
  interest for that object (scaling/trailing construction + warmup exclusions deplete counts), no correctness
  failure. Disclosed; never defaulted. The hybrid 3202-class object is expected more power-limited than native
  8360-class.
- **Hybrid vs native divergence (the central new fact):** EXP-061 found native generalises while hybrid does
  not. If native is EVIDENCE_FOR while hybrid is EVIDENCE_AGAINST/INCONCLUSIVE, the exit-machinery behaviour is
  a matched-substrate conditioning property; convergence would broaden the claim. The divergence is the
  deliverable, not a defect.
- **SUBSTRATE/METHOD_DEFECT:** any reconciliation, determinism, causality, or invariant failure → fix before
  reporting. Invariant checks: (i) **`M-BENCH` reproduces EXP-061 `M0` / EXP-060B `BENCH-MA`** and **`H-BENCH`
  reproduces EXP-061 `H0`** per-cell median + qualifying count to `RECON_TOL = 1e-9`; (ii) population
  reconciliation: hybrid ↔ EXP-053/060/061 `H0` (3202-class), native ↔ EXP-060B/061 `M0` (8360-class), exact;
  (iii) leg weights sum to 1.0 for every arm type, and a degenerate single-trigger arm (all 3 legs sharing one
  trigger) reproduces the equivalent single-leg arm's `R_event` to float precision; (iv) the trailing stop is
  monotone (never loosens) and changes level **only** on secondary-ZigZag confirmation bars (`ConfirmTime ≤
  CloseTime`); (v) every exit price is a real-bar P15 fill with `CloseTime ≤ train_end_ts`; (vi) the shared
  adverse/trailing stop, when it binds, closes all still-open partial legs at the same bar/level; (vii)
  **matched-count holds per object** — each arm type's RM/RH count equals that object's cell arm signal count.

Deliverable label: **MA_POSITION_MGMT_CHARACTERISED (dual-object)**, carrying — **per object, individually** —
the per-cell + P11 (non-4h) readout for every arm type, the EVIDENCE_* classification, the arm−RM and
arm−benchmark contrasts, the disclosed mean/trim/tail diagnostic (decisive for EXP-067/EXP-068/G-015 mean
question), **exit-reason composition** (the fraction of weight exiting via each leg trigger / shared stop /
trailing stop / time cap — the mechanism diagnostic), win rate, BENCH first-hit `r`, and all qualifying/
`DATA_CENSORED`/warmup counts; plus the reconciliation table (native `M-BENCH` ↔ EXP-061 `M0` / EXP-060B
BENCH-MA; hybrid `H-BENCH` ↔ EXP-061 `H0`; populations vs EXP-053/060/061). **No phase closure or candidate
registration here.**

## Complexity Budget

- **Max distinct statistical methods: 4** — identical to EXP-059/064/065 plus the dual-object extension:
  (1) regime-clustered moving-block bootstrap CI on an arm's **median** per cell; (2) the same bootstrap on the
  per-cell **mean + 10% trimmed mean** + worst-5% tail-share (P4 diagnostic); (3) `arm − RM` independent
  contrast CI (`contrast_ci`; binding, P5); (4) `arm − benchmark` paired-median contrast CI
  (`xen.favourable_targets.paired_median_contrast_ci`, common qualifying-event subset). Applied across the
  predeclared 12-arm set **on two objects** — a parameterised re-instrumentation, not new methods. Running the
  same 4 methods on the second object adds no distinct method, consistent with EXP-065.
- **Max visualisations: 5** — each rendered **per object** (hybrid and native panels/series, never pooled):
  (i) per-arm median-expectancy forest/CI per cell vs that object's benchmark; (ii) arm−benchmark and arm−RM
  contrast heatmap (arm types × cells; non-4h cells marked; per object); (iii) expectancy distribution by arm
  type (pooled within object); (iv) P11 (non-4h) composition / "wins" map across arm types (hybrid vs native
  side-by-side); (v) **exit-reason composition by arm type + median-vs-mean P4 preview** — per-arm fraction of
  weight via each exit reason beside per-cell qualifying counts and the median vs raw mean vs 10% trimmed mean +
  worst-5% tail-share for the best arms. Secondary tables to CSV.
- **Max new code modules: 1 — *expected 0*.** Reuses `xen.position_exits` (EXP-059: multi-leg P15 partial-exit
  resolver + structure trailing-stop builder/resolver), the EXP-058/065 `third_event_caps` forward-locator
  **pointed at MA segments** (reversal-event leg), and the EXP-064 **dual-object** MA pipeline; the only new code
  path vs EXP-064 is the per-arm position-management exit build (replacing EXP-064's per-variant
  favourable-target build), the per-arm-per-object RM call (new dedicated RNG purpose offsets), and the
  trimmed-mean/tail-share statistic. At most one thin orchestration wrapper under `code/`; **no new `xen/`
  analysis module**.

## Metric Denominators & Zero-Baseline

- **Per-event realised gross return** (ATR units) is the position-weighted `R_event` (above), defined for every
  **qualifying** event of an arm instance (of an object) — barriers/legs constructible (`fav_dist > 0`, finite
  positive `ATR_entry`, and, for trailing arms, the secondary ZigZag available) and every leg / the position
  reaching a finite P15 exit within the TRAIN-fenced window. `DATA_CENSORED` (any leg's window truncated by the
  TRAIN edge before resolution) and construction-warmup events are **excluded** from median/mean/trim and
  **disclosed as counts** per cell per arm per object.
- **Per-cell endpoints:** `E_cell_median` (binding, P3/P14) and `E_cell_mean` + 10% trimmed mean (P4
  diagnostic), each over the arm's qualifying-event population **per object**, each with its own fixed-seed
  bootstrap CI. Because every arm retains the MA benchmark time cap as the ultimate backstop, qualifying counts
  and censoring stay comparable to the BENCH arm; trailing arms additionally exclude events with no secondary-ZigZag
  pivot history (warmup), disclosed.
- **Zero-baseline / power:** a cell with **< 30 qualifying events** for an arm (of an object) is
  **NOT_VIABLE-by-power** for that arm/object (non-reportable), never an undefined/infinite ratio. Worst-5%
  tail-share: 0 negative mass → tail-share = 0.0 (finite).
- **Exit-reason composition** is computed and reported per arm per object as a **disclosed secondary**: the
  fraction of position weight exiting via each leg's favourable trigger, the shared adverse/trailing stop, the
  reversal-event, and the time cap. Never enters viability.
- **First-hit `r`** is defined only for the single-leg **BENCH** arm (`r = n_FAV/(n_FAV+n_ADV)`, TIMECAP
  excluded, EXP-049 convention), disclosed **per object** (expected ≈0.50, replicating EXP-061 M0/H0). For
  multi-leg/trailing arms `r` is undefined and is **not** reported as viability.

## Data Requirements

Per cell (instrument × domain), TRAIN slice only: lazy `pl.scan_parquet`; `analysis_rows = int(total*0.7)`,
`train_rows = int(analysis_rows*0.7)`; collect only the first `train_rows` file-order 1-minute rows (F01
prefix; never sort/collect the full file, never read TEST/holdout); assert chronological; `train_end_ts` =
last `CloseTime`. Aggregate each member domain (5m strict; others `min_coverage=0.90`); fence to
`CloseTime ≤ train_end_ts`; generate HA candles; run ZigZag (`atr_mult=1.0`) → confirmed moves +
`confirm_indices` (hybrid conditioning mask + disclosed contrast); run secondary ZigZag (`atr_mult=0.5`) →
secondary confirmed pivots + confirm indices (trailing stop structure — substrate-independent, used in both
objects); run `ma_segment_moves` (MA(20,50) on real close) → confirmed MA segments + crossover indices + the MA
in-progress state (`live_in_progress_state` on MA arrays, supplying `rd` / `M_sofar` / `start_epoch`, shared by
both objects); detect haramis on HA candles aligned by `CloseTime`; build **both** conditioned populations —
hybrid (`zz["stat"]["retained_p75"]`, byte-identical to EXP-053/060/061 `H0`) and native
(`ma["stat"]["retained_p75"]`, byte-identical to EXP-061 `M0`); compute the MA benchmark fav + adv levels +
MA adaptive cap; for each of the 12 arm types compute per-event leg/stop exits via the `position_exits`
resolvers (partial legs and/or structure trailing; reversal-event leg via the MA-segment next-`rd`-confirm
locator + opposing-harami locator) under P15, the weighted `R_event`, the qualifying mask **on each object's
population**; build the per-object per-arm matched-random-on-MA null through the identical pipeline; bootstrap
per-cell median + mean + 10% trimmed mean per arm per object (fixed seed, dedicated purposes) + worst-5%
tail-share; compute `arm − RM` (independent, binding) and `arm − benchmark` (paired) contrasts per object;
reconcile `M-BENCH` ↔ EXP-061 `M0` / EXP-060B `BENCH-MA` and `H-BENCH` ↔ EXP-061 `H0` (and populations vs
EXP-053); compose by P11 with the non-4h rule **per object**; second full pass for determinism. `tqdm` over
the 99-cell grid; **bounded per-cell memory** (per-event forward scans bounded by `bench_N`; per-cell arrays
released after summarisation; plots from collected per-cell summaries only — no reloads). Output
**byte-identical across `--workers`** counts (fixed-order reassembly + order-independent per-cell RNG).
Outputs (`results/`): `per_cell_expectancy.parquet` (per cell × arm × **object**: median/mean/trimmed + CIs,
arm−RM and arm−benchmark contrasts, n_qualifying, censoring/warmup counts, exit-reason composition, win rate,
viability + beats-RM + beats-benchmark flags); `position_mgmt_map.csv` (binding `/STRONG-STAT` summary per arm
type per object + P11 non-4h tally); `secondary_map.csv` (`/STRONG-HA` deferred, ZigZag contrast deferred,
BENCH `r` per object, exit-reason composition per object); `reconciliation.csv` (native `M-BENCH` ↔ EXP-061
M0 / EXP-060B BENCH-MA; hybrid `H-BENCH` ↔ EXP-061 H0; populations vs EXP-053/060/061, per object);
`composition_readout.json` (per-object per-arm P11 non-4h, wins, EVIDENCE_* fork, mean-diagnostic summary →
EXP-067/EXP-068/G-015 input); `run_metadata.json` (seed, frozen + inherited constants, EXP-059/060/060B/061/064
source paths/hashes, holdout fence, `disclosed_secondaries_not_computed`). Output dirs created only in
orchestration. Every per-cell record carries an `object` tag; per-object CSV/JSON keys separate hybrid and
native; **no pooled aggregate is emitted**.

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

Fork **EXP-064's dual-object `code/run_experiment.py`** (it already builds both conditioned populations —
hybrid `H0` via `bench_signal_arm`'s `cond_mask` override and native `M0` — the shared MA in-progress
geometry, the per-object matched-random controls via `matched_random_arm`, the corrected reconciliation roles,
the P4 mean/trim/tail bootstrap, and a per-variant OAT loop with per-object reporting). Changes, all bounded:
**(1)** replace EXP-064's per-variant **favourable-target** axis with the per-arm **position-management exit**
axis — compose EXP-059's `xen.position_exits` (multi-leg P15 partial-exit resolver + structure trailing-stop
builder/resolver) fed the **MA-substrate** fav/adv levels and MA adaptive cap, and the EXP-058/065
`third_event_caps` forward-locator **pointed at MA segments** for the reversal-event leg; also load and run the
secondary ZigZag (`atr_mult=0.5`) for the structure trailing stop. **(2)** Run each arm type on **both** object
populations — native (`ma["stat"]["retained_p75"]`) and hybrid (`zz["stat"]["retained_p75"]` via `cond_mask`;
verify the ZigZag mask indexes onto the MA entry order by `CloseTime`) — reporting individually with an
`object` tag on every per-cell × per-arm row. **(3)** Run `matched_random_arm` through each arm type's exit
pipeline to produce per-object nulls RM-* (native) / RH-* (hybrid) — each matched to its **own** object's arm
count, excluding its **own** object's signal entries, on **fresh dedicated RNG purposes per object/arm** so no
existing stream shifts — and compute per-object per-arm `arm − RM` (`contrast_ci`) and `arm − benchmark`
(`paired_median_contrast_ci`) contrasts. **(4)** Reconcile **`M-BENCH` ↔ EXP-061 `M0` / EXP-060B `BENCH-MA`**
and **`H-BENCH` ↔ EXP-061 `H0`** exactly (`RECON_TOL = 1e-9`; SUBSTRATE/METHOD_DEFECT if not), and reconcile
populations vs EXP-053 (hybrid 3202-class) / EXP-061 (native 8360-class). **(5)** Emit **per-object** P11
(non-4h) / signal-vs-RM / lever readouts (never pooled); add the binding exit-reason composition and the P4
mean-diagnostic summary. Keep EXP-064's per-instrument `ProcessPoolExecutor` with native-thread pinning and
fixed-order reassembly (byte-identical for any `--workers`). Fixed per-cell seed throughout (P3); `tqdm`;
bounded memory; **do not adjudicate G-015**. The existing native/hybrid BENCH median+mean RNG paths must stay
byte-identical to EXP-061 (use new RNG purposes for new arm exit builds and their nulls only) so the EXP-061
reconciliation holds for both objects.
