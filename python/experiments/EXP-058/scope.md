# Experiment: EXP-058 — Third-Barrier Geometry (Conditioned HA Harami; `/THIRD-TIME`, `/THIRD-EVENT` vs Benchmark Adaptive Cap)

> **Mandatory-reading precondition (014-B, binding).** `014-A-conditioning-gap-and-validation-lessons.md`
> was read in full before this scope was written. EXP-058 is the **third-barrier geometry** surface read
> (HYP-011, P14/P16). The four mandatory rules are honoured as follows, recorded so Stage 4 can check:
> - **(a) conditioning** — honoured. The object measured is the **live `/STRONG`-conditioned HA harami**
>   (the actual family signal, identical population to EXP-053/054/055/056/057), not the raw harami or the
>   unconditioned ZigZag substrate. `/STRONG-STAT` (P7, live magnitude-percentile) is binding; `/STRONG-HA`
>   (P8) is a disclosed secondary arm. Only the **third barrier** is varied (OAT); the signal, anchor,
>   favourable target, adverse target, and fills are held at benchmark.
> - **(b) harami-anchor** — honoured. Entry is the **harami confirmation-bar real close** `C`, the family's
>   claimed lead point — *not* the ZigZag trend-change confirmation (the EXP-049 anchor). The ZigZag
>   trend-change is used by `/THIRD-EVENT` only as a forward **exit** event (a future-confirmed structural
>   close-out of a position already entered at the harami), never as the entry.
> - **(c) position-in-move descriptive-only / never a live filter** — honoured. EXP-050's position metric is
>   not used. The `/THIRD-EVENT` exit uses the next ZigZag move confirmed (with `ConfirmTime > entry`) in the
>   reversal direction — a quantity that becomes known forward-in-time after entry and is acted on at the
>   confirmation bar (exactly as the benchmark TIMECAP acts at a forward bar), never an unconfirmed pivot.
> - **(d) expectancy / not first-hit `r`** — honoured. The binding endpoint is **median gross per-event
>   expectancy** (P14, ATR-normalised, P15 fills), with first-hit `r` and **censoring fraction** retained as
>   **disclosed secondaries**. The third barrier governs the "neither target hit" exit (and, via censoring,
>   the qualifying denominator), so the censoring fraction is reported prominently — but it never binds.
> EXP-058 does **not** treat the EXP-049 `r≈0.50` null or the EXP-050 front-loading as evidence against the
> family — those measured the *unconditioned* object.

**Phase / checkpoint:** `2026-06-14-014-ha-harami-substrate-and-capture` (014-B; G0-B PASS 2026-06-15).
**Family / candidate:** `CF-HA-HARAMI-001` (`REGISTERED`, OPEN) · `CF-HA-HARAMI-001/HYP-011` — EXP-058
(registered PLANNED, Phase 014-B batch, `multiplicity-registry.md` line 386). Exercises the registered
branches `CF-HA-HARAMI-001/THIRD-TIME` and `CF-HA-HARAMI-001/THIRD-EVENT`.
**Surface role:** Surface read 3 of the 014-B post-lead slate — third-barrier geometry comparison. The
lever motivated directly by 014-A G1 and EXP-055: the benchmark P4 cap collapsed to the **6-bar floor in
96/99 cells**, yet EXP-055 found the lifetime reversal move **is available** (AVAILABILITY_GOOD). This
experiment asks whether *extending the holding horizon* (time or structural event) converts that available
move into higher gross expectancy, and at what censoring cost. Sibling of EXP-056 (favourable) / EXP-057
(adverse).
**Governing design:** `014-B-design.md` (§2/§3/§5 surface, §7, §8) + `014-B-D0-addendum.md`
(P14/P15/P16/P20); inherits Phase 014 `design.md` §8 D0 (P1–P13) and the family spec
`candidate-families/harami.md` (third-barrier variants `/THIRD-EVENT`, `/THIRD-TIME`).
**Operator scope decisions (2026-06-16, recorded before any data contact):** see §"Operator decisions".
**Reuses:** the EXP-053/056/057 conditioned-signal construction and P15/P14 resolver
(`xen.expectancy.live_in_progress_state`, `live_strong_stat`, `adaptive_time_caps_by_epoch`,
`benchmark_barriers`, `resolve_path_ordered`, `realised_returns`, `qualifying_mask`,
`bootstrap_median_distribution`, `median_ci`, `contrast_ci`); the paired-median contrast bootstrap
(`xen.favourable_targets.paired_median_contrast_ci`); ZigZag (`xen.zigzag`), harami (`xen.ha_harami`),
`/STRONG-HA` (`xen.strong_move.annotate_ha_impulse`), confirmation indices (`xen.capture_barriers`).

