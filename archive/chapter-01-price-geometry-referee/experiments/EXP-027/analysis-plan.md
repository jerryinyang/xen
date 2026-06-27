# Analysis Plan: Experiment EXP-027

## Objective

Determine whether a predeclared **event-level** evaluation method — **per-event
matched-control expectancy** as the binding decision statistic (the EXP-021/022
regime-cluster bootstrap + stratified paired sign-permutation + Holm inference and
Evidence-FOR rule, reused unchanged in structure), with an exposure-aware
**equity-curve-vs-buy-hold companion** — has **controlled false-positive error**
(empirical FPR ≤ α₀ = 0.05 under known-null sparse event processes) and **recovery**
(a finite empirical **event-level MDE** at TPR ≥ 0.80 while FPR ≤ α₀) across the
5m / 1h / 4h domains, within the sparse activity envelope {~3 %, ~6 %, ~12 %}
trigger prevalence that brackets the real AVWAP signal.

This is the **event-level, sparse-activity analog of EXP-003/005**: the same
operating-characteristic logic (FPR / TPR / empirical MDE on synthetic null +
planted-edge draws), but the unit of analysis is the **event**, never the bar, and
the target regime is **sparse**, not ≥80 %-active. The method is calibrated only on
synthetic substrates and is **frozen before EXP-028 reads any real candidate
result**.

## Reused vs. new components

