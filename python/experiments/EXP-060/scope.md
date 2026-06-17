# Experiment: EXP-060 — Combined Event System (Conditioned HA Harami; Best Per-Layer Geometry, 2×2 Favourable×Adverse Factorial + Champion)

> **Mandatory-reading precondition (014-B, binding).** `014-A-conditioning-gap-and-validation-lessons.md`
> was read in full before this scope was written. EXP-060 is the **combined event system** read (HYP-013,
> P14/P15/P16; assembles the survivors of EXP-053/056/057/058/059), the **last 014-B surface read** and the
> sole quantitative input to the single 014-B **G2**. The four mandatory rules are honoured as follows,
> recorded so Stage 4 can check:
> - **(a) conditioning** — honoured. The object measured is the **live `/STRONG`-conditioned HA harami** (the
>   actual family signal, population byte-identical to EXP-053/054/055/056/057/058/059), not the raw harami or
>   the unconditioned ZigZag substrate. `/STRONG-STAT` (P7, live magnitude-percentile) is binding; `/STRONG-HA`
>   (P8) is a disclosed secondary arm.
> - **(b) harami-anchor** — honoured. Entry is the **harami confirmation-bar real close** `C`, the family's
>   claimed lead point — *not* the ZigZag trend-change confirmation (the EXP-049 anchor). A forward ZigZag
>   trend-change / opposing harami is used only as an *exit* event (V2A has no reversal leg; V2A is purely
>   fractional-target legs), never as the entry.
> - **(c) position-in-move descriptive-only / never a live filter** — honoured. EXP-050's position metric is
>   not used. Every exit trigger (fractional favourable targets, the time cap) is acted on at a bar known
>   forward-in-time after entry; no unconfirmed pivot is referenced.
> - **(d) expectancy / not first-hit `r`** — honoured. The binding endpoint is **median gross per-event
>   expectancy** (P14, ATR-normalised, P15 fills) of the **position-weighted realised return**. First-hit `r`
>   is undefined/secondary for multi-leg exits and is reported only for the single-leg BENCH arm; win rate and
>   exit-reason composition are disclosed secondaries.
> EXP-060 does **not** treat the EXP-049 `r≈0.50` null or the EXP-050 front-loading as evidence against the
> family — those measured the *unconditioned* object.

**Phase / checkpoint:** `2026-06-14-014-ha-harami-substrate-and-capture` (014-B; G0-B PASS 2026-06-15).
**Family / candidate:** `CF-HA-HARAMI-001` (`REGISTERED`, OPEN) · `CF-HA-HARAMI-001/HYP-013` — EXP-060
(registered PLANNED, Phase 014-B batch, `multiplicity-registry.md` line 390). Composes the registered branches
`CF-HA-HARAMI-001/EXIT-PARTIAL` (P17, the V2A scheme) and `CF-HA-HARAMI-001/ADV-NONE` (P3 alternative) on the
benchmark favourable (P2) + benchmark adaptive-cap third barrier (P4); the longer-horizon disclosed sibling
exercises the registered `CF-HA-HARAMI-001/THIRD-TIME` grid (floor=48). **No new countable item** is
introduced — the combined event definition consumes a candidate slot only at G2 PROCEED_TO_SCREEN (P21), never
in this scope.
**Surface role:** the **final** 014-B read. The four surface levers were measured one-at-a-time against
predeclared benchmark defaults: favourable (EXP-056 EVIDENCE_AGAINST — benchmark 50% wins), adverse (EXP-057
EVIDENCE_FOR — `/ADV-NONE` wins), third barrier (EXP-058 EVIDENCE_AGAINST — benchmark adaptive cap wins),
position management (EXP-059 EVIDENCE_FOR — `/EXIT-PARTIAL` V2A strongest). The conditioned signal is real
(EXP-053 EVIDENCE_FOR) and the move is available (EXP-055 AVAILABILITY_GOOD). EXP-060 **assembles the best
per-layer geometry onto one event** and asks whether the combined system clears P11 expectancy viability vs
P13 baselines — the G2 PROCEED_TO_SCREEN condition. Output feeds the single 014-B G2; **no closure or candidate
registration here**.
**Governing design:** `014-B-design.md` (§2/§3/§5 surface row EXP-060, §6, §7, §8 PROCEED_TO_SCREEN criterion)
+ `014-B-D0-addendum.md` (P14/P15/P16/P17/P20/P21); inherits Phase 014 `design.md` §8 D0 (P1–P13) and the
family spec `candidate-families/harami.md` (branches `/EXIT-PARTIAL`, `/ADV-NONE`, `/THIRD-TIME`).
**Reuses (no new modules expected):** the EXP-053/057/058/059 conditioned-signal construction and the
benchmark/P15/P14 machinery — `xen.expectancy.live_in_progress_state`, `live_strong_stat`,
`adaptive_time_caps_by_epoch`, `benchmark_barriers`, `resolve_path_ordered`, `realised_returns`,
`qualifying_mask`, `bootstrap_median_distribution`, `median_ci`, `contrast_ci`; the multi-leg P15 resolver and
weighted returns `xen.position_exits.resolve_legs`, `leg_levels_from_fracs`, `weighted_returns`,
`exit_reason_weights`; the ADV-NONE adverse layer `xen.adverse_targets.adverse_none_sentinel` (passes
`adv = ∓inf` into the shared resolver so no stop ever binds); the paired-median contrast
`xen.favourable_targets.paired_median_contrast_ci`; ZigZag (`xen.zigzag.generate_zigzag`, primary
`atr_mult=1.0`), harami (`xen.ha_harami.detect_ha_harami`), `/STRONG-HA`
(`xen.strong_move.annotate_ha_impulse`), confirmation indices (`xen.capture_barriers.confirm_indices`).

