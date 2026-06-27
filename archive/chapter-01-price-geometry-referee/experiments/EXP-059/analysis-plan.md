# Analysis Plan: Experiment EXP-059

**Title:** Position-Management Exits (Conditioned HA Harami; `/EXIT-PARTIAL`, `/EXIT-TRAIL-STRUCT`, individually and combined)
**Phase / checkpoint:** `2026-06-14-014-ha-harami-substrate-and-capture` (014-B; G0-B PASS 2026-06-15)
**Family / HYP:** `CF-HA-HARAMI-001/HYP-012` — EXP-059 (PLANNED, Phase 014-B batch)
**Binding endpoint:** median per-event **position-weighted** gross expectancy `E_cell` (P14), ATR-normalised,
P15 fills, real prices, on the binding `/STRONG-STAT` arm; per-cell viable iff `CI_low > 0` (one-sided 95%
moving-block bootstrap) AND ≥30 qualifying events; composed by P11 (≥5 cells over ≥3 instruments).
**Discipline:** gross; 0 candidate slots; 0 TEST reads; TRAIN only; holdouts sealed; detection on HA candles,
**all outcome metrics on real prices**. This plan does **not** expand `scope.md`; it specifies *how* the
12 predeclared arms are computed, validated, and read. No standalone governance (Stage 4 runs consolidated).

---

## Objective

Determine whether replacing the benchmark single fixed exit (50% favourable / 1:1 adverse / adaptive time
cap, single leg) with **scaled favourable take-profits** (`/EXIT-PARTIAL`) and/or an **adverse-side
market-structure trailing stop** (`/EXIT-TRAIL-STRUCT`, 0.5×ATR ZigZag) — individually and combined — raises
the conditioned HA-harami's gross per-event **median position-weighted expectancy**, per cell and composed by
P11, and which scheme (if any) beats benchmark. The endpoint is the one P14 was created for: a first-hit `r`
cannot express the value of partial exits or trailing stops, so the binding metric is the position-weighted
realised return. This is a characterization read feeding the single 014-B G2 — never a closure here.

**Predeclared binding arm set (12; identical to `scope.md` §Operator decisions):** `BENCH` (single-leg
reference, reproduces EXP-053); `PARTIAL-V1/V2A/V2B/V2C`; `TRAIL-PURE/TP-INIT/TP-NOINIT`;
`COMBINED-V1/V2A/V2B/V2C`. Each runs on the binding `/STRONG-STAT` population; `/STRONG-HA` and the MAD
`/STRONG-STAT` form are disclosed secondary arms; both P13 baselines (matched-count random in-regime
timestamps; MA(20,50) segmentation) run through the identical per-arm pipeline.

---

## Methodology

### Step 1: TRAIN-slice loading, domain construction, holdout fence

- **Method:** F01 file-order-prefix slicing per cell. Lazy `pl.scan_parquet`; `total_rows`;
  `analysis_rows = int(total_rows*0.7)`; `train_rows = int(analysis_rows*0.7)`; collect the first `train_rows`
  file-order 1-minute rows only; assert strictly increasing `CloseTime`; `train_end_ts = max(CloseTime)`.
  Aggregate each member domain (5m strict; 15m/30m/1h/2h/4h via `xen.bar_aggregator.aggregate_ohlc`,
  `min_coverage=0.90`); fence all derived series to `CloseTime ≤ train_end_ts`.
- **Why this method:** byte-identical fence to EXP-049/053–058 guarantees the conditioned population reconciles
  exactly with EXP-053 and that neither the nested TEST stratum nor the final-30% global holdout is touched.
- **Simpler alternative considered:** sort-then-slice on `CloseTime` — rejected; the F01 prefix is the
  established convention and avoids materialising the full file (bounded memory, holdout never collected).
- **Assumptions:** 1-minute base rows are in chronological file order (asserted). Holds — VAL-001/VAL-004.
- **Expected output:** per-cell TRAIN real domain bars + `train_end_ts`; the holdout-exclusion guard.

### Step 2: Substrate, detector, and the conditioned population (identical to EXP-053–058)

