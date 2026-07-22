---
name: spreadbps-unusable
description: Staging SpreadBps is a mean-print differential, not executable spread.
metadata: { type: lesson, chapter: 4 }
---
INFR-017 found `SpreadBps` negative in roughly 32–40% of BTC/ETH TRAIN minutes because it
subtracts mean prices of different aggressor-side trades across the minute. It is pinned
`UNUSABLE`; never floor, rename or cost from it. Current cost-floor proxies are conservative upper
bounds, not quotes, validated on only 20 symbol-days; exact net claims otherwise require a
separately validated reconstruction.
