#!/usr/bin/env python3
"""Trim the single trailing bar-mark at exactly holdout_start from every HTFCAP cell.

Operator-approved fix (option A, 2026-07-18). AMENDMENT-4 extended the emission window to
end AT holdout_start (2025-01-08T00:00:00Z); the `--extend-test` emitter ran one MTM mark too
far, to the bar whose SourceCloseTime == holdout_start. The canonical candidate-gate fence is
strict (every emitted ts < AnalysisEndUtc), so all 108 cells failed ONLY that check.

This drops marks with SourceCloseTime >= holdout_start (== boundary only; none are strictly
past it) from each cell's positions.parquet, making the emission strictly pre-holdout. It
asserts, per cell, that zero trades and zero data past the boundary are removed. Receipt:
results/boundary_trim_receipt.json.

Usage (from python/):
  uv run python experiments/XENA-HTFCAP-001/code/trim_boundary_mark.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

CODE = Path(__file__).resolve().parent
EXP = CODE.parent
ROOT = EXP.parents[1]  # python/
REPO = ROOT.parent
RUNS_ROOT = REPO / "data" / "nautilus_runs" / "XENA-HTFCAP-001"
RESULTS = EXP / "results"

HOLDOUT_START_UTC = "2025-01-08T00:00:00Z"
HOLDOUT_START_NS = 1736294400000000000  # 2025-01-08T00:00:00Z


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _trim_marks(path: Path, tag: str) -> tuple[int, int, int]:
    """Drop rows with SourceCloseTime >= holdout_start from a marks parquet in place.

    Returns (n_before, n_after, n_past_boundary). Idempotent (already-trimmed → removes 0).
    """
    marks = pl.read_parquet(path).with_columns(
        pl.col("SourceCloseTime").cast(pl.Int64).alias("_ns")
    )
    n_before = marks.height
    past = marks.filter(pl.col("_ns") > HOLDOUT_START_NS).height
    if past != 0:
        raise RuntimeError(f"{path.parent.name}/{tag}: {past} marks STRICTLY past "
                           "holdout_start — not a boundary overrun; refusing to trim")
    trimmed = marks.filter(pl.col("_ns") < HOLDOUT_START_NS).drop("_ns")
    trimmed.write_parquet(path)
    return n_before, trimmed.height, past


def trim_cell(cell_dir: Path) -> dict:
    """Drop the boundary mark from both emission layers; assert no trade impact."""
    xena_dir = cell_dir / "xena"
    cis_path = xena_dir / "cis_trades.parquet"

    # guard: trades must not touch the boundary (verified globally; assert per cell)
    cis = pl.read_parquet(cis_path).with_columns(
        pl.col("EntryTime").cast(pl.Int64).alias("_e"),
        pl.col("ExitTime").cast(pl.Int64).alias("_x"),
    )
    live = cis.filter(pl.col("Censored").cast(pl.Boolean).not_())
    trades_at_boundary = (
        cis.filter(pl.col("_e") >= HOLDOUT_START_NS).height
        + live.filter(pl.col("_x") >= HOLDOUT_START_NS).height
    )
    if trades_at_boundary != 0:
        raise RuntimeError(f"{cell_dir.name}: {trades_at_boundary} trades at/after "
                           "holdout_start — refusing to trim (needs re-emission)")

    xb, xa, _ = _trim_marks(xena_dir / "positions.parquet", "xena/positions")
    bb, ba, _ = _trim_marks(cell_dir / "bar_marks.parquet", "bar_marks")

    return {
        "cell": cell_dir.name,
        "xena_marks_before": xb,
        "xena_marks_after": xa,
        "xena_removed": xb - xa,
        "bar_marks_before": bb,
        "bar_marks_after": ba,
        "bar_marks_removed": bb - ba,
        "trades_removed": 0,
    }


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    cells = sorted(
        d for d in RUNS_ROOT.iterdir()
        if d.is_dir() and (d / "xena" / "positions.parquet").exists()
    )
    if not cells:
        print("no emitted cells found")
        return 1

    rows = []
    for d in cells:
        rows.append(trim_cell(d))

    total_xena = sum(r["xena_removed"] for r in rows)
    total_bar = sum(r["bar_marks_removed"] for r in rows)
    receipt = {
        "universe_id": "XENA-HTFCAP-001",
        "operation": "trim trailing bar-mark at holdout_start (option A, operator-approved)",
        "layers": ["xena/positions.parquet", "bar_marks.parquet"],
        "generated_utc": _utc_now(),
        "holdout_start_utc": HOLDOUT_START_UTC,
        "n_cells": len(rows),
        "total_xena_marks_removed": total_xena,
        "total_bar_marks_removed": total_bar,
        "trades_removed_total": 0,
        "note": "idempotent; xena/positions already trimmed in first pass (removes 0 now)",
        "cells": rows,
    }
    (RESULTS / "boundary_trim_receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    print(f"trimmed {len(rows)} cells; xena marks removed={total_xena}; "
          f"bar_marks removed={total_bar}; trades_removed=0")
    print(f"WROTE {RESULTS / 'boundary_trim_receipt.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
