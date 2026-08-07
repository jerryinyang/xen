"""Post-run corrections + coverage-gap closure (operator-approved 2026-07-26)."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE)); sys.path.insert(1,str(HERE.parents[1]/"SPDR-018"/"screen_code"))
import sigma_targets, deflators, uniform_controls as ctl, retarget, arm_c18b, cells
from config18b import RESULTS_DIR, CTRADER_SYMBOLS
for p in ("SPDR-012","SPDR-013","SPDR-014","SPDR-015"): retarget.rebind(p)

# ---- 1. precision targets in sigma units -----------------------------------------------------
d=pd.read_parquet(RESULTS_DIR/"metrics_by_cell.parquet")
d=sigma_targets.apply(d)
d.to_parquet(RESULTS_DIR/"metrics_by_cell.parquet",index=False)
m=d.arm.isin(["B","C"])
print("powered abs->sigma:",int(pd.to_numeric(d.loc[m,'at_parent_target_precision_absolute__SUPERSEDED'],errors='coerce').fillna(0).sum()),
      "->",int(d.loc[m,'at_parent_target_precision'].fillna(False).sum()),flush=True)

pc=pd.read_parquet(RESULTS_DIR/"panel_C.parquet")
cj=json.loads((RESULTS_DIR/"controls.json").read_text())

# ---- 2. M-3 on the CORRECT shock-MOMO object (P-MOMO only), gross ----------------------------
mo=pc[pc.policy=="P-MOMO"]
live=mo[mo.shock_flag.astype(bool)]; pool=mo[~mo.shock_flag.astype(bool)]
if len(live)>=5 and len(pool)>=5:
    cj["magnitude_matched_C2_MOMO_gross"]=ctl.magnitude_matched(
        live["c_gross_bps"].abs().to_numpy(float), live["c_gross_bps"].to_numpy(float),
        pool["c_gross_bps"].abs().to_numpy(float), pool["c_gross_bps"].to_numpy(float),
        np.zeros(len(pool),bool))
    print("C2 P-MOMO gross M-3:",cj["magnitude_matched_C2_MOMO_gross"].get("live_effect_bps"),
          "pctile",cj["magnitude_matched_C2_MOMO_gross"].get("percentile"),"n",len(live),flush=True)
mr=pc[pc.policy=="P-MR"]
l2=mr[mr.shock_flag.astype(bool)]; p2=mr[~mr.shock_flag.astype(bool)]
if len(l2)>=5 and len(p2)>=5:
    cj["magnitude_matched_C2_MR_gross"]=ctl.magnitude_matched(
        l2["c_gross_bps"].abs().to_numpy(float), l2["c_gross_bps"].to_numpy(float),
        p2["c_gross_bps"].abs().to_numpy(float), p2["c_gross_bps"].to_numpy(float),
        np.zeros(len(p2),bool))
cj["magnitude_matched_full_panel_shock_flag"]={
    **cj.get("magnitude_matched_full_panel_shock_flag",{}),
    "SUPERSEDED":"net, and over all shock bars incl. rows carrying no momentum policy; "
                 "use magnitude_matched_C2_MOMO_gross"}

# ---- 3. session-stratified M-3 on the shock rows (the analyst's P1) --------------------------
hr=pd.to_datetime(mo["event_ts"],unit="ns").dt.hour
sess={"ASIA":(0,8),"EU":(8,16),"US":(16,24)}
cj["magnitude_matched_C2_MOMO_by_session"]={}
for name,(a,b) in sess.items():
    sel=mo[(hr>=a)&(hr<b)]
    lv=sel[sel.shock_flag.astype(bool)]; pl_=sel[~sel.shock_flag.astype(bool)]
    if len(lv)<5 or len(pl_)<5:
        cj["magnitude_matched_C2_MOMO_by_session"][name]={"status":"TOO_FEW","n_live":int(len(lv))};continue
    cj["magnitude_matched_C2_MOMO_by_session"][name]=ctl.magnitude_matched(
        lv["c_gross_bps"].abs().to_numpy(float), lv["c_gross_bps"].to_numpy(float),
        pl_["c_gross_bps"].abs().to_numpy(float), pl_["c_gross_bps"].to_numpy(float),
        np.zeros(len(pl_),bool))
    r=cj["magnitude_matched_C2_MOMO_by_session"][name]
    print(f"  session {name}: live {r.get('live_effect_bps')} pctile {r.get('percentile')} n {len(lv)}",flush=True)
(RESULTS_DIR/"controls.json").write_text(json.dumps(cj,indent=2,sort_keys=True,default=str))

# ---- 4. coverage gaps C7, C8 (cheap, from the arm-C records/panel) ---------------------------
c1=[r for r in d[(d.arm=="C")&(d.residue_item=="C1")].to_dict("records")]
extra=arm_c18b.sign_flip_rows(c1) if hasattr(arm_c18b,"sign_flip_rows") else []
import importlib
a18=importlib.import_module("arm_c")            # SPDR-018's arm C has both helpers
extra=a18.sign_flip_rows(c1)
rate=a18.rate_lean_rows(pc)
gap=cells.to_frame(extra+rate)
gap["universe"]="CTRADER"
gap.to_parquet(RESULTS_DIR/"coverage_gap_C7_C8.parquet",index=False)
print("C7 rows",len(extra),"C8 rows",len(rate),flush=True)
# ---- 5. B3 given a NATIVE definition on this universe ----------------------------------------
# SPDR-018 defined B3 by pointing at SPDR-013's PUBLISHED CRYPTO table ("the positive-mean cells
# that are every one UNPOWERED"). That reference does not exist for cTrader, which is why the item
# looked absent. The definition is reconstructed natively: cells on cTrader's OWN arm-B grid whose
# mean is positive and which do not reach the (sigma-scaled) precision target.
b=d[d.arm=="B"].copy()
for c in ("net_mean","gross_mean"):
    b[c]=pd.to_numeric(b.get(c),errors="coerce")
pw=b["at_parent_target_precision"].fillna(False).astype(bool)
b3=b[(b.net_mean>0)&(~pw)].copy()
b3["residue_item"]="B3"
b3["b3_definition"]=("NATIVE to this universe: positive net mean AND short of the sigma-scaled "
                    "precision target. SPDR-018's B3 was defined by reference to SPDR-013's "
                    "published crypto table, which has no cTrader analogue.")
b3.to_parquet(RESULTS_DIR/"coverage_gap_B3.parquet",index=False)
print("B3 native cells:",len(b3),
      "| of which gross-positive:",int((b3.gross_mean>0).sum()),flush=True)
b3g=b[(b.gross_mean>0)&(~pw)]
print("B3 on GROSS basis:",len(b3g),flush=True)

json.dump(deflators.detail(),open(RESULTS_DIR/"deflators.json","w"),indent=2,default=str)
print("done",flush=True)
