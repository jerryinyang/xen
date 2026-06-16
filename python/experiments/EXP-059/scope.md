# Experiment: EXP-059 — Position-Management Exits (Conditioned HA Harami; `/EXIT-PARTIAL`, `/EXIT-TRAIL-STRUCT`, individually and combined)

> **Mandatory-reading precondition (014-B, binding).** `014-A-conditioning-gap-and-validation-lessons.md`
> was read in full before this scope was written. EXP-059 is the **position-management exits** surface read
> (HYP-012, P14/P15/P16/P17/P18). The four mandatory rules are honoured as follows, recorded so Stage 4 can
> check:
> - **(a) conditioning** — honoured. The object measured is the **live `/STRONG`-conditioned HA harami**
>   (the actual family signal, identical population to EXP-053/054/055/056/057/058), not the raw harami or the
>   unconditioned ZigZag substrate. `/STRONG-STAT` (P7, live magnitude-percentile) is binding; `/STRONG-HA`
>   (P8) is a disclosed secondary arm. Only the **position-management exit machinery** (favourable-side scaled
>   exits and/or adverse-side structure trailing) is varied (OAT); the signal, anchor, and **third barrier**
>   are held at benchmark, and the favourable/adverse benchmark levels are held wherever an exit layer does not
>   replace them.
> - **(b) harami-anchor** — honoured. Entry is the **harami confirmation-bar real close** `C`, the family's
>   claimed lead point — *not* the ZigZag trend-change confirmation (the EXP-049 anchor). A forward ZigZag
>   trend-change is used only as an *exit* event (`/EXIT-PARTIAL` reversal leg), never as the entry.
> - **(c) position-in-move descriptive-only / never a live filter** — honoured. EXP-050's position metric is
>   not used. Every exit trigger (first-profitable-close, fractional targets, reversal event, structure
>   trailing stop) is acted on at a bar known forward-in-time after entry; no unconfirmed pivot is referenced.
> - **(d) expectancy / not first-hit `r`** — honoured. The binding endpoint is **median gross per-event
>   expectancy** (P14, ATR-normalised, P15 fills) of the **position-weighted realised return** (multi-leg
>   exits collapse to one per-event number). First-hit `r` is undefined/secondary for multi-leg exits and is
>   reported only for the single-leg benchmark arm; win rate and exit-reason composition are disclosed
>   secondaries. The metric is exactly the one P14 chose *because* partial exits and trailing stops cannot
>   express value under a first-hit rate (lessons §8.6) — this is the experiment that lever was designed for.
> EXP-059 does **not** treat the EXP-049 `r≈0.50` null or the EXP-050 front-loading as evidence against the
> family — those measured the *unconditioned* object.

**Phase / checkpoint:** `2026-06-14-014-ha-harami-substrate-and-capture` (014-B; G0-B PASS 2026-06-15).
**Family / candidate:** `CF-HA-HARAMI-001` (`REGISTERED`, OPEN) · `CF-HA-HARAMI-001/HYP-012` — EXP-059
(registered PLANNED, Phase 014-B batch, `multiplicity-registry.md` line 387). Exercises the registered
branches `CF-HA-HARAMI-001/EXIT-PARTIAL` (P17) and `CF-HA-HARAMI-001/EXIT-TRAIL-STRUCT` (P18).
**Surface role:** Surface read 4 of the 014-B post-lead slate — **position-management exits**, the lever P14
was created to measure. EXP-055 found the conditioned reversal move **is available** (AVAILABILITY_GOOD), and
EXP-053 found the conditioned signal has positive gross expectancy under a single benchmark geometry
(EVIDENCE_FOR). This experiment asks whether **scaling out of the favourable side** and/or **trailing the
adverse side on market structure** captures more of that available move (higher gross median expectancy) than
the single fixed benchmark exit. Sibling of EXP-056 (favourable) / EXP-057 (adverse) / EXP-058 (third
barrier); its survivors feed the combined-event system EXP-060 and G2.
**Governing design:** `014-B-design.md` (§2/§3/§5 surface row EXP-059, §6, §7, §8) + `014-B-D0-addendum.md`
(P14/P15/P16/P17/P18/P20); inherits Phase 014 `design.md` §8 D0 (P1–P13) and the family spec
`candidate-families/harami.md` (position-management branches `/EXIT-PARTIAL`, `/EXIT-TRAIL-STRUCT`).
**Operator scope decisions (2026-06-16, recorded before any data contact):** see §"Operator decisions".
**Reuses:** the EXP-053/056/057/058 conditioned-signal construction and benchmark/P15/P14 machinery
(`xen.expectancy.live_in_progress_state`, `live_strong_stat`, `adaptive_time_caps_by_epoch`,
`benchmark_barriers`, `resolve_path_ordered`, `realised_returns`, `qualifying_mask`,
`bootstrap_median_distribution`, `median_ci`, `contrast_ci`); the paired-median contrast bootstrap
(`xen.favourable_targets.paired_median_contrast_ci`); the forward `rd`-confirm locator pattern
(`xen.third_barrier.third_event_caps`); ZigZag (`xen.zigzag.generate_zigzag` — primary `atr_mult=1.0` and a
**second** `atr_mult=0.5` instance for the trailing structure), harami (`xen.ha_harami`), `/STRONG-HA`
(`xen.strong_move.annotate_ha_impulse`), confirmation indices (`xen.capture_barriers`).

