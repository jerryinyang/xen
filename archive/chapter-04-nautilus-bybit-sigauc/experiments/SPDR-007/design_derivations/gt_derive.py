"""Designer-side golden-trace derivation for SPDR-007 (not developer code).

Derives 2 hand-checkable S1-confirmed-break events under the INFR-018 frozen pin
(anchor A-USOPEN, L=15, A6 = D4-t50-w30, poke delta = 0) so QA can diff the
implementation against them.
"""

from __future__ import annotations

import sys
from datetime import datetime

import polars as pl

sys.path.insert(0, "python/src")

from xen.sigbar import fences, sessions  # noqa: E402
from xen.sigbar.acceptance import QUALIFY_MINUTES, find_pokes  # noqa: E402

L = 15
SPEC = [s for s in sessions.CANDIDATE_ANCHORS if s.anchor_id == "A-USOPEN"][0]


def one(symbol: str, day: str) -> None:
    bars = fences.load_bars(symbol, "DESIGN")
    lo, hi = bars["OpenTime"].min(), bars["OpenTime"].max()
    anchors = sessions.anchor_table(SPEC, lo, hi)
    sess = sessions.session_breaks(bars, anchors, L)
    joined = sessions.attach_sessions(bars, anchors, L)
    pokes = find_pokes(joined, sess, 0.0)

    target = datetime.fromisoformat(day)
    row = pokes.filter(
        (pl.col("anchor_ts") >= target) & (pl.col("anchor_ts") < target.replace(hour=23, minute=59))
    )
    if row.height == 0:
        print(f"{symbol} {day}: no poke")
        return
    r = row.row(0, named=True)

    qend = r["qualify_end"]
    sess_end = r["session_end"]
    side = r["poke_side"]
    ibw = r["ib_width"]

    # D4-t50-w30: fraction of bars in [poke_ts, poke_ts+30) closing beyond the edge >= 0.5
    edge = r["ib_high"] if side == 1 else r["ib_low"]
    qual = joined.filter(
        (pl.col("OpenTime") >= r["poke_ts"]) & (pl.col("OpenTime") < qend)
    )
    beyond = (qual["Close"] > edge) if side == 1 else (qual["Close"] < edge)
    frac = float(beyond.sum()) / qual.height

    entry_bar = joined.filter(pl.col("OpenTime") == qend)
    if entry_bar.height == 0:
        print(f"{symbol} {day}: no entry bar at {qend}")
        return
    entry = float(entry_bar["Open"][0])

    post = joined.filter((pl.col("OpenTime") > qend) & (pl.col("OpenTime") < sess_end))
    hi_p, lo_p = float(post["High"].max()), float(post["Low"].min())
    if side == 1:
        mfe, mae = hi_p - entry, entry - lo_p
    else:
        mfe, mae = entry - lo_p, hi_p - entry

    mid = (r["ib_high"] + r["ib_low"]) / 2.0
    print(f"--- {symbol} session {r['anchor_ts']} (side {'UP' if side==1 else 'DOWN'})")
    print(f"  IB [{r['anchor_ts']}, +{L}m)  high {r['ib_high']}  low {r['ib_low']}  width {ibw}")
    print(f"  ib_width_bps = 1e4*{ibw}/{mid} = {1e4*ibw/mid:.4f}")
    print(f"  poke_ts {r['poke_ts']}  extreme {r['poke_extreme']}")
    print(f"  qualify [{r['poke_ts']}, {qend})  n_bars {qual.height}  beyond_frac {frac:.4f}"
          f"  -> D4-t50 {'ACCEPT' if frac >= 0.5 else 'REJECT'}")
    print(f"  entry bar OpenTime {qend}  entry Open {entry}")
    print(f"  session_end {sess_end}  n_post {post.height}")
    print(f"  MFE {mfe:.6g} = {mfe/ibw:.4f} IBw   MAE {mae:.6g} = {mae/ibw:.4f} IBw")
    print(f"  asym = {mfe/ibw - mae/ibw:.4f}")


if __name__ == "__main__":
    one("BTCUSDT", "2023-01-11")
    one("SOLUSDT", "2023-01-11")
    one("ETHUSDT", "2022-11-09")
