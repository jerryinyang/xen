# Analysis Plan: Experiment EXP-057 — Adverse-Target Geometry (Conditioned HA Harami; `/ADV-EXTREME`, `/ADV-NONE` vs Benchmark 1:1)

## Objective

Determine whether, on the **live `/STRONG`-conditioned HA harami** (entered at the harami
confirmation-bar close, faded against the in-progress strong move; the **identical population** to
EXP-053/056), **changing only the adverse-target geometry** raises gross per-event **median** expectancy
(P14: ATR-normalised realised return under P15 path-ordered fills, regime-clustered moving-block
bootstrap CI) above the **benchmark 1:1** adverse target. The **favourable** target is held at the
benchmark **50%-of-`M_sofar`** level for every variant, and the third barrier at the benchmark
**adaptive time cap** — pure one-at-a-time (OAT) variation of the **adverse** leg over a **predeclared
variant sweep**:

| # | Variant id | Class | Adverse target | Binding? |
|---|-----------|-------|----------------|----------|
| 1 | `BENCH` | benchmark (P3) | `adv = C − rd·0.50·M_sofar` (1:1) | binding (reference) |
| 2 | `ADV-EXTREME-raw` | `/ADV-EXTREME` | buffered faded-move running extreme; R:R free | binding |
| 3 | `ADV-EXTREME-rr1` | `/ADV-EXTREME` | extreme widened to `adv_dist = max(extreme_dist, fav_dist)` (≥1:1) | binding |
| 4 | `ADV-NONE` | `/ADV-NONE` | no adverse barrier (fav-or-timecap only) | binding |

The deliverable is a **characterization readout** (`ADVERSE_TARGET_CHARACTERISED`) feeding the single
014-B G2 — **no gate is adjudicated here, no candidate registered, 0 slots / 0 TEST reads**, TRAIN-only,
gross. Detection on HA candles; **every outcome metric on real domain-bar OHLC**, never HA prices.
Methods are non-parametric (bootstrap of a robust median); no normality/stationarity/i.i.d. assumption.

> **Scope-fidelity notes / methodological posture (resolved within scope, not broadened):**
> 1. **The variant−benchmark contrast is *paired*.** Every variant is scored on the *same* conditioned
>    harami events as the benchmark — only the adverse level (and hence the resolved class/exit) differs
>    — so the per-event returns are positively correlated. The contrast is therefore a **paired** block
>    bootstrap on the **common qualifying-event subset** (events resolved under both that variant and the
>    benchmark), using the existing `xen.favourable_targets.paired_median_contrast_ci`, not the
>    independence-assuming `xen.expectancy.contrast_ci`. This is the correct operationalization of the
>    scope's named "variant − benchmark contrast", not a new test. (Same posture as EXP-056.)
> 2. **P13 baselines (matched-random, MA-seg) are *disclosed secondaries* and do NOT enter the binding
>    verdict.** The scope's binding EVIDENCE_FOR limb (b) is the **variant−benchmark** contrast; the
>    benchmark variant already carries EXP-053's "beats matched controls" result. Baselines are computed
>    per variant for context/robustness and reported, but the EVIDENCE_* label is decided on
>    own-viability + benchmark-contrast only. (Confirmed consistent with the scope §Baselines.)
> 3. **No within-experiment family-wise correction across the 4 variants** (multiplicity posture, §Step 8
>    and §Multiplicity). EXP-057 *emits* uncorrected per-variant readouts; the binding family-wise
>    inference is deferred to the single 014-B G2 across the full surface (programme/registry pattern).
> 4. **First-hit `r` is a disclosed secondary, reported prominently but never binding.** This lever is
>    *expected* to move `r` off the EXP-049/053 ≈0.50 null (a tight extreme stop → `r` well below 0.50;
>    `/ADV-NONE` → a degenerate `r=1.0` wherever any FAV occurs, since `n_ADV=0`). The off-0.50 narrative
>    is the headline story for the desk, but the **median expectancy** endpoint (P14) is what decides
>    viability — precisely because `r` cannot see the large negative timecap tail that a removed/tightened
>    stop admits (lessons §8.6: match the metric to the mechanism).

---

## Methodology

The construction Steps 1–2 (substrate, HA, harami, live in-progress state, `/STRONG-STAT` binding +
`/STRONG-HA` disclosed conditioning) are **identical to EXP-053/056** and **reuse the same
`xen.expectancy` functions** (`live_in_progress_state`, `live_strong_stat`) so the binding conditioned
population is **byte-identical to EXP-053's** (verified in Step 9 reconciliation). They are summarised
here and not re-derived. Steps 4–9 (P15 resolution, median bootstrap, baselines, contrasts, composition,
gates) reuse the EXP-056 kernels unchanged; **only Step 3 (the adverse-target construction) is new.**

