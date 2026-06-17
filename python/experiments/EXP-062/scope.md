# Experiment: EXP-062 — MA(20,50)-Substrate Lifetime Availability (Conditioned HA Harami; AVWAP-Analog MFE/MAE, **Dual Conditioning Object: Hybrid and Native**, Phase 015 Lead L2)

> **Re-run under `D0-amendment-001-dual-parallel-substrate.md` (2026-06-17).** The prior EXP-062
> measured a single MA availability arm (`A_MA`) labelled *hybrid* but actually conditioned on
> MA-segment `/STRONG-STAT` — the **native** object. The genuine **hybrid** object
> (ZigZag-`/STRONG-STAT`-conditioned × MA lifetime window) was never computed. This re-run emits
> **both** objects **individually** (separate availability arms, separate matched-random nulls,
> separate `MOVE_AVAILABLE`/`SIGNAL_ATTRIBUTABLE`/P11, separate AVAILABILITY_* fork — never pooled)
> and **supersedes the prior EXP-062 result in place**.

> **Mandatory-reading precondition (Phase 015, binding — inherited from 014-B).**
> `../../docs/experiments-docs/checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/014-A-conditioning-gap-and-validation-lessons.md`
> was read in full before this scope was written. The four mandatory rules are honoured, recorded so
> Stage 4 can check:
> - **(a) conditioning** — honoured, **and now disambiguated** (Amendment 001). Two live
>   `/STRONG-STAT`-conditioned HA-harami objects are measured individually over the **same** MA
>   lifetime window: **hybrid** (filter on the in-progress confirmed *ZigZag* move — entry population
>   byte-identical to EXP-053; the genuinely-new object) and **native** (filter recomputed on the
>   in-progress confirmed *MA segment* — the population the prior `A_MA` actually used; reconciles to
>   EXP-055's `ma_seg` arm). `/STRONG-STAT` (P7) is binding in each; the raw harami and unconditioned
>   ZigZag substrate are not the object. Each object's matched-random-on-MA control is a deliberate
>   **null** (P5), not a signal claim. The two objects are never pooled.
> - **(b) harami-anchor** — honoured: the per-event window is anchored at the **harami confirmation-bar
>   real close** `C`, the family's claimed lead point — *not* the ZigZag (or MA) trend-change
>   confirmation. The MA(20,50) substrate supplies only the lifetime **window boundary** and the
>   excursion geometry; it does **not** move the anchor. The matched-random control intentionally breaks
>   the anchor (that is what makes it a null).
> - **(c) position-in-move descriptive-only / never a live filter** — honoured. EXP-050's position metric
>   is not used as a filter. The lifetime **window boundary** uses retroactively-confirmed MA-segment
>   crossovers, permitted here because this is a **descriptive characterisation of completed moves**
>   (completed-move grouping; family doc lines 139–143; the same P19 allowance EXP-055 relied on), not a
>   live signal condition. No barrier, entry, or filter uses an unconfirmed crossover.
> - **(d) expectancy / not first-hit `r`** — honoured *with the availability-appropriate endpoint*. This
>   is an **availability** diagnostic, not a capture/expectancy read: the binding metrics are **lifetime
>   favourable MFE and adverse MAE** (gross, ATR-normalised), with the **median** the binding statistic
>   (P14) and the **mean + 10% trim + worst-5% tail-share** the P4 diagnostic. No trading rule, barrier,
>   partial exit, or stop is applied (those are EXP-063–067); measuring availability under first-hit `r`
>   would foreordain the answer (lessons §8.6).
> EXP-062 does **not** treat the EXP-049 `r≈0.50` null or the EXP-050 front-loading as evidence against
> the family — those measured the *unconditioned* object on the ZigZag substrate. It settles the open
> AVWAP parallel **on the MA substrate** (lessons §7): *move available + capture missing* (keep iterating
> geometry/exits across L3/S1–S4) vs *no available move* (closure better-supported).

**Phase / checkpoint:** `2026-06-17-015-ma-substrate-conditioned-harami-full-surface` (Phase 015; **G0 PASS 2026-06-17**).
**Family / candidate:** `CF-HA-HARAMI-001` (`REGISTERED`, OPEN) · Phase 015 lead **L2** ·
`CF-HA-HARAMI-001/HYP-015` — EXP-062 (Phase 015 batch, `multiplicity-registry.md` line 476).
**Registry precondition (satisfied):** `CF-HA-HARAMI-001/MA-SUBSTRATE` and **both** its conditioning
modes (`hybrid`, `native`) are **REGISTERED** and parallel first-class per `D0-amendment-001`
(Phase 015 batch, 2026-06-17, G0 PASS); HYP-015/EXP-062 is the listed plan (`EXP-055`-analog, L2),
now emitting both objects individually. The MA-segment lifetime window, the conditioned `/STRONG-STAT` population,
and the matched-random baseline are already registered (Phase 014/014-B + EXP-055/EXP-061 reuse). The
reference band `{0.5, 1.0}` ATR is the EXP-055 operator-declared reporting yardstick (reference-only,
never subtracted). **No new countable item is introduced here.**
**Surface role:** the Phase 015 **lead L2** — the AVWAP EXP-047/EXP-055 analog *on the MA substrate*.
EXP-055 found `AVAILABILITY_GOOD` on the ZigZag substrate (74 `MOVE_AVAILABLE` cells). The MA segments are
**longer** than ZigZag moves (the structural reason MA "wins" in EXP-060B), so this read asks whether the
extra lifetime favourable room is (i) real and (ii) **signal-attributable** (the conditioned harami beats
matched-random-on-MA), and characterises the **adverse** distribution (MAE median + tail) to size the
**downside-bounding** opportunity the L3 read (EXP-063) acts on. Output feeds the single terminal
**G-015** after the full slate; **no closure or candidate registration here** (P9 no-early-closure).
**Governing design / D0:** `design.md` (§1 two objects; §3 objective; §4 mean posture; §5 slate L2;
§7 G-015 criteria) + `D0-predeclarations.md` (P1 substrate; **P2 both objects parallel/individual**;
P3 median binding + fixed seed; P4 mean diagnostic; **P5 matched-null per object every read**; P6 non-4h
composition; P10 power; **P12 reconciliation roles — native↔EXP-055 `ma_seg` 1e-9, hybrid anchorless**) +
`D0-amendment-001-dual-parallel-substrate.md`. Inherits 014-B P14/P15 and the EXP-055 (HYP-008)
availability method.
**Reuses (expected 0 new `xen/` modules):** EXP-055's `code/availability.py` wholesale
(`end_of_mb_window`, `lifetime_excursions_atr`, `window_invariants_ok`, `median_block_bootstrap`,
`median_diff_block_bootstrap`, `move_available`, `availability_status`, `composition_fork`); EXP-055's
`ma_segment_moves` / `ma_seg_arm` (the EXP-062 binding object is exactly EXP-055's MA-segmentation
**baseline** arm, here promoted to binding) and `matched_random_arm` (generic over `confirm_idx` /
`state_all` — passed the MA analogs to form the binding RM-on-MA null); the EXP-053/061 conditioned-signal
construction (`xen.expectancy.live_in_progress_state`, `live_strong_stat`); ZigZag (`xen.zigzag`), HA
(`xen.heiken_ashi_generator`), harami (`xen.ha_harami`), `/STRONG-HA` (`xen.strong_move`). The mean / 10%
trimmed-mean / worst-5% tail-share diagnostic reuses EXP-061's `bootstrap_stat_distribution` /
`_trimmed_mean` / `_tail_share_worst5` (P4).

## Slot & ledger accounting (binding)

- **0 candidate slots, 0 TEST reads.** Characterization/diagnostic per the Phase 015 D0 (P11). No countable
  item is introduced: `MA-SUBSTRATE` (+ `hybrid` mode) is registered at G0; the MA lifetime window, the
  conditioned population, and the matched-random null pre-exist (EXP-055/EXP-061). A slot is consumed only
  at a future G-015 PROCEED.
- **No TEST stratum is read.** All work on the **TRAIN** slice (first 70% of the first-70% analysis set;
  F01 file-order prefix; identical fence to EXP-049/053–061). Population byte-identical to EXP-053/055/060;
  no new stratum opened; `test-read-ledger.md` requires no entry; the global-holdout seal carries forward.
  No HA-harami TEST stratum has ever been read.
- All work **gross**; detection on HA candles; **all outcome metrics on real-price OHLC**; MA(20,50)
  computed on **real close** (identical to EXP-055/060/061 `ma_segment_moves`). No HA price enters any
  metric; the reference band is gross, ATR-normalised, and never subtracted.

---

## Question (exploratory / diagnostic)

For the live `/STRONG-STAT`-conditioned HA harami (hybrid mode; anchored at the harami confirmation-bar
real close `C`; the EXP-053/060/061 population), over the **full reversal MA segment** that follows it —
the lifetime window `[C+1 → end of the reversal MA segment M_b]`, where M_b ends at the **2nd MA(20,50)
crossover at/after the entry** — what is the gross, ATR-normalised distribution of **lifetime favourable
excursion (MFE)** vs **lifetime adverse excursion (MAE)**, per cell and composed across the 99-cell grid,
and:

1. is a meaningful favourable reversal move **available** (median MFE robustly above the 1.0-ATR reference
   line and above its own median MAE — the EXP-055 `MOVE_AVAILABLE` test)?
2. is that favourable availability **signal-attributable** — does the conditioned harami's median MFE
   **beat matched-random-on-MA** (the in-regime null through the identical MA lifetime window), or is the
   room a generic property of the (longer) MA segments (P5)?
3. what does the **adverse** side look like — median MAE, its raw/trimmed mean, and the **worst-5%
   tail-share** — i.e. is there **room to bound the downside** (a thin, truncatable MAE tail) while keeping
   the favourable capture, sizing the bounded-downside opportunity the L3 read (EXP-063) acts on (P4)?

This is a **characterisation**, not an edge test. There is no "success"/"failure" edge claim; the
deliverable is the MA-substrate availability map, the signal-vs-null attribution, the adverse/tail
decomposition, and the AVWAP-comparison fork readout — all feeding the single terminal **G-015**. The
falsifiable sub-structure (correctness, not edge) is the monotone/causal/determinism/reconciliation set
under §Correctness Gates.

---

## Scope Boundaries

### Data Views

- **Real domain bars** (5m strict; 15m/30m/1h/2h/4h via `xen.bar_aggregator.aggregate_ohlc`,
  `min_coverage=0.90` — identical to EXP-048/049/053/055/061/VAL-004) for the MA(20,50)-crossover substrate
  (`ma_segment_moves` on real close), the ZigZag substrate (`atr_mult=1.0`, disclosed contrast), confirmed
  moves/segments, `/STRONG-STAT` magnitudes, ATR normalisation, the lifetime window, and **all** excursion
  metrics.
- **Heiken Ashi candles** (`xen.heiken_ashi_generator`) for **harami detection only** (frozen EXP-048
  detector) and the disclosed `/STRONG-HA` arm. **No HA price enters any metric.**

### Event population (two conditioning objects, measured individually over the same MA window)

Both objects share the **same** frozen HA-harami detection, the **same** MA(20,50) lifetime window
boundary (the 2nd MA crossover at/after entry), and the **same** `rd`; they differ **only** in the
`/STRONG-STAT` conditioning filter:

- **Hybrid (`A_MA_hyb`).** Qualifies iff the harami passes `/STRONG-STAT` p75 on the **in-progress
  confirmed ZigZag move** magnitude-so-far (P2 hybrid mode). The conditioning mask is **byte-identical
  to EXP-053/055's ZigZag-`/STRONG-STAT` set** (the same `live_in_progress_state` / `live_strong_stat`
  on the ZigZag move). MA supplies only the lifetime window + `rd`. **This is the genuinely-new
  object** (a ZigZag-conditioned population over the MA window was never computed before).