## Operator decisions (2026-06-16, recorded before any data contact)

- **This is a predeclared third-barrier *sweep*, not a single comparison.** All variants are predeclared
  here; **no post-result variant selection** — every variant is reported and composed by P11; final routing
  is the single 014-B G2.
- **`/THIRD-TIME` grid = raise the floor only, `k=1.5` and `window=20` fixed.** The benchmark adaptive cap
  is `N = max(6, round(1.5 × median(trailing-20 confirmed-move durations)))` (P4). The `/THIRD-TIME`
  variants change **only the floor**: `floor ∈ {6 (BENCH), 12, 24, 48}` → `N_v = max(floor_v,
  round(1.5 × median(durations)))`. Operator rationale (recorded): the binding constraint is the floor
  (P4 collapsed to floor=6 in 96/99 cells per 014-A G1), so probing longer horizons means relaxing the
  floor directly; cells whose `round(1.5 × median)` term already exceeds a given floor are unchanged at that
  variant (the lever bites exactly where the floor binds, by construction). `window=20`, `k=1.5`,
  `min_moves=5` are held at benchmark.
- **`/THIRD-EVENT` = exit on the next ZigZag trend-change confirmed in the reversal direction `rd`.** Hold
  the harami-anchored reversal position until the ZigZag confirms a new move with `Direction == rd` and
  `ConfirmTime > entry` (the substrate's structural confirmation that the faded reversal has completed), then
  exit at **that confirmation bar's real close**. FAV / ADV bind if reached first. Operator rationale
  (recorded): once the substrate itself confirms the reversal we predicted, the structural reason to keep
  holding is spent; the in-progress move's own confirmation (a `Direction == −rd` trend-change, adverse to
  us) is handled by the benchmark 1:1 adverse stop, which is almost always hit first in that case, so the
  event barrier targets the *fade-succeeded* exit.
- **`/THIRD-EVENT` carries a max-horizon backstop = `8 × bench_N`** (bounds censoring; makes the event
  horizon comparable to the `/THIRD-TIME` maximum). Effective per-event cap `n_event_evt = min(bars to the
  next `rd`-confirm after entry, 8 × bench_N)`; if no `rd`-confirm occurs within the backstop, the event
  exits at the backstop bar (a long time cap); if the backstop window is truncated by the TRAIN data edge
  before resolution, the event is `DATA_CENSORED` (disclosed). `bench_N` is the BENCH (floor=6) adaptive cap
  for that entry; an entry that is P4 warmup-excluded (`< 5` trailing durations, `bench_N` undefined) is
  excluded from `/THIRD-EVENT` as well.
- **Favourable target and adverse target are held at benchmark for every variant** (P2: `fav_dist =
  0.50 × M_sofar`, real-close-anchored; P3: 1:1 adverse `adv_dist = fav_dist`). This is pure OAT on the
  third barrier. The favourable-target lever is EXP-056; the adverse-target lever is EXP-057; combining
  levers is EXP-060.

## Slot & ledger accounting (binding)

- **0 candidate slots, 0 TEST reads.** Characterization/diagnostic per the 014-B D0 addendum
  (`014-B-D0-addendum.md` slot & ledger accounting). The `/THIRD-TIME` and `/THIRD-EVENT` branches are
  registered but consume a slot only when a future scope activates one as a screening candidate — which, per
  P21, cannot happen before G2 PROCEED_TO_SCREEN.
- **No TEST stratum is read.** All work is on the **TRAIN** slice (first 70% of the first-70% analysis set),
  identical fence to EXP-049/053/054/055/056/057. No `test-read-ledger.md` tally applies; no entry is
  created. The conditioned HA-harami event population already had its first new-universe TRAIN contact in
  EXP-053 (same definition); no new stratum is opened and the global-holdout seal carries forward unchanged.
  The nested analysis-set **TEST stratum is not read**; the final-30% **global holdout** is never loaded,
  inspected, or touched. **Note on `/THIRD-EVENT` backstop and longer `/THIRD-TIME` caps:** forward
  excursion/exit scans run only within the TRAIN slice and are clipped to the TRAIN data edge — a window that
  would extend past `train_end_ts` is `DATA_CENSORED`, never resolved against TEST/holdout rows.
