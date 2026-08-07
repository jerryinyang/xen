"""Q3 — is W/L a real movable degree of freedom, or the arithmetic mirror of p<0.5?

Test design (analyst's own, not the screen's):
  Identity: mean = p*W - (1-p)*L.  Define R = (p*W) / ((1-p)*L).
  mean = (1-p)*L*(R-1)  =>  R == 1  <=>  mean == 0.
  If the path is driftless with a fixed-horizon exit, R == 1 exactly and
      W/L == (1-p)/p
  i.e. W/L is FULLY determined by p — no free handle.
  So: (a) how much of log(W/L) variance is explained by log((1-p)/p)?
      (b) how far is R from 1, and is that distance distinguishable from 0 at the cell CIs?
      (c) does exit_mode (the actual capture-geometry lever, arm B) move W/L at MATCHED p?
          That is the only test that speaks to MOVABILITY rather than accounting.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen")
RES = ROOT / "python/experiments/SPDR-018/results"
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 60)

m = pd.read_parquet(RES / "metrics_by_cell.parquet")
a = m[(m["at_parent_target_precision"] == True) & (m["gross_p"].notna())].copy()
a = a[(a["gross_p"] > 0) & (a["gross_p"] < 1) & (a["gross_W"] > 0) & (a["gross_L"] > 0)]
print("powered signed cells used:", len(a))

a["logWL"] = np.log(a["gross_W"] / a["gross_L"])
a["logmirror"] = np.log((1 - a["gross_p"]) / a["gross_p"])
a["R"] = (a["gross_p"] * a["gross_W"]) / ((1 - a["gross_p"]) * a["gross_L"])
a["logR"] = np.log(a["R"])

print("\n--- (a) variance decomposition ---")
x, y = a["logmirror"].values, a["logWL"].values
b1, b0 = np.polyfit(x, y, 1)
r = np.corrcoef(x, y)[0, 1]
print(f"OLS log(W/L) = {b0:+.4f} + {b1:+.4f}*log((1-p)/p)   r={r:.4f}  R2={r ** 2:.4f}")
print("  (driftless mirror predicts intercept 0, slope 1, R2 1)")
print(f"sd log(W/L)          = {y.std():.4f}")
print(f"sd log((1-p)/p)      = {x.std():.4f}")
print(f"sd residual log(R)   = {a['logR'].std():.4f}   <- the FREE component")
print(f"free share of W/L variation (sd ratio) = {a['logR'].std() / y.std():.4f}")

print("\n--- (b) how far is R from 1 (i.e. mean from 0) ---")
print(a["R"].describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]).to_string())
print("frac cells with |log R| < 0.05 (mean within ~5% of zero-line):",
      (a["logR"].abs() < 0.05).mean().round(4))
print("median |gross_mean| bps:", a["gross_mean"].abs().median().round(3),
      " median W:", a["gross_W"].median().round(1), " -> |mean|/W =",
      (a["gross_mean"].abs().median() / a["gross_W"].median()).round(4))

# is the mean distinguishable from zero per cell?
mean_sig = ((a["gross_mean_ci_low"] > 0) | (a["gross_mean_ci_high"] < 0))
print("cells whose gross-mean block CI excludes zero:", int(mean_sig.sum()), "/", len(a),
      f"= {mean_sig.mean():.4f}")
print("  of those, sign: pos", int((a.loc[mean_sig, 'gross_mean'] > 0).sum()),
      " neg", int((a.loc[mean_sig, 'gross_mean'] < 0).sum()))

print("\n--- (c) MOVABILITY: does exit_mode move W/L at matched p?  (arm B) ---")
B = a[(a["arm"] == "B") & a["exit_mode"].notna()]
print("arm B powered cells:", len(B))
g = B.groupby("exit_mode").agg(
    n_cells=("gross_p", "size"), p=("gross_p", "median"), W=("gross_W", "median"),
    L=("gross_L", "median"), WL=("gross_W_L", "median"), R=("R", "median"),
    mirror=("logmirror", lambda s: float(np.exp(np.median(s)))),
    mean_bps=("gross_mean", "median"), net_bps=("net_mean", "median"),
    n_ep=("gross_n", "median"))
g["WL_over_mirror"] = g["WL"] / g["mirror"]
print(g.round(4).to_string())

# residualised W/L: does exit_mode explain variance in log(R)?  (log R = logWL - logmirror)
print("\nlog(R) by exit_mode (the part of W/L NOT forced by p):")
print(B.groupby("exit_mode")["logR"].describe()[["count", "mean", "std", "50%"]].round(4).to_string())

# Same test on arm B ALL cells (not only powered) for breadth
Ball = m[(m["arm"] == "B") & m["gross_p"].notna() & (m["gross_p"] > 0) & (m["gross_p"] < 1)
         & (m["gross_W"] > 0) & (m["gross_L"] > 0)].copy()
Ball["logR"] = np.log((Ball["gross_p"] * Ball["gross_W"]) / ((1 - Ball["gross_p"]) * Ball["gross_L"]))
Ball["logWL"] = np.log(Ball["gross_W"] / Ball["gross_L"])
Ball["logmirror"] = np.log((1 - Ball["gross_p"]) / Ball["gross_p"])
print("\nALL arm-B signed cells (n=%d):" % len(Ball))
gg = Ball.groupby("exit_mode").agg(n=("logWL", "size"), WL=("gross_W_L", "median"),
                                   p=("gross_p", "median"), logR_med=("logR", "median"),
                                   gross_bps=("gross_mean", "median"))
print(gg.round(4).to_string())
r2 = np.corrcoef(Ball["logmirror"], Ball["logWL"])[0, 1] ** 2
print("R2 of mirror on all arm-B signed cells:", round(r2, 4))

print("\n--- (d) W/L CI width vs the mirror prediction, per cell ---")
a["mirror_WL"] = (1 - a["gross_p"]) / a["gross_p"]
inci = (a["gross_W_L_ci_low"] <= a["mirror_WL"]) & (a["mirror_WL"] <= a["gross_W_L_ci_high"])
print("cells whose W/L block-CI CONTAINS the driftless mirror value (1-p)/p:",
      int(inci.sum()), "/", int(a["gross_W_L_ci_low"].notna().sum()),
      f"= {inci.sum() / max(1, a['gross_W_L_ci_low'].notna().sum()):.4f}")
print("  -> a cell whose CI contains the mirror cannot be shown to have a free W/L handle at this n")

# whole-grid version
allsig = m[m["gross_p"].notna() & (m["gross_p"] > 0) & (m["gross_p"] < 1) &
           (m["gross_W"] > 0) & (m["gross_L"] > 0)].copy()
allsig["logR"] = np.log((allsig["gross_p"] * allsig["gross_W"]) /
                        ((1 - allsig["gross_p"]) * allsig["gross_L"]))
allsig["logWL"] = np.log(allsig["gross_W"] / allsig["gross_L"])
allsig["logmirror"] = np.log((1 - allsig["gross_p"]) / allsig["gross_p"])
print("\nWHOLE GRID (%d signed cells): R2 = %.4f, sd logWL=%.4f, sd logR=%.4f" % (
    len(allsig), np.corrcoef(allsig["logmirror"], allsig["logWL"])[0, 1] ** 2,
    allsig["logWL"].std(), allsig["logR"].std()))
for arm in ["B", "C"]:
    s = allsig[allsig.arm == arm]
    print("  arm %s: n=%d R2=%.4f sd_logWL=%.4f sd_logR=%.4f med_WL=%.3f" % (
        arm, len(s), np.corrcoef(s["logmirror"], s["logWL"])[0, 1] ** 2,
        s["logWL"].std(), s["logR"].std(), s["gross_W_L"].median()))