## Operator decisions (2026-06-16, recorded before any data contact)

Three predeclared-design forks were resolved by the operator at Stage 1 (recorded with rationale; no data
contact preceded these):

1. **Predeclared arm set = 2×2 favourable×adverse factorial + BENCH anchor (4 distinct binding-reported
   configs).** Cross `{50%-single-leg, V2A 3-leg partial}` favourable × `{1:1, /ADV-NONE}` adverse, with the
   third barrier held at the **benchmark adaptive time cap** (floor=6) for all four. BENCH = the `(50%, 1:1)`
   cell (also the EXP-053 reproduction/invariant anchor), so the four configs are: **A0 BENCH**, **A1
   50%×NONE**, **A2 V2A×1:1**, **A3 V2A×NONE (champion)**. Rationale (operator): a 2×2 factorial maximises
   inferential density — it recovers the favourable main effect, the adverse main effect, **and** their
   interaction — at best information-per-degree-of-freedom for a TRAIN-only gross read, without diluting power
   into low-prior arms. (Broader "next-best alternative" siblings — V2C, MAG-0.5 — were declined to keep the
   focused "best per-layer" intent.)
2. **G2 binding candidate = the champion A3 (V2A×ADV-NONE) only.** Only the champion's P11 expectancy
   viability vs P13 baselines drives the G2 PROCEED_TO_SCREEN / CHARACTERISED_NOT_VIABLE fork. The adjacent
   factorial cells (A1, A2) and the disclosed horizon sibling are **non-binding attribution context** — they
   inform *why* the combined system is/ isn't viable, not *whether* it is. Rationale (operator): preserves the
   confirmatory distinction between the single pre-registered composite hypothesis and the attribution arms;
   matches 014-B design §8 ("≥1 combined event definition clears P11") with one predeclared definition.
3. **Add one longer-horizon disclosed-only sibling: A4 = champion at `/THIRD-TIME` floor=48.** The benchmark
   adaptive cap collapsed to the 6-bar floor in 96/99 cells (014-A G1), which bounds V2A's scaled legs and
   ADV-NONE's "let it run" adverse. A4 re-runs the champion under the **longest registered `/THIRD-TIME` grid
   point** (`floor=48`, `k=1.5`, `window=20`, `min_moves=5` — EXP-058's grid; the `/THIRD-TIME` lever raises
   the *floor*, not k). A4 is **DISCLOSED-ONLY, non-binding** (it does not enter the G2 fork). Rationale
   (operator): prevents the 6-bar floor from being an uninterpretable confound — gives the mechanism room to
   breathe so a champion failure can be attributed to mechanism vs. horizon truncation. Using a registered
   grid point (not a new value) keeps this within predeclared multiplicity; no new tuning.

Additional standing decisions (precedent-default, no deviation):
- **This is a predeclared assembly, not a search.** Every arm/config below is predeclared here; **no
  post-result variant selection** — every arm is reported and composed by P11; routing is the single 014-B G2
  after the full slate (no intermediate gate, no early closure inside 014-B).
- The "best per-layer geometry" is a **deterministic function of already-recorded prior results**
  (EXP-053/056/057/058/059), fixed at this scope — it is *not* selected from EXP-060's own outputs.
- **Leg weighting fixed:** every partial scheme splits the full entry weight into exactly **3 equal legs**
  (`w = 1/3`); single-leg arms are `w = 1`. (P17 "≤3 equal parts"; fixed at 3 across the sweep, identical to
  EXP-059.)
- **V2A favourable legs** = `{1/3, 2/3, 1} × fav_dist`, `fav_dist = 0.50·M_sofar` (P2; final leg = the
  benchmark 50% favourable level) — identical to EXP-059 PARTIAL-V2A.
- `/STRONG-STAT` (P7) is the binding conditioning filter for every arm; `/STRONG-HA` (P8) is a disclosed
  secondary arm; both P13 baselines (matched-random, MA(20,50)) run through the identical per-arm pipeline.

## Slot & ledger accounting (binding)

