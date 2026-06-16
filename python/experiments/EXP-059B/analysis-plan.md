# Analysis Plan: Experiment EXP-059B

**Title:** Uncapped Structure Trailing (Conditioned HA Harami; `/EXIT-TRAIL-UNCAPPED`)
**Phase / checkpoint:** `2026-06-14-014-ha-harami-substrate-and-capture` (014-B; G0-B PASS 2026-06-15)
**Family / HYP:** `CF-HA-HARAMI-001/HYP-012b` — EXP-059B (SCOPED, Phase 014-B batch); follow-up to EXP-059
**Binding endpoint:** median per-event **position-weighted** gross expectancy `E_cell` (P14), ATR-normalised,
P15 fills, real prices, on the binding `/STRONG-STAT` arm; per-cell viable iff `CI_low > 0` (one-sided 95%
moving-block bootstrap) AND ≥30 qualifying events; composed by P11 (≥5 cells over ≥3 instruments).
**Discipline:** gross; 0 candidate slots; 0 TEST reads; TRAIN only; holdouts sealed; detection on HA candles,
**all outcome metrics on real prices**. This plan does **not** expand `scope.md`; it specifies *how* the 5
predeclared arms are computed, validated, and read. No standalone governance (Stage 4 runs consolidated).

---

## Objective

Determine whether the structure trailing stop, run **as a standalone adverse-exit model** (no benchmark
time-cap backstop and no initial 1:1 stop — the position carries no adverse exit until the first secondary
`atr_mult=0.5` ZigZag pivot confirms after entry, then ratchets), raises the conditioned HA-harami's gross
per-event **median position-weighted expectancy** vs the benchmark single fixed exit — alone
(`TRAIL-PURE-UNCAPPED`) or alongside V2A partial favourable legs (`COMBINED-UNCAPPED-V2A`). EXP-059 measured
every trailing/combined arm **inside** the benchmark 6-bar-floor cap (`n_event = bench_n` in
`xen.position_exits.resolve_legs`/`build_active_stops`, with an explicit `TIMECAP` exit); even
`TRAIL-TP-NOINIT` retained the cap. EXP-059B fills that gap on the identical conditioned population and
99-cell grid, and isolates the cap effect with paired capped no-init siblings. This is a characterization read
feeding the single 014-B G2 — never a closure here.

**Predeclared arm set (5; identical to `scope.md` §Arms):**

| # | Arm | Fav side | Adverse model | Cap | Init stop | Role |
|---|-----|----------|---------------|-----|-----------|------|
| 1 | `BENCH` | 50% fav (1 leg) | 1:1 fixed | adaptive cap | 1:1 | Reference; reproduces EXP-053/059 (invariant). Binding contrast anchor. |
| 2 | `TRAIL-PURE-UNCAPPED` | none (1 leg) | structure trail | **none** | **none** | **BINDING.** Pure trailing as designed. |
| 3 | `COMBINED-UNCAPPED-V2A` | V2A {1/3,2/3,1}×fav_dist | structure trail (open weight) | **none** | **none** | **BINDING.** Partials + uncapped no-init trailing. |
| 4 | `TRAIL-PURE-NOINIT-CAPPED` | none (1 leg) | structure trail | adaptive cap | none | **Disclosed** cap-isolation sibling of #2. |
| 5 | `COMBINED-V2A-NOINIT-CAPPED` | V2A | structure trail (open weight) | adaptive cap | none | **Disclosed** cap-isolation sibling of #3. |

`/STRONG-HA` is a disclosed secondary filter arm run through the identical pipeline; both P13 baselines
(matched-count random in-regime timestamps; MA(20,50) segmentation) run through the identical per-arm
pipeline.

---

## Methodology

### Step 1: TRAIN-slice loading, domain construction, holdout fence

- **Method:** F01 file-order-prefix slicing per cell. Lazy `pl.scan_parquet`; `total_rows`;
  `analysis_rows = int(total_rows*0.7)`; `train_rows = int(analysis_rows*0.7)`; collect the first `train_rows`
  file-order 1-minute rows only; assert strictly increasing `CloseTime`; `train_end_ts = max(CloseTime)`,
  `last_train_idx = train_rows − 1` (the index any unbounded forward scan may not pass). Aggregate each member
  domain (5m strict; 15m/30m/1h/2h/4h via `xen.bar_aggregator.aggregate_ohlc`, `min_coverage=0.90`); fence all
  derived series to `CloseTime ≤ train_end_ts`.
