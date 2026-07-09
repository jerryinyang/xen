import numpy as np, polars as pl
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

EXP = Path(__file__).resolve().parents[1]
RES, PLT = EXP / "results", EXP / "plots"
PLT.mkdir(exist_ok=True)
d = pl.read_parquet(RES / "rederived_cells.parquet")
htf = d.filter((pl.col("variant") != "none") & (pl.col("n") > 0))

# --- robustness of the CI-excluding-zero lift cells ---
sig = htf.filter((pl.col("lift_ci_lo") > 0) | (pl.col("lift_ci_hi") < 0))
sig = sig.with_columns([pl.col("ci_lo_seedrange").list.get(0).alias("sr0"),
                        pl.col("ci_lo_seedrange").list.get(1).alias("sr1")])
print("CI-excl-zero lift cells:", sig.height)
print("  of which block_frag=True:", int(sig["block_frag"].sum()))
print("  admit_frac>0.95 (degenerate):", sig.filter(pl.col("baseline_admit_frac")>0.95).height)
n_pos = htf.filter(pl.col("lift_ci_lo")>0).height
n_neg = htf.filter(pl.col("lift_ci_hi")<0).height
print(f"positive-lift CI>0: {n_pos}  adverse CI<0: {n_neg}  total lift cells: {htf.height}")
print(f"observed CI-excl-zero rate: {(n_pos+n_neg)/htf.height:.3f} (chance ~0.05 two-sided)")

# binomial-ish: are pos and neg balanced (noise) vs skewed (systematic)?
print(f"pos/neg balance: {n_pos}/{n_neg}")

# --- Control B per variant family: momentum percentile in random-timing battery ---
b = htf.with_columns(pl.col("variant").str.contains("di").alias("is_di"))
print("\nControl B by DI:")
print(b.group_by("is_di").agg(pl.col("mom_pctile_in_twin").median().alias("med_pctile"),
      (pl.col("mom_pctile_in_twin")>0.975).mean().alias("frac_beat_p975"), pl.len()).to_pandas().to_string())

# ---- FIGURES ----
# 1. baseline horizon curves per stratum
hz = pl.read_parquet(RES / "horizon.parquet")
fig, ax = plt.subplots(figsize=(9,5))
for (ins, dom), g in hz.group_by(["instrument","domain"]):
    g = g.sort("hold_mult")
    ax.plot(g["hold_mult"], g["mean_atr"], marker="o", label=f"{ins} {dom}", alpha=.7)
ax.axhline(0, color="k", lw=.8)
ax.set_xlabel("hold multiple"); ax.set_ylabel("mean ATR-norm fwd return")
ax.set_title("Unfiltered momentum: mean forward return vs hold (per stratum)")
ax.legend(fontsize=7, ncol=2); fig.tight_layout(); fig.savefig(PLT/"horizon_baseline.png", dpi=110)

# 2. lift distribution with CI-excl-zero highlighted
fig, ax = plt.subplots(figsize=(8,5))
lift = htf.filter(pl.col("lift").is_not_null())
col = np.where((lift["lift_ci_lo"]>0).to_numpy(),"tab:green",
      np.where((lift["lift_ci_hi"]<0).to_numpy(),"tab:red","0.7"))
ax.scatter(lift["baseline_admit_frac"], lift["lift"], c=col, s=10, alpha=.6)
ax.axhline(0,color="k",lw=.8)
ax.set_xlabel("baseline_admit_frac (degeneracy axis)"); ax.set_ylabel("HTF-filter lift (ATR units)")
ax.set_title("HTF-filter lift vs baseline (green=CI>0, red=CI<0, grey=wash)")
fig.tight_layout(); fig.savefig(PLT/"lift_scatter.png", dpi=110)

# 3. Control B histogram
fig, ax = plt.subplots(figsize=(8,4))
ax.hist(htf["mom_pctile_in_twin"].to_numpy(), bins=30, color="tab:blue", alpha=.8)
ax.axvline(0.975,color="r",ls="--",label="p97.5 (beat-random)")
ax.axvline(0.5,color="k",ls=":")
ax.set_xlabel("momentum mean percentile within 25-seed random-timing battery")
ax.set_ylabel("cells"); ax.set_title("Control B: momentum timing vs matched-random timing")
ax.legend(); fig.tight_layout(); fig.savefig(PLT/"controlB_percentile.png", dpi=110)

# 4. dose-response absdisp vs atr_pct (normaliser guard)
dose = pl.read_parquet(RES/"dose_response.parquet")
fig, ax = plt.subplots(figsize=(8,4))
for cond,c in [("adx","tab:orange"),("atr_pct","tab:purple")]:
    v = dose.filter(pl.col("cond")==cond)["rho_absdisp"].to_numpy()
    ax.hist(v, bins=20, alpha=.6, label=cond, color=c)
ax.axvline(0,color="k"); ax.set_xlabel("Spearman rho(conditioner, |ATR-norm return|)")
ax.set_ylabel("cells"); ax.set_title("Dose-response dispersion (normaliser-guard: atr_pct sign)")
ax.legend(); fig.tight_layout(); fig.savefig(PLT/"dose_absdisp.png", dpi=110)
print("\nplots written to", PLT)