- **Native (`A_MA_nat`).** Qualifies iff the harami passes `/STRONG-STAT` p75 on the **in-progress
  confirmed MA segment** magnitude-so-far (recomputed on MA segments). **Population byte-identical to
  the prior EXP-062 `A_MA` and reconciles to EXP-055's `ma_seg` arm** (1e-9).

Entry anchor is the harami close `C` in both. `/STRONG-HA` (P8: run of `X=3` large-body HA bars, no
opposing wick) and the MAD `/STRONG-STAT` sensitivity are **disclosed secondary** arms through the
identical pipeline (computed on each object's own substrate filter where applicable). Each object's
matched-random-on-MA null draws **non-harami** in-MA-regime timestamps, **matched-count to that
object's qualifying count**, on **independent dedicated RNG streams**.

### Lifetime window (MA-substrate analog of the EXP-055 end-of-M_b decision)

For each qualifying harami at entry bar `e` (entry = harami confirmation-bar real close `C`, real-bar
index aligned by `CloseTime`):

- Let `ma_confirm_idx` be the sorted MA(20,50)-crossover bar indices for the cell (`ma_segment_moves`
  `confirm_idx`; segments alternate direction by construction).
- `pos = searchsorted(ma_confirm_idx, e, side="right")` — the first MA crossover **strictly after** `e`.
  - `c1 = ma_confirm_idx[pos]` ends the in-progress (faded) MA segment **M_a**.
  - `c2 = ma_confirm_idx[pos+1]` ends the **reversal MA segment M_b** — the **window end**.
- **Window** = real bars `[e+1, c2]` (inclusive of the M_b end-crossover bar). Excursions measured over
  this window on real OHLC.
- **DATA_CENSORED** (excluded from medians/means, disclosed as a count/fraction): fewer than **two** MA
  crossovers exist at/after `e` before the TRAIN edge (`pos+1 ≥ ma_confirm_idx.size`), i.e. M_b does not
  complete inside TRAIN. Never silently clipped to the TRAIN edge; censoring is a disclosed exclusion.

This is the **direct MA analog of EXP-055's operator decision** (window end = end of the reversal move
M_b), computed by `availability.end_of_mb_window(entry_idx, ma_confirm_idx)` — **exactly what EXP-055's
`ma_seg_arm` already did** as a disclosed baseline. It is a **descriptive completed-move grouping** (the
retroactively-confirmed MA crossovers `c1`,`c2` are future information relative to the bars between them,
used only as a descriptive lifetime boundary — never as a live signal/entry/filter; family doc lines
139–143, P9, P19).

