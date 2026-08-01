"""SPDR-023 fresh-context analyst — X5: device outcomes rebuilt from the raw ledger.

Reconstructs, for every MANAGEMENT-class arm episode that actually traded, the realised
signed outcome in bps from the ledger's own FILLED and CLOSED price rows, then reports each
arm against BOTH available comparators on the SAME eligible origins:

  * fixed-device comparator  (the device's own fixed form, e.g. FIXED_TARGET_M1.00)
  * plain baseline           (FIXED_BASELINE_PLAIN - no target/stop/trail, 4-bar exit)

Gross of spread. Fees/funding are NOT recoverable from these two ledger rows, so this measure
is GROSS-OF-ALL-COST and is labelled as such; it is not the canonical cost-bearing figure.
Emitted per stratum with count, effective count, block-bootstrap CI and MDE. No verdict.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).parent))
from x2_native_paired import Z, block_ci_mean  # noqa: E402

ROOT = Path("/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen")
RUNS = {
    "ctrader": ROOT / "data/nautilus_runs/SPDR-023-ctrader-train-20260731T004708Z",
    "crypto": ROOT / "data/nautilus_runs/SPDR-023-crypto-train-20260731T004708Z",
}
OUT = ROOT / "python/experiments/SPDR-023/results/analyst"
PLAIN = "FIXED_BASELINE_PLAIN"


def episodes(universe: str) -> pl.DataFrame:
    R = RUNS[universe]
    er = pl.scan_parquet(R / "episode_results.parquet")
    meta = (pl.scan_parquet(R / "policy_schedule.parquet")
            .select("origin_id", "arm_id", "entry_variant", "symbol", "side", "device",
                    "setting", "component", "arm_class", "decision_ts")
            .unique(subset=["origin_id", "arm_id", "entry_variant"]))
    ent = (er.filter((pl.col("arm_class").str.contains("MANAGEMENT"))
                     & (pl.col("state") == "FILLED"))
           .select("origin_id", "arm_id", "entry_variant",
                   pl.col("price").alias("entry_px"), pl.col("ts_ns").alias("entry_ns")))
    ext = (er.filter((pl.col("arm_class").str.contains("MANAGEMENT"))
                     & (pl.col("state") == "CLOSED"))
           .select("origin_id", "arm_id", "entry_variant",
                   pl.col("price").alias("exit_px"), pl.col("ts_ns").alias("exit_ns"),
                   "exit_reason"))
    return (ent.join(ext, on=["origin_id", "arm_id", "entry_variant"], how="inner")
            .join(meta, on=["origin_id", "arm_id", "entry_variant"], how="left")
            .with_columns(
                outcome_bps=pl.col("side") * (pl.col("exit_px") - pl.col("entry_px"))
                / pl.col("entry_px") * 10000.0,
                duration_min=(pl.col("exit_ns") - pl.col("entry_ns")) / 6e10,
            ).collect())


def compare(g: pl.DataFrame, comp: pl.DataFrame, label: str) -> dict:
    """Paired comparison on the intersection of origins actually traded by both arms."""
    j = g.join(comp.select("origin_id", pl.col("outcome_bps").alias("c_bps")),
               on="origin_id", how="inner").sort("decision_ts")
    if j.height == 0:
        return {f"{label}_paired_n": 0, f"{label}_estimate_bps": float("nan"),
                f"{label}_ci_low": float("nan"), f"{label}_ci_high": float("nan"),
                f"{label}_effective_n": 0, f"{label}_mde_bps": float("nan"),
                f"{label}_availability": "UNAVAILABLE_NO_SHARED_TRADED_ORIGIN"}
    d = (j["outcome_bps"] - j["c_bps"]).to_numpy()
    r = block_ci_mean(d)
    sd = float(np.std(d, ddof=1)) if len(d) > 1 else float("nan")
    return {
        f"{label}_paired_n": int(len(d)),
        f"{label}_estimate_bps": r["stat"],
        f"{label}_median_bps": float(np.median(d)),
        f"{label}_ci_low": r["ci_low"], f"{label}_ci_high": r["ci_high"],
        f"{label}_ci_low_seed_min": r["ci_low_seed_min"],
        f"{label}_ci_low_seed_max": r["ci_low_seed_max"],
        f"{label}_ci_excludes_zero": bool(r["ci_low"] > 0 or r["ci_high"] < 0),
        f"{label}_effective_n": r["n_eff"],
        f"{label}_mde_bps": float(Z * sd / np.sqrt(r["n_eff"])) if r["n_eff"] else float("nan"),
        f"{label}_availability": "AVAILABLE",
    }


# device -> its fixed-device comparator arm_id
FIXED_FOR_DEVICE = {
    "TARGET": "FIXED_TARGET_M1.00", "STOP": "FIXED_STOP_M1.00",
    "TRAIL": "FIXED_TRAIL_M1.00", "HOLD": "FIXED_HOLD_B4", "SIZE": "FIXED_BASELINE_PLAIN",
}


def run(universe: str) -> None:
    o = OUT / universe
    o.mkdir(parents=True, exist_ok=True)
    ep = episodes(universe)
    print(universe, "traded management episodes:", ep.height)

    rows = []
    for (sym, var), blk in ep.group_by(["symbol", "entry_variant"], maintain_order=True):
        plain = blk.filter(pl.col("arm_id") == PLAIN)
        for arm, g in blk.group_by("arm_id", maintain_order=True):
            arm = arm[0]
            g = g.sort("decision_ts")
            dev = g["device"][0]
            fixed_id = FIXED_FOR_DEVICE.get(str(dev).split("+")[0], None)
            fixed = blk.filter(pl.col("arm_id") == fixed_id) if fixed_id else blk.head(0)
            x = g["outcome_bps"].to_numpy()
            r = block_ci_mean(x)
            sd = float(np.std(x, ddof=1)) if len(x) > 1 else float("nan")
            rec = dict(
                universe=universe, symbol=sym, entry_variant=var, arm_id=arm,
                arm_class=g["arm_class"][0], device=dev, setting=g["setting"][0],
                component=g["component"][0],
                traded_episodes=int(g.height),
                measure="realised_outcome_bps_gross_of_all_cost",
                observed_mean_bps=r["stat"], observed_median_bps=float(np.median(x)),
                obs_ci_low=r["ci_low"], obs_ci_high=r["ci_high"],
                obs_effective_n=r["n_eff"],
                obs_mde_bps=float(Z * sd / np.sqrt(r["n_eff"])) if r["n_eff"] else float("nan"),
                mean_duration_min=float(g["duration_min"].mean()),
                exit_target_share=float((g["exit_reason"] == "TARGET").mean()),
                exit_stop_share=float((g["exit_reason"] == "STOP").mean()),
                exit_trail_share=float((g["exit_reason"] == "TRAIL").mean()),
                exit_hold_share=float((g["exit_reason"] == "HOLD").mean()),
                fixed_device_comparator=fixed_id,
            )
            rec.update(compare(g, fixed, "vs_fixed_device") if fixed.height
                       else {"vs_fixed_device_paired_n": 0,
                             "vs_fixed_device_availability":
                                 "UNAVAILABLE_COMPARATOR_HAS_NO_TRADED_EPISODE"})
            rec.update(compare(g, plain, "vs_plain_baseline") if plain.height
                       else {"vs_plain_baseline_paired_n": 0,
                             "vs_plain_baseline_availability":
                                 "UNAVAILABLE_PLAIN_BASELINE_HAS_NO_TRADED_EPISODE"})
            rows.append(rec)
    out = pl.DataFrame(rows, infer_schema_length=None).sort(
        "symbol", "entry_variant", "device", "arm_id")
    out.write_parquet(o / "device_outcomes_both_comparators.parquet")
    out.write_csv(o / "device_outcomes_both_comparators.csv")
    print(universe, "device arm-strata", out.height)
    pl.Config.set_tbl_width_chars(280)
    print(out.group_by("device").agg(
        pl.len(), pl.col("traded_episodes").median().alias("median_traded"),
        (pl.col("vs_fixed_device_paired_n") > 0).sum().alias("fixed_cmp_available"),
        (pl.col("vs_plain_baseline_paired_n") > 0).sum().alias("plain_cmp_available"),
    ).sort("device"))


if __name__ == "__main__":
    for u in sys.argv[1:] or ["ctrader", "crypto"]:
        run(u)
