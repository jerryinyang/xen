# Analysis Plan: Experiment EXP-044

## Objective

Measure, for each of the **50 READY cells** from EXP-043 (17 instruments ×
{1h, 2h, 4h}, minus JP225-2h), whether the **frozen EXP-027 event-level
inference** — per-event direction-signed matched-control excess (bps),
regime-cluster bootstrap CI, stratified paired sign-permutation p, the
Evidence-FOR rule — applied **standalone per cell** (single instrument,
single domain; no cross-instrument aggregation, no cross-domain Holm), has
**controlled per-cell FPR** (≤ α₀ = 0.05 under two structurally different
nulls) and **recovery** (a finite per-cell event-level MDE at TPR ≥ 0.80) at
that cell's **realized TRAIN event count** (EXP-043 `power_statement.csv`:
32–273 events). The output is a **per-cell coverage map** that adjudicates
G1 leg (ii) (Phase 011 design §8.2) and supplies the MDE-vs-count power
context for Tracks B and D.

This is EXP-027 re-run at the per-cell unit on the Phase 011 grid: same
nulls-on-real-scaffold construction, same frozen decision rule, with the
instrument-aggregation and Holm steps removed (predeclared here) and the
event count pinned to each cell's realized TRAIN population.

## Reused vs. new components

| Component | Source | Status in EXP-044 |
| --- | --- | --- |
| F01-compliant TRAIN load (file-order `floor(0.7·floor(0.7·total))` rows), domain-bar construction (1h/2h/4h, `min_coverage=0.90`) | EXP-043 `code/run_experiment.py` | reused by copy/import, unchanged (the certified substrate path) |
| Frozen baseline event/regime generation (`generate_avwap_events` defaults) | `xen.avwap` (frozen) | reused unchanged — regenerates the EXP-043-certified scaffolding bit-for-bit; **event outcomes never read** |
| Stationary-block resampling, block-length estimation, `percentile_ci`, `seed_for` | `xen.referee_calibration` | imported unchanged (null #2 + CI utilities) |
| Matched-control construction (same `regime_id`, not-trigger, exclusion window, ≥3/≤5 by nearest anchor age then timestamp), `signed_log_bps` | EXP-027 `code/` (EXP-021 lineage) | reused by copy, unchanged in semantics |
| Bootstrap CI, sign-permutation p, Evidence-FOR rule | EXP-027 `code/` | reused **unchanged in structure**, evaluated per cell (single instrument; **no `domain_effect` equal-weight step, no `holm_adjust`**) |
| Per-cell sparse placebo/planted-edge substrate at realized counts; coverage-map classifier | new | the experiment-local helper (1 module budget) |

No new or modified `python/src/xen/` module.

## Methodology

### Step 1: Dependency gates and scaffolding (no real event outcomes)

- **Method**: Hard-fail unless EXP-043 `run_metadata.json` records
  READINESS_DELIVERED with `substrate_alert: false`; load
  `readiness_map.csv` and `power_statement.csv`, cross-check that their
  READY sets agree, contain exactly 50 cells, and exclude JP225-2h.
  **Source-identity binding**: each instrument's source file name, total
  row count, TRAIN row count, and TRAIN-end timestamp are asserted against
  the EXP-043 `boundaries` record — event-count equality alone is not a
  substrate guarantee if files are recollected or drift. Regenerate per
  cell the frozen-baseline regime intervals and event-trigger locations on
  TRAIN bars exactly as EXP-043 did (same loader, same generator
  defaults), and assert the regenerated event count equals the EXP-043
  realized count (consistency gate, hard-fail per cell on mismatch).
- **Anti-overfitting fence (binding)**: real event **outcomes** (forward
  returns, completions, targets) are never computed or read for the real
  triggers; only regime intervals, anchor ages, trigger **locations** (to
  exclude them from control pools and placement), and realized **counts**
  enter. The signal under test is entirely synthetic.
- **Why**: the calibration must run on the exact certified Phase 011
  scaffolding for its verdicts to transfer; reading real outcomes would
  make this a candidate screen.
- **Simpler alternative**: synthetic regimes — rejected; per-cell cluster
  structure (few, uneven regimes: 35–300 per cell) is precisely what is
  being stress-tested.
- **Output**: validated per-cell scaffolding; gate confirmations in
  `run_metadata.json`.

### Step 2: Holdout-safe precompute

- **Method**: Per cell, precompute once: `log(Close)`; direction-signed
  forward `H_cal`-bar return for every bar (`signed_log_bps`); per-regime
  eligible control/placement pools (not a real trigger, outside the
  exclusion window, enough future bars for `H_cal`); anchor age per bar.
  **Fence enforcement, literal**: forward outcomes at real trigger bars
  are NaN-masked in both the real (N1) and block-permuted (N2) outcome
  arrays — pools already exclude those bars, and the mask makes any
  accidental gather propagate loudly instead of leaking silently.
  TRAIN-only rows (F01 slice before any construction); TEST and the final
  30% holdout never touched; assert every regime index lands in the TRAIN
  frame.
- **Calibration outcome window `H_cal` = 8 completed domain bars**
  (primary and only). Rationale: the gate operates on a per-event scalar
  excess, so operating characteristics transfer across hold definitions
  (EXP-027 finding: H=3 vs H=6 FPR both controlled — horizon-insensitive);
  H=8 is the interior centre of the Phase 011 FH grid {2,…,23} and so
  matches the Track B hold scale. A second-horizon robustness leg is
  dropped as already answered by EXP-027 (simplicity over duplication).
- **Output**: per-cell arrays in memory; fence confirmations in metadata.

### Step 3: Per-cell sparse synthetic substrate

- **Calibration point = the cell's realized event population** (no
  activity grid, no tiers): per draw, place **exactly** `n_bull(cell)` and
  `n_bear(cell)` placebo triggers (EXP-043 realized TRAIN counts) within
  the cell's real regime intervals. Each direction's target is distributed
  across that direction's regime pools by deterministic largest-remainder
  allocation (proportional to pool size, caps redistributed), then placed
  with the EXP-027 clustered mechanism (uniform seeds plus pyramid
  follow-ons within ±span; intensity the same predeclared structural
  parameter as EXP-027, never fit to real locations). Pyramid follow-ons
  are restricted to membership in the **generating regime's pool** (never
  an adjacent regime, which would distort the direction mix); collisions
  are topped up with uniform in-pool picks so the placed count is exact.
  Placed counts per direction are recorded per draw
  (`placement_exact` flag); a shortfall is possible only when a
  direction's pools are smaller than its target, and is disclosed, never
  silent. Direction mix therefore matches the realized bull/bear split
  exactly (stressing per-direction reportability where it is thin, e.g.
  JP225-4h 11/21).
