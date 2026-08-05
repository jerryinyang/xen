"""Probe 9 (read-only): does any vol component change SELECTION quality on the origin lens?
Selection metrics: event_rate, fill_rate, exposure_per_origin. Plus selected-vs-excluded outcome gap."""
import polars as pl
ROOT='python/experiments'
CELLS=[(e,u) for e in ('SPDR-021','SPDR-022','SPDR-023') for u in ('ctrader','crypto')]
def P(e,u,f): return f'{ROOT}/{e}/results/analysis/{u}/{f}'

print('=== P9a origin-lens estimate by COMPONENT (state=ALL, non-fixed) — hit rate + est/MDE ===')
for e,u in CELLS:
    n=pl.read_parquet(P(e,u,'native_parameter_origins.parquet')).filter(
        (pl.col('arm_class')!='FIXED_NATIVE')&(pl.col('state')=='ALL')&pl.col('estimate').is_finite())
    g=n.group_by('component').agg([
        pl.len().alias('rows'),
        (((pl.col('ci_low')>0)|(pl.col('ci_high')<0))).sum().alias('res'),
        ((pl.col('ci_low')>0)).sum().alias('pos'),
        ((pl.col('ci_high')<0)).sum().alias('neg'),
        pl.col('estimate').median().alias('med_est'),
        pl.col('mde').median().alias('med_mde')]).with_columns(
        (pl.col('med_est').abs()/pl.col('med_mde')).alias('e_mde')).sort('component')
    print(f'--- {e[-3:]}/{u}')
    for r in g.iter_rows(named=True):
        print(f"    {str(r['component']):22s} rows={r['rows']:5d} res={r['res']:4d} ({r['res']/r['rows']:5.1%}) pos={r['pos']:4d} neg={r['neg']:4d} e/MDE={r['e_mde']:.2f}")

print()
print('=== P9b selected vs excluded origins: is the SELECTED set actually better? (SPDR-021) ===')
for u in ('ctrader','crypto'):
    s=pl.read_parquet(P('SPDR-021',u,'native_parameter_selected_excluded.parquet'))
    print(f'--- 021/{u} rows={s.height}, selection values={sorted(set(s["selection"].to_list()))}')
    g=s.filter(pl.col('outcome_bps').is_not_null()).group_by(['component','selection']).agg([
        pl.len().alias('n'), pl.col('outcome_bps').mean().alias('mean_bps'),
        pl.col('outcome_bps').median().alias('med_bps'),
        (pl.col('outcome_bps')>0).mean().alias('win_share')])
    piv=g.pivot(values=['n','mean_bps','win_share'],index='component',on='selection')
    print(piv)

print()
print('=== P9c selection_checks: sign_share_difference and excluded_mean_median_gap ===')
for e,u in CELLS:
    s=pl.read_parquet(P(e,u,'selection_checks.parquet')).filter(pl.col('sign_share_difference').is_finite())
    if s.height==0: continue
    print(f"{e[-3:]}/{u[:4]:7s} n={s.height:5d} med_sign_share_diff={s['sign_share_difference'].median():+.5f} "
          f"p10={s['sign_share_difference'].quantile(.1):+.4f} p90={s['sign_share_difference'].quantile(.9):+.4f} "
          f"share_|diff|>0.05={(s['sign_share_difference'].abs()>0.05).mean():.1%}")
