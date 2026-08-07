"""SPDR-012 analyst — script 11: residual DESIGN-vs-CONFIRM difference after span matching,
D1 within-month IC, and the three candidate bases table."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats

EXP = Path(__file__).resolve().parents[1]
RES = EXP / "results"
OUT = EXP / "analysis_code"
pl.Config.set_tbl_rows(120)
pl.Config.set_tbl_width_chars(240)


def sp(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 15:
        return np.nan
    return float(stats.spearmanr(a[ok], b[ok]).statistic)


def main() -> None:
    v = pl.read_parquet(RES / "vol_reliability.parquet")
    v = v.with_columns(pl.from_epoch("slot_start", time_unit="ns").alias("ts"))
    v = v.with_columns(pl.col("ts").dt.strftime("%Y-%m").alias("ym"),
                       pl.col("ts").dt.date().cast(pl.Int32).alias("dnum"))
    oos = v.filter(pl.col("oos"))

    print("===== A. where does the DESIGN IC sit in the CONFIRM span-matched distribution? =====")
    rows = []
    for clock in ("H1", "H4", "D1"):
        for sym in sorted(set(oos.filter((pl.col("clock") == clock)
                                         & (pl.col("band") == "DESIGN"))["symbol"].to_list())):
            dgn = oos.filter((pl.col("symbol") == sym) & (pl.col("clock") == clock)
                             & (pl.col("band") == "DESIGN"))
            cnf = oos.filter((pl.col("symbol") == sym) & (pl.col("clock") == clock)
                             & (pl.col("band") == "CONFIRM"))
            if cnf.height < 100 or dgn.height < 50:
                continue
            nd = dgn["dnum"].n_unique()
            gd = cnf["dnum"].to_numpy(); uq = np.unique(gd)
            if len(uq) <= nd:
                continue
            for tag, xcol in (("rv20", "rv20"), ("ridge", "pred__vlevel_ridge__target_abs_oo")):
                dv = sp(dgn[xcol].to_numpy(), dgn["target_abs_oo"].to_numpy())
                xs = cnf[xcol].to_numpy(); ys = cnf["target_abs_oo"].to_numpy()
                vals = []
                for s0 in range(len(uq) - nd + 1):
                    m = (gd >= uq[s0]) & (gd <= uq[s0 + nd - 1])
                    vals.append(sp(xs[m], ys[m]))
                vals = np.array([x for x in vals if np.isfinite(x)])
                rows.append({"symbol": sym, "clock": clock, "stat": tag, "design_ic": dv,
                             "confirm_median": float(np.median(vals)),
                             "percentile_of_design": float((vals < dv).mean() * 100)})
    r = pl.DataFrame(rows)
    r.write_csv(OUT / "out_span_matched_percentile.csv")
    print(r.group_by(["stat", "clock"]).agg(
        pl.len().alias("cells"),
        pl.col("design_ic").median().round(3),
        pl.col("confirm_median").median().round(3),
        pl.col("percentile_of_design").median().round(1),
        (pl.col("percentile_of_design") < 5).sum().alias("below_p5"),
        (pl.col("percentile_of_design") > 95).sum().alias("above_p95"),
    ).sort(["stat", "clock"]).to_pandas().to_string())

    print("\n===== B. D1 within-month fit-free IC (level removed) =====")
    out = []
    for (clock, band), g in v.group_by(["clock", "band"], maintain_order=True):
        per = []
        for (sym, ym), gg in g.group_by(["symbol", "ym"]):
            if gg.height < 18:
                continue
            x = sp(gg["rv20"].to_numpy(), gg["target_abs_oo"].to_numpy())
            if np.isfinite(x):
                per.append(x)
        if per:
            out.append({"clock": clock, "band": band, "n_symbol_months": len(per),
                        "median_within_month_ic": float(np.median(per)),
                        "frac_positive": float(np.mean(np.array(per) > 0))})
    print(pl.DataFrame(out).sort(["clock", "band"]).to_pandas().to_string())

    print("\n===== C. THREE CANDIDATE BASES =====")
    m = pl.read_parquet(RES / "metrics_by_cell.parquet")
    pr = m.filter((pl.col("arm") == "V-LEVEL") & (pl.col("metric") == "oos_ic")
                  & (pl.col("model") == "ridge") & (pl.col("target") == "target_abs_oo"))
    st = m.filter(pl.col("arm") == "STABILITY")
    ctrl = json.loads((RES / "controls.json").read_text())["cells"]
    n_shuf = n_blk = n_tot = 0
    for k, bands in ctrl.items():
        for b, d in bands.items():
            if not isinstance(d, dict) or d.get("status") != "OK":
                continue
            n_tot += 1
            n_shuf += int(d["TIME-SHUFFLE-PREDICTORS"].get("live_inside_central_90") is False)
            n_blk += int(d["TARGET-LABEL-DERANGEMENT"].get("one_sided_p", 1) < 0.05)

    def basis(band, labelcol, thirds):
        sub = pr.filter(pl.col("band") == band)
        sup = sub.filter(pl.col(labelcol) == "SUPPORTED")
        pw = sub.filter(pl.col(labelcol) != "UNPOWERED")
        t = st.filter(pl.col("metric") == f"n_thirds_positive_{thirds}") if thirds else None
        return {
            "basis": f"{band} / {labelcol} / thirds={thirds}",
            "clause1_symbols_SUPPORTED": len(set(sup["symbol"].to_list())),
            "clause1_of_25_pinned": f"{len(set(sup['symbol'].to_list()))}/25",
            "cells_total": sub.height, "cells_powered": pw.height, "cells_SUPPORTED": sup.height,
            "cells_IC_positive": int((sub["value"] > 0).sum()),
            "clause2_outside_shuffle_c90": f"{n_shuf}/{n_tot}",
            "clause2_block_derangement_p<0.05": f"{n_blk}/{n_tot}",
            "clause3_cells_with_>=2of3_positive_thirds": (
                int((t["value"] >= 2).sum()) if t is not None else None),
            "clause3_cells_evaluated": (t.height if t is not None else None),
        }

    for b in (basis("CONFIRM", "band_label", None),
              basis("DESIGN", "band_label", "calendar"),
              basis("DESIGN", "band_label_detected", "sample")):
        print(json.dumps(b, indent=1))


if __name__ == "__main__":
    main()