- All work is **gross** (no costs). Detection on HA candles; **every outcome metric on real prices**
  (`RealOpen/High/Low/Close` domain-bar OHLC), never HA prices.

---

## Hypothesis

For the live `/STRONG`-conditioned HA harami (anchored at the harami confirmation-bar close, faded against
the in-progress strong move, favourable target held at the benchmark 50%-of-`M_sofar` level and adverse
target held at the benchmark 1:1 level), **at least one alternative third-barrier geometry** (`/THIRD-TIME`
floor ∈ {12, 24, 48}; `/THIRD-EVENT` ZigZag-`rd`-confirm with 8× backstop) produces **higher gross per-event
median expectancy** (P14, ATR-normalised, P15 fills, real prices) than the **benchmark adaptive cap** (P4,
floor=6), on the binding `/STRONG-STAT` arm, with the favourable and adverse targets held at benchmark (OAT
on the third barrier).

Falsifiable: if **no** alternative third-barrier variant clears the P11 quorum (≥5 cells over ≥3 instruments
with CI_low > 0 on its own expectancy) **and** beats the benchmark variant (variant − benchmark paired
contrast CI_low > 0 in the quorum), then third-barrier geometry is **not** a lever that improves conditioned
capture on benchmark favourable/adverse geometry (a valid characterization result that feeds G2 — never a
closure inside 014-B).

## Question

Does changing only the **third barrier** — from the benchmark floor-6 adaptive time cap to a longer-floor
adaptive cap (`/THIRD-TIME` floor ∈ {12, 24, 48}) or to a structural event cap (`/THIRD-EVENT`: hold until
the ZigZag confirms a reversal-direction move, backstopped at 8× the benchmark cap) — improve the conditioned
HA-harami's gross per-event median expectancy vs the benchmark, per cell and composed across the grid, and
which variant (if any) wins? And at what cost in **censoring** (the fraction of events whose longer window is
truncated by the data edge) and in **TIMECAP/event-exit composition** (disclosed secondaries)?

---

## Scope Boundaries

### Data Views

- **Real domain bars** (5m strict; 15m/30m/1h/2h/4h via `xen.bar_aggregator.aggregate_ohlc`,
  `min_coverage=0.90` — identical to EXP-048/049/053/054/055/056/057/VAL-004) for the ZigZag substrate,
  confirmed moves, strong-move magnitudes, the third-barrier caps (time and event), barriers, fills, ATR
  normalisation, and **all** outcome metrics.
- **Heiken Ashi candles** (`xen.heiken_ashi_generator`, from the same domain bars) for **harami detection
  only** (`xen.ha_harami.detect_ha_harami`, frozen EXP-048 detector). **No HA price enters any metric.**

### Event population (the live conditioned signal — identical to EXP-053/054/055/056/057)

- An HA harami (frozen detector) **AND** the live `/STRONG-STAT` magnitude-percentile filter: the in-progress
  confirmed-ZigZag move's **magnitude-so-far** `M_sofar = |C − start_pivot|` (last *confirmed* pivot → harami
  real close `C`) is **≥ p75** of the trailing-20 confirmed-move magnitudes (P7, binding). `/STRONG-HA` (P8:
  run of `X=3` large-body HA bars, no opposing wick) is a **disclosed secondary** arm run through the
  identical pipeline.
- **Trade / reversal direction** `rd = Direction_k` of the last confirmed move
  (`xen.expectancy.live_in_progress_state`; in-progress trend `= −Direction_k`, so the reversal/fade trade is
  in `rd`). No `/BARCFG` isolation; all qualifying haramis count.
- Construction reuses `xen.expectancy.live_in_progress_state` + `live_strong_stat` — the **same functions
  EXP-053/056/057 used** — so the binding population is byte-identical to EXP-053's conditioned events
  (verified by population reconciliation).

### Entry anchor

