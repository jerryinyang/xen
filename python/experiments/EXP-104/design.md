# EXP-104 — Causal volatility regime and liquidity-sweep outcomes

- **Family:** `CF-LIQSWP-001/HYP-004`
- **Checkpoint:** `2026-08-11-019-liquidity-sweeps`
- **Status:** holistic design freeze through AMENDMENT-14; fresh QA required
- **Vehicle:** analysis-only re-analysis of the retained EXP-100 Nautilus emission; no new `BacktestNode`, re-emission, TEST read, or holdout access
- **Scope:** cTrader TRAIN only; `EURUSD`, `XAUUSD`, `USTEC`; 264 retained cells

## 1. Current source and authority

```text
FROZEN-SOURCE:
  root: data/nautilus_runs/EXP-100/full/
  source_version: retained 264-cell AMENDMENT-14 TRAIN emission; EXP-100 is
    completed and read-only.
  current_state_authority: EXP-100/report.md and checkpoint-019/status.md
    operator verdict; the EXP-100 design's historical rerun authorization is not
    operative. Do not rerun, modify, relabel, or re-emit EXP-100.
  family_gate: python/experiments/EXP-100/results/estimand_validation.json
  gate_precondition: blocking_pass=true; n_cells=264; every
    python/experiments/EXP-100/results/execution/full/<cell_id>.json has
    blocking_pass=true. Check this before reading any source row.
  per_cell_inputs: run_metadata.json, raids.parquet, tpo_profiles.parquet,
    bar_marks.parquet, raids_destroyed.parquet, event_log.jsonl.
  fence: INFR-021 cTrader TRAIN, 2021-06-02T00:01:00Z through
    2023-11-22T00:00:00Z; manifest SHA256
    4cdc7b01dd47200710d0d961639d55d52e1129ca89096e841eafd816b6061de0.
  seal: retain each cell's config_hash and event_log_sha256; require
    emission_contract_version=nautilus-emission-v1, Nautilus=1.230.0,
    cost_model=NO_COST_CHARGED, and one_backtest_node=true.
  analysis_boundary: independent Python analysis under analysis_code/ only;
    no source mutation, new engine process, TEST, or holdout query.

JOIN:
  raid regime/outcome reads use raids.parquet. Optional profile fields are a left
  join from raids to tpo_profiles on (raid_id, profile_generation). Report missing,
  extra, and undefined joins; never use an inner join or outcome-based row removal.
```

The binding EXP-100 decision excludes every
`profile_undefined_reason=ATR_UNDEFINED` row from excursion, normalized-excursion,
`strong_move`, and excursion-derived interpretation without repair or substitution.
All rows and reasons remain visible. `pre_mfe_retrace={price,status}` is source
metadata only and is outside HYP-004.

## 2. Mechanism, causal regime, and object identity

```text
MECHANISM: A causal volatility state may change raid frequency, excursion/swing
magnitude, duration, and strong-move incidence. The state is measured from
completed same-asset observation-timeframe bars available before each event and
is never rewritten by later volatility.
DERIVED: estimand=raid-frequency and primary-outcome distributions by emitted
raid_regime, with fixed MID comparisons; null=cross-regime future-destroyed
outcome alignment; horizon=raid through the first opposing reference event or
TRAIN censor; test=direct LOW/HIGH versus MID contrasts plus a descriptive
frequency-rate contrast, all per stratum; pnl_object=none because this event
study contains no trade, leg, episode, or capital estimand.
```

```text
OBJECT-IDENTITY:
  measurement object == trading object: YES — emitted regime labels attach to the
    same level/raid/swing objects whose outcomes are read; no proxy trade is used.
  measured conditioning event == traded entry event: N/A — this is a descriptive
    event study with no deployment rule, orders, fills, or P&L.
  effect-splitting windows non-overlapping: YES — raid, confirmation, and endpoint
    labels are event-time snapshots; one raid's outcome interval is not counted twice.
```

