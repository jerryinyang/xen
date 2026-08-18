# EXP-102 — Repeated raids and prior-raid count

- **Family:** `CF-LIQSWP-001/HYP-002`
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
```

The binding EXP-100 decision excludes every
`profile_undefined_reason=ATR_UNDEFINED` row from excursion, normalized-excursion,
`strong_move`, and excursion-derived interpretation without repair or substitution.
All rows, counts, statuses, and reasons remain visible. `pre_mfe_retrace={price,status}`
is retained as source metadata but is outside HYP-002.

Frozen field map: design term “previous completed raid count” is exactly emitted
`prior_raid_count`; no `previous_raid_count` field is invented. The canonical duration
source is `swing_duration_ns`; emitted `duration_ns` is its byte-equal compatibility
alias. Assert equality before reading duration and display hours as
`swing_duration_ns / 3_600_000_000_000`. Outcome fields are `swing_price`, `swing_bps`,
`swing_atr`, `swing_duration_ns`, and `strong_move`.

## 2. Mechanism and object identity

```text
MECHANISM: Multiple completed raids of one persistent liquidity level may change the
later-swing distribution. Each raid remains a separate object and carries the count
of earlier completed raids on that same level; the level is the dependence cluster.
DERIVED: estimand=outcomes by exact prior-raid count and fixed count-zero
comparators; null=cross-count future-destroyed outcome alignment;
horizon=confirmation through the first opposing reference event or TRAIN censor;
test=non-parametric direct count-band contrasts with a clustered unpaired
strong-move proportion contrast; pnl_object=none because this event study
contains no trade, leg, episode, or capital estimand.
```

```text
OBJECT-IDENTITY:
  measurement object == trading object: YES — each emitted level-linked raid and
    its later swing are measured directly; no collapsed level or synthetic entry is used.
  measured conditioning event == traded entry event: N/A — this is a descriptive
    event study with no deployment rule, orders, fills, or P&L ledger.
  effect-splitting windows non-overlapping: YES — every raid owns its own excursion,
    confirmation, and later-swing interval; shared level history is clustered by level_id.
```

## 3. Scope, population, and estimand

Every result row is separate by
`archive_symbol × timeframe × confirmation_method × confirmation_reference × side × config`.
Every raid remains in the census. Report exact `prior_raid_count` and fixed descriptive
bands `0`, `1`, and `2+`; these bands are grouping variables, not new emission labels,
gates, or selection rules.

The fixed comparator is `prior_raid_count=0` within the same named stratum. No band is
compared with another adaptive or selected band. The later-swing population is exactly:

```text
status == COMPLETED
and primary_attribution == true
and primary_completed == true
```

`CONFIRMED_NON_PRIMARY`, `FAILED_BREAKOUT`,
`RIGHT_CENSORED_EXCURSION`, `RIGHT_CENSORED_CONFIRMATION`, and
`RIGHT_CENSORED_ENDPOINT` rows remain in status/censor tables. Non-primary rows are
never treated as later-swing endpoints merely because a convenience field is non-null.
No imputation or silent denominator change is allowed.

Primary estimators are arm-minus-count-zero differences in mean `swing_atr` (where
finite) and mean `swing_duration_ns`; medians are robust secondary disclosures.
`strong_move` is an unpaired difference in proportions under the same level-cluster
resampling; no raid pairing is asserted. `swing_price` and `swing_bps` are finite
source summaries and are not separate hard tripwire estimands. ATR-undefined rows
remain countable but are excluded from `swing_atr`, `strong_move`, and excursion-derived
interpretation under the operator decision.

## 4. Estimator and neutral report contract

A cluster is the complete history of one `level_id`, including all count bands it
contributes. Sort clusters by `(first_raid_timestamp, level_id)`. Because one level
can contribute rows to multiple count bands, all arms are resampled **jointly** from
the same cluster sequence.

For each requested block length `L`:

1. If count zero or a requested arm has no eligible observation, emit all counts,
   null estimate/interval, and `EMPTY_ARM`; keep the row and do not infer a direction.
2. If `n_clusters >= 2`, set `L_eff=min(max(1,L), n_clusters-1)`. Draw
   `ceil(n_clusters/L_eff)` starts uniformly from `[0,n_clusters)`, append
   `L_eff` circularly consecutive whole clusters per start, and truncate to the
   first `n_clusters`. This retains the joint count composition of each resample.
3. Recompute both arm statistics and the arm-minus-zero contrast on every resample.
   Use 10,000 resamples for seeds `0,1,2,3,4`; use NumPy `linear` quantiles for the
   95% percentile interval. Report each seed's bounds, median bounds, and seed-bound
   ranges. Default `L=5`; sensitivity `L=2` and `L=10`, each capped by the same rule.
4. Report every count band, status, missingness, censor reason, estimate, interval,
   and seed result. Pooled figures are disclosure-only.

```text
REPORT-LAYERS:
  observed: counts, count-band composition, exclusions, means, medians, direct
    contrasts, intervals, seed ranges, and destroyed-control distributions by stratum.
  ideal: count-zero is the fixed comparator and the estimator/population are held
    constant; no pass/fail or post-outcome comparator exists.
  interpretation: the analyst states direction, interval overlap, robustness,
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