The **harami confirmation-bar real close** `C` (real domain-bar close at the harami timestamp), strictly
before any ZigZag trend-change confirmation. Identical to EXP-053/055/056/057.

### Third-barrier variants (predeclared sweep; OAT on the third barrier only)

For every variant the **favourable** target is the benchmark `fav = C + rd·fav_dist`, `fav_dist =
0.50 × M_sofar` (P2), and the **adverse** target is the benchmark 1:1 `adv = C − rd·fav_dist` (P3)
(`xen.expectancy.benchmark_barriers`). Variants differ only in the **third barrier**, expressed as the
per-event window length `n_event` (in real domain bars after entry) fed to the P15 resolver
(`xen.expectancy.resolve_path_ordered`). Fills are P15. The qualifying denominator is FAV/ADV/TIMECAP with a
finite exit and finite positive `ATR_entry` (`xen.expectancy.qualifying_mask`); `DATA_CENSORED` (window
truncated by the TRAIN edge before resolution) is excluded-with-record (disclosed as the censoring fraction),
never measured against truncated data.

1. **Benchmark (reference variant, P4 — floor=6):** `N = max(6, round(1.5 × median(trailing-20 confirmed-move
   durations)))` (`xen.expectancy.adaptive_time_caps_by_epoch`, default `floor=6`). Reproduces the EXP-053
   benchmark third barrier — the anchor every alternative is contrasted against. (Per-cell median + `r ≈
   0.50` expected, replicating EXP-049/053.)

2. **`/THIRD-TIME-T12` (floor=12):** `N = max(12, round(1.5 × median(durations)))` — `adaptive_time_caps_by_epoch`
   re-called with `floor=12`, all other knobs at benchmark (`window=20`, `k=1.5`, `min_moves=5`).

3. **`/THIRD-TIME-T24` (floor=24):** `N = max(24, round(1.5 × median(durations)))` (`floor=24`).

4. **`/THIRD-TIME-T48` (floor=48):** `N = max(48, round(1.5 × median(durations)))` (`floor=48`).

5. **`/THIRD-EVENT` (ZigZag `rd`-confirm, 8× backstop):** the effective per-event cap is
   `n_event_evt = min(bars_to_next_rd_confirm, 8 × bench_N)`, where:
   - `bars_to_next_rd_confirm` = `confirm_idx[j] − entry_idx` for the **smallest** `j` with `Direction[j] ==
     rd` **and** `ConfirmTime[j] > entry_epoch` (the next confirmed reversal-direction move strictly after
     entry); if none exists within the data, this term is `+∞` (the backstop binds).
   - `bench_N` = the BENCH (floor=6) adaptive cap for that entry; `8 × bench_N` is the backstop.
   - Resolved through the **unchanged** `resolve_path_ordered`: a scan of `[entry+1, entry+n_event_evt]` that
     returns FAV/ADV if a target is hit first, else `TIMECAP` exiting at `close[entry+n_event_evt]` (the
     `rd`-confirm bar's real close when the event bound, or the backstop bar's real close when the backstop
     bound), else `DATA_CENSORED` if the window is truncated by the TRAIN edge before resolution.
   - **Warmup/availability:** an entry that is P4-warmup-excluded (BENCH `warmup` true, `bench_N` undefined)
     has no defined backstop and is **excluded-with-record** for `/THIRD-EVENT`. `n_event_evt ≥ 1` by
     construction (`bench_N ≥ 6`); a degenerate `n_event_evt = 0` cannot occur for a non-warmup entry.
   - **Disclosed split:** the fraction of TIMECAP exits that bound on the **actual `rd`-confirm event** vs on
     the **backstop** is reported per cell (an event-vs-time-cap composition disclosure feeding the censoring
     narrative).

**Total predeclared third-barrier variants:** 1 benchmark + 3 `/THIRD-TIME` (T12, T24, T48) + 1
`/THIRD-EVENT` = **5 binding variants**. Each variant runs on the binding `/STRONG-STAT` arm and the
`/STRONG-HA` arm (disclosed), with both P13 baselines.

### Favourable target, adverse target, fills (benchmark; held fixed)

- **Favourable (P2, benchmark 50%):** `fav = C + rd·0.50·M_sofar` for every variant
  (`xen.expectancy.benchmark_barriers`).
