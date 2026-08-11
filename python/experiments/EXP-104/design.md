# EXP-104 — Volatility-regime conditioning

- **Family:** `CF-LIQSWP-001/HYP-004`
- **Checkpoint:** `2026-08-11-019-liquidity-sweeps`
- **Status:** design complete; fresh QA pending
- **Vehicle:** Nautilus `BacktestNode`, TRAIN only
- **Amendments:** inherits checkpoint AMENDMENT-2 through AMENDMENT-5; no experiment-specific amendment. Counts: **0L / 1T / 3N**.

## Mechanism

```text
MECHANISM: Causal volatility state may change the frequency, size, duration, and
quality of liquidity raids and their later swings. The regime is measured from
completed same-asset observation-timeframe bars before the event.
DERIVED: estimand=raid and outcome distributions by causal volatility regime;
null=future-destroyed outcome alignment; horizon=raid through opposing confirmation
or censor; test=direct LOW/MID/HIGH descriptive contrasts.
```

## Object identity

```text
OBJECT-IDENTITY:
  measurement object == trading object: YES — volatility labels attach to the
    same emitted level/raid/swing objects.
  measured conditioning event == traded entry event: N/A — no deployment strategy.
  effect-splitting windows non-overlapping: YES — regime labels are sampled at
    raid, excursion, confirmation, and endpoint timestamps without rewriting the
    underlying outcome interval.
```

## Frozen regime

Use causal Wilder ATR(14)/close on each asset and observation timeframe. Rank the
current completed-bar value against the trailing 252 completed values for the
same asset and timeframe; labels are LOW below the 33rd percentile, MID from the
33rd through the 67th percentile, and HIGH above the 67th percentile. Warmup and
missing history are explicit states. Regime labels at raid, excursion,
confirmation, and endpoint are all emitted.

## Scope and estimand

Report raid frequency, excursion magnitude/duration, later swing magnitude/
duration, strong-move frequency, breakout/failure frequency, and profile/tight-gap
frequency by regime. All assets, venues, base timeframes, level configurations,
and confirmation methods remain separate.

## Control and tripwire

```text
CONTROL FUTURE_DESTROY:
  question answered: do regime-conditioned outcome differences require aligned
    future movement rather than the regime label and event calendar alone?
  population: same raid objects with post-confirmation outcome blocks deranged
    within asset × timeframe × configuration.
  bite: changes swing and strong-move outcomes while preserving causal regime labels.
  non-vacuity: outcome-level ATR magnitudes and durations change.
  expected outcome if H true: regime outcome contrasts collapse; if H false: they remain.
  disclosure: fixed-point count and destroy/raw contrast ratio.
  destroy form: DERANGEMENT, zero fixed points.

TRIPWIRE: future-destroyed outcome blocks
  must collapse regime/outcome contrasts;
  vacuity check: regime labels remain fixed while outcomes move;
  derangement=YES;
  integrity_bite: INTEGRITY_Z × bootstrap_SE, INTEGRITY_Z=2.8.
```

Uncertainty is clustered by level ID within every named venue/asset/timeframe/
configuration cell.

## Interpretation and sample size

```text
BANDS (operator-only): higher, overlapping, or lower regime distributions.
SAMPLE-SIZE:
  expected events per stratum: measured by preflight; no count gate.
  minimum_n_for_primary_inference: none.
  declared_fixed_comparator: MID regime within the same named stratum, with the
    all-regime descriptive distribution retained.
  channels: swing_atr (outcome_level); regime frequency (count).
  strata predeclared thin: all venue × asset × timeframe × level × method cells,
    including warmup/missing-regime reasons.
```

## Golden trace

```text
GOLDEN-TRACE:
  At a raid timestamp, ATR/close is below the trailing 33rd percentile and the
  emitted regime_at_raid is LOW. A later ATR increase may change the regime at
  confirmation, but it cannot rewrite the earlier raid label.
```

## Hard versus informative

```text
HARD (block): causal ATR provenance, regime-label timing, fence/holdout,
  outcome reconciliation, future-destroy integrity, deterministic replay, and
  zero-cost compliance.
INFORMATIVE: frequency, magnitude, duration, strong-move, breakout, profile, PSR
  where applicable, and cross-venue comparisons.
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