- **0 candidate slots, 0 TEST reads.** Characterization/diagnostic per the 014-B D0 addendum
  (`014-B-D0-addendum.md` slot & ledger accounting). The composed branches (`/EXIT-PARTIAL`, `/ADV-NONE`,
  `/THIRD-TIME`) are already registered; a candidate branch — the surviving combined definition — consumes a
  slot only at G2 PROCEED_TO_SCREEN (P21), never in this scope.
- **No TEST stratum is read.** All work is on the **TRAIN** slice (first 70% of the first-70% analysis set),
  identical fence to EXP-049/053/054/055/056/057/058/059. The conditioned HA-harami event population had its
  first new-universe TRAIN contact in EXP-053 (same definition); **no new stratum is opened**, so the
  `test-read-ledger.md` requires no entry and the global-holdout seal carries forward unchanged. The
  current per-stratum counted-read tally is **irrelevant** (no TEST stratum is touched); for the record, no
  HA-harami TEST stratum has ever been read (every 014-A/B read is TRAIN-only).
- All work is **gross** (no costs). Detection on HA candles; **every outcome metric on real prices**
  (`RealOpen/High/Low/Close` domain-bar OHLC), never HA prices.

---

## Hypothesis

For the live `/STRONG`-conditioned HA harami (anchored at the harami confirmation-bar close, faded against the
in-progress strong move), the **combined event system that assembles the best per-layer geometry** — V2A 3-leg
scaled favourable take-profits at `{1/3, 2/3, 1}×(0.50·M_sofar)`, **no adverse stop** (`/ADV-NONE`), benchmark
adaptive time cap as the ultimate backstop — produces **positive gross per-event median expectancy** (P14,
ATR-normalised, position-weighted realised return, P15 fills, real prices) that **clears the P11 quorum**
(≥5 cells over ≥3 instruments with CI_low > 0) **and beats both P13 baselines** (matched-random, MA(20,50)) in
that quorum, on the binding `/STRONG-STAT` arm.

Falsifiable: if the champion combined definition does **not** clear P11 expectancy viability vs both P13
baselines, then the assembled best-per-layer combined event system is **not** a viable candidate on benchmark
geometry — a valid CHARACTERISED_NOT_VIABLE characterization result that feeds G2 (closure well-supported, but
adjudicated only at the single 014-B G2 across the full slate — never a closure inside this experiment).

## Question

Does assembling the four measured per-layer winners onto **one** conditioned HA-harami event — V2A scaled
favourable exits + no adverse stop + benchmark adaptive cap — produce a positive, P11-composed, baseline-
beating gross per-event median expectancy (the G2 PROCEED condition)? And, attributively (disclosed, non-
binding): how does the champion decompose across the **2×2 favourable×adverse factorial** (favourable main
effect, adverse main effect, interaction) vs the BENCH reference, and does relaxing the benchmark 6-bar-floor
horizon (A4, `/THIRD-TIME` floor=48) materially change the champion's expectancy (mechanism vs truncation)?

---

## Scope Boundaries

### Data Views

- **Real domain bars** (5m strict; 15m/30m/1h/2h/4h via `xen.bar_aggregator.aggregate_ohlc`,
  `min_coverage=0.90` — identical to EXP-048/049/053–059/VAL-004) for the primary ZigZag substrate
  (`atr_mult=1.0`), confirmed moves, strong-move magnitudes, the benchmark third-barrier adaptive cap (and the
  floor=48 sibling cap), all barrier/leg levels, P15 fills, ATR normalisation, and **all** outcome metrics.
- **Heiken Ashi candles** (`xen.heiken_ashi_generator`, from the same domain bars) for **harami detection
  only** (`xen.ha_harami.detect_ha_harami`, frozen EXP-048 detector) and the `/STRONG-HA` arm
  (`xen.strong_move.annotate_ha_impulse`). **No HA price enters any metric.**
- No secondary trailing ZigZag is needed (no `/EXIT-TRAIL-STRUCT` arm here — EXP-059/059B characterised
  trailing as detrimental; it is excluded from the combined system).

### Event population (the live conditioned signal — identical to EXP-053/054/055/056/057/058/059)

- An HA harami (frozen detector) **AND** the live `/STRONG-STAT` magnitude-percentile filter: the in-progress
  confirmed-ZigZag move's **magnitude-so-far** `M_sofar = |C − start_pivot|` (last *confirmed* pivot → harami
  real close `C`) is **≥ p75** of the trailing-20 confirmed-move magnitudes (P7, binding). `/STRONG-HA` (P8:
  run of `X=3` large-body HA bars, no opposing wick) is a **disclosed secondary** arm run through the
  identical pipeline.
- **Trade / reversal direction** `rd = Direction_k` of the last confirmed primary-ZigZag move
  (`xen.expectancy.live_in_progress_state`; in-progress trend `= −Direction_k`, so the reversal/fade trade is
  in `rd`). No `/BARCFG` isolation; all qualifying haramis count.
- Construction reuses `xen.expectancy.live_in_progress_state` + `live_strong_stat` — the **same functions
  EXP-053/057/058/059 used** — so the binding population is **byte-identical** to EXP-053's conditioned events
  (verified by population reconciliation; SUBSTRATE/METHOD_DEFECT if it diverges).

