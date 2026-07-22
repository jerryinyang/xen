---
name: spreadbps-unusable
description: Staging SpreadBps is a mean-print differential, not executable spread.
metadata: { type: lesson, chapter: 4 }
---
INFR-017 found `SpreadBps` negative in roughly 32–40% of BTC/ETH TRAIN minutes because it
subtracts mean prices of different aggressor-side trades across the minute. It is pinned
`UNUSABLE`; never floor, rename or cost from it. Chapter 05 uses no replacement proxy. Spread cost
is unavailable and not charged, so reported cost understates total cost and fully-net claims are
prohibited.