## Operator decisions (2026-06-16, recorded before any data contact)

- **This is a predeclared position-management *sweep*, not a single comparison.** Every variant below is
  predeclared here; **no post-result variant selection** — every variant is reported and composed by P11;
  routing is the single 014-B G2 after the full slate (no intermediate gate, no early closure).
- **All exit schemes split the full entry weight into exactly 3 equal legs (`w = 1/3` each)** (P17 "≤3 equal
  parts"; fixed at 3 for every variant so the leg weighting is constant across the sweep). The single-leg
  benchmark is `w = 1` on one leg.
- **`/EXIT-PARTIAL` Variant #1 (event triggers)** — three legs exit on, respectively: **leg-1** the first bar
  whose real close is in profit (`rd·(close − C) > 0`); **leg-2** the benchmark 50% favourable target (P2);
  **leg-3** a **reversal event** = the *first of* (i) the next **primary-ZigZag** (`atr_mult=1.0`)
  trend-change confirmed with `Direction == rd` and `ConfirmTime > entry` (the fade-succeeded structural
  completion — **identical to the EXP-058 `/THIRD-EVENT` exit**), or (ii) the next `/STRONG`-conditioned HA
  harami whose reversal direction `== −rd` (a harami fading the rd reversal move, signalling the rd move is
  exhausting), confirmed after entry. **Directional-encoding note (transparent correction):** the Q1 preview
  shown to the operator illustratively labelled the reversal event `dir == -rd` for both arms; because leg-3
  is a **take-profit** leg, the correct fade-succeeded completion is the ZigZag arm `Direction == rd` and the
  opposing-harami arm reversal-direction `== −rd`. The operator approved "either trigger, whichever first";
  this scope encodes the correct take-profit semantics (a `−rd` ZigZag confirmation is the *adverse* event,
  already handled by the 1:1 stop, and is **not** a take-profit trigger). Stage 4 verifies the encoding.
- **`/EXIT-PARTIAL` Variant #2 (percentage-to-final-target) — test all three predeclared split grids as
  distinct variants** (operator: "test all options as different variants"). All three split the weight into 3
  equal legs; legs take profit at predeclared **multiples of the benchmark favourable distance**
  `fav_dist = 0.50 × M_sofar`:
  - **V2A (even thirds):** leg targets at `{1/3, 2/3, 3/3} × fav_dist` (final leg = the benchmark fav level).
  - **V2B (runner):** leg targets at `{0.5, 1.0, 1.5} × fav_dist` (final leg runs to 1.5× the benchmark
    distance; resolves on its extended target, the shared adverse stop, or the benchmark time cap).
  - **V2C (fixed + reversal runner):** legs 1–2 at `{1/3, 2/3} × fav_dist`; leg-3 is a **runner** exiting on
    the **reversal event** (same definition as V1 leg-3) — a V1/V2 hybrid.
- **`/EXIT-TRAIL-STRUCT` (adverse side = structure trailing stop on a smaller-ATR ZigZag, `ATR_MULT_TRAIL =
  0.5`, P18) — test all three favourable/initial-stop treatments as distinct variants** (operator:
  "`Pure trailing, no fixed TP` is the primary intended design, but test all these options"):
  - **TRAIL-PURE (primary):** **no fixed favourable target** (let the position run); single-leg position
    exiting only on a trailing-stop fill or the benchmark time cap. Initial stop = the benchmark 1:1 adverse
    level until the first secondary-ZigZag pivot confirms after entry, then the stop ratchets.
  - **TRAIL-TP-INIT:** retain the benchmark 50% favourable take-profit (P2); initial stop = benchmark 1:1,
    then ratchet.
  - **TRAIL-TP-NOINIT:** retain the benchmark 50% take-profit; **no adverse stop** until the first
    secondary-ZigZag pivot confirms after entry (unstopped early — acceptable, gross-only), then ratchet.
- **Trailing-stop ratchet rule (binding predeclaration; derived from "trailing stop" semantics).** The active
  stop is **monotone — it never loosens**. For a long fade (`rd=+1`): on a newly confirmed secondary-ZigZag
  **pivot high** (an `atr_mult=0.5` up-move confirmed, `ConfirmTime ≤` the current bar), set
  `stop ← max(stop, most-recent confirmed secondary pivot low)`. For a short fade (`rd=−1`): on a newly
  confirmed **pivot low**, set `stop ← min(stop, most-recent confirmed secondary pivot high)`. The stop level
  in force at any bar uses only secondary-ZigZag moves with `ConfirmTime ≤ CloseTime` of that bar (causal —
  pivots are retroactively located, so the stop moves at the *confirmation* bar, never at the pivot bar).
- **`/EXIT-TRAIL-STRUCT` favourable side held at benchmark where present; the third barrier (adaptive time
  cap, P4 benchmark) is held at benchmark for *every* arm.** EXP-059 is pure OAT on the position-management
  exit machinery. The horizon lever is EXP-058 (`/THIRD-TIME`, `/THIRD-EVENT`); combining the best position
  management with the best third barrier is **EXP-060**, not here. **Consequence disclosed:** because the
  benchmark cap collapsed to the 6-bar floor in 96/99 cells (014-A G1), the reversal-event legs (V1 leg-3,
  V2C runner) and the runner target (V2B) are bounded by ~6 bars in most cells; many will exit at the time
  cap rather than the reversal/extended trigger. This is the intended clean-OAT measurement (does scaling/
  trailing help *within the benchmark horizon*?); the horizon×position-management interaction is EXP-060.
- **Combined arms (`/EXIT-PARTIAL` ⊕ `/EXIT-TRAIL-STRUCT`)** — the favourable side is the partial-exit legs
  and the adverse side is the structure trailing stop (replacing the benchmark 1:1 stop that otherwise binds
  open legs). Combine **each of the 4 partial-favourable schemes** (V1, V2A, V2B, V2C) with the structure
  trailing adverse using the **benchmark-1:1 initial stop** then ratchet (one fixed trailing treatment for
  the combined set — the standalone TRAIL arms already characterise the init-stop sensitivity, so combined
  does not re-sweep it). Third barrier (time cap) at benchmark. 4 combined arms.
- **Binding comparison = each variant vs the BENCH single-geometry reference** (the EXP-053 benchmark: fav
  50%, adv 1:1, adaptive time cap, single leg) via the paired-median contrast on the common qualifying-event
  subset — identical contrast design to EXP-056/057/058.

**Full predeclared binding-arm set (12 arms; each on the binding `/STRONG-STAT` population, with `/STRONG-HA`
disclosed and both P13 baselines):**

| # | Arm id | Favourable side | Adverse side | Third barrier | Notes |
|---|--------|-----------------|--------------|---------------|-------|
| 1 | `BENCH` | 50% fav (1 leg) | 1:1 stop | adaptive cap | reference; reproduces EXP-053 benchmark |
| 2 | `PARTIAL-V1` | legs {first-profit-close, 50% fav, reversal-event} | 1:1 stop (all open legs) | adaptive cap | event-trigger partials |
| 3 | `PARTIAL-V2A` | legs at {1/3, 2/3, 3/3}×fav_dist | 1:1 stop | adaptive cap | even-thirds |
| 4 | `PARTIAL-V2B` | legs at {0.5, 1.0, 1.5}×fav_dist | 1:1 stop | adaptive cap | runner to 1.5× |
| 5 | `PARTIAL-V2C` | legs {1/3, 2/3}×fav_dist + reversal-event runner | 1:1 stop | adaptive cap | fixed+reversal runner |
| 6 | `TRAIL-PURE` | none (let it run, 1 leg) | structure trail (1:1 init) | adaptive cap | **primary trailing intent** |
| 7 | `TRAIL-TP-INIT` | 50% fav (1 leg) | structure trail (1:1 init) | adaptive cap | TP + trail |
| 8 | `TRAIL-TP-NOINIT` | 50% fav (1 leg) | structure trail (no init stop) | adaptive cap | TP + trail, unstopped early |
| 9 | `COMBINED-V1` | V1 partial legs | structure trail (1:1 init) | adaptive cap | partial fav + trail adverse |
| 10 | `COMBINED-V2A` | V2A partial legs | structure trail (1:1 init) | adaptive cap | |
| 11 | `COMBINED-V2B` | V2B partial legs | structure trail (1:1 init) | adaptive cap | |
| 12 | `COMBINED-V2C` | V2C partial legs | structure trail (1:1 init) | adaptive cap | |

## Slot & ledger accounting (binding)

- **0 candidate slots, 0 TEST reads.** Characterization/diagnostic per the 014-B D0 addendum
  (`014-B-D0-addendum.md` slot & ledger accounting). The `/EXIT-PARTIAL` and `/EXIT-TRAIL-STRUCT` branches are
  registered but consume a slot only when a future scope activates one as a screening candidate — which, per
  P21, cannot happen before G2 PROCEED_TO_SCREEN.
- **No TEST stratum is read.** All work is on the **TRAIN** slice (first 70% of the first-70% analysis set),
  identical fence to EXP-049/053/054/055/056/057/058. **The TEST-read ledger requires no entry and none is
  created; the current counted-read tally is irrelevant because no TEST stratum is touched.** The conditioned
  HA-harami event population already had its first new-universe TRAIN contact in EXP-053 (same definition); no
  new stratum is opened and the global-holdout seal carries forward unchanged. **Forward scans** (reversal-
  event legs, runner targets, trailing-stop ratchet, time caps) run only within the TRAIN slice and are
  clipped to the TRAIN data edge — a window that would extend past `train_end_ts` is `DATA_CENSORED`, never
  resolved against TEST/holdout rows.
- All work is **gross** (no costs). Detection on HA candles; **every outcome metric on real prices**
  (`RealOpen/High/Low/Close` domain-bar OHLC), never HA prices.

---

## Hypothesis

For the live `/STRONG`-conditioned HA harami (anchored at the harami confirmation-bar close, faded against the
in-progress strong move, third barrier held at the benchmark adaptive time cap), **at least one
position-management exit scheme** — favourable-side scaled exits (`/EXIT-PARTIAL` V1, V2A, V2B, V2C),
adverse-side structure trailing (`/EXIT-TRAIL-STRUCT` PURE, TP-INIT, TP-NOINIT), or their combination
(COMBINED-V1/V2A/V2B/V2C) — produces **higher gross per-event median expectancy** (P14, ATR-normalised,
position-weighted realised return, P15 fills, real prices) than the **benchmark single fixed exit**
(50% fav / 1:1 stop / adaptive cap, single leg), on the binding `/STRONG-STAT` arm.

Falsifiable: if **no** position-management arm clears the P11 quorum (≥5 cells over ≥3 instruments with
CI_low > 0 on its own median expectancy) **and** beats the benchmark arm (variant − benchmark paired contrast
CI_low > 0 in the quorum), then position-management exit machinery is **not** a lever that improves
conditioned capture on benchmark barrier geometry (a valid characterization result that feeds G2 — never a
closure inside 014-B).

## Question

Does replacing the benchmark single fixed exit with **scaled favourable take-profits** (event-trigger or
fraction-of-target legs, with or without a reversal-event runner) and/or an **adverse-side market-structure
trailing stop** (0.5×ATR ZigZag, with or without a fixed favourable target) raise the conditioned
HA-harami's gross per-event median expectancy vs the benchmark, per cell and composed across the grid, and
which scheme (if any) wins? At what cost in qualifying-event **count** (scaled/trailing exits add
construction and warmup exclusions) and in **exit-reason composition** (which legs/stops actually bind —
disclosed secondaries)?

---

## Scope Boundaries

### Data Views

- **Real domain bars** (5m strict; 15m/30m/1h/2h/4h via `xen.bar_aggregator.aggregate_ohlc`,
  `min_coverage=0.90` — identical to EXP-048/049/053–058/VAL-004) for the primary ZigZag substrate
  (`atr_mult=1.0`), the **secondary trailing ZigZag** (`atr_mult=0.5`), confirmed moves, strong-move
  magnitudes, the benchmark third-barrier cap, all barrier/leg/stop levels, P15 fills, ATR normalisation, and
  **all** outcome metrics.
- **Heiken Ashi candles** (`xen.heiken_ashi_generator`, from the same domain bars) for **harami detection
  only** (`xen.ha_harami.detect_ha_harami`, frozen EXP-048 detector) — including the opposing-harami arm of
  the reversal-event trigger. **No HA price enters any metric.**

### Event population (the live conditioned signal — identical to EXP-053/054/055/056/057/058)

- An HA harami (frozen detector) **AND** the live `/STRONG-STAT` magnitude-percentile filter: the in-progress
  confirmed-ZigZag move's **magnitude-so-far** `M_sofar = |C − start_pivot|` (last *confirmed* pivot → harami
  real close `C`) is **≥ p75** of the trailing-20 confirmed-move magnitudes (P7, binding). `/STRONG-HA` (P8:
  run of `X=3` large-body HA bars, no opposing wick) is a **disclosed secondary** arm run through the
  identical pipeline.
