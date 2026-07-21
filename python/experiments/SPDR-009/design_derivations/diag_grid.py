"""Count-only power grid for the SPDR-009 event definition.

NOTHING in this script touches a forward outcome — it counts events under
candidate operationalisations of "heavy effort, no result, at a level" so the
design can pick a definition that is powered before any read exists. Choosing an
event definition on event COUNTS is a power decision; choosing it on outcomes
would be selection. Only counts are emitted.

Legs swept:
  effort  : volume_resid >= pinned p90 (FROZEN — never swept)
  result  : range_resid <= {pinned p10, per-symbol p25, per-symbol p50}
  contact : level inside the bar's range | |Close-level| <= tau * ib_width,
            tau in {0.05, 0.10, 0.25}
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

TAUS = (0.05, 0.10, 0.25)


def grid(symbol: str, th: dict) -> list[dict]:
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
    d_hi, dr_abs_hi = th["delta_abs"]["high"], th["delta_ratio"]["abs_high"]
    rr = j["range_resid"].drop_nulls()
    cuts = {
        "p10_pinned": th["range"]["low"],
        "p25": float(rr.quantile(0.25)),
        "p50": float(rr.quantile(0.50)),
    }

    rows = []
    for name, cut in cuts.items():
        base = j.filter((pl.col("volume_resid") >= v_hi) & (pl.col("range_resid") <= cut))
        if base.height == 0:
            rows.append({"symbol": symbol, "result_cut": name, "n_base": 0})
            continue
        jj = (
            base.select("anchor_ts", "OpenTime", "Close", "High", "Low", "ib_width",
                        "delta_abs_resid", "delta_ratio_resid")
            .join(lv, on="anchor_ts", how="inner")
            .filter(pl.col("ib_width") > 0)
            .with_columns(
                (pl.col("Close") - pl.col("level_price")).abs().alias("d"),
                (
                    (pl.col("Low") <= pl.col("level_price"))
                    & (pl.col("level_price") <= pl.col("High"))
                ).alias("inside"),
            )
            .with_columns((pl.col("d") / pl.col("ib_width")).alias("d_norm"))
        )
        row = {"symbol": symbol, "result_cut": name, "n_base": base.height}
        for label, expr in [("inside", pl.col("inside"))] + [
            (f"tau{t}", pl.col("d_norm") <= t) for t in TAUS
        ]:
            hit = jj.filter(expr)
            # one event per (bar, level_kind); count distinct bars too
            n_pairs = hit.height
            n_bars = hit.select(pl.col("OpenTime").n_unique()).item() if n_pairs else 0
            n_s9 = (
                hit.filter(
                    (pl.col("delta_abs_resid") >= d_hi)
                    & (pl.col("delta_ratio_resid").abs() >= dr_abs_hi)
                ).height
                if n_pairs
                else 0
            )
            row[f"{label}_pairs"] = n_pairs
            row[f"{label}_bars"] = n_bars
            row[f"{label}_deltaqual_pairs"] = n_s9
        rows.append(row)
    return rows


def main() -> None:
    reg = json.loads((repo_root() / REGISTRY).read_text())
    th_all = reg["class_thresholds"]["per_symbol_values"]
    syms = sys.argv[1:] or ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT"]
    out = []
    for s in syms:
        if s not in th_all:
            continue
        for row in grid(s, th_all[s]):
            out.append(row)
            print(json.dumps(row))
    (Path(__file__).parent / "diag_grid.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
