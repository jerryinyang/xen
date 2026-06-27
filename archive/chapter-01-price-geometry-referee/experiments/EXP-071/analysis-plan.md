# Analysis Plan: Experiment EXP-071

## Objective

Run the **one-shot TEST confirmation** for the CF-HA-HARAMI-001 candidate family (CAND-001).
This experiment is the harami family's analog of EXP-037 / EXP-038 in the AVWAP pipeline —
the first counted TEST reads in the family's history, executed after the EXP-070 method
calibration delivered a validated, Null-A-controlled inference pipeline (CALIBRATION_DELIVERED,
2026-06-18).

The inference pipeline (EXP-068 `N-PARTIAL-V2A` / `N-V2A×ADV-NONE` / `N-BENCH` / `RM-native`
machinery) is **applied unchanged in semantics** to the TEST stratum of the predeclared 6-cell
binding family. The question is whether the MA(20,50)-native `/STRONG-STAT`-conditioned HA
harami, under `N-PARTIAL-V2A`, shows per-event gross ATR-normalised expectancy with
`median CI_low > 0`, `raw-mean CI_low > 0`, and `beats-RM contrast CI_low > 0`
(all Holm-adjusted at α = 0.05) in at least 3 cells spanning at least 2 instruments, of which
at least 2 are non-4h, with each clearing cell's point estimate exceeding its EXP-070-derived
calibrated margin — all predeclared in D0 P9 before any TEST row was loaded.

**TRAIN rows** (first 49% per file) are used only for (a) P12 reconciliation pre-flight and
(b) carrying MA / `/STRONG-STAT` / ATR state into the TEST window. No TRAIN harami event
enters a binding TEST inference. The **global holdout** (final 30%) is never loaded.

## Reused vs. New Components

| Component | Source | Status in EXP-071 |
| --- | --- | --- |
| TRAIN-only 1-minute load (first 49%), domain bar build, `real_ohlc`, `bar_aggregator` | EXP-068 `code/run_experiment.py`, `xen.bar_aggregator` | Reused unchanged (state carry-in and P12 anchor; the same certified TRAIN/domain path) |
| HA-harami detection (`generate_heiken_ashi`, `detect_ha_harami`, `harami_entry_indices`) | `xen.heiken_ashi_generator`, `xen.ha_harami`, EXP-068 | Reused unchanged — **detection on HA candles only; outcomes always on real prices** |
| MA(20,50) segmentation + native `/STRONG-STAT` mask (`ma_segment_moves`, `live_strong_stat`, `_ma_context`) | EXP-068, `xen.strong_move` | Reused unchanged — binding native conditioning object |
| `N-PARTIAL-V2A` resolution + `RM-native` matched-random (`signal_arm`, `matched_random_arm`, barriers/legs via `xen.capture_barriers`, `xen.position_exits`) | EXP-068 | Reused **unchanged in structure** — the binding inference arm and its attribution null |
| `N-V2A×ADV-NONE` + `N-BENCH` exit arms | EXP-068 | Reused unchanged — disclosed arms (non-binding) |
| Median/mean moving-block bootstrap + CI + contrast (`bootstrap_median_distribution`, `bootstrap_stat_distribution`, `median_ci`, `contrast_ci`), `_winsorized_mean`, `_summarize_arm` | `xen.expectancy`, EXP-068 | Reused **unchanged** — the decision statistics |
| TEST-slice loader with TRAIN state carry-in | New | (a) One of five new pieces in the experiment-local module |
| Freeze-file writer (atomic write + SHA-256 pin) | New | (b) Written before any TEST row is loaded; enforces D0 P8 |
| Holm-adjusted composition classifier | New | (c) Per-cell CI → conjunction flags → experiment verdict |
| Equal-weight portfolio aggregator | New | (d) Pools per-event returns across 6 cells for the P10 disclosure |
| TEST-read manifest emitter | New | (e) Per-stratum read-count ledger for `test-read-ledger.md` update |

No new or modified `python/src/xen/` module. All five new pieces live inside the single
experiment-local module under `python/experiments/EXP-071/code/`.

---

## Methodology

### Step 1: Dependency Gates, P12 Reconciliation, and Freeze-File Write