- **Trade / reversal direction** `rd = Direction_k` of the last confirmed primary-ZigZag move
  (`xen.expectancy.live_in_progress_state`; in-progress trend `= −Direction_k`, so the reversal/fade trade is
  in `rd`). No `/BARCFG` isolation; all qualifying haramis count.
- Construction reuses `xen.expectancy.live_in_progress_state` + `live_strong_stat` — the **same functions
  EXP-053/056/057/058 used** — so the binding population is byte-identical to EXP-053's conditioned events
  (verified by population reconciliation).

### Entry anchor

The **harami confirmation-bar real close** `C` (real domain-bar close at the harami timestamp), strictly
before any ZigZag trend-change confirmation. Identical to EXP-053/055/056/057/058.

### Position-management exit variants (predeclared sweep; OAT on the exit machinery only)

Notation: `C` = entry close; `rd` = trade direction; `M_sofar` = magnitude-so-far; `fav_dist = 0.50·M_sofar`
(P2); `fav = C + rd·fav_dist` (benchmark favourable level); `adv = C − rd·fav_dist` (benchmark 1:1 adverse
level); `bench_N` = benchmark P4 adaptive cap (floor=6). Every leg/stop is evaluated on **real prices** under
the **P15 path model** (bullish bar `Close ≥ Open`: `O→L→H→C`; bearish: `O→H→L→C`). Every arm's forward scan
runs `[entry_idx+1, entry_idx + bench_N]` (the benchmark time cap), TRAIN-fenced; a window truncated by the
edge before all legs/the position resolve is `DATA_CENSORED` (excluded-with-record, disclosed).

