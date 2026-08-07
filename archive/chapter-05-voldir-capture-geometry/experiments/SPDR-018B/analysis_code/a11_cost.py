import numpy as np, pandas as pd
pd.set_option('display.width',260)
R="python/experiments/SPDR-018B/results/"
m=pd.read_parquet(R+"metrics_by_cell.parquet")
sg=m[m.gross_p.notna()].copy(); pw=sg[sg.at_parent_target_precision==True].copy()
print("=== Q5: does the 12.9%-clear-net survive the UNSCALED cost floor? ===")
ratio=0.17854966
pw['cost_unscaled']=pw.gross_cost_bps/ratio
pw['p_be_net_unscaled']=(pw.gross_L+pw.cost_unscaled)/(pw.gross_W+pw.gross_L)
print("  vol-scaled cost: median %.3f min %.3f  |  unscaled: median %.3f min %.3f"%(
  pw.gross_cost_bps.median(),pw.gross_cost_bps.min(),pw.cost_unscaled.median(),pw.cost_unscaled.min()))
print("  clears net (VOL-SCALED)  : %d/%d = %.4f  [screen: 0.129]"%((pw.gross_p>pw.gross_p_be_net).sum(),len(pw),(pw.gross_p>pw.gross_p_be_net).mean()))
print("  clears net (UNSCALED)    : %d/%d = %.4f"%((pw.gross_p>pw.p_be_net_unscaled).sum(),len(pw),(pw.gross_p>pw.p_be_net_unscaled).mean()))
print("  clears gross             : %d/%d = %.4f"%((pw.gross_p>pw.gross_p_be).sum(),len(pw),(pw.gross_p>pw.gross_p_be).mean()))
print("  net mean UNSCALED median : %.3f bps  (vol-scaled %.3f)"%((pw.gross_mean-pw.cost_unscaled).median(),pw.net_mean.median()))
print("\n  per stratum:")
for c in ['symbol','arm','exit_mode']:
    for v,d in pw.groupby(c,dropna=False):
        cu=d.gross_cost_bps/ratio; pbn=(d.gross_L+cu)/(d.gross_W+d.gross_L)
        print(f"   {c}={str(v):22s} n={len(d):5d} gross {float((d.gross_p>d.gross_p_be).mean()):.4f}  net_scaled {float((d.gross_p>d.gross_p_be_net).mean()):.4f}  net_UNSCALED {float((d.gross_p>pbn).mean()):.4f}")

print("\n=== crypto comparison in SIGMA units ===")
sc,sy=13.034237315995593,73.0006
print("  cTrader: gross mean %.4f bps = %.5f sigma ; cost %.3f bps = %.4f sigma"%(
  pw.gross_mean.median(),pw.gross_mean.median()/sc,pw.gross_cost_bps.median(),pw.gross_cost_bps.median()/sc))
print("  crypto : gross mean -1.178 bps = %.5f sigma ; cost 13.540 bps = %.4f sigma"%(-1.178/sy,13.54/sy))
print("  cTrader W %.2f bps = %.3f sigma ; L %.2f = %.3f sigma"%(pw.gross_W.median(),pw.gross_W.median()/sc,pw.gross_L.median(),pw.gross_L.median()/sc))
print("  crypto  W 128.65 bps = %.3f sigma ; L 75.55 = %.3f sigma"%(128.65/sy,75.55/sy))

print("\n=== residue items present in the emission ===")
allit=set()
for v in m.residue_item.dropna().unique(): allit.update(v.split(','))
print("  present:",sorted(allit))
for it in ['A1','A2','A3','A4','A5','B1','B2','B3','B4','B5','C1','C2','C3','C4','C5','C6','C7','C8','C9','D1','D2','D3','D4','D5','D6','D7','D8']:
    n=m.residue_item.fillna('').str.split(',').apply(lambda L: it in L).sum()
    print(f"   {it}: {n}")
