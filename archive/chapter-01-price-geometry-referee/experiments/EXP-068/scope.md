# Experiment: EXP-068 — MA(20,50)-Substrate Native Combined Champion (Conditioned HA Harami; Best Per-Layer Native Geometry vs RM-Native; Hybrid Disclosed; Phase 015 S4/Native)

> **New scope under `D0-amendment-001-dual-parallel-substrate.md` (2026-06-17).** Amendment 001
> elevated the MA-native conditioning object to a parallel first-class substrate and corrected the
> Phase 015 slate: EXP-068 becomes the **native combined champion** (merges the old N1+N2 planned
> experiments), mirroring EXP-060 (the ZigZag combined champion) but for the native object on the
> MA(20,50) substrate. The prior planned scope for this slot (before the amendment) is superseded in
> full; no results existed to preserve. EXP-067 carries the analogous **hybrid** combined champion.
> EXP-069 is **DROPPED** (Amendment 001; retained in the ledger, never deleted).

> **Mandatory-reading precondition (Phase 015, binding — inherited from 014-B).**
> `../../docs/experiments-docs/checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/014-A-conditioning-gap-and-validation-lessons.md`
> was read in full before this scope was written. EXP-068 is the Phase 015 **native combined
> champion** integrative surface read (S4/native; mirrors EXP-060) on the **MA(20,50) substrate**,
> primary object **native only** (hybrid disclosed from surface reads). The four mandatory rules are
> honoured, recorded so Stage 4 can check:
> - **(a) conditioning** — honoured, **and fully disambiguated** (Amendment 001). The **native**
>   object is the sole binding-measurement object here: haramis conditioned by `/STRONG-STAT` on
>   the in-progress confirmed **MA segment** (magnitude-so-far ≥ p75 of trailing-20 confirmed MA
>   segments; causal; 8360-class). This is the object that expressed the 85/99 edge in EXP-060B,
>   the object that was signal-attributable at benchmark in EXP-061 (8 cells/6 instruments), and the
>   object for which PARTIAL-V2A was EVIDENCE_FOR (21 cells/13 instruments) in EXP-066. The
>   **hybrid** object (ZigZag-`/STRONG-STAT`, 3202-class) is **disclosed** from the completed
>   dual-object surface reads (EXP-061–066) — EVIDENCE_AGAINST at all layers — but is **not** a
>   binding measurement object in EXP-068 (that role belongs to EXP-067). `/STRONG-STAT` (P7) is
>   binding for the native object; `/STRONG-HA` (P8) is a disclosed-secondary arm (deferred). The
>   native matched-random-on-MA control is a deliberate **null** (binding per P5), not a signal
>   claim.
> - **(b) harami-anchor** — honoured. Entry is the **harami confirmation-bar real close** `C` for
>   the native object. The MA(20,50) substrate supplies the outcome geometry (`rd` / `M_sofar` /
>   favourable target / adaptive cap). The matched-random control intentionally breaks the anchor
>   (that is what makes it a null).
> - **(c) position-in-move descriptive-only / never a live filter** — honoured. EXP-050's position
>   metric is not used. Every exit trigger (fractional targets, time cap) is acted on at a bar known
>   forward-in-time after entry.
> - **(d) expectancy / not first-hit `r`** — honoured. The **binding endpoint** is the Phase 015
>   **median** gross per-event expectancy (P3/P14) of the **position-weighted realised return**
>   (multi-leg exits collapse to one per-event number). The **G-015 conjunction** further requires
>   the champion arm to be **raw-mean-positive** (CI_low > 0; P4 co-primary) simultaneously,
>   composed at P11+P6. First-hit `r` is disclosed for the single-leg BENCH arm only and never
>   binds.
> EXP-068 does **not** treat the EXP-049 `r≈0.50` null or EXP-050 front-loading as evidence against
> the family — those measured the *unconditioned ZigZag* object.

