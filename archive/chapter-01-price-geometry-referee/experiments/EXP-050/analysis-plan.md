# Analysis Plan: Experiment EXP-050

**Phase 014-A · `CF-HA-HARAMI-001` / HYP-003 · Harami-in-Context: Position-in-Move
vs Predeclared Baselines.** TRAIN-only, gross, descriptive; 0 candidate slots, 0
TEST reads. This plan operationalizes the approved `scope.md` and changes none of
its frozen decisions (pivot-tiling assignment; price-excursion position primary,
duration-fraction secondary; P9 near-exhaustion `pos ≥ 0.67` and `Δ ≥ 0.10`
materiality; random baseline binding, MA(20,50) segmentation disclosed; P11
composition; `RealClose` signal price; all haramis pooled, no `/BARCFG`).

## Objective

For each EXP-048-READY cell (instrument × domain), determine whether every HA
harami can be placed **deterministically and look-ahead-safely** within its
containing confirmed ZigZag move, and measure the per-cell **final-third rate**
`FT = P(pos ≥ 0.67)` of harami positions (price-excursion) against the **random
matched-count baseline** `FT_rand` (binding) and the **MA(20,50)
alternative-segmentation baseline** (disclosed), so the P9 materiality rule
(`Δ = FT − FT_rand ≥ 0.10` ∧ assigned ≥ 30) and P11 composition (≥ 5 cells over
≥ 3 instruments) can be applied as a **mechanical readout** (the design §10 G1
adjudication is checkpoint desk work, not declared here).

The only reference quantity is the **direction-matched random-timing baseline
`FT_rand`** — the final-third rate a randomly-timed, direction-composition-matched
event would attain inside the same confirmed moves. Materiality asks whether harami
timing concentrates near exhaustion **above** that random-timing reference by the
predeclared 10 pp margin.

## Data, ordering, and exclusions (binding)

- Real domain OHLC (5m strict; 15m/30m/1h/2h/4h at `min_coverage=0.90`), rebuilt
  per cell exactly as EXP-048/EXP-049. The harami detector runs on HA candles of
  the same real domain bars (detection only); the HA frame's `RealClose` supplies
  the signal price. **No metric uses HA prices.**
- Order everything by `CloseTime`; never align by bar index across views. The
  signal event is the `xen.ha_harami` harami at `HA0Time`; the move segmentation is
  the `xen.zigzag` confirmed-move sequence.
- TRAIN-only (first 49 % by the F01 file-order prefix); nested TEST and the
  final-30 % holdout are never read (metadata + TRAIN prefix only). All harami
  `HA0Time`, move `ConfirmTime`, and eligible in-move bars are fenced to
  `CloseTime ≤ train_end_ts`.
- Cell membership = EXP-048 **READY ∪ READY_FLAGGED** (99 cells; hard precondition:
  EXP-048 READINESS_DELIVERED + audit PASS, satisfied). The 3 COVERAGE_EXCLUDED
  cells carry their EXP-048 status forward, unmeasured.

## Position-in-move metric (price excursion, shared definition)

For any real domain bar at time `t` with real `Close = P`, assigned under pivot
tiling to confirmed move `i` (`StartTime_i < t ≤ EndTime_i`, direction `d_i`,
`StartPrice S_i`, `EndPrice E_i`):

```
pos(t) = (P − S_i) / (E_i − S_i)
```

The denominator `(E_i − S_i)` carries the move's sign, so `pos` is direction-signed
for up- and down-moves alike; a degenerate move `E_i = S_i` is excluded with record.
**Near-exhaustion (P9):** `pos ≥ 0.67`. A harami's `pos` equals the `pos` of its own
domain bar (signal price `= RealClose = Close` at `HA0Time`), so harami positions
and the random in-move baseline are computed on the **identical** metric and price —
apples-to-apples by construction. `pos` may fall slightly outside `[0, 1]` (intrabar
overshoot of the close past a pivot); it is reported unclipped and only thresholded
at 0.67.

## Methodology

