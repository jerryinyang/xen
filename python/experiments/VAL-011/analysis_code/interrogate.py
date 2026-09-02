"""Read-only TPO geometry, regime-transition, and all-raid frequency characterisation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import polars as pl


ROOT = Path(__file__).resolve().parents[4]
SOURCE_ROOT = ROOT / "data/nautilus_runs/EXP-100/full"
GATE = ROOT / "python/experiments/VAL-009/results/estimand_validation.json"
OUT = ROOT / "python/experiments/VAL-011/results/conditioning_summary.json"
TRAIN_END_NS = 1_700_611_200 * 1_000_000_000
RAID_COLUMNS = [
    "raid_id",
    "profile_generation",
    "sweep_ts_ns",
    "status",
    "primary_attribution",
    "primary_completed",
    "profile_undefined_reason",
    "raid_regime",
    "confirmation_regime",
    "endpoint_regime",
    "swing_atr",
    "strong_move",
    "swing_duration_ns",
    "side",
]


def physical_cell_name(source_cell: str) -> str:
    return source_cell.replace("-breakout_bar-", "-METHOD-").replace("-level_close-", "-METHOD-")


def canonical_source_cells(source_cells: Iterable[str]) -> list[str]:
    """Choose one deterministic representative for each BB/LC duplicate pair."""
    representatives: dict[str, str] = {}
    for source_cell in sorted(source_cells):
        representatives.setdefault(physical_cell_name(source_cell), source_cell)
    return list(representatives.values())


def frequency_summary(marks: pl.DataFrame, raids: pl.DataFrame) -> dict[str, dict[str, float | int]]:
    """Count every next-mark raid start against its preceding-mark regime exposure."""
    prior = marks.sort("ts_event_ns").with_columns(pl.col("regime").shift(1).alias("prior_regime")).filter(pl.col("prior_regime").is_not_null())
    starts = raids.group_by("sweep_ts_ns").agg(pl.col("raid_id").n_unique().alias("starts"))
    joined = prior.join(starts, left_on="ts_event_ns", right_on="sweep_ts_ns", how="left").with_columns(pl.col("starts").fill_null(0))
    answer: dict[str, dict[str, float | int]] = {}
    for row in joined.group_by("prior_regime").agg(pl.len().alias("exposure"), pl.col("starts").sum().alias("starts")).to_dicts():
        exposure, starts_n = int(row["exposure"]), int(row["starts"])
        answer[str(row["prior_regime"])] = {"exposure": exposure, "starts": starts_n, "rate_per_1000_marks": 1000.0 * starts_n / exposure}
    return answer


def aggregate_frequency(marks: pl.DataFrame, raids: pl.DataFrame) -> dict[str, dict[str, float | int]]:
    aggregate: dict[str, dict[str, float | int]] = {}
    for cell in marks["source_cell"].unique().to_list():
        table = frequency_summary(
            marks.filter(pl.col("source_cell") == cell).drop("source_cell"),
            raids.filter(pl.col("source_cell") == cell).select("sweep_ts_ns", "raid_id", "side"),
        )
        for regime, row in table.items():
            bucket = aggregate.setdefault(regime, {"exposure": 0, "starts": 0})
            bucket["exposure"] = int(bucket["exposure"]) + int(row["exposure"])
            bucket["starts"] = int(bucket["starts"]) + int(row["starts"])
    for row in aggregate.values():
        exposure = int(row["exposure"])
        row["rate_per_1000_marks"] = 1000.0 * int(row["starts"]) / exposure if exposure else None
    return aggregate


def regime_contrast_summary(raids: pl.DataFrame) -> dict[str, dict[str, dict[str, float | int | None]]]:
    """Keep the three outcome channels visible in LOW/HIGH versus MID descriptions."""
    keys = ["source_cell", "side"]
    grouped = raids.group_by([*keys, "raid_regime"]).agg(
        pl.len().alias("n"),
        pl.col("swing_atr").mean().alias("swing_atr"),
        pl.col("strong_move").cast(pl.Float64).mean().alias("strong_move_rate"),
        (pl.col("swing_duration_ns").mean() / 3_600_000_000_000).alias("duration_hours"),
    )
    mid = grouped.filter(pl.col("raid_regime") == "MID").drop("raid_regime")
    result: dict[str, dict[str, dict[str, float | int | None]]] = {}
    for arm in ("LOW", "HIGH"):
        paired = grouped.filter(pl.col("raid_regime") == arm).drop("raid_regime").join(
            mid, on=keys, how="inner", suffix="_mid"
        )
        channels: dict[str, dict[str, float | int | None]] = {}
        for channel in ("swing_atr", "strong_move_rate", "duration_hours"):
            differences = (paired[channel] - paired[f"{channel}_mid"]).drop_nulls()
            n = differences.len()
            channels[channel] = {
                "n_strata": n,
                "n_negative": int((differences < 0).sum()),
                "n_zero": int((differences == 0).sum()),
                "n_positive": int((differences > 0).sum()),
                "mean_stratum_difference": float(differences.mean()) if n else None,
                "median_stratum_difference": float(differences.median()) if n else None,
            }
        result[f"{arm}_vs_MID"] = channels
    return result


def _frames() -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    profile_columns = ["raid_id", "profile_generation", "undefined_reason", "gap_span_va", "gap_span_atr", "va_width", "tight_gap", "profile_start_ts_ns", "profile_end_ts_ns"]
    raid_scans, profile_scans, mark_scans = [], [], []
    for cell in sorted(SOURCE_ROOT.iterdir()):
        if not cell.is_dir():
            continue
        raid_scans.append(pl.scan_parquet(cell / "raids.parquet").select(RAID_COLUMNS).filter(pl.col("sweep_ts_ns") <= TRAIN_END_NS).with_columns(pl.lit(cell.name).alias("source_cell")))
        profile_scans.append(pl.scan_parquet(cell / "tpo_profiles.parquet").select(profile_columns).with_columns(pl.lit(cell.name).alias("source_cell")))
        mark_scans.append(pl.scan_parquet(cell / "bar_marks.parquet").select("ts_event_ns", "regime").filter(pl.col("ts_event_ns") <= TRAIN_END_NS).with_columns(pl.lit(cell.name).alias("source_cell")))
    return pl.concat(raid_scans).collect(engine="streaming"), pl.concat(profile_scans).collect(engine="streaming"), pl.concat(mark_scans).collect(engine="streaming")


def main() -> None:
    gate = json.loads(GATE.read_text())
    if not gate.get("blocking_pass"):
        raise RuntimeError("EXP-100 estimand gate is not valid for VAL-011")
    raids, profiles, marks = _frames()
    canonical_cells = canonical_source_cells(marks["source_cell"].unique().to_list())
    physical_raids = raids.filter(pl.col("source_cell").is_in(canonical_cells))
    physical_profiles = profiles.filter(pl.col("source_cell").is_in(canonical_cells))
    physical_marks = marks.filter(pl.col("source_cell").is_in(canonical_cells))
    joined = physical_raids.join(physical_profiles, on=["source_cell", "raid_id", "profile_generation"], how="left", nulls_equal=True)
    defined = joined.filter(pl.col("undefined_reason").is_null() & pl.col("gap_span_va").is_finite())
    transition = physical_raids.group_by("raid_regime", "confirmation_regime", "endpoint_regime").len().sort("len", descending=True).head(20).to_dicts()
    physical_outcomes = physical_raids.filter(
        (pl.col("status") == "COMPLETED")
        & pl.col("primary_attribution").fill_null(False)
        & pl.col("primary_completed").fill_null(False)
        & (pl.col("profile_undefined_reason").fill_null("") != "ATR_UNDEFINED")
        & pl.col("swing_atr").is_finite()
    )
    payload = {
        "gate": {"blocking_pass": True, "n_source_cells": 264, "n_physical_cells": len(canonical_cells)},
        "raw_source_parity": {
            "profile_join": {"raids": raids.height, "profiles": profiles.height},
            "all_raid_frequency": aggregate_frequency(marks, raids),
        },
        "physical_grid": {
            "profile_join": {"raids": physical_raids.height, "profiles": physical_profiles.height, "joined": joined.height},
            "defined_geometry": defined.select(pl.len().alias("n"), pl.col("gap_span_va").median().alias("gap_span_va_median"), pl.col("gap_span_va").quantile(0.1).alias("p10"), pl.col("gap_span_va").quantile(0.9).alias("p90"), pl.col("va_width").median().alias("va_width_median")).to_dicts()[0],
            "top_regime_transitions": transition,
            "all_raid_frequency": aggregate_frequency(physical_marks, physical_raids),
            "outcome_regime_contrasts": regime_contrast_summary(physical_outcomes),
        },
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
