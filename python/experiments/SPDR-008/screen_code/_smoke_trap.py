"""Smoke test: xen.sigbar.trap core vs the SPDR-008 §8 golden traces.

Run: uv run --with nautilus_trader==1.230.0 --with polars --with numpy --with pandas
     --with tqdm --with scipy --with matplotlib python
     python/experiments/SPDR-008/screen_code/_smoke_trap.py
"""
from __future__ import annotations

import sys

import polars as pl

sys.path.insert(0, "python/src")

from xen.sigbar import fences, sessions, trap  # noqa: E402
from xen.sigbar.baselines import residualise  # noqa: E402

L = 15
SPEC = [s for s in sessions.CANDIDATE_ANCHORS if s.anchor_id == "A-USOPEN"][0]
BASELINES = "python/experiments/INFR-017/results/seasonal_baselines.parquet"


def _prep(symbol: str):
    bars = fences.load_bars(symbol, "DESIGN")
    lo, hi = bars["OpenTime"].min(), bars["OpenTime"].max()
    anch = sessions.anchor_table(SPEC, lo, hi)
    sess = sessions.session_breaks(bars, anch, L)
    joined = sessions.attach_sessions(bars, anch, L)
    bl = pl.scan_parquet(BASELINES).filter(pl.col("symbol") == symbol).collect()
    if bl.height:
        joined = joined.with_columns(
            pl.when(pl.col("Volume") > 0).then(pl.col("Delta") / pl.col("Volume"))
            .otherwise(None).alias("delta_ratio")
        )
        joined = residualise(joined, bl, "delta_ratio", time_col="OpenTime")
    else:
        joined = joined.with_columns(pl.lit(None, dtype=pl.Float64).alias("delta_ratio_resid"))
    return joined, sess


def _traps_for(joined, sess, up_col, dn_col, use_frozen_ib=False):
    from xen.sigbar import acceptance
    lv = trap.boundary_levels(joined, sess) if up_col.startswith(("pva", "prior")) else \
        sess.select("anchor_ts", "ib_high", "ib_low", "ib_width")
    pokes = trap.find_pokes_at_level(joined, lv, up_col, dn_col)
    if use_frozen_ib:
        fp = acceptance.find_pokes(joined, sess, 0.0)
        rej = acceptance.evaluate_discriminator(joined, fp, trap._D4_FROZEN)
    else:
        rej = trap.d4_reject_at_level(joined, pokes)
    return trap.find_traps(joined, pokes, rej)


def one(tag, symbol, up_col, dn_col, day, use_frozen_ib=False):
    joined, sess = _prep(symbol)
    if tag == "IB":
        trap.assert_ib_matches_frozen(joined, sess)
    t = _traps_for(joined, sess, up_col, dn_col, use_frozen_ib)
    if t.height == 0:
        print(f"[{tag}] {symbol}: no traps"); return
    row = t.filter((pl.col("anchor_ts") >= pl.lit(day).str.to_datetime())
                   & (pl.col("anchor_ts") < (pl.lit(day).str.to_datetime() + pl.duration(days=1))))
    if row.height == 0:
        print(f"[{tag}] {symbol} {day}: no trap this session (first is {t['anchor_ts'][0]})"); return
    r = row.row(0, named=True)
    print(f"[{tag}] {symbol} {r['anchor_ts']}  poke_side {r['poke_side']}  level {r['level']:.6g} "
          f"opp {r['opposite_edge']:.6g}  poke_extreme {r['poke_extreme']:.6g}")
    print(f"      reclaim {r['reclaim_ts']}  entry {r['entry']:.6g}  mfe_rev_norm {r['mfe_rev_norm']:.4f} "
          f"mae_rev_norm {r['mae_rev_norm']:.4f}  trap_load {r['trap_load']}  race {r['race']}")


if __name__ == "__main__":
    # GT-1 IB down (+load), GT-2 IB up SOL (−load), GT-3 PVA/PRIOR BTC
    one("IB", "BTCUSDT", "ib_high", "ib_low", "2022-07-15", use_frozen_ib=True)
    one("IB", "SOLUSDT", "ib_high", "ib_low", "2022-07-14", use_frozen_ib=True)
    one("PVA", "BTCUSDT", "pva_high", "pva_low", "2022-07-17")
    one("PRIOR", "BTCUSDT", "prior_high", "prior_low", "2022-07-16")
    print("SMOKE OK — assert_ib_matches_frozen passed for both IB symbols")
