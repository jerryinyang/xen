# Analysis Plan: Experiment EXP-049

**Phase 014-A · `CF-HA-HARAMI-001` / HYP-002 · 3-Barrier Capture Readiness & Gross
Capture Rate.** TRAIN-only, gross, exit-agnostic; 0 candidate slots, 0 TEST reads.
This plan operationalizes the approved `scope.md` and changes none of its frozen
decisions (ZigZag-confirmation anchor; both favourable geometries with G1
distance-based primary / G2 retracement-level secondary; conservative same-bar
double-touch → ADVERSE; P4 adaptive time cap; P5 `LOOKBACK=1`; P12 viability;
P11 composition).

## Objective

For each EXP-048-READY cell (instrument × domain), measure whether the 3-barrier
capture system can be built **deterministically and causally**, and estimate the
per-cell gross favourable-before-adverse capture rate
`r = P(fav before adv | resolved)` under the predeclared default barriers, with a
serial-dependence-aware interval so the P12 viability rule and P11 composition can
be applied **as a mechanical readout** (the design §10 G1 routing adjudication is
checkpoint desk work, not declared here).

The only market-quantity null is the **symmetric-barrier zero-edge reference
`r = 0.50`** (P3's 1:1 R:R makes fav and adv equidistant, so a path with no
directional drift resolves either way with probability 0.50). Viability asks
whether `r` is materially and reliably above 0.50.

## Data, ordering, and exclusions (binding)

- Real domain OHLC only (5m strict; 15m/30m/1h/2h/4h at `min_coverage=0.90`),
  rebuilt per cell exactly as EXP-048. The HA harami detector is **not** used.
- Order everything by `CloseTime`; never align by bar index. The capture event is
  the `xen.zigzag` confirmed move; entry index = `ConfirmIdx`.
- TRAIN-only (first 49% by the F01 file-order prefix); nested TEST and the
  final-30% holdout are never read (metadata + TRAIN prefix only). Forward
  resolution windows are fenced to `CloseTime ≤ train_end_ts`.
- Cell membership = EXP-048 **READY ∪ READY_FLAGGED** (hard precondition:
  EXP-048 READINESS_DELIVERED + audit PASS). Excluded cells carry their EXP-048
  status forward, unmeasured.

## Methodology

### Step 1 — Barrier construction (causal) and forward resolution

- **Method:** Deterministic per-event construction from `xen.zigzag` output, then a
  bounded first-touch scan on real `High`/`Low` over the P4 window. New module
  `xen/capture_barriers.py`.
- **Why sufficient:** The endpoint is a counting outcome (which barrier is touched
  first); no model is needed. First-touch on OHLC is the standard triple-barrier
  evaluation.
- **Simpler alternative considered:** Close-only crossing (ignore intrabar
  High/Low). Rejected — it ignores realized intrabar excursions and would
  understate both fav and adv hits; OHLC touch is the faithful, conservative read.
- **Per event (both geometries G1, G2 built in one shared scan):**
  - `C = ConfirmClose`, `d = Direction`, `S = StartPrice`, `E = EndPrice`,
    `M = |E − S|` (exclude `M = 0`, record), `rd = −d`.
  - **G1 (primary):** `fav_dist = 0.50·M`; `fav = C + rd·fav_dist`;
    `adv = C − rd·fav_dist`.
  - **G2 (secondary):** `level = E − d·0.50·M`; `fav_dist = rd·(level − C)`;
    **degenerate if `fav_dist ≤ 0`** → exclude from G2, record; else `fav = level`,
    `adv = C − rd·fav_dist`.
  - **P4 cap:** `N = max(6, round(1.5·median(duration_bars of trailing 20 moves
    confirmed strictly before this event)))`; **< 5 trailing moves → warmup-excluded**
    (no barrier, record). `duration_bars(move_i) = ConfirmIdx_i − ConfirmIdx_{i−1}`.
  - **Resolution window:** `i ∈ [ConfirmIdx+1, min(ConfirmIdx+N, train_last_idx)]`.
    First bar with `fav_hit`/`adv_hit` resolves; **same-bar both → ADV**
    (conservative). Class ∈ {FAV, ADV, TIMECAP, DATA_CENSORED}. `TIMECAP` =
    neither by `N`; `DATA_CENSORED` = window truncated by `train_last_idx` before
    `N` and before any hit.
