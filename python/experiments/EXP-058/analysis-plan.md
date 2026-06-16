# Analysis Plan: Experiment EXP-058 — Third-Barrier Geometry (Conditioned HA Harami; `/THIRD-TIME`, `/THIRD-EVENT` vs Benchmark Adaptive Cap)

## Objective

Determine whether, on the **live `/STRONG`-conditioned HA harami** (entered at the harami confirmation-bar
close, faded against the in-progress strong move; the **identical population** to EXP-053/056/057),
**changing only the third-barrier geometry** raises gross per-event **median** expectancy (P14:
ATR-normalised realised return under P15 path-ordered fills, regime-clustered moving-block bootstrap CI)
above the **benchmark adaptive time cap** (P4, floor=6). The **favourable** target (benchmark 50%-of-`M_sofar`)
and the **adverse** target (benchmark 1:1) are held fixed for every variant — pure one-at-a-time (OAT)
variation of the **third barrier** over a **predeclared variant sweep**:

| # | Variant id | Class | Third barrier (per-event window `n_event`, in real bars after entry) | Binding? |
|---|-----------|-------|----------------------------------------------------------------------|----------|
| 1 | `BENCH` | benchmark (P4) | `N = max(6, round(1.5·median(trailing-20 durations)))` | binding (reference) |
| 2 | `THIRD-TIME-T12` | `/THIRD-TIME` | `N = max(12, round(1.5·median(durations)))` (floor=12) | binding |
| 3 | `THIRD-TIME-T24` | `/THIRD-TIME` | `N = max(24, round(1.5·median(durations)))` (floor=24) | binding |
| 4 | `THIRD-TIME-T48` | `/THIRD-TIME` | `N = max(48, round(1.5·median(durations)))` (floor=48) | binding |
| 5 | `THIRD-EVENT` | `/THIRD-EVENT` | `min(bars to next `rd`-confirm after entry, 8·bench_N)` | binding |

The deliverable is a **characterization readout** (`THIRD_BARRIER_CHARACTERISED`) feeding the single 014-B
G2 — **no gate is adjudicated here, no candidate registered, 0 slots / 0 TEST reads**, TRAIN-only, gross.
Detection on HA candles; **every outcome metric on real domain-bar OHLC**, never HA prices. Methods are
non-parametric (bootstrap of a robust median); no normality/stationarity/i.i.d. assumption.

