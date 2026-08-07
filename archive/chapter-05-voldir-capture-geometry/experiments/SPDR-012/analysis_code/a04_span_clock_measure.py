"""SPDR-012 analyst — script 4.

A. SPAN SCALING — pooled rank IC as a function of the measurement window length (in dates),
   inside CONFIRM only. Tests whether the DESIGN<CONFIRM gap is a property of the statistic
   rather than of the period.
B. LEVEL DECOMPOSITION — pooled IC vs within-calendar-month IC vs within-day IC vs
   within-hour-of-day IC, per cell. How much of the reported skill is level structure?
C. CLOCK — is H1 > H4 > D1 a horizon effect or a sample effect? Matched dates + matched span,
   and the bps gap re-expressed relative to the clock's own mean |move|.
D. MEASURE — is the D1 Parkinson/GK advantage a range-vs-close effect or a window-length
   effect? Compare single-bar |r| / parkinson / gk against 20-bar averages of each.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats

EXP = Path(__file__).resolve().parents[1]
RES = EXP / "results"
OUT = EXP / "analysis_code"
RNG = np.random.default_rng(1010)

pl.Config.set_tbl_rows(120)
pl.Config.set_tbl_width_chars(250)


def sp(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 15:
        return float("nan")
    return float(stats.spearmanr(a[ok], b[ok]).statistic)


def within_group_ic(x, y, grp, min_n=15):
    """Rank IC after converting both series to within-group percentile ranks."""
    ok = np.isfinite(x) & np.isfinite(y)
    x, y, grp = x[ok], y[ok], grp[ok]
    rx = np.full(len(x), np.nan)
    ry = np.full(len(y), np.nan)
    for g in np.unique(grp):
        m = grp == g
        if m.sum() < min_n:
            continue
        rx[m] = stats.rankdata(x[m]) / (m.sum() + 1)
        ry[m] = stats.rankdata(y[m]) / (m.sum() + 1)
    return sp(rx, ry), int(np.isfinite(rx).sum())


def load():
    v = pl.read_parquet(RES / "vol_reliability.parquet")
    v = v.with_columns(pl.from_epoch("slot_start", time_unit="ns").alias("ts"))
    return v.with_columns([
        pl.col("ts").dt.strftime("%Y-%m").alias("ym"),
        pl.col("ts").dt.date().cast(pl.Int32).alias("dnum"),
        pl.col("ts").dt.hour().alias("hod"),
    ])


def part_a(v: pl.DataFrame) -> None:
    print("\n===== A. SPAN SCALING (CONFIRM only, fit-free rv20 -> next |move|) =====")
    print("random contiguous date windows of length L; median over 60 draws x 15 symbols\n")
    rows = []
    c = v.filter(pl.col("band") == "CONFIRM")
    for clock in ("H1", "H4", "D1"):
        cc = c.filter(pl.col("clock") == clock)
        syms = [s for s in cc["symbol"].unique().to_list()]
        for L in (15, 30, 60, 100, 150, 220, 290):
            per = []
            for sym in syms:
                g = cc.filter(pl.col("symbol") == sym)
                d = g["dnum"].to_numpy()
                uq = np.unique(d)
                if len(uq) < L:
                    continue
                x = g["rv20"].to_numpy(); y = g["target_abs_oo"].to_numpy()
                for _ in range(60):
                    s0 = RNG.integers(0, len(uq) - L + 1)
                    m = (d >= uq[s0]) & (d <= uq[s0 + L - 1])
                    val = sp(x[m], y[m])
                    if np.isfinite(val):
                        per.append(val)
            if per:
                rows.append({"clock": clock, "window_dates": L, "n_draws": len(per),
                             "median_ic": float(np.median(per)),
                             "p25": float(np.percentile(per, 25)),
                             "p75": float(np.percentile(per, 75))})
    df = pl.DataFrame(rows)
    df.write_csv(OUT / "out_span_scaling.csv")
    print(df.pivot(values="median_ic", index="window_dates", on="clock"))
    print(df)


def part_b(v: pl.DataFrame) -> None:
    print("\n===== B. LEVEL DECOMPOSITION (per cell, OOS rows, ridge prediction) =====")
    rows = []
    oos = v.filter(pl.col("oos"))
    for (sym, clock, band), g in oos.group_by(["symbol", "clock", "band"], maintain_order=True):
        p = g["pred__vlevel_ridge__target_abs_oo"].to_numpy()
        y = g["target_abs_oo"].to_numpy()
        ym = g["ym"].to_numpy()
        dn = g["dnum"].to_numpy()
        hh = g["hod"].to_numpy()
        r = {"symbol": sym, "clock": clock, "band": band, "n": g.height,
             "ic_pooled": sp(p, y)}
        r["ic_within_month"], r["n_wm"] = within_group_ic(p, y, ym)
        if clock in ("H1", "H4"):
            r["ic_within_day"], r["n_wd"] = within_group_ic(p, y, dn, min_n=6 if clock == "H4" else 15)
        else:
            r["ic_within_day"], r["n_wd"] = float("nan"), 0
        if clock == "H1":
            r["ic_within_hod"], _ = within_group_ic(p, y, hh, min_n=30)
        else:
            r["ic_within_hod"] = float("nan")
        rows.append(r)
    df = pl.DataFrame(rows)
    df.write_csv(OUT / "out_level_decomposition.csv")
    print(df.group_by(["band", "clock"]).agg([
        pl.len().alias("cells"),
        pl.col("ic_pooled").median().round(4),
        pl.col("ic_within_month").median().round(4),
        pl.col("ic_within_day").median().round(4),
        pl.col("ic_within_hod").median().round(4),
        (pl.col("ic_within_month") / pl.col("ic_pooled")).median().round(3).alias("retain_month"),
        (pl.col("ic_within_day") / pl.col("ic_pooled")).median().round(3).alias("retain_day"),
    ]).sort(["clock", "band"]))
    print(df.sort(["clock", "band", "symbol"]))


def part_c(v: pl.DataFrame) -> None:
    print("\n===== C. CLOCK — matched dates, matched span =====")
    # C1: same date set for all three clocks, per symbol, CONFIRM band, fit-free rv20
    c = v.filter(pl.col("band") == "CONFIRM")
    rows = []
    for sym in sorted(set(c["symbol"].to_list())):
        sets = {}
        for clock in ("H1", "H4", "D1"):
            g = c.filter((pl.col("symbol") == sym) & (pl.col("clock") == clock))
            if g.height == 0:
                sets = {}
                break
            sets[clock] = g
        if not sets:
            continue
        common = set(sets["H1"]["dnum"].to_list())
        for clock in ("H4", "D1"):
            common &= set(sets[clock]["dnum"].to_list())
        if len(common) < 60:
            continue
        r = {"symbol": sym, "n_common_dates": len(common)}
        for clock in ("H1", "H4", "D1"):
            g = sets[clock].filter(pl.col("dnum").is_in(list(common)))
            r[f"ic_{clock}"] = sp(g["rv20"].to_numpy(), g["target_abs_oo"].to_numpy())
            r[f"n_{clock}"] = g.height
            r[f"meanmove_{clock}"] = float(np.nanmean(g["target_abs_oo"].to_numpy()))
        rows.append(r)
    df = pl.DataFrame(rows)
    df.write_csv(OUT / "out_clock_matched.csv")
    print("matched-date fit-free IC by clock (CONFIRM):")
    print(df)
    print(df.select([pl.col(c).median().round(4) for c in
                     ("ic_H1", "ic_H4", "ic_D1", "meanmove_H1", "meanmove_H4", "meanmove_D1")]))

    # C2: bootstrap the H1-D1 and H4-D1 differences over symbols
    for a, b in (("ic_H1", "ic_H4"), ("ic_H4", "ic_D1"), ("ic_H1", "ic_D1")):
        d = (df[a] - df[b]).to_numpy()
        d = d[np.isfinite(d)]
        bs = np.array([np.median(RNG.choice(d, len(d), replace=True)) for _ in range(4000)])
        print(f"  {a} - {b}: median {np.median(d):+.4f} "
              f"[{np.percentile(bs,2.5):+.4f},{np.percentile(bs,97.5):+.4f}]  + in {(d>0).sum()}/{len(d)}")

    # C3: regime gap normalised by the clock's own mean |move|
    m = pl.read_parquet(RES / "metrics_by_cell.parquet")
    for arm in ("V-REGIME", "V-REGIME-HMM"):
        g = (m.filter((pl.col("arm") == arm) & pl.col("metric").is_in(
            ["gap_high_low_bps", "mean_abs_oo_high_bps", "mean_abs_oo_low_bps"]))
            .pivot(values="value", index=["symbol", "clock", "band"], on="metric"))
        g = g.with_columns(
            (pl.col("gap_high_low_bps") / ((pl.col("mean_abs_oo_high_bps")
                                            + pl.col("mean_abs_oo_low_bps")) / 2)).alias("rel_gap"),
            (pl.col("mean_abs_oo_high_bps") / pl.col("mean_abs_oo_low_bps")).alias("ratio_hi_lo"),
        )
        print(f"\n  {arm}: gap in bps vs gap relative to the clock's own mean |move|")
        print(g.group_by(["band", "clock"]).agg([
            pl.len().alias("cells"),
            pl.col("gap_high_low_bps").median().round(1).alias("gap_bps"),
            pl.col("rel_gap").median().round(3),
            pl.col("ratio_hi_lo").median().round(3),
            ((pl.col("mean_abs_oo_high_bps") + pl.col("mean_abs_oo_low_bps")) / 2)
            .median().round(1).alias("mean_move_bps"),
        ]).sort(["clock", "band"]))


def part_d(v: pl.DataFrame) -> None:
    print("\n===== D. MEASURE — range vs close, single-bar vs 20-bar window =====")
    rows = []
    for (sym, clock, band), g in v.group_by(["symbol", "clock", "band"], maintain_order=True):
        g = g.sort("slot_start")
        if g.height < 120:
            continue
        park = g["parkinson"].to_numpy()
        gk = g["gk"].to_numpy()
        absr = g["abs_r"].to_numpy()
        y = g["target_abs_oo"].to_numpy()

        def roll(a, w=20):
            s = pl.Series(a)
            return s.rolling_mean(window_size=w, min_samples=w).to_numpy()

        rows.append({
            "symbol": sym, "clock": clock, "band": band, "n": g.height,
            "ic_absr_1bar": sp(absr, y),
            "ic_park_1bar": sp(park, y),
            "ic_gk_1bar": sp(gk, y),
            "ic_rv20_cc20": sp(g["rv20"].to_numpy(), y),
            "ic_park20": sp(roll(park), y),
            "ic_gk20": sp(roll(gk), y),
            "ic_absr20": sp(roll(absr), y),
            "ic_ewma": sp(g["ewma_vol"].to_numpy(), y),
        })
    df = pl.DataFrame(rows)
    df.write_csv(OUT / "out_measure_matrix.csv")
    print(df.group_by(["band", "clock"]).agg([
        pl.len().alias("cells"),
        pl.col("ic_absr_1bar").median().round(4),
        pl.col("ic_park_1bar").median().round(4),
        pl.col("ic_gk_1bar").median().round(4),
        pl.col("ic_absr20").median().round(4),
        pl.col("ic_rv20_cc20").median().round(4),
        pl.col("ic_park20").median().round(4),
        pl.col("ic_gk20").median().round(4),
        pl.col("ic_ewma").median().round(4),
    ]).sort(["clock", "band"]))
    print("\nper-symbol D1 detail:")
    print(df.filter(pl.col("clock") == "D1").sort(["band", "symbol"]))


def main() -> None:
    v = load()
    part_a(v)
    part_b(v)
    part_c(v)
    part_d(v)


if __name__ == "__main__":
    main()
