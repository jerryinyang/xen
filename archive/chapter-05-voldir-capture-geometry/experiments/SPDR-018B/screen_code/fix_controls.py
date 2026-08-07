"""Rebuild arm C's panel and compute its controls — the M-3 comparator is the replication target
for SPDR-018's one live thread (C2 shock-MOMO), and a resumed run left the panel empty so it was
silently skipped. The panel is persisted this time so it can never be skipped again."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(1, str(HERE.parents[1]/"SPDR-018"/"screen_code"))
import retarget, arm_c18b, uniform_controls as controls
from config18b import RESULTS_DIR, CTRADER_SYMBOLS

for p in ("SPDR-012","SPDR-013","SPDR-014","SPDR-015"): retarget.rebind(p)
man = retarget.ctrader_manifest()
pp = RESULTS_DIR/"panel_C.parquet"
if pp.exists():
    pc = pd.read_parquet(pp); print("panel_C resumed", pc.shape, flush=True)
else:
    fr=[arm_c18b.build_posts(s, man) for s in CTRADER_SYMBOLS]
    pc = pd.concat([f for f in fr if not f.empty], ignore_index=True)
    out = pc.copy()
    for c in out.columns:
        if out[c].dtype==object and len(set(out[c].dropna().map(lambda v:type(v).__name__)))>1:
            out[c]=out[c].map(lambda v: v if v is None else str(v)).astype("string")
    out.to_parquet(pp, index=False); print("panel_C built+persisted", pc.shape, flush=True)

cj = json.loads((RESULTS_DIR/"controls.json").read_text())
cp = pc[(pc.source=="Z-VOL")&(pc.z==1.5)&(pc.H==12)&(pc.event_type=="E-TOUCH")
        &(pc.h==12)&(pc.policy=="P-NONE")]
print("arm C primary cell rows:", len(cp), flush=True)
if len(cp) > 10:
    grp=(cp["symbol"].astype(str)+"|"+pd.to_datetime(cp["entry_ts"],unit="ns").dt.strftime("%Y-%m")).to_numpy()
    cj["arm_C_side_derangement"]=controls.side_derangement(
        cp["c_net_bps"].to_numpy(float), cp["side"].to_numpy(float), grp)
    cj["magnitude_matched"]={}
    for cond in ("shock_flag","mag_high"):
        live=cp[cp[cond].astype(bool)]; pool=cp[~cp[cond].astype(bool)]
        if len(live)<5 or len(pool)<5:
            cj["magnitude_matched"][cond]={"status":"TOO_FEW_ROWS","n_live":int(len(live)),
                                           "n_pool":int(len(pool))}; continue
        cj["magnitude_matched"][cond]=controls.magnitude_matched(
            live["c_gross_bps"].abs().to_numpy(float), live["c_net_bps"].to_numpy(float),
            pool["c_gross_bps"].abs().to_numpy(float), pool["c_net_bps"].to_numpy(float),
            np.zeros(len(pool),dtype=bool))
    # the C2 thread on its own terms: shock vs non-shock across the WHOLE arm-C panel
    for cond in ("shock_flag",):
        live=pc[pc[cond].astype(bool)]; pool=pc[~pc[cond].astype(bool)]
        cj["magnitude_matched_full_panel_"+cond]=controls.magnitude_matched(
            live["c_gross_bps"].abs().to_numpy(float), live["c_net_bps"].to_numpy(float),
            pool["c_gross_bps"].abs().to_numpy(float), pool["c_net_bps"].to_numpy(float),
            np.zeros(len(pool),dtype=bool))
cj["controls_rebuilt_note"]=("arm C controls were skipped by a resumed run (empty panel); "
                             "rebuilt here and the panel persisted to results/panel_C.parquet")
(RESULTS_DIR/"controls.json").write_text(json.dumps(cj,indent=2,sort_keys=True,default=str))
print("controls.json updated", flush=True)
