"""Emit the analyst's full per-stratum tables (CSV) and console summaries."""

from __future__ import annotations

import argparse
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[4]
EXP = ROOT / "python/experiments/SPDR-021"
CANON = EXP / "results/analysis"
OUT = EXP / "results/analyst"

pl.Config.set_tbl_rows(3000)
pl.Config.set_tbl_width_chars(400)
pl.Config.set_fmt_str_lengths(70)
pl.Config.set_tbl_cols(40)


def md(df: pl.DataFrame) -> str:
    cols = df.columns
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for row in df.iter_rows():
        cells = []
        for v in row:
            if v is None:
                cells.append("null")
            elif isinstance(v, float):
                cells.append("nan" if v != v else f"{v:.4g}")
            else:
                cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", required=True)
    ap.add_argument("--section", required=True)
    args = ap.parse_args()
    u, sec = args.universe, args.section
    c = CANON / u
    OUT.mkdir(parents=True, exist_ok=True)

    if sec == "export":
        for name in [
            "native_parameter_origins",
            "per_stratum_estimates",
            "device_target",
            "device_stop",
            "device_trail",
            "device_hold",
            "device_size",
            "state_sections",
            "selection_checks",
            "controls",
        ]:
            df = pl.read_parquet(c / f"{name}.parquet")
            df.write_csv(OUT / f"{name}_{u}.csv")
            print(name, df.height)
        return

    npo = pl.read_parquet(c / "native_parameter_origins.parquet")

    if sec == "fixed":
        f = npo.filter(pl.col("arm_class") == "FIXED_NATIVE").select(
            "symbol", "state", "eligible_origins", "signal_count", "event_count",
            "fill_count", "signal_rate", "event_rate", "fill_rate",
            "exposure_per_origin", "estimate", "ci_low", "ci_high", "mde", "effective_n",
        ).sort("symbol", "state")
        print(md(f))
        ps = pl.read_parquet(c / "per_stratum_estimates.parquet").filter(
            pl.col("arm_id") == "FIXED_NATIVE_BREAKOUT"
        ).select(
            "symbol", "state", "trade_count", "gross_mean_bps", "gross_median_bps",
            "gross_trimmed_mean_bps", "win_share", "mean_win_bps", "mean_loss_bps",
            "win_loss_ratio", "breakeven_win_share_net", "edge_bps", "mfe_bps",
            "mae_bps", "exit_reason", "partial_cost_mean_bps",
        ).sort("symbol", "state")
        print()
        print(md(ps))
        return

    if sec == "native_all":
        a = npo.filter(pl.col("state") == "ALL").select(
            "symbol", "component", "parameter", "orientation", "orientation_pair",
            "eligible_origins", "signal_count", "event_count", "fill_count",
            "fill_rate", "exposure_per_origin", "estimate", "ci_low", "ci_high",
            "mde", "effective_n",
        ).sort("component", "parameter", "orientation", "symbol")
        print(md(a))
        return

    if sec == "native_arm_summary":
        a = npo.filter(pl.col("state") == "ALL")
        s = (
            a.group_by("arm_class", "component", "parameter", "orientation")
            .agg(
                pl.len().alias("symbols"),
                pl.col("estimate").median().alias("est_median"),
                pl.col("estimate").min().alias("est_min"),
                pl.col("estimate").max().alias("est_max"),
                (pl.col("ci_low") > 0).sum().alias("ci_excl_zero_pos"),
                (pl.col("ci_high") < 0).sum().alias("ci_excl_zero_neg"),
                pl.col("fill_count").sum().alias("fills_total"),
                pl.col("event_count").sum().alias("events_total"),
                pl.col("effective_n").median().alias("eff_n_median"),
                pl.col("mde").median().alias("mde_median"),
            )
            .sort("arm_class", "component", "parameter", "orientation")
        )
        print(md(s))
        return

    if sec == "native_states":
        a = npo.filter(pl.col("state") != "ALL").select(
            "symbol", "arm_class", "component", "parameter", "orientation", "state",
            "eligible_origins", "signal_count", "event_count", "fill_count",
            "estimate", "ci_low", "ci_high", "mde", "effective_n",
        )
        s = (
            a.group_by("arm_class", "component", "parameter", "orientation", "state")
            .agg(
                pl.len().alias("symbols"),
                pl.col("event_count").sum().alias("event_n"),
                pl.col("fill_count").sum().alias("fill_n"),
                pl.col("estimate").median().alias("est_median"),
                pl.col("estimate").min().alias("est_min"),
                pl.col("estimate").max().alias("est_max"),
            )
            .sort("arm_class", "component", "parameter", "orientation", "state")
        )
        print(md(s))
        return

    if sec.startswith("device_"):
        dev = sec.split("_", 1)[1]
        d = pl.read_parquet(c / f"device_{dev}.parquet")
        s = (
            d.group_by("arm_class", "component", "device", "setting", "comparator_id",
                       "state", "metric_name")
            .agg(
                pl.len().alias("symbols"),
                pl.col("observed").median().alias("obs_median"),
                pl.col("comparator_observed").median().alias("cmp_median"),
                pl.col("estimate").median().alias("est_median"),
                pl.col("estimate").min().alias("est_min"),
                pl.col("estimate").max().alias("est_max"),
                (pl.col("ci_low") > 0).sum().alias("ci_pos"),
                (pl.col("ci_high") < 0).sum().alias("ci_neg"),
                pl.col("episode_n").sum().alias("episode_n"),
                pl.col("effective_n").median().alias("eff_n_med"),
                pl.col("mde").median().alias("mde_med"),
            )
            .sort("arm_class", "component", "setting", "state", "metric_name")
        )
        print(md(s))
        return

    if sec == "device_full":
        for dev in ["target", "stop", "trail", "hold", "size"]:
            d = pl.read_parquet(c / f"device_{dev}.parquet").select(
                "symbol", "arm_id", "arm_class", "component", "device", "setting",
                "comparator_id", "state", "metric_name", "observed",
                "comparator_observed", "estimate", "ci_low", "ci_high", "mde",
                "episode_n", "effective_n",
            ).sort("component", "setting", "metric_name", "symbol", "state")
            print(f"\n### device_{dev}\n")
            print(md(d))
        return

    if sec == "paired":
        p = pl.read_parquet(c / "per_stratum_estimates.parquet").filter(
            pl.col("estimate_source") == "PAIRED_EPISODE"
        )
        s = (
            p.group_by("arm_class", "component", "device", "setting", "comparator_id",
                       "state")
            .agg(
                pl.len().alias("symbols"),
                pl.col("estimate").median().alias("est_median"),
                pl.col("estimate").min().alias("est_min"),
                pl.col("estimate").max().alias("est_max"),
                (pl.col("ci_low") > 0).sum().alias("ci_pos"),
                (pl.col("ci_high") < 0).sum().alias("ci_neg"),
                pl.col("paired_n").sum().alias("paired_n"),
                pl.col("effective_n").median().alias("eff_n_med"),
                pl.col("mde").median().alias("mde_med"),
                pl.col("trade_count").sum().alias("trade_n"),
                pl.col("gross_mean_bps").median().alias("gross_med"),
                pl.col("win_share").median().alias("win_share_med"),
            )
            .sort("arm_class", "component", "device", "setting", "state")
        )
        print(md(s))
        return

    if sec == "states":
        ss = pl.read_parquet(c / "state_sections.parquet")
        print("distinct states:", ss["state"].unique().sort().to_list())
        print()
        print(md(ss.group_by("state").agg(
            pl.len().alias("strata"),
            pl.col("row_n").sum().alias("rows"),
            pl.col("mean_outcome_bps").median().alias("mean_outcome_median"),
            pl.col("mean_outcome_bps").min().alias("mean_outcome_min"),
            pl.col("mean_outcome_bps").max().alias("mean_outcome_max"),
        ).sort("state")))
        print()
        print(md(ss.group_by("component", "state").agg(
            pl.len().alias("strata"), pl.col("row_n").sum().alias("rows")
        ).sort("component", "state")))
        return

    if sec == "selection":
        sc = pl.read_parquet(c / "selection_checks.parquet")
        print(md(sc.group_by("component").agg(
            pl.len().alias("strata"),
            pl.col("payoff_scale_ratio").median().alias("payoff_scale_med"),
            pl.col("payoff_scale_ratio").min().alias("payoff_scale_min"),
            pl.col("payoff_scale_ratio").max().alias("payoff_scale_max"),
            pl.col("sign_share_difference").median().alias("sign_diff_med"),
            pl.col("sign_share_difference").min().alias("sign_diff_min"),
            pl.col("sign_share_difference").max().alias("sign_diff_max"),
            pl.col("excluded_mean_median_gap").median().alias("gap_med"),
            pl.col("selected_n").sum().alias("selected_n"),
            pl.col("excluded_n").sum().alias("excluded_n"),
        ).sort("component")))
        return

    if sec == "cofill":
        cov = pl.read_csv(OUT / f"cofill_coverage_{u}.csv")
        pa = pl.read_csv(OUT / f"cofill_paired_{u}.csv")
        print(md(cov.group_by("arm_class").agg(
            pl.col("adaptive_rows").sum(), pl.col("adaptive_filled").sum(),
            pl.col("fixed_filled").sum(), pl.col("both_filled").sum(),
        )))
        print()
        print(md(pa.group_by("arm_class", "component", "orientation").agg(
            pl.len().alias("symbols"),
            pl.col("paired_n").sum().alias("paired_n"),
            pl.col("paired_mean_delta_bps").median().alias("delta_median"),
            pl.col("paired_mean_delta_bps").min().alias("delta_min"),
            pl.col("paired_mean_delta_bps").max().alias("delta_max"),
            pl.col("iid_halfwidth_bps").median().alias("iid_hw_median"),
            pl.col("same_fill_ts_share").median().alias("same_fill_ts_share"),
        ).sort("arm_class", "component", "orientation")))
        return

    if sec == "recompute":
        r = pl.read_csv(OUT / f"native_recompute_{u}.csv")
        print(md(r.group_by("arm_class", "component", "orientation").agg(
            pl.len().alias("symbols"),
            pl.col("filled_n").sum().alias("filled_n"),
            pl.col("closed_n").sum().alias("closed_n"),
            pl.col("order_created_n").sum().alias("order_created_n"),
            pl.col("no_event_n").sum().alias("no_event_n"),
            pl.col("no_feature_n").sum().alias("no_feature_n"),
            pl.col("gross_mean_bps_trades").median().alias("gross_mean_med"),
            pl.col("win_share_trades").median().alias("win_share_med"),
        ).sort("arm_class", "component", "orientation")))
        return

    raise SystemExit(f"unknown section {sec}")


if __name__ == "__main__":
    main()
