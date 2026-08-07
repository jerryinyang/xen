"""SPDR-017 fresh-context interrogation. Canonical xen.evaluation only; no local accounting.

Re-derives every headline from raw results/*.parquet independently of screen_code.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "python" / "src"))
from xen import evaluation as ev  # noqa: E402

RES = Path(__file__).resolve().parents[1] / "results"
OUT = Path(__file__).resolve().parents[1] / "results"
TRAIN_END_NS = 1702857600 * 1_000_000_000  # 2023-12-18T00:00Z
_DAY_NS = 86_400_000_000_000

PRIMARY = dict(source="M-ZONE", ablation="A2", model="M-RIDGE", z=1.5, H=12,
               event_type="E-TOUCH", h=12)


def day_block_ci(r: np.ndarray, day: np.ndarray, block_days: int, n_boot=5000, seeds=5):
    """Block bootstrap on per-day mean sufficient stats (matches screen unit=day)."""
    r = np.asarray(r, float)
    m = np.isfinite(r)
    r, day = r[m], day[m]
    if r.size < 3:
        return dict(point=float("nan"), ci_low=float("nan"), ci_high=float("nan"),
                    se=float("nan"), n_dates=0, n=int(r.size))
    uniq, inv = np.unique(day, return_inverse=True)
    nd = uniq.size
    tot = np.bincount(inv, weights=r, minlength=nd)
    cnt = np.bincount(inv, minlength=nd)
    point = float(tot.sum() / cnt.sum())
    if nd < 3:
        return dict(point=point, ci_low=float("nan"), ci_high=float("nan"),
                    se=float("nan"), n_dates=nd, n=int(r.size))
    L = min(block_days, nd)
    k = int(np.ceil(nd / L))
    offs = np.arange(L)
    los, his, sds = [], [], []
    for seed in (101, 211, 307, 401, 503)[:seeds]:
        rng = np.random.default_rng(seed)
        starts = rng.integers(0, nd, size=(n_boot, k))
        idx = (starts[:, :, None] + offs[None, None, :]) % nd
        idx = idx.reshape(n_boot, k * L)[:, :nd]
        s_tot = tot[idx].sum(axis=1)
        s_cnt = cnt[idx].sum(axis=1)
        stats = np.where(s_cnt > 0, s_tot / np.maximum(s_cnt, 1), np.nan)
        fin = stats[np.isfinite(stats)]
        los.append(np.quantile(fin, 0.025))
        his.append(np.quantile(fin, 0.975))
        sds.append(fin.std())
    return dict(point=point, ci_low=float(min(los)), ci_high=float(max(his)),
               se=float(max(sds)), mde_bps=float(2.8 * max(sds)),
               n_dates=int(nd), n=int(r.size),
               ci_low_seed_range=[float(min(los)), float(max(los))])


def load_primary(band="DESIGN", policy="P-NONE"):
    pe = pl.scan_parquet(RES / "post_event.parquet")
    f = pe.filter(
        (pl.col("band") == band) & (pl.col("source") == PRIMARY["source"]) &
        (pl.col("ablation") == PRIMARY["ablation"]) & (pl.col("model") == PRIMARY["model"]) &
        (pl.col("z") == PRIMARY["z"]) & (pl.col("H") == PRIMARY["H"]) &
        (pl.col("event_type") == PRIMARY["event_type"]) & (pl.col("h") == PRIMARY["h"]) &
        (pl.col("policy") == policy) &
        (pl.col("side") != 0) & pl.col("r_h").is_finite()
    )
    return f.collect()


def per_stratum_primary(band="DESIGN"):
    df = load_primary(band)
    rows = []
    for sym, g in df.group_by("symbol"):
        sym = sym[0]
        r = g["r_h"].to_numpy()
        day = (g["entry_ts"].to_numpy() // _DAY_NS).astype(np.int64)
        lab = g["label"].to_list()
        ci1 = day_block_ci(r, day, 1)
        ci3 = day_block_ci(r, day, 3)
        ci7 = day_block_ci(r, day, 7)
        rows.append(dict(
            symbol=sym, n=int(r.size),
            mean=float(r.mean()), median=float(np.median(r)), std=float(r.std()),
            p_momo=float(np.mean([x == "MOMO" for x in lab])),
            p_mr=float(np.mean([x == "MR" for x in lab])),
            p_flat=float(np.mean([x == "FLAT" for x in lab])),
            n_dates=ci1["n_dates"],
            ci_low_env=float(min(ci1["ci_low"], ci3["ci_low"], ci7["ci_low"])),
            ci_high_env=float(max(ci1["ci_high"], ci3["ci_high"], ci7["ci_high"])),
            mde_bps=float(ci1.get("mde_bps", float("nan"))),
            ci_low_b1=ci1["ci_low"], ci_low_b3=ci3["ci_low"], ci_low_b7=ci7["ci_low"],
            ci_high_b1=ci1["ci_high"], ci_high_b3=ci3["ci_high"], ci_high_b7=ci7["ci_high"],
        ))
    return pl.DataFrame(rows).sort("symbol")


def base_conditional(band="DESIGN"):
    """Event-conditioned r_h vs ambient (uncond band) per symbol: mean/disp/sign shift."""
    c = json.load(open(RES / "controls.json"))
    rows = []
    for sym, d in c["by_symbol"].items():
        u = d.get("uncond")
        if not u:
            continue
        live, ctrl = u["live"], u["control_arm"]
        rows.append(dict(
            symbol=sym,
            live_n=live["n"], amb_n=ctrl["n"],
            live_mean=live["mean_r_h"], amb_mean=ctrl["mean_r_h"],
            dmean=live["mean_r_h"] - ctrl["mean_r_h"],
            live_median=live["median_r_h"], amb_median=ctrl["median_r_h"],
            dmedian=live["median_r_h"] - ctrl["median_r_h"],
            live_pmomo=live["p_momo"], amb_pmomo=ctrl["p_momo"],
            dp_momo=live["p_momo"] - ctrl["p_momo"],
            live_pev=live["p_event"], amb_pev=ctrl["p_event"],
            dp_event=live["p_event"] - ctrl["p_event"],
        ))
    return pl.DataFrame(rows).sort("symbol")


def model_ic(band="DESIGN"):
    mo = pl.scan_parquet(RES / "model_oos.parquet").filter(
        (pl.col("band") == band) & (pl.col("ablation") == "A2") &
        (pl.col("model") == "M-RIDGE") & (pl.col("H") == 12) &
        pl.col("yhat_bps").is_finite() & pl.col("y_bps").is_finite()
    ).collect()
    rows = []
    for sym, g in mo.group_by("symbol"):
        sym = sym[0]
        yh = g["yhat_bps"].to_numpy()
        y = g["y_bps"].to_numpy()
        ae = g["abs_err_bps"].to_numpy()
        if yh.size < 50:
            continue
        # Spearman IC
        from scipy.stats import spearmanr, pearsonr
        ic_s = spearmanr(yh, y).correlation
        ic_p = pearsonr(yh, y)[0]
        rows.append(dict(symbol=sym, n=int(yh.size), ic_spearman=float(ic_s),
                         ic_pearson=float(ic_p), mae_bps=float(np.nanmean(ae)),
                         yhat_std=float(yh.std()), y_std=float(y.std())))
    return pl.DataFrame(rows).sort("symbol")


def ablation_by_symbol(band="DESIGN"):
    ab = pl.read_parquet(RES / "ablation.parquet")
    return ab.sort(["symbol", "ablation"])


def vs014():
    v = pl.read_parquet(RES / "vs_014_baseline.parquet")
    prim = v.filter((pl.col("z") == 1.5) & (pl.col("H") == 12) & (pl.col("h") == 12) &
                    (pl.col("event") == "E-TOUCH") & pl.col("delta_mean_r_h").is_finite())
    return v, prim


def controls_summary():
    c = json.load(open(RES / "controls.json"))
    rows = []
    for sym, d in c["by_symbol"].items():
        row = dict(symbol=sym)
        for key, short in [("time_shuffle", "ts"), ("matched_random", "mr"),
                           ("feature_shuffle", "fs"), ("level_only", "lo"),
                           ("path_future_destroy", "t1")]:
            x = d.get(key)
            if x:
                if "live_percentile" in x:
                    row[f"{short}_pct"] = x["live_percentile"]
                    row[f"{short}_seeds"] = x.get("n_seeds")
                if key == "level_only":
                    row["lo_dmean"] = x.get("delta_mean_r_h")
                if key == "path_future_destroy":
                    row["t1_live_net"] = x.get("live_mean_partial_net")
                    row["t1_p95"] = x.get("null_p95")
                    row["t1_survive"] = x.get("survives_above_p95")
        rows.append(row)
    return pl.DataFrame(rows).sort("symbol"), c.get("class_notes")


def money_by_symbol(band="DESIGN"):
    me = pl.scan_parquet(RES / "money_episodes.parquet").filter(
        (pl.col("band") == band) & pl.col("partial_net_bps").is_finite()
    ).collect()
    rows = []
    for (sym, pol), g in me.group_by(["symbol", "policy"]):
        pn = g["partial_net_bps"].to_numpy()
        gr = g["gross_bps"].to_numpy()
        rows.append(dict(symbol=sym, policy=pol, n=int(pn.size),
                         mean_net=float(pn.mean()), median_net=float(np.median(pn)),
                         mean_gross=float(gr.mean()), win_rate=float((pn > 0).mean())))
    return pl.DataFrame(rows).sort(["symbol", "policy"])


def fence_check():
    out = {}
    for f in ["post_event.parquet", "money_episodes.parquet", "events.parquet"]:
        lf = pl.scan_parquet(RES / f)
        cols = lf.collect_schema().names()
        tcol = "exit_ts" if "exit_ts" in cols else "event_ts"
        mx = lf.select(pl.col(tcol).max()).collect().item()
        out[f] = dict(col=tcol, max_ts=int(mx), under_train_end=bool(mx < TRAIN_END_NS))
    return out


if __name__ == "__main__":
    print("=== FENCE ===")
    print(json.dumps(fence_check(), indent=2))

    print("\n=== MODEL IC (DESIGN A2 RIDGE H=12) ===")
    ic = model_ic()
    print(ic)
    print("median spearman IC", float(ic["ic_spearman"].median()),
          "median pearson", float(ic["ic_pearson"].median()))

    print("\n=== PRIMARY CELL PER-STRATUM (DESIGN) ===")
    ps = per_stratum_primary("DESIGN")
    with pl.Config(tbl_rows=40, tbl_cols=20):
        print(ps.select(["symbol", "n", "n_dates", "mean", "median", "std",
                         "p_momo", "p_mr", "ci_low_env", "ci_high_env", "mde_bps"]))
    ps.write_parquet(OUT / "an_primary_per_stratum_DESIGN.parquet")

    print("\n  sign split:", (ps["mean"] > 0).sum(), "pos /", (ps["mean"] < 0).sum(), "neg")
    print("  median of means:", float(ps["mean"].median()))
    print("  any CI env excludes 0:",
          ((ps["ci_low_env"] > 0) | (ps["ci_high_env"] < 0)).sum())
    print("  min mde:", float(ps["mde_bps"].min()), "max mde:", float(ps["mde_bps"].max()))

    print("\n=== PRIMARY CELL PER-STRATUM (CONFIRM) ===")
    psc = per_stratum_primary("CONFIRM")
    with pl.Config(tbl_rows=40, tbl_cols=20):
        print(psc.select(["symbol", "n", "mean", "median", "ci_low_env", "ci_high_env", "mde_bps"]))
    psc.write_parquet(OUT / "an_primary_per_stratum_CONFIRM.parquet")
    print("  any CI env excludes 0:",
          ((psc["ci_low_env"] > 0) | (psc["ci_high_env"] < 0)).sum())

    print("\n=== BASE-CONDITIONAL (event vs ambient, DESIGN) ===")
    bc = base_conditional()
    with pl.Config(tbl_rows=40, tbl_cols=20):
        print(bc)
    bc.write_parquet(OUT / "an_base_conditional_DESIGN.parquet")
    bcf = bc.filter(pl.col("dmean").is_finite())
    print("  [finite-only] n:", bcf.height, " median dmean:", float(bcf["dmean"].median()),
          " mean dmean:", float(bcf["dmean"].mean()))
    print("  median dp_event:", float(bc["dmean"].median()),
          " median dp_event:", float(bc["dp_event"].median()),
          " median dp_momo:", float(bc["dp_momo"].median()))
    print("  dmean sign split:", (bc["dmean"] > 0).sum(), "pos /", (bc["dmean"] < 0).sum(), "neg")

    print("\n=== ABLATION per symbol (mean_r_h) ===")
    ab = ablation_by_symbol()
    piv = ab.pivot(values="mean_r_h", index="symbol", on="ablation")
    with pl.Config(tbl_rows=40):
        print(piv)
    # WEAK-DIR load-bearing: A2 vs A1 and A1 vs A0
    for lay in ["A0", "A1", "A2"]:
        sub = ab.filter(pl.col("ablation") == lay)
        print(f"  {lay}: median mean_r_h {float(sub['mean_r_h'].median()):+.2f} "
              f"mean {float(sub['mean_r_h'].mean()):+.2f}")
    if set(["A0", "A1", "A2"]).issubset(set(piv.columns)):
        d21 = (piv["A2"] - piv["A1"]).drop_nulls()
        d10 = (piv["A1"] - piv["A0"]).drop_nulls()
        print("  A2-A1 median:", float(d21.median()), "pos frac:", float((d21 > 0).mean()))
        print("  A1-A0 median:", float(d10.median()), "pos frac:", float((d10 > 0).mean()))

    print("\n=== vs 014 Z-VOL ===")
    vall, vprim = vs014()
    print("  primary cell (z1.5 H12 h12 E-TOUCH) matched rows:", vprim.height)
    print("  median delta_mean_r_h:", float(vprim["delta_mean_r_h"].median()))
    print("  frac M-ZONE>Z-VOL:", float((vprim["delta_mean_r_h"] > 0).mean()))
    print("  median mzone_n:", float(vprim["mzone_n"].median()),
          "median zvol_n:", float(vprim["zvol_n"].median()))
    vall_f = vall.filter(pl.col("delta_mean_r_h").is_finite())
    print("  ALL matched rows median delta:", float(vall_f["delta_mean_r_h"].median()),
          " frac>0:", float((vall_f["delta_mean_r_h"] > 0).mean()), " n rows:", vall_f.height)

    print("\n=== CONTROLS ===")
    cs, notes = controls_summary()
    with pl.Config(tbl_rows=40, tbl_cols=20):
        print(cs)
    for col in ["ts_seeds", "mr_seeds", "fs_seeds"]:
        if col in cs.columns:
            print(f"  {col} min/max:", int(cs[col].min()), int(cs[col].max()))
    if "t1_survive" in cs.columns:
        print("  T1 survivors:", cs.filter(pl.col("t1_survive") == True).height)

    print("\n=== MONEY (partial cost) ===")
    mb = money_by_symbol()
    with pl.Config(tbl_rows=60):
        print(mb)
    for pol in ["P-MOMO", "P-MR"]:
        sub = mb.filter(pl.col("policy") == pol)
        print(f"  {pol}: median mean_net {float(sub['mean_net'].median()):+.1f} "
              f"median median_net {float(sub['median_net'].median()):+.1f} "
              f"median mean_gross {float(sub['mean_gross'].median()):+.1f} "
              f"symbols with mean_net>0: {(sub['mean_net']>0).sum()}/{sub.height}")
