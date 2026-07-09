"""EXP-021 disclosure: horizon-multiplier sensitivity. Is h = 2*HL load-bearing?

Reuses my own screen.py construction (analyst's own analysis_code). 4h primary cell
(median/raw/single-worst/hedged): recompute mean rho per instrument at h = round(m*HL) for
m in {1,2,3} (clip [1,12]). HL is fitted per instrument (AR1); the multiplier m is the
pre-registered constant under test.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import screen as S   # noqa: E402  (my own analysis_code; DOMAIN defaults to 4h with no argv)


def main():
    assert S.DOMAIN == "4h", "run with no arg (4h primary)"
    panel = S.build_panel()
    st = S.compute_state(panel)
    syms = st["syms"]
    m_cons, s = S.consensus_resid(st["U"], "median", "raw")
    maxabs = np.nanmax(np.abs(s), axis=1)
    maxabs[~st["valid"]] = np.nan
    k = S.trailing_threshold(maxabs, S.K_TRAIL_W)
    hl = {i: S.ar1_halflife(s[st["valid"], i]) for i in range(len(syms))}

    out = []
    for mult in (1, 2, 3):
        hby = {i: (int(np.clip(round(mult * hl[i]), 1, 12)) if np.isfinite(hl[i]) else 6)
               for i in range(len(syms))}
        events = S.build_events(st, s, k, "single", hby)
        rows = S.rho_for_events(st, events, hby, "median", True)
        by = {}
        for r in rows:
            by.setdefault(r[1], []).append(r[4])
        for i, sym in enumerate(syms):
            rho = np.array([v for v in by.get(i, []) if np.isfinite(v)])
            if len(rho) < 2:
                continue
            ci = S.ev.block_bootstrap_ci(rho)
            out.append({"mult": f"{mult}xHL", "instrument": sym, "h": hby[i],
                        "n": len(rho), "mean_rho_bps": float(np.mean(rho)) * 1e4,
                        "ci_low_bps": ci["ci"][0] * 1e4})
    df = pl.DataFrame(out)
    df.write_parquet(S.RESULTS / "h_sensitivity.parquet")
    pl.Config.set_tbl_rows(40)
    piv = df.pivot(values="mean_rho_bps", index="instrument", on="mult", aggregate_function="first")
    print("=== mean rho (bps) by horizon multiplier — 4h median/raw/single/hedged ===")
    print(piv)
    print("=== sign-stability across multipliers (does the read depend on 2x?) ===")
    print(df.group_by("instrument").agg(
        (pl.col("mean_rho_bps") > 0).sum().alias("n_pos_of3"),
        pl.col("mean_rho_bps").min().round(2).alias("min"),
        pl.col("mean_rho_bps").max().round(2).alias("max")).sort("instrument"))


if __name__ == "__main__":
    main()
