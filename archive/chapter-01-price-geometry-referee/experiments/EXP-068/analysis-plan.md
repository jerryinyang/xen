# Analysis Plan: EXP-068 — MA(20,50)-Substrate Native Combined Champion

## Objective

Determine whether any of the three predeclared native champion arms —
**N-BENCH** (benchmark reference), **N-PARTIAL-V2A** (S3 surface winner; PARTIAL-V2A + 1:1
adverse), or **N-V2A×ADV-NONE** (PARTIAL-V2A + no adverse stop; ZigZag champion analog; novel on
native MA) — satisfies the **G-015 conjunction** for the native conditioning object
(MA-segment `/STRONG-STAT`, 8360-class):

> **(a) median-viable** (per-cell `E_cell_median CI_low > 0`, ≥ 30 qualifying events) **AND**
> **(b) raw-mean-positive** (per-cell `E_cell_mean CI_low > 0`; P4 co-primary — binding in G-015,
> not only diagnostic) **AND** **(c) signal-attributable** (`arm − RM-native` median contrast
> `CI_low > 0`; P5), all composed at **P11+P6** (≥ 5 passing cells over ≥ 3 instruments, with
> ≥ 3 outside the 4h domain).

A champion arm satisfying the full conjunction triggers G-015 PROCEED_TO_SCREEN for the native
object. Failure to satisfy the conjunction on any arm triggers CHARACTERISED_NOT_VIABLE or
MEAN_RECOVERABLE–FOLLOW-UP based on the P4 closure-rule structure. The hybrid object result is
disclosed from EXP-061–066 / EXP-067 and never pooled with native.

---

## Methodology

### Step 0 — P12 Reconciliation Gate (pre-analysis; SUBSTRATE/METHOD_DEFECT guard)

- **Method**: Exact numerical comparison (absolute difference ≤ `RECON_TOL = 1e-9`) of per-cell
  median expectancy and qualifying event count between EXP-068 arm outputs and reference
  experiments.
- **Why this method**: P12 mandates that the native pipeline reproduces prior results
  byte-identically before any new result is reported. Exact comparison is the only sufficient
  check; tolerance tests on derived statistics would not catch pipeline defects.
- **Simpler alternative considered**: Visual comparison of per-cell medians. Rejected — numerical
  tolerance check is required by the governance predeclaration; visual comparison cannot confirm
  1e-9 agreement.
- **Assumptions**: Deterministic RNG seeding (fixed per-cell seed P3); identical TRAIN slice
  boundaries (F01 file-order prefix, same holdout fence as EXP-061/066); identical arm
  construction logic and P15 fill model.
- **Expected output**: `reconciliation.csv` with three reconciliation rows:
  - `N-BENCH` ↔ EXP-061 `M0` / EXP-060B `BENCH-MA`: max absolute difference in per-cell median
    and count over 99 cells — must be ≤ 1e-9.
  - `N-PARTIAL-V2A` ↔ EXP-066 `M-PARTIAL-V2A`: same check — must be ≤ 1e-9.
  - `H-BENCH` ↔ EXP-061 `H0` (correctness check, not a binding result): must be ≤ 1e-9.
  - **If any check fails → SUBSTRATE/METHOD_DEFECT. Do not proceed to reporting.**
- **Determinism check**: second full pass (identical seed, same TRAIN slice) must produce
  byte-identical per-cell outputs for all 3 champion arms and their RM nulls.

---

### Step 1 — Per-cell Median Bootstrap CI (Binding Endpoint; P3/P14)

- **Method**: Regime-clustered moving-block bootstrap confidence interval on the per-event
  position-weighted gross expectancy median, per cell per arm.
- **Why this method**: The binding endpoint is the median (P3/P14), chosen for robustness to
  the heavy-tailed distribution of conditioned-harami returns; bootstrap CI (rather than
  parametric) is required because financial return distributions are non-normal and
  serially dependent. Regime-clustered blocks preserve the autocorrelation structure of MA-regime
  sequences, removing the implicit IID assumption of the standard bootstrap. The block length
  `b = round(m^(1/3))` (where `m` = qualifying event count per cell) is the pre-declared EXP-061
  convention, unchanged.
- **Simpler alternative considered**: Signed-rank test (Wilcoxon) on per-event returns against
  zero. Rejected — it tests a different null (symmetric distribution centred at zero) and does not
  produce the CI required for the viability gate. The bootstrap CI is the direct method for
  `CI_low > 0`.