- **Adverse (P3, benchmark 1:1):** `adv = C − rd·0.50·M_sofar` for every variant (same call).
- **Fill model (P15, method standard):** when a single domain bar could touch more than one level, fills
  resolve in path order — bullish bar (`Close ≥ Open`): `Open → Low → High → Close`; bearish (`Close < Open`):
  `Open → High → Low → Close`. TIMECAP exits at the cap/event bar's real close; `DATA_CENSORED` (window
  truncated by the TRAIN/data edge before resolution) carries no exit price and is excluded. Reuse
  `xen.expectancy.resolve_path_ordered`. Documented approximation; disclosed in every result.

### Parameters (all frozen D0; no tuning)

ZigZag Wilder ATR(14), `ATR_MULT = 1.0` (P1); `/STRONG-STAT` trailing-20, ≥p75 (P7); `/STRONG-HA` `X=3`
(P8); benchmark favourable `X = 50%` of `M_sofar` (P2); benchmark adverse 1:1 (P3); benchmark time-cap
`(k=1.5, window=20, floor=6, statistic=median, min_moves=5)` (P4); ATR-normalisation divisor = Wilder ATR(14)
at the harami entry bar (P14); bootstrap `b = round(m^(1/3))`, `N_BOOT = 10_000`, fixed seed (P14). **New
predeclared third-barrier parameters (this scope):** `/THIRD-TIME` floors `{6 (BENCH), 12, 24, 48}` with
`k=1.5`/`window=20`/`min_moves=5` held at benchmark; `/THIRD-EVENT` opposing-event definition = next confirmed
ZigZag move with `Direction == rd` and `ConfirmTime > entry`; `/THIRD-EVENT` backstop multiple `= 8 × bench_N`.
None is tuned against outcomes; sensitivity is not swept beyond the predeclared variant set.

### Instruments / cells

The **99-cell EXP-049/053/054/055/056/057 member grid**: 17 instruments × {5m,15m,30m,1h,2h,4h} minus the 3
COVERAGE_EXCLUDED cells (US500-4h, JP225-2h, JP225-4h). Per-cell first, then **P11** composition (≥5 cells
over ≥3 instruments) for any "winning variant" claim. Full-grid breadth required by P11 and the "no blanket
assumptions" principle. DE30 carries the truncated-coverage disclosure.

### Time range

Full dataset, nested chronological split. **TRAIN only** = first 70% of the first-70% analysis set (per cell,
F01 file-order-prefix convention identical to EXP-049/053/054/055/056/057: `train_end_ts` = last `CloseTime`
of the first `int(int(total_rows*0.7)*0.7)` file-order 1-minute rows). TEST (last 30% of the analysis set) and
the final-30% **global holdout** are **not** read. Longer-horizon and event windows are clipped to
`train_end_ts`; an unresolved truncated window is `DATA_CENSORED` (disclosed), never resolved past the edge.

### Baselines (P13 / P20 — disclosed secondaries)

- **Matched-count random in-regime timestamps** (same cell/regime/direction, EXP-021/027 exclusion
  convention) run through the **identical third-barrier + barrier + resolver pipeline** for each variant —
  does a given third-barrier geometry beat random entries under the same geometry?
- **MA(20,50) segmentation** (alternative trend substrate, EXP-050/053 baseline): conditioned-harami
  expectancy under MA-segmented moves for each variant, disclosed. For `/THIRD-EVENT` under the MA-seg
  baseline, the opposing event is the next MA-segment confirmation in direction `rd` (the analogous structural
  event in that substrate), with the same `8 × bench_N` backstop computed from the MA-seg benchmark cap.
- Baselines are disclosed secondaries; the binding readout is each variant's own expectancy and the variant −
  benchmark contrast.

### Look-ahead / causality discipline (binding)

- ZigZag pivots are future information until confirmed. The signal (harami + `/STRONG-STAT`), `M_sofar`, the
  favourable/adverse targets, and all third-barrier caps use **only** confirmed, completed prior moves and
  **real bars at or before the entry bar** for *construction at entry*. The `/THIRD-TIME` caps depend only on
  durations of moves confirmed **strictly before** entry (`adaptive_time_caps_by_epoch` semantics, unchanged).
