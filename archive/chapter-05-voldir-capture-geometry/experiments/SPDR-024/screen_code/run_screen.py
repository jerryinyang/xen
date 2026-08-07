#!/usr/bin/env python3
"""Independent TRAIN-only runner for SPDR-024.

Two things distinguish this wrapper from the SPDR-021 one, and both come from the design:

* `--domain` selects the signal domain. H1 and H4 are separate cells and are never pooled
  (OD-2), so they are separate runs with separate output directories.
* `--phase hold` runs arms A and B only. The common maximum hold does not exist until arm B's
  duration distribution does, so it cannot be a parameter of the run that produces it
  (design section 7 H1/H2).

`--future-shift 1` is the leak tripwire and nothing else: it makes every volatility component
readable one signal-domain bar earlier than it could have been, so each arm conditions on
information it could not have had. Its emission is never used as a research result.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PYTHON_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PYTHON_ROOT / "src"))

from xen.adaptive_management import runner  # noqa: E402
from xen.adaptive_management.contracts import (  # noqa: E402
    SPDR024_HOLD_PHASE_ARMS,
    experiment_spec,
)

EXPERIMENT_ID = "SPDR-024"


def _print_progress(event: dict) -> None:
    print(json.dumps(event, sort_keys=True), file=sys.stderr, flush=True)


def main(argv: list[str] | None = None) -> dict:
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", required=True, choices=("crypto", "ctrader"))
    parser.add_argument("--domain", default="H1", choices=("H1", "H4"))
    parser.add_argument("--phase", default="full", choices=("hold", "full"))
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument(
        "--hold-cap-bars",
        type=int,
        default=None,
        help="common maximum hold, in signal-domain bars; only from the cap-rule artifact",
    )
    parser.add_argument(
        "--future-shift",
        type=int,
        default=0,
        choices=(0, 1),
        help="leak tripwire: make components readable one domain bar early",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)

    arm_filter = SPDR024_HOLD_PHASE_ARMS if args.phase == "hold" else None
    if args.phase == "hold" and args.hold_cap_bars is not None:
        raise SystemExit(
            "the hold phase produces the cap; it may not also be given one (design section 7)"
        )
    result = runner.run_experiment(
        experiment_spec(EXPERIMENT_ID, args.domain),
        args.universe,
        args.output,
        jobs=args.jobs,
        dry_run=args.dry_run,
        resume=args.resume,
        hold_cap_bars=args.hold_cap_bars,
        arm_filter=arm_filter,
        future_shift_bars=args.future_shift,
        progress=_print_progress,
    )
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return result


if __name__ == "__main__":
    main()
