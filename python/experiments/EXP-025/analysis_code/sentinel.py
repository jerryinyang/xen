"""EXP-025 — CTRL-NULLSENT: ADX-only sentinel, family-wise read (design §6 amended).

Per-stratum net mean + block CI on TRAIN trades; investigation triggers only if the count
of CI-clear strata exceeds the binomial 95th percentile at p=0.05 x N.
"""
import glob, json, os, sys
import numpy as np
import pandas as pd
from scipy.stats import binom

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
from xen.evaluation import block_bootstrap_ci

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
RES = os.path.join(os.path.dirname(__file__), "..", "results")


def main() -> None:
    cuts = json.load(open(os.path.join(RES, "train_cuts.json")))
    rows = []
    for d in sorted(glob.glob(os.path.join(ROOT, "data", "strategy_runs", "EXP-025-sent", "htfdi_*"))):
        sym = json.load(open(os.path.join(d, "run_metadata.json")))["symbol"]
        t = pd.read_parquet(os.path.join(d, "cis_trades.parquet"))
        t = t[~t["Censored"].astype(bool)]
        t["EntryTime"] = pd.to_datetime(t["EntryTime"])
        t = t[t["EntryTime"] < pd.Timestamp(cuts[sym])].sort_values("EntryTime")
        x = t["RealizedBps"].to_numpy(float)
        ci = block_bootstrap_ci(x, block=8)
        rows.append(dict(symbol=sym, n=len(x), mean_bps=x.mean() if len(x) else np.nan,
                         ci_low=ci["ci"][0], ci_high=ci["ci"][1],
                         clear=bool(ci["ci"][0] > 0 or ci["ci"][1] < 0)))
    out = pd.DataFrame(rows)
    n_clear = int(out["clear"].sum())
    thresh = int(binom.ppf(0.95, len(out), 0.05))
    out.to_csv(os.path.join(RES, "sentinel.csv"), index=False)
    print(out.to_string(index=False))
    print(f"\nCI-clear strata: {n_clear}/{len(out)}; binomial 95th pct at p=0.05: {thresh} "
          f"-> {'INVESTIGATE' if n_clear > thresh else 'WITHIN EXPECTATION'}")


if __name__ == "__main__":
    main()
