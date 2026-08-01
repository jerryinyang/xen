"""SPDR-022 analyst pass 4: assemble the markdown reporting tables.

Reads only the analyst tables written by a1-a3 and the canonical analysis artifacts.
Writes CSV mirrors of every table quoted in analysis.md plus a markdown fragment file.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

OUT = Path("python/experiments/SPDR-022/results/analyst")
CAN = Path("python/experiments/SPDR-022/results/analysis")


def md(frame: pl.DataFrame, floats: int = 3) -> str:
    cols = frame.columns
    exprs = []
    for c in cols:
        if frame.schema[c] in (pl.Float64, pl.Float32):
            exprs.append(pl.col(c).round(floats).cast(pl.Utf8).fill_null("-"))
        else:
            exprs.append(pl.col(c).cast(pl.Utf8).fill_null("-"))
    f = frame.select(exprs)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in f.iter_rows():
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def main() -> None:
    out_md = []
    for u in ("ctrader", "crypto"):
        rates = pl.read_parquet(OUT / f"{u}_native_arm_rates.parquet")
        paired = pl.read_parquet(OUT / f"{u}_native_paired.parquet")
        census = pl.read_parquet(OUT / f"{u}_device_arm_census.parquet").with_columns(
            pl.col("n_completed_trades").fill_null(0)
        )

        # --- native: component x parameter x orientation x variant ------
        j = paired.join(
            rates.select(
                "symbol", "entry_variant", "arm_id", "band_event_rate",
                "decided_side_rate", "selectivity", "n_order_created", "n_filled",
                "fill_rate_of_selected", "fill_gross_mean_bps", "win_share",
            ),
            on=["symbol", "entry_variant", "arm_id"],
        ).with_columns(
            pl.when(pl.col("arm_class") == "NATIVE")
            .then(
                pl.col("arm_id").str.extract(r"_(BAND_[ZH])_", 1)
            )
            .otherwise(pl.lit("BAND_Z+BAND_H"))
            .alias("parameter")
        )
        j.write_csv(OUT / f"{u}_native_full_stratum_table.csv")

        comp = (
            j.group_by("entry_variant", "component", "parameter", "orientation")
            .agg(
                pl.len().alias("symbols"),
                pl.col("band_event_rate").min().alias("band_ev_min"),
                pl.col("band_event_rate").median().alias("band_ev_med"),
                pl.col("band_event_rate").max().alias("band_ev_max"),
                pl.col("decided_side_rate").min().alias("decided_min"),
                pl.col("selectivity").median().alias("select_med"),
                pl.col("fill_rate_of_selected").median().alias("realised_fill_med"),
                pl.col("a_estimate_bps").min().alias("A_min"),
                pl.col("a_estimate_bps").median().alias("A_med"),
                pl.col("a_estimate_bps").max().alias("A_max"),
                pl.col("a_half_width").median().alias("A_hw_med"),
                pl.col("a_effective_n").median().alias("A_effn_med"),
                (pl.col("a_ci_low") > 0).sum().alias("A_ci_above_0"),
                (pl.col("a_ci_high") < 0).sum().alias("A_ci_below_0"),
                pl.col("b_estimate_bps").min().alias("B_min"),
                pl.col("b_estimate_bps").median().alias("B_med"),
                pl.col("b_estimate_bps").max().alias("B_max"),
                pl.col("b_half_width").median().alias("B_hw_med"),
                pl.col("b_n").median().alias("B_n_med"),
                pl.col("b_effective_n").median().alias("B_effn_med"),
                (pl.col("b_ci_low") > 0).sum().alias("B_ci_above_0"),
                (pl.col("b_ci_high") < 0).sum().alias("B_ci_below_0"),
            )
            .sort("entry_variant", "component", "parameter", "orientation")
        )
        comp.write_csv(OUT / f"{u}_native_component_table.csv")
        out_md.append(f"\n### {u}: native z/H by component x parameter x orientation\n")
        out_md.append(md(comp))

        # --- device census ------------------------------------------------
        dev = (
            census.group_by("entry_variant", "device", "arm_class", "arm_id", "setting", "component")
            .agg(
                pl.len().alias("symbols"),
                pl.col("eligible_origins").sum().alias("eligible_origins"),
                pl.col("n_order_created").sum().alias("selected"),
                pl.col("n_completed_trades").sum().alias("completed_trades"),
                pl.col("exit_target").fill_null(0).sum().alias("exit_target"),
                pl.col("exit_stop").fill_null(0).sum().alias("exit_stop"),
                pl.col("exit_trail").fill_null(0).sum().alias("exit_trail"),
                pl.col("exit_hold").fill_null(0).sum().alias("exit_hold"),
                pl.col("gross_mean_bps").median().alias("gross_mean_bps_med"),
                pl.col("win_share").median().alias("win_share_med"),
            )
            .sort("entry_variant", "device", "arm_class", "arm_id")
        )
        dev.write_csv(OUT / f"{u}_device_arm_table.csv")
        out_md.append(f"\n### {u}: management arm execution census\n")
        out_md.append(md(dev))

    (OUT / "report_tables.md").write_text("\n".join(out_md))
    print("wrote", OUT / "report_tables.md")


if __name__ == "__main__":
    main()
