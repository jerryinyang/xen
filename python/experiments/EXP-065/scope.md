# Experiment: EXP-065 — MA(20,50)-Substrate Third-Barrier Geometry (Conditioned HA Harami; `/THIRD-TIME`, `/THIRD-EVENT` vs Benchmark Adaptive Cap; **Dual Conditioning Object: Hybrid and Native**, Phase 015 Surface S2)

> **Re-run under `D0-amendment-001-dual-parallel-substrate.md` (2026-06-17).** The prior EXP-065
> scope measured a single MA third-barrier axis labelled *hybrid* but reconciled its benchmark arm
> to EXP-061 `M0` — which is the **native** object (MA-segment `/STRONG-STAT`, 8360-class), not the
> hybrid object (ZigZag-`/STRONG-STAT`, 3202-class). That is the propagated labelling defect the
> amendment corrects, and its old Exclusions wrongly deferred *all* MA-native conditioning to EXP-068.
> This re-run emits the full 5-variant third-barrier axis **for both conditioning objects individually**
> (separate variant arms, separate matched-random nulls, separate per-cell viability, separate P11
> composition, separate EVIDENCE fork — never pooled) and supersedes the prior single-object EXP-065
> scope in place. EXP-065 was **paused** (no `results/`, no code); resumption is dual-object from the
> start, so no prior result is overturned — only the scope/plan.

