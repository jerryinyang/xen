# Analysis Plan: Experiment EXP-055 — Long-Horizon Availability (Conditioned HA Harami, AVWAP-Analog Lifetime MFE/MAE)

## Objective

Characterise, gross and ATR-normalised, the **lifetime favourable excursion (MFE)** vs **adverse
excursion (MAE)** of the live `/STRONG`-conditioned HA harami over the **full reversal move** that
follows it (harami entry → end of reversal move M_b), per cell on the 99-cell member grid, and emit the
AVWAP-comparison fork: *move available + capture missing* (AVAILABILITY_GOOD, like AVWAP EXP-047) vs
*no available favourable move* (AVAILABILITY_POOR, worse than AVWAP). This is a **descriptive /
diagnostic** characterisation (HYP-008, P19) — there is **no edge claim**; the falsifiable sub-structure
is correctness (determinism, causality, EXP-053 population reconciliation), not a hypothesis test of an
edge. The experiment **emits** the readout; §8 routing is the single 014-B G2 desk adjudication (no
self-adjudication, mirroring EXP-054). TRAIN-only; 0 candidate slots; 0 TEST reads; holdouts sealed; all
metrics on real prices (`RealOpen/High/Low/Close`), never HA prices.

Restated readout question: *Does the conditioned harami's predicted reversal move offer a meaningful
favourable excursion (robustly above the 1.0-ATR reference line and above its own adverse excursion)
across a P11 quorum, or not?*

---

## Methodology

The pipeline composes frozen primitives; the only new code is a thin EXP-055 helper (the ≤1 module the
scope allows). All conditioning, ZigZag, harami, `/STRONG-HA`, confirmation-index, and matched-control
machinery is **reused**; the helper adds the end-of-M_b window, the ATR-normalised lifetime excursion,
a **median** moving-block bootstrap, and the mechanical readout.

### Step 0: Per-cell construction (deterministic, causal; not a statistical test)

- **Method**: Reuse `xen.bar_aggregator.aggregate_ohlc` (5m strict; 15m/30m/1h/2h/4h `min_coverage=0.90`),
  `xen.zigzag.generate_zigzag(bars, atr_period=14, atr_mult=1.0)` → confirmed moves;
  `xen.capture_barriers.confirm_indices(moves, bars)` → `confirm_idx`; `xen.heiken_ashi_generator` +
  `xen.ha_harami.detect_ha_harami` → harami entry bars (aligned to real bars by `CloseTime`);
  `xen.expectancy.live_in_progress_state` + `live_strong_stat` → the binding conditioned population
  (`defined ∧ retained_p75`), `rd`, `M_sofar`; `xen.strong_move.annotate_ha_impulse` → the `/STRONG-HA`
  disclosed arm; `xen.zigzag.wilder_atr(bars, 14)` → `ATR_entry` at each harami bar.
- **Why this method**: byte-identical reuse of the EXP-053 conditioned-signal construction guarantees the
  same population is measured (verified by the reconciliation gate, Step 5), so any availability finding
  is attributable to the lifetime window, not a re-derived signal.
- **Simpler alternative considered**: re-detect the signal locally — rejected; it risks population drift
  vs EXP-053 and duplicates audited code.
- **Assumptions**: the EXP-048 detector and EXP-053 conditioning are correct (already audited PASS). HA
  candles used for **detection only**; no HA price enters any metric.
- **Expected output**: per cell, an event table `{entry_idx, entry_time, entry_close C, rd, ATR_entry,
  regime_id, strong_stat_pass, strong_ha_pass, strong_mad_pass}`.

### Step 1: Lifetime window to the end of reversal move M_b (deterministic; not a test)

- **Method**: For each qualifying harami at entry bar `e`, `pos = np.searchsorted(confirm_idx, e,
  side="right")`; `c1 = confirm_idx[pos]` (ends the faded move M_a), `c2 = confirm_idx[pos+1]` (ends the
  reversal move M_b) — the **window end** (operator decision). Window = real bars `[e+1, c2]`. If
  `pos+1 ≥ confirm_idx.size` (M_b does not complete inside TRAIN), the event is **DATA_CENSORED** and
  excluded from all medians (disclosed as a count/fraction). Reuses the EXP-047 `move_size.lifetime_end`
  boundary logic, **extended by one confirmation index**.
- **Why this method**: the family predicts the reversal move M_b; measuring availability over M_b's full
  swing is the faithful AVWAP-analog (in EXP-047 the lifetime covered the move being traded). Using the
  retroactively-confirmed `c1`,`c2` is permitted here as a **descriptive completed-move grouping** (P19;
  family doc lines 139–143) — it is never a live entry/filter/barrier.