### Metrics (gross, ATR-normalised, real prices)

For each qualifying, non-censored event, over the window `[e+1, c2]` (`availability.lifetime_excursions_atr`):

- **Lifetime favourable MFE** = max favourable excursion in the reversal direction `rd`:
  long (`rd=+1`): `MFE = (max(High[e+1..c2]) − C)/ATR_entry`; short (`rd=−1`): `MFE = (C − min(Low[e+1..c2]))/ATR_entry`.
- **Lifetime adverse MAE** = max adverse excursion against `rd`: long: `MAE = (C − min(Low))/ATR_entry`;
  short: `MAE = (max(High) − C)/ATR_entry`. Both floored at `0.0` (standard excursion convention).
- **`ATR_entry` = Wilder ATR(14) at the harami entry bar** — the **same divisor as EXP-053/055/061** (P14),
  so EXP-062 excursions are directly comparable to the EXP-061 benchmark expectancy and the EXP-055 ZigZag
  availability.
- Per event: `MFE`, `MAE`, and the derived `MFE − MAE` (favourable-availability asymmetry, ATR units).

### Mean / trim / tail diagnostic (P4 — the downside-bounding preview, disclosed)

Alongside the **median** (binding) MFE and MAE per cell, the read emits — **for the MAE distribution
primarily, and the MFE distribution for completeness** — the **raw mean** (bootstrap CI), the **10%
symmetric trimmed mean** (bootstrap CI), and the **worst-5% tail-share** (the fraction of total adverse
excursion contributed by the worst 5% of events; for MAE the "worst" tail is the largest adverse
excursions). A thin, top-heavy MAE tail (large tail-share, trimmed-mean MAE ≪ raw-mean MAE) ⇒ the downside
is **bounded-recoverable** (a 1:1 / `/ADV-EXTREME-rr1` stop would truncate it) — the mechanistic input to
L3 (EXP-063). These are **diagnostic only**: they never set a `MOVE_AVAILABLE` flag or any viability gate
(P4 closure-on-mean rule — a mean/tail read never closes anything here).

