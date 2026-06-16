# Analysis Plan: Experiment EXP-056 — Favourable-Target Geometry (Conditioned HA Harami; `/VPTARGET`, `/MAGTARGET` vs Benchmark 50%)

## Objective

Determine whether, on the **live `/STRONG`-conditioned HA harami** (entered at the harami
confirmation-bar close, faded against the in-progress strong move; the **identical population** to
EXP-053), **changing only the favourable-target geometry** raises gross per-event **median** expectancy
(P14: ATR-normalised realised return under P15 path-ordered fills, regime-clustered moving-block
bootstrap CI) above the **benchmark 50%-of-`M_sofar`** target. The adverse target is held at the
benchmark **1:1** model (so adverse distance tracks each variant's favourable distance) and the third
barrier at the benchmark **adaptive time cap** — pure one-at-a-time (OAT) variation of the favourable
leg over a **predeclared variant sweep**:

| # | Variant id | Class | Favourable target | Binding? |
|---|-----------|-------|-------------------|----------|
| 1 | `BENCH` | benchmark (P2) | `fav = C + rd·0.50·M_sofar` | binding (reference) |
| 2 | `VP-POC` | `/VPTARGET` prior-move | POC of prior completed move `M_k` | binding (VP baseline) |
| 3 | `VP-NEAR` | `/VPTARGET` prior-move | nearer 70%-value-area edge of `M_k` | binding |
| 4 | `VP-FAR` | `/VPTARGET` prior-move | farther 70%-value-area edge of `M_k` | binding |
| 5 | `MAG-0.5x5` | `/MAGTARGET` | `0.5·median(|mag| trailing 5 moves)` | binding |
| 6 | `MAG-1.0x5` | `/MAGTARGET` | `1.0·median(|mag| trailing 5 moves)` | binding |
| 7 | `MAG-0.5x20` | `/MAGTARGET` | `0.5·median(|mag| trailing 20 moves)` | binding |
| 8 | `MAG-1.0x20` | `/MAGTARGET` | `1.0·median(|mag| trailing 20 moves)` | binding |
| 9 | `VP-POC-INPROG` | `/VPTARGET` in-progress | POC of the in-progress move's bars | **disclosed-only** |

The deliverable is a **characterization readout** (`FAVOURABLE_TARGET_CHARACTERISED`) feeding the single
014-B G2 — **no gate is adjudicated here, no candidate registered, 0 slots / 0 TEST reads**, TRAIN-only,
gross. Detection on HA candles; **every outcome metric on real domain-bar OHLC**, never HA prices.
Methods are non-parametric (bootstrap of a robust median); no normality/stationarity/i.i.d. assumption.

> **Scope-fidelity notes / ambiguities surfaced to the operator (resolved within scope, not broadened):**
> 1. **The variant−benchmark contrast is *paired*.** Every variant is scored on the *same* conditioned
>    harami events as the benchmark — only the target levels differ — so the per-event returns are
>    positively correlated. The contrast is therefore a **paired** block bootstrap on the **common
>    qualifying-event subset** (events resolved under both that variant and the benchmark), not the
>    independence-assuming `xen.expectancy.contrast_ci`. This is the correct operationalization of the
>    scope's named "variant − benchmark contrast", not a new test.
> 2. **P13 baselines (matched-random, MA-seg) are *disclosed secondaries* and do NOT enter the binding
>    verdict.** The scope's binding EVIDENCE_FOR limb (b) is the **variant−benchmark** contrast; the
>    benchmark variant already carries EXP-053's "beats matched controls" result. Baselines are computed
>    per variant for context/robustness and reported, but the EVIDENCE_* label is decided on
>    own-viability + benchmark-contrast only. (Confirmed consistent with the scope §Baselines, which
>    lists them under "disclosed secondaries".)
> 3. **No within-experiment family-wise correction across the 8 variants** (multiplicity posture, §Step 8
>    and §Multiplicity). EXP-056 *emits* uncorrected per-variant readouts; the binding family-wise
>    inference is deferred to the single 014-B G2 across the full surface (programme/registry pattern).

---

## Methodology

The construction Steps 1–2 (substrate, HA, harami, live in-progress state, `/STRONG-STAT` binding +
`/STRONG-HA` disclosed conditioning) are **identical to EXP-053** and **reuse the same
`xen.expectancy` functions** (`live_in_progress_state`, `live_strong_stat`) so the binding conditioned
population is **byte-identical to EXP-053's** (verified in Step 9 reconciliation). They are summarised
here and not re-derived.

### Step 1: Per-cell construction (reused from EXP-053)

- **Method**: per cell (instrument × domain), TRAIN slice only. Holdout/TEST-safe load: lazy
  `pl.scan_parquet`; `total_rows`; `train_rows = int(int(total_rows·0.7)·0.7)`; collect only the first
  `train_rows` file-order 1-minute rows (F01 prefix; never sort/collect the full file, never read TEST or
  holdout); assert chronological; `train_end_ts = max(CloseTime)`. Aggregate the domain via
  `xen.bar_aggregator.aggregate_ohlc` (5m strict; others `min_coverage=0.90`), **carrying `TickVolume`**
  (summed over constituents); fence to `CloseTime ≤ train_end_ts`. ZigZag substrate
  `xen.zigzag.generate_zigzag(bars, atr_period=14, atr_mult=1.0)` → confirmed moves; real-bar
  `ATR_entry` from `xen.zigzag.wilder_atr(High,Low,Close,14)`; HA candles
  (`xen.heiken_ashi_generator`); haramis `xen.ha_harami.detect_ha_harami` mapped to domain-bar indices
  by **exact `CloseTime` match** (searchsorted + equality assert); live in-progress state
  `xen.expectancy.live_in_progress_state` → `(valid, k, rd, start_price, start_epoch, m_sofar)`.
- **Why**: frozen, separately-validated D0 primitives (EXP-048 PASS); compose, do not re-derive. The
  live in-progress state anchors at the harami *before* the ZigZag confirms (the family's claimed lead),
  the gap the lessons doc identifies.
- **Assumptions**: ZigZag pivots are future information until confirmed (only moves with
  `ConfirmTime ≤ t_i` and the known `EndPrice_k` pivot are used); `C` is the harami bar's own close;
  alignment by `CloseTime`, never bar index.
- **Expected output**: per cell, the ordered harami-event table with `entry_idx, C, rd, M_sofar,
  ATR_entry`, the confirmed-move arrays, and `confirm_idx` (`xen.capture_barriers.confirm_indices`).

### Step 2: Live conditioning — `/STRONG-STAT` (binding) and `/STRONG-HA` (disclosed) (reused from EXP-053)

- **Method**: `/STRONG-STAT` (binding, P7): `xen.expectancy.live_strong_stat` with window 20, min 5,
  q 0.75 → `retained_p75` (binding) and `retained_mad` (disclosed sensitivity); retained iff
  `M_sofar ≥ p75(trailing-20 confirmed-move magnitudes)`; `<5` prior moves → NO_DECISION/warmup-excluded.
  `/STRONG-HA` (disclosed, P8): `xen.strong_move.annotate_ha_impulse` (window 20, min 5) +
  `find_impulse_runs(run_len=3)`; retain iff a same-direction completed impulse run lies inside the
  in-progress span and completed at/before `t_i`. Trade direction `rd` from Step 1 for both arms; **no
  `/BARCFG` filter**.
- **Why**: P16 — `/STRONG-STAT` is the live conditioning that defines the family signal; position-in-move
  (EXP-050) is descriptive-only and never a filter.
- **Expected output**: per cell, the binding `/STRONG-STAT`(p75) retention mask, the `/STRONG-HA` and
  STAT-MAD disclosed masks, retained counts, and retained fraction `f` (sanity vs EXP-051 0.20–0.27 /
  EXP-053).

### Step 3: Favourable-target construction per variant (the new module)

For each **retained** harami event, build the favourable price level `fav` for **every** variant. The
**adverse** target is the benchmark 1:1 model `adv = C − rd·fav_dist` where `fav_dist = rd·(fav − C)`;
the **third barrier** is the benchmark adaptive time cap `xen.expectancy.adaptive_time_caps_by_epoch`
(unchanged across variants). All on **real prices**.

- **`BENCH`** (reference): `xen.expectancy.benchmark_barriers(C, rd, m_sofar)` →
  `fav = C + rd·0.50·M_sofar`, `adv = C − rd·0.50·M_sofar`. (Reproduces EXP-053 exactly.)

- **`/VPTARGET` (new module) — volume profile of the prior completed move `M_k`** (LOOKBACK=1, binding
  reference; `M_k` = the last confirmed move, `xen.expectancy.live_in_progress_state.k`):
  - **Reference bars**: domain bars `[bar_idx(StartTime_k) … bar_idx(EndTime_k)]` inclusive (pivot →
    pivot of `M_k`; all `CloseTime ≤ EndTime_k < ConfirmTime_k ≤ t_i` ⇒ causal). Map `StartTime_k`,
    `EndTime_k` to bar indices by exact `CloseTime` match.
  - **Profile**: price range `[min Low, max High]` over the reference bars; fixed-width bins of width
    `w = 0.10 · ATR_entry` (`≥1` bin; bin count `= max(1, ceil((hi−lo)/w))`). Each reference bar's
    `TickVolume` is distributed **uniformly across `[Low, High]`** in proportion to each bin's overlap
    fraction with `[Low, High]` (a degenerate `High==Low` bar deposits its full volume in the single bin
    containing that price). Accumulate per-bin volume.
  - **POC** = centre of the **maximum-volume bin**; tie-break **lowest bin index (lowest price)**,
    predeclared deterministic.
  - **70% value area**: start from the POC bin; repeatedly annex the neighbouring bin (immediately above
    or below the current contiguous run) with the **larger** volume until cumulative volume `≥ 0.70 ·
    total`; tie-break **annex the upper bin first**, predeclared. `VAH` = high edge of the highest VA
    bin; `VAL` = low edge of the lowest VA bin.
  - **Three levels** → three variant targets: `VP-POC` = POC centre; among `{VAL, VAH}` keep only levels
    with valid signed reversal distance `rd·(level − C) > 0`, then `VP-NEAR` = the valid level with the
    **smaller** `fav_dist`, `VP-FAR` = the valid level with the **larger** `fav_dist`.
  - **Insufficient-profile / validity exclusions (per event, per VP variant, disclosed counts)**:
    `M_k` reference span `< 3` domain bars → all three VP variants excluded-with-record; a particular VP
    level with `rd·(level − C) ≤ 0` → **that level's** variant excluded-with-record (e.g. POC behind `C`
    excludes `VP-POC` only). Never silently clamped.

- **`VP-POC-INPROG`** (disclosed-only): identical construction but reference bars are the **in-progress
  move** `[bar_idx(EndTime_k)+1 … entry_idx]`; POC only. Retained to **empirically expose** the
  path-dependence concern (operator note). Never binding.

- **`/MAGTARGET` (new module) — trailing-magnitude distance** (LOOKBACK>1; magnitude estimate, no
  absolute level): for `(frac, W) ∈ {0.5,1.0}×{5,20}`,
  `fav_dist = frac · median(|EndPrice − StartPrice| of the trailing W moves confirmed strictly before
  t_i)`; `fav = C + rd·fav_dist`. Warmup: `< W` confirmed moves before the harami → that variant excluded
  -with-record (disclosed). `fav_dist > 0` always (magnitudes positive), so no signed-side exclusion.

- **Generalized barrier helper** (new module) `barriers_from_fav(C, rd, fav_level) → (fav, adv,
  fav_dist)` with `fav_dist = rd·(fav_level − C)`, `adv = C − rd·fav_dist`, and a `valid = fav_dist > 0`
  flag; used for all VP variants. `/MAGTARGET` and `BENCH` build `fav` from a distance directly (always
  valid).

- **Why**: the registered `/VPTARGET` / `/MAGTARGET` favourable models, varied OAT against the frozen
  benchmark; the prior-completed-move VP reference is the operator's binding choice (in-progress VP
  retained only as a disclosed diagnostic). The 1:1 adverse and adaptive cap are held fixed so the read
  isolates the favourable leg.
