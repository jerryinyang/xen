"""SPDR-018 fresh-context analyst — pass 1: inventory, fences, identity, powered counts.

Re-derives everything from results/*.parquet. Never imports screen_code/.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen")
RES = ROOT / "python/experiments/SPDR-018/results"
OUT = RES

pd.set_option("display.width", 260)
pd.set_option("display.max_columns", 80)

m = pd.read_parquet(RES / "metrics_by_cell.parquet")

print("=" * 90)
print("A. CELL INVENTORY")
print("=" * 90)
print("total cells:", len(m))
print(m.groupby("arm").size())

# residue item expansion (cells can carry multiple items)
rows = []
for it, sub in m.groupby("residue_item"):
    for tag in str(it).split(","):
        rows.append((tag.strip(), len(sub)))
inv = pd.DataFrame(rows, columns=["item", "n"]).groupby("item")["n"].sum().sort_index()
print("\nresidue item coverage (expanded, cells may double-count):")
print(inv.to_string())

print("\n" + "=" * 90)
print("B. SIGNED CELLS AND THE (p,W,L) LAYER")
print("=" * 90)
signed = m[m["net_p"].notna()].copy()
print("cells with net_p:", len(signed))
print("cells with gross_p:", m["gross_p"].notna().sum())
print("cells with unprefixed p:", m["p"].notna().sum())

# do the unprefixed columns duplicate gross or net?
both = m[m["p"].notna() & m["net_p"].notna()]
print("unprefixed p == net_p on overlap:", np.allclose(both["p"], both["net_p"], equal_nan=True), len(both))
both2 = m[m["p"].notna() & m["gross_p"].notna()]
print("unprefixed p == gross_p on overlap:", np.allclose(both2["p"], both2["gross_p"], equal_nan=True), len(both2))

print("\n" + "=" * 90)
print("C. IDENTITY RECONSTRUCTION  |p*W - (1-p)*L - mean| (re-derived by analyst)")
print("=" * 90)
for pref in ["gross", "net"]:
    s = m[m[f"{pref}_p"].notna()]
    lhs = s[f"{pref}_p"] * s[f"{pref}_W"] - (1 - s[f"{pref}_p"]) * s[f"{pref}_L"]
    resid = (lhs - s[f"{pref}_mean"]).abs()
    print(f"{pref}: n={len(s)}  max|resid|={resid.max():.3e} bps  "
          f"p99={resid.quantile(0.99):.3e}  n_over_0.01bps={(resid > 0.01).sum()}")
    # flat-row handling: does p exclude zeros?
    print(f"   p_flat: median={s[f'{pref}_p_flat'].median():.6f} max={s[f'{pref}_p_flat'].max():.4f}")
    # check p == n_pos/(n_pos+n_neg)
    denom = s[f"{pref}_n_pos"] + s[f"{pref}_n_neg"]
    pr = s[f"{pref}_n_pos"] / denom
    print(f"   p == n_pos/(n_pos+n_neg): maxdiff={np.nanmax(np.abs(pr - s[f'{pref}_p'])):.3e}")

print("\n" + "=" * 90)
print("D. BREAK-EVEN / EDGE RE-DERIVATION")
print("=" * 90)
s = m[m["net_p"].notna()]
pbe = s["net_L"] / (s["net_W"] + s["net_L"])
print("gross p_be recompute vs net_p_be: max diff", np.nanmax(np.abs(pbe - s["net_p_be"])))
pben = (s["net_L"] + s["net_cost_bps"]) / (s["net_W"] + s["net_L"])
print("p_be_net recompute vs net_p_be_net: max diff", np.nanmax(np.abs(pben - s["net_p_be_net"])))
print("edge recompute vs net_edge: max diff", np.nanmax(np.abs((s["net_p"] - s["net_p_be_net"]) - s["net_edge"])))

print("\n" + "=" * 90)
print("E. POWERED SIGNED CELLS")
print("=" * 90)
pw = m[(m["at_parent_target_precision"] == True) & (m["net_p"].notna())]
print("signed & at parent target precision:", len(pw))
allterms = pw[pw[["net_p", "net_W", "net_L", "net_p_be_net"]].notna().all(axis=1)]
print("with all (p,W,L,p_be_net) terms:", len(allterms))
print("\nMEDIANS (screen.md claims in brackets):")
claims = {
    "net_p": 0.3887, "net_W": 128.6, "net_L": 75.6, "net_W_L": 1.484,
    "net_p_be": 0.4025, "net_p_be_net": 0.4992, "gross_mean": -1.18,
    "net_mean": -15.16, "net_cost_bps": 13.54,
}
for k, v in claims.items():
    got = allterms[k].median()
    print(f"  {k:16s} analyst={got:12.4f}   screen={v:10.4f}   diff={got - v:+.4f}")

print("\nW/L > 1 fraction: %.4f  (screen 0.999)" % (allterms["net_W_L"] > 1).mean())
print("above GROSS break-even (p > p_be): %.4f  (screen 0.325)" % (allterms["net_p"] > allterms["net_p_be"]).mean())
print("above NET break-even (p > p_be_net): %.6f  (screen 0.000)" % (allterms["net_p"] > allterms["net_p_be_net"]).mean())
print("count above net be:", (allterms["net_p"] > allterms["net_p_be_net"]).sum())
print("p > 0.5 fraction: %.4f (screen 0.005) [disclosure only, never a reference]" % (allterms["net_p"] > 0.5).mean())
print("median (p_be_net - p_be) cost term: %.4f (screen +0.0650)" % (allterms["net_p_be_net"] - allterms["net_p_be"]).median())
print("median (p_be - p) rate term:        %.4f (screen +0.0067)" % (allterms["net_p_be"] - allterms["net_p"]).median())
print("median net_edge: %.4f" % allterms["net_edge"].median())
print("median gross_edge: %.4f" % allterms["gross_edge"].median())

print("\n" + "=" * 90)
print("F. BAND LABELS")
print("=" * 90)
for col in ["band_label_mean", "band_label_edge", "band_label_ic", "band_label_gap", "band_label_r2"]:
    if col in m:
        vc = m.groupby("arm")[col].value_counts().unstack(fill_value=0)
        if vc.values.sum():
            print(f"\n{col}:")
            print(vc.to_string())

print("\n" + "=" * 90)
print("G. NOT_RESOLVABLE")
print("=" * 90)
nr = json.loads((RES / "not_resolvable.json").read_text())
print("type:", type(nr), (list(nr.keys())[:10] if isinstance(nr, dict) else len(nr)))