### Reference band (EXP-055 operator-declared: 0.5× and 1.0× ATR — reference-only, never subtracted)

Two fixed reference lines at **0.5 ATR-units** and **1.0 ATR-units** annotate every MFE/MAE distribution
and the per-cell median table. They are a **cost-floor analog** (the gross, ATR-normalised stand-in for the
EXP-047 frozen cost floor): a **declared, fixed ATR fraction**, used **only as a comparison yardstick**
(median MFE reported as a multiple of each line). They are **never subtracted** from any excursion and carry
**no net-of-cost interpretation** (all work is gross). The **1.0-ATR upper line** is the binding
`MOVE_AVAILABLE` comparison (median-MFE CI_low > 1.0, exactly as EXP-055).

### Predeclared arm set (lifetime availability × {MA, ZigZag} × {signal, matched-random})

| # | Arm | Object | Substrate | Conditioning | Window | Role |
|---|-----|--------|-----------|--------------|--------|------|
| **A_MA_hyb** | conditioned harami, MA lifetime | **hybrid** | MA(20,50) | **ZigZag** `/STRONG-STAT` | MA M_b (2nd MA crossover) | **Binding object — HYBRID.** NEW; no outcome anchor. |
| **RM_MA_hyb** | matched-random in-regime | hybrid null | MA(20,50) | — (random in-regime) | MA M_b | **Binding null for `A_MA_hyb`** (P5). Matched to its count. NEW. |
| **A_MA_nat** | conditioned harami, MA lifetime | **native** | MA(20,50) | **MA-segment** `/STRONG-STAT` | MA M_b | **Binding object — NATIVE.** Reconciles to EXP-055 `ma_seg` (1e-9). |
| **RM_MA_nat** | matched-random in-regime | native null | MA(20,50) | — (random in-regime) | MA M_b | **Binding null for `A_MA_nat`** (P5). Matched to its count (prior `RM_MA`). |
| A_ZZ | conditioned harami, ZigZag lifetime | zigzag | ZigZag | ZigZag `/STRONG-STAT` | ZigZag M_b | Disclosed substrate contrast. Reconciles to EXP-055 binding arm. |
| RM_ZZ | matched-random in-regime | zigzag null | ZigZag | — (random in-regime) | ZigZag M_b | Disclosed ZigZag null (EXP-055 matched-random analog). |

`/STRONG-STAT` is binding for every signal arm. **No** barrier / favourable-target / adverse-target / time-cap /
third-barrier / exit / first-hit-`r` arm here — those are the later Phase 015 reads (L3/S1–S3). The
binding discriminators are, **per object individually (never pooled)**: each object's availability
(`MOVE_AVAILABLE`) **and** its own `signal − null` median-MFE contrast (`A_MA_hyb − RM_MA_hyb`;
`A_MA_nat − RM_MA_nat`). Disclosed secondaries: the `/STRONG-HA` arm, the MAD `/STRONG-STAT`
sensitivity arm, and the ZigZag arms (A_ZZ / RM_ZZ).

