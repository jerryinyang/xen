"""SPDR-001 analysis figures (neutral quantification)."""
import polars as pl, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
R = Path("experiments/SPDR-001/results"); P = Path("experiments/SPDR-001/plots"); P.mkdir(exist_ok=True)
edge = pl.read_parquet(R/"rich_edge.parquet"); dist = pl.read_parquet(R/"rich_dist.parquet")
dose = pl.read_parquet(R/"rich_dose.parquet")
INST = ["EURUSD","XAUUSD","BTCUSD","USTEC"]; C = dict(zip(INST,["#4C78A8","#F58518","#54A24B","#E45756"]))

# 1. Dispersion dose-response: ATR-pct decile -> forward-move std, per instrument (1h/5min H24)
fig,ax=plt.subplots(figsize=(7,4.5))
for ins in INST:
    d=dose.filter((pl.col('conditioner')=='atrpct')&(pl.col('domain')=='1h/5min')&(pl.col('hold_bars')==24)&(pl.col('instrument')==ins)).sort('decile')
    ax.plot(d['decile'],d['move_std'],'-o',color=C[ins],label=ins)
ax.set_xlabel('HTF ATR trailing-percentile decile (0=low vol regime, 9=high)')
ax.set_ylabel('LTF forward-move std (ATR units)')
ax.set_title('Dispersion dose-response: HTF vol regime shapes LTF outcome spread\n(1h/5min, H=24) — monotone, mean stays ~0')
ax.legend(); ax.grid(alpha=.3); fig.tight_layout(); fig.savefig(P/"dispersion_dose_atrpct.png",dpi=110); plt.close(fig)

# 2. Horizon scaling of the DI edge (BTCUSD & USTEC 1h/5min di + strongest cells)
fig,ax=plt.subplots(figsize=(7,4.5))
for ins in ["BTCUSD","USTEC"]:
    for var,ls in [("di","-"),("atrH_adxHi_di",":"),("atrM_adxHi_di","--")]:
        d=edge.filter((pl.col('domain')=='1h/5min')&(pl.col('instrument')==ins)&(pl.col('variant')==var)).sort('hold_bars')
        if d.height:
            ax.plot(d['hold_bars'],d['edge'],ls,color=C[ins],marker='o',
                    label=f"{ins} {var}",alpha=.85)
ax.axhline(0,color='k',lw=.7); ax.set_xlabel('hold (LTF bars)'); ax.set_ylabel('DI signed edge (ATR units)')
ax.set_title('Horizon: DI edge accumulates ~linearly with hold (per-bar ~const)')
ax.legend(fontsize=7); ax.grid(alpha=.3); fig.tight_layout(); fig.savefig(P/"horizon_edge.png",dpi=110); plt.close(fig)

# 3. Instrument x domain heterogeneity: mean DI edge (sign flips by instrument)
fig,ax=plt.subplots(figsize=(7,4.5))
doms=["1d/1h","4h/1h","1h/5min"]; x=np.arange(len(doms)); w=.2
for i,ins in enumerate(INST):
    vals=[edge.filter((pl.col('instrument')==ins)&(pl.col('domain')==dm))['edge'].mean() for dm in doms]
    ax.bar(x+i*w,vals,w,color=C[ins],label=ins)
ax.axhline(0,color='k',lw=.7); ax.set_xticks(x+1.5*w); ax.set_xticklabels(doms)
ax.set_ylabel('mean DI edge (ATR units)'); ax.set_title('Sign heterogeneity: HTF direction continues (USTEC) vs reverses (XAUUSD)')
ax.legend(); ax.grid(alpha=.3,axis='y'); fig.tight_layout(); fig.savefig(P/"heterogeneity_edge.png",dpi=110); plt.close(fig)

# 4. Drift vs timing decomposition + phase-shift (scatter: edge vs phaseshift)
fig,ax=plt.subplots(1,2,figsize=(11,4.5))
for ins in INST:
    d=edge.filter(pl.col('instrument')==ins)
    ax[0].scatter(d['drift_comp'],d['edge'],s=10,color=C[ins],alpha=.6,label=ins)
    ax[1].scatter(d['edge'],d['phaseshift_edge'],s=10,color=C[ins],alpha=.6,label=ins)
lim=1.0
ax[0].plot([-lim,lim],[-lim,lim],'k--',lw=.6); ax[0].set_xlim(-.3,.3)
ax[0].set_xlabel('drift component tau*d (coin-flip twin)'); ax[0].set_ylabel('DI edge')
ax[0].set_title('Edge is NOT drift: drift_comp ~0, edge spans wide')
ax[1].plot([-lim,lim],[-lim,lim],'k--',lw=.6,label='no collapse'); ax[1].axhline(0,color='k',lw=.5)
ax[1].set_xlabel('DI edge (aligned HTF)'); ax[1].set_ylabel('phase-shift edge (mis-aligned HTF)')
ax[1].set_title('Phase-shift collapses/reverses the edge (alignment-dependent)')
for a in ax: a.grid(alpha=.3); a.legend(fontsize=7)
fig.tight_layout(); fig.savefig(P/"drift_timing_phaseshift.png",dpi=110); plt.close(fig)

# 5. std_ratio heatmap: ATR regime x instrument (gating shape effect)
fig,ax=plt.subplots(figsize=(7,4))
base=dist.filter(pl.col('variant')=='none').select(['instrument','domain','hold_bars','std']).rename({'std':'bstd'})
g=dist.join(base,on=['instrument','domain','hold_bars']).with_columns((pl.col('std')/pl.col('bstd')).alias('sr'))
vars_=['atr_low','atr_med','atr_high','adx_lt25','adx_25_75','adx_ge75']
def _med(ins,v):
    x=g.filter((pl.col('instrument')==ins)&(pl.col('variant')==v))['sr'].median()
    return float(x) if x is not None else np.nan
M=np.array([[_med(ins,v) for v in vars_] for ins in INST],dtype=float)
im=ax.imshow(M,cmap='RdBu_r',vmin=0.6,vmax=1.4,aspect='auto')
ax.set_xticks(range(len(vars_))); ax.set_xticklabels(vars_,rotation=30,ha='right')
ax.set_yticks(range(len(INST))); ax.set_yticklabels(INST)
for i in range(len(INST)):
    for j in range(len(vars_)):
        ax.text(j,i,f"{M[i,j]:.2f}",ha='center',va='center',fontsize=8)
ax.set_title('Forward-move std ratio vs unfiltered baseline (gating = shape lever)')
fig.colorbar(im,label='std / baseline std'); fig.tight_layout(); fig.savefig(P/"std_ratio_heatmap.png",dpi=110); plt.close(fig)
print("wrote 5 figures to", P)