- **Assumptions**: (i) Returns within a cell are exchangeable within regime blocks (the regime-
  clustered bootstrap relaxes the full-IID assumption); (ii) the MA-segment regime is a reasonable
  clustering unit for harami returns (supported by the EXP-061 design rationale); (iii) ≥ 30
  qualifying events per cell is sufficient for bootstrap stability (the power floor established at
  G0).
- **Expected output**: Per-cell × per-arm table with `E_cell_median`, `CI_low`, `CI_high`
  (one-sided 95%), `n_qualifying`, `n_censored`, `n_warmup_excluded`. Per-cell viability flag:
  `median_viable = (CI_low > 0) AND (n_qualifying ≥ 30)`. Populated in
  `per_cell_expectancy.parquet`.
- **Note on N-V2A×ADV-NONE qualifying count**: because there is no adverse stop, events that
  would have been stopped-out in N-PARTIAL-V2A remain active until the MA cap. This may slightly
  increase qualifying counts vs N-PARTIAL-V2A (no stop-out induced censoring), but may increase
  negative-return events (previously stopped-out adverse moves are now fully absorbed). The two
  qualifying count differences are disclosed; no post-hoc comparison is made.

---

### Step 2 — Per-cell Mean + Trimmed Mean + Tail-Share Bootstrap CI (P4 Co-primary; G-015 Binding)

- **Method**: Regime-clustered moving-block bootstrap CI on the raw mean, the 10% trimmed mean,
  and the worst-5% tail-share, per cell per arm. The **raw mean CI** is the G-015 co-primary
  (binding for PROCEED_TO_SCREEN); the trimmed mean and tail-share diagnose the P4 closure rule
  (CHARACTERISED_NOT_VIABLE vs MEAN_RECOVERABLE).
- **Why this method**: The mean is included in the G-015 conjunction because the Phase 015 D0
  motivating question is whether bounded-downside and/or partial-exit geometry can recover the
  negative mean seen in EXP-060B (mean ≈ 0 at benchmark). The raw mean CI directly answers
  "is the mean positive and stable?". The trimmed mean strips the worst-5% tail (the P4 closure
  rule: if trimmed mean is also negative, the mean deficit is structural, not tail-driven).
  The worst-5% tail-share quantifies how much of the negative mass sits in the extreme tail.
- **Simpler alternative considered**: Report the raw mean only without trimming. Rejected — the
  P4 closure rule explicitly requires all three to diagnose CHARACTERISED_NOT_VIABLE vs
  MEAN_RECOVERABLE–FOLLOW-UP. The three statistics together are the predeclared P4 package.
- **Assumptions**: Same regime-clustered bootstrap structure as Step 1. Trimmed mean: trim 10%
  from both tails by count (`m * 0.10` events removed each side; rounding per-cell); if the cell
  has < 10 events per tail-side, the trimmed mean is disclosed as unreliable (though the power
  floor of ≥ 30 makes this rare). Tail-share: `(sum of returns in worst-5% of events) / |sum of
  all negative returns|`; if no negative returns → tail-share = 0.0 (finite, not NaN).
- **Expected output**: Per-cell × per-arm: `E_cell_mean`, `mean_CI_low`, `mean_CI_high`;
  `E_cell_trimmed_mean`, `trimmed_CI_low`, `trimmed_CI_high`; `tail_share_worst5` (point
  estimate). G-015 co-primary flag: `mean_positive = (mean_CI_low > 0)`. P4 closure-rule
  flags: `trimmed_mean_negative = (trimmed_CI_high < 0)`, `tail_driven = (tail_share > 0.40)`
  (threshold pre-declared at EXP-063 P4 convention; if tail-share > 40% the deficit is
  tail-driven, MEAN_RECOVERABLE candidate). All in `per_cell_expectancy.parquet`.

---

### Step 3 — arm−RM Independent Contrast CI (P5 Signal Attribution; Binding)

- **Method**: Independent-samples bootstrap contrast CI on the difference in per-cell median
  expectancy between the champion arm and its matched-random-on-MA null (RM-native), using
  `xen.expectancy.contrast_ci`. One contrast per arm per cell.
- **Why this method**: The RM null is constructed with a different (non-harami) population of the
  same size, so the arm and RM samples are independent (no common events). The independent-samples
  contrast CI is therefore the correct form — the paired contrast would be inappropriate here
  (no event-level pairing). `CI_low > 0` means the champion arm's median exceeds the same-object
  null by a positive margin with 95% confidence — the P5 signal-attribution criterion.
