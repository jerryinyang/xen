"""EXP-022 Phase-2 probe: characterise the disclosed USTEC lead (R_US bloc, anchor S, hedged).

Reuses screen.py construction (no re-derivation). Answers operator Q1 robustness / Q2 time-in-market
/ Q3 alpha-beta split. TRAIN-only; holdout untouched (screen loads first 49%).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("screen", HERE / "screen.py")
sc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc)
import xen.evaluation as ev  # noqa: E402

USTEC = sc.MEMBERS.index("ustec")
US_BLOC = [sc.MEMBERS.index(s) for s in sc.REGIONS["US"]]     # ustec,us500,us2000,us30
LI = US_BLOC.index(USTEC)                                     # local col of USTEC in bloc


def build_bloc_state():
    panel = sc.build_panel()
    times = panel["CloseTime"].to_numpy()
    O = np.column_stack([panel[f"O_{s}"].to_numpy().astype(float) for s in sc.MEMBERS])[:, US_BLOC]
    US = np.column_stack([panel[f"uS_{s}"].to_numpy().astype(float) for s in sc.MEMBERS])[:, US_BLOC]
    present = np.isfinite(US) & np.isfinite(O)
    valid = present.sum(axis=1) >= 2
    return times, O, US, present, valid


def rows_for(O, present, valid, U, a="mean", b="raw", hmult=2.0):
    """Single-worst hedged rows for USTEC in the US bloc, horizon = hmult*HL."""
    m, s = sc.consensus_resid(U, present, a, b)
    _, s_hl = sc.consensus_resid(U, present, a, b)
    hl = sc.ar1_halflife(s_hl[valid, LI][np.isfinite(s_hl[valid, LI])])
    h = int(np.clip(round(hmult * hl), 1, 12)) if np.isfinite(hl) else 6
    hvec = np.full(len(US_BLOC), h)
    maxabs = np.where(valid, np.nanmax(np.where(present, np.abs(s), np.nan), axis=1), np.nan)
    k = sc.trailing_threshold(maxabs, sc.K_TRAIL_W)
    cols = np.array(US_BLOC)
    rows = sc.build_rows(O, present, s, k, valid, "single", hvec, a, True, cols)
    ust = [r for r in rows if r[1] == USTEC]
    return ust, h, hl


def rho_arr(rows):
    return np.array([r[4] for r in rows], float)


def main():
    times, O, US, present, valid = build_bloc_state()
    ust, h, hl = rows_for(O, present, valid, US, "mean", "raw", 2.0)
    rho = rho_arr(ust)
    tvec = np.array([r[0] for r in ust])
    print(f"USTEC R_US/S mean/raw/single/hedged: n={len(rho)} h={h} HL={hl:.2f} "
          f"mean_rho={rho.mean()*1e4:.2f}bps")

    # Q1: block sensitivity + seed range
    bs = ev.block_sensitivity(rho, [3, 5, 10])
    print("\n[Q1] block_sensitivity ci_low (bps) @ block 3/5/10:",
          [round(r["ci"][0] * 1e4, 2) for r in bs], "-> sign(ci_low) stable:",
          len({np.sign(r["ci"][0]) for r in bs}) == 1)
    ci = ev.block_bootstrap_ci(rho)
    print(f"    ci={[round(x*1e4,2) for x in ci['ci']]}bps  ci_low_seed_range="
          f"{[round(x*1e4,2) for x in ci['ci_low_seed_range']]}bps  mde={ev.mde(rho)*1e4:.2f}bps")

    # Q1: temporal halves
    mid = np.median(tvec)
    h1, h2 = rho[tvec <= mid], rho[tvec > mid]
    for lab, x in [("H1", h1), ("H2", h2)]:
        c = ev.block_bootstrap_ci(x)
        print(f"    {lab}: n={len(x)} mean={x.mean()*1e4:.2f}bps ci={[round(v*1e4,2) for v in c['ci']]}")

    # Q1: horizon sensitivity 1/2/3x HL
    print("\n[Q1] horizon sensitivity (xHL):")
    for hm in (1.0, 2.0, 3.0):
        u2, hh, _ = rows_for(O, present, valid, US, "mean", "raw", hm)
        r2 = rho_arr(u2)
        c = ev.block_bootstrap_ci(r2)
        print(f"    {hm:.0f}xHL (h={hh}): n={len(r2)} mean={r2.mean()*1e4:.2f}bps "
              f"ci={[round(v*1e4,2) for v in c['ci']]}")

    # Q2: time-in-market. active USTEC bars in the bloc construction = present & valid-consensus
    ust_active = int((present[:, LI] & valid).sum())
    n_ev = len(rho)
    occ_seq = n_ev * h / ust_active            # sequential single-position occupancy
    print(f"\n[Q2] time-in-market: {n_ev} single-worst events, h={h}; "
          f"USTEC active(valid) bars={ust_active}; "
          f"event-rate={n_ev/ust_active*100:.1f}% of active bars; "
          f"held-fraction (n*h/active)={occ_seq*100:.1f}%")

    # Q3: alpha/beta. hedged rho vs unhedged rho at SAME events; beta of USTEC fwd on bloc consensus fwd
    m, s = sc.consensus_resid(US, present, "mean", "raw")
    g_ust, g_con, fade = [], [], []
    for r in ust:
        t, k1 = r[0], r[0] + 1
        g = np.log(O[k1 + h] / O[k1])
        fp = present[t] & np.isfinite(g)
        gp = g[fp]
        g_ust.append(g[LI]); g_con.append(np.mean(gp)); fade.append(r[5])
    g_ust, g_con, fade = np.array(g_ust), np.array(g_con), np.array(fade)
    rho_hedged = fade * (g_ust - g_con)
    rho_unhedged = fade * g_ust
    beta = np.polyfit(g_con, g_ust, 1)[0]
    print(f"\n[Q3] alpha/beta split (same events):")
    print(f"    rho hedged (alpha) ={rho_hedged.mean()*1e4:+.2f}bps")
    print(f"    rho unhedged (raw) ={rho_unhedged.mean()*1e4:+.2f}bps")
    print(f"    beta component (unhedged-hedged)={(rho_unhedged.mean()-rho_hedged.mean())*1e4:+.2f}bps")
    print(f"    USTEC forward beta to bloc consensus = {beta:.3f}")


if __name__ == "__main__":
    main()
