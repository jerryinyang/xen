"""Run INFR-009 P-BF: design (bite+K+freeze) → confirm gate.

Usage:
  python analysis_code/run_pbf_cal.py              # full design+confirm
  python analysis_code/run_pbf_cal.py --design-only
  python analysis_code/run_pbf_cal.py --confirm-only   # requires freeze in design.md / pbf_design.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "python" / "src"))

from xen.xena.calibration_pbf import run_pbf  # noqa: E402

OUT = ROOT / "python" / "experiments" / "INFR-009" / "results"
DESIGN_MD = ROOT / "python" / "experiments" / "INFR-009" / "design.md"


def write_freeze_into_design(procedure: dict) -> None:
    """Fill §P-BF.7 FREEZE boundary after design, before confirm is trusted.

    Uses a callable repl so JSON backslashes are not interpreted as re escapes.
    """
    text = DESIGN_MD.read_text(encoding="utf-8")
    block = (
        "### P-BF.7 FREEZE boundary (filled after DESIGN bank only — before CONFIRM)\n\n"
        f"**Frozen UTC:** {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n\n"
        "```\n"
        "STATUS: FROZEN_AFTER_DESIGN\n"
        f"procedure: {json.dumps(procedure, sort_keys=True)}\n"
        "confirm_must_not_change_this_block: true\n"
        "```\n\n"
    )
    pat = re.compile(
        r"### P-BF\.7 FREEZE boundary.*?(?=\n---\n|\n\*End design)",
        flags=re.S,
    )
    text2, n = pat.subn(lambda _m: block, text, count=1)
    if n == 0:
        text2 = text.replace(
            "*End design. P4 only after P-BF CONFIRM PASS + separate operator mandate. No P3e.*",
            block + "*End design. P4 only after P-BF CONFIRM PASS + separate operator mandate. No P3e.*",
        )
    DESIGN_MD.write_text(text2, encoding="utf-8")


def load_frozen_procedure() -> dict:
    path = OUT / "pbf_design.json"
    if not path.exists():
        raise SystemExit(f"missing {path}; run design first")
    design = json.loads(path.read_text(encoding="utf-8"))
    proc = design.get("frozen_procedure")
    if not proc:
        raise SystemExit("pbf_design.json has no frozen_procedure (design_ok failed?)")
    return proc


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--design-only", action="store_true")
    ap.add_argument("--confirm-only", action="store_true")
    ap.add_argument("--workers", type=int, default=None)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print("P-BF start", utc, flush=True)
    log_path = OUT / "pbf_run.log"
    # tee-style: also mirror key lines are already flushed by harness

    try:
        if args.confirm_only:
            proc = load_frozen_procedure()
            design, confirm = run_pbf(n_workers=args.workers, procedure=proc)
        else:
            design, confirm = run_pbf(
                n_workers=args.workers, design_only=args.design_only)
    except Exception as e:
        err = {
            "error": repr(e),
            "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        (OUT / "pbf_error.json").write_text(json.dumps(err, indent=2))
        print("FATAL", err, flush=True)
        raise

    design["generated_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (OUT / "pbf_design.json").write_text(json.dumps(design, indent=2, default=str))
    print("wrote", OUT / "pbf_design.json", flush=True)

    if design.get("design_ok") and design.get("frozen_procedure"):
        write_freeze_into_design(design["frozen_procedure"])
        print("wrote freeze into design.md §P-BF.7", flush=True)

    if confirm is not None:
        confirm["generated_utc"] = design["generated_utc"]
        (OUT / "pbf_confirm.json").write_text(json.dumps(confirm, indent=2, default=str))
        print(json.dumps(confirm["stop_condition"], indent=2))
        print("VERDICT:", confirm["stop_condition"]["verdict"])
        print("wrote", OUT / "pbf_confirm.json")
    else:
        print("design_ok:", design.get("design_ok"), "stop:", design.get("stop_reason"))
        if not design.get("design_ok"):
            print("STOP before confirm:", design.get("note") or design.get("stop_reason"))
    print("P-BF done", datetime.now(timezone.utc).isoformat(), flush=True)


if __name__ == "__main__":
    main()