`CausalWilderATR(14)` updates only when a completed observation bar arrives. The
feature is `x_t = ATR_t / close_t`; a finite positive current value is appended to
the trailing maximum-252-value window **before** percentile ranking. With sorted
window values, boundaries are linearly interpolated at `(n-1)*0.33` and
`(n-1)*0.67`; `x < lower` is LOW, `x > upper` is HIGH, and equality is MID.
Fewer than 252 retained values produce `REGIME_WARMUP`; non-finite/non-positive ATR
produces `ATR_UNDEFINED`.

Pre-analysis design correction (recorded, without changing frozen EXP-100 source):
the retained processor completes the observation update before `_on_reference_bar`.
Therefore a reference event sharing an observation timestamp consumes the post-update
state for `confirmation_regime`; this corrects the former prose/golden-trace ordering.

Event field authority is the frozen raid schema:

- `raid_atr`/`raid_regime` and `excursion_atr`/`excursion_regime` are the cached
  state before the relevant observation update.
- `confirmation_atr`/`confirmation_regime` consume the post-update state when the
  completed reference timestamp is also an observation update; otherwise they consume
  the latest completed observation state.
- `endpoint_atr`/`endpoint_regime` consume the state at the completed reference event,
  using the same timestamp ordering.
- `bar_marks.regime` is the post-update observation label and is authoritative for
  this timestamp consistency audit; it never overwrites a raid label.
- All cross-view checks join by timestamp to the immediately preceding observation
  mark, never by row or bar index.

## 3. Population and estimands

Report every asset, observation timeframe, level configuration,
confirmation method/reference, side, and regime separately. The raw census includes
every raid; LOW, MID, HIGH, `REGIME_WARMUP`, and `ATR_UNDEFINED` states; every status;
all censor rows; and all profile join reasons.

The later-swing population is exactly:

```text
status == COMPLETED
and primary_attribution == true
and primary_completed == true
```

`RIGHT_CENSORED_ENDPOINT` is censored, not completed. Failed,
confirmation-censored, excursion-censored, and non-primary rows remain visible and
are excluded from the complete later-swing denominator. Primary conditioning uses
`raid_regime`; confirmation and endpoint regimes are secondary event-time strata.

Primary estimators are LOW-minus-MID and HIGH-minus-MID differences in mean `swing_atr`
(where finite) and mean `swing_duration_ns`; medians and finite `swing_price`/
`swing_bps` summaries are secondary. `strong_move` is an unpaired difference in
proportions under joint level clustering. ATR-undefined rows remain countable but
are excluded from `swing_atr`, `strong_move`, and excursion-derived interpretation.
Assert `swing_duration_ns == duration_ns` row-wise before duration analysis and display
hours as `swing_duration_ns / 3_600_000_000_000`.

### Raid-frequency estimand

For each exact `asset × observation timeframe × confirmation method/reference ×
level config × side` cell, order completed observation marks by timestamp. Let
`b_i` be a mark and `b_(i-1)` its immediately preceding completed observation mark.
A raid starting on `b_i` uses the cached state from `b_(i-1)`; this is the authoritative
causal exposure state. For regime `r` in `{LOW,MID,HIGH}`:

```text
exposure_r = count of eligible b_i whose preceding cached regime is r
starts_r   = count of unique raid_id with sweep_ts_ns == b_i.ts_event_ns and raid_regime == r
rate_r     = 1,000 * starts_r / exposure_r
contrast_r = rate_r - rate_MID
```

`b_i` is eligible only when the preceding mark exists and its causal regime is LOW,
MID, or HIGH; warmup/undefined exposure is reported separately and never silently
converted to an arm. Assert that every counted `raid_id` joins exactly once to its
`sweep_ts_ns` observation mark and that its emitted `raid_regime` equals the
preceding mark's regime. Multiple levels/raid starts on one observation bar count as
multiple unique starts. If `exposure_r=0`, emit counts, null rate/contrast/interval,
and `EMPTY_EXPOSURE`; if MID exposure is zero, every MID contrast is likewise null.