**Benchmark reference (arm 1) —** single leg, `w=1`: `resolve_path_ordered` with `(fav, adv, bench_N)`
(`xen.expectancy`), exactly EXP-053's benchmark. Reproduces EXP-053 per-cell median expectancy and `r≈0.50`
(invariant check).

**`/EXIT-PARTIAL` (arms 2–5) —** full weight in **3 equal legs** (`w=1/3`). All open legs share the
**benchmark 1:1 adverse stop** `adv` (if `adv` is reached first along the P15 path at any bar, every still-open
leg exits at `adv`) and the **benchmark time cap** (still-open legs exit at the cap bar's real close). Each
leg's favourable trigger:
- **V1 (arm 2):** leg-1 = first bar with `rd·(close − C) > 0` → exit at that `close`; leg-2 = `fav` (P15
  intrabar touch); leg-3 = reversal event = first of {primary-ZigZag `Direction==rd` confirm with
  `ConfirmTime>entry`; opposing conditioned harami reversal-dir `−rd` confirmed after entry} → exit at that
  confirmation bar's real `close` (bounded by the time cap; reuses the `third_event_caps` forward-locator
  pattern for the ZigZag arm).
- **V2A (arm 3):** legs at `{1/3, 2/3, 1} × fav_dist` favourable distance → levels `C + rd·frac·fav_dist`
  (P15 intrabar touch).
