"""SPDR-014 final neutral interrogation — re-derives all verdict-bearing numbers
from raw emissions (post_event.parquet, events.parquet). Data-analyst owned.

Outputs results/final_magnitudes.json + printed summary.
No import of screen_code. Only polars/numpy + own block bootstrap.
"""
import json
from pathlib import Path
import numpy as np
import polars as pl

RES = Path(__file__).resolve().parents[1] / "results"
SEED = 20260724


# ----------------------------------------------------------------------------- helpers
def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (p, (c - h) / d, (c + h) / d)


def date_block_boot(vals, dates, stat=np.mean, n_boot=4000, block_days=3, seed=SEED):
    """Block bootstrap over event dates. vals aligned to integer day index `dates`."""
    vals = np.asarray(vals, float)
    dates = np.asarray(dates)
    if len(vals) == 0:
        return (float("nan"), float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    uniq = np.unique(dates)
    # group values by day
    day_to_idx = {d: np.where(dates == d)[0] for d in uniq}
    # build blocks of consecutive day-labels
    n_days = len(uniq)
    point = stat(vals)
    ests = np.empty(n_boot)
    n_blocks = max(1, int(np.ceil(n_days / block_days)))
    for b in range(n_boot):
        picks = []
        for _ in range(n_blocks):
            start = rng.integers(0, n_days)
            for j in range(block_days):
                di = uniq[(start + j) % n_days]
                picks.append(day_to_idx[di])
        idx = np.concatenate(picks)
        ests[b] = stat(vals[idx])
    return (float(point), float(np.percentile(ests, 2.5)), float(np.percentile(ests, 97.5)))


def day_index(ts_ns):
    return (np.asarray(ts_ns, np.int64) // (86_400_000_000_000)).astype(np.int64)


# ----------------------------------------------------------------------------- load
pe = pl.read_parquet(RES / "post_event.parquet")
ev = pl.read_parquet(RES / "events.parquet")

# characterisation frame: P-NONE only
char = pe.filter(pl.col("policy") == "P-NONE")

out = {}

# ============================================================ 1. EVENT RATES (events.parquet)
# p_event per source x z x H (DESIGN, E-TOUCH, H1), pooled + per-symbol
er = ev.filter((pl.col("band") == "DESIGN") & (pl.col("clock") == "H1") &
               (pl.col("event_type") == "E-TOUCH"))
rate_tbl = (er.group_by(["source", "z", "H"])
            .agg(pl.len().alias("n_origins"),
                 pl.col("event").sum().alias("n_event"),
                 pl.col("event").mean().alias("p_event"))
            .sort(["source", "z", "H"]))
out["event_rate_by_source_z_H_DESIGN_ETOUCH"] = rate_tbl.to_dicts()

# event rate monotonic in z (selectivity)
sel = (er.filter(pl.col("source") == "Z-VOL").group_by("z")
       .agg(pl.col("event").mean().alias("p_event"), pl.len().alias("n")).sort("z"))
out["zvol_selectivity_by_z"] = sel.to_dicts()

# ============================================================ 2. RESIDUAL + RATE LEAN per stratum
# DESIGN, P-NONE, E-TOUCH, H1, decided side only (side != 0 and label != UNDECIDED)
def strat_table(df, group_cols):
    dec = df.filter(pl.col("side") != 0)
    g = (dec.group_by(group_cols)
         .agg(pl.len().alias("n_decided"),
              (pl.col("label") == "MOMO").sum().alias("n_momo"),
              (pl.col("label") == "MR").sum().alias("n_mr"),
              (pl.col("label") == "FLAT").sum().alias("n_flat"),
              pl.col("r_h").mean().alias("mean_r_h"),
              pl.col("r_h").median().alias("median_r_h"),
              pl.col("r_h").std().alias("std_r_h"),
              pl.col("event_ts").n_unique().alias("n_dates"))
         .sort(group_cols))
    return g

base = char.filter((pl.col("band") == "DESIGN") & (pl.col("clock") == "H1") &
                   (pl.col("event_type") == "E-TOUCH"))

# per source x z x H x h, pooled over symbols
cells = strat_table(base, ["source", "z", "H", "h"])
# add wilson CI on p_momo + MDE
rows = []
for r in cells.to_dicts():
    n = r["n_decided"]; k = r["n_momo"]
    p, lo, hi = wilson(k, n)
    sr = r["std_r_h"] or float("nan")
    nd = r["n_dates"] or 0
    mde = 2.8 * sr / np.sqrt(nd) if nd > 0 else float("nan")
    r.update({"p_momo": p, "p_momo_lo": lo, "p_momo_hi": hi,
              "p_mr": (r["n_mr"] / n) if n else float("nan"),
              "mde_bps": mde,
              "powered": bool(n >= 80 and nd >= 30 and (mde is not None and mde <= 10))})
    rows.append(r)
out["design_pnone_etouch_by_source_z_H_h"] = rows
out["n_powered_residual_cells_pooled"] = int(sum(x["powered"] for x in rows))

# primary cell pooled across symbols: Z-VOL z=1.5 H=12 h=12
prim = base.filter((pl.col("source") == "Z-VOL") & (pl.col("z") == 1.5) &
                   (pl.col("H") == 12) & (pl.col("h") == 12) & (pl.col("side") != 0))
pv = prim.select("r_h", "event_ts", "label").to_dict(as_series=False)
di = day_index(pv["event_ts"])
mean_pt, mean_lo, mean_hi = date_block_boot(pv["r_h"], di, np.mean)
med_pt, med_lo, med_hi = date_block_boot(pv["r_h"], di, np.median)
k = sum(1 for x in pv["label"] if x == "MOMO"); n = len(pv["label"])
pmp, pmlo, pmhi = wilson(k, n)
out["primary_cell_pooled_ZVOL_z1.5_H12_h12"] = {
    "n_decided": n, "mean_r_h": mean_pt, "mean_r_h_ci": [mean_lo, mean_hi],
    "median_r_h": med_pt, "median_r_h_ci": [med_lo, med_hi],
    "p_momo": pmp, "p_momo_ci": [pmlo, pmhi],
    "note": "date-block bootstrap block=3d, 4000 resamples; raw live (not paired-Δ vs control)"}

# per-symbol primary cell
persym = []
for sym in sorted(prim.select("symbol").unique().to_series().to_list()):
    s = prim.filter(pl.col("symbol") == sym)
    d = s.select("r_h", "event_ts", "label").to_dict(as_series=False)
    if len(d["r_h"]) == 0:
        continue
    dd = day_index(d["event_ts"])
    mp, ml, mh = date_block_boot(d["r_h"], dd, np.mean, n_boot=2000)
    kk = sum(1 for x in d["label"] if x == "MOMO"); nn = len(d["label"])
    pp, pl_, ph = wilson(kk, nn)
    persym.append({"symbol": sym, "n_decided": nn, "mean_r_h": mp,
                   "mean_r_h_ci": [ml, mh], "median_r_h": float(np.median(d["r_h"])),
                   "p_momo": pp, "p_momo_ci": [pl_, ph], "n_dates": int(len(np.unique(dd)))})
out["primary_cell_per_symbol"] = persym

# ============================================================ 3. RATE LEAN pooled (all decided, DESIGN P-NONE E-TOUCH Z-VOL)
allzvol = base.filter((pl.col("source") == "Z-VOL") & (pl.col("side") != 0))
d = allzvol.select("label").to_series().to_list()
k = d.count("MOMO"); n = len(d)
pp, plo, phi = wilson(k, n)
out["rate_lean_pooled_ZVOL_all_z_H_h"] = {
    "n_decided": n, "p_momo": pp, "p_momo_ci": [plo, phi],
    "p_mr": d.count("MR") / n, "p_flat": d.count("FLAT") / n,
    "lean_above_0.5": pp - 0.5}

# ============================================================ 4. LAST-K MARKOV CONDITIONER (the new facet)
# stratify primary-ish frame by last_k_high_4 and last_k_high_12
def lastk_facet(kcol):
    # bucket counts: 0, low(1..K/2), high(>K/2) — but report by exact value where n allows
    g = (allzvol.group_by(kcol)
         .agg(pl.len().alias("n"),
              (pl.col("label") == "MOMO").sum().alias("n_momo"),
              pl.col("r_h").mean().alias("mean_r_h"),
              pl.col("r_h").median().alias("median_r_h"),
              pl.col("event_ts").n_unique().alias("n_dates"))
         .sort(kcol))
    res = []
    for r in g.to_dicts():
        p, lo, hi = wilson(r["n_momo"], r["n"])
        r.update({"p_momo": p, "p_momo_ci": [lo, hi]})
        res.append(r)
    return res
out["lastk_high_4_facet_ZVOL"] = lastk_facet("last_k_high_4")
out["lastk_high_12_facet_ZVOL"] = lastk_facet("last_k_high_12")

# contrast: last_k_high_4 == 0 vs == max, mean_r_h + p_momo with block CI
for kcol, hi_thresh in [("last_k_high_4", 4), ("last_k_high_12", 12)]:
    lowdf = allzvol.filter(pl.col(kcol) == 0)
    hidf = allzvol.filter(pl.col(kcol) >= (hi_thresh - 0 if kcol == "last_k_high_4" else 8))
    def summ(df):
        dd = df.select("r_h", "event_ts", "label").to_dict(as_series=False)
        if len(dd["r_h"]) == 0:
            return None
        idx = day_index(dd["event_ts"])
        mp, ml, mh = date_block_boot(dd["r_h"], idx, np.mean, n_boot=2000)
        kk = sum(1 for x in dd["label"] if x == "MOMO"); nn = len(dd["label"])
        pp, plo2, phi2 = wilson(kk, nn)
        return {"n": nn, "mean_r_h": mp, "mean_r_h_ci": [ml, mh], "p_momo": pp,
                "p_momo_ci": [plo2, phi2], "median_r_h": float(np.median(dd["r_h"]))}
    out[f"contrast_{kcol}_low0_vs_high"] = {"low_0": summ(lowdf), "high": summ(hidf)}

# ============================================================ 5. OTHER CONDITIONERS
for cond in ["vol_tercile", "mag_high", "shock_flag", "slow_regime"]:
    g = (allzvol.group_by(cond)
         .agg(pl.len().alias("n"), (pl.col("label") == "MOMO").sum().alias("n_momo"),
              pl.col("r_h").mean().alias("mean_r_h"), pl.col("r_h").median().alias("median_r_h"),
              pl.col("event_ts").n_unique().alias("n_dates")).sort(cond))
    res = []
    for r in g.to_dicts():
        p, lo, hi = wilson(r["n_momo"], r["n"])
        r.update({"p_momo": p, "p_momo_ci": [lo, hi]}); res.append(r)
    out[f"conditioner_{cond}_ZVOL"] = res

# ============================================================ 6. DESIGN vs CONFIRM (primary cell, pooled)
dc = {}
for band in ["DESIGN", "CONFIRM"]:
    s = char.filter((pl.col("band") == band) & (pl.col("clock") == "H1") &
                    (pl.col("event_type") == "E-TOUCH") & (pl.col("source") == "Z-VOL") &
                    (pl.col("z") == 1.5) & (pl.col("H") == 12) & (pl.col("h") == 12) &
                    (pl.col("side") != 0))
    dd = s.select("label", "r_h").to_dict(as_series=False)
    n = len(dd["label"]); k = dd["label"].count("MOMO")
    p, lo, hi = wilson(k, n)
    dc[band] = {"n": n, "p_momo": p, "p_momo_ci": [lo, hi],
                "mean_r_h": float(np.mean(dd["r_h"])) if n else None,
                "median_r_h": float(np.median(dd["r_h"])) if n else None}
out["design_vs_confirm_primary_cell"] = dc

# ============================================================ 7. EVENT-DEF SENSITIVITY (DESIGN Z-VOL z1.5 H12 h12)
ed = {}
for etype in ["E-TOUCH", "E-CLOSE", "E-HORIZON"]:
    s = char.filter((pl.col("band") == "DESIGN") & (pl.col("clock") == "H1") &
                    (pl.col("event_type") == etype) & (pl.col("source") == "Z-VOL") &
                    (pl.col("z") == 1.5) & (pl.col("H") == 12) & (pl.col("h") == 12) &
                    (pl.col("side") != 0))
    dd = s.select("label", "r_h").to_dict(as_series=False)
    n = len(dd["label"]); k = dd["label"].count("MOMO")
    p, lo, hi = wilson(k, n)
    ed[etype] = {"n": n, "p_momo": p, "p_momo_ci": [lo, hi],
                 "mean_r_h": float(np.mean(dd["r_h"])) if n else None,
                 "median_r_h": float(np.median(dd["r_h"])) if n else None}
out["event_def_sensitivity_primary"] = ed

# ============================================================ 8. Z-MAG vs Z-VOL (DESIGN E-TOUCH z1.5 H12 h12)
zc = {}
for src in ["Z-VOL", "Z-MAG", "Z-MAG-SENS"]:
    s = char.filter((pl.col("band") == "DESIGN") & (pl.col("clock") == "H1") &
                    (pl.col("event_type") == "E-TOUCH") & (pl.col("source") == src) &
                    (pl.col("z") == 1.5) & (pl.col("H") == 12) & (pl.col("h") == 12) &
                    (pl.col("side") != 0))
    dd = s.select("label", "r_h").to_dict(as_series=False)
    n = len(dd["label"]); k = dd["label"].count("MOMO")
    p, lo, hi = wilson(k, n)
    zc[src] = {"n": n, "p_momo": p, "p_momo_ci": [lo, hi],
               "mean_r_h": float(np.mean(dd["r_h"])) if n else None}
out["source_compare_primary"] = zc

# ============================================================ 9. MONEY + STRADDLE (disclosure)
money = pe.filter(pl.col("policy").is_in(["P-MOMO", "P-MR"]))
mg = (money.filter(pl.col("band") == "DESIGN").group_by(["policy", "source"])
      .agg(pl.len().alias("n_legs"),
           pl.col("partial_net_bps").mean().alias("mean_partial_net"),
           pl.col("partial_net_bps").median().alias("median_partial_net"),
           (pl.col("partial_net_bps") > 0).mean().alias("win_rate"),
           pl.col("gross_bps").mean().alias("mean_gross"))
      .sort(["policy", "source"]))
out["money_DESIGN_by_policy_source"] = mg.to_dicts()

strad = pl.read_parquet(RES / "straddle.parquet")
out["straddle_summary"] = (strad.group_by("band").agg(
    pl.col("mean_partial_net").mean().alias("mean_partial_net"),
    pl.col("median_partial_net").median().alias("median_partial_net"),
    pl.len().alias("n_cells")).to_dicts()) if "band" in strad.columns else strad.to_dicts()[:5]

# ============================================================ 10. POWER SUMMARY
ec = pl.read_parquet(RES / "expectancy_by_cell.parquet")
sub = ec.filter((pl.col("band") == "DESIGN") & (pl.col("policy") == "P-NONE") &
                (pl.col("event") == "E-TOUCH") & (pl.col("clock") == "H1"))
out["power_summary_DESIGN_ETOUCH"] = {
    "n_cells": sub.height,
    "n_powered_screen_rule": int(sub.filter((pl.col("n_events") >= 80) & (pl.col("n_dates") >= 30) & (pl.col("mde_bps") <= 10)).height),
    "mde_bps_p10": float(sub["mde_bps"].quantile(0.1)),
    "mde_bps_median": float(sub["mde_bps"].median()),
    "mde_bps_min": float(sub["mde_bps"].min()),
    "n_events_median": float(sub["n_events"].median()),
    "n_events_max": int(sub["n_events"].max()),
    "n_dates_median": float(sub["n_dates"].median())}

# symbols with zero coverage (NaN scale) and event counts
out["symbol_coverage"] = (base.filter(pl.col("side") != 0).group_by("symbol")
                          .agg(pl.len().alias("n_decided_etouch")).sort("n_decided_etouch").to_dicts())

Path(RES / "final_magnitudes.json").write_text(json.dumps(out, indent=2, default=float))
print("WROTE results/final_magnitudes.json")

# ---- console highlights
print("\n=== EVENT RATE Z-VOL selectivity by z (DESIGN E-TOUCH) ===")
for r in out["zvol_selectivity_by_z"]:
    print(f"  z={r['z']}: p_event={r['p_event']:.3f} n={r['n']}")
print("\n=== PRIMARY CELL pooled (Z-VOL z1.5 H12 h12) ===")
pc = out["primary_cell_pooled_ZVOL_z1.5_H12_h12"]
print(f"  n={pc['n_decided']} mean_r_h={pc['mean_r_h']:.2f} CI{[round(x,1) for x in pc['mean_r_h_ci']]} "
      f"median={pc['median_r_h']:.2f} p_momo={pc['p_momo']:.3f} CI{[round(x,3) for x in pc['p_momo_ci']]}")
print("\n=== RATE LEAN pooled Z-VOL all cells ===")
rl = out["rate_lean_pooled_ZVOL_all_z_H_h"]
print(f"  n={rl['n_decided']} p_momo={rl['p_momo']:.4f} CI{[round(x,4) for x in rl['p_momo_ci']]} "
      f"lean={rl['lean_above_0.5']:+.4f} p_mr={rl['p_mr']:.4f} p_flat={rl['p_flat']:.4f}")
print("\n=== LAST-K HIGH 4 facet (Z-VOL) ===")
for r in out["lastk_high_4_facet_ZVOL"]:
    print(f"  k4={r['last_k_high_4']}: n={r['n']} p_momo={r['p_momo']:.3f} CI{[round(x,3) for x in r['p_momo_ci']]} "
          f"mean_r_h={r['mean_r_h']:.2f} median={r['median_r_h']:.2f}")
print("\n=== LAST-K HIGH 12 facet (Z-VOL) ===")
for r in out["lastk_high_12_facet_ZVOL"]:
    print(f"  k12={r['last_k_high_12']}: n={r['n']} p_momo={r['p_momo']:.3f} mean_r_h={r['mean_r_h']:.2f}")
print("\n=== CONTRAST last_k_high_4 low0 vs high ===")
print(" ", out["contrast_last_k_high_4_low0_vs_high"])
print("\n=== DESIGN vs CONFIRM primary ===")
print(" ", out["design_vs_confirm_primary_cell"])
print("\n=== EVENT-DEF sensitivity ===")
print(" ", out["event_def_sensitivity_primary"])
print("\n=== SOURCE compare primary ===")
print(" ", out["source_compare_primary"])
print("\n=== MONEY DESIGN by policy/source ===")
for r in out["money_DESIGN_by_policy_source"]:
    print(f"  {r['policy']}/{r['source']}: n={r['n_legs']} mean_net={r['mean_partial_net']:.2f} "
          f"median={r['median_partial_net']:.2f} win={r['win_rate']:.3f} gross={r['mean_gross']:.2f}")
print("\n=== POWER summary ===")
print(" ", out["power_summary_DESIGN_ETOUCH"])
print("\n=== CONDITIONERS ===")
for cond in ["vol_tercile", "mag_high", "shock_flag", "slow_regime"]:
    print(f"  {cond}:")
    for r in out[f"conditioner_{cond}_ZVOL"]:
        key = r[cond]
        print(f"    {key}: n={r['n']} p_momo={r['p_momo']:.3f} mean_r_h={r['mean_r_h']:.2f}")
PY
