"""SPDR-014 neutral re-analysis (fresh-context data-analyst).

Re-derives every verdict-bearing magnitude from raw emissions in results/.
Canonical CI tool: xen.evaluation.block_bootstrap_ci. No experiment-local analysis code imported.

Outputs:
  results/perstratum_magnitudes.json   -- full per-stratum magnitude table (nothing pooled-hidden)
  prints summary tables to stdout
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from xen.evaluation import block_bootstrap_ci

RES = Path(__file__).resolve().parent.parent / "results"
PRIMARY = dict(source="Z-VOL", z=1.5, H=12, event="E-TOUCH", h=12)
DEADBAND = 5.0


def load():
    pe = pl.read_parquet(RES / "post_event.parquet")
    ec = pl.read_parquet(RES / "expectancy_by_cell.parquet")
    controls = json.loads((RES / "controls.json").read_text())
    return pe, ec, controls


def date_of(ts_ns: pl.Series) -> pl.Series:
    return (ts_ns // (86_400 * 1_000_000_000)).cast(pl.Int64)


def ci_mean(r: np.ndarray, block: int, seed: int = 101):
    if r.size < 3:
        return dict(ci_low=float("nan"), ci_high=float("nan"), ci_low_seed_range=None)
    out = block_bootstrap_ci(r, np.mean, block=block, n_boot=4000, seed=seed, n_seeds=5)
    return dict(ci_low=out["ci"][0], ci_high=out["ci"][1],
               ci_low_seed_range=out.get("ci_low_seed_range"))


def thirds_sign(df: pl.DataFrame) -> tuple[int, list[float]]:
    """Sign consistency of mean r_h across 3 chronological thirds by event_ts."""
    d = df.sort("event_ts")
    n = d.height
    if n < 6:
        return 0, []
    means = []
    for k in range(3):
        lo, hi = n * k // 3, n * (k + 1) // 3
        means.append(float(d["r_h"][lo:hi].mean()))
    overall = float(d["r_h"].mean())
    agree = sum(1 for m in means if np.sign(m) == np.sign(overall) and overall != 0)
    return agree, means


def primary_slice(pe: pl.DataFrame, band: str) -> pl.DataFrame:
    return pe.filter(
        (pl.col("source") == PRIMARY["source"]) & (pl.col("z") == PRIMARY["z"])
        & (pl.col("H") == PRIMARY["H"]) & (pl.col("event_type") == PRIMARY["event"])
        & (pl.col("h") == PRIMARY["h"]) & (pl.col("policy") == "P-NONE")
        & (pl.col("clock") == "H1") & (pl.col("band") == band)
        & (pl.col("side") != 0)
    )


def per_symbol_primary(pe, controls, band="DESIGN"):
    sl = primary_slice(pe, band)
    rows = []
    for sym in sorted(sl["symbol"].unique().to_list()):
        d = sl.filter(pl.col("symbol") == sym)
        r = d["r_h"].to_numpy()
        r = r[~np.isnan(r)]
        n = r.size
        if n == 0:
            continue
        ndates = date_of(d["event_ts"]).n_unique()
        mean = float(np.mean(r))
        med = float(np.median(r))
        p_momo = float((r > DEADBAND).mean())
        p_mr = float((r < -DEADBAND).mean())
        p_flat = float((np.abs(r) <= DEADBAND).mean())
        agree, third_means = thirds_sign(d)
        ci = ci_mean(np.array(d.sort("event_ts")["r_h"].to_numpy()), block=12)
        sd = float(np.std(r, ddof=1)) if n > 1 else float("nan")
        mde = 2.8 * sd / np.sqrt(max(ndates, 1))
        cj = controls["by_symbol"].get(sym, {})
        mr_null = cj.get("matched_random", {}).get("null_mean_mean", float("nan"))
        ts_null = cj.get("time_shuffle", {}).get("null_mean_mean", float("nan"))
        mr_pct = cj.get("matched_random", {}).get("live_percentile", float("nan"))
        ts_pct = cj.get("time_shuffle", {}).get("live_percentile", float("nan"))
        rows.append(dict(
            symbol=sym, band=band, n_events=n, n_dates=int(ndates),
            mean_r_h=mean, median_r_h=med,
            p_momo=p_momo, p_mr=p_mr, p_flat=p_flat, p_momo_minus_mr=p_momo - p_mr,
            delta_vs_matched_random=mean - mr_null if mr_null == mr_null else float("nan"),
            delta_vs_time_shuffle=mean - ts_null if ts_null == ts_null else float("nan"),
            matched_random_null=mr_null, time_shuffle_null=ts_null,
            live_pct_matched_random=mr_pct, live_pct_time_shuffle=ts_pct,
            ci_low_mean=ci["ci_low"], ci_high_mean=ci["ci_high"],
            ci_low_seed_range=ci["ci_low_seed_range"],
            thirds_sign_agree=agree, third_means=third_means,
            std_r_h=sd, mde_bps=float(mde),
        ))
    return rows


def supported_eval(row):
    """Apply design 8.1 SUPPORTED-residual definition per symbol primary cell.
    mean Δ vs MR or TS >= +5 AND CI-low on Δ > 0 AND median Δ >= 0 AND sign consistent >=2/3 thirds.
    Δ CI-low approximated: live-mean CI-low minus null (null treated as fixed 200-seed offset).
    """
    powered = not (row["n_events"] < 80 or row["n_dates"] < 30 or row["mde_bps"] > 10)
    results = {}
    for ctrl, dcol, nullcol in [("matched_random", "delta_vs_matched_random", "matched_random_null"),
                                 ("time_shuffle", "delta_vs_time_shuffle", "time_shuffle_null")]:
        d = row[dcol]
        null = row[nullcol]
        ci_low_delta = row["ci_low_mean"] - null if null == null else float("nan")
        med_delta = row["median_r_h"] - null if null == null else float("nan")
        cond_mag = d >= 5.0
        cond_cilow = ci_low_delta > 0
        cond_med = med_delta >= 0
        cond_thirds = row["thirds_sign_agree"] >= 2
        results[ctrl] = dict(
            delta=d, ci_low_delta=ci_low_delta, median_delta=med_delta,
            cond_mag=bool(cond_mag), cond_cilow=bool(cond_cilow),
            cond_median=bool(cond_med), cond_thirds=bool(cond_thirds),
            SUPPORTED=bool(cond_mag and cond_cilow and cond_med and cond_thirds),
        )
    return dict(powered=powered, **results)


def event_rates(ec):
    """p_event by source x z x H x event (P-NONE, DESIGN); pooled dist across symbols."""
    d = ec.filter((pl.col("band") == "DESIGN") & (pl.col("policy") == "P-NONE")
                  & (pl.col("h") == 12) & (pl.col("source") == "Z-VOL"))
    agg = (d.group_by(["source", "z", "H", "event"])
           .agg(pl.col("p_event").mean().alias("p_event_mean"),
                pl.col("p_event").median().alias("p_event_median"),
                pl.col("p_event").min().alias("p_event_min"),
                pl.col("p_event").max().alias("p_event_max"),
                pl.col("symbol").n_unique().alias("n_sym"))
           .sort(["event", "z", "H"]))
    return agg


def heterogeneity(pe, band="DESIGN"):
    """Mean r_h across conditioners, pooled over symbols, primary source/z/H/event, h=12."""
    sl = primary_slice(pe, band)
    out = {}
    for col in ["vol_tercile", "mag_high", "shock_flag", "slow_regime"]:
        g = (sl.group_by(col).agg(
            pl.col("r_h").mean().alias("mean_r_h"),
            pl.col("r_h").median().alias("median_r_h"),
            (pl.col("r_h") > DEADBAND).mean().alias("p_momo"),
            (pl.col("r_h") < -DEADBAND).mean().alias("p_mr"),
            pl.len().alias("n")).sort(col))
        out[col] = g.to_dicts()
    return out


def dose_response(pe, band="DESIGN"):
    """Mean r_h across z, H, h for Z-VOL E-TOUCH P-NONE, pooled over symbols."""
    sl = pe.filter((pl.col("source") == "Z-VOL") & (pl.col("event_type") == "E-TOUCH")
                   & (pl.col("policy") == "P-NONE") & (pl.col("clock") == "H1")
                   & (pl.col("band") == band) & (pl.col("side") != 0))
    g = (sl.group_by(["z", "H", "h"]).agg(
        pl.col("r_h").mean().alias("mean_r_h"),
        pl.col("r_h").median().alias("median_r_h"),
        (pl.col("r_h") > DEADBAND).mean().alias("p_momo"),
        (pl.col("r_h") < -DEADBAND).mean().alias("p_mr"),
        pl.len().alias("n")).sort(["z", "H", "h"]))
    return g


def event_def_sens(pe, band="DESIGN"):
    sl = pe.filter((pl.col("source") == "Z-VOL") & (pl.col("z") == 1.5) & (pl.col("H") == 12)
                   & (pl.col("h") == 12) & (pl.col("policy") == "P-NONE") & (pl.col("clock") == "H1")
                   & (pl.col("band") == band) & (pl.col("side") != 0))
    g = (sl.group_by("event_type").agg(
        pl.col("r_h").mean().alias("mean_r_h"),
        pl.col("r_h").median().alias("median_r_h"),
        (pl.col("r_h") > DEADBAND).mean().alias("p_momo"),
        (pl.col("r_h") < -DEADBAND).mean().alias("p_mr"),
        pl.len().alias("n")).sort("event_type"))
    return g


def money_and_straddle(pe):
    me = pl.read_parquet(RES / "money_episodes.parquet")
    st = pl.read_parquet(RES / "straddle.parquet")
    money = (me.filter(pl.col("band") == "DESIGN").group_by(["policy", "source"]).agg(
        pl.col("partial_net_bps").mean().alias("mean_partial_net"),
        pl.col("partial_net_bps").median().alias("median_partial_net"),
        pl.col("gross_bps").mean().alias("mean_gross"),
        pl.len().alias("n")).sort(["policy", "source"]))
    strad = (st.filter(pl.col("band") == "DESIGN").group_by(["arm", "H"]).agg(
        pl.col("mean_partial_net").mean().alias("mean_pnet"),
        pl.col("median_partial_net").mean().alias("median_pnet"),
        pl.col("n_episodes").sum().alias("n")).sort(["arm", "H"]))
    return money, strad


def main():
    pe, ec, controls = load()
    print("=" * 80)
    print("PRIMARY-CELL PER-SYMBOL (DESIGN, Z-VOL z=1.5 H=12 E-TOUCH h=12, P-NONE)")
    print("=" * 80)
    rows_d = per_symbol_primary(pe, controls, "DESIGN")
    rows_c = per_symbol_primary(pe, controls, "CONFIRM")
    supp = {}
    hdr = f"{'sym':<13}{'n':>5}{'nd':>4}{'mean':>8}{'med':>8}{'pmo':>6}{'pmr':>6}{'dMR':>8}{'dTS':>8}{'ciL':>8}{'3rd':>4}{'MDE':>7}{'pow':>4}"
    print(hdr)
    for r in rows_d:
        s = supported_eval(r)
        supp[r["symbol"]] = s
        anysupp = s["matched_random"]["SUPPORTED"] or s["time_shuffle"]["SUPPORTED"]
        print(f"{r['symbol']:<13}{r['n_events']:>5}{r['n_dates']:>4}{r['mean_r_h']:>8.1f}"
              f"{r['median_r_h']:>8.1f}{r['p_momo']:>6.2f}{r['p_mr']:>6.2f}"
              f"{r['delta_vs_matched_random']:>8.1f}{r['delta_vs_time_shuffle']:>8.1f}"
              f"{r['ci_low_mean']:>8.1f}{r['thirds_sign_agree']:>4}{r['mde_bps']:>7.1f}"
              f"{('Y' if s['powered'] else 'n'):>4}"
              f"{'  <-SUPP' if anysupp else ''}")

    n_supp = sum(1 for s in supp.values()
                 if s["matched_random"]["SUPPORTED"] or s["time_shuffle"]["SUPPORTED"])
    n_pow = sum(1 for s in supp.values() if s["powered"])
    print(f"\nPowered primary symbols: {n_pow}/{len(supp)}; SUPPORTED-residual (design 8.1): {n_supp}")

    print("\n" + "=" * 80)
    print("EVENT RATES p_event by z x H x event (Z-VOL DESIGN, dist across symbols)")
    print("=" * 80)
    er = event_rates(ec)
    print(er)

    print("\n" + "=" * 80)
    print("DOSE-RESPONSE mean r_h across z x H x h (Z-VOL E-TOUCH DESIGN, pooled)")
    print("=" * 80)
    dr = dose_response(pe, "DESIGN")
    with pl.Config(tbl_rows=40):
        print(dr)

    print("\n" + "=" * 80)
    print("HETEROGENEITY (primary cell, pooled over symbols, DESIGN)")
    print("=" * 80)
    het = heterogeneity(pe, "DESIGN")
    for k, v in het.items():
        print(f"-- {k} --")
        for row in v:
            print("  ", {kk: (round(vv, 2) if isinstance(vv, float) else vv) for kk, vv in row.items()})

    print("\n" + "=" * 80)
    print("EVENT-DEF SENSITIVITY (Z-VOL z=1.5 H=12 h=12 DESIGN, pooled)")
    print("=" * 80)
    print(event_def_sens(pe, "DESIGN"))

    print("\n" + "=" * 80)
    print("MONEY + STRADDLE (DESIGN, disclosure-only, PARTIAL_FEES_FUNDING_ONLY)")
    print("=" * 80)
    money, strad = money_and_straddle(pe)
    print(money)
    print(strad)

    # DESIGN vs CONFIRM primary pooled
    print("\n" + "=" * 80)
    print("DESIGN vs CONFIRM primary-cell pooled mean r_h")
    print("=" * 80)
    for label, rows in [("DESIGN", rows_d), ("CONFIRM", rows_c)]:
        allr = np.concatenate([[]])
        means = [r["mean_r_h"] for r in rows]
        ns = [r["n_events"] for r in rows]
        wmean = np.average(means, weights=ns) if means else float("nan")
        print(f"{label}: n_sym={len(rows)} weighted-mean r_h={wmean:.2f} "
              f"simple-median-of-sym-means={np.median(means):.2f}")

    # dump full per-stratum table
    out = dict(
        primary_design=rows_d, primary_confirm=rows_c,
        supported_eval={k: v for k, v in supp.items()},
        n_powered_primary=n_pow, n_supported_residual=n_supp,
        event_rates=er.to_dicts(), dose_response=dr.to_dicts(),
        heterogeneity=het, event_def_sensitivity=event_def_sens(pe, "DESIGN").to_dicts(),
        money=money.to_dicts(), straddle=strad.to_dicts(),
    )
    (RES / "perstratum_magnitudes.json").write_text(json.dumps(out, indent=1, default=str))
    print("\nWrote results/perstratum_magnitudes.json")


if __name__ == "__main__":
    main()
