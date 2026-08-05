"""Probe 6 (read-only): FREE device metrics split by setting; and fixed baselines."""
import polars as pl
ROOT='python/experiments'
CELLS=[(e,u) for e in ('SPDR-021','SPDR-022','SPDR-023') for u in ('ctrader','crypto')]
def P(e,u,f): return f'{ROOT}/{e}/results/analysis/{u}/{f}'
TARGETS=[('size','drawdown_bps'),('size','concentration'),('hold','outcome_by_time_bps'),
         ('stop','loss_severity_bps'),('trail','favourable_excursion_captured')]
for dev,met in TARGETS:
    print(f'##### {dev}/{met} — split by setting')
    print(f'{"cell":13s} {"setting":40s} {"n":>4s} {"res":>4s} {"pos":>4s} {"neg":>4s} {"medEst":>11s} {"medMDE":>10s} {"e/MDE":>6s} {"blks":>5s}')
    for e,u in CELLS:
        d=pl.read_parquet(P(e,u,f'device_{dev}.parquet')).filter(
            (pl.col('arm_class')!='FIXED_MANAGEMENT')&(pl.col('state')=='ORDER_CREATED')&
            (pl.col('metric_name')==met)&pl.col('estimate').is_finite()&pl.col('ci_low').is_finite())
        for st in sorted(set(d['setting'].to_list())):
            x=d.filter(pl.col('setting')==st)
            res=x.filter((pl.col('ci_low')>0)|(pl.col('ci_high')<0))
            pos=res.filter(pl.col('ci_low')>0).height; neg=res.filter(pl.col('ci_high')<0).height
            me=x['estimate'].median(); mm=x['mde'].median()
            print(f'{e[-3:]+"/"+u[:4]:13s} {st:40s} {x.height:4d} {res.height:4d} {pos:4d} {neg:4d} {me:11.3f} {mm if mm is not None else float("nan"):10.3f} {abs(me)/mm if mm else float("nan"):6.2f} {x["effective_trade_blocks"].median():5.0f}')
    print()
