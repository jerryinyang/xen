import numpy as np, pandas as pd
pd.set_option('display.width',250); pd.set_option('display.max_columns',60)
R="python/experiments/SPDR-018B/results/"
m=pd.read_parquet(R+"metrics_by_cell.parquet")
sg=m[m.gross_p.notna()].copy()
pw=sg[sg.at_parent_target_precision==True].copy()

print("=== band label semantics ===")
print(pd.crosstab(sg.band_label_mean,sg.at_parent_target_precision,dropna=False).to_string())

def mirror(d,name):
    d=d[(d.gross_p>0)&(d.gross_p<1)&(d.gross_W_L>0)].copy()
    y=np.log(d.gross_W_L); x=np.log((1-d.gross_p)/d.gross_p)
    if len(d)<10 or x.std()==0: return None
    b,a=np.polyfit(x,y,1); r=np.corrcoef(x,y)[0,1]
    logR=np.log(d.gross_p*d.gross_W/((1-d.gross_p)*d.gross_L))
    return dict(stratum=name,n=len(d),slope=b,intercept=a,R2=r*r,
        sd_logWL=y.std(),sd_mirror=x.std(),sd_logR=logR.std(),
        free_share=logR.std()/y.std(),med_logR=logR.median(),mean_logR=logR.mean(),
        mean_log_resid=(y-(a+b*x)).mean(),
        WL_med=d.gross_W_L.median(),WL_p5=d.gross_W_L.quantile(.05),WL_p95=d.gross_W_L.quantile(.95),
        WL_min=d.gross_W_L.min(),WL_max=d.gross_W_L.max())

print("\n=== MIRROR REGRESSION log(W/L) ~ log((1-p)/p) ===")
rows=[mirror(pw,'ALL POWERED'),mirror(sg,'ALL SIGNED')]
for a_,d in pw.groupby('arm'): rows.append(mirror(d,f'powered arm={a_}'))
for a_,d in sg.groupby('arm'): rows.append(mirror(d,f'signed arm={a_}'))
for s,d in pw.groupby('symbol'): rows.append(mirror(d,f'powered sym={s}'))
b=sg[sg.arm=='B']
rows.append(mirror(b,'arm B all signed (5 exit modes)'))
for e,d in b.groupby('exit_mode'): rows.append(mirror(d,f'armB exit={e}'))
print(pd.DataFrame([r for r in rows if r]).to_string(float_format=lambda x:f"{x:.4f}"))

print("\n=== ARM B MOVABILITY: exit mode table (ALL signed arm-B cells) ===")
b2=b.copy(); b2['mirror']=(1-b2.gross_p)/b2.gross_p
b2['logR']=np.log(b2.gross_p*b2.gross_W/((1-b2.gross_p)*b2.gross_L))
print(b2.groupby('exit_mode').agg(n=('gross_p','size'),p=('gross_p','median'),
   W_L=('gross_W_L','median'),mirror=('mirror','median'),logR=('logR','median'),
   gross=('gross_mean','median'),net=('net_mean','median'),W=('gross_W','median'),L=('gross_L','median'),
   powered=('at_parent_target_precision','sum'),nrows=('gross_n','median')).to_string(float_format=lambda x:f"{x:.4f}"))

print("\n=== per-cell: does W/L CI exclude the mirror value? (powered) ===")
for nm,d in [('ALL POWERED',pw),('armB powered',pw[pw.arm=='B']),('armC powered',pw[pw.arm=='C']),('armB all signed',b)]:
    dd=d[d.gross_W_L_ci_low.notna()&d.gross_W_L_ci_high.notna()].copy()
    mir=(1-dd.gross_p)/dd.gross_p
    excl=((mir<dd.gross_W_L_ci_low)|(mir>dd.gross_W_L_ci_high))
    print(f"  {nm:16s} n_with_CI {len(dd):5d}  CI excludes mirror {excl.sum():5d} ({excl.mean():.3f})  -> cannot distinguish {1-excl.mean():.3f}")

print("\n=== R = pW/((1-p)L) on powered ===")
Rr=pw.gross_p*pw.gross_W/((1-pw.gross_p)*pw.gross_L)
print("  median %.4f  p5 %.4f p95 %.4f min %.4f max %.4f ; share |logR|<0.05 = %.3f"%(
   Rr.median(),Rr.quantile(.05),Rr.quantile(.95),Rr.min(),Rr.max(),(np.abs(np.log(Rr))<0.05).mean()))
print("  median |gross_mean|/W = %.4f"%(pw.gross_mean.abs()/pw.gross_W).median())
ci=pw[pw.gross_mean_ci_low.notna()]
exz=((ci.gross_mean_ci_low>0)|(ci.gross_mean_ci_high<0))
print("  powered cells with gross-mean CI excluding zero: %d/%d = %.4f ; of those, negative: %d"%(
   exz.sum(),len(ci),exz.mean(),(ci[exz].gross_mean<0).sum()))
