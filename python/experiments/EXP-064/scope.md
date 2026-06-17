# Experiment: EXP-064 — MA(20,50)-Substrate Favourable-Target Geometry (Hybrid Conditioned HA Harami; `/VPTARGET`, `/MAGTARGET` vs Benchmark 50%, Phase 015 Surface S1)

> **Mandatory-reading precondition (Phase 015, binding — inherited from 014-B).**
> `../../docs/experiments-docs/checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/014-A-conditioning-gap-and-validation-lessons.md`
> was read in full before this scope was written. EXP-064 is the Phase 015 **favourable-target
> geometry** surface read (S1; mirrors EXP-056) on the **MA(20,50) substrate**. The four mandatory
> rules are honoured, recorded so Stage 4 can check:
> - **(a) conditioning** — honoured. The object is the **live `/STRONG-STAT`-conditioned HA harami**,
>   **hybrid** mode: the entry population is **byte-identical to EXP-053/060** (the EXP-060B object).
>   `/STRONG-STAT` (P7, live magnitude-percentile) is binding; `/STRONG-HA` (P8) is a disclosed
>   secondary arm. Only the **favourable-target geometry** is varied (OAT); the signal, anchor, adverse
>   model, third barrier, and fills are held at the MA benchmark. The matched-random-on-MA control is a
>   deliberate **null** (binding per P5), not a signal claim.
> - **(b) harami-anchor** — honoured. Entry is the **harami confirmation-bar real close** `C`. The
>   MA(20,50) substrate supplies only the outcome geometry (`rd` / `M_sofar` / favourable-target
>   reference / adaptive cap); it does **not** move the anchor. The matched-random control intentionally
>   breaks the anchor (that is what makes it a null).
> - **(c) position-in-move descriptive-only / never a live filter** — honoured. No position-in-move
>   metric is used. The favourable-target references are **confirmed, completed** MA segments (known at
>   entry); no unconfirmed MA crossover enters any target, filter, or barrier.
> - **(d) expectancy / not first-hit `r`** — honoured. The binding endpoint is the Phase 015 **median**
>   gross per-event expectancy (P3/P14). The **mean** (raw + 10% trimmed + worst-5% tail-share, each
>   CI'd) is the P4 **diagnostic co-primary**, disclosed; first-hit `r` is disclosed for single-leg arms
>   only and never binds.
> EXP-064 does **not** treat the EXP-049 `r≈0.50` null or EXP-050 front-loading as evidence against the
> family — those measured the *unconditioned ZigZag* object.

**Phase / checkpoint:** `2026-06-17-015-ma-substrate-conditioned-harami-full-surface` (Phase 015; **G0 PASS 2026-06-17**).
**Family / candidate:** `CF-HA-HARAMI-001` (`REGISTERED`, OPEN) · Phase 015 surface **S1** ·
`CF-HA-HARAMI-001/HYP-017` — EXP-064 (Phase 015 batch, `multiplicity-registry.md` line 478). Exercises the
registered branches `CF-HA-HARAMI-001/VPTARGET` and `CF-HA-HARAMI-001/MAGTARGET` on the registered
`CF-HA-HARAMI-001/MA-SUBSTRATE` (mode `hybrid`).
**Registry precondition (satisfied):** `MA-SUBSTRATE` + modes (`hybrid`, `native`) **REGISTERED** (Phase 015
batch, 2026-06-17, G0 PASS); `/VPTARGET`, `/MAGTARGET`, the benchmark 3-barrier geometry, and the
matched-random baseline pre-exist (Phase 014 / 014-B). HYP-017/EXP-064 is the listed plan. **No new countable
item is introduced here.**
**Surface role:** Surface read 1 of the Phase 015 post-lead slate — favourable-target geometry on MA.
EXP-061 (L1) established the benchmark MA geometry is signal-attributable (EVIDENCE_FOR; M0 ≻ RM0 generalised
beyond the champion). EXP-064 asks whether **changing only the favourable target** improves the conditioned
harami's MA-substrate gross median expectancy. The surface runs **regardless** of the lead (P9 no-early-
closure); output feeds the single terminal **G-015** after the full slate. **No closure or candidate
registration here.**
**Governing design / D0:** `design.md` (§3 objective; §5 slate S1; §7 G-015 criteria) + `D0-predeclarations.md`
(P1 substrate; P2 hybrid; P3 median binding + fixed seed; P4 mean diagnostic; P5 matched-null per object;
P6 non-4h composition; P8 OAT grids reused unchanged; P9 slate; P10 power; P12 reconciliation). Inherits
014-B P14/P15/P16/P20 and the family spec `candidate-families/harami.md` (favourable-target variants).
**Reuses (no new `xen/` module expected):** the EXP-056 favourable-target machinery
(`xen.favourable_targets`: volume-profile builder, trailing-magnitude target, `barriers_from_fav`,
`paired_median_contrast_ci`) **applied on MA-segment references**; the EXP-060/060B per-cell MA pipeline
(`ma_segment_moves` / `ma_seg_arm` / matched-random selection in `python/experiments/EXP-060/code/`, reused by
EXP-060B/EXP-061); `xen.expectancy.*` (`live_in_progress_state`, `live_strong_stat`,
`adaptive_time_caps_by_epoch`, `benchmark_barriers`, `resolve_path_ordered`, `realised_returns`,
`qualifying_mask`, `bootstrap_median_distribution`, `bootstrap_mean_distribution`, `median_ci`, `contrast_ci`);
ZigZag (`xen.zigzag`, disclosed contrast), harami (`xen.ha_harami`), `/STRONG-HA`
(`xen.strong_move.annotate_ha_impulse`), confirmation indices (`xen.capture_barriers`).