> **Scope-fidelity notes / methodological posture (resolved within scope, not broadened):**
> 1. **The variant−benchmark contrast is *paired*.** Every variant is scored on the *same* conditioned
>    harami events as the benchmark — only the third barrier (and hence the resolved class/exit) differs —
>    so the per-event returns are positively correlated. The contrast is therefore a **paired** block
>    bootstrap on the **common qualifying-event subset** (events resolved under both that variant and the
>    benchmark), using `xen.favourable_targets.paired_median_contrast_ci`, not the independence-assuming
>    `xen.expectancy.contrast_ci`. This is the correct operationalization of the scope's named
>    "variant − benchmark contrast", not a new test. (Same posture as EXP-056/057.)
> 2. **P13 baselines (matched-random, MA-seg) are *disclosed secondaries* and do NOT enter the binding
>    verdict.** The scope's binding EVIDENCE_FOR limb (b) is the **variant−benchmark** contrast; the
>    benchmark variant already carries EXP-053's "beats matched controls" result. Baselines are computed
>    per variant for context/robustness and reported, but the EVIDENCE_* label is decided on
>    own-viability + benchmark-contrast only. (Confirmed consistent with the scope §Baselines.)
> 3. **No within-experiment family-wise correction across the 5 variants** (multiplicity posture, §Step 8
>    and §Multiplicity). EXP-058 *emits* uncorrected per-variant readouts; the binding family-wise
>    inference is deferred to the single 014-B G2 across the full surface (programme/registry pattern).
> 4. **Censoring is the binding-disclosed trade-off, not a verdict input.** Extending the horizon is
>    *expected* to raise the `DATA_CENSORED` fraction (longer windows hit the TRAIN data edge) and thereby
>    erode qualifying counts. The censoring fraction is reported prominently per variant per cell because it
>    is the cost side of the third-barrier lever and the mechanism of an INCONCLUSIVE read — but it never
>    binds; viability is decided on **median expectancy** over the qualifying population (P14).
> 5. **First-hit `r` is a disclosed secondary expected to stay near 0.50.** Favourable/adverse geometry is
>    held at benchmark 1:1, so `r` should not move materially across variants; the third-barrier lever moves
>    expectancy through the **TIMECAP exit price** (where the cap/event bar's close lands) and the
>    **FAV-vs-TIMECAP composition** (a longer horizon lets a would-be-time-stopped winner run to the
>    favourable target, or lets a would-be winner give back into a worse close), not through `r`. Reported
>    for completeness; never binding (lessons §8.6: match the metric to the mechanism).

---

## Methodology

The construction Steps 1–2 (substrate, HA, harami, live in-progress state, `/STRONG-STAT` binding +
`/STRONG-HA` disclosed conditioning) are **identical to EXP-053/056/057** and **reuse the same
`xen.expectancy` functions** (`live_in_progress_state`, `live_strong_stat`) so the binding conditioned
population is **byte-identical to EXP-053's** (verified in Step 9 reconciliation). They are summarised here
and not re-derived. Steps 4–9 (P15 resolution, median bootstrap, baselines, contrasts, composition, gates)
reuse the EXP-056/057 kernels unchanged; **only Step 3 (the third-barrier construction) is new, and within
it only the `/THIRD-EVENT` cap helper is new code — the `/THIRD-TIME` caps re-call an existing function.**

### Step 1: Per-cell construction (reused from EXP-053/056/057)

- **Method**: per cell (instrument × domain), TRAIN slice only. Holdout/TEST-safe load: lazy
  `pl.scan_parquet`; `total_rows`; `train_rows = int(int(total_rows·0.7)·0.7)`; collect only the first
  `train_rows` file-order 1-minute rows (F01 prefix; never sort/collect the full file, never read TEST or
  holdout); assert chronological; `train_end_ts = max(CloseTime)`. Aggregate the domain via
  `xen.bar_aggregator.aggregate_ohlc` (5m strict; others `min_coverage=0.90`); fence to
  `CloseTime ≤ train_end_ts`. ZigZag substrate `xen.zigzag.generate_zigzag(bars, atr_period=14,
  atr_mult=1.0)` → confirmed moves; real-bar `ATR_entry` from `xen.zigzag.wilder_atr(High,Low,Close,14)`;
  HA candles (`xen.heiken_ashi_generator`); haramis `xen.ha_harami.detect_ha_harami` mapped to domain-bar
  indices by **exact `CloseTime` match** (searchsorted + equality assert); live in-progress state
  `xen.expectancy.live_in_progress_state` → `(valid, k, rd, start_price, start_epoch, m_sofar)`.
- **Why**: frozen, separately-validated D0 primitives (EXP-048 PASS); compose, do not re-derive. The live
  in-progress state anchors at the harami *before* the ZigZag confirms (the family's claimed lead).
- **Simpler alternative considered**: re-deriving the conditioned population from raw detectors — rejected;
  reuse the EXP-053 functions verbatim so the population is identical by construction (Step 9 anchor).
- **Assumptions**: ZigZag pivots are future information until confirmed (only moves with `ConfirmTime ≤ t_i`
  and the known `EndPrice_k` pivot are used); `C` is the harami bar's own close; alignment by `CloseTime`,
  never bar index.
- **Expected output**: per cell, the ordered harami-event table with `entry_idx, C, rd, M_sofar, ATR_entry`,
  the confirmed-move arrays (`Direction`, `ConfirmTime`/`confirm_epoch`, magnitudes) and `confirm_idx`
  (`xen.capture_barriers.confirm_indices`).

### Step 2: Live conditioning — `/STRONG-STAT` (binding) and `/STRONG-HA` (disclosed) (reused from EXP-053/056/057)

- **Method**: `/STRONG-STAT` (binding, P7): `xen.expectancy.live_strong_stat` with window 20, min 5, q 0.75
  → `retained_p75` (binding) and `retained_mad` (disclosed sensitivity); retained iff
  `M_sofar ≥ p75(trailing-20 confirmed-move magnitudes)`; `<5` prior moves → NO_DECISION/warmup-excluded.
  `/STRONG-HA` (disclosed, P8): `xen.strong_move.annotate_ha_impulse` (window 20, min 5) +
  `find_impulse_runs(run_len=3)`; retain iff a same-direction completed impulse run lies inside the
  in-progress span and completed at/before `t_i`. Trade direction `rd` from Step 1 for both arms; **no
  `/BARCFG` filter**.
- **Why**: P16 — `/STRONG-STAT` is the live conditioning that defines the family signal; position-in-move
  (EXP-050) is descriptive-only and never a filter.
- **Simpler alternative considered**: a single arm (binding only) — rejected; the `/STRONG-HA` disclosed arm
  is a registered robustness check, run through the identical pipeline at marginal cost.
- **Assumptions**: magnitude-percentile is computed over completed confirmed moves only (causal).
- **Expected output**: per cell, the binding `/STRONG-STAT`(p75) retention mask, the `/STRONG-HA` and
  STAT-MAD disclosed masks, retained counts, and retained fraction `f` (sanity vs EXP-051 0.20–0.27 /
  EXP-053).

### Step 3: Third-barrier construction per variant (the **new module**, `xen/third_barrier.py`)

For each **retained** harami event, the **favourable** and **adverse** targets are the benchmark objects,
identical across all five variants: `xen.expectancy.benchmark_barriers(C, rd, m_sofar)` →
`fav = C + rd·0.50·M_sofar`, `adv = C − rd·0.50·M_sofar` (1:1). Variants differ **only** in the per-event
window length `n_event` (real bars after entry) passed to the shared P15 resolver. All on **real prices**.

- **`BENCH`** (reference, P4 floor=6): `N = max(6, round(1.5·median(trailing-20 durations)))` via
  `xen.expectancy.adaptive_time_caps_by_epoch(entry_epoch, move_confirm_epoch, confirm_idx, window=20,
  k_mult=1.5, floor=6, min_moves=5)` → `(n_event_bench, warmup_bench)`. `< 5` trailing durations → warmup
  (no barrier). Reproduces EXP-053 (per-cell median + `r≈0.50` expected).

- **`THIRD-TIME-T12/T24/T48`** (no new code): the **same** `adaptive_time_caps_by_epoch` re-called with
  `floor ∈ {12, 24, 48}` and every other knob at benchmark (`window=20`, `k_mult=1.5`, `min_moves=5`) →
  `n_event_v = max(floor_v, round(1.5·median(durations)))`. The warmup mask is **identical** across all
  `/THIRD-TIME` variants and BENCH (warmup depends only on having `≥5` trailing durations, not on the
  floor), so the conditioned, non-warmup population is the same set of entries for all four time variants —
  only `n_event` (the horizon) changes. This is exactly the floor-only lever the operator predeclared.

- **`THIRD-EVENT`** (the **new** causal helper `third_event_caps`): for each retained event, locate the
  **smallest** confirmed-move index `j` with `Direction[j] == rd` **AND** `confirm_epoch[j] > entry_epoch`
  (the next reversal-direction structural confirmation strictly after entry; `searchsorted` on the ascending
  `confirm_epoch` for the strict-after lower bound, then advance to the first `rd`-direction move at/after
  that bound). Then:
  - `bars_to_event = confirm_idx[j] − entry_idx` if such `j` exists (and `confirm_idx[j] > entry_idx`,
    asserted), else `+∞`;
  - `backstop = 8 · n_event_bench` (the BENCH adaptive cap for that entry);
  - `n_event_evt = min(bars_to_event, backstop)`;
  - **Warmup/availability:** an entry that is BENCH-warmup (`warmup_bench` true, `n_event_bench` undefined →
    `backstop` undefined) is **excluded-with-record** for `/THIRD-EVENT` (disclosed count). For a non-warmup
    entry `n_event_bench ≥ 6` ⇒ `backstop ≥ 48` ⇒ `n_event_evt ≥ 1` (no degenerate zero-length window).
  - **Resolution semantics (via the unchanged resolver):** `resolve_path_ordered` scans
    `[entry+1, entry+n_event_evt]`; FAV/ADV bind if a target is hit first; else `TIMECAP` exiting at
    `close[entry+n_event_evt]` — the **`rd`-confirm bar's real close** when `bars_to_event ≤ backstop`, or
    the **backstop bar's real close** when the backstop bound; else `DATA_CENSORED` if the window is
    truncated by the TRAIN edge before resolution.
  - **Disclosed split:** per cell, the fraction of `/THIRD-EVENT` TIMECAP exits that bound on the **actual
    `rd`-confirm event** (`bars_to_event ≤ backstop`) vs on the **backstop** — an event-vs-time composition
    disclosure feeding the censoring narrative.

- **Why**: the registered `/THIRD-TIME` (floor-only horizon extension; operator decision) and `/THIRD-EVENT`
  (next-`rd`-ZigZag-confirm exit with an `8×` backstop; operator decision) third-barrier models, varied OAT
  against the frozen benchmark cap, with favourable/adverse legs held fixed so the read isolates the third
  barrier. Motivated directly by 014-A G1 (P4 collapsed to the 6-bar floor in 96/99 cells) and EXP-055
  (AVAILABILITY_GOOD — the lifetime move exists): does extending the holding horizon capture it?
- **Simpler alternative considered**: raising `k_mult` instead of the floor — rejected; with the cap
  floor-bound in 96/99 cells, raising `k_mult` would not change the binding cells, whereas the floor lever
  bites exactly where the constraint sits (operator decision §scope). A single longer time cap (no event
  variant) — rejected; `/THIRD-EVENT` tests a structurally different "give-up" rule registered separately.
- **Assumptions**: the `/THIRD-EVENT` exit is causal — it uses the next move confirmed with `ConfirmTime >
  entry` (known forward in real time, exactly as TIMECAP resolves at a forward bar) and exits at that
  confirmation bar's real close, never an unconfirmed pivot. The time-cap durations use only moves confirmed
  strictly before `t_i` (`adaptive_time_caps_by_epoch` semantics, unchanged).
- **Expected output**: per retained event, for each variant `(n_event, warmup/availability flag)`; for
  `/THIRD-EVENT` additionally `(bars_to_event, backstop, event_bound vs backstop_bound flag)`. The
  benchmark `fav/adv` arrays shared by all variants.

### Step 4: P15 path-ordered fill resolution + realised gross return per variant (reused kernels)

- **Method**: for each variant's retained, non-warmup event, resolve first-touch via
  `xen.expectancy.resolve_path_ordered` (explicit bounded sequential scan over
  `[entry_idx+1, min(entry_idx+n_event, last_idx)]` on real OHLC; same-bar double-touch resolved by the P15
  intrabar path — bullish `O→L→H→C`, bearish `O→H→L→C`) → classes `{FAV, ADV, TIMECAP, DATA_CENSORED}` and
  exit price (target level for FAV/ADV; cap/event-bar real **close** for TIMECAP). Realised gross return
  `xen.expectancy.realised_returns` → `r_e = rd·(exit − C)/ATR_entry`. Qualifying population
  `xen.expectancy.qualifying_mask` = built-barrier `{FAV,ADV,TIMECAP}` with finite exit and `ATR_entry>0`;
  `DATA_CENSORED` excluded (disclosed as the censoring count/fraction).
- **Why**: first-hit `r` is blind to the family's position-management value (P14/lessons §8.6); the
  realised-return endpoint is what the mechanism can express, and P15 is the adopted 014-B fill standard
  (EXP-054). The resolver loop's causal/streaming semantics are the object under test — **not vectorized**.
  The benchmark `fav/adv` are identical to BENCH across variants, so any class/return difference is
  attributable solely to the horizon (`n_event`) — the pure third-barrier OAT read.
- **Simpler alternative considered**: the EXP-049 worst-case tie-break — rejected; EXP-054 adopted P15 as
  the 014-B fill standard.
- **Assumptions**: the intrabar path is a documented approximation (1-minute base bars not replayed);
  disclosed; EXP-054 bounded its effect as immaterial (median Δr 0.010).
- **Expected output**: per variant per cell, the entry-time-ordered `r_e` series and the
  `(FAV,ADV,TIMECAP,DATA_CENSORED, warmup/availability-excluded)` counts.

### Step 5: Per-cell median expectancy + regime-clustered moving-block bootstrap *(stat methods 1–2)*

- **Method**: per cell × variant × arm (`/STRONG-STAT` binding; `/STRONG-HA` disclosed),
  `E_cell = median(r_e over qualifying events)`. CI via `xen.expectancy.bootstrap_median_distribution`
  (events in entry-time order; block `b = max(1, round(m^(1/3)))`; `ceil(m/b)` contiguous blocks per
  resample truncated to `m`; `N_BOOT=10_000`; batched; **fixed seed = master + stable per-(cell,variant)
  offset**) → `median_ci` one-sided `CI_low` (5th pct) + two-sided (2.5/97.5). **Method 1** = each variant's
  signal median CI; **method 2** = each P13 baseline median CI (Step 6). The mean is a disclosed secondary.
- **Why**: the per-event ATR-normalised return distribution is fat-tailed (FAV/ADV cluster near
  `±dist/ATR`; the TIMECAP mass spreads and shifts as the horizon lengthens) → the **median** is the robust
  location estimator (P14); the moving-block bootstrap is non-parametric and preserves local serial/regime
  dependence.
- **Simpler alternative considered**: sign / Wilcoxon test on `r_e>0` — rejected as binding (assumes
  exchangeable events, tests a different null); normal-theory t-CI rejected (fat tails). Reported informally
  at most.
- **Expected output**: per cell × variant × arm `(m, E_cell, CI_low_1s, CI_lo_2s, CI_hi_2s, block_len, mean,
  r, win_rate, timecap_frac, censored_frac)` and `viable_status` (`VIABLE` iff `CI_low_1s>0` AND `m≥30`;
  else `CI_SPANS_0` / `NOT_VIABLE_BY_POWER`).

### Step 6: P13 baselines through the identical per-variant pipeline (disclosed) *(method 2 reused)*

- **Method**: both baselines are scored through the **identical** Step 3–5 pipeline **for every binding
  variant** (benchmark favourable/adverse targets, the variant's third barrier, P15 fills, median + same
  bootstrap), marked **disclosed-only**:
  1. **Matched-count random in-regime timestamps**: draw the same count as the variant's qualifying events,
     without replacement, from the cell's eligible-bar pool (TRAIN bars with a defined in-progress move,
     defined `ATR_entry`, defined BENCH cap, and not a retained-signal bar); each drawn bar takes the
     **in-progress `rd`** at that bar (direction is NOT randomised), computes its own `M_sofar`, benchmark
     fav/adv, and the variant's third-barrier `n_event` identically (its own `bench_N`/durations for
     `/THIRD-TIME`; its own next-`rd`-confirm + `8×bench_N` for `/THIRD-EVENT`). Fixed per-(cell,variant)
     seed, distinct RNG stream from the bootstrap.
  2. **MA(20,50) segmentation**: replace the ATR-ZigZag substrate with MA(20,50)-crossover segments on
     domain `Close` (EXP-050/053 arm); re-run the full conditioned-signal pipeline (harami + current-price
     magnitude-percentile + harami anchor + benchmark fav/adv + the variant's third barrier + P15) on MA
     segments. For `/THIRD-EVENT` under MA-seg, the opposing event is the next MA-segment confirmation with
     `Direction == rd` and `ConfirmTime > entry`, with the same `8 × bench_N` backstop computed from the
     MA-seg benchmark cap.
- **Why**: P13/P20. Disclosed robustness — does a given third-barrier geometry beat random entries (matched
  count, same geometry, same regime pool, same direction rule) and is any effect ZigZag-specific?
- **Simpler alternative considered**: omit baselines — rejected; P13/P20 require both as disclosed
  secondaries (the registry's matched-control discipline).
- **Note (runtime)**: this is the compute-dominant part (≈ 5 variants × 2 baselines × 99 cells × 10k
  bootstrap, and the longer-horizon variants scan more bars per event). It is **disclosed-only** and must
  not block the binding read; `tqdm`, bounded per-cell memory, fixed seeds. A baseline cell with `< 30`
  matched events is `NOT_VIABLE_BY_POWER` (disclosed), never an undefined ratio.
- **Expected output**: per cell × variant, baseline `(m, E_cell, CI_low_1s, …, censored_frac)` for
  matched-random and MA-seg, same schema as Step 5.

### Step 7: Contrasts — variant−benchmark (paired, binding) and variant−baseline (independent, disclosed) *(stat methods 3–4)*

- **Method 3 — variant − benchmark (PAIRED; binding):** the variant and the benchmark are evaluated on the
  **same conditioned events** (same favourable/adverse targets; only the third-barrier horizon differs), so
  the contrast is paired on the **common qualifying-event subset** `S = {events qualifying under BOTH this
  variant and BENCH}` (entry-time ordered). Use `xen.favourable_targets.paired_median_contrast_ci` (a paired
  moving-block bootstrap: one set of block indices applied to **both** the variant `r_e` and the benchmark
  `r_e` restricted to `S`; statistic `Δ* = median(variant_S*) − median(BENCH_S*)`), one-sided `CI_low(Δ)`
  (5th pct) + two-sided. **Variant beats benchmark in a cell iff `CI_low(Δ) > 0` AND `|S| ≥ 30`.** Pairing
  on the same resample indices cancels the shared event/regime noise → the correct (tighter) difference CI;
  `xen.expectancy.contrast_ci` is **not** used here (it would over-state variance).
- **Method 4 — variant − baseline (INDEPENDENT; disclosed):** variant signal vs each P13 baseline are
  **independent** event sets (different timestamps) → use `xen.expectancy.contrast_ci` (independent block
  bootstraps). Disclosed-only.
- **Matched cells in the quorum**: the benchmark-beat composition counts only cells where **both** the
  variant and BENCH are reportable (`m_variant ≥ 30` AND `m_BENCH ≥ 30` AND `|S| ≥ 30`); a cell where BENCH
  is itself non-viable is **not** counted as a "beat" — recorded separately as `variant_viable_where_bench_not`.
- **`/THIRD-EVENT` / long-horizon pairing note**: `S` for an alternative vs `BENCH` is the subset where both
  resolve into the qualifying set. A longer horizon does not change an event already resolved FAV/ADV early
  (the early touch binds identically under both), so those pair exactly; the contrast's signal lives in
  events the benchmark TIMECAP'd at floor=6 that the longer horizon resolves differently — provided they are
  not pushed into `DATA_CENSORED` (in which case they leave `S`, reducing `|S|` — the censoring–power tension
  surfaces directly in `|S|`). This is the intended paired comparison.
- **Expected output**: per cell × variant, `CI_low(Δ_bench)` (paired) + the `beats_bench` boolean and `|S|`;
  `CI_low(Δ_random)`, `CI_low(Δ_MA)` (independent, disclosed).

### Step 8: P11 composition + mechanical EVIDENCE_* classification (binding)

- **Method** (binding arm `/STRONG-STAT`, all gross, TRAIN-only, **per variant**):
  - `viable[variant,cell] = (CI_low_1s(variant) > 0) AND (m ≥ 30)`.
  - `beats_bench[variant,cell] = (CI_low(Δ_bench) > 0) AND (m_variant≥30 AND m_BENCH≥30 AND |S|≥30)`.
  - `win[variant,cell] = viable AND beats_bench`.
  - Per variant: `V = #viable cells`, `I_V = #instruments`; `W = #win cells`, `I_W = #instruments`;
    `P_powered = #cells with m≥30`, `I_powered`.
  - **P11**: a composition holds iff **≥5 cells over ≥3 instruments**.
  - **Variant passes** iff its `win` composition clears P11 (`W≥5 AND I_W≥3`).
- **No within-experiment family-wise correction** (see §Multiplicity). All 4 binding alternatives (plus the
  benchmark reference) are reported; the verdict is descriptive and feeds G2.
- **Expected output**: per-variant composition tallies, the variant-pass booleans, the EVIDENCE_* label, and
  the multiplicity disclosure block → `composition_readout.json` + `third_barrier_map.csv`.

### Step 9: Determinism, causality, reconciliation, invariant gates (binding correctness)

- **Determinism**: re-run one cell per instrument (first usable) end-to-end; assert byte-identical per-cell
  per-variant outputs (binding `/STRONG-STAT` arm across all five variants + both baselines). Any mismatch →
  SUBSTRATE/METHOD_DEFECT.
- **Causality / invariants (assert in code)**: every quantity at `t_i` uses only bars `≤ t_i` and moves with
  `ConfirmTime ≤ t_i` *for construction at entry*; the `/THIRD-TIME` caps use only durations of moves
  confirmed strictly before `t_i`; the `/THIRD-EVENT` exit move has `ConfirmTime > t_i` and
  `confirm_idx > entry_idx` (a strictly forward exit, asserted); first-touch scans start at `entry_idx+1`
  and read no bar with `CloseTime > train_end_ts` (else DATA_CENSORED); `fav_dist > 0` for every resolved
  event. Violation on ≥3 instruments → SUBSTRATE/METHOD_DEFECT.
- **Predeclared invariant checks (named in the scope; assert + report):**
  1. **Benchmark reproduces EXP-053**: the `BENCH` variant's per-cell median expectancy **and** first-hit
     `r` (≈0.50) match EXP-053's benchmark `E_cell`/`r` on the same grid to numerical tolerance (`|Δ| ≤ 1e-9`
     on the shared events; same detector/filter/fence/geometry/cap, same functions). The conditioned
     `/STRONG-STAT` population (count + per-cell `entry_epoch` digest) matches EXP-053 exactly.
  2. **Cap monotonicity in floor, event-wise**: for every retained non-warmup event,
     `n_event_BENCH ≤ n_event_T12 ≤ n_event_T24 ≤ n_event_T48` (raising the floor can only raise the cap).
     Assert elementwise; any violation → SUBSTRATE/METHOD_DEFECT.
  3. **`/THIRD-EVENT` cap bounds**: for every retained non-warmup event, `1 ≤ n_event_evt ≤ 8·n_event_BENCH`,
     and where the event bound (`bars_to_event ≤ backstop`) the exit bar is a confirmed `rd`-direction move
     with `ConfirmTime > entry`. Assert; any violation → SUBSTRATE/METHOD_DEFECT.
  4. **Warmup-set identity across time variants**: the conditioned non-warmup population is identical for
     BENCH/T12/T24/T48 (the floor does not change the warmup mask). Assert the masks are equal; a difference
     would indicate a cap-construction bug → SUBSTRATE/METHOD_DEFECT.
- **Population reconciliation (vs EXP-053)**: emitted as `population_reconciliation.csv` — the binding
  conditioned-event set and the `BENCH` per-cell median/`r` vs EXP-053. Exact match expected; any mismatch
  is a defect investigated before the readout is trusted.
- **Expected output**: `determinism_ok`, `causality_ok`, `reconciliation_ok`, `invariants_ok` flags + the
  per-cell BENCH-vs-EXP-053 diff table.

---

## Multiplicity posture (predeclared)

EXP-058 is **gross, 0-slot, 0-TEST characterization** feeding the **single 014-B G2** (the design forbids
intermediate gates and early closure). The cross-variant multiplicity is controlled by, in order:

1. **Full predeclaration + report-all (file-drawer/registry control).** All 5 binding variants are
   predeclared in the scope and **every** one is reported with its full per-cell readout — none is drawered
   or selected post-result. Primary multiplicity control (registry pattern).
2. **P11 breadth as the robustness filter.** A "variant passes" requires viability **and** benchmark-beat on
   **≥5 cells over ≥3 instruments** — far stronger against per-cell noise than any single uncorrected CI.
3. **Deferral of binding family-wise inference to G2.** EXP-058 applies **no** Holm/Bonferroni across the
   variants; its per-variant `CI_low` thresholds are **uncorrected one-sided 95%**. The binding family-wise
   correction across the full 014-B surface (favourable/adverse/third/exit geometries) is the **single G2
   desk adjudication**'s responsibility, on the complete slate — not this experiment's.
4. **Multiplicity disclosure (no new statistical method).** The readout reports, for the desk: the number of
   binding variants that pass (`n_pass`), the per-variant `(W, I_W)` margins above the P11 quorum, and a
   **fragility flag** for any pass resting on a bare quorum (exactly 5 cells or exactly 3 instruments). No
   computed permutation null is added (stays within the 4-method budget).

This posture is fixed before results exist and is not revisited after seeing them.

---

## Visualisations (5 / 5)

1. **Per-variant median-expectancy forest plot** (binding `/STRONG-STAT` arm): for each binding variant,
   member cells' `E_cell` with one-sided `CI_low` whiskers, faceted/colour-grouped by variant, with the
   `BENCH` per-cell median overlaid as a reference marker. *Answers: is each variant's conditioned expectancy
   > 0 per cell, and how does it sit vs benchmark as the horizon lengthens?*
2. **Variant − benchmark contrast heatmap**: alternatives (rows) × cells (cols), cell colour = paired
   `CI_low(Δ_bench)` sign/magnitude (with `beats_bench` hatching). *Answers: which third-barrier variant
   beats benchmark, where, and is it coherent across cells/instruments or scattered?*
3. **Pooled per-event return distribution by variant** (violin/box of ATR-normalised `r_e` across viable
   cells, per-variant medians + the BENCH median line overlaid). *Answers: distribution shape (justifies the
   median), where mass sits vs 0, and how the TIMECAP mass moves as the horizon lengthens — the mechanism of
   any expectancy change.*
4. **First-hit `r` + P11 "wins-over-benchmark" composition map** (combined panel): (a) per-variant `r`
   distribution across cells with the 0.50 reference line (the disclosed near-0.50 expectation under fixed
   1:1 geometry); (b) instrument × domain `win / viable-only / CI_SPANS_0 / NOT_VIABLE_BY_POWER /
   COVERAGE_EXCLUDED` status grid per variant. *Answers: did `r` stay near 0.50 (as expected), and does any
   variant clear ≥5 cells / ≥3 instruments on the binding endpoint?*
5. **Censoring + TIMECAP composition / power map by variant** (the horizon-vs-power trade-off): per variant,
   the pooled `DATA_CENSORED` fraction and TIMECAP fraction (and, for `/THIRD-EVENT`, the event-vs-backstop
   split) alongside per-cell qualifying-event counts with the 30-event power floor marked. *Answers: how much
   each longer horizon costs in censoring/power and how many cells survive to be reportable — central to an
   INCONCLUSIVE read.*

Secondary tables (`/STRONG-HA` arm, STAT-MAD arm, both P13 baselines and their contrasts, `r`/win-rate/
TIMECAP/censoring fractions, `/THIRD-EVENT` event-vs-backstop split, per-variant exclusion counts) go to CSV,
not plots.

---

## Interpretation Guide (predefined, mechanical)

Binding arm `/STRONG-STAT`; per variant; all gross; TRAIN-only. Let a variant **pass** iff its `win`
composition clears P11 (`W ≥ 5` over `≥3` instruments), where `win = viable AND beats_bench` (Step 8).

- **EVIDENCE_FOR** (a third-barrier lever helps) iff **≥1 binding alternative variant passes** — it is
  viable on its own median expectancy **and** beats the benchmark on the paired contrast, on ≥5 cells over
  ≥3 instruments. → At least one alternative third-barrier geometry improves conditioned capture over the
  floor-6 benchmark cap on this surface leg. Report **all** passing variants and their margins; **no
  candidate registration / no selection of a single winner** (G2 only). *(Reason: extending the holding
  horizon, time- or event-based, converts the available longer-horizon move (EXP-055) into higher gross
  median expectancy, robustly across the grid.)*
- **EVIDENCE_AGAINST** (third-barrier geometry is not a lever) iff there are **enough powered cells to
  adjudicate** — for the benchmark and ≥1 alternative, `P_powered ≥ 5` over `≥3` instruments — **and no**
  binding alternative variant passes. → Recorded as a measured-negative characterization; routing deferred
  to the single 014-B G2. *(Reason: with adequate power, no longer horizon reliably beats the benchmark cap;
  the third barrier is not where conditioned capture is gained — consistent with a symmetric path where
  extra time gives FAV and ADV equally, and TIMECAP exits were not systematically cutting winners.)*
- **INCONCLUSIVE (power-limited)** iff a P11 quorum of powered cells **cannot be formed** for the benchmark
  and the alternatives (`P_powered < 5` or `I_powered < 3` on the variants of interest), with no correctness
  failure. → Censoring/warmup exclusions (expected to bite hardest on T48 and `/THIRD-EVENT`) depleted counts
  below the adjudication floor; disclosed, never defaulted to a ratio. *(Reason: insufficient coverage at the
  longer horizons, not absence of effect — the censoring map quantifies it.)*
- **SUBSTRATE/METHOD_DEFECT** iff any determinism, causality, invariant, or reconciliation gate fails
  (Step 9 — including the four predeclared invariant checks) → fix before reporting; no efficacy claim.

Disclosed-only (never change the verdict): the `/STRONG-HA` arm, mean expectancy, **first-hit `r`** (expected
to stay ≈0.50 under fixed 1:1 geometry — a material move off 0.50 would itself be a flagged surprise to
report), win rate, **per-variant censoring fraction** (the binding-disclosed trade-off), TIMECAP fraction,
`/THIRD-EVENT` event-vs-backstop split, the STAT-MAD sensitivity, and both P13 baselines and their
(independent) contrasts. Their agreement/divergence is reported for context — in particular, the
**expectancy-vs-censoring trade-off** is the headline lesson: a longer horizon that raises median expectancy
but censors a large fraction of events (eroding power) is a different finding from one that raises expectancy
cheaply, and both differ from a horizon that simply admits more symmetric noise (expectancy flat, `r` ≈ 0.50,
censoring up).

---

## Implementation Safety / Constraints for `experiment-developer`

- **Holdout / TEST**: slice the **1-minute base** to the first `int(int(total_rows·0.7)·0.7)` file-order
  rows before any aggregation; never materialize TEST or the final-30% holdout. No new-universe holdout/TEST
  row is read (the conditioned event definition already had its first TRAIN contact in EXP-053). The longer
  horizons and the `/THIRD-EVENT` backstop scan **only** within the TRAIN slice; a window extending past
  `train_end_ts` resolves to `DATA_CENSORED`, never to a TEST/holdout row.
- **Temporal order & alignment**: sort/assert domain bars by `CloseTime`; align HA↔real and
  harami/move-times↔bar grid by **exact `CloseTime` match** (searchsorted + equality assert), never by bar
  index. The `/THIRD-EVENT` exit bar is located from `confirm_idx[j]` (the exact-matched confirmation index),
  not by bar-count arithmetic across views.
- **Causality (assert)**: every quantity at `t_i` uses only bars `≤ t_i` and moves `ConfirmTime ≤ t_i` for
  construction; the time cap uses only moves confirmed strictly before `t_i`; the `/THIRD-EVENT` exit move
  satisfies `ConfirmTime > t_i` and `confirm_idx > entry_idx` (forward exit); first-touch scans start at
  `entry_idx+1`; `M_sofar` uses only `C` and the known `StartPrice_inprogress`.
- **Sequential vs vectorized**: keep the **P15 first-touch resolver** (`resolve_path_ordered`) and the
  **live in-progress-state walk** explicit/bounded (causal semantics under test — do not vectorize). The
  `/THIRD-EVENT` cap helper may use `searchsorted` for the strict-after lower bound and a vectorized
  next-`rd`-direction lookup **only** if it is provably equivalent to a forward scan and references no move
  with `ConfirmTime ≤ entry` for the exit (prefer the explicit per-event forward index search; the
  populations are small). `/THIRD-TIME` caps come from `adaptive_time_caps_by_epoch` unchanged. Bootstrap
  index construction and MA segmentation may be vectorized in bounded batches (reuse the existing batching).
- **Denominators / zero-baseline**: qualifying population per variant = FAV/ADV/TIMECAP (built barrier);
  `< 30` → `NOT_VIABLE_BY_POWER` (no ratio); warmup (`<5` cap durations; NO_DECISION `/STRONG-STAT`;
  `/THIRD-EVENT` BENCH-warmup) and DATA_CENSORED events are excluded with **disclosed per-variant counts**.
  First-hit `r` uses `n_FAV/(n_FAV+n_ADV)` (TIMECAP excluded from the `r` denominator, EXP-049 convention).
  The censoring fraction is `n_DATA_CENSORED / n_built_window` per variant per cell (reported). The paired
  benchmark contrast uses the **common** qualifying subset `S` with `|S| ≥ 30`.
- **Determinism / seeds**: single master seed in constants; per-(cell,variant,purpose) RNG via
  `default_rng([master, cell_index, purpose+variant_idx])` (distinct streams for bootstrap vs matched-random
  draws — reuse the EXP-057 `_rng` purpose-base scheme); emit a determinism self-check (re-run a sample,
  assert identical) and the EXP-053 reconciliation anchor.
- **Progress / memory / runtime**: `tqdm` over the 99-cell grid; per-cell bounded memory (process and
  discard each cell; persist only per-cell×variant summary rows + a bounded per-event parquet for plots).
  The per-variant × per-baseline bootstrap matrix and the longer-horizon scans are the runtime-dominant
  parts — disclose expected runtime; baselines are disclosed-only and must not gate the binding read.
- **Real-price discipline**: HA prices only in `detect_ha_harami` / `annotate_ha_impulse`; `C`, `M_sofar`,
  benchmark fav/adv, all third-barrier caps, fills, `ATR_entry`, returns, `r`, win rate, censoring **all** on
  real domain OHLC. **No HA price in any metric.**
- **New module** (the one new module): `xen/third_barrier.py` — the causal `third_event_caps` helper
  (next-`rd`-confirmed-move locator with `ConfirmTime > entry`, `bars_to_event`, the `8·bench_N` backstop,
  BENCH-warmup availability exclusion, and the event-vs-backstop bound flag) plus a thin `variant_caps`
  wrapper that returns each variant's per-event `n_event` array (BENCH/T12/T24/T48 by delegating to
  `adaptive_time_caps_by_epoch(floor=F)`; `/THIRD-EVENT` via `third_event_caps`). Everything else reuses
  `xen.expectancy` (`live_in_progress_state`, `live_strong_stat`, `adaptive_time_caps_by_epoch`,
  `benchmark_barriers`, `resolve_path_ordered`, `realised_returns`, `qualifying_mask`,
  `bootstrap_median_distribution`, `median_ci`, `contrast_ci`), `xen.favourable_targets`
  (`paired_median_contrast_ci`), `xen.zigzag`, `xen.heiken_ashi_generator`, `xen.ha_harami`,
  `xen.strong_move`, `xen.capture_barriers`, `xen.bar_aggregator`.