- **V2B (arm 4):** legs at `{0.5, 1.0, 1.5} × fav_dist` favourable distance (the 1.5× leg is a runner).
- **V2C (arm 5):** legs 1–2 at `{1/3, 2/3} × fav_dist`; leg-3 runner = reversal event (V1 leg-3 definition).

**`/EXIT-TRAIL-STRUCT` (arms 6–8) —** single position (`w=1`); adverse side = the monotone structure trailing
stop on the **secondary `atr_mult=0.5` ZigZag** (ratchet rule in §Operator decisions); favourable/initial-stop
per arm:
- **TRAIL-PURE (arm 6, primary):** no favourable target; initial stop `adv` (benchmark 1:1) until the first
  secondary pivot confirms after entry, then ratchet; exit on trailing-stop fill or time cap.
- **TRAIL-TP-INIT (arm 7):** favourable target `fav`; initial stop `adv`; ratchet; exit on fav touch,
  trailing-stop fill, or time cap (P15 path order resolves same-bar fav-vs-stop).
- **TRAIL-TP-NOINIT (arm 8):** favourable target `fav`; **no stop** until the first secondary pivot confirms,
  then ratchet; exit on fav touch, trailing-stop fill, or time cap.

**Combined (arms 9–12) —** `/EXIT-PARTIAL` favourable legs (V1, V2A, V2B, V2C respectively) **⊕** the
structure trailing adverse stop (1:1 init, ratchet) replacing the benchmark 1:1 stop that binds open legs;
time cap at benchmark. Leg favourable triggers exactly as the corresponding partial arm.

**Per-event realised return (binding endpoint input).** For every arm the per-event realised gross return is
the **position-weighted** sum of leg returns: `R_event = Σ_l w_l · rd·(exit_px_l − C)/ATR_entry`, where each
leg's `exit_px_l` is its P15 fill (favourable level, shared adverse/trailing stop, reversal-event/cap close),
`Σ_l w_l = 1`, and `ATR_entry` = Wilder ATR(14) at the harami entry bar (P14). Single-leg arms (BENCH,
TRAIL-*) are the `w=1` special case. `R_event` is the per-event value fed to the median bootstrap and the
paired contrast — the same statistical machinery as EXP-056/057/058, only the per-event value construction
changes.

### Parameters (all frozen D0 / predeclared this scope; no tuning)

Primary ZigZag Wilder ATR(14), `ATR_MULT = 1.0` (P1); **secondary trailing ZigZag Wilder ATR(14),
`ATR_MULT_TRAIL = 0.5` (P18)**; `/STRONG-STAT` trailing-20, ≥p75 (P7); `/STRONG-HA` `X=3` (P8); benchmark
favourable `X = 50%` of `M_sofar` (P2); benchmark adverse 1:1 (P3); benchmark time cap
`(k=1.5, window=20, floor=6, statistic=median, min_moves=5)` (P4) for every arm; ATR-normalisation divisor =
Wilder ATR(14) at the harami entry bar (P14); bootstrap `b = round(m^(1/3))`, `N_BOOT = 10_000`, fixed seed
(P14). **New predeclared position-management parameters (this scope):** 3 equal legs (`w=1/3`); V1/V2C
reversal-event = first of {primary-ZigZag `Direction==rd` confirm; opposing conditioned harami reversal-dir
`−rd`}, bounded by the benchmark cap; V2A fractions `{1/3, 2/3, 1}`; V2B fractions `{0.5, 1.0, 1.5}`;
trailing-stop monotone ratchet to the most-recent confirmed secondary pivot; initial-stop treatments
{1:1, none} per arm. None is tuned against outcomes; no grid is swept beyond this predeclared set.

### Instruments / cells

The **99-cell EXP-049/053–058 member grid**: 17 instruments × {5m,15m,30m,1h,2h,4h} minus the 3
COVERAGE_EXCLUDED cells (US500-4h, JP225-2h, JP225-4h). Per-cell first, then **P11** composition (≥5 cells
over ≥3 instruments) for any "winning arm" claim. Full-grid breadth required by P11 and the "no blanket
assumptions" principle. DE30 carries the truncated-coverage disclosure.

### Time range

Full dataset, nested chronological split. **TRAIN only** = first 70% of the first-70% analysis set (per cell,
F01 file-order-prefix convention identical to EXP-049/053–058: `train_end_ts` = last `CloseTime` of the first
`int(int(total_rows*0.7)*0.7)` file-order 1-minute rows). TEST (last 30% of the analysis set) and the
final-30% **global holdout** are **not** read. All forward windows (legs, reversal events, trailing ratchet,
caps) are clipped to `train_end_ts`; an unresolved truncated window is `DATA_CENSORED` (disclosed), never
resolved past the edge.

