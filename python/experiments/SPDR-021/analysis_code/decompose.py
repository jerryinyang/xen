"""Decompose the common-origin native estimand and stress its interval.

Two products:
  1. selection decomposition — because every arm on an origin issues the SAME stop
     price, the adaptive-minus-fixed delta can only come from origins where exactly
     one of the two arms filled. This verifies that identity and sizes each side.
  2. CI robustness — 5-seed block-bootstrap battery at 24h plus a 12/24/48h block
     sweep, per stratum, on the same delta the canonical table reports.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[4]
EXP = ROOT / "python/experiments/SPDR-021"
OUT = EXP / "results/analyst"
RUNS = {
    "ctrader": ROOT / "data/nautilus_runs/SPDR-021-ctrader-train-20260731T004708Z",
    "crypto": ROOT / "data/nautilus_runs/SPDR-021-crypto-train-20260731T004708Z",
}


def build(run: Path) -> pl.DataFrame:
    lf = pl.scan_parquet(run / "episode_results.parquet").select(
        "episode_id", "arm_id", "policy_id", "state", "ts_ns", "price"
    )
    keys = ["episode_id", "arm_id", "policy_id"]
    entry = (
        lf.filter(pl.col("state") == "FILLED")
        .group_by(keys)
        .agg(
            pl.col("price").drop_nulls().first().cast(pl.Float64).alias("entry_price"),
            pl.col("ts_ns").first().cast(pl.Int64).alias("entry_ns"),
        )
    )
    closed = (
        lf.filter(pl.col("state") == "CLOSED")
        .group_by(keys)
        .agg(
            pl.col("price").drop_nulls().last().cast(pl.Float64).alias("exit_price"),
            pl.col("ts_ns").last().cast(pl.Int64).alias("exit_ns"),
        )
    )
    sched = pl.scan_parquet(run / "native_parameter_schedule.parquet").select(
        "episode_id", "origin_id", "symbol", "arm_id", "arm_class", "component",
        "orientation", "state", "side", "decision_ts", "event_ts",
        "policy_id", "threshold_atr", "expiry_bars",
    ).with_columns(
        pl.when(pl.col("arm_id").str.contains("BREAKOUT_THRESHOLD"))
        .then(pl.lit("BREAKOUT_THRESHOLD"))
        .when(pl.col("arm_id").str.contains("PENDING_EXPIRY"))
        .then(pl.lit("PENDING_EXPIRY"))
        .otherwise(pl.lit("BREAKOUT_THRESHOLD+PENDING_EXPIRY"))
        .alias("parameter")
    )
    f = (
        sched.join(entry, on=keys, how="left")
        .join(closed, on=keys, how="left")
        .with_columns(
            (
                pl.col("side")
                * (pl.col("exit_price") - pl.col("entry_price"))
                / pl.col("entry_price")
                * 1e4
            ).alias("gross_bps")
        )
        .with_columns(
            pl.col("gross_bps").fill_null(0.0).alias("outcome_bps"),
            pl.col("entry_ns").is_not_null().alias("filled"),
            (
                (pl.col("entry_ns") - pl.col("event_ts").dt.epoch("ns"))
                / 3_600_000_000_000
            ).alias("time_to_fill_h"),
        )
    )
    return f.collect()


def decompose(frame: pl.DataFrame) -> pl.DataFrame:
    ok = ["origin_id", "symbol"]
    fixed = frame.filter(pl.col("arm_class") == "FIXED_NATIVE").select(
        *ok,
        pl.col("outcome_bps").alias("fx_bps"),
        pl.col("filled").alias("fx_filled"),
    )
    a = frame.filter(pl.col("arm_class") != "FIXED_NATIVE").join(fixed, on=ok, how="left")
    a = a.with_columns(
        pl.col("fx_bps").fill_null(0.0), pl.col("fx_filled").fill_null(False)
    )
    g = ["symbol", "arm_id", "arm_class", "component", "parameter", "orientation"]
    return (
        a.group_by(g)
        .agg(
            pl.len().alias("origins_n"),
            pl.col("filled").sum().alias("adaptive_fills"),
            pl.col("fx_filled").sum().alias("fixed_fills"),
            (pl.col("filled") & pl.col("fx_filled")).sum().alias("both_fill"),
            (pl.col("filled") & ~pl.col("fx_filled")).sum().alias("adaptive_only"),
            (~pl.col("filled") & pl.col("fx_filled")).sum().alias("fixed_only"),
            pl.when(pl.col("filled") & pl.col("fx_filled"))
            .then((pl.col("outcome_bps") - pl.col("fx_bps")).abs())
            .otherwise(0.0)
            .max()
            .alias("max_abs_both_fill_delta_bps"),
            pl.when(pl.col("filled") & ~pl.col("fx_filled"))
            .then(pl.col("outcome_bps"))
            .otherwise(0.0)
            .sum()
            .alias("adaptive_only_sum_bps"),
            pl.when(~pl.col("filled") & pl.col("fx_filled"))
            .then(pl.col("fx_bps"))
            .otherwise(0.0)
            .sum()
            .alias("fixed_only_sum_bps"),
            (pl.col("outcome_bps") - pl.col("fx_bps")).mean().alias("estimate"),
            pl.col("time_to_fill_h").median().alias("time_to_fill_median_h"),
            pl.col("time_to_fill_h").quantile(0.9).alias("time_to_fill_p90_h"),
            (pl.col("state") == "ORDER_CREATED").sum().alias("orders"),
        )
        .with_columns(
            (
                (pl.col("adaptive_only_sum_bps") - pl.col("fixed_only_sum_bps"))
                / pl.col("origins_n")
            ).alias("estimate_from_selection_only"),
            (pl.col("adaptive_fills") / pl.col("origins_n")).alias("fill_rate_true"),
            (pl.col("orders") / pl.col("origins_n")).alias("order_rate"),
        )
        .with_columns(
            (pl.col("estimate") - pl.col("estimate_from_selection_only"))
            .abs()
            .alias("decomposition_residual_bps")
        )
        .sort(g)
    )


def ci_battery(frame: pl.DataFrame, n_boot: int = 1000) -> pl.DataFrame:
    ok = ["origin_id", "symbol"]
    fixed = frame.filter(pl.col("arm_class") == "FIXED_NATIVE").select(
        *ok, pl.col("outcome_bps").alias("fx_bps")
    )
    a = (
        frame.filter(pl.col("arm_class") != "FIXED_NATIVE")
        .join(fixed, on=ok, how="left")
        .with_columns(
            (pl.col("outcome_bps") - pl.col("fx_bps").fill_null(0.0)).alias("delta")
        )
    )
    rows = []
    for hours in (12, 24, 48):
        a = a.with_columns(
            pl.col("decision_ts")
            .cast(pl.Datetime("ns", "UTC"))
            .dt.truncate(f"{hours}h")
            .alias(f"_blk{hours}")
        )
    for key, grp in a.group_by(["symbol", "arm_id"], maintain_order=True):
        row = {"symbol": key[0], "arm_id": key[1], "estimate": float(grp["delta"].mean())}
        for hours in (12, 24, 48):
            agg = grp.group_by(f"_blk{hours}").agg(
                pl.col("delta").sum().alias("s"), pl.len().alias("c")
            )
            s = agg["s"].to_numpy().astype(float)
            c = agg["c"].to_numpy().astype(float)
            nb = len(s)
            if nb < 2:
                continue
            lows, highs = [], []
            seeds = (240730, 1, 2, 3, 4) if hours == 24 else (240730,)
            for seed in seeds:
                rng = np.random.default_rng(seed)
                idx = rng.integers(0, nb, size=(n_boot, nb))
                draws = s[idx].sum(1) / c[idx].sum(1)
                lo, hi = np.quantile(draws, [0.025, 0.975])
                lows.append(float(lo))
                highs.append(float(hi))
            row[f"ci_low_{hours}h"] = lows[0]
            row[f"ci_high_{hours}h"] = highs[0]
            row[f"blocks_{hours}h"] = nb
            if hours == 24:
                row["ci_low_seed_min"] = min(lows)
                row["ci_low_seed_max"] = max(lows)
                row["ci_high_seed_min"] = min(highs)
                row["ci_high_seed_max"] = max(highs)
                row["seed_band_straddles_zero"] = bool(
                    min(lows) <= 0.0 <= max(lows) or min(highs) <= 0.0 <= max(highs)
                )
        rows.append(row)
    out = pl.from_dicts(rows, infer_schema_length=None)
    return out.with_columns(
        (
            (pl.col("ci_low_12h") > 0).cast(pl.Int8)
            + (pl.col("ci_low_24h") > 0).cast(pl.Int8)
            + (pl.col("ci_low_48h") > 0).cast(pl.Int8)
        ).alias("n_blocks_ci_low_pos"),
        (
            (pl.col("ci_high_12h") < 0).cast(pl.Int8)
            + (pl.col("ci_high_24h") < 0).cast(pl.Int8)
            + (pl.col("ci_high_48h") < 0).cast(pl.Int8)
        ).alias("n_blocks_ci_high_neg"),
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", required=True)
    args = ap.parse_args()
    u = args.universe
    OUT.mkdir(parents=True, exist_ok=True)
    frame = build(RUNS[u])
    d = decompose(frame)
    d.write_csv(OUT / f"decomposition_{u}.csv")
    print("max decomposition residual (bps):", d["decomposition_residual_bps"].max())
    print("max |delta| on co-filled origins (bps):", d["max_abs_both_fill_delta_bps"].max())
    print("strata:", d.height)
    b = ci_battery(frame)
    b.write_csv(OUT / f"ci_battery_{u}.csv")
    print("ci battery rows:", b.height)
    print(
        b.select(
            (pl.col("n_blocks_ci_low_pos") == 3).sum().alias("pos_all3blocks"),
            (pl.col("n_blocks_ci_high_neg") == 3).sum().alias("neg_all3blocks"),
            (pl.col("n_blocks_ci_low_pos").is_between(1, 2)).sum().alias("pos_blockfragile"),
            (pl.col("n_blocks_ci_high_neg").is_between(1, 2)).sum().alias("neg_blockfragile"),
            pl.col("seed_band_straddles_zero").sum().alias("seed_fragile"),
        )
    )


if __name__ == "__main__":
    main()
