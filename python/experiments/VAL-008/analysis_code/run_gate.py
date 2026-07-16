"""VAL-008 estimand gate wrapper (design.md §3, AMENDMENT-1).

validate_family without per-cell --expect (per-cell metadata["symbol"] makes a family-level
expectation fail every single-symbol cell), then the predeclared family completeness check:
n_cells == 39 AND aggregated manifest.emitted == {BTCUSDT, ETHUSDT, SOLUSDT}.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # python/
sys.path.insert(0, str(ROOT / "src"))

from xen.estimand_validation import check_no_local_accounting, validate_family  # noqa: E402

EXPECTED_SYMBOLS = {"BTCUSDT", "ETHUSDT", "SOLUSDT"}
EXPECTED_CELLS = 39
FAMILY_ROOT = ROOT.parent / "data" / "nautilus_runs" / "VAL-008"
OUT = Path(__file__).resolve().parents[1] / "results" / "estimand_validation.json"


def main() -> int:
    report = validate_family(FAMILY_ROOT)
    emitted = set(report["manifest"]["emitted"])
    completeness = {
        "n_cells": report["n_cells"],
        "expected_cells": EXPECTED_CELLS,
        "emitted": sorted(emitted),
        "expected_symbols": sorted(EXPECTED_SYMBOLS),
        "ok": report["n_cells"] == EXPECTED_CELLS and emitted == EXPECTED_SYMBOLS,
    }
    accounting = check_no_local_accounting(Path(__file__).resolve().parents[1] / "code")
    accounting_analysis = check_no_local_accounting(Path(__file__).resolve().parent)
    report["family_completeness"] = completeness
    report["no_local_accounting_code"] = accounting
    report["no_local_accounting_analysis"] = accounting_analysis
    report["blocking_pass"] = bool(
        report["blocking_pass"]
        and completeness["ok"]
        and accounting["ok"]
        and accounting_analysis["ok"]
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "cells"}, indent=2, default=str))
    print(f"BLOCKING_PASS: {report['blocking_pass']}")
    return 0 if report["blocking_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
