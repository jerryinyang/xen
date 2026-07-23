"""SPDR-012 analyst — script 3: is the DESIGN/CONFIRM difference period or sample size?

Three probes, all on the emitted per-origin rows (results/vol_reliability.parquet):

  P1  fit-free IC (rv20, ewma_vol -> next |move|) on exactly the rows the ridge OOS uses.
      If the DESIGN/CONFIRM gap survives with no model fitted, it is not an estimation effect.
  P2  CONFIRM subsampled to DESIGN-sized unique-date counts (contiguous date blocks, 400 draws)
      -> where does the DESIGN point estimate sit in that distribution?
  P3  calendar-month IC profile of the same fit-free statistic, across the whole timeline.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats

EXP = Path(__file__).resolve().parents[1]
RES = EXP / "results"
OUT = EXP / "analysis_code"
RNG = np.random.default_rng(20260723)

pl.Config.set_tbl_rows(120)
pl.Config.set_tbl_width_chars(240)


def sp(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 20:
        return float("nan")
    return float(stats.spearmanr(a[ok], b[ok]).statistic)


def main() -> None:
    v = pl.read_parquet(RES / "vol_reliability.parquet")
    v = v.with_columns([
        pl.from_epoch("slot_start", time_unit="ns").alias("ts"),
    ])
    v = v.with_columns(pl.col("ts").dt.strftime("%Y-%m").alias("ym"),
                       pl.col("ts").dt.date().alias("date"))

    oos = v.filter(pl.col("oos"))

    # ---------- P1: fit-free IC on the exact OOS rows ----------
    rows = []
    for (sym, clock, band), g in oos.group_by(["symbol", "clock", "band"], maintain_order=True):
        y = g["target_abs_oo"].to_numpy()
        rows.append({
            "symbol": sym, "clock": clock, "band": band,
            "n": g.height, "n_dates": g["date"].n_unique(),
            "ic_ridge": sp(g["pred__vlevel_ridge__target_abs_oo"].to_numpy(), y),
            "ic_rv20": sp(g["rv20"].to_numpy(), y),
            "ic_ewma": sp(g["ewma_vol"].to_numpy(), y),
            "ic_park": sp(g["parkinson"].to_numpy(), y),
            "ic_gk": sp(g["gk"].to_numpy(), y),
            "ic_absr": sp(g["abs_r"].to_numpy(), y),
        })
    ff = pl.DataFrame(rows)
    ff.write_csv(OUT / "out_fitfree_oos_ic.csv")

    print("=== P1  fit-free vs fitted IC, on the SAME OOS rows (median over symbols) ===")
    print(ff.group_by(["band", "clock"]).agg([
        pl.len().alias("cells"),
        pl.col("ic_ridge").median().round(4),
        pl.col("ic_rv20").median().round(4),
        pl.col("ic_ewma").median().round(4),
        pl.col("ic_park").median().round(4),
        pl.col("ic_gk").median().round(4),
        pl.col("ic_absr").median().round(4),
        pl.col("n_dates").median(),
    ]).sort(["clock", "band"]))

    print("\n=== P1b paired per-symbol CONFIRM - DESIGN (only symbols present in both) ===")
    d = ff.filter(pl.col("band") == "DESIGN")
    c = ff.filter(pl.col("band") == "CONFIRM")
    j = d.join(c, on=["symbol", "clock"], suffix="_C")
    for col in ("ic_ridge", "ic_rv20", "ic_ewma", "ic_park", "ic_gk", "ic_absr"):
        j = j.with_columns((pl.col(col + "_C") - pl.col(col)).alias("d_" + col))
    for clock in ("H1", "H4", "D1"):
        s = j.filter(pl.col("clock") == clock)
        line = [f"{clock}  n={s.height}"]
        for col in ("ic_ridge", "ic_rv20", "ic_ewma", "ic_park", "ic_gk"):
            dv = s["d_" + col].to_numpy()
            # paired bootstrap over symbols
            bs = np.array([np.median(RNG.choice(dv, len(dv), replace=True)) for _ in range(4000)])
            line.append(f"{col[3:]}: {np.median(dv):+.3f} [{np.percentile(bs,2.5):+.3f},"
                        f"{np.percentile(bs,97.5):+.3f}] (+ in {(dv>0).sum()}/{len(dv)})")
        print("  " + " | ".join(line))

    # ---------- P2: CONFIRM subsampled to DESIGN date counts ----------
    print("\n=== P2  CONFIRM restricted to a DESIGN-sized contiguous date window ===")
    res = []
    for clock in ("H1", "H4", "D1"):
        dd = d.filter(pl.col("clock") == clock)
        for sym in dd["symbol"].to_list():
            nd = int(dd.filter(pl.col("symbol") == sym)["n_dates"][0])
            g = oos.filter((pl.col("symbol") == sym) & (pl.col("clock") == clock)
                           & (pl.col("band") == "CONFIRM"))
            if g.height < 50:
                continue
            gdate = g["date"].cast(pl.Int32).to_numpy()  # days since epoch
            dates = np.unique(gdate)
            if len(dates) <= nd:
                continue
            gp = g["pred__vlevel_ridge__target_abs_oo"].to_numpy()
            gy = g["target_abs_oo"].to_numpy()
            grv = g["rv20"].to_numpy()
            starts = np.arange(0, len(dates) - nd + 1)
            ics_r, ics_v = [], []
            for s0 in starts:
                lo, hi = dates[s0], dates[s0 + nd - 1]
                mask = (gdate >= lo) & (gdate <= hi)
                ics_r.append(sp(gp[mask], gy[mask]))
                ics_v.append(sp(grv[mask], gy[mask]))
            ics_r = np.array(ics_r); ics_v = np.array(ics_v)
            dr = float(dd.filter(pl.col("symbol") == sym)["ic_ridge"][0])
            dv_ = float(dd.filter(pl.col("symbol") == sym)["ic_rv20"][0])
            res.append({
                "symbol": sym, "clock": clock, "design_dates": nd, "n_windows": len(starts),
                "design_ic_ridge": dr, "confirm_sub_ridge_p5": float(np.nanpercentile(ics_r, 5)),
                "confirm_sub_ridge_med": float(np.nanmedian(ics_r)),
                "confirm_sub_ridge_p95": float(np.nanpercentile(ics_r, 95)),
                "design_below_p5_ridge": bool(dr < np.nanpercentile(ics_r, 5)),
                "design_ic_rv20": dv_,
                "confirm_sub_rv20_p5": float(np.nanpercentile(ics_v, 5)),
                "confirm_sub_rv20_med": float(np.nanmedian(ics_v)),
                "confirm_sub_rv20_p95": float(np.nanpercentile(ics_v, 95)),
                "design_below_p5_rv20": bool(dv_ < np.nanpercentile(ics_v, 5)),
            })
    sub = pl.DataFrame(res)
    sub.write_csv(OUT / "out_confirm_subsampled.csv")
    print(sub.group_by("clock").agg([
        pl.len().alias("cells"),
        pl.col("design_ic_ridge").median().round(3),
        pl.col("confirm_sub_ridge_med").median().round(3),
        pl.col("confirm_sub_ridge_p5").median().round(3),
        pl.col("design_below_p5_ridge").sum().alias("design_below_confirmP5_ridge"),
        pl.col("design_ic_rv20").median().round(3),
        pl.col("confirm_sub_rv20_med").median().round(3),
        pl.col("design_below_p5_rv20").sum().alias("design_below_confirmP5_rv20"),
    ]).sort("clock"))
    print(sub)

    # ---------- P3: monthly profile ----------
    print("\n=== P3  calendar-month fit-free IC (rv20 -> next |move|), pooled across symbols ===")
    mrows = []
    for (clock, ym), g in v.group_by(["clock", "ym"], maintain_order=True):
        per = []
        for sym, gg in g.group_by("symbol"):
            if gg.height < 40:
                continue
            per.append(sp(gg["rv20"].to_numpy(), gg["target_abs_oo"].to_numpy()))
        per = [x for x in per if np.isfinite(x)]
        if not per:
            continue
        mrows.append({"clock": clock, "ym": ym, "n_symbols": len(per),
                      "med_ic_rv20": float(np.median(per)),
                      "p25": float(np.percentile(per, 25)), "p75": float(np.percentile(per, 75))})
    mp = pl.DataFrame(mrows).sort(["clock", "ym"])
    mp.write_csv(OUT / "out_monthly_ic.csv")
    for clock in ("H1", "H4", "D1"):
        print(f"\n-- {clock} --")
        print(mp.filter(pl.col("clock") == clock).select("ym", "n_symbols", "med_ic_rv20", "p25", "p75"))


if __name__ == "__main__":
    main()