Frequency uncertainty resamples the chronological observation-mark units, carrying
each mark's complete raid-start list and preceding regime. For one-day block length,
use `L=96` bars for 15m, `L=48` for 30m, and `L=24` for 1h; sensitivities are
`L/2` and `2L`, with `L_eff=min(max(1,L), n_bars-1)` when `n_bars>=2`. Draw
`ceil(n_bars/L_eff)` starts uniformly from `[0,n_bars)`, append circular blocks,
and truncate to `n_bars`. Recompute exposures, starts, rates, and LOW/HIGH-minus-MID
contrasts for 10,000 resamples and seeds `0,1,2,3,4`, using NumPy `linear` 95%
percentiles. Report each seed, median bounds, seed ranges, and empty-exposure
reasons. This frequency read is descriptive and is not covered by the outcome
future-destroy tripwire.

## 4. Outcome estimator and neutral report contract

For outcome contrasts, clusters are complete `level_id` histories sorted by
`(first_raid_timestamp, level_id)`. A level may contribute multiple regime arms, so
all LOW/MID/HIGH arms are resampled jointly from the same cluster sequence. For block
lengths `L=5` (default), `L=2`, and `L=10` (sensitivities):

1. If an arm or MID has no eligible outcome, emit counts, null estimate/interval,
   and `EMPTY_ARM`; do not drop or interpret the row.
2. If `n_clusters>=2`, cap `L` at `n_clusters-1`, draw circular whole-cluster
   blocks from the full `[0,n_clusters)` start range, and truncate to `n_clusters`.
3. Recompute LOW-minus-MID and HIGH-minus-MID means/proportions on 10,000 resamples
   for seeds `0,1,2,3,4`; use NumPy `linear` percentile bounds. Report all seed
   bounds, median bounds, seed ranges, counts, and exclusions.

```text
REPORT-LAYERS:
  observed: regime counts, exposure counts, rates, outcomes, exclusions, direct
    contrasts, intervals, seed ranges, and destroyed-control distributions by stratum.
  ideal: MID is the fixed comparator for outcome and frequency contrasts; the same
    population, timestamp convention, and estimator are retained. No pass/fail field.
  interpretation: the analyst describes direction, interval overlap, robustness,
    and evidence for and against. No row receives a value label. An operator may
    append a tag only in a separate decision record after reviewing the complete
    evidence; it is not part of analysis tables or plots.
  analyst_boundary: analysis.md is a no-verdict handoff; a fresh analyst works
    from the registered design and emission, not implementation narrative. Observed
    and inferred statements stay separate; the analyst cannot decide progression or
    family status.
```

No machine or analysis-table field may be named `SUPPORTED`, `WASH`, `CONTRADICTED`,
`WORTH_EXPLORING`, `NOT_WORTH`, or `INCONCLUSIVE`. OPERATOR-ONLY READING BANDS (not emitted or assigned by code): positive-direction
contrast with its interval above zero; interval overlapping zero; or negative-direction
contrast with its interval below zero. They are not analysis labels, gates,
rankings, row filters, or dispositions; any tag belongs only in a separate operator
decision record.

## 5. Cross-regime future destroy and validity tripwire

```text
CONTROL REGIME_CROSSWISE_FUTURE_DESTROY:
  question answered: do regime-conditioned outcome differences require aligned
    future movement rather than regime labels, event counts, or calendar state?
  population: outcome-bearing rows grouped by exact
    archive_symbol × timeframe × confirmation_method × confirmation_reference ×
    config × side × status × primary_completed × outcome-nullness class. Regime
    labels are pooled within each group. The nullness class is the five-bit tuple
    (is_null(swing_price), is_null(swing_bps), is_null(swing_atr),
    is_null(duration_ns), is_null(strong_move)); duration_ns is the asserted alias
    of swing_duration_ns.
  mapping: copy the raw rows; sort each group by (raid_id, original_row_position).
    For each seed d=0..1999, draw default_rng(d).permutation(n) and reject/re-draw
    until perm[i] != i for every recipient i. Move the complete outcome block
    (swing_price, swing_bps, swing_atr, swing_duration_ns, duration_ns,
    strong_move) from donor perm[i] to recipient i. The donor regime may equal the
    recipient regime; forbidding same-regime donors can swap arms rather than
    destroy association. Regime/event fields, status, eligibility, nullness, and
    row counts stay fixed. A group with n<2 produces VOID_NO_DERANGEMENT and remains
    disclosed.
  DISJOINT from signal population: the destroy is calculated on a separate copy
    after the raw estimate; it cannot alter causal regime fields, event timestamps,
    or the raw population.
  bite: the pre-read fixture in the tripwire block plants +0.50 ATR,
    +3_600_000_000_000 ns, and +0.25 proportion contrasts; its destroyed means
    must satisfy the declared validity inequalities before live rows are read.
  non-vacuity: the mapping changes sufficient statistics of swing_atr,
    swing_duration_ns, and strong_move while preserving the global outcome-block
    multiset and exactly zero fixed points.
  expected outcome: if a regime/outcome relationship is aligned, the direct
    contrast moves toward zero after destruction; otherwise raw and destroyed
    contrasts are both reported without a mechanism claim.
  disclosure: raw contrast; all 2,000 destroyed contrasts; their mean and empirical
    95% interval; collapse_fraction = mean_destroyed/raw (control-to-raw ratio);
    fixed-point count; changed-field count; mapped-row count; and any VOID reason.
  destroy form: 2,000 DERANGEMENTS (zero fixed points each).
```