- **Simpler alternative considered**: window to `c1` only (end of M_a) — rejected by the operator and on
  methodology: it truncates the reversal swing and biases favourable MFE toward zero ("no move
  available" artifact). A fixed time-cap window — rejected: not the pivot-to-pivot read P19 specifies.
- **Assumptions**: ZigZag confirmations are monotone in index (guaranteed by the generator);
  `c2 > c1 > e`.
- **Expected output**: per event, `c2` and a `data_censored` flag; per cell, the censored count/fraction.

### Step 2: ATR-normalised lifetime MFE and MAE (deterministic; the metric, not a test)

- **Method**: Over `[e+1, c2]` on real OHLC, rd-aware:
  - `rd=+1`: `MFE = (max(High) − C)/ATR_entry`, `MAE = (C − min(Low))/ATR_entry`;
  - `rd=−1`: `MFE = (C − min(Low))/ATR_entry`, `MAE = (max(High) − C)/ATR_entry`;
  - both floored at `0.0` (standard excursion convention, as `move_size.excursions`). Derived per event:
    `MFE − MAE` (favourable-availability asymmetry, ATR units).
  - `ATR_entry` = Wilder ATR(14) at the harami entry bar `e` — the **same divisor as EXP-053** (P14), so
    excursions are directly comparable to EXP-053 expectancy.
- **Why this method**: max favourable/adverse excursion over the trade's natural lifetime is the
  canonical "how much move was available" measure (EXP-047 analog); ATR-normalisation makes cells
  comparable and matches the 014-B endpoint discipline. Adapts `move_size.excursions` (which returned
  log-bps `×10_000`) to divide by `ATR_entry` instead.
- **Simpler alternative considered**: log-bps excursions (EXP-047 units) — rejected for cross-cell
  comparability and consistency with the 014-B ATR endpoint. Close-to-close lifetime return — rejected:
  it measures *captured-at-pivot* return, not *available* excursion (the diagnostic question is
  availability).
- **Assumptions**: real `High`/`Low` bound the realised intrabar path (true for domain bars built from
  1-minute bars); excursions are a *ceiling* on capturable move (availability, not capture).
- **Expected output**: per event `{MFE, MAE, MFE−MAE}` (ATR units); per cell, the qualifying-event arrays.

### Step 3 (TEST 1 & 2): Regime-clustered moving-block bootstrap CI of the per-cell median MFE and median MAE

- **Method**: A **median** moving-block bootstrap that mirrors `xen.capture_barriers.block_bootstrap_ci`'s
  resampling but takes the **median of a continuous statistic** instead of a ratio. Order the cell's
  qualifying-event values by **entry time** (confirmation/clustering unit = the confirmed move the harami
  sits in, consistent with the P12 regime-clustered bootstrap). Let `m` = qualifying-event count, block
  length `b = max(1, round(m**(1/3)))`, `n_blocks = ceil(m/b)`. Each of `N_BOOT = 10_000` replicates draws
  `n_blocks` contiguous blocks (uniform start in `[0, m−b]`), concatenates, truncates to length `m`, and
  takes the **median**. Report `median`, one-sided 95% lower bound `ci_low_1s = percentile(5)`, and the
  two-sided `[2.5, 97.5]`. Fixed seed; batched (`BOOT_BATCH=2_000`) for bounded memory. Applied **once to
  MFE (TEST 1)** and **once to MAE (TEST 2)** per cell.
- **Why this method**: the per-event MFE distribution is heavy-tailed and serially clustered (consecutive
  haramis share regimes); the moving-block bootstrap is the programme's frozen non-parametric tool for
  exactly this dependence (no normality/i.i.d. assumption), and the median is robust to the fat tail
  (consistent with the P14 median endpoint). It reuses the audited resampling logic, swapping the
  statistic.
- **Simpler alternative considered**: i.i.d. percentile bootstrap (`move_size.bootstrap_median_se`) —
  rejected: ignores serial clustering, understating uncertainty. Bootstrap **SE** of the median (EXP-047)
  — rejected: a percentile CI_low is the binding quantity for the MOVE_AVAILABLE leg and avoids a normal
  SE approximation on a skewed statistic. Mann-Whitney/Wilcoxon — not applicable (one-sample location CI,
  not a two-group test).
- **Assumptions**: events within a cell are block-exchangeable under the moving-block scheme; clustering is
  adequately captured at the confirmed-move scale (the same assumption EXP-049/053 made). Heavy tails are
  handled by the median + percentile CI.
- **Expected output**: per cell `{median_MFE, mfe_ci_low_1s, mfe_ci_lo_2s, mfe_ci_hi_2s, block_len}` and the
  same for MAE; the `median_MFE` expressed as a **multiple of the 0.5-ATR and 1.0-ATR** reference lines.

### Step 4 (TEST 3 & 4): Baseline contrasts — matched-random and MA(20,50) segmentation (disclosed secondaries)

- **Method**: Two disclosed-secondary contrasts on the **median MFE**, signal − baseline:
  - **TEST 3 — matched-random**: the EXP-053 **matched-count random** construction (P13 "matched-count
    random timestamps, same cell/regime"): draw a count equal to the signal's qualifying `m` from the
    eligible in-progress pool (valid in-progress move, `M_sofar>0`, finite positive ATR, **excluding the
    binding `/STRONG-STAT` signal bars**); each drawn bar takes **its own** in-progress reversal `rd` and
    its lifetime MFE is measured over **its own** end-of-M_b window (the 2nd confirmation at/after the
    drawn bar) by the identical Step 1–2 procedure. (This is the directly comparable sibling-lead EXP-053
    baseline; `move_size.matched_controls`' regime-nearest-age selection is *not* used because its
    regime-end window is incompatible with the end-of-M_b lifetime definition — disclosed secondary,
    non-binding either way.)
  - **TEST 4 — MA(20,50) segmentation**: re-segment moves with the MA(20,50) substrate (EXP-050/053
    baseline), recompute the conditioned haramis' lifetime MFE under MA-defined `c2`.
  - For each, the contrast CI is a **moving-block bootstrap of the median difference** (independent
    block-resample of each population by its own confirmation order, `median(signal*) − median(base*)` per
    replicate, `N_BOOT=10_000`, fixed seed, percentile `ci_low_1s = percentile(5)`). "Signal exceeds
    baseline" iff contrast `ci_low_1s > 0`.
- **Why this method**: answers "is the favourable reversal move specific to the conditioned harami, or a
  generic regime property?" (matched-random, the direct EXP-047 anchor-vs-baseline analog) and "is
  availability ZigZag-specific?" (MA segmentation, the EXP-050 front-loading control). The median-diff
  moving-block bootstrap is the consistent non-parametric contrast.
- **Simpler alternative considered**: paired per-event difference vs the matched control set — rejected:
  controls are pooled (variable count per event) and the binding readout is the cell median, so an
  unpaired median-diff (the EXP-047 `bootstrap_median_diff_se` design, upgraded to block + percentile) is
  the faithful, simpler choice. These remain **disclosed secondaries**, never the binding availability leg.
- **Assumptions**: controls share the event's regime (enforced by `matched_controls`); independent
  block-resampling of the two populations is an acknowledged approximation given partial matching
  (disclosed). Cells with < `CONTROLS_MIN`-feasible controls contribute no contrast (disclosed).
- **Expected output**: per cell `{base_median_MFE, contrast_median, contrast_ci_low_1s, contrast_ci_2s}`
  for each baseline; a `signal_beats_baseline` flag per baseline.

### Step 5: Correctness gates (binding; not statistical tests)

- **Determinism**: a full second pass (re-aggregate → re-ZigZag → re-detect → re-condition → re-measure)
  reproduces every per-cell figure **frame-identically**; any mismatch → SUBSTRATE/METHOD_DEFECT.
- **Causality / window invariants**: `MFE ≥ 0`, `MAE ≥ 0`; for every non-censored event
  `e+1 ≤ c2 ≤ train_last_idx`, `c2 = confirm_idx[pos+1]` with `confirm_idx[pos] > e`; no event reads a bar
  with `CloseTime > train_end_ts`. Violation on ≥3 instruments → SUBSTRATE/METHOD_DEFECT.
- **EXP-053 population reconciliation**: the binding `/STRONG-STAT` conditioned-event set per cell (count +
  a `entry_idx/entry_time/rd` digest) matches EXP-053's conditioned population (same detector, filter,
  TRAIN fence). A mismatch is disclosed and resolved before the readout is trusted.

---

## Mechanical Readout (emitted; NOT self-adjudicated)

All gross, per-cell first, composed by **P11** (≥5 cells over ≥3 instruments). Power floor: a cell with
**< 30 qualifying (non-censored) events** is **NOT_VIABLE-by-power** — non-reportable for the
composition, disclosed, never an undefined ratio.

- **Qualifying-event population** (the denominator): events that (a) pass binding `/STRONG-STAT`
  (`defined ∧ retained_p75`) with a valid live in-progress move, (b) have `ATR_entry` defined
  (post-Wilder-warmup), and (c) are **not DATA_CENSORED** (M_b completes inside TRAIN). Warmup-excluded and
  DATA_CENSORED events are removed **before** the 30-event count and disclosed as counts/fractions — so a
  cell heavy in censored events can fall to NOT_VIABLE-by-power.
- **Per-cell `MOVE_AVAILABLE`** (mechanical, three legs, all required):
  1. **Power**: ≥ 30 qualifying events;
  2. **Availability vs reference**: median-MFE bootstrap `ci_low_1s > 1.0` (the upper reference line used
     as a **comparison threshold** on the median's lower bound — mirrors EXP-047 `leg2_floor`
     `median_mfe ≥ M×floor`; the reference value is **never subtracted** from any MFE, it only bounds the
     median from below);
  3. **Asymmetry**: `median_MFE > median_MAE` (favourable availability dominates adverse).
- **Family fork (descriptive label; routing is G2 only):**
  - **AVAILABILITY_GOOD** — `MOVE_AVAILABLE` clears P11. Reading: a meaningful favourable reversal move is
    available that the short-horizon benchmark capture (EXP-049/053) missed → the AVWAP situation; the
    014-B capture-geometry/exit surface (EXP-056–060) is justified.
  - **AVAILABILITY_POOR** — `MOVE_AVAILABLE` does not clear P11. Reading: no broadly-available favourable
    reversal move; closure is better-supported than for AVWAP — **but no closure inside 014-B** (G2 only).
  - **INCONCLUSIVE** — fewer than the P11 quorum of cells reach ≥30 qualifying events, no correctness
    failure (conditioning + the 2-confirmation window deplete counts).
  - **SUBSTRATE/METHOD_DEFECT** — any determinism/causality/reconciliation failure → fix before reporting.

The reference band stays "never subtracted" everywhere: the 0.5/1.0-ATR lines appear **only** (i) as a
lower-bound comparison for the median (leg 2) and (ii) as descriptive multiples (`median_MFE / 0.5`,
`median_MFE / 1.0`) on tables/plots — exactly EXP-047's "≈5–9× the floor" reporting. No excursion, no
median, no contrast is ever reduced by the reference value; all returns remain gross.

---

## Visualisations (4 / 4)

1. **Per-cell median MFE & MAE forest plot** (one row per reportable cell; MFE and MAE medians with
   one-sided 95% CIs), with vertical **0.5-ATR and 1.0-ATR reference lines** — shows, per cell, whether the
   favourable excursion robustly clears the band and exceeds adverse. Answers the MOVE_AVAILABLE leg
   visually.
2. **Median `MFE − MAE` asymmetry heatmap** (17 instruments × 6 domains; NOT_VIABLE-by-power and
   COVERAGE_EXCLUDED cells greyed) — shows where favourable availability dominates adverse across the grid.
3. **Pooled MFE and MAE distributions** (histograms/KDE over all qualifying events, or a representative
   powered subset), with the 0.5/1.0-ATR reference lines and median markers — shows distribution shape
   (heavy tail justifying the median) and the bulk vs the band.
4. **`MOVE_AVAILABLE` / P11 composition map** (17 × 6 status grid: MOVE_AVAILABLE / not-available /
   NOT_VIABLE-by-power / COVERAGE_EXCLUDED), with the cell and instrument counts and the AVAILABILITY_*
   fork annotated — the headline deliverable.

Baseline contrasts (`/STRONG-HA`, matched-random, MA-segmentation, MAD arm), reference-line multiples, and
censoring counts go to **CSV**, not extra plots.

---

## Interpretation Guide (pre-registered; criteria fixed before results)

- If **`MOVE_AVAILABLE` clears P11** (≥5 cells, ≥3 instruments) → **AVAILABILITY_GOOD**: the conditioned
  harami's reversal move offers a robust favourable excursion (median MFE lower bound > 1.0 ATR and >
  MAE) that the short-horizon capture missed — the AVWAP "available move, missing capture" situation. This
  *motivates* the remaining 014-B capture-geometry/exit experiments; it is **not** an edge or tradability
  claim (gross, availability is a ceiling on capture).
