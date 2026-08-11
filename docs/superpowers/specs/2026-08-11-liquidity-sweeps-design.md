# Liquidity-sweeps research design

- **Date:** 2026-08-11
- **Checkpoint:** `2026-08-11-019-liquidity-sweeps`
- **Family:** `CF-LIQSWP-001`
- **Status:** operator-approved design; implementation and fresh-context QA pending
- **Source of truth:** `docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/liquidity.md`

## Objective

Measure liquidity-level raids as online stateful events across the full cTrader
compatibility universe and the causal Bybit top-10 universe. The work is
characterisation, not a deployability claim.

## Frozen scope

- Observation timeframes: 15 minutes, 30 minutes, and 1 hour.
- Engine source: 1-minute real OHLCV bars; higher-timeframe state is built
  online. The existing `xen.bar_aggregator` convention is the parity reference.
- Level families: previous completed 1H/4H/1D/1W levels, previous completed
  Asia/Europe/America session levels, and causal rolling 16/32/64/128/256-bar
  levels.
- Confirmation reference: 1H levels for 15m/30m observations and 1D levels for
  1h observations.
- Confirmation methods are tested separately: higher-timeframe breakout-bar
  confirmation and close beyond a configured higher-degree level.
- Distances and profile widths are emitted raw and normalised by causal
  same-asset, same-observation-timeframe Wilder ATR(14).

## Value-gap contract

For a completed sweep, the profile interval runs from the 1-minute bar that
establishes maximum excursion through the completed close of the same-direction
confirmation event. Each closed 1-minute bar contributes one TPO count to every
fixed ATR-scaled price bin intersecting its inclusive low-high range. The value
area is grown from the lowest-price maximum-TPO bin until it contains at least
70% of total TPO count, with upper-bin-first ties.

The value gap is the lowest-density set of bins inside the VA whose cumulative
TPO count reaches at least 30% of VA TPO count. The exact bin mask and its
conservative outer span are retained. A gap is tight exactly when:

```text
gap_span < 0.30 * (VAH - VAL)
```

The comparison is between TPO mass and price span; it is not a price-width
definition of the gap itself. Degenerate profiles and bin-resolution limits
are emitted with explicit reasons and are never silently removed.

## Experiment sequence

1. `EXP-100` — streaming detector, confirmation, and coverage validity.
2. `EXP-101` — level significance versus later swing outcomes.
3. `EXP-102` — repeated raids and prior-raid count.
4. `EXP-103` — value-gap and tight-gap conditioning.
5. `EXP-104` — volatility-regime conditioning.

Every experiment is TRAIN-only, cost-free, per-stratum, and subject to fresh
QA before execution. No TEST or holdout data is loaded.

## Design gate

No Nautilus strategy code is written until the checkpoint designs pass a fresh
clause-by-clause QA review. The value-gap implementation must pass synthetic
TPO conservation, VA construction, tightness-boundary, reset-on-new-maximum,
causality, and deterministic replay tests before any real-data run.