- **Method**: Hard-fail gating sequence followed by atomic freeze-file write.

  1. **Dependency gates** (abort on any failure):
     - Load `python/experiments/EXP-070/results/calibration_map.csv` — assert all 6 P5 cells have
       verdict = `PASS` (Null-A conjunction FPR ≤ 0.05); read per-cell `calibrated_margin_atr` and
       Null-B advisory FPR values; hard-fail if any cell is `FPR_EXCLUDED` or `METHOD_DEFECT`.
     - Load `python/experiments/EXP-070/results/temporal_stability.csv` — read per-cell
       `DECAYING` / `STABLE` / `GROWING` flags.
     - Load `python/experiments/EXP-068/results/g015_verdict.json` — assert
       `native_per_arm["PARTIAL-V2A"]["g015_passes"]["cells"]` ex-EURUSD equals **exactly** the
       declared 6 P5 cells (set equality; abort otherwise).
     - For each instrument bind the source file name and total 1-minute row count against EXP-068's
       recorded boundaries (source-identity gate).

  2. **P12 reconciliation** (binding, before any new TEST inference): regenerate per cell on the
     TRAIN slice — domain bars, HA-harami entries, MA segments, native `/STRONG-STAT` mask — using
     the reused functions, then run the frozen `signal_arm` for `N-BENCH` and `N-PARTIAL-V2A` and
     `matched_random_arm` for `RM-native`, and assert the per-cell `median`, `mean`, `ci_low_1s`,
     `mean_ci_low_1s`, and the `beats-RM` contrast reproduce EXP-068 `per_cell_expectancy.parquet`
     (and EXP-061 `M0`, EXP-066 `PARTIAL-V2A`) **at 1e-9** (D0 P1). Hard-fail on any mismatch —
     this is the freeze-faithfulness proof required before any TEST contact.

  3. **Freeze-file write** (D0 P8 — binding): write `EXP-071/frozen_selection.json` **atomically**
     (to a `.tmp` sibling, then `os.replace` to the final path) recording:
     - The predeclared binding TEST family (6 cells, byte-identical to D0 P5).
     - EXP-070 Null-A conjunction FPRs and `calibrated_margin_atr` per cell.
     - EXP-070 temporal stability flags (`DECAYING` / `STABLE` / `GROWING`) per cell.
     - EXP-070 Null-B advisory conjunction FPRs per cell (contextual; not gating).
     - The composition threshold (P9) verbatim.
     - Bootstrap parameters: `BASE_SEED = 20260616`, `N_BOOT = 10_000`,
       block-length rule `b = round(m^(1/3))`.
     - Composite portfolio seed: `[BASE_SEED, 999, "composite"]`.
     - EXP-070 result file hashes (SHA-256 of `calibration_map.csv`,
       `temporal_stability.csv`) as provenance.
     Append the SHA-256 of the file's content to the file after writing. Record the freeze-file path
     and hash in `run_metadata.json`. **No TEST row is loaded before this step completes.**

- **Why**: the dependency chain ensures the inference machinery is byte-reused from its
  governance-certified TRAIN state before any TEST contact; the P12 1e-9 reconciliation is the
  only proof the resolver did not change; the atomic freeze-file write is the D0 P8 contract
  (irrevocable commitment to the TEST family and composition threshold before the TEST stratum is
  visible to the code).

- **Simpler alternative considered**: trust EXP-068 / EXP-070 metadata without re-running the
  arms or writing a freeze file. Rejected — the P12 reconciliation is the freeze-faithfulness
  guarantee governance requires; skipping the freeze file would make the TEST-family commitment
  unfalsifiable.

- **Expected output**: validated dependency confirmations; `reconciliation.csv` (per-cell anchor
  diffs ≤ 1e-9); `frozen_selection.json` (written, SHA-256-pinned, path recorded in
  `run_metadata.json`); gates recorded in `run_metadata.json`.

---

### Step 2: TEST-Slice Load with TRAIN State Carry-In