### Step 1: Per-cell construction (reused from EXP-053/056)

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
- **Why**: frozen, separately-validated D0 primitives (EXP-048 PASS); compose, do not re-derive. The
  live in-progress state anchors at the harami *before* the ZigZag confirms (the family's claimed lead),
  the gap the lessons doc identifies.
- **Simpler alternative considered**: re-deriving the conditioned population from raw detectors — rejected;
  reuse the EXP-053 functions verbatim so the population is identical by construction (Step 9 anchor).
- **Assumptions**: ZigZag pivots are future information until confirmed (only moves with
  `ConfirmTime ≤ t_i` and the known `EndPrice_k` pivot are used); `C` is the harami bar's own close;
  alignment by `CloseTime`, never bar index.
- **Expected output**: per cell, the ordered harami-event table with `entry_idx, C, rd, M_sofar,
  ATR_entry, start_epoch (EndTime_k)`, the confirmed-move arrays, and `confirm_idx`
  (`xen.capture_barriers.confirm_indices`).

### Step 2: Live conditioning — `/STRONG-STAT` (binding) and `/STRONG-HA` (disclosed) (reused from EXP-053/056)

- **Method**: `/STRONG-STAT` (binding, P7): `xen.expectancy.live_strong_stat` with window 20, min 5,
  q 0.75 → `retained_p75` (binding) and `retained_mad` (disclosed sensitivity); retained iff
  `M_sofar ≥ p75(trailing-20 confirmed-move magnitudes)`; `<5` prior moves → NO_DECISION/warmup-excluded.
  `/STRONG-HA` (disclosed, P8): `xen.strong_move.annotate_ha_impulse` (window 20, min 5) +
  `find_impulse_runs(run_len=3)`; retain iff a same-direction completed impulse run lies inside the
  in-progress span and completed at/before `t_i`. Trade direction `rd` from Step 1 for both arms; **no
  `/BARCFG` filter**.
- **Why**: P16 — `/STRONG-STAT` is the live conditioning that defines the family signal; position-in-move
  (EXP-050) is descriptive-only and never a filter.
- **Simpler alternative considered**: a single arm (binding only) — rejected; the `/STRONG-HA` disclosed
  arm is a registered robustness check, run through the identical pipeline at marginal cost.
- **Assumptions**: magnitude-percentile is computed over completed confirmed moves only (causal).
- **Expected output**: per cell, the binding `/STRONG-STAT`(p75) retention mask, the `/STRONG-HA` and
  STAT-MAD disclosed masks, retained counts, and retained fraction `f` (sanity vs EXP-051 0.20–0.27 /
  EXP-053).

### Step 3: Adverse-target construction per variant (the **new module**, `xen/adverse_targets.py`)

For each **retained** harami event, the **favourable** target and **adaptive cap** are the benchmark
objects, identical across all four variants:
- `BENCH` favourable: `xen.expectancy.benchmark_barriers(C, rd, m_sofar)` → `fav = C + rd·0.50·M_sofar`,
  `fav_dist = 0.50·M_sofar` (used by every variant for the favourable leg);
- adaptive cap: `xen.expectancy.adaptive_time_caps_by_epoch` (P4; `<5` durations → warmup, no barrier).

Variants then differ **only** in the adverse level `adv` (`adv_dist = rd·(C − adv)`, the distance from
`C` to the stop in the adverse `−rd` direction). All on **real prices**.

- **`BENCH`** (reference, P3 1:1): `adv = C − rd·0.50·M_sofar` (`adv_dist = fav_dist`). The benchmark
  barrier pair is exactly `xen.expectancy.benchmark_barriers` — reproduces EXP-053 (`r≈0.50` expected).

- **Faded-move running extreme (new module `faded_move_extreme`)** — the causal scan shared by both
  `/ADV-EXTREME` forms. For each retained event, locate the in-progress-move start bar index
  `start_idx = bar_idx(start_epoch)` (`start_epoch = EndTime_k`, mapped to the domain-bar grid by exact
  `CloseTime` match; the start pivot is the terminal pivot of a move **confirmed at or before** `t_i`, so
  all scanned bars satisfy `CloseTime ≤ t_i` ⇒ causal). Over the **inclusive span** `[start_idx+1 …
  entry_idx]` on real OHLC:
  - `rd = +1` (long fade): `faded_extreme = min(Low)` over the span;
  - `rd = −1` (short fade): `faded_extreme = max(High)` over the span.
  - **Span edge case (predeclared):** if `entry_idx == start_idx` (no intervening bar), the span is the
    entry bar alone and `faded_extreme = entry-bar Low` (`rd=+1`) / `High` (`rd=−1`) — still defined.
  - **Availability/warmup:** if `InProgressState.valid` is False (no confirmed move precedes the harami),
    or `start_idx` cannot be resolved, the event is **excluded-with-record** for both `/ADV-EXTREME`
    forms (disclosed count). `ATR_entry` non-finite or ≤0 → excluded.
  - This is an explicit **bounded sequential** running-extreme scan (causal semantics; not the EXP-050
    descriptive position metric, not an unconfirmed end pivot) — see §Implementation Safety.

- **`ADV-EXTREME-raw`** (new module `adverse_extreme_raw`): `adv = faded_extreme − rd·0.25·ATR_entry`
  (the `0.25·ATR_entry` buffer extends the stop **further in the adverse `−rd` direction**:
  `rd=+1` → below the swing low; `rd=−1` → above the swing high). Then
  `adv_dist = rd·(C − adv) = rd·(C − faded_extreme) + 0.25·ATR_entry`. Because `faded_extreme` is the
  extreme on the adverse side, `rd·(C − faded_extreme) ≥ 0`, so `adv_dist ≥ 0.25·ATR_entry > 0`.
  - **Degeneracy floor (predeclared, raw only):** event excluded-with-record if
    `adv_dist < ADV_FLOOR = 0.10·ATR_entry`. By construction `adv_dist ≥ 0.25·ATR_entry`, so this floor
    is essentially never binding for raw; it is retained as a defensive invariant and disclosed (expected
    count ≈ 0). Never silently clamped.
  - Typically a **tight** stop (`adv_dist ≪ fav_dist`) → R:R < 1:1, `r` expected **well below 0.50**.

- **`ADV-EXTREME-rr1`** (new module `adverse_extreme_rr1`): identical `faded_extreme`/buffer, then widen
  to at least the benchmark 1:1 distance: `adv_dist = max(adv_dist_raw, fav_dist)`; `adv = C − rd·adv_dist`.
  Keeps R:R ≥ 1:1 like the benchmark, so any expectancy difference vs `BENCH` is attributable to the
  **extreme-anchoring** of the stop, not to a tighter stop. No degeneracy exclusion can fire
  (`adv_dist ≥ fav_dist > 0`).

- **`ADV-NONE`** (new module `adverse_none_sentinel`): no adverse barrier. Implemented by passing an
  **unreachable** adverse level to the shared P15 resolver: `adv = −∞` for `rd=+1`, `adv = +∞` for
  `rd=−1`. In `xen.expectancy._scan_path`, `adv_hit` is `low[i] ≤ −∞` (`rd=+1`) or `high[i] ≥ +∞`
  (`rd=−1`) — never True — so the resolver returns **only** `FAV` or `TIMECAP` (or `DATA_CENSORED` at the
  data edge). No validity/degeneracy exclusion applies (there is no stop); only warmup/`ATR_entry`/
  censoring exclusions apply. This variant deliberately admits large negative timecap returns — that
  asymmetry is the object of measurement, and is exactly what the median endpoint (not `r`) captures.

- **Generalized adverse barrier helper** (new module) `barriers_with_adverse(C, rd, fav_dist, adv) →
  (fav, adv, fav_dist, adv_dist, valid)` where `fav = C + rd·fav_dist` (benchmark favourable) and
  `valid = (fav_dist > 0) AND (adv_dist ≥ ADV_FLOOR)` for stopped variants; `valid = (fav_dist > 0)` for
  `/ADV-NONE` (the `−∞/+∞` sentinel is always "valid" as a built window). `fav_dist > 0` always holds for
  the conditioned population (`M_sofar > 0`).

- **Why**: the registered `/ADV-EXTREME` (operator-chosen faded-move-extreme reference, raw and ≥1:1
  forms) and `/ADV-NONE` adverse models, varied OAT against the frozen benchmark 1:1, with the favourable
  leg and cap held fixed so the read isolates the adverse leg. The faded-move running extreme is the only
  *causal* reading of "previous-move-extreme" for a reversal fade (the start pivot itself sits on the
  favourable side of `C`, so it cannot be an adverse stop — the relevant adverse reference is how far the
  faded move actually ran against the eventual reversal).
- **Simpler alternative considered**: a single `/ADV-EXTREME` form — rejected; the raw/rr1 pair is the
  operator's predeclared decomposition (where-the-stop-sits vs how-wide-it-is), and both are registered.
- **Assumptions**: the faded-move extreme scan is causal (`start_epoch = EndTime_k` of a move confirmed
  `≤ t_i`; all span bars `≤ t_i`); the buffer/ floor are fixed fractions of the known `ATR_entry`.
- **Expected output**: per retained event, for each variant `(fav, adv, fav_dist, adv_dist, valid_flag,
  exclusion_reason)`, plus `faded_extreme`, the shared adaptive cap `N`, and the warmup flag.

### Step 4: P15 path-ordered fill resolution + realised gross return per variant (reused kernels)

- **Method**: for each variant's valid, non-warmup event, resolve first-touch via
  `xen.expectancy.resolve_path_ordered` (explicit bounded sequential scan over
  `[entry_idx+1, min(entry_idx+N, last_idx)]` on real OHLC; same-bar double-touch resolved by the P15
  intrabar path — bullish `O→L→H→C`, bearish `O→H→L→C`) → classes `{FAV, ADV, TIMECAP, DATA_CENSORED}`
  and exit price (target level for FAV/ADV; cap-bar real **close** for TIMECAP). For `/ADV-NONE` the
  `±∞` adverse sentinel guarantees `adv_hit` never fires → classes are `{FAV, TIMECAP, DATA_CENSORED}`
  only (an asserted invariant, Step 9). Realised gross return `xen.expectancy.realised_returns` →
  `r_e = rd·(exit − C)/ATR_entry`. Qualifying population `xen.expectancy.qualifying_mask` = built-barrier
  `{FAV,ADV,TIMECAP}` with finite exit and `ATR_entry>0`.
- **Why**: first-hit `r` is blind to the family's position-management value (P14/lessons §8.6); the
  realised-return endpoint is what the mechanism can express, and P15 removes the worst-case-tie-break
  bias on a near-0.50 substrate. The resolver loop's causal/streaming semantics are the object under
  test — **not vectorized**.
- **Simpler alternative considered**: the EXP-049 worst-case tie-break — rejected; EXP-054 adopted P15 as
  the 014-B fill standard.
- **Assumptions**: the intrabar path is a documented approximation (1-minute base bars not replayed);
  disclosed; EXP-054 bounded its effect as immaterial (median Δr 0.010). The `±∞` sentinel is finite-safe
  inside the comparison logic (`low ≤ −∞`/`high ≥ +∞` evaluate False; no NaN produced).
- **Expected output**: per variant per cell, the entry-time-ordered `r_e` series and the
  `(FAV,ADV,TIMECAP,DATA_CENSORED, warmup, validity-excluded)` counts.

### Step 5: Per-cell median expectancy + regime-clustered moving-block bootstrap *(stat methods 1–2)*

- **Method**: per cell × variant × arm (`/STRONG-STAT` binding; `/STRONG-HA` disclosed),
  `E_cell = median(r_e over qualifying events)`. CI via `xen.expectancy.bootstrap_median_distribution`
  (events in entry-time order; block `b = max(1, round(m^(1/3)))`; `ceil(m/b)` contiguous blocks per
  resample truncated to `m`; `N_BOOT=10_000`; batched; **fixed seed = master + stable per-(cell,variant)
  offset**) → `median_ci` one-sided `CI_low` (5th pct) + two-sided (2.5/97.5). **Method 1** = each
  variant's signal median CI; **method 2** = each P13 baseline median CI (Step 6). The mean is a
  disclosed secondary.
- **Why**: the per-event ATR-normalised return distribution is fat-tailed (FAV/ADV cluster near
  `±dist/ATR`, TIMECAP spreads, and `/ADV-NONE` adds a heavy negative tail) → the **median** is the
  robust location estimator (P14); the moving-block bootstrap is non-parametric and preserves local
  serial/regime dependence.
- **Simpler alternative considered**: sign / Wilcoxon test on `r_e>0` — rejected as binding (assumes
  exchangeable events, tests a different null); normal-theory t-CI rejected (fat tails, especially
  `/ADV-NONE`). Reported informally at most.
- **Expected output**: per cell × variant × arm `(m, E_cell, CI_low_1s, CI_lo_2s, CI_hi_2s, block_len,
  mean, r, win_rate, timecap_frac)` and `viable_status` (`VIABLE` iff `CI_low_1s>0` AND `m≥30`; else
  `CI_SPANS_0` / `NOT_VIABLE_BY_POWER`).

### Step 6: P13 baselines through the identical per-variant pipeline (disclosed) *(method 2 reused)*

- **Method**: both baselines are scored through the **identical** Step 3–5 pipeline **for every binding
  variant** (same benchmark favourable target, the variant's adverse model, adaptive cap, P15 fills,
  median + same bootstrap), marked **disclosed-only**:
  1. **Matched-count random in-regime timestamps**: draw the same count as the variant's qualifying
     events, without replacement, from the cell's eligible-bar pool (TRAIN bars with a defined
     in-progress move, defined `ATR_entry`, defined cap, and not a retained-signal bar); each drawn bar
     takes the **in-progress `rd`** at that bar (direction is NOT randomised), computes its own
     `M_sofar`/`faded_extreme` from its in-progress move, and builds that variant's adverse geometry
     identically. Fixed per-(cell,variant) seed, distinct RNG stream from the bootstrap.
  2. **MA(20,50) segmentation**: replace the ATR-ZigZag substrate with MA(20,50)-crossover segments on
     domain `Close` (EXP-050/053 arm); re-run the full conditioned-signal pipeline (harami +
     current-price magnitude-percentile + harami anchor + benchmark favourable + the variant's adverse
     geometry + cap + P15) on MA segments. The faded-move extreme is taken over the MA-segment
     in-progress span.
