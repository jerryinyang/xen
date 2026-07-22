#!/usr/bin/env python3
"""INFR-014 CAL orchestrator — WP1–WP4 + WP6.

Order (design): DESIGN both classes → CONFIRM both (if design_ok) → registry pin
→ next-open artifact. Chapter-03 pin never loaded.

Usage:
  PYTHONPATH=src python experiments/INFR-014/code/run_cal.py [--class CLS-FILTER|CLS-EPISODE|ALL]
  PYTHONPATH=src python experiments/INFR-014/code/run_cal.py --toy   # small n for wiring smoke
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXP = Path(__file__).resolve().parents[1]
RESULTS = EXP / "results"
sys.path.insert(0, str(ROOT / "src"))

from xen.nautilus.universe_selection import SelectionRule, rule_hash
from xen.xena.calibration_bybit import (
    CLASS_IDS,
    CONFIRM_SCALE,
    DESIGN_SCALE,
    confirm_gate,
    cost_pins_payload,
    next_open_sanity_artifact,
    run_design,
    verify_bybit_registry,
    write_bybit_registry,
)
from xen.xena.calibration_p3b import ScaleSpec as _ScaleSpec


def _json_dump(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    def _default(o):
        if isinstance(o, float):
            return o
        return str(o)

    path.write_text(json.dumps(obj, indent=2, default=_default) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--class", dest="class_id", default="ALL",
                    choices=["ALL", "CLS-FILTER", "CLS-EPISODE"])
    ap.add_argument("--toy", action="store_true",
                    help="tiny n_null for wiring only (NOT binding pin)")
    ap.add_argument("--design-only", action="store_true")
    ap.add_argument("--confirm-only", action="store_true",
                    help="load design_*.json and run confirm")
    args = ap.parse_args()

    RESULTS.mkdir(parents=True, exist_ok=True)
    _json_dump(RESULTS / "cost_pins.json", cost_pins_payload())

    # WP6 next-open apparatus (required even if market-only)
    print("[INFR-014] WP6 next-open discriminating control...", flush=True)
    no_art = next_open_sanity_artifact(seed=42)
    _json_dump(RESULTS / "next_open_control.json", no_art)

    # default selection rule hash for registry
    rh = rule_hash(SelectionRule())
    _json_dump(RESULTS / "selection_rule_default.json", {
        "rule": SelectionRule().__dict__,
        "rule_hash": rh,
    })

    if args.toy:
        design_scale = _ScaleSpec("toy_design", n_null=4, n_cand=8, budget=40,
                                  n_restarts=2, n_power=2, n_coverage=4)
        confirm_scale = _ScaleSpec("toy_confirm", n_null=4, n_cand=8, budget=40,
                                   n_restarts=2, n_power=2, n_coverage=4)
        print("[INFR-014] TOY scales — not binding for pin", flush=True)
    else:
        design_scale = DESIGN_SCALE
        confirm_scale = CONFIRM_SCALE

    classes = list(CLASS_IDS) if args.class_id == "ALL" else [args.class_id]
    class_results: dict = {}

    for cid in classes:
        design_path = RESULTS / f"design_{cid}.json"
        confirm_path = RESULTS / f"confirm_{cid}.json"

        if args.confirm_only:
            design = json.loads(design_path.read_text())
        else:
            print(f"[INFR-014] WP2 DESIGN {cid}...", flush=True)
            design = run_design(cid, scale=design_scale)
            _json_dump(design_path, design)

        class_results[cid] = {"design": design, "confirm": None}

        if not design.get("design_ok"):
            print(f"[INFR-014] {cid} bite FAIL → TERMINAL, no confirm", flush=True)
            continue
        if args.design_only:
            continue

        print(f"[INFR-014] WP3 CONFIRM {cid} (n_null={confirm_scale.n_null})...", flush=True)
        # enforce predeclared n for binding runs
        if not args.toy and confirm_scale.n_null != 200:
            raise SystemExit("binding confirm requires n_null=200")
        confirm = confirm_gate(cid, design["frozen_procedure"], scale=confirm_scale)
        _json_dump(confirm_path, confirm)
        class_results[cid]["confirm"] = confirm
        print(
            f"[INFR-014] {cid} verdict={confirm['outcome']['verdict']}",
            flush=True,
        )

    # WP4 registry — only if ≥1 class certifiable
    registry_ok = None
    if not args.design_only and not args.toy:
        print("[INFR-014] WP4 registry write...", flush=True)
        try:
            art = write_bybit_registry(
                class_results,
                out_path=RESULTS / "bybit_pc_frozen_registry.json",
                selection_rule_default_hash=rh,
                next_open_artifact=no_art,
            )
            reg = verify_bybit_registry(RESULTS / "bybit_pc_frozen_registry.json")
            _json_dump(RESULTS / "registry_verify.json", {
                "ok": True,
                "sha256": art["sha256"],
                "schema": reg["schema"],
                "recorded_utc": datetime.now(timezone.utc).isoformat(),
            })
            print(f"[INFR-014] registry sha256={art['sha256']}", flush=True)
            registry_ok = True
        except Exception as e:
            _json_dump(RESULTS / "registry_verify.json", {
                "ok": False,
                "error": f"{type(e).__name__}: {e}",
                "recorded_utc": datetime.now(timezone.utc).isoformat(),
            })
            print(f"[INFR-014] registry NOT written: {e}", flush=True)
            registry_ok = False
    elif args.toy:
        print("[INFR-014] toy mode — skip binding registry write", flush=True)

    # Always write cal_summary from this runner (QA Issue 11 — reproducible)
    summary = {
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "classes": {
            cid: {
                "design_ok": (class_results.get(cid) or {}).get("design", {}).get("design_ok"),
                "verdict": (
                    ((class_results.get(cid) or {}).get("confirm") or {})
                    .get("outcome", {}).get("verdict")
                ),
                "per_cadence": (
                    ((class_results.get(cid) or {}).get("confirm") or {})
                    .get("per_cadence")
                ),
            }
            for cid in classes
        },
        "registry_written": bool(registry_ok),
        "toy": bool(args.toy),
        "producer": "experiments/INFR-014/code/run_cal.py",
    }
    _json_dump(RESULTS / "cal_summary.json", summary)
    print(json.dumps(summary, indent=2, default=str), flush=True)
    # binding path: registry refused when zero certifiable is a valid TERMINAL outcome (rc 0)
    # only fail hard if design_ok but confirm missing for non-toy full run
    if not args.toy and not args.design_only:
        for cid in classes:
            d = (class_results.get(cid) or {}).get("design") or {}
            c = (class_results.get(cid) or {}).get("confirm")
            if d.get("design_ok") and c is None:
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