> **Mandatory-reading precondition (Phase 015, binding — inherited from 014-B).**
> `../../docs/experiments-docs/checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/014-A-conditioning-gap-and-validation-lessons.md`
> was read in full before this scope was written. EXP-065 is the Phase 015 **third-barrier geometry**
> surface read (S2; mirrors EXP-058) on the **MA(20,50) substrate**, on **both** conditioning objects.
> The four mandatory rules are honoured, recorded so Stage 4 can check:
> - **(a) conditioning** — honoured, **and now disambiguated** (Amendment 001). Two live
>   `/STRONG-STAT`-conditioned HA-harami objects are measured individually over the **same** MA(20,50)
>   favourable/adverse/cap geometry, varying **only the third barrier**: **hybrid** (filter on the
>   in-progress confirmed *ZigZag* move — entry population byte-identical to EXP-053/060/061's hybrid
>   `H0`; the genuinely-new object) and **native** (filter recomputed on the in-progress confirmed *MA
>   segment* — the population EXP-061's `M0` measured; reconciles to EXP-061 native `M0` / EXP-060B
>   `BENCH-MA`). `/STRONG-STAT` (P7) is binding in each; `/STRONG-HA` (P8) is a disclosed-secondary arm
>   (deferred for runtime — see Exclusions). Only the **third barrier** is varied (OAT); the signal,
>   anchor, favourable target (MA 50%), adverse target (MA 1:1), and fills are held at the MA benchmark.
>   Each object's matched-random-on-MA control is a deliberate **null** (binding per P5), not a signal
>   claim. The two objects are never pooled.
> - **(b) harami-anchor** — honoured. Entry is the **harami confirmation-bar real close** `C` in both
>   objects. The `/THIRD-EVENT` exit uses a forward **MA-segment confirmation** in the reversal direction
>   (a future-confirmed structural close-out of a position already entered at the harami), never as the
>   entry and never an unconfirmed crossover. The matched-random controls intentionally break the anchor
>   (that is what makes them nulls).
> - **(c) position-in-move descriptive-only / never a live filter** — honoured. EXP-050's position
>   metric is not used. The `/THIRD-EVENT` exit uses the next MA-segment confirmed (`ConfirmTime > entry`)
>   in direction `rd` — a quantity known forward-in-time, acted on at the confirmation bar — not a
>   position-in-move filter.
> - **(d) expectancy / not first-hit `r`** — honoured. The binding endpoint is the Phase 015 **median**
>   gross per-event expectancy (P3/P14), computed **per object individually**. The **mean** (raw + 10%
>   trimmed + worst-5% tail-share, each CI'd) is the P4 **diagnostic co-primary**, disclosed; first-hit
>   `r` and the **censoring fraction** are disclosed secondaries. The third barrier governs the "neither
>   target hit" exit and the qualifying denominator, so the censoring fraction is reported prominently —
>   but never binds.
> EXP-065 does **not** treat the EXP-049 `r≈0.50` null or EXP-050 front-loading as evidence against the
> family — those measured the *unconditioned ZigZag* object.

**Phase / checkpoint:** `2026-06-17-015-ma-substrate-conditioned-harami-full-surface` (Phase 015; **G0 PASS 2026-06-17**).
**Family / candidate:** `CF-HA-HARAMI-001` (`REGISTERED`, OPEN) · Phase 015 surface **S2** ·
`CF-HA-HARAMI-001/HYP-018` — EXP-065 (Phase 015 batch, `multiplicity-registry.md` line 489, "hybrid + native (S2),
individually"). Exercises the registered branches `CF-HA-HARAMI-001/THIRD-TIME` and `CF-HA-HARAMI-001/THIRD-EVENT`
on the registered `CF-HA-HARAMI-001/MA-SUBSTRATE` (both modes `hybrid` and `native`, parallel first-class per
Amendment 001).
**Registry precondition (satisfied):** `MA-SUBSTRATE` + **both** conditioning modes (`hybrid`, `native`, parallel
first-class per `D0-amendment-001`) **REGISTERED** (Phase 015 batch, 2026-06-17, G0 PASS); `/THIRD-TIME`,
`/THIRD-EVENT`, the benchmark 3-barrier geometry, and the matched-random baseline pre-exist (Phase 014 / 014-B +
EXP-061 reuse). HYP-018/EXP-065 is the listed plan (`EXP-058`-analog, S2), now emitting both objects individually.
**No new countable item is introduced here.**
**Surface role:** Surface read 2 of the Phase 015 post-lead slate — third-barrier geometry on MA, on **both**
objects. EXP-061 (L1) established the **native** MA benchmark geometry is signal-attributable (EVIDENCE_FOR;
`M0 ≻ RM0` generalised beyond the champion, 8 cells) while the **hybrid** object generalised in only 1 cell
(EVIDENCE_AGAINST) — so the third-barrier question must be read **per object**. EXP-062 (L2) found the MA-segment
lifetime reversal move **is available** (AVAILABILITY_GOOD); MA segments are longer than ZigZag moves, so the
benchmark cap may bind before the available move is captured. This experiment asks, **per object**, whether
**extending the holding horizon** (time or structural MA-segment event) converts that available move into higher
gross MA-substrate median expectancy, at what censoring cost, and whether any such gain is signal-attributable
(beats its same-object RM-on-MA null, P5). The surface runs **regardless** of the lead (P9 no-early-closure);
output feeds the single terminal **G-015** after the full slate. **No closure or candidate registration here.**
**Governing design / D0:** `design.md` (§3 objective; §5 slate S2; §7 G-015 criteria, judged per object) +
`D0-predeclarations.md` (P1 substrate; **P2 both objects parallel/individual**; P3 median binding + fixed seed;
P4 mean diagnostic; **P5 matched-null per object every read**; P6 non-4h composition; P8 OAT grids reused unchanged;
P9 slate; P10 power; **P12 reconciliation roles — native↔EXP-061 `M0`/EXP-060B 1e-9, hybrid↔EXP-061 `H0` 1e-9 +
EXP-053 population**) + `D0-amendment-001-dual-parallel-substrate.md`. Inherits 014-B P14/P15/P16/P20 and the family
spec `candidate-families/harami.md` (third-barrier variants).
**Reuses (no new `xen/` module expected):** the EXP-058 third-barrier machinery (`xen.third_barrier`: `/THIRD-TIME`
floor re-call + causal next-`rd`-confirm `/THIRD-EVENT` locator), **applied to MA segments** (the EXP-058
MA-seg-baseline path already implements this); the EXP-061 **dual-object** MA pipeline (`ma_segment_moves`,
`_ma_context`, `_zz_context`, `bench_signal_arm` with its `cond_mask` override, `matched_random_arm`, `resolve_arm`)
and its P4 mean-diagnostic functions (`bootstrap_stat_distribution`, `_trimmed_mean`, `_tail_share_worst5`);
`xen.expectancy.*` (`live_in_progress_state`, `live_strong_stat`, `adaptive_time_caps_by_epoch`, `benchmark_barriers`,
`resolve_path_ordered`, `realised_returns`, `qualifying_mask`, `bootstrap_median_distribution`,
`bootstrap_mean_distribution`, `median_ci`, `contrast_ci`); `xen.favourable_targets.paired_median_contrast_ci`;
ZigZag (`xen.zigzag`, hybrid conditioning mask + disclosed contrast), harami (`xen.ha_harami`), `/STRONG-HA`
(`xen.strong_move.annotate_ha_impulse`), confirmation indices (`xen.capture_barriers`). **EXP-064's dual-object
`code/run_experiment.py` is the closest structural fork base** (it already runs a per-variant OAT loop on **both**
object populations with per-object RM nulls and the P4 mean/trim/tail diagnostic — EXP-065 swaps its favourable-target
axis for the third-barrier axis).

## Slot & ledger accounting (binding)

- **0 candidate slots, 0 TEST reads.** Characterization/diagnostic per the Phase 015 D0 (P11). No countable
  item is introduced: `MA-SUBSTRATE` (+ both `hybrid`/`native` modes) is registered at G0; `/THIRD-TIME`,
  `/THIRD-EVENT`, the benchmark geometry, and the matched-random nulls pre-exist. A slot is consumed only at a
  G-015 PROCEED on a future scope.
- **No TEST stratum is read.** All work on the **TRAIN** slice (first 70% of the first-70% analysis set; F01
  file-order prefix; identical fence to EXP-049/053–064). Hybrid population byte-identical to EXP-053/060/061
  `H0`; native population byte-identical to EXP-060B/061 `M0`; no new stratum opened; `test-read-ledger.md`
  requires no entry; global-holdout seal carries forward. No HA-harami TEST stratum has ever been read. **Note on
  the `/THIRD-EVENT` backstop and longer `/THIRD-TIME` caps:** forward excursion/exit scans run only within the
  TRAIN slice and are clipped to the TRAIN data edge — a window extending past `train_end_ts` is `DATA_CENSORED`,
  never resolved against TEST/holdout rows.
- All work **gross**; detection on HA candles; **all outcome metrics on real-price OHLC**; MA(20,50) computed on
  **real close** (identical to EXP-060/061 `ma_segment_moves`). No HA price enters any metric.

---

## Hypothesis

On the `/STRONG-STAT`-conditioned HA harami, **for each conditioning object individually** (hybrid and native),
99-cell TRAIN grid, MA(20,50) substrate, entered at the harami confirmation-bar real close `C` and faded against
the in-progress confirmed-MA-segment move, with the favourable target held at the MA benchmark 50%-of-`M_sofar`
level and the adverse target held at the MA benchmark 1:1 level (OAT on the **third barrier only**): **at least
one alternative third-barrier geometry** (`/THIRD-TIME` floor ∈ {12, 24, 48}; `/THIRD-EVENT` next-MA-segment-`rd`-confirm
with 8× backstop) produces **higher gross per-event median expectancy** (P3/P14, ATR-normalised, P15 fills, real
prices) than the **benchmark MA adaptive cap** (floor=6), on the binding `/STRONG-STAT` arm, **and** that winning
variant is **signal-attributable** (beats its own same-object matched-random-on-MA null, P5).

The two objects are judged **individually, never pooled** (P2); the phase-level reading of this lever is the
**stronger object's** outcome (consistent with EXP-061: native is the object that expresses the edge), with the
other object's result documented in parallel.

**Falsifiable, per object:** if **no** alternative third-barrier variant simultaneously (a) is median-viable per
cell, (b) beats its same-object matched-random-on-MA null (`variant − RM` contrast CI_low > 0), and (c) beats that
object's benchmark MA variant (`variant − benchmark` paired contrast CI_low > 0), all composed by P11 with the P6
non-4h breadth rule, then third-barrier geometry is **not** an MA-substrate lever that improves conditioned capture
**for that object** (a valid characterization result feeding G-015 — never a closure inside Phase 015; the surface
runs regardless, P9).

## Question

On the MA substrate, **for each object (hybrid, native)**, does changing only the **third barrier** — from the
benchmark floor-6 MA adaptive cap to a longer-floor adaptive cap (`/THIRD-TIME` floor ∈ {12, 24, 48}) or to a
structural MA-segment event cap (`/THIRD-EVENT`: hold until the MA substrate confirms a reversal-direction segment,
backstopped at 8× the benchmark cap) — improve the conditioned HA-harami's gross per-event median expectancy vs
that object's benchmark, per cell and composed across the 99-cell grid, beat the same-object matched-random-on-MA
null, and which variant (if any) wins? At what cost in **censoring** (the fraction of events whose longer window is
truncated by the data edge) and in **TIMECAP/event-exit composition** (disclosed secondaries)? Does the EXP-058
ZigZag-substrate result (no variant cleared P11) reproduce or differ on MA, where segments are longer — and does
the picture differ between the hybrid and native objects?

---

## Scope Boundaries

### Data Views

- **Real domain bars** (5m strict; 15m/30m/1h/2h/4h via `xen.bar_aggregator.aggregate_ohlc`,
  `min_coverage=0.90` — identical to EXP-049/053–064/VAL-004) for the MA(20,50)-crossover substrate
  (`ma_segment_moves` on real close), the ZigZag substrate (`atr_mult=1.0`, hybrid conditioning mask + disclosed
  contrast), confirmed moves/segments, `/STRONG-STAT` magnitudes (on ZigZag for hybrid / on MA segments for
  native), the third-barrier caps (time and MA-segment event), benchmark fav/adv levels, P15 fills, ATR
  normalisation, and **all** outcome metrics.
- **Heiken Ashi candles** (`xen.heiken_ashi_generator`) for **harami detection only** (frozen EXP-048 detector)
  and the disclosed/deferred `/STRONG-HA` arm. **No HA price enters any metric.**

### Event population (two conditioning objects, measured individually over the same MA third-barrier geometry)

Both objects share the **same** frozen HA-harami detection, the **same** MA(20,50) outcome geometry
(`rd` / `M_sofar` / favourable target / adverse target), and the **same** real bars; they differ **only** in the
`/STRONG-STAT` conditioning filter (P2) and, per variant, in the third barrier under test:

- **Hybrid (`H-*`).** Qualifies iff the harami passes `/STRONG-STAT` p75 on the **in-progress confirmed ZigZag
  move** magnitude-so-far `M_sofar^{ZZ} = |C − start_pivot|` ≥ p75 of the trailing-20 confirmed-ZigZag-move
  magnitudes (hybrid mode). The conditioning mask is **byte-identical to EXP-053/060/061's hybrid `H0` set** (the
  same `live_in_progress_state` / `live_strong_stat` on the ZigZag move, applied through the MA context via the
  `bench_signal_arm` `cond_mask` override). MA supplies only the geometry. **This is the genuinely-new object**
  for the third-barrier axis (a ZigZag-conditioned third-barrier surface over MA geometry was never computed
  before Amendment 001). Its internal-lineage anchor is **EXP-061 `H0`** (the `H-BENCH` variant reproduces it);
  its conditioning population reconciles to **EXP-053's 3202-class ZigZag-`/STRONG-STAT` set**; it has **no
  EXP-060B/058 outcome back-reconciliation anchor**.
- **Native (`M-*`).** Qualifies iff the harami passes `/STRONG-STAT` p75 on the **in-progress confirmed MA
  segment** magnitude-so-far ≥ p75 of the trailing-20 confirmed-MA-segment magnitudes (recomputed on MA segments;
  causal — only segments confirmed at/before the harami bar). **Population byte-identical to EXP-061 native `M0`
  and EXP-060B `BENCH-MA`**; the `M-BENCH` variant **reconciles to them (1e-9)** — the object the prior
  (mislabelled) EXP-065 scope actually intended.

Entry anchor is the harami close `C` in both. The **trade / reversal direction** `rd` and the **MA-segment
magnitude-so-far** `M_sofar` used to build the benchmark fav/adv levels come from the **MA(20,50) substrate**
(`ma_seg_arm`: last confirmed MA crossover → `C`), exactly the EXP-060/061 construction; the conditioning filter
differs by object but the geometry is the same. Construction reuses `xen.expectancy.live_in_progress_state` +
`live_strong_stat` and the EXP-060 `ma_segment_moves`/`ma_seg_arm` — the **same functions EXP-053/060/061 used**.
Each object's matched-random-on-MA nulls draw **non-harami** in-MA-regime timestamps, **matched-count to that
object's qualifying count per variant**, on **independent dedicated RNG streams** distinct from the other object's.

### Entry anchor

The **harami confirmation-bar real close** `C` (real domain-bar close at the harami timestamp), strictly before
any ZigZag/MA trend-change confirmation. Identical to EXP-053/061.

### Third-barrier variants on MA (predeclared sweep; OAT on the third barrier only; **per object**)

For every variant the **favourable** target is the MA benchmark `fav = C + rd·0.50·M_sofar` and the **adverse**
target is the MA benchmark 1:1 `adv = C − rd·0.50·M_sofar` (`M_sofar` from the MA segment). Variants differ only
in the **third barrier**, expressed as the per-event window length `n_event` (real domain bars after entry) fed to
the P15 resolver. Fills are P15. The qualifying denominator is FAV/ADV/TIMECAP with a finite exit and finite
positive `ATR_entry`; `DATA_CENSORED` (window truncated by the TRAIN edge before resolution) is excluded-with-record
(disclosed as the censoring fraction), never measured against truncated data. **Each variant is built and resolved
twice — once on the hybrid population, once on the native population — and reported individually.**

1. **Benchmark (reference variant, floor=6; `{M,H}-BENCH`):** the MA-defined adaptive cap (the `ma_seg_arm`
   benchmark cap, `N = max(6, round(1.5 × median(trailing-20 confirmed-MA-segment durations)))`, knobs `window=20`,
   `k=1.5`, `min_moves=5`). The **native** `M-BENCH` arm **is EXP-061's `M0` / EXP-060B `BENCH-MA`** (the P12
   native reconciliation target); the **hybrid** `H-BENCH` arm **is EXP-061's `H0`** (the P12 hybrid reconciliation
   target). Each is the anchor every same-object alternative is contrasted against.

