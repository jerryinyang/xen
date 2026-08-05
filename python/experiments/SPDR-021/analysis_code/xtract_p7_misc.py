"""Probe 7 (read-only): sign shares, controls diagnosticity, concentration leave-out, baselines."""
import polars as pl
ROOT='python/experiments'
CELLS=[(e,u) for e in ('SPDR-021','SPDR-022','SPDR-023') for u in ('ctrader','crypto')]
def P(e,u,f): return f'{ROOT}/{e}/results/analysis/{u}/{f}'

print('=== P7a sign share (ALL finite rows), FREE metrics of interest ===')
for dev,met in [('size','drawdown_bps'),('size','concentration'),('hold','outcome_by_time_bps'),
                ('trail','favourable_excursion_captured'),('stop','recovery_after_stop_bps')]:
    print(f'-- {dev}/{met}')
    for e,u in CELLS:
        d=pl.read_parquet(P(e,u,f'device_{dev}.parquet')).filter(
            (pl.col('arm_class')!='FIXED_MANAGEMENT')&(pl.col('state')=='ORDER_CREATED')&
            (pl.col('metric_name')==met)&pl.col('estimate').is_finite()&(pl.col('estimate')!=0))
        pos=d.filter(pl.col('estimate')>0).height
        print(f'   {e[-3:]}/{u[:4]:7s} n={d.height:4d} pos_share={pos/max(d.height,1):6.1%}')

print()
print('=== P7b controls: TIME_DERANGEMENT / MAGNITUDE_MATCH diagnosticity ===')
for e,u in CELLS:
    c=pl.read_parquet(P(e,u,'controls.parquet'))
    for ctl in ['TIME_DERANGEMENT','MAGNITUDE_MATCH']:
        x=c.filter((pl.col('control')==ctl)&pl.col('estimate').is_finite())
        if x.height==0: continue
        res=x.filter((pl.col('ci_low')>0)|(pl.col('ci_high')<0)).height
        print(f'{e[-3:]}/{u[:4]:7s} {ctl:18s} rows={x.height:5d} CIexcl={res:4d} ({res/x.height:5.1%}) med_est={x["estimate"].median():.6g} med_|est|={x["estimate"].abs().median():.6g}')

print()
print('=== P7c TIME_DERANGEMENT vs its paired real estimate (is it permutation-invariant?) ===')
for e,u in CELLS:
    c=pl.read_parquet(P(e,u,'controls.parquet'))
    td=c.filter(pl.col('control')=='TIME_DERANGEMENT').select(['symbol','entry_variant','arm_id','component','estimate']).rename({'estimate':'td'})
    n=pl.read_parquet(P(e,u,'native_parameter_origins.parquet')).filter(pl.col('state')=='ALL').select(['symbol','entry_variant','arm_id','component','estimate']).rename({'estimate':'real'})
    j=td.join(n,on=['symbol','entry_variant','arm_id','component'],how='inner').filter(pl.col('td').is_finite()&pl.col('real').is_finite())
    if j.height==0: print(e,u,'no join'); continue
    ident=j.filter((pl.col('td')-pl.col('real')).abs()<1e-12).height
    close=j.filter((pl.col('td')-pl.col('real')).abs()<1e-9).height
    print(f'{e[-3:]}/{u[:4]:7s} joined={j.height:5d} identical<1e-12={ident} ({ident/j.height:5.1%}) <1e-9={close} ({close/j.height:5.1%}) med|td-real|={(j["td"]-j["real"]).abs().median():.3g}')

print()
print('=== P7d concentration: which symbol carries the interval-excluding native rows (ctrader) ===')
for e in ('SPDR-021','SPDR-022','SPDR-023'):
    n=pl.read_parquet(P(e,'ctrader','native_parameter_origins.parquet')).filter(
        (pl.col('arm_class')!='FIXED_NATIVE')&(pl.col('state')=='ALL')&pl.col('estimate').is_finite())
    res=n.filter((pl.col('ci_low')>0)|(pl.col('ci_high')<0))
    print(f'{e} ctrader resolving={res.height}/{n.height}',
          res.group_by('symbol').agg([pl.len(),(pl.col('estimate')<0).sum().alias('neg')]).sort('symbol').to_dicts())
    # leave-symbol-out pooled mean
    for sym in sorted(set(n['symbol'].to_list())):
        full=n['estimate'].mean(); lo=n.filter(pl.col('symbol')!=sym)['estimate'].mean()
        print(f'    pooled mean all={full:.5f}  without {sym}={lo:.5f}')

print()
print('=== P7e fixed baselines, per symbol/variant (per_stratum FIXED_NATIVE, finite gross) ===')
for e,u in CELLS:
    p=pl.read_parquet(P(e,u,'per_stratum_estimates.parquet')).filter(
        (pl.col('arm_class')=='FIXED_NATIVE')&pl.col('gross_mean_bps').is_finite())
    if p.height==0: print(e,u,'none'); continue
    g=p.group_by('entry_variant').agg([
        pl.col('gross_mean_bps').median().alias('med_gross_bps'),
        pl.col('win_share').median().alias('med_win'),
        pl.col('breakeven_win_share_net').median().alias('med_be'),
        pl.col('win_loss_ratio').median().alias('med_wl'),
        pl.col('exposure_per_origin').median().alias('med_expo'),
        pl.col('trade_count').sum().alias('trades'), pl.len().alias('rows')])
    print(f'--- {e} {u}'); print(g)