- If **`MOVE_AVAILABLE` fails P11** with adequate power → **AVAILABILITY_POOR**: the favourable reversal
  excursion does not robustly clear the band and/or does not exceed adverse across the grid — worse than
  AVWAP. This *strengthens* the eventual closure case but **decides nothing inside 014-B** (the full
  surface is measured first; G2 adjudicates).
- If **fewer than the P11 quorum of cells reach ≥30 qualifying events** → **INCONCLUSIVE** (power-limited
  by conditioning + the 2-confirmation window); disclose the censored/warmup attrition, recommend a
  follow-up scope if availability remains the open question.
- **Matched-random contrast** (disclosed): if signal median MFE exceeds matched-random (contrast
  `ci_low_1s > 0`) across the quorum, the favourable move is **harami-specific**, not a generic regime
  property; if not, availability is a regime ambient and the conditioning adds no availability — a
  material caveat on any AVAILABILITY_GOOD reading.
- **MA-segmentation contrast** (disclosed): agreement indicates availability is substrate-robust;
  divergence indicates it is ZigZag-specific (echoing EXP-050 front-loading).
- **`/STRONG-HA` arm** (disclosed): if it broadly agrees with `/STRONG-STAT`, the availability finding is
  filter-robust; divergence is disclosed, binding read stays `/STRONG-STAT`.
