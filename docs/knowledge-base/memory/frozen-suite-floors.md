---
name: frozen-suite-floors
description: Frozen per-domain MDE floors for the three referee components; never retune after seeing a candidate
metadata: { type: reference, chapter: 01 }
---

Frozen detection floors (bps), 5m / 1h / 4h:
- Strict 5-check gate stack (EXP-003/005): 1 / 4 / 12
- Ratified-loose referee (EXP-011/012): 0.5 / 2 / 8
- Revised portfolio-fitness unit (EXP-018): 12 / 16 / 32

L5 materiality is the binding, α-invariant leg. Per-instrument MDEs can be lower than pooled
(EXP-008). Do not retune thresholds/losses/costs/denominators/pass-logic after seeing a
candidate outcome. Detail: [[../evaluation-framework]].