### Step 1 — Per-cell construction (deterministic, causal) and assignment

- **Method:** Frozen-generator construction + a vectorized interval-join assignment.
  Per cell: build real domain bars (`xen.bar_aggregator`), fence to TRAIN; generate
  HA candles (`xen.heiken_ashi_generator`) and detect haramis (`xen.ha_harami`,
  frozen); run `xen.zigzag.generate_zigzag(atr_period=14, atr_mult=1.0)` (frozen).
- **Assignment (pivot tiling):** assign each harami `HA0Time` to the confirmed move
  with `StartTime_i < HA0Time ≤ EndTime_i`. Implement as a `join_asof` **forward** on
  `EndTime` (smallest `EndTime ≥ HA0Time`) followed by a `StartTime < HA0Time`
  guard — exact under the contiguous pivot tiling (`EndTime_{i−1} = StartTime_i`).
  Haramis with no forward match (after the last confirmed pivot) are **forming-tail
  excluded**; haramis failing the `StartTime` guard (before the first pivot) are
  **warmup excluded**; haramis whose containing move is degenerate (`E_i = S_i`) are
  **degenerate excluded**. All three exclusions are counted/disclosed, never
  defaulted.
- **Why sufficient:** Assignment + `pos` is a deterministic geometric computation on
  a **precomputed completed segmentation**; no model is needed. The interval-join is
  causally inert (it groups completed moves; it is not a live signal — see the
  descriptive-allowance note below). The genuinely sequential logic lives inside the
  frozen `xen.zigzag` state machine and the one-row-shift `xen.ha_harami` detector,
  which are not re-implemented here.
- **Simpler alternative considered:** a per-harami Python search loop over moves —
  rejected as unnecessary (the vectorized interval-join is exact and faster); the
  ZigZag/HA generation stays sequential inside the frozen modules.
- **Descriptive-allowance note (binding):** `pos` uses the move's terminal pivot
  `E_i`, which is future information relative to a mid-move harami. This is permitted
  **only** as the predeclared, non-tradable descriptive characterization of
  **completed** moves (P9 "completed-move grouping"); **no** trading, signal,
  capture, or P&L decision consumes `pos` or any unconfirmed pivot. The same
  allowance covers the random baseline's in-move bars and the MA-segmentation
  scoring.
- **Expected output:** per-harami records (`HA0Time`, direction `d_i`, `pos`,
  `dur_pos`, final-third flags, exclusion class) and per-cell tallies
  (`n_assigned`, `n_warmup_excl`, `n_formingtail_excl`, `n_degenerate_excl`,
  `n_haramis_total`).

### Step 2 — Per-cell final-third rate `FT` and the exact random baseline `FT_rand`

- **Method (FT):** `FT = (# assigned haramis with pos ≥ 0.67) / n_assigned`, per
  cell. Denominator = **assigned** haramis only.
- **Method (FT_rand — exact, deterministic):** the direction-stratified population
  in-move final-third rate. Build the **eligible in-move bar population**: every
  TRAIN domain bar assigned (same pivot-tiling interval-join) to a non-degenerate
  confirmed move, labelled by its move direction `d` and its `pos`. For each
  direction `d`, let `q_d = P(pos ≥ 0.67 | in-move bars of direction d)`. Then

  ```
  FT_rand = Σ_d  w_d · q_d ,   w_d = (# assigned haramis with direction d) / n_assigned
  ```

  i.e. the expected final-third rate of a random, direction-composition-matched
  event placed uniformly over in-move bars — the **closed-form R→∞ limit** of the
  scope's matched-count draw, computed exactly to remove Monte-Carlo noise from a
  governance-binding baseline (eligible in-move bars number in the thousands per
  cell, so the population rate is essentially noise-free; a finite matched-count
  draw would only add sampling noise to a binding number — see *Reconciliation*).
  The harami bars are **included** in the eligible population (a randomly-timed event
  could land on any in-move bar); this is the conservative choice.
- **Gap:** `Δ = FT − FT_rand` (point). Zero-edge reference: under random timing
  `Δ = 0`.
