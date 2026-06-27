# Analysis Plan: Experiment EXP-062

**MA(20,50)-Substrate Lifetime Availability (Conditioned HA Harami; AVWAP-Analog MFE/MAE, Dual Conditioning Object: Hybrid and Native)**
Phase 015 lead **L2** · `CF-HA-HARAMI-001/HYP-015` · EXP-055 analog on the MA substrate · forks
EXP-055 (`availability.py`) + the existing EXP-062 single-object harness, and reuses EXP-061's dual-object
MA matched-random + P4 diagnostic.

> **Re-run under `D0-amendment-001-dual-parallel-substrate.md` (2026-06-17).** The prior EXP-062 measured a
> single MA availability arm labelled *hybrid* but actually conditioning on MA-segment `/STRONG-STAT` — the
> **native** object. The genuine **hybrid** object (ZigZag-`/STRONG-STAT`-conditioned × MA lifetime window)
> was never computed. This plan emits **both** objects individually (separate arms, separate matched-random
> nulls, separate readouts — never pooled) and supersedes the prior EXP-062 in place.

> **Mandatory-reading precondition honoured.** `014-A-conditioning-gap-and-validation-lessons.md` was
> read in full (recorded in `scope.md`); this plan keeps the conditioning / harami-anchor /
> descriptive-position / median-availability-endpoint rules. Each object's matched-random-on-MA control
> (`RM_MA_hyb`, `RM_MA_nat`) is a deliberate **null** (P5), not a signal claim; every outcome metric is on
> real prices; no position-in-move metric is used; the reference band is never subtracted (gross throughout).

## Objective

Characterise, gross and ATR-normalised, the **lifetime favourable excursion (MFE)** vs **adverse excursion
(MAE)** of the live `/STRONG-STAT`-conditioned HA harami over the **full reversal MA segment** that follows it
(entry → end of the reversal MA segment M_b, where M_b ends at the **2nd MA(20,50) crossover at/after entry**),
**for each of two conditioning objects individually**, per cell on the 99-cell member grid, and answer three
questions per object feeding the single terminal **G-015**:

The two objects share the **same** frozen HA-harami detection, the **same** MA(20,50) lifetime window, and the
**same** MA in-progress `rd`; they differ **only** in the `/STRONG-STAT` conditioning filter (P2):

- **Hybrid `A_MA_hyb`** — `/STRONG-STAT` p75 on the **in-progress confirmed ZigZag move** magnitude-so-far. Mask
  byte-identical to EXP-053/055/061's hybrid set; **the genuinely-new object** (a ZigZag-conditioned population
  over the MA lifetime window was never computed before). **No outcome back-reconciliation anchor.**
- **Native `A_MA_nat`** — `/STRONG-STAT` p75 recomputed on the **in-progress confirmed MA segment**
  magnitude-so-far. Population byte-identical to the prior EXP-062 `A_MA`; **reconciles to EXP-055's `ma_seg`
  baseline arm (1e-9)**.

Per object:

1. **Availability** — is a meaningful favourable reversal move available on the MA substrate (median MFE robustly
   above the 1.0-ATR reference line and above its own median MAE — the EXP-055 `MOVE_AVAILABLE` test)?
2. **Signal attribution (P5, binding leg)** — is that favourable room **harami-specific** or a generic property of
   the (longer) MA segments? The binding discriminator is the object's **`A_MA_* − RM_MA_*`** median-MFE contrast
   vs its **own** matched-random-on-MA null: a `MOVE_AVAILABLE` cell is `SIGNAL_ATTRIBUTABLE` for the object iff its
   median MFE beats matched-random through the identical MA lifetime window (contrast `ci_low_1s > 0`).
3. **Downside-bounding room (P4 diagnostic)** — what does the **adverse** distribution look like (median MAE,
   raw/trimmed mean, worst-5% tail-share)? A thin, top-heavy MAE tail ⇒ a 1:1 / `/ADV-EXTREME-rr1` stop (the L3 read
   EXP-063) could truncate the downside while keeping the favourable capture — this sizes that opportunity, per
   object.

