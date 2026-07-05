"""EXP-020 ARM G: MR grid vs inverted momentum-grid twin.

Estimand (design §1): per-round-trip net bps + month-episode net incl. censored-inventory
MTM. Canonical accounting: xen.adjudication.per_leg_net (NetBps = RealizedBps - cost) —
censored legs carry their MTM in RealizedBps (marked to last close, Censored=1).
Costs: gross (cost=0), commission-only (FTMO pinned), weekend-ceiling stress (EURJPY none).
Month episode = calendar month of the leg's ENTRY (anchor-cycle attribution); realized vs
censored disclosed separately (VAL-006 survivorship discipline).
"""
from __future__ import annotations

import json

import numpy as np
import polars as pl

from common import ALL_SYMBOLS, RESULTS, block_of, load_run, params_table

from xen.adjudication import per_leg_net
from xen.evaluation import block_bootstrap_ci, mde, round_trip_cost_bps

RNG_BLOCK_MONTHS = 3  # block bootstrap over month series (episodes are ~independent; use 3)


def leg_table(arm: str, sym: str, cost_bps: float) -> pl.DataFrame:
    """per_leg_net (canonical) + censored-MTM fill-in.

    Engine emits RealizedBps=NaN for Censored=1 legs (open_at_end); their mark price is
    the emitted ExitFillPrice (= last close, FlushGridCensored). MTM disclosure =
    Direction*(Exit/Entry-1)*1e4 minus HALF the round-trip cost (entry side paid only).
    """
    ct = load_run(arm, sym)["cis_trades"]
    if ct.height == 0:
        return ct
    legs = per_leg_net(ct, cost_bps=cost_bps)
    mtm = (pl.col("Direction").cast(pl.Float64)
           * (pl.col("ExitFillPrice") / pl.col("EntryFillPrice") - 1.0) * 1e4
           - cost_bps / 2.0)
    legs = legs.with_columns(
        pl.when(pl.col("Censored") == 1).then(mtm)
        .otherwise(pl.col("NetBps")).alias("NetBps"))
    return legs.with_columns(
        pl.col("EntryTime").dt.strftime("%Y-%m").alias("month"),
        pl.col("EntryTime").dt.strftime("%Y").alias("year"))


def month_series(legs: pl.DataFrame, all_months: list[str]) -> np.ndarray:
    """Month-episode net incl. censored MTM (0 for months without legs)."""
    m = dict(legs.group_by("month").agg(pl.col("NetBps").sum()).iter_rows())
    return np.array([m.get(k, 0.0) for k in all_months])


def analyse_cell(sym: str, comm_rt: float, spread_ceiling: float | None,
                 months: list[str]) -> dict:
    out: dict = {"symbol": sym, "block": block_of(sym)}
    for arm_key, arm in [("mr", "G"), ("inv", "G-invert")]:
        for cost_key, cost in [("gross", 0.0), ("comm", comm_rt),
                               ("stress", None if spread_ceiling is None
                                else comm_rt + spread_ceiling)]:
            if cost is None:
                out[f"{arm_key}_{cost_key}"] = None
                continue
            legs = leg_table(arm, sym, cost)
            if legs.height == 0:
                out[f"{arm_key}_{cost_key}"] = {"n_legs": 0}
                continue
            real = legs.filter(pl.col("Censored") == 0)
            cens = legs.filter(pl.col("Censored") == 1)
            ms = month_series(legs, months)
            bb = block_bootstrap_ci(ms, block=RNG_BLOCK_MONTHS)
            rt = real["NetBps"].to_numpy()
            rt_ci = block_bootstrap_ci(rt, block=1) if len(rt) > 3 else None
            out[f"{arm_key}_{cost_key}"] = {
                "n_legs": legs.height, "n_realized": real.height,
                "n_censored": cens.height,
                "rt_mean_bps": float(np.mean(rt)) if len(rt) else None,
                "rt_ci": rt_ci["ci"] if rt_ci else None,
                "realized_total_bps": float(rt.sum()) if len(rt) else 0.0,
                "censored_mtm_total_bps": float(cens["NetBps"].sum()),
                "total_incl_mtm_bps": float(legs["NetBps"].sum()),
                "month_mean_bps": bb["stat"], "month_ci": bb["ci"],
                "month_mde_bps": mde(ms, block=RNG_BLOCK_MONTHS),
                "yearly_total": dict(legs.group_by("year")
                                     .agg(pl.col("NetBps").sum()).iter_rows()),
            }
    # twin spread on month series (gross): MR - inverted, paired by month
    lm = leg_table("G", sym, 0.0)
    li = leg_table("G-invert", sym, 0.0)
    if lm.height and li.height:
        diff = month_series(lm, months) - month_series(li, months)
        bb = block_bootstrap_ci(diff, block=RNG_BLOCK_MONTHS)
        out["twin_spread_gross"] = {"month_mean_bps": bb["stat"], "month_ci": bb["ci"],
                                    "mde": mde(diff, block=RNG_BLOCK_MONTHS)}
    return out


