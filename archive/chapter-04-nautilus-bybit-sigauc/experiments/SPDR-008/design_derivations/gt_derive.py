"""Designer-side golden-trace derivation for SPDR-008 (NOT developer code).

Pins concrete IB / PVA / PRIOR trap events under the INFR-018 frozen pin
(anchor A-USOPEN, L=15, A6 = D4-t50-w30, poke delta = 0, kernel K-UNIFORM) so QA
can diff the developer's `xen.sigbar.trap` against an independent oracle. This is
the designer's own re-derivation — deliberately separate from the implementation.

A confirmed trap: a poke beyond a boundary level that FAILS A6 (< 50% of the next
30 bars close beyond) and RECLAIMS (closes back inside within the 30-min window).
Outcome = reversal toward the opposite edge of that boundary's structure vs the
poke-extreme stop. trap_load SIGN is shown from measured flow (poke_side * ΣΔ of
the poke-and-fail bars); the frozen screen uses the seasonally-normalised
delta_ratio_resid, which carries the same sign.
"""

from __future__ import annotations

import sys
import types
from datetime import timedelta

import polars as pl

sys.path.insert(0, "python/src")

# Designer-side derivation only: xen.sigbar.__init__ eagerly imports data_types
# (the engine catalog lane, needs nautilus_trader). This script touches only
# fences/profile/sessions, none of which use the engine. Register stub xen /
# xen.sigbar packages pointing at the real source dirs so submodule imports
# resolve WITHOUT running the heavy __init__.
for _pkg, _path in (("xen", "python/src/xen"), ("xen.sigbar", "python/src/xen/sigbar")):
    _m = types.ModuleType(_pkg)
    _m.__path__ = [_path]
    sys.modules[_pkg] = _m

from xen.sigbar import fences, profile, sessions  # noqa: E402
from xen.sigbar.baselines import residualise  # noqa: E402

L = 15
QUALIFY = 30
SPEC = [s for s in sessions.CANDIDATE_ANCHORS if s.anchor_id == "A-USOPEN"][0]
BASELINES = "python/experiments/INFR-017/results/seasonal_baselines.parquet"


def _prep(symbol: str):
    bars = fences.load_bars(symbol, "DESIGN")
    lo, hi = bars["OpenTime"].min(), bars["OpenTime"].max()
    anchors = sessions.anchor_table(SPEC, lo, hi)
    sess = sessions.session_breaks(bars, anchors, L)
    joined = sessions.attach_sessions(bars, anchors, L)
    # attach the SIGNED A5 residual (delta_ratio_resid) independently of trap.py
    bl = pl.scan_parquet(BASELINES).filter(pl.col("symbol") == symbol).collect()
    if bl.height:
        joined = joined.with_columns(
            pl.when(pl.col("Volume") > 0).then(pl.col("Delta") / pl.col("Volume"))
            .otherwise(None).alias("delta_ratio")
        )
        joined = residualise(joined, bl, "delta_ratio", time_col="OpenTime")
    else:
        joined = joined.with_columns(pl.lit(None, dtype=pl.Float64).alias("delta_ratio_resid"))
    return bars, sess, joined


def _prior_levels(joined: pl.DataFrame, sess: pl.DataFrame) -> pl.DataFrame:
    """Per anchor_ts: prior session's real high/low and proxy VAH/VAL (K-UNIFORM)."""
    anc = sess.select("anchor_ts").sort("anchor_ts")
    rows = []
    prev = None
    for a in anc["anchor_ts"]:
        if prev is not None:
            pb = joined.filter(pl.col("anchor_ts") == prev)
            if pb.height >= 30:
                edges, prof = profile.build_profile(pb, "K-UNIFORM")
                _, val, vah = profile.poc_and_value_area(edges, prof)
                rows.append({
                    "anchor_ts": a, "prior_anchor": prev,
                    "prior_high": float(pb["High"].max()), "prior_low": float(pb["Low"].min()),
                    "pva_high": vah, "pva_low": val,
                })
        prev = a
    return pl.DataFrame(rows) if rows else pl.DataFrame()


