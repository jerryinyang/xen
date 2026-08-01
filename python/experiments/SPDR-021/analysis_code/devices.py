"""Independent device-arm interrogation, including the plain-management baseline.

The canonical device_*.parquet tables compare each adaptive device arm against its
FIXED_<DEVICE>_<SETTING> comparator only. The run also emits FIXED_BASELINE_PLAIN
(device NONE, unit size, no target/stop/trail) which no canonical table reports.
This script measures every management arm against BOTH comparators, episode-paired.
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
        "episode_id", "arm_id", "policy_id", "state", "ts_ns", "price", "exit_reason"
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
            pl.col("exit_reason").drop_nulls().last().alias("exit_reason_r"),
        )
    )
    sched = pl.scan_parquet(run / "policy_schedule.parquet").select(
        "episode_id", "origin_id", "symbol", "arm_id", "arm_class", "component",
        "device", "setting", "comparator_id", "state", "side", "decision_ts",
        "policy_id", "risk_size", "eligible", "eligibility_status",
    )
    return (
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
            pl.col("entry_ns").is_not_null().alias("filled"),
            (pl.col("gross_bps") * pl.col("risk_size")).alias("risked_bps"),
        )
        .collect()
    )


def paired(frame: pl.DataFrame, comparator_arm: str | None) -> pl.DataFrame:
    """Episode-paired adaptive-minus-comparator on jointly-filled episodes."""
    if comparator_arm is None:
        cmp = frame.select(
            "episode_id",
            pl.col("arm_id").alias("comparator_id"),
            pl.col("gross_bps").alias("c_bps"),
            pl.col("risked_bps").alias("c_risked"),
            pl.col("filled").alias("c_filled"),
            pl.col("exit_reason_r").alias("c_exit"),
        )
        adaptive = frame.filter(pl.col("arm_id") != pl.col("comparator_id"))
        j = adaptive.join(cmp, on=["episode_id", "comparator_id"], how="inner")
        label = "FIXED_DEVICE"
    else:
        cmp = frame.filter(pl.col("arm_id") == comparator_arm).select(
            "episode_id",
            pl.col("gross_bps").alias("c_bps"),
            pl.col("risked_bps").alias("c_risked"),
            pl.col("filled").alias("c_filled"),
            pl.col("exit_reason_r").alias("c_exit"),
        )
        adaptive = frame.filter(pl.col("arm_id") != comparator_arm)
        j = adaptive.join(cmp, on="episode_id", how="inner")
        label = "PLAIN_BASELINE"
    j = j.filter(pl.col("filled") & pl.col("c_filled")).with_columns(
        (pl.col("gross_bps") - pl.col("c_bps")).alias("delta"),
        (pl.col("risked_bps") - pl.col("c_risked")).alias("delta_risked"),
    )
    g = ["symbol", "arm_id", "arm_class", "component", "device", "setting"]
    rows = []
    def _f(x):
        return float("nan") if x is None else float(x)

    for key, grp in j.group_by(g, maintain_order=True):
        ident = dict(zip(g, key, strict=True))
        d = grp["delta"].to_numpy().astype(float)
        d = d[~np.isnan(d)]
        blk = (
            grp.with_columns(
                pl.col("decision_ts").cast(pl.Datetime("ns", "UTC")).dt.truncate("24h").alias("_b")
            )
            .group_by("_b")
            .agg(pl.col("delta").sum().alias("s"), pl.len().alias("c"))
        )
        s = blk["s"].to_numpy().astype(float)
        c = blk["c"].to_numpy().astype(float)
        lo = hi = float("nan")
        if len(s) >= 2:
            rng = np.random.default_rng(240730)
            idx = rng.integers(0, len(s), size=(2000, len(s)))
            draws = s[idx].sum(1) / c[idx].sum(1)
            lo, hi = (float(x) for x in np.quantile(draws, [0.025, 0.975]))
        rows.append(
            {
                **ident,
                "comparator": label,
                "comparator_id": comparator_arm or grp["comparator_id"][0],
                "paired_n": grp.height,
                "blocks_24h": len(s),
                "estimate_bps": _f(np.mean(d)) if len(d) else float("nan"),
                "median_bps": _f(np.median(d)) if len(d) else float("nan"),
                "ci_low": lo,
                "ci_high": hi,
                "halfwidth_low": (_f(np.mean(d)) - lo) if len(d) else float("nan"),
                "arm_mean_bps": _f(grp["gross_bps"].mean()),
                "cmp_mean_bps": _f(grp["c_bps"].mean()),
                "arm_win_share": _f((grp["gross_bps"] > 0).mean()),
                "cmp_win_share": _f((grp["c_bps"] > 0).mean()),
                "risked_delta_bps": _f(grp["delta_risked"].mean()),
            }
        )
    return pl.from_dicts(rows, infer_schema_length=None).sort(g)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", required=True)
    args = ap.parse_args()
    u = args.universe
    OUT.mkdir(parents=True, exist_ok=True)
    frame = build(RUNS[u])

    # population / state accounting for the management grid
    pop = (
        frame.group_by("arm_class", "device", "setting", "state", "eligibility_status")
        .agg(
            pl.len().alias("rows"),
            pl.col("filled").sum().alias("filled"),
            pl.col("exit_price").is_not_null().sum().alias("closed"),
        )
        .sort("arm_class", "device", "setting", "state")
    )
    pop.write_csv(OUT / f"device_population_{u}.csv")

    exits = (
        frame.filter(pl.col("exit_reason_r").is_not_null())
        .group_by("arm_class", "device", "setting", "exit_reason_r")
        .agg(pl.len().alias("n"))
        .sort("arm_class", "device", "setting", "exit_reason_r")
    )
    exits.write_csv(OUT / f"device_exit_reasons_{u}.csv")

    a = paired(frame, None)
    b = paired(frame, "FIXED_BASELINE_PLAIN")
    both = pl.concat([a, b], how="diagonal_relaxed")
    both.write_csv(OUT / f"device_paired_both_comparators_{u}.csv")
    print("fixed-device rows:", a.height, " plain-baseline rows:", b.height)
    print(
        both.group_by("comparator").agg(
            pl.len().alias("strata"),
            (pl.col("ci_low") > 0).sum().alias("ci_low_pos"),
            (pl.col("ci_high") < 0).sum().alias("ci_high_neg"),
            pl.col("paired_n").sum().alias("paired_n"),
        )
    )


if __name__ == "__main__":
    main()
