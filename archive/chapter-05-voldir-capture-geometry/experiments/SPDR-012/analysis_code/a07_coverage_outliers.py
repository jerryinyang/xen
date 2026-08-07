"""SPDR-012 analyst — script 7: coverage, band spans, completeness, and the contrary strata."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats

EXP = Path(__file__).resolve().parents[1]
RES = EXP / "results"
OUT = EXP / "analysis_code"
pl.Config.set_tbl_rows(200)
pl.Config.set_tbl_width_chars(240)


def main() -> None:
    v = pl.read_parquet(RES / "vol_reliability.parquet")
    v = v.with_columns(pl.from_epoch("slot_start", time_unit="ns").alias("ts"))
    diag = json.loads((RES / "cell_diagnostics.json").read_text())

    print("===== band spans actually scored, per symbol (H1) =====")
    sp = (v.filter(pl.col("clock") == "H1")
          .group_by(["symbol", "band"])
          .agg(pl.col("ts").min().alias("first"), pl.col("ts").max().alias("last"),
               pl.len().alias("n"), pl.col("oos").sum().alias("n_oos"))
          .sort(["band", "symbol"]))
    print(sp.to_pandas().to_string())

    print("\n===== OOS-scored span (the window the primary IC is actually measured on) =====")
    o = (v.filter(pl.col("oos"))
         .group_by(["symbol", "clock", "band"])
         .agg(pl.col("ts").min().alias("oos_first"), pl.col("ts").max().alias("oos_last"),
              pl.len().alias("n"))
         .with_columns(((pl.col("oos_last") - pl.col("oos_first")).dt.total_days()).alias("span_days")))
    print(o.group_by(["band", "clock"]).agg(
        pl.col("oos_first").min(), pl.col("oos_last").max(),
        pl.col("span_days").median().alias("median_span_days")).sort(["clock", "band"]).to_pandas().to_string())

    print("\n===== completeness / dropped bars =====")
    rows = []
    for k, d in diag["cells"].items():
        sym, clock = k.split("|")
        rows.append({"symbol": sym, "clock": clock, "status": d.get("status"),
                     "slots": d.get("n_clock_slots"), "complete": d.get("n_complete"),
                     "frac_complete": (d.get("n_complete") or 0) / d["n_clock_slots"]
                     if d.get("n_clock_slots") else None,
                     "origins": d.get("n_origins_total"),
                     "design": d.get("n_design_origins"), "confirm": d.get("n_confirm_origins"),
                     "boundary_dropped": d.get("n_boundary_dropped"),
                     "contig_design": d.get("contiguous_frac_design"),
                     "contig_confirm": d.get("contiguous_frac_confirm")})
    dg = pl.DataFrame(rows)
    dg.write_csv(OUT / "out_diagnostics.csv")
    print(dg.group_by("clock").agg(
        pl.len().alias("cells"),
        pl.col("frac_complete").median().round(4), pl.col("frac_complete").min().round(4).alias("min"),
        pl.col("boundary_dropped").sum().alias("boundary_dropped_total"),
        pl.col("contig_confirm").median().round(3),
        pl.col("contig_confirm").min().round(3).alias("min_contig_confirm"),
        pl.col("contig_design").min().round(3).alias("min_contig_design"),
    ).sort("clock").to_pandas().to_string())
    print(dg.filter(pl.col("frac_complete") < 0.99).sort("frac_complete").head(15).to_pandas().to_string())

    print("\n===== the contrary strata =====")
    m = pl.read_parquet(RES / "metrics_by_cell.parquet")
    pr = m.filter((pl.col("arm") == "V-LEVEL") & (pl.col("metric") == "oos_ic")
                  & (pl.col("model") == "ridge") & (pl.col("target") == "target_abs_oo"))
    print(pr.filter(pl.col("value") < 0).select(
        "symbol", "clock", "band", "value", "ci_low", "ci_high", "n_obs", "n_dates",
        "band_label", "band_label_detected").to_pandas().to_string())

    print("\n--- INJUSDT D1: the one CONTRADICTED cell, month by month ---")
    g = v.filter((pl.col("symbol") == "INJUSDT") & (pl.col("clock") == "D1")
                 & (pl.col("band") == "CONFIRM") & pl.col("oos"))
    g = g.with_columns(pl.col("ts").dt.strftime("%Y-%m").alias("ym"))
    out = []
    for ym, gg in g.group_by("ym", maintain_order=True):
        if gg.height < 12:
            continue
        out.append({"ym": ym[0] if isinstance(ym, tuple) else ym, "n": gg.height,
                    "ic": float(stats.spearmanr(gg["pred__vlevel_ridge__target_abs_oo"],
                                                gg["target_abs_oo"]).statistic),
                    "mean_move": float(gg["target_abs_oo"].mean()),
                    "mean_pred": float(gg["pred__vlevel_ridge__target_abs_oo"].mean())})
    print(pl.DataFrame(out).sort("ym").to_pandas().to_string())
    print("full-band IC:", stats.spearmanr(g["pred__vlevel_ridge__target_abs_oo"], g["target_abs_oo"]).statistic)
    # is the negative driven by a level trend?
    print("corr(pred, time):", stats.spearmanr(np.arange(g.height), g["pred__vlevel_ridge__target_abs_oo"]).statistic)
    print("corr(y, time):", stats.spearmanr(np.arange(g.height), g["target_abs_oo"]).statistic)

    print("\n===== power: MDE vs realised IC, primary cells =====")
    pr2 = pr.with_columns((pl.col("value") / pl.col("mde")).alias("effect_over_mde"))
    print(pr2.group_by(["band", "clock"]).agg(
        pl.col("mde").median().round(3), pl.col("value").median().round(3),
        pl.col("effect_over_mde").median().round(2),
        (pl.col("effect_over_mde") > 1).sum().alias("cells_effect_gt_mde"),
        pl.len().alias("cells")).sort(["clock", "band"]).to_pandas().to_string())


if __name__ == "__main__":
    main()