- **Assumptions**: VP reference bars are causal (`M_k` confirmed before `t_i`); bin width tied to
  `ATR_entry` (known at `t_i`) — deterministic, no look-ahead. `TickVolume` is a **broker tick-count
  proxy** for traded volume — disclosed in every `/VPTARGET` result.
- **Expected output**: per retained event, for each variant `(fav, adv, fav_dist, valid_flag,
  exclusion_reason)`, plus the shared adaptive cap `N` and warmup flag.

### Step 4: P15 path-ordered fill resolution + realised gross return per variant (reused kernels)

- **Method**: for each variant's valid, non-warmup event, resolve first-touch via
  `xen.expectancy.resolve_path_ordered` (explicit bounded sequential scan over
  `[entry_idx+1, min(entry_idx+N, last_idx)]` on real OHLC; same-bar double-touch resolved by the P15
  intrabar path — bullish `O→L→H→C`, bearish `O→H→L→C`) → classes `{FAV, ADV, TIMECAP, DATA_CENSORED}`
  and exit price (target level for FAV/ADV; cap-bar real **close** for TIMECAP). Realised gross return
  `xen.expectancy.realised_returns` → `r_e = rd·(exit − C)/ATR_entry`. Qualifying population
  `xen.expectancy.qualifying_mask` = built-barrier `{FAV,ADV,TIMECAP}` with finite exit and
  `ATR_entry>0`.
