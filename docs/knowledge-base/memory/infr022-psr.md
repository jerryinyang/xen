---
name: infr022-psr
description: INFR-022 PSR pairing: psr + psr_n beside every mean-trade/leg bps read, same series
metadata: { type: lesson, chapter: 6 }
---
Operator directive INFR-022 (2026-08-08), lesson L-64: Probabilistic Sharpe Ratio (Bailey &
Lopez de Prado 2012, skew/kurt-adjusted, empirical moments, per-trade series) is reported beside
every mean trade/leg bps read on the SAME series and population: `psr` + `psr_n` (NaN + n when
n < 2; row still reported, N3). PSR is evidence, never a gate.