This is a **descriptive / diagnostic** characterisation (HYP-015) — there is **no edge claim**; the falsifiable
sub-structure is correctness (determinism, causality, the **EXP-055 `ma_seg` reconciliation** for native, the
EXP-053 population reconciliation for both, the hybrid mask verified transitively via `A_ZZ`), not a hypothesis test
of an edge. EXP-062 **emits** the readout per object; routing is the single terminal **G-015** desk adjudication (no
self-adjudication, mirroring EXP-055). TRAIN-only; 0 candidate slots; 0 TEST reads; holdouts sealed; all metrics on
real prices, never HA prices. **The two objects are never pooled.**

---

## Methodology

The pipeline composes frozen primitives; **0 new `xen/` module is expected**. EXP-055's `code/availability.py` is
reused unchanged (end-of-M_b window, ATR-normalised excursion, median moving-block bootstrap, median-diff bootstrap,
`MOVE_AVAILABLE`/composition readout — all already MA-generic). The existing EXP-062 harness already builds the MA
context (`_ma_context`), the ZigZag context (`_zz_context`), the generic `_ctx_arm` (which **accepts an explicit
conditioning mask**), the generic `matched_random_arm`, and the P4 MAE mean/trim/tail. The dual-object change is:
(a) **relabel** the existing MA arm as the **native `A_MA_nat`** (it conditions on `ma["stat"]["retained_p75"]` —
confirmed in code); (b) **add** the **hybrid `A_MA_hyb`** = `_ctx_arm(ma, ohlc, zz["stat"]["retained_p75"], …)` (the
ZigZag `/STRONG-STAT` mask through the MA context/geometry); (c) **add** the hybrid null `RM_MA_hyb` (the generic
`matched_random_arm` with the MA `state_all`/`confirm_idx`, matched to `A_MA_hyb`'s count, excluding the hybrid
signal entries, on **new dedicated RNG purposes**); (d) emit **per-object** readouts.

The arms per cell:

| Arm | Object | Conditioning | Role |
|-----|--------|--------------|------|
| **`A_MA_hyb`** | hybrid | ZigZag `/STRONG-STAT` mask × MA window | **Binding signal — HYBRID** (NEW; no outcome anchor) |
| **`RM_MA_hyb`** | hybrid null | matched-random in-MA-regime, matched to `A_MA_hyb` | **Binding null for hybrid** (P5; NEW) |
| **`A_MA_nat`** | native | MA-segment `/STRONG-STAT` × MA window | **Binding signal — NATIVE** (reconciles EXP-055 `ma_seg`) |
| **`RM_MA_nat`** | native null | matched-random in-MA-regime, matched to `A_MA_nat` | **Binding null for native** (P5; the prior `RM_MA`) |
| `A_ZZ` | zigzag | ZigZag `/STRONG-STAT` × ZigZag window | Disclosed substrate contrast (reconciles EXP-055 binding) |
| `RM_ZZ` | zigzag null | matched-random in-ZigZag-regime | Disclosed ZigZag null |

`A_MA_hyb` and `A_MA_nat` share the MA context (`rd`, window `c2`, `ATR_entry`, `buildable`); they differ only in the
qualifying mask. `RM_MA_hyb` and `RM_MA_nat` share the MA in-regime eligible pool but match different counts, exclude
different signal entries, and use disjoint RNG. The two objects are reported individually; never summed.

### Step 0: Per-cell construction (deterministic, causal; not a statistical test)

- **Method**: Reuse `xen.bar_aggregator.aggregate_ohlc` (5m strict; others `min_coverage=0.90`);
  `xen.zigzag.generate_zigzag(bars, atr_period=14, atr_mult=1.0)` → confirmed moves + `confirm_idx` (the hybrid
  conditioning mask + disclosed ZigZag substrate); EXP-055/061 `ma_segment_moves` (MA(20,50) on real close) → MA
  segments + MA `confirm_idx` (binding substrate, shared by both MA objects); `xen.heiken_ashi_generator` +
  `xen.ha_harami.detect_ha_harami` → harami entry bars (aligned to real bars by `CloseTime`; the **same** entry array
  feeds both objects); `xen.expectancy.live_in_progress_state` + `live_strong_stat` → the conditioned populations,
  computed **per substrate** (the ZigZag in-progress state → `zz["stat"]["retained_p75"]` = the hybrid mask; the MA
  in-progress state → `ma["stat"]["retained_p75"]` = the native mask; both applied through the **MA** context for the
  binding arms); `xen.strong_move.annotate_ha_impulse` → the `/STRONG-HA` disclosed arm; `xen.zigzag.wilder_atr` →
  `ATR_entry` at each harami bar.
