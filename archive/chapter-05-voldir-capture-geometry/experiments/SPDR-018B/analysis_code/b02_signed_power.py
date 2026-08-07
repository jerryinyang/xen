"""Signed-cell definition, power counts, identity residual, headline (p,W,L) picture."""
import numpy as np
import pandas as pd

R = "python/experiments/SPDR-018B/results/"
m = pd.read_parquet(R + "metrics_by_cell.parquet")
tgt = m["at_parent_target_precision"].fillna(False).astype(bool)
sup = m["at_parent_target_precision_absolute__SUPERSEDED"].fillna(0).astype(bool)

print("=== candidate 'signed' definitions ===")
defs = {
    "gross_p notnull": m["gross_p"].notna(),
    "gross_p & W & L notnull": m["gross_p"].notna() & m["gross_W"].notna() & m["gross_L"].notna(),
    "gross_n notnull": m["gross_n"].notna(),
    "sigma_target notnull": m["target_mde_bps_sigma_scaled"].notna(),
    "gross_mean notnull": m["gross_mean"].notna(),
}
for k, v in defs.items():
    print(f"  {k:28s} n={v.sum():5d}  at_target={int((v&tgt).sum()):5d}  superseded={int((v&sup).sum()):5d}")

signed = defs["gross_p & W & L notnull"]

print("\n=== identity residual, re-derived by me (gross) ===")
s = m[signed].copy()
recon = s["gross_p"] * s["gross_W"] - (1 - s["gross_p"]) * s["gross_L"]
res = (recon - s["gross_mean_signed_rows"]).abs()
print("max residual vs mean_signed_rows (bps):", res.max(), " cells>0.01:", int((res > 0.01).sum()))
res2 = (recon - s["gross_mean"]).abs()
print("max residual vs gross_mean (bps):", res2.max(), " p99:", res2.quantile(0.99))
print("emitted gross_identity_residual_bps max:", s["gross_identity_residual_bps"].max())
print("p == n_pos/(n_pos+n_neg) max diff:",
      (s["gross_p"] - s["gross_n_pos"] / (s["gross_n_pos"] + s["gross_n_neg"])).abs().max())
print("p_flat median/p95/max:", s["gross_p_flat"].median(), s["gross_p_flat"].quantile(.95), s["gross_p_flat"].max())

print("\n=== break-even re-derivation from W,L,cost ===")
pbe = s["gross_L"] / (s["gross_W"] + s["gross_L"])
print("max |p_be - derived|:", (s["gross_p_be"] - pbe).abs().max())
c = s["gross_cost_bps"]
pbe_net = (s["gross_L"] + c) / (s["gross_W"] + s["gross_L"])
print("max |p_be_net - (L+c)/(W+L)|:", (s["gross_p_be_net"] - pbe_net).abs().max())
edge_d = s["gross_p"] - s["gross_p_be_net"]
print("max |gross_edge - (p - p_be_net)|:", (s["gross_edge"] - edge_d).abs().max())
print("cost charged: median", c.median(), "min", c.min(), "max", c.max())
print("unscaled net cost present?", [x for x in m.columns if "unscaled" in x.lower()])

def picture(df, label):
    d = dict(
        label=label, n_cells=len(df),
        med_n=df["gross_n"].median(),
        p=df["gross_p"].median(), W=df["gross_W"].median(), L=df["gross_L"].median(),
        W_L=df["gross_W_L"].median(),
        p_be=df["gross_p_be"].median(), p_be_net=df["gross_p_be_net"].median(),
        edge=df["gross_edge"].median(),
        gross_bps=df["gross_mean"].median(), net_bps=df["net_mean"].median(),
        gross_median_bps=df["gross_median"].median(),
        gross_trim10=df["gross_trimmed_mean_10"].median(),
        cost=df["gross_cost_bps"].median(),
        share_above_gross_be=(df["gross_p"] > df["gross_p_be"]).mean(),
        share_above_net_be=(df["gross_p"] > df["gross_p_be_net"]).mean(),
        share_WL_gt1=(df["gross_W_L"] > 1).mean(),
    )
    return d

pw = m[signed & tgt]
print("\n=== HEADLINE: 315 powered signed cells (sigma-scaled target) ===")
for k, v in picture(pw, "powered_sigma").items():
    print(f"  {k:22s} {v}")
print("\n=== superseded basis (absolute 10bps) for comparison ===")
for k, v in picture(m[signed & sup], "powered_absolute").items():
    print(f"  {k:22s} {v}")
print("\n=== all signed cells ===")
for k, v in picture(m[signed], "all_signed").items():
    print(f"  {k:22s} {v}")

print("\n=== net-clearing counts ===")
for name, sel in [("sigma-powered", signed & tgt), ("absolute-powered", signed & sup)]:
    d = m[sel]
    print(f"  {name}: n={len(d)} clears gross={int((d.gross_p>d.gross_p_be).sum())} "
          f"clears net={int((d.gross_p>d.gross_p_be_net).sum())} "
          f"({(d.gross_p>d.gross_p_be_net).mean()*100:.2f}%)")

print("\n=== band labels (mean) over all cells ===")
print(m["band_label_mean"].value_counts(dropna=False).to_string())
print("\n=== band labels on the 315 ===")
print(pw["band_label_mean"].value_counts(dropna=False).to_string())
print("\nNOT_RESOLVABLE (mean) count:", int((m["band_label_mean"] == "NOT_RESOLVABLE").sum()))
print("levers_exhausted:", int(m["levers_exhausted"].fillna(False).sum()))

print("\n=== powered cells by arm ===")
print(m[signed].assign(t=tgt).groupby("arm").agg(signed=("gross_p", "size"), powered=("t", "sum")).to_string())
