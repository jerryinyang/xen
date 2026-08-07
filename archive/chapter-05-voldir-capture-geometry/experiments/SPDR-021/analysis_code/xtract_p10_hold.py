"""Probe 10 (read-only): realised hold-duration distribution on SPDR-021, for a non-arbitrary cap."""
import polars as pl
ROOT='python/experiments'
def P(e,u,f): return f'{ROOT}/{e}/results/analysis/{u}/{f}'
for u in ('ctrader','crypto'):
    t=pl.read_parquet(P('SPDR-021',u,'native_parameter_shared_trades.parquet')).filter(
        pl.col('_entry_ns').is_not_null()&pl.col('_exit_ns').is_not_null())
    t=t.with_columns(((pl.col('_exit_ns')-pl.col('_entry_ns'))/60e9).alias('hold_min'))
    t=t.filter(pl.col('hold_min')>=0)
    # dedupe to unique positions so arms don't multi-count the same trade
    d=t.unique(subset=['symbol','position_id'])
    print(f'=== 021/{u}: unique positions={d.height}')
    q=[0.5,0.75,0.9,0.95,0.99]
    print('   hold minutes  ', {f'p{int(x*100)}': round(d["hold_min"].quantile(x),1) for x in q},
          ' mean', round(d['hold_min'].mean(),1), ' max', round(d['hold_min'].max(),1))
    print('   hold H1 bars  ', {f'p{int(x*100)}': round(d["hold_min"].quantile(x)/60,2) for x in q})
    print('   hold H4 bars  ', {f'p{int(x*100)}': round(d["hold_min"].quantile(x)/240,2) for x in q})
    print('   exit_reason mix', d.group_by('exit_reason').agg(pl.len()).sort('len',descending=True).to_dicts()[:6])
    # what share would a cap at N H1 bars bind?
    for cap in (2,4,8,12,24,48):
        print(f'      cap {cap:3d} H1 bars ({cap*60:5d} min): binds {(d["hold_min"]>cap*60).mean():6.2%} of positions')
