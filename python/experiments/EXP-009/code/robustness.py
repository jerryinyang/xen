"""EXP-009 robustness probe — are the per-stratum passes on S3_DETREND + S5_SPREAD stable?

Operator-requested (2026-07-01) before booking. Analysis-only, TRAIN-only, 0 reads. Re-derives the
per-instrument passes for the two resolved headline anchor series under each perturbation, and reports the
**count of leak-clean per-stratum passes** (any_pass on E1 hit@0.03 or E2 frac@0.05, label-permutation
collapses) — the per-stratum reading (L-03), not the axis-majority rule. Perturbations: horizon m, H_CAP,
|z|-bin edges, recent-third TRAIN, event-specific vs cell-median horizon, floor band.

Writes results/robustness.json + plots/R_robustness.png.
"""
from __future__ import annotations

import importlib.util
import json
import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from tqdm.auto import tqdm

from xen import availability_gate as ag
from xen import cross_domain_mr as cdm
from xen import reversion_targets as rt


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


_E8 = Path(__file__).resolve().parents[2] / "EXP-008" / "code"
R = _load(_E8 / "run_experiment.py", "exp8_run")
logger = logging.getLogger("EXP-009.robustness")

SEED = 20260701
SERIES = ("S3_DETREND", "S5_SPREAD")
FLOORS = {"hit": 0.03, "frac": 0.05}
N_MIN = 100
LP_TOL = 0.03


def _measure(idxs, H, hl, ed, a_lag, dev_lag, reverse=False):
    out = []
    for c, h, s in zip(idxs, H, hl):
        r = rt.measure_entry(int(c), ed.open, ed.low, ed.high, a_lag[c], dev_lag[c], int(h), s, reverse)
        out.append((np.nan, np.nan, np.nan) if r is None else r)
    return np.asarray(out, dtype=np.float64).reshape(-1, 3)


def cell_pass(series, a_min, e_min, m, h_cap, zedges, recent_third, cell_median_hl, floors,
              basket_full, train, rng) -> list[dict]:
    """Per-instrument leak-clean pass results for one S* series (all 3 pairs handled by caller)."""
    rows = []
    for sym in R.ALL_INSTRUMENTS:
        t = train[sym]
        basket = basket_full.get(sym) if basket_full else None
        if recent_third:
            cut = int(t.height * 2 / 3)
            t = t.slice(cut, t.height - cut)
            basket = None if series == "S5_SPREAD" else None    # S5+recent-third skipped (basket realign)
            if series == "S5_SPREAD":
                continue
        ed = R.build_exec_domain(t, e_min)
        anc = R.anchor_arrays(t, a_min)
        asr = cdm.anchor_series(series, ed.close, ed.ct, anc, basket)
        if not np.any(np.isfinite(asr.dev)):
            continue
        al = rt.anchor_price_level(series, ed.close, asr.dev)
        a_lag = np.concatenate([[np.nan], al[:-1]])
        dl = np.concatenate([[np.nan], asr.dev[:-1]])
        n = ed.close.shape[0]
        zl = np.concatenate([[np.nan], asr.z[:-1]])
        ext = np.flatnonzero((np.arange(n) >= cdm.W_S) & np.isfinite(zl) & (np.abs(zl) >= zedges[0])
                             & (ed.regime_lag >= 0))
        sp = np.zeros(n, bool); hl = np.full(n, np.nan)
        for i in ext:
            w = asr.dev[i - cdm.W_S:i]
            sp[i] = cdm.mr_screen_pass(w); hl[i] = cdm.half_life(w)
        hz = rt.event_horizon(hl, m, h_cap)
        cond_all = ext[sp[ext] & (hz[ext] > 0)]; fail_all = ext[~sp[ext]]
        if cond_all.shape[0] < N_MIN or fail_all.shape[0] < 2:
            continue
        if cell_median_hl:
            mh = int(np.median(hz[cond_all])); hz = np.where(hz > 0, mh, 0)
        cond = _measure(cond_all, hz[cond_all], hl[cond_all], ed, a_lag, dl)
        keep = np.isfinite(cond[:, 0]); cond_idx = cond_all[keep]; cond = cond[keep]
        if cond_idx.shape[0] < N_MIN:
            continue

        def zbin(v):
            for b in range(len(zedges) - 1):
                if zedges[b] <= v < zedges[b + 1]:
                    return b
            return -1
        groups = {}
        for c in fail_all:
            groups.setdefault((zbin(abs(zl[c])), int(ed.regime_lag[c])), []).append(c)
        cidx, cH, cHL = [], [], []
        for j in cond_idx:
            g = groups.get((zbin(abs(zl[j])), int(ed.regime_lag[j])))
            if g:
                cidx.append(int(rng.choice(g))); cH.append(int(hz[j])); cHL.append(float(hl[j]))
        if len(cidx) < N_MIN:
            continue
        ctrl = _measure(np.array(cidx), np.array(cH), np.array(cHL), ed, a_lag, dl)
        # E1 hit + E2 frac
        passes = {}
        for name, kk, kind in (("hit", 0, ag.STAT_MEAN), ("frac", 1, ag.STAT_MEDIAN)):
            cv = cond[:, kk][np.isfinite(cond[:, kk])]; tv = ctrl[:, kk][np.isfinite(ctrl[:, kk])]
            if cv.shape[0] < 2 or tv.shape[0] < 2:
                passes[name] = False; continue
            d = ag._stat_1d(cv, kind) - ag._stat_1d(tv, kind)
            se = ag.cell_se(cv, tv, kind, rng, n_boot=2000)
            mde = ag.Z_ONE_SIDED * se if np.isfinite(se) else np.nan
            fl = floors[name]
            passes[name] = bool(np.isfinite(mde) and mde <= fl and d >= fl and (d - mde) > 0)
        # label-perm collapse (hit)
        union = np.concatenate([cond_idx, fail_all]); lp = []
        for _ in range(10):
            pm = rng.permutation(union.shape[0])
            pc = union[pm[:cond_idx.shape[0]]]; pf = union[pm[cond_idx.shape[0]:cond_idx.shape[0] * 2]]
            mc = _measure(pc, hz[cond_idx], hl[cond_idx], ed, a_lag, dl)
            mf = _measure(pf, hz[cond_idx][:pf.shape[0]], hl[cond_idx][:pf.shape[0]], ed, a_lag, dl)
            lp.append(np.nanmean(mc[:, 0]) - np.nanmean(mf[:, 0]))
        leak_clean = abs(float(np.nanmean(lp))) < LP_TOL
        rows.append({"sym": sym, "any_pass": bool(passes["hit"] or passes["frac"]),
                     "leak_clean": leak_clean})
    return rows


