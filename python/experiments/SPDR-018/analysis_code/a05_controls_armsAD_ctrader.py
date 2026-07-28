"""Q6 controls, arms A & D quantification, cTrader replication, integrity re-check, IN-5 CI coverage."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen")
RES = ROOT / "python/experiments/SPDR-018/results"
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 90); pd.set_option("display.max_rows", 400)

m = pd.read_parquet(RES / "metrics_by_cell.parquet")

print("=" * 100); print("INTEGRITY SELF-CHECK (re-read, not re-run)"); print("=" * 100)
ic = json.loads((RES / "integrity_selfcheck.json").read_text())
print("top keys:", list(ic.keys()))
def walk(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("status", "class", "hard", "failed", "n_failed", "ok", "pass", "result"):
                print(f"  {p}.{k} = {v}")
            else:
                walk(v, p + "." + k)
walk(ic)

print("\n" + "=" * 100); print("PARENT PARITY"); print("=" * 100)
print(json.dumps(json.loads((RES / "parent_parity.json").read_text()), indent=1)[:2600])

print("\n" + "=" * 100); print("CONTROLS"); print("=" * 100)
ct = json.loads((RES / "controls.json").read_text())
print("keys:", list(ct.keys()))
print(json.dumps(ct, indent=1)[:7000])
