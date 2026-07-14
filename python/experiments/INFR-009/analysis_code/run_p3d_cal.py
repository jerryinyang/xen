"""Run INFR-009 P3d design bank fit → freeze → confirm bank gate."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "python" / "src"))

from xen.xena.calibration_p3d import run_p3d  # noqa: E402

OUT = ROOT / "python" / "experiments" / "INFR-009" / "results"
DESIGN_MD = ROOT / "python" / "experiments" / "INFR-009" / "design.md"


def write_freeze_into_design(procedure: dict) -> None:
    """Fill §P3d.8 FREEZE boundary after design, before confirm is trusted."""
    text = DESIGN_MD.read_text(encoding="utf-8")
    block = (
        "### P3d.8 FREEZE boundary (filled after DESIGN bank only — before CONFIRM)\n\n"
        f"**Frozen UTC:** {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n\n"
        "```\n"
        "STATUS: FROZEN_AFTER_DESIGN\n"
        f"procedure: {json.dumps(procedure, sort_keys=True)}\n"
        "confirm_must_not_change_this_block: true\n"
        "```\n"
    )
    text2, n = re.subn(
        r"### P3d\.8 FREEZE boundary.*?(?=\n---\n|\n\*End design)",
        block + "\n",
        text,
        count=1,
        flags=re.S,
    )
    if n == 0:
        # fallback append before end
        text2 = text.replace(
            "*End design. P4 only after P3d CONFIRM PASS + separate operator mandate.*",
            block + "\n*End design. P4 only after P3d CONFIRM PASS + separate operator mandate.*",
        )
    DESIGN_MD.write_text(text2, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("P3d start", datetime.now(timezone.utc).isoformat(), flush=True)
    design, confirm = run_p3d(purge_mult=1)

    # Freeze procedure into design.md BEFORE writing confirm as the gate artifact
    write_freeze_into_design(design["frozen_procedure"])
    print("wrote freeze into design.md §P3d.8", flush=True)

    design["generated_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    confirm["generated_utc"] = design["generated_utc"]

    (OUT / "p3d_design.json").write_text(json.dumps(design, indent=2, default=str))
    (OUT / "p3d_confirm.json").write_text(json.dumps(confirm, indent=2, default=str))
    print(json.dumps(confirm["stop_condition"], indent=2))
    print("VERDICT:", confirm["stop_condition"]["verdict"])
    print("wrote", OUT / "p3d_design.json", OUT / "p3d_confirm.json")


if __name__ == "__main__":
    main()
