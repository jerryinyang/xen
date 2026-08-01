"""SPDR-022 analyst pass 3: management-device execution census + device-native reads.

For every management arm: origins, order-created, realised fills, realised closes,
blocked, open-at-fence, exit-reason mix, and the realised outcome distribution --
per symbol and entry variant, no pruning.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import polars as pl

OUT = Path("python/experiments/SPDR-022/results/analyst")
LEDGER_KEY = ["episode_id", "arm_id", "policy_id"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--universe", required=True)
    a = ap.parse_args()
    run, u = Path(a.run), a.universe
    OUT.mkdir(parents=True, exist_ok=True)

    symbols = (
        pl.scan_parquet(run / "origins.parquet")
        .select(pl.col("symbol").unique())
        .collect()["symbol"]
        .to_list()
    )
    parts = []
    for sym in sorted(symbols):
        led = (
            pl.scan_parquet(run / "episode_results.parquet")
            .filter(
                (pl.col("policy_id") != "NONE")
                & pl.col("origin_id").str.starts_with(f"{sym}-")
            )
            .select("episode_id", "arm_id", "policy_id", "state", "price", "exit_reason")
        )
        entry = (
            led.filter(pl.col("state") == "FILLED")
            .group_by(LEDGER_KEY)
            .agg(pl.col("price").drop_nulls().first().alias("entry_price"))
        )
        closed = (
            led.filter(pl.col("state") == "CLOSED")
            .group_by(LEDGER_KEY)
            .agg(
                pl.col("price").drop_nulls().last().alias("exit_price"),
                pl.col("exit_reason").drop_nulls().last().alias("xr"),
            )
        )
        counts = (
            led.group_by("arm_id")
            .agg(
                (pl.col("state") == "FILLED").sum().alias("n_filled"),
                (pl.col("state") == "CLOSED").sum().alias("n_closed"),
                (pl.col("state") == "BLOCKED_ACTIVE").sum().alias("n_blocked"),
                (pl.col("state") == "OPEN_AT_FENCE_END").sum().alias("n_open_at_fence"),
                (pl.col("state") == "EXIT_DENIED").sum().alias("n_exit_denied"),
                (pl.col("state") == "DENIED").sum().alias("n_denied"),
            )
        )
        sched = (
            pl.scan_parquet(run / "policy_schedule.parquet")
            .filter(pl.col("symbol") == sym)
            .select(
                "symbol", "entry_variant", "arm_id", "arm_class", "component", "device",
                "setting", "comparator_id", "episode_id", "policy_id", "state", "side",
                "risk_size", "hold_bars",
            )
        )
        trades = (
            sched.join(entry, on=LEDGER_KEY, how="inner")
            .join(closed, on=LEDGER_KEY, how="inner")
            .with_columns(
                (
                    pl.col("side")
                    * (pl.col("exit_price") - pl.col("entry_price"))
                    / pl.col("entry_price")
                    * 1e4
                ).alias("gross_bps")
            )
        )
        per = (
            sched.group_by(
                "symbol", "entry_variant", "arm_id", "arm_class", "component", "device",
                "setting", "comparator_id",
            )
            .agg(
                pl.len().alias("eligible_origins"),
                (pl.col("state") == "ORDER_CREATED").sum().alias("n_order_created"),
            )
            .join(
                trades.group_by("symbol", "entry_variant", "arm_id").agg(
                    pl.len().alias("n_completed_trades"),
                    pl.col("gross_bps").mean().alias("gross_mean_bps"),
                    pl.col("gross_bps").median().alias("gross_median_bps"),
                    pl.col("gross_bps").std().alias("gross_sd_bps"),
                    (pl.col("gross_bps") > 0).mean().alias("win_share"),
                    (pl.col("xr") == "TARGET").sum().alias("exit_target"),
                    (pl.col("xr") == "STOP").sum().alias("exit_stop"),
                    (pl.col("xr") == "TRAIL").sum().alias("exit_trail"),
                    (pl.col("xr") == "HOLD").sum().alias("exit_hold"),
                ),
                on=["symbol", "entry_variant", "arm_id"],
                how="left",
            )
            .join(counts, on="arm_id", how="left")
            .collect()
        )
        parts.append(per)
        print(f"{u}/{sym}: {per.height} device-arm strata", flush=True)
    out = pl.concat(parts).sort("symbol", "entry_variant", "device", "arm_id")
    out.write_parquet(OUT / f"{u}_device_arm_census.parquet")
    print(out.group_by("device").agg(
        pl.len().alias("strata"),
        pl.col("n_completed_trades").fill_null(0).sum().alias("completed_trades"),
        (pl.col("n_completed_trades").fill_null(0) == 0).sum().alias("strata_with_zero_trades"),
    ).sort("device"))


if __name__ == "__main__":
    main()