### Parameters (all frozen / predeclared; no tuning)

ZigZag Wilder ATR(14), `ATR_MULT=1.0` (P1; disclosed contrast only); **MA(20,50) on real close (fixed; P1
— not swept)**; `LOOKBACK=1` for the in-progress reference; `/STRONG-STAT` trailing-20 ≥ p75 (P7; MAD
disclosed); `/STRONG-HA` `X=3` (P8); ATR-normalisation divisor = Wilder ATR(14) at the harami entry bar
(P14); reference band `{0.5, 1.0}` ATR (EXP-055 operator-declared, reference-only); bootstrap
`b = max(1, round(m^(1/3)))`, `N_BOOT = 10_000`, **fixed per-cell seed (P3)** — `np.random.default_rng([BASE_SEED, cell_index, purpose])`.
No barrier model, no time cap, no partial exit, no trailing stop (no capture rule in an availability read);
no grid swept; no parameter tuned against outcomes.

### Instruments / cells / time range

The **99-cell EXP-049/053–061 member grid** (17 instruments × {5m,15m,30m,1h,2h,4h} − 3 COVERAGE_EXCLUDED:
US500-4h, JP225-2h, JP225-4h). Per-cell first, then **P11** with the **P6 non-4h rule** (≥5 cells over ≥3
instruments, **with ≥3 of the qualifying cells outside the 4h domain**) for any family-level availability
or attribution claim. **TRAIN only** = first 70% of the first-70% analysis set (F01 file-order prefix;
identical fence to EXP-049/053–061). TEST and the final-30% global holdout are **not** read. Forward windows
clipped to `train_end_ts`; events whose M_b would complete past the TRAIN edge are `DATA_CENSORED`. DE30
carries the truncated-coverage disclosure (broker history ends 2026-01-16).

### Look-ahead / causality discipline (binding)

- ZigZag and MA(20,50) segmentation are future information until confirmed. The **signal** (harami +
  `/STRONG-STAT`) and `M_sofar` use only the **confirmed start pivot/crossover** (known) and the entry
  bar's own real close (known) — reused causal construction from `xen.expectancy.live_in_progress_state` /
  `live_strong_stat`. MA(20,50) `_sma` is trailing; MA segments are bounded by crossovers confirmed before
  entry. Matched-random entries are constructed causally with the identical pre-entry-only in-progress state.
- The lifetime **window boundary** (`c1`,`c2`) uses retroactively-confirmed MA crossovers **only as a
  descriptive completed-move grouping** (P19; family doc lines 139–143). No entry, filter, or excursion
  threshold references an unconfirmed crossover or any future bar beyond the excursion window itself.
- Excursions read only bars `[e+1, c2]`, fenced `CloseTime ≤ train_end_ts` (a censored event whose M_b
  would complete past the TRAIN edge is `DATA_CENSORED`-excluded, never measured against truncated data).
- Ordering/alignment by `CloseTime`, never bar index across views.

### Exclusions

- No costs (gross only); the reference band is never subtracted and carries no net interpretation.
- **No capture rule of any kind** — no 3-barrier geometry, no favourable/adverse target, no time cap, no
  first-hit `r`, no `/ADV-NONE`/`/ADV-EXTREME`, no `/VPTARGET`/`/MAGTARGET`/`/THIRD-*`, no `/EXIT-*`.
  EXP-062 measures *available* excursion, not *captured* return (capture is EXP-061/063–067).
- No `/BARCFG`/`/CONFIRM` overlays; no MA-native conditioning (that is EXP-068/069); no MA-parameter sweep
  (MA(20,50) fixed); no position-in-move *filter*.
- No parameter tuning, no post-result variant or reference-line selection; no gate adjudication (single
  G-015 after the full slate — EXP-062 emits a characterization readout only). No TEST or holdout contact;
  no candidate slot; no TEST read.

## Outcome readout (predeclared, mechanical; EXP-062 emits — it does not self-adjudicate G-015)

Like EXP-055, EXP-062 **emits** the readout; phase routing is the single terminal **G-015** desk
adjudication. All readouts are gross, per-cell first, composed by **P11 with the P6 non-4h rule**,
**computed and reported separately for each object** (hybrid `A_MA_hyb`, native `A_MA_nat`) — never
pooled. Power floor: a cell with **< 30 qualifying non-censored events** (per arm) is
**NOT_VIABLE-by-power** (non-reportable for the composition, disclosed, never an undefined ratio).

- **Per-cell `MOVE_AVAILABLE` (graded, mechanical; `availability.move_available`), per object:** a
  reportable cell is flagged `MOVE_AVAILABLE` for an object iff **(i)** ≥30 qualifying events on that
  object's signal arm, **(ii)** the regime-clustered moving-block bootstrap **CI_low of median MFE >
  1.0** (the upper reference line — a *comparison threshold*, never a subtraction), **AND (iii)** median
  MFE > median MAE. Each cell additionally reports median MFE as a **multiple of both reference lines**
  (×0.5-ATR, ×1.0-ATR) and median MAE, with CIs, **per object**.