- **Assumptions:** none distributional. Causality holds by construction (all
  thresholds from moves confirmed ≤ event; window strictly after entry, fenced to
  TRAIN). The first-touch loop is genuinely sequential within an event window and
  must stay an explicit bounded loop (a few hundred events/cell) — vectorize only
  loading/aggregation/summary.
- **Expected output:** per-event records (class, geometry distances, `N`, flags)
  and per-cell tallies `FAV/ADV/TIMECAP/DATA_CENSORED/warmup_excluded/
  g2_degenerate_excluded` for both geometries.

### Step 2 — Per-cell capture rate `r` and denominators (descriptive)

- **Method:** `r = FAV / (FAV + ADV)` over **resolved** events, per cell per
  geometry. `resolved = FAV + ADV`.
- **Zero-baseline / power:** `resolved < 30` → **NOT_VIABLE-by-power**
  (non-reportable for routing); `resolved = 0` → NOT_VIABLE-by-power, never `0/0`.
- **Disclosed secondaries (never binding):** `fav_all = FAV / defined`
  (defined = events with a built barrier); `timecap_frac = TIMECAP / defined`;
  `datatrunc_frac = DATA_CENSORED / defined`; plus `warmup_excluded` and (G2)
  `g2_degenerate_excluded` counts/fractions. Also report per cell: confirmed-move
  count, median/`IQR` of `N_event`, and FAV/ADV split.
- **Expected output:** `capture_rate_map.csv` (G1) + `capture_rate_secondary.csv`
  (G2) + `censoring_disclosure.csv`.

### Step 3 — Regime-clustered block bootstrap CI for the proportion `r` (the one inferential method)

`r` is a **proportion of a serially dependent binary sequence**, not a median, so
EXP-047 `move_size.py` median/i.i.d. bootstrap helpers do **not** apply to the
binding CI (they may be reused only for incidental descriptive SEs). Sequential
ZigZag moves alternate direction and their forward windows overlap (an event's
`N`-bar window can extend past the next confirmation), and outcomes share
volatility/regime persistence — an i.i.d. event bootstrap would understate
uncertainty. We therefore use a **moving-block bootstrap over the
confirmation-time-ordered event sequence** — the "regime-clustered" bootstrap of
P12, where the clustering unit is the confirmed move (one regime) and contiguous
blocks preserve dependence across adjacent regimes.

- **Method:** Moving-block bootstrap (MBB) of `r`, per cell per geometry.
  1. Take the cell's **full ordered sequence of events that have a built barrier**
     (length `m = defined`), each labelled `FAV` / `ADV` / `UNRESOLVED`
     (TIMECAP ∪ DATA_CENSORED). Blocking the full sequence (not just the resolved
     subsequence) jointly propagates outcome **and** resolution-status dependence
     (e.g., low-vol stretches that cluster TIMECAPs widen the interval honestly).
  2. **Block length** (frozen rule, no post-hoc choice): `b = max(1,
     round(m**(1/3)))` — the standard MBB rate for a sample-mean functional.
  3. Draw `ceil(m / b)` blocks, each a contiguous run of `b` consecutive events
     with a uniformly random start in `[0, m−b]` (last block truncated so the
     resample length is exactly `m`). Compute `r* = FAV* / (FAV* + ADV*)`.
  4. **Degenerate resample** (`FAV*+ADV* = 0`): discard and redraw (bounded
     attempts); expected count ≈ 0 given `resolved ≥ 30`. If the degenerate
     fraction exceeds 0.1 %, record it (a power signal, not a silent fix).
  5. `N_BOOT = 10_000`; per-cell `np.random.default_rng` seeded deterministically
     from a fixed base seed spawned by cell index (independent, reproducible).
  6. **One-sided 95 % `CI_low` = 5th percentile of `{r*}`** (percentile method —
     simplest sufficient, non-parametric, consistent with the frozen descriptive
     bootstrap layer; bounded support `[0,1]` makes BCa unnecessary). Also store
     the two-sided `[2.5th, 97.5th]` for disclosure; the **binding** quantity is
     the one-sided `CI_low`.