- **Why this method:** byte-identical fence to EXP-049/053–059 guarantees the conditioned population reconciles
  exactly with EXP-053 and that neither the nested TEST stratum nor the final-30% global holdout is touched.
- **Simpler alternative considered:** sort-then-slice on `CloseTime` — rejected; the F01 prefix is the
  established convention and avoids materialising the full file.
- **Assumptions:** 1-minute base rows are in chronological file order (asserted). Holds — VAL-001/VAL-004.
- **Expected output:** per-cell TRAIN real domain bars + `train_end_ts` + `last_train_idx`; the
  holdout-exclusion guard.

### Step 2: Substrate, detector, and the conditioned population (identical to EXP-053–059)

- **Method:** primary `xen.zigzag.generate_zigzag(bars, atr_period=14, atr_mult=1.0)` → confirmed moves +
  `xen.capture_barriers.confirm_indices`; **secondary** `generate_zigzag(bars, atr_period=14, atr_mult=0.5)`
  → secondary confirmed moves/pivots + confirm indices (for the trailing stop only); HA candles
  (`xen.heiken_ashi_generator`) → `xen.ha_harami.detect_ha_harami` (frozen EXP-048 detector), aligned to real
  bars by `CloseTime`; `xen.expectancy.live_in_progress_state` (`rd`, `start_pivot`/`start_idx`, `M_sofar`) +
  `live_strong_stat` (binding p75 retention; disclosed MAD); `/STRONG-HA` via
  `xen.strong_move.annotate_ha_impulse`.
- **Why this method:** every primitive is frozen and validated (EXP-048/051); reusing the *same* functions is
  what makes the population reconcile with EXP-053 exactly (invariant ii).
- **Simpler alternative considered:** none — the conditioned-signal definition is fixed by P16.
- **Assumptions:** ZigZag/HA causality (pivots future-info until confirmed). Holds by construction.
- **Expected output:** the binding `/STRONG-STAT` conditioned event set per cell (entry bar `C`, `rd`,
  `M_sofar`, `start_idx`, `ATR_entry`); the `/STRONG-HA` arm.

### Step 3: Benchmark geometry + adaptive time cap (BENCH and capped siblings only)

- **Method:** `xen.expectancy.benchmark_barriers(C, rd, M_sofar)` → `fav_dist = 0.5·M_sofar`,
  `fav = C + rd·fav_dist`, `adv = C − rd·fav_dist`; `xen.expectancy.adaptive_time_caps_by_epoch(..., floor=6)`
  → `bench_N`, `warmup` (P4). `bench_N` bounds the forward window for arms 1/4/5 only; the **uncapped arms (2,
  3) do not use `bench_N` as a window bound** (Step 5). The V2A leg levels `C + rd·{1/3,2/3,1}·fav_dist` are
  shared by arms 3 and 5.
- **Why this method:** OAT discipline — only the adverse-exit model (cap on/off, init stop) varies; the
  favourable level and the benchmark cap (where present) are reused verbatim from EXP-053/059.
- **Assumptions:** `M_sofar > 0` for a valid target (gated). Holds for conditioned events by construction.
- **Expected output:** per-event `fav`, `adv`, `fav_dist`, V2A levels, `bench_N`, `warmup`, `ATR_entry`.

### Step 4: BENCH + capped sibling resolvers (reuse EXP-059 machinery)

- **Method:** BENCH single leg via `xen.expectancy.resolve_path_ordered(fav, adv, bench_N)` (exactly EXP-053).
  The capped siblings (arms 4, 5) reuse the **existing** EXP-059 `xen.position_exits.resolve_legs` /
  `build_active_stops` path with `adv_mode = ADV_TRAIL` and `trail_init_none = True` (no initial stop), the
  benchmark `bench_N` window, and the `PX_TIMECAP` exit for any still-open leg at the cap. Arm 5 uses the V2A
  leg kinds/levels; arm 4 is single-leg `LEG_NONE`.
