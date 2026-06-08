# Analysis Plan: Experiment EXP-025

## Objective

Determine whether EXP-020 AVWAP bounce trigger bars show direct support/resistance
behavior at the AVWAP line itself, measured by a predeclared event-bar
line-rejection score, versus matched same-regime non-event control bars. This is
a diagnostic component study. It runs no candidate screen, uses no future-return
horizon, and does not touch the global holdout.

The core estimand is the domain-level paired difference:

```text
event line_rejection_score_bps - mean(matched-control line_rejection_score_bps)
```

at the event/control bar itself.

## Methodology

### Step 1: Dependency Gate And Substrate Reconstruction

- **Method**: Validate EXP-020 and EXP-024 dependencies, then rebuild 5m/1h/4h
  domain bars from the exact source files recorded in EXP-020
  `analysis_metadata.csv`. Reconstruct only the first-70% chronological analysis
  slice. Compare reconstructed domain row counts and min/max `CloseTime` values
  to EXP-020 metadata. Load EXP-020 `avwap_events.csv` and
  `avwap_state_summary.csv`.
- **Why this method**: EXP-025 is meant to test the same frozen first-branch
  substrate as EXP-020/021/022. Rebuilding from source with metadata equality
  catches wrong files, changed slicing, or accidental holdout access.
- **Simpler alternative considered**: Use EXP-020 event tables alone. Rejected
  because the primary metric needs real `High/Low/Close` at event and control
  bars and contemporaneous per-bar AVWAP/band values for controls.
- **Assumptions**:
  - EXP-020 substrate is the authoritative event definition.
  - `trigger_idx` indexes the same rebuilt domain frame when EXP-020 metadata
    checks pass.
  - Domain bars are chronologically ordered by `CloseTime`.
- **Expected output**: `domain_reconstruction_check.csv` and dependency fields in
  `run_metadata.json`.

### Step 2: Causal Per-Bar AVWAP/Band Replay

- **Method**: For each instrument/domain/regime, replay the frozen EXP-020 AVWAP
  math from the recorded `anchor_idx` through `regime_end_idx`, producing per-bar
  `avwap`, `band_spread`, `band_spread_bps`, `anchor_age_bars`, and
  `close_to_avwap_bps`. Use the same source, volume exponent, and MAD-band rule
  as `xen.avwap`. Validate event rows by checking that replayed AVWAP at
  `trigger_idx` equals EXP-020 `avwap_at_trigger` within tight floating tolerance.
- **Why this method**: Controls require contemporaneous AVWAP values; EXP-020
  persists only trigger-time AVWAP values. Causal replay is deterministic and
  exactly scoped to the frozen substrate.
- **Simpler alternative considered**: Estimate control AVWAP from event AVWAP or
  interpolate between event rows. Rejected because that would not be the actual
  line seen at the control timestamp and would compromise the S/R test.
- **Assumptions**:
  - Replay uses only bars up to each evaluated timestamp.
  - `band_spread_bps = 10000 * log((AVWAP + band_spread) / AVWAP)` when AVWAP
    and spread are finite and positive.
  - `close_to_avwap_bps = 10000 * log(Close / AVWAP)`; absolute distance is used
    for proximity matching.
- **Expected output**: an in-memory per-cell state table used by matching and
  validation rows; optional sampled validation rows if implementation needs them.

### Step 3: Event-Bar Score Computation

- **Method**: Compute the primary line-rejection score for every event and
  candidate control bar:

  For bullish direction:

  ```text
  close_rebound_bps = 10000 * log(Close / AVWAP)
  adverse_penetration_bps = max(0, 10000 * log(AVWAP / Low))
  line_rejection_score_bps = close_rebound_bps - adverse_penetration_bps
  ```

  For bearish direction:

  ```text
  close_rebound_bps = 10000 * log(AVWAP / Close)
  adverse_penetration_bps = max(0, 10000 * log(High / AVWAP))
  line_rejection_score_bps = close_rebound_bps - adverse_penetration_bps
  ```

  Invalid OHLC or non-finite AVWAP rows are non-reportable, not coerced.
