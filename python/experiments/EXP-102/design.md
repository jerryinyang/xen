# EXP-102 — Repeated raids

- **Family:** `CF-LIQSWP-001/HYP-002`
- **Checkpoint:** `2026-08-11-019-liquidity-sweeps`
- **Status:** design complete; fresh QA pending
- **Vehicle:** Nautilus `BacktestNode`, TRAIN only
- **Amendments:** inherits checkpoint AMENDMENT-2 through AMENDMENT-5; no experiment-specific amendment. Counts: **0L / 1T / 3N**.

## Mechanism

```text
MECHANISM: Repeated completed raids of the same persistent liquidity level may
change the distribution of the eventual swing. Each raid is a separate object,
linked to one level and carrying the number of previous completed raids.
DERIVED: estimand=outcomes by exact prior-raid count and predeclared count bands;
null=future-destroyed outcome alignment; horizon=confirmation to opposing event or
censor; test=direct within-level clustered contrasts.
```

## Object identity

```text
OBJECT-IDENTITY:
  measurement object == trading object: YES — every completed raid remains an
    individual level-linked event.
  measured conditioning event == traded entry event: N/A — no deployment rule.
  effect-splitting windows non-overlapping: YES — each raid has one outcome
    record; later raids do not overwrite earlier outcomes.
```

## Scope and estimand

Emit exact `previous_raid_count` and report both the exact count and the fixed
descriptive bands `0`, `1`, and `2+`. The same level may contribute to multiple
rows, so the uncertainty unit is `level_id`, not raid count. Outcomes are
`swing_atr`, `swing_duration`, `strong_move`, and breakout/failure state.

No raid is removed for failing to produce a later strong move. Missing endpoints
are explicit right-censoring.

## Control and tripwire

```text
CONTROL FUTURE_DESTROY:
  question answered: does the prior-raid/outcome relationship use aligned future
    movement rather than repeated event labels alone?
  population: all emitted raid rows, with future outcome blocks deranged within
    asset × timeframe × level configuration.
  bite: changes the outcome columns while preserving exact previous_raid_count.
  non-vacuity: swing_atr and strong_move are changed by the destroy.
  expected outcome if H true: count-band contrasts collapse; if H false: they remain.
  disclosure: fixed-point count and destroy/raw contrast ratio.
  destroy form: DERANGEMENT, zero fixed points.

TRIPWIRE: future-destroyed outcome blocks
  must collapse the repeated-raid contrast;
  vacuity check: the repeated-raid label is preserved while outcomes move;
  derangement=YES;
  integrity_bite: INTEGRITY_Z × bootstrap_SE, INTEGRITY_Z=2.8.
```

## Interpretation and sample size

```text
BANDS (operator-only): higher, overlapping, or lower observed count-band outcomes.
SAMPLE-SIZE:
  expected events per stratum: measured by preflight; no count gate.
  minimum_n_for_primary_inference: none.
  declared_fixed_comparator: prior_raid_count=0 within the same named level/config
    stratum, with the all-count descriptive table retained.
  channels: swing_atr (outcome_level); strong_move (paired_delta).
  strata predeclared thin: every venue × asset × timeframe × level configuration.
```

## Golden trace

```text
GOLDEN-TRACE:
  One high level is raided, returned, and later raided again before the opposing
  confirmation. The first row has previous_raid_count=0; the second has
  previous_raid_count=1. Both rows remain in the emission and share one level_id.
```

## Hard versus informative

```text
HARD (block): raid-link integrity, no collapsed rows, causal outcome timestamps,
  fence/holdout, future-destroy integrity, deterministic replay, and zero-cost.
INFORMATIVE: count-band distributions, durations, magnitudes, breakout rates,
  PSR if a mean-bps series is emitted, and venue comparisons.
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
