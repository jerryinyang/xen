# EXP-104 — Volatility-regime conditioning

- **Family:** `CF-LIQSWP-001/HYP-004`
- **Checkpoint:** `2026-08-11-019-liquidity-sweeps`
- **Status:** design amended through AMENDMENT-13; fresh QA pending
- **Vehicle:** analysis-only re-analysis of the frozen EXP-100 Nautilus emission; no new `BacktestNode`, no re-emission
- **Scope:** cTrader TRAIN only; `EURUSD`, `XAUUSD`, `USTEC`; 264 frozen cells

## Frozen source and join contract

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

JOIN:
  raid regime/outcome reads use raids.parquet. Profile/tight-gap fields, when
  disclosed, are a left join from raids to tpo_profiles on
  (raid_id, profile_generation). Missing/extra joins and undefined profiles stay
  visible; no inner join or outcome-based row removal is allowed.
```

## Mechanism and causal regime definition

```text
MECHANISM: Causal volatility state may change the frequency, size, duration, and
quality of liquidity raids and their later swings. The regime is measured from
completed same-asset observation-timeframe bars before the event and is never
rewritten by later volatility.
DERIVED: estimand=raid and primary-outcome distributions by emitted causal regime;
null=cross-regime future-destroyed outcome alignment; horizon=raid through opposing
confirmation or censor; test=direct LOW/MID/HIGH descriptive contrasts.
```

```text
OBJECT-IDENTITY:
  measurement object == trading object: YES — regime labels attach to the same
    emitted level/raid/swing objects; no proxy trade is substituted.
  measured conditioning event == traded entry event: N/A — no deployment strategy,
    fills, or P&L ledger is in scope.
  effect-splitting windows non-overlapping: YES — event labels are snapshots at
    raid, excursion, confirmation, and endpoint; the underlying outcome interval
    is not rewritten or counted as a second effect window.
```

`CausalWilderATR(14)` is updated only on completed observation bars. The source
feature is `x_t = ATR_t / close_t`. `CausalVolatilityRegime` appends the current
finite positive `x_t` to its maximum-252-value window before ranking it. Percentile
boundaries use sorted values and linear interpolation at positions
`(n-1)*0.33` and `(n-1)*0.67`; values strictly below the lower boundary are LOW,
strictly above the upper boundary are HIGH, and equality is MID. Fewer than 252
retained values emit `REGIME_WARMUP`; non-finite/non-positive ATR emits
`ATR_UNDEFINED`.

Event-time field authority is the frozen raid schema, not a re-computed analysis
feature: `raid_atr`/`raid_regime` and `excursion_atr`/`excursion_regime` are the
cached state available before the relevant event's observation update;
`confirmation_atr`/`confirmation_regime` and `endpoint_atr`/`endpoint_regime` are
the cached state at their completed reference event. `bar_marks.regime` is the
post-update observation label and is used only for a timestamp consistency check;
it must not overwrite an emitted raid label. A timestamp join to the immediately
preceding observation mark is used to audit raid-regime causality, never a bar index.

## Scope, population, and estimand

Report all cTrader assets, observation timeframes, level configurations,
confirmation methods/references, and sides separately. Raw population includes
every raid, every regime state (LOW/MID/HIGH/WARMUP/ATR_UNDEFINED), every status,
all right-censor rows, and all profile join reasons.

Primary later-swing population is exactly
`status=COMPLETED AND primary_attribution=true AND primary_completed=true`.
`RIGHT_CENSORED_ENDPOINT` is reported as censored, not completed; failed,
confirmation-censored, excursion-censored, and non-primary rows remain visible and
are excluded from the complete later-swing denominator. Primary conditioning uses
`raid_regime`; confirmation and endpoint regimes are secondary event-time strata.
Raid frequency is a count of raid starts per completed observation bar, with the
preceding-bar regime exposure reconstructed by timestamp and cross-checked against
`raid_regime`; if the exposure state is unavailable, the count is reported without
an invented rate.

Primary outcomes are `swing_atr`, `swing_bps`, `duration_ns`, and `strong_move`.
Five-seed level-clustered block-bootstrap intervals, block sensitivity, mean/median
summaries, and paired-label deltas are reported. No machine regime label or value
verdict is assigned. No trade/leg-bps series exists; PSR is explicitly N/A.

## Control and tripwire

```text
CONTROL REGIME_CROSSWISE_FUTURE_DESTROY:
  question answered: do regime-conditioned outcome differences require aligned
    future movement rather than regime labels, event counts, or calendar state?
  population: rows carrying an outcome block, grouped by exact
    archive_symbol × timeframe × confirmation_method × confirmation_reference ×
    config × side × status × primary_completed × outcome-nullness class; regime
    labels are pooled within each group.
  mapping: deterministically move post-confirmation outcome blocks
    (swing_price, swing_bps, swing_atr, duration_ns, strong_move) to a row with a
    different LOW/MID/HIGH regime label; preserve raid/excursion/confirmation/
    endpoint regime fields, event fields, status, eligibility, missingness, and
    row counts. Use a zero-fixed-point derangement. Groups without at least two
    regime labels are reported N/A with their counts, never dropped.
  DISJOINT from signal population: the destroy changes only future outcome-block
    alignment and does not alter causal regime fields or event identity.
  bite: a pre-read fixture plants a known +0.50 ATR outcome contrast between two
    current regime labels at fixed population; the crosswise destroy must remove it.
  non-vacuity: swing_atr, duration_ns, and strong_move sufficient statistics move.
  expected outcome if H true: regime contrasts collapse toward the MID comparator;
    if H false: a contrast remains.
  disclosure: raw/destroy contrast, collapse fraction, fixed points, and mapped
    row count per stratum.
  destroy form: DERANGEMENT (zero fixed points).