- **Simpler alternative considered**: Mann-Whitney U test on event-level returns (arm vs RM).
  Considered but the scope mandates the bootstrap contrast CI (the predeclared EXP-060B/061/066
  method); the U-test would be a deviation from the programme standard. The contrast CI also
  directly quantifies the margin (the deliverable), not just the direction.
- **Assumptions**: (i) The RM null is constructed independently of the harami signal events
  (guaranteed by the exclusion of harami timestamps from the RM pool); (ii) matched-count holds
  per arm per cell (`n_RM = n_signal` for each arm) — verified by the invariant check; (iii)
  regime-clustered bootstrap blocks applied separately to signal and RM populations and the
  difference is computed per draw.
- **Expected output**: Per-cell × per-arm: `arm_rm_contrast`, `contrast_CI_low`,
  `contrast_CI_high` (one-sided 95%). Signal-attribution flag: `beats_rm = (contrast_CI_low > 0)`.
  In `per_cell_expectancy.parquet`.

---

### Step 4 — arm−Benchmark Paired Contrast CI (Disclosed Secondary; Context for G-015 Margin)

- **Method**: Paired-median bootstrap contrast CI (`xen.favourable_targets.paired_median_contrast_ci`)
  on the difference between each arm's per-event median expectancy and the N-BENCH arm's, using the
  **common qualifying-event subset** (events that qualify in both the arm and N-BENCH).
- **Why this method**: The benchmark contrast contextualises the champion margin vs the simple
  single-leg exit — confirming that the champion arm adds expectancy over the baseline, not merely
  over the null. It is **not a G-015 criterion** (the G-015 conjunction does not require
  arm > benchmark; only arm > RM and arm > 0 on both endpoints). It is disclosed secondary context
  supporting the surface synthesis, and is required by the P11 composition logic for the champion
  map.
- **Simpler alternative considered**: Independent contrast (not paired). Rejected for the
  arm−benchmark contrast: many events are shared between N-BENCH and N-PARTIAL-V2A (identical
  conditioning population; only exit path differs), so the paired approach on the common subset
  appropriately removes event-level noise that is common to both. N-V2A×ADV-NONE shares the same
  entry events but potentially different qualifying counts (no stop-out censoring); the common
  subset removes censored events that differ.
- **Assumptions**: Common qualifying-event subset defined as events that both qualify in the arm
  and in N-BENCH (valid construction, non-censored in both). If the common subset < 30, the paired
  contrast is `NOT_VIABLE-by-power` (disclosed); this is a secondary metric and does not gate
  G-015.
- **Expected output**: Per-cell × per-arm (arms 2 and 3 vs benchmark arm 1):
  `arm_bench_contrast`, `bench_contrast_CI_low`, `bench_contrast_CI_high`. Flag:
  `beats_bench = (bench_contrast_CI_low > 0)`. In `per_cell_expectancy.parquet`.

---

### Step 5 — G-015 Conjunction Evaluation and P11+P6 Composition

- **Method**: Per-cell boolean conjunction of the three binding flags, followed by the P11+P6
  counting rule.
- **Why this method**: The G-015 criterion is a pre-declared conjunction (median AND mean AND RM
  simultaneously). No statistical test is needed — the conjunction is evaluated from the already-
  computed bootstrap CI flags (Steps 1–3). P11+P6 is a counting rule, not a test.
- **Simpler alternative considered**: Report each criterion separately without the conjunction.
  Rejected — the G-015 predeclaration requires the simultaneous conjunction; separate reporting
  would be misleading. The conjunction is disclosed alongside individual criterion counts.
- **Expected output**: Per-cell × per-arm: `g015_passes = median_viable AND mean_positive AND
  beats_rm` (boolean). Then: per-arm P11+P6 tally =
  `(n_g015_passes, n_instruments_passing, n_non4h_g015_passes)` — with the G-015 PROCEED
  criterion `n_g015_passes ≥ 5 AND n_instruments_passing ≥ 3 AND n_non4h_g015_passes ≥ 3`.
  Also disclosed individually (not part of G-015): `n_median_viable`, `n_mean_positive`,
  `n_beats_rm` per arm at P11+P6, and the EVIDENCE_FOR status (`median_viable AND beats_rm AND
  beats_bench`, the S3 criterion from EXP-066 for comparison). In `champion_map.csv` and
  `g015_verdict.json`.

---

### Step 6 — P4 Closure-Rule Evaluation (CHARACTERISED_NOT_VIABLE vs MEAN_RECOVERABLE)