**Phase / checkpoint:** `2026-06-17-015-ma-substrate-conditioned-harami-full-surface` (Phase 015; **G0 PASS 2026-06-17**).
**Family / candidate:** `CF-HA-HARAMI-001` (`REGISTERED`, OPEN) · Phase 015 surface **S4/native** ·
`CF-HA-HARAMI-001/HYP-021` — EXP-068 (Phase 015 batch, `multiplicity-registry.md` line 492,
"native combined champion (merges old N1+N2)"). Exercises the registered
`CF-HA-HARAMI-001/MA-SUBSTRATE` in mode `native` (parallel first-class per Amendment 001), using
the pre-existing registered branches `/EXIT-PARTIAL` (P17) and `/ADV-NONE` (disclosed unbounded
reference) alongside the benchmark geometry.
**Registry precondition (satisfied):** `MA-SUBSTRATE` (mode `native`, parallel first-class per
`D0-amendment-001`) **REGISTERED** (Phase 015 batch, 2026-06-17, G0 PASS); `/EXIT-PARTIAL` (V2A
variant), the benchmark geometry (`/BENCH-MA`), `/ADV-NONE` (disclosed reference), and the
matched-random baseline pre-exist (Phase 014/014-B; EXP-060B; EXP-066). HYP-021/EXP-068 is the
listed plan. **No new countable item is introduced here.**
**Surface role:** Integrative terminal read S4/native of the Phase 015 slate — native combined
champion on MA, feeding G-015. The per-layer surface reads (EXP-061 L1 through EXP-066 S3) have
characterised each geometric lever on **both** conditioning objects individually. EXP-068 now
assembles the **native per-layer winners** into champion arm combinations and tests them under the
**G-015 conjunction** (median-viable AND raw-mean-positive AND beats RM-native at P11+P6). No
closure or candidate registration here; those are G-015 outcomes only. The surface runs regardless
of any individual-layer result (P9).
**Governing design / D0:** `design.md` (§3 objective; §5 slate S4/native; §7 G-015 criteria) +
`D0-predeclarations.md` (P1 substrate; P2 native primary/hybrid disclosed; P3 median binding + fixed
seed; **P4 mean co-primary in G-015 conjunction**; **P5 matched-null per object every read**; P6
non-4h composition; P9 slate; **P12 reconciliation roles — native `N-BENCH`↔EXP-061 `M0`/EXP-060B
1e-9; native `N-PARTIAL-V2A`↔EXP-066 `M-PARTIAL-V2A` 1e-9**) + `D0-amendment-001-dual-parallel-substrate.md`.
Inherits 014-B P14/P15/P17/P18/P20 and the family spec `candidate-families/harami.md`.
**Reuses (no new `xen/` module expected):** **EXP-066's native-side pipeline** (dual-object
`code/run_experiment.py`, already running the native population through the 12-arm position-management
exit grid with per-arm RM-native nulls, per-cell median + P4 mean/trim/tail bootstrap, P11 (non-4h)
composition, and the full P12 reconciliation logic). EXP-068 reduces this to the **3 predeclared
champion arms** on the native object, adds the **N-V2A×ADV-NONE** arm (PARTIAL-V2A + no adverse
stop — the new combination not in EXP-066), and applies the extended G-015 viability conjunction
(median AND mean both CI_low > 0 simultaneously, per cell, at P11+P6).

---

## Per-layer native champion assembly (Phase 015 surface synthesis)

The following per-layer surface results determine the native champion arms tested in EXP-068. All
results are from the **TRAIN** slice; no post-result tuning.

| Layer | Experiment | Native result | Native per-layer winner |
|-------|-----------|---------------|------------------------|
| L1 — Benchmark capture | EXP-061 | EVIDENCE_FOR: benchmark geometry M0 signal-attributable (8 cells/6 instr, 8 non-4h; reconciles EXP-060B 99/99 @1e-9) | **N-BENCH**: benchmark 50% fav / 1:1 adv / MA cap — baseline confirmed |
| L2 — MFE/MAE availability | EXP-062 | AVAILABILITY_GOOD: 91/99 MOVE_AVAILABLE; room abundant (generic MA-segment property, not harami-specific) | Confirms favourable capture has room; sizing consistent with benchmark geometry |
| L3 — Adverse geometry | EXP-063 | EVIDENCE_FOR (nuanced): V-BENCH (1:1) generalises (8 cells/6 instr); mean_viable composes (10 cells); **recovery_positive=0** (ADV-NONE contrast never crosses zero) | **V-BENCH 1:1** = adverse winner (bounded-downside); ADV-NONE disclosed as the unbounded reference whose combination with PARTIAL exits is not yet computed |
| S1 — Favourable target | EXP-064 | EVIDENCE_AGAINST: no variant beats both benchmark and RM at P11 for native (MAG-0.5×20 beats RM in 8 cells but beats benchmark in only 3) | **Benchmark 50% fav** stays (no alternative lever) |
| S2 — Third barrier | EXP-065 | EVIDENCE_AGAINST: no alternative composes at P11 for native; MA benchmark cap wins | **MA benchmark adaptive cap** stays (no alternative lever) |
| S3 — Position-management exits | EXP-066 | EVIDENCE_FOR: native **PARTIAL-V2A** (21 cells/13 instr/21 non-4h; also mean-positive 11 cells/6 instr/7 non-4h) | **PARTIAL-V2A** = exit winner (legs at {1/3, 2/3, 1} × fav_dist; benchmark 1:1 adverse) |

**Champion arm derivation:**
- S1 and S2 found no improvement → favourable target and third barrier held at benchmark.
- L3 found V-BENCH 1:1 adversely (bounded-downside); but `recovery_positive=0` across all cells means bounded-downside adverse does not recover the mean.
- S3 winner (PARTIAL-V2A) was tested in EXP-066 with **benchmark 1:1 adverse** → already measured; reproduces as `N-PARTIAL-V2A` by P12.
- EXP-060B champion (85/99 native on ZigZag) used **ADV-NONE** (no adverse stop) with single-leg benchmark exits. **PARTIAL-V2A + ADV-NONE** on native MA has **never been computed** — EXP-066 held adverse at 1:1 for all PARTIAL arms, and EXP-063 tested ADV-NONE with single-leg benchmark exits only. This combination (`N-V2A×ADV-NONE`) is the critical missing integrative test and the direct analog of the EXP-060B champion exit geometry with partial scaling.

**EXP-068 therefore tests three champion arms against RM-native under the G-015 conjunction:**

| # | Arm | Arm id | Favourable side | Adverse side | Third barrier | Notes |
|---|-----|--------|-----------------|--------------|---------------|-------|
| 1 | BENCH | `N-BENCH` | 50% fav (1 leg, `w=1`) | 1:1 stop | MA adaptive cap | P12: reproduces EXP-061 `M0` / EXP-060B `BENCH-MA` to 1e-9 |
| 2 | PARTIAL-V2A | `N-PARTIAL-V2A` | legs at {1/3, 2/3, 1}×`fav_dist` (`w=1/3` each) | 1:1 stop | MA adaptive cap | S3 native winner; P12: reproduces EXP-066 `M-PARTIAL-V2A` per-cell median + count to 1e-9 |
| 3 | V2A×ADV-NONE | `N-V2A×ADV-NONE` | legs at {1/3, 2/3, 1}×`fav_dist` (`w=1/3` each) | **no adverse stop** (ADV-NONE) | MA adaptive cap | ZigZag champion analog (EXP-060B V2A×ADV-NONE) with partial exits; novel on native MA — never previously computed |

