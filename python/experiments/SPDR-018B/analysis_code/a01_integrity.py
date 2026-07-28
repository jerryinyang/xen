"""SPDR-018B analyst a01 — integrity re-derivation from results/ only. No screen_code import."""
import json, numpy as np, pandas as pd
R="python/experiments/SPDR-018B/results/"
m=pd.read_parquet(R+"metrics_by_cell.parquet")
print("total cells", len(m))
print("\n-- arm counts --"); print(m.arm.value_counts().sort_index())
print("\n-- universe --", m.universe.unique() if 'universe' in m else None)
print("\n-- symbols --", sorted(m.symbol.dropna().unique().tolist()))

# 1. pass-field / at_or_above scan
bad=[c for c in m.columns if c=='pass' or c.startswith('pass_') or 'at_or_above_p' in c]
print("\n[1] offending columns:", bad)

# 2. identity on signed cells (gross family)
sg=m[m.gross_p.notna()].copy()
print("\n[2] signed cells (gross_p notna):", len(sg))
res=(sg.gross_p*sg.gross_W-(1-sg.gross_p)*sg.gross_L-sg.gross_mean_signed_rows).abs()
print("   identity residual vs mean_signed_rows: max %.3e  p99 %.3e  n>0.01bps %d"%(res.max(),res.quantile(.99),(res>0.01).sum()))
res2=(sg.gross_p*sg.gross_W-(1-sg.gross_p)*sg.gross_L-sg.gross_mean).abs()
print("   identity residual vs gross_mean      : max %.3e  median %.3e"%(res2.max(),res2.median()))
# p == n_pos/(n_pos+n_neg)
pp=sg.gross_n_pos/(sg.gross_n_pos+sg.gross_n_neg)
print("   max |p - n_pos/(n_pos+n_neg)| = %.3e"%(sg.gross_p-pp).abs().max())
# p_be, p_be_net reconstruction
pbe=sg.gross_L/(sg.gross_W+sg.gross_L)
print("   max |p_be - L/(W+L)| = %.3e"%(sg.gross_p_be-pbe).abs().max())
pben=(sg.gross_L+sg.gross_cost_bps)/(sg.gross_W+sg.gross_L)
print("   max |p_be_net - (L+c)/(W+L)| = %.3e"%(sg.gross_p_be_net-pben).abs().max())
print("   gross_cost_bps describe:"); print(sg.gross_cost_bps.describe())

# 3. powered counts
print("\n[3] at_parent_target_precision counts (all cells):")
print(m.at_parent_target_precision.value_counts(dropna=False))
pw=sg[sg.at_parent_target_precision==True]
print("   powered SIGNED cells:", len(pw))
print("   by arm:"); print(pw.arm.value_counts().sort_index())

# 4. band labels
print("\n[4] band_label_mean value counts (signed):")
print(sg.band_label_mean.value_counts(dropna=False))

# 5. flat rows
print("\n[5] gross_p_flat: median %.4f p95 %.4f max %.4f ; cells>0.05: %d"%(
   sg.gross_p_flat.median(),sg.gross_p_flat.quantile(.95),sg.gross_p_flat.max(),(sg.gross_p_flat>0.05).sum()))

# 6. mde source
print("\n[6] mde_source_for_bands (gross):", sg.gross_mde_source_for_bands.value_counts(dropna=False).to_dict())

# 7. holdout / fence from panel
p=pd.read_parquet(R+"panel_C.parquet")
print("\n[7] panel_C rows", len(p), "exit_ts max", p.exit_ts.max(), "min", p.entry_ts.min())
print("   rows >= 2024-12-13:", (pd.to_datetime(p.exit_ts,utc=True)>=pd.Timestamp("2024-12-13",tz="UTC")).sum())
print("   rows >= 2023-11-22 (train_end):", (pd.to_datetime(p.exit_ts,utc=True)>=pd.Timestamp("2023-11-22",tz="UTC")).sum())
print("   symbols:", sorted(p.symbol.unique().tolist()))
