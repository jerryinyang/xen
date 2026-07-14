---
name: nautilus-bybit-migration
description: INFR-010 (2026-07-14) — engine NautilusTrader, primary data Bybit USDT-perp OHLCV from trades archives; chapter-04 gate = Phase D VAL
metadata: { type: project, chapter: 4 }
---

Chapter-03 close pivoted the substrate (INFR-010 design v2, operator decisions D1–D8):
NautilusTrader engine (event-driven, deterministic); primary data = 1m OHLCV **derived from
Bybit trades archives**, full USDT linear perp universe **including delisted** (the archive
listing is the anti-survivorship census); MBP/L2 store (BTC/ETH/SOL) contracts-only, collection
deferred. T1/T2 fill-cost tiers with the **spread-scale routing rule** (gross within ~3× RT
spread undecidable on T1). Holdout = **global calendar fence** (one date pair, all symbols,
hash-pinned manifest). Bybit fees+funding replace the FTMO table at Phase C. Phases:
0 chapter close → A dataset (INFR-011) ∥ B engine → C governance rebind (INFR-012) → D e2e
VAL (opens Chapter 04) → E MBP skeleton (INFR-013). No live trading/capture (D7); no vendor
data (D1). cTrader stack + FX/indices data archived at `archive/chapter-03-xena-mtfctx/`
(holdout obligations on that data still binding). [[xena-pc-binder-pin]]