- **Why this method / simpler alternative considered:** A plain i.i.d. bootstrap of
  the resolved binaries (or a Wald/normal-approx CI on a proportion) is simpler but
  **under-propagates serial dependence** → optimistic `CI_low`, biasing a binding
  routing decision toward false VIABLE. MBB is the minimal robust upgrade. A
  resolved-subsequence-only block bootstrap was considered and rejected: it fixes
  the denominator and discards resolution-status variability. No analytical
  (binomial) CI is used — it assumes i.i.d. Bernoulli, which is violated.
- **Assumptions:** approximate stationarity *within a cell's TRAIN span* over the
  block scale (weak; MBB is robust to moderate non-stationarity and the cap on
  block length keeps blocks local). No normality, no independence.
- **Expected output:** per cell per geometry `r, ci_low_1s, ci_lo_2s, ci_hi_2s,
  resolved, n_boot_degenerate, block_len`.

### Step 4 — Determinism & causality invariant batteries (validation, not a test)

- **Determinism:** full second pass (re-aggregate, re-run ZigZag, rebuild barriers,
  re-resolve, identical seeds) → per-cell records and per-event class tables must be
  **frame-identical**.
- **Causality / fence battery (counts, all must be 0):** every reference/trailing
  move `ConfirmTime ≤` event `ConfirmTime`; `N_event ≥ 6`; no NaN in barrier
  fields; `M > 0`; warmup events carry no barrier (not silently capped); every
  evaluated forward bar `CloseTime ≤ train_end_ts`; G1 `fav_dist > 0` always.
- **BARRIER_REFUTED rule (predeclared, systematic-defect gate):** **non-determinism
  on any cell**, OR a causality/TRAIN-fence invariant violated on **≥ 3
  instruments** → halt 014-A pending fix. Otherwise CAPTURE_READINESS_DELIVERED.

### Step 5 — Viability and composition readout (mechanical; not the gate)

- **VIABLE cell (P12, primary G1):** `r ≥ 0.55` **and** `ci_low_1s > 0.50`
  **and** `resolved ≥ 30`. Per-cell status ∈ {VIABLE, BELOW_R (r<0.55),
  CI_SPANS_050 (ci_low_1s ≤ 0.50), NOT_VIABLE_BY_POWER (resolved<30),
  EXCLUDED (not EXP-048-READY)}.
- **Composition (P11):** `n_viable` cells and distinct instruments among them;
  `composition_met = (n_viable ≥ 5) ∧ (n_instruments ≥ 3)`, computed on G1
  (binding readout) and on G2 (parallel, disclosed, non-binding).
- **Sensitivity disclosure (non-binding, EXP-047 convention):** would composition
  be met at relaxed bars `(≥4 cells/≥2 instr)` and `(≥3 cells/≥2 instr)`, and at
  `r ≥ 0.52`? Informs robustness; the binding rule stays P12/P11.
- **Expected output:** `composition_readout.json` (G1 + G2 + sensitivity).

## Visualisations (4 / 4 — fixed by scope)

1. **Primary G1 capture-rate `r` heatmap** (17×6) — annotated `r`; non-READY /
   NOT_VIABLE-by-power cells masked/greyed. Shows where capture geometry favours
   the reversal and the 0.50 reference.
2. **VIABLE-status heatmap** (categorical: VIABLE / BELOW_R / CI_SPANS_050 /
   NOT_VIABLE_BY_POWER / EXCLUDED) — the P12 map at a glance.
3. **Resolved-event-count heatmap** (17×6) — power context; reads the 30-event
   floor directly.
4. **Unresolved-fraction heatmap** (`timecap_frac + datatrunc_frac`, 17×6) — how
   much the adaptive cap / TRAIN edge censors per cell (P4 censoring disclosure).