- **Why this method**: byte-identical reuse of the EXP-053/061 conditioned-signal construction guarantees the
  hybrid mask equals EXP-061's `H0` mask and the native mask equals EXP-061's `M0` mask, so each object's population
  is the audited one (verified by Step 6 reconciliation); any availability finding is attributable to the MA lifetime
  window, not a re-derived signal.
- **Simpler alternative considered**: re-detect the signal locally — rejected; risks population drift vs
  EXP-053/055/061 and duplicates audited code.
- **Assumptions**: the EXP-048 detector and EXP-053/061 conditioning are correct (audited PASS). HA candles for
  **detection only**; no HA price in any metric.
- **Expected output**: per cell, per object, the conditioned event table `{entry_idx, entry_time, entry_close C, rd
  (MA), ATR_entry, regime_id, strong_stat_pass}` (hybrid mask, native mask) + the disclosed ZigZag arm.

### Step 1: MA lifetime window to the end of the reversal MA segment M_b (deterministic; not a test)

- **Method**: identical to the prior EXP-062 — for each qualifying harami at entry bar `e`, on the MA `confirm_idx`,
  `pos = searchsorted(ma_confirm_idx, e, side="right")`; `c1 = ma_confirm_idx[pos]`, `c2 = ma_confirm_idx[pos+1]`
  (window end). Window = real bars `[e+1, c2]`. `pos+1 ≥ size` → **DATA_CENSORED** (excluded; disclosed). This is
  `availability.end_of_mb_window(entry_idx, ma_confirm_idx)`. **The window is computed once on the shared MA context
  and applies identically to both objects** (they share `entry_idx` and the MA `confirm_idx`); only the qualifying
  mask differs, so each object's `c2`/censoring is the per-object subset of the same window array.
- **Why this method**: the family predicts the reversal move M_b; on the MA substrate M_b is the reversal MA
  segment. The retroactively-confirmed crossovers `c1`,`c2` are used **only** as a descriptive completed-move grouping
  (P19; family doc lines 139–143) — never a live entry/filter/barrier.
- **Simpler alternative considered**: window to `c1` only — rejected (truncates the reversal swing, biases MFE toward
  zero, per EXP-055). A fixed time-cap window — rejected (not the segment-to-segment read).
- **Assumptions**: MA crossovers monotone in index (guaranteed by `ma_segment_moves`); `c2 > c1 > e`.
- **Expected output**: per event `c2` + `data_censored` flag; per cell per object, the censored count/fraction.

### Step 2: ATR-normalised lifetime MFE and MAE (deterministic; the metric, not a test)

- **Method**: `availability.lifetime_excursions_atr` over `[e+1, c2]` on real OHLC, rd-aware, both floored at `0.0`;
  derived per event `MFE − MAE`. `ATR_entry` = Wilder ATR(14) at `e` (the same divisor as EXP-053/055/061, P14), per
  object on its own qualifying subset.
- **Why this method**: max favourable/adverse excursion over the trade's natural lifetime is the canonical
  availability measure (AVWAP/EXP-055 analog); ATR-normalisation makes cells comparable.
- **Simpler alternative considered**: close-to-close lifetime return — rejected (measures *captured* return). Log-bps
  — rejected (ATR-normalisation is the 015 endpoint discipline).
- **Assumptions**: real `High`/`Low` bound the realised intrabar path; excursions are a *ceiling* on capturable move.
- **Expected output**: per event `{MFE, MAE, MFE−MAE}` (ATR units); per cell per object, the qualifying arrays per arm.

### Step 3 (TEST 1 & 2): Regime-clustered moving-block bootstrap CI of per-cell median MFE and median MAE, per object

- **Method**: `availability.median_block_bootstrap` — block `b = max(1, round(m**(1/3)))`, `n_blocks = ceil(m/b)`,
  `N_BOOT=10_000`, **fixed per-cell seed** (`np.random.default_rng([BASE_SEED, cell_index, purpose])`, P3), batched
  (`BOOT_BATCH=2_000`). Report `median`, `ci_low_1s = percentile(5)`, two-sided `[2.5, 97.5]`. Applied to **MFE
  (TEST 1)** and **MAE (TEST 2)** for **both** binding arms `A_MA_hyb` and `A_MA_nat` on **dedicated per-object RNG
  purposes** (the native purposes are byte-identical to the prior EXP-062 so its EXP-055 reconciliation still holds;
  the hybrid arm uses new purposes). The disclosed `A_ZZ`/`RM_MA_*`/`RM_ZZ`/`/STRONG-HA`/MAD arms reuse the identical
  machinery, each with its own stream.
