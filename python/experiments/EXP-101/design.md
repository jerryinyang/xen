# EXP-101 — Level configuration and later-swing outcomes

- **Family:** `CF-LIQSWP-001/HYP-001`
- **Checkpoint:** `2026-08-11-019-liquidity-sweeps`
- **Status:** holistic design freeze through AMENDMENT-17; analysis rebuild required
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
```

The binding EXP-100 operator decision excludes every
`profile_undefined_reason=ATR_UNDEFINED` row from excursion, normalized-excursion,
`strong_move`, and excursion-derived interpretation without repair or substitution.
All rows and reasons remain visible. `pre_mfe_retrace={price,status}` is retained as
source metadata but is outside HYP-001.

Frozen fields are exact: `config`/`source_configuration`, `raid_id`, `level_id`,
`swing_price`, `swing_bps`, `swing_atr`, `strong_move`, `swing_duration_ns`, and
`duration_ns`. `swing_duration_ns` is canonical; `duration_ns` is its byte-equal
compatibility alias. Assert equality before any duration read and display hours as
`swing_duration_ns / 3_600_000_000_000`.

## 2. Mechanism and object identity

```text
MECHANISM: If level degree carries significance, raids of higher-degree or
longer-window levels should have different later-swing outcome distributions than
raids of lower-degree levels under the same causal raid definition. The measured
object is a level-linked raid and its later confirmed swing; no trade or fill is
being inferred.
DERIVED: estimand=per-stratum outcome distributions and direct fixed-baseline
contrasts; null=cross-configuration future-destroyed outcome alignment;
horizon=confirmation through the first opposing reference event or TRAIN censor;
test=non-parametric direct mean/median contrasts and an unpaired strong-move
proportion contrast, all per stratum; pnl_object=none because this event study
contains no trade, leg, episode, or capital estimand.
```

```text
OBJECT-IDENTITY:
  measurement object == trading object: YES — the emitted level-linked raid and
    later swing are the object under study; no proxy entry or synthetic fill is used.
  measured conditioning event == traded entry event: N/A — this is a descriptive
    event study, not a deployment strategy; no orders, fills, or P&L are read.
  effect-splitting windows non-overlapping: YES — each raid owns its excursion,
    confirmation, and later-swing interval; repeated level dependence is clustered
    by level_id rather than treated as independent events.
```

## 3. Scope, population, and estimand

Every result row is separate by
`archive_symbol × timeframe × confirmation_method × confirmation_reference × side × config`.
The 11 configurations are:

- Family A: `PREVIOUS_1H`, `PREVIOUS_4H`, `PREVIOUS_1D`, `PREVIOUS_1W`.
- Family B: `PREVIOUS_ASIA`, `PREVIOUS_EUROPE`, `PREVIOUS_AMERICA`.
- Family C: `ROLLING_7`, `ROLLING_14`, `ROLLING_22`, `ROLLING_252`.

The fixed comparator is `PREVIOUS_1H` within Family A, `PREVIOUS_ASIA` within
Family B, and `ROLLING_7` within Family C, always in the same named stratum.
Ordered configuration descriptions and any pairwise comparisons are disclosures;
no adaptive arm is selected after seeing an outcome.

The census contains every raid row: `COMPLETED`, `CONFIRMED_NON_PRIMARY`,
`FAILED_BREAKOUT`, all right-censor statuses, null outcomes, and thin cells. The
outcome population is every raid eligible at an expected-side confirmation
(AMENDMENT-17):

```text
completed primary of a confirmation set
OR CONFIRMED_NON_PRIMARY in the same source_cell × side whose endpoint_ts_ns
equals that primary's confirmation_ts_ns, after the primary leftover is attached
```

Each raid keeps its own first push. The leftover path is the set's completed
primary leftover. `strong_move` is leftover ATR vs own max_excursion_atr.
Failed, excursion-censored, confirmation-censored, unmatched non-primary, and
missing-outcome rows remain in status/count tables. `swing_price`, `swing_bps`, and `swing_duration_ns` are read
only when finite. `swing_atr` and `strong_move` exclude ATR-undefined rows under the
binding EXP-100 decision. The excluded count is printed beside every affected row.

Primary estimators are the arm-minus-fixed-comparator difference in mean `swing_atr`
(where defined) and mean `swing_duration_ns`; median differences are robust
secondary disclosures. `strong_move` is an **unpaired** difference in proportions;
no raid pairing is asserted. Raw `swing_price` and `swing_bps` are source-field
summaries, not separate hard tripwire estimands.

## 4. Estimator and neutral report contract

Clusters are complete `level_id` histories. Sort clusters by
`(first_raid_timestamp, level_id)` and keep every row belonging to a selected
cluster. For EXP-101, arm and fixed-baseline clusters are distinct configuration
populations and are resampled independently. For each requested block length `L`:

1. If either arm has no eligible observation, emit counts, null estimate/interval,
   and `EMPTY_ARM`; do not remove the row or infer a direction.
2. If `n_clusters >= 2`, set `L_eff=min(max(1,L), n_clusters-1)`; draw
   `ceil(n_clusters/L_eff)` starts uniformly from `[0,n_clusters)`, append
   `L_eff` circularly consecutive clusters per start, and truncate to the first
   `n_clusters`. This is repeated independently for the two populations.
3. Recompute both arm statistics and their difference on every resample. Use 10,000
   resamples for seeds `0,1,2,3,4`; the 95% percentile interval uses NumPy's
   `linear` quantile method. Report each seed's bounds, the median lower/upper
   bound, and the seed-bound ranges. Default `L=5`; sensitivities are `L=2` and
   `L=10`, each capped by the same rule.
4. Report counts, missingness, status/censor composition, mean, median, direct
   difference, interval, seed range, and every requested configuration. Pooled
   figures are disclosure-only.

```text
REPORT-LAYERS:
  observed: counts, populations, exclusions, means, medians, direct contrasts,
    intervals, seed ranges, and control distributions, all named by stratum.
  ideal: the fixed comparator and the same estimator on the same population;
    there is no pass/fail field and no post-outcome comparator.
  interpretation: the analyst describes direction, interval overlap, robustness,
    and evidence both for and against. No row receives a value label. An operator
    may append a tag only in a separate decision record after reviewing the complete
    evidence; it is not part of analysis tables or plots.
  analyst_boundary: analysis.md is a no-verdict handoff; a fresh analyst works
    from the registered design and emission, not implementation narrative. Observed
    and inferred statements stay separate; the analyst cannot decide progression or
    family status.