- **Why this method**: The score is a single direct event-bar measure of line
  rejection: close away from the line in the regime direction minus intrabar
  adverse penetration through the line. It does not use future continuation and
  therefore does not duplicate EXP-021.
- **Simpler alternative considered**: Use only close distance from AVWAP, or only
  intrabar penetration. Rejected because either alone only captures one side of
  the support/resistance claim. The combined score is still one predeclared
  metric and keeps both components visible.
- **Assumptions**:
  - A positive score is meaningful only relative to matched controls, because
    event trigger logic itself requires a close cross in the regime direction.
  - Real `High/Low/Close` values are the appropriate price basis; AVWAP is a
    reference line, not a trade price.
- **Expected output**: score component columns in `line_rejection_observations.csv`.

### Step 4: Matched Same-Regime Control Construction

- **Method**: For each event, build a deterministic same-regime non-event control
  pool:
  - same instrument/domain/regime/direction;
  - not an EXP-020 trigger bar;
  - not within ±6 completed domain bars of any trigger in the same cell;
  - finite replayed AVWAP and band spread;
  - line-proximate: `abs(close_to_avwap_bps) <= max(1.0, band_spread_bps)`.

  Select up to 5 controls, ranked by nearest absolute close-to-AVWAP distance,
  nearest anchor age, nearest timestamp/index, then smaller index. Require at
  least 3 controls for reportability.
- **Why this method**: The same-regime restriction controls for regime state and
  anchored AVWAP context. Matching primarily on distance to AVWAP keeps the
  comparison about line reaction, not arbitrary bars elsewhere in the regime.
- **Simpler alternative considered**: Reuse EXP-021's controls exactly. Rejected
  because EXP-021 matched on anchor age and timestamp for future-return
  continuation, not on proximity to the line itself.
- **Assumptions**:
  - Controls near the line but not bounce triggers are the correct null for
    direct S/R behavior.
  - Reusing controls across events within the same regime is acceptable when
    uncertainty clusters by regime.
- **Expected output**: `line_rejection_observations.csv` and
  `control_match_diagnostics.csv`, including non-reportable reason counts.

### Step 5: Domain-Level Primary Inference

- **Method**: For reportable matched events, compute paired differences
  `event_score - mean(control_scores)`. Summarize each instrument/domain by the
  event-weighted mean paired difference. Summarize each domain by equal-weighting
  reportable instruments. Use a regime-cluster bootstrap within
  instrument/direction strata for 95% CIs. Use a stratified paired sign
  permutation test for the primary domain-level statistic, Holm-adjusted across
  the three domains.
- **Why this method**: It matches EXP-021's inference pattern, preserves the
  event/regime dependence structure, and avoids normality assumptions on
  financial bar metrics.
- **Simpler alternative considered**: A simple t-test on event-level paired
  differences. Rejected because it assumes i.i.d. observations and lets
  high-count/high-volatility instruments dominate.
- **Assumptions**:
  - Regime clusters are an appropriate dependence unit for AVWAP state-machine
    events and controls.
  - Equal instrument weighting is the correct domain-level summary for a
    component claim intended to generalize across the four instruments.
- **Expected output**: `domain_line_rejection_tests.csv` with effect bps, CI,
  raw p, Holm p, reportability, and decision labels.

### Step 6: Matching-Balance And Component Diagnostics

- **Method**: Report, by instrument/domain/direction and domain, event vs control
  absolute close-to-AVWAP distance distributions; median event-control proximity
  differences; mean close-rebound and adverse-penetration components by role;
  first-vs-pyramid descriptive split. The predeclared balance guard marks the
  experiment inconclusive if median absolute event-vs-control close-to-AVWAP
  distance differs by more than 2 bps in every reportable domain.
- **Why this method**: A positive line-rejection score is only interpretable if
  controls are actually comparable line-neighborhood bars. Component diagnostics
  explain whether any effect comes from stronger closes away from the line,
  reduced penetration, or both.
