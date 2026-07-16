#!/usr/bin/env python3
"""
INFR-011 Step 3 (amended) — in-stream: day file bytes → 1m OHLCV + pseudo-quote spreads + invariants.

Invariants (blocking):
- volume ≡ Σ trades
- monotonic ts
- OHLC bounds
- gap ledger

4y cap + streaming: this runs on the decompressed stream; no raw landing except keep-forever trio.
"""
print("derive+invariants (streaming) stub — integrate with downloader; 4y cap enforced upstream.")