- **Per-cell `SIGNAL_ATTRIBUTABLE` (P5; mechanical), per object:** the object's median MFE **beats its
  own null** — `A_MA_hyb − RM_MA_hyb` (hybrid) / `A_MA_nat − RM_MA_nat` (native) independent
  median-difference moving-block bootstrap (`availability.median_diff_block_bootstrap`) has
  **CI_low_1s > 0**. Disclosed in parallel: each object's `signal − null` median-MAE contrast (is the
  conditioned signal's adverse excursion *smaller* than random's, or merely its favourable *larger*?).
- **Family-level fork (the deliverable label, descriptive — final routing is G-015), computed
  separately for each object on its binding `A_MA_*` arm:**
  - **AVAILABILITY_GOOD** (the AVWAP situation — *move available, capture missing*): `MOVE_AVAILABLE`
    clears **P11 with the P6 non-4h rule**. Reading: a meaningful favourable reversal move is available on
    the MA substrate that the short-horizon benchmark capture (EXP-061) missed → continuing to iterate
    capture geometry/exits across the surface (L3/S1–S4) is justified. The `SIGNAL_ATTRIBUTABLE` tally
    (how many `MOVE_AVAILABLE` cells also beat RM_MA, with non-4h breadth) is reported alongside — it
    qualifies whether the available room is signal-driven or a generic MA-segment property.
  - **AVAILABILITY_POOR** (worse than AVWAP — *no available favourable move*): `MOVE_AVAILABLE` does **not**
    clear P11+non-4h. Reading: closure is **better-supported** than for AVWAP — but **no closure occurs
    inside Phase 015** (G-015 only, on the full surface).
  - **INCONCLUSIVE** (power-limited): fewer than the P11 quorum of cells reach ≥30 qualifying events
    (conditioning + the 2-MA-crossover window deplete counts), with no correctness failure. Disclosed;
    never defaulted.
  - **SUBSTRATE/METHOD_DEFECT:** any determinism, causality, invariant, or **reconciliation** failure
    (§Correctness Gates) → fix before reporting.
- Disclosed in parallel: the `/STRONG-HA` arm and the MAD `/STRONG-STAT` arm; the ZigZag arms (A_ZZ / RM_ZZ
  — does availability *and* its signal-attribution differ between substrates?); the DATA_CENSORED fraction
  per cell per arm; the MFE/MAE distributions; the median `MFE − MAE` asymmetry map; the P4 mean/trim/tail
  decomposition (MAE-focused) feeding L3.

Deliverable label: **MA_AVAILABILITY_CHARACTERISED (dual-object)**, carrying — **per object,
individually** — the per-cell `MOVE_AVAILABLE` map, the `SIGNAL_ATTRIBUTABLE` (`A_MA_hyb−RM_MA_hyb` /
`A_MA_nat−RM_MA_nat`) tally, the P11+non-4h composition, the per-object AVAILABILITY_* fork, both
reference-line multiples, and the MAE mean/trim/tail decomposition (the L3 downside-bounding input);
plus the disclosed `/STRONG-HA`/MAD/ZigZag arms, the reconciliation (native↔EXP-055 `ma_seg` 1e-9;
hybrid conditioning↔EXP-053 via A_ZZ), and all censoring counts. **No phase closure or candidate
registration here.**

## Correctness Gates (falsifiable sub-structure; binding)

- **Determinism (P12):** a full second pass (re-aggregate, re-run ZigZag + MA segmentation, re-detect
  haramis, re-condition, re-measure excursions, re-draw matched-random under the fixed per-cell seed)
  reproduces every per-cell figure frame-identically. Any mismatch → SUBSTRATE/METHOD_DEFECT. Output must be
  **byte-identical across `--workers` counts** (order-independent per-cell RNG + fixed merge order).
- **Causality / window invariants (`availability.window_invariants_ok`, on MA `confirm_idx`):** `MFE ≥ 0`,
  `MAE ≥ 0`; every excursion window satisfies `e+1 ≤ c2 ≤ train_last_idx`; `c2 = ma_confirm_idx[pos+1]`
  with `ma_confirm_idx[pos] > e`; no event reads a bar with `CloseTime > train_end_ts`; MA reference
  segments end at/before entry (`_causality_ok` MA leg). Violation on ≥3 instruments →
  SUBSTRATE/METHOD_DEFECT.
- **Matched-count invariant (P5), per object:** each null's qualifying-draw target equals its **own**
  object's binding signal-arm qualifying count (`RM_MA_hyb=A_MA_hyb`, `RM_MA_nat=A_MA_nat`,
  `RM_ZZ=A_ZZ`).
