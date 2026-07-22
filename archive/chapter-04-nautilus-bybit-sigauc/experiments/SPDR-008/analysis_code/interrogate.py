"""SPDR-008 fresh-context interrogation — raw-emission reads only (data-analyst).

Never imports experiment-local analysis code. Recomputes from the emitted parquet /
json only; canonical xen only for nothing accounting-bearing (screen has no P&L).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

RES = Path("python/experiments/SPDR-008/results")
BT = ("IB", "PVA", "PRIOR")


def sec(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


def main():
    des = pl.read_parquet(RES / "trap_DESIGN.parquet")
    con = pl.read_parquet(RES / "trap_CONFIRM.parquet")
    amap = pl.read_parquet(RES / "allocation_map.parquet")
    layers = json.loads((RES / "layers.json").read_text())
    floor = json.loads((RES / "floor_table.json").read_text())

    # ---- 1. Causality / structural spot-checks ------------------------------
    sec("1. CAUSALITY & STRUCTURE (trap_DESIGN)")
    d = des
    bad_entry = d.filter(
        (pl.col("entry_ts") - pl.col("reclaim_ts")).dt.total_minutes() != 1
    ).height
    bad_order = d.filter(pl.col("reclaim_ts") < pl.col("poke_ts")).height
    bad_npost = d.filter(pl.col("n_post") <= 0).height
    print(f"events DESIGN={d.height} CONFIRM={con.height}")
    print(f"entry_ts != reclaim_ts+1min : {bad_entry}")
    print(f"reclaim_ts < poke_ts        : {bad_order}")
    print(f"n_post <= 0                 : {bad_npost}")
    print(f"n_post  min/median/max      : {d['n_post'].min()}/{d['n_post'].median()}/{d['n_post'].max()}")
    print(f"entry_phase min/median/max  : {d['entry_phase'].min()}/{d['entry_phase'].median()}/{d['entry_phase'].max()}")
    # one extra bar out of median n_post — materiality of entry-bar inclusion
    print(f"1-bar / median n_post       : {1.0/float(d['n_post'].median()):.4%}")

    # ---- 2. mfe_rev_norm distribution (outlier / tail check, L-20) ----------
    sec("2. mfe_rev_norm DISTRIBUTION per boundary (mean is outlier-prone)")
    for b in BT:
        v = des.filter(pl.col("boundary") == b)["mfe_rev_norm"].to_numpy()
        v = v[np.isfinite(v)]
        print(f"{b:5s} n={len(v):6d} mean={v.mean():7.3f} median={np.median(v):6.3f} "
              f"q90={np.quantile(v,.9):6.2f} q99={np.quantile(v,.99):7.2f} max={v.max():8.1f}")

    # ---- 3. T4 pooled(event-wt) vs day-mean(unweighted) contrast ------------
    sec("3. T4 ESTIMATOR MISMATCH: pooled event-weighted vs unweighted day-mean")
    print("(the reported 'contrast' is event-weighted; the day-clustered CI is centered")
    print(" on the UNWEIGHTED day-mean — where they disagree, 'excludes zero' is a")
    print(" weighting artifact, not a robust edge)\n")
    for b in BT:
        for band, df in (("DESIGN", des), ("CONFIRM", con)):
            e = df.filter(pl.col("boundary") == b)
            lyr = layers["per_boundary"][b][band]["T4_availability"]
            cmean = lyr["control_mean"]
            pooled_trap = float(np.nanmean(e["mfe_rev_norm"].to_numpy()))
            dm = (e.group_by("day").agg(pl.col("mfe_rev_norm").mean().alias("m")))["m"].to_numpy()
            daymean_trap = float(np.nanmean(dm))
            print(f"{b:5s} {band:7s} ctrl={cmean:6.3f} | pooled_trap={pooled_trap:6.3f} "
                  f"-> contrast={pooled_trap-cmean:+.3f} (reported {lyr['contrast']:+.3f}) | "
                  f"daymean_trap={daymean_trap:6.3f} -> day_contrast={daymean_trap-cmean:+.3f} | "
                  f"CI={np.round(lyr['day_clustered_ci'],3) if lyr['day_clustered_ci'] else None} "
                  f"excl0={lyr['excludes_zero']}")

    # ---- 4. K=3 / multiplicity null budget ----------------------------------
    sec("4. K=3 MULTIPLICITY: null false-qualifier budget (allocation_map)")
    print("Gate = per_cell_p<=0.05 (rho in top-5% of own derangement null) AND rho_confirm>0.")
    print("Mirror-null gate = per_cell_p>=0.95 (rho in BOTTOM-5%) AND rho_confirm<0.")
    print("Under a symmetric null the two counts match; excess of 'supported' over 'mirror' = signal.\n")
    tot_sup = tot_mir = tot_pw = 0
    for b in BT:
        pw = amap.filter((pl.col("boundary") == b) & (pl.col("n") >= 20))
        n_p05 = pw.filter(pl.col("per_cell_p") <= 0.05).height
        sup = pw.filter((pl.col("per_cell_p") <= 0.05) & (pl.col("rho_confirm") > 0))
        mir = pw.filter((pl.col("per_cell_p") >= 0.95) & (pl.col("rho_confirm") < 0))
        n_p05_hi = pw.filter(pl.col("per_cell_p") >= 0.95).height
        exp_analytic = pw.height * 0.05 * 0.5
        print(f"{b:5s} powered={pw.height:3d} | p<=.05:{n_p05:2d} ->&conf>0(SUPPORTED):{sup.height:2d} "
              f"| p>=.95:{n_p05_hi:2d} ->&conf<0(MIRROR):{mir.height:2d} "
              f"| analytic_null_exp={exp_analytic:.2f}")
        tot_sup += sup.height; tot_mir += mir.height; tot_pw += pw.height
    print(f"\nTOTAL powered={tot_pw} | SUPPORTED={tot_sup} | MIRROR(anti)={tot_mir} | "
          f"analytic null exp={tot_pw*0.025:.2f}")

    # ---- 5. The 6 IB 'signed_supported' cells: are they real or marginal? ---
    sec("5. IB signed_supported CELLS — detail")
    ibsup = amap.filter((pl.col("boundary") == "IB") & pl.col("signed_supported_cell"))
    with pl.Config(tbl_rows=30, tbl_cols=12, fmt_str_lengths=20):
        print(ibsup.select("symbol", "n", "rho", "per_cell_p", "mde_rho",
                           "rho_confirm", "high_low_diff", "median_mfe_rev_norm"))
    print("\nT2 marginal (high_low_diff) sign among the 6 IB 'supported':")
    print(f"  high_low_diff > 0: {ibsup.filter(pl.col('high_low_diff')>0).height}/6  "
          f"(a real signed edge needs HIGH>LOW; T1 & T2 should agree)")
    # how strong is the CONFIRM reproduction? (just a sign gate, magnitude disclosed)
    print(f"  rho_confirm median among 6 = {ibsup['rho_confirm'].median():.4f} "
          f"(gate only requires >0; magnitude tells if reproduction is weak)")

    # ---- 6. pos/neg rho symmetry across ALL powered cells -------------------
    sec("6. per-cell rho SYMMETRY (a real monotone effect skews POSITIVE)")
    for b in BT:
        pw = amap.filter((pl.col("boundary") == b) & (pl.col("n") >= 20))
        pos = pw.filter(pl.col("rho") > 0.10).height
        neg = pw.filter(pl.col("rho") < -0.10).height
        med = float(pw["rho"].median())
        print(f"{b:5s} powered={pw.height:3d} rho>+.10:{pos:2d} rho<-.10:{neg:2d} "
              f"median_rho={med:+.4f} mean_rho={float(pw['rho'].mean()):+.4f}")

    # ---- 7. Money floor ------------------------------------------------------
    sec("7. MONEY FLOOR (floor_table) + edge-in-bps conversion")
    ibw = np.array([r["design_median_ib_width_bps"] for r in floor])
    print(f"design_median_ib_width_bps across {len(ibw)} symbols: "
          f"median={np.median(ibw):.1f} q25={np.quantile(ibw,.25):.1f} q75={np.quantile(ibw,.75):.1f}")
    print(f"floor ex-spread (taker11+funding3) = 14.0 bps (+ per-symbol spread at graduation)\n")
    medibw = float(np.median(ibw))
    print("Signed marginal value (T2 HIGH-LOW) in bps  = contrast_ibw * median_ib_width_bps:")
    for b in BT:
        for band, df in (("DESIGN", des), ("CONFIRM", con)):
            t2 = layers["per_boundary"][b][band]["T2_tier_marginal"]
            pc = t2.get("paired_day_contrast", {})
            c = pc.get("mean")
            if c is not None:
                print(f"  {b:5s} {band:7s} T2 HIGH-LOW = {c:+.3f} ibw = {c*medibw:+.1f} bps "
                      f"(CI excl0={pc.get('excludes_zero')})")
    print("\nUnsigned availability edge (T4) in bps  = contrast_ibw * median_ib_width_bps:")
    for b in BT:
        for band, df in (("DESIGN", des), ("CONFIRM", con)):
            t4 = layers["per_boundary"][b][band]["T4_availability"]
            c = t4["contrast"]
            print(f"  {b:5s} {band:7s} T4 = {c:+.3f} ibw = {c*medibw:+.1f} bps "
                  f"(CI excl0={t4['excludes_zero']})")

    # ---- 8. PVA p=0.052 whiff: below MDE? flips on CONFIRM? ------------------
    sec("8. PVA DESIGN p=0.052 WHIFF")
    for band in ("DESIGN", "CONFIRM"):
        t1 = layers["per_boundary"]["PVA"][band]["T1_load_monotonicity"]
        print(f"PVA {band:7s} rho={t1['rho']:+.4f} MDE(null95)={t1['mde_rho_at_n']:.4f} "
              f"p={t1['one_sided_p_ge_observed']} -> rho{'>=' if t1['rho']>=t1['mde_rho_at_n'] else '<'}MDE, "
              f"SUPPORTED={t1['SUPPORTED']}")


if __name__ == "__main__":
    main()
