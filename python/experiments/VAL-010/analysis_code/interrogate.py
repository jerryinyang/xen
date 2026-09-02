"""Read-only later-swing anatomy characterisation of the EXP-100 raid emission."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import polars as pl


ROOT = Path(__file__).resolve().parents[4]
SOURCE_ROOT = ROOT / "data/nautilus_runs/EXP-100/full"
GATE = ROOT / "python/experiments/VAL-009/results/estimand_validation.json"
OUT = ROOT / "python/experiments/VAL-010/results/anatomy_summary.json"
TRAIN_END_NS = 1_700_611_200 * 1_000_000_000
OUTCOME_COLUMNS = [
    "raid_id", "sweep_ts_ns", "status", "primary_attribution", "primary_completed",
    "profile_undefined_reason", "max_excursion_atr", "swing_atr", "strong_move",
    "swing_duration_ns", "pre_mfe_retrace", "archive_symbol", "timeframe", "config",
    "side", "prior_raid_count",
]


def anatomy_summary(frame: pl.DataFrame) -> dict[str, Any]:
    """Describe both sides of the emitted strong-move inequality."""
    surplus = frame["swing_atr"] - frame["max_excursion_atr"]
    retrace = frame["pre_mfe_retrace"]
    statuses = (
        retrace.struct.field("status").to_list()
        if isinstance(retrace.dtype, pl.Struct)
        else [None] * frame.height
    )
    return {
        "n": frame.height,
        "mean_max_excursion_atr": float(frame["max_excursion_atr"].mean()),
        "mean_swing_atr": float(frame["swing_atr"].mean()),
        "mean_surplus_atr": float(surplus.mean()),
        "strong_move_rate": float(frame["strong_move"].cast(pl.Float64).mean()),
        "median_duration_hours": float(frame["swing_duration_ns"].median() / 3_600_000_000_000),
        "retrace_status_counts": dict(sorted(Counter("NULL" if value is None else str(value) for value in statuses).items())),
    }


def anatomy_by_repeat_band(frame: pl.DataFrame) -> list[dict[str, Any]]:
    """Keep the registered repeat bands separate for the three outcome channels."""
    banded = frame.with_columns(
        pl.when(pl.col("prior_raid_count") == 0).then(pl.lit("0"))
        .when(pl.col("prior_raid_count") == 1).then(pl.lit("1"))
        .otherwise(pl.lit("2+")).alias("repeat_band")
    )
    return [
        {"config": config, "repeat_band": repeat_band, **anatomy_summary(group)}
        for (config, repeat_band), group in banded.group_by(
            ["config", "repeat_band"], maintain_order=True
        )
    ]


def repeat_contrast_summary(frame: pl.DataFrame) -> dict[str, dict[str, dict[str, float | int]]]:
    """Describe physical-stratum repeat contrasts without giving them inferential weight."""
    banded = frame.with_columns(
        pl.when(pl.col("prior_raid_count") == 0).then(pl.lit("0"))
        .when(pl.col("prior_raid_count") == 1).then(pl.lit("1"))
        .otherwise(pl.lit("2+")).alias("repeat_band")
    )
    keys = ["physical_cell", "side", "config"]
    grouped = banded.group_by([*keys, "repeat_band"]).agg(
        pl.len().alias("n"),
        pl.col("swing_atr").mean().alias("swing_atr"),
        pl.col("strong_move").cast(pl.Float64).mean().alias("strong_move_rate"),
        (pl.col("swing_duration_ns").mean() / 3_600_000_000_000).alias("duration_hours"),
    )
    baseline = grouped.filter(pl.col("repeat_band") == "0").drop("repeat_band")
    result: dict[str, dict[str, dict[str, float | int]]] = {}
    for band in ("1", "2+"):
        paired = grouped.filter(pl.col("repeat_band") == band).drop("repeat_band").join(
            baseline, on=keys, how="inner", suffix="_baseline"
        )
        channels: dict[str, dict[str, float | int]] = {}
        for channel in ("swing_atr", "strong_move_rate", "duration_hours"):
            differences = (paired[channel] - paired[f"{channel}_baseline"]).drop_nulls()
            channels[channel] = {
                "n_strata": differences.len(),
                "n_negative": int((differences < 0).sum()),
                "n_zero": int((differences == 0).sum()),
                "n_positive": int((differences > 0).sum()),
                "mean_stratum_difference": float(differences.mean()),
                "median_stratum_difference": float(differences.median()),
            }
        result[f"{band}_vs_0"] = channels
    return result


def _outcomes() -> pl.DataFrame:
    scans = [
        pl.scan_parquet(cell / "raids.parquet").select(OUTCOME_COLUMNS).filter(
            (pl.col("status") == "COMPLETED") & pl.col("primary_attribution").fill_null(False)
            & pl.col("primary_completed").fill_null(False) & (pl.col("profile_undefined_reason").fill_null("") != "ATR_UNDEFINED")
            & pl.col("max_excursion_atr").is_finite() & pl.col("swing_atr").is_finite()
            & (pl.col("sweep_ts_ns") <= TRAIN_END_NS)
        ).with_columns(pl.lit(cell.name).alias("source_cell"))
        for cell in sorted(SOURCE_ROOT.iterdir()) if cell.is_dir()
    ]
    return pl.concat(scans).collect(engine="streaming")


def main() -> None:
    gate = json.loads(GATE.read_text())
    if not gate.get("blocking_pass"):
        raise RuntimeError("EXP-100 estimand gate is not valid for VAL-010")
    raw = _outcomes()
    physical = raw.with_columns(
        pl.col("source_cell").str.replace("-breakout_bar-", "-METHOD-")
        .str.replace("-level_close-", "-METHOD-").alias("physical_cell")
    ).unique(["physical_cell", "raid_id"])
    OUT.write_text(json.dumps({
        "gate": {"blocking_pass": True, "n_cells": 264},
        "raw_source_rows": anatomy_summary(raw),
        "physical_grid": anatomy_summary(physical),
        "physical_grid_by_config_and_repeat_band": anatomy_by_repeat_band(physical),
        "physical_stratum_repeat_contrasts": repeat_contrast_summary(physical),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
