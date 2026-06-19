# Analysis Plan: Experiment EXP-070

> **Amended 2026-06-18 (D0-amendment-003).** Two surgical changes after the first run's
> `METHOD_DEFECT`: (1) the **binding FPR object** is now the **full P4/P9 conjunction**
> (`ci_low_1s>0 ∧ mean_ci_low_1s>0 ∧ beats_rm_low_1s>0`), with the **median-leg FPR**
> demoted to a disclosed, non-binding diagnostic; (2) the **Null B `beats-RM` arm** is
> **symmetrized** (real entry geometry, rotated forward path) because `beats-RM` is now part
> of the binding object. All numeric thresholds (α₀=0.05, 0.06 tolerance, >2/3 defect rule)
> and every other element are unchanged. See
> `docs/experiments-docs/checkpoints/2026-06-18-016-harami-candidate-screening/D0-amendment-003-binding-fpr-object-and-symmetric-null-b.md`.

> **Amended 2026-06-18 (D0-amendment-004).** Following the second run's structural
> Null-B geometry-bias finding (STRONG-STAT barrier geometry advantage survives block
> rotation because it is a property of the entry point, not the forward path), the
> operator directed that **Null-A is the sole binding null** for conjunction FPR control.
> Null-B is now an **advisory contextual diagnostic**: still computed, reported, and
> disclosed in the EXP-071 freeze file, but not a gating condition for cell classification
> or experiment verdict. The binding conjunction-FPR formula, thresholds, and all other
> analysis steps are unchanged. **No re-run required.** See
> `docs/experiments-docs/checkpoints/2026-06-18-016-harami-candidate-screening/D0-amendment-004-null-b-demoted-to-advisory.md`.

## Objective

Measure, for each of the **six predeclared P5 TEST-family cells** — GBPUSD-5m,
GBPUSD-1h, NZDUSD-1h, NZDUSD-2h, GBPJPY-30m, US2000-4h (ex-EURUSD) — whether the
**frozen EXP-068 `N-PARTIAL-V2A` event-level inference** (per-event gross ATR-normalised
real-price return → moving-block bootstrap median CI `ci_low_1s`, with the raw-mean
co-primary CI, the 10% winsorized-mean point estimate, and the `beats-RM-native`
two-sample bootstrap contrast; `b = round(m^(1/3))`, `N_BOOT = 10_000`, deterministic
per-cell seed), **applied standalone per cell** on the MA(20,50)-native
`/STRONG-STAT`-conditioned HA-harami population, has:

1. **controlled per-cell FPR** on the **binding full conjunction** (empirical
   `P(ci_low_1s > 0 ∧ mean_ci_low_1s > 0 ∧ beats_rm_low_1s > 0) ≤ α₀ = 0.05` — the exact
   P4/P9 cell-acceptance event; D0-amendment-003) under **two structurally-different**
   matched-structure nulls (operator decision; both must control); the **median-leg FPR**
   `P(ci_low_1s > 0)` is retained as a disclosed, non-binding diagnostic;
2. **finite recovery** — a non-degenerate bootstrap CI width (D0 P7 Leg 2) **and** a
   finite per-cell planted-edge MDE at TPR ≥ 0.80 (operator-added power-context curve);
3. **deterministic byte-identical replay** (D0 P7 Leg 3); and
4. a disclosed **temporal-stability** classification on a TRAIN-only walk-forward
   (D0 P7 Leg 4),

at each cell's realized TRAIN event count, **TRAIN rows only, zero TEST/holdout contact,
0 candidate slots**. The output is a per-cell **calibration map** that fixes the EXP-071
binding-family membership (PASS / FPR_EXCLUDED) before any counted TEST read, plus the
per-cell MDE and temporal-stability context the EXP-071 freeze file (D0 P8) records.

This is **EXP-027 / EXP-044 re-run at the per-cell unit**, but on the EXP-068 harami
machinery (not the AVWAP matched-control machinery): the inference under test is the
EXP-068 `signal_arm` / `matched_random_arm` / `_summarize_arm` / `contrast` pipeline,
reused **unchanged in semantics**, evaluated per cell with the entry population replaced
by synthetic null/planted-edge populations.

