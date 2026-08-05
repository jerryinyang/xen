"""Probe 8 (read-only): absorbing-device degeneracy, apparatus gaps, selection checks."""
import polars as pl
ROOT='python/experiments'
CELLS=[(e,u) for e in ('SPDR-021','SPDR-022','SPDR-023') for u in ('ctrader','crypto')]
def P(e,u,f): return f'{ROOT}/{e}/results/analysis/{u}/{f}'

print('=== P8a absorbing-device degeneracy: reach_rate on TARGET-only arms, stop_rate on STOP-only arms ===')
for dev,met in [('target','reach_rate'),('stop','stop_rate')]:
    for e,u in CELLS:
        d=pl.read_parquet(P(e,u,f'device_{dev}.parquet')).filter(
            (pl.col('metric_name')==met)&(pl.col('state')=='ORDER_CREATED')&
            (pl.col('arm_class').is_in(['MANAGEMENT','MANAGEMENT_COMPONENT_COMBINATION']))&
            pl.col('estimate').is_finite())
        z=d.filter(pl.col('estimate').abs()<1e-15).height
        print(f'{dev}/{met:11s} {e[-3:]}/{u[:4]:7s} rows={d.height:4d} exact_zero_delta={z:4d} ({z/max(d.height,1):6.1%})  med_observed={d["observed"].median()} med_comp={d["comparator_observed"].median()}')
    print()

print('=== P8b apparatus: column population ===')
for e,u in CELLS:
    s=pl.read_parquet(P(e,u,'selection_checks.parquet'))
    n=s.height
    psr=s['payoff_scale_ratio'].is_finite().sum() if 'payoff_scale_ratio' in s.columns else -1
    print(f'{e[-3:]}/{u[:4]:7s} selection_checks rows={n:4d} payoff_scale_ratio finite={psr}  sign_share_diff finite={s["sign_share_difference"].is_finite().sum()}  excl_gap finite={s["excluded_mean_median_gap"].is_finite().sum()}')
print()
for e,u in CELLS:
    h=pl.read_parquet(P(e,u,'device_hold.parquet'))
    he=h.filter(pl.col('metric_name')=='holding_efficiency')
    ob=h.filter(pl.col('metric_name')=='outcome_by_time_bps')
    print(f'{e[-3:]}/{u[:4]:7s} holding_efficiency rows={he.height:4d} finite_est={he["estimate"].is_finite().sum():4d} vs outcome_by_time rows={ob.height:4d} finite={ob["estimate"].is_finite().sum():4d}')
print()
print('=== P8c spread cost columns in per_stratum ===')
for e,u in CELLS:
    p=pl.read_parquet(P(e,u,'per_stratum_estimates.parquet'))
    print(f'{e[-3:]}/{u[:4]:7s} spread_cost_status uniq={set(p["spread_cost_status"].to_list())} spread_rt_bps uniq={set(p["spread_rt_bps"].to_list())} cost_scope uniq={set(p["cost_scope"].to_list())} partial_cost_mean_bps finite={p["partial_cost_mean_bps"].is_finite().sum()}/{p.height} med={p.filter(pl.col("partial_cost_mean_bps").is_finite())["partial_cost_mean_bps"].median()}')