- **Why this method:** the capped siblings are exactly EXP-059's trailing machinery with the init stop removed
  — reusing the frozen resolver (unmodified) guarantees the cap-isolation contrast (Step 9) differs from the
  uncapped arm *only* by the cap, and lets BENCH reproduce EXP-053/059 (invariant i).
- **Simpler alternative considered:** re-implement the capped path — rejected; reuse is correct and avoids
  drift from EXP-059.
- **Expected output:** per event per leg for arms 1/4/5: exit class ∈ {FAV, ADV/TRAIL, TIMECAP, DATA_CENSORED}
  and exit price; the per-leg exit-reason tags.

### Step 5: NEW — uncapped lazy trailing resolver (arms 2, 3; the only new code)

The single genuinely new computation, added as a **new entry point** in `xen.position_exits` (e.g.
`resolve_legs_uncapped` + a lazy active-stop helper). **It must not call the dense `build_active_stops`** —
that allocates `(n_events, max(n_event)+1)`; uncapped, `max(n_event)` would be ~the full TRAIN length, giving
an `O(n_events × train_len)` matrix that blows up memory. The stop is computed **lazily inside** a bounded,
explicit, **sequential** forward scan over real OHLC. **Do not vectorize this loop — it is the object under
test. Do not modify the existing `resolve_legs`/`build_active_stops`/`_scan_event` (EXP-059's frozen results
depend on them); add alongside.**

- **Window.** Scan `[entry_idx + 1, last_train_idx]` (no `bench_N` bound). The scan terminates early when the
  trailing stop fills or all legs close.
- **Lazy active-stop update (causal, monotone).** Maintain a pointer into the secondary confirmed moves
  (Direction, `EndPrice`, `ConfirmIdx`), ascending in `ConfirmIdx`. At each bar `i`, advance the pointer over
  all secondary confirmations with `ConfirmIdx ≤ i`; for a long fade (`rd=+1`) each newly confirmed secondary
  **up-move** (`Direction=+1`) ratchets `stop ← max(stop, previous opposite secondary pivot EndPrice)`; mirror
  (`min`, pivot low → stop on a confirmed pivot low) for a short fade. The stop is **NaN (inactive — no adverse
  exit) until the first post-entry secondary confirmation** (no initial stop). This reproduces the P18 ratchet
  in EXP-059's `build_active_stops` exactly, computed incrementally rather than into a dense array.
- **Per-bar P15 resolution.** Same path order as EXP-059: bullish bar (`Close ≥ Open`) `O→L→H→C`; bearish
  `O→H→L→C`. For a long fade the adverse-side extreme is the Low and the favourable side the High (mirror for
  short). Per bar: (i) if the trailing stop is active and its level is reached on the adverse-side extreme
  **before** the favourable side along the path, **all still-open legs close at the stop level/bar** (TRAIL);
  (ii) otherwise touched V2A favourable-level legs (arm 3 only) close at their levels; (iii) if the trailing
  stop is active and reached on the adverse extreme **after** the favourable side, all still-open legs close at
  the stop.
- **No TIMECAP, DATA_CENSORED at the edge.** The uncapped arms emit **no** `PX_TIMECAP` class. If the scan
  reaches `last_train_idx` with the position (or any open leg) still open, those legs are **`DATA_CENSORED`**
  (excluded-with-record) — never resolved on truncated/TEST data.
- **Causal/streaming correctness argument:** every quantity read at bar `i` is real OHLC of a bar with index
  `> entry_idx` and `CloseTime ≤ train_end_ts`; the active stop uses only secondary moves with `ConfirmIdx ≤ i`
  (and a ZigZag `ConfirmTime` is strictly later than the pivot it locates → the pivot price is from a
  fully-confirmed past move). No future bar enters any decision. Per-event cost is
  `O(last_train_idx − entry_idx)` worst case, not `O(6)` — budget runtime accordingly.
- **Why this method (vs reusing the capped resolver):** unbounding the window and removing the cap/init-stop
  changes the window length to the TRAIN edge and removes the `TIMECAP` terminal class; the dense-array stop
  builder is infeasible at that length. A lazy entry point is necessary and minimal (still 0 new modules — an
  added function in the existing `position_exits.py`).
