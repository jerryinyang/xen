"""EXP-020 plots (6): ARM R premium forest; ARM R cumulative premium (MR block);
ARM G twin-spread forest; ARM G cumulative month net MR vs INV (key cells);
fill cadence vs A1 implied; realized vs censored-MTM decomposition."""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import polars as pl

from common import ALL_SYMBOLS, PLOTS, RESULTS, block_of, load_run, params_table
from armG_analysis import leg_table, month_series
from armR_analysis import premium_series

C_MR, C_RW, C_MID = "#4269d0", "#ff725c", "#efb118"  # fixed block colors
C_LIVE, C_TWIN = "#4269d0", "#9c6b4e"
BLOCK_COLOR = {"MR": C_MR, "RW": C_RW, "mid": C_MID}

plt.rcParams.update({"figure.dpi": 130, "axes.grid": True, "grid.alpha": 0.25,
                     "axes.spines.top": False, "axes.spines.right": False})


def forest(ax, rows, mean_key, ci_key, title, xlabel):
    ys = np.arange(len(rows))[::-1]
    for y, r in zip(ys, rows):
        c = BLOCK_COLOR[r["block"]]
        ci = r[ci_key]
        ax.plot(ci, [y, y], color=c, lw=2)
        ax.plot([r[mean_key]], [y], "o", color=c, ms=6)
    ax.axvline(0, color="0.4", lw=1)
    ax.set_yticks(ys)
    ax.set_yticklabels([f"{r['symbol']} ({r['block']})" for r in rows], fontsize=8)
    ax.set_title(title, fontsize=10)
    ax.set_xlabel(xlabel, fontsize=9)


def main() -> None:
    PLOTS.mkdir(exist_ok=True)
    armR = json.loads((RESULTS / "armR_premium.json").read_text())["cells"]
    armG = json.loads((RESULTS / "armG_grid.json").read_text())
    par = {r["symbol"]: r for r in params_table().iter_rows(named=True)}

    # 1: ARM R gross premium forest
    fig, ax = plt.subplots(figsize=(7, 6))
    forest(ax, armR, "gross_mean_bps_bar", "gross_ci",
           "ARM R: gross rebalancing premium (rebalanced - twin), block bootstrap 95% CI",
           "bps per 4h bar")
    fig.tight_layout(); fig.savefig(PLOTS / "armR_premium_forest.png"); plt.close(fig)

    # 2: ARM R cumulative premium, MR block
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for sym in ["NZDUSD", "AUDUSD", "GBPUSD", "USDCAD"]:
        d = premium_series(sym)
        ax.plot(d["t"], np.cumsum(d["prem_bps"]), lw=1.4, label=sym)
    ax.axhline(0, color="0.4", lw=1)
    ax.legend(fontsize=8); ax.set_title("ARM R: cumulative gross premium, MR block", fontsize=10)
    ax.set_ylabel("cumulative bps")
    fig.tight_layout(); fig.savefig(PLOTS / "armR_cum_premium_mr.png"); plt.close(fig)

    # 3: ARM G twin-spread forest (month mean, MR grid - inverted twin, gross incl MTM)
    rows = [{"symbol": c["symbol"], "block": c["block"],
             "m": c["twin_spread_gross"]["month_mean_bps"],
             "ci": c["twin_spread_gross"]["month_ci"]} for c in armG["cells"]]
    fig, ax = plt.subplots(figsize=(7, 6))
    forest(ax, rows, "m", "ci",
           "ARM G: twin spread (MR grid - momentum grid), monthly net incl. MTM",
           "bps per month")
    ax.set_xlim(-900, 1900)
    fig.tight_layout(); fig.savefig(PLOTS / "armG_twin_spread_forest.png"); plt.close(fig)

    # 4: ARM G cumulative month net MR vs INV, four key cells
    fig, axes = plt.subplots(2, 2, figsize=(10, 6), sharex=False)
    for ax, sym in zip(axes.flat, ["USDCAD", "NZDUSD", "AUDUSD", "US2000"]):
        pos = load_run("G", sym)["positions"].filter(~pl.col("Warmup"))
        months = sorted(pos["SourceCloseTime"].dt.strftime("%Y-%m").unique().to_list())
        x = np.arange(len(months))
        ax.plot(x, np.cumsum(month_series(leg_table("G", sym, 0.0), months)),
                color=C_LIVE, lw=1.6, label="MR grid")
        ax.plot(x, np.cumsum(month_series(leg_table("G-invert", sym, 0.0), months)),
                color=C_TWIN, lw=1.6, label="momentum twin")
        ax.axhline(0, color="0.4", lw=0.8)
        ax.set_title(f"{sym} ({block_of(sym)})", fontsize=9)
        step = max(len(months) // 5, 1)
        ax.set_xticks(x[::step]); ax.set_xticklabels(months[::step], fontsize=7)
    axes.flat[0].legend(fontsize=8)
    fig.suptitle("ARM G: cumulative monthly net (gross, incl. censored MTM)", fontsize=11)
    fig.tight_layout(); fig.savefig(PLOTS / "armG_cum_month_net.png"); plt.close(fig)

    # 5: fill cadence vs A1 implied
    fig, ax = plt.subplots(figsize=(8, 4.5))
    syms = ALL_SYMBOLS
    act = [armG["cadence"][s]["mr"]["fills_per_month"] for s in syms]
    imp = [par[s]["implied_crossings_per_month"] for s in syms]
    x = np.arange(len(syms))
    ax.bar(x - 0.2, imp, 0.4, color="0.7", label="A1 implied crossings/mo")
    ax.bar(x + 0.2, act, 0.4, color=[BLOCK_COLOR[block_of(s)] for s in syms],
           label="actual fills/mo (MR grid)")
    ax.set_xticks(x); ax.set_xticklabels(syms, rotation=60, fontsize=7)
    ax.legend(fontsize=8)
    ax.set_title("ARM G: actual fill cadence vs design-implied crossings (cap-bind collapse)",
                 fontsize=10)
    fig.tight_layout(); fig.savefig(PLOTS / "armG_cadence_vs_implied.png"); plt.close(fig)

    # 6: realized vs censored MTM decomposition (MR grid, gross)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    real, cens = [], []
    for s in syms:
        legs = leg_table("G", s, 0.0)
        real.append(float(legs.filter(pl.col("Censored") == 0)["NetBps"].sum()))
        cens.append(float(legs.filter(pl.col("Censored") == 1)["NetBps"].sum()))
    ax.bar(x, real, 0.6, color="#6cc5b0", label="realized round trips")
    ax.bar(x, cens, 0.6, bottom=0, color="#a463f2", alpha=0.85,
           label="censored end-inventory MTM")
    tot = np.array(real) + np.array(cens)
    ax.plot(x, tot, "k_", ms=14, label="total incl. MTM")
    ax.axhline(0, color="0.4", lw=1)
    ax.set_xticks(x); ax.set_xticklabels(syms, rotation=60, fontsize=7)
    ax.legend(fontsize=8); ax.set_ylabel("bps (sum over TRAIN)")
    ax.set_title("ARM G MR grid: realized harvest vs censored-inventory MTM (survivorship view)",
                 fontsize=10)
    fig.tight_layout(); fig.savefig(PLOTS / "armG_realized_vs_censored.png"); plt.close(fig)
    print("plots written to", PLOTS)


if __name__ == "__main__":
    main()
