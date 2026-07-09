"""EXP-025 T1 — per-cell TRAIN statistics + SEL-NEIGHBOR qualification (design §7).

Blocks: trades are non-overlapping (one position at a time), so one trade already spans
>= H LTF bars; the design's block >= H (in bars) is satisfied at block=1 in trade units.
Primary CI uses block=8 trades (regime persistence conservatism) with the INFR-004 sweep
at {4, 8, 16}; sign flips across the sweep are flagged block-fragile.
"""
import json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
from xen.evaluation import block_bootstrap_ci, round_trip_cost_bps, trimmed_mean

RES = os.path.join(os.path.dirname(__file__), "..", "results")
X_GRID = [2, 3, 4, 5, 8]
BASE_USD = {"EURJPY": 1.08, "GBPJPY": 1.26, "AUDJPY": 0.66}   # pinned base->USD for flat_USD crosses


def commission_bps(sym: str, px: float) -> float:
    if sym in ("DE40", "STOXX50"):        # not in FTMO table under these names; index class,
        return 0.0                        # 0 commission (design §10: "indices 0 commission")
    try:
        return round_trip_cost_bps(sym, px, spread_pips=0.0, base_usd_rate=BASE_USD.get(sym))
    except Exception as e:                                    # noqa: BLE001 - disclose, don't die
        print(f"WARN commission {sym}: {e}", file=sys.stderr)
        return float("nan")


def main() -> None:
    df = pd.read_parquet(os.path.join(RES, "train_trades.parquet"))
    comm = {s: commission_bps(s, float(g["EntryFillPrice"].median()))
            for s, g in df.groupby("symbol")}
    json.dump(comm, open(os.path.join(RES, "commission_bps.json"), "w"), indent=2)

    out = []
    for (sym, x, h), g in df.groupby(["symbol", "x", "h"]):
        g = g.sort_values("EntryTime")
        gross = g["RealizedBps"].to_numpy(float)
        net = gross - comm[sym]
        r = dict(symbol=sym, x=x, h=h, n=len(g), comm_bps=comm[sym],
                 gross_mean=gross.mean(), net_mean=net.mean(),
                 net_median=float(np.median(net)), net_sd=net.std(),
                 net_trimmed=trimmed_mean(net),
                 hit=float((gross > 0).mean()))
        ci = block_bootstrap_ci(net, block=8)
        r.update(ci_low=ci["ci"][0], ci_high=ci["ci"][1],
                 ci_low_seed_range=str(ci["ci_low_seed_range"]))
        for b in (4, 16):
            cb = block_bootstrap_ci(net, block=b)
            r[f"ci_low_b{b}"], r[f"ci_high_b{b}"] = cb["ci"]
        f0 = net[(g["fold"] == "F0").to_numpy()]
        f1 = net[(g["fold"] == "F1").to_numpy()]
        f2 = net[(g["fold"] == "F2").to_numpy()]
        c0 = block_bootstrap_ci(f0, block=8)
        c1 = block_bootstrap_ci(f1, block=8)
        c2 = block_bootstrap_ci(f2, block=8)
        f12 = np.concatenate([f1, f2])
        r.update(f0_n=len(f0), f0_mean=c0["stat"], f0_ci_low=c0["ci"][0], f0_ci_high=c0["ci"][1],
                 f0_ci_low_seed_range=str(c0["ci_low_seed_range"]),
                 f1_mean=f1.mean() if len(f1) else np.nan, f1_ci_high=c1["ci"][1],
                 f2_mean=f2.mean() if len(f2) else np.nan, f2_ci_high=c2["ci"][1],
                 f12_mean=f12.mean() if len(f12) else np.nan)
        # per-year net means (regime stability disclosure)
        yr = g["EntryTime"].dt.year.to_numpy()
        for y in sorted(set(yr)):
            r[f"net_{y}"] = float(net[yr == y].mean())
        out.append(r)
    cells = pd.DataFrame(out)

    # ---- SEL-NEIGHBOR (design §7, amended) --------------------------------------------
    q = []
    for (sym, h), grp in cells.groupby(["symbol", "h"]):
        grp = grp.set_index("x")
        for x in X_GRID:
            i = X_GRID.index(x)
            nb = [X_GRID[j] for j in (i - 1, i, i + 1) if 0 <= j < len(X_GRID)]
            f0s = [grp.loc[k, "f0_mean"] for k in nb]
            if len(f0s) == 3:
                nb_med = float(np.sort(f0s)[1])
            else:                                            # boundary: lower median of 2 = min
                nb_med = float(min(f0s))
            row = grp.loc[x]
            r1 = row["f0_mean"] > 0 and row["f0_ci_low"] > 0
            r2 = nb_med > 0
            r3 = (np.sign(row["f12_mean"]) == np.sign(row["f0_mean"])
                  and not (row["f1_ci_high"] < 0) and not (row["f2_ci_high"] < 0))
            contradicted = [k for k in nb if grp.loc[k, "f0_ci_high"] < 0]
            q.append(dict(symbol=sym, x=x, h=h, qualifies=bool(r1 and r2 and r3),
                          rule1_own_ci=bool(r1), rule2_nb_median=bool(r2),
                          rule3_fold_persist=bool(r3), nb_median=nb_med,
                          contradicted_neighbours=str(contradicted)))
    qual = pd.DataFrame(q)
    cells = cells.merge(qual, on=["symbol", "x", "h"])
    cells.to_csv(os.path.join(RES, "cell_stats.csv"), index=False)

    qc = cells[cells["qualifies"]]
    print("qualifying cells:", len(qc))
    if len(qc):
        print(qc[["symbol", "x", "h", "n", "net_mean", "ci_low", "ci_high",
                  "f0_mean", "f0_ci_low", "nb_median"]].to_string(index=False))


if __name__ == "__main__":
    main()