- **Method:** primary `xen.zigzag.generate_zigzag(bars, atr_period=14, atr_mult=1.0)` → confirmed moves +
  `xen.capture_barriers.confirm_indices`; **secondary** `generate_zigzag(bars, atr_period=14, atr_mult=0.5)`
  → secondary confirmed moves/pivots + confirm indices (for the trailing stop only); HA candles
  (`xen.heiken_ashi_generator`) → `xen.ha_harami.detect_ha_harami` (frozen EXP-048 detector), aligned to real
  bars by `CloseTime`; `xen.expectancy.live_in_progress_state` (supplies `rd`, `start_pivot`/`start_idx`,
  `M_sofar`) + `live_strong_stat` (binding p75 retention; disclosed median+MAD); `/STRONG-HA` via
  `xen.strong_move.annotate_ha_impulse`.
- **Why this method:** every primitive is frozen and validated (EXP-048/051); reusing the *same* functions is
  what makes the population reconcile with EXP-053 exactly (invariant ii).
- **Simpler alternative considered:** none — the conditioned-signal definition is fixed by P16.
- **Assumptions:** ZigZag/HA causality (pivots future-info until confirmed; HA detection uses only
  at-or-before-`t_i` data). Holds by construction (EXP-048 readiness PASS).
- **Expected output:** the binding `/STRONG-STAT` conditioned event set per cell (entry bar `C`, `rd`,
  `M_sofar`, `start_idx`, `ATR_entry = Wilder ATR(14)` at the entry bar); the `/STRONG-HA` and MAD arms.

### Step 3: Benchmark geometry + adaptive time cap (held at benchmark for every arm)

- **Method:** `xen.expectancy.benchmark_barriers(C, rd, M_sofar)` → `fav_dist = 0.5·M_sofar`,
  `fav = C + rd·fav_dist`, `adv = C − rd·fav_dist`; `xen.expectancy.adaptive_time_caps_by_epoch(..., floor=6)`
  → `bench_N`, `warmup` (P4). Every arm's forward window is `[entry+1, entry+bench_N]`.
- **Why this method:** OAT discipline — only the position-management exit machinery varies; the favourable
  level, the adverse level (where not replaced by a trailing stop), and the third barrier are benchmark.
- **Simpler alternative considered:** none; this is the EXP-053 benchmark, reused verbatim.
- **Assumptions:** `M_sofar > 0` for a valid target (gated). Holds for conditioned events by construction.
- **Expected output:** per-event `fav`, `adv`, `fav_dist`, `bench_N`, `warmup`, `ATR_entry`.

### Step 4: NEW — multi-leg P15 partial-exit resolver (PARTIAL + COMBINED favourable side)

The single genuinely new computation (a), in the new module `position_exits.py`. Per event, a **bounded,
explicit, sequential** forward scan over real OHLC `[entry+1, min(entry+bench_N, last_train_idx)]` assigns each
of 3 equal legs (`w=1/3`) its P15 exit. **This loop is the object under test — never vectorize it.**

- **Per-bar resolution (P15 path order).** For bar `i`, the intrabar visit order is fixed: bullish bar
  (`Close ≥ Open`) `O→L→H→C`; bearish (`Close < Open`) `O→H→L→C`. For a long fade (`rd=+1`) the adverse side
  is the Low and the favourable side is the High; for a short fade (`rd=−1`) the adverse side is the High and
  the favourable side is the Low. Each bar contributes exactly one Low-visit and one High-visit in path order,
  so a level is checked at most once per bar (no double-counting). The resolution per bar:
  1. Walk the two extremes in path order. At the **adverse-side** extreme, if the shared **benchmark 1:1
     adverse** `adv` is reached (Low ≤ adv for long / High ≥ adv for short), **all still-open legs close at
     `adv` at bar `i`** (invariant vi) — the event is fully resolved this bar.
  2. At the **favourable-side** extreme (reached before the adverse along the path, or the adverse not
     reached), close every still-open **fractional/benchmark-target leg** whose favourable level is touched
     (High ≥ level for long / Low ≤ level for short), at that **level** (gaps fill at the level). Multiple
     target legs touched on one bar close in increasing-distance order at their own levels.
  3. After the intrabar extremes, if leg-1 is the **first-profitable-close** leg (V1/COMBINED-V1) and is still
     open and `rd·(close[i] − C) > 0`, close leg-1 at `close[i]`.
  4. If bar `i` is the precomputed **reversal-event** bar (Step 6) and the **reversal-event leg** (V1/V2C
     leg-3) is still open, close it at `close[i]`.