def _find_trap(joined: pl.DataFrame, sess: pl.DataFrame, level_col_up: str, level_col_dn: str,
               levels: pl.DataFrame | None = None):
    """First confirmed trap (failed+reclaimed poke) at the given up/down levels."""
    s = sess.join(levels, on="anchor_ts", how="inner") if levels is not None else sess
    for r in s.sort("anchor_ts").iter_rows(named=True):
        up, dn = r[level_col_up], r[level_col_dn]
        if up is None or dn is None or not (up > dn):
            continue
        post = joined.filter(
            (pl.col("anchor_ts") == r["anchor_ts"])
            & (pl.col("mins_since") >= L)
            & (pl.col("OpenTime") < r["session_end"])
        ).sort("OpenTime")
        if post.height == 0:
            continue
        up_hit = post.filter(pl.col("High") > up)
        dn_hit = post.filter(pl.col("Low") < dn)
        cand = []
        if up_hit.height:
            cand.append((1, up_hit["OpenTime"][0], up))
        if dn_hit.height:
            cand.append((-1, dn_hit["OpenTime"][0], dn))
        if not cand:
            continue
        side, poke_ts, level = min(cand, key=lambda c: c[1])
        qend = poke_ts + timedelta(minutes=QUALIFY)
        if qend >= r["session_end"]:
            continue
        qual = post.filter((pl.col("OpenTime") >= poke_ts) & (pl.col("OpenTime") < qend))
        if qual.height == 0:
            continue
        beyond = (qual["Close"] > level) if side == 1 else (qual["Close"] < level)
        frac = float(beyond.sum()) / qual.height
        if frac >= 0.5:
            continue  # accepted, not a trap
        # reclaim: first bar in the window closing back inside the level
        inside = (qual["Close"] <= level) if side == 1 else (qual["Close"] >= level)
        recl = qual.filter(inside)
        if recl.height == 0:
            continue
        reclaim_ts = recl["OpenTime"][0]
        poke_bars = qual.filter(pl.col("OpenTime") <= reclaim_ts)
        poke_extreme = float(poke_bars["High"].max()) if side == 1 else float(poke_bars["Low"].min())
        load_sign_raw = side * float(poke_bars["Delta"].sum())
        rr = poke_bars["delta_ratio_resid"]
        trap_load = None if rr.null_count() == rr.len() else side * float(rr.fill_null(0.0).sum())
        entry_bar = post.filter(pl.col("OpenTime") == reclaim_ts + timedelta(minutes=1))
        if entry_bar.height == 0:
            continue
        entry = float(entry_bar["Open"][0])
        rev_side = -side  # reversal is opposite the poke
        opp = dn if side == 1 else up  # opposite edge of the structure
        out = post.filter(pl.col("OpenTime") > reclaim_ts)
        if out.height == 0:
            continue
        hi_p, lo_p = float(out["High"].max()), float(out["Low"].min())
        if rev_side == 1:  # long reversal (after failed down-poke)
            mfe, mae = hi_p - entry, entry - lo_p
        else:              # short reversal (after failed up-poke)
            mfe, mae = entry - lo_p, hi_p - entry
        ibw = r["ib_width"]
        return {
            "anchor_ts": r["anchor_ts"], "prior_anchor": r.get("prior_anchor"),
            "side_poke": side, "level": level, "poke_ts": poke_ts, "poke_extreme": poke_extreme,
            "beyond_frac": frac, "reclaim_ts": reclaim_ts, "entry": entry, "rev_side": rev_side,
            "opposite_edge": opp, "ib_width": ibw, "mfe_norm": mfe / ibw, "mae_norm": mae / ibw,
            "load_sign_raw": load_sign_raw, "trap_load": trap_load, "n_post": out.height,
        }
    return None


def _show(tag: str, symbol: str, t: dict | None) -> None:
    if t is None:
        print(f"[{tag}] {symbol}: NO TRAP FOUND")
        return
    print(f"[{tag}] {symbol}  session {t['anchor_ts']}  (prior {t.get('prior_anchor')})")
    print(f"    poke_side {'UP' if t['side_poke']==1 else 'DOWN'}  level {t['level']:.6g}  "
          f"poke_ts {t['poke_ts']}  poke_extreme {t['poke_extreme']:.6g}")
    print(f"    beyond_frac {t['beyond_frac']:.4f} (<0.5 REJECT)  reclaim_ts {t['reclaim_ts']}")
    print(f"    entry {t['entry']:.6g}  rev_side {'LONG' if t['rev_side']==1 else 'SHORT'}  "
          f"opposite_edge {t['opposite_edge']:.6g}  ib_width {t['ib_width']:.6g}")
    tl = t['trap_load']
    print(f"    MFE_rev_norm {t['mfe_norm']:.4f}  MAE_rev_norm {t['mae_norm']:.4f}  n_post {t['n_post']}")
    print(f"    trap_load (poke_side*Σ delta_ratio_resid) {tl if tl is None else round(tl,4)}  "
          f"[raw poke_side*ΣΔ {t['load_sign_raw']:+.4g}]")


def main() -> None:
    fences.assert_frozen_inputs()
    for sym in ("BTCUSDT", "SOLUSDT", "ETHUSDT"):
        bars, sess, joined = _prep(sym)
        lv = _prior_levels(joined, sess)
        _show("IB", sym, _find_trap(joined, sess, "ib_high", "ib_low"))
        if lv.height:
            _show("PVA", sym, _find_trap(joined, sess, "pva_high", "pva_low", lv))
            _show("PRIOR", sym, _find_trap(joined, sess, "prior_high", "prior_low", lv))
        print()


if __name__ == "__main__":
    main()