- **Simpler alternative considered**: Omit balance and component diagnostics.
  Rejected because matching quality is central to this direct S/R claim and
  because the combined primary metric needs component transparency.
- **Assumptions**:
  - Balance diagnostics are quality checks, not alternate market-edge tests.
  - First/pyramid splits are descriptive and cannot alter the primary verdict.
- **Expected output**: `control_match_diagnostics.csv`,
  `line_rejection_summary.csv`, and plot-ready summaries.

## Visualisations

1. **Domain effect forest**: domain-level paired line-rejection effect with 95%
   CIs and Holm decision labels — primary result visual.
2. **Event vs control score distributions**: reportable event and matched-control
   `line_rejection_score_bps` distributions by domain — shows overlap and
   tail behavior.
3. **Matching proximity diagnostics**: event vs control absolute close-to-AVWAP
   distance by domain — verifies line-neighborhood balance.
4. **Score component decomposition**: close-rebound and adverse-penetration
   components by event/control role and domain — explains the primary score.

## Interpretation Guide

- **Evidence FOR** if at least one reportable domain has positive primary paired
  line-rejection effect, CI lower bound > 0 bps, and Holm-adjusted p <= 0.05.
  Interpretation: the EXP-020 bounce trigger bar shows direct AVWAP-line
  rejection beyond matched line-neighborhood controls.
- **Evidence AGAINST** if no domain is reportable, or every reportable domain's
  CI upper bound <= 0 bps. Interpretation: this direct S/R metric does not show
  measurable line reaction beyond controls.
- **Inconclusive** if no domain meets Evidence FOR but at least one reportable
  domain spans 0 bps, or matching balance fails the predeclared 2 bps proximity
  guard in every reportable domain.
- A positive result does **not** qualify a tradable strategy or unlock a
  candidate screen by itself. It supports the mechanism-level claim that the
  AVWAP line has direct event-bar reaction evidence.
- A negative result does **not** invalidate EXP-021/022. It means their positive
  component evidence may be continuation/completion behavior rather than direct
  line support/resistance.

## Complexity Check

- Statistical tests: 2 / 2
  1. Primary paired line-rejection effect with bootstrap CI and Holm-adjusted
     permutation p-values.
  2. Matching-balance proximity guard.
- Visualisations: 4 / 4.
- New modules: 0 / 0 shared modules. Implementation should use
  `python/experiments/EXP-025/code/run_experiment.py` only unless governance
  later approves a reusable module.

## Implementation Safety Constraints

- **Holdout fence**: load only first-70% chronological slices; do not inspect,
  count, plot, or emit any final-holdout rows.
- **Source-file discipline**: filter timebar inputs to exact EXP-020
  `source_file` names and validate reconstructed metadata before analysis.
- **Temporal ordering**: sort by `CloseTime`; align events by
  `(instrument, domain, trigger_idx, trigger_time, trigger_close)` and hard-fail
  on mismatches.
- **Causal AVWAP replay**: per-bar AVWAP/band replay must use only each regime's
  anchor and bars up to the evaluated timestamp. Do not interpolate from future
  event rows.
- **No future outcomes**: primary metric is `h=0`; no future close, target, or
  lifetime outcome can enter the metric or control matching.
- **Real prices**: use real domain `High/Low/Close` for score components.
  AVWAP is a reference line only.
- **No threshold sweep**: line-proximity rule and 2 bps balance guard are fixed.
  Do not add alternate thresholds after seeing results.
- **Denominators**: report raw events, reportable events, non-reportable reasons,
  controls per event, and direction counts. Empty denominators emit null /
  non-reportable, never zero effect.
- **Performance**: outer loops are bounded by 4 instruments x 3 domains and
  regime/event matching. Use `tqdm` for file/cell loops. Vectorize score
  computation where causally equivalent; keep AVWAP replay and matching logic
  explicit if sequential state is clearer.
- **Output discipline**: helpers return data; orchestration writes results and
  plots. Plot from summaries or bounded reportable records, not repeated heavy
  data loads.