- **Zero-baseline / power:** `n_assigned < 30` → **NOT_REPORTABLE-by-power**
  (non-reportable for the P11 numerator; `FT` still reported descriptively but flagged,
  never `0/0`); `n_assigned = 0` → `FT = null`, NOT_REPORTABLE, never `0/0`. A
  direction with haramis always has ≥ 1 eligible in-move bar (the harami bars
  themselves), so `q_d` is defined whenever `w_d > 0`.
- **Why sufficient / simpler alternative:** rates are the endpoint; an exact
  population baseline is the simplest noise-free reference. A single random draw was
  considered (scope sketch) and is superseded by its exact limit (tighter, seed-free
  binding number).
- **Expected output:** `final_third_rate_map.csv` (`FT, FT_rand, Δ, n_assigned`,
  direction split, `q_up`, `q_down`, `w_up`, `w_down`).

### Step 3 — Regime-clustered moving-block bootstrap CI on `Δ` (the one inferential method)

`FT` is a **proportion of a serially dependent binary sequence** (haramis cluster in
time; adjacent final-third indicators are dependent through shared volatility/trend
regime), exactly the EXP-049 situation. An i.i.d. event bootstrap would understate
uncertainty. We therefore use a **moving-block bootstrap (MBB) over the
`HA0Time`-ordered harami indicator sequence**, holding `FT_rand` fixed (a
low-variance population quantity). This is the "regime-clustered" resample the scope
calls for, reusing the EXP-049 MBB convention verbatim.

- **Method:** per **reportable** cell (`n_assigned ≥ 30`):
  1. Sequence `I_k = 1[pos_k ≥ 0.67]`, `k = 1…n` (`n = n_assigned`), ordered by
     `HA0Time`.
  2. **Block length** (frozen rule, no post-hoc choice): `b = max(1,
     round(n**(1/3)))` — the standard MBB rate for a sample-mean functional (`FT`
     is a mean of indicators).
  3. Draw `ceil(n/b)` contiguous blocks of `b` consecutive indicators, uniform start
     in `[0, n−b]`, last block truncated so the resample length is exactly `n`;
     `FT* = mean(I*)`; `Δ* = FT* − FT_rand`.
  4. `N_BOOT = 10_000`; per-cell `np.random.default_rng` spawned deterministically
     from a frozen base seed by global cell index (`SeedSequence(BASE_SEED).spawn`,
     `BASE_SEED = 20260615`), independent and reproducible.
  5. **CI:** two-sided `[2.5th, 97.5th]` percentile of `{Δ*}` (disclosed) and the
     one-sided `ci_low_1s = 5th` percentile of `{Δ*}` (support for `Δ > 0`). The
     percentile method is sufficient (bounded `[0,1]` functional; consistent with the
     frozen descriptive bootstrap layer; BCa unnecessary).
- **Binding vs support (no goalpost move):** the **binding** materiality is the
  **point** rule `Δ ≥ 0.10 ∧ n_assigned ≥ 30` (D0 P9). The CI is **disclosed
  support only**: `ci_low_1s > 0` flags `Δ` reliably positive; `ci_low_1s > 0.10`
  flags `Δ` reliably above the materiality margin (a stronger disclosed tier). The CI
  adds **no** binding threshold beyond D0.
- **Why this method / simpler alternative considered:** a plain i.i.d. bootstrap of
  the harami binaries, or a Wald proportion CI, is simpler but **under-propagates
  serial dependence** → optimistic interval. A permutation test against random-timing
  labels was considered and is mathematically answered by `FT_rand` + the MBB CI
  (`ci_low_1s(Δ) > 0` is the "beyond chance" read); a separate permutation test would
  duplicate the inference and spend a second test. MBB is the minimal robust choice,
  consistent with EXP-049.
- **Assumptions:** approximate within-cell stationarity over the block scale (weak;
  MBB is robust to moderate non-stationarity; the cube-root block cap keeps blocks
  local). No normality, no independence.