- **Why this method**: the per-event MFE/MAE distribution is heavy-tailed and serially clustered; the moving-block
  bootstrap is the programme's frozen non-parametric tool for this dependence (no normality/i.i.d.), and the median is
  robust to the fat tail (the P14 binding statistic).
- **Simpler alternative considered**: i.i.d. percentile bootstrap — rejected (ignores serial clustering). Bootstrap
  SE of the median — rejected (a percentile CI_low is the binding `MOVE_AVAILABLE` quantity).
- **Assumptions**: events within a cell are block-exchangeable at the confirmed-segment scale (EXP-049/053/055).
- **Expected output**: per cell × object × arm `{median_MFE, mfe_ci_low_1s, …, median_MAE, mae_ci_low_1s, …,
  block_len}`; `median_MFE` as a **multiple of the 0.5-ATR and 1.0-ATR** reference lines.

### Step 4 (TEST 3, BINDING per object): `A_MA_* − RM_MA_*` matched-random signal-attribution contrast

- **Method**: `availability.median_diff_block_bootstrap` on the **median MFE** (binding) and, disclosed, the **median
  MAE**, signal − null, **once per object**. Each object's matched-random-on-MA null is the EXP-055/061 matched-count
  construction on the **MA** substrate: draw a count equal to the object's qualifying `m` from the eligible in-regime
  MA pool (valid MA in-progress state, `M_sofar>0`, finite positive ATR), **excluding that object's own
  `/STRONG-STAT` signal bars** (`RM_MA_hyb` excludes the hybrid entries; `RM_MA_nat` excludes the native entries);
  each drawn bar takes its own MA in-progress reversal `rd` and its lifetime MFE/MAE over its own MA end-of-M_b
  window. Drawn from **fresh dedicated per-object per-cell RNG purposes** (no existing stream shift; the native
  purposes match the prior EXP-062 `RM_MA`). The contrast CI is the moving-block bootstrap of the median difference
  (independent block-resample of each population by its own order, `N_BOOT=10_000`, fixed seed,
  `ci_low_1s = percentile(5)`). **`SIGNAL_ATTRIBUTABLE` for the object iff its contrast `ci_low_1s > 0`.**
- **Why this method**: P5 mandates the matched-random-on-MA null in *every* read, **per object** — this is the test
  that disentangled signal from substrate in EXP-060B. On a substrate whose segments are structurally longer, "more
  favourable room" is meaningless unless it exceeds what a random in-regime entry on the same MA segments gets. The
  median-diff moving-block bootstrap is the consistent non-parametric contrast (matched-random draws are **not
  paired** to specific haramis — disjoint pools matched on count/regime/direction — so an independence-assuming
  median-diff is correct).
- **Simpler alternative considered**: a paired per-event difference (Wilcoxon) — rejected (disjoint, unpaired pools).
  One shared MA null for both objects — rejected: P5 requires each null matched to **its own** object's count and
  excluding **its own** signal entries; a shared null would mis-attribute the hybrid (lower-count) object.
- **Assumptions**: independent block-resampling of the two populations (true by construction — disjoint pools). NaN
  bound when either arm is power-limited (handled; never defaulted to a number).
- **Expected output**: per cell per object `{rm_median_MFE, contrast_median, contrast_ci_low_1s, contrast_ci_2s}`,
  the disclosed MAE contrast, and the per-object `signal_attributable` flag. The disclosed ZigZag analog
  `A_ZZ − RM_ZZ` is computed identically.

### Step 5 (TEST 4, P4 DIAGNOSTIC): MAE mean / 10% trimmed mean / worst-5% tail-share (disclosed), per object

- **Method**: Reuse the existing EXP-062 `_stat_block_bootstrap` (byte-identical block construction to the median
  bootstrap; dedicated RNG streams) for the **raw mean** and the **10% symmetric trimmed mean** of the **MAE**
  distribution (and MFE for completeness), each with a percentile CI; and `_tail_share_largest5` for the **worst-5%
  tail-share** of MAE (the fraction of total adverse excursion contributed by the largest-5% adverse events — finite
  in `[0,1]`). Computed **per object** (hybrid and native MAE distributions are different populations).
