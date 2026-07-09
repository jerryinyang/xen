"""EXP-021 probe: AUDUSD 1D performance + ACTUAL overlap-aware time-in-market (4h & 1D).

Reuses my own screen.py construction. Occupancy = union of hold windows [t+1, t+1+h] over AUDUSD
single-worst events, / valid bars. Two reads: OVERLAP (raw union, multiple concurrent AUDUSD legs
allowed) and SEQUENTIAL (one position at a time — skip a new entry while still holding).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import screen as S   # noqa: E402  (DOMAIN from argv; run per-domain)

AUD = None  # resolved below


def occupancy(domain: str):
    panel = S.build_panel()
    st = S.compute_state(panel)
    syms = st["syms"]
    i_aud = syms.index("audusd")
    m, s = S.consensus_resid(st["U"], "median", "raw")
    maxabs = np.nanmax(np.abs(s), axis=1)
    maxabs[~st["valid"]] = np.nan
    k = S.trailing_threshold(maxabs, S.K_TRAIL_W)
    hl = S.ar1_halflife(s[st["valid"], i_aud])
    h = int(np.clip(round(2 * hl), 1, 12)) if np.isfinite(hl) else 6
    n = st["U"].shape[0]
    absr = np.abs(s)

    # AUDUSD single-worst events (argmax over basket == audusd, |s|>=k)
    ev_t = [t for t in range(n - 1)
            if st["valid"][t] and np.isfinite(k[t])
            and int(np.nanargmax(absr[t])) == i_aud and absr[t, i_aud] >= k[t] and t + 1 + h < n]

    occ_overlap = np.zeros(n, bool)
    for t in ev_t:
        occ_overlap[t + 1: t + 1 + h] = True          # entry open t+1 .. exit open t+1+h

    # sequential: one position at a time
    occ_seq = np.zeros(n, bool)
    busy_until = -1
    n_seq_trades = 0
    for t in ev_t:
        if t + 1 > busy_until:
            occ_seq[t + 1: t + 1 + h] = True
            busy_until = t + h
            n_seq_trades += 1

    vb = int(st["valid"].sum())
    return {"domain": domain, "h": h, "n_bars": n, "valid_bars": vb,
            "aud_events": len(ev_t),
            "occ_overlap_bars": int(occ_overlap.sum()),
            "occ_overlap_pct": occ_overlap.sum() / vb,
            "occ_seq_trades": n_seq_trades,
            "occ_seq_bars": int(occ_seq.sum()),
            "occ_seq_pct": occ_seq.sum() / vb}


def main():
    dom = S.DOMAIN
    # AUDUSD cell scoreboard for this domain
    suff = S.SUFFIX
    c = pl.read_parquet(S.RESULTS / f"cell_reads{suff}.parquet").filter(pl.col("instrument") == "audusd")
    pl.Config.set_tbl_rows(20)
    print(f"=== AUDUSD cell scoreboard [{dom}] ===")
    print(c.select("A", "B", "C", "D", "n_events", "mean_rho_bps", "ci_low_bps", "mde_bps",
                   "p_perm", "tripwire_collapse").sort("mean_rho_bps", descending=True))
    print(f"=== AUDUSD ACTUAL time-in-market [{dom}] (single-worst median/raw) ===")
    o = occupancy(dom)
    for kk, vv in o.items():
        print(f"  {kk}: {vv:.3f}" if isinstance(vv, float) else f"  {kk}: {vv}")


if __name__ == "__main__":
    main()
