#!/usr/bin/env python3
"""§4.4 cadence-coverage attestation (CLS-FILTER LOW-only pin).

Per-candidate: n_legs + mean hold hours from emission cis_trades.
Park / escalate if certified top-1 stream is HIGH-shaped under LOW-only pin:
  mean hold < 2h  OR  leg density matches HIGH calibration class.

HIGH-shaped heuristic (design §4.4): mean hold < 2h.
Writes results/cadence_attestation.json — integrity check, not a quality gate.

Usage (from python/):
  uv run python experiments/XENA-HTFCAP-001/code/cadence_attestation.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import polars as pl

CODE = Path(__file__).resolve().parent
EXP = CODE.parent
ROOT = EXP.parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from xen.nautilus.adjudication_shim import emission_to_adjudication_frames  # noqa: E402

UNIVERSE_ID = "XENA-HTFCAP-001"
RUNS_ROOT = REPO / "data" / "nautilus_runs" / UNIVERSE_ID
MANIFEST_PATH = RUNS_ROOT / "universe_manifest.json"
RESULTS = EXP / "results"

# design §4.4 — LOW class holds 4–16h; HIGH-shaped if mean hold < 2h
HIGH_SHAPED_MEAN_HOLD_HOURS = 2.0


def _leg_stats(emission_dir: Path) -> dict[str, Any]:
    if not (emission_dir / "run_metadata.json").exists():
        return {"emitted": False, "n_legs": 0, "mean_hold_hours": None}
    try:
        _pos, cis, _meta = emission_to_adjudication_frames(emission_dir)
    except Exception as e:  # noqa: BLE001
        return {"emitted": True, "error": str(e), "n_legs": 0, "mean_hold_hours": None}
    live = cis.filter(pl.col("Censored").cast(pl.Boolean).not_())
    n = live.height
    if n == 0:
        return {"emitted": True, "n_legs": 0, "mean_hold_hours": None, "high_shaped": False}
    # hold = ExitTime - EntryTime
    et = live.get_column("EntryTime").cast(pl.Datetime("ns"))
    xt = live.get_column("ExitTime").cast(pl.Datetime("ns"))
    hold_ns = (xt.cast(pl.Int64) - et.cast(pl.Int64)).to_numpy()
    mean_h = float(hold_ns.mean() / 1e9 / 3600.0)
    high_shaped = mean_h < HIGH_SHAPED_MEAN_HOLD_HOURS
    return {
        "emitted": True,
        "n_legs": int(n),
        "mean_hold_hours": mean_h,
        "min_hold_hours": float(hold_ns.min() / 1e9 / 3600.0),
        "max_hold_hours": float(hold_ns.max() / 1e9 / 3600.0),
        "high_shaped": bool(high_shaped),
    }


def main() -> int:
    if not MANIFEST_PATH.exists():
        raise SystemExit(f"missing manifest {MANIFEST_PATH}")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = []
    n_high = 0
    n_emitted = 0
    for c in manifest["candidates"]:
        cid = c["candidate_id"]
        emission_dir = RUNS_ROOT / cid
        st = _leg_stats(emission_dir)
        st.update(
            {
                "candidate_id": cid,
                "symbol": c["symbol"],
                "role": c.get("role"),
                "hold_bars": c.get("hold_bars"),
                "filter_model": c.get("filter_model"),
            }
        )
        if st.get("emitted") and st.get("n_legs", 0) >= 0 and "error" not in st:
            if (emission_dir / "run_metadata.json").exists():
                n_emitted += 1
        if st.get("high_shaped"):
            n_high += 1
        rows.append(st)

    # Integrity: if any emitted binding cell is HIGH-shaped, flag park/escalate
    bind_high = [
        r for r in rows
        if r.get("role") == "binding" and r.get("high_shaped")
    ]
    artifact = {
        "universe_id": UNIVERSE_ID,
        "generated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "pin_cadence": "CLS-FILTER LOW_ONLY",
        "high_shaped_rule": f"mean_hold_hours < {HIGH_SHAPED_MEAN_HOLD_HOURS}",
        "n_candidates": len(rows),
        "n_emitted": n_emitted,
        "n_high_shaped": n_high,
        "n_binding_high_shaped": len(bind_high),
        "coverage_ok_for_low_pin": len(bind_high) == 0 or n_emitted == 0,
        "park_if_top1_high_shaped": (
            "If certified top-1 stream is HIGH-shaped under LOW-only pin → "
            "no gate spend; park + operator escalation (design §4.4)"
        ),
        "candidates": rows,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / "cadence_attestation.json"
    out.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(
        f"WROTE {out} emitted={n_emitted} high_shaped={n_high} "
        f"binding_high={len(bind_high)} coverage_ok={artifact['coverage_ok_for_low_pin']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
