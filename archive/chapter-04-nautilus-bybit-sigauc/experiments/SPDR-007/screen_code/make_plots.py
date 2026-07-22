"""SPDR-007 plots (≤5, design §9). Reads the emitted results/; recomputes nothing.

Run after spine_screen.py:  python python/experiments/SPDR-007/screen_code/make_plots.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[4]
RESULTS = ROOT / "python" / "experiments" / "SPDR-007" / "results"
PLOTS = ROOT / "python" / "experiments" / "SPDR-007" / "plots"


def _load(name: str) -> dict:
    return json.loads((RESULTS / name).read_text())


def plot_mfe_distribution() -> None:
    de = pl.read_parquet(RESULTS / "spine_events_DESIGN.parquet")
    ce = pl.read_parquet(RESULTS / "spine_events_CONFIRM.parquet")
    freeze = _load("protection_freeze.json")
    fig, ax = plt.subplots(figsize=(9, 5))
    d = de["mfe_norm"].drop_nulls().to_numpy()
    c = ce["mfe_norm"].drop_nulls().to_numpy()
    bins = np.linspace(0, np.quantile(np.concatenate([d, c]), 0.97), 60)
    ax.hist(d, bins=bins, density=True, alpha=0.5, label=f"DESIGN (n={len(d)})")
    ax.hist(c, bins=bins, density=True, alpha=0.5, label=f"CONFIRM (n={len(c)})")
    for p in (0.65, 0.70):
        q = freeze["pooled"][f"p{int(p*100)}"]["protection_ibw"]
        ax.axvline(q, ls="--", label=f"Protection p={p} (q̂={q:.2f} IBw)")
    ax.set_xlabel("MFE / IB width (favourable excursion, IB-width units)")
    ax.set_ylabel("density")
    ax.set_title("S2 favourable-excursion distribution + Protection Level (pooled)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS / "01_mfe_distribution_protection.png", dpi=140)
    plt.close(fig)


def plot_calibration() -> None:
    r1 = _load("layers.json")["R1_calibration_master_gate"]["pooled"]
    ps = sorted(float(k[1:]) / 100 for k in r1)
    realised = [r1[f"p{int(p*100)}"]["realised_hit_rate"] for p in ps]
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot([0.6, 0.75], [0.6, 0.75], "k--", alpha=0.5, label="perfect reproduction")
    ax.scatter(ps, realised, s=80, zorder=3)
    for p, r in zip(ps, realised):
        ax.annotate(f"  p={p}: realised {r:.3f}", (p, r), fontsize=9)
    ax.set_xlabel("nominal hit probability p")
    ax.set_ylabel("realised CONFIRM hit rate P(MFE ≥ q̂)")
    ax.set_title("R1 master gate — Protection-quantile reproduction (TRAIN-internal)")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(PLOTS / "02_calibration_master_gate.png", dpi=140)
    plt.close(fig)


def plot_regime_terciles() -> None:
    de = pl.read_parquet(RESULTS / "spine_events_DESIGN.parquet").drop_nulls("ib_width_pctl")
    d = de.with_columns(
        pl.when(pl.col("ib_width_pctl") <= 1 / 3).then(pl.lit("NARROW"))
        .when(pl.col("ib_width_pctl") <= 2 / 3).then(pl.lit("MID"))
        .otherwise(pl.lit("WIDE")).alias("regime")
    )
    order = ["NARROW", "MID", "WIDE"]
    data = [d.filter(pl.col("regime") == r)["mfe_norm"].drop_nulls().to_numpy() for r in order]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.boxplot(data, tick_labels=[f"{r}\n(n={len(x)})" for r, x in zip(order, data)], showfliers=False)
    ax.set_ylabel("MFE / IB width")
    ax.set_title("R3 regime — favourable excursion by IB-width tercile (causal ≤ t−1)")
    fig.tight_layout()
    fig.savefig(PLOTS / "03_regime_terciles.png", dpi=140)
    plt.close(fig)


def plot_coherence() -> None:
    r4 = _load("layers.json")["R4_coherence"]
    if r4.get("unpowered"):
        return
    de = pl.read_parquet(RESULTS / "spine_events_DESIGN.parquet").drop_nulls("coh")
    lo, hi = r4["tercile_edges"]
    d = de.with_columns(
        pl.when(pl.col("coh") <= lo).then(pl.lit("LOW"))
        .when(pl.col("coh") <= hi).then(pl.lit("MID")).otherwise(pl.lit("HIGH")).alias("ct")
    )
    order = ["LOW", "MID", "HIGH"]
    data = [d.filter(pl.col("ct") == c)["mfe_norm"].drop_nulls().to_numpy() for c in order]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.boxplot(data, tick_labels=[f"{c}\n(n={len(x)})" for c, x in zip(order, data)], showfliers=False)
    ax.set_ylabel("MFE / IB width")
    ax.set_title(f"R4 Δ-coherence terciles — contrast {r4['mfe_norm_contrast']:+.3f} IBw (HIGH−LOW)")
    fig.tight_layout()
    fig.savefig(PLOTS / "04_coherence_terciles.png", dpi=140)
    plt.close(fig)


def plot_floor() -> None:
    floor = _load("floor_table.json")["per_symbol"]
    freeze = _load("protection_freeze.json")
    rows = []
    for s, v in floor.items():
        w = v.get("median_ib_width_bps")
        if w is None:
            continue
        tp1_bps = freeze["pooled"]["p70"]["protection_ibw"] * w
        rows.append((s, v["cost_floor_bps"], tp1_bps))
    rows.sort(key=lambda r: r[2], reverse=True)
    rows = rows[:40]
    syms = [r[0] for r in rows]
    fig, ax = plt.subplots(figsize=(11, 5))
    x = np.arange(len(syms))
    ax.bar(x, [r[2] for r in rows], color="steelblue", label="TP1 (Protection, p70) bps")
    ax.plot(x, [r[1] for r in rows], "r_", ms=12, mew=2, label="cost floor bps")
    ax.set_xticks(x)
    ax.set_xticklabels(syms, rotation=90, fontsize=6)
    ax.set_ylabel("bps")
    ax.set_title("R0 money floor — TP1 (pooled p70) vs round-trip cost floor per symbol (top 40 by TP1)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS / "05_money_floor.png", dpi=140)
    plt.close(fig)


def main() -> None:
    PLOTS.mkdir(parents=True, exist_ok=True)
    for fn in (plot_mfe_distribution, plot_calibration, plot_regime_terciles,
               plot_coherence, plot_floor):
        try:
            fn()
            print(f"ok: {fn.__name__}")
        except Exception as exc:  # a missing optional artifact should not sink the batch
            print(f"skip {fn.__name__}: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