- **Method**: per cell, load the full TRAIN 1-minute slice (rows `[0, train_cutoff)`) to build
  the MA / `/STRONG-STAT` / ATR state, then load the TEST 1-minute slice (rows
  `[train_cutoff, analysis_cutoff)`) and build TEST domain bars using `xen.bar_aggregator` from
  the TEST rows only. Carry the MA / `/STRONG-STAT` warmup state — not events — from the final
  TRAIN bar into the TEST window via a single sequential pass (TRAIN bars consumed for state;
  their harami events are never placed into the TEST inference set). Assert that every TEST harami
  entry index falls strictly within `[train_cutoff, analysis_cutoff)` (hard-fail otherwise).

  Split boundaries (per instrument):
  ```
  analysis_cutoff = int(total_1m_rows * 0.7)
  train_cutoff    = int(analysis_cutoff * 0.7)   # ≈ 49% of total
  # TEST slice: [train_cutoff, analysis_cutoff)
  # holdout:    [analysis_cutoff, total)         — NEVER LOADED
  ```

  Per-cell domain and coverage:
  | Cell | Domain | Coverage rule |
  | --- | --- | --- |
  | GBPUSD-5m | 5m | strict (EXP-068 convention) |
  | GBPUSD-1h | 1h | `min_coverage = 0.90` |
  | NZDUSD-1h | 1h | `min_coverage = 0.90` |
  | NZDUSD-2h | 2h | `min_coverage = 0.90` |
  | GBPJPY-30m | 30m | `min_coverage = 0.90` |
  | US2000-4h | 4h | `min_coverage = 0.90` |

  Generate HA candles from TEST domain bars (detection only). Compute ATR on TEST bars using the
  trailing state from TRAIN (no TEST-internal look-back past the state boundary). Qualifying
  harami entries: `/STRONG-STAT`-conditioned harami events within the TEST window with valid
  outcome windows that close before `analysis_cutoff`. Cells with fewer than `POWER_FLOOR = 30`
  qualifying TEST events are recorded as `below-floor`, excluded from binding composition, and
  disclosed — never silently counted.

- **Why**: the MA / `/STRONG-STAT` / ATR geometry requires look-back that spans the TRAIN/TEST
  boundary; the state carry-in is the only causal way to initialise the TEST window without
  loading the holdout or using the TEST rows for warmup.

- **Simpler alternative considered**: load only the TEST rows and re-initialise state from
  scratch. Rejected — causal streaming requires the warmup state from TRAIN; re-initialising
  from TEST rows would suppress harami events in the early TEST window and change the event
  population relative to EXP-068's certified TRAIN benchmarks.

- **Expected output**: per-cell TEST harami entry arrays, per-event `m_sofar`, ATR, barrier
  geometry — all in memory; event counts per cell (disclosed in `run_metadata.json`); `below-floor`
  cells flagged.

---

### Step 3: Per-Cell Inference on TEST Events (All Four Arms)

- **Method**: for each of the 6 binding cells, run all four arms on the same TEST harami entry
  set using the reused EXP-068 machinery, unchanged in semantics:

  1. **`N-PARTIAL-V2A` (binding arm)**: `signal_arm` with the V2A partial exit — three leg
     thresholds at cumulative `{1/3, 2/3, 1} × fav_dist`, shared 1:1 adverse stop and MA-adaptive
     cap, P15 path-ordered intrabar fills (bullish: O→L→H→C; bearish: O→H→L→C). Outcomes on
     `RealOpen/RealHigh/RealLow/RealClose` (domain bars from real 1-minute time bars).
  2. **`N-V2A×ADV-NONE` (disclosed secondary arm)**: same partial exit with `adv_count = 0`
     (no adverse stop); MA cap is sole stop-out.
  3. **`N-BENCH` (disclosed signal-check)**: single-leg benchmark (50%×M_sofar fav, 1:1 adv,
     MA cap).
  4. **`RM-native` (matched-random attribution null)**: `matched_random_arm` with the same draw
     count as the `N-PARTIAL-V2A` arm per cell, drawn from the eligible MA-regime pool (causal,
     non-harami entries in the TEST window), resolved with `N-PARTIAL-V2A` exit geometry.

  Per cell, for each arm, compute via `_summarize_arm`:
  - **Median** per-event ATR-normalised return + moving-block bootstrap CI (`b = round(m^(1/3))`,
    `N_BOOT = 10_000`, deterministic per-cell seed `_rng([BASE_SEED, cell_index])`).
  - **Raw mean** per-event return + bootstrap CI (same bootstrap call — the mean co-primary is
    a second statistic from the same bootstrap draws, no additional bootstrap).
  - **10% symmetric winsorized mean** point estimate (`TRIM_FRAC = 0.10`, `_winsorized_mean`
    function from EXP-068 — point estimate only, no bootstrap).

  Per cell, compute the **`beats-RM-native` two-sample contrast** between the `N-PARTIAL-V2A`
  per-event return set and the `RM-native` per-event return set via `contrast_ci`
  (moving-block bootstrap, same `b` and `N_BOOT`, seed `_rng([BASE_SEED, cell_index, "contrast"])`).