### Entry anchor

The **harami confirmation-bar real close** `C` (real domain-bar close at the harami timestamp), strictly
before any ZigZag trend-change confirmation. Identical to EXP-053/055/056/057/058/059.

### Predeclared arm set (best-per-layer assembly; 2×2 factorial + BENCH + 1 disclosed horizon sibling)

Notation: `C` = entry close; `rd` = trade direction; `M_sofar` = magnitude-so-far; `fav_dist = 0.50·M_sofar`
(P2); `fav = C + rd·fav_dist` (benchmark favourable level); `adv = C − rd·fav_dist` (benchmark 1:1 adverse
level); `bench_N` = benchmark P4 adaptive cap (floor=6); `N48` = `/THIRD-TIME` floor=48 adaptive cap. Every
leg/level is evaluated on **real prices** under the **P15 path model** (bullish bar `Close ≥ Open`:
`O→L→H→C`; bearish: `O→H→L→C`). Each arm's forward scan runs `[entry_idx+1, entry_idx + N]` (its own cap),
TRAIN-fenced; a window truncated by the edge before the position resolves is `DATA_CENSORED` (excluded-with-
record, disclosed).

| # | Arm id | Favourable side | Adverse side | Third barrier | Role |
|---|--------|-----------------|--------------|---------------|------|
| A0 | `BENCH` | 50% fav (1 leg) | 1:1 stop | adaptive cap (floor=6) | Reference; reproduces EXP-053 benchmark; the (50%,1:1) cell of the 2×2. **Invariant anchor.** |
| A1 | `50%×NONE` | 50% fav (1 leg) | **/ADV-NONE** (no stop) | adaptive cap (floor=6) | Adverse main-effect isolation (≈ EXP-057 ADV-NONE re-anchored at the single 50% leg). **Disclosed, non-binding.** |
| A2 | `V2A×1:1` | V2A legs `{1/3,2/3,1}×fav_dist` | 1:1 stop (all open legs) | adaptive cap (floor=6) | Favourable main-effect isolation (= EXP-059 PARTIAL-V2A re-anchored). **Disclosed, non-binding.** |
| A3 | `V2A×NONE` **(champion)** | V2A legs `{1/3,2/3,1}×fav_dist` | **/ADV-NONE** (no stop) | adaptive cap (floor=6) | **Best per-layer geometry. The single binding G2 candidate.** |
| A4 | `V2A×NONE@T48` | V2A legs `{1/3,2/3,1}×fav_dist` | **/ADV-NONE** (no stop) | **/THIRD-TIME floor=48** cap | Champion under relaxed horizon. **DISCLOSED-ONLY, non-binding** (mechanism-vs-truncation isolation). |

Arm construction (all reuse existing resolvers; **no `/EXIT-TRAIL-STRUCT`, no reversal-event legs** — V2A is
pure fractional-target legs):
- **A0 BENCH** — single leg `w=1`: `resolve_path_ordered(fav, adv, bench_N)` (`xen.expectancy`), exactly
  EXP-053's benchmark. Reproduces EXP-053 per-cell median expectancy, qualifying count, and `r≈0.50`
  (invariant check).
- **A1 50%×NONE** — single leg `w=1`, favourable level `fav`; adverse via
  `xen.adverse_targets.adverse_none_sentinel` (`adv = ∓inf`, never binds); cap `bench_N`. Resolves on `fav`
  touch (P15) or `TIMECAP`.
- **A2 V2A×1:1** — 3 equal legs at `{1/3,2/3,1}×fav_dist` (`leg_levels_from_fracs`), shared 1:1 adverse stop
  `adv` (binds all still-open legs at the same bar/level when reached on the P15 path), cap `bench_N`;
  `resolve_legs` with `adv_mode=ADV_FIXED`, `adv_level=adv`. Identical to EXP-059 PARTIAL-V2A.
- **A3 V2A×NONE (champion)** — 3 equal legs at `{1/3,2/3,1}×fav_dist`; shared adverse = the ADV-NONE sentinel
  (`adv_level=∓inf`, never binds); cap `bench_N`; `resolve_legs` with `adv_mode=ADV_FIXED`,
  `adv_level=±inf`. Still-open legs run to their favourable target or exit `TIMECAP` at the cap bar's real
  close. **This is the only novel cross-layer cell** (V2A validated under 1:1; ADV-NONE validated under a
  single 50% leg — their combination is unmeasured).
- **A4 V2A×NONE@T48** — identical to A3 but the third-barrier cap is `N48 = max(48, round(1.5×median(trailing-20
  confirmed-move durations)))` (`adaptive_time_caps_by_epoch` re-called with `floor=48`, all other knobs at
  benchmark). Disclosed-only.

