---
name: joint-sits-at-breakeven-cost-not-rate
description: The powered joint (p, W, L) sits at net break-even on both universes and 91-96% of the gap is cost, not rate.
metadata: { type: project, chapter: 5 }
---
`0 of 1,413` powered crypto cells and `0 of 315` powered cTrader cells clear net break-even.
Crypto: `p` 0.3887 vs `p_be_net` 0.4992 (`edge` −0.0728), gross mean −1.18 bps, 32.5% clear
*gross*. cTrader: `p` 0.4868 vs `p_be` 0.4855 (gap +0.0013), gross mean −0.080 bps = **0.006σ**.
The identity `E[net] = p·W − (1−p)·L − cost` reconciles to 1.46e-11 bps. **91% (crypto) to 96%
(cTrader) of the distance to break-even is COST, not rate.**

Two consequences. First, there is no rate improvement worth finding on this substrate, because
the deficit is not a rate deficit. Second, **no successor here is evaluable at all while spread
remains uncharged** — the cost precondition binds before any modelling question does. The
structure replicated *more tightly* on the second universe, which is why this is treated as
structural rather than a sampling result.

See [[wl-is-the-mirror-of-p]] and [[spreadbps-unusable]].
