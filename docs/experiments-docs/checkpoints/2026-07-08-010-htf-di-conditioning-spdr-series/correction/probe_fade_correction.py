"""Correction probe (2026-07-08, post-audit) — re-derive every fade-relevant SPDR magnitude on
the CORRECT estimand (raw forward move, not side-signed) with hold-matched block bootstrap
(block >= H for overlapping per-bar series; the original SPDR-001 analysis used block=5 while
autocorrelation persists to lag ~H).

Outputs (this directory):
  dirgap_cells.csv   — 48 full-sample dir_gap cells (inst x domain x hold), block=5 vs block=H CI
  sign_counts.csv    — 84 DI-variant cells per instrument: CI-excl-0 counts, block=5 vs block=H
  xau_fill_probe.csv — SPDR-003 XAU 1d/1h H24: side-signed vs raw-move spread + half-split
  atrdi_cells.csv    — BTC 1h/5min ATR x DI interaction cells, block=5 vs block=H
  spdr002_ustec.csv  — SPDR-002 USTEC DI sign-conditioning re-derivation (H12/24/36/48)
"""
import csv, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]                       # repo root
PY = ROOT / "python"
sys.path.insert(0, str(PY / "experiments/SPDR-001/screen_code"))
sys.path.insert(0, str(PY / "experiments/SPDR-002/screen_code"))
sys.path.insert(0, str(PY / "experiments/SPDR-003/screen_code"))
sys.path.insert(0, str(PY / "src"))
import spdr001_screen as S1
import spdr002_screen as S2
import spdr003_screen as S3

N_BOOT = 1500

def blockci(x, block, n_boot=N_BOOT, seed=0):
    n = len(x); eff = max(1, min(int(block), n - 1)); nb = int(np.ceil(n / eff))
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, n, size=(n_boot, nb))
    pos = (starts[:, :, None] + np.arange(eff)[None, None, :]) % n
    samp = x[pos.reshape(n_boot, -1)[:, :n]]
    mm = samp.mean(axis=1)
    return float(np.percentile(mm, 2.5)), float(np.percentile(mm, 97.5))

def two_sample_ci(a, b, block, n_boot=N_BOOT, seed=0):
    rng = np.random.default_rng(seed)
    def bs(x):
        blk = max(1, min(int(block), x.size - 1)); nbk = int(np.ceil(x.size / blk))
        st = rng.integers(0, x.size, nbk)
        return np.concatenate([np.take(x, np.arange(s, s + blk), mode="wrap")
                               for s in st])[:x.size].mean()
    d = [bs(a) - bs(b) for _ in range(n_boot)]
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))

