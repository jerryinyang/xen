import numpy as np, pandas as pd
pd.set_option('display.width',260); pd.set_option('display.max_columns',60)
R="python/experiments/SPDR-018B/results/"
m=pd.read_parquet(R+"metrics_by_cell.parquet")
b=m[(m.arm=='B')&m.gross_p.notna()].copy()
print("=== arm B: mean vs median vs trimmed by exit mode (all signed) ===")
print(b.groupby('exit_mode').agg(n=('gross_p','size'),nrows=('gross_n','median'),
  mean=('gross_mean','median'),median=('gross_median','median'),trim=('gross_trimmed_mean_10','median'),
  netmean=('net_mean','median'),netmedian=('net_median','median'),
  mde=('gross_block_mde_mean_bps','median'),pw=('at_parent_target_precision','sum'),
  ndates=('gross_n_dates','median')).to_string(float_format=lambda x:f"{x:.3f}"))

print("\n=== the 10 POWERED trail cells + 11 powered stop cells ===")
cols=['symbol','band','clock','basis','signal','residue_item','gross_n','gross_n_dates','gross_p','gross_W','gross_L','gross_W_L','gross_mean','gross_median','gross_trimmed_mean_10','net_mean','gross_block_mde_mean_bps','gross_mean_ci_low','gross_mean_ci_high','gross_cost_bps','gross_p_be_net']
for em in ['trail','stop','time']:
    d=b[(b.exit_mode==em)&(b.at_parent_target_precision==True)]
    print(f"\n--- {em} powered ({len(d)}) ---")
    print(d[cols].to_string(float_format=lambda x:f"{x:.3f}"))

print("\n=== how can n=68 be powered at MDE<=10bps? block MDE for trail powered ===")
d=b[(b.exit_mode=='trail')]
print(d[['gross_n','gross_n_dates','gross_block_mde_mean_bps','at_parent_target_precision','thirds_sign_agree','thirds_populated']].describe().to_string())
