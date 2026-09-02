"""Read-only lifecycle and selection characterisation of the EXP-100 raid emission."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import polars as pl


ROOT = Path(__file__).resolve().parents[4]
SOURCE_ROOT = ROOT / "data/nautilus_runs/EXP-100/full"
GATE = ROOT / "python/experiments/VAL-009/results/estimand_validation.json"
OUT = ROOT / "python/experiments/VAL-009/results/selection_summary.json"
TRAIN_END_NS = 1_700_611_200 * 1_000_000_000


def _counts(values: list[Any]) -> dict[str, int]:
    return dict(sorted(Counter("NULL" if value is None else str(value) for value in values).items()))


def selection_summary(frame: pl.DataFrame) -> dict[str, Any]:
    """Return source-row selection facts for a supplied raid frame."""
    selection_rows = frame.filter(
        (pl.col("primary_attribution").fill_null(False) & pl.col("confirmation_ts_ns").is_not_null())
        | (pl.col("status") == "CONFIRMED_NON_PRIMARY")
    ).with_columns(
        pl.when(pl.col("status") == "CONFIRMED_NON_PRIMARY")
        .then(pl.col("endpoint_ts_ns"))
        .otherwise(pl.col("confirmation_ts_ns"))
        .alias("selection_ts_ns")
    ).filter(pl.col("selection_ts_ns").is_not_null())
    cell_key = "physical_cell" if "physical_cell" in frame.columns else "source_cell"
    set_keys = ["selection_ts_ns"]
    if cell_key in frame.columns:
        set_keys.append(cell_key)
    if "side" in frame.columns:
        set_keys.append("side")
    sets = selection_rows.group_by(set_keys).agg(
        pl.len().alias("n"),
        pl.col("primary_attribution").fill_null(False).sum().alias("primaries"),
    )
    age = (frame["sweep_ts_ns"] - frame["level_creation_ts_ns"]).cast(pl.Int64)
    return {
        "n": frame.height,
        "status_counts": _counts(frame["status"].to_list()),
        "competition_sets": {
            "n_sets": sets.height,
            "sets_with_competition": sets.filter(pl.col("n") > 1).height,
            "max_set_size": int(sets["n"].max() or 0),
            "sets_with_exactly_one_primary": sets.filter(pl.col("primaries") == 1).height,
        },
        "exact_repeat_count": _counts(frame["prior_raid_count"].to_list()),
        "level_age_ns": {
            "mean": float(age.mean() or 0.0),
            "median": float(age.median() or 0.0),
            "p95": float(age.quantile(0.95) or 0.0),
        },
    }


def _source_frame() -> pl.DataFrame:
    columns = [
        "raid_id", "status", "confirmation_ts_ns", "endpoint_ts_ns", "primary_attribution", "prior_raid_count",
        "sweep_ts_ns", "level_creation_ts_ns", "archive_symbol", "timeframe", "config", "side",
    ]
    scans = [
        pl.scan_parquet(cell / "raids.parquet").select(columns).filter(
            pl.col("sweep_ts_ns") <= TRAIN_END_NS
        ).with_columns(pl.lit(cell.name).alias("source_cell"))
        for cell in sorted(SOURCE_ROOT.iterdir()) if cell.is_dir()
    ]
    return pl.concat(scans).collect(engine="streaming")


def _gate() -> dict[str, Any]:
    gate = json.loads(GATE.read_text())
    if not gate.get("blocking_pass") or gate.get("n_cells") != 264:
        raise RuntimeError("EXP-100 estimand gate is not valid for VAL-009")
    return {"blocking_pass": True, "n_cells": 264, "path": str(GATE)}


def main() -> None:
    gate = _gate()
    raw = _source_frame()
    physical = raw.with_columns(
        pl.col("source_cell").str.replace("-breakout_bar-", "-METHOD-")
        .str.replace("-level_close-", "-METHOD-").alias("physical_cell")
    ).unique(["physical_cell", "raid_id"])
    payload = {"gate": gate, "raw_source_rows": selection_summary(raw), "physical_grid": selection_summary(physical)}
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
