"""Per-stratum magnitude table (no pooling, no verdict). stratum = instrument x domain x variant x hold.
Emits results/stratum_magnitudes.{parquet,csv,md}. Each row = the measured effect of HTF context
on the momentum outcome for ONE stratum, with uncertainty."""
import numpy as np, polars as pl
from pathlib import Path

RES = Path(__file__).resolve().parents[1] / "results"
d = pl.read_parquet(RES / "rederived_cells.parquet")

# baseline ('none') arm per instrument x domain x hold -> join onto every HTF arm
base = d.filter(pl.col("variant") == "none").select(
    ["instrument", "domain", "hold_bars",
     pl.col("mean_atr").alias("base_mean"), pl.col("std_atr").alias("base_std"),
     pl.col("hitrate").alias("base_hit"), pl.col("n").alias("base_n"),
     pl.col("ci_lo").alias("base_ci_lo"), pl.col("ci_hi").alias("base_ci_hi")])

POWER_FLOOR = 30   # block-bootstrap floor; below this a stratum is UNPOWERED (B-5), not a negative

t = (d.join(base, on=["instrument", "domain", "hold_bars"], how="left")
     .with_columns([
        (pl.col("std_atr") / pl.col("base_std")).alias("disp_ratio"),
        ((pl.col("hitrate") - pl.col("base_hit")) * 100).alias("dhit_pp"),
        (pl.col("n") < POWER_FLOOR).alias("unpowered"),
     ]))

cols = ["domain", "variant", "instrument", "hold_bars", "di", "n", "unpowered", "mde",
        "base_mean", "base_hit",
        "mean_atr", "hitrate", "lift", "lift_ci_lo", "lift_ci_hi",
        "disp_ratio", "dhit_pp", "mom_pctile_in_twin", "collapse_frac",
        "baseline_admit_frac", "block_frag"]
t = t.select(cols).sort(["domain", "variant", "instrument", "hold_bars"])

t.write_parquet(RES / "stratum_magnitudes.parquet")
r = t.with_columns([pl.col(c).round(4) for c in
                    ["mde","base_mean","base_hit","mean_atr","hitrate","lift","lift_ci_lo",
                     "lift_ci_hi","disp_ratio","dhit_pp","mom_pctile_in_twin","collapse_frac",
                     "baseline_admit_frac"]])
r.write_csv(RES / "stratum_magnitudes.csv")

# markdown render, grouped by domain -> variant, hold as columns per instrument line
def fmt(x, nd=2):
    return "" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{nd}f}"

lines = ["# SPDR-002 per-stratum magnitude table (no pooling, no verdict)",
         "",
         "stratum = instrument x domain x variant x hold. lift = filtered mean - unfiltered baseline "
         "mean (ATR units), CI = two-sample block bootstrap. disp = filtered/baseline std ratio. "
         "dhit = filtered - baseline hit-rate (pp). twinPct = momentum-arm mean percentile within the "
         "25-seed random-timing battery. collapse = Control-C phase-shift lift / raw lift (DI arms). "
         "U = UNPOWERED (n<30, B-5 — not a negative).",
         ""]
domains = ["1d/1h", "4h/1h", "1h/5min"]
for dom in domains:
    lines.append(f"\n## Domain {dom}\n")
    sub = t.filter(pl.col("domain") == dom)
    for var in sorted(sub["variant"].unique().to_list()):
        vv = sub.filter(pl.col("variant") == var)
        lines.append(f"\n### {var}\n")
        lines.append("| inst | hold | n | base_mean | arm_mean | lift | lift_CI | disp× | dhit_pp | twinPct | collapse | U |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for row in vv.sort(["instrument", "hold_bars"]).iter_rows(named=True):
            ci = f"[{fmt(row['lift_ci_lo'])},{fmt(row['lift_ci_hi'])}]" if row['lift'] is not None else ""
            lines.append("| {inst} | {h} | {n} | {bm} | {am} | {lf} | {ci} | {dr} | {dh} | {tp} | {cf} | {u} |".format(
                inst=row['instrument'], h=row['hold_bars'], n=row['n'],
                bm=fmt(row['base_mean']), am=fmt(row['mean_atr']), lf=fmt(row['lift']), ci=ci,
                dr=fmt(row['disp_ratio']), dh=fmt(row['dhit_pp'], 1),
                tp=fmt(row['mom_pctile_in_twin']), cf=fmt(row['collapse_frac']),
                u="U" if row['unpowered'] else ""))
Path(RES / "stratum_magnitudes.md").write_text("\n".join(lines))

# ---- surface strata whose LIFT CI is clear of zero AND powered (magnitudes, not a rate) ----
mat = t.filter((pl.col("lift_ci_lo") > 0) | (pl.col("lift_ci_hi") < 0)).filter(
    ~pl.col("unpowered") & (pl.col("baseline_admit_frac") < 0.95) & ~pl.col("block_frag"))
print("=== STRATA WITH LIFT CI CLEAR OF ZERO (powered, non-degenerate, block-robust) ===")
print(mat.select(["domain","variant","instrument","hold_bars","n","base_mean","mean_atr","lift",
                  "lift_ci_lo","lift_ci_hi","disp_ratio","dhit_pp","mom_pctile_in_twin",
                  "collapse_frac"]).sort("lift").to_pandas().to_string())
print("\ncount:", mat.height, " positive-lift:", mat.filter(pl.col('lift')>0).height,
      " negative-lift:", mat.filter(pl.col('lift')<0).height)
print("wrote stratum_magnitudes.{parquet,csv,md}")