- **Time cap / censoring.** At `i = entry+bench_N` any still-open leg closes at `close[i]` (TIMECAP). If the
  cap bar is past the TRAIN edge (`entry+bench_N > last_train_idx`) and the event has not otherwise resolved
  all legs, the event is **`DATA_CENSORED`** (excluded-with-record, disclosed) — never resolved on truncated
  data.
- **Causal/streaming correctness argument:** every quantity read at bar `i` is the real OHLC of a bar with
  `CloseTime ≤ train_end_ts` and index `> entry_idx`; the leg targets, `adv`, and `bench_N` are fixed at
  entry; the reversal-event bar is located by a forward as-of search (Step 6) confirmed strictly after entry.
  No future bar enters any decision. The scan is bounded by `bench_N` (≈6 bars in 96/99 cells), so per-event
  cost is O(bench_N).
- **Why this method (vs reusing `resolve_path_ordered`):** the existing resolver handles one fav/one adv/one
  cap; partial exits require *per-leg* assignment under a *shared* stop/cap and the two bar-level triggers
  (first-profit-close, reversal-event). A new resolver is necessary and minimal.
- **Expected output:** per event, per leg: exit class ∈ {FAV-leg, ADV, FIRST-PROFIT, REVERSAL, TIMECAP,
  DATA_CENSORED} and exit price; the per-leg exit-reason tags feed the disclosed exit-reason composition.

### Step 5: NEW — causal monotone structure trailing-stop builder + P15 trailing resolver (TRAIL + COMBINED adverse)

The new computation (b). The adverse side is a monotone trailing stop on the **secondary 0.5×ATR ZigZag**.

- **Active-stop step function (causal).** Precompute, from the secondary confirmed moves (Direction,
  `EndPrice`, `ConfirmIdx`), the trailing stop. For a long fade (`rd=+1`): when a secondary **up-move**
  (`Direction=+1`, a pivot **high**) confirms (`ConfirmIdx = c`), the candidate stop is the `EndPrice` of the
  **most recent** secondary **down-move** (`Direction=−1`, pivot **low**) with `ConfirmIdx ≤ c`; apply the
  monotone ratchet `stop ← max(stop, candidate)`. Mirror for a short fade (`rd=−1`: a confirmed pivot low
  trails the stop to the most recent confirmed pivot high; `stop ← min(stop, candidate)`). The **active stop
  at bar `i`** is the latest ratcheted value over secondary confirmations with `ConfirmIdx ≤ i`.
  **Initial stop:** `adv` (benchmark 1:1) for `TRAIL-PURE`/`TRAIL-TP-INIT`/all `COMBINED`; **none** (no adverse
  exit) for `TRAIL-TP-NOINIT` until the first secondary confirmation after entry.
- **Per-bar P15 resolution.** Forward scan `[entry+1, min(entry+bench_N, last_train_idx)]`. At bar `i`, update
  the active stop to reflect any secondary confirmation with `ConfirmIdx ≤ i` (monotone). Then, in path order:
  the favourable target `fav` (present for TP arms / partial legs in COMBINED; absent for `TRAIL-PURE`) and the
  active trailing stop are checked exactly as in Step 4 (adverse-side extreme = the stop level; favourable-side
  extreme = `fav`/leg levels). A trailing-stop fill exits the (remaining) position at the **stop level**; the
  favourable side exits at its level; the time cap / `DATA_CENSORED` rule is identical to Step 4. In COMBINED
  arms the trailing stop replaces the shared 1:1 stop for all open partial legs.
- **Causal/streaming correctness argument:** the active stop at bar `i` uses only secondary moves with
  `ConfirmIdx ≤ i` (i.e. `ConfirmTime ≤ CloseTime(i)`); because a ZigZag `ConfirmTime` is strictly later than
  the pivot `EndTime` it locates (zigzag causality note), the pivot price used is from a fully-confirmed past
  move — no unconfirmed pivot, no future bar. The ratchet is monotone (the stop never loosens), so it is a
  non-decreasing (long) / non-increasing (short) step function. The loop is bounded by `bench_N` and is **not
  vectorized**.
- **Why this method:** a structure trailing stop is path-dependent and updates on confirmation events; it
  cannot be expressed by the fixed-level resolver. Minimal and necessary.
- **Expected output:** per event: exit class ∈ {FAV, TRAIL-STOP, TIMECAP, DATA_CENSORED} (+ per-leg for
  COMBINED), exit price(s), and the trailing-update trace count (for the monotone invariant check).

