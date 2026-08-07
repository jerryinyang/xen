# SPDR-022 — Volatility-adaptive management after MOMO breach entries

- **Family / registration:** `CF-VOLDIR-001/HYP-D9`
- **Checkpoint:** `2026-07-25-018-trade-opportunity-capture-geometry`
- **Status:** `FIRST PASS INVALIDATED — AMENDED RERUN AUTHORISED 2026-08-03; ANALYSIS PENDING`
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

How does each confirmed volatility component change the MOMO breach model's native `z/H` geometry
and each applicable external management device relative to their fixed forms?

```text
MECHANISM:
  E-TOUCH or E-CLOSE supplies a causal breach side and MOMO enters with that side at the next real
  open. Confirmed volatility objects alter z and H in both directions, changing which breach events
  exist, or alter post-entry distance, duration, selection or risk normalisation. No volatility
  object supplies direction.

DERIVED:
  estimand = common-origin adaptive-minus-fixed change for z/H; paired
             adaptive-minus-fixed-device change per post-entry management row
  null     = same zone origins under fixed z/H; same MOMO episodes under the fixed device;
             time-deranged and magnitude-matched controls
  horizon  = native one-minute execution within H1 caps {2,4,12,24}
  test     = direct estimate + dependence-matched CI; descriptive map, no binary verdict
```

```text
OBJECT-IDENTITY:
  measurement object == trading object: YES — every eligible zone origin is retained for native
    geometry reads, and Nautilus fills/closes the breach episodes supplying trade/device measures
  measured conditioning event == traded entry event: YES — first E-TOUCH/E-CLOSE under the
    declared fixed/direct/reverse z/H rule, entry at the next real open with the breach side
  effect-splitting windows non-overlapping: YES — one open episode per instrument and entry variant
```

## Entry and baseline

The fixed comparator uses the SPDR-014 Z-VOL band at H1, EWMA Parkinson width, `z=1.5`, `H=12`.
The programme contract adds separate direct and reverse z arms, direct and reverse H arms, and all
four z+H orientation pairs for every volatility component. `E-TOUCH` and `E-CLOSE` remain separate.
The baseline enters with the breach side, uses unit size, has no target, stop or trail, and exits
after four H1 bars.

The 2026-08-03 common amendment in `adaptive-management-design.md` is binding: actual fills use
engine `_entry_ns`; common fills require both sides to fill; SIZE closes after the fixed four-H1-bar
strategy hold; and eligible, filled, closed, common-filled and common-closed populations are
reported separately. This experiment's native keys remain `z` and `H`, with `E-TOUCH` and
`E-CLOSE` separate. No grid element changes.

Band-event rate, decided-side rate and selectivity are emitted for every arm. Neither event variant
may become the other's fallback.

## Arms and outputs

Run native geometry first: z alone, H alone, then the bounded z+H combination. Run the external
management matrix separately; do not cross it with native arms. Pending-order expiry does not
apply. Report every zone origin, event/no-event and selected/excluded paths, plus all common
device-native measures separately for `E-TOUCH` and `E-CLOSE`.

```text
POWER:
  event count, effective count, paired CI and block MDE are emitted for every row
  no row is removed or labelled positive/negative because of power

HARD:
  TRAIN/holdout fence; t-1 provenance; event/entry parity with SPDR-014; Nautilus fill and exit
  reconciliation; deterministic rerun; future-shift tripwire; zero-fixed-point derangement

INFORMATIVE:
  every effect, CI, MDE, state contrast, magnitude-matched comparison and partial-cost view
```

## Golden traces

Synthetic UTC fixtures, hand-derived from this design:

1. Centre `100`, unit width `1`, categorical `HIGH`: direct `z=1.0`, fixed `z=1.5`, reverse
   `z=2.0`. H1 high reaches `101.6` at `2023-01-03T02:00Z`; direct/fixed E-TOUCH, reverse no event.
   MOMO enters long at the next real open `101.4`.
2. Centre `100`, lower `98.5`: the first outside close `98.4` occurs on origin bar 16.
   `LONG_ON_HIGH H=24` produces a down E-CLOSE and next-open short entry `98.3`; fixed `H=12` and
   `SHORT_ON_HIGH H=4` expire without an event.
3. Long fill `100`, target `102`, stop `98`: minute path `101/99` then `102.2/99.5`.
   Nautilus exits at the target before any later stop touch.

## Claim boundary

This experiment describes MOMO only. It does not gate either companion experiment, choose between
E-TOUCH and E-CLOSE, issue a family verdict, or authorise XENA.
