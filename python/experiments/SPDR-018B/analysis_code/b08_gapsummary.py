import numpy as np, pandas as pd
R="python/experiments/SPDR-018B/results/"
c=pd.read_parquet(R+"coverage_gap_C7_C8.parquet")
c7=c[c.residue_item=="C7"]; c8=c[c.residue_item=="C8"]
print("C7 pairs:",len(c7))
print(" sign_flipped share: %.4f"%c7.sign_flipped.mean())
print(" of flipped, band CIs overlap: %.4f"%c7.loc[c7.sign_flipped,"band_cis_overlap"].mean())
mde=(c7.design_block_mde_bps.abs()+c7.confirm_block_mde_bps.abs())
print(" |delta| > pooled two-band MDE: all pairs %.4f ; flipped only %.4f"%((c7.delta_bps.abs()>mde).mean(),(c7.loc[c7.sign_flipped,"delta_bps"].abs()>mde[c7.sign_flipped]).mean()))
print(" equal-weight DESIGN %.3f CONFIRM %.3f"%(c7.design_mean_bps.mean(),c7.confirm_mean_bps.mean()))
wd=np.average(c7.design_mean_bps,weights=c7.design_n); wc=np.average(c7.confirm_mean_bps,weights=c7.confirm_n)
print(" n-weighted DESIGN %.3f CONFIRM %.3f diff %.3f"%(wd,wc,wc-wd))
print(" median design_n %.0f confirm_n %.0f"%(c7.design_n.median(),c7.confirm_n.median()))
print("\nC8 cells:",len(c8))
print(" p_momo row-weighted median %.4f ; per-symbol-mean median %.4f ; median |diff| %.4f"%(
 c8.p_momo_pooled_row_weighted.median(),c8.p_momo_mean_of_per_symbol.median(),
 (c8.p_momo_pooled_row_weighted-c8.p_momo_mean_of_per_symbol).abs().median()))
print(" n_symbols momo-leaning median %.1f vs mr-leaning %.1f (of %.1f)"%(
 c8.n_symbols_momo_leaning.median(),c8.n_symbols_mr_leaning.median(),c8.n_symbols.median()))
b3=pd.read_parquet(R+"coverage_gap_B3.parquet")
print("\nB3 native cells:",len(b3))
print(" all gross_mean>0? ",(b3.gross_mean>0).mean()," all net_mean>0? ",(b3.net_mean>0).mean())
print(" at_parent_target_precision:",int(b3.at_parent_target_precision.fillna(False).sum()),"of",len(b3))
print(" median n %.0f, median n_dates %.0f, median block MDE %.2f"%(b3.gross_n.median(),b3.gross_n_dates.median(),b3.gross_block_mde_mean_bps.median()))
print(" median p %.4f W %.2f L %.2f W/L %.3f gross %.3f net %.3f"%(b3.gross_p.median(),b3.gross_W.median(),b3.gross_L.median(),b3.gross_W_L.median(),b3.gross_mean.median(),b3.net_mean.median()))
print(" breakdown band x clock:"); print(pd.crosstab(b3.band,b3.clock).to_string())
print(" symbols:",b3.symbol.value_counts().to_dict())
print(" exit_mode:",b3.exit_mode.value_counts().to_dict())
