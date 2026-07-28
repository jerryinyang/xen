"""Add the controls SPDR-018B inherited from SPDR-018 §7 but never ran.

The design inherits THREE uniform controls and THREE tripwires. The run emitted only
side-derangement and the M-3 comparator: ambient-base and all three tripwires were absent, while
screen.md §7 said "Deviations: none". That is the SAME class of failure SPDR-018 made with
TRIPWIRE-2 — a HARD-declared check silently not running under a clean-sheet claim.
"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE)); sys.path.insert(1,str(HERE.parents[1]/"SPDR-018"/"screen_code"))
import uniform_controls as ctl
from config18b import RESULTS_DIR

pc=pd.read_parquet(RESULTS_DIR/"panel_C.parquet")
cj=json.loads((RESULTS_DIR/"controls.json").read_text())
cp=pc[(pc.source=="Z-VOL")&(pc.z==1.5)&(pc.H==12)&(pc.event_type=="E-TOUCH")&(pc.h==12)
      &(pc.policy=="P-NONE")]
print("primary cell rows",len(cp),flush=True)

# --- AMBIENT-BASE: the cell's own conditional effect vs the unconditional distribution ---------
amb=pc[(pc.policy=="P-NONE")]
cj["arm_C_ambient_base"]=ctl.ambient_base(
    cp["c_net_bps"].to_numpy(float), amb["c_net_bps"].to_numpy(float), cost_bps=0.0,
    ts_live=cp["entry_ts"].to_numpy(np.int64), ts_ambient=amb["entry_ts"].to_numpy(np.int64))
print("ambient-base done",flush=True)

# --- TRIPWIRE-1: construction assertions (HARD) ------------------------------------------------
tws=[]
sub=cp.dropna(subset=["event_idx","entry_idx","exit_idx","h"])
tws.append(ctl.tripwire_1_construction({
    "decision_idx": sub["event_idx"].to_numpy(np.int64),
    "entry_idx": sub["entry_idx"].to_numpy(np.int64),
    "exit_idx": sub["exit_idx"].to_numpy(np.int64),
    "h": sub["h"].to_numpy(np.int64)}))
print("tripwire-1 held",flush=True)

# --- TRIPWIRE-2: legal vs a forward-inclusive (leaky) selector on the same rows ----------------
r=cp["c_gross_bps"].to_numpy(float)
legal_mask=(cp["last_k_state_2"]=="LH").to_numpy() if "last_k_state_2" in cp else np.zeros(len(cp),bool)
k=int(legal_mask.sum())
legal=float(np.nanmean(r[legal_mask])) if k else float("nan")
order=np.argsort(-np.where(np.isfinite(r),r,-np.inf)); leaky=float(np.nanmean(r[order[:k]])) if k else float("nan")
tws.append(ctl.tripwire_2_leaky_twin(legal,leaky,n_matched=k))
print(f"tripwire-2 legal {legal:.2f} leaky {leaky:.2f}",flush=True)

# --- TRIPWIRE-3: forward-path derangement (report layer) --------------------------------------
grp=(cp["symbol"].astype(str)+"|"+pd.to_datetime(cp["entry_ts"],unit="ns").dt.strftime("%Y-%m")).to_numpy()
side=cp["side"].to_numpy(float); net=cp["c_net_bps"].to_numpy(float)
tws.append(ctl.tripwire_3_forward_path(side, net*side, grp))
print("tripwire-3 done",flush=True)

cj["tripwires"]=tws
cj["controls_completeness_note"]=(
    "ambient-base and TRIPWIRE-1/2/3 were ABSENT from the original SPDR-018B emission and are "
    "added here. screen.md §7's 'Deviations: none' was inaccurate and is corrected.")
(RESULTS_DIR/"controls.json").write_text(json.dumps(cj,indent=2,sort_keys=True,default=str))

sc=json.loads((RESULTS_DIR/"integrity_selfcheck.json").read_text())
sc["checks"].append({"check":"TRIPWIRE-1 CONSTRUCTION ASSERTIONS held","severity":"HARD",
                     "held":True,"detail":tws[0]})
sc["checks"].append({"check":"TRIPWIRE-2 LEAKY-VARIANT DISCRIMINATION","severity":"HARD",
                     "held":bool(np.isfinite(legal) and np.isfinite(leaky) and abs(leaky)>abs(legal)),
                     "detail":tws[1]})
sc["checks"].append({"check":"TRIPWIRE-3 FORWARD-PATH DERANGEMENT (report layer)",
                     "severity":"INFORMATIVE","detail":tws[2]})
sc["checks"].append({"check":"AMBIENT-BASE control present","severity":"HARD","held":True,
                     "detail":"added post-hoc; see controls.json arm_C_ambient_base"})
sc["late_addition_note"]=cj["controls_completeness_note"]
failed=[c["check"] for c in sc["checks"] if c["severity"]=="HARD" and not c.get("held")]
sc["hard_all_held"]=not failed; sc["failed_checks"]=failed
(RESULTS_DIR/"integrity_selfcheck.json").write_text(json.dumps(sc,indent=2,sort_keys=True,default=str))
print("HARD checks now:",sum(1 for c in sc['checks'] if c['severity']=='HARD'),"failed:",failed,flush=True)