- The `/THIRD-EVENT` exit is a **forward** event: it uses the next ZigZag move confirmed with `ConfirmTime >
  entry` (known going forward in real time, exactly as the benchmark TIMECAP resolves at a forward bar), and
  exits at that confirmation bar's real close — not at the retroactively-located pivot, and never referencing
  an unconfirmed pivot. This is causal (the exit decision is taken at the confirmation bar, in real time), not
  look-ahead.
- Excursion/exit scans read only bars `[entry_idx+1, min(entry_idx+n_event, last_train_idx)]`, fenced
  `CloseTime ≤ train_end_ts`; an event whose window is truncated by the TRAIN edge before resolution is
  `DATA_CENSORED` (excluded, disclosed), never measured against truncated data.
- Ordering/alignment by `CloseTime`, never bar index across views.

### Real-price outcome discipline

Harami detected on HA candles; `M_sofar`, ATR normalisation, fav/adv levels, all third-barrier caps, fills,
expectancy, `r`, win rate, and censoring all on real domain-bar OHLC. **No HA price in any metric.**

### Exclusions

- No costs (gross only).
- **Third-barrier geometry only.** No `/VPTARGET`/`/MAGTARGET` (EXP-056 — favourable held at benchmark 50%),
  no `/ADV-EXTREME`/`/ADV-NONE` (EXP-057 — adverse held at benchmark 1:1), no `/EXIT-PARTIAL`/
  `/EXIT-TRAIL-STRUCT` (EXP-059), no combined system (EXP-060). No `/BARCFG`/`/CONFIRM` overlays; no
  position-in-move *filter*.
- No parameter tuning; **no post-result variant selection** (all predeclared variants reported); no gate
  adjudication (single G2 after the full 014-B slate — EXP-058 emits a characterization readout only).
- No TEST or holdout contact; no candidate slot; no TEST read.

## Success / Failure Criteria

All criteria are **gross**, per-cell first, composed by **P11** (≥5 cells over ≥3 instruments). The binding
endpoint is **median per-event gross expectancy** `E_cell` (ATR units, P15 fills), on the **`/STRONG-STAT`
arm**; per-cell viable iff **CI_low > 0** (regime-clustered moving-block bootstrap, one-sided 95%) **AND ≥ 30
qualifying events**.

- **EVIDENCE_FOR (a third-barrier lever helps):** ≥1 alternative variant **(a)** clears P11 on its own median
  expectancy **AND (b)** beats the benchmark variant on the **variant − benchmark contrast** (paired contrast
  CI_low > 0 on the common qualifying-event subset) within the P11 quorum (matched cells). The winning
  variant(s) and their margin over benchmark are the deliverable; no candidate registration (G2 only).
- **EVIDENCE_AGAINST (third-barrier geometry is not a lever):** no alternative variant both clears P11 and
  beats the benchmark contrast. Recorded as a measured-negative characterization; routing deferred to G2
  across the full slate.
- **INCONCLUSIVE (power-limited):** fewer than the P11 quorum of cells reach ≥30 qualifying events on the
  variants of interest (censoring/warmup exclusions deplete counts — the expected failure mode of the longest
  horizons), no correctness failure. Disclosed; never defaulted to a ratio.
- **SUBSTRATE/METHOD_DEFECT:** any determinism, causality, or invariant failure → fix before reporting.
  Invariant checks include: (i) benchmark variant reproduces EXP-053 per-cell expectancy and count to
  tolerance; (ii) `/THIRD-TIME` per-event cap is **monotone non-decreasing in floor** event-wise
  (`N_BENCH ≤ N_T12 ≤ N_T24 ≤ N_T48`); (iii) `/THIRD-EVENT` per-event cap satisfies `1 ≤ n_event_evt ≤
  8 × bench_N` and any bound `rd`-confirm has `ConfirmTime > entry`; (iv) population reconciliation vs EXP-053
  exact (conditioned `/STRONG-STAT` population identical).

The deliverable label is **THIRD_BARRIER_CHARACTERISED** carrying the per-cell + P11 readout for every
variant, the EVIDENCE_* classification, the benchmark contrast per variant, both filter arms, both P13
baselines, and all disclosed secondaries (per-variant **censoring fraction** — the binding trade-off of
horizon extension; first-hit `r`; win rate; mean; TIMECAP fraction; `/THIRD-EVENT` event-vs-backstop exit
split; warmup exclusion counts; `/STRONG-HA` arm; MAD arm). No phase closure or candidate registration here.

