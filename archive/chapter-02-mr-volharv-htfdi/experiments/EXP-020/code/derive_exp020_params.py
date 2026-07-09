"""EXP-020 candidate-blind parameter derivation (design §4 / §11.1, tripwire 2).

Reads ONLY EXP-019 result artifacts (python/experiments/EXP-019/results/):
  - legs_live.parquet : per-leg gross NetBps (cost=0) at fixed holds — |NetBps| at
    HorizonBars=H is the |H-bar open-to-open log move| in bps at random times.
  - costs.csv         : per-instrument round-trip commission bps (x1) at median price.

Derives per instrument (zero tuning, one value each):
  sigma12_bps  = median |12-bar log move|  (bps)         [substrate scale]
  g_bps        = sigma12_bps                              [ARM G grid spacing]
  b_price_bps  = 0.5 * sigma12_bps                        [ARM R band, price terms]
  b_w          = 0.25 * sigma12_bps / 1e4                 [ARM R band, weight terms]
  implied crossings/month  ~= (bars_per_month/12) * (rms12/median12)^2
    (quadratic-variation traversal count at spacing g; bars_per_month = 4900/44
     uniform TRAIN approximation, design §8; informative only)
  UNPOWERED-risk flag: implied crossings/month < 4 (design §8 predeclaration).

Stress read (informative, design §7 blocker): weekend CLOSED-MARKET spread snapshot
2026-07-05 03:24 (.ignore/temp/photos/, FTMO symbols page) = predeclared STRESS CEILING,
never the binding cost. EURJPY absent from the snapshot -> spread UNPINNED (no stress read).
Kill check: g_bps (gross harvest per grid round trip) vs weekend RT cost
(spread_bps + comm_rt_bps_x1).

Byte-reproducible: deterministic (no RNG); rerun by QA must byte-diff the output CSV.
"""
from __future__ import annotations

import json
from pathlib import Path

import polars as pl

EXP019_RESULTS = Path(__file__).resolve().parents[2] / "EXP-019" / "results"
OUT = Path(__file__).resolve().parents[1] / "results"

BARS_PER_MONTH = 4900.0 / 44.0          # design §8 TRAIN approximation, uniform
H_SIGMA = 12                             # substrate scale (design §4)
UNPOWERED_CROSSINGS = 4.0                # design §8 predeclared floor

# Weekend CLOSED-MARKET spread snapshot 2026-07-05 03:24 (FTMO symbols page screenshots,
# .ignore/temp/photos/). Full published spread in bps of mid. STRESS CEILING ONLY.
WEEKEND_SPREAD_BPS: dict[str, float | None] = {
    "AUDJPY": 0.080 / 111.961 * 1e4,     # 7.15
    "AUDUSD": 0.00037 / 0.693775 * 1e4,  # 5.33
    "GBPJPY": 0.083 / 215.4465 * 1e4,    # 3.85
    "GBPUSD": 0.00027 / 1.335045 * 1e4,  # 2.02
    "EURUSD": 0.00025 / 1.143655 * 1e4,  # 2.19
    "NZDUSD": 0.00024 / 0.5708 * 1e4,    # 4.20
    "USDCAD": 0.00099 / 1.420725 * 1e4,  # 6.97
    "USDCHF": 0.00066 / 0.80366 * 1e4,   # 8.21
    "USDJPY": 0.024 / 161.377 * 1e4,     # 1.49
    "EURJPY": None,                      # MISSING from snapshot -> UNPINNED
    "XAUUSD": 0.46 / 4174.99 * 1e4,      # 1.10
    "BTCUSD": 1.00 / 62708.64 * 1e4,     # 0.16
    "USTEC": 1.45 / 29654.755 * 1e4,     # 0.49  (US100.cash)
    "US500": 0.55 / 7503.455 * 1e4,      # 0.73
    "US2000": 0.94 / 3003.22 * 1e4,      # 3.13
    "JP225": 10.0 / 69680.5 * 1e4,       # 1.44
}

MR_BLOCK = ("NZDUSD", "AUDUSD", "GBPUSD", "USDCAD")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    legs = pl.read_parquet(EXP019_RESULTS / "legs_live.parquet")
    comm = pl.read_csv(EXP019_RESULTS / "costs.csv")

    sub = (legs.filter((pl.col("Censored") == 0) & (pl.col("HorizonBars") == H_SIGMA))
               .with_columns(pl.col("NetBps").abs().alias("abs_move")))
    prof = (sub.group_by("symbol")
               .agg(pl.col("abs_move").median().alias("sigma12_bps"),
                    (pl.col("abs_move").pow(2).mean().sqrt()).alias("rms12_bps"),
                    pl.len().alias("n_legs_h12"))
               .sort("symbol"))

    df = (prof.join(comm.select("symbol", "comm_rt_bps_x1"), on="symbol")
              .with_columns(
                  pl.col("sigma12_bps").alias("g_bps"),
                  (0.5 * pl.col("sigma12_bps")).alias("b_price_bps"),
                  (0.25 * pl.col("sigma12_bps") / 1e4).alias("b_w"),
              )
              .with_columns(
                  ((BARS_PER_MONTH / H_SIGMA)
                   * (pl.col("rms12_bps") / pl.col("g_bps")).pow(2))
                  .alias("implied_crossings_per_month"))
              .with_columns(
                  (pl.col("implied_crossings_per_month") < UNPOWERED_CROSSINGS)
                  .alias("unpowered_risk"))
              .with_columns(
                  pl.col("symbol").replace_strict(WEEKEND_SPREAD_BPS, default=None)
                    .alias("weekend_spread_bps"))
              .with_columns(
                  (pl.col("weekend_spread_bps") + pl.col("comm_rt_bps_x1"))
                  .alias("weekend_rt_cost_bps"))
              .with_columns(
                  (pl.col("g_bps") - pl.col("weekend_rt_cost_bps"))
                  .alias("stress_net_per_rt_bps"))
              .sort("symbol"))

    df = df.with_columns(pl.col("symbol").is_in(list(MR_BLOCK)).alias("mr_block"))
    df.write_csv(OUT / "exp020_params.csv")

    mr = df.filter(pl.col("mr_block"))
    kill = bool((mr["stress_net_per_rt_bps"] <= 0).all())
    summary = {
        "bars_per_month": BARS_PER_MONTH,
        "h_sigma": H_SIGMA,
        "unpowered_cells": df.filter(pl.col("unpowered_risk"))["symbol"].to_list(),
        "spread_unpinned": [s for s, v in WEEKEND_SPREAD_BPS.items() if v is None],
        "mr_block_all_dead_at_weekend_ceiling": kill,
    }
    (OUT / "exp020_params_summary.json").write_text(json.dumps(summary, indent=2))

    with pl.Config(tbl_rows=20, tbl_cols=15, float_precision=2):
        print(df.select("symbol", "mr_block", "sigma12_bps", "g_bps", "b_price_bps",
                        "b_w", "implied_crossings_per_month", "unpowered_risk",
                        "weekend_spread_bps", "comm_rt_bps_x1", "stress_net_per_rt_bps"))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
