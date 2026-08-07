"""QUARANTINED pre-AMENDMENT-7. Do not use for emission or analysis.md."""
raise RuntimeError(
    "AMENDMENT_7_QUARANTINE: this script is legacy (pre R1-R5 floor fix). "
    "Use analysis_code/analyse.py emission only; see legacy_pre_a7/README.md."
)

"""Selection channel restricted to GENUINE rejections (state == NO_EVENT).

The emitted read pools two disjoint populations into 'rejected':
  * NO_EVENT   - the rule evaluated the origin and declined it  (a genuine rejection)
  * NO_FEATURE - the component's feature did not exist yet      (warm-up; never evaluated)
Only the first answers 'does the filter select better trades?'.
"""
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


rows = []
for cell in CELLS:
    d = pl.read_parquet(f"{ROOT}/{cell}/episodes.parquet")
    arms = d.filter(pl.col("arm_class").is_in(["NATIVE", "NATIVE_COMBINATION"]))["arm_id"].unique().sort().to_list()
    for arm in arms:
        a = d.filter(pl.col("arm_id") == arm)
        adm = a.filter(pl.col("admitted") & pl.col("exit_ts").is_not_null())
        rej_all = a.filter(pl.col("counterfactual_source") == "FIXED_ARM_REALISED_OUTCOME")
        rej_gen = rej_all.filter(pl.col("state") == "NO_EVENT")
        rej_nof = rej_all.filter(pl.col("state") == "NO_FEATURE")
        rec = {"cell": cell, "arm": arm, "n_admitted": adm.height,
               "n_rejected_emitted": rej_all.height,
               "n_rejected_genuine": rej_gen.height, "n_rejected_no_feature": rej_nof.height,
               "no_feature_share_of_rejected": rej_nof.height / rej_all.height if rej_all.height else None,
               "admitted_mean_bps": float(adm["outcome_bps"].mean()) if adm.height else None,
               "rejected_emitted_mean_bps": float(rej_all["counterfactual_outcome_bps"].mean()) if rej_all.height else None,
               "rejected_genuine_mean_bps": float(rej_gen["counterfactual_outcome_bps"].mean()) if rej_gen.height else None,
               "rejected_no_feature_mean_bps": float(rej_nof["counterfactual_outcome_bps"].mean()) if rej_nof.height else None}
        if rej_gen.height >= 30 and adm.height >= 30:
            diff = bm(adm, "outcome_bps", 3) - bm(rej_gen, "counterfactual_outcome_bps", 77)
            rec["contrast_genuine_bps"] = rec["admitted_mean_bps"] - rec["rejected_genuine_mean_bps"]
            rec["ci_genuine"] = [float(np.quantile(diff, .025)), float(np.quantile(diff, .975))]
            rec["ci_excludes_zero"] = bool(rec["ci_genuine"][0] > 0 or rec["ci_genuine"][1] < 0)
            rec["mde_bps"] = float(2.8 * np.sqrt(
                adm["outcome_bps"].var() / adm.height
                + rej_gen["counterfactual_outcome_bps"].var() / rej_gen.height))
        else:
            rec["status"] = "NOT_RESOLVABLE_fewer_than_30_genuine_rejections"
        rows.append(rec)
    print(cell, "done", file=sys.stderr)
json.dump(rows, open(sys.argv[1], "w"), indent=1)
