"""Probe 3 (read-only): SPDR-022 vs SPDR-023 mirror test on the shared native origin/trade lens."""
import polars as pl
ROOT='python/experiments'
def P(e,u,f): return f'{ROOT}/{e}/results/analysis/{u}/{f}'
KEY=['symbol','entry_variant','arm_id','component','parameter','orientation','state']

for u in ('ctrader','crypto'):
    a=pl.read_parquet(P('SPDR-022',u,'native_parameter_origins.parquet')).filter(
        (pl.col('state')=='ALL')&(pl.col('arm_class')!='FIXED_NATIVE')).select(KEY+['estimate','mde','ci_low','ci_high'])
    b=pl.read_parquet(P('SPDR-023',u,'native_parameter_origins.parquet')).filter(
        (pl.col('state')=='ALL')&(pl.col('arm_class')!='FIXED_NATIVE')).select(KEY+['estimate','mde','ci_low','ci_high'])
    j=a.join(b,on=KEY,how='inner',suffix='_23').filter(pl.col('estimate').is_finite()&pl.col('estimate_23').is_finite())
    r=j.select(pl.corr('estimate','estimate_23')).item()
    opp=j.filter(pl.col('estimate')*pl.col('estimate_23')<0).height
    print(f'ORIGIN LENS {u}: joined={j.height} pearson_r={r:.4f} opposite_sign={opp}/{j.height} ({opp/j.height:.1%})')
    # sum test: 022 + 023 ~ 0 ?
    s=j.select([(pl.col('estimate')+pl.col('estimate_23')).abs().median().alias('med_abs_sum'),
                pl.col('estimate').abs().median().alias('med_abs_022'),
                pl.col('estimate_23').abs().median().alias('med_abs_023')])
    print('   ',s.to_dicts()[0])

print()
print('=== trade lens: per (symbol,arm_id,component,parameter,entry_variant) mean paired delta, 022 vs 023 ===')
for u in ('ctrader','crypto'):
    K=['symbol','entry_variant','arm_id','component','parameter']
    def agg(e):
        t=pl.read_parquet(P(e,u,'native_parameter_shared_trades.parquet')).filter(
            pl.col('paired_outcome_delta_bps').is_not_null())
        return t.group_by(K).agg([pl.col('paired_outcome_delta_bps').mean().alias('m'),pl.len().alias('n')])
    j=agg('SPDR-022').join(agg('SPDR-023'),on=K,how='inner',suffix='_23')
    j=j.filter((pl.col('m')!=0)|(pl.col('m_23')!=0))
    r=j.select(pl.corr('m','m_23')).item()
    opp=j.filter(pl.col('m')*pl.col('m_23')<0).height
    print(f'TRADE LENS {u}: groups={j.height} pearson_r={r:.4f} opposite_sign={opp}/{j.height} ({opp/j.height:.1%})')