- **Method**: Rule-based classification using the per-cell mean/trimmed-mean/tail-share outputs
  from Step 2, applied globally (over all cells of the strongest arm) to identify the failure
  mode if no arm clears the G-015 conjunction.
- **Why this method**: The P4 closure rule is predeclared and deterministic given the Step 2
  outputs; no additional statistical method is needed.
- **Expected output** (disclosed in `g015_verdict.json`, relevant only if G-015 fails):
  - For each arm: the count of cells where `trimmed_mean_negative AND mean_negative` (structural
    deficit) vs `mean_negative AND tail_driven` (tail artefact, MEAN_RECOVERABLE candidate).
  - Overall P4 closure assessment: `STRUCTURAL` if, across the champion arms, trimmed mean is
    negative in the majority of powered cells AND tail-share ≤ 40%; `TAIL_DRIVEN` if tail-share
    > 40% in the majority of powered cells; `PARTIAL_RECOVERY` if mean is positive but not
    concurrent with median-viable AND beats-RM at P11+P6.

---

### Step 7 — Hybrid Champion Disclosed Summary

- **Method**: Tabular summary from EXP-061–066 surface read results, populated into
  `secondary_map.csv` and the `disclosed_hybrid` section of `g015_verdict.json`.
- **Expected output**:
  - Per-layer hybrid result table: EXP-061 H0 (1 cell, EVIDENCE_AGAINST); EXP-063 hybrid
    (EVIDENCE_AGAINST); EXP-064 hybrid (EVIDENCE_AGAINST, 0/7 variants); EXP-065 hybrid
    (INCONCLUSIVE, power-limited); EXP-066 H-PARTIAL-V2A (EVIDENCE_AGAINST, 0 arms at P11).
  - EXP-067 hybrid combined champion result: populated when available (PLANNED at EXP-068 scope
    time); if not yet available, noted as `EXP-067 PENDING`.
  - Cross-object comparison: native G-015 verdict vs disclosed hybrid surface summary — is the
    edge an object-specific or substrate-general property?

---

## Visualisations (max 4)

**1. Per-arm median-expectancy forest plot (per cell, native; headline)**
- Type: Forest/CI dot plot.
- X-axis: `E_cell_median` in ATR units. Y-axis: 99 cells (instrument × domain), sorted by domain
  then instrument. Three series: N-BENCH (grey), N-PARTIAL-V2A (blue), N-V2A×ADV-NONE (orange).
  Error bars = bootstrap 95% CI_low/CI_high. Zero line dashed. Non-4h cells highlighted.
- What it shows: per-cell median viability for each arm; where the champion arms exceed the
  benchmark; the G-015 conjunction cells (flagged where all three criteria pass simultaneously).
- Sub-question answered: "Which cells drive the champion arm's composition? Is the excess over
  benchmark consistent with the S3 finding of 21 cells for N-PARTIAL-V2A?"

**2. arm−RM contrast heatmap (arms × cells; G-015 overlay)**
- Type: Heatmap. Rows = 3 arms (N-BENCH, N-PARTIAL-V2A, N-V2A×ADV-NONE). Columns = 99 cells
  (instrument × domain groups). Cell colour = `contrast_CI_low` (RM margin lower bound; blue=
  positive, red=negative/zero). White hatching on cells where `g015_passes = True`. 4h-domain
  cells marked with a border.
- What it shows: where each arm beats RM-native (P5 signal attribution); how the ADV-NONE arm
  compares to PARTIAL-V2A on signal attribution; which cells simultaneously satisfy the G-015
  conjunction (hatched).
- Sub-question answered: "Does N-V2A×ADV-NONE maintain or improve signal attribution over N-
  PARTIAL-V2A? Does ADV-NONE broaden or narrow the set of RM-beating cells?"

**3. Median vs raw mean vs 10% trimmed mean — P4 G-015 co-primary diagnostic (per arm)**
- Type: Three-panel scatter plot (one panel per champion arm). X-axis: per-cell median ATR
  expectancy. Y-axis: raw mean ATR expectancy. Second y-axis overlay (or side-by-side): trimmed
  mean. Points coloured by `g015_passes` status (green=full conjunction, yellow=median only,
  red=neither). Zero lines on both axes. Worst-5% tail-share encoded as point size.
- What it shows: the per-cell relationship between median and mean viability; whether mean-positive
  and median-viable cells coincide; the tail-share structure driving mean deficits.
