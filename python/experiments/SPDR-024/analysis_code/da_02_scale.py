"""Data-analyst independent recomputation of the SCALE channel (PRIMARY estimand).

Never imports the implementer's analyse.py. Symbol-clustered bootstrap under the three
declared variance treatments (V-A trade, V-B fixed time block, V-C regime-episode block).
"""
from __future__ import annotations
import json
import sys
import numpy as np
import polars as pl

sys.path.insert(0, "experiments/SPDR-024/analysis_code")

CELLS = ["ctrader_H1", "ctrader_H4", "crypto_H1", "crypto_H4"]
ROOT = "experiments/SPDR-024/results/analysis"
BASE = "FIXED_SIZE_UNIT"
N_BOOT = 2000
N_SEEDS = 3
DOM_NS = {"H1": 3_600_000_000_000, "H4": 14_400_000_000_000}


def paired(d: pl.DataFrame, arm: str, cell: str) -> pl.DataFrame:
    b = d.filter((pl.col("arm_id") == BASE) & pl.col("exit_ts").is_not_null()).select(
        ["origin_id", "symbol", "entry_ts", "regime_state", "regime_episode_id",
         "outcome_bps", "capital_normalised_return_bps", "risk_size"])
    a = d.filter((pl.col("arm_id") == arm) & pl.col("exit_ts").is_not_null()).select(
        ["origin_id", "outcome_bps", "capital_normalised_return_bps", "risk_size"])
    j = b.join(a, on="origin_id", suffix="_a").with_columns(
        (pl.col("capital_normalised_return_bps_a") - pl.col("capital_normalised_return_bps")).alias("delta"),
        (pl.col("outcome_bps_a") - pl.col("outcome_bps")).alias("delta_bps"),
    ).sort(["symbol", "entry_ts"])
    dom = DOM_NS[cell.split("_")[1]]
    j = j.with_columns(
        (pl.col("entry_ts").dt.epoch("ns") // (24 * dom)).alias("tblock"))
    return j


from da_boot import two_stage_boot_mean  # noqa: E402


def cluster_boot(j: pl.DataFrame, block_col: str | None, seed: int, n_boot: int,
                 col: str = "z") -> np.ndarray:
    z = j[col].to_numpy()
    _, sym = np.unique(j["symbol"].to_numpy(), return_inverse=True)
    if block_col is None:
        blk = np.arange(len(z))
    else:
        _, blk = np.unique(j[block_col].to_numpy(), return_inverse=True)
    return two_stage_boot_mean(z, sym, blk, n_boot=n_boot, seed=seed)


def n_blocks(j: pl.DataFrame, block_col: str | None) -> int:
    if block_col is None:
        return j.height
    return j.select(pl.struct(["symbol", block_col]).n_unique()).item()


def band(est: float, lo: float, hi: float, mde: float, n_trades: int) -> str:
    if n_trades < 30:
        return "UNPOWERED"
    if abs(est) >= mde and ((lo > 0 and est > 0) or (hi < 0 and est < 0)):
        return "SUPPORTED" if est > 0 else "CONTRADICTED"
    if abs(est) < mde and lo <= 0 <= hi:
        return "WASH"
    if est <= -mde and hi < 0:
        return "CONTRADICTED"
    return "INDETERMINATE"


rows = []
persym_rows = []
for cell in CELLS:
    d = pl.read_parquet(f"{ROOT}/{cell}/episodes.parquet")
    arms = (d.filter((pl.col("arm_class") == "MANAGEMENT") & (pl.col("device") == "SIZE"))
            ["arm_id"].unique().sort().to_list())
    for arm in arms:
        j = paired(d, arm, cell)
        sig = j.group_by("symbol").agg(pl.col("delta").std().alias("sg"))
        j = j.join(sig, on="symbol").with_columns(
            pl.when(pl.col("sg") > 0).then(pl.col("delta") / pl.col("sg")).otherwise(0.0).alias("z"))
        comp = d.filter(pl.col("arm_id") == arm)["component"][0]
        setting = d.filter(pl.col("arm_id") == arm)["setting"][0]
        est = float(j["z"].mean())
        rec = {"cell": cell, "arm": arm, "component": comp, "setting": setting,
               "n_paired": j.height,
               "mean_delta_bps": float(j["delta"].mean()),
               "median_delta_bps": float(j["delta"].median()),
               "exact_zero_delta_share_primary": float(np.mean(j["delta"].to_numpy() == 0)),
               "exact_zero_delta_share_pernotional": float(np.mean(j["delta_bps"].to_numpy() == 0)),
               "risk_size_mean": float(j["risk_size_a"].mean()),
               "risk_size_min": float(j["risk_size_a"].min()),
               "risk_size_max": float(j["risk_size_a"].max()),
               "risk_size_n_unique": int(j["risk_size_a"].n_unique()),
               "estimate_sigma": est}
        for name, bc in [("V_A", None), ("V_B", "tblock"), ("V_C", "regime_episode_id")]:
            los, his = [], []
            for s in range(N_SEEDS):
                st = cluster_boot(j, bc, 1000 + s, N_BOOT)
                los.append(np.quantile(st, 0.025))
                his.append(np.quantile(st, 0.975))
            nb = n_blocks(j, bc)
            mde = 2.8 / np.sqrt(nb)
            lo, hi = float(np.median(los)), float(np.median(his))
            rec[f"{name}_ci_low"] = lo
            rec[f"{name}_ci_high"] = hi
            rec[f"{name}_ci_low_seed_range"] = [float(min(los)), float(max(los))]
            rec[f"{name}_blocks"] = nb
            rec[f"{name}_mde"] = float(mde)
            rec[f"{name}_band"] = band(est, lo, hi, mde, j.height)
            rec[f"{name}_width"] = hi - lo
        # governing = widest CI AND largest MDE, conservative on both
        gov = max(["V_A", "V_B", "V_C"], key=lambda t: rec[f"{t}_width"])
        govm = max(["V_A", "V_B", "V_C"], key=lambda t: rec[f"{t}_mde"])
        rec["governing_treatment_widestCI"] = gov
        rec["governing_treatment_largestMDE"] = govm
        rec["governing_band_widestCI"] = rec[f"{gov}_band"]
        # strictest possible: widest CI bounds x largest MDE
        wlo = min(rec[f"{t}_ci_low"] for t in ["V_A", "V_B", "V_C"])
        whi = max(rec[f"{t}_ci_high"] for t in ["V_A", "V_B", "V_C"])
        wmde = max(rec[f"{t}_mde"] for t in ["V_A", "V_B", "V_C"])
        rec["strict_band"] = band(est, wlo, whi, wmde, j.height)
        rec["strict_ci"] = [wlo, whi]
        rec["strict_mde"] = wmde
        rows.append(rec)
        # per symbol
        for sym, g in j.group_by("symbol"):
            persym_rows.append({"cell": cell, "arm": arm, "component": comp, "setting": setting,
                                "symbol": sym[0], "n": g.height,
                                "mean_delta_bps": float(g["delta"].mean()),
                                "estimate_sigma": float(g["z"].mean()),
                                "mde_VA": float(2.8 / np.sqrt(g.height))})
        print(f"{cell} {arm} done", file=sys.stderr)

pl.DataFrame(rows).write_parquet("/tmp/da_scale.parquet") if False else None
json.dump(rows, open(sys.argv[1], "w"), indent=1)
json.dump(persym_rows, open(sys.argv[2], "w"), indent=1)