```

No machine or analysis-table field may be named `SUPPORTED`, `WASH`, `CONTRADICTED`,
`WORTH_EXPLORING`, `NOT_WORTH`, or `INCONCLUSIVE`. OPERATOR-ONLY READING BANDS (not emitted or assigned by code): positive-direction
contrast with its interval above zero; interval overlapping zero; or negative-direction
contrast with its interval below zero. These are not analysis labels, gates,
rankings, row filters, or dispositions; any tag belongs only in a separate operator
decision record.

## 5. Cross-configuration future destroy and validity tripwire

```text
CONTROL CONFIG_CROSSWISE_FUTURE_DESTROY:
  question answered: does a configuration/outcome contrast require the aligned
    post-confirmation path rather than event counts or labels alone?
  population: outcome-bearing rows grouped by exact
    archive_symbol × timeframe × confirmation_method × confirmation_reference ×
    side × status × primary_completed × outcome-nullness class. Configuration is
    deliberately pooled within each group. The nullness class is the five-bit
    tuple (is_null(swing_price), is_null(swing_bps), is_null(swing_atr),
    is_null(duration_ns), is_null(strong_move)); duration_ns is the asserted alias
    of swing_duration_ns.
  mapping: copy the raw rows; sort each group by (raid_id, original_row_position).
    For each seed d=0..1999, draw default_rng(d).permutation(n) and reject/re-draw
    until perm[i] != i for every recipient i. Move the complete outcome block
    (swing_price, swing_bps, swing_atr, swing_duration_ns, duration_ns,
    strong_move) from donor perm[i] to recipient i. The donor configuration may
    equal the recipient configuration; forbidding that can swap two arms rather
    than destroy their association. Event fields, configuration, status,
    eligibility, nullness, and row counts stay fixed. A group with n<2 stays
    fixed and is disclosed via the group-size report; it does not void the
    control, because its rows contribute identically to the raw and destroyed
    contrasts (AMENDMENT-16). The control voids only when no group is movable
    (VOID_NO_MOVABLE_ROWS) or no eligible value changes (VOID_NO_CHANGED_VALUE).
  DISJOINT from signal population: the destroy is computed on a separate copy
    after the raw estimate; it cannot alter raw rows, labels, source timestamps, or
    the signal population.
  bite: the pre-read fixture in the tripwire block plants +0.50 ATR,
    +3_600_000_000_000 ns, and +0.25 proportion contrasts; its destroyed means
    must satisfy the declared validity inequalities before live rows are read.
  non-vacuity: the assignment changes the sufficient statistics of swing_atr,
    swing_duration_ns, and strong_move while preserving the global outcome-block
    multiset and exactly zero fixed points.
  expected outcome: if an aligned configuration relationship exists, the direct
    contrast moves toward zero after destruction; otherwise the raw and destroyed
    contrasts are both reported without a mechanism claim.
  disclosure: raw contrast; all 2,000 destroyed contrasts; their mean and empirical
    95% interval; collapse_fraction = mean_destroyed/raw (control-to-raw ratio);
    fixed-point count; changed-field count; mapped-row count; and the reason for
    any VOID population.
  destroy form: 2,000 DERANGEMENTS (zero fixed points each).
