import numpy as np, pandas as pd
pd.set_option('display.width',260); pd.set_option('display.max_columns',60)
R="python/experiments/SPDR-018B/results/"
p=pd.read_parquet(R+"panel_C.parquet")
print("panel rows",len(p))
print(p[['symbol','clock','band','source','z','H','h','policy','event_type','shock_flag','mag_high','vol_tercile','slow_regime']].nunique().to_string())
print("\nshock_flag counts:"); print(p.shock_flag.value_counts(dropna=False))

print("\n=== RAW SPLIT: gross_bps by shock_flag (rows) ===")
g=p.groupby('shock_flag').gross_bps.agg(['size','mean','median','std'])
print(g.to_string())
print("\n=== per symbol x shock ===")
print(p.groupby(['symbol','shock_flag']).gross_bps.agg(['size','mean','median','std']).to_string())
print("\n=== per band x shock ===")
print(p.groupby(['band','shock_flag']).gross_bps.agg(['size','mean','median']).to_string())
print("\n=== per policy x shock ===")
print(p.groupby(['policy','shock_flag']).gross_bps.agg(['size','mean','median']).to_string())
print("\n=== per event_type x shock ===")
print(p.groupby(['event_type','shock_flag']).gross_bps.agg(['size','mean','median']).to_string())
print("\n=== per H x shock (mean gross) ===")
print(p.pivot_table(index='H',columns='shock_flag',values='gross_bps',aggfunc=['size','mean']).to_string())

# what does shock select on?  compare |r| and vol tercile composition
p['abs_r']=p.gross_bps.abs()
print("\n=== what shock selects: |gross| and composition ===")
print(p.groupby('shock_flag').agg(abs_r=('abs_r','median'),abs_r_mean=('abs_r','mean'),
  side_long=('side',lambda s:(s>0).mean()),tercile=('vol_tercile','mean'),
  maghigh=('mag_high','mean'),slow=('slow_regime','mean')).to_string())
print("\n=== day-of-week / hour composition (24/5 question) ===")
p['dt']=pd.to_datetime(p.event_ts,utc=True)
p['dow']=p.dt.dt.dayofweek; p['hr']=p.dt.dt.hour
print(pd.crosstab(p.dow,p.shock_flag,normalize='columns').to_string())
print(pd.crosstab(p.hr,p.shock_flag,normalize='columns').round(4).to_string())