- **Expected output:** per event per leg for arms 2/3: exit class ∈ {FAV, TRAIL, DATA_CENSORED} and exit
  price; the bar index of exit (for holding duration, Step 12).

### Step 6: Position-weighted realised return + qualifying mask

- **Method:** `R_event = Σ_l w_l · rd·(exit_px_l − C)/ATR_entry`, `Σ_l w_l = 1` (3 legs `w=1/3` for V2A
  combined arms; 1 leg `w=1` for BENCH/TRAIL-PURE arms). Each `exit_px_l` is the Step 4/5 P15 fill. Reuse the
  `xen.position_exits.weighted_returns` sign/normalisation convention. **Qualifying** (the P14 denominator):
  `fav_dist > 0`, finite `ATR_entry > 0`, the arm's construction available (trailing arms require ≥1 prior
  secondary-ZigZag confirmation history else warmup-excluded), and **every** leg / the position reaches a
  finite P15 exit within the TRAIN-fenced window (else `DATA_CENSORED`).
- **Why this method:** the weighted realised return is exactly the mechanism's P&L; the only endpoint that can
  credit trailing stops and partial exits (P14). The qualifying rule mirrors EXP-053–059.
- **Simpler alternative considered:** first-hit `r` — rejected by P14; retained as a disclosed secondary for
  the single-leg BENCH arm only.
- **Assumptions:** ATR-normalisation makes cells comparable (P14). Leg weights are a fixed governance constant.
- **Expected output:** per cell per arm, the qualifying-event `R_event` population (entry-time order), plus
  per-event exit-bar offset and a per-arm censoring/warmup tally.

### Step 7: Per-cell median bootstrap CI (binding viability) — statistical method (1)

- **Method:** `xen.expectancy.bootstrap_median_distribution(R_event, rng, N_BOOT=10_000)` (moving-block,
  `b = round(m^{1/3})`, regime-cluster preserving) + `xen.expectancy.median_ci` → `E_cell` (median),
  one-sided 95% lower bound (5th pct), two-sided bounds. Per-cell viable iff `CI_low > 0` AND `m ≥ 30`.
- **Why this method:** the per-event return distribution is fat-tailed (P14 chose the median); a non-parametric
  moving-block bootstrap respects serial/regime dependence without distributional assumptions. Identical to
  EXP-053–059.
- **Simpler alternative considered:** i.i.d. bootstrap / normal CI — rejected (ignores serial dependence;
  normality fails for these returns).
- **Assumptions:** approximate within-cell stationarity; block length absorbs short-range dependence.
  Acknowledged-weak, mitigated by the block bootstrap.
- **Expected output:** per cell per arm: `E_cell`, `ci_low_1s`, two-sided CI, `m`, viability flag.

### Step 8: Arm − BENCH paired-median contrast (binding "beats benchmark") — statistical method (2)

- **Method:** `xen.favourable_targets.paired_median_contrast_ci(arm_R, bench_R, rng, N_BOOT=10_000)` on the
  **common qualifying-event subset** (events qualifying under *both* the arm and BENCH, entry-time order, equal
  length) — one block-index draw applied to both series so shared event/regime noise cancels. A binding arm
  "beats benchmark" iff the paired contrast `CI_low > 0`.
- **Why this method:** the arm and BENCH share the same conditioned events; the paired contrast is the correct,
  tighter test of "does this exit model add value over the fixed exit on the same events." Identical design to
  EXP-056/057/058/059. **Interpretation caveat (predeclared):** BENCH resolves most events at/before bar 6
  while the uncapped arm may hold them far longer; the common subset **excludes events the uncapped arm
  `DATA_CENSORED`** — so the contrast measures added value of the uncapped scheme over the benchmark *on events
  the uncapped scheme could complete*. The censoring share (Step 10) must be read alongside.
- **Simpler alternative considered:** independent two-sample contrast — rejected (discards the pairing).
- **Assumptions:** common-subset pairing is well-defined (both arms qualify); disclosed where it drops below 30.
- **Expected output:** per cell per binding arm: paired contrast median Δ, `ci_low_1s`, two-sided CI, common `m`.