**Per-event realised return (binding endpoint input).** For every arm the per-event realised gross return is
the **position-weighted** sum of leg returns: `R_event = Σ_l w_l · rd·(exit_px_l − C)/ATR_entry`, where each
leg's `exit_px_l` is its P15 fill (favourable level, shared adverse stop where present, or cap close),
`Σ_l w_l = 1`, and `ATR_entry` = Wilder ATR(14) at the harami entry bar (P14). Single-leg arms (A0, A1) are
the `w=1` special case. `R_event` is the per-event value fed to the median bootstrap and the paired contrasts
— the same statistical machinery as EXP-056/057/058/059 (`xen.position_exits.weighted_returns`); only the
arm configuration changes.

### Factorial decomposition (disclosed, non-binding attribution)

On the common qualifying-event subset (per cell, events qualifying under both compared arms), report:
- **Favourable main effect:** `A2 − A0` (under 1:1) and `A3 − A1` (under ADV-NONE) paired-median contrasts.
- **Adverse main effect:** `A1 − A0` (single 50% leg) and `A3 − A2` (V2A legs) paired-median contrasts.
- **Interaction:** `(A3 − A2) − (A1 − A0)` — does V2A scaled exits and no-stop combine super-/sub-additively?
- **Champion value:** `A3 − A0` (champion vs benchmark) — the headline "value of the combined system" (still
  disclosed; the *binding* G2 readout is A3's own P11 viability vs P13 baselines, per operator decision 2).
- **Horizon sensitivity:** `A4 − A3` — does relaxing the 6-bar floor change the champion materially?

### Parameters (all frozen D0 / predeclared this scope; no tuning)

Primary ZigZag Wilder ATR(14), `ATR_MULT = 1.0` (P1); `/STRONG-STAT` trailing-20, ≥p75 (P7); `/STRONG-HA`
`X=3` (P8); benchmark favourable `X = 50%` of `M_sofar` (P2); benchmark adverse 1:1 (P3) where present; ADV-NONE
sentinel (`adv = ∓inf`) for A1/A3/A4; benchmark time cap `(k=1.5, window=20, floor=6, statistic=median,
min_moves=5)` (P4) for A0–A3; the **registered `/THIRD-TIME` floor=48** cap (`k=1.5, window=20, floor=48,
min_moves=5`) for A4 only; ATR-normalisation divisor = Wilder ATR(14) at the harami entry bar (P14); bootstrap
`b = round(m^(1/3))`, `N_BOOT = 10_000`, fixed seed (P14). **Predeclared position-management parameters
(carried from EXP-059):** 3 equal legs (`w=1/3`); V2A fractions `{1/3, 2/3, 1}`. None is tuned against
outcomes; no grid is swept beyond this predeclared set.

### Instruments / cells

The **99-cell EXP-049/053–059 member grid**: 17 instruments × {5m,15m,30m,1h,2h,4h} minus the 3
COVERAGE_EXCLUDED cells (US500-4h, JP225-2h, JP225-4h). Per-cell first, then **P11** composition (≥5 cells over
≥3 instruments) for any "viable"/"champion" claim. Full-grid breadth required by P11 and the "no blanket
assumptions" principle. DE30 carries the truncated-coverage disclosure.

### Time range

Full dataset, nested chronological split. **TRAIN only** = first 70% of the first-70% analysis set (per cell,
F01 file-order-prefix convention identical to EXP-049/053–059: `train_end_ts` = last `CloseTime` of the first
`int(int(total_rows*0.7)*0.7)` file-order 1-minute rows). TEST (last 30% of the analysis set) and the
final-30% **global holdout** are **not** read. All forward windows (legs, caps incl. the floor=48 sibling) are
clipped to `train_end_ts`; an unresolved truncated window is `DATA_CENSORED` (disclosed), never resolved past
the edge.

### Baselines (P13 / P20 — binding for the champion, disclosed for the rest)

- **Matched-count random in-regime timestamps** (same cell/regime/direction, EXP-021/027 exclusion
  convention) run through the **identical exit pipeline** for each arm — does the combined scheme beat random
  entries under the *same* scheme? (For the **champion A3**, the `A3 − matched-random` paired contrast CI_low > 0
  is a **binding** G2 condition; for A0–A2/A4 it is disclosed.)
- **MA(20,50) segmentation** (alternative trend substrate, EXP-050/053 baseline): conditioned-harami
  expectancy under MA-segmented moves for each arm, disclosed. (For the **champion A3**, `A3 − MA(20,50)` is a
  **binding** G2 condition — tests whether the combined edge is an artifact of ZigZag segmentation; for the
  rest, disclosed.)
- The binding G2 readout is the champion's own median expectancy P11 viability **and** its dominance over
  **both** P13 baselines in the quorum.

### Look-ahead / causality discipline (binding)

- Primary ZigZag pivots are future information until confirmed. The signal (harami + `/STRONG-STAT`),
  `M_sofar`, the favourable/adverse benchmark levels, the V2A leg levels, and both adaptive caps use **only**
  confirmed, completed prior moves and **real bars at or before the entry bar** for *construction at entry*.
- Every exit is a **forward** event acted on at a bar known going forward in real time: fractional-target
  touch (intrabar P15), shared 1:1 stop (where present, intrabar P15), and the time cap (cap bar's real
  close). No exit references an unconfirmed pivot or any future bar.
- The forward scan reads only bars `[entry_idx+1, min(entry_idx+N, last_train_idx)]`, fenced
  `CloseTime ≤ train_end_ts`; a window truncated before resolution is `DATA_CENSORED` (excluded, disclosed).
- Ordering/alignment by `CloseTime`, never bar index across views (primary ZigZag, HA candles, and real bars
  are aligned by `CloseTime`).

### Real-price outcome discipline

Harami detected on HA candles (and `/STRONG-HA` impulse runs on HA bodies); `M_sofar`, ATR normalisation, all
benchmark/leg levels, both adaptive caps, P15 fills, weighted expectancy, win rate, and exit-reason
composition on **real domain-bar OHLC**. **No HA price in any metric.**

### Exclusions

- No costs (gross only).
- **Best-per-layer assembly only.** The arm set is exactly the 2×2 factorial + BENCH + the one disclosed
  floor=48 sibling above. **No** `/VPTARGET`/`/MAGTARGET` (EXP-056), **no** `/ADV-EXTREME` (EXP-057), **no**
  `/THIRD-EVENT` or other `/THIRD-TIME` floors than the one registered floor=48 sibling (EXP-058), **no**
  `/EXIT-TRAIL-STRUCT`/`/EXIT-TRAIL-UNCAPPED` (EXP-059/059B characterised them detrimental), **no** other V2*
  partial schemes (V1/V2B/V2C). No `/BARCFG`/`/CONFIRM` overlays; no position-in-move *filter*.
- No parameter tuning; **no post-result variant selection** (all predeclared arms reported; the binding
  champion is fixed *now*, not chosen from outputs); no gate adjudication (single G2 after the full 014-B
  slate — EXP-060 emits a characterization readout only).
- No TEST or holdout contact; no candidate slot; no TEST read.

## Success / Failure Criteria

All criteria are **gross**, per-cell first, composed by **P11** (≥5 cells over ≥3 instruments). The binding
endpoint is **median per-event position-weighted gross expectancy** `E_cell` (ATR units, P15 fills), on the
**`/STRONG-STAT` arm**; per-cell viable iff **CI_low > 0** (regime-clustered moving-block bootstrap, one-sided
95%) **AND ≥ 30 qualifying events**.

- **PROCEED_TO_SCREEN-eligible (combined system viable) — feeds G2:** the **champion A3 (V2A×ADV-NONE)** **(a)**
  clears P11 on its own median expectancy (≥5 cells over ≥3 instruments with CI_low > 0, ≥30 events) **AND
  (b)** beats **both** P13 baselines (matched-random and MA(20,50)) on the paired contrast (CI_low > 0) within
  the P11 quorum. EXP-060 records this as the candidate-event characterisation; **the actual PROCEED/NOT
  decision and any candidate registration are made by the operator at G2**, not here.
- **CHARACTERISED_NOT_VIABLE-eligible:** the champion does not clear (a)∧(b). Recorded as a measured-negative
  characterization of the full conditioned best-per-layer surface; routing deferred to G2 (closure
  well-supported but adjudicated there, never here).
- **INCONCLUSIVE (power-limited):** fewer than the P11 quorum of cells reach ≥30 qualifying events on the
  champion (conditioning + ADV-NONE/cap censoring deplete counts), no correctness failure. Disclosed; never
  defaulted to a ratio.
- **SUBSTRATE/METHOD_DEFECT:** any determinism, causality, or invariant failure → fix before reporting.
  Invariant checks: (i) the **A0 BENCH** arm reproduces EXP-053 per-cell median expectancy, qualifying count,
  and `r≈0.50` to tolerance; (ii) population reconciliation vs EXP-053 **exact** (the conditioned
  `/STRONG-STAT` population is identical); (iii) leg weights sum to 1.0 for every arm, and a degenerate V2A
  with all three legs at the same `fav` level reproduces the single-leg 50% arm's `R_event` to float
  precision; (iv) the **ADV-NONE sentinel never fires an adverse exit** (no `ADV` exit class in A1/A3/A4 —
  only `FAV`/`TIMECAP`/`DATA_CENSORED`); (v) every exit price is a real-bar P15 fill and every exit bar has
  `CloseTime ≤ train_end_ts`; (vi) the shared 1:1 stop (A0/A2), when it binds, closes all still-open legs at
  the same bar/level; (vii) A4 differs from A3 **only** by the cap (`N48 ≥ bench_N` per event; identical legs/
  population), so `A4 − A3 ≥ 0` in expectancy is mechanically admissible only via fewer cap-truncations — any
  A4 population divergence from A3 beyond the cap is a defect.

The deliverable label is **COMBINED_SYSTEM_CHARACTERISED** carrying: the champion A3 per-cell + P11 readout and
its EVIDENCE_* classification vs both P13 baselines (the binding G2 input); the full 2×2 factorial
decomposition (favourable/adverse main effects + interaction, disclosed); the `A3 − A0` champion-vs-benchmark
contrast (disclosed); the `A4 − A3` horizon-sensitivity read (disclosed); both filter arms (`/STRONG-STAT`
binding, `/STRONG-HA` disclosed); both P13 baselines; and all disclosed secondaries (per-arm qualifying-event
count and `DATA_CENSORED`/warmup exclusion counts; **exit-reason composition** — fraction of weight exiting via
each leg / the 1:1 stop / the time cap; win rate; mean per-event return; first-hit `r` for the single-leg A0/A1
arms only). **No phase closure or candidate registration here** (single 014-B G2 after the full slate).

## Complexity Budget

- **Max distinct statistical methods: 4** — identical to EXP-056/057/058/059: (1) regime-clustered
  moving-block bootstrap CI on an arm's median expectancy per cell (`xen.expectancy.bootstrap_median_distribution`
  + `median_ci`); (2) the same on each P13 baseline; (3) paired-median contrast CI for the factorial main
  effects / interaction / champion-vs-benchmark / horizon sibling
  (`xen.favourable_targets.paired_median_contrast_ci`, common qualifying-event subset); (4) arm − baseline
  contrast CI (`xen.expectancy.contrast_ci`). These four methods are applied across the predeclared arm set
  (a parameterised assembly over one experiment, not new methods per arm) — consistent with the 014-B surface
  design and the EXP-056/057/058/059 precedent.
