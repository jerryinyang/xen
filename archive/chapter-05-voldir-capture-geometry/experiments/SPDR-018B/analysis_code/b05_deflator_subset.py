"""Which subset reproduces deflators.json's payoff scales? And the 10 'trail' cells under the old target."""
import json
import numpy as np
import pandas as pd

R = "python/experiments/SPDR-018B/results/"
m = pd.read_parquet(R + "metrics_by_cell.parquet")
tgt = m["at_parent_target_precision"].fillna(False).astype(bool)
sup = m["at_parent_target_precision_absolute__SUPERSEDED"].fillna(0).astype(bool)
signed = m["gross_p"].notna()
target = {"B": 43.165921721854424, "C": 83.01517868406692}

print("=== hunting the deflator payoff scale ===")
subsets = {
    "all signed": signed,
    "powered (sigma)": signed & tgt,
    "powered (absolute/superseded)": signed & sup,
    "per-symbol only": signed & ~m.symbol.astype(str).str.contains("POOLED"),
    "pooled only": signed & m.symbol.astype(str).str.contains("POOLED"),
    "TRAIN band": signed & (m.band == "TRAIN"),
    "CONFIRM band": signed & (m.band == "CONFIRM"),
    "DESIGN band": signed & (m.band == "DESIGN"),
}
for arm in ["B", "C"]:
    print(f"  arm {arm} target={target[arm]:.3f}")
    for name, sel in subsets.items():
        d = m[sel & (m.arm == arm)]
        if not len(d):
            continue
        for stat, val in [("median(W+L)", (d.gross_W + d.gross_L).median()),
                          ("median W + median L", d.gross_W.median() + d.gross_L.median()),
                          ("mean(W+L)", (d.gross_W + d.gross_L).mean())]:
            hit = "  <== MATCH" if abs(val - target[arm]) < 0.6 else ""
            print(f"      {name:32s} {stat:20s} n={len(d):5d} {val:9.3f}{hit}")

# row-level payoff scale from panel_C (arm C) and arm_B parquet
print("\n=== row-level payoff scale (arm C, panel_C) ===")
p = pd.read_parquet(R + "panel_C.parquet")
g = p["c_gross_bps"]
W = g[g > 0].mean(); L = -g[g < 0].mean()
print(f"  all rows: W={W:.3f} L={L:.3f} W+L={W+L:.3f}  (target {target['C']:.3f})")
print(f"  median |gross| = {g.abs().median():.3f}; 2*median|gross| = {2*g.abs().median():.3f}")

print("\n=== the 10 'trail' cells under the SUPERSEDED absolute target ===")
b = m[signed & (m.arm == "B")].copy()
b["pwr_sup"] = sup[b.index]; b["pwr_sig"] = tgt[b.index]
tr = b[b.exit_mode == "trail"]
print("  trail cells:", len(tr), "powered(absolute):", int(tr.pwr_sup.sum()),
      "powered(sigma):", int(tr.pwr_sig.sum()))
sel = tr[tr.pwr_sup]
print("  their gross means:", np.round(np.sort(sel.gross_mean.values), 2))
print("  excluded (absolute basis): n=%d  mean of means=%.3f  median=%.3f" %
      ((~tr.pwr_sup).sum(), tr.loc[~tr.pwr_sup, "gross_mean"].mean(), tr.loc[~tr.pwr_sup, "gross_mean"].median()))
cols = ["symbol", "band", "clock", "gross_n", "gross_p", "gross_W", "gross_L", "gross_W_L", "gross_mean",
        "gross_mean_ci_low", "gross_mean_ci_high", "gross_block_mde_mean_bps", "gross_edge"]
print(sel[cols].round(3).to_string())
print("\n  full trail population, gross_mean distribution:")
print(np.round(tr.gross_mean.quantile([0, .05, .25, .5, .75, .95, 1]).values, 2))
print("  trail cells with gross_mean > 0:", int((tr.gross_mean > 0).sum()), "/", len(tr))
print("  trail mean-of-means %.2f vs median-of-means %.2f  (left tail: min %.1f)" %
      (tr.gross_mean.mean(), tr.gross_mean.median(), tr.gross_mean.min()))

print("\n=== sign-selectivity of the two gates, per arm x exit_mode ===")
for basis, flag in [("sigma 1.785", tgt), ("absolute 10", sup)]:
    print(f"  --- basis {basis} ---")
    d = m[signed].copy(); d["pwr"] = flag[d.index]
    r = d.groupby("arm").apply(lambda x: pd.Series({
        "n": len(x), "powered": int(x.pwr.sum()),
        "pwr_mean": x.loc[x.pwr, "gross_mean"].mean(), "exc_mean": x.loc[~x.pwr, "gross_mean"].mean(),
        "pwr_share_pos": (x.loc[x.pwr, "gross_mean"] > 0).mean(),
        "exc_share_pos": (x.loc[~x.pwr, "gross_mean"] > 0).mean(),
        "pwr_payoff": (x.loc[x.pwr, "gross_W"] + x.loc[x.pwr, "gross_L"]).median(),
        "exc_payoff": (x.loc[~x.pwr, "gross_W"] + x.loc[~x.pwr, "gross_L"]).median(),
    }), include_groups=False)
    print(r.round(3).to_string())