### Baselines (P13 / P20 — disclosed secondaries)

- **Matched-count random in-regime timestamps** (same cell/regime/direction, EXP-021/027 exclusion
  convention) run through the **identical exit pipeline** for each arm — does a given position-management
  scheme beat random entries under the same scheme?
- **MA(20,50) segmentation** (alternative trend substrate, EXP-050/053 baseline): conditioned-harami
  expectancy under MA-segmented moves for each arm, disclosed. For arms whose reversal-event leg uses the
  primary ZigZag, the MA-seg baseline uses the analogous MA-segment confirmation in direction `rd`; the
  secondary trailing structure for the MA-seg baseline uses the same `atr_mult=0.5` ZigZag (the trailing
  structure is a real-bar construct independent of the entry segmentation).
- Baselines are disclosed secondaries; the binding readout is each arm's own median expectancy and the
  arm − benchmark paired contrast.

### Look-ahead / causality discipline (binding)

- Primary and secondary ZigZag pivots are future information until confirmed. The signal
  (harami + `/STRONG-STAT`), `M_sofar`, the favourable/adverse benchmark levels, the leg targets, and the
  benchmark time cap use **only** confirmed, completed prior moves and **real bars at or before the entry
  bar** for *construction at entry*.
- Every exit is a **forward** event acted on at a bar known going forward in real time: first-profitable
  close (at the bar close), fractional-target touch (intrabar P15), reversal event (at the confirmation bar's
  close — primary-ZigZag `Direction==rd` confirm or opposing-harami confirm, never an unconfirmed pivot), and
  the structure trailing stop (the stop level in force at bar `t` uses only secondary-ZigZag moves with
  `ConfirmTime ≤ CloseTime(t)` — the stop moves at the confirmation bar, never the retroactive pivot bar).
- The trailing ratchet is monotone (never loosens) and uses only confirmed secondary pivots; the forward scan
  reads only bars `[entry_idx+1, min(entry_idx+bench_N, last_train_idx)]`, fenced `CloseTime ≤ train_end_ts`;
  a window truncated before resolution is `DATA_CENSORED` (excluded, disclosed).
- Ordering/alignment by `CloseTime`, never bar index across views (primary ZigZag, secondary ZigZag, HA
  candles, and real bars are aligned by `CloseTime`).

### Real-price outcome discipline

Harami detected on HA candles; `M_sofar`, ATR normalisation, all benchmark/leg/stop levels, the secondary
trailing ZigZag, P15 fills, weighted expectancy, win rate, and exit-reason composition on real domain-bar
OHLC. **No HA price in any metric** (the opposing-harami reversal arm uses HA candles only to *locate* the
exit bar, then exits at that bar's **real** close).

### Exclusions

- No costs (gross only).
- **Position-management exits only.** Favourable benchmark level (50%), adverse benchmark level (1:1 — except
  where the trailing stop replaces it), and the third barrier (adaptive cap) are held at benchmark; no
  `/VPTARGET`/`/MAGTARGET` (EXP-056), no `/ADV-EXTREME`/`/ADV-NONE` (EXP-057), no `/THIRD-TIME`/`/THIRD-EVENT`
  horizon change (EXP-058 — the third barrier is benchmark for every arm; the reversal-event leg is bounded by
  the benchmark cap), no combined-system optimisation across all layers (EXP-060). No `/BARCFG`/`/CONFIRM`
  overlays; no position-in-move *filter*. No `ATR_MULT_TRAIL` sensitivity grid (the registered
  `/THIRD-TIME`-analog sensitivity is out of this scope; `0.5` is the frozen P18 default).
- No parameter tuning; **no post-result variant selection** (all 12 predeclared arms reported); no gate
  adjudication (single G2 after the full 014-B slate — EXP-059 emits a characterization readout only).
- No TEST or holdout contact; no candidate slot; no TEST read.

## Success / Failure Criteria

All criteria are **gross**, per-cell first, composed by **P11** (≥5 cells over ≥3 instruments). The binding
endpoint is **median per-event position-weighted gross expectancy** `E_cell` (ATR units, P15 fills), on the
**`/STRONG-STAT` arm**; per-cell viable iff **CI_low > 0** (regime-clustered moving-block bootstrap, one-sided
95%) **AND ≥ 30 qualifying events**.

- **EVIDENCE_FOR (a position-management scheme helps):** ≥1 arm (2–12) **(a)** clears P11 on its own median
  expectancy **AND (b)** beats the benchmark arm on the **arm − benchmark contrast** (paired contrast CI_low >
  0 on the common qualifying-event subset) within the P11 quorum (matched cells). The winning arm(s) and their
  margin over benchmark are the deliverable; no candidate registration (G2 only).
- **EVIDENCE_AGAINST (position management is not a lever):** no alternative arm both clears P11 and beats the
  benchmark contrast. Recorded as a measured-negative characterization; routing deferred to G2 across the full
  slate.
- **INCONCLUSIVE (power-limited):** fewer than the P11 quorum of cells reach ≥30 qualifying events on the arms
  of interest (scaling/trailing construction + warmup exclusions deplete counts), no correctness failure.
  Disclosed; never defaulted to a ratio.
- **SUBSTRATE/METHOD_DEFECT:** any determinism, causality, or invariant failure → fix before reporting.
  Invariant checks include: (i) the BENCH arm reproduces EXP-053 per-cell median expectancy and qualifying
  count to tolerance; (ii) population reconciliation vs EXP-053 exact (the conditioned `/STRONG-STAT`
  population is identical); (iii) leg weights sum to 1.0 for every arm, and a degenerate single-trigger arm
  (all 3 legs sharing one trigger) reproduces the equivalent single-leg arm's `R_event` to float precision;
  (iv) the trailing stop is monotone (never loosens) and changes level **only** on secondary-ZigZag
  confirmation bars (`ConfirmTime ≤ CloseTime`); (v) every exit price is a real-bar P15 fill and every exit
  bar has `CloseTime ≤ train_end_ts`; (vi) the shared adverse stop, when it binds, closes all still-open
  partial legs at the same bar/level.

The deliverable label is **POSITION_MGMT_CHARACTERISED** carrying the per-cell + P11 readout for every arm,
the EVIDENCE_* classification, the benchmark contrast per arm, both filter arms (`/STRONG-STAT` binding,
`/STRONG-HA` disclosed), both P13 baselines, and all disclosed secondaries (per-arm qualifying-event count and
`DATA_CENSORED`/warmup exclusion counts; **exit-reason composition** — the fraction of weight exiting via each
leg trigger / shared stop / trailing stop / time cap; win rate; mean per-event return; first-hit `r` for the
BENCH single-leg arm only; `/STRONG-HA` arm; MAD `/STRONG-STAT` sensitivity arm). No phase closure or
candidate registration here.

## Complexity Budget

- **Max distinct statistical methods: 4** — identical to EXP-056/057/058: (1) regime-clustered moving-block
  bootstrap CI on an arm's median expectancy per cell (`xen.expectancy.bootstrap_median_distribution` +
  `median_ci`); (2) the same on each P13 baseline; (3) arm − benchmark paired-median contrast CI
  (`xen.favourable_targets.paired_median_contrast_ci`, common qualifying-event subset); (4) arm − baseline
  contrast CI (`xen.expectancy.contrast_ci`). These four methods are applied across the predeclared 12-arm set
  (a parameterised sweep over one experiment, not new methods per arm) — consistent with the 014-B surface
  design and the EXP-056/057/058 precedent.
