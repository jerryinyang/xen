---
name: look-ahead-rct-pattern
description: The rct[di] favourable-index look-ahead that shipped a false DEPLOYABLE_CONFIRMED; banned
metadata: { type: lesson, chapter: 01 }
---

EXIT-RCT rested `rct_target[di]` (target from bar `di`'s own close) as the intrabar limit
*during* bar `di`; live-actable is `rct_target[di-1]`. Inflated edge ~+0.25 ATR/trade; CF-MR-001
TRADABLE/DEPLOYABLE retracted. Invisible to numeric re-derivation (audit re-ran the same
contaminated module). Banned pattern. Structural fix: cTrader-primary execution + causal-provenance
audit pass + leak tripwires. Full mechanism + fix in [[../lessons-and-amendments]] L-01.
