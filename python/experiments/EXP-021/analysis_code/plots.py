"""EXP-021 plots (<=5). Reads results/, writes plots/. No verdict logic here."""
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


def main():
    sub = pl.read_parquet(R / "substrate.parquet")
    cell = pl.read_parquet(R / "cell_reads.parquet")

    # 1. Substrate: VR2 heatmap (instrument x A_B), MR if <1
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for ax, metric, title in [(axes[0], "VR2", "Variance ratio VR(2)  (<1 = mean-reverting)"),
                              (axes[1], "autocorr1", "Lag-1 autocorr of residual  (<0 = MR)")]:
        piv = sub.with_columns((pl.col("A") + "_" + pl.col("B")).alias("AB")) \
                 .pivot(values=metric, index="instrument", on="AB", aggregate_function="first")
        cols = [c for c in piv.columns if c != "instrument"]
        mat = piv.select(cols).to_numpy()
        center = 1.0 if metric == "VR2" else 0.0
        im = ax.imshow(mat, aspect="auto", cmap="RdBu_r",
                       vmin=center - abs(np.nanmax(np.abs(mat - center))),
                       vmax=center + abs(np.nanmax(np.abs(mat - center))))
        ax.set_xticks(range(len(cols))); ax.set_xticklabels(cols, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(piv.height)); ax.set_yticklabels(piv["instrument"].to_list(), fontsize=8)
        ax.set_title(title, fontsize=10)
        for (r, c), v in np.ndenumerate(mat):
            ax.text(c, r, f"{v:.2f}", ha="center", va="center", fontsize=7)
        fig.colorbar(im, ax=ax, fraction=0.046)
    fig.suptitle("EXP-021 substrate — is the consensus residual mean-reverting?")
    fig.tight_layout(); fig.savefig(P / "1_substrate.png", dpi=110); plt.close(fig)

    # 2. mean rho by cell (marginal per axis), single-worst hedged primary family
    prim = cell.filter((pl.col("C") == "single") & (pl.col("D") == "hedged"))
    fig, ax = plt.subplots(figsize=(11, 5))
    prim = prim.with_columns((pl.col("A") + "/" + pl.col("B")).alias("cell"))
    insts = prim["instrument"].unique().to_list()
    cells = prim["cell"].unique().sort().to_list()
    x = np.arange(len(insts)); w = 0.8 / len(cells)
    for j, cl in enumerate(cells):
        sub_c = prim.filter(pl.col("cell") == cl).sort("instrument")
        d = {r["instrument"]: r for r in sub_c.iter_rows(named=True)}
        vals = [d.get(i, {}).get("mean_rho_bps", np.nan) for i in insts]
        los = [d.get(i, {}).get("ci_low_bps", np.nan) for i in insts]
        his = [d.get(i, {}).get("ci_high_bps", np.nan) for i in insts]
        yerr = np.array([np.array(vals) - np.array(los), np.array(his) - np.array(vals)])
        ax.bar(x + j * w, vals, w, label=cl, yerr=np.abs(yerr), capsize=2, alpha=0.85)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(x + 0.4); ax.set_xticklabels(insts, rotation=30)
    ax.set_ylabel("mean rho (bps, idio forward)"); ax.legend(fontsize=8, ncol=4)
    ax.set_title("EXP-021 rho by instrument x (A/B) — single-worst, hedged (95% block-boot CI)")
    fig.tight_layout(); fig.savefig(P / "2_rho_by_cell.png", dpi=110); plt.close(fig)

    # 3. signal vs twins (primary median/raw/single/hedged)
    pk = cell.filter((pl.col("A") == "median") & (pl.col("B") == "raw")
                     & (pl.col("C") == "single") & (pl.col("D") == "hedged")).sort("instrument")
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(pk.height)
    ax.bar(x - 0.25, pk["mean_rho_bps"], 0.25, label="signal", color="C0")
    ax.bar(x, pk["ri_twin_bps"], 0.25, label="random-index twin", color="C1")
    ax.bar(x + 0.25, pk["rt_twin_bps"], 0.25, label="random-timing twin", color="C2")
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels(pk["instrument"].to_list(), rotation=30)
    ax.set_ylabel("mean rho (bps)"); ax.legend()
    ax.set_title("EXP-021 signal vs twins — median/raw/single/hedged")
    fig.tight_layout(); fig.savefig(P / "3_signal_vs_twins.png", dpi=110); plt.close(fig)

    # 4. tripwire collapse (must -> 0) primary family single-worst
    tw = cell.filter(pl.col("C") == "single").sort("instrument")
    fig, ax = plt.subplots(figsize=(10, 5))
    for d, off, col in [("hedged", -0.2, "C0"), ("unhedged", 0.2, "C3")]:
        t = tw.filter(pl.col("D") == d).group_by("instrument").agg(
            pl.col("mean_rho_bps").mean().alias("sig"),
            pl.col("tripwire_bps").mean().alias("trip")).sort("instrument")
        x = np.arange(t.height)
        ax.bar(x + off - 0.1, t["sig"], 0.18, color=col, alpha=0.9, label=f"{d} signal")
        ax.bar(x + off + 0.1, t["trip"], 0.18, color=col, alpha=0.4, label=f"{d} tripwire")
        ax.set_xticks(x); ax.set_xticklabels(t["instrument"].to_list(), rotation=30)
    ax.axhline(0, color="k", lw=0.8); ax.legend(fontsize=8)
    ax.set_ylabel("mean rho (bps)")
    ax.set_title("EXP-021 leak tripwire — block-permute pairing MUST collapse rho->0")
    fig.tight_layout(); fig.savefig(P / "4_tripwire.png", dpi=110); plt.close(fig)

    print("plots written to", P)


if __name__ == "__main__":
    main()