Secondary G2 `r`, all censoring breakdowns, warmup/degenerate counts, and the
sensitivity readout go to CSV/JSON, not extra plots.

## Interpretation Guide (pre-registered; maps readout → design §10 without self-adjudicating)

- **If** barrier batteries are clean (no BARRIER_REFUTED) **and** G1
  `composition_met` is **true** (≥5 VIABLE cells over ≥3 instruments): the capture
  readout is **consistent with design §10 PROCEED_TO_SCREEN leg (b)** — capture
  geometry viable. The experiment reports this as the readout; the **G1 desk
  adjudication** (combining EXP-048 readiness leg (a) and the future 014-B leg (c))
  makes the routing call. Do **not** self-declare PROCEED.
- **If** batteries clean **and** G1 `composition_met` is **false**: readout is
  **consistent with CHARACTERISED_NOT_VIABLE on the capture leg** (the AVWAP
  failure mode in new dress — substrate real, capture geometry not viable). Again,
  desk adjudication, not self-declared.
- **If** BARRIER_REFUTED fires: **SUBSTRATE_REFUTED-analog** — a primitive/aggregation
  defect; halt and fix before any further 014-A capture reads.
- **If** most cells are NOT_VIABLE_BY_POWER (`resolved < 30`): **INCONCLUSIVE on
  power**, not a capture verdict; record the realized resolved counts (a new scope
  would be needed to power them, e.g., longer history or pooled domains).
- **G1 vs G2 disagreement:** if G1 and G2 composition readouts diverge materially,
  flag for desk attention as a geometry-definition sensitivity (non-binding;
  G1 is the predeclared primary). Agreement strengthens the readout.
- **Effect-size honesty:** report `r` with `ci_low_1s` and `resolved` for every
  cell; never read a cell VIABLE on `r ≥ 0.55` alone without the CI and the
  30-event floor; a high `r` on `resolved = 31` with `ci_low_1s` barely above 0.50
  is a weak VIABLE and must be described as such.

## Safety constraints for `experiment-developer`

- **Timestamp ordering:** all slicing/fencing by `CloseTime`; assert TRAIN slice
  is sorted; never sort/collect the full file (F01 prefix loader, EXP-048 pattern).
- **Causality:** trailing-move window and reference move must use only confirmations
  strictly before / at the event; forward window strictly after `ConfirmIdx` and
  `≤ train_end_ts`. No look-ahead, no TEST/holdout read.
- **Denominators / zero-baseline:** `resolved` is the binding denominator;
  `resolved < 30` → NOT_VIABLE_BY_POWER (never `0/0`); `defined` is the secondary
  denominator; emit explicit flags, never silent NaN.
- **Sequential vs vectorized:** the first-touch resolution loop and the ZigZag state
  machine stay explicit bounded loops (causal semantics under test); vectorize only
  loading, aggregation, per-cell summary, and the bootstrap resampling index math.
- **Bootstrap reproducibility:** `N_BOOT = 10_000`, frozen base seed, per-cell
  spawned RNG, deterministic block length `b = max(1, round(m**(1/3)))`; the
  determinism pass must reproduce identical CI bounds.
- **Progress / memory:** `tqdm` over the instrument/cell outer loop; per-cell
  bounded memory (do not retain all domain frames); plots built from collected
  per-cell summaries (no reloads).
- **No tuning:** nothing selected/frozen against EXP-049 output; G1 is the
  predeclared binding geometry; thresholds are P12/P11 verbatim.

## Complexity Check

- **Statistical tests:** 1 / 1 — the regime-clustered moving-block bootstrap CI for
  `r` (one method; applied per cell per geometry; the `r≥0.55` and `resolved≥30`
  conditions are descriptive gates, and `r=0.50` is a fixed reference, not extra
  tests).
- **Visualisations:** 4 / 4 — as listed.
- **New modules:** 1 / 1 — `python/src/xen/capture_barriers.py` (causal triple-barrier
  resolution + the block bootstrap of the proportion). `xen.zigzag`,
  `xen.bar_aggregator`, and EXP-047 `move_size.py` reused unchanged.