def main():
    # ---------- Table A: full-sample dir_gap (edge series), all 48 cells ----------
    rows_a, rows_b = [], []
    ctx_cache = {}
    for sym in S1.INSTRUMENTS:
        train = S1.load_train_1m(sym)
        counts = {"b5": [0, 0], "bH": [0, 0], "cells": 0}
        for name, htf_min, ltf_min, ratio in S1.DOMAIN_PAIRS:
            ctx = S1.build_domain_ctx(name, htf_min, ltf_min, train)
            ctx_cache[(sym, name)] = ctx
            n = ctx.n
            for mlt in S1.HOLD_MULTS:
                hold = ratio * mlt
                base = ctx.valid & (np.arange(n) + hold < n)
                i = np.nonzero(base)[0]
                mv = (ctx.ltf_open[i + hold] - ctx.ltf_open[i]) / ctx.ltf_atr_prev[i]
                d = ctx.htf_dir[i].astype(float)
                x = d * mv                                  # edge series; dir_gap = 2*mean approx
                gap = float(mv[d == 1].mean() - mv[d == -1].mean())
                lo5, hi5 = blockci(x, 5)
                loH, hiH = blockci(x, hold)
                rows_a.append(dict(instrument=sym, domain=name, hold=hold,
                                   dir_gap=round(gap, 4), edge=round(float(x.mean()), 4),
                                   n=int(i.size),
                                   ci5_lo=round(lo5, 4), ci5_hi=round(hi5, 4),
                                   ciH_lo=round(loH, 4), ciH_hi=round(hiH, 4),
                                   clear_b5=(lo5 > 0 or hi5 < 0), clear_bH=(loH > 0 or hiH < 0)))
                # ---------- Table B: all DI-axis variants, sign counts ----------
                mv_all = np.full(n, np.nan); mv_all[i] = mv
                for sp in [s for s in S1.variant_specs() if s["sig"]]:
                    j = np.nonzero(base & sp["mask"](ctx))[0]
                    if j.size < 50:
                        continue
                    xv = ctx.htf_dir[j].astype(float) * mv_all[j]
                    counts["cells"] += 1
                    l5, h5 = blockci(xv, 5); lH, hH = blockci(xv, hold)
                    if l5 > 0: counts["b5"][0] += 1
                    elif h5 < 0: counts["b5"][1] += 1
                    if lH > 0: counts["bH"][0] += 1
                    elif hH < 0: counts["bH"][1] += 1
        rows_b.append(dict(instrument=sym, n_cells=counts["cells"],
                           block5_pos=counts["b5"][0], block5_neg=counts["b5"][1],
                           blockH_pos=counts["bH"][0], blockH_neg=counts["bH"][1]))

    # ---------- Table C: SPDR-003 XAU 1d/1h H24 fill probe ----------
    sym = "XAUUSD"; train = S1.load_train_1m(sym)
    ctx = ctx_cache[(sym, "1d/1h")]
    fside, fprice = S3.build_fill_table(ctx, train)
    hold = 24; n = ctx.n
    idx = np.nonzero(ctx.valid & (fside != 0) & (np.arange(n) + hold < n))[0]
    ent = S1.greedy_entries(idx, hold)
    side = fside[ent].astype(float)
    move = (ctx.ltf_open[ent + hold] - fprice[ent]) / ctx.ltf_atr_prev[ent]
    r_signed = side * move
    d = ctx.htf_dir[ent]
    ok = np.isfinite(r_signed)
    r_signed, move, d, ent2 = r_signed[ok], move[ok], d[ok], ent[ok]
    rows_c = []
    def crow(label, a, b, blk):
        sp = float(a.mean() - b.mean()); lo, hi = two_sample_ci(a, b, blk)
        rows_c.append(dict(estimand=label, n_pos=int(a.size), n_neg=int(b.size),
                           spread=round(sp, 4), ci_lo=round(lo, 4), ci_hi=round(hi, 4),
                           clear=(lo > 0 or hi < 0)))
    crow("side_signed_full", r_signed[d == 1], r_signed[d == -1], 10)
    crow("raw_move_full", move[d == 1], move[d == -1], 10)
    half = ent2 < np.median(ent2)
    crow("side_signed_half1", r_signed[half & (d == 1)], r_signed[half & (d == -1)], 10)
    crow("side_signed_half2", r_signed[~half & (d == 1)], r_signed[~half & (d == -1)], 10)
    crow("raw_move_half1", move[half & (d == 1)], move[half & (d == -1)], 10)
    crow("raw_move_half2", move[~half & (d == 1)], move[~half & (d == -1)], 10)

    # ---------- Table D: BTC ATR x DI interaction ----------
    rows_d = []
    ctx = ctx_cache[("BTCUSD", "1h/5min")]
    n = ctx.n
    for reg, rn in [(S1.REGIME_HIGH, "atrH_adxHi_di"), (S1.REGIME_LOW, "atrL_adxHi_di")]:
        mask0 = (ctx.atr_reg == reg) & (ctx.adx_bucket >= 1)
        for hold in (12, 24, 36, 48):
            j = np.nonzero(ctx.valid & mask0 & (np.arange(n) + hold < n))[0]
            mv = (ctx.ltf_open[j + hold] - ctx.ltf_open[j]) / ctx.ltf_atr_prev[j]
            x = ctx.htf_dir[j].astype(float) * mv
            l5, h5 = blockci(x, 5); lH, hH = blockci(x, hold)
            rows_d.append(dict(variant=rn, hold=hold, edge=round(float(x.mean()), 4), n=int(j.size),
                               ci5_lo=round(l5, 4), ci5_hi=round(h5, 4),
                               ciH_lo=round(lH, 4), ciH_hi=round(hH, 4),
                               clear_bH=(lH > 0 or hH < 0)))

    # ---------- Table E: SPDR-002 USTEC DI sign-conditioning ----------
    rows_e = []
    ctx = ctx_cache[("USTEC", "1h/5min")]
    sig = S2.momentum_signal(ctx)
    n = ctx.n
    for hold in (12, 24, 36, 48):
        base = ctx.valid & (sig != 0) & (np.arange(n) + hold < n)
        def rr(mask):
            k = np.nonzero(mask)[0]
            e = S1.greedy_entries(k, hold)
            return sig[e] * (ctx.ltf_open[e + hold] - ctx.ltf_open[e]) / ctx.ltf_atr_prev[e]
        a = rr(base & (sig == ctx.htf_dir)); b = rr(base & (sig != ctx.htf_dir))
        eff = float(a.mean() - b.mean())
        lo, hi = two_sample_ci(a, b, 5)
        rows_e.append(dict(hold=hold, n_agree=int(a.size), n_disagree=int(b.size),
                           effect=round(eff, 4), ci_lo=round(lo, 4), ci_hi=round(hi, 4),
                           clear=(lo > 0 or hi < 0)))

    for fname, rows in [("dirgap_cells.csv", rows_a), ("sign_counts.csv", rows_b),
                        ("xau_fill_probe.csv", rows_c), ("atrdi_cells.csv", rows_d),
                        ("spdr002_ustec.csv", rows_e)]:
        with open(HERE / fname, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
        print(f"wrote {fname} ({len(rows)} rows)")

if __name__ == "__main__":
    main()