```text
TRIPWIRE: REGIME_CROSSWISE_FUTURE_DESTROY
  must collapse the aligned regime/outcome contrast when a raw contrast is present;
    the fixture's destroyed-to-raw ratio is expected near zero. Live ratios are
    disclosed, not used as value thresholds.
  vacuity check: outcome blocks move across fixed regime labels while the event
    population and marginal outcome blocks remain fixed, so this destroy can change
    the regime contrast.
  authority: HARD validity only for the outcome estimators in §3. It never assigns
    value, quality, power, or significance labels. Raid frequency has its own hard
    timestamp/provenance and exposure-denominator checks; it is not silently
    claimed to be validated by this future destroy.
  outer bootstrap: for each seed s=0..4, generate 10,000 joint level-cluster
    populations using §4. For every population b, recompute D_raw[s,b] and all
    2,000 deranged contrasts D_destroy[s,b,d]. Set
    m_destroy[s,b]=mean_d(D_destroy[s,b,d]);
    bootstrap_SE_raw[s]=std_b(D_raw[s,b], ddof=1); and
    bootstrap_SE_mean_destroyed[s]=std_b(m_destroy[s,b], ddof=1).
  live read: on the unresampled source population compute each LOW/HIGH-versus-MID
    D_raw and m_destroy[s]=mean_d(D_destroy[s,d]). For every seed with finite
    values, if abs(D_raw) > INTEGRITY_Z*bootstrap_SE_raw[s], require
    abs(m_destroy[s]) <= INTEGRITY_Z*bootstrap_SE_raw[s] (AMENDMENT-15: the
    derangement mean collapses the destroyed contrast and its nested SE by the
    same factor 1/(m_g-1), so the registered comparison against
    bootstrap_SE_mean_destroyed[s] reduces to the raw comparison for
    single-group populations and cannot be satisfied by the registered fixture
    plants; the destroyed mean must instead fall back inside the raw contrast's
    own bite band, which the registered fixture satisfies for every seed and
    channel — bootstrap_SE_mean_destroyed[s] is still computed and disclosed
    per seed). If that
    inequality fails, mark the affected stratum/channel invalid as
    VOID_FUTURE_DESTROY_SURVIVAL; do not interpret it as evidence against the
    mechanism. If D_raw is zero or non-finite, collapse_fraction is NaN and the
    live collapse attestation is not applicable. If no seed satisfies the raw
    inequality, report the control but do
    not claim a live collapse attestation. A missing statistic, failed derangement,
    or failed reconciliation is invalidity, never a null result.
  integrity_bite: INTEGRITY_Z=2.8. This is the same-estimator bootstrap standard
    error used only for validity; it is not MDE, a detection floor, a value floor,
    or a row-selection rule.
  fixture before live analysis: use 200 rows per regime arm with identical fixed
    labels and no nulls. The pre-read smoke uses 10 outer-bootstrap replicates; live uses 10,000. For swing_atr, alternate MID 0.90/1.10 and the LOW/HIGH arms
    1.40/1.60 (raw contrast +0.50). For duration, alternate MID
    3_000_000_000_000/4_200_000_000_000 and the LOW/HIGH arms
    6_600_000_000_000/7_800_000_000_000 (raw contrast
    +3_600_000_000_000 ns). For strong_move, set true at one quarter of MID
    positions and one half of the LOW/HIGH arm positions (raw proportion contrast
    +0.25). Every seed and channel must satisfy the raw-bite and destroyed-
    non-bite inequalities above. Failure blocks the affected live control.
```

