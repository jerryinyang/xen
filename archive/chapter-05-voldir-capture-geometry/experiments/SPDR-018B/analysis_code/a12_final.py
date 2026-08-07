import numpy as np, pandas as pd, json
pd.set_option('display.width',260)
R="python/experiments/SPDR-018B/results/"
m=pd.read_parquet(R+"metrics_by_cell.parquet")
sg=m[m.gross_p.notna()].copy(); pw=sg[sg.at_parent_target_precision==True].copy()

print("=== A. trade-scale vs bar-scale: is the 0.17855 cost ratio right? ===")
print("  W ratio cT/crypto = %.4f ; L ratio = %.4f ; (W+L) ratio = %.4f ; bar-sigma ratio = 0.17855"%(
 41.334/128.65,36.111/75.55,(41.334+36.111)/(128.65+75.55)))
for r in [0.17855,0.30,0.379,0.478]:
    cu=pw.gross_cost_bps/0.17854966*r; pbn=(pw.gross_L+cu)/(pw.gross_W+pw.gross_L)
    print(f"   ratio {r:.5f} -> floor {13.5*r:6.2f} bps, clears net {float((pw.gross_p>pbn).mean()):.4f}, net mean median {(pw.gross_mean-cu).median():7.3f}")

print("\n=== B. cross-symbol homogeneity on POWERED PER-SYMBOL cells only (no pooled) ===")
ps=pw[pw.symbol.isin(['EURUSD','XAUUSD','USTEC'])]
print(ps.groupby('symbol').agg(n=('gross_p','size'),p=('gross_p','median'),p_be=('gross_p_be','median'),
  d=('gross_p','median'),WL=('gross_W_L','median'),gross=('gross_mean','median'),
  lo=('gross_mean_ci_low','median'),hi=('gross_mean_ci_high','median'),
  logR=('gross_p',lambda s:np.nan)).to_string(float_format=lambda x:f"{x:.4f}"))
ps=ps.copy(); ps['dist']=ps.gross_p-ps.gross_p_be
ps['logR']=np.log(ps.gross_p*ps.gross_W/((1-ps.gross_p)*ps.gross_L))
print(ps.groupby('symbol')[['dist','logR','gross_mean']].describe().T.to_string(float_format=lambda x:f"{x:.4f}"))
print("\n  sign of median gross mean per symbol:",{s:float(d.gross_mean.median()) for s,d in ps.groupby('symbol')})
print("  share of per-symbol powered cells clearing gross be:",{s:float((d.gross_p>d.gross_p_be).mean()) for s,d in ps.groupby('symbol')})

print("\n=== C. controls: plant curves in full ===")
c=json.load(open(R+"controls.json"))
for k in ['arm_B_side_derangement','arm_C_side_derangement']:
    v=c[k]; print(f"\n {k}: live {v['live_effect_bps']:.4f} nullmean {v['null_mean']:.4f} sd {v['null_sd']:.4f} pct {v['percentile']} n {v['n']}")
    print("   plant curve:",[(round(pc['live_effect']-v['live_effect_bps']),pc['percentile']) for pc in v['plant_curve']])
for k in ['shock_flag','mag_high']:
    v=c['magnitude_matched'][k]; print(f"\n M-3 {k}: live {v['live_effect_bps']:.4f} nullmean {v['null_mean']:.4f} sd {v['null_sd']:.4f} pct {v['percentile']} n_live {v['n_live']}")
    print("   plant curve:",[(round(pc['live_effect']-v['live_effect_bps']),pc['percentile']) for pc in v['plant_curve']])
v=c['magnitude_matched_full_panel_shock_flag']
print(f"\n M-3 FULL PANEL: live {v['live_effect_bps']:.4f} nullmean {v['null_mean']:.4f} sd {v['null_sd']:.4f} pct {v['percentile']} n_live {v['n_live']}")
print("   plant curve:",[(round(pc['live_effect']-v['live_effect_bps']),pc['percentile']) for pc in v['plant_curve']])
print("\n controls present:",[k for k in c if not k.startswith(('cost','spread','universe','seeds','controls'))])

print("\n=== D. CI hygiene: seed-range columns present? ===")
print("  cols with 'seed' or 'sweep':",[x for x in m.columns if 'seed' in x.lower() or 'sweep' in x.lower()])
print("  median/trimmed CI columns present:",[x for x in m.columns if 'median_ci' in x or 'trimmed' in x])

print("\n=== E. mean vs median vs trimmed disagreement (powered) ===")
print("  gross mean med %.3f | gross median med %.3f | trimmed med %.3f"%(
  pw.gross_mean.median(),pw.gross_median.median(),pw.gross_trimmed_mean_10.median()))
print("  sign agreement mean-vs-median %.3f ; mean-vs-trimmed %.3f"%(
  (np.sign(pw.gross_mean)==np.sign(pw.gross_median)).mean(),
  (np.sign(pw.gross_mean)==np.sign(pw.gross_trimmed_mean_10)).mean()))
print("  net: mean %.3f median %.3f trimmed %.3f"%(pw.net_mean.median(),pw.net_median.median(),pw.net_trimmed_mean_10.median()))

print("\n=== F. arm A / arm D — what did they produce (unsigned)? ===")
a=m[m.arm=='A']; d=m[m.arm=='D']
print(" arm A:",len(a),"cells, powered",int(a.at_parent_target_precision.sum()),"labels:",a.band_label_ic.value_counts(dropna=False).to_dict() if 'band_label_ic' in a else None)
print("   band_label_gap:",a.band_label_gap.value_counts(dropna=False).to_dict())
print("   band_label_r2:",a.band_label_r2.value_counts(dropna=False).to_dict())
print(" arm D:",len(d),"cells, powered",int(d.at_parent_target_precision.sum()))
print("   band_label:",d.band_label.value_counts(dropna=False).to_dict())
print("   by residue item:"); print(d.groupby('residue_item').agg(n=('n','size'),pw=('at_parent_target_precision','sum'),val=('value','median')).to_string())
print("\n arm A by residue item:"); print(a.groupby('residue_item').agg(n=('n','size'),pw=('at_parent_target_precision','sum')).to_string())