### Step 9: Cap-isolation paired contrast (disclosed) — statistical method (2), different arm pair

- **Method:** the **same** `paired_median_contrast_ci` applied to (uncapped arm − its capped no-init sibling)
  on their common qualifying subset: `TRAIL-PURE-UNCAPPED − TRAIL-PURE-NOINIT-CAPPED` and
  `COMBINED-UNCAPPED-V2A − COMBINED-V2A-NOINIT-CAPPED`. Disclosed (never binding).
- **Why this method:** the sibling differs from the uncapped arm **only by the cap** (same no-init stop, same
  trailing structure, same favourable side), so this contrast attributes any expectancy difference
  specifically to *removing the cap*, cleanly separating it from the trailing-vs-fixed-exit difference that the
  vs-BENCH contrast measures. Same method as Step 8 → no new statistical method.
- **Assumptions:** common-subset pairing well-defined; the subset is the events both arms resolve (the uncapped
  arm censors a strict superset of what the capped sibling censors near the TRAIN edge — disclosed).
- **Expected output:** per cell: cap-isolation median Δ, `ci_low_1s`, two-sided CI, common `m`.

### Step 10: P13 baselines + arm − baseline contrast — statistical methods (1) on baselines, (3) contrast

- **Method:** run each binding arm's full uncapped pipeline on (a) **matched-count random in-regime
  timestamps** (same cell/regime/direction, EXP-021/027 exclusion convention) and (b) **MA(20,50)**
  segmentation (the secondary 0.5×ATR trailing ZigZag is a real-bar construct, unchanged). Bootstrap each
  baseline median (method 1) and the arm − baseline median difference via `xen.expectancy.contrast_ci`
  (independent streams).
- **Why this method:** baselines test "does the uncapped scheme beat random/alternative-segmentation entries
  under the same scheme" — a specificity check, disclosed (never binding). Identical to EXP-053–059.
- **Simpler alternative considered:** drop baselines — rejected; P13/P20 require them as disclosed secondaries.
- **Assumptions:** independence between signal and baseline draws (stated in `contrast_ci`).
- **Expected output:** per cell per binding arm: baseline medians + arm − baseline contrast (disclosed).

### Step 11: P11 composition + EVIDENCE_* fork

- **Method:** a binding arm is a **per-cell win** iff it is viable (`CI_low>0`, `m≥30`) AND beats benchmark
  (Step 8 `CI_low>0`). The arm clears **P11** iff its wins span ≥5 cells over ≥3 instruments. EVIDENCE_FOR iff
  ≥1 binding arm clears P11; EVIDENCE_AGAINST iff neither does (with sufficient power); **INCONCLUSIVE
  (power-limited)** iff fewer than the P11 quorum of cells reach ≥30 qualifying events on the binding arms
  because uncapped `DATA_CENSORED` depleted counts (no correctness failure); SUBSTRATE/METHOD_DEFECT on any
  invariant failure (Step 13).
- **Why this method:** P11 is the frozen programme composition convention applied after per-cell adjudication;
  the fork is the predeclared mechanical routing. No phase closure here — feeds G2.
- **Expected output:** `composition_readout.json` (per-arm P11 status, wins-over-benchmark map, cap-isolation
  summary, separated-censoring summary, EVIDENCE_*).

### Step 12: Disclosed secondaries

- **Separated `DATA_CENSORED` (binding disclosure requirement):** report the uncapped arms' (#2, #3)
  `DATA_CENSORED` count and rate **separately** from the capped arms' (#1 BENCH, #4, #5) censoring — they have
  different causes (uncapped: unbounded window reaches the TRAIN edge; capped: window past the edge before the
  6-bar cap). The uncapped censoring rate per cell drives the power readout (Step 11) and must be visible
  before any vs-BENCH contrast is interpreted.
- **Holding duration (mechanism diagnostic, disclosed):** per arm, the distribution (median, p90, max) of
  exit-bar offset (`exit_idx − entry_idx`) over qualifying events. Expected: BENCH and capped siblings ≤
  `bench_N` (~6 bars in 96/99 cells); the uncapped arms much longer. Quantifies how much extra holding the
  uncapped model buys and contextualises the censoring.