TRIPWIRE: REGIME_CROSSWISE_FUTURE_DESTROY
  must collapse the emitted regime/outcome alignment;
  vacuity check: outcome blocks move across fixed regime labels and the planted
    contrast changes, so this control can referee HYP-004;
  if permutation-based: derangement=YES (zero fixed points; L-28);
  integrity_bite: INTEGRITY_Z × bootstrap_SE from the same regime-contrast
    estimator, INTEGRITY_Z=2.8; validity only, never MDE or a research floor.
```

The EXP-100 within-configuration destroy remains an apparatus receipt, not the sole
HYP-004 contrast control, because it can preserve regime-conditioned marginals.

## Interpretation and sample size

```text
BANDS (per stratum, operator-only):
  SUPPORTED: direct regime contrast is positive with its reported interval;
  WASH: direct contrast is small or interval-overlapping;
  CONTRADICTED: direct contrast is negative with its reported interval.
  These are report-layer tags only; never machine fields, gates, or row filters.
POOLED: disclosure-only.
SAMPLE-SIZE:
  expected events per stratum: measured from the frozen emission; planning context only.
  minimum_n_for_primary_inference: none; all regime/status/reason rows remain.
  declared_fixed_comparator: MID regime within the same named asset/timeframe/
    method/reference/config/side stratum; all-regime distribution retained.
  channels:
    - name: continuous outcome and duration contrasts
      sigma_denominator: outcome_level
    - name: strong_move paired labels
      sigma_denominator: paired_delta
    - name: raid frequency counts
      sigma_denominator: event_count
  strata predeclared thin: every asset × timeframe × method × reference × side × config
    and every WARMUP/ATR_UNDEFINED/status reason.
```

No MDE, power curve, detection floor, `UNPOWERED` machine label, or count veto is allowed.

## Golden trace

```text
GOLDEN-TRACE (252-value causal window):
  T1 (2023-01-03T10:00:00Z): before the completed observation update, the cached
    x=ATR/close is 0.80 and the sorted trailing-window boundaries are lower=0.90
    and upper=1.10. A high-level raid starts; emitted raid_atr/raid_regime and
    excursion_atr/excursion_regime are the pre-update values and regime=LOW.
  T2 (2023-01-03T10:15:00Z): the completed observation has x=1.20. The current
    value is appended, so bar_marks.regime=HIGH; the already-emitted raid_regime
    remains LOW and is not rewritten. A value exactly 0.90 or 1.10 would be MID
    because only strict inequalities produce LOW/HIGH.
  T3 (2023-01-03T11:00:00Z and 12:00:00Z): a completed 1H confirmation observes
    the current cached state HIGH, so confirmation_regime=HIGH; a later opposing
    endpoint with x=1.00 has endpoint_regime=MID. The raid's LOW label remains
    unchanged, and each regime field is tied to its own event timestamp.
```

## Governance, amendments, and final null

```text
HARD (block): frozen family estimand gate; holdout exclusion; causal regime
  provenance and timestamp joins; schema/object/outcome reconciliation;
  no-local-accounting; deterministic read; REGIME_CROSSWISE_FUTURE_DESTROY
  integrity; zero-cost compliance.
INFORMATIVE (operator judges): regime frequencies, all outcome sizes, intervals,
  status/censor rates, profile disclosures, robustness reads, and collapse fractions.

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
  regime, status, count, outcome, and interval.
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