### Step 6: Reversal-event locator (V1/V2C leg-3; COMBINED-V1/V2C)

- **Method:** the reversal-event bar = the **earlier** of (i) the next **primary-ZigZag** move confirmed with
  `Direction == rd` and `ConfirmTime > entry` — reuse the `xen.third_barrier.third_event_caps` forward-locator
  (the fade-succeeded structural completion, identical to EXP-058 `/THIRD-EVENT`); and (ii) the next
  **`/STRONG`-conditioned HA harami** whose reversal direction `== −rd` with confirmation bar `> entry` (a
  harami fading the rd reversal move) — a forward as-of search over the same conditioned harami stream. The leg
  exit bar = `min(reversal_event_idx, entry+bench_N)` (the benchmark cap bounds it); the leg closes at that
  bar's real `close`, or at `adv`/trailing-stop if the adverse binds first (Steps 4–5).
- **Why this method:** the take-profit "reversal event" must signal the rd reversal move has *completed/is
  exhausting* — a `Direction==rd` ZigZag confirmation (fade succeeded) or an opposing (`−rd`) conditioned
  harami. A `Direction==−rd` ZigZag confirmation is the *adverse* event (the strong move resumed) and is
  **not** a take-profit trigger — it is already handled by the 1:1 / trailing stop (scope §Operator decisions
  directional-encoding correction). Stage 4 verifies the directional encoding.
- **Assumptions:** ZigZag moves alternate direction, so the forward scan stops within ≤2 confirmations; the
  opposing-harami locator uses the same conditioned stream (no new detector). Causal (both events confirmed
  strictly after entry).
- **Expected output:** per event, the reversal-event bar index (or "none within cap"), with the binding/
  backstop-by-cap split as a disclosed secondary.

### Step 7: Position-weighted realised return + qualifying mask

- **Method:** `R_event = Σ_l w_l · rd·(exit_px_l − C)/ATR_entry`, `Σ_l w_l = 1` (3 legs `w=1/3` for
  partial/combined; 1 leg `w=1` for BENCH/TRAIL). Each `exit_px_l` is the Step 4/5 P15 fill. Reuse the
  `xen.expectancy.realised_returns` sign/normalisation convention per leg, then weight-sum.
  **Qualifying** (the P14 denominator): `fav_dist > 0`, finite `ATR_entry > 0`, the arm's construction
  available (for trailing arms the secondary ZigZag must have ≥1 prior confirmation history else warmup-
  excluded), and **every** leg / the position reaches a finite P15 exit within the TRAIN-fenced window
  (else `DATA_CENSORED`). `DATA_CENSORED` and warmup events are excluded from the median and **disclosed as
  counts** per cell per arm.
- **Why this method:** the weighted realised return is exactly the mechanism's P&L; it is the only endpoint
  that can credit partial exits and trailing stops (P14). The qualifying rule mirrors EXP-053–058 (built
  window, finite exit), generalised to "all legs resolved".
- **Simpler alternative considered:** first-hit `r` — rejected by P14 (blind to multi-leg exits); retained as
  a disclosed secondary for the single-leg BENCH arm only.
- **Assumptions:** ATR-normalisation makes cells comparable (P14). Leg weights are a fixed governance constant
  (not tuned).
- **Expected output:** per cell per arm, the qualifying-event `R_event` population (entry-time order).

### Step 8: Per-cell median bootstrap CI (binding viability) — statistical method (1)

- **Method:** `xen.expectancy.bootstrap_median_distribution(R_event, rng, N_BOOT=10_000)` (moving-block,
  `b = round(m^{1/3})`, regime-cluster preserving) + `xen.expectancy.median_ci` → `E_cell` (median),
  one-sided 95% lower bound (5th pct), two-sided bounds. Per-cell viable iff `CI_low > 0` AND `m ≥ 30`.
- **Why this method:** the per-event return distribution is fat-tailed (P14 chose the median); a non-parametric
  moving-block bootstrap respects serial/regime dependence without distributional assumptions (programme
  principle: non-parametric by default). Identical to EXP-053–058.
- **Simpler alternative considered:** i.i.d. bootstrap / normal CI — rejected (ignores serial dependence;
  normality fails for these returns).
