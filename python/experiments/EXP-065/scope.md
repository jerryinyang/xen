# Experiment: EXP-065 — MA(20,50)-Substrate Third-Barrier Geometry (Hybrid Conditioned HA Harami; `/THIRD-TIME`, `/THIRD-EVENT` vs Benchmark Adaptive Cap, Phase 015 Surface S2)

> **Mandatory-reading precondition (Phase 015, binding — inherited from 014-B).**
> `../../docs/experiments-docs/checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/014-A-conditioning-gap-and-validation-lessons.md`
> was read in full before this scope was written. EXP-065 is the Phase 015 **third-barrier geometry**
> surface read (S2; mirrors EXP-058) on the **MA(20,50) substrate**. The four mandatory rules are
> honoured, recorded so Stage 4 can check:
> - **(a) conditioning** — honoured. The object is the **live `/STRONG-STAT`-conditioned HA harami**,
>   **hybrid** mode: entry population **byte-identical to EXP-053/060**. `/STRONG-STAT` (P7) is binding;
>   `/STRONG-HA` (P8) is a disclosed secondary. Only the **third barrier** is varied (OAT); the signal,
>   anchor, favourable target, adverse target, and fills are held at the MA benchmark. The
>   matched-random-on-MA control is a deliberate **null** (binding per P5), not a signal claim.
> - **(b) harami-anchor** — honoured. Entry is the **harami confirmation-bar real close** `C`. The
>   `/THIRD-EVENT` exit uses a forward **MA-segment confirmation** in the reversal direction (a
>   future-confirmed structural close-out of a position already entered at the harami), never as the
>   entry and never an unconfirmed crossover.
> - **(c) position-in-move descriptive-only / never a live filter** — honoured. EXP-050's position
>   metric is not used. The `/THIRD-EVENT` exit uses the next MA-segment confirmed (`ConfirmTime > entry`)
>   in direction `rd` — a quantity known forward-in-time, acted on at the confirmation bar.
> - **(d) expectancy / not first-hit `r`** — honoured. The binding endpoint is the Phase 015 **median**
>   gross per-event expectancy (P3/P14). The **mean** (raw + 10% trimmed + worst-5% tail-share, each
>   CI'd) is the P4 **diagnostic co-primary**, disclosed; first-hit `r` and the **censoring fraction**
>   are disclosed secondaries. The third barrier governs the "neither target hit" exit and the
>   qualifying denominator, so the censoring fraction is reported prominently — but never binds.
> EXP-065 does **not** treat the EXP-049 `r≈0.50` null or EXP-050 front-loading as evidence against the
> family — those measured the *unconditioned ZigZag* object.

**Phase / checkpoint:** `2026-06-17-015-ma-substrate-conditioned-harami-full-surface` (Phase 015; **G0 PASS 2026-06-17**).
**Family / candidate:** `CF-HA-HARAMI-001` (`REGISTERED`, OPEN) · Phase 015 surface **S2** ·
`CF-HA-HARAMI-001/HYP-018` — EXP-065 (Phase 015 batch, `multiplicity-registry.md` line 479). Exercises the
registered branches `CF-HA-HARAMI-001/THIRD-TIME` and `CF-HA-HARAMI-001/THIRD-EVENT` on the registered
`CF-HA-HARAMI-001/MA-SUBSTRATE` (mode `hybrid`).
**Registry precondition (satisfied):** `MA-SUBSTRATE` + modes **REGISTERED** (Phase 015 batch, 2026-06-17,
G0 PASS); `/THIRD-TIME`, `/THIRD-EVENT`, the benchmark 3-barrier geometry, and the matched-random baseline
pre-exist (Phase 014 / 014-B). HYP-018/EXP-065 is the listed plan. **No new countable item is introduced
here.**
**Surface role:** Surface read 2 of the Phase 015 post-lead slate — third-barrier geometry on MA. EXP-062
(L2) found the MA-segment lifetime reversal move **is available** (AVAILABILITY_GOOD); MA segments are longer
than ZigZag moves, so the benchmark cap may bind before the available move is captured. This experiment asks
whether **extending the holding horizon** (time or structural MA-segment event) converts that available move
into higher gross MA-substrate median expectancy, at what censoring cost, and whether any such gain is
signal-attributable (beats RM-on-MA, P5). The surface runs **regardless** of the lead (P9); output feeds the
single terminal **G-015**. **No closure or candidate registration here.**
**Governing design / D0:** `design.md` (§3 objective; §5 slate S2; §7 G-015 criteria) + `D0-predeclarations.md`
(P1 substrate; P2 hybrid; P3 median binding + fixed seed; P4 mean diagnostic; P5 matched-null per object;
P6 non-4h composition; P8 OAT grids reused unchanged; P9 slate; P10 power; P12 reconciliation). Inherits
014-B P14/P15/P16/P20 and the family spec `candidate-families/harami.md` (third-barrier variants).
**Reuses (no new `xen/` module expected):** the EXP-058 third-barrier machinery (`xen.third_barrier`:
`/THIRD-TIME` floor re-call + causal next-`rd`-confirm `/THIRD-EVENT` locator), **applied to MA segments**;
the EXP-060/060B/061 per-cell MA pipeline (`ma_segment_moves` / `ma_seg_arm` / matched-random); `xen.expectancy.*`
(`live_in_progress_state`, `live_strong_stat`, `adaptive_time_caps_by_epoch`, `benchmark_barriers`,
`resolve_path_ordered`, `realised_returns`, `qualifying_mask`, `bootstrap_median_distribution`,
`bootstrap_mean_distribution`, `median_ci`, `contrast_ci`); `xen.favourable_targets.paired_median_contrast_ci`;
ZigZag (`xen.zigzag`, disclosed contrast), harami (`xen.ha_harami`), `/STRONG-HA`
(`xen.strong_move.annotate_ha_impulse`), confirmation indices (`xen.capture_barriers`).

## Slot & ledger accounting (binding)

- **0 candidate slots, 0 TEST reads.** Characterization/diagnostic per the Phase 015 D0 (P11). No countable
  item is introduced. A slot is consumed only at a G-015 PROCEED on a future scope.
- **No TEST stratum is read.** All work on the **TRAIN** slice (first 70% of the first-70% analysis set; F01
  file-order prefix; identical fence to EXP-049/053–064). Population byte-identical to EXP-053/060; no new
  stratum opened; `test-read-ledger.md` requires no entry; global-holdout seal carries forward. **Note on the
  `/THIRD-EVENT` backstop and longer `/THIRD-TIME` caps:** forward excursion/exit scans run only within the
  TRAIN slice and are clipped to the TRAIN data edge — a window extending past `train_end_ts` is
  `DATA_CENSORED`, never resolved against TEST/holdout rows.
- All work **gross**; detection on HA candles; **all outcome metrics on real-price OHLC**; MA(20,50) on **real
  close**. No HA price enters any metric.

---

## Hypothesis

For the hybrid live `/STRONG`-conditioned HA harami on the **MA(20,50) substrate** (entered at the harami
confirmation-bar close, faded against the in-progress MA segment, favourable target held at the MA benchmark
50%-of-`M_sofar` level and adverse target held at the MA benchmark 1:1 level), **at least one alternative
third-barrier geometry** (`/THIRD-TIME` floor ∈ {12, 24, 48}; `/THIRD-EVENT` next-MA-segment-`rd`-confirm with
8× backstop) produces **higher gross per-event median expectancy** (P3/P14, ATR-normalised, P15 fills, real
prices) than the **benchmark MA adaptive cap** (floor=6), on the binding `/STRONG-STAT` arm, with the
favourable and adverse targets held at the MA benchmark (OAT on the third barrier), and that winning variant is
**signal-attributable** (beats its own matched-random-on-MA null, P5).

**Falsifiable:** if **no** alternative third-barrier variant simultaneously (a) is median-viable per cell,
(b) beats its matched-random-on-MA null (`variant − RM` contrast CI_low > 0), and (c) beats the benchmark MA
variant (`variant − benchmark` paired contrast CI_low > 0), all composed by P11 with the P6 non-4h breadth
rule, then third-barrier geometry is **not** an MA-substrate lever that improves conditioned capture (a valid
characterization result feeding G-015 — never a closure inside Phase 015; the surface runs regardless, P9).

## Question

On the MA substrate, does changing only the **third barrier** — from the benchmark floor-6 MA adaptive cap to
a longer-floor adaptive cap (`/THIRD-TIME` floor ∈ {12, 24, 48}) or to a structural MA-segment event cap
(`/THIRD-EVENT`: hold until the MA substrate confirms a reversal-direction segment, backstopped at 8× the
benchmark cap) — improve the hybrid conditioned HA-harami's gross per-event median expectancy vs the benchmark,
per cell and composed across the grid, beat the matched-random-on-MA null, and which variant (if any) wins? At
what cost in **censoring** (the fraction of events whose longer window is truncated by the data edge) and in
**TIMECAP/event-exit composition** (disclosed secondaries)? Does the EXP-058 ZigZag-substrate result (no
variant cleared P11) reproduce or differ on MA, where segments are longer?

---

## Scope Boundaries

### Data Views

- **Real domain bars** (5m strict; 15m/30m/1h/2h/4h via `xen.bar_aggregator.aggregate_ohlc`,
  `min_coverage=0.90`) for the MA(20,50)-crossover substrate (`ma_segment_moves`), the ZigZag substrate
  (`atr_mult=1.0`, disclosed contrast), confirmed moves/segments, `/STRONG-STAT` magnitudes, the third-barrier
  caps (time and MA-segment event), benchmark fav/adv levels, P15 fills, ATR normalisation, and **all** outcome
  metrics.
- **Heiken Ashi candles** for **harami detection only** (frozen EXP-048 detector). **No HA price enters any
  metric.**

### Event population (hybrid conditioned signal — byte-identical to EXP-053/060)

- An HA harami (frozen detector) **AND** the live `/STRONG-STAT` magnitude-percentile filter on the in-progress
  confirmed-**ZigZag** move's magnitude-so-far ≥ p75 of the trailing-20 confirmed-ZigZag magnitudes (P7,
  binding; **hybrid** — conditioning move is ZigZag, outcome geometry is MA). `/STRONG-HA` (P8, `X=3`) is a
  disclosed secondary arm.
