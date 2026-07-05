"""EXP-019 analysis plots (4, per complexity budget)."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import polars as pl

BASE = Path(__file__).resolve().parents[1]
RES, PLOTS = BASE / "results", BASE / "plots"
HOLDS = (6, 12, 24, 48)


def main() -> None:
    PLOTS.mkdir(exist_ok=True)
    legs = pl.read_parquet(RES / "legs_live.parquet").filter(pl.col("Censored") == 0)
    bat = pl.read_csv(RES / "battery.csv")

    # 1 — NZDUSD per-seed means (pooled + per hold) vs the EXP-018 +31.5 target.
    fig, axes = plt.subplots(1, 5, figsize=(16, 3.2), sharey=True)
    nz = legs.filter(pl.col("symbol") == "NZDUSD")
    pooled = nz.group_by("seed").agg(pl.col("NetBps").mean().alias("m"))["m"].to_numpy()
    panels = [("pooled", pooled)] + [
        (f"H={h}", nz.filter(pl.col("HorizonBars") == h).group_by("seed")
         .agg(pl.col("NetBps").mean().alias("m"))["m"].to_numpy()) for h in HOLDS]
    for ax, (title, x) in zip(axes, panels):
        ax.scatter(np.zeros_like(x), x, alpha=0.6, s=18)
        ax.axhline(31.5, color="red", ls="--", lw=1, label="EXP-018 +31.5")
        ax.axhline(0, color="gray", lw=0.5)
        ax.set_title(title); ax.set_xticks([])
    axes[0].set_ylabel("per-seed mean gross bps/leg"); axes[0].legend(fontsize=7)
    fig.suptitle("NZDUSD 25-seed battery vs the EXP-018 anomaly")
    fig.tight_layout(); fig.savefig(PLOTS / "nzdusd_seed_battery.png", dpi=130); plt.close(fig)

    # 2 — battery mean / MDE across all 64 strata.
    fig, ax = plt.subplots(figsize=(12, 4))
    syms = sorted(bat["symbol"].unique().to_list())
    for i, h in enumerate(HOLDS):
        sub = bat.filter(pl.col("HorizonBars") == h).sort("symbol")
        xs = np.arange(len(syms)) + (i - 1.5) * 0.18
        ax.bar(xs, (sub["battery_mean"] / sub["battery_mde"]).to_numpy(), 0.17, label=f"H={h}")
    ax.axhline(1, color="red", ls="--", lw=0.8); ax.axhline(-1, color="red", ls="--", lw=0.8)
    ax.set_xticks(range(len(syms))); ax.set_xticklabels(syms, rotation=60, fontsize=7)
    ax.set_ylabel("battery mean / MDE"); ax.legend(fontsize=7)
    ax.set_title("Seed-battery mean in MDE units, 64 strata (|x|>1 = beyond MDE)")
    fig.tight_layout(); fig.savefig(PLOTS / "battery_strata.png", dpi=130); plt.close(fig)

    # 3 — direction split vs analytic drift at H=48.
    d = pl.read_csv(RES / "direction.csv").filter(pl.col("HorizonBars") == 48).sort("symbol")
    fig, ax = plt.subplots(figsize=(12, 4))
    x = np.arange(d.height)
    ax.scatter(x - 0.1, d["mean_bps_1"], color="tab:green", label="long observed")
    ax.scatter(x + 0.1, d["mean_bps_-1"], color="tab:red", label="short observed")
    ax.scatter(x - 0.1, d["drift_long_expected_bps"], marker="_", s=200, color="tab:green")
    ax.scatter(x + 0.1, d["drift_short_expected_bps"], marker="_", s=200, color="tab:red")
    ax.axhline(0, color="gray", lw=0.5)
    ax.set_xticks(x); ax.set_xticklabels(d["symbol"].to_list(), rotation=60, fontsize=7)
    ax.set_ylabel("mean gross bps/leg")
    ax.set_title("H=48 direction split: dots = observed, dashes = drift benchmark ±mu*H")
    ax.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(PLOTS / "direction_vs_drift_h48.png", dpi=130); plt.close(fig)

    # 4 — VR profile.
    vr = pl.read_csv(RES / "vr.csv")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for sym in sorted(vr["symbol"].unique().to_list()):
        sub = vr.filter(pl.col("symbol") == sym).sort("H")
        ax.plot(sub["H"], sub["vr"], marker="o", ms=3, lw=1, label=sym)
    ax.axhline(1.0, color="gray", ls="--", lw=0.8)
    ax.set_xlabel("H (4h bars)"); ax.set_ylabel("VR(H)")
    ax.set_title("Variance-ratio profile (substrate disclosure for HYP-002)")
    ax.legend(fontsize=6, ncol=2)
    fig.tight_layout(); fig.savefig(PLOTS / "vr_profile.png", dpi=130); plt.close(fig)
    print("plots written")


if __name__ == "__main__":
    main()
