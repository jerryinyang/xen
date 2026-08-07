"""Data-analyst independent SELECTION-channel recomputation with intervals.

The emitted selection_channel_estimates.parquet carries NO confidence interval and only one
variance treatment; the design's band rule needs both. Recomputed here.
"""
from __future__ import annotations
import json
import sys
import numpy as np
import polars as pl

sys.path.insert(0, "experiments/SPDR-024/analysis_code")
from da_boot import two_stage_boot_mean  # noqa: E402

CELLS = ["ctrader_H1", "ctrader_H4", "crypto_H1", "crypto_H4"]
ROOT = "experiments/SPDR-024/results/analysis"
N_BOOT = 2000
N_SEEDS = 3
DOM_NS = {"H1": 3_600_000_000_000, "H4": 14_400_000_000_000}


def boot_mean(df: pl.DataFrame, val: str, block_col: str, seed: int) -> np.ndarray:
    v = df[val].to_numpy()
    _, sym = np.unique(df["symbol"].to_numpy(), return_inverse=True)
    if block_col == "TRADE":
        blk = np.arange(len(v))
    else:
        _, blk = np.unique(df[block_col].to_numpy(), return_inverse=True)
    return two_stage_boot_mean(v, sym, blk, n_boot=N_BOOT, seed=seed)


rows = []
for cell in CELLS:
    d = pl.read_parquet(f"{ROOT}/{cell}/episodes.parquet")
    dom = DOM_NS[cell.split("_")[1]]
    d = d.with_columns((pl.col("decision_ts").dt.epoch("ns") // (24 * dom)).alias("tblock"))
    base = d.filter((pl.col("arm_id") == "FIXED_NATIVE_BREAKOUT") & pl.col("exit_ts").is_not_null())
    base_mean = float(base["outcome_bps"].mean())
    arms = (d.filter(pl.col("arm_class").is_in(["NATIVE", "NATIVE_COMBINATION"]))
            ["arm_id"].unique().sort().to_list())
    for arm in arms:
        a = d.filter(pl.col("arm_id") == arm)
        adm = a.filter(pl.col("admitted") & pl.col("exit_ts").is_not_null())
        rej = a.filter(pl.col("counterfactual_source") == "FIXED_ARM_REALISED_OUTCOME")
        rec = {"cell": cell, "arm": arm, "component": a["component"][0],
               "entry_variant": a["entry_variant"][0],
               "n_admitted": adm.height, "n_rejected": rej.height,
               "n_baseline_fills": base.height, "baseline_mean_bps": base_mean,
               "admitted_mean_bps": float(adm["outcome_bps"].mean()) if adm.height else None,
               "rejected_cf_mean_bps": float(rej["counterfactual_outcome_bps"].mean()) if rej.height else None,
               "admitted_median_bps": float(adm["outcome_bps"].median()) if adm.height else None,
               "rejected_cf_median_bps": float(rej["counterfactual_outcome_bps"].median()) if rej.height else None,
               "admitted_win_share": float((adm["outcome_bps"].to_numpy() > 0).mean()) if adm.height else None,
               "rejected_win_share": float((rej["counterfactual_outcome_bps"].to_numpy() > 0).mean()) if rej.height else None,
               "rejected_cf_zero_share": float((rej["counterfactual_outcome_bps"].to_numpy() == 0).mean()) if rej.height else None,
               }
        if rej.height >= 5 and adm.height >= 5:
            rec["contrast_bps"] = rec["admitted_mean_bps"] - rec["rejected_cf_mean_bps"]
            for tname, bc in [("V_A", "TRADE"), ("V_B", "tblock"), ("V_C", "regime_episode_id")]:
                los, his = [], []
                for s in range(N_SEEDS):
                    da = boot_mean(adm, "outcome_bps", bc, 500 + s)
                    dr = boot_mean(rej, "counterfactual_outcome_bps", bc, 900 + s)
                    diff = da - dr
                    los.append(np.quantile(diff, 0.025))
                    his.append(np.quantile(diff, 0.975))
                rec[f"{tname}_ci"] = [float(np.median(los)), float(np.median(his))]
                rec[f"{tname}_width"] = float(np.median(his) - np.median(los))
            wlo = min(rec[f"{t}_ci"][0] for t in ["V_A", "V_B", "V_C"])
            whi = max(rec[f"{t}_ci"][1] for t in ["V_A", "V_B", "V_C"])
            rec["strict_ci"] = [wlo, whi]
            rec["strict_ci_excludes_zero"] = bool(wlo > 0 or whi < 0)
            # median contrast (outlier-robust)
            rec["contrast_median_bps"] = rec["admitted_median_bps"] - rec["rejected_cf_median_bps"]
            # trimmed-mean contrast
            def tm(x, t=0.1):
                a_ = np.sort(x)
                k = int(len(a_) * t)
                return float(a_[k:len(a_) - k].mean()) if len(a_) - 2 * k > 0 else float(a_.mean())
            rec["contrast_trimmed10_bps"] = tm(adm["outcome_bps"].to_numpy()) - tm(rej["counterfactual_outcome_bps"].to_numpy())
            # win-share contrast (a location-free selection read)
            rec["win_share_contrast"] = rec["admitted_win_share"] - rec["rejected_win_share"]
        rows.append(rec)
        print(f"{cell} {arm} done", file=sys.stderr)

json.dump(rows, open(sys.argv[1], "w"), indent=1)
