import numpy as np, pandas as pd, json
pd.set_option('display.width',260); pd.set_option('display.max_columns',60)
R="python/experiments/SPDR-018B/results/"
p=pd.read_parquet(R+"panel_C.parquet")
print("rows",len(p))
print("\nnon-null counts:"); print(p[['r_h','gross_bps','partial_net_bps','c_gross_bps','c_net_bps','c_net_unscaled_bps','side','label']].notna().sum().to_string())
print("\n=== RAW SPLIT on each candidate column, by shock_flag ===")
for col in ['r_h','gross_bps','partial_net_bps','c_gross_bps','c_net_bps','c_net_unscaled_bps']:
    g=p.groupby('shock_flag')[col].agg(['size','count','mean','median'])
    print(f"\n-- {col} --"); print(g.to_string())

print("\n=== try to reproduce control live effects ===")
# full panel: live -4.2098 on n_live 30319
for col in ['r_h','c_gross_bps','gross_bps']:
    d=p[p.shock_flag==True]
    print(f"  full-panel shock mean {col}: {d[col].mean():.4f} (n={d[col].count()})")
# primary cell n_live 290
print("\n  hunting the primary cell (n_live 290, live -9.3832):")
best=[]
for (sym,clk,bnd,z,H,h,pol,et),d in p.groupby(['symbol','clock','band','z','H','h','policy','event_type'],dropna=False):
    dd=d[d.shock_flag==True]
    for col in ['c_gross_bps','r_h','gross_bps']:
        v=dd[col]
        if v.count()==290: best.append((sym,clk,bnd,z,H,h,pol,et,col,v.count(),v.mean()))
for b in best[:40]: print("   ",b)
