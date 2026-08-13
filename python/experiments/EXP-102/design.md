# EXP-102 — Repeated raids

- **Family:** `CF-LIQSWP-001/HYP-002`
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

Frozen field map: design term **previous completed raid count** is the emitted
`prior_raid_count` column exactly; no `previous_raid_count` column is invented.
Design term `swing_duration_ns` is the emitted `duration_ns` exactly, with display
hours equal to `duration_ns / 3_600_000_000_000`. Outcomes are
`swing_atr`, `swing_price`, `swing_bps`, `duration_ns`, and `strong_move`.

## Mechanism

```text
MECHANISM: Repeated completed raids of the same persistent liquidity level may
change the distribution of the eventual swing. Each raid is a separate object,
linked to one level and carrying the number of previous completed raids.
DERIVED: estimand=outcomes by exact prior-raid count and fixed count-zero
comparators; null=cross-count future-destroyed outcome alignment;
horizon=confirmation to opposing event or censor; test=level-clustered direct
count-band contrasts.
```

## Object identity

```text
OBJECT-IDENTITY:
  measurement object == trading object: YES — every emitted raid remains an
    individual level-linked event; no collapsed level aggregate is substituted.
  measured conditioning event == traded entry event: N/A — no deployment rule,
    fills, or P&L ledger is in scope.
  effect-splitting windows non-overlapping: YES — each raid owns one excursion,
    confirmation, and later-swing interval; later raids never overwrite earlier
    rows. Shared level dependence is clustered by level_id.
```

## Scope, population, and estimand

Every row from every frozen cell remains in the raw population. Report exact
`prior_raid_count` and fixed descriptive bands `0`, `1`, and `2+`; the band is a
report grouping, not an emission label or gate. Strata are
`archive_symbol × timeframe × confirmation_method × confirmation_reference × side × config`.
The fixed comparator is `prior_raid_count=0` within that same named stratum; all
count bands remain visible even when the comparator or a band is thin.

Primary later-swing population is exactly
`status=COMPLETED AND primary_attribution=true AND primary_completed=true`.
`CONFIRMED_NON_PRIMARY` rows are retained as confirmation/profile-only rows and
are not used as later-swing endpoints, even if a convenience field is non-null.
`FAILED_BREAKOUT`, `RIGHT_CENSORED_EXCURSION`, `RIGHT_CENSORED_CONFIRMATION`, and
`RIGHT_CENSORED_ENDPOINT` remain in status/censor tables with their counts and
nullness. No imputation or silent denominator change is allowed.

Primary continuous reads use `swing_atr`, `swing_bps`, and `duration_ns`; binary
`strong_move` is secondary. Five-seed level-clustered block-bootstrap intervals,
block sensitivity, mean/median summaries, and paired label deltas are reported.
No row is removed because its count, status, or interval is inconvenient.

## Control and tripwire

```text
CONTROL COUNT_CROSSWISE_FUTURE_DESTROY:
  question answered: does the prior-raid-count contrast require aligned future
    movement rather than the count label or repeated-event distribution alone?
  population: rows carrying an outcome block, grouped by exact
    archive_symbol × timeframe × confirmation_method × confirmation_reference ×
    side × config × status × primary_completed × outcome-nullness class; count
    values are pooled within each group, not separated.
  mapping: deterministically move outcome blocks (swing_price, swing_bps,
    swing_atr, duration_ns, strong_move) to a row with a different prior_raid_count
    or count band; use a zero-fixed-point derangement. Keep level/event fields,
    count labels, status, eligibility, missingness, and row counts fixed. If a
    group has no feasible cross-count map, report N/A with its count, never drop it.
  DISJOINT from signal population: the destroy is a separate future-block
    alignment and does not alter raw raid identity or count labels.
  bite: a pre-read fixture plants a known +0.50 ATR contrast between count-zero
    and count-one rows at fixed status and population; the crosswise destroy must
    remove that count/outcome alignment.
  non-vacuity: it changes the sufficient statistics of swing_atr, duration_ns,
    and strong_move while preserving the global outcome-block multiset.
  expected outcome if H true: count-band contrasts collapse toward count zero;
    if H false: a contrast remains.
  disclosure: raw/destroy contrast, collapse fraction, fixed points, and mapped
    row count per stratum.
  destroy form: DERANGEMENT (zero fixed points).

TRIPWIRE: COUNT_CROSSWISE_FUTURE_DESTROY
  must collapse the repeated-raid-count/outcome alignment;
  vacuity check: outcome blocks move across count labels and the planted contrast
    changes, so this control can referee HYP-002;
  if permutation-based: derangement=YES (zero fixed points; L-28);
  integrity_bite: INTEGRITY_Z × bootstrap_SE from the same count-contrast
    estimator, INTEGRITY_Z=2.8; validity only, never MDE or a research floor.
```