## Slot & ledger accounting (binding)

- **0 candidate slots, 0 TEST reads.** Characterization/diagnostic per the Phase 015 D0 (P11). No countable
  item is introduced: `MA-SUBSTRATE` (+ modes) is registered at G0; `/VPTARGET`, `/MAGTARGET`, the benchmark
  geometry, and the matched-random null pre-exist. A slot is consumed only at a G-015 PROCEED on a future
  scope.
- **No TEST stratum is read.** All work on the **TRAIN** slice (first 70% of the first-70% analysis set; F01
  file-order prefix; identical fence to EXP-049/053–063). Population byte-identical to EXP-053/060; no new
  stratum opened; `test-read-ledger.md` requires no entry; global-holdout seal carries forward. No HA-harami
  TEST stratum has ever been read.
- All work **gross**; detection on HA candles; **all outcome metrics on real-price OHLC**; MA(20,50) computed
  on **real close** (identical to EXP-060/061 `ma_segment_moves`). No HA price enters any metric.

---

## Hypothesis

For the hybrid live `/STRONG`-conditioned HA harami on the **MA(20,50) substrate** (entered at the harami
confirmation-bar real close `C`, faded against the in-progress confirmed-MA-segment move), **at least one
alternative favourable-target geometry** — `/VPTARGET` (volume-profile levels of the prior *completed MA
segment*) or `/MAGTARGET` (trailing-MA-segment-magnitude distances) — produces **higher gross per-event median
expectancy** (P3/P14, ATR-normalised, P15 fills, real prices) than the **benchmark 50%-of-`M_sofar`
favourable target** (MA benchmark), on the binding `/STRONG-STAT` arm, with the adverse target held at the
MA benchmark 1:1 model and the third barrier at the MA-defined adaptive cap (OAT on favourable geometry), and
that winning variant is **signal-attributable** (beats its own matched-random-on-MA null, P5).

**Falsifiable:** if **no** alternative favourable-target variant simultaneously (a) is median-viable per
cell, (b) beats its matched-random-on-MA null (`variant − RM` contrast CI_low > 0), and (c) beats the
benchmark MA variant (`variant − benchmark` contrast CI_low > 0), all composed by P11 with the P6 non-4h
breadth rule, then favourable-target geometry is **not** an MA-substrate lever that improves conditioned
capture (a valid characterization result feeding G-015 — never a closure inside Phase 015; the surface runs
regardless, P9).

