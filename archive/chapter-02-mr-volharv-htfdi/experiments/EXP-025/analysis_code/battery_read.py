"""Probe (a): 25-seed matched-cadence random-direction battery vs candidate — DIAGNOSTIC.

Design §6 CTRL-RND-BATTERY read, applied to the 3 full-TRAIN disclosure cells (not an
eligibility claim: rule 1 already failed; this discriminates DI-information vs drift).
Battery preserves entry cadence and hold; direction ~ Bernoulli(0.5) — drift-SYMMETRIC:
a drift edge is halved-and-cancelled in expectation, a DI edge is destroyed entirely.
Read: candidate TRAIN net mean vs battery mean in seed-SD units + percentile rank.
NOTE the battery's expected mean is ~0 net of drift; a candidate that beats the battery by
< 2 seed-SD is inside the no-information envelope.
"""
import glob, json, os, sys
import numpy as np
import pandas as pd

RES = os.path.join(os.path.dirname(__file__), "..", "results")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
CELLS = [("HK50", 2, 48), ("US500", 4, 24), ("US500", 5, 24)]


def main() -> None:
    cuts = json.load(open(os.path.join(RES, "train_cuts.json")))
    cand = pd.read_parquet(os.path.join(RES, "train_trades.parquet"))
    rows = []
    for sym, x, h in CELLS:
        c = cand[(cand.symbol == sym) & (cand.x == x) & (cand.h == h)]
        cand_mean = float(c["RealizedBps"].mean())
        seeds = []
        pat = os.path.join(ROOT, "data", "strategy_runs",
                           f"EXP-025-bat1???-{sym.lower()}-x{x}-e0-h{h}", "htfdi_*")
        for d in sorted(glob.glob(pat)):
            m = json.load(open(os.path.join(d, "run_metadata.json")))
            seed = m["parameters"]["battery_seed"]
            t = pd.read_parquet(os.path.join(d, "cis_trades.parquet"))
            t = t[~t["Censored"].astype(bool)]
            t["EntryTime"] = pd.to_datetime(t["EntryTime"])
            t = t[t["EntryTime"] < pd.Timestamp(cuts[sym])]
            seeds.append(dict(seed=seed, n=len(t), mean=float(t["RealizedBps"].mean())))
        s = pd.DataFrame(seeds)
        assert len(s) == 25, f"{sym} x{x} h{h}: {len(s)} seeds"
        bat_mean, bat_sd = s["mean"].mean(), s["mean"].std(ddof=1)
        z = (cand_mean - bat_mean) / bat_sd
        pct = float((s["mean"] < cand_mean).mean())
        # cadence disclosure (D5): battery n vs candidate n
        rows.append(dict(cell=f"{sym} x{x} h{h}", cand_n=len(c), cand_mean=round(cand_mean, 3),
                         bat_mean=round(bat_mean, 3), bat_sd=round(bat_sd, 3),
                         bat_n_min=int(s.n.min()), bat_n_max=int(s.n.max()),
                         z_seed_sd=round(z, 2), pct_rank=pct,
                         beats_2sd=bool(z >= 2)))
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(RES, "battery_read.csv"), index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
