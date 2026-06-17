# Experiment: EXP-063 — MA(20,50)-Substrate Adverse Geometry & the Mean Investigation (Conditioned HA Harami; Benchmark 1:1, `/ADV-EXTREME-rr1`, `/ADV-NONE`; **Dual Conditioning Object: Hybrid and Native**, Phase 015 Lead L3)

> **Re-run under `D0-amendment-001-dual-parallel-substrate.md` (2026-06-17).** The prior EXP-063
> measured a single MA arm labelled *hybrid* but actually conditioned on MA-segment `/STRONG-STAT` —
> the **native** object. The genuine **hybrid** object (ZigZag-`/STRONG-STAT`-conditioned × MA-segment
> adverse geometry) was never computed. This re-run emits the full 4-variant adverse axis **for both
> conditioning objects individually** (separate variant arms, separate matched-random nulls, separate
> per-cell viability, separate mean-investigation decomposition, separate P11 composition, separate
> AVAILABILITY/EVIDENCE fork — never pooled) and **supersedes the prior EXP-063 result in place**.

> **Mandatory-reading precondition (Phase 015, binding — inherited from 014-B).**
> `../../docs/experiments-docs/checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/014-A-conditioning-gap-and-validation-lessons.md`
> was read in full before this scope was written. The four mandatory rules are honoured, recorded so
> Stage 4 can check:
> - **(a) conditioning** — honoured, **and now disambiguated** (Amendment 001). Two live
>   `/STRONG-STAT`-conditioned HA-harami objects are measured individually over the **same** MA(20,50)
>   adverse/favourable/cap geometry: **hybrid** (filter on the in-progress confirmed *ZigZag* move —
>   entry population byte-identical to EXP-053/060/061's hybrid `H0`; the genuinely-new object) and
>   **native** (filter recomputed on the in-progress confirmed *MA segment* — the population the prior
>   EXP-063 actually used; reconciles to EXP-061's native `M0` / EXP-060B `BENCH-MA`). `/STRONG-STAT`
>   (P7) is binding in each; the raw harami and unconditioned ZigZag substrate are not the object. Each
>   object's matched-random-on-MA controls are deliberate **nulls** (P5), not signal claims. The two
>   objects are never pooled.
> - **(b) harami-anchor** — honoured. Entry is the **harami confirmation-bar real close** `C` in both
>   objects, the family's claimed lead point — *not* the ZigZag or MA trend-change confirmation. The
>   MA(20,50) substrate supplies only the outcome geometry (`rd` / `M_sofar` / favourable target / cap)
>   and, for `/ADV-EXTREME`, the **last confirmed MA segment's running extreme** (P7 Q5); none of these
>   moves the anchor. The matched-random controls intentionally break the anchor (that is what makes
>   them nulls).
> - **(c) position-in-move descriptive-only / never a live filter** — honoured. EXP-050's position metric
>   is not used. The `/ADV-EXTREME` reference extreme is the **causal running extreme of the in-progress
>   (faded) MA segment as-of entry** (over real bars `[ma_start_idx+1 … entry_idx]`) — a quantity known at
>   the entry timestamp from completed real bars — never an unconfirmed crossover or future bar. Every
>   exit acts on a bar known forward-in-time.
> - **(d) expectancy / not first-hit `r`** — honoured. The **binding** endpoint is the Phase 015 **median**
>   gross per-event expectancy (P3/P14), computed **per object individually**. The **mean** (raw + 10%
>   trimmed + worst-5% tail-share, each CI'd) is the **decisive object of this read** — the P4 diagnostic
>   co-primary — *but it is never a blind disqualifier* (P4 closure-on-mean rule). First-hit `r` disclosed
>   for single-leg arms only.
> EXP-063 does **not** treat the EXP-049 `r≈0.50` null or the EXP-050 front-loading as evidence against the
> family — those measured the *unconditioned* object on the ZigZag substrate.

**Phase / checkpoint:** `2026-06-17-015-ma-substrate-conditioned-harami-full-surface` (Phase 015; **G0 PASS 2026-06-17**).
**Family / candidate:** `CF-HA-HARAMI-001` (`REGISTERED`, OPEN) · Phase 015 lead **L3** ·
`CF-HA-HARAMI-001/HYP-016` — EXP-063 (Phase 015 batch, `multiplicity-registry.md`).
**Registry precondition (satisfied):** `CF-HA-HARAMI-001/MA-SUBSTRATE` and **both** its conditioning modes
(`hybrid`, `native`) are **REGISTERED** and parallel first-class per `D0-amendment-001` (Phase 015 batch,
2026-06-17, G0 PASS); HYP-016/EXP-063 is the listed plan (`EXP-057`-analog + the §4 mean diagnostic, L3),
now emitting both objects individually. The adverse-target variants `CF-HA-HARAMI-001/ADV-EXTREME` and
`CF-HA-HARAMI-001/ADV-NONE` are already registered (Phase 014-B batch); Phase 015 records their
**MA-substrate reuse** on both objects (P8/P11). The benchmark 3-barrier geometry and the matched-random
baseline pre-exist (Phase 014/014-B + EXP-061 reuse). **No new countable item is introduced here.**
**Surface role:** the Phase 015 **lead L3** — the EXP-057 adverse-geometry analog *on the MA substrate*, **plus the
decisive mean investigation** (design §4, D0 P4), now on **both** conditioning objects. EXP-060B found the
MA-substrate edge is **median-only**: M3 gross mean ≈0/negative, skew gap 1.20 ATR driven by the **uncapped
`/ADV-NONE` downside**. EXP-061 (L1) showed the **native** object generalises to benchmark geometry (8 cells)
while the **hybrid** object does not (1 cell) — so the mean investigation must be read **per object**. EXP-062
(L2) sized the adverse tail per object (`mae_tail_decomposition.csv`). EXP-063 is the **"why is the mean
negative, and does bounding the downside fix it" read, per object**: bounded-downside adverse models (benchmark
1:1, `/ADV-EXTREME-rr1`) vs the unbounded `/ADV-NONE` reference, with the full §4 tail-share / trimmed-mean /
recovery decomposition. Output feeds the single terminal **G-015** after the full slate; **no closure or
candidate registration here** (P9 no-early-closure).
**Governing design / D0:** `design.md` (§3 objective; **§4 mean diagnostic posture**; §5 slate L3; §7 G-015
criteria, judged per object) + `D0-predeclarations.md` (P1 substrate; **P2 both objects parallel/individual**;
P3 median binding + fixed seed; **P4 mean diagnostic + closure rule**; **P5 matched-null per object every read**;
P6 non-4h composition; **P7 bounded-downside set + `/ADV-EXTREME-rr1` causal construction**; P8 OAT reuse; P10
power; **P12 reconciliation roles — native↔EXP-061 `M0`/EXP-060B 1e-9, hybrid anchorless**) +
`D0-amendment-001-dual-parallel-substrate.md`. Inherits 014-B P14/P15/P16 and the EXP-057 (HYP-010)
adverse-target method.
**Reuses (expected 0 new `xen/` modules):** `xen.adverse_targets` **wholesale** (substrate-generic:
`faded_move_extreme`, `adverse_extreme_raw`, `adverse_extreme_rr1`, `adverse_none_sentinel`,
`barriers_with_adverse`); the EXP-061 **dual-object** MA pipeline (`ma_segment_moves`, `_ma_context`,
`_zz_context`, `bench_signal_arm` with its `cond_mask` override, `matched_random_arm`, `resolve_arm`) and its
P4 mean-diagnostic functions (`bootstrap_stat_distribution`, `_trimmed_mean`, `_tail_share_worst5`);
`xen.expectancy.*` (`live_in_progress_state`, `live_strong_stat`, `adaptive_time_caps_by_epoch`,
`benchmark_barriers`, `resolve_path_ordered`, `realised_returns`, `qualifying_mask`,
`bootstrap_median_distribution`, `median_ci`, `contrast_ci`); `xen.favourable_targets.paired_median_contrast_ci`
(the variant−benchmark paired contrast); ZigZag (`xen.zigzag`), HA (`xen.heiken_ashi_generator`), harami
(`xen.ha_harami`), `/STRONG-HA` (`xen.strong_move`). **EXP-061's dual-object `code/run_experiment.py` is the
fork base** (it already computes hybrid `H0` and native `M0` BENCH arms, the `_zz_context`/`_ma_context`, the
per-object matched-random controls `RH0`/`RM0`, the corrected reconciliation roles, and the P4 mean/trim/tail
diagnostic — EXP-063 generalises its single BENCH geometry to the 4-variant adverse axis, per object).

## Slot & ledger accounting (binding)

- **0 candidate slots, 0 TEST reads.** Characterization/diagnostic per the Phase 015 D0 (P11). No countable item is
  introduced: `MA-SUBSTRATE` (+ both `hybrid`/`native` modes) is registered at G0; the `/ADV-EXTREME` and
  `/ADV-NONE` branches and the matched-random nulls pre-exist (Phase 014-B / P13). A slot is consumed only at a
  future G-015 PROCEED.
- **No TEST stratum is read.** All work on the **TRAIN** slice (first 70% of the first-70% analysis set; F01
  file-order prefix; identical fence to EXP-049/053–062). Hybrid population byte-identical to EXP-053/060/061;
  native population byte-identical to EXP-060B/061 `M0`; no new stratum opened; `test-read-ledger.md` requires no
  entry; the global-holdout seal carries forward. No HA-harami TEST stratum has ever been read.
- All work **gross**; detection on HA candles; **all outcome metrics on real-price OHLC** (`RealOpen/High/Low/Close`),
  never HA prices; MA(20,50) computed on **real close** (identical to EXP-060/061 `ma_segment_moves`).

---

## Hypothesis

On the conditioned `/STRONG-STAT` HA harami, **for each conditioning object individually** (hybrid and native),
99-cell TRAIN grid, MA(20,50) substrate, entered at the harami confirmation-bar real close `C` with the favourable
target held at the benchmark `0.50·M_sofar` and the MA-defined adaptive cap held fixed (OAT on the **adverse leg
only**):

1. **(median lever)** At least one **bounded-downside** adverse variant (benchmark **1:1** or `/ADV-EXTREME-rr1`)
   is **median-viable** per cell (one-sided 95% regime-clustered moving-block-bootstrap CI_low > 0, ≥ 30 qualifying
   events), **beats its own matched-random-on-MA null** (variant `− RM`-variant contrast CI_low > 0), and **clears
   P11** with the P6 non-4h breadth (≥ 5 cells / ≥ 3 instruments / ≥ 3 cells outside 4h); **and**
2. **(mean recovery — the decisive read, P4)** replacing the unbounded `/ADV-NONE` reference with a bounded-downside
   model **truncates the adverse tail and moves the raw mean upward** — quantified by (a) the per-variant raw mean +
   10% trimmed mean (each CI'd), (b) the worst-5% tail-share, and (c) the **bounded-downside recovery contrast**
   `mean(bounded) − mean(/ADV-NONE)` (CI'd) per cell and composed.

The two objects are judged **individually, never pooled** (P2); the phase-level reading of this lever is the
**stronger object's** outcome (consistent with EXP-061: native is the object that expresses the edge), with the
other object's result documented in parallel.

**Falsifiable (median lever), per object:** if **no** bounded-downside variant clears P11 viability **and** beats
its RM-on-MA null in the quorum, that object's MA-substrate median edge does not survive a stop-bearing geometry —
it requires the `/ADV-NONE` asymmetry. **Falsifiable (mean), per object:** if the bounded-downside variants' raw
means are **also negative**, their 10% trimmed means are **also negative**, and the recovery contrast does **not**
move the mean materially positive, then the negative mean is **structural and geometry-irrecoverable** on the
bounded-downside axis for that object (the positive demonstration the P4 closure rule requires). **No outcome closes
the family inside Phase 015** — the surface (S1–S3, both objects; combined champions EXP-067 hybrid / EXP-068
native) runs regardless (no early-closure, P9); routing is the single terminal G-015.

**Readiness precondition (P12, gates interpretation):** the **native** `M-BENCH` (1:1) arm reconciles to
**EXP-061 native `M0` / EXP-060B `BENCH-MA`** (per-cell median + qualifying count, `RECON_TOL = 1e-9`); the
**hybrid** `H-BENCH` arm reconciles to **EXP-061 hybrid `H0`** (per-cell median + qualifying count, 1e-9 — its
internal-lineage anchor) and its ZigZag-`/STRONG-STAT` conditioning population reconciles to EXP-053's set
(transitively via the disclosed `Z-BENCH` ZigZag arm); the `/ADV-NONE`-MA arms' adverse/tail behaviour is
consistent with **EXP-062's per-object `mae_tail_decomposition.csv`** (the L2→L3 hand-off, disclosed cross-check,
per object); the conditioned populations reconcile to **EXP-053/060/061** exactly. A reconciliation / causality /
determinism / invariant failure is a **SUBSTRATE/METHOD_DEFECT** — fixed before any read is interpreted.

## Question

On the MA(20,50)-substrate conditioned harami, **for each object (hybrid, native)**, does changing only the
**adverse target** — from the benchmark 1:1 model to the extreme-anchored ≥1:1 stop (`/ADV-EXTREME-rr1`, the
bounded-downside candidate) or to no stop at all (`/ADV-NONE`, the unbounded skew source under study) — (i) improve
the gross per-event **median** expectancy and beat matched-random-on-MA, and (ii) **explain and/or repair the
EXP-060B negative mean**: is the `/ADV-NONE` mean negativity a thin, truncatable adverse tail (⇒
bounded-downside-recoverable) or a broadly negative distribution (⇒ structural)? This is the decisive "why is the
mean negative, and does bounding fix it" read (design §4), now resolved on the object that actually expresses the
edge (native) **and** on the genuinely-new hybrid object, individually.

---

## Scope Boundaries

### Data Views

- **Real domain bars** (5m strict; 15m/30m/1h/2h/4h via `xen.bar_aggregator.aggregate_ohlc`, `min_coverage=0.90` —
  identical to EXP-048/049/053–062/VAL-004) for the MA(20,50)-crossover substrate (`ma_segment_moves` on real
  close), the ZigZag substrate (`atr_mult=1.0`, for the hybrid conditioning mask + the disclosed `Z-BENCH`
  contrast), confirmed moves/segments, `/STRONG-STAT` magnitudes, the in-progress MA-segment extreme
  (`/ADV-EXTREME`), benchmark favourable/adverse levels, the adaptive cap, P15 fills, ATR normalisation, and
  **all** outcome metrics.
- **Heiken Ashi candles** (`xen.heiken_ashi_generator`) for **harami detection only** (frozen EXP-048 detector)
  and the disclosed `/STRONG-HA` arm. **No HA price enters any metric.**

### Event population (two conditioning objects, measured individually over the same MA adverse geometry)

Both objects share the **same** frozen HA-harami detection, the **same** MA(20,50) outcome geometry
(`rd` / `M_sofar` / benchmark favourable / adaptive cap / `/ADV-EXTREME` MA-segment extreme), and the **same** real
bars; they differ **only** in the `/STRONG-STAT` conditioning filter (P2):

- **Hybrid (`H-*`).** Qualifies iff the harami passes `/STRONG-STAT` p75 on the **in-progress confirmed ZigZag
  move** magnitude-so-far (hybrid mode). The conditioning mask is **byte-identical to EXP-053/060/061's hybrid `H0`
  set** (the same `live_in_progress_state` / `live_strong_stat` on the ZigZag move, applied through the MA context
  via the `bench_signal_arm` `cond_mask` override). MA supplies only the geometry. **This is the genuinely-new
  object** for the adverse axis (a ZigZag-conditioned adverse surface over MA geometry was never computed before).
  Its internal-lineage anchor is **EXP-061 `H0`** (the `H-BENCH` variant reproduces it); it has **no EXP-060B/057
  back-reconciliation anchor**.
- **Native (`M-*`).** Qualifies iff the harami passes `/STRONG-STAT` p75 on the **in-progress confirmed MA
  segment** magnitude-so-far (recomputed on MA segments). **Population byte-identical to EXP-061 native `M0` and
  EXP-060B `BENCH-MA`**; the `M-BENCH` variant **reconciles to them (1e-9)** — the object the prior EXP-063 actually
  measured.

Entry anchor is the harami close `C` in both. `/STRONG-HA` (P8: run of `X=3` large-body HA bars, no opposing wick)
is a **disclosed secondary** arm through the identical pipeline (deferred for runtime; see Exclusions). Each
object's matched-random-on-MA nulls draw **non-harami** in-MA-regime timestamps, **matched-count to that object's
qualifying count per variant**, on **independent dedicated RNG streams** distinct from the other object's.

### Adverse-target variants (predeclared OAT sweep on the adverse leg; MA substrate; **per object**)

For every variant the **favourable** target is the benchmark `fav = C + rd·0.50·M_sofar` (P2,
`xen.expectancy.benchmark_barriers` with MA-defined `M_sofar`) and the **third barrier** is the benchmark MA-defined
adaptive cap (P4: `N = max(6, round(1.5 × median duration of trailing 20 confirmed MA segments))`,
`xen.expectancy.adaptive_time_caps_by_epoch` on the MA `confirm_epoch`/`confirm_idx`). Variants differ **only** in
the adverse level `adv`. Fills are **P15**. All levels on **real prices**. **Each variant is built and resolved
twice — once on the hybrid population, once on the native population — and reported individually.**

| # | Variant (per object) | Adverse model | Binding? | Role |
|---|----------------------|---------------|----------|------|
| **{M,H}-BENCH** | benchmark 1:1 | `adv = C − rd·0.50·M_sofar` (`adv_dist = fav_dist`) | **BINDING** (bounded-downside axis, P7) | Reference; native `M-BENCH` reconciles to **EXP-061 `M0` / EXP-060B `BENCH-MA`** (1e-9); hybrid `H-BENCH` reconciles to **EXP-061 `H0`** (1e-9). |
| **{M,H}-RR1** | `/ADV-EXTREME-rr1` | extreme-anchored, widened to ≥ 1:1 (`adv_dist = max(adv_dist_raw, fav_dist)`) | **BINDING** (bounded-downside axis, P7) | The bounded-downside candidate; isolates extreme-anchoring from stop-width. |
| **{M,H}-NONE** | `/ADV-NONE` | unreachable stop (∓∞ by `rd`) — only FAV / TIMECAP resolve | **DISCLOSED reference (not a viability candidate)** | The EXP-060B champion adverse model — the **skew source under study**; the bounded-downside recovery baseline. |
| **{M,H}-RAW** | `/ADV-EXTREME-raw` | buffered faded extreme, R:R free (typically sub-1:1) | **DISCLOSED secondary** | The tight-stop contrast (faithful to EXP-057); separates *where* the stop sits from *how wide*. |

- **`/ADV-EXTREME` reference extreme on MA (P7 Q5), per object.** The faded-move running extreme is the extreme of
  the **in-progress (faded) MA segment** as-of entry: over real bars `[ma_start_idx+1 … entry_idx]` inclusive, where
  `ma_start_idx` is the bar of the in-progress MA segment's start crossover (the **last confirmed** MA crossover
  at/before entry — `start_epoch` of `xen.expectancy.live_in_progress_state` built on the MA segment arrays) and
  `entry_idx` is the harami bar. `min(Low)` for a long fade (`rd=+1`), `max(High)` for a short fade (`rd=−1`).
  Computed by `xen.adverse_targets.faded_move_extreme` (substrate-generic; the MA start index is the only change vs
  EXP-057). **The MA in-progress state — hence `rd`, `M_sofar`, `ma_start_idx`, the fav level, and the cap — is the
  same for both objects** (both score on MA geometry); the objects differ only in *which haramis qualify*. Buffer
  `0.25·ATR_entry`; raw degeneracy floor `adv_dist ≥ 0.10·ATR_entry` (raw form only); rr1 widens to
  `max(adv_dist_raw, fav_dist)`. The extreme is the **last confirmed MA segment's** extreme, no look-ahead (P7 Q5).
- **Validity / exclusions (per variant per object, disclosed counts, never silent clamps):** an event is *valid*
  iff `fav_dist > 0` (always true for the conditioned population, `M_sofar > 0`) and — for stopped variants — a
  finite adverse level with `adv_dist > 0` (and `adv_dist ≥ ADV_FLOOR` for `{M,H}-RAW`). Warmup (no in-progress MA
  span / non-finite `ATR_entry`), degeneracy (RAW floor breach), and `DATA_CENSORED` (window truncated by the TRAIN
  edge) events are **excluded-with-record** per cell per variant per object. `{M,H}-NONE` has no stop, so only
  warmup/censoring exclusions apply; they deliberately admit large negative TIMECAP returns — that asymmetry is the
  object of measurement.
- **No post-result variant selection.** Every variant on every object is reported and composed by P11; routing is
  the single G-015.

### Matched-random-on-MA null, per variant, **per object** (P5)

For each variant **of each object** a **matched-count random in-regime** control (native: RM-BENCH/RM-RR1/RM-NONE/
RM-RAW; hybrid: RH-BENCH/RH-RR1/RH-NONE/RH-RAW) draws non-harami in-regime timestamps (same cell / direction, valid
live MA state, positive `m_sofar`, finite positive ATR, not-in-warmup, **excluding that object's conditioned-harami
entries**) matched-count to that object's qualifying harami count for the variant, and resolves them through the
**identical** per-variant adverse + favourable + cap + P15 pipeline (the `matched_random_arm` construction, generic
over the adverse builder). Signal-attribution requires the variant's median to **beat its own object's RM**
(independent `variant − RM` contrast CI_low > 0, `xen.expectancy.contrast_ci` — the matched-random events are
disjoint from the haramis, so the contrast is independence-assuming, per EXP-060B I2). The hybrid and native nulls
draw from the **same MA in-regime pool** but are matched to **different counts** and exclude **different signal
entries**, on **disjoint dedicated RNG streams**; the two objects' contrasts are **never pooled**.

### The mean investigation (P4 — the decisive content; design §4), **per object**

Alongside the **median** (binding) per cell per variant per object, the read emits and composes the full §4
decomposition **separately for each object**:

- **Raw mean** (regime-clustered moving-block bootstrap CI, fixed per-cell seed) — `bootstrap_stat_distribution(…, "mean")`.
- **10% symmetric trimmed mean** (bootstrap CI) — `bootstrap_stat_distribution(…, "trim")`. If the trimmed mean
  crosses positive while the raw mean does not, the negativity is **outlier-driven** (bound the downside); if the
  trimmed mean is **also** negative, it is **structural**.
- **Worst-5% tail-share** — `_tail_share_worst5`: the fraction of total negative return contributed by the worst 5%
  of events. A thin, top-heavy tail (large share) ⇒ removable; a broadly negative distribution (small share, many
  negatives) ⇒ structural.
- **Bounded-downside recovery contrast (the mechanistic "can we fix it" read):** per cell per object, the **mean**
  contrasts `mean(*-BENCH) − mean(*-NONE)` and `mean(*-RR1) − mean(*-NONE)` (independent-bootstrap CI via
  `contrast_ci` on the stored per-variant mean distributions — the variants resolve disjoint *exits* on the same
  entries but the bounded vs unbounded return populations differ only by the stop, so the contrast is reported as
  the recovery delta with its CI). Does bounding the downside move the raw mean materially upward / positive?
- **Concentration:** the per-cell raw/trimmed mean and tail-share are tabulated by **instrument / domain / regime**,
  with the **low-n 4h** cells flagged — to confront the EXP-060B 8/14-low-n-4h lead concentration (is the negative
  mean concentrated, or pervasive?), **per object**.

**Closure-on-mean rule (binding, P4).** A median-viable / raw-mean-negative result **does not close the family.**
Closure-on-mean is well-supported only on a **positive demonstration of structural irrecoverability on the
expressing object**: the trimmed mean is **also** negative **AND** the negativity **persists under the
bounded-downside models** (the recovery contrast does not lift it) **AND** it is **not removable-tail-driven** (the
worst-5% tail-share is not dominant). A bare raw-mean-CI miss never closes. EXP-063 **emits** this readout, per
object; the closure adjudication is G-015.

### Favourable target, third barrier, fills (benchmark; held fixed across variants and objects)

- **Favourable (P2, benchmark 50%):** `fav = C + rd·0.50·M_sofar` for every variant (MA-defined `M_sofar`).
- **Third barrier (P4, benchmark MA-defined adaptive cap):** `N = max(6, round(1.5 × median(duration of the trailing
  20 MA segments confirmed strictly before the harami)))`; `< 5` trailing durations → warmup-excluded
  (`adaptive_time_caps_by_epoch`).
- **Fill model (P15, method standard):** path-ordered intrabar fills — bullish bar `Open→Low→High→Close`, bearish
  `Open→High→Low→Close`; TIMECAP at the cap bar real close; `DATA_CENSORED` excluded (`resolve_path_ordered`).
  Documented approximation; disclosed in every result.

### Parameters (all frozen / predeclared; no tuning)

ZigZag Wilder ATR(14), `ATR_MULT = 1.0` (P1; hybrid conditioning mask + disclosed `Z-BENCH` contrast); **MA(20,50)
on real close (fixed; P1 — not swept)**; `/STRONG-STAT` trailing-20 ≥ p75 (P7; MAD disclosed/deferred); `/STRONG-HA`
`X=3` (P8; deferred); benchmark favourable `X = 50%` of `M_sofar` (P2); benchmark adverse 1:1 (P3 reference
variant); MA-defined time cap `(k=1.5, window=20, floor=6, statistic=median, min_moves=5)` (P4); `/ADV-EXTREME`
buffer `= 0.25·ATR_entry`, degeneracy floor `ADV_FLOOR = 0.10·ATR_entry` (raw only), `/ADV-NONE` sentinel `∓∞` by
`rd` (all frozen EXP-057 constants, reused unchanged); ATR-normalisation divisor = Wilder ATR(14) at the harami
entry bar (P14); mean trim fraction **10%**, tail-share **worst-5%** (P4 ratified); bootstrap
`b = max(1, round(m^(1/3)))`, `N_BOOT = 10_000`, **fixed per-cell seed (P3)** —
`np.random.default_rng([BASE_SEED, cell_index, purpose])` with dedicated purposes per object/variant/statistic so
the native `M-BENCH` median path stays byte-identical to EXP-061 `M0` and the hybrid `H-BENCH` path stays
byte-identical to EXP-061 `H0`. No grid swept; no parameter tuned against outcomes.

### Instruments / cells / time range

The **99-cell EXP-049/053–062 member grid** (17 instruments × {5m,15m,30m,1h,2h,4h} − 3 COVERAGE_EXCLUDED: US500-4h,
JP225-2h, JP225-4h). Per-cell first, then **P11** with the **P6 non-4h rule** (≥ 5 cells over ≥ 3 instruments, with
≥ 3 of the qualifying cells outside 4h) for any family-level claim, **per object**. **TRAIN only** = first 70% of
the first-70% analysis set (F01 file-order prefix; identical fence to EXP-049/053–062). TEST and the final-30%
global holdout are **not** read. Forward windows clipped to `train_end_ts`; truncated → `DATA_CENSORED`. DE30
carries the truncated-coverage disclosure (broker history ends 2026-01-16).

### Look-ahead / causality discipline (binding)

- ZigZag and MA(20,50) segmentation are future information until confirmed. The signal (harami + `/STRONG-STAT`, on
  the ZigZag move for hybrid / the MA segment for native), `M_sofar`, the favourable level, the cap, and the
  **`/ADV-EXTREME` in-progress-MA-segment extreme** use **only** confirmed prior moves/segments and **real bars at or
  before the entry bar** (via `live_in_progress_state`). The faded-extreme span `[ma_start_idx+1 … entry_idx]` is all
  `CloseTime ≤ C`'s bar (the MA start crossover is confirmed at/before entry); it is a causal running extreme, not
  the EXP-050 descriptive position metric and not an unconfirmed crossover. MA(20,50) `_sma` is trailing; MA segments
  are bounded by crossovers confirmed before entry. Matched-random entries are constructed causally with the
  identical pre-entry-only state, per object.
- Every exit is forward (P15 intrabar touch / stop / cap-bar real close); no exit references an unconfirmed crossover
  or future bar. Forward scan reads only `[entry_idx+1, min(entry_idx+N, last_train_idx)]`, `CloseTime ≤ train_end_ts`.
  Ordering/alignment by `CloseTime`, never bar index across views.

### Real-price outcome discipline

Harami detected on HA candles; `M_sofar`, the in-progress-MA-segment extreme, ATR normalisation, fav/adv levels,
fills, expectancy, mean/trim/tail, `r`, win rate, and censoring all on real domain-bar OHLC. **No HA price in any
metric.**

### Exclusions

- No costs (gross only).
- **Adverse-target geometry + mean diagnostic only, on both objects.** No `/VPTARGET`/`/MAGTARGET` (S1/EXP-064 —
  favourable held at benchmark 50%), no `/THIRD-EVENT`/`/THIRD-TIME` (S2/EXP-065), no `/EXIT-PARTIAL`/`/EXIT-TRAIL-STRUCT`
  (S3/EXP-066), no combined system (S4/EXP-067 hybrid, EXP-068 native); **no MA-parameter sweep** (MA(20,50) fixed);
  **no** `/BARCFG`/`/CONFIRM` overlay; **no** position-in-move filter; **no** V2A partial exit (the V2A×NONE champion
  is S3/S4 — EXP-063 holds the favourable leg at benchmark single-target, OAT on adverse).
- No parameter tuning; **no post-result variant or object selection** (all predeclared variants on both objects
  reported); no gate adjudication (single G-015 after the full slate — EXP-063 emits a characterization readout
  only). No TEST or holdout contact; no candidate slot; no TEST read.

## Success / Failure Criteria (per object, never pooled)

All **gross**, per-cell first, P11-composed (≥ 5 cells over ≥ 3 instruments, **≥ 3 outside 4h**); per-cell viable
iff **CI_low > 0** (one-sided 95% regime-clustered moving-block bootstrap, fixed seed) **AND ≥ 30 qualifying events**.
Binding endpoint = **median** per-event gross expectancy (P3/P14); the **mean** (raw + 10% trimmed + worst-5%
tail-share + the bounded-downside recovery contrast) is the P4 **decisive diagnostic** (never a blind disqualifier,
P4 closure rule). The fork is computed **separately for each object**; the phase-level reading is the stronger
object's, the other documented in parallel.

- **EVIDENCE_FOR (bounded-downside lever helps + mean recoverable):** ≥ 1 bounded-downside variant (`*-BENCH` or
  `*-RR1`) is median-viable, beats its RM-on-MA null, and clears P11 with non-4h breadth, **and** the §4
  decomposition shows the mean is materially lifted by bounding (recovery contrast CI_low > 0 in the quorum, and/or
  the bounded-variant raw or trimmed mean clears 0 where `*-NONE`'s does not). Recorded **per object**: a
  bounded-downside MA geometry both preserves the median edge and repairs the skew — the strongest input toward a
  G-015 PROCEED/MEAN_RECOVERABLE for that object.
- **MEDIAN_ONLY (median survives, mean does not recover):** a bounded-downside variant is median-viable and beats
  RM, but its raw mean stays negative, its trimmed mean stays negative, and the recovery contrast does not lift the
  mean materially — the negativity is structural on the bounded-downside axis for that object. Recorded as the
  positive structural-irrecoverability demonstration the P4 closure rule needs (feeds G-015; never a closure here).
- **EVIDENCE_AGAINST (adverse geometry not a median lever):** no bounded-downside variant both clears P11 viability
  and beats its RM null for that object. Recorded; that object's MA median edge may require the `/ADV-NONE`
  asymmetry. **Family stays OPEN** — the surface runs regardless (P9).
- **INCONCLUSIVE (power-limited):** fewer than the P11 quorum of cells reach ≥ 30 qualifying events on the
  variants/contrasts of interest for that object (degeneracy/warmup/censoring deplete counts; the hybrid object is
  expected to be the more power-limited per EXP-061); no correctness failure. Disclosed; never defaulted.
- **SUBSTRATE/METHOD_DEFECT:** any reconciliation, determinism, causality, or invariant failure → fix before
  reporting. Invariant checks: (i) **`M-BENCH` reproduces EXP-061 `M0` / EXP-060B `BENCH-MA`** and **`H-BENCH`
  reproduces EXP-061 `H0`** per-cell median + qualifying count to `1e-9`; (ii) **`*-RAW` `adv_dist` ≤ `*-RR1`
  `adv_dist`** event-wise (rr1 widens), each object; (iii) **`*-NONE` produces 0 ADV outcomes** (`adv_hit` never
  fires), each object; (iv) population reconciliation: hybrid ↔ EXP-053/060/061 `H0`, native ↔ EXP-060B/061 `M0`,
  exact for each signal arm; (v) **matched-count holds per object** — each RM/RH draw target equals its object's
  variant qualifying count; (vi) every exit price is a real-bar P15 fill with `CloseTime ≤ train_end_ts`; (vii) the
  **per-object `*-NONE` MAE/tail behaviour is consistent with EXP-062's per-object `mae_tail_decomposition.csv`**
  (disclosed L2→L3 cross-check, not a hard gate).

Deliverable label: **MA_ADVERSE_GEOMETRY_AND_MEAN_CHARACTERISED (dual-object)**, carrying — **per object,
individually** — the per-variant per-cell + P11 median readout (bounded-downside binding, `*-NONE`/`*-RAW`
disclosed); each variant's RM-on-MA signal-attribution; the **full §4 mean decomposition** (raw mean, 10% trimmed
mean, worst-5% tail-share, the bounded-downside recovery contrast, the instrument/domain/regime concentration with
low-n-4h flags) and the MEDIAN_ONLY vs EVIDENCE_FOR vs structural-irrecoverability readout per the P4 closure rule;
the readiness / reconciliation table (native `M-BENCH` ↔ EXP-061 `M0` / EXP-060B; hybrid `H-BENCH` ↔ EXP-061 `H0`;
`*-NONE` ↔ EXP-062 tail, per object); and first-hit `r` per variant per object (the off-0.50 narrative). The
`/STRONG-HA` / MAD / ZigZag-adverse secondaries are **deferred** (see Exclusions). **No phase closure or candidate
registration here.**

## Complexity Budget (Comparative experiment)

- **Max distinct statistical methods: 4** — (1) regime-clustered moving-block bootstrap CI on a variant's **median**
  per cell (`bootstrap_median_distribution` + `median_ci`); (2) the same bootstrap applied to the per-cell **raw mean
  + 10% trimmed mean** (`bootstrap_stat_distribution`; the P4 diagnostic) with the worst-5% tail-share point
  estimate; (3) `variant − RM` signal-vs-null contrast CI (`contrast_ci`, independent — the binding
  signal-attribution test, applied per variant per object); (4) the **bounded-downside recovery / variant−benchmark
  contrast** CI — `mean(bounded) − mean(*-NONE)` and the variant−benchmark median paired contrast
  (`xen.favourable_targets.paired_median_contrast_ci` on the common qualifying subset where applicable). A
  parameterised re-instrumentation of EXP-057/EXP-061 applied to two objects — **not new methods** (running the same
  4 methods on a second object adds no distinct method).
- **Max visualisations: 5** — each rendered **per object** (hybrid and native panels/series, never pooled): (i)
  per-variant **median-expectancy forest** per cell vs benchmark (bounded-downside binding, `*-NONE` disclosed); (ii)
  per-variant **variant − RM-on-MA** signal-attribution forest (non-4h cells marked) — the binding discriminator;
  (iii) **the mean investigation** — per-variant raw-mean vs 10%-trimmed mean with worst-5% tail-share annotated,
  `*-NONE` vs bounded side-by-side (the headline skew/recovery plot); (iv) **bounded-downside recovery map** —
  `mean(bounded) − mean(*-NONE)` across cells (does bounding lift the mean?) with the low-n-4h concentration flagged;
  (v) P11 composition / wins map across variants **and objects** (median-viable ∧ beats-RM ∧ non-4h; hybrid vs native
  side-by-side). Secondary tables to CSV.
- **Max new code modules: 1 — *expected 0*.** Reuses `xen.adverse_targets` wholesale (substrate-generic) and the
  EXP-061 **dual-object** MA pipeline + P4 functions. The only orchestration change vs EXP-061 is the per-variant
  adverse-level build (the existing `xen.adverse_targets` builders, fed the MA in-progress start index) and the
  per-object × per-variant RM/contrast loop. At most one thin orchestration wrapper under `code/`; **no new `xen/`
  analysis module.**

## Metric Denominators & Zero-Baseline

- **Per-event realised gross return** (ATR units) is defined for every **qualifying** event of a variant (of an
  object) — a built barrier (valid `adv_dist ≥ ADV_FLOOR` for stopped variants; `*-NONE` always has a built window)
  resolving to FAV, ADV, or TIMECAP. Return = `rd·(exit_price − C)/ATR_entry` (`realised_returns`), `exit_price` the
  P15 path-ordered fill, `ATR_entry` = Wilder ATR(14) at the harami entry bar. `DATA_CENSORED`, warmup-excluded, and
  degeneracy-excluded events are **excluded** from median/mean/trim/tail and **disclosed as counts** per cell per
  variant per object.
- **Per-cell endpoints:** `median` (binding, P14); raw mean + 10% trimmed mean (P4 diagnostic, each fixed-seed
  bootstrap CI); worst-5% tail-share point estimate. Each over the variant's qualifying-event population, per object.
- **Zero-baseline / power:** a cell with **< 30 qualifying events** for a variant (of an object) is
  **NOT_VIABLE-by-power** for that variant/object (non-reportable for its readout), never an undefined/infinite ratio.
  Conditioning + per-variant degeneracy/warmup exclusions reduce counts vs the unconditioned base; the hybrid object
  (3202-class on EURUSD-5m) is structurally lower-count than native (8360-class); depleted cells are disclosed.
- **Worst-5% tail-share:** finite in `[0,1]`; a cell with no negative return mass reports **0.0** (never NaN/inf,
  per `_tail_share_worst5`); an empty/degenerate cell reports it undefined → excluded.
- **Bounded-downside recovery contrast:** defined only where both `*-NONE` and the bounded variant are powered
  (≥ 30) on the same object; otherwise disclosed as power-limited, never defaulted.
- **First-hit `r`** per variant per object (disclosed secondary): `r = n_FAV/(n_FAV + n_ADV)` over resolved FAV/ADV
  events, TIMECAP excluded from the denominator (EXP-049 convention). For `*-NONE`, `n_ADV = 0` ⇒ `r = 1.0` by
  construction where any FAV occurs — reported with that explicit caveat (degenerate `r`; exactly why `r` is
  non-binding).
- **Disclosed secondaries (never binding):** per-arm qualifying / `DATA_CENSORED` / warmup / degeneracy counts; win
  rate; first-hit `r` per variant per object; the EXP-062 per-object MAE-tail cross-check (emitted in
  `reconciliation.csv` / `secondary_map.csv`).
- **Deferred disclosed secondaries (runtime/budget; NOT computed in EXP-063, explicitly — not silently):** the
  `/STRONG-HA` conditioning arm, the MAD `/STRONG-STAT` sensitivity arm, and a full **ZigZag-substrate adverse
  surface**. With the adverse axis now run on **two** conditioning objects, computing it on three further populations
  would multiply the per-cell arm count against the performance mandate while adding only non-binding
  robustness/substrate context. The binding question (does a bounded-downside variant keep median viability + beat
  RM-on-MA, per object) and the decisive §4 mean investigation are fully answered on the binding
  `/STRONG-STAT`-on-MA axis for both objects without them. The deferral is recorded in `run_metadata.json`
  (`disclosed_secondaries_not_computed`); if G-015 needs them, they are a bounded follow-up.

## Data Requirements

Per cell (instrument × domain), TRAIN slice only: lazy `pl.scan_parquet`; read total row count from metadata;
`analysis_rows = int(total_rows*0.7)`, `train_rows = int(analysis_rows*0.7)`; collect only the first `train_rows`
file-order 1-minute rows (F01 prefix; never sort/collect the full file, never read TEST or holdout); assert
chronological; `train_end_ts` = last `CloseTime`. Aggregate each member domain (5m strict; others
`min_coverage=0.90`); fence to `CloseTime ≤ train_end_ts`; generate HA candles; run
`xen.zigzag.generate_zigzag(bars, atr_period=14, atr_mult=1.0)` → confirmed moves + confirm/start/end indices
(the hybrid conditioning mask + disclosed `Z-BENCH` contrast); run `ma_segment_moves` (MA(20,50) on real close) → MA
confirmed segments + indices; detect haramis on HA candles aligned by `CloseTime`; build **both** conditioned
populations — hybrid (`zz["stat"]["retained_p75"]`, byte-identical to EXP-053/060/061 `H0`) and native
(`ma["stat"]["retained_p75"]`, byte-identical to EXP-061 `M0`) — and the MA in-progress state
(`live_in_progress_state` on MA arrays, supplying `rd` / `M_sofar` / `start_epoch` → `ma_start_idx`, shared by both
objects); compute the benchmark favourable level + MA adaptive cap; for each predeclared adverse variant build
`adv`/`adv_dist` via `xen.adverse_targets` (`*-BENCH` from `benchmark_barriers`; `*-RAW`/`*-RR1` from the MA-fed
`faded_move_extreme` + `adverse_extreme_raw`/`adverse_extreme_rr1`; `*-NONE` from `adverse_none_sentinel`) and
resolve it **on each object's population** via `resolve_path_ordered` → `realised_returns` → `qualifying_mask`;
bootstrap per-cell median + raw mean + 10% trimmed mean per variant per object (fixed seed) + worst-5% tail-share;
build the per-object per-variant matched-random-on-MA nulls (RM-* native, RH-* hybrid) by matched-count in-regime
selection through the identical per-variant pipeline and the `variant − RM` contrast; compute the per-object
bounded-downside recovery contrasts `mean(*-BENCH/*-RR1) − mean(*-NONE)`; reconcile native `M-BENCH` ↔ EXP-061 `M0` /
EXP-060B `BENCH-MA` and hybrid `H-BENCH` ↔ EXP-061 `H0`, and cross-check each object's `*-NONE` tail vs EXP-062;
compose by P11 with the P6 non-4h rule, per object; second full pass for determinism. `tqdm` over the 99-cell grid
(per-instrument worker); **bounded per-cell memory** (forward scans bounded by `bench_n`; release per-cell arrays
after summarisation). Outputs (`results/`): `per_cell_expectancy.parquet` (per cell × variant × **object**:
median/mean/trimmed + CIs, tail-share, gap, n_qualifying, censoring/warmup/degeneracy, win rate, `r`, viability +
RM-beat + mean-viable flags); `adverse_map.csv` (binding `/STRONG-STAT` summary per variant per object + P11 non-4h
tally); `mean_investigation.csv` (the §4 decomposition per object: raw/trimmed mean, tail-share, recovery contrast,
instrument/domain concentration with low-n-4h flags — the headline deliverable); `signal_attribution.csv`
(`variant − RM-on-MA` per variant per object); `secondary_map.csv` (`*-RAW`, ZigZag `Z-BENCH` disclosed, `r`);
`reconciliation.csv` (native `M-BENCH` ↔ EXP-061 `M0` / EXP-060B; hybrid `H-BENCH` ↔ EXP-061 `H0`; `*-NONE` ↔
EXP-062 tail; population vs EXP-053/060/061, per object); `composition_readout.json` (per-object per-variant P11 +
non-4h, the EVIDENCE_FOR / MEDIAN_ONLY / EVIDENCE_AGAINST / INCONCLUSIVE fork per the P4 closure rule, per object →
G-015 input); `run_metadata.json` (seed, frozen constants, EXP-061/EXP-062/EXP-060B source paths/hashes,
parallelism note, holdout fence, `disclosed_secondaries_not_computed`). Bounded plots (≤5) from the collected
per-cell summaries (no reloads), rendered per object. Output **byte-identical across `--workers`** counts
(order-independent per-cell RNG + fixed merge order).

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

Fork **EXP-061's dual-object `code/run_experiment.py`** (it already computes hybrid `H0` and native `M0` BENCH
arms via `bench_signal_arm` with the `cond_mask` override, the `_zz_context`/`_ma_context`, the per-object
matched-random controls `RH0`/`RM0` via `matched_random_arm`, the corrected reconciliation roles, and the P4
mean/trim/tail bootstrap). Changes, all bounded: **(1)** generalise the single BENCH `resolve_arm` to a
**per-variant loop** over the 4 adverse models, building each variant's `adv`/`adv_dist` from `xen.adverse_targets`
— `*-BENCH` via the existing `benchmark_barriers` (keeps the `M0`/`H0` median paths byte-identical, so `M-BENCH`
reconciles to EXP-061 `M0` and `H-BENCH` to EXP-061 `H0` exactly), `*-RAW`/`*-RR1` via `faded_move_extreme` (fed the
**MA** in-progress `start_idx` from `ma_context["state"].start_epoch` mapped to the grid) + `adverse_extreme_raw`/
`_rr1`, `*-NONE` via `adverse_none_sentinel`. **(2)** Run each variant on **both** object populations — native
(`ma["stat"]["retained_p75"]`) and hybrid (`zz["stat"]["retained_p75"]` via `cond_mask` through the MA context;
verify `ma["entry_idx"]` and `zz["entry_idx"]` are the identical harami-entry array — both detect on the same HA
candles aligned by `CloseTime`; if a context stores entries differently, index the ZigZag mask onto the MA entry
order by `CloseTime` before applying). **(3)** Run the existing `matched_random_arm` through each variant's pipeline
to produce the per-object nulls RM-BENCH/RR1/NONE/RAW (native) and RH-BENCH/RR1/NONE/RAW (hybrid) — each matched to
its **own** object's variant count, excluding its **own** object's signal entries, on **fresh dedicated RNG purposes
per object/variant** so no existing stream shifts — and the per-object per-variant `variant − RM` contrast. **(4)**
Add the **bounded-downside recovery contrasts** `mean(*-BENCH/*-RR1) − mean(*-NONE)` (`contrast_ci` on the stored
per-variant mean distributions) and the §4 instrument/domain/regime concentration table with low-n-4h flags, **per
object**. **(5)** Reconcile native `M-BENCH` ↔ EXP-061 `M0` / EXP-060B `BENCH-MA` and hybrid `H-BENCH` ↔ EXP-061
`H0` exactly (SUBSTRATE/METHOD_DEFECT if not), and cross-check each object's `*-NONE` MAE/tail against EXP-062's
per-object `mae_tail_decomposition.csv` (disclosed). **(6)** Emit **per-object** P11 / signal-vs-RM /
**mean-investigation** readouts (never pooled; add an `object` tag to every per-cell × per-variant row). Adopt
EXP-061's per-instrument `ProcessPoolExecutor` with per-process native-thread pinning (`POLARS_MAX_THREADS=1` etc.)
and fixed-order reassembly (byte-identical output for any `--workers`). Fixed per-cell seed throughout (P3); `tqdm`;
bounded memory; **do not adjudicate G-015** (single gate after the full slate). The existing native/hybrid BENCH
median+mean RNG paths must stay byte-identical to EXP-061 (use new RNG purposes for the new adverse variants and the
new nulls only) so the EXP-061 reconciliation still holds for both objects.