- **Expected output:** per cell `ci_low_1s, ci_lo_2s, ci_hi_2s, block_len`, appended
  to `final_third_rate_map.csv`.

### Step 4 — Disclosed secondaries (point estimates only; no extra test)

All computed from the same per-cell records (no second bootstrap, no extra test):

- **MA(20,50) alternative segmentation (P13.2, disclosed):**
  `xen.referee_calibration.ma_crossover_positions(close, fast=20, slow=50)` on the
  cell's TRAIN real closes; a **regime/move** = a maximal contiguous run of constant
  non-zero position, `move_start/move_end` prices = `Close` at the run's first/last
  bar, direction = the run's sign. Re-score the **same** haramis under MA-regime
  pivot tiling → `FT_MA` (over MA-assigned haramis); `FT_MA_rand` (exact
  direction-matched population rate over in-MA-regime bars); `Δ_MA_vs_rand = FT_MA −
  FT_MA_rand` (the apples-to-apples robustness read: does the clustering survive an
  independent segmentation?) and `Δ_MA = FT − FT_MA` (the direct ZigZag-vs-MA rate
  difference the scope names). Haramis in a flat/warmup region or a degenerate MA
  regime are excluded with record. **Disclosed, non-binding.**
- **Duration-fraction position (P9 secondary):** `dur_pos = (idx(HA0Time) −
  idx(StartTime_i)) / (idx(EndTime_i) − idx(StartTime_i))` on domain-bar indices;
  `FT_dur = P(dur_pos ≥ 0.67)` and `Δ_dur = FT_dur − FT_dur_rand` (exact
  direction-matched in-move duration-fraction baseline). Disclosed.
- **Position distribution summary:** per-cell median and IQR of harami `pos`, and
  fixed-bin histogram counts (20 bins over `[−0.5, 1.5]`) for haramis and for the
  in-move baseline (bounded plot inputs, emitted from the analysis pass — no reload).
- **Excluded fractions:** `warmup`, `forming-tail`, `degenerate` counts/fractions
  (ZigZag and, separately, MA flat/degenerate).
- **Expected output:** `secondary_disclosure.csv`.

### Step 5 — Determinism & causality/assignment invariant batteries (validation, not a test)

- **Determinism:** a full second pass (re-aggregate, re-HA, re-detect, re-ZigZag,
  re-assign, recompute `FT/FT_rand`, re-run the MBB with the same spawned seeds) →
  per-cell records and per-event class tables must be **frame-identical**, including
  identical CI bounds.
- **Battery (counts, all must be 0):** (1) **detector self-check** —
  `ReducedOK == original-harami-predicate` on every harami row; (2) **assignment
  well-formedness** — every assigned harami maps to exactly one non-degenerate
  containing move, `pos` finite; exclusion classes are mutually exclusive and sum to
  `n_haramis_total`; (3) **causality / TRAIN fence** — every harami `HA0Time`, move
  `ConfirmTime`, and eligible in-move bar has `CloseTime ≤ train_end_ts`; the metric
  references only confirmed-move boundaries (descriptive allowance, declared); no row
  read beyond the TRAIN edge.
- **CONTEXT_REFUTED rule (predeclared, systematic-defect gate):** **non-determinism
  on any cell**, OR a battery (1)–(3) invariant violated on **≥ 3 instruments** →
  halt 014-A pending fix. Otherwise CONTEXT_CHARACTERISATION_DELIVERED.

### Step 6 — Materiality and composition readout (mechanical; not the gate)

- **Materially-clustered cell (P9, binding random baseline):** `clustered_binding =
  (Δ ≥ 0.10) ∧ (n_assigned ≥ 30)`. Per-cell status ∈ {CLUSTERED, NOT_CLUSTERED
  (Δ < 0.10), NOT_REPORTABLE_BY_POWER (n_assigned < 30), EXCLUDED (not
  EXP-048-READY)}.
- **Disclosed support tiers (non-binding):** `Δ>0 & ci_low_1s>0` (reliably positive);
  `clustered_binding & ci_low_1s>0.10` (reliably material).
