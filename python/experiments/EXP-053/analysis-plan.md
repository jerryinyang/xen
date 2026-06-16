# Analysis Plan: Experiment EXP-053 — Conditioned-Signal Efficacy (HA Harami at Strong-Move Exhaustion, Harami-Anchored)

## Objective

Determine whether the **live, causal, `/STRONG`-conditioned HA harami**, entered at the **harami
confirmation-bar close** and traded as a **reversal of the in-progress strong move** under the
benchmark 3-barrier geometry with **path-ordered intrabar fills (P15)**, has **positive gross
per-event expectancy** (P14: per-cell **median** ATR-normalised realised return, regime-clustered
moving-block bootstrap CI) that **clears P11** (≥5 viable cells over ≥3 instruments) **and exceeds
both P13 matched-control baselines**. This is the central family hypothesis that 014-A never ran
through an outcome read. The deliverable is a **characterization readout** feeding the single 014-B
G2 — no gate is adjudicated here, no candidate branch is registered, **0 slots / 0 TEST reads**,
TRAIN-only, gross.

All detection is on Heiken Ashi candles; **every outcome metric is on real domain-bar OHLC**
(`Open/High/Low/Close`), never HA prices. Methods are non-parametric (bootstrap of a robust median);
no normality, stationarity, or i.i.d. assumption is made.

---

## Methodology