- **Trade / reversal direction** `rd` and `M_sofar` for the benchmark fav/adv levels come from the **MA(20,50)
  substrate** (`ma_seg_arm`), exactly the EXP-060/061 construction.
- Construction reuses `xen.expectancy.live_in_progress_state` + `live_strong_stat` and the EXP-060
  `ma_segment_moves`/`ma_seg_arm` — the population is byte-identical to EXP-053's conditioned events (verified
  by reconciliation) and the MA geometry is byte-identical to EXP-061's.

### Entry anchor

The **harami confirmation-bar real close** `C`, strictly before any ZigZag/MA trend-change confirmation.
Identical to EXP-053/061.

### Third-barrier variants on MA (predeclared sweep; OAT on the third barrier only)

For every variant the **favourable** target is the MA benchmark `fav = C + rd·0.50·M_sofar` and the **adverse**
target is the MA benchmark 1:1 `adv = C − rd·0.50·M_sofar` (`M_sofar` from the MA segment). Variants differ
only in the **third barrier**, expressed as the per-event window length `n_event` (real domain bars after
entry) fed to the P15 resolver. Fills are P15. The qualifying denominator is FAV/ADV/TIMECAP with a finite exit
and finite positive `ATR_entry`; `DATA_CENSORED` (window truncated by the TRAIN edge before resolution) is
excluded-with-record (disclosed as the censoring fraction), never measured against truncated data.