## Question

On the MA substrate, does changing only the **favourable target** — from the benchmark 50%-of-MA-segment
magnitude level to a volume-profile level of the prior completed MA segment (`/VPTARGET`: near VA edge / POC /
far VA edge) or a trailing-magnitude distance (`/MAGTARGET`: `{0.5,1.0} × median(trailing-{5,20} MA-segment
magnitudes)`) — improve the hybrid conditioned HA-harami's gross per-event median expectancy vs the benchmark,
per cell and composed across the 99-cell grid, beat the matched-random-on-MA null, and which variant (if any)
wins? Does the EXP-056 ZigZag-substrate result (0/8 variants beat benchmark) reproduce or differ on MA?

---

## Scope Boundaries

### Data Views

- **Real domain bars** (5m strict; 15m/30m/1h/2h/4h via `xen.bar_aggregator.aggregate_ohlc`,
  `min_coverage=0.90` — identical to EXP-049/053–063/VAL-004) for the MA(20,50)-crossover substrate
  (`ma_segment_moves` on real close), the ZigZag substrate (`atr_mult=1.0`, disclosed contrast), confirmed
  moves/segments, `/STRONG-STAT` magnitudes, the favourable-target construction (volume profile and trailing
  magnitudes on MA segments), the MA-defined adaptive cap, the benchmark/variant favourable levels, P15 fills,
  ATR normalisation, and **all** outcome metrics.
- **Heiken Ashi candles** (`xen.heiken_ashi_generator`) for **harami detection only** (frozen EXP-048
  detector). **No HA price enters any metric.**
- **`TickVolume`** (domain-bar, summed from constituent 1-minute bars by `xen.bar_aggregator`) is the only
  volume input to `/VPTARGET`. It is **broker tick count, a proxy for traded volume**; the proxy limitation is
  disclosed in every `/VPTARGET` result.

### Event population (hybrid conditioned signal — byte-identical to EXP-053/060)

- An HA harami (frozen detector) **AND** the live `/STRONG-STAT` magnitude-percentile filter on the
  **in-progress confirmed-ZigZag move's magnitude-so-far** `M_sofar^{ZZ} = |C − start_pivot|` ≥ p75 of the
  trailing-20 confirmed-ZigZag-move magnitudes (P7, binding) — **hybrid** mode: the qualifying population is
  the **EXP-053/060 ZigZag-`/STRONG-STAT` set** (binding; P2; the conditioning move is ZigZag, the *outcome
  geometry* is MA). `/STRONG-HA` (P8: run of `X=3` large-body HA bars, no opposing wick) is a disclosed
  secondary arm through the identical pipeline.
- **Trade / reversal direction** `rd` and the **MA-segment magnitude-so-far** `M_sofar` used to build every
  favourable target come from the **MA(20,50) substrate** (`ma_seg_arm`: last confirmed MA crossover → `C`),
  exactly the EXP-060/061 construction. The conditioning filter uses the ZigZag move (hybrid); the geometry
  uses the MA segment.
- Construction reuses `xen.expectancy.live_in_progress_state` + `live_strong_stat` and the EXP-060
  `ma_segment_moves`/`ma_seg_arm` — the **same functions EXP-053/060/061 used** — so the binding population is
  byte-identical to EXP-053's conditioned events (verified by population reconciliation) and the MA geometry is
  byte-identical to EXP-061's.

### Entry anchor

The **harami confirmation-bar real close** `C` (real domain-bar close at the harami timestamp), strictly before
any ZigZag/MA trend-change confirmation. Identical to EXP-053/061.

### Favourable-target variants on MA (predeclared sweep; OAT on the favourable leg only)

All variants define a **favourable price level** `fav` in the reversal direction `rd` from `C`; the favourable
distance is `fav_dist = rd·(fav − C)`. The **adverse** target is the MA benchmark 1:1 model
`adv = C − rd·fav_dist` (benchmark adverse is 1:1, so adverse distance = favourable distance for every
variant). The **third barrier** is the MA-defined adaptive cap (the `ma_seg_arm` cap; benchmark, P4-analog).
Fills are P15. **Validity rule (all variants):** an event is *valid* iff `fav_dist > 0` (target on the
reversal side of `C`) **and** the reference context is defined; events with `fav_dist ≤ 0` or an undefined
profile/reference are **excluded-with-record** (a disclosed degenerate count per cell), never silently clamped.