- Sub-question answered: "Where does the mean fail to accompany the median? Is the mean failure
  structural (trimmed mean also negative) or tail-driven (large tail-share)? Does N-V2A×ADV-NONE
  recover the mean relative to N-PARTIAL-V2A by removing the adverse stop, consistent with the
  EXP-060B V2A×ADV-NONE champion observation?"

**4. G-015 conjunction summary — per-arm criterion tallies at P11+P6**
- Type: Grouped horizontal bar chart. Three bars per arm (median-viable, mean-positive, beats-RM,
  all-three / G-015 passes) showing the count of qualifying cells at P11+P6 (out of 99), with
  the ≥ 5 cell threshold marked. Instrument count and non-4h cell count annotated for the
  all-three bar. Also shows the S3 EVIDENCE_FOR criterion (median-viable AND beats-RM AND
  beats-bench) as a reference bar for N-PARTIAL-V2A.
- What it shows: the effect of adding the mean-positive requirement to the S3 composition
  (i.e., how many cells that were median-viable AND beats-RM in EXP-066 also satisfy mean-
  positive); which arm, if any, satisfies the full G-015 conjunction at P11+P6; whether the
  mean criterion is the bottleneck.
- Sub-question answered: "How many of EXP-066's 21 N-PARTIAL-V2A cells survive the G-015
  conjunction? Does N-V2A×ADV-NONE produce more mean-positive cells by removing the adverse stop?"

---

## Implementation Safety Constraints

The following constraints must be honoured by `experiment-developer` (EXP-066 conventions
carried forward):

1. **Timestamp ordering**: All views (MA segments, ZigZag, HA candles, real bars) aligned by
   `CloseTime`. Never by bar index. The `H-BENCH` P12 check arm must verify
   `ma["entry_idx"]` alignment with `zz["entry_idx"]` via `CloseTime` join before applying
   the hybrid conditioning mask.

2. **TRAIN slice — holdout never read**: `scan.slice(0, train_rows)` only; `analysis_rows =
   int(total*0.7)`; `train_rows = int(analysis_rows*0.7)`. Forward scans clipped to
   `CloseTime ≤ train_end_ts`. Any window truncated before resolution → `DATA_CENSORED`
   (excluded with record).

3. **N-V2A×ADV-NONE implementation safety**: the no-adverse-stop branch must ensure that
   (a) no stop level is set or referenced during the forward scan for events in this arm,
   (b) every event's position resolves to a finite P15 exit (leg target touch or MA cap close)
   — an event with a window that ends before any leg target is reached is `DATA_CENSORED`, and
   (c) the invariant check confirms zero stop-out exits in this arm's records. Any stop-out
   record in N-V2A×ADV-NONE output → pipeline defect.

4. **Matched-count invariant**: each arm's RM-native count must equal the signal arm's qualifying
   count per cell. Verified per cell before bootstrap; mismatch → `INVARIANT_FAIL` (stops the
   run for that cell, disclosed in output).

5. **Fixed per-cell RNG seed (P3)**: `np.random.default_rng([BASE_SEED, cell_index, purpose])`
   where `purpose` values are distinct per arm/statistic combination and do NOT overlap with
   EXP-061/066 purpose assignments (so N-BENCH and N-PARTIAL-V2A existing RNG streams stay
   byte-identical to EXP-061/066).

6. **P12 reconciliation check before any result reporting**: load EXP-061 `M0`/EXP-060B
   `BENCH-MA` and EXP-066 `M-PARTIAL-V2A` reference files from fixed paths/hashes recorded in
   `run_metadata.json`; compute per-cell max absolute difference; assert ≤ 1e-9 for all 99 cells;
   stop with `SUBSTRATE/METHOD_DEFECT` if any cell fails.

7. **Bounded memory**: per-cell arrays released after per-cell summary is collected. No
   full-dataset materialisation before the holdout split. Per-event forward-scan windows are
   bounded by `bench_N` (the MA cap). Bootstrap draws are not stored beyond the CI computation.

8. **Progress**: `tqdm` over the 99-cell outer loop; logged progress to stderr (not stdout to
   avoid log mixing with result tables). `ProcessPoolExecutor` per-instrument worker (≤ `--workers`
   argument) with fixed-order reassembly for byte-identical multi-worker output.

9. **Zero-baseline for tail-share**: if no negative return events in a cell → tail-share = 0.0
   (not NaN/inf). If trimmed mean computation results in < 1 event per tail side →
   `trimmed_mean_unreliable = True` (disclosed flag in output; the trimmed mean is still computed
   and reported).

10. **Output directories created only in orchestration** (not at import time).

---