- **Population reconciliation (P12 anchor, corrected roles):** the **native** `A_MA_nat` arm
  **reproduces EXP-055's `ma_seg` baseline arm** — per-cell qualifying count, median MFE, and median MAE
  to float tolerance (`RECON_TOL = 1e-9`) — and the A_ZZ arm reproduces EXP-055's binding ZigZag arm
  likewise. The **hybrid** `A_MA_hyb` arm has **no outcome back-reconciliation anchor** (new object); its
  ZigZag-`/STRONG-STAT` conditioning mask is the same mask that defines A_ZZ's population (= EXP-053/055
  conditioned set), so the conditioning is verified **transitively via A_ZZ** (count + digest), while its
  qualifying count under the MA window is a disclosed-new quantity. A reconciliation failure is a
  SUBSTRATE/METHOD_DEFECT — fixed before the readout is trusted.

## Complexity Budget

- **Max statistical methods: 4** (Comparative experiment) — (1) regime-clustered moving-block bootstrap CI
  on median MFE per cell; (2) the same on median MAE; (3) the **A_MA − RM_MA** matched-random median-MFE
  (and disclosed median-MAE) difference bootstrap (`median_diff_block_bootstrap`); (4) the P4 mean + 10%
  trimmed-mean bootstrap CI + worst-5% tail-share (MAE-focused diagnostic). A re-instrumentation of the
  EXP-055/EXP-061 machinery, not new methods.
- **Max visualisations: 4** — (i) **per-cell median MFE & MAE forest** with the 0.5/1.0-ATR reference band
  (binding availability map); (ii) **A_MA vs RM_MA median-MFE contrast forest** (the signal-attribution
  discriminator, non-4h cells marked); (iii) **MAE tail decomposition** — per-cell raw-mean vs 10%-trimmed
  MAE with worst-5% tail-share annotated (the L3 downside-bounding preview); (iv) **`MOVE_AVAILABLE` /
  `SIGNAL_ATTRIBUTABLE` / P11+non-4h composition map** (17×6, with NOT_VIABLE-by-power and
  COVERAGE_EXCLUDED cells marked). Disclosed-arm tables, censoring counts, and reference-line multiples go
  to CSV.
- **Max new code modules: 0–1.** **Expected 0 new `xen/` module.** EXP-055's `code/availability.py` is
  copied into `code/` unchanged (or imported) and the orchestration in `code/run_experiment.py` reuses it
  plus the EXP-061 MA-substrate matched-random and mean/trim/tail diagnostic. At most one thin orchestration
  module under `code/`.

## Metric Denominators & Zero-Baseline

- **Qualifying-event population** (the MFE/MAE denominator): events that (a) pass the binding `/STRONG-STAT`
  filter (`defined ∧ retained_p75`) with a valid live in-progress move (`InProgressState.valid`,
  `m_sofar>0`), (b) have `ATR_entry` defined and positive (post-Wilder-ATR-warmup), and (c) are **not
  DATA_CENSORED** (M_b completes inside TRAIN). Warmup-excluded and `DATA_CENSORED` events are **excluded**
  from medians/means and **disclosed as counts/fractions** per cell per arm.
- **Per-cell endpoint:** `median` over the qualifying-event MFE (and, separately, MAE) population (binding,
  P14). The raw mean, 10% trimmed mean, and worst-5% tail-share are the P4 disclosed diagnostic.
- **Zero-baseline / power:** a cell with **< 30 qualifying events** (per arm) is **NOT_VIABLE-by-power**
  (non-reportable for the composition), never an undefined or infinite ratio. Conditioning + the
  2-MA-crossover window reduce counts vs the unconditioned base; cells dropping below 30 are disclosed.
- **Worst-5% tail-share:** if a cell has 0 negative-direction mass (for MAE, MAE ≥ 0 always, so the
  "tail" is the largest excursions; the share is over total adverse contribution) the share is a finite
  value in `[0,1]`, never NaN/inf; an empty/degenerate cell reports the share as undefined → excluded.
- **Reference band:** fixed `{0.5, 1.0}` ATR-units; median MFE/MAE reported as multiples of each; never a
  denominator, never subtracted.
- **Disclosed secondaries (never the binding availability readout):** mean/trimmed-mean/tail MFE & MAE; the
  median `MFE − MAE`; the DATA_CENSORED and warmup fractions; the `/STRONG-HA` and MAD arms; the ZigZag arms.

## Data Requirements