## Reused vs. new components

| Component | Source | Status in EXP-070 |
| --- | --- | --- |
| TRAIN-only 1-minute load (first 49%), `build_domain`, `real_ohlc`, `bar_aggregator` | EXP-068 `code/run_experiment.py`, `xen.bar_aggregator` | reused unchanged (the certified TRAIN/domain path; must reproduce EXP-068 counts) |
| HA-harami detection (`generate_heiken_ashi`, `detect_ha_harami`, `harami_entry_indices`) | `xen.heiken_ashi_generator`, `xen.ha_harami`, EXP-068 | reused unchanged — **detection on HA candles only; never used for outcomes** |
| MA(20,50) segmentation + native `/STRONG-STAT` mask (`ma_segment_moves`, `live_strong_stat`, `_ma_context` → `ma["stat"]["retained_p75"]`) | EXP-068, `xen.strong_move` | reused unchanged — the native conditioning object (binding) |
| `N-PARTIAL-V2A` resolution + `RM-native` matched-random (`signal_arm`, `matched_random_arm`, barriers/legs via `xen.capture_barriers`, `xen.position_exits`) | EXP-068 | reused **unchanged in structure** — this is the inference being calibrated |
| Median/mean moving-block bootstrap + CI + contrast (`bootstrap_median_distribution`, `bootstrap_stat_distribution`, `median_ci`, `contrast_ci`), `_winsorized_mean`, `_summarize_arm` | `xen.expectancy`, EXP-068 | reused **unchanged** — the decision statistics |
| Per-cell two-null + planted-edge substrate; FPR/TPR/MDE classifier; walk-forward | new | the one experiment-local helper (1-module budget) |

No new or modified `python/src/xen/` module.

## Methodology

### Step 1: Dependency gates, P12 reconciliation, and the frozen entry populations

- **Method**: Hard-fail unless EXP-068 `results/run_metadata.json` records its completed
  status and `results/g015_verdict.json`
  `native_per_arm["PARTIAL-V2A"]["g015_passes"]["cells"]` minus `EURUSD` equals **exactly**
  the six P5 cells (assert set equality; abort otherwise). For each instrument bind the
  source file name, total row count, and the first-49% TRAIN row count against EXP-068's
  recorded boundaries (source-identity gate — equal event counts alone are insufficient if
  a file was recollected). Regenerate per cell, on the TRAIN slice, the EXP-068 domain
  bars, HA-harami entries, MA segments, and the native `/STRONG-STAT` mask using the
  reused functions.
- **P12 reconciliation (binding, before any null/planted measurement)**: run the frozen
  `signal_arm` for `BENCH` and `PARTIAL-V2A` and `matched_random_arm` for `RM-native` on
  each of the six cells and assert the per-cell `median`, `mean`, `ci_low_1s`,
  `mean_ci_low_1s`, and the `beats-RM` contrast reproduce EXP-068
  `per_cell_expectancy.parquet` (and EXP-061 `M0`, EXP-066 `PARTIAL-V2A`) **at 1e-9**
  (D0 P1). Hard-fail on any mismatch — this proves the machinery is byte-reused before it
  is calibrated.
- **Anti-overfitting fence (binding)**: the real harami events' resolved **outcomes** are
  read only for the P12 reconciliation anchor (they are already-published TRAIN values);
  they are **never** used to set the null placement, the planted-edge grid, or any
  pass/fail threshold. The signal under calibration test is entirely synthetic (Step 3).
- **Why**: the calibration must run on the exact EXP-068 TRAIN scaffolding for its
  verdicts to transfer to EXP-071; the 1e-9 reconciliation is the freeze-faithfulness
  proof the gate (and Stage-4 governance) require.
- **Simpler alternative considered**: trust EXP-068's metadata without re-running the
  arms. Rejected — the reconciliation is the only guarantee the inference is unchanged.
- **Expected output**: validated per-cell entry populations (indices, returns, masks) in
  memory; `reconciliation.csv` (per-cell anchor diffs, all ≤ 1e-9); gate confirmations in
  `run_metadata.json`.