**Hybrid champion (disclosed, not re-measured as binding arms in EXP-068):** the hybrid object
(ZigZag-`/STRONG-STAT`, 3202-class) was EVIDENCE_AGAINST at L1 (EXP-061: 1 cell), EVIDENCE_AGAINST
at S1/S3 (EXP-064, EXP-066), and INCONCLUSIVE at S2 (EXP-065: power-limited). The hybrid combined
champion (EXP-067, PLANNED) assembles the parallel hybrid per-layer winners; EXP-068 references
EXP-067's result as the cross-object comparison when available, or cites the surface read summaries
(EVIDENCE_AGAINST dominant) as the disclosed hybrid context. The hybrid is **not a binding
measurement object in EXP-068** and is **never pooled** with the native result.

---

## Slot & ledger accounting (binding)

- **0 candidate slots, 0 TEST reads.** Characterization/diagnostic per the Phase 015 D0 (P11). No
  countable item is introduced: `MA-SUBSTRATE` (mode `native`) is registered at G0; `/EXIT-PARTIAL`
  (V2A variant), `/ADV-NONE` (disclosed reference), the benchmark geometry, and the matched-random
  null pre-exist. A slot is consumed only at a G-015 PROCEED_TO_SCREEN on a future scope — and only
  if the G-015 conjunction is satisfied here.
- **No TEST stratum is read.** All work on the **TRAIN** slice (first 70% of the first-70% analysis
  set; F01 file-order prefix; identical fence to EXP-049/053–066). Native population byte-identical
  to EXP-060B/EXP-061 `M0` (8360-class); no new stratum opened; `test-read-ledger.md` requires no
  entry; global-holdout seal carries forward. Forward scans (leg targets, time cap) run only within
  the TRAIN slice and are clipped to `train_end_ts` — a window extending past `train_end_ts` is
  `DATA_CENSORED`, never resolved against TEST/holdout rows.
- All work **gross**; detection on HA candles; **all outcome metrics on real-price OHLC**; MA(20,50)
  on **real close**. No HA price enters any metric.

---

## Hypothesis

On the `/STRONG-STAT`-conditioned HA harami, **native conditioning object** (MA-segment
`/STRONG-STAT`, 8360-class), 99-cell TRAIN grid, MA(20,50) substrate, entered at the harami
confirmation-bar real close `C` and faded against the in-progress MA segment, third barrier held at
the MA benchmark adaptive cap, favourable target at the MA benchmark 50%: **at least one of the two
predeclared champion arms** — `N-PARTIAL-V2A` (PARTIAL-V2A + 1:1 adverse, the S3 native winner) or
`N-V2A×ADV-NONE` (PARTIAL-V2A + ADV-NONE, the ZigZag champion analog) — satisfies the **G-015
conjunction** simultaneously: (a) **median-viable** per cell (CI_low > 0, ≥ 30 qualifying events),
(b) **raw-mean-positive** per cell (CI_low > 0; P4 co-primary), and (c) **signal-attributable**
(beats its same-object matched-random-on-MA null, `arm − RM-native` contrast CI_low > 0; P5), all
composed at **P11 with the P6 non-4h breadth rule** (≥ 5 qualifying cells over ≥ 3 instruments,
with ≥ 3 qualifying cells outside the 4h domain).

The two champion arms are judged **individually**, with the stronger arm's G-015 status as the
deliverable. The hybrid object result is **disclosed** from EXP-061–066 / EXP-067 (EVIDENCE_AGAINST
dominant) alongside, never pooled.

**Falsifiable:** if **no** champion arm simultaneously satisfies the full G-015 conjunction (median-
viable AND mean-positive AND beats RM-native) composed at P11+P6, then the native combined champion
does not satisfy the G-015 PROCEED_TO_SCREEN criterion — a valid characterization result triggering
CHARACTERISED_NOT_VIABLE or MEAN_RECOVERABLE–FOLLOW-UP depending on the P4 mean-diagnostic
structure. Family stays OPEN until the single G-015 gate adjudicates after the full slate.

## Question