- **Composition (P11):** `n_clustered` cells and distinct instruments among them;
  `composition_met = (n_clustered ≥ 5) ∧ (n_instruments ≥ 3)`, computed on the
  binding random baseline. Report in parallel (disclosed, non-binding): the
  composition under the stronger `ci_low_1s>0.10` tier, and the **MA-robustness
  composition** (cells with `clustered_binding` **and** `Δ_MA_vs_rand ≥ 0.10`).
- **Sensitivity disclosure (non-binding, EXP-049 convention):** would composition be
  met at `Δ ≥ 0.05` and `Δ ≥ 0.15`, and at relaxed `(≥4 cells/≥2 instr)`? Informs
  robustness; the binding rule stays P9/P11 verbatim.
- **Expected output:** `composition_readout.json` (binding + support tiers + MA
  robustness + sensitivity).

## Visualisations (4 / 4 — fixed by scope)

1. **Observed final-third-rate `FT` heatmap** (17×6) — annotated `FT`; non-READY and
   NOT_REPORTABLE-by-power cells masked/greyed. Shows where harami positions
   concentrate, against the per-cell random reference encoded in plot 2.
2. **Gap `Δ = FT − FT_rand` heatmap** (17×6) — diverging colormap centred at 0, the
   `Δ = 0.10` materiality contour highlighted; CLUSTERED cells marked. The P9 map at
   a glance.
3. **Pooled position-in-move distribution** — overlaid histograms of harami `pos`
   vs the in-move random baseline `pos` (pooled across reportable cells from the
   emitted fixed-bin counts; equal-weight-per-cell to avoid large-cell domination),
   with a vertical line at `pos = 0.67`. Shows whether harami mass shifts toward
   exhaustion relative to random timing.
4. **Assigned-harami-count heatmap** (17×6) — annotated `n_assigned`; reads the
   30-event reportability floor directly (power context). Excluded fractions →
   `secondary_disclosure.csv`.

`FT_MA`, `Δ_MA`, `Δ_MA_vs_rand`, duration-fraction, and all exclusion breakdowns go
to CSV/JSON, not extra plots.

## Interpretation Guide (pre-registered; maps readout → design §10 without self-adjudicating)

- **If** batteries are clean (no CONTEXT_REFUTED) **and** `composition_met` is
  **true** (≥ 5 CLUSTERED cells over ≥ 3 instruments on the binding random
  baseline): the readout is **consistent with harami timing concentrating near
  exhaustion above chance** — a positive input to combined-event registration
  (014-B). The experiment reports the readout; the **G1 desk adjudication** makes the
  routing call. Do **not** self-declare a family decision.
- **If** batteries clean **and** `composition_met` is **false**: readout is **harami
  timing not materially clustered near exhaustion vs random timing** — the
  "exhaustion" premise is weakened (the signal may fire broadly across the move). Desk
  adjudication, not self-declared.
- **MA-robustness:** if CLUSTERED cells also show `Δ_MA_vs_rand ≥ 0.10`, the
  clustering is a **property of harami timing** (survives independent segmentation);
  if `Δ_MA_vs_rand ≈ 0` while `Δ` is large, the clustering may be a **ZigZag
  segmentation artifact** — a binding caveat for the desk. Disclosed, non-binding.
- **If** CONTEXT_REFUTED fires: a primitive/assignment defect; halt and fix before
  any further 014-A characterization.
- **If** most cells are NOT_REPORTABLE_BY_POWER (`n_assigned < 30`): **INCONCLUSIVE
  on power** for those cells, not a clustering verdict; record realized counts (a new
  scope would be needed to power them).
- **Effect-size honesty:** report `FT, FT_rand, Δ, ci_low_1s, n_assigned` for every
  cell; never read CLUSTERED off `Δ ≥ 0.10` alone on `n_assigned = 30` with a CI
  spanning 0 — describe such a cell as weak/uncertain. Duration-fraction and
  price-excursion reads that disagree are flagged (the move's price vs time geometry
  differ).

