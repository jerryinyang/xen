"""VAL-006 Phase 0 — estimand validation gate over every in-scope multi-leg family root.

Scope: 4h allow/extend/both-leg roots of EXP-014b and EXP-014c (+ shift twins), plus the
EXP-016 root (TRAIN+TEST span; TEST is not read here — the gate only validates accounting).
Blocking output: results/estimand_validation.json (per root, per cell).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "python" / "src"))

from xen.estimand_validation import validate_family  # noqa: E402
from xen.referee_adaptive import adaptive_cost_bps_for  # noqa: E402

DATA = ROOT / "data" / "strategy_runs"
OUT = ROOT / "python" / "experiments" / "VAL-006" / "results" / "estimand_validation.json"

S8 = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD",
      "USTEC", "US500", "US2000", "JP225"]

ROOTS = [
    # EXP-014b e0 (moving exit) multi-leg + both-leg
    "EXP-014b-4h-s8-allow-z15", "EXP-014b-4h-s8-allow-z20",
    "EXP-014b-4h-s8-extend-z15", "EXP-014b-4h-s8-extend-z20",
    "EXP-014b-4h-s8-extend-z15-shift", "EXP-014b-4h-s8-extend-z20-shift",
    "EXP-014b-4h-s8-bllim-z15", "EXP-014b-4h-s8-bllim-z20",
    "EXP-014b-4h-s8-blmkt-z15", "EXP-014b-4h-s8-blmkt-z20",
    # EXP-014c e1-e3 multi-leg
    "EXP-014c-4h-s8-e1-allow-z15", "EXP-014c-4h-s8-e1-allow-z20",
    "EXP-014c-4h-s8-e1-extend-z15", "EXP-014c-4h-s8-e1-extend-z20",
    "EXP-014c-4h-s8-e2-allow-z15",
    "EXP-014c-4h-s8-e2-extend-z15", "EXP-014c-4h-s8-e2-extend-z15-shift",
    "EXP-014c-4h-s8-e2-extend-z20",
    "EXP-014c-4h-s8-e3-allow-z15", "EXP-014c-4h-s8-e3-allow-z20",
    "EXP-014c-4h-s8-e3-extend-z15", "EXP-014c-4h-s8-e3-extend-z15-shift",
    "EXP-014c-4h-s8-e3-extend-z20",
    # EXP-016 (TRAIN+TEST span; accounting gate only)
    "EXP-016-4h-s8-e3-extend-z15", "EXP-016-4h-s8-e3-extend-z15-shift",
]


def main() -> int:
    reports = {}
    all_ok = True
    for name in ROOTS:
        root = DATA / name
        if not root.exists():
            reports[name] = {"blocking_pass": False, "error": "root missing"}
            all_ok = False
            continue
        # cost varies per instrument; gate reconciliation is gross so a flat cost is fine,
        # but use the frozen map for the physicality report via per-run validation
        rep = validate_family(root, expected_instruments=None, cost_bps=0.0)
        # re-run physicality per cell with the frozen per-instrument cost
        for cell in rep["cells"]:
            inst = cell.get("instrument")
            if inst and cell.get("physicality"):
                from xen.estimand_validation import validate_run
                cell_rep = validate_run(cell["run_dir"],
                                        cost_bps=adaptive_cost_bps_for(inst, "4h"))
                cell.update(cell_rep)
        rep["blocking_pass"] = bool(all(c["blocking_pass"] for c in rep["cells"])
                                    and rep["cells"])
        n_cells = rep["n_cells"]
        ok = rep["blocking_pass"]
        all_ok &= ok
        reports[name] = rep
        print(f"{name:45s} cells={n_cells:2d} pass={ok}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"blocking_pass": all_ok, "roots": reports},
                              indent=2, default=str))
    print(f"\nOVERALL BLOCKING_PASS: {all_ok}\n→ {OUT}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
