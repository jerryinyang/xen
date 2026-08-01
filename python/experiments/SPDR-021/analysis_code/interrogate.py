"""Fresh-context analyst interrogation of SPDR-021 (independent of analyse.py).

Recomputes the common-origin estimand from raw emissions, audits row keys, and
repairs the empty shared-trade diagnostic by pairing on realised ledger fills.

Run:  python analysis_code/interrogate.py --universe ctrader
Outputs land in python/experiments/SPDR-021/results/analyst/.
"""

from __future__ import annotations

import argparse
import json
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
CANON = EXP / "results/analysis"


def ledger_outcomes(run: Path) -> pl.DataFrame:
    """(episode_id, arm_id, policy_id) -> realised entry/exit, gross bps."""
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
            pl.col("exit_reason").drop_nulls().last().alias("exit_reason"),
        )
    )
    return entry.join(closed, on=keys, how="full", coalesce=True).collect()


def native_frame(run: Path, universe: str) -> pl.DataFrame:
    sched = pl.scan_parquet(run / "native_parameter_schedule.parquet").select(
        "episode_id",
        "origin_id",
        "symbol",
        "entry_variant",
        "arm_id",
        "arm_class",
        "component",
        "orientation",
        "comparator_id",
        "state",
        "side",
        "decision_ts",
        "event_ts",
        "policy_id",
    )
    led = ledger_outcomes(run).lazy()
    frame = sched.join(led, on=["episode_id", "arm_id", "policy_id"], how="left")
    frame = frame.with_columns(
        (
            pl.col("side")
            * (pl.col("exit_price") - pl.col("entry_price"))
            / pl.col("entry_price")
            * 1e4
        ).alias("gross_bps")
    ).with_columns(pl.col("gross_bps").fill_null(0.0).alias("outcome_bps"))
    return frame.collect()


def recompute_native(frame: pl.DataFrame) -> pl.DataFrame:
    okeys = ["origin_id", "symbol", "entry_variant"]
    fixed = frame.filter(pl.col("arm_class") == "FIXED_NATIVE").select(
        *okeys, pl.col("outcome_bps").alias("fixed_outcome_bps")
    )
    f = frame.join(fixed, on=okeys, how="left").with_columns(
        pl.col("fixed_outcome_bps").fill_null(0.0),
        (pl.col("outcome_bps") - pl.col("fixed_outcome_bps").fill_null(0.0)).alias("delta"),
    )
    g = ["symbol", "arm_id", "arm_class", "component", "orientation"]
    return (
        f.group_by(g)
        .agg(
            pl.len().alias("origins_n"),
            pl.col("delta").mean().alias("estimate_recomputed"),
            pl.col("delta").std().alias("delta_sd"),
            (pl.col("state") == "ORDER_CREATED").sum().alias("order_created_n"),
            (pl.col("state") == "NO_EVENT").sum().alias("no_event_n"),
            (pl.col("state") == "NO_FEATURE").sum().alias("no_feature_n"),
            pl.col("entry_ns").is_not_null().sum().alias("filled_n"),
            pl.col("exit_price").is_not_null().sum().alias("closed_n"),
            pl.col("gross_bps").mean().alias("gross_mean_bps_trades"),
            pl.col("gross_bps").median().alias("gross_median_bps_trades"),
            (pl.col("gross_bps") > 0).mean().alias("win_share_trades"),
        )
        .sort(g)
    )