1. **Benchmark (reference variant, MA benchmark):** `fav_dist = 0.50 × M_sofar`; `fav = C + rd·0.50·M_sofar`,
   `M_sofar` from the MA segment (`ma_seg_arm`). This arm **is EXP-061's M0 / EXP-060B `BENCH-MA`** — the
   anchor every alternative is contrasted against and the P12 reconciliation target.

2. **`/VPTARGET` — volume profile of the prior completed MA segment (LOOKBACK=1), binding reference.** Build a
   volume profile from the domain bars constituting the **immediately preceding *completed* confirmed MA
   segment** (the last confirmed MA segment before the in-progress one, known at entry; bars from that
   segment's start crossover to its confirming crossover). Each constituent bar's `TickVolume` is distributed
   **uniformly across its `[Low, High]` range** into fixed-width price bins (bin width `= 0.10 × ATR_entry`,
   predeclared; ≥1 bin). From the profile:
   - **POC** = centre of the maximum-volume bin (**VP baseline variant**).
   - **Value area = 70%** of total profile volume, the contiguous bin run grown outward from the POC; low
     boundary `VAL`, high boundary `VAH`.
   - **near VA edge** = VA boundary with the **smaller** valid `fav_dist`; **far VA edge** = VA boundary with
     the **larger** valid `fav_dist` (among `{VAL, VAH}` with `rd·(level − C) > 0`).
   - **Insufficient-profile rule:** a prior completed MA segment with **< 3 domain bars** → no valid profile →
     event excluded-with-record (disclosed); a level on the wrong side of `C` → that *level's* variant event
     excluded-with-record.
   - Three binding `/VPTARGET` variants: **VP-POC** (baseline), **VP-near-VA**, **VP-far-VA**.

3. **`/VPTARGET` — in-progress-MA-segment POC (disclosed secondary only).** Identical construction but the
   profile is built from the **in-progress MA segment's** domain bars (segment start crossover → entry bar).
   Retained to **empirically expose** the path-dependence concern (EXP-056 operator rationale); **never
   binding**, reported as a disclosed secondary.

4. **`/MAGTARGET` — trailing-MA-segment-magnitude distance (LOOKBACK>1; predeclared grid).**
   `fav_dist = frac × median(magnitudes of the trailing W confirmed MA segments confirmed strictly before the
   harami)`, `fav = C + rd·fav_dist`, over the grid `frac ∈ {0.5, 1.0} × W ∈ {5, 20}` (4 variants:
   MAG-0.5×5, MAG-1.0×5, MAG-0.5×20, MAG-1.0×20). Magnitude estimate only — no absolute price level. Warmup:
   **fewer than `W` confirmed MA segments** before the harami → event excluded-with-record for that variant
   (disclosed). `fav_dist > 0` always holds (magnitudes positive).

**Total predeclared favourable-target variants:** 1 benchmark + 3 binding `/VPTARGET` + 4 `/MAGTARGET` =
**8 binding variants**; plus 1 disclosed-secondary in-progress VP-POC. Each variant runs on the binding
`/STRONG-STAT` arm (binding) and the `/STRONG-HA` arm (disclosed).

### Matched-random-on-MA null (RM; **binding per P5**, per variant)

For **each** favourable-target variant, a **matched-count random in-regime** control (the EXP-060B
matched-random-in-MA-regime selection, reused unchanged; same cell / direction / regime, EXP-021/027 exclusion
convention, matched-count to the cell's qualifying harami count) is run through the **identical variant
favourable-target + adverse + cap + P15 pipeline** on the MA substrate. **Signal-attribution requires the
variant beats its own RM null** (`variant − RM` median contrast CI_low > 0) — elevated from the EXP-056
disclosed-secondary status to **binding** by Phase 015 P5 (matched-random null in *every* read). The RM draws
are **independent** of the harami events (no common subset to pair); the contrast uses the independence-assuming
`xen.expectancy.contrast_ci`.

### Adverse target, third barrier, fills (MA benchmark; held fixed)

- **Adverse (MA benchmark 1:1):** `adv = C − rd·fav_dist` — distance equals the variant's favourable distance.
- **Third barrier (MA-defined adaptive cap, benchmark):** the `ma_seg_arm` adaptive cap (the EXP-060/061
  benchmark cap derived from MA-segment durations), reused unchanged for every variant. Warmup-excluded when
  the cap is undefined (insufficient confirmed MA segments), disclosed.
- **Fill model (P15, method standard):** when a single domain bar could touch more than one level, fills
  resolve in path order — bullish bar (`Close ≥ Open`): `Open → Low → High → Close`; bearish (`Close < Open`):
  `Open → High → Low → Close`. TIMECAP exits at the cap bar's real close. Reuse
  `xen.expectancy.resolve_path_ordered`. Documented approximation; disclosed.

### Parameters (all frozen / predeclared; no tuning)

MA(20,50) on real close (fixed; P1 — not swept); ZigZag Wilder ATR(14), `ATR_MULT = 1.0` (disclosed contrast);
`/STRONG-STAT` trailing-20, ≥p75 (P7); `/STRONG-HA` `X=3` (P8); benchmark favourable `X = 50%` of `M_sofar`
(MA); adverse 1:1; MA adaptive cap `(k=1.5, window=20, floor=6, statistic=median, min_moves=5)`-analog as
in EXP-060/061; ATR-normalisation divisor = Wilder ATR(14) at the harami entry bar (P14); bootstrap
`b = round(m^(1/3))`, `N_BOOT = 10_000`, **fixed per-cell seed (P3)**. **New predeclared favourable-target
parameters (this scope):** VP reference = prior completed MA segment (LOOKBACK=1); VP bin width
`= 0.10 × ATR_entry`; VP value area `= 70%`; VP insufficient-profile floor `= 3` domain bars; `/MAGTARGET`
grid `frac ∈ {0.5, 1.0} × W ∈ {5, 20}`, statistic = median (over MA-segment magnitudes). None tuned against
outcomes; sensitivity not swept beyond the predeclared grid.

### Instruments / cells / time range

The **99-cell EXP-049/053–063 member grid** (17 instruments × {5m,15m,30m,1h,2h,4h} − 3 COVERAGE_EXCLUDED:
US500-4h, JP225-2h, JP225-4h). Per-cell first, then **P11** with the **P6 non-4h rule** (≥5 cells over ≥3
instruments, with ≥3 qualifying cells outside the 4h domain) for any "winning variant" claim. **TRAIN only** =
first 70% of the first-70% analysis set (F01 file-order prefix; identical fence to EXP-049/053–063;
`train_end_ts` = last `CloseTime` of the first `int(int(total_rows*0.7)*0.7)` file-order 1-minute rows). TEST
and the final-30% **global holdout** are **not** read. Forward windows clipped to `train_end_ts`; truncated →
`DATA_CENSORED`. DE30 carries the truncated-coverage disclosure.

### Look-ahead / causality discipline (binding)

- ZigZag and MA(20,50) segmentation are future information until confirmed. The signal (harami +
  `/STRONG-STAT`), `rd`, `M_sofar`, and every favourable target use **only confirmed, completed prior
  moves/segments and the entry bar's own real close** — never an unconfirmed pivot/crossover or any future
  bar. The VP reference MA segment is confirmed at entry; its bars are all `CloseTime ≤ C`'s bar. `/MAGTARGET`
  magnitudes are from MA segments confirmed strictly before the harami. The MA adaptive cap uses only MA
  segments confirmed strictly before the harami. MA(20,50) `_sma` is trailing. Matched-random entries are
  constructed causally with the identical pre-entry-only state.
- Excursion scans read only bars `[entry_idx+1, cap]`, fenced `CloseTime ≤ train_end_ts`; a window truncated
  by the TRAIN edge before resolution is `DATA_CENSORED` (excluded, disclosed), never measured against
  truncated data.
- Ordering/alignment by `CloseTime`, never bar index across views.

### Real-price outcome discipline

Harami detected on HA candles; `M_sofar`, the volume profile (real-bar prices + `TickVolume`), trailing MA
magnitudes, ATR normalisation, fav/adv levels, fills, expectancy, `r`, win rate, and censoring all on real
domain-bar OHLC. MA(20,50) computed on **real close**. **No HA price in any metric.**

### Exclusions

- No costs (gross only).
- **Favourable-target geometry only.** No `/ADV-EXTREME`/`/ADV-NONE` (EXP-063 adverse), no `/THIRD-EVENT`/
  `/THIRD-TIME` (EXP-065), no `/EXIT-PARTIAL`/`/EXIT-TRAIL-STRUCT` (EXP-066), no combined system (EXP-067).
  No `/BARCFG`/`/CONFIRM` overlays; no position-in-move *filter*. **No MA-native conditioning** (EXP-068);
  **no MA-parameter sweep** (MA(20,50) fixed).
- No parameter tuning; **no post-result variant selection** (all 8 predeclared variants reported and
  composed); no gate adjudication (single G-015 after the full slate — EXP-064 emits a characterization
  readout only). No TEST or holdout contact; no candidate slot; no TEST read.

## Success / Failure Criteria

All **gross**, per-cell first, P11-composed with the **P6 non-4h rule** (≥5 cells over ≥3 instruments, ≥3
outside 4h). Binding endpoint = **median per-event gross expectancy** `E_cell` (ATR units, P15 fills), on the
**`/STRONG-STAT` arm**; per-cell viable iff **CI_low > 0** (regime-clustered moving-block bootstrap, one-sided
95%, fixed seed) **AND ≥ 30 qualifying events**. The **mean** (raw + 10% trimmed + worst-5% tail-share, each
CI'd) is the P4 disclosed diagnostic, never a viability gate.

- **EVIDENCE_FOR (a favourable-target lever helps on MA):** ≥1 alternative variant **(a)** is median-viable
  per cell **AND (b)** beats its matched-random-on-MA null (`variant − RM` median contrast CI_low > 0; P5
  signal-attribution) **AND (c)** beats the benchmark MA variant (`variant − benchmark` contrast CI_low > 0),
  all composed by **P11 with the non-4h breadth rule**. The winning variant(s), their RM margin, and their
  benchmark margin are the deliverable; no candidate registration (G-015 only).
- **EVIDENCE_AGAINST (favourable geometry is not an MA lever):** no alternative variant clears the combined
  (viable ∧ beats-RM ∧ beats-benchmark) P11 quorum. Recorded as a measured-negative characterization; routing
  deferred to G-015. **Family stays OPEN** — the surface (S2/S3/S4, native) runs regardless (P9).
- **INCONCLUSIVE (power-limited):** fewer than the P11 quorum of cells reach ≥30 qualifying events on the
  variants of interest (validity/warmup exclusions deplete counts), no correctness failure. Disclosed; never
  defaulted to a ratio.
- **SUBSTRATE/METHOD_DEFECT:** any reconciliation, determinism, causality, or invariant failure → fix before
  reporting. Invariant checks: (i) the **benchmark MA arm reproduces EXP-061 `M0` / EXP-060B `BENCH-MA`**
  per-cell median + qualifying count to float tolerance (`RECON_TOL = 1e-9`); (ii) population reconciliation vs
  EXP-053 exact for the conditioned `/STRONG-STAT` population; (iii) **matched-count holds** — each variant's
  RM qualifying-draw count equals its cell's variant signal-arm count; (iv) the 1:1 adverse stop, when it
  binds, closes the position at the same bar/level; (v) every exit price is a real-bar P15 fill with
  `CloseTime ≤ train_end_ts`; (vi) `fav_dist > 0` for every counted event (validity rule).

Deliverable label: **MA_FAVOURABLE_TARGET_CHARACTERISED**, carrying the per-cell + P11 (non-4h) readout for
every variant, the EVIDENCE_* classification, the variant−RM and variant−benchmark contrasts, both filter
arms, the disclosed mean/trim/tail diagnostic, the disclosed in-progress VP-POC, the disclosed ZigZag-substrate
benchmark contrast (reconciling to EXP-056 benchmark), first-hit `r` (single-leg arms), and all exclusion/
censoring counts. **No phase closure or candidate registration here.**

## Complexity Budget

- **Max distinct statistical methods: 4** — (1) regime-clustered moving-block bootstrap CI on a variant's
  **median** expectancy per cell (`bootstrap_median_distribution` + `median_ci`); (2) the same bootstrap on the
  per-cell **mean + 10% trimmed mean** + worst-5% tail-share (P4 diagnostic, dedicated RNG streams); (3)
  `variant − RM` independent contrast CI (`contrast_ci`; binding, P5); (4) `variant − benchmark` paired-median
  contrast CI (`xen.favourable_targets.paired_median_contrast_ci`, common qualifying-event subset). Applied
  across the predeclared 8-variant grid (a parameterised sweep, not new methods per variant) — consistent with
  EXP-056 and the Phase 015 lead.
- **Max visualisations: 5** — (i) per-variant median-expectancy forest/CI per cell vs benchmark (headline);
  (ii) variant−benchmark and variant−RM contrast heatmap (variants × cells; non-4h cells marked); (iii)
  expectancy distribution by variant (pooled); (iv) P11 (non-4h) composition / "wins" map across variants;
  (v) median-vs-mean (P4 skew preview) for the benchmark + best variant. Secondary tables to CSV.
- **Max new code modules: 1 — *expected 0*.** Reuses `xen.favourable_targets` (EXP-056) applied to MA-segment
  references and the EXP-060/061 MA pipeline; the only new code path is calling the existing matched-random
  selector through each **variant** favourable-target geometry (RM per variant) plus the trimmed-mean/tail-share
  statistic on the existing bootstrap. At most one thin orchestration wrapper under `code/`; **no new `xen/`
  analysis module**.

## Metric Denominators & Zero-Baseline

- **Per-event realised gross return** (ATR units) is defined for every **qualifying** event of a variant —
  those with a built barrier (valid `fav_dist > 0`, profile/warmup defined) whose outcome is `FAV`, `ADV`, or
  `TIMECAP`. Return = `rd·(exit_price − C)/ATR_entry` (`xen.expectancy.realised_returns`), `exit_price` the P15
  path-ordered fill (target for FAV/ADV; cap-bar real close for TIMECAP), `ATR_entry` = Wilder ATR(14) at the
  harami entry bar.
- **Per-cell endpoints:** `E_cell_median` (binding, P3/P14) and `E_cell_mean` + 10% trimmed mean (P4
  diagnostic), each over the variant's qualifying-event population, each with its own fixed-seed bootstrap CI.
  `DATA_CENSORED`, warmup-excluded, and validity-excluded events are **excluded** from median/mean/trim and
  **disclosed as counts** per cell per variant.
- **Zero-baseline / power:** a cell with **< 30 qualifying events** for a variant is **NOT_VIABLE-by-power**
  for that variant (non-reportable), never an undefined/infinite ratio. The MA substrate qualifies a (typically
  larger) count than ZigZag; depleted cells disclosed, never defaulted. Worst-5% tail-share: a cell with 0
  negative return mass reports tail-share = 0.0 (finite), never NaN/inf.
- **First-hit `r`** = `fav/(fav+adv)` defined per variant (single-leg geometry), disclosed (EXP-049
  comparability); never binding.
- **Disclosed secondaries (never binding):** mean + 10% trimmed mean + worst-5% tail-share; first-hit `r`;
  win rate; TIMECAP/censoring fraction; the in-progress VP-POC variant; the `/STRONG-HA` arm; the disclosed
  ZigZag-substrate benchmark contrast (vs EXP-056); per-variant validity/profile-exclusion counts; `/VPTARGET`
  `TickVolume`-proxy note.

## Data Requirements

Per cell (instrument × domain), TRAIN slice only: lazy `pl.scan_parquet`; `analysis_rows = int(total*0.7)`,
`train_rows = int(analysis_rows*0.7)`; collect only the first `train_rows` file-order 1-minute rows (F01
prefix; never sort/collect the full file, never read TEST/holdout); assert chronological; `train_end_ts` =
last `CloseTime`. Aggregate each member domain (5m strict; others `min_coverage=0.90`, carrying `TickVolume`);
fence to `CloseTime ≤ train_end_ts`; generate HA candles; run ZigZag (`atr_mult=1.0`) → confirmed moves +
`confirm_indices`; run `ma_segment_moves` (MA(20,50) on real close) → confirmed MA segments + crossover
indices; detect haramis on HA candles aligned by `CloseTime`; build the hybrid live conditioned
`/STRONG-STAT`/`/STRONG-HA` population (byte-identical to EXP-053/060) and the MA `rd`/`M_sofar`; for each
qualifying harami compute every predeclared favourable target on MA references (benchmark, 3 VP-prior, 4 MAG,
+ disclosed in-progress VP-POC), set adverse 1:1 and the MA adaptive cap, resolve each under P15, compute
ATR-normalised gross returns; build the per-variant matched-random-on-MA null through the identical pipeline;
bootstrap per-cell median + mean + trimmed mean per variant per arm (fixed seed); compute `variant − RM`
(binding) and `variant − benchmark` (paired) contrasts; compose by P11 with the non-4h rule; second full pass
for determinism. `tqdm` over the 99-cell grid; bounded per-cell memory (forward scans bounded by the MA cap;
do not retain all domain frames or all bootstrap draws). Outputs (`results/`): `per_cell_expectancy.parquet`
(per cell × variant × arm: median/mean/trimmed + CIs, variant−RM and variant−benchmark contrasts, n_qualifying,
exclusion/censoring counts, `r`, win rate, viability + beats-RM + beats-benchmark flags);
`favourable_target_map.csv` (binding `/STRONG-STAT` summary per variant + P11 non-4h tally);
`secondary_map.csv` (`/STRONG-HA`, in-progress VP-POC, ZigZag benchmark contrast);
`reconciliation.csv` (benchmark MA arm ↔ EXP-061 M0 / EXP-060B BENCH-MA: median/count exact; population vs
EXP-053); `composition_readout.json` (per-variant P11 non-4h, wins, EVIDENCE_* fork → G-015 input);
`run_metadata.json` (seed, frozen + new predeclared constants, EXP-056/060/060B/061 source paths/hashes,
holdout fence). Bounded plots from collected per-cell summaries (no reloads).

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

Fork EXP-061's `code/run_experiment.py` (it already builds the hybrid population, the MA `ma_seg_arm` geometry,
the benchmark MA arm M0 + matched-random RM0, and the mean/trim/tail diagnostic). Compose with EXP-056's
`xen.favourable_targets` (volume profile + trailing-magnitude target + `barriers_from_fav`) **pointed at
MA-segment references** (prior completed MA segment for VP; trailing-W MA-segment magnitudes for MAG). For each
qualifying harami compute the 8 variant favourable levels, set `adv` 1:1 and the MA adaptive cap, resolve each
under P15 (`resolve_path_ordered`) → `realised_returns` → `qualifying_mask`; run the matched-random-on-MA
selector through **each variant** geometry (RM per variant; new dedicated RNG purpose offsets so no existing
stream shifts); bootstrap per-cell median + mean + 10% trimmed mean per variant; compute `variant − RM`
(`contrast_ci`, binding) and `variant − benchmark` (`paired_median_contrast_ci`); emit the layered per-variant
P11 (non-4h) / wins / EVIDENCE_* readout. **Reconcile the benchmark MA arm to EXP-061 M0 / EXP-060B BENCH-MA
exactly** (SUBSTRATE/METHOD_DEFECT if not). Fixed per-cell seed throughout (P3). **Do not adjudicate G-015**
(single gate after the full slate).