1. **Benchmark (reference variant, floor=6):** the MA-defined adaptive cap (the `ma_seg_arm` benchmark cap,
   `N = max(6, round(1.5 × median(trailing-20 confirmed-MA-segment durations)))`, knobs `window=20`, `k=1.5`,
   `min_moves=5`). This arm **is EXP-061's M0 / EXP-060B `BENCH-MA`** — the anchor every alternative is
   contrasted against and the P12 reconciliation target.

2. **`/THIRD-TIME-T12` (floor=12):** `N = max(12, round(1.5 × median(MA-segment durations)))` —
   `adaptive_time_caps_by_epoch` re-called with `floor=12` on the MA-segment durations, all other knobs at
   benchmark.

3. **`/THIRD-TIME-T24` (floor=24):** `N = max(24, round(1.5 × median(MA-segment durations)))` (`floor=24`).

4. **`/THIRD-TIME-T48` (floor=48):** `N = max(48, round(1.5 × median(MA-segment durations)))` (`floor=48`).

5. **`/THIRD-EVENT` (MA-segment `rd`-confirm, 8× backstop):** the effective per-event cap is
   `n_event_evt = min(bars_to_next_rd_ma_confirm, 8 × bench_N)`, where:
   - `bars_to_next_rd_ma_confirm` = (confirm index of the **smallest**-index confirmed MA segment with
     `Direction == rd` and `ConfirmTime > entry_epoch`) − `entry_idx` (the next confirmed reversal-direction
     **MA segment** strictly after entry — the analogous structural event to EXP-058's ZigZag `/THIRD-EVENT`,
     on the MA substrate, per the EXP-058 MA-seg-baseline convention); if none exists within the data, this
     term is `+∞` (the backstop binds).
   - `bench_N` = the BENCH (floor=6) MA adaptive cap for that entry; `8 × bench_N` is the backstop.
   - Resolved through the **unchanged** `resolve_path_ordered`: a scan of `[entry+1, entry+n_event_evt]`
     returning FAV/ADV if a target is hit first, else `TIMECAP` exiting at `close[entry+n_event_evt]` (the
     `rd`-confirm MA-segment bar's real close when the event bound, or the backstop bar's real close), else
     `DATA_CENSORED` if the window is truncated by the TRAIN edge before resolution.
   - **Warmup/availability:** an entry that is benchmark-warmup-excluded (`bench_N` undefined: insufficient
     confirmed MA segments) has no defined backstop and is **excluded-with-record** for `/THIRD-EVENT`.
     `n_event_evt ≥ 1` by construction (`bench_N ≥ 6`).
   - **Disclosed split:** the fraction of TIMECAP exits bounding on the **actual `rd` MA-segment event** vs the
     **backstop** is reported per cell.

