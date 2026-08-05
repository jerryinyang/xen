"""Read-only extraction probes over SPDR-021/022/023 canonical analysis artifacts.

Usage: python probe_extract.py <probe>
Probes: devgrid | a1 | native | baseline | controls | conc
No artifact is written or modified.
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[3]  # python/
EXPS = ["SPDR-021", "SPDR-022", "SPDR-023"]
UNIS = ["ctrader", "crypto"]
DEVICES = ["target", "stop", "trail", "hold", "size"]

# Pre-test F classification (device metrics)
FORCED = {
    "reach_rate", "stop_rate",              # absorbing-device degeneracy
    "decay_bps", "opportunity_duration",     # function of elapsed time under hold arms
    "adverse_excursion_bps",                 # farther stop reached later
    "peak_giveback_bps",                     # wider trail gives back more
    "risk_dispersion", "tail_loss_bps",      # halving risk scales dispersion
    "concentration", "time_to_target",
    "loss_severity_bps", "loss_tail_bps",
    "missed_excess_bps",
}
FREE = {
    "outcome_by_time_bps", "favourable_excursion_captured",
    "drawdown_bps", "realised_capture_bps", "recovery_after_stop_bps",
    "holding_efficiency",
}


def cell_path(exp: str, uni: str) -> Path:
    return ROOT / "experiments" / exp / "results" / "analysis" / uni


def device_frame(exp: str, uni: str) -> pl.DataFrame:
    out = []
    for dv in DEVICES:
        d = pl.read_parquet(cell_path(exp, uni) / f"device_{dv}.parquet")
        out.append(d.with_columns(pl.lit(dv.upper()).alias("device_file")))
    return pl.concat(out, how="vertical_relaxed")


def qualify(g: pl.DataFrame, floor: int = 30) -> dict:
    """Per-cell qualifying rule (a)/(b) from Gate A1, on rows meeting the effective floor."""
    g = g.filter(pl.col("effective_trade_blocks") >= floor)
    n = g.height
    if n == 0:
        return {"n": 0, "rule": None}
    pos = g.filter(pl.col("ci_low") > 0).height
    neg = g.filter(pl.col("ci_high") < 0).height
    med_est = g["estimate"].median()
    med_mde = g["mde"].median()
    same_sign = (g["estimate"] > 0).sum()
    rule = None
    side = 0
    if pos > n / 2:
        rule, side = "a", 1
    elif neg > n / 2:
        rule, side = "a", -1
    elif med_mde is not None and med_est is not None and abs(med_est) > med_mde and (
        same_sign == n or same_sign == 0
    ):
        rule, side = "b", 1 if med_est > 0 else -1
    return {
        "n": n, "pos": pos, "neg": neg, "med_est": med_est, "med_mde": med_mde,
        "ratio": (abs(med_est) / med_mde) if med_mde else None,
        "sign_share": same_sign / n, "rule": rule, "side": side,
        "min_eff": g["effective_trade_blocks"].min(),
    }


def probe_devgrid() -> None:
    rows = []
    for exp in EXPS:
        for uni in UNIS:
            d = device_frame(exp, uni)
            keys = ["device_file", "setting", "component", "metric_name", "state", "arm_class"]
            for key, g in d.group_by(keys):
                q = qualify(g)
                rows.append(dict(zip(["device", "setting", "component", "metric", "state", "arm_class"], key))
                            | {"exp": exp, "uni": uni} | q)
    out = pl.DataFrame(rows)
    out.write_parquet("/tmp/devgrid.parquet")
    print(out.shape)
    print(out.filter(pl.col("rule").is_not_null()).height, "qualifying family-cells")


def probe_a1() -> None:
    d = pl.read_parquet("/tmp/devgrid.parquet")
    d = d.with_columns(
        pl.when(pl.col("metric").is_in(list(FORCED))).then(pl.lit("FORCED"))
        .when(pl.col("metric").is_in(list(FREE))).then(pl.lit("FREE"))
        .otherwise(pl.lit("?")).alias("forcedness")
    )
    # claim = device x setting x component x metric x state, aggregated over 6 cells
    agg = (
        d.filter(pl.col("state") == "ORDER_CREATED")
        .group_by(["device", "setting", "component", "metric", "forcedness"])
        .agg(
            cells=pl.col("exp").len(),
            qual=pl.col("rule").is_not_null().sum(),
            sides=pl.col("side").filter(pl.col("rule").is_not_null()).unique(),
            min_ratio=pl.col("ratio").filter(pl.col("rule").is_not_null()).min(),
            min_eff=pl.col("min_eff").filter(pl.col("rule").is_not_null()).min(),
            unis=pl.col("uni").filter(pl.col("rule").is_not_null()).n_unique(),
            exps=pl.col("exp").filter(pl.col("rule").is_not_null()).n_unique(),
        )
        .with_columns(consistent_side=pl.col("sides").list.len() == 1)
        .filter(pl.col("qual") >= 4)
        .sort(["forcedness", "qual", "min_ratio"], descending=[False, True, True])
    )
    with pl.Config(tbl_rows=200, tbl_cols=20, fmt_str_lengths=45):
        print(agg)


if __name__ == "__main__":
    globals()[f"probe_{sys.argv[1]}"]()
