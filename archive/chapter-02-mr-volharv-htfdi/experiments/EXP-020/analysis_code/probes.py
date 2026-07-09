"""EXP-020 falsification probes: cadence vs A1, cap dynamics, concentration,
year attribution, USDCAD/US2000 deep-dive, RW alarm scan, physicality."""
from __future__ import annotations

import json

import numpy as np
import polars as pl

from common import ALL_SYMBOLS, RESULTS, block_of, load_run, params_table

from xen.evaluation import block_bootstrap_ci

from armG_analysis import leg_table, month_series


def cadence_table() -> None:
    par = {r["symbol"]: r for r in params_table().iter_rows(named=True)}
    d = json.loads((RESULTS / "armG_grid.json").read_text())["cadence"]
    print("== ARM G fill cadence vs A1 implied crossings/month, cap dynamics (MR arm) ==")
    print(f"{'sym':7s} {'blk':3s} {'fills/mo':>8s} {'A1impl':>7s} {'short':>6s} "
          f"{'bars@cap':>8s} {'anyLeg':>7s} {'meanLegs':>8s} {'capskip':>8s} {'cens':>4s}")
    for sym in ALL_SYMBOLS:
        c = d[sym]["mr"]
        impl = par[sym]["implied_crossings_per_month"]
        print(f"{sym:7s} {block_of(sym):3s} {c['fills_per_month']:8.2f} {impl:7.1f} "
              f"{c['fills_per_month'] / impl:6.2f} {c['frac_bars_at_cap']:8.3f} "
              f"{c['frac_bars_any_leg']:7.3f} {c['mean_open_legs']:8.2f} "
              f"{c['cap_skip_events']:8d} {c['censored']:4d}")


def concentration(sym: str) -> dict:
    """Does the MR-grid total survive removing the best months / the best year?"""
    pos = load_run("G", sym)["positions"].filter(~pl.col("Warmup"))
    months = sorted(pos["SourceCloseTime"].dt.strftime("%Y-%m").unique().to_list())
    lm = leg_table("G", sym, 0.0)
    li = leg_table("G-invert", sym, 0.0)
    ms = month_series(lm, months)
    diff = ms - month_series(li, months)
    out = {"symbol": sym, "total": float(ms.sum()), "spread_total": float(diff.sum())}
    for k in (1, 3, 5):
        out[f"total_wo_top{k}"] = float(ms.sum() - np.sort(ms)[-k:].sum())
        out[f"spread_wo_top{k}"] = float(diff.sum() - np.sort(diff)[-k:].sum())
    yrs = np.array([m[:4] for m in months])
    out["yearly_mr"] = {y: float(ms[yrs == y].sum()) for y in np.unique(yrs)}
    out["yearly_spread"] = {y: float(diff[yrs == y].sum()) for y in np.unique(yrs)}
    # halves split
    h = len(ms) // 2
    b1 = block_bootstrap_ci(diff[:h], block=3)
    b2 = block_bootstrap_ci(diff[h:], block=3)
    out["spread_half1"] = {"mean": b1["stat"], "ci": b1["ci"]}
    out["spread_half2"] = {"mean": b2["stat"], "ci": b2["ci"]}
    return out


def rw_alarm_scan() -> None:
    print("== RW-block artifact alarm scan (CI-positive cells) ==")
    r = json.loads((RESULTS / "armR_premium.json").read_text())["cells"]
    g = json.loads((RESULTS / "armG_grid.json").read_text())["cells"]
    for c in r:
        if c["block"] == "RW" and c["gross_ci"][0] > 0:
            print("  ALARM armR:", c["symbol"], c["gross_mean_bps_bar"], c["gross_ci"])
    for c in g:
        ts = c.get("twin_spread_gross")
        if c["block"] == "RW" and ts and ts["month_ci"][0] > 0:
            print("  ALARM armG spread:", c["symbol"], ts["month_mean_bps"], ts["month_ci"])
    print("  (scan complete; no line above = no RW CI-positive cell)")


def physicality_armR(sym: str) -> dict:
    """What IS the R strategy: annualized path return vs its own twin, maxDD of premium."""
    from armR_analysis import premium_series
    d = premium_series(sym)
    cum = np.cumsum(d["prem_bps"]) / 1e4
    dd = float(np.max(np.maximum.accumulate(cum) - cum))
    bars_yr = 6 * 252
    return {"symbol": sym,
            "ann_premium_pct": float(np.mean(d["prem_bps"]) * bars_yr / 100),
            "premium_maxdd_pct": dd * 100,
            "ann_turnover_x": float(np.mean(d["turnover_frac"]) * bars_yr)}


def main() -> None:
    cadence_table()
    print("\n== Concentration / attribution (MR grid gross incl. MTM) ==")
    rows = [concentration(s) for s in ["USDCAD", "NZDUSD", "AUDUSD", "GBPUSD", "US2000"]]
    for c in rows:
        print(f"{c['symbol']:7s} tot {c['total']:+9.1f} wo_top3 {c['total_wo_top3']:+9.1f} "
              f"| spread {c['spread_total']:+9.1f} wo_top3 {c['spread_wo_top3']:+9.1f} "
              f"| yearly_spread {c['yearly_spread']}")
        print(f"        spread half1 {c['spread_half1']['mean']:+7.2f} {c['spread_half1']['ci']} "
              f"half2 {c['spread_half2']['mean']:+7.2f} {c['spread_half2']['ci']}")
    print()
    rw_alarm_scan()
    print("\n== ARM R physicality ==")
    phys = [physicality_armR(s) for s in ["NZDUSD", "USDCAD", "US2000", "BTCUSD"]]
    for p in phys:
        print(f"{p['symbol']:7s} ann_premium {p['ann_premium_pct']:+.3f}% "
              f"maxDD {p['premium_maxdd_pct']:.3f}% ann_turnover {p['ann_turnover_x']:.2f}x")
    (RESULTS / "probes.json").write_text(json.dumps(
        {"concentration": rows, "physicality_armR": phys}, indent=2, default=str))


if __name__ == "__main__":
    main()