## Interpretation Guide

### G-015 Conjunction Outcomes (per arm, then overall)

**PROCEED_TO_SCREEN (G-015):**
- At least one arm has ≥ 5 cells over ≥ 3 instruments (≥ 3 non-4h) where `g015_passes = True`.
- Meaning: the native combined champion satisfies the G-015 criterion; the G-015 gate can
  adjudicate PROCEED for the native object. The qualifying arm, RM margin, and the mean+trim
  diagnostic are the candidate definition.
- The conjunction is tight — EXP-066 PARTIAL-V2A had 21 median-viable/beats-RM cells and 11
  mean-positive cells. If the mean-positive cells overlap sufficiently with the median-viable/
  beats-RM cells and at least 5 are non-4h, the criterion is met. If N-V2A×ADV-NONE produces
  more mean-positive cells (by not absorbing adverse tails), the ADV-NONE arm may be the
  qualifying champion.

**CHARACTERISED_NOT_VIABLE:**
- No arm has ≥ 5 `g015_passes` cells at P11+P6.
- P4 closure-rule classification: `trimmed_mean_negative` AND `tail_share ≤ 0.40` in the majority
  of powered cells across the best arm → structural mean-irrecoverability → feeds G-015
  CHARACTERISED_NOT_VIABLE (native side).
- Distinction from EVIDENCE_FOR (S3): if N-PARTIAL-V2A has ≥ 5 cells with `median_viable AND
  beats_rm AND beats_bench` but < 5 cells with `mean_positive` simultaneously, the arm is
  surface-positive (replicates EXP-066 EVIDENCE_FOR) but does not satisfy the G-015 conjunction.
  Report both statuses to distinguish the surface finding from the G-015 verdict.

**MEAN_RECOVERABLE–FOLLOW-UP:**
- No arm at P11+P6 `g015_passes`, but the mean failure is tail-driven (`tail_share > 0.40`
  in the majority of powered cells) or mean-positive in isolation without median+RM composition.
  The negative mean is not structural → family stays OPEN.

**INCONCLUSIVE (power-limited):**
- Fewer than 5 cells have ≥ 30 qualifying events on one or more arms. Disclosed per arm; never
  defaulted to a ratio or forced into a category.

**SUBSTRATE/METHOD_DEFECT:**
- Any P12 reconciliation failure (max diff > 1e-9 for N-BENCH or N-PARTIAL-V2A) or determinism
  failure (two-pass mismatch). Pipeline must be fixed; results invalidated.

### Cross-arm diagnostic questions

- **Does N-V2A×ADV-NONE improve the mean over N-PARTIAL-V2A?** If `E_cell_mean` for
  N-V2A×ADV-NONE is higher per cell (especially in cells where N-PARTIAL-V2A is mean-negative),
  the adverse stop was absorbing returns that partial-leg scaling can access; ADV-NONE removes
  that ceiling at the cost of potentially larger adverse tails. The tail-share diagnostic reveals
  whether the tail cost materialises.
- **Does N-V2A×ADV-NONE hurt the median relative to N-PARTIAL-V2A?** If median falls (more
  cells not viable) but mean rises, the distribution has become more skewed-positive — the mean
  improvement comes from a fewer-but-larger winner profile. This is informative for G-015 (which
  requires both median AND mean to be positive simultaneously per cell).
- **Is the mean-positive requirement the bottleneck for N-PARTIAL-V2A?** Compare
  `n_median_viable AND beats_rm` (the S3 criterion count, replicating EXP-066's 21 cells) with
  `n_g015_passes` (adds mean-positive). If the gap is large, the mean is not recovered by the
  S3 champion; ADV-NONE is the key test for whether partial-exit scaling can recover it.

---

## Complexity Check

| Dimension | Planned | Budget |
|-----------|---------|--------|
| Statistical methods | 4 (median CI, mean+trimmed+tail-share CI, arm−RM contrast CI, arm−benchmark paired contrast CI) | ≤ 4 |
| Visualisations | 4 (forest plot, contrast heatmap, median/mean P4 diagnostic, G-015 conjunction summary) | ≤ 4 |
| New code modules | 0 (fork EXP-066; ADV-NONE branch is a flag within existing partial-exit resolver) | ≤ 1 |

Plan fits the complexity budget. The analysis is a direct extension of EXP-066's validated
methodology, reduced to 3 champion arms with an extended G-015 conjunction evaluation and one
novel arm (N-V2A×ADV-NONE) whose implementation delta is a conditional branch in the existing
resolver.