- **Why**: first-hit `r` is blind to the family's position-management value (P14/lessons §8.6); the
  realised-return endpoint is what the mechanism can express, and P15 removes the worst-case-tie-break
  bias on a near-0.50 substrate. The resolver loop's causal/streaming semantics are the object under
  test — **not vectorized**.
- **Assumptions**: the intrabar path is a documented approximation (1-minute base bars not replayed);
  disclosed; EXP-054 bounded its effect as immaterial (median Δr 0.010).
- **Expected output**: per variant per cell, the entry-time-ordered `r_e` series, the
  `(FAV,ADV,TIMECAP,DATA_CENSORED, warmup, validity-excluded)` counts.

### Step 5: Per-cell median expectancy + regime-clustered moving-block bootstrap *(stat methods 1–2)*

- **Method**: per cell × variant × arm (`/STRONG-STAT` binding; `/STRONG-HA` disclosed),
  `E_cell = median(r_e over qualifying events)`. CI via `xen.expectancy.bootstrap_median_distribution`
  (events in entry-time order; block `b = max(1, round(m^(1/3)))`; `ceil(m/b)` contiguous blocks per
  resample truncated to `m`; `N_BOOT=10_000`; batched; **fixed seed = master + stable per-(cell,variant)
  offset**) → `median_ci` one-sided `CI_low` (5th pct) + two-sided (2.5/97.5). **Method 1** = each
  variant's signal median CI; **method 2** = each P13 baseline median CI (Step 6). The mean is a
  disclosed secondary.