- **Why this method**: the L2 read must size the **downside-bounding** opportunity the L3 read (EXP-063) acts on, per
  object. A thin, top-heavy MAE tail (large tail-share, trimmed-mean MAE ≪ raw-mean MAE) ⇒ the adverse side is
  **bounded-recoverable**; a broadly-large MAE ⇒ bounding cannot help. This previews the L3 mean-recovery
  investigation, which is itself per-object.
- **Simpler alternative considered**: report median MAE only — rejected (cannot distinguish a thin truncatable tail
  from a broadly-large adverse distribution). Report raw mean only — rejected (cannot separate removable-tail from
  structural; D0 P4).
- **Assumptions**: same as Step 3; the mean/trim are tail-sensitive so their CIs are wider — that width is the
  measurement, not a defect.
- **Expected output**: per cell per object `{mae_mean, mae_mean_ci_*, mae_trim10, mae_trim_ci_*,
  mae_tail_share_worst5}` (and MFE analogs). **Never** sets a `MOVE_AVAILABLE` or viability flag (P4 closure-on-mean
  rule).

### Step 6: Correctness gates (binding; not statistical tests)

- **Determinism (P12)**: a full second pass reproduces every per-cell figure **frame-identically** (all arms — both
  objects, both nulls, ZigZag, HA, MAD — both contrasts, both population digests); byte-identical across `--workers`.
  Any mismatch → SUBSTRATE/METHOD_DEFECT.
- **Causality / window invariants** (`availability.window_invariants_ok` on MA `confirm_idx`; EXP-061 `_causality_ok`
  MA leg): `MFE ≥ 0`, `MAE ≥ 0`; for every non-censored event `e+1 ≤ c2 ≤ train_last_idx`, `c2 = ma_confirm_idx[pos+1]`
  with `ma_confirm_idx[pos] > e`; no event reads `CloseTime > train_end_ts`; MA reference segments end at/before
  entry. Checked on the shared MA window + each object's qualifying subset. Violation on ≥3 instruments →
  SUBSTRATE/METHOD_DEFECT.
- **Matched-count invariant (P5), per object**: `RM_MA_hyb.draw_count == A_MA_hyb.m`; `RM_MA_nat.draw_count ==
  A_MA_nat.m`; `RM_ZZ.draw_count == A_ZZ.m`.
- **Reconciliation (P12 anchor, corrected roles)**: the **native** `A_MA_nat` arm reproduces EXP-055's `ma_seg`
  baseline arm — per-cell qualifying count + median MFE + median MAE to `RECON_TOL = 1e-9`; the disclosed **`A_ZZ`**
  arm reproduces EXP-055's binding ZigZag arm likewise. The **hybrid** `A_MA_hyb` arm has **no outcome
  back-reconciliation anchor** (new object); its ZigZag-`/STRONG-STAT` conditioning mask is the same mask that defines
  `A_ZZ`'s population (= EXP-053/055 conditioned set), so the conditioning is verified **transitively via `A_ZZ`**
  (count + digest), while its qualifying count under the MA window is a disclosed-new quantity. A reconciliation
  failure is a SUBSTRATE/METHOD_DEFECT — resolved before the readout is trusted.

---

## Mechanical Readout (emitted; NOT self-adjudicated), computed separately per object

All gross, per-cell first, composed by **P11 with the P6 non-4h rule** (≥5 cells over ≥3 instruments, with **≥3 of
the qualifying cells outside the 4h domain**), **per object**. Power floor: a cell with **< 30 qualifying
(non-censored) events** on an object's arm is **NOT_VIABLE-by-power** for that object — non-reportable, disclosed,
never a ratio. **The two objects are never pooled.**

- **Per-cell `MOVE_AVAILABLE`** (`availability.move_available`, three legs, all required, on the object's binding
  arm): (1) power ≥ 30 qualifying events; (2) median-MFE bootstrap `ci_low_1s > 1.0` (the upper reference line as a
  **comparison threshold**, never subtracted); (3) `median_MFE > median_MAE`. Computed for `A_MA_hyb` and `A_MA_nat`.