- **Max visualisations: 5** — (i) per-arm median-expectancy forest/CI per cell vs benchmark; (ii) arm −
  benchmark contrast heatmap (arms × cells); (iii) expectancy distribution by arm (pooled); (iv) P11
  composition / "wins-over-benchmark" map across arms; (v) **exit-reason composition by arm** (which legs/
  stops bind — the mechanism diagnostic) alongside per-cell qualifying-event counts. Secondary tables to CSV.
- **Max new code modules: 1** — a bounded **position-management exits** helper (`position_exits.py`) supplying
  (a) the **multi-leg P15 partial-exit resolver** (per event, assign each leg its P15 fill given its
  favourable trigger, the shared adverse stop, and the time cap; handle first-profitable-close and
  reversal-event legs; return per-leg exit classes/prices and the weighted `R_event`), (b) the **structure
  trailing-stop builder + P15 trailing resolver** (derive the causal monotone active-stop step function from
  the secondary ZigZag's confirmed pivots; resolve fav-vs-trail-vs-cap under P15), and (c) thin per-arm
  composition wrappers. The benchmark single-leg resolver, fills, realised returns, qualifying mask, median
  bootstrap, contrasts, ZigZag, harami, strong-move, confirmation-index, in-progress-state, and the
  `third_event_caps` forward-locator pattern are **reused** from existing `xen` modules. Orchestration in
  `code/run_experiment.py`.

## Metric Denominators & Zero-Baseline

- **Per-event realised gross return** (ATR units) is the position-weighted `R_event` (above), defined for
  every **qualifying** event of an arm — an event whose barriers/legs are constructible (`fav_dist > 0`,
  finite positive `ATR_entry`, and, for trailing arms, the secondary ZigZag available) and whose every leg /
  the position reaches a finite P15 exit (favourable trigger, shared adverse/trailing stop, reversal-event/cap
  close) within the TRAIN-fenced window. `DATA_CENSORED` (any leg's window truncated by the TRAIN edge before
  resolution) and construction-warmup events are **excluded** from the median and **disclosed as counts** per
  cell per arm.
- **Per-cell endpoint (binding):** `E_cell = median` over the arm's qualifying-event `R_event` population.
  Because every arm retains the benchmark time cap as the ultimate backstop, qualifying counts and censoring
  stay comparable to the EXP-053 benchmark; trailing arms additionally exclude events with no secondary-ZigZag
  pivot history (warmup), disclosed.
- **Zero-baseline / power:** a cell with **< 30 qualifying events** for an arm is **NOT_VIABLE-by-power** for
  that arm (non-reportable for its readout), never an undefined or infinite ratio. Conditioning + per-arm
  construction/warmup/censoring exclusions reduce counts vs the unconditioned base; depleted cells are
  disclosed, never defaulted.
- **Exit-reason composition** is computed and reported per arm as a **disclosed secondary**: the fraction of
  position weight exiting via each leg's favourable trigger, the shared adverse/trailing stop, the
  reversal-event, and the time cap. This is the binding *mechanism* diagnostic (how the scheme actually
  realises P&L) but never enters viability.
- **First-hit `r`** is defined only for the single-leg **BENCH** arm (`r = n_FAV/(n_FAV+n_ADV)`, TIMECAP
  excluded, EXP-049 convention) and reported as a disclosed secondary anchor (expected ≈0.50, replicating
  EXP-049/053). For multi-leg / trailing arms `r` is undefined (the mechanism is multi-exit by construction)
  and is **not** reported as viability — exactly the P14 rationale for this experiment.
- **Disclosed secondaries (never binding):** per-arm qualifying count, `DATA_CENSORED`/warmup exclusion
  counts, exit-reason composition, win rate, mean per-event return, BENCH first-hit `r`, the `/STRONG-HA` arm,
  both P13 baselines, the MAD `/STRONG-STAT` sensitivity arm.

## Data Requirements

Per cell (instrument × domain), TRAIN slice only: lazy `pl.scan_parquet`; read total row count;
`analysis_rows = int(total_rows*0.7)`, `train_rows = int(analysis_rows*0.7)`; collect only the first
`train_rows` file-order 1-minute rows (F01 prefix; never sort/collect the full file, never read TEST or
holdout); assert chronological; `train_end_ts` = last `CloseTime`. Aggregate each member domain (5m strict;
others `min_coverage=0.90`); fence to `CloseTime ≤ train_end_ts`; generate HA candles; run the **primary**
`xen.zigzag.generate_zigzag(bars, atr_period=14, atr_mult=1.0)` → confirmed moves +
`xen.capture_barriers.confirm_indices`, and the **secondary** `generate_zigzag(bars, atr_period=14,
atr_mult=0.5)` → secondary confirmed moves/pivots + their confirm indices (for the trailing stop); detect
haramis on HA candles aligned by `CloseTime`; build the live in-progress state + `/STRONG-STAT`/`/STRONG-HA`
conditioning (`xen.expectancy`); compute the benchmark favourable + adverse levels + adaptive cap; for each of
the 12 arms compute per-event leg/stop exits via the new `position_exits` resolvers (partial legs and/or
structure trailing) under P15, the weighted `R_event`, the qualifying mask, bootstrap the per-cell median per
arm, compute both P13 baselines through the identical per-arm pipeline, compose by P11; second full pass for
determinism. `tqdm` over the 99-cell grid; **bounded per-cell memory** (do not retain all domain frames or all
bootstrap draws; per-event forward scans are bounded by `bench_N` ≈ 6 bars in most cells); fixed seed;
deterministic. Outputs (`results/`): `per_cell_expectancy.parquet` (per cell × arm: median/CI expectancy,
paired contrast vs benchmark, n_qualifying, censoring/warmup counts, exit-reason composition, win rate,
baseline medians/contrasts, viability flag); `position_mgmt_map.csv` (binding `/STRONG-STAT` summary per arm);
`secondary_map.csv` (`/STRONG-HA`, MAD arm, baselines, BENCH `r`, exit-reason composition);
`composition_readout.json` (per-arm P11, wins-over-benchmark, EVIDENCE_* fork);
`population_reconciliation.csv` (binding conditioned population vs EXP-053; BENCH expectancy/`r`/count vs
EXP-053); `run_metadata.json` (seed, frozen + new predeclared constants, EXP-053 source paths/hashes). Bounded
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

Compose existing primitives; the only new code is the bounded `position_exits.py` module (multi-leg P15
partial-exit resolver + structure trailing-stop builder/resolver). Pipeline per cell:
`xen.zigzag.generate_zigzag` (primary 1.0 + secondary 0.5) → confirmed moves +
`xen.capture_barriers.confirm_indices`; `xen.heiken_ashi_generator` + `xen.ha_harami.detect_ha_harami`
→ harami entry bars (aligned by `CloseTime`); `xen.expectancy.live_in_progress_state` + `live_strong_stat`
→ the binding conditioned population (identical to EXP-053; cross-checked by `population_reconciliation`);
`xen.strong_move.annotate_ha_impulse` → the `/STRONG-HA` arm. For each qualifying harami: compute the
benchmark levels + adaptive cap (`benchmark_barriers`, `adaptive_time_caps_by_epoch`); build each arm's
per-event exits — BENCH via `resolve_path_ordered`; PARTIAL/COMBINED via the new multi-leg resolver (legs +
shared stop/trail + cap, P15); TRAIL via the new trailing builder/resolver; reversal-event legs reuse the
`third_event_caps` forward-locator (primary ZigZag `Direction==rd`) plus an opposing-harami locator — then
`realised_returns`-style weighted `R_event` → `qualifying_mask`; bootstrap per-cell median per arm
(`bootstrap_median_distribution`, `median_ci`); paired contrast vs benchmark
(`xen.favourable_targets.paired_median_contrast_ci`) and vs baselines (`xen.expectancy.contrast_ci`). Emit the
layered per-arm P11 / wins-over-benchmark / EVIDENCE_* readout plus the binding exit-reason composition
disclosure; **do not adjudicate §8** (single 014-B G2 after the full slate).
