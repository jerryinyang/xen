#!/usr/bin/env python3
"""Independent TRAIN-only runner for SPDR-021."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PYTHON_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PYTHON_ROOT / "src"))

from xen.adaptive_management import runner  # noqa: E402
from xen.adaptive_management.contracts import experiment_spec  # noqa: E402


def _print_progress(event: dict) -> None:
    print(json.dumps(event, sort_keys=True), file=sys.stderr, flush=True)


def main(argv: list[str] | None = None) -> dict:
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", required=True, choices=("crypto", "ctrader"))
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)
    result = runner.run_experiment(
        experiment_spec("SPDR-021"),
        args.universe,
        args.output,
        jobs=args.jobs,
        dry_run=args.dry_run,
        resume=args.resume,
        progress=_print_progress,
    )
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return result


if __name__ == "__main__":
    main()