### Step 2: Holdout/TEST-safe precompute

- **Method**: Per cell, precompute once on the **TRAIN slice only** (first 49% per file):
  the real OHLC arrays (`real_ohlc`), MA-segment state, ATR, the eligible MA-regime pool
  (`state_all.valid & m_sofar>0 & finite ATR & ~warmup`), the harami entry indices, and
  the native conditioning mask. Assert every index lands inside the TRAIN frame
  (hard-fail otherwise). **TEST (next 21%) and the final-30% holdout are never loaded** —
  the loader slices `floor(0.7·floor(0.7·total))` file-order rows before any domain build.
- **Why**: makes thousands of synthetic draws reduce to index selection + the reused
  resolver/bootstrap, with the holdout/TEST fence enforced once at load.
- **Simpler alternative considered**: recompute per draw — rejected on performance only;
  numerically identical.
- **Expected output**: per-cell precomputed arrays (memory); fence confirmations in
  `run_metadata.json`.

### Step 3: Two structurally-different nulls + planted-edge substrate (the only new logic)

The true **harami** edge is exactly zero under both nulls; both run the frozen
`N-PARTIAL-V2A` machinery unchanged. They stress different dependence channels (the
EXP-027/044 two-null philosophy, translated to the OHLC-path harami resolver).

- **Null A — matched-random placement (RM-native-analog; the D0 P7 literal null)**: per
  draw, replace the harami-conditioned entries with a **matched-count** random draw
  (`draw_count` = the cell's qualifying signal `m`) from the eligible MA-regime pool
  **excluding the real signal entries** — i.e., `matched_random_arm`'s exact mechanism —
  resolved through the identical `N-PARTIAL-V2A` exit machinery on the **real** OHLC path.
  This carries any substrate / barrier-induced drift; the median-leg FPR here measures
  exactly how often a non-harami population of this size spuriously shows `ci_low_1s > 0`.
- **Null B — outcome-permuted placement (block-rotated path)**: per draw, keep the
  **real harami entry positions and count**, but resolve them against a **block-circular-
  rotated** OHLC path (whole bars rotated in contiguous blocks by a random offset, so each
  bar stays internally valid — `High ≥ max(O,C)`, `Low ≤ min(O,C)` — while the
  harami-at-bar↔forward-path alignment is broken). Block length = the frozen
  `b = round(m_bars^(1/3))` analog on the bar series (or the `xen` block-length utility),
  fixed in code before measurement. Null B permutes **outcomes** while holding placement;
  Null A permutes **placement** while holding outcomes — genuinely different null
  mechanisms, both with true harami edge 0.
  - **Null B `beats-RM` arm (symmetric; D0-amendment-003).** Because `beats-RM` is now part
    of the **binding** conjunction (Step 4 / Change 1), the Null B matched-random arm must be
    constructed **symmetrically** with the Null B pseudo-signal. Draw `draw_count` matched-
    random entries from the eligible MA-regime pool (excluding the real signal entries, as in
    Null A) and resolve them with their **real-path entry geometry** — real entry close,
    `rd`, `m_sofar`, ATR, and MA-adaptive time caps taken from the **real (un-rotated) state
    at the drawn indices** — walked **forward on the same block-rotated path** as the
    pseudo-signal. Both Null B arms then differ from each other only in **placement**
    (real-harami vs matched-random) and from the real signal only in the **permuted forward
    path**, so the contrast's true `beats-RM` edge is exactly 0. (The first run resolved this
    arm with the entry close and time caps taken from the *rotated* path while `rd`/`m_sofar`/
    ATR came from the *real* state — an asymmetry that biased `beats-RM` and inflated Null B's
    conjunction-FPR in a count-graded way; corrected here. Null A is unchanged.)