- **Why**: this is exactly the frozen EXP-068 inference the EXP-070 calibration certified; the
  only change from TRAIN to TEST is the input event population (TEST harami entries instead of
  TRAIN). All four arms are run per-cell rather than selectively so the disclosed arms provide
  the MEAN_RECOVERABLE diagnostic and signal-check anchor at no additional statistical cost.

- **Simpler alternative considered**: run only the binding arm and skip the disclosed arms. Rejected
  — `N-V2A×ADV-NONE` is required by D0 P2 / P11 for MEAN_RECOVERABLE classification; `N-BENCH`
  is required by P11 as signal-check anchor. Both run on the same events at the same bootstrap cost.

- **Expected output**: per-cell arm results frame in memory (median, CI bounds, mean, CI bounds,
  winsorized mean, `beats-RM` CI bounds, event count, bootstrap block length, seed used); inputs
  for Step 4 Holm adjustment and Step 5 portfolio aggregation.

---

### Step 4: Holm Adjustment and Composition Classification

- **Method**: apply Holm-Bonferroni correction across the 6-cell binding family at α = 0.05
  separately for the **median CI leg** and the **`beats-RM` contrast CI leg**.

  For each of the two Holm-adjusted legs:
  - Extract from the bootstrap distribution the per-cell one-sided p-value:
    `p_median[cell] = fraction of bootstrap median samples ≤ 0`;
    `p_beats_rm[cell] = fraction of bootstrap contrast samples ≤ 0`.
  - Order cells by p-value ascending (most significant first). Apply Holm step-down:
    compare sorted `p_i` against `α / (k − i + 1)` where `k = 6` and `i` is the rank. A cell
    is Holm-rejected (CI_low ≤ 0 after adjustment) iff its sorted `p_i > α / (k − i + 1)`;
    all subsequent cells are also Holm-rejected regardless of their raw p. Record both the raw
    and Holm-adjusted lower CI bounds per cell.

  Per-cell conjunction evaluation (all four conditions must hold for a cell to **clear**):
  1. `median CI_low > 0` (Holm-adjusted)
  2. `raw-mean CI_low > 0` (unadjusted — the raw-mean leg is not Holm-adjusted; see D0 P4)
  3. `beats-RM contrast CI_low > 0` (Holm-adjusted)
  4. `N-PARTIAL-V2A` median point estimate > `calibrated_margin_atr` from EXP-070
     (deterministic quantile comparison against the frozen calibration map — not a new
     statistical test; no RNG or bootstrap)

  **Below-floor cells** (< 30 qualifying TEST events) are excluded from the composition with
  explicit disposition `below_floor` in `composition_verdict.json` — never counted as clearing
  or failing, never NaN-propagated.

  **Experiment-level verdict** (exhaustive, unambiguous; D0 P9):
  - **`TEST_CONFIRMED`**: ≥ 3 cells clear the full conjunction, spanning ≥ 2 instruments, of
    which ≥ 2 clearing cells are non-4h.
  - **`TEST_INCONCLUSIVE`**: the family fails the composition threshold but the portfolio
    composite CI spans zero (power-limited; no systematic negative — wide CIs, not directional
    failure), or the cell count falls below the threshold with wide individual CIs.
  - **`TEST_NOT_CONFIRMED`**: the family fails the composition threshold with `CI_low ≤ 0`
    in the majority of binding cells — systematic negative, not power-limited.

  **Yellow-flag detection** (D0 P4 / scope §Success Criteria): for `N-PARTIAL-V2A`, a cell
  that satisfies `median CI_low > 0` (Holm-adjusted) ∧ `beats-RM CI_low > 0` (Holm-adjusted)
  ∧ `winsorm > 0` but `raw-mean CI_low ≤ 0` receives a `yellow_flag = true` note in
  `composition_verdict.json`. The raw-mean failure is informative in a PARTIAL_RECOVERY cell
  and warrants inspection before EXP-072.

  **MEAN_RECOVERABLE flag** (D0 P11 / scope §Disclosures): for `N-V2A×ADV-NONE`, a cell that
  is `winsorm > 0` ∧ `raw-mean ≤ 0` is flagged `mean_recoverable = true` — the primary
  EXP-072 tail-filter candidate pool.

