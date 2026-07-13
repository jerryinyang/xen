"""XENA-003 plots: cost-sensitivity curve + per-leg gross decomposition."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "python" / "experiments" / "XENA-003"
RA = OUT / "results_analyst"
PL = OUT / "plots"


def main() -> None:
    PL.mkdir(parents=True, exist_ok=True)
    cs = json.loads((RA / "cost_sweep.json").read_text())
    ctl = json.loads((RA / "controls.json").read_text())
    sw = cs["spread_sweep"]

    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    for r in cs["subsets"]:
        y = [r["sweep"][str(s)]["F_point"] for s in sw]
        ax[0].plot(sw, np.clip(y, -40, None), marker="o", ms=3, lw=1, alpha=.75,
                   label=f"rank{r['rank']}" if r["rank"] < 3 else None)
    ax[0].axhline(0, color="k", lw=1)
    ax[0].axhspan(-40, 0, color="crimson", alpha=.06)
    ax[0].set_xlabel("added round-trip spread (bps) on top of the design §4 commission pins")
    ax[0].set_ylabel("portfolio gross->net log-wealth F (search band)")
    ax[0].set_title("XENA-003 cost sensitivity — all 12 certified finalists\n"
                    "(F clipped at -40; -32.2 = account ruin floor)")
    ax[0].legend(fontsize=8)
    be = [r["breakeven_extra_spread_bps"] for r in ctl["subsets"]]
    ax[0].axvline(float(np.median(be)), ls="--", color="crimson",
                  label=f"median breakeven {np.median(be):.2f} bps")
    ax[0].legend(fontsize=8)

    d = pl.read_parquet(RA / "leg_diagnostics.parquet")
    comp = {"print premium\n(limit fill vs\nfill-bar open)": d["print_bps"].mean(),
            "forward path\n(fill-bar open\n-> exit)": d["path_bps"].mean(),
            "= gross/leg": d["gross_bps"].mean(),
            "of which:\nfirst mark\n(fill -> next open)": d["first_mark_bps"].mean(),
            "rest of the\nhold period": d["exit_vs_next_open_bps"].mean()}
    cols = ["#4c78a8", "#e45756", "#54a24b", "#f58518", "#b279a2"]
    ax[1].bar(range(len(comp)), list(comp.values()), color=cols)
    ax[1].set_xticks(range(len(comp)))
    ax[1].set_xticklabels(list(comp), fontsize=7)
    ax[1].axhline(0, color="k", lw=1)
    for i, v in enumerate(comp.values()):
        ax[1].text(i, v + (.3 if v > 0 else -.6), f"{v:+.2f}", ha="center", fontsize=8)
    ax[1].set_ylabel("bps of entry price per leg")
    ax[1].set_title("Where the money is: 717,967 finalist-member legs, search band")
    fig.tight_layout()
    fig.savefig(PL / "cost_sensitivity_and_decomposition.png", dpi=140)
    print("wrote", PL / "cost_sensitivity_and_decomposition.png")


if __name__ == "__main__":
    main()
