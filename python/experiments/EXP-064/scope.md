# Experiment: EXP-064 — MA(20,50)-Substrate Favourable-Target Geometry (Conditioned HA Harami; `/VPTARGET`, `/MAGTARGET` vs Benchmark 50%; **Dual Conditioning Object: Hybrid and Native**, Phase 015 Surface S1)

> **Re-run under `D0-amendment-001-dual-parallel-substrate.md` (2026-06-17).** The prior EXP-064
> scope measured a single MA favourable-target axis labelled *hybrid* but reconciled its benchmark
> arm to EXP-061 `M0` — which is the **native** object (MA-segment `/STRONG-STAT`, 8360-class), not
> the hybrid object (ZigZag-`/STRONG-STAT`, 3202-class). That is the propagated labelling defect the
> amendment corrects. This re-run emits the full 8-variant favourable-target axis **for both
> conditioning objects individually** (separate variant arms, separate matched-random nulls, separate
> per-cell viability, separate P11 composition, separate EVIDENCE fork — never pooled) and supersedes
> the prior single-object EXP-064 scope in place. EXP-064 was **paused** (no `results/`, no code);
> resumption is dual-object from the start, so no prior result is overturned — only the scope/plan.

> **Mandatory-reading precondition (Phase 015, binding — inherited from 014-B).**
> `../../docs/experiments-docs/checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/014-A-conditioning-gap-and-validation-lessons.md`
> was read in full before this scope was written. EXP-064 is the Phase 015 **favourable-target
> geometry** surface read (S1; mirrors EXP-056) on the **MA(20,50) substrate**, on **both**
> conditioning objects. The four mandatory rules are honoured, recorded so Stage 4 can check:
> - **(a) conditioning** — honoured, **and now disambiguated** (Amendment 001). Two live
>   `/STRONG-STAT`-conditioned HA-harami objects are measured individually over the **same** MA(20,50)
>   favourable/adverse/cap geometry: **hybrid** (filter on the in-progress confirmed *ZigZag* move —
>   entry population byte-identical to EXP-053/060/061's hybrid `H0`; the genuinely-new object) and
>   **native** (filter recomputed on the in-progress confirmed *MA segment* — the population EXP-061's
>   `M0` measured; reconciles to EXP-061 native `M0` / EXP-060B `BENCH-MA`). `/STRONG-STAT` (P7) is
>   binding in each; `/STRONG-HA` (P8) is a disclosed secondary arm. Only the **favourable-target
>   geometry** is varied (OAT); the signal, anchor, adverse model (benchmark 1:1), third barrier
>   (MA adaptive cap), and fills are held at the MA benchmark. Each object's matched-random-on-MA
>   control is a deliberate **null** (binding per P5), not a signal claim. The two objects are never
>   pooled.
> - **(b) harami-anchor** — honoured. Entry is the **harami confirmation-bar real close** `C` in both
>   objects. The MA(20,50) substrate supplies only the outcome geometry (`rd` / `M_sofar` /
>   favourable-target reference / adaptive cap); it does **not** move the anchor. The matched-random
>   controls intentionally break the anchor (that is what makes them nulls).
> - **(c) position-in-move descriptive-only / never a live filter** — honoured. EXP-050's position
>   metric is not used. The favourable-target references are **confirmed, completed** MA segments
>   (known at entry); no unconfirmed MA crossover enters any target, filter, or barrier.
> - **(d) expectancy / not first-hit `r`** — honoured. The binding endpoint is the Phase 015 **median**
>   gross per-event expectancy (P3/P14), computed **per object individually**. The **mean** (raw + 10%
>   trimmed + worst-5% tail-share, each CI'd) is the P4 **diagnostic co-primary**, disclosed; first-hit
>   `r` is disclosed for single-leg arms only and never binds.
> EXP-064 does **not** treat the EXP-049 `r≈0.50` null or EXP-050 front-loading as evidence against the
> family — those measured the *unconditioned ZigZag* object.

**Phase / checkpoint:** `2026-06-17-015-ma-substrate-conditioned-harami-full-surface` (Phase 015; **G0 PASS 2026-06-17**).
**Family / candidate:** `CF-HA-HARAMI-001` (`REGISTERED`, OPEN) · Phase 015 surface **S1** ·
`CF-HA-HARAMI-001/HYP-017` — EXP-064 (Phase 015 batch, `multiplicity-registry.md` line 488). Exercises the
registered branches `CF-HA-HARAMI-001/VPTARGET` and `CF-HA-HARAMI-001/MAGTARGET` on the registered
`CF-HA-HARAMI-001/MA-SUBSTRATE` (both modes `hybrid` and `native`, parallel first-class per Amendment 001).
**Registry precondition (satisfied):** `MA-SUBSTRATE` + **both** conditioning modes (`hybrid`, `native`,
parallel first-class per `D0-amendment-001`) **REGISTERED** (Phase 015 batch, 2026-06-17, G0 PASS);
`/VPTARGET`, `/MAGTARGET`, the benchmark 3-barrier geometry, and the matched-random baseline pre-exist
(Phase 014 / 014-B + EXP-061 reuse). HYP-017/EXP-064 is the listed plan (`EXP-056`-analog, S1), now emitting
both objects individually. **No new countable item is introduced here.**
**Surface role:** Surface read 1 of the Phase 015 post-lead slate — favourable-target geometry on MA, on
**both** objects. EXP-061 (L1) established the **native** MA benchmark geometry is signal-attributable
(EVIDENCE_FOR; `M0 ≻ RM0` generalised beyond the champion, 8 cells) while the **hybrid** object generalised
in only 1 cell (EVIDENCE_AGAINST) — so the favourable-target question must be read **per object**. EXP-064
asks whether **changing only the favourable target** improves the conditioned harami's MA-substrate gross
median expectancy, on each object. The surface runs **regardless** of the lead (P9 no-early-closure); output
feeds the single terminal **G-015** after the full slate. **No closure or candidate registration here.**
**Governing design / D0:** `design.md` (§3 objective; §5 slate S1; §7 G-015 criteria, judged per object) +
`D0-predeclarations.md` (P1 substrate; **P2 both objects parallel/individual**; P3 median binding + fixed seed;
P4 mean diagnostic; **P5 matched-null per object every read**; P6 non-4h composition; P8 OAT grids reused
unchanged; P9 slate; P10 power; **P12 reconciliation roles — native↔EXP-061 `M0`/EXP-060B 1e-9, hybrid↔EXP-061
`H0` 1e-9 + EXP-053 population**) + `D0-amendment-001-dual-parallel-substrate.md`. Inherits 014-B
P14/P15/P16/P20 and the family spec `candidate-families/harami.md` (favourable-target variants).
**Reuses (no new `xen/` module expected):** the EXP-056 favourable-target machinery
(`xen.favourable_targets`: volume-profile builder, trailing-magnitude target, `barriers_from_fav`,
`paired_median_contrast_ci`) **applied on MA-segment references**; the EXP-061 **dual-object** MA pipeline
(`ma_segment_moves`, `_ma_context`, `_zz_context`, `bench_signal_arm` with its `cond_mask` override,
`matched_random_arm`, `resolve_arm`) and its P4 mean-diagnostic functions (`bootstrap_stat_distribution`,
`_trimmed_mean`, `_tail_share_worst5`); `xen.expectancy.*` (`live_in_progress_state`, `live_strong_stat`,
`adaptive_time_caps_by_epoch`, `benchmark_barriers`, `resolve_path_ordered`, `realised_returns`,
`qualifying_mask`, `bootstrap_median_distribution`, `bootstrap_mean_distribution`, `median_ci`, `contrast_ci`);
ZigZag (`xen.zigzag`, hybrid conditioning mask + disclosed contrast), harami (`xen.ha_harami`), `/STRONG-HA`
(`xen.strong_move.annotate_ha_impulse`), confirmation indices (`xen.capture_barriers`). **EXP-063's dual-object
`code/run_experiment.py` is the closest structural fork base** (it already runs a per-variant OAT loop on
**both** object populations with per-object RM nulls and the P4 mean/trim/tail diagnostic — EXP-064 swaps its
adverse axis for the favourable-target axis).

## Slot & ledger accounting (binding)

- **0 candidate slots, 0 TEST reads.** Characterization/diagnostic per the Phase 015 D0 (P11). No countable
  item is introduced: `MA-SUBSTRATE` (+ both `hybrid`/`native` modes) is registered at G0; `/VPTARGET`,
  `/MAGTARGET`, the benchmark geometry, and the matched-random nulls pre-exist. A slot is consumed only at a
  G-015 PROCEED on a future scope.
- **No TEST stratum is read.** All work on the **TRAIN** slice (first 70% of the first-70% analysis set; F01
  file-order prefix; identical fence to EXP-049/053–063). Hybrid population byte-identical to EXP-053/060/061
  `H0`; native population byte-identical to EXP-060B/061 `M0`; no new stratum opened; `test-read-ledger.md`
  requires no entry; global-holdout seal carries forward. No HA-harami TEST stratum has ever been read.
- All work **gross**; detection on HA candles; **all outcome metrics on real-price OHLC**; MA(20,50) computed
  on **real close** (identical to EXP-060/061 `ma_segment_moves`). No HA price enters any metric.

---

## Hypothesis

On the `/STRONG-STAT`-conditioned HA harami, **for each conditioning object individually** (hybrid and native),
99-cell TRAIN grid, MA(20,50) substrate, entered at the harami confirmation-bar real close `C` and faded against
the in-progress confirmed-MA-segment move, with the adverse target held at the MA benchmark 1:1 model and the
third barrier at the MA-defined adaptive cap (OAT on the **favourable leg only**): **at least one alternative
favourable-target geometry** — `/VPTARGET` (volume-profile levels of the prior *completed MA segment*) or
`/MAGTARGET` (trailing-MA-segment-magnitude distances) — produces **higher gross per-event median expectancy**
(P3/P14, ATR-normalised, P15 fills, real prices) than the **benchmark 50%-of-`M_sofar` favourable target**, on
the binding `/STRONG-STAT` arm, **and** that winning variant is **signal-attributable** (beats its own
same-object matched-random-on-MA null, P5).

The two objects are judged **individually, never pooled** (P2); the phase-level reading of this lever is the
**stronger object's** outcome (consistent with EXP-061: native is the object that expresses the edge), with the
other object's result documented in parallel.

**Falsifiable, per object:** if **no** alternative favourable-target variant simultaneously (a) is
median-viable per cell, (b) beats its same-object matched-random-on-MA null (`variant − RM` contrast CI_low > 0),
and (c) beats that object's benchmark MA variant (`variant − benchmark` contrast CI_low > 0), all composed by
P11 with the P6 non-4h breadth rule, then favourable-target geometry is **not** an MA-substrate lever that
improves conditioned capture **for that object** (a valid characterization result feeding G-015 — never a
closure inside Phase 015; the surface runs regardless, P9).

## Question

On the MA substrate, **for each object (hybrid, native)**, does changing only the **favourable target** — from
the benchmark 50%-of-MA-segment magnitude level to a volume-profile level of the prior completed MA segment
(`/VPTARGET`: near VA edge / POC / far VA edge) or a trailing-magnitude distance (`/MAGTARGET`:
`{0.5,1.0} × median(trailing-{5,20} MA-segment magnitudes)`) — improve the conditioned HA-harami's gross
per-event median expectancy vs that object's benchmark, per cell and composed across the 99-cell grid, beat the
same-object matched-random-on-MA null, and which variant (if any) wins? Does the EXP-056 ZigZag-substrate result
(0/8 variants beat benchmark) reproduce or differ on MA, and does the picture differ between the hybrid and
native objects?

---

## Scope Boundaries

### Data Views

- **Real domain bars** (5m strict; 15m/30m/1h/2h/4h via `xen.bar_aggregator.aggregate_ohlc`,
  `min_coverage=0.90` — identical to EXP-049/053–063/VAL-004) for the MA(20,50)-crossover substrate
  (`ma_segment_moves` on real close), the ZigZag substrate (`atr_mult=1.0`, hybrid conditioning mask + disclosed
  contrast), confirmed moves/segments, `/STRONG-STAT` magnitudes (on ZigZag for hybrid / on MA segments for
  native), the favourable-target construction (volume profile and trailing magnitudes on MA segments), the
  MA-defined adaptive cap, the benchmark/variant favourable levels, P15 fills, ATR normalisation, and **all**
  outcome metrics.
- **Heiken Ashi candles** (`xen.heiken_ashi_generator`) for **harami detection only** (frozen EXP-048
  detector) and the disclosed `/STRONG-HA` arm. **No HA price enters any metric.**
- **`TickVolume`** (domain-bar, summed from constituent 1-minute bars by `xen.bar_aggregator`) is the only
  volume input to `/VPTARGET`. It is **broker tick count, a proxy for traded volume**; the proxy limitation is
  disclosed in every `/VPTARGET` result.

### Event population (two conditioning objects, measured individually over the same MA favourable geometry)

Both objects share the **same** frozen HA-harami detection, the **same** MA(20,50) outcome geometry
(`rd` / `M_sofar` / favourable target / adaptive cap), and the **same** real bars; they differ **only** in the
`/STRONG-STAT` conditioning filter (P2):

- **Hybrid (`H-*`).** Qualifies iff the harami passes `/STRONG-STAT` p75 on the **in-progress confirmed ZigZag
  move** magnitude-so-far `M_sofar^{ZZ} = |C − start_pivot|` ≥ p75 of the trailing-20 confirmed-ZigZag-move
  magnitudes (hybrid mode). The conditioning mask is **byte-identical to EXP-053/060/061's hybrid `H0` set**
  (the same `live_in_progress_state` / `live_strong_stat` on the ZigZag move, applied through the MA context via
  the `bench_signal_arm` `cond_mask` override). MA supplies only the geometry. **This is the genuinely-new
  object** for the favourable axis (a ZigZag-conditioned favourable-target surface over MA geometry was never
  computed before Amendment 001). Its internal-lineage anchor is **EXP-061 `H0`** (the `H-BENCH` variant
  reproduces it); its conditioning population reconciles to **EXP-053's 3202-class ZigZag-`/STRONG-STAT` set**;
  it has **no EXP-060B/056 outcome back-reconciliation anchor**.
- **Native (`M-*`).** Qualifies iff the harami passes `/STRONG-STAT` p75 on the **in-progress confirmed MA
  segment** magnitude-so-far ≥ p75 of the trailing-20 confirmed-MA-segment magnitudes (recomputed on MA
  segments; causal — only segments confirmed at/before the harami bar). **Population byte-identical to EXP-061
  native `M0` and EXP-060B `BENCH-MA`**; the `M-BENCH` variant **reconciles to them (1e-9)** — the object the
  prior (mislabelled) EXP-064 scope actually intended.

Entry anchor is the harami close `C` in both. The **trade / reversal direction** `rd` and the **MA-segment
magnitude-so-far** `M_sofar` used to build every favourable target come from the **MA(20,50) substrate**
(`ma_seg_arm`: last confirmed MA crossover → `C`), exactly the EXP-060/061 construction; the conditioning filter
differs by object but the geometry is the same. Construction reuses `xen.expectancy.live_in_progress_state` +
`live_strong_stat` and the EXP-060 `ma_segment_moves`/`ma_seg_arm` — the **same functions EXP-053/060/061 used**.
Each object's matched-random-on-MA nulls draw **non-harami** in-MA-regime timestamps, **matched-count to that
object's qualifying count per variant**, on **independent dedicated RNG streams** distinct from the other
object's.

### Entry anchor

The **harami confirmation-bar real close** `C` (real domain-bar close at the harami timestamp), strictly before
any ZigZag/MA trend-change confirmation. Identical to EXP-053/061.

### Favourable-target variants on MA (predeclared sweep; OAT on the favourable leg only; **per object**)

All variants define a **favourable price level** `fav` in the reversal direction `rd` from `C`; the favourable
distance is `fav_dist = rd·(fav − C)`. The **adverse** target is the MA benchmark 1:1 model
`adv = C − rd·fav_dist` (benchmark adverse is 1:1, so adverse distance = favourable distance for every variant).
The **third barrier** is the MA-defined adaptive cap (the `ma_seg_arm` cap; benchmark, P4-analog). Fills are P15.
**Each variant is built and resolved twice — once on the hybrid population, once on the native population — and
reported individually.** **Validity rule (all variants, both objects):** an event is *valid* iff `fav_dist > 0`
(target on the reversal side of `C`) **and** the reference context is defined; events with `fav_dist ≤ 0` or an
undefined profile/reference are **excluded-with-record** (a disclosed degenerate count per cell per variant per
object), never silently clamped.

1. **Benchmark (reference variant, MA benchmark; `{M,H}-BENCH`):** `fav_dist = 0.50 × M_sofar`;
   `fav = C + rd·0.50·M_sofar`, `M_sofar` from the MA segment (`ma_seg_arm`). The **native** `M-BENCH` arm **is
   EXP-061's `M0` / EXP-060B `BENCH-MA`** (the P12 native reconciliation target); the **hybrid** `H-BENCH` arm
   **is EXP-061's `H0`** (the P12 hybrid reconciliation target). Each is the anchor every same-object alternative
   is contrasted against.

2. **`/VPTARGET` — volume profile of the prior completed MA segment (LOOKBACK=1), binding reference.** Build a
   volume profile from the domain bars constituting the **immediately preceding *completed* confirmed MA
   segment** (the last confirmed MA segment before the in-progress one, known at entry; bars from that segment's
   start crossover to its confirming crossover). Each constituent bar's `TickVolume` is distributed **uniformly
   across its `[Low, High]` range** into fixed-width price bins (bin width `= 0.10 × ATR_entry`, predeclared;
   ≥1 bin). From the profile:
   - **POC** = centre of the maximum-volume bin (**VP baseline variant**).
   - **Value area = 70%** of total profile volume, the contiguous bin run grown outward from the POC; low
     boundary `VAL`, high boundary `VAH`.
   - **near VA edge** = VA boundary with the **smaller** valid `fav_dist`; **far VA edge** = VA boundary with the
     **larger** valid `fav_dist` (among `{VAL, VAH}` with `rd·(level − C) > 0`).
   - **Insufficient-profile rule:** a prior completed MA segment with **< 3 domain bars** → no valid profile →
     event excluded-with-record (disclosed); a level on the wrong side of `C` → that *level's* variant event
     excluded-with-record.
   - Three binding `/VPTARGET` variants per object: **VP-POC** (baseline), **VP-near-VA**, **VP-far-VA**.

3. **`/VPTARGET` — in-progress-MA-segment POC (disclosed secondary only).** Identical construction but the
   profile is built from the **in-progress MA segment's** domain bars (segment start crossover → entry bar).
   Retained to **empirically expose** the path-dependence concern (EXP-056 operator rationale); **never
   binding**, reported as a disclosed secondary, per object.

4. **`/MAGTARGET` — trailing-MA-segment-magnitude distance (LOOKBACK>1; predeclared grid).**
   `fav_dist = frac × median(magnitudes of the trailing W confirmed MA segments confirmed strictly before the
   harami)`, `fav = C + rd·fav_dist`, over the grid `frac ∈ {0.5, 1.0} × W ∈ {5, 20}` (4 variants per object:
   MAG-0.5×5, MAG-1.0×5, MAG-0.5×20, MAG-1.0×20). Magnitude estimate only — no absolute price level. Warmup:
   **fewer than `W` confirmed MA segments** before the harami → event excluded-with-record for that variant
   (disclosed). `fav_dist > 0` always holds (magnitudes positive).

**Total predeclared favourable-target variants per object:** 1 benchmark + 3 binding `/VPTARGET` + 4 `/MAGTARGET`
= **8 binding variants**; plus 1 disclosed-secondary in-progress VP-POC. **× 2 objects = 16 binding variant arms
total** (reported individually, never pooled). Each variant runs on the binding `/STRONG-STAT` arm of its object;
the `/STRONG-HA` arm is a disclosed secondary (deferred for runtime — see Exclusions).

### Matched-random-on-MA null (RM; **binding per P5**, per variant, **per object**)

For **each** favourable-target variant **of each object**, a **matched-count random in-regime** control (the
EXP-060B matched-random-in-MA-regime selection, reused unchanged; same cell / direction / regime, valid live MA
state, EXP-021/027 exclusion convention, **matched-count to that object's qualifying harami count for the
variant**, **excluding that object's conditioned-harami entries**) is run through the **identical variant
favourable-target + adverse + cap + P15 pipeline** on the MA substrate. Native nulls are `RM-BENCH/RM-VP-*/RM-MAG-*`;
hybrid nulls are `RH-BENCH/RH-VP-*/RH-MAG-*`. **Signal-attribution requires the variant beats its own same-object
RM null** (`variant − RM` median contrast CI_low > 0; P5). The RM draws are **independent** of the harami events
(no common subset to pair); the contrast uses the independence-assuming `xen.expectancy.contrast_ci`. The hybrid
and native nulls draw from the **same MA in-regime pool** but are matched to **different counts** and exclude
**different signal entries**, on **disjoint dedicated RNG streams**; the two objects' contrasts are **never
pooled**.

### Adverse target, third barrier, fills (MA benchmark; held fixed across variants and objects)

- **Adverse (MA benchmark 1:1):** `adv = C − rd·fav_dist` — distance equals the variant's favourable distance.
- **Third barrier (MA-defined adaptive cap, benchmark):** the `ma_seg_arm` adaptive cap
  (`N = max(6, round(1.5 × median duration of the trailing 20 confirmed MA segments))`,
  `xen.expectancy.adaptive_time_caps_by_epoch` on the MA `confirm_epoch`/`confirm_idx`), reused unchanged for
  every variant and object. Warmup-excluded when the cap is undefined (insufficient confirmed MA segments),
  disclosed.
- **Fill model (P15, method standard):** path-ordered intrabar fills — bullish bar (`Close ≥ Open`):
  `Open → Low → High → Close`; bearish (`Close < Open`): `Open → High → Low → Close`. TIMECAP exits at the cap
  bar's real close. Reuse `xen.expectancy.resolve_path_ordered`. Documented approximation; disclosed.

### Parameters (all frozen / predeclared; no tuning)

MA(20,50) on real close (fixed; P1 — not swept); ZigZag Wilder ATR(14), `ATR_MULT = 1.0` (hybrid conditioning
mask + disclosed contrast); `/STRONG-STAT` trailing-20, ≥p75 (P7; on ZigZag for hybrid / on MA segments for
native); `/STRONG-HA` `X=3` (P8; disclosed/deferred); benchmark favourable `X = 50%` of `M_sofar` (MA); adverse
1:1; MA adaptive cap `(k=1.5, window=20, floor=6, statistic=median, min_moves=5)`-analog as in EXP-060/061;
ATR-normalisation divisor = Wilder ATR(14) at the harami entry bar (P14); bootstrap `b = round(m^(1/3))`,
`N_BOOT = 10_000`, **fixed per-cell seed (P3)** — `np.random.default_rng([BASE_SEED, cell_index, purpose])` with
dedicated purposes per object/variant/statistic so the native `M-BENCH` median path stays byte-identical to
EXP-061 `M0` and the hybrid `H-BENCH` path byte-identical to EXP-061 `H0`. **Favourable-target parameters (this
scope):** VP reference = prior completed MA segment (LOOKBACK=1); VP bin width `= 0.10 × ATR_entry`; VP value
area `= 70%`; VP insufficient-profile floor `= 3` domain bars; `/MAGTARGET` grid `frac ∈ {0.5, 1.0} × W ∈ {5, 20}`,
statistic = median (over MA-segment magnitudes); mean trim fraction **10%**, tail-share **worst-5%** (P4). None
tuned against outcomes; sensitivity not swept beyond the predeclared grid.

### Instruments / cells / time range

The **99-cell EXP-049/053–063 member grid** (17 instruments × {5m,15m,30m,1h,2h,4h} − 3 COVERAGE_EXCLUDED:
US500-4h, JP225-2h, JP225-4h). Per-cell first, then **P11** with the **P6 non-4h rule** (≥5 cells over ≥3
instruments, with ≥3 qualifying cells outside the 4h domain) for any "winning variant" claim, **per object**.
**TRAIN only** = first 70% of the first-70% analysis set (F01 file-order prefix; identical fence to
EXP-049/053–063; `train_end_ts` = last `CloseTime` of the first `int(int(total_rows*0.7)*0.7)` file-order
1-minute rows). TEST and the final-30% **global holdout** are **not** read. Forward windows clipped to
`train_end_ts`; truncated → `DATA_CENSORED`. DE30 carries the truncated-coverage disclosure.

### Look-ahead / causality discipline (binding)

- ZigZag and MA(20,50) segmentation are future information until confirmed. The signal (harami +
  `/STRONG-STAT`, on the ZigZag move for hybrid / the MA segment for native), `rd`, `M_sofar`, and every
  favourable target use **only confirmed, completed prior moves/segments and the entry bar's own real close** —
  never an unconfirmed pivot/crossover or any future bar. The VP reference MA segment is confirmed at entry; its
  bars are all `CloseTime ≤ C`'s bar. `/MAGTARGET` magnitudes are from MA segments confirmed strictly before the
  harami. The MA adaptive cap uses only MA segments confirmed strictly before the harami. MA(20,50) `_sma` is
  trailing. The native `/STRONG-STAT` filter references only confirmed prior MA segments. Matched-random entries
  are constructed causally with the identical pre-entry-only state, per object.
- Excursion scans read only bars `[entry_idx+1, cap]`, fenced `CloseTime ≤ train_end_ts`; a window truncated by
  the TRAIN edge before resolution is `DATA_CENSORED` (excluded, disclosed), never measured against truncated
  data.
- Ordering/alignment by `CloseTime`, never bar index across views.

### Real-price outcome discipline

Harami detected on HA candles; `M_sofar`, the volume profile (real-bar prices + `TickVolume`), trailing MA
magnitudes, ATR normalisation, fav/adv levels, fills, expectancy, mean/trim/tail, `r`, win rate, and censoring
all on real domain-bar OHLC. MA(20,50) computed on **real close**. **No HA price in any metric.**

### Exclusions

- No costs (gross only).
- **Favourable-target geometry only, on both objects.** No `/ADV-EXTREME`/`/ADV-NONE` (EXP-063 adverse, adverse
  held at benchmark 1:1), no `/THIRD-EVENT`/`/THIRD-TIME` (EXP-065, third barrier held at the MA adaptive cap),
  no `/EXIT-PARTIAL`/`/EXIT-TRAIL-STRUCT` (EXP-066), no combined system (EXP-067 hybrid / EXP-068 native). No
  `/BARCFG`/`/CONFIRM` overlays; no position-in-move *filter*; **no MA-parameter sweep** (MA(20,50) fixed).
- No parameter tuning; **no post-result variant or object selection** (all 8 predeclared variants on **both**
  objects reported and composed); no gate adjudication (single G-015 after the full slate — EXP-064 emits a
  characterization readout only). No TEST or holdout contact; no candidate slot; no TEST read.
- **Deferred disclosed secondaries (runtime/budget; NOT computed here, explicitly — not silently):** the
  `/STRONG-HA` conditioning arm and the full **ZigZag-substrate favourable surface** — **including the single
  ZigZag benchmark contrast vs EXP-056**. With the favourable axis now run on **two** conditioning objects
  (16 binding variant arms + their nulls per cell), computing it on further conditioning populations (the
  ZigZag substrate geometry has its own M_sofar / cap pipeline) would multiply the per-cell arm count against
  the performance mandate while adding only non-binding robustness context — exactly the EXP-063 dual-object
  deferral pattern (governance-APPROVED). The disclosed **in-progress VP-POC** arm **is** computed
  (`secondary_map.csv`). The deferral is recorded in `run_metadata.json` (`disclosed_secondaries_not_computed`);
  if G-015 needs the ZigZag comparison, it is a bounded follow-up.

## Success / Failure Criteria (per object, never pooled)

All **gross**, per-cell first, P11-composed with the **P6 non-4h rule** (≥5 cells over ≥3 instruments, ≥3
outside 4h). Binding endpoint = **median per-event gross expectancy** `E_cell` (ATR units, P15 fills), on the
**`/STRONG-STAT` arm**; per-cell viable iff **CI_low > 0** (regime-clustered moving-block bootstrap, one-sided
95%, fixed seed) **AND ≥ 30 qualifying events**. The **mean** (raw + 10% trimmed + worst-5% tail-share, each
CI'd) is the P4 disclosed diagnostic, never a viability gate. The fork is computed **separately for each
object**; the phase-level reading is the stronger object's, the other documented in parallel.

- **EVIDENCE_FOR (a favourable-target lever helps on MA, for that object):** ≥1 alternative variant **(a)** is
  median-viable per cell **AND (b)** beats its same-object matched-random-on-MA null (`variant − RM` median
  contrast CI_low > 0; P5 signal-attribution) **AND (c)** beats that object's benchmark MA variant
  (`variant − benchmark` contrast CI_low > 0), all composed by **P11 with the non-4h breadth rule**. The
  winning variant(s), their RM margin, and their benchmark margin are the deliverable; no candidate registration
  (G-015 only).
- **EVIDENCE_AGAINST (favourable geometry is not an MA lever for that object):** no alternative variant clears
  the combined (viable ∧ beats-RM ∧ beats-benchmark) P11 quorum for that object. Recorded as a measured-negative
  characterization; routing deferred to G-015. **Family stays OPEN** — the surface (S2/S3/S4, both objects) runs
  regardless (P9).
- **INCONCLUSIVE (power-limited):** fewer than the P11 quorum of cells reach ≥30 qualifying events on the
  variants of interest for that object (validity/warmup exclusions deplete counts; the hybrid object — 3202-class
  — is expected more power-limited than native — 8360-class), no correctness failure. Disclosed; never defaulted
  to a ratio.
- **SUBSTRATE/METHOD_DEFECT:** any reconciliation, determinism, causality, or invariant failure → fix before
  reporting. Invariant checks: (i) the **native benchmark arm `M-BENCH` reproduces EXP-061 `M0` / EXP-060B
  `BENCH-MA`** and the **hybrid benchmark arm `H-BENCH` reproduces EXP-061 `H0`** per-cell median + qualifying
  count to float tolerance (`RECON_TOL = 1e-9`); (ii) population reconciliation: hybrid ↔ EXP-053/060/061 `H0`
  (3202-class), native ↔ EXP-060B/061 `M0` (8360-class), exact per object; (iii) **matched-count holds per
  object** — each variant's RM/RH qualifying-draw count equals that object's cell variant signal-arm count;
  (iv) the 1:1 adverse stop, when it binds, closes the position at the same bar/level; (v) every exit price is a
  real-bar P15 fill with `CloseTime ≤ train_end_ts`; (vi) `fav_dist > 0` for every counted event (validity rule).

Deliverable label: **MA_FAVOURABLE_TARGET_CHARACTERISED (dual-object)**, carrying — **per object, individually** —
the per-cell + P11 (non-4h) readout for every variant, the EVIDENCE_* classification, the variant−RM and
variant−benchmark contrasts, the disclosed mean/trim/tail diagnostic, the disclosed in-progress VP-POC,
first-hit `r` (single-leg arms), and all exclusion/censoring counts; plus the reconciliation table (native `M-BENCH` ↔ EXP-061 `M0` /
EXP-060B; hybrid `H-BENCH` ↔ EXP-061 `H0`; populations vs EXP-053/060/061). **No phase closure or candidate
registration here.**

## Complexity Budget (Comparative experiment)

- **Max distinct statistical methods: 4** — (1) regime-clustered moving-block bootstrap CI on a variant's
  **median** expectancy per cell (`bootstrap_median_distribution` + `median_ci`); (2) the same bootstrap on the
  per-cell **mean + 10% trimmed mean** (`bootstrap_stat_distribution`) + worst-5% tail-share point estimate (P4
  diagnostic, dedicated RNG streams); (3) `variant − RM` independent contrast CI (`contrast_ci`; binding, P5);
  (4) `variant − benchmark` paired-median contrast CI (`xen.favourable_targets.paired_median_contrast_ci`,
  common qualifying-event subset). Applied across the predeclared 8-variant grid **on two objects** (a
  parameterised sweep re-instrumented per object — **not new methods**; running the same 4 methods on a second
  object adds no distinct method) — consistent with EXP-056/EXP-063 and the Phase 015 lead.
- **Max visualisations: 5** — each rendered **per object** (hybrid and native panels/series, never pooled): (i)
  per-variant median-expectancy forest/CI per cell vs benchmark (headline); (ii) variant−benchmark and
  variant−RM contrast heatmap (variants × cells; non-4h cells marked); (iii) expectancy distribution by variant
  (pooled within object); (iv) P11 (non-4h) composition / "wins" map across variants (hybrid vs native
  side-by-side); (v) median-vs-mean (P4 skew preview) for the benchmark + best variant. Secondary tables to CSV.
- **Max new code modules: 1 — *expected 0*.** Reuses `xen.favourable_targets` (EXP-056) applied to MA-segment
  references and the EXP-061/063 **dual-object** MA pipeline; the only new code path vs EXP-063 is the
  per-variant favourable-target build (the existing `xen.favourable_targets` builder, fed MA-segment references)
  in place of EXP-063's per-variant adverse build, plus the per-object × per-variant RM/contrast loop (already
  dual-object in EXP-063). At most one thin orchestration wrapper under `code/`; **no new `xen/` analysis
  module**.

## Metric Denominators & Zero-Baseline

- **Per-event realised gross return** (ATR units) is defined for every **qualifying** event of a variant (of an
  object) — those with a built barrier (valid `fav_dist > 0`, profile/warmup defined) whose outcome is `FAV`,
  `ADV`, or `TIMECAP`. Return = `rd·(exit_price − C)/ATR_entry` (`xen.expectancy.realised_returns`), `exit_price`
  the P15 path-ordered fill (target for FAV/ADV; cap-bar real close for TIMECAP), `ATR_entry` = Wilder ATR(14)
  at the harami entry bar.
- **Per-cell endpoints:** `E_cell_median` (binding, P3/P14) and `E_cell_mean` + 10% trimmed mean (P4
  diagnostic), each over the variant's qualifying-event population **per object**, each with its own fixed-seed
  bootstrap CI. `DATA_CENSORED`, warmup-excluded, and validity-excluded events are **excluded** from
  median/mean/trim and **disclosed as counts** per cell per variant per object.
- **Zero-baseline / power:** a cell with **< 30 qualifying events** for a variant (of an object) is
  **NOT_VIABLE-by-power** for that variant/object (non-reportable), never an undefined/infinite ratio. The MA
  substrate qualifies a (typically larger) native count (8360-class) than the hybrid (3202-class); depleted
  cells disclosed, never defaulted. Worst-5% tail-share: a cell with 0 negative return mass reports
  tail-share = 0.0 (finite), never NaN/inf.
- **First-hit `r`** = `fav/(fav+adv)` defined per variant per object (single-leg geometry), disclosed (EXP-049
  comparability); never binding.
- **Disclosed secondaries (never binding):** mean + 10% trimmed mean + worst-5% tail-share; first-hit `r`; win
  rate; TIMECAP/censoring fraction; the in-progress VP-POC variant; per-variant validity/profile-exclusion
  counts; `/VPTARGET` `TickVolume`-proxy note — all per object.
- **Deferred disclosed secondaries (runtime/budget; NOT computed in EXP-064, explicitly):** the `/STRONG-HA`
  conditioning arm and the full ZigZag-substrate favourable surface (recorded in `run_metadata.json`).

## Data Requirements

Per cell (instrument × domain), TRAIN slice only: lazy `pl.scan_parquet`; `analysis_rows = int(total*0.7)`,
`train_rows = int(analysis_rows*0.7)`; collect only the first `train_rows` file-order 1-minute rows (F01
prefix; never sort/collect the full file, never read TEST/holdout); assert chronological; `train_end_ts` =
last `CloseTime`. Aggregate each member domain (5m strict; others `min_coverage=0.90`, carrying `TickVolume`);
fence to `CloseTime ≤ train_end_ts`; generate HA candles; run ZigZag (`atr_mult=1.0`) → confirmed moves +
`confirm_indices` (hybrid conditioning mask + disclosed `Z-BENCH` contrast); run `ma_segment_moves` (MA(20,50)
on real close) → confirmed MA segments + crossover indices + the MA in-progress state (`live_in_progress_state`
on MA arrays, supplying `rd` / `M_sofar` / `start_epoch`, shared by both objects); detect haramis on HA candles
aligned by `CloseTime`; build **both** conditioned populations — hybrid (`zz["stat"]["retained_p75"]`,
byte-identical to EXP-053/060/061 `H0`) and native (`ma["stat"]["retained_p75"]`, byte-identical to EXP-061
`M0`); for each qualifying harami compute every predeclared favourable target on MA references (benchmark, 3
VP-prior, 4 MAG, + disclosed in-progress VP-POC), set adverse 1:1 and the MA adaptive cap, resolve each under
P15 **on each object's population**, compute ATR-normalised gross returns; bootstrap per-cell median + mean +
10% trimmed mean per variant per object (fixed seed) + worst-5% tail-share; build the per-object per-variant
matched-random-on-MA null (RM-* native, RH-* hybrid) through the identical pipeline; compute `variant − RM`
(binding, independent) and `variant − benchmark` (paired) contrasts per object; reconcile native `M-BENCH` ↔
EXP-061 `M0` / EXP-060B `BENCH-MA` and hybrid `H-BENCH` ↔ EXP-061 `H0` (and populations vs EXP-053); compose by
P11 with the non-4h rule **per object**; second full pass for determinism. `tqdm` over the 99-cell grid
(per-instrument worker); bounded per-cell memory (forward scans bounded by the MA cap; release per-cell arrays
after summarisation; do not retain all domain frames or all bootstrap draws). Outputs (`results/`):
`per_cell_expectancy.parquet` (per cell × variant × **object**: median/mean/trimmed + CIs, tail-share,
variant−RM and variant−benchmark contrasts, n_qualifying, exclusion/censoring counts, `r`, win rate, viability +
beats-RM + beats-benchmark flags); `favourable_target_map.csv` (binding `/STRONG-STAT` summary per variant per
object + P11 non-4h tally); `secondary_map.csv` (in-progress VP-POC per object; ZigZag benchmark contrast
deferred — see Exclusions);
`reconciliation.csv` (native `M-BENCH` ↔ EXP-061 M0 / EXP-060B BENCH-MA; hybrid `H-BENCH` ↔ EXP-061 H0;
populations vs EXP-053/060/061, per object); `composition_readout.json` (per-object per-variant P11 non-4h,
wins, EVIDENCE_* fork → G-015 input); `run_metadata.json` (seed, frozen + new predeclared constants,
EXP-056/060/060B/061/063 source paths/hashes, parallelism note, holdout fence,
`disclosed_secondaries_not_computed`). Bounded plots from collected per-cell summaries (no reloads), rendered
per object. Output **byte-identical across `--workers`** counts (order-independent per-cell RNG + fixed merge
order).

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
# domain aggregation (xen.bar_aggregator, carrying TickVolume) for 5m strict / others min_coverage=0.90
```

## Suggested Direction

Fork **EXP-063's dual-object `code/run_experiment.py`** (it already builds both conditioned populations —
hybrid `H0` via `bench_signal_arm`'s `cond_mask` override and native `M0` — the shared MA in-progress geometry,
the per-object matched-random controls via `matched_random_arm`, the corrected reconciliation roles, the P4
mean/trim/tail bootstrap, and a per-variant OAT loop with per-object reporting). Changes, all bounded: **(1)**
replace EXP-063's per-variant **adverse** build with the per-variant **favourable-target** build — compose
EXP-056's `xen.favourable_targets` (volume profile + trailing-magnitude target + `barriers_from_fav`) **pointed
at MA-segment references** (prior completed MA segment for VP; trailing-W MA-segment magnitudes for MAG), holding
the adverse at benchmark 1:1 and the third barrier at the MA adaptive cap; the 8-variant favourable grid replaces
the 4-variant adverse grid. **(2)** Run each variant on **both** object populations — native
(`ma["stat"]["retained_p75"]`) and hybrid (`zz["stat"]["retained_p75"]` via `cond_mask`; verify the ZigZag mask
indexes onto the MA entry order by `CloseTime`) — and report individually with an `object` tag on every per-cell
× per-variant row. **(3)** Run `matched_random_arm` through each variant's favourable-target pipeline to produce
the per-object nulls RM-* (native) / RH-* (hybrid) — each matched to its **own** object's variant count,
excluding its **own** object's signal entries, on **fresh dedicated RNG purposes per object/variant** so no
existing stream shifts — and the per-object per-variant `variant − RM` (`contrast_ci`) and `variant − benchmark`
(`paired_median_contrast_ci`) contrasts. **(4)** Reconcile **native `M-BENCH` ↔ EXP-061 `M0` / EXP-060B
`BENCH-MA`** and **hybrid `H-BENCH` ↔ EXP-061 `H0`** exactly (per-cell median + count, `RECON_TOL = 1e-9`;
SUBSTRATE/METHOD_DEFECT if not), and reconcile populations vs EXP-053 (hybrid 3202-class) / EXP-061 (native
8360-class). **(5)** Emit **per-object** P11 (non-4h) / signal-vs-RM / lever readouts (never pooled). Keep
EXP-063's per-instrument `ProcessPoolExecutor` with native-thread pinning (`POLARS_MAX_THREADS=1` etc.) and
fixed-order reassembly (byte-identical output for any `--workers`). Fixed per-cell seed throughout (P3); `tqdm`;
bounded memory; **do not adjudicate G-015** (single gate after the full slate). The existing native/hybrid BENCH
median+mean RNG paths must stay byte-identical to EXP-061 (use new RNG purposes for the new favourable variants
and their nulls only) so the EXP-061 reconciliation holds for both objects.