**Total predeclared third-barrier variants:** 1 benchmark + 3 `/THIRD-TIME` (T12, T24, T48) + 1 `/THIRD-EVENT`
= **5 binding variants**. Each variant runs on the binding `/STRONG-STAT` arm and the `/STRONG-HA` arm
(disclosed), each with its matched-random-on-MA null (binding, P5).

### Matched-random-on-MA null (RM; **binding per P5**, per variant)

For **each** third-barrier variant, the EXP-060B matched-random-in-MA-regime selection (reused unchanged;
matched-count to the cell's qualifying harami count, same cell/direction/regime) is run through the
**identical variant third-barrier + benchmark fav/adv + P15 pipeline** on MA. **Signal-attribution requires
the variant beats its own RM null** (`variant − RM` median contrast CI_low > 0; independence-assuming
`contrast_ci`) — elevated from the EXP-058 disclosed-secondary status to **binding** by Phase 015 P5.

### Favourable target, adverse target, fills (MA benchmark; held fixed)

- **Favourable (MA benchmark 50%):** `fav = C + rd·0.50·M_sofar` for every variant.
- **Adverse (MA benchmark 1:1):** `adv = C − rd·0.50·M_sofar` for every variant.
- **Fill model (P15, method standard):** bullish bar (`Close ≥ Open`): `O→L→H→C`; bearish: `O→H→L→C`. TIMECAP
  exits at the cap/event bar's real close; `DATA_CENSORED` carries no exit price and is excluded. Reuse
  `xen.expectancy.resolve_path_ordered`. Documented approximation; disclosed.

### Parameters (all frozen / predeclared; no tuning)

MA(20,50) on real close (fixed; P1); ZigZag Wilder ATR(14), `ATR_MULT=1.0` (disclosed contrast);
`/STRONG-STAT` trailing-20, ≥p75 (P7); `/STRONG-HA` `X=3` (P8); benchmark favourable `X = 50%` of MA `M_sofar`;
benchmark adverse 1:1; benchmark MA adaptive cap `(k=1.5, window=20, floor=6, statistic=median, min_moves=5)`;
ATR-normalisation = Wilder ATR(14) at the harami entry bar (P14); bootstrap `b = round(m^(1/3))`,
`N_BOOT = 10_000`, **fixed per-cell seed (P3)**. **New predeclared third-barrier parameters (this scope):**
`/THIRD-TIME` floors `{6 (BENCH), 12, 24, 48}` with `k=1.5`/`window=20`/`min_moves=5` held at benchmark (on
MA-segment durations); `/THIRD-EVENT` opposing-event = next confirmed MA segment with `Direction == rd` and
`ConfirmTime > entry`; `/THIRD-EVENT` backstop multiple `= 8 × bench_N`. None tuned against outcomes.

### Instruments / cells / time range

The **99-cell EXP-049/053–064 member grid** (17 instruments × {5m,15m,30m,1h,2h,4h} − 3 COVERAGE_EXCLUDED).
Per-cell first, then **P11** with the **P6 non-4h rule** (≥5 cells over ≥3 instruments, ≥3 outside 4h).
**TRAIN only** = first 70% of the first-70% analysis set (F01 file-order prefix; identical fence to
EXP-049/053–064). TEST and the final-30% **global holdout** are **not** read. Longer-horizon and event windows
clipped to `train_end_ts`; unresolved truncated windows `DATA_CENSORED` (disclosed). DE30 carries the
truncated-coverage disclosure.

### Look-ahead / causality discipline (binding)

- ZigZag and MA(20,50) segmentation are future information until confirmed. The signal (harami +
  `/STRONG-STAT`), `rd`, `M_sofar`, the favourable/adverse targets, and all `/THIRD-TIME` caps use **only**
  confirmed, completed prior moves/segments and **real bars at or before the entry bar** for construction at
  entry. The `/THIRD-TIME` caps depend only on durations of MA segments confirmed **strictly before** entry.
- The `/THIRD-EVENT` exit is a **forward** event: it uses the next MA segment confirmed with
  `ConfirmTime > entry` (known going forward in real time, exactly as the benchmark TIMECAP resolves at a
  forward bar) and exits at that confirmation bar's real close — never at the retroactively-located crossover,
  never an unconfirmed crossover. Causal (the exit decision is taken at the confirmation bar).
- Excursion/exit scans read only bars `[entry_idx+1, min(entry_idx+n_event, last_train_idx)]`, fenced
  `CloseTime ≤ train_end_ts`; a window truncated before resolution is `DATA_CENSORED`. Matched-random entries
  constructed causally with the identical pre-entry-only state.
- Ordering/alignment by `CloseTime`, never bar index across views.

### Real-price outcome discipline

Harami detected on HA candles; `M_sofar`, ATR normalisation, fav/adv levels, all third-barrier caps, fills,
expectancy, `r`, win rate, and censoring all on real domain-bar OHLC. MA(20,50) on **real close**. **No HA
price in any metric.**

### Exclusions

- No costs (gross only).
- **Third-barrier geometry only.** No `/VPTARGET`/`/MAGTARGET` (EXP-064 — favourable held at MA benchmark
  50%), no `/ADV-EXTREME`/`/ADV-NONE` (EXP-063 — adverse held at MA benchmark 1:1), no `/EXIT-PARTIAL`/
  `/EXIT-TRAIL-STRUCT` (EXP-066), no combined system (EXP-067). No `/BARCFG`/`/CONFIRM` overlays; no
  position-in-move *filter*. **No MA-native conditioning** (EXP-068); **no MA-parameter sweep**.
- No parameter tuning; **no post-result variant selection** (all 5 predeclared variants reported); no gate
  adjudication (single G-015 after the full slate). No TEST or holdout contact; no candidate slot; no TEST
  read.

## Success / Failure Criteria

All **gross**, per-cell first, P11-composed with the **P6 non-4h rule**. Binding endpoint = **median per-event
gross expectancy** `E_cell` (ATR units, P15 fills), on the **`/STRONG-STAT` arm**; per-cell viable iff
**CI_low > 0** (regime-clustered moving-block bootstrap, one-sided 95%, fixed seed) **AND ≥ 30 qualifying
events**. The **mean** (raw + 10% trimmed + worst-5% tail-share, each CI'd) is the P4 disclosed diagnostic.

- **EVIDENCE_FOR (a third-barrier lever helps on MA):** ≥1 alternative variant **(a)** is median-viable per
  cell **AND (b)** beats its matched-random-on-MA null (P5) **AND (c)** beats the benchmark MA variant (paired
  contrast CI_low > 0), all composed by **P11 with the non-4h breadth rule**. The winning variant(s), their RM
  margin, and their benchmark margin are the deliverable; no candidate registration (G-015 only).
- **EVIDENCE_AGAINST (third-barrier geometry is not an MA lever):** no alternative variant clears the combined
  (viable ∧ beats-RM ∧ beats-benchmark) P11 quorum. Recorded as a measured-negative characterization; routing
  deferred to G-015. **Family stays OPEN** — the surface runs regardless (P9).
- **INCONCLUSIVE (power-limited):** fewer than the P11 quorum reach ≥30 qualifying events on the variants of
  interest (censoring/warmup exclusions deplete counts — the expected failure mode of the longest horizons), no
  correctness failure. Disclosed; never defaulted.
- **SUBSTRATE/METHOD_DEFECT:** any reconciliation, determinism, causality, or invariant failure → fix before
  reporting. Invariant checks: (i) the **benchmark variant reproduces EXP-061 `M0` / EXP-060B `BENCH-MA`**
  per-cell median + count to `RECON_TOL = 1e-9`; (ii) `/THIRD-TIME` per-event cap is **monotone non-decreasing
  in floor** event-wise (`N_BENCH ≤ N_T12 ≤ N_T24 ≤ N_T48`); (iii) `/THIRD-EVENT` per-event cap satisfies
  `1 ≤ n_event_evt ≤ 8 × bench_N` and any bound `rd` MA-segment confirm has `ConfirmTime > entry`; (iv)
  population reconciliation vs EXP-053 exact; (v) **matched-count holds** — each variant's RM count equals its
  cell's variant signal-arm count; (vi) every exit price is a real-bar P15 fill with
  `CloseTime ≤ train_end_ts`.

Deliverable label: **MA_THIRD_BARRIER_CHARACTERISED**, carrying the per-cell + P11 (non-4h) readout for every
variant, the EVIDENCE_* classification, the variant−RM and variant−benchmark contrasts, both filter arms, the
disclosed mean/trim/tail diagnostic, per-variant **censoring fraction** (the binding trade-off of horizon
extension), the `/THIRD-EVENT` event-vs-backstop split, first-hit `r`, win rate, the disclosed ZigZag-substrate
benchmark contrast (vs EXP-058 benchmark), and all warmup/exclusion counts. **No phase closure or candidate
registration here.**

## Complexity Budget

- **Max distinct statistical methods: 4** — (1) regime-clustered moving-block bootstrap CI on a variant's
  **median** per cell; (2) the same bootstrap on the per-cell **mean + 10% trimmed mean** + worst-5% tail-share
  (P4 diagnostic); (3) `variant − RM` independent contrast CI (`contrast_ci`; binding, P5); (4) `variant −
  benchmark` paired-median contrast CI (`xen.favourable_targets.paired_median_contrast_ci`, common
  qualifying-event subset). Applied across the predeclared 5-variant set — a parameterised sweep, not new
  methods per variant.
- **Max visualisations: 5** — (i) per-variant median-expectancy forest/CI per cell vs benchmark; (ii) variant−
  benchmark and variant−RM contrast heatmap (variants × cells; non-4h marked); (iii) expectancy distribution by
  variant (pooled); (iv) P11 (non-4h) composition / "wins" map; (v) **censoring + TIMECAP composition by
  variant** (the horizon-vs-power trade-off) alongside per-cell qualifying-event counts and the median-vs-mean
  P4 preview. Secondary tables to CSV.
- **Max new code modules: 1 — *expected 0*.** Reuses `xen.third_barrier` (EXP-058) with the next-`rd`-confirm
  locator pointed at **MA segments** (the EXP-058 MA-seg-baseline path already implements this) and the
  EXP-060/061 MA pipeline; `/THIRD-TIME` caps via re-calling `adaptive_time_caps_by_epoch(floor=F)` on
  MA-segment durations; the only new code is the per-variant matched-random-on-MA call (RM) plus the
  trimmed-mean/tail-share statistic. At most one thin orchestration wrapper under `code/`; **no new `xen/`
  analysis module**.

## Metric Denominators & Zero-Baseline

- **Per-event realised gross return** (ATR units) defined for every **qualifying** event of a variant —
  built-window outcome `FAV`, `ADV`, or `TIMECAP`. Return = `rd·(exit_price − C)/ATR_entry` (`realised_returns`),
  `exit_price` the P15 fill (target for FAV/ADV; cap/event-bar real close for TIMECAP), `ATR_entry` = Wilder
  ATR(14) at the harami entry bar.
- **Per-cell endpoints:** `E_cell_median` (binding, P3/P14) and `E_cell_mean` + 10% trimmed mean (P4
  diagnostic), each with its own fixed-seed bootstrap CI. `DATA_CENSORED` and warmup-excluded events are
  **excluded** from median/mean/trim and **disclosed as counts** per cell per variant. The censoring fraction
  (`DATA_CENSORED` / built window) is a prominently disclosed secondary because it grows with horizon — the cost
  side of the lever.
- **Zero-baseline / power:** a cell with **< 30 qualifying events** for a variant is **NOT_VIABLE-by-power**
  for that variant (non-reportable), never an undefined/infinite ratio. Longer horizons (T48, `/THIRD-EVENT`
  backstop) are expected to deplete the most — depleted cells disclosed, never defaulted. Worst-5% tail-share:
  0 negative mass → tail-share = 0.0 (finite).
- **First-hit `r`** = `n_FAV/(n_FAV+n_ADV)` (TIMECAP excluded, EXP-049 convention), disclosed per variant.
  Because fav/adv geometry is held at MA benchmark (1:1), `r` is expected to stay near 0.50; the lever moves
  expectancy through the **TIMECAP exit price** and the **FAV-vs-TIMECAP composition**, not `r`. Never binding.
- **Disclosed secondaries (never binding):** per-variant censoring fraction; first-hit `r`; mean + 10% trimmed
  mean + worst-5% tail-share; win rate; TIMECAP fraction; `/THIRD-EVENT` event-vs-backstop split; per-variant
  warmup-exclusion counts; the `/STRONG-HA` arm; the disclosed ZigZag-substrate benchmark contrast.

## Data Requirements

Per cell (instrument × domain), TRAIN slice only: lazy `pl.scan_parquet`; `analysis_rows = int(total*0.7)`,
`train_rows = int(analysis_rows*0.7)`; collect only the first `train_rows` file-order 1-minute rows (F01
prefix; never sort/collect the full file, never read TEST/holdout); assert chronological; `train_end_ts` =
last `CloseTime`. Aggregate each member domain (5m strict; others `min_coverage=0.90`); fence to
`CloseTime ≤ train_end_ts`; generate HA candles; run ZigZag (`atr_mult=1.0`) → confirmed moves +
`confirm_indices`; run `ma_segment_moves` (MA(20,50) on real close) → confirmed MA segments + crossover
indices; detect haramis on HA candles aligned by `CloseTime`; build the hybrid live conditioned
`/STRONG-STAT`/`/STRONG-HA` population (byte-identical to EXP-053/060) and the MA `rd`/`M_sofar`; compute the MA
benchmark fav + adv levels (`benchmark_barriers` on MA references), then each predeclared third-barrier
variant's per-event `n_event` — BENCH/T12/T24/T48 via `adaptive_time_caps_by_epoch(floor=F)` on MA-segment
durations, `/THIRD-EVENT` via the next-`rd` MA-segment-confirm locator + 8× backstop — resolve each variant
under P15 (`resolve_path_ordered`), compute ATR-normalised gross returns; build the per-variant
matched-random-on-MA null through the identical pipeline; bootstrap per-cell median + mean + trimmed mean per
variant per arm (fixed seed); compute `variant − RM` (binding) and `variant − benchmark` (paired) contrasts;
compose by P11 with the non-4h rule; second full pass for determinism. `tqdm` over the 99-cell grid; bounded
per-cell memory. Outputs (`results/`): `per_cell_expectancy.parquet` (per cell × variant × arm: median/mean/
trimmed + CIs, variant−RM and variant−benchmark contrasts, n_qualifying, censoring/warmup counts, TIMECAP
fraction, `/THIRD-EVENT` event-vs-backstop split, `r`, win rate, viability + beats-RM + beats-benchmark flags);
`third_barrier_map.csv` (binding `/STRONG-STAT` summary per variant + P11 non-4h tally); `secondary_map.csv`
(`/STRONG-HA`, ZigZag benchmark contrast, `r`, censoring); `reconciliation.csv` (benchmark MA arm ↔ EXP-061
M0 / EXP-060B BENCH-MA: median/count exact; population vs EXP-053); `composition_readout.json` (per-variant
P11 non-4h, wins, EVIDENCE_* fork → G-015 input); `run_metadata.json` (seed, frozen + new predeclared
constants, EXP-058/060/060B/061 source paths/hashes, holdout fence). Bounded plots from collected per-cell
summaries (no reloads).

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

Fork EXP-061's `code/run_experiment.py` (hybrid population, MA `ma_seg_arm` benchmark geometry, matched-random
selector, mean/trim/tail diagnostic) and compose with EXP-058's `xen.third_barrier` next-`rd`-confirm locator
pointed at **MA segments** (the EXP-058 MA-seg baseline already implements the MA-segment event path).
`/THIRD-TIME` floors via `adaptive_time_caps_by_epoch(floor=F)` on MA-segment durations; `/THIRD-EVENT` via the
MA-segment next-`rd`-confirm + 8× backstop. Resolve each variant under P15; run the matched-random-on-MA
selector through **each variant** third barrier (RM per variant; new dedicated RNG purpose offsets); bootstrap
per-cell median + mean + 10% trimmed mean; compute `variant − RM` (`contrast_ci`, binding) and `variant −
benchmark` (`paired_median_contrast_ci`); emit the layered per-variant P11 (non-4h) / wins / EVIDENCE_* readout
plus the binding censoring disclosure. **Reconcile the benchmark MA arm to EXP-061 M0 / EXP-060B BENCH-MA
exactly** (SUBSTRATE/METHOD_DEFECT if not). Fixed per-cell seed throughout (P3). **Do not adjudicate G-015**
(single gate after the full slate).
