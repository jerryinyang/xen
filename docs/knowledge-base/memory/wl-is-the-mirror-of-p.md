---
name: wl-is-the-mirror-of-p
description: On this substrate the payoff ratio W/L is ~97% the arithmetic mirror of the hit rate p, so exit geometry cannot move the mean.
metadata: { type: project, chapter: 5 }
---
Measured at power on two independent universes (25 Bybit USDT-perps, 3 cTrader instruments
sharing no venue, cost model or vendor): `W/L` regresses on `p` with R² **0.9667** (crypto) and
**0.9746** (cTrader), slope 0.9656. Exit geometry moves `W/L` by **36–67×** while `p` moves
inversely by very nearly the compensating amount, leaving the mean where it was; 82.8% (crypto)
and 93% (cTrader) of cells are statistically indistinguishable from the driftless mirror.

Consequence: the capture branch's two-dimensional search space is approximately
one-dimensional. **Do not open a family whose thesis is that a better exit, hold, trail or size
rule converts a break-even joint into a positive one** — that class is refuted at power
(`P-02` generalised). See [[joint-sits-at-breakeven-cost-not-rate]] and
[[chapter05-dispositions]].
