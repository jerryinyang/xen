"""Driver — INFR-009 P-C exit (c) two-stage calibration (design.md §P-C).

    python run_pc_cal.py --design-only     # bite + coverage; freeze between phases
    python run_pc_cal.py --confirm-only    # gate on frozen procedure in pc_design.json
    python run_pc_cal.py                    # design → confirm (if design_ok)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from xen.xena.calibration_pc import confirm_gate, run_design

RESULTS = Path(__file__).resolve().parents[1] / "results"


def _write(name: str, obj: dict) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / name
    path.write_text(json.dumps(obj, indent=1, default=str), encoding="utf-8")
    print(f"  wrote {path}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--design-only", action="store_true")
    ap.add_argument("--confirm-only", action="store_true")
    args = ap.parse_args()

    if args.confirm_only:
        design = json.loads((RESULTS / "pc_design.json").read_text(encoding="utf-8"))
        proc = design.get("frozen_procedure")
        if not proc:
            raise SystemExit("pc_design.json has no frozen_procedure (design not OK)")
        confirm = confirm_gate(proc)
        _write("pc_confirm.json", confirm)
        print(f"[P-C] confirm verdict: {confirm['outcome']['verdict']}", flush=True)
        return

    design = run_design()
    _write("pc_design.json", design)
    print(f"[P-C] design_ok={design['design_ok']} stop_reason={design.get('stop_reason')}",
          flush=True)
    if not design["design_ok"] or args.design_only:
        return

    confirm = confirm_gate(design["frozen_procedure"])
    _write("pc_confirm.json", confirm)
    print(f"[P-C] confirm verdict: {confirm['outcome']['verdict']}", flush=True)


if __name__ == "__main__":
    main()