2. **`/THIRD-TIME-T12` (floor=12):** `N = max(12, round(1.5 × median(MA-segment durations)))` —
   `adaptive_time_caps_by_epoch` re-called with `floor=12` on the MA-segment durations, all other knobs at
   benchmark.

3. **`/THIRD-TIME-T24` (floor=24):** `N = max(24, round(1.5 × median(MA-segment durations)))` (`floor=24`).

4. **`/THIRD-TIME-T48` (floor=48):** `N = max(48, round(1.5 × median(MA-segment durations)))` (`floor=48`).

5. **`/THIRD-EVENT` (MA-segment `rd`-confirm, 8× backstop):** the effective per-event cap is
   `n_event_evt = min(bars_to_next_rd_ma_confirm, 8 × bench_N)`, where:
   - `bars_to_next_rd_ma_confirm` = (confirm index of the **smallest**-index confirmed MA segment with
     `Direction == rd` and `ConfirmTime > entry_epoch`) − `entry_idx` (the next confirmed reversal-direction **MA
     segment** strictly after entry — the analogous structural event to EXP-058's ZigZag `/THIRD-EVENT`, on the MA
     substrate, per the EXP-058 MA-seg-baseline convention); if none exists within the data, this term is `+∞`
     (the backstop binds).
   - `bench_N` = the BENCH (floor=6) MA adaptive cap for that entry; `8 × bench_N` is the backstop.
   - Resolved through the **unchanged** `resolve_path_ordered`: a scan of `[entry+1, entry+n_event_evt]` returning
     FAV/ADV if a target is hit first, else `TIMECAP` exiting at `close[entry+n_event_evt]` (the `rd`-confirm
     MA-segment bar's real close when the event bound, or the backstop bar's real close), else `DATA_CENSORED` if
     the window is truncated by the TRAIN edge before resolution.
   - **Warmup/availability:** an entry that is benchmark-warmup-excluded (`bench_N` undefined: insufficient
     confirmed MA segments) has no defined backstop and is **excluded-with-record** for `/THIRD-EVENT`.
     `n_event_evt ≥ 1` by construction (`bench_N ≥ 6`).
   - **Disclosed split:** the fraction of TIMECAP exits bounding on the **actual `rd` MA-segment event** vs the
     **backstop** is reported per cell per object.

