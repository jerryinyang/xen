"""EXP-022 plots (<=6). Reads results/, writes plots/. No verdict logic here."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import polars as pl

EXP = Path(__file__).resolve().parents[1]
R = EXP / "results"
P = EXP / "plots"
P.mkdir(exist_ok=True)


def substrate_heatmap(sub: pl.DataFrame):
    """1. VR(2) + lag-1 autocorr, primary build N x anchor P (mean over A,B)."""
    p = sub.filter((pl.col("build") == "N") & (pl.col("anchor") == "P"))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for ax, metric, title, center in [
            (axes[0], "VR2", "VR(2)  (<1 = mean-reverting)", 1.0),
            (axes[1], "autocorr1", "lag-1 autocorr  (level residual: 0<AR<1)", 0.0)]:
        piv = (p.with_columns((pl.col("A") + "_" + pl.col("B")).alias("AB"))
               .pivot(values=metric, index="instrument", on="AB", aggregate_function="first"))
        cols = [c for c in piv.columns if c != "instrument"]
        mat = piv.select(cols).to_numpy()
        span = np.nanmax(np.abs(mat - center)) or 1.0
        im = ax.imshow(mat, aspect="auto", cmap="RdBu_r", vmin=center - span, vmax=center + span)
        ax.set_xticks(range(len(cols))); ax.set_xticklabels(cols, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(piv.height)); ax.set_yticklabels(piv["instrument"].to_list(), fontsize=8)
        ax.set_title(title, fontsize=10)
        for (r, c), v in np.ndenumerate(mat):
            if np.isfinite(v):
                ax.text(c, r, f"{v:.2f}", ha="center", va="center", fontsize=7)
        fig.colorbar(im, ax=ax, fraction=0.046)
    fig.suptitle("EXP-022 substrate — is the equity-basket consensus residual mean-reverting? (N/P)")
    fig.tight_layout(); fig.savefig(P / "1_substrate.png", dpi=110); plt.close(fig)


def rho_by_cell(cell: pl.DataFrame):
    """2. mean rho by instrument x (A/B), single-worst hedged, primary N/P (95% block-boot CI)."""
    prim = cell.filter((pl.col("build") == "N") & (pl.col("anchor") == "P")
                       & (pl.col("C") == "single") & (pl.col("D") == "hedged")
                       & (pl.col("n_events") >= 30))
    prim = prim.with_columns((pl.col("A") + "/" + pl.col("B")).alias("cell"))
    insts = sorted(prim["instrument"].unique().to_list())
    cells = sorted(prim["cell"].unique().to_list())
    fig, ax = plt.subplots(figsize=(11, 5))
    x = np.arange(len(insts)); w = 0.8 / max(len(cells), 1)
    for j, cl in enumerate(cells):
        d = {r["instrument"]: r for r in prim.filter(pl.col("cell") == cl).iter_rows(named=True)}
        vals = np.array([d.get(i, {}).get("mean_rho_bps", np.nan) for i in insts], float)
        los = np.array([d.get(i, {}).get("ci_low_bps", np.nan) for i in insts], float)
        his = np.array([d.get(i, {}).get("ci_high_bps", np.nan) for i in insts], float)
        yerr = np.abs(np.array([vals - los, his - vals]))
        ax.bar(x + j * w, vals, w, label=cl, yerr=yerr, capsize=2, alpha=0.85)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(x + 0.3); ax.set_xticklabels(insts, rotation=30)
    ax.set_ylabel("mean rho (bps, idio forward)"); ax.legend(fontsize=8, ncol=4)
    ax.set_title("EXP-022 rho by instrument x (A/B) — single-worst hedged, N/P (n>=30)")
    fig.tight_layout(); fig.savefig(P / "2_rho_by_cell.png", dpi=110); plt.close(fig)


def signal_vs_twins(cell: pl.DataFrame):
    """3. signal vs random-index / random-timing twins, primary median/raw/single/hedged N/P."""
    pk = cell.filter((pl.col("build") == "N") & (pl.col("anchor") == "P")
                     & (pl.col("A") == "median") & (pl.col("B") == "raw")
                     & (pl.col("C") == "single") & (pl.col("D") == "hedged")
                     & (pl.col("n_events") >= 30)).sort("instrument")
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(pk.height)
    ax.bar(x - 0.25, pk["mean_rho_bps"], 0.25, label="signal", color="C0")
    ax.bar(x, pk["ri_twin_bps"], 0.25, label="random-index twin", color="C1")
    ax.bar(x + 0.25, pk["rt_twin_bps"], 0.25, label="random-timing twin", color="C2")
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels(pk["instrument"].to_list(), rotation=30)
    ax.set_ylabel("mean rho (bps)"); ax.legend()
    ax.set_title("EXP-022 signal vs twins — median/raw/single/hedged, N/P")
    fig.tight_layout(); fig.savefig(P / "3_signal_vs_twins.png", dpi=110); plt.close(fig)


def tripwire(cell: pl.DataFrame):
    """4. leak tripwire — block-permute of the (s->forward) pairing MUST collapse rho->0."""
    tw = cell.filter((pl.col("build") == "N") & (pl.col("anchor") == "P")
                     & (pl.col("C") == "single") & (pl.col("n_events") >= 30)).sort("instrument")
    fig, ax = plt.subplots(figsize=(10, 5))
    for d, off, col in [("hedged", -0.2, "C0"), ("unhedged", 0.2, "C3")]:
        t = (tw.filter(pl.col("D") == d).group_by("instrument")
             .agg(pl.col("mean_rho_bps").mean().alias("sig"),
                  pl.col("tripwire_bps").mean().alias("trip")).sort("instrument"))
        x = np.arange(t.height)
        ax.bar(x + off - 0.09, t["sig"], 0.18, color=col, alpha=0.9, label=f"{d} signal")
        ax.bar(x + off + 0.09, t["trip"], 0.18, color=col, alpha=0.4, label=f"{d} tripwire")
        ax.set_xticks(x); ax.set_xticklabels(t["instrument"].to_list(), rotation=30)
    ax.axhline(0, color="k", lw=0.8); ax.legend(fontsize=8)
    ax.set_ylabel("mean rho (bps)")
    ax.set_title("EXP-022 leak tripwire — block-permute pairing MUST collapse rho->0 (N/P)")
    fig.tight_layout(); fig.savefig(P / "4_tripwire.png", dpi=110); plt.close(fig)


def maxstat_bands(ms: pl.DataFrame):
    """5. best (min) max-stat fw_p per instrument, per construction — significance floor."""
    fig, ax = plt.subplots(figsize=(11, 5))
    constructions = (ms.with_columns((pl.col("build") + "/" + pl.col("anchor")).alias("cons")))
    order = ["N/P", "N/S", "A/P", "A/S", "R_US/P", "R_US/S", "R_EU/P", "R_EU/S",
             "R_ASIA/P", "R_ASIA/S"]
    insts = sorted(constructions["instrument"].unique().to_list())
    w = 0.8 / len(order)
    x = np.arange(len(insts))
    for j, cons in enumerate(order):
        d = {r["instrument"]: r["fw_p"] for r in
             constructions.filter(pl.col("cons") == cons).group_by("instrument")
             .agg(pl.col("fw_p_maxstat").min().alias("fw_p")).iter_rows(named=True)}
        vals = [d.get(i, np.nan) for i in insts]
        ax.bar(x + j * w, vals, w, label=cons, alpha=0.85)
    ax.axhline(0.05, color="r", lw=1, ls="--", label="0.05")
    ax.set_xticks(x + 0.4); ax.set_xticklabels(insts, rotation=30)
    ax.set_ylabel("min family-wise max-stat p (over 16 cells)"); ax.legend(fontsize=7, ncol=5)
    ax.set_title("EXP-022 max-stat significance — best cell per instrument x construction "
                 "(PRIMARY = N/P; others robustness)")
    fig.tight_layout(); fig.savefig(P / "5_maxstat.png", dpi=110); plt.close(fig)


def cross_build(cell: pl.DataFrame):
    """6. cross-build/anchor sign stability of single-worst hedged mean rho per instrument."""
    q = cell.filter((pl.col("C") == "single") & (pl.col("D") == "hedged")
                    & (pl.col("A") == "median") & (pl.col("B") == "raw")
                    & (pl.col("n_events") >= 30))
    q = q.with_columns((pl.col("build") + "/" + pl.col("anchor")).alias("cons"))
    insts = sorted(q["instrument"].unique().to_list())
    conss = ["N/P", "N/S", "A/P", "A/S", "R_US/P", "R_US/S", "R_EU/P", "R_EU/S",
             "R_ASIA/P", "R_ASIA/S"]
    mat = np.full((len(insts), len(conss)), np.nan)
    for r in q.iter_rows(named=True):
        if r["cons"] in conss:
            mat[insts.index(r["instrument"]), conss.index(r["cons"])] = r["mean_rho_bps"]
    fig, ax = plt.subplots(figsize=(11, 5))
    span = np.nanmax(np.abs(mat)) or 1.0
    im = ax.imshow(mat, aspect="auto", cmap="RdBu_r", vmin=-span, vmax=span)
    ax.set_xticks(range(len(conss))); ax.set_xticklabels(conss, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(insts))); ax.set_yticklabels(insts, fontsize=8)
    for (r, c), v in np.ndenumerate(mat):
        if np.isfinite(v):
            ax.text(c, r, f"{v:.0f}", ha="center", va="center", fontsize=7)
    fig.colorbar(im, ax=ax, fraction=0.046, label="mean rho (bps)")
    ax.set_title("EXP-022 cross-build/anchor stability — single-worst hedged mean rho (bps)")
    fig.tight_layout(); fig.savefig(P / "6_cross_build.png", dpi=110); plt.close(fig)


def main():
    sub = pl.read_parquet(R / "substrate.parquet")
    cell = pl.read_parquet(R / "cell_reads.parquet")
    ms = pl.read_parquet(R / "maxstat.parquet")
    substrate_heatmap(sub)
    rho_by_cell(cell)
    signal_vs_twins(cell)
    tripwire(cell)
    maxstat_bands(ms)
    cross_build(cell)
    print("plots written to", P)


if __name__ == "__main__":
    main()