- **Why**: the per-event ATR-normalised return distribution is fat-tailed (FAV/ADV cluster at
  `±fav_dist/ATR`, TIMECAP spreads) → the **median** is the robust location estimator (P14); the
  moving-block bootstrap is non-parametric and preserves local serial/regime dependence.
- **Simpler alternative considered**: sign / Wilcoxon test on `r_e>0` — rejected as binding (assumes
  exchangeable events, tests a different null); normal-theory t-CI rejected (fat tails). Reported
  informally at most.
- **Expected output**: per cell × variant × arm `(m, E_cell, CI_low_1s, CI_lo_2s, CI_hi_2s, block_len,
  mean, r, win_rate, timecap_frac)` and `viable_status` (`VIABLE` iff `CI_low_1s>0` AND `m≥30`; else
  `CI_SPANS_0` / `NOT_VIABLE_BY_POWER`).

### Step 6: P13 baselines through the identical per-variant pipeline (disclosed) *(method 2 reused)*

- **Method**: both baselines are scored through the **identical** Step 3–5 pipeline **for every binding
  variant** (same favourable geometry, 1:1 adverse, adaptive cap, P15 fills, median + same bootstrap),
  marked **disclosed-only**:
  1. **Matched-count random in-regime timestamps**: draw the same count as the variant's qualifying
     events, without replacement, from the cell's eligible-bar pool (TRAIN bars with a defined
     in-progress move, defined `ATR_entry`, defined cap, and not a retained-signal bar); each drawn bar
     takes the **in-progress `rd`** at that bar (direction is NOT randomised) and builds that variant's
     geometry identically. Fixed per-(cell,variant) seed, distinct RNG stream from the bootstrap.
  2. **MA(20,50) segmentation**: replace the ATR-ZigZag substrate with MA(20,50)-crossover segments on
     domain `Close` (EXP-050/053 arm); re-run the full conditioned-signal pipeline (harami +
     current-price magnitude-percentile + harami anchor + the variant's favourable geometry + 1:1 adverse
     + cap + P15) on MA segments. For `/VPTARGET` the reference move is the prior completed MA segment;
     for `/MAGTARGET` the trailing magnitudes are completed MA-segment ranges.
