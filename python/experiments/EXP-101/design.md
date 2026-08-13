# EXP-101 — Level significance and later swing outcomes

- **Family:** `CF-LIQSWP-001/HYP-001`
- **Checkpoint:** `2026-08-11-019-liquidity-sweeps`
- **Status:** design amended through AMENDMENT-13; fresh QA pending
- **Vehicle:** analysis-only re-analysis of the frozen EXP-100 Nautilus emission; no new `BacktestNode`, no re-emission
- **Scope:** cTrader TRAIN only; `EURUSD`, `XAUUSD`, `USTEC`; 264 frozen cells

## Frozen source contract

```text
FROZEN-SOURCE:
  root: data/nautilus_runs/EXP-100/full/
  family_gate: python/experiments/EXP-100/results/estimand_validation.json
  gate_precondition: family_gate.blocking_pass=true; n_cells=264; every
    python/experiments/EXP-100/results/execution/full/<cell_id>.json has
    blocking_pass=true; do not read any source row before this check.
  per_cell_inputs: run_metadata.json, raids.parquet, tpo_profiles.parquet,
    bar_marks.parquet, raids_destroyed.parquet, event_log.jsonl.
  fence: INFR-021 cTrader TRAIN, 2021-06-02T00:01:00Z through
    2023-11-22T00:00:00Z; manifest SHA256
    4cdc7b01dd47200710d0d961639d55d52e1129ca89096e841eafd816b6061de0.
  seal: each cell uses its own run_metadata.config_hash and
    run_metadata.event_log_sha256; emission_contract_version=nautilus-emission-v1;
    Nautilus=1.230.0; cost_model=NO_COST_CHARGED; one_backtest_node=true.
  analysis_boundary: read-only Python analysis under analysis_code/; no new
    Nautilus process, no new emission, no TEST, and no holdout access.
```

The frozen raid field map is exact: `config`/`source_configuration` identifies the
level configuration; `raid_id` and `level_id` preserve object identity;
`swing_atr`, `swing_price`, `swing_bps`, `strong_move`, and `duration_ns` are the
outcomes. The analysis alias `swing_duration_ns` means `duration_ns` exactly; it is
not an emitted column. Display hours are `duration_ns / 3_600_000_000_000`.

## Mechanism

```text
MECHANISM: If level degree carries significance, raids of higher-degree or
longer-window levels should have different later-swing distributions than raids
of lower-degree levels, after the same causal raid definition. The unit is the
level-attributed raid and its later confirmed swing.
DERIVED: estimand=per-stratum outcome distributions and direct fixed-baseline
contrasts; null=cross-configuration future-destroyed outcome alignment;
horizon=confirmation to first opposing event or censor; test=clustered direct
mean/median and paired-label contrasts.
```

## Object identity

```text
OBJECT-IDENTITY:
  measurement object == trading object: YES — the same emitted level-attributed
    raid supplies the measured outcome; no synthetic entry is substituted.
  measured conditioning event == traded entry event: N/A — this is an event study,
    not a deployment strategy and emits no orders or fills.
  effect-splitting windows non-overlapping: YES — each raid owns its excursion,
    confirmation, and later-swing intervals; repeated level dependence is clustered
    by level_id.
```

## Scope and estimand

Every read is separate by `archive_symbol × timeframe × confirmation_method ×
confirmation_reference × side × config`. The exact configuration set is:

- Family A: `PREVIOUS_1H`, `PREVIOUS_4H`, `PREVIOUS_1D`, `PREVIOUS_1W`.
- Family B: `PREVIOUS_ASIA`, `PREVIOUS_EUROPE`, `PREVIOUS_AMERICA`.
- Family C: `ROLLING_7`, `ROLLING_14`, `ROLLING_22`, `ROLLING_252`.

The fixed comparator is `PREVIOUS_1H` for Family A, `PREVIOUS_ASIA` for Family B,
and `ROLLING_7` for Family C, always within the same named asset/timeframe/method/
reference/side stratum. Ordered degree reads and pairwise reads are disclosures
against those fixed comparators; no adaptive arm is compared with another adaptive
arm and no machine significance label is emitted.

Raw population: every raid row from every frozen cell, including
`COMPLETED`, `CONFIRMED_NON_PRIMARY`, `FAILED_BREAKOUT`, all right-censor statuses,
undefined/null outcomes, and thin cells. Primary later-swing population:
`status=COMPLETED AND primary_attribution=true AND primary_completed=true`.
`RIGHT_CENSORED_ENDPOINT` is retained in a censor table and is not silently treated
as a completed endpoint. Failed, excursion-censored, confirmation-censored, and
non-primary rows remain visible with counts and null reasons; they do not enter the
complete later-swing denominator. `swing_atr`, `swing_bps`, `swing_duration_ns`,
and `strong_move` are read only from the stated primary population.

Primary summaries are mean and median outcome levels with five-seed clustered
block-bootstrap intervals over `level_id`; block sensitivity is reported. The
binary `strong_move` read is a paired proportion/delta with the same level cluster.
All rows retain `n`; pooled figures are disclosure-only.

## Control and tripwire