- **Max visualisations: 5** — (i) per-arm median-expectancy forest/CI per cell (champion highlighted vs
  BENCH); (ii) **2×2 factorial decomposition** (favourable main effect, adverse main effect, interaction —
  pooled + per-cell heatmap); (iii) champion A3 expectancy distribution + P11 composition / "viable-vs-
  baselines" map across cells (the binding G2 read); (iv) exit-reason composition by arm (which legs / the
  1:1 stop / the cap bind — the mechanism diagnostic) alongside per-cell qualifying-event counts; (v) horizon
  sensitivity `A4 − A3` (champion at floor=6 vs floor=48) per cell. Secondary tables to CSV.
- **Max new code modules: 1** — *expected 0*: the arm set composes existing resolvers
  (`xen.position_exits.resolve_legs` + `leg_levels_from_fracs` + `weighted_returns` + `exit_reason_weights`,
  `xen.adverse_targets.adverse_none_sentinel`, `xen.expectancy.resolve_path_ordered` +
  `adaptive_time_caps_by_epoch` + bootstrap/CI/contrast, `xen.favourable_targets.paired_median_contrast_ci`).
  At most one thin **combined-arm composition wrapper** (assemble the 5 arm configs and the factorial-contrast
  table) may be added under `code/` if orchestration clarity requires it; **no new `xen/` analysis module**.
  Orchestration in `code/run_experiment.py`.

