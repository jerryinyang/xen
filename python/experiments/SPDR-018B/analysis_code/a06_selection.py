import numpy as np, pandas as pd
pd.set_option('display.width',260)
R="python/experiments/SPDR-018B/results/"
m=pd.read_parquet(R+"metrics_by_cell.parquet")
sg=m[m.gross_p.notna()].copy()
print("=== Does the precision filter (MDE<=10bps) select on realised dispersion? ===")
for nm,d in [('ALL signed',sg),('arm B',sg[sg.arm=='B']),('arm C',sg[sg.arm=='C']),
             ('armB trail',sg[(sg.arm=='B')&(sg.exit_mode=='trail')]),
             ('armB stop',sg[(sg.arm=='B')&(sg.exit_mode=='stop')])]:
    g=d.groupby('at_parent_target_precision')
    print(f"\n{nm}:")
    print(g.agg(n=('gross_mean','size'),mean_of_mean=('gross_mean','mean'),med_of_mean=('gross_mean','median'),
      mde=('gross_block_mde_mean_bps','median'),W=('gross_W','median'),L=('gross_L','median'),
      nrows=('gross_n','median'),skew_proxy=('gross_L','median')).to_string(float_format=lambda x:f"{x:.3f}"))

print("\n=== implied per-episode sd from block MDE (sd ~ MDE*sqrt(n)/1.96) vs W,L ===")
sg['implied_sd']=sg.gross_block_mde_mean_bps*np.sqrt(sg.gross_n)/1.96
t=sg[(sg.arm=='B')&(sg.exit_mode=='trail')]
print(t.groupby('at_parent_target_precision')[['implied_sd','gross_W','gross_L','gross_mean','gross_n']].median().to_string())

print("\n=== per-cell gross-mean CI excluding zero: sign balance, per stratum (powered) ===")
pw=sg[sg.at_parent_target_precision==True]
def sgn(d):
    dd=d[d.gross_mean_ci_low.notna()]
    ex=(dd.gross_mean_ci_low>0)|(dd.gross_mean_ci_high<0)
    e=dd[ex]
    return dict(n=len(dd),n_excl=int(ex.sum()),frac=float(ex.mean()) if len(dd) else np.nan,
                neg=int((e.gross_mean<0).sum()),pos=int((e.gross_mean>0).sum()),
                max_pos_gross=float(e.gross_mean.max()) if len(e) else np.nan)
rows=[dict(stratum='ALL POWERED',**sgn(pw))]
for c in ['arm','symbol','exit_mode','band']:
    for v,d in pw.groupby(c,dropna=False): rows.append(dict(stratum=f'{c}={v}',**sgn(d)))
print(pd.DataFrame(rows).to_string())
