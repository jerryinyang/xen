# EXP-100 — Liquidity-sweep streaming apparatus

- **Family:** `CF-LIQSWP-001/HYP-000`
- **Checkpoint:** `2026-08-11-019-liquidity-sweeps`
- **Status:** performance QA APPROVE; full TRAIN matrix execution next
- **Vehicle:** Nautilus `BacktestNode`, TRAIN only
- **Amendments:** inherits checkpoint AMENDMENT-2 through AMENDMENT-5; no experiment-specific amendment. Counts: **0L / 1T / 3N**.

## Mechanism

```text
MECHANISM: A causal streaming state machine should preserve the identity and
chronology of active liquidity levels, excursions, completed raids, confirmation,
breakout, and later-swing states. This experiment tests measurement validity and
coverage, not market value.
DERIVED: estimand=emitted-state coverage/reconciliation and deterministic replay;
null=future-destroyed post-raid alignment; horizon=full TRAIN band with explicit
right-censoring; test=hard integrity checks plus neutral state summaries.
```

## Object identity

```text
OBJECT-IDENTITY:
  measurement object == trading object: YES — the emitted level/raid object is
    the object used by every later experiment.
  measured conditioning event == traded entry event: N/A — no candidate trade is
    evaluated; engine fills are only granular-path diagnostics.
  effect-splitting windows non-overlapping: YES — each raid owns one event record;
    shared level dependence is represented by level_id, not duplicated objects.
```

## Scope and estimand

Run all three base timeframes, both confirmation methods, both confirmation
references (1H for 15m/30m and 1D for 1h), both venues, and every frozen level
configuration. Verify:

- exact level identity and catalogue membership at each timestamp;
- strict excursion, inclusive return, and explicit ambiguous intrabar handling;
- repeated-raid linkage and most-recent-resolvable attribution;
- confirmation and endpoint chronology;
- TPO profile state, conservation, reset, VA, gap, and tightness fields;
- deterministic replay and artifact hash equality.

## Controls

```text
CONTROL FUTURE_DESTROY:
  question answered: does later outcome state depend on the aligned future path?
  population: the same emitted raid objects with post-confirmation blocks
    deranged within asset × timeframe × configuration.
  bite: changes swing, duration, and strong-move fields while preserving event
    counts and marginal block values.
  non-vacuity: swing_atr and strong_move must change when future blocks move.
  expected outcome if H true: alignment contrast collapses; if H false: it remains.
  disclosure: report fixed points and destroy/raw contrast ratio.
  destroy form: DERANGEMENT, zero fixed points.
```

## Tripwire

```text
TRIPWIRE: future-destroyed post-raid blocks
  must collapse the aligned outcome contrast;
  vacuity check: the destroy changes the outcome fields being reconciled;
  derangement=YES;
  integrity_bite: INTEGRITY_Z × bootstrap_SE, INTEGRITY_Z=2.8.
```

## Interpretation and sample size

```text
BANDS (operator-only): COMPLETE, PARTIAL_COVERAGE, or COVERAGE_GAP may describe
  observed artifact coverage; none is machine-assigned as a value verdict.
SAMPLE-SIZE:
  expected events per stratum: measured by preflight; no count gate.
  minimum_n_for_primary_inference: none.
  declared_fixed_comparator: the synthetic golden trace and same-stratum replay.
  channels: state counts (count); numeric reconciliation (absolute difference).
  strata predeclared thin: every venue × asset × timeframe × configuration cell.
```

## Golden trace

```text
GOLDEN-TRACE:
  T1: high level 100.00; a 1m bar high=101.20; later 1m low=100.00. Emit one
      completed raid with max excursion 1.20 and prior raid count 0.
  T2: a second active high level is raided before confirmation. The later
      resolvable raid receives attribution; both level objects remain emitted.
  T3: the 1H expected-side bar closes; sweep confirmation is timestamped at that
      completed close, not at the next bar’s open. Later opposing confirmation
      closes the swing and the profile.
```

## Hard versus informative

```text
HARD (block): holdout exclusion, causal timestamps, emission completeness,
  deterministic replay, state reconciliation, TPO conservation, future-destroy
  integrity, and zero-cost compliance.
INFORMATIVE: coverage counts, state frequencies, interval widths, and venue
  differences.
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
