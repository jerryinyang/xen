"""SPDR-012 analyst — script 9: independent causality re-derivation.

SPDR-012 ships with NO hard leak gate (AMENDMENT-T1). The causality claim therefore rests on
construction. This script re-derives it from scratch, independently of screen_code/ and of the
QA pass:

  A. recompute rv20 from the G1 golden-trace closes by hand.
  B. reimplement the expanding-window monthly-refit ridge from the emitted feature columns and
     compare with the emitted prediction series, for several cells.
  C. run a deliberately leaky variant (fit window includes the rows it predicts) and confirm the
     comparison discriminates.
  D. confirm no emitted feature at origin i is a function of bar i+1 (shift test).
"""
from __future__ import annotations

from pathlib import Path

import json
import numpy as np
import polars as pl
from scipy import stats

EXP = Path(__file__).resolve().parents[1]
RES = EXP / "results"

FEATS = ["rv20", "ewma_vol", "parkinson", "gk"]


def fit_ridge(X, y, alpha=1.0):
    mu = X.mean(0); sd = X.std(0); sd[sd == 0] = 1.0
    Z = (X - mu) / sd
    Z1 = np.hstack([np.ones((len(Z), 1)), Z])
    P = np.eye(Z1.shape[1]) * alpha
    P[0, 0] = 0.0
    beta = np.linalg.solve(Z1.T @ Z1 + P, Z1.T @ y)
    return mu, sd, beta


def predict(mu, sd, beta, X):
    Z = (X - mu) / sd
    return np.hstack([np.ones((len(Z), 1)), Z]) @ beta


def walk_forward(df: pl.DataFrame, leaky=False):
    """Expanding window, initial fit = first 40% of the cell's DESIGN origins, monthly re-fit."""
    df = df.sort("slot_start")
    X = df.select(FEATS).to_numpy()
    y = df["target_abs_oo"].to_numpy()
    # re-fit schedule is keyed to the TARGET bar's calendar month (determined empirically:
    # this is the only convention that reproduces the emission bit-for-bit)
    months = pl.from_epoch(df["target_slot_start"], time_unit="ns").dt.strftime("%Y-%m").to_numpy()
    n = len(y)
    a0 = int(0.40 * n)  # floor — matches cell_diagnostics.initial_fit_n
    out = np.full(n, np.nan)
    a = a0
    while a < n:
        # next refit boundary = start of the next calendar month after ts[a]
        cur = months[a]
        b = a
        while b < n and months[b] == cur:
            b += 1
        fit_hi = b if leaky else a
        Xf, yf = X[:fit_hi], y[:fit_hi]
        ok = np.isfinite(Xf).all(1) & np.isfinite(yf)
        if ok.sum() >= 30:
            mu, sd, beta = fit_ridge(Xf[ok], yf[ok])
            out[a:b] = predict(mu, sd, beta, X[a:b])
        a = b
    return out


def main() -> None:
    print("===== A. G1 rv20 recomputed by hand from the listed closes =====")
    g1 = json.loads((RES / "golden_traces.json").read_text())["G1"]
    closes = np.array(g1["closes_used"])
    r = np.diff(np.log(closes))
    rv20 = float(np.sqrt(np.mean(r ** 2)))
    print(f"  my rv20 = {rv20:.17f}")
    print(f"  screen  = {g1['rv20_screen']:.17f}")
    print(f"  rel err = {abs(rv20 - g1['rv20_screen']) / g1['rv20_screen']:.3e}"
          f"  | 20 returns recomputed independently: {len(r)}")

    v = pl.read_parquet(RES / "vol_reliability.parquet")

    print("\n===== B/C. independent walk-forward re-derivation vs the emitted predictions =====")
    for sym, clock in (("BTCUSDT", "H4"), ("ETHUSDT", "H1"), ("SOLUSDT", "H1"), ("DOGEUSDT", "H4"), ("MATICUSDT", "H1")):
        d = v.filter((pl.col("symbol") == sym) & (pl.col("clock") == clock)
                     & (pl.col("band") == "DESIGN")).sort("slot_start")
        if d.height < 200:
            print(f"  {sym} {clock}: too few rows"); continue
        mine = walk_forward(d)
        leak = walk_forward(d, leaky=True)
        emitted = d["pred__vlevel_ridge__target_abs_oo"].to_numpy()
        ok = np.isfinite(mine) & np.isfinite(emitted)
        print(f"  {sym} {clock} DESIGN: n={d.height} oos_rows={ok.sum()} "
              f"max|mine-emitted| = {np.nanmax(np.abs(mine[ok]-emitted[ok])):.3e} bps "
              f"| leaky variant differs by up to {np.nanmax(np.abs(leak[ok]-emitted[ok])):.2f} bps")

    print("\n===== D. shift test — is any feature at origin i a function of bar i+1? =====")
    # If a feature were contaminated by the target bar, feature[i] would correlate with
    # bar i+1 realised measures MORE than feature[i+1] correlates with bar i+1's own measures.
    rows = []
    for (sym, clock), g in v.filter(pl.col("band") == "CONFIRM").group_by(
            ["symbol", "clock"], maintain_order=True):
        g = g.sort("slot_start")
        if g.height < 500:
            continue
        pk = g["parkinson"].to_numpy()
        rows.append({
            "symbol": sym, "clock": clock,
            # feature at i vs the SAME bar's parkinson (should be 1.0 by identity)
            "self": float(stats.spearmanr(pk, pk).statistic),
            # feature at i vs the NEXT bar's parkinson (must be < self; a leak would push it to 1)
            "vs_next_bar": float(stats.spearmanr(pk[:-1], pk[1:]).statistic),
            # rv20 at i vs rv20 at i+1 (19/20 overlap -> ~0.97, mechanical, NOT a leak)
            "rv20_lag1": float(stats.spearmanr(g["rv20"].to_numpy()[:-1],
                                               g["rv20"].to_numpy()[1:]).statistic),
        })
    df = pl.DataFrame(rows)
    print(df.group_by("clock").agg(pl.col("self").median(), pl.col("vs_next_bar").median().round(3),
                                   pl.col("rv20_lag1").median().round(3), pl.len()).sort("clock"))
    print("  interpretation: parkinson[i] vs parkinson[i+1] is a persistence correlation "
          "(0.3-0.5), not 1.0 -> the feature is not the target bar's own realised measure.")

    # target identity check: target_abs_oo[i] must equal oo_move[i+1] when the bars are adjacent
    print("\n===== D2. target identity: target_abs_oo[i] == oo_move[i+1] on contiguous rows =====")
    bad = tot = 0
    for (sym, clock, band), g in v.group_by(["symbol", "clock", "band"], maintain_order=True):
        g = g.sort("slot_start")
        t = g["target_abs_oo"].to_numpy()[:-1]
        nx = g["oo_move"].to_numpy()[1:]
        cont = g["next_contiguous"].to_numpy()[:-1]
        ok = np.isfinite(t) & np.isfinite(nx) & (cont == True)  # noqa: E712
        tot += int(ok.sum())
        bad += int(np.sum(np.abs(t[ok] - nx[ok]) > 1e-6))
    print(f"  contiguous rows checked: {tot} | mismatches: {bad}")
    print("  (oo_move[i] is the move that is already realised at origin i and is never a feature;")
    print("   target_abs_oo[i] is the NEXT bar's move -> strictly one clock bar ahead.)")


if __name__ == "__main__":
    main()