The existing EXP-100 within-configuration destroy is retained as an apparatus
receipt, but it is not sufficient for HYP-002 because it preserves count-band
marginals when count is not the mapping variable.

## Interpretation and sample size

```text
BANDS (per stratum, operator-only):
  SUPPORTED: direct count-band contrast is positive with its reported interval;
  WASH: direct contrast is small or interval-overlapping;
  CONTRADICTED: direct contrast is negative with its reported interval.
  These are report-layer tags only; never machine fields, gates, or row filters.
POOLED: disclosure-only.
SAMPLE-SIZE:
  expected events per stratum: measured from the frozen emission; planning context only.
  minimum_n_for_primary_inference: none; every count/status row is reported.
  declared_fixed_comparator: prior_raid_count=0 in the same named stratum.
  channels:
    - name: continuous swing and duration contrasts
      sigma_denominator: outcome_level
    - name: strong_move paired labels
      sigma_denominator: paired_delta
  strata predeclared thin: every asset × timeframe × method × reference × side × config × count band.
```

No trade or leg-bps series exists; PSR is explicitly **N/A**. No MDE, power curve,
detection floor, `UNPOWERED` machine label, or count veto is allowed.

## Golden trace

```text
GOLDEN-TRACE:
  T1 (2023-01-03T10:00:00Z, 15m/1H): one PREVIOUS_1H high level at 100.00
    is raided by a completed bar high=101.20, low=100.80, close=101.00;
    the row has prior_raid_count=0, max_excursion=1.20, and null return.
  T2 (2023-01-03T10:15:00Z and 10:30:00Z): the first raid returns at 10:15;
    a later completed observation bar with high=101.50, low=100.90, close=101.20
    starts a second raid on the same level. The second row has the same level_id
    and prior_raid_count=1. The first row remains present; neither row is collapsed.
  T3 (2023-01-03T11:00:00Z): the expected-side 1H close settles the second/latest
    row as primary and the first as CONFIRMED_NON_PRIMARY. At 12:00:00Z the
    opposing reference event completes only the primary row. Expected flags are
    first: primary_attribution=false/primary_completed=false; second:
    primary_attribution=true/status=COMPLETED, with duration_ns equal to one hour
    from confirmation to endpoint. A same-bar return never closes either raid.
```

## Governance, amendments, and final null

```text
HARD (block): frozen family estimand gate; holdout exclusion; causal timestamp
  provenance; schema/object/count reconciliation; no-local-accounting;
  deterministic read; COUNT_CROSSWISE_FUTURE_DESTROY integrity; zero-cost compliance.
INFORMATIVE (operator judges): count distributions, all outcome sizes, intervals,
  status/censor rates, robustness reads, and collapse fractions.

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
  expected machine false-qualifier count under a global null is zero by
  construction. The future-destroy result is a validity attestation, not a value
  qualifier. No battery eligibility rule is applied, no rows are hidden, and no
  status transition is automated. No one-directional amendment streak reaches
  three. F02 time-stability, F04 exit-matched null, and F06 derived phase-shift
  threshold rules are N/A: there is no battery selection, path-dependent exit,
  or phase-shift retention gate. F07 is satisfied by retaining every realised
  count, status, interval, and censor reason.
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