- **Assumptions:** approximate stationarity within a cell's TRAIN block structure; block length absorbs
  short-range dependence. Acknowledged-weak, mitigated by the block bootstrap (no stronger claim is made).
- **Expected output:** per cell per arm: `E_cell`, `ci_low_1s`, two-sided CI, `m`, viability flag.

### Step 9: Arm − benchmark paired-median contrast (binding "beats benchmark") — statistical method (2)

- **Method:** `xen.favourable_targets.paired_median_contrast_ci(arm_R, bench_R, rng, N_BOOT=10_000)` on the
  **common qualifying-event subset** (events qualifying under *both* the arm and BENCH, entry-time order, equal
  length) — one block-index draw applied to both series so shared event/regime noise cancels. The arm "beats
  benchmark" iff the paired contrast `CI_low > 0`.
- **Why this method:** the arm and BENCH share the same conditioned events; a paired contrast is the correct,
  tighter test of "does this exit scheme add value over the fixed exit on the same events" (vs the
  independence-assuming `contrast_ci`). Identical design to EXP-056/057/058.
- **Simpler alternative considered:** independent two-sample contrast — rejected (discards the pairing, wider
  CIs, ignores that arms share events).
- **Assumptions:** common-subset pairing is well-defined (both arms qualify); disclosed where the common subset
  drops below 30.
- **Expected output:** per cell per arm: paired contrast median Δ, `ci_low_1s`, two-sided CI, common `m`.

### Step 10: P13 baselines + arm − baseline contrast — statistical methods (1) on baselines, (3) contrast

- **Method:** run each arm's full pipeline on (a) **matched-count random in-regime timestamps** (same
  cell/regime/direction, EXP-021/027 exclusion convention) and (b) **MA(20,50)** segmentation (alternative
  trend substrate; the secondary 0.5×ATR trailing ZigZag is a real-bar construct, unchanged; the reversal-event
  ZigZag arm uses the MA-segment `rd`-confirmation analogue). Bootstrap each baseline median (method 1) and the
  arm − baseline median difference via `xen.expectancy.contrast_ci` (independent streams).
- **Why this method:** baselines test "does the scheme beat random/alternative-segmentation entries under the
  same scheme" — a specificity check, disclosed (never binding). Identical to EXP-053–058.
- **Simpler alternative considered:** drop baselines — rejected; P13/P20 require them as disclosed secondaries.
- **Assumptions:** independence between signal and baseline draws (Monte-Carlo pairing convenience, stated in
  `contrast_ci`).
- **Expected output:** per cell per arm: baseline medians + arm − baseline contrast (disclosed).

### Step 11: P11 composition + EVIDENCE_* fork

- **Method:** an arm is a **per-cell win** iff it is viable (`CI_low>0`, `m≥30`) AND beats benchmark
  (Step 9 `CI_low>0`). The arm clears **P11** iff its wins span ≥5 cells over ≥3 instruments. EVIDENCE_FOR iff
  ≥1 arm clears P11; EVIDENCE_AGAINST iff none; INCONCLUSIVE iff fewer than the P11 quorum of cells reach ≥30
  qualifying events on the arms of interest (power-limited, no correctness failure); SUBSTRATE/METHOD_DEFECT on
  any invariant failure (Step 13).
- **Why this method:** P11 is the frozen programme composition convention applied after per-cell adjudication;
  the fork is the predeclared mechanical routing. No phase closure here — feeds G2.
- **Expected output:** `composition_readout.json` (per-arm P11 status, wins-over-benchmark map, EVIDENCE_*).

### Step 12: Disclosed secondaries

- **Exit-reason composition (binding mechanism diagnostic, disclosed, never viability):** per arm, the fraction
  of position weight exiting via each leg's favourable trigger, first-profitable-close, reversal-event, the
  shared 1:1 / trailing stop, and the time cap. This is *how* the scheme realises P&L — the primary
  interpretive lens for why an arm wins or loses.
- **Others:** `/STRONG-HA` arm; MAD `/STRONG-STAT` arm; per-arm qualifying count + `DATA_CENSORED`/warmup
  counts; win rate (fraction with `R_event>0`); mean per-event return; **first-hit `r` for the BENCH arm only**
  (`n_FAV/(n_FAV+n_ADV)`, TIMECAP excluded; expected ≈0.50, replicating EXP-049/053); both P13 baselines;
  reversal-event event-vs-cap split. None enters viability.

