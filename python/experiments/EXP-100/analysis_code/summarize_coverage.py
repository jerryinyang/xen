"""Build per-stratum coverage tables and destroy-collapse diagnostics."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

REPO = Path(__file__).resolve().parents[4]
OUT_DIR = REPO / "python/experiments/EXP-100/results/analysis"
CENSUS = OUT_DIR / "cell_census.parquet"
CLOCK = OUT_DIR / "trading_clock.parquet"


def _write(name: str, frame: pl.DataFrame) -> None:
    frame.write_csv(OUT_DIR / name)


def destroy_collapse_table(census: pl.DataFrame) -> pl.DataFrame:
    changed = census.filter(pl.col("destroy_non_vacuity") == "CHANGED")
    return changed.select(
        [
            "cell_id",
            "symbol",
            "timeframe",
            "method",
            "confirm_ref",
            "level_config",
            "n_confirmed",
            "destroy_n_value_changed",
            "destroy_n_swing_changed",
            "mean_abs_d_swing",
            "raw_mean_swing",
            "raw_se_swing",
            "integrity_bite",
            "destroy_collapses",
            "destroy_contrast_meta",
        ]
    ).sort(["n_confirmed", "cell_id"])


def main() -> None:
    census = pl.read_parquet(CENSUS)
    clock = pl.read_parquet(CLOCK)

    by_cfg = (
        census.group_by(["symbol", "timeframe", "level_config"])
        .agg(
            [
                pl.len().alias("n_cells"),
                pl.col("n_levels").min().alias("min_levels"),
                pl.col("n_levels").max().alias("max_levels"),
                pl.col("n_raids").min().alias("min_raids"),
                pl.col("n_raids").max().alias("max_raids"),
                pl.col("n_confirmed").min().alias("min_confirmed"),
                pl.col("n_confirmed").max().alias("max_confirmed"),
                pl.col("n_completed").sum().alias("sum_completed"),
                pl.col("n_same_bar_return").sum().alias("sum_same_bar_return"),
                pl.col("n_ambiguous").sum().alias("sum_ambiguous_retired"),
                pl.col("same_bar_return_frac").median().alias("median_same_bar_frac"),
            ]
        )
        .sort(["symbol", "timeframe", "level_config"])
    )
    _write("coverage_by_symbol_tf_config.csv", by_cfg)

    by_tf = (
        census.group_by(["symbol", "timeframe"])
        .agg(
            [
                pl.len().alias("n_cells"),
                pl.col("n_levels").sum(),
                pl.col("n_raids").sum(),
                pl.col("n_confirmed").sum(),
                pl.col("n_completed").sum(),
                pl.col("n_same_bar_return").sum(),
                pl.col("n_ambiguous").sum().alias("n_ambiguous_retired"),
                pl.col("n_failed").sum(),
                pl.col("n_non_primary").sum(),
                pl.col("same_bar_return_frac").median().alias("median_same_bar_frac"),
            ]
        )
        .sort(["symbol", "timeframe"])
    )
    _write("coverage_by_symbol_tf.csv", by_tf)

    by_cfg_only = (
        census.group_by("level_config")
        .agg(
            [
                pl.len().alias("n_cells"),
                pl.col("n_levels").min().alias("min_levels"),
                pl.col("n_levels").median().alias("median_levels"),
                pl.col("n_levels").max().alias("max_levels"),
                pl.col("n_raids").min().alias("min_raids"),
                pl.col("n_raids").median().alias("median_raids"),
                pl.col("n_raids").max().alias("max_raids"),
                pl.col("n_confirmed").min().alias("min_confirmed"),
                pl.col("n_confirmed").median().alias("median_confirmed"),
                pl.col("n_confirmed").max().alias("max_confirmed"),
                pl.col("n_completed").sum().alias("sum_completed"),
                pl.col("n_same_bar_return").sum().alias("sum_same_bar_return"),
                pl.col("n_ambiguous").sum().alias("sum_ambiguous_retired"),
                (pl.col("n_levels") == 0).sum().alias("zero_level_cells"),
                (pl.col("n_raids") == 0).sum().alias("zero_raid_cells"),
                (pl.col("n_confirmed") <= 1).sum().alias("le_1_confirmed_cells"),
            ]
        )
        .sort("level_config")
    )
    _write("coverage_by_config.csv", by_cfg_only)

    destroy = destroy_collapse_table(census)
    _write("destroy_cells.csv", destroy)
    n_lt5 = destroy.filter(pl.col("n_confirmed") < 5).height
    n_ge5 = destroy.filter(pl.col("n_confirmed") >= 5).height
    fail_ge5 = destroy.filter(
        (pl.col("n_confirmed") >= 5) & (pl.col("destroy_collapses") == False)
    )
    fail_lt5 = destroy.filter(
        (pl.col("n_confirmed") < 5) & (pl.col("destroy_collapses") == False)
    )
    meta_changed = destroy.filter(pl.col("destroy_n_value_changed") == 0)

    clock_1d = clock.filter(pl.col("level_config") == "PREVIOUS_1D").select(
        [
            "symbol",
            "timeframe",
            "n_levels",
            "n_anchors",
            "weekend_anchors",
            "create_sunday",
            "first_anchor",
            "last_anchor",
        ]
    )
    clock_1w = clock.filter(pl.col("level_config") == "PREVIOUS_1W").select(
        [
            "symbol",
            "timeframe",
            "n_levels",
            "n_anchors",
            "create_sunday",
            "first_anchor",
            "last_anchor",
        ]
    )
    _write("clock_1d.csv", clock_1d)
    _write("clock_1w.csv", clock_1w)

    summary = {
        "destroy_changed_cells": destroy.height,
        "destroy_n_confirmed_lt5": n_lt5,
        "destroy_n_confirmed_ge5": n_ge5,
        "destroy_collapse_false_ge5": fail_ge5["cell_id"].to_list(),
        "destroy_collapse_false_lt5_n": fail_lt5.height,
        "destroy_collapse_false_lt5": fail_lt5.select(
            ["cell_id", "n_confirmed", "mean_abs_d_swing", "integrity_bite"]
        ).to_dicts(),
        "destroy_changed_but_zero_value_swaps": meta_changed["cell_id"].to_list(),
        "min_1d_anchors": int(clock_1d["n_anchors"].min()),
        "max_1d_anchors": int(clock_1d["n_anchors"].max()),
        "min_1w_anchors": int(clock_1w["n_anchors"].min()),
        "max_1w_anchors": int(clock_1w["n_anchors"].max()),
        "1d_weekend_anchors": int(clock_1d["weekend_anchors"].sum()),
        "1d_create_sunday_rows": int(clock.filter(pl.col("level_config") == "PREVIOUS_1D")["create_sunday"].sum()),
        "1w_create_sunday_rows": int(clock.filter(pl.col("level_config") == "PREVIOUS_1W")["create_sunday"].sum()),
        "defined_tpo_total": int(census["n_defined_tpo"].sum()),
        "undefined_tpo_total": int(census["n_undefined_tpo"].sum()),
        "tight_defined_total": int(census["n_tight_defined"].sum()),
        "primary_attr_total": int(census["n_primary_attr"].sum()),
        "failed_total": int(census["n_failed"].sum()),
        "non_primary_total": int(census["n_non_primary"].sum()),
        "censor_exc_total": int(census["n_censor_exc"].sum()),
        "censor_conf_total": int(census["n_censor_conf"].sum()),
        "censor_end_total": int(census["n_censor_end"].sum()),
        "same_bar_return_total": int(census["n_same_bar_return"].sum()),
        "return_total": int(census["n_return"].sum()),
        "confirm_without_return_total": int(census["n_confirm_without_return"].sum()),
        "ambiguous_retired_total": int(census["n_ambiguous"].sum()),
        "same_bar_closed_ambiguous_total": int(
            census["n_same_bar_closed_ambiguous"].sum()
        ),
    }
    (OUT_DIR / "coverage_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