- **Exit-reason composition (disclosed):** per arm, the fraction of position weight exiting via the favourable
  legs, the trailing stop (TRAIL), the fixed adverse (ADV, BENCH only), the time cap (TIMECAP, capped arms
  only), and DATA_CENSORED. The primary lens for *why* an arm wins or loses.
- **Others:** `/STRONG-HA` arm; per-arm qualifying count + warmup counts; win rate (fraction `R_event>0`); mean
  per-event return; **first-hit `r` for the BENCH arm only** (`n_FAV/(n_FAV+n_ADV)`, TIMECAP excluded; expected
  ≈0.50, replicating EXP-049/053); both P13 baselines. None enters viability.

### Step 13: Determinism + predeclared invariant checks (correctness gate)

Two full passes (fixed seed) must produce identical outputs. The predeclared invariants (scope
§Success/Failure) are asserted in-code and reported:
1. **BENCH reproduces EXP-053/059** per-cell median expectancy and qualifying count to tolerance (and BENCH `r`).
2. **Population reconciliation vs EXP-053 exact** — the binding `/STRONG-STAT` conditioned population is
   identical (entry timestamps, `rd`, `M_sofar`).
3. **Leg weights sum to 1.0** for every arm; a **degenerate single-trigger uncapped arm** (all 3 legs forced to
   one trigger) reproduces the equivalent single-leg uncapped `R_event` to float precision.
4. **Trailing stop monotone** (never loosens) and changes level **only** on secondary-ZigZag confirmation bars
   (`ConfirmIdx ≤ i`) — asserted for both the lazy (uncapped) and dense (capped sibling) stop paths, **and the
   lazy uncapped stop reproduces the dense capped-sibling stop on the shared `[entry+1, entry+bench_N]` prefix
   to float precision** (the two stop computations must agree where their windows overlap).
5. **Every exit is a real-bar P15 fill** with `CloseTime ≤ train_end_ts` (no exit past the TRAIN edge).
6. **Uncapped arms emit no `TIMECAP` class** — only TRAIL, FAV, or DATA_CENSORED; a still-open position at
   `last_train_idx` is DATA_CENSORED.
7. **Trailing stop binds all still-open legs** at the same bar/level when it fills (combined arms).

Any failure → SUBSTRATE/METHOD_DEFECT, fix before reporting (no result-aware threshold change).

**Runtime bound for the uncapped invariants (post-review F03).** The degenerate-match (3), shared-stop
(7), no-TIMECAP (6), and edge invariants re-run the `O(last_train_idx − entry)` uncapped resolver, so
they are evaluated on a **bounded, deterministic, evenly-spaced sample of up to 1500 conditioned events
per cell** rather than the full population; the cheap dense-bounded monotone (4a) and lazy==dense-prefix
(4b) checks still run over the full conditioned population. Disclosed in `run_metadata.json`.

**External oracle for the uncapped region (post-review F07).** The in-run `lazy==dense` check only covers
the shared `[entry+1, entry+bench_N]` prefix; the uncapped region (offset > `bench_N`) — the object under
test — is anchored by `tests/test_position_exits_uncapped.py` (hand-derived ground truth: a trailing fill
past offset 6, DATA_CENSORED at the edge, shared-stop binding, prefix equivalence, F04 additivity).

---

## Visualisations (5 / 5)

1. **Per-arm median-expectancy forest/CI per cell vs benchmark** — does each binding arm's `E_cell` sit above 0
   and above BENCH, per cell? (BENCH and capped siblings overlaid for reference.)
2. **Arm − BENCH contrast heatmap (binding arms × cells)** — where (cells) the paired contrast `CI_low > 0`;
   the P11 pattern at a glance.
3. **Cap-isolation contrast by cell** (uncapped − capped sibling, both pairs) — the marginal effect of removing
   the cap, holding the trailing model fixed.
4. **P11 / wins-over-benchmark map + separated `DATA_CENSORED` rate** across arms — per-arm winning cells and
   instruments vs the ≥5/≥3 quorum, annotated with the uncapped-censoring rate so power-limitation is visible
   beside the verdict.
5. **Exit-reason composition + holding-duration by arm** (stacked weights + duration percentiles) — the binding
   mechanism diagnostic: which exits bind and how much longer the uncapped arms hold.

