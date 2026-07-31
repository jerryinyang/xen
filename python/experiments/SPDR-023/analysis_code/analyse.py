"""Analyse one completed SPDR-023 run without contacting another experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from xen.adaptive_management.analysis import analyse_run

EXPERIMENT_ID = "SPDR-023"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    config = json.loads((args.run / "config.json").read_text(encoding="utf-8"))
    if config.get("experiment_id") != EXPERIMENT_ID:
        raise ValueError(f"{EXPERIMENT_ID} wrapper received a different experiment run")
    analyse_run(args.run, args.output)


if __name__ == "__main__":
    main()
