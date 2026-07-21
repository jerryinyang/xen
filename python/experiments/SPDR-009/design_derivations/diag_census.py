"""Deduplicated event census for SPDR-009 §6.3 — COUNT ONLY, no forward outcome.

QA run 1 (I-7, I-8) found the §6.3 power table reported (bar × level) PAIRS, not
events: a bar inside several level zones was counted several times, and the
P_WIDE multiplier was quoted at the effort∧result stage rather than at the event
stage. This script emits the deduplicated numbers both pools actually deliver.

No return, excursion, or forward price is computed, loaded, or written anywhere
in this file. The event definition must never be chosen against outcomes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from gt_derive import REGISTRY, levels_for, resid  # noqa: E402

from xen.sigbar.fences import load_bars, repo_root  # noqa: E402
from xen.sigbar.sessions import anchor_table, attach_sessions, session_breaks  # noqa: E402
from xen.sigbar.spine import IB_MINUTES, anchor_spec  # noqa: E402

#: (result-leg, contact tolerance) for each declared pool.
POOLS = {"P": ("p10_pinned", 0.25), "P_WIDE": ("p25", 0.10)}
#: Refractory in bars — an event whose entry falls this close to an accepted
#: event's entry is dropped (design §2). max(H) over the micro holds.
REFRACTORY = 10


def census(symbol: str, th: dict) -> list[dict]:
    bars = load_bars(symbol, "DESIGN")
    if bars.height == 0:
        return []
    spec = anchor_spec()
    anchors = anchor_table(spec, bars["OpenTime"].min(), bars["OpenTime"].max())
    sess = session_breaks(bars, anchors, IB_MINUTES)
    lv = levels_for(bars, sess)
    r = resid(bars, symbol)
    j = attach_sessions(r, anchors, IB_MINUTES).join(
        sess.select("anchor_ts", "ib_width"), on="anchor_ts", how="left"
    )
    v_hi = th["volume"]["high"]
    d_hi, dr_hi = th["delta_abs"]["high"], th["delta_ratio"]["abs_high"]
    rr = j["range_resid"].drop_nulls()
    cuts = {"p10_pinned": th["range"]["low"], "p25": float(rr.quantile(0.25))}

    rows = []
    for pool, (cut_name, tau) in POOLS.items():
        # prev_close is the PREVIOUS BAR's close, computed before the event
        # filter — taking it after would make it the previous QUALIFYING bar and
        # break the tie rule differently from gt_derive.py (QA-2 R-8).
        base = j.with_columns(
            pl.col("Close").shift(1).alias("prev_close")
        ).filter(
            (pl.col("volume_resid") >= v_hi)
            & (pl.col("range_resid") <= cuts[cut_name])
            & (pl.col("ib_width") > 0)
        )
        if base.height == 0:
            rows.append({"symbol": symbol, "pool": pool, "n_effort_result": 0, "n_events": 0})
            continue
        hit = (
            base.join(lv, on="anchor_ts", how="inner")
            .filter(
                (pl.col("Close") - pl.col("level_price")).abs()
                <= tau * pl.col("ib_width")
            )
            .filter(
                ~pl.col("level_kind").str.starts_with("IB")
                | (pl.col("mins_since") >= IB_MINUTES)
            )
            .with_columns(
                (pl.col("Close") - pl.col("level_price")).abs().alias("d_level")
            )
        )
        if hit.height == 0:
            rows.append(
                {"symbol": symbol, "pool": pool, "n_effort_result": base.height,
                 "n_pairs": 0, "n_events": 0}
            )
            continue
        # DEDUP: one event per bar, nearest level wins (design §3.2 pooled rule)
        ev = (
            hit.sort(["OpenTime", "d_level"])
            .group_by("OpenTime")
            .first()
            .sort("OpenTime")
        )
        into = (
            pl.when(pl.col("Close") < pl.col("level_price"))
            .then(1)
            .when(pl.col("Close") > pl.col("level_price"))
            .then(-1)
            .when(pl.col("prev_close") < pl.col("level_price"))
            .then(1)
            .when(pl.col("prev_close") > pl.col("level_price"))
            .then(-1)
            .otherwise(0)
            .alias("into_side")
        )
        ev = ev.with_columns(into).filter(pl.col("into_side") != 0)
        ev = ev.with_columns(
            (pl.col("into_side") * pl.col("delta_ratio_resid")).alias("signed_score")
        )
        # REFRACTORY on entry times (event_ts + 1min); greedy first-wins
        ts = ev["OpenTime"].to_list()
        keep, last = [], None
        for i, t in enumerate(ts):
            if last is None or (t - last).total_seconds() / 60 > REFRACTORY:
                keep.append(i)
                last = t
        ev = ev[keep]
        big = pl.col("delta_abs_resid") >= d_hi
        n_s9 = ev.filter(big & (pl.col("signed_score") >= dr_hi)).height
        n_mir = ev.filter(big & (pl.col("signed_score") <= -dr_hi)).height
        rows.append(
            {
                "symbol": symbol,
                "pool": pool,
                "result_cut": cut_name,
                "tau": tau,
                "n_effort_result": base.height,
                "n_pairs": hit.height,
                "n_events_dedup_refractory": ev.height,
                "n_S9": n_s9,
                "n_MIRROR": n_mir,
                "n_BASE": ev.height - n_s9 - n_mir,
            }
        )
    return rows


def main() -> None:
    reg = json.loads((repo_root() / REGISTRY).read_text())
    th_all = reg["class_thresholds"]["per_symbol_values"]
    syms = sys.argv[1:] or [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT",
        "ADAUSDT", "AVAXUSDT", "LINKUSDT", "MATICUSDT", "LTCUSDT",
    ]
    out = []
    for s in syms:
        if s not in th_all:
            print(f"{s}: no pinned class thresholds")
            continue
        for row in census(s, th_all[s]):
            out.append(row)
            print(json.dumps(row))
    (Path(__file__).parent / "diag_census.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
