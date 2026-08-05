"""Probe 11 (read-only): LEVEL_FORECAST_K4 / K12 behaviour, esp. on the surviving SIZE device."""
import polars as pl
ROOT='python/experiments'
CELLS=[(e,u) for e in ('SPDR-021','SPDR-022','SPDR-023') for u in ('ctrader','crypto')]
def P(e,u,f): return f'{ROOT}/{e}/results/analysis/{u}/{f}'
print('=== SIZE / drawdown_bps by COMPONENT (the surviving lever) ===')
print(f'{"cell":13s} {"component":22s} {"n":>4s} {"res":>4s} {"pos":>4s} {"neg":>4s} {"medEst":>11s} {"e/MDE":>6s}')
for e,u in CELLS:
    d=pl.read_parquet(P(e,u,'device_size.parquet')).filter(
        (pl.col('arm_class')!='FIXED_MANAGEMENT')&(pl.col('state')=='ORDER_CREATED')&
        (pl.col('metric_name')=='drawdown_bps')&pl.col('estimate').is_finite())
    for c in sorted({str(x) for x in d['component'].to_list()}):
        x=d.filter(pl.col('component')==c)
        r=x.filter((pl.col('ci_low')>0)|(pl.col('ci_high')<0))
        me=x['estimate'].median(); mm=x['mde'].median()
        print(f'{e[-3:]+"/"+u[:4]:13s} {c:22s} {x.height:4d} {r.height:4d} {r.filter(pl.col("ci_low")>0).height:4d} {r.filter(pl.col("ci_high")<0).height:4d} {me:11.2f} {abs(me)/mm if mm else float("nan"):6.2f}')
    print()
print('=== SIZE / risk_dispersion by COMPONENT (forced reference) — same split ===')
for e,u in [('SPDR-021','ctrader'),('SPDR-021','crypto')]:
    d=pl.read_parquet(P(e,u,'device_size.parquet')).filter(
        (pl.col('arm_class')!='FIXED_MANAGEMENT')&(pl.col('state')=='ORDER_CREATED')&
        (pl.col('metric_name')=='risk_dispersion')&pl.col('estimate').is_finite())
    g=d.group_by('component').agg([pl.len(),(((pl.col('ci_low')>0)|(pl.col('ci_high')<0))).sum().alias('res'),
        pl.col('estimate').median().alias('med'),pl.col('mde').median().alias('mde')]).sort('component')
    print(e[-3:],u); print(g)