- **Planted edge (recovery / MDE)**: base = Null A's `g = 0` draws (random placement, real
  path, true edge 0). Add a known **direction-signed ATR-normalised drift `g`** to each
  event's resolved per-event return (outcomes only — never placement/matching), so the
  true per-event location shifts by exactly `g`. **Edge grid (ATR units, geometric,
  fixed in Stage 2 before measurement, decoupled from the cells' observed medians to
  avoid metric-shopping):** `g ∈ {0, 0.025, 0.05, 0.10, 0.20, 0.40, 0.80}` ATR. The
  wider 0.80 endpoint is declared now so a thin cell with a large MDE never forces a
  post-hoc grid extension. `g = 0` reuses the Null A null cell.
  - **Translation-equivariance shortcut (compute structure only; no statistical object
    changes)**: the bootstrap median is translation-equivariant, so adding `g` to every
    per-event return shifts every bootstrap median (and the raw-mean, and the
    signal-side of the `beats-RM` contrast) by exactly `+g`. Therefore
    `ci_low_1s(g) = ci_low_1s(0) + g`, and `TPR(g) = fraction of Null-A draws with
    ci_low_1s(0) > −g`. The bootstrap runs **once per draw at `g = 0`**; the whole edge
    grid is read off by thresholding the stored `ci_low_1s(0)` — exact, not approximate
    (EXP-044's "evaluate all edges per draw," sharpened).
- **Draws**: **1000 per (cell × null)** and the same 1000 Null-A draws reused for every
  `g`. Seeds via the EXP-068 `_rng([BASE_SEED, cell_index, purpose])` convention with a
  dedicated EXP-070 purpose-block per (cell, null, draw) — disjoint from EXP-068's blocks
  so no existing stream shifts. **Precision (met by construction at 1000 complete draws):**
  Wilson 95% half-width ≈ 0.0135 at FPR = 0.05 (≤ 0.03 target) and ≈ 0.025 at TPR = 0.80
  (≤ 0.05 target).
- **Per-draw reportability**: a draw is reportable iff its qualifying-event count
  `m ≥ POWER_FLOOR = 30` (the EXP-068 floor; below it `_summarize_arm` does not bootstrap).
  **Draw-completion floor**: a (cell × null) point is usable only if ≥ 90% of its 1000
  draws are reportable; otherwise the point — and, if it is a null point, the cell — is
  `CALIBRATION_UNDERPOWERED` with the completion rate recorded. No silent drops.
- **Why**: matched-random placement is the D0-named null and the harami-attribution null
  the gate's `beats-RM` leg also uses; the block-rotated-path null is the structurally
  independent second null the operator required; the additive ATR drift is the per-event
  analog of EXP-005/027's planted edge.
- **Simpler alternative considered**: a single null (D0 literal) — rejected by operator
  decision (a one-null FPR pass could be an artifact of that null's construction). A
  fully-synthetic price path — rejected; the real MA-segment cluster structure is the
  crux being stress-tested.
- **Expected output**: per-draw bounded verdict rows (cell, null, draw, `m`, `median`,
  `ci_low_1s`, `mean_ci_low_1s`, `beats_rm_low_1s`, reportable) feeding Step 4.

### Step 4: Per-cell operating characteristics and calibration classification

- **Binding FPR object (D0 P7 Leg 1 / D0-amendment-003)**: per (cell, null), the binding
  **conjunction-FPR** = fraction of **reportable** draws satisfying the full P4/P9 cell-
  acceptance conjunction `ci_low_1s > 0 ∧ mean_ci_low_1s > 0 ∧ beats_rm_low_1s > 0`
  (un-Holm-adjusted — the single-cell operating point; Holm across the family is an EXP-071
  object that can only *reduce* false positives, so this map is conservative for the gate).
  This is the **exact event EXP-071 fires on**, so it is the correct calibration target.
  Wilson 95% intervals on every rate. Primary α₀ = 0.05; {0.10, 0.01} reported within budget.
- **Disclosed secondary FPR (non-binding)**: the **median-leg** FPR (`P(ci_low_1s > 0)`) —
  the P3 viability endpoint — reported alongside the binding conjunction-FPR. On this
  absolute-return population it inherits substrate/barrier drift and will typically run far
  above α₀ (caveat 1); it is retained so the substrate-driven nature of each cell's positive
  median stays visible to the EXP-071 freeze decision, but it does **not** gate.
- **TPR / MDE**: per (cell, g) TPR via the translation shortcut on Null-A draws (the median
  leg remains the recovery/detection statistic — the planted edge is added to returns and
  shifts the bootstrap median); **per-cell planted-edge MDE(α₀)** = smallest `g` with
  `TPR ≥ 0.80` while the cell's **binding conjunction-FPR** ≤ α₀ under **both** nulls;
  non-finite (`null`, never 0) if no grid point qualifies or the conjunction-FPR is
  uncontrolled.
- **CI-width (Leg 2)**: record the full-TRAIN bootstrap median CI width per cell; a
  degenerate (zero-width) CI in any retained cell is a defect.
- **Calibrated margin (P9 condition 4 input; D0-amendment-003; budget-neutral)**: per cell,
  emit `calibrated_margin_atr` = the empirical (1 − α₀) quantile of the **Null-A** pseudo-
  signal **median point-estimate** distribution over reportable draws — i.e., the level the
  per-event median must clear to sit in the top-α₀ null tail (the R1.2-analog mechanical
  margin a real cell's EXP-071 point estimate must exceed, P9 condition 4). It is a quantile
  of the **already-computed** Null-A draw statistics — **no new bootstrap, test, plot, or
  module** — recorded in `calibration_map.csv` and `run_metadata.json` for the EXP-071
  freeze file (D0 P8). EXP-070 thus produces the P9 margin; it is not deferred to EXP-071.
- **Precision gate**: the Wilson half-width gate (FPR ≤ 0.03, TPR ≤ 0.05) now applies to
  the **binding conjunction-FPR** (D0-amendment-003) — `CALIBRATION_UNDERPOWERED` keys on
  the binding object's precision, not the disclosed median leg. (At 1000 complete draws a
  small conjunction-FPR ~0.01–0.05 has half-width ≈ 0.006–0.014, comfortably within 0.03;
  re-checked on realized reportable counts.)
- **Per-cell verdict (exhaustive, unambiguous):**
  - **PASS** (eligible for the EXP-071 binding family): both nulls' **conjunction-FPR**
    point estimates ≤ α₀ (precision-adequate) **and** finite non-degenerate CI width **and**
    finite planted-edge MDE — MDE value recorded.
  - **FPR_EXCLUDED** (dropped from the binding family with record, disclosed in the
    EXP-071 freeze file, D0 P7/P8): **conjunction-FPR** point estimate **> 0.06** under
    **either** null at adequate precision (graded `material` when the Wilson 95% lower
    bound also exceeds α₀). Cells with conjunction-FPR in (0.05, 0.06] are **retained** with
    the measured FPR reported (D0 P7 tolerance band).
  - **MDE_UNRESOLVED**: FPR controlled but no finite planted-edge MDE on the grid at
    TPR ≥ 0.80 (a disclosed power limitation; the cell still meets the lighter D0 Leg-2
    finite-CI requirement — its binding-family disposition is flagged for the EXP-071
    freeze decision, never silently dropped).
  - **CALIBRATION_UNDERPOWERED**: precision or draw-completion-floor shortfall only
    (variance, fixable by a precision-only re-run) — never a point-estimate failure.
- **Two-null disagreement diagnostic (caveat, not an auto-defect)**: non-overlapping
  Wilson 95% FPR intervals at α₀ between Null A and Null B with both precision-adequate.
  Before reading disagreement as a method problem, check whether Null B's excess tracks
  low event count / few MA segments (block-rotation distortion is worse with fewer blocks)
  — a count-graded pattern points to a rotation artifact, a flat pattern to genuine method
  failure (EXP-044 interpretation lesson).
- **Output**: `fpr_per_cell.csv` (both nulls; the **binding conjunction-FPR** and the
  **disclosed median-leg FPR**; Wilson bounds; completion rates), `tpr_mde_per_cell.csv`,
  `ci_width_per_cell.csv`, `calibration_map.csv` (verdict + machine-readable reason +
  `calibrated_margin_atr` per cell).

### Step 5: Temporal-stability walk-forward (D0 P7 Leg 4, disclosed, non-excluding)

- **Method**: per cell, partition the **TRAIN** timeline into consecutive **6-month**
  windows (step = one window). For each window compute the **median** per-event
  `N-PARTIAL-V2A` point estimate over the harami events whose entry falls in that window
  (point estimate only — no per-window bootstrap). Classify the cell:
  `DECAYING` iff the **final-window** median is more than **1 bootstrap SE** below the
  **full-TRAIN** median (SE = standard deviation of the full-TRAIN bootstrap median
  distribution already computed in Step 1/4); `GROWING` iff more than 1 SE above;
  `STABLE` otherwise. Windows with < POWER_FLOOR events are reported as low-power and
  excluded from the final-window comparison if the final window itself is below floor
  (disclosed).
- **Role**: `DECAYING` is a **disclosed flag carried into the EXP-071 D0 freeze file**; it
  does **not** exclude a cell from the binding family on this ground alone (D0 P7 Leg 4).
- **Why**: a TRAIN-edge decay would weaken a same-direction TEST read and is exactly the
  context EXP-071's one-shot interpretation needs; measuring it costs no TEST contact.
- **Simpler alternative considered**: skip (D0 makes it optional in spirit) — rejected;
  it is a frozen D0 leg and cheap given the point-estimate-only construction.
- **Output**: `temporal_stability.csv` (per-cell per-window medians, full-TRAIN median ±
  1 SE, flag).

### Step 6: Determinism replay and metadata

- **Method**: re-run two fixed cells — the single 4h cell **US2000-4h** (thin / hardest)
  and a high-count non-4h cell (**GBPUSD-1h**) — with identical seeds; assert frame-
  identical per-draw verdicts and identical FPR/TPR/MDE/temporal flags
  (`determinism_pass`). A **full second pass** of all six cells must reproduce every
  output file **byte-identical** (D0 P7 Leg 3); the SHA-256 of the headline outputs is
  recorded in `run_metadata.json` (hash-pin). `run_metadata.json` records the edge grid,
  seeds/purpose-blocks, draw and `N_BOOT` counts, the dependency + P12 + fence
  confirmations, the per-cell headline, and the experiment verdict (CALIBRATION_DELIVERED
  / METHOD_DEFECT / INCONCLUSIVE).

## Visualisations (5 / 5 budget)

1. **Per-cell FPR plot** (6 cells, faceted/paired by Null A vs Null B, with Wilson bands,
   the α₀ = 0.05 line and the 0.06 exclusion line) — the binding error-control read.
2. **Per-cell recovery curves** (TPR vs planted edge `g`, one panel per cell, the 0.80
   line and the cell's MDE marked) — the recovery read.
3. **MDE vs realized TRAIN event count** (one point per cell, MDE_UNRESOLVED annotated)
   — where per-cell inference stops recovering as counts fall (esp. US2000-4h).
4. **Calibration-precision / completion diagnostic** (Wilson half-widths and
   draw-completion rates across cells) — which cells carry usable precision.
5. **Temporal-stability walk-forward panel** (per-cell window medians vs full-TRAIN ± 1
   SE, DECAYING/STABLE/GROWING labelled).

## Interpretation Guide

- **`CALIBRATION_DELIVERED` (Evidence FOR)**: the six-cell map is produced with every cell
  classified, the MDE table and temporal flags recorded, the P12 reconciliation ≤ 1e-9,
  and the determinism second pass byte-identical. The **PASS** set is the cells EXP-071's
  binding family may read; **FPR_EXCLUDED** cells are dropped with record into the EXP-071
  freeze file (an excluded thin/4h cell — plausibly US2000-4h — is a valid, expected
  outcome, information not defect). EXP-071 is then authorised to write its freeze file
  (D0 P8) and read the PASS strata.
- **`METHOD_DEFECT` (Evidence AGAINST / gate-blocking, D0 P7 / design §7)**: **binding
  conjunction-FPR** > 0.06 in **> 2/3 of the six cells** (≥ 5) under either null
  (D0-amendment-003), **or** a degenerate (zero-width) CI in any retained cell, **or** the
  determinism second pass is not byte-identical. Consequence: **fix the calibration and
  re-run EXP-070 before any TEST contact**; consumes no counted reads.
- **`INCONCLUSIVE`**: the map is produced but **> 1/3 of the cells** (≥ 3) are
  `CALIBRATION_UNDERPOWERED`. Consequence: operator decides a precision-only re-run (more
  draws, no object change) vs. accepting a reduced binding family for EXP-071.
- A **PASS (binding conjunction-FPR ≤ α₀) alongside a high disclosed median-leg FPR** is
  the **expected, designed** reading on this population, not an anomaly: it says the cell's
  absolute median is partly substrate-driven (so the median leg alone over-fires under the
  nulls) while the harami attribution rests on the `beats-RM` excess inside the binding
  conjunction. The high median-leg FPR is reported as context, never as a failure — the
  binding object already requires `beats-RM` ∧ raw-mean ∧ median jointly.
- Report ATR-unit effects and absolute rates with CIs; non-finite MDE reported as such;
  **never a percentage over the 0-edge null baseline.** The `beats-RM` contrast is against
  the `RM-native` distribution, never against zero.

**Predeclared interpretation caveats (read before any verdict):**

1. **The median leg is absolute, not an excess — which is exactly why it is non-binding
   (D0-amendment-003).** Unlike EXP-027/044 (matched-control subtraction → true null value
   0), EXP-068's median leg is the raw per-event return, so under both nulls it inherits the
   substrate/barrier drift and its null value is **not 0**. A high median-leg FPR is
   therefore the *correct, expected* signal that a cell's positive median is not
   harami-attributable on its own — **not** a method defect. The binding object is the
   **full P4/P9 conjunction**, which includes the `beats-RM` contrast: `beats-RM` is a
   **matched excess** (signal − matched-random on the same scaffold) whose true null value
   **is 0**, so the conjunction-FPR is a properly calibrated type-I object in the
   EXP-027/044 sense. Read the binding conjunction-FPR for the verdict and the disclosed
   median-leg FPR for context; do **not** "fix" or re-centre the median statistic itself.
2. **Null B is a different dependence structure, not the same with more noise.** Block
   rotation preserves per-bar OHLC validity and block-local microstructure but breaks
   cross-block path continuity; with very few blocks (thin 4h) it distorts more. Grade any
   two-null disagreement against event/segment count before declaring a method failure
   (Step 4 diagnostic).
3. **Block-length is set on the bar series** while the per-event statistic lives on the
   resolved-return series; the likely error direction is a too-short block
   (anti-conservative → FPR excess shows up first), which the FPR measurement itself
   detects. `block_len` is recorded per cell for this diagnosis.
4. **The MDE is in ATR units at the `N-PARTIAL-V2A` exit horizon.** A PASS certifies the
   inference on this cell's event population at a representative per-event scalar; it does
   not re-certify any cost-bearing or alternative-exit outcome (those are EXP-072/EXP-073
   objects, each behind its own D0).

## Implementation Safety Constraints

- **Per-event unit end-to-end**; denominators are reportable matched events and reportable
  draws — **never bars**. No per-bar suite or floor anywhere.
- **Inference frozen**: `signal_arm` / `matched_random_arm` / `_summarize_arm` /
  `bootstrap_median_distribution` / `median_ci` / `contrast_ci` / `_winsorized_mean` are
  reused **unchanged in semantics**; the only new code is the null/planted-edge placement
  and the FPR/TPR/MDE/walk-forward classifier. No frozen statistical object is modified.
- **Fence**: real harami outcomes are read only for the P12 1e-9 anchor; planted drift
  touches **outcomes only**, never placement/matching; placement uses only bar-time
  regime/segment/ATR information.
- **Holdout/TEST**: TRAIN slice (`floor(0.7·floor(0.7·total))` file-order rows) before any
  domain build; **TEST (next 21%) and final-30% holdout never loaded**; indices re-asserted
  inside the TRAIN frame; **0 counted TEST reads** (the six P5 strata stay at 0 — verified
  against `test-read-ledger.md`).
- **Real-price discipline**: every per-event return is a direction-signed ATR-normalised
  **real-price** excursion; HA candles are used for **detection only**; no HA-price metric;
  no costs/stops-as-P&L/sizing/financing (gross calibration).
- **Zero-baseline**: null per-event location is exactly 0; FPR/TPR are absolute proportions
  with Wilson intervals; non-finite MDE reported as such (never 0); below-floor cells/draws
  carry explicit finite dispositions, never NaN propagation or silent zeros.
- **Determinism**: all randomness via the `_rng([BASE_SEED, cell_index, purpose])`
  convention with EXP-070-dedicated purpose blocks disjoint from EXP-068; replay asserted
  on two cells and a byte-identical full second pass.
- **Performance / vectorization**: precompute returns, pools, masks, and the `g=0`
  bootstrap once per cell; per draw reduces to index selection + the reused resolver +
  the chunked `BOOT_BATCH` bootstrap; the planted-edge grid is read off the stored
  `ci_low_1s(0)` (no re-bootstrap). Vectorize only where causally equivalent to the EXP-068
  resolver (identical sample membership, ordering, denominators). 6 cells × 2 nulls × 1000
  draws × `N_BOOT=10_000` is the ceiling; `tqdm` over the (cell × null × draw) loop with
  per-cell postfix; concise logging; helpers return data.
- **No silent drops**: unreportable draws, below-floor windows, two-null disagreements, and
  any reconciliation/fence-gate failure are recorded with reasons.

## Complexity Check

- Statistical tests: **4 / 4** — (1) moving-block bootstrap median CI (the frozen
  inference under test; also supplies the raw-mean/winsorized co-primaries and the
  walk-forward SE — no extra test); (2) two-sample bootstrap `beats-RM-native` contrast;
  (3) Wilson FPR/TPR intervals; (4) grid-defined per-cell planted-edge MDE determination.
  **D0-amendment-003 adds no test:** the binding conjunction-FPR is a Boolean of the median
  (1), raw-mean (1), and `beats-RM` (2) legs already computed; the `calibrated_margin_atr`
  is an empirical quantile of the already-computed Null-A draw statistics; the symmetric
  Null B `beats-RM` arm reuses the same frozen resolver. Budget unchanged at 4/4, 5/5, 1/1.
- Visualisations: **5 / 5** as listed.
- New modules: **1 / 1** experiment-local helper under `python/experiments/EXP-070/code/`.
  No new/modified shared `python/src/xen/` module.

## Expected Output Files

```text
python/experiments/EXP-070/results/
- calibration_map.csv     # per-cell PASS / FPR_EXCLUDED / MDE_UNRESOLVED / CALIBRATION_UNDERPOWERED + reason + calibrated_margin_atr
- fpr_per_cell.csv        # binding conjunction-FPR + disclosed median-leg FPR by cell × null × alpha, Wilson bounds, completion
- tpr_mde_per_cell.csv    # TPR by cell × planted edge g; per-cell MDE @ TPR≥0.80 (finite or null)
- ci_width_per_cell.csv   # full-TRAIN bootstrap median/mean CI width per cell (Leg-2 finite check)
- temporal_stability.csv  # per-cell per-window medians + full-TRAIN median ± 1 SE + DECAYING/STABLE/GROWING
- reconciliation.csv      # P12: EXP-061 M0 / EXP-068 BENCH+PARTIAL-V2A / EXP-066 PARTIAL-V2A diffs (≤1e-9)
- draw_verdicts.parquet   # bounded per-draw rows (cell, null, draw, m, ci_low_1s, mean_low, beats_rm_low, reportable)
- run_metadata.json       # status, P12/fence/dependency gates, seeds, draw/N_BOOT counts, determinism hash, verdict
python/experiments/EXP-070/plots/
- fpr_per_cell.png
- recovery_mde_curves.png
- mde_vs_event_count.png
- calibration_precision.png
- temporal_stability.png
```