## 5. Cross-count future destroy and validity tripwire

```text
CONTROL COUNT_CROSSWISE_FUTURE_DESTROY:
  question answered: does a prior-raid-count/outcome contrast require the aligned
    future movement rather than the count label or repeated-event distribution alone?
  population: outcome-bearing rows grouped by exact
    archive_symbol × timeframe × confirmation_method × confirmation_reference ×
    side × config × status × primary_completed × outcome-nullness class. Count
    values are pooled within each group. The nullness class is the five-bit tuple
    (is_null(swing_price), is_null(swing_bps), is_null(swing_atr),
    is_null(duration_ns), is_null(strong_move)); duration_ns is the asserted alias
    of swing_duration_ns.
  mapping: copy the raw rows; sort each group by (raid_id, original_row_position).
    For each seed d=0..1999, draw default_rng(d).permutation(n) and reject/re-draw
    until perm[i] != i for every recipient i. Move the complete outcome block
    (swing_price, swing_bps, swing_atr, swing_duration_ns, duration_ns,
    strong_move) from donor perm[i] to recipient i. The donor count may equal the
    recipient count; forbidding it can swap two count arms and preserve the absolute
    contrast. Level/event fields, count labels, status, eligibility, nullness, and
    row counts stay fixed. A group with n<2 stays fixed and is disclosed via the
    group-size report; it does not void the control, because its rows contribute
    identically to the raw and destroyed contrasts (AMENDMENT-16). The control
    voids only when no group is movable (VOID_NO_MOVABLE_ROWS) or no eligible
    value changes (VOID_NO_CHANGED_VALUE).
  DISJOINT from signal population: the destroy is calculated on a separate copy
    after the raw estimate; it cannot alter raw raid identity, count labels,
    timestamps, or the signal population.
  bite: the pre-read fixture in the tripwire block plants +0.50 ATR,
    +3_600_000_000_000 ns, and +0.25 proportion contrasts; its destroyed means
    must satisfy the declared validity inequalities before live rows are read.
  non-vacuity: the mapping changes sufficient statistics of swing_atr,
    swing_duration_ns, and strong_move while preserving the global outcome-block
    multiset and exactly zero fixed points.
  expected outcome: if an aligned count relationship exists, the direct contrast
    moves toward zero after destruction; otherwise raw and destroyed contrasts are
    both reported without a mechanism claim.
  disclosure: raw contrast; all 2,000 destroyed contrasts; their mean and empirical
    95% interval; collapse_fraction = mean_destroyed/raw (control-to-raw ratio);
    fixed-point count; changed-field count; mapped-row count; and any VOID reason.
  destroy form: 2,000 DERANGEMENTS (zero fixed points each).
```

```text
TRIPWIRE: COUNT_CROSSWISE_FUTURE_DESTROY
  must collapse the aligned count/outcome contrast when a raw contrast is present;
    the fixture's destroyed-to-raw ratio is expected near zero. Live ratios are
    disclosed, not used as value thresholds.
  vacuity check: outcome blocks move across fixed count labels while the event
    population and marginal outcome blocks remain fixed, so this destroy can change
    this count contrast.
  authority: HARD validity only. It never assigns value, quality, power, or
    significance labels. Its authorized estimators are the raw same-population
    mean swing_atr contrast, mean swing_duration_ns contrast, and unpaired
    strong_move proportion contrast defined in §3.
  outer bootstrap: for each seed s=0..4, generate 10,000 joint level-cluster
    populations using §4. For every population b, recompute D_raw[s,b] and all
    2,000 deranged contrasts D_destroy[s,b,d]. Set
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
    per seed). If that
    inequality fails, mark the affected stratum/channel invalid as
    VOID_FUTURE_DESTROY_SURVIVAL; do not interpret it as evidence against the
    mechanism. If D_raw is zero or non-finite, collapse_fraction is NaN and the
    live collapse attestation is not applicable. If no seed satisfies the raw
    inequality, report the control but do
    not claim a live collapse attestation. A missing statistic, failed derangement,
    or failed reconciliation is also invalidity, never a null result.
  integrity_bite: INTEGRITY_Z=2.8. This is the same-estimator bootstrap standard
    error used only for validity; it is not MDE, a detection floor, a value floor,
    or a row-selection rule.
  fixture before live analysis: use 200 rows per count arm with identical fixed
    labels and no nulls. For swing_atr, alternate count-zero 0.90/1.10 and count-one
    1.40/1.60 (raw contrast +0.50). For duration, alternate count-zero
    3_000_000_000_000/4_200_000_000_000 and count-one
    6_600_000_000_000/7_800_000_000_000 (raw contrast
    +3_600_000_000_000 ns). For strong_move, set true at one quarter of count-zero
    positions and one half of count-one positions (raw proportion contrast +0.25).
    Every seed and channel must satisfy the raw-bite and destroyed-non-bite
    inequalities above. Failure blocks the affected live control implementation.
```

