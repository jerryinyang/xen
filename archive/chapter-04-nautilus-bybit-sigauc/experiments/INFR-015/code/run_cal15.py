"""INFR-015 CAL runner — CLS-EPISODE amendment (design → confirm → pin amend).

Fork B: design bite FAIL => TERMINAL, no confirm. Confirm TERMINAL-2 => no write,
pin ac8a1eb6… stands. Amend only on certifiable verdict (design §11/§13).
"""
from __future__ import annotations

import json
from pathlib import Path

from xen.xena.calibration_bybit15 import (
    CONFIRM_SCALE_15,
    DESIGN_SCALE_15,
    amend_registry_episode,
    confirm_gate_ep,
    run_design_ep,
)
from xen.xena.calibration_bybit import IntegrityError

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
EXISTING_PIN = ROOT.parent / "INFR-014" / "results" / "bybit_pc_frozen_registry.json"


def _dump(name: str, obj: dict) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / name).write_text(json.dumps(obj, indent=2, default=str) + "\n",
                                encoding="utf-8")
    print(f"[INFR-015] wrote results/{name}", flush=True)


def main() -> None:
    summary: dict = {"producer": "run_cal15.py", "experiment": "INFR-015"}
    design = run_design_ep(scale=DESIGN_SCALE_15)
    _dump("design_CLS-EPISODE.json", design)
    summary["design_ok"] = design.get("design_ok")
    summary["design_stop_reason"] = design.get("stop_reason")

    if not design.get("design_ok"):
        summary["verdict"] = "TERMINAL (design bank — Fork B)"
        summary["pin_amended"] = False
        _dump("cal15_summary.json", summary)
        return

    confirm = confirm_gate_ep(design["frozen_procedure"], scale=CONFIRM_SCALE_15)
    _dump("confirm_CLS-EPISODE.json", confirm)
    outcome = confirm["outcome"]
    summary["verdict"] = outcome["verdict"]
    summary["per_cadence"] = confirm["per_cadence"]

    try:
        artifact = amend_registry_episode(
            EXISTING_PIN, design, confirm,
            out_path=RESULTS / "bybit_pc_frozen_registry.json",
        )
        summary["pin_amended"] = True
        summary["new_sha256"] = artifact["sha256"]
        summary["superseded"] = artifact["registry"]["superseded_pins"]
    except IntegrityError as e:
        summary["pin_amended"] = False
        summary["write_refusal"] = str(e)

    _dump("cal15_summary.json", summary)


if __name__ == "__main__":
    main()
