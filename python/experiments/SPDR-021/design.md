# SPDR-021 — Volatility-adaptive management on a fixed breakout benchmark

- **Family / registration:** `CF-VOLDIR-001/HYP-D8`
- **Checkpoint:** `2026-07-25-018-trade-opportunity-capture-geometry`
- **Status:** `DESIGN APPROVED 2026-07-30 — IMPLEMENTATION AND EXECUTION NOT YET AUTHORISED`
- **Vehicle:** NautilusTrader; SPDR TRAIN-only characterisation
- **Programme contract:** checkpoint
  `adaptive-management-design.md` is binding in full

```text
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: reported cost understates total cost; reported net performance is overstated
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

## Question and mechanism

How does each confirmed volatility component change the breakout's native threshold/expiry and each
applicable external management device relative to their fixed forms?

```text
MECHANISM:
  The candlestick pattern supplies direction. Confirmed volatility objects supply only expected
  move scale, slow state, short shock state, next-swing opportunity and tail risk. Applying those
  objects in both directions to the breakout threshold and pending lifetime changes which orders
  exist; applying them to target, stop, trail, hold or risk normalisation changes post-entry
  management. No volatility object is treated as a direction forecast.

DERIVED:
  estimand = common-origin adaptive-minus-fixed change for threshold/expiry; paired
             adaptive-minus-fixed-device change for post-entry management
  null     = same signal origins under fixed threshold/expiry; same filled episodes under the fixed
             device; time-deranged and magnitude-matched controls
  horizon  = native one-minute execution within H1 caps {1,2,4,12,24}
  test     = direct estimate + dependence-matched CI; descriptive map, no binary verdict
```

```text
OBJECT-IDENTITY:
  measurement object == trading object: YES — every eligible breakout origin is retained for
    native-parameter reads, and Nautilus fills/closes the orders supplying trade/device measures
  measured conditioning event == traded entry event: YES — the completed-bar pattern plus the
    declared fixed/direct/reverse threshold creates the stop order; all state is frozen beforehand
  effect-splitting windows non-overlapping: YES — one live order or position per instrument
```

## Entry and baseline

The fixed comparator uses `0.50 × ATR(20)`, two-bar pending expiry and one-bar active hold. The
programme contract adds separate direct and reverse threshold arms, direct and reverse expiry arms,
and the four threshold+expiry orientation pairs for every volatility component. Values are frozen;
none is selected from outcomes. The plain management baseline is unit size with no target, stop or
trail.

## Arms and outputs

Run native parameters first: threshold alone, expiry alone, then the bounded threshold+expiry
combination. Run the external management matrix separately; do not cross it with native arms.
`E-TOUCH/E-CLOSE` do not apply. Report every eligible origin, signal count, selected/excluded paths,
order-fill rate and time-to-fill in addition to the common device-native measures.

```text
POWER:
  event count, effective count, paired CI and block MDE are emitted for every row
  no row is removed or labelled positive/negative because of power

HARD:
  TRAIN/holdout fence; t-1 provenance; Nautilus order/fill reconciliation; deterministic rerun;
  future-shift tripwire; zero-fixed-point derangement

INFORMATIVE:
  every effect, CI, MDE, state contrast, magnitude-matched comparison and partial-cost view
```

## Golden traces

Synthetic UTC fixtures, hand-derived from this design:

1. `2023-01-01T02:00Z`: `ATR20=2`, prior-bar low `97 < min(99,98)`, closes `101−99`;
   impulse is exactly `1.0 ATR`, with continuous scale ratio `q=2`. Direct threshold is `0.25`,
   fixed is `0.50`, reverse is `1.00`: direct/fixed create the long stop, reverse does not because
   the rule is strict `>`. Buy stop `102` fills at `02:07Z` when the minute high reaches `102.2`.
2. `2023-01-02T02:00Z`: prior-bar high `103 > max(101,102)`, closes `98−100`; short signal passes
   in categorical `HIGH`. Sell stop `97` is reached only during the second H1 bar: `LONG_ON_HIGH`
   expiry 4 fills, fixed expiry 2 fills, `SHORT_ON_HIGH` expiry 1 expires unfilled.
3. Long fill `100`, target `102`, stop `98`: `10:01Z` high/low `101/99`, `10:02Z`
   `102.2/99.5`. Target exits at `10:02Z`; a later fall through `98` cannot rewrite the exit.

## Claim boundary

This experiment characterises the breakout substrate only. It does not gate `SPDR-022` or
`SPDR-023`, issue a family verdict, or authorise XENA.
