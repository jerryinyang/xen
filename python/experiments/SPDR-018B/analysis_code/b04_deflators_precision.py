"""Verify the two deflators, the precision target, and the selection artifact on the powered subset."""
import json
import numpy as np
import pandas as pd

R = "python/experiments/SPDR-018B/results/"
m = pd.read_parquet(R + "metrics_by_cell.parquet")
defl = json.load(open(R + "deflators.json"))
up = json.load(open(R + "unit_pin.json"))
tgt = m["at_parent_target_precision"].fillna(False).astype(bool)
sup = m["at_parent_target_precision_absolute__SUPERSEDED"].fillna(0).astype(bool)
signed = m["gross_p"].notna()

print("=== precision deflator ===")
print("  claimed 0.17854965954623905; 13.034237315995593/73.001 =", 13.034237315995593 / 73.001)
print("  emitted sigma_target_deflator uniq:", m.sigma_target_deflator.unique())
print("  10 bps * deflator =", 10 * 0.17854965954623905, " emitted sigma target uniq:",
      m.target_mde_bps_sigma_scaled.dropna().unique())
print("\n  superseded absolute target x sigma-scaled target crosstab (signed cells):")
print(pd.crosstab(m.loc[signed, "target_mde_bps_absolute__SUPERSEDED"],
                  m.loc[signed, "target_mde_bps_sigma_scaled"], dropna=False).to_string())
print("\n  precision_basis x arm (signed):")
print(pd.crosstab(m.loc[signed, "arm"], m.loc[signed, "precision_basis"]).to_string())

print("\n=== is the target flag reproducible from block_mde? ===")
s = m[signed].copy()
mde = s["gross_block_mde_mean_bps"]
print("  gross_block_mde_mean_bps notnull:", mde.notna().sum(), "median", mde.median())
recomputed = mde <= s["target_mde_bps_sigma_scaled"]
print("  mde<=1.7855 count:", int(recomputed.sum()), " emitted at_target count:", int(tgt[signed].sum()),
      " agreement:", (recomputed == tgt[signed]).mean())
rec_abs = mde <= s["target_mde_bps_absolute__SUPERSEDED"]
print("  mde<=absolute count:", int(rec_abs.sum()), " emitted superseded count:", int(sup[signed].sum()),
      " agreement:", (rec_abs == sup[signed]).mean())
print("  MDE quantiles on signed cells:", np.round(mde.quantile([.05, .25, .5, .75, .95]).values, 3))
print("  MDE = 2.8*sigma/sqrt(n)? median implied sigma from mde*sqrt(n)/2.8:",
      (mde * np.sqrt(s.gross_n) / 2.8).median())

print("\n=== cost deflator: per-arm payoff scale, re-derived ===")
for arm in ["B", "C"]:
    d = m[signed & (m.arm == arm)]
    scale = (d.gross_W + d.gross_L).median()
    print(f"  arm {arm}: my median(W+L) = {scale:.4f}  |  deflators.json ctrader = "
          f"{defl['cost_deflator']['per_arm'][arm]['ctrader_payoff_scale_bps']:.4f}  "
          f"ratio claimed {defl['cost_deflator']['per_arm'][arm]['ratio']:.6f}")
    print(f"      implied crypto scale = {defl['cost_deflator']['per_arm'][arm]['crypto_payoff_scale_bps']:.2f}"
          f"  -> my ratio = {scale/defl['cost_deflator']['per_arm'][arm]['crypto_payoff_scale_bps']:.6f}")
print("  cost charged per arm (median gross_cost_bps):")
print(m[signed].groupby("arm").gross_cost_bps.describe()[["count", "min", "50%", "max"]].to_string())
print("  13.5 * 0.261 =", 13.5 * 0.26114175183386523, " 13.5 * 0.3118 =", 13.5 * 0.31183168078605744,
      " 13.5*0.17855 =", 13.5 * 0.17854965954623905)

print("\n=== NET-CLEARING at the UNSCALED borrowed floor (14 bps raw) ===")
pw = m[signed & tgt].copy()
for label, mult in [("vol-scaled (as emitted)", 1.0), ("unscaled borrowed", None)]:
    if mult is None:
        # reverse the per-arm deflator to get the unscaled cost
        r = pw.arm.map({"B": 0.26114175183386523, "C": 0.31183168078605744}).fillna(0.28648671630996136)
        cost = pw.gross_cost_bps / r
    else:
        cost = pw.gross_cost_bps
    pbe_net = (pw.gross_L + cost) / (pw.gross_W + pw.gross_L)
    print(f"  {label}: median cost {cost.median():.3f} bps, clears net "
          f"{int((pw.gross_p > pbe_net).sum())}/{len(pw)}")