- **Why**: P13/P20. Disclosed robustness — does a given geometry beat random entries (matched count,
  same geometry, same regime pool, same direction rule) and is any effect ZigZag-specific?
- **Note (runtime)**: this is the compute-dominant part (≈ 8 variants × 2 baselines × 99 cells × 10k
  bootstrap). It is **disclosed-only** and must not block the binding read; `tqdm`, bounded per-cell
  memory, fixed seeds. If a baseline cell has `< 30` matched events it is `NOT_VIABLE_BY_POWER`
  (disclosed), never an undefined ratio.
- **Expected output**: per cell × variant, baseline `(m, E_cell, CI_low_1s, …)` for matched-random and
  MA-seg, same schema as Step 5.

### Step 7: Contrasts — variant−benchmark (paired, binding) and variant−baseline (independent, disclosed) *(stat methods 3–4)*

- **Method 3 — variant − benchmark (PAIRED; binding):** the variant and the benchmark are evaluated on
  the **same conditioned events**, so the contrast is paired on the **common qualifying-event subset**
  `S = {events qualifying under BOTH this variant and BENCH}` (entry-time ordered). A **paired moving-block
  bootstrap** (new module `paired_median_contrast_ci`, reusing the `bootstrap_median_distribution` block
  construction): for each resample draw **one** set of block indices over `S` and apply them to **both**
  the variant `r_e` series and the benchmark `r_e` series restricted to `S`; statistic
  `Δ* = median(variant_S*) − median(BENCH_S*)`. Report one-sided `CI_low(Δ)` (5th pct) and two-sided
  bounds. **Variant beats benchmark in a cell iff `CI_low(Δ) > 0` AND `|S| ≥ 30`.** Pairing on the same
  resample indices cancels the shared event/regime noise → the correct (tighter) difference CI;
  the independence-assuming `xen.expectancy.contrast_ci` is **not** used here (it would over-state
  variance and could hide a real difference).
- **Method 4 — variant − baseline (INDEPENDENT; disclosed):** variant signal vs each P13 baseline are
  **independent** event sets (different timestamps) → use `xen.expectancy.contrast_ci` (independent block
  bootstraps, resample-index pairing as Monte-Carlo convenience). Disclosed-only.
- **Matched cells in the quorum**: the benchmark-beat composition counts only cells where **both** the
  variant and BENCH are reportable (`m_variant ≥ 30` AND `m_BENCH ≥ 30` AND `|S| ≥ 30`); a cell where
  BENCH is itself non-viable is **not** counted as a "beat" (avoids crediting a variant for clearing a
  degenerate benchmark) — recorded separately as `variant_viable_where_bench_not` for disclosure.
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
- **No within-experiment family-wise correction** (see §Multiplicity). All 8 binding variants are
  reported; the verdict is descriptive and feeds G2.
- **Expected output**: per-variant composition tallies, the variant-pass booleans, the EVIDENCE_* label,
  and the multiplicity disclosure block → `composition_readout.json` + `favourable_target_map.csv`.

### Step 9: Determinism, causality, reconciliation gates (binding correctness)

- **Determinism**: re-run one cell (and the full grid in a second pass over a fixed sample) end-to-end;
  assert byte-identical per-cell per-variant outputs. Any mismatch → SUBSTRATE/METHOD_DEFECT.
- **Causality / invariants (assert in code)**: every quantity at `t_i` uses only bars `≤ t_i` and moves
  with `ConfirmTime ≤ t_i`; VP reference bars satisfy `CloseTime ≤ EndTime_k < ConfirmTime_k ≤ t_i`;
  barriers/cap use only moves confirmed strictly before `t_i`; first-touch scan starts at `entry_idx+1`
  and reads no bar with `CloseTime > train_end_ts` (else DATA_CENSORED); `fav_dist > 0` for every
  resolved event; VP bins partition `[lo,hi]` and bin volumes sum to the reference TickVolume total
  (±1e-9). Violation on ≥3 instruments → SUBSTRATE/METHOD_DEFECT.
