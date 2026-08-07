"""HIGH-minus-LOW baseline expectancy contrast, and per-arm gated-vs-ungated contrast."""
from __future__ import annotations
import json
import sys
import numpy as np
import polars as pl
sys.path.insert(0, "experiments/SPDR-024/analysis_code")
from da_boot import two_stage_boot_mean

CELLS = ["ctrader_H1", "ctrader_H4", "crypto_H1", "crypto_H4"]
ROOT = "experiments/SPDR-024/results/analysis"


def bm(df, col, seed):
    v = df[col].to_numpy()
    _, s = np.unique(df["symbol"].to_numpy(), return_inverse=True)
    return two_stage_boot_mean(v, s, np.arange(len(v)), n_boot=2000, seed=seed)


out = {}
for cell in CELLS:
    d = pl.read_parquet(f"{ROOT}/{cell}/episodes.parquet")
    b = d.filter((pl.col("arm_id") == "FIXED_SIZE_UNIT") & pl.col("exit_ts").is_not_null())
    hi = b.filter(pl.col("regime_state") == "HIGH")
    lo = b.filter(pl.col("regime_state") == "LOW")
    diff = bm(hi, "outcome_bps", 1) - bm(lo, "outcome_bps", 2)
    rec = {"HIGH_n": hi.height, "LOW_n": lo.height,
           "HIGH_mean": float(hi["outcome_bps"].mean()), "LOW_mean": float(lo["outcome_bps"].mean()),
           "HIGH_minus_LOW": float(hi["outcome_bps"].mean() - lo["outcome_bps"].mean()),
           "ci": [float(np.quantile(diff, .025)), float(np.quantile(diff, .975))],
           "HIGH_median": float(hi["outcome_bps"].median()), "LOW_median": float(lo["outcome_bps"].median())}
    # per-arm: baseline mean on gated (risk_size<1) vs ungated rows
    arms = d.filter((pl.col("arm_class") == "MANAGEMENT") & (pl.col("device") == "SIZE"))["arm_id"].unique().sort().to_list()
    per = []
    bs = b.select(["origin_id", "symbol", "outcome_bps"])
    for arm in arms:
        a = d.filter((pl.col("arm_id") == arm) & pl.col("exit_ts").is_not_null()).select(["origin_id", "risk_size"])
        j = bs.join(a, on="origin_id")
        g = j.filter(pl.col("risk_size") < 1.0)
        u = j.filter(pl.col("risk_size") >= 1.0)
        r = {"arm": arm, "n_gated": g.height, "n_ungated": u.height,
             "gated_mean_bps": float(g["outcome_bps"].mean()) if g.height else None,
             "ungated_mean_bps": float(u["outcome_bps"].mean()) if u.height else None,
             "mean_risk_size_gated": float(g["risk_size"].mean()) if g.height else None}
        if g.height > 20 and u.height > 20:
            dd = bm(g, "outcome_bps", 3) - bm(u, "outcome_bps", 4)
            r["gated_minus_ungated"] = r["gated_mean_bps"] - r["ungated_mean_bps"]
            r["ci"] = [float(np.quantile(dd, .025)), float(np.quantile(dd, .975))]
        per.append(r)
    rec["per_arm_gate"] = per
    out[cell] = rec
    print(cell, "done", file=sys.stderr)
json.dump(out, open(sys.argv[1], "w"), indent=1)