```

```text
TRIPWIRE: CONFIG_CROSSWISE_FUTURE_DESTROY
  must collapse the aligned configuration/outcome contrast when a raw contrast is
    present; the fixture's destroyed-to-raw ratio is expected near zero. Live ratios
    are disclosed, not used as value thresholds.
  vacuity check: outcome blocks move across fixed configuration labels while the
    event population and marginal outcome blocks remain fixed, so this destroy can
    change this configuration contrast.
  authority: HARD validity only. It never assigns value, quality, power, or
    significance labels. Its authorized estimators are the raw same-population
    mean swing_atr contrast, mean swing_duration_ns contrast, and unpaired
    strong_move proportion contrast defined in §3.
  outer bootstrap: for each seed s=0..4, generate 10,000 cluster-bootstrap
    populations using the §4 mechanics. For every population b, recompute the raw
    contrast D_raw[s,b] and all 2,000 deranged contrasts D_destroy[s,b,d]. Set
    m_destroy[s,b]=mean_d(D_destroy[s,b,d]);
    bootstrap_SE_raw[s]=std_b(D_raw[s,b], ddof=1); and
    bootstrap_SE_mean_destroyed[s]=std_b(m_destroy[s,b], ddof=1).
  live read: on the unresampled source population compute D_raw and
    m_destroy[s]=mean_d(D_destroy[s,d]). For every seed with finite values, if
    abs(D_raw) > INTEGRITY_Z*bootstrap_SE_raw[s], require
    abs(m_destroy[s]) <= INTEGRITY_Z*bootstrap_SE_raw[s] (AMENDMENT-15: the
    derangement mean collapses the destroyed contrast and its nested SE by the
    same factor 1/(m_g-1), so the registered comparison against
    bootstrap_SE_mean_destroyed[s] reduces to the raw comparison for
    single-group populations and cannot be satisfied by the registered fixture
    plants; the destroyed mean must instead fall back inside the raw contrast's
    own bite band, which the registered fixture satisfies for every seed and
    channel — bootstrap_SE_mean_destroyed[s] is still computed and disclosed
    per seed). If the latter
    inequality fails, mark the affected stratum/channel invalid as
    VOID_FUTURE_DESTROY_SURVIVAL; do not interpret it as evidence against the
    mechanism. If D_raw is zero or non-finite, collapse_fraction is NaN and the
    live collapse attestation is not applicable. If no seed satisfies the raw
    inequality, report the control but do
    not claim a live collapse attestation. A missing statistic, failed derangement,
    or failed estimator reconciliation is also invalidity, never a null result.
  integrity_bite: INTEGRITY_Z=2.8. This is the same-estimator bootstrap standard
    error used only for validity; it is not MDE, a detection floor, a value floor,
    or a row-selection rule.
  fixture before live analysis: use 200 rows per arm with identical fixed labels
    and no nulls. The pre-read smoke uses 10 outer-bootstrap replicates; live uses 10,000.
    For swing_atr, alternate baseline 0.90/1.10 and arm 1.40/1.60
    (raw contrast +0.50). For duration, alternate baseline
    3_000_000_000_000/4_200_000_000_000 and arm
    6_600_000_000_000/7_800_000_000_000 (raw contrast
    +3_600_000_000_000 ns). For strong_move, set true at one quarter of baseline
    positions and one half of arm positions (raw proportion contrast +0.25).
    Every seed and channel must satisfy the raw-bite and destroyed-non-bite
    inequalities above. Failure blocks the affected live control implementation.
```

The retained EXP-100 within-configuration destroy is an apparatus receipt only; it
cannot validate this contrast because it preserves each configuration's marginal.

```text
FIXTURE-TOPOLOGY:
  rows_per_arm: 200 (BASELINE and ARM) for each registered contrast pair —
    every (arm, comparator) contrast contributes its own BASELINE/ARM row block
    with the declared plants, so every registered contrast is exercised by the
    pre-read smoke; one row is one complete level cluster;
  level_id=FIXTURE-{arm}-level-{i:04d}; cluster_size=1;
  first_raid_timestamp=1_700_000_000_000_000_000 + i*900_000_000_000;
  deterministic row permutation seed=4, then raid_id=fixture-raid-{position:04d};
  cluster ordering=(first_raid_timestamp, level_id); no source row is read.
  fixture outer bootstrap=10 for the pre-read smoke; live=10,000.
