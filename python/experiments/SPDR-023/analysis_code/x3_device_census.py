"""SPDR-023 fresh-context analyst — X3: management-device episode census.

Counts, per management arm x entry variant x symbol, the episodes the LEDGER actually
records (FILLED / CLOSED / BLOCKED_ACTIVE / EXIT_DENIED / ...), and sets them beside the
`episode_n` / `effective_n` the canonical device_*.parquet tables report for the same
stratum. Emits the full join; no pruning, no verdict.
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

ROOT = Path("/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen")
ART = ROOT / "python/experiments/SPDR-023/results/analysis"
RUNS = {
    "ctrader": ROOT / "data/nautilus_runs/SPDR-023-ctrader-train-20260731T004708Z",
    "crypto": ROOT / "data/nautilus_runs/SPDR-023-crypto-train-20260731T004708Z",
}
OUT = ROOT / "python/experiments/SPDR-023/results/analyst"
DEVICES = ["target", "stop", "trail", "hold", "size"]


def run(universe: str) -> None:
    o = OUT / universe
    o.mkdir(parents=True, exist_ok=True)
    er = pl.scan_parquet(RUNS[universe] / "episode_results.parquet")
    pol = pl.scan_parquet(RUNS[universe] / "policy_schedule.parquet")

    # symbol is not on episode_results; take it from the policy schedule via origin_id
    sym = pol.select("origin_id", "symbol").unique()

    led = (
        er.filter(pl.col("arm_class").str.contains("MANAGEMENT"))
        .join(sym, on="origin_id", how="left")
        .group_by("symbol", "entry_variant", "arm_id", "arm_class")
        .agg(
            (pl.col("state") == "ORDER_CREATED").sum().alias("led_order_created"),
            (pl.col("state") == "FILLED").sum().alias("led_filled"),
            (pl.col("state") == "CLOSED").sum().alias("led_closed"),
            (pl.col("state") == "BLOCKED_ACTIVE").sum().alias("led_blocked_active"),
            (pl.col("state") == "EXIT_DENIED").sum().alias("led_exit_denied"),
            (pl.col("state") == "DENIED").sum().alias("led_denied"),
            (pl.col("state") == "OPEN_AT_FENCE_END").sum().alias("led_open_at_fence_end"),
            (pl.col("state") == "HOLD_DUE").sum().alias("led_hold_due"),
            (pl.col("state") == "NO_EVENT").sum().alias("led_no_event"),
            (pl.col("state") == "NO_FEATURE").sum().alias("led_no_feature"),
            (pl.col("state") == "EVENT_UNDECIDED").sum().alias("led_event_undecided"),
            (pl.col("state") == "INCOMPLETE").sum().alias("led_incomplete"),
            (pl.col("state") == "CENSORED").sum().alias("led_censored"),
            (pl.col("exit_reason") == "TARGET").sum().alias("exit_target"),
            (pl.col("exit_reason") == "STOP").sum().alias("exit_stop"),
            (pl.col("exit_reason") == "TRAIL").sum().alias("exit_trail"),
            (pl.col("exit_reason") == "HOLD").sum().alias("exit_hold"),
            pl.len().alias("ledger_rows"),
        )
        .collect()
    )
    led = led.with_columns(
        blocked_share=pl.col("led_blocked_active")
        / (pl.col("led_blocked_active") + pl.col("led_filled")),
    )
    led.write_parquet(o / "device_arm_ledger_census.parquet")
    led.write_csv(o / "device_arm_ledger_census.csv")

    # reported power per device stratum
    rep = pl.concat(
        [pl.read_parquet(ART / universe / f"device_{d}.parquet").with_columns(
            device_family=pl.lit(d.upper())) for d in DEVICES],
        how="vertical_relaxed",
    )
    rep_small = (
        rep.group_by("symbol", "entry_variant", "arm_id", "device_family")
        .agg(pl.col("episode_n").max().alias("reported_episode_n"),
             pl.col("effective_n").max().alias("reported_effective_n"),
             pl.col("mde").min().alias("reported_min_mde"),
             pl.len().alias("reported_rows"))
    )
    j = rep_small.join(led, on=["symbol", "entry_variant", "arm_id"], how="left").with_columns(
        reported_over_actual_filled=pl.col("reported_episode_n") / pl.col("led_filled"),
    ).sort("led_filled")
    j.write_parquet(o / "device_reported_vs_ledger.parquet")
    j.write_csv(o / "device_reported_vs_ledger.csv")

    print(f"== {universe}: management arm-strata {led.height}")
    print(led.group_by("arm_class").agg(
        pl.col("led_filled").sum().alias("filled"),
        pl.col("led_blocked_active").sum().alias("blocked"),
        pl.col("led_exit_denied").sum().alias("exit_denied"),
        pl.col("led_filled").median().alias("median_filled_per_stratum"),
    ).sort("arm_class"))
    print("device strata by actual filled-episode band:")
    print(j.with_columns(
        band=pl.when(pl.col("led_filled") < 10).then(pl.lit("<10"))
        .when(pl.col("led_filled") < 100).then(pl.lit("10-99"))
        .when(pl.col("led_filled") < 1000).then(pl.lit("100-999"))
        .otherwise(pl.lit(">=1000"))
    ).group_by("device_family", "band").agg(pl.len()).sort("device_family", "band"))


if __name__ == "__main__":
    for u in sys.argv[1:] or ["ctrader", "crypto"]:
        run(u)
