import numpy as np, pandas as pd
pd.set_option('display.width',250); pd.set_option('display.max_columns',60)
R="python/experiments/SPDR-018B/results/"
m=pd.read_parquet(R+"metrics_by_cell.parquet")
sg=m[m.gross_p.notna()].copy()
pw=sg[sg.at_parent_target_precision==True].copy()
print("powered signed:",len(pw),"of",len(sg))

def pic(d,name):
    return dict(stratum=name,n_cells=len(d),
        p=d.gross_p.median(),W=d.gross_W.median(),L=d.gross_L.median(),
        W_L=d.gross_W_L.median(),p_be=d.gross_p_be.median(),p_be_net=d.gross_p_be_net.median(),
        gross_mean=d.gross_mean.median(),net_mean=d.net_mean.median() if 'net_mean' in d else np.nan,
        cost=d.gross_cost_bps.median(),
        clears_gross=float((d.gross_p>d.gross_p_be).mean()),
        clears_net=float((d.gross_p>d.gross_p_be_net).mean()),
        median_n=d.gross_n.median())
print("\n=== HEADLINE (powered signed) ===")
h=pic(pw,'ALL POWERED'); 
for k,v in h.items(): print(f"  {k:14s} {v}")
print("\n screen claims: p .4922 p_be .4917 p_be_net .5265 W/L 1.034 gross -0.08 net -2.62 clears_gross .475 clears_net .129")

rows=[pic(pw,'ALL POWERED')]
for col in ['symbol','arm','band','clock','exit_mode','basis','residue_item']:
    if col not in pw: continue
    for v,d in pw.groupby(col,dropna=False):
        if len(d)<1: continue
        rows.append(pic(d,f"{col}={v}"))
T=pd.DataFrame(rows)
T.to_csv("python/experiments/SPDR-018B/results/analyst_stratum_tables.csv",index=False)
print("\n=== PER-STRATUM (powered signed) ===")
print(T.to_string(float_format=lambda x:f"{x:.4f}"))
