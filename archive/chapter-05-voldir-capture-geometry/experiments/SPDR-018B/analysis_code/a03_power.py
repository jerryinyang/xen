import numpy as np, pandas as pd
pd.set_option('display.width',250); pd.set_option('display.max_columns',60)
R="python/experiments/SPDR-018B/results/"
m=pd.read_parquet(R+"metrics_by_cell.parquet")
sg=m[m.gross_p.notna()].copy()
print("=== target rules present (signed) ===")
print(sg.groupby(['arm','target_rule']).agg(n=('gross_p','size'),
    tgt=('target_mde','median'), mde=('gross_block_mde_mean_bps','median'),
    nmed=('gross_n','median'), pw=('at_parent_target_precision','mean')).to_string())
print("\n=== block MDE distribution by arm (signed) ===")
print(sg.groupby('arm')['gross_block_mde_mean_bps'].describe().to_string())
print("\n=== target_mde distribution by arm ===")
print(sg.groupby('arm')['target_mde'].describe().to_string())
print("\n=== sigma-normalised: MDE/sigma  (cTrader pooled sigma 13.034) ===")
sig=13.034237315995593
for a,d in sg.groupby('arm'):
    print(f"  arm {a}: median MDE {d.gross_block_mde_mean_bps.median():.3f} bps = {d.gross_block_mde_mean_bps.median()/sig:.4f} sigma ; target {d.target_mde.median():.3f} bps = {d.target_mde.median()/sig:.4f} sigma")
print("  crypto sigma 73.001 -> a 13.5bps target is 0.1849 sigma ; on cTrader 13.5bps = %.4f sigma"%(13.5/sig))
print("\n=== powered share by arm ===")
print(sg.groupby('arm').at_parent_target_precision.agg(['size','sum','mean']).to_string())
print("\n=== NOT_RESOLVABLE / UNPOWERED breakdown by arm & symbol ===")
print(pd.crosstab([sg.arm,sg.symbol],sg.band_label_mean,dropna=False).to_string())