On the native MA object, does assembling the per-layer surface winners into the predeclared
champion arms — **PARTIAL-V2A + 1:1 adverse** (the S3 native winner at 21 cells/13 instruments)
and **PARTIAL-V2A + ADV-NONE** (the EXP-060B champion geometry with partial scaling, never
previously computed on native MA with partial exits) — satisfy the G-015 conjunction
simultaneously (median-viable AND mean-positive AND beats RM-native), composed at P11+P6? Does the
mean-positive criterion (the constraint S3's EVIDENCE_FOR did not yet require) hold for the
champion arm(s) under the expanded conjunction? Does removing the adverse stop (`ADV-NONE`) in
combination with PARTIAL-V2A partial exits recover the negative mean seen under bounded-downside
geometry in EXP-063, or does it worsen the tail structure? At what qualifying-event count cost?
Which arm (if either) satisfies all three G-015 criteria simultaneously?

---

## Scope Boundaries

### Data Views

- **Real domain bars** (5m strict; 15m/30m/1h/2h/4h via `xen.bar_aggregator.aggregate_ohlc`,
  `min_coverage=0.90`) for the MA(20,50)-crossover substrate (`ma_segment_moves`), confirmed MA
  segments, `/STRONG-STAT` magnitudes on MA segments (native), the MA benchmark third-barrier cap,
  all champion-arm leg/stop levels, P15 fills, ATR normalisation, and **all** outcome metrics.
- **Heiken Ashi candles** for **harami detection only** (frozen EXP-048 detector). **No HA price
  enters any metric.**
- **ZigZag** (`atr_mult=1.0`) for the hybrid-side conditioning mask (hybrid `H0` via `cond_mask`
  override — needed for the P12 hybrid `H-BENCH` reconciliation check only; **not a binding
  measurement object**).

### Event population (native conditioning object; binding measurement)

The **native** object qualifies iff the harami passes `/STRONG-STAT` p75 on the in-progress
confirmed **MA segment** magnitude-so-far ≥ p75 of the trailing-20 confirmed-MA-segment magnitudes
(recomputed on MA segments; causal — only segments confirmed at/before the harami bar). **Population
byte-identical to EXP-060B `BENCH-MA` / EXP-061 `M0` / EXP-066 `M-BENCH`** (8360-class); the
`N-BENCH` arm **reconciles to them (1e-9)** at P12, and `N-PARTIAL-V2A` reconciles to EXP-066
`M-PARTIAL-V2A` (1e-9) — both checks are binding SUBSTRATE/METHOD_DEFECT guards.

Entry anchor is the harami close `C`. The **trade / reversal direction** `rd` and the
**MA-segment magnitude-so-far** `M_sofar` (hence `fav_dist = 0.50 × M_sofar`, all leg targets, and
the MA adaptive cap) come from the **MA(20,50) substrate** (`ma_seg_arm`), exactly the
EXP-060/061/066 construction. Each arm's matched-random-on-MA null draws **non-harami**
in-MA-regime timestamps, **matched-count to the native qualifying count for that arm**, excluding
the native conditioned-harami entries, on a **dedicated RNG stream**.

### Entry anchor

The **harami confirmation-bar real close** `C`, strictly before any ZigZag/MA trend-change
confirmation. Identical to EXP-053/060B/061/066.

### Champion arms (3 binding arms; native object)

Notation: `C` = entry close; `rd` = trade direction; `M_sofar` = MA-segment magnitude-so-far;
`fav_dist = 0.50 × M_sofar` (MA benchmark); `fav_l = C + rd·(l/3)·fav_dist` for `l ∈ {1,2,3}`
(V2A leg targets); `bench_N` = MA benchmark adaptive cap. Every leg/stop is evaluated on **real
prices** under the **P15 path model** (bullish bar `Close ≥ Open`: `O→L→H→C`; bearish:
`O→H→L→C`). Every arm's forward scan runs `[entry_idx+1, entry_idx + bench_N]`, TRAIN-fenced; a
window truncated before the position resolves is `DATA_CENSORED` (excluded-with-record, disclosed).

**Arm 1 — N-BENCH (benchmark reference):**
Single leg (`w=1`): `resolve_path_ordered` with `(fav, adv, bench_N)` where `fav = C + rd·fav_dist`
and `adv = C − rd·fav_dist` (1:1 stop). **P12 primary reconciliation target**: per-cell median +
qualifying count must match EXP-061 `M0` / EXP-060B `BENCH-MA` to `RECON_TOL = 1e-9`; failure →
SUBSTRATE/METHOD_DEFECT. Disclosed: `r = n_FAV/(n_FAV+n_ADV)` (EXP-049 comparability), expected
≈ 0.50.

**Arm 2 — N-PARTIAL-V2A (S3 surface winner; bounded-downside champion):**
Three equal legs (`w=1/3`): targets at `{1/3, 2/3, 1} × fav_dist` from `C` in direction `rd`. All
open legs share the **MA benchmark 1:1 adverse stop** `adv`; all open legs exit at the MA cap bar's
real close if the cap is reached first (P15 path order resolves same-bar conflicts). Per-event
realised return: `R_event = (1/3)·r_1 + (1/3)·r_2 + (1/3)·r_3` where each `r_l = rd·(exit_l − C)/ATR_entry`.
**P12 secondary reconciliation target**: per-cell median + qualifying count must match EXP-066
`M-PARTIAL-V2A` to `RECON_TOL = 1e-9`; failure → SUBSTRATE/METHOD_DEFECT.

**Arm 3 — N-V2A×ADV-NONE (ZigZag champion analog; novel on native MA with partial exits):**
Three equal legs (`w=1/3`): targets at `{1/3, 2/3, 1} × fav_dist` from `C` in direction `rd`.
**No adverse stop** — open legs remain live until they hit their favourable target or the MA cap
expires; **the MA adaptive cap is the sole stop-out mechanism** for each leg. Each leg exits at
its favourable-price touch (P15 intrabar) or at the cap bar's real close, whichever comes first.
Per-event realised return: `R_event = (1/3)·r_1 + (1/3)·r_2 + (1/3)·r_3`. **No P12
reconciliation anchor exists** for this arm (it was never computed before EXP-068); the
determinism check (two-pass byte-identical) applies instead. This arm is the direct analog of the
EXP-060B V2A×ADV-NONE champion geometry, now combined with partial scaling.

**Total predeclared champion arms: 3 binding arm types** on the native object. The `/STRONG-HA`
arm is a disclosed-secondary (deferred — see Exclusions). Each arm carries its own same-object
matched-random-on-MA null (binding per P5).

**Per-event realised return (binding endpoint input).** For every arm the per-event gross return is
the position-weighted sum of leg returns: `R_event = Σ_l w_l · rd·(exit_px_l − C)/ATR_entry`,
`Σ_l w_l = 1`, `ATR_entry` = Wilder ATR(14) at the harami entry bar (P14). Single-leg arms are the
`w=1` special case.

### Matched-random-on-MA null (RM-native; **binding per P5**, per arm)

For **each** champion arm, a **matched-count random in-regime** control (the EXP-060B / EXP-066
matched-random-in-MA-regime selection, reused unchanged; same cell / direction / regime, valid live
MA state, **matched-count to the native qualifying count for that arm**, **excluding the native
conditioned-harami entries**) is run through the **identical arm exit pipeline** on MA. Native nulls:
`RM-BENCH`, `RM-PARTIAL-V2A`, `RM-V2A×ADV-NONE`. **Signal-attribution requires the arm beats its
own RM-native null** (`arm − RM` median contrast CI_low > 0; P5 binding). The RM draws are
independent of the harami events; the contrast uses the independence-assuming
`xen.expectancy.contrast_ci`. **Dedicated RNG stream per arm** (fresh purpose offsets vs EXP-066
so no existing native stream shifts).

### Parameters (all frozen / predeclared; no tuning)

MA(20,50) on real close (fixed; P1); primary ZigZag Wilder ATR(14), `ATR_MULT=1.0` (hybrid
`H-BENCH` P12 check only); `/STRONG-STAT` trailing-20, ≥p75 (P7; on MA segments for native);
`/STRONG-HA` `X=3` (P8; disclosed, deferred); benchmark favourable `X = 50%` of `M_sofar`;
benchmark adverse 1:1 (for N-BENCH and N-PARTIAL-V2A); **N-V2A×ADV-NONE: no adverse stop**;
benchmark MA adaptive cap `(k=1.5, window=20, floor=6, statistic=median, min_moves=5)` for all
three arms; ATR-normalisation = Wilder ATR(14) at the harami entry bar (P14); bootstrap
`b = round(m^(1/3))`, `N_BOOT = 10_000`, **fixed per-cell seed (P3)** —
`np.random.default_rng([BASE_SEED, cell_index, purpose])` with dedicated purposes per arm/statistic
so the native `N-BENCH` median path stays byte-identical to EXP-061 `M0` and EXP-066 `M-BENCH`, and
`N-PARTIAL-V2A` stays byte-identical to EXP-066 `M-PARTIAL-V2A`. **Position-management parameters
(inherited unchanged from EXP-059 P17, applied here):** 3 equal legs (`w=1/3`); V2A fractions
`{1/3, 2/3, 1}`; no trailing stop (N-PARTIAL-V2A and N-V2A×ADV-NONE use fixed-target legs only).
None tuned against outcomes; no grid swept beyond this predeclared set.

### Instruments / cells / time range

The **99-cell EXP-049/053–066 member grid** (17 instruments × {5m,15m,30m,1h,2h,4h} − 3
COVERAGE_EXCLUDED: US500-4h, JP225-2h, JP225-4h). Per-cell first, then **P11** with the **P6
non-4h rule** (≥ 5 cells over ≥ 3 instruments, with ≥ 3 qualifying cells outside the 4h domain).
**TRAIN only** = first 70% of the first-70% analysis set (F01 file-order prefix; identical fence to
EXP-049/053–066). TEST and the final-30% **global holdout** are **not** read. All forward windows
clipped to `train_end_ts`; unresolved truncated windows `DATA_CENSORED` (disclosed). DE30 carries
the truncated-coverage disclosure.

### Look-ahead / causality discipline (binding)

- MA(20,50) segmentation is future information until confirmed. The signal (harami + `/STRONG-STAT`
  on the MA segment), `rd`, `M_sofar`, the leg targets, and the MA adaptive cap use **only**
  confirmed, completed prior MA segments and **real bars at or before the entry bar**. The native
  `/STRONG-STAT` filter references only confirmed prior MA segments.
- Every exit is a **forward** event acted on at a bar known going forward in real time: fractional
  target touch (intrabar P15) or the cap bar's real close. For ADV-NONE arms: no adverse stop is
  set; the forward scan reads only bars `[entry_idx+1, min(entry_idx+bench_N, last_train_idx)]`,
  fenced `CloseTime ≤ train_end_ts`.
- Ordering/alignment by `CloseTime`, never bar index across views. The `N-BENCH` / `N-PARTIAL-V2A`
  determinism check two-pass verifies byte-identical reconciliation vs EXP-061 / EXP-066 for all
  99 cells.

### Real-price outcome discipline

Harami detected on HA candles; `M_sofar`, ATR normalisation, all leg targets, P15 fills, weighted
expectancy on real domain-bar OHLC. MA(20,50) on **real close**. **No HA price in any metric.**

### Exclusions

- No costs (gross only).
- **Champion arms only** — 3 arms on the native object. No additional geometric OAT: no
  `/VPTARGET`/`/MAGTARGET` (EXP-064; S1 EVIDENCE_AGAINST, benchmark 50% stays), no
  `/THIRD-TIME`/`/THIRD-EVENT` (EXP-065; S2 EVIDENCE_AGAINST, MA cap stays), no `/EXIT-TRAIL-STRUCT`
  (EXP-066; trailing stop not part of the predeclared champion arms), no `/ADV-EXTREME` (not a
  predeclared champion arm), no combined system optimisation beyond the predeclared champion set. No
  `/BARCFG`/`/CONFIRM` overlays; no position-in-move *filter*; **no MA-parameter sweep**.
- **Hybrid object: not a binding measurement object in EXP-068.** The hybrid champion (`H-BENCH` +
  hybrid champion arms) is measured and adjudicated in EXP-067. EXP-068 carries only the native
  binding arms; the `H-BENCH` arm is run **for P12 reconciliation check only** (verifying that the
  native pipeline's ZigZag path still reproduces EXP-061 `H0` — binding correctness check) but its
  results are **not included in any native P11 composition, not used in G-015 for the native object,
  and not presented as a binding hybrid result**. Cross-object comparison is disclosed from
  EXP-061–066 + EXP-067 (when available).
- No parameter tuning; no post-result arm selection (3 predeclared arms, all reported); no early
  gate adjudication (single G-015 after the full slate). No TEST or holdout contact; no candidate
  slot; no TEST read.
- **Deferred disclosed secondaries (runtime/budget; NOT computed here, explicitly — not silently):**
  the `/STRONG-HA` conditioning arm; the `N-V2C×ADV-NONE` and other partial-V-variant + ADV-NONE
  combinations (only V2A is predeclared for ADV-NONE, mirroring the EXP-060B champion axis; further
  ADV-NONE variants are a promotion follow-up only if EXP-068 PROCEED). Recorded in
  `run_metadata.json` (`disclosed_secondaries_not_computed`).

---

## Success / Failure Criteria

All **gross**, per-cell first, P11-composed with the **P6 non-4h rule** (≥ 5 cells over ≥ 3
instruments, ≥ 3 outside 4h). Binding endpoint = **median per-event position-weighted gross
expectancy** `E_cell` (ATR units, P15 fills) on the native `/STRONG-STAT` arm; per-cell viable iff
**CI_low > 0** AND ≥ 30 qualifying events. The **G-015 conjunction** additionally requires
**raw-mean CI_low > 0** in the same cell (mean is a co-primary here, not only a diagnostic). The
10% trimmed mean + worst-5% tail-share are disclosed secondaries supporting the P4 closure rule.

- **PROCEED_TO_SCREEN (G-015):** ≥ 1 champion arm satisfies the full conjunction **(a)** median
  `CI_low > 0` AND **(b)** raw mean `CI_low > 0` AND **(c)** `arm − RM-native` median contrast
  `CI_low > 0` (P5), all **composed at P11 with the P6 non-4h breadth rule**. The qualifying arm,
  its RM margin, and its mean + trim diagnostic are the G-015 deliverable. A candidate registration
  (first slot) is triggered at the G-015 gate — not here.
- **CHARACTERISED_NOT_VIABLE:** no champion arm satisfies all three G-015 conjunction criteria at
  P11+P6 for the native object, **and** the P4 closure rule triggers (10% trimmed mean also
  negative AND the negative mean persists under ADV-NONE AND is not removable-tail-driven). Signals
  structural mean-irrecoverability for native; G-015 CHARACTERISED_NOT_VIABLE if the hybrid object
  (EXP-067) concurs.
- **MEAN_RECOVERABLE–FOLLOW-UP:** no champion arm satisfies the full conjunction at P11+P6 but the
  mean picture is partially positive — e.g. mean-positive in isolation without median+RM composition,
  or mean-negative but dominated by a removable worst-5% tail. Family stays OPEN; targeted follow-up
  (e.g. tail-filtering or parameter relaxation on the ADV-NONE arm). The 10% trimmed mean + tail-
  share diagnose this fork.
- **EVIDENCE_FOR (surface contribution, not G-015):** if a champion arm is median-viable AND beats
  RM at P11+P6 but mean is not positive (satisfies S3 criterion but not G-015 conjunction) — noted
  as the maximum surface contribution; G-015 outcome is still CHARACTERISED_NOT_VIABLE or
  MEAN_RECOVERABLE depending on mean structure. This is the EXP-066 PARTIAL-V2A result status
  reproduced formally.
- **INCONCLUSIVE (power-limited):** fewer than the P11 quorum of cells have ≥ 30 qualifying events
  on the champion arms (ADV-NONE warmup or low-liquidity cells), no correctness failure. Disclosed;
  never defaulted.
- **SUBSTRATE/METHOD_DEFECT:** any reconciliation, determinism, causality, or invariant failure →
  fix before reporting. Invariant checks: (i) **`N-BENCH` reproduces EXP-061 `M0` / EXP-060B
  `BENCH-MA`** per-cell median + qualifying count to `RECON_TOL = 1e-9`; (ii) **`N-PARTIAL-V2A`
  reproduces EXP-066 `M-PARTIAL-V2A`** per-cell median + qualifying count to `RECON_TOL = 1e-9`;
  (iii) **`H-BENCH` (P12 check arm) reproduces EXP-061 `H0`** per-cell median + qualifying count to
  `RECON_TOL = 1e-9`; (iv) population reconciliation: native ↔ EXP-060B/061/066 `M0/M-BENCH`
  (8360-class exact); (v) leg weights sum to 1.0 for every champion arm; (vi) for ADV-NONE arms the
  only stop is the MA cap — any event with a stop-out before `bench_N` is a pipeline defect; (vii)
  **matched-count holds** — each arm's RM count equals the native cell arm signal count.

Deliverable label: **NATIVE_COMBINED_CHAMPION_G015_INPUT**, carrying — **per champion arm** —
the per-cell + P11 (non-4h) readout, the EVIDENCE_*/PROCEED_*/CHARACTERISED_* classification,
arm−RM contrast, raw mean + 10% trimmed mean + worst-5% tail-share (P4 G-015 co-primary), the G-015
conjunction verdict (median AND mean AND RM at P11+P6), disclosed hybrid champion summary from
EXP-061–066 / EXP-067, and all qualifying/`DATA_CENSORED` counts; plus the reconciliation table
(N-BENCH ↔ EXP-061 M0 / EXP-060B; N-PARTIAL-V2A ↔ EXP-066 M-PARTIAL-V2A; H-BENCH ↔ EXP-061 H0).
**No candidate registration here — G-015 gate only.**

---

## Complexity Budget

- **Max distinct statistical methods: 4** — same 4 as EXP-066: (1) regime-clustered moving-block
  bootstrap CI on an arm's **median** per cell; (2) the same bootstrap on the per-cell **mean +
  10% trimmed mean** + worst-5% tail-share (P4 co-primary; now binding in G-015 conjunction, not
  only diagnostic); (3) `arm − RM` independent contrast CI (`contrast_ci`; binding, P5); (4)
  `arm − benchmark` paired-median contrast CI (`xen.favourable_targets.paired_median_contrast_ci`,
  common qualifying-event subset). Applied across 3 predeclared champion arms — a parameterised
  reduction vs EXP-066's 12-arm grid, not new methods.
- **Max visualisations: 4** — (i) per-arm median-expectancy forest/CI per cell (champion arms vs
  benchmark, native; highlighting the G-015 conjunction cells); (ii) arm−RM contrast heatmap (arms ×
  cells; non-4h cells marked; G-015 conjunction overlay); (iii) median vs raw mean vs 10% trimmed
  mean per champion arm — P4 co-primary diagnostic showing where the conjunction fails/passes;
  (iv) G-015 verdict summary — per-arm P11 (non-4h) tally for each conjunction criterion
  (median-viable / mean-positive / beats-RM / all-three) with disclosed hybrid champion reference.
  Secondary tables to CSV.
- **Max new code modules: 1 — *expected 0*.** Reuses EXP-066's native-side code (dual-object
  pipeline); EXP-068 strips to 3 champion arms on the native object, adds the `N-V2A×ADV-NONE`
  forward scanner (no adverse stop — a conditional omission of the adverse stop in the existing
  partial-exit resolver), and updates the output stage to emit the G-015 conjunction verdict per arm.
  At most one thin orchestration wrapper under `code/`; **no new `xen/` analysis module**.

---

## Metric Denominators & Zero-Baseline

- **Per-event realised gross return** (ATR units) is the position-weighted `R_event` (above),
  defined for every **qualifying** event of a champion arm — barriers/legs constructible
  (`fav_dist > 0`, finite positive `ATR_entry`) and the position resolving to a finite P15 exit
  within the TRAIN-fenced window. `DATA_CENSORED` (any leg's window truncated by the TRAIN edge
  before resolution) and construction-warmup events are **excluded** from median/mean/trim and
  **disclosed as counts** per cell per arm.
- **Per-cell G-015 endpoints:** `E_cell_median` (CI_low > 0 binding; P3/P14) AND `E_cell_mean`
  (CI_low > 0 binding; P4 co-primary in G-015 conjunction), each over the arm's qualifying-event
  population, each with its own fixed-seed bootstrap CI. The 10% trimmed mean + worst-5% tail-share
  support the P4 closure rule (disclosed secondaries supporting CHARACTERISED_NOT_VIABLE vs
  MEAN_RECOVERABLE).
- **G-015 conjunction evaluated per cell, composed at P11+P6:** a cell "passes the conjunction" iff
  `E_cell_median CI_low > 0` AND `E_cell_mean CI_low > 0` AND `arm − RM contrast CI_low > 0`,
  simultaneously. P11+P6 requires ≥ 5 passing cells over ≥ 3 instruments, with ≥ 3 outside 4h.
- **Zero-baseline / power:** a cell with < 30 qualifying events for an arm is
  **NOT_VIABLE-by-power** (non-reportable), never an undefined/infinite ratio. ADV-NONE arms may
  have slightly different qualifying counts vs PARTIAL-V2A (all events qualified at construction;
  warmup exclusions for cap apply equally). Worst-5% tail-share: 0 negative mass → tail-share = 0.0
  (finite). First-hit `r` defined only for the single-leg `N-BENCH` arm, disclosed.

---

## Data Requirements

Per cell (instrument × domain), TRAIN slice only: lazy `pl.scan_parquet`;
`analysis_rows = int(total*0.7)`, `train_rows = int(analysis_rows*0.7)`; collect only the first
`train_rows` file-order 1-minute rows (F01 prefix; never sort/collect the full file, never read
TEST/holdout); assert chronological; `train_end_ts` = last `CloseTime`. Aggregate each member
domain (5m strict; others `min_coverage=0.90`); fence to `CloseTime ≤ train_end_ts`; generate HA
candles; run `ma_segment_moves` (MA(20,50) on real close) → confirmed MA segments + crossover
indices + the MA in-progress state (`live_in_progress_state` on MA arrays, supplying `rd` /
`M_sofar` / `start_epoch`); run ZigZag (`atr_mult=1.0`) → confirmed moves + `confirm_indices`
(for hybrid `H-BENCH` P12 check only); detect haramis on HA candles aligned by `CloseTime`; build
the **native** conditioned population (`ma["stat"]["retained_p75"]`, byte-identical to
EXP-060B/061 `M0`); compute the MA benchmark fav + adv levels + MA adaptive cap; for each of the
3 champion arm types compute per-event leg/stop exits via the `position_exits` resolvers (BENCH:
single-leg; N-PARTIAL-V2A: 3-leg partial with 1:1 adverse; N-V2A×ADV-NONE: 3-leg partial with no
adverse stop, MA cap only) under P15, the weighted `R_event`, and the qualifying mask on the
**native population**; build the per-arm matched-random-on-MA native null (`RM-BENCH`,
`RM-PARTIAL-V2A`, `RM-V2A×ADV-NONE`) through the identical pipeline; bootstrap per-cell median +
mean + 10% trimmed mean per arm (fixed seed, dedicated purposes) + worst-5% tail-share; compute
`arm − RM` (independent, binding) contrast per arm; reconcile `N-BENCH` ↔ EXP-061 `M0` /
EXP-060B `BENCH-MA` and `N-PARTIAL-V2A` ↔ EXP-066 `M-PARTIAL-V2A` (both to 1e-9; also reconcile
`H-BENCH` ↔ EXP-061 `H0` as correctness check); compose by P11+P6 per arm; evaluate G-015
conjunction per cell per arm; second full pass for determinism. `tqdm` over the 99-cell grid;
**bounded per-cell memory** (per-event forward scans bounded by `bench_N`; per-cell arrays
released after summarisation; plots from collected per-cell summaries only — no reloads). Output
**byte-identical across `--workers`** counts (fixed-order reassembly + order-independent per-cell
RNG).

**Outputs (`results/`):** `per_cell_expectancy.parquet` (per cell × arm: median/mean/trimmed + CIs,
tail-share, arm−RM contrast, n_qualifying, censoring counts, viability + beats-RM + mean-positive
+ G015-conjunction flags); `champion_map.csv` (binding `/STRONG-STAT` summary per arm + P11 non-4h
tally + G-015 conjunction tally); `secondary_map.csv` (BENCH `r`, tail-share/trimmed per arm,
H-BENCH P12 check result, hybrid champion disclosed summary from EXP-061–066/EXP-067);
`reconciliation.csv` (N-BENCH ↔ EXP-061 M0 / EXP-060B BENCH-MA; N-PARTIAL-V2A ↔ EXP-066
M-PARTIAL-V2A; H-BENCH ↔ EXP-061 H0; native population vs EXP-060B/061/066);
`g015_verdict.json` (per-arm G-015 conjunction tally: median-viable / mean-positive / beats-RM /
all-three counts at P11+P6; overall PROCEED_TO_SCREEN / CHARACTERISED_NOT_VIABLE /
MEAN_RECOVERABLE / INCONCLUSIVE verdict for native; disclosed hybrid champion from surface reads /
EXP-067); `run_metadata.json` (seed, frozen + inherited constants,
EXP-059/060/060B/061/066 source paths/hashes, holdout fence,
`disclosed_secondaries_not_computed`). Output dirs created only in orchestration. **No pooled
aggregate across arms or objects is emitted.**

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

Fork **EXP-066's `code/run_experiment.py`** (native-side pipeline already validated — the
`N-BENCH` and `N-PARTIAL-V2A` paths reproduce to 1e-9 and are fully instrumented for per-arm RM
nulls, P4 mean/trim/tail bootstrap, and P11 non-4h composition). Changes, all bounded: **(1)**
reduce the arm loop from 12 arm types to **3 predeclared champion arms** on the native object;
strip all hybrid binding arms (keep `H-BENCH` in a separate P12 check sub-pass only); **(2)** add
the **`N-V2A×ADV-NONE` forward scanner** — identical leg targets as `N-PARTIAL-V2A`
(`{1/3, 2/3, 1} × fav_dist`) but with the adverse stop omitted: the only exit triggers are the
three leg-target touches (P15 intrabar) or the MA cap bar's real close (`DATA_CENSORED` if the
window is truncated before all legs resolve); implement this as a conditional flag in the existing
partial-exit resolver (`no_adverse=True` branch — at most 5–10 lines); **(3)** add the **P12
secondary reconciliation check** for `N-PARTIAL-V2A` → EXP-066 `M-PARTIAL-V2A` (same pattern as
the existing `N-BENCH` ↔ EXP-061 check, pointing at the EXP-066 results file); **(4)** update the
G-015 conjunction evaluation: per-cell, per-arm, flag `g015_passes` = `median CI_low > 0` AND
`mean CI_low > 0` AND `arm−RM contrast CI_low > 0` simultaneously — emit the P11+P6 count over
`g015_passes` cells as the decisive readout; **(5)** emit `g015_verdict.json` with the per-arm
G-015 verdict and the disclosed hybrid champion summary from EXP-061–066 / EXP-067. Keep
EXP-066's per-instrument `ProcessPoolExecutor` with native-thread pinning and fixed-order
reassembly (byte-identical for any `--workers`). Fixed per-cell seed throughout (P3); `tqdm`;
bounded memory; **do not adjudicate G-015 within the code** (that is a documented output
interpretation step in results.md). The existing `N-BENCH` RNG paths must stay byte-identical to
EXP-061/066 (use new RNG purposes for `N-V2A×ADV-NONE` and its null only).
