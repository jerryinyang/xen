"""Digest rederived emissions into the tables analysis.md quotes. Pure reads, no re-derivation."""
import json
from pathlib import Path
import numpy as np
import polars as pl

RES = Path(__file__).resolve().parents[1] / "results"
d = pl.read_parquet(RES / "rederived_cells.parquet")
dose = pl.read_parquet(RES / "dose_response.parquet")
hz = pl.read_parquet(RES / "horizon.parquet")

htf = d.filter(pl.col("variant") != "none")
print("=== SCOPE ===")
print("total cells", d.height, "htf cells", htf.height, "empty", d.filter(pl.col("n")==0).height)
print("median htf n", float(np.median(htf.filter(pl.col('n')>0)["n"].to_numpy())))

# power map
print("\n=== POWER (n distribution by variant family) ===")
d2 = d.filter(pl.col("n")>0)
print(d2.group_by("variant").agg(pl.col("n").median().alias("med_n"),
      pl.col("mde").median().alias("med_mde"), pl.len().alias("cells")).sort("med_n").to_pandas().to_string())

# baseline (unfiltered momentum) per stratum
print("\n=== UNFILTERED MOMENTUM BASELINE (mean_atr, ci, hitrate) per instrument x domain x hold ===")
base = d.filter(pl.col("variant")=="none").select(
    ["instrument","domain","hold_mult","n","mean_atr","ci_lo","ci_hi","hitrate","std_atr","skew","block_frag"])
print(base.to_pandas().to_string())
base_pos = base.filter((pl.col("ci_lo")>0)); base_neg = base.filter((pl.col("ci_hi")<0))
print("baseline cells CI>0:", base_pos.height, " CI<0:", base_neg.height, " of", base.height)

# lift: HTF filter over baseline
print("\n=== HTF-FILTER LIFT (filtered - unfiltered baseline), CI excludes zero ===")
lift = htf.filter(pl.col("n")>0)
lpos = lift.filter(pl.col("lift_ci_lo")>0)
lneg = lift.filter(pl.col("lift_ci_hi")<0)
print("lift cells:", lift.height, " CI_lo>0:", lpos.height, " CI_hi<0:", lneg.height)
print("-- degeneracy: admit_frac distribution --")
print(lift.select("baseline_admit_frac").describe())
print("-- lift CI>0 cells that are NOT degenerate (admit_frac<0.95) --")
print(lpos.filter(pl.col("baseline_admit_frac")<0.95).select(
    ["instrument","domain","variant","hold_mult","n","baseline_admit_frac","lift","lift_ci_lo","lift_ci_hi","di"]).to_pandas().to_string())
print("-- lift CI<0 (adverse) non-degenerate --")
print(lneg.filter(pl.col("baseline_admit_frac")<0.95).select(
    ["instrument","domain","variant","hold_mult","n","baseline_admit_frac","lift","lift_ci_lo","lift_ci_hi","di"]).to_pandas().to_string())

# DI confirmation specifically + Control C collapse
print("\n=== DI-CONFIRM ARMS: lift + phase-shift collapse ===")
di = htf.filter(pl.col("di") & (pl.col("n")>0))
print("di cells:", di.height, " lift CI_lo>0:", di.filter(pl.col('lift_ci_lo')>0).height,
      " lift CI_hi<0:", di.filter(pl.col('lift_ci_hi')<0).height)
if "collapse_frac" in di.columns:
    cc = di.filter(pl.col("lift_ci_lo")>0).select(
        ["instrument","domain","variant","hold_mult","lift","lift_ci_lo","phase_lift","collapse_frac","baseline_admit_frac"])
    print("-- DI cells with lift CI>0: does phase-shift collapse? --")
    print(cc.to_pandas().to_string())

# Control B: momentum vs random timing
print("\n=== CONTROL B: momentum percentile within 25-seed random-timing battery ===")
if "mom_pctile_in_twin" in htf.columns:
    b = htf.filter(pl.col("n")>0)
    print("frac cells with momentum mean > twin p97.5:",
          float((b["mom_pctile_in_twin"]>0.975).mean()),
          " > twin median:", float((b["mom_pctile_in_twin"]>0.5).mean()))
    print(b.select("mom_pctile_in_twin").describe())

# dispersion normaliser guard
print("\n=== DISPERSION NORMALISER GUARD (baseline arms, three reads) ===")
bz = d.filter(pl.col("variant")=="none").select(
    ["instrument","domain","hold_mult","std_atr","std_bps","std_flatr"])
print(bz.to_pandas().to_string())

# dose response
print("\n=== DOSE-RESPONSE (Spearman rho, unfiltered momentum) ===")
print(dose.group_by("cond").agg(
    pl.col("rho_mean").median().alias("med_rho_mean"),
    pl.col("rho_absdisp").median().alias("med_rho_absdisp"),
    pl.len()).to_pandas().to_string())
print("-- per (instrument,domain,cond) median over holds --")
print(dose.group_by(["instrument","domain","cond"]).agg(
    pl.col("rho_mean").median(), pl.col("rho_absdisp").median()).sort(["cond","instrument","domain"]).to_pandas().to_string())
# count dose CIs excluding zero
dd = dose.with_columns([pl.col("rho_mean_ci").list.get(0).alias("rm_lo"),
                        pl.col("rho_mean_ci").list.get(1).alias("rm_hi"),
                        pl.col("rho_absdisp_ci").list.get(0).alias("rd_lo"),
                        pl.col("rho_absdisp_ci").list.get(1).alias("rd_hi")])
print("dose rho_mean CI excl 0:", dd.filter((pl.col('rm_lo')>0)|(pl.col('rm_hi')<0)).height, "/", dd.height)
print("dose rho_absdisp CI excl 0:", dd.filter((pl.col('rd_lo')>0)|(pl.col('rd_hi')<0)).height, "/", dd.height)
print("  absdisp POSITIVE (vol clustering) CI>0:", dd.filter(pl.col('rd_lo')>0).height,
      " vs adx-pct only:", dd.filter((pl.col('cond')=='atr_pct')&(pl.col('rd_lo')>0)).height)

# horizon curves
print("\n=== HORIZON (unfiltered momentum mean_atr by hold_mult, per instrument/domain) ===")
print(hz.pivot(values="mean_atr", index=["instrument","domain"], on="hold_mult").to_pandas().to_string())
print("-- hitrate --")
print(hz.pivot(values="hitrate", index=["instrument","domain"], on="hold_mult").to_pandas().to_string())

# heterogeneity of baseline mean across instruments (per domain, hold=1)
print("\n=== HETEROGENEITY: baseline mean_atr spread across instruments ===")
for dom in ["1d/1h","4h/1h","1h/5min"]:
    sub = base.filter(pl.col("domain")==dom)
    print(dom, "mean_atr range", round(sub["mean_atr"].min(),3), "->", round(sub["mean_atr"].max(),3),
          "hitrate range", round(sub["hitrate"].min(),3),"->",round(sub["hitrate"].max(),3))