## Metric Denominators & Zero-Baseline

- **Per-event realised gross return** (ATR units) is the position-weighted `R_event` (above), defined for
  every **qualifying** event of an arm — an event whose barriers/legs are constructible (`fav_dist > 0`,
  finite positive `ATR_entry`) and whose every leg / the position reaches a finite P15 exit (favourable level,
  shared 1:1 stop where present, or cap close) within the TRAIN-fenced window. `DATA_CENSORED` (window
  truncated by the TRAIN edge before resolution) and construction-warmup events are **excluded** from the
  median and **disclosed as counts** per cell per arm.
- **Per-cell endpoint (binding):** `E_cell = median` over the arm's qualifying-event `R_event` population.
  ADV-NONE arms cannot adverse-stop, so all non-favourable resolution is via the time cap — qualifying counts
  stay comparable to BENCH (the cap is the shared backstop); the floor=48 sibling (A4) raises censoring on
  late-TRAIN / shallow-history cells (longer windows), disclosed separately.
- **Zero-baseline / power:** a cell with **< 30 qualifying events** for an arm is **NOT_VIABLE-by-power** for
  that arm (non-reportable for its readout), never an undefined or infinite ratio. Conditioning + per-arm
  censoring exclusions reduce counts vs the unconditioned base; depleted cells are disclosed, never defaulted.
- **Exit-reason composition** per arm (disclosed secondary): fraction of position weight exiting via each V2A
  leg's favourable target, the shared 1:1 stop (A0/A2 only), and the time cap. The binding *mechanism*
  diagnostic — how the combined scheme realises P&L — but never enters viability.
- **First-hit `r`** is defined only for the single-leg **A0/A1** arms (`r = n_FAV/(n_FAV+n_ADV)`, TIMECAP
  excluded, EXP-049 convention; A1 has no adverse so `r→` favourable-vs-cap is reported as a disclosed
  descriptive only) and reported as a disclosed secondary anchor (A0 expected ≈0.50, replicating
  EXP-049/053). For multi-leg arms (A2/A3/A4) `r` is undefined and **not** reported as viability — exactly the
  P14 rationale.
