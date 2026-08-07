"""Produce the SPDR-011 estimand gate artifact with correct per-cell expectations.

`validate_family` forwards one `expected_instruments` list to every cell, so a five-symbol
expectation can never pass on SPDR-011's per-symbol cells (design §13 emits one cell per
symbol). The instrument expectation is therefore applied twice, at the level where it is
meaningful: each cell must contain its own symbol, and the family must contain all five.

Canonical calls only — no local reimplementation of any check.
"""
from __future__ import annotations

import json
from pathlib import Path

from xen.estimand_validation import validate_family, validate_run

ROOT = Path(__file__).resolve().parents[4]
FAMILY = ROOT / "data/nautilus_runs/SPDR-011"
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT"]
OUT = ROOT / "python/experiments/SPDR-011/results/estimand_validation.json"


def main() -> None:
    cells = {
        symbol: validate_run(FAMILY / symbol, expected_instruments=[symbol])
        for symbol in SYMBOLS
    }
    family = validate_family(FAMILY, expected_instruments=SYMBOLS)

    report = {
        "gate_version": "v2",
        "root": str(FAMILY.relative_to(ROOT)),
        "n_cells": len(cells),
        "expectation_note": (
            "Per-cell expectation is the cell's own symbol; the five-symbol expectation is "
            "asserted at family level. validate_family forwards one list to every cell "
            "(src/xen/estimand_validation.py:367), which cannot hold for per-symbol cells."
        ),
        "family_manifest": family["manifest"],
        "cells": cells,
        "blocking_pass": bool(
            all(cell["blocking_pass"] for cell in cells.values())
            and family["manifest"]["ok"]
        ),
    }
    OUT.write_text(json.dumps(report, indent=2, default=str))
    for symbol, cell in cells.items():
        flags = {k: v.get("ok") for k, v in cell.items() if isinstance(v, dict) and "ok" in v}
        print(f"{symbol:9s} blocking_pass={cell['blocking_pass']} {flags}")
    print("family_manifest:", json.dumps(family["manifest"]))
    print("BLOCKING_PASS:", report["blocking_pass"])


if __name__ == "__main__":
    main()
