"""Designer-side: (a) DIVISOR pin — median IB-width in bps per symbol (DESIGN bank);
(b) locate a DOWN-side ACCEPT event for golden trace GT-2.

Measures the NORMALISER only, never the effect. The MFE quantile is the screen's
own read and is deliberately not computed here.
"""

from __future__ import annotations

import sys

import polars as pl

sys.path.insert(0, "python/src")

from xen.sigbar import fences, sessions  # noqa: E402
from xen.sigbar.acceptance import find_pokes  # noqa: E402

L = 15
SPEC = [s for s in sessions.CANDIDATE_ANCHORS if s.anchor_id == "A-USOPEN"][0]
SYMS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT"]


def build(symbol: str):
    bars = fences.load_bars(symbol, "DESIGN")
    lo, hi = bars["OpenTime"].min(), bars["OpenTime"].max()
    anchors = sessions.anchor_table(SPEC, lo, hi)
    sess = sessions.session_breaks(bars, anchors, L)
    joined = sessions.attach_sessions(bars, anchors, L)
    return bars, joined, sess


for sym in SYMS:
    bars, joined, sess = build(sym)
    s = sess.filter(pl.col("ib_width") > 0).with_columns(
        (1e4 * pl.col("ib_width") / ((pl.col("ib_high") + pl.col("ib_low")) / 2)).alias("ibw_bps")
    )
    q = s["ibw_bps"]
    print(f"{sym:9s} n_sessions {s.height:4d}  IBwidth_bps median {q.median():8.3f}"
          f"  q25 {q.quantile(0.25):7.3f}  q75 {q.quantile(0.75):8.3f}")

# --- GT-2: first DOWN-side ACCEPT under D4-t50-w30 on SOLUSDT
print("\nsearching DOWN-side ACCEPT (SOLUSDT):")
bars, joined, sess = build("SOLUSDT")
pokes = find_pokes(joined, sess, 0.0).filter(pl.col("poke_side") == -1).sort("poke_ts")
found = 0
for r in pokes.iter_rows(named=True):
    qual = joined.filter(
        (pl.col("OpenTime") >= r["poke_ts"]) & (pl.col("OpenTime") < r["qualify_end"])
    )
    if qual.height == 0:
        continue
    frac = float((qual["Close"] < r["ib_low"]).sum()) / qual.height
    if frac < 0.5:
        continue
    eb = joined.filter(pl.col("OpenTime") == r["qualify_end"])
    if eb.height == 0:
        continue
    entry = float(eb["Open"][0])
    post = joined.filter(
        (pl.col("OpenTime") > r["qualify_end"]) & (pl.col("OpenTime") < r["session_end"])
    )
    ibw = r["ib_width"]
    mfe = entry - float(post["Low"].min())
    mae = float(post["High"].max()) - entry
    mid = (r["ib_high"] + r["ib_low"]) / 2
    print(f"  session {r['anchor_ts']}  IB[{r['ib_low']}, {r['ib_high']}] w={ibw:.6g}"
          f" ({1e4*ibw/mid:.3f} bps)")
    print(f"    poke_ts {r['poke_ts']} extreme {r['poke_extreme']}  beyond_frac {frac:.4f} ACCEPT")
    print(f"    entry {r['qualify_end']} open {entry}  session_end {r['session_end']}"
          f"  n_post {post.height}")
    print(f"    MFE {mfe:.6g} = {mfe/ibw:.4f} IBw  MAE {mae:.6g} = {mae/ibw:.4f} IBw"
          f"  asym {mfe/ibw - mae/ibw:.4f}")
    found += 1
    if found >= 2:
        break