- A NaN bootstrap lower bound (all-degenerate resample, e.g. m < block feasibility) is treated as
  **not** MOVE_AVAILABLE (cannot assert `ci_low_1s > 1.0`), never silently passed — same guard as
  `viable_status`.

Goalposts are fixed here: the 1.0-ATR leg, the `median_MFE > median_MAE` leg, the 30-event floor, and the
P11 quorum are not revised after seeing results.

---

## Implementation Safety Constraints (for experiment-developer)

- **Timestamp ordering**: align HA candles ↔ real bars by `CloseTime`; order events by entry time; never
  align by bar index across views. ZigZag/confirmation indices are real-bar indices within the cell frame.
- **Holdout / TRAIN fence**: F01 file-order prefix only — `train_rows = int(int(total_rows*0.7)*0.7)`,
  `scan.slice(0, train_rows)`; never sort/collect the full file; never read TEST or the final-30% holdout;
  fence domain bars to `CloseTime ≤ train_end_ts`; excursion windows clip at `train_last_idx` only via the
  DATA_CENSORED exclusion (a censored event is dropped, never measured against a truncated window).
- **Denominators / zero-baseline**: medians computed only over qualifying (non-censored, post-warmup)
  events; `< 30` → NOT_VIABLE-by-power (string status), never a ratio or `0/0`; NaN bootstrap bound →
  not-available. Reference multiples `median_MFE / {0.5, 1.0}` are reporting-only and skip when the median
  is undefined.
