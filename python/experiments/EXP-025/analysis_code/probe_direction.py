"""Probe (b): long vs short net decomposition across all index cells (drift forensics).

If the index positives are drift (beta), each index's edge should sit on its own realized
drift side and scale with H; a DI-information edge should appear on both sides.
Also computes the per-symbol TRAIN drift (mean H-bar open-to-open return per trade slot)
as the beta yardstick.
"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
from xen.evaluation import block_bootstrap_ci

RES = os.path.join(os.path.dirname(__file__), "..", "results")
IDX = ["USTEC", "US500", "US2000", "JP225", "AUS200", "US30", "STOXX50", "DE40", "HK50", "UK100"]


def main() -> None:
    df = pd.read_parquet(os.path.join(RES, "train_trades.parquet"))
    rows = []
    for (sym, x, h), g in df.groupby(["symbol", "x", "h"]):
        if sym not in IDX:
            continue
        r = dict(symbol=sym, x=x, h=h, n=len(g))
        for d, tag in ((1, "long"), (-1, "short")):
            s = g[g["Direction"] == d].sort_values("EntryTime")["RealizedBps"].to_numpy(float)
            ci = block_bootstrap_ci(s, block=8)
            r[f"{tag}_n"] = len(s)
            r[f"{tag}_mean"] = float(s.mean()) if len(s) else np.nan
            r[f"{tag}_ci_low"], r[f"{tag}_ci_high"] = ci["ci"]
        # drift yardstick: signed sum/n if all trades were longs = mean unsigned move captured
        raw = (g["Direction"] * g["RealizedBps"]).to_numpy(float)   # unsigned H-bar return
        r["drift_bps_per_slot"] = float(raw.mean())
        rows.append(r)
    out = pd.DataFrame(rows).sort_values(["symbol", "x", "h"])
    out.to_csv(os.path.join(RES, "direction_split.csv"), index=False)

    # summary: per symbol pooled over cells
    print("Per-symbol pooled (disclosure): long vs short mean bps, drift/slot")
    agg = out.groupby("symbol").apply(
        lambda t: pd.Series(dict(
            long_mean=np.average(t.long_mean, weights=t.long_n),
            short_mean=np.average(t.short_mean, weights=t.short_n),
            drift=np.average(t.drift_bps_per_slot, weights=t.n))), include_groups=False)
    print(agg.round(2).to_string())
    # cells where BOTH sides positive-signed (DI-information shape)
    both = out[(out.long_mean > 0) & (out.short_mean > 0)]
    print(f"\ncells with both sides > 0: {len(both)}/{len(out)}")
    if len(both):
        print(both[["symbol", "x", "h", "long_mean", "short_mean"]].to_string(index=False))
    # cells where the edge side matches the drift sign
    out["edge_side"] = np.where(out.long_mean.fillna(-9e9) > out.short_mean.fillna(-9e9), 1, -1)
    out["drift_side"] = np.sign(out.drift_bps_per_slot)
    match = (out.edge_side == out.drift_side).mean()
    print(f"\nfraction of index cells whose stronger side == drift side: {match:.2f}")


if __name__ == "__main__":
    main()
