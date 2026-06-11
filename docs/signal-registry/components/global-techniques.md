# Global Technique Notes

This file records reusable components that may become future registered
candidate branches. Nothing in this file is eligible for measurement until it is
promoted into `multiplicity-registry.md` with a candidate or component ID.

## Trigger Components (can be for exits or entries)

### Heiken Ashi Exhaustion Patterns

These are possible exit overlays. If used, signal decisions may inspect Heiken
Ashi features, but P&L and return evaluation must use real time-bar prices.

#### Pattern 1: Harami Size Pattern

- Latest HA bar: `bar_0`.
- Previous HA bar: `bar_1`.
- Signal condition:
  `max(close_1, open_1) > max(close_0, open_0)` and
  `min(close_1, open_1) < min(close_0, open_0)`.
- Deferred variants:
  - signal direction follows `bar_0`;
  - signal direction independent of bar color.

#### Pattern 2: Trailing Exit Price

- Short-exit reference: HA high or `max(HAOpen, HAClose)`.
- Long-exit reference: HA low or `min(HAOpen, HAClose)`.
- Deferred execution variants:
  - stop-style trigger;
  - bar-close market-style trigger.

### Last-X High/Low

- Long-exit reference: lowest low over the last X traditional candles.
- Short-exit reference: highest high over the last X traditional candles.
- `X` is not registered. Any value or sweep must be predeclared before use.




## Position Management Components

### Pyramiding

- Adds entries in the same direction as an existing position.
- Required parameter: maximum open positions.
- Not registered for Phase 004 Batch 004-A.





## Risk Management Components

No risk-management component is currently registered.

## Notes

These notes are intentionally non-operative. Treat them as backlog material, not
as experiment authorization.
