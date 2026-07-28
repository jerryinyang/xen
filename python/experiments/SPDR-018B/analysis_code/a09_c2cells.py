import numpy as np, pandas as pd
pd.set_option('display.width',280); pd.set_option('display.max_columns',60)
R="python/experiments/SPDR-018B/results/"
m=pd.read_parquet(R+"metrics_by_cell.parquet")
c=m[(m.arm=='C')&m.gross_p.notna()].copy()
print("arm C signed cells",len(c))
print("\nconditioner values:"); print(c.conditioner.value_counts(dropna=False).to_string())
print("\nconditioner_value:"); print(c.conditioner_value.value_counts(dropna=False).to_string())
print("\nresidue_item C2 cells:", (c.residue_item=='C2').sum())

sh=c[c.conditioner=='shock_flag'] if 'shock_flag' in set(c.conditioner.dropna()) else None
print("\n=== cells grouped by conditioner+value (all arm C signed) ===")
g=c.groupby(['conditioner','conditioner_value'],dropna=False).agg(
   n_cells=('gross_p','size'),rows=('gross_n','sum'),pw=('at_parent_target_precision','sum'),
   gross_mean_of_mean=('gross_mean','mean'),gross_med=('gross_mean','median'),
   net_med=('net_mean','median'),p=('gross_p','median'),WL=('gross_W_L','median'))
print(g.to_string(float_format=lambda x:f"{x:.4f}"))

print("\n=== POWERED only ===")
cp=c[c.at_parent_target_precision==True]
g2=cp.groupby(['conditioner','conditioner_value'],dropna=False).agg(
   n_cells=('gross_p','size'),rows=('gross_n','sum'),
   gross_mean_of_mean=('gross_mean','mean'),gross_med=('gross_mean','median'),
   ci_lo=('gross_mean_ci_low','median'),ci_hi=('gross_mean_ci_high','median'),
   net_med=('net_mean','median'),p=('gross_p','median'),p_be=('gross_p_be','median'))
print(g2.to_string(float_format=lambda x:f"{x:.4f}"))

print("\n=== C2 residue item detail (per policy/symbol) ===")
c2=c[c.residue_item=='C2']
print("C2 cells",len(c2),"powered",int(c2.at_parent_target_precision.sum()))
print(c2.groupby(['conditioner','conditioner_value','policy'],dropna=False).agg(
  n=('gross_p','size'),pw=('at_parent_target_precision','sum'),
  gross=('gross_mean','median'),net=('net_mean','median'),rows=('gross_n','median')).to_string(float_format=lambda x:f"{x:.4f}"))
c2p=c2[c2.at_parent_target_precision==True]
print("\nC2 powered by policy x symbol:")
print(c2p.groupby(['policy','symbol'],dropna=False).agg(n=('gross_p','size'),
  gross=('gross_mean','median'),lo=('gross_mean_ci_low','median'),hi=('gross_mean_ci_high','median'),
  net=('net_mean','median'),rows=('gross_n','median')).to_string(float_format=lambda x:f"{x:.4f}"))