- **Population reconciliation (vs EXP-053)**: the binding `/STRONG-STAT` conditioned-event set (count +
  `trigger_idx/time/rd` digest per cell) **and** the `BENCH` variant's per-cell median expectancy must
  match EXP-053's conditioned population and benchmark `E_cell` on the same grid (same detector, filter,
  TRAIN fence, geometry). Exact match expected (same functions, same constants); any mismatch is a
  defect, investigated before the readout is trusted. This is the cross-experiment anchor that the same
  signal and the same benchmark are being measured.
- **Expected output**: `determinism_ok`, `causality_ok`, `reconciliation_ok` flags + the per-cell
  BENCH-vs-EXP-053 diff table.

---

## Multiplicity posture (predeclared)

EXP-056 is **gross, 0-slot, 0-TEST characterization** feeding the **single 014-B G2** (the design
forbids intermediate gates and early closure). The cross-variant multiplicity is therefore controlled by,
in order:

1. **Full predeclaration + report-all (file-drawer/registry control).** All 8 binding variants (and the
   disclosed in-progress VP-POC) are predeclared in the scope and **every** one is reported with its full
   per-cell readout — none is drawered or selected post-result. This is the programme's primary
   multiplicity control (registry pattern; cf. EXP-046's 7-variant entry screen).
2. **P11 breadth as the robustness filter.** A "variant passes" requires viability **and**
   benchmark-beat on **≥5 cells over ≥3 instruments** — far stronger against per-cell noise than any
   single uncorrected CI; a variant winning on scattered singletons cannot pass.
3. **Deferral of binding family-wise inference to G2.** EXP-056 applies **no** Holm/Bonferroni across the
   8 variants; its per-variant `CI_low` thresholds are **uncorrected one-sided 95%**. The binding
   family-wise correction across the full 014-B surface (all favourable/adverse/third/exit geometries) is
   the **single G2 desk adjudication**'s responsibility, on the complete slate — not this experiment's.
4. **Multiplicity disclosure (no new statistical method).** The readout reports, for the desk: the number
   of binding variants that pass (`n_pass`), the per-variant `(W, I_W)` margins above the P11 quorum, and
   a **fragility flag** for any pass resting on a bare quorum (exactly 5 cells or exactly 3 instruments,
   mirroring EXP-046's bare-clearance disclosure). No computed permutation null is added (stays within
   the 4-method budget); the desk uses these counts plus the G2 family-wise correction.

This posture is fixed before results exist and is not revisited after seeing them.

---

## Visualisations (5 / 5)

1. **Per-variant median-expectancy forest plot** (binding `/STRONG-STAT` arm): for each binding variant,
   member cells' `E_cell` with one-sided `CI_low` whiskers, faceted or colour-grouped by variant, with
   the `BENCH` per-cell median overlaid as a reference marker. *Answers: is each variant's conditioned
   expectancy > 0 per cell, and how does it sit vs benchmark?*
2. **Variant − benchmark contrast heatmap**: variants (rows) × cells (cols), cell colour = paired
   `CI_low(Δ_bench)` sign/magnitude (with `beats_bench` hatching). *Answers: which variant beats benchmark,
   where, and is it coherent across cells/instruments or scattered?*
3. **Pooled per-event return distribution by variant** (violin/box of ATR-normalised `r_e` across viable
   cells, per-variant medians + the BENCH median line overlaid). *Answers: distribution shape (justifies
   the median), where mass sits vs 0, FAV/ADV/TIMECAP structure per geometry.*
4. **P11 "wins-over-benchmark" composition map**: instrument × domain grid per variant (small multiples
   or a variants×cells status grid) coloured by `win / viable-only / CI_SPANS_0 / NOT_VIABLE_BY_POWER /
   COVERAGE_EXCLUDED`. *Answers: does any variant clear ≥5 cells / ≥3 instruments, and where?*
5. **Per-cell qualifying-event / exclusion-fraction map**: per variant, qualifying-event count and the
   exclusion breakdown (validity `fav_dist≤0`, insufficient-profile, warmup, DATA_CENSORED) as a stacked
   fraction, with the 30-event power floor marked. *Answers: how much each geometry costs in power and how
   many cells survive to be reportable — central to an INCONCLUSIVE read.*

Secondary tables (`/STRONG-HA` arm, in-progress VP-POC, STAT-MAD arm, both P13 baselines and their
contrasts, `r`/win-rate/TIMECAP fractions, `TickVolume`-proxy note) go to CSV, not plots.

---

## Interpretation Guide (predefined, mechanical)

Binding arm `/STRONG-STAT`; per variant; all gross; TRAIN-only. Let a variant **pass** iff its `win`
composition clears P11 (`W ≥ 5` over `≥3` instruments), where `win = viable AND beats_bench` (Step 8).

- **EVIDENCE_FOR** (a favourable-target lever helps) iff **≥1 binding alternative variant passes** — it
  is viable on its own median expectancy **and** beats the benchmark on the paired contrast, on ≥5 cells
  over ≥3 instruments. → At least one alternative favourable geometry improves conditioned capture over
  the benchmark on this surface leg. Report **all** passing variants and their margins; **no candidate
  registration / no selection of a single winner** (G2 only). *(Reason: the family's defining conditioned
  signal captures more under a different, predeclared favourable target than under the 50%-of-`M_sofar`
  benchmark, robustly across the grid.)*
- **EVIDENCE_AGAINST** (favourable geometry is not a lever) iff there are **enough powered cells to
  adjudicate** — for the benchmark and ≥1 alternative, `P_powered ≥ 5` over `≥3` instruments — **and no**
  binding alternative variant passes. → Recorded as a measured-negative characterization; routing
  deferred to the single 014-B G2. *(Reason: with adequate power, no alternative favourable target
  reliably beats the benchmark; the favourable leg is not where conditioned capture is gained.)*
- **INCONCLUSIVE (power-limited)** iff a P11 quorum of powered cells **cannot be formed** for the
  benchmark and the alternatives (`P_powered < 5` or `I_powered < 3` on the variants of interest), with
  no correctness failure. → Validity/warmup/censoring exclusions (heaviest on `/VPTARGET` short-`M_k`
  references and `/MAGTARGET` long-`W` warmup) depleted counts below the adjudication floor; disclosed,
  never defaulted to a ratio. *(Reason: insufficient coverage, not absence of effect.)*
- **SUBSTRATE/METHOD_DEFECT** iff any determinism, causality, invariant, or reconciliation gate fails
  (Step 9) → fix before reporting; no efficacy claim.

Disclosed-only (never change the verdict): the `/STRONG-HA` arm, the in-progress VP-POC variant, mean
expectancy, first-hit `r`, win rate, TIMECAP/censoring fractions, the STAT-MAD sensitivity, and both P13
baselines and their (independent) contrasts. Their agreement/divergence is reported for context — in
particular, **`VP-POC-INPROG` vs `VP-POC`** quantifies the operator's path-dependence concern, and the
matched-random contrast indicates whether a winning geometry beats random entries under the same geometry.

---

## Implementation Safety / Constraints for `experiment-developer`

- **Holdout / TEST**: slice the **1-minute base** to the first `int(int(total_rows·0.7)·0.7)` file-order
  rows before any aggregation; never materialize TEST or the final-30% holdout. No new-universe
  holdout/TEST row is read (the conditioned event definition already had its first TRAIN contact in
  EXP-053).
- **Temporal order & alignment**: sort/assert domain bars by `CloseTime`; align HA↔real and
  harami/move-times↔bar grid by **exact `CloseTime` match** (searchsorted + equality assert), never by
  bar index.
- **Causality (assert)**: every quantity at `t_i` uses only bars `≤ t_i` and moves `ConfirmTime ≤ t_i`;
  VP reference (`M_k`) bars are all `≤ EndTime_k`; `/MAGTARGET` magnitudes and the time cap use only
  moves confirmed strictly before `t_i`; first-touch scan starts at `entry_idx+1`; `M_sofar` uses only
  `C` and the known `StartPrice_inprogress`.
- **Sequential vs vectorized**: keep the **P15 first-touch resolver** (`resolve_path_ordered`) and the
  **live in-progress-state walk** explicit/bounded (causal semantics under test — do not vectorize). VP
  binning, trailing-magnitude windows, MA segmentation, and bootstrap **index construction** may be
  vectorized in bounded batches (reuse `bootstrap_median_distribution` batching). The VP profile builder
  is per-event; its cost is `n_bins = ceil((maxHigh − minLow of M_k) / (0.1·ATR_entry))`, i.e. bounded by
  the reference move's **range/ATR ratio**, *not* its bar count. A `VP_MAX_BINS` guard
  (`favourable_targets.py`) trips a SUBSTRATE/METHOD_DEFECT on a runaway ratio (e.g. volatility
  contraction) rather than allocating an unbounded profile.
- **Denominators / zero-baseline**: qualifying population per variant = FAV/ADV/TIMECAP (built barrier);
  `< 30` → `NOT_VIABLE_BY_POWER` (no ratio); validity (`fav_dist≤0`), insufficient-profile (`<3` ref
  bars), warmup (`/MAGTARGET <W` moves; `<5` cap durations; NO_DECISION `/STRONG-STAT`), and
  DATA_CENSORED events are excluded with **disclosed per-variant counts**. The paired benchmark contrast
  uses the **common** qualifying subset `S` with `|S| ≥ 30`.
- **Determinism / seeds**: single master seed in constants; per-(cell,variant,purpose) RNG via
  `default_rng(master + stable_offset)` (distinct streams for bootstrap vs matched-random draws); emit a
  determinism self-check (re-run a sample, assert identical) and the EXP-053 reconciliation anchor.
- **Progress / memory / runtime**: `tqdm` over the 99-cell grid; per-cell bounded memory (process and
  discard each cell; persist only per-cell×variant summary rows + a bounded per-event parquet for plots).
  The per-variant × per-baseline bootstrap matrix is the runtime-dominant part — disclose expected
  runtime; baselines are disclosed-only and must not gate the binding read.
- **Real-price discipline**: HA prices only in `detect_ha_harami` / `annotate_ha_impulse`; `C`, `M_sofar`,
  VP profile (real `Low/High` + `TickVolume`), trailing magnitudes, barriers, fills, `ATR_entry`,
  returns, `r`, win rate **all** on real domain OHLC. `TickVolume` is a tick-count **proxy** — disclosed
  in every `/VPTARGET` output.
- **New module** (the one new module): `xen/favourable_targets.py` — the volume-profile builder
  (TickVolume→bins, POC, 70% VA, near/far edges, deterministic tie-breaks), the trailing-magnitude target,
  `barriers_from_fav`, and `paired_median_contrast_ci` (paired block bootstrap reusing the
  `bootstrap_median_distribution` block construction). Everything else reuses `xen.expectancy`
  (`live_in_progress_state`, `live_strong_stat`, `adaptive_time_caps_by_epoch`, `benchmark_barriers`,
  `resolve_path_ordered`, `realised_returns`, `qualifying_mask`, `bootstrap_median_distribution`,
  `median_ci`, `contrast_ci`), `xen.zigzag`, `xen.heiken_ashi_generator`, `xen.ha_harami`,
  `xen.strong_move`, `xen.capture_barriers`, `xen.bar_aggregator`.
- **Frozen constants** (no tuning): `atr_period=14`, `atr_mult=1.0`, benchmark `X=0.50`, R:R `1:1`,
  time-cap `(k=1.5, window=20, floor=6, median)`, STAT `(window=20, min=5, q=0.75)`, HA `run_len=3`,
  VP `(bin_width=0.10·ATR_entry, value_area=0.70, min_ref_bars=3, POC tie=lowest-price,
  VA tie=upper-first)`, MAG grid `frac∈{0.5,1.0}×W∈{5,20}`, `POWER_FLOOR=30`, `N_BOOT=10_000`,
  `BOOT_BATCH=2_000`, `P11=(≥5 cells, ≥3 instruments)`.

---

## Complexity Check

- **Statistical methods: 4 / 4** — (1) variant median block-bootstrap CI; (2) baseline median bootstrap
  (matched-random + MA-seg, same method); (3) **paired** variant−benchmark contrast CI; (4) independent
  variant−baseline contrast CI (disclosed). The `/STRONG-HA` arm, STAT-MAD, in-progress VP-POC, mean,
  `r`, win rate, TIMECAP fraction reuse these methods as **disclosed secondaries** — no new method. The
  multiplicity disclosure adds **no** computed test (counts only).
- **Visualisations: 5 / 5** — forest; variant−benchmark contrast heatmap; return-distribution-by-variant;
  wins-over-benchmark composition map; qualifying/exclusion-fraction map.
- **New modules: 1 / 1** — `xen/favourable_targets.py` (VP builder + trailing-magnitude target +
  `barriers_from_fav` + paired contrast bootstrap). All other machinery reused.