- **Per-cell `SIGNAL_ATTRIBUTABLE`** (P5, binding, per object): the object's median MFE beats its own null — the
  `A_MA_* − RM_MA_*` median-MFE contrast `ci_low_1s > 0`. Reported alongside `MOVE_AVAILABLE` and tallied with the
  non-4h rule, per object.
- **Per-object family fork (descriptive label; routing is G-015 only), on each binding `A_MA_*` arm:**
  - **AVAILABILITY_GOOD** — `MOVE_AVAILABLE` clears **P11 + the P6 non-4h rule** for the object. Reading: a meaningful
    favourable reversal move is available on MA for that conditioning object → the surface reads (L3/S1–S4) are
    justified. The `SIGNAL_ATTRIBUTABLE` tally qualifies whether the room is signal-driven or generic to MA segments.
  - **AVAILABILITY_POOR** — `MOVE_AVAILABLE` does not clear P11+non-4h with adequate power for the object. Reading: no
    broadly-available favourable reversal move on MA for that object; closure better-supported — **but no closure
    inside Phase 015** (G-015 only).
  - **INCONCLUSIVE** — fewer than the P11 quorum of cells reach ≥30 qualifying events for the object (conditioning +
    the 2-MA-crossover window deplete counts; the hybrid object is expected the more power-limited), no correctness
    failure.
  - **SUBSTRATE/METHOD_DEFECT** — any determinism/causality/invariant/reconciliation failure → fix before reporting.
- Disclosed in parallel: the `/STRONG-HA` and MAD `/STRONG-STAT` arms; the ZigZag arms (`A_ZZ` / `RM_ZZ` + their
  attribution contrast); the DATA_CENSORED fraction per cell per object per arm; the median `MFE − MAE` asymmetry
  map; the **P4 MAE mean/trim/tail decomposition** per object (the L3 downside-bounding input).

The reference band stays "never subtracted" everywhere: the 0.5/1.0-ATR lines appear **only** as (i) a lower-bound
comparison for the median (leg 2) and (ii) descriptive multiples on tables/plots. No excursion, median, mean, or
contrast is ever reduced by the reference value; all returns remain gross.

---

## Visualisations (4 / 4) — each carries both objects (hybrid + native), never pooled

1. **Per-cell median MFE & MAE forest plot** — one row per reportable cell, with the **native** and **hybrid** binding
   arms drawn as distinct series (e.g. colour/marker), MFE and MAE medians with one-sided 95% CIs, vertical **0.5-ATR
   and 1.0-ATR reference lines** — the `MOVE_AVAILABLE` legs visualised per object.
2. **`A_MA_* − RM_MA_*` median-MFE contrast forest** — per-cell signal-attribution `ci_low_1s` for **native** and
   **hybrid** (two series, coloured by each object's `SIGNAL_ATTRIBUTABLE`; non-4h cells marked; disclosed
   `A_ZZ − RM_ZZ` overlaid) — the binding discriminator: is the favourable room harami-specific on MA, per object?
3. **MAE tail decomposition** — per reportable cell, raw-mean MAE vs 10%-trimmed MAE with worst-5% tail-share
   annotated, **per object** (native + hybrid panels or series) — the P4 / L3 downside-bounding preview.
4. **`MOVE_AVAILABLE` / `SIGNAL_ATTRIBUTABLE` / P11+non-4h composition map** — instrument × domain status grid
   rendered **per object** (two panels: native, hybrid), NOT_VIABLE-by-power and COVERAGE_EXCLUDED cells greyed,
   non-4h cells marked, cell/instrument counts and the per-object AVAILABILITY_* fork annotated — the headline
   deliverable.

Disclosed-arm contrasts, reference-line multiples, MFE mean/trim/tail, and censoring counts go to **CSV**, not extra
plots. (Plot count stays 4 by drawing both objects within each figure; an extra per-object split is acceptable only
if it keeps the total ≤ the scope's 4-plot budget — otherwise the second object goes to a CSV-backed appendix panel.)

---

## Interpretation Guide (pre-registered; criteria fixed before results), per object

- If an object's **`MOVE_AVAILABLE` clears P11 + the P6 non-4h rule** → **AVAILABILITY_GOOD** for that object: the
  conditioned harami's MA reversal segment offers a robust favourable excursion (median MFE lower bound > 1.0 ATR and
  > MAE) — the AVWAP "available move, missing capture" situation **on the live MA substrate** for that conditioning
  object. This *motivates* the remaining surface reads; it is **not** an edge/tradability claim (gross).