Per cell (instrument × domain), TRAIN slice only: lazy `pl.scan_parquet`; read total row count from
metadata; `analysis_rows = int(total_rows*0.7)`, `train_rows = int(analysis_rows*0.7)`; collect only the
first `train_rows` file-order 1-minute rows (F01 prefix; never sort/collect the full file, never read TEST
or holdout); assert chronological; `train_end_ts` = last `CloseTime`. Aggregate each member domain (5m
strict; others `min_coverage=0.90`); fence domain bars to `CloseTime ≤ train_end_ts`; generate HA candles;
run `xen.zigzag.generate_zigzag(bars, atr_period=14, atr_mult=1.0)` → confirmed moves + `confirm_idx`
(disclosed contrast); run `ma_segment_moves` (MA(20,50) on real close) → MA segments + `confirm_idx`;
detect haramis on HA candles aligned by `CloseTime`; build the live in-progress state + `/STRONG-STAT`
(`/STRONG-HA` disclosed) conditioning (`xen.expectancy`); for each qualifying harami resolve the MA
end-of-M_b window (`availability.end_of_mb_window` on MA `confirm_idx`) and compute ATR-normalised lifetime
MFE/MAE (`lifetime_excursions_atr`); bootstrap per-cell median MFE/MAE (fixed seed) + the P4
mean/trim/tail; build the matched-random-on-MA null (RM_MA) by matched-count in-regime selection through
the identical MA lifetime window (`matched_random_arm` with MA `state_all`/`confirm_idx`) and the
`A_MA − RM_MA` contrast; build the disclosed ZigZag arms (A_ZZ / RM_ZZ); reconcile A_MA / A_ZZ to EXP-055;
second full pass for determinism. `tqdm` over the 99-cell grid (per-instrument worker); **bounded per-cell
memory** (release per-cell arrays after summarisation; the excursion loop is bounded by the MA-segment
window). Outputs (`results/`): `per_cell_availability.parquet` (per cell × arm: median/CI MFE, median/CI
MAE, MFE−MAE, mean/trim/tail MFE & MAE, ×0.5/×1.0 reference multiples, n_qualifying, n_censored,
`MOVE_AVAILABLE`, `SIGNAL_ATTRIBUTABLE`, A_MA−RM_MA contrasts); `availability_map.csv` (binding A_MA +
MOVE_AVAILABLE + SIGNAL_ATTRIBUTABLE + P11/non-4h tally); `availability_secondary.csv` (`/STRONG-HA`, MAD,
ZigZag arms, censoring); `mae_tail_decomposition.csv` (P4 MAE mean/trim/tail per cell — the L3 input);
`reconciliation.csv` (A_MA↔EXP-055 `ma_seg`, A_ZZ↔EXP-055 binding: median MFE/MAE + count exact);
`population_reconciliation.csv` (vs EXP-053/055 conditioned population); `composition_readout.json` (P11 +
non-4h, AVAILABILITY_* fork, SIGNAL_ATTRIBUTABLE tally, reference-line multiples → G-015 input);
`run_metadata.json` (seed, frozen constants, reference band, EXP-055/EXP-061 source paths/hashes,
parallelism note, holdout fence). Four bounded plots from the collected per-cell summaries (no reloads).

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

Fork the prior EXP-062 `code/run_experiment.py` (it already computes the native `A_MA`/`RM_MA`, the
ZigZag `A_ZZ`/`RM_ZZ`, and reconciles to EXP-055). `availability.py` is unchanged. Make three changes:
**(1)** relabel the existing MA arm as **native `A_MA_nat`** (it conditions on `ma["stat"]["retained_p75"]`
— confirmed) and add the **hybrid `A_MA_hyb`** — `_ctx_arm` already accepts an explicit conditioning
mask, so call it with the **MA context** but the **ZigZag mask** `zz["stat"]["retained_p75"]` (verify
`ma["entry_idx"]` and `zz["entry_idx"]` are the identical harami-entry array — both detect on the same HA
candles aligned by `CloseTime`; if a context stores entries differently, index the ZigZag mask onto the
MA entry order by `CloseTime` before applying). **(2)** add the hybrid null **`RM_MA_hyb`** (the generic
`matched_random_arm` with the MA `state_all`/`confirm_idx`, matched to `A_MA_hyb`'s count, excluding the
hybrid signal entries, on **new dedicated RNG purposes** distinct from `RM_MA_nat`/`RM_ZZ`) plus the
**`A_MA_hyb − RM_MA_hyb`** median-MFE/MAE contrast; keep the native and ZigZag contrasts. **(3)** emit
**per-object** `MOVE_AVAILABLE` / `SIGNAL_ATTRIBUTABLE` / AVAILABILITY_* / P11 (non-4h) readouts (never
pooled; add an `object` tag to every per-cell row), and set reconciliation to the corrected roles:
native `A_MA_nat` ↔ EXP-055 `ma_seg` (median MFE/MAE + count 1e-9); `A_ZZ` ↔ EXP-055 binding ZigZag;
hybrid `A_MA_hyb` has **no outcome anchor** (its ZigZag conditioning mask verified transitively via the
A_ZZ population digest/count). Keep the MAE mean/trim/tail P4 diagnostic per object. Retain EXP-062's
per-instrument `ProcessPoolExecutor` parallelism with native-thread pinning and fixed-order reassembly
(byte-identical output for any `--workers`); fixed per-cell seed (P3); `tqdm`; bounded memory; **do not
adjudicate G-015**. The existing native/ZigZag arms must stay byte-identical (use new RNG purposes for
the hybrid arms only) so their EXP-055 reconciliation still holds.
