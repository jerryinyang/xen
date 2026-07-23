"""SPDR-012 analyst — script 8: dose-response, heterogeneity, distribution shape,
and two targeted falsification probes.

1. Dose-response: mean/median next |move| by decile of the V-LEVEL forecast, per clock/band,
   per symbol (monotonicity count) and normalised by the cell's own mean.
2. Heterogeneity: cross-symbol dispersion of the primary IC; I^2-style read.
3. Distribution shape: is the forecast moving the location, the dispersion, or the tail?
4. Falsification A: does the D1 range-measure advantage track bar completeness (a coverage
   artifact) — per-symbol advantage vs fraction of complete D1 slots.
5. Falsification B: within-month (level-removed) dose response — does the ladder survive?
"""
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


def deciles(x, y, k=10):
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    if len(x) < k * 8:
        return None
    q = np.quantile(x, np.linspace(0, 1, k + 1))
    q[0] -= 1e-12; q[-1] += 1e-12
    idx = np.clip(np.digitize(x, q[1:-1]), 0, k - 1)
    return np.array([[np.mean(y[idx == i]), np.median(y[idx == i]),
                      np.mean(y[idx == i] > np.quantile(y, 0.90)), (idx == i).sum()]
                     for i in range(k)])


def main() -> None:
    v = pl.read_parquet(RES / "vol_reliability.parquet")
    v = v.with_columns(pl.from_epoch("slot_start", time_unit="ns").alias("ts"))
    v = v.with_columns(pl.col("ts").dt.strftime("%Y-%m").alias("ym"))
    oos = v.filter(pl.col("oos"))

    # ---- 1. dose-response ----
    print("===== 1. DOSE-RESPONSE: next |move| by forecast decile =====")
    agg = {}
    rows = []
    for (sym, clock, band), g in oos.group_by(["symbol", "clock", "band"], maintain_order=True):
        d = deciles(g["pred__vlevel_ridge__target_abs_oo"].to_numpy(),
                    g["target_abs_oo"].to_numpy())
        if d is None:
            continue
        mu = np.nanmean(g["target_abs_oo"].to_numpy())
        agg.setdefault((clock, band), []).append(d[:, 0] / mu)
        mono = int(np.sum(np.diff(d[:, 0]) > 0))
        rows.append({"symbol": sym, "clock": clock, "band": band,
                     "d1_over_mean": d[0, 0] / mu, "d10_over_mean": d[-1, 0] / mu,
                     "ratio_d10_d1": d[-1, 0] / d[0, 0] if d[0, 0] > 0 else np.nan,
                     "monotone_steps_of_9": mono,
                     "tailrate_d1": d[0, 2], "tailrate_d10": d[-1, 2]})
    dr = pl.DataFrame(rows)
    dr.write_csv(OUT / "out_dose_response.csv")
    for k in sorted(agg):
        arr = np.vstack(agg[k])
        print(f"\n{k[1]} {k[0]}  (n_cells={arr.shape[0]}) — mean next |move| / cell mean, by decile")
        print("  " + "  ".join(f"{x:.2f}" for x in np.median(arr, axis=0)))
    print("\nper-cell summary:")
    print(dr.group_by(["band", "clock"]).agg(
        pl.len().alias("cells"),
        pl.col("d1_over_mean").median().round(3), pl.col("d10_over_mean").median().round(3),
        pl.col("ratio_d10_d1").median().round(2),
        pl.col("monotone_steps_of_9").median(),
        pl.col("tailrate_d1").median().round(3), pl.col("tailrate_d10").median().round(3),
    ).sort(["clock", "band"]).to_pandas().to_string())

    # ---- 2. heterogeneity ----
    print("\n===== 2. HETEROGENEITY of the primary IC across symbols =====")
    m = pl.read_parquet(RES / "metrics_by_cell.parquet")
    pr = m.filter((pl.col("arm") == "V-LEVEL") & (pl.col("metric") == "oos_ic")
                  & (pl.col("model") == "ridge") & (pl.col("target") == "target_abs_oo"))
    for (band, clock), g in pr.group_by(["band", "clock"], maintain_order=True):
        val = g["value"].to_numpy(); se = g["se"].to_numpy()
        w = 1 / se ** 2
        mu = np.sum(w * val) / np.sum(w)
        Q = np.sum(w * (val - mu) ** 2)
        dfree = len(val) - 1
        I2 = max(0.0, (Q - dfree) / Q) if Q > 0 else 0.0
        print(f"  {band} {clock}: n={len(val)} mean={val.mean():.3f} sd={val.std(ddof=1):.3f} "
              f"range=[{val.min():.3f},{val.max():.3f}] median_se={np.median(se):.3f} "
              f"Q={Q:.1f} (df {dfree}) I^2={I2:.2f}")

    # ---- 3. distribution shape ----
    print("\n===== 3. SHAPE: does the forecast move location, dispersion, or tail? =====")
    rows = []
    for (sym, clock, band), g in oos.group_by(["symbol", "clock", "band"], maintain_order=True):
        p = g["pred__vlevel_ridge__target_abs_oo"].to_numpy()
        y = g["target_abs_oo"].to_numpy()
        ok = np.isfinite(p) & np.isfinite(y)
        p, y = p[ok], y[ok]
        if len(y) < 150:
            continue
        hi = p >= np.quantile(p, 0.8)
        lo = p <= np.quantile(p, 0.2)
        rows.append({"symbol": sym, "clock": clock, "band": band,
                     "mean_ratio": y[hi].mean() / y[lo].mean(),
                     "median_ratio": np.median(y[hi]) / np.median(y[lo]),
                     "p90_ratio": np.quantile(y[hi], .9) / np.quantile(y[lo], .9),
                     "cv_hi": y[hi].std() / y[hi].mean(), "cv_lo": y[lo].std() / y[lo].mean()})
    sh = pl.DataFrame(rows)
    sh.write_csv(OUT / "out_shape.csv")
    print(sh.group_by(["band", "clock"]).agg(
        pl.len().alias("cells"), pl.col("mean_ratio").median().round(3),
        pl.col("median_ratio").median().round(3), pl.col("p90_ratio").median().round(3),
        pl.col("cv_hi").median().round(3), pl.col("cv_lo").median().round(3),
    ).sort(["clock", "band"]).to_pandas().to_string())

    # ---- 4. D1 range advantage vs completeness ----
    print("\n===== 4. is the D1 range advantage a coverage artifact? =====")
    diag = json.loads((RES / "cell_diagnostics.json").read_text())["cells"]
    mm = pl.read_csv(OUT / "out_measure_matrix.csv").filter(pl.col("clock") == "D1")
    mm = mm.with_columns((pl.col("ic_park_1bar") - pl.col("ic_absr_1bar")).alias("range_adv"))
    fc = []
    for sym in mm["symbol"].to_list():
        d = diag.get(f"{sym}|D1", {})
        fc.append((d.get("n_complete") or 0) / d["n_clock_slots"] if d.get("n_clock_slots") else np.nan)
    mm = mm.with_columns(pl.Series("frac_complete_slots", fc))
    print(mm.select("symbol", "band", "ic_absr_1bar", "ic_park_1bar", "range_adv",
                    "frac_complete_slots").to_pandas().to_string())
    x = mm["frac_complete_slots"].to_numpy(); y = mm["range_adv"].to_numpy()
    ok = np.isfinite(x) & np.isfinite(y)
    print("  Spearman(range advantage, fraction of complete D1 slots) =",
          round(float(stats.spearmanr(x[ok], y[ok]).statistic), 3), f"(n={ok.sum()})")
    print("  same on H1 for reference:")
    mh = pl.read_csv(OUT / "out_measure_matrix.csv").filter(pl.col("clock") == "H1")
    mh = mh.with_columns((pl.col("ic_park_1bar") - pl.col("ic_absr_1bar")).alias("range_adv"))
    print("   H1 median range advantage:", round(float(mh["range_adv"].median()), 3),
          "| D1 median:", round(float(mm["range_adv"].median()), 3))

    # ---- 5. within-month dose response ----
    print("\n===== 5. LEVEL-REMOVED dose response (ranks taken inside each calendar month) =====")
    agg2 = {}
    for (sym, clock, band), g in oos.group_by(["symbol", "clock", "band"], maintain_order=True):
        p = g["pred__vlevel_ridge__target_abs_oo"].to_numpy()
        y = g["target_abs_oo"].to_numpy()
        ym = g["ym"].to_numpy()
        ok = np.isfinite(p) & np.isfinite(y)
        p, y, ym = p[ok], y[ok], ym[ok]
        rp = np.full(len(p), np.nan); ry = np.full(len(p), np.nan)
        for u in np.unique(ym):
            msk = ym == u
            if msk.sum() < 20:
                continue
            rp[msk] = stats.rankdata(p[msk]) / (msk.sum() + 1)
            ry[msk] = y[msk] / np.mean(y[msk])
        d = deciles(rp, ry)
        if d is None:
            continue
        agg2.setdefault((clock, band), []).append(d[:, 0])
    for k in sorted(agg2):
        arr = np.vstack(agg2[k])
        print(f"  {k[1]} {k[0]} (cells={arr.shape[0]}) within-month |move| / month mean, by decile of within-month forecast rank")
        print("   " + "  ".join(f"{x:.2f}" for x in np.median(arr, axis=0)))


if __name__ == "__main__":
    main()