def cadence_and_cap(sym: str) -> dict:
    """Fill cadence vs A1 implied crossings; cap-bind dynamics; censoring magnitude."""
    out = {}
    for arm_key, arm in [("mr", "G"), ("inv", "G-invert")]:
        r = load_run(arm, sym)
        ct, ev = r["cis_trades"], r["events"]
        pos = r["positions"].filter(~pl.col("Warmup"))
        n_months = max(len(pos["SourceCloseTime"].dt.strftime("%Y-%m").unique()), 1)
        evc = dict(ev["EventType"].value_counts().iter_rows())
        legs_open = pos["OpenLegs"].to_numpy()
        out[arm_key] = {
            "n_legs": ct.height,
            "fills_per_month": ct.height / n_months,
            "unwinds": int(ct.filter(pl.col("ExitReason") == "grid_unwind").height),
            "censored": int(ct.filter(pl.col("Censored") == 1).height),
            "cap_skip_events": int(evc.get("cap_skip", 0)),
            "arm_skip_breach": int(evc.get("arm_skip_breach", 0)),
            "frac_bars_at_cap": float((legs_open >= 8).mean()),
            "frac_bars_any_leg": float((legs_open > 0).mean()),
            "mean_open_legs": float(legs_open.mean()),
            "max_bars_held_realized": int(ct.filter(pl.col("Censored") == 0)["BarsHeld"].max())
            if ct.filter(pl.col("Censored") == 0).height else None,
        }
    return out


def main() -> None:
    par = params_table()
    prow = {r["symbol"]: r for r in par.iter_rows(named=True)}
    cells, cadence = [], {}
    for sym in ALL_SYMBOLS:
        pos = load_run("G", sym)["positions"].filter(~pl.col("Warmup"))
        months = sorted(pos["SourceCloseTime"].dt.strftime("%Y-%m").unique().to_list())
        px = float(pos["RealClose"][0])
        comm_rt = round_trip_cost_bps(sym, px, spread_pips=0.0)
        cells.append(analyse_cell(sym, comm_rt, prow[sym]["weekend_spread_bps"], months))
        cadence[sym] = cadence_and_cap(sym)
        cadence[sym]["implied_crossings_per_month_A1"] = prow[sym][
            "implied_crossings_per_month"]
        c = cells[-1]
        g = c["mr_gross"]
        i = c["inv_gross"]
        print(f"{sym:7s} {c['block']:3s} MR legs={g['n_legs']:4d} rt_gross={g['rt_mean_bps']} "
              f"tot={g['total_incl_mtm_bps']:+9.1f} (cens {g['censored_mtm_total_bps']:+9.1f}) | "
              f"INV legs={i['n_legs']:4d} tot={i['total_incl_mtm_bps']:+9.1f} | "
              f"spread {c['twin_spread_gross']['month_mean_bps']:+7.2f} "
              f"CI{c['twin_spread_gross']['month_ci']}")
    (RESULTS / "armG_grid.json").write_text(
        json.dumps({"cells": cells, "cadence": cadence}, indent=2, default=str))
    print("written", RESULTS / "armG_grid.json")


if __name__ == "__main__":
    main()