| Component | Source | Status in EXP-027 |
| --- | --- | --- |
| `seed_for`, `list_timebar_files`, `load_analysis_data`, `build_domain_frames`, `DOMAIN_SPECS` | `xen.referee_calibration` | imported unchanged (holdout-safe load + domain build) |
| `permuted_returns`, `estimate_block_length`, stationary-block resampling, `percentile_ci` | `xen.referee_calibration` | imported unchanged (null #2 + CI utilities) |
| Same-regime control construction (`build_exclusion_masks`, `regime_candidate_base`, `select_controls`, `signed_log_bps`) | EXP-021 `code/run_experiment.py` | reused by copy into the EXP-027 helper, **vectorized** but causally equivalent |
| `domain_effect`, `bootstrap_ci`, `permutation_p`, `holm_adjust`, `decide_verdict` (Evidence-FOR rule) | EXP-021 `code/run_experiment.py` | reused **unchanged in structure**; this is the decision rule being calibrated |
| Sparse synthetic-event substrate (placebo placement + planted-edge) | new | experiment-local helper, the only new logic |
| Exposure-aware equity-curve companion | new | experiment-local helper; non-gating |

No new or modified `python/src/xen/` module is introduced.

## Methodology

### Step 1: Dependency gate and scaffolding load (no event outcomes)

- **Method**: Assert the EXP-020 substrate gate exactly as EXP-021 does
  (`overall_status == SUPPORTED_FULL`, ready `{5m,1h,4h}`, zero invariant failures,
  deterministic replay) via `run_metadata.json`, `domain_readiness.csv`,
  `invariant_checks.csv`, `determinism_check.csv`. Load **only** the regime summary
  `avwap_state_summary.csv` (regime intervals: `regime_id`, `regime_start_idx`,
  `regime_end_idx`, `anchor_idx`, direction) as the matched-control scaffolding.
- **Anti-overfitting fence (binding)**: `avwap_events.csv` is **not** loaded for its
  bounce outcomes. The real per-event returns/locations are never read. Only (a) the
  regime intervals/anchor indices and (b) the documented aggregate activity rate
  (~6 %, used solely to centre the predeclared grid) inform EXP-027. The signal
  under test is entirely synthetic (placebo + planted-edge).
- **Why this method**: The inference being calibrated *is* EXP-021/022's; its
  scaffolding (regimes, anchor age) must be the real one for the calibration to
  speak to EXP-028. Reading real event outcomes would make this a candidate screen,
  not a method calibration — the exact metric-shopping the phase forbids.
- **Simpler alternative considered**: Fully synthetic regimes (no EXP-020). Rejected:
  the sparse-regime cluster structure (few, uneven regimes at 4h) is the crux of the
  calibration and must be real to be informative.
- **Assumptions**: EXP-020 regimes were produced inside the first-70 % analysis set
  (re-verified by the domain join in Step 2). Temporal authority is `CloseTime`.
- **Expected output**: validated regime tables in memory; dependency status in
  `run_metadata.json`.

### Step 2: Holdout-safe domain reconstruction and precompute

- **Method**: For each instrument, `load_analysis_data` (lazy first-70 % slice) then
  `build_domain_frames` → real 5m (strict) / 1h / 4h (`min_coverage=0.90`) `Close`
  arrays, identical to EXP-020/021. Re-assert the holdout fence and regime alignment
  by checking every `regime_*_idx` indexes a real bar in the first-70 % frame
  (hard-fail otherwise). **Precompute once per (instrument, domain)**: `log(Close)`;
  per-regime eligible-candidate index pools (`regime_candidate_base`, the same
  not-trigger / outside-exclusion logic but over all bars, since placebo triggers are
  assigned per draw); anchor age per bar; and the direction-signed `H_cal`-bar
  forward return for every bar (`signed_log_bps`). These precomputes are real-data,
  draw-independent, and let each draw reduce to index selection + gather.
- **Why this method**: real future `Close` outcomes with an independent holdout fence,
  and a precompute that makes thousands of draws tractable without changing any
  sample-membership or temporal semantics.
- **Simpler alternative considered**: recomputing returns/candidates inside each draw
  (EXP-021's one-shot style). Rejected on performance only — it repeats identical
  heavy work thousands of times; the precompute is numerically identical.
- **Assumptions**: forward returns are outcomes, never inputs to placement/matching.
- **Expected output**: per-cell precomputed arrays (in memory); holdout-fence and
  alignment confirmations in `run_metadata.json`.

### Step 3: Sparse synthetic-event substrate (placebo placement + nulls + planted edge)

- **Method**: Define the calibration grid:
  - **activity (placebo-trigger prevalence)** `p_trig ∈ {0.03, 0.06, 0.12}`, primary
    `0.06`; per cell, number of placebo triggers = `round(p_trig · n_eligible_bars)`,
    so per-domain event counts track the real ones (5m → thousands; 4h → ~100s),
    reproducing the realistic sparse sample size that drives the inference's behavior;
  - **null generators** (no planted edge):
    - **N1 placebo-on-real**: place placebo triggers within real regimes on real
      returns, allowing intra-regime clustering / short consecutive runs to emulate
      pyramids (clustering intensity a predeclared structural parameter informed by
      the documented aggregate pyramid share, **never** real event locations); the
      matched-control design removes regime drift, so the true per-event excess is 0;
    - **N2 block-permuted-returns**: identical placement, but the per-bar real log
      returns are stationary-block resampled per instrument (`estimate_block_length`
      on train + `permuted_returns`/stationary blocks from `xen.referee_calibration`)
      before forward returns are formed — breaks any incidental placement↔return
      dependence while preserving autocorrelation/vol-clustering scale (two-null
      agreement, EXP-001 precedent);
  - **planted-edge** (recovery): on the **N1** substrate at the **primary** activity
    `0.06`, add a known direction-signed additive drift `g` bps to each placebo
    event's `H_cal` outcome return (controls unchanged), so the true per-event excess
    equals `g`. Edge grid `g ∈ {0, 1, 2, 4, 8, 16, 32, 64}` bps (geometric, domain-
    agnostic, **decoupled from EXP-021's observed +3.8/+9.1/+37.6 magnitudes**);
    `g = 0` reuses the N1/0.06 null cell.
  - **calibration outcome window**: `H_cal = 3` completed domain bars (primary; the
    EXP-021-validated machinery) with `H_cal = 6` as an FPR-only robustness check. The
    gate operates on a per-event **scalar** excess, so its operating characteristics
    transfer to the variable lifetime hold EXP-028 will use; `H_cal` sets the units of
    the measured MDE, not the structural validity.
  - draws per cell = **500**; fixed seeds via
    `seed_for(EXPERIMENT_ID, domain, p_trig, null_or_edge, draw_index, purpose)`.
- **Why this method**: it is the EXP-003/005 paired null + planted-positive pattern
  translated to events. Two structurally different nulls bound accidental structure;
  the additive per-event drift is the closed-form per-event analog of EXP-005's
  latent-state drift; placement preserves the sparse cluster structure the
  regime-cluster bootstrap must cope with.
- **Simpler alternative considered**: a single uniform-random null without clustering.
  Rejected — it would under-stress the cluster bootstrap exactly where sparsity bites
  (4h), inflating apparent FPR control.
- **Assumptions**: placement and matching use only timestamp / regime / anchor-age
  known at the bar; the planted drift touches **outcomes only**, never placement or
  matching; the Bernoulli/clustered placement is independent of returns under nulls.
- **Expected output**: per-draw placebo event/control sets feeding Step 4 (not all
  persisted; bounded per-draw verdict rows persisted in `draw_verdicts.csv`).

### Step 4: Per-draw decision pipeline (REUSED EXP-021 inference, unchanged in structure)

- **Method**: For each draw, run the EXP-021 pipeline to a single per-domain verdict:
  1. **matched controls** per placebo event — same `regime_id`, not a placebo
     trigger, outside a 6-bar exclusion window of any placebo trigger, ≥ enough future
     bars for `H_cal`, ranked by nearest anchor age then nearest timestamp, ≤ 5
     selected, ≥ 3 required to be reportable (`MAX_CONTROLS=5`, `MIN_CONTROLS=3`,
     `EXCLUSION_BARS=6`);
  2. **per-event paired diff** `event_return_bps − mean(control_return_bps)` on the
     precomputed `H_cal` direction-signed returns;
  3. **domain effect** = equal-weight mean across reportable instruments of each
     instrument's event-weighted mean paired diff (`domain_effect`);
  4. **95 % regime-cluster bootstrap CI** (`bootstrap_ci`, `N_BOOT=1000`, resampling
     `regime_id` clusters within (instrument, direction) strata);
  5. **stratified paired sign-permutation p** (`permutation_p`, `N_PERM=1000`);
  6. **Holm across the 3 domains** (`holm_adjust`) within the draw;
  7. **per-domain verdict** via the EXP-021 Evidence-FOR rule (`decide_verdict`):
     `FOR ⇔ effect>0 ∧ CI_low>0 ∧ Holm_p ≤ α`; AGAINST/INCONCLUSIVE as defined there.
     Reportability thresholds (`≥30` events, `≥8`/direction, `≥3`/4 instruments)
     identical to EXP-021; a draw failing reportability in a domain is recorded
     `UNDER_POWERED`, not counted toward FOR/AGAINST.
- **Inner-resample count rationale**: EXP-021 used 10 000 for a single one-shot test;
  EXP-003/005 used 1 000 per verdict across many draws. EXP-027 follows the
  calibration convention (`1 000`) — a compute knob, **not** a structural change;
  permutation resolution `(1+ge)/(1+1000)≈10⁻³` clears α and the bootstrap CI is
  stable at this count.
- **Why this method**: the object being validated is precisely this decision rule;
  calibrating anything else would not speak to EXP-028.
- **Simpler alternative considered**: a per-event t-test / two-proportion test.
  Rejected for the same reasons EXP-021/022 rejected them (non-normal, clustered,
  repeated events within regimes).
- **Assumptions**: regime clusters are the dependence unit; instruments equal-weighted
  so a high-count instrument cannot redefine the domain (EXP-008 finding).
- **Expected output**: `draw_verdicts.csv` (per draw × domain: effect, CI, raw_p,
  Holm_p, decision, reportability).

### Step 5: Operating characteristics — FPR, TPR, event-level MDE

- **Method**:
  - **FPR** per (domain, `p_trig`, null generator, α) = fraction of adequately
    powered null draws with verdict `FOR`; also the **family-wise** any-domain FPR per
    draw. Wilson 95 % intervals on every rate.
  - **TPR** per (domain, `g`, α) at primary `p_trig=0.06` = fraction of adequately
    powered planted-edge draws with verdict `FOR`. Wilson intervals.
  - **event-level MDE** per (domain, α) = smallest `g` on the grid with
    `TPR ≥ 0.80` while the matched `FPR ≤ α₀`; **non-finite (no recovery)** if no grid
    point qualifies (reported as `null`/`inf`, never 0).
  - **precision gate**: a cell is usable only if FPR Wilson half-width ≤ 0.03 and TPR
    Wilson half-width ≤ 0.05; under-powered cells are reported and excluded from
    FOR/AGAINST claims (EXP-003/005 rule).
- **Why this method**: Wilson intervals are the established pass-rate uncertainty here;
  the grid-based empirical MDE is the EXP-003/005 recovery measure, decoupled from the
  real candidate (operator decision: "measure event-level MDE").
- **Simpler alternative considered**: a fixed economic recovery target or anchoring to
  EXP-021's effects. Rejected per scope — the former is arbitrary, the latter is
  metric-shopping against the real candidate.
- **Assumptions**: FPR/TPR are absolute proportions over draw verdicts; never a
  percentage over a zero baseline.
- **Expected output**: `fpr_summary.csv`, `tpr_summary.csv`, `mde_summary.csv`.

### Step 6: Exposure-aware equity-curve companion (non-gating)

- **Method**: Per (instrument, domain, draw), build the selective strategy's
  per-trade return series — direction-signed real `H_cal` log return on placebo-event
  trades, flat between — and the **exposure-matched baseline**: the same number of
  trades taken at the event's **matched-control** bars (identical hold, identical
  direction-signing). Aggregate both to cumulative log-equity curves. Summarize two
  statistics: (i) terminal log-equity difference `strategy − exposure-matched
  baseline`, with a regime-cluster bootstrap CI (reuses Step 4's `bootstrap_ci`
  machinery on this statistic — **no new test**); (ii) a downside-risk-adjusted ratio
  (mean per-trade return ÷ downside deviation, Sortino-style — the methods catalog
  prefers Sortino over Sharpe). The raw 100 %-invested **buy-hold** curve is plotted
  as original-metric-book **context only**, explicitly annotated as exposure-mismatched
  and therefore *not* the comparator — the exposure-matched baseline is the
  apples-to-apples object, which structurally prevents the per-bar dilution artifact
  from re-entering.
- **Calibration (non-gating)**: under the N1 null, report the fraction of draws with a
  spuriously positive terminal difference / advantage (companion false-advantage rate)
  — it should not systematically exceed chance; under planted edge, the advantage
  should grow with `g`. This is reported alongside the gate and informs interpretation
  but **does not decide METHOD_VALID**.
- **Why this method**: it realizes the original headline (equity vs buy-hold) on an
  exposure-matched / risk-adjusted basis, so a ~6 %-exposed curve is never naively
  compared to a 100 %-invested one — the precise mismatch the framing review flagged.
- **Simpler alternative considered**: raw terminal-return strategy-vs-buy-hold.
  Rejected — it reintroduces the exposure/dilution mismatch that broke EXP-023.
- **Assumptions**: log-return additivity for equity aggregation; downside deviation is
  finite (cells with degenerate dispersion → null ratio, reported, not zero).
- **Expected output**: `equity_companion_summary.csv`.

### Step 7: Determinism replay, validity-range verdict, metadata

- **Method**: Re-run one fixed (domain, `p_trig`, `g`) cell with identical seeds and
  assert byte-identical FPR/TPR (`determinism_pass`). Classify the **method verdict**:
  - **METHOD_VALID** if, in every domain at primary `p_trig=0.06`, FPR ≤ α₀ under both
    nulls (Wilson within tolerance) and a finite event-level MDE exists, FPR is not
    materially above α₀ across the {0.03,0.06,0.12} bracket, replay matches, and the
    companion shows no systematic null false-advantage;
  - **METHOD_INVALID** if FPR is materially uncontrolled at the sparse rates in
    powered cells, or no finite MDE exists in any domain at 0.06;
  - **INCONCLUSIVE** if error is controlled with recovery in some domains but precision
    is insufficient to declare a finite MDE in others, or the two nulls disagree beyond
    tolerance.
- **Expected output**: `run_metadata.json` with grid, seeds, draw/resample counts,
  dependency + holdout-fence confirmations, per-domain FPR/TPR/MDE headline, and the
  validity-range verdict.

## Visualisations

1. **FPR vs. activity-rate**, faceted by domain, one line per null generator, with the
   α₀ = 0.05 reference and Wilson bands — the controlled-error read across the bracket.
2. **Recovery curves**: TPR vs. planted edge `g` by domain at `p_trig=0.06`, with the
   0.80 line and each domain's empirical event-level MDE marked — the recovery read.
3. **Calibration-precision diagnostic**: Wilson half-widths / under-powered-cell map
   across the grid — shows which cells carry usable precision (esp. 4h).
4. **Equity-curve companion**: representative strategy vs. exposure-matched baseline
   curves under null and under a mid-grid planted edge, with buy-hold drawn as
   annotated context — shows the companion behaves sanely and exposure-fairly.
5. **Method verdict summary**: per-domain FPR (both nulls) and event-level MDE with the
   METHOD_VALID/INVALID/INCONCLUSIVE label — the headline.

## Interpretation Guide

- If, at `p_trig=0.06`, every domain has FPR ≤ 0.05 under **both** nulls (Wilson within
  tolerance) **and** a finite event-level MDE (TPR ≥ 0.80 at FPR ≤ α₀), and FPR stays
  controlled across {0.03,0.06,0.12}, and replay matches → **METHOD_VALID**: the
  event-level method is a fit-for-purpose yardstick on the sparse regime; EXP-028 may
  proceed under it. The reported per-domain MDEs define what per-event edge EXP-028 can
  detect.
- If FPR materially exceeds α₀ in adequately powered sparse cells → the inference does
  **not** control error at this activity (it manufactures false edges) → **METHOD_INVALID**.
- If no finite MDE exists in any domain at 0.06 (TPR never reaches 0.80 at controlled
  FPR) → the method cannot detect a planted sparse edge → **METHOD_INVALID**.
- If error is controlled and recovery holds on some domains but precision is
  insufficient elsewhere, or the two nulls disagree beyond tolerance →
  **INCONCLUSIVE**: report the partial map; a precision-only re-run (more draws, no
  object change) or operator review, not a metric change.
- The equity-curve companion is **interpretive only**: a sane companion strengthens a
  METHOD_VALID reading; an anomalous companion is a caveat, never a gate, and must not
  trigger a change to any frozen object in-phase.
- Never compute a percentage over the ~0 null baseline; report bps effects, absolute
  rates, and their CIs.

## Implementation Safety Constraints

- **Per-EVENT unit, end-to-end**: every estimand, denominator, null, verdict, and the
  companion are per-event or per-event-aggregated. The frozen per-bar suite and any
  per-bar MDE floor are **not** imported, invoked, compared against, or used as a
  sanity floor anywhere. Denominators are **reportable matched events**, never bars.
- **Anti-overfitting fence**: `avwap_events.csv` bounce outcomes are never read; only
  EXP-020 regime intervals/anchor ages (scaffolding) and the documented ~6 % rate
  (grid centring). The method is fully specified by this plan and frozen before
  EXP-028 reads any real candidate result.
- **Holdout**: first-70 % lazy slice before any collection/build (`load_analysis_data`);
  the final 30 % is never loaded; regime indices re-checked against the first-70 %
  frame.
- **Look-ahead**: placement and matching use only bar-time regime/anchor-age info;
  forward returns are outcomes; the planted drift is added to outcomes only.
- **Real-price discipline**: outcomes are direction-signed log bps on real domain
  `Close`; no synthetic chart prices, no costs/stops/fills/sizing (method calibration,
  not P&L).
- **Zero-baseline**: null per-event excess is exactly 0 bps; FPR/TPR are absolute
  proportions with Wilson intervals; non-finite MDE is reported as such (never 0).
- **Determinism**: all randomness via `seed_for(...)`; replay equality asserted.
- **Performance / vectorization**: precompute real returns, regime candidate pools, and
  anchor ages once; per draw reduces to index selection + gather + the chunked
  vectorized bootstrap/permutation (`BOOT_CHUNK`/`PERM_CHUNK` as in EXP-021).
  Control matching may be vectorized (per-regime sorted-by-anchor-age search) **only**
  if causally equivalent to EXP-021's `select_controls` (deterministic nearest anchor
  age → timestamp → row index, no future info, identical sample membership).
  Optimization must not change draw counts, sample membership, temporal ordering,
  denominators, metric definitions, or the decision rule.
- **Progress / output**: `tqdm` over the (domain × activity × null/edge × draw) loops
  (many bootstrap verdicts, per EXP-005); concise logging; helpers return data.

## Complexity Check

- Statistical tests: **4 / 4** — (1) regime-cluster bootstrap CI; (2) stratified paired
  sign-permutation with Holm; (3) Wilson FPR/TPR intervals; (4) grid-defined
  event-level MDE determination. (The equity companion reuses test (1)'s bootstrap on a
  different statistic — no new test.)
- Visualisations: **5 / 5** — FPR-vs-activity; recovery/MDE curves; calibration-precision
  diagnostic; equity-curve companion; method-verdict summary.
- New modules: **1 / 1** — one experiment-local helper under
  `python/experiments/EXP-027/code/` (sparse-null/planted-edge substrate + reused
  inference). No new/modified shared `python/src/xen/` module.

## Expected Output Files

```text
python/experiments/EXP-027/results/
- draw_verdicts.csv             # per draw x domain: effect, CI, raw_p, Holm_p, decision, reportability
- fpr_summary.csv               # FPR by domain / p_trig / null generator / alpha (Wilson)
- tpr_summary.csv               # TPR by domain / planted edge g / alpha at p_trig=0.06 (Wilson)
- mde_summary.csv               # event-level MDE by domain / alpha (finite or non-recovery)
- equity_companion_summary.csv  # exposure-matched equity diff + risk-adjusted ratio, null vs planted
- run_metadata.json             # grid, seeds, counts, dependency+holdout fence, verdict
python/experiments/EXP-027/plots/
- fpr_by_activity.png
- recovery_mde_curves.png
- calibration_precision.png
- equity_companion.png
- method_verdict_summary.png
```
