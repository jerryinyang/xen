"""Run INFR-009 P3c freeze-grade-n confirm (n_null=200; P3b procedure held)."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "python" / "src"))

from xen.xena.calibration_p3c import run_p3c_calibration  # noqa: E402

OUT = ROOT / "python" / "experiments" / "INFR-009" / "results"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("P3c freeze-grade-n start", datetime.now(timezone.utc).isoformat(), flush=True)
    report = run_p3c_calibration(purge_mult=1)
    report["generated_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path = OUT / "p3c_calibration.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report["stop_condition"], indent=2))
    print("wrote", path)
    print("VERDICT:", report["stop_condition"]["verdict"])


if __name__ == "__main__":
    main()
