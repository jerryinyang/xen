"""Run INFR-009 P3 calibration (fresh null bank only).

Writes results/p3_calibration.json. NEVER touches XENA-001/002/003 or holdout.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "python" / "src"))

from xen.xena.calibration_p3 import run_p3_calibration  # noqa: E402

OUT = ROOT / "python" / "experiments" / "INFR-009" / "results"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("P3 CAL start", datetime.now(timezone.utc).isoformat(), flush=True)
    # Predeclared n_null=40; n_power/n_coverage as design §P3
    report = run_p3_calibration(n_null=40, n_power=8, n_coverage=40)
    report["generated_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path = OUT / "p3_calibration.json"
    # slim write: drop ultra-verbose nested rows already present as alpha_*_rows
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    stop = report["stop_condition"]
    print(json.dumps(stop, indent=2))
    print("wrote", path)
    print("VERDICT:", stop["verdict"])


if __name__ == "__main__":
    main()