## Complexity Budget

- **Max distinct statistical methods: 4** — (1) regime-clustered moving-block bootstrap CI on a variant's
  median expectancy per cell (`xen.expectancy.bootstrap_median_distribution` + `median_ci`); (2) same on each
  P13 baseline; (3) variant − benchmark paired-median contrast CI
  (`xen.favourable_targets.paired_median_contrast_ci`, common qualifying-event subset); (4) variant − baseline
  contrast CI (`xen.expectancy.contrast_ci`). These four methods are applied across the predeclared
  third-barrier variant set (a parameterised sweep over one experiment, not new methods per variant) —
  consistent with the 014-B surface design and the EXP-056/057 precedent.
- **Max visualisations: 5** — (i) per-variant median-expectancy forest/CI per cell vs benchmark; (ii) variant
  − benchmark contrast heatmap (variants × cells); (iii) expectancy distribution by variant (pooled);
  (iv) P11 composition / "wins-over-benchmark" map across variants; (v) **censoring + TIMECAP composition by
  variant** (the horizon-vs-power trade-off) alongside per-cell qualifying-event counts. Secondary tables to
  CSV.
- **Max new code modules: 1** — a bounded **third-barrier geometry** helper (`third_barrier.py`) supplying
  the causal `/THIRD-EVENT` per-event cap builder (locate the next `rd`-direction confirmed move with
  `ConfirmTime > entry`, compute bars-to-event, apply the `8 × bench_N` backstop and warmup exclusion) plus a
  thin wrapper that produces each variant's per-event `n_event` array. The `/THIRD-TIME` caps are produced by
  **re-calling** `xen.expectancy.adaptive_time_caps_by_epoch` with different `floor` values (no new code). The
  resolver, fills, realised returns, qualifying mask, median bootstrap, and contrasts are **reused** from
  `xen.expectancy`/`xen.favourable_targets`; ZigZag, harami, strong-move, confirmation-index, and the
  in-progress-state machinery are reused. Orchestration in `code/run_experiment.py`.

## Metric Denominators & Zero-Baseline

- **Per-event realised gross return** (ATR units) is defined for every **qualifying** event of a variant —
  those with a built window whose outcome is `FAV`, `ADV`, or `TIMECAP`. Return = `rd·(exit_price −
  C)/ATR_entry` (`xen.expectancy.realised_returns`), where `exit_price` is the P15 path-ordered fill (target
  level for FAV/ADV; cap/event bar real close for TIMECAP) and `ATR_entry` = Wilder ATR(14) at the harami
  entry bar.
- **Per-cell endpoint (binding):** `E_cell = median` over the variant's qualifying-event return population
  (`xen.expectancy.qualifying_mask`). `DATA_CENSORED` and warmup-excluded events are **excluded** from the
  median and **disclosed as counts** per cell per variant. The censoring fraction (`DATA_CENSORED` / built
  window) is a prominently disclosed secondary because it grows with horizon and is the cost side of the
  third-barrier lever.
- **Zero-baseline / power:** a cell with **< 30 qualifying events** for a variant is **NOT_VIABLE-by-power**
  for that variant (non-reportable for its readout), never an undefined or infinite ratio. Conditioning +
  per-variant censoring/warmup exclusions reduce counts vs the unconditioned base; longer horizons
  (T48, `/THIRD-EVENT` backstop) are expected to deplete the most — depleted cells are disclosed.
- **First-hit `r`** is computed and reported per variant as a **disclosed secondary**: `r = n_FAV / (n_FAV +
  n_ADV)` over resolved FAV/ADV events, with TIMECAP excluded from the `r` denominator (EXP-049 convention).
  Because favourable/adverse geometry is held at benchmark (1:1), `r` is expected to stay near 0.50 across
  variants; the third-barrier lever moves expectancy through the **TIMECAP exit price** and the
  **FAV-vs-TIMECAP composition**, not through `r`. `r` never enters viability.
- **Disclosed secondaries (never binding):** per-variant censoring fraction; first-hit `r`; mean per-event
  return; win rate (fraction with return > 0); TIMECAP fraction; `/THIRD-EVENT` event-vs-backstop exit split;
  per-variant warmup exclusion counts; the `/STRONG-HA` arm; both P13 baselines; the MAD `/STRONG-STAT`
  sensitivity arm.

