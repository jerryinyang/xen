"""Run INFR-009 P3b re-calibration (disjoint bank; studentized LCB + purge)."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "python" / "src"))

from xen.xena.calibration_p3b import run_p3b_calibration  # noqa: E402

OUT = ROOT / "python" / "experiments" / "INFR-009" / "results"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("P3b CAL start", datetime.now(timezone.utc).isoformat(), flush=True)
    report = run_p3b_calibration(purge_mult=1, run_production=True)
    report["generated_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path = OUT / "p3b_calibration.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report["stop_condition"], indent=2))
    print("wrote", path)
    print("VERDICT:", report["stop_condition"]["verdict"])


if __name__ == "__main__":
    main()
