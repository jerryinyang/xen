"""Recompute the true SPDR-007 event population (I-1 fix).

Population = every A6-ACCEPTED poke under the frozen rule D4-t50-w30, delta=0,
i.e. `says_accept == True` — NOT n_yes (resolved-and-accept). Computed on the
frozen top-20 online panel over each band, per symbol.
"""

from __future__ import annotations

import sys

import polars as pl

sys.path.insert(0, "python/src")

from xen.sigbar import fences, sessions  # noqa: E402
from xen.sigbar.acceptance import Discriminator, evaluate_discriminator, find_pokes  # noqa: E402

L = 15
SPEC = [s for s in sessions.CANDIDATE_ANCHORS if s.anchor_id == "A-USOPEN"][0]
DISC = Discriminator("D4-t50-w30", "D4", False, {"tau": 0.50, "w": 30})


def panel_symbols(band: str) -> list[str]:
    import json
    reg = json.load(open("python/experiments/INFR-018/results/instrument_registry.json"))
    # Membership parquet lists realised daily panel; take the distinct symbol set.
    path = f"python/experiments/INFR-018/results/universe_membership_{band}.parquet"
    m = pl.read_parquet(path)
    col = "symbol" if "symbol" in m.columns else m.columns[-1]
    return sorted(m[col].unique().to_list())


def one(symbol: str, band: str):
    bars = fences.load_bars(symbol, band)
    if bars.height == 0:
        return None
    lo, hi = bars["OpenTime"].min(), bars["OpenTime"].max()
    anchors = sessions.anchor_table(SPEC, lo, hi)
    sess = sessions.session_breaks(bars, anchors, L)
    joined = sessions.attach_sessions(bars, anchors, L)
    pokes = find_pokes(joined, sess, 0.0)
    if pokes.height == 0:
        return (0, 0)
    ev = evaluate_discriminator(joined, pokes, DISC)
    n_pokes = pokes.height
    n_accept = int(ev["says_accept"].sum())
    return (n_pokes, n_accept)


for band in ("DESIGN", "CONFIRM"):
    syms = panel_symbols(band)
    rows = []
    for s in syms:
        r = one(s, band)
        if r is None:
            continue
        rows.append((s, r[0], r[1]))
    df = pl.DataFrame(rows, schema=["symbol", "pokes", "accepts"], orient="row")
    tot_p = int(df["pokes"].sum())
    tot_a = int(df["accepts"].sum())
    acc = df.filter(pl.col("accepts") > 0)["accepts"]
    print(f"=== {band}: {df.height} panel symbols with bars")
    print(f"    total pokes {tot_p}   total ACCEPTS (says_accept) {tot_a}")
    print(f"    per-symbol accepts: median {acc.median():.1f}  q25 {acc.quantile(0.25):.0f}"
          f"  q75 {acc.quantile(0.75):.0f}  min {acc.min()}  max {acc.max()}")
    print(f"    symbols with <40 accepts: {df.filter(pl.col('accepts')<40).height}"
          f" / {df.height}   with <10: {df.filter(pl.col('accepts')<10).height}")
    df.write_parquet(f"/tmp/pop_{band}.parquet")