## Data Requirements

Per cell (instrument × domain), TRAIN slice only: lazy `pl.scan_parquet`; read total row count;
`analysis_rows = int(total_rows*0.7)`, `train_rows = int(analysis_rows*0.7)`; collect only the first
`train_rows` file-order 1-minute rows (F01 prefix; never sort/collect the full file, never read TEST or
holdout); assert chronological; `train_end_ts` = last `CloseTime`. Aggregate each member domain (5m strict;
others `min_coverage=0.90`); fence to `CloseTime ≤ train_end_ts`; generate HA candles; run
`xen.zigzag.generate_zigzag(bars, atr_period=14, atr_mult=1.0)` → confirmed moves +
`xen.capture_barriers.confirm_indices`; detect haramis on HA candles aligned by `CloseTime`; build the live
in-progress state + `/STRONG-STAT`/`/STRONG-HA` conditioning (`xen.expectancy`); compute the benchmark
favourable + adverse targets (`benchmark_barriers`), then each predeclared third-barrier variant's per-event
`n_event` — BENCH/T12/T24/T48 via `adaptive_time_caps_by_epoch(floor=F)`, `/THIRD-EVENT` via the new helper
(next `rd`-confirm + 8× backstop) — resolve each variant under P15 (`resolve_path_ordered`), compute
ATR-normalised gross returns, bootstrap the per-cell median per variant, compute both P13 baselines through
the identical per-variant pipeline, compose by P11; second full pass for determinism. `tqdm` over the 99-cell
grid; bounded per-cell memory (do not retain all domain frames or all bootstrap draws); fixed seed;
deterministic. Outputs (`results/`): `per_cell_expectancy.parquet` (per cell × variant: median/CI expectancy,
paired contrast vs benchmark, n_qualifying, censoring/warmup counts, TIMECAP fraction, `/THIRD-EVENT`
event-vs-backstop split, `r`, win rate, baseline medians/contrasts, viability flag); `third_barrier_map.csv`
(binding `/STRONG-STAT` summary per variant); `secondary_map.csv` (`/STRONG-HA`, MAD arm, baselines, `r`,
censoring); `composition_readout.json` (per-variant P11, wins-over-benchmark, EVIDENCE_* fork);
`population_reconciliation.csv` (binding conditioned population vs EXP-053; benchmark expectancy/`r` vs
EXP-053); `run_metadata.json` (seed, frozen + new predeclared constants, EXP-053 source paths/hashes).
Bounded plots from the collected per-cell summaries (no reloads).

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

Compose existing primitives; the only new code is the bounded `/THIRD-EVENT` cap helper (causal next-`rd`-
confirm locator + 8× backstop + warmup exclusion). Pipeline per cell: `xen.zigzag.generate_zigzag` → confirmed
moves + `xen.capture_barriers.confirm_indices`; `xen.heiken_ashi_generator` + `xen.ha_harami.detect_ha_harami`
→ harami entry bars (aligned by `CloseTime`); `xen.expectancy.live_in_progress_state` (supplies
`start_epoch`/`rd`/`m_sofar`) + `live_strong_stat` → the binding conditioned population (identical to EXP-053;
cross-checked by `population_reconciliation`); `xen.strong_move.annotate_ha_impulse` → the `/STRONG-HA` arm.
For each qualifying harami: compute the benchmark favourable + adverse targets
(`xen.expectancy.benchmark_barriers`); compute each variant's per-event `n_event` — BENCH/T12/T24/T48 via
`adaptive_time_caps_by_epoch(floor=F)`, `/THIRD-EVENT` via the new helper — resolve each variant via
`xen.expectancy.resolve_path_ordered` → `realised_returns` → `qualifying_mask`; bootstrap per-cell median per
variant (`bootstrap_median_distribution`, `median_ci`); paired contrast vs benchmark
(`xen.favourable_targets.paired_median_contrast_ci`) and vs baselines (`xen.expectancy.contrast_ci`). Emit the
layered per-variant P11 / wins-over-benchmark / EVIDENCE_* readout plus the binding censoring disclosure; **do
not adjudicate §8** (single 014-B G2 after the full slate).