- **Null generators (2, structurally different)**:
  - **N1 placebo-on-real**: placebo triggers on real TRAIN returns, no
    planted edge; matched-control subtraction makes the true per-event
    excess exactly 0.
  - **N2 block-permuted**: identical placement; per-bar log returns
    stationary-block resampled per instrument (block length estimated on
    TRAIN) before forward returns are formed — two-null agreement,
    EXP-001/027 precedent.
- **Planted edge (recovery)**: on N1, add a known direction-signed drift
  `g` to each placebo event's `H_cal` outcome (controls untouched); true
  per-event excess = `g`. **Edge grid `g ∈ {1, 2, 4, 8, 16, 32, 64, 128}
  bps** (geometric; extends EXP-027's grid by 128 because thin 4h cells
  (32–55 events) plausibly carry MDEs above 64 bps — declaring the wider
  endpoint now avoids post-hoc grid extension). `g = 0` reuses the N1
  null cell.
- **Draws**: **500 per (cell × generator)** and **500 per (cell × g)**;
  seeds via `seed_for(EXP-044, instrument, domain, generator_or_g,
  draw_index, purpose)`. 500 draws gives Wilson 95% half-width ≈ 0.019 at
  FPR = 0.05 (≤ 0.03 threshold) and ≈ 0.035 at TPR = 0.80 (≤ 0.05
  threshold) — the precision gates are met by construction when all draws
  complete.
- **Bounded-compute truncation — not used (justification)**: the rule
  ("skip higher `g` after two consecutive TPR = 1.000 points") was defined
  for a `g`-outer-loop design. The implementation evaluates all edges per
  draw instead: the expensive simulation and bootstrap run **once** per
  draw at `g = 0` (a planted edge shifts the effect and percentile CI by
  exactly +`g`), and only the cheap per-edge sign permutation repeats.
  Truncating would require cross-draw state for a minority of the compute,
  so all grid points are measured. This is a compute-structure choice
  only; no predeclared statistical object changes.
- **Why**: realized-count placement answers the exact §8.2 question — does
  inference work *on this cell's population* — without a tier mapping's
  approximation. The conservative-tier option in the scope is therefore
  not used.
- **Output**: per-draw event/control sets feeding Step 4 (only bounded
  per-draw verdict rows persisted).

### Step 4: Per-draw, per-cell decision pipeline (frozen rule, aggregation removed)

Per draw: matched controls per placebo event (same `regime_id`, not a
trigger, outside the 6-bar exclusion window, ≥3 required / ≤5 selected by
nearest anchor age then timestamp — `MIN_CONTROLS=3`, `MAX_CONTROLS=5`,
`EXCLUSION_BARS=6`, all EXP-027 values); per-event paired diff
`event − mean(controls)` on precomputed `H_cal` signed returns; **cell
effect = event-weighted mean paired diff** (single instrument — the
`domain_effect` equal-weight step has no object and is removed); 95%
regime-cluster bootstrap CI (`N_BOOT=1000`, resampling `regime_id`
clusters within direction strata); stratified paired sign-permutation p
(`N_PERM=1000`); verdict **FOR ⇔ effect > 0 ∧ CI_low > 0 ∧ raw p ≤ α**
(no Holm in-experiment — single-cell unit; the Track D Holm-5 correction
is a G3 object applied later and can only *reduce* false positives, so the
per-cell α₀ map measured here is conservative for G3 use).

**Per-draw reportability (per-cell analog of EXP-021's rule)**: ≥30
reportable matched events **and** ≥8 per direction; the ≥3-of-4-instruments
leg is dropped (no instrument aggregation). Failing draws are recorded
`UNDER_POWERED` and excluded from FPR/TPR numerators and denominators.
**Draw-completion floor**: a (cell × generator) or (cell × g) point is
usable only if **≥90% of its 500 draws are reportable**; otherwise the
point — and, if it is a null point, the cell — is classified
CALIBRATION_UNDERPOWERED with the completion rate recorded.

- **Output**: `draw_verdicts.parquet` (cell, generator/g, draw, effect,
  CI, p, decision, reportability; bounded columns).

### Step 5: Per-cell operating characteristics and coverage classification

- **FPR** per (cell, generator, α ∈ {0.10, 0.05, 0.01}; primary 0.05) =
  fraction of reportable null draws FOR, with Wilson 95% intervals.
  **TPR** per (cell, g, α) likewise. **Per-cell event-level MDE**(α₀) =
  smallest `g` with TPR ≥ 0.80 while the cell's FPR ≤ α₀ under **both**
  nulls; non-finite (`null`, never 0) if no grid point qualifies.
- **Precision gate**: FPR Wilson half-width ≤ 0.03 and TPR half-width
  ≤ 0.05 (met at 500 complete draws; re-checked on realized reportable
  counts).
- **Coverage classification (the G1 leg (ii) object)** — exhaustive and
  binary-gate-unambiguous:
  - **COVERED**: both nulls' FPR point estimates ≤ α₀
    (Wilson-precision-adequate) **and** finite MDE — MDE value recorded;
  - **NOT_COVERED**: at adequate precision, an FPR point estimate above α₀
    under either generator (reason flagged `material` when the Wilson 95%
    lower bound also exceeds α₀, `adequate_precision` otherwise — the
    point-estimate criterion decides; the flag grades severity), **or**
    no finite MDE on the grid;
  - **CALIBRATION_UNDERPOWERED**: reserved strictly for precision or
    draw-completion floor shortfalls (variance problems, fixable by a
    precision-only re-run), never for point-estimate failures.
  The coverage map also records per-cell diagnostics: regimes per
  direction, block length, and allocated placement counts.
- **Substrate-level check (METHOD_NOT_TRANSFERABLE trigger)**: two-null
  FPR disagreement = non-overlapping Wilson 95% intervals at α₀ with both
  points precision-adequate; the AGAINST trigger is disagreement in ≥3
  instruments, or Wilson-lower-bound FPR > α₀ across **every**
  precision-adequate cell of an entire domain.
- **Output**: `fpr_per_cell.csv`, `tpr_mde_per_cell.csv`,
  `coverage_map.csv` (verdict + machine-readable reason per cell).

### Step 6: Determinism replay and metadata

Re-run two fixed cells (one high-count 1h, one thin 4h) with identical
seeds; assert frame-identical per-draw verdicts and identical FPR/TPR/MDE
(`determinism_pass`). `run_metadata.json` records grid, seeds, counts,
truncation events, dependency/fence confirmations, per-cell headline, and
the experiment verdict per the scope (CALIBRATION_DELIVERED /
METHOD_NOT_TRANSFERABLE / INCONCLUSIVE, with the >1/3-underpowered rule).

## Visualisations (5 / 5 budget)

1. **Per-cell FPR heatmap** (17×3 grid, faceted by null generator, α₀
   reference) — the error-control read.
2. **Per-cell MDE heatmap** (17×3, finite values annotated, NOT_COVERED /
   UNDERPOWERED hatched) — the recovery read and the Track B/D power map.
3. **MDE vs realized event count** scatter by domain (log-log, one point
   per cell) — where per-cell inference stops working as counts fall.
4. **Calibration-precision / completion diagnostic** — Wilson half-widths
   and draw-completion rates across cells.
5. **Coverage-verdict summary** — COVERED / NOT_COVERED /
   CALIBRATION_UNDERPOWERED counts and the G1-leg-(ii) headline.

## Interpretation Guide

- **CALIBRATION_DELIVERED** (Evidence FOR): every cell classified, MDE
  table recorded, determinism PASS. The COVERED set defines the cells G1
  leg (ii) admits to Track B; NOT_COVERED cells are excluded with record
  (a NOT_COVERED thin-4h tail is a valid, expected outcome — information,
  not defect). G1 adjudication 2 of 2 then closes in
  `G1-gate-review.md` against `coverage_map.csv`.
- **METHOD_NOT_TRANSFERABLE** (Evidence AGAINST, substrate-level): two-null
  disagreement in ≥3 instruments or domain-wide FPR excess per Step 5 —
  the per-cell application itself is invalid; G1 cannot close; operator
  review before any Track B work.
- **INCONCLUSIVE**: >1/3 of cells CALIBRATION_UNDERPOWERED — operator
  decides precision-only re-run (more draws, no object change) vs reduced
  Track B grid.
- Report bps differences and absolute rates with CIs; non-finite MDE
  reported as such; never a percentage over the 0-bps null baseline.

**Predeclared interpretation caveats (read before any verdict):**

1. **Horizon-transfer assumption.** The map is calibrated at the single
   scalar window H_cal = 8. EXP-027 showed FPR control at H = 3 and H = 6
   at pooled-domain scale only; H = 8 and the per-cell unit are an
   extrapolation of that finding, and Track B/D exits span FH {2,…,23} and
   MAD-band-target durations. A COVERED verdict certifies the **inference
   machinery on this cell's event population at a representative scalar
   per-event excess**, not every exit-specific outcome window.
   **Post-G1 validation item**: if Track D selects cells whose trained
   exits sit far from H≈8 (especially thin 4h cells), a targeted
   second-horizon FPR check on those specific cells is the predeclared
   follow-up before the binding TEST read — a new scope, not a rerun.
2. **N2 is a different dependence structure, not the same structure with
   different noise.** N2 keeps the real regime placement/control geometry
   but block-permutes the return series, breaking contemporaneous
   regime-level variance structure — an intentional hybrid (EXP-001/027
   two-null precedent, validated at pooled scale). If the two nulls
   disagree, first check whether N2 excess correlates with low per-cell
   regime counts (fewer regimes → more permutation distortion) before
   reading disagreement as METHOD_NOT_TRANSFERABLE; a regime-count-graded
   pattern points to a block-permutation artifact, a flat pattern to a
   genuine method failure.
3. **Small-regime bootstrap coverage.** The regime-cluster bootstrap CI is
   part of the frozen rule under test; its coverage degrades when a
   direction stratum has very few regimes, and that degradation shows up
   **in the measured FPR** — which is exactly what the calibration is for.
   Do not "fix" the CI method (metric-shopping); instead, read cells with
   < 5 regimes in either direction (see `n_regimes_bull/bear` in the
   coverage map) with the expectation that FPR excess there is plausibly a
   small-cluster bootstrap artifact, honestly disqualifying for that cell.
4. **Block length is estimated on per-bar returns** (first ACF lag < 1/e),
   the same construction EXP-027 used, while the test statistic lives on
   overlapping H_cal-bar windows. The likely error direction is a too-short
   block (anti-conservative N2 → FPR excess on N2 first), which the
   per-cell FPR measurement detects; `block_length` is recorded per cell
   for exactly this diagnosis.

## Implementation Safety Constraints

- **Per-event unit end-to-end**; denominators are reportable matched
  events and reportable draws — never bars. No per-bar suite or floor
  appears anywhere.
- **Fence**: real trigger outcomes never computed/read; planted drift
  touches outcomes only, never placement/matching; placement uses only
  bar-time regime/anchor-age/trigger-location information.
- **Holdout/TEST**: F01 TRAIN slice (file-order rows) before any
  construction; TEST stratum and final-30% holdout never loaded; regime
  indices re-asserted inside the TRAIN frame.
- **Real-price discipline**: direction-signed log bps on real domain
  `Close`; no costs/stops/sizing.
- **Determinism**: all randomness through `seed_for`; replay asserted on
  two cells.
- **Performance / vectorization**: precompute returns, pools, anchor ages
  once per cell; per draw = index selection + gather + chunked vectorized
  bootstrap/permutation (EXP-027 `BOOT_CHUNK`/`PERM_CHUNK` pattern).
  Control matching may be vectorized only if causally equivalent to the
  EXP-027 `select_controls` ordering (deterministic anchor-age →
  timestamp → row-index tie-break, identical sample membership).
  Optimizations must not change draw counts (except the predeclared
  TPR-truncation rule), sample membership, ordering, denominators, metric
  definitions, or the decision rule. ~50 cells × ≤5 000 draws × 2 000
  inner resamples is the budget ceiling; `tqdm` over the outer
  (cell × generator/edge) loop with per-cell postfix; concise logging;
  helpers return data.
- **No silent drops**: unreportable draws, truncated grid points, and
  consistency-gate failures are recorded with reasons.

## Complexity Check

- Statistical tests: **4 / 4** — regime-cluster bootstrap CI; stratified
  paired sign-permutation; Wilson FPR/TPR intervals; grid-defined per-cell
  MDE. (No Holm in-experiment; no equity companion in this scope.)
- Visualisations: **5 / 5** as listed.
- New modules: **1 / 1** experiment-local helper under
  `python/experiments/EXP-044/code/`.

## Expected Output Files

```text
python/experiments/EXP-044/results/
- coverage_map.csv        # per-cell COVERED / NOT_COVERED / CALIBRATION_UNDERPOWERED + reason
- fpr_per_cell.csv        # FPR by cell × generator × alpha, Wilson bounds, completion rates
- tpr_mde_per_cell.csv    # TPR by cell × g × alpha; per-cell MDE (finite or null)
- draw_verdicts.parquet   # bounded per-draw rows
- run_metadata.json       # status, gates, seeds, counts, truncations, determinism, verdict
python/experiments/EXP-044/plots/
- fpr_per_cell_heatmap.png
- mde_per_cell_heatmap.png
- mde_vs_event_count.png
- calibration_precision.png
- coverage_verdict_summary.png
```