## Safety constraints for `experiment-developer`

- **Timestamp ordering:** all slicing/fencing by `CloseTime`; assert the TRAIN slice
  is sorted; never sort/collect the full file (F01 prefix loader, EXP-048 pattern).
  Cross-view alignment (haramis ↔ moves ↔ MA regimes) by timestamp interval, never by
  bar index.
- **Causality / fence:** harami detection and ZigZag are the frozen modules (do not
  edit); the interval-join groups **completed** moves only (descriptive allowance,
  declared); every `HA0Time`/`ConfirmTime`/in-move bar `≤ train_end_ts`; no TEST or
  holdout read (metadata + TRAIN prefix only).
- **Denominators / zero-baseline:** `n_assigned` is the binding denominator;
  `n_assigned < 30` → NOT_REPORTABLE_BY_POWER (never `0/0`); exclusion classes are
  explicit flags that partition `n_haramis_total`; emit flags, never silent NaN.
- **Sequential vs vectorized:** the ZigZag state machine and the one-row-shift harami
  detector stay inside their frozen modules; the assignment interval-join, the
  baseline rate computation, the histogram binning, and the bootstrap **index math**
  are safe to vectorize. The MBB resample is index-based (no Python row loop over
  bars).
- **Bootstrap reproducibility:** `N_BOOT = 10_000`, frozen `BASE_SEED = 20260615`,
  per-cell RNG via `SeedSequence(BASE_SEED).spawn` by global cell index, block length
  `b = max(1, round(n**(1/3)))`; the determinism pass must reproduce identical CI
  bounds.
- **Progress / memory:** `tqdm` over the instrument/cell outer loop; per-cell bounded
  memory (do not retain all domain frames or all per-bar positions across cells — emit
  only per-cell scalars + fixed-bin histogram counts); all four plots built from the
  collected per-cell summaries (no reloads, no regeneration for plotting).
- **No tuning:** nothing selected/frozen against EXP-050 output; thresholds are P9/P11
  verbatim; the random baseline is binding, MA-segmentation is disclosed.

## Reconciliation with the scope's resample sketch (for governance)

The scope sketched `FT_rand` as the **mean of `R` fixed-seed matched-count draws**
and a "resample CI on `Δ`." This plan implements that intent **more precisely and
without weakening any decision**: (1) `FT_rand` is the **exact closed-form** of that
draw's `R→∞` limit (the direction-stratified population in-move rate), eliminating
Monte-Carlo noise from a governance-binding baseline; (2) the **CI on `Δ`** is the
serial-dependence-aware MBB of the harami indicator sequence (FT_rand held fixed),
consistent with EXP-049's established convention and statistically correct for a
proportion of a dependent binary series (an i.i.d. matched-count draw would
understate uncertainty). Both changes are pre-data-contact, tighten rather than
relax the read, and tune nothing against outcomes. The binding materiality remains
the D0 P9 point rule `Δ ≥ 0.10 ∧ n_assigned ≥ 30`.

## Complexity Check

- **Statistical tests:** 1 / 1 — the regime-clustered moving-block bootstrap CI on
  `Δ` (one method, per reportable cell). `FT`, `FT_rand`, `FT_MA`, `FT_MA_rand`,
  `FT_dur` are deterministic point computations; `Δ ≥ 0.10` and `n_assigned ≥ 30`
  are descriptive gates; `Δ = 0` is a fixed reference — none are additional tests.
- **Visualisations:** 4 / 4 — as listed.
- **New modules:** ≤ 1 / 1 — `python/src/xen/move_position.py` (causal pivot-tiling
  assignment + price-excursion/duration-fraction position; reusable in 014-B), or an
  experiment-local helper under `code/` if the developer judges it not yet reusable.
  `xen.zigzag`, `xen.ha_harami`, `xen.heiken_ashi_generator`, `xen.bar_aggregator`,
  `xen.referee_calibration.ma_crossover_positions` reused unchanged.
```
