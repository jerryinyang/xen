"""Probe 5 (read-only): sign split of CI-excluding rows for FREE device metrics; baselines."""
import polars as pl
ROOT='python/experiments'
CELLS=[(e,u) for e in ('SPDR-021','SPDR-022','SPDR-023') for u in ('ctrader','crypto')]
def P(e,u,f): return f'{ROOT}/{e}/results/analysis/{u}/{f}'
FREE={'hold':'outcome_by_time_bps','size':'drawdown_bps','trail':'favourable_excursion_captured',
      'stop':'recovery_after_stop_bps','target':'realised_capture_bps','trail2':'loss_tail_bps',
      'size2':'concentration','stop2':'loss_severity_bps','target2':'missed_excess_bps'}
DEVF={'hold':'hold','size':'size','trail':'trail','stop':'stop','target':'target',
      'trail2':'trail','size2':'size','stop2':'stop','target2':'target'}
print(f'{"cell":14s} {"metric":32s} {"n":>5s} {"res":>5s} {"res%":>6s} {"pos":>5s} {"neg":>5s} {"posShareOfRes":>13s}')
for e,u in CELLS:
    for k,met in FREE.items():
        d=pl.read_parquet(P(e,u,f'device_{DEVF[k]}.parquet')).filter(
            (pl.col('arm_class')!='FIXED_MANAGEMENT')&(pl.col('state')=='ORDER_CREATED')&
            (pl.col('metric_name')==met)&pl.col('estimate').is_finite()&pl.col('ci_low').is_finite())
        n=d.height
        if n==0: continue
        res=d.filter((pl.col('ci_low')>0)|(pl.col('ci_high')<0))
        pos=res.filter(pl.col('ci_low')>0).height; neg=res.filter(pl.col('ci_high')<0).height
        print(f'{e[-3:]+"/"+u[:4]:14s} {met:32s} {n:5d} {res.height:5d} {res.height/n:6.1%} {pos:5d} {neg:5d} {pos/max(res.height,1):13.1%}')
    print()
print('=== baselines: FIXED_MANAGEMENT device rows -> comparator_observed; and FIXED native per_stratum ===')
for e,u in CELLS:
    p=pl.read_parquet(P(e,u,'per_stratum_estimates.parquet')).filter(pl.col('arm_class')=='FIXED_NATIVE')
    print(f'--- {e} {u} FIXED_NATIVE rows={p.height}')
    print(p.select(['symbol','entry_variant','arm_id','exposure_per_origin','fill_rate','gross_mean_bps','win_share','breakeven_win_share_net','win_loss_ratio','trade_count','estimate','ci_low','ci_high']).head(8))