- **Why**: Holm-Bonferroni is the declared FWER-controlling adjustment for the 6-cell family
  (D0 P3/P9). It is uniformly more powerful than Bonferroni, step-down, and preserves the
  declared α = 0.05 family-wise error rate without further approximation. The `raw-mean CI_low`
  is not Holm-adjusted because it is a per-cell co-primary, not a family-level multiple
  comparison — the composition already gates on the conjunction of three independent legs.

- **Simpler alternative considered**: Bonferroni correction instead of Holm. Holm is strictly
  more powerful and equally simple to implement; Bonferroni would be more conservative at no
  benefit. The scope and D0 predeclare Holm, so no choice is available.

- **Expected output**: `per_cell_results.csv` (per cell × arm: median, raw-mean, winsorm point
  estimates; raw and Holm-adjusted CI bounds; conjunction flags; `margin_clear`; `yellow_flag`;
  `mean_recoverable`; `below_floor`); `composition_verdict.json` (per-cell clearing flags +
  experiment-level verdict + clearing cell list + instrument/non-4h counts).

---

### Step 5: Portfolio-Aggregate Disclosure (D0 P10, Non-Binding)

- **Method**: pool all per-event `N-PARTIAL-V2A` returns from the binding cells that entered
  inference (i.e., the declared family minus any `below-floor` cells), equally weighted by cell
  (each cell contributes its per-event return set at equal weight, regardless of cell event
  count). Compute the composite:
  - Composite median and raw mean with moving-block bootstrap CI (`b = round(m_total^(1/3))`,
    `N_BOOT = 10_000`, seed predeclared in `frozen_selection.json` as
    `[BASE_SEED, 999, "composite"]`).
  - 10% symmetric winsorized mean point estimate (same `_winsorized_mean` function).
  Record in `portfolio_results.csv`. This metric is entered in `test-read-ledger.md` as a
  **disclosure** against all 6 member strata — not a counted read per stratum.

- **Why**: the portfolio disclosure (D0 P10) is the gross anchor for EXP-073 portfolio
  construction and informs G-016 with a family-level signal view. Equal weighting is the
  simplest non-arbitrary aggregation scheme consistent with no position-sizing assumptions.
  The composite seed is predeclared in the freeze file (before TEST load) so it cannot be
  chosen post-hoc.

- **Simpler alternative considered**: skip the portfolio disclosure and rely only on per-cell
  results. Rejected — the portfolio aggregate is a D0 P10 predeclared deliverable and serves as
  EXP-073's gross anchor; it cannot be deferred without a D0 amendment.

- **Expected output**: `portfolio_results.csv` (composite median, mean, winsorm; CI lower and
  upper bounds; contributing cell list; total event count; bootstrap block length; seed).

---

### Step 6: TEST-Read Manifest and Run Metadata

- **Method**: emit `test_read_manifest.csv` with one row per binding stratum that entered a
  per-cell inference (i.e., the 6 P5 cells, minus any `below-floor` exclusions), recording:
  `instrument`, `domain`, `counted_reads_consumed = 1`. Cells excluded as `below-floor` record
  `counted_reads_consumed = 0` with disposition noted. This manifest is the input for the
  same-commit `test-read-ledger.md` update in Stage 7 documentation.

  Emit `run_metadata.json` recording:
  - Experiment status and verdict.
  - Freeze-file path and SHA-256 hash.
  - Dependency gate confirmations (EXP-070, EXP-068, EXP-066, EXP-061 P12 results).
  - P12 reconciliation max absolute diff per cell (≤ 1e-9 required).
  - Per-cell event counts (TEST qualifying events per arm).
  - Bootstrap seeds, `N_BOOT`, block lengths per cell.
  - Composite portfolio seed.
  - Determinism hash (SHA-256 of `per_cell_results.csv` and `portfolio_results.csv`).
  - Source file names and row counts per instrument.

