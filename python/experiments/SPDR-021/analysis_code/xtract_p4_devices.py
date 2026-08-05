"""Probe 4 (read-only): Pre-test G forced/free paired contrasts on identical device rows."""
import polars as pl
ROOT='python/experiments'
CELLS=[(e,u) for e in ('SPDR-021','SPDR-022','SPDR-023') for u in ('ctrader','crypto')]
def P(e,u,f): return f'{ROOT}/{e}/results/analysis/{u}/{f}'
ROW=['symbol','entry_variant','arm_id','arm_class','component','setting','comparator_id','state']

PAIRS={ # device : (FORCED, FREE)
 'hold' :('decay_bps','outcome_by_time_bps'),
 'size' :('risk_dispersion','drawdown_bps'),
 'trail':('peak_giveback_bps','favourable_excursion_captured'),
 'stop' :('adverse_excursion_bps','recovery_after_stop_bps'),
 'target':('time_to_target','realised_capture_bps'),
}

def stats(df):
    f=df.filter(pl.col('estimate').is_finite()&pl.col('ci_low').is_finite()&pl.col('mde').is_finite())
    n=f.height
    if n==0: return None
    hit=f.filter((pl.col('ci_low')>0)|(pl.col('ci_high')<0)).height
    return dict(n=n,hit=hit,rate=hit/n,med_est=f['estimate'].median(),med_mde=f['mde'].median(),
                ratio=abs(f['estimate'].median())/f['mde'].median() if f['mde'].median() else float('nan'),
                med_blocks=f['effective_trade_blocks'].median())

print('=== Pre-test G: FORCED vs FREE on IDENTICAL rows (state=ORDER_CREATED, non-fixed arms) ===')
print(f'{"cell":18s} {"device":7s} {"metric":32s} {"hit/n":>10s} {"rate":>7s} {"medEst":>10s} {"medMDE":>9s} {"e/MDE":>7s} {"blocks":>7s}')
for e,u in CELLS:
    for dev,(F,R) in PAIRS.items():
        d=pl.read_parquet(P(e,u,f'device_{dev}.parquet')).filter(
            (pl.col('arm_class')!='FIXED_MANAGEMENT')&(pl.col('state')=='ORDER_CREATED'))
        # restrict to rows where BOTH metrics finite (identical population)
        keys_f=d.filter((pl.col('metric_name')==F)&pl.col('estimate').is_finite()).select(ROW)
        keys_r=d.filter((pl.col('metric_name')==R)&pl.col('estimate').is_finite()).select(ROW)
        keys=keys_f.join(keys_r,on=ROW,how='inner')
        dd=d.join(keys,on=ROW,how='inner')
        for lab,met in (('FORCED',F),('FREE  ',R)):
            s=stats(dd.filter(pl.col('metric_name')==met))
            if s: print(f'{e[-3:]+"/"+u:18s} {dev:7s} {lab+" "+met:32s} {str(s["hit"])+"/"+str(s["n"]):>10s} {s["rate"]:7.1%} {s["med_est"]:10.3f} {s["med_mde"]:9.3f} {s["ratio"]:7.2f} {s["med_blocks"]:7.0f}')
    print()
