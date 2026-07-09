"""EXP-020 tripwire 1: live vs +1-bar-delay (NZDUSD, USDCAD; both arms).
Report collapse fractions (L-15), never binaries. ARM R: premium mean (delayed R vs the
same unrebalanced twin). ARM G: gross month-mean incl. censored MTM + realized RT mean.
"""
from __future__ import annotations

import json

import numpy as np
import polars as pl

from common import BLOCK_BARS, RESULTS, load_run

from xen.evaluation import block_bootstrap_ci, collapse_fraction

from armR_analysis import premium_series
from armG_analysis import leg_table, month_series


def armR_read(sym: str) -> dict:
    live = premium_series(sym, "R")
    dly = premium_series(sym, "R-delay1")
    bl = block_bootstrap_ci(live["prem_bps"], block=BLOCK_BARS)
    bd = block_bootstrap_ci(dly["prem_bps"], block=BLOCK_BARS)
    # paired diff on common bars
    common, ia, ib = np.intersect1d(live["t"], dly["t"], return_indices=True)
    diff = live["prem_bps"][ia] - dly["prem_bps"][ib]
    bdiff = block_bootstrap_ci(diff, block=BLOCK_BARS)
    return {"symbol": sym,
            "live_mean": bl["stat"], "live_ci": bl["ci"], "live_trades": live["n_reb_trades"],
            "delay_mean": bd["stat"], "delay_ci": bd["ci"], "delay_trades": dly["n_reb_trades"],
            "collapse_fraction": collapse_fraction(bl["stat"], bd["stat"]),
            "paired_diff_mean": bdiff["stat"], "paired_diff_ci": bdiff["ci"]}


def armG_read(sym: str) -> dict:
    out = {"symbol": sym}
    pos = load_run("G", sym)["positions"].filter(~pl.col("Warmup"))
    months = sorted(pos["SourceCloseTime"].dt.strftime("%Y-%m").unique().to_list())
    res = {}
    for key, arm in [("live", "G"), ("delay", "G-delay1")]:
        legs = leg_table(arm, sym, 0.0)
        real = legs.filter(pl.col("Censored") == 0)
        ms = month_series(legs, months)
        bb = block_bootstrap_ci(ms, block=3)
        res[key] = {"n_legs": legs.height, "n_realized": real.height,
                    "rt_mean_gross": float(real["NetBps"].mean()),
                    "total_incl_mtm": float(legs["NetBps"].sum()),
                    "month_mean": bb["stat"], "month_ci": bb["ci"]}
    out.update(res)
    out["collapse_fraction_total"] = collapse_fraction(
        res["live"]["total_incl_mtm"], res["delay"]["total_incl_mtm"])
    out["collapse_fraction_rt"] = collapse_fraction(
        res["live"]["rt_mean_gross"], res["delay"]["rt_mean_gross"])
    return out


def main() -> None:
    out = {"armR": [armR_read(s) for s in ["NZDUSD", "USDCAD"]],
           "armG": [armG_read(s) for s in ["NZDUSD", "USDCAD"]]}
    for r in out["armR"]:
        print(f"R {r['symbol']}: live {r['live_mean']:+.4f} {r['live_ci']} "
              f"delay {r['delay_mean']:+.4f} {r['delay_ci']} "
              f"cf={r['collapse_fraction']:.2f} paired_diff {r['paired_diff_mean']:+.4f} "
              f"{r['paired_diff_ci']}")
    for g in out["armG"]:
        print(f"G {g['symbol']}: live tot {g['live']['total_incl_mtm']:+.1f} "
              f"(rt {g['live']['rt_mean_gross']:+.2f}, n={g['live']['n_legs']}) "
              f"delay tot {g['delay']['total_incl_mtm']:+.1f} "
              f"(rt {g['delay']['rt_mean_gross']:+.2f}, n={g['delay']['n_legs']}) "
              f"cf_tot={g['collapse_fraction_total']:.2f} cf_rt={g['collapse_fraction_rt']:.2f}")
    (RESULTS / "tripwire_delay.json").write_text(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