- **Signal-attribution qualifier (binding, P5), per object:** read AVAILABILITY_GOOD **together with** the object's
  `SIGNAL_ATTRIBUTABLE` tally. Broad `MOVE_AVAILABLE` + broad `SIGNAL_ATTRIBUTABLE` (with non-4h breadth) ⇒ the room
  is **harami-specific on MA**; broad `MOVE_AVAILABLE` + sparse `SIGNAL_ATTRIBUTABLE` ⇒ a **generic
  MA-segment-length property** (a material caveat to G-015). Expectation from EXP-061: the **native** object is the
  one that expressed the benchmark-geometry edge, so native availability + attribution is the primary read; the
  **hybrid** object is expected weaker/power-limited — that contrast is itself a deliverable.
- If an object's **`MOVE_AVAILABLE` fails P11+non-4h** with adequate power → **AVAILABILITY_POOR** for that object:
  worse than AVWAP; *strengthens* the eventual closure case for that object but **decides nothing inside Phase 015**.
- If **fewer than the P11 quorum reach ≥30 qualifying events** for an object → **INCONCLUSIVE** (power-limited);
  disclose the censored/warmup attrition; recommend a follow-up scope if availability remains open for that object.
- **MAE tail decomposition (P4, the L3 input), per object:** a thin, top-heavy MAE tail across the powered cells ⇒
  the downside is **bounded-recoverable** (EXP-063's stop should truncate it); a broadly-large MAE ⇒ bounding cannot
  help (a structural caveat carried to L3/G-015). This read *sizes* the L3 opportunity per object; it does not
  pre-judge L3.
- **Hybrid vs native divergence (the central new fact):** if native is AVAILABILITY_GOOD + attributable while hybrid
  is POOR/INCONCLUSIVE, the available room is a **matched-substrate conditioning property** (consistent with EXP-061's
  benchmark-geometry finding). Convergence (both available + attributable) would broaden the family claim. The
  divergence is the deliverable, not a defect.
- **ZigZag / `/STRONG-HA` / MAD arms (disclosed):** agreement ⇒ substrate/filter-robust; divergence quantifies the
  MA-segment-length / filter effects. Binding read stays `/STRONG-STAT` on MA.
- A NaN bootstrap lower bound is treated as **not** `MOVE_AVAILABLE` / **not** `SIGNAL_ATTRIBUTABLE` for that object,
  never silently passed.

Goalposts are fixed here: the 1.0-ATR leg, the `median_MFE > median_MAE` leg, the per-object `A_MA_* − RM_MA_*`
`ci_low_1s > 0` attribution leg, the 30-event floor, the P11 quorum, and the P6 non-4h rule are not revised after
results, for either object.

---

## Implementation Safety Constraints (for experiment-developer)

- **Timestamp ordering / alignment**: align HA candles ↔ real bars by exact `CloseTime`-epoch match
  (`_map_to_grid`), order events by entry time; never align by bar index across views. The **same** harami
  `entry_idx` feeds both objects; verify `ma["entry_idx"]` and `zz["entry_idx"]` are the identical array (both detect
  on the same HA candles aligned by `CloseTime`) before applying the cross-substrate hybrid mask through the MA
  context. ZigZag/MA confirmation indices are real-bar indices within the cell frame.
- **Holdout / TRAIN fence (binding)**: F01 file-order prefix only — `analysis_rows = int(total_rows*0.7)`,
  `train_rows = int(analysis_rows*0.7)`, `scan.slice(0, train_rows)`; never sort/collect the full file; never read
  TEST or the final-30% holdout; assert chronological; fence domain bars to `CloseTime ≤ train_end_ts`; excursion
  windows clip via the DATA_CENSORED exclusion only. Reuse EXP-062 `load_train_1m` unchanged.
- **Causality / no look-ahead**: MA(20,50) `_sma` trailing only; MA segments bounded by crossovers confirmed
  **before** entry; signal/`M_sofar` from `live_in_progress_state` use only the confirmed start crossover/pivot + the
  entry-bar close; matched-random entries (both objects) constructed causally with the identical pre-entry-only state;
  `c1`,`c2` are descriptive grouping only; excursions read only `[e+1, c2]`. Keep EXP-062's `_causality_ok` MA leg.
  Assert `MFE,MAE ≥ 0` and `c2 > e`.
- **Real-price discipline**: detection on HA candles only; **every** metric on real OHLC; MA(20,50) on **real close**.
  No HA price in any metric; the reference band is never subtracted.
- **Denominators / zero-baseline**: medians/means over qualifying (non-censored, post-warmup) events only, per
  object; `< 30` → NOT_VIABLE-by-power (string status), never a ratio or `0/0`; NaN bootstrap bound →
  not-available / not-attributable; reference multiples `median_MFE / {0.5, 1.0}` reporting-only; worst-5%
  tail-share finite in `[0,1]` (0.0 when no adverse mass), never NaN/inf; empty/degenerate cell → tail-share
  undefined → excluded.
- **Bootstrap / determinism / RNG discipline (critical)**: **fixed per-cell seed** recorded in `run_metadata.json`;
  `N_BOOT=10_000`, `BOOT_BATCH=2_000`; block `b=max(1,round(m**(1/3)))`. **The native `A_MA_nat` / `RM_MA_nat` /
  `A_ZZ` / `RM_ZZ` RNG purposes must stay byte-identical to the prior EXP-062** so their EXP-055 reconciliation still
  holds; the **new hybrid `A_MA_hyb` / `RM_MA_hyb` arms and their contrast use fresh dedicated RNG purpose offsets**
  (no existing stream shifts). Second full pass reproduces frame-identical output; no wall-clock or unordered-set
  dependence.
- **Vectorisation**: keep the per-event excursion window scan as the bounded loop in `lifetime_excursions_atr`
  (causally clear); the bootstrap is vectorised in batches. Reuse EXP-062's NumPy/Polars vectorized state
  construction verbatim; do not rewrite the sequential causal logic. Resolving a second object reuses the same
  primitives on a different mask — no new sequential algorithm.
- **Performance / parallelism (integrity-preserving)**: keep EXP-062's per-instrument `ProcessPoolExecutor` with
  per-process native-thread pinning (`POLARS_MAX_THREADS=1` etc.) and fixed-order reassembly. Parallelism must
  **not** alter sample membership, ordering, denominators, metric definitions, seeds, or causal/streaming semantics —
  byte-identical output for any `--workers`.
- **Reconciliation source**: load EXP-055's `per_cell_availability.parquet` (the `ma_seg` + `stat` arms) as the P12
  anchor for native `A_MA_nat` + `A_ZZ`; a missing/empty anchor is SUBSTRATE/METHOD_DEFECT. The hybrid arm has **no**
  anchor (verified transitively via `A_ZZ` digest/count).
- **Bounded memory / progress / output**: `tqdm` over the 99-cell grid (per-instrument worker); per-cell arrays
  released after summarisation; plots built from collected per-cell summaries only — no data reloads. Output dirs
  created only in orchestration. Every per-cell record carries an `object`/arm tag; per-object CSVs/JSON keys
  separate hybrid and native; **no pooled aggregate is emitted**.

---

## Complexity Check

- **Statistical methods: 4 / 4** (Comparative experiment) — (1) median-MFE moving-block bootstrap CI; (2)
  median-MAE moving-block bootstrap CI; (3) the **`A_MA_* − RM_MA_*`** matched-random median-MFE (binding) +
  median-MAE (disclosed) difference bootstrap; (4) the P4 MAE (and MFE) mean + 10% trimmed-mean bootstrap CI +
  worst-5% tail-share. **Running these four methods on the second (hybrid) object adds no distinct method** — same
  estimator, different population. The `MOVE_AVAILABLE` legs and reference-line multiples reuse test (1).
- **Visualisations: 4 / 4** — MFE/MAE forest + band (both objects); contrast forest (both objects); MAE tail
  decomposition (both objects); composition map (both objects). Both objects are carried within the 4-plot budget.
- **New modules: 0 / ≤1** — EXP-055's `availability.py` reused; the only additions are the hybrid binding arm (the
  existing `_ctx_arm` with the ZigZag mask), the hybrid null (the generic `matched_random_arm` with MA inputs
  matched to the hybrid count), the hybrid contrast, and the per-object readout/columns — all in the orchestration
  `code/run_experiment.py`. **No new `xen/` module.**

Plan fits the scope's complexity budget exactly; the dual-object structure doubles arms/columns/series, not methods
or plots.