- **Why**: P13/P20. Disclosed robustness — does a given adverse geometry beat random entries (matched
  count, same geometry, same regime pool, same direction rule) and is any effect ZigZag-specific?
- **Simpler alternative considered**: omit baselines — rejected; P13/P20 require both as disclosed
  secondaries (the registry's matched-control discipline).
- **Note (runtime)**: this is the compute-dominant part (≈ 4 variants × 2 baselines × 99 cells × 10k
  bootstrap). It is **disclosed-only** and must not block the binding read; `tqdm`, bounded per-cell
  memory, fixed seeds. A baseline cell with `< 30` matched events is `NOT_VIABLE_BY_POWER` (disclosed),
  never an undefined ratio.
- **Expected output**: per cell × variant, baseline `(m, E_cell, CI_low_1s, …)` for matched-random and
  MA-seg, same schema as Step 5.

### Step 7: Contrasts — variant−benchmark (paired, binding) and variant−baseline (independent, disclosed) *(stat methods 3–4)*

- **Method 3 — variant − benchmark (PAIRED; binding):** the variant and the benchmark are evaluated on
  the **same conditioned events** (same favourable target/cap; only the adverse model differs), so the
  contrast is paired on the **common qualifying-event subset** `S = {events qualifying under BOTH this
  variant and BENCH}` (entry-time ordered). Use `xen.favourable_targets.paired_median_contrast_ci`
  (a paired moving-block bootstrap: one set of block indices applied to **both** the variant `r_e` and
  the benchmark `r_e` restricted to `S`; statistic `Δ* = median(variant_S*) − median(BENCH_S*)`),
  one-sided `CI_low(Δ)` (5th pct) + two-sided. **Variant beats benchmark in a cell iff `CI_low(Δ) > 0`
  AND `|S| ≥ 30`.** Pairing on the same resample indices cancels the shared event/regime noise → the
  correct (tighter) difference CI; `xen.expectancy.contrast_ci` is **not** used here (it would over-state
  variance).
- **Method 4 — variant − baseline (INDEPENDENT; disclosed):** variant signal vs each P13 baseline are
  **independent** event sets (different timestamps) → use `xen.expectancy.contrast_ci` (independent block
  bootstraps, resample-index pairing as Monte-Carlo convenience). Disclosed-only.
- **Matched cells in the quorum**: the benchmark-beat composition counts only cells where **both** the
  variant and BENCH are reportable (`m_variant ≥ 30` AND `m_BENCH ≥ 30` AND `|S| ≥ 30`); a cell where
  BENCH is itself non-viable is **not** counted as a "beat" — recorded separately as
  `variant_viable_where_bench_not` for disclosure.
- **`/ADV-NONE` pairing note**: `S` for `/ADV-NONE` vs `BENCH` is the subset where both resolve. Because
  `/ADV-NONE` removes the stop, an event that hits the benchmark `ADV` early may run on to FAV/TIMECAP
  under `/ADV-NONE` — both still qualify (built barrier, resolved), so they enter `S` with **different
  exit prices**; this is the intended paired comparison of the same entries under two adverse rules.
- **Expected output**: per cell × variant, `CI_low(Δ_bench)` (paired) + the `beats_bench` boolean;
  `CI_low(Δ_random)`, `CI_low(Δ_MA)` (independent, disclosed).

### Step 8: P11 composition + mechanical EVIDENCE_* classification (binding)

- **Method** (binding arm `/STRONG-STAT`, all gross, TRAIN-only, **per variant**):
  - `viable[variant,cell] = (CI_low_1s(variant) > 0) AND (m ≥ 30)`.
  - `beats_bench[variant,cell] = (CI_low(Δ_bench) > 0) AND (m_variant≥30 AND m_BENCH≥30 AND |S|≥30)`.
  - `win[variant,cell] = viable AND beats_bench`.
  - Per variant: `V = #viable cells`, `I_V = #instruments among them`; `W = #win cells`,
    `I_W = #instruments among them`; `P_powered = #cells with m≥30`, `I_powered`.
  - **P11**: a composition holds iff **≥5 cells over ≥3 instruments**.
  - **Variant passes** iff its `win` composition clears P11 (`W≥5 AND I_W≥3`) — i.e. it is viable AND
    beats benchmark on ≥5 cells over ≥3 instruments.
- **No within-experiment family-wise correction** (see §Multiplicity). All 3 binding alternatives (plus
  the benchmark reference) are reported; the verdict is descriptive and feeds G2.
- **Expected output**: per-variant composition tallies, the variant-pass booleans, the EVIDENCE_* label,
  and the multiplicity disclosure block → `composition_readout.json` + `adverse_target_map.csv`.

### Step 9: Determinism, causality, reconciliation, invariant gates (binding correctness)

- **Determinism**: re-run one cell (and the full grid in a second pass over a fixed sample) end-to-end;
  assert byte-identical per-cell per-variant outputs. Any mismatch → SUBSTRATE/METHOD_DEFECT.
- **Causality / invariants (assert in code)**: every quantity at `t_i` uses only bars `≤ t_i` and moves
  with `ConfirmTime ≤ t_i`; the faded-move-extreme span is `[start_idx+1 … entry_idx]` with all
  `CloseTime ≤ t_i` (`start_epoch = EndTime_k`, the terminal pivot of a move confirmed `≤ t_i`);
  barriers/cap use only moves confirmed strictly before `t_i`; first-touch scan starts at `entry_idx+1`
  and reads no bar with `CloseTime > train_end_ts` (else DATA_CENSORED); `fav_dist > 0` for every
  resolved event. Violation on ≥3 instruments → SUBSTRATE/METHOD_DEFECT.
- **Predeclared invariant checks (named in the scope; assert + report):**
  1. **Benchmark reproduces EXP-053**: the `BENCH` variant's per-cell median expectancy **and** first-hit
     `r` (≈0.50) match EXP-053's benchmark `E_cell`/`r` on the same grid to numerical tolerance
     (`|Δ| ≤ 1e-9` on the shared events; same detector/filter/fence/geometry, same functions). The
     conditioned `/STRONG-STAT` population (count + `trigger_idx/time/rd` digest per cell) matches
     EXP-053 exactly.
  2. **Raw ≤ rr1 adverse distance, event-wise**: for every retained event, `adv_dist(ADV-EXTREME-raw) ≤
     adv_dist(ADV-EXTREME-rr1)` (the `max(·, fav_dist)` widen can only increase distance). Assert
     elementwise; any violation → SUBSTRATE/METHOD_DEFECT.
  3. **`/ADV-NONE` yields 0 ADV outcomes**: across all cells, `n_ADV(ADV-NONE) == 0` (the `±∞` sentinel
     is never touched). Assert; any nonzero → SUBSTRATE/METHOD_DEFECT.
  4. **Adverse-side ordering**: for `ADV-EXTREME-raw`, `rd·(C − adv) > 0` (stop on the adverse side) and
     `adv` lies at/beyond `faded_extreme` in the `−rd` direction (buffer applied correctly).
- **Population reconciliation (vs EXP-053)**: emitted as `population_reconciliation.csv` — the binding
  conditioned-event set and the `BENCH` per-cell median/`r` vs EXP-053. Exact match expected; any
  mismatch is a defect investigated before the readout is trusted.
- **Expected output**: `determinism_ok`, `causality_ok`, `reconciliation_ok`, `invariants_ok` flags + the
  per-cell BENCH-vs-EXP-053 diff table.

---

## Multiplicity posture (predeclared)

EXP-057 is **gross, 0-slot, 0-TEST characterization** feeding the **single 014-B G2** (the design forbids
intermediate gates and early closure). The cross-variant multiplicity is controlled by, in order:

1. **Full predeclaration + report-all (file-drawer/registry control).** All 4 binding variants are
   predeclared in the scope and **every** one is reported with its full per-cell readout — none is
   drawered or selected post-result. Primary multiplicity control (registry pattern).
2. **P11 breadth as the robustness filter.** A "variant passes" requires viability **and**
   benchmark-beat on **≥5 cells over ≥3 instruments** — far stronger against per-cell noise than any
   single uncorrected CI; a variant winning on scattered singletons cannot pass.
3. **Deferral of binding family-wise inference to G2.** EXP-057 applies **no** Holm/Bonferroni across the
   variants; its per-variant `CI_low` thresholds are **uncorrected one-sided 95%**. The binding
   family-wise correction across the full 014-B surface (favourable/adverse/third/exit geometries) is the
   **single G2 desk adjudication**'s responsibility, on the complete slate — not this experiment's.
4. **Multiplicity disclosure (no new statistical method).** The readout reports, for the desk: the number
   of binding variants that pass (`n_pass`), the per-variant `(W, I_W)` margins above the P11 quorum, and
   a **fragility flag** for any pass resting on a bare quorum (exactly 5 cells or exactly 3 instruments).
   No computed permutation null is added (stays within the 4-method budget).

This posture is fixed before results exist and is not revisited after seeing them.

---

## Visualisations (5 / 5)

1. **Per-variant median-expectancy forest plot** (binding `/STRONG-STAT` arm): for each binding variant,
   member cells' `E_cell` with one-sided `CI_low` whiskers, faceted or colour-grouped by variant, with
   the `BENCH` per-cell median overlaid as a reference marker. *Answers: is each variant's conditioned
   expectancy > 0 per cell, and how does it sit vs benchmark?*
2. **Variant − benchmark contrast heatmap**: variants (rows) × cells (cols), cell colour = paired
   `CI_low(Δ_bench)` sign/magnitude (with `beats_bench` hatching). *Answers: which adverse variant beats
   benchmark, where, and is it coherent across cells/instruments or scattered?*
3. **Pooled per-event return distribution by variant** (violin/box of ATR-normalised `r_e` across viable
   cells, per-variant medians + the BENCH median line overlaid). *Answers: distribution shape (justifies
   the median), where mass sits vs 0, and the FAV/ADV/TIMECAP structure per adverse model — in particular
   the `/ADV-NONE` negative timecap tail and the `ADV-EXTREME-raw` tight-stop ADV cluster.*
4. **First-hit `r` vs benchmark, per variant + P11 "wins-over-benchmark" composition map** (combined
   panel): (a) per-variant `r` distribution across cells with the 0.50 reference line (the off-0.50
   narrative — disclosed); (b) instrument × domain `win / viable-only / CI_SPANS_0 / NOT_VIABLE_BY_POWER
   / COVERAGE_EXCLUDED` status grid per variant. *Answers: did the lever move `r` off 0.50, and does any
   variant clear ≥5 cells / ≥3 instruments on the binding endpoint?*
5. **Per-cell qualifying-event / exclusion-fraction map**: per variant, qualifying-event count and the
   exclusion breakdown (degeneracy `adv_dist<ADV_FLOOR`, warmup, DATA_CENSORED) as a stacked fraction,
   with the 30-event power floor marked. *Answers: how much each adverse geometry costs in power and how
   many cells survive to be reportable — central to an INCONCLUSIVE read.*

Secondary tables (`/STRONG-HA` arm, STAT-MAD arm, both P13 baselines and their contrasts, `r`/win-rate/
TIMECAP fractions, per-variant exclusion counts) go to CSV, not plots.

---

## Interpretation Guide (predefined, mechanical)

Binding arm `/STRONG-STAT`; per variant; all gross; TRAIN-only. Let a variant **pass** iff its `win`
composition clears P11 (`W ≥ 5` over `≥3` instruments), where `win = viable AND beats_bench` (Step 8).

- **EVIDENCE_FOR** (an adverse-target lever helps) iff **≥1 binding alternative variant passes** — it is
  viable on its own median expectancy **and** beats the benchmark on the paired contrast, on ≥5 cells over
  ≥3 instruments. → At least one alternative adverse geometry improves conditioned capture over the 1:1
  benchmark on this surface leg. Report **all** passing variants and their margins; **no candidate
  registration / no selection of a single winner** (G2 only). *(Reason: the family's defining conditioned
  signal captures more under a different, predeclared adverse target than under the 1:1 benchmark,
  robustly across the grid.)*
- **EVIDENCE_AGAINST** (adverse geometry is not a lever) iff there are **enough powered cells to
  adjudicate** — for the benchmark and ≥1 alternative, `P_powered ≥ 5` over `≥3` instruments — **and no**
  binding alternative variant passes. → Recorded as a measured-negative characterization; routing
  deferred to the single 014-B G2. *(Reason: with adequate power, no alternative adverse target reliably
  beats the 1:1 benchmark; the adverse leg is not where conditioned capture is gained.)*
- **INCONCLUSIVE (power-limited)** iff a P11 quorum of powered cells **cannot be formed** for the
  benchmark and the alternatives (`P_powered < 5` or `I_powered < 3` on the variants of interest), with no
  correctness failure. → Degeneracy/warmup/censoring exclusions depleted counts below the adjudication
  floor; disclosed, never defaulted to a ratio. *(Reason: insufficient coverage, not absence of effect.)*
- **SUBSTRATE/METHOD_DEFECT** iff any determinism, causality, invariant, or reconciliation gate fails
  (Step 9 — including the four predeclared invariant checks) → fix before reporting; no efficacy claim.

Disclosed-only (never change the verdict): the `/STRONG-HA` arm, mean expectancy, **first-hit `r`** (the
off-0.50 narrative — `ADV-EXTREME-raw` expected `r ≪ 0.50`, `/ADV-NONE` degenerate `r→1.0`), win rate,
TIMECAP/censoring fractions, the STAT-MAD sensitivity, and both P13 baselines and their (independent)
contrasts. Their agreement/divergence is reported for context — in particular, the **`r`-vs-expectancy
divergence** is the headline lesson: a lever that moves `r` favourably (tight extreme stop) can still fail
the median-expectancy endpoint if it converts would-be winners into stop-outs, and a lever that destroys
`r` (`/ADV-NONE`) can still win on expectancy if the favourable runs dominate the negative timecap tail.

---

## Implementation Safety / Constraints for `experiment-developer`

- **Holdout / TEST**: slice the **1-minute base** to the first `int(int(total_rows·0.7)·0.7)` file-order
  rows before any aggregation; never materialize TEST or the final-30% holdout. No new-universe
  holdout/TEST row is read (the conditioned event definition already had its first TRAIN contact in
  EXP-053).
- **Temporal order & alignment**: sort/assert domain bars by `CloseTime`; align HA↔real and
  harami/move-times↔bar grid by **exact `CloseTime` match** (searchsorted + equality assert), never by
  bar index. The faded-move-extreme `start_idx` is located from `start_epoch` by the same exact match.
- **Causality (assert)**: every quantity at `t_i` uses only bars `≤ t_i` and moves `ConfirmTime ≤ t_i`;
  the faded-move-extreme span `[start_idx+1 … entry_idx]` is all `≤ t_i`; the time cap uses only moves
  confirmed strictly before `t_i`; first-touch scan starts at `entry_idx+1`; `M_sofar` uses only `C` and
  the known `StartPrice_inprogress`.
- **Sequential vs vectorized**: keep the **P15 first-touch resolver** (`resolve_path_ordered`), the
  **live in-progress-state walk**, and the **faded-move running-extreme scan** explicit/bounded (causal
  semantics under test — do not vectorize). The faded-extreme scan is a single bounded pass over the
  in-progress span per event; an `np.minimum.reduceat`/slice-min over the contiguous span is acceptable
  **only** if it is provably equivalent to the bounded scan and reads no bar `> entry_idx` (prefer the
  explicit bounded slice-min `Low[start_idx+1:entry_idx+1].min()`). Bootstrap **index construction** and
  MA segmentation may be vectorized in bounded batches (reuse `bootstrap_median_distribution` batching).
- **`/ADV-NONE` sentinel**: pass `adv = −np.inf` for `rd=+1` events and `adv = +np.inf` for `rd=−1`
  events into `resolve_path_ordered`; assert no NaN is produced and `n_ADV == 0` across the variant
  (Step 9 invariant). Do **not** special-case the resolver — the existing comparison logic handles `±∞`.
- **Denominators / zero-baseline**: qualifying population per variant = FAV/ADV/TIMECAP (built barrier);
  `< 30` → `NOT_VIABLE_BY_POWER` (no ratio); degeneracy (`adv_dist < ADV_FLOOR`, raw only), warmup
  (`<5` cap durations; NO_DECISION `/STRONG-STAT`; in-progress span unavailable for `/ADV-EXTREME`), and
  DATA_CENSORED events are excluded with **disclosed per-variant counts**. First-hit `r` uses
  `n_FAV/(n_FAV+n_ADV)` (TIMECAP excluded from the `r` denominator, EXP-049 convention); for `/ADV-NONE`,
  `n_ADV=0` ⇒ `r=1.0` where any FAV occurs (disclosed degenerate). The paired benchmark contrast uses the
  **common** qualifying subset `S` with `|S| ≥ 30`.
- **Determinism / seeds**: single master seed in constants; per-(cell,variant,purpose) RNG via
  `default_rng(master + stable_offset)` (distinct streams for bootstrap vs matched-random draws); emit a
  determinism self-check (re-run a sample, assert identical) and the EXP-053 reconciliation anchor.
- **Progress / memory / runtime**: `tqdm` over the 99-cell grid; per-cell bounded memory (process and
  discard each cell; persist only per-cell×variant summary rows + a bounded per-event parquet for plots).
  The per-variant × per-baseline bootstrap matrix is the runtime-dominant part — disclose expected
  runtime; baselines are disclosed-only and must not gate the binding read.
- **Real-price discipline**: HA prices only in `detect_ha_harami` / `annotate_ha_impulse`; `C`, `M_sofar`,
  `faded_extreme` (real `Low/High`), barriers, fills, `ATR_entry`, returns, `r`, win rate **all** on real
  domain OHLC. **No HA price in any metric.**
- **New module** (the one new module): `xen/adverse_targets.py` — the causal `faded_move_extreme`
  running-extreme scan, the `adverse_extreme_raw` / `adverse_extreme_rr1` adverse-level builders (buffer,
  ADV_FLOOR degeneracy, ≥1:1 widen), the `adverse_none_sentinel` (`±∞` by direction), and the generalized
  `barriers_with_adverse`. Everything else reuses `xen.expectancy` (`live_in_progress_state`,
  `live_strong_stat`, `adaptive_time_caps_by_epoch`, `benchmark_barriers`, `resolve_path_ordered`,
  `realised_returns`, `qualifying_mask`, `bootstrap_median_distribution`, `median_ci`, `contrast_ci`),
  `xen.favourable_targets` (`paired_median_contrast_ci`), `xen.zigzag`, `xen.heiken_ashi_generator`,
  `xen.ha_harami`, `xen.strong_move`, `xen.capture_barriers`, `xen.bar_aggregator`.
- **Frozen constants** (no tuning): `atr_period=14`, `atr_mult=1.0`, benchmark favourable `X=0.50`,
  benchmark adverse R:R `1:1`, time-cap `(k=1.5, window=20, floor=6, median)`, STAT `(window=20, min=5,
  q=0.75)`, HA `run_len=3`, **`/ADV-EXTREME` buffer = 0.25·ATR_entry**, **`ADV_FLOOR = 0.10·ATR_entry`**,
  **`/ADV-NONE` sentinel = ∓∞ by direction**, `POWER_FLOOR=30`, `N_BOOT=10_000`, `BOOT_BATCH=2_000`,
  `P11=(≥5 cells, ≥3 instruments)`.

---

## Complexity Check

- **Statistical methods: 4 / 4** — (1) variant median block-bootstrap CI; (2) baseline median bootstrap
  (matched-random + MA-seg, same method); (3) **paired** variant−benchmark contrast CI; (4) independent
  variant−baseline contrast CI (disclosed). The `/STRONG-HA` arm, STAT-MAD, mean, `r`, win rate, TIMECAP
  fraction reuse these methods as **disclosed secondaries** — no new method. The multiplicity disclosure
  adds **no** computed test (counts only).
- **Visualisations: 5 / 5** — forest; variant−benchmark contrast heatmap; return-distribution-by-variant;
  `r`-vs-benchmark + wins-over-benchmark composition (combined panel); qualifying/exclusion-fraction map.
- **New modules: 1 / 1** — `xen/adverse_targets.py` (faded-move-extreme scan + raw/rr1 adverse builders +
  `/ADV-NONE` sentinel + `barriers_with_adverse`). All other machinery reused (incl.
  `xen.favourable_targets.paired_median_contrast_ci`).
