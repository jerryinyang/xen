import sys
from pathlib import Path
import pandas as pd
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE)); sys.path.insert(1,str(HERE.parents[1]/"SPDR-018"/"screen_code"))
import retarget, arm_c18b
from config18b import RESULTS_DIR, CTRADER_SYMBOLS
for p in ("SPDR-012","SPDR-013","SPDR-014","SPDR-015"): retarget.rebind(p)
man=retarget.ctrader_manifest()
fr=[arm_c18b.build_posts(s,man) for s in CTRADER_SYMBOLS]
pc=pd.concat([f for f in fr if not f.empty],ignore_index=True)
out=pc.copy()
for c in out.columns:
    if out[c].dtype==object and len(set(out[c].dropna().map(lambda v:type(v).__name__)))>1:
        out[c]=out[c].map(lambda v: v if v is None else str(v)).astype("string")
out.to_parquet(RESULTS_DIR/"panel_C.parquet",index=False)
print("panel_C rebuilt+persisted",pc.shape,flush=True)
