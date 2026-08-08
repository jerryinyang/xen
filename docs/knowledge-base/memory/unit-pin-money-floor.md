---
name: unit-pin-money-floor
description: L-21 — pin the normalisation unit at every screen→graduation seam
metadata: { type: lesson, chapter: 2 }
---
A dimensionless screen effect becomes a money claim only through an explicit, **re-computed**
unit derivation (which ATR, which timeframe, which lag) at graduation. Never assert the unit
across a seam.

EXP-025 is the canonical failure: SPDR screen normalised by 5min ATR while the graduation
design asserted 1h ATR — a 4.1× inflation of the target. Binding: `docs/references/spdr-lane.md`
(L-21). See [[spdr-speed-run-lane]].

Under the live zero-cost model (L-62 / [[infr022-zero-cost]]), there is **no** money-unit or
cost-stack floor on the value path; unit honesty is independent of cost.
