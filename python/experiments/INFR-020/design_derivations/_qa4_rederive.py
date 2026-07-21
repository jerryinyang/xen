# Scratch from QA run 4 — safe to delete.
# Re-derives aggregates from diag_universe_coverage.json (count-only).
from __future__ import annotations

import json
import statistics
from pathlib import Path

rows = json.loads(Path(__file__).with_name("diag_universe_coverage.json").read_text())
assert len(rows) == 194
for p in ("5m", "15m", "60m"):
    rets = [r["periods"][p]["retention"] for r in rows]
    print(
        p,
        "median",
        statistics.median(rets),
        ">=0.90",
        sum(x >= 0.90 for x in rets),
        ">=0.50",
        sum(x >= 0.50 for x in rets),
        "<0.20",
        sum(x < 0.20 for x in rets),
    )
crv = next(r for r in rows if r["symbol"] == "CRVUSDT")["periods"]["60m"]["retention"]
below = sum(r["periods"]["60m"]["retention"] < crv for r in rows)
print("CRV", crv, "n_below", below, "pctile", round(100 * below / 194, 1))
