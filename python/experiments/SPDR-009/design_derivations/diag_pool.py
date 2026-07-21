"""Diagnostic: how large is the S9 candidate pool, and what binds it?

Designer-side power probe for SPDR-009 §6. Reports, per symbol on the DESIGN
band: bars, unsigned climax-hold base count, the marginal effect of each leg,
and the distribution of distance from the base bar's close to its nearest
structural level (normalised by that session's IB width) — the quantity that
decides whether "at a level" needs a stated tolerance (source §2.1: profile
levels are zones with tolerance, never precision levels).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

sys.path.insert(0, str(Path(__file__).parent))
from gt_derive import REGISTRY, levels_for, resid  # noqa: E402

from xen.sigbar.fences import load_bars, repo_root  # noqa: E402
from xen.sigbar.sessions import anchor_table, attach_sessions, session_breaks  # noqa: E402
from xen.sigbar.spine import IB_MINUTES, anchor_spec  # noqa: E402


def probe(symbol: str, th: dict) -> dict:
    bars = load_bars(symbol, "DESIGN")
    if bars.height == 0:
        return {"symbol": symbol, "n_bars": 0}
    spec = anchor_spec()
    anchors = anchor_table(spec, bars["OpenTime"].min(), bars["OpenTime"].max())
    sess = session_breaks(bars, anchors, IB_MINUTES)
    lv = levels_for(bars, sess)
    r = resid(bars, symbol)
    j = attach_sessions(r, anchors, IB_MINUTES).join(
        sess.select("anchor_ts", "ib_width"), on="anchor_ts", how="left"
    )

    v_hi, r_lo = th["volume"]["high"], th["range"]["low"]
    d_hi, dr_abs_hi = th["delta_abs"]["high"], th["delta_ratio"]["abs_high"]

    n = j.height
    n_v = j.filter(pl.col("volume_resid") >= v_hi).height
    n_r = j.filter(pl.col("range_resid") <= r_lo).height
    base = j.filter((pl.col("volume_resid") >= v_hi) & (pl.col("range_resid") <= r_lo))
    n_base = base.height
    n_abs = base.filter(pl.col("delta_abs_resid") >= d_hi).height
    n_s9 = base.filter(
        (pl.col("delta_abs_resid") >= d_hi)
        & (pl.col("delta_ratio_resid").abs() >= dr_abs_hi)
    ).height

    # distance from each base bar's close to its nearest level, in IB widths
    d_norm = np.array([])
    n_contact = 0
    if n_base:
        jj = base.select("anchor_ts", "OpenTime", "Close", "High", "Low", "ib_width").join(
            lv, on="anchor_ts", how="inner"
        )
        if jj.height:
            jj = jj.with_columns(
                (pl.col("Close") - pl.col("level_price")).abs().alias("d"),
                (
                    (pl.col("Low") <= pl.col("level_price"))
                    & (pl.col("level_price") <= pl.col("High"))
                ).alias("inside"),
            )
            g = jj.group_by("OpenTime").agg(
                pl.col("d").min().alias("d_min"),
                pl.col("ib_width").first(),
                pl.col("inside").any().alias("any_inside"),
            )
            g = g.filter(pl.col("ib_width") > 0).with_columns(
                (pl.col("d_min") / pl.col("ib_width")).alias("d_norm")
            )
            d_norm = g["d_norm"].drop_nulls().to_numpy()
            n_contact = int(g["any_inside"].sum())

    q = (
        {f"p{int(p*100)}": float(np.quantile(d_norm, p)) for p in (0.1, 0.25, 0.5, 0.75)}
        if len(d_norm)
        else {}
    )
    return {
        "symbol": symbol,
        "n_bars": n,
        "n_vol_high": n_v,
        "n_range_low": n_r,
        "n_base_joint": n_base,
        "n_base_and_delta_abs": n_abs,
        "n_base_and_delta_abs_and_ratio": n_s9,
        "n_base_level_inside_bar": n_contact,
        "d_norm_quantiles_ib_widths": q,
        "frac_base_within_0.05_ib": (
            float((d_norm <= 0.05).mean()) if len(d_norm) else None
        ),
        "frac_base_within_0.10_ib": (
            float((d_norm <= 0.10).mean()) if len(d_norm) else None
        ),
        "frac_base_within_0.25_ib": (
            float((d_norm <= 0.25).mean()) if len(d_norm) else None
        ),
    }


def main() -> None:
    reg = json.loads((repo_root() / REGISTRY).read_text())
    th_all = reg["class_thresholds"]["per_symbol_values"]
    syms = sys.argv[1:] or ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT"]
    rows = []
    for s in syms:
        if s not in th_all:
            print(f"{s}: no pinned class thresholds")
            continue
        row = probe(s, th_all[s])
        rows.append(row)
        print(json.dumps(row, indent=1))
    (Path(__file__).parent / "diag_pool.json").write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