Secondary tables (`/STRONG-HA`, baselines, BENCH `r`) to CSV, not plots.

---

## Interpretation Guide (predeclared, before results)

- If **≥1 binding arm clears P11** (≥5 cells / ≥3 instruments, `E_cell CI_low>0`) **AND beats benchmark**
  (paired contrast `CI_low>0`) in the quorum → **EVIDENCE_FOR**: the uncapped trailing model improves
  conditioned gross capture; the winning arm(s) + margin are the deliverable for G2/EXP-060 (no candidate
  registration here). Read the **divergent-subset** cap-isolation contrast (`capiso_div_*`, events held past
  `bench_N`) — with its `capiso_div_share` — to confirm the gain comes from *removing the cap* (not just the
  trailing structure, which EXP-059 already characterised capped); the full-common contrast is dominated by
  within-cap structural zeros and a near-zero value there on a small divergent share is **not** a null cap
  effect (post-review F02). Use the exit-reason/holding-duration panels (now measured for *every* arm,
  post-review F04) to attribute *why*.
- If **neither binding arm both clears P11 and beats benchmark**, with adequate power → **EVIDENCE_AGAINST**:
  removing the cap/initial-stop from the trailing model is not a lever on the benchmark favourable geometry; a
  measured-negative characterization. Cross-check EXP-055 (move available) and EXP-057 (`/ADV-NONE` beat 1:1
  under the cap) — if the move is available and removing the stop helped *capped* but uncapping does not, the
  binding constraint is elsewhere; routed to G2.
- If **fewer than the P11 quorum of cells reach ≥30 qualifying events** on the binding arms because uncapped
  `DATA_CENSORED` depleted counts, no correctness failure → **INCONCLUSIVE (power-limited)**; disclose the
  separated censoring, never default to a ratio. This is a **materially likely** outcome and is a legitimate
  finding (the uncapped model cannot be powered on TRAIN history), not a failure to report.
- If **any invariant (Step 13) fails** → **SUBSTRATE/METHOD_DEFECT**; fix and re-run before any reading.
- The **separated `DATA_CENSORED` disclosure gates interpretation of the vs-BENCH contrast**: a positive
  contrast on a heavily-censored arm describes only the uncensored (typically shorter, earlier-resolving)
  subpopulation and must be reported with the censoring share, never generalised to the full conditioned set.

---

## Implementation Safety Constraints (for `experiment-developer`)

- **Temporal ordering / causality:** all alignment by `CloseTime`, never bar index across the primary ZigZag,
  secondary ZigZag, HA, and real-bar views. The uncapped scan reads only bars with index `> entry_idx` and
  `CloseTime ≤ train_end_ts`; the lazy stop uses only `ConfirmIdx ≤ i`.
- **Do NOT vectorize the uncapped resolver (Step 5).** It is an explicit bounded sequential loop; its
  causal/streaming semantics are the object under test. The window is `[entry+1, last_train_idx]` with early
  termination on stop fill / all legs closed.
- **Do NOT materialize a dense per-bar stop array for the uncapped arms** — compute the stop lazily via an
  advancing secondary-confirmation pointer. The dense `build_active_stops` is reused **only** for the capped
  siblings (where `width ≈ 6`).
- **Do NOT change the behaviour of `resolve_legs` / `build_active_stops` / `_scan_event`** — add the new
  uncapped entry point alongside; EXP-059's frozen results depend on the existing functions (and BENCH
  reproduction, invariant i, requires them unchanged). *(Post-review F04 remediation:* `_scan_event` /
  `resolve_legs` and `resolve_path_ordered` / `_scan_path` were extended with an **additive** measured
  exit-offset return / optional out-param so every arm reports its true holding duration; classes,
  prices, and all downstream metrics are byte-identical whether or not the new argument is supplied, and
  the frozen EXP-049/053–059 callers — which unpack the unchanged 2-tuples — are unaffected. The exact
  post-fix source is pinned by `resolver_source_sha256` in `run_metadata.json`.)*
- **Denominators / zero-baseline:** a cell with `<30` qualifying events for an arm is NOT_VIABLE-by-power
  (non-reportable), never an undefined/infinite ratio; `DATA_CENSORED`/warmup excluded-with-record, disclosed
  (uncapped censoring tallied separately).