def n_stratum_pass(rows: list[dict]) -> int:
    return sum(1 for r in rows if r["any_pass"] and r["leak_clean"])


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    rng = np.random.default_rng(SEED)
    train = {s: R.load_train_1m(s) for s in tqdm(R.ALL_INSTRUMENTS, desc="load")}
    exec_mins = sorted({e for (_, e) in cdm.DOMAIN_PAIRS.values()})
    baskets = {e: R.build_baskets(train, e, R.ALL_INSTRUMENTS) for e in exec_mins}
    Z = (2.0, 2.5, 3.0, np.inf)
    settings = {
        "baseline": dict(m=3, h_cap=48, zedges=Z, recent_third=False, cell_median_hl=False),
        "m=2": dict(m=2, h_cap=48, zedges=Z, recent_third=False, cell_median_hl=False),
        "m=4": dict(m=4, h_cap=48, zedges=Z, recent_third=False, cell_median_hl=False),
        "H_CAP=96": dict(m=3, h_cap=96, zedges=Z, recent_third=False, cell_median_hl=False),
        "z-edges 2/3": dict(m=3, h_cap=48, zedges=(2.0, 3.0, np.inf), recent_third=False,
                            cell_median_hl=False),
        "recent-third": dict(m=3, h_cap=48, zedges=Z, recent_third=True, cell_median_hl=False),
        "cell-median-HL": dict(m=3, h_cap=48, zedges=Z, recent_third=False, cell_median_hl=True),
    }
    out = {"floors": FLOORS, "per_series": {s: {} for s in SERIES}, "floor_sweep": {s: {} for s in SERIES}}
    base_rows = {}
    for series in SERIES:
        for name, p in tqdm(settings.items(), desc=series):
            rows = []
            for pair, (a_min, e_min) in cdm.DOMAIN_PAIRS.items():
                bf = baskets[e_min] if series == "S5_SPREAD" else None
                rows += cell_pass(series, a_min, e_min, floors=FLOORS, basket_full=bf, train=train,
                                  rng=rng, **p)
            out["per_series"][series][name] = {"n_stratum_pass": n_stratum_pass(rows),
                                               "n_cells": len(rows)}
            if name == "baseline":
                base_rows[series] = rows
        # floor sweep on baseline rows would need per-cell deltas; recompute cheaply via floors dict
        for fl_h, fl_f in ((0.02, 0.03), (0.03, 0.05), (0.05, 0.08)):
            rows = []
            for pair, (a_min, e_min) in cdm.DOMAIN_PAIRS.items():
                bf = baskets[e_min] if series == "S5_SPREAD" else None
                rows += cell_pass(series, a_min, e_min, m=3, h_cap=48, zedges=Z, recent_third=False,
                                  cell_median_hl=False, floors={"hit": fl_h, "frac": fl_f},
                                  basket_full=bf, train=train, rng=rng)
            out["floor_sweep"][series][f"hit{fl_h}/frac{fl_f}"] = n_stratum_pass(rows)

    R_DIR = Path("python/experiments/EXP-009/results")
    P_DIR = Path("python/experiments/EXP-009/plots")
    R_DIR.mkdir(parents=True, exist_ok=True); P_DIR.mkdir(parents=True, exist_ok=True)
    (R_DIR / "robustness.json").write_text(json.dumps(out, indent=2))

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(1, 2, figsize=(14, 5))
    names = list(settings)
    for series, mk in zip(SERIES, ("o-", "s-")):
        ax[0].plot(names, [out["per_series"][series][n]["n_stratum_pass"] for n in names], mk,
                   label=series)
    ax[0].set_ylabel("leak-clean per-stratum passes"); ax[0].set_title("Robustness across settings")
    ax[0].tick_params(axis="x", rotation=45); ax[0].legend(); ax[0].axhline(0, color="k", lw=0.6)
    for series, mk in zip(SERIES, ("o-", "s-")):
        fl = list(out["floor_sweep"][series])
        ax[1].plot(fl, [out["floor_sweep"][series][f] for f in fl], mk, label=series)
    ax[1].set_ylabel("passes"); ax[1].set_title("Floor sweep"); ax[1].legend()
    fig.suptitle("EXP-009 robustness — per-stratum pass stability (S3_DETREND, S5_SPREAD)")
    fig.tight_layout(); fig.savefig(P_DIR / "R_robustness.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("robustness written")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
