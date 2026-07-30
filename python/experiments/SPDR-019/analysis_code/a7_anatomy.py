"""A7 — episode anatomy, concentration, occupancy, per-year stability, cost sensitivity."""
from __future__ import annotations
from pathlib import Path
import numpy as np, polars as pl

RES = Path(__file__).resolve().parents[1] / "results"
NS = 1_000_000_000
pl.Config.set_tbl_rows(40); pl.Config.set_tbl_width_chars(230); pl.Config.set_fmt_float("mixed")
ep = pl.scan_parquet(RES / "episodes.parquet")
L0 = ep.filter((pl.col("variant_id") == "L0_BASELINE") & (pl.col("delta") == 0.5))

print("=== per-episode r_bps distribution, L0 d=0.5 (the P&L-bearing object) ===")
print(L0.group_by("clock").agg(
    pl.len().alias("n"), pl.col("r_bps").mean().alias("mean"), pl.col("r_bps").median().alias("median"),
    pl.col("r_bps").std().alias("sd"), pl.col("r_bps").quantile(0.01).alias("q01"),
    pl.col("r_bps").quantile(0.05).alias("q05"), pl.col("r_bps").quantile(0.95).alias("q95"),
    pl.col("r_bps").quantile(0.99).alias("q99"), (pl.col("r_bps") == 0).mean().alias("frac_flat")).collect())

print("\n=== CONCENTRATION: does log R survive removing the top winners? (pooled, per clock) ===")
for clk in ("M15", "H1"):
    d = L0.filter(pl.col("clock") == clk).select("r_bps").collect()["r_bps"].to_numpy()
    d = d[np.isfinite(d)]
    def logR(x):
        pos, neg = x[x > 0], x[x < 0]
        if not len(pos) or not len(neg):
            return np.nan
        p = len(pos) / (len(pos) + len(neg)); W = pos.mean(); L = -neg.mean()
        return np.log(W / L) - np.log((1 - p) / p)
    order = np.argsort(-d)
    print(f"  {clk}: full log R={logR(d):+.5f}", end="")
    for k in (1, 3, 5, 10, 50):
        print(f" | drop top {k}: {logR(np.delete(d, order[:k])):+.5f}", end="")
    print()

print("\n=== OCCUPANCY: fraction of calendar time with an open episode (L0 d=0.5, per symbol) ===")
occ = (L0.with_columns((pl.col("exit_ts") - pl.col("fill_ts")).alias("dur"))
       .group_by(["clock", "symbol"]).agg(pl.col("dur").sum().alias("in_mkt_ns"),
                                          pl.col("fill_ts").min().alias("t0"), pl.col("exit_ts").max().alias("t1"),
                                          pl.len().alias("n"))
       .with_columns((pl.col("in_mkt_ns") / (pl.col("t1") - pl.col("t0"))).alias("occupancy")).collect())
print(occ.group_by("clock").agg(pl.col("occupancy").min().alias("min"), pl.col("occupancy").median().alias("med"),
                                pl.col("occupancy").max().alias("max")))

print("\n=== PER-YEAR STABILITY of L0 log R (regime artifact check) ===")
yr = (L0.with_columns((pl.col("fill_ts") // (NS)).cast(pl.Int64).alias("s"))
      .with_columns(pl.from_epoch(pl.col("s"), time_unit="s").dt.year().alias("year"))
      .select(["clock", "year", "r_bps"]).collect())
rows = []
for (clk, y), g in yr.group_by(["clock", "year"]):
    x = g["r_bps"].to_numpy(); pos, neg = x[x > 0], x[x < 0]
    if not len(pos) or not len(neg):
        continue
    p = len(pos) / (len(pos) + len(neg)); W = pos.mean(); L = -neg.mean()
    rows.append({"clock": clk, "year": y, "n": len(x), "p": p, "W_L": W / L,
                 "log_R": float(np.log(W / L) - np.log((1 - p) / p)), "mean_bps": x.mean()})
print(pl.DataFrame(rows).sort(["clock", "year"]))

print("\n=== COST SENSITIVITY (DISCLOSURE ONLY — cost enters no estimand, AMENDMENT-C5) ===")
for clk in ("M15", "H1"):
    d = L0.filter(pl.col("clock") == clk).select("r_bps").collect()["r_bps"].to_numpy()
    print(f"  {clk}: gross mean/episode {d.mean():+.3f} bps; disclosed partial cost floor 13.5 bps "
          f"(fees+funding only, SPREAD NOT CHARGED) -> gross mean is {d.mean()/13.5:.3f}x the floor")
