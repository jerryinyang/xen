"""EXP-025 — Phase 2 falsification probes on the best-looking strata.

No cell qualified under SEL-NEIGHBOR; probes characterise the near-misses and establish
the negative's power (MDE) so "no effect" is distinguishable from "cannot see".
"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
from xen.evaluation import block_bootstrap_ci, mde

RES = os.path.join(os.path.dirname(__file__), "..", "results")
FOCUS = [("HK50", 2, 48), ("HK50", 8, 36), ("USTEC", 4, 48), ("USTEC", 5, 48),
         ("US2000", 8, 48), ("USTEC", 3, 24)]


def main() -> None:
    df = pd.read_parquet(os.path.join(RES, "train_trades.parquet"))
    comm = pd.read_json(os.path.join(RES, "commission_bps.json"), typ="series")

    print("== MDE per cell class (is the negative powered?) ==")
    rows = []
    for (sym, x, h), g in df.groupby(["symbol", "x", "h"]):
        net = g["RealizedBps"].to_numpy(float) - (comm.get(sym, 0.0) or 0.0)
        rows.append(dict(symbol=sym, x=x, h=h, n=len(g),
                         mde_bps=2 * net.std() / np.sqrt(len(net))))
    m = pd.DataFrame(rows)
    m.to_csv(os.path.join(RES, "mde.csv"), index=False)
    print(m.groupby("h")["mde_bps"].describe()[["min", "50%", "max"]].to_string())
    print("cells with MDE > 10 bps:", int((m.mde_bps > 10).sum()), "/", len(m))

    print("\n== Focus cells: year stability / concentration / DI-strength / ATR strata ==")
    for sym, x, h in FOCUS:
        g = df[(df.symbol == sym) & (df.x == x) & (df.h == h)].sort_values("EntryTime")
        net = g["RealizedBps"].to_numpy(float) - (comm.get(sym, 0.0) or 0.0)
        yr = g["EntryTime"].dt.year
        ytab = {int(y): round(float(net[(yr == y).to_numpy()].mean()), 2) for y in sorted(yr.unique())}
        srt = np.sort(net)[::-1]
        tot = net.sum()
        conc = {k: round(float((tot - srt[:k].sum()) / len(net)), 3) for k in (1, 3, 5, 20)}
        distr = dict(q01=np.quantile(net, .01), q05=np.quantile(net, .05),
                     med=np.median(net), q95=np.quantile(net, .95), q99=np.quantile(net, .99))
        # DI-margin split (mechanism: bigger DI gap -> bigger effect if real)
        gap = (g["HtfPlusDi"] - g["HtfMinusDi"]).abs().to_numpy(float)
        hi = gap > np.median(gap)
        ci_hi = block_bootstrap_ci(net[hi], block=8)
        ci_lo = block_bootstrap_ci(net[~hi], block=8)
        # ATR-tercile amplifier
        vr = g["EntryVolRegime"].to_numpy(int)
        atr = {int(v): [round(float(net[vr == v].mean()), 2), int((vr == v).sum())]
               for v in sorted(set(vr))}
        print(f"\n{sym} x{x} h{h} n={len(g)} net={net.mean():.2f}")
        print(f"  per-year net: {ytab}")
        print(f"  net/trade after dropping top-k winners: {conc}")
        print(f"  dist: {[f'{k}={v:.1f}' for k, v in distr.items()]}")
        print(f"  DI-margin high: {ci_hi['stat']:.2f} CI {np.round(ci_hi['ci'],2)} | "
              f"low: {ci_lo['stat']:.2f} CI {np.round(ci_lo['ci'],2)}")
        print(f"  ATR tercile [mean, n] (-1=unset): {atr}")

    print("\n== Cost-to-death (bps commission that zeroes pooled net), per focus symbol ==")
    for sym in {s for s, _, _ in FOCUS}:
        g = df[df.symbol == sym]
        print(f"  {sym}: pooled gross {g.RealizedBps.mean():.2f} bps/trade "
              f"(dies at commission > that); frozen comm {comm.get(sym, 0.0):.2f}")


if __name__ == "__main__":
    main()
