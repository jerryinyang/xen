---
name: signed-volume-provenance
description: Bybit buy/sell volume is verified exact taker-aggressor volume on the signed lane.
metadata: { type: reference, chapter: 4 }
---
INFR-017 reconstructed 20/20 declared symbol-days from raw Bybit trades with bit-exact
Volume, BuyVolume, SellVolume and NTrades and unanimous aggressor-side semantics. Delta is a
real exchange-native taker-flow measurement, not tick-count volume. This validates the data
source; CF-SIGAUC-001's tested transforms still added no tradable marginal value.
