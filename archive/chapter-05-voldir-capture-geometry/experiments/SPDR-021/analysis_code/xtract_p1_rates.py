"""Extraction probe 1 (read-only): per-cell interval-exclusion rates. Finite rows only."""
import polars as pl, json

ROOT='python/experiments'
CELLS=[(e,u) for e in ('SPDR-021','SPDR-022','SPDR-023') for u in ('ctrader','crypto')]
DEV=['target','stop','trail','hold','size']
def P(e,u,f): return f'{ROOT}/{e}/results/analysis/{u}/{f}'
FIN=lambda c: pl.col(c).is_finite()

def load_dev(e,u):
    fr=[]
    for d in DEV:
        x=pl.read_parquet(P(e,u,f'device_{d}.parquet')).with_columns(pl.lit(d.upper()).alias('dev'))
        fr.append(x)
    return pl.concat(fr)

def rates(df,label):
    f=df.filter(FIN('estimate')&FIN('ci_low')&FIN('ci_high'))
    n=f.height
    excl=f.filter((pl.col('ci_low')>0)|(pl.col('ci_high')<0)).height
    exact0=f.filter((pl.col('ci_low')==0)&(pl.col('ci_high')==0)&(pl.col('estimate')==0)).height
    m=f.filter(FIN('mde'))
    mh=m.filter(pl.col('estimate').abs()>pl.col('mde')).height
    print(f'{label:34s} finite={n:6d} CIexcl0={excl:5d} ({excl/max(n,1):6.2%})  exactzero={exact0:5d}  |est|>MDE={mh:5d}/{m.height:6d} ({mh/max(m.height,1):6.2%})')
    return dict(finite=n,ci_excl=excl,exact_zero=exact0,mde_hit=mh,mde_rows=m.height)

out={}
print('=== P1a devices (non-fixed arms, ORDER_CREATED state) ===')
for e,u in CELLS:
    d=load_dev(e,u).filter((pl.col('arm_class')!='FIXED_MANAGEMENT')&(pl.col('state')=='ORDER_CREATED'))
    out[f'{e}|{u}|dev']=rates(d,f'{e} {u} DEVICE')
print()
print('=== P1a2 devices split by metric ===')
for e,u in CELLS:
    d=load_dev(e,u).filter((pl.col('arm_class')!='FIXED_MANAGEMENT')&(pl.col('state')=='ORDER_CREATED'))
    for met in sorted(set(d['metric_name'].to_list())):
        rates(d.filter(pl.col('metric_name')==met), f'  {e[-3:]}/{u[:3]} {met}')
    print()
print('=== P1b native origin lens (non-fixed, state=ALL) ===')
for e,u in CELLS:
    n=pl.read_parquet(P(e,u,'native_parameter_origins.parquet')).filter(
        (pl.col('arm_class')!='FIXED_NATIVE')&(pl.col('state')=='ALL'))
    out[f'{e}|{u}|nat']=rates(n,f'{e} {u} NATIVE(ALL)')
print()
print('=== P1c native trade lens (per_stratum COMMON_CLOSE_TRADE, native arms) ===')
for e,u in CELLS:
    p=pl.read_parquet(P(e,u,'per_stratum_estimates.parquet')).filter(
        (pl.col('estimate_source')=='COMMON_CLOSE_TRADE')&pl.col('arm_class').is_in(['NATIVE','NATIVE_COMBINATION']))
    out[f'{e}|{u}|nat_trade']=rates(p,f'{e} {u} NATIVE-TRADE')
json.dump(out,open('/private/tmp/claude-501/-Users-jerryinyang-cAlgo-Sources-Robots-Xen-Xen/6c93bc6e-0610-4c88-b3f7-f08115a752da/scratchpad/p1.json','w'),indent=1)