- **Why**: the manifest is the machine-readable input for the test-read-ledger update, which
  must occur in the same commit as the results (D0 P6). The `run_metadata.json` preserves the
  full provenance chain required for Stage 5 audit and Stage 8 governance.

- **Simpler alternative considered**: document the TEST-read counts manually in Stage 7 without
  a manifest file. Rejected — a machine-readable manifest reduces human error in the ledger
  update and is required by the scope's declared output contract.

- **Expected output**: `test_read_manifest.csv`; `run_metadata.json` with all confirmations.

---

### Step 7: Determinism Replay

- **Method**: re-run Steps 2–6 for exactly two cells — **US2000-4h** (thinnest, single 4h cell)
  and **GBPUSD-1h** (high-count non-4h) — with identical seeds and frozen inputs, and assert
  that all per-draw statistics and the final output rows for those two cells are frame-identical
  (`determinism_pass = true`). Additionally, perform a **full second pass** of all six cells
  and assert `per_cell_results.csv` and `portfolio_results.csv` reproduce byte-identically
  (SHA-256 comparison against the first-pass hash recorded in `run_metadata.json`).

- **Why**: determinism is a D0 P7 Leg 3 binding requirement; its failure would invalidate the
  audit (Stage 5) and governance (Stage 8) conclusions. The two-cell spot check runs inline
  without I/O cost; the full second-pass byte comparison is the governance-grade proof.

- **Simpler alternative considered**: rely on fixed seeds as a logical guarantee of determinism
  without a second-pass comparison. Rejected — the EXP-070 calibration required the full
  second pass for the same reason; this experiment's TEST contact imposes at least as strong a
  reproducibility requirement.

- **Expected output**: `determinism_pass` flag and second-pass SHA-256 match recorded in
  `run_metadata.json`.

---

## Visualisations (5 / 5 budget)

1. **Per-cell median effect vs. calibrated margin** (forest-plot style, all 6 cells): one row
   per cell, showing the `N-PARTIAL-V2A` median point estimate with Holm-adjusted CI, the
   `N-V2A×ADV-NONE` median point estimate alongside it, and a vertical reference line at the
   cell's EXP-070 calibrated margin. Cells are labelled with their temporal stability flag
   (`GROWING` / `DECAYING` / `STABLE`). Clearing cells are distinguished visually. This is the
   headline composition read.

2. **Composition heatmap** (cell × conjunction leg): rows = 6 cells, columns = the 4 composition
   conditions (median CI_low > 0, raw-mean CI_low > 0, beats-RM CI_low > 0, margin clear);
   each cell filled green/red/grey (clearing / failing / below-floor). Yellow-flag cells carry
   a marker. The heatmap immediately shows which legs pass and which fail across the family.

3. **`beats-RM` contrast per cell with CI**: one panel per cell (or 6-panel facet), showing the
   `N-PARTIAL-V2A` `beats-RM` contrast point estimate with Holm-adjusted bootstrap CI and a
   zero reference line. Distinguishes cells that clear this leg from those that do not. This
   is the harami-attribution diagnostic — cells where `beats-RM` fails despite positive median
   warrant the strongest caution.

4. **Portfolio-aggregate composite CI** (bootstrap distribution plot): histogram / KDE of the
   composite `N-PARTIAL-V2A` bootstrap median distribution (over the pooled 6-cell returns)
   with the 95% CI bounds and the point estimate annotated. A vertical zero line confirms
   whether the composite CI spans zero or is strictly positive.

5. **Winsorized mean diagnostic per cell** (dual-arm comparison): per cell, a paired bar or
   dot plot of `N-PARTIAL-V2A` and `N-V2A×ADV-NONE` winsorized mean point estimates alongside
   the raw mean point estimate. Cells where `N-V2A×ADV-NONE` is `winsorm+` ∧ `mean−`
   (MEAN_RECOVERABLE candidates for EXP-072) are annotated. Yellow-flagged binding cells
   (winsorm+ ∧ mean−) carry a marker.

---

## Interpretation Guide

### Experiment-Level Verdicts

- **`TEST_CONFIRMED`** (Evidence FOR): ≥ 3 binding cells clear the full conjunction (median+,
  mean+, beats-RM+, margin+) spanning ≥ 2 instruments, ≥ 2 non-4h. CAND-001 advances.
  *Consequence:* EXP-072 (cost-aware / tail-filter) and EXP-073 (portfolio construction) may be
  opened with explicit operator direction; each requires its own D0 before data contact.
  Counted TEST reads are recorded in `test-read-ledger.md` in the same commit as results.