> **Binding decision (operator, 2026-06-15) — magnitude-so-far uses the current price, not the
> running extreme.** `M_sofar = |C − StartPrice_inprogress|`, where `C` is the **harami-bar real
> close** (the current price at the signal) and `StartPrice_inprogress` is the last *confirmed* pivot.
> The earlier draft proposed the in-progress **running extreme** `E_sofar` for dimensional consistency
> with the pivot-to-pivot trailing magnitudes; that is **rejected** because it violates an explicit,
> binding family rule. The family spec (`candidate-families/harami.md`, "Strong-Move / End-of-Trend
> Filter", lines 168–170) requires: *"exclude moves below threshold; and exclude signals that occur
> before significance is confirmed, or after a retracement pulls them back within the threshold
> range."* `E_sofar` is **monotonic** — once a move's extreme crosses p75 it stays ≥ p75 for the rest
> of the move — so the **retracement-exclusion clause could never fire** under `E_sofar` (a
> pulled-back harami would be wrongly retained). Only the **current-price** measure `|C − Start|`
> retraces: when price pulls back, `M_sofar` shrinks below threshold and the pullback signal is
> correctly excluded. Moreover, the single point-in-time test **`M_sofar ≥ threshold` (current price)
> implements BOTH family exclusions at once** — "before significance is confirmed" (`M_sofar` has not
> yet reached threshold) and "after a retracement" (`M_sofar` has fallen back below it). The
> dimensional-consistency concern is subordinate and, in fact, the conservative "shrink on retracement"
> behaviour **is** the retracement rule operating as intended. **Entry and the magnitude reference are
> therefore the same price point `C`** (the harami close) — which, as Step 3 proves, collapses the
> distance (G1) and retracement-level (G2) favourable geometries into one identical target, so EXP-053
> computes a **single benchmark favourable geometry**.

### Step 1: Per-cell construction (substrate, HA, harami, live in-progress state)

- **Method**: Compose the frozen Phase-014 primitives per cell (instrument × domain), TRAIN slice only.
  1. **Holdout-safe loading** (per scope loading pattern): lazy `pl.scan_parquet` of the instrument's
     1-minute file, sort by `CloseTime`; `analysis_cutoff = int(0.7·total_rows)`, `train_cutoff =
     int(0.7·analysis_cutoff)`; slice `[0, train_cutoff)` of the **1-minute base** (fences the global
     holdout *and* TEST in one cut — neither is ever materialized), then aggregate to the domain via
     `xen.bar_aggregator` (5m strict; 15m/30m/1h/2h/4h `min_coverage=0.90`). Reuse the EXP-048/049
     cell-loader helper if one exists; otherwise replicate this exactly and assert consistency with
     their slicing.
  2. **ZigZag substrate** on real domain bars: `xen.zigzag.generate_zigzag(bars, atr_period=14,
     atr_mult=1.0)` → confirmed moves (`StartTime/EndTime/ConfirmTime/Direction/StartPrice/EndPrice/
     ConfirmClose/ATRAtConfirm`).
  3. **Real-bar ATR(14)** for normalisation: `xen.zigzag.wilder_atr(High, Low, Close, 14)` over the
     domain bars → `ATR_entry[i]` per bar index.
  4. **HA candles** from the same domain bars (`xen.heiken_ashi_generator`); **haramis**
     `xen.ha_harami.detect_ha_harami(ha)` → events keyed by `HA0Time` (the harami candle CloseTime =
     entry timestamp; carries the real bar CloseTime). Map each `HA0Time` to its domain-bar index by
     **exact `CloseTime` match** (`np.searchsorted` + equality assert, as in
     `xen.capture_barriers.confirm_indices`) — never by bar position.
  5. **Live in-progress state at each harami bar `i`** (the causal core; explicit, not from a
     completed-move row): let `k` = index of the last confirmed move with `ConfirmTime ≤ t_i`
     (forward as-of search on `ConfirmTime` epochs). The in-progress move then has
     `StartPrice_inprogress = EndPrice_k`, `StartTime_inprogress = EndTime_k`, and **in-progress trend
     `= −Direction_k`**. The **reversal trade direction** is `rd = Direction_k = −(in-progress trend)`
     (we fade the in-progress strong move). The **entry / current price** `C` = the harami bar's real
     close; the **magnitude-so-far** is `M_sofar = |C − StartPrice_inprogress|` (current price, per the
     binding decision above — the running extreme is **not** used). Haramis with **no** confirmed move
     before `t_i` (`k` undefined) are **warmup-excluded** (also excluded by the Step-2 `<5`-window gate).
- **Why this method**: these are the frozen, separately-validated D0 primitives (EXP-048 readiness
  PASS); EXP-053 composes them — no re-derivation. The live in-progress state is the only correct way
  to anchor at the harami *before* the ZigZag confirms (the family's claimed lead); using a completed
  ZigZag move would reproduce EXP-049's downstream anchor, which the lessons doc identifies as the gap.
- **Simpler alternative considered**: anchoring on the completed ZigZag confirmation (EXP-049) — rejected:
  it does not test the harami's lead and is the exact unconditioned object 014-A already measured.
- **Assumptions**: ZigZag pivots are future information until confirmed — honoured (only moves with
  `ConfirmTime ≤ t_i` and the *known* `EndPrice_k` pivot are used; `C` is the harami bar's own close,
  known at `t_i`). Temporal order on `CloseTime`; cross-view alignment HA↔real by `CloseTime` exact match.
- **Expected output**: per cell, an ordered table of harami events with `entry_idx`, `C` (entry close),
  `rd`, `M_sofar`, `ATR_entry`, and the trailing completed-move magnitude window — the input to Step 2.

### Step 2: Live conditioning — `/STRONG-STAT` (binding) and `/STRONG-HA` (disclosed)

- **Method**: per harami event at `t_i`:
  - **`/STRONG-STAT` (binding, P7)**: trailing window = magnitudes `|EndPrice − StartPrice|` of the
    last `min(20, available)` moves with `ConfirmTime ≤ t_i`; `< 5` available → **NO_DECISION /
    warmup-excluded**. Threshold = the **p75** linear (type-7) quantile of that window
    (`xen.strong_move._quantile_sorted` semantics). **Retained iff `M_sofar ≥ threshold`** (inclusive),
    with `M_sofar` measured to the **current price `C`** (Step 1). This single point-in-time test
    **implements both binding family exclusions** (`candidate-families/harami.md` lines 168–170):
    "before significance is confirmed" (`M_sofar` still below threshold — move hasn't travelled far
    enough) **and** "after a retracement pulls it back within the threshold range" (`M_sofar` has shrunk
    back below threshold). The retracement limb is expressible **only** because the current-price measure
    retraces — a running extreme, being monotonic, could never trigger it. This is the *live*
    magnitude-percentile "end-of-move" detector (lessons doc §2), distinct from `strong_stat_decisions`,
    which keys off a completed-move index, not a live timestamp. The **median+1·MAD** form is a
    disclosed sensitivity.
  - **`/STRONG-HA` (disclosed, P8)**: annotate HA candles with `xen.strong_move.annotate_ha_impulse`
    (window 20, min_window 5) and detect runs with `find_impulse_runs(run_len=3)`. Retain the harami
    iff a qualifying **same-direction** run (run_dir == in-progress trend) lies inside the in-progress
    span and **completed at/before** the harami bar: `run_first_time > StartTime_inprogress` AND
    `run_last_time ≤ t_i`. (Any-direction = disclosed sensitivity.)
  - **Trade direction** is `rd` from Step 1 for **both** arms; **no `/BARCFG` filter** — all qualifying
    haramis count regardless of the harami candle colour (`HA0Direction`); BARCFG isolation is a
    separate registered branch, out of scope.
- **Why this method**: P16 makes `/STRONG-STAT` the live conditioning that defines the family signal;
  position-in-move (EXP-050) is **descriptive-only** and is **not** used as a filter (its end pivot is
  future information). `/STRONG-HA` is the registered alternative form (operator-ratified to run as a
  disclosed arm).
- **Assumptions**: both filters are causal by construction (strictly-prior windows / completed runs).
- **Expected output**: per cell, two boolean retention masks (STAT-p75 binding; HA same-dir disclosed)
  + the two sensitivity masks (STAT-MAD, HA any-dir); retained-event counts and retained fraction `f`
  vs the unconditioned harami base (sanity vs EXP-051 `f ≈ 0.20–0.27`).

### Step 3: Benchmark barriers from `M_sofar` (single favourable geometry) + adaptive time cap

- **Method**: for each **retained** harami event (per arm), entry `C` = harami-bar real close,
  `fav_dist = 0.50 · M_sofar` (P2):
  - **Benchmark favourable geometry (single)**: `fav = C + rd·fav_dist`; **adverse target (P3)**
    `adv = C − rd·fav_dist` (1:1). This is the only benchmark favourable geometry for EXP-053.
  - **G1 ≡ G2 collapse (proof; why only one geometry).** EXP-049 reported two favourable
    constructions: G1 (distance from entry, `fav = C + rd·0.5·M`) and G2 (retracement *level*,
    `level = E − Direction·0.5·M`, `fav = level`). They differed there only because the entry
    (`ConfirmClose`) lay **downstream** of the reference move's end pivot `E`. Here the magnitude
    reference ends at the current price `C` itself (`M_sofar = |C − Start_inprogress|`, binding
    decision), so the G2 level becomes `level = Start_inprogress + (in-progress trend)·0.5·M_sofar`,
    and since `in-progress trend = −rd` and `Start_inprogress = C − (in-progress trend)·M_sofar`, this
    reduces to `level = (C + Start_inprogress)/2 = C + rd·0.5·M_sofar = ` the G1 target **exactly**
    (`fav_dist_g2 = rd·(level − C) = 0.5·M_sofar = fav_dist`, never degenerate). G1 and G2 are
    therefore the **same target** for every harami-anchored event; G2 carries no independent
    information and is **not** computed as a separate arm. (A genuinely distinct second geometry would
    require a different favourable model — those are the registered `/MAGTARGET` / `/VPTARGET` branches,
    EXP-056, out of scope here.)
  - **Third barrier (P4)**: per-event adaptive time cap
    `N = max(6, round(1.5 · median(duration_bars of the last 20 moves confirmed strictly before t_i)))`,
    where `duration_bars` of a confirmed move = its `ConfirmTime`-index minus the prior move's
    `ConfirmTime`-index (reuse `xen.capture_barriers.time_caps` duration semantics, but the trailing
    window is anchored to **moves confirmed before the harami `t_i`**, not to a completed-move row).
    `< 5` trailing durations → **warmup-excluded** (no barrier built), never silently capped. Scan
    window `[entry_idx+1, min(entry_idx+N, last_train_idx)]`.
- **Why this method**: the frozen benchmark geometry (P2/P3/P4) with the operator-ratified
  current-price magnitude-so-far reference; the favourable target is the single benchmark construction
  (the EXP-049 G1/G2 distinction collapses, as proved above).
- **Assumptions**: `M_sofar > 0` (degenerate zero-magnitude in-progress moves excluded); barriers use
  only data ≤ `t_i`. The time cap uses only moves confirmed before `t_i`.
- **Expected output**: per retained event, `(fav, adv, N, entry_idx, rd)`, plus warmup / zero-magnitude
  exclusion flags with counts.

### Step 4: P15 path-ordered intrabar fill resolution + realised gross return (the new module)

- **Method** (the single new module, `xen/expectancy.py` — P15 fill standard + P14 return; reused
  across EXP-054–060): an **explicit bounded sequential** first-touch scan per event over
  `[entry_idx+1, min(entry_idx+N, last_idx)]` on **real OHLC** (causal/streaming semantics are the
  object under test — **do not vectorize this loop**). For each scan bar:
  - long (`rd=+1`): `fav` touched iff `High ≥ fav`; `adv` touched iff `Low ≤ adv`.
  - short (`rd=−1`): `fav` touched iff `Low ≤ fav`; `adv` touched iff `High ≥ adv`.
  - **Single touch** → that class fills. **Same-bar double touch** → resolve by **P15 path order**:
    bullish bar (`Close ≥ Open`) visits `Low` before `High` (path `O→L→H→C`); bearish bar
    (`Close < Open`) visits `High` before `Low` (path `O→H→L→C`). The level on the **first-visited**
    extreme fills: long+bullish → `adv` (Low side) first; long+bearish → `fav` (High side) first;
    short+bullish → `fav` (Low side) first; short+bearish → `adv` (High side) first. (This replaces
    EXP-049's blanket-adverse tie-break; EXP-054 quantifies the difference.)
  - **Outcome classes**: `FAV`, `ADV`, `TIMECAP` (full `N` bars, no touch — exit at the cap bar's real
    **close**), `DATA_CENSORED` (window truncated by the TRAIN edge before `N` and before any touch).
  - **Exit price**: `fav`/`adv` **target level** for `FAV`/`ADV` (gaps fill at the level — gross,
    per scope; slippage realism is deferred); cap-bar real **close** for `TIMECAP`.
  - **Realised gross return** (ATR units): `r_e = rd · (exit_price − C) / ATR_entry`,
    `ATR_entry =` Wilder ATR(14) at `entry_idx`. (FAV ⇒ `+fav_dist/ATR`; ADV ⇒ `−fav_dist/ATR`;
    TIMECAP ⇒ signed close move.) Events with `ATR_entry` NaN/≤0 are excluded (post-warmup this should
    not occur; disclosed if it does).
- **Qualifying-event population** (the P14 denominator): events with a built barrier (not
  warmup/degenerate-excluded) resolving to **`FAV`, `ADV`, or `TIMECAP`**. `DATA_CENSORED` and
  warmup/degenerate events are **excluded** from the median and **disclosed as counts**.
- **Power floor**: a cell with **`< 30` qualifying events** is **NOT_VIABLE_BY_POWER** (non-reportable
  for the readout) — never an undefined/infinite ratio.
- **Why this method**: first-hit `r` is blind to partial exits/trailing stops and would foreordain a
  null (lessons §8.6/P14); a real-valued realised-return endpoint is the metric the family's mechanism
  can express, and the P15 path model removes the worst-case-tie-break bias on a near-`0.50` substrate.
- **Assumptions**: the intrabar path (`O→L→H→C` / `O→H→L→C`) is a **documented approximation** of
  unobserved intrabar motion (1-minute base bars are not replayed inside the domain bar) — disclosed in
  every dependent result; EXP-054 bounds its effect vs the worst-case baseline.
- **Expected output**: per qualifying event, `(class, exit_price, r_e)` on the single benchmark
  geometry; per cell, the ordered `r_e` series (by entry time) for the bootstrap.

### Step 5: Per-cell median expectancy + regime-clustered moving-block bootstrap *(stat tests 1–3)*

- **Method**: per cell × arm (STAT binding, HA disclosed), `E_cell = median(r_e over qualifying events)`. Uncertainty
  via a **regime-clustered moving-block bootstrap** of the **median**, mirroring
  `xen.capture_barriers.block_bootstrap_ci` **block construction exactly** — events ordered by **entry
  time**; block length `b = max(1, round(m^(1/3)))`; `ceil(m/b)` contiguous blocks drawn with
  replacement per resample, concatenated and truncated to length `m`; `N_BOOT = 10_000`; batched
  (`BOOT_BATCH = 2_000`); **fixed seed** (master seed offset by a stable cell index). **The only change
  vs the proportion bootstrap is the statistic**: `np.median` of the resampled real-valued `r_e`
  series instead of `sum(fav)/sum(resolved)`. Report one-sided 95% **`CI_low` = 5th percentile** and
  two-sided **2.5/97.5** bounds of the bootstrap-median distribution. No degenerate-resample discard is
  needed (a median of `m ≥ 30` values is always defined); guard only the empty-series case.
  - Stat test **1** = signal STAT-arm median bootstrap; **2** = matched-random baseline; **3** =
    MA(20,50)-segmentation baseline (Step 6). The `/STRONG-HA` arm reuses method 1 (disclosed, not an
    additional method).
- **Why this method**: the per-event ATR-normalised return distribution is **fat-tailed** (FAV/ADV
  cluster at ±`0.5·M_sofar/ATR`, TIMECAP spreads), so the **median** is the robust location estimator
  (operator P14 decision); the moving-block bootstrap is **non-parametric** and preserves local
  serial/regime dependence (blocks of temporally adjacent events) — no normality/stationarity/i.i.d.
  assumption, per programme principles. Mean is reported as a disclosed secondary.
- **Simpler alternative considered**: a one-sample Wilcoxon signed-rank or sign test on `r_e > 0` —
  rejected as the binding test: it assumes exchangeable/i.i.d. events (ignores regime clustering) and
  tests a different (symmetry/sign) null than the median-location CI the endpoint requires. Reported
  informally at most. A normal-theory t-CI is rejected (fat tails).
- **Assumptions**: events within a block share regime context (local time contiguity) — the moving
  block captures this without assuming a parametric dependence structure.
- **Expected output**: per cell × arm, `(m, E_cell, CI_low_1s, CI_lo_2s, CI_hi_2s,
  block_len, mean, r=fav/(fav+adv), win_rate, timecap_frac)` and a per-cell `viable_status`
  (`VIABLE` iff `CI_low_1s > 0` AND `m ≥ 30`; else `CI_SPANS_0` / `NOT_VIABLE_BY_POWER`).

### Step 6: P13 baselines through the identical metric

- **Method**: both baselines are scored through the **identical** Step 3–5 pipeline (benchmark
  geometry, P15 fills, median + same bootstrap):
  1. **Matched-count random timestamps** (same cell): draw **the same number** of entry timestamps as
     the conditioned signal had qualifying events, **without replacement**, from the cell's
     **eligible-bar pool** — bars in the TRAIN slice that (a) have a defined in-progress move
     (`k` defined), (b) defined `ATR_entry`, (c) defined adaptive time cap, and (d) are **not** a
     retained-signal bar. **Direction is NOT random**: each drawn bar takes the `rd` of the in-progress
     move at that bar, and `M_sofar`/barriers are built identically. This isolates the
     **harami + `/STRONG`** condition (same direction rule, same geometry, same regime pool), not the
     trade-direction convention. Fixed per-cell seed (master seed + cell index, distinct stream from
     the bootstrap). "Regime match" = same instrument × domain × TRAIN window (one eligible pool spans
     the cell's realised regimes).
  2. **MA(20,50) alternative move segmentation**: replace the ATR-ZigZag segmentation with
     MA(20,50)-crossover segments on domain `Close` (the EXP-050 robustness arm) — a "move" runs from
     one crossover to the next; in-progress start = last crossover, in-progress trend = sign of
     (fast−slow); in-progress start = last crossover, current price `C` = signal close,
     `M_sofar = |C − last-crossover price|`, and the trailing magnitudes are completed-MA-segment
     ranges. Re-run the **full conditioned-signal** pipeline (harami + `/STRONG-STAT` current-price
     magnitude-percentile + harami anchor + benchmark geometry + P15) on MA segments. Tests whether any
     effect is ZigZag-specific (EXP-050 found
     front-loading attenuates under MA segmentation).
- **Why this method**: P13. The matched-count random control removes the conditioning while holding
  count, cell, regime pool, direction rule, and geometry fixed → isolates signal value. The MA arm is a
  structural robustness control (is the effect substrate-specific?).
- **Assumptions**: the eligible-bar pool is a fair regime-matched null for "a non-signal point in an
  in-progress move." Matched count equalises power so the contrast is not a sample-size artifact.
- **Expected output**: per cell, baseline `(m, E_cell, CI_low_1s, …)` for matched-random and MA-seg,
  same schema as Step 5.

### Step 7: Signal − baseline contrast CI *(stat test 4)*

- **Method**: per cell, the difference of medians `Δ = E_cell(signal STAT arm) − E_cell(baseline)` for
  each baseline. Because signal and baseline are **independent** event sets on the same cell, bootstrap
  the difference: draw the signal block-bootstrap median and the baseline block-bootstrap median
  **independently** (same `N_BOOT`, paired by resample index using independent fixed seeds) and take
  `Δ* = median_signal* − median_baseline*`; report one-sided **`CI_low(Δ) = 5th percentile`** and
  two-sided bounds. **Signal exceeds baseline** in a cell iff `CI_low(Δ) > 0`.
- **Why this method**: the scope's EVIDENCE_FOR uses an OR — "signal viable where baseline is not, **or**
  `signal − baseline CI_low > 0`." The contrast CI makes the second limb mechanically checkable while
  staying non-parametric.
- **Assumptions**: independence of the two event sets (different timestamps); local dependence within
  each is preserved by its own moving blocks.
- **Expected output**: per cell, `CI_low(Δ_random)` and `CI_low(Δ_MA)` and the per-cell
  baseline-beat boolean.

### Step 8: P11 composition + mechanical EVIDENCE_* classification

- **Method** (binding arm = `/STRONG-STAT`, single benchmark geometry, all gross, TRAIN-only):
  - `viable[cell] = (CI_low_1s(signal) > 0) AND (m ≥ 30)`.
  - `beats_baseline[cell] = (NOT viable_random[cell]) OR (CI_low(Δ_random)[cell] > 0)`, computed
    likewise for MA; `beats_both[cell] = beats_random AND beats_MA`.
  - `V_sig` = #`viable` cells; `I_sig` = #distinct instruments among them.
  - `P_powered` = #cells with `m ≥ 30`; `I_powered` = #distinct instruments among them.
  - **P11 (programme convention)**: a composition holds iff **≥5 cells over ≥3 instruments**.
- **Expected output**: the composition tallies and the EVIDENCE_* label (Interpretation Guide below),
  emitted to a `composition_readout.json` + per-cell `outcome_primary.csv`.

---

## Visualisations

1. **Per-cell median-expectancy forest plot** (binding STAT arm): each member cell's `E_cell` with its
   one-sided `CI_low` whisker, sorted by `E_cell`, coloured by `viable_status`; matched-random and
   MA-seg baseline medians overlaid as markers per cell. *Answers: is conditioned expectancy > 0 and
   above baselines, per cell, and how many clear it?*
2. **P11 composition heatmap**: instrument (rows) × domain (cols) grid, each cell coloured by status
   (`VIABLE` / `CI_SPANS_0` / `NOT_VIABLE_BY_POWER` / `COVERAGE_EXCLUDED`), annotated with `m` and
   `E_cell`. *Answers: does the ≥5-cells-over-≥3-instruments quorum hold, and where is it concentrated?*
3. **Per-event return distribution by arm** (violin/box of ATR-normalised `r_e`, pooled across viable
   cells, per-cell medians overlaid): signal STAT, signal HA, matched-random, MA-seg. *Answers: the
   distribution shape (justifies the median), where mass sits relative to 0, FAV/ADV/TIMECAP structure.*
4. **Conditioning event-count / retained-fraction map**: per cell, qualifying-event count and retained
   fraction `f` (conditioned ÷ unconditioned harami base), with the 30-event power floor marked.
   *Answers: how much conditioning costs in power; how many cells survive to be reportable.*

---

## Interpretation Guide (predefined, mechanical)

- **EVIDENCE_FOR** (conditioned efficacy supported) iff **all**:
  (i) `V_sig ≥ 5` AND `I_sig ≥ 3` (signal clears P11 on the binding endpoint); **and**
  (ii) the **baseline-beat** composition also clears P11 — `#{cells: viable AND beats_both} ≥ 5` over
  `≥3` instruments. → The `/STRONG`-conditioned, harami-anchored signal has positive gross expectancy
  beyond matched controls on benchmark geometry. *(Reason: the family's defining conjunction, anchored
  at its claimed lead point, produces a robust, control-beating positive median across the grid.)*
- **EVIDENCE_AGAINST** (not supported on benchmark geometry) iff there are **enough powered cells to
  adjudicate** — `P_powered ≥ 5` over `≥3` instruments — **and** EVIDENCE_FOR fails (signal misses the
  P11-viable quorum, **or** clears it but the baseline-beat composition does not). → Recorded as a
  measured-negative characterization; routing deferred to the single 014-B G2 across the full slate.
  *(Reason: with adequate power, the conditioned signal's median is not reliably positive and/or not
  above what a random in-progress-move entry achieves.)*
- **INCONCLUSIVE (power-limited)** iff `P_powered < 5` **or** `I_powered < 3` (a P11 quorum of powered
  cells cannot be formed) with no correctness failure. → Conditioning dropped too many cells below 30
  qualifying events to adjudicate; disclosed, never defaulted to a ratio. *(Reason: insufficient
  coverage, not absence of effect.)*
- **SUBSTRATE/METHOD_DEFECT** iff any determinism, causality, or invariant check fails (Step "Implementation
  safety") → fix before reporting; no efficacy claim.

Disclosed-only (never change the verdict): the `/STRONG-HA` arm, mean expectancy,
first-hit `r`, win rate, TIMECAP fraction, and the STAT-MAD / HA-any-direction sensitivities. Their
agreement or divergence is reported for context.

---

## Implementation Safety / Constraints for `experiment-developer`

- **Holdout / TEST**: slice the **1-minute base** to `[0, int(0.7·int(0.7·total_rows)))` before any
  aggregation; never materialize TEST or the final-30% holdout. No new-universe holdout/TEST row is read.
- **Temporal order & alignment**: sort domain bars by `CloseTime`; align HA↔real and harami↔bar grid by
  **exact `CloseTime` match** (searchsorted + equality assert), never by bar index. Map move
  `ConfirmTime`/`EndTime` to bar indices the same way.
- **Causality (assert in code)**: every quantity at a harami bar `t_i` uses only bars `≤ t_i` and only
  moves with `ConfirmTime ≤ t_i`; barriers/time-cap use only moves confirmed strictly before `t_i`; the
  first-touch scan starts at `entry_idx+1`. `M_sofar` uses only `C` (the harami close at `t_i`) and the
  known `StartPrice_inprogress` pivot — no future bar, no running extreme.
- **Sequential vs vectorized**: keep the **P15 first-touch resolver** and the **live in-progress-state
  walk** as explicit bounded loops (their causal/streaming semantics are the object under test —
  do not vectorize). Trailing-magnitude windows, MA segmentation, and the bootstrap **index
  construction** may be vectorized in bounded batches (reuse the `block_bootstrap_ci` batching).
- **Denominators / zero-baseline**: qualifying population = FAV/ADV/TIMECAP (built barrier); `< 30` →
  `NOT_VIABLE_BY_POWER` (no ratio); `M_sofar = 0`, NaN `ATR_entry`, and warmup → excluded
  with disclosed counts.
- **Determinism**: single master seed in constants; per-cell/per-purpose RNG via `default_rng(master +
  stable_offset)`; emit a **determinism self-check** (re-run one cell end-to-end, assert byte-identical
  outputs) and a **reconciliation** anchor (recompute one cell's FAV/ADV counts and one `r_e` by hand /
  independent path, assert match) — these double as the SUBSTRATE/METHOD_DEFECT guards.
- **Progress / memory**: `tqdm` over the 99-cell grid (× arms); per-cell bounded memory (process and
  discard each cell; persist only per-cell summary rows + a bounded per-event parquet for plots).
- **Real-price discipline**: HA prices only in `detect_ha_harami` and `annotate_ha_impulse`; `C`,
  `M_sofar`, barriers, fills, `ATR_entry`, returns, `r`, win rate **all** on real domain OHLC.
- **New module** `xen/expectancy.py` (reused EXP-054–060): live in-progress state, P15 path-ordered
  resolver, realised-return, and the **median** moving-block bootstrap. Everything else reuses
  `xen.zigzag`, `xen.heiken_ashi_generator`, `xen.ha_harami`, `xen.strong_move`,
  `xen.capture_barriers` (`time_caps` durations, bootstrap block construction), `xen.bar_aggregator`.
- **Frozen constants** (no tuning): `atr_period=14`, `atr_mult=1.0`, `X=0.50`, R:R `1:1`,
  time-cap `(k=1.5, window=20, floor=6, median)`, STAT `(window=20, min=5, q=0.75)`, HA `run_len=3`,
  `RESOLVED/POWER_FLOOR=30`, `N_BOOT=10_000`, `BOOT_BATCH=2_000`, `P11 = (≥5 cells, ≥3 instruments)`.

---

## Complexity Check

- **Statistical tests: 4 / 4** — (1) signal median block-bootstrap CI; (2) matched-random median
  bootstrap; (3) MA(20,50)-segmentation median bootstrap; (4) signal−baseline contrast CI. (`/STRONG-HA`
  arm, MAD/any-dir sensitivities, mean, `r`, win rate, TIMECAP fraction reuse these
  methods as **disclosed secondaries** — no new method.)
- **Geometry note:** EXP-049's G1/G2 favourable constructions collapse to a single identical target
  under the current-price magnitude-so-far reference (Step 3 proof); EXP-053 computes one benchmark
  favourable geometry, not two.
- **Visualisations: 4 / 4** — forest plot; composition heatmap; return-distribution-by-arm; retained
  fraction/event-count map.
- **New modules: 1 / 1** — `xen/expectancy.py` (P15 fill + P14 realised-return + median bootstrap).