The retained EXP-100 within-configuration destroy is an apparatus receipt only; it
preserves count-band marginals and cannot validate HYP-002.

## 6. Sample size, complexity, and integrity boundary

```text
SAMPLE-SIZE:
  expected events per stratum: measured from the retained emission; planning context only.
  minimum_n_for_primary_inference: none; every realised count/status row retains n,
    estimate, interval, exclusions, and reason codes.
  declared_fixed_comparator: prior_raid_count=0 in the same named stratum.
  channels:
    - name: mean swing_atr
      sigma_denominator: outcome_level
    - name: mean swing_duration_ns
      sigma_denominator: outcome_level
    - name: strong_move proportion difference
      sigma_denominator: unpaired_proportion_delta
  strata predeclared thin: every asset × timeframe × method × reference × side ×
    config × count band, including empty arms and ATR-undefined reason rows.
COMPLEXITY-BUDGET:
  estimators: one direct count-band contrast plus median/quantile disclosures; no
    parametric test. control: one 2,000-seed future destroy and one 5-seed outer
    bootstrap battery. plots: at most three purpose-specific distribution/contrast
    plots; pooled plots are disclosure-only. analysis modules: one independent module.
```

```text
HARD (block): source gate-first check; TRAIN/holdout fence; causal timestamp
  provenance; schema/object/count reconciliation; no-local-accounting;
  deterministic analysis; binding ATR_UNDEFINED exclusion; future-destroy
  validity; and zero-cost compliance.
INFORMATIVE (operator judges): every observed count, effect, interval, frequency,
  distribution, robustness read, control ratio, and cross-stratum comparison.
```

There is no trade or leg-bps series, so PSR is **N/A**. No cost, spread, commission,
swap, power calculation, detection threshold, sample-size veto, automatic label, or
family disposition is in scope.

## 7. Deterministic fixture cluster contract

The pre-source fixture used by `analysis_code/analysis.py --fixture-only` has exactly
200 rows in count band `0` and 200 rows in count band `1` (the `2+` band is represented
in the live census and remains reportable). Each row is its own complete level cluster:
`level_id=FIXTURE-0-level-{i:04d}` for band 0 and
`FIXTURE-1-level-{i:04d}` for band 1, cluster size one, with
`first_raid_timestamp=1700000000000000000 + i*900000000000`. Both arms use
`config=FIXTURE_CONFIG`. Rows are deterministically permuted with seed=4 and then
assigned `raid_id=fixture-raid-{position:04d}`.
Ordering is the complete lexicographic `(first_raid_timestamp, level_id)` order; no
row order or arm sort is used as a substitute. Fixture outcomes alternate within each
arm exactly as declared in the tripwire (+0.50 ATR, +3,600,000,000,000 ns, +0.25
strong-move contrast), and all status, nullness, and fixed-field labels are identical.
The pre-read fixture uses 10 outer-bootstrap replicates for speed; live analysis uses
the declared 10,000.
Every control still uses exactly 2,000 destroys with seeds `d=0..1999`; each group
constructs `default_rng(d).permutation(n)` and rejects fixed points, moves the complete
outcome block, and leaves the source copy unchanged. The fixture records both
`bootstrap_SE_raw` and `bootstrap_SE_mean_destroyed` and applies `INTEGRITY_Z=2.8`.

## 8. Golden trace

```text
GOLDEN-TRACE (BREAKOUT_BAR; 15m observation, 1H reference):
  T1 (2023-01-03T10:00:00Z): one PREVIOUS_1H high level is 100.00. The completed
    15m bar is high=101.20, low=100.80, close=101.00; it starts a raid with
    prior_raid_count=0, max_excursion=1.20, and no return yet.
  T2 (2023-01-03T10:15:00Z and 10:30:00Z): the first raid touches 100.00 at
    10:15 and remains live. The 10:30 completed 15m bar has high=101.50,
    low=100.90, close=101.20 and starts a second raid on the same level. It has
    the same level_id and prior_raid_count=1; the first row remains present.
  T3 (reference close 2023-01-03T11:00:00Z): the previous completed 1H reference
    bar has low=99.50. The completed 1H bar has OHLC=(100.50,101.00,98.00,99.40),
    so close<99.50 is the expected-side event for the high level. It assigns the
    later raid primary_attribution=true and the first
    CONFIRMED_NON_PRIMARY. At 2023-01-03T12:00:00Z the next completed 1H bar has
    previous reference high=101.00 and OHLC=(99.40,101.20,99.20,101.10), so
    close>101.00 is the opposing event and completes only the primary row.
    Expected swing_duration_ns=duration_ns=3_600_000_000_000. A same-bar return
    never closes either raid.
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
AMENDMENT-14: add pre_mfe_retrace without changing HYP-002 — DIRECTION: NEUTRAL
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

FINAL-NULL / SELECTION ACCOUNTING:
  final design has 4 looser / 3 tighter / 8 neutral amendments. It has no
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