**Total predeclared third-barrier variants per object:** 1 benchmark + 3 `/THIRD-TIME` (T12, T24, T48) + 1
`/THIRD-EVENT` = **5 binding variants**; **× 2 objects = 10 binding variant arms total** (reported individually,
never pooled). Each variant runs on the binding `/STRONG-STAT` arm of its object; the `/STRONG-HA` arm is a
disclosed secondary (deferred for runtime — see Exclusions). Each variant arm carries its own matched-random-on-MA
null (binding, P5).

### Matched-random-on-MA null (RM; **binding per P5**, per variant, **per object**)

For **each** third-barrier variant **of each object**, a **matched-count random in-regime** control (the EXP-060B
matched-random-in-MA-regime selection, reused unchanged; same cell / direction / regime, valid live MA state,
EXP-021/027 exclusion convention, **matched-count to that object's qualifying harami count for the variant**,
**excluding that object's conditioned-harami entries**) is run through the **identical variant third-barrier +
benchmark fav/adv + P15 pipeline** on the MA substrate. Native nulls are `RM-BENCH/RM-T12/RM-T24/RM-T48/RM-EVENT`;
hybrid nulls are `RH-BENCH/RH-T12/RH-T24/RH-T48/RH-EVENT`. **Signal-attribution requires the variant beats its own
same-object RM null** (`variant − RM` median contrast CI_low > 0; independence-assuming `contrast_ci`) — elevated
from the EXP-058 disclosed-secondary status to **binding** by Phase 015 P5. The RM draws are **independent** of the
harami events (no common subset to pair). The hybrid and native nulls draw from the **same MA in-regime pool** but
are matched to **different counts** and exclude **different signal entries**, on **disjoint dedicated RNG streams**;
the two objects' contrasts are **never pooled**.

### Favourable target, adverse target, fills (MA benchmark; held fixed across variants and objects)

- **Favourable (MA benchmark 50%):** `fav = C + rd·0.50·M_sofar` for every variant and object.
- **Adverse (MA benchmark 1:1):** `adv = C − rd·0.50·M_sofar` for every variant and object.
- **Fill model (P15, method standard):** bullish bar (`Close ≥ Open`): `O→L→H→C`; bearish: `O→H→L→C`. TIMECAP
  exits at the cap/event bar's real close; `DATA_CENSORED` carries no exit price and is excluded. Reuse
  `xen.expectancy.resolve_path_ordered`. Documented approximation; disclosed.

### Parameters (all frozen / predeclared; no tuning)

MA(20,50) on real close (fixed; P1 — not swept); ZigZag Wilder ATR(14), `ATR_MULT=1.0` (hybrid conditioning mask +
disclosed contrast); `/STRONG-STAT` trailing-20, ≥p75 (P7; on ZigZag for hybrid / on MA segments for native);
`/STRONG-HA` `X=3` (P8; disclosed/deferred); benchmark favourable `X = 50%` of MA `M_sofar`; benchmark adverse 1:1;
benchmark MA adaptive cap `(k=1.5, window=20, floor=6, statistic=median, min_moves=5)`; ATR-normalisation = Wilder
ATR(14) at the harami entry bar (P14); bootstrap `b = round(m^(1/3))`, `N_BOOT = 10_000`, **fixed per-cell seed
(P3)** — `np.random.default_rng([BASE_SEED, cell_index, purpose])` with dedicated purposes per object/variant/statistic
so the native `M-BENCH` median path stays byte-identical to EXP-061 `M0` and the hybrid `H-BENCH` path byte-identical
to EXP-061 `H0`. **New predeclared third-barrier parameters (this scope):** `/THIRD-TIME` floors `{6 (BENCH), 12, 24,
48}` with `k=1.5`/`window=20`/`min_moves=5` held at benchmark (on MA-segment durations); `/THIRD-EVENT` opposing-event
= next confirmed MA segment with `Direction == rd` and `ConfirmTime > entry`; `/THIRD-EVENT` backstop multiple
`= 8 × bench_N`; mean trim fraction **10%**, tail-share **worst-5%** (P4). None tuned against outcomes; sensitivity
not swept beyond the predeclared grid.

### Instruments / cells / time range

The **99-cell EXP-049/053–064 member grid** (17 instruments × {5m,15m,30m,1h,2h,4h} − 3 COVERAGE_EXCLUDED:
US500-4h, JP225-2h, JP225-4h). Per-cell first, then **P11** with the **P6 non-4h rule** (≥5 cells over ≥3
instruments, with ≥3 qualifying cells outside the 4h domain) for any "winning variant" claim, **per object**.
**TRAIN only** = first 70% of the first-70% analysis set (F01 file-order prefix; identical fence to
EXP-049/053–064; `train_end_ts` = last `CloseTime` of the first `int(int(total_rows*0.7)*0.7)` file-order 1-minute
rows). TEST and the final-30% **global holdout** are **not** read. Longer-horizon and event windows clipped to
`train_end_ts`; unresolved truncated windows `DATA_CENSORED` (disclosed). DE30 carries the truncated-coverage
disclosure.

### Look-ahead / causality discipline (binding)

- ZigZag and MA(20,50) segmentation are future information until confirmed. The signal (harami + `/STRONG-STAT`, on
  the ZigZag move for hybrid / the MA segment for native), `rd`, `M_sofar`, the favourable/adverse targets, and all
  `/THIRD-TIME` caps use **only** confirmed, completed prior moves/segments and **real bars at or before the entry
  bar** for construction at entry. The `/THIRD-TIME` caps depend only on durations of MA segments confirmed
  **strictly before** entry. The native `/STRONG-STAT` filter references only confirmed prior MA segments.
- The `/THIRD-EVENT` exit is a **forward** event: it uses the next MA segment confirmed with `ConfirmTime > entry`
  (known going forward in real time, exactly as the benchmark TIMECAP resolves at a forward bar) and exits at that
  confirmation bar's real close — never at the retroactively-located crossover, never an unconfirmed crossover.
  Causal (the exit decision is taken at the confirmation bar).
- Excursion/exit scans read only bars `[entry_idx+1, min(entry_idx+n_event, last_train_idx)]`, fenced
  `CloseTime ≤ train_end_ts`; a window truncated before resolution is `DATA_CENSORED`. Matched-random entries
  constructed causally with the identical pre-entry-only state, per object.
- Ordering/alignment by `CloseTime`, never bar index across views.

### Real-price outcome discipline

Harami detected on HA candles; `M_sofar`, ATR normalisation, fav/adv levels, all third-barrier caps, fills,
expectancy, mean/trim/tail, `r`, win rate, and censoring all on real domain-bar OHLC. MA(20,50) on **real close**.
**No HA price in any metric.**

### Exclusions

- No costs (gross only).
- **Third-barrier geometry only, on both objects.** No `/VPTARGET`/`/MAGTARGET` (EXP-064 — favourable held at MA
  benchmark 50%), no `/ADV-EXTREME`/`/ADV-NONE` (EXP-063 — adverse held at MA benchmark 1:1), no `/EXIT-PARTIAL`/
  `/EXIT-TRAIL-STRUCT` (EXP-066), no combined system (EXP-067 hybrid / EXP-068 native). No `/BARCFG`/`/CONFIRM`
  overlays; no position-in-move *filter*; **no MA-parameter sweep** (MA(20,50) fixed).
- No parameter tuning; **no post-result variant or object selection** (all 5 predeclared variants on **both**
  objects reported and composed); no gate adjudication (single G-015 after the full slate — EXP-065 emits a
  characterization readout only). No TEST or holdout contact; no candidate slot; no TEST read.
- **Deferred disclosed secondaries (runtime/budget; NOT computed here, explicitly — not silently):** the
  `/STRONG-HA` conditioning arm and the full **ZigZag-substrate third-barrier surface** — **including the single
  ZigZag benchmark contrast vs EXP-058**. With the third-barrier axis now run on **two** conditioning objects (10
  binding variant arms + their nulls per cell), computing it on further conditioning populations (the ZigZag
  substrate geometry has its own `M_sofar` / cap pipeline) would multiply the per-cell arm count against the
  performance mandate while adding only non-binding robustness context — exactly the EXP-063/EXP-064 dual-object
  deferral pattern (governance-APPROVED). The deferral is recorded in `run_metadata.json`
  (`disclosed_secondaries_not_computed`); if G-015 needs the ZigZag comparison, it is a bounded follow-up.

## Success / Failure Criteria (per object, never pooled)

All **gross**, per-cell first, P11-composed with the **P6 non-4h rule** (≥5 cells over ≥3 instruments, ≥3 outside
4h). Binding endpoint = **median per-event gross expectancy** `E_cell` (ATR units, P15 fills), on the
**`/STRONG-STAT` arm**; per-cell viable iff **CI_low > 0** (regime-clustered moving-block bootstrap, one-sided 95%,
fixed seed) **AND ≥ 30 qualifying events**. The **mean** (raw + 10% trimmed + worst-5% tail-share, each CI'd) is the
P4 disclosed diagnostic, never a viability gate. The fork is computed **separately for each object**; the
phase-level reading is the stronger object's, the other documented in parallel.

- **EVIDENCE_FOR (a third-barrier lever helps on MA, for that object):** ≥1 alternative variant **(a)** is
  median-viable per cell **AND (b)** beats its same-object matched-random-on-MA null (`variant − RM` median contrast
  CI_low > 0; P5 signal-attribution) **AND (c)** beats that object's benchmark MA variant (`variant − benchmark`
  paired contrast CI_low > 0), all composed by **P11 with the non-4h breadth rule**. The winning variant(s), their
  RM margin, and their benchmark margin are the deliverable; no candidate registration (G-015 only).
- **EVIDENCE_AGAINST (third-barrier geometry is not an MA lever for that object):** no alternative variant clears
  the combined (viable ∧ beats-RM ∧ beats-benchmark) P11 quorum for that object. Recorded as a measured-negative
  characterization; routing deferred to G-015. **Family stays OPEN** — the surface (S3/S4, both objects) runs
  regardless (P9).
- **INCONCLUSIVE (power-limited):** fewer than the P11 quorum of cells reach ≥30 qualifying events on the variants
  of interest for that object (censoring/warmup exclusions deplete counts — the expected failure mode of the longest
  horizons; the hybrid object — 3202-class — is expected more power-limited than native — 8360-class), no
  correctness failure. Disclosed; never defaulted to a ratio.
- **SUBSTRATE/METHOD_DEFECT:** any reconciliation, determinism, causality, or invariant failure → fix before
  reporting. Invariant checks: (i) the **native benchmark arm `M-BENCH` reproduces EXP-061 `M0` / EXP-060B
  `BENCH-MA`** and the **hybrid benchmark arm `H-BENCH` reproduces EXP-061 `H0`** per-cell median + qualifying count
  to `RECON_TOL = 1e-9`; (ii) `/THIRD-TIME` per-event cap is **monotone non-decreasing in floor** event-wise
  (`N_BENCH ≤ N_T12 ≤ N_T24 ≤ N_T48`) within each object; (iii) `/THIRD-EVENT` per-event cap satisfies
  `1 ≤ n_event_evt ≤ 8 × bench_N` and any bound `rd` MA-segment confirm has `ConfirmTime > entry`; (iv) population
  reconciliation: hybrid ↔ EXP-053/060/061 `H0` (3202-class), native ↔ EXP-060B/061 `M0` (8360-class), exact per
  object; (v) **matched-count holds per object** — each variant's RM/RH count equals that object's cell variant
  signal-arm count; (vi) every exit price is a real-bar P15 fill with `CloseTime ≤ train_end_ts`.

Deliverable label: **MA_THIRD_BARRIER_CHARACTERISED (dual-object)**, carrying — **per object, individually** — the
per-cell + P11 (non-4h) readout for every variant, the EVIDENCE_* classification, the variant−RM and
variant−benchmark contrasts, the disclosed mean/trim/tail diagnostic, per-variant **censoring fraction** (the
binding trade-off of horizon extension), the `/THIRD-EVENT` event-vs-backstop split, first-hit `r`, win rate, and
all warmup/exclusion counts; plus the reconciliation table (native `M-BENCH` ↔ EXP-061 `M0` / EXP-060B `BENCH-MA`;
hybrid `H-BENCH` ↔ EXP-061 `H0`; populations vs EXP-053/060/061). **No phase closure or candidate registration here.**

## Complexity Budget (Comparative experiment)

- **Max distinct statistical methods: 4** — (1) regime-clustered moving-block bootstrap CI on a variant's **median**
  expectancy per cell (`bootstrap_median_distribution` + `median_ci`); (2) the same bootstrap on the per-cell
  **mean + 10% trimmed mean** (`bootstrap_stat_distribution`/`bootstrap_mean_distribution`) + worst-5% tail-share
  point estimate (P4 diagnostic, dedicated RNG streams); (3) `variant − RM` independent contrast CI (`contrast_ci`;
  binding, P5); (4) `variant − benchmark` paired-median contrast CI
  (`xen.favourable_targets.paired_median_contrast_ci`, common qualifying-event subset). Applied across the
  predeclared 5-variant grid **on two objects** (a parameterised sweep re-instrumented per object — **not new
  methods**; running the same 4 methods on a second object adds no distinct method) — consistent with EXP-058/EXP-064
  and the Phase 015 lead.
- **Max visualisations: 5** — each rendered **per object** (hybrid and native panels/series, never pooled): (i)
  per-variant median-expectancy forest/CI per cell vs benchmark (headline); (ii) variant−benchmark and variant−RM
  contrast heatmap (variants × cells; non-4h cells marked); (iii) expectancy distribution by variant (pooled within
  object); (iv) P11 (non-4h) composition / "wins" map across variants (hybrid vs native side-by-side); (v)
  **censoring + TIMECAP composition by variant** (the horizon-vs-power trade-off) alongside per-cell qualifying-event
  counts and the median-vs-mean P4 preview. Secondary tables to CSV.
- **Max new code modules: 1 — *expected 0*.** Reuses `xen.third_barrier` (EXP-058) with the next-`rd`-confirm
  locator pointed at **MA segments** (the EXP-058 MA-seg-baseline path already implements this) and the EXP-061/064
  **dual-object** MA pipeline; `/THIRD-TIME` caps via re-calling `adaptive_time_caps_by_epoch(floor=F)` on MA-segment
  durations; the only new code path vs EXP-064 is the per-variant third-barrier build in place of EXP-064's
  per-variant favourable-target build, plus the per-object × per-variant RM/contrast loop (already dual-object in
  EXP-064). At most one thin orchestration wrapper under `code/`; **no new `xen/` analysis module**.

## Metric Denominators & Zero-Baseline

- **Per-event realised gross return** (ATR units) is defined for every **qualifying** event of a variant (of an
  object) — built-window outcome `FAV`, `ADV`, or `TIMECAP`. Return = `rd·(exit_price − C)/ATR_entry`
  (`xen.expectancy.realised_returns`), `exit_price` the P15 fill (target for FAV/ADV; cap/event-bar real close for
  TIMECAP), `ATR_entry` = Wilder ATR(14) at the harami entry bar.
- **Per-cell endpoints:** `E_cell_median` (binding, P3/P14) and `E_cell_mean` + 10% trimmed mean (P4 diagnostic),
  each over the variant's qualifying-event population **per object**, each with its own fixed-seed bootstrap CI.
  `DATA_CENSORED` and warmup-excluded events are **excluded** from median/mean/trim and **disclosed as counts** per
  cell per variant per object. The censoring fraction (`DATA_CENSORED` / built window) is a prominently disclosed
  secondary because it grows with horizon — the cost side of the lever.
- **Zero-baseline / power:** a cell with **< 30 qualifying events** for a variant (of an object) is
  **NOT_VIABLE-by-power** for that variant/object (non-reportable), never an undefined/infinite ratio. Longer
  horizons (T48, `/THIRD-EVENT` backstop) are expected to deplete the most; the MA substrate qualifies a (typically
  larger) native count (8360-class) than the hybrid (3202-class); depleted cells disclosed, never defaulted. Worst-5%
  tail-share: a cell with 0 negative return mass reports tail-share = 0.0 (finite), never NaN/inf.
- **First-hit `r`** = `n_FAV/(n_FAV+n_ADV)` (TIMECAP excluded, EXP-049 convention), disclosed per variant per
  object. Because fav/adv geometry is held at MA benchmark (1:1), `r` is expected to stay near 0.50; the lever moves
  expectancy through the **TIMECAP exit price** and the **FAV-vs-TIMECAP composition**, not `r`. Never binding.
- **Disclosed secondaries (never binding):** per-variant censoring fraction; first-hit `r`; mean + 10% trimmed mean
  + worst-5% tail-share; win rate; TIMECAP fraction; `/THIRD-EVENT` event-vs-backstop split; per-variant
  warmup-exclusion counts — all per object.
- **Deferred disclosed secondaries (runtime/budget; NOT computed in EXP-065, explicitly):** the `/STRONG-HA`
  conditioning arm and the full ZigZag-substrate third-barrier surface, including the single ZigZag benchmark
  contrast vs EXP-058 (recorded in `run_metadata.json`).

## Data Requirements

Per cell (instrument × domain), TRAIN slice only: lazy `pl.scan_parquet`; `analysis_rows = int(total*0.7)`,
`train_rows = int(analysis_rows*0.7)`; collect only the first `train_rows` file-order 1-minute rows (F01 prefix;
never sort/collect the full file, never read TEST/holdout); assert chronological; `train_end_ts` = last `CloseTime`.
Aggregate each member domain (5m strict; others `min_coverage=0.90`); fence to `CloseTime ≤ train_end_ts`; generate
HA candles; run ZigZag (`atr_mult=1.0`) → confirmed moves + `confirm_indices` (hybrid conditioning mask + disclosed
contrast); run `ma_segment_moves` (MA(20,50) on real close) → confirmed MA segments + crossover indices + the MA
in-progress state (`live_in_progress_state` on MA arrays, supplying `rd` / `M_sofar` / `start_epoch`, shared by both
objects); detect haramis on HA candles aligned by `CloseTime`; build **both** conditioned populations — hybrid
(`zz["stat"]["retained_p75"]`, byte-identical to EXP-053/060/061 `H0`) and native (`ma["stat"]["retained_p75"]`,
byte-identical to EXP-061 `M0`); compute the MA benchmark fav + adv levels (`benchmark_barriers` on MA references),
then each predeclared third-barrier variant's per-event `n_event` — BENCH/T12/T24/T48 via
`adaptive_time_caps_by_epoch(floor=F)` on MA-segment durations, `/THIRD-EVENT` via the next-`rd` MA-segment-confirm
locator + 8× backstop — resolve each variant under P15 (`resolve_path_ordered`) **on each object's population**,
compute ATR-normalised gross returns; build the per-object per-variant matched-random-on-MA null (RM-* native, RH-*
hybrid) through the identical pipeline; bootstrap per-cell median + mean + 10% trimmed mean per variant per object
(fixed seed) + worst-5% tail-share; compute `variant − RM` (binding, independent) and `variant − benchmark` (paired)
contrasts per object; reconcile native `M-BENCH` ↔ EXP-061 `M0` / EXP-060B `BENCH-MA` and hybrid `H-BENCH` ↔ EXP-061
`H0` (and populations vs EXP-053); compose by P11 with the non-4h rule **per object**; second full pass for
determinism. `tqdm` over the 99-cell grid (per-instrument worker); bounded per-cell memory (forward scans bounded by
the cap / `8 × bench_N`; release per-cell arrays after summarisation; do not retain all domain frames or all
bootstrap draws). Outputs (`results/`): `per_cell_expectancy.parquet` (per cell × variant × **object**: median/mean/
trimmed + CIs, tail-share, variant−RM and variant−benchmark contrasts, n_qualifying, censoring/warmup counts, TIMECAP
fraction, `/THIRD-EVENT` event-vs-backstop split, `r`, win rate, viability + beats-RM + beats-benchmark flags);
`third_barrier_map.csv` (binding `/STRONG-STAT` summary per variant per object + P11 non-4h tally); `secondary_map.csv`
(`r`, censoring, TIMECAP composition per object; `/STRONG-HA` + ZigZag benchmark contrast deferred — see Exclusions);
`reconciliation.csv` (native `M-BENCH` ↔ EXP-061 M0 / EXP-060B BENCH-MA; hybrid `H-BENCH` ↔ EXP-061 H0; populations
vs EXP-053/060/061, per object); `composition_readout.json` (per-object per-variant P11 non-4h, wins, censoring
summary, EVIDENCE_* fork → G-015 input); `run_metadata.json` (seed, frozen + new predeclared constants,
EXP-058/060/060B/061/064 source paths/hashes, parallelism note, holdout fence, `disclosed_secondaries_not_computed`).
Bounded plots from collected per-cell summaries (no reloads), rendered per object. Output **byte-identical across
`--workers`** counts (order-independent per-cell RNG + fixed merge order).

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

Fork **EXP-064's dual-object `code/run_experiment.py`** (it already builds both conditioned populations — hybrid
`H0` via `bench_signal_arm`'s `cond_mask` override and native `M0` — the shared MA in-progress geometry, the
per-object matched-random controls via `matched_random_arm`, the corrected reconciliation roles, the P4 mean/trim/tail
bootstrap, and a per-variant OAT loop with per-object reporting). Changes, all bounded: **(1)** replace EXP-064's
per-variant **favourable-target** build with the per-variant **third-barrier** build — compose EXP-058's
`xen.third_barrier` (`/THIRD-TIME` floor re-call via `adaptive_time_caps_by_epoch(floor=F)` on MA-segment durations;
the causal next-`rd`-confirm `/THIRD-EVENT` locator **pointed at MA segments** + 8× backstop), holding the favourable
at MA benchmark 50% and the adverse at MA benchmark 1:1; the 5-variant third-barrier grid replaces EXP-064's 8-variant
favourable grid. **(2)** Run each variant on **both** object populations — native (`ma["stat"]["retained_p75"]`) and
hybrid (`zz["stat"]["retained_p75"]` via `cond_mask`; verify the ZigZag mask indexes onto the MA entry order by
`CloseTime`) — and report individually with an `object` tag on every per-cell × per-variant row. **(3)** Run
`matched_random_arm` through each variant's third-barrier pipeline to produce the per-object nulls RM-* (native) /
RH-* (hybrid) — each matched to its **own** object's variant count, excluding its **own** object's signal entries, on
**fresh dedicated RNG purposes per object/variant** so no existing stream shifts — and the per-object per-variant
`variant − RM` (`contrast_ci`) and `variant − benchmark` (`paired_median_contrast_ci`) contrasts. **(4)** Reconcile
**native `M-BENCH` ↔ EXP-061 `M0` / EXP-060B `BENCH-MA`** and **hybrid `H-BENCH` ↔ EXP-061 `H0`** exactly (per-cell
median + count, `RECON_TOL = 1e-9`; SUBSTRATE/METHOD_DEFECT if not), and reconcile populations vs EXP-053 (hybrid
3202-class) / EXP-061 (native 8360-class). **(5)** Emit **per-object** P11 (non-4h) / signal-vs-RM / lever readouts
with the binding **censoring** disclosure beside every win count (never pooled). Keep EXP-064's per-instrument
`ProcessPoolExecutor` with native-thread pinning (`POLARS_MAX_THREADS=1` etc.) and fixed-order reassembly
(byte-identical output for any `--workers`). Fixed per-cell seed throughout (P3); `tqdm`; bounded memory; **do not
adjudicate G-015** (single gate after the full slate). The existing native/hybrid BENCH median+mean RNG paths must
stay byte-identical to EXP-061 (use new RNG purposes for the new third-barrier variants and their nulls only) so the
EXP-061 reconciliation holds for both objects.
