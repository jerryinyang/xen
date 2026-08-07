#!/usr/bin/env python3
"""Run one SPDR-024 cell end to end, in the order the design requires.

The order is not cosmetic. Arm B runs first because the common maximum hold does not exist
until its duration distribution does; the cap then falls out of the declared rule mechanically.
The estimand gate runs before any analysis. The self-check runs before anything is pruned, and
nothing is pruned unless it passed.

Every step's timing and peak memory is recorded, so the performance claim is measured rather
than asserted.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
EXPERIMENT = HERE.parent
PYTHON_ROOT = EXPERIMENT.parents[1]
sys.path.insert(0, str(PYTHON_ROOT / "src"))

from xen.adaptive_management.runner import universe_config  # noqa: E402

RESULTS = EXPERIMENT / "results"


def _run(name: str, argv: list[str], log: Path) -> dict:
    started = time.monotonic()
    before = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w", encoding="utf-8") as stream:
        completed = subprocess.run(argv, stdout=stream, stderr=subprocess.STDOUT, check=False)
    after = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    record = {
        "step": name,
        "returncode": completed.returncode,
        "wall_seconds": round(time.monotonic() - started, 2),
        "peak_child_rss_bytes": int(max(before, after)),
        "log": str(log),
    }
    print(json.dumps(record), flush=True)
    if completed.returncode != 0:
        raise SystemExit(f"{name} failed (see {log})")
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", required=True, choices=("crypto", "ctrader"))
    parser.add_argument("--domain", required=True, choices=("H1", "H4"))
    parser.add_argument("--jobs", type=int, default=3)
    parser.add_argument(
        "--prune",
        action="store_true",
        help=(
            "delete the shift/replay runs on pass. OFF by default: they are the inputs the "
            "tripwire and determinism checks need, so pruning makes the self-check "
            "un-rerunnable without regenerating them"
        ),
    )
    args = parser.parse_args(argv)

    cell = f"{args.universe}_{args.domain}"
    runs = RESULTS / "runs" / cell
    logs = RESULTS / "logs" / cell
    python = sys.executable
    steps: list[dict] = []

    steps.append(
        _run(
            "hold_phase",
            [python, str(HERE / "run_screen.py"), "--universe", args.universe,
             "--domain", args.domain, "--phase", "hold", "--output", str(runs / "hold"),
             "--jobs", str(args.jobs)],
            logs / "hold.log",
        )
    )
    cap_path = RESULTS / f"{cell}_cap_rule.json"
    steps.append(
        _run(
            "cap_rule",
            [python, str(HERE / "cap_rule.py"), "--run", str(runs / "hold"),
             "--out", str(cap_path)],
            logs / "cap_rule.log",
        )
    )
    cap = json.loads(cap_path.read_text(encoding="utf-8"))
    cap_arguments = (
        ["--hold-cap-bars", str(cap["hold_cap_bars"])]
        if cap.get("status") == "SELECTED"
        else []
    )
    print(json.dumps({"cap_rule_status": cap.get("status"), "hold_cap_bars": cap.get("hold_cap_bars")}), flush=True)

    steps.append(
        _run(
            "full_grid",
            [python, str(HERE / "run_screen.py"), "--universe", args.universe,
             "--domain", args.domain, "--phase", "full", "--output", str(runs / "full"),
             "--jobs", str(args.jobs), *cap_arguments],
            logs / "full.log",
        )
    )
    steps.append(
        _run(
            "future_shift_tripwire",
            [python, str(HERE / "run_screen.py"), "--universe", args.universe,
             "--domain", args.domain, "--phase", "full", "--future-shift", "1",
             "--output", str(runs / "shift"), "--jobs", str(args.jobs), *cap_arguments],
            logs / "shift.log",
        )
    )
    steps.append(
        _run(
            "determinism_replay",
            [python, str(HERE / "run_screen.py"), "--universe", args.universe,
             "--domain", args.domain, "--phase", "full", "--output", str(runs / "replay"),
             "--jobs", "1", *cap_arguments],
            logs / "replay.log",
        )
    )
    estimand_path = RESULTS / f"estimand_validation_{cell}.json"
    symbols = ",".join(universe_config(args.universe).symbols)
    steps.append(
        _run(
            "estimand_gate",
            [python, "-m", "xen.estimand_validation", str(runs / "full" / "cells"),
             "--expect", symbols, "--out", str(estimand_path)],
            logs / "estimand.log",
        )
    )
    steps.append(
        _run(
            "selfcheck",
            [python, str(HERE / "selfcheck.py"), "--run", str(runs / "full"),
             "--golden-traces", str(RESULTS / "golden_traces.json"),
             "--shifted-run", str(runs / "shift"), "--replay-run", str(runs / "replay"),
             "--estimand-validation", str(estimand_path),
             "--out", str(RESULTS / "selfcheck" / cell)],
            logs / "selfcheck.log",
        )
    )
    steps.append(
        _run(
            "analysis",
            [python, str(EXPERIMENT / "analysis_code" / "analyse.py"),
             "--run", str(runs / "full"),
             "--output", str(RESULTS / "analysis" / cell), "--jobs", str(args.jobs)],
            logs / "analysis.log",
        )
    )

    if args.prune:
        # Only after the self-check passed: these two are reproducible from the same code and
        # the same fence, and the primary emission is untouched.
        for name in ("shift", "replay"):
            shutil.rmtree(runs / name, ignore_errors=True)
        steps.append({"step": "prune_reproducible_runs", "removed": ["shift", "replay"]})

    performance = RESULTS / "performance" / f"{cell}.json"
    performance.parent.mkdir(parents=True, exist_ok=True)
    performance.write_text(
        json.dumps(
            {
                "cell": cell,
                "universe": args.universe,
                "signal_domain": args.domain,
                "jobs": args.jobs,
                "steps": steps,
                "total_wall_seconds": round(
                    sum(item.get("wall_seconds", 0.0) for item in steps), 2
                ),
                "peak_child_rss_bytes": max(
                    (item.get("peak_child_rss_bytes", 0) for item in steps), default=0
                ),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"cell": cell, "status": "COMPLETE", "performance": str(performance)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