The retained EXP-100 within-configuration destroy is an apparatus receipt only; it
preserves regime-conditioned marginals and is not the HYP-004 control.

```text
FIXTURE-TOPOLOGY:
  rows_per_arm=200 (MID, LOW, and HIGH; LOW and HIGH both take the declared arm
  plants so both registered regime contrasts are exercised); one row is one
  complete level cluster;
  level_id=FIXTURE-{regime}-level-{i:04d}; cluster_size=1;
  first_raid_timestamp=1_700_000_000_000_000_000 + i*900_000_000_000;
  config=FIXTURE_CONFIG for MID and HIGH arms;
  deterministic row permutation seed=4, then raid_id=fixture-raid-{position:04d};
  cluster ordering=(first_raid_timestamp, level_id); regime/status/nullness fields
  are fixed except for the declared arm label and outcome values.
  fixture outer bootstrap=10 for the pre-read smoke; live=10,000.
```

## 6. Sample size, complexity, and integrity boundary

```text
SAMPLE-SIZE:
  expected events per stratum: measured from the retained emission; planning context only.
  minimum_n_for_primary_inference: none; every realised row retains counts, rates,
    estimates, intervals, exclusions, and reason codes.
  declared_fixed_comparator: MID regime within the same named asset/timeframe/
    method/reference/config/side stratum; all-regime and warmup/undefined counts
    are disclosures.
  channels:
    - name: mean swing_atr and mean swing_duration_ns contrasts
      sigma_denominator: outcome_level
    - name: strong_move proportion difference
      sigma_denominator: unpaired_proportion_delta
    - name: raid-frequency rate contrast
      sigma_denominator: event_count
  strata predeclared thin: every asset × timeframe × method × reference × side ×
    config × regime, including warmup, ATR-undefined, empty exposure, empty arms,
    and status/censor reasons.
COMPLEXITY-BUDGET:
  estimators: one frequency-rate contrast and two outcome contrasts, with median/
    quantile disclosures; no parametric test. controls: one future destroy plus
    the frequency timestamp/exposure audit. plots: at most four purpose-specific
    regime/rate/contrast plots; pooled plots are disclosure-only. analysis modules:
    one independent module.
```

```text
HARD (block): source gate-first check; TRAIN/holdout fence; causal regime
  provenance and timestamp joins; schema/object/count reconciliation;
  no-local-accounting; deterministic analysis; binding ATR_UNDEFINED exclusion;
  future-destroy outcome validity; frequency exposure-denominator validity; and
  zero-cost compliance.
INFORMATIVE (operator judges): every observed regime, exposure, rate, effect,
  interval, status, robustness read, control ratio, and cross-stratum comparison.
```

There is no trade or leg-bps series, so PSR is **N/A**. No cost, spread, commission,
swap, power calculation, detection threshold, sample-size veto, automatic label, or
family disposition is in scope.

## 7. Golden trace

```text
GOLDEN-TRACE (252-value causal window; all values are predeclared fixture state):
  T1 (2023-01-03T10:00:00Z): immediately before the completed observation update,
    the cached x=0.80 and the sorted trailing window has lower=0.90 and upper=1.10.
    A high-level raid starts; raid_atr/excursion_atr and raid_regime/excursion_regime
    use the cached pre-update state, so the emitted regime is LOW.
  T2 (2023-01-03T10:15:00Z): the completed observation has x=1.20. The current
    value is appended before ranking; the retained 252-value window still has
    lower=0.90 and upper=1.10, so bar_marks.regime=HIGH. The prior raid_regime
    remains LOW. Values exactly 0.90 or 1.10 would be MID, not LOW or HIGH.
  T3 (2023-01-03T10:30:00Z, 10:45:00Z, 11:00:00Z, 11:15:00Z, 11:30:00Z,
    11:45:00Z, 12:00:00Z): the completed observation updates are explicitly
    x=1.20 at 10:30 and 10:45; the completed 11:00 observation update has x=1.00
    and is processed before `_on_reference_bar`, so the same-timestamp reference
    consumes post-update confirmation_regime=MID (not the pre-update HIGH state).
    The 11:15, 11:30, and 11:45 updates are x=1.00; after each update the retained
    window boundaries remain lower=0.90 and upper=1.10. Before the completed 12:00
    reference event, the cached x=1.00 is still MID, so endpoint_regime=MID. The
    raid's original LOW label is
    unchanged; each regime field is tied to its own event timestamp and the
    preceding-observation join is explicit.
```