- **`TEST_INCONCLUSIVE`** (Power-limited): the composition threshold is not met but the
  portfolio composite CI spans zero without a systematic negative direction, or the cell count
  falls short with wide CIs. Family stays OPEN; counted reads consumed. No automatic follow-up
  prescribed — a targeted follow-up may be scoped separately.

- **`TEST_NOT_CONFIRMED`** (Evidence AGAINST): the family fails the composition threshold with
  `CI_low ≤ 0` in the majority of binding cells (systematic negative). CAND-001 retired on this
  scope; family stays OPEN; counted reads consumed. No EXP-072 / EXP-073 activation.

### DECAYING Temporal Flag Interpretation

Three of the six binding cells carry a `DECAYING` flag from EXP-070 (GBPUSD-1h severe,
NZDUSD-1h mild, GBPJPY-30m severe), meaning their TRAIN-period point estimate decayed more
than 1 bootstrap SE from the full-TRAIN value in the final walk-forward window. This is a
**disclosed context, not a gate**: DECAYING cells are not excluded from the binding family
and are counted in the composition. The flag informs interpretation:

- A DECAYING cell that **clears** in TEST is positive evidence with the caveat that the
  TRAIN-period edge was weakening; interpret with the decay context disclosed.
- A DECAYING cell that **fails** in TEST is consistent with the decay trajectory; it does not
  independently invalidate a family-level confirmation from other cells.
- STABLE and GROWING cells (NZDUSD-2h, US2000-4h, GBPUSD-5m) carry no decay caveat;
  their TEST reads are the cleanest composition evidence.

The composition threshold does not require all 6 cells to clear — a partial confirmation
(≥ 3 / ≥ 2 instruments / ≥ 2 non-4h) is valid even if DECAYING cells fail.

### Yellow-Flag Cells (N-PARTIAL-V2A)

A `yellow_flag` cell is one where `N-PARTIAL-V2A` satisfies median+ ∧ beats-RM+ ∧ winsorm+
but `raw-mean CI_low ≤ 0`. In a PARTIAL_RECOVERY arm, the raw mean is more sensitive to
tail events than in a single-leg arm; a winsorm+ ∧ mean− pattern suggests the distribution
has a positive bulk but the raw mean is dragged by a small number of large adverse outcomes.
Yellow-flag cells **do not automatically fail or pass** the composition — the full conjunction
requires `raw-mean CI_low > 0`, so a yellow-flag cell fails on condition 2. The flag is a
note to investigate before EXP-072 (the tail-filter experiment): if the raw-mean drag is a
small number of outlier outcomes (a tail-filter candidate), the cell may be recoverable.

### MEAN_RECOVERABLE Candidates (N-V2A×ADV-NONE)

A `N-V2A×ADV-NONE` cell that is `winsorm+ ∧ mean−` indicates that the winsorized bulk of
outcomes is positive while the raw mean is pulled negative by tail events — the archetypical
MEAN_RECOVERABLE profile. These cells are **EXP-072 tail-filter candidates**. Their disposition
does not affect the binding verdict (the disclosed arm never upgrades or vetoes the binding arm);
it informs the EXP-072 D0 scope design if TEST_CONFIRMED is returned.

### Predeclared Interpretation Caveats

1. **First counted TEST reads**: this is the harami family's first TEST contact. A single
   TEST_CONFIRMED result — while actionable — is still one read on a 2-read cap per stratum.
   Effect sizes and CIs should be reported as observed; no shrinkage or adjustment is applied.
2. **Gross only**: EXP-071 measures gross gross ATR-normalised expectancy; no transaction cost,
   financing, slippage, or sizing. A gross TEST_CONFIRMED is necessary but not sufficient for
   live trading. Cost-adjusted evaluation is EXP-072's scope.
3. **The portfolio composite is non-binding**: the portfolio CI is a disclosure, not a gate.
   The experiment-level verdict is determined solely by the per-cell composition threshold.
4. **Below-floor cells** (< 30 TEST events) are excluded from composition with explicit record.
   If more than 2 cells are below floor, note the reduced composition power in the result.

---

