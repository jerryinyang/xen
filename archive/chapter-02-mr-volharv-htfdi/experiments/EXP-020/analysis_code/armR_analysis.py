"""EXP-020 ARM R: rebalancing premium = per-bar Δ log return (rebalanced - unrebalanced twin).

Design §1/§6/§8: block bootstrap (block=60) per instrument; §6 plant check (+2 bps per
rebalance injected analysis-side, must be detected) runs BEFORE the real read; costs:
gross (engine fills, zero-spread bid=ask backtest), minus commission (FTMO pinned),
minus weekend-ceiling spread stress (predeclared ceiling; EURJPY no stress read).
Live-spread net is BLOCKED (carried blocker).
"""
from __future__ import annotations

import json

import numpy as np
import polars as pl

from common import (ALL_SYMBOLS, BLOCK_BARS, RESULTS, block_of, load_run,
                    params_table, per_bar_log_returns)

from xen.evaluation import block_bootstrap_ci, mde, round_trip_cost_bps, split_by

BPS = 1e4


def premium_series(sym: str, live_arm: str = "R") -> dict:
    """Aligned per-bar premium (bps) + per-bar cost-drag series (bps of V)."""
    r = load_run(live_arm, sym)
    tw = load_run("R-twin", sym)
    t_r, ret_r = per_bar_log_returns(r["positions"])
    t_t, ret_t = per_bar_log_returns(tw["positions"])
    # align on common timestamps (both runs share the 4h calendar; assert near-total overlap)
    common, ia, ib = np.intersect1d(t_r, t_t, return_indices=True)
    assert len(common) >= 0.99 * min(len(t_r), len(t_t)), f"{sym}: align loss"
    prem = (ret_r[ia] - ret_t[ib]) * BPS

    # per-bar traded-notional fraction (for cost drag): sum(|delta|*px)/V at the fill bar
    pos = r["positions"].filter(~pl.col("Warmup")).sort("SourceCloseTime")
    t = pos["SourceCloseTime"].to_numpy()
    v = (pos["PortUnits"] * pos["RealClose"] + pos["PortCash"]).to_numpy()
    tb = r["trade_blotter"].filter(pl.col("TradeSequence") > 1)
    turn = np.zeros(len(t))
    bi = np.searchsorted(t, tb["SourceCloseTime"].to_numpy(), side="right") - 1
    notion = (tb["PositionDelta"].abs() * tb["Price"]).to_numpy()
    for j, i in enumerate(bi):
        if 0 <= i < len(t):
            turn[i] += notion[j] / v[i]
    # align turnover to the premium bars (premium bar k corresponds to t_r[ia][k])
    turn_al = turn[np.searchsorted(t, common)]
    reb_flag = turn_al > 0
    return {"t": common, "prem_bps": prem, "turnover_frac": turn_al,
            "reb_flag": reb_flag, "n_reb_trades": tb.height,
            "init_price": float(tb["Price"][0]) if tb.height else float(pos["RealClose"][0])}


def cost_drag(sym: str, d: dict, spread_bps: float | None) -> np.ndarray:
    """Per-bar cost drag in bps of V: turnover_frac × (half-spread + per-side commission)."""
    comm_rt = round_trip_cost_bps(sym, d["init_price"], spread_pips=0.0)  # commission-only RT
    per_side = comm_rt / 2.0 + (spread_bps / 2.0 if spread_bps is not None else 0.0)
    return d["turnover_frac"] * per_side


def read_cell(sym: str, d: dict, spread_ceiling: float | None) -> dict:
    prem = d["prem_bps"]
    n = len(prem)
    out = {"symbol": sym, "block": block_of(sym), "n_bars": n,
           "n_reb_trades": d["n_reb_trades"],
           "reb_bars_frac": float(d["reb_flag"].mean()),
           "mean_turnover_per_bar": float(d["turnover_frac"].mean())}
    gross = block_bootstrap_ci(prem, block=BLOCK_BARS)
    out["gross_mean_bps_bar"] = gross["stat"]
    out["gross_ci"] = gross["ci"]
    out["mde_bps_bar"] = mde(prem, block=BLOCK_BARS)
    # commission-only net
    net_c = prem - cost_drag(sym, d, None)
    bc = block_bootstrap_ci(net_c, block=BLOCK_BARS)
    out["netcomm_mean_bps_bar"] = bc["stat"]
    out["netcomm_ci"] = bc["ci"]
    # weekend-ceiling stress
    if spread_ceiling is not None:
        net_s = prem - cost_drag(sym, d, spread_ceiling)
        bs = block_bootstrap_ci(net_s, block=BLOCK_BARS)
        out["stress_mean_bps_bar"] = bs["stat"]
        out["stress_ci"] = bs["ci"]
    else:
        out["stress_mean_bps_bar"] = None
        out["stress_ci"] = None
    # yearly split of the gross premium (2022-attribution / regime stability)
    years = d["t"].astype("datetime64[Y]").astype(str)
    ys = split_by(prem, years, block=BLOCK_BARS)
    out["yearly_gross"] = {k: {"mean": v["stat"], "ci": v["ci"], "n": v["n"]}
                           for k, v in ys.items()}
    return out


def plant_check(sym: str = "NZDUSD") -> dict:
    """§6 B-5 plant: +2 bps per rebalance-fill bar injected into the live path premium;
    the premium read must detect the offset (mean shifts by ~2·reb_frac, CI separates)."""
    d = premium_series(sym)
    prem = d["prem_bps"]
    planted = prem + 2.0 * d["reb_flag"]
    raw = block_bootstrap_ci(prem, block=BLOCK_BARS)
    pl_ = block_bootstrap_ci(planted, block=BLOCK_BARS)
    expected_shift = 2.0 * d["reb_flag"].mean()
    detected = (pl_["stat"] - raw["stat"]) > 0.5 * expected_shift and \
        pl_["ci"][0] > raw["ci"][0]
    return {"symbol": sym, "expected_shift_bps_bar": expected_shift,
            "observed_shift_bps_bar": pl_["stat"] - raw["stat"],
            "raw_ci": raw["ci"], "planted_ci": pl_["ci"],
            "detected": bool(detected)}


def main() -> None:
    par = params_table()
    spread = {r["symbol"]: r["weekend_spread_bps"] for r in par.iter_rows(named=True)}

    plants = [plant_check("NZDUSD"), plant_check("USDCAD")]
    print("PLANT CHECKS (must pass before real read):")
    for p in plants:
        print(" ", p["symbol"], "expected", round(p["expected_shift_bps_bar"], 4),
              "observed", round(p["observed_shift_bps_bar"], 4), "detected:", p["detected"])
    assert all(p["detected"] for p in plants), "plant not detected - premium read invalid"

    rows = []
    for sym in ALL_SYMBOLS:
        d = premium_series(sym)
        rows.append(read_cell(sym, d, spread.get(sym)))
        r = rows[-1]
        print(f"{sym:7s} {r['block']:3s} n={r['n_bars']} reb={r['n_reb_trades']:5d} "
              f"gross {r['gross_mean_bps_bar']:+.4f} bps/bar CI[{r['gross_ci'][0]:+.4f},"
              f"{r['gross_ci'][1]:+.4f}] netcomm {r['netcomm_mean_bps_bar']:+.4f} "
              f"stress {r['stress_mean_bps_bar'] if r['stress_mean_bps_bar'] is None else round(r['stress_mean_bps_bar'], 4)}")

    (RESULTS / "armR_premium.json").write_text(
        json.dumps({"plants": plants, "cells": rows}, indent=2, default=str))
    print("written", RESULTS / "armR_premium.json")


if __name__ == "__main__":
    main()