```text
CONTROL CONFIG_CROSSWISE_FUTURE_DESTROY:
  question answered: does the level-configuration contrast require alignment of
    the real post-confirmation path rather than event counts or labels alone?
  population: rows carrying an outcome block, grouped by exact
    archive_symbol × timeframe × confirmation_method × confirmation_reference ×
    side × status × primary_completed × outcome-nullness class; configurations
    are pooled within each group, not separated.
  mapping: deterministically move outcome blocks (swing_price, swing_bps,
    swing_atr, duration_ns, strong_move) to a different configuration row; use a
    zero-fixed-point derangement and reject any same-configuration assignment.
    Event fields, configuration labels, status, eligibility, missingness, and
    row counts stay fixed. A group with no feasible cross-configuration map is
    reported N/A with its count, never dropped.
  DISJOINT from signal population: the destroy is a separate future-block
    alignment and does not alter the raw event/configuration rows.
  bite: a pre-read synthetic fixture plants a known +0.50 ATR contrast between
    two current configuration labels at fixed population size; the crosswise
    destroy must remove that planted label/outcome alignment.
  non-vacuity: it changes the sufficient statistics of swing_atr, duration_ns,
    and strong_move while preserving their global block multiset.
  expected outcome if H true: direct configuration contrasts collapse toward the
    fixed same-stratum comparator; if H false: a contrast remains.
  disclosure: raw/destroy contrast, collapse fraction, fixed points, and mapped
    row count are reported per stratum.
  destroy form: DERANGEMENT (zero fixed points).

TRIPWIRE: CONFIG_CROSSWISE_FUTURE_DESTROY
  must collapse the level/configuration outcome alignment;
  vacuity check: outcome blocks move across configuration labels and the planted
    contrast changes, so the control can referee this estimand;
  if permutation-based: derangement=YES (zero fixed points; L-28);
  integrity_bite: INTEGRITY_Z × bootstrap_SE from the same contrast estimator,
    INTEGRITY_Z=2.8; this is validity only, never MDE or a research floor.
```

The existing EXP-100 within-configuration destroy remains an apparatus integrity
receipt, but it is not used as the sole HYP-001 contrast control because it preserves
each configuration's outcome distribution.

## Interpretation and sample size

```text
BANDS (per stratum, operator-only):
  SUPPORTED: direct contrast is positive with its reported interval;
  WASH: the direct contrast is small or interval-overlapping;
  CONTRADICTED: direct contrast is negative with its reported interval.
  These are report-layer tags only; never machine fields, gates, or row filters.
POOLED: disclosure-only unless asset and venue homogeneity is demonstrated.
SAMPLE-SIZE:
  expected events per stratum: measured from the frozen emission; planning context only.
  minimum_n_for_primary_inference: none; counts and intervals remain for every row.
  declared_fixed_comparator: the named Family A/B/C baseline above.
  channels:
    - name: continuous swing and duration contrasts
      sigma_denominator: outcome_level
    - name: strong_move paired labels
      sigma_denominator: paired_delta
  strata predeclared thin: every asset × timeframe × method × reference × side × config.
```

No trade or leg-bps series exists; PSR is explicitly **N/A**. No MDE, power curve,
detection floor, `UNPOWERED` machine label, or count veto is allowed.

## Golden trace

```text
GOLDEN-TRACE:
  T1 (2023-01-03T10:00:00Z, 15m/1H): distinct PREVIOUS_1H and ROLLING_7 high
    levels both have price=100.00. The completed observation bar has
    high=101.20, low=100.80, close=101.00, causal raid_atr=1.00. Two distinct
    raid rows start with prior_raid_count=0, max_excursion=1.20, and null return.
  T2 (2023-01-03T10:15:00Z): low=100.00 records return_ts_ns for both rows;
    AMENDMENT-13 keeps both raids live. A later 1H expected-side close at
    2023-01-03T11:00:00Z settles the latest row primary and the earlier row
    CONFIRMED_NON_PRIMARY; the two config/level identities remain separate.
  T3 (2023-01-03T12:00:00Z): the first opposing reference event ends the primary
    swing. With level=100.00, raid_atr=1.00, post-confirm favorable extreme=98.00,
    the primary row has swing_price=2.00, swing_atr=2.00, swing_bps=200.0,
    duration_ns=3_600_000_000_000, and strong_move=true when max_excursion=1.20.
```

## Governance, amendments, and final null

```text
HARD (block): frozen family estimand gate; holdout exclusion; causal timestamp
  provenance; schema/object reconciliation; no-local-accounting; deterministic
  read; CONFIG_CROSSWISE_FUTURE_DESTROY integrity; zero-cost compliance.
INFORMATIVE (operator judges): all effect sizes, intervals, frequencies, labels,
  robustness reads, and collapse fractions.

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

FINAL-NULL / SELECTION ACCOUNTING:
  final gate set is the complete 2L/3T/7N ledger above. There is no candidate
  qualification gate, capped-read selection rule, or machine value verdict;
  therefore expected machine false-qualifier count under a global null is zero
  by construction. The future-destroy result is a validity attestation, not a
  value qualifier. No battery eligibility rule is applied, no rows are hidden,
  and no status transition is automated. No one-directional amendment streak
  reaches three. F02 time-stability, F04 exit-matched null, and F06 derived
  phase-shift threshold rules are N/A: this is a frozen no-exit read with no
  battery selection or phase-shift retention gate. F07 is satisfied by retaining
  every realised count and interval.
```

## Zero-cost disclosure

```text
ZERO-COST-DISCLOSURE:
  cost_model: NO_COST_CHARGED
  spread: not modeled
  commissions: not modeled
  swaps/funding: not modeled
  implication: every figure in this document is gross and cost-free; no spread, commission,
  or swap enters any calculation. Realised results would differ (likely worse) under any
  real cost schedule.
  prohibited_claims: fully-net, cost-complete, tradable, deployable
  lifting: only an explicit operator directive may introduce a cost model for a scoped
  experiment; the directive is recorded in that experiment's design.md.
```