def cofill(frame: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Independent shared-trade pairing on realised ledger fills."""
    okeys = ["origin_id", "symbol", "entry_variant"]
    fixed = frame.filter(pl.col("arm_class") == "FIXED_NATIVE").select(
        *okeys,
        pl.col("entry_ns").alias("fixed_entry_ns"),
        pl.col("gross_bps").alias("fixed_gross_bps"),
    )
    adaptive = frame.filter(pl.col("arm_class") != "FIXED_NATIVE")
    j = adaptive.join(fixed, on=okeys, how="inner")
    both = j.filter(
        pl.col("entry_ns").is_not_null() & pl.col("fixed_entry_ns").is_not_null()
    ).with_columns(
        (pl.col("gross_bps") - pl.col("fixed_gross_bps")).alias("paired_delta_bps"),
        (pl.col("entry_ns") == pl.col("fixed_entry_ns")).alias("same_fill_ts"),
    )
    coverage = j.group_by("symbol", "arm_class").agg(
        pl.len().alias("adaptive_rows"),
        pl.col("entry_ns").is_not_null().sum().alias("adaptive_filled"),
        pl.col("fixed_entry_ns").is_not_null().sum().alias("fixed_filled"),
        (pl.col("entry_ns").is_not_null() & pl.col("fixed_entry_ns").is_not_null())
        .sum()
        .alias("both_filled"),
    )
    summary = (
        both.group_by("symbol", "arm_id", "arm_class", "component", "orientation")
        .agg(
            pl.len().alias("paired_n"),
            pl.col("paired_delta_bps").mean().alias("paired_mean_delta_bps"),
            pl.col("paired_delta_bps").median().alias("paired_median_delta_bps"),
            pl.col("paired_delta_bps").std().alias("paired_sd_bps"),
            pl.col("same_fill_ts").mean().alias("same_fill_ts_share"),
        )
        .with_columns(
            (
                1.96
                * pl.col("paired_sd_bps")
                / pl.col("paired_n").cast(pl.Float64).sqrt()
            ).alias("iid_halfwidth_bps")
        )
        .sort("symbol", "arm_id")
    )
    return coverage.sort("symbol", "arm_class"), summary


def audit(run: Path, universe: str, frame: pl.DataFrame) -> dict:
    c = CANON / universe
    npo = pl.read_parquet(c / "native_parameter_origins.parquet")
    nse = pl.scan_parquet(c / "native_parameter_selected_excluded.parquet")
    ps = pl.read_parquet(c / "per_stratum_estimates.parquet")
    sched_n = pl.scan_parquet(run / "native_parameter_schedule.parquet").select(pl.len()).collect().item()
    pol_n = pl.scan_parquet(run / "policy_schedule.parquet").select(pl.len()).collect().item()
    nse_n = nse.select(pl.len()).collect().item()
    # every (symbol, arm_id) in schedule present in npo ALL rows
    sched_keys = (
        pl.scan_parquet(run / "native_parameter_schedule.parquet")
        .select("symbol", "arm_id")
        .unique()
        .collect()
    )
    npo_keys = npo.filter(pl.col("state") == "ALL").select("symbol", "arm_id").unique()
    missing = sched_keys.join(npo_keys, on=["symbol", "arm_id"], how="anti")
    # per-state row counts in npo must sum to the ALL row count per (symbol, arm_id)
    per_state = (
        npo.filter(pl.col("state") != "ALL")
        .group_by("symbol", "arm_id")
        .agg(pl.col("eligible_origins").first().alias("elig"))
    )
    all_rows = npo.filter(pl.col("state") == "ALL").select(
        "symbol", "arm_id", pl.col("eligible_origins").alias("elig_all")
    )
    # schedule row counts per (symbol, arm_id)
    sched_counts = (
        pl.scan_parquet(run / "native_parameter_schedule.parquet")
        .group_by("symbol", "arm_id")
        .agg(pl.len().alias("sched_rows"))
        .collect()
    )
    joined = all_rows.join(sched_counts, on=["symbol", "arm_id"], how="full", coalesce=True)
    mismatch = joined.filter(pl.col("elig_all") != pl.col("sched_rows"))
    # state coverage: every observed state in the raw ledger vs reported tables
    ledger_states = (
        pl.scan_parquet(run / "episode_results.parquet")
        .group_by("state")
        .agg(pl.len())
        .collect()
    )
    return {
        "universe": universe,
        "native_schedule_rows": sched_n,
        "policy_schedule_rows": pol_n,
        "selected_excluded_rows": nse_n,
        "selected_excluded_equals_schedule": nse_n == sched_n,
        "native_origin_rows": npo.height,
        "per_stratum_rows": ps.height,
        "per_stratum_equals_native_plus_paired": ps.height
        == npo.height + ps.filter(pl.col("estimate_source") == "PAIRED_EPISODE").height,
        "schedule_arm_keys": sched_keys.height,
        "arm_keys_missing_from_reported_table": missing.height,
        "arm_keys_with_row_count_mismatch": mismatch.height,
        "ledger_states": {r["state"]: r["len"] for r in ledger_states.iter_rows(named=True)},
        "npo_states": {
            r["state"]: r["len"]
            for r in npo.group_by("state").agg(pl.len()).iter_rows(named=True)
        },
        "per_state_groups": per_state.height,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", required=True, choices=["ctrader", "crypto"])
    args = ap.parse_args()
    u = args.universe
    run = RUNS[u]
    OUT.mkdir(parents=True, exist_ok=True)

    frame = native_frame(run, u)
    rec = recompute_native(frame)
    rec.write_csv(OUT / f"native_recompute_{u}.csv")

    cov, paired = cofill(frame)
    cov.write_csv(OUT / f"cofill_coverage_{u}.csv")
    paired.write_csv(OUT / f"cofill_paired_{u}.csv")

    # parity vs canonical ALL-state estimates
    npo = pl.read_parquet(CANON / u / "native_parameter_origins.parquet").filter(
        pl.col("state") == "ALL"
    )
    par = npo.select(
        "symbol", "arm_id", "estimate", "ci_low", "ci_high", "mde", "effective_n"
    ).join(rec, on=["symbol", "arm_id"], how="full", coalesce=True)
    par = par.with_columns(
        (pl.col("estimate") - pl.col("estimate_recomputed")).abs().alias("abs_diff")
    )
    par.write_csv(OUT / f"parity_{u}.csv")

    aud = audit(run, u, frame)
    aud["parity_max_abs_diff_bps"] = float(par["abs_diff"].max())
    aud["parity_rows_over_1e_6"] = int((par["abs_diff"] > 1e-6).sum())
    aud["cofill_paired_rows_total"] = int(paired["paired_n"].sum())
    (OUT / f"audit_{u}.json").write_text(json.dumps(aud, indent=1, default=str))
    print(json.dumps(aud, indent=1, default=str))


if __name__ == "__main__":
    main()
