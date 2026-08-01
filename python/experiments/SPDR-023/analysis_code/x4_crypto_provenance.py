"""SPDR-023 fresh-context analyst — X4: crypto engine-change provenance check.

The crypto run's first 13 of 25 symbols (config.json symbol order) were produced before an
engine memory-release change; the remaining 12 after. The change is understood to be
memory-only with the emission unchanged. This script looks for an observable discontinuity
between the two groups in row shapes, state mixes and fill rates. Descriptive only.
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

ROOT = Path("/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen")
R = ROOT / "data/nautilus_runs/SPDR-023-crypto-train-20260731T004708Z"
OUT = ROOT / "python/experiments/SPDR-023/results/analyst/crypto"

cfg = json.loads((R / "config.json").read_text())
SYMS = cfg["symbols"]
GROUP_A = SYMS[:13]   # produced before the engine memory-release change
GROUP_B = SYMS[13:]   # produced after


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    nps = pl.scan_parquet(R / "native_parameter_schedule.parquet")
    grp = pl.when(pl.col("symbol").is_in(GROUP_A)).then(pl.lit("A_pre_change")) \
            .otherwise(pl.lit("B_post_change"))

    per_symbol = (
        nps.with_columns(group=grp)
        .group_by("symbol", "group", "entry_variant")
        .agg(
            pl.len().alias("rows"),
            pl.col("origin_id").n_unique().alias("origins"),
            pl.col("native_arm_id").n_unique().alias("arms"),
            (pl.col("state") == "ORDER_CREATED").mean().alias("order_created_share"),
            (pl.col("state") == "NO_FEATURE").mean().alias("no_feature_share"),
            (pl.col("state") == "NO_EVENT").mean().alias("no_event_share"),
            (pl.col("state") == "EVENT_UNDECIDED").mean().alias("event_undecided_share"),
            (pl.col("state") == "INCOMPLETE").mean().alias("incomplete_share"),
            (pl.col("state") == "CENSORED").mean().alias("censored_share"),
            (pl.col("entry_ts").is_not_null()).mean().alias("entry_ts_share"),
            pl.col("z").mean().alias("z_mean"),
            pl.col("horizon").mean().alias("h_mean"),
            pl.col("decision_ts").min().alias("first_decision_ts"),
            pl.col("decision_ts").max().alias("last_decision_ts"),
        )
        .sort("group", "symbol", "entry_variant")
        .collect()
    )
    per_symbol.write_csv(OUT / "crypto_provenance_per_symbol.csv")
    per_symbol.write_parquet(OUT / "crypto_provenance_per_symbol.parquet")

    er = pl.scan_parquet(R / "episode_results.parquet")
    pol = pl.scan_parquet(R / "policy_schedule.parquet").select("origin_id", "symbol").unique()
    led = (
        er.join(pol, on="origin_id", how="left")
        .with_columns(group=grp)
        .group_by("symbol", "group")
        .agg(
            pl.len().alias("ledger_rows"),
            (pl.col("state") == "FILLED").sum().alias("filled"),
            (pl.col("state") == "CLOSED").sum().alias("closed"),
            (pl.col("state") == "BLOCKED_ACTIVE").sum().alias("blocked"),
            (pl.col("state") == "EXIT_DENIED").sum().alias("exit_denied"),
            (pl.col("state") == "OPEN_AT_FENCE_END").sum().alias("open_at_fence_end"),
        )
        .with_columns(fill_rate=pl.col("filled") / pl.col("ledger_rows"))
        .sort("group", "symbol")
        .collect()
    )
    led.write_csv(OUT / "crypto_provenance_ledger_per_symbol.csv")

    j = per_symbol.join(led, on=["symbol", "group"], how="left")
    grp_summary = (
        j.group_by("group").agg(
            pl.col("symbol").n_unique().alias("symbols"),
            pl.col("rows").sum().alias("native_rows"),
            pl.col("arms").min().alias("min_arms"), pl.col("arms").max().alias("max_arms"),
            pl.col("order_created_share").mean().alias("mean_order_created_share"),
            pl.col("order_created_share").std().alias("sd_order_created_share"),
            pl.col("no_feature_share").mean().alias("mean_no_feature_share"),
            pl.col("event_undecided_share").mean().alias("mean_event_undecided_share"),
            pl.col("entry_ts_share").mean().alias("mean_entry_ts_share"),
            pl.col("fill_rate").mean().alias("mean_ledger_fill_rate"),
            pl.col("fill_rate").std().alias("sd_ledger_fill_rate"),
            pl.col("exit_denied").sum().alias("exit_denied"),
            pl.col("open_at_fence_end").sum().alias("open_at_fence_end"),
        ).sort("group")
    )
    grp_summary.write_csv(OUT / "crypto_provenance_group_summary.csv")
    pl.Config.set_tbl_width_chars(300)
    print("GROUP A (first 13, pre-change):", GROUP_A)
    print("GROUP B (last 12, post-change):", GROUP_B)
    print(grp_summary)
    print(j.select("symbol", "group", "arms", "order_created_share", "entry_ts_share",
                   "fill_rate", "exit_denied", "open_at_fence_end").sort("group", "symbol"))


if __name__ == "__main__":
    main()