## Implementation Safety Constraints

- **Per-event unit end-to-end**: denominators are qualifying TEST harami events per cell.
  Never bars, candles, or minutes. No per-bar suite or floor anywhere.

- **Holdout fence**: the global holdout (`[analysis_cutoff, total)` = final 30% of rows)
  is **never loaded**. The `load_test_1m` helper slices `[0, analysis_cutoff)` before any
  domain build; `analysis_cutoff = int(total * 0.7)`. Assert indices inside `[0, analysis_cutoff)`
  before and after the TRAIN/TEST boundary separation.

- **Freeze-before-TEST**: `frozen_selection.json` must be written and SHA-256-pinned before
  `load_test_1m` is called for any instrument. Any code path that loads TEST rows without the
  freeze file present is a governance violation. The freeze file write uses `os.replace` (atomic
  rename from `.tmp`) to prevent partial-write corruption.

- **Real-price outcome discipline**: HA candles are used for harami **detection only**. Every
  per-event return is a direction-signed ATR-normalised real-price excursion under the arm's
  exit rule, evaluated on `RealOpen/RealHigh/RealLow/RealClose` (domain bars from real 1-minute
  time bars). No metric is ever computed from `HAOpen / HAHigh / HALow / HAClose`.

- **No TRAIN events in binding TEST inference**: TRAIN bars are loaded for state carry-in (MA
  warmup, `/STRONG-STAT` history, ATR) only. The harami entry indices from the TRAIN slice are
  used only for P12 reconciliation. No TRAIN event enters `signal_arm` or `matched_random_arm`
  in the TEST inference pass.

- **Inference frozen**: `signal_arm`, `matched_random_arm`, `_summarize_arm`,
  `bootstrap_median_distribution`, `median_ci`, `contrast_ci`, and `_winsorized_mean` are
  reused **unchanged in semantics** from EXP-068. No frozen statistical object is modified.
  The only new code is the TEST loader, freeze-file writer, Holm classifier, portfolio
  aggregator, and manifest emitter.

- **Determinism via fixed seeds**: all randomness uses the `_rng([BASE_SEED, cell_index, purpose])`
  convention from EXP-068, with EXP-071 purpose-blocks disjoint from EXP-068 blocks. The
  composite seed `[BASE_SEED, 999, "composite"]` is predeclared in the freeze file. A full
  second-pass byte-identical reproduction is asserted.

- **No silent drops**: cells below the power floor (< 30 qualifying TEST events), any
  reconciliation or fence-gate failure, and any below-floor window are recorded with reasons
  in `composition_verdict.json` and `run_metadata.json`. Never NaN-propagated or silently
  counted as clearing or failing.

- **No HA-price metrics; no costs**: no HA-price return, no transaction cost, no net P&L,
  no slippage, no sizing, no financing (gross only; D0 P12). Costs enter EXP-072.

- **No parameter tuning; no new shared xen modules**: no sweep, parameter choice, metric
  reselection, or grid extension after TEST rows are loaded. One experiment-local module
  under `python/experiments/EXP-071/code/` only; no new or modified `python/src/xen/` module.

- **No optimisation that changes sample membership or denominators**: reuse EXP-068's vectorized
  resolver where causally equivalent. Avoid Python row loops over large frames; use `tqdm` for
  any outer loop over cells. Do not repeat heavy TRAIN/domain builds for plotting — the analysis
  pass returns bounded plot inputs.

---

## Complexity Check

- **Statistical tests: 4 / 4** — (1) regime-clustered moving-block bootstrap CI (median +
  raw-mean + winsorized mean — one bootstrap pass per cell/arm supplies all three; no extra
  test); (2) two-sample moving-block bootstrap `beats-RM-native` contrast CI; (3) Holm-Bonferroni
  FWER adjustment across the 6-cell binding family (applied twice: once for the median leg,
  once for the `beats-RM` leg); (4) per-cell calibrated-margin check (deterministic quantile
  comparison against the frozen EXP-070 `calibration_map.csv` — not a new statistical test,
  no RNG or bootstrap). Budget exhausted at 4/4; no additional inference layers.
- **Visualisations: 5 / 5** as listed above.
- **New code modules: 1 / 1** experiment-local module under `python/experiments/EXP-071/code/`.
  No new or modified shared `python/src/xen/` module.