### Step 13: Determinism + predeclared invariant checks (correctness gate)

Two full passes (fixed seed) must produce identical outputs. The six predeclared invariants (scope
§Success/Failure) are asserted in-code and reported:
1. **BENCH reproduces EXP-053** per-cell median expectancy and qualifying count to tolerance (and BENCH `r`).
2. **Population reconciliation vs EXP-053 exact** — the binding `/STRONG-STAT` conditioned population is
   identical (entry timestamps, `rd`, `M_sofar`).
3. **Leg weights sum to 1.0** for every arm; a **degenerate single-trigger arm** (all 3 legs forced to one
   trigger) reproduces the equivalent single-leg `R_event` to float precision.
4. **Trailing stop monotone** (never loosens) and changes level **only** on secondary-ZigZag confirmation bars
   (`ConfirmIdx ≤ i`).
5. **Every exit is a real-bar P15 fill** with `CloseTime ≤ train_end_ts` (no exit past the TRAIN edge).
6. **Shared adverse stop closes all still-open partial legs** at the same bar/level when it binds.

Any failure → SUBSTRATE/METHOD_DEFECT, fix before reporting (no result-aware threshold change).

---

## Visualisations (5 / 5)

1. **Per-arm median-expectancy forest/CI per cell vs benchmark** — does an arm's `E_cell` sit above 0 and
   above BENCH, per cell?
2. **Arm − benchmark contrast heatmap (arms × cells)** — where (cells) and for which arms the paired contrast
   `CI_low > 0`; the P11 pattern at a glance.
3. **Expectancy distribution by arm (pooled)** — the shape/shift of per-event `R_event` across arms (median
   robustness; fat tails).
4. **P11 composition / wins-over-benchmark map across arms** — per-arm count of winning cells and instruments
   vs the ≥5/≥3 quorum; the EVIDENCE_* readout.
5. **Exit-reason composition by arm** (stacked, with per-cell qualifying counts annotated) — the binding
   mechanism diagnostic: which legs/stops actually bind, and how censoring/warmup deplete counts.

Secondary tables (`/STRONG-HA`, MAD, baselines, reversal-event split, BENCH `r`) to CSV, not plots.

---

## Interpretation Guide (predeclared, before results)

- If **≥1 arm clears P11** (≥5 cells / ≥3 instruments, `E_cell CI_low>0`) **AND beats benchmark** (paired
  contrast `CI_low>0`) in the quorum → **EVIDENCE_FOR**: that position-management scheme improves conditioned
  gross capture; the winning arm(s) + margin are the deliverable for G2/EXP-060 (no candidate registration
  here). Read the exit-reason composition to attribute *why* (e.g. trailing captures runner moves; partials
  bank early then run).
- If **no arm both clears P11 and beats benchmark** → **EVIDENCE_AGAINST**: position-management exit machinery
  is not a lever on benchmark barrier geometry; a measured-negative characterization. Cross-check against
  EXP-055 (move available) and EXP-053 (benchmark positive) — if the move is available yet no exit scheme
  improves on the fixed exit, capture is geometry-limited, routed to G2 across the full slate.
- If **fewer than the P11 quorum of cells reach ≥30 qualifying events** on the arms of interest (scaling/
  trailing/warmup deplete counts) with no correctness failure → **INCONCLUSIVE (power-limited)**; disclose the
  depletion, never default to a ratio.
- If **any invariant (Step 13) fails** → **SUBSTRATE/METHOD_DEFECT**; fix and re-run before any reading.
- The **exit-reason composition is the binding mechanism lens** (disclosed): a positive `E_cell` whose weight
  exits overwhelmingly at the time cap means the *cap*, not the scheme, drove the result (the EXP-058 horizon
  lever, not this one). First-hit `r` is interpreted **only** for BENCH (≈0.50 expected; it is meaningless for
  multi-leg arms by construction — exactly the P14 rationale).

---

## Implementation Safety Constraints (for `experiment-developer`)

- **Temporal ordering / causality:** all alignment by `CloseTime`, never bar index across the primary ZigZag,
  secondary ZigZag, HA, and real-bar views. The Step 4/5 resolvers and the Step 6 locators read only bars with
  index `> entry_idx` and `CloseTime ≤ train_end_ts`; the trailing stop uses only `ConfirmIdx ≤ i`.
