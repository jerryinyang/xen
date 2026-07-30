"""A2 — day-block (calendar-day) rule verification + row accounting + identity re-derivation."""
from __future__ import annotations
from pathlib import Path
import numpy as np, polars as pl

RES = Path(__file__).resolve().parents[1] / "results"
NS = 1_000_000_000
DAY = 86400 * NS

met = pl.read_parquet(RES / "metrics_by_cell.parquet")
ep = pl.scan_parquet(RES / "episodes.parquet")

# ---- 3a. n_dates independently recomputed from episode EXIT dates, TRAIN band = both sub-bands
probe_v = ["L0_BASELINE", "L4_HOLD_20H_UNMOD", "L1_SHAT_DECILE_GE9", "L4_TARGET_A2_MOD"]
eps = (
    ep.filter(pl.col("variant_id").is_in(probe_v))
    .with_columns((pl.col("exit_ts") // DAY).alias("d_exit"), (pl.col("fill_ts") // DAY).alias("d_fill"))
    .group_by(["variant_id", "clock", "delta"])
    .agg(pl.len().alias("n_ep"), pl.col("d_exit").n_unique().alias("days_exit"),
         pl.col("d_fill").n_unique().alias("days_fill"))
    .collect()
)
probe = met.filter((pl.col("scope") == "POOLED") & (pl.col("band") == "TRAIN")
                   & pl.col("variant_id").is_in(probe_v)).select(
    ["variant_id", "clock", "delta", "n", "n_dates", "n_days", "effective_block_cap"])
j = probe.join(eps, on=["variant_id", "clock", "delta"], how="left").with_columns(
    (pl.col("n_dates") - pl.col("days_exit")).alias("nd_minus_days_exit"),
    (pl.col("n_dates") - pl.col("days_fill")).alias("nd_minus_days_fill"))
print("=== n_dates vs independently counted UTC calendar days (pooled TRAIN) ===")
with pl.Config(tbl_rows=60, tbl_width_chars=220):
    print(j.sort(["variant_id", "clock", "delta"]))

# ---- 3b. is n_dates CLOCK-INVARIANT in the way a calendar rule implies?
inv = (met.filter((pl.col("scope") == "POOLED") & (pl.col("band") == "TRAIN"))
       .pivot(on="clock", index=["variant_id", "delta"], values="n_dates")
       .with_columns((pl.col("M15") - pl.col("H1")).alias("d"))
       )
print("\n=== n_dates M15 vs H1 (pooled TRAIN): a CALENDAR rule keeps these close; a BAR rule would not ===")
print(inv.select(pl.col("d").min().alias("min"), pl.col("d").median().alias("med"),
                 pl.col("d").max().alias("max"), pl.col("H1").median().alias("H1_med"),
                 pl.col("M15").median().alias("M15_med")))

# ---- 3c. block sweep actually {1,3,7} days on M15 too
pb = met.filter((pl.col("scope") == "POOLED") & (pl.col("band") == "TRAIN")
                & (pl.col("variant_id") == "L0_BASELINE")).select(
    ["clock", "delta", "n", "n_dates", "per_block_ci", "per_seed_ci", "ci_low", "ci_high", "block_mde"])
print("\n=== per-block / per-seed CI structure, L0 pooled TRAIN ===")
for r in pb.iter_rows(named=True):
    print(r["clock"], r["delta"], "n_dates=", r["n_dates"], "ci=", round(r["ci_low"],5), round(r["ci_high"],5))
    print("   per_block:", r["per_block_ci"])
    print("   per_seed :", str(r["per_seed_ci"])[:400])

# ---- 4. Row accounting: the four buckets
b_ci = met.filter(pl.col("ci_low").is_not_null() & pl.col("ci_high").is_not_null())
b_exempt = met.filter(pl.col("ci_absent_reason").is_not_null())
b_sizing = met.filter(pl.col("sizing_no_logR_claim") == True)  # noqa: E712
print("\n=== ROW ACCOUNTING ===")
print("total rows            :", met.height)
print("carries a CI          :", b_ci.height)
print("ci_absent_reason set  :", b_exempt.height, b_exempt["ci_absent_reason"].value_counts().to_dicts())
print("sizing_no_logR_claim  :", b_sizing.height)
print("log_R null            :", met.filter(pl.col("log_R").is_null()).height)
print("overlap ci&exempt     :", met.filter(pl.col("ci_low").is_not_null() & pl.col("ci_absent_reason").is_not_null()).height)
print("overlap ci&sizing     :", met.filter(pl.col("ci_low").is_not_null() & (pl.col("sizing_no_logR_claim") == True)).height)  # noqa: E712
unclass = met.filter(pl.col("ci_low").is_null() & pl.col("ci_absent_reason").is_null()
                     & (pl.col("sizing_no_logR_claim") != True))  # noqa: E712
print("UNCLASSIFIED          :", unclass.height)

# validate exempt reasons against the cell's OWN p,W,L,n,n_dates (never against log_R)
ex = b_exempt.select(["variant_id","clock","delta","scope","band","ci_absent_reason","p","W","L","n","n_dates"])
defined = ((pl.col("p").is_not_null()) & (pl.col("W").is_not_null()) & (pl.col("L").is_not_null())
           & (pl.col("p") > 0) & (pl.col("p") < 1) & (pl.col("W") > 0) & (pl.col("L") > 0))
ex = ex.with_columns(defined.alias("logR_defined"))
print("\n=== EXEMPT CELLS validated on their own p,W,L,n,n_dates ===")
with pl.Config(tbl_rows=60, tbl_width_chars=240):
    print(ex.sort(["ci_absent_reason","n_dates"]))

# ---- 5. Identity re-derivation, independent
sc = met.filter(pl.col("log_R").is_not_null() & pl.col("p").is_not_null())
sc = sc.with_columns(
    (pl.col("p")*pl.col("W") - (1-pl.col("p"))*pl.col("L") - pl.col("mean")).abs().alias("id_res"),
    ((pl.col("W")/pl.col("L")).log() - ((1-pl.col("p"))/pl.col("p")).log() - pl.col("log_R")).abs().alias("logr_res"),
)
print("\n=== IDENTITY / log R DEFINITION re-derived by me ===")
print("cells checked:", sc.height,
      "max |p*W-(1-p)*L-mean| bps:", sc["id_res"].max(),
      "max |log(W/L)-log((1-p)/p) - log_R|:", sc["logr_res"].max())
print("rows with log_R but no ci_low:", met.filter(pl.col("log_R").is_not_null() & pl.col("ci_low").is_null()).height)