- **Causality**: signal/`M_sofar` use only the confirmed start pivot + entry-bar close; `c1`,`c2` are
  descriptive grouping only; excursions read only `[e+1, c2]`. Assert `MFE,MAE ≥ 0` and `c2 > e`.
- **Bootstrap**: seed fixed in `run_metadata.json`; `N_BOOT=10_000`, `BOOT_BATCH=2_000`; block
  `b=max(1,round(m**(1/3)))`; the median moving-block bootstrap and the median-diff contrast live in the
  EXP-055 helper (the ≤1 new module), reusing the `block_bootstrap_ci` resampling pattern with `np.median`.
- **Vectorisation**: the per-event excursion window scan is a bounded Python loop over a few hundred events
  per cell (as `move_size.excursions`) — keep it explicit (causally clear); the bootstrap is vectorised in
  batches. `tqdm` over the 99-cell outer loop; bounded per-cell memory (do not retain all domain frames).
- **Determinism**: the second full pass must reproduce frame-identical outputs; no wall-clock or
  unordered-set dependence.

---

## Complexity Check

- **Statistical tests: 4 / 4** — (1) median-MFE moving-block bootstrap CI; (2) median-MAE moving-block
  bootstrap CI; (3) matched-random median-MFE contrast CI; (4) MA(20,50)-segmentation median-MFE contrast
  CI. The MOVE_AVAILABLE legs (CI_low > 1.0; median MFE > median MAE) and reference-line multiples reuse
  test (1) — no new inference. `/STRONG-HA` and the MAD arm reuse tests (1)/(2)'s machinery on disclosed
  populations (no new method).
- **Visualisations: 4 / 4** — forest (MFE/MAE + band); MFE−MAE asymmetry heatmap; pooled distributions +
  band; MOVE_AVAILABLE / P11 composition map.
- **New modules: 1 / 1** — the EXP-055 lifetime-availability helper (end-of-M_b window; ATR-normalised
  excursion; median moving-block + median-diff bootstrap; mechanical readout). All other machinery reused
  from `xen.*` and EXP-047 `move_size.py`.