- **Do NOT vectorize the resolvers (Steps 4–5).** They are explicit bounded sequential loops over real OHLC —
  their causal/streaming semantics are the object under test (mirrors `xen.expectancy.resolve_path_ordered`'s
  "do not vectorize" contract). Bound per-event work by `bench_N`.
- **Denominators / zero-baseline:** a cell with `<30` qualifying events for an arm is NOT_VIABLE-by-power
  (non-reportable), never an undefined/infinite ratio; `DATA_CENSORED`/warmup excluded-with-record, disclosed.
- **Real prices only:** every exit price is real-bar OHLC; HA candles only *locate* the opposing-harami
  reversal bar, then exit at that bar's **real** close. No HA price in any metric.
- **Bounded memory + progress:** `tqdm` over the 99-cell grid; do not retain all domain frames or all bootstrap
  draws (`BOOT_BATCH` batching as in `xen.expectancy`); per-cell bounded.
- **Determinism:** fixed seed; two full passes byte-identical (Step 13). No output directory creation at import
  time; helper functions return data (no helper-level prints); concise orchestration logging only.
- **No safe-optimization that changes membership/order/denominators:** leg/stop resolution order, the P15 path,
  the qualifying rule, and the regime-cluster bootstrap block construction are fixed.

---

## Complexity Check

- **Statistical methods: 4 / 4** — (1) moving-block bootstrap median CI on an arm's `E_cell` per cell; (2) the
  same on each P13 baseline; (3) arm − benchmark paired-median contrast CI; (4) arm − baseline contrast CI.
  Applied across the 12-arm predeclared sweep (a parameterised sweep over one experiment, **not** new methods
  per arm) — identical method set to EXP-056/057/058.
- **Visualisations: 5 / 5** (listed above).
- **New code modules: 1 / 1** — `position_exits.py` (multi-leg P15 partial-exit resolver + structure
  trailing-stop builder/resolver + thin per-arm composition wrappers). All other machinery (benchmark
  resolver, fills, realised returns, qualifying mask, median/contrast bootstraps, ZigZag, harami, strong-move,
  confirmation indices, in-progress state, `third_event_caps` forward-locator) is reused.

---

## Data-View Comparison Considerations

- **Cross-view alignment:** primary ZigZag, secondary ZigZag, HA candles, and real bars align by `CloseTime`.
  The conditioned harami population must reconcile **exactly** with EXP-053 (invariant ii) — different exit
  arms produce different *qualifying* counts (scaling/trailing/warmup/censoring), which is expected and
  disclosed, but the underlying signal set is identical.
- **Event-count differences:** trailing arms exclude events with no prior secondary-ZigZag confirmation history
  (warmup); runner/reversal legs bounded by `bench_N` may shift qualifying counts. Report per-arm qualifying
  counts and exclusion reasons; compose only over cells reaching ≥30.
- **Real-price discipline:** all P&L/excursion on `RealOpen/High/Low/Close`; HA only for detection.

---

## Limitations (predeclared)

- **Benchmark cap bounds the reversal/runner legs.** Because the benchmark P4 cap collapsed to the 6-bar floor
  in **96/99 cells** (014-A G1), the reversal-event legs (V1 leg-3, V2C runner) and the V2B 1.5× runner have
  only ~6 bars to resolve in most cells; many will exit at the time cap rather than their intended
  reversal/extended trigger. This is the intended **clean-OAT** measurement (does position management help
  *within the benchmark horizon*?). The **horizon × position-management interaction** — pairing the best
  position-management scheme with the best EXP-058 third barrier (`/THIRD-TIME`/`/THIRD-EVENT`) — is **deferred
  to EXP-060** (combined event system), not measured here. Disclosed in the readout so a flat result on the
  runner-style arms is not misread as "trailing/running never helps" — only "not within ~6 bars".
- **Trailing-stop init-stop sensitivity** is characterised only by the three standalone TRAIL arms; the
  COMBINED arms use the single benchmark-1:1-init treatment (no re-sweep) — a scoped, disclosed choice.
- **`ATR_MULT_TRAIL = 0.5` is the frozen P18 default**; its sensitivity (the registered `/THIRD-TIME`-analog
  grid) is out of this scope.
- **Gross only**; the cost model enters only at a future tradability screen of a registered candidate branch.
- Standard moving-block bootstrap caveats (approximate within-cell stationarity) apply, mitigated by the block
  construction; no stronger statistical claim is made.
```
