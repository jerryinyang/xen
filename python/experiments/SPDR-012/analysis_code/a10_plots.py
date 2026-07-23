"""SPDR-012 analyst — script 10: plots for analysis.md."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import polars as pl

EXP = Path(__file__).resolve().parents[1]
OUT = EXP / "analysis_code"
PLOTS = EXP / "plots"
PLOTS.mkdir(exist_ok=True)

COL = {"H1": "#2b6cb0", "H4": "#b7791f", "D1": "#9b2c2c"}


def p1_span():
    d = pl.read_csv(OUT / "out_span_scaling.csv")
    fig, ax = plt.subplots(figsize=(7, 4.4))
    for clock in ("H1", "H4", "D1"):
        s = d.filter(pl.col("clock") == clock).sort("window_dates")
        ax.plot(s["window_dates"], s["median_ic"], "o-", color=COL[clock], label=clock)
        ax.fill_between(s["window_dates"], s["p25"], s["p75"], color=COL[clock], alpha=0.13)
    ax.axhline(0, color="k", lw=0.7)
    ax.axvline(100, color="grey", ls=":", lw=1)
    ax.text(103, ax.get_ylim()[0] + 0.02, "DESIGN-band\nOOS length", fontsize=7, color="grey")
    ax.axvline(290, color="grey", ls=":", lw=1)
    ax.text(255, ax.get_ylim()[0] + 0.02, "CONFIRM\nlength", fontsize=7, color="grey")
    ax.set_xlabel("measurement window (unique dates)")
    ax.set_ylabel("fit-free rank IC  (rv20 -> next |open->open| move)")
    ax.set_title("The headline IC scales with how long a window you measure it over\n"
                 "(CONFIRM band only, random contiguous windows, median over 15 symbols)",
                 fontsize=10)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(PLOTS / "span_scaling.png", dpi=150)
    plt.close(fig)


def p2_forest():
    d = pl.read_csv(OUT / "out_vlevel_strata.csv")
    fig, axes = plt.subplots(1, 2, figsize=(11, 6.5), sharex=True)
    for ax, band in zip(axes, ("CONFIRM", "DESIGN")):
        s = d.filter(pl.col("band") == band).sort(["clock", "value"])
        ypos = 0
        yt, yl = [], []
        for clock in ("H1", "H4", "D1"):
            g = s.filter(pl.col("clock") == clock).sort("value")
            for row in g.iter_rows(named=True):
                ax.plot([row["ci_low"], row["ci_high"]], [ypos, ypos], color=COL[clock], lw=1.4)
                ax.plot([row["value"]], [ypos], "o", color=COL[clock], ms=4)
                yt.append(ypos); yl.append(f"{row['symbol'][:12]} {clock}")
                ypos += 1
            ypos += 1
        ax.set_yticks(yt); ax.set_yticklabels(yl, fontsize=6)
        ax.axvline(0, color="k", lw=0.8)
        ax.axvline(0.10, color="green", ls="--", lw=0.8)
        ax.set_title(f"{band}\n(bar = min/max envelope over 3 blocks x 5 seeds)", fontsize=9)
        ax.set_xlabel("V-LEVEL ridge OOS rank IC")
    fig.suptitle("Per-stratum primary IC — dashed line = design 6.3 SUPPORTED threshold 0.10",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(PLOTS / "vlevel_forest.png", dpi=150)
    plt.close(fig)


def p3_dose():
    raw = {
        ("CONFIRM", "H1"): [0.52, 0.63, 0.70, 0.80, 0.88, 0.93, 1.06, 1.22, 1.39, 1.91],
        ("CONFIRM", "H4"): [0.57, 0.62, 0.70, 0.80, 0.92, 1.00, 1.02, 1.18, 1.35, 1.80],
        ("CONFIRM", "D1"): [0.71, 0.80, 0.82, 0.86, 0.94, 0.88, 0.94, 1.16, 1.07, 1.33],
    }
    lvl = {
        ("CONFIRM", "H1"): [0.64, 0.74, 0.79, 0.87, 0.91, 0.97, 1.06, 1.15, 1.26, 1.57],
        ("CONFIRM", "H4"): [0.76, 0.81, 0.83, 0.91, 0.94, 0.97, 1.07, 1.06, 1.24, 1.33],
        ("CONFIRM", "D1"): [0.84, 0.83, 0.94, 0.86, 0.97, 1.03, 0.92, 1.05, 1.08, 1.16],
    }
    x = np.arange(1, 11)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
    for ax, (data, title) in zip(axes, ((raw, "pooled (as reported)"),
                                        (lvl, "level removed (ranks inside each calendar month)"))):
        for clock in ("H1", "H4", "D1"):
            ax.plot(x, data[("CONFIRM", clock)], "o-", color=COL[clock], label=clock)
        ax.axhline(1.0, color="k", lw=0.7, ls=":")
        ax.set_xlabel("decile of the V-LEVEL forecast")
        ax.set_title(title, fontsize=9)
        ax.set_xticks(x)
    axes[0].set_ylabel("mean next |move| / cell mean")
    axes[0].legend(frameon=False)
    fig.suptitle("Dose-response, CONFIRM band (median over 15 symbols)", fontsize=10)
    fig.tight_layout()
    fig.savefig(PLOTS / "dose_response.png", dpi=150)
    plt.close(fig)


def p4_regime():
    d = pl.read_csv(OUT / "out_regime_partition.csv").filter(pl.col("band") == "CONFIRM")
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, (a, b, lab) in zip(axes, [
        ("frac_high_markov", "frac_high_hmm", "fraction of bars called HIGH"),
        ("mean_runlen_markov_high", "mean_runlen_hmm_high", "mean HIGH run length (bars)"),
        ("auc_absr_for_markov", "auc_absr_for_hmm", "AUC of |r_t| for the state"),
    ]):
        for clock in ("H1", "H4", "D1"):
            s = d.filter(pl.col("clock") == clock)
            ax.scatter(s[a], s[b], color=COL[clock], s=22, label=clock)
        lo = min(float(d[a].min()), float(d[b].min()))
        hi = max(float(d[a].max()), float(d[b].max()))
        ax.plot([lo, hi], [lo, hi], "k:", lw=0.8)
        ax.set_xlabel("V-REGIME (rolling-median split)")
        ax.set_ylabel("V-REGIME-HMM")
        ax.set_title(lab, fontsize=9)
    axes[0].legend(frameon=False, fontsize=8)
    fig.suptitle("The two regime arms are not measuring the same thing (CONFIRM band)", fontsize=10)
    fig.tight_layout()
    fig.savefig(PLOTS / "regime_partition.png", dpi=150)
    plt.close(fig)


def p5_monthly():
    d = pl.read_csv(OUT / "out_monthly_ic.csv")
    fig, ax = plt.subplots(figsize=(9, 4))
    for clock in ("H1", "H4"):
        s = d.filter((pl.col("clock") == clock) & (pl.col("n_symbols") >= 5)).sort("ym")
        ax.plot(s["ym"], s["med_ic_rv20"], "o-", color=COL[clock], label=clock)
        ax.fill_between(s["ym"], s["p25"], s["p75"], color=COL[clock], alpha=0.12)
    ax.axvline("2023-03", color="k", ls="--", lw=1)
    ax.text("2023-03", 0.34, "  DESIGN | CONFIRM", fontsize=8)
    ax.axhline(0, color="k", lw=0.7)
    ax.set_ylabel("within-month fit-free rank IC")
    ax.set_title("Within-month predictability does not step at the DESIGN/CONFIRM boundary",
                 fontsize=10)
    ax.tick_params(axis="x", rotation=70, labelsize=7)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(PLOTS / "monthly_ic.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    p1_span(); p2_forest(); p3_dose(); p4_regime(); p5_monthly()
    print("wrote:", sorted(p.name for p in PLOTS.glob("*.png")))
