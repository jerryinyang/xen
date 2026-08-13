# EXP-100 — Liquidity-sweep streaming apparatus

- **Family:** `CF-LIQSWP-001/HYP-000`
- **Checkpoint:** `2026-08-11-019-liquidity-sweeps`
- **Status:** AMENDMENT-13 264-cell TRAIN analysis complete; HYP-000 upheld by operator confirmation (2026-08-13)
- **Vehicle:** Nautilus `BacktestNode`, TRAIN only
- **Amendments:** inherits checkpoint AMENDMENT-2 through AMENDMENT-13. Counts: **2L / 3T / 7N**.
  - **AMENDMENT-8:** raid grain on the observation bar; 1m reserved for TPO / max-excursion / swing / fills.
  - **AMENDMENT-13:** beyond the level starts a live raid; same-bar return does not close it.
  - **AMENDMENT-9:** 1h cells confirm on 1H and 4H (not 1D); run 15m then 30m then 1h.
  - **AMENDMENT-10:** 1D/1W = NY 17:00 trading day / Mon–Fri week, not contiguous minute bars.
  - **AMENDMENT-11:** rolling windows 7/14/22/252; matrix **264**.
    - **AMENDMENT-12:** tightness `gap_span < 0.50 * VA_width`; gap selection stays emptiest 30% of VA TPO.
  - **ONLINE PROFILE:** every closed 1m source bar updates active TPO bins immediately; no full-history source log or deferred rebuild is permitted.
  - **DURATION FIELDS:** emit `excursion_duration_ns` from first excursion through return or censor and `swing_duration_ns` from confirmation through endpoint; retain `duration_ns` as the exact swing-duration alias.

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

Run all three base timeframes, both confirmation methods, **cTrader assets only**
(`EURUSD`, `XAUUSD`, `USTEC`; AMENDMENT-7), and every frozen level
configuration. Confirmation references: 1H for 15m/30m; **1H and 4H** for 1h
(AMENDMENT-9). Matrix size: **264 cells** (AMENDMENT-11). Run order: all 15m, then all 30m,
then all 1h. Verify:

- exact level identity and catalogue membership at each timestamp;
- strict observation-bar excursion starts a live raid; same-bar return is recorded and does not close it (AMENDMENT-13);
- repeated-raid linkage and close-all-eligible settlement (AMENDMENT-6):
  latest expected-side raid stays primary; earlier eligible returned raids close
  as `CONFIRMED_NON_PRIMARY`; all eligible opposing unconfirmed raids fail;
- confirmation and endpoint chronology;
- TPO profile state, conservation, reset, VA, gap, and tightness fields;
- deterministic replay and artifact hash equality;
- bounded online profile state and explicit excursion/swing duration fields.

Source bars must be minute-aligned and strictly increasing. Normal market-closure gaps in
the cTrader replication are accepted as periods with no observed bars: no flat/synthetic
bars are inserted, no TPO counts accrue during closure, and an incomplete aggregation
window is reset at the next observed bar. Duplicate or backward timestamps are rejected.

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
  strata predeclared thin: every cTrader asset × timeframe × configuration cell (AMENDMENT-7).
```

## Golden trace

```text
GOLDEN-TRACE:
  T1: high level 100.00; a completed observation bar high=101.20; a later
      observation bar low=100.00. The first bar already started a live raid
      (max excursion 1.20, prior raid count 0); the later return is recorded
      on that live object. A same-bar return would also leave it live
      (AMENDMENT-13). A 1m wick that is not the observation high does not
      start a raid (AMENDMENT-8).
  T2: a second active high level is raided on a later observation bar before
      confirmation. The later resolvable raid receives primary attribution and
      stays live; the earlier eligible returned raid settles as
      CONFIRMED_NON_PRIMARY on the same expected-side reference event
      (AMENDMENT-6).
  T3: the 1H expected-side bar closes; sweep confirmation is timestamped at that
      completed close, not at a 15m or 1m stamp. Later opposing confirmation
      closes the swing and the 1m TPO profile.
```

## Hard versus informative

```text
HARD (block): holdout exclusion, causal timestamps, emission completeness,
  deterministic replay, state reconciliation, TPO conservation, future-destroy
  integrity, and zero-cost compliance.
INFORMATIVE: coverage counts, state frequencies, interval widths, and asset
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
