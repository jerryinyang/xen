# SPDR-013 — Direction expectancy (placeholder)

- **Family:** `CF-VOLDIR-001`
- **Checkpoint:** `2026-07-23-017-structural-vol-direction-programme`
- **Status:** `DESIGN PENDING / DEFAULT BLOCKED ON SPDR-012 GATE`
- **Authority:** do not execute until complete design + operator gate after SPDR-012 (default sequence).

## Bound by

- Checkpoint §5 Step B, §8.2  
- RAW §3 Step B, §5.2  
- Lane: `docs/references/spdr-lane.md`

## Required content of the full design

1. SMA arms: 14 / 25 primary; ≤50; angle filter on/off; **no 200-SMA**.  
2. ZigZag ATR params; line features (magnitude, direction, angle, path-local noise).  
3. AR/light ML head: predict **magnitude and/or volatility of the next whole move**.  
4. Capture geometry: cut losers quickly; let winners run (frozen rules).  
5. Primary scoring: availability-when-right, damage-when-wrong, **expectancy bps** — **not win-rate**.  
6. Partial-cost caveat on any trading bps.  
7. Forbidden: range-break primary direction without new evidence.
