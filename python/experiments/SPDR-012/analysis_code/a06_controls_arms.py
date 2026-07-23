"""SPDR-012 analyst — script 6: controls, remaining arms, and verification of screen.md figures."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

EXP = Path(__file__).resolve().parents[1]
RES = EXP / "results"
OUT = EXP / "analysis_code"
pl.Config.set_tbl_rows(200)
pl.Config.set_tbl_width_chars(250)


def med(df, metric, **kw):
    q = df.filter(pl.col("metric") == metric)
    for k, v in kw.items():
        q = q.filter(pl.col(k) == v)
    return q


def main() -> None:
    m = pl.read_parquet(RES / "metrics_by_cell.parquet")
    c = json.loads((RES / "controls.json").read_text())["cells"]

    # ---------------- controls ----------------
    print("===== CONTROLS (per powered cell) =====")
    rows = []
    for key, bands in c.items():
        sym, clock = key.split("|")
        for band, d in bands.items():
            if not isinstance(d, dict) or d.get("status") != "OK":
                continue
            sh = d.get("TIME-SHUFFLE-PREDICTORS", {})
            bl = d.get("TARGET-LABEL-DERANGEMENT", {})
            un = d.get("TARGET-DERANGEMENT-UNRESTRICTED", {})
            rl = d.get("TARGET-FUTURE-DESTROY_REPORT_LAYER", {})
            rows.append({
                "symbol": sym, "clock": clock, "band": band, "n_obs": d.get("n_obs"),
                "live": sh.get("live"),
                "shuf_p50": sh.get("p50"), "shuf_p95": sh.get("p95"), "shuf_sd": sh.get("sd"),
                "shuf_outside_c90": sh.get("live_inside_central_90") is False,
                "shuf_p": sh.get("one_sided_p"),
                "blk_p50": bl.get("p50"), "blk_p95": bl.get("p95"),
                "blk_retention": (bl.get("p50") / sh.get("live")) if sh.get("live") else None,
                "blk_p": bl.get("one_sided_p"), "blk_above_p95": bl.get("live_above_p95"),
                "unr_p50": un.get("p50"), "unr_sd": un.get("sd"),
                "layer": rl.get("interpretation"), "z_live": rl.get("z_live"),
            })
    ct = pl.DataFrame(rows)
    ct.write_csv(OUT / "out_controls.csv")
    print("cells:", ct.height)
    print(ct.group_by(["band", "clock"]).agg([
        pl.len().alias("cells"),
        pl.col("live").median().round(3),
        pl.col("shuf_p50").median().round(3), pl.col("shuf_p95").median().round(3),
        pl.col("shuf_outside_c90").sum().alias("outside_shuffle_c90"),
        pl.col("blk_p50").median().round(3),
        pl.col("blk_retention").median().round(3),
        pl.col("blk_above_p95").sum().alias("above_block_p95"),
        pl.col("unr_p50").median().round(4),
    ]).sort(["clock", "band"]).to_pandas().to_string())
    print("\ntotals: outside shuffle central-90 =", int(ct["shuf_outside_c90"].sum()), "/", ct.height,
          "| block derangement live>p95 =", int(ct["blk_above_p95"].sum()), "/", ct.height,
          "| block p<0.05 =", int((ct["blk_p"] < 0.05).sum()))
    print("block-form retention (null p50 / live): overall median",
          round(float(ct["blk_retention"].median()), 3),
          "min", round(float(ct["blk_retention"].min()), 3),
          "max", round(float(ct["blk_retention"].max()), 3))
    print("future-destroy report layer:", ct.group_by("layer").agg(pl.len()).to_dicts())
    print("\ncells NOT outside the shuffle central 90%:")
    print(ct.filter(~pl.col("shuf_outside_c90")).select(
        "symbol", "clock", "band", "live", "shuf_p95", "n_obs").to_pandas().to_string())

    # ---------------- V-CLOCK ----------------
    print("\n===== V-CLOCK =====")
    vc = m.filter(pl.col("arm") == "V-CLOCK")
    print(vc.filter(pl.col("metric").str.starts_with("incr_r2"))
          .group_by(["band", "clock", "metric"])
          .agg(pl.len().alias("cells"), pl.col("value").median().round(4),
               pl.col("value").min().round(4).alias("min"),
               pl.col("value").max().round(4).alias("max"),
               (pl.col("value") > 0).sum().alias("n_positive"))
          .sort(["clock", "band", "metric"]).to_pandas().to_string())
    print("\nbase R2 (V-LEVEL only) vs plus terms:")
    print(vc.filter(pl.col("metric").str.starts_with("oos_r2"))
          .group_by(["band", "clock", "metric"]).agg(pl.col("value").median().round(4))
          .sort(["clock", "band", "metric"]).to_pandas().to_string())

    # ---------------- V-TAIL ----------------
    print("\n===== V-TAIL =====")
    vt = m.filter(pl.col("arm") == "V-TAIL")
    print(vt.filter(pl.col("metric").is_in(
        ["exceed_diff_p90", "exceed_diff_p95", "exceed_p90_high", "exceed_p90_low",
         "exceed_p95_high", "exceed_p95_low"]))
        .group_by(["band", "clock", "metric"])
        .agg(pl.len().alias("cells"), pl.col("value").median().round(4),
             (pl.col("ci_low") > 0).sum().alias("ci_low_gt0"))
        .sort(["clock", "band", "metric"]).to_pandas().to_string())

    # ---------------- V-XS ----------------
    print("\n===== V-XS =====")
    vx = m.filter(pl.col("arm") == "V-XS")
    print(vx.filter(pl.col("metric").is_in(["xs_gap_top_minus_bottom_bps", "xs_ic_rank_vs_target"]))
          .group_by(["band", "clock", "metric", pl.col("symbol") == "POOLED"])
          .agg(pl.len().alias("cells"), pl.col("value").median().round(3),
               pl.col("value").min().round(3).alias("min"), pl.col("value").max().round(3).alias("max"),
               (pl.col("ci_low") > 0).sum().alias("ci_low_gt0"))
          .sort(["clock", "band", "metric"]).to_pandas().to_string())

    # ---------------- V-PERSIST ----------------
    print("\n===== V-PERSIST =====")
    vp = m.filter(pl.col("arm") == "V-PERSIST")
    print(vp.filter(pl.col("metric").is_in(
        ["autocorr_abs_r_lag1", "autocorr_abs_r_lag2", "autocorr_abs_r_lag3", "autocorr_abs_r_lag5",
         "autocorr_rv20_lag1", "half_life_abs_r_bars", "ar1_slope_abs_r",
         "ic_lag1_rv20_vs_target", "ic_abs_r_lag1_persist"]))
        .group_by(["band", "clock", "metric"]).agg(pl.col("value").median().round(3), pl.len())
        .sort(["clock", "band", "metric"]).to_pandas().to_string())

    # ---------------- V-MEASURE emitted ICs (verify screen.md 4) ----------------
    print("\n===== V-MEASURE emitted univariate IC (screen.md 4) =====")
    vm = m.filter((pl.col("arm") == "V-MEASURE") & pl.col("metric").str.starts_with("ic_"))
    print(vm.group_by(["band", "clock", "metric"])
          .agg(pl.len().alias("cells"), pl.col("value").median().round(4),
               (pl.col("ci_low") > 0).sum().alias("ci_low_gt0"))
          .sort(["clock", "band", "metric"]).to_pandas().to_string())

    # ---------------- V-LEVEL model comparison + dmae (verify screen.md 3) ----------------
    print("\n===== V-LEVEL model comparison, target_abs_oo =====")
    vl = m.filter((pl.col("arm") == "V-LEVEL") & (pl.col("target") == "target_abs_oo"))
    print(vl.filter(pl.col("metric") == "oos_ic").group_by(["band", "clock", "model"])
          .agg(pl.col("value").median().round(4), pl.len())
          .sort(["clock", "band", "model"]).to_pandas().to_string())
    print("\ndmae_vs_uncond (bps) and oos_r2_vs_uncond:")
    for met in ("dmae_vs_uncond", "oos_r2_vs_uncond"):
        print(met)
        print(vl.filter((pl.col("metric") == met) & (pl.col("model") == "ridge"))
              .group_by(["band", "clock"]).agg(pl.len().alias("cells"),
                                               pl.col("value").median().round(4),
                                               (pl.col("ci_low") > 0).sum().alias("ci_low_gt0"))
              .sort(["clock", "band"]).to_pandas().to_string())

    # contiguity
    print("\n===== contiguity + contiguous-subset IC =====")
    print(m.filter(pl.col("metric") == "target_contiguous_frac")
          .group_by(["band", "clock"]).agg(pl.col("value").median().round(3),
                                           pl.col("value").min().round(3).alias("min"))
          .sort(["clock", "band"]).to_pandas().to_string())
    a = m.filter(pl.col("metric") == "oos_ic_contiguous_subset").select(
        "symbol", "clock", "band", pl.col("value").alias("ic_contig"))
    b = vl.filter((pl.col("metric") == "oos_ic") & (pl.col("model") == "ridge")).select(
        "symbol", "clock", "band", pl.col("value").alias("ic_all"))
    j = a.join(b, on=["symbol", "clock", "band"])
    print(j.group_by(["band", "clock"]).agg(pl.col("ic_contig").median().round(4),
                                            pl.col("ic_all").median().round(4),
                                            (pl.col("ic_contig") - pl.col("ic_all")).median().round(4)
                                            .alias("delta"))
          .sort(["clock", "band"]).to_pandas().to_string())

    # zero-origin placeholder rows
    print("\n===== cell_status placeholder rows =====")
    print(m.filter(pl.col("metric") == "cell_status")
          .select("symbol", "clock", "band", "arm", "band_label", "note").unique()
          .sort("symbol").to_pandas().to_string()[:2500])


if __name__ == "__main__":
    main()
