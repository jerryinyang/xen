"""SPDR-022 analyst pass 2: native z/H arm strata, re-derived from raw emissions.

Emits, per (symbol, entry_variant, arm):
  band-event rate, decided-side rate, selectivity, fill rate, realised-fill gross
  distribution, and the common-origin AND both-filled paired adaptive-minus-fixed
  deltas with a 24h-block bootstrap interval, count, effective count and half-width.

Memory: ledger is reduced to FILLED/CLOSED rows before any join; the schedule is
projected to the columns used. Nothing wide is collected.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import polars as pl

OUT = Path("python/experiments/SPDR-022/results/analyst")
BLOCK_HOURS = 24
N_BOOT = 1000
SEED = 240730

SCHED_COLS = [
    "origin_id", "symbol", "decision_ts", "episode_id", "entry_variant",
    "arm_id", "arm_class", "component", "orientation", "state", "side",
    "z", "horizon", "entry_ts", "event_ts", "comparator_id", "policy_id",
]
# episode_id is NOT unique across arms: every management arm reuses the fixed-native
# episode_id. The ledger key is (episode_id, arm_id, policy_id).
LEDGER_KEY = ["episode_id", "arm_id", "policy_id"]


def episode_outcomes(run: Path, symbol: str | None = None) -> pl.DataFrame:
    led = pl.scan_parquet(run / "episode_results.parquet").filter(
        pl.col("state").is_in(["FILLED", "CLOSED"])
    )
    if symbol is not None:
        led = led.filter(pl.col("origin_id").str.starts_with(f"{symbol}-"))
    entry = (
        led.filter(pl.col("state") == "FILLED")
        .group_by(LEDGER_KEY)
        .agg(pl.col("price").drop_nulls().first().alias("entry_price"))
    )
    exit_ = (
        led.filter(pl.col("state") == "CLOSED")
        .group_by(LEDGER_KEY)
        .agg(
            pl.col("price").drop_nulls().last().alias("exit_price"),
            pl.col("exit_reason").drop_nulls().last().alias("exit_reason"),
        )
    )
    return entry.join(exit_, on=LEDGER_KEY, how="full", coalesce=True).collect()


def block_ci(delta: np.ndarray, block: np.ndarray) -> dict:
    n = len(delta)
    if n == 0:
        return dict(estimate=np.nan, ci_low=np.nan, ci_high=np.nan, half_width=np.nan,
                    effective_n=0, n=0)
    est = float(delta.mean())
    uniq, inv = np.unique(block, return_inverse=True)
    nb = len(uniq)
    if nb < 2:
        return dict(estimate=est, ci_low=np.nan, ci_high=np.nan, half_width=np.nan,
                    effective_n=nb, n=n)
    sums = np.bincount(inv, weights=delta, minlength=nb)
    cnts = np.bincount(inv, minlength=nb).astype(float)
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, nb, size=(N_BOOT, nb))
    means = sums[idx].sum(1) / cnts[idx].sum(1)
    lo, hi = np.quantile(means, [0.025, 0.975])
    return dict(estimate=est, ci_low=float(lo), ci_high=float(hi),
                half_width=float(est - lo), effective_n=nb, n=n)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--universe", required=True)
    ap.add_argument("--by-symbol", action="store_true")
    a = ap.parse_args()
    run, u = Path(a.run), a.universe
    OUT.mkdir(parents=True, exist_ok=True)

    if a.by_symbol:
        symbols = (
            pl.scan_parquet(run / "origins.parquet")
            .select(pl.col("symbol").unique())
            .collect()["symbol"]
            .to_list()
        )
        rate_parts, pair_parts = [], []
        for sym in sorted(symbols):
            r, p = _one(run, sym)
            rate_parts.append(r)
            pair_parts.append(p)
            print(f"{u}/{sym}: rates {r.height} paired {p.height}", flush=True)
        pl.concat(rate_parts).write_parquet(OUT / f"{u}_native_arm_rates.parquet")
        pl.concat(pair_parts).write_parquet(OUT / f"{u}_native_paired.parquet")
        return
    rates, paired = _one(run, None)
    rates.write_parquet(OUT / f"{u}_native_arm_rates.parquet")
    paired.write_parquet(OUT / f"{u}_native_paired.parquet")
    print(f"{u}: rates {rates.height} rows, paired {paired.height} rows")


def _one(run: Path, symbol: str | None):
    outc = episode_outcomes(run, symbol)
    sched = pl.scan_parquet(run / "native_parameter_schedule.parquet").select(SCHED_COLS)
    if symbol is not None:
        sched = sched.filter(pl.col("symbol") == symbol)
    frame = (
        sched.join(outc.lazy(), on=LEDGER_KEY, how="left")
        .with_columns(
            (
                pl.col("side")
                * (pl.col("exit_price") - pl.col("entry_price"))
                / pl.col("entry_price")
                * 1e4
            ).alias("gross_bps"),
            pl.col("decision_ts").dt.truncate(f"{BLOCK_HOURS}h").alias("blk"),
        )
        .with_columns(pl.col("gross_bps").is_not_null().alias("filled"))
        .collect()
    )

    # ---- rate table (every arm, every state visible) --------------------
    rates = (
        frame.group_by("symbol", "entry_variant", "arm_id", "arm_class", "component",
                       "orientation")
        .agg(
            pl.len().alias("eligible_origins"),
            (pl.col("state") == "ORDER_CREATED").sum().alias("n_order_created"),
            (pl.col("state") == "NO_EVENT").sum().alias("n_no_event"),
            (pl.col("state") == "NO_FEATURE").sum().alias("n_no_feature"),
            (pl.col("state") == "EVENT_UNDECIDED").sum().alias("n_event_undecided"),
            (pl.col("state") == "INCOMPLETE").sum().alias("n_incomplete"),
            (pl.col("state") == "CENSORED").sum().alias("n_censored"),
            pl.col("event_ts").is_not_null().sum().alias("n_event_ts"),
            pl.col("entry_ts").is_not_null().sum().alias("n_entry_intent"),
            pl.col("filled").sum().alias("n_filled"),
            pl.col("gross_bps").mean().alias("fill_gross_mean_bps"),
            pl.col("gross_bps").median().alias("fill_gross_median_bps"),
            pl.col("gross_bps").std().alias("fill_gross_sd_bps"),
            (pl.col("gross_bps") > 0).sum().alias("n_win"),
            pl.col("z").mean().alias("z_mean"),
            pl.col("horizon").mean().alias("h_mean"),
        )
        .with_columns(
            band_event_rate=(pl.col("n_order_created") + pl.col("n_event_undecided"))
            / pl.col("eligible_origins"),
            decided_side_rate=pl.when(
                (pl.col("n_order_created") + pl.col("n_event_undecided")) > 0
            )
            .then(
                pl.col("n_order_created")
                / (pl.col("n_order_created") + pl.col("n_event_undecided"))
            )
            .otherwise(None),
            selectivity=pl.col("n_order_created") / pl.col("eligible_origins"),
            fill_rate_of_eligible=pl.col("n_filled") / pl.col("eligible_origins"),
            fill_rate_of_selected=pl.when(pl.col("n_order_created") > 0)
            .then(pl.col("n_filled") / pl.col("n_order_created"))
            .otherwise(None),
            win_share=pl.when(pl.col("n_filled") > 0)
            .then(pl.col("n_win") / pl.col("n_filled"))
            .otherwise(None),
        )
        .sort("symbol", "entry_variant", "arm_id")
    )

    # ---- paired vs fixed ------------------------------------------------
    fixed = frame.filter(pl.col("arm_class") == "FIXED_NATIVE").select(
        "origin_id", "symbol", "entry_variant",
        pl.col("gross_bps").alias("fixed_gross_bps"),
        pl.col("filled").alias("fixed_filled"),
    )
    adapt = frame.filter(pl.col("arm_class") != "FIXED_NATIVE").join(
        fixed, on=["origin_id", "symbol", "entry_variant"], how="left"
    )
    del frame

    rows = []
    keys = ["symbol", "entry_variant", "arm_id", "arm_class", "component", "orientation"]
    for key, g in adapt.group_by(keys, maintain_order=True):
        ident = dict(zip(keys, key))
        blk = g["blk"].to_numpy()
        # (a) common-origin, zero-filled (canonical convention)
        d0 = (g["gross_bps"].fill_null(0.0) - g["fixed_gross_bps"].fill_null(0.0)).to_numpy()
        s0 = block_ci(d0, blk)
        # (b) both-filled only
        m = (g["filled"] & g["fixed_filled"]).to_numpy()
        d1 = (g["gross_bps"] - g["fixed_gross_bps"]).to_numpy()[m]
        s1 = block_ci(d1, blk[m])
        rows.append(
            {
                **ident,
                "population_a": "COMMON_ORIGIN_ZERO_FILLED",
                "a_estimate_bps": s0["estimate"], "a_ci_low": s0["ci_low"],
                "a_ci_high": s0["ci_high"], "a_half_width": s0["half_width"],
                "a_n": s0["n"], "a_effective_n": s0["effective_n"],
                "population_b": "BOTH_FILLED_PAIRED",
                "b_estimate_bps": s1["estimate"], "b_ci_low": s1["ci_low"],
                "b_ci_high": s1["ci_high"], "b_half_width": s1["half_width"],
                "b_n": s1["n"], "b_effective_n": s1["effective_n"],
                "n_adaptive_filled": int(g["filled"].sum()),
                "n_fixed_filled": int(g["fixed_filled"].sum()),
                "n_neither_filled": int((~g["filled"] & ~g["fixed_filled"]).sum()),
                "n_adaptive_only": int((g["filled"] & ~g["fixed_filled"]).sum()),
                "n_fixed_only": int((~g["filled"] & g["fixed_filled"]).sum()),
            }
        )
    return rates, pl.from_dicts(rows, infer_schema_length=None)


if __name__ == "__main__":
    main()