```

## 6. Sample size, complexity, and integrity boundary

```text
SAMPLE-SIZE:
  expected events per stratum: measured from the retained emission; planning context only.
  minimum_n_for_primary_inference: none; every realised row retains n, estimate,
    interval, exclusions, and reason codes.
  declared_fixed_comparator: Family A PREVIOUS_1H; Family B PREVIOUS_ASIA;
    Family C ROLLING_7, each within the exact named stratum.
  channels:
    - name: mean swing_atr
      sigma_denominator: outcome_level
    - name: mean swing_duration_ns
      sigma_denominator: outcome_level
    - name: strong_move proportion difference
      sigma_denominator: unpaired_proportion_delta
  strata predeclared thin: every asset × timeframe × method × reference × side ×
    config, including empty arms and ATR-undefined reason rows.
COMPLEXITY-BUDGET:
  estimators: one direct contrast plus median/quantile disclosures; no parametric test.
  control: one 2,000-seed future destroy and one 5-seed outer bootstrap battery.
  plots: at most three purpose-specific distribution/contrast plots; pooled plots
    are disclosure-only. analysis modules: one independent analysis module.
```

```text
HARD (block): source gate-first check; TRAIN/holdout fence; causal timestamp
  provenance; schema/object/count reconciliation; no-local-accounting;
  deterministic analysis; binding ATR_UNDEFINED exclusion; future-destroy
  validity; and zero-cost compliance.
INFORMATIVE (operator judges): every observed effect, interval, frequency,
  distribution, robustness read, control ratio, and cross-stratum comparison.
```

There is no trade or leg-bps series, so PSR is **N/A**. No cost, spread, commission,
swap, power calculation, detection threshold, sample-size veto, automatic label, or
family disposition is in scope.

## 7. Golden trace

```text
GOLDEN-TRACE:
  T1 (2023-01-03T10:00:00Z; separate 15m/1H source cells): PREVIOUS_1H and
    ROLLING_7 high levels each equal 100.00. In each independent cell, the
    completed observation bar is high=101.20, low=100.80, close=101.00 and
    causal raid_atr=1.00. Each cell starts its own raid with prior_raid_count=0,
    max_excursion=1.20, and null return. No cross-cell ordering is inferred.
  T2 (2023-01-03T10:15:00Z and 11:00:00Z): a completed observation low=100.00
    records return_ts_ns in each cell and AMENDMENT-13 keeps each raid live. The
    11:00 expected-side 1H close independently assigns primary_attribution=true
    in each cell. A raid is not CONFIRMED_NON_PRIMARY merely because another
    configuration has an equal-price level.
  T3 (2023-01-03T12:00:00Z): the first opposing reference event ends each
    primary swing. With level=100.00, raid_atr=1.00, favorable extreme=98.00,
    each row has swing_price=2.00, swing_atr=2.00, swing_bps=200.0,
    swing_duration_ns=duration_ns=3_600_000_000_000, and strong_move=true because
    2.00 > 1.20. Later outcomes cannot rewrite either configuration identity.
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
AMENDMENT-14: add pre_mfe_retrace without changing HYP-001 — DIRECTION: NEUTRAL
  running count: 2 looser / 3 tighter / 8 neutral
AMENDMENT-15: destroyed non-bite compares the destroyed mean against the raw
  bootstrap SE (see TRIPWIRE live read) — DIRECTION: LOOSER
  running count: 3 looser / 3 tighter / 8 neutral
  (OPERATOR-APPROVED 2026-08-17 — checkpoint 019 §2)
AMENDMENT-16: singleton destroy groups (n<2) stay fixed and are disclosed via
  the group-size report; they do not void the control (their rows contribute
  identically to raw and destroyed contrasts); the control voids only when no
  group is movable (VOID_NO_MOVABLE_ROWS) or no eligible value changes
  (VOID_NO_CHANGED_VALUE) — DIRECTION: LOOSER
  running count: 4 looser / 3 tighter / 8 neutral
  (OPERATOR-APPROVED 2026-08-18 — checkpoint 019 §2)
AMENDMENT-17: later-swing population is every raid eligible at confirmation,
  not only the latest primary. Shared leftover from the completed primary;
  own first push retained; no EXP-100 rerun — DIRECTION: LOOSER
  running count: 5 looser / 3 tighter / 8 neutral
  FLAG: third consecutive looser after A-15/A-16; operator 2026-09-02 overrode.

FINAL-NULL / SELECTION ACCOUNTING:
  final design has 5 looser / 3 tighter / 8 neutral amendments. It has no
  machine qualification, ranking, capped-read selection, or value verdict, so
  expected machine false-qualifier count under a global null is zero by
  construction. This is an accounting statement, not evidence. No row is hidden,
  dropped, or relabelled by n, interval, sign, or control result. F02/F04/F06 are
  not applicable: there is no battery selection, path-dependent exit, or phase-
  shift retention gate. F07 is satisfied by retaining every realised row.
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
