"""Probe 2 (read-only): native trade lens — structural degeneracy + concentration; origin lens by parameter."""
import polars as pl
ROOT='python/experiments'
CELLS=[(e,u) for e in ('SPDR-021','SPDR-022','SPDR-023') for u in ('ctrader','crypto')]
def P(e,u,f): return f'{ROOT}/{e}/results/analysis/{u}/{f}'

print('=== P2a native shared-trade paired delta: share exactly zero, by parameter ===')
for e,u in CELLS:
    t=pl.read_parquet(P(e,u,'native_parameter_shared_trades.parquet'))
    t=t.filter(pl.col('paired_outcome_delta_bps').is_not_null())
    g=t.group_by('parameter').agg([
        pl.len().alias('rows'),
        (pl.col('paired_outcome_delta_bps').abs()<1e-12).sum().alias('exact_zero'),
        pl.col('paired_outcome_delta_bps').mean().alias('mean_delta'),
        pl.col('paired_outcome_delta_bps').median().alias('med_delta'),
    ]).with_columns((pl.col('exact_zero')/pl.col('rows')).alias('zero_share')).sort('parameter')
    print(f'--- {e} {u} (total rows={t.height})'); print(g)

print()
print('=== P2b concentration: top-1% |delta| share of summed delta, and its sign ===')
for e,u in CELLS:
    t=pl.read_parquet(P(e,u,'native_parameter_shared_trades.parquet')).filter(
        pl.col('paired_outcome_delta_bps').is_not_null() & (pl.col('paired_outcome_delta_bps').abs()>1e-12))
    if t.height==0: print(e,u,'no non-zero pairs'); continue
    s=t['paired_outcome_delta_bps']
    thr=s.abs().quantile(0.99)
    top=t.filter(pl.col('paired_outcome_delta_bps').abs()>=thr)
    tot=s.sum()
    print(f'{e} {u}: nonzero_pairs={t.height} sum={tot:.1f} top1%_n={top.height} top1%_sum={top["paired_outcome_delta_bps"].sum():.1f} share={top["paired_outcome_delta_bps"].sum()/tot if tot else float("nan"):.3f}')

print()
print('=== P2c origin lens: CI-excl hit rate by parameter x component (state=ALL) ===')
for e,u in CELLS:
    n=pl.read_parquet(P(e,u,'native_parameter_origins.parquet')).filter(
        (pl.col('arm_class')!='FIXED_NATIVE')&(pl.col('state')=='ALL')&pl.col('estimate').is_finite())
    g=n.group_by('parameter').agg([
        pl.len().alias('rows'),
        (((pl.col('ci_low')>0)|(pl.col('ci_high')<0))).sum().alias('ci_excl'),
        (pl.col('estimate').abs()>pl.col('mde')).sum().alias('mde_hit'),
        pl.col('estimate').median().alias('med_est'),
        pl.col('mde').median().alias('med_mde'),
    ]).sort('parameter')
    print(f'--- {e} {u}'); print(g)
