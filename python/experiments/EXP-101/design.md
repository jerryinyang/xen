# EXP-101 — Level significance and later swing outcomes

- **Family:** `CF-LIQSWP-001/HYP-001`
- **Checkpoint:** `2026-08-11-019-liquidity-sweeps`
- **Status:** design complete; fresh QA pending
- **Vehicle:** Nautilus `BacktestNode`, TRAIN only
- **Amendments:** inherits checkpoint AMENDMENT-2 through AMENDMENT-5; no experiment-specific amendment. Counts: **0L / 1T / 3N**.

## Mechanism

```text
MECHANISM: If level degree carries significance, raids of higher-degree or
longer-window levels should have different later-swing distributions than raids
of lower-degree levels, after the same causal raid definition. The unit is the
level-attributed raid and its later confirmed swing.
DERIVED: estimand=per-stratum ATR-normalised swing distributions and direct
degree contrasts; null=future-destroyed outcome alignment; horizon=confirmation
to first opposing event or censor; test=ordered and pairwise descriptive contrasts.
```

## Object identity

```text
OBJECT-IDENTITY:
  measurement object == trading object: YES — the same level-attributed raid
    object supplies the outcome; no synthetic entry is substituted.
  measured conditioning event == traded entry event: N/A — this is an event study,
    not a deployable strategy.
  effect-splitting windows non-overlapping: YES — each raid’s outcome interval is
    closed once its opposing event arrives; repeated level dependence is clustered.
```

## Scope and estimand

Report every asset, venue, base timeframe, confirmation method/reference, side,
level family, and configuration separately. Significance is represented by:

- family A: 1H < 4H < 1D < 1W;
- family B: Asia, Europe, America as separate session strata;
- family C: 16 < 32 < 64 < 128 < 256 bars.

Primary outcomes are `swing_atr`, `swing_duration`, and
`strong_move = swing_atr > max_excursion_atr`. Raw price and bps are audit
columns; ATR units are the comparison scale.

## Control and tripwire

```text
CONTROL FUTURE_DESTROY:
  question answered: is the significance/outcome contrast tied to the real future
    path rather than event counts or level labels alone?
  population: same raid objects with post-confirmation outcome blocks deranged
    within asset × timeframe × configuration.
  bite: changes swing_atr, duration, and strong_move without changing level strata.
  non-vacuity: the primary continuous outcomes are directly altered.
  expected outcome if H true: degree contrasts collapse toward the same-stratum
    destroyed baseline; if H false: they remain similar.
  disclosure: fixed-point count and destroy/raw contrast ratio.
  destroy form: DERANGEMENT, zero fixed points.

TRIPWIRE: future-destroyed post-confirmation blocks
  must collapse the level/outcome relationship;
  vacuity check: the destroyed fields are the outcome estimands;
  derangement=YES;
  integrity_bite: INTEGRITY_Z × bootstrap_SE, INTEGRITY_Z=2.8.
```

Uncertainty is clustered by `level_id` within the full named stratum. No pooled
venue verdict is produced.

## Interpretation and sample size

```text
BANDS (operator-only): higher, overlapping, or lower observed distributions;
  no band is machine-assigned and no row is dropped for count.
SAMPLE-SIZE:
  expected events per stratum: measured by preflight; planning context only.
  minimum_n_for_primary_inference: none.
  declared_fixed_comparator: all raids in the same family/configuration stratum.
  channels: swing_atr (outcome_level); strong_move (paired_delta).
  strata predeclared thin: all venue × asset × timeframe × method × level cells.
```

## Golden trace

```text
GOLDEN-TRACE:
  A 1H level and a C-16 level are both raided and later confirmed. Their records
  remain separate even when prices coincide. The A level and C-16 level receive
  separate significance labels and separate outcome rows.
```

## Hard versus informative

```text
HARD (block): fence/causality, object identity, outcome reconciliation,
  future-destroy integrity, deterministic replay, and zero-cost compliance.
INFORMATIVE: all degree contrasts, ATR distributions, durations, strong-move
  frequencies, PSR where any mean-bps series is emitted, and cross-venue checks.
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