- **Disclosed secondaries (never binding):** per-arm qualifying count, `DATA_CENSORED`/warmup exclusion
  counts, exit-reason composition, win rate, mean per-event return, A0/A1 first-hit `r`, the `/STRONG-HA` arm,
  both P13 baselines on the non-champion arms, the factorial main effects/interaction, the `A4 − A3` horizon
  read.

## Data Requirements

Per cell (instrument × domain), TRAIN slice only: lazy `pl.scan_parquet`; read total row count;
`analysis_rows = int(total_rows*0.7)`, `train_rows = int(analysis_rows*0.7)`; collect only the first
`train_rows` file-order 1-minute rows (F01 prefix; never sort/collect the full file, never read TEST or
holdout); assert chronological; `train_end_ts` = last `CloseTime`. Aggregate each member domain (5m strict;
others `min_coverage=0.90`); fence to `CloseTime ≤ train_end_ts`; generate HA candles; run the **primary**
`xen.zigzag.generate_zigzag(bars, atr_period=14, atr_mult=1.0)` → confirmed moves +
`xen.capture_barriers.confirm_indices`; detect haramis on HA candles aligned by `CloseTime`; build the live
in-progress state + `/STRONG-STAT`/`/STRONG-HA` conditioning (`xen.expectancy`); compute the benchmark
favourable + adverse levels + both adaptive caps (`benchmark_barriers`, `adaptive_time_caps_by_epoch` with
`floor=6` and `floor=48`); for each of the 5 arm configs compute per-event leg/level exits via the existing
resolvers (`resolve_path_ordered` for A0; `resolve_legs` + `adverse_none_sentinel`/1:1 for A1–A4) under P15,
the weighted `R_event` (`weighted_returns`), the qualifying mask; bootstrap the per-cell median per arm; compute
both P13 baselines through the identical per-arm pipeline; compute the factorial paired contrasts; compose by
P11; second full pass for determinism. `tqdm` over the 99-cell grid; **bounded per-cell memory** (do not retain
all domain frames or all bootstrap draws; per-event forward scans bounded by `bench_N`≈6 bars in most cells,
and by `N48` for A4 only). Fixed seed; deterministic. Outputs (`results/`):
`per_cell_expectancy.parquet` (per cell × arm: median/CI expectancy, paired contrasts (factorial + vs
BENCH + vs baselines), n_qualifying, censoring/warmup counts, exit-reason composition, win rate, viability
flag); `champion_map.csv` (binding A3 `/STRONG-STAT` readout per cell: median/CI, vs both baselines, viability,
P11 tally); `factorial_map.csv` (main effects + interaction per cell, pooled); `secondary_map.csv`
(`/STRONG-HA`, A0/A1 `r`, exit-reason composition, A4 horizon sibling); `composition_readout.json` (champion
P11 vs baselines → PROCEED-eligible/NOT-eligible fork input for G2; factorial summary);
`population_reconciliation.csv` (binding conditioned population vs EXP-053; A0 BENCH expectancy/`r`/count vs
EXP-053); `run_metadata.json` (seed, frozen + predeclared constants, EXP-053 source paths/hashes). Bounded
plots from the collected per-cell summaries (no reloads).

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

Compose existing primitives; **no new `xen/` module**. Pipeline per cell:
`xen.zigzag.generate_zigzag` (primary `atr_mult=1.0`) → confirmed moves +
`xen.capture_barriers.confirm_indices`; `xen.heiken_ashi_generator` + `xen.ha_harami.detect_ha_harami`
→ harami entry bars (aligned by `CloseTime`); `xen.expectancy.live_in_progress_state` + `live_strong_stat`
→ the binding conditioned population (identical to EXP-053; cross-checked by `population_reconciliation`);
`xen.strong_move.annotate_ha_impulse` → the `/STRONG-HA` arm. For each qualifying harami: compute the
benchmark favourable level + 1:1 adverse + both adaptive caps (`benchmark_barriers`,
`adaptive_time_caps_by_epoch` floor=6 and floor=48); build the 5 arm configs — A0 via `resolve_path_ordered`;
A1 via `resolve_legs` (single leg at `fav`, adverse = `adverse_none_sentinel`); A2 via `resolve_legs`
(V2A legs via `leg_levels_from_fracs({1/3,2/3,1})`, 1:1 `adv_level`); A3 via `resolve_legs` (V2A legs, adverse
= `adverse_none_sentinel`); A4 = A3 with the floor=48 cap — then `weighted_returns` → `R_event` →
`qualifying_mask`; bootstrap per-cell median per arm (`bootstrap_median_distribution`, `median_ci`); paired
contrasts (`paired_median_contrast_ci` for the factorial main effects, interaction, vs-BENCH, and `A4−A3`;
`contrast_ci` for vs-baseline). Emit the binding champion-vs-baselines readout, the disclosed factorial
decomposition, exit-reason composition, and the horizon sibling; **do not adjudicate §8** (single 014-B G2
after the full slate).