- **Frozen constants** (no tuning): `atr_period=14`, `atr_mult=1.0`, benchmark favourable `X=0.50`,
  benchmark adverse R:R `1:1`, time-cap `(k=1.5, window=20, median, min_moves=5)` with **`/THIRD-TIME` floors
  `{6 (BENCH), 12, 24, 48}`**, **`/THIRD-EVENT` opposing event = next confirmed move `Direction==rd` with
  `ConfirmTime>entry`**, **`/THIRD-EVENT` backstop = 8·bench_N**, STAT `(window=20, min=5, q=0.75)`, HA
  `run_len=3`, `POWER_FLOOR=30`, `N_BOOT=10_000`, `BOOT_BATCH=2_000`, `P11=(≥5 cells, ≥3 instruments)`.

---

## Complexity Check

- **Statistical methods: 4 / 4** — (1) variant median block-bootstrap CI; (2) baseline median bootstrap
  (matched-random + MA-seg, same method); (3) **paired** variant−benchmark contrast CI; (4) independent
  variant−baseline contrast CI (disclosed). The `/STRONG-HA` arm, STAT-MAD, mean, `r`, win rate, TIMECAP and
  censoring fractions reuse these methods as **disclosed secondaries** — no new method. The multiplicity
  disclosure adds **no** computed test (counts only).
- **Visualisations: 5 / 5** — forest; variant−benchmark contrast heatmap; return-distribution-by-variant;
  `r` + wins-over-benchmark composition (combined panel); censoring/TIMECAP composition + power map.
- **New modules: 1 / 1** — `xen/third_barrier.py` (`/THIRD-EVENT` cap helper + per-variant `n_event`
  wrapper; `/THIRD-TIME` via the existing `adaptive_time_caps_by_epoch`). All other machinery reused (incl.
  `xen.favourable_targets.paired_median_contrast_ci`).