- **Real prices only:** every exit price is real-bar OHLC; HA candles only detect the harami. No HA price in
  any metric.
- **Bounded memory + progress:** `tqdm` over the 99-cell grid; do not retain all domain frames or all bootstrap
  draws (`BOOT_BATCH` batching as in `xen.expectancy`); per-cell bounded. Note the uncapped per-event scan is
  `O(last_train_idx − entry_idx)` — the event loop per cell is materially slower than EXP-059; budget runtime.
- **Determinism:** fixed seed; two full passes byte-identical (Step 13). No output directory creation at import
  time; helper functions return data (no helper-level prints); concise orchestration logging only.
- **No safe-optimization that changes membership/order/denominators:** leg/stop resolution order, the P15 path,
  the qualifying rule, the uncapped window bound, and the regime-cluster bootstrap block construction are fixed.

---

## Complexity Check

- **Statistical methods: 4 / 4** — (1) moving-block bootstrap median CI on an arm's `E_cell` per cell; (2)
  paired-median contrast CI (used for both the binding vs-BENCH contrast and the disclosed cap-isolation
  contrast — same method, different arm pair); (3) arm − baseline contrast CI; (1) re-applied to each P13
  baseline median. Applied across the 5-arm set (a parameterised set over one experiment, **not** new methods
  per arm) — identical method family to EXP-056/057/058/059.
- **Visualisations: 5 / 5** (listed above).
- **New code modules: 0 / 0** — extend the existing `xen.position_exits` with a **new uncapped entry point**
  (`resolve_legs_uncapped` + lazy active-stop helper); the existing resolvers, the benchmark resolver, fills,
  realised returns, qualifying mask, median/contrast bootstraps, ZigZag, harami, strong-move, confirmation
  indices, and in-progress state are reused unchanged.

---

## Data-View Comparison Considerations

- **Cross-view alignment:** primary ZigZag, secondary ZigZag, HA candles, and real bars align by `CloseTime`.
  The conditioned harami population must reconcile **exactly** with EXP-053 (invariant ii); different exit arms
  produce different *qualifying* counts (uncapped censoring/warmup), which is expected and disclosed, but the
  underlying signal set is identical.
- **Event-count differences:** the uncapped arms exclude (a) events with no prior secondary-ZigZag confirmation
  history (warmup) and (b) events whose unbounded window reaches the TRAIN edge before the trailing stop fills
  (`DATA_CENSORED`). The latter is the dominant, novel depletion vs EXP-059 and is tallied separately. Compose
  only over cells reaching ≥30.
- **Real-price discipline:** all P&L/excursion on `RealOpen/High/Low/Close`; HA only for detection.

---

## Limitations (predeclared)

- **Uncapped windows deplete late-TRAIN events.** Events whose trailing window cannot complete before
  `train_end_ts` are `DATA_CENSORED`. On shallow-history or late-clustered cells this can push qualifying
  counts below 30, making the binding arms NOT_VIABLE-by-power — an INCONCLUSIVE outcome that is a genuine
  property of the uncapped model on the available TRAIN slice, not a defect. Disclosed per cell, separately
  from capped censoring.
- **The vs-BENCH contrast is on the uncensored common subset.** It cannot speak to the censored
  (typically longest-running) events; a positive contrast describes only the subpopulation both arms resolve.
- **No initial stop means early adverse excursions are unbounded** until the first secondary confirmation —
  expected to widen the per-event return distribution (more fat-tailed), which is exactly why the **median**
  endpoint (P14) is binding; the mean is disclosed.
- **`ATR_MULT_TRAIL = 0.5` is the frozen P18 default**; its sensitivity (the registered `/THIRD-TIME`-analog
  grid) is out of this scope. Only V2A is paired with the uncapped trailing (the simplest broad EXP-059
  performer, no reversal-event leg → no `bench_N` dependence); other partial schemes are out of scope.
- **Gross only**; the cost model enters only at a future tradability screen of a registered candidate branch.
- Standard moving-block bootstrap caveats (approximate within-cell stationarity) apply, mitigated by the block
  construction; no stronger statistical claim is made.