print("\n=== SELECTION-ARTIFACT CHECK: powered subset vs excluded population ===")
print("  payoff scale (W+L) median: powered", (pw.gross_W + pw.gross_L).median(),
      " unpowered signed", (m[signed & ~tgt].gross_W + m[signed & ~tgt].gross_L).median())
print("  gross_mean median: powered %.3f, unpowered signed %.3f" %
      (pw.gross_mean.median(), m[signed & ~tgt].gross_mean.median()))

# arm B, exit_mode strata
b = m[signed & (m.arm == "B")].copy()
b["pwr"] = tgt[b.index]
print("\n  arm B by exit_mode:")
g = b.groupby("exit_mode").apply(lambda d: pd.Series({
    "n": len(d), "powered": int(d.pwr.sum()),
    "gross_pwr": d.loc[d.pwr, "gross_mean"].mean() if d.pwr.any() else np.nan,
    "gross_unpwr": d.loc[~d.pwr, "gross_mean"].mean() if (~d.pwr).any() else np.nan,
    "WL_pwr": d.loc[d.pwr, "gross_W_L"].median() if d.pwr.any() else np.nan,
    "p_pwr": d.loc[d.pwr, "gross_p"].median() if d.pwr.any() else np.nan,
    "payoff_pwr": (d.loc[d.pwr, "gross_W"] + d.loc[d.pwr, "gross_L"]).median() if d.pwr.any() else np.nan,
    "payoff_unpwr": (d.loc[~d.pwr, "gross_W"] + d.loc[~d.pwr, "gross_L"]).median() if (~d.pwr).any() else np.nan,
}), include_groups=False)
print(g.to_string())

tr = b[b.exit_mode == "trail"]
print("\n  === the arm-B `trail` claim (10 powered at +7..+23 vs 116 excluded at -27.6) ===")
print("   trail cells:", len(tr), " powered:", int(tr.pwr.sum()), " excluded:", int((~tr.pwr).sum()))
print("   powered trail gross_mean:", np.round(np.sort(tr.loc[tr.pwr, "gross_mean"].values), 2))
print("   powered trail mean of means: %.3f  median: %.3f" %
      (tr.loc[tr.pwr, "gross_mean"].mean(), tr.loc[tr.pwr, "gross_mean"].median()))
print("   excluded trail mean of means: %.3f  median: %.3f  n=%d" %
      (tr.loc[~tr.pwr, "gross_mean"].mean(), tr.loc[~tr.pwr, "gross_mean"].median(), int((~tr.pwr).sum())))
print("   ALL trail cells mean of means: %.3f" % tr.gross_mean.mean())
print("   powered trail: median n=%.0f, median W=%.2f L=%.2f W/L=%.3f p=%.4f, payoff scale=%.2f" %
      (tr.loc[tr.pwr, "gross_n"].median(), tr.loc[tr.pwr, "gross_W"].median(), tr.loc[tr.pwr, "gross_L"].median(),
       tr.loc[tr.pwr, "gross_W_L"].median(), tr.loc[tr.pwr, "gross_p"].median(),
       (tr.loc[tr.pwr, "gross_W"] + tr.loc[tr.pwr, "gross_L"]).median()))
print("   excluded trail: median n=%.0f, median W=%.2f L=%.2f, payoff scale=%.2f" %
      (tr.loc[~tr.pwr, "gross_n"].median(), tr.loc[~tr.pwr, "gross_W"].median(), tr.loc[~tr.pwr, "gross_L"].median(),
       (tr.loc[~tr.pwr, "gross_W"] + tr.loc[~tr.pwr, "gross_L"]).median()))
print("   powered trail CI_low>0 count:", int((tr.loc[tr.pwr, "gross_mean_ci_low"] > 0).sum()),
      "  of", int(tr.pwr.sum()))
print("   powered trail detail:")
cols = ["symbol", "band", "clock", "gross_n", "gross_p", "gross_W", "gross_L", "gross_W_L",
        "gross_mean", "gross_mean_ci_low", "gross_mean_ci_high", "gross_block_mde_mean_bps",
        "gross_cost_bps", "gross_p_be_net", "gross_edge"]
print(tr.loc[tr.pwr, cols].round(3).to_string())

print("\n  === does the dispersion gate select the sign? whole-grid check ===")
for arm in ["B", "C"]:
    d = m[signed & (m.arm == arm)].copy()
    d["pwr"] = tgt[d.index]
    print(f"   arm {arm}: powered mean-of-gross-means {d.loc[d.pwr,'gross_mean'].mean():+.3f} "
          f"vs excluded {d.loc[~d.pwr,'gross_mean'].mean():+.3f}; "
          f"powered share gross>0 {(d.loc[d.pwr,'gross_mean']>0).mean():.3f} "
          f"vs excluded {(d.loc[~d.pwr,'gross_mean']>0).mean():.3f}")
