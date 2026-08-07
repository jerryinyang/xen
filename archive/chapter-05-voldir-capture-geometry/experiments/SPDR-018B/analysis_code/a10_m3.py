"""Analyst's own M-3 magnitude-matched comparator, on GROSS and on the MOMO subset."""
import numpy as np, pandas as pd
pd.set_option('display.width',260)
R="python/experiments/SPDR-018B/results/"
p=pd.read_parquet(R+"panel_C.parquet")
p['dt']=pd.to_datetime(p.event_ts,utc=True)
print("check c_gross_bps == side*r_h ?",np.nanmax(np.abs(p.c_gross_bps-p.side*p.r_h)))
print("check c_net_bps == c_gross - cost_vs ?",np.nanmax(np.abs(p.c_net_bps-(p.c_gross_bps-p.cost_bps_vol_scaled))))
print("cost_bps_vol_scaled describe:"); print(p.cost_bps_vol_scaled.describe().to_string())
print("cost_raw_bps describe:"); print(p.cost_raw_bps.describe().to_string())
print("vol_scale_ratio:",p.vol_scale_ratio.unique()[:5])
print("\npolicy counts:"); print(p.policy.value_counts(dropna=False).to_string())
print("gross_bps non-null by policy:"); print(p.groupby('policy').gross_bps.count().to_string())

def m3(live_mask, pool_mask, col, nseed=2000, seed=7, exclude_bars=1, label=""):
    d=p.copy()
    live=d[live_mask].dropna(subset=[col])
    # neighbourhood exclusion: drop pool rows within +-1 t_idx of a live row, same symbol/clock/band/z/H
    key=['symbol','clock','band','z','H']
    liveidx=set(zip(*[live[k] for k in key],live.t_idx))
    pool=d[pool_mask].dropna(subset=[col]).copy()
    def near(r):
        return any((r.symbol,r.clock,r.band,r.z,r.H,r.t_idx+o) in liveidx for o in (-1,0,1))
    pool=pool[~pool.apply(near,axis=1)]
    if len(live)==0 or len(pool)==0: return None
    a=np.abs(live.r_h.values); q=np.quantile(a,np.linspace(0,1,11)); q[0]=-np.inf; q[-1]=np.inf
    lb=np.digitize(np.abs(live.r_h.values),q[1:-1]); pb=np.digitize(np.abs(pool.r_h.values),q[1:-1])
    need=np.bincount(lb,minlength=10); pv=pool[col].values
    idx=[np.where(pb==k)[0] for k in range(10)]
    supply=[len(i) for i in idx]
    rng=np.random.default_rng(seed); nulls=np.empty(nseed)
    for s in range(nseed):
        acc=[]
        for k in range(10):
            if need[k]==0: continue
            if supply[k]==0: continue
            acc.append(pv[rng.choice(idx[k],need[k],replace=True)])
        nulls[s]=np.concatenate(acc).mean()
    lv=live[col].mean()
    pct=float((nulls<lv).mean())
    return dict(label=label,col=col,n_live=len(live),n_pool=len(pool),live=lv,
        null_mean=nulls.mean(),null_sd=nulls.std(),pct=pct,
        q05=np.quantile(nulls,.05),q95=np.quantile(nulls,.95),
        delta=lv-nulls.mean(),deciles_no_supply=[k for k in range(10) if need[k]>0 and supply[k]==0])

rows=[]
sh=p.shock_flag==True; nsh=p.shock_flag==False
momo=p.policy=='P-MOMO'; mr=p.policy=='P-MR'
for col in ['c_gross_bps','c_net_bps','c_net_unscaled_bps']:
    r=m3(sh,nsh,col,label="FULL PANEL shock vs non-shock"); rows.append(r); print(r)
for col in ['gross_bps','partial_net_bps']:
    r=m3(sh&momo,nsh&momo,col,label="P-MOMO ONLY shock vs non-shock"); rows.append(r); print(r)
    r=m3(sh&mr,nsh&mr,col,label="P-MR ONLY shock vs non-shock"); rows.append(r); print(r)
pd.DataFrame(rows).to_csv("python/experiments/SPDR-018B/results/analyst_m3.csv",index=False)
print("\n",pd.DataFrame(rows).to_string())
