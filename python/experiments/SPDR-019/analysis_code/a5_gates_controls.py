"""A5 — gate discrimination, controls, selection check, cost disclosure."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, polars as pl

RES = Path(__file__).resolve().parents[1] / "results"
pl.Config.set_tbl_rows(60); pl.Config.set_tbl_width_chars(250)
met = pl.read_parquet(RES / "metrics_by_cell.parquet")

print("=" * 96); print("A. GATE DISCRIMINATION — does each layer actually SELECT, or is it inert?"); print("=" * 96)
l0 = met.filter(pl.col("variant_id") == "L0_BASELINE").select(
    ["clock", "delta", "scope", "band", pl.col("n").alias("n_L0"), pl.col("log_R").alias("logR_L0")])
for v in ("L1_SHAT_DECILE_GE5", "L1_SHAT_DECILE_GE9", "L2_SHOCK_HMM", "L2_LEVEL_RMARKOV_K4",
          "L2_LEVEL_RMARKOV_K12", "L2_JOINT_HMM_HIGH_AND_K12_HIGH", "L3_TGTCUR_FIRES"):
    s = met.filter(pl.col("variant_id") == v).join(l0, on=["clock", "delta", "scope", "band"], how="inner")
    s = s.with_columns((pl.col("n") / pl.col("n_L0")).alias("keep_frac"))
    ident = s.filter((pl.col("n") == pl.col("n_L0")))
    print(f"{v:<34} rows={s.height:<5} keep_frac med={s['keep_frac'].median():.3f} "
          f"min={s['keep_frac'].min():.3f} max={s['keep_frac'].max():.3f} | INERT (keeps 100%): {ident.height} rows "
          f"({100*ident.height/max(1,s.height):.1f}%)")

print("\n--- interaction rows that are structurally ZERO (gate inert => no interaction exists) ---")
it = met.filter(pl.col("variant_id") == "L2_INTERACTION_HMM_X_K12")
print(f"total interaction rows {it.height}; ci_width==0 (exact cancellation) {it.filter(pl.col('ci_width')==0).height}; "
      f"log_R==0 exactly {it.filter(pl.col('log_R')==0).height}")

print("\n" + "=" * 96); print("B. CONTROLS (results/controls.json)"); print("=" * 96)
ctl = json.load(open(RES / "controls.json"))
def walk(o, d=0, k=""):
    if isinstance(o, dict):
        ks = list(o.keys())
        print("  " * d + f"{k}: dict[{len(ks)}] {ks[:8]}")
        if d < 1:
            for kk in ks[:4]:
                walk(o[kk], d + 1, kk)
    elif isinstance(o, list):
        print("  " * d + f"{k}: list[{len(o)}]")
        if o and d < 2:
            walk(o[0], d + 1, k + "[0]")
    else:
        print("  " * d + f"{k}: {str(o)[:90]}")
walk(ctl, 0, "root")