## 8. Amendments and final selection accounting

```text
AMENDMENT-2: 1H confirmation for 15m/30m, 1D for 1h — DIRECTION: TIGHTER
  running count: 0 looser / 1 tighter / 0 neutral
AMENDMENT-3: retain 1m engine input — DIRECTION: NEUTRAL
  running count: 0 looser / 1 tighter / 1 neutral
AMENDMENT-4: causal ATR normalisation — DIRECTION: NEUTRAL
  running count: 0 looser / 1 tighter / 2 neutral
AMENDMENT-5: SoT tight-gap condition — DIRECTION: NEUTRAL
  running count: 0 looser / 1 tighter / 3 neutral
AMENDMENT-6: close-all-eligible settlement — DIRECTION: TIGHTER
  running count: 0 looser / 2 tighter / 3 neutral
AMENDMENT-7: cTrader-only universe — DIRECTION: TIGHTER
  running count: 0 looser / 3 tighter / 3 neutral
AMENDMENT-8: observation-bar raid grain — DIRECTION: NEUTRAL
  running count: 0 looser / 3 tighter / 4 neutral
AMENDMENT-9: 1H and 4H 1h references; retire 1D — DIRECTION: LOOSER
  running count: 1 looser / 3 tighter / 4 neutral
AMENDMENT-10: NY 17:00 trading day/week — DIRECTION: NEUTRAL
  running count: 1 looser / 3 tighter / 5 neutral
AMENDMENT-11: rolling 7/14/22/252; 264 cells — DIRECTION: NEUTRAL
  running count: 1 looser / 3 tighter / 6 neutral
AMENDMENT-12: tightness at 50% VA width; gap mass 30% — DIRECTION: NEUTRAL
  running count: 1 looser / 3 tighter / 7 neutral
AMENDMENT-13: same-bar return leaves raid live — DIRECTION: LOOSER
  running count: 2 looser / 3 tighter / 7 neutral
AMENDMENT-14: add pre_mfe_retrace without changing HYP-004 — DIRECTION: NEUTRAL
  running count: 2 looser / 3 tighter / 8 neutral
AMENDMENT-15: destroyed non-bite compares the destroyed mean against the raw
  bootstrap SE (see TRIPWIRE live read) — DIRECTION: LOOSER
  running count: 3 looser / 3 tighter / 8 neutral

FINAL-NULL / SELECTION ACCOUNTING:
  final design has 3 looser / 3 tighter / 8 neutral amendments. It has no
  machine qualification, ranking, capped-read selection, or value verdict, so
  expected machine false-qualifier count under a global null is zero by
  construction. This is an accounting statement, not evidence. No row is hidden,
  dropped, or relabelled by n, interval, sign, regime, or control result.
  F02/F04/F06 are not applicable: there is no battery selection, path-dependent
  exit, or phase-shift retention gate. F07 is satisfied by retaining every realised
  regime, status, exposure, count, outcome, and interval.
```

## 9. Zero-cost disclosure

```text
ZERO-COST-DISCLOSURE
  cost_model: NO_COST_CHARGED
  spread: not modeled
  commissions: not modeled
  swaps/funding: not modeled
  implication: every figure in this document is gross and cost-free; no spread,
    commission, or swap enters any calculation. Realised results would differ
    (likely worse) under any real cost schedule.
  prohibited_claims: fully-net, cost-complete, tradable, deployable
  lifting: only an explicit operator directive may introduce a cost model for a
    scoped experiment; the directive is recorded in that experiment's design.md.
```
