"""INFR-015 AMENDMENT-4 runner — floor derivation → bite → confirm → pin amend.

TERMINAL-3 on: no admissible floor, bite fail, or confirm fail — no write in all
three; pin ac8a1eb6… stands (design §14.5).
"""
from __future__ import annotations

import json
from pathlib import Path

from xen.xena.calibration_bybit import IntegrityError
from xen.xena.calibration_bybit15 import (
    CONFIRM_SCALE_15,
    CONFIRM_SEEDS_A4,
    DESIGN_SCALE_15,
    DESIGN_SEEDS_A4,
    amend_registry_episode,
    confirm_gate_a4,
    run_design_a4,
)

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
EXISTING_PIN = ROOT.parent / "INFR-014" / "results" / "bybit_pc_frozen_registry.json"


def _dump(name: str, obj: dict) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / name).write_text(json.dumps(obj, indent=2, default=str) + "\n",
                                encoding="utf-8")
    print(f"[INFR-015/A4] wrote results/{name}", flush=True)


def main() -> None:
    summary: dict = {"producer": "run_cal15_a4.py", "experiment": "INFR-015/AMENDMENT-4"}
    design = run_design_a4(scale=DESIGN_SCALE_15)
    # rows are large — persist derivation + slim rows
    slim = dict(design)
    slim["rows_by_cadence"] = {
        k: {"cov_rate_floor_off": v["cov_rate_floor_off"],
            "alpha_hat_floor_off": v["alpha_hat_floor_off"],
            "seed_bases": v["seed_bases"],
            "coverage_rows": v["coverage_rows"], "alpha_rows": v["alpha_rows"]}
        for k, v in (design.get("rows_by_cadence") or {}).items()
    }
    _dump("design_a4_CLS-EPISODE.json", slim)
    summary["design_ok"] = design.get("design_ok")
    summary["stop_reason"] = design.get("stop_reason")
    summary["floor_star"] = (design.get("floor_derivation") or {}).get("floor_star")

    if not design.get("design_ok"):
        summary["verdict"] = f"TERMINAL-3 ({design.get('stop_reason')})"
        summary["pin_amended"] = False
        _dump("cal15_a4_summary.json", summary)
        return

    confirm = confirm_gate_a4(design["frozen_procedure"], scale=CONFIRM_SCALE_15)
    _dump("confirm_a4_CLS-EPISODE.json", confirm)
    summary["verdict"] = confirm["outcome"]["verdict"]
    summary["per_cadence"] = confirm["per_cadence"]

    try:
        artifact = amend_registry_episode(
            EXISTING_PIN, design, confirm,
            out_path=RESULTS / "bybit_pc_frozen_registry.json",
            design_seeds=DESIGN_SEEDS_A4, confirm_seeds=CONFIRM_SEEDS_A4,
            amended_by="INFR-015/AMENDMENT-4",
        )
        summary["pin_amended"] = True
        summary["new_sha256"] = artifact["sha256"]
        summary["superseded"] = artifact["registry"]["superseded_pins"]
    except IntegrityError as e:
        summary["pin_amended"] = False
        summary["write_refusal"] = str(e)

    _dump("cal15_a4_summary.json", summary)


if __name__ == "__main__":
    main()